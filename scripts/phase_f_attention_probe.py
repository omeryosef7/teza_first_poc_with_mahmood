"""Phase-F1.3 computational core — CoT-hijacking attention-to-span measurement.

Design source (FIXED): ``docs/COT_HIJACKING_EXACT_MECHANISM_REPORT.md`` §6.1a + §6.2.

This module is the CPU-testable numeric CORE of F1.3. It is **pure math on
attention tensors + integer token ranges** — no text, no goal/preview strings,
and no model ever enter it. It operates only on numpy attention weights already
extracted upstream, plus integer half-open key-token ranges from the F1.1 span
annotation (§2 of the design report).

Per §6.2, for every (layer ℓ, head h) we measure the **attention mass directed
FROM the generation / ``final_answer_cue`` query positions TO each labelled
span's key-token range**, normalized by the query row's total attention. The
success−failure contrast ΔA[ℓ,h,comp] is the candidate mechanistic signal.

Per §6.1a the cross-outcome contrast is *direction-agnostic* and the primary
components (present in BOTH splits) are ``benign_puzzle_scaffold``,
``harmful_instruction`` and ``final_answer_cue``. ``injected_reasoning`` is
absent from successes (0% of successes vs 61–68% of failures), so attention INTO
it is a **failure-only** (candidate refusal) probe, not a success-contrast.

Import-time contract: this module is **torch-free**. ``torch`` is imported
LAZILY, only inside the GPU wrapper, which is a documented stub that is not run
or tested off-GPU (GPU execution is deferred to Phase-F1.3, blocked on a
non-competing L40S slot).
"""

from __future__ import annotations

from typing import Dict, List, Sequence, Tuple

import numpy as np

# A (layer, head) key.
LH = Tuple[int, int]
# A half-open [start, end) key-token range.
Range = Tuple[int, int]


# --------------------------------------------------------------------------- #
# Core: attention mass from query rows into labelled spans.
# --------------------------------------------------------------------------- #
def attention_mass_to_spans(
    attn: np.ndarray,
    query_positions: Sequence[int],
    span_token_ranges: Dict[str, Sequence[Range]],
    *,
    normalize: bool = True,
) -> Dict[LH, Dict[str, float]]:
    """Attention mass from ``query_positions`` into each component's key spans.

    Parameters
    ----------
    attn:
        numpy array of shape ``[n_layers, n_heads, n_q, n_k]`` holding attention
        weights (each query row over the ``n_k`` key positions sums to ~1).
    query_positions:
        Query indices to measure FROM (e.g. the ``final_answer_cue`` /
        generation token positions). Masses are aggregated by the MEAN over
        these query rows. Indices outside ``[0, n_q)`` are ignored.
    span_token_ranges:
        Mapping ``{component: [(tok_start, tok_end), ...]}`` of half-open
        ``[start, end)`` key-token ranges. A component may have multiple
        instances; their key tokens are UNIONed (never double-counted, even if
        the ranges overlap). Ranges are clipped to ``[0, n_k)``.
    normalize:
        If True (default), divide each component's summed mass by the total
        attention over ALL ``n_k`` keys for the (mean of the) selected query
        rows, yielding fractions in ``[0, 1]``. These need not sum to 1 across
        components because the components need not cover all keys. If False,
        return the raw summed attention mass.

    Returns
    -------
    dict
        Nested ``{(layer, head): {component: mass}}``. ``mass`` is the mean over
        ``query_positions`` of the summed attention into that component's key
        tokens (normalized per ``normalize``).

    Notes
    -----
    Graceful degenerate handling (never raises, never indexes out of bounds):

    * empty / all-invalid ``query_positions`` → every mass is ``0.0``;
    * a component with no ranges, or ranges fully outside ``[0, n_k)`` → ``0.0``;
    * ``normalize=True`` with zero total row attention → ``0.0``.

    Because summation is linear, the mean-over-queries of a per-row span sum
    equals the span sum of the mean-over-queries row; we therefore reduce the
    selected query rows to a single mean row per (ℓ, h) and sum over spans.
    """
    attn = np.asarray(attn)
    if attn.ndim != 4:
        raise ValueError(
            f"attn must be 4-D [n_layers, n_heads, n_q, n_k]; got shape {attn.shape}"
        )
    n_layers, n_heads, n_q, n_k = attn.shape

    components = list(span_token_ranges.keys())

    # Valid query rows (in-bounds), stable order.
    q_idx = [int(q) for q in query_positions if 0 <= int(q) < n_q]

    # Precompute a boolean key mask per component (union of clipped ranges).
    comp_masks: Dict[str, np.ndarray] = {}
    for comp in components:
        mask = np.zeros(n_k, dtype=bool)
        for (start, end) in span_token_ranges[comp]:
            s = max(0, int(start))
            e = min(n_k, int(end))
            if e > s:
                mask[s:e] = True
        comp_masks[comp] = mask

    out: Dict[LH, Dict[str, float]] = {}
    for layer in range(n_layers):
        for head in range(n_heads):
            comp_masses: Dict[str, float] = {}
            if not q_idx:
                # No valid query rows → all masses zero.
                for comp in components:
                    comp_masses[comp] = 0.0
                out[(layer, head)] = comp_masses
                continue

            # Mean attention row over the selected query positions: shape [n_k].
            mean_row = attn[layer, head, q_idx, :].mean(axis=0)
            total = float(mean_row.sum())
            denom = total if (normalize and total > 0.0) else None

            for comp in components:
                mask = comp_masks[comp]
                span_sum = float(mean_row[mask].sum()) if mask.any() else 0.0
                if normalize:
                    comp_masses[comp] = (span_sum / denom) if denom else 0.0
                else:
                    comp_masses[comp] = span_sum
            out[(layer, head)] = comp_masses
    return out


