"""phase5_patch_spec.py — pure, GPU-free patch-spec builder for Phase-5 Q3/Q4.

This isolates the correctness-critical (and B9-prone) part of the per-example
component-patch harness: mapping a corpus example to the RIGHT row of the
per-example vector artifact (built by build_phase5_perexample) and emitting the
list of per-layer patches to apply. Kept free of torch/model so it can be fully
unit-tested; the GPU harness (built on greenlight) consumes `arm_patch_spec` and
wraps each entry in a dc.LayerPatch at the codeword position.

Sign convention:
  * necessity  (base = doublespeak prompt):  sign = -1  → SUBTRACT the example's
    own component, moving the doublespeak state toward the donor along that arm.
  * sufficiency (base = donor prompt):        sign = +1  → ADD the component,
    moving the donor state toward doublespeak.

Each spec entry is a dict {layer, vector(np.float32), mode:'add', alpha:sign}.
Using mode='add' with alpha=±1 and the pre-scaled per-example vector keeps the
dose identical to the natural per-example shift magnitude (on-manifold, §8.2) —
no separate gap rescale, unlike the mean-direction Phase-4 add arm.
"""
from __future__ import annotations
import numpy as np

VALID_ARMS = ("full", "bomb", "refusal", "remainder", "random")


def example_row_index(artifact, example_id):
    """Row of `example_id` in the artifact's example_ids, with a hard guard.

    Guards the absolute-position/index bug class (B9): the vector rows are ordered
    by artifact['example_ids']; a caller must look up by id, never reuse a corpus
    enumeration index. Raises if the id is absent."""
    ids = artifact["example_ids"]
    # build once-per-artifact map lazily and cache on the dict
    cache = artifact.get("_id2row")
    if cache is None:
        cache = {e: i for i, e in enumerate(ids)}
        artifact["_id2row"] = cache
    if example_id not in cache:
        raise KeyError(f"example_id {example_id!r} not in artifact "
                       f"({len(ids)} ids); cannot align patch vector")
    return cache[example_id]


def arm_patch_spec(artifact, arm, example_id, band=None, sign=-1):
    """Return [{layer, vector, mode, alpha}, ...] for one example and one arm.

    band defaults to the artifact's own layers. Only layers present in the arm are
    emitted. sign must be +1 (add / sufficiency) or -1 (subtract / necessity)."""
    if arm not in VALID_ARMS:
        raise ValueError(f"unknown arm {arm!r}; valid: {VALID_ARMS}")
    if sign not in (1, -1):
        raise ValueError("sign must be +1 (add) or -1 (subtract)")
    row = example_row_index(artifact, example_id)
    layers = artifact["layers"] if band is None else [L for L in band if L in artifact["layers"]]
    arm_by_layer = artifact["arms"][arm]
    spec = []
    for L in layers:
        if L not in arm_by_layer:
            continue
        vec = np.asarray(arm_by_layer[L][row], dtype=np.float32)
        spec.append({"layer": int(L), "vector": vec, "mode": "add", "alpha": float(sign)})
    return spec


def spec_norm(spec):
    """Total L2 magnitude of a spec (diagnostic / smoke sanity)."""
    return float(np.sqrt(sum(float(e["vector"] @ e["vector"]) for e in spec)))
