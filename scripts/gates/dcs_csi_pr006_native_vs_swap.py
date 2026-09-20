"""Rank the recipient's OWN native axis inside the SWAP read's own key set.

The swap read and the PR-CSI-005 read are different reads with different --arms lists, so their key
intersections need not match. Comparing "swap rank 4" against "native rank 36" across two reads is
the S-125 key-set trap. This computes BOTH ranks inside ONE report, on ONE key set.

REVIEW R10 MAJOR-3 / MINOR-1. Two defects fixed here:

  (1) THE TWO NUMBERS THIS SCRIPT EXISTS TO MAKE COMPARABLE CAME OFF DIFFERENT PATHS. The native
      was `round(installation_by_arm["KO_AXIS"] - installation_by_arm["KO"], 5)` -- a difference of
      two values the analyser had ALREADY rounded to 5 dp -- while the controls it is ranked against
      were rounded ONCE from unrounded means. Reconstructing every control the lossy way disagrees
      with the report's own controls on 20 of 46 (button/train), 13 of 46 (basket/train) and 18 of
      46 (basket/validation), always by exactly 1e-5, which is the spacing of the controls near the
      middle of the distribution. Perturbing the native by that 1e-5 moves the committed rank 36 to
      35. Both the native and the swap are now recomputed from `domain_means` over the report's own
      domain set -- the SAME source at the SAME precision as each other and as the controls -- and
      the recomputed swap rank is ASSERTED against the rank the report itself committed.

  (2) NO EXIT CODE AND ALMOST NO ASSERTS. Apart from `len(ctrl) == 46` the script asserted nothing
      and returned nothing, so mutations Q1 (KO_AXIS -> KO_FULL) and Q2 (KO -> BASE) both ran clean
      and printed an authoritative-looking "native KO_AXIS ..." line with a fabricated number. The
      arm names are now named constants, asserted present, asserted to be at the pinned layer, and
      the reference arm is taken from the report and asserted to be the one the read used.
"""
import json
import sys

CELLS = [
    ("A: basket axis -> BUTTON ko, TRAIN", "reports/DCS_CSI_SWAP_button_train_L18_from_basket_n46.json", "XSWAP_FROM_BASKET"),
    ("B: button axis -> BASKET ko, TRAIN", "reports/DCS_CSI_SWAP_basket_train_L18_from_button_n46.json", "XSWAP_FROM_BUTTON"),
    ("B: button axis -> BASKET ko, VALIDATION", "reports/DCS_CSI_SWAP_basket_validation_L18_from_button_n46.json", "XSWAP_FROM_BUTTON"),
]
N_CELLS = 3
NATIVE_ARM = "KO_AXIS"       # the recipient's OWN axis -- the thing the swap is being compared to
EXPECT_REF_ARM = "KO"        # the sufficiency reference: h' = h_ko + P_w(h_clean - h_ko)
EXPECT_LAYER = 18
HELPS_RANK = 2               # PRE-FIXED in configs/dcs_csi_pr006_axis_swap.json: HELPS == rank <= 2

# S-134 / MAJOR-5: the size of the comparison is asserted, not printed as a literal.
assert len(CELLS) == N_CELLS, "CELLS holds %d cells, expected %d" % (len(CELLS), N_CELLS)

fail = []
n_cells = 0