# --------------------------------------------------------------------------- #
# Contrast aggregation over records.
# --------------------------------------------------------------------------- #
def success_failure_contrast(
    per_record: List[Dict[str, object]],
) -> Dict[LH, Dict[str, Dict[str, float]]]:
    """Aggregate per-record span masses into a success−failure contrast.

    Parameters
    ----------
    per_record:
        List of records, each ``{"is_success": bool, "masses": {(layer, head):
        {component: mass}}}`` where ``masses`` is the output of
        :func:`attention_mass_to_spans` for one attacked output.

    Returns
    -------
    dict
        ``{(layer, head): {component: {"succ_mean", "fail_mean", "delta",
        "n_succ", "n_fail"}}}`` where ``delta = succ_mean - fail_mean``. For a
        given (ℓ, h, component), ``n_succ`` / ``n_fail`` count the success /
        failure records that actually reported a mass for it; means are taken
        over exactly those records, and default to ``0.0`` when the count is 0.

    This is pure aggregation over the numeric masses — no attention tensors.
    """
    # Accumulate mass lists split by outcome, keyed by (layer, head) -> comp.
    succ: Dict[LH, Dict[str, List[float]]] = {}
    fail: Dict[LH, Dict[str, List[float]]] = {}

    for rec in per_record:
        bucket = succ if bool(rec.get("is_success")) else fail
        masses = rec.get("masses") or {}
        for lh, comp_map in masses.items():
            slot = bucket.setdefault(lh, {})
            for comp, mass in comp_map.items():
                slot.setdefault(comp, []).append(float(mass))

    # Every (layer, head, component) that appears in either outcome.
    all_lh = set(succ) | set(fail)

    out: Dict[LH, Dict[str, Dict[str, float]]] = {}
    for lh in all_lh:
        s_comps = succ.get(lh, {})
        f_comps = fail.get(lh, {})
        comp_out: Dict[str, Dict[str, float]] = {}
        for comp in set(s_comps) | set(f_comps):
            s_vals = s_comps.get(comp, [])
            f_vals = f_comps.get(comp, [])
            succ_mean = float(np.mean(s_vals)) if s_vals else 0.0
            fail_mean = float(np.mean(f_vals)) if f_vals else 0.0
            comp_out[comp] = {
                "succ_mean": succ_mean,
                "fail_mean": fail_mean,
                "delta": succ_mean - fail_mean,
                "n_succ": len(s_vals),
                "n_fail": len(f_vals),
            }
        out[lh] = comp_out
    return out


def top_k_heads_by_abs_delta(
    contrast: Dict[LH, Dict[str, Dict[str, float]]],
    component: str,
    k: int,
) -> List[LH]:
    """Return the ``k`` (layer, head) with the largest ``|delta|`` for ``component``.

    Only (ℓ, h) that carry an entry for ``component`` are considered. Ties are
    broken by (layer, head) ascending for determinism. ``k <= 0`` → ``[]``;
    fewer than ``k`` candidates → all of them.
    """
    if k <= 0:
        return []
    scored: List[Tuple[float, LH]] = []
    for lh, comp_map in contrast.items():
        if component in comp_map:
            scored.append((abs(comp_map[component]["delta"]), lh))
    # Sort by |delta| desc, then (layer, head) asc for stable output.
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [lh for _, lh in scored[:k]]


# --------------------------------------------------------------------------- #
# GPU wrapper — STUB ONLY (documented, gated, not run, not tested).
# --------------------------------------------------------------------------- #
def require_gpu() -> None:
    """Raise unless a CUDA GPU is available (torch imported lazily here)."""
    import torch  # lazy: keeps module import torch-free

    if not torch.cuda.is_available():
        raise RuntimeError(
            "require_gpu(): no CUDA device available — Phase-F1.3 attention "
            "extraction is GPU-only and must run on a non-competing L40S slot."
        )


def extract_attention_for_record(
    model,
    tokenizer,
    templated_text: str,
    **kwargs,
) -> np.ndarray:
    """Extract a ``[n_layers, n_heads, n_q, n_k]`` attention tensor (GPU-deferred STUB).

    Intended behavior (per §6.2, to be wired in during Phase-F1.3 execution):

    1. Tokenize ``templated_text`` (already chat-templated attacked output;
       reuse ``poc_stage4/qwen3_model.py`` templating) and move inputs to GPU.
    2. Run a single clean (unablated) forward pass with
       ``output_attentions=True`` under ``torch.no_grad()``.
    3. Stack the per-layer attention tuples into one tensor of shape
       ``[n_layers, n_heads, n_q, n_k]`` (drop the batch dim; batch size 1).
    4. ``.detach().to(torch.float32).cpu().numpy()`` and return it, to be fed
       straight into :func:`attention_mass_to_spans` together with the F1.1 span
       token ranges (§2) and the ``final_answer_cue`` / generation query rows.

    Per §6.2 the cross-outcome contrast uses components present in BOTH splits
    (``benign_puzzle_scaffold`` / ``harmful_instruction`` / ``final_answer_cue``);
    per §6.1a ``injected_reasoning`` is a failure-only (refusal) probe.

    This function is intentionally NOT implemented on CPU: it loads a model and
    runs a GPU forward pass, which the F1.3 safety scope defers.
    """
    require_gpu()
    raise NotImplementedError(
        "GPU-deferred: wire in Phase-F1.3 execution "
        "(forward with output_attentions=True; stack layers/heads; CPU numpy)."
    )
