# DCS-PR-049: the three BLOCKING pre-analysis items

**Y1 power for a 2-way estimator · Y2 the hedge-free stratum · Y3 the register
re-measurement and its kill condition**

Script: `scripts/dcs_ts_pr049_blockers.py` — CPU only, no GPU, no model weights, no
SLURM, no network. The Llama-3.1-8B-Instruct tokenizer is loaded from the local HF cache
with `HF_HUB_OFFLINE=1` solely to count tokens.
Run: `python scripts/dcs_ts_pr049_blockers.py --reps 200 --n-perm 200 --mutate`
Preregistrations read and hash-verified at load: `configs/dcs_ts_pr049.json` (FROZEN
2026-09-07) and `configs/dcs_ts_pr048.json`, both through `scripts/dcs_ts_prereg.py`,
which refuses on a null sha, a hash that disagrees with disk, or a missing gate.

Every number below is re-derived from the raw bank JSONL rows. No producer-written
summary field is used as evidence: `n_chars` is recomputed from `full_prompt`, the
concept label comes from the file opened rather than the row's self-description, and
`demo_block ⊂ full_prompt` is asserted row by row.

**RESULT: 19 of 20 checks PASS on the real corpus; 11/11 mutations turn at least one
GREEN check RED.** Three of those mutations were GREEN on the first pass and each exposed
a real gap in the harness — they are documented in §5 rather than quietly fixed.

**The one failing check, `Y3-surf`, is a measurement and not a broken harness.** The
narrow hedge-only advantage on knife-vs-gun is +0.0348 and the preregistered kill
condition SURVIVES — but the broader *register-only* surface classifier on the same
contrast reaches **+0.2065**, which exceeds the same +0.10 bar. The kill condition is
written about hedges and is answered on its own terms; the surface result is a separate,
live limitation and is reported at full strength in §3e rather than folded into the
verdict it does not govern.

---

## 0. The population these three items bind to

| | |
|---|---|
| bank family | `ts116m`, all six banks (`{button,basket}` × `{bomb,knife,gun}`) |
| selector | field **`cell` == "C"** × `query_kind` == `semantic_one_word` × `n_examples` == 4 |
| exclusions | `restaurant_kitchen` (C-082) and `subway_station` (C-087), whole-population, both prompt-only, both prospective, both in TRAIN |
| rows bound | **6840** = 114 domains × 10 rows × 3 concepts × 2 codewords; 120 rows dropped by the two exclusions |
| per concept | bomb 2280 / knife 2280 / gun 2280 |
| domains | **114 analysed** = 68 train / 23 validation / 23 test, from `dcs_ts116_domain_split.json`, field `dsplit` |
| knife-vs-gun probe rows | train 2720 / test 920 (validation 920, untouched) |

**A side finding, measured rather than inherited (POP-03).** The preregistration's
`_cell_note` warns that selecting `condition == "natural_doublespeak"` instead of the
field `cell` binds ZERO rows (A-039). On ts116m that consequence **does not reproduce**:
the two selectors bind the *same* 6840 rows, set-identical on `(codeword, concept,
prompt_id)`. The instruction is still correct — select on `cell` — but its stated
consequence is corpus-specific, and a mutation built on it would have been a mutation
against nothing. That is why it is reported here as a measurement and not carried as a
guard. (`prompt_id` alone is *not* unique across the six banks — 6840 rows carry only
1140 distinct ids — which is itself a trap; the first version of this check compared six
collapsed sets and would have "passed" vacuously.)

---

## 1. Y1 — power for a 2-way estimator at chance 0.5

PR-048's power analysis (`scripts/dcs_ts_power.py`,
`reports/DCS_TS_POWER_ANALYSIS.md`) is computed for a 3-way contrast at chance
1/3 (0.333333) and **does not transfer** to a 2-way contrast at chance 0.5. The
estimators are reused — `t_mde`, `t_power`, `sign_power`, `perm_p`, `clopper_pearson`
are imported from `dcs_ts_power.py`, not re-implemented — so every difference below is a
difference of design, not of arithmetic.

### (a) The two-sided sign-test p-floor at n = 23 test domains

| quantity | value |
|---|---|
| attainable two-sided floor, 2 · 0.5²³ | **2.3842 × 10⁻⁷** |
| independent brute-force check (all 2²³ sign patterns enumerated) | 2.3842 × 10⁻⁷ (exact agreement) |
| one-sided floor | 1.1921 × 10⁻⁷ |
| distinct attainable p-values | 24 |
| domains above chance needed to reject at α = 0.05 | **k ≥ 17 of 23** |
| per-domain success probability for 80 % sign-test power | π ≥ **0.788** |

