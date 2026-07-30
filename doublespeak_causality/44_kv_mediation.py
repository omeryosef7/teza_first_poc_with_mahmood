"""
44_kv_mediation.py — S3 (NEXT_CAUSAL_SPRINT) Demonstration K/V mediation.

Localises WHERE in the receiver the doublespeak concept is routed, and resolves the
Stage-2 "cloze-readout-attends-context" confound. The receiver is ALWAYS the
DOUBLESPEAK prompt; we realise a 2x2 over

    Factor A = query STATE at codeword_last   (LayerPatch replace, block OUTPUT)
    Factor B = demonstration K/V              (DemoStateSwap at demo-codeword resid_pre)

    | cell | query state       | demo K/V     |
    | C1   | h_DS (self)       | DS           |  = plain DS forward (baseline)
    | C2   | h_Neutral (patch) | DS           |  = 34's DS_from_Neutral query transplant
    | C3   | h_DS (self)       | Neutralized  |  DemoStateSwap at demo codewords <- Neutral
    | C4   | h_Neutral (patch) | Neutralized  |  both together (ExitStack)

Two readouts per cell, both SCALAR (numbers only are persisted):
  1. semantic_score next-token mass (p_concept, p_codeword) — comparable to Stage 2.
  2. CONFOUND-FREE PatchscopeDecoder (07): the query codeword rep captured under the cell
     is injected into a DEMO-FREE inspection prompt, so the "?" slot cannot re-read the
     demos. This isolates concept-in-the-vector from concept-re-read-from-context.

Extra arms:
  * C1_selfswap — DemoStateSwap with source == the receiver's OWN demo resid_pre.
    Faithfulness: must equal C1 exactly.
  * random_control — DemoStateSwap at an equal count of NON-codeword demo positions,
    source rows from count-matched Neutral non-codeword positions. Concept must NOT move.

Estimands (reduced with stats.py, the 43 pattern), per layer window:
  DE_via_demoKV = mean(C2 - C4)   concept reading carried specifically by the demo K/V
  ReRead_test   = mean(C1 - C3)   THE discriminator: does neutralizing demo K/V collapse
                                  the concept even with the genuine DS query state?
  INT_2x2       = mean((C1-C3) - (C2-C4))
plus faithfulness (C1_selfswap - C1 ~ 0) and the random-control effect (C1 - random ~ 0).

The reducer `analyze_rows` is import-safe / CPU-only (no model), used by the test.

Usage:
  python 44_kv_mediation.py --bench ... --model ... --out-root ... --n-prompts 12 --seed 0
  python 44_kv_mediation.py --analyze <interv_raw.jsonl> --out summary.json   # reduce only
"""
import os
import sys
import json
import time
import math
import random
import argparse
import importlib.util
from collections import defaultdict
from contextlib import ExitStack

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds_common as dc
import pair_common as pc
import stats as st

HERE = os.path.dirname(os.path.abspath(__file__))

N_BOOT, MIN_N = 10000, 8
CELLS = ("C1", "C2", "C3", "C4")


def _load_numeric(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, filename))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# --------------------------------------------------------------------------- #
# Reducer (import-safe, CPU-only — no torch model needed)
# --------------------------------------------------------------------------- #
def item_key(r):
    return (r.get("split"), r.get("demo_style"), r.get("n_demos"),
            r.get("readout"), str(r.get("window")))


def _ci_block(x, y):
    d = st.paired_bootstrap_ci(x, y, n_boot=N_BOOT, seed=0)
    out = {"n": d["n"], "effect": round(d["mean_diff"], 5),
           "lo": round(d["lo"], 5), "hi": round(d["hi"], 5),
           "ci_reliable": d["ci_reliable"], "degenerate": d["degenerate"]}
    if d["n"] >= 2:
        out["p_raw"] = round(
            st.permutation_test_paired(x, y, n_perm=2000, seed=0)["p"], 6)
        out["cohens_d"] = round(st.paired_cohens_d(x, y), 4)
    return out


