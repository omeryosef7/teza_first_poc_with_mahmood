"""§22 POWER, swept across EVERY committed rank-test cell in this sprint.

WHY A SWEEP AND NOT MORE ONE-OFFS. S-220 and S-221 computed power for two cells because one was new
and one carried a negative conclusion. But §22 says "every behavioural endpoint", and the claim table
rests on TWENTY-ONE committed rank tests whose power was never computed. Doing them one at a time
invites picking the interesting ones; doing them all at once means the uninteresting answers are on
the record too.

WHAT IT REPORTS PER CELL
  * the attainable floor 1/(n_controls+1), and THE CERTIFYING RANK -- the largest r with
    r/(n+1) <= alpha. For n=46 that is 2; for n=20 it is 1; FOR n=10 IT IS ZERO, i.e. NO OUTCOME
    WHATSOEVER could have certified at alpha=0.05, however large the effect. That is a property of
    the family size, fixed before any data, and it is the first thing a reader of such a cell needs.
  * power at the OBSERVED candidate shift, by resampling that cell's own 46/22/10 empirical control
    values -- no Gaussian assumption.
  * the MDE at 80% power, in raw units and as a multiple of the observed shift.

⛔ THE NOISE MODEL IS THE SAME ONE S-220 FLAGGED: the null spread is the control arms' own values,
which conflate domain sampling noise with arm-to-arm heterogeneity, and these artifacts cannot
decompose them. The candidate is modelled as a control draw plus a constant shift, so a candidate
whose per-domain PATTERN differs from the controls' is outside this analysis.
"""
import argparse, glob, json, os, random, statistics, sys, tempfile


def atomic_write_json(path, obj):
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_atomic_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2); fh.write("\n"); fh.flush(); os.fsync(fh.fileno())
        if os.path.getsize(tmp) == 0:
            raise OSError("0 bytes after flush+fsync")
        json.load(open(tmp))
        os.chmod(tmp, 0o644); os.replace(tmp, path)
        try:
            dfd = os.open(d, os.O_RDONLY)
            try: os.fsync(dfd)
            finally: os.close(dfd)
        except OSError:
            pass
    except Exception as e:
        try: os.unlink(tmp)
        except OSError: pass
        raise OSError("atomic_write_json FAILED for %s: %r" % (path, e)) from e
    return os.path.getsize(path)


def certifying_rank(n_controls, alpha):
    """Largest r with r/(n_controls+1) <= alpha. ZERO means no outcome can certify."""
    n = n_controls + 1
    r = int(alpha * n)
    while r > 0 and r / n > alpha:
        r -= 1
    return r


