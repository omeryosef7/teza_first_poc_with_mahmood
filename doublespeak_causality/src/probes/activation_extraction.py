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


def _prompt_text(corpus_example: dict, prompt_field: str) -> str:
    """Load the templated prompt text for a condition. Runs on the GPU node only."""
    txt = corpus_example[prompt_field]
    if not isinstance(txt, str) or not txt:
        raise ValueError(f"missing/empty prompt field {prompt_field}")
    return txt


def preflight_positions(lm, corpus, items, n_check=8):
    """Cross-check capture_components' resolved codeword_last against the corpus's
    precomputed query span. Guards the absolute-position bug class (B9). Aborts on any
    mismatch. Returns the number checked."""
    by_id = {str(e["example_id"]): e for e in corpus["examples"]}
    checked = 0
    for it in items[:n_check]:
        ex = by_id[it.example_id]
        text = _prompt_text(ex, it.prompt_field)
        pos = pc.resolve_positions(lm, text, it.codeword)
        want = it.query_span()  # (start, end) into templated tokens
        if want is None:
            continue
        # corpus span is [start, end); the query codeword's last token is end-1.
        # resolve_positions.codeword_last is a single token index for a single-token
        # codeword. For single-token codewords, end-1 == start.
        exp_tok = want[1] - 1
        if pos.codeword_last != exp_tok:
            raise AssertionError(
                f"position mismatch for {it.example_id}/{it.condition}: "
                f"capture={pos.codeword_last} corpus_query_last={exp_tok} "
                f"(absolute-position bug class B9 -- aborting)")
        checked += 1
    return checked


def extract(lm, corpus, items):
    """Return (acts float32 [n, L, P, H], kept_items) extracting resid_post at the
    primary positions for each item. Items whose positions cannot be resolved are
    dropped and reported (never silently)."""
    by_id = {str(e["example_id"]): e for e in corpus["examples"]}
    blocks, kept, dropped = [], [], []
    for it in items:
        ex = by_id[it.example_id]
        text = _prompt_text(ex, it.prompt_field)
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
    if dropped:
        print(f"[extract] dropped {len(dropped)} items with unresolved positions "
              f"(first: {dropped[:3]})")
    acts = np.stack(blocks, axis=0) if blocks else np.empty((0,))
    return acts, kept


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
                       revision=args.revision)

    n_pre = preflight_positions(lm, corpus, items)
    print(f"[preflight] verified {n_pre} codeword positions against corpus spans")

    acts, kept = extract(lm, corpus, items)
    if acts.shape[0] != len(kept):
        raise RuntimeError("acts/items length mismatch")

    os.makedirs(args.out, exist_ok=True)
    np.save(os.path.join(args.out, "acts.npy"), acts)
    with open(os.path.join(args.out, "items.jsonl"), "w") as fh:
        for it in kept:
            rec = pdset.to_jsonl_records([it])[0]
            rec.pop("codeword_spans", None)  # keep metadata compact; spans re-derivable
            fh.write(json.dumps(rec) + "\n")

    meta = {
        "script": "src/probes/activation_extraction.py",
        "manifest": "configs/manifests/role_probe_sprint_v1.json",
        "component": COMPONENT, "residual_space": "hidden_states[L+1] (D1)",
        "positions": list(PRIMARY_POSITIONS),
        "n_items": len(kept), "acts_shape": list(acts.shape),
        "cohort": args.cohort, "conditions": list(conds),
        "corpus": os.path.relpath(os.path.abspath(args.corpus), _PKG),
        "preflight_checked": n_pre,
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
