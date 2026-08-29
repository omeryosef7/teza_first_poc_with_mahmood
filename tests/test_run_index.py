"""`has this already been run?`, answered by configuration rather than by tag.

WHY. Two demonstrated costs, not a hypothetical. §12.21: I launched cap-640 reruns for three
populations whose configuration-identical runs already existed — 384 of 384 rows came back
byte-identical, so the compute bought nothing. §23: a peer nearly spent GPU on a cell measured four
days earlier, invisible because their note tracked the gap BY TAG while the data is organised by
(bank, model, arm).

The property that makes the tool work is that `tag` is EXCLUDED from the identity — indexing by tag
is the failure it exists to prevent. That is what these tests pin.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "boombness"))
import run_index as ri  # noqa: E402


def test_tag_is_NOT_part_of_the_identity():
    """⛔ THE CORE PROPERTY. If tag were in IDENTITY, two runs of the same experiment under
    different tags would never group, and the tool would reproduce the exact failure it exists for."""
    assert "tag" not in ri.IDENTITY
    assert "bank" in ri.IDENTITY and "arm" in ri.IDENTITY and "max_new" in ri.IDENTITY


def test_identity_ignores_tag_but_separates_a_real_config_difference():
    base = dict.fromkeys(ri.IDENTITY, "x")
    a = dict(base, tag="abL12_Bctrl", run="a")
    b = dict(base, tag="fuR12_Cctrl", run="b")
    assert ri.identity(a) == ri.identity(b), "differing tags must not split one experiment"
    c = dict(base, tag="a", arm="C_other")
    assert ri.identity(a) != ri.identity(c), "a real config difference must split"


def test_the_row_file_is_named_per_root():
    """retrieval_strength writes retrieval.jsonl; assuming results.jsonl reported 0 rows for it
    in the sibling guard (§12.29). Same trap, pinned here too."""
    assert ri.ROW_FILE["retrieval_strength"] == "retrieval.jsonl"
    assert ri.ROW_FILE["score_behavior"] == "results.jsonl"


def test_the_real_corpus_scans_and_carries_identity_fields():
    runs = ri.scan(["score_behavior"])
    assert len(runs) > 100, f"only {len(runs)} runs scanned; the corpus is larger"
    r = runs[0]
    for k in ("run", "done", "rows", "bank", "arm", "max_new"):
        assert k in r, f"scan() dropped {k}"


def test_the_known_duplicate_pair_groups_together():
    """The concrete instance: e6A_ticket_bomb and its cap-640 rerun are one experiment.

    Both DONE at 96 rows, identical bank/model/arm/cap. If these ever stop grouping, the identity
    has lost a field that matters.
    """
    runs = {r["run"]: r for r in ri.scan(["score_behavior"])}
    a = next((v for k, v in runs.items() if k.startswith("e6A_ticket_bomb_")), None)
    b = next((v for k, v in runs.items() if k.startswith("k640_lbA_ticket_bomb_")), None)
    if not (a and b):
        return                                   # artifacts pruned; nothing to assert
    assert ri.identity(a) == ri.identity(b), (
        "the documented duplicate pair no longer groups — identity has gained a spurious field")
