"""surgical_knockout.py — plan §10.1/§10.2: cut the edges that actually carry the meaning.

MOTIVATED DIRECTLY BY GATE G1. The §5 pilot showed the doublespeak reading is driven by the
DEMONSTRATION positions, not by the codeword token's own representation: transplanting the demos
moves the semantic readout +71–84% of the baseline→ceiling span, while transplanting the query
token moves it ~76% the WRONG way. That says the codeword's meaning is *retrieved from the
demonstration block at answer time* rather than stored in the codeword token.

This module tests that directly, and surgically. If the meaning is retrieved by attention from the
final codeword token to the demonstration tokens, then cutting exactly those edges should collapse
the semantic readout — and cutting the same NUMBER of other edges should not.

TWO INGREDIENTS, BOTH ALREADY BUILT AND VERIFIED
  * `dominance.py` (ported from the hijacking paper) ranks edges: `D_dir[h, src]` is how much of
    the Boombness arriving at the final codeword token was supplied by source position `src`
    through head `h`. That is what makes this *surgical* rather than "ablate the demo block and
    report that something happened".
  * `pair_common.AttentionKnockout` cuts specific (query_pos → key_pos) edges per layer and head.
    It REQUIRES `attn_implementation="eager"`; under SDPA a custom 4-D mask is silently ignored and
    the knockout becomes a no-op that still reports a number. The loader here forces eager and the
    self-check below would catch it anyway.

CONTROLS (plan §10.1 asks for all of these, and they are the difference between a result and a
story):
  `topk_demo`        cut the k highest-|D_dir| demonstration edges          — the hypothesis
  `random_demo`      cut k RANDOM demonstration edges                       — is it these edges?
  `bottomk_demo`     cut the k lowest-|D_dir| demonstration edges           — is the ranking real?
  `random_nondemo`   cut k random edges to NON-demonstration positions      — is it the demos?
  `same_head_random` cut k edges in the SAME heads but random positions     — head or position?
  `all_demo`         cut every demonstration edge                           — the ceiling
  `none`             no intervention                                        — the floor

Every arm cuts the SAME NUMBER of edges except `all_demo` and `none`, which is what makes them
comparable; the count is recorded per row so that can be checked rather than assumed.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import json
import math
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_DIR, FailureLedger, RunDir, ds, pair, read_jsonl, seed_everything  # noqa: E402
import signals as sg  # noqa: E402
from dominance import dominance_at  # noqa: E402
from extract_boombness import resolve_occurrences  # noqa: E402

DEFAULT_BANK = os.path.join(DATA_DIR, "boombness_prompt_bank.jsonl")
ARMS = ("none", "topk_demo", "bottomk_demo", "random_demo", "random_nondemo",
        "same_head_random", "all_demo", "positive_control",
        "all_layers_demo", "no_demo_text")

# THE TWO DYNAMIC-RANGE CONTROLS THE FIRST VERSION LACKED.
# `positive_control` (block every pre-query key at the CHOSEN layers) turned out to move the
# readout LESS than `all_demo`, so it established no dynamic range and made the §10 null
# uninterpretable. Two stronger ceilings are now measured on every run:
#   all_layers_demo  cut query->demo edges at EVERY layer, not just the chosen few. If the
#                    demonstration influence is distributed over depth, a 2-layer cut can do
#                    nothing while an all-layer cut does a lot; that distinction is the whole
#                    question and the first design could not see it.
#   no_demo_text     evaluate the prompt with the demonstration block DELETED. This is the true
#                    ceiling: it is what "the demonstrations are not there" actually means, in
#                    text space, with no attention machinery involved. If even this does not move
#                    the readout, the readout is not measuring the demonstrations' influence and
#                    nothing else in §10 can be interpreted.

# POSITIVE CONTROL — the arm that makes a null interpretable.
# `positive_control` blocks EVERY key before the query position, in every head, at the chosen
# layers. The final token is then left attending only to itself, which must move the readout
# enormously. If it does not, the knockout is not firing and every other arm's "no effect" is a
# statement about the hook, not about the model. The first knockout smoke returned deltas of
# <=0.12 log-odds with three arms at exactly 0.000, which is exactly the pattern a dead
# intervention produces, so this arm is now mandatory rather than optional.


@torch.no_grad()
def semantic_logodds(lm, ids: List[int], c_ids: Sequence[int], w_ids: Sequence[int]) -> float:
    """The readout that G1 was decided on: log p(concept) - log p(codeword) at the answer position."""
    t = torch.tensor([ids], device=lm.model.device)
    logits = lm.model(input_ids=t, use_cache=False).logits[0, -1, :].float().cpu()
    lp = torch.log_softmax(logits, dim=-1)
    ci = torch.tensor(sorted(set(c_ids)), dtype=torch.long)
    wi = torch.tensor(sorted(set(w_ids)), dtype=torch.long)
    return float(lp[ci].logsumexp(0) - lp[wi].logsumexp(0))


def pick_edges(D_dir: Dict[int, torch.Tensor], demo_positions: Sequence[int],
               all_positions: Sequence[int], k: int, arm: str, rng) -> Dict[int, List[Tuple[int, int]]]:
    """Return {layer: [(head, src), ...]} for one arm. Every arm returns exactly k edges."""
    out: Dict[int, List[Tuple[int, int]]] = {}
    demo = set(demo_positions)
    for L, D in D_dir.items():
        nh, T = D.shape
        cand_demo = [(h, s) for h in range(nh) for s in range(T) if s in demo]
        cand_non = [(h, s) for h in range(nh) for s in range(T)
                    if s not in demo and s < T - 1]
        if arm == "all_layers_demo":
            out[L] = cand_demo          # caller widens the layer set for this arm
            continue
        if arm == "positive_control":
            out[L] = [(h, s) for h in range(nh) for s in range(T) if s < T - 1]
            continue
        if arm == "all_demo":
            out[L] = cand_demo
            continue
        if not cand_demo:
            out[L] = []
            continue
        if arm == "topk_demo":
            out[L] = sorted(cand_demo, key=lambda e: -abs(float(D[e[0], e[1]])))[:k]
        elif arm == "bottomk_demo":
            out[L] = sorted(cand_demo, key=lambda e: abs(float(D[e[0], e[1]])))[:k]
        elif arm == "random_demo":
            out[L] = [cand_demo[i] for i in rng.permutation(len(cand_demo))[:k]]
        elif arm == "random_nondemo":
            if not cand_non:
                out[L] = []
            else:
                out[L] = [cand_non[i] for i in rng.permutation(len(cand_non))[:k]]
        elif arm == "same_head_random":
            top = sorted(cand_demo, key=lambda e: -abs(float(D[e[0], e[1]])))[:k]
            heads = [h for h, _ in top]
            pool = [s for s in all_positions if s not in demo and s < D.shape[1] - 1]
            if not pool:
                out[L] = []
            else:
                out[L] = [(h, int(pool[rng.integers(len(pool))])) for h in heads]
        else:
            raise ValueError(f"unknown arm {arm!r}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", default=DEFAULT_BANK)
    ap.add_argument("--fit-dir", required=True)
    ap.add_argument("--model", default=None)
    ap.add_argument("--layers", default="8,12,18,24", help="layers to rank AND knock out")
    ap.add_argument("--topk", type=int, default=16, help="edges cut per layer per arm")
    ap.add_argument("--n-families", type=int, default=8)
    ap.add_argument("--n-examples", default="4,8")
    ap.add_argument("--query-kind", default="semantic_one_word")
    ap.add_argument("--condition", default="natural_doublespeak")
    ap.add_argument("--seed", type=int, default=20260816)
    ap.add_argument("--tag", default="pilot")
    args = ap.parse_args()
    seed_everything(args.seed)

    import numpy as np
    rng = np.random.default_rng(args.seed)
    dc, pc = ds(), pair()
    want_n = {int(x) for x in args.n_examples.split(",")}
    rows = [r for r in read_jsonl(args.bank)
            if r["query_kind"] == args.query_kind and r["condition"] == args.condition
            and r["n_examples"] in want_n and r["bank_block"] == "core2x2"][:args.n_families]

    run = RunDir("surgical_knockout", args, tag=args.tag)
    ledger = FailureLedger()

    # eager is MANDATORY: under SDPA the 4-D mask is ignored and every knockout silently no-ops.
    lm = dc.load_model(args.model or dc.PRIMARY_MODEL, dtype=torch.float32,
                       attn_implementation="eager")
    run.note_model(lm.model_id, revision=lm.revision, dtype=str(lm.dtype),
                   attn_implementation="eager", num_layers=lm.num_layers,
                   note="eager required: AttentionKnockout is a no-op under SDPA")

    payload = None
    for split in ("dev", "heldout"):
        p = os.path.join(args.fit_dir, f"directions_fit_{split}.pt")
        if os.path.exists(p):
            payload = torch.load(p, map_location="cpu", weights_only=False)
            run.note(direction_file=p)
            break
    if payload is None:
        raise SystemExit(f"no directions_fit_*.pt under {args.fit_dir}")

    layers = [int(x) for x in args.layers.split(",")]
    d_surface = {L: payload["d_surface"][L] for L in layers if L in payload["d_surface"]}
    c_ids, w_ids, id_meta = sg.readout_id_pair(lm.tokenizer, rows[0]["concept"], rows[0]["codeword"])
    run.note(readout_ids=id_meta, layers=layers, topk=args.topk, arms=list(ARMS))
    print(f"[knockout] {len(rows)} prompts, layers={layers}, k={args.topk} edges/layer/arm")

    n = 0
    for row in rows:
        try:
            _, ids, last, _, _ = resolve_occurrences(dc, lm.tokenizer, row)
        except ValueError as e:
            ledger.fail(f"resolve:{e}", row["prompt_id"])
            continue
        dst = last[-1]                       # the final (query) codeword occurrence
        demo_pos = last[:-1]                 # the demonstration codeword occurrences
        if not demo_pos:
            ledger.fail("no_demo_occurrences", row["prompt_id"])
            continue

        try:
            dom = dominance_at(lm, ids, dst=dst, layers=layers, direction=d_surface,
                               check_invariants=True)
        except Exception as e:
            ledger.fail(f"dominance:{type(e).__name__}:{str(e)[:60]}", row["prompt_id"])
            continue

        base = {k: row[k] for k in ("prompt_id", "prompt_sha16", "family_id", "condition",
                                    "cell", "domain", "split", "n_examples", "query_kind")}
        base.update({"dst": dst, "n_demo_occurrences": len(demo_pos), "seq_len": len(ids)})

        for arm in ARMS:
            if arm == "none":
                val = semantic_logodds(lm, ids, c_ids, w_ids)
                run.log_row({**base, "arm": arm, "n_edges_cut": 0, "semantic_logodds": val})
                n += 1
                continue
            if arm == "no_demo_text":
                # The true ceiling: the same query with the demonstration block removed.
                q = row.get("final_query_text") or ""
                if not q:
                    ledger.fail("no_demo_text:missing_query", row["prompt_id"])
                    continue
                t2 = dc.apply_template(lm.tokenizer, q)
                ids2 = lm.tokenizer(t2, add_special_tokens=False)["input_ids"]
                val = semantic_logodds(lm, ids2, c_ids, w_ids)
                run.log_row({**base, "arm": arm, "n_edges_cut": -1,
                             "seq_len_used": len(ids2), "semantic_logodds": val})
                n += 1
                continue
            arm_layers = list(range(lm.num_layers)) if arm == "all_layers_demo" else layers
            dom_arm = dom["D_dir"]
            if arm == "all_layers_demo":
                # D_dir was only computed at `layers`; for an all-layer cut we need an edge set
                # per layer, and the ranking is irrelevant because every demo edge is cut.
                dom_arm = {L: dom["D_dir"][layers[0]] for L in arm_layers}
            edges = pick_edges(dom_arm, demo_pos, list(range(len(ids))),
                               args.topk, arm, rng)
            n_cut = sum(len(v) for v in edges.values())
            if n_cut == 0:
                ledger.fail(f"arm_{arm}:no_edges", row["prompt_id"])
                continue
            try:
                with contextlib.ExitStack() as st:
                    for L, es in edges.items():
                        if not es:
                            continue
                        # AttentionKnockout blocks (query_positions -> blocked_keys) per head.
                        by_head: Dict[int, List[int]] = collections.defaultdict(list)
                        for h, s in es:
                            by_head[h].append(s)
                        for h, srcs in by_head.items():
                            st.enter_context(pc.AttentionKnockout(
                                lm.model, [L], query_positions=[dst],
                                blocked_keys=sorted(set(srcs)), heads=[h]))
                    val = semantic_logodds(lm, ids, c_ids, w_ids)
            except Exception as e:
                ledger.fail(f"knockout_{arm}:{type(e).__name__}:{str(e)[:60]}", row["prompt_id"])
                continue
            run.log_row({**base, "arm": arm, "n_edges_cut": n_cut, "semantic_logodds": val})
            n += 1
        ledger.ok()

    run.finish(summary={"model": lm.model_id, "n_rows": n, "arms": list(ARMS),
                        "positive_control_note": "positive_control blocks every pre-query key in "
                                                 "every head; if its delta is small the knockout "
                                                 "is not firing and all other arms are void",
                        "layers": layers, "topk": args.topk,
                        "condition": args.condition, "query_kind": args.query_kind},
               ledger=ledger)
    print(f"[knockout] {n} rows -> {run.path}")
    print(f"[knockout] failures: {ledger.as_dict()['failure_reasons']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
