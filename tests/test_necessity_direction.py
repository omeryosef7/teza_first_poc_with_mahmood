"""S-110 / PR-CSI-003: the Phase-2 NECESSITY arm's sign conventions are INVERTED, and both analysis
paths must read them that way WITHOUT moving the sufficiency path and WITHOUT negating any reported
number.

The defect class these lock down. Every arm in the record tests SUFFICIENCY -- under a live
knockout, ADD BACK the clean state's component along the installation axis -- so the reference arm
is KO and "the candidate did something" means a LARGER POSITIVE difference. The necessity arm
(`--rescue-donor ko`, built in S-110) starts from a CLEAN forward and REMOVES the installed
component, so its reference arm is BASE and "the candidate did something" means a LARGER NEGATIVE
difference. Read with the old orientation, a necessity run produces a complete, VOID-free contrast
table in which every decision is inverted and every number still looks plausible -- the worst
possible failure, because nothing in the artifact says it happened.

Four separate hazards, each with its own test and each asserted on BOTH halves:

  * THE SUFFICIENCY PATH MUST NOT MOVE. 164 committed results were produced by the unflagged path.
    `test_sufficiency_headline_is_unmoved` re-derives the committed
    `reports/DCS_CSI_SUBSPACE_button_train_rank1.json` headline THROUGH the patched code -- and the
    independent path's `reports/DCS_CSI_REDERIVE_button_train_L20.json` alongside it. This is the
    most important test in the file.
  * THE INVERSION MUST ACTUALLY INVERT, not be silently ignored. The same synthetic numbers are run
    under both directions: a candidate that drops installation ranks FIRST under necessity and LAST
    under sufficiency. A `--direction` flag that were accepted and then dropped on the floor would
    pass a necessity-only assertion and fail this one.
  * NUMBERS KEEP THEIR NATURAL SIGN. Nothing is multiplied by -1 to reuse the old comparisons: a
    removal that drops installation must appear in the artifact as a NEGATIVE number, because a
    reader who sees "+0.09" against an arm labelled "removal" will misread it, and the verdict
    string must not carry the sufficiency wording ("recover", "not above them") into a removal.
  * A GATE THAT DISAPPEARS IS WORSE THAN ONE THAT FAILS. There is no inert identity control for
    this direction (PR-CSI-003 required_gates.no_inert_identity_control_exists: the natural one IS
    the identity and is refused by the arm's own precondition), so the gate is SKIPPED with its
    reason written into the artifact -- including on the VOID early-return path, which is the
    artifact most likely to be read once and never re-run. And the capability gate must answer
    CANNOT ANSWER, citing plan section 15, rather than a negative, exactly as the sufficiency
    branch does.
"""
import importlib.util
import json
import math
import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORE_DIR = os.path.join(REPO, "outputs", "boombness", "score_behavior")

# The committed headline this file refuses to let move (reports/DCS_CSI_SUBSPACE_button_train_rank1
# .json and reports/DCS_CSI_REDERIVE_button_train_L20.json, both produced by the unflagged path).
COMMITTED = {
    "manipulation": -0.20558,
    "positive_control": 0.06955,
    "candidate": 0.00040,
    "rank": 4, "of": 11,
    "n_keys_common": 666, "n_domains": 67,
    "verdict_tail": "It is INSIDE the controls, not above them.",
}
COMMITTED_ARMS = ("BASE,KO,KO_SELF,KO_FULL,KO_AXIS,KO_ORTH,KO_SHUF0,KO_SHUF1,KO_SHUF2,KO_SHUF3,"
                  "KO_RAND0,KO_RAND1,KO_RAND2,KO_RAND3,KO_RAND4,KO_RAND5")
COMMITTED_JOBS = "896679,896771"


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, relpath))
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture()
def analyze():
    return _load("csi_analyze_dirtest", "scripts/dcs_csi_subspace_analyze.py")


@pytest.fixture()
def indep():
    return _load("csi_rederive_subspace_dirtest", "scripts/dcs_csi_rederive_subspace.py")


def _run(mod, argv):
    """Invoke a script's main() as the CLI would, and hand back its parsed artifact."""
    old = sys.argv
    sys.argv = ["prog"] + [str(x) for x in argv]
    try:
        rc = mod.main()
    finally:
        sys.argv = old
    outp = argv[argv.index("--out") + 1]
    with open(outp, encoding="utf-8") as fh:
        return rc, json.load(fh)


# ============================================================ half 1: the record must not move
def _committed_available():
    if not os.path.isdir(SCORE_DIR):
        return False
    return os.path.isdir(os.path.join(SCORE_DIR,
                                      "csi1_button_train_KO_AXIS_20260915_195425_1707119"))


@pytest.mark.skipif(not _committed_available(),
                    reason="the score_behavior output tree for the committed button-TRAIN L20 arms "
                           "is not present on this host; nothing to re-derive")
