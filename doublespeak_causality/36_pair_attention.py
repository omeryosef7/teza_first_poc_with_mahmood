"""
36_pair_attention.py — CAUSAL_CORE_PLAN §6 + §16.10 (S8). Phase C: where the mapping
travels, and through which component.

Two intervention families on the fixed pair, both scored with the SAME forward-only
semantic score used everywhere else, so the numbers are directly comparable to the
residual-stream sweeps of `34_intervention_sweep.py`:

  --mode knockout   block attention FROM the final codeword token TO a source set:
                      prev_codewords    earlier occurrences of the codeword
                      demos_all         every demonstration token (request intact)
                      demos_first/last  only the first / only the final demonstration
                      request_only      the request, demonstrations intact  [control]
                      random_matched    count-matched random earlier tokens  [control]
                    at three granularities (plan §6 coarse-to-fine):
                      all_layers -> per_layer -> head_groups -> per_head
                    Per-head knockout does not exist anywhere in the prior code; it is
                    added in pair_common.AttentionKnockout by expanding the mask over the
                    query-head axis.

  --mode component  patch the codeword's attention output vs its MLP output vs the full
                    residual, Neutral<-DS and DS<-Neutral, per layer. This is what
                    separates ACQUISITION of the mapping (attention writes it) from
                    CONSOLIDATION (the MLP fixes it into the residual).

EAGER ATTENTION IS MANDATORY for --mode knockout: under SDPA/flash a custom additive 4-D
mask is not applied verbatim and the knockout silently becomes a no-op. The script loads
with attn_implementation="eager" and asserts the mask it receives is 4-D.

Usage:
  python 36_pair_attention.py --bench ... --reps-dir ... --mode knockout --granularity per_layer
"""
import os
import sys
import json
import time
import random
import argparse

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds_common as dc
import pair_common as pc

HERE = os.path.dirname(os.path.abspath(__file__))

SOURCE_SETS = ("prev_codewords", "demos_all", "demos_first", "demos_last",
               "request_only", "random_matched")


