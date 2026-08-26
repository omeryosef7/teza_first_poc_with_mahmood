"""Can a count-matched non-demonstration control be BUILT on this bank? CPU-only, no GPU.

*** QUARANTINED AND THEN FIXED, 2026-08-26 (R-46 -> R-47). ***
The first version reported 0.111/0.158 where the real pre-flight reported 1.0, and it was
quarantined with a GUESSED cause (a templating mismatch). **That guess was wrong.**
`nondemo_control_draw` returns a TUPLE `(positions, record)`, and this script did `len(drawn)` --
which is 2, the tuple's length. Every ratio was therefore `2 / n_demo_keys`: 2/18 = 0.111,
2/13 = 0.154. The demo positions themselves were always correct (13/28/56/114, matching the real
arms exactly), which is precisely why the numbers looked plausible.

The fix takes `match_ratio` from the record the function itself computes rather than recomputing it
here -- a derived quantity should be read from the thing that derived it, not re-derived beside it.

VALIDATED TWICE, 2026-08-26. (a) Against R-24's historical pre-flight on the d10 bank: 1.0 / 0.875 /
0.0 / 0.0 across n_examples 1/2/4/8, reproduced exactly including the 0.875 mean. (b) Against a
LIVE arm on a different bank -- `p13_matched_d1` on `longpre10` -- where this script predicted
min 1.000 at all four doses and the arm's own pre-flight recorded min 1.000 at all four doses, 40
rows each. A prediction that matches a real run on a bank it was not tuned against is the strongest
check available without re-burning the GPU time.

WHY THIS EXISTS. `control_draw_match_ratio` decides whether demonstration-specificity is testable
at a given dose (R-24, R-25), and until now the only way to read it was to submit a GPU arm and let
`score_behavior`'s pre-flight print it -- which on 2026-08-26 meant waiting 3+ hours in a
fair-share queue for a number that needs no model at all. The ratio is pure TOKENIZATION: how many
demonstration positions are there, and how many non-demo positions remain once the query span is
protected.

It reuses the very functions the pre-flight uses -- `resolve_occurrences`, `demo_key_positions`,
`query_span_positions`, `nondemo_control_draw` -- rather than reimplementing the arithmetic, because
a feasibility check that disagrees with the thing it predicts is worse than no check. The
`--verify-against` option asserts exactly that agreement when a real run is available.

Usage
-----
    python src/boombness/control_feasibility.py --bank <bank>.jsonl \
        --model meta-llama/Llama-3.1-8B-Instruct --n-examples 1,2,4,8 --tag feas
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "doublespeak_causality"))

import common  # noqa: E402
import ds_common as dc  # noqa: E402
from extract_boombness import resolve_occurrences  # noqa: E402
from score_behavior import (demo_key_positions, nondemo_control_draw,  # noqa: E402
                            query_span_positions)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", required=True)
    # NO DEFAULT (C-18, 2026-08-26). It used to default to Llama, and every argsfile I wrote
    # omitted it -- so R-49/R-51's "feasible at every dose" was a LLAMA measurement that I then
    # generalised to the method and applied to Qwen3, where the pool is 112 tokens against a
    # 114-token demo block and the control cannot be built at all. Feasibility is a property of
    # (bank, TOKENIZER), never of a bank alone, so the model must be stated every time.
    ap.add_argument("--model", required=True,
                    help="REQUIRED: feasibility depends on the tokenizer, so it cannot be defaulted.")
    ap.add_argument("--n-examples", default="1,2,4,8")
    ap.add_argument("--conditions", default="natural_doublespeak")
    ap.add_argument("--query-kinds", default="behavioral")
    ap.add_argument("--bank-blocks", default="core2x2,core2x2_slot3")
    ap.add_argument("--seed", type=int, default=20260825)
    ap.add_argument("--enable-thinking", default="false")
    ap.add_argument("--tag", default="feas")
    ap.add_argument("--experiment", default="control_feasibility")
    args = ap.parse_args()

    run = common.RunDir(args.experiment, args=args, tag=args.tag)
    ledger = common.FailureLedger()
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(args.model)

    want_ne = {int(x) for x in args.n_examples.split(",") if x.strip()}
    want_c = set(args.conditions.split(","))
    want_q = set(args.query_kinds.split(","))
    want_b = set(args.bank_blocks.split(","))
    thinking = str(args.enable_thinking).lower() in ("1", "true", "yes")

    per_dose = collections.defaultdict(list)
    infeasible = collections.Counter()
    for line in open(args.bank):
        row = json.loads(line)
        if (row.get("n_examples") not in want_ne or row.get("condition") not in want_c
                or row.get("query_kind") not in want_q or row.get("bank_block") not in want_b):
            continue
        try:
            templated, ids, *_ = resolve_occurrences(dc, tok, row, enable_thinking=thinking)
        except Exception as e:                      # noqa: BLE001
            ledger.fail(f"resolve:{type(e).__name__}", row["prompt_id"])
            continue
        dk, reason = demo_key_positions(tok, row, templated)
        if reason:
            ledger.fail(f"demokeys:{reason}", row["prompt_id"])
            continue
        prot = query_span_positions(tok, row, templated, dk)
        rec = {}
        try:
            # NOTE THE UNPACK. This returns (positions, record); `len()` on the tuple is 2 and was
            # the whole of the original defect. `match_ratio` is read from the record the function
            # itself computed -- never re-derived here.
            _pos, rec = nondemo_control_draw(dk, len(ids), protected=prot,
                                             seed=args.seed, policy="strict", log=rec)
            ratio = float(rec.get("match_ratio", 0.0))
        except Exception as exc:                     # noqa: BLE001
            # strict REFUSES a row it cannot count-match; that refusal IS ratio 0, and the
            # function attaches its record to the exception so the reason survives.
            rec = dict(getattr(exc, "record", {}) or {})
            ratio = float(rec.get("match_ratio", 0.0))
            infeasible[row["n_examples"]] += 1
        ledger.ok()
        pool = int(rec.get("n_pool", 0))   # the function's own pool size, not a re-derivation
        per_dose[row["n_examples"]].append(
            {"n_demo": len(dk), "n_drawable_pool": pool, "match_ratio": ratio})

    out_doses = {}
    for v in sorted(per_dose):
        rs = [x["match_ratio"] for x in per_dose[v]]
        out_doses[str(v)] = {
            "n_rows": len(rs),
            "match_ratio_min": min(rs), "match_ratio_mean": sum(rs) / len(rs),
            "n_below_1": sum(1 for r in rs if r < 1.0),
            "feasible_strict": all(r >= 1.0 for r in rs),
            "median_n_demo": statistics.median(x["n_demo"] for x in per_dose[v]),
            # THE MAX IS THE CRITERION, NOT THE MEDIAN (C-18). A strict control must be buildable on
            # EVERY row, so the pool has to clear the LONGEST demo block at the dose. n_preamble=8
            # once gave a pool of 118 against a median of 114 and still failed, because the longest
            # rows reach 128; its mean ratio read a comfortable 0.650 while its min was 0.000.
            "max_n_demo": max(x["n_demo"] for x in per_dose[v]),
            "min_drawable_pool": min(x["n_drawable_pool"] for x in per_dose[v]),
            # CONSERVATIVE BOUND, NOT A PER-ROW DIAGNOSIS. This compares the LONGEST demo block at
            # the dose against the SMALLEST pool at the dose -- and those are usually DIFFERENT ROWS.
            # So it can be positive while every individual row is feasible: on pool B at
            # n_examples=8 it reads 10 (max demo 132 vs min pool 122) while match_ratio_min is
            # 1.000, because the 132-token row has a larger pool than 122. Use it to see how close
            # the bank is to trouble; use match_ratio_min to decide feasibility.
            "pool_deficit_vs_max_demo": max(0, max(x["n_demo"] for x in per_dose[v])
                                            - min(x["n_drawable_pool"] for x in per_dose[v])),
            # THE PER-ROW VERSION, which is the one that actually implies infeasibility.
            "n_rows_demo_exceeds_own_pool": sum(1 for x in per_dose[v]
                                                if x["n_demo"] > x["n_drawable_pool"]),
            "median_drawable_pool": statistics.median(x["n_drawable_pool"] for x in per_dose[v]),
            "n_refused_by_strict_policy": infeasible.get(v, 0),
        }
    out = {"schema": "CONTROL_FEASIBILITY/1", "bank": args.bank, "model": args.model,
           "per_dose": out_doses,
           "all_doses_feasible": all(v["feasible_strict"] for v in out_doses.values()),
           "NOTE": ("match_ratio = drawn keys / demo keys under the STRICT policy, computed from "
                    "tokenization alone. A dose with ratio < 1.0 cannot carry a count-matched "
                    "non-demo control, so demonstration-specificity is untestable there.")}
    path = os.path.join(run.path, "control_feasibility.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    run.finish(summary={"all_doses_feasible": out["all_doses_feasible"]}, ledger=ledger)
    print(f"[feas] wrote {path}")
    for v, c in out_doses.items():
        print(f"  n_examples={v:>2}: rows={c['n_rows']:3d} demo med/MAX={c['median_n_demo']:.0f}/{c['max_n_demo']} "
              f"pool med/MIN={c['median_drawable_pool']:.0f}/{c['min_drawable_pool']} "
              f"deficit={c['pool_deficit_vs_max_demo']} ratio min={c['match_ratio_min']:.3f} "
              f"mean={c['match_ratio_mean']:.3f} feasible={c['feasible_strict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
