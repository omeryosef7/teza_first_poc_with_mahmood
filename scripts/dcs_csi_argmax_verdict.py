#!/usr/bin/env python3
"""THE ARGMAX VERDICT, in ONE place, so two rungs cannot drift apart.

WHY THIS FILE EXISTS (S-398/S-402). PR-CSI-021 measures a DIFFERENT QUANTITY (rung 2, decodability)
with the SAME STATISTIC as PR-CSI-020 (rung 1, necessity). S-389 settled that this must be so, and
the reason is not tidiness: AM-34's ladder claims the rungs are SEPARABLE, so testing that claim
requires the same statistic applied to a different quantity. If the two drifted, a rung-1/rung-2
disagreement would be indistinguishable from an artefact of the statistic.

⛔ AND THE ALTERNATIVE HAS BEEN MEASURED. S-350 found that this sprint's two "independent
implementations" of this very statistic agreed ONLY at M = K -- a difference that would have
published a PASS against a prereg recording that it could not certify. The way to make two things
identical is to make them one thing.

⚠ THE BODY BELOW WAS MOVED, NOT RETYPED, out of `dcs_csi_pr016_argmax_test.py` (lines 196-342 as
of ec821f61) so that every R28/R29/R30-B fix embedded in its comments travels intact. The gate on
this refactor is that PR-CSI-020's PUBLISHED read reproduces BIT-FOR-BIT; see S-402.
"""
from __future__ import annotations

import itertools
import sys


def binom_tail(M, K, p0):
    """P(Binom(K, p0) >= M). Kept here so callers need not import it separately."""
    from math import comb
    return sum(comb(K, m) * p0 ** m * (1 - p0) ** (K - m) for m in range(M, K + 1))


