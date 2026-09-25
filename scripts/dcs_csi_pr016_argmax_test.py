"""PR-CSI-016's PRIMARY: does the basket TRAIN screen predict the BUTTON argmax cell?

Thin by design. The census reader (`scripts/dcs_csi_head_census.py`) already produces every per-cell
E, its ci95, GATE 0 and the per-head bars; this file does NOTHING but apply the rules the prereg
froze to that published report. It computes no effect of its own, so it cannot disagree with the
census about a number -- only about a verdict, which is the only thing it is for.

THE TEST (frozen in configs/dcs_csi_pr016_cell_census_button.json under PRIMARY):
  M = #{admitted heads h : argmax_L |E(cell (L,h))| == that head's frozen screen-predicted layer}
  p = P(Binom(K, 1/9) >= M), one-sided.
  SUCCESS = p <= alpha AND the matching heads do not all share one band layer.

⚠ THE SPANNING RULE IS NOT OPTIONAL AND IS NOT A TIE-BREAK. The screen predicts L14 for two of the
three heads, so a shared bias toward the top of the band would deliver M=2 and p=0.034 while
measuring nothing about the screen. A violation is CANNOT ANSWER, whatever p says.
"""
import argparse, json, os, sys
from math import comb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dcs_csi_argmax_verdict as _verdict   # noqa: E402 -- the SHARED verdict (S-402)


