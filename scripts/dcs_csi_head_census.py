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
import argparse, collections, importlib.util, json, os, random, statistics, sys

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
        print("[census] CELL family: per-cell dose %d = %d/%d layers -- PREDICTED, NOT MEASURED. "
              "THIS FAMILY'S ARMS VALIDATE THAT ARITHMETIC." % (PER_CELL, DOSE_UNIT, NLAYERS))
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
            got = None
        elif IS_CELLS and arm != ko_arm:
            # IDENTITY FROM knockout_cells ONLY. This arm's knockout_heads is EMPTY, which
            # recorded_heads() maps to "ALL" -- so the head-level check would certify every 1-cell arm
            # as the all-32 knockout (S-292).
            got = recorded_cells(dirs[arm])
        else:
            got = recorded_heads(dirs[arm])
        if arm == base_arm:
            ok_id, why = (got in (None, "ALL", []) or True), "not intervened"
        elif arm == ko_arm:
            ok_id = (got == "ALL")
            why = "omitted flag == all 32" if ok_id else "expected ALL, recorded %r" % (got,)
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
            g0[arm]["dose_expectation_status"] = (
                "PREDICTED (DOSE_UNIT/band_width, untested uniformity assumption -- S-292)"
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
        _thr = (pr.get("DETECTABILITY_PREREGISTERED") or {}).get("min_abs_E_for_ci95_to_exclude_0")
        _cells = sorted((k for k in hs), key=lambda x: sorted(hs[x])[0][0])
        print("\n[census] DEPTH MAP -- head %s, one cell per layer, in LAYER order. NO RANK, NO p."
              % pr.get("h_star"))
        if _thr:
            print("         preregistered detectability bar: |E| > %.6f (S-294). "
                  "'-' = ci95 includes 0." % _thr)
        _cleared = []
        for k in _cells:
            L, h = sorted(hs[k])[0]
            excl0 = (CI[k][1] < 0) or (CI[k][0] > 0)
            if excl0:
                _cleared.append((k, L, E[k]))
            print("   L%-3d %-9s E = %+.6f  ci95 [%+.6f, %+.6f]  %s"
                  % (L, k, E[k], CI[k][0], CI[k][1], "CLEARS 0" if excl0 else "-"))
        print("\n[census] %d of %d cells have a ci95 excluding 0." % (len(_cleared), len(_cells)))
        if not _cleared:
            print("         NOTHING CLEARS THE BAR. This outcome was PREREGISTERED AS COHERENT "
                  "before any arm ran:")
            print("         " + (pr.get("DETECTABILITY_PREREGISTERED") or {}).get(
                "COHERENT_OUTCOME_IF_NOTHING_CLEARS_IT", "(the prereg records it)"))
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
        out["CELL_FAMILY"] = {
            "h_star": pr.get("h_star"), "layers": pr.get("layers"), "band": pr.get("band"),
            "per_cell_dose_predicted": PER_CELL,
            "per_cell_dose_observed": sorted({g0[k]["median_prefill_edits"] for k in hs}),
            "per_cell_dose_verdict": ("CONFIRMED" if sorted(
                {g0[k]["median_prefill_edits"] for k in hs}) in ([PER_CELL], [float(PER_CELL)])
                else "REFUTED -- the uniformity assumption behind DOSE_UNIT/band_width is WRONG and "
                     "every cell dose expectation in the sprint must be re-derived (S-292)"),
            "cells": {k: sorted(hs[k]) for k in sorted(hs)},
            "DETECTABILITY_PREREGISTERED": pr.get("DETECTABILITY_PREREGISTERED"),
            "n_cells_with_ci95_excluding_0": sum(1 for k in hs if (CI[k][1] < 0 or CI[k][0] > 0)),
            "NOTHING_CLEARED_THE_BAR_IS_A_PREREGISTERED_COHERENT_OUTCOME": (
                (pr.get("DETECTABILITY_PREREGISTERED") or {}).get(
                    "COHERENT_OUTCOME_IF_NOTHING_CLEARS_IT")),
        }
    n = w4.atomic_write_json(a.out, out)
    print("\n[census] wrote+verified %s (%d bytes)" % (a.out, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
