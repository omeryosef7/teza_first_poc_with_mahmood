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
recorded_cells = census.recorded_cells
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
    for fn in (recorded_heads, recorded_cells, liveness, strict_run_dir):
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
    # ⛔ S-260. FAMILY-AGNOSTIC, and the previous shape was worse than a gap.
    # This sweep used to refuse any prereg without NO_RANK_TEST and point the reader at
    # dcs_csi_pr010_gate0_sweep.py -- which dies on `KeyError: 'K'` for PR-CSI-013, whose prereg has
    # no K. The two sweeps therefore formed a LOOP that led nowhere, and the refusal message was
    # ACTIVELY MISLEADING: it named a tool that crashes. Writing a THIRD sweep would be the
    # fork-the-generator antipattern S-251 warned about, so this one is generalised instead: arms come
    # from `base_arms` (default PR-CSI-010's names, verified to bind) plus every head_sets entry.
    # `control_pool` is skipped explicitly -- it is a DRAW POOL, not an arm (pr010_freeze.py:128).
    # ⛔ CELL FAMILIES (PR-CSI-014, S-292). A prereg carrying `cell_sets` names (layer, head) CELLS
    # rather than band-wide heads. The two are mutually exclusive: an arm set is one or the other, and
    # a prereg with both would be two families in one file (S-227 at the family level).
    #
    # ⚠ THE COLLISION THAT MAKES THIS DELICATE. A cell arm passes --knockout-cells and NOT
    # --knockout-heads, so its recorded `knockout_heads` is the EMPTY STRING -- which
    # `recorded_heads()` correctly reads as "ALL", because for a head family an omitted flag IS the
    # all-32 arm. So on a cell family the head-level identity check would report every 1-cell arm as
    # the all-32 knockout. This is S-246's dose collision reappearing on the LAYER axis, and the
    # remedy is the same: identity comes from the field that actually names the intervention. On a
    # cell family that is `knockout_cells`, and `recorded_heads` is not consulted at all.
    cs = pr.get("cell_sets")
    hs = pr.get("head_sets")
    if cs and hs:
        sys.exit("REFUSING: the prereg carries BOTH head_sets and cell_sets. An arm family is one "
                 "or the other; a file with both declares two families and no reader can know "
                 "which arms it is being asked to verify.")
    if not cs and not hs:
        sys.exit("REFUSING: the prereg carries neither head_sets nor cell_sets.")
    IS_CELLS = bool(cs)
    if IS_CELLS:
        hs = {k: [tuple(int(x) for x in c) for c in v] for k, v in cs.items()}
        PER_CELL, NLAYERS = census.per_cell_dose(pr)
    base = list(pr.get("base_arms", ["HD_BASE", "HD_KO"]))
    if len(base) != 2:
        sys.exit("REFUSING: base_arms must name exactly 2 arms, got %r" % (base,))
    for b in base:
        if b in hs:
            sys.exit("REFUSING: base arm %r also appears in head_sets -- it carries no head list" % b)
    arms = base + [k for k in sorted(hs) if k != "control_pool"]
    if "n_arms_per_split" in pr and len(arms) != pr["n_arms_per_split"]:
        sys.exit("REFUSING: enumerated %d arms but the prereg declares n_arms_per_split=%d"
                 % (len(arms), pr["n_arms_per_split"]))
    jobs = a.require_slurm_job.split(",") if a.require_slurm_job else None
    DOSE = census.DOSE_UNIT
    # R26. The expected dose per arm, precomputed so "is the dose identity-diagnostic" can be DERIVED
    # from whether any OTHER arm expects the same number, instead of hardcoding the single collision at
    # DOSE_UNIT. The old rule was wrong on 10 of D34's 44 arms (all eight LOO_*, and HD_TOPK/HD_BOTK
    # which BOTH expect 16128) and wrong on every cell arm (all expect 224).
    import collections as _c
    _dose_of = {}
    for _arm in arms:
        _k = 0 if _arm == base[0] else (32 if _arm == base[1] else len(hs[_arm]))
        if IS_CELLS and _arm not in base:
            _dose_of[_arm] = PER_CELL * _k
        else:
            _dose_of[_arm] = 0 if _arm == base[0] else (DOSE if _arm == base[1] else DOSE * _k)
    _shared = _c.Counter(_dose_of.values())

    print("%s GATE 0 SWEEP -- %s | %d arms declared%s"
          % (pr["id"], a.split, len(arms),
             ("  | CELL family: per-cell dose %d = %d/%d layers  \u26a0 PREDICTED, NOT MEASURED"
              % (PER_CELL, DOSE, NLAYERS)) if IS_CELLS else ""))
    if IS_CELLS:
        # The head-level 2016 was MEASURED (S-215/S-246). The per-cell figure divides it by the band
        # width and so assumes the edits are UNIFORM across layers -- untestable from any artefact on
        # disk, because the hook counters are summed across layers before being written. Saying so on
        # every run is the difference between a gate that verifies an identity and one that enforces
        # an assumption; the first cell arm ever run VALIDATES this arithmetic.
        print("  \u26a0 the per-cell dose is a PREDICTION from DOSE_UNIT/%d under an untested "
              "uniformity assumption." % NLAYERS)
        print("    A cell arm's dose check is therefore UNVERIFIED, not confirmatory, until one "
              "cell arm has landed and matched it.")
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
        k = 0 if arm == base[0] else (32 if arm == base[1] else len(hs[arm]))
        # The two BASE arms are head-level on every family: base[0] is the clean reference and
        # base[1] is the all-32 band knockout that serves as the denominator. Only the non-base arms
        # of a cell family are cell-scoped.
        if arm in base or not IS_CELLS:
            want = 0 if arm == base[0] else (DOSE if arm == base[1] else DOSE * k)
        else:
            want = PER_CELL * k
        if arm == base[0]:
            ok_id, why = True, "not intervened"
        elif arm == base[1]:
            got = recorded_heads(d)
            ok_id = (got == "ALL"); why = "ALL 32" if ok_id else "expected ALL, got %r" % (got,)
        elif IS_CELLS:
            # IDENTITY FROM `knockout_cells` ONLY. See the collision note above: this arm's
            # `knockout_heads` is empty and would read as "ALL".
            got = recorded_cells(d)
            if got is None:
                ok_id, why = False, "NO knockout_cells recorded -- CANNOT VERIFY"
            elif got == "NOT_A_CELL_ARM":
                ok_id, why = False, "knockout_cells EMPTY -- this arm is not cell-scoped"
            else:
                ok_id = (list(got) == sorted(hs[arm]))
                why = ("matches prereg" if ok_id
                       else "got %s != %s" % (got, sorted(hs[arm])))
        else:
            got = recorded_heads(d)
            if got is None:
                ok_id, why = False, "NO knockout_heads recorded -- CANNOT VERIFY"
            elif got == "ALL":
                ok_id, why = False, "records ALL 32, prereg says %s -- S-246 COLLISION" % (hs[arm],)
            else:
                ok_id = (list(got) == list(hs[arm]))
                why = "matches prereg" if ok_id else "got %s != %s" % (got, hs[arm])
        ok = (L["violations"] == {} and L["total_decode_edits"] == 0
              and L["median_prefill_edits"] == want and ok_id)
        fails += (not ok)
        diag = ("" if _shared[want] == 1
                else "  <- dose NOT identity-diagnostic: %d arms expect %s (S-246/R26)"
                     % (_shared[want], want))
        print("%-12s %6d %14s %12d %7d %5d  %-26s %s%s"
              % (arm, L["n_rows"], L["median_prefill_edits"], want, L["total_decode_edits"],
                 len(L["violations"]), why[:26], "PASS" if ok else "FAIL", diag if ok else ""))
    print()
    if fails:
        sys.exit("GATE 0: %d of %d landed arm(s) FAILED." % (fails, landed))
    # ⛔ ZERO LANDED ARMS IS NOT A PASS (S-292). This printed "GATE 0: every landed arm passes
    # (0 of 23)" and exited 0 whenever NOTHING matched -- a typo in --tag-prefix, the wrong split, a
    # --require-slurm-job naming a job that produced nothing. That is exactly the rule this file's own
    # docstring invokes against the dose check (R20-6: any check whose PASS is consistent with reading
    # NOTHING is not a check), and the sweep was run repeatedly as a progress check through PR-013's
    # night, where a mistyped prefix would have reported a pass over an empty set.
    #
    # It exits 3 rather than raising a generic failure because ZERO-LANDED is a legitimate state early
    # in a live family -- the sweep is designed to run while arms are in flight -- so it must be
    # distinguishable by a caller from a real GATE 0 failure (which exits 1 above).
    if landed == 0:
        print("GATE 0: NOTHING TO CHECK -- 0 of %d declared arms resolved. THIS IS NOT A PASS."
              % len(arms))
        print("  Either no arm has landed yet, or --tag-prefix/--split/--require-slurm-job name "
              "something that does not exist.")
        sys.exit(3)
    print("GATE 0: every landed arm passes (%d of %d). Identity verified from each arm's own "
          "%s. No endpoint field was read."
          % (landed, len(arms), "knockout_cells" if IS_CELLS else "knockout_heads"))


if __name__ == "__main__":
    main()
