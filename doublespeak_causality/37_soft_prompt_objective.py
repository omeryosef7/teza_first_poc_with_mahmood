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


def optimize_one(lm, templated, raw_prompt, target_ids, free_slice, steps, lr, seed):
    """Adam on free embeddings at `free_slice`; maximize log p(target) at the last position."""
    torch.manual_seed(seed)
    dev = lm.model.device
    ids = torch.tensor([lm.tokenizer(templated, add_special_tokens=False)["input_ids"]],
                       device=dev)
    emb_layer = lm.model.get_input_embeddings()
    with torch.no_grad():
        base = emb_layer(ids).detach()                       # [1, T, d]
    a, b = free_slice
    free = torch.nn.Parameter(base[:, a:b, :].clone().float())
    opt = torch.optim.Adam([free], lr=lr)
    tgt = torch.tensor(target_ids, device=dev)

    traj = []
    best = {"step": 0, "p_target": None}
    for step in range(steps + 1):
        emb = base.clone()
        emb[:, a:b, :] = free.to(base.dtype)
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
    return {"trajectory": traj, "p_start": traj[0], "p_end": traj[-1],
            "p_best": best["p_target"], "best_step": best["step"],
            "n_free_tokens": b - a}


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
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--lr", type=float, default=0.01)
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
        f"pair_softprompt_{args.target}_{args.free_positions}_{tag}_"
        f"{time.strftime('%Y%m%d_%H%M%S')}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    print(f"[soft] target={args.target}({target_word}) free={args.free_positions} "
          f"steps={args.steps} lr={args.lr} n={len(rows)} -> {out_dir}")

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
                           args.steps, args.lr, args.seed + i)
        res.update({"sid": r["sid"], "split": r["split"], "demo_style": r["demo_style"],
                    "n_demos": r["n_demos"], "free_slice": list(free_slice),
                    "n_prompt_tokens": n_tok})
        results.append(res)
        print(f"  [soft] {i+1}/{len(rows)} {r['sid']}: "
              f"p_start={res['p_start']:.5f} -> p_best={res['p_best']:.5f} "
              f"(step {res['best_step']}, {res['n_free_tokens']} free tokens)")

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
        "n_prompts": len(results), "n_skipped": n_skipped,
        "p_start_mean": (sum(starts) / len(starts)) if starts else None,
        "p_best_mean": (sum(bests) / len(bests)) if bests else None,
        "improvement_ci": (None if ci is None else
                           {"mean": round(ci["mean_diff"], 6), "lo": round(ci["lo"], 6),
                            "hi": round(ci["hi"], 6), "n": ci["n"],
                            "ci_reliable": ci["ci_reliable"]}),
        "results": results, "status": "COMPLETE",
    }
    with open(os.path.join(out_dir, "softprompt_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(f"[soft] p_start={summary['p_start_mean']:.5f} -> "
          f"p_best={summary['p_best_mean']:.5f}")
    if ci:
        print(f"[soft] improvement {ci['mean_diff']:+.5f} "
              f"[{ci['lo']:+.5f},{ci['hi']:+.5f}] n={ci['n']}")
    print(f"[soft] -> {out_dir}")


if __name__ == "__main__":
    main()
