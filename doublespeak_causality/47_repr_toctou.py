"""
47_repr_toctou.py — NEXT3 §T3. REPRESENTATIONAL (forward-only) TOCTOU generalization test.

Behaviorally, S4 #6 found the depth-gated refusal consequence is PAIR-DEPENDENT (noisy).
This isolates the CHECK itself, with no generation and no judge noise: does installing the
concept EARLY (before the ~L18 refusal check reads the codeword position) raise the refusal
representation MORE than installing it LATE (at/after the check)? If early > late ACROSS
bomb/grenade/chlorine, the depth-gated refusal check generalizes even where the downstream
behavioral flip does not.

Mechanism (why fixed-L18 readout is the RIGHT probe, not a confound): v_refusal was fit at
layer 18, i.e. hidden_states[19] == post-block-18 residual (build_refusal_direction_llama.py:
hs[L+1] == LayerPatch row L). A LayerPatch `add` at layer L propagates into hs[19] iff L<=18.
So an EARLY install (window ⊆ layers before the check) reaches the L18 refusal readout, while a
LATE install (window ⊆ layers at/after the check) does NOT — which is EXACTLY the signature of a
depth-gated check sitting at ~L18. output_hidden_states reflects the hook edit: HF appends
hidden_states[L+1] as the (hook-modified) return of block L (Llama decoder loop).

Design (per pair, per NEUTRAL prompt — receiver is the benign neutral item):
  * install pos = codeword_last (pair_common.resolve_positions on the TEMPLATED text)
  * readout    = projection of hs[refusal_layer+1][final_prompt] onto v_refusal (unit-normed)
  * ARMS: baseline (no install) | main install d_Direct over {early,mid,late} window (LayerPatch
    add @ codeword_last for every layer in the window) | norm-matched-random control over the SAME
    window (must NOT raise the projection).
  * per-item scalars only (projection floats) — NO generation, NO harmful text persisted.

Estimand (analyze_rows, CPU-testable):
  install_effect(pair,t)      = mean_i [ proj_main(t) - proj_baseline ]           (paired-bootstrap CI)
  random_effect(pair,t)       = mean_i [ proj_rand(t) - proj_baseline ]           (control, want ~0)
  install_above_random(pair,t)= mean_i [ proj_main(t) - proj_rand(t) ]
  early_vs_late(pair)         = mean_i [ proj_main(early) - proj_main(late) ]      (HYPOTHESIS > 0)
  pooled early_vs_late        = same per-item diff CONCATENATED across pairs       (generalization)

Reuse (no reinvention): ds_common.LayerPatch (add), pair_common.resolve_positions,
pair_common.norm_matched_random, 18_run_behavioral_necessity.layer_windows, d_Direct row L from
a pair_directions_*/directions.npz (key d_Direct|split|resid_post|codeword_last, [n_layers,H]),
v_refusal from refusal_direction_llama_L18.pt, stats.paired_bootstrap_ci.

Run (GPU, L40S) — pairs are comma-lists, POSITIONALLY matched (bench[i] <-> dir-dir[i]):
  python 47_repr_toctou.py \
    --bench data/pair_benchmark/pair_carrot_bomb.json,data/pair_benchmark/pair_carrot_grenade.json,data/pair_benchmark/pair_carrot_chlorine.json \
    --dir-dir outputs/pair_directions_BOMB,outputs/pair_directions_GRENADE,outputs/pair_directions_CHLORINE \
    --refusal-pt outputs/stage_gcg_full/refusal_direction_llama_L18.pt --n-items 40 --out <dir>
Reduce-only (CPU): python 47_repr_toctou.py --analyze <run_dir_or_repr_toctou_raw.jsonl>
"""
import os
import sys
import json
import time
import argparse
from contextlib import ExitStack

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stats as st

TIMINGS = ("early", "mid", "late")


# --------------------------------------------------------------------------- #
# Reducer (import-safe: numpy + stats only; no torch model, no harmful text)
# --------------------------------------------------------------------------- #
def _paired(x, y):
    """Paired-bootstrap CI of mean(x - y), + permutation p when n>=2. Mirrors 45's _ci_block."""
    d = st.paired_bootstrap_ci(x, y, n_boot=10000, seed=0)
    out = {"n": d["n"], "effect": round(d["mean_diff"], 6), "lo": round(d["lo"], 6),
           "hi": round(d["hi"], 6), "ci_reliable": d["ci_reliable"], "degenerate": d["degenerate"]}
    if d["n"] >= 2:
        out["p_raw"] = round(st.permutation_test_paired(x, y, n_perm=2000, seed=0)["p"], 6)
    return out