def power_at(ctrl, delta, max_rank, B, rng, higher_is_better):
    if max_rank < 1:
        return 0.0
    hit = 0
    for _ in range(B):
        cs = [ctrl[rng.randrange(len(ctrl))] for _ in range(len(ctrl))]
        c = ctrl[rng.randrange(len(ctrl))] + delta
        better = sum(1 for x in cs if (x >= c if higher_is_better else x <= c))
        if 1 + better <= max_rank:
            hit += 1
    return hit / B


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports", default="reports")
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--B", type=int, default=8000)
    ap.add_argument("--seed", type=int, default=20260922)
    ap.add_argument("--target-power", type=float, default=0.80)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    cells = []
    for f in sorted(glob.glob(os.path.join(a.reports, "*.json"))):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if not isinstance(d, dict) or "control_recovery_distribution" not in d:
            continue
        crd = d["control_recovery_distribution"]
        ctrl = crd.get("controls")
        ctrl = list(ctrl.values()) if isinstance(ctrl, dict) else list(ctrl or [])
        if len(ctrl) < 2 or crd.get("candidate") is None:
            continue
        cells.append((os.path.basename(f), d, crd, [float(x) for x in ctrl]))

    print("[sweep] SIZE cells = %d | alpha = %.3f | B = %d" % (len(cells), a.alpha, a.B))
    if not cells:
        sys.exit("VACUOUS: no rank-test cell found")

    rng = random.Random(a.seed)
    rows, n_cannot = [], 0
    print()
    print("%-52s %5s %4s %5s %6s %8s %8s %7s" %
          ("cell", "n_ct", "dom", "rank", "cert_r", "shift", "P(cert)", "MDE/obs"))
    for name, d, crd, ctrl in cells:
        cand = float(crd["candidate"])
        # ⛔ ORIENTATION IS DERIVED FROM THE DATA AND REFUSED IF AMBIGUOUS -- NEVER DEFAULTED.
        # The first version of this file read `"MOST POSITIVE" in str(crd.get("rank_orientation",""))`,
        # and `rank_orientation` is ABSENT (None) in the older basket artifacts. `"MOST POSITIVE" in
        # "NONE"` is False, so those cells were silently scored lower-is-better: candidates that
        # actually ranked 1 came out with a negative shift and P(certify) = 0.0000. An absent field
        # read as a value -- the same class as S-168's gate, S-182's vacuous witness and R16-2's
        # missing denominator, and the FOURTH time in this sprint.
        # The reported rank is the authority: recompute it BOTH ways and keep the reading that
        # reproduces it. If both or neither match, refuse -- a power number for a cell whose
        # direction is unknown is worse than no number.
        rep_rank = crd.get("candidate_rank_among_controls")
        # TIES COUNT AGAINST THE CANDIDATE (>=, not >), which is the artifacts' own convention and
        # the conservative one. Established, not assumed: button_train_L18_n46 has exactly ONE
        # control tied with the candidate at -0.00014, and its reported rank 36 is reproduced by
        # 1 + count(x >= cand) = 36 while strict > gives 35. A tie rule off by one silently shifts
        # every rank in a family by one place.
        hi_rank = 1 + sum(1 for x in ctrl if x >= cand)
        lo_rank = 1 + sum(1 for x in ctrl if x <= cand)
        hib_ok, lob_ok = (hi_rank == rep_rank), (lo_rank == rep_rank)
        if hib_ok == lob_ok:
            sys.exit("REFUSING for %s: reported rank %r is reproduced by %s -- the orientation "
                     "cannot be established from the artifact (higher-is-better gives %d, "
                     "lower-is-better gives %d)"
                     % (name, rep_rank, "BOTH readings" if hib_ok else "NEITHER reading",
                        hi_rank, lo_rank))
        hib = hib_ok
        mu0 = statistics.fmean(ctrl)
        shift = (cand - mu0) if hib else (mu0 - cand)
        cert_r = certifying_rank(len(ctrl), a.alpha)
        floor = 1.0 / (len(ctrl) + 1)
        if cert_r < 1:
            n_cannot += 1
            p_obs, mde, ratio = 0.0, None, None
        else:
            sgn = 1.0 if hib else -1.0
            p_obs = power_at(ctrl, sgn * shift, cert_r, a.B, rng, hib)
            sd = statistics.stdev(ctrl)
            mde = None
            for k in range(1, 61):
                dd = sgn * k * 0.25 * sd
                if power_at(ctrl, dd, cert_r, max(1500, a.B // 4), rng, hib) >= a.target_power:
                    mde = abs(dd); break
            ratio = (mde / shift) if (mde is not None and shift not in (0.0,)) else None
        rows.append({"cell": name, "orientation_derived":
                         ("higher_is_better" if hib else "lower_is_better"),
                     "orientation_field_in_artifact": crd.get("rank_orientation"),
                     "n_controls": len(ctrl), "n_domains": d.get("n_domains"),
                     "observed_rank": crd.get("candidate_rank_among_controls"),
                     "attainable_floor": floor, "certifying_rank_at_alpha": cert_r,
                     "candidate": cand, "control_mean": mu0,
                     "control_sd": statistics.stdev(ctrl),
                     "observed_shift_toward_better": shift,
                     "power_at_observed": round(p_obs, 4),
                     "MDE_80pct": None if mde is None else round(mde, 8),
                     "MDE_over_observed_shift": None if ratio is None else round(ratio, 2),
                     "NO_RANK_CAN_CERTIFY": cert_r < 1})
        print("%-52s %5d %4s %5s %6d %8.5f %8.4f %7s"
              % (name[:52], len(ctrl), d.get("n_domains"), crd.get("candidate_rank_among_controls"),
                 cert_r, shift, p_obs, ("--" if ratio is None else "%.1fx" % ratio)))

    out = {
        "schema": "dcs_csi_rank_power_sweep/1", "alpha": a.alpha, "B": a.B, "seed": a.seed,
        "target_power": a.target_power, "n_cells": len(rows),
        "n_cells_where_NO_rank_certifies": n_cannot,
        "STRUCTURAL_NOTE": ("certifying_rank_at_alpha = 0 means the family is too small for ANY "
                            "outcome to reach alpha: the attainable floor 1/(n+1) already exceeds it. "
                            "That is fixed before data collection and is not a property of the effect"),
        "TIE_CONVENTION": ("ties count AGAINST the candidate (>=), matching the artifacts' own "
                           "rank definition, verified against button_train_L18_n46 whose one "
                           "tied control makes strict > give 35 where the artifact says 36"),
        "NOISE_MODEL_CAVEAT": ("the null spread is each cell's own control values, conflating domain "
                               "sampling noise with arm-to-arm heterogeneity; the candidate is "
                               "modelled as a control draw plus a constant shift"),
        "cells": rows,
    }
    n = atomic_write_json(a.out, out)
    print()
    print("[sweep] wrote+verified %s (%d bytes)" % (a.out, n))
    print("[sweep] cells where NO rank could certify at alpha=%.2f: %d of %d"
          % (a.alpha, n_cannot, len(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
