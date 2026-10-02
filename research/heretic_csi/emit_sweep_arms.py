#!/usr/bin/env python3
"""Emit the P2a rescue-sweep arm plan from a rank-sweep axis .pt, and PRE-FLIGHT-check its keys.

For each requested rank r it resolves:
  * the candidate basis key: `cand_rank1` for r==1 (the inherited KO_AXIS primary), else `cand_pls{r}`;
  * its rank-matched control keys present in the .pt:
      r==1  -> ctrl_orth, ctrl_random{i}, ctrl_shuffled{j}
      r>=2  -> ctrl_random_r{r}_{i}, ctrl_shuffled_pls{r}_{j}
Each control is norm-matched to its own rank's candidate (--rescue-norm-match-key <cand_key>).

Output (stdout): tab-separated `ARMNAME<TAB>BASIS_KEY<TAB>NORMMATCH_KEY<TAB>ROLE<TAB>RANK`, one per line,
candidates before their controls, capped at --nrand random + --nshuf shuffled controls per rank.
Exits non-zero (and prints MISSING) if a requested candidate key is absent — so the slurm fails BEFORE
the expensive cold model load.
"""
from __future__ import annotations
import argparse, sys
import torch


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pt", required=True)
    ap.add_argument("--ranks", required=True, help="comma list, e.g. 1,4,32")
    ap.add_argument("--nrand", type=int, default=8)
    ap.add_argument("--nshuf", type=int, default=4)
    a = ap.parse_args()
    keys = set(torch.load(a.pt, map_location="cpu", weights_only=False)["bases"].keys())
    ranks = [int(x) for x in a.ranks.split(",") if x.strip()]
    missing, lines = [], []
    for r in ranks:
        cand = "cand_rank1" if r == 1 else f"cand_pls{r}"
        if cand not in keys:
            missing.append(cand); continue
        lines.append(f"KO_CAND_r{r}\t{cand}\t\tcandidate\t{r}")
        if r == 1:
            rand = [k for k in (["ctrl_orth"] + [f"ctrl_random{i}" for i in range(50)]) if k in keys]
            shuf = [f"ctrl_shuffled{j}" for j in range(50) if f"ctrl_shuffled{j}" in keys]
        else:
            rand = [f"ctrl_random_r{r}_{i}" for i in range(100) if f"ctrl_random_r{r}_{i}" in keys]
            shuf = [f"ctrl_shuffled_pls{r}_{j}" for j in range(100) if f"ctrl_shuffled_pls{r}_{j}" in keys]
        for i, k in enumerate(rand[:a.nrand]):
            lines.append(f"KO_RND_r{r}_{i}\t{k}\t{cand}\tcontrol_random\t{r}")
        for j, k in enumerate(shuf[:a.nshuf]):
            lines.append(f"KO_SHUF_r{r}_{j}\t{k}\t{cand}\tcontrol_shuffled\t{r}")
    if missing:
        print("MISSING\t" + ",".join(missing), file=sys.stderr)
        return 3
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
