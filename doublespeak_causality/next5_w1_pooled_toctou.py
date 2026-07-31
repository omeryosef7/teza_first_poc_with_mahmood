"""W1 pooled mid-vs-late TOCTOU interaction across the two MID-dominant pairs (grenade+chlorine).
Scalars only: reads the `cat` label field per row, never any completion text. Tests the
GENERALIZED T3 prediction: pairs whose refusal check localizes at MID show a positive
mid-vs-late behavioral compliance-flip interaction. Pooling -> n=80 for tighter CIs.
"""
import os, sys, json, glob, importlib.util
HERE = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/doublespeak_causality"
sys.path.insert(0, HERE)
import stats as st

spec = importlib.util.spec_from_file_location("t45", os.path.join(HERE, "45_toctou_factorial.py"))
t45 = importlib.util.module_from_spec(spec); spec.loader.exec_module(t45)

DIRS = {
    "grenade":  sorted(glob.glob(os.path.join(HERE, "outputs/toctou_*695290")))[-1],
    "chlorine": sorted(glob.glob(os.path.join(HERE, "outputs/toctou_*695291")))[-1],
}

def per_item_mid_late(rows, oc="MALICIOUS"):
    """Return the list of per-item mid-late diff-of-diffs interaction values."""
    main = [r for r in rows if r.get("arm", "main") == "main"]
    idx = {(r["pid"], r["cell"], r.get("timing")): r for r in main}
    pids = sorted({r["pid"] for r in main})
    def get(pid, cell, timing):
        r = idx.get((pid, cell, timing))
        return None if r is None else t45._indicator(r, oc)
    vals = []
    for p in pids:
        cells = [("A", None), ("C", None), ("B", "mid"), ("D", "mid"), ("B", "late"), ("D", "late")]
        gv = {(c, tt): get(p, c, tt) for c, tt in cells}
        if any(v is None for v in gv.values()):
            continue
        a, c = gv[("A", None)], gv[("C", None)]
        bm, dm = gv[("B", "mid")], gv[("D", "mid")]
        bl, dl = gv[("B", "late")], gv[("D", "late")]
        vals.append(((dm - c) - (bm - a)) - ((dl - c) - (bl - a)))
    return vals

pooled = []
per_pair = {}
for name, d in DIRS.items():
    rows = [json.loads(l) for l in open(os.path.join(d, "toctou_raw.jsonl"))]
    v = per_item_mid_late(rows)
    per_pair[name] = v
    pooled += v
    ci = st.paired_bootstrap_ci(v, [0.0] * len(v), n_boot=10000, seed=0)
    pp = st.permutation_test_paired(v, [0.0] * len(v), n_perm=5000, seed=0)["p"]
    print(f"{name:9s} mid-late INTERACTION: eff={ci['mean_diff']:+.4f} "
          f"[{ci['lo']:+.4f},{ci['hi']:+.4f}] n={ci['n']} p_raw={pp:.4f} reliable={ci['ci_reliable']}")

ci = st.paired_bootstrap_ci(pooled, [0.0] * len(pooled), n_boot=10000, seed=0)
pp = st.permutation_test_paired(pooled, [0.0] * len(pooled), n_perm=5000, seed=0)["p"]
print(f"{'POOLED':9s} mid-late INTERACTION: eff={ci['mean_diff']:+.4f} "
      f"[{ci['lo']:+.4f},{ci['hi']:+.4f}] n={ci['n']} p_raw={pp:.4f} reliable={ci['ci_reliable']}")
print(f"  (pooled tests the generalized prediction: MID-dominant pairs show a positive "
      f"mid-vs-late behavioral TOCTOU interaction)")

# Cluster-robust (stratified) bootstrap: resample items WITHIN each pair, so pair-level
# structure can't inflate significance. Conservative counterpart to the iid pooled CI above.
import numpy as np
rng = np.random.default_rng(0)
arrs = [np.array(per_pair[k], float) for k in ("grenade", "chlorine")]
boot = []
for _ in range(20000):
    m = np.mean([a[rng.integers(0, len(a), len(a))].mean() for a in arrs])
    boot.append(m)
boot = np.sort(boot)
lo, hi = boot[int(0.025 * len(boot))], boot[int(0.975 * len(boot))]
obs = np.mean([a.mean() for a in arrs])
print(f"{'STRATIFIED':9s} (within-pair resample, equal pair weight): eff={obs:+.4f} "
      f"[{lo:+.4f},{hi:+.4f}] excludes_0={bool(lo > 0 or hi < 0)}")
