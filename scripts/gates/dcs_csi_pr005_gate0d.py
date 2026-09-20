"""PR-CSI-005 gate 0d -- the code-identity anchor.

Compare the rescue-fired rows of CODEANCHOR_R0 (current blob) against the original KO_RAND0
(job 902005, blob bc8e777 with a DIRTY tree) on six readout fields. Expect max|diff| == 0.

NON-VACUITY IS ASSERTED, not hoped for. The first version of this script looked for a field
`rescue_positions_written` that does not exist, matched ZERO rows, and printed PASS -- which is
review finding R2-M5 ("checks that could not fail") and S-042's vacuous identity gate, committed a
third time. A gate that can pass on an empty comparison is not a gate.
"""
import json, os, glob, sys

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
SB = os.path.join(REPO, "outputs/boombness/score_behavior")
FIELDS = ["logp_concept", "logp_codeword", "semantic_logodds", "p_concept", "p_codeword", "top1_id"]
MIN_ROWS = 600  # 670 expected; anything far below means the selector is broken, not the data

A_DIR = sorted(glob.glob(os.path.join(SB, "csi1_button_train_CODEANCHOR_R0_*")))[-1]
B_DIR = os.path.join(SB, "csi1_button_train_KO_RAND0_20260916_223555_2963342")


def rows(d):
    out, fired, total = {}, 0, 0
    with open(os.path.join(d, "results.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            total += 1
            lv = r.get("rescue_liveness") or {}
            if not lv.get("fired"):
                continue
            fired += 1
            out[(r.get("domain"), r.get("family_id"))] = r
    return out, fired, total


for tag, d in (("A CODEANCHOR_R0", A_DIR), ("B KO_RAND0 (stage 1)", B_DIR)):
    m = json.load(open(os.path.join(d, "RUNMETA.json")))
    c = json.load(open(os.path.join(d, "config.json")))["args"]
    dn = json.load(open(os.path.join(d, "DONE.json")))
    print("%-22s %s" % (tag, os.path.basename(d)))
    print("    job=%s gpu=%s host=%s  git_commit=%s dirty=%s" % (
        m.get("slurm_job_id"), m.get("gpu"), m.get("hostname"),
        str(m.get("git_commit"))[:12], m.get("git_dirty")))
    print("    status=%s rows=%s failed=%s | layer=%s key=%s normkey=%s donor=%s" % (
        dn.get("status"), dn.get("rows_written"), dn.get("n_rows_failed"),
        c.get("rescue_layer"), c.get("rescue_basis_key"),
        c.get("rescue_norm_match_key"), c.get("rescue_donor")))

A, fa, ta = rows(A_DIR)
B, fb, tb = rows(B_DIR)
common = sorted(set(A) & set(B))
print("\nrows total: A=%d B=%d | rescue-FIRED: A=%d B=%d | common keys=%d (A-only=%d B-only=%d)"
      % (ta, tb, fa, fb, len(common), len(set(A) - set(B)), len(set(B) - set(A))))

# --- NON-VACUITY, asserted before any comparison is believed -------------------------------------
assert fa >= MIN_ROWS, "A fired on only %d rows -- selector broken, not a result" % fa
assert fb >= MIN_ROWS, "B fired on only %d rows -- selector broken, not a result" % fb
assert len(common) >= MIN_ROWS, "only %d common keys -- comparison is vacuous" % len(common)
for f in FIELDS:
    present = sum(1 for k in common if A[k].get(f) is not None and B[k].get(f) is not None)
    assert present == len(common), "field %s present on only %d of %d common rows" % (f, present, len(common))
print("non-vacuity: OK (%d common rescue-fired rows, all six fields present on every one)" % len(common))

bad = {}
for f in FIELDS:
    mx, n_bad = 0.0, 0
    for k in common:
        d = abs(float(A[k][f]) - float(B[k][f]))
        if d != 0.0:
            n_bad += 1
        mx = max(mx, d)
    bad[f] = (mx, n_bad)
    print("  %-18s max|diff| = %-22r nonzero_rows=%d" % (f, mx, n_bad))

ok = all(v[0] == 0.0 and v[1] == 0 for v in bad.values())
print("\nGATE 0d: %s" % ("PASS -- all six bit-identical on all %d compared rows" % len(common) if ok else "FAIL"))
if not ok:
    print("  -> POOLED family is CANNOT ANSWER. Prespecified fallback: read the 36 NEW controls alone")
    print("     as a family of 36 (floor 1/37 = 0.02703) against a candidate RE-RUN under current")
    print("     code, and DISCARD the 10. X (the PRIMARY) survives this failure unchanged.")
sys.exit(0 if ok else 1)
