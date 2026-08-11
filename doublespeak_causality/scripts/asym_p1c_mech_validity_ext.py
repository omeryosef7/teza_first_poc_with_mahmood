#!/usr/bin/env python3
"""ASYMMETRY SPRINT — PHASE 1c: extended mechanistic-validity readout (plan §19.1 + §19.2).

Extends `scripts/phase_gate7_mech_validity.py` (which shipped means-only, seed 42, test only,
at one position and two layers) along the four axes the plan asks for, plus a layer sweep:

  §19.1(a) SEEDS         every arm/seed the caller passes (42, 43, 44), not just 42.
  §19.1(b) DISTRIBUTION  PER-PROMPT arrays (not just means) and a `none` (no-suffix)
                         baseline alongside `neutral` and the vanilla-doublespeak suffix.
  §19.1(c) TRAIN->TEST   the SAME quantity on the frozen train pool and on held-out test,
                         so the generalization gap of the suffix's refusal suppression is
                         measurable (--manifest may be given more than once).
  §19.1(d) JOIN KEY      every row carries `task_id`, so a CPU analysis can join per-prompt
                         refusal drop to per-prompt jailbreak success. No text is read here.
  §19.2    LAYER SWEEP   refusal projection across a band of fit layers (default L10..L24),
                         not only the L18 target: broad near-identical suppression across
                         layers => generic (H4); a suffix-specific deepening at its own
                         target layer => partial specificity.

ALSO (this sprint's Phase-0 finding D2): every projection is measured at BOTH
  `decision`    = last token of the templated prompt  (where the axis was fitted/validated)
  `last_suffix` = last suffix token                   (where the GCG objective read it)
so the fit/use position mismatch can be quantified on the real optimized suffixes.

Off-by-one: --refusal-fit-layers / --concept-fit-layers take FIT layers; +1 is applied here
(a direction file L{k} was fitted at hidden_states[k+1]). Both numbers land in meta.json.

SAFETY: reads suffix strings from FINAL_CANDIDATES.jsonl but NEVER writes or prints them;
output is scalars keyed by task_id only.
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402
import torch  # noqa: E402

import ds_common as dc  # noqa: E402


def load_unit(path):
    v = torch.load(path, map_location="cpu", weights_only=True).float().flatten()
    return v / (v.norm() + 1e-8)


def final_suffix(run_dir):
    """First row of FINAL_CANDIDATES.jsonl == the optimizer's best suffix."""
    with open(os.path.join(run_dir, "FINAL_CANDIDATES.jsonl")) as fh:
        return json.loads(fh.readline())["suffix_str"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--manifest", action="append", required=True,
                    help="path[:split] — repeatable. e.g. foo.jsonl:test  bar.jsonl:train")
    ap.add_argument("--arm", action="append", default=[], help="label=run_dir (repeatable)")
    ap.add_argument("--refusal-dir", default=os.path.join(HERE, "outputs/refusal_alllayers"))
    ap.add_argument("--refusal-fit-layers", default=",".join(str(x) for x in range(10, 25)),
                    help="§19.2 layer sweep; FIT layers, +1 applied internally")
    ap.add_argument("--concept-npz",
                    default=os.path.join(HERE, "outputs/unified_directions/clearharm.npz"))
    ap.add_argument("--concept-fit-layers", default="9,16")
    ap.add_argument("--enable-thinking", default="false")
    ap.add_argument("--n-max", type=int, default=0, help="0 = all")
    ap.add_argument("--n-random-suffix", type=int, default=0,
                    help="unoptimized random-token suffixes (the decisive H4 control)")
    ap.add_argument("--n-suffix-tokens", type=int, default=16)
    ap.add_argument("--random-suffix-seed", type=int, default=42)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    t0 = time.time()
    os.makedirs(args.out_dir, exist_ok=True)
    enable_thinking = dc.parse_enable_thinking(args.enable_thinking)

    lm = dc.load_model(args.model)
    dev = next(lm.model.parameters()).device

    # ---- directions, keyed by hidden_states row (fit layer k -> hs[k+1]) ----
    refusal, concept = {}, {}
    for k in [int(x) for x in args.refusal_fit_layers.split(",") if x != ""]:
        p = os.path.join(args.refusal_dir, f"refusal_direction_llama_L{k}.pt")
        if os.path.exists(p):
            refusal[k + 1] = load_unit(p).to(dev)
    assert refusal, "no refusal directions loaded"
    if args.concept_npz and os.path.exists(args.concept_npz):
        cnpz = np.load(args.concept_npz)["concept"]
        for k in [int(x) for x in args.concept_fit_layers.split(",") if x != ""]:
            v = torch.tensor(np.asarray(cnpz[k]), dtype=torch.float32).flatten()
            concept[k + 1] = (v / (v.norm() + 1e-8)).to(dev)
    print(f"[dirs] refusal rows={sorted(refusal)} concept rows={sorted(concept)}", flush=True)

    # ---- suffix conditions ----
    conds = {"none": "", "neutral": " "}
    for a in args.arm:
        label, rd = a.split("=", 1)
        conds[label] = final_suffix(rd)

    # UNOPTIMIZED controls (the decisive H4 test). The optimized "random-direction" arm is
    # still a GCG-optimized suffix; if suppression is generic, a suffix that was never
    # optimized at all should reproduce the same profile. Two flavours:
    #   `init`        the GCG initialization suffix (' !' x n), i.e. optimization step 0
    #   `randtokNNN`  n_suffix uniformly-sampled ordinary vocabulary tokens
    if args.n_suffix_tokens > 0:
        init_ids = lm.tokenizer(" !" * args.n_suffix_tokens,
                                add_special_tokens=False)["input_ids"]
        conds["init"] = lm.tokenizer.decode(init_ids)
        if args.n_random_suffix > 0:
            rng = np.random.default_rng(args.random_suffix_seed)
            special = set(int(x) for x in (lm.tokenizer.all_special_ids or []))
            pool = []
            for tid in range(int(lm.tokenizer.vocab_size)):
                if tid in special:
                    continue
                s = lm.tokenizer.convert_ids_to_tokens(tid)
                if not s:
                    continue
                t = s.replace("Ġ", " ").replace("Ċ", "\n")
                if not t.strip():
                    continue
                try:
                    t.encode("ascii")
                except UnicodeEncodeError:
                    continue
                pool.append(tid)
            for i in range(args.n_random_suffix):
                ids = rng.choice(pool, size=args.n_suffix_tokens, replace=False)
                conds[f"randtok{i:03d}"] = lm.tokenizer.decode([int(x) for x in ids])
    print(f"[conds] n={len(conds)}: "
          f"{[c for c in conds if not c.startswith('randtok')]} + "
          f"{sum(c.startswith('randtok') for c in conds)} randtok", flush=True)

    keys = [("refusal", r) for r in sorted(refusal)] + [("concept", r) for r in sorted(concept)]

    # Number of template tokens the chat template appends AFTER the user content
    # (`<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n`). Measured from the live
    # tokenizer, never hardcoded: render two prompts whose user content differs only in its
    # tail and walk backwards while the token ids agree.
    _ia = lm.tokenizer(dc.apply_template(lm.tokenizer, "X", add_generation_prompt=True,
                                         enable_thinking=enable_thinking),
                       return_tensors="pt")["input_ids"][0].tolist()
    _ib = lm.tokenizer(dc.apply_template(lm.tokenizer, "X Y Y Y", add_generation_prompt=True,
                                         enable_thinking=enable_thinking),
                       return_tensors="pt")["input_ids"][0].tolist()
    TAIL = 0
    while TAIL < min(len(_ia), len(_ib)) and _ia[-1 - TAIL] == _ib[-1 - TAIL]:
        TAIL += 1
    assert 1 <= TAIL < 16, f"template tail detection produced implausible TAIL={TAIL}"
    print(f"[template] {TAIL} template tokens follow the user content "
          f"-> last user/suffix token is at index len-1-{TAIL}", flush=True)

    @torch.no_grad()
    def project(instruction, suffix):
        """-> {(pos_name, kind, hs_row): float}. Both positions, one forward."""
        text = dc.apply_template(lm.tokenizer, instruction + suffix,
                                 add_generation_prompt=True, enable_thinking=enable_thinking)
        hs = dc.forward_hidden_states(lm, text)["hidden_states"]
        n_tok = hs[0].shape[1]
        pos = {"decision": n_tok - 1}
        if suffix:                      # last suffix token == last user-content token
            pos["last_suffix"] = n_tok - 1 - TAIL
        out = {}
        for kind, row in keys:
            d = refusal[row] if kind == "refusal" else concept[row]
            for pname, p in pos.items():
                out[(pname, kind, row)] = float(torch.dot(hs[row][0, p, :].float(), d))
        return out

    rows = []
    for spec in args.manifest:
        path, _, split = spec.partition(":")
        items = [json.loads(l) for l in open(path)]
        if split:
            items = [it for it in items if it.get("split") == split]
        seen, uniq = set(), []
        for it in items:
            if it["task_id"] in seen:
                continue
            seen.add(it["task_id"])
            uniq.append(it)
        if args.n_max:
            uniq = uniq[: args.n_max]
        assert len(uniq) >= 20, f"plan §3.4 needs >=20 unique items, got {len(uniq)} for {spec}"
        pool = split or os.path.basename(path)
        print(f"[data] {spec} -> n={len(uniq)}", flush=True)
        for i, it in enumerate(uniq):
            for cname, suf in conds.items():
                pr = project(it["instruction"], suf)
                for (pname, kind, row), val in pr.items():
                    rows.append({"pool": pool, "task_id": it["task_id"], "cond": cname,
                                 "pos": pname, "kind": kind, "hs_row": row,
                                 "fit_layer": row - 1, "proj": val})
            if (i + 1) % 10 == 0:
                print(f"  [{pool}] {i+1}/{len(uniq)} ({time.time()-t0:.0f}s)", flush=True)

    with open(os.path.join(args.out_dir, "projections.jsonl"), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    meta = {"phase": "P1c_mech_validity_ext", "model": args.model,
            "manifests": args.manifest, "arms": args.arm,
            "conditions": list(conds), "n_rows": len(rows),
            "n_random_suffix": args.n_random_suffix,
            "n_suffix_tokens": args.n_suffix_tokens,
            "random_suffix_seed": args.random_suffix_seed,
            "refusal_fit_layers": sorted(r - 1 for r in refusal),
            "concept_fit_layers": sorted(r - 1 for r in concept),
            "hidden_states_rows_refusal": sorted(refusal),
            "hidden_states_rows_concept": sorted(concept),
            "off_by_one_note": "direction L{k} fitted at hidden_states[k+1]; +1 applied here",
            "template_tail_tokens_after_user_content": TAIL,
            "positions": {"decision": "last token of templated prompt (fit/readout position)",
                          "last_suffix": "last suffix token (position the GCG objective read)"},
            "elapsed_s": time.time() - t0}
    meta.update(lm.meta())
    json.dump(meta, open(os.path.join(args.out_dir, "meta.json"), "w"), indent=2)
    dc.write_runmeta(args.out_dir, args=args, extra=meta)
    dc.write_done(args.out_dir, rows_written=len(rows))
    print(f"[out] {args.out_dir} rows={len(rows)} {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
