"""Measure every undocumented SHORT run and add a KNOWN_SHORT entry with its evidence.

Deliberately NOT a blanket exemption: each entry records the measured domain spread and the
complete list of failing prompt_ids, and the run is only exempted if its failure_reasons are
exclusively the norm-match degeneracy guard. Anything else is REPORTED and left to fail.

REVIEW R9b / R10 fixed four ways this could write, or claim, something it had not measured:

  MAJOR-2  IT WOULD EXEMPT A LOSS FAR BEYOND --allow-short AND SAY OTHERWISE. A synthetic run that
           lost 50 of 670 rows across 5 whole domains, with a failure_reasons ledger summing to 1,
           was documented with an exemption reading "Within the declared --allow-short 4". Nothing
           compared the measured shortfall to the ceiling, and nothing checked that the ledger's
           reasons summed to n_rows_failed. Both are now REFUSAL conditions, and the ceiling is
           READ from the preregistration rather than baked into the template string.

  MAJOR-3  NO SIZE ASSERTION ON THE COMPARISON. A run whose reference arm shared no keys with it
           produced "0 lost row(s) ... in 0 distinct domain(s) ... n_failed 0" -- a self-
           contradicting exemption (669 succeeded of 670 attempted, 0 failed) with an EMPTY
           evidence list, written without complaint. This is the standing S-134 / S-042 lesson.
           The reference's key count, the missing set and their agreement with the ledger are all
           asserted before anything is formatted.

  MAJOR-4  THE REFERENCE ARM WAS PICKED BY mtime FROM A 72%-WRONG-LAYER POOL. `rid.rsplit("_", 3)
           [0].rsplit("_", 1)[0]` truncated the arm name mid-way ("csi1_button_train_KO"), globbed
           118 dirs, filtered only on row count, and took `sorted(cands)[-1]` -- the NEWEST BY
           mtime. Measured: 83 candidates, 60 of them rescue_layer=20. It got layer-18 references
           only because those happened to be the newest that day. The family prefix now comes from
           the run's OWN config (tag minus arm, exactly), candidates must match on rescue_layer,
           bank, expect_n and rescue_donor, the same slurm allocation is PREFERRED and the
           selection is deterministic (sorted run_id), never mtime.

  MAJOR-8  IT PRINTED "documented:" AFTER A str.replace THAT MAY HAVE CHANGED NOTHING. If the
           anchor "KNOWN_SHORT = {\\n" is ever absent the replace is a no-op and the script still
           printed success and counted the entry. The anchor is asserted present, the replace is
           asserted to have CHANGED the text and to contain the new block, and the file is written
           atomically (temp + fsync + replace), read back, byte-counted and re-parsed -- this is
           NFS with an asynchronous EDQUOT (S-124).
"""
import json, os, glob, collections, re, subprocess, sys, ast, tempfile

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
P = os.path.join(REPO, "src/boombness/run_completeness_check.py")
SB = os.path.join(REPO, "outputs/boombness/score_behavior")
DEGEN = "norm-match DEGENERATE"

# THE CEILING IS READ, NOT BAKED. configs/dcs_csi_pr005_button_L18_family.json:285 says "Do NOT
# widen --allow-short"; the machine-readable copy of that number lives in the necessity family
# config. A documenter that prints the ceiling but never compares to it is the MAJOR-2 defect.
ALLOW_SHORT_CFG = os.path.join(REPO, "configs/dcs_csi_pr003a_necessity_family.json")
ALLOW_SHORT = json.load(open(ALLOW_SHORT_CFG))["population"]["allow_short"]
assert isinstance(ALLOW_SHORT, int) and 0 < ALLOW_SHORT < 100, \
    "allow_short read from %s is %r -- refusing to run with a nonsense ceiling" % (ALLOW_SHORT_CFG, ALLOW_SHORT)

# Config fields a reference arm must MATCH for its key set to be the same population as the short
# run's. rescue_layer is the S-127 field: the same tag exists at L18 and at L20.
REF_MUST_MATCH = ("rescue_layer", "bank", "expect_n", "rescue_donor")

