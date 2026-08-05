# Behavioral refusal-locus — consolidated results table (paper Table 1)

Llama-3.1-8B-Instruct, bf16, greedy decode. Two cohorts (**clearharm** 86 = 44 train/42 test;
**curated** 51 = 30/21), **locked** train/test. Behavioral metric = StrongREJECT ASR (MALICIOUS ≥0.25);
representational metric = refusal-axis projection at the decision token. Paired **McNemar exact** + bootstrap
CI where paired. All numbers verified against raw (zero transcription errors); all harnesses code-audited
(mappings consistent, no off-by-one), the necessity outputs coherence-audited. Every result carries a
matched control (random head / random position / norm-matched random direction).

| # | Claim | Experiment | Effect (clearharm) | Effect (curated) | Significance | Control | Verdict |
|---|---|---|---|---|---|---|---|
| **1a** | Carry heads behaviorally **inert** | BEHAV-CARRY | ΔASR +0.09 tr / +0.07 te | −0.10 tr / 0.00 te | McNemar p≥0.28 (ns) | random-head ~0 | **NULL** |
| **1b** | L8–11 write behaviorally **inert** | BEHAV-WRITE | ΔASR −0.02 tr / 0.00 te | +0.07 tr / 0.00 te | McNemar p≥0.69 (ns) | random-pos ~0 | **NULL** |
| **2** | Refusal ablation **sufficient** (> DS) | BEHAV-REFUSAL | direct+abl ASR .57/.55 vs base .14/.07 (Δ+.43/+.48) | .70/.71 vs .27/.29 (Δ+.43/+.43) | p<1e-5 / p≤4e-3 (all splits ≤.004) | random-dir null (p≥.5) | **CAUSAL** |
| **3** | Refusal re-injection **necessary** | BEHAV-REFUSAL (inject) | ds ASR .39/.38 → **.00**/.**00** @α12 | .33/.10 → **.00**/**.00** | McNemar p=2e-5…2e-3 | random-dir null (p≥.12); empty=0; coherence-audited | **CAUSAL** |
| **4** | DS **suppresses** the refusal axis (repr) | REFPROJ | proj@L31 direct 15.2 / ds 3.6 / neutral 6.9 (DS≤benign) | direct 15.5 / ds −1.2 / neutral −1.6 | onset ~L8, grows w/ depth | random-dir null every layer | **CONFIRMED** |
| **5** | Refusal **decision read mid-late** (calibrated) | CALIB-INJECT | rescue L22 ΔASR −0.25 (p=.001); L9 ns (p=.45) | L22 −0.20 (p=.031); L9 ns | L16/22/28 sig, L9 ns, both cohorts | random-dir null all layers | **CAUSAL** |
| **6** | Concept-remap ⊥ refusal-suppression (**decoupled**) | WRITE×REFUSAL | p_concept .88→.80 (control fires); refusal frac_restored ≈0 (|·|<.02) | p_concept .69→.46; frac_restored ≈0 (|·|<.05) | control CIs exclude 0; refusal Δ CIs include 0 | positive control (p_concept) | **INDEPENDENT** |
| **7** | Refusal proj **predicts jailbreak** (item-level) | REP→BEHAVIOR (join REFPROJ×BEHAV-REFUSAL) | **AUC 0.87**, r=−0.58 (jailbreak proj −1.15 vs refused +3.60) | null (AUC .42) — suppression *uniform* → concept-dilution 2nd mechanism | Mann-Whitney p=3.8e-9 / p=.79 | (per-item, both directions) | **PREDICTIVE (clearharm)** |
| **8** | Outcome set at **decision point** (not re-engaged) | REFUSAL-TRAJECTORY | @token0 L30: jailbreak −2.1 vs refuses 9.1 vs Direct 13.6 (separated from step 0) | ds_refused_rate=**0.0** (uniform) → concept-dilution confirmed | trajectories separated @token0, never cross | outcome-split | **DECISION-POINT** |

**Reading it:** rows 1a/1b — the concept circuit, though representationally necessary+sufficient for the
codeword→concept *readout*, does not causally drive the jailbreak. Rows 2–3 — one orthogonal refusal
direction is behaviorally necessary *and* sufficient (removing it jailbreaks harder than Doublespeak;
restoring it into Doublespeak drives ASR to zero). Rows 4–5 — Doublespeak suppresses the refusal
representation from the L8–11 write band, but the behavioral refusal *decision* is read mid-late (~L16–22).
Row 6 — the two effects are causally independent pathways, which is *why* the concept circuit is behaviorally
epiphenomenal.

**One-line conclusion.** Doublespeak is an imperfect in-context **refusal-suppression** technique; the
elaborate token→concept remap is a behaviorally epiphenomenal, causally-decoupled bystander. **Defense: scrub
the refusal axis, not the concept subspace.**

Sources (all committed): PHASE_BEHAV_CARRY.md · PHASE_BEHAV_WRITE.md · PHASE_BEHAV_REFUSAL.md ·
PHASE_WRITE_REFUSAL_INTX.md. Figures: figures/behavioral_dissociation.png · refusal_depth_mechanism.png ·
causal_decoupling.png. (Open, GPU-blocked: per-token refusal-trajectory dynamics for the ~0.35 base ASR.)
