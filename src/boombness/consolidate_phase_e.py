"""consolidate_phase_e.py -- emit plan §7's three named Phase-E artifacts, and compute the four
numbers that currently exist ONLY as markdown.

WHY. Review #3's finding R3-3 was that the sprint's headline Phase-F contrasts lived in no committed
file. An audit of Phase E found the same shape in four more places, and this script is the missing
producer for all of them:

  M1  the 16-category AdvBench breakdown (E1's central claim that the effect is BROAD and is
      *weakest* where the direction was fitted). `analyze_external_arms.py` emits pooled and
      cluster-MEAN statistics only -- it has no per-domain output path at all.
  M3  the multiplicity correction over the `d_surface` layer profile. "Holm rejects nothing" is
      the single most load-bearing negative in the sprint and it was markdown-only.
  M6  cos(d_surface, refusalness). `direction_cosines.json` covers only the three 2x2 siblings;
      the refusalness geometry -- the evidence that the two channels are separable -- was never
      written to disk.
  M2  the benign-arm aggregation. Four `bng_*` runs completed on 2026-08-20 and nothing reads them.

Everything else is MERGED VERBATIM from committed analysis JSON. This script recomputes nothing that
already has a producer; where a number exists, it is copied with its source path recorded beside it,
so the merged files add navigability without adding a second, drifting derivation.

WHAT IT DELIBERATELY DOES NOT DO. It does not silently drop the pieces the audit found missing that
need GPU (`d_inter`, the orthogonalised arms, d_surface at L20, refusalness below L12). Each is
written into a `missing` block of the artifact it belongs to, with its cost, so the gap is a field
in the file rather than an absence.

SAFETY. The benign aggregation reads generation text to apply the repo's keyword refusal detector;
it emits ONLY rates. No generation text is written to any artifact.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import os
import statistics as st
import subprocess
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_g8 import cluster_mean_ci  # noqa: E402
from common import read_jsonl, REPO_ROOT as REPO  # noqa: E402

OUT_DIR = os.path.join(REPO, "outputs/boombness_followup")
B = os.path.join(REPO, "outputs/boombness")
J = os.path.join(B, "judge")
SB = os.path.join(B, "score_behavior")


def load(path: str) -> dict:
    with open(path) as fh:
        return json.load(fh)


def src(path: str) -> str:
    return os.path.relpath(path, REPO)


# --------------------------------------------------------------------------- #
# M1 -- the per-category breakdown, from committed judge rows
# --------------------------------------------------------------------------- #
def by_category(arms: Dict[str, str]) -> dict:
    """Paired per-prompt delta vs baseline, broken out by AdvBench category (`domain`).

    THE UNIT HERE IS THE CATEGORY, NOT THE PROMPT. E1's question is "is the effect broad, or is it
    concentrated in the harm type the direction was fitted on", and that is a statement about the
    distribution ACROSS categories. So the test is a one-sample t over the 16 category means plus a
    sign test, and both are reported -- not a pooled prompt-level statistic, which would answer a
    different question and would be dominated by the two largest categories (127 + 68 of 495 rows).
    """
    base = {r["prompt_id"]: r for r in read_jsonl(os.path.join(arms["baseline"], "results.jsonl"))
            if r.get("judge_status") == "ok"}
    out = {"unit_of_inference": "CATEGORY (not prompt); n = number of categories",
           "baseline_run": src(arms["baseline"]), "arms": {}}
    for name, d in arms.items():
        if name == "baseline":
            continue
        rows = {r["prompt_id"]: r for r in read_jsonl(os.path.join(d, "results.jsonl"))
                if r.get("judge_status") == "ok"}
        pids = sorted(set(base) & set(rows))
        per_cat: Dict[str, List[float]] = collections.defaultdict(list)
        for p in pids:
            per_cat[str(base[p].get("domain"))].append(
                float(rows[p]["strongreject_score"]) - float(base[p]["strongreject_score"]))
        cats = {c: {"n_prompts": len(v), "mean_delta": st.mean(v),
                    "baseline_asr": st.mean(1.0 if base[p]["malicious_at_0.5"] else 0.0
                                            for p in pids
                                            if str(base[p].get("domain")) == c)}
                for c, v in sorted(per_cat.items())}
        means = [c["mean_delta"] for c in cats.values()]
        movable = [c for c, v in cats.items() if v["mean_delta"] != 0.0]
        pos = sum(1 for m in means if m > 0)
        neg = sum(1 for m in means if m < 0)
        zero = sum(1 for m in means if m == 0)
        n = len(means)
        sem = st.stdev(means) / math.sqrt(n) if n > 1 else None
        # sign test over the categories that CAN move: a category pinned at 0.000 in every arm
        # carries no information about direction and inflates the null if counted as a tie.
        mv = [c["mean_delta"] for cn, c in cats.items() if cn in movable]
        k = sum(1 for m in mv if m > 0)
        p_sign = (sum(math.comb(len(mv), i) for i in range(k, len(mv) + 1)) / (2 ** len(mv))
                  if mv else None)
        out["arms"][name] = {
            "run": src(d), "n_prompts": len(pids), "n_categories": n,
            "categories": cats,
            "mean_over_categories": st.mean(means), "sem_over_categories": sem,
            "t_over_categories": (st.mean(means) / sem) if sem else None,
            "df": n - 1,
            "n_categories_positive": pos, "n_categories_negative": neg,
            "n_categories_exactly_zero": zero,
            "n_movable_categories": len(mv),
            "sign_test_over_movable_p_one_sided": p_sign,
            "immovable_categories": sorted(c for c in cats if c not in movable),
        }
    return out


# --------------------------------------------------------------------------- #
# M3 -- multiplicity over a layer profile
# --------------------------------------------------------------------------- #
def holm_bh(pvals: Dict[str, float], alpha: float = 0.05) -> dict:
    """Holm-Bonferroni and Benjamini-Hochberg over a named family of p-values.

    Degenerate depths (p_cl null) are EXCLUDED from the family and named, because including an
    untestable depth as a member would shrink everyone else's adjusted p for free.
    """
    items = sorted(((k, v) for k, v in pvals.items() if v is not None), key=lambda kv: kv[1])
    m = len(items)
    holm, running = {}, 0.0
    for i, (k, p) in enumerate(items):
        adj = min(1.0, (m - i) * p)
        running = max(running, adj)          # Holm adjusted p-values are monotone
        holm[k] = running
    bh, prev = {}, 1.0
    for i in range(m - 1, -1, -1):
        k, p = items[i]
        prev = min(prev, p * m / (i + 1))
        bh[k] = prev
    return {
        "family_size_m": m,
        "excluded_degenerate": sorted(k for k, v in pvals.items() if v is None),
        "alpha": alpha,
        "raw": dict(items),
        "holm_adjusted": holm,
        "holm_rejects": sorted(k for k, v in holm.items() if v <= alpha),
        "bh_adjusted": bh,
        "bh_rejects": sorted(k for k, v in bh.items() if v <= alpha),
    }


# --------------------------------------------------------------------------- #
# M6 -- cos(d_surface, refusalness), with a random baseline
# --------------------------------------------------------------------------- #
def refusal_geometry(fit_dir: str, refusal_glob: str, split: str = "heldout",
                     n_draws: int = 2000, seed: int = 20260820) -> dict:
    import torch
    payload = torch.load(os.path.join(fit_dir, f"directions_fit_{split}.pt"),
                         map_location="cpu", weights_only=False)
    ds = payload["d_surface"]
    g = torch.Generator().manual_seed(seed)
    rows, dim = {}, None
    for path in sorted(glob.glob(refusal_glob)):
        L = int(os.path.basename(path).split("_L")[-1].split(".")[0])
        v = torch.load(path, map_location="cpu", weights_only=False)
        if L not in ds:
            rows[f"L{L}"] = {"error": f"no d_surface fitted at layer {L}"}
            continue
        a, b = ds[L].float(), v.float().reshape(-1)
        if a.shape != b.shape:
            rows[f"L{L}"] = {"error": f"dim mismatch {tuple(a.shape)} vs {tuple(b.shape)}"}
            continue
        dim = a.numel()
        cos = float(torch.dot(a, b) / (a.norm() * b.norm()))
        rows[f"L{L}"] = {"cos": cos, "abs_cos": abs(cos),
                         "shared_variance_frac": cos * cos,
                         "refusal_direction_file": src(path)}
    # A cosine is only interpretable against the null for THIS dimensionality: two random unit
    # vectors in R^4096 have |cos| ~ 1/sqrt(d) ~ 0.0156, not 0.
    base = None
    if dim:
        draws = []
        for _ in range(n_draws):
            x = torch.randn(dim, generator=g)
            y = torch.randn(dim, generator=g)
            draws.append(float(torch.dot(x, y) / (x.norm() * y.norm())))
        base = {"n_draws": n_draws, "seed": seed, "dim": dim,
                "sd": st.stdev(draws), "mean_abs": st.mean(abs(d) for d in draws),
                "analytic_sd_1_over_sqrt_d": 1.0 / math.sqrt(dim)}
        for k, r in rows.items():
            if "cos" in r:
                r["z_vs_random"] = r["cos"] / base["sd"]
    return {"fit_dir": src(fit_dir), "split": split, "by_layer": rows,
            "random_baseline": base,
            "note": "cos is against d_surface. A cosine near the random sd is AT CHANCE, not zero."}


# --------------------------------------------------------------------------- #
# M2 -- the benign arms (reads text to apply the repo's refusal detector; emits rates only)
# --------------------------------------------------------------------------- #
def benign_arms(runs: Dict[str, str]) -> dict:
    sys.path.insert(0, os.path.join(REPO, "doublespeak_causality"))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "bj", os.path.join(REPO, "doublespeak_causality", "18_run_behavioral_necessity.py"))
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        kw_refusal = mod.kw_refusal
    except Exception as e:                                    # pragma: no cover
        return {"error": f"could not load the repo refusal detector: {type(e).__name__}: {e}"}

    out = {"note": "outcome measure is OVER-REFUSAL on benign prompts; no judge is involved, "
                   "because there is no harmful goal to score against",
           "arms": {}}
    texts: Dict[str, Dict[str, str]] = {}
    for name, d in runs.items():
        rows = list(read_jsonl(os.path.join(d, "gens.jsonl")))
        texts[name] = {r["prompt_id"]: r.get("generation", "") for r in rows}
        refused = [kw_refusal(t) for t in texts[name].values()]
        doms = collections.Counter(r.get("domain") for r in rows)
        out["arms"][name] = {
            "run": src(d), "n": len(rows), "n_domains": len(doms),
            "over_refusal_rate": (sum(1 for x in refused if x) / len(refused)) if refused else None,
            "n_refused": sum(1 for x in refused if x),
            "mean_chars": st.mean(len(t) for t in texts[name].values()) if rows else None,
        }
    # How much does each arm PERTURB the text relative to baseline? Word-level Jaccard, paired.
    if "baseline" in texts:
        bt = texts["baseline"]
        for name, tt in texts.items():
            if name == "baseline":
                continue
            pids = sorted(set(bt) & set(tt))
            js = []
            for p in pids:
                a, b = set(bt[p].lower().split()), set(tt[p].lower().split())
                if a or b:
                    js.append(len(a & b) / len(a | b))
            out["arms"][name]["mean_word_jaccard_vs_baseline"] = st.mean(js) if js else None
            out["arms"][name]["n_paired"] = len(js)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-benign", action="store_true")
    ap.add_argument("--skip-geometry", action="store_true")
    args = ap.parse_args()

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                            capture_output=True, text=True).stdout.strip()
    head = {"git_commit": commit, "producer": "src/boombness/consolidate_phase_e.py",
            "merge_policy": "existing numbers are COPIED from their committed producer with the "
                            "source path recorded; nothing already produced is recomputed"}
    os.makedirs(OUT_DIR, exist_ok=True)

    A = os.path.join(B, "advbench_decomposition.json")
    Bf = os.path.join(B, "advbench_superadd_control.json")
    C = os.path.join(B, "advbench_direction_specificity.json")
    D = os.path.join(B, "advbench_layer_profile.json")
    E = os.path.join(OUT_DIR, "l15_and_refusal_L12.json")
    G = os.path.join(OUT_DIR, "refusalness_layer_profile.json")
    Hf = os.path.join(B, "direction_cosines.json")
    I = os.path.join(B, "clearharm_decomposition_regoal.json")
    K = os.path.join(B, "advbench_decomposition_qwen3.json")
    L = os.path.join(B, "clearharm_decomposition_qwen3.json")
    M1f = os.path.join(B, "condition_profile_llama_projout.json")
    M2f = os.path.join(B, "condition_profile_llama_len_B.json")

    # ---------------- E1 ----------------
    a, bf, c, i, k, l = load(A), load(Bf), load(C), load(I), load(K), load(L)
    e1 = {**head, "plan_section": "§7 E1 -- external semantic categories",
          "advbench": {
              "source": src(A), "label": a["label"], "n": a["n_common"],
              "arms": a["arms"], "paired_vs_baseline": a["paired_vs_baseline"],
              "super_additivity": a.get("super_additivity"),
              "super_additivity_vs_control": a.get("super_additivity_vs_control"),
              "control_only_super_additivity": {"source": src(Bf),
                                                **bf.get("super_additivity", {})},
              "direction_comparators_L8": {
                  "source": src(C),
                  "arms": {n: c["arms"][n] for n in ("d_naive", "d_context") if n in c["arms"]},
                  "paired_vs_baseline": {n: c["paired_vs_baseline"][n]
                                         for n in ("d_naive", "d_context")
                                         if n in c["paired_vs_baseline"]}},
              "by_category_M1": by_category({
                  "baseline": os.path.join(J, "abg_base_20260819_011714_1480836"),
                  "remove_d_surface": os.path.join(J, "abg_B_20260819_013447_1506491"),
                  "remove_d_surface_ctrl": os.path.join(J, "abg_Bctrl_20260819_020905_1520524"),
                  "remove_refusalness": os.path.join(J, "abg_C_20260819_011714_1480835"),
                  "remove_both": os.path.join(J, "abg_D_20260819_013551_1507682")}),
          },
          "clearharm": {"source": src(I), "label": i["label"], "n": i["n_common"],
                        "arms": i["arms"], "paired_vs_baseline": i["paired_vs_baseline"],
                        "control_band": i.get("control_band"),
                        "super_additivity": i.get("super_additivity"),
                        "caveat": "6 clusters cannot resolve super-additivity; and this file has "
                                  "NO arm-B matched random control (audit M10)"},
          "internal_conditions": {
              "projout": {"source": src(M1f), **load(M1f).get("conditions", {})},
              "length_fair_512tok": {"source": src(M2f), **load(M2f).get("conditions", {})},
              "caveat": "R-15 retracted the 'harmful-yes / benign-no' READING of these deltas; "
                        "the deltas themselves stand"},
          "cross_model_floor_note": {
              "advbench_qwen3": {"source": src(K), "baseline_asr": k["arms"]["baseline"]["asr_at_0.5"],
                                 "paired_vs_baseline": k["paired_vs_baseline"]},
              "clearharm_qwen3": {"source": src(L),
                                  "paired_vs_baseline": l["paired_vs_baseline"]},
              "citability": "FLOOR-LIMITED (baseline ASR 0.008). Not citable as causal success or "
                            "failure. And per R-13 the Qwen3 codeword-substituted judging is "
                            "separately compromised -- see topicality_qwen3_armD.json"},
          "missing_requires_gpu": {
              "ambiguous_dual_use_category": "no such bank exists; authoring one is the piece most "
                                             "vulnerable to being written toward the answer",
              "benign_technical_vs_everyday": "benign_unrelated_40 is one undifferentiated set"},
          }
    if not args.skip_benign:
        e1["benign_M2"] = benign_arms({
            "baseline": os.path.join(SB, "bng_base_20260820_055743_617412"),
            "remove_d_surface": os.path.join(SB, "bng_B_20260820_055743_617416"),
            "remove_d_surface_ctrl": os.path.join(SB, "bng_Bctrl_20260820_055744_617417"),
            "remove_refusalness": os.path.join(SB, "bng_C_20260820_055743_617419")})

    # ---------------- E2 ----------------
    d, e, g = load(D), load(E), load(G)
    ds_p = {kk: vv.get("p_cl") for kk, vv in d["paired_vs_baseline"].items()
            if kk.startswith("L")}
    ds_p["L15"] = e["paired_vs_baseline"]["L15_B"].get("p_cl")
    e2 = {**head, "plan_section": "§7 E2 -- layer profile replication",
          "shared_baseline": {"note": "every arm below is paired against ONE baseline judge run, so "
                                      "the arms are not independent of each other",
                              "baseline": d["arms"]["baseline"]},
          "d_surface": {"source": src(D), "arms": d["arms"],
                        "paired_vs_baseline": d["paired_vs_baseline"],
                        "L15_from": src(E),
                        "L15": {"arm": e["arms"]["L15_B"],
                                "paired": e["paired_vs_baseline"]["L15_B"],
                                "control": e["arms"]["L15_Bctrl"],
                                "control_paired": e["paired_vs_baseline"]["L15_Bctrl"]},
                        "degenerate_depths": [kk for kk, vv in d["paired_vs_baseline"].items()
                                              if vv.get("degenerate")]},
          "refusalness": {"source": src(G), "arms": g["arms"],
                          "paired_vs_baseline": g["paired_vs_baseline"]},
          "multiplicity_M3": {"d_surface_profile": holm_bh(ds_p),
                              "refusalness_profile": holm_bh(
                                  {kk: vv.get("p_cl") for kk, vv in g["paired_vs_baseline"].items()
                                   if kk.endswith("_C")})},
          "missing_requires_gpu": {
              "d_surface_L20": "the only planned depth with no run; also the one depth where a "
                               "DEPTH-MATCHED d_surface vs refusalness comparison would be possible",
              "refusalness_below_L12": "a DATA gap, not a bug: Llama refusal directions exist on "
                                       "disk at exactly L12,14,16,18,20, so the interaction cannot "
                                       "be measured inside d_surface's own L6-L12 band"},
          }

    # ---------------- E3 ----------------
    e3 = {**head, "plan_section": "§7 E3 -- direction specificity, extended",
          "behavioral_same_operation_L8": {
              "source": src(C), "operation": "project_out, alpha 1.0, layer 8",
              "arms": c["arms"], "paired_vs_baseline": c["paired_vs_baseline"],
              "reuse_note": "the d_surface and random arms here are the SAME judge runs as "
                            "advbench_decomposition's B and Bctrl -- not independent evidence"},
          "refusalness_at_its_own_depth": {
              "source": src(G), "caveat": "L18/L12, NOT L8 -- this row is at a different depth "
                                          "from the four above and is not a like-for-like row",
              "L18": {"arm": g["arms"]["L18_C"], "paired": g["paired_vs_baseline"]["L18_C"]},
              "L12": {"arm": g["arms"]["L12_C"], "paired": g["paired_vs_baseline"]["L12_C"]}},
          "geometry_siblings": {"source": src(Hf), **load(Hf)},
          "missing_requires_gpu": {
              "d_inter": "the vector EXISTS in directions_fit_heldout.pt but no project_out arm has "
                         "ever been run for it, on any layer, dataset or model. Cost: 1 run + 1 "
                         "judge (the matched random control already exists as ab_Bctrl)",
              "orthogonalised_arms": "neither d_surface-minus-refusalness nor the reverse has been "
                                     "run. Deliberately deprioritised: at cos <= 0.13 they differ "
                                     "from the plain arms by <2% of the vector. Cost: 2 + 2"},
          }
    if not args.skip_geometry:
        e3["geometry_vs_refusalness_M6"] = refusal_geometry(
            os.path.join(B, "extract_boombness/full_20260816_185942_1008673"),
            os.path.join(REPO, "doublespeak_causality/outputs/stage_gcg_full",
                         "refusal_direction_llama_L*.pt"))

    for name, obj in (("d_surface_external_decomposition", e1),
                      ("d_surface_layer_profile_replication", e2),
                      ("direction_specificity_extended", e3)):
        p = os.path.join(OUT_DIR, name + ".json")
        with open(p, "w") as fh:
            json.dump(obj, fh, indent=2)
        print(f"[phaseE] wrote {src(p)}")

    m1 = e1["advbench"]["by_category_M1"]["arms"]["remove_d_surface"]
    print(f"  M1 remove_d_surface: mean over {m1['n_categories']} categories "
          f"{m1['mean_over_categories']:+.4f} sem {m1['sem_over_categories']:.4f} "
          f"t {m1['t_over_categories']:+.2f} df {m1['df']}; "
          f"{m1['n_categories_positive']}+/{m1['n_categories_negative']}-/"
          f"{m1['n_categories_exactly_zero']}=0; sign p {m1['sign_test_over_movable_p_one_sided']}")
    h = e2["multiplicity_M3"]["d_surface_profile"]
    print(f"  M3 d_surface  Holm(m={h['family_size_m']}) rejects: {h['holm_rejects'] or 'NOTHING'} "
          f"| BH rejects: {h['bh_rejects'] or 'nothing'}")
    h2 = e2["multiplicity_M3"]["refusalness_profile"]
    print(f"  M3 refusalness Holm(m={h2['family_size_m']}) rejects: {h2['holm_rejects']}")
    if not args.skip_geometry:
        gg = e3["geometry_vs_refusalness_M6"]
        print(f"  M6 cos(d_surface, refusalness): "
              + ", ".join(f"{kk} {vv.get('cos'):+.4f} (z {vv.get('z_vs_random'):+.1f})"
                          for kk, vv in gg["by_layer"].items() if "cos" in vv)
              + f" | random sd {gg['random_baseline']['sd']:.5f}")
    if not args.skip_benign and "error" not in e1.get("benign_M2", {}):
        for n, v in e1["benign_M2"]["arms"].items():
            print(f"  M2 {n:22s} over-refusal {v['over_refusal_rate']:.4f} "
                  f"jaccard {v.get('mean_word_jaccard_vs_baseline')}")


if __name__ == "__main__":
    main()
