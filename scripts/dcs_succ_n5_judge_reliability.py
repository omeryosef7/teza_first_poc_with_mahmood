#!/usr/bin/env python3
"""`PR-066` `N5`: the judge's test-retest reliability, measured on BYTE-IDENTICAL prompts.

`PR-066` asked for a re-judge of a random 200-row subset with the cache disabled. The bank supplies
something better, for free, and `C-209` is how it was noticed: **at dose 0 cell A and cell C are
byte-identical prompts** -- with no demonstrations, the demonstration block was the only thing that
distinguished them -- verified 232/232 families (and B/E likewise). So the `tsb66_A_n0` and
`tsb66_C_n0` arms are THE SAME PROMPTS, generated twice and judged twice, in four independent runs.
Their disagreement is the end-to-end reliability of generation + judging on exactly the population
whose ASR this phase reports.

⚠ WHAT THIS MEASURES, PRECISELY. It is NOT judge-only noise. The two arms were GENERATED separately
as well as judged separately, so the disagreement bounds generation + judge jointly. Greedy decoding
should make the generation half deterministic given identical input; whether it did is checked here
(`n_identical_completions`) rather than assumed, because "greedy is deterministic" is a claim about
kernels and batching, not about arithmetic.

GATE. Every run directory is checked for `DONE.json` FIRST. This exists because the first attempt at
this computation ran against a judge directory holding 101 of 226 rows and produced a
plausible-looking 16% disagreement rate and kappa 0.39 -- a wrong number that only the pair count
disclosed (`ENTRY 029`).

USAGE
  python scripts/dcs_succ_n5_judge_reliability.py
  python scripts/dcs_succ_n5_judge_reliability.py --selftest
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def one_complete_run(pattern: str) -> str:
    dirs = [d for d in sorted(glob.glob(pattern)) if os.path.exists(os.path.join(d, "DONE.json"))]
    if not dirs:
        raise SystemExit("REFUSING: no run with DONE.json matches %s. A directory without the "
                         "completeness marker may hold a partial file, and a partial file produces "
                         "a plausible number." % pattern)
    if len(dirs) > 1:
        raise SystemExit("REFUSING: %d completed runs match %s; refusing to pick one by mtime."
                         % (len(dirs), pattern))
    return dirs[0]


def kappa(tt, tf, ft, ff):
    n = tt + tf + ft + ff
    if n == 0:
        return float("nan")
    po = (tt + ff) / n
    pe = ((tt + tf) / n) * ((tt + ft) / n) + ((ft + ff) / n) * ((tf + ff) / n)
    return (po - pe) / (1 - pe) if pe != 1 else float("nan")


def wilson(k, n, z=1.959964):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def selftest() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        print("  %-50s %s" % (name, "PASS" if cond else "FAIL"))
        ok = ok and bool(cond)

    chk("kappa is 1 on perfect agreement", abs(kappa(10, 0, 0, 90) - 1.0) < 1e-12)
    chk("kappa is 0 on chance agreement", abs(kappa(25, 25, 25, 25)) < 1e-12)
    chk("kappa is negative below chance", kappa(0, 50, 50, 0) < 0)
    lo, hi = wilson(15, 93)
    chk("wilson brackets the point estimate", lo < 15 / 93 < hi)
    chk("wilson on zero has lower bound 0", wilson(0, 100)[0] == 0.0)
    try:
        one_complete_run(os.path.join(REPO, "outputs/boombness/judge/__nope__*"))
        chk("refuses when no completed run matches", False)
    except SystemExit:
        chk("refuses when no completed run matches", True)
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm-a", default="A_n0")
    ap.add_argument("--arm-b", default="C_n0")
    ap.add_argument("--bank", default=os.path.join(
        REPO, "data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl"))
    ap.add_argument("--block", default="cds_n0")
    ap.add_argument("--out", default=os.path.join(REPO, "outputs/dcs_succ/n5_judge_reliability.json"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        print("=== selftest ===")
        return selftest()

    cells = {"A_n0": "A", "C_n0": "C", "B_n0": "B", "E_n0": "E"}
    ca, cb = cells[a.arm_a], cells[a.arm_b]

    ja = one_complete_run(os.path.join(REPO, "outputs/boombness/judge/tsb66j_%s_*" % a.arm_a))
    jb = one_complete_run(os.path.join(REPO, "outputs/boombness/judge/tsb66j_%s_*" % a.arm_b))
    ga = one_complete_run(os.path.join(REPO, "outputs/boombness/score_behavior/tsb66_%s_*" % a.arm_a))
    gb = one_complete_run(os.path.join(REPO, "outputs/boombness/score_behavior/tsb66_%s_*" % a.arm_b))

    def rows(d, f="results.jsonl"):
        return {json.loads(l)["prompt_id"]: json.loads(l)
                for l in open(os.path.join(d, f), encoding="utf-8")}

    JA, JB, GA, GB = rows(ja), rows(jb), rows(ga, "gens.jsonl"), rows(gb, "gens.jsonl")

    # family_id -> the two cells' prompt_ids, and the PROMPTS MUST BE IDENTICAL (checked, not assumed)
    fam, n_prompt_mismatch = {}, 0
    for line in open(a.bank, encoding="utf-8"):
        r = json.loads(line)
        if r["query_kind"] == "behavioral" and r["bank_block"] == a.block and r["cell"] in (ca, cb):
            fam.setdefault(r["family_id"], {})[r["cell"]] = r
    pairs = []
    for f, d in fam.items():
        if ca not in d or cb not in d:
            continue
        pa, pb = d[ca]["prompt_id"], d[cb]["prompt_id"]
        if pa not in JA or pb not in JB:
            continue
        if d[ca]["full_prompt"] != d[cb]["full_prompt"]:
            n_prompt_mismatch += 1
            continue
        pairs.append((pa, pb))
    if not pairs:
        raise SystemExit("REFUSING: zero byte-identical judged pairs bound")

    tt = tf = ft = ff = 0
    sdiff, n_ident_gen = [], 0
    for pa, pb in pairs:
        la = bool(JA[pa].get("malicious_at_0.5"))
        lb = bool(JB[pb].get("malicious_at_0.5"))
        tt += la and lb; tf += la and not lb; ft += (not la) and lb; ff += (not la) and (not lb)
        sdiff.append(abs(float(JA[pa]["strongreject_score"]) - float(JB[pb]["strongreject_score"])))
        if pa in GA and pb in GB:
            n_ident_gen += (GA[pa]["generation"] == GB[pb]["generation"])

    n = len(pairs)
    dis = tf + ft
    lo, hi = wilson(dis, n)
    asr_a, asr_b = (tt + tf) / n, (tt + ft) / n
    res = {
        "_label": "PR-066 N5 -- test-retest of GENERATION + JUDGE on byte-identical prompts",
        "arm_a": a.arm_a, "arm_b": a.arm_b,
        "judge_run_a": os.path.basename(ja), "judge_run_b": os.path.basename(jb),
        "gen_run_a": os.path.basename(ga), "gen_run_b": os.path.basename(gb),
        "n_byte_identical_judged_pairs": n,
        "n_pairs_dropped_prompt_text_differed": n_prompt_mismatch,
        "n_identical_completions": n_ident_gen,
        "frac_identical_completions": n_ident_gen / n if n else None,
        "label_table_a_b": {"TT": tt, "TF": tf, "FT": ft, "FF": ff},
        "label_disagreement_rate": dis / n,
        "label_disagreement_wilson95": [lo, hi],
        "observed_agreement": (tt + ff) / n,
        "cohen_kappa": kappa(tt, tf, ft, ff),
        "asr_arm_a": asr_a, "asr_arm_b": asr_b, "abs_asr_difference": abs(asr_a - asr_b),
        "mean_abs_score_difference": sum(sdiff) / len(sdiff),
        "frac_scores_exactly_equal": sum(1 for x in sdiff if x == 0) / len(sdiff),
        "_reading": "the two arms are the SAME prompts, generated twice and judged twice, so this "
                    "bounds generation + judge JOINTLY. No ASR difference smaller than "
                    "abs_asr_difference is a result.",
    }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
