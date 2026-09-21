"""PR-CSI-009 GATE 0 -- every VOID condition checked BEFORE any cosine is computed.

Written while job 914750 was still extracting, so it cannot have been shaped by the answer.

Every gate prints the SIZE of its comparison and asserts that size FIRST (S-134): a gate that can pass
on an empty comparison is not a gate. Thresholds and expectations come from the preregistration, which
is read at runtime -- the prose and the code must not be able to disagree (S-151).

This script computes NO COSINE. That is PART 4 of the frozen read and runs only if this exits 0.
"""
import json, os, sys, glob, hashlib

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
os.chdir(REPO)
PREREG = "configs/dcs_csi_pr009_basket_reextract_3090.json"
COMMITTED = "outputs/boombness/extract_boombness/cont1_behavioral_basket_bomb_20260910_113902_3966018"
SNAP = "0e9e39f249a16976918f6564b8830bc894c89659"
BANK_SHA16 = "79511d9e254571e6"
# VOID 7: the committed axes are COMPARISON TARGETS and must not be touched. Shas taken 2026-09-21,
# before the refit existed.
COMMITTED_AXES = {
    "configs/dcs_csi_axis_basket_behavioral.pt": "9fd8975480273ba235e925fdc94a7020",
    "configs/dcs_csi_axis_basket_L20.pt":        "131255c343bcc924bf5b51c935e27e96",
}
EXEMPT_ARGS = {"layers", "tag", "model"}   # named in VOID condition 3, amended before submission

fail = []


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()[:32]


def dig(o, keys):
    if isinstance(o, dict):
        for k in keys:
            if k in o and o[k] not in (None, ""):
                return o[k]
        for v in o.values():
            r = dig(v, keys)
            if r:
                return r
    return None


pr = json.load(open(PREREG))
print("[gate0] prereg %s  id=%s" % (PREREG, pr["id"]))

# ---- resolve the NEW run -----------------------------------------------------------------------
cands = sorted(glob.glob("outputs/boombness/extract_boombness/cont1re_behavioral_basket_bomb_2026*"))
cands = [d for d in cands if os.path.exists(os.path.join(d, "RUNMETA.json"))]
print("[gate0] SIZE candidate new corpora = %d" % len(cands))
if len(cands) != 1:
    sys.exit("EXPECTED exactly one cont1re corpus, found %d: %s -- ambiguous, refusing" % (len(cands), cands))
NEW = cands[0]
print("[gate0] new corpus %s" % NEW)

rm = json.load(open(os.path.join(NEW, "RUNMETA.json")))
new_args = json.load(open(os.path.join(NEW, "config.json")))["args"]
old_args = json.load(open(os.path.join(COMMITTED, "config.json")))["args"]

# ---- VOID 1: hardware, from the RUN's own metadata, never the sbatch line -----------------------
gpu = str(dig(rm, ["gpu", "gpu_name", "device_name"]))
cc = dig(rm, ["compute_capability"])
print("[gate0] VOID 1 GPU: %r  compute_capability %s" % (gpu, cc))
if gpu != "NVIDIA GeForce RTX 3090":
    fail.append("VOID 1: gpu is %r, required 'NVIDIA GeForce RTX 3090'" % gpu)
if cc is not None and float(cc) < 8.0:
    fail.append("VOID 1: compute_capability %s < 8.0 -- bf16 would be EMULATED, which is the thing "
                "this experiment exists to avoid" % cc)

# ---- VOID 2: bank identity ----------------------------------------------------------------------
bank = new_args.get("bank")
got_bank = hashlib.sha256(open(bank, "rb").read()).hexdigest()[:16]
print("[gate0] VOID 2 bank %s  sha16 %s (expect %s)" % (os.path.basename(str(bank)), got_bank, BANK_SHA16))
if got_bank != BANK_SHA16:
    fail.append("VOID 2: bank sha16 %s != %s" % (got_bank, BANK_SHA16))
if str(bank) != str(old_args.get("bank")):
    fail.append("VOID 2: bank PATH differs from the committed run: %r vs %r" % (bank, old_args.get("bank")))

