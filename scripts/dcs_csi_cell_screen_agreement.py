#!/usr/bin/env python
"""Cell-level agreement between the TRAIN AtP screen and the VALIDATION cell interventions.

S-269 recorded the open question in as many words: the screen's per-CELL ordering "has never been
validated against anything".  S-254 had validated it only at HEAD level (rho = +0.7713).  With
PR-CSI-014 (head 2) and PR-CSI-015 (heads 17/19/23) there are now 4 heads x 9 band layers = 36 cells
carrying BOTH a TRAIN screen value and a VALIDATION intervention effect, so the question is answerable
at zero GPU cost.

  *** THIS ANALYSIS IS EXPLORATORY.  IT WAS NOT PREREGISTERED. ***

It is descriptive and carries no verdict.  Three limits are emitted into the report itself rather than
left to the reader:
  * the 36 cells are NOT 36 independent units -- they are 4 heads x 9 layers, so the p-values are
    inflated.  The only defensible unit is the HEAD (n = 4), and the report gives the per-head figures.
  * the 4 heads are D34's load-bearing four, selected on VALIDATION.  Heads with large effects have
    sharper screens AND sharper interventions, so argmax agreement is easier for them than for a head
    drawn at random.  Nothing here generalises to the other 28 heads.
  * the screen is TRAIN (67 domains); the interventions are VALIDATION (23 domains).  Disjoint, and the
    script asserts the split labels rather than trusting them.
"""
import argparse, hashlib, json, os

BAND = list(range(6, 15))