The floor is seven orders of magnitude below α, so the sign test's *floor* is never the
binding constraint. Its **k ≥ 17 of 23 requirement is** — see the verdict.

### (b) The permutation floor 1/(B+1)

| B | floor 1/(B+1) | smallest *measured* (non-floor) p, 2/(B+1) | below α? |
|---|---|---|---|
| 200 | 0.004975 | 0.009950 | yes |
| 2 000 | 4.998 × 10⁻⁴ | 9.995 × 10⁻⁴ | yes |
| **10 000** | **9.999 × 10⁻⁵** | 2.000 × 10⁻⁴ | yes |

`configs/dcs_ts_pr049.json` → `primary.n_perm` is read at runtime and **is 10000**;
the floor it fixes is 9.999 × 10⁻⁵, exactly as `_p_floor_rule` states. Confirmed. The
previous phase's headline `p = 0.004975` *was* the floor at B = 200 and was read as a
measurement; at B = 10000 a zero-exceedance result must still be published as
`p < 1/(B+1)`, never as a bare `0.0001`.

### (c) MDE in accuracy units above 0.5, α = 0.05, power 0.8, n = 23 domains

**There is no measured 2-way per-domain accuracy anywhere in the record.** The only
per-domain accuracies that exist are the six old 3-way ones. The between-domain SD is
therefore an **assumption**, and it is bracketed rather than picked:

| assumed SD | MDE @ α=0.05 | MDE @ Holm α=0.025 | what this SD is |
|---|---|---|---|
| 0.05 | 0.0306 | 0.0341 | ASSUMPTION — optimistic |
| 0.10 | 0.0611 | 0.0682 | ASSUMPTION — moderate |
| **0.1406** | **0.0859** | **0.0959** | ASSUMPTION — PR-048's *projected 3-way* SD, borrowed unchanged. A 3-way SD is not a 2-way SD. |
| 0.15 | 0.0917 | 0.1024 | ASSUMPTION — pessimistic |
| 0.20 | 0.1223 | 0.1365 | ASSUMPTION — very pessimistic |
| **0.25** | **0.1528** | **0.1706** | DISTRIBUTION-FREE CEILING: per-domain accuracies confined to [0.5, 1] have sample SD ≤ (1−0.5)/2 |
| 0.3439 | 0.2102 | 0.2347 | ASSUMPTION — PR-048's χ² 95 % upper bound on an SD estimated from SIX domains. *Exceeds* the [0.5,1] ceiling, so it is only reachable if some test domains fall below chance. |
| 0.50 | 0.3056 | 0.3412 | DISTRIBUTION-FREE CEILING on [0,1] |

Holm across the two primaries (PR-048 3-way, PR-049 2-way) at family-wise α = 0.05 means
the conservative planning α for this member is **0.025**, and that column is the one a
co-primary must survive.

Each reported MDE is round-tripped: `t_power(23, MDE, sd)` returns 0.800 ± 0.005 at every
SD in the bracket (check `Y1-c2`). Monotonicity alone would have passed an MDE computed
without the type-II term — which is how an MDE gets published ~40 % too small — so the
definition is checked, not just the shape.

Per-domain rows for this contrast: **m = 40** (10 rows × 2 concepts × 2 codewords), so
the binomial-noise-inflated projected SD is `sqrt(sd² + 0.25/40)`, listed in the JSON.

### (d) Power curves over n_test ∈ {12, 23, 29, 46}

Power of the one-sample t-test against 0.5, α = 0.05:

| SD | δ | n=12 | n=23 | n=29 | n=46 |
|---|---|---|---|---|---|
| 0.1406 | 0.050 | 0.203 | 0.371 | 0.456 | 0.656 |
| 0.1406 | 0.075 | 0.393 | 0.686 | 0.792 | 0.943 |
| 0.1406 | 0.100 | 0.613 | **0.903** | 0.959 | 0.997 |
| 0.1406 | 0.150 | 0.919 | **0.998** | 1.000 | 1.000 |
| 0.20 | 0.100 | 0.353 | 0.630 | 0.739 | 0.913 |
| 0.20 | 0.150 | 0.658 | **0.930** | 0.974 | 0.999 |
| 0.25 | 0.100 | 0.245 | 0.450 | 0.548 | 0.756 |
| 0.25 | 0.150 | 0.475 | **0.785** | 0.877 | 0.978 |
| 0.3439 | 0.150 | 0.282 | 0.516 | 0.621 | 0.825 |

