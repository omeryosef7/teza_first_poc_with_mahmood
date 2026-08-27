"""C-20: a rescue patch BELOW the knockout band is a no-op by construction, not a control.

The knockout masks attention inside a band [lo, hi]. Layers below `lo` are untouched, so the
knocked-out run's PROMPT-position activations there are bit-identical to the clean run's. A
`DonorPatch` that writes clean donor activations at such a layer therefore writes the value that is
already present: `rescue_liveness` reports `fired: true` and the generations do not change.

Measured 2026-08-26/27 on four independent arms -- two models, two position modes, three sessions --
every one byte-identical to its own session's knockout-only arm, while every IN-band arm differed.

C9, C11 and C12 each published this arm as a layer-specificity control. It cannot serve as one. This
test stops a below-band layer being described as a control again, by asserting the rule that makes it
vacuous rather than by re-reading run directories (which are not part of the repo).
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
