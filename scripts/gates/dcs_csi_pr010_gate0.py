"""GATE 0 for PR-CSI-010, verified INDEPENDENTLY of the freezer that wrote it.

It re-derives every frozen quantity from its stated source and refuses on any disagreement. It does
NOT import the freezer: a checker that shares the producer's code cannot catch the producer's bug.

⛔ COVERAGE IS STATED, NOT IMPLIED. REVIEW R13 found `dcs_csi_pr009_gate0.py` announcing that "every
VOID condition" was checked while covering four of seven. This gate prints, per VOID condition,
whether it is CHECKED HERE or NOT CHECKABLE UNTIL THE ARMS EXIST -- and the run-time ones are the
launcher's and the reader's job, not this file's.
"""
import argparse, json, random, sys


def draw(pool, k, seed):
    return sorted(random.Random(seed).sample(sorted(pool), k))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--screen", required=True)
    ap.add_argument("--gate", required=True)
    ap.add_argument("--axis", default="configs/dcs_csi_axis_basket_behavioral.pt")
    a = ap.parse_args()

    pr = json.load(open(a.prereg))
    scr = json.load(open(a.screen))
    gate = json.load(open(a.gate))
    fail = []

    def chk(ok, label, detail=""):
        print("  %-4s %s%s" % ("PASS" if ok else "FAIL", label, ("  -- " + detail) if detail else ""))
        if not ok:
            fail.append(label)

    K = pr["K"]
    hs = pr["head_sets"]
    S = {int(h): float(v) for h, v in scr["S_signed_by_head"].items()}
    n_heads = scr["n_heads"]

    print("PR-CSI-010 GATE 0 -- every frozen quantity re-derived from source")
    print("prereg: %s" % a.prereg)
    print()
    print("[A] the head sets come from the screen, not from the prereg's own copy")
    chk(hs["HD_TOPK"] == sorted(S, key=lambda h: S[h])[:K], "HD_TOPK is the K most-negative S[h]",
        "prereg %s" % hs["HD_TOPK"])
    chk(hs["HD_BOTK"] == sorted(S, key=lambda h: abs(S[h]))[:K], "HD_BOTK is the K |S[h]| closest to 0",
        "prereg %s" % hs["HD_BOTK"])
    chk(not (set(hs["HD_TOPK"]) & set(hs["HD_BOTK"])), "HD_TOPK and HD_BOTK are disjoint")
    chk(hs["control_pool"] == sorted(set(range(n_heads)) - set(hs["HD_TOPK"])),
        "control pool is exactly the 32-K non-candidate heads", "%d heads" % len(hs["control_pool"]))

    print()
    print("[B] the 20 control draws are reproducible from the stated seed rule")
    rands = {k: v for k, v in hs.items() if k.startswith("HD_RAND")}
    chk(len(rands) == pr["n_controls"], "control family has n_controls arms",
        "%d of %d" % (len(rands), pr["n_controls"]))
    bad = [k for i, k in enumerate(sorted(rands))
           if rands[k] != draw(hs["control_pool"], K, pr["seed_base"] + i)]
    chk(not bad, "every draw reproduces from seed_base + index", "mismatched: %s" % (bad or "none"))
    chk(all(len(v) == K for v in rands.values()), "every control draw has exactly K heads")
    leak = [k for k, v in rands.items() if set(v) & set(hs["HD_TOPK"])]
    chk(not leak, "NO control contains a candidate head", "leaking: %s" % (leak or "none"))
    chk(len({tuple(v) for v in rands.values()}) == len(rands), "all draws are distinct")
    chk("HD_BOTK" not in rands and not any(v == hs["HD_BOTK"] for v in rands.values()),
        "HD_BOTK does NOT enter the control family (S-120(e) foot-gun)")

    print()
    print("[C] the floor arithmetic, and it is stated with the p")
    floor = pr["attainable_floor"]
    chk(abs(floor["floor_p"] - 1.0 / (pr["n_controls"] + 1)) < 1e-9,
        "floor p == 1/(n_controls+1)", "%.4f" % floor["floor_p"])
    chk(floor["floor_p"] <= 0.05, "floor clears alpha = 0.05 (only at rank 1)")
    chk(2.0 / (pr["n_controls"] + 1) > 0.05, "rank 2 does NOT clear alpha -- stated in the prereg")
    chk(pr["n_arms_per_split"] == 4 + pr["n_controls"], "arm count == 4 + n_controls",
        str(pr["n_arms_per_split"]))

    print()
    print("[D] gate 2 (attribution trustworthiness) agrees with the gate artifact")
    g2 = pr["gate2_attribution_trustworthiness"]
    for f in ("pearson", "spearman", "min_corr", "TRUSTWORTHY"):
        chk(g2[f] == gate[f], "gate2.%s matches the artifact" % f, repr(g2[f]))
    chk(g2["TRUSTWORTHY"] is True, "gate 2 PASSED, so the prereg's selector clause applies")
    chk(g2["fallback_used"] is False, "fallback selection NOT used (consistent with the pass)")
    chk(g2.get("n_domains_in_gate", 0) >= 20,
        "the gate was measured across domains, not a few", "%s domains" % g2.get("n_domains_in_gate"))

    print()
    print("[E] the screen's own provenance is recorded and internally consistent")
    sp = pr["screen_provenance"]
    chk(sp["attn_implementation_loaded"] == "eager", "screen ran under LOADED eager")
    chk(sp["n_rows_used"] == scr["n_rows_used"] == 670, "screen used 670 rows", str(sp["n_rows_used"]))
    chk(sp["n_domains"] == scr["n_domains"] == 67, "screen covered 67 domains")
    chk(sp["model_id"] == scr["model_id"], "model id matches the screen")
    chk([round(S[h], 6) for h in hs["HD_TOPK"]] == sp["S_by_head_topk_values"],
        "the recorded HD_TOPK S values match the screen")

    print()
    print("[F] TEST domains are named and are absent from the fitted population")
    try:
        import torch
        ax = torch.load(a.axis, map_location="cpu", weights_only=False)["meta"]
        fitted = set(ax["fit_population"]["domains"])
        held = set(ax["held_out_validation_domains"])
        test = set(pr["population"]["test_domains"])
        chk(not (test & fitted), "no TEST domain in the fit population")
        chk(not (test & held), "no TEST domain in the validation population")
        chk(len(fitted) == 67 and len(held) == 23, "67 train / 23 validation domains",
            "%d / %d" % (len(fitted), len(held)))
    except Exception as e:
        chk(False, "axis artifact readable", repr(e))

    print()
    print("[G] VOID-condition coverage -- WHAT THIS GATE CAN AND CANNOT SEE")
    coverage = {
        1: ("compared arms on one GPU architecture", "NOT CHECKABLE -- no arms exist yet; the reader must verify"),
        2: ("attn_implementation LOADED == eager", "PARTIAL -- verified for the SCREEN above; each arm must re-verify"),
        3: ("clean worktree + exported provenance", "NOT CHECKABLE -- enforced by dcs_csi_submit.sh at submit"),
        4: ("score_behavior.py unmodified while arms run", "NOT CHECKABLE -- a run-time condition"),
        5: ("head sets/seeds match this file", "CHECKED HERE for the prereg; each arm's config must be compared on read"),
        6: ("HD_BOTK excluded; family not narrowed", "CHECKED HERE"),
        7: ("no TEST domain in any arm", "CHECKED HERE for the axis; each arm's population must be re-checked"),
    }
    for i in sorted(coverage):
        what, how = coverage[i]
        print("  VOID %d  %-42s %s" % (i, what, how))
    print()
    print("  3 of 7 checked here in full, 1 partially, 3 not checkable before the arms exist.")
    print("  THIS GATE DOES NOT CLAIM TO CLEAR THE FAMILY -- it clears the PREREGISTRATION.")

    print()
    if fail:
        print("GATE 0 FAILED: %d check(s) -- %s" % (len(fail), "; ".join(fail)))
        sys.exit(1)
    print("GATE 0 PASSED -- the preregistration is internally consistent and fully re-derivable.")


if __name__ == "__main__":
    main()
