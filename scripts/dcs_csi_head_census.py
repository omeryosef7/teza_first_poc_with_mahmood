"""The CENSUS reader for PR-CSI-012. A MAP, not a verdict.

WHY A NEW FILE AND NOT W4. W4 is a RANK-TEST tool: candidate, control family, floor, p. S-245 measured
that a rank among the 8 HD_TOPK singletons has an attainable floor of 1/8 = 0.125 and cannot clear
alpha = 0.05 for ANY effect size, so this family has no candidate and no family. Bending W4 into a census
would mean either inventing a control family from a prereg that deliberately declares none, or disabling
its rank test at read time -- and a tool whose central assertion can be switched off is not a guard.
S-246 gave W4 the reciprocal refusal; this file carries the mirror of it.

WHAT IT SHARES, DELIBERATELY. Every quantity that must mean the same thing across the sprint is imported
from the file that already defines it -- W4's `by_domain` (hence `load_installation`, the SOLE definition
of y_install and its concept-free channel filter), its `liveness`, its `boot_mean`/`pct`, its
`atomic_write_json`, and `dcs_csi_rederive_patch.strict_run_dir` for "a complete run". Nothing here
re-implements an endpoint or a resampler.

⚠ THE ONE CHECK THAT IS NEW, AND WHY IT HAS TO BE. S-246 measured that the realised-dose identity is
BLIND on this family: a K-head arm records K x 2016 prefill edits and the all-32 arm records 2016, so a
SINGLETON records exactly what HD_KO records. A mis-specified singleton that silently knocked out all 32
heads would PASS the dose check and then read as ONE HEAD CARRYING THE ENTIRE EFFECT -- the exact false
positive this census exists to avoid. So arm identity here is asserted from the run's OWN recorded
`knockout_heads` against the preregistered head set, per arm, and the expected dose is derived from
len(head_set) rather than from a single K constant.
"""
import argparse, collections, importlib.util, json, math, os, random, statistics, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


w4 = _load("w4", os.path.join(REPO, "scripts", "dcs_csi_head_analyze.py"))
rederive = _load("rederive", os.path.join(REPO, "scripts", "dcs_csi_rederive_patch.py"))

DOSE_UNIT = 2016          # the all-head arm's median prefill edits, MEASURED (S-215, S-246)


def recorded_heads(run_dir):
    """The arm's OWN record of which heads it knocked out. Returns None if the field is ABSENT --
    never [] and never 'all', because absence must not be readable as a value (R20-6's standing rule:
    any check whose PASS is consistent with reading nothing is not a check)."""
    cfg = json.load(open(os.path.join(run_dir, "config.json")))
    a = cfg.get("args", cfg)
    if "knockout_heads" not in a:
        return None
    v = a["knockout_heads"]
    if v is None or v == "":
        return "ALL"                      # omitted flag == all 32 band heads (HD_KO's shape)
    if isinstance(v, (list, tuple)):
        return [int(x) for x in v]
    return [int(x) for x in str(v).split(",")]


def recorded_cells(run_dir):
    """The arm's OWN record of which (layer, head) CELLS it knocked out (PR-CSI-014, S-291).

    Returns a sorted list of (L, h) tuples; `None` if the field is ABSENT; and the string
    "NOT_A_CELL_ARM" when the field exists but is empty.

    ⚠ THE EMPTY VALUE IS *NOT* "ALL", WHICH IS THE OPPOSITE OF `recorded_heads`' CONVENTION.
    There, an omitted `--knockout-heads` means "every head in the band" -- the widest possible
    intervention -- because the flag's absence is how the all-32 arm is expressed. Here an omitted
    `--knockout-cells` means the arm is not cell-scoped AT ALL; its scope is whatever
    `knockout_heads` says. Returning "ALL" would make a plain head arm read as a 288-cell arm, i.e.
    the widest possible reading of a field that was simply not in use.

    Absence (`None`) is still distinct from emptiness: every artefact produced BEFORE S-291 lacks the
    key entirely, and "this run predates the flag" must not be readable as "this run used no cells"
    (R20-6: any check whose PASS is consistent with reading nothing is not a check)."""
    cfg = json.load(open(os.path.join(run_dir, "config.json")))
    a = cfg.get("args", cfg)
    if "knockout_cells" not in a:
        return None
    v = a["knockout_cells"]
    if v is None or v == "":
        return "NOT_A_CELL_ARM"
    if isinstance(v, (list, tuple)):
        out = [(int(x[0]), int(x[1])) for x in v]
    else:
        out = []
        for tok in str(v).split(","):
            tok = tok.strip()
            if not tok:
                continue
            L, h = tok.split(":")
            out.append((int(L), int(h)))
    return sorted(out)


def band_width(prereg):
    """How many LAYERS the preregistered band spans, read from the prereg's own `intervention`.

    Taken from the prereg rather than hardcoded as 9, because the band is a preregistered quantity
    and a constant here could silently disagree with the arm that ran."""
    iv = prereg.get("intervention") or {}
    band = iv.get("band")
    if not band:
        spec = iv.get("intervene") or ""
        parts = spec.split(":")
        band = parts[2] if len(parts) > 2 else ""
    if not band:
        raise SystemExit("REFUSING: the prereg carries no intervention band, so a per-cell dose "
                         "cannot be derived. Cell arms need one.")
    lo, hi = (int(x) for x in str(band).split("-"))
    if hi < lo:
        raise SystemExit("REFUSING: band %r is inverted" % (band,))
    return hi - lo + 1


