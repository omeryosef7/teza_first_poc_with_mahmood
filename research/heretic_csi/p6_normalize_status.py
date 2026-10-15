#!/usr/bin/env python3
"""One-off (review #8): add explicit g1_status / g2_status / g3_status to existing Stage-0 manifests with the SAME
rules as p6_write_manifest.py / p6_g2.py; locked + atomic. Never changes any measured value."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p6_manifest_io  # noqa: E402
REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"


def norm(m):
    st = m.get("status")
    g3 = m.get("g3") or {}; g1 = m.get("g1"); g2 = m.get("g2")
    m["g3_status"] = g3.get("G3") if st in ("G3_PASS", "G3_FAIL", "ERROR_EXTRACT") else "UNDECIDED"
    m["g1_status"] = (("PASS" if g1["ci95"][0] > 0.05 else "FAIL") if isinstance(g1, dict) and "ci95" in g1 else
                      ("NOT_APPLICABLE_G3_FAIL" if st == "G3_FAIL" else "UNDECIDED"))
    m["g2_status"] = (g2["G2"] if isinstance(g2, dict) and "G2" in g2 else
                      ("NOT_APPLICABLE_G3_FAIL" if st == "G3_FAIL" else "UNDECIDED"))
    return m


for cw in sys.argv[1:]:
    man = os.path.join(REPO, f"outputs/heretic_csi/p6/stage0_{cw}.json")
    m = p6_manifest_io.update(man, norm)
    print(cw, m["status"], "g3", m["g3_status"], "g1", m["g1_status"], "g2", m["g2_status"])