def binom_tail(M, K, p):
    """P(Binom(K, p) >= M). `p` is 1/len(band) and is passed explicitly -- R28 filed the hardcoded
    1/9 default as an un-pinned literal inside a preregistered statistic, the same class R27 filed
    against the PR-015 freeze script's screen literal."""
    return sum(comb(K, i) * p ** i * (1 - p) ** (K - i) for i in range(M, K + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--census", required=True, help="the report dcs_csi_head_census.py wrote")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    # ⚠ S-293 §5: a traceback is not a refusal. Name the missing artefact.
    for lbl, path in (("prereg", a.prereg), ("census report", a.census)):
        if not os.path.exists(path):
            sys.exit("REFUSING: the %s %r does not exist. This reader computes nothing of its own; "
                     "without the census report there is no endpoint to read." % (lbl, path))
    pr = json.load(open(a.prereg))
    # ⚠ S-321: WIDENED from PR-CSI-016 to the named families that share this frozen primary. The
    # filename is now a misnomer and is KEPT anyway: runargs/dcs_csi_pr016_read.txt names this path,
    # and a frozen read must go on resolving to the file it was frozen against (R26 chain of custody).
    # The id list is EXPLICIT rather than open: a test reader that accepts any prereg is not a
    # preregistered test, which is the property the original single-id check was protecting.
    # ⚠ S-350: PR-CSI-020 added. S-321 widened this allowlist AND NOTHING ELSE, and the reader
    # still refused because `BC_H%s_L%02d` encoded PR-016's arm naming -- S-322's lesson. The
    # family-encoding sites have since been removed (S-322 inverts cell_sets for arm names, S-323
    # reads GATING from the prereg, S-332 checks n_arms_per_split), so widening the id is now
    # sufficient -- but "sufficient" was VERIFIED by running this reader end to end against a
    # synthetic PR-020 census, not assumed from the diff.
    IMPLEMENTS = ("PR-CSI-016", "PR-CSI-018", "PR-CSI-020")
    if pr.get("id") not in IMPLEMENTS:
        sys.exit("REFUSING: this reader implements the frozen primary of %s only; got %r."
                 % (" / ".join(IMPLEMENTS), pr.get("id")))
    for _f in ("PRIMARY", "ADMISSION", "DETECTABILITY_PREREGISTERED_PER_HEAD", "heads", "layers"):
        if _f not in pr:
            sys.exit("REFUSING: prereg %r carries no %r, which this reader requires. Checked before "
                     "the census is opened (S-296)." % (pr.get("id"), _f))
    rep = json.load(open(a.census))
    if rep.get("prereg_id") != pr["id"]:
        sys.exit("REFUSING: census report is for %r, not %r." % (rep.get("prereg_id"), pr["id"]))
    if not rep.get("ON_PROTOCOL", False):
        sys.exit("REFUSING: the census report is not ON_PROTOCOL.")
    # ⚠⚠ R28/S-312 -- THIS WAS A BLOCKER AND IT WAS MINE. The check read
    # `GATE_0_and_identity["all_pass"]`, a key `dcs_csi_head_census.py` has NEVER written: it writes
    # {"per_arm": ..., "identity": ...}. So the preregistered PRIMARY refused EVERY real census
    # report, and would have done so after 32 arms had already run. My own 9 tests passed only
    # because my own test helper fabricated {"all_pass": True} -- a shape the producer never emits.
    # A test that invents its input validates the test, not the code.
    # The replacement reads the per-arm record the census actually writes, so the check is also no
    # longer hollow: a report with a failing arm and a cheerful summary flag cannot pass.
    g0 = rep.get("GATE_0_and_identity") or {}
    per_arm = g0.get("per_arm")
    if not isinstance(per_arm, dict) or not per_arm:
        sys.exit("REFUSING: the census report carries no GATE_0_and_identity['per_arm'] record, so "
                 "GATE 0 cannot be verified. Absence is not a pass (R20-6). (R28/S-312)")
    _bad = sorted(k for k, v in per_arm.items() if not (isinstance(v, dict) and v.get("pass")))
    if _bad:
        sys.exit("REFUSING: GATE 0 did not pass on %d of %d arms (%s). No endpoint may be read. "
                 "(S-202)" % (len(_bad), len(per_arm), ", ".join(_bad[:6])))
    # ⚠ R30-B/S-332: THE CHECK ABOVE ITERATES THE RECORD'S OWN KEYS, so its denominator is whatever
    # the record happens to contain and ABSENCE IS A PASS -- the very thing the refusal two lines up
    # says it is not. R30-B truncated a census's per_arm to a SINGLE arm, left all 61 other E's in
    # place, and the read published VERDICT PASS at K=6 M=6 with no warning; deleting just
    # BF_H6_L11 and HD_29 did the same. The frozen read's claim is "GATE 0 PASS on all 62 arms",
    # and nothing here could substantiate the "all 62": `n_arms_per_split` was never read.
    # This is the S-301/R20-6 shape one level up -- not a missing value, a missing ROW.
    _declared = set(pr.get("base_arms") or [])
    _declared |= set(pr.get("cell_sets") or pr.get("head_sets") or {})
    _missing = sorted(_declared - set(per_arm))
    if _missing:
        sys.exit("REFUSING: the census's GATE_0_and_identity['per_arm'] record covers %d arms but "
                 "prereg %r declares %d. %d are ABSENT (%s). Absence is not a pass (R20-6): a "
                 "truncated record would otherwise self-report its own truncated total. "
                 "(R30-B/S-332)"
                 % (len(per_arm), pr["id"], len(_declared), len(_missing), ", ".join(_missing[:6])))
    _want_arms = pr.get("n_arms_per_split")
    if _want_arms is not None and len(per_arm) != int(_want_arms):
        sys.exit("REFUSING: GATE 0 record holds %d arms; prereg %r freezes n_arms_per_split=%d. "
                 "(R30-B/S-332)" % (len(per_arm), pr["id"], int(_want_arms)))
    if rep.get("split") != pr.get("split"):
        sys.exit("REFUSING: the census report is split %r but the prereg froze %r. This family is a "
                 "VALIDATION read. (R28/S-312)" % (rep.get("split"), pr.get("split")))

    E, CI = rep["E"], rep["ci95"]
    cf = rep["CELL_FAMILY"]
    band = pr["layers"]
    per_head = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]
    ratio = float(pr["ADMISSION"]["ratio"])
    alpha = float(pr["PRIMARY"]["alpha"])

    # ⚠⚠ R29/S-322 -- A BLOCKER, AND IT WAS MINE. Until now this reader built cell-arm names as
    # "BC_H%s_L%02d" -- PR-CSI-016's prefix, HARDCODED. S-321 widened the id check to admit
    # PR-CSI-018 and touched nothing else, so the reader refused PR-018 outright ("head 6's
    # single-cell arms are absent from the census report") on a perfectly well-formed census. Caught
    # by RUNNING the frozen STEP 2 on a real-shaped synthetic census, not by reading it -- the exact
    # S-312 lesson, and the second time a family-specific literal has survived a widening.
    # The prereg ALREADY maps arm name -> cells. Invert it, and no naming convention is assumed.
    cs = pr.get("cell_sets") or {}
    cell_arm = {}
    for _arm, _cells in cs.items():
        if len(_cells) != 1:
            continue                      # a whole-head / bar-source arm, not a cell
        _L, _h = int(_cells[0][0]), int(_cells[0][1])
        if (_h, _L) in cell_arm:
            sys.exit("REFUSING: prereg %r has TWO arms for cell (L%d, head %d): %r and %r. The "
                     "argmax would be ambiguous. (R29/S-322)"
                     % (pr["id"], _L, _h, cell_arm[(_h, _L)], _arm))
        cell_arm[(_h, _L)] = _arm
    bars = (cf.get("bars_COMPUTED_FROM_A_FROZEN_RULE") or {})
    rows, admitted, dropped = [], [], []
    for h in [str(x) for x in pr["heads"]]:
        # ⚠ R34-D/S-375: THIS SUBSCRIPT WAS UNGUARDED while the identical guard sat four lines
        # below (`if h not in bars`). A head named in pr["heads"] but absent from `per_head` was a
        # bare KeyError in STEP 2 -- i.e. AFTER the GPU -- instead of a named refusal. R33 used
        # exactly this mutation and the prereg self-test still cannot see it, because `per_head` is
        # a LOCAL ALIAS of a prereg sub-dict and the static scan only follows `pr[...]` chains.
        if h not in per_head:
            sys.exit("REFUSING: prereg %r names head %s in `heads` but declares no "
                     "DETECTABILITY_PREREGISTERED_PER_HEAD.per_head entry for it, so neither its "
                     "bar source nor its screen prediction exists. Absence is not admission "
                     "(R20-6). (R34-D/S-375)" % (pr["id"], h))
        src = per_head[h]["bar_source_arm"]
        if src not in E:
            sys.exit("REFUSING: head %s's whole-head arm %r is absent from the census report, so "
                     "ADMISSION cannot be evaluated. Absence is not admission. (R20-6)" % (h, src))
        if h not in bars:
            sys.exit("REFUSING: the census report records no computed bar for head %s. The prereg "
                     "froze the bar as a RULE (S-311); a report without its output cannot be read."
                     % h)
        if "bar" not in (bars.get(h) or {}):
            sys.exit("REFUSING: the census records no `bar` for head %s. (R28/S-312)" % h)
        bar = float(bars[h]["bar"])
        if not (bar > 0):
            sys.exit("REFUSING: head %s's computed bar is %r. A non-positive bar means the source "
                     "arm had no per-domain spread; it must not silently drop the head with a "
                     "published power of 0.0, which is the opposite of the truth. (R28/S-312)"
                     % (h, bar))
        _missing = [L for L in band if cell_arm.get((int(h), L)) not in E]
        if _missing:
            sys.exit("REFUSING: head %s has no census effect for band layer(s) %r. The prereg names "
                     "arms %r for them. (R28/S-312, R29/S-322)"
                     % (h, _missing, [cell_arm.get((int(h), L)) for L in _missing]))
        if len([L for L in band if (int(h), L) in cell_arm]) != len(band):
            sys.exit("REFUSING: prereg %r does not name a single-cell arm for every band layer of "
                     "head %s, so its argmax would be taken over an incomplete set. (R29/S-322)"
                     % (pr["id"], h))
        eh, ci = E[src], CI[src]
        excl0 = (ci[1] < 0) or (ci[0] > 0)
        power = abs(eh) / bar if bar else 0.0
        # R28 MINOR: |E|/bar at exactly the frozen 1.5 evaluates below it for ~8% of boundary pairs
        # in IEEE doubles (abs(-0.009)/0.006 == 1.4999999999999998). A tolerance at the 1e-12 level
        # cannot admit anything the criterion meant to exclude.
        ok = bool(excl0 and power >= ratio - 1e-12)
        # the argmax, over the NINE SINGLE CELLS of this head only -- never the whole-head arm
        cells = {L: E[cell_arm[(int(h), L)]] for L in band}
        top = sorted(band, key=lambda L: -abs(cells[L]))
        tie = abs(cells[top[0]]) == abs(cells[top[1]])
        row = {"head": int(h), "whole_head_arm": src, "E_whole_head": eh, "ci95_whole_head": ci,
               "bar": bar, "power_ratio": power, "ci95_excludes_0": excl0, "ADMITTED": ok,
               "argmax_layer": top[0], "argmax_E": cells[top[0]], "runner_up_layer": top[1],
               "runner_up_E": cells[top[1]], "argmax_is_a_TIE": tie,
               "screen_predicted_layer": per_head[h]["screen_predicted_layer"],
               "per_cell_E": {str(L): cells[L] for L in band}}
        # ⚠ R28/S-312: split the pure OBSERVATION from the SCORING decision. These were one field,
        # so a head dropped by ADMISSION whose argmax DID equal its screen layer was published as
        # MATCHES_SCREEN=false directly beside argmax_layer == screen_predicted_layer -- which reads
        # as the screen being wrong about a head the design had merely declined to score.
        row["ARGMAX_EQUALS_SCREEN"] = bool(top[0] == per_head[h]["screen_predicted_layer"])
        row["COUNTED_IN_M"] = bool(ok and not tie and row["ARGMAX_EQUALS_SCREEN"])
        row["MATCHES_SCREEN"] = row["COUNTED_IN_M"]      # retained name, now unambiguous
        rows.append(row)
        (admitted if ok else dropped).append(row)

    # ⚠⚠ S-402: THE VERDICT LOGIC MOVED OUT OF THIS FILE, into scripts/dcs_csi_argmax_verdict.py.
    # It was NOT rewritten -- the body was moved verbatim so every R28/R29/R30-B fix embedded in its
    # comments travels intact. PR-CSI-021 (rung 2) measures a DIFFERENT QUANTITY with the SAME
    # statistic, and S-389 settled that it must be the same; S-350 measured what "two independent
    # implementations" of this statistic is worth (they agreed only at M = K, and the difference
    # would have published a PASS against a prereg saying it could not certify).
    # ⛔ THE GATE ON THIS REFACTOR is that PR-CSI-020's PUBLISHED read reproduces BIT-FOR-BIT.
    _d = _verdict.decide(admitted, band, alpha, pr["PRIMARY"].get("GATING"), pr["id"])
    K, M, matched, ties = _d["K"], _d["M"], _d["matched"], _d["ties"]
    p0, p, p_cond, p_perm = _d["p0"], _d["p"], _d["p_cond"], _d["p_perm"]
    K_u, M_u, perms = _d["K_u"], _d["M_u"], _d["perms"]
    _gating, _gate_name, _gate_p = _d["gating"], _d["gate_name"], _d["gate_p"]
    _floor_parts, _floor_name = _d["floor_parts"], _d["floor_name"]
    _floor_p, span, spanning_ok = _d["floor_p"], _d["span"], _d["spanning_ok"]
    verdict, why = _d["verdict"], _d["why"]
    _pred = [r["screen_predicted_layer"] for r in admitted]

    # ⚠ R28/S-312: MUST_NOT_BE_SAID used to be chosen by `verdict == "PASS"`, so a spanning-rule
    # CANNOT ANSWER -- which fires with p <= alpha, i.e. a POSITIVE-LOOKING number in hand -- was
    # published carrying the IF_NULL prohibitions, including "the screen is useless". Exactly the
    # branch where that is both wrong and harmful.
    if verdict == "PASS":
        must_not = pr["MUST_NOT_BE_SAID_IF_POSITIVE"]
    elif verdict == "FAIL":
        must_not = pr["MUST_NOT_BE_SAID_IF_NULL"]
    else:
        must_not = (["CANNOT ANSWER is NOT a null and NOT a positive. Neither the IF_POSITIVE nor "
                     "the IF_NULL list applies, because no verdict was reached."]
                    + pr["MUST_NOT_BE_SAID_IF_POSITIVE"] + pr["MUST_NOT_BE_SAID_IF_NULL"])
    out = {
        "schema": "dcs_csi_pr016_argmax_test/1", "prereg_id": pr["id"],
        "prereg": a.prereg, "census_report": a.census,
        "K_admitted": K, "M_matches": M, "p_one_sided": p, "alpha": alpha,
        "null": pr["PRIMARY"]["null"], "VERDICT": verdict, "why": why,
        "null_p_per_head": p0, "n_band_layers": len(band),
        "GATING": _gating,
        # ⚠ R34-C/S-369: THESE TWO WERE EMITTED UNCONDITIONALLY while `p_conditional` and
        # `p_permutation` just below were correctly nulled on `M is None`. `_gate_name`/`_gate_p` are
        # computed ABOVE the verdict branches, so on the TIE branch -- whose own text reads "M and p
        # are NOT computed: a tied head is undetermined, not a miss" -- the JSON published
        # `gating_p`: the single number this prereg says the claim must be stated with, computed
        # under a tie-as-miss scoring rule the prereg NEVER FROZE. A downstream reader keying on
        # `gating_p` took a headline-grade pass off a CANNOT ANSWER.
        "gating_p_name": (None if M is None else _gate_name),
        "gating_p": (None if M is None else _gate_p),
        "ROBUSTNESS": {
            "shared_predicted_layers": sorted({L for L in _pred if _pred.count(L) > 1}),
            # ⚠ R34-C/S-369: M_unique is a SCORING COUNT, not an observation -- on a tie it
            # carries the tie-as-miss rule directly, which is the same leak as `gating_p` above.
            # K_unique IS an observation (it depends only on which heads were admitted) and stays.
            "K_unique": K_u, "M_unique": (None if M is None else M_u),
            "p_conditional": (None if M is None else p_cond),
            "p_permutation": (None if M is None else p_perm),
            "n_permutations": len(perms),
            # ⚠ R30-B/S-332: THIS FIELD USED TO BE GATED ON WHETHER TWO ADMITTED HEADS SHARE A
            # PREDICTED LAYER -- PR-CSI-016's criterion -- RATHER THAN ON THE PREREG'S DECLARED
            # GATING. S-323 moved the GATE onto `PRIMARY.GATING` and left the WORDING behind on the
            # old rule, one field over. Under weakest_of_three, any admission that leaves the
            # admitted predictions all distinct made this field read "the binomial p alone" while
            # MUST_NOT_BE_SAID_IF_POSITIVE[0] in the SAME JSON says quoting the binomial alone is
            # FORBIDDEN. R30-B produced it: a PASS gated on permutation = 0.041667 whose published
            # instruction named a binomial 273x smaller. The wording follows the GATING or it is
            # not the prereg's wording.
            "THE_CLAIM_MUST_BE_STATED_WITH": (
                "the binomial p alone (this prereg declares PRIMARY.GATING = 'binomial_only')"
                if _gating == "binomial_only" else
                "the WEAKEST of the binomial, conditional and permutation p's, EACH NAMED -- this "
                "prereg declares PRIMARY.GATING = %r. Quoting the binomial alone is FORBIDDEN "
                "whatever the admitted heads' predicted layers happen to be (R30-B/S-332)."
                % (_gating,)),
            "GATING_FLOOR": {
                "name": _floor_name, "p": _floor_p, "parts": _floor_parts,
                "WHAT_THIS_IS": "the p the gating statistic would report on a PERFECT result at "
                                "the realised K and admitted multiset. If it exceeds alpha the "
                                "read was unwinnable before the data and the verdict is CANNOT "
                                "ANSWER (structural), never FAIL. (R30-B/S-332)"},
        },
        "matching_layers": (["L%d" % L for L in span] if span is not None else None),
        "spanning_rule_satisfied": (spanning_ok if (span is not None and verdict in
                                                    ("PASS", "CANNOT ANSWER") and M) else
                                    "NOT_APPLICABLE -- the rule was never reached"),
        "intervention_argmax_marginal": {"L%d" % L: sum(1 for r in admitted if r["argmax_layer"] == L)
                                         for L in band},
        "per_head": rows,
        "dropped_heads": [{"head": r["head"], "power_ratio": r["power_ratio"],
                           "ci95_excludes_0": r["ci95_excludes_0"],
                           "NOT_A_MISS": "dropped by the frozen ADMISSION rule, computed from the "
                                         "whole-head arm alone; it is removed from K, not counted "
                                         "against the screen"} for r in dropped],
        "MUST_NOT_BE_SAID": must_not,
    }
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    json.load(open(a.out))

    print("[pr016] ADMISSION (from the whole-head arm alone, ratio >= %.1f):" % ratio)
    for r in rows:
        print("  head %-3d %-6s E=%+.6f ci95 [%+.6f,%+.6f] bar=%.6f |E|/bar=%.2f  %s"
              % (r["head"], r["whole_head_arm"], r["E_whole_head"], r["ci95_whole_head"][0],
                 r["ci95_whole_head"][1], r["bar"], r["power_ratio"],
                 "ADMITTED" if r["ADMITTED"] else "DROPPED (not a miss)"))
    print("\n[pr016] ARGMAX vs the frozen basket-TRAIN screen prediction:")
    for r in rows:
        if not r["ADMITTED"]:
            continue
        print("  head %-3d argmax L%-2d (E=%+.6f, runner-up L%-2d %+.6f)  screen said L%-2d  -> %s%s"
              % (r["head"], r["argmax_layer"], r["argmax_E"], r["runner_up_layer"],
                 r["runner_up_E"], r["screen_predicted_layer"],
                 "MATCH" if r["MATCHES_SCREEN"] else "miss", "  ⚠ TIE" if r["argmax_is_a_TIE"] else ""))
    if M is None:
        print("\n[pr016] K = %d admitted; M and p NOT COMPUTED (a tied argmax is undetermined)" % K)
    else:
        print("\n[pr016] K = %d admitted, M = %d matches, p = %.6f (Binom(K, 1/%d), one-sided)"
              % (K, M, p, len(band)))
        # ⚠ R30-B/S-332: this block was gated on "do two admitted heads share a predicted layer",
        # so under an admission that left the predictions distinct the conditional and permutation
        # p's WERE NEVER PRINTED -- the only number on the transcript beside the verdict line was
        # the binomial, on a read gated by something else entirely. A p the verdict does not use,
        # printed alone, is the one number that must never stand alone here. It follows the GATING.
        if _gating != "binomial_only":
            print("[pr016] ⚠ ROBUSTNESS -- this prereg gates on the WEAKEST of three; all three are "
                  "reported whatever the admitted heads' predicted layers are:")
            print("          binomial     K=%d M=%d  p = %.6f" % (K, M, p))
            print("          conditional  K_unique=%d M_unique=%d  p = %.6f   (the informative heads "
                  "only%s)" % (K_u, M_u, p_cond,
                               "; K_unique=0 -> UNDEFINED, carried as the placeholder 1.0"
                               if not K_u else ""))
            print("          permutation  over %d assignments of the prediction multiset  p = %.6f"
                  % (len(perms), p_perm))
            print("          -> the claim must be stated with the WEAKEST of %.6f / %.6f / %.6f"
                  % (p, p_cond, p_perm))
            print("          FLOOR (best attainable at this K/multiset): %s = %.6f%s"
                  % (_floor_name, _floor_p,
                     "  ⛔ EXCEEDS alpha -- this read was UNWINNABLE before the data"
                     if _floor_p > alpha else ""))
        print("[pr016] matching layers %s -> spanning rule %s"
              % (["L%d" % L for L in span],
                 "SATISFIED" if spanning_ok else "VIOLATED" if M else "not reached (no matches)"))
    print("[pr016] VERDICT: %s -- %s" % (verdict, why))
    print("[pr016] wrote+verified %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
