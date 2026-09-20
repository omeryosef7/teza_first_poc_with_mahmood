"""PR-CSI-008 GATE 0 -- the P3 pre-GPU lexical screen. Runs BEFORE any P3 GPU number exists.

Every gate prints the SIZE of its comparison and asserts that size FIRST (sprint entry S-134): a
gate that can pass on an empty comparison is not a gate. Here the sizes are the candidate count and
the corpus row count, and either being 0 ABORTS.

Two things this gate deliberately does NOT do:
  * it does not hardcode a single threshold. Every number comes out of the preregistration, so the
    gate cannot drift away from the document that froze it (S-138's cell-assignment lesson: the
    prose and the rule must not be able to disagree);
  * it does not trust the stored token audit. It re-tokenises every candidate LIVE and aborts on
    disagreement -- S-139's lesson, where a field was added to one code path and never reached the
    artifact, and only running the thing caught it.
"""
import json, os, re, sys, hashlib, tempfile

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
os.chdir(REPO)
PREREG = "configs/dcs_csi_pr008_codeword_screen.json"

fail = []


def sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:32]


def atomic_write_json(path, obj):
    """Temp + fsync + SIZE CHECK + RE-PARSE **of the temp file** + chmod + os.replace.

    R11 fixed two regressions here against the canonical S-130 helper
    (scripts/rah_verify_phase1.py:230-262), both of which R11 demonstrated rather than argued:

      * ORDER. The first version called os.replace FIRST and read back afterwards, so a short write
        -- which is exactly what EDQUOT produces, and the quota is at 197 G of 200 G -- landed at
        the real artifact name and DESTROYED the previous good report before anything checked it.
        That is the S-124 outcome the sprint spent 138 sites eliminating. Everything is now verified
        on the TEMP file, so the destination is unchanged on any failure.
      * PERMISSIONS. The first version chmod'd only when the destination already existed, so on a
        first run mkstemp's 0600 rode through os.replace onto the report. Measured: the committed
        report was the ONLY 0600 file among 237 in reports/. The canonical helper's `except OSError:
        mode = 0o644` fallback is restored.

    Raises rather than asserts: `python -O` strips asserts, and this is the only verification the
    helper has.
    """
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_atomic_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())          # EDQUOT surfaces HERE, not in a GC finaliser
        n = os.path.getsize(tmp)
        if n == 0:
            raise OSError("temp file is 0 bytes after a flush+fsync that reported success")
        with open(tmp, "r", encoding="utf-8") as fh:
            json.load(fh)                  # a truncated write does not re-parse
        try:
            mode = os.stat(path).st_mode & 0o7777
        except OSError:
            mode = 0o644
        os.chmod(tmp, mode)
        os.replace(tmp, path)              # atomic within the directory
    except Exception as e:
        try:
            nb = os.path.getsize(tmp)
        except OSError:
            nb = -1
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise OSError("atomic_write_json FAILED for %s -- %d bytes reached the temp file; the "
                      "destination is UNCHANGED (never truncated). Cause: %r" % (path, nb, e)) from e
    return os.path.getsize(path)


pr = json.load(open(PREREG))
crit = {c["id"]: c for c in pr["criteria"]}

# ---- VOID condition 2: corpus identity -------------------------------------------------------
corpus_p = pr["corpus"]["path"]
got_sha = sha16(corpus_p)
print("[gate0] corpus %s\n        sha16 %s (prereg %s)" % (corpus_p, got_sha, pr["corpus"]["sha256_16"]))
if got_sha != pr["corpus"]["sha256_16"]:
    sys.exit("VOID condition 2: corpus sha16 %s != prereg %s" % (got_sha, pr["corpus"]["sha256_16"]))

aud_p = pr["candidate_pool_source"]["artifact"]
aud_sha = sha16(aud_p)
print("[gate0] audit  %s\n        sha16 %s (prereg %s)" % (aud_p, aud_sha, pr["candidate_pool_source"]["sha256_16"]))
if aud_sha != pr["candidate_pool_source"]["sha256_16"]:
    sys.exit("VOID: candidate pool artifact sha16 %s != prereg %s" % (aud_sha, pr["candidate_pool_source"]["sha256_16"]))

audit = json.load(open(aud_p))
cands = [r["word"] for r in audit["rows"]]
stored = {r["word"]: r for r in audit["rows"]}

# ---- NON-VACUITY, asserted FIRST (S-134) -----------------------------------------------------
print("[gate0] SIZE candidates = %d" % len(cands))
assert len(cands) > 0, "VACUOUS: zero candidates"
assert len(cands) == pr["candidate_pool_source"]["n_candidates"], (
    "candidate count %d != prereg %d" % (len(cands), pr["candidate_pool_source"]["n_candidates"]))

rows = [json.loads(l) for l in open(corpus_p)]
print("[gate0] SIZE corpus rows = %d" % len(rows))
assert len(rows) > 0, "VACUOUS: zero corpus rows"
assert len(rows) == pr["corpus"]["n_rows"], "corpus rows %d != prereg %d" % (len(rows), pr["corpus"]["n_rows"])
ndom = len({r["domain"] for r in rows})
assert ndom == pr["corpus"]["n_domains"], "domains %d != prereg %d" % (ndom, pr["corpus"]["n_domains"])

