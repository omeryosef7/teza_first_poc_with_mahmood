# P2 — Patching ALL codeword occurrences roughly DOUBLES the L9 write necessity

**Status: ✅ COMPLETE on all three benches.** clearharm-v1 + curated (jobs 714998 / 714999) and the
**v2 116-example replication (job 718027)**. The finding holds everywhere it was tested.
**Plan:** §5 P2, bullet B6 ("patch all codeword occurrences, not just the last").
**Zero new code** — `phase6_mlp_causal.py` already implemented `--positions {demo,query,all}` (line 131);
the `all` cell had **never been launched**.

---

## 1. What changed

| mode | positions patched |
|---|---|
| `demo` (the sprint's standard) | the ~12 demonstration-codeword occurrences |
| `query` | the codeword occurrence inside the forced-choice question |
| **`all`** (new) | **demo + query jointly** |

Everything else is identical: same bench, same splits, same readout (forced-choice `p_concept`), same
analyzer (`phase6_analyze.py`, Wilcoxon + Holm over the 32-layer family, 2000-resample bootstrap CI).

**The reported effect is already specificity-controlled.** `necessity_specific = random_control − C3`,
where `random_control` installs the benign `mlp_out` at **count-matched** non-codeword positions drawn from
the in-demo-text span (`rlen = min(m, |ds_pool|, |b_pool|)`, phase6_mlp_causal.py:198). So a larger effect
is **not** explained by "we patched more positions" — the control grows with the intervention.

---

## 2. Result — L9 necessity, demo-only vs all-occurrence

All four cells, same analyzer, same n:

| cohort · split | n | demo-only L9 | **all-occurrence L9** | ratio |
|---|---|---|---|---|
| clearharm dev | 44 | +0.0625 [0.023, 0.113] | **+0.0889 [0.037, 0.153]** | **1.42×** |
| clearharm heldout | 41 | +0.0153 [0.006, 0.029] | **+0.0348 [0.011, 0.069]** | **2.27×** |
| curated dev | 30 | +0.0493 [0.021, 0.081] | **+0.1003 [0.033, 0.183]** | **2.03×** |
| curated heldout | 21 | +0.0970 [0.038, 0.162] | **+0.1797 [0.092, 0.277]** | **1.85×** |

**L9 is Holm-significant in all four cells under both modes, and is the argmax layer in all four under
`all`.** The all-occurrence effect is larger in every cell, by 1.4×–2.3×.

Holm-significant bands under `all`:

| cell | Holm+ layers |
|---|---|
| clearharm dev | L8 (+0.044), **L9 (+0.089)**, L11 (+0.037), L12 (+0.022), L15, L20 |
| clearharm heldout | **L9 (+0.035)**, L22 (+0.0005) |
| curated dev | L8 (+0.025), **L9 (+0.100)**, L12 (+0.029), L20 |
| curated heldout | **L9 (+0.180)**, L12 (+0.036) |

Self-swap controls exactly 0.0 at every layer/split (smoke and full). Sufficiency remains ≤ 0 everywhere,
unchanged from demo-only — **the write is still necessary and not sufficient.**

---

## 2b. v2 replication (116-example bench, job 718027) — it holds

Run on `bench_clearharm_v2.json` (86 clearharm + 30 expanded concepts), same analyzer, same Holm family:

| cell | n | demo-only L9 | **all-occurrence L9** | ratio |
|---|---|---|---|---|
| v2 dev | 59 | +0.0798 | **+0.1101 [0.060, 0.170]** | 1.38× |
| v2 heldout | 55 | +0.0304 | **+0.0649 [0.030, 0.108]** | **2.13×** |

L9 is the **argmax and Holm-significant on both splits**. Holm-significant bands: dev **L7–L12** (plus L15,
L20), heldout **L9, L12, L22**. Note the dev band now reaches **L7**, one layer earlier than the v1 benches
showed — consistent with the write being distributed across a band rather than pinned to L9.

**The ratio replicates across every bench tested:** 1.42× / 2.27× (clearharm v1), 2.03× / 1.85× (curated),
1.38× / 2.13× (v2). All six cells lie in **1.38–2.27×**, on three independently-built benches and 30 novel
concepts. The claim that the demo-only measurement understates the write by roughly a factor of two is not
a single-bench artifact.

*(Provenance note: this is the relaunch of job 714997, which was cancelled after hanging ~3 h in weight
loading with zero output — a node-level stall, not a code fault. 718027 ran the identical configuration to
completion.)*

## 3. Reading

The concept write is **not confined to the demonstration block**. The query-codeword occurrence carries a
real, independent share of the same L9 write, and the two contributions **add**: patching them jointly
roughly doubles the necessity effect relative to the demonstrations alone, against a count-matched control.

This reconciles a loose end from the previous sprint. Its audit found that the query-codeword MLP is "3–4×
weaker than demo but **not absent**" on clearharm (L9/L15/L20 survived Holm on both splits) — which
contradicted the report prose calling the query position inert. The `all` cell now shows why that mattered:
the demo-only measurement was **understating the write by roughly a factor of two** because it was patching
only part of the write site.

**Consequence for the circuit description.** The L8–L11 / L9-peak write should be described as operating
over *every codeword occurrence in context*, not "at the demonstrations". The narrower demo-only framing
used in `FINAL_CAUSAL_CIRCUIT_REPORT.md` and `PHASE6_MLP.md` understates the effect size.

---

## 4. Honest limitations

- **Larger, but still not sufficient.** Sufficiency (`S3_install − S_random`) stays ≈ 0 at every layer, so
  this does not change the necessity-not-sufficiency verdict.
- **Representational only.** This is the forced-choice `p_concept` readout. It says nothing about behavior;
  the behavioral write ablation (BEHAV-WRITE) was null *and* prefill-only, and its decode-safe re-test (P10)
  is still outstanding.
- **The ratio is not itself a tested quantity.** demo-only and all-occurrence are separate runs; the
  1.4–2.3× ratios are descriptive comparisons of two independently-estimated effects, not a paired test of
  the difference. A within-item paired contrast of the two position sets would be needed to put a CI on the
  increment — cheap to add and worth doing before this goes in the paper.
- ~~v2 replication still running~~ **DONE — see §2b. It replicates.**
- Per-occurrence resolution (each demonstration individually, first vs second half of the demo block) is
  **not** covered here — that is the remaining part of plan §5 P2 and needs the new
  `resolve_all_occurrences` helper.

---

## 5. Reproduce

```
sbatch --time=08:00:00 --export=ALL,DSBENCH=doublespeak_causality/data/bench/bench_clearharm.json,\
DSNPROMPTS=0,DSGRAN=layer,DSPOS=all doublespeak_causality/slurm/run_phase6_mlpko.sh
python scripts/phase6_analyze.py outputs/phase6_KO_<cohort>_mlp_out_all_layer_<ts>_<job>
```

Runs: clearharm `phase6_KO_clearharm_mlp_out_all_layer_20260805_142528_714998`,
curated `phase6_KO_curated_mlp_out_all_layer_20260805_142420_714999`.
Demo-only baselines: `phase6_mlpKO_clearharm_demo_layer_20260803_102135_703532`,
`phase6_mlpKO_curated_demo_layer_20260803_102227_703531`.
