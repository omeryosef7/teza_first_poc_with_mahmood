"""Phase-F1.3 probe DRIVER — CPU orchestration around the verified numeric core.

Design source (FIXED): ``docs/COT_HIJACKING_EXACT_MECHANISM_REPORT.md`` §6.1a–§6.4.

This module turns F1.1 span-annotation records (``*_spans.jsonl``, §2) into the
``per_record`` list that :func:`scripts.phase_f_attention_probe.success_failure_contrast`
consumes, and drives the full DISCOVERY-split attention-to-span contrast (§6.2)
end to end. The model forward pass is INJECTED as a callable ``forward_fn`` — the
ONLY model touchpoint — so every function here is CPU-only, torch-free at import,
and fully unit-testable with a mocked forward. No model is wired here; that is a
later main-loop step.

Safety contract (F1.3 scope). Only NUMERIC / BOOLEAN / STRUCTURAL fields of the
span records ever enter this module. :func:`load_records` is the SOLE file reader;
it SANITIZES each record at parse time, explicitly dropping the top-level ``goal``
and every span instance's ``preview`` so no harmful text can reach any downstream
function. ``task_id`` is retained only as an opaque id string for the
deterministic discovery/test hash and is NEVER printed or stored in outputs.

GPU note (documentation only; NOT implemented here). In production ``forward_fn``
is a main-loop closure over
:func:`scripts.phase_f_attention_probe.extract_attention_for_record` — the
``require_gpu`` stub which loads the target model (reusing
``poc_stage4/qwen3_model.py`` templating) and runs a single clean forward pass
with ``output_attentions=True`` under ``torch.no_grad()``, stacking the per-layer
attention tuples into a ``[n_layers, n_heads, n_q, n_k]`` numpy array. That
closure is wired during Phase-F1.3 GPU execution (blocked on a non-competing L40S
slot); it is intentionally NOT constructed in this module, which stays torch-free.
"""

from __future__ import annotations

import csv
import hashlib
import json
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from scripts.phase_f_attention_probe import (
    attention_mass_to_spans,
    success_failure_contrast,
    top_k_heads_by_abs_delta,
)

# A half-open [tok_start, tok_end) token-index range.
Range = Tuple[int, int]

# §6.2 primary cross-outcome components (present in BOTH splits) PLUS the
# failure-only ``injected_reasoning`` refusal probe (§6.1a).
DEFAULT_COMPONENTS: List[str] = [
    "benign_puzzle_scaffold",
    "harmful_instruction",
    "final_answer_cue",
    "injected_reasoning",
]

# Fallback query-window width when ``final_answer_cue`` is absent/unlocated (§6.2).
_FALLBACK_QUERY_WINDOW = 32


def _located_instances(record: Dict, component: str) -> List[Dict]:
    """Return a component's instance dicts iff it is present AND ``located``.

    Reads only the structural ``located`` flag and the instance list; never any
    text field. Missing component or ``located == False`` → empty list.
    """
    spans = record.get("spans") or {}
    comp = spans.get(component) or {}
    if not comp.get("located"):
        return []
    return list(comp.get("instances") or [])


def _instance_range(inst: Dict) -> Optional[Range]:
    """Half-open ``(tok_start, tok_end)`` for one instance, or None if unusable.

    Only integer token fields are read. Instances whose token indices are absent
    (``None``, e.g. a char span that mapped to no token) or degenerate
    (``tok_end <= tok_start``) are skipped.
    """
    ts = inst.get("tok_start")
    te = inst.get("tok_end")
    if ts is None or te is None:
        return None
    ts, te = int(ts), int(te)
    if te <= ts:
        return None
    return (ts, te)


def query_positions_for_record(record: Dict) -> List[int]:
    """Query token positions to measure FROM, per §6.2.

    The queries are the generation / ``final_answer_cue`` positions: the UNION of
    the integer token indices covered by the ``final_answer_cue`` component's
    located instance ``[tok_start, tok_end)`` half-open ranges. If
    ``final_answer_cue`` is absent or unlocated, fall back to the LAST
    ``_FALLBACK_QUERY_WINDOW`` (=32) token positions of the sequence,
    ``range(max(0, n_tokens - 32), n_tokens)``.

    Never reads text. Returns a sorted list of distinct positions.
    """
    positions: set[int] = set()
    for inst in _located_instances(record, "final_answer_cue"):
        rng = _instance_range(inst)
        if rng is not None:
            positions.update(range(rng[0], rng[1]))
    if positions:
        return sorted(positions)
    # Fallback: last 32 positions of the sequence.
    n_tokens = int(record.get("n_tokens") or 0)
    return list(range(max(0, n_tokens - _FALLBACK_QUERY_WINDOW), n_tokens))


