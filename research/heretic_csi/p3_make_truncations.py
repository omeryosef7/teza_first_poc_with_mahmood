#!/usr/bin/env python3
"""P3 interventions (factor construction only, CPU): SVD TRUNCATION and single-component REMOVAL of a learned
P2b operator, written in F2's factors format so p2b_runner applies them via `op:<file>:<KEY>` unchanged.

Per module ΔW = U S V^T (exact, from the factors). Keys written:
  TOP{k}       sum of the top-k singular components of EVERY module (raw: its norm is <= the full ΔW's)
  TOP{k}N      same directions, each module rescaled to the FULL operator's per-module Frobenius norm
               (separates "which directions" from "how much norm"); declared variant
  DROP{i}      full ΔW minus component i (1-based, per module, ordered by singular value) -- necessity of
               component i; raw (norm decreases)
  REEXP        the original operator re-expressed (sanity: must reproduce KO_CAND within numerical tolerance)
k in {1,2,4,8} with k < rank; i in 1..min(rank,4). Controls are generated at run time by the runner's
`rand:<file>:<KEY>:<seed>` (rank-k, per-module norm-matched to that key) -- see p3p4_emit.py.
"""
import argparse, os, sys
import torch

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "research", "heretic_csi"))
import p2b_operator as po          # noqa: E402
from p3_svd_analysis import svd_factored  # noqa: E402


def components(fac):
    return {n: svd_factored(A, B) for n, (A, B) in fac.items()}


def build(fac, keep):
    """keep(n, S) -> index tensor of components to keep; returns factors (A=diag(S)V^T, B=U) float32."""
    out = {}
    C = components(fac)
    for n, (U, S, V) in C.items():
        idx = keep(n, S)
        out[n] = ((torch.diag(S[idx]) @ V[:, idx].t()).float(), U[:, idx].float())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--factors", required=True, help="F2 factors_<cw>_r<R>.pt")
    ap.add_argument("--key", default="CAND")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    blob = torch.load(a.factors, map_location="cpu")
    fac = blob["operators"][a.key]["factors"]
    r = next(iter(fac.values()))[0].shape[0]
    full_n = {n: po.fro_norm(A, B) for n, (A, B) in fac.items()}
    ops = {"REEXP": {"factors": build(fac, lambda n, S: torch.arange(len(S))), "meta": {"from": a.key, "note": "CAND re-expressed from its SVD; must reproduce KO_CAND (named REEXP, not FULL, to avoid clashing with the KO_FULL whole-state-rescue liveness arm)"}}}
    for k in (1, 2, 4, 8):
        if k < r:
            t = build(fac, lambda n, S, k=k: torch.arange(min(k, len(S))))
            ops[f"TOP{k}"] = {"factors": t, "meta": {"from": a.key, "k": k, "renorm": False}}
            ops[f"TOP{k}N"] = {"factors": po.rescale_to(t, full_n), "meta": {"from": a.key, "k": k, "renorm": "per-module to FULL"}}
    if r >= 2:
        for i in range(1, min(r, 4) + 1):
            ops[f"DROP{i}"] = {"factors": build(fac, lambda n, S, i=i: torch.tensor([j for j in range(len(S)) if j != i - 1], dtype=torch.long)),
                               "meta": {"from": a.key, "removed_component": i}}
    # sanity: FULL reproduces the original ΔW
    for n, (A, B) in fac.items():
        A2, B2 = ops["REEXP"]["factors"][n]
        d = (B.double() @ A.double() - B2.double() @ A2.double()).norm() / max(1e-12, full_n[n])
        if d > 1e-4:
            raise SystemExit(f"REEXP re-expression mismatch {n}: rel {d:.2e}")
    for key, o in ops.items():
        o["meta"]["raw_fro"] = {n: po.fro_norm(A, B) for n, (A, B) in o["factors"].items()}
    torch.save({"operators": ops, "provenance": {"source": a.factors, "source_key": a.key, "rank": r}}, a.out)
    print("P3_TRUNC_DONE", a.out, sorted(ops))


if __name__ == "__main__":
    main()
