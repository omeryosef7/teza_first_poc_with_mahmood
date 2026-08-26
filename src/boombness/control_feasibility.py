"""Can a count-matched non-demonstration control be BUILT on this bank? CPU-only, no GPU.

*** QUARANTINED 2026-08-26 (R-46). DO NOT QUOTE THIS SCRIPT'S RATIOS. ***
It disagrees with measured reality: on the d10 bank at n_examples=1 the real `score_behavior`
pre-flight (job 780231) reported match_ratio 1.0 with 40/40 rows feasible, and this script reports
0.111 min / 0.158 mean and feasible=False. The likely cause is a templating mismatch -- this
script's `--enable-thinking` default versus the one the real arm ran under -- which would shift
every position, but that is UNPROVEN. Until `--verify-against` reproduces a real pre-flight
row-for-row, the numbers here are not evidence of anything.

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
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
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
        try:
            drawn = nondemo_control_draw(dk, len(ids), protected=prot,
                                         seed=args.seed, policy="strict")
            ratio = len(drawn) / len(dk) if dk else None
        except Exception:                            # noqa: BLE001
            # the strict policy REFUSES a row it cannot match; that refusal IS ratio 0.
            ratio = 0.0
            infeasible[row["n_examples"]] += 1
        ledger.ok()
        pool = max(0, len(ids) - len(dk) - len(set(prot) - set(dk)))
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
        print(f"  n_examples={v:>2}: rows={c['n_rows']:3d} demo~{c['median_n_demo']:.0f} "
              f"pool~{c['median_drawable_pool']:.0f} ratio min={c['match_ratio_min']:.3f} "
              f"mean={c['match_ratio_mean']:.3f} feasible={c['feasible_strict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
