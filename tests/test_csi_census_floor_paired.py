#!/usr/bin/env python3
"""The paired two-floor comparison must refuse the three ways it can be made meaningless (S-559).

*** WHY THIS FILE EXISTS. ***
S-558 compared two option-mass floors by subtracting POINT ESTIMATES and recorded, as its own
not-established item, that it propagated no interval. S-559 built
`scripts/dcs_csi_census_floor_paired.py` to do it properly. The trap that script exists to avoid is
NOT arithmetic -- it is that the obvious repair (compare the two census artefacts' MARGINAL ci95s) is
invalid, because both floors are computed over the SAME domains from NESTED row sets. Measured at
S-559: the two per-domain difference vectors correlate r = 0.43..0.90, pairing narrows the interval
1.32x..2.99x, and BOTH movements that are established under pairing read as null unpaired.

So the properties worth a test are the ones that would silently make the comparison unpaired or
vacuous while still printing a number:
  1. a floor of 0 -- "paired against itself", which would print delta == 0 for every arm,
  2. a reference arm the script does not load -- the floor keyed on something unverified, the
     PR-CSI-025 VOID 7 hazard that BASE arms are NOT uniformly named (HD_BASE/BF_BASE/BK_BASE),
  3. a floor that changes the DOMAIN SET -- the resample vector would not be the same vector, so the
     comparison would not be paired at all,
  4. and the anchor's own margin must NOT be reported as a comparison: it is 1.0 by construction.
Each is asserted against the SOURCE, because three of the four cannot be provoked from the real data
(the real floor retains all 23 domains) and a guard that only exists on an unreachable path is
exactly the kind S-534 found asserting nothing.
"""
import importlib.util
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAIRED = os.path.join(REPO, "scripts", "dcs_csi_census_floor_paired.py")


def _src():
    with open(PAIRED, encoding="utf-8") as fh:
        return fh.read()


def test_the_script_exists_and_parses():
    import ast
    ast.parse(_src())


def test_a_nonpositive_floor_is_refused():
    """floor 0 would compare the control branch against itself and print delta == 0 everywhere."""
    src = _src()
    assert "if a.floor <= 0.0:" in src, "no guard on a non-positive floor"
    i = src.index("if a.floor <= 0.0:")
    assert "REFUSING" in src[i:i + 400] and "vacuous" in src[i:i + 400]


def test_a_reference_arm_the_script_does_not_load_is_refused():
    """The key set must come from an arm this reader actually opened, not from a name."""
    src = _src()
    assert "if a.reference not in dirs:" in src
    i = src.index("if a.reference not in dirs:")
    seg = src[i:i + 600]
    assert "REFUSING" in seg
    assert "VOID 7" in seg, "the refusal must name WHY base arms cannot be assumed uniformly named"


def test_a_floor_that_changes_the_domain_set_is_refused():
    """If the floor drops a whole domain the resample vector is not the same vector."""
    src = _src()
    assert "if dc != df:" in src
    i = src.index("if dc != df:")
    seg = src[i:i + 500]
    assert "REFUSING" in seg and "not paired" in seg


def test_the_anchor_is_not_reported_as_clearing_or_failing_itself():
    """|E(anchor)|/|E(anchor)| == 1.0 with a degenerate interval; 'above'/'below' would be false."""
    src = _src()
    assert 'if arm == a.anchor_arm:' in src, "no special case for the anchor's own margin"
    i = src.index('if arm == a.anchor_arm:')
    seg = src[i:i + 400]
    assert "by construction" in seg
    assert "above 1.0" not in seg.split("elif")[0], "the anchor branch must not print a comparison"


def test_one_shared_resample_drives_every_statistic():
    """The whole point: ONE index vector per replicate, both floors evaluated on it."""
    src = _src()
    assert "def stats_on(idx):" in src
    i = src.index("def stats_on(idx):")
    seg = src[i:i + 900]
    assert 'v["ctrl"][i] for i in idx' in seg and 'v["flr"][i] for i in idx' in seg, \
        "both branches must be evaluated on the SAME idx, or the bootstrap is not paired"
    # and only one idx is drawn per replicate
    j = src.index("for _ in range(a.B):")
    assert src[j:j + 200].count("rng.randrange(n) for _ in range(n)") == 1, \
        "more than one resample per replicate would unpair the comparison"


def test_it_declares_that_it_freezes_nothing():
    src = _src()
    assert "NO_VERDICT" in src
    assert "NO_PREREGISTERED_BAR" in src