def analyze_rows(rows, timings=TIMINGS):
    """Reduce per-item projection rows into per-pair + pooled TOCTOU estimands.

    Row schema: {pid, pair, timing, arm, proj}. Baseline row has timing=="baseline", arm=="main".
    Install rows: timing in `timings`, arm in {"main","rand"}. `proj` is the L18 refusal
    projection scalar. Pairs on pid within each pair; pools per-item diffs ACROSS pairs.
    """
    idx = {(r["pid"], r["pair"], r["timing"], r.get("arm", "main")): float(r["proj"])
           for r in rows if r.get("proj") is not None}
    pairs = sorted({r["pair"] for r in rows})

    def g(pid, pair, timing, arm="main"):
        return idx.get((pid, pair, timing, arm))

    per_pair = {}
    pooled_evl = []                       # early-late main diffs, concatenated across pairs
    pooled_evm = []                       # early-MID main diffs (the non-degenerate test), across pairs
    pooled_ar = {t: [] for t in timings}  # install-above-random diffs, per timing, across pairs
    pgrid = []                            # pairs with an early_vs_mid p_raw, for Holm across pairs

    for pair in pairs:
        pids = sorted({r["pid"] for r in rows if r["pair"] == pair})
        res = {"install_effect": {}, "random_effect": {}, "install_above_random": {},
               "early_vs_late": None, "early_vs_mid": None, "n_items": 0}
        for t in timings:
            keep = [p for p in pids
                    if g(p, pair, t, "main") is not None and g(p, pair, "baseline") is not None]
            if len(keep) >= 2:
                res["install_effect"][t] = _paired(
                    [g(p, pair, t, "main") for p in keep], [g(p, pair, "baseline") for p in keep])
            keepr = [p for p in pids
                     if g(p, pair, t, "rand") is not None and g(p, pair, "baseline") is not None]
            if len(keepr) >= 2:
                res["random_effect"][t] = _paired(
                    [g(p, pair, t, "rand") for p in keepr], [g(p, pair, "baseline") for p in keepr])
            keepa = [p for p in pids
                     if g(p, pair, t, "main") is not None and g(p, pair, t, "rand") is not None]
            if len(keepa) >= 2:
                xm = [g(p, pair, t, "main") for p in keepa]
                xr = [g(p, pair, t, "rand") for p in keepa]
                res["install_above_random"][t] = _paired(xm, xr)
                pooled_ar[t] += [a - b for a, b in zip(xm, xr)]
        if "early" in timings and "late" in timings:
            keep = [p for p in pids
                    if g(p, pair, "early", "main") is not None and g(p, pair, "late", "main") is not None]
            res["n_items"] = len(keep)
            if len(keep) >= 2:
                xe = [g(p, pair, "early", "main") for p in keep]
                xl = [g(p, pair, "late", "main") for p in keep]
                res["early_vs_late"] = _paired(xe, xl)
                pooled_evl += [a - b for a, b in zip(xe, xl)]
        # BUG-CHECK C4: early_vs_late is MECHANICALLY DEGENERATE — the late window (layers
        # > refusal readout layer) is causally after the readout, so proj_main(late) is
        # bit-identical to baseline and early_vs_late == install_effect(early). The genuine
        # depth-differential is early_vs_MID (both windows propagate to the readout layer).
        # Headline this instead; keep early_vs_late only for reference.
        if "early" in timings and "mid" in timings:
            keepm = [p for p in pids
                     if g(p, pair, "early", "main") is not None and g(p, pair, "mid", "main") is not None]
            if len(keepm) >= 2:
                xe = [g(p, pair, "early", "main") for p in keepm]
                xm = [g(p, pair, "mid", "main") for p in keepm]
                res["early_vs_mid"] = _paired(xe, xm)
                pooled_evm += [a - b for a, b in zip(xe, xm)]
                if "p_raw" in res["early_vs_mid"]:
                    pgrid.append(pair)
        per_pair[pair] = res

    pooled = {"install_above_random": {}}
    if pooled_evl:   # kept for reference only (degenerate: late arm == baseline)
        pooled["early_vs_late"] = _paired(pooled_evl, [0.0] * len(pooled_evl))
    if pooled_evm:
        pooled["early_vs_mid"] = _paired(pooled_evm, [0.0] * len(pooled_evm))
    # GENERALIZATION VERDICT is based on early_vs_MID (the non-degenerate depth contrast).
    # NOTE: the dominant depth is pair-dependent (bomb early>mid; grenade/chlorine mid>early),
    # so 'early>mid in every pair' is NOT expected to hold — this flag is descriptive only.
    signs = [per_pair[p]["early_vs_mid"]["effect"] for p in pairs
             if per_pair[p].get("early_vs_mid") is not None]
    pooled["early_gt_mid_all_pairs"] = bool(signs) and all(s > 0 for s in signs)
    if pooled.get("early_vs_mid"):
        pem = pooled["early_vs_mid"]
        pooled["generalizes_early_dominant"] = bool(pooled["early_gt_mid_all_pairs"]
                                                    and pem.get("ci_reliable") and pem["lo"] > 0)
    for t, v in pooled_ar.items():
        if len(v) >= 2:
            pooled["install_above_random"][t] = _paired(v, [0.0] * len(v))

    # Holm across the per-pair early_vs_MID family (generalization is a multi-pair claim)
    if pgrid:
        keys = sorted(pgrid)
        adj = st.holm_bonferroni([per_pair[p]["early_vs_mid"]["p_raw"] for p in keys])
        for p, pa in zip(keys, adj):
            blk = per_pair[p]["early_vs_mid"]
            blk["p_holm"] = round(float(pa), 6)
            blk["significant_corrected"] = bool(pa < 0.05 and blk.get("ci_reliable"))
    return {"pairs": per_pair, "pooled": pooled, "timings": list(timings)}


