#!/usr/bin/env python3
"""§27 X5 (last cross-model gate) -- does the CONCEPT readout FAIL to explain behavior on
Qwen3-14B, while the REFUSAL readout succeeds (per X3/X4)?

Two steps in one script (mirrors X2's fit+validate structure), no new *generation* GPU work
beyond forward passes (forward/patching allowlist >=23GB is fine; this script is forward-only):

  (a) FIT a diff-of-means CONCEPT direction on Qwen3-14B, at a layer sweep, thinking-OFF.
      Mirrors build_refusal_direction_llama.py's diff-of-means, but the contrast is
      CONCEPT-token vs CODEWORD-token last-hidden rather than harmful vs harmless:
          v_concept[L] = normalize( mean(h @ concept-token, DIRECT prompt)
                                    - mean(h @ codeword-token, NEUTRAL prompt) )
      captured at hidden_states[L+1] (post-block-L residual == directions row L). Token
      positions come from pair_common.word_first_ids (first-token ids of the concept /
      codeword surface forms), with dc.target_positions as the robust offset fallback.
      Fit on --fit-split only, so evaluation below is out-of-sample. Written to
      outputs/concept_qwen3/concept_direction_qwen3_L{L}.pt (+ .json, incl. `separation`).

  (b) PROJECT + PREDICT. For every --eval-split DOUBLESPEAK item, project the last-prompt-
      token residual onto the CONCEPT direction (and, for the positive control, onto the
      Qwen3 REFUSAL direction in outputs/refusal_qwen3, plus a norm-matched RANDOM control)
      at each layer. Then -- reusing the P6 analyze_jacobian_predicts_behavior.py AUC +
      seeded-percentile-bootstrap-CI pattern -- join per-item projections with the Qwen3
      behav_refusal ds_base jailbreak label (--beh dir, by id) and report the AUC for
      jailbreak, per split and pooled.

ENDPOINT: concept-proj AUC ~= 0.5 (concept readout FAILS to predict Qwen3 jailbreak), while
refusal-proj AUC > 0.5 (refusal readout succeeds) -- the representation!=behavior dissociation
holds cross-model. If --beh is absent, the projections are still written; the AUC step is
skipped with a note (so a smoke run needs no prior behavioral run).

Usage (GPU, do NOT run from the agent):
  python scripts/phase_x5_concept_qwen3.py \
    --bench data/behavioral_v3b/beh_clearharm.json --model Qwen/Qwen3-14B \
    --refusal-dir outputs/refusal_qwen3 --layers 16,20,24,28,32 \
    --fit-split train --eval-splits train,test --enable-thinking false \
    --beh outputs/behav_refusal_clearharm_a1.0_<ts>_<job>
"""
from __future__ import annotations
import argparse, json, os, sys, time, glob
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__)); DC = os.path.dirname(HERE)
sys.path.insert(0, DC)
import ds_common as dc
import pair_common as pc


