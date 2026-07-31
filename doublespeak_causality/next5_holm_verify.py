"""
next5_holm_verify.py — NEXT5 verification: ONE Holm-Bonferroni family across ALL new inferential
claims of the sprint, per the plan's verification section. Scalars only.

Family (the load-bearing NEW null-tests):
  W1   pooled mid-late TOCTOU interaction (grenade+chlorine)         vs 0   (paired permutation)
  W3b  DS concept component MINUS BENIGN_REMAP  concept component     >0    (two-sample permutation)
  W3b  DS concept component MINUS UNRELATED_TARGET concept component  >0    (two-sample permutation)

(W2 DeepSeek is not a claim — reliable=False; W4/W5 are validated/negative, no positive null-test.)

Run (CPU): python next5_holm_verify.py
"""
import os, sys, json, glob
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import stats as st

# ---- W1 pooled mid-late interaction (reuse the reducer logic) ----
import importlib.util
spec = importlib.util.spec_from_file_location("t45", os.path.join(HERE, "45_toctou_factorial.py"))
t45 = importlib.util.module_from_spec(spec); spec.loader.exec_module(t45)

def w1_pooled_vals():
    vals = []
    for tag in ("695290", "695291"):
        d = sorted(glob.glob(os.path.join(HERE, f"outputs/toctou_*{tag}")))[-1]
        rows = [json.loads(l) for l in open(os.path.join(d, "toctou_raw.jsonl"))]
        main = [r for r in rows if r.get("arm", "main") == "main"]
        idx = {(r["pid"], r["cell"], r.get("timing")): r for r in main}
        pids = sorted({r["pid"] for r in main})
        def get(p, c, t):
            r = idx.get((p, c, t)); return None if r is None else t45._indicator(r, "MALICIOUS")
        for p in pids:
            cells = {(c, tt): get(p, c, tt) for c, tt in
                     [("A", None), ("C", None), ("B", "mid"), ("D", "mid"), ("B", "late"), ("D", "late")]}
            if any(v is None for v in cells.values()):
                continue
            a, c = cells[("A", None)], cells[("C", None)]
            bm, dm = cells[("B", "mid")], cells[("D", "mid")]
            bl, dl = cells[("B", "late")], cells[("D", "late")]
            vals.append(((dm - c) - (bm - a)) - ((dl - c) - (bl - a)))
    return vals

# ---- W3b concept components per condition (reuse w3b projection) ----
def w3b_concept_components():
    rd = sorted(glob.glob(os.path.join(HERE, "outputs/pair_reps_Llama-3.1-8B-Instruct_*_694691")))[-1]
    dd = sorted(glob.glob(os.path.join(HERE, "outputs/pair_directions_*_694691")))[-1]
    dirs = np.load(os.path.join(dd, "directions.npz"), allow_pickle=True)
    d_conc = dirs["d_Direct|dev|resid_post|codeword_last"].astype(np.float64)
    d_conc = d_conc / (np.linalg.norm(d_conc, axis=-1, keepdims=True) + 1e-8)
    means = np.load(os.path.join(rd, "means.npz"), allow_pickle=True)
    mu = means["NEUTRAL_CODEWORD|dev|resid_post|codeword_last"].astype(np.float64)
    summ = json.load(open(os.path.join(rd, "reps_summary.json")))
    pp = np.load(os.path.join(rd, "per_prompt.npz"), allow_pickle=True)["resid_post_codeword"].astype(np.float64)
    band = list(range(12, 25))
    out = {}
    for cond in ("DOUBLESPEAK", "BENIGN_REMAP", "UNRELATED_TARGET"):
        idx = [i for i, r in enumerate(summ["rows"]) if r.get("split") == "heldout" and r["condition"] == cond]
        R = pp[idx] - mu[None, :, :]
        comp = np.einsum("nlh,lh->nl", R, d_conc)[:, band].mean(axis=1)
        out[cond] = comp
    return out

def two_sample_perm_p(a, b, n_perm=20000, seed=0):
    a = np.asarray(a, float); b = np.asarray(b, float)
    obs = a.mean() - b.mean()
    pool = np.concatenate([a, b]); na = len(a)
    rng = np.random.default_rng(seed)
    cnt = 0
    for _ in range(n_perm):
        rng.shuffle(pool)
        if (pool[:na].mean() - pool[na:].mean()) >= obs:   # one-sided (DS > control)
            cnt += 1
    return (cnt + 1) / (n_perm + 1), float(obs)

# ---- assemble family ----
w1 = w1_pooled_vals()
p_w1 = st.permutation_test_paired(w1, [0.0] * len(w1), n_perm=20000, seed=0)["p"]
comp = w3b_concept_components()
p_b, eff_b = two_sample_perm_p(comp["DOUBLESPEAK"], comp["BENIGN_REMAP"])
p_u, eff_u = two_sample_perm_p(comp["DOUBLESPEAK"], comp["UNRELATED_TARGET"])

fam = [("W1_pooled_mid_late_interaction", p_w1),
       ("W3b_DS_minus_BENIGN_concept", p_b),
       ("W3b_DS_minus_UNRELATED_concept", p_u)]
names = [f[0] for f in fam]
praw = [f[1] for f in fam]
padj = st.holm_bonferroni(praw)

print("=== NEXT5 single Holm family across all new inferential claims ===")
print(f"  W1 pooled mid-late: n={len(w1)} mean={np.mean(w1):+.4f}")
print(f"  W3b DS-BENIGN concept diff={eff_b:+.4f} ; DS-UNRELATED diff={eff_u:+.4f}")
print(f"{'claim':38s} {'p_raw':>10s} {'p_holm':>10s}  survives(<0.05)")
allsurv = True
for (nm, _), pr, pa in zip(fam, praw, padj):
    surv = pa < 0.05; allsurv &= surv
    print(f"{nm:38s} {pr:10.5f} {pa:10.5f}  {surv}")
print(f"\nALL survive Holm at 0.05: {allsurv}")
out = {"family": [{"claim": nm, "p_raw": round(pr, 6), "p_holm": round(pa, 6), "survives": bool(pa < 0.05)}
                  for (nm, _), pr, pa in zip(fam, praw, padj)],
       "all_survive": bool(allsurv),
       "w1_n": len(w1), "w1_mean": round(float(np.mean(w1)), 5),
       "w3b_ds_minus_benign": round(eff_b, 5), "w3b_ds_minus_unrelated": round(eff_u, 5)}
json.dump(out, open(os.path.join(HERE, "outputs", "next5_holm_family.json"), "w"), indent=2)
print(f"-> outputs/next5_holm_family.json")