def span_ranges_for_record(
    record: Dict,
    components: Optional[Sequence[str]] = None,
) -> Dict[str, List[Range]]:
    """Map each requested component to its located instances' token ranges.

    For every component in ``components`` (default :data:`DEFAULT_COMPONENTS`),
    return the list of ``(tok_start, tok_end)`` half-open ranges of its located
    instances, or an empty list when the component is absent/unlocated or none of
    its instances carry usable integer token indices. Only structural/integer
    fields are read.
    """
    if components is None:
        components = DEFAULT_COMPONENTS
    out: Dict[str, List[Range]] = {}
    for comp in components:
        ranges: List[Range] = []
        for inst in _located_instances(record, comp):
            rng = _instance_range(inst)
            if rng is not None:
                ranges.append(rng)
        out[comp] = ranges
    return out


def component_token_length(record: Dict, component: str) -> int:
    """Total token length covered by ``component``'s located instance ranges.

    Sums ``tok_end - tok_start`` over every located instance of ``component``
    (reusing :func:`span_ranges_for_record`, which already applies the
    ``located`` gate and skips degenerate/unmapped ranges). Returns ``0`` when
    the component is absent, unlocated, or carries no usable integer token
    indices. Purely structural — reads only integer token indices, never text.

    Note: overlapping instances are summed independently (no de-duplication);
    this is the raw scaffold TOKEN-LENGTH used later to test the length/structure
    CONFOUND, distinct from the UNION-based key mask used for attention mass.
    """
    ranges = span_ranges_for_record(record, [component])[component]
    return sum(int(te) - int(ts) for (ts, te) in ranges)


def build_per_record(
    records: Sequence[Dict],
    forward_fn: Callable[[Dict], np.ndarray],
    components: Optional[Sequence[str]] = None,
) -> List[Dict]:
    """Build the ``per_record`` list for :func:`success_failure_contrast`.

    For each record: obtain its attention tensor via the INJECTED ``forward_fn``
    (``attn = forward_fn(record)``; returns a numpy array of shape
    ``[n_layers, n_heads, n_q, n_k]``), compute per-(layer, head) attention mass
    into each component's key spans with
    :func:`scripts.phase_f_attention_probe.attention_mass_to_spans`, and emit
    ``{"is_success": record["is_success"], "masses": masses}``.

    ``forward_fn`` is the ONLY model touchpoint — mocked in tests, a real GPU
    forward closure in production (see module docstring).
    """
    if components is None:
        components = DEFAULT_COMPONENTS
    per_record: List[Dict] = []
    for record in records:
        attn = forward_fn(record)
        if attn is None:
            # forward_fn signalled a RECOVERABLE per-record failure (e.g. missing
            # attack_prompt or a tokenizer/template alignment mismatch it chose to skip
            # rather than raise). Drop this record so one bad row can't kill the batch;
            # the runner is responsible for logging the reason.
            continue
        masses = attention_mass_to_spans(
            attn,
            query_positions_for_record(record),
            span_ranges_for_record(record, components),
        )
        per_record.append(
            {"is_success": record.get("is_success"), "masses": masses}
        )
    return per_record


def build_per_record_meta(
    records: Sequence[Dict],
    forward_fn: Callable[[Dict], np.ndarray],
    components: Optional[Sequence[str]] = None,
) -> List[Dict]:
    """Parallel to :func:`build_per_record`, carrying CONFOUND-test metadata.

    Identical forward/mass computation as :func:`build_per_record`, but each
    emitted entry additionally carries the record's ``n_tokens`` and the
    per-component located token-lengths (``comp_lens``) so a later analysis can
    regress per-record attention mass on scaffold token-length within
    success/failure groups. Returns
    ``[{"is_success", "n_tokens", "masses", "comp_lens"}]``.

    This does NOT replace :func:`build_per_record` (whose return keys are left
    untouched); it is the parallel path used only when a per-record CSV is
    requested. ``forward_fn`` is again the ONLY model touchpoint. A ``forward_fn``
    that returns ``None`` for a record signals a recoverable per-record failure
    and that record is dropped (same policy as :func:`build_per_record`).
    """
    if components is None:
        components = DEFAULT_COMPONENTS
    per_record: List[Dict] = []
    for record in records:
        attn = forward_fn(record)
        if attn is None:
            continue
        masses = attention_mass_to_spans(
            attn,
            query_positions_for_record(record),
            span_ranges_for_record(record, components),
        )
        comp_lens = {
            comp: component_token_length(record, comp) for comp in components
        }
        per_record.append(
            {
                "is_success": record.get("is_success"),
                "n_tokens": record.get("n_tokens"),
                "masses": masses,
                "comp_lens": comp_lens,
            }
        )
    return per_record


