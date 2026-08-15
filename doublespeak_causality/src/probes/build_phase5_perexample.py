"""build_phase5_perexample.py — Phase 5 Q3/Q4 per-example patch vectors (plan §9).

The mean-field Q3 is subsumed by Phase 4 (v_bomb IS the unit mean diff-of-means;
verified cos=1.0 — see reports/PHASE5_DECOMPOSITION.md). The *non-redundant*
Phase-5 behavioral test is PER-EXAMPLE component patching: install each example's
OWN decomposed component of its donor shift, not the population mean.

For each matched (doublespeak, donor) example i and band layer L, at the codeword
position, we form Δhᵢ(L) = h_dsᵢ(L) − h_donorᵢ(L) and its components along the
per-layer Bombness direction v_bomb[L] and the (fixed) refusal direction:

    full_i      = Δhᵢ
    bomb_i      = (Δhᵢ · v_bomb) v_bomb
    refusal_i   = (Δhᵢ · r) r
    remainder_i = Δhᵢ − P_plane Δhᵢ        (P_plane = proj onto span(v_bomb, r), QR)
    random_i    = norm-matched(‖bomb_i‖) random, seeded

The GPU harness (built on greenlight) loads this artifact and, when generating for
example i, adds ±arm_i at the band — SUBTRACT from the doublespeak prompt
(necessity) or ADD into the donor prompt (sufficiency). Pure numpy (+torch save),
NO GPU, NO generation. Scalar/vector artifact only — never touches text.

    python -m src.probes.build_phase5_perexample --run <dir> \
        --v-bomb outputs/phase4_directions/v_bomb_clearharm.pt \
        --refusal outputs/stage_gcg_full/refusal_direction_llama_L18.pt \
        --donor benign --band 8-21 --out outputs/phase5_perexample/comp_clearharm.pt
"""
from __future__ import annotations
import argparse, json, os
import numpy as np

POSITIONS_DEFAULT = ["codeword_last", "final_prompt"]
ARMS = ["full", "bomb", "refusal", "remainder", "random"]


def _unit(v):
    n = float(np.linalg.norm(v))
    return v / n if n > 0 else v


def parse_band(s):
    if s is None:
        return list(range(8, 22))
    if "-" in s:
        a, b = s.split("-")
        return list(range(int(a), int(b) + 1))
    return [int(x) for x in s.split(",")]


def build_perexample(acts, triples, vbomb, refusal, band, pos_idx, donor="benign", seed=20260814):
    """Return arms: {arm: {L: ndarray(n_ex, d)}}, plus ordered example_ids."""
    eids = sorted(triples.keys())
    ref = _unit(np.asarray(refusal, dtype=np.float64))
    rng = np.random.default_rng(seed)
    arms = {a: {} for a in ARMS}
    diag = {}
    for L in band:
        if L not in vbomb:
            continue
        vb = _unit(np.asarray(vbomb[L], dtype=np.float64))
        # Orthogonalise refusal against v_bomb so the decomposition is EXACTLY
        # additive and the three arms are mutually orthogonal (v_bomb ⟂ refusal
        # only ~cos 0.09, so a raw dual-projection would double-count the overlap
        # and break bomb+refusal+remainder == full). The 'refusal' arm is thus the
        # refusal direction with its Bombness-aligned part removed.
        ref_perp = _unit(ref - (ref @ vb) * vb)
        full = np.stack([
            acts[triples[e]["doublespeak"], L, pos_idx, :].astype(np.float64)
            - acts[triples[e][donor], L, pos_idx, :].astype(np.float64)
            for e in eids
        ])                                                   # (n, d)
        pb = full @ vb                                       # (n,)
        pr = full @ ref_perp
        bomb = np.outer(pb, vb)                              # (n, d)
        refv = np.outer(pr, ref_perp)
        remainder = full - bomb - refv                       # exact orthogonal complement
        # norm-matched random per example (match ‖bomb_i‖)
        r = rng.standard_normal(full.shape)
        r /= np.linalg.norm(r, axis=1, keepdims=True)
        rand = r * np.linalg.norm(bomb, axis=1, keepdims=True)
        arms["full"][L] = full.astype(np.float32)
        arms["bomb"][L] = bomb.astype(np.float32)
        arms["refusal"][L] = refv.astype(np.float32)
        arms["remainder"][L] = remainder.astype(np.float32)
        arms["random"][L] = rand.astype(np.float32)
        # additivity + energy diagnostics (mean over examples)
        recon_err = float(np.mean(np.linalg.norm(bomb + refv + remainder - full, axis=1)
                                  / (np.linalg.norm(full, axis=1) + 1e-9)))
        diag[L] = {
            "recon_rel_err": recon_err,
            "mean_frac_bomb": float(np.mean(pb ** 2 / (np.sum(full ** 2, 1) + 1e-12))),
            "mean_frac_remainder": float(np.mean(np.sum(remainder ** 2, 1)
                                                 / (np.sum(full ** 2, 1) + 1e-12))),
        }
    return arms, eids, diag


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--v-bomb", required=True)
    ap.add_argument("--refusal", required=True)
    ap.add_argument("--donor", default="benign", choices=["benign", "neutral"])
    ap.add_argument("--band", default="8-21")
    ap.add_argument("--position", default="codeword_last")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    import torch

    acts = np.load(os.path.join(args.run, "acts.npy"))
    items = [json.loads(l) for l in open(os.path.join(args.run, "items.jsonl"))]
    meta = json.load(open(os.path.join(args.run, "RUNMETA.json")))
    positions = meta.get("positions", POSITIONS_DEFAULT)
    pos_idx = positions.index(args.position)
    by = {}
    for i, it in enumerate(items):
        by.setdefault(it.get("example_id"), {})[it.get("condition")] = i
    triples = {e: d for e, d in by.items()
               if {"doublespeak", args.donor} <= set(d.keys())}

    vbd = torch.load(args.v_bomb, map_location="cpu")
    vbomb = {int(L): np.asarray(v) for L, v in vbd["v_bomb"].items()}
    refusal = torch.load(args.refusal, map_location="cpu")
    refusal = refusal.float().numpy() if hasattr(refusal, "float") else np.asarray(refusal)
    band = [L for L in parse_band(args.band) if L in vbomb]

    arms, eids, diag = build_perexample(acts, triples, vbomb, refusal, band, pos_idx,
                                        donor=args.donor)
    max_err = max(d["recon_rel_err"] for d in diag.values())
    print(f"[phase5-perex] {len(eids)} examples | band {band[0]}..{band[-1]} | "
          f"donor={args.donor} | max recon rel-err {max_err:.2e} "
          f"({'OK' if max_err < 1e-5 else 'WARN additivity'})")
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    payload = {
        "example_ids": eids, "layers": band, "position": args.position,
        "donor": args.donor, "arms": {
            a: {L: torch.tensor(arms[a][L]) for L in band} for a in ARMS
        },
        "diag": diag,
        "meta": {"run": args.run, "v_bomb": args.v_bomb, "refusal": args.refusal,
                 "component": "resid_post==hidden_states[L+1]", "seed": 20260814},
    }
    torch.save(payload, args.out)
    print(f"[phase5-perex] saved {args.out} | arms={ARMS}")
    for L in (band[0], band[-1]):
        print(f"  L{L}: frac_bomb={diag[L]['mean_frac_bomb']:.3f} "
              f"frac_remainder={diag[L]['mean_frac_remainder']:.3f}")


if __name__ == "__main__":
    main()
