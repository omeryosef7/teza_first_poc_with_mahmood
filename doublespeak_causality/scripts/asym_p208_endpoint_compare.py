#!/usr/bin/env python
"""
ASYMMETRY SPRINT §20.8 — is the graded endpoint actually better than binary ASR here?

§20.8 as written (expand to n=300) is INFEASIBLE: the corpus ceiling is 179 and 148 are already
used (logged 2026-08-14 08:00). The proposed alternative is to drop binary ASR as the primary
endpoint in favour of the continuous/graded score. That is an argument, not evidence.

This tests it head-to-head on the SAME rows, for each of §7.5's six contrasts:
  * binary  -> exact McNemar + paired bootstrap CI on dASR
  * graded  -> Wilcoxon signed-rank + paired bootstrap CI on mean score difference
Both endpoints, same pairing, same items, same bootstrap. If the graded endpoint does not
produce materially tighter inference, option 3 is NOT supported and §20.8 needs a different
resolution -- that outcome is reported, not buried.

To compare CI widths across endpoints on one scale, the graded CI is also expressed in units of
the pooled per-item score SD (a standardized effect), since raw score units and ASR units are not
commensurable.

Scalars only; never reads model text.
"""
import argparse, json, sys
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon, binomtest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from aggregate_perprompt_asr import collect, _load_kw_refusal  # noqa: E402

JOBDIR = Path("doublespeak_causality/data/gcg/clearharm_llama_v3/perprompt_test")
EVAL_SEED = 42          # generation seed on every row; NOT the GCG optimization seed


def arm_scores(arm, seed, budget, kw):
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
        for r in collect(job["output_dir"], label, EVAL_SEED, kw):
            if r["task_id"] == job["task_id"] and r["score"] is not None:
                out[r["task_id"]] = float(r["score"])
    return out


def boot_ci(d, n_boot, rng):
    d = np.asarray(d, float)
    b = d[rng.integers(0, len(d), (n_boot, len(d)))].mean(axis=1)
    lo, hi = np.percentile(b, [5, 95])
    return float(lo), float(hi)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-boot", type=int, default=20000)
    ap.add_argument("--out", default="doublespeak_causality/outputs/asym_p208_endpoint_compare.json")
    args = ap.parse_args()
    kw = _load_kw_refusal()
    rng = np.random.default_rng(0)

    CONTRASTS = [("mechanism", "matched_random"), ("mechanism", "vanilla"),
                 ("matched_random", "vanilla")]
    rows = []
    print(f"{'budget':<7}{'contrast':<28}{'seed':>5}{'  BINARY dASR [90% CI]':>28}{'p':>8}"
          f"{'   GRADED dscore [90% CI]':>30}{'p':>8}")
    for budget, blab in (("s5", "low"), ("", "full")):
        for a_arm, b_arm in CONTRASTS:
            for seed in (42, 43, 44):
                A, B = arm_scores(a_arm, seed, budget, kw), arm_scores(b_arm, seed, budget, kw)
                if not A or not B:
                    continue
                ids = sorted(set(A) & set(B))
                if len(ids) < 20:
                    continue
                sa = np.array([A[i] for i in ids]); sb = np.array([B[i] for i in ids])
                ba = (sa >= 0.5).astype(float); bb = (sb >= 0.5).astype(float)

                db = ba - bb
                nb = int(((ba == 1) & (bb == 0)).sum()); nc = int(((ba == 0) & (bb == 1)).sum())
                p_bin = binomtest(nb, nb + nc, 0.5).pvalue if nb + nc else 1.0
                lo_b, hi_b = boot_ci(db, args.n_boot, rng)

                dg = sa - sb
                try:
                    p_gr = float(wilcoxon(sa, sb, zero_method="wilcox").pvalue)
                except ValueError:
                    p_gr = float("nan")
                lo_g, hi_g = boot_ci(dg, args.n_boot, rng)
                sd_pool = float(np.std(np.concatenate([sa, sb])))

                rows.append({"budget": blab, "contrast": f"{a_arm}-{b_arm}", "seed": seed,
                             "n": len(ids),
                             "binary_delta": float(db.mean()), "binary_ci90": [lo_b, hi_b],
                             "binary_width": hi_b - lo_b, "binary_p": float(p_bin),
                             "graded_delta": float(dg.mean()), "graded_ci90": [lo_g, hi_g],
                             "graded_width": hi_g - lo_g, "graded_p": p_gr,
                             "score_sd_pooled": sd_pool,
                             "graded_width_sd_units": (hi_g - lo_g) / sd_pool if sd_pool else None})
                print(f"{blab:<7}{a_arm+'-'+b_arm:<28}{seed:>5}"
                      f"  {db.mean():+.3f} [{lo_b:+.3f},{hi_b:+.3f}]{p_bin:>8.3f}"
                      f"   {dg.mean():+.3f} [{lo_g:+.3f},{hi_g:+.3f}]{p_gr:>8.3f}")

    Path(args.out).write_text(json.dumps({"n_boot": args.n_boot, "rows": rows}, indent=2))
    bw = np.array([r["binary_width"] for r in rows])
    gw = np.array([r["graded_width_sd_units"] for r in rows])
    bwsd = np.array([r["binary_width"] / np.sqrt(0.15 * 0.85) for r in rows])  # ASR in SD units
    nsig_b = sum(r["binary_p"] < 0.05 for r in rows)
    nsig_g = sum(r["graded_p"] < 0.05 for r in rows)
    print(f"\n  contrasts: {len(rows)}")
    print(f"  significant at .05 -- binary {nsig_b}/{len(rows)}   graded {nsig_g}/{len(rows)}")
    print(f"  mean CI width, standardized (SD units): binary {bwsd.mean():.3f}   graded {gw.mean():.3f}")
    print(f"  graded/binary width ratio = {gw.mean()/bwsd.mean():.3f} "
          f"({'graded tighter' if gw.mean() < bwsd.mean() else 'NO improvement -- option 3 unsupported'})")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
