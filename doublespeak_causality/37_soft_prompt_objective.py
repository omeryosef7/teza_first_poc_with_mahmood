"""
37_soft_prompt_objective.py — CAUSAL_CORE_PLAN §8.5 + §16.13 (S11). THE GATE FOR S12.

Continuous (soft-prompt) optimization over DEMONSTRATION positions, asking the plan's
question directly: *is the causal objective optimizable in principle here?* If continuous
optimization cannot move the causal score, the objective must be debugged before any
GCG/MAC is attempted (§8.5) — a discrete failure would otherwise be uninterpretable.

WHY NOT REUSE scripts/reinforce_objective/soft_prompt_reinforce.py: that harness is built
for REINFORCE over *sampled generations* scored by an ASR-style reward, because its
objective (harmful behaviour) is not differentiable. Ours is: the causal score is the
next-token probability of the concept at the readout position, so it can be optimized by
plain backprop through `inputs_embeds`. Using REINFORCE here would add sampling variance to
a quantity we can differentiate exactly, and would make a null result ambiguous — exactly
what the §8.5 gate must not be. We reuse the *pattern* (Adam on a free-embedding Parameter,
per-step logging, best-checkpoint tracking) and ds_common/pair_common for everything else.

WHAT IS OPTIMIZED: the token embeddings at the demonstration-block positions of a
NEUTRAL_CODEWORD prompt are replaced by free parameters, initialised at their current
values. Everything else (the readout question, the chat template) is frozen. So this is an
upper bound on what *any* demonstration-level attack could achieve at those positions.

CONTROLS (both essential — without them "it optimized" means nothing):
  * `--target unrelated` optimizes toward an unrelated word instead of the concept. If the
    score moves just as easily, the machinery is trivially steerable and a positive result
    on the concept says nothing.
  * `--free-positions readout` optimizes the READOUT tokens instead of the demonstrations.
    If that is much easier, the effect is about the question, not the demonstrations.

Reports the causal score per step, its ceiling, and the paired improvement over step 0.
Scalars only are persisted (plan §15).

Usage:
  python 37_soft_prompt_objective.py --bench ... --steps 200 --n-prompts 8
"""
import os
import sys
import json
import time
import argparse

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds_common as dc
import pair_common as pc
import stats as st

HERE = os.path.dirname(os.path.abspath(__file__))


def demo_span(lm, templated, raw_prompt):
    """[start, end) token indices of the demonstration block in the templated prompt.

    Same boundary rule as 36_pair_attention: locate the separator in the RAW prompt and map
    it in, because the chat template itself ends with a blank line (searching the templated
    string finds the assistant header instead — the bug that invalidated job 693618).
    """
    ids = lm.tokenizer(templated, add_special_tokens=False)["input_ids"]
    pstart = templated.find(raw_prompt)
    sep_local = raw_prompt.rfind("\n\n")
    if pstart < 0 or sep_local <= 0:
        return None
    sep_char = pstart + sep_local + 2
    enc = lm.tokenizer(templated, add_special_tokens=False, return_offsets_mapping=True)
    offs = enc["offset_mapping"]
    if not dc._offsets_are_sane(offs, len(templated)):
        return None
    start = next((i for i, (s, e) in enumerate(offs) if e > s and s >= pstart), None)
    end = next((i for i, (s, e) in enumerate(offs) if e > s and s >= sep_char), None)
    if start is None or end is None or end <= start:
        return None
    return start, end, len(ids)


def readout_span(lm, templated, raw_prompt):
    sp = demo_span(lm, templated, raw_prompt)
    if sp is None:
        return None
    _, end, n = sp
    return end, n


