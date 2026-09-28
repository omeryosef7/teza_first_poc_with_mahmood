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
    p = subprocess.run([sys.executable, PAIRED, "--tag-prefix", "x", "--expect-n", "1",
                        "--arms", "A", "--reference", "A", "--floor", "0"],
                       capture_output=True, text=True)
    assert p.returncode != 0
    assert "REFUSING" in (p.stdout + p.stderr)


def test_it_reuses_the_census_option_mass_keys_rather_than_reimplementing_them():
    """A second implementation of the floor would be a second thing to get wrong."""
    src = _src()
    assert "census._option_mass_keys" in src
    assert "w4.by_domain" in src
    assert "w4.pct" in src
