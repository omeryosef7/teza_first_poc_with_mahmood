# reports/PHASE7_PATH.md — Path mediation: DIRECT-vs-TOTAL of the answer-position head band

**Question (plan Q7 / Gate 5):** are the Phase-5 answer-position heads genuine concept-**carry** (their
effect flows through downstream layers) or readout-**proximal output** heads (direct to the logit)?

## Method
`scripts/phase7_direct_total.py`, reusing `50_path_patching`'s freeze primitives verbatim
(`FreezeAllHeadsExcept` + `FreezeMLP` + `capture_clean_all`). For each candidate head S:
- **TOTAL[S]** = m_clean − M(patch S's z ← BENIGN at the answer position; everything recomputes).
- **DIRECT[S]** = m_clean − M(same benign injection, but ALL downstream heads + MLPs frozen to clean-DS →
  only S's residual-skip path to the logit survives).
- **direct_frac = median(DIRECT/TOTAL)** over examples with |TOTAL| > 0.05.

Metric M = logit_diff(concept − codeword) at the last position (same as 48/49/50). Sanity gate (audit
14/15): direct_frac is nulled unless `freeze_consistency_dev ≤ 0.05` (freeze-all-clean + clean sender
reproduces m_clean) AND `selfswap_dev ≤ 0.05`. Jobs 704725 (curated) / 704726 (clearharm), n≥20/split.
**All heads trust=True; freeze_consistency_dev = 0.0 and selfswap_dev = 0.0 everywhere** (freeze exact).

## Result — mid-band = CARRY (mediated), late = PROXIMAL OUTPUT (direct). Both cohorts, both splits.

direct_frac (0 ⇒ fully mediated/carry · 1 ⇒ fully direct-to-logit):

| head | curated dev | curated heldout | clearharm dev | clearharm heldout | reading |
|------|------------|-----------------|---------------|-------------------|---------|
| L14H4  | 0.00 | 0.00 | 0.00 | 0.00 | **carry** |
| L14H5  | 0.00 | 0.05 | 0.00 | 0.00 | **carry** |
| L14H23 | 0.00 | 0.00 | 0.00 | 0.00 | **carry** |
| L15H4  | 0.00 | 0.00 | 0.00 | 0.00 | **carry** |
| L15H8  | 0.00 | 0.00 | 0.00 | 0.00 | **carry** |
| L17H27 | 0.17 | 0.00 | 0.09 | 0.07 | mostly carry (small direct) |
| L18H20 | 0.00 | 0.04 | 0.08 | 0.09 | **carry** |
| L21H10 | 0.00 | 0.00 | 0.00 | 0.02 | **carry** |
| L30H15 | 0.65 | 0.57 | 0.50 | 0.47 | **proximal output** |
| L31H0  | 0.76 | 0.63 | 0.60 | 0.63 | **proximal output** |

- **The mid-to-late-mid band L14–L21 are CARRY heads (direct_frac ≈ 0):** freezing all downstream
  heads/MLPs to clean removes essentially their whole logit effect, so that effect is *reconstructed by
  downstream layers* — they feed the concept forward, they do not write it to the logit directly.
- **Only the latest heads L30–L31 are readout-PROXIMAL output heads (direct_frac ≈ 0.5–0.76):** roughly
  half-or-more of their effect reaches the logit through the residual skip alone.
- **Resolves the Phase-5 proximity caveat:** the mechanistically important mid-band (L14–L21) is genuine
  carry, NOT a readout artifact. The proximity concern applies only to L30–L31.

## Interpretation — the assembled causal circuit
**L8–11 demonstration-codeword retrieval (K/V) + L9 MLP write → L14–L21 answer-position CARRY heads
(effect mediated through downstream layers) → L30–L31 proximal OUTPUT heads → logit.**

Each stage is causally tested: demo-KV necessity (Phase 4), MLP-write necessity @L9 (Phase 6, Wilcoxon
Holm all 4 cells), head necessity L14–18 (Phase 5, Wilcoxon Holm 3/4 powered cells), and now the
carry-vs-output separation (Phase 7). Distributed within each band (no single necessary head/edge), but
clear directed layer structure. Gate 5 met for the carry band.

## Phase 7b — circuit closure: the L14–L21 carry band READS the L9 MLP write (mediation)

`scripts/phase7b_mediation.py`. Neutralize the L9 demo-codeword MLP write (ComponentOutSwap ← benign,
= Phase-6 necessity, drop `C1→pA`), then FREEZE the carry-head answer-position z to their clean DS values
(ZHeadPatch) so they output the concept contribution regardless of the L9 change. If freezing RESTORES the
reading, the L9 effect is mediated by the carry band. `mediation_frac = (pB − pA)/(C1 − pA)`. Control =
freeze the same COUNT of RANDOM non-carry heads. self-check = freeze carry without touching L9 (must ≈ C1).
Jobs 705295/705296, on L9-responsive examples (C1−pA > 0.02).

| cell | n(L9-resp) | median mediation_frac (carry) | random-head control |
|------|-----------|-------------------------------|---------------------|
| curated dev      | 9  | **0.76** | 0.0 |
| curated heldout  | 9  | **0.83** | 0.0 |
| clearharm dev    | 13 | **0.75** | −0.0 |
| clearharm heldout| 9  | **1.46** (overshoot, n=9) | −0.0 |

- **Freezing the L14–L21 carry band restores ~75–83% of the L9-neutralization drop** (clearharm heldout
  overshoots at small n) — the L9 write's effect on the reading is **mediated by the carry band**. self-check
  exact (0.0) all cells.
- **Random-head freeze restores 0%** — perfectly specific to the carry heads, both cohorts+splits.
- → **the L9-write → L14–21-carry EDGE is causal.** The circuit is now a directed, edge-connected pathway,
  not two separately-validated endpoints.

## Phase 7c — the carry band is (partially) SUFFICIENT: sufficiency EMERGES at L14–21

`scripts/phase7c_sufficiency.py`. Install the DS carry-head answer-position z into a BENIGN receiver
(ZHeadPatch) — does the concept reading appear? Arms S1 (benign) / S3_carry (install DS carry z) / S_rand
(install DS z from the same count of RANDOM non-carry heads) / S_self (benign's own z, no-op). Jobs
706024/706025, full n both cohorts.

| cell | S1 (benign) | S3 (install DS carry) | sufficiency_specific = S3−S_rand [95% CI] |
|------|-------------|-----------------------|--------------------------------------------|
| curated dev      | 0.000 | **0.162** | **+0.162 [.086,.254]** |
| curated heldout  | 0.001 | **0.240** | **+0.239 [.126,.370]** |
| clearharm dev    | 0.064 | **0.434** | **+0.369 [.268,.477]** |
| clearharm heldout| 0.068 | **0.467** | **+0.406 [.297,.509]** |

- **Installing the DS carry-head z into a benign prompt RAISES the reading substantially** (to 0.16–0.47;
  the full DS reading is ~0.8–0.88, so 20–53% of it), **significant and specific on all 4 cells** (random-
  head install does nothing — S3−S_rand ≈ S3−S_1), self-check exact (0.0).
- **This is the FIRST component with both necessity AND sufficiency.** Every earlier sufficiency test was
  ≈0: demo-KV install (Phase 4), MLP-write install (Phase 6 S3), behavioral state-injection (≤0.16). The
  carry-head output, uniquely, **transplants the concept reading** into a benign context.
- **Not readout-proximity:** Phase 7 showed these heads are mediated (direct_frac ≈ 0), so injecting their z
  is not a direct-logit hack — the effect propagates through downstream layers.
- **Interpretation — sufficiency EMERGES at the carry stage.** The binding is context-bound / non-
  transplantable at the demonstration/write stage (necessary-not-sufficient at L8–12), but by the time the
  concept is carried in the L14–21 answer-position heads it has become a **transplantable representation**.
  This is a progression: context-bound retrieval/write → transplantable carried concept.

## Phase 7d — sufficiency ONSET: cumulative across L14–21, L17H27 pivotal

`scripts/phase7d_onset.py` installs CUMULATIVE carry subsets (L14 → L14–15 → L14–17 → L14–18 → L14–21)
DS→benign to locate the context-bound→transplantable transition. Controls pass (S_rand ≈ S1, self-dev 0.0).
Jobs 706055/706056. p_concept by cumulative subset:

| cell | L14 | L14–15 | L14–17 | L14–18 | L14–21 |
|------|-----|--------|--------|--------|--------|
| curated dev      | .004 | .007 | **.077** | .117 | .162 |
| curated heldout  | .017 | .052 | **.208** | .185 | .240 |
| clearharm dev    | .193 | .209 | **.409** | .359 | .434 |
| clearharm heldout| .157 | .179 | **.388** | .349 | .467 |

- **Sufficiency accumulates GRADUALLY across the band — not an abrupt L14 switch.** The single largest jump
  is **adding L17 (H27)**: curated dev ×11 (.007→.077), heldout ×4 (.052→.208), clearharm ×2 both splits.
  L17H27 is also the top necessity head on clearharm — a pivotal carry head.
- **Cohort difference:** clearharm has substantial L14-alone sufficiency (.16–.19) while curated builds from
  ≈0 (L14) with the jump at L17 — clearharm carries concept-signal earlier (its concept-in-context nature).
- → sufficiency, like necessity, is **distributed within the L14–21 band** (pivotal head L17H27); the full
  band gives maximal transplantability. Consistent with the whole-circuit "distributed within a band" theme.

### v2 confirmation (116-ex expanded bench)
Carry-head sufficiency generalizes to the larger data: dev (n=59) suf_specific **+0.326 [.246,.411]**,
heldout (n=57) **+0.348 [.261,.439]** (S1≈0.05 → S3≈0.40), self-swap 0.0. Confirmed on 30 novel concepts.

## Caveats / next
- Partial sufficiency (20–53% of the full reading) — the carry heads are a strong but not complete injectate.
- Representational sufficiency (FC p_concept). Whether the carry-head install is BEHAVIORALLY sufficient
  (StrongREJECT ASR) is a separate question (prior state-injection was ≤0.16 behaviorally) — future work.
- mediation medians (Phase 7b) are over the L9-responsive subset (n=9–13); clearharm heldout overshoots at
  small n. direct_frac (Phase 7) is a median over |TOTAL|>0.05 examples.

Reproduce: `python scripts/phase7_direct_total.py --bench data/bench/bench_<cohort>.json --heads <L..H..list>`.
