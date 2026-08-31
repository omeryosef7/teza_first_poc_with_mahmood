"""`RAH3-PR-001` §2.3 -- the non-copy capture site, and the proof that each invariant can go RED.

WHY THIS FILE EXISTS. `RAH2-C-020` retracted that phase's positive result on one fact: the donor was
captured at the CONCEPT'S OWN SURFACE TOKEN, so "transport" and "copying" were indistinguishable.
`RAH3` makes that distinction a property of the instrument. Every invariant below therefore has a
paired `MUTANT_` test that constructs the violating input and asserts the code REFUSES -- because a
guard that has never been observed failing is not a guard (`RAH2-C-023`: a mutation chosen for
maximum headroom proves only that the harness runs).

⚠ `test_default_capture_mode_is_surface_and_offset_is_zero` is load-bearing beyond this sprint: if
the default ever changes, every artifact in `outputs/boombness/rah_preflight/` becomes
non-reproducible without anything erroring.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "boombness"))
import rah_preflight_transport as pf  # noqa: E402


class _Tok:
    """Decode-only stub. Mirrors the real tokenizer's contract for the pure resolver."""
    def __init__(self, pieces): self.pieces = pieces
    def decode(self, ids): return self.pieces[ids[0]]


def _fixture(pieces):
    """Build (text, ids, offsets, tok) from a token-piece list, exactly as a BPE tokenizer would:
    concatenation is the text and each token owns a contiguous character span including its leading
    space. Reproduces the real segmentation observed on both models."""
    text, offsets = "", []
    for p in pieces:
        offsets.append((len(text), len(text) + len(p)))
        text += p
    ids = list(range(len(pieces)))
    return text, ids, offsets, _Tok({i: p for i, p in enumerate(pieces)})


#: the REAL trailer, verified identical on Llama-3.1-8B and Qwen3-14B and on both banks by
#: outputs/boombness/rah_preflight/rah3_capture_site_probe.json (8 donors x 2 models x 2 pairs).
TRAILER = [".", " given", " the", " context", "."]
PIECES = [" A", " carrot", " is", " nearby", ".", " build", " a", " bomb"] + TRAILER
ANCHOR = PIECES.index(" bomb")
LABELS = {"bomb": 7, "carrot": 1, "knife": 900, "ticket": 901}


def _resolve(pieces=PIECES, mode="offset", off=1, concept="bomb", codeword="carrot",
             labels=None):
    text, ids, offsets, tok = _fixture(pieces)
    return pf.resolve_donor_capture(tok, ids, offsets, text, concept, codeword,
                                    LABELS if labels is None else labels, mode, off, "T")


# --------------------------------------------------------------------------------------------- #
# the default -- historical reproduction
# --------------------------------------------------------------------------------------------- #
def test_default_capture_mode_is_surface_and_offset_is_zero():
    """Pins the CLI default. A silent change here invalidates every prior artifact."""
    import argparse
    src = open(pf.__file__, encoding="utf-8").read()
    assert '"--capture-mode", default="surface"' in src
    assert '"--capture-offset", type=int, default=0' in src
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture-mode", default="surface", choices=["surface", "offset"])
    ap.add_argument("--capture-offset", type=int, default=0)
    a = ap.parse_args([])
    assert (a.capture_mode, a.capture_offset) == ("surface", 0)


def test_surface_path_resolves_exactly_where_the_historical_two_lines_did():
    """Bit-identity of the DEFAULT path against the pre-RAH3 inline code, on the same input."""
    text, ids, offsets, tok = _fixture(PIECES)
    pos_c = text.lower().rfind("bomb")
    historical = pf.token_index_covering(offsets, pos_c, pos_c + len("bomb"))
    rec = _resolve(mode="surface", off=0)
    assert rec["donor_tok_idx"] == historical == ANCHOR
    assert rec["donor_piece"] == " bomb"
    assert rec["overlaps_concept_surface"] is True     # the copy site, correctly flagged as such


def test_MUTANT_surface_mode_refuses_a_nonzero_offset():
    with pytest.raises(SystemExit, match="forbids a non-zero offset"):
        _resolve(mode="surface", off=1)


def test_MUTANT_offset_mode_refuses_offset_zero():
    """offset=0 is the surface path in disguise -- a COPY test labelled a non-copy control."""
    with pytest.raises(SystemExit, match="surface path in disguise"):
        _resolve(mode="offset", off=0)


# --------------------------------------------------------------------------------------------- #
# the registered site: N = +1
# --------------------------------------------------------------------------------------------- #
def test_registered_offset_plus_one_is_structurally_valid():
    rec = _resolve(off=1)
    assert rec["donor_piece"] == "."
    assert rec["donor_tok_idx"] == ANCHOR + 1
    assert rec["concept_tok_idx"] == ANCHOR
    assert rec["tok_distance_from_concept"] == 1
    assert rec["overlaps_concept_surface"] is False
    assert rec["overlaps_codeword_surface"] is False
    assert rec["is_candidate_label"] is False
    assert rec["candidate_matches"] == []
    assert rec["capture_mode"] == "offset" and rec["capture_offset"] == 1


