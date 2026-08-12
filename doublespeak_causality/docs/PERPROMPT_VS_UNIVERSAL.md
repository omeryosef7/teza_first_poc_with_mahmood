# PER-PROMPT vs UNIVERSAL GCG — plan §7.5 (per Mahmood)

*Asymmetry sprint deliverable. **Written 2026-08-12, BEFORE any §7.5 run has been launched.***
*§1–§5 are pre-registered: methods, arms, and the exact reading rules are fixed now so the
result cannot be framed after the fact. §6 is empty and will be filled from the runs.*

---

## 1. The question, and why the existing negative cannot answer it

Our token-space negative is a **universal** suffix result: **one** suffix optimized on a train
pool and evaluated on frozen held-out prompts. The Gate-7 headline — **0.465 refusal vs 0.464
random** — is a **transfer** number (seeds 42+43, 50-step first cut, 20-item train pool → 42-item
held-out test).

A universal suffix failing to beat a matched random direction is consistent with **two very
different explanations**, and the universal setting **cannot distinguish them**:

* **H3 — objective failure.** The mechanism objective is a poor optimization target.
* **H1/H4 + §5.5 — universality failure.** The direction *is* reachable per prompt, but through
  **prompt-specific** token moves, so no single shared suffix can exploit it.

A per-prompt attack is **easier** than universal, is **still an unsolved and legitimate threat
model**, and **isolates the objective question from the universality confound**. That is the
experiment.

---

## 2. Design — and three corrections made before launch

Arms, each optimizing a **separate suffix per prompt** on the frozen **test** split (n = 37):

| arm | objective |
|---|---|
| **vanilla** | task loss only |
| **mechanism** | refusal projection at the validated **L18 / hs19** |
| **matched random** | norm-matched random direction, matched per §7.3 |

**3 seeds (42, 43, 44).** Held identical to the universal matrix: suffix length 16, topk 256,
`--no-filter-cand`, `suffix_placement=user`, `--selection-mode weighted`, greedy eval,
**StrongREJECT ≥ 0.5** (§3.6 governs; ≥0.25 reported as a secondary column only).

### Correction 1 — compute asymmetry (this experiment has TWO budgets, not one)
A per-prompt arm at 200 steps *per prompt* spends **~37× the optimizer compute** of the universal
arm, which spends 200 steps total. "Per-prompt beats universal" would therefore be
**uninterpretable** from the full-budget arm alone. So every arm is run at **both**:

* **full budget** — 200 steps/prompt. This is the *threat model*.
* **compute-matched** — ~5 steps/prompt (200 ÷ 37). This is the *fair contrast*.

**Both budgets are reported wherever a per-prompt-vs-universal number appears.** Neither alone is
sufficient, and quoting only the full-budget number would be the single easiest way to overstate
this result.

### Correction 2 — the two settings do not measure the same quantity
A per-prompt suffix is evaluated **on the very prompt it was optimized for**: there is **no
transfer component at all**. The universal number is a *transfer* result on held-out prompts.
Comparing them directly is apples-to-oranges.

**Therefore:** the per-prompt number is **never** labelled a held-out number, and the
apples-to-apples reference is reported alongside it — **the universal suffix's ASR on the same 37
prompts**.

*(This is not a §3.5 leakage violation: no layer, λ, threshold, seed or suffix is selected using
test outcomes. Hyperparameters are frozen from train; the per-prompt attack simply is the threat
model. But it is not a generalization measurement and must never be presented as one.)*

### Correction 3 — the baseline must be the position-corrected universal arms
At n = 1, `legacy_fixed` reduces **exactly** to `per_task_suffix` (its index is
`suffix_slice.stop - 1` computed from `train_tasks[0]`, which at n=1 *is* the prompt). So
comparing a per-prompt refusal arm against the **published legacy** universal arms would partly
measure **the D1 bug fix** rather than the per-prompt setting.

Baseline is therefore `asym_p3_arm07p*` / `arm07pr*` (**position-corrected**), and the per-prompt
arms pass **`--refusal-dir-position-mode per_task_decision`** — D1 vanishes at n=1, but **D2, the
within-task template offset, does not.** Verified from the universal arms' persisted
`CONFIG.json` that both settings use the **same** direction files.