def test_sufficiency_headline_is_unmoved(analyze, tmp_path):
    """THE regression, and the most important test here: the UNFLAGGED path reproduces the committed
    button/TRAIN rank-1 headline exactly.

    164 committed results were produced before `--direction` existed and must not move by a digit.
    Both halves: the numbers are identical AND the verdict is still the sufficiency verdict with its
    sufficiency wording, so the direction machinery cannot have leaked into the default path. The
    bootstrap n is reduced because every asserted quantity here is a point estimate or a rank, none
    of which depends on the bootstrap draw count.
    """
    outp = str(tmp_path / "suff.json")
    rc, got = _run(analyze, ["--codeword", "button", "--tag-prefix", "csi1_button_train",
                             "--expect-n", 670, "--arms", COMMITTED_ARMS, "--split", "train",
                             "--require-rescue-layer", 20, "--require-slurm-job", COMMITTED_JOBS,
                             "--allow-short", 3, "--n-boot", 300, "--out", outp])
    assert rc == 0, got.get("VOID")
    assert got["VOID"] == []
    C = got["contrasts"]
    assert C["manipulation_ko_minus_base"]["point"] == COMMITTED["manipulation"]
    assert C["positive_control_full_minus_ko"]["point"] == COMMITTED["positive_control"]
    assert C["candidate_minus_ko"]["point"] == COMMITTED["candidate"]
    assert got["n_keys_common"] == COMMITTED["n_keys_common"]
    assert got["n_domains"] == COMMITTED["n_domains"]
    dist = got["control_recovery_distribution"]
    assert dist["candidate_rank_among_controls"] == COMMITTED["rank"]
    assert dist["n_controls"] + 1 == COMMITTED["of"]
    assert got["gates"] == {"manipulation_check": True, "identity_check": True,
                            "instrument_capable": True}
    # ...and the other half: still the sufficiency verdict, in the sufficiency's own words.
    assert got["VERDICT"].endswith(COMMITTED["verdict_tail"])
    assert "ranks 4 of 11" in got["VERDICT"]
    assert got["direction"] == "sufficiency"
    assert got["reference_arm"] == "KO"
    # The identity gate is EVALUATED in this direction, so nothing may be recorded as skipped.
    assert got["gates_skipped"] == {}
    # The recovery fraction still reaches the real estimator (a positive denominator), i.e. the
    # sign-aware check added for necessity did not start refusing the sufficiency case.
    assert got["recovery_fraction_candidate_of_full"]["status"] == "ok"
    assert got["recovery_fraction_candidate_of_full"]["denominator_point"] == 0.06955


@pytest.mark.skipif(not _committed_available(),
                    reason="the score_behavior output tree for the committed button-TRAIN L20 arms "
                           "is not present on this host; nothing to re-derive")
def test_sufficiency_headline_is_unmoved_in_the_independent_path(indep, tmp_path):
    """The same guarantee for the path that deliberately shares no code: the committed
    `DCS_CSI_REDERIVE_button_train_L20.json` ranks (4 of 11 pooled, 3 of 7 random, 2 of 5 shuffled)
    must survive the direction flag being added to this file too."""
    outp = str(tmp_path / "suff_indep.json")
    rc, got = _run(indep, ["--tag-prefix", "csi1_button_train", "--split", "train",
                           "--expect-n", 670, "--allow-short", 3,
                           "--controls", "KO_SHUF0,KO_SHUF1,KO_SHUF2,KO_SHUF3,KO_RAND0,KO_RAND1,"
                                         "KO_RAND2,KO_RAND3,KO_RAND4,KO_RAND5",
                           "--require-rescue-layer", 20, "--require-slurm-job", COMMITTED_JOBS,
                           "--out", outp])
    assert rc == 0
    assert got["direction"] == "sufficiency" and got["reference_arm"] == "KO"
    assert got["candidate_minus_ko"] == COMMITTED["candidate"]
    assert got["gates"]["manipulation_ko_minus_base"]["point"] == COMMITTED["manipulation"]
    assert got["gates"]["positive_control_full_minus_ko"]["point"] == COMMITTED["positive_control"]
    assert got["instrument_capable"] is True
    assert [(v["rank"], v["of"], v["verdict"]) for v in got["ranks"].values()] == [
        (4, 11, "DOES NOT PASS"), (3, 7, "DOES NOT PASS"), (2, 5, "DOES NOT PASS")]


# ==================================================== half 2: a synthetic necessity run, built here
# Eight REAL train domains, so no split manifest has to be monkeypatched in either path (the
# independent path reads the manifest off disk itself and cannot be diverged from -- S-085).
DOMS = ["apiary_unit", "bar_cellar", "battery_assembly", "blood_bank",
        "bus_garage", "cable_works", "campsite_park", "care_home_store"]
SLOTS = ["slot0", "slot1"]
N_ROWS = len(DOMS) * len(SLOTS)

# Arm -> the level its y_install sits at. NEC_BASE is the CLEAN ceiling and the reference arm;
# NEC_KO is the knockout floor; KO_NEC_FULL removes the whole state; the candidate removes the
# rank-1 component and is, by construction, the LARGEST DROP in the family. Every control sits
# within +-0.004 of NEC_BASE, which is the realistic shape (S-050): the family straddles zero.
NEC_LEVELS = {
    "NEC_BASE": 0.600,          # reference / ceiling
    "NEC_KO": 0.400,            # floor -> manipulation = -0.200
    "KO_NEC_FULL": 0.500,       # whole-state removal -> -0.100, clearly negative
    "KO_NEC_AXIS": 0.590,       # candidate                -> -0.010  (strongest drop)
    "KO_NEC_ORTH": 0.596,       # norm-matched comparator   -> -0.004
    "KO_NEC_SHUF0": 0.598,      # -0.002
    "KO_NEC_SHUF1": 0.600,      #  0.000
    "KO_NEC_SHUF2": 0.602,      # +0.002
    "KO_NEC_SHUF3": 0.604,      # +0.004
    "KO_NEC_RAND0": 0.597,      # -0.003
    "KO_NEC_RAND1": 0.599,      # -0.001
    "KO_NEC_RAND2": 0.601,      # +0.001
    "KO_NEC_RAND3": 0.603,      # +0.003
}
NEC_CONTROLS = [k for k in NEC_LEVELS if k.startswith(("KO_NEC_SHUF", "KO_NEC_RAND"))]
NEC_ARMS = ["NEC_BASE", "NEC_KO", "KO_NEC_FULL", "KO_NEC_AXIS", "KO_NEC_ORTH"] + NEC_CONTROLS


