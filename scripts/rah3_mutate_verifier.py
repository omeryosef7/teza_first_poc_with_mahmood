"""Mutation-test verifier A across DISTINCT assertion classes.
RAH2-C-023: perturbing the one value with the most headroom proves only that the harness runs."""
import json, subprocess, sys, glob, os, copy
SRC = sorted(glob.glob("outputs/boombness/rah_preflight/rah3smoke_p_cb_*.json"))[0]
base = json.load(open(SRC))
TMP = "/tmp/claude-47249/-home-sharifm-students-omeryosef-first-poc-teza-first-poc-with-mahmood/c4574da8-ea23-4dbe-94e1-61b2080f9c68/scratchpad/mut.json"

def _atomic_json_dump(obj, path, **kw):
    """Atomic, VERIFIED JSON write. Fix for sprint entry S-124.

    Replaces `json.dump(x, open(p, "w"), ...)`, whose handle is never closed: `open` truncates the
    destination immediately and the buffered bytes are flushed only in the GC finaliser, where
    CPython PRINTS and then SWALLOWS an EDQUOT. A full quota therefore produced a 0-byte file at a
    real artifact name, with "wrote <path>" on stdout and exit status 0 -- indistinguishable from a
    finished report. Temp file + fsync + size check + re-parse + os.replace makes the write ATOMIC
    as well as checked: a half-written file never appears at the real name, and whatever was there
    before survives a failure. On any error this RAISES, naming the path and the byte count.
    """
    import tempfile                        # local: keeps this helper drop-in and import-order-free
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_atomic_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, **kw)
            fh.flush()
            os.fsync(fh.fileno())          # EDQUOT surfaces HERE, not in a GC finaliser
        n = os.path.getsize(tmp)
        if n == 0:
            raise OSError("temp file is 0 bytes after a flush+fsync that reported success")
        with open(tmp, "r", encoding="utf-8") as fh:
            json.load(fh)                  # a truncated write does not re-parse
        try:
            mode = os.stat(path).st_mode & 0o7777   # keep the artifact's existing permissions:
        except OSError:                             # mkstemp makes the temp file 0600 and
            mode = 0o644                            # os.replace would carry that onto the report
        os.chmod(tmp, mode)
        os.replace(tmp, path)              # atomic within the directory
    except Exception as e:
        try:
            n = os.path.getsize(tmp)
        except OSError:
            n = -1
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise OSError("atomic_json_dump FAILED for %s -- %d bytes reached the temp file; the "
                      "destination is UNCHANGED (never truncated). Cause: %r" % (path, n, e)) from e
    return os.path.getsize(path)


def mutate(name, fn):
    d = copy.deepcopy(base); fn(d)
    _atomic_json_dump(d, TMP)
    r = subprocess.run([sys.executable, "scripts/rah3_verify_noncopy_independent.py", TMP],
                       capture_output=True, text=True, env=dict(os.environ, HF_HUB_OFFLINE="1"))
    red = r.returncode != 0
    nf = [l for l in r.stdout.splitlines() if l.startswith("  FAIL:")]
    print("%-46s -> %s (%d failed checks)" % (name, "RED  ✓" if red else "GREEN ✗ VACUOUS", len(nf)))
    if nf: print("      e.g. %s" % nf[0][:130])
    return red

M = []
M.append(mutate("capture piece changed on ONE donor",
                lambda d: d["donors"][0].__setitem__("donor_piece", " given")))
M.append(mutate("capture index shifted by 1",
                lambda d: d["donors"][1].__setitem__("donor_tok_idx", d["donors"][1]["donor_tok_idx"]+1)))
M.append(mutate("capture_mode flipped back to surface",
                lambda d: d.__setitem__("capture_mode", "surface")))
M.append(mutate("capture_offset changed to +2",
                lambda d: d.__setitem__("capture_offset", 2)))
M.append(mutate("a label id corrupted",
                lambda d: d["label_ids"].__setitem__(d["concept"], 999)))
M.append(mutate("hops falsified to 0 on an eligible cell",
                lambda d: [c.__setitem__("hops", 0) for c in d["grid"] if c["form"]=="fewshot_cat"][0]))
M.append(mutate("rah3_eligible flipped True on fc_probe_last",
                lambda d: [c.__setitem__("rah3_eligible", True) for c in d["grid"] if c["form"]=="fc_probe_last"][0]))
M.append(mutate("mass_gate_ok flipped True below the gate",
                lambda d: [c.__setitem__("mass_gate_ok", True) for c in d["grid"] if not c["mass_gate_ok"]][0]))
M.append(mutate("pos_ctrl_max inflated by 1 PERCENT (relative tol)",
                lambda d: d["grid"][0].__setitem__("pos_ctrl_max", d["grid"][0]["pos_ctrl_max"]*1.01)))
M.append(mutate("pos_ctrl_max inflated by 0.0001 PERCENT",
                lambda d: d["grid"][0].__setitem__("pos_ctrl_max", d["grid"][0]["pos_ctrl_max"]*1.000001)))
M.append(mutate("best_donor_L moved off the argmax",
                lambda d: d["grid"][0].__setitem__("best_donor_L", d["grid"][0]["best_donor_L"]+1)))
M.append(mutate("positive_control_ok flipped True on a failing cell",
                lambda d: [c.__setitem__("positive_control_ok", True) for c in d["grid"] if not c["positive_control_ok"]][0]))
M.append(mutate("patch liveness falsified (vacuous cell hidden)",
                lambda d: d["grid"][0].__setitem__("n_patch_changed_at_best", 0)))
M.append(mutate("bank_sha256 corrupted",
                lambda d: d["provenance"].__setitem__("bank_sha256", "0"*64)))
M.append(mutate("a provenance field deleted",
                lambda d: d["provenance"].pop("branch")))
M.append(mutate("expected_n_donors != actual",
                lambda d: d["provenance"].__setitem__("expected_n_donors", 99)))
M.append(mutate("uplift arithmetic broken",
                lambda d: d["grid"][0].__setitem__("uplift_over_unpatched", d["grid"][0]["uplift_over_unpatched"]*1.5)))
print("\n%d/%d mutations went RED" % (sum(M), len(M)))
sys.exit(0 if all(M) else 1)
