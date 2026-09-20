"""Rank the recipient's OWN native axis inside the SWAP read's own key set.

The swap read and the PR-CSI-005 read are different reads with different --arms lists, so their key
intersections need not match. Comparing "swap rank 4" against "native rank 36" across two reads is
the S-125 key-set trap. This computes BOTH ranks inside ONE report, on ONE key set.
"""
import json

CELLS = [
    ("A: basket axis -> BUTTON ko, TRAIN", "reports/DCS_CSI_SWAP_button_train_L18_from_basket_n46.json", "XSWAP_FROM_BASKET"),
    ("B: button axis -> BASKET ko, TRAIN", "reports/DCS_CSI_SWAP_basket_train_L18_from_button_n46.json", "XSWAP_FROM_BUTTON"),
    ("B: button axis -> BASKET ko, VALIDATION", "reports/DCS_CSI_SWAP_basket_validation_L18_from_button_n46.json", "XSWAP_FROM_BUTTON"),
]

for lbl, f, swaparm in CELLS:
    d = json.load(open(f))
    crd = d["control_recovery_distribution"]
    ctrl = crd["controls"]
    swap = crd["candidate"]
    inst = d["installation_by_arm"]
    ko = inst["KO"]
    native = round(inst["KO_AXIS"] - ko, 5)

    assert len(ctrl) == 46, "expected 46 controls, got %d" % len(ctrl)
    vals = sorted(ctrl.values(), reverse=True)

    def rank_of(x):
        return 1 + sum(1 for v in vals if v >= x)

    print("=" * 92)
    print("%s      [n_keys=%d n_domains=%d]" % (lbl, d["n_keys_common"], d["n_domains"]))
    print("   controls compared: %d   (both ranks computed on THIS report's key set)" % len(ctrl))
    print("   swap   %-20s %+.5f  -> rank %2d of %d" % (swaparm, swap, rank_of(swap), len(ctrl) + 1))
    print("   native %-20s %+.5f  -> rank %2d of %d" % ("KO_AXIS", native, rank_of(native), len(ctrl) + 1))
    print("   control distribution: max %+.5f  median %+.5f  min %+.5f"
          % (vals[0], vals[len(vals) // 2], vals[-1]))
    print("   PRE-FIXED RULE: HELPS == rank <= 2  ->  swap %s" % ("HELPS" if rank_of(swap) <= 2 else "does NOT help"))
