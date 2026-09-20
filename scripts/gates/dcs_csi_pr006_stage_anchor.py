"""PR-CSI-006 staging anchor -- does loading the model from the node-local staged copy produce
bit-identical output to loading it from the shared NFS snapshot path?

WHY THIS EXISTS. PR-CSI-006 gate 0g diffs each swap arm's RUNMETA.argv against the recipient's own
native KO_AXIS. For basket/validation the diff included --model: the swap arm loaded
/tmp/dcs_snap_omeryosef/<rev> and the native loaded the shared hub path .../snapshots/<rev>. Same
revision, different path. The preregistration calls staging "a load-time workaround that touches
nothing scientific" -- but that is an ARGUMENT.

S-134's gate 0d did NOT settle it: BOTH of its arms used the staged path (measured). So one arm was
bought: the basket/validation KO_AXIS re-run under the staged path as STAGEANCHOR_AXIS, with
basis == norm-match-key == cand_rank1 so the rescale is the IDENTITY and the arm is arithmetically
the native KO_AXIS.

Non-vacuity is asserted before any difference is believed (S-134).
"""
import json, os, glob, sys

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
SB = os.path.join(REPO, "outputs/boombness/score_behavior")
FIELDS = ["logp_concept", "logp_codeword", "semantic_logodds", "p_concept", "p_codeword", "top1_id"]
MIN_ROWS = 220  # 230 expected

A_DIR = sorted(glob.glob(os.path.join(SB, "csi1_basket_validation_STAGEANCHOR_AXIS_2026*")))[-1]
B_DIR = sorted(glob.glob(os.path.join(SB, "csi1_basket_validation_KO_AXIS_2026*")))[-1]


def rows(d):
    out, fired, total = {}, 0, 0
    with open(os.path.join(d, "results.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            total += 1
            if not (r.get("rescue_liveness") or {}).get("fired"):
                continue
            fired += 1
            out[(r.get("domain"), r.get("family_id"))] = r
    return out, fired, total


for tag, d in (("A STAGEANCHOR_AXIS (staged)", A_DIR), ("B KO_AXIS (NFS hub path)", B_DIR)):
    m = json.load(open(os.path.join(d, "RUNMETA.json")))
    a = m["args"]
    dn = json.load(open(os.path.join(d, "DONE.json")))
    print("%-30s %s" % (tag, os.path.basename(d)))
    print("    job=%s gpu=%s host=%s rows=%s" % (m.get("slurm_job_id"), m.get("gpu"), m.get("hostname"), dn.get("rows_written")))
    print("    model=%s" % a.get("model"))
    print("    layer=%s key=%s normkey=%r donor=%s" % (a.get("rescue_layer"), a.get("rescue_basis_key"),
                                                       a.get("rescue_norm_match_key"), a.get("rescue_donor")))

A, fa, ta = rows(A_DIR)
B, fb, tb = rows(B_DIR)
common = sorted(set(A) & set(B))
print("\nrows total A=%d B=%d | rescue-FIRED A=%d B=%d | common=%d (A-only=%d B-only=%d)"
      % (ta, tb, fa, fb, len(common), len(set(A) - set(B)), len(set(B) - set(A))))

assert fa >= MIN_ROWS, "A fired on only %d rows -- selector broken" % fa
assert fb >= MIN_ROWS, "B fired on only %d rows -- selector broken" % fb
assert len(common) >= MIN_ROWS, "only %d common keys -- comparison is vacuous" % len(common)
for f in FIELDS:
    present = sum(1 for k in common if A[k].get(f) is not None and B[k].get(f) is not None)
    assert present == len(common), "field %s on only %d of %d rows" % (f, present, len(common))
print("non-vacuity: OK (%d common rescue-fired rows, all six fields present on every one)" % len(common))

bad = {}
for f in FIELDS:
    mx, n = 0.0, 0
    for k in common:
        d = abs(float(A[k][f]) - float(B[k][f]))
        if d != 0.0:
            n += 1
        mx = max(mx, d)
    bad[f] = (mx, n)
    print("  %-18s max|diff| = %-22r nonzero_rows=%d" % (f, mx, n))

ok = all(v[0] == 0.0 and v[1] == 0 for v in bad.values())
print("\nSTAGING ANCHOR: %s" % ("PASS -- node-local staging is INERT on all %d compared rows; the "
                                "--model path difference in gate 0g is a load-time path, not a "
                                "scientific difference" % len(common) if ok else
                                "FAIL -- staging CHANGES the output; the basket/validation cell is CANNOT ANSWER"))
sys.exit(0 if ok else 1)
