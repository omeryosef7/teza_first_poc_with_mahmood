"""Does crossing codeword/concept pairs break PC1 dominance? (Phase 5 bank-acceptance gate.)

WHY. The single-pair 2x2 bank puts ~0.82 of the centred cell-mean variance into ONE component, so
`d_surface` is essentially PC1 and no direction orthogonal to it can reach within 6-12x of its dose.
That is why "same dose, different direction" is not constructible on this bank -- retraction R-25 and
correction C-2 are both consequences of it.

This measures the fix BEFORE building a new bank, by pooling the cell means of three pairs that were
already fitted (carrot/bomb, carrot/knife, button/bomb). No GPU, no new generation.

The reported quantity is not the spectrum for its own sake but `arm / max_complement_dose`: the best
dose ANY direction orthogonal to the arm can achieve. That is the number an in-subspace control is
bounded by, and therefore the number the bank-acceptance gate should be written against.

CAVEAT, stated in the artifact too: pooling three separate banks is not the same object as one bank
with crossed pairs. Each was centred within its own row-set. Same model / layers / extraction config
makes the pooling reasonable, but a real Phase 5 bank must be built and measured, not simulated here.
"""
from __future__ import annotations

import argparse
import json
import os

import torch

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_FITS = {
    "carrot_bomb": "full_20260816_185942_1008673",
    "carrot_knife": "knifefit_20260821_135218_4045492",
    "button_bomb": "buttonfit_20260821_150557_1157907",
}


def _centred(payload, layer):
    cm = payload["cell_means"]
    M = torch.stack([cm[c][layer].reshape(-1) for c in sorted(cm)]).double()
    return M - M.mean(0, keepdim=True)


def spectrum(M):
    s = torch.linalg.svdvals(M)
    v = s ** 2
    tot = float(v.sum())
    return [float(x) / tot for x in v if float(x) / tot > 1e-12]


def dose_of(M, u):
    u = u.double().reshape(-1)
    u = u / u.norm()
    return float(((M @ u) ** 2).sum()) / float((M ** 2).sum())


def max_complement_dose(M, u):
    """Top eigenvalue of the cloud with u removed: the ceiling an orthogonal control can reach."""
    u = u.double().reshape(-1)
    u = u / u.norm()
    Mp = M - (M @ u.reshape(-1, 1)) @ u.reshape(1, -1)
    return float(torch.linalg.svdvals(Mp)[0] ** 2) / float((M ** 2).sum())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--layers", default="6,8,10,12,18")
    ap.add_argument("--arm-pair", default="carrot_bomb", help="whose d_surface is the arm")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    layers = [int(x) for x in a.layers.split(",")]
    P = {k: torch.load(os.path.join(REPO, "outputs/boombness/extract_boombness", v,
                                    "directions_fit_dev.pt"), map_location="cpu",
                       weights_only=False) for k, v in DEFAULT_FITS.items()}
    out = {"question": "does crossing codeword/concept pairs break PC1 dominance of the cell-mean cloud?",
           "fits": DEFAULT_FITS, "arm_pair": a.arm_pair, "layers": layers,
           "caveat": ("pooling three separately-fitted banks is not the same object as one bank with "
                      "crossed pairs; each was centred within its own row-set. Same model/layers/"
                      "extraction config makes it reasonable, but a real Phase 5 bank must be built "
                      "and measured rather than simulated this way."),
           "single_pair": {}, "pooled": {}}
    for L in layers:
        u = P[a.arm_pair]["d_surface"][L]
        for pair, pl in P.items():
            M = _centred(pl, L)
            out["single_pair"].setdefault(pair, {})[f"L{L}"] = {
                "pc_fractions": spectrum(M),
                "arm_dose": dose_of(M, pl["d_surface"][L]),
                "max_complement_dose": max_complement_dose(M, pl["d_surface"][L]),
            }
            d = out["single_pair"][pair][f"L{L}"]
            d["arm_over_max_complement"] = d["arm_dose"] / d["max_complement_dose"]
        Mp = torch.stack([P[p]["cell_means"][c][L].reshape(-1)
                          for p in DEFAULT_FITS for c in sorted(P[p]["cell_means"])]).double()
        Mp = Mp - Mp.mean(0, keepdim=True)
        fr = spectrum(Mp)
        out["pooled"][f"L{L}"] = {
            "n_cells": int(Mp.shape[0]), "pc_fractions": fr,
            "n_pcs_ge_0.10": sum(1 for f in fr if f >= 0.10),
            "arm_dose": dose_of(Mp, u), "max_complement_dose": max_complement_dose(Mp, u),
            "arm_over_max_complement": dose_of(Mp, u) / max_complement_dose(Mp, u),
        }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print(f"[spectrum] -> {a.out}")
    for L in layers:
        s1 = out["single_pair"][a.arm_pair][f"L{L}"]
        sp = out["pooled"][f"L{L}"]
        print(f"  L{L:<3d} single PC1={s1['pc_fractions'][0]:.4f} gap={s1['arm_over_max_complement']:.1f}x"
              f"   |  pooled PC1={sp['pc_fractions'][0]:.4f} gap={sp['arm_over_max_complement']:.2f}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
