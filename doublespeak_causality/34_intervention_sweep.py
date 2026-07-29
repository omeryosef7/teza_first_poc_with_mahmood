"""
34_intervention_sweep.py — CAUSAL_CORE_PLAN §4 + §5 (S5/S6/S7).

The intervention engine for the fixed pair. One script, four modes, so the layer scan,
the dose-response, the control battery and the held-out confirmation all share exactly
the same patching path (no arm can differ by accident):

  --mode layer_scan   every layer x a coarse alpha grid, arms {add_Direct, add_DS} plus
                      identity and a small random control. Locates candidate layers.
  --mode dose         selected layers x a fine SIGNED alpha grid (§4.5): is the effect
                      monotonic and REVERSIBLE?
  --mode controls     selected layers x the full matched-perturbation battery (§5):
                      >=20 norm-matched random, orthogonal-random, in-PCA-subspace
                      random, unrelated/benign/other-codeword directions, adjacent-token
                      and random-token sites, shuffled source->target patches.
  --mode replace      activation replacement (§4.4) over single layers and windows:
                      Neutral<-DS, Neutral<-Direct, DS<-Neutral, plus identity/random.

Outcome is the FORWARD-ONLY semantic score (next-token probability mass on the concept
vs the codeword). That is ~10x cheaper than generation and is what makes the exhaustive
sweep affordable; --generate additionally records the one-word label on a subsample.

CROSS-FITTING (§2, §14) is on by default: a prompt in split `dev` is intervened with the
direction fitted on `heldout`, and vice versa, so no test prompt contributed to the
direction that moves it.

Reuse: ds_common.LayerPatch (unchanged), pair_common.semantic_score / patched_generate /
control-vector builders, 18_run_behavioral_necessity.layer_windows (the canonical window
definition). Scalars only are persisted.

Usage:
  python 34_intervention_sweep.py --bench ... --reps-dir ... --dir-dir ... --mode layer_scan
"""
import os
import re
import sys
import json
import time
import random
import argparse
import importlib.util

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds_common as dc
import pair_common as pc

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_numeric(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, filename))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_nec = _load_numeric("beh_necessity", "18_run_behavioral_necessity.py")
layer_windows = _nec.layer_windows          # canonical early/mid/late definition

N_RANDOM_CONTROLS = 20                      # plan §5: ">=20 norm-matched random vectors"


def other(split):
    return "heldout" if split == "dev" else "dev"


def parse_floats(s):
    return [float(x) for x in s.split(",") if x.strip()]


def parse_ints(s):
    return [int(x) for x in s.split(",") if x.strip()]


