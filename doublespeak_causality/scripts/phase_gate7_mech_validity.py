#!/usr/bin/env python3
"""Gate-7 §17 MECHANISTIC-VALIDITY check (NEXT sprint Q5).

For each optimized suffix, does the optimizer actually MOVE its intended internal target on
HELD-OUT prompts — and does the mechanism suffix move it MORE than the matched random suffix?

Measures, on v3 test doublespeak prompts, the projection of the last-token (decision) hidden
state onto the refusal / concept unit directions (at the fitted hidden_states[k+1] rows), for
each suffix condition. Compares:
  - refusal-optimized suffix vs refusal-random suffix vs neutral: does refusal projection DROP more?
  - concept-optimized suffix vs concept-random suffix vs neutral: does concept projection RISE more?

Matches the eval's suffix placement exactly: user_content = instruction + suffix_str, then chat
template (user turn). Reads suffix strings from each arm's FINAL_CANDIDATES.jsonl (row[0].suffix_str);
never prints suffix or prompt text. Scalar JSON output only.

Usage:
  python scripts/phase_gate7_mech_validity.py \
     --manifest data/gcg/clearharm_llama_v3/clearharm_llama_doublespeak.jsonl --split test \
     --arm refusal_L18=outputs/stage_gcg_full/phase9b_v3_arm07_refusal_down_L18_seed42 \
     --arm refusal_rand_L18=outputs/stage_gcg_full/phase9b_v3_arm07r_refusal_rand_L18_seed42 \
     --out reports/GATE7_V3_MECH_VALIDITY_seed42.json
"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import ds_common as dc  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402


def load_unit(path):
    v = torch.load(path, map_location="cpu", weights_only=True).float().flatten()
    return v / (v.norm() + 1e-8)


def final_suffix(run_dir):
    f = os.path.join(run_dir, "FINAL_CANDIDATES.jsonl")
    with open(f) as fh:
        row = json.loads(fh.readline())
    return row["suffix_str"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--arm", action="append", default=[], help="label=run_dir (repeatable)")
    ap.add_argument("--refusal-dir", default=os.path.join(HERE, "outputs/refusal_alllayers"))
    ap.add_argument("--concept-npz", default=os.path.join(HERE, "outputs/unified_directions/clearharm.npz"))
    ap.add_argument("--refusal-fit-layers", default="12,18,22")
    ap.add_argument("--concept-fit-layers", default="9,16")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    lm = dc.load_model(args.model); dev = lm.model.device

    # directions keyed by the hidden_states row (fit-layer k -> hs[k+1])
    refusal = {}
    for k in [int(x) for x in args.refusal_fit_layers.split(",")]:
        p = os.path.join(args.refusal_dir, f"refusal_direction_llama_L{k}.pt")
        if os.path.exists(p):
            refusal[k + 1] = load_unit(p).to(dev)
    concept = {}
    cnpz = np.load(args.concept_npz)["concept"]
    for k in [int(x) for x in args.concept_fit_layers.split(",")]:
        v = torch.tensor(cnpz[k], dtype=torch.float32)
        concept[k + 1] = (v / (v.norm() + 1e-8)).to(dev)

    # suffix conditions
    conds = {"none": "", "neutral": " "}
    for a in args.arm:
        label, rd = a.split("=", 1)
        conds[label] = final_suffix(rd)

    # manifest is JSONL
    items = [json.loads(l) for l in open(args.manifest)]
    items = [it for it in items if it.get("split") == args.split]

    @torch.no_grad()
    def proj_last(instruction, suffix):
        user_content = instruction + suffix
        text = dc.apply_template(lm.tokenizer, user_content, add_generation_prompt=True)
        fwd = dc.forward_hidden_states(lm, text)
        hs = fwd["hidden_states"]  # tuple[L+1] [1,seq,H]
        out = {}
        for row, d in refusal.items():
            h = hs[row][0, -1, :].float()
            out[f"refusal_hs{row}"] = float(torch.dot(h, d))
        for row, d in concept.items():
            h = hs[row][0, -1, :].float()
            out[f"concept_hs{row}"] = float(torch.dot(h, d))
        return out

    # accumulate per condition
    keys = [f"refusal_hs{r}" for r in refusal] + [f"concept_hs{r}" for r in concept]
    agg = {c: {k: [] for k in keys} for c in conds}
    for it in items:
        instr = it["instruction"]
        for c, suf in conds.items():
            pr = proj_last(instr, suf)
            for k in keys:
                agg[c][k].append(pr[k])

    result = {"model": args.model, "split": args.split, "n_items": len(items),
              "conditions": list(conds.keys()), "means": {}, "deltas_vs_neutral": {}}
    for c in conds:
        result["means"][c] = {k: float(np.mean(agg[c][k])) for k in keys}
    for c in conds:
        if c == "neutral":
            continue
        result["deltas_vs_neutral"][c] = {
            k: float(np.mean(np.array(agg[c][k]) - np.array(agg["neutral"][k]))) for k in keys}

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(result, open(args.out, "w"), indent=2)
    print(f"[mech] n_items={len(items)} conditions={list(conds.keys())}")
    for c in conds:
        print(f"  {c:20s} " + " ".join(f"{k}={result['means'][c][k]:+.3f}" for k in keys))
    print(f"[out] {args.out}")


if __name__ == "__main__":
    main()
