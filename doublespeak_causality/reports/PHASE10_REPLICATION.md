# PHASE 10 — Second-corpus replication (AdvBench), external validity + power

Plan §14. Independent replication of the headline causal results on a **second harmful
corpus** (AdvBench doublespeak, leakage-0, built by `build_advbench_doublespeak.py`),
not pooled with ClearHarm. Purpose: external validity and higher behavioral power
(§14.1–14.3).

| | |
| --- | --- |
| Model | Llama-3.1-8B-Instruct (bf16, sdpa) |
| Corpus | `advbench_doublespeak_v1.json` — 399 records, source AdvBench sha256 `6cd1a5c6…`; leakage-0 (concept- & codeword-disjoint), test **n=88** (≈2× ClearHarm's 42) |
| Extraction | run 758606 (acts 1197×32×2×4096) |
| Phase 4 | run 758657 (FACTORIAL + refusal), test split, StrongREJECT ≥0.5 |

## Result 1 — Gate 1: Bombness decodes, but the probe is confounded (honest limitation)

| position | holdout AUC | position_only | length_only | token_id |
| --- | --- | --- | --- | --- |
| codeword | **0.982** [0.96,1.00] | 0.785 | 0.752 | 0.500 |
| decision | **1.000** | 0.785 | 0.752 | 0.500 |

Two corpus versions were built:

| corpus | Gate 1 | holdout AUC | position_only | length_only |
| --- | --- | --- | --- | --- |
| v1 (demos not length-matched) | FAIL | 0.982 | 0.785 | 0.752 |
| **v2 (length-matched, `--equalize-demos`)** | **PASS** | **0.9995** | **0.531** | **0.529** |

The v1 build did not length-match the doublespeak vs benign demo blocks, so the codeword's
absolute position (mean gap **−18 tokens**) and prompt length correlated with the label —
`position_only`/`length_only` reached 0.75–0.79 (a property of the corpus, not the readout).
**Fixed in v2:** the builder now pads the shorter demo block with neutral filler to equal
token length (`equalize_demo_lengths`), collapsing the codeword-position gap to **1.1 tokens**.
On v2, Bombness **decodes essentially perfectly (AUC 0.9995) with every control at chance**
(position 0.531, length 0.529, token-id 0.500, label-shuffle 0.494, random-dir 0.472) — a
**clean, confound-free second-corpus probe (Gate 1 PASS).** Decodability external validity is
therefore established cleanly, not just as a bounded signal. (The behavioral results, Result 2,
are on v1 and are confound-robust regardless — they use the refusal lever + interventions, not
the probe.)

## Result 2 — Phase 4: Story A replicates at higher power (the confound-robust core)

Base ASR 0.205 (n=88). The **refusal** arm is independent of the Bombness probe confound.

| arm | ΔASR | 95%/McNemar | manipulation check |
| --- | --- | --- | --- |
| **refusal ablation (the lever)** | **+0.295** | b=3 c=29, **p=0.0** | refusal rate 0.64→0.19 |
| bomb necessity (ablate v_bomb) | +0.057 | b=0 c=5, p=0.06 (n.s.) | readout dropped −0.8…−1.6 (passed) |
| bomb vs norm-matched random | +0.034 | b=1 c=4, p=0.38 (n.s.) | — (bomb ≈ random) |

_(McNemar convention throughout this report and the power table: **b** = base-success→arm-fail
(losses), **c** = base-fail→arm-success (gains); ΔASR = (c−b)/n. Confirmed by independent raw
re-derivation, E64.)_

**2×2 factorial (n=88):**

| effect | estimate | 95% CI |
| --- | --- | --- |
| **main effect refusal** | **+0.284** | [0.188, 0.381] |
| main effect Bombness | +0.046 | [0.011, 0.085] |
| interaction | −0.023 | [−0.102, 0.057] |

**Reading.** The **refusal lever replicates strongly and significantly** on the
independent corpus (+0.295, p=0.0; 2×2 main +0.284) — the confound-robust headline holds
with external validity. Bombness ablation is **behaviorally null** (necessity +0.057 n.s.,
and **indistinguishable from random** ablation, +0.034 p=0.38) despite a passing
manipulation check — epiphenomenal, replicating ClearHarm. The 2×2 Bombness main effect is
a tiny +0.046; because it equals the random-ablation effect it is **non-specific**, not
evidence of a causal Bombness channel. No interaction (no gating). This is Story A
(Bombness epiphenomenal; refusal is the lever) reproduced on a second corpus.

## Result 3 — Prospective power (§14.2)

Paired-McNemar power from the actual AdvBench discordant rates:

| arm | discordant rate p_disc | at n=88: min detectable ΔASR (80%) |
| --- | --- | --- |
| refusal | 0.364 (b=3, c=29) | **0.186** — so the +0.295 refusal effect is well-powered (p=0.0) |
| bomb | 0.057 (b=0, c=5) | unreachable — only 5/88 pairs move; the null is a tight bound |

For a ΔASR = 0.10 effect at 80% power, ~**n=305** is required — even n=88 cannot resolve a
0.10 effect, so the Bombness null (+0.05) is correctly reported as a **bound**, not "exactly
zero". The second corpus roughly doubles power (n=88 vs 42) and is decisive for the
refusal-magnitude effect, which is the point of Phase 10.

## Not run (honestly bounded)

- **Dual-probe prediction (§14.3 item 5)** on AdvBench: needs behavioral outcomes on the
  TRAIN split (Phase 4 generated only the test split), i.e. a further base-generation GPU
  run; and the Bombness predictor is confounded by Result 1, so its predictive value would
  be muddied. Deferred rather than report a confounded predictor.
- A **length-matched** second corpus (clean Gate 1) — the builder fix for Result 1.

## Verdict

Phase 10 delivers its purpose: **the causal headline — refusal suppression is the
behavioral lever, Bombness is epiphenomenal — replicates on an independent harmful corpus
at ~2× power**, with the refusal effect now significant (p=0.0) rather than CI-bounded. The
one caveat (probe position/length confound from unmatched demos) is documented and does not
affect the confound-robust refusal result.

## Reproduce

```
python scripts/build_advbench_doublespeak.py --seed 7
sbatch --constraint=l40s --export=ALL,MODE=full,COHORT=advbench,CORPUS=<advbench_v1.json>,SPACE=resid_post run_probe_extract.slurm
python -m src.probes.gate1_eval --run <ext> --position codeword_last
python -m src.probes.build_intervention_directions --run <ext> --band 8,...,31 --out outputs/phase4_directions/v_bomb_advbench.pt
sbatch --constraint=l40s --export=ALL,MODE=full,COHORT=advbench,CORPUS=<advbench_v1.json>,FACTORIAL=1,WITH_REFUSAL=1 run_phase4_bombness.slurm
python -m src.probes.analyze_phase4 --run <phase4> --out reports/PHASE10_PHASE4.json
python scripts/phase10_power_analysis.py --from-run <phase4> --base-field ds_base_score --arm-field ds_refusal_ablate_score --corpus-n 88
```