def _md5(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def _spearman(x, y):
    from scipy import stats
    r, p = stats.spearmanr(x, y)
    return float(r), float(p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen", default="outputs/boombness/dcs_csi/w1_screen_train_basket_916132.json")
    ap.add_argument("--pr014", default="reports/DCS_CSI_PR014_CELL_CENSUS_validation.json")
    ap.add_argument("--pr015", default="reports/DCS_CSI_PR015_CELL_CENSUS_3HEADS_validation.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    scr = json.load(open(a.screen))
    # S-202 discipline: assert the split labels, never assume them.
    if scr.get("split") != "train":
        raise SystemExit("REFUSING: screen split is %r, expected 'train' -- the whole point is that "
                         "nomination is held out from the read." % scr.get("split"))
    atp = scr["AtP_by_cell"]
    if len(atp) != 288:
        raise SystemExit("REFUSING: screen has %d cells, expected 288 (32 heads x 9 band layers)." % len(atp))

    p14 = json.load(open(a.pr014))
    p15 = json.load(open(a.pr015))
    for nm, rep in (("PR-CSI-014", p14), ("PR-CSI-015", p15)):
        if rep.get("split") != "validation":
            raise SystemExit("REFUSING: %s split is %r, expected 'validation'." % (nm, rep.get("split")))
    E14, E15 = p14["E"], p15["E"]

    # (head, layer) -> (train AtP, validation E).  Head 2 from PR-014, heads 17/19/23 from PR-015.
    cells = []
    for h in (17, 19, 23):
        for L in BAND:
            cells.append((h, L, atp["%d,%d" % (L, h)], E15["CL_H%d_L%02d" % (h, L)]))
    for L in BAND:
        cells.append((2, L, atp["%d,2" % L], E14["CL_L%02d" % L]))

    heads = sorted({c[0] for c in cells})
    peak_screen = {h: max((c for c in cells if c[0] == h), key=lambda c: abs(c[2])) for h in heads}
    peak_inter = {h: max((c for c in cells if c[0] == h), key=lambda c: abs(c[3])) for h in heads}

    A = [c[2] for c in cells]
    E = [c[3] for c in cells]
    r_all, p_all = _spearman(A, E)
    nonpeak = [c for c in cells if c[1] != peak_screen[c[0]][1]]
    r_np, p_np = _spearman([c[2] for c in nonpeak], [c[3] for c in nonpeak])

    per_head = {}
    for h in heads:
        sub = [c for c in cells if c[0] == h]
        sub8 = [c for c in sub if c[1] != peak_screen[h][1]]
        r9, p9 = _spearman([c[2] for c in sub], [c[3] for c in sub])
        r8, p8 = _spearman([c[2] for c in sub8], [c[3] for c in sub8])
        per_head[str(h)] = {
            "screen_argmax_layer": peak_screen[h][1],
            "intervention_argmax_layer": peak_inter[h][1],
            "argmax_agrees": peak_screen[h][1] == peak_inter[h][1],
            "signs_agree": (peak_screen[h][2] * peak_screen[h][3]) > 0,
            "rho_all9": r9, "p_all9": p9,
            "rho_8_nonpeak": r8, "p_8_nonpeak": p8,
        }

    # The band-edge rival: is the screen's argmax generically the last band layer?  Measured over all
    # 32 heads, not over the 4 this family looked at.
    tally = {}
    for h in range(32):
        am = max(BAND, key=lambda L: abs(atp["%d,%d" % (L, h)]))
        tally[am] = tally.get(am, 0) + 1
    p_marginal = 1.0
    for h in heads:
        p_marginal *= tally.get(peak_screen[h][1], 0) / 32.0

    n_match = sum(1 for h in heads if per_head[str(h)]["argmax_agrees"])
    out = {
        "schema": "dcs_csi_cell_screen_agreement/1",
        "STATUS": "EXPLORATORY -- NOT PREREGISTERED. Descriptive only; carries no verdict, rank or "
                  "success criterion. Generated after PR-CSI-015 was read.",
        "codeword": "basket", "concept": "bomb",
        "screen": {"path": a.screen, "md5": _md5(a.screen), "split": scr.get("split"),
                   "n_domains": scr.get("n_domains"), "n_cells": len(atp)},
        "interventions": {"PR-CSI-014": {"path": a.pr014, "md5": _md5(a.pr014), "split": "validation",
                                         "n_domains": p14.get("n_domains")},
                          "PR-CSI-015": {"path": a.pr015, "md5": _md5(a.pr015), "split": "validation",
                                         "n_domains": p15.get("n_domains")}},
        "cells": [{"head": h, "layer": L, "atp_train": t, "E_validation": e} for h, L, t, e in cells],
        "n_cells": len(cells), "n_heads": len(heads),
        "spearman_all_cells": {"rho": r_all, "p": p_all, "n": len(cells)},
        "spearman_dominant_cells_removed": {"rho": r_np, "p": p_np, "n": len(nonpeak)},
        "per_head": per_head,
        "argmax_agreement": {"n_match": n_match, "n_heads": len(heads)},
        "band_edge_rival": {
            "question": "is the screen's argmax generically L14, the last layer of band 6-14?",
            "screen_argmax_tally_over_all_32_heads": {str(k): v for k, v in sorted(tally.items())},
            "L14_share_of_32_heads": tally.get(14, 0) / 32.0,
            "modal_layer": max(tally, key=lambda k: tally[k]),
            "p_all_match_under_screens_own_marginal": p_marginal,
            "p_all_match_under_uniform_1_over_9": (1.0 / len(BAND)) ** len(heads),
            # ⚠ The threshold below is a HEURISTIC ANNOTATION, not a preregistered criterion.  S-305
            # named the class this belongs to: a bare number in code that reads like a frozen rule.  So
            # the rule is emitted beside its own verdict and the verdict says what it is.
            "verdict_rule": "heuristic, NOT preregistered: call the rival refuted when L14 is the screen "
                            "argmax for no more than 2x its uniform expectation (2 * 32/9 = %.2f heads)"
                            % (2.0 * 32.0 / len(BAND)),
            "verdict_is_preregistered": False,
            "verdict": ("REFUTED as an explanation" if tally.get(14, 0) <= 2.0 * 32.0 / len(BAND)
                        else "NOT REFUTED -- L14 is over-represented; discount the agreement"),
        },
        "CANNOT_DO": [
            "no claim that any cell is the writer -- no rank, no control family, no p-value",
            "no claim that the screen is a validated cell selector IN GENERAL -- this is 4 heads of 32, "
            "and all four were selected as load-bearing on VALIDATION, which makes argmax agreement "
            "easier for them than for a head drawn at random",
            "no claim about the other 28 heads or any cell of them",
            "the 36 cells are NOT independent; the only defensible unit is the HEAD (n=4)",
            "nothing revising D32-D36",
        ],
    }
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    json.load(open(a.out))  # write-then-verify, as every reader in this sprint does

    print("[cell-screen] EXPLORATORY, NOT PREREGISTERED. %d cells over %d heads." % (len(cells), len(heads)))
    print("[cell-screen] Spearman all cells        rho=%+.4f p=%.3e  (S-254's HEAD-level was +0.7713)" % (r_all, p_all))
    print("[cell-screen] dominant cells removed    rho=%+.4f p=%.3e" % (r_np, p_np))
    for h in heads:
        d = per_head[str(h)]
        print("[cell-screen]   head %2d  screen L%-2d vs intervention L%-2d  %-8s  rho9=%+.3f  rho8(no peak)=%+.3f"
              % (h, d["screen_argmax_layer"], d["intervention_argmax_layer"],
                 "MATCH" if d["argmax_agrees"] else "MISMATCH", d["rho_all9"], d["rho_8_nonpeak"]))
    print("[cell-screen] argmax agreement %d of %d heads" % (n_match, len(heads)))
    br = out["band_edge_rival"]
    print("[cell-screen] band-edge rival: L14 is the screen argmax for %d of 32 heads (modal layer L%s); "
          "p(all match) = %.2e under the screen's own marginal vs %.2e uniform -> %s"
          % (tally.get(14, 0), br["modal_layer"], br["p_all_match_under_screens_own_marginal"],
             br["p_all_match_under_uniform_1_over_9"], br["verdict"]))
    print("[cell-screen]   (that verdict is a HEURISTIC, not preregistered: %s)" % br["verdict_rule"])
    print("[cell-screen] wrote+verified %s" % a.out)


if __name__ == "__main__":
    main()
