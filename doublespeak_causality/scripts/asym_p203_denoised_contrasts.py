#!/usr/bin/env python
"""
ASYMMETRY SPRINT §20.3 payoff — re-run §7.5's contrasts on a JUDGE-DENOISED endpoint.

§20.3 established (2026-08-14 10:45):
  * rows at score 0.0/1.0 are effectively deterministic -- 0/40 flipped over M=5, SD 0.0023;
  * only the 4.65 % intermediate band is unstable (33/93 flipped);
  * judge noise is 1.8-7.5 % of a single-pass arm ASR's variance.

I asserted there that judge noise is "cheaply removable by majority-vote over M=5 on the band".
This does it, rather than leaving it as a claim. The M=5 replicate run already covers EVERY band
row in the corpus, so a fully denoised endpoint is constructible with no new API calls:

    denoised(row) = majority-vote success over 5 replicates   if row is in the band
                    single-pass success                        otherwise (validated deterministic)

Then re-run all 18 §7.5 contrasts and compare against the single-pass result. Since judge noise is
a small share of variance, the expectation is that NOTHING material changes -- and confirming that
is the point: it converts "judge noise does not drive our conclusions" from an argument into a
demonstration. Any conclusion that DOES flip is reported loudly.

Scalars only; never reads model text.
"""
import argparse, json, sys
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aggregate_perprompt_asr import collect, _load_kw_refusal  # noqa: E402

JOBDIR = Path("doublespeak_causality/data/gcg/clearharm_llama_v3/perprompt_test")
EVAL_SEED = 42
STEP = 0.125


def load_replicates(path, band_steps=2.0):
    """-> {(output_dir,row_key,task_id,condition_label): majority_success}"""
    d = json.load(open(path))
    out = {}
    for r in d["band_rows"]:
        succ = [s >= 0.5 for s in r["scores"]]
        out[r["key"]] = sum(succ) * 2 > len(succ)
    return out, d


def arm_rows(arm, seed, budget, kw):
    tag = f"_{budget}" if budget else ""
    jl = JOBDIR / f"joblist_asym_p75_{arm}{tag}_seed{seed}.jsonl"
    if not jl.exists():
        return None
    label = f"asym_p75_{arm}{tag}"
    out = {}
    for line in open(jl, encoding="utf-8"):
        if not line.strip():
            continue
        job = json.loads(line)
        od = job["output_dir"]
        p = Path(od) / "FREE_GENERATION_RESULTS.jsonl"
        if not p.exists():
            continue
        for ln in open(p, encoding="utf-8"):
            r = json.loads(ln)
            if r.get("condition_label") != label or r.get("seed") != EVAL_SEED:
                continue
            if r.get("task_id") != job["task_id"]:
                continue
            s = r.get("strongreject_score")
            if s is None:
                continue
            out[r["task_id"]] = {
                "score": float(s),
                "key": "|".join(str(x) for x in (od, r.get("row_key"), r.get("task_id"), label)),
            }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicates",
                    default="doublespeak_causality/outputs/asym_p203_judge_replicates.json")
    ap.add_argument("--out",
                    default="doublespeak_causality/outputs/asym_p203_denoised_contrasts.json")
    ap.add_argument("--band-steps", type=float, default=2.0)
    args = ap.parse_args()

    maj, repdata = load_replicates(args.replicates, args.band_steps)
    print(f"[repl] majority votes available for {len(maj)} band rows "
          f"(pool band was {repdata['pool_band']})")
    kw = _load_kw_refusal()

    CONTRASTS = [("mechanism", "matched_random"), ("mechanism", "vanilla"),
                 ("matched_random", "vanilla")]
    rows, n_used, n_band_seen, n_band_missing = [], 0, 0, 0
    print(f"\n{'budget':<7}{'contrast':<28}{'seed':>5}{'single dASR':>13}{'denoised dASR':>15}"
          f"{'  changed':>10}{'p_single':>10}{'p_denoise':>11}")
    for budget, blab in (("s5", "low"), ("", "full")):
        for a_arm, b_arm in CONTRASTS:
            for seed in (42, 43, 44):
                A, B = arm_rows(a_arm, seed, budget, kw), arm_rows(b_arm, seed, budget, kw)
                if not A or not B:
                    continue
                ids = sorted(set(A) & set(B))
                if len(ids) < 20:
                    continue

                def endpoint(D, tid, denoise):
                    r = D[tid]
                    in_band = abs(r["score"] - 0.5) <= args.band_steps * STEP + 1e-9
                    if denoise and in_band:
                        nonlocal n_band_seen, n_band_missing
                        n_band_seen += 1
                        if r["key"] in maj:
                            return float(maj[r["key"]])
                        n_band_missing += 1        # fall back, but count it -- never silent
                    return float(r["score"] >= 0.5)

                res = {}
                for tag, dn in (("single", False), ("denoised", True)):
                    ba = np.array([endpoint(A, t, dn) for t in ids])
                    bb = np.array([endpoint(B, t, dn) for t in ids])
                    nb = int(((ba == 1) & (bb == 0)).sum()); nc = int(((ba == 0) & (bb == 1)).sum())
                    res[tag] = {"delta": float((ba - bb).mean()),
                                "p": float(binomtest(nb, nb + nc, 0.5).pvalue) if nb + nc else 1.0}
                n_used += 1
                changed = abs(res["single"]["delta"] - res["denoised"]["delta"]) > 1e-9
                sig_flip = (res["single"]["p"] < 0.05) != (res["denoised"]["p"] < 0.05)
                rows.append({"budget": blab, "contrast": f"{a_arm}-{b_arm}", "seed": seed,
                             "n": len(ids), **{f"{k}_{m}": res[k][m] for k in res for m in res[k]},
                             "delta_changed": changed, "significance_flipped": sig_flip})
                print(f"{blab:<7}{a_arm+'-'+b_arm:<28}{seed:>5}"
                      f"{res['single']['delta']:>+13.4f}{res['denoised']['delta']:>+15.4f}"
                      f"{'  YES' if changed else '   no':>10}"
                      f"{res['single']['p']:>10.3f}{res['denoised']['p']:>11.3f}")

    nch = sum(r["delta_changed"] for r in rows)
    nfl = sum(r["significance_flipped"] for r in rows)
    print(f"\n  contrasts: {n_used}")
    print(f"  band rows encountered: {n_band_seen}  (majority vote missing for {n_band_missing})")
    print(f"  contrasts whose dASR CHANGED at all: {nch}/{n_used}")
    print(f"  contrasts whose SIGNIFICANCE flipped: {nfl}/{n_used}")
    print(f"  significant at .05 -- single {sum(r['single_p']<0.05 for r in rows)}/{n_used}"
          f"   denoised {sum(r['denoised_p']<0.05 for r in rows)}/{n_used}")
    if nfl:
        print("  *** A CONCLUSION FLIPPED under denoising -- investigate before citing either ***")
    Path(args.out).write_text(json.dumps(
        {"band_steps": args.band_steps, "n_band_rows_denoised": n_band_seen,
         "n_band_majority_missing": n_band_missing, "rows": rows}, indent=2))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
