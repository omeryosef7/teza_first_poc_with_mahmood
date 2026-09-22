"""GATE 0 for the PR-CSI-012 CENSUS, sweepable WHILE THE 44 ARMS ARE IN FLIGHT.

The census reader refuses until all 44 arms exist -- correctly, since a census of 6 heads is not a
census. But that means a liveness or IDENTITY defect would surface only after ~4 GPU-hours. This sweep
checks every LANDED arm now, and reads NO ENDPOINT FIELD.

⚠ WHY IDENTITY IS THE POINT HERE, NOT LIVENESS. S-246 measured that a K-head arm records K x 2016
prefill edits while the ALL-32 arm records 2016, so a SINGLETON records exactly what HD_KO records. The
dose check cannot tell them apart. Arm identity is therefore asserted from each run's OWN recorded
`knockout_heads` against the preregistered head set -- and this sweep reuses the census reader's
`recorded_heads` rather than re-deriving it, so there is ONE definition of "which heads did this arm
actually knock out".

⛔ THE ENDPOINT-BLINDNESS GUARD IS EXTENDED HERE. pr010's version scans only its own source, which is
sound for a self-contained file but says nothing about code it imports and calls. This one also scans
the SOURCE OF EVERY IMPORTED CALLABLE IT USES. A guard that stops at the module boundary is a guard
with a hole exactly where the borrowed code is.
"""
import argparse, inspect, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "scripts"))

ENDPOINT_FIELDS = ("semantic_logodds", "logp_concept", "logp_codeword", "y_install",
                   "semantic_prob", "installation")

import importlib.util


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


census = _load("census", os.path.join(REPO, "scripts", "dcs_csi_head_census.py"))
recorded_heads = census.recorded_heads
liveness = census.w4.liveness
strict_run_dir = census.rederive.strict_run_dir


def _scan(src, label, bad):
    for i, line in enumerate(src.splitlines(), 1):
        s = line.lstrip()
        if s.startswith(("#", '"', "'")) or "ENDPOINT_FIELDS" in line:
            continue
        for f in ENDPOINT_FIELDS:
            if ('get("%s")' % f) in line or ('["%s"]' % f) in line:
                bad.append("%s:%d: %s" % (label, i, s))


def assert_reads_no_endpoint():
    """Self-source AND the source of every imported callable this sweep actually calls."""
    bad = []
    _scan(open(os.path.abspath(__file__), encoding="utf-8").read(), "self", bad)
    for fn in (recorded_heads, liveness, strict_run_dir):
        try:
            _scan(inspect.getsource(fn), "%s.%s" % (fn.__module__, fn.__name__), bad)
        except (OSError, TypeError):
            bad.append("%r: SOURCE UNAVAILABLE -- cannot prove it reads no endpoint" % (fn,))
    if bad:
        raise SystemExit("REFUSING: this sweep (or code it calls) accesses an ENDPOINT field, so "
                         "running it during a live family would be a peek at the answer:\n  "
                         + "\n  ".join(bad))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--tag-prefix", required=True)
    ap.add_argument("--split", required=True, choices=["train", "validation"])
    ap.add_argument("--expect-n", type=int, default=230)
    ap.add_argument("--require-slurm-job", default=None)
    a = ap.parse_args()

    assert_reads_no_endpoint()
    pr = json.load(open(a.prereg))
    if not pr.get("NO_RANK_TEST"):
        sys.exit("REFUSING: prereg %r is not a CENSUS -- use scripts/gates/dcs_csi_pr010_gate0_sweep.py"
                 % pr.get("id"))
    hs = pr["head_sets"]
    arms = ["HD_BASE", "HD_KO"] + sorted(hs)
    jobs = a.require_slurm_job.split(",") if a.require_slurm_job else None
    DOSE = census.DOSE_UNIT

    print("%s GATE 0 SWEEP -- %s | %d arms declared" % (pr["id"], a.split, len(arms)))
    print("%-12s %6s %14s %12s %7s %5s  %-26s %s"
          % ("arm", "rows", "median_pre", "want", "decode", "viol", "identity", "verdict"))
    landed = fails = 0
    for arm in arms:
        try:
            d = strict_run_dir("%s_%s" % (a.tag_prefix, arm), a.expect_n,
                               row_file="results.jsonl", require_slurm_jobs=jobs)
        except SystemExit:
            print("%-12s -- not landed --" % arm); continue
        except Exception:
            print("%-12s -- not landed --" % arm); continue
        landed += 1
        L = liveness(d)
        k = 0 if arm == "HD_BASE" else (32 if arm == "HD_KO" else len(hs[arm]))
        want = 0 if arm == "HD_BASE" else (DOSE if arm == "HD_KO" else DOSE * k)
        got = None if arm == "HD_BASE" else recorded_heads(d)
        if arm == "HD_BASE":
            ok_id, why = True, "not intervened"
        elif arm == "HD_KO":
            ok_id = (got == "ALL"); why = "ALL 32" if ok_id else "expected ALL, got %r" % (got,)
        elif got is None:
            ok_id, why = False, "NO knockout_heads recorded -- CANNOT VERIFY"
        elif got == "ALL":
            ok_id, why = False, "records ALL 32, prereg says %s -- S-246 COLLISION" % (hs[arm],)
        else:
            ok_id = (list(got) == list(hs[arm]))
            why = "matches prereg" if ok_id else "got %s != %s" % (got, hs[arm])
        ok = (L["violations"] == {} and L["total_decode_edits"] == 0
              and L["median_prefill_edits"] == want and ok_id)
        fails += (not ok)
        diag = "" if want != DOSE else "  <- dose NOT identity-diagnostic (S-246)"
        print("%-12s %6d %14s %12d %7d %5d  %-26s %s%s"
              % (arm, L["n_rows"], L["median_prefill_edits"], want, L["total_decode_edits"],
                 len(L["violations"]), why[:26], "PASS" if ok else "FAIL", diag if ok else ""))
    print()
    if fails:
        sys.exit("GATE 0: %d of %d landed arm(s) FAILED." % (fails, landed))
    print("GATE 0: every landed arm passes (%d of %d). Identity verified from each arm's own "
          "knockout_heads. No endpoint field was read." % (landed, len(arms)))


if __name__ == "__main__":
    main()
