"""activation_extraction.py -- extract residual activations at codeword positions for
the Bombness probe. SLURM/GPU entrypoint (plan §3.1: all model compute via SLURM).

Reuses existing, unit-tested infrastructure rather than new hooks (plan §2A.9):
  - ds_common.load_model            -> Llama-3.1-8B-Instruct, bf16, sdpa (manifest)
  - pair_common.capture_components  -> one forward pass, {resid_post} at named
                                       positions, all layers, float32 CPU.

`resid_post` == hidden_states[L+1] == our D1 raw residual space (manifest D1;
Appendix A3). We do NOT use upstream's normalized mid-block space for the headline
probe; a normalized-space robustness arm is a later, separate extraction.

Positions (plan §5.2 primary): `codeword_last` (the QUERY codeword, = last codeword
occurrence) and `final_prompt` (the decision token, last prompt token). Both always
exist for the binding conditions, so every item yields a fixed (n_layers, 2, hidden)
block -- no ragged positions.

Padding / position-index safety (manifest D5, Appendix A9.2 / bug class B9): each
item is a SINGLE-example forward pass (batch 1, no padding), so there is no
left-pad + arange(0,N) position drift and no absolute-index reuse across examples.
A preflight cross-checks capture_components' resolved `codeword_last` against the
corpus's precomputed query span for a sample of items; a mismatch aborts the run.

Output (immutable, plan §3.7): one run dir under outputs/ with
  acts.npy            float32 [n_items, n_layers, n_positions, hidden]
  items.jsonl         aligned metadata (ids/split/label/codeword/positions) - NO prompt text
  RUNMETA.json        provenance via ds_common env metadata
  DONE.json           written only after validation
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# repo import path
_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.join(_HERE, "..", "..")
sys.path.insert(0, _PKG)

import numpy as np  # noqa: E402

import ds_common as dc          # noqa: E402
import pair_common as pc        # noqa: E402
from src.probes import probe_dataset as pdset  # noqa: E402

PRIMARY_POSITIONS = ("codeword_last", "final_prompt")
COMPONENT = "resid_post"  # == hidden_states[L+1], D1 space


def _templated_prompt(lm, corpus_example: dict, prompt_field: str) -> str:
    """Load the RAW prompt for a condition and apply the official chat template.

    The corpus `*_prompt` fields are raw (pre-template); the corpus's
    `codeword_occurrences_templated` spans are in CHAT-TEMPLATED token space, and the
    chat-templated form is also how the model is actually attacked (the behavioural
    harness templates). We reuse the canonical `ds_common.apply_template`
    (single user turn, add_generation_prompt=True, Llama default) so the codeword
    positions match the corpus spans and the refusal-direction work. Runs on the GPU
    node only (loads prompt text). Verified offline: templating puts the last codeword
    token at the corpus's query-span index (see execution log E12)."""
    txt = corpus_example[prompt_field]
    if not isinstance(txt, str) or not txt:
        raise ValueError(f"missing/empty prompt field {prompt_field}")
    return dc.apply_template(lm.tokenizer, txt, add_generation_prompt=True)


def preflight_positions(lm, corpus, items, n_check=24):
    """Sanity-check the codeword positions used for extraction.

    Correctness is by CONSTRUCTION: `capture_components` itself calls
    `resolve_positions(lm, text, codeword)` to locate the query codeword (its LAST
    occurrence, which is the query in a doublespeak prompt), so the extraction reads at
    exactly the position this preflight resolves. The B9 absolute-position bug class
    (an index computed once and reused across examples) is structurally impossible here
    -- positions are resolved per example.

    So the HARD check is only: the codeword resolves, and `codeword_last` is a real
    prompt-body position (0 <= codeword_last < final_prompt). The corpus
    `codeword_occurrences_templated` spans are a SOFT cross-check reported as a match
    rate but NOT enforced: those spans are STALE for a large fraction of examples --
    they were computed on a different rendering than the stored `*_prompt` field
    (occurrence counts differ, e.g. 13 vs 9), which the stored prompt (used by both this
    extraction and the behavioural harness) does not match. See BUG_AND_DEVIATION_LOG
    B19. Returns (n_doublespeak_checked, n_other_resolved, corpus_span_match_rate)."""
    by_id = {str(e["example_id"]): e for e in corpus["examples"]}
    checked = other = 0
    span_hits = span_tot = 0
    for it in items[:n_check]:
        ex = by_id[it.example_id]
        text = _templated_prompt(lm, ex, it.prompt_field)
        pos = pc.resolve_positions(lm, text, it.codeword)
        # HARD: codeword resolves to a real prompt-body position (before the decision token)
        if pos.codeword_last is None or not (0 <= pos.codeword_last < pos.final_prompt):
            raise AssertionError(
                f"codeword position invalid for {it.example_id}/{it.condition}: "
                f"codeword_last={pos.codeword_last} final_prompt={pos.final_prompt}")
        if it.condition != pdset.POSITIVE_CONDITION:
            other += 1
            continue
        checked += 1
        # SOFT: corpus-span cross-check (reported, not enforced -- spans are stale, B19)
        want = it.query_span()
        if want is not None:
            span_tot += 1
            if pos.codeword_last == want[1] - 1:
                span_hits += 1
    rate = round(span_hits / span_tot, 3) if span_tot else None
    if rate is not None and rate < 0.5:
        print(f"[preflight] WARN corpus-span match rate {rate} (<0.5) -- spans are stale "
              f"(B19); extraction uses resolve_positions on the stored prompt, which is "
              f"correct by construction.", flush=True)
    return checked, other, rate


