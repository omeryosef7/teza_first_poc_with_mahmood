"""
31_validate_readouts.py — CAUSAL_CORE_PLAN §16.4 (the S2 GATE).

Validate every SAFE semantic readout of the fixed-pair benchmark BEFORE any
intervention result is interpreted. A readout is only usable if it separates the
positive control (DIRECT_CONCEPT: the word genuinely means the concept) from the
negative control (NEUTRAL_CODEWORD: the word genuinely means itself).

Two scalar modalities per prompt, obtained from ONE greedy generation:
  * next-token probability of the concept vs the codeword (readout scores[0]);
  * the generated one-word answer, mapped to a meaning lexicon.

Nothing operationally harmful is ever requested: the answer is a meaning LABEL.
Per plan §15 stdout carries ids/labels/scalars only.

Reuse: ds_common (load/template/positions), stats.paired_bootstrap_ci, and the
house output-dir convention (<prefix>_<ModelTag>_<ts>_<jobid>).

Usage:
  python 31_validate_readouts.py --bench data/pair_benchmark/pair_carrot_bomb.json \
      --model meta-llama/Llama-3.1-8B-Instruct --out-root outputs
"""
import os
import re
import sys
import json
import time
import argparse

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds_common as dc
import stats as st

HERE = os.path.dirname(os.path.abspath(__file__))

# Readout-pass thresholds for the S2 gate (plan §16.4).
POS_CONTROL_MIN = 0.80   # DIRECT_CONCEPT must be read as the concept at least this often
NEG_CONTROL_MAX = 0.20   # NEUTRAL_CODEWORD must be read as the concept at most this often


# --------------------------------------------------------------------------- #
# Token / answer helpers
# --------------------------------------------------------------------------- #
def word_first_ids(tokenizer, word):
    """First-token ids for every surface form the model might emit for `word`.

    The assistant turn may start the answer with or without a leading space and
    with or without capitalisation, so scoring a single id undercounts the mass.
    """
    ids = set()
    for surface in (f" {word}", word, f" {word.capitalize()}", word.capitalize()):
        enc = tokenizer.encode(surface, add_special_tokens=False)
        if enc:
            ids.add(int(enc[0]))
    return sorted(ids)


def normalize_answer(text):
    """Lowercase, strip punctuation/markup, keep the first few words."""
    t = re.sub(r"[^a-zA-Z\s]", " ", text or "").lower()
    return [w for w in t.split() if w][:4]


def classify_answer(text, lexicons):
    """Map a one-word answer to a lexicon key, or OTHER/EMPTY."""
    words = normalize_answer(text)
    if not words:
        return "EMPTY"
    for w in words:
        for key, vocab in lexicons.items():
            if w in vocab:
                return key
    return "OTHER"


