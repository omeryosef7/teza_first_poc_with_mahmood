# ADVANCED OPTIMIZER RESULTS — PHASE 3 / GATE E

*Asymmetry sprint deliverable (plan §15.4).*
*Methods and the interpretation rules are written **before** the arms finish; §4 is filled
from the runs. Nothing in §1–§3 or §5 depends on the outcome.*

---

## 1. What this phase tests, and what it does NOT

Phase 0 found that the published token-space objective was **misconfigured**: it read the
refusal projection at **one absolute token index derived from `train_tasks[0]`**, which is the
intended token for **1 of 40** training prompts and out of range (silently contributing zero)
for another — and that index sits 5 template tokens before the position where the refusal axis
was fitted and causally validated (defects **D1** and **D2**, execution log E0.3).

So Gate D's negative rested on an objective that, for 39/40 prompts, was not reading the
coordinate it claimed to. This phase re-runs it **position-corrected**, everything else held
identical, to answer one question:

> **Was the token-space negative caused by the position defect?**

### It is NOT a clean test of H2′ — stated up front
A diagnostic (execution log 05:36, **corrected at 10:45** after audit BUG A — the first pass
read the projection at the *legacy* position even in corrected runs, understating it ~14×; the
numbers below are the corrected ones) shows that at **λ = 0.25**, the published value which
these arms copy for comparability, the refusal term is **0.370 % mean / 1.495 % max of the
`total_loss` that GCG's candidate selection minimizes**. Over training the task loss moved
**1,443×** more than λ·refusal. Candidates are therefore chosen overwhelmingly on task loss,
and the mechanism term carries little selection weight.

It is, however, **not inert**: the mechanism arm drives its own projection from **+0.131 to
+0.001** (a 99 % reduction) while the matched random arm moves **63× less**. So even at 0.37 %
weight the objective demonstrably has purchase on the coordinate it names — which is what makes
the λ question below the binding one, rather than a formality.

> **Therefore: a negative here means "the position fix ALONE does not rescue the objective",
> NOT "H2′ (linear-surrogate invalidity at discrete step size) is confirmed."** A λ at which
> the mechanism term carries meaningful weight has never been run — not by this sprint and not
> by the published one. That is recorded as the top follow-up, NOT RUN.

## 2. Design

Six arms: **3 seeds (42, 43, 44) × {mechanism, matched random}**, satisfying plan §7.4's
"minimum 3 identical seeds across arms".

| held identical to the published matrix | value |
|---|---|
| λ (`lambda_refusal_dir`) | 0.25 |
| layer index | 19 (= L18 + the off-by-one) |
| direction files | `refusal_direction_llama_L18.pt` / `refusal_rand_L18_normmatched_seed20260809.pt` — **the same random control the published matrix used** |
| suffix length / topk | 16 / 256 |
| steps × batch | 200 × 32 (same candidate-forward budget) |
| manifest, placement, `--no-filter-cand`, selection mode | v3 train pool 40, user, yes, weighted |
| **the ONE difference** | `--refusal-dir-position-mode per_task_decision` |

Verified from each arm's persisted `CONFIG.json`, not from a startup log line (execution log
05:06). Both arms of every seed share a GPU class (a5000), so the mechanism-vs-random contrast
is internally matched.

## 3. How Gate E will be read (pre-registered)

Plan §12 Gate E: *only call mechanism-derived token optimization a POSITIVE if the mechanism
objective beats its matched random objective on locked test, with consistent sign across
seeds, statistical support, AND the intended internal target moves more than random. ASR alone
is insufficient.*

Applied here:
1. **Held-out ASR**, evaluated through the same `26_eval_p9_gcg_heldout_asr.py --split test`
   path the published matrix used, so the new arms are scored identically to the arms they
   are compared against. `judge_fail_frac` must be **0** before any reading (a null judge
   scores everything benign and would make a working arm look like total failure).
2. **Sign consistency across the 3 seeds.** The published matrix's central weakness was
   **2/3 sign flips**; a mean is not enough.
3. **Effect vs the judge-noise floor.** Measured at **±0.03–0.08** at n=37 (execution log,
   judge nondeterminism). Any |ΔASR| below 0.08 is reported as *within judge noise*, not as an
   effect — which is what retired the published +0.018.
4. **The internal-target check** (the Q5 question, now asked of an objective that actually
   read the right coordinate): does the final corrected suffix move the held-out refusal
   projection more than the matched random suffix? Run via
   `scripts/asym_p1c_mech_validity_ext.py` on the new suffixes.

## 4. Results

**PENDING — arms in flight at the time of writing.** Will be filled from:
* `outputs/stage_gcg_full/asym_p3_arm07p_refusal_down_L18_poscorr_seed{42,43,44}/`
* `outputs/stage_gcg_full/asym_p3_arm07pr_refusal_rand_L18_poscorr_seed{42,43,44}/`

⚠ `asym_p3_arm07p_refusal_down_L18_poscorr_seed42_SMOKE3STEP` is a **3-step / batch-16 smoke**
and must never be scored — it carries a `DO_NOT_SCORE.txt` and any `asym_p3_*` glob will match
it.

## 5. The λ follow-up — **IN FLIGHT**, not deferred

**A λ probe is the single highest-value next experiment**, and it exists because of §1's
diagnostic rather than because of any result here. It is now **running**: λ = 10 ×
{mechanism, matched random} × seeds {42, 43, 44}, everything else identical to §2.

**The corrected diagnostic also made this experiment far more tractable than first estimated.**
From the understated 0.026 % share I extrapolated that ~50 % mechanism weight would need
λ ≈ 900 (≈3,600× published). From the corrected 0.370 % share the linear estimate is
**λ ≈ 34**, and the observed λ = 10 share is **22.7 %** — so meaningful weight is reachable at
**~40× the published λ, not ~3,600×**. The retracted number would have made this look
prohibitive; it is not.

### Early reading (λ = 10, seed 42, step 27/200 — diagnostic, no verdict)
| arm | task_loss moved | projection | refusal share |
|---|---|---|---|
| mechanism | **4.3** | +0.169 → **−0.074** (crosses zero) | **22.7 %** |
| matched random | **27.9** | +0.020 → +0.012 | 5.6 % |

λ = 10 does what it was meant to — real weight, projection driven past zero — **but the task
loss has nearly stopped improving.** That the two arms diverge this way is consistent with
Gate C: the refusal direction is *reachable*, so the optimizer profitably spends budget on it;
the random direction is not, so its λ term yields little gradient.

> **The finding may be that no λ both preserves the attack and gives the mechanism meaningful
> weight.** That would be a stronger and more general statement than either a positive or a
> negative at λ = 0.25.

**Binding reading rule (fixed 10:07, before these runs finish):** the λ arms' *internal-target*
number gets **no verdict** — single-seed quantities of that type proved unstable and produced
this sprint's one retraction. Only **ΔASR, consistent across all 3 seeds**, counts as evidence.