# --------------------------------------------------------------------------- #
# GPU run (forward-only; imports torch only here)
# --------------------------------------------------------------------------- #
def _load_v18():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "v18", os.path.join(HERE, "18_run_behavioral_necessity.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _receiver_neutrals(bench, n_items):
    """Unique benign `neutral` prompts (dedup by pid; neutral text is demo-independent)."""
    seen, items = set(), []
    for r in bench["behavioral"]:
        if r["pid"] in seen:
            continue
        seen.add(r["pid"])
        items.append({"pid": r["pid"], "neutral": r["neutral"], "codeword": r["codeword"]})
    return items[:n_items] if n_items else items


def run():
    import torch
    import ds_common as dc
    import pair_common as pc

    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True,
                    help="comma-list of pair benchmark jsons (positionally matched to --dir-dir)")
    ap.add_argument("--dir-dir", required=True,
                    help="comma-list of pair_directions dirs (each with directions.npz)")
    ap.add_argument("--refusal-pt", required=True, help="refusal_direction_llama_L18.pt")
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--dir-split", default="heldout", choices=["dev", "heldout"])
    ap.add_argument("--refusal-layer", type=int, default=None,
                    help="override; else read from the .pt's .json metadata")
    ap.add_argument("--windows", default=",".join(TIMINGS),
                    help="comma list of timing windows (subset of early,mid,late)")
    ap.add_argument("--alpha", type=float, default=1.0, help="d_Direct install dose")
    ap.add_argument("--n-items", type=int, default=40)
    ap.add_argument("--enable-thinking", default="default", choices=["default", "on", "off"])
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", "--out-dir", dest="out", default=None)
    args = ap.parse_args()

    benches = [b for b in args.bench.split(",") if b.strip()]
    dirdirs = [d for d in args.dir_dir.split(",") if d.strip()]
    if len(benches) != len(dirdirs):
        raise SystemExit(f"--bench ({len(benches)}) and --dir-dir ({len(dirdirs)}) must align 1:1")
    timings = tuple(w for w in args.windows.split(",") if w.strip())
    _ET = {"default": None, "on": True, "off": False}[args.enable_thinking]

    dc.set_seed(args.seed)
    v18 = _load_v18()
    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    tag = args.model.split("/")[-1]
    out_dir = args.out or os.path.join(
        HERE, "outputs", f"repr_toctou_{tag}_{time.strftime('%Y%m%d_%H%M%S')}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)

    v_ref = torch.load(args.refusal_pt).float().flatten()
    v_hat = v_ref / (v_ref.norm() + 1e-8)
    rlayer = args.refusal_layer if args.refusal_layer is not None \
        else json.load(open(args.refusal_pt.replace(".pt", ".json")))["layer"]

    lm = dc.load_model(args.model)
    v_hat_dev = v_hat.to(lm.model.device)
    windows_all = v18.layer_windows(lm.num_layers)
    windows = {t: windows_all[t] for t in timings}
    # readout is hs[rlayer+1]; a LATE window fully downstream of it is mechanically inert (documented)
    read_hs = rlayer + 1

    @torch.no_grad()
    def projection(text, patches, install_pos, read_pos):
        """Forward with LayerPatch `add` hooks; return proj of hs[read_hs][read_pos] onto v_hat."""
        tok = lm.tokenizer(text, return_tensors="pt", add_special_tokens=False).to(lm.model.device)
        with ExitStack() as stack:
            for (L, vec) in patches:
                stack.enter_context(dc.LayerPatch(lm.model, L, [install_pos],
                                                  vector=vec.to(lm.model.device), mode="add",
                                                  alpha=args.alpha))
            out = lm.model(**tok, output_hidden_states=True, return_dict=True)
        resid = out.hidden_states[read_hs][0, read_pos, :].float()
        return float(torch.dot(resid, v_hat_dev.float()))

    rows, pairs_meta, n_skip = [], [], 0
    for bpath, dpath in zip(benches, dirdirs):
        bench = json.load(open(bpath))
        concept = bench["pair"]["concept"]
        codeword = bench["pair"]["codeword"]
        dirs = np.load(os.path.join(dpath, "directions.npz"))
        dkey = f"d_Direct|{args.dir_split}|resid_post|codeword_last"
        d_direct = dirs[dkey].astype(np.float32)                  # [n_layers, H], row L == LayerPatch L
        # sanity: the directions dir must belong to THIS pair (positional alignment guard)
        dsum = os.path.join(dpath, "directions_summary.json")
        if os.path.exists(dsum):
            dpair = json.load(open(dsum)).get("pair", {})
            if dpair.get("concept") and dpair["concept"] != concept:
                raise SystemExit(f"pair mismatch: bench concept={concept} but {dpath} is {dpair.get('concept')}")
        d_by_L = {L: torch.from_numpy(d_direct[L]) for L in range(lm.num_layers)}
        # per-layer norm-matched random control vectors (deterministic; matched to d_Direct[L] norm)
        rand_by_L = {L: pc.norm_matched_random(torch.from_numpy(d_direct[L]), 1, args.seed)[0]
                     for L in range(lm.num_layers)}
        pairs_meta.append({"concept": concept, "codeword": codeword, "bench": os.path.abspath(bpath),
                           "dir_dir": os.path.abspath(dpath), "dir_key": dkey})

        items = _receiver_neutrals(bench, args.n_items)
        n_base = 0
        for i, it in enumerate(items):
            neu = dc.apply_template(lm.tokenizer, it["neutral"], enable_thinking=_ET)
            try:
                pos = pc.resolve_positions(lm, neu, codeword)
            except Exception:
                n_skip += 1
                continue
            if pos.codeword_last is None:
                n_skip += 1
                continue
            ipos, rpos = pos.codeword_last, pos.final_prompt

            def emit(timing, arm, patches):
                rows.append({"pid": it["pid"], "pair": concept, "timing": timing, "arm": arm,
                             "proj": projection(neu, patches, ipos, rpos)})

            emit("baseline", "main", [])                                     # no-install baseline
            n_base += 1
            for t, wl in windows.items():
                emit(t, "main", [(L, d_by_L[L]) for L in wl])               # concept install
                emit(t, "rand", [(L, rand_by_L[L]) for L in wl])            # norm-matched random control
            if (i + 1) % 10 == 0:
                print(f"  [{concept}] {i+1}/{len(items)} (baseline n={n_base})", flush=True)
        print(f"[repr_toctou] pair={concept}: {n_base} items done", flush=True)

    analysis = analyze_rows(rows, timings=timings)
    summary = {"plan": "NEXT3 §T3 representational TOCTOU generalization", "model": args.model,
               "meta": lm.meta(), "refusal_pt": os.path.abspath(args.refusal_pt),
               "refusal_layer": rlayer, "readout_hidden_state_index": read_hs,
               "dir_split": args.dir_split, "alpha": args.alpha, "windows": {t: list(windows[t]) for t in timings},
               "n_items_arg": args.n_items, "n_skipped": n_skip, "pairs": pairs_meta,
               "status": "COMPLETE", "analysis": analysis}
    with open(os.path.join(out_dir, "repr_toctou_raw.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    json.dump(summary, open(os.path.join(out_dir, "repr_toctou_summary.json"), "w"), indent=2)

    _print_summary(analysis)
    print(f"[repr_toctou] {len(pairs_meta)} pairs, {len(rows)} rows, skipped={n_skip} -> {out_dir}")


def _print_summary(analysis):
    for pair, res in analysis["pairs"].items():
        evl = res.get("early_vs_late")
        if evl:
            print(f"  {pair:10s} early-late eff={evl['effect']:+.4f} [{evl['lo']:+.4f},{evl['hi']:+.4f}] "
                  f"n={evl['n']} sig={evl.get('significant_corrected')}")
    pev = analysis["pooled"].get("early_vs_late")
    if pev:
        print(f"  POOLED     early-late eff={pev['effect']:+.4f} [{pev['lo']:+.4f},{pev['hi']:+.4f}] "
              f"n={pev['n']} generalizes={analysis['pooled'].get('generalizes')}")


def analyze_only(path):
    p = path if path.endswith(".jsonl") else os.path.join(path, "repr_toctou_raw.jsonl")
    rows = [json.loads(l) for l in open(p)]
    res = analyze_rows(rows)
    out = os.path.join(os.path.dirname(os.path.abspath(p)), "repr_toctou_reanalysis.json")
    json.dump(res, open(out, "w"), indent=2)
    print(f"[repr_toctou] reduce-only over {len(rows)} rows -> {out}")
    _print_summary(res)


if __name__ == "__main__":
    if "--analyze" in sys.argv:
        i = sys.argv.index("--analyze")
        analyze_only(sys.argv[i + 1])
    else:
        run()
