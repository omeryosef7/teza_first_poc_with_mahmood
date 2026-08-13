# PER-PROMPT vs UNIVERSAL GCG — plan §7.5 (per Mahmood)

*Asymmetry sprint deliverable. **§1–§5 were written 2026-08-12 BEFORE any §7.5 run was
launched** — methods, arms and the exact reading rules were fixed in advance so the result could
not be framed after the fact. **§6 was added 2026-08-13 from the completed compute-matched runs**
and is read against those pre-registered rules, unchanged.*

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

## 6. Results — COMPUTE-MATCHED arm complete (3 seeds); full-budget arm still running

*Everything below is the **compute-matched** budget (~5 steps/prompt, matched to the universal
arm's 200 total steps). The **full-budget** arm (200 steps/prompt — the threat model) is running
and is reported separately when it lands.*

### 6.1 Behavioural — COMPLETE 3×3 matrix (ASR, n=37, judge_fail 0.0 throughout)
| arm | seed42 | seed43 | seed44 | mean | spread |
|---|---|---|---|---|---|
| **vanilla** (task loss only) | 0.0811 | 0.1892 | 0.1622 | 0.1442 | 2.33× |
| **mechanism** | 0.1892 | 0.1622 | 0.1892 | **0.1802** | **1.17×** |
| **matched random** | 0.1081 | 0.1622 | 0.1081 | 0.1261 | 1.50× |

**Paired contrasts (exact McNemar per seed):**

| contrast | seed42 | seed43 | seed44 | mean | sign-consistent? | significant |
|---|---|---|---|---|---|---|
| **mechanism − matched random** | +0.0811 | 0.0000 | +0.0811 | **+0.054** | **YES** (2 pos, 1 zero, **0 reversals**) | **0/3** |
| mechanism − vanilla | +0.1081 | −0.0270 | +0.0270 | +0.036 | **NO** | 0/3 |
| matched random − vanilla | +0.0270 | −0.0270 | −0.0541 | −0.018 | **NO** | 0/3 |

**Read carefully, because the three contrasts do not behave the same way:**

* **Only `mechanism − matched random` never reverses.** It is positive in two seeds and exactly
  zero in the third. That is the contrast §7.5 exists to measure, and it is **directionally
  consistent** — but the mean (**+0.054**) sits **below the ±0.03–0.08 judge floor** and **0 of 3
  seeds reach p < 0.05**.
* **Neither direction arm reliably beats vanilla.** Both of those contrasts flip sign across
  seeds. So the direction term does **not** dependably improve per-prompt attack success at all.
* **The mechanism arm is the most stable of the three** (spread 1.17× vs 2.33× for vanilla) —
  consistent with the sprint-wide finding that mechanism arms are stable and *contrasts* are not.

**Verdict against the §4 pre-registered rules: NOT a positive.** Gate E requires the contrast to
clear the noise floor **and** the internal target to move more than random. It clears neither: the
behavioural effect is sub-floor and never significant, and §6.2 shows the projection endpoint
fails outright (1 of 3, one reversal). **The consistent sign is worth reporting as an unresolved
weak signal — not as an effect.**

### 6.2 Mechanistic (§19.1 before→after projection) — the endpoint that IS adequately powered
| seed | mech drop | random drop | mech − rand | Wilcoxon p |
|---|---|---|---|---|
| 42 | −0.5233 | −0.1322 | **−0.3911** | **0.0092** |
| 43 | −0.3706 | −0.3699 | −0.0007 | 0.50 |
| **44** | −0.2459 | −0.3438 | **+0.0979** | 0.88 |

**1 of 3 significant; seed 43 an exact tie; seed 44 nominally reversed.** Holm across seeds leaves
only seed 42. **Gate E's internal-target clause is NOT met.** A continuous paired measurement at
n=37 is *not* power-limited the way binary ASR is, so unlike §6.1 this one is a **real** negative.

### 6.3 Per-prompt vs universal, at matched compute
| arm | ASR |
|---|---|
| per-prompt mechanism (mean of 3 seeds) | **0.180** |
| universal mechanism, λ=0.25 | 0.162 |
| universal random, λ=0.25 | 0.216 |

**No detectable per-prompt advantage** (+0.018, far inside the judge floor) — **and the comparison
is stacked in favour of per-prompt**, which is scored on the very prompts it optimized (zero
transfer) while the universal arm is scored on held-out transfer. Per-prompt does not win even
with that thumb on the scale.

### 6.4 What this says about the hypothesis §7.5 was added to test
**It argues against the universality-failure explanation (H1/H4 + §5.5).** If the universal
failure were caused by prompt-specific token routes, removing the universality constraint should
have helped. At matched compute it does not — on either endpoint. The discrete/objective
explanation is left standing, the same direction the λ probe pointed.

### 6.5 The methodological finding that outlived the result
**The per-prompt attack is highly reproducible; the CONTRAST against a single random control is
not.**

| quantity | spread across seeds |
|---|---|
| per-prompt mechanism ASR | **1.17×** (0.189 / 0.162 / 0.189) |
| λ=10 universal mechanism ASR | 6.25× |
| add-on 1 projection contrast | 582× |

In every collapsed contrast this sprint measured, **seed 42 had the weakest random control of its
set**, which inflated its contrast. §3.8 already mandates **≥50 random directions** for
reachability geometry; **behavioural and mechanistic contrasts currently use exactly one**, and
seeds vary the *suffix*, not the *direction* — so they never average over control-direction
variance at all. **That is the single highest-value methodological fix this sprint identified.**

---

### 6.6 FULL-BUDGET arm (200 steps/prompt — the threat model)

*Added 2026-08-14. seeds 42 and 43 complete on all three arms; seed 44 in flight.*

| arm | seed42 ASR | seed43 ASR | seed42 graded | seed43 graded |
|---|---|---|---|---|
| vanilla | **0.3514** | 0.2973 | **0.3311** | 0.2736 |
| mechanism | 0.2703 | **0.2973** | 0.2838 | **0.2838** |
| matched random | 0.3243 | 0.2162 | 0.2872 | 0.1892 |

**Paired mechanism − matched random:**

| seed | ΔASR | McNemar p | Δ graded | Wilcoxon p |
|---|---|---|---|---|
| 42 | **−0.0541** | 0.754 | −0.0034 | 0.944 |
| 43 | **+0.0811** | 0.453 | +0.0946 | 0.148 |

**Sign-inconsistent across seeds on both measures; nothing significant.**

**The three-arm ordering does not replicate either:**
* seed 42: mechanism **<** random **<** vanilla
* seed 43: random **<** vanilla **=** mechanism

Vanilla goes 1st→2nd, random 2nd→3rd, mechanism 3rd→1st. **No arm holds its rank.**

#### What the full-budget arm DOES establish
1. **Compute dominates direction.** The matched-random arm alone rises **0.1081 → 0.3243**
   (+0.216) from 5→200 steps/prompt — **three times the judge floor, and larger than any
   direction effect measured anywhere in this sprint.** This is design correction 1 confirmed
   empirically rather than argued: had §7.5 been run *only* at full budget, "per-prompt beats
   universal" would have followed — produced entirely by compute, using a **random** direction.
2. **Direction identity buys nothing at either budget**, on either measure.
3. **Per-prompt suffixes transfer.** Off-diagonal ASR **0.200** (mechanism) / **0.173** (random)
   — at or above the universal arm's own held-out ASR (0.162) — and the diagonal-vs-off-diagonal
   gap is **identical** for mechanism and random (+0.1243 both).

### 6.7 Mechanistic endpoint at full budget
| arm set | mech − rand | Wilcoxon p |
|---|---|---|
| FULL seed42 | −0.1981 | 0.295 |
| FULL seed43 | **−0.4502** | **0.063** |

At full budget the projection favours the mechanism in **both** seeds (one marginal), **while the
behavioural contrast in those same seeds flips sign**. On the same suffixes, same seeds, same
budget: **the internal target moves in the predicted direction and the behaviour does not
follow** — the program's representation ≠ behaviour dissociation, reproduced inside §7.5.
**Two seeds, one marginal: suggestive, not established.**

## 7. Still pending
* **seed 44** full-budget arms (all three) and its mechval — completes the 3×3 full-budget design.
  Cannot rescue an ordering that has already flipped; determines only which unstable ordering
  recurs.