Sign-test requirement by n: k ≥ 10/12, **k ≥ 17/23**, k ≥ 21/29, k ≥ 31/46; the π needed
for 80 % sign power falls only slowly with n (0.870 → **0.788** → 0.772 → 0.719).

### (e) FPR calibration on pure noise, through the full pipeline

200 replicates, no concept signal anywhere. Features carry a domain random effect (shared
by every row of a domain at every layer) plus a (layer, domain, concept) group random
effect — the real bank's nuisance structure, since all rows of one concept in one domain
share a demonstration pool. Domain-grouped 68/23/23 split; the **real** 36-candidate grid
(`layer_grid` 6–14 × `C_grid` {0.01, 0.1, 1, 10}) selected on **validation**;
domain-level group permutation (the 2! relabels of a 2-class arm), B = 200 per replicate.

| | |
|---|---|
| rejections at α = 0.05 | **8 / 200** |
| FPR | **0.0400**, 95 % Clopper-Pearson CI **[0.0174, 0.0773]** — covers nominal 0.05 |
| null domain-mean accuracy | 0.4951 (chance 0.5) |
| median p | 0.545 |
| candidates in the selection grid | 36 |

The pipeline is calibrated at chance 0.5. Two deliberate defects break it and both are
caught (§5): selecting the hyperparameters on TEST instead of VALIDATION, and permuting
at row level instead of domain level (which inflates the FPR to ≈ 0.17, matching the
3-way measurement that motivated the domain-level rule).

### (f) VERDICT — the call, made before any test read

The success rule in `primary.success` is a **conjunction**: significant by domain-level
group permutation **AND** above chance in a majority of test domains by two-sided sign
test. Powering only the permutation arm overstates the design. Modelling per-domain
accuracy as Normal(0.5 + δ, sd), the sign arm's per-domain success probability is
Φ(δ/sd) and its power is exact-binomial. The two arms read the same per-domain vector and
are positively correlated, so min(·) is an upper bound on the conjunction and the product
a lower bound; the verdict uses **min**, the generous one, so an inadequate call cannot be
an artefact of the bound.

At the planning bar **δ = +0.15** (a domain-mean of 0.65 on a 2-way contrast — far below
the +0.415 the old 3-way probe showed against its own chance):

| SD | t arm | sign arm | conjunction (α=0.05) | conjunction (Holm α=0.025) |
|---|---|---|---|---|
| 0.10 | 1.000 | 0.999 | 0.999 | 0.997 |
| **0.1406** | 0.998 | 0.963 | **0.963** | **0.900** |
| 0.15 | 0.996 | 0.940 | 0.940 | 0.855 |
| 0.20 | 0.930 | 0.748 | 0.748 | 0.575 |
| 0.25 (ceiling) | 0.785 | 0.550 | **0.550** | 0.365 |
| 0.3439 | 0.516 | 0.317 | 0.317 | 0.175 |

> ### **Y1 VERDICT: CO-PRIMARY.**
> **The number it rests on: conjunctive power 0.963 at α = 0.05 and 0.900 under the
> Holm-corrected α = 0.025, for δ = +0.15 at n = 23, at the working between-domain SD of
> 0.1406 — with MDE 0.0859 (Holm 0.0959).**

Three things this verdict is honest about, and they are part of the verdict, not
footnotes to it:

1. **The SD is borrowed, not measured.** 0.1406 is PR-048's *projected 3-way* value. No
   2-way per-domain accuracy exists yet.
2. **The binding arm is the sign test, not the permutation test** — at every SD in the
   bracket the sign arm is the weaker of the two. The design needs k ≥ 17 of 23 domains
   above 0.5, i.e. π ≥ 0.788. A result that clears the permutation test while landing at
   14/23 domains fails `primary.success` as written.
3. **The verdict flips at a computable SD, and that SD is checkable before any test
   read.** Conjunctive power falls below 0.80 at **SD = 0.188** (α = 0.05) and at
   **SD = 0.160** (Holm α = 0.025). At the distribution-free ceiling SD = 0.25 the
   conjunction is only 0.550 — *not* adequately powered.

