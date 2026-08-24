"""retrieval_strength.py — the MEASUREMENT gate for the retrieval account (Phase 7).

R-AI showed the retrieval account makes a prediction the dose account cannot -- knockout effect grows
with `n_examples` -- and it held on both models. That is PREDICTION. This is MEASUREMENT: a per-prompt
scalar for how strongly the generation position actually attends to the demonstration block.

THE CONTROL IS ACROSS LAYERS, NOT ACROSS POSITIONS -- and the first design was wrong.

Draft 1 compared demo-block mass against `knockout_key_set("nondemo_random", ...)`, the repo's
count-matched demo-disjoint draw. The 8-row smoke (job 777298) refuted it immediately:
`demo_mass 0.0374` vs `ctrl_mass 0.2489`, with demo > ctrl in **0 of 4** measurable rows, and 4 of 8
rows unmeasurable (`infeasible_control`). The reason is that a count-matched draw matches SIZE but not
POSITION, and attention is dominated by the BOS sink and by recency: a random non-demo draw collects
sink mass, while the demonstration block sits in the middle distance. The control was measuring
position, not retrieval.

The fix uses the contrast the CAUSAL experiment already validated: the SAME demo positions, in the
SAME prompt, in the band where the knockout works (L6-14 on Llama) versus the late band where the
identical knockout is nearly inert (L20-31, Phase 2's `D_ctrl`). Positional priors are shared by both
bands and largely cancel, no draw can be infeasible, and the scalar is aligned with the causal claim it
is meant to measure: retrieval should be elevated exactly where cutting it changes behaviour.

The count-matched draw is still recorded per row for reference, but it is NOT the headline scalar and
its positional confound is stated in the artifact.

WHAT IS CAPTURED. One eager forward per prompt with `output_attentions=True`, no generation. For each
layer in the band, attention from the final prompt position (the position whose distribution produces
the first generated token), averaged over heads. Scalars only -- no prompt or completion text is
written, in line with every other artifact in this phase.

Run:
  python src/boombness/retrieval_strength.py --bank <bank> --band-lo 6 --band-hi 14 --limit 8
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "doublespeak_causality"))

import ds_common as dc            # noqa: E402
import score_behavior as sb       # noqa: E402
from common import RunDir         # noqa: E402


@torch.no_grad()
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", required=True)
    ap.add_argument("--model", default=None)
    ap.add_argument("--query-kinds", default="behavioral")
    ap.add_argument("--conditions", default="natural_doublespeak")
    ap.add_argument("--bank-blocks", default="core2x2,core2x2_slot3")
    ap.add_argument("--n-examples", default="1,2,4,8")
    ap.add_argument("--band-lo", type=int, default=6)
    ap.add_argument("--band-hi", type=int, default=14)
    ap.add_argument("--late-lo", type=int, default=20)
    ap.add_argument("--late-hi", type=int, default=31)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--expect-n", type=int, default=0)
    ap.add_argument("--enable-thinking", default=None)
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--seed", type=int, default=20260823)
    ap.add_argument("--tag", default="retr")
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.bank)]
    qk = set(args.query_kinds.split(","))
    cond = set(args.conditions.split(","))
    blocks = set(args.bank_blocks.split(","))
    nex = {int(x) for x in args.n_examples.split(",")}
    rows = [r for r in rows if r.get("query_kind") in qk and r.get("condition") in cond
            and r.get("bank_block") in blocks and int(r.get("n_examples", -1)) in nex]
    if args.limit:
        rows = rows[:args.limit]
    if args.expect_n and len(rows) != args.expect_n:
        raise SystemExit(f"[retr] REFUSING: filter yielded {len(rows)} rows, --expect-n {args.expect_n}")
    print(f"[retr] population n={len(rows)}", flush=True)

    model_id = args.model or dc.PRIMARY_MODEL
    et = dc.parse_enable_thinking(args.enable_thinking)
    lm = dc.load_model(model_id, dtype=getattr(torch, args.dtype), attn_implementation="eager")
    n_layers = lm.num_layers
    if not (0 <= args.band_lo <= args.band_hi < n_layers):
        raise SystemExit(f"[retr] REFUSING: band {args.band_lo}-{args.band_hi} outside 0-{n_layers-1} "
                         f"for {model_id}")
    if not (0 <= args.late_lo <= args.late_hi < n_layers):
        raise SystemExit(f"[retr] REFUSING: late band {args.late_lo}-{args.late_hi} outside "
                         f"0-{n_layers-1} for {model_id}")
    band = list(range(args.band_lo, args.band_hi + 1))
    late = list(range(args.late_lo, args.late_hi + 1))
    print(f"[retr] model={model_id} layers={n_layers} band={args.band_lo}-{args.band_hi} "
          f"({len(band)} blocks, depth {args.band_lo/n_layers:.3f}-{(args.band_hi+1)/n_layers:.3f})",
          flush=True)

    run = RunDir("retrieval_strength", args=args, tag=args.tag)
    run.note(bank=args.bank, model=model_id, band=[args.band_lo, args.band_hi],
             late_band=[args.late_lo, args.late_hi], population_n=len(rows), enable_thinking=et,
             headline_scalar="demo_mass(band) - demo_mass(late_band), same positions same prompt",
             control_note="count_matched nondemo_random is ALSO recorded but is positionally "
                          "confounded (BOS sink + recency) and is NOT the headline -- see docstring")
    from common import FailureLedger
    ledger = FailureLedger()

    out, skipped = [], {}
    for i, r in enumerate(rows):
        templated = dc.apply_template(lm.tokenizer, r["full_prompt"], enable_thinking=et)
        dk, why = sb.demo_key_positions(lm.tokenizer, r, templated)
        if why:
            skipped[why] = skipped.get(why, 0) + 1
            continue
        ids = lm.tokenizer(templated, add_special_tokens=False, return_tensors="pt")["input_ids"]
        seq_len = int(ids.shape[1])
        try:
            ctrl = sb.knockout_key_set("nondemo_random", dk, seq_len, args.seed + i)
        except sb.InfeasibleControl:
            ctrl = None      # reference-only; never a reason to drop a row
        o = lm.model(input_ids=ids.to(lm.model.device), output_attentions=True, use_cache=False)
        q = seq_len - 1                       # the position that emits the first generated token
        d_idx = torch.tensor(dk, device=o.attentions[0].device)
        c_idx = (torch.tensor(ctrl, device=o.attentions[0].device) if ctrl is not None else None)
        def _mass(layers, idx, per_head=False):
            v, ph = [], {}
            for L in layers:
                a = o.attentions[L][0, :, q, :]        # (heads, kv)
                h = a[:, idx].sum(-1)                  # (heads,)
                v.append(float(h.mean()))
                if per_head:
                    ph[str(L)] = [float(x) for x in h]
            return (v, ph) if per_head else v
        # PER-HEAD, added after R-AK. Band-level mass ANTI-predicts causal importance on Qwen3
        # (band 0.0316 vs late 0.0416 while the band knockout is 2.7x stronger). A band average can
        # hide a small set of heads that do carry retrieval, so the head vectors are kept.
        dmass, dhead = _mass(band, d_idx, per_head=True)
        lmass, lhead = _mass(late, d_idx, per_head=True)   # SAME positions, late band
        cmass = _mass(band, c_idx) if ctrl is not None else []
        dm = sum(dmass) / len(dmass)
        lm_ = sum(lmass) / len(lmass)
        cm = (sum(cmass) / len(cmass)) if cmass else None
        out.append({"prompt_id": r["prompt_id"], "domain": r.get("domain"),
                    "n_examples": int(r.get("n_examples")), "split": r.get("split"),
                    "n_demo_keys": len(dk), "seq_len": seq_len,
                    "demo_mass_band": dm, "demo_mass_late": lm_,
                    "retrieval_strength": dm - lm_,          # HEADLINE
                    "retrieval_ratio": (dm / lm_) if lm_ > 0 else None,
                    "ctrl_mass_band_REFERENCE_ONLY": cm,
                    "per_layer_demo_band": dict(zip(map(str, band), dmass)),
                    "per_layer_demo_late": dict(zip(map(str, late), lmass)),
                    "per_head_band": dhead, "per_head_late": lhead,
                    "band_head_max": max(max(v) for v in dhead.values()),
                    "late_head_max": max(max(v) for v in lhead.values())})
        if (i + 1) % 24 == 0:
            print(f"[retr] {i+1}/{len(rows)}", flush=True)
        del o

    with open(os.path.join(run.path, "retrieval.jsonl"), "w") as fh:
        for rec in out:
            fh.write(json.dumps(rec) + "\n")
    if not out:
        raise SystemExit("[retr] REFUSING: no rows measured")
    ds = [x["demo_mass_band"] for x in out]; ls = [x["demo_mass_late"] for x in out]
    summ = {"n": len(out), "skipped": skipped,
            "demo_mass_band_mean": sum(ds) / len(ds),
            "demo_mass_late_mean": sum(ls) / len(ls),
            "retrieval_strength_mean": sum(ds) / len(ds) - sum(ls) / len(ls),
            "frac_rows_band_gt_late": sum(1 for x in out if x["demo_mass_band"] > x["demo_mass_late"]) / len(out),
            "band_head_max_mean": sum(x["band_head_max"] for x in out) / len(out),
            "late_head_max_mean": sum(x["late_head_max"] for x in out) / len(out),
            "frac_rows_bandHeadMax_gt_lateHeadMax":
                sum(1 for x in out if x["band_head_max"] > x["late_head_max"]) / len(out)}
    print(f"[retr] {json.dumps(summ)}", flush=True)
    run.finish(summary=summ, ledger=ledger)
    print(f"[retr] -> {run.path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