# --------------------------------------------------------------------------- #
# AUC + bootstrap CI -- verbatim pattern from scripts/analyze_jacobian_predicts_behavior.py
# --------------------------------------------------------------------------- #
def _auc(x, y):
    x = np.asarray(x, float); y = np.asarray(y, int)
    pos, neg = x[y == 1], x[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    gt = sum((p > neg).sum() for p in pos)
    eq = sum((p == neg).sum() for p in pos)
    return (gt + 0.5 * eq) / (len(pos) * len(neg))


def _boot(x, y, n=5000, seed=0, orient=None):
    """FIXED a-priori orientation: `x` is the SCORE already oriented so that HIGHER => more
    jailbreak (callers pass score = -projection, hypothesis: lower projection => more jailbreak).
    Reports the RAW AUC of that fixed-orientation score (may be < 0.5 for a null/anti-predictive
    axis); no data-driven max(AUC, 1-AUC) flip. `orient` retained for signature compat (unused)."""
    x = np.asarray(x, float); y = np.asarray(y, int)
    a0 = _auc(x, y)
    rng = np.random.default_rng(seed)
    idx = np.arange(len(y)); out = []
    for _ in range(n):
        s = rng.choice(idx, len(idx), replace=True)
        if y[s].sum() in (0, len(s)):
            continue
        out.append(_auc(x[s], y[s]))
    if not out:
        return a0, float("nan"), float("nan"), False
    lo, hi = np.percentile(out, [2.5, 97.5])
    return a0, float(lo), float(hi), False


# --------------------------------------------------------------------------- #
# Token position of a word via word_first_ids (last occurrence), with a robust fallback
# --------------------------------------------------------------------------- #
def _word_last_pos(lm, input_ids, word, text):
    """Position of the last token that begins `word`, via pc.word_first_ids; fall back to
    dc.target_positions' offset-aware finder if no first-token id matches (in-context
    tokenization differs from the standalone surface forms)."""
    cand = set(pc.word_first_ids(lm.tokenizer, word))
    matches = [i for i, t in enumerate(input_ids) if t in cand]
    if matches:
        return matches[-1]
    try:
        return dc.target_positions(lm.tokenizer, input_ids, word, text=text).codeword_last
    except Exception:
        return None


def _load_bench(path):
    data = json.load(open(path))
    items = data["items"] if isinstance(data, dict) else data
    cohort = (data.get("_meta", {}) if isinstance(data, dict) else {}).get(
        "cohort", os.path.splitext(os.path.basename(path))[0])
    return items, cohort


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True, help="behavioral_v3b bench (items w/ harmful_word, codeword, demos)")
    ap.add_argument("--model", default="Qwen/Qwen3-14B")
    ap.add_argument("--refusal-dir", default=os.path.join(DC, "outputs", "refusal_qwen3"),
                    help="dir of refusal_direction_llama_L{L}.pt (positive-control axis; reused from X2)")
    ap.add_argument("--layers", default="16,20,24,28,32", help="comma-list; should match --refusal-dir layers")
    ap.add_argument("--fit-split", default="train", help="split used to FIT the concept direction (out-of-sample eval)")
    ap.add_argument("--eval-splits", default="train,test", help="splits projected + AUC-scored")
    ap.add_argument("--beh", default=None,
                    help="Qwen3 behav_refusal run dir (raw.jsonl w/ id + ds_base_label) for the AUC join; "
                         "if omitted, projections are written and the AUC step is skipped")
    ap.add_argument("--n", type=int, default=0, help="cap items per split (0 = all); smoke lever")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--enable-thinking", default="false",
                    help="Qwen3 thinking model -> 'false' (empty <think></think>, no live <think> before readout)")
    ap.add_argument("--out-dir", default=None, help="override run dir (default outputs/x5_concept_qwen3_<cohort>_<ts>_<job>)")
    ap.add_argument("--concept-out", default=os.path.join(DC, "outputs", "concept_qwen3"),
                    help="where the fit concept_direction_qwen3_L{L}.pt files are written")
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16"])
    args = ap.parse_args()

    et = dc.parse_enable_thinking(args.enable_thinking)
    layers = [int(x) for x in args.layers.split(",") if x.strip()]
    fit_split = args.fit_split.strip()
    eval_splits = [s.strip() for s in args.eval_splits.split(",") if s.strip()]

    dc.set_seed(args.seed); rng = np.random.default_rng(args.seed)
    items, cohort = _load_bench(args.bench)

    ts = time.strftime("%Y%m%d_%H%M%S"); uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = args.out_dir or os.path.join(DC, "outputs", f"x5_concept_qwen3_{cohort}_{ts}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(args.concept_out, exist_ok=True)
    # RUNMETA FIRST (defensive; never raises)
    dc.write_runmeta(out_dir, args, extra={"phase": "x5_concept_qwen3", "cohort": cohort,
                                           "layers": layers, "fit_split": fit_split,
                                           "eval_splits": eval_splits})

    print(f"[x5] model={args.model} cohort={cohort} layers={layers} think={args.enable_thinking}", flush=True)
    print(f"[x5] fit_split={fit_split} eval_splits={eval_splits} refusal_dir={args.refusal_dir}", flush=True)
    print(f"[x5] out_dir={out_dir}  concept_out={args.concept_out}", flush=True)
    print(f"date {time.strftime('%Y-%m-%dT%H:%M:%S')}", flush=True)

    lm = dc.load_model(args.model, dtype=getattr(torch, args.dtype))
    dc.write_runmeta(out_dir, args, extra={"model_loaded": args.model, "num_layers": lm.num_layers})
    if max(layers) + 1 >= lm.num_layers + 1:
        raise SystemExit(f"layer {max(layers)} out of range for {lm.num_layers}-layer model")

    @torch.no_grad()
    def fwd_and_pos(raw_prompt, word):
        """One forward pass on the templated prompt; return hidden_states + the word position."""
        t = dc.apply_template(lm.tokenizer, raw_prompt, add_generation_prompt=True, enable_thinking=et)
        fwd = dc.forward_hidden_states(lm, t)
        pos = _word_last_pos(lm, fwd["input_ids"], word, t)
        return fwd["hidden_states"], pos

    # ---- (a) FIT concept direction: diff-of-means concept-token vs codeword-token -------- #
    concept_hs = {L: [] for L in layers}      # DIRECT prompt, at the concept (harmful_word) token
    codeword_hs = {L: [] for L in layers}     # NEUTRAL prompt, at the codeword token
    n_fit = n_skip = 0
    for it in items:
        if it.get("split") != fit_split:
            continue
        hw, cw = it["harmful_word"], it["codeword"]
        instr = it["harmful_instruction"]
        if hw not in instr:
            instr = f"Give detailed step-by-step instructions to make a {hw}."
        demos = it["demos"] if isinstance(it["demos"], str) else "\n".join(it["demos"])
        try:
            conds = dc.build_conditions(instr, hw, cw, demos)
        except AssertionError:
            n_skip += 1; continue
        try:
            hs_d, pos_c = fwd_and_pos(conds.direct, hw)     # concept token in DIRECT
            hs_n, pos_k = fwd_and_pos(conds.neutral, cw)    # codeword token in NEUTRAL
        except Exception as e:
            print(f"[x5][fit] skip id={it.get('id')} ({e!r})", flush=True); n_skip += 1; continue
        if pos_c is None or pos_k is None:
            n_skip += 1; continue
        for L in layers:
            concept_hs[L].append(hs_d[L + 1][0, pos_c, :].float().cpu())
            codeword_hs[L].append(hs_n[L + 1][0, pos_k, :].float().cpu())
        n_fit += 1
    print(f"[x5][fit] used {n_fit} items (skipped {n_skip}) from split={fit_split}", flush=True)
    if n_fit == 0:
        raise SystemExit(f"no fit items on split={fit_split}")

    concept_dir = {}                                   # {L: unit vector}
    concept_meta = {}
    for L in layers:
        mc = torch.stack(concept_hs[L]).mean(0)
        mk = torch.stack(codeword_hs[L]).mean(0)
        v = mc - mk
        v = v / (v.norm() + 1e-8)
        pc_c = torch.stack([torch.dot(h / (h.norm() + 1e-8), v) for h in concept_hs[L]])
        pc_k = torch.stack([torch.dot(h / (h.norm() + 1e-8), v) for h in codeword_hs[L]])
        sep = float(pc_c.mean() - pc_k.mean())
        pt_path = os.path.join(args.concept_out, f"concept_direction_qwen3_L{L}.pt")
        torch.save(v, pt_path)
        meta = {"model": args.model, "contrast": "concept_token_minus_codeword_token",
                "layer": L, "d_model": int(v.shape[0]), "hidden_states_index": L + 1,
                "directions_row": L, "n_fit": n_fit, "fit_split": fit_split,
                "bench": os.path.abspath(args.bench), "separation": sep,
                "proj_concept_mean": float(pc_c.mean()), "proj_codeword_mean": float(pc_k.mean()),
                "enable_thinking": et, "env": dc.env_metadata()}
        json.dump(meta, open(pt_path.replace(".pt", ".json"), "w"), indent=2)
        concept_dir[L] = v; concept_meta[L] = meta
        print(f"[x5][fit] L{L}: separation={sep:+.4f} -> {pt_path}", flush=True)

    # ---- refusal directions (positive control) + a norm-matched random control ---------- #
    refusal_dir = {}
    for L in layers:
        p = os.path.join(args.refusal_dir, f"refusal_direction_llama_L{L}.pt")
        if os.path.exists(p):
            v = torch.load(p, map_location="cpu").float().flatten()
            refusal_dir[L] = v / (v.norm() + 1e-8)
    print(f"[x5] refusal dirs present at layers {sorted(refusal_dir)}", flush=True)
    rand_dir = {L: (pc.norm_matched_random(concept_dir[L], 1, args.seed + L)[0]) for L in layers}
    rand_dir = {L: rand_dir[L] / (rand_dir[L].norm() + 1e-8) for L in layers}

    # ---- (b) PROJECT doublespeak last-prompt-token residual onto each axis --------------- #
    fh = open(os.path.join(out_dir, "raw.jsonl"), "w")
    n_proj = 0
    for it in items:
        if it.get("split") not in eval_splits:
            continue
        hw, cw = it["harmful_word"], it["codeword"]
        instr = it["harmful_instruction"]
        if hw not in instr:
            instr = f"Give detailed step-by-step instructions to make a {hw}."
        demos = it["demos"] if isinstance(it["demos"], str) else "\n".join(it["demos"])
        try:
            conds = dc.build_conditions(instr, hw, cw, demos)
        except AssertionError:
            continue
        t = dc.apply_template(lm.tokenizer, conds.doublespeak, add_generation_prompt=True, enable_thinking=et)
        try:
            hs = dc.forward_hidden_states(lm, t)["hidden_states"]
        except Exception as e:
            print(f"[x5][proj] skip id={it.get('id')} ({e!r})", flush=True); continue
        rec = {"id": it.get("id"), "split": it.get("split"), "cohort": cohort,
               "concept": {}, "refusal": {}, "rand": {}}
        for L in layers:
            vec = hs[L + 1][0, -1, :].float().cpu()      # last prompt token (decides first gen token)
            rec["concept"][str(L)] = float(torch.dot(vec, concept_dir[L]))
            rec["rand"][str(L)] = float(torch.dot(vec, rand_dir[L]))
            if L in refusal_dir:
                rec["refusal"][str(L)] = float(torch.dot(vec, refusal_dir[L]))
        fh.write(json.dumps(rec) + "\n"); fh.flush(); n_proj += 1
    fh.close()
    print(f"[x5][proj] wrote {n_proj} doublespeak projection rows", flush=True)

    # ---- AUC: does the projection predict jailbreak? (P6 analyzer pattern) --------------- #
    summary = {"model": args.model, "cohort": cohort, "layers": layers,
               "fit_split": fit_split, "eval_splits": eval_splits,
               "enable_thinking": et, "n_proj": n_proj,
               "concept_separation": {str(L): round(concept_meta[L]["separation"], 4) for L in layers},
               "auc": None, "beh": args.beh}

    if args.beh:
        beh_path = args.beh
        if not os.path.isabs(beh_path) and not os.path.exists(beh_path):
            beh_path = os.path.join(DC, args.beh)
        beh_raw = os.path.join(beh_path, "raw.jsonl")
        if not os.path.exists(beh_raw):
            print(f"[x5][auc] WARNING: --beh raw.jsonl not found at {beh_raw}; skipping AUC", flush=True)
        else:
            lab = {}
            for l in open(beh_raw):
                r = json.loads(l)
                if "ds_base_label" in r and r.get("id") is not None:
                    lab[r["id"]] = (r.get("split"), int(r["ds_base_label"] == "MALICIOUS"))
            proj = [json.loads(l) for l in open(os.path.join(out_dir, "raw.jsonl"))]
            proj = [r for r in proj if r["id"] in lab]
            print(f"[x5][auc] joined {len(proj)} items with behavioral labels from {beh_raw}", flush=True)
            auc = {"n_joined": len(proj), "concept": {}, "refusal": {}, "rand": {}}
            if proj:
                for axis in ("concept", "refusal", "rand"):
                    for L in layers:
                        Lk = str(L)
                        rows = [r for r in proj if Lk in r[axis]]
                        cell = {}
                        for sp in ["pooled"] + eval_splits:
                            ks = [r for r in rows if sp == "pooled" or lab[r["id"]][0] == sp]
                            # FIXED a-priori orientation: lower projection => more jailbreak,
                            # so score = -projection (both concept and refusal axes). Raw AUC.
                            x = [-r[axis][Lk] for r in ks]; y = [lab[r["id"]][1] for r in ks]
                            a, lo, hi, _ = _boot(x, y, seed=args.seed, orient=False)
                            cell[sp] = {"auc": round(a, 4), "ci95": [round(lo, 4), round(hi, 4)],
                                        "n": len(ks), "n_mal": int(sum(y))}
                        cell["orientation"] = "lower_proj_more_jailbreak"  # fixed a-priori (score=-proj)
                        auc[axis][Lk] = cell
            summary["auc"] = auc
            # headline print
            for L in layers:
                Lk = str(L)
                c = auc["concept"].get(Lk, {}).get("pooled", {})
                rf = auc["refusal"].get(Lk, {}).get("pooled", {})
                print(f"[x5][auc] L{L} pooled  concept AUC={c.get('auc')} CI{c.get('ci95')}  "
                      f"refusal AUC={rf.get('auc')} CI{rf.get('ci95')}", flush=True)

    json.dump(summary, open(os.path.join(out_dir, "summary.json"), "w"), indent=2)
    dc.write_done(out_dir, rows_written=n_proj, extra={"n_fit": n_fit, "auc_computed": summary["auc"] is not None})
    print(f"[x5] done -> {out_dir}", flush=True)
    print(f"date {time.strftime('%Y-%m-%dT%H:%M:%S')}", flush=True)


if __name__ == "__main__":
    main()
