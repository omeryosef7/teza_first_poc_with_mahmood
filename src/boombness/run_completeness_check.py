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

THREE, added §12.28.1 — `gens.jsonl` holds a row that `results.jsonl` never scored. This is the
COMPLEMENT of check 1, not a stronger version of it, and the distinction is the whole point:

    check 1 (expect_n)      sees rows missing from BOTH files.  On d38beh: all 81.
    check 3 (file agreement) sees only rows in ONE file.        On d38beh: 20 of 81, in 7 of the
                                                                11 damaged domains.

So file agreement **understates damage by construction** — the rows that failed hardest are absent
from both files and leave nothing to compare — and it must never be read as a completeness result.
What it adds is the thing check 1 cannot give: WHICH rows crossed, and therefore that generation and
scoring disagree at all. Four of d38beh's eleven damaged domains are invisible to it entirely.

⛔ AND IT DEGENERATES SILENTLY, which was caught in a live sweep before this was mechanised. Gens
dumping is opt-in: **74 of 585 run pairs have a 0-BYTE `gens.jsonl`**, and the natural spelling
(`if gens and gens != results`) passes every one of them while reporting full coverage. So a run
with no gens rows is classified NOT COMPARABLE, counted, and reported — never quietly skipped — and
the comparable count carries its own degenerate-pass floor.

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
    "dcsbk_C_baseline_20260903_001039_2020176":
        "DCS-PR-003: 3 of 380 rows (0.79%) in ONE domain (school_campus|dev, "
        "semantic_forced_choice) raise resolve:occurrence_count_mismatch text=6 tokens=7. This is "
        "the SAME basket-bank tokenisation defect as CDS-C-002, on the forced-choice rows instead "
        "of the behavioral ones, so the prompt_ids differ (fe58e74c6db2c963, 5569ed8ebf385e15, "
        "6720558908e9e2a2) and the counts are one higher. The mechanism is TOKENISATION OF THE "
        "CODEWORD -- fixed per prompt, computable from the tokenizer alone, independent of any "
        "outcome. This run LEDGERED them; the two intervened arms of the same wave (840376, "
        "840377) went FATAL on the identical rows, which is CDS-R-020 reproduced exactly. "
        "SUPERSEDED by 840623/840624/840625, which pass "
        "data/boombness_prompts/exclusions/cds38_basket_bomb_occurrence_mismatch_forcedchoice.txt "
        "to every arm so the exclusion is declared and identical rather than emergent from where "
        "the exception was caught. This dir is kept as the record of the failure, not analysed",
    "d38beh_20260829_022027_2389958":
        "§12.28: disk quota removed 77 of 608 rows (12.7%), concentrated in 11 of 38 domains, and "
        "the ledger's 586 disagrees with the 543 persisted. Kept as the negative example and "
        "superseded by d38beh2; it must never be analysed",
    "cds1A_basket_20260901_191635_1462938":
        "CDS-C-002: 3 of 380 rows (0.79%) in ONE domain (school_campus|dev, slots 0/8/12) raise "
        "resolve:occurrence_count_mismatch text=5 tokens=6, because the basket bank's incidental "
        "repair (baskets=crates, basket=crate) leaves a codeword occurrence that tokenises to six "
        "pieces against five text matches. UNLIKE d38beh the attrition mechanism is TOKENISATION OF "
        "THE CODEWORD, which is fixed per prompt and independent of the outcome -- and the three "
        "prompt ids (f953fbbb2376f8db, 56c76e11095a5d48, 566c998c6df83a30) were named in the log "
        "BEFORE any generation ran, from the tokenizer alone. The cell is analysed at n=377 with "
        "school_campus at 7 rows instead of 10, and that imbalance is stated wherever it is used",
    "tsc1dp_basket_20260902_003952_2408231":
        "TSC-PR-001 / TSC-C-002: the SAME three CDS-C-002 rows, now excluded EXPLICITLY rather than "
        "ledgered. This is the C_demo_processing_only arm of the basket replication, run with "
        "--exclude-prompt-ids data/boombness_prompts/exclusions/"
        "cds38_basket_bomb_occurrence_mismatch.txt (exclude_prompt_ids_sha16=52ba6a6cfc3fe6f6, "
        "n_excluded=3). CDS-R-020: the same tokenisation failure is SKIPPED by the failure ledger "
        "in a baseline arm and FATAL in an intervened one, so the exclusion is declared up front "
        "and identically in every arm instead of emerging from where the exception was caught. "
        "All FIVE arms verified to carry the identical 377 prompt_ids (0 rows either-only against "
        "cds1A_basket_20260901_191635_1462938). The shortfall is one domain, school_campus at 7 "
        "rows instead of 10, it is the same domain in every arm, it is fixed by the tokenizer and "
        "independent of any outcome, and it is stated wherever the cell is used",
    "tsc1c1_basket_20260902_005544_1565940":
        "TSC-PR-001 / TSC-C-002: the SAME three CDS-C-002 rows, now excluded EXPLICITLY rather than "
        "ledgered. This is the CTRL_matched_d1 arm of the basket replication, run with "
        "--exclude-prompt-ids data/boombness_prompts/exclusions/"
        "cds38_basket_bomb_occurrence_mismatch.txt (exclude_prompt_ids_sha16=52ba6a6cfc3fe6f6, "
        "n_excluded=3). CDS-R-020: the same tokenisation failure is SKIPPED by the failure ledger "
        "in a baseline arm and FATAL in an intervened one, so the exclusion is declared up front "
        "and identically in every arm instead of emerging from where the exception was caught. "
        "All FIVE arms verified to carry the identical 377 prompt_ids (0 rows either-only against "
        "cds1A_basket_20260901_191635_1462938). The shortfall is one domain, school_campus at 7 "
        "rows instead of 10, it is the same domain in every arm, it is fixed by the tokenizer and "
        "independent of any outcome, and it is stated wherever the cell is used",
    "tsc1c2_basket_20260902_003917_1554639":
        "TSC-PR-001 / TSC-C-002: the SAME three CDS-C-002 rows, now excluded EXPLICITLY rather than "
        "ledgered. This is the CTRL_matched_d2 arm of the basket replication, run with "
        "--exclude-prompt-ids data/boombness_prompts/exclusions/"
        "cds38_basket_bomb_occurrence_mismatch.txt (exclude_prompt_ids_sha16=52ba6a6cfc3fe6f6, "
        "n_excluded=3). CDS-R-020: the same tokenisation failure is SKIPPED by the failure ledger "
        "in a baseline arm and FATAL in an intervened one, so the exclusion is declared up front "
        "and identically in every arm instead of emerging from where the exception was caught. "
        "All FIVE arms verified to carry the identical 377 prompt_ids (0 rows either-only against "
        "cds1A_basket_20260901_191635_1462938). The shortfall is one domain, school_campus at 7 "
        "rows instead of 10, it is the same domain in every arm, it is fixed by the tokenizer and "
        "independent of any outcome, and it is stated wherever the cell is used",
    "tsc1c3_basket_20260902_005544_1565941":
        "TSC-PR-001 / TSC-C-002: the SAME three CDS-C-002 rows, now excluded EXPLICITLY rather than "
        "ledgered. This is the CTRL_matched_d3 arm of the basket replication, run with "
        "--exclude-prompt-ids data/boombness_prompts/exclusions/"
        "cds38_basket_bomb_occurrence_mismatch.txt (exclude_prompt_ids_sha16=52ba6a6cfc3fe6f6, "
        "n_excluded=3). CDS-R-020: the same tokenisation failure is SKIPPED by the failure ledger "
        "in a baseline arm and FATAL in an intervened one, so the exclusion is declared up front "
        "and identically in every arm instead of emerging from where the exception was caught. "
        "All FIVE arms verified to carry the identical 377 prompt_ids (0 rows either-only against "
        "cds1A_basket_20260901_191635_1462938). The shortfall is one domain, school_campus at 7 "
        "rows instead of 10, it is the same domain in every arm, it is fixed by the tokenizer and "
        "independent of any outcome, and it is stated wherever the cell is used",
}

