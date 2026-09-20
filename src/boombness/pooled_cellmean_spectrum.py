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
import sys

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# P0.2e: one definition of the units-explicit dose siblings, imported, never re-typed.
from insubspace_null_test import DOSE_UNITS_CELLMEAN, dose_fields, read_dose  # noqa: E402

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


def _atomic_json_dump(obj, path, **kw):
    """Atomic, VERIFIED JSON write. Fix for sprint entry S-124.

    Replaces `json.dump(x, open(p, "w"), ...)`, whose handle is never closed: `open` truncates the
    destination immediately and the buffered bytes are flushed only in the GC finaliser, where
    CPython PRINTS and then SWALLOWS an EDQUOT. A full quota therefore produced a 0-byte file at a
    real artifact name, with "wrote <path>" on stdout and exit status 0 -- indistinguishable from a
    finished report. Temp file + fsync + size check + re-parse + os.replace makes the write ATOMIC
    as well as checked: a half-written file never appears at the real name, and whatever was there
    before survives a failure. On any error this RAISES, naming the path and the byte count.
    """
    import tempfile                        # local: keeps this helper drop-in and import-order-free
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_atomic_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, **kw)
            fh.flush()
            os.fsync(fh.fileno())          # EDQUOT surfaces HERE, not in a GC finaliser
        n = os.path.getsize(tmp)
        if n == 0:
            raise OSError("temp file is 0 bytes after a flush+fsync that reported success")
        with open(tmp, "r", encoding="utf-8") as fh:
            json.load(fh)                  # a truncated write does not re-parse
        try:
            mode = os.stat(path).st_mode & 0o7777   # keep the artifact's existing permissions:
        except OSError:                             # mkstemp makes the temp file 0600 and
            mode = 0o644                            # os.replace would carry that onto the report
        os.chmod(tmp, mode)
        os.replace(tmp, path)              # atomic within the directory
    except Exception as e:
        try:
            n = os.path.getsize(tmp)
        except OSError:
            n = -1
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise OSError("atomic_json_dump FAILED for %s -- %d bytes reached the temp file; the "
                      "destination is UNCHANGED (never truncated). Cause: %r" % (path, n, e)) from e
    return os.path.getsize(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--layers", default="6,8,10,12,18")
    # Fits are an ARGUMENT, not a constant, so the measurement grows as extractions land instead of
    # requiring an edit (and a stale hardcoded list is its own defect class here).
    ap.add_argument("--fit", action="append", default=[], metavar="NAME=RUNDIR",
                    help="repeatable; overrides DEFAULT_FITS entirely when given")
    ap.add_argument("--arm-pair", default="carrot_bomb", help="whose d_surface is the arm")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    layers = [int(x) for x in a.layers.split(",")]
    fits = dict(DEFAULT_FITS)
    if a.fit:
        fits = {}
        for spec in a.fit:
            if "=" not in spec:
                raise SystemExit(f"--fit needs NAME=RUNDIR, got {spec!r}")
            k, v = spec.split("=", 1)
            fits[k] = v
    P = {}
    for k, v in fits.items():
        rd = os.path.join(REPO, "outputs/boombness/extract_boombness", v)
        if not os.path.exists(os.path.join(rd, "DONE.json")):
            raise SystemExit(f"REFUSING: {v} has no DONE.json -- an unfinished extraction must not "
                             f"be fitted from (require_done discipline)")
        P[k] = torch.load(os.path.join(rd, "directions_fit_dev.pt"), map_location="cpu",
                          weights_only=False)
    out = {"question": "does crossing codeword/concept pairs break PC1 dominance of the cell-mean cloud?",
           "fits": fits, "arm_pair": a.arm_pair, "layers": layers,
           "caveat": ("pooling three separately-fitted banks is not the same object as one bank with "
                      "crossed pairs; each was centred within its own row-set. Same model/layers/"
                      "extraction config makes it reasonable, but a real Phase 5 bank must be built "
                      "and measured rather than simulated this way."),
           "dose_units": DOSE_UNITS_CELLMEAN,
           "single_pair": {}, "pooled": {}}
    for L in layers:
        u = P[a.arm_pair]["d_surface"][L]
        for pair, pl in P.items():
            M = _centred(pl, L)
            out["single_pair"].setdefault(pair, {})[f"L{L}"] = {
                "pc_fractions": spectrum(M),
                **dose_fields(dose_of(M, pl["d_surface"][L]), "arm_dose"),
                **dose_fields(max_complement_dose(M, pl["d_surface"][L]),
                              "max_complement_dose"),
            }
            d = out["single_pair"][pair][f"L{L}"]
            # consumer prefers the units-explicit keys, falls back to the historical ones (P0.2e)
            d["arm_over_max_complement"] = (read_dose(d, "arm_dose")
                                            / read_dose(d, "max_complement_dose"))
        Mp = torch.stack([P[p]["cell_means"][c][L].reshape(-1)
                          for p in fits for c in sorted(P[p]["cell_means"])]).double()
        Mp = Mp - Mp.mean(0, keepdim=True)
        fr = spectrum(Mp)
        out["pooled"][f"L{L}"] = {
            "n_cells": int(Mp.shape[0]), "pc_fractions": fr,
            "n_pcs_ge_0.10": sum(1 for f in fr if f >= 0.10),
            **dose_fields(dose_of(Mp, u), "arm_dose"),
            **dose_fields(max_complement_dose(Mp, u), "max_complement_dose"),
            "arm_over_max_complement": dose_of(Mp, u) / max_complement_dose(Mp, u),
        }
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    _atomic_json_dump(out, a.out, indent=1)
    print(f"[spectrum] -> {a.out}")
    for L in layers:
        s1 = out["single_pair"][a.arm_pair][f"L{L}"]
        sp = out["pooled"][f"L{L}"]
        print(f"  L{L:<3d} single PC1={s1['pc_fractions'][0]:.4f} gap={s1['arm_over_max_complement']:.1f}x"
              f"   |  pooled PC1={sp['pc_fractions'][0]:.4f} gap={sp['arm_over_max_complement']:.2f}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
