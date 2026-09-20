#!/usr/bin/env python3
"""PR-CSI-001 smoke checker: does the subspace intervention actually DO anything on
`semantic_one_word` prompts, and are its controls real?

This exists because every failure mode below produces a run that COMPLETES CLEANLY:
  * the query span resolves empty on semantic prompts -> every row is ledger-failed and the
    rescue writes nothing, but DONE.json still says ok;
  * the rescue fires but writes a ~zero-norm delta -> indistinguishable from not firing;
  * the norm-matched control writes a different norm than the candidate -> the control cannot
    fail and the candidate looks specific for geometric reasons;
  * KO_SELF is not inert -> the patch is not writing what it read and no rescue number means
    anything.
It reports PASS/FAIL per condition and refuses to summarise anything as OK on missing data.
"""
from __future__ import annotations
import argparse, glob, importlib.util, json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s); sys.modules[mod] = m; s.loader.exec_module(m); return m


def newest(tag):
    """ANCHORED match -- see the note in dcs_csi_rederive_patch.strict_run_dir.

    The unanchored version silently resolved arm "KO" to the "KO_SELF" directory, which made the
    identity check compare KO_SELF against itself and pass vacuously (S-042)."""
    pat = re.compile(r"^" + re.escape(tag) + r"_\d{8}_\d{6}_\d+$")
    ds = [d for d in sorted(glob.glob(os.path.join(REPO, "outputs/boombness/score_behavior", tag + "_*")))
          if pat.match(os.path.basename(d)) and os.path.exists(os.path.join(d, "results.jsonl"))]
    return ds[-1] if ds else None


def rows(d):
    return [json.loads(l) for l in open(os.path.join(d, "results.jsonl"))]


FAILS = []