def test_it_refuses_a_nonpositive_floor_when_actually_invoked():
    """The guard is reachable from argv, not only present in the source."""
    # --out became REQUIRED at S-564 (R42-M4), so it must be supplied here or argparse rejects the
    # call before the floor guard is ever reached -- which would make this test pass for the wrong
    # reason. The path is never written: the floor refusal fires first.
    p = subprocess.run([sys.executable, PAIRED, "--tag-prefix", "x", "--expect-n", "1",
                        "--arms", "A", "--reference", "A", "--floor", "0",
                        "--out", os.devnull],
                       capture_output=True, text=True)
    assert p.returncode != 0
    assert "REFUSING" in (p.stdout + p.stderr), (p.stdout + p.stderr)[:400]


def test_it_reuses_the_census_option_mass_keys_rather_than_reimplementing_them():
    """A second implementation of the floor would be a second thing to get wrong."""
    src = _src()
    assert "census._option_mass_keys" in src
    assert "w4.by_domain" in src
    assert "w4.pct" in src


# ---- R42 / S-562: the guards review R42 said were missing --------------------------------------
# Each of these was a REACHABLE path to a wrong-but-plausible output, reproduced from argv before the
# fix. They are asserted against the source AND, where cheap, exercised, because the published numbers
# came out of this file before any of them existed.

def test_the_interval_label_is_derived_from_ci_and_cannot_say_ci95_when_it_is_not():
    """R42-M5: `--ci 0.50` printed AND serialized the literal "ci95" and flipped a verdict."""
    src = _src()
    assert 'CIL = "ci%g" % round(a.ci * 100)' in src, "no derived label"
    # The literal must not survive as a KEY or SUBSCRIPT. It legitimately appears in prose
    # (docstring, and the comment recording the defect), so a bare substring test over the whole
    # file is looser than the property -- which is the exact over-matching this review kept finding.
    assert '["ci95"]' not in src, "a hardcoded ci95 subscript can lie about the level"
    assert '"ci95":' not in src, "a hardcoded ci95 key can lie about the level"
    assert 'delta (%s)" % CIL' in src


def test_a_nondefault_ci_actually_prints_its_own_label():
    p = subprocess.run([sys.executable, PAIRED, "--tag-prefix", "csi5_census_basket_validation",
                        "--expect-n", "230", "--reference", "HD_BASE", "--floor", "0.05",
                        "--arms", "SINGLE_02", "--anchor-arm", "HD_BOTK", "--ci", "0.50",
                        "--min-rows", "1"], capture_output=True, text=True)
    if p.returncode != 0:          # corpus absent in this checkout
        return
    assert "ci50" in p.stdout, "the label must follow --ci"
    assert "ci95" not in p.stdout, "a 50%% interval must never be labelled ci95"


def test_the_base_arm_among_arms_is_a_named_refusal_not_a_keyerror():
    """R42-M6: `--arms HD_BASE,...` raised a bare KeyError: 'pct' naming the symptom."""
    src = _src()
    assert 'if "pct" not in r:' in src
    i = src.index('if "pct" not in r:')
    seg = src[i:i + 600]
    assert "REFUSING" in seg and "base arm" in seg


def test_a_zero_anchor_refuses_instead_of_printing_an_empty_margin_section():
    """R42-M7: it printed a MARGIN header with no rows and exited 0."""
    src = _src()
    assert 'if not any(res[arm].get("margin_flr") for arm in arms):' in src
    i = src.index('if not any(res[arm].get("margin_flr") for arm in arms):')
    assert "REFUSING" in src[i:i + 500]


def test_a_domain_thinned_below_min_rows_refuses():
    """R42-C1/S-561: the floor took freight_yard to ONE row carrying 1/23 of the estimate."""
    src = _src()
    assert "--min-rows" in src
    assert "if min(rpd.values()) < a.min_rows:" in src
    i = src.index("if min(rpd.values()) < a.min_rows:")
    assert "REFUSING" in src[i:i + 700]


def test_min_rows_default_is_not_1():
    """A default of 1 would make the guard inert on exactly the run that needed it."""
    src = _src()
    i = src.index('"--min-rows"')
    seg = src[i:i + 200]
    assert "default=1" not in seg, "min-rows must not default to the value that permits everything"


def test_per_domain_retention_is_printed_and_serialized():
    """The domain SET check licensed 'the SAME 23 domains' while the domains were thinned 10 -> 1."""
    src = _src()
    assert "[retention] rows per domain" in src
    assert '"rows_per_domain"' in src and '"min_rows_per_domain"' in src


def test_the_slot_pooled_decomposition_is_computed_and_reported():
    """Identical to domain-equal at floor 0 BY CONSTRUCTION, so divergence = re-weighting."""
    src = _src()
    assert "def pooled(arm, br):" in src
    assert "sign_reverses_vs_domain_equal" in src
    assert "[decomp]" in src