def _y(level, arm_idx, d_idx):
    """A per-domain value. The +0.01*d_idx term is common to every arm, so paired differences are
    unaffected by it; the tiny arm-dependent term keeps those differences from being IDENTICAL
    across domains, which would drive every sign-flip p to its own floor and make
    `p_at_its_floor` uninformative."""
    jit = (((d_idx * (arm_idx + 1)) % 5) - 2) * 0.00005
    return level + 0.01 * d_idx + jit


def _logps(p):
    """logp_concept / logp_codeword whose two-way softmax is exactly `p`."""
    return math.log(p / (1.0 - p)), 0.0


def _write_arm(root, tag_prefix, arm, arm_idx, level, *, necessity, layer=18, job="999001",
               codeword="basket"):
    """One STRUCTURALLY REAL run dir: exactly the files and fields both paths actually read.

    `necessity=True` writes the `necessity_*` block score_behavior.py emits only under
    `--rescue-donor ko` (field names and values taken from the real S-111 smoke rows), plus
    `hook_counters_measured_on`, which is how the arm records that its knockout-liveness counters
    describe the DONOR capture and not the readout.
    """
    d = os.path.join(root, "%s_%s_20260918_010101_1" % (tag_prefix, arm))
    os.makedirs(d)
    is_base = arm.endswith("_BASE")
    is_ko_floor = arm in ("NEC_KO", "KO")
    is_full = arm.endswith("_FULL")
    is_self = arm.endswith("_SELF")
    rescues = not (is_base or is_ko_floor)
    rows = []
    for d_idx, dom in enumerate(DOMS):
        for slot in SLOTS:
            lc, lk = _logps(_y(level, arm_idx, d_idx))
            r = {"prompt_id": "p_%s_%s" % (dom, slot), "domain": dom,
                 "family_id": "%s|%s|semantic_one_word" % (dom, slot),
                 "query_kind": "semantic_one_word", "cell": "C",
                 "logp_concept": lc, "logp_codeword": lk, "option_mass": 0.9,
                 "model": "llama-3.1-8b@rev0",
                 "hook_n_prefill_edits": None if is_base else 432,
                 "hook_n_decode_edits": 0,
                 "hook_liveness_violations": None if is_base else [],
                 "knockout_scope": None if is_base else "target_surface_row_only",
                 "rescue_layer": layer if rescues else None}
            if rescues:
                # FULL writes the whole state, so like the real arm it records no projection norm
                # and no `n_positions`; everything else records a norm-matched projection.
                r["rescue_liveness"] = ({"n_positions_written": 112, "n_forward_calls": 4,
                                         "fired": True} if (is_full or is_self) else
                                        {"delta_norm_mean": 0.99, "proj_norm_mean": 0.064,
                                         "written_norm_mean": 0.064,
                                         "norm_match_target_mean": 0.064,
                                         "captured_energy_frac_mean": 0.024, "rank": 1,
                                         "n_positions": 28,
                                         "n_positions_norm_match_degenerate": 0,
                                         "n_positions_written": 112, "n_forward_calls": 4,
                                         "fired": True, "wrote_nonzero": True})
                if not (is_full or is_self):
                    r["rescue_basis"] = "synthetic_axis_%s.pt" % codeword
                    r["rescue_basis_key"] = ("cand_rank1" if arm.endswith("_AXIS") else
                                             "ctrl_orth" if arm.endswith("_ORTH") else "ctrl_shuf")
                    r["rescue_norm_match_key"] = "nm_%s" % codeword
                    r["rescue_basis_meta"] = {"codeword": codeword, "fit_split": "train",
                                              "n_fit_domains": 67,
                                              "fit_domains_sha16": "4614853e5636eb5f",
                                              "basis_sha16": "fad8b030ae93976e"}
            if necessity and rescues:
                r["hook_counters_measured_on"] = "donor_capture_forward"
                r["necessity_direction"] = "remove-under-clean"
                r["necessity_donor_knockout"] = {"n_prefill_edits": 432, "n_decode_edits": 0}
                r["necessity_readout_knockout_delta"] = {"n_edits": 0, "n_prefill_edits": 0,
                                                         "n_decode_edits": 0}
                r["necessity_donor_delta_norm"] = 0.99
                r["necessity_patch_positions_written"] = 112
                r["necessity_violations"] = []
            rows.append(r)
    with open(os.path.join(d, "results.jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    with open(os.path.join(d, "gens.jsonl"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps({"prompt_id": r["prompt_id"], "domain": r["domain"],
                                 "generation": ""}) + "\n")
    json.dump({"schema": "DONE/1", "status": "ok", "rows_written": len(rows)},
              open(os.path.join(d, "DONE.json"), "w"))
    json.dump({"args": {"arm": arm, "bank": "data/bank_%s.jsonl" % codeword,
                        "exclude_prompt_ids": None, "attn_impl": "eager", "dtype": "bfloat16",
                        "rescue_layer": layer if rescues else None,
                        "rescue_donor": "ko" if (necessity and rescues) else "clean"}},
              open(os.path.join(d, "config.json"), "w"))
    json.dump({"slurm_job_id": job, "hostname": "n-999"},
              open(os.path.join(d, "RUNMETA.json"), "w"))
    return d


