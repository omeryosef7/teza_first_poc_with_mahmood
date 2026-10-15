#!/usr/bin/env python3
"""AMENDMENT_7 (M4): remove the TEST-inclusive `descriptive_C_dose4_all_splits_median` from every manifest's g3 block
(locked + atomic). Touches nothing else; prints only codeword + whether the key was present. Values stay recoverable from
git history / Stage-0 logs; they were never used by any gate."""
import glob, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p6_manifest_io  # noqa: E402
REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
K = "descriptive_C_dose4_all_splits_median"
for man in sorted(glob.glob(os.path.join(REPO, "outputs/heretic_csi/p6/stage0_*.json"))):
    seen = []
    def fn(m):
        for blk in (m, m.get("previous_manifest") or {}):
            g = blk.get("g3") if isinstance(blk, dict) else None
            if isinstance(g, dict) and K in g:
                g.pop(K); seen.append(True)
        return m
    p6_manifest_io.update(man, fn)
    print(os.path.basename(man), "removed" if seen else "absent")