**Preregistered contingency, recorded now:** PR-048 already requires a TRAIN-only nested-
LODO between-domain SD measurement before the confirmatory run (`power.flip_trigger`).
If the knife-vs-gun TRAIN-only between-domain SD exceeds **0.188** (or 0.160 against the
Holm α), this contrast is **demoted from CO-PRIMARY to EXPLORATORY**, decided on TRAIN
alone and before TEST is read. Under PR-048's existing 58/29/29 rebuild the same bar at
n = 29 would be met at SD ≈ 0.21.

---

## 2. Y2 — the hedge-free stratum, re-derived on ts116m

Hedge definition: the **narrow five families**, read out of the existing audit scripts
and not invented here — `scripts/dcs_ts116n_audit_leakage.py::HEDGE_PATTERNS` and
`scripts/dcs_ts116m_audit_concept_backing.py::HEDGE_NARROW`, which agree with each other
and with the preregistration's `_register_asymmetry` block:

```
resembl\w*      simulat\w*      \bdrills?\b      false alarm      look(s|ed|ing)? like
```

All five bind on ts116m (check `Y2-live`): **1248 of 6840** probe rows carry at least one
hedge in their demonstration block. A hedge-free count computed from a dead lexicon is
vacuous, so liveness is a check, not an assumption.

A row is *hedge-free* iff its **demonstration block** — the treatment — matches none of
the five.

### TEST-domain probe rows, per concept, with denominators

| concept | hedge-free / total | % | TEST domains with ≥ 1 hedge-free row |
|---|---|---|---|
| bomb | **248 / 460** | 53.9 % | 23 / 23 |
| knife | **452 / 460** | 98.3 % | 23 / 23 |
| gun | **420 / 460** | 91.3 % | 23 / 23 |

TRAIN, for reference: bomb 726/1360 (53.4 %), knife 1354/1360 (99.6 %), gun 1240/1360
(91.2 %) over 68/68 domains.

**The superseded ts116n figures 115 bomb / 212 knife / 195 gun are not quoted and are not
comparable** — they are recorded in the JSON only as the values being replaced. Every
number above is larger, and the ordering (bomb ≪ gun < knife) is the same asymmetry the
preregistration describes: bomb's discourse register is hedged, knife's essentially never
is.

### Balanced usable N

| | knife vs gun | all three concepts |
|---|---|---|
| balanced row-level N (2 × / 3 × the smallest arm) | **840** | **744** |
| domain-balanced N (min over concepts *within each domain*, summed) | **832** | 732 |
| usable TEST domains (≥ 1 hedge-free row in **every** arm) | **23 / 23** | **23 / 23** |
| MDE at that n_domains, SD 0.1406 / 0.25 | 0.0859 / 0.1528 | same |

The per-domain floor is high, not marginal: across the 23 TEST domains the hedge-free
count out of 20 rows runs knife 14–20 (median 20) and gun 10–20 (median 20). The
thinnest cells are `planetarium` (gun 10/20) and `lifeboat_station` (knife 14/20). Bomb
is the thin arm at 4–18 (`art_gallery` 4/20), which is why the 3-way stratum is smaller.

> ### **Y2 FEASIBILITY: YES — a balanced hedge-free re-analysis is feasible at the full
> n_domains = 23 for knife-vs-gun (balanced N = 840 rows, 832 domain-balanced), and at
> 23/23 domains for the 3-way stratum too (balanced N = 744).**

This stratum exists at the **domain** level, not only at row level — which is the
distinction that matters, because the domain is the independence unit. The
loss versus the full contrast is ~9 % of rows and **zero domains**, so the hedge-free
re-analysis costs no domain-level power at all relative to the primary. It remains a
SECONDARY robustness stratum under the preregistered multiplicity structure.

---

## 3. Y3 — the register re-measurement on ts116m

All classifiers: multinomial logistic regression, standardiser fit on **TRAIN domains
only**, evaluated on the 23 TEST domains, domain-grouped and disjoint (asserted, and the
assertion is itself mutated). **Validation is carried but never read.** Train 2720 rows /
68 domains, test 920 rows / 23 domains for each pairwise contrast. Chance for a 2-way
contrast is 0.5, so the advantage is reported as (accuracy − 0.5).

### (a,b) Hedge-only classifier — the five regexes as five count features