TEMPLATE = (
    "DCS-CSI-133: {exp}. {n} row(s) of {exp_n} REFUSED by the sprint's own norm-match degeneracy "
    "guard (SubspaceDonorPatch, review R2-M5) with 'REFUSING to patch: N of 28 positions are "
    "norm-match DEGENERATE': the control basis was near-orthogonal to the clean->KO delta at some "
    "position, so rescaling its projection would have amplified float noise into an arbitrary "
    "QR-gauge direction. The guard declines to fabricate a control rather than silently write a "
    "meaningless one. This is the EXPECTED 3090 behaviour recorded in DCS-CSI-121's table "
    "(norm-matched on 3090: 669-670 rows every time; the V100 column is 0 rows every time, which "
    "is why that hardware is a VOID condition). MECHANISM (not a verified property of this run): "
    "degeneracy is the angle between a fixed basis and a fixed delta, both determined before any "
    "readout, and the delta is identical across arms -- so the loss is expected to be "
    "outcome-independent. MEASURED here against the full {refn}-row arm {ref} ({alloc}, "
    "rescue_layer {layer}): the {n} lost row(s) fall in {d} distinct domain(s), at most {m} row(s) "
    "per domain out of 10, and both analysers intersect (domain, slot) KEYS across all arms before "
    "averaging, so every arm is compared on the same key set regardless. Within the declared "
    "--allow-short {allow} (measured shortfall {n}). Ledger: n_attempted {exp_n}, n_succeeded {s}, "
    "n_failed {n}. Failing prompt_ids (complete): {pids}."
)


