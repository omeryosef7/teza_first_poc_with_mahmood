"""W4 -- the analyser for the PR-CSI-010 HEAD family. Option 3 of S-196.

WHY THIS FILE EXISTS. S-196 measured that `dcs_csi_subspace_analyze.py` VOIDs every head arm on
conditions a head arm can never satisfy (`rescue_basis_key`, `rescue_norm_match_key` -- always None
for a knockout arm, subspace_analyze.py:752,754). Design 4.2's "no new analyser" premise is false.

WHY OPTION 3 AND NOT THE CHEAPER ONE. Promoting `dcs_csi_rederive_subspace.py` to primary would work
today and would spend the design's CROSS-CHECK: it is the independent path, written to share no code,
and a sprint in which three consecutive reviews each found a real defect should not retire its second
opinion to save a file. Editing `subspace_analyze.py` would put every committed subspace number at
risk of a regression for an experiment that is not a subspace experiment. This file is ADDITIVE:
nothing existing changes, and if the user prefers option 1 or 2 it is simply unused.

WHAT IT SHARES, DELIBERATELY, AND WHAT IT DOES NOT.
  SHARES `dcs_cont_layerpos_map.load_installation` -- the SOLE definition of the endpoint, including
    the concept-free channel filter and the duplicate-key refusal. Re-implementing y_install would
    mean measuring a different thing and calling it the same name.
  SHARES `dcs_csi_rederive_patch.strict_run_dir` -- so "a complete run" means exactly one thing
    across this sprint (DONE.json ok, rows_written == expect_n, row count agrees, exactly one
    candidate or RAISE).
  DOES NOT share the subspace VOID battery, because none of it applies.
  DOES NOT re-implement the rank test's independent path: `dcs_csi_rederive_subspace.py`
    --direction necessity remains the second opinion, and S-196 measured that it RUNS on head arms.

THE UNIT IS THE DOMAIN, EVERYWHERE (rule 3.3). load_installation keys on (domain, family_slot), so
slots are averaged WITHIN a domain first and every statistic below resamples DOMAINS.
"""
import argparse, importlib.util, json, math, os, random, statistics, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


lpm = _load("lpm", os.path.join(REPO, "scripts", "dcs_cont_layerpos_map.py"))
rederive = _load("rederive", os.path.join(REPO, "scripts", "dcs_csi_rederive_patch.py"))


def atomic_write_json(path, obj):
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_atomic_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=False); fh.write("\n")
            fh.flush(); os.fsync(fh.fileno())
        if os.path.getsize(tmp) == 0:
            raise OSError("0 bytes after flush+fsync")
        with open(tmp, "r", encoding="utf-8") as fh:
            json.load(fh)
        try:
            mode = os.stat(path).st_mode & 0o7777
        except OSError:
            mode = 0o644
        os.chmod(tmp, mode); os.replace(tmp, path)
        try:
            dfd = os.open(d, os.O_RDONLY)
            try: os.fsync(dfd)
            finally: os.close(dfd)
        except OSError:
            pass
    except Exception as e:
        try: nb = os.path.getsize(tmp)
        except OSError: nb = -1
        try: os.unlink(tmp)
        except OSError: pass
        raise OSError("atomic_write_json FAILED for %s -- %d bytes reached temp; destination "
                      "UNCHANGED. Cause: %r" % (path, nb, e)) from e
    return os.path.getsize(path)


def by_domain(run_dir):
    """(domain -> mean y_install over that domain's slots), plus the per-domain SLOT SET.

    The slot set is returned because comparing domain SETS is not enough (R15-3): if two arms bind
    a different number of slots for the same domain, both pass a set comparison while their domain
    means average DIFFERENT ROWS, and the paired delta then contrasts slightly different
    populations inside a domain that looks matched. Measured: the real 670-row arms are uniformly
    10 slots per domain, so this is latent rather than live -- but it is latent only because
    `strict_run_dir` enforces `expect_n`, and a guard that depends on another guard should say so.
    """
    inst, n_seen, kinds = lpm.load_installation(run_dir)
    per, slots = {}, {}
    for (dom, slot), p in inst.items():
        per.setdefault(dom, []).append(float(p))
        slots.setdefault(dom, set()).add(slot)
    return ({d: statistics.fmean(v) for d, v in per.items()}, slots, n_seen, kinds)