def decide(admitted, band, alpha, gating, prereg_id, grandfathered=("PR-CSI-016",)):
    """The preregistered argmax verdict.

    `admitted` is the list of per-head row dicts the caller built -- each carrying
    `screen_predicted_layer`, `argmax_layer`, `argmax_is_a_TIE` and `COUNTED_IN_M`.
    Returns every quantity the caller needs to emit, so nothing is recomputed downstream."""
    _GATING_DEFAULT_GRANDFATHERED = grandfathered
    pr = {"id": prereg_id, "PRIMARY": {"GATING": gating}}   # shim: the body reads these two only
    K = len(admitted)
    matched = [r for r in admitted if r["COUNTED_IN_M"]]
    M = len(matched)
    ties = [r for r in admitted if r["argmax_is_a_TIE"]]
    p0 = 1.0 / len(band)
    p = binom_tail(M, K, p0) if K else 1.0
    # ⚠ R29/S-322: WHICH p GATES IS THE PREREG'S DECISION, NOT THIS FILE'S. PR-CSI-016 froze
    # "binomial_only" (its co-primaries bound the wording, because at K_unique=0 gating on them would
    # have failed it structurally); PR-CSI-018 froze "weakest_of_three", because it was BUILT so the
    # permutation test is answerable. This reader applied PR-016's rule to both and printed PASS on a
    # PR-018 census whose weakest p was 0.21, and again at 0.33. The default is PR-016's, so its
    # published read is untouched; anything else must be declared.
    # ⚠ R29/S-323: FAIL CLOSED. Defaulting to binomial_only for ANY prereg meant that if PR-CSI-018's
    # GATING field were ever lost -- a bad merge, a reverted freeze, a hand-edit -- the reader would
    # silently apply the WRONG rule to it rather than refuse. Same shape as the codeword default
    # S-308 had to scope. The default is grandfathered to the ONE family whose frozen prereg predates
    # the field; everything else must say what it gates on.
    _GATING_DEFAULT_GRANDFATHERED = ("PR-CSI-016",)
    _gating = pr["PRIMARY"].get("GATING")
    if not _gating:
        if pr["id"] not in _GATING_DEFAULT_GRANDFATHERED:
            sys.exit("REFUSING: prereg %r declares no PRIMARY.GATING, and only %s may fall back to "
                     "the legacy 'binomial_only' default. Guessing which p-value gates is guessing "
                     "the success criterion. (R29/S-323)"
                     % (pr["id"], ", ".join(_GATING_DEFAULT_GRANDFATHERED)))
        _gating = "binomial_only"
    if _gating not in ("binomial_only", "weakest_of_three"):
        sys.exit("REFUSING: prereg %r declares PRIMARY.GATING = %r, which this reader does not "
                 "implement. (R29/S-322)" % (pr["id"], _gating))
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
    if _gating == "weakest_of_three":
        _cands = {"binomial": p, "conditional": p_cond, "permutation": p_perm}
        _gate_name = max(_cands, key=lambda k: _cands[k])
        _gate_p = _cands[_gate_name]
    else:
        _gate_name, _gate_p = "binomial", p
    # ⚠ R30-B/S-332: THE GATING STATISTIC'S OWN FLOOR, i.e. the p it would report on a PERFECT
    # result at the REALISED K and multiset. The reader already had this idea and applied it to
    # exactly one case -- "the floor at K=1 is 1/9 and cannot clear alpha" -- while three other
    # ways of reaching an unwinnable read published a FAIL instead.
    #
    # R30-B demonstrated both on synthetic censuses built in the census's own output shape:
    #   * K_unique = 0. `p_cond` is then the PLACEHOLDER 1.0 on the line above -- not a p-value, a
    #     stand-in for a statistic that does not exist. Under weakest_of_three max() promotes that
    #     placeholder to the gate and the verdict is FAIL. A 4-of-4 agreement with a prediction
    #     frozen on another split AND another codeword was published as a null, carrying the
    #     IF_NULL prohibitions. That is verbatim the S-317 death THIS FAMILY WAS BUILT TO ESCAPE.
    #   * K = 2. The permutation space holds 2 assignments, floor 0.5, so weakest > alpha is FORCED
    #     whatever the data -- and the prereg defines FAILURE only "with K >= 3". 60 of the 729
    #     reachable configurations published FAIL below that threshold.
    #
    # A read whose BEST attainable p cannot clear alpha did not fail to find the effect; it could
    # not have found it. That is CANNOT ANSWER (structural), and conflating the two is how a
    # family that was never able to certify gets cited as evidence against the hypothesis.
    _floor_parts = {"binomial": binom_tail(K, K, p0),
                    "conditional": (binom_tail(K_u, K_u, p0) if K_u else 1.0),
                    "permutation": ((1.0 / len(perms)) if perms else 1.0)}
    if _gating == "weakest_of_three":
        _floor_name = max(_floor_parts, key=lambda k: _floor_parts[k])
    else:
        _floor_name = "binomial"
    _floor_p = _floor_parts[_floor_name]
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
    elif _gate_p > alpha and K < 3:
        # ⚠ R30-B/S-332, AND A CORRECTION OF MY OWN FIRST FIX. The prereg defines FAILURE as "the
        # weakest p > 0.05 WITH K >= 3". Below that it defines no adverse verdict at all, and the
        # code's only guard was `K < 2`, so K=2 published FAIL -- 60 of R30-B's 729 reachable
        # configurations did. At K=2 the permutation space holds 2 assignments, floor 0.5, so
        # weakest > alpha is FORCED whatever the data: a structural non-answer, exactly like K=1.
        #
        # ⚠ MY FIRST ATTEMPT AT THIS GUARD KEYED ON THE FLOOR ALONE (_floor_p > alpha -> CANNOT
        # ANSWER) AND WAS WRONG. It converted K=3/M=3 -- where the permutation floor is 1/3 and the
        # prereg says in terms that K >= 3 with weakest > alpha IS a FAILURE -- into CANNOT ANSWER.
        # An existing test caught it. Deciding after the fact that a preregistered FAILURE is
        # really a non-answer, because its floor is unflattering, is the post-hoc move this sprint
        # exists to forbid. The floor is now REPORTED everywhere and CHANGES THE VERDICT NOWHERE
        # the prereg has spoken.
        verdict, why = "CANNOT ANSWER", (
            "STRUCTURAL: K=%d and the prereg defines FAILURE only with K >= 3. The gating "
            "statistic's floor at this K and admitted multiset is %s = %.6f > alpha = %.2f, so no "
            "outcome could have certified and the observed M=%d is NOT evidence against the screen. "
            "(binomial floor %.6f | conditional floor %.6f | permutation floor %.6f over %d "
            "assignments)"
            % (K, _floor_name, _floor_p, alpha, M, _floor_parts["binomial"],
               _floor_parts["conditional"], _floor_parts["permutation"], len(perms)))
    elif _gate_p > alpha:
        verdict, why = "FAIL", (
            "%s = %.6f > alpha = %.2f at K=%d, M=%d" % (_gate_name, _gate_p, alpha, K, M)
            # ⚠ R30-B/S-332: the prereg's FAILURE stands, but a FAILURE whose BEST attainable p
            # could not have cleared alpha must never be cited as evidence AGAINST the screen. The
            # sharpest case is K_unique=0, where `p_cond` is the placeholder 1.0 rather than a
            # p-value and max() promotes it to the gate -- S-317's death, which this family was
            # built to escape. The verdict is the prereg's; this sentence is what stops it being
            # misread as a refutation.
            + ("" if _floor_p <= alpha else
               "  ⛔ STRUCTURALLY UNWINNABLE: the floor at this K and admitted multiset is %s = "
               "%.6f > alpha, so NO outcome could have certified. This is NOT evidence against the "
               "screen.%s" % (_floor_name, _floor_p,
                              "  K_unique=0: the conditional is UNDEFINED and carried as the "
                              "placeholder 1.0." if not K_u else ""))
            + ("" if _gating == "binomial_only" else
               "  [binomial %.6f | conditional %.6f | permutation %.6f -- this prereg gates on the "
               "WEAKEST]" % (p, p_cond, p_perm)))
    elif not spanning_ok:
        verdict, why = "CANNOT ANSWER", (
            "the SPANNING RULE is violated: all %d matching head(s) share band layer L%s, so a shared "
            "depth bias and a correct screen are indistinguishable here. p = %.6f is NOT quotable as "
            "a pass." % (M, span[0] if span else "?", p))
    else:
        verdict, why = "PASS", ("%s = %.6f <= alpha = %.2f at K=%d, M=%d; matches span layers %s"
                                % (_gate_name, _gate_p, alpha, K, M, ["L%d" % L for L in span]))

    return {"K": K, "M": M, "matched": matched, "ties": ties, "p0": p0, "p": p,
            "p_cond": p_cond, "p_perm": p_perm, "K_u": K_u, "M_u": M_u, "perms": perms,
            "gating": _gating, "gate_name": _gate_name, "gate_p": _gate_p,
            "floor_parts": _floor_parts, "floor_name": _floor_name, "floor_p": _floor_p,
            "span": span, "spanning_ok": spanning_ok, "verdict": verdict, "why": why}