# ---- VOID condition 1 + L1: LIVE re-tokenisation ---------------------------------------------
from transformers import AutoTokenizer
snap = pr["tokenizer"]["snapshot"]
tok_path = "/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/" + snap
if not os.path.isdir(tok_path):
    sys.exit("VOID condition 1: tokenizer snapshot dir absent: %s" % tok_path)
tk = AutoTokenizer.from_pretrained(tok_path)
print("[gate0] tokenizer loaded from snapshot %s" % snap[:12])

live = {}
drift = []
for w in cands:
    t_space = tk.tokenize(" " + w)
    t_bare = tk.tokenize(w)
    t_cap = tk.tokenize(" " + w.capitalize())
    live[w] = dict(n_tok_space=len(t_space), n_tok_bare=len(t_bare), n_tok_cap=len(t_cap),
                   tok_space=t_space)
    s = stored[w]
    for k in ("n_tok_space", "n_tok_bare", "n_tok_cap"):
        if live[w][k] != s[k]:
            drift.append((w, k, s[k], live[w][k]))
if drift:
    for w, k, a, b in drift:
        print("  DRIFT %-12s %-12s stored=%s live=%s" % (w, k, a, b))
    sys.exit("ABORT: stored token audit disagrees with live tokenisation on %d field(s). The audit "
             "artifact is stale or the tokenizer changed; either way the pool is not what the "
             "preregistration describes." % len(drift))
print("[gate0] live re-tokenisation agrees with stored audit on %d candidates x 3 fields" % len(cands))

# ---- L2: incidental literal incidence --------------------------------------------------------
texts = [(r.get("full_prompt") or "") for r in rows]
N = len(texts)
inc = {}
for w in cands:
    pat = re.compile(r"\b" + re.escape(w) + r"\b", re.I)
    inc[w] = sum(1 for t in texts if pat.search(t))

# ---- apply the criteria ----------------------------------------------------------------------
L2_thr = crit["L2"]["threshold"]
L2_exempt = set(crit["L2"].get("exempt", []))
deny = set(crit["L3"]["denylist"])

results = []
for w in cands:
    r = dict(word=w, n_tok_space=live[w]["n_tok_space"], n_tok_bare=live[w]["n_tok_bare"],
             n_tok_cap=live[w]["n_tok_cap"], tok_space=live[w]["tok_space"],
             incidence_rows=inc[w], incidence_rate=round(inc[w] / N, 6))
    r["L1_pass"] = (live[w]["n_tok_space"] == 1)
    r["L2_exempt"] = w in L2_exempt
    r["L2_pass"] = True if r["L2_exempt"] else (inc[w] / N <= L2_thr)
    r["L3_pass"] = w.lower() not in deny
    results.append(r)

surv = [r["word"] for r in results if r["L1_pass"] and r["L2_pass"] and r["L3_pass"]]

# ---- L5: pairwise distinctness among SURVIVORS ------------------------------------------------
nested = sorted({(a, b) for a in surv for b in surv if a != b and a in b})
for a, b in nested:
    fail.append("L5: surviving candidate %r is a substring of %r" % (a, b))
for r in results:
    r["L5_pass"] = r["word"] in surv and not any(r["word"] == a or r["word"] == b for a, b in nested)

final = [w for w in surv if not any(w == a or w == b for a, b in nested)]

# ---- report ------------------------------------------------------------------------------------
print("\n%-12s %6s %6s %5s %8s %8s  %s" % ("word", "space", "bare", "cap", "rows", "rate", "verdict"))
for r in sorted(results, key=lambda x: (-int(x["word"] in final), x["incidence_rate"])):
    why = []
    if not r["L1_pass"]: why.append("L1 multi-token(%d)" % r["n_tok_space"])
    if not r["L2_pass"]: why.append("L2 incidence %.3f%%" % (100 * r["incidence_rate"]))
    if not r["L3_pass"]: why.append("L3 denylist")
    v = "KEEP" if r["word"] in final else "drop: " + ", ".join(why)
    if r["L2_exempt"]: v += "  [L2 exempt: own codeword]"
    print("%-12s %6d %6d %5d %8d %7.2f%%  %s" % (r["word"], r["n_tok_space"], r["n_tok_bare"],
                                                 r["n_tok_cap"], r["incidence_rows"],
                                                 100 * r["incidence_rate"], v))

print("\n[gate0] survivors: %d of %d" % (len(final), len(cands)))
assert len(final) > 0, "FAILURE: zero survivors -- a pool of nothing is not a pass"

out = dict(schema="dcs_csi_pr008_lexical_screen/1", prereg=PREREG, prereg_id=pr["id"],
           corpus=dict(path=corpus_p, sha16=got_sha, n_rows=N, n_domains=ndom),
           candidate_pool=dict(artifact=aud_p, sha16=aud_sha, n=len(cands)),
           tokenizer=dict(snapshot=snap),
           thresholds=dict(L2=L2_thr, L2_exempt=sorted(L2_exempt), L3_denylist_n=len(deny)),
           rows=results, survivors=final, n_survivors=len(final),
           nested_pairs_dropped=[list(x) for x in nested], failures=fail)
p_out = pr["outputs"]["report"]
n = atomic_write_json(p_out, out)
print("[gate0] wrote+verified %s (%d bytes)" % (p_out, n))

if fail:
    print("\nGATE 0 FAILURES:")
    for f in fail:
        print("  -", f)
    sys.exit(1)
print("\nGATE 0 PASS")