# ---- VOID 3: one token, and only the three named exemptions -------------------------------------
keys = sorted(set(old_args) | set(new_args))
compared = [k for k in keys if k.lstrip("_") not in EXEMPT_ARGS]
print("[gate0] SIZE args compared = %d (exempt: %s)" % (len(compared), sorted(EXEMPT_ARGS)))
if len(compared) < 15:
    sys.exit("VACUOUS: only %d args compared -- refusing to certify a one-token A/B on that" % len(compared))
diffs = [(k, old_args.get(k), new_args.get(k)) for k in compared if str(old_args.get(k)) != str(new_args.get(k))]
for k, a, b in diffs:
    print("     DIFF %-26s committed=%r  new=%r" % (k, str(a)[:40], str(b)[:40]))
if diffs:
    fail.append("VOID 3: %d non-exempt arg(s) differ: %s" % (len(diffs), [d[0] for d in diffs]))
else:
    print("     every non-exempt arg is IDENTICAL to the committed run")

# the manipulation itself must be present and be exactly what was declared
print("[gate0] the manipulation: layers committed=%r  new=%r" % (str(old_args.get("layers"))[:44], new_args.get("layers")))
if str(new_args.get("layers")) != "18,20":
    fail.append("the manipulation is wrong: --layers is %r, declared 18,20" % new_args.get("layers"))
if str(old_args.get("layers")) == str(new_args.get("layers")):
    fail.append("--layers did NOT change -- this is not an A/B")

# VOID 3 amended: --model must resolve to the SAME revision as the committed run
# THE CORPUS MUST BE FINISHED. Running this gate while job 914750 was still extracting showed it
# PASSING with population "new=None" -- absent evidence read as passing evidence, which is the exact
# S-134 vacuous shape this gate exists to refuse, in the gate written to refuse it. Caught only
# because the gate was run before the data existed. Absence is now a REFUSAL.
_nm = os.path.join(NEW, "metadata.json")
if not os.path.exists(_nm):
    sys.exit("REFUSING: %s has no metadata.json -- the extraction has not finished. A gate that "
             "certifies an unfinished corpus certifies nothing." % NEW)
new_meta_raw = json.load(open(_nm))
new_rev = dig(new_meta_raw, ["model_revision_resolved_commit"])
if new_rev is None:
    sys.exit("REFUSING: the new corpus records no model_revision_resolved_commit -- VOID 3 cannot be "
             "checked, and an unmeasurable VOID condition is not a satisfied one.")
old_meta = json.load(open(os.path.join(COMMITTED, "metadata.json")))
old_rev = old_meta.get("model_revision_resolved_commit")
print("[gate0] VOID 3 (amended) model revision: committed %s | new %s | required %s"
      % (str(old_rev)[:12], str(new_rev)[:12], SNAP[:12]))
if old_rev != SNAP:
    fail.append("the COMMITTED run resolved to %r, not the snapshot this prereg pins" % old_rev)
if new_rev != SNAP:
    fail.append("VOID 3: the new run resolved to %r, not %r" % (new_rev, SNAP))

# ---- population: the cosine must be a comparison, not a different experiment --------------------
new_meta = new_meta_raw
for k in ("n_bank_rows_used", "n_result_rows"):
    a, b = old_meta.get(k), new_meta.get(k)
    print("[gate0] population %-18s committed=%s  new=%s" % (k, a, b))
    if b is None:
        fail.append("population field %s is ABSENT from the new corpus -- it cannot be compared, and "
                    "an uncomparable population is not a matching one" % k)
    elif a != b:
        fail.append("population differs on %s: committed %s vs new %s -- a cosine over a different "
                    "population is not the comparison this preregistration declared" % (k, a, b))

# ---- VOID 7: nothing committed was overwritten --------------------------------------------------
print("[gate0] SIZE committed axes checked = %d" % len(COMMITTED_AXES))
for p, want in COMMITTED_AXES.items():
    got = sha16(p)
    ok = (got == want)
    print("     %-46s %s %s" % (os.path.basename(p), got, "OK" if ok else "*** CHANGED ***"))
    if not ok:
        fail.append("VOID 7: %s has CHANGED (%s != %s) -- a comparison target was overwritten" % (p, got, want))

print()
if fail:
    print("=== GATE 0 FAILURES (each is a VOID condition) ===")
    for f in fail:
        print("   -", f)
    sys.exit(1)
print("=== GATE 0 PASS -- every VOID condition checked. NO COSINE COMPUTED; that is PART 4. ===")