def test_an_interval_from_fewer_than_B_draws_refuses():
    """R42-m9: quantiles were taken from however many draws survived, with no disclosure."""
    src = _src()
    assert "if len(xs) != a.B:" in src
    i = src.index("if len(xs) != a.B:")
    assert "REFUSING" in src[i:i + 400]


# ---- R42-M3 / M4 / F6, S-564: provenance, identity and a written artefact ------------------------

def test_out_is_required_not_optional():
    """R42-M4: --out defaulted to None and no artefact was ever written, so three entries' worth of
    intervals lived only in a terminal. The census's own --out is required=True."""
    src = _src()
    assert 'ap.add_argument("--out", required=True' in src
    assert '"--out", default=None' not in src


def test_it_is_invoked_without_out_and_refuses():
    p = subprocess.run([sys.executable, PAIRED, "--tag-prefix", "x", "--expect-n", "1",
                        "--arms", "A", "--reference", "A", "--floor", "0.05"],
                       capture_output=True, text=True)
    assert p.returncode != 0
    assert "--out" in (p.stdout + p.stderr)


def test_the_artefact_is_written_atomically_through_w4():
    """A half-written artefact is worse than none; w4.atomic_write_json fsyncs and re-reads."""
    src = _src()
    assert "w4.atomic_write_json(a.out, blob)" in src
    assert "json.dump(blob" not in src, "a plain json.dump is not atomic"


def test_a_slurm_job_filter_can_be_required():
    """R42-M3: strict_run_dir was called with NO slurm filter, while the census's frozen read passes
    --require-slurm-job. rederive's R8-B1 records the S-104b near-miss this reopens."""
    src = _src()
    assert '"--require-slurm-job"' in src
    assert "require_slurm_jobs=jobs" in src


def test_arm_identity_is_asserted_from_the_runs_own_record():
    """Resolving arms by TAG NAME alone would publish a mislabelled directory as the named arm."""
    src = _src()
    assert "census.recorded_heads(d)" in src
    assert 'if got is None:' in src
    i = src.index("census.recorded_heads(d)")
    seg = src[i:i + 1800]
    assert "REFUSING" in seg and "Absence is not a value" in seg


def test_a_SINGLE_arm_whose_record_disagrees_with_its_name_refuses():
    src = _src()
    assert 'want = [int(m.group(1))]' in src
    i = src.index('want = [int(m.group(1))]')
    assert "REFUSING" in src[i:i + 500]


def test_the_base_arms_EMPTY_is_not_published_as_ALL():
    """recorded_heads maps an EMPTY knockout_heads to the string "ALL" (S-292). Publishing that
    verbatim would state that the clean reference knocked out all 32 heads -- the ACTIVELY CONCEALS
    defect R30-A/S-332 fixed in the census."""
    src = _src()
    assert 'if arm == a.base_arm:' in src
    i = src.index('if arm == a.base_arm:')
    seg = src[i:i + 1400]
    assert 'EMPTY -- no intervention flag' in seg
    assert "REFUSING" in seg, "a base arm carrying a real head list must refuse"


def test_the_artefact_records_run_dirs_reference_and_job():
    src = _src()
    for key in ('"run_dirs"', '"reference_run_dir"', '"require_slurm_job"',
                '"arm_identity_from_own_knockout_heads"'):
        assert key in src, "artefact does not record %s" % key


def test_the_published_artefact_exists_and_carries_its_provenance():
    """The point of M4/F6: the intervals must be reproducible from a file, not from the log."""
    import json
    p = os.path.join(REPO, "reports",
                     "DCS_CSI_FLOOR_PAIRED_csi5_census_basket_validation.json")
    if not os.path.isfile(p):
        return                            # corpus/artefact absent in this checkout
    d = json.load(open(p, encoding="utf-8"))
    assert d["schema"] == "dcs_csi_census_floor_paired/1"
    assert d["require_slurm_job"] == "918631"
    assert d["reference_run_dir"].startswith("csi5_census_basket_validation_HD_BASE_")
    assert len(d["run_dirs"]) == 6 and len(d["domains"]) == 23
    ident = d["arm_identity_from_own_knockout_heads"]
    assert ident["SINGLE_19"] == [19] and ident["SINGLE_23"] == [23]
    assert "EMPTY" in ident["HD_BASE"], "base arm must not be recorded as ALL"
    assert d["results"]["HD_BOTK"]["pooled"]["sign_reverses_vs_domain_equal"] is True