@torch.no_grad()
def generate_with_first_scores(lm, templated_text, max_new_tokens, id_groups):
    """Greedy-generate and return the completion plus first-token probability mass.

    id_groups: {name: [token_id, ...]}. Returns p[name] = summed softmax mass of that
    group at the FIRST generated position (the next-token-probability readout).
    """
    tok = lm.tokenizer(templated_text, return_tensors="pt",
                       add_special_tokens=False).to(lm.model.device)
    in_len = tok["input_ids"].shape[1]
    out = lm.model.generate(
        **tok, max_new_tokens=max_new_tokens, do_sample=False,
        eos_token_id=lm.eos_token_ids, pad_token_id=lm.tokenizer.pad_token_id,
        return_dict_in_generate=True, output_scores=True,
    )
    probs = torch.softmax(out.scores[0][0].float(), dim=-1)
    p = {name: float(probs[ids].sum()) for name, ids in id_groups.items()}
    gen_ids = out.sequences[0][in_len:]
    completion = lm.tokenizer.decode(gen_ids, skip_special_tokens=True)
    return completion, p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(HERE, "outputs"))
    ap.add_argument("--max-new-tokens", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None,
                    help="smoke cap on rows, STRATIFIED over (condition, readout) so a "
                         "capped run still exercises both gate controls")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--enable-thinking", default=None,
                    choices=[None, "true", "false"], help="Qwen3-style thinking toggle")
    args = ap.parse_args()

    dc.set_seed(args.seed)
    bench = json.load(open(args.bench))
    pair, lexicons = bench["pair"], bench["lexicons"]
    rows_in = bench["semantic"]
    if args.limit:
        # round-robin over (condition, readout) cells: a capped smoke run must still
        # contain BOTH the positive and the negative control, or the gate is vacuous.
        cells = {}
        for r in rows_in:
            cells.setdefault((r["condition"], r["readout"]), []).append(r)
        order = sorted(cells)
        picked, k = [], 0
        while len(picked) < args.limit and any(len(cells[c]) > k for c in order):
            for c in order:
                if k < len(cells[c]) and len(picked) < args.limit:
                    picked.append(cells[c][k])
            k += 1
        rows_in = picked

    think = None if args.enable_thinking is None else (args.enable_thinking == "true")

    lm = dc.load_model(args.model)
    tag = args.model.split("/")[-1]
    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    ts = time.strftime("%Y%m%d_%H%M%S") + "_" + uniq
    out_dir = os.path.join(args.out_root, f"pair_readout_{tag}_{ts}")
    os.makedirs(out_dir, exist_ok=True)
    print(f"[readout] model={tag} layers={lm.num_layers} rows={len(rows_in)} -> {out_dir}")

    # Probability groups: the concept, the codeword, and both control sources.
    id_groups = {}
    for role in ("concept", "codeword", "benign_source", "unrelated_source"):
        w = pair.get(role)
        if w:
            id_groups[role] = word_first_ids(lm.tokenizer, w)
    # Single-token sanity (plan gotcha: multi-token words make the mass misleading).
    single_tok = {r: len(lm.tokenizer.encode(" " + pair[r], add_special_tokens=False)) == 1
                  for r in ("concept", "codeword") if pair.get(r)}

    raw_path = os.path.join(out_dir, "readout_raw.jsonl")
    n_done = 0
    with open(raw_path, "w") as fh:
        for r in rows_in:
            templated = dc.apply_template(lm.tokenizer, r["prompt"], enable_thinking=think)
            completion, p = generate_with_first_scores(
                lm, templated, args.max_new_tokens, id_groups)
            label = classify_answer(completion, lexicons)
            rec = {
                "sid": r["sid"], "condition": r["condition"], "split": r["split"],
                "demo_style": r["demo_style"], "n_demos": r["n_demos"],
                "readout": r["readout"], "probe_word": r["probe_word"],
                "expected_lexicon": r["expected_lexicon"],
                "p": p, "answer_label": label, "answer": completion.strip()[:64],
                # convenience scalars used by the gate + all downstream analyses
                "p_concept": p.get("concept"), "p_codeword": p.get("codeword"),
                "reads_as_concept": int(label == pair["concept"]),
                "reads_as_codeword": int(label == pair["codeword"]),
                "reads_as_expected": int(label == r["expected_lexicon"]),
            }
            fh.write(json.dumps(rec) + "\n")
            n_done += 1
            if n_done % 100 == 0:
                print(f"  [readout] {n_done}/{len(rows_in)}")

    rows = [json.loads(l) for l in open(raw_path)]

    # ---- aggregate + gate ----
    def agg(sel):
        s = [r for r in rows if sel(r)]
        if not s:
            return None
        n = len(s)
        return {
            "n": n,
            "reads_as_concept": round(sum(r["reads_as_concept"] for r in s) / n, 4),
            "reads_as_codeword": round(sum(r["reads_as_codeword"] for r in s) / n, 4),
            "reads_as_expected": round(sum(r["reads_as_expected"] for r in s) / n, 4),
            "p_concept": round(sum(r["p_concept"] for r in s) / n, 5),
            "p_codeword": round(sum(r["p_codeword"] for r in s) / n, 5),
        }

    readouts = sorted({r["readout"] for r in rows})
    conditions = sorted({r["condition"] for r in rows})
    by_readout, gate = {}, {}
    for ro in readouts:
        per_cond = {c: agg(lambda r, c=c, ro=ro: r["readout"] == ro and r["condition"] == c)
                    for c in conditions}
        by_readout[ro] = per_cond
        pos = per_cond.get("DIRECT_CONCEPT") or {}
        neg = per_cond.get("NEUTRAL_CODEWORD") or {}
        # label-based gate, with the probability-mass margin reported alongside
        pos_v, neg_v = pos.get("reads_as_concept"), neg.get("reads_as_concept")
        gate[ro] = {
            "positive_control_reads_as_concept": pos_v,
            "negative_control_reads_as_concept": neg_v,
            "positive_control_p_concept": pos.get("p_concept"),
            "negative_control_p_concept": neg.get("p_concept"),
            "pass": bool(pos_v is not None and neg_v is not None
                         and pos_v >= POS_CONTROL_MIN and neg_v <= NEG_CONTROL_MAX),
        }

    # ---- paired DS-vs-Neutral contrast (matched on split/style/n_demos/readout) ----
    def key(r):
        return (r["split"], r["demo_style"], r["n_demos"], r["readout"])
    ds = {key(r): r for r in rows if r["condition"] == "DOUBLESPEAK"}
    nu = {key(r): r for r in rows if r["condition"] == "NEUTRAL_CODEWORD"}
    shared = sorted(set(ds) & set(nu), key=lambda t: tuple(str(v) for v in t))
    contrasts = {}
    if shared:
        for metric in ("reads_as_concept", "p_concept"):
            x = [ds[k][metric] for k in shared]
            y = [nu[k][metric] for k in shared]
            ci = st.paired_bootstrap_ci(x, y, n_boot=10000, seed=0)
            contrasts[f"DS_minus_Neutral_{metric}"] = {
                "mean": round(ci["mean_diff"], 4), "lo": round(ci["lo"], 4),
                "hi": round(ci["hi"], 4), "n": ci["n"],
                "ci_reliable": ci["ci_reliable"], "degenerate": ci["degenerate"]}

    summary = {
        "model": lm.meta(), "pair": pair, "bench": os.path.abspath(args.bench),
        "bench_meta": bench["_meta"],
        "plan": "CAUSAL_CORE_PLAN §16.4 (S2 gate)",
        "thresholds": {"POS_CONTROL_MIN": POS_CONTROL_MIN,
                       "NEG_CONTROL_MAX": NEG_CONTROL_MAX},
        "single_token": single_tok,
        "n_rows": len(rows), "by_readout": by_readout,
        "gate": gate,
        "gate_pass_any": any(g["pass"] for g in gate.values()),
        "gate_pass_readouts": [ro for ro, g in gate.items() if g["pass"]],
        "contrasts": contrasts,
        "status": "COMPLETE",
    }
    with open(os.path.join(out_dir, "readout_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    print("[readout] GATE (positive DIRECT_CONCEPT / negative NEUTRAL_CODEWORD, "
          "'reads as concept'):")
    for ro in readouts:
        g = gate[ro]
        print(f"  {ro:18} pos={g['positive_control_reads_as_concept']} "
              f"neg={g['negative_control_reads_as_concept']} "
              f"-> {'PASS' if g['pass'] else 'FAIL'}")
    print(f"[readout] passing readouts: {summary['gate_pass_readouts']}")
    print(f"[readout] -> {out_dir}")


if __name__ == "__main__":
    main()