# --------------------------------------------------------------------------- #
# Patch-site resolution
# --------------------------------------------------------------------------- #
def patch_sites(pos, site, rng):
    """Token indices to intervene on, for a resolved PairPositions and a site name."""
    if site == "codeword_last":
        return [pos.codeword_last]
    if site == "codeword_all":
        return list(pos.codeword_all)
    if site == "following":
        return [] if pos.following is None else [pos.following]
    if site == "final_prompt":
        return [pos.final_prompt]
    if site == "adjacent":                       # control: the token before the codeword
        p = pos.codeword_last - 1
        return [p] if p >= 0 else []
    if site == "random_token":                   # control: a random earlier token
        hi = max(1, pos.codeword_last)
        return [rng.randrange(0, hi)]
    raise ValueError(f"unknown patch site {site!r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--reps-dir", required=True)
    ap.add_argument("--dir-dir", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--out-root", default=os.path.join(HERE, "outputs"))
    ap.add_argument("--mode", required=True,
                    choices=["layer_scan", "dose", "controls", "replace"])
    ap.add_argument("--readout", default="one_word")
    ap.add_argument("--component", default="resid_post",
                    help="LayerPatch edits the block OUTPUT, so directions must come "
                         "from resid_post; other values are for diagnostics only")
    ap.add_argument("--dir-position", default="codeword_last",
                    help="position the direction was FITTED at")
    ap.add_argument("--site", default="codeword_last",
                    help="token site the direction is APPLIED at")
    ap.add_argument("--layers", default="", help="comma ints; empty => all layers")
    ap.add_argument("--windows", default="",
                    help="comma window names for --mode replace (early,mid,late)")
    ap.add_argument("--alphas", default="1.0")
    ap.add_argument("--n-prompts", type=int, default=20,
                    help="prompts per condition (matched cells, deterministic)")
    ap.add_argument("--splits", default="dev,heldout")
    ap.add_argument("--crossfit", default="true", choices=["true", "false"])
    ap.add_argument("--generate", action="store_true",
                    help="also record the one-word label (slower)")
    ap.add_argument("--max-new-tokens", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    rng = random.Random(args.seed)
    crossfit = args.crossfit == "true"

    bench = json.load(open(args.bench))
    pair = bench["pair"]
    reps_sum = json.load(open(os.path.join(args.reps_dir, "reps_summary.json")))
    dirs = np.load(os.path.join(args.dir_dir, "directions.npz"))
    per_prompt = np.load(os.path.join(args.reps_dir, "per_prompt.npz"))["resid_post_codeword"]

    lm = dc.load_model(args.model)
    L = lm.num_layers
    if L != reps_sum["n_layers"]:
        raise SystemExit(f"layer mismatch: model {L} vs reps {reps_sum['n_layers']}")

    layers = parse_ints(args.layers) if args.layers else list(range(L))
    alphas = parse_floats(args.alphas)
    wins = [w.strip() for w in args.windows.split(",") if w.strip()]
    splits = [s.strip() for s in args.splits.split(",") if s.strip()]

    id_groups = {r: pc.word_first_ids(lm.tokenizer, pair[r])
                 for r in ("concept", "codeword", "benign_source", "unrelated_source")
                 if pair.get(r)}

    # ---- select matched prompt cells ----
    sem = [r for r in bench["semantic"] if r["readout"] == args.readout]
    cells = {}
    for r in sem:
        cells.setdefault((r["condition"], r["split"]), []).append(r)
    for k in cells:
        cells[k].sort(key=lambda r: r["sid"])

    def pick(condition, split):
        return cells.get((condition, split), [])[: args.n_prompts]

    # per-prompt source reps for replacement arms, indexed by matched cell
    row_of = {r["sid"]: r["row"] for r in reps_sum["rows"]}

    def source_vec(condition, ref_row, ell):
        """Rep of the matched prompt in `condition` (same style/n_demos/split)."""
        sid = f"{condition}|{ref_row['split']}|{ref_row['demo_style']}|" \
              f"{ref_row['n_demos']}|{ref_row['readout']}"
        r = row_of.get(sid)
        if r is None:
            return None
        return torch.from_numpy(per_prompt[r, ell, :].astype(np.float32))

    def direction(name, split, ell):
        key = f"{name}|{other(split) if crossfit else split}|{args.component}|{args.dir_position}"
        if key not in dirs:
            return None
        return torch.from_numpy(dirs[key][ell].astype(np.float32))

    def subspace(split, ell):
        key = f"pca_DS|{other(split) if crossfit else split}|{ell}"
        return torch.from_numpy(dirs[key].astype(np.float32)) if key in dirs else None

    tag = args.model.split("/")[-1]
    uniq = os.environ.get("SLURM_JOB_ID") or str(os.getpid())
    out_dir = os.path.join(
        args.out_root,
        f"pair_interv_{args.mode}_{tag}_{time.strftime('%Y%m%d_%H%M%S')}_{uniq}")
    os.makedirs(out_dir, exist_ok=True)
    print(f"[interv] mode={args.mode} L={L} layers={len(layers)} alphas={alphas} "
          f"site={args.site} crossfit={crossfit} -> {out_dir}")

    raw_path = os.path.join(out_dir, "interv_raw.jsonl")
    fh = open(raw_path, "w")
    n_rows = 0

    def emit(row, templated, positions, patches, extra):
        nonlocal n_rows
        p = pc.semantic_score(lm, templated, id_groups, patches)
        rec = {"sid": row["sid"], "condition": row["condition"], "split": row["split"],
               "demo_style": row["demo_style"], "n_demos": row["n_demos"],
               "readout": row["readout"], "n_patch_positions": len(positions),
               "p_concept": p.get("concept"), "p_codeword": p.get("codeword"),
               "p_benign": p.get("benign_source"), "p_unrelated": p.get("unrelated_source"),
               **extra}
        if args.generate:
            rec["answer"] = pc.patched_generate(
                lm, templated, patches, args.max_new_tokens).strip()[:64]
        fh.write(json.dumps(rec) + "\n")
        n_rows += 1
        if n_rows % 500 == 0:
            print(f"  [interv] {n_rows} rows")

    # ---- arm construction -------------------------------------------------- #
    def add_arms(split, ell):
        """(arm_name, vector, mode) triples for additive/projective interventions."""
        arms = []
        for dname in ("d_Direct", "d_DS"):
            v = direction(dname, split, ell)
            if v is not None:
                arms.append((f"add_{dname}", v, "add"))
        if args.mode in ("controls",):
            for dname in ("d_benign", "d_unrelated", "d_repeated"):
                v = direction(dname, split, ell)
                if v is not None:
                    arms.append((f"add_{dname}", v, "add"))
        return arms

    def random_controls(split, ell, n):
        """The matched-perturbation distribution (plan §5)."""
        base = direction("d_DS", split, ell)
        if base is None:
            return []
        out = []
        rnd = pc.norm_matched_random(base, n, seed=args.seed + 1000 * ell)
        orth = pc.orthogonal_random(base, n, seed=args.seed + 2000 * ell)
        for i in range(n):
            out.append((f"rand_norm_matched_{i}", rnd[i], "add"))
            out.append((f"rand_orthogonal_{i}", orth[i], "add"))
        B = subspace(split, ell)
        if B is not None:
            insub = pc.in_subspace_random(B, base, n, seed=args.seed + 3000 * ell)
            for i in range(n):
                out.append((f"rand_in_pca_subspace_{i}", insub[i], "add"))
        return out

    # ---- the four modes ---------------------------------------------------- #
    def run_additive(target_condition, layer_list, alpha_list, n_rand, sites):
        for split in splits:
            for row in pick(target_condition, split):
                templated = dc.apply_template(lm.tokenizer, row["prompt"])
                pos = pc.resolve_positions(lm, templated, row["probe_word"])
                for site in sites:
                    positions = patch_sites(pos, site, rng)
                    if not positions:
                        continue
                    # identity / alpha=0 control, once per (prompt, site)
                    emit(row, templated, positions, [],
                         {"arm": "identity", "layer": None, "alpha": 0.0,
                          "site": site, "mode": args.mode})
                    for ell in layer_list:
                        arms = add_arms(split, ell) + random_controls(split, ell, n_rand)
                        for (aname, vec, pmode) in arms:
                            for a in alpha_list:
                                emit(row, templated, positions,
                                     [(ell, positions, vec, pmode, a)],
                                     {"arm": aname, "layer": ell, "alpha": a,
                                      "site": site, "mode": args.mode})

    def run_projection(layer_list, alpha_list, sites):
        """Removal (§4.3): project the direction OUT of a successful DS run."""
        for split in splits:
            for row in pick("DOUBLESPEAK", split):
                templated = dc.apply_template(lm.tokenizer, row["prompt"])
                pos = pc.resolve_positions(lm, templated, row["probe_word"])
                for site in sites:
                    positions = patch_sites(pos, site, rng)
                    if not positions:
                        continue
                    emit(row, templated, positions, [],
                         {"arm": "identity", "layer": None, "alpha": 0.0,
                          "site": site, "mode": args.mode})
                    for ell in layer_list:
                        for dname in ("d_DS", "d_Direct"):
                            v = direction(dname, split, ell)
                            if v is None:
                                continue
                            for a in alpha_list:
                                emit(row, templated, positions,
                                     [(ell, positions, v, "project_out", a)],
                                     {"arm": f"projout_{dname}", "layer": ell,
                                      "alpha": a, "site": site, "mode": args.mode})

    def run_replace(window_names, layer_list):
        """Activation replacement (§4.4), single layers and multi-layer windows."""
        wmap = layer_windows(L)
        groups = [(f"layer{l}", [l]) for l in layer_list]
        groups += [(w, list(wmap[w])) for w in window_names if w in wmap]
        specs = [("Neutral_from_DS", "NEUTRAL_CODEWORD", "DOUBLESPEAK"),
                 ("Neutral_from_Direct", "NEUTRAL_CODEWORD", "DIRECT_CONCEPT"),
                 ("DS_from_Neutral", "DOUBLESPEAK", "NEUTRAL_CODEWORD"),
                 ("Neutral_from_Benign", "NEUTRAL_CODEWORD", "BENIGN_REMAP"),
                 ("Neutral_from_Unrelated", "NEUTRAL_CODEWORD", "UNRELATED_TARGET")]
        for split in splits:
            for (aname, tgt_cond, src_cond) in specs:
                for row in pick(tgt_cond, split):
                    templated = dc.apply_template(lm.tokenizer, row["prompt"])
                    pos = pc.resolve_positions(lm, templated, row["probe_word"])
                    positions = patch_sites(pos, args.site, rng)
                    if not positions:
                        continue
                    emit(row, templated, positions, [],
                         {"arm": "identity", "layer": None, "alpha": 0.0,
                          "site": args.site, "mode": args.mode, "group": "none"})
                    for gname, ells in groups:
                        patches, ok = [], True
                        for ell in ells:
                            v = source_vec(src_cond, row, ell)
                            if v is None:
                                ok = False
                                break
                            patches.append((ell, positions, v, "replace", 1.0))
                        if not ok:
                            continue
                        emit(row, templated, positions, patches,
                             {"arm": aname, "layer": (ells[0] if len(ells) == 1 else None),
                              "group": gname, "alpha": 1.0, "site": args.site,
                              "mode": args.mode})
                        # shuffled source->target control (plan §5)
                        shuf = [r for r in cells.get((src_cond, split), [])
                                if r["sid"] != row["sid"]]
                        if shuf:
                            donor = shuf[rng.randrange(len(shuf))]
                            dpatches, ok = [], True
                            for ell in ells:
                                dr = row_of.get(donor["sid"])
                                if dr is None:
                                    ok = False
                                    break
                                dv = torch.from_numpy(
                                    per_prompt[dr, ell, :].astype(np.float32))
                                dpatches.append((ell, positions, dv, "replace", 1.0))
                            if ok:
                                emit(row, templated, positions, dpatches,
                                     {"arm": f"{aname}_SHUFFLED", "layer":
                                      (ells[0] if len(ells) == 1 else None),
                                      "group": gname, "alpha": 1.0, "site": args.site,
                                      "mode": args.mode})

    t0 = time.time()
    if args.mode == "layer_scan":
        run_additive("NEUTRAL_CODEWORD", layers, alphas, n_rand=2,
                     sites=[args.site])
    elif args.mode == "dose":
        run_additive("NEUTRAL_CODEWORD", layers, alphas, n_rand=2, sites=[args.site])
        run_projection(layers, [a for a in alphas if a >= 0], sites=[args.site])
    elif args.mode == "controls":
        run_additive("NEUTRAL_CODEWORD", layers, alphas, n_rand=N_RANDOM_CONTROLS,
                     sites=[args.site, "adjacent", "random_token"])
    elif args.mode == "replace":
        run_replace(wins or ["early", "mid", "late"], layers)
    fh.close()

    summary = {
        "model": lm.meta(), "pair": pair, "plan": "CAUSAL_CORE_PLAN §4/§5 (S5-S7)",
        "mode": args.mode, "bench": os.path.abspath(args.bench),
        "reps_dir": os.path.abspath(args.reps_dir),
        "dir_dir": os.path.abspath(args.dir_dir),
        "readout": args.readout, "component": args.component,
        "dir_position": args.dir_position, "site": args.site,
        "layers": layers, "alphas": alphas, "windows": wins,
        "splits": splits, "crossfit": crossfit,
        "n_prompts_per_cell": args.n_prompts, "n_random_controls": N_RANDOM_CONTROLS,
        "generate": args.generate, "seed": args.seed,
        "n_layers": L, "windows_def": {k: list(v) for k, v in layer_windows(L).items()},
        "n_rows": n_rows, "elapsed_s": round(time.time() - t0, 1),
        "status": "COMPLETE",
    }
    with open(os.path.join(out_dir, "interv_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(f"[interv] {n_rows} rows in {summary['elapsed_s']}s -> {out_dir}")


if __name__ == "__main__":
    main()