| contrast | accuracy | **advantage** | AUROC | domain-mean acc |
|---|---|---|---|---|
| **knife vs gun** | 0.5348 | **+0.0348** | 0.5353 | 0.5348 |
| bomb vs knife | 0.7217 | **+0.2217** | 0.7246 | 0.7217 |
| bomb vs gun | 0.6870 | **+0.1870** | 0.6911 | 0.6870 |

Measured on the full prompt instead of the demonstration block: knife-vs-gun +0.0370,
bomb-vs-knife +0.2109, bomb-vs-gun +0.1739 — the same picture, so the result is not an
artefact of which text field is read.

**The review's ts116n figures replicate on ts116m**: +0.211 → **+0.2217** on
bomb-vs-knife, +0.037 → **+0.0348** on knife-vs-gun. Register is confirmed as a
**bomb-vs-rest severity axis**, not a uniform nuisance: hedge-only buys 6.4× more on
bomb-vs-knife than on knife-vs-gun. This is the measurement PR-049 was built on, and it
holds on the live corpus.

### (c) Register-only classifier on knife-vs-gun

17 surface features: total hedge count, mean sentence length, sentence count, word count,
type-token ratio, mean word length, counts of `, . ; : - ' " ( ?`, digit count, uppercase
count.

| | accuracy | **advantage** | AUROC |
|---|---|---|---|
| register-only (17 features) | 0.7065 | **+0.2065** | 0.7479 |
| register-only, **length-free** (hedge rate and punctuation counts per word, TTR, mean word length; every raw length channel removed) | 0.6870 | **+0.1870** | 0.7315 |

The length-free variant retains 91 % of the advantage (+0.1870 of +0.2065), so **this is
not length wearing a different name** — it is lexical/orthographic composition. The
surface of a knife demonstration block and the surface of a gun demonstration block
differ enough for a 17-feature logistic regression to separate them at 0.71 accuracy on
held-out domains.

### (d) Length-only classifier on knife-vs-gun, characters **and** tokens

| | accuracy | advantage | AUROC |
|---|---|---|---|
| length in **characters** (full prompt + demo block) | 0.6174 | **+0.1174** | 0.6537 |
| length in **TOKENS** (Llama-3.1-8B-Instruct, offline) | 0.5435 | **+0.0435** | 0.5466 |

C-084 again, on the 2-way contrast this time: the character figure (+0.1174) is nearly
three times the token figure (+0.0435), and **the token figure is the honest one** —
the model reads tokens. Measuring length in characters here would have overstated the
length confound by 0.074 accuracy. The tokenizer is a hard requirement of this script:
withholding it turns two checks RED rather than silently falling back to characters.

### THE KILL CONDITION

`configs/dcs_ts_pr049.json` → `kill_condition`, declared 2026-09-07 before this
measurement existed and read out of the config at runtime (the analyzer refuses if the
string no longer names +0.10):

> *"If Y3 shows the hedge-only advantage on knife-vs-gun is NOT small — say it exceeds
> +0.10 — then this contrast is not register-clean and its whole rationale fails. In that
> case it is withdrawn rather than reported."*

Measured: hedge-only knife-vs-gun accuracy **0.5348** on 920 TEST rows over 23 domains,
advantage **+0.0348**, AUROC 0.5353, domain-mean advantage +0.0348.

> ### **Y3 KILL CONDITION: SURVIVE — the hedge-only advantage on knife-vs-gun is +0.0348, against a threshold of +0.10.**

The measurement clears the threshold by a factor of nearly three, and it clears it in the
same direction and at nearly the same magnitude as the ts116n figure that motivated the
preregistration. PR-049 is **not** withdrawn.

### (e) THE SURFACE RESULT — a failing check, reported at full strength

`Y3-surf` states the claim that the broader register-only classifier also stays within
+0.10 on knife-vs-gun. **It does not, and the check FAILS.**

| classifier on knife-vs-gun | advantage | within +0.10? |
|---|---|---|
| hedge-only (the five families) — *what the kill condition governs* | **+0.0348** | yes |
| length-only, TOKENS | +0.0435 | yes |
| length-only, characters | +0.1174 | **no** |
| register-only, length-free | +0.1870 | **no** |
| register-only, all 17 surface features | **+0.2065** | **no** |

This does **not** trigger the kill condition, and it is not treated as if it did: the
kill condition is written about the hedge-only classifier and about nothing else, it was
frozen in that form before the measurement existed, and rewriting its scope after seeing
this number would be exactly the move the freeze exists to prevent. `Y3-kill` is
SURVIVE and stays SURVIVE.