#: Degenerate-pass floor. If the scan finds fewer runs than this, the SCANNER has broken rather than
#: the corpus having shrunk — the same failure `ledger_propagation_check.MIN_EXPECTED` guards.
MIN_EXPECTED = 50

#: Separate floor for check 3. It must be its OWN number: the comparable population (runs that
#: actually dumped generations) is a different and much smaller set than the expect_n population,
#: and sharing a floor would let one collapse while the other held the count up.
MIN_COMPARABLE = 200


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


def file_agreement(run_dir, rowfile):
    """Rows in `gens.jsonl` that `results.jsonl` never scored. `None` means NOT COMPARABLE.

    Returning `None` rather than a passing verdict is the entire safety property here — see the
    module docstring. An absent or empty `gens.jsonl` means generation dumping was off, which is
    not evidence of agreement and must not be counted as a checked run.

    Only `gen_only` is a defect. `results` legitimately EXCEEDS `gens` when dumping was partial
    (two runs in this corpus are strict subsets that way), so a scored row with no dumped generation
    is expected; a GENERATED row that was never scored is a row that went missing between the two
    stages.
    """
    gp = os.path.join(run_dir, "gens.jsonl")
    if not os.path.isfile(gp) or os.path.getsize(gp) == 0:
        return None
    gens = {r["prompt_id"] for r in _rows(gp) if "prompt_id" in r}
    if not gens:
        return None
    scored = {r["prompt_id"] for r in _rows(os.path.join(run_dir, rowfile)) if "prompt_id" in r}
    if not scored:
        return None
    return gens - scored