def per_cell_dose(prereg, dose_unit=None):
    """The prefill edits ONE cell is EXPECTED to record: DOSE_UNIT / (layers in the band).

    ⚠ THIS IS A PREDICTION, NOT A MEASURED IDENTITY, AND THE DIFFERENCE IS LOAD-BEARING.
    `DOSE_UNIT = 2016` was MEASURED (S-215, S-246): it is what a one-head arm actually recorded. The
    per-cell figure divides it by the band width, which assumes the 2016 edits are spread UNIFORMLY
    across the nine layers -- 224 each. That assumption has never been tested and CANNOT be tested
    from any artefact on disk, because the hook counters are summed across layers before they are
    written (pair_common seeds them once and every per-layer hook increments the same dict).

    So the first cell arm ever run VALIDATES this arithmetic; it does not merely pass a gate built on
    it. Consumers must report a cell arm's dose check as UNVERIFIED until that happens, which is why
    this returns the expectation and the divisibility fact TOGETHER rather than a bare number."""
    unit = DOSE_UNIT if dose_unit is None else int(dose_unit)
    n = band_width(prereg)
    if n <= 0:
        raise SystemExit("REFUSING: band width %d" % n)
    if unit % n != 0:
        raise SystemExit(
            "REFUSING: DOSE_UNIT %d is not divisible by the %d-layer band, so a per-cell dose is "
            "not an integer and the uniformity assumption is already false. Measure the per-cell "
            "dose before gating on it." % (unit, n))
    return unit // n, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--tag-prefix", required=True)
    ap.add_argument("--split", required=True, choices=["train", "validation", "test"])
    ap.add_argument("--expect-n", type=int, required=True)
    ap.add_argument("--require-slurm-job", default=None)
    ap.add_argument("--allow-short", type=int, default=0)
    ap.add_argument("--B", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20260922)
    ap.add_argument("--ci", type=float, default=0.95)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    pr = json.load(open(a.prereg))

    # THE MIRROR OF S-246's GUARD. This tool must refuse a RANK prereg as firmly as the rank tools
    # refuse a census, or the two families could be read by the wrong estimator in either direction.
    if not pr.get("NO_RANK_TEST"):
        sys.exit("REFUSING: prereg %r does not declare NO_RANK_TEST -- it is a RANK-TEST "
                 "preregistration (candidate + control family + floor) and this is the CENSUS reader. "
                 "Use scripts/dcs_csi_head_analyze.py. (S-247)" % pr.get("id"))
    if pr["split"] != a.split:
        sys.exit("REFUSING: prereg says split %r, invoked with %r" % (pr["split"], a.split))

    # ⛔⛔ S-296. EVERY PREREG FIELD THIS READER WILL NEED IS VALIDATED *HERE*, BEFORE ANY ARM IS
    # LOADED. This file already carries S-261's note that a bare `E["HD_TOPK"]` would KeyError "after
    # everything was computed and before anything was written, which is fail-closed but needlessly
    # destructive of a completed run" -- and then did the same thing with `pr["WHAT_THIS_CANNOT_ANSWER"]`,
    # which is read only while building `out`. PR-CSI-014 is a CENSUS that emitted the RANK family's
    # field name (`WHAT_THIS_CANNOT_DO`), so this reader would have died at the last step, AFTER the GPU
    # time was already spent. A field the reader needs is a PRECONDITION, not a late lookup.
    _cannot = next((k for k in ("WHAT_THIS_CANNOT_ANSWER", "WHAT_THIS_CANNOT_DO") if k in pr), None)
    if _cannot is None:
        sys.exit("REFUSING: prereg %r carries neither WHAT_THIS_CANNOT_ANSWER nor "
                 "WHAT_THIS_CANNOT_DO. The census report copies that block verbatim so a reader cannot "
                 "see the numbers without the limits; absence is not a pass (R20-6). (S-296)"
                 % pr.get("id"))
    for _f in ("CENSUS_DELIVERABLE", "SELECTION_RE_ENTERS_WHEN", "DOSE_IDENTITY_IS_BLIND_HERE",
               "population", "n_arms_per_split", "id"):
        if _f not in pr:
            sys.exit("REFUSING: prereg %r carries no %r, which this reader copies into the report. "
                     "Checked BEFORE the arms are loaded so a missing field costs milliseconds and not "
                     "a GPU allocation. (S-296)" % (pr.get("id"), _f))

    # ⛔ CELL FAMILIES (PR-CSI-014). A prereg carrying `cell_sets` names (layer, head) CELLS; the two
    # blocks are mutually exclusive, as in the GATE 0 sweep and the argv generator (S-292, S-293).
    _cs = pr.get("cell_sets")
    if _cs and pr.get("head_sets"):
        sys.exit("REFUSING: prereg %r carries BOTH head_sets and cell_sets. An arm family is one or "
                 "the other. (S-296)" % pr.get("id"))
    if not _cs and "head_sets" not in pr:
        sys.exit("REFUSING: prereg %r carries neither head_sets nor cell_sets. (S-296)" % pr.get("id"))
    IS_CELLS = bool(_cs)
    if IS_CELLS:
        hs = {k: [tuple(int(x) for x in c) for c in v] for k, v in _cs.items()}
        PER_CELL, NLAYERS = per_cell_dose(pr)
        # S-301: the STATUS comes from the PREREG, not from a hardcoded string. It was literally
        # "PREDICTED, NOT MEASURED", which was true when S-292 wrote it and became FALSE the moment
        # PR-CSI-014 measured 224.0 on nine cells (S-299). A banner that cannot stop saying "predicted"
        # after the prediction has been confirmed is a banner that will eventually mislead.
        _dose_status = (pr.get("DOSE_EXPECTATION") or {}).get("STATUS", "STATUS NOT DECLARED BY THE PREREG")
        print("[census] CELL family: per-cell dose %d = %d/%d layers -- %s"
              % (PER_CELL, DOSE_UNIT, NLAYERS, _dose_status))
    else:
        hs = pr["head_sets"]
    # S-261, discharging S-260's rule. The base arms are NAMED BY THE PREREG, defaulting to
    # PR-CSI-010's names (verified to bind by the byte-identity regression in S-261). Before this they
    # were literals throughout this file. That was FAIL-CLOSED -- a family with other names would have
    # missed at strict_run_dir and refused loudly, never silently -- but it is the same latent shape
    # that made PR-CSI-013 VOID in S-260, and it left this reader inconsistent with the argv generator
    # and the GATE 0 sweep, which both read `base_arms` now.
    base_arm, ko_arm = list(pr.get("base_arms", ["HD_BASE", "HD_KO"]))
    for b in (base_arm, ko_arm):
        if b in hs:
            sys.exit("REFUSING: base arm %r also appears in %s -- it carries no arm list"
                     % (b, "cell_sets" if IS_CELLS else "head_sets"))
    arms = [base_arm, ko_arm] + sorted(hs)
    if len(arms) != pr["n_arms_per_split"]:
        sys.exit("REFUSING: resolved %d arms, prereg declares n_arms_per_split=%d"
                 % (len(arms), pr["n_arms_per_split"]))
    jobs = a.require_slurm_job.split(",") if a.require_slurm_job else None

    dirs, per, live, slots = {}, {}, {}, {}
    for arm in arms:
        d = rederive.strict_run_dir("%s_%s" % (a.tag_prefix, arm), a.expect_n,
                                    row_file="results.jsonl", allow_short=a.allow_short,
                                    require_slurm_jobs=jobs)
        dirs[arm] = d
        per[arm], slots[arm], _, _ = w4.by_domain(d)
        live[arm] = w4.liveness(d)

    doms = sorted(set.intersection(*(set(v) for v in per.values())))
    print("[census] arms = %d | domains common to ALL arms = %d | expect-n = %d | split = %s"
          % (len(arms), len(doms), a.expect_n, a.split))
    if not doms:
        sys.exit("VACUOUS: no domain is present in every arm")
    ragged = {arm: sorted(set(per[arm]) - set(doms)) for arm in arms if set(per[arm]) - set(doms)}
    if ragged:
        sys.exit("REFUSING: arms disagree on their domain sets: %s"
                 % {k: v[:4] for k, v in list(ragged.items())[:4]})
    ref = slots[arms[0]]
    for arm in arms[1:]:
        bad = {d for d in doms if slots[arm].get(d) != ref.get(d)}
        if bad:
            sys.exit("REFUSING: arm %s binds different SLOTS from %s in %d domain(s) (e.g. %s)"
                     % (arm, arms[0], len(bad), sorted(bad)[:3]))
    # W4's R15-9a convention, ADOPTED RATHER THAN RE-INVENTED. The domain count binds only when the
    # run CLAIMS to be the preregistered one -- i.e. when --expect-n equals the preregistered row
    # count. W4 derives the condition from expect_n instead of offering an override flag, because an
    # override could be passed to a real run to silence the guard while expect_n is already pinned by
    # the arms themselves (strict_run_dir admits no arm whose rows_written differs). An off-protocol
    # count is announced LOUDLY instead of being quietly treated as compliant. The first version of
    # this file made the check unconditional, which is stricter but diverges from the sprint's own
    # reasoned convention for no stated reason -- and a second convention is a second thing to get
    # wrong.
    want_dom = pr["population"]["%s_domains" % a.split]
    want_n = pr["population"]["%s_expect_n" % a.split]
    on_protocol = (a.expect_n == want_n)
    if on_protocol:
        if len(doms) != want_dom:
            sys.exit("REFUSING: %d domains analysed but %s preregisters %d for %s"
                     % (len(doms), pr["id"], want_dom, a.split))
    else:
        print("[census] OFF-PROTOCOL: --expect-n %d != the preregistered %d for %s, so the domain "
              "count (%d, prereg says %d) is NOT binding and NOTHING HERE IS A RESULT."
              % (a.expect_n, want_n, a.split, len(doms), want_dom))
    test_dom = set(pr["population"].get("test_domain_ids") or [])
    leaked = sorted(set(doms) & test_dom)
    if leaked:
        sys.exit("REFUSING: TEST domain(s) present: %s (VOID 5)" % leaked)

    # ---- GATE 0 + ARM IDENTITY. The identity check is the only one that works here (S-246). ----
    # ⛔⛔ R26. `dose_is_diagnostic_of_identity` USED TO BE `want_dose not in (DOSE_UNIT,)`, i.e. "the
    # dose identifies this arm unless it equals the all-head arm's dose". That hardcodes ONE collision
    # and misses every other one, and it was WRONG ON 10 OF D34's 44 ARMS: the eight LOO_* arms all
    # expect 14112, and HD_TOPK and HD_BOTK BOTH expect 16128 -- so the dose cannot distinguish the
    # candidate 8-set from the null 8-set, which is the contrast D32/D33 rest on, while the field
    # claimed it could. On a CELL family it is wrong again and in the same direction: every 1-cell arm
    # expects 224, so the dose cannot tell CL_L06 from CL_L10.
    #
    # The property is DERIVED now: a dose identifies an arm iff no OTHER arm in this family expects the
    # same dose. That is the general statement of S-246's collision, and it subsumes the old rule.
    # ⚠ No scientific claim moves. Identity was always asserted from each arm's own recorded head/cell
    # list, which is the check that actually discriminates; this field only reports what the DOSE
    # contributed, and it was overstating it.
    _dose_of = {}
    for arm in arms:
        _k = 0 if arm == base_arm else (32 if arm == ko_arm else len(hs[arm]))
        if IS_CELLS and arm not in (base_arm, ko_arm):
            _dose_of[arm] = PER_CELL * _k
        else:
            _dose_of[arm] = 0 if arm == base_arm else (DOSE_UNIT if arm == ko_arm else DOSE_UNIT * _k)
    _dose_counts = collections.Counter(_dose_of.values())

    g0, ident = {}, {}
    for arm in arms:
        L = live[arm]
        k = 0 if arm == base_arm else (32 if arm == ko_arm else len(hs[arm]))
        # On a CELL family the two base arms stay HEAD-level: base_arm is the clean reference and
        # ko_arm the all-32/all-band denominator. Only the remaining arms are cell-scoped, and their
        # expected dose is PER_CELL * (number of cells), not DOSE_UNIT * k.
        if IS_CELLS and arm not in (base_arm, ko_arm):
            want_dose = PER_CELL * k
        else:
            want_dose = 0 if arm == base_arm else (DOSE_UNIT if arm == ko_arm else DOSE_UNIT * k)
        if arm == base_arm:
            # ⚠ R30-A/S-332: `got` was hardcoded to None here and the verdict below then read
            # `(got in (None, "ALL", []) or True)` -- an expression that is unconditionally True.
            # The base arm's own recorded flags were never read, and the published report wrote
            # "recorded": null, which ACTIVELY CONCEALS a flag rather than merely missing it.
            # VOID condition 4 ("BF_BASE carrying any intervention flag") was, like VOID 8 before
            # R29, prose consumed by no reader. The dose check catches a base arm whose hook really
            # fired; it cannot catch a config/run mismatch, which is what this reads.
            got = recorded_cells(dirs[arm]) if IS_CELLS else recorded_heads(dirs[arm])
        elif IS_CELLS and arm != ko_arm:
            # IDENTITY FROM knockout_cells ONLY. This arm's knockout_heads is EMPTY, which
            # recorded_heads() maps to "ALL" -- so the head-level check would certify every 1-cell arm
            # as the all-32 knockout (S-292).
            got = recorded_cells(dirs[arm])
        else:
            got = recorded_heads(dirs[arm])
        if arm == base_arm:
            # R30-A/S-332: a genuine test. The base arm must record NO cell list and NO head list.
            # recorded_heads() maps an empty knockout_heads to "ALL" (S-292), so "ALL" is the
            # base arm's EMPTY, not a knockout of everything -- the dose check (want 0) is what
            # separates those two, and it runs alongside this.
            _bad_base = got not in (None, "ALL", [], "", "NOT_A_CELL_ARM")
            ok_id = not _bad_base
            why = "not intervened" if ok_id else "CARRIES AN INTERVENTION FLAG: %r" % (got,)
        elif arm == ko_arm:
            # ⚠ R27/S-310 -- THE COLLISION ON THE DENOMINATOR. Cell arms are defended by
            # `knockout_cells`; the all-32 arm was defended by `knockout_heads == "ALL"` ALONE. But a
            # full-band NINE-CELL arm (all 9 layers of one head) also records an EMPTY
            # `knockout_heads`, which recorded_heads() maps to "ALL", AND it carries the identical
            # dose 9 x 224 = 2016. So on any family containing such an arm, CL_KO and that arm are
            # INDISTINGUISHABLE on both the identity field and the dose -- R27 demonstrated it on a
            # 3-arm scratch family, where the sweep printed "ALL 32  PASS" for an arm that was one
            # head wide. PR-CSI-016 is exactly that family: the census reader refuses a prereg
            # carrying both head_sets and cell_sets, so its whole-head arms MUST be expressed as
            # 9-cell lists. The defect was "not exploitable today" when R27 filed it and would have
            # been exploitable by the very next family.
            # A true all-32 arm carries NO cell list. Absence of the field is NOT a pass (R20-6).
            _kc = recorded_cells(dirs[arm])
            # ⚠ R28/S-312 -- S-310 OVER-REACHED AND BROKE A PUBLISHED FAMILY. The collision it closed
            # exists only where an arm CAN be cell-scoped. D34 (PR-CSI-012) is a pure HEAD census whose
            # HD_KO predates --knockout-cells, so the field is ABSENT, and requiring it made D34
            # unreadable -- while this file's own comments call D34's reproduction load-bearing.
            # In a head family no arm can impersonate the denominator, so the cell check is scoped to
            # cell families, where every arm is post-S-291 and the field always exists.
            ok_id = (got == "ALL") and (_kc == "NOT_A_CELL_ARM" or not IS_CELLS)
            if got != "ALL":
                why = "expected ALL, recorded %r" % (got,)
            elif _kc is None and IS_CELLS:
                why = ("config records NO knockout_cells field -- CANNOT distinguish the all-32 arm "
                       "from a full-band 9-cell arm, which shares its dose (R20-6)")
            elif not IS_CELLS:
                why = "omitted flag == all 32 (head family: no arm here can be cell-scoped)"
            elif _kc != "NOT_A_CELL_ARM":
                why = ("THE DENOMINATOR IS CELL-SCOPED: knockout_heads is empty (reads as ALL) but "
                       "knockout_cells records %r. This is the S-246 collision on the KO arm and the "
                       "dose 2016 cannot tell them apart." % (_kc,))
            else:
                why = "omitted flag == all 32, and no cell list"
        elif got is None:
            ok_id, why = False, "config records NO knockout_heads field -- CANNOT VERIFY (absence is " \
                                "not a value; R20-6)"
        elif got == "ALL":
            ok_id, why = False, "config records ALL 32 heads but the prereg says %s -- THIS IS THE " \
                                "S-246 COLLISION: the dose check would have passed" % (hs[arm],)
        elif IS_CELLS:
            if got == "NOT_A_CELL_ARM":
                ok_id, why = False, "config records an EMPTY knockout_cells -- this arm is not " \
                                    "cell-scoped, so it is not the arm the prereg names"
            else:
                ok_id = (list(got) == sorted(hs[arm]))
                why = "matches prereg" if ok_id else "recorded %s != prereg %s" % (got, sorted(hs[arm]))
        else:
            ok_id = (list(got) == list(hs[arm]))
            why = "matches prereg" if ok_id else "recorded %s != prereg %s" % (got, hs[arm])
        ident[arm] = {"k": k, "recorded": got, "expected": (None if arm in (base_arm, ko_arm)
                                                            else list(hs[arm])),
                      "ok": bool(ok_id), "why": why}
        # ⛔ CELL-ONLY METADATA. Added ONLY on a cell family so a HEAD family's report stays
        # BYTE-IDENTICAL. D34's full-object reproduction has been load-bearing evidence four times in
        # this sprint (S-261, S-292, S-295, and the check below), and growing keys on an existing
        # artefact would retire that property to say something a cell family can say for itself.
        if IS_CELLS:
            ident[arm]["identity_field"] = ("knockout_cells" if arm not in (base_arm, ko_arm)
                                            else "knockout_heads")
        g0[arm] = {"n_rows": L["n_rows"], "violations": L["violations"],
                   "total_decode_edits": L["total_decode_edits"],
                   "median_prefill_edits": L["median_prefill_edits"],
                   "expected_median_prefill_edits": want_dose,
                   "dose_ok": (L["median_prefill_edits"] == want_dose),
                   # S-246: the dose value 2016 is shared by HD_KO and EVERY SINGLETON, so for
                   # those arms the dose is a liveness check and NOT an identity check. Said out loud
                   # per arm so a reader never mistakes a passing dose for a verified arm.
                   "dose_is_diagnostic_of_identity": (_dose_counts[want_dose] == 1),
                   "n_arms_sharing_this_expected_dose": _dose_counts[want_dose],
                   "pass": bool(L["violations"] == {} and L["total_decode_edits"] == 0
                                and L["median_prefill_edits"] == want_dose and ok_id)}
        if IS_CELLS:
            # ⚠ R27/S-308 -- THE FOURTH INSTANCE OF THE S-305 CLASS, and the first to reach a
            # PUBLISHED artefact. S-301 replaced this exact hardcode at the PRINT banner and left it
            # here, 160 lines below, where it is written into the JSON for every cell arm. The
            # published PR-CSI-015 report therefore declares all 27 of its cell arms "PREDICTED ...
            # untested uniformity assumption" while its own prereg declares STATUS "MEASURED" and its
            # own stdout says the dose is CONFIRMED. The prereg is the source; this file is not.
            g0[arm]["dose_expectation_status"] = (
                str((pr.get("DOSE_EXPECTATION") or {}).get(
                    "STATUS", "STATUS NOT DECLARED BY THE PREREG -- treat the dose as UNVERIFIED"))
                if arm not in (base_arm, ko_arm) else "MEASURED (S-215, S-246)")
    failed = sorted(k for k, v in g0.items() if not v["pass"])
    if failed:
        for k in failed:
            print("  GATE 0 FAIL %-12s dose %s want %s | identity: %s"
                  % (k, g0[k]["median_prefill_edits"], g0[k]["expected_median_prefill_edits"],
                     ident[k]["why"]))
        sys.exit("CANNOT ANSWER: GATE 0 failed on %d arm(s): %s" % (len(failed), failed))
    print("[census] GATE 0 PASS on all %d arms | arm identity verified from each run's own %s"
          % (len(arms), "knockout_cells (cell arms) / knockout_heads (base arms)" if IS_CELLS
             else "knockout_heads"))

    # ---- the census itself: E(arm) = mean over DOMAINS of (y(arm) - y(HD_BASE)) ----
    rng = random.Random(a.seed)
    lo_q, hi_q = (1 - a.ci) / 2.0, 1 - (1 - a.ci) / 2.0
    E, CI = {}, {}
    for arm in arms:
        if arm == base_arm:
            continue
        d = [per[arm][x] - per[base_arm][x] for x in doms]
        E[arm] = statistics.fmean(d)
        bs = w4.boot_mean(d, a.B, rng)
        CI[arm] = [w4.pct(bs, lo_q), w4.pct(bs, hi_q)]

    singles = sorted(k for k in hs if k.startswith("SINGLE_"))
    loos = sorted(k for k in hs if k.startswith("LOO_"))
    # the LOO marginal: what head h contributes to the 8-set = E(HD_TOPK) - E(LOO_h)
    marg = {k: (E["HD_TOPK"] - E[k]) for k in loos} if "HD_TOPK" in E else {}

    if IS_CELLS:
        # THE DEPTH MAP. Printed in LAYER order, not sorted by effect: the question is where the load
        # sits along depth, and sorting by effect hides the shape that answers it. The detectability
        # threshold is printed BESIDE every row, and the preregistered coherent outcome is restated
        # here so a reader of the log sees it next to the numbers rather than only in the prereg.
        # ⛔⛔⛔ S-301. THE BAR IS RESOLVED PER CELL AND ITS ABSENCE IS A REFUSAL, NOT A ZERO.
        # This read `DETECTABILITY_PREREGISTERED.min_abs_E_for_ci95_to_exclude_0` and nothing else. A
        # prereg that names its bars ANYWHERE ELSE -- PR-CSI-015 puts them in
        # `DETECTABILITY_PREREGISTERED_PER_HEAD` because its three heads have different spreads -- would
        # leave `_thr = None`, every `clears` test would be False, and the headline would print
        # "0 of 27 cells CLEAR THE PREREGISTERED BAR". **A FALSE NULL MANUFACTURED BY A MISSING FIELD**,
        # and the most damaging possible form of it: the preregistered verdict would read as the
        # preregistered-coherent "nothing concentrates" outcome. This is the R20-6 rule -- any check
        # whose result is consistent with reading NOTHING is not a check -- on the one field the whole
        # verdict turns on.
        # ⚠ R27/S-308: S-301 taught THIS function the PER_HEAD container and left the three other
        # consumers of the same block reading the old name only -- so PR-CSI-015's published report
        # carried DETECTABILITY_PREREGISTERED, preregistered_bar and
        # NOTHING_CLEARED_THE_BAR_IS_A_PREREGISTERED_COHERENT_OUTCOME as **null** while its headline
        # was computed against the per-head bars that were right there. The fix is ONE resolver that
        # every consumer goes through, because the defect class is "fixed at the site in front of me".
        # ⚠ R30-A/S-333: this was `PER_HEAD or DETECTABILITY_PREREGISTERED or {}` -- an `or`, not a
        # search -- so the moment a prereg carried a per-head block the LEGACY block became
        # unreachable for every field. That is precisely the S-308 defect the single resolver was
        # written to end ("a null in a published artefact"), transposed off the bars and onto the
        # coherent-outcome text: a prereg that DOES record
        # COHERENT_OUTCOME_IF_NOTHING_CLEARS_IT in the legacy block published `null`, and had
        # nothing cleared the bar, stdout would have printed "⚠ THE PREREG RECORDS NO
        # COHERENT-OUTCOME TEXT ... do not read this null as a preregistered null" against a prereg
        # that records exactly that text. Precedence is preserved -- the per-head block still wins
        # every field it defines -- but a field it does not define is no longer invisible.
        _detect_blocks = [b for b in (pr.get("DETECTABILITY_PREREGISTERED_PER_HEAD"),
                                      pr.get("DETECTABILITY_PREREGISTERED"))
                          if isinstance(b, dict)]
        _HAS_PER_HEAD = bool((pr.get("DETECTABILITY_PREREGISTERED_PER_HEAD") or {}).get("per_head"))

        def _detect(*names, **kw):
            """A field of the detectability block under ANY of its spellings, searched across BOTH
            blocks in precedence order. Absence is explicit."""
            for _blk in _detect_blocks:
                for nm in names:
                    if nm in _blk and _blk[nm] is not None:
                        return _blk[nm]
            return kw.get("default")

        _per_head_bars = (pr.get("DETECTABILITY_PREREGISTERED_PER_HEAD") or {}).get("per_head") or {}
        _single_bar = (pr.get("DETECTABILITY_PREREGISTERED") or {}).get(
            "min_abs_E_for_ci95_to_exclude_0")

        # ⚠ S-311. THE BAR AS A *RULE* RATHER THAN A NUMBER, and why that is not a loophole.
        # PR-CSI-016 reads BUTTON. Heads 17 and 23 have never had a button arm, so no bar for them
        # can exist as a number before the family runs -- and S-308 (correctly) made a missing
        # numeric bar a REFUSAL. The way out is NOT to weaken that refusal but to let a prereg freeze
        # the DERIVATION instead, naming the arm it will be computed from. The rule is frozen before
        # any arm runs; only its ARITHMETIC waits for the data.
        #   * the source arm must be named PER HEAD and must be IN THIS FAMILY;
        #   * it must be that head's FULL BAND -- every layer, exactly once. A source arm pointing at
        #     a single cell would compute the bar from the very quantity it is used to judge, which
        #     is the circularity this whole block exists to avoid, so it is a REFUSAL;
        #   * it is EXCLUDED from the depth map and from every clearing count: it is a 9-cell arm,
        #     not a cell, and counting it would put a 2016-dose arm in a per-cell census;
        #   * absence of BOTH a number and a rule is still a refusal (R20-6, unchanged).
        _bar_rule = (pr.get("DETECTABILITY_PREREGISTERED_PER_HEAD") or {}).get("BAR_IS_A_RULE") or {}
        # ⚠ R28/S-312: the rule's ONLY numeric parameter must be DECLARED and sane, and it is a
        # property of the RULE, so it is validated ONCE here rather than per head -- a parameter
        # checked inside a per-head branch is only checked for the heads that reach that branch.
        # A missing z used to default to 1.96 and then be written into the report as though the
        # prereg had frozen it: false metadata in a published artefact, the R27/S-308 class. And
        # z = 0.0 was accepted, giving a bar of 0.0 and "11 of 27 cells CLEAR THE PREREGISTERED BAR".
        _RULE_Z = None
        if _bar_rule:
            if "z" not in _bar_rule:
                sys.exit("REFUSING: prereg %r declares BAR_IS_A_RULE without `z`. The rule's only "
                         "numeric parameter cannot be supplied by this file -- that would publish a "
                         "default as though it were preregistered. (R28/S-312)" % pr["id"])
            try:
                _RULE_Z = float(_bar_rule["z"])
            except (TypeError, ValueError):
                sys.exit("REFUSING: BAR_IS_A_RULE.z = %r is not a number. (R28/S-312)"
                         % (_bar_rule["z"],))
            if not (0.5 <= _RULE_Z <= 5.0):
                sys.exit("REFUSING: BAR_IS_A_RULE.z = %r is outside [0.5, 5.0]. z=0 makes every cell "
                         "clear a bar of zero; an enormous z makes every cell fail. (R28/S-312)"
                         % _RULE_Z)
        # ⚠ R28/S-312: keyed on ARM GRANULARITY, not on the bar_source_arm string. Keying on the
        # string meant that a head whose bar is a frozen NUMBER left its own 9-cell whole-head arm in
        # the census -- leaking a 2016-dose arm into the depth map, into the clearing counts, and into
        # the per-CELL dose check, which then printed "REFUTED -- the uniformity assumption is WRONG"
        # on a perfectly healthy run. A per-CELL census judges CELLS; an arm covering more than one
        # cell is a whole-head arm whatever the prereg calls it.
        _NAMED_SOURCES = {d.get("bar_source_arm") for d in _per_head_bars.values()
                          if isinstance(d, dict) and d.get("bar_source_arm")}
        _BAR_SOURCE_ARMS = {k for k in hs if len(hs[k]) > 1} | (_NAMED_SOURCES & set(hs))
        for _nm in sorted(_NAMED_SOURCES - set(hs)):
            sys.exit("REFUSING: bar_source_arm %r is not an arm of prereg %r. (S-311)"
                     % (_nm, pr["id"]))
        # ⚠ R30-A/S-333. EVERYTHING NAMED HERE IS REMOVED FROM THE CENSUS BEFORE ANY CHECK LOOKS AT
        # IT. `_bar_from_rule`'s in-family / full-band guards only ever run for heads that reach
        # `_bar_for`, i.e. heads that still have judged cells -- so a per_head key for a head with no
        # 1-cell arms (a typo, a template leftover, a head retired from the family) deleted arms from
        # the depth map with ZERO validation. The comment at the _bar_for branch already names this
        # shape -- "the named arm has already been removed from the census ... An arm can vanish from
        # a published depth map with no check having looked at it" -- and closed only the
        # both-criteria sub-case.
        #
        # R30-A demonstrated both halves. One stray entry `per_head["99"] = {"bar_source_arm":
        # "BF_H11_L07"}` silently cut n_cells_judged from 8 to 7. Four stray entries naming head 6's
        # four cells deleted HEAD 6 ENTIRELY: gone from the depth map, from the per-head bars and
        # from every clearing count, the headline moving from "6 of 8 cells CLEAR" to "3 of 4", exit
        # 0, and not one line of stdout mentioning it. That is a head dropped by an admission-like
        # mechanism with no mention -- the R29 class recurring at a new site.
        #
        # The geometry guard is therefore hoisted to run for EVERY named source, before exclusion.
        _FAMILY_HEADS = {int(c[1]) for _k in hs for c in hs[_k]}
        for _hk, _hd in sorted(_per_head_bars.items()):
            _src = (_hd or {}).get("bar_source_arm") if isinstance(_hd, dict) else None
            if not _src:
                continue                       # a head whose bar is a frozen NUMBER names no arm
            # ⚠ R30-A/S-333 F7: MOST SPECIFIC DIAGNOSIS FIRST. Hoisting the geometry guard made it
            # fire ahead of two narrower prereg-authoring checks that had lived downstream in
            # `_bar_for`/`_bar_from_rule`, so "you gave this head two criteria" was reported as
            # "this arm is not a full band" -- both refuse, but the operator is sent to the wrong
            # line. R30-A filed exactly this ordering complaint against the VOID-8 loop. Centralise
            # the precedence here rather than leave it to whichever check happens to run first.
            if _hd.get("min_abs_E_for_ci95_to_exclude_0") is not None:
                sys.exit("REFUSING: prereg %r gives head %s BOTH a frozen bar "
                         "(min_abs_E_for_ci95_to_exclude_0) AND a bar_source_arm %r. A head has "
                         "ONE criterion. (R28/S-312)" % (pr["id"], _hk, _src))
            if not _bar_rule:
                sys.exit("REFUSING: prereg %r names bar_source_arm %r for head %s but declares no "
                         "DETECTABILITY_PREREGISTERED_PER_HEAD['BAR_IS_A_RULE'] block. An arm name "
                         "without a frozen derivation is not a preregistered criterion. (S-311)"
                         % (pr["id"], _src, _hk))
            try:
                _h = int(_hk)
            except (TypeError, ValueError):
                sys.exit("REFUSING: DETECTABILITY_PREREGISTERED_PER_HEAD key %r is not a head "
                         "number, yet it names bar_source_arm %r -- which would be removed from the "
                         "census on its say-so. (R30-A/S-333)" % (_hk, _src))
            if _h not in _FAMILY_HEADS:
                sys.exit("REFUSING: head %d is not a head of prereg %r (its heads are %s), yet its "
                         "per_head entry names bar_source_arm %r. A stray entry silently DELETES "
                         "that arm from the depth map and shrinks the census. (R30-A/S-333)"
                         % (_h, pr["id"], sorted(_FAMILY_HEADS), _src))
            if "layers" in pr:
                _want = sorted([int(L), _h] for L in pr["layers"])
                _got = sorted([int(c[0]), int(c[1])] for c in hs[_src])
                if _got != _want:
                    sys.exit("REFUSING: head %d's bar_source_arm %r covers %r, not that head's FULL "
                             "BAND %r. An arm narrower than the whole head is excluded from the "
                             "census on the strength of a name nothing checked. (R30-A/S-333)"
                             % (_h, _src, _got, _want))
        _bar_computed = {}

        def _bar_from_rule(h):
            """bar(h) from THIS family's own whole-head arm, per a rule frozen before the run."""
            src = (_per_head_bars.get(str(h)) or {}).get("bar_source_arm")
            if not src:
                return None
            if not _bar_rule:
                sys.exit("REFUSING: prereg %r names bar_source_arm %r for head %d but declares no "
                         "DETECTABILITY_PREREGISTERED_PER_HEAD['BAR_IS_A_RULE'] block. An arm name "
                         "without a frozen derivation is not a preregistered criterion. (S-311)"
                         % (pr["id"], src, h))
            if src not in hs:
                sys.exit("REFUSING: head %d's bar_source_arm %r is not an arm of prereg %r. (S-311)"
                         % (h, src, pr["id"]))
            if src not in per:
                sys.exit("REFUSING: head %d's bar_source_arm %r did not land, so its bar cannot be "
                         "computed. A bar that silently defaults is the S-301 false null. (S-311)"
                         % (h, src))
            if "layers" not in pr:
                sys.exit("REFUSING: prereg %r declares a bar RULE but no `layers`, so the full-band "
                         "guard cannot run. S-296: a field the reader needs is a PRECONDITION, not a "
                         "late lookup. (R28/S-312)" % pr["id"])
            want = sorted([int(L), int(h)] for L in pr["layers"])
            got = sorted([int(c[0]), int(c[1])] for c in hs[src])
            if got != want:
                sys.exit("REFUSING: head %d's bar_source_arm %r covers %r, not that head's FULL BAND "
                         "%r. A bar derived from anything narrower than the whole head is computed "
                         "from the quantity it judges. (S-311)" % (h, src, got, want))
            d = [per[src][x] - per[base_arm][x] for x in doms]
            z = _RULE_Z
            bar = z * statistics.stdev(d) / math.sqrt(len(doms))
            _bar_computed[str(h)] = {"bar": bar, "source_arm": src, "z": z, "n_domains": len(doms),
                                     "per_domain_SD": statistics.stdev(d),
                                     "E_of_the_source_arm": statistics.fmean(d),
                                     "COMPUTED_AT_READ_TIME_FROM_A_RULE_FROZEN_BEFORE_THE_RUN": True}
            return bar

        def _bar_for(arm):
            """That arm's preregistered bar. REFUSES rather than returning None."""
            h = sorted(hs[arm])[0][1]
            if str(h) in _per_head_bars:
                _e = _per_head_bars[str(h)]
                if (_e.get("min_abs_E_for_ci95_to_exclude_0") is not None
                        and _e.get("bar_source_arm")):
                    # ⚠ R28/S-312: the number wins, so _bar_from_rule never runs and NONE of its
                    # guards (in-family, full-band, landed) are applied -- yet the named arm has
                    # already been removed from the census. An arm can vanish from a published depth
                    # map with no check having looked at it. Two criteria for one head is not a
                    # preregistration.
                    sys.exit("REFUSING: prereg %r gives head %d BOTH a frozen bar "
                             "(min_abs_E_for_ci95_to_exclude_0) AND a bar_source_arm %r. A head has "
                             "ONE criterion. (R28/S-312)"
                             % (pr["id"], h, _e.get("bar_source_arm")))
                v = _e.get("min_abs_E_for_ci95_to_exclude_0")
                if v is None:
                    _r = _bar_from_rule(h)
                    if _r is not None:
                        return _r
                    sys.exit("REFUSING: prereg %r gives head %d no "
                             "min_abs_E_for_ci95_to_exclude_0. A missing bar would make every cell read "
                             "as 'below the bar' and print a FALSE NULL. (S-301)" % (pr["id"], h))
                return float(v)
            # ⚠ R27/S-308: FAIL CLOSED ON PARTIAL ABSENCE. S-301 closed the case where the prereg
            # has NO bar at all and left open the far more likely one: a prereg that carries a
            # PER_HEAD block but omits ONE head, alongside a legacy global bar. That head was then
            # silently judged against ANOTHER HEAD'S bar, with no warning and exit 0. Demonstrated by
            # R27 on the real 29 arms: removing per_head['23'] and leaving head 2's global 0.019181
            # flipped CL_H23_L07 from CLEARS to below-the-bar, the headline from 3-of-27 to 2-of-27,
            # and head 23 from preregistered outcome A to outcome C -- the distributed-profile NULL.
            # If a prereg declares bars PER HEAD, then EVERY head must be in it.
            if _HAS_PER_HEAD:
                sys.exit("REFUSING: prereg %r declares DETECTABILITY_PREREGISTERED_PER_HEAD but has "
                         "no entry for head %d. Falling back to a shared bar would judge this head "
                         "against ANOTHER head's criterion and can flip its preregistered outcome. "
                         "A per-head prereg must be total. (R27/S-308)" % (pr["id"], h))
            if _single_bar is not None:
                return float(_single_bar)
            sys.exit("REFUSING: prereg %r carries no preregistered detectability bar for head %d -- "
                     "neither DETECTABILITY_PREREGISTERED_PER_HEAD['per_head']['%d'] nor "
                     "DETECTABILITY_PREREGISTERED. Without it every cell would test as 'below the bar' "
                     "and the headline would report a null that was never measured. Absence is not a "
                     "pass (R20-6). (S-301)" % (pr["id"], h, h))

        _judged = [k for k in hs if k not in _BAR_SOURCE_ARMS]
        # ⚠ R30-A/S-333: the exclusion set was written to the JSON as
        # `bar_source_arms_EXCLUDED_FROM_THE_DEPTH_MAP` and printed NOWHERE, so a reader of the log
        # -- which is how these families are actually read at 4am -- saw a depth map and a clearing
        # count with no indication that arms had been removed to produce them. An exclusion that
        # changes the headline belongs on the transcript, next to the GATE 0 banner.
        print("[census] EXCLUDED FROM THE DEPTH MAP (%d arm(s), whole-head or named bar sources): "
              "%s\n[census] JUDGED: %d cell arm(s)."
              % (len(_BAR_SOURCE_ARMS), ", ".join(sorted(_BAR_SOURCE_ARMS)) or "none", len(_judged)))
        if not _judged:
            sys.exit("REFUSING: every arm of prereg %r is a bar source arm; there are no cells to "
                     "read. (S-311)" % pr["id"])
        # ⚠⚠ R29/S-323 -- VOID CONDITION 8, NOW ACTUAL CODE. PR-CSI-018's frozen read asserted
        # "VOID CONDITION 8 IS CHECKED HERE AND IT IS FREE ... Six independent provenance checks".
        # NOTHING CHECKED IT. `VOID_CONDITIONS` is written by every freeze script and consumed by no
        # reader, gate or test; `pr013_whole_head_REFERENCE` was written by one script and read by
        # none. That is the R27/VOID-6 state, and worse, because the read CLAIMED code performed it.
        # The compounding harm R29 demonstrated: a drifted HD_<h> silently moves that head's BAR
        # (the bar is 1.96*SD of that same arm), so the head is quietly DROPPED by ADMISSION and
        # published as "NOT_A_MISS ... removed from K", shrinking K and the permutation space with no
        # mention of provenance. Repointing HD_6 at another head's rows gave a 1.97e-03 difference --
        # ~2000x the 1e-6 threshold -- and the read exited 0 with "GATE 0 PASS on all 62 arms".
        # Generic by construction: it fires for ANY prereg whose per_head carries a reference block.
        # ⚠ R30-A/S-332: THIS LOOP USED TO `continue` OVER A MISSING OR NULL REFERENCE -- no count,
        # no print, no record -- which is the R20-6 rule this file preaches ("any check whose PASS is
        # consistent with reading NOTHING is not a check") violated on the one condition R29 was
        # filed for. The report carried no provenance key at all, so the artefact could not
        # distinguish "checked and free" from "never checked". That indistinguishability WAS the
        # substance of R29's finding; closing the drift case while leaving the absence case silent
        # reinstated it one branch over.
        # ⚠ AND A CORRECTION OF MY OWN FIRST FIX HERE. I first made a PARTIAL declaration -- some
        # heads carrying a reference, some not -- a REFUSAL, by analogy with S-308's "if a prereg
        # declares bars PER HEAD then EVERY head must be in it". That analogy is FALSE and the
        # existing VOID-8 tests caught it. A bar is something every head must have; a PRIOR
        # MEASUREMENT is something a head either has or does not. PR-CSI-016's heads 17 and 23 had
        # never had a button arm at all -- that absence is the entire reason S-311's bar-as-a-RULE
        # exists -- so a family where only some heads carry a reference is LEGITIMATE and expected.
        # The fix is disclosure, not refusal: every unevaluated head is named on stdout and in the
        # artefact, so "checked and free" can never again be confused with "never checked".
        _prov = {"checked": [], "skipped": [], "tolerances": {}}
        for _hk, _hd in sorted(_per_head_bars.items()):
            # ⚠ S-349: THE REFERENCE KEY ENCODED A FAMILY. This read only
            # `pr013_whole_head_REFERENCE`, so VOID condition 8 was reachable ONLY by families whose
            # prior measurement happens to be PR-CSI-013's. A BASKET family takes its references
            # from PR-CSI-012, would have had to misname the key to be checked at all, and would
            # otherwise have been skipped -- loudly since S-341, but skipped.
            # This is S-322 exactly: "widening a single-family artefact means finding everything
            # that ENCODES the family, not everything that NAMES it." The family-neutral key is
            # `whole_head_REFERENCE`; the PR-013 spelling stays readable so published preregs keep
            # working, and declaring BOTH is a refusal because a head has ONE criterion (S-312).
            _ref = None
            if isinstance(_hd, dict):
                _new = _hd.get("whole_head_REFERENCE")
                _old = _hd.get("pr013_whole_head_REFERENCE")
                if _new is not None and _old is not None:
                    sys.exit("REFUSING: head %s declares BOTH whole_head_REFERENCE and the legacy "
                             "pr013_whole_head_REFERENCE. A head has ONE provenance reference. "
                             "(S-349)" % _hk)
                _ref = _new if _new is not None else _old
            if not _ref or _ref.get("E") is None:
                _prov["skipped"].append(_hk)
                print("[census] PROVENANCE head %-3s -- NO REFERENCE DECLARED; VOID condition 8 was "
                      "NOT EVALUATED for this head (R30-A/S-332)" % _hk)
                continue
            # ⚠ R30-A/S-332: `void_tolerance` used to fall back to a 1e-6 SUPPLIED BY THIS FILE and
            # was accepted at any magnitude. Ten lines up, BAR_IS_A_RULE.z must be DECLARED ("the
            # rule's only numeric parameter cannot be supplied by this file -- that would publish a
            # default as though it were preregistered") and must lie in [0.5, 5.0] because a z of 0
            # makes every cell clear a bar of zero. The identical argument applies to a tolerance
            # and neither half had been applied: with void_tolerance 1e9 the reader printed
            # "|diff|=3.86e-03  OK" beside a 3860x violation. A check that states the opposite of
            # the truth is worse than one that stays silent.
            if _ref.get("void_tolerance") is None:
                sys.exit("REFUSING: head %s's whole_head_REFERENCE declares no "
                         "void_tolerance. A tolerance supplied by the READER is a default published "
                         "as though it were preregistered. (R30-A/S-332)" % _hk)
            _tol_decl = float(_ref["void_tolerance"])
            if not (0.0 < _tol_decl <= 1e-3):
                sys.exit("REFUSING: head %s's void_tolerance is %r, outside (0, 1e-3]. S-318 "
                         "demonstrated BIT-IDENTICAL reproduction of a whole-head arm across two "
                         "jobs and two nodes, so any tolerance approaching an effect size makes the "
                         "condition vacuous while still printing OK. (R30-A/S-332)" % (_hk, _tol_decl))
            _prov["tolerances"][_hk] = _tol_decl
            _src = _hd.get("bar_source_arm")
            if _src not in E:
                sys.exit("REFUSING: head %s declares a whole-head reference but its source arm %r is "
                         "absent, so the provenance condition cannot be evaluated. Absence is not a "
                         "pass (R20-6). (R29/S-323)" % (_hk, _src))
            _d = abs(E[_src] - float(_ref["E"]))
            _tol = _tol_decl
            _prov["checked"].append({"head": _hk, "source_arm": _src, "E": E[_src],
                                     "reference_E": float(_ref["E"]), "abs_diff": _d,
                                     "void_tolerance": _tol, "within": bool(_d <= _tol)})
            print("[census] PROVENANCE head %-3s %-8s E=%+.8f vs reference %+.8f  |diff|=%.2e  %s"
                  % (_hk, _src, E[_src], float(_ref["E"]), _d,
                     "OK" if _d <= _tol else "*** EXCEEDS %.0e ***" % _tol))
            if _d > _tol:
                sys.exit("REFUSING: VOID CONDITION -- head %s's arm %r records E=%.8f but the prereg "
                         "freezes a prior measurement of the SAME head, codeword and split at "
                         "%.8f (|diff| %.2e > %.0e). S-318 demonstrated bit-identical reproduction "
                         "across two jobs and two NODES, so this means the population, bank, "
                         "exclusions or model revision has DRIFTED and nothing in this family is "
                         "readable. (R29/S-323)"
                         % (_hk, _src, E[_src], float(_ref["E"]), _d, _tol))
        print("[census] VOID CONDITION 8: %d of %d head(s) CHECKED against a frozen prior "
              "measurement, %d NOT EVALUATED%s."
              % (len(_prov["checked"]), len(_per_head_bars), len(_prov["skipped"]),
                 "" if not _prov["skipped"] else " (heads %s)" % ", ".join(_prov["skipped"])))

        _heads_here = sorted({sorted(hs[k])[0][1] for k in _judged})
        # LAYER order within HEAD order: the question is the shape along depth, and on a multi-head
        # family interleaving the heads would hide each head's shape instead of showing three of them.
        _cells = sorted(_judged, key=lambda x: (sorted(hs[x])[0][1], sorted(hs[x])[0][0]))
        print("\n[census] DEPTH MAP -- head(s) %s, one cell per (head, layer), in HEAD then LAYER "
              "order. NO RANK, NO p."
              % (pr.get("h_star") if pr.get("h_star") is not None
                 else ", ".join(str(h) for h in _heads_here)))
        _bars_used = {h: _bar_for(next(k for k in _judged if sorted(hs[k])[0][1] == h))
                      for h in _heads_here}
        if len(_bars_used) == 1:
            print("         preregistered detectability bar: |E| > %.6f (S-294). The right-hand "
                  "column is the PREREGISTERED verdict;" % list(_bars_used.values())[0])
        else:
            print("         preregistered detectability bar, PER HEAD (S-294 method; these heads have "
                  "different spreads):")
            for h in _heads_here:
                print("           head %-3d |E| > %.6f" % (h, _bars_used[h]))
            print("         The right-hand column is the PREREGISTERED verdict;")
        print("         'ci95 excl 0' is a separate, WEAKER fact shown beside it.")
        _thr = list(_bars_used.values())[0] if len(_bars_used) == 1 else None
        # ⛔⛔ S-300, fixing the defect S-299 found in its own output. TWO CRITERIA LIVE HERE AND THEY
        # DISAGREE. The PREREGISTERED one is |E| > thr (S-294, frozen before any arm ran); "ci95 excludes
        # 0" is a DIFFERENT and much weaker test. On PR-CSI-014 they gave 1 and 2: CL_L11 excluded zero
        # at E = +0.000952 -- 5.0% of the bar, ci95 lower bound +0.000040 (24x smaller than |E|), and the
        # WRONG SIGN -- while the headline printed "2 of 9" directly under a line naming the bar.
        # The bar the prereg named is now the HEADLINE, and the weaker count is reported beside it as
        # what it is. A verdict must be read against the criterion that was frozen, not the one the
        # reader found convenient.
        _cleared, _excl0 = [], []
        for k in _cells:
            L, h = sorted(hs[k])[0]
            excl0 = (CI[k][1] < 0) or (CI[k][0] > 0)
            clears = abs(E[k]) > _bar_for(k)
            if excl0:
                _excl0.append((k, L, E[k]))
            if clears:
                _cleared.append((k, L, E[k]))
            print("   L%-3d %-9s E = %+.6f  ci95 [%+.6f, %+.6f]  %-14s %s"
                  % (L, k, E[k], CI[k][0], CI[k][1],
                     "CLEARS THE BAR" if clears else "below the bar",
                     "ci95 excl 0" if excl0 else ""))
        print("\n[census] %d of %d cells CLEAR THE PREREGISTERED BAR (%s)."
              % (len(_cleared), len(_cells),
                 ("|E| > %.6f" % _thr) if _thr is not None else "each against its own head's bar"))
        if len(_heads_here) > 1:
            for h in _heads_here:
                _hc = [c for c in _cleared if sorted(hs[c[0]])[0][1] == h]
                _hn = [k for k in _cells if sorted(hs[k])[0][1] == h]
                print("           head %-3d: %d of %d clear (bar %.6f)%s"
                      % (h, len(_hc), len(_hn), _bars_used[h],
                         "  -> " + ", ".join("L%d" % c[1] for c in _hc) if _hc else ""))
        print("         (%d of %d have a ci95 excluding 0 -- a WEAKER test, not the preregistered "
              "criterion; a cell can exclude 0 at a fraction of the bar, and on PR-CSI-014 one did.)"
              % (len(_excl0), len(_cells)))
        if not _cleared:
            print("         NOTHING CLEARS THE BAR. This outcome was PREREGISTERED AS COHERENT "
                  "before any arm ran:")
            # Both spellings: PR-CSI-014 wrote ..._IT, PR-CSI-015 wrote ..._CLEARS. And the old
            # default ASSERTED that the prereg records something when it may not (R20-6).
            print("         " + str(_detect("COHERENT_OUTCOME_IF_NOTHING_CLEARS_IT",
                                            "COHERENT_OUTCOME_IF_NOTHING_CLEARS",
                                            default="\u26a0 THE PREREG RECORDS NO COHERENT-OUTCOME "
                                                    "TEXT FOR THIS BRANCH -- do not read this null as "
                                                    "a preregistered null (R20-6).")))
        # The per-cell dose is the arithmetic this family exists to validate -- say what it measured.
        _doses = sorted({g0[k]["median_prefill_edits"] for k in _cells})
        print("\n[census] PER-CELL DOSE VALIDATION: predicted %d, observed median_prefill_edits %s "
              "-> %s" % (PER_CELL, _doses,
                         "CONFIRMED" if _doses == [float(PER_CELL)] or _doses == [PER_CELL]
                         else "REFUTED -- the uniformity assumption behind DOSE_UNIT/band_width is "
                              "WRONG and every cell dose expectation must be re-derived (S-292)"))
    else:
        print("\n[census] SINGLE-HEAD EFFECTS, most negative first (E, ci95). NO RANK, NO p.")
        for k in sorted(singles, key=lambda x: E[x]):
            print("   %-11s E = %+.6f  ci95 [%+.6f, %+.6f]" % (k, E[k], CI[k][0], CI[k][1]))
        print("\n[census] LEAVE-ONE-OUT of HD_TOPK, and head h's MARGINAL = E(HD_TOPK) - E(LOO_h)")
        for k in sorted(loos, key=lambda x: -marg[x]):
            print("   %-11s E = %+.6f  ci95 [%+.6f, %+.6f]   marginal %+.6f"
                  % (k, E[k], CI[k][0], CI[k][1], marg[k]))
    # S-261: print only the anchors this family actually has. Bare E["HD_TOPK"] would KeyError on a
    # census whose prereg declares no K-head comparators -- after everything was computed and before
    # anything was written, which is fail-closed but needlessly destructive of a completed run.
    _anch = [(k, E[k]) for k in (ko_arm, "HD_TOPK", "HD_BOTK") if k in E]
    print("\n[census] anchors:  " + "   ".join("%s %+.6f" % (k, v) for k, v in _anch))

    out = {
        "schema": "dcs_csi_head_census/1",
        "prereg": a.prereg, "prereg_id": pr["id"], "split": a.split,
        "tag_prefix": a.tag_prefix, "expect_n": a.expect_n, "n_domains": len(doms),
        "B": a.B, "seed": a.seed, "ci": a.ci, "ON_PROTOCOL": on_protocol,
        "E": {k: round(v, 8) for k, v in E.items()},
        "ci95": {k: [round(v[0], 8), round(v[1], 8)] for k, v in CI.items()},
        "loo_marginal": {k: round(v, 8) for k, v in marg.items()},
        "GATE_0_and_identity": {"per_arm": g0, "identity": ident},
        "NO_RANK_TEST": True,
        "REPORTABLE_AS": pr["CENSUS_DELIVERABLE"],
        "CANNOT_DO": pr[_cannot],
        "SELECTION_RE_ENTERS_WHEN": pr["SELECTION_RE_ENTERS_WHEN"],
        "DOSE_IDENTITY_IS_BLIND_HERE": pr["DOSE_IDENTITY_IS_BLIND_HERE"],
        "NO_VERDICT": "This file contains NO verdict, NO rank and NO p-value by design. Singling out "
                      "any one head for a claim requires a HELD-OUT AXIS -- see "
                      "SELECTION_RE_ENTERS_WHEN.",
    }
    # ⛔ CELL-ONLY TOP-LEVEL KEYS, added AFTER the shared dict is built, for the same reason the
    # per-arm extras are: a HEAD family's report must remain BYTE-IDENTICAL to what D34 was written
    # from. A cell family says more because it HAS more to say; it does not change what a head family
    # emits.
    if IS_CELLS:
        out["ARM_GRANULARITY"] = "cell"
        out["CANNOT_DO_FIELD"] = _cannot
        # ⚠ R30-A/S-332: the report used to carry NO provenance key, so a reader could not tell
        # "VOID condition 8 was checked and is free" from "it was never evaluated" -- which is
        # verbatim the false claim R29 caught in PR-CSI-018's own frozen read. The condition is now
        # code AND the artefact witnesses it: every head checked, with its diff and the tolerance
        # actually used, and every head skipped, named.
        out["VOID_8_PROVENANCE"] = {
            "n_heads_declared": len(_per_head_bars),
            "n_checked": len(_prov["checked"]), "n_not_evaluated": len(_prov["skipped"]),
            "heads_not_evaluated": _prov["skipped"],
            "tolerance_used_per_head": _prov["tolerances"],
            "checks": _prov["checked"],
            "WHAT_THIS_IS": "each head's whole-head arm E compared to the prereg's frozen prior "
                            "measurement of the SAME head, codeword and split. A diff above the "
                            "head's DECLARED void_tolerance is a refusal, not a warning. The "
                            "tolerance may not be defaulted by this reader. (R29/S-323, R30-A/S-332)"}
        out["CELL_FAMILY"] = {
            "h_star": pr.get("h_star"), "layers": pr.get("layers"), "band": pr.get("band"),
            "per_cell_dose_predicted": PER_CELL,
            # ⚠ S-311: the BAR SOURCE ARMS are 9-cell arms with dose 2016, not 224. Including them here
            # would make the per-CELL dose check read two doses and print REFUTED on a healthy run.
            "per_cell_dose_observed": sorted({g0[k]["median_prefill_edits"] for k in _cells}),
            "per_cell_dose_verdict": ("CONFIRMED" if sorted(
                {g0[k]["median_prefill_edits"] for k in _cells}) in ([PER_CELL], [float(PER_CELL)])
                else "REFUTED -- the uniformity assumption behind DOSE_UNIT/band_width is WRONG and "
                     "every cell dose expectation in the sprint must be re-derived (S-292)"),
            "cells": {k: sorted(hs[k]) for k in sorted(hs)},
            "DETECTABILITY_PREREGISTERED": (pr.get("DETECTABILITY_PREREGISTERED_PER_HEAD")
                                            or pr.get("DETECTABILITY_PREREGISTERED")),
            # S-300: the PREREGISTERED count first, the weaker one beside it, both named for exactly
            # what they measure so neither can be quoted as the other.
            "n_cells_CLEARING_THE_PREREGISTERED_BAR": sum(
                1 for k in _cells if abs(E[k]) > _bar_for(k)),
            "preregistered_bar": _thr,
            "preregistered_bar_per_head": {str(h): _bars_used[h] for h in _heads_here},
            # S-311: when a bar came from a frozen RULE rather than a frozen NUMBER, the report
            # records the computed value, the arm it came from and the rule's own parameters --
            # S-308's lesson: a report that has a criterion must RECORD it.
            "bars_COMPUTED_FROM_A_FROZEN_RULE": (_bar_computed or None),
            "bar_source_arms_EXCLUDED_FROM_THE_DEPTH_MAP": sorted(_BAR_SOURCE_ARMS) or None,
            "n_cells_judged": len(_cells),
            "cells_clearing_the_preregistered_bar": sorted(
                k for k in _cells if abs(E[k]) > _bar_for(k)),
            "n_cells_with_ci95_excluding_0": sum(1 for k in _cells if (CI[k][1] < 0 or CI[k][0] > 0)),
            # ⚠ R27/S-308: this note used to say "the prereg froze |E| > preregistered_bar" on a
            # MULTI-HEAD family, where preregistered_bar is null by design and the real criterion
            # lives in preregistered_bar_per_head. It pointed a reader at a null.
            "WEAKER_CRITERION_NOTE": (
                "n_cells_with_ci95_excluding_0 is NOT the preregistered criterion. The prereg froze "
                "|E| > %s. A cell can exclude 0 at a small fraction of the bar and with the wrong "
                "sign; on PR-CSI-014 CL_L11 did exactly that (S-299/S-300). ⚠ AND THE CONVERSE, "
                "measured on THIS family (R27/S-308): the bar is 1.96*SE of the NINE-CELL HEAD arm, "
                "whose per-domain spread is much larger than a single cell's, so cells exclude 0 far "
                "below it -- 7 of PR-CSI-015's 24 non-clearing cells do, the smallest at 14%% of the "
                "bar. 'Below the bar' therefore means NOT DETECTABLE AT THE PREREGISTERED "
                "RESOLUTION, and must NOT be read as 'this cell shows no effect'."
                % ("preregistered_bar" if _thr is not None
                   else "that head's own preregistered_bar_per_head entry")),
            "NOTHING_CLEARED_THE_BAR_IS_A_PREREGISTERED_COHERENT_OUTCOME": _detect(
                "COHERENT_OUTCOME_IF_NOTHING_CLEARS_IT", "COHERENT_OUTCOME_IF_NOTHING_CLEARS"),
        }
    n = w4.atomic_write_json(a.out, out)
    print("\n[census] wrote+verified %s (%d bytes)" % (a.out, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
