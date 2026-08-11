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

## bf16 vs 8-bit vs 4-bit — dose-response comparison (ALL DONE), test n=42
Direct-prompt ASR under refusal-ablation vs norm-matched random-ablation, α∈{0,0.5,1.0}; McNemar for
the α=1.0 refusal-ablation vs base:
| precision | refabl ASR α=0/0.5/1 | randabl ASR α=0/0.5/1 | refusal_rate refabl 0→1 | α=1 ΔASR | McNemar p |
|---|---|---|---|---|---|
| **bf16** (746744) | 0.191 / 0.476 / 0.476 | 0.214 / 0.143 / 0.191 | 0.762 → 0.238 | **+0.286** | 0.0005 |
| **8-bit** (745089) | 0.262 / 0.429 / 0.524 | 0.262 / 0.143 / 0.143 | 0.738 → 0.238 | **+0.262** | 0.0074 |
| **4-bit** NF4 (746743) | 0.167 / 0.643 / 0.762 | 0.167 / 0.167 / 0.167 | 0.762 → 0.071 | **+0.571** | <1e-4 |

**Q7 verdict — the causal refusal-ablation effect is QUANTIZATION-ROBUST.** At every precision:
(1) ablating the refusal direction raises harmful compliance **dose-dependently** and **significantly**
(p ≤ 0.007); (2) it is **specific** — the norm-matched random-ablation control stays flat or drops at
all precisions; (3) refusal_rate collapses under refusal-ablation (0.76→0.07–0.24) but not under random.
The effect is if anything **strongest at 4-bit** (ΔASR +0.571). Conclusion: the paper's central causal
claim (refusal-suppression is the behavioral locus, and it is a specific direction) does not depend on
full precision — it survives 8-bit and 4-bit NF4 quantization on Llama-3.1-8B.
