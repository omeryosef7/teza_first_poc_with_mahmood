#!/usr/bin/env python3
"""PR-CSI-021's READ: the preregistered RUNG 2 (decodability) verdict.

⛔ IT COMPUTES NO STATISTIC OF ITS OWN. Every branch, every p-value, the gating selection and the
floors come from `scripts/dcs_csi_argmax_verdict.decide()` -- the SAME function
`dcs_csi_pr016_argmax_test.py` calls for rung 1. S-389 settled that this must be so: AM-34's ladder
claims the rungs are SEPARABLE, so testing that claim requires the SAME statistic applied to a
DIFFERENT quantity, and if the two drifted a rung-1/rung-2 disagreement would be indistinguishable
from an artefact of the statistic. S-350 measured the alternative: two "independent
implementations" of this statistic agreed ONLY at M = K.

WHAT THIS FILE CONTRIBUTES is the mapping from a rung-2 artefact to the `admitted` rows `decide()`
consumes -- and that mapping IS the design decision S-400/S-401 made, so it is spelled out here
rather than buried:

    for each head h:
        norm(L) = |contrib(L,h)| / mean_{h' != h} |contrib(L,h')|        <- LEAVE-ONE-OUT
        argmax over the nine band layers of norm(L)
        MATCH iff that argmax == h's frozen screen-predicted layer

⚠⚠ THE LEAVE-ONE-OUT LAYER NORMALISATION IS PART OF THE STATISTIC, NOT A PRESENTATION CHOICE.
   S-399 measured that the RAW |contrib| carries a depth confound of ~44x across the band -- a
   layer-14 head's output passes through 17 fewer blocks before the final-residual direction is
   read than a layer-6 head's -- and that all EIGHT raw argmaxes landed in the top three of nine
   layers (P = 1.52e-04 under a uniform argmax). Normalising collapses that to 1.40x. WITHOUT IT
   THIS READ MEASURES DEPTH, NOT AGREEMENT.

⚠ K IS FIXED AT 8. There is no rung-2 admission gate: the heads are PR-CSI-020's, every one of
   which passed rung-1 admission (dropped_heads: [], D40). So `admitted` is all eight heads and the
   floor is exact. ⛔ The head set is therefore RUNG-1-SELECTED and is NOT held out.

⛔ WHAT A VERDICT FROM THIS FILE IS NOT. The quantity is a DIRECT-PATH projection: it ignores what
   layers L+1..31 do to a cell's output. A cell can be causally necessary and have near-zero direct
   projection. And it is NOT a decomposition of y_install -- the endpoint aggregates the casings
   with LOGSUMEXP and this direction is LINEAR (S-381/S-382). The prereg's prohibition lists carry
   both, in BOTH directions, and this reader copies them into its output.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dcs_csi_argmax_verdict as _verdict          # noqa: E402  -- the SHARED verdict (S-402)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--measurement", required=True,
                    help="the RUNG2 artefact from scripts/dcs_csi_rung2_celldecode.py")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    pr = json.load(open(a.prereg))
    if pr.get("id") != "PR-CSI-021":
        sys.exit("REFUSING: this reader implements PR-CSI-021, not %r." % pr.get("id"))
    # ---- the prereg must DISCLOSE, not merely contain fields ---------------------------------
    # ⚠ S-404: this reader wrote `"⚠ CHOSEN_AFTER_SEEING_TRAIN": pr.get(...)` and the key did not
    # exist in the emitted prereg, so it published the disclosure as `null` -- a field that exists
    # to disclose, carrying nothing, in the output a reader would quote. A missing disclosure is
    # now a REFUSAL: S-401 requires this read to travel with the fact that its statistic was chosen
    # after seeing train, and a null cannot carry that.
    _pw = pr.get("POWER_BY_SEEDED_MONTE_CARLO") or {}
    for _k in ("⚠ THE_STATISTIC_WAS_CHOSEN_AFTER_SEEING_TRAIN", "q_exact_95CI",
               "q_MEASURED_ON_TRAIN", "table"):
        if not _pw.get(_k):
            sys.exit("REFUSING: the prereg's POWER block carries no %r. S-401 requires this read "
                     "to travel with its power table, the exact interval on q, and the fact that "
                     "the statistic was chosen after seeing train. A disclosure that is absent "
                     "cannot be published as null. (S-404)" % _k)
    if not pr["PRIMARY"].get("⚠ THE_LAYER_NORMALISATION_IS_PART_OF_THE_STATISTIC"):
        sys.exit("REFUSING: the prereg does not record that the LEAVE-ONE-OUT layer normalisation "
                 "is part of the statistic. S-399 measured a ~44x depth confound without it; a "
                 "prereg that does not say so describes a different experiment. (S-404)")

    art = json.load(open(a.measurement))

    # ---- the measurement must be the one the prereg describes -------------------------------
    if art.get("schema") != "DCS_CSI_RUNG2/1":
        sys.exit("REFUSING: %r is not a DCS_CSI_RUNG2/1 artefact (schema %r)."
                 % (a.measurement, art.get("schema")))
    if art.get("⚠ IS_SMOKE"):
        sys.exit("REFUSING: the measurement is a SMOKE run (IS_SMOKE true, limit %r). A verdict "
                 "from a limited, domain-CONTIGUOUS sample is not a verdict -- domain is the "
                 "statistical unit and a smoke covers one domain." % art.get("limit_applied"))
    if art.get("split") != pr.get("split"):
        sys.exit("REFUSING: the measurement is split %r but the prereg froze %r."
                 % (art.get("split"), pr.get("split")))
    want_n = pr["population"]["validation_expect_n"]
    want_d = pr["population"]["validation_domains"]
    if (art.get("selection_n_rows"), art.get("selection_n_domains")) != (want_n, want_d):
        sys.exit("REFUSING: the measurement covers %r rows / %r domains; the prereg freezes %d/%d. "
                 "A population that is not the declared one is not the population."
                 % (art.get("selection_n_rows"), art.get("selection_n_domains"), want_n, want_d))
    if art.get("n_prompts_used") != want_n:
        sys.exit("REFUSING: %r of %d declared prompts were measured (skipped: %r). Absence is not "
                 "a measurement (R20-6)." % (art.get("n_prompts_used"), want_n, art.get("skipped")))

    # ---- VOID 13: the decomposition must have been CHECKED, and the number must be on disk ----
    recon = art.get("recon_rel_err_first_row")
    if not recon:
        sys.exit("REFUSING: the measurement carries no recon_rel_err. That is the only check "
                 "standing between this and a wrong GQA head map or o_proj slicing, and its "
                 "ABSENCE is not a pass (R20-6 / VOID 13).")
    tol = 3e-2 if art.get("dtype") == "bfloat16" else 1e-3
    worst = max(float(v) for v in recon.values())
    if worst > tol:
        sys.exit("REFUSING: worst recon_rel_err %.3e exceeds the %s tolerance %.0e. The "
                 "decomposition did not reconstruct the module's own output. (VOID 13)"
                 % (worst, art.get("dtype"), tol))

    # ---- the mapping: rung-2 artefact -> the rows `decide()` consumes ------------------------
    band = list(pr["layers"])
    heads = list(pr["heads"])
    per_head = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]
    cm = art["cell_mean_over_domains"]

    def mag(L, h):
        v = cm.get("L%d_h%d" % (L, h))
        if v is None:
            sys.exit("REFUSING: the measurement has no value for cell (L%d, head %d), so this "
                     "head's argmax would be taken over an incomplete set." % (L, h))
        return abs(float(v))

    rows = []
    for h in heads:
        # ⚠ LEAVE-ONE-OUT: head h is excluded from its own layer baseline. With 8 heads a
        # self-inclusive mean would let a large cell inflate its own denominator by 1/8 and
        # shrink its own normalised value -- an effect that points the wrong way and is avoidable.
        norm = {}
        for L in band:
            others = [mag(L, hh) for hh in heads if hh != h]
            base = statistics.fmean(others)
            if not (base > 0):
                sys.exit("REFUSING: the leave-one-out baseline at L%d is %r, so the normalised "
                         "value is undefined. (S-401)" % (L, base))
            norm[L] = mag(L, h) / base
        order = sorted(band, key=lambda L: -norm[L])
        tie = norm[order[0]] == norm[order[1]]
        sp = int(per_head[str(h)]["screen_predicted_layer"])
        row = {"head": int(h), "argmax_layer": order[0], "runner_up_layer": order[1],
               "argmax_is_a_TIE": bool(tie), "screen_predicted_layer": sp,
               "normalised": {str(L): norm[L] for L in band},
               "raw_abs": {str(L): mag(L, h) for L in band},
               "signed_raw": {str(L): float(cm["L%d_h%d" % (L, h)]) for L in band}}
        row["ARGMAX_EQUALS_SCREEN"] = bool(order[0] == sp)
        # K is fixed at 8 -- there is no rung-2 admission gate (see the module docstring)
        row["COUNTED_IN_M"] = bool((not tie) and row["ARGMAX_EQUALS_SCREEN"])
        row["MATCHES_SCREEN"] = row["COUNTED_IN_M"]
        rows.append(row)
        print("[pr021] head %-3s normalised argmax L%-3d (runner-up L%-3d)  screen said L%-3d  %s%s"
              % (h, order[0], order[1], sp,
                 "MATCH" if row["ARGMAX_EQUALS_SCREEN"] else "miss",
                 "  ⚠ TIE" if tie else ""), flush=True)

    d = _verdict.decide(rows, band, float(pr["PRIMARY"]["alpha"]),
                        pr["PRIMARY"].get("GATING"), pr["id"])

    if d["verdict"] == "PASS":
        must_not = pr["MUST_NOT_BE_SAID_IF_POSITIVE"]
    elif d["verdict"] == "FAIL":
        must_not = pr["MUST_NOT_BE_SAID_IF_NULL"]
    else:
        must_not = (["CANNOT ANSWER is NOT a null and NOT a positive."]
                    + pr["MUST_NOT_BE_SAID_IF_POSITIVE"] + pr["MUST_NOT_BE_SAID_IF_NULL"])

    out = {
        "schema": "DCS_CSI_PR021_READ/1",
        "prereg_id": pr["id"], "measurement": a.measurement,
        "RUNG": "2 (DECODABILITY) -- AM-34's ladder. It stands BESIDE the rung-1 results, never "
                "as a stronger version of them: the rungs are separable.",
        "K_admitted": d["K"], "M_matches": d["M"], "alpha": float(pr["PRIMARY"]["alpha"]),
        "p_one_sided": d["p"], "GATING": d["gating"],
        "gating_p_name": (None if d["M"] is None else d["gate_name"]),
        "gating_p": (None if d["M"] is None else d["gate_p"]),
        "VERDICT": d["verdict"], "why": d["why"],
        "matching_layers": (None if d["span"] is None else ["L%d" % L for L in d["span"]]),
        "spanning_rule_satisfied": (d["spanning_ok"] if d["verdict"] == "PASS"
                                    else "NOT_APPLICABLE -- the rule was never reached"),
        "ROBUSTNESS": {"K_unique": d["K_u"],
                       "M_unique": (None if d["M"] is None else d["M_u"]),
                       "p_conditional": (None if d["M"] is None else d["p_cond"]),
                       "p_permutation": (None if d["M"] is None else d["p_perm"]),
                       "n_permutations": len(d["perms"]),
                       "GATING_FLOOR": {"name": d["floor_name"], "p": d["floor_p"],
                                        "parts": d["floor_parts"]}},
        "per_head": rows,
        "⚠ THE_STATISTIC_IS_THE_RUNG_1_ONE": "computed by scripts/dcs_csi_argmax_verdict.decide(), "
            "the same function dcs_csi_pr016_argmax_test.py calls. Not a reimplementation (S-350).",
        "⚠ THE_NORMALISATION_IS_PART_OF_THE_STATISTIC": "leave-one-out mean of the OTHER heads at "
            "each layer. S-399 measured a ~44x depth confound in the RAW values; without this the "
            "read measures depth, not agreement.",
        "⚠ CHOSEN_AFTER_SEEING_TRAIN": _pw["⚠ THE_STATISTIC_WAS_CHOSEN_AFTER_SEEING_TRAIN"],
        "⚠ q_EXACT_95CI": _pw["q_exact_95CI"],
        "POWER": pr.get("POWER_BY_SEEDED_MONTE_CARLO"),
        "recon_rel_err_worst": worst, "dtype": art.get("dtype"),
        "MUST_NOT_BE_SAID": must_not,
        "WHAT_THIS_CANNOT_ANSWER": pr.get("WHAT_THIS_CANNOT_ANSWER"),
    }
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
    print("[pr021] K = %d, M = %d" % (d["K"], d["M"] if d["M"] is not None else -1), flush=True)
    print("[pr021] VERDICT: %s -- %s" % (d["verdict"], d["why"]), flush=True)
    print("[pr021] wrote %s" % a.out, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