def test_codeword_token_index_is_recorded_and_is_None_when_absent():
    assert _resolve(off=1)["codeword_tok_idx"] == PIECES.index(" carrot")
    assert _resolve(off=1, codeword="absentword")["codeword_tok_idx"] is None


# --------------------------------------------------------------------------------------------- #
# every non-copy invariant, each proven RED
# --------------------------------------------------------------------------------------------- #
def test_concept_overlap_at_a_POSITIVE_offset_is_UNREACHABLE_by_construction():
    """A structural fact worth pinning, discovered by trying to mutate this guard red and failing.

    Two earlier attempts did NOT raise the NON-COPY violation:
      * `[' bomb', ' bomb']` -- `rfind` anchors on the LAST occurrence, so a duplicate AFTER the
        anchor is unreachable at +1;
      * `[' bomb', ' bombard']` -- 'bomb' inside ' bombard' is at a LATER character position, so
        `rfind` selects THAT, and the ANCHOR assertion fires first with a different message.

    So at a POSITIVE offset the concept-overlap branch cannot be reached: any concept characters
    downstream of the anchor would have BEEN the anchor. The branch is still live and is proven RED
    at a negative offset by the next test. ⚠ Recorded rather than forced -- a mutation contrived
    until it goes red proves nothing (`RAH2-C-023`)."""
    pieces = [" build", " a", " bomb", " bombard"] + TRAILER
    with pytest.raises(SystemExit, match="anchor: token .* is not a piece of"):
        _resolve(pieces=pieces, off=1)


def test_MUTANT_capture_landing_on_a_concept_SUBTOKEN_RAISES():
    """Multi-piece concept: ' bo'+'mb'. rfind anchors on the LAST piece, but a NEGATIVE offset
    lands on the first -- still the concept surface, still a copy."""
    pieces = [" build", " a", " bo", "mb"] + TRAILER
    with pytest.raises(SystemExit, match="NON-COPY VIOLATION.*CONCEPT"):
        _resolve(pieces=pieces, off=-1)


def test_MUTANT_capture_landing_on_the_codeword_surface_RAISES():
    pieces = [" build", " a", " bomb", " carrot"] + TRAILER
    with pytest.raises(SystemExit, match="NON-COPY VIOLATION.*CODEWORD"):
        _resolve(pieces=pieces, off=1)


def test_MUTANT_capture_landing_on_a_candidate_label_by_TOKEN_ID_RAISES():
    """The id is what the readout scores, so an id match supplies the answer even when the decoded
    string looks innocuous. A string-only check would MISS this."""
    pieces = [" build", " a", " bomb", " knife"] + TRAILER
    labels = {"bomb": PIECES.index(" bomb"), "carrot": 1, "knife": 3, "ticket": 901}
    with pytest.raises(SystemExit, match="NON-COPY VIOLATION.*candidate label"):
        _resolve(pieces=pieces, off=1, labels=labels)


def test_MUTANT_capture_out_of_bounds_RAISES():
    with pytest.raises(SystemExit, match="outside"):
        _resolve(off=999)
    with pytest.raises(SystemExit, match="outside"):
        _resolve(off=-999)


def test_MUTANT_whitespace_capture_token_RAISES():
    pieces = [" build", " a", " bomb", "   "] + TRAILER
    with pytest.raises(SystemExit, match="whitespace"):
        _resolve(pieces=pieces, off=1)


def test_MUTANT_absent_concept_surface_RAISES():
    with pytest.raises(SystemExit, match="absent from templated donor"):
        _resolve(off=1, concept="notinthetext")


def test_MUTANT_unknown_capture_mode_RAISES():
    with pytest.raises(SystemExit, match="unknown capture_mode"):
        _resolve(mode="offsett", off=1)


# --------------------------------------------------------------------------------------------- #
# cross-row consistency (§9: "offset produces inconsistent semantics across rows")
# --------------------------------------------------------------------------------------------- #
def test_capture_consistency_accepts_identical_rows():
    rows = [{"donor_piece": ".", "tok_distance_from_concept": 1} for _ in range(8)]
    assert pf.assert_capture_consistent(rows) == {"n_rows": 8, "donor_piece": ".",
                                                  "tok_distance": 1}


def test_MUTANT_capture_consistency_RAISES_on_one_divergent_piece():
    """One row out of eight landing elsewhere means the offset denotes two different structural
    positions, and averaging over them would be silent."""
    rows = [{"donor_piece": ".", "tok_distance_from_concept": 1} for _ in range(7)]
    rows.append({"donor_piece": " given", "tok_distance_from_concept": 1})
    with pytest.raises(SystemExit, match="INCONSISTENT capture"):
        pf.assert_capture_consistent(rows)