def write_per_record_csv(
    per_record_full: Sequence[Dict],
    components: Sequence[str],
    out_csv: str,
) -> None:
    """Write the PER-RECORD long-format CSV for the length/structure confound test.

    ``per_record_full`` is the output of :func:`build_per_record_meta` (each entry
    ``{"is_success", "n_tokens", "masses", "comp_lens"}``) and ``components`` is
    the ordered component list to emit. For every (record, layer, component) a row
    is written, giving ``len(per_record_full) × n_layers × len(components)`` rows.

    Columns:

    * ``record_index``  — anonymous 0-based position in ``per_record_full``. This
      is NEVER ``task_id`` (or any id/text); it exists only to group a record's
      rows. Records carry no identifying field into this CSV.
    * ``is_success``    — bool of that record's outcome.
    * ``n_tokens``      — total sequence token count of that record.
    * ``component``     — component name.
    * ``layer``         — attention layer index.
    * ``mean_mass_over_heads`` — mean over that layer's heads of the record's
      attention mass into ``component`` (``0.0`` for heads that reported no mass).
    * ``component_tok_len``    — located token-length of ``component`` for that
      record (from :func:`component_token_length`, via ``comp_lens``).

    Safety: only numeric/boolean/structural values are written; no ``goal``,
    ``preview``, ``task_id`` or any text ever reaches this file.
    """
    # Deterministic sorted union of layer indices across all records' masses.
    layers: set[int] = set()
    for entry in per_record_full:
        for (layer, _head) in (entry.get("masses") or {}).keys():
            layers.add(int(layer))
    sorted_layers = sorted(layers)

    fieldnames = [
        "record_index",
        "is_success",
        "n_tokens",
        "component",
        "layer",
        "mean_mass_over_heads",
        "component_tok_len",
    ]
    rows: List[Dict] = []
    for record_index, entry in enumerate(per_record_full):
        masses = entry.get("masses") or {}
        comp_lens = entry.get("comp_lens") or {}
        # Group per-head masses by layer once for this record.
        by_layer: Dict[int, List[Dict[str, float]]] = {}
        for (layer, _head), comp_map in masses.items():
            by_layer.setdefault(int(layer), []).append(comp_map)
        for layer in sorted_layers:
            head_maps = by_layer.get(layer, [])
            for comp in components:
                if head_maps:
                    vals = [float(cm.get(comp, 0.0)) for cm in head_maps]
                    mean_mass = float(np.mean(vals))
                else:
                    mean_mass = 0.0
                rows.append(
                    {
                        "record_index": record_index,
                        "is_success": bool(entry.get("is_success")),
                        "n_tokens": int(entry.get("n_tokens") or 0),
                        "component": comp,
                        "layer": layer,
                        "mean_mass_over_heads": mean_mass,
                        "component_tok_len": int(comp_lens.get(comp, 0)),
                    }
                )
    with open(out_csv, "w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def discovery_test_split(
    records: Sequence[Dict],
    frac: float = 0.5,
) -> Tuple[List[Dict], List[Dict]]:
    """Deterministic discovery/test split by a stable hash of ``task_id`` (§6.0).

    A record goes to DISCOVERY iff
    ``int(md5(task_id).hexdigest()[:8], 16) % 100 < frac * 100`` and to TEST
    otherwise. Splitting on ``task_id`` (never on row index) guarantees a behavior
    never appears in both halves. Fully deterministic — no RNG, no wall clock.
    ``task_id`` is used only as an opaque hash key and is never printed.

    Records with a missing/empty ``task_id`` are routed to TEST (they cannot be
    stably assigned to discovery).
    """
    threshold = frac * 100
    discovery: List[Dict] = []
    test: List[Dict] = []
    for record in records:
        task_id = record.get("task_id")
        if not task_id:
            test.append(record)
            continue
        digest = hashlib.md5(str(task_id).encode()).hexdigest()
        bucket = int(digest[:8], 16) % 100
        if bucket < threshold:
            discovery.append(record)
        else:
            test.append(record)
    return discovery, test