---

## 3. Endpoints

1. **Per-prompt ASR** — each prompt contributes one Bernoulli outcome; pooled with a bootstrap CI.
   A single prompt's summary is **never** quoted on its own as "ASR".
2. **Internal refusal projection, before → after** the optimized suffix, per prompt (§19.1) — via
   `asym_p1c_mech_validity_ext.py --arm-perprompt`. **This is the core of what Mahmood asked
   for**, and it is what makes Gate E's "internal target must move" clause evaluable here.
3. **Refusal rate, empty rate, judge-failure fraction.**
4. **Transfer matrix** — prompt *i*'s suffix applied to prompt *j*.

---

## 4. Pre-registered reading rules

**The judge noise floor applies here unchanged.** Measured at **±0.03–0.08** on ASR at n = 37
(3.4 % label flips at `temperature = 0`). The per-prompt arms have the **same n = 37**, so **any
|ΔASR| below 0.08 is reported as within judge noise, not as an effect.** This is the rule that
retired the published +0.018 and it is not relaxed for a collaborator-requested experiment.

**Gate E, as amended §12:** a **per-prompt** positive is distinct from a **universal** positive. A
per-prompt-only positive **RE-SCOPES the universal negative — it does not overturn it** — and both
forms still require the intended internal target to move more than matched random.

| outcome | reading |
|---|---|
| **mechanism > random per-prompt, 3/3 seeds, above noise, AND projection moves more** | the negative is a **universality / prompt-specificity failure** (H1/H4, §5.5), *not* an objective failure. Re-scope the paper claim from *"the mechanism objective doesn't work"* to *"the mechanism objective doesn't transfer into a universal suffix."* |
| **mechanism ≈ random per-prompt** | a **stronger structural negative** — objective/reachability failure, independent of universality. This is the outcome that would most strengthen the current paper. |
| **ASR separates but the projection does not** | Gate E **fails** regardless of ASR. Report as non-mechanistic. |
| **sign inconsistent across the 3 seeds** | **no verdict.** Both of this sprint's retractions came from promoting a quantity that a further seed then flipped. |

### Transfer matrix
* **diagonal ≫ off-diagonal** ⇒ a **prompt-specific** token route (H1/H4 + §5.5) — this would
  *explain* the universal failure mechanistically rather than merely restate it.
* **diagonal ≈ off-diagonal** ⇒ the suffix is **generic**; per-prompt optimization bought nothing
  a universal suffix could not have found.
* **Analysis is paired BY SOURCE**: each source's own-prompt outcome against that same source's
  off-diagonal outcomes. Diagonal (n=37) and off-diagonal (n≈185) are *not* independent samples
  and must not be compared as two unpaired pools.
* **Subsampling is disclosed, not silent** (§3.15): default k = 5 off-diagonal targets per source
  (37×6 = 222 generations) versus the full 37×37 = 1369. The chosen k and the **exact sampled
  target ids** are recorded in the plan file. The diagonal is never sampled away.

---

## 5. Implementation note (§7.1 compliance)

**Zero changes to the optimizer, the objective, or the eval driver.** Per-prompt optimization is
expressible today by passing a **1-row manifest**; the transfer matrix works because the eval
driver already applies one run-dir's suffix to every row of a manifest and its row key is
`(task_id, suffix_label, seed)`. Total new code: five small data/plan/analysis scripts plus one
SLURM runner.

Two silent-failure modes are guarded, both of which would otherwise **exit 0 while producing
garbage**: an empty train list (now unreachable by construction — the parser accepts `{train,all}`
and the splitter emits `all`), and cross-prompt checkpoint resume (`config_hash()` excludes
`manifest_path` **and** `output_dir`, so two prompts sharing a directory would load each other's
checkpoint with no mismatch).

---

## 6. Results

**PENDING — not launched.** The 6-job cap is fully consumed by the λ = 10 probe. Next GPU action
is a **10-step 1-row smoke** to settle the unmeasured ~5 s/step estimate (no `n_train_tasks=1`
timing exists anywhere in `outputs/`) before sizing the sharded package.

Will be filled from `outputs/stage_gcg_perprompt/` via
`scripts/aggregate_perprompt_asr.py --mode {perprompt,transfer}`.
