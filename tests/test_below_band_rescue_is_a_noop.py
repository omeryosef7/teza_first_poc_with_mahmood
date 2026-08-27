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
    return rescue_layer >= lo


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


@pytest.mark.parametrize("model,layer", [("Qwen/Qwen3-14B", 7), ("Qwen/Qwen3-14B", 17),
                                         ("meta-llama/Llama-3.1-8B-Instruct", 6),
                                         ("meta-llama/Llama-3.1-8B-Instruct", 14)])
def test_in_band_patches_are_real_interventions(model, layer):
    """C-20's replacement control patches the BOTTOM of the band, which is in-band and can fail."""
    assert patch_can_differ_from_recipient(model, layer)
