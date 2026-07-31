"""
next5_w3b_superposition.py — NEXT5 W3-b: test the paper's SECOND (untested) hypothesis.

The paper hypothesizes TOCTOU (we tested it, S4/T3) AND semantic SUPERPOSITION: the codeword's
representation simultaneously encodes the codeword identity (carrot) AND the harmful concept
(bomb). This tests superposition via direction projection — no new model runs, reuses committed
diff-of-means axes + captured reps.

Axes (built on DEV, unit-normalized per layer; anchored at the NEUTRAL_CODEWORD mean):
  concept axis  = d_Direct   = mean(DIRECT_CONCEPT)   - mean(NEUTRAL_CODEWORD)
  codeword axis = d_repeated = mean(REPEATED_CODEWORD)- mean(NEUTRAL_CODEWORD)
Reps tested on HELDOUT (clean train/test split). For each rep r at layer L:
  concept_component  = (r - mu_NEUTRAL) . d_Direct_hat
  codeword_component = (r - mu_NEUTRAL) . d_repeated_hat

Control-separation gate (must pass for a both-components result to mean superposition):
  DIRECT     loads concept >> codeword     (concept present, codeword absent)
  REPEATED   loads codeword >> concept     (codeword present, concept absent)
Superposition signature: DOUBLESPEAK loads BOTH concept AND codeword (both CIs exclude 0) in the
emergence band. Also reports cos(concept_axis, codeword_axis) per layer (axes must be distinct).

Scalars only (projections + CIs + cosines); no reps/text persisted to stdout.

Run (CPU): python next5_w3b_superposition.py \
    --reps-dir outputs/pair_reps_..._694691 --dir-dir outputs/pair_directions_..._694691
"""
import os
import sys
import json
import argparse
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stats as st

CONCEPT_AX = "d_Direct"
CODEWORD_AX = "d_repeated"
COND = ["DIRECT_CONCEPT", "REPEATED_CODEWORD", "DOUBLESPEAK", "NEUTRAL_CODEWORD",
        "BENIGN_REMAP", "UNRELATED_TARGET"]


def unit_rows(M):
    n = np.linalg.norm(M, axis=-1, keepdims=True)
    return M / (n + 1e-8)


