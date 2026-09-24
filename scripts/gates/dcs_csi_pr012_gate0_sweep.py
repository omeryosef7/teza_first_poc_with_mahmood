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
import argparse, glob, inspect, json, os, re, sys

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

    # ⛔⛔ S-305. THE STATUS COMES FROM THE PREREG, NOT FROM A HARDCODED STRING.
    # This printed "⚠ PREDICTED, NOT MEASURED ... UNVERIFIED" unconditionally. That was true when S-292
    # wrote it and became FALSE the moment PR-CSI-014 measured 224.0 on nine cells across nine layers
    # (S-299) -- so on PR-CSI-015, whose prereg declares STATUS "MEASURED", the sweep asserted the
    # OPPOSITE OF THE PREREG on every single run.
    # ⚠ S-301 fixed exactly this hardcode IN THE CENSUS READER and not here. That is the third time in
    # this sprint a lesson was applied at ONE site (S-295: W4's guard; S-296: one late lookup of
    # several; now this) -- the pattern is fixing the instance that was in front of me instead of
    # grepping for the class. The grep is `PREDICTED, NOT MEASURED`, and it is now empty.
    _dose_status = (pr.get("DOSE_EXPECTATION") or {}).get(
        "STATUS", "STATUS NOT DECLARED BY THE PREREG -- treat the dose as UNVERIFIED")
    print("%s GATE 0 SWEEP -- %s | %d arms declared%s"
          % (pr["id"], a.split, len(arms),
             ("  | CELL family: per-cell dose %d = %d/%d layers  -- %s"
              % (PER_CELL, DOSE, NLAYERS, _dose_status)) if IS_CELLS else ""))
    if IS_CELLS:
        # The head-level 2016 was MEASURED (S-215/S-246). The per-cell figure divides it by the band
        # width, which assumed the edits are UNIFORM across layers; PR-CSI-014 then measured it. Which
        # of those a given family is in is the PREREG's statement, printed above, not this file's.
        # ⚠ FAIL CLOSED. My first version branched on "PREDICTED" in the status, so an UNDECLARED
        # status -- whose default text contains neither word -- fell through to the identity branch and
        # announced an unverified dose AS AN IDENTITY. The test written to assert this test's own intent
        # caught it immediately. The identity branch now requires the prereg to say MEASURED explicitly;
        # everything else, absence included, is UNVERIFIED (R20-6: absence is not a pass).
        # ⚠ R27/S-308 -- S-305's fix FAILED OPEN ON THE NEGATION OF ITS OWN KEYWORD. A substring
        # test for "MEASURED" is True for "NOT MEASURED", "NOT YET MEASURED" and "UNMEASURED", all
        # of which then printed the IDENTITY branch for a dose the prereg says was never measured.
        # Demonstrated by R27 on the real 29 arms. The status is now required to BEGIN with the
        # word, and every negative form is refused explicitly. Absence is still UNVERIFIED (R20-6).
        _ds = str(_dose_status).strip().upper()
        _dose_confirmed = (_ds.startswith("MEASURED")
                           and not any(w in _ds for w in ("NOT MEASURED", "NOT YET MEASURED",
                                                          "UNMEASURED", "PREDICTED")))
        if not _dose_confirmed:
            print("  \u26a0 the per-cell dose is a PREDICTION from DOSE_UNIT/%d under an untested "
                  "uniformity assumption." % NLAYERS)
            print("    A cell arm's dose check is therefore UNVERIFIED, not confirmatory, until one "
                  "cell arm has landed and matched it.")
        else:
            print("  the per-cell dose %d = DOSE_UNIT/%d is an IDENTITY for this family per its prereg, "
                  "so a deviation is a CODE defect" % (PER_CELL, NLAYERS))
            print("    and a VOID condition -- not a surprising fact about the model (S-299).")
    print("%-12s %6s %14s %12s %7s %5s  %-26s %s"
          % ("arm", "rows", "median_pre", "want", "decode", "viol", "identity", "verdict"))
    landed = fails = refused = incomplete = 0
    for arm in arms:
        # ⚠ R27/S-308. This block used to swallow EVERY refusal from strict_run_dir into
        # "-- not landed --", incrementing neither `landed` nor `fails`. R27 demonstrated it on the
        # real arms: corrupting CL_H19_L14's DONE.json ledger -- one of the THREE cells that cleared
        # the bar -- printed "-- not landed --" and then "every landed arm passes (28 of 29)",
        # exit 0. A second complete run dir from the void job 918967 did the same, which is exactly
        # the S-103/S-104 relaunch shape the frozen read warns about. An arm that HAS directories
        # and was refused is a FAILURE; only an arm with NO directory at all is "not landed".
        _tag = "%s_%s" % (a.tag_prefix, arm)
        _cands = [x for x in glob.glob(os.path.join(census.rederive.SCORE_DIR, _tag + "_*"))
                  if re.match(r"^" + re.escape(_tag) + r"_\d{8}_\d{6}_\d+$", os.path.basename(x))]
        try:
            d = strict_run_dir(_tag, a.expect_n,
                               row_file="results.jsonl", require_slurm_jobs=jobs)
        except (SystemExit, Exception) as e:
            if not _cands:
                print("%-12s -- not landed --" % arm); continue
            # ⚠ S-315 -- MY OWN R27/S-308 FIX MISFIRED ON A LIVE FAMILY, and it misfired the FIRST
            # time it met one. That fix said "an arm that HAS directories and was refused is a
            # FAILURE", which is right for a ledger mismatch, a bad DONE.status or two complete dirs
            # -- and WRONG for an arm that is being written RIGHT NOW. An in-flight arm also has a
            # directory that exists and is refused, because its DONE.json does not exist yet. The
            # frozen read says GATE 0 "may be swept incrementally at any time", so under S-308 every
            # mid-family sweep would report a spurious FAIL and exit 1 -- which is worse than the
            # defect it replaced, because a sweep that always cries wolf is a sweep whose real
            # failures get waved through.
            # The discriminator is a FILESYSTEM FACT, not a parse of the refusal text: an arm none of
            # whose candidate directories carries a DONE.json has not finished writing. (A DIED arm
            # looks the same at this instant and is reported the same way -- INCOMPLETE, not passed
            # and not failed. Only the final sweep, when the job is gone, can tell them apart, and
            # the arm-count guard is what catches a family that never completed.)
            _done = [x for x in _cands if os.path.exists(os.path.join(x, "DONE.json"))]
            if not _done:
                incomplete += 1
                print("%-12s  .. IN FLIGHT -- %d run dir(s), no DONE.json yet (neither passed nor "
                      "failed)" % (arm, len(_cands)))
                continue
            fails += 1
            refused += 1
            print("%-12s  \u26a0 GATE 0 FAIL -- %d run dir(s) EXIST and %d carry a DONE.json, but "
                  "were REFUSED: %s" % (arm, len(_cands), len(_done), str(e)[:150]))
            continue
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
            # ⚠ R27/S-310: the same collision, on the DENOMINATOR. A full-band 9-cell arm records an
            # EMPTY knockout_heads (-> "ALL") and the identical dose 9 x 224 = 2016, so this check
            # alone certifies a one-head-wide arm as the all-32 knockout. A true all-32 arm carries
            # NO cell list; absence of the field is not a pass (R20-6). PR-CSI-016 is the first
            # family that will actually contain such an arm.
            got = recorded_heads(d)
            _kc = recorded_cells(d)
            ok_id = (got == "ALL") and (_kc == "NOT_A_CELL_ARM")
            why = ("ALL 32, no cell list" if ok_id
                   else "expected ALL, got %r" % (got,) if got != "ALL"
                   else "NO knockout_cells field -- cannot rule out a 9-cell arm sharing this dose"
                   if _kc is None
                   else "CELL-SCOPED DENOMINATOR: knockout_cells records %r (S-246 collision)" % (_kc,))
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
        sys.exit("GATE 0: %d FAILURE(S) over %d arm(s) that resolved to a run directory "
                 "(%d passed GATE 0; %d had directories that were REFUSED by strict_run_dir and "
                 "are counted as failures rather than as 'not landed' -- R27/S-308)."
                 % (fails, landed + refused, landed - (fails - refused), refused))
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
        print("GATE 0: NOTHING TO CHECK -- 0 of %d declared arms resolved%s. THIS IS NOT A PASS."
              % (len(arms),
                 "" if not refused else " (and %d had run directories that were REFUSED)" % refused))
        print("  Either no arm has landed yet, or --tag-prefix/--split/--require-slurm-job name "
              "something that does not exist.")
        sys.exit(3)
    print("GATE 0: every landed arm passes (%d of %d). Identity verified from each arm's own "
          "%s. No endpoint field was read."
          % (landed, len(arms), "knockout_cells" if IS_CELLS else "knockout_heads"))
    if incomplete:
        # S-315: a partial sweep must never read as a finished one. The count above already
        # discloses landed-vs-declared; this names WHY the rest are missing.
        print("  .. %d arm(s) IN FLIGHT (run dir present, no DONE.json). THIS SWEEP IS PARTIAL and "
              "is NOT the family's GATE 0 verdict." % incomplete)
    # ⛔ R30-D/S-332. A PARTIAL SWEEP EXITED 0 -- THE SAME CODE AS A COMPLETE PASS.
    # S-292 established that a sweep resolving NOTHING is not a pass and made it exit 3. The same
    # argument applies one step along and was never carried there: "61 of 62, one IN FLIGHT" also
    # exited 0, with text a reader skims as healthy progress. The comment at the in-flight branch
    # says "only the final sweep, when the job is gone, can tell [a DIED arm] apart, and the
    # ARM-COUNT GUARD is what catches a family that never completed" -- and R30-D established that
    # NO SUCH GUARD EXISTS IN THIS FILE. `landed == len(arms)` is asserted nowhere; `incomplete`
    # never reaches the exit code. A comment promising a protection nothing performs is the R29
    # VOID-8 shape exactly.
    #
    # Demonstrated on a fixture: an arm with DONE.json deleted and results.jsonl truncated to 117 of
    # 230 rows printed ".. IN FLIGHT" and "every landed arm passes (31 of 62)", exit 0. A half
    # written arm missing 113 rows read as healthy progress, and the frozen read's STEP 0 -- whose
    # own wording is "GATE 0 liveness + ARM IDENTITY on ALL 62 ARMS" -- would have been recorded as
    # passed.
    #
    # Exit 3, not 1: an incomplete sweep is a LEGITIMATE state while the family is on the GPU (the
    # sweep is designed to be run mid-flight), so it must stay distinguishable by a caller from a
    # real GATE 0 failure. 3 already means "ran, but this is NOT the family's verdict".
    if landed != len(arms):
        print("GATE 0 IS NOT COMPLETE: %d of %d declared arms passed, %d in flight, %d never "
              "landed. THIS IS NOT THE FAMILY'S GATE 0 VERDICT and must not be recorded as one. "
              "Re-run when the job is gone; an arm still lacking DONE.json then has DIED, and the "
              "in-flight branch cannot tell those apart by itself. (R30-D/S-332)"
              % (landed, len(arms), incomplete, len(arms) - landed - incomplete))
        sys.exit(3)
    return 0


if __name__ == "__main__":
    main()
