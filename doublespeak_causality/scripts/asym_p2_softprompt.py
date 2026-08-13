#!/usr/bin/env python3
"""ASYMMETRY SPRINT — PHASE 2: continuous soft-prompt reachability (plan §6, §19.4, §19.6).

Separates three claims that the sprint's central question conflates:

    activation-space reachable  >=  continuous-INPUT reachable  >=  discrete-TOKEN reachable

by optimizing a UNIVERSAL 16-position suffix in three progressively more constrained
parameterizations, all against the SAME objective, the SAME frozen v3 train pool, and the
SAME held-out test set the GCG matrix used:

  param=free      unconstrained vectors in R^d at each suffix position, subject to an
                  explicit L2 budget on the perturbation from the initial suffix embedding.
                  -> upper bound on CONTINUOUS input reachability.
  param=simplex   logits over the vocabulary; the embedding used is the softmax-weighted
                  convex combination of embedding rows. Every real token sequence is a
                  VERTEX of this simplex, so its optimum UPPER-BOUNDS any discrete suffix.
                  -> upper bound on TOKEN reachability.
  (+ rounding)    §19.4: the simplex solution is projected to its per-position argmax token
                  and re-evaluated as an ordinary hard prompt. The retention ratio is the
                  sharpest direct test of the DISCRETE-TOKEN BOTTLENECK (H2).

Design reused from `$DC/37_soft_prompt_objective.py` (simplex parameterization, peak-weight /
blended-position diagnostics, discretization retention, and the logit-budget sufficiency
check that caught an earlier run whose "null" was an optimizer artefact). The objective and
the universal/held-out protocol are new.

OBJECTIVES (`--objective`)
  refusal   minimize  mean_p <h_p , v_refusal>          (h = residual at hs[19], decision pos)
  random    identical, with a norm-matched random unit direction (the specificity control)
  task      maximize  log p(safe_target_prefix)          (the vanilla GCG objective)
  none      no optimization; evaluate the init suffix    (the floor)

POSITIONS / OFF-BY-ONE — see docs/ASYMMETRY_SPRINT_EXECUTION_LOG.md E0.3.
  The objective is read at the `decision` position (last token of the templated prompt),
  which is where the refusal axis was FITTED and causally validated — NOT at the last suffix
  token that the GCG code path used (defect D2). The `last_suffix` projection is also
  recorded so the two positions can be compared on identical solutions.
  --refusal-fit-layer takes a FIT layer; +1 is applied here and asserted into meta.json.

TRAIN/TEST DISCIPLINE (plan §3.5): optimization sees ONLY the train pool. The held-out test
split is evaluated once, after the solution is frozen. Nothing is selected on test.

SAFETY: writes scalars and (optionally) the solution tensor. Generations are written to a
separate raw file for the judge; no generated text is printed to stdout.
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402
import torch  # noqa: E402

import ds_common as dc  # noqa: E402
import pair_common as pc  # noqa: E402


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def load_unit(path):
    v = torch.load(path, map_location="cpu", weights_only=True).float().flatten()
    return v / (v.norm() + 1e-8)


def template_tail(tokenizer, enable_thinking):
    """How many template tokens follow the user content (measured, never hardcoded)."""
    a = tokenizer(dc.apply_template(tokenizer, "X", enable_thinking=enable_thinking),
                  return_tensors="pt")["input_ids"][0].tolist()
    b = tokenizer(dc.apply_template(tokenizer, "X Y Y Y", enable_thinking=enable_thinking),
                  return_tensors="pt")["input_ids"][0].tolist()
    n = 0
    while n < min(len(a), len(b)) and a[-1 - n] == b[-1 - n]:
        n += 1
    assert 1 <= n < 16, f"implausible template tail {n}"
    return n


class Prompt:
    """Token layout for one item: [head | suffix (n_suf) | tail (template)] (+ target ids)."""

    __slots__ = ("task_id", "head", "tail", "target", "n_head", "n_tail")

    def __init__(self, task_id, head, tail, target):
        self.task_id, self.head, self.tail, self.target = task_id, head, tail, target
        self.n_head, self.n_tail = len(head), len(tail)


def build_prompts(tokenizer, items, n_suffix, tail_len, enable_thinking, device):
    """Split each templated prompt into the part before the suffix and the template tail.

    The suffix sits at the END of the USER content (placement=user, matching the GCG eval),
    i.e. immediately before the `<|eot_id|><|start_header_id|>assistant...` tail.
    """
    out = []
    # a filler suffix of exactly n_suffix known tokens, used only to locate the split
    filler_ids = tokenizer(" !" * n_suffix, add_special_tokens=False)["input_ids"]
    assert len(filler_ids) == n_suffix, \
        f"' !'*{n_suffix} tokenized to {len(filler_ids)} tokens"
    filler_str = tokenizer.decode(filler_ids)
    for it in items:
        text = dc.apply_template(tokenizer, it["instruction"] + filler_str,
                                 enable_thinking=enable_thinking)
        ids = tokenizer(text, return_tensors="pt")["input_ids"][0]
        n = ids.numel()
        suf_lo, suf_hi = n - tail_len - n_suffix, n - tail_len
        assert ids[suf_lo:suf_hi].tolist() == filler_ids, \
            f"suffix slot mislocated for {it['task_id']}"
        tgt = tokenizer(it["safe_target_prefix"], add_special_tokens=False)["input_ids"]
        out.append(Prompt(it["task_id"],
                          ids[:suf_lo].to(device), ids[suf_hi:].to(device),
                          torch.tensor(tgt, device=device)))
    return out


# --------------------------------------------------------------------------- #
# the soft suffix
# --------------------------------------------------------------------------- #

class SoftSuffix:
    """A universal 16-position suffix, shared across all prompts.

    param='free'    : var = the embeddings themselves; the perturbation from the init
                      embedding is projected back into an L2 ball of radius `budget` after
                      every step (plan §6.2 -- a continuous optimizer can otherwise win
                      trivially with an enormous embedding norm).
    param='simplex' : var = vocabulary logits; embedding = softmax(var/T) @ E. Initialised
                      at the real init tokens with a +-init_scale gap so step 0 reproduces
                      the discrete starting point.
    """

    def __init__(self, tokenizer, embed_w, n_suffix, param, device, seed,
                 budget=None, temperature=1.0, init_scale=10.0):
        self.param, self.temperature, self.budget = param, temperature, budget
        self.E = embed_w
        g = torch.Generator(device="cpu").manual_seed(seed)
        init_ids = tokenizer(" !" * n_suffix, add_special_tokens=False)["input_ids"]
        self.init_ids = torch.tensor(init_ids, device=device)
        with torch.no_grad():
            self.e_init = embed_w[self.init_ids].detach().float().clone()   # [L, d]
        if param == "free":
            noise = torch.randn(self.e_init.shape, generator=g).to(device)
            noise = noise / noise.norm(dim=1, keepdim=True) * 1e-3
            self.var = torch.nn.Parameter(self.e_init.clone() + noise)
        elif param == "simplex":
            v = torch.full((n_suffix, embed_w.shape[0]), -init_scale,
                           device=device, dtype=torch.float32)
            v.scatter_(1, self.init_ids.unsqueeze(1), init_scale)
            self.var = torch.nn.Parameter(v)
        else:
            raise ValueError(param)

    def embeddings(self):
        if self.param == "free":
            return self.var
        w = torch.softmax(self.var / self.temperature, dim=-1)
        # matmul in the embedding's own dtype: `self.E.float()` would materialise a ~2 GB
        # fp32 copy of the [vocab, d] matrix on EVERY forward.
        return (w.to(self.E.dtype) @ self.E).float()

    @torch.no_grad()
    def project(self):
        """Enforce the L2 perturbation budget (free only)."""
        if self.param != "free" or self.budget is None:
            return
        d = self.var.data - self.e_init
        n = d.norm(dim=1, keepdim=True)
        scale = torch.clamp(self.budget / (n + 1e-8), max=1.0)
        self.var.data = self.e_init + d * scale

    @torch.no_grad()
    def diagnostics(self):
        out = {"param": self.param}
        if self.param == "free":
            d = (self.var.data - self.e_init).norm(dim=1)
            out.update(pert_norm_mean=float(d.mean()), pert_norm_max=float(d.max()),
                       emb_norm_mean=float(self.var.data.norm(dim=1).mean()),
                       init_emb_norm_mean=float(self.e_init.norm(dim=1).mean()),
                       budget=self.budget)
        else:
            w = torch.softmax(self.var.data / self.temperature, dim=-1)
            mx = w.max(dim=-1).values
            am = w.argmax(dim=-1)
            out.update(mean_peak_weight=float(mx.mean()), min_peak_weight=float(mx.min()),
                       n_blended_positions=int((mx < 0.9).sum()),
                       frac_positions_changed=float((am != self.init_ids).float().mean()))
        return out

    @torch.no_grad()
    def argmax_ids(self):
        if self.param != "simplex":
            return None
        return torch.softmax(self.var.data / self.temperature, dim=-1).argmax(dim=-1)


# --------------------------------------------------------------------------- #
# forward / objective
# --------------------------------------------------------------------------- #

def forward_batch(model, embed_w, prompts, soft_emb, hs_rows, need_target=False):
    """Right-aligned-free batching: prompts differ in length, so run them one at a time but
    keep the graph shared. Returns per-prompt {'h': {row: h_decision}, 'h_suf': {...},
    'ce': target cross-entropy or None}.

    (Padding a batch would change the decision position's attention mask handling for no
    real speedup at these lengths; one-at-a-time keeps the layout provably identical to the
    eval path.)
    """
    res = []
    for p in prompts:
        head = embed_w[p.head].unsqueeze(0)
        tail = embed_w[p.tail].unsqueeze(0)
        emb = torch.cat([head, soft_emb.unsqueeze(0).to(head.dtype), tail], dim=1)
        if need_target:
            emb = torch.cat([emb, embed_w[p.target].unsqueeze(0)], dim=1)
        out = model(inputs_embeds=emb, output_hidden_states=True)
        n_dec = p.n_head + soft_emb.shape[0] + p.n_tail - 1     # decision position
        n_suf = p.n_head + soft_emb.shape[0] - 1                # last suffix position
        r = {"h": {row: out.hidden_states[row][0, n_dec, :].float() for row in hs_rows},
             "h_suf": {row: out.hidden_states[row][0, n_suf, :].float() for row in hs_rows},
             "ce": None}
        if need_target:
            lg = out.logits[0, n_dec: n_dec + p.target.numel(), :]
            r["ce"] = torch.nn.functional.cross_entropy(lg.float(), p.target)
        res.append(r)
    return res


def objective_value(res, kind, v, row, v_ref=None, proj0=None, mu=0.0):
    """Scalar loss to MINIMIZE, averaged over the batch.

    `task_orth` (plan §20.1, the ORTHOGONALITY TEST on Gate D): minimise the ordinary task
    loss while PINNING the refusal projection to its clean per-prompt value, via a quadratic
    penalty mu*(proj - proj0)^2. The question it answers: can 16 free continuous positions
    force compliance WITHOUT moving the refusal coordinate? If yes, Gate D's ASR 0.784 was
    not evidence of mechanism-guided attack, and the continuous-vs-discrete asymmetry is
    partly an artifact of comparing an unconstrained continuous attacker against a
    mechanism-constrained discrete one.
    """
    if kind == "task":
        return torch.stack([r["ce"] for r in res]).mean()
    if kind == "task_orth":
        ce = torch.stack([r["ce"] for r in res]).mean()
        pen = torch.stack([(torch.dot(r["h"][row], v_ref) - p0) ** 2
                           for r, p0 in zip(res, proj0)]).mean()
        return ce + mu * pen
    return torch.stack([torch.dot(r["h"][row], v) for r in res]).mean()


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--train-manifest", default=None,
                    help="frozen optimization pool; defaults to --manifest with --train-split")
    ap.add_argument("--train-split", default="train")
    ap.add_argument("--test-split", default="test")
    ap.add_argument("--objective", choices=["refusal", "random", "task", "task_orth", "none"],
                    required=True)
    ap.add_argument("--orth-mu", type=float, default=1.0,
                    help="§20.1 penalty weight pinning the refusal projection to its clean "
                         "per-prompt value (objective=task_orth only)")
    ap.add_argument("--param", choices=["free", "simplex"], default="free")
    ap.add_argument("--budget", type=float, default=None,
                    help="L2 ball radius on the per-position perturbation (free only)")
    ap.add_argument("--budget-rel", type=float, default=None,
                    help="budget as a MULTIPLE of the mean init embedding norm (free only)")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--init-scale", type=float, default=10.0)
    ap.add_argument("--n-suffix", type=int, default=16)
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--refusal-dir", default=os.path.join(HERE, "outputs/refusal_alllayers"))
    ap.add_argument("--refusal-fit-layer", type=int, default=18)
    ap.add_argument("--enable-thinking", default="false")
    ap.add_argument("--eval-every", type=int, default=50)
    ap.add_argument("--max-new", type=int, default=256)
    ap.add_argument("--generate", action="store_true", default=True)
    ap.add_argument("--no-generate", dest="generate", action="store_false")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    if args.smoke:
        args.steps, args.batch, args.max_new = 6, 2, 16

    t0 = time.time()
    os.makedirs(args.out_dir, exist_ok=True)
    dc.set_seed(args.seed)
    enable_thinking = dc.parse_enable_thinking(args.enable_thinking)

    lm = dc.load_model(args.model)
    model, tokenizer = lm.model, lm.tokenizer
    device = next(model.parameters()).device
    for p in model.parameters():                    # only the suffix is trainable
        p.requires_grad_(False)
    embed_w = model.get_input_embeddings().weight

    fit_layer = args.refusal_fit_layer
    row = fit_layer + 1
    assert 1 <= row <= lm.num_layers, f"hs row {row} out of range"
    print(f"[cfg] refusal fit_layer={fit_layer} -> hidden_states_index={row} "
          f"(+1 applied HERE)", flush=True)

    v_ref = load_unit(os.path.join(args.refusal_dir,
                                   f"refusal_direction_llama_L{fit_layer}.pt")).to(device)
    if args.objective == "random":
        v = pc.norm_matched_random(v_ref.cpu(), 1, seed=args.seed + 1000)[0].to(device)
        v = v / v.norm()
    else:
        v = v_ref
    cos_ref = float(torch.dot(v, v_ref))
    print(f"[dir] objective={args.objective} cos(v, v_refusal)={cos_ref:+.4f} "
          f"|v|={float(v.norm()):.4f}", flush=True)

    tail_len = template_tail(tokenizer, enable_thinking)
    print(f"[template] tail={tail_len}", flush=True)

    def load_items(path, split, n_min):
        rows_ = [json.loads(l) for l in open(path)]
        if split:
            rows_ = [r for r in rows_ if r.get("split") == split]
        seen, uniq = set(), []
        for r in rows_:
            if r["task_id"] in seen:
                continue
            seen.add(r["task_id"])
            uniq.append(r)
        assert len(uniq) >= n_min, f"need >={n_min} unique items, got {len(uniq)} ({path}:{split})"
        return uniq

    tr_path = args.train_manifest or args.manifest
    tr_split = None if args.train_manifest else args.train_split
    train_items = load_items(tr_path, tr_split, 2 if args.smoke else 20)
    test_items = load_items(args.manifest, args.test_split, 2 if args.smoke else 20)
    if args.smoke:
        train_items, test_items = train_items[:2], test_items[:2]
    tr_ids = {it["task_id"] for it in train_items}
    te_ids = {it["task_id"] for it in test_items}
    assert not (tr_ids & te_ids), \
        f"TRAIN/TEST LEAKAGE: {len(tr_ids & te_ids)} shared task_ids"
    print(f"[data] train={len(train_items)} test={len(test_items)} leakage=0", flush=True)

    train = build_prompts(tokenizer, train_items, args.n_suffix, tail_len,
                          enable_thinking, device)
    test = build_prompts(tokenizer, test_items, args.n_suffix, tail_len,
                         enable_thinking, device)

    budget = args.budget
    if args.budget_rel is not None:
        with torch.no_grad():
            init_ids = tokenizer(" !" * args.n_suffix, add_special_tokens=False)["input_ids"]
            mean_norm = float(embed_w[torch.tensor(init_ids, device=device)]
                              .float().norm(dim=1).mean())
        budget = args.budget_rel * mean_norm
        print(f"[budget] rel={args.budget_rel} x mean_init_emb_norm={mean_norm:.4f} "
              f"-> L2 radius {budget:.4f}", flush=True)

    assert not (args.param == "free" and budget is None and args.objective != "none"), \
        "plan §6.2: a `free` soft prompt MUST carry an explicit L2 budget " \
        "(--budget or --budget-rel), otherwise it wins trivially with a huge embedding norm"
    soft = SoftSuffix(tokenizer, embed_w, args.n_suffix, args.param, device, args.seed,
                      budget=budget, temperature=args.temperature,
                      init_scale=args.init_scale)

    @torch.no_grad()
    def evaluate(prompts, tag):
        """Refusal projection at BOTH positions, per prompt. No selection happens here."""
        emb = soft.embeddings().detach()
        rec = []
        for p in prompts:
            r = forward_batch(model, embed_w, [p], emb, [row])[0]
            rec.append({"task_id": p.task_id, "pool": tag,
                        "proj_decision": float(torch.dot(r["h"][row], v_ref)),
                        "proj_last_suffix": float(torch.dot(r["h_suf"][row], v_ref)),
                        "obj_decision": float(torch.dot(r["h"][row], v))})
        return rec

    baseline_train = evaluate(train, "train")
    baseline_test = evaluate(test, "test")
    print(f"[baseline] train proj={np.mean([r['proj_decision'] for r in baseline_train]):+.4f} "
          f"test proj={np.mean([r['proj_decision'] for r in baseline_test]):+.4f}", flush=True)

    traj = []
    if args.objective != "none":
        opt = torch.optim.Adam([soft.var], lr=args.lr)
        rng = np.random.default_rng(args.seed)
        need_target = args.objective in ("task", "task_orth")
        # §20.1: per-prompt CLEAN projection, captured before optimization starts.
        proj0_by_id = {r["task_id"]: r["proj_decision"] for r in baseline_train}
        for step in range(args.steps):
            idx = rng.choice(len(train), size=min(args.batch, len(train)), replace=False)
            opt.zero_grad(set_to_none=True)
            tot = 0.0
            # GRADIENT ACCUMULATION, one prompt at a time. Holding `batch` graphs alive
            # simultaneously (each with output_hidden_states over ~33 layers x ~240 tokens)
            # is what OOMs; accumulating keeps exactly one graph resident and is
            # mathematically identical for a mean-reduced loss.
            for i in idx:
                res = forward_batch(model, embed_w, [train[i]], soft.embeddings(), [row],
                                    need_target=need_target)
                _p0 = ([torch.tensor(proj0_by_id[train[i].task_id], device=v.device,
                                     dtype=v.dtype)] if args.objective == "task_orth" else None)
                loss = objective_value(res, args.objective, v, row,
                                       v_ref=v_ref, proj0=_p0, mu=args.orth_mu) / len(idx)
                loss.backward()
                tot += float(loss.detach())
                del res, loss
            opt.step()
            soft.project()
            traj.append({"step": step, "loss": tot})
            if (step + 1) % args.eval_every == 0 or step == 0:
                print(f"[step {step+1}/{args.steps}] loss={tot:+.5f} "
                      f"{soft.diagnostics()} ({time.time()-t0:.0f}s)", flush=True)

    final_train = evaluate(train, "train")
    final_test = evaluate(test, "test")

    # ---- §19.4 rounding probe: does the effect survive discretization? ----
    rounding = None
    ids_hard = soft.argmax_ids()
    if ids_hard is not None:
        with torch.no_grad():
            e_hard = embed_w[ids_hard].float()
        saved = soft.var.data.clone()
        hard_train, hard_test = [], []
        with torch.no_grad():
            for prompts, tag, sink in ((train, "train", hard_train), (test, "test", hard_test)):
                for p in prompts:
                    r = forward_batch(model, embed_w, [p], e_hard, [row])[0]
                    sink.append({"task_id": p.task_id, "pool": tag,
                                 "proj_decision": float(torch.dot(r["h"][row], v_ref)),
                                 "proj_last_suffix": float(torch.dot(r["h_suf"][row], v_ref)),
                                 "obj_decision": float(torch.dot(r["h"][row], v))})
        soft.var.data = saved
        rounding = {"hard_token_ids": [int(x) for x in ids_hard],
                    "train": hard_train, "test": hard_test}

    # ---- generations for the judge (held-out only) ----
    if args.generate:
        gen_path = os.path.join(args.out_dir, "GENERATIONS.jsonl")
        emb = soft.embeddings().detach()
        with open(gen_path, "w") as fh, torch.no_grad():
            for p in test:
                full = torch.cat([embed_w[p.head].unsqueeze(0),
                                  emb.unsqueeze(0).to(embed_w.dtype),
                                  embed_w[p.tail].unsqueeze(0)], dim=1)
                # pad_token_id == eos here, so transformers cannot infer the mask and warns;
                # every position is real (no padding), so pass an explicit all-ones mask.
                attn = torch.ones(full.shape[:2], dtype=torch.long, device=full.device)
                out = model.generate(inputs_embeds=full, attention_mask=attn,
                                     max_new_tokens=args.max_new, do_sample=False,
                                     pad_token_id=tokenizer.pad_token_id)
                txt = tokenizer.decode(out[0], skip_special_tokens=True)
                fh.write(json.dumps({"task_id": p.task_id, "split": args.test_split,
                                     "response": txt}) + "\n")
        print(f"[gen] wrote {gen_path}", flush=True)

    meta = {
        "phase": "P2_softprompt", "model": args.model, "objective": args.objective,
        "param": args.param, "budget": budget, "budget_rel": args.budget_rel,
        "temperature": args.temperature, "init_scale": args.init_scale,
        "n_suffix": args.n_suffix, "steps": args.steps, "lr": args.lr,
        "batch": args.batch, "seed": args.seed,
        "refusal_fit_layer": fit_layer, "hidden_states_index": row,
        "off_by_one_note": "direction L{k} fitted at hidden_states[k+1]; +1 applied here",
        "cos_objective_vs_refusal": cos_ref,
        "n_train": len(train), "n_test": len(test), "train_test_leakage": 0,
        "template_tail_tokens": tail_len,
        "logit_budget": args.lr * args.steps if args.param == "simplex" else None,
        "init_gap": 2 * args.init_scale if args.param == "simplex" else None,
        "budget_sufficient": (bool(args.lr * args.steps > 2 * args.init_scale)
                              if args.param == "simplex" else None),
        "final_diagnostics": soft.diagnostics(),
        "elapsed_s": time.time() - t0,
    }
    meta.update(lm.meta())
    json.dump(meta, open(os.path.join(args.out_dir, "meta.json"), "w"), indent=2)
    json.dump({"baseline_train": baseline_train, "baseline_test": baseline_test,
               "final_train": final_train, "final_test": final_test,
               "rounding": rounding, "trajectory": traj},
              open(os.path.join(args.out_dir, "projections.json"), "w"), indent=2)
    torch.save({"var": soft.var.data.cpu(), "param": args.param,
                "embeddings": soft.embeddings().detach().cpu()},
               os.path.join(args.out_dir, "soft_suffix.pt"))
    dc.write_runmeta(args.out_dir, args=args, extra=meta)
    dc.write_done(args.out_dir, rows_written=len(final_test))

    dtr = np.mean([a["proj_decision"] for a in final_train]) - \
        np.mean([a["proj_decision"] for a in baseline_train])
    dte = np.mean([a["proj_decision"] for a in final_test]) - \
        np.mean([a["proj_decision"] for a in baseline_test])
    print(f"[RESULT] obj={args.objective} param={args.param} "
          f"Dproj_train={dtr:+.4f} Dproj_test={dte:+.4f}", flush=True)
    if rounding:
        dhard = np.mean([a["proj_decision"] for a in rounding["test"]]) - \
            np.mean([a["proj_decision"] for a in baseline_test])
        print(f"[RESULT] rounded(test) Dproj={dhard:+.4f} "
              f"retention={dhard / dte if dte else float('nan'):.3f}", flush=True)
    print(f"[out] {args.out_dir} {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
