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
def forward_hidden(lm, ids: List[int]) -> torch.Tensor:
    """Return hidden states as [n_blocks+1, seq, H] float32 on CPU (index 0 = embeddings)."""
    t = torch.tensor([ids], device=lm.model.device)
    out = lm.model(input_ids=t, output_hidden_states=True, use_cache=False)
    return torch.stack([h[0].float().cpu() for h in out.hidden_states], dim=0)


# --------------------------------------------------------------------------- #
# Stage: fit
# --------------------------------------------------------------------------- #
def stage_fit(lm, dc, rows: List[Dict], layers: List[int], run: RunDir,
              ledger: FailureLedger, position: str = "codeword_last") -> Dict[str, Dict]:
    """Accumulate 2x2 cell means per split, then estimate directions per split."""
    sums: Dict[str, Dict[str, Dict[int, torch.Tensor]]] = collections.defaultdict(
        lambda: collections.defaultdict(dict))
    counts: Dict[str, collections.Counter] = collections.defaultdict(collections.Counter)

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
        hs = forward_hidden(lm, ids)
        cell = COND_TO_CELL[row["condition"]]
        split = row["split"]
        for L in layers:
            v = hs[L + 1, pos, :]
            cur = sums[split][cell].get(L)
            sums[split][cell][L] = v if cur is None else cur + v
        counts[split][cell] += 1
        ledger.ok()

    fitted: Dict[str, Dict] = {}
    for split, cells in sums.items():
        means = {c: {L: v / counts[split][c] for L, v in per_layer.items()}
                 for c, per_layer in cells.items()}
        try:
            dset = sg.estimate_directions(
                means, n_per_cell=dict(counts[split]),
                meta={"split_fitted_on": split, "position": position,
                      "model": lm.model_id, "n_fit_rows": sum(counts[split].values())})
        except ValueError as e:
            ledger.fail(f"fit_directions:{e}", split)
            continue
        payload = dset.as_payload()
        payload["cell_means"] = means
        path = run.p(f"directions_fit_{split}.pt")
        torch.save(payload, path)
        fitted[split] = payload
        print(f"[fit] split={split} cells={dict(counts[split])} -> {os.path.basename(path)}")
        for name in ("d_surface", "d_context", "d_inter", "d_naive"):
            g = dset.gap[name]
            print(f"       ||{name}|| by layer: " +
                  " ".join(f"L{L}={g[L]:.2f}" for L in layers[::max(1, len(layers)//8)]))
    return fitted


# --------------------------------------------------------------------------- #
# Stage: score
# --------------------------------------------------------------------------- #
def _cross_fit_split(split: str, available: Sequence[str]) -> str:
    """Score a dev row with heldout-fitted directions and vice versa."""
    other = "heldout" if split == "dev" else "dev"
    if other in available:
        return other
    return split


@torch.no_grad()
def stage_score(lm, dc, rows: List[Dict], layers: List[int], fitted: Dict[str, Dict],
                run: RunDir, ledger: FailureLedger, dir_names: Sequence[str],
                logit_lens_layers: Sequence[int], cache_final_reps: bool) -> Dict:
    tok = lm.tokenizer
    concept_ids = sg.word_token_ids(tok, rows[0]["concept"])
    codeword_ids = sg.word_token_ids(tok, rows[0]["codeword"])
    c_ids = sorted(set(concept_ids["all_first_ids"]))
    w_ids = sorted(set(codeword_ids["all_first_ids"]))
    run.note(concept_token_ids=c_ids, codeword_token_ids=w_ids,
             concept_variants={k: v for k, v in concept_ids.items()},
             codeword_variants={k: v for k, v in codeword_ids.items()},
             layer_convention=sg.LAYER_CONVENTION)
    print(f"[score] concept first-ids={c_ids} codeword first-ids={w_ids}")

    cache: Dict[str, torch.Tensor] = {}
    n_scored = 0
    for row in rows:
        try:
            _, ids, last, following, n_sub = resolve_occurrences(dc, tok, row)
        except ValueError as e:
            ledger.fail(f"score:{e}", row["prompt_id"])
            continue
        fit_split = _cross_fit_split(row["split"], list(fitted))
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
                "directions_fitted_on": fit_split,
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
                                   cache_final_reps=not args.no_cache_reps))
        summary["gap_by_split"] = {s: {k: v for k, v in p["gap"].items()}
                                   for s, p in fitted.items()}

    run.finish(summary=summary, ledger=ledger)
    print(f"[extract] -> {run.path}")
    print(f"[extract] failures: {ledger.as_dict()['failure_reasons']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