def _build(root, tag_prefix, *, necessity, levels=None, arms=None, extra=None):
    """Write one complete arm set. `levels` overrides individual arm levels."""
    lv = dict(NEC_LEVELS)
    lv.update(levels or {})
    lv.update(extra or {})
    names = list(arms or NEC_ARMS) + list((extra or {}).keys())
    for i, arm in enumerate(names):
        _write_arm(root, tag_prefix, arm, i, lv[arm], necessity=necessity)
    return names


def _nec_argv(root, names, outp, direction, **kw):
    argv = ["--codeword", "basket", "--tag-prefix", "nec", "--expect-n", N_ROWS,
            "--arms", ",".join(names), "--split", "train", "--direction", direction,
            "--base-arm", "NEC_BASE", "--ko-arm", "NEC_KO", "--full-arm", "KO_NEC_FULL",
            "--candidate-arm", "KO_NEC_AXIS", "--comparator-arm", "KO_NEC_ORTH",
            "--control-prefixes", "KO_NEC_SHUF,KO_NEC_RAND",
            "--n-boot", 400, "--out", outp]
    for k, v in kw.items():
        argv += ["--" + k.replace("_", "-"), v]
    return argv


def test_necessity_inverts_the_rank_and_sufficiency_on_the_same_numbers_does_not(analyze, tmp_path,
                                                                                monkeypatch):
    """THE inversion test: the SAME y_install numbers rank the candidate FIRST under necessity and
    LAST under sufficiency.

    Without the second half a `--direction necessity` that was parsed and then ignored would pass:
    the assertion "it inverted" is only meaningful beside "and the other orientation does the
    opposite on identical data". The candidate here drops installation by -0.010 while its eight
    controls sit in [-0.003, +0.004] of NEC_BASE, so read as a REMOVAL it is the most extreme arm
    in its family, and read as a RECOVERY from NEC_KO it is the least.
    """
    root = str(tmp_path / "runs")
    os.makedirs(root)
    monkeypatch.setattr(analyze.rederive, "SCORE_DIR", root)
    names = _build(root, "nec", necessity=True)
    rc, nec = _run(analyze, _nec_argv(root, names, str(tmp_path / "nec.json"), "necessity"))
    assert rc == 0, nec.get("VOID")
    assert nec["VOID"] == []

    # ---- necessity: reference is BASE, values keep their NATURAL (negative) sign, rank is FIRST
    assert nec["direction"] == "necessity" and nec["reference_arm"] == "NEC_BASE"
    assert nec["stronger_candidate_is"] == "MORE NEGATIVE"
    C = nec["contrasts"]
    assert "positive_control_full_minus_base" in C and "positive_control_full_minus_ko" not in C
    assert C["positive_control_full_minus_base"]["point"] == pytest.approx(-0.100, abs=5e-4)
    assert C["candidate_minus_base"]["point"] == pytest.approx(-0.010, abs=5e-4)
    assert C["manipulation_ko_minus_base"]["point"] == pytest.approx(-0.200, abs=5e-4)
    dist = nec["control_removal_distribution"]
    assert dist["candidate_rank_among_controls"] == 1, dist
    assert dist["n_controls"] == 8
    assert dist["candidate"] < 0 and min(dist["controls"].values()) > dist["candidate"]
    assert nec["gates"]["instrument_capable"] is True
    assert "INCONCLUSIVE" in nec["VERDICT"] and "LARGEST DROP" in nec["VERDICT"]
    # NOTHING was negated to get there.
    assert "not multiplied by -1" in nec["sign_policy"] or "nothing is multiplied" in nec["sign_policy"]

    # ---- the same numbers, the other orientation: the candidate is now LAST -------------------
    # Written without the `necessity_*` block, because a run that DECLARES `necessity_direction`
    # is (correctly) refused by --direction sufficiency -- see the VOID test below. The y_install
    # values are produced by the identical level table, so only the orientation differs.
    root2 = str(tmp_path / "runs2")
    os.makedirs(root2)
    monkeypatch.setattr(analyze.rederive, "SCORE_DIR", root2)
    names2 = _build(root2, "nec", necessity=False,
                    extra={"KO_NEC_SELF": NEC_LEVELS["NEC_KO"]})
    argv = _nec_argv(root2, names2, str(tmp_path / "suf.json"), "sufficiency")
    argv += ["--self-arm", "KO_NEC_SELF"]
    rc2, suf = _run(analyze, argv)
    assert rc2 == 0, suf.get("VOID")
    assert suf["VOID"] == []
    assert suf["reference_arm"] == "NEC_KO"
    sdist = suf["control_recovery_distribution"]
    assert sdist["n_controls"] == 8
    assert sdist["candidate_rank_among_controls"] == sdist["n_controls"] + 1 == 9, sdist
    # Same underlying installation values in both runs, to prove the numbers really are identical
    # and only the DECISION moved.
    assert suf["installation_by_arm"]["KO_NEC_AXIS"] == nec["installation_by_arm"]["KO_NEC_AXIS"]
    assert suf["installation_by_arm"]["NEC_BASE"] == nec["installation_by_arm"]["NEC_BASE"]
    assert "not above them" in suf["VERDICT"]


