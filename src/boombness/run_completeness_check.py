"""run_completeness_check.py — a run that FINISHED but did not persist all its rows.

THE FAILURE THIS EXISTS FOR, and it is not hypothetical. `d38beh_20260829_022027_2389958` carries a
`DONE.json`, wrote a terminal verdict and parses cleanly. It is missing **77 of 608 rows** because a
shared filesystem hit a disk quota mid-run. Every automated check in this repo accepted it.

**`score_behavior.py` already has an `--expect-n` check — and it did not fire.** That check counts
the BANK rows selected before generation (line ~1323); this one counts the rows actually PERSISTED
after it. 608 rows were selected and 543 were written, and nothing compared those two numbers.

TWO CHECKS, because the run's own bookkeeping was also wrong:

  1. `results.jsonl` rows >= `args.expect_n`.
  2. `results.jsonl` rows >= the failure ledger's `n_succeeded`. On d38beh the ledger claimed 586
     succeeded while 543 were written: the quota killed writes AFTER rows were counted successful,
     so **a guard trusting the ledger would have passed it**. The files are the authority.

WHAT THIS GUARD CANNOT DO, stated because §12.28 turns on it: it detects that rows are MISSING. It
cannot tell whether their absence is biased, and on d38beh it was — the attrition mechanism was
write volume while the outcome was attack success, which is the same thing as generation length.
That judgement lives in the plan, not here. This guard is the mechanical half only.

Surveyed at introduction: 200 DONE runs carry an `expect_n`; **199 are complete and 1 is short**, so
this is a narrow check and not a source of routine noise.

Reads run directories only. No model, no network.
"""
from __future__ import annotations

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
#: The row file is NAMED PER ROOT, not assumed. The first run of this guard reported four
#: `retrieval_strength` runs as holding 0 rows; they hold 96, in `retrieval.jsonl`. Assuming
#: "results.jsonl" everywhere is the same select-by-a-pattern-I-supplied failure this guard exists
#: to catch, committed inside the guard itself.
ROW_FILE = {
    "score_behavior": "results.jsonl",
    "extract_boombness": "results.jsonl",
    "retrieval_strength": "retrieval.jsonl",
}

#: Runs known to be short, with the reason. A short run is not automatically a defect — but silence
#: about one is. Same convention as `ledger_propagation_check.METHOD_ONLY`.
KNOWN_SHORT = {
    "d38beh_20260829_022027_2389958":
        "§12.28: disk quota removed 77 of 608 rows (12.7%), concentrated in 11 of 38 domains, and "
        "the ledger's 586 disagrees with the 543 persisted. Kept as the negative example and "
        "superseded by d38beh2; it must never be analysed",
}

#: Degenerate-pass floor. If the scan finds fewer runs than this, the SCANNER has broken rather than
#: the corpus having shrunk — the same failure `ledger_propagation_check.MIN_EXPECTED` guards.
MIN_EXPECTED = 50


def _rows(path):
    try:
        return [json.loads(l) for l in open(path, encoding="utf-8")]
    except Exception:
        return []


def cell_imbalance(rows):
    """Modal (domain x n_examples) cell count, and how many cells fall short of it.

    A peer's suggestion and the better of the two checks here: it needs NO expectation about
    totals, is derivable from the file alone, and fails loudly on exactly the shape that made
    d38beh dangerous -- 27 of 38 domains whole and 11 partial. It does not catch uniform loss, but
    uniform loss is the benign case; non-uniform loss is what biases a clustered analysis.
    """
    cells = {}
    for r in rows:
        d, n = r.get("domain"), r.get("n_examples")
        if d is None or n is None:
            return None
        cells[(d, n)] = cells.get((d, n), 0) + 1
    if len(cells) < 4:
        return None
    modal = max(set(cells.values()), key=list(cells.values()).count)
    short = [c for c, v in cells.items() if v < modal]
    return modal, len(cells), len(short)


def scan():
    problems, checked = [], 0
    for root, rowfile in sorted(ROW_FILE.items()):
        for d in sorted(glob.glob(os.path.join(ROOT, "outputs", "boombness", root, "*/"))):
            if not os.path.isfile(os.path.join(d, "DONE.json")):
                continue
            try:
                cfg = json.load(open(os.path.join(d, "config.json"), encoding="utf-8"))["args"]
            except Exception:
                continue
            expect = cfg.get("expect_n")
            if not expect:
                continue
            checked += 1
            rid = os.path.basename(d.rstrip("/"))
            rows = _rows(os.path.join(d, rowfile))
            n = len(rows)
            if n < expect:
                problems.append((rid, f"persisted {n} rows in {rowfile} against --expect-n {expect}"))
                continue
            succeeded = None
            try:
                succeeded = json.load(open(os.path.join(d, "summary.json"),
                                           encoding="utf-8"))["failures"]["n_succeeded"]
            except Exception:
                pass
            if succeeded and n < succeeded:
                problems.append((rid, f"persisted {n} rows but its ledger claims {succeeded} "
                                      f"succeeded -- the files are the authority"))
                continue
            ci = cell_imbalance(rows)
            if ci and ci[2]:
                problems.append((rid, f"{ci[2]} of {ci[1]} (domain x dose) cells hold fewer than "
                                      f"the modal {ci[0]} rows -- loss is NON-UNIFORM, which is "
                                      f"what biases a clustered analysis"))
    return problems, checked


def main() -> int:
    problems, checked = scan()
    if checked < MIN_EXPECTED:
        print(f"[run-complete] FAIL — only {checked} runs carried an expect_n, expected at least "
              f"{MIN_EXPECTED}. The scanner has broken; a guard that checks nothing must not pass.")
        return 1
    print(f"[run-complete] {checked} finished runs carry an expect_n; "
          f"{len(KNOWN_SHORT)} documented short")
    ok = True
    for rid, why in problems:
        if rid in KNOWN_SHORT:
            continue
        ok = False
        print(f"  SHORT {rid}: {why}")
        print("      -> a DONE.json does not mean the rows are there. Rerun it, or document it in "
              "KNOWN_SHORT with why the shortfall is acceptable.")
    if not ok:
        print("[run-complete] FAIL — a finished run did not persist all its rows.")
        return 1
    print("[run-complete] every finished run persisted its full row count")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
