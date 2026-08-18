"""extract_boombness.py — measure Boombness for every target occurrence in the bank (plan §6, §7).

Two GPU passes, both one forward per prompt:

  --stage fit    over the core 2x2 rows only: accumulate per-cell, per-layer means of the
                 residual stream at the FINAL target occurrence, then estimate
                 d_surface / d_context / d_inter / d_naive (signals.estimate_directions).
                 Fitted SEPARATELY on `dev` and on `heldout` so scoring can cross-fit.

  --stage score  over the whole bank: for every target occurrence i and every layer L,
                 record the direction projections and the logit-lens scores. Scoring a row
                 from split S uses directions fitted on the OTHER split (house cross-fitting
                 convention, 33_build_directions.py), so a Boombness score is never read off
                 a direction fitted on the same text.

TOKEN POSITIONS — the trap this repo has hit twice (feedback_absolute_position_index_bug):
a position must be resolved PER EXAMPLE. Nothing here caches an index across prompts; every
occurrence span is recomputed from that prompt's own templated string, and an occurrence that
cannot be resolved is recorded as a FAILURE (plan §2.2), never skipped silently.

LAYER CONVENTION: block L == hidden_states[L+1]; hidden_states[0] is the embedding. Records
carry `layer_convention` so a downstream reader cannot get this wrong.

Responsible handling: no generation happens here and no prompt text is written to results;
rows carry ids and scalars only.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (DATA_DIR, FailureLedger, OUT_ROOT, RunDir, ds, read_jsonl,  # noqa: E402
                    seed_everything, validate_direction_payload)
import signals as sg  # noqa: E402
from ds_common import parse_enable_thinking as dc_parse_thinking  # noqa: E402

DEFAULT_BANK = os.path.join(DATA_DIR, "boombness_prompt_bank.jsonl")


# --------------------------------------------------------------------------- #
# Fit-payload IDENTITY (defect T8, second half — 2026-08-19)
# --------------------------------------------------------------------------- #
# `common.validate_direction_payload` closed three quarters of T8: it compares the payload's own
# `meta` against the consuming run's MODEL, POSITION and LAYER SET. Two identity fields it cannot
# check, because nothing ever WROTE them into the payload:
#
#   BANK.  A direction is a difference of cell means over a specific set of prompts. The bank has
#          been regenerated three times this sprint (1464 -> 1752 -> 2352 rows) and retraction R1's
#          stated root cause is joining across regenerations by `prompt_id`. A d_surface fitted on
#          the 1464-row bank, consumed by a score run over the 2352-row bank, is a cross-bank join
#          wearing the same file name — and `--fit-dir` is precisely the flag that carries it
#          across runs. `common.compare_bank_hashes` was written for this comparison in the same
#          commit that split `bank_content_sha16` into two names, and had NO caller anywhere in the
#          repo: the fifth guard this sprint shipped without a live call site.
#   DTYPE. The direction tensors are always float32 (`estimate_directions` casts), so the payload's
#          dtype says nothing. What matters is the dtype of the ACTIVATIONS the cell means were
#          taken from: a d fitted from bfloat16 residuals and applied to float32 residuals is a
#          different measurement, and every cosine moves silently.
#
# Both are checked HERE rather than in `common.validate_direction_payload` only because this agent
# does not own `common.py`. They belong in the shared validator so `score_behavior`,
# `aggressive_patching` and `surgical_knockout` inherit them instead of growing a fourth copy —
# reported as a cross-file dependency, NOT worked around by editing that file.
#
# BACKWARD COMPATIBILITY IS NOT AGREEMENT. Every payload committed before today has no
# `bank_rows_sha16` and no `fit_dtype` in its meta. An absent field is recorded in
# `unknown_identity` and is NOT fatal — but it is never counted as a match either, which is the
# rule `compare_bank_hashes` already states: "an old artifact that predates the rows hash must not
# be able to certify a join it never recorded."
def validate_fit_identity(payload: Dict, path: str, *, model, position: str,
                          layers: Sequence[int], bank_meta: Optional[Dict] = None,
                          dtype: Optional[str] = None, strict: bool = True,
                          allow_cross_bank: bool = False) -> Dict:
    """`common.validate_direction_payload` plus the BANK and DTYPE the payload was fitted under.

    Returns the merged verdict dict. Raises SystemExit when `strict` and anything MISMATCHES
    (never merely because something is unrecorded).
    """
    v = validate_direction_payload(payload, path=path, model=model, position=position,
                                   layers=list(layers), strict=False)
    v.setdefault("problems", [])
    v["unknown_identity"] = []
    meta = payload.get("meta") if isinstance(payload, dict) else None
    if not isinstance(meta, dict):
        # The base validator has already recorded "no meta block"; nothing further is checkable.
        if strict and v["problems"]:
            raise SystemExit(f"[validate_fit_identity] REFUSING {path or 'payload'}: "
                             + " | ".join(v["problems"]))
        return v

    bank_meta = bank_meta or {}
    v.setdefault("problems_nonfatal", [])
    v["cross_bank_fit"] = False

    # THREE BANK FACTS, AND THEY ARE NOT INDEPENDENT (verifier fix, 2026-08-19).
    #
    # (1) The first version downgraded a `bank_file_sha16` MISMATCH to non-fatal
    #     UNCONDITIONALLY, on the stated ground that "same prompts, different bytes is a
    #     re-serialisation". That ground is `bank_rows_sha16` AGREEING, and the code never
    #     checked whether it had. On an EXTERNAL bank (plan 14 / ClearHarm / AdvBench) the rows
    #     hash is None on BOTH sides by construction -- those files carry no per-row
    #     `prompt_sha16` and `note_bank` correctly refuses to invent one -- so the only fatal
    #     bank check was permanently unavailable on exactly the banks now in flight, and
    #     `fit on ClearHarm -> score on AdvBench` passed strict=True with an empty problems list.
    #     The downgrade now REQUIRES a rows hash that was compared and agreed.
    #
    # (2) `note_bank` hashes the bank FILE and `--limit` truncates the rows AFTER it, so a
    #     `--limit 24` fit over the 2352-row bank stamps the FULL bank's hashes and a later full
    #     score run was certified `checked: bank_rows_sha16` against a fit built from 24 of 2352
    #     prompts. outputs/boombness/extract_boombness/smoke_20260816_183101_1000604 and
    #     smoke_20260816_183822_1001753 are both `limit: 24` on that bank. Only the row COUNT can
    #     see it -- and it is fatal ONLY when nothing else says the banks differ, because two
    #     different banks are *expected* to have different row counts (see 3).
    #
    # (3) APPLYING A FIT ACROSS BANKS IS A REAL WORKFLOW, NOT ONLY A BUG. The 2x2 direction is
    #     deliberately applied to other prompt sets: `roleblk_20260818_114425_1408585` is a
    #     committed `--stage score --fit-dir <2x2 fit> --bank role_style_block.jsonl` run (720
    #     rows against a 1464-row fit), and 44 committed score_behavior/knockout runs apply that
    #     same fit to the ClearHarm (179), AdvBench (495) and 2352-row banks. A guard that made
    #     that fatal with no way to say "yes, on purpose" would be routed around with a bypass
    #     hack the first time someone re-fits -- which is how a guard becomes decoration. So a
    #     bank-identity mismatch is FATAL BY DEFAULT and expressible: `--allow-cross-bank-fit`
    #     turns it into a recorded, printed, counted `cross_bank_fit`. It downgrades NOTHING
    #     else -- not the model, not the position, not the dtype, and not (2).
    rows_a, rows_b = meta.get("bank_rows_sha16"), bank_meta.get("bank_rows_sha16")
    rows_checked = bool(rows_a and rows_b)
    rows_agree = rows_checked and rows_a == rows_b
    bank_mismatches: List[str] = []
    if rows_checked:
        v["checked"].append("bank_rows_sha16")
        if not rows_agree:
            bank_mismatches.append(
                f"bank_rows_sha16: directions were FITTED on bank {rows_a} but this run reads bank "
                f"{rows_b} ({bank_meta.get('bank_path')}) -- a direction is a difference of cell "
                f"means over a specific prompt set, and joining across bank regenerations by "
                f"prompt_id is retraction R1's stated root cause")
    else:
        v["unknown_identity"].append("bank_rows_sha16")

    file_a, file_b = meta.get("bank_file_sha16"), bank_meta.get("bank_file_sha16")
    if file_a and file_b:
        v["checked"].append("bank_file_sha16")
        if file_a != file_b:
            msg = (f"bank_file_sha16: directions were FITTED on bank file {file_a} but this run "
                   f"reads bank file {file_b} ({bank_meta.get('bank_path')})")
            if rows_agree:
                # Same prompts (the rows hash was COMPARED and AGREED), different file bytes: a
                # re-serialisation is not a different bank. Recorded, not fatal.
                v["problems_nonfatal"].append(
                    msg + " -- but bank_rows_sha16 was compared and AGREES, so this is a "
                          "re-serialisation of the same prompt set, not a different bank")
            else:
                bank_mismatches.append(
                    msg + " -- and bank_rows_sha16 could not certify these are the same prompts "
                          f"(rows hashes: fit={rows_a!r}, run={rows_b!r}), so nothing establishes "
                          f"that this is the same bank")
    else:
        v["unknown_identity"].append("bank_file_sha16")

    v["bank_identity_mismatch"] = bool(bank_mismatches)
    if bank_mismatches:
        if allow_cross_bank:
            v["cross_bank_fit"] = True
            v["problems_nonfatal"].extend(
                m + " [DECLARED via --allow-cross-bank-fit: applying a direction to a different "
                    "prompt set is a real analysis; it is recorded here so no reader can mistake "
                    "it for a same-bank measurement]" for m in bank_mismatches)
        else:
            v["problems"].extend(
                m + " (if this is deliberate -- applying the 2x2 direction to another prompt set "
                    "-- say so with --allow-cross-bank-fit, which records it instead of hiding "
                    "it)" for m in bank_mismatches)

    n_a, n_b = meta.get("n_bank_rows_used"), bank_meta.get("n_bank_rows_used")
    if n_a is not None and n_b is not None:
        v["checked"].append("n_bank_rows_used")
        if int(n_a) != int(n_b):
            msg = (f"n_bank_rows_used: directions were FITTED over {n_a} bank row(s) but this run "
                   f"reads {n_b}")
            if v["bank_identity_mismatch"]:
                # Two different banks are expected to differ in size; the size is not the finding,
                # the bank identity above is.
                v["problems_nonfatal"].append(
                    msg + " -- expected, because the bank identity already differs")
            else:
                v["problems"].append(
                    msg + " -- and NOTHING says the banks differ, so this is the same bank read "
                          "twice at different lengths: `--limit` truncates the rows AFTER "
                          "note_bank hashes the file, so the bank hashes cannot see it")
    else:
        v["unknown_identity"].append("n_bank_rows_used")

    a, b = meta.get("fit_dtype"), (str(dtype) if dtype is not None else None)
    if a and b:
        v["checked"].append("fit_dtype")
        if str(a) != b:
            v["problems"].append(
                f"fit_dtype: the cell means were taken from {a} activations but this run reads "
                f"{b} activations -- the stored direction is float32 either way, so nothing about "
                f"the arithmetic complains while every cosine moves")
    else:
        v["unknown_identity"].append("fit_dtype")

    v["n_unknown_identity_fields"] = len(v["unknown_identity"])
    v["n_nonfatal_identity_problems"] = len(v["problems_nonfatal"])
    if strict and v["problems"]:
        raise SystemExit(f"[validate_fit_identity] REFUSING {path or 'payload'}: "
                         + " | ".join(v["problems"]))
    return v


def read_run_bank_meta(run, bank_path: Optional[str]) -> Dict:
    """The bank identity `RunDir.note_bank` recorded, read back off the run -- or a hard stop.

    WHY THIS IS NOT AN INLINE `getattr(run, "_extra_meta", {}).get(k)` (verifier fix, 2026-08-19).
    `_extra_meta` is a PRIVATE attribute of a class in a file this module does not own. The inline
    form defaulted to `{}` on any of: the attribute being renamed, `note_bank` not having been
    called, or `note_bank` having failed. Every one of those produced `None` for every hash, which
    `validate_fit_identity` then reports as `unknown_identity` -- i.e. the whole T8 identity guard
    would degrade to "nothing recorded, nothing checked" and say so only in a field nobody diffs.
    That is the sprint's dead-guard shape keyed on an incidental property (an attribute name).
    A run that was given a `--bank` and cannot produce its recorded path stops here instead.
    """
    meta = getattr(run, "_extra_meta", None)
    if not isinstance(meta, dict):
        raise SystemExit(
            "[extract] RunDir exposes no `_extra_meta` mapping, so the bank hashes note_bank "
            "recorded cannot be read back. The T8 identity stamp would silently become 'unknown' "
            "on every field. Fix the accessor rather than shipping an unverifiable fit dir.")
    out = {k: meta.get(k) for k in ("bank_path", "bank_file_sha16", "bank_rows_sha16",
                                    "bank_n_rows")}
    if bank_path and out["bank_path"] is None:
        raise SystemExit(
            f"[extract] note_bank recorded no bank_path for {bank_path!r} "
            f"(keys present: {sorted(meta)[:12]}). Refusing to stamp or check a fit payload whose "
            f"bank identity is unrecoverable.")
    return out


CORE_2X2 = ("benign_literal", "direct_harmful", "natural_doublespeak", "concept_in_benign_ctx")
COND_TO_CELL = {"benign_literal": "A", "direct_harmful": "B",
                "natural_doublespeak": "C", "concept_in_benign_ctx": "E"}
CORE_2X2_CELLS = ("A", "B", "C", "E")


# --------------------------------------------------------------------------- #
# Occurrence resolution
# --------------------------------------------------------------------------- #
# THINKING-MODE TEMPLATE (set from --enable-thinking; 2026-08-17).
# `ds_common.apply_template` warns that "Qwen3's default is thinking-ON, and enable_thinking=False
# must be passed EXPLICITLY". It changes the PROMPT rendering (an empty <think> block is added to the
# assistant prefix), so it affects extraction as well as generation — the two must agree or the
# representation is read off a different prompt than the one generated from, which is the exact
# manipulated-vs-measured error this sprint retracted five times.
ENABLE_THINKING = None   # None = model default


def resolve_occurrences(dc, tok, row: Dict, enable_thinking="__module__"
                        ) -> Tuple[str, List[int], List[int], List[int], List[int]]:
    """Return (templated_text, input_ids, last_idx_per_occurrence, following_idx, n_subtokens).

    `n_subtokens` per occurrence is returned and recorded because the tokenization audit
    showed the target is NOT uniformly one token across arms on every model — and a
    2-subtoken occurrence puts a different vector at `codeword_last` (its last piece, e.g.
    "rot") than a 1-subtoken one. Downstream analysis must be able to condition on it rather
    than average over it.

    Raises ValueError with a specific reason if the occurrences cannot be resolved or do not
    match the character-level count the generator recorded.
    """
    # AUDIT 11 (A11-9): this templated with the MODULE-LEVEL ENABLE_THINKING, which only
    # extract_boombness's own main() ever sets. score_behavior.py has its OWN global and calls this
    # as a pre-flight gate, so on a `--enable-thinking false` run the gate validated a thinking-ON
    # template while the readout and dc.generate used thinking-OFF. Sixth instance of the
    # one-of-two-paths shape. Callers now pass the mode explicitly.
    #
    # VERIFIED INERT for the three committed thinking-off runs (q3_projout, q3_projctrl,
    # qwen3nt_base): all 960/960 succeeded with ZERO resolve failures, because enable_thinking
    # injects `<think></think>` into the ASSISTANT prefix, after the user content where the target
    # occurrences live. No reported number changes; the guard now checks what it claims to.
    _et = ENABLE_THINKING if enable_thinking == "__module__" else enable_thinking
    templated = dc.apply_template(tok, row["full_prompt"],
                                  enable_thinking=_et)
    ids = tok(templated, add_special_tokens=False)["input_ids"]
    # A ROW WITH NO TARGET WORD HAS NOTHING TO RESOLVE, and must say so BEFORE the search.
    # First attempt at supporting external harmful sets (plan §14) only narrowed the `not last`
    # raise below. That was the wrong one of two paths: `target_surface` is the EMPTY STRING on
    # such rows, and an empty needle matches at every token, so `last` came back with 24-33 hits
    # and the COUNT-MISMATCH check above it fired instead --
    #     resolve:occurrence_count_mismatch:text=0,tokens=27
    # killing 179/179 rows in all three ClearHarm arms (jobs 764745-747) while SLURM reported
    # COMPLETED 0:0. The FailureLedger is the only reason that was visible at all: `counts: {}`
    # with an itemised reason per row, which is exactly what plan §2.2 mandates it for.
    if not row.get("target_surface"):
        if row["n_target_occurrences"] not in (0, None):
            raise ValueError(f"no_target_surface_but_expected:{row['n_target_occurrences']}")
        return templated, ids, [], [], []
    hit = dc.find_word_occurrences_in_text(tok, templated, row["target_surface"],
                                           add_special_tokens=False)
    last = list(hit.last_idx)
    if len(last) != row["n_target_occurrences"]:
        raise ValueError(f"occurrence_count_mismatch:text={row['n_target_occurrences']},"
                         f"tokens={len(last)}")
    if not last and row["n_target_occurrences"] != 0:
        raise ValueError("no_target_occurrence")
    # A row that DECLARES zero occurrences and has zero is not a failure -- the metadata and the
    # tokenizer AGREE, which is the only thing this gate exists to check (the count comparison
    # above does that work). The unconditional raise was correct while every row came from the
    # sprint's own generator, where the codeword is always present; it made an EXTERNAL harmful set
    # (plan §14 / ClearHarm) unscoreable, because those prompts carry no codeword at all and every
    # row would have died in the pre-flight gate with `no_target_occurrence`. Callers that need a
    # target POSITION (extract_boombness's own stages) must check `last` themselves; callers using
    # this purely as a metadata-vs-tokenizer gate (score_behavior) now pass such rows.
    if max(last) >= len(ids):
        raise ValueError(f"occurrence_index_out_of_range:{max(last)}>={len(ids)}")
    following = [i + 1 if i + 1 < len(ids) else i for i in last]
    n_sub = [e - st for st, e in hit.spans]
    return templated, ids, last, following, n_sub


@torch.no_grad()
def forward_hidden(lm, ids: List[int], _diag: Optional[Dict] = None) -> torch.Tensor:
    """Return hidden states as [n_blocks+1, seq, H] float32 on CPU (index 0 = embeddings).

    THE LAST ELEMENT NEEDS A HOOK, NOT A SLICE. transformers 5.12 ties the last entry of
    `out.hidden_states` to `out.last_hidden_state`
    (`transformers/utils/output_capturing.py:265-267`, `tie_last_hidden_states=True` by default),
    and for Llama `last_hidden_state = self.norm(final_block_output)`. So the tuple element that
    looks like "block N-1's residual" is actually the POST-FINAL-NORM state, while every other
    element is a raw block output.

    Left alone that breaks three things at once: the logit lens would RMSNorm an already-normed
    vector at the last layer, the per-layer curves would have a silent semantic discontinuity at
    their right-hand end, and `aggressive_patching` would transplant a post-norm donor vector
    into a position the model then norms again.

    So we capture `layers[-1]`'s true output with a forward hook and substitute it in. The result
    is uniform: `hs[L+1]` is the raw output of block `L` for every `L`. `_diag`, if given,
    receives the relative discrepancy between the hooked and the tied vector, so the correction
    can be shown to have mattered rather than asserted to.
    """
    layers = dc_layers(lm)
    grabbed: Dict[str, torch.Tensor] = {}

    def _hook(mod, inp, out):
        grabbed["h"] = (out[0] if isinstance(out, tuple) else out).detach()

    handle = layers[-1].register_forward_hook(_hook)
    try:
        t = torch.tensor([ids], device=lm.model.device)
        out = lm.model(input_ids=t, output_hidden_states=True, use_cache=False)
        hs = [h[0].float().cpu() for h in out.hidden_states]
    finally:
        handle.remove()

    if "h" not in grabbed:
        raise RuntimeError("forward hook on the last decoder block did not fire; refusing to "
                           "fall back to the tied post-norm hidden state silently")
    raw_last = grabbed["h"][0].float().cpu()
    if len(hs) != lm.num_layers + 1:
        raise RuntimeError(f"expected {lm.num_layers + 1} hidden states, got {len(hs)}")
    if _diag is not None:
        tied = hs[-1]
        denom = float(tied.norm()) or 1.0
        _diag["last_layer_tied_vs_raw_relnorm"] = float((tied - raw_last).norm()) / denom
    hs[-1] = raw_last
    return torch.stack(hs, dim=0)


def dc_layers(lm):
    """The decoder block ModuleList, via the house accessor."""
    return ds()._get_layers(lm.model)


# --------------------------------------------------------------------------- #
# Stage: fit
# --------------------------------------------------------------------------- #
def stage_fit(lm, dc, rows: List[Dict], layers: List[int], run: RunDir,
              ledger: FailureLedger, position: str = "codeword_last",
              fit_identity: Optional[Dict] = None) -> Dict[str, Dict]:
    """Estimate the 2x2 directions per split, averaging every cell over THE SAME families.

    The identification argument behind d_surface = 1/2[(B-C)+(E-A)] is that the two differences
    are context-matched, and that only holds if the four cells are averaged over the same set of
    families. Equal cell COUNTS are not sufficient — a run that loses family f from cell B and a
    different family g from cell C has 30 rows in each and a d_surface contaminated by which
    demo blocks happened to survive. So per-family vectors are kept, the four cells' family sets
    are intersected, and any family missing from any cell is dropped from ALL of them and
    recorded in the ledger.
    """
    # per_fam[split][cell][family_id] = Tensor[len(layers), H]
    per_fam: Dict[str, Dict[str, Dict[str, torch.Tensor]]] = collections.defaultdict(
        lambda: collections.defaultdict(dict))
    diag_accum: List[float] = []

    fit_rows = [r for r in rows
                if r["condition"] in CORE_2X2 and r["bank_block"] == "core2x2"
                and r["query_kind"] == "behavioral" and r["n_examples"] > 0]
    print(f"[fit] {len(fit_rows)} rows across splits "
          f"{collections.Counter(r['split'] for r in fit_rows)}")

    for row in fit_rows:
        try:
            _, ids, last, following, _ = resolve_occurrences(dc, lm.tokenizer, row)
        except ValueError as e:
            ledger.fail(f"fit:{e}", row["prompt_id"])
            continue
        # NO OCCURRENCE, NO POSITION TO FIT AT (silent-failure audit, 2026-08-19).
        # `resolve_occurrences` returns EMPTY occurrence lists, without raising, for a row whose
        # `target_surface` is the empty string -- the shape that plan 14's external harmful sets
        # (ClearHarm/AdvBench) have by construction, and the shape the 2026-08-18 fix deliberately
        # made non-fatal there. Its own docstring says "callers that need a target POSITION
        # (extract_boombness's own stages) must check `last` themselves"; neither stage did. Here
        # the consequence was an IndexError on `last[-1]` that kills the whole fit with a
        # traceback carrying no prompt_id; in `stage_score` it was silent (see there). Counted with
        # a reason at both, so the run says which rows had nothing to read.
        if position != "last" and not last:
            ledger.fail(f"fit:no_occurrence_at_position:{position}", row["prompt_id"])
            continue
        if position == "codeword_last":
            pos = last[-1]
        elif position == "last":
            pos = len(ids) - 1          # final prompt token, matching refusalness' default
        else:
            pos = following[-1]
        diag: Dict[str, float] = {}
        hs = forward_hidden(lm, ids, _diag=diag)
        if "last_layer_tied_vs_raw_relnorm" in diag:
            diag_accum.append(diag["last_layer_tied_vs_raw_relnorm"])
        per_fam[row["split"]][COND_TO_CELL[row["condition"]]][row["family_id"]] = \
            torch.stack([hs[L + 1, pos, :] for L in layers], dim=0)
        ledger.ok()

    if diag_accum:
        run.note(last_layer_tied_vs_raw_relnorm_mean=sum(diag_accum) / len(diag_accum),
                 last_layer_tied_vs_raw_relnorm_max=max(diag_accum),
                 last_layer_note="hidden_states[-1] is tied to last_hidden_state (post final "
                                 "norm) in transformers 5.x; forward_hidden substitutes the "
                                 "hooked raw block output so hs[L+1] is uniform across L")

    fitted: Dict[str, Dict] = {}
    fit_report: Dict[str, Dict] = {}
    for split, cells in per_fam.items():
        if not set(CORE_2X2_CELLS).issubset(cells):
            ledger.fail(f"fit:missing_cells:{sorted(set(CORE_2X2_CELLS) - set(cells))}", split)
            continue
        fam_sets = {c: set(cells[c]) for c in CORE_2X2_CELLS}
        common = set.intersection(*fam_sets.values())
        dropped = {c: sorted(fam_sets[c] - common) for c in CORE_2X2_CELLS}
        n_dropped = sum(len(v) for v in dropped.values())
        if n_dropped:
            for c, fams in dropped.items():
                for f in fams:
                    ledger.fail(f"fit:family_not_in_all_cells:{c}", f)
            print(f"[fit] split={split} DROPPED {n_dropped} cell-family entries not present in "
                  f"all four cells; {len(common)} families common to all cells")
        if not common:
            ledger.fail("fit:no_common_families", split)
            continue

        common_sorted = sorted(common)
        means: Dict[str, Dict[int, torch.Tensor]] = {}
        for c in CORE_2X2_CELLS:
            stacked = torch.stack([cells[c][f] for f in common_sorted], dim=0)   # [n_fam, nL, H]
            m = stacked.mean(dim=0)
            means[c] = {L: m[i] for i, L in enumerate(layers)}

        fam_hash = hashlib.sha256("|".join(common_sorted).encode()).hexdigest()[:16]
        try:
            dset = sg.estimate_directions(
                means, n_per_cell={c: len(common_sorted) for c in CORE_2X2_CELLS},
                meta={"split_fitted_on": split, "position": position, "model": lm.model_id,
                      "n_families_common": len(common_sorted), "family_set_sha16": fam_hash,
                      "n_cell_family_entries_dropped": n_dropped,
                      # T8 identity (2026-08-19): WHICH BANK and WHICH ACTIVATION DTYPE these cell
                      # means came from. Without them a consumer can only check model/position/
                      # layers, and the two remaining ways to build a phantom cell -- fit on the
                      # 1464-row bank and score the 2352-row one, or fit in bf16 and score in fp32
                      # -- stay invisible. See validate_fit_identity above.
                      "fit_layers": list(layers),
                      "layer_convention": sg.LAYER_CONVENTION,
                      **(fit_identity or {})})
        except ValueError as e:
            ledger.fail(f"fit_directions:{e}", split)
            continue
        payload = dset.as_payload()
        payload["cell_means"] = means
        payload["families"] = common_sorted
        path = run.p(f"directions_fit_{split}.pt")
        torch.save(payload, path)
        fitted[split] = payload
        fit_report[split] = {"n_families_common": len(common_sorted),
                             "family_set_sha16": fam_hash,
                             "n_cell_family_entries_dropped": n_dropped,
                             "n_rows_per_cell": {c: len(fam_sets[c]) for c in CORE_2X2_CELLS}}
        print(f"[fit] split={split} families={len(common_sorted)} (sha16 {fam_hash}) "
              f"-> {os.path.basename(path)}")
        for name in ("d_surface", "d_context", "d_inter", "d_naive"):
            g = dset.gap[name]
            print(f"       ||{name}|| by layer: " +
                  " ".join(f"L{L}={g[L]:.2f}" for L in layers[::max(1, len(layers)//8)]))
    run.note(fit_report=fit_report)
    return fitted


# --------------------------------------------------------------------------- #
# Stage: score
# --------------------------------------------------------------------------- #
def _cross_fit_split(split: str, available: Sequence[str]) -> Tuple[str, bool]:
    """Score a dev row with heldout-fitted directions and vice versa.

    Returns (split_to_use, is_self_fit). Falling back to the row's OWN split is legal only as an
    explicit, recorded state: a cosine read off a direction fitted on the very same text is
    inflated by in-sample fit, and the §6.4 sanity check would then pass trivially. The caller
    records `is_self_fit` on every row and the run summary counts them, so no consumer can
    mistake a self-fit number for a cross-fit one.
    """
    other = "heldout" if split == "dev" else "dev"
    if other in available:
        return other, False
    return split, True


@torch.no_grad()
def stage_score(lm, dc, rows: List[Dict], layers: List[int], fitted: Dict[str, Dict],
                run: RunDir, ledger: FailureLedger, dir_names: Sequence[str],
                logit_lens_layers: Sequence[int], cache_final_reps: bool,
                readout_id_mode: str = "primary", position: str = "codeword_last") -> Dict:
    """BUG FIXED 2026-08-17 (independent audit). `position` was accepted by `stage_fit` but NOT by
    `stage_score`, which unconditionally read at the codeword occurrence. A run launched with
    `--position last` therefore RE-FIT the direction on last-token activations and then READ it at
    the codeword — a combination nobody asked for, reported under the label "d_surface at the last
    token". 1464/1464 rows carried a `token_pos` identical to the codeword run and 0/2352 sat at
    `seq_len-1`. The cell was a phantom, and an entire conclusion (the predictor x position 2x2,
    and the §18 label move to C) was built on it."""
    tok = lm.tokenizer
    # Symmetric, validated readout ids — one whole-word token per side. See
    # signals.readout_ids for why the naive "first id of every variant" set was wrong.
    c_ids, w_ids, id_meta = sg.readout_id_pair(tok, rows[0]["concept"], rows[0]["codeword"],
                                               mode=readout_id_mode)
    run.note(readout_ids=id_meta, concept_token_ids=c_ids, codeword_token_ids=w_ids,
             layer_convention=sg.LAYER_CONVENTION)
    print(f"[score] readout ids ({readout_id_mode}): concept={c_ids} "
          f"{id_meta['concept']['full_word_pieces']}  codeword={w_ids} "
          f"{id_meta['codeword']['full_word_pieces']}")

    cache: Dict[str, torch.Tensor] = {}
    n_scored = 0
    # T8b (2026-08-18). PER-LAYER COVERAGE OF THE HEADLINE METRIC.
    # The inner loop below does `d = payload[name].get(L); if d is None: continue` -- it drops the
    # column, still writes the row, still calls ledger.ok(), and the run reports n_failed = 0. A
    # score run whose --layers is wider than the fit's (the Qwen3 depth fit covers 14 of 40 blocks;
    # `--layers all` against it would ask for 40) therefore produces a results.jsonl in which
    # `d_surface|L*|cos` SIMPLY DOES NOT EXIST at the missing layers, while every completeness
    # signal the run emits says it is whole. A missing column is not a zero and it is not a NaN --
    # it is an absent key, so a downstream `mean()` over the rows that DO have it silently changes
    # its denominator per layer instead of raising.
    # Counting is the whole fix: presence and absence are tallied per (direction, layer) and
    # published in summary.json, so "the metric does not exist at 22 of 32 layers" is a number in
    # the artifact rather than something discovered by a reader who happens to grep for a column.
    cov_present: Dict[str, Dict[int, int]] = {n: {L: 0 for L in layers} for n in dir_names}
    cov_missing: Dict[str, Dict[int, int]] = {n: {L: 0 for L in layers} for n in dir_names}
    # CROSS-FIT COVERAGE (silent-failure audit, 2026-08-19).
    # `_cross_fit_split`'s docstring promises "the caller records `is_self_fit` on every row and the
    # run summary COUNTS THEM, so no consumer can mistake a self-fit number for a cross-fit one".
    # The per-row flag was written; the count never was. A `--stage score --fit-dir X` run where X
    # holds only `directions_fit_dev.pt` silently self-fits every dev row, and the summary's
    # `splits_fitted: ["dev"]` is the only trace -- one that says which splits were FITTED, not how
    # many rows were scored against their OWN text. It has already happened twice on this
    # checkout: extract_boombness/smoke_20260816_183101 and smoke_20260816_183822 fitted `dev`
    # alone, so 24/24 of their rows are self-fit and nothing in either summary says so.
    n_self_fit = n_cross_fit = 0
    self_fit_by_split: Dict[str, int] = collections.defaultdict(int)
    # Rows that resolve cleanly but have NO occurrence to read at the requested position.
    n_no_occurrence = 0
    for row in rows:
        try:
            _, ids, last, following, n_sub = resolve_occurrences(dc, tok, row)
        except ValueError as e:
            ledger.fail(f"score:{e}", row["prompt_id"])
            continue
        fit_split, is_self_fit = _cross_fit_split(row["split"], list(fitted))
        payload = fitted.get(fit_split)
        if payload is None:
            ledger.fail("score:no_fitted_directions", row["prompt_id"])
            continue

        # NO OCCURRENCE, NO ROW -- AND THE OLD CODE STILL CALLED IT A SUCCESS.
        # (silent-failure audit, 2026-08-19.) For `--position codeword_last` the loop below
        # iterates `zip(last, following, n_sub)`. `resolve_occurrences` returns those three lists
        # EMPTY, without raising, for a row whose `target_surface` is the empty string -- exactly
        # what plan 14's external harmful banks look like. The loop body then never executed, no
        # record was ever logged, and control fell through to `ledger.ok()` and `n_scored += 1`.
        # A whole bank of such rows produces `n_scored_rows: 179`, `n_failed: 0`, DONE.json, and a
        # results.jsonl with ZERO rows in it. That is the same failure that killed ClearHarm arms
        # 764745-747 (`COMPLETED 0:0`), one layer further in: there the count check raised, here
        # nothing did. Counted with a reason, so the ledger sees it.
        if position != "last" and not last:
            ledger.fail(f"score:no_occurrence_at_position:{position}", row["prompt_id"])
            n_no_occurrence += 1
            continue

        hs = forward_hidden(lm, ids)
        n_occ = 1 if position == "last" else len(last)
        # `last` holds the codeword-occurrence indices. For `--position last` the readout is the
        # final PROMPT token instead; there is exactly one such position per prompt, so the
        # per-occurrence loop collapses to a single record.
        if position == "last":
            occ_iter = [(len(ids) - 1, len(ids) - 1, n_sub[-1] if n_sub else 1)]
        else:
            occ_iter = list(zip(last, following, n_sub))
        for occ_i, (pos, fpos, nsub) in enumerate(occ_iter):
            # SELF-CHECK. The phantom-cell bug was invisible because nothing ever asserted that the
            # readout index matched the requested position. It does now, on every row.
            if position == "last" and pos != len(ids) - 1:
                raise AssertionError(
                    f"--position last but readout index {pos} != seq_len-1 ({len(ids)-1})")
            if position == "codeword_last" and pos not in last:
                raise AssertionError(
                    f"--position codeword_last but readout index {pos} is not a codeword occurrence")
            rec: Dict[str, object] = {
                "prompt_id": row["prompt_id"], "prompt_sha16": row.get("prompt_sha16"), "family_id": row["family_id"],
                "condition": row["condition"], "cell": row["cell"], "domain": row["domain"],
                "split": row["split"], "bank_block": row["bank_block"],
                "query_kind": row["query_kind"], "n_examples": row["n_examples"],
                "strength": row["strength"], "consistency": row["consistency"],
                "example_position": row["example_position"], "role_style": row["role_style"],
                "target_surface": row["target_surface"],
                "occurrence_index": occ_i, "n_occurrences": n_occ,
                "is_final_occurrence": occ_i == n_occ - 1,
                "is_query_occurrence": occ_i == n_occ - 1,   # query word is always last
                "token_pos": pos, "seq_len": len(ids),
                "n_subtokens": nsub, "is_single_token": nsub == 1,
                "directions_fitted_on": fit_split, "is_self_fit": is_self_fit,
                "layer_convention": sg.LAYER_CONVENTION,
            }
            for L in layers:
                h = hs[L + 1, pos, :]
                for name in dir_names:
                    d = payload[name].get(L)
                    if d is None:
                        cov_missing[name][L] += 1
                        continue
                    cov_present[name][L] += 1
                    s = sg.direction_boombness(h, d)
                    rec[f"{name}|L{L}|cos"] = s["cosine"]
                    rec[f"{name}|L{L}|proj"] = s["projection"]
                rec[f"hnorm|L{L}"] = float(h.norm())
            # Batched logit lens: one lm_head matmul for every (layer, position) pair of this
            # occurrence instead of 2*len(logit_lens_layers) separate calls. The `following`
            # readout is included because the house code repeatedly finds the semantic content
            # sits on the token AFTER the word, so both are recorded rather than assumed.
            if logit_lens_layers:
                stack = torch.stack(
                    [hs[L + 1, pos, :] for L in logit_lens_layers]
                    + [hs[L + 1, fpos, :] for L in logit_lens_layers], dim=0)
                lls = sg.logit_lens_boombness_batch(lm, stack, c_ids, w_ids)
                nL = len(logit_lens_layers)
                for j, L in enumerate(logit_lens_layers):
                    ll = lls[j]
                    rec[f"ll|L{L}|boombness"] = ll["logit_lens_boombness"]
                    rec[f"ll|L{L}|p_concept"] = ll["p_concept"]
                    rec[f"ll|L{L}|p_codeword"] = ll["p_codeword"]
                    rec[f"ll|L{L}|rank_concept"] = ll["rank_concept"]
                    rec[f"llfollow|L{L}|boombness"] = lls[nL + j]["logit_lens_boombness"]
            run.log_row(rec)

        if cache_final_reps:
            # BUG FIXED 2026-08-17. This indexed `last[-1]` (the final codeword occurrence)
            # UNCONDITIONALLY, so a `--position last` run cached codeword-position vectors while its
            # metadata recorded position="last". Three shipped caches were mislabelled that way — and
            # the mislabel was introduced by the phantom-cell fix itself, which threaded `position`
            # into the readout and missed the cache. Fifth instance of the one-of-two-paths shape.
            # No reported number was affected (all six probes runs consume codeword_last extracts),
            # but the cache must agree with the readout it claims to summarise.
            cache_pos = (len(ids) - 1) if position == "last" else last[-1]
            cache[row["prompt_id"]] = torch.stack(
                [hs[L + 1, cache_pos, :] for L in layers], dim=0).half()
        if is_self_fit:
            n_self_fit += 1
            self_fit_by_split[str(row["split"])] += 1
        else:
            n_cross_fit += 1
        ledger.ok()
        n_scored += 1
        if n_scored % 100 == 0:
            print(f"[score] {n_scored}/{len(rows)} rows")

    # --- coverage report (T8b) -------------------------------------------------------------- #
    coverage: Dict[str, object] = {}
    total_missing_cells = 0
    for name in dir_names:
        missing_layers = sorted(L for L in layers if cov_present[name][L] == 0
                                and cov_missing[name][L] > 0)
        partial_layers = sorted(L for L in layers if cov_present[name][L] > 0
                                and cov_missing[name][L] > 0)
        n_missing_cells = sum(cov_missing[name].values())
        total_missing_cells += n_missing_cells
        coverage[name] = {
            "n_layers_requested": len(layers),
            "n_layers_with_no_direction": len(missing_layers),
            "layers_with_no_direction": missing_layers,
            "layers_partially_covered": partial_layers,
            "n_row_layer_cells_written": sum(cov_present[name].values()),
            "n_row_layer_cells_missing": n_missing_cells,
            "n_rows_per_covered_layer": {str(L): cov_present[name][L] for L in layers},
        }
        if missing_layers:
            print(f"[score] COVERAGE WARNING: {name} has NO fitted direction at "
                  f"{len(missing_layers)}/{len(layers)} requested layers {missing_layers[:12]}"
                  f"{'...' if len(missing_layers) > 12 else ''} — every `{name}|L*|cos` column at "
                  f"those layers is ABSENT from results.jsonl. This is not a failure of any ROW, "
                  f"so the failure ledger cannot see it; summary.json['direction_layer_coverage'] "
                  f"is where it is recorded.")
    if total_missing_cells:
        print(f"[score] {total_missing_cells} (row, direction, layer) cells had no direction and "
              f"were omitted from results.jsonl.")

    if cache_final_reps and cache:
        os.makedirs(run.cache, exist_ok=True)
        torch.save({"layers": layers, "layer_convention": sg.LAYER_CONVENTION,
                    "position": position,
                    "dtype": "float16", "reps": cache},
                   os.path.join(run.cache, "final_occurrence_reps.pt"))
        print(f"[score] cached {len(cache)} final-occurrence rep stacks")
    if n_self_fit:
        print(f"[score] SELF-FIT WARNING: {n_self_fit}/{n_self_fit + n_cross_fit} rows were scored "
              f"against directions fitted on their OWN split {dict(self_fit_by_split)} — an "
              f"in-sample cosine is inflated by fit and the §6.4 sanity check passes trivially on "
              f"it. summary.json['cross_fit'] carries the count.")
    return {"n_scored_rows": n_scored,
            "cross_fit": {"n_self_fit_rows": n_self_fit, "n_cross_fit_rows": n_cross_fit,
                          "self_fit_frac": (n_self_fit / (n_self_fit + n_cross_fit))
                                           if (n_self_fit + n_cross_fit) else 0.0,
                          "self_fit_rows_by_split": dict(self_fit_by_split),
                          "note": "a self-fit row's Boombness is read off a direction fitted on "
                                  "the very same text; the per-row `is_self_fit` flag has always "
                                  "been written, but nothing counted it until 2026-08-19"},
            "n_rows_with_no_occurrence_at_position": n_no_occurrence,
            "direction_layer_coverage": coverage,
            "n_missing_direction_layer_cells": total_missing_cells,
            "coverage_note": "a (direction, layer) with n_layers_with_no_direction > 0 has NO "
                             "column in results.jsonl at those layers; the failure ledger counts "
                             "ROWS and is blind to a missing COLUMN (defect T8b, 2026-08-18)"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", default=DEFAULT_BANK)
    ap.add_argument("--model", default=None, help="default = ds_common.PRIMARY_MODEL")
    ap.add_argument("--stage", choices=["fit", "score", "both"], default="both")
    ap.add_argument("--fit-dir", default=None,
                    help="run dir containing directions_fit_*.pt (for --stage score)")
    ap.add_argument("--layers", default="all", help="'all' or comma list of BLOCK indices")
    ap.add_argument("--logit-lens-layers", default="",
                    help="comma list of BLOCK indices; default = every 4th layer + last")
    ap.add_argument("--directions", default="d_surface,d_context,d_inter,d_naive")
    ap.add_argument("--enable-thinking", default=None,
                    choices=[None, "true", "false"],
                    help="explicitly set the chat template's thinking mode. REQUIRED for Qwen3-class "
                         "models: their default is thinking-ON, which for a matched comparison "
                         "against a non-thinking model must be turned OFF.")
    ap.add_argument("--position", default="codeword_last",
                    choices=["codeword_last", "last"],   # "following" removed 2026-08-17: it was an
                    # ACCEPTED choice that stage_score silently ignored, so fit and score
                    # would have read DIFFERENT tokens — the same one-of-two-paths shape as
                    # the phantom cell. No committed run used it. Re-add only with a
                    # matching branch in stage_score AND a per-row assertion.
                    help="'last' (final prompt token) added 2026-08-17 to complete the "
                         "position x predictor comparison. The sprint compared d_surface at "
                         "`codeword_last` against refusalness at the last token and declared "
                         "Boombness the better ASR predictor by 3.7x; at MATCHED position that "
                         "ratio inverted to 0.80. Measuring d_surface at `last` too is what makes "
                         "the comparison a 2x2 instead of two half-matched cells.")
    ap.add_argument("--readout-ids", default="primary", choices=["primary", "full_word"],
                    help="which token ids stand for the words in the logit lens; 'primary' is "
                         "the single leading-space whole-word token per side (symmetric)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--seed", type=int, default=20260816)
    ap.add_argument("--tag", default="run")
    ap.add_argument("--no-cache-reps", action="store_true")
    ap.add_argument("--allow-cross-bank-fit", action="store_true",
                    help="declare that the --fit-dir directions were fitted on a DIFFERENT bank "
                         "than this run scores. That is a real analysis -- the committed run "
                         "roleblk_20260818_114425 applies the 2x2 fit to role_style_block.jsonl, "
                         "and 44 committed runs apply it to ClearHarm/AdvBench -- but it is not "
                         "the default, because 'fit on the 1464-row bank, score the 2352-row "
                         "bank' is the same shape and is a phantom cell. Declaring it records "
                         "`cross_bank_fit` in summary.json instead of hiding it. It does NOT "
                         "relax the model, position, dtype or same-bank row-count checks.")
    args = ap.parse_args()
    global ENABLE_THINKING
    ENABLE_THINKING = dc_parse_thinking(args.enable_thinking)
    seed_everything(args.seed)

    dc = ds()
    rows = read_jsonl(args.bank)
    if args.limit:
        rows = rows[:args.limit]

    run = RunDir("extract_boombness", args, tag=args.tag, want_cache=True)
    ledger = FailureLedger()

    model_id = args.model or dc.PRIMARY_MODEL
    lm = dc.load_model(model_id, dtype=getattr(torch, args.dtype), attn_implementation="sdpa")
    run.note_bank(args.bank)
    run.note_model(lm.model_id, revision=lm.revision, dtype=str(lm.dtype),
                   attn_implementation="sdpa", num_layers=lm.num_layers,
                   hidden_size=lm.hidden_size)
    print(f"[extract] model={lm.model_id} layers={lm.num_layers} hidden={lm.hidden_size}")

    layers = (list(range(lm.num_layers)) if args.layers == "all"
              else [int(x) for x in args.layers.split(",") if x.strip() != ""])
    ll_layers = ([int(x) for x in args.logit_lens_layers.split(",") if x.strip() != ""]
                 if args.logit_lens_layers
                 else sorted(set(list(range(0, lm.num_layers, 4)) + [lm.num_layers - 1])))
    run.note(layers=layers, logit_lens_layers=ll_layers, bank=args.bank, n_bank_rows=len(rows))

    # THE BANK AND DTYPE THIS RUN IS ACTUALLY USING (defect T8 identity, 2026-08-19).
    # `run.note_bank` has already hashed the bank two ways; those hashes are what a fit payload
    # must be stamped with and what a consumed payload is checked against. Read back off the run
    # rather than recomputed, so there is ONE hashing implementation in play and this file cannot
    # drift from `common.rows_sha16` the way `bank_content_sha16` drifted (defect T11).
    run_bank_meta = read_run_bank_meta(run, args.bank)
    # `n_bank_rows_used` is len(rows) AFTER --limit, i.e. the prompt set this process actually has
    # in play. It is the only one of these fields that a `--limit` run does not share with a full
    # run over the same file. See validate_fit_identity.
    run_bank_meta["n_bank_rows_used"] = len(rows)
    run_bank_meta["bank_limit"] = int(args.limit or 0)
    fit_identity = {"fit_dtype": str(lm.dtype),
                    **{k: v for k, v in run_bank_meta.items() if k != "bank_n_rows"}}

    fitted: Dict[str, Dict] = {}
    summary_fit_validation: Dict[str, Dict] = {}
    if args.stage in ("fit", "both"):
        fitted = stage_fit(lm, dc, rows, layers, run, ledger, position=args.position,
                           fit_identity=fit_identity)
        # A --stage both run fits and scores in one process, so a mismatch here would be a bug in
        # THIS file rather than a mis-wired job. Validated anyway: the check costs nothing and a
        # silently self-inconsistent payload is exactly what T8 was.
        summary_fit_validation = {
            sp: validate_fit_identity(pl, path=f"<in-process:{sp}>", model=lm.model_id,
                                      position=args.position, layers=layers,
                                      bank_meta=run_bank_meta, dtype=str(lm.dtype), strict=True,
                                      # ONE-OF-TWO-PATHS: the flag is threaded through BOTH
                                      # consumer sites. It is structurally inert here (a
                                      # --stage both run fits and scores the same rows in one
                                      # process), and passing it anyway is what keeps the two
                                      # call sites from drifting apart again.
                                      allow_cross_bank=args.allow_cross_bank_fit)
            for sp, pl in fitted.items()}
    if args.stage == "score":
        src = args.fit_dir
        if not src:
            raise SystemExit("--stage score requires --fit-dir")
        # T8 (2026-08-18). A payload used to be loaded and used without ANYONE reading
        # `payload["meta"]`, which records the position, the model and the layers the directions
        # were FITTED on. The 2026-08-17 phantom-cell fix added a per-row assert that the READOUT
        # index matches --position; that proves where h was read, never where d was fitted, so
        # "fit at `last`, read at `codeword_last`" -- the original phantom cell -- and the worse
        # cross-model variant both still walked past every guard in the repo. The same blind load
        # sits in aggressive_patching.py (~404) and surgical_knockout.py (~240); the validator
        # lives in common.py so those two can adopt it without a third copy.
        # LATENT, verified before the fix: of the 70 committed runs carrying a fit_dir, 0 mismatch
        # on model or position. No committed number changes.
        fit_validation = {}
        for split in ("dev", "heldout"):
            p = os.path.join(src, f"directions_fit_{split}.pt")
            if os.path.exists(p):
                payload = torch.load(p, map_location="cpu", weights_only=False)
                fit_validation[split] = validate_fit_identity(
                    payload, path=p, model=lm.model_id, position=args.position, layers=layers,
                    bank_meta=run_bank_meta, dtype=str(lm.dtype), strict=True,
                    allow_cross_bank=args.allow_cross_bank_fit)
                fitted[split] = payload
        if not fitted:
            raise SystemExit(f"no directions_fit_*.pt under {src}")
        run.note(fit_dir=src, fit_dir_validation=fit_validation)
        summary_fit_validation = fit_validation
        n_nonfatal = sum(v.get("n_nonfatal_identity_problems", 0) for v in fit_validation.values())
        if n_nonfatal:
            # Non-fatal is not silent. These are real MISMATCHES that were downgraded because
            # something stronger certified the join; if they are never printed the downgrade is
            # indistinguishable from agreement, which is the state T8 was.
            for sp, v in fit_validation.items():
                for m in v.get("problems_nonfatal", []):
                    print(f"[extract] fit identity NON-FATAL MISMATCH ({sp}): {m}")
        n_unknown = sum(v.get("n_unknown_identity_fields", 0) for v in fit_validation.values())
        if n_unknown:
            print(f"[extract] {n_unknown} identity field(s) across {len(fit_validation)} fit "
                  f"payload(s) are UNRECORDED (a fit dir written before 2026-08-19 stamps no bank "
                  f"hash and no activation dtype). They are reported as `unknown_identity` in "
                  f"summary.json, NOT as agreement: an artifact that never recorded a field cannot "
                  f"certify it matches.")

    summary: Dict[str, object] = {"model": lm.model_id, "n_bank_rows": len(rows),
                                  "layers": layers, "logit_lens_layers": ll_layers,
                                  "splits_fitted": sorted(fitted),
                                  "position": args.position,
                                  "fit_dir_validation": summary_fit_validation,
                                  "fit_identity_unknown_fields": sum(
                                      v.get("n_unknown_identity_fields", 0)
                                      for v in summary_fit_validation.values()),
                                  "fit_identity_nonfatal_problems": sum(
                                      v.get("n_nonfatal_identity_problems", 0)
                                      for v in summary_fit_validation.values()),
                                  "cross_bank_fit": any(
                                      v.get("cross_bank_fit") for v in
                                      summary_fit_validation.values()),
                                  "cross_bank_fit_declared": bool(args.allow_cross_bank_fit),
                                  "bank_file_sha16": run_bank_meta["bank_file_sha16"],
                                  "bank_rows_sha16": run_bank_meta["bank_rows_sha16"],
                                  "activation_dtype": str(lm.dtype)}
    if args.stage in ("score", "both"):
        if not fitted:
            raise SystemExit("nothing fitted; cannot score")
        summary.update(stage_score(lm, dc, rows, layers, fitted, run, ledger,
                                   args.directions.split(","), ll_layers,
                                   cache_final_reps=not args.no_cache_reps,
                                   readout_id_mode=args.readout_ids,
                                   position=args.position))
        summary["gap_by_split"] = {s: {k: v for k, v in p["gap"].items()}
                                   for s, p in fitted.items()}

    run.finish(summary=summary, ledger=ledger)
    print(f"[extract] -> {run.path}")
    print(f"[extract] failures: {ledger.as_dict()['failure_reasons']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