def test_necessity_verdict_never_borrows_the_sufficiency_wording(analyze, tmp_path, monkeypatch):
    """REVIEW R3-B1's shape, transposed onto the direction: a branch whose text is false.

    "It is INSIDE the controls, not above them" is direction-specific -- for a REMOVAL the
    candidate would have to be BELOW its controls -- so it must never be emitted verbatim under
    necessity, and neither must the word "recover". Both halves: the necessity artifact carries
    none of that vocabulary, and the sufficiency artifact still carries all of it (so the check
    cannot be satisfied by deleting the wording from both).
    """
    root = str(tmp_path / "runs")
    os.makedirs(root)
    monkeypatch.setattr(analyze.rederive, "SCORE_DIR", root)
    # Push the candidate INTO the family, so the FAIL branch -- the one that owns the wording -- is
    # the branch that actually runs.
    names = _build(root, "nec", necessity=True, levels={"KO_NEC_AXIS": 0.6035})
    rc, nec = _run(analyze, _nec_argv(root, names, str(tmp_path / "nec.json"), "necessity"))
    assert rc == 0 and nec["VOID"] == []
    assert nec["control_removal_distribution"]["candidate_rank_among_controls"] > 1
    v = nec["VERDICT"]
    assert "DOES NOT PASS" in v
    assert "not above them" not in v
    assert "recover" not in v
    assert "not below them" in v and "drop installation at least as much" in v
    # no recovery-flavoured KEY may exist either: a "recovery fraction" printed for a removal is
    # the same misreading in a different place
    assert "recovery_fraction_candidate_of_full" not in nec
    assert "removal_fraction_candidate_of_full" in nec
    assert not [k for k in nec["contrasts"] if k.startswith("recovery_")]
    assert [k for k in nec["contrasts"] if k.startswith("removal_")]

    # the other half: the sufficiency table still says exactly what it always said
    assert "not above them" in analyze.VERDICT_TEXT["sufficiency"]["rank_fail"]
    assert "recover at least as much as it does" in analyze.VERDICT_TEXT["sufficiency"]["rank_fail"]
    assert "not above them" not in analyze.VERDICT_TEXT["necessity"]["rank_fail"]


def test_capability_gate_refuses_a_whole_state_removal_that_does_not_drop(analyze, tmp_path,
                                                                          monkeypatch):
    """PR-CSI-003 required_gates.positive_control and plan section 15: if KO_NEC_FULL does not pull
    installation toward KO, the instrument is broken and the candidate's result is CANNOT ANSWER,
    NOT a negative.

    Both halves, because "refuses everything" is not the behaviour wanted: the wrong-way whole-state
    removal yields CANNOT ANSWER with no negative verdict anywhere in the string, and the correctly
    dropping one (the test above) yields a real verdict. The refusal must also reach the effect
    fraction, whose denominator is the same quantity -- a fraction computed from a broken instrument
    is exactly the "nonsense number with a plausible CI" this whole file is about.
    """
    root = str(tmp_path / "runs")
    os.makedirs(root)
    monkeypatch.setattr(analyze.rederive, "SCORE_DIR", root)
    # whole-state REMOVAL that RAISES installation: +0.10 instead of -0.10
    names = _build(root, "nec", necessity=True, levels={"KO_NEC_FULL": 0.700})
    rc, nec = _run(analyze, _nec_argv(root, names, str(tmp_path / "nec.json"), "necessity"))
    assert rc == 0 and nec["VOID"] == []
    assert nec["contrasts"]["positive_control_full_minus_base"]["point"] > 0
    assert nec["gates"]["instrument_capable"] is False
    v = nec["VERDICT"]
    assert v.startswith("CANNOT ANSWER")
    assert "section 15" in v
    assert "NOT a negative result" in v
    assert "DOES NOT PASS" not in v and "INCONCLUSIVE" not in v and "PASSES" not in v
    # and the fraction refuses on the SIGN of its denominator, with the sign it wanted recorded
    rf = nec["removal_fraction_candidate_of_full"]
    assert rf["status"] == "CANNOT ANSWER"
    assert rf["expected_denominator_sign"] == "negative"
    assert rf["denominator_point"] > 0
    assert "section 15" in rf["reason"] and "NOT a negative result" in rf["reason"]


def test_a_marginal_drop_whose_ci_touches_zero_is_also_CANNOT_ANSWER(analyze, tmp_path, monkeypatch):
    """The other end of the same gate: the point estimate alone is not enough. Necessity requires
    the UPPER ci95 bound to be below zero, mirroring the sufficiency branch's demand that the LOWER
    bound be above zero. A whole-state removal that lands exactly ON NEC_BASE has point 0, so it
    cannot satisfy either form and must not be waved through on a technicality."""
    root = str(tmp_path / "runs")
    os.makedirs(root)
    monkeypatch.setattr(analyze.rederive, "SCORE_DIR", root)
    names = _build(root, "nec", necessity=True, levels={"KO_NEC_FULL": NEC_LEVELS["NEC_BASE"]})
    rc, nec = _run(analyze, _nec_argv(root, names, str(tmp_path / "nec.json"), "necessity"))
    assert rc == 0 and nec["VOID"] == []
    pc = nec["contrasts"]["positive_control_full_minus_base"]
    assert abs(pc["point"]) < 1e-3 and pc["ci95"][1] >= 0
    assert nec["gates"]["instrument_capable"] is False
    assert nec["VERDICT"].startswith("CANNOT ANSWER")


