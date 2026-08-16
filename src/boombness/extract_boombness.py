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
from common import DATA_DIR, FailureLedger, OUT_ROOT, RunDir, ds, read_jsonl, seed_everything  # noqa: E402
import signals as sg  # noqa: E402

DEFAULT_BANK = os.path.join(DATA_DIR, "boombness_prompt_bank.jsonl")
CORE_2X2 = ("benign_literal", "direct_harmful", "natural_doublespeak", "concept_in_benign_ctx")
COND_TO_CELL = {"benign_literal": "A", "direct_harmful": "B",
                "natural_doublespeak": "C", "concept_in_benign_ctx": "E"}
CORE_2X2_CELLS = ("A", "B", "C", "E")


# --------------------------------------------------------------------------- #
# Occurrence resolution
# --------------------------------------------------------------------------- #
def resolve_occurrences(dc, tok, row: Dict) -> Tuple[str, List[int], List[int], List[int], List[int]]:
    """Return (templated_text, input_ids, last_idx_per_occurrence, following_idx, n_subtokens).

    `n_subtokens` per occurrence is returned and recorded because the tokenization audit
    showed the target is NOT uniformly one token across arms on every model — and a
    2-subtoken occurrence puts a different vector at `codeword_last` (its last piece, e.g.
    "rot") than a 1-subtoken one. Downstream analysis must be able to condition on it rather
    than average over it.

    Raises ValueError with a specific reason if the occurrences cannot be resolved or do not
    match the character-level count the generator recorded.
    """
    templated = dc.apply_template(tok, row["full_prompt"])
    ids = tok(templated, add_special_tokens=False)["input_ids"]
    hit = dc.find_word_occurrences_in_text(tok, templated, row["target_surface"],
                                           add_special_tokens=False)
    last = list(hit.last_idx)
    if len(last) != row["n_target_occurrences"]:
        raise ValueError(f"occurrence_count_mismatch:text={row['n_target_occurrences']},"
                         f"tokens={len(last)}")
    if not last:
        raise ValueError("no_target_occurrence")
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
              ledger: FailureLedger, position: str = "codeword_last") -> Dict[str, Dict]:
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
        pos = last[-1] if position == "codeword_last" else following[-1]
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
                      "n_cell_family_entries_dropped": n_dropped})
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
                readout_id_mode: str = "primary") -> Dict:
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

        hs = forward_hidden(lm, ids)
        n_occ = len(last)
        for occ_i, (pos, fpos, nsub) in enumerate(zip(last, following, n_sub)):
            rec: Dict[str, object] = {
                "prompt_id": row["prompt_id"], "family_id": row["family_id"],
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
                        continue
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
            cache[row["prompt_id"]] = torch.stack(
                [hs[L + 1, last[-1], :] for L in layers], dim=0).half()
        ledger.ok()
        n_scored += 1
        if n_scored % 100 == 0:
            print(f"[score] {n_scored}/{len(rows)} rows")

    if cache_final_reps and cache:
        os.makedirs(run.cache, exist_ok=True)
        torch.save({"layers": layers, "layer_convention": sg.LAYER_CONVENTION,
                    "position": "codeword_last(final occurrence)",
                    "dtype": "float16", "reps": cache},
                   os.path.join(run.cache, "final_occurrence_reps.pt"))
        print(f"[score] cached {len(cache)} final-occurrence rep stacks")
    return {"n_scored_rows": n_scored}


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
    ap.add_argument("--position", default="codeword_last", choices=["codeword_last", "following"])
    ap.add_argument("--readout-ids", default="primary", choices=["primary", "full_word"],
                    help="which token ids stand for the words in the logit lens; 'primary' is "
                         "the single leading-space whole-word token per side (symmetric)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--seed", type=int, default=20260816)
    ap.add_argument("--tag", default="run")
    ap.add_argument("--no-cache-reps", action="store_true")
    args = ap.parse_args()
    seed_everything(args.seed)

    dc = ds()
    rows = read_jsonl(args.bank)
    if args.limit:
        rows = rows[:args.limit]

    run = RunDir("extract_boombness", args, tag=args.tag, want_cache=True)
    ledger = FailureLedger()

    model_id = args.model or dc.PRIMARY_MODEL
    lm = dc.load_model(model_id, dtype=getattr(torch, args.dtype), attn_implementation="sdpa")
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

    fitted: Dict[str, Dict] = {}
    if args.stage in ("fit", "both"):
        fitted = stage_fit(lm, dc, rows, layers, run, ledger, position=args.position)
    if args.stage == "score":
        src = args.fit_dir
        if not src:
            raise SystemExit("--stage score requires --fit-dir")
        for split in ("dev", "heldout"):
            p = os.path.join(src, f"directions_fit_{split}.pt")
            if os.path.exists(p):
                fitted[split] = torch.load(p, map_location="cpu", weights_only=False)
        if not fitted:
            raise SystemExit(f"no directions_fit_*.pt under {src}")
        run.note(fit_dir=src)

    summary: Dict[str, object] = {"model": lm.model_id, "n_bank_rows": len(rows),
                                  "layers": layers, "logit_lens_layers": ll_layers,
                                  "splits_fitted": sorted(fitted),
                                  "position": args.position}
    if args.stage in ("score", "both"):
        if not fitted:
            raise SystemExit("nothing fitted; cannot score")
        summary.update(stage_score(lm, dc, rows, layers, fitted, run, ledger,
                                   args.directions.split(","), ll_layers,
                                   cache_final_reps=not args.no_cache_reps,
                                   readout_id_mode=args.readout_ids))
        summary["gap_by_split"] = {s: {k: v for k, v in p["gap"].items()}
                                   for s, p in fitted.items()}

    run.finish(summary=summary, ledger=ledger)
    print(f"[extract] -> {run.path}")
    print(f"[extract] failures: {ledger.as_dict()['failure_reasons']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
