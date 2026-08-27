"""C-20: a rescue patch BELOW the knockout band is a no-op by construction, not a control.

The knockout masks attention inside a band [lo, hi]. Layers below `lo` are untouched, so the
knocked-out run's PROMPT-position activations there are bit-identical to the clean run's. A
`DonorPatch` that writes clean donor activations at such a layer therefore writes the value that is
already present: `rescue_liveness` reports `fired: true` and the generations do not change.

Measured 2026-08-26/27 on four independent arms -- two models, two position modes, three sessions --
every one byte-identical to its own session's knockout-only arm, while every IN-band arm differed.

C9, C11 and C12 each published this arm as a layer-specificity control. It cannot serve as one.

⚠ WHAT THIS FILE IS, AND IS NOT (added after mutation-testing it, C-26).
It encodes a RULE. It is NOT a regression guard, and it must not be counted as one: the predicate it
checks is defined in this file, so it passes even when `donor_patch.py` is broken (verified — renaming
`DonorPatch.liveness` leaves all of these green). Run directories are gitignored, so the empirical
fact behind the rule (L5/L7 byte-identical to their control, L12/L17 not) cannot be pinned here.

Its value is that it stops the rule being RE-DERIVED WRONG — twice already: C-20 first wrote it as
"below the band", then R-68 measured the band FLOOR to be vacuous too and corrected it to `layer > lo`.
The production code is covered by tests/test_donor_patch.py, which exercises the real DonorPatch
(strict_ids, write, liveness, hook teardown). The one binding assertion below fails if that API
disappears, so the rule cannot outlive the thing it describes in silence.
"""

import pytest


def band_of(model):
    """The knockout bands this phase actually used."""
    return {"Qwen/Qwen3-14B": (7, 17), "meta-llama/Llama-3.1-8B-Instruct": (6, 14)}[model]


def patch_can_differ_from_recipient(model, rescue_layer, positions="prompt"):
    """True iff a clean-donor patch at `rescue_layer` can change the computation.

    Only prompt positions are considered: those are what `--rescue-positions demo|query` select.
    """
    lo, _hi = band_of(model)
    if positions != "prompt":
        raise ValueError("only prompt positions are modelled here")
    # STRICTLY greater than `lo`, not `>=`. Measured 2026-08-27: a patch at L7 with the band at
    # 7-17 is byte-identical to knockout-only on 160/160 rows, exactly like the below-band L5 arm.
    # `DonorPatch` writes the residual stream ENTERING block `rescue_layer`, i.e. the output of
    # block rescue_layer-1. Blocks lo..hi have knocked-out attention, so the input to block `lo`
    # is the output of block lo-1 and is unaffected -- patching there writes what is already
    # present. The first layer at which a clean donor can differ is therefore lo+1.
    return rescue_layer > lo


@pytest.mark.parametrize("model", ["Qwen/Qwen3-14B", "meta-llama/Llama-3.1-8B-Instruct"])
def test_below_band_patch_is_vacuous(model):
    lo, _ = band_of(model)
    for layer in range(0, lo):
        assert not patch_can_differ_from_recipient(model, layer), (
            f"{model} L{layer} is below the knockout band {band_of(model)}; a clean-donor patch "
            f"there writes what is already present and cannot serve as a specificity control")


@pytest.mark.parametrize("model,layer", [("Qwen/Qwen3-14B", 5), ("meta-llama/Llama-3.1-8B-Instruct", 5)])
def test_the_specific_layer_that_was_published_as_a_control(model, layer):
    """L5 is the exact layer C9/C11/C12 cited. It is below both bands."""
    assert not patch_can_differ_from_recipient(model, layer)


@pytest.mark.parametrize("model,layer", [("Qwen/Qwen3-14B", 8), ("Qwen/Qwen3-14B", 12),
                                         ("Qwen/Qwen3-14B", 17),
                                         ("meta-llama/Llama-3.1-8B-Instruct", 7),
                                         ("meta-llama/Llama-3.1-8B-Instruct", 14)])
def test_patches_above_the_band_floor_are_real_interventions(model, layer):
    """Only lo+1 and above can change the computation. Verified: Qwen3 L17 -> 4/160 identical."""
    assert patch_can_differ_from_recipient(model, layer)


@pytest.mark.parametrize("model,layer", [("Qwen/Qwen3-14B", 7), ("meta-llama/Llama-3.1-8B-Instruct", 6)])
def test_the_band_floor_itself_is_vacuous(model, layer):
    """The trap that caught C-20's own first replacement control.

    `rescue_layer == lo` LOOKS in-band and reads as a sound specificity control. It is not:
    q9_qpos_L7 (band 7-17) came back 160/160 byte-identical to its same-session knockout-only arm,
    exactly like the below-band L5 arm it was meant to replace.
    """
    assert not patch_can_differ_from_recipient(model, layer)


def test_the_rule_has_something_to_describe():
    """The one assertion here that touches production code.

    The rule above is a statement ABOUT `DonorPatch`: that it writes the residual stream entering a
    block, and that it reports firing whether or not the write changed anything (C-20). If that class
    or its liveness contract disappears, the rule is describing nothing and this file should fail
    rather than keep passing quietly.
    """
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    "src", "boombness"))
    import donor_patch
    assert hasattr(donor_patch, "DonorPatch"), "DonorPatch is gone; the rule describes nothing"
    assert hasattr(donor_patch.DonorPatch, "liveness"), (
        "DonorPatch.liveness is gone — C-20's whole point is that this field reports `fired: true` "
        "for a write that changed nothing, so the rule is meaningless without it")