def test_the_skipped_identity_gate_is_recorded_with_its_reason(analyze, tmp_path, monkeypatch):
    """PR-CSI-003 required_gates.no_inert_identity_control_exists: there IS no inert identity
    control for this direction, so the gate is SKIPPED -- and a gate that quietly disappears is
    worse than one that fails.

    Three halves here, all of which have to hold:
      * the necessity artifact RECORDS the skip, its reason and the preregistration that states it,
        and does NOT report an `identity_check` result;
      * the sufficiency artifact still EVALUATES the gate and records nothing as skipped;
      * an arm offered as the identity control for this direction is REFUSED rather than quietly
        used, because the only thing worse than a missing gate is a fake one.
    """
    root = str(tmp_path / "runs")
    os.makedirs(root)
    monkeypatch.setattr(analyze.rederive, "SCORE_DIR", root)
    names = _build(root, "nec", necessity=True)
    rc, nec = _run(analyze, _nec_argv(root, names, str(tmp_path / "nec.json"), "necessity"))
    assert rc == 0 and nec["VOID"] == []
    sk = nec["gates_skipped"]["identity_check"]
    assert sk["status"] == "SKIPPED"
    assert "no inert identity control" in sk["reason"]
    assert "refused by the necessity arm's own precondition" in sk["reason"]
    assert "pr003" in sk["prereg"] and "no_inert_identity_control_exists" in sk["prereg"]
    assert sk["nearest_available_control"] == "KO_NEC_ORTH"
    assert "identity_check" not in nec["gates"]
    assert "identity_self_minus_ko" not in nec["contrasts"]

    # refused, not quietly accepted
    with pytest.raises(SystemExit) as e:
        _run(analyze, _nec_argv(root, names + ["KO_NEC_SELFX"], str(tmp_path / "x.json"),
                                "necessity") + ["--self-arm", "KO_NEC_SELFX"])
    assert "no inert identity control can exist" in str(e.value)


def test_the_skipped_gate_survives_the_VOID_early_return(analyze, tmp_path, monkeypatch):
    """The artifact most likely to be read once and never re-run is the VOID one, and the VOID path
    returns before the gates are evaluated. If the skip record were built where the gates are, the
    reason would be absent from exactly that artifact. Asserted on a genuinely VOIDed run."""
    root = str(tmp_path / "runs")
    os.makedirs(root)
    monkeypatch.setattr(analyze.rederive, "SCORE_DIR", root)
    names = _build(root, "nec", necessity=True)
    # break a VOID condition that has nothing to do with the direction: a TEST-split domain would
    # need a different bank, so use the cheapest real one -- a bank that does not name the codeword.
    rc, nec = _run(analyze, _nec_argv(root, names, str(tmp_path / "nec.json"), "necessity",
                                      codeword="button"))
    assert rc == 2
    assert nec["VERDICT"].startswith("VOID")
    assert nec["gates_skipped"]["identity_check"]["status"] == "SKIPPED"
    assert "no inert identity control" in nec["gates_skipped"]["identity_check"]["reason"]


def test_the_direction_is_checked_against_the_rows_not_taken_on_trust(analyze, tmp_path,
                                                                     monkeypatch):
    """`--direction` decides what every sign in the artifact means, so it is verified against what
    the run actually did (`necessity_direction`, written by score_behavior.py only under
    `--rescue-donor ko`).

    Both halves, and both are real hazards: necessity arms read as sufficiency invert every decision
    silently, and sufficiency arms read as necessity do the same in reverse.
    """
    root = str(tmp_path / "nec_runs")
    os.makedirs(root)
    monkeypatch.setattr(analyze.rederive, "SCORE_DIR", root)
    names = _build(root, "nec", necessity=True, extra={"KO_NEC_SELFY": NEC_LEVELS["NEC_KO"]})
    argv = _nec_argv(root, names, str(tmp_path / "a.json"), "sufficiency")
    argv += ["--self-arm", "KO_NEC_SELFY"]
    rc, got = _run(analyze, argv)
    assert rc == 2
    assert any("--direction sufficiency but these arms' rows declare necessity_direction" in v
               for v in got["VOID"]), got["VOID"]

    root2 = str(tmp_path / "suf_runs")
    os.makedirs(root2)
    monkeypatch.setattr(analyze.rederive, "SCORE_DIR", root2)
    names2 = _build(root2, "nec", necessity=False)
    rc2, got2 = _run(analyze, _nec_argv(root2, names2, str(tmp_path / "b.json"), "necessity"))
    assert rc2 == 2
    assert any("is not (entirely) a necessity arm" in v for v in got2["VOID"]), got2["VOID"]