def load_records(spans_path: str) -> List[Dict]:
    """Read a ``*_spans.jsonl`` and return SANITIZED, text-free record dicts.

    This is the ONLY file reader in the driver and the single choke point for the
    F1.3 safety contract: harmful text is dropped AT PARSE so nothing downstream
    can touch it. For each JSONL line, only these fields are copied through:

    * ``is_success`` (bool), ``n_tokens`` (int), ``target_model`` (str),
    * ``task_id`` (opaque id string — kept for the split hash, never printed),
    * ``spans``: for each component only ``located`` (bool) and, per instance,
      the four integer token/char indices ``char_start``/``char_end``/
      ``tok_start``/``tok_end``.

    The top-level ``goal`` and every span instance's ``preview`` are NEVER read
    or copied (``preview`` is simply not among the whitelisted instance keys, and
    ``goal`` is explicitly ``pop``-ed as a belt-and-braces guard).
    """
    records: List[Dict] = []
    with open(spans_path, "r", encoding="utf-8") as fin:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            # Belt-and-braces: never let the harmful goal survive parsing.
            raw.pop("goal", None)

            clean_spans: Dict[str, Dict] = {}
            for comp, comp_val in (raw.get("spans") or {}).items():
                comp_val = comp_val or {}
                clean_instances: List[Dict] = []
                for inst in comp_val.get("instances") or []:
                    # Whitelist ONLY the four integer index fields; `preview` is
                    # deliberately excluded so no harmful text is ever copied.
                    clean_instances.append(
                        {
                            "char_start": inst.get("char_start"),
                            "char_end": inst.get("char_end"),
                            "tok_start": inst.get("tok_start"),
                            "tok_end": inst.get("tok_end"),
                        }
                    )
                clean_spans[comp] = {
                    "located": bool(comp_val.get("located")),
                    "instances": clean_instances,
                }

            records.append(
                {
                    "is_success": raw.get("is_success"),
                    "n_tokens": raw.get("n_tokens"),
                    "target_model": raw.get("target_model"),
                    "task_id": raw.get("task_id"),
                    # integer join keys (safe, non-text) so a GPU forward_fn can map each
                    # record back to its attack_prompt in the ORIGINAL attacked jsonl: the
                    # tuple (task_id, conversation_id, attack_iteration) is unique per record
                    # whereas task_id alone is not (multiple attack_iterations per behavior).
                    "conversation_id": raw.get("conversation_id"),
                    "attack_iteration": raw.get("attack_iteration"),
                    "spans": clean_spans,
                }
            )
    return records


def run_probe(
    spans_path: str,
    forward_fn: Callable[[Dict], np.ndarray],
    out_csv: str,
    components: Optional[Sequence[str]] = None,
    top_k: int = 10,
    per_record_csv: Optional[str] = None,
) -> Dict:
    """Full DISCOVERY-split attention-to-span contrast (§6.2), end to end.

    Pipeline: :func:`load_records` (sanitized) → :func:`discovery_test_split`
    (DISCOVERY half only; the TEST half is reserved for F1.5 causal work) →
    :func:`build_per_record` with the injected ``forward_fn`` →
    :func:`success_failure_contrast` → :func:`top_k_heads_by_abs_delta` per
    component. Writes a tidy CSV with columns
    ``layer, head, component, succ_mean, fail_mean, delta, n_succ, n_fail`` (one
    row per (layer, head, component) that appears in the contrast) and returns
    ``{"contrast": ..., "top_heads": {component: [(layer, head), ...]}, "n_discovery": int, "n_test": int}``.
    """
    if components is None:
        components = DEFAULT_COMPONENTS

    records = load_records(spans_path)
    discovery, test = discovery_test_split(records)

    per_record = build_per_record(discovery, forward_fn, components)
    contrast = success_failure_contrast(per_record)

    top_heads: Dict[str, List[Tuple[int, int]]] = {
        comp: top_k_heads_by_abs_delta(contrast, comp, top_k) for comp in components
    }

    _write_contrast_csv(out_csv, contrast)

    # Optional parallel path: emit the per-record long-format CSV for the later
    # length/structure CONFOUND test. Recomputes masses via build_per_record_meta
    # over the SAME discovery split; the aggregate output above is unaffected.
    if per_record_csv is not None:
        per_record_full = build_per_record_meta(discovery, forward_fn, components)
        write_per_record_csv(per_record_full, list(components), per_record_csv)

    return {
        "contrast": contrast,
        "top_heads": top_heads,
        "n_discovery": len(discovery),
        "n_test": len(test),
    }


def _write_contrast_csv(
    out_csv: str,
    contrast: Dict[Tuple[int, int], Dict[str, Dict[str, float]]],
) -> None:
    """Write the tidy per-(layer, head, component) contrast CSV."""
    fieldnames = [
        "layer",
        "head",
        "component",
        "succ_mean",
        "fail_mean",
        "delta",
        "n_succ",
        "n_fail",
    ]
    # Deterministic ordering: (layer, head) ascending, then component name.
    rows: List[Dict] = []
    for (layer, head) in sorted(contrast.keys()):
        comp_map = contrast[(layer, head)]
        for comp in sorted(comp_map.keys()):
            stats = comp_map[comp]
            rows.append(
                {
                    "layer": layer,
                    "head": head,
                    "component": comp,
                    "succ_mean": stats["succ_mean"],
                    "fail_mean": stats["fail_mean"],
                    "delta": stats["delta"],
                    "n_succ": stats["n_succ"],
                    "n_fail": stats["n_fail"],
                }
            )
    with open(out_csv, "w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
