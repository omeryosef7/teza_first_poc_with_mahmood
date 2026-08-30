#!/usr/bin/env python
"""rah_analyze_dose.py -- `RBD-PR-005` / `RAH-PR-003`: is the low baseline ASR DOSE- or CONCEPT-driven?

Compares baseline harmful ASR at `n_examples = 8` against `n_examples = 16`, per (model x lexical
pair), on rows judged in the SAME window by the SAME pinned model at the SAME commit
(`RAH-C-003` explains why "same window" and not "same invocation": the two doses live in different
banks and `compare_bank_hashes(strict=True)` refuses a cross-bank join).

WHAT THIS DOES NOT DO. `RBD-PR-005` names NO numeric threshold, no margin, no alpha and no stopping
rule -- its only quantitative phrase is "rises materially". `RAH-PR-003` recorded that this sprint
does NOT invent one after the fact. So this script reports raw counts, ratios and intervals, plus
the MEASURED re-judge drift on the n=8 rows, and states what the design can and cannot resolve. It
emits no pass/fail verdict.

REUSE. Clustering is `common.clustered_proportion_ci` (resamples DOMAINS, the repo's standard);
nothing statistical is reimplemented here. Independent re-derivation lives in
`scripts/rah_verify_dose.py`, which shares no code with this file.

Usage:
  python scripts/rah_analyze_dose.py --out outputs/boombness/rah_phase1b/rah_dose.json
"""
from __future__ import annotations
import argparse
import collections
import glob
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))

SCHEMA = "RAH_DOSE_DIAGNOSTIC/1"

#: (model, pair) -> (n8 judge tag prefix, n16 judge tag prefix, ORIGINAL RBD n8 tag prefix).
#: The original is used ONLY to measure re-judge drift; its ASR is never mixed into a comparison.
CELLS = {
    ("Llama-3.1-8B", "lantern_poison"): ("rahj_plp_n8", "rahj_plp_n16", "rbdplpj_rbdplpA_beh"),
    ("Llama-3.1-8B", "candle_missile"): ("rahj_pcm_n8", "rahj_pcm_n16", "rbdpcmj_rbdpcmA_beh"),
    ("Qwen3-14B", "lantern_poison"): ("rahj_qlp_n8", "rahj_qlp_n16", "rbdqlpj_rbdqlpA_beh"),
    ("Qwen3-14B", "candle_missile"): ("rahj_qcm_n8", "rahj_qcm_n16", "rbdqcmj_rbdqcmA_beh"),
}
EXPECT = {"n8": 80, "n16": 40}


def newest(prefix):
    hits = sorted(glob.glob(os.path.join(ROOT, "outputs/boombness/judge", prefix + "_*")))
    return hits[-1] if hits else None


def load(d):
    return [json.loads(l) for l in open(os.path.join(d, "results.jsonl")) if l.strip()]


def summarize(rows, label, problems):
    """ASR on the COMPLETE population. No filtering of any kind (sprint plan section 9.1)."""
    jm = collections.Counter(r["judge_model_used"] for r in rows)
    st = collections.Counter(r["judge_status"] for r in rows)
    if set(jm) != {"openai/gpt-4o-mini"}:
        problems.append("%s: judge models %r" % (label, dict(jm)))
    if set(st) != {"ok"}:
        problems.append("%s: judge statuses %r" % (label, dict(st)))
    ids = [r["prompt_id"] for r in rows]
    if len(set(ids)) != len(ids):
        problems.append("%s: duplicate prompt_ids" % label)
    k = sum(1 for r in rows if r["malicious_at_0.5"] == 1)
    return {"attacks": k, "n": len(rows), "asr": k / len(rows) if rows else float("nan"),
            "refused": sum(1 for r in rows if r.get("refused")),
            "n_domains": len(set(r["domain"] for r in rows)),
            "cache_hits": sum(1 for r in rows if r.get("judge_cache_hit")),
            "judge_models": dict(jm), "judge_status": dict(st)}


def drift(orig_rows, new_rows):
    """Re-judge instability on byte-identical text, measured on the n=8 rows themselves.

    `judge_cache_hit` rows CANNOT flip -- a cached verdict is replayed, not recomputed -- so the
    honest denominator is the genuinely re-judged subset. Both are reported.
    """
    om = {r["prompt_id"]: r["malicious_at_0.5"] for r in orig_rows}
    nm = {r["prompt_id"]: r["malicious_at_0.5"] for r in new_rows}
    cached = {r["prompt_id"] for r in new_rows if r.get("judge_cache_hit")}
    common = sorted(set(om) & set(nm))
    fresh = [p for p in common if p not in cached]
    up = sum(1 for p in common if nm[p] and not om[p])
    dn = sum(1 for p in common if om[p] and not nm[p])
    up_f = sum(1 for p in fresh if nm[p] and not om[p])
    dn_f = sum(1 for p in fresh if om[p] and not nm[p])
    return {"n_common": len(common), "n_cached": len(common) - len(fresh), "n_fresh": len(fresh),
            "up": up, "down": dn, "flips": up + dn,
            "flip_rate_all": (up + dn) / len(common) if common else float("nan"),
            "flips_fresh": up_f + dn_f, "up_fresh": up_f, "down_fresh": dn_f,
            "flip_rate_fresh": (up_f + dn_f) / len(fresh) if fresh else float("nan"),
            "orig_attacks": sum(om.values()), "new_attacks": sum(nm.values())}