def _paired(a_map, b_map):
    keys = sorted(set(a_map) & set(b_map))
    return [a_map[k] for k in keys], [b_map[k] for k in keys], keys


# (name, minuend cell, subtrahend cell). INT_2x2 handled separately.
_ESTIMANDS = [
    ("ReRead_test",   "C1", "C3"),
    ("DE_via_demoKV", "C2", "C4"),
    ("faithfulness",  "C1_selfswap", "C1"),
    ("random_control", "C1", "random_control"),
]


def analyze_rows(rows, metric="p_concept"):
    """Reduce raw per-(prompt, window, cell) scalars into windowed estimands + CIs."""
    windows = sorted({str(r.get("window")) for r in rows
                      if str(r.get("window")) not in ("none", "None")})
    # (cell, window) -> {item_key -> value}
    cv = defaultdict(dict)
    for r in rows:
        v = r.get(metric)
        if v is None:
            continue
        cv[(r.get("cell"), str(r.get("window")))][item_key(r)] = v

    est, pgrid = {}, []
    for g in windows:
        maps = {c: cv.get((c, g), {}) for c in
                ("C1", "C2", "C3", "C4", "C1_selfswap", "random_control")}
        for name, a, b in _ESTIMANDS:
            x, y, keys = _paired(maps[a], maps[b])
            if len(x) < 2:
                est[f"{name}|{g}"] = {"estimand": name, "window": g,
                                      "n": len(x), "insufficient": True}
                continue
            blk = _ci_block(x, y)
            blk.update({"estimand": name, "window": g,
                        "thin": bool(blk["n"] < MIN_N)})
            est[f"{name}|{g}"] = blk
            if "p_raw" in blk:
                pgrid.append(f"{name}|{g}")

        # INT_2x2 = (C1 - C3) - (C2 - C4), paired over shared items
        shared = sorted(set(maps["C1"]) & set(maps["C2"])
                        & set(maps["C3"]) & set(maps["C4"]))
        if len(shared) >= 2:
            items = [(maps["C1"][k] - maps["C3"][k]) - (maps["C2"][k] - maps["C4"][k])
                     for k in shared]
            blk = _ci_block(items, [0.0] * len(items))
            blk.update({"estimand": "INT_2x2", "window": g,
                        "thin": bool(blk["n"] < MIN_N)})
            est[f"INT_2x2|{g}"] = blk
            if "p_raw" in blk:
                pgrid.append(f"INT_2x2|{g}")
        else:
            est[f"INT_2x2|{g}"] = {"estimand": "INT_2x2", "window": g,
                                   "n": len(shared), "insufficient": True}

    if pgrid:
        adj = st.holm_bonferroni([est[k]["p_raw"] for k in sorted(pgrid)])
        for k, pa in zip(sorted(pgrid), adj):
            est[k]["p_holm"] = round(float(pa), 6)
            est[k]["significant_corrected"] = bool(pa < 0.05)

    def eff(name, g):
        e = est.get(f"{name}|{g}")
        return e.get("effect") if e and "effect" in e else None

    verdicts = {}
    for g in windows:
        rr, de, it = eff("ReRead_test", g), eff("DE_via_demoKV", g), eff("INT_2x2", g)
        faith, rand = eff("faithfulness", g), eff("random_control", g)
        verdicts[g] = {
            # ReRead collapses -> the cloze readout re-reads the demos (trivial);
            # survives (small ReRead) -> the DS query state is self-sufficient.
            "reread_dependent_on_demoKV": (rr is not None and rr >= 0.05),
            "demoKV_carries_concept": (de is not None and de >= 0.05),
            "faithful_selfswap": (faith is not None and abs(faith) < 0.02),
            "random_control_inert": (rand is not None and abs(rand) < 0.05),
            "effects": {"ReRead_test": rr, "DE_via_demoKV": de, "INT_2x2": it,
                        "faithfulness": faith, "random_control": rand},
        }
    return {"metric": metric, "windows": windows, "min_n_for_confirmatory": MIN_N,
            "estimands": est, "verdicts": verdicts, "n_rows": len(rows)}