def liveness(run_dir):
    """GATE 0 reads the ROWS, not a summary: a summary can be written by a run that edited nothing."""
    pre, dec, viol, rows, qrows = [], 0, {}, 0, []
    with open(os.path.join(run_dir, "results.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("query_kind") != "semantic_one_word" or r.get("cell") != "C":
                continue
            rows += 1
            pre.append(int(r.get("hook_n_prefill_edits") or 0))
            dec += int(r.get("hook_n_decode_edits") or 0)
            qrows.append(int(r.get("hook_n_query_rows_edited") or 0))
            v = r.get("hook_liveness_violations")
            if v:
                viol[str(v)] = viol.get(str(v), 0) + 1
    return {"n_rows": rows, "total_prefill_edits": sum(pre),
            "median_prefill_edits": (statistics.median(pre) if pre else 0),
            "min_prefill_edits": (min(pre) if pre else 0),
            "total_decode_edits": dec, "violations": viol,
            "median_query_rows_edited": (statistics.median(qrows) if qrows else 0)}


def boot_mean(vals, B, rng):
    n = len(vals)
    return [statistics.fmean([vals[rng.randrange(n)] for _ in range(n)]) for _ in range(B)]


def pct(xs, q):
    ys = sorted(xs)
    k = (len(ys) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(ys) - 1)
    return ys[lo] + (ys[hi] - ys[lo]) * (k - lo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--tag-prefix", required=True)
    ap.add_argument("--split", required=True, choices=("train", "validation"))
    ap.add_argument("--expect-n", type=int, required=True)
    ap.add_argument("--allow-short", type=int, default=0)
    ap.add_argument("--require-slurm-job", default=None)
    ap.add_argument("--B", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20260921)
    ap.add_argument("--ci", type=float, default=0.95)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    pr = json.load(open(a.prereg))
    hs = pr["head_sets"]
    # The prefix comes from the preregistration; PR-CSI-010 predates the field, so absence
    # defaults to HD_RAND -- and the default is VERIFIED to bind, never assumed (S-168).
    # S-246. A CENSUS preregistration declares NO_RANK_TEST and carries no candidate, control family
    # or floor. Without this guard the rank tooling dies on a bare KeyError or reports "control_prefix
    # matches no head set" -- both fail-closed, but both name the SYMPTOM rather than the cause and
    # would send a reader hunting for a missing field. Refuse by NAME instead.
    if pr.get("NO_RANK_TEST"):
        sys.exit("REFUSING: prereg %r declares NO_RANK_TEST -- it is a CENSUS (no candidate, no control "
                 "family, no floor) and this tool is a RANK-TEST tool. Use the census reader. (S-246)"
                 % pr["id"])
    # ⛔ S-252. W4 IS HARD-CODED TO THIS FAMILY SHAPE, and saying so is the fix rather than pretending
    # otherwise. It names HD_BASE / HD_KO / HD_TOPK / HD_BOTK throughout, and its REPORTABLE_AS speaks
    # of "K head INDICES ... carry at least half of the A1 knockout's effect" -- language about a
    # K-head SUBSET. PR-CSI-013's candidate is BT_SINGLE, a SINGLE head, with base arms BT_BASE /
    # BT_KO. Making the codeword a parameter (above) was necessary and is NOT sufficient: a family
    # with different arm names cannot be read here at all, and one with K = 1 would be described by
    # reporting language written for a subset. Refuse by NAME instead of emitting a wrong artefact.
    _need = [k for k in ("HD_TOPK", "HD_BOTK") if k not in pr["head_sets"]]
    if _need:
        sys.exit("REFUSING: prereg %r does not declare %s in head_sets. W4 is hard-coded to the "
                 "HD_BASE/HD_KO/HD_TOPK/HD_BOTK family shape and its reporting language describes a "
                 "K-head SUBSET, so it cannot read a differently-shaped family (e.g. PR-CSI-013, "
                 "whose candidate BT_SINGLE is ONE head). That family needs its own reader. (S-252)"
                 % (pr["id"], _need))
    if pr.get("base_arms") and list(pr["base_arms"]) != ["HD_BASE", "HD_KO"]:
        sys.exit("REFUSING: prereg %r declares base_arms %r; W4 reads HD_BASE and HD_KO only. (S-252)"
                 % (pr["id"], pr["base_arms"]))
    cprefix = pr.get("control_prefix", "HD_RAND")
    controls = sorted(k for k in hs if k.startswith(cprefix))
    if not controls:
        sys.exit("REFUSING: control_prefix %r matches no head set in the prereg" % cprefix)
    arms = ["HD_BASE", "HD_KO", "HD_TOPK", "HD_BOTK"] + controls
    jobs = a.require_slurm_job.split(",") if a.require_slurm_job else None

    # VOID 6, CHECKED HERE AND NOT ASSUMED (S-120(e)): the family must be exactly the prereg's.
    if len(controls) != pr["n_controls"]:
        sys.exit("REFUSING: control family is %d arms, the prereg says %d"
                 % (len(controls), pr["n_controls"]))
    if "HD_BOTK" in controls or "HD_TOPK" in controls:
        sys.exit("REFUSING: the comparator or the candidate entered the control family (VOID 6)")

    dirs, per, live, slots = {}, {}, {}, {}
    for arm in arms:
        d = rederive.strict_run_dir("%s_%s" % (a.tag_prefix, arm), a.expect_n,
                                    row_file="results.jsonl", allow_short=a.allow_short,
                                    require_slurm_jobs=jobs)
        dirs[arm] = d
        per[arm], slots[arm], n_seen, kinds = by_domain(d)
        live[arm] = liveness(d)

    doms = sorted(set.intersection(*(set(v) for v in per.values())))
    print("[head] SIZE arms = %d | domains common to ALL arms = %d | expect-n = %d | split = %s"
          % (len(arms), len(doms), a.expect_n, a.split))
    if not doms:
        sys.exit("VACUOUS: no domain is present in every arm")
    ragged = {arm: sorted(set(per[arm]) - set(doms)) for arm in arms if set(per[arm]) - set(doms)}
    if ragged:
        sys.exit("REFUSING: arms disagree on their domain sets, so a paired contrast would silently "
                 "compare different populations: %s" % {k: v[:4] for k, v in list(ragged.items())[:4]})

    # R15-3: the SLOT SETS must match per domain, not merely the domain sets.
    ref = slots[arms[0]]
    for arm in arms[1:]:
        bad = {d for d in doms if slots[arm].get(d) != ref.get(d)}
        if bad:
            sys.exit("REFUSING: arm %s binds different SLOTS from %s in %d domain(s) (e.g. %s) -- "
                     "the domain means would average different rows and the paired delta would "
                     "contrast different populations inside a matched-looking domain"
                     % (arm, arms[0], len(bad), sorted(bad)[:3]))

    # R15-9a: the DOMAIN count is the statistical unit and must equal the preregistered population.
    # strict_run_dir enforces the ROW count; nothing enforced the DOMAIN count, so a changed
    # exclusion file could have delivered 670 rows over the wrong number of domains, silently.
    # The count binds when this run CLAIMS TO BE THE PREREGISTERED ONE, which is exactly when
    # --expect-n equals the preregistered row count for the split. Deriving the condition from
    # expect_n rather than adding an override flag matters: an override could be passed to a real
    # run to silence the guard, whereas expect_n is already pinned by the arms themselves
    # (strict_run_dir admits no arm whose rows_written differs). An off-protocol row count is
    # announced loudly instead of being quietly treated as compliant.
    want_dom = pr["population"]["%s_domains" % a.split]
    want_n = pr["population"]["%s_expect_n" % a.split]
    on_protocol = (a.expect_n == want_n)
    if on_protocol:
        if len(doms) != want_dom:
            sys.exit("REFUSING: %d domains analysed but PR-CSI-010 preregisters %d for %s"
                     % (len(doms), want_dom, a.split))
    else:
        print("[head] ⛔ OFF-PROTOCOL: --expect-n %d != the preregistered %d for %s, so the "
              "domain-count check does NOT apply and THIS IS NOT A PREREGISTERED ANALYSIS."
              % (a.expect_n, want_n, a.split))

    # R15-9b: VOID condition 7 AT READ TIME. pr010_gate0 checked the AXIS and said in as many words
    # that "each arm's population must be re-checked" on read. This is that re-check.
    test_doms = set(pr["population"]["test_domains"])
    leaked = sorted(set(doms) & test_doms)
    if leaked:
        sys.exit("REFUSING (VOID 7): TEST domain(s) present in the analysed population: %s" % leaked)
    if on_protocol:
        print("[head] population OK: %d domains == preregistered %d | no TEST domain present"
              % (len(doms), want_dom))

    # ---- GATE 0: liveness -----------------------------------------------------------------
    g0 = {}
    for arm in arms:
        L = live[arm]
        if arm == "HD_BASE":
            ok = (L["total_prefill_edits"] == 0 and L["total_decode_edits"] == 0)
            why = "the BASE arm must be UNINTERVENED"
        else:
            ok = (L["total_prefill_edits"] > 0 and L["total_decode_edits"] == 0 and not L["violations"])
            why = "an intervened arm must edit in prefill, never in decode, with no violations"
        g0[arm] = {"pass": bool(ok), "why": why, **L}
    gate0 = all(v["pass"] for v in g0.values())

    # THE REALISED-DOSE IDENTITY (S-175, confirmed on live data in S-193): the all-head arm writes
    # ONE broadcast row per (row, layer); a K-head arm expands and writes K explicit rows. So a
    # K-head arm records K TIMES MORE, never K/32 of it.
    K = pr["K"]
    mk = g0["HD_KO"]["median_prefill_edits"] or 0
    dose = {}
    for arm in ["HD_TOPK", "HD_BOTK"] + controls:
        m = g0[arm]["median_prefill_edits"] or 0
        r = (m / mk) if mk else None
        dose[arm] = {"median": m, "ratio_to_all_head": r,
                     "expected": K, "pass": bool(r is not None and abs(r - K) < 1e-6)}
    dose_ok = all(v["pass"] for v in dose.values())

    # ---- the contrasts, domain unit -------------------------------------------------------
    base = per["HD_BASE"]
    rng = random.Random(a.seed)
    lo_q, hi_q = (1 - a.ci) / 2, 1 - (1 - a.ci) / 2
    E, CI, deltas = {}, {}, {}
    for arm in arms:
        if arm == "HD_BASE":
            continue
        dv = [per[arm][d] - base[d] for d in doms]
        deltas[arm] = dv
        E[arm] = statistics.fmean(dv)
        bs = boot_mean(dv, a.B, random.Random(a.seed))
        CI[arm] = [pct(bs, lo_q), pct(bs, hi_q)]

    # ---- GATE 1: the positive control -----------------------------------------------------
    gate1 = bool(E["HD_KO"] < 0 and CI["HD_KO"][1] < 0)

    # ---- the rank test: ONE candidate against the 20 controls -----------------------------
    fam = controls + ["HD_TOPK"]
    order = sorted(fam, key=lambda x: E[x])          # more NEGATIVE = stronger (necessity)
    rank = order.index("HD_TOPK") + 1
    n_fam = len(fam)
    p_rank = rank / float(n_fam)
    floor = 1.0 / float(n_fam)

    # ---- F, with a degenerate-denominator refusal -----------------------------------------
    F = F_ci = None
    if gate1 and abs(E["HD_KO"]) > 1e-9:
        F = E["HD_TOPK"] / E["HD_KO"]
        r2 = random.Random(a.seed + 1)
        fb = []
        for _ in range(a.B):
            idx = [r2.randrange(len(doms)) for _ in range(len(doms))]
            num = statistics.fmean([deltas["HD_TOPK"][i] for i in idx])
            den = statistics.fmean([deltas["HD_KO"][i] for i in idx])
            if abs(den) > 1e-9:
                fb.append(num / den)
        F_ci = [pct(fb, lo_q), pct(fb, hi_q)] if len(fb) > a.B // 2 else None

    # ---- the verdict, read in the design's order ------------------------------------------
    # ⛔ THE VERDICT TABLE IS FOR VALIDATION ONLY. Design 6 reads "Then, on **VALIDATION**:" before
    # the four verdicts, and design 5.3 says a TRAIN rank is "selection-contaminated, not an
    # inferential statement" -- the heads were CHOSEN on TRAIN activations, so TRAIN rank 1 is partly
    # a restatement of the selection. W4 applied the table regardless of split and wrote
    # "WE FOUND (part of) THE WRITER" into a TRAIN artifact, which is the overclaim S-205 was about,
    # one level worse: not a headline missing its scope but a headline that does not exist for this
    # split. A TRAIN run now reports the gates and the numbers and NO verdict.
    if a.split == "train":
        verdict = ("DESCRIPTIVE -- NO VERDICT IS DEFINED FOR TRAIN. Design 6 applies the verdict "
                   "table to VALIDATION only, and this rank is SELECTION-CONTAMINATED by "
                   "construction (design 5.3): the head set was chosen using these activations. "
                   "GATE 0 and GATE 1 are still adjudicated below and still mean what they say.")
    elif not gate0 or not dose_ok:
        verdict = "VOID -- GATE 0 (liveness or the realised-dose identity) failed; this is not a result"
    elif not gate1:
        verdict = ("CANNOT ANSWER -- GATE 1 failed: the instrument did not move the endpoint "
                   "(E(HD_KO) not clearly negative). Feasibility is reported; THE CANDIDATE IS NOT.")
    elif rank == 1 and F is not None and F >= 0.50 and F_ci and not (F_ci[0] <= 0 <= F_ci[1]):
        # S-259, per R22-5: W4's sign guarantee is IMPLICIT and this records why it holds, plus an
        # assertion that cannot fire under the current logic and WILL fire if either half is ever
        # weakened. GATE 1 (reached above) forces E(HD_KO) < 0, and F = E(HD_TOPK)/E(HD_KO) >= 0.50
        # with a negative denominator forces E(HD_TOPK) < 0. So W4 does NOT have R22's defect -- but
        # it is protected by an IMPLICATION across two separate conditions, not by a clause, and an
        # implication is only as durable as both of its halves.
        assert E["HD_TOPK"] < 0 and E["HD_KO"] < 0, (
            "W4 INVARIANT BROKEN: a positive verdict requires both effects negative "
            "(E(HD_TOPK)=%r, E(HD_KO)=%r). GATE 1 or the F threshold has been weakened." % (
                E["HD_TOPK"], E["HD_KO"]))
        verdict = "WE FOUND (part of) THE WRITER"
    elif rank == 1 and F is not None and 0 < F < 0.50:
        verdict = "PARTIALLY LOCALISED"
    elif p_rank > 0.05:
        verdict = "IT IS DISTRIBUTED (candidate sits inside the control family)"
    else:
        verdict = "CANNOT ANSWER -- no preregistered branch matched; reported as such rather than forced"

    # ⛔ A BARE VERDICT STRING IS AN OVERCLAIM WAITING TO BE QUOTED.
    # Design 6 does not merely name the verdicts, it fixes the WORDS a positive one may be reported
    # in -- "8 head indices, applied across blocks 6-14 on the query-codeword row ... for leg (i) of
    # the circuit only". W4 emitted "WE FOUND (part of) THE WRITER" and nothing else, so the artifact
    # invited a later reader to quote the headline without the scope that makes it true. The scope is
    # not decoration: design 10 states that --knockout-heads TIES A HEAD INDEX ACROSS 6-14, so no arm
    # in this family can address a single (layer, head) cell -- even though the SCREEN ranks cells and
    # its top cell was L14 h19. The intervention is coarser than the attribution, by construction.
    # S-252. THE CODEWORD IS READ FROM THE PREREG AND NOT HARD-CODED, because this is the field a
    # CLAIM GETS QUOTED FROM. It said "for basket" unconditionally, so reading a BUTTON family with
    # this tool would have emitted a button result whose own reporting language attributed it to
    # basket -- not a numerical error, a PROVENANCE error written into the artefact that the claim is
    # then taken from. Defaults to "basket" because PR-010/011 predate the field, and the default is
    # verified to bind (S-168) by the byte-identity regression in S-252.
    cw = pr.get("codeword", "basket")
    n_cand = len(pr["head_sets"]["HD_TOPK"])
    REPORTABLE_AS = {
        "WE FOUND (part of) THE WRITER":
            ("%d head INDICES, applied across blocks 6-14 on the query-codeword row, carry at least "
             "half of the A1 knockout's effect on installation for %s -- for leg (i) of the "
             "circuit ONLY. NOT a claim about any single (layer, head) cell." % (n_cand, cw)),
        "PARTIALLY LOCALISED":
            ("those %d head indices carry a real but MINORITY share of the A1 knockout's effect. "
             "NOT 'the writer', and not a claim about any single (layer, head) cell." % n_cand),
        "IT IS DISTRIBUTED (candidate sits inside the control family)":
            ("no %d-head subset is privileged: the demo->codeword-row write is spread across heads. " % n_cand +
             "Plan section 19 Gate C then says KEEP THE REPRESENTATION RESULT AND DO NOT INVENT A "
             "CIRCUIT."),
    }
    out = {
        "schema": "dcs_csi_head_analyze/1",
        "REPORTABLE_AS": REPORTABLE_AS.get(verdict,
                         "no preregistered reporting language applies to this verdict; report the "
                         "gates and the refusal, not a headline"),
        "CANNOT_DO": [
            "cannot test leg (ii) (rel-11 -> rel-6): no scope exists for it",
            "cannot resolve WHICH LAYER a head acts at -- --knockout-heads ties the index across 6-14",
            "cannot test blocks 0-5 or 15-18 causally without first establishing an all-head ceiling there",
            ("does NOT do cross-codeword transfer away from %s; a transfer test is a SEPARATE "
             "preregistered family with its own verdict" % cw) if cw != "basket" else
            ("does NOT do cross-codeword transfer to button; that is only meaningful after a POSITIVE "
             "basket head result, and is the NEXT design"),
        ],
        "prereg": a.prereg, "prereg_id": pr["id"], "tag_prefix": a.tag_prefix, "split": a.split,
        "n_domains": len(doms), "expect_n": a.expect_n,
        "ON_PROTOCOL": on_protocol,
        "protocol_note": (None if on_protocol else
                          "OFF-PROTOCOL: expect_n != the preregistered row count, so "
                          "the domain-count check did not apply; NOT a preregistered analysis"), "B": a.B, "seed": a.seed, "ci": a.ci,
        "run_dirs": {k: os.path.basename(v) for k, v in dirs.items()},
        "GATE_0_liveness": {"pass": gate0, "per_arm": g0},
        "REALISED_DOSE": {"pass": dose_ok, "expected_ratio": K,
                          "note": "K x the all-head arm (S-175); NEVER K/32", "per_arm": dose},
        "GATE_1_positive_control": {"pass": gate1, "E_HD_KO": E["HD_KO"], "ci95": CI["HD_KO"]},
        "E": {k: round(v, 8) for k, v in E.items()},
        "ci95": {k: [round(v[0], 8), round(v[1], 8)] for k, v in CI.items()},
        # ⛔ THE p IS STORED EXACTLY, NOT ROUNDED, AND SO IS THE FLOOR. round(1/21, 6) = 0.047619
        # is BELOW the true 0.047619047..., so rounding moves a p-value in the direction that
        # FLATTERS the result and makes p == floor compare FALSE at rank 1. This is the same
        # defect gate 0 caught in the prereg freezer (S-190) -- I wrote it a second time, in the
        # file that reports the p. `p_display` exists for prose and is never compared.
        "rank_test": {"candidate": "HD_TOPK", "rank": rank, "of": n_fam,
                      "p": p_rank, "p_display": "%.6f" % p_rank, "attainable_floor": floor,
                      "floor_note": ("the p is reported WITH its floor, always. rank 1 of %d gives "
                                     "p = the floor = %.6f; rank 2 gives %.6f and does NOT clear "
                                     "alpha = 0.05" % (n_fam, floor, 2.0 / n_fam)),
                      "order_most_negative_first": order},
        "F": None if F is None else round(F, 8),
        "F_ci95": None if F_ci is None else [round(F_ci[0], 8), round(F_ci[1], 8)],
        "VERDICT": verdict,
        "comparator_HD_BOTK": {"E": round(E["HD_BOTK"], 8), "ci95": CI["HD_BOTK"],
                               "note": "the COMPARATOR; it is NOT in the control family (VOID 6)"},
        "TRAIN_CAVEAT": ("selection-contaminated, not an inferential statement"
                         if a.split == "train" else None),
        "INDEPENDENT_PATH": ("dcs_csi_rederive_subspace.py --direction necessity shares no code with "
                             "this file and must be run as the second opinion (S-196 measured that "
                             "it RUNS on head arms)"),
    }
    n = atomic_write_json(a.out, out)
    print("[head] wrote+verified %s (%d bytes)" % (a.out, n))
    print("[head] GATE 0 %s | dose %s | GATE 1 %s"
          % ("PASS" if gate0 else "FAIL", "PASS" if dose_ok else "FAIL", "PASS" if gate1 else "FAIL"))
    print("[head] E(HD_KO) = %.6f ci95 %s" % (E["HD_KO"], [round(x, 6) for x in CI["HD_KO"]]))
    print("[head] E(HD_TOPK) = %.6f ci95 %s" % (E["HD_TOPK"], [round(x, 6) for x in CI["HD_TOPK"]]))
    print("[head] rank %d of %d | p = %.6f | FLOOR = %.6f" % (rank, n_fam, p_rank, floor))
    print("[head] F = %s ci95 %s" % (F, F_ci))
    if a.split == "train":
        print("[head] TRAIN IS DESCRIPTIVE: this rank is SELECTION-CONTAMINATED, not an "
              "inferential statement.")
    print("[head] VERDICT: %s" % verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
