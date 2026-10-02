#!/usr/bin/env python3
"""Rank-r subspace bases for the P2a activation-space rescue rank-sweep, in the EXACT format the
frozen CSI rescue harness consumes.

REUSE / PROVENANCE. The rescue `h' = h_ko + P(h_clean - h_ko)` and the rank test are already
implemented in `src/boombness/score_behavior.py` (rescue arm) and `scripts/dcs_csi_subspace_analyze.py`
(rank test vs the 46-control family). Both consume a basis file written by `scripts/dcs_csi_axis.py`
(`save_bases`): `torch.save({"meta": meta, "bases": {key: Tensor[r, hidden]}}, path)`, float32, with
`meta["bases"][key] = {"rank", "sha16"}` and `meta["bases_sha16_of"]="saved_float32_tensor_bytes"`.

This module adds exactly the two pieces P2a needs and the inherited work lacked at rank>1:
  1. `random_orthonormal_basis` — the RANK-MATCHED control. CSI's rank-5 PLS was a NEGATIVE precisely
     because a random rank-5 subspace beat it; a rank-k candidate must be scored against random rank-k,
     never against a rank-1 null. This is that control, orthonormal and seedable.
  2. `save_basis` — writes a basis in the byte-exact `dcs_csi_axis` format so score_behavior and
     subspace_analyze accept it with zero changes.
`pls1` is reproduced from `scripts/dcs_csi_axis.py:pls1` (the project's own code, WITH deflation — the
deflation is load-bearing; without it 'rank r' collapses to rank 1). We copy rather than import because
dcs_csi_axis.py runs module-load side effects (`_load(...)`); the function is 20 lines of pure torch.

Pure torch; no GPU needed to build a basis (features come from the extracted clean reps).
"""
from __future__ import annotations

import hashlib
from typing import Dict

import torch


def sha16(t: torch.Tensor) -> str:
    """Byte hash of the persisted float32 tensor (matches dcs_csi_axis.sha16)."""
    return hashlib.sha256(t.to(torch.float32).contiguous().numpy().tobytes()).hexdigest()[:16]


def pls1(X: torch.Tensor, y: torch.Tensor, r: int) -> torch.Tensor:
    """PLS1 (NIPALS) rank-r weight matrix [r, hidden] WITH DEFLATION.

    Provenance: scripts/dcs_csi_axis.py:pls1 (copied; project code, not AGPL). Deflation is the point:
    without deflating X every component collapses onto the same direction (rank-1 wearing a hat)."""
    Xr = X.clone().double()
    yr = y.clone().double()
    W = []
    for _ in range(r):
        w = Xr.T @ yr
        n = w.norm()
        if float(n) < 1e-12:
            break
        w = w / n
        t = Xr @ w
        tt = float(t @ t)
        if tt < 1e-18:
            break
        p = (Xr.T @ t) / tt
        Xr = Xr - torch.outer(t, p)
        yr = yr - (float(t @ yr) / tt) * t
        W.append(w)
    if not W:
        raise ValueError("pls1 produced no components")
    return torch.stack(W, 0).to(X.dtype)


def random_orthonormal_basis(r: int, hidden: int, seed: int, device="cpu",
                             dtype=torch.float32) -> torch.Tensor:
    """A random rank-r orthonormal subspace [r, hidden] — the RANK-MATCHED control for a rank-r
    candidate. Rows are orthonormal (so the projector P = BᵀB onto span(B) is a true rank-r
    projection, matching how the candidate basis is used)."""
    if r > hidden:
        raise ValueError(f"rank {r} > hidden {hidden}")
    g = torch.Generator(device=device).manual_seed(int(seed))
    M = torch.randn(hidden, r, generator=g, device=device, dtype=dtype)
    Q = torch.linalg.qr(M).Q            # [hidden, r], orthonormal columns
    return Q.t().contiguous()           # [r, hidden], orthonormal rows


def random_orthonormal_family(r: int, hidden: int, n: int, base_seed: int, key: str,
                              device="cpu", dtype=torch.float32) -> Dict[str, torch.Tensor]:
    """A family of `n` independent rank-r orthonormal controls, keyed `<key>__rand<i>`.
    Distinct seeds per draw (base_seed+i) — the seed MUST reach the draw (CSI retraction #7: a
    dropped control seed produced byte-identical 'controls' and a fake n=1 band)."""
    return {f"{key}__rand{i}": random_orthonormal_basis(r, hidden, base_seed + i, device, dtype)
            for i in range(n)}


def save_basis(bases: Dict[str, torch.Tensor], meta: dict, path: str) -> dict:
    """Write bases in the byte-exact dcs_csi_axis format. Downcast FIRST, hash the downcast tensors,
    then save those same objects (dcs_csi_axis.save_bases order — the hash is a property of the file)."""
    saved = {k: B.to(torch.float32).contiguous() for k, B in bases.items()}
    meta = dict(meta)
    meta["bases"] = {k: {"rank": int(saved[k].shape[0]), "sha16": sha16(saved[k])} for k in saved}
    meta["bases_sha16_of"] = "saved_float32_tensor_bytes"
    torch.save({"meta": meta, "bases": saved}, path)
    return meta


def load_basis(path: str):
    """Load a basis file; returns (meta, bases_dict). Mirrors how score_behavior reads it."""
    obj = torch.load(path, map_location="cpu", weights_only=False)
    return obj["meta"], obj["bases"]
