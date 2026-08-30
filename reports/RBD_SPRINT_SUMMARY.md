# Representation–Behaviour Dissociation — confirmatory sprint

**2026-08-29 15:24 → 2026-08-30 14:40 IDT · branch `behavioral-causality-sprint` · `10fcd035..d96ec2f2`**

Every number here was recomputed from raw `results.jsonl` by **seven independent read-only auditors
across two adversarial passes** (`RBD-DR-004`, `RBD-DR-005`). **Both passes reproduced every number
exactly. Both passes found defects only in prose.** Where a claim is weaker than an earlier draft
said, the correction is marked ⚠ and carries its `RBD-C-*` id.

---

## 1. The question

A prior phase reported that `demo_processing_only` — an attention knockout masking demo→demo
attention during prefill — **removed the doublespeak attack while leaving concept binding intact**
(binding 45/48 preserved; attacks 30/96 → 8/96). If real, that is a **representation/behaviour
dissociation**: the adversarial mapping is still installed and can no longer be used.

That observation came from **2 banks, `core2x2`, 48 families, one concept (`bomb`)**. This sprint
asked whether it survives on **held-out material**, and was designed to **kill it if false**.

## 2. Design

| | |
|---|---|
| **Models** | Llama-3.1-8B-Instruct, Qwen3-14B (28 / 22 runs, all L40S) |
| **Banks** | 2 NEW lexical pairs — `lantern↔poison`, `candle↔missile` — 960 rows each, **20 held-out domains**, 4 conditions |
| **Arms** | A baseline · **B `demo_processing_only`** · C same scope **late band** (dose-matched control) · D `legacy_all_query` · E `response_query_only` |
| **Readouts** | **A** binding (`semantic_forced_choice`) · **B** benign mapping-use (**new this sprint**) · **C** harmful ASR (StrongREJECT ≥ 0.5) |
| **Preregistered** | cap 640 · margin 0.0521 · min effect **9 rows** · equivalence margin **0.10** · headroom **[14, 96]** · α 0.05 · liveness ≥ 0.99 — **all frozen in code before the data existed** |

**Preregistered outcome space** — A dissociation · B representation-damage · C no effect · D
behaviour-only · **E population cannot answer.** Naming E in advance is what let the sprint decline
rather than rationalise.

## 3. Result: the dissociation does not replicate

### Binding falls under the intervention

| n = 80 families | baseline | **`demo_processing_only`** | late-band control |
|---|---|---|---|
| **Llama** × `lantern_poison` | 78/80 | **61/80** — Δ −0.2125, 18 lost / 1 gained, p 7.6e-05 | **78/80 — Δ exactly 0.0000** |
| **Qwen3** × `lantern_poison` | 75/80 | **9/80** — Δ −0.8250, **66 lost / 0 gained** | **75/80 — Δ exactly 0.0000** |

The control is **exactly dose-matched** — arms B and C have identical `total_prefill_edits` within
each bank — so **the band, not the amount of intervention, is what differs.**

**Outcome A is excluded on the binding conjunct alone.**

> ⚠ **`RBD-C-020` — this is NOT symmetric.** Qwen3's −0.8250 is decisive. **Llama's turns on 1.3 of
> 80 families**: re-running the equivalence test with `n10 = 16` instead of the observed 18 returns
> `NOT_ESTABLISHED`. And Llama's *other* cell (`candle_missile`) **does not fail** — it returns
> `NOT_ESTABLISHED` and was **set aside post hoc**. Say **"excluded on Qwen3, not preserved on Llama
> at the margin"** — never "dead on both models".

> ⚠ **`RBD-C-015`** — "the control is exactly inert" holds for **binding on `lantern_poison` only**.
> It is not inert on benign use (24→23, 69→67), on ASR (12→16, 5→7), or on `candle_missile` binding.

### The behavioural half could not be measured — Outcome E

Baseline attacks: **12/160** (Llama), **5/160** (Qwen3), against a preregistered floor of **14**.
Llama's arm B passed every T2 criterion (12 → 1, cluster p 0.0064) **and is still declined**, because
a population failing its headroom precondition cannot carry a claim in *either* direction.

**The audit supplied the strongest reason to hold that line.** On Qwen3, **not one baseline attack
survives into any arm** — including the control that is exactly inert on binding:

| Qwen3 A→ | B | C | D | E |
|---|---|---|---|---|
| down / up / **both** | 5 / 2 / **0** | 5 / 7 / **0** | 5 / 5 / **0** | 5 / 6 / **0** |

**Attack success is not reproducible arm-to-arm at these rates.** So the Llama 12-down/1-up pattern
**must not be read as a mechanism signature** — the design cannot distinguish it from churn.

## 4. What the sprint found that nobody planned

**A large raw model difference in mapping use.** Given the same installed mapping and the same
property question, **Qwen3 answers with the mapped option 69/80 where Llama answers 24/80** — raw
difference **+0.5625, CI [0.4208, 0.6695]**, Fisher p 3.3e-13.