def test_MUTANT_capture_consistency_RAISES_on_divergent_distance():
    rows = [{"donor_piece": ".", "tok_distance_from_concept": 1} for _ in range(7)]
    rows.append({"donor_piece": ".", "tok_distance_from_concept": 2})
    with pytest.raises(SystemExit, match="INCONSISTENT capture"):
        pf.assert_capture_consistent(rows)


def test_MUTANT_capture_consistency_RAISES_on_zero_rows():
    """A run with no donors must not report a vacuous PASS."""
    with pytest.raises(SystemExit, match="no donor rows"):
        pf.assert_capture_consistent([])


# --------------------------------------------------------------------------------------------- #
# char-span helper
# --------------------------------------------------------------------------------------------- #
def test_char_spans_finds_every_occurrence_case_insensitively():
    assert pf._char_spans("a Bomb and a bomb", "bomb") == [(2, 6), (13, 17)]
    assert pf._char_spans("nothing here", "bomb") == []


def test_provenance_gains_the_rah3_fields():
    """§37: branch, python executable, bank sha, expected/actual n are written by main(); the
    helpers they come from must at least exist and not raise."""
    assert pf._git_branch() is None or isinstance(pf._git_branch(), str)
    assert pf._diff_sha256() is None or len(pf._diff_sha256()) == 64
    assert len(pf.sha256_file(pf.__file__)) == 64


# --------------------------------------------------------------------------------------------- #
# `RAH3-C-003` -- MASS_GATE was a DEAD LITERAL and is now applied
# --------------------------------------------------------------------------------------------- #
def test_MASS_GATE_is_a_real_constant_and_distinct_from_the_positive_control_threshold():
    """⚠ Before `RAH3-C-003` the value 0.05 was written into every artifact as `mass_gate` and read
    by NO code path. The two thresholds are different numbers for different purposes
    (`RAH2-C-027`)."""
    assert pf.MASS_GATE == 0.05
    assert pf.POSITIVE_CONTROL_THRESH == 0.1
    assert pf.MASS_GATE != pf.POSITIVE_CONTROL_THRESH


def test_mass_gate_is_APPLIED_ON_THE_PRODUCTION_PATH_not_merely_persisted():
    """§49 production-path wiring: the tested function must be the one `main()` actually calls, or
    the guard tests a helper nothing uses."""
    src = open(pf.__file__, encoding="utf-8").read()
    assert '"mass_gate_ok": cell_mass_gate_ok(best["option_mass_mean"])' in src
    # the dead literal must survive ONLY in the comment that documents it as a defect
    code = [ln for ln in src.splitlines()
            if '"mass_gate": 0.05' in ln and not ln.lstrip().startswith("#")]
    assert code == [], "the dead literal is back on a code line: %r" % code


def test_cell_mass_gate_ok_boundary_and_the_historical_floor():
    assert pf.cell_mass_gate_ok(0.05) is True          # >= , not >
    assert pf.cell_mass_gate_ok(0.0499) is False
    # the Track-A precedent that passed straight through an unenforced gate
    assert pf.cell_mass_gate_ok(6.96e-08) is False


# --------------------------------------------------------------------------------------------- #
# `RAH3-C-004` -- a patch that never applied must not be scored as a scientific null
# --------------------------------------------------------------------------------------------- #
def test_run_with_a_live_patch_passes():
    cells = [{"n_patch_changed_at_best": 8} for _ in range(20)]
    assert pf.assert_run_not_vacuous(cells) == {"n_cells": 20, "n_cells_with_a_live_patch": 20}


def test_MUTANT_run_where_the_patch_NEVER_changed_anything_RAISES():
    """The exact H9 failure: `LayerPatch` silently skips an out-of-range position, every forward is
    really unpatched, and the grid reads as a clean negative."""
    cells = [{"n_patch_changed_at_best": 0} for _ in range(20)]
    with pytest.raises(SystemExit, match="VACUOUS"):
        pf.assert_run_not_vacuous(cells)


def test_MUTANT_empty_grid_RAISES_rather_than_reporting_a_vacuous_pass():
    with pytest.raises(SystemExit, match="no cells to check"):
        pf.assert_run_not_vacuous([])


def test_MUTANT_missing_liveness_counter_RAISES_rather_than_skipping_the_guard():
    """A missing key must FAIL, not be `.get(..., default)`-ed into a pass."""
    with pytest.raises(SystemExit, match="carry no patch-liveness counter"):
        pf.assert_run_not_vacuous([{"n_patch_changed_at_best": 8}, {"L": 3}])


def test_one_live_cell_out_of_many_is_enough_to_not_be_VACUOUS():
    """Deliberately weak: vacuity is about the INSTRUMENT, not about the effect. A grid where one
    cell responds is a real measurement with mostly-null cells, which is a legitimate result."""
    cells = [{"n_patch_changed_at_best": 0} for _ in range(19)] + [{"n_patch_changed_at_best": 1}]
    assert pf.assert_run_not_vacuous(cells)["n_cells_with_a_live_patch"] == 1
