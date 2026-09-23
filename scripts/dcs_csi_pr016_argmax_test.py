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
    if pr.get("id") != "PR-CSI-016":
        sys.exit("REFUSING: this reader implements PR-CSI-016's frozen primary only; got %r. "
                 "A test reader that accepts any prereg is not a preregistered test." % pr.get("id"))
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
    if rep.get("split") != pr.get("split"):
        sys.exit("REFUSING: the census report is split %r but the prereg froze %r. This family is a "
                 "VALIDATION read. (R28/S-312)" % (rep.get("split"), pr.get("split")))

    E, CI = rep["E"], rep["ci95"]
    cf = rep["CELL_FAMILY"]
    band = pr["layers"]
    per_head = pr["DETECTABILITY_PREREGISTERED_PER_HEAD"]["per_head"]
    ratio = float(pr["ADMISSION"]["ratio"])
    alpha = float(pr["PRIMARY"]["alpha"])

    bars = (cf.get("bars_COMPUTED_FROM_A_FROZEN_RULE") or {})
    rows, admitted, dropped = [], [], []
    for h in [str(x) for x in pr["heads"]]:
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
        if "BC_H%s_L%02d" % (h, band[0]) not in E:
            sys.exit("REFUSING: head %s's single-cell arms are absent from the census report. "
                     "(R28/S-312)" % h)
        eh, ci = E[src], CI[src]
        excl0 = (ci[1] < 0) or (ci[0] > 0)
        power = abs(eh) / bar if bar else 0.0
        # R28 MINOR: |E|/bar at exactly the frozen 1.5 evaluates below it for ~8% of boundary pairs
        # in IEEE doubles (abs(-0.009)/0.006 == 1.4999999999999998). A tolerance at the 1e-12 level
        # cannot admit anything the criterion meant to exclude.
        ok = bool(excl0 and power >= ratio - 1e-12)
        # the argmax, over the NINE SINGLE CELLS of this head only -- never the whole-head arm
        cells = {L: E["BC_H%s_L%02d" % (h, L)] for L in band}
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

    K = len(admitted)
    matched = [r for r in admitted if r["COUNTED_IN_M"]]
    M = len(matched)
    ties = [r for r in admitted if r["argmax_is_a_TIE"]]
    p0 = 1.0 / len(band)
    p = binom_tail(M, K, p0) if K else 1.0
    # ⚠ R28/S-312 ROBUSTNESS CO-PRIMARIES, frozen before the run.
    # (a) CONDITIONAL: only heads whose predicted layer is UNIQUE among the admitted heads are
    #     informative against a shared band-bias null; heads sharing a prediction match for free.
    _pred = [r["screen_predicted_layer"] for r in admitted]
    uniq = [r for r in admitted if _pred.count(r["screen_predicted_layer"]) == 1]
    K_u = len(uniq)
    M_u = sum(1 for r in uniq if r["COUNTED_IN_M"])
    p_cond = binom_tail(M_u, K_u, p0) if K_u else 1.0
    # (b) PERMUTATION: does the screen put the ODD prediction on the RIGHT head? A shared band bias
    #     cannot fake this, because it says nothing about WHICH head gets the minority layer.
    import itertools
    obs = [r["argmax_layer"] for r in admitted]
    preds = list(_pred)
    perms = set(itertools.permutations(preds))
    hits = sum(1 for q in perms if sum(1 for a, b in zip(obs, q) if a == b) >= M)
    p_perm = (hits / len(perms)) if perms else 1.0
    span = sorted({r["argmax_layer"] for r in matched})
    # ⚠ R28/S-312: the spanning rule is only MEANINGFUL where it was reached. It used to be emitted
    # as False on every FAIL and on K<2, where the prereg's own wording ("the matching heads must not
    # all share one band layer") is vacuously satisfied by an empty match set. A reader of a FAIL
    # JSON saw spanning_rule_satisfied=false and could report a second failure that never happened.
    spanning_ok = len(span) >= 2

    if ties:
        # ⚠ R28/S-312: a tied head is UNDETERMINED, not a miss. It used to be scored as a miss and
        # M/p were still published, so the JSON carried quotable numbers from a scoring rule the
        # prereg never froze for this case.
        verdict, why = "CANNOT ANSWER", ("a tie for the argmax on head(s) %s -- preregistered "
                                         "CANNOT_ANSWER_IF. M and p are NOT computed: a tied head is "
                                         "undetermined, not a miss."
                                         % [r["head"] for r in ties])
        M, p, span, spanning_ok = None, None, None, None
    elif K < 2:
        verdict, why = "CANNOT ANSWER", (
            ("NO head was ADMITTED: every head failed the frozen power gate, which the prereg prices "
             "as this family's real risk" if K == 0 else
             "only 1 head ADMITTED; the floor at K=1 is 1/%d = %.4f and cannot clear alpha=%.2f"
             % (len(band), p0, alpha)))
    elif p > alpha:
        verdict, why = "FAIL", "p = %.6f > alpha = %.2f at K=%d, M=%d" % (p, alpha, K, M)
    elif not spanning_ok:
        verdict, why = "CANNOT ANSWER", (
            "the SPANNING RULE is violated: all %d matching head(s) share band layer L%s, so a shared "
            "depth bias and a correct screen are indistinguishable here. p = %.6f is NOT quotable as "
            "a pass." % (M, span[0] if span else "?", p))
    else:
        verdict, why = "PASS", ("p = %.6f <= alpha = %.2f at K=%d, M=%d; matches span layers %s"
                                % (p, alpha, K, M, ["L%d" % L for L in span]))

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
        "ROBUSTNESS": {
            "shared_predicted_layers": sorted({L for L in _pred if _pred.count(L) > 1}),
            "K_unique": K_u, "M_unique": M_u, "p_conditional": (None if M is None else p_cond),
            "p_permutation": (None if M is None else p_perm),
            "n_permutations": len(perms),
            "THE_CLAIM_MUST_BE_STATED_WITH": (
                "the binomial p alone (no admitted heads share a predicted layer)"
                if not any(_pred.count(L) > 1 for L in _pred) else
                "the WEAKEST of the binomial, conditional and permutation p's, each named -- two "
                "admitted heads share a predicted layer, so a shared band bias would deliver those "
                "matches for free (R28/S-312)"),
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
        if any(_pred.count(L) > 1 for L in _pred):
            print("[pr016] ⚠ ROBUSTNESS -- heads sharing a predicted layer match FOR FREE under a "
                  "shared band bias:")
            print("          conditional  K_unique=%d M_unique=%d  p = %.6f   (the informative heads "
                  "only)" % (K_u, M_u, p_cond))
            print("          permutation  over %d assignments of the prediction multiset  p = %.6f"
                  % (len(perms), p_perm))
            print("          -> the claim must be stated with the WEAKEST of %.6f / %.6f / %.6f"
                  % (p, p_cond, p_perm))
        print("[pr016] matching layers %s -> spanning rule %s"
              % (["L%d" % L for L in span],
                 "SATISFIED" if spanning_ok else "VIOLATED" if M else "not reached (no matches)"))
    print("[pr016] VERDICT: %s -- %s" % (verdict, why))
    print("[pr016] wrote+verified %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