def keys_of(d):
    ks, pids = set(), {}
    with open(os.path.join(d, "results.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            k = (r.get("domain"), r.get("family_id") or r.get("slot") or r.get("prompt_sha16"))
            ks.add(k)
            pids[k] = r.get("prompt_id")
    return ks, pids


def family_prefix(args):
    """The run tag with its ARM stripped, exactly -- not by counting underscores.

    The old `rid.rsplit("_", 3)[0].rsplit("_", 1)[0]` turned KO_SHUF9 into "csi1_button_train_KO"
    and matched 118 unrelated dirs; a run tagged plain "KO" would have stripped to
    "csi1_button_train" and matched BASE as a reference (REVIEW R9b MAJOR-4).
    """
    tag, arm = args.get("tag") or "", args.get("arm") or ""
    if arm and tag.endswith("_" + arm):
        return tag[:-(len(arm) + 1)]
    return None


def wrap(text, indent="        ", width=96):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        lines.append(cur)
    body = "\n".join('%s"%s "' % (indent, l.replace('"', '\\"')) for l in lines[:-1])
    return body + '\n%s"%s",' % (indent, lines[-1].replace('"', '\\"'))


def atomic_write_and_verify(path, text):
    """Temp + fsync + os.replace, then READ BACK, byte-count and re-parse.

    NFS reports EDQUOT ASYNCHRONOUSLY (S-124): a write that returned cleanly can still have landed
    truncated, and `os.path.getsize` on a successful-then-truncated file looks just as plausible.
    The only evidence a write happened is reading it back.
    """
    want = text.encode()
    dirn = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=dirn, prefix=".tmp_", suffix=".py")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(want)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    with open(path, "rb") as fh:
        got = fh.read()
    assert got == want, ("READ-BACK MISMATCH on %s: wrote %d bytes, read %d back. NFS/EDQUOT "
                         "(S-124). The file is NOT what this script intended." % (path, len(want), len(got)))
    ast.parse(got.decode())
    return len(got)


# 1. find undocumented SHORT runs from the guard itself
out = subprocess.run([sys.executable, os.path.join(REPO, "src/boombness/run_completeness_check.py")],
                     capture_output=True, text=True, cwd=REPO).stdout
shorts = re.findall(r"SHORT (\S+): persisted (\d+) rows in results\.jsonl against --expect-n (\d+)", out)
print("undocumented SHORT runs:", len(shorts))
print("declared ceiling: --allow-short %d (read from %s)" % (ALLOW_SHORT, os.path.relpath(ALLOW_SHORT_CFG, REPO)))
if not shorts:
    sys.exit(0)

src = open(P).read()
anchor = "KNOWN_SHORT = {\n"
# MAJOR-8: the anchor is asserted PRESENT before a single entry is built, not hoped for.
assert src.count(anchor) == 1, (
    "the KNOWN_SHORT anchor %r occurs %d times in %s -- every str.replace below would be a NO-OP "
    "(or ambiguous) while this script printed 'documented:' anyway (REVIEW R9b MAJOR-8)"
    % (anchor, src.count(anchor), P))
added, refused = 0, []

for rid, got, expn in shorts:
    d = os.path.join(SB, rid)
    expn = int(expn)
    got = int(got)
    done = json.load(open(os.path.join(d, "DONE.json")))
    reasons = done.get("failure_reasons") or {}
    if not reasons or not all(DEGEN in str(k) for k in reasons):
        refused.append((rid, "not a pure degeneracy loss: %s" % (list(reasons)[:1] or "no ledger")))
        continue

    # --- MAJOR-2: the shortfall must be WITHIN the declared ceiling, and the ledger must ACCOUNT
    #     for it. Both were previously unchecked while the template asserted compliance. ----------
    n_failed = int(done.get("n_rows_failed") or 0)
    n_attempt = int(done.get("n_rows_attempted") or 0)
    reason_sum = sum(int(v) for v in reasons.values())
    shortfall = expn - got
    if shortfall > ALLOW_SHORT:
        refused.append((rid, "shortfall %d rows EXCEEDS the declared --allow-short %d -- the "
                             "preregistration says RE-RUN via group X, never exempt"
                        % (shortfall, ALLOW_SHORT)))
        continue
    if not (reason_sum == n_failed == shortfall):
        refused.append((rid, "ledger does not account for the loss: sum(failure_reasons)=%d, "
                             "n_rows_failed=%d, expect_n - rows_written=%d -- these must agree"
                        % (reason_sum, n_failed, shortfall)))
        continue
    if n_attempt and n_attempt != expn:
        refused.append((rid, "ledger n_attempted=%d but --expect-n is %d" % (n_attempt, expn)))
        continue

    # --- MAJOR-4: the reference arm, filtered by CONFIG and chosen DETERMINISTICALLY -------------
    args = json.load(open(os.path.join(d, "config.json")))["args"]
    meta = json.load(open(os.path.join(d, "RUNMETA.json")))
    job = str(meta.get("slurm_job_id"))
    fam = family_prefix(args)
    if not fam:
        refused.append((rid, "cannot derive the arm-stripped family prefix from tag=%r arm=%r"
                        % (args.get("tag"), args.get("arm"))))
        continue
    pool, same_job = [], []
    for o in sorted(glob.glob(os.path.join(SB, fam + "_*"))):
        if os.path.abspath(o) == os.path.abspath(d):
            continue
        need = [os.path.join(o, x) for x in ("DONE.json", "config.json", "RUNMETA.json", "results.jsonl")]
        if not all(os.path.exists(x) for x in need):
            continue
        dj = json.load(open(need[0]))
        if dj.get("rows_written") != expn:
            continue
        ao = json.load(open(need[1]))["args"]
        if family_prefix(ao) != fam:
            continue
        if any(ao.get(k) != args.get(k) for k in REF_MUST_MATCH):
            continue
        pool.append(o)
        if str(json.load(open(need[2])).get("slurm_job_id")) == job:
            same_job.append(o)
    if not pool:
        refused.append((rid, "no CONFIG-COMPATIBLE full-row reference arm in family %r (matched on "
                             "%s)" % (fam, ", ".join(REF_MUST_MATCH))))
        continue
    # prefer the same slurm allocation; deterministic by run_id either way, NEVER by mtime
    chosen = sorted(same_job or pool)[-1]
    ref_meta = json.load(open(os.path.join(chosen, "RUNMETA.json")))
    ref_job = str(ref_meta.get("slurm_job_id"))
    alloc = ("of the SAME slurm allocation %s" % job if same_job else
             "from slurm allocation %s, while the short run is %s -- no full-row arm of the same "
             "allocation was available" % (ref_job, job))

    kr, pr = keys_of(chosen)
    kk, _ = keys_of(d)
    missing = kr - kk

    # --- MAJOR-3: the comparison's SIZE is asserted before its result is believed ----------------
    if len(kr) != expn:
        refused.append((rid, "reference %s holds %d distinct keys, not %d -- the comparison is not "
                             "over the full arm" % (os.path.basename(chosen), len(kr), expn)))
        continue
    if len(kk) != got:
        refused.append((rid, "short run holds %d distinct keys but %d rows -- duplicate keys, the "
                             "missing set would be wrong" % (len(kk), got)))
        continue
    if len(missing) != n_failed or len(missing) == 0:
        refused.append((rid, "missing-key set is %d rows but the ledger says %d failed -- refusing "
                             "to write an exemption whose evidence list does not match its ledger "
                             "(a ZERO-row exemption is the S-134 pattern)" % (len(missing), n_failed)))
        continue
    if kk - kr:
        refused.append((rid, "the short run holds %d keys the reference does not -- they are not "
                             "the same prompt population" % len(kk - kr)))
        continue

    doms = collections.Counter(k[0] for k in missing)
    assert doms, "unreachable: len(missing) > 0 was asserted above"
    entry = TEMPLATE.format(
        exp="PR-CSI-005 button L18 family" if "button" in rid else "PR-CSI-003 necessity",
        n=len(missing), exp_n=expn, s=got, refn=expn,
        ref=os.path.basename(chosen), alloc=alloc, layer=args.get("rescue_layer"),
        allow=ALLOW_SHORT,
        d=len(doms), m=max(doms.values()),
        pids=", ".join(sorted(str(pr[k]) for k in missing)))
    block = '    "%s":\n%s\n' % (rid, wrap(entry))

    # --- MAJOR-8: the replace must actually have CHANGED the text -------------------------------
    before = src
    src = src.replace(anchor, anchor + block, 1)
    assert src != before, (
        "str.replace was a NO-OP for %s -- the anchor %r is not in the text this script is holding. "
        "The old version printed 'documented:' here anyway (REVIEW R9b MAJOR-8)." % (rid, anchor))
    assert block in src, "the block for %s is not in the text after the replace" % rid
    assert src.count('    "%s":' % rid) == 1, "entry for %s appears %d times" % (rid, src.count('    "%s":' % rid))
    print("documented: %s  (%s/%s rows, %d lost, %d domains, ref %s %s)"
          % (rid, got, expn, len(missing), len(doms), os.path.basename(chosen),
             "[same alloc]" if same_job else "[DIFFERENT alloc %s]" % ref_job))
    added += 1

if added:
    n = atomic_write_and_verify(P, src)
    print("wrote %d bytes to %s (read back and re-parsed; %d entries added)" % (n, P, added))
    # and the table really does hold every rid we just claimed to document
    tbl = open(P).read()
    for rid, _, _ in shorts:
        if rid in [r for r, _ in refused]:
            continue
        assert '    "%s":' % rid in tbl, "entry for %s is not in the file on disk" % rid
else:
    print("nothing written (0 entries added)")
for rid, why in refused:
    print("REFUSED to exempt:", rid, "--", why)
# A refusal is not "nothing to do": the run stays undocumented and run_completeness_check.py will
# keep FAILING on it, which is the intended outcome. Exiting 0 on a refusal made the two cases
# indistinguishable to a caller (REVIEW R9b MINOR-2, same class).
if refused:
    print("%d run(s) REFUSED. They remain undocumented and the completeness guard will keep "
          "failing on them -- that is the point. Do not widen the ceiling to make this pass."
          % len(refused))
sys.exit(1 if refused else 0)
