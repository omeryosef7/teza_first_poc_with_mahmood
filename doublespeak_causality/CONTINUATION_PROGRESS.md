# Continuation Sprint — Progress Log

Tracking execution of `reports/CAUSAL_CONTINUATION_MASTER_PLAN.md`.
Branch: `behavioral-causality-sprint`. Model: Llama-3.1-8B-Instruct bf16.
Loop: every 30 min (cron `86decf2e`, session-only, expires after 7 days).

**Legend:** ☐ not started · ◐ in progress · ☑ done · ⚠ blocked/needs-decision · ✗ null/negative result

---

## Environment facts (established tick 1, reuse these)

- Login node has **no torch/numpy/scipy** on system `python3`.
  Use `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`
  (numpy 2.4.6, scipy 1.17.1, torch 2.7.1+cu126) for all CPU analysis.
- 26 `scripts/phase*.py` harnesses exist (the plan's "21" was an undercount).
- `ds_common.env_metadata()` exists at ds_common.py:82 and imports torch → must not be a hard
  dependency of any CPU-only provenance path.
- SLURM rules unchanged: no dependencies, ≤6 parallel, L40S only, comma-lists in wrapper defaults
  (never in `--export`).

---

## Phase status

| Phase | Status | Note |
|---|---|---|
| P0 — trust the repo | ◐ | tick 1 in progress |
| P8.0 — interaction from existing data (free) | ◐ | tick 1 in progress |
| P10.0 — graded re-analysis of the nulls (free) | ◐ | tick 1 in progress |
| P1b — ClearHarm v3 | ☐ | after P0 |
| P1 — corrected baseline + drift envelope | ☐ | needs GPU |
| P10 — decode-safe re-test | ☐ | needs new primitive + GPU |
| P8 — combined causal ASR factorial | ☐ | needs P1b + P8.1 α calibration |
| P9 — GCG/MAC Gate 7 | ☐ | needs P9.0 optimizer bug fixes |
| P2 — all codeword occurrences | ☐ | one free cell already implemented, never launched |
| P3/P4/P5 — attention, induction heads, path matrix | ☐ | |
| P6 — Jacobian readout | ☐ | |
| P7 — concept ⊥ refusal + re-validate 32 refusal dirs | ☐ | blocks per-layer refusal claims |
| P11 — framework robustness | ☐ | appendix |
| P12 — quantized | ☐ | appendix |
| P13 — cross-model | ☐ | last |
| P14 — paper assembly + claim audit | ☐ | last |

---

## Results so far

### ⭐ P8.0 — the Doublespeak × refusal-down interaction is significantly SUB-ADDITIVE
**Independently verified** (recomputed from scratch by the main agent; matches the analysis script to 4 dp).
`reports/PHASE8_0_PILOT_INTERACTION.md` · `scripts/analyze_interaction_2x2.py` · `outputs/interaction_2x2.json`

clearharm pooled, n=86, within-item `D_i = Y(1,1) − Y(1,0) − Y(0,1) + Y(0,0)`:

| outcome | Î | 95% CI | perm p |
|---|---|---|---|
| binary ASR | **−0.1860** | [−0.349, −0.023] | **0.0451** |
| graded score | **−0.1904** | [−0.340, −0.041] | **0.0162** |
| compliance | −0.1977 | [−0.337, −0.058] | 0.0115 |

Cell ASRs (pooled): Y(0,0) 0.105 · Y(1,0) 0.372 · Y(0,1) 0.558 · Y(1,1) 0.640.
curated pooled n=51: Î = **−0.3922** [−0.588, −0.196], **p = 0.0004** (same direction, stronger).

**The robust item-level fact:** `D_i = +2` occurs **0 times in 137 items** across both cohorts and all
splits, while `D_i = −2` occurs 5 times. This is immune to the averaging/ceiling confound below.

⚠ **Honest caveats (all in the report):** at α = 1.0 the design is saturated — `I_max` = +0.174 (clearharm)
and 62.8% of items are already jailbroken by one factor alone, so they can only contribute `D_i ≤ 0`; a
negative Î is therefore *partly arithmetically forced*. clearharm-test binary p = 0.0498 is knife-edge and
pooled significance depends on pooling train+test (defensible — no model selection on either — but must be
stated). **P8.1's α calibration is a genuine blocking prerequisite** before the magnitude of Î means anything.

**Reading:** Doublespeak and refusal-ablation are sub-additive, consistent with them acting on a *shared
refusal bottleneck* rather than independent channels. Plan §0.6's prediction is confirmed, not refuted.

### 🐛 Judge divergence — a real bug in the script that produced the Phase 2.1 baseline
`scripts/behav_judge.py` now holds the single judge contract, differential-tested against all 6 copies
(35 kw_refusal + 175 classify + 140 extended + 175 end-to-end cases per file). 4 of 6 agree exactly.

- **FINDING 1 (paper-relevant).** `14_behavioral_eval.py` has **no EMPTY label**. The four `phase_behav_*`
  harnesses short-circuit `if not completion.strip(): return None, "EMPTY"`; `14_behavioral_eval.py:88-101`
  does not, so a blank generation is sent to the judge and folded into BENIGN (or MALICIOUS), and its
  summary has **no `empty_rate` guard at all**. On a synthetic 5-row cohort this moves ASR by −0.40 and
  refusal_rate by +0.40. **`14_behavioral_eval.py` is what produced the Phase 2.1 baseline
  (clearharm DS 0.349 / direct 0.116).** Those numbers need an empty-generation audit — logged as an
  action item for P1.
- **FINDING 2 (low exposure).** `+inf` score handling drifts: `14` labels it MALICIOUS, the `phase_*` copies
  label it BENIGN/REJECTED. Only reachable if the StrongREJECT rubric returns a non-finite score.

### 📋 Artifact audit — tick-1 baseline (`scripts/audit_artifacts.py`, 0.5 s, exit 1)
367 run dirs · summary.json in 91 · **RUNMETA.json in 0 · DONE.json in 0** · 20 empty dirs ·
1 raw-without-summary (the job-708038 aborted twin) · 62 fixed-name (clobber-on-rerun) dirs ·
20 job ids shared by 69 dirs · 350 unregistered runs · outputs 8.9 GiB · disk 98% used.
**Manifest drift is 3, not the 1 the recon reported** — two `subsample.npz` files drift at *identical size*,
so the cheap size-only check misses them; only `--verify-hashes` catches it.

---

## Tick log (most recent first)

### Tick 2 — 2026-08-05 — P8.0 verified; judge + audit landed
3 of 7 agents returned. Independently re-derived the P8.0 interaction from scratch before accepting it
(exact match). Recorded the artifact baseline. Found and documented the `14_behavioral_eval.py` EMPTY-label
bug. 4 agents still running (provenance core, validators, P10.0 graded re-analysis, primitive tests).

### Tick 1 — 2026-08-05 — P0.1 artifact preservation shipped (commit `27a4cfe`)
Set up the 30-min loop. **Un-ignored the evidence:** 287 summary files + 219 SLURM logs (13 MB) now in git;
raw.jsonl / gens / npz / pt remain archive-only. Three-pass safety filtering — the third pass (scanning the
actually-staged blobs) caught `ds_gcgopt_692819.out`, which echoes the evolving GCG suffix every step and
which the first two heuristics missed. 20 `.out` files and all `.err`/`.log` are held back pending manual
redaction. **Deviation from plan §2.2 item 2**, which said commit logs wholesale — reported to Omer.
