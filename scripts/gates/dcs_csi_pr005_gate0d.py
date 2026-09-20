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

# REVIEW R10 MAJOR-6. A_DIR used to be `sorted(glob(...))[-1]` -- "the newest dir", with no job
# filter and no layer filter. That is the S-127 hazard by name: every tag exists twice, once at
# L18 and once at L20, and "newest" picked the wrong twin once already. Both arms are now resolved
# by their RUNMETA slurm_job_id and the resolution is asserted UNIQUE. The job ids are the ones in
# the sprint log: 912838 is the CODEANCHOR_R0 re-run under the current blob, 902005 is stage 1's
# original KO_RAND0. (B_DIR was hardcoded to a path, which is unique but says nothing about WHY;
# the glob for KO_RAND0 matches two dirs, one at L18 and one at L20, so the filter is load-bearing.)
A_JOB, B_JOB = "912838", "902005"


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


A_DIR = by_job("csi1_button_train_CODEANCHOR_R0_*", A_JOB)
B_DIR = by_job("csi1_button_train_KO_RAND0_2026*", B_JOB)


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


meta = {}
for tag, d in (("A CODEANCHOR_R0", A_DIR), ("B KO_RAND0 (stage 1)", B_DIR)):
    m = json.load(open(os.path.join(d, "RUNMETA.json")))
    c = json.load(open(os.path.join(d, "config.json")))["args"]
    dn = json.load(open(os.path.join(d, "DONE.json")))
    meta[tag[0]] = (m, c)
    print("%-22s %s" % (tag, os.path.basename(d)))
    print("    job=%s gpu=%s host=%s  git_commit=%s dirty=%s" % (
        m.get("slurm_job_id"), m.get("gpu"), m.get("hostname"),
        str(m.get("git_commit"))[:12], m.get("git_dirty")))
    print("    status=%s rows=%s failed=%s | layer=%s key=%s normkey=%s donor=%s" % (
        dn.get("status"), dn.get("rows_written"), dn.get("n_rows_failed"),
        c.get("rescue_layer"), c.get("rescue_basis_key"),
        c.get("rescue_norm_match_key"), c.get("rescue_donor")))

# --- THE CONTRAST THIS GATE EXISTS TO ESTABLISH, ASSERTED ----------------------------------------
# REVIEW R10 MAJOR-7. This is a CODE-IDENTITY anchor: it is only evidence if the two arms ran
# DIFFERENT blobs. It used to print `git_commit=dabfeb854ec6` vs `git_commit=bc8e77793633` and
# never compare them -- so if both arms had run the same blob the gate would have passed and
# proved nothing, which is the S-042 vacuous-identity-gate shape. It also never asserted that
# everything ELSE about the two arms is the same, without which "bit-identical" is not a
# statement about the code.
ga = str(meta["A"][0].get("git_commit"))
gb = str(meta["B"][0].get("git_commit"))
print("\nCONTRAST ASSERTED: git_commit A=%s vs B=%s -> DIFFER=%s" % (ga[:12], gb[:12], ga != gb))
assert ga and ga != "None", "arm A carries no git_commit -- the contrast cannot be established"
assert gb and gb != "None", "arm B carries no git_commit -- the contrast cannot be established"
assert ga != gb, ("BOTH ARMS RAN THE SAME BLOB (%s). This gate is a CODE-identity anchor; with one "
                  "blob on both sides a PASS proves nothing at all (REVIEW R10 MAJOR-7, S-042)."
                  % ga[:12])
SAME = ["rescue_layer", "rescue_basis_key", "rescue_norm_match_key", "rescue_donor", "bank", "expect_n"]
for f in SAME:
    va, vb = meta["A"][1].get(f), meta["B"][1].get(f)
    print("  same-by-assertion  %-24s A=%-14r B=%-14r %s" % (f, va, vb, "OK" if va == vb else "DIFFER"))
    assert va == vb, ("the two arms differ on %s (%r vs %r) -- a bit-identity result would then be "
                      "about that difference, not about the code blob" % (f, va, vb))
print("  -> the ONLY declared difference between the two arms is the code blob.\n")

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