def source_positions(lm, templated, probe, name, rng):
    """Key positions to block, per source-set name. Returns [] when not applicable."""
    ids = lm.tokenizer(templated, add_special_tokens=False)["input_ids"]
    hit = dc.find_word_occurrences(lm.tokenizer, ids, probe)
    cw_last = hit.last_idx[-1]
    prev = hit.last_idx[:-1]
    # demo/request boundary: shared, F2-corrected implementation (see ds_common)
    req_start, located = dc.request_start_token(lm.tokenizer, templated, hit.first_idx[-1])
    demos = list(range(0, req_start))

    if name == "prev_codewords":
        return prev, located
    if name == "demos_all":
        return demos, located
    if name in ("demos_first", "demos_last"):
        # split the demo span at newlines: one demonstration per line
        nl = [i for i, t in enumerate(ids[:req_start])
              if "\n" in lm.tokenizer.decode([t])]
        if not nl:
            return [], located
        if name == "demos_first":
            return list(range(0, nl[0] + 1)), located
        return list(range(nl[-1] + 1, req_start)), located
    if name == "request_only":
        return [p for p in range(req_start, len(ids)) if p != cw_last], located
    if name == "random_matched":
        pool = [p for p in range(0, req_start) if p not in set(hit.last_idx)]
        k = min(len(demos), len(pool))
        return sorted(rng.sample(pool, k)) if k else [], located
    raise ValueError(name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--reps-dir", default=None,
                    help="required for --mode component (supplies the source reps)")
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(HERE, "outputs"))
    ap.add_argument("--mode", required=True, choices=["knockout", "component"])
    ap.add_argument("--granularity", default="per_layer",
                    choices=["all_layers", "per_layer", "head_groups", "per_head"])
    ap.add_argument("--readout", default="cloze")
    ap.add_argument("--demo-styles", default="",
                    help="comma list; empty => all. Use the S2 gate-passing styles.")
    ap.add_argument("--layers", default="", help="comma ints; empty => all")
    ap.add_argument("--head-group-size", type=int, default=8)
    ap.add_argument("--n-prompts", type=int, default=12)
    ap.add_argument("--splits", default="dev,heldout")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    rng = random.Random(args.seed)
    bench = json.load(open(args.bench))
    pair = bench["pair"]

    styles = {s.strip() for s in args.demo_styles.split(",") if s.strip()}
    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    rows = [r for r in bench["semantic"]
            if r["readout"] == args.readout and r["split"] in splits
            and (not styles or r["demo_style"] in styles)]

    # eager attention is REQUIRED for the mask-based knockout to have any effect
    attn = "eager" if args.mode == "knockout" else "sdpa"
    lm = dc.load_model(args.model, attn_implementation=attn)
    L = lm.num_layers
    n_heads = int(lm.model.config.num_attention_heads)
    layers = ([int(x) for x in args.layers.split(",") if x.strip()]
              if args.layers else list(range(L)))

    id_groups = {r: pc.word_first_ids(lm.tokenizer, pair[r])
                 for r in ("concept", "codeword") if pair.get(r)}

    tag = args.model.split("/")[-1]
    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(
        args.out_root,
        f"pair_attn_{args.mode}_{tag}_{time.strftime('%Y%m%d_%H%M%S')}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    print(f"[attn] mode={args.mode} gran={args.granularity} attn_impl={attn} "
          f"L={L} heads={n_heads} rows={len(rows)} -> {out_dir}")

    raw = open(os.path.join(out_dir, "attn_raw.jsonl"), "w")
    n_rows, n_unlocated = 0, 0

    def emit(rec):
        nonlocal n_rows
        raw.write(json.dumps(rec) + "\n")
        n_rows += 1
        if n_rows % 200 == 0:
            print(f"  [attn] {n_rows} rows")

    # ------------------------------------------------------------------ #
    if args.mode == "knockout":
        by_cell = {}
        for r in rows:
            by_cell.setdefault((r["condition"], r["split"]), []).append(r)
        targets = [c for c in ("DOUBLESPEAK", "NEUTRAL_CODEWORD") ]
        for cond in targets:
            for split in splits:
                for r in sorted(by_cell.get((cond, split), []),
                                key=lambda x: x["sid"])[: args.n_prompts]:
                    templated = dc.apply_template(lm.tokenizer, r["prompt"])
                    pos = pc.resolve_positions(lm, templated, r["probe_word"])
                    q = [pos.codeword_last]
                    base = pc.semantic_score(lm, templated, id_groups)
                    common = {"sid": r["sid"], "condition": cond, "split": split,
                              "demo_style": r["demo_style"], "n_demos": r["n_demos"],
                              "readout": r["readout"]}
                    emit({**common, "source_set": "none", "granularity": "baseline",
                          "layers": None, "heads": None, "n_blocked": 0,
                          "p_concept": base.get("concept"),
                          "p_codeword": base.get("codeword")})
                    for sname in SOURCE_SETS:
                        keys, located = source_positions(
                            lm, templated, r["probe_word"], sname, rng)
                        if not located:
                            n_unlocated += 1
                        if not keys:
                            continue
                        if args.granularity == "all_layers":
                            groups = [("all", list(range(L)), None)]
                        elif args.granularity == "per_layer":
                            groups = [(f"L{l}", [l], None) for l in layers]
                        elif args.granularity == "head_groups":
                            g = args.head_group_size
                            groups = [(f"L{l}_h{h}-{min(h+g, n_heads)-1}", [l],
                                       list(range(h, min(h + g, n_heads))))
                                      for l in layers for h in range(0, n_heads, g)]
                        else:  # per_head
                            groups = [(f"L{l}_h{h}", [l], [h])
                                      for l in layers for h in range(n_heads)]
                        for gname, ells, heads in groups:
                            with pc.AttentionKnockout(lm.model, ells, q, keys, heads):
                                p = pc.semantic_score(lm, templated, id_groups)
                            emit({**common, "source_set": sname,
                                  "granularity": args.granularity, "group": gname,
                                  "layers": ells, "heads": heads,
                                  "n_blocked": len(keys),
                                  "request_boundary_located": located,
                                  "p_concept": p.get("concept"),
                                  "p_codeword": p.get("codeword")})

    # ------------------------------------------------------------------ #
    else:  # component patching: attention output vs MLP output vs residual
        if not args.reps_dir:
            raise SystemExit("--mode component requires --reps-dir")
        rs = json.load(open(os.path.join(args.reps_dir, "reps_summary.json")))
        cube = np.load(os.path.join(args.reps_dir, "subsample.npz"))
        sub, sub_rows = cube["cube"], list(cube["rows"])
        comps, poss = rs["components"], rs["positions"]
        row_meta = {m["row"]: m for m in rs["rows"]}
        sid_to_row = {m["sid"]: m["row"] for m in rs["rows"]}
        pi = poss.index("codeword_last")

        def src(condition, ref, comp):
            sid = f"{condition}|{ref['split']}|{ref['demo_style']}|" \
                  f"{ref['n_demos']}|{ref['readout']}"
            row = sid_to_row.get(sid)
            if row is None or row not in sub_rows:
                return None
            return sub[sub_rows.index(row), comps.index(comp), pi]   # [L, H] fp16

        specs = [("Neutral_from_DS", "NEUTRAL_CODEWORD", "DOUBLESPEAK"),
                 ("DS_from_Neutral", "DOUBLESPEAK", "NEUTRAL_CODEWORD")]
        for aname, tgt, srcc in specs:
            for split in splits:
                cand = sorted([r for r in rows if r["condition"] == tgt
                               and r["split"] == split
                               and sid_to_row.get(r["sid"]) in sub_rows],
                              key=lambda x: x["sid"])[: args.n_prompts]
                for r in cand:
                    templated = dc.apply_template(lm.tokenizer, r["prompt"])
                    pos = pc.resolve_positions(lm, templated, r["probe_word"])
                    p0 = pc.semantic_score(lm, templated, id_groups)
                    common = {"sid": r["sid"], "condition": tgt, "split": split,
                              "demo_style": r["demo_style"], "n_demos": r["n_demos"],
                              "readout": r["readout"], "arm": aname}
                    emit({**common, "component": "none", "layer": None,
                          "p_concept": p0.get("concept"), "p_codeword": p0.get("codeword")})
                    for comp in ("attn_out", "mlp_out", "resid_post"):
                        M = src(srcc, r, comp)
                        if M is None:
                            continue
                        for l in layers:
                            v = torch.from_numpy(M[l].astype(np.float32))
                            if not torch.isfinite(v).all():
                                continue
                            with pc.SubmodulePatch(lm.model, l, comp,
                                                   [pos.codeword_last], v, "replace"):
                                p = pc.semantic_score(lm, templated, id_groups)
                            emit({**common, "component": comp, "layer": l,
                                  "p_concept": p.get("concept"),
                                  "p_codeword": p.get("codeword")})
    raw.close()

    summary = {
        "model": lm.meta(), "pair": pair, "plan": "CAUSAL_CORE_PLAN §6 (S8)",
        "mode": args.mode, "granularity": args.granularity,
        "attn_implementation": attn, "readout": args.readout,
        "demo_styles": sorted(styles) or "all", "splits": splits,
        "layers": layers, "n_layers": L, "n_heads": n_heads,
        "head_group_size": args.head_group_size,
        "n_prompts_per_cell": args.n_prompts, "seed": args.seed,
        "bench": os.path.abspath(args.bench),
        "reps_dir": (os.path.abspath(args.reps_dir) if args.reps_dir else None),
        "source_sets": list(SOURCE_SETS),
        "n_rows": n_rows, "n_request_boundary_unlocated": n_unlocated,
        "status": "COMPLETE",
    }
    with open(os.path.join(out_dir, "attn_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(f"[attn] {n_rows} rows (boundary unlocated: {n_unlocated}) -> {out_dir}")


if __name__ == "__main__":
    main()
