"""score_behavior.py — the behavioural + comprehension readouts for the bank (plan §5.3, §8, §9).

One GPU pass over the bank. Three kinds of row are handled differently, deliberately:

  query_kind = semantic_one_word     forward only. The answer IS the next token, so the safe
                                     semantic readout is p(concept) vs p(codeword) — no
                                     generation, no judge, no harmful text produced at all.
  query_kind = comprehension_usage   forward only. p("literal") vs p("codeword"): the plan §2.6
                                     comprehension control, so an intervention that lowers ASR
                                     by destroying comprehension can be told apart from one
                                     that lowers it by removing the mechanism.
  query_kind = behavioral            generation. Text goes to gens.jsonl (never stdout, never a
                                     subagent); the API judge runs separately in
                                     judge_boombness.py so GPU time is not spent waiting on
                                     OpenAI, and so re-judging at another threshold costs nothing.

The split between generating and judging is the house pattern and it matters for §2.2: the
continuous StrongReject score is always persisted, so ASR can be recomputed at 0.25 or 0.5
without regenerating anything.

Optional interventions (--intervene) apply a direction at a layer band while generating, which
is what plan §10.3/§10.4 needs; with no flag this is a clean baseline pass.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from typing import Dict, List, Optional, Sequence

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_DIR, FailureLedger, RunDir, ds, pair, read_jsonl, seed_everything  # noqa: E402
import signals as sg  # noqa: E402
from extract_boombness import resolve_occurrences  # noqa: E402

DEFAULT_BANK = os.path.join(DATA_DIR, "boombness_prompt_bank.jsonl")

# Answer-token groups for the forward-only readouts.
# Both must be SINGLE tokens with a leading space or the forced choice is unanswerable;
# signals.readout_ids enforces it. " codeword" is 3 tokens on Llama-3.1-8B, hence "coded".
COMPREHENSION_WORDS = ("literal", "coded")


@torch.no_grad()
def next_token_readout(lm, templated: str, groups: Dict[str, Sequence[int]]) -> Dict[str, float]:
    """Probability mass on each id group at the next-token position."""
    ids = lm.tokenizer(templated, add_special_tokens=False)["input_ids"]
    t = torch.tensor([ids], device=lm.model.device)
    logits = lm.model(input_ids=t, use_cache=False).logits[0, -1, :].float().cpu()
    lp = torch.log_softmax(logits, dim=-1)
    out = {}
    for name, g in groups.items():
        idx = torch.tensor(sorted(set(g)), dtype=torch.long)
        out[f"p_{name}"] = float(lp[idx].logsumexp(0).exp())
    return out


def make_intervention(dc, pc, lm, spec: Optional[Dict], payload: Optional[Dict]):
    """Return a list of context managers implementing --intervene, or []."""
    if not spec:
        return []
    name, mode, band, alpha = spec["direction"], spec["mode"], spec["layers"], spec["alpha"]
    dmap = payload[name] if name in payload else None
    if dmap is None:
        raise SystemExit(f"direction {name!r} not in the fitted payload")
    ctxs = []
    for L in band:
        d = dmap.get(L)
        if d is None:
            continue
        if mode == "project_out":
            ctxs.append(pc.AllPositionProjectOut(lm.model, L, d, alpha=alpha))
        elif mode == "add":
            ctxs.append(pc.AllPositionAdd(lm.model, L, d, alpha=alpha))
        else:
            raise SystemExit(f"unknown intervention mode {mode!r}")
    if not ctxs:
        raise SystemExit(f"intervention {name}/{mode} produced no hooks over layers {band}")
    return ctxs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", default=DEFAULT_BANK)
    ap.add_argument("--model", default=None)
    ap.add_argument("--query-kinds", default="semantic_one_word,comprehension_usage,behavioral")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--max-new", type=int, default=192)
    ap.add_argument("--no-generate", action="store_true",
                    help="skip the behavioral generation pass (forward readouts only)")
    ap.add_argument("--fit-dir", default=None, help="needed only with --intervene")
    ap.add_argument("--intervene", default="",
                    help='e.g. "d_surface:project_out:8-21:1.0" or "d_surface:add:8-21:2.0"')
    ap.add_argument("--arm", default="base", help="label written on every row")
    ap.add_argument("--readout-ids", default="primary", choices=["primary", "full_word"])
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--seed", type=int, default=20260816)
    ap.add_argument("--tag", default="run")
    args = ap.parse_args()
    seed_everything(args.seed)

    dc, pc = ds(), pair()
    rows = read_jsonl(args.bank)
    kinds = [k.strip() for k in args.query_kinds.split(",") if k.strip()]
    rows = [r for r in rows if r["query_kind"] in kinds]
    if args.limit:
        rows = rows[:args.limit]

    run = RunDir("score_behavior", args, tag=args.tag)
    ledger = FailureLedger()

    model_id = args.model or dc.PRIMARY_MODEL
    lm = dc.load_model(model_id, dtype=getattr(torch, args.dtype), attn_implementation="sdpa")
    run.note_model(lm.model_id, revision=lm.revision, dtype=str(lm.dtype),
                   attn_implementation="sdpa", num_layers=lm.num_layers)

    spec = None
    payload = None
    if args.intervene:
        name, mode, band_s, alpha_s = args.intervene.split(":")
        lo, hi = (int(x) for x in band_s.split("-"))
        spec = {"direction": name, "mode": mode, "layers": list(range(lo, hi + 1)),
                "alpha": float(alpha_s)}
        if not args.fit_dir:
            raise SystemExit("--intervene requires --fit-dir")
        # Cross-fit is not meaningful for an intervention applied to every row, so the
        # direction used is recorded explicitly instead of being silently chosen.
        p = os.path.join(args.fit_dir, "directions_fit_dev.pt")
        if not os.path.exists(p):
            p = os.path.join(args.fit_dir, "directions_fit_heldout.pt")
        payload = torch.load(p, map_location="cpu", weights_only=False)
        run.note(intervention=spec, intervention_direction_file=p)
        print(f"[score] intervention {spec} from {os.path.basename(p)}")

    concept = rows[0]["concept"]
    codeword = rows[0]["codeword"]
    # Symmetric, validated readout ids (signals.readout_ids): one whole-word token per side.
    # readout_id_pair itself raises on overlap or on a multi-token leading-space form.
    c_ids, w_ids, id_meta = sg.readout_id_pair(lm.tokenizer, concept, codeword,
                                               mode=args.readout_ids)
    comp_meta = {w: sg.readout_ids(lm.tokenizer, w) for w in COMPREHENSION_WORDS}
    comp_ids = {w: [comp_meta[w]["primary_id"]] for w in COMPREHENSION_WORDS}
    run.note(readout_ids=id_meta, comprehension_readout_ids=comp_meta,
             concept_token_ids=c_ids, codeword_token_ids=w_ids,
             comprehension_token_ids=comp_ids, arm=args.arm)
    print(f"[score] readout ids ({args.readout_ids}): concept={c_ids} codeword={w_ids} "
          f"comprehension={comp_ids}")

    gens_path = run.p("gens.jsonl")
    gens_fh = open(gens_path, "a")
    n_gen = 0
    counts = collections.Counter()

    for i, row in enumerate(rows):
        templated = dc.apply_template(lm.tokenizer, row["full_prompt"])
        base = {k: row.get(k) for k in
                ("prompt_id", "prompt_sha16", "family_id", "condition", "cell", "domain", "split",
                 "bank_block", "query_kind", "n_examples", "strength", "consistency",
                 "example_position", "role_style", "target_surface", "n_target_occurrences")}
        base["arm"] = args.arm
        base["model"] = lm.model_id

        # Position sanity: the readouts below are prompt-level, but a row whose occurrences
        # cannot be resolved is one whose bank metadata disagrees with the tokenizer, and it
        # must not be silently scored (plan §2.2).
        try:
            resolve_occurrences(dc, lm.tokenizer, row)
        except ValueError as e:
            ledger.fail(f"resolve:{e}", row["prompt_id"])
            continue

        try:
            ctxs = make_intervention(dc, pc, lm, spec, payload)
            import contextlib
            with contextlib.ExitStack() as st:
                for c in ctxs:
                    st.enter_context(c)

                if row["query_kind"] in ("semantic_one_word",):
                    rec = next_token_readout(lm, templated,
                                             {"concept": c_ids, "codeword": w_ids})
                    rec["semantic_margin"] = rec["p_concept"] - rec["p_codeword"]
                    run.log_row({**base, "readout": "semantic", **rec})
                    counts["semantic"] += 1

                elif row["query_kind"] == "comprehension_usage":
                    rec = next_token_readout(lm, templated,
                                             {w: comp_ids[w] for w in COMPREHENSION_WORDS})
                    rec["comprehension_margin"] = rec["p_coded"] - rec["p_literal"]
                    run.log_row({**base, "readout": "comprehension", **rec})
                    counts["comprehension"] += 1

                elif row["query_kind"] == "behavioral":
                    if args.no_generate:
                        counts["behavioral_skipped"] += 1
                    else:
                        g = dc.generate(lm, row["full_prompt"], max_new_tokens=args.max_new,
                                        templated=True)
                        text = g["text"] if isinstance(g, dict) else str(g)
                        gens_fh.write(json.dumps({**base, "generation": text,
                                                  "n_chars": len(text)}) + "\n")
                        gens_fh.flush()
                        run.log_row({**base, "readout": "generation",
                                     "gen_chars": len(text),
                                     "gen_empty": len(text.strip()) == 0})
                        n_gen += 1
                        counts["behavioral"] += 1
            ledger.ok()
        except Exception as e:
            ledger.fail(f"{row['query_kind']}:{type(e).__name__}:{str(e)[:80]}", row["prompt_id"])
            continue

        if (i + 1) % 100 == 0:
            print(f"[score] {i+1}/{len(rows)} rows  {dict(counts)}")

    gens_fh.close()
    run.finish(summary={"model": lm.model_id, "arm": args.arm, "n_bank_rows": len(rows),
                        "counts": dict(counts), "n_generations": n_gen,
                        "gens_path": gens_path if n_gen else None,
                        "intervention": spec,
                        "note": "ASR is NOT computed here — run judge_boombness.py on gens.jsonl"},
               ledger=ledger)
    print(f"[score] {dict(counts)} -> {run.path}")
    print(f"[score] failures: {ledger.as_dict()['failure_reasons']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
