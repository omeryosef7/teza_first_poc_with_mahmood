#!/usr/bin/env python3
"""PR-HCSI-S084 PARENT BINDING RULE (configs/heretic_csi/ANALYSIS_COMMANDS_S084.md, S-114).

Run AFTER research/heretic_csi/p2a_powered_analyze.py (frozen, unmodified). Applies the identical decide() rule
to the frozen analyzer's own 5-dp-ROUNDED statistics and combines it with the unrounded decision:
PASS only if BOTH pass; any disagreement => "DOES NOT PASS (rounding-sensitive)"; VOID propagates.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import p2a_powered_analyze as A

POW = os.path.join(A.ROOT, "reports/heretic_csi/P2A_BUTTON_R4_POWERED.json")
OUT = os.path.join(A.ROOT, "reports/heretic_csi/P2A_BUTTON_R4_POWERED_BINDING.json")


def combine(unrounded, rounded):
    u, r = unrounded["VERDICT"], rounded["VERDICT"]
    if u.startswith("VOID") or r.startswith("VOID"):
        return u if u.startswith("VOID") else r
    if u == r:
        return u
    return "DOES NOT PASS (rounding-sensitive)"


def main():
    p = json.load(open(POW))
    d = json.load(open(A.ANA))
    ctr = d["control_recovery_distribution"]
    rs = p["decision_unrounded"]["row_set"]
    rounded = A.decide(ctr["candidate"], dict(ctr["controls"]), A.LOOKS, p["candidate_minus_KO"]["ci95"][0],
                       (not d.get("VOID")) and all(bool(v) for v in d["gates"].values()), p["VOID"],
                       rs["n_keys_common"], {a: 1 for a in rs["arms_with_dropped_keys"]})
    assert rounded["rank"] == d["verdict_basis"]["candidate_rank"], (rounded["rank"], d["verdict_basis"]["candidate_rank"])
    final = combine(p["decision_unrounded"], rounded)
    res = {"rule": "PARENT BINDING RULE (S-114): PASS only if unrounded AND rounded decisions both PASS",
           "unrounded": p["decision_unrounded"], "rounded_frozen_analyzer": rounded, "FINAL_VERDICT": final}
    json.dump(res, open(OUT, "w"), indent=1, default=str)
    print(json.dumps({"unrounded_rank": p["decision_unrounded"]["rank"], "unrounded_verdict": p["decision_unrounded"]["VERDICT"],
                      "rounded_rank": rounded["rank"], "rounded_verdict": rounded["VERDICT"],
                      "holm_unrounded": p["decision_unrounded"]["holm"], "holm_rounded": rounded["holm"],
                      "FINAL_VERDICT": final}, indent=1))


if __name__ == "__main__":
    main()
