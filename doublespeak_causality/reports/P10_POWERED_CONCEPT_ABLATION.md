# §10 — Powered Concept-Circuit Behavioral Ablation (v3, pooled n=324)

**Status:** ✅ DONE. **Informative NULL — the concept circuit is behaviorally negligible at power**, and
crucially **less effective than a count-matched random ablation** → its small ASR effect is non-specific
degradation, not a concept lever. Powered confirmation of **Claim A (concept remap epiphenomenal)** and
resolves the earlier underpowered (n≈86, power 0.09–0.14) nulls (Gate C).

**Run:** `phase10_powered_concept_L8_9_10_11_...732980` (324 items, 0 skipped) · v3 clearharm+generated pooled ·
`scripts/phase10_powered_concept_ablation.py`. Arms (decode-safe, StrongREJECT-judged): baseline · write-ablation
(L8–11 MLP at codeword positions) · carry-ablation (L14–21 carry heads) · write+carry (full circuit) ·
**rand-ablation (count-matched random MLP positions + random heads = specificity control)**. Primary = paired
binary McNemar; secondary = graded Wilcoxon.

## Result — POOLED (n=324, ASR_base=0.333); target minimum meaningful ΔASR=0.09
| arm | ΔASR | 95% CI | McNemar p | approx MDE | verdict |
|---|---|---|---|---|---|
| write ablation | +0.059 | [0.004, 0.113] | 0.048 | 0.079 | small/sig but < random |
| carry ablation | +0.031 | [−0.014, 0.075] | 0.22 | 0.064 | informative-null |
| **write+carry (full concept circuit)** | **+0.046** | [−0.011, 0.104] | 0.14 | **0.083** | **INFORMATIVE-NULL** (MDE ≤ 0.09) |
| **rand ablation (control)** | **+0.161** | [0.110, 0.211] | ~0 | 0.076 | (largest effect) |

Per cohort: **clearharm (the real-attack cohort, n=170): write+carry ΔASR = 0.000 (b=22/c=22, p=1.0)** — an exact
null — while rand = +0.124 (p<1e-3). generated (n=154): write+carry +0.097 (p=0.04) but rand +0.201 (bigger).

## Interpretation
1. **Ablating the full concept circuit does NOT meaningfully reduce jailbreak ASR** — informative-null at
   n=324 (MDE 0.083 ≤ the 0.09 minimum meaningful effect; point estimate +0.046, CI includes 0), and an
   *exact* null on clearharm. This converts the old underpowered nulls into a powered one (Gate C).
2. **The decisive specificity fact:** a **count-matched RANDOM ablation reduces ASR ~3× MORE** than the
   concept-circuit ablation (+0.161 vs +0.046 pooled; +0.124 vs 0.000 clearharm). If the concept circuit were
   a behavioral locus, ablating it should beat random — it does the opposite. The small ASR movement from any
   ablation is **non-specific model degradation, not a concept-specific effect.** → **Claim A confirmed at
   power: the concept remap is behaviorally epiphenomenal.**
3. Sign note: all ablation ΔASR are ≥0 (ablation slightly *raises* refusal / lowers ASR via generic damage),
   never a concept-specific reduction.

## Caveat
The random-ablation ASR drop (and part of the concept-ablation drop) is likely **degradation/incoherence**
rather than genuine refusal re-engagement — ablating MLPs/heads breaks fluent generation (graded mean score
0.263→0.122 for rand). The empty/incoherence guard should be inspected before calling any ablation a "defense";
for the **epiphenomenality** conclusion this only strengthens the point (concept ablation < random damage).

## Verdict
**Gate C: concept circuit is behaviorally negligible at power (informative-null), and specifically less
effective than random ablation → Claim A (concept-remap epiphenomenal) is confirmed, not merely underpowered.**