def test_the_necessity_arms_own_four_legs_are_re_asserted_from_the_rows(analyze, tmp_path,
                                                                        monkeypatch):
    """S-110's legs 2, 3 and 4 are re-checked HERE, from the rows the analyser reads, because a gate
    that only ever ran inside the scorer is a gate this artifact cannot vouch for.

    Parameterised over the three break modes so each leg is shown to refuse ON ITS OWN -- a single
    "broken is refused" assertion passes as soon as one leg works and lets the others rot (the
    lesson tests/test_necessity_arm.py records).
    """
    breaks = {
        "leg2_knockout_left_on_the_readout": (
            {"necessity_readout_knockout_delta": {"n_edits": 7}}, "leg 2"),
        "leg3_patch_never_fired": ({"necessity_patch_positions_written": 0}, "leg 3"),
        "leg4_nothing_to_remove": ({"necessity_donor_delta_norm": 0.0}, "leg 4"),
    }
    for name, (patch, needle) in breaks.items():
        root = str(tmp_path / name)
        os.makedirs(root)
        monkeypatch.setattr(analyze.rederive, "SCORE_DIR", root)
        names = _build(root, "nec", necessity=True)
        # break the CANDIDATE arm only, in one field, leaving everything else intact
        cand_dir = [os.path.join(root, x) for x in os.listdir(root) if "KO_NEC_AXIS" in x][0]
        rp = os.path.join(cand_dir, "results.jsonl")
        rows = [json.loads(l) for l in open(rp, encoding="utf-8")]
        for r in rows:
            r.update(patch)
        with open(rp, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        rc, got = _run(analyze, _nec_argv(root, names, str(tmp_path / (name + ".json")),
                                          "necessity"))
        assert rc == 2, name
        assert any(needle in v and "KO_NEC_AXIS" in v for v in got["VOID"]), (name, got["VOID"])


def test_effect_fraction_guard_is_sign_aware_but_keeps_the_magnitude_rule(analyze):
    """The decision on `recovery_fraction`'s `min_denominator=0.01` guard, locked down.

    What was checked rather than assumed: the existing guard tests `abs(den_point) < min_denominator`,
    so its MAGNITUDE half already handles a negative denominator, and the ratio num/den it then
    returns is correctly signed for either direction (both negative -> a positive fraction of the
    whole-state removal, directly comparable with the sufficiency fraction). What it does NOT do is
    check that the denominator has the sign the DIRECTION requires, which is how a broken instrument
    produces a plausible-looking fraction. So the SIGN check was added in front of it and the
    magnitude rule was left exactly as 164 committed results found it.

    Both halves for both directions: the right-signed denominator reaches the real estimator and
    returns a number, and the wrong-signed one returns CANNOT ANSWER with a stated reason.
    """
    doms = ["d%d" % i for i in range(20)]
    def series(v):
        return {d: v + 0.001 * i for i, d in enumerate(doms)}

    nec = analyze.direction_profile("necessity")
    suf = analyze.direction_profile("sufficiency")
    base, ref = series(0.60), series(0.60)

    # necessity, right-signed: FULL removes 0.10 -> a real fraction, and the guard's abs() means
    # a -0.10 denominator is NOT rejected for magnitude
    ok = analyze.effect_fraction(nec, doms, series(0.50), base, series(0.59),
                                 2000, 1, min_denominator=0.01)
    assert ok["status"] == "ok"
    assert ok["denominator_point"] == pytest.approx(-0.10, abs=1e-9)
    assert ok["point"] == pytest.approx(0.10, abs=1e-3)      # 10 % of the whole-state removal
    # necessity, wrong-signed: refused on the SIGN, not silently ratio'd
    bad = analyze.effect_fraction(nec, doms, series(0.70), base, series(0.59),
                                  2000, 1, min_denominator=0.01)
    assert bad["status"] == "CANNOT ANSWER" and bad["expected_denominator_sign"] == "negative"
    # necessity, right-signed but DEGENERATE in magnitude: the pre-existing rule still applies
    tiny = analyze.effect_fraction(nec, doms, series(0.5995), base, series(0.59),
                                   2000, 1, min_denominator=0.01)
    assert tiny["status"] == "CANNOT ANSWER" and "degenerate" in tiny["reason"]

    # sufficiency, unchanged in both directions of failure
    assert analyze.effect_fraction(suf, doms, series(0.70), ref, series(0.61),
                                   2000, 1, min_denominator=0.01)["status"] == "ok"
    mirror = analyze.effect_fraction(suf, doms, series(0.50), ref, series(0.61),
                                     2000, 1, min_denominator=0.01)
    assert mirror["status"] == "CANNOT ANSWER" and mirror["expected_denominator_sign"] == "positive"


def test_the_direction_is_recorded_in_both_artifacts_beside_the_run_dir_filters(analyze, indep,
                                                                                tmp_path,
                                                                                monkeypatch):
    """Review R8-m5 / sprint item P0.4: a report that is not self-describing about how it was
    produced is what that item exists to prevent, and the DIRECTION is the single fact that decides
    what every sign in the file means. It must be recorded by BOTH paths, next to the run-dir
    filters they already record."""
    root = str(tmp_path / "runs")
    os.makedirs(root)
    monkeypatch.setattr(analyze.rederive, "SCORE_DIR", root)
    monkeypatch.setattr(indep, "SB", root)
    names = _build(root, "nec", necessity=True)
    _, nec = _run(analyze, _nec_argv(root, names, str(tmp_path / "nec.json"), "necessity",
                                     require_rescue_layer=18))
    for k in ("direction", "reference_arm", "reference_arm_role", "stronger_candidate_is",
              "sign_policy", "direction_contract", "require_rescue_layer", "require_slurm_job"):
        assert k in nec, k
    assert nec["direction"] == "necessity" and nec["require_rescue_layer"] == 18
    assert nec["prereg"].endswith("dcs_csi_pr003_necessity_basket.json")

    _, ind = _run(indep, ["--tag-prefix", "nec", "--split", "train", "--expect-n", N_ROWS,
                          "--allow-short", 0, "--direction", "necessity",
                          "--base", "NEC_BASE", "--ko", "NEC_KO", "--full", "KO_NEC_FULL",
                          "--candidate", "KO_NEC_AXIS", "--controls", ",".join(NEC_CONTROLS),
                          "--require-rescue-layer", 18, "--out", str(tmp_path / "ind.json")])
    for k in ("direction", "reference_arm", "stronger_candidate_is", "sign_policy",
              "instrument_capable", "identity_gate", "require_rescue_layer", "require_slurm_job"):
        assert k in ind, k
    assert ind["direction"] == "necessity" and ind["reference_arm"] == "NEC_BASE"
    assert "no inert identity control" in ind["identity_gate"]


def test_the_independent_path_inverts_the_rank_too_and_not_by_shared_code(indep, tmp_path,
                                                                         monkeypatch):
    """The two paths share no code on purpose, so a sign convention applied in one and not the other
    would let them "agree" on a rank that one of them read upside down -- which is exactly the
    two-path guarantee review R8-M1 found broken on the layer axis.

    Both halves on identical synthetic data: the necessity run ranks the candidate FIRST and reports
    its value as NEGATIVE, and the sufficiency run on the same numbers ranks it LAST.
    """
    root = str(tmp_path / "runs")
    os.makedirs(root)
    monkeypatch.setattr(indep, "SB", root)
    _build(root, "nec", necessity=True)
    common = ["--tag-prefix", "nec", "--split", "train", "--expect-n", N_ROWS, "--allow-short", 0,
              "--base", "NEC_BASE", "--ko", "NEC_KO", "--full", "KO_NEC_FULL",
              "--candidate", "KO_NEC_AXIS", "--controls", ",".join(NEC_CONTROLS)]
    _, nec = _run(indep, common + ["--direction", "necessity",
                                   "--out", str(tmp_path / "n.json")])
    assert nec["reference_arm"] == "NEC_BASE"
    assert nec["candidate_minus_base"] == pytest.approx(-0.010, abs=5e-4)
    assert nec["gates"]["positive_control_full_minus_base"]["point"] == pytest.approx(-0.100,
                                                                                     abs=5e-4)
    assert nec["instrument_capable"] is True
    assert nec["ranks"]["pooled"]["rank"] == 1
    assert nec["ranks"]["pooled"]["of"] == 9
    assert nec["ranks"]["random_only"]["rank"] == 1 and nec["ranks"]["shuffled_only"]["rank"] == 1

    _, suf = _run(indep, common + ["--direction", "sufficiency", "--out", str(tmp_path / "s.json")])
    assert suf["reference_arm"] == "NEC_KO"
    assert suf["candidate_minus_ko"] == pytest.approx(0.190, abs=5e-4)
    assert suf["ranks"]["pooled"]["rank"] == 9      # dead last of its own family
    assert suf["ranks"]["random_only"]["rank"] == 5 and suf["ranks"]["shuffled_only"]["rank"] == 5


def test_the_independent_paths_capability_gate_also_refuses_rather_than_reporting_a_negative(
        indep, tmp_path, monkeypatch):
    """The gate has to bind in BOTH paths, or the independent re-derivation would happily publish a
    rank from a broken instrument while the primary path declared CANNOT ANSWER -- a disagreement
    that reads as a code bug rather than the design decision it is. Both halves: the wrong-way
    whole-state removal replaces every family verdict with CANNOT ANSWER, and the good run above
    still returns real verdicts."""
    root = str(tmp_path / "runs")
    os.makedirs(root)
    monkeypatch.setattr(indep, "SB", root)
    _build(root, "nec", necessity=True, levels={"KO_NEC_FULL": 0.700})
    _, got = _run(indep, ["--tag-prefix", "nec", "--split", "train", "--expect-n", N_ROWS,
                          "--allow-short", 0, "--direction", "necessity",
                          "--base", "NEC_BASE", "--ko", "NEC_KO", "--full", "KO_NEC_FULL",
                          "--candidate", "KO_NEC_AXIS", "--controls", ",".join(NEC_CONTROLS),
                          "--out", str(tmp_path / "n.json")])
    assert got["instrument_capable"] is False
    for nm, v in got["ranks"].items():
        assert v["verdict"].startswith("CANNOT ANSWER"), (nm, v)
        assert "section 15" in v["verdict"]
        assert "NOT a negative result" in v["verdict"]
        assert "DOES NOT PASS" not in v["verdict"]


def test_the_default_output_filename_cannot_overwrite_the_sufficiency_report(analyze, tmp_path,
                                                                            monkeypatch):
    """PR-CSI-003 runs the necessity direction on basket/TRAIN -- the same codeword and split as the
    committed sufficiency report `reports/DCS_CSI_SUBSPACE_basket_train.json`. With the direction
    absent from the DEFAULT filename (the one an operator gets by omitting --out) the necessity run
    would silently overwrite the report it is meant to be paired with: data loss dressed as a
    successful run.

    Exercised through the real `_write`, with REPO redirected into a scratch tree so nothing lands
    in reports/. Both halves: sufficiency keeps its historical name exactly, and necessity gets a
    different one.
    """
    monkeypatch.setattr(analyze, "REPO", str(tmp_path))
    os.makedirs(os.path.join(str(tmp_path), "reports"))

    class A(object):
        out = None
        codeword = "basket"
        split = "train"
        option_mass_floor = 0.0
        direction = "sufficiency"

    a = A()
    analyze._write({"x": 1}, a)
    a.direction = "necessity"
    analyze._write({"x": 2}, a)
    written = sorted(os.listdir(os.path.join(str(tmp_path), "reports")))
    assert written == ["DCS_CSI_SUBSPACE_NECESSITY_basket_train.json",
                       "DCS_CSI_SUBSPACE_basket_train.json"], written


def test_an_unknown_direction_is_refused_by_the_profile_not_defaulted(analyze):
    """Missing or unrecognised load-bearing metadata must RAISE, not default (plan section 14). The
    argparse `choices` already refuses at the CLI, but `direction_profile` is the function every
    site reads its orientation from, so it must refuse on its own rather than falling through to
    the sufficiency orientation."""
    with pytest.raises(SystemExit):
        analyze.direction_profile("whatever")
    assert analyze.direction_profile("necessity")["expected_denominator_sign"] == -1
    assert analyze.direction_profile("sufficiency")["expected_denominator_sign"] == 1
    assert set(analyze.VERDICT_TEXT) == set(analyze.DIRECTIONS)
    # every branch key exists for BOTH directions, so no branch can fall back to the other's text
    assert (set(analyze.VERDICT_TEXT["sufficiency"])
            == set(analyze.VERDICT_TEXT["necessity"])
            == {"cannot_answer", "rank_pass", "rank_inconclusive", "rank_fail",
                "single_pass", "single_fail"})