def ci1(x):
    """one-sample mean + bootstrap CI (reuse paired_bootstrap_ci vs 0)."""
    d = st.paired_bootstrap_ci(list(map(float, x)), [0.0] * len(x), n_boot=10000, seed=0)
    return {"mean": round(d["mean_diff"], 4), "lo": round(d["lo"], 4), "hi": round(d["hi"], 4),
            "n": d["n"], "excl0": bool(d["lo"] > 0 or d["hi"] < 0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps-dir", required=True)
    ap.add_argument("--dir-dir", required=True)
    ap.add_argument("--component", default="resid_post")
    ap.add_argument("--position", default="codeword_last")
    ap.add_argument("--axis-split", default="dev", help="split used to BUILD axes")
    ap.add_argument("--test-split", default="heldout", help="split used to TEST reps")
    ap.add_argument("--band", default="12,24", help="emergence band lo,hi (inclusive) for the verdict")
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    comp, pos = args.component, args.position
    dirs = np.load(os.path.join(args.dir_dir, "directions.npz"), allow_pickle=True)
    d_conc = unit_rows(dirs[f"{CONCEPT_AX}|{args.axis_split}|{comp}|{pos}"].astype(np.float64))   # (32,H)
    d_code = unit_rows(dirs[f"{CODEWORD_AX}|{args.axis_split}|{comp}|{pos}"].astype(np.float64))
    L = d_conc.shape[0]
    cos_axes = [float(np.dot(d_conc[l], d_code[l])) for l in range(L)]

    means = np.load(os.path.join(args.reps_dir, "means.npz"), allow_pickle=True)
    mu_neutral = means[f"NEUTRAL_CODEWORD|{args.axis_split}|{comp}|{pos}"].astype(np.float64)      # (32,H)

    summ = json.load(open(os.path.join(args.reps_dir, "reps_summary.json")))
    rows = summ["rows"]
    pp = np.load(os.path.join(args.reps_dir, "per_prompt.npz"), allow_pickle=True)
    cands = [f"{comp}_{pos}", f"{comp}_{pos.replace('_last', '')}"]
    key = next((k for k in cands if k in pp), None)
    if key is None:
        raise KeyError(f"per_prompt.npz lacks any of {cands}; has {list(pp.keys())}")
    cube = pp[key].astype(np.float64)            # (n_rows, 32, H) aligned with rows

    # collect per-condition prompt indices on the test split
    by_cond = defaultdict(list)
    for i, r in enumerate(rows):
        if r.get("split") == args.test_split:
            by_cond[r["condition"]].append(i)

    lo_b, hi_b = (int(x) for x in args.band.split(","))
    band = list(range(lo_b, hi_b + 1))

    results = {}
    band_vals = {}                                # cond -> (conc_band[n], code_band[n]) for 2-sample tests
    for cond in COND:
        idx = by_cond.get(cond, [])
        if not idx:
            continue
        R = cube[idx]                             # (n, 32, H)
        Rc = R - mu_neutral[None, :, :]           # center at neutral anchor
        conc = np.einsum("nlh,lh->nl", Rc, d_conc)   # (n, 32) concept component per layer
        code = np.einsum("nlh,lh->nl", Rc, d_code)   # (n, 32) codeword component per layer
        # band-averaged per prompt, then one-sample CI across prompts
        conc_band = conc[:, band].mean(axis=1)
        code_band = code[:, band].mean(axis=1)
        band_vals[cond] = (conc_band, code_band)
        results[cond] = {
            "n_prompts": len(idx),
            "concept_component_band": ci1(conc_band),
            "codeword_component_band": ci1(code_band),
            "per_layer_concept_mean": [round(float(conc[:, l].mean()), 4) for l in range(L)],
            "per_layer_codeword_mean": [round(float(code[:, l].mean()), 4) for l in range(L)],
        }

    # Two-sample (unpaired) bootstrap difference of means, DS vs a remap control.
    def diff2(a, b):
        a = np.asarray(a, float); b = np.asarray(b, float)
        rng = np.random.default_rng(0)
        boot = np.array([a[rng.integers(0, len(a), len(a))].mean()
                         - b[rng.integers(0, len(b), len(b))].mean() for _ in range(20000)])
        boot.sort()
        lo, hi = float(boot[500]), float(boot[19500])
        return {"mean": round(float(a.mean() - b.mean()), 4), "lo": round(lo, 4),
                "hi": round(hi, 4), "excl0": bool(lo > 0 or hi < 0)}

    # DS concept-specificity: DS concept component ABOVE the benign-remap / unrelated controls
    # (the codeword component is shared by ALL codeword conditions, so it is NOT DS-specific;
    # the DS-specific claim is the CONCEPT riding on top of the retained codeword component).
    concept_specificity = {}
    if "DOUBLESPEAK" in band_vals:
        dsc = band_vals["DOUBLESPEAK"][0]
        for ctrl in ("BENIGN_REMAP", "UNRELATED_TARGET"):
            if ctrl in band_vals:
                concept_specificity[f"DS_minus_{ctrl}"] = diff2(dsc, band_vals[ctrl][0])

    # verdicts
    ds = results.get("DOUBLESPEAK", {})
    direct = results.get("DIRECT_CONCEPT", {})
    repeated = results.get("REPEATED_CODEWORD", {})
    def excl(d, k): return bool(d.get(k, {}).get("excl0"))
    def m(d, k): return d.get(k, {}).get("mean")

    gate_direct = (excl(direct, "concept_component_band")
                   and m(direct, "concept_component_band") > m(direct, "codeword_component_band"))
    gate_repeated = (m(repeated, "codeword_component_band") is not None
                     and m(repeated, "codeword_component_band") > m(repeated, "concept_component_band"))
    ds_both = (excl(ds, "concept_component_band") and excl(ds, "codeword_component_band")
               and m(ds, "concept_component_band") > 0 and m(ds, "codeword_component_band") > 0)
    # concept-specificity: DS concept component significantly ABOVE the remap controls
    concept_specific = bool(concept_specificity
                            and all(v["excl0"] and v["mean"] > 0 for v in concept_specificity.values()))

    verdict = {
        "control_gate_direct_loads_concept_not_codeword": gate_direct,
        "control_gate_repeated_loads_codeword_not_concept": gate_repeated,
        "controls_separate": bool(gate_direct and gate_repeated),
        "DS_loads_both_components": ds_both,
        "DS_concept_specific_vs_remap_controls": concept_specific,
        "concept_specificity": concept_specificity,
        # superposition SUPPORTED requires: DS carries BOTH components AND the concept component
        # is DS-specific (above benign/unrelated remaps that share the codeword component).
        "superposition_supported": bool(ds_both and concept_specific and gate_direct),
        "cos_axes_band_mean": round(float(np.mean([cos_axes[l] for l in band])), 4),
        "band": [lo_b, hi_b],
        "note_repeated_axis_n": repeated.get("n_prompts"),
        "note": ("codeword component is shared by all codeword/remap conditions (not DS-specific); "
                 "the DS-specific superposition signal is the CONCEPT component riding on top."),
    }

    out = {"axis_component": comp, "axis_position": pos,
           "axis_split": args.axis_split, "test_split": args.test_split,
           "concept_axis": CONCEPT_AX, "codeword_axis": CODEWORD_AX,
           "cos_axes_per_layer": [round(c, 4) for c in cos_axes],
           "per_condition": results, "verdict": verdict}
    out_dir = args.out_dir or args.reps_dir
    op = os.path.join(out_dir, "w3b_superposition.json")
    json.dump(out, open(op, "w"), indent=2)

    print(f"[w3b] axes {comp}/{pos}  build={args.axis_split} test={args.test_split}  "
          f"band L{lo_b}-{hi_b}  cos(axes)={verdict['cos_axes_band_mean']}")
    for cond in COND:
        if cond in results:
            c = results[cond]["concept_component_band"]; k = results[cond]["codeword_component_band"]
            print(f"  {cond:20s} n={results[cond]['n_prompts']:2d}  "
                  f"concept={c['mean']:+.3f}[{c['lo']:+.3f},{c['hi']:+.3f}]{'*' if c['excl0'] else ' '}  "
                  f"codeword={k['mean']:+.3f}[{k['lo']:+.3f},{k['hi']:+.3f}]{'*' if k['excl0'] else ' '}")
    for k, v in concept_specificity.items():
        print(f"  {k:22s} concept diff={v['mean']:+.3f}[{v['lo']:+.3f},{v['hi']:+.3f}]{'*' if v['excl0'] else ' '}")
    print(f"  VERDICT: controls_separate={verdict['controls_separate']} "
          f"DS_both={verdict['DS_loads_both_components']} "
          f"DS_concept_specific={verdict['DS_concept_specific_vs_remap_controls']} "
          f"superposition_supported={verdict['superposition_supported']}")
    print(f"[w3b] -> {op}")


if __name__ == "__main__":
    main()
