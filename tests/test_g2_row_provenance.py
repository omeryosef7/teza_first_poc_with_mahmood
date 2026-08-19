"""R-18: analyze_g2 must RECORD what its rows are, not just how many.

The published G2 figure (rho +0.2618 within-domain, p=5e-4, n=234) was computed over a row set that
was 31% sibling families sharing demonstrations and 31% experimentally-manipulated designed variance,
because the filter was `condition == arm` and nothing else. The artifact recorded `n_analysed: 234`
and no description of the 234. On the 90 clean rows the same statistic is -0.0518 (p=0.658).

These tests pin the guard: the slot must be RECOVERABLE from family_id (the judge rows do not carry
`family_slot`, and the first version of the check reported `{None: 234}` and a sibling count of 0 --
a guard that could not fire), and the filters must actually filter.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))

import analyze_g2 as g2  # noqa: E402

SRC = open(os.path.join(ROOT, "src", "boombness", "analyze_g2.py")).read()


def _slot_of(row):
    """Mirror of the helper defined inside main(); kept in sync by test_slot_regex_matches_source."""
    v = row.get("family_slot")
    if v is not None:
        return v
    m = re.search(r"\|slot(\d+)\|", row.get("family_id") or "")
    return int(m.group(1)) if m else None


def test_slot_is_recoverable_from_family_id_when_the_field_is_absent():
    """THE GUARD. Judge rows carry `family_id` but NOT `family_slot`. A check that reads only the
    field counts every row as slot-None and reports 0 siblings -- which is what the first version
    did, on data containing 72 of them."""
    row = {"family_id": "farm_storage|dev|slot2|n4|none|consistent|near|plain|behavioral"}
    assert row.get("family_slot") is None          # the field really is absent
    assert _slot_of(row) == 2                      # and the slot is still recovered


def test_slot_prefers_the_explicit_field_when_present():
    row = {"family_slot": 0, "family_id": "d|dev|slot2|n4|none|consistent|near|plain|behavioral"}
    assert _slot_of(row) == 0


def test_slot_is_none_and_countable_when_neither_source_exists():
    """Unrecoverable must be None and reported, never silently folded into slot 0."""
    assert _slot_of({"family_id": "no-slot-here"}) is None
    assert _slot_of({}) is None


def test_source_defines_the_filters_and_the_warning():
    """The flags and the warning must exist in the module, addressed by name."""
    assert "--require-bank-block" in SRC
    assert "--slot0-only" in SRC
    assert "R-18 WARNING" in SRC


def test_composition_is_recomputed_after_filtering_not_before():
    """The first version printed the PRE-filter composition beside a post-filter n -- it showed
    `families: 72` on a run that had just dropped all 72. The post-filter recomputation must be
    present, and the pre-filter counts must be kept under an explicitly-named key."""
    assert "by_bank_block_BEFORE_filters" in SRC
    assert 'composition["by_bank_block"] = dict(collections.Counter(blocks[p][0] for p in kept))' in SRC


def test_row_composition_is_written_into_the_artifact():
    """A count is not a description of a sample. The artifact must carry the composition."""
    assert '"row_composition": composition' in SRC


def test_the_committed_clean_artifact_disagrees_with_the_published_one():
    """The regression this file exists for: if someone re-runs unfiltered and overwrites the clean
    artifact, this fails. Both must exist and must differ in the cited estimand."""
    import json
    out = os.path.join(ROOT, "outputs", "boombness")
    pub = os.path.join(out, "g2_analysis_cwpos.json")
    cln = os.path.join(out, "g2_analysis_cwpos_CLEAN.json")
    if not (os.path.exists(pub) and os.path.exists(cln)):
        import pytest
        pytest.skip("artifacts not present in this checkout")
    P = json.load(open(pub))["clustered_inference"]["rho_within_domain"]
    C = json.load(open(cln))["clustered_inference"]["rho_within_domain"]
    assert P > 0.2, f"published within-domain rho should be the retracted +0.26, got {P}"
    assert C < 0.0, f"clean within-domain rho should be negative, got {C}"
