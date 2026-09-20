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

# REVIEW R10 MAJOR-6. BOTH dirs used to be `sorted(glob(...))[-1]` -- "the newest dir", no job
# filter, no layer filter. This script's own docstring criticises S-134's gate 0d for a related
# omission; it should not itself resolve its arms by mtime. Both are now resolved by RUNMETA
# slurm_job_id and the resolution is asserted UNIQUE. Job ids from the sprint log: 913232 is the
# STAGEANCHOR_AXIS arm bought for this anchor, 897658 is the original basket/validation KO_AXIS.
A_JOB, B_JOB = "913232", "897658"


def by_job(pattern, job):
    hits = []
    for d in sorted(glob.glob(os.path.join(SB, pattern))):
        rm = os.path.join(d, "RUNMETA.json")
        if not os.path.exists(rm):
            continue
        if str(json.load(open(rm)).get("slurm_job_id")) == str(job):
            hits.append(d)
    assert len(hits) == 1, ("pattern %r + job %s matched %d run dirs, expected EXACTLY 1 -- "
                            "refusing to pick 'the newest' (S-127, REVIEW R10 MAJOR-6): %s"
                            % (pattern, job, len(hits), [os.path.basename(h) for h in hits]))
    return hits[0]


A_DIR = by_job("csi1_basket_validation_STAGEANCHOR_AXIS_2026*", A_JOB)
B_DIR = by_job("csi1_basket_validation_KO_AXIS_2026*", B_JOB)


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


ARGS = {}
for tag, d in (("A STAGEANCHOR_AXIS (staged)", A_DIR), ("B KO_AXIS (NFS hub path)", B_DIR)):
    m = json.load(open(os.path.join(d, "RUNMETA.json")))
    a = m["args"]
    dn = json.load(open(os.path.join(d, "DONE.json")))
    ARGS[tag[0]] = a
    print("%-30s %s" % (tag, os.path.basename(d)))
    print("    job=%s gpu=%s host=%s rows=%s" % (m.get("slurm_job_id"), m.get("gpu"), m.get("hostname"), dn.get("rows_written")))
    print("    model=%s" % a.get("model"))
    print("    layer=%s key=%s normkey=%r donor=%s" % (a.get("rescue_layer"), a.get("rescue_basis_key"),
                                                       a.get("rescue_norm_match_key"), a.get("rescue_donor")))

# --- THE CONTRAST THIS ANCHOR EXISTS TO ESTABLISH, ASSERTED --------------------------------------
# REVIEW R10 MAJOR-7. This anchor answers "does the STAGED --model path change the output?". It is
# only evidence if the two arms actually loaded the model from DIFFERENT paths. The previous
# version printed both paths and never compared them -- which is EXACTLY the omission this file's
# own docstring records against S-134's gate 0d ("BOTH of its arms used the staged path"). Written
# down and repeated anyway; now asserted.
ma, mb = str(ARGS["A"].get("model")), str(ARGS["B"].get("model"))
print("\nCONTRAST ASSERTED: --model A=%s" % ma)
print("                   --model B=%s" % mb)
print("                   DIFFER=%s | A is the staged /tmp copy=%s" % (ma != mb, ma.startswith("/tmp/")))
assert ma and ma != "None" and mb and mb != "None", "an arm carries no --model -- no contrast to make"
assert ma != mb, ("BOTH ARMS LOADED THE SAME --model PATH (%s). This anchor exists to contrast the "
                  "node-local staged copy against the shared NFS hub path; with one path on both "
                  "sides a PASS proves nothing -- which is the very failure this script's docstring "
                  "records against S-134's gate 0d (REVIEW R10 MAJOR-7)." % ma)
assert ma.startswith("/tmp/"), ("arm A is supposed to be the STAGED (node-local /tmp) load, got %r" % ma)
assert not mb.startswith("/tmp/"), ("arm B is supposed to be the shared NFS hub load, got %r" % mb)
assert os.path.basename(ma.rstrip("/")) == os.path.basename(mb.rstrip("/")), (
    "the two --model paths point at DIFFERENT revisions (%s vs %s) -- then a difference would be "
    "about the weights, not about the load path"
    % (os.path.basename(ma.rstrip("/")), os.path.basename(mb.rstrip("/"))))
# ... and every OTHER arm-defining field must AGREE, or "bit-identical" is not about the path.
# (rescue_norm_match_key is deliberately NOT in this list: A carries 'cand_rank1' and B carries '',
# and gate 0g discharges that difference separately -- with basis == norm-match-key the rescale is
# the identity, which is the whole reason this arm is arithmetically the native KO_AXIS.)
for f in ("rescue_layer", "rescue_basis_key", "rescue_donor", "bank", "expect_n"):
    va, vb = ARGS["A"].get(f), ARGS["B"].get(f)
    print("  same-by-assertion  %-22s A=%-14r B=%-14r %s" % (f, va, vb, "OK" if va == vb else "DIFFER"))
    assert va == vb, ("the two arms differ on %s (%r vs %r) -- a bit-identity result would then be "
                      "about that difference, not about the staged path" % (f, va, vb))
print("  -> the ONLY declared difference between the two arms is the --model PATH"
      " (plus the discharged rescue_norm_match_key).\n")

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