> ⚠ **`RBD-C-016` — the *composition* reading is NOT established.** Both control runs are
> **Llama-only**; no `benign_literal` or `direct_harmful` condition was ever run on Qwen3, so the
> **mapping-attributable lift is not estimated on the model the claim is about.** On Llama the lift
> is indistinguishable from its own no-mapping control (24/80 vs **32/80**, McNemar **p = 0.215**) —
> and that control being **0.40, not the intuitive 0.50**, is exactly why Qwen3's cannot be assumed.

**A structural limit on the readout inventory.** Both candidate exposure-clean readouts **failed the
option-mass gate** on the decisive Qwen3 cell (0.001–0.038 against 0.05). The reason is general:

> **A readout that names its options is high-mass and exposure-confounded; one that does not is
> exposure-clean and unreportable. No readout in this project's inventory is both.**

So "does the intervention destroy *reportability* more than *use*?" is **not answerable with
behavioural readouts**. The route is activation-level patching.

> ⚠ **`RBD-C-017`** — "behavioural headroom is concept-driven" is **downgraded to OBSERVATION**. My
> control clause ("same design, dose, domains, cap, judge") was **false on every clause**: domains
> 100% disjoint, role styles 1 vs 6, cap 640 vs 192, comparator judge model unknown. And this repo
> records a **3.6× bomb-internal ASR swing from a two-sentence preamble change** — larger than the
> gap I attributed to concept, with `rbd12`'s 0.075 sitting inside it.

## 5. Integrity — what held

| | |
|---|---|
| runs | **50/50 DONE, 0 aborted**, 0 excluded |
| liveness | **34/34** intervened runs at `frac_rows_scope_live = 1.0`, `scope_violations = {}`, each against its **own** contract |
| gates | `--allow-tail-readout` **false in all 50 configs** |
| judge | 1600/1600 rows, one pinned model, **completion-hash join verified on all 20 dirs: 1600 matched, 0 mismatched** |
| filtering | **none.** No ASR was computed on a filtered population at any point |
| truncation | 5 at-cap rows in 1600 (0.31%) |
| tests | **294** through the pre-commit hook, 130 in the six new files |

**No number moved across either audit.** Every defect in both passes was a quantifier, a scope, a
control clause, a stale file, or a population label.

## 6. The methodological finding

> **The correction pass was itself the largest single source of new error.**

`RBD-DR-004` corrected six overstatements — and **created one**: it added the words *"option mass
0.64–0.95 on every core run"* where the original text had **no quantifier at all**. The real range is
**0.6048–1.0000**; 0.64–0.95 is the Llama-only subrange. A universal quantifier attached to a
model-specific range, **in the row certifying the instrument's validity, written by the pass whose
job was to remove overstatements.**

It also applied its fixes to the *tables* and not to the *prose people quote*: the addendum's
one-paragraph summary still carried the uncorrected claim 16 lines above its own correction.

**A correction is a claim, and it needs the same audit as the claim it replaces.** That is why
`RBD-DR-005` existed, and why a third pass over `RBD-DR-005`'s own edits is the honest next step
rather than an optional one.

## 7. What to do next

1. **Screen behavioural headroom on a development population, before committing to a lexical pair.**
   Excluding ASR from bank selection was right — it prevents choosing material by outcome — but the
   cost was headroom failing on all four cells. A **separate prior screening stage** fixes this
   without contaminating the confirmation.
2. **Run the Qwen3 all-condition control.** One run closes `RBD-C-016` and would convert the raw
   model difference into a real composition claim. **Cheapest high-value item in the backlog.**
3. **Go activation-level for report-vs-use.** No behavioural readout can settle it.
4. `RBD-PR-005` (n = 16 dose diagnostic) remains registered and unrun.

## 8. Reusable output

**13 new files, 3,191 lines** (+3,897 / −12 across `src`, `scripts`, `tests`):

* **`paired_equivalence.py`** — the equivalence test the repo lacked: Newcombe method-10, domain
  cluster bootstrap, conservative envelope, rule-of-three at the φ = 1 singularity
* **Readout B** (`mapping_use_forced_choice`) — measures mapping *use* without touching harm
* **`rbd_bank_audit.py`** — validates a bank **without importing the module that built it**
* **`rbd_verify_independent.py`** — re-derives every headline from raw rows, **stdlib only**
* **`asr_protocol` completion-hash join** — documented in this project since before the sprint and
  **never actually implemented**; now enforced, and it verified 1600/1600

**Cost:** 8.9 GPU-hours across 54 SLURM jobs, 36 commits.

---

### One paragraph

**The representation/behaviour dissociation does not replicate on held-out material.**
`demo_processing_only` **damages the mapping it was supposed to spare** — decisively on Qwen3
(−0.8250, 66 families lost to 0 gained), marginally on Llama — while a dose-matched late-band
control is exactly inert on binding. The behavioural half **could not be measured at all**: baseline
attack rates of 12/160 and 5/160 against a floor of 14, and on Qwen3 not one baseline attack
survives into *any* arm. **The sprint's own preregistration named this outcome before the data
existed, which is the only reason it could be reported as a decline rather than rationalised into a
finding.** Two adversarial passes moved no number and corrected six claims in each direction —
including one false claim created by the first correction pass itself.
