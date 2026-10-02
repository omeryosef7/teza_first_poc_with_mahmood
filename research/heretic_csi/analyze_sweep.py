#!/usr/bin/env python3
"""P2a analysis harness: run dcs_csi_subspace_analyze.py per rank and collect the rescue-vs-rank curve.

For each rank r it builds the arm list (liveness BASE/KO/KO_SELF/KO_FULL + candidate KO_CAND_r{r} + that
rank's KO_RAND_/KO_SHUF_ controls, resolved by emit_sweep_arms.py), calls the frozen analyzer (which
computes the sufficiency recovery fraction + the rank test vs the control family), and tabulates
rank -> recovery_fraction, rank_p, verdict. The analyzer and its rank test are REUSED unchanged.

Usage:
  python analyze_sweep.py --pt configs/heretic_csi/hcsi_ranksweep_basket.pt \
    --codeword basket --tag-prefix hcsi_p2a_basket --ranks 1,4,32 --expect-n 24 \
    --split train --nrand 6 --nshuf 2 --out-dir reports/heretic_csi
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys

ROOT = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
PY = "/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python"
LIVENESS = ["BASE", "KO", "KO_SELF", "KO_FULL"]


def rank_arms(pt, rank, nrand, nshuf):
    out = subprocess.run([PY, os.path.join(ROOT, "research/heretic_csi/emit_sweep_arms.py"),
                          "--pt", pt, "--ranks", str(rank), "--nrand", str(nrand), "--nshuf", str(nshuf)],
                         capture_output=True, text=True, cwd=ROOT)
    if out.returncode != 0:
        raise SystemExit(f"emit_sweep_arms failed for rank {rank}: {out.stderr}")
    names = [ln.split("\t")[0] for ln in out.stdout.strip().splitlines() if ln.strip()]
    return names  # KO_CAND_r{r}, KO_RAND_r{r}_*, KO_SHUF_r{r}_*


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pt", required=True)
    ap.add_argument("--codeword", required=True)
    ap.add_argument("--tag-prefix", required=True)
    ap.add_argument("--ranks", required=True)
    ap.add_argument("--expect-n", type=int, required=True)
    ap.add_argument("--split", default="train")
    ap.add_argument("--nrand", type=int, default=46)
    ap.add_argument("--nshuf", type=int, default=10)
    ap.add_argument("--option-mass-floor", default="0.05")
    ap.add_argument("--out-dir", default="reports/heretic_csi")
    a = ap.parse_args()
    os.makedirs(os.path.join(ROOT, a.out_dir), exist_ok=True)
    ranks = [int(x) for x in a.ranks.split(",") if x.strip()]
    rows = []
    for r in ranks:
        sweep = rank_arms(a.pt, r, a.nrand, a.nshuf)
        cand = f"KO_CAND_r{r}"
        comparator = next((s for s in sweep if s.startswith(f"KO_RAND_r{r}_")), cand)
        arms = LIVENESS + sweep
        outj = os.path.join(ROOT, a.out_dir, f"{a.tag_prefix}_r{r}.json")
        cmd = [PY, os.path.join(ROOT, "scripts/dcs_csi_subspace_analyze.py"),
               "--codeword", a.codeword, "--tag-prefix", a.tag_prefix,
               "--expect-n", str(a.expect_n), "--arms", ",".join(arms),
               "--candidate-arm", cand, "--comparator-arm", comparator,
               "--control-prefixes", "KO_SHUF,KO_RAND", "--split", a.split,
               "--direction", "sufficiency", "--option-mass-floor", a.option_mass_floor,
               "--out", outj]
        print(f"\n=== rank {r}: candidate={cand} n_controls={len(sweep)-1} ===", flush=True)
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        sys.stdout.write(res.stdout[-2000:])
        if res.returncode != 0:
            sys.stderr.write(res.stderr[-2000:])
            rows.append({"rank": r, "status": "ANALYZER_ERROR"})
            continue
        try:
            d = json.load(open(outj))
            rows.append({"rank": r,
                         "recovery_fraction": d.get("recovery_fraction_candidate_of_full"),
                         "rank_p": (d.get("specificity_test") or {}).get("rank_p"),
                         "verdict": d.get("VERDICT")})
        except Exception as e:
            rows.append({"rank": r, "status": f"PARSE_ERR {e}"})
    print("\n==== RESCUE-vs-RANK SUMMARY (", a.codeword, a.split, ") ====")
    for row in rows:
        print(json.dumps(row))
    summ = os.path.join(ROOT, a.out_dir, f"{a.tag_prefix}_SUMMARY_{a.split}.json")
    json.dump({"codeword": a.codeword, "split": a.split, "rows": rows}, open(summ, "w"), indent=2)
    print("wrote", summ)


if __name__ == "__main__":
    main()
