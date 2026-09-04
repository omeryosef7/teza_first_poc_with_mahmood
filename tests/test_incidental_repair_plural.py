"""`DCS-C-037` / `DCS-C-037b`: the incidental-collision repair must match what the DETECTOR matches,
on EVERY field the builder reads.

WHY THIS TEST EXISTS. Two bugs, one week apart in the same function:

  C-037   the detector matches `\\b{word}s?\\b` (singular OR plural) while the repair matched
          `\\b{word}\\b` (singular only). A plural collision was therefore DETECTED and could never
          be REPAIRED -- `prompt_families` refused forever, telling the caller to use a flag that
          could not work. Unreachable for the canonical banks, whose three collisions are singular.

  C-037b  the first fix reached `pool["sentences"]` and NOT `pool["dev"]` / `pool["heldout"]`,
          because those two branches differ by an `isinstance(x, str)` guard. That is the field that
          matters: `build_prompt` draws from `dev`/`heldout` while the DETECTOR reads `sentences`,
          so the detector saw a repaired pool and the builder used an unrepaired one. The defect
          reached a 12 992-row bank and was caught downstream by `resolve_occurrences`.

Both were silent-by-construction: nothing in the repo compared the two matchers, or compared the
field the guard reads against the field the builder reads. This test does both.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "boombness"))
import prompt_families as pf  # noqa: E402

WORD, ALT = "button", "switch"


def _pool(sentences):
    return {"domain": "d", "valence": "filler", "natural_word": "carrot",
            "sentences": list(sentences), "dev": list(sentences),
            "heldout": list(sentences), "n": len(sentences)}


def test_plural_is_repaired_on_every_field_the_builder_reads():
    """C-037b: `sentences` alone is not enough -- `build_prompt` reads `dev`/`heldout`."""
    pools = {"d|filler": _pool(["two stop buttons here", "one button there"])}
    out = pf.apply_incidental_repairs(pools, {WORD: ALT})
    for field in ("sentences", "dev", "heldout"):
        joined = " ".join(out["d|filler"][field]).lower()
        assert not re.search(rf"\b{WORD}s?\b", joined), f"{field} still carries a collision"


def test_number_is_carried_across_not_dropped():
    """`buttons` -> `switches`, never `switchs` and never a silent singularisation."""
    out = pf.apply_incidental_repairs({"d|filler": _pool(["two stop buttons here"])}, {WORD: ALT})
    got = out["d|filler"]["sentences"][0].lower()
    assert "switches" in got, got
    assert "switchs" not in got, got


def test_repair_matches_exactly_what_the_detector_matches():
    """The core of C-037: run the DETECTOR over the REPAIRED pools; it must find nothing.

    This is the invariant that was violated for both bugs, and it is stated in terms of the two
    functions rather than a regex, so it keeps holding if either implementation changes."""
    pools = {"d|filler": _pool(["a button", "two buttons", "BUTTONS shouted", "no collision here"])}
    assert pf.incidental_codeword_collisions(pools, WORD), "fixture must actually collide"
    repaired = pf.apply_incidental_repairs(pools, {WORD: ALT})
    assert pf.incidental_codeword_collisions(repaired, WORD) == [], \
        "the detector still fires on pools the repair claims to have fixed"


def test_a_pools_own_natural_word_is_never_rewritten():
    """Pre-existing contract, pinned so the plural change cannot loosen it: for `knife` the
    collision IS the concept, and a blanket replace would rewrite every harm pool into sentences
    about a peeler -- a bank that teaches nothing."""
    pools = {"d|harm": {"domain": "d", "valence": "harm", "natural_word": "knife",
                        "sentences": ["a knife and knives"], "n": 1}}
    out = pf.apply_incidental_repairs(pools, {"knife": "peeler"})
    assert "knife" in out["d|harm"]["sentences"][0], "rewrote a pool's OWN natural word"