for lbl, f, swaparm in CELLS:
    d = json.load(open(f))
    crd = d["control_recovery_distribution"]
    ctrl = crd["controls"]
    n_cells += 1

    # --- the arms are NAMED and their presence ASSERTED (mutations Q1/Q2) ------------------------
    dm = d["domain_means"]
    ref_arm = d["reference_arm"]
    assert ref_arm == EXPECT_REF_ARM, (
        "%s: the read's reference arm is %r, not %r -- a 'recovery' measured against a different "
        "baseline is a different quantity" % (f, ref_arm, EXPECT_REF_ARM))
    for arm in (NATIVE_ARM, swaparm, ref_arm):
        assert arm in dm, "%s: arm %r is absent from domain_means -- cannot measure it" % (f, arm)
    rl = d.get("resolved_rescue_layers") or {}
    for arm in (NATIVE_ARM, swaparm):
        assert rl.get(arm) == [EXPECT_LAYER], (
            "%s: arm %r resolved to rescue layers %r, expected [%d] -- this is the S-127 twin-layer "
            "hazard, the arm is not the one this cell is about" % (f, arm, rl.get(arm), EXPECT_LAYER))
    # WHAT MAKES AN ARM *THE NATIVE AXIS* IS ITS BASIS KEY, not its name. arm_meta records what
    # each arm actually patched: KO_AXIS -> ['cand_rank1'], KO_FULL -> [], KO_ORTH -> ['ctrl_orth'],
    # XSWAP_FROM_* -> ['swap_cand_from_*']. Mutation Q1 (KO_AXIS -> KO_FULL) printed a fabricated
    # "native KO_AXIS +0.10938 -> rank 1 of 47" and exited 0; this is what stops it.
    am = d["arm_meta"]
    assert am.get(NATIVE_ARM, {}).get("basis_keys") == ["cand_rank1"], (
        "%s: arm %r patched basis_keys %r, not ['cand_rank1'] -- it is NOT the recipient's own "
        "rank-1 axis and must not be printed as 'native %s' (REVIEW R10 mutation Q1)"
        % (f, NATIVE_ARM, am.get(NATIVE_ARM, {}).get("basis_keys"), NATIVE_ARM))
    swap_keys = am.get(swaparm, {}).get("basis_keys") or []
    assert len(swap_keys) == 1 and str(swap_keys[0]).startswith("swap_cand_from_"), (
        "%s: arm %r patched basis_keys %r -- a swap arm must patch exactly one swap_cand_from_* key"
        % (f, swaparm, swap_keys))
    print("   arm identity: %s basis_keys=%s | %s basis_keys=%s"
          % (NATIVE_ARM, am[NATIVE_ARM]["basis_keys"], swaparm, swap_keys))

    # --- ONE source, ONE precision, for the candidate, the native AND the controls ---------------
    DOMS = sorted(dm[ref_arm])
    assert len(DOMS) == int(d["n_domains"]), (
        "%s: domain_means carries %d domains, report says n_domains=%s" % (f, len(DOMS), d["n_domains"]))
    for a in (NATIVE_ARM, swaparm, ref_arm):
        assert sorted(dm[a]) == DOMS, "%s: arm %r has a different domain set" % (f, a)
    base = sum(dm[ref_arm][x] for x in DOMS) / float(len(DOMS))

    def recovery(arm):
        return sum(dm[arm][x] for x in DOMS) / float(len(DOMS)) - base

    assert len(ctrl) == 46, "expected 46 controls, got %d" % len(ctrl)
    for c in ctrl:
        assert c in dm, "%s: control %r is in the distribution block but not in domain_means" % (f, c)
    rec = {c: recovery(c) for c in ctrl}
    swap = recovery(swaparm)
    native = recovery(NATIVE_ARM)
    vals = sorted(rec.values(), reverse=True)

    def rank_of(x):
        # Ties count AGAINST the candidate (`>=`), exactly as dcs_csi_subspace_analyze.py ranks.
        return 1 + sum(1 for v in vals if v >= x)

    r_swap, r_native = rank_of(swap), rank_of(native)

    print("=" * 92)
    print("%s      [n_keys=%d n_domains=%d]" % (lbl, d["n_keys_common"], d["n_domains"]))
    print("   controls compared: %d   (both ranks computed on THIS report's key set,"
          " from domain_means, at the SAME precision)" % len(ctrl))
    print("   swap   %-20s %+.8f  -> rank %2d of %d" % (swaparm, swap, r_swap, len(ctrl) + 1))
    print("   native %-20s %+.8f  -> rank %2d of %d" % (NATIVE_ARM, native, r_native, len(ctrl) + 1))
    print("   control distribution: max %+.8f  median %+.8f  min %+.8f"
          % (vals[0], vals[len(vals) // 2], vals[-1]))

    # --- the recomputation must reproduce what the report committed ------------------------------
    print("   cross-check vs the report: candidate %+.5f (report %+.5f) rank %d (report %d)"
          % (swap, crd["candidate"], r_swap, crd["candidate_rank_among_controls"]))
    if round(swap, 5) != crd["candidate"]:
        fail.append("%s: recomputed candidate %+.8f does not round to the report's %+.5f"
                    % (swaparm, swap, crd["candidate"]))
    if r_swap != crd["candidate_rank_among_controls"]:
        fail.append("%s: recomputed candidate rank %d != the report's %d"
                    % (swaparm, r_swap, crd["candidate_rank_among_controls"]))

    # --- ties, stated rather than silently settled by `>=` ---------------------------------------
    for who, x in (("swap", swap), ("native", native)):
        t = sorted(c for c in rec if rec[c] == x)
        t5 = sorted(c for c in ctrl if ctrl[c] == round(x, 5))
        if t or t5:
            print("   TIES on the %s: exact at domain_means precision %s | exact at the report's"
                  " 5 dp %s (the 5-dp ties are NOT ties at full precision)" % (who, t or "none", t5 or "none"))

    print("   PRE-FIXED RULE: HELPS == rank <= %d  ->  swap %s"
          % (HELPS_RANK, "HELPS" if r_swap <= HELPS_RANK else "does NOT help"))

assert n_cells == N_CELLS, "read %d cells, expected %d" % (n_cells, N_CELLS)
print("=" * 92)
print("cells compared: %d (expected %d)" % (n_cells, N_CELLS))
if fail:
    print("FAIL -> %s" % fail)
else:
    print("OK -- every recomputed candidate rank reproduces the rank its own report committed.")
sys.exit(0 if not fail else 1)
