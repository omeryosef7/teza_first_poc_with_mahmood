# Quantization Extension (Q7 / Phase 6)

Question: does the paper's causal result — **ablating the refusal direction raises harmful compliance,
specifically (vs a norm-matched random direction), dose-dependently** — survive weight quantization?

Model: Llama-3.1-8B-Instruct. Refusal axis: L18 (validated readout). Bench: `behavioral_v3b/beh_clearharm.json`,
**test split n=42**. Intervention: activation-space ablation of the refusal direction at strength α
(0.0/0.5/1.0), StrongREJECT-judged, vs a norm-matched **random** ablation control. Same script
(`phase_behav_refusal.py`), identical config across precisions — only the model load precision changes.

NOTE: this is the **activation-space ablation** result (the refusal axis IS causal for behavior),
distinct from the **token-space GCG** result (Gate D: mechanism-derived suffixes are non-specific).
The two together are the paper's thesis: the refusal axis is causal when intervened on directly, yet
does not convert into a token-space optimization lever.

## 8-bit (bnb) — DONE (job 745089), test n=42
ASR by arm (direct = plain harmful prompt; refabl = refusal-direction ablation; randabl = random control):
| arm | α=0.0 | α=0.5 | α=1.0 |
|---|---|---|---|
| direct + **refusal**-ablation | 0.262 | **0.429** | **0.524** |
| direct + random-ablation | 0.262 | 0.143 | 0.143 |
| refusal_rate (refusal-ablation) | 0.738 | 0.405 | **0.238** |
| refusal_rate (random-ablation) | 0.738 | 0.833 | 0.810 |

Paired stats (direct+refabl vs direct): α=0.5 ΔASR **+0.167** (McNemar p=0.065); α=1.0 ΔASR **+0.262**
(flip 13↑/2↓, **p=0.0074**). Random ablation does the opposite (ASR ↓, refusal_rate ↑).
**Read:** under 8-bit, ablating the refusal direction is **behaviorally causal, dose-dependent, and
SPECIFIC** (beats norm-matched random), and drives refusal_rate from 0.74→0.24. "refusal-suppression ≈
Doublespeak" also holds (ds_base vs direct+refabl ΔASR≈0). The core causal finding is quantization-robust.

## bf16 control — RUNNING (job 746744, same config)
## 4-bit (NF4) — RUNNING (job 746743, same config)
_bf16 vs 8-bit vs 4-bit dose-response comparison table to be filled when both land._