def optimize_one(lm, templated, raw_prompt, target_ids, free_slice, steps, lr, seed,
                 param="simplex", temperature=1.0, init_scale=10.0):
    """Adam over `free_slice`; maximize log p(target) at the last position.

    param="free"     — unconstrained vectors in R^d at each position.
    param="simplex"  — logits over the VOCABULARY; the embedding used is the softmax-weighted
                       convex combination of embedding rows. This is the meaningful
                       relaxation: its optimum is an upper bound on what a real *token*
                       sequence can do, because any token sequence is a vertex of this
                       simplex.

    Why the default is `simplex`: with `free`, the first run of this gate drove the causal
    score from 0.000 to 0.9999 — but so did the UNRELATED-target control (0.001 -> 0.9999).
    An unconstrained soft prompt over 58-202 positions has far more capacity than any token
    sequence, so it reaches any target and the "positive control" is vacuous. It proves the
    optimizer works, not that the causal objective is reachable by a demonstration attack.
    """
    torch.manual_seed(seed)
    dev = lm.model.device
    ids = torch.tensor([lm.tokenizer(templated, add_special_tokens=False)["input_ids"]],
                       device=dev)
    emb_layer = lm.model.get_input_embeddings()
    with torch.no_grad():
        base = emb_layer(ids).detach()                       # [1, T, d]
        E = emb_layer.weight.detach()                        # [V, d]
    a, b = free_slice
    tgt = torch.tensor(target_ids, device=dev)

    if param == "free":
        var = torch.nn.Parameter(base[:, a:b, :].clone().float())
    else:
        # initialise the logits at the ACTUAL tokens, so step 0 reproduces the real prompt
        init = torch.full((b - a, E.shape[0]), -init_scale, device=dev,
                          dtype=torch.float32)
        init.scatter_(1, ids[0, a:b].unsqueeze(1), init_scale)
        var = torch.nn.Parameter(init)
    init_ids = ids[0, a:b].clone()
    opt = torch.optim.Adam([var], lr=lr)

    def current_embeddings():
        if param == "free":
            return var.to(base.dtype)
        w = torch.softmax(var / temperature, dim=-1)          # [L, V]
        return (w @ E.float()).to(base.dtype).unsqueeze(0)    # [1, L, d]

    traj = []
    best = {"step": 0, "p_target": None}
    for step in range(steps + 1):
        emb = base.clone()
        emb[:, a:b, :] = current_embeddings()
        out = lm.model(inputs_embeds=emb, return_dict=True)
        logits = out.logits[0, -1, :].float()
        logp = torch.log_softmax(logits, dim=-1)
        # probability MASS over all surface forms of the target
        p = torch.logsumexp(logp[tgt], dim=0)
        loss = -p
        pv = float(p.exp())
        traj.append(round(pv, 6))
        if best["p_target"] is None or pv > best["p_target"]:
            best = {"step": step, "p_target": pv}
        if step == steps:
            break
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
    # How close is the relaxed solution to a real token sequence? A simplex solution whose
    # per-position max weight is near 1.0 IS (almost) a token sequence and its score is
    # achievable discretely; one spread across the vocabulary is not.
    # DISCRETIZATION CHECK — the number that actually bounds a token attack.
    # peak_w < 1 means the relaxed optimum is a BLEND of tokens, which no real prompt can
    # be. So take the argmax token sequence, run it as an ordinary hard prompt, and report
    # the score it achieves. relaxed >> discretized means the relaxed win was bought with
    # off-manifold blending and does NOT bound what a discrete attack can do.
    p_discrete = None
    if param != "free":
        with torch.no_grad():
            hard = ids.clone()
            hard[0, a:b] = torch.softmax(var / temperature, dim=-1).argmax(dim=-1)
            out_h = lm.model(input_ids=hard, return_dict=True)
            lp = torch.log_softmax(out_h.logits[0, -1, :].float(), dim=-1)
            p_discrete = float(torch.logsumexp(lp[tgt], dim=0).exp())

    peak, frac_changed = None, None
    if param != "free":
        with torch.no_grad():
            w = torch.softmax(var / temperature, dim=-1)
            peak = float(w.max(dim=-1).values.mean())
            # DID THE OPTIMIZER ACTUALLY EXPLORE? The logits start with a gap of
            # 2*init_scale between the initial token and every other token; Adam moves a
            # logit by ~lr per step, so with too small an lr*steps budget the argmax CANNOT
            # change and a "null" is an optimizer artefact, not a result. The first simplex
            # run had init_scale=10 and lr=0.01 x 300 steps = ~3 logit units against a gap
            # of 20, and duly reported p_best == p_start == 0.00000 for every prompt.
            frac_changed = float((w.argmax(dim=-1) != init_ids).float().mean())
    return {"trajectory": traj, "p_start": traj[0], "p_end": traj[-1],
            "p_best": best["p_target"], "best_step": best["step"],
            "n_free_tokens": b - a, "param": param,
            "mean_peak_weight": (None if peak is None else round(peak, 4)),
            "frac_positions_changed": (None if frac_changed is None
                                       else round(frac_changed, 4)),
            "optimizer_moved": (None if frac_changed is None else bool(frac_changed > 0)),
            "logit_budget": round(lr * steps, 2), "init_gap": 2 * init_scale,
            "budget_sufficient": bool(lr * steps > 2 * init_scale),
            "p_discretized": (None if p_discrete is None else round(p_discrete, 6)),
            "discretization_retention": (None if (p_discrete is None or not best["p_target"])
                                         else round(p_discrete / best["p_target"], 4))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(HERE, "outputs"))
    ap.add_argument("--readout", default="cloze")
    ap.add_argument("--demo-styles", default="news,narrative,technical",
                    help="use the S2 gate-passing styles")
    ap.add_argument("--condition", default="NEUTRAL_CODEWORD")
    ap.add_argument("--target", default="concept",
                    choices=["concept", "unrelated", "codeword"],
                    help="'unrelated' is the triviality control")
    ap.add_argument("--free-positions", default="demos", choices=["demos", "readout"],
                    help="'readout' is the locus control")
    ap.add_argument("--param", default="simplex", choices=["simplex", "free"],
                    help="simplex = convex combination over the vocabulary (a true "
                         "relaxation of a token sequence); free = unconstrained R^d, which "
                         "makes the gate vacuous (see optimize_one docstring)")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--init-scale", type=float, default=10.0,
                    help="simplex logits start at +/-init_scale, so step 0 reproduces the "
                         "REAL prompt. lr*steps must exceed 2*init_scale or the argmax "
                         "cannot move and a null is an optimizer artefact.")
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--lr", type=float, default=1.0,
                    help="on VOCAB LOGITS for --param simplex (needs to be O(1), "
                         "not O(0.01)); use ~0.01 only for --param free")
    ap.add_argument("--n-prompts", type=int, default=8)
    ap.add_argument("--splits", default="dev,heldout")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    bench = json.load(open(args.bench))
    pair = bench["pair"]
    styles = {s.strip() for s in args.demo_styles.split(",") if s.strip()}
    splits = [s.strip() for s in args.splits.split(",") if s.strip()]

    rows = [r for r in bench["semantic"]
            if r["readout"] == args.readout and r["condition"] == args.condition
            and r["split"] in splits and (not styles or r["demo_style"] in styles)]
    rows.sort(key=lambda r: r["sid"])
    rows = rows[: args.n_prompts]
    if not rows:
        raise SystemExit("no matching prompts")

    lm = dc.load_model(args.model)
    target_word = {"concept": pair["concept"], "codeword": pair["codeword"],
                   "unrelated": pair.get("unrelated_source", "piano")}[args.target]
    target_ids = pc.word_first_ids(lm.tokenizer, target_word)

    tag = args.model.split("/")[-1]
    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(
        args.out_root,
        f"pair_softprompt_{args.param}_{args.target}_{args.free_positions}_{tag}_"
        f"{time.strftime('%Y%m%d_%H%M%S')}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    print(f"[soft] target={args.target}({target_word}) free={args.free_positions} "
          f"param={args.param} steps={args.steps} lr={args.lr} n={len(rows)} -> {out_dir}")

    results, n_skipped = [], 0
    for i, r in enumerate(rows):
        templated = dc.apply_template(lm.tokenizer, r["prompt"])
        sp = demo_span(lm, templated, r["prompt"])
        if sp is None:
            n_skipped += 1
            continue
        start, end, n_tok = sp
        free_slice = (start, end) if args.free_positions == "demos" else (end, n_tok)
        if free_slice[1] <= free_slice[0]:
            n_skipped += 1
            continue
        res = optimize_one(lm, templated, r["prompt"], target_ids, free_slice,
                           args.steps, args.lr, args.seed + i,
                           param=args.param, temperature=args.temperature,
                           init_scale=args.init_scale)
        res.update({"sid": r["sid"], "split": r["split"], "demo_style": r["demo_style"],
                    "n_demos": r["n_demos"], "free_slice": list(free_slice),
                    "n_prompt_tokens": n_tok})
        results.append(res)
        print(f"  [soft] {i+1}/{len(rows)} {r['sid']}: "
              f"p_start={res['p_start']:.5f} -> p_best={res['p_best']:.5f} "
              f"(step {res['best_step']}, {res['n_free_tokens']} free tokens, "
              f"peak_w={res.get('mean_peak_weight')} "
              f"changed={res.get('frac_positions_changed')} "
              f"DISCRETE={res.get('p_discretized')})")

    starts = [x["p_start"] for x in results]
    bests = [x["p_best"] for x in results]
    ci = (st.paired_bootstrap_ci(bests, starts, n_boot=10000, seed=0)
          if len(results) >= 2 else None)
    summary = {
        "model": lm.meta(), "pair": pair, "plan": "CAUSAL_CORE_PLAN §8.5 (S11 gate)",
        "bench": os.path.abspath(args.bench),
        "readout": args.readout, "condition": args.condition,
        "demo_styles": sorted(styles), "splits": splits,
        "target": args.target, "target_word": target_word, "target_ids": target_ids,
        "free_positions": args.free_positions,
        "steps": args.steps, "lr": args.lr, "seed": args.seed,
        "param": args.param, "temperature": args.temperature,
        "init_scale": args.init_scale,
        "logit_budget": round(args.lr * args.steps, 2),
        "budget_sufficient": bool(args.lr * args.steps > 2 * args.init_scale),
        "n_prompts": len(results), "n_skipped": n_skipped,
        "p_start_mean": (sum(starts) / len(starts)) if starts else None,
        "p_best_mean": (sum(bests) / len(bests)) if bests else None,
        "p_discretized_mean": (
            (sum(x["p_discretized"] for x in results if x.get("p_discretized") is not None)
             / max(1, sum(1 for x in results if x.get("p_discretized") is not None)))
            if results else None),
        "improvement_ci": (None if ci is None else
                           {"mean": round(ci["mean_diff"], 6), "lo": round(ci["lo"], 6),
                            "hi": round(ci["hi"], 6), "n": ci["n"],
                            "ci_reliable": ci["ci_reliable"]}),
        "results": results, "status": "COMPLETE",
    }
    with open(os.path.join(out_dir, "softprompt_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(f"[soft] p_start={summary['p_start_mean']:.5f} -> "
          f"p_best={summary['p_best_mean']:.5f} "
          f"-> DISCRETIZED={summary['p_discretized_mean']}")
    if ci:
        print(f"[soft] improvement {ci['mean_diff']:+.5f} "
              f"[{ci['lo']:+.5f},{ci['hi']:+.5f}] n={ci['n']}")
    print(f"[soft] -> {out_dir}")


if __name__ == "__main__":
    main()