But the preregistration's *rationale* is broader than its kill condition. `_why_this_exists`
says knife-vs-gun "is clean on register AND on length". On ts116m that sentence is **only
partly supported**, and the correction belongs in the record before the probe runs:

* **Clean on hedges** (+0.0348) — supported, and it replicates the ts116n figure.
* **Clean on token length** (+0.0435) — supported; token length is not a live confound,
  consistent with C-084.
* **Clean on character length** (+0.1174) — *not* supported, though C-084's argument that
  the model reads tokens applies here too and downgrades this channel.
* **Clean on surface register generally** (+0.2065, +0.1870 length-free) — **not
  supported.**

The consequence is a bar, not a withdrawal, and it is the bar the preregistration already
names: the N5 concept-masked TF-IDF baseline is the instrument for residual surface
signal, and **the probe must beat it**. What Y3 adds is a concrete floor that the N5 bar
now has to clear on this contrast — a surface classifier reaching 0.7065 domain-mean
accuracy on knife-vs-gun. A probe result near 0.71 on this contrast would be
uninterpretable as concept identity. That floor should be recorded alongside the primary
statistic when the confirmatory run reports.

---

## 4. What every check binds to

| check | binds | result |
|---|---|---|
| POP-01 | 6840 rows, primary dose only, exact count + domain count + arm balance | PASS |
| POP-02 | 68/23/23 domains, no unassigned row | PASS |
| POP-03 | `cell` vs `condition` selector equivalence, measured on ts116m | PASS |
| Y1-00 | PR-049 chance 0.5 ≠ PR-048 chance 1/3 | PASS |
| Y1-a | sign floor, closed form vs 2²³ brute force | PASS |
| Y1-b | permutation floors; `primary.n_perm` == 10000 | PASS |
| Y1-c | MDE monotone in SD, every SD labelled | PASS |
| Y1-c2 | each MDE attains 0.800 power (definition round-tripped) | PASS |
| Y1-d | power monotone in n_test | PASS |
| Y1-e | FPR on pure noise covers nominal α and null sits at 0.5 | PASS |
| Y1-V | the CO-PRIMARY verdict, under the conjunctive rule | PASS |
| Y2-live | all five hedge families bind non-zero rows | PASS |
| Y2-count | hedge-free counts per concept with denominators | PASS |
| Y2-feas | ≥ 12 TEST domains usable in **both** knife and gun arms | PASS |
| Y3-split | train/test domain-grouped and disjoint; validation untouched | PASS |
| Y3-tok | tokenizer loads offline; token counts available | PASS |
| Y3-kill | the preregistered kill condition | PASS (SURVIVE) |
| Y3-asym | register is a bomb-vs-rest axis, not uniform | PASS |
| Y3-reg | register-only and length-only measured, tokens included | PASS |
| Y3-surf | the surface caveat, reported whichever way it lands | **FAIL** — register-only is +0.2065, above +0.10; a measurement, not a harness defect (§3e) |

The failing check is left failing. It is not rewritten to a threshold it clears, and
its claim is not narrowed after the fact; the run exits non-zero because the corpus did
not satisfy a claim the harness stated.

Every check fails loudly on zero binding: `Checks.add` overrides `ok` to False whenever
`n_bound == 0`, and `require_nonempty` raises `ZeroBinding` before any statistic is
computed over an empty set.

---

## 5. Mutation harness — and the three gaps it found

`--mutate` re-runs the whole harness under 11 deliberate defects. **A mutation counts
as caught only if it turns RED one of the 19 checks that are GREEN on the real corpus** —
`Y3-surf` is already RED there, so crediting it would hand every mutation a catch it did
not make. (The first mutation run did exactly that before the accounting was fixed.)

| mutation | what it does | checks turned RED |
|---|---|---|
| `pool_doses` | pools the n_examples=8 replication dose into the primary cell (`_dose_rule` forbids it) | POP-01 |
| `empty_population` | selects cell "Z" | raises `ZeroBinding` before any statistic |
| `keep_excluded_domains` | stops excluding `restaurant_kitchen` / `subway_station` | POP-01, POP-02 |
| `corrupt_split` | puts 5 TEST domains into TRAIN as well | POP-02, Y2-count |
| `dead_hedge_lexicon` | a hedge lexicon matching nothing | Y2-live |
| `hedge_leak` | appends "It resembled a device." to every GUN demo block | Y2-feas, Y3-kill, Y3-asym |
| `row_level_permutation` | permutes labels at ROW level in the FPR simulation | Y1-e |
| `test_selected_hyperparams` | selects layer/C on TEST rather than VALIDATION | Y1-e |
| `mde_drop_beta` | computes the MDE without the type-II term | Y1-c2 |
| `perm_floor_naive` | uses the naive `#{null ≥ obs}/B` p (floor 0) | Y1-b |
| `no_tokenizer` | withholds the tokenizer | Y3-tok, Y3-reg |