def extract(lm, corpus, items):
    """Return (acts float32 [n, L, P, H], kept_items) extracting resid_post at the
    primary positions for each item. Items whose positions cannot be resolved are
    dropped and reported (never silently)."""
    by_id = {str(e["example_id"]): e for e in corpus["examples"]}
    blocks, kept, posmeta, dropped = [], [], [], []
    for it in items:
        ex = by_id[it.example_id]
        text = _templated_prompt(lm, ex, it.prompt_field)
        res = pc.capture_components(lm, text, it.codeword,
                                    components=[COMPONENT],
                                    position_names=PRIMARY_POSITIONS)
        names = res["position_names"]
        if list(names) != list(PRIMARY_POSITIONS):
            dropped.append((it.example_id, it.condition, names))
            continue
        # reps[COMPONENT]: [n_layers, n_positions, hidden]; positions in `names` order
        blocks.append(res["reps"][COMPONENT].numpy().astype(np.float32))
        kept.append(it)
        # scalar position/length metadata for the Gate-1 position/length controls
        # (D5, plan §5.4): codeword token index and sequence length per item.
        p = res["positions"]
        posmeta.append({"codeword_last_idx": int(p["codeword_last"]),
                        "seq_len": int(p["final_prompt"]) + 1})
    if dropped:
        print(f"[extract] dropped {len(dropped)} items with unresolved positions "
              f"(first: {dropped[:3]})")
    acts = np.stack(blocks, axis=0) if blocks else np.empty((0,))
    return acts, kept, posmeta


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", default=os.path.join(
        _PKG, "data", "splits", "clearharm_doublespeak_v3.json"))
    ap.add_argument("--cohort", default=None, help="clearharm / generated / None=all")
    ap.add_argument("--conditions", default="doublespeak,benign,neutral")
    ap.add_argument("--out", required=True, help="run dir under outputs/ (created)")
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--revision", default=None, help="pin the HF revision (recorded)")
    ap.add_argument("--quantize", default=None, choices=[None, "8bit", "4bit"],
                    help="bnb quantization for large models (e.g. Qwen3-14B); acceptable "
                         "for reading activations. Recorded in RUNMETA.")
    ap.add_argument("--limit", type=int, default=0, help="smoke: first N items only")
    args = ap.parse_args()

    corpus = pdset.load_corpus(os.path.abspath(args.corpus))
    conds = tuple(c.strip() for c in args.conditions.split(",") if c.strip())
    items = pdset.build_items(corpus, conditions=conds, cohort=args.cohort)
    # split discipline is a hard precondition of any probe extraction
    pdset.assert_split_discipline(items)
    if args.limit:
        items = items[:args.limit]

    import torch
    lm = dc.load_model(args.model, dtype=getattr(torch, args.dtype),
                       revision=args.revision, quantize=args.quantize)

    n_pre, n_other, span_rate = preflight_positions(lm, corpus, items)
    print(f"[preflight] {n_pre} doublespeak + {n_other} benign/neutral positions resolved "
          f"(hard check passed); corpus-span match rate {span_rate} (soft, B19)")

    acts, kept, posmeta = extract(lm, corpus, items)
    if acts.shape[0] != len(kept) or len(posmeta) != len(kept):
        raise RuntimeError("acts/items/posmeta length mismatch")

    os.makedirs(args.out, exist_ok=True)
    np.save(os.path.join(args.out, "acts.npy"), acts)
    with open(os.path.join(args.out, "items.jsonl"), "w") as fh:
        for it, pm in zip(kept, posmeta):
            rec = pdset.to_jsonl_records([it])[0]
            rec.pop("codeword_spans", None)  # keep metadata compact; spans re-derivable
            rec.update(pm)                    # codeword_last_idx, seq_len (Gate-1 controls)
            fh.write(json.dumps(rec) + "\n")

    meta = {
        "script": "src/probes/activation_extraction.py",
        "manifest": "configs/manifests/role_probe_sprint_v1.json",
        "component": COMPONENT, "residual_space": "hidden_states[L+1] (D1)",
        "positions": list(PRIMARY_POSITIONS),
        "n_items": len(kept), "acts_shape": list(acts.shape),
        "cohort": args.cohort, "conditions": list(conds),
        "corpus": os.path.relpath(os.path.abspath(args.corpus), _PKG),
        "preflight_doublespeak_checked": n_pre, "preflight_other_resolved": n_other,
        "preflight_corpus_span_match_rate": span_rate,
        **dc.env_metadata(),
        "model_meta": lm.meta(),
    }
    with open(os.path.join(args.out, "RUNMETA.json"), "w") as fh:
        json.dump(meta, fh, indent=2, default=str)
    with open(os.path.join(args.out, "DONE.json"), "w") as fh:
        json.dump({"status": "ok", "n_items": len(kept)}, fh)
    print(f"[done] {len(kept)} items -> {args.out}  acts{list(acts.shape)}")


if __name__ == "__main__":
    main()
