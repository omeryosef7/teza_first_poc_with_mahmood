"""Phase 5 (plan §9) — component-restricted decomposition of the donor shift.

ZERO-GPU / ZERO-GENERATION slice: for matched (doublespeak, benign, neutral)
triples we form the donor activation difference at each layer and partition its
ENERGY into

    Δh = Δh_bomb + Δh_refusal + Δh_other

where Δh_bomb is the component along the validated per-layer Bombness direction
v_bomb[L], Δh_refusal is the component along the (fixed L18) refusal direction,
and Δh_other is the orthogonal remainder. Because v_bomb ⟂ refusal only
approximately (cos 0.06–0.15, BOMBNESS_PROBE_VALIDATION §4), we project onto an
*orthonormalised* basis of span(v_bomb, v_refusal) (QR) so the plane energy is
exact and the remainder is a true orthogonal complement.

This answers the *precondition* to Phase-5 Q1–Q4 before spending any GPU: if the
donor shift Δh carries almost no energy along v_bomb, then "the Bombness
component mediates behaviour" is quantitatively moot. Reuses only artifacts
already on disk (acts.npy, v_bomb_*.pt, refusal_direction_*.pt).

Read-only, scalar-only (norms / fractions / cosines) — never touches generation
text. Run on CPU in the poc_stage2 env:

    python -m src.probes.phase5_decompose --run <extraction_dir> \
        --v-bomb outputs/phase4_directions/v_bomb_clearharm.pt \
        --refusal outputs/stage_gcg_full/refusal_direction_llama_L18.pt
"""
from __future__ import annotations
import argparse, json, os
import numpy as np


# candidate bands from plan §9 (concept-write / refusal-onset / decision)
BANDS = {
    "concept_write_L8_11": [8, 9, 10, 11],
    "refusal_onset_L13_18": [13, 14, 15, 16, 17, 18],
    "decision_L18_22": [18, 19, 20, 21, 22],
}


def _unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def load_triples(run_dir: str):
    """Return acts (n,L,pos,d), and per-condition index lists keyed by example_id."""
    acts = np.load(os.path.join(run_dir, "acts.npy"))
    items = [json.loads(l) for l in open(os.path.join(run_dir, "items.jsonl"))]
    meta = json.load(open(os.path.join(run_dir, "RUNMETA.json")))
    positions = meta["positions"]
    by_eid: dict = {}
    for i, it in enumerate(items):
        eid = it.get("example_id")
        cond = it.get("condition")
        by_eid.setdefault(eid, {})[cond] = i
    # keep only complete triples
    triples = {
        eid: d for eid, d in by_eid.items()
        if {"doublespeak", "benign", "neutral"} <= set(d.keys())
    }
    return acts, items, positions, triples


def alignment_selfcheck(acts, triples, vbomb, pos_idx, donor="neutral"):
    """Recompute diff-of-means (doublespeak - donor) at each layer from acts and
    confirm it aligns with the stored v_bomb[L]. Guards the B9 index-bug class:
    if acts layer axis were misaligned with v_bomb keys, cos would not be ~1."""
    out = {}
    for L, v in vbomb.items():
        ds = np.stack([acts[d["doublespeak"], L, pos_idx, :] for d in triples.values()])
        dn = np.stack([acts[d[donor], L, pos_idx, :] for d in triples.values()])
        dom = _unit(ds.mean(0) - dn.mean(0))
        out[L] = float(np.dot(dom, _unit(np.asarray(v))))
    return out