def scan_file_agreement():
    """Check 3, over every DONE run — it needs no `expect_n`, so its population is its own."""
    problems, comparable, not_comparable = [], 0, 0
    for root, rowfile in sorted(ROW_FILE.items()):
        for d in sorted(glob.glob(os.path.join(ROOT, "outputs", "boombness", root, "*/"))):
            if not os.path.isfile(os.path.join(d, "DONE.json")):
                continue
            missing = file_agreement(d, rowfile)
            if missing is None:
                not_comparable += 1
                continue
            comparable += 1
            if missing:
                rid = os.path.basename(d.rstrip("/"))
                problems.append((rid, f"{len(missing)} generated rows were NEVER SCORED -- "
                                      f"generation and scoring disagree about which rows exist"))
    return problems, comparable, not_comparable


def is_a_run(run_dir, rowfile):
    """A DONE directory that is actually a generation run, not a fit or export artifact.

    ⛔ THE DISTINCTION THIS DRAWS WAS PREVIOUSLY MADE BY SILENCE (§12.28.4). `scan()` dropped any
    directory whose `config.json` would not parse, with no counter — so `fitN_concept` and three
    siblings, which are fit artifacts carrying neither a config nor a row file, were skipped
    identically to how a REAL run that lost its config would be skipped. The guard printed
    "210 finished runs carry an expect_n", which reads as *not applicable* when it also meant
    *could not tell*. Those two states shared an output line, which a peer named as the general
    form of the `canonical_figures` defect.

    A run is anything that persisted a row file. That splits the cases: no config AND no rows is a
    non-run and is counted as one; no config WITH rows is a run whose expectation cannot be
    recovered, which is a defect.
    """
    return os.path.isfile(os.path.join(run_dir, rowfile))


def scan():
    problems, checked, non_runs = [], 0, []
    for root, rowfile in sorted(ROW_FILE.items()):
        for d in sorted(glob.glob(os.path.join(ROOT, "outputs", "boombness", root, "*/"))):
            if not os.path.isfile(os.path.join(d, "DONE.json")):
                continue
            rid_ = os.path.basename(d.rstrip("/"))
            try:
                cfg = json.load(open(os.path.join(d, "config.json"), encoding="utf-8"))["args"]
            except Exception:
                if is_a_run(d, rowfile):
                    problems.append((rid_, "persisted rows but its config.json is missing or "
                                           "unreadable -- its --expect-n cannot be recovered, so "
                                           "this run is UNCHECKABLE rather than complete"))
                else:
                    non_runs.append(rid_)
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
    return problems, checked, non_runs


def main() -> int:
    problems, checked, non_runs = scan()
    fa_problems, comparable, not_comparable = scan_file_agreement()
    problems += fa_problems
    if checked < MIN_EXPECTED:
        print(f"[run-complete] FAIL — only {checked} runs carried an expect_n, expected at least "
              f"{MIN_EXPECTED}. The scanner has broken; a guard that checks nothing must not pass.")
        return 1
    if comparable < MIN_COMPARABLE:
        print(f"[run-complete] FAIL — only {comparable} runs were COMPARABLE for file agreement, "
              f"expected at least {MIN_COMPARABLE}. Check 3 has collapsed to a no-op.")
        return 1
    print(f"[run-complete] {checked} finished runs carry an expect_n; "
          f"{len(KNOWN_SHORT)} documented short; "
          f"{len(non_runs)} DONE dirs are not runs (no config and no row file)")
    print(f"[run-complete] file agreement: {comparable} runs comparable, {not_comparable} NOT "
          f"comparable (no generations dumped) -- and file agreement sees only one-sided losses, "
          f"never rows missing from both files")
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