# --------------------------------------------------------------------------- #
# GPU path
# --------------------------------------------------------------------------- #
def _single_id(tokenizer, word):
    ids = (tokenizer.encode(f" {word}", add_special_tokens=False)
           or tokenizer.encode(word, add_special_tokens=False))
    return ids[-1]


def run(args):
    dc.set_seed(args.seed)
    rng = random.Random(args.seed)

    bench = json.load(open(args.bench))
    pair = bench["pair"]
    layer_windows = _load_numeric("beh_necessity", "18_run_behavioral_necessity.py").layer_windows

    lm = dc.load_model(args.model)
    L = lm.num_layers
    R = L - 4                                   # late confound-free readout layer (07 default)
    dec = _load_numeric("patchscope", "07_patchscope_readout.py").PatchscopeDecoder(lm)

    id_groups = {r: pc.word_first_ids(lm.tokenizer, pair[r])
                 for r in ("concept", "codeword") if pair.get(r)}
    concept_id = _single_id(lm.tokenizer, pair["concept"])
    code_id = _single_id(lm.tokenizer, pair["codeword"])

    splits = [s.strip() for s in args.splits.split(",") if s.strip()]
    rows = [r for r in bench["semantic"] if r["readout"] == args.readout
            and r["split"] in splits]
    by_sid = {r["sid"]: r for r in rows}
    by_cell = defaultdict(list)
    for r in rows:
        by_cell[(r["condition"], r["split"])].append(r)

    wmap = layer_windows(L)
    win_names = [w.strip() for w in args.windows.split(",") if w.strip()] \
        or ["early", "mid", "late"]
    windows = [(w, list(wmap[w])) for w in win_names if w in wmap]

    tag = args.model.split("/")[-1]
    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(
        args.out_root,
        f"pair_kv_mediation_{tag}_{time.strftime('%Y%m%d_%H%M%S')}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    raw_path = os.path.join(out_dir, "interv_raw.jsonl")
    fh = open(raw_path, "w")
    n_rows = [0]
    dev = lm.model.device

    print(f"[kv] L={L} R={R} windows={win_names} splits={splits} -> {out_dir}")

    @torch.no_grad()
    def eval_cell(ds_tok, ds_query, contexts):
        """Forward the DS receiver under `contexts`; return the two scalar readouts."""
        with ExitStack() as stack:
            for c in contexts:
                stack.enter_context(c)
            out = lm.model(**ds_tok, output_hidden_states=True, return_dict=True)
        probs = torch.softmax(out.logits[0, -1, :].float(), dim=-1)
        p_conc = float(sum(probs[i] for i in id_groups["concept"]))
        p_code = float(sum(probs[i] for i in id_groups["codeword"]))
        rep = out.hidden_states[R + 1][0, ds_query, :]
        ps_h, ps_c = dec.decode(rep.to(dev), R, concept_id, code_id)
        return p_conc, p_code, float(ps_h), float(ps_c)

    def emit(base, window, cell, n_swapped, res):
        p_conc, p_code, ps_h, ps_c = res
        rec = {**base, "window": window, "cell": cell, "n_demo_swapped": n_swapped,
               "p_concept": p_conc, "p_codeword": p_code,
               "ps_concept": ps_h, "ps_codeword": ps_c}
        fh.write(json.dumps(rec) + "\n")
        n_rows[0] += 1
        if n_rows[0] % 200 == 0:
            print(f"  [kv] {n_rows[0]} rows")

    @torch.no_grad()
    def capture_resid(templated, positions, want_post_last=False):
        """resid_pre (and optionally resid_post of the LAST position) at `positions`.
        Returns {'pre': Tensor[L, n_pos, H], 'post_last': Tensor[L, H] or None}."""
        comps = ["resid_pre", "resid_post"] if want_post_last else ["resid_pre"]
        tok = lm.tokenizer(templated, return_tensors="pt",
                           add_special_tokens=False).to(dev)
        with pc.ComponentCapture(lm, comps, positions) as cap:
            lm.model(**tok, return_dict=True)
        s = cap.stacked()
        post_last = s["resid_post"][:, -1, :] if want_post_last else None
        return {"pre": s["resid_pre"], "post_last": post_last}

    for split in splits:
        cand = sorted(by_cell.get(("DOUBLESPEAK", split), []),
                      key=lambda r: r["sid"])[: args.n_prompts]
        for r in cand:
            templated = dc.apply_template(lm.tokenizer, r["prompt"])
            pos = pc.resolve_positions(lm, templated, r["probe_word"])
            ds_query = pos.codeword_last
            ds_demo_cw = list(pos.codeword_all[:-1])          # prev_cw = hit.last_idx[:-1]
            cwset = set(pos.codeword_all)
            ds_tok = lm.tokenizer(templated, return_tensors="pt",
                                  add_special_tokens=False).to(dev)
            base = {"sid": r["sid"], "condition": "DOUBLESPEAK", "split": split,
                    "demo_style": r["demo_style"], "n_demos": r["n_demos"],
                    "readout": r["readout"]}

            # matched NEUTRAL_CODEWORD prompt (same split/style/n_demos/readout)
            nsid = f"NEUTRAL_CODEWORD|{split}|{r['demo_style']}|{r['n_demos']}|{r['readout']}"
            nrow = by_sid.get(nsid)

            # ---- source capture (one Neutral forward + one DS-own forward) ---- #
            neu_pre_demo = neu_post_query = None
            neu_pre_rand = ds_rand = None
            if nrow is not None:
                ntmpl = dc.apply_template(lm.tokenizer, nrow["prompt"])
                npos = pc.resolve_positions(lm, ntmpl, nrow["probe_word"])
                neu_demo_cw = list(npos.codeword_all[:-1])
                neu_cwset = set(npos.codeword_all)
                # count-matched random NON-codeword positions on both sides
                ds_pool = [p for p in range(0, ds_query) if p not in cwset]
                neu_pool = [p for p in range(0, npos.codeword_last) if p not in neu_cwset]
                m = min(len(ds_demo_cw), len(neu_demo_cw))
                rlen = min(len(ds_demo_cw), len(ds_pool), len(neu_pool))
                ds_rand = sorted(rng.sample(ds_pool, rlen)) if rlen else []
                neu_rand = sorted(rng.sample(neu_pool, rlen)) if rlen else []
                cap_pos = neu_demo_cw + neu_rand + [npos.codeword_last]
                ncap = capture_resid(ntmpl, cap_pos, want_post_last=True)
                nd = len(neu_demo_cw)
                neu_pre_demo = ncap["pre"][:, :nd, :]                  # [L, nd, H]
                neu_pre_rand = ncap["pre"][:, nd:nd + rlen, :]         # [L, rlen, H]
                neu_post_query = ncap["post_last"]                    # [L, H]
                # align to last-m most-recent demos on both sides
                ds_swap_pos = ds_demo_cw[-m:] if m else []
                neu_pre_demo_m = neu_pre_demo[:, -m:, :] if m else None
            else:
                ds_swap_pos, neu_pre_demo_m, m = [], None, 0

            # DS own resid_pre at its demo codewords (for the self-swap faithfulness arm)
            ds_pre_demo = (capture_resid(templated, ds_demo_cw)["pre"]
                           if ds_demo_cw else None)

            # ---- C1 baseline (window-independent; reused per window) ---- #
            c1 = eval_cell(ds_tok, ds_query, [])

            for wname, ells in windows:
                emit(base, wname, "C1", 0, c1)

                # C2: neutral query state via LayerPatch replace at ds_query
                if neu_post_query is not None:
                    c2_ctx = [dc.LayerPatch(lm.model, l, [ds_query],
                                            neu_post_query[l], "replace")
                              for l in ells]
                    emit(base, wname, "C2", 0, eval_cell(ds_tok, ds_query, c2_ctx))

                # C3: neutralized demo K/V via DemoStateSwap
                if m:
                    src3 = {l: neu_pre_demo_m[l] for l in ells}
                    c3_ctx = [pc.DemoStateSwap(lm.model, ds_swap_pos, src3)]
                    emit(base, wname, "C3", m, eval_cell(ds_tok, ds_query, c3_ctx))

                # C4: both together
                if neu_post_query is not None and m:
                    src4 = {l: neu_pre_demo_m[l] for l in ells}
                    c4_ctx = ([dc.LayerPatch(lm.model, l, [ds_query],
                                             neu_post_query[l], "replace") for l in ells]
                              + [pc.DemoStateSwap(lm.model, ds_swap_pos, src4)])
                    emit(base, wname, "C4", m, eval_cell(ds_tok, ds_query, c4_ctx))

                # C1_selfswap: DemoStateSwap with the receiver's OWN demo resid_pre
                if ds_pre_demo is not None:
                    srcs = {l: ds_pre_demo[l] for l in ells}
                    ss_ctx = [pc.DemoStateSwap(lm.model, ds_demo_cw, srcs)]
                    emit(base, wname, "C1_selfswap", len(ds_demo_cw),
                         eval_cell(ds_tok, ds_query, ss_ctx))

                # random_control: neutralize count-matched NON-codeword positions
                if neu_pre_rand is not None and ds_rand:
                    srcr = {l: neu_pre_rand[l] for l in ells}
                    rc_ctx = [pc.DemoStateSwap(lm.model, ds_rand, srcr)]
                    emit(base, wname, "random_control", len(ds_rand),
                         eval_cell(ds_tok, ds_query, rc_ctx))
    fh.close()

    all_rows = [json.loads(x) for x in open(raw_path)]
    summary = {
        "model": lm.meta(), "pair": pair, "plan": "STAGE3_KV_PLAN (S3)",
        "bench": os.path.abspath(args.bench), "readout": args.readout,
        "splits": splits, "windows": win_names,
        "windows_def": {k: list(v) for k, v in wmap.items()},
        "n_layers": L, "readout_layer": R, "n_prompts_per_cell": args.n_prompts,
        "seed": args.seed, "n_rows": len(all_rows),
        "p_concept": analyze_rows(all_rows, "p_concept"),
        "ps_concept": analyze_rows(all_rows, "ps_concept"),
        "status": "COMPLETE",
    }
    with open(os.path.join(out_dir, "kv_mediation_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(f"[kv] {len(all_rows)} rows -> {out_dir}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--analyze", default=None,
                    help="reduce-only: path to an existing interv_raw.jsonl (no model)")
    ap.add_argument("--out", default=None, help="summary path for --analyze")
    ap.add_argument("--metric", default="p_concept")
    ap.add_argument("--bench")
    ap.add_argument("--reps-dir", default=None,
                    help="matched-pair reps (optional; C2/C3 sources are captured live "
                         "from the Neutral forward for internal consistency)")
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(HERE, "outputs"))
    ap.add_argument("--readout", default="cloze")
    ap.add_argument("--windows", default="early,mid,late")
    ap.add_argument("--splits", default="dev,heldout")
    ap.add_argument("--n-prompts", type=int, default=12)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    if args.analyze:
        rows = [json.loads(x) for x in open(args.analyze)]
        res = analyze_rows(rows, args.metric)
        out = args.out or (args.analyze + ".summary.json")
        json.dump(res, open(out, "w"), indent=1)
        print(f"[kv-analyze] {len(rows)} rows metric={args.metric} -> {out}")
        return
    if not args.bench:
        raise SystemExit("--bench is required unless --analyze is given")
    run(args)


if __name__ == "__main__":
    main()