def decompose(acts, triples, vbomb, refusal, pos_idx, donor="neutral"):
    """Per-layer energy partition of Δh = h_doublespeak - h_<donor>."""
    rows = {}
    ref = _unit(np.asarray(refusal, dtype=np.float64))
    for L, vb in vbomb.items():
        vb = _unit(np.asarray(vb, dtype=np.float64))
        # orthonormal basis for span(vb, ref) via QR (handles non-orthogonality)
        B, _ = np.linalg.qr(np.stack([vb, ref], axis=1))  # (d, k<=2)
        e_tot = e_bomb = e_ref = e_plane = 0.0
        cbomb = []
        cref = []
        n = 0
        for d in triples.values():
            dh = (acts[d["doublespeak"], L, pos_idx, :].astype(np.float64)
                  - acts[d[donor], L, pos_idx, :].astype(np.float64))
            t = float(dh @ dh)
            if t == 0.0:
                continue
            pb = float(dh @ vb)
            pr = float(dh @ ref)
            plane = B.T @ dh                      # coords in the 2D plane
            e_tot += t
            e_bomb += pb * pb
            e_ref += pr * pr
            e_plane += float(plane @ plane)
            nrm = np.sqrt(t)
            cbomb.append(pb / nrm)
            cref.append(pr / nrm)
            n += 1
        rows[L] = {
            "n": n,
            "frac_bomb": e_bomb / e_tot if e_tot else 0.0,
            "frac_refusal": e_ref / e_tot if e_tot else 0.0,
            "frac_plane": e_plane / e_tot if e_tot else 0.0,
            "frac_remainder": 1.0 - (e_plane / e_tot) if e_tot else 0.0,
            "mean_cos_bomb": float(np.mean(cbomb)) if cbomb else 0.0,
            "mean_cos_refusal": float(np.mean(cref)) if cref else 0.0,
        }
    return rows


def band_summary(rows):
    out = {}
    for name, layers in BANDS.items():
        ls = [L for L in layers if L in rows]
        if not ls:
            continue
        out[name] = {
            "layers": ls,
            "frac_bomb": float(np.mean([rows[L]["frac_bomb"] for L in ls])),
            "frac_refusal": float(np.mean([rows[L]["frac_refusal"] for L in ls])),
            "frac_remainder": float(np.mean([rows[L]["frac_remainder"] for L in ls])),
            "mean_cos_bomb": float(np.mean([rows[L]["mean_cos_bomb"] for L in ls])),
            "mean_cos_refusal": float(np.mean([rows[L]["mean_cos_refusal"] for L in ls])),
        }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--v-bomb", required=True)
    ap.add_argument("--refusal", required=True)
    ap.add_argument("--donor", default="neutral", choices=["neutral", "benign"])
    ap.add_argument("--position", default="codeword_last")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    import torch
    acts, items, positions, triples = load_triples(args.run)
    pos_idx = positions.index(args.position)
    vbd = torch.load(args.v_bomb, map_location="cpu")
    vbomb = {int(L): np.asarray(v) for L, v in vbd["v_bomb"].items()}
    refusal = torch.load(args.refusal, map_location="cpu")
    refusal = refusal.float().numpy() if hasattr(refusal, "float") else np.asarray(refusal)

    n_tri = len(triples)
    print(f"[phase5] {n_tri} complete triples | position={args.position} "
          f"idx={pos_idx} | donor={args.donor} | layers={sorted(vbomb)[:3]}..{max(vbomb)}")

    # Index-alignment guard (B9 class): v_bomb was built as diff-of-means
    # (doublespeak - benign), so the recomputed benign-donor diff-of-means MUST
    # align (cos~1) with stored v_bomb at every layer iff the acts layer axis is
    # aligned with the v_bomb keys. This is donor-INDEPENDENT of --donor below.
    selfchk = alignment_selfcheck(acts, triples, vbomb, pos_idx, donor="benign")
    min_cos = min(selfchk.values())
    print(f"[selfcheck] benign diff-of-means vs stored v_bomb cos: "
          f"min={min_cos:.3f} max={max(selfchk.values()):.3f} "
          f"({'OK — layer axis aligned' if min_cos > 0.9 else 'WARN — possible index misalignment'})")

    rows = decompose(acts, triples, vbomb, refusal, pos_idx, donor=args.donor)
    bands = band_summary(rows)

    print("\n  band                    frac_bomb  frac_refusal  frac_remainder  cos_bomb  cos_ref")
    for name, b in bands.items():
        print(f"  {name:<22}  {b['frac_bomb']:.4f}     {b['frac_refusal']:.4f}        "
              f"{b['frac_remainder']:.4f}         {b['mean_cos_bomb']:+.3f}    {b['mean_cos_refusal']:+.3f}")

    result = {
        "run": args.run, "donor": args.donor, "position": args.position,
        "n_triples": n_tri, "selfcheck_min_cos": min_cos,
        "selfcheck_cos_per_layer": selfchk,
        "per_layer": rows, "bands": bands,
    }
    out = args.out or os.path.join(args.run, f"phase5_decompose_{args.donor}_{args.position}.json")
    json.dump(result, open(out, "w"), indent=2)
    print(f"\n[phase5] wrote {out}")


if __name__ == "__main__":
    main()