`hedge_leak` is the important one: it is the defect the kill condition exists to catch,
and it does flip `Y3-kill` from SURVIVE to KILL. A kill condition that could not go off
would not be a kill condition.

### The three mutations that came back GREEN on the first pass

Each was a genuine hole in the harness, not a mutation that "didn't apply". They are
recorded because the fix is the finding.

1. **`wrong_cell_field` was GREEN because it is not a defect on this corpus.** Selecting
   `condition == "natural_doublespeak"` binds exactly the same 6840 rows as `cell == "C"`
   on ts116m; A-039's zero-binding failure is corpus-specific. The mutation was replaced
   with `pool_doses` (a real violation of the preregistration's `_dose_rule`), and the
   selector equivalence became the positive measurement POP-03. Building the new
   POP-03 then exposed a second trap: `prompt_id` is shared across the six banks, so the
   first version compared six collapsed 1140-element sets and would have passed
   vacuously. It now keys on `(codeword, concept, prompt_id)` and asserts the set size
   equals the row count.
2. **`row_level_permutation` was GREEN because the mutation arm ran at only 20 FPR
   replicates.** Row-level permutation genuinely inflates the FPR to ≈ 0.17 against a
   nominal 0.05, but at 20 replicates the Clopper-Pearson interval is [0.004, 0.32] and
   still covers 0.05, so the check could not see it. The mutation arm now runs at 100
   replicates and `Y1-e` additionally requires the point estimate to stay within 2α. An
   under-powered check is not a check.
3. **`mde_drop_beta` was GREEN because `Y1-c` only tested monotonicity.** Dropping the
   type-II term shrinks every MDE by roughly 40 % while leaving the curve monotone
   increasing in SD, so a shape check passes an MDE that is wrong by a factor. `Y1-c2`
   now round-trips the definition: `t_power(23, MDE, sd)` must return 0.800 ± 0.005.
   This is the same family as "a check that reads the same broken source" — a check that
   tests a property the defect preserves.

**11 / 11 mutations turn at least one GREEN check RED.**

---

## 6. Three-line summary

1. **Y1 — CO-PRIMARY.** Conjunctive power (domain-level permutation **and** two-sided
   sign test) is **0.963** at α = 0.05 and **0.900** under the Holm-corrected α = 0.025
   for δ = +0.15 at n = 23, at the borrowed working between-domain SD of 0.1406
   (MDE 0.0859 / 0.0959); the binding arm is the sign test (k ≥ 17 of 23), and the call
   flips to EXPLORATORY if the TRAIN-only between-domain SD exceeds **0.188** — checkable
   before any TEST read.
2. **Y2 — FEASIBLE at the full n_domains = 23.** On ts116m the TEST hedge-free stratum is
   **bomb 248/460, knife 452/460, gun 420/460**; all 23 TEST domains carry hedge-free
   rows in every arm, giving a balanced knife-vs-gun N of **840 rows** (832
   domain-balanced) and a 3-way N of 744 — the stratum exists at the domain level, not
   only at row level. The superseded 115/212/195 figures are retired.
3. **Y3 — SURVIVE.** The hedge-only advantage on knife-vs-gun is **+0.0348**
   (accuracy 0.5348, AUROC 0.5353, 920 TEST rows / 23 domains) against the preregistered
   kill threshold of **+0.10**, and the ts116n motivating figures replicate
   (bomb-vs-knife **+0.2217** vs +0.211; knife-vs-gun +0.0348 vs +0.037) — so the
   contrast is register-clean in the sense the kill condition names and PR-049 is **not
   withdrawn**; but the broader register-only surface classifier reaches **+0.2065**
   (+0.1870 with every length channel removed) on the same contrast, so "clean on
   register generally" is *not* supported and the N5 bar the probe must beat now has a
   measured floor of 0.7065.