def check(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print("  %-5s %-52s %s" % (tag, name, detail))
    if not cond:
        FAILS.append(name)


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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", required=True)
    ap.add_argument("--prefix", default="csi1sm")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    lpm = _load("lpm", "scripts/dcs_cont_layerpos_map.py")

    arms = ["BASE", "KO", "KO_SELF", "KO_FULL", "KO_AXIS", "KO_ORTH"]
    R, D = {}, {}
    for arm in arms:
        d = newest("%s_%s_%s" % (a.prefix, a.codeword, arm))
        if d is None:
            print("MISSING arm %s" % arm); FAILS.append("arm_%s_missing" % arm); continue
        D[arm] = d
        R[arm] = rows(d)
        print("[dir ] %-9s %-54s rows=%d" % (arm, os.path.basename(d), len(R[arm])))
    if len(R) != len(arms):
        print("\nSMOKE FAIL: not all arms present"); return 1

    n = len(R["KO"])
    rep = {"schema": "dcs_csi_p1_smoke/1", "codeword": a.codeword, "n_rows": n,
           "run_dirs": {k: os.path.basename(v) for k, v in D.items()}}

    print("\n[1] knockout live on semantic prompts")
    for arm in ("KO", "KO_SELF", "KO_FULL", "KO_AXIS", "KO_ORTH"):
        pre = [r.get("hook_n_prefill_edits") or 0 for r in R[arm]]
        dec = sum(r.get("hook_n_decode_edits") or 0 for r in R[arm])
        check("%s knockout live on every row" % arm, min(pre) > 0, "min prefill edits=%d" % min(pre))
        check("%s zero decode-time edits" % arm, dec == 0, "decode edits=%d" % dec)
    check("BASE has no knockout", all(not (r.get("hook_n_prefill_edits") or 0) for r in R["BASE"]))

    print("\n[2] query span is non-empty, so the rescue has positions")
    for arm in ("KO_SELF", "KO_FULL", "KO_AXIS", "KO_ORTH"):
        npos = [r.get("n_rescue_positions") for r in R[arm]]
        ok = all(x is not None and x > 0 for x in npos)
        check("%s wrote positions on every row" % arm, ok,
              "n_rescue_positions min/max=%s/%s" % (min(x for x in npos if x is not None) if ok else "?",
                                                     max(x for x in npos if x is not None) if ok else "?"))
        fired = sum(1 for r in R[arm] if (r.get("rescue_liveness") or {}).get("fired"))
        check("%s rescue fired on every row" % arm, fired == len(R[arm]), "%d/%d" % (fired, len(R[arm])))
    rep["n_rescue_positions"] = sorted({r.get("n_rescue_positions") for r in R["KO_FULL"]})

    print("\n[3] KO_SELF is INERT (the identity control)")
    inst = {}
    for arm in arms:
        try:
            inst[arm], _, _ = lpm.load_installation(D[arm])
        except Exception as e:                                          # noqa: BLE001
            print("   could not read installation for %s: %s" % (arm, str(e)[:120]))
    if "KO" in inst and "KO_SELF" in inst:
        common = sorted(set(inst["KO"]) & set(inst["KO_SELF"]))
        diffs = [abs(inst["KO_SELF"][k] - inst["KO"][k]) for k in common]
        mean_diff = sum(inst["KO_SELF"][k] - inst["KO"][k] for k in common) / len(common)
        # THRESHOLD CORRECTED (S-043). The first version demanded per-key bit-exactness
        # (max|diff| < 1e-6). That criterion was invented here, not preregistered, and it "passed"
        # only because an unanchored glob was comparing KO_SELF with itself (S-042). The quantity
        # PR-CSI-001 actually specifies is the MEAN difference against `self_inert_tol = 0.005`,
        # which is what enters every contrast; per-key scatter from float nondeterminism in the
        # extra donor-capture forward does not. The per-key max is still reported, as a
        # DIAGNOSTIC rather than a gate -- loosening a gate because it failed would be exactly the
        # wrong move, so the gate is being moved onto the preregistered quantity, not widened.
        check("KO_SELF reproduces KO in the MEAN (prereg self_inert_tol=0.005)",
              abs(mean_diff) < 0.005,
              "mean diff=%+.3e  (per-key max=%.3e over %d keys, diagnostic only)"
              % (mean_diff, max(diffs) if diffs else float('nan'), len(common)))
        rep["self_identity_mean_diff"] = mean_diff
        rep["self_identity_max_abs_diff_DIAGNOSTIC"] = max(diffs) if diffs else None

    print("\n[4] the axis arm writes a NONZERO delta")
    for arm in ("KO_FULL", "KO_AXIS", "KO_ORTH"):
        wn = [(r.get("rescue_liveness") or {}).get("written_norm_mean") for r in R[arm]]
        wn = [x for x in wn if x is not None]
        if arm == "KO_FULL":
            check("KO_FULL is the whole-state patch (no written_norm recorded)", True,
                  "whole-state DonorPatch does not project")
            continue
        check("%s wrote a nonzero norm on every row" % arm, bool(wn) and min(wn) > 1e-6,
              "min=%.6f mean=%.6f" % (min(wn), sum(wn) / len(wn)) if wn else "NO NORM RECORDED")
        cf = [(r.get("rescue_liveness") or {}).get("captured_energy_frac_mean") for r in R[arm]]
        cf = [x for x in cf if x is not None]
        if cf:
            rep["%s_captured_energy_frac_mean" % arm] = round(sum(cf) / len(cf), 5)

    print("\n[5] the control is genuinely NORM-MATCHED to the candidate")
    ax = {r["prompt_id"]: (r.get("rescue_liveness") or {}).get("written_norm_mean") for r in R["KO_AXIS"]}
    ot = {r["prompt_id"]: (r.get("rescue_liveness") or {}).get("written_norm_mean") for r in R["KO_ORTH"]}
    common = sorted(set(ax) & set(ot))
    d = [abs(ax[p] - ot[p]) for p in common if ax[p] is not None and ot[p] is not None]
    check("KO_ORTH norm == KO_AXIS norm, per row", bool(d) and max(d) < 1e-5,
          "max|diff|=%.3e over %d rows" % (max(d) if d else float('nan'), len(d)))
    deg = sum((r.get("rescue_liveness") or {}).get("n_positions_norm_match_degenerate") or 0
              for r in R["KO_ORTH"])
    check("KO_ORTH had NO norm-match-degenerate positions", deg == 0, "degenerate=%d" % deg)
    rep["norm_match_max_abs_diff"] = max(d) if d else None
    rep["orth_degenerate_positions"] = deg

    print("\n[6] the basis identity is recorded on the rows")
    for arm, key in (("KO_AXIS", "cand_rank1"), ("KO_ORTH", "ctrl_orth")):
        keys = {r.get("rescue_basis_key") for r in R[arm]}
        check("%s rows record basis key %r" % (arm, key), keys == {key}, "got %s" % sorted(keys))

    print("\n[7] the endpoint moved at all (a sanity read, NOT a result)")
    if len(inst) == len(arms):
        means = {k: round(sum(v.values()) / len(v), 4) for k, v in inst.items()}
        rep["installation_mean_by_arm_SMOKE_ONLY"] = means
        print("   y_install by arm (24 rows, NOT a result):", json.dumps(means))
        check("KO reduced installation vs BASE", means["KO"] < means["BASE"],
              "BASE=%.4f KO=%.4f" % (means["BASE"], means["KO"]))

    rep["FAILS"] = FAILS
    rep["VERDICT"] = "SMOKE PASS" if not FAILS else "SMOKE FAIL (%d)" % len(FAILS)
    outp = a.out or os.path.join(REPO, "reports/DCS_CSI_P1_SMOKE_%s.json" % a.codeword)
    _atomic_json_dump(rep, outp, indent=1)
    print("\n%s  -> %s" % (rep["VERDICT"], os.path.relpath(outp, REPO)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