def main():
    import common as cm

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="outputs/boombness/rah_phase1b/rah_dose.json")
    a = ap.parse_args()

    problems, cells = [], {}
    for (model, pair), (t8, t16, torig) in sorted(CELLS.items()):
        d8, d16, dorig = newest(t8), newest(t16), newest(torig)
        if not d8 or not d16:
            # `RAH-C-006` / review S4: a pending cell is a PROBLEM, not a print. Otherwise the
            # producer exits 0 with problems==[] over half the registered population and the
            # verifier PASSes over whatever survived.
            problems.append("%s x %s: PENDING (n8=%s n16=%s)" % (model, pair, bool(d8), bool(d16)))
            print("[dose] %s x %s: PENDING" % (model, pair))
            continue
        r8, r16 = load(d8), load(d16)
        for rr, key in ((r8, "n8"), (r16, "n16")):
            if len(rr) != EXPECT[key]:
                problems.append("%s/%s/%s: %d rows, expected %d"
                                % (model, pair, key, len(rr), EXPECT[key]))
        s8 = summarize(r8, "%s/%s/n8" % (model, pair), problems)
        s16 = summarize(r16, "%s/%s/n16" % (model, pair), problems)

        # `RAH-C-006` / review F5. `clustered_proportion_ci` SILENTLY substitutes an iid Wilson
        # interval when the cluster bootstrap is degenerate (every draw identical, e.g. a 0/40
        # cell), announcing it only on stdout. Publishing that under a clustered name is exactly
        # what its own comment warns against, and it also makes an independent verifier FAIL a
        # correct cell. Capture the provenance and persist it.
        lo8, hi8, k8, d8g = cm.clustered_proportion_ci(
            [r["malicious_at_0.5"] == 1 for r in r8], [r["domain"] for r in r8], return_diag=True)
        lo16, hi16, k16, d16g = cm.clustered_proportion_ci(
            [r["malicious_at_0.5"] == 1 for r in r16], [r["domain"] for r in r16], return_diag=True)

        dr = drift(load(dorig), r8) if dorig else None
        ratio = (s16["asr"] / s8["asr"]) if s8["asr"] > 0 else float("inf")
        cells["%s x %s" % (model, pair)] = {
            "n8": dict(s8, ci_domain_cluster=[lo8, hi8], n_clusters=k8,
                       ci_interval_source=d8g.get("interval_source", "MISSING"),
                       judge_dir=os.path.basename(d8)),
            "n16": dict(s16, ci_domain_cluster=[lo16, hi16], n_clusters=k16,
                        ci_interval_source=d16g.get("interval_source", "MISSING"),
                        judge_dir=os.path.basename(d16)),
            "abs_delta_asr": s16["asr"] - s8["asr"], "ratio_n16_over_n8": ratio,
            "delta_rows_per_40": s16["attacks"] - s8["attacks"] / 2.0,
            "rejudge_drift_on_n8": dr,
            "orig_judge_dir": os.path.basename(dorig) if dorig else None}
        print("[dose] %-13s x %-15s  n8 %2d/%-3d %.4f [%.4f,%.4f]   n16 %2d/%-3d %.4f [%.4f,%.4f]"
              "   ratio %.2fx" % (model, pair, s8["attacks"], s8["n"], s8["asr"], lo8, hi8,
                                  s16["attacks"], s16["n"], s16["asr"], lo16, hi16, ratio))
        if dr:
            print("        re-judge drift on the SAME n8 rows: %d flips / %d fresh (%.4f); "
                  "up %d down %d; %d cached and cannot flip"
                  % (dr["flips_fresh"], dr["n_fresh"], dr["flip_rate_fresh"],
                     dr["up_fresh"], dr["down_fresh"], dr["n_cached"]))

    # Pooled per model, reported SEPARATELY per model (models are replications, never replicates).
    pooled = {}
    for model in sorted({m for m, _ in CELLS}):
        got = [v for k, v in cells.items() if k.startswith(model + " x ")]
        if len(got) != 2:
            continue
        a8 = sum(g["n8"]["attacks"] for g in got); n8 = sum(g["n8"]["n"] for g in got)
        a16 = sum(g["n16"]["attacks"] for g in got); n16 = sum(g["n16"]["n"] for g in got)
        pooled[model] = {"n8_attacks": a8, "n8_n": n8, "n8_asr": a8 / n8,
                         "n16_attacks": a16, "n16_n": n16, "n16_asr": a16 / n16,
                         "ratio": (a16 / n16) / (a8 / n8) if a8 else float("inf"),
                         "note": "pooled over 2 lexical pairs; pairs are NOT independent replicates "
                                 "(shared generator, domain pool and readout)"}
        print("[dose] POOLED %-13s  n8 %d/%d = %.4f   n16 %d/%d = %.4f   ratio %.2fx"
              % (model, a8, n8, a8 / n8, a16, n16, a16 / n16, pooled[model]["ratio"]))

    out = {"schema": SCHEMA, "registration": "RBD-PR-005 executed as RAH-PR-003",
           "no_threshold_note": "RBD-PR-005 names no numeric threshold, margin, alpha or stopping "
                                "rule. None is invented here. Counts, ratios and intervals only.",
           "cells": cells, "pooled_per_model": pooled, "problems": problems,
           "complete": len(cells) == len(CELLS),
           "n_cells_expected": len(CELLS), "n_cells_present": len(cells)}
    os.makedirs(os.path.dirname(os.path.join(ROOT, a.out)), exist_ok=True)
    with open(os.path.join(ROOT, a.out), "w") as f:
        json.dump(out, f, indent=1)
    print("\n[dose] -> %s" % a.out)
    if problems:
        print("[dose] STRUCTURAL PROBLEMS:")
        for p in problems:
            print("   *", p)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
