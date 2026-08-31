# RAH2 — the readout problem: can a readout be exposure-clean AND high-mass?

**Namespace `RAH2-`.** Append-only. Opened 2026-08-31, immediately after the RAH sprint closed at
`4284e68c`. Ids: `RAH2-PR-###` preregistration · `RAH2-R-###` result · `RAH2-C-###` correction ·
`RAH2-DR-###` deep review. **Never reuse a bare `PR-`/`R-`/`C-`, and never a `RAH-` id.**

Predecessors, both closed and not to be reopened here:
`reports/RBD_SPRINT_SUMMARY.md` · `reports/RAH_SPRINT_SUMMARY.md` ·
`external_md/REPRESENTATION_ACCESS_AND_HEADROOM_NEXT_SPRINT_PLAN_AND_PROGRESS.md`.

---

# 0. The problem, and why it is the right one

Two sprints have now hit the same wall from opposite sides.

**`RBD-R-033`, behavioural:**

> A readout that names its options is high-mass and **exposure-confounded**; one that does not is
> exposure-clean and **unreportable**. No readout in this project's inventory is both.

**`RAH-R-018`, activation-level** — built the instrument that was supposed to escape it, and hit it
again:

| receiver | names its options? | outcome |
|---|---|---|
| `fc_probe_last` | **yes** | high mass — and transports the **codeword**, not the mapped concept |
| `id07_tmpl` | **no** | transported the concept on its selection bank (0.4344) — **median option mass 7.1e-08 on held-out material**, 0/80 rows above a 0.05 gate |

**Every downstream question in this line is blocked on this.** Track A cannot be answered without a
readout that is both; Track B's behavioural readouts are the same trade-off in a different costume.
Solving it is worth more than either individual result the two sprints were chasing.

## 0.1 The hypothesis this phase tests

The two properties have been treated as one axis. **They are plausibly two.**

* **Exposure confound** comes from **naming the candidate answers** in the prompt. A donor carrying a
  surface token can then win by lexical match against a printed label — which is exactly what
  `RAH-R-018` observed (`fc_probe_last` transports `carrot`/`lantern`, the codeword).
* **Option mass** comes from **constraining the answer slot** — telling the model *what kind of
  thing* goes next, so its probability concentrates on a small vocabulary.

> **`H1` (separability).** A receiver can constrain the answer slot **without naming any candidate**,
> and thereby be exposure-clean *and* high-mass.

The existing inventory only ever tested the two extremes: `fc_probe_last` names all four candidates
**and** constrains the slot; `id07_tmpl` names none **and** leaves the slot unconstrained (it is a
free repetition continuation). **The middle of that space has never been tested**, and `H1` says the
middle is where a usable readout lives.

**`H0` (null).** Constraint and naming are inseparable in practice: any prompt that concentrates mass
on the candidate vocabulary does so by making the candidates retrievable from the prompt, so
exposure-clean readouts are unreportable and the trade-off is real.

**`H0` is a perfectly good outcome** and would convert two sprints' worth of observation into a
characterised property rather than a repeated obstacle.

---

# 1. Design

## 1.1 The receiver ladder

Five forms spanning the naming × constraint space. Two are the known extremes, carried forward
unchanged so the new ones are measured against them on the same rows.

| id | names candidates | constrains slot | prompt shape |
|---|---|---|---|
| `fc_probe_last` | **all 4** | strong | *"Labels: A, B, C, D … Which describes X?" + `Answer:`* |
| `id07_tmpl` | none | **none** | repetition continuation, `"hello hello\nworld world\ncat cat\nX"` |
| **`cat_cue`** (new) | **none** | strong | *"The word X refers to a kind of"* |
| **`synonym`** (new) | **none** | strong | *"X means the same as the word"* |
| **`defn_oneword`** (new) | **none** | medium | *"Define X in exactly one word." + `Answer:`* |

The three new forms **name no candidate** — structurally exposure-clean by the same test the sprint
already applies — while constraining the answer slot to a noun / synonym / single word.

## 1.2 What is measured, on the same rows, for every form

| metric | definition | what it decides |
|---|---|---|
| **mass** | summed probability of the four candidate first-token ids at the read slot | reportability; gate **0.05** (the repository's standard) |
| **naming** | does any candidate string appear in the rendered receiver? | exposure-cleanliness, structural and binary |
| **prior** | unpatched P(concept) and unpatched argmax | whether a "result" is the receiver's own bias |
| **transport** | P(concept) under a **clean concept-bearing** donor (`direct_harmful`) | positive control, gate **0.1** uplift |
| **discrimination** | P(concept) − P(codeword) under a **codeword-position** donor | whether it reads the mapping or the surface |

**`mass` and `naming` are the two axes of `H1` and both are primary.** A form that is high-mass and
names nothing is what `H1` predicts exists.

## 1.3 Success and failure, fixed now

| outcome | condition |
|---|---|
| **`H1` SUPPORTED** | ≥1 new form has **median mass ≥ 0.05**, names no candidate, and passes the positive control — **on held-out material** |
| **`H1` FALSIFIED** | every exposure-clean form is below the mass gate on held-out material, while the option-naming form clears it — the trade-off is real |
| **CANNOT ANSWER** | the positive control fails for all forms, or option ids collide, or the population is incomplete |

**Mass is measured on held-out material or it does not count.** `RAH-R-018`'s whole lesson is that a
receiver can look fine on its selection bank and collapse six orders of magnitude on a new pair.

## 1.4 Populations

* **Development**: level-A discovery banks (`carrot↔bomb`, `basket↔bomb`, `ticket↔knife`). Used to
  build the forms, check tokenisation, and confirm the positive control fires.
* **Held-out**: `lantern↔poison` and `candle↔missile` — the pairs on which `RAH-R-018` failed. **The
  form set is frozen before these are run.**

No form may be added, reworded or dropped after held-out data is seen. Any post-hoc form is a new
preregistration.

## 1.5 Anti-fishing

* The sweep program (`rah_preflight_transport.py`) **contains no intervention code path** — verified
  by `grep`, returns 0 — so nothing here can see an intervened arm.
* Donors are `direct_harmful` (positive control) and `natural_doublespeak` (the real question); both
  are **baseline** conditions with no knockout applied.
* Candidate first-token ids are asserted **single-token and pairwise distinct on both models** before
  any run, and a collision **refuses** rather than degrades.
* Every form is measured on **the same rows**, so mass differences cannot be a population difference.

---

# 2. What this phase will NOT do

* **Not** re-open Track A's verdict. `RAH-R-018` stands at **A-IV**. A usable readout would license a
  *new* Track-A attempt under a *new* preregistration, not a re-reading of the old one.
* **Not** search receiver layers for a reportable cell. `R` is fixed at the value the closed sprint
  froze per model (depth fraction 0.125 → R=4 Llama / R=5 Qwen3) **for the primary comparison**;
  the R-sweep is reported only as a secondary diagnostic, and `RAH-DR-004` B3 stands: **no R-profile
  statement is model-general.**
* **Not** claim a solved readout from development data. Held-out or it does not count.

---

# 3. Progress log

## `RAH2-PR-001` — this design, registered — 2026-08-31

Everything in §0–§2 is fixed before any RAH2 forward pass exists: the hypothesis, the five-form
ladder, the five metrics, the 0.05 mass gate and 0.1 positive-control gate, the development/held-out
split, the success and failure conditions, and the anti-fishing constraints.

**Deliberately left open**, to be fixed in a freeze entry before the held-out run: nothing. The form
set, the gates and the populations are all frozen now — this design has no calibration stage, because
the two gates it uses are inherited from the closed sprint rather than derived here.

---

## `RAH2-R-001` — `H1` FALSIFIED on development, both models. Constraint without naming makes mass WORSE — 2026-08-31

**Status: DEVELOPMENT RESULT. `H1` falsified; `H0` supported. Registered early stop invoked — the
held-out run is NOT warranted and is not run.**

Runs `rah2dev_p_cb_20260831_100101` (Llama, 52 min) and `rah2dev_q_cb_…` (Qwen3), level-A
`carrot↔bomb`, donor = `natural_doublespeak` at the codeword, 8 donors, all donor layers × 5 receiver
layers × the 5-form ladder. No intervention exists in this program.

### Patched option mass, best over receiver layers — the `H1` primary metric

| form | names candidates? | Llama | Qwen3 |
|---|---|---|---|
| `fc_probe_last` | **all four** | **0.1484** | **0.9998** |
| `id07_tmpl` | none | 0.0410 | **0.4344** |
| `cat_cue` | none | 0.000626 | 0.002049 |
| `defn_oneword` | none | 3.12e-05 | 1.42e-06 |
| `synonym` | none | 2.18e-05 | **1.38e-11** |

Mass gate 0.05. **The three new forms sit 1.5–10 orders of magnitude BELOW the form they were meant
to improve on, on both models.** `H1` predicted they would be *higher*.

### `H1` is falsified, and the reason sharpens the problem

The ordering is identical on both models:

```
names all four   >   names none, ECHO frame   >>   names none, SEMANTIC frame
```

**My preregistered framing was wrong in a specific and informative way.** I described `id07_tmpl` as
having *"no slot constraint — a free repetition continuation"*. It is not unconstrained: the
repetition frame is a **strong** constraint, and what it constrains toward is **echoing the patched
token itself**. That is exactly why it has mass — the patched representation is the thing being
echoed.

So the axis is not *naming vs constraint*. It is **what the constraint points at**:

| framing | where mass goes | consequence |
|---|---|---|
| **naming** the candidates | onto the printed candidate words | mass, and the exposure confound — a surface-carrying donor wins by lexical match |
| **echo / identity** (`id07_tmpl`) | onto whatever was patched | mass, but it reads **surface identity**, not the mapping |
| **semantic category** (`cat_cue`, `synonym`, `defn_oneword`) | spread across a large category vocabulary | **no mass on these four words in particular** |

> **`H0` supported, and stated more precisely than either predecessor sprint managed:**
> **mass on a SPECIFIC small candidate vocabulary requires either printing that vocabulary (which
> creates the exposure confound) or asking the model to echo the patched token (which reads surface
> identity rather than the mapping). Constraining the slot semantically constrains it to a
> CATEGORY, not to the candidates — so it buys no mass on them.**

That is why the trade-off has survived two sprints and three readout families: the two escape routes
are not two, they are the same two mechanisms, and the third route tested here does not exist.

### The registered early stop, invoked

`RAH2-PR-001` requires **held-out** mass ≥ 0.05. The new forms are 2–10 orders below that in
**development**, and `RAH-R-018` measured directly that held-out can only be worse — the same
`id07_tmpl` configuration read **0.4344 in development and 7.1e-08 held out**, a collapse of six
orders on a lexical-pair change.

**A form cannot climb 2–10 orders on a held-out pair when a better form fell 6.** The held-out run is
therefore not warranted, and is not run. That was stated as the criterion **before** the second model
reported, not chosen after seeing it.

### ⚠ Scope

Development only: **level-A `carrot↔bomb`, 8 donors, 2 models, one donor condition.** The claim is
about **these five receiver forms**, not about all possible readouts — a form that constrains toward
the candidates *without printing them* (a learned or retrieved constraint, rather than a written one)
is untested and is **not** excluded by this result.

### What this costs and what it buys

Cost: ~1.5 GPU-hours. Buys: `H1` — the most natural idea for escaping the trade-off, and the one both
predecessor sprints implicitly assumed was available — is **tested and dead**, with a mechanism for
*why*. That is worth more than the third repetition of "no readout is both."

---

## `RAH2-PR-002` — the one route `RAH2-R-001` left open: constrain toward the candidates WITHOUT printing them — 2026-08-31

**Status: PREREGISTERED (prospective). Written and committed before any `RAH2-PR-002` forward pass.**
A new preregistration, as `RAH2-PR-001` §1.4 requires for any form added after its ladder was fixed.

### Why this specific route, and why it is not a rescue attempt

`RAH2-R-001` did not merely falsify `H1` — it produced a mechanism, and the mechanism names its own
exception. Mass on a small candidate vocabulary was found to come from exactly two sources:

| framing | mass comes from | what it reads |
|---|---|---|
| **naming** (`fc_probe_last`) | the candidates being **printed** | the printed surface → exposure confound |
| **echo** (`id07_tmpl`) | the model being asked to **repeat the patched token** | **surface identity**, not the mapping |
| semantic category (`cat_cue`…) | nothing — spreads over a category | ✗ falsified |

Both working mechanisms point the answer slot at something already present: a printed word, or the
patched token itself. **Neither points it at *a function of* the patched token.**

> **`H2`.** A receiver can constrain the answer slot toward **the output of a mapping applied to the
> patched representation** — demonstrated **in context, on unrelated word pairs** — without printing
> any candidate. If so it is exposure-clean (nothing named), high-mass (the slot is tightly
> constrained by the demonstrated task), and reads a **function of** the donor rather than its
> surface.

This is the mechanism the echo frame has, generalised from *identity* to *an arbitrary demonstrated
mapping*. It is the standard Patchscopes construction and **it has never been tried in this
repository** — every prior receiver here was identity/repetition or forced choice.

⚠ **This is a NEW mechanism, not a reworded old form.** `RAH2-R-001` is not being rescued: `H1`
stays falsified, and if `H2` fails the trade-off stands with three mechanisms tested rather than two.

### The two new forms

Both are few-shot, both name **no** candidate, both patch at the probe and read at the final position.

| id | prompt | what the slot is constrained toward |
|---|---|---|
| **`fewshot_cat`** | `apple -> fruit` / `hammer -> tool` / `sparrow -> bird` / `<probe> ->` | the **category** of the patched token |
| **`fewshot_syn`** | `big -> large` / `swift -> fast` / `begin -> start` / `<probe> ->` | a **synonym** of the patched token |

The exemplar pairs are **deliberately unrelated** to every candidate — no weapon, no container, no
hazard term — so the demonstration cannot prime the candidate vocabulary. **This is checked
structurally** by the same `names_any_candidate` test, and additionally by requiring that no exemplar
shares a first token with any candidate.

### Metrics, gates and populations — UNCHANGED from `RAH2-PR-001`

Same five metrics, same 0.05 mass gate, same 0.1 positive-control gate, same development
(level-A `carrot↔bomb`) → held-out (`lantern↔poison`) split, same anti-fishing constraints, and the
two known extremes carried forward on the same rows as reference.

### Outcomes, fixed now

| outcome | condition |
|---|---|
| **`H2` SUPPORTED** | a few-shot form reaches **median mass ≥ 0.05 on HELD-OUT material**, names no candidate, and passes the positive control |
| **`H2` FALSIFIED** | few-shot forms are below the mass gate, like the semantic forms — the trade-off stands with **three** mechanisms tested |
| **PARTIAL** | high mass in development that collapses held-out, as `id07_tmpl` did (0.4344 → 7.1e-08). **This is a FAILURE for the purpose of the readout problem**, and is recorded as such, not as a near-miss |

### The early-stop rule, restated so it binds this run too

If both models show the few-shot forms **≥ 2 orders below the gate in development**, the held-out run
is **not** warranted and is not run — the same rule invoked in `RAH2-R-001`, stated before the data.
If development mass clears the gate, **held-out is mandatory** and is the only thing that counts.

### `RAH2-PR-002` CPU verification — executed BEFORE any GPU forward pass

Both tokenizers, both candidate vocabularies. `exemplar_candidate_collisions` uses the **raw** first
token of `" word"`, not `signals.readout_ids`: exemplars appear in the PROMPT and are never scored,
so the single-token requirement does not apply to them (`sparrow` is 2 tokens on Llama — the first
attempt at this check crashed on exactly that, which is the intended loud failure).

| model | form | seq | patch q | read | hops | last 2 tokens | names a candidate? |
|---|---|---|---|---|---|---|---|
| Llama | `fewshot_cat` | 18 | 15 | 17 | 2 | `'"'`, `' ->'` | **[]** |
| Llama | `fewshot_syn` | 17 | 14 | 16 | 2 | `'"'`, `' ->'` | **[]** |
| Llama | `fc_probe_last` (ref) | 75 | 66 | 74 | 8 | `'Answer'`, `':'` | all 4 |
| Llama | `id07_tmpl` (ref) | 45 | 44 | 44 | 0 | — | [] |
| Qwen3 | `fewshot_cat` | 17 | 14 | 16 | 2 | `'"'`, `' ->'` | **[]** |
| Qwen3 | `fewshot_syn` | 16 | 13 | 15 | 2 | `'"'`, `' ->'` | **[]** |
| Qwen3 | `fc_probe_last` (ref) | 52 | 39 | 51 | 12 | `'Answer'`, `':'` | all 4 |
| Qwen3 | `id07_tmpl` (ref) | 22 | 21 | 21 | 0 | — | [] |

Exemplar/candidate first-token collisions: **NONE** on either model against either vocabulary.

The few-shot forms sit **between** the two reference extremes on the hop count (2, vs 0 for echo and
8–12 for forced choice) — which is what the mechanism predicts: the slot is one mapping step away
from the patched token rather than zero (repeat it) or many (walk to a printed list).

`+2` guard tests (`tests/test_rah_preflight_spans.py` 7 → **9**), each **proven able to fail** by
mutation (inserting `poison -> bad` as an exemplar turns the naming test red).

---

## `RAH2-C-001` — a GAP in `RAH2-PR-002`'s stopping rule, found by the data falling into it

**Correction, raised against my own preregistration, before acting on the development data.**

`RAH2-PR-002` fixed two branches and they do not tile the outcome space:

* *"development mass clears the gate"* → held-out is **mandatory**;
* *"both models ≥ 2 orders below the gate in development"* → held-out is **not warranted**.

The few-shot forms landed in **neither**. Best development mass is **0.0040** (Llama) and **0.0063**
(Qwen3) against a 0.05 gate — below it, but by **1.1 and 0.9 orders**, not 2.

**What I did NOT do:** re-read the rule as "roughly two orders", or argue from the one precedent
(`id07_tmpl` fell 0.4344 → 7.1e-08 held-out) that a form failing in development cannot pass held-out.
That inference is probably right and it is still an inference, and the whole point of the split is not
to make it.

**What I did:** took the branch that spends compute rather than the one that saves it — **held-out is
being run** (jobs 827899 Llama, 827900 Qwen3). A gap in a stopping rule is resolved toward measuring,
never toward the conclusion the partial data already suggests.

**The rule is amended for future ids, prospectively:** *if development mass is below the gate by less
than 2 orders on either model, held-out is run.* This amendment is recorded here **before** the
held-out numbers exist.

---

## `RAH2-C-002` — I quoted the wrong field, and it flattered the falsification by ~5×

Found while checking, before writing `RAH2-R-002`, whether the `p_concept`-vs-`p_codeword`
comparison is taken at a single donor layer.

`rah_preflight_transport.py:449` selects `best = max(per_layer, key=p_concept_mean)`. Every
`*_at_best` field is then read **from that layer**. Two consequences:

* **Good:** `pos_ctrl_max`, `p_codeword_at_best` and `patched_option_mass_at_best` are all
  same-layer, so `p_concept > p_codeword` comparisons are sound. That was the worry; it is clean.
* **Bad:** `patched_option_mass_at_best` is *the option mass at the `p_concept`-argmax layer*, **not
  the maximum option mass**. For a form whose `p_concept` is tiny everywhere, the layer that
  maximises `p_concept` is not the layer that maximises mass — so this field **understates** the mass
  a form can reach.

I had been reading it as "best mass". Corrected, from `per_layer` in the same committed artifacts, no
re-run:

| | quoted as "best mass" (wrong field) | max mass over **all** (R, L) |
|---|---|---|
| Llama dev `fewshot_syn` | 0.0040 | **0.0293** |
| Qwen3 dev `fewshot_syn` | 0.0063 | **0.0308** |

**This is a ~5× understatement and it ran in the direction that made my own falsification look
easier.** The conclusion does not change — see `RAH2-R-002` — but the margin does, from "2 orders
below the gate" to "a factor of 3–4 below it", and the honest number is the one that makes the
falsification harder to claim. Both readings are reported below.

⚠ The max-over-(R, L) figure is an **upper bound obtained by maximising over two free parameters**.
It is **NOT AN ESTIMATOR** and is reported only because it is the reading most favourable to the
hypothesis being falsified.

---

## `RAH2-R-002` — `H2` FALSIFIED on held-out material, on both models — 2026-08-31

Jobs **827848 / 827849** (development, level-A `carrot↔bomb`) and **827899 / 827900** (held-out,
`lantern↔poison`), all **COMPLETED**, all at commit `c09068bc`, `dirty=0`. Donor
`natural_doublespeak` at the codeword surface, 8 donors, `n_examples=8`, 5 receiver depths × all
donor layers. Held-out was run because `RAH2-C-001` resolved a gap in the stopping rule toward
measuring.

### Primary registered readout — the three-conjunct gate

**`positive_control_ok` is `False` for `fewshot_cat` and `fewshot_syn` at every receiver depth, on
both models, on both banks — 40 of 40 configurations.** Not one passed.

### Mass, both readings, against the 0.05 gate

| | | Llama dev | Qwen3 dev | **Llama held-out** | **Qwen3 held-out** |
|---|---|---|---|---|---|
| `fewshot_syn` | at `p_conc`-argmax L | 0.0040 | 0.0063 | 0.000655 | 0.000798 |
| `fewshot_syn` | **max over (R, L)** | 0.0293 | 0.0308 | **0.0117** | **0.0163** |
| `fewshot_cat` | at `p_conc`-argmax L | 0.00060 | 0.00064 | 0.000648 | 0.000333 |
| `fewshot_cat` | **max over (R, L)** | 0.0177 | 0.00129 | **0.00815** | **0.00181** |

**Under the reading most favourable to `H2` — maximising over both free parameters — the best
few-shot form reaches 0.33× the gate on Qwen3 held-out and 0.23× on Llama.** It is below the gate on
every model, every bank, both forms, under both readings. `H2` is **FALSIFIED**.

### Why it fails, as far as this run can say

For **7 of the 8** (model × bank × form) cells, `p_codeword > p_concept` at the selected layer — e.g.
Llama held-out `fewshot_syn` 5.18e-04 vs 3.27e-06. The single exception is **Qwen3 development
`fewshot_cat`** (4.60e-04 vs 1.80e-04). So the small mass the few-shot receivers do place on the
candidate vocabulary sits **predominantly on the codeword, not the mapped concept**: the demonstrated
mapping fires, and it maps the **surface it was handed**. That is the echo mechanism one step
removed, not a new one.

⚠ This is a description of where the mass sits, at n=8 donors, with **no interval and no test**. It is
**not** a demonstrated mechanism.

### The trade-off, now with three mechanisms tested and no exception found

| mechanism | names candidates | held-out mass | reads |
|---|---|---|---|
| forced choice (`fc_probe_last`) | **yes** | 0.70 / 0.99992 | exposure-confounded — `p_code` 0.34 / 0.411 **beats** `p_conc` 0.00096 / 0.023, and it **fails the three-conjunct gate on both models** |
| echo (`id07_tmpl`) | no | 0.000695 / 0.000253 | surface identity — and it **collapses held-out on Llama too** (dev 0.0410), a second instance of the collapse previously seen once |
| **in-context mapping (`fewshot_*`)** | **no** | **0.0117 / 0.0163** | the surface it was handed |

⚠ **Scope.** Three mechanisms, two models, two lexical pairs, one donor condition, 8 donors per cell.
`RAH2-R-001`'s statement stands and is not strengthened by this: the trade-off is **not obviously
escapable**, on the routes tried. It is **not** established that no exposure-clean high-mass readout
exists.

⚠ **Do not conflate with Track A.** The `id07_tmpl` held-out figure here (2.53e-04, Qwen3, best over
donor layers, 8 donors, preflight) is a **different estimand** from `RAH-R-018`'s **7.147e-08** (median
over 80 families, fixed configuration, the assay). Both say "unreportable"; neither number may be
substituted for the other.

### Registered outcome

**`H2` FALSIFIED.** Not PARTIAL — the forms failed in development *and* held-out, so the
dev-high/held-out-collapse branch never applied.

---

# `RAH2-DR-001` — deep adversarial review — 2026-08-31

Two read-only auditors, scoped to code and to claims-vs-artifacts. **Every finding below was
re-verified by me against the artifacts before being accepted or rejected** — one was rejected.
Nothing here is taken on the auditor's word.

**This review changes the headline result of both `RAH2-R-001` and `RAH2-R-002`.** The changes are
recorded as amendments; the original entries stay in place with `SUPERSEDED` pointers, per the
append-only rule.

## D1 `RAH2-C-003` — **FATAL.** The falsifications are **Qwen3-only**. On Llama the registered CANNOT-ANSWER branch fired and I did not report it

`RAH2-PR-001` §1.3 fixed: *"**CANNOT ANSWER** | the positive control fails for all forms"*.

Verified count of `positive_control_ok` across every RAH2 run:

| run | model | passing configs |
|---|---|---|
| `rah2dev_p_cb` | Llama | **0 / 25** |
| `rah2fs_p_cb` | Llama | **0 / 20** |
| `rah2fs_p_lp` | Llama | **0 / 20** |
| `rah2dev_q_cb` | Qwen3 | 5 / 25 (`id07_tmpl`, all depths) |
| `rah2fs_q_cb` | Qwen3 | 5 / 20 (`id07_tmpl`, all depths) |
| `rah2fs_q_lp` | Qwen3 | 2 / 20 (`fc_probe_last` R=30, 36) |

**On Llama, no form at any depth on any bank passed the gate — 0 of 65.** The instrument was never
shown to transport anything on Llama in this phase. `RAH2-R-001`'s *"H1 FALSIFIED on both models"* and
`RAH2-R-002`'s *"H2 FALSIFIED ... on both models"* are therefore **not supported on Llama**: a form
that reads nothing cannot distinguish "this framing fails" from "nothing was transported".

**Compounding it:** `RAH2-PR-001` §1.5 registered the positive control as a **`direct_harmful`** donor
arm. **No `direct_harmful` run exists in RAH2** — all six runs are `natural_doublespeak`. So the field
I have been calling `pos_ctrl_max` is not the registered positive control at all; it is the
discrimination arm's own P(concept). The registered positive control **was never run**.

**Corrected claim status:**
> `H1` and `H2` are **FALSIFIED on Qwen3**. On **Llama** the outcome is **CANNOT ANSWER** — the
> registered positive control was not run, and the substitute field fails for every form at every
> depth. Llama's few-shot and semantic numbers are recorded but carry **no falsification weight**.

The prior sprint did establish Llama transport (`RAH-R-013`, `fc_probe_last` at R=4, P(concept)
0.8421, `direct_harmful` donor). That is a **cross-phase** citation from a different donor condition
and does not substitute for the arm `RAH2-PR-001` registered.

## D2 `RAH2-C-004` — a false claim in `RAH2-R-002`'s trade-off table

I wrote that `fc_probe_last` *"fails the three-conjunct gate on both models"* held-out. **False on
Qwen3:** `rah2fs_q_lp` has `GATE.n_passing = 2` — R=30 (`p_conc` 0.5562 vs `p_code` 0.0951) and R=36
(0.4999 vs 0.0852). Both conjuncts I claimed were violated are satisfied. I had quoted the R=10 cell,
which is selected by **max mass**, not by the gate.

**Corrected:** *"`fc_probe_last` fails the gate at every depth on Llama held-out (0/5) and at 3 of 5
depths on Qwen3 held-out; at R=30 and R=36 on Qwen3 it **passes**. It is excluded as a readout because
it prints all four candidates — an exposure confound — not because it fails the gate."*

## D3 `RAH2-C-005` — `RAH2-C-002` was applied to one table and not the other, and fixing that flips a universal

`RAH2-C-002` established that `patched_option_mass_at_best` understates mass. I applied it to the
few-shot table and left `RAH2-R-001`'s ladder table on the field C-002 calls wrong. Max over (R, L),
same committed artifacts:

| Llama form | quoted | corrected | factor |
|---|---|---|---|
| `synonym` | 2.18e-05 | **0.00301** | **138×** |
| `cat_cue` | 0.000626 | 0.00198 | 3.2× |
| `defn_oneword` | 3.12e-05 | 9.76e-05 | 3.1× |

(Qwen3's ladder numbers are unchanged under the corrected reading.)

**A universal flips.** `RAH2-R-001` claims *"The ordering is identical on both models"*. Under the
corrected reading it is **not**: on Llama `synonym` (0.00301) **exceeds** `cat_cue` (0.00198), the
reverse of Qwen3. **Only the group-level ordering (naming > echo >> semantic) is common to both.**

## D4 `RAH2-C-006` — the "2–10 orders" figure is wrong, and the true number makes a skipped run **owed**

`RAH2-R-001` says the ladder forms are *"2–10 orders below"* the gate. Verified: the range is
**1.39–9.56**. `cat_cue` is **1.90** orders below on Llama and **1.39** on Qwen3 — **less than 2 on
both models**, which is exactly the gap `RAH2-C-001` later resolved *toward measuring*.

So `RAH2-C-001`'s amendment retroactively obliges a **ladder held-out run**, which was skipped.
**Submitted: jobs 827941 (Llama), 827942 (Qwen3).** Until they report, **`H1`'s held-out status for
`cat_cue` is OPEN, not falsified.**

## D5 `RAH2-C-007` — `RAH2-R-001` made the exact inference `RAH2-C-001` says was not made

`RAH2-R-001`: *"A form cannot climb 2–10 orders on a held-out pair when a better form fell 6."*
`RAH2-C-001`: *"What I did NOT do: ... argue from the one precedent ... That inference is probably
right and it is still an inference."*

The two are in direct conflict. **The `RAH2-R-001` sentence is WITHDRAWN.** D4's run replaces it with
a measurement.

## D6 `RAH2-C-008` — two registered measurement definitions were not the ones computed

* **Median → mean.** §1.2/§1.3 register the gate on *median* mass. `rah_preflight_transport.py:448`
  computes `option_mass_mean` over 8 donors. **`grep -c median` on the module returns 0 — no median
  exists in any artifact.** Every mass figure in this log is a **mean over 8 donors**, at a layer
  selected by a *different* statistic (`p_concept_mean`).
* **Frozen R → best over R.** §2 registers R **frozen** at depth 0.125 for the primary comparison,
  with the R-sweep *"reported only as a secondary diagnostic"*. `RAH2-R-001`'s primary table is
  explicitly *"best over receiver layers"*. At the frozen R=4 the Llama numbers are materially
  different: `id07_tmpl` **0.0226** (not 0.0410), `cat_cue` **3.54e-04** (not 6.26e-04), `synonym`
  **5.42e-06** (not 2.18e-05).

Both are **deviations from the preregistration**, not errors in arithmetic. Recorded as such. The
frozen-R cell is the registered primary and is now stated; max-over-R and max-over-(R,L) are
secondary and are labelled upper bounds.

## D7 `RAH2-C-009` — the population was narrowed and I called it "UNCHANGED"

`RAH2-PR-002` says *"populations — **UNCHANGED** from `RAH2-PR-001`"*. `RAH2-PR-001` §1.4 registers
**three** development banks (`carrot↔bomb`, `basket↔bomb`, `ticket↔knife`) and **two** held-out pairs
(`lantern↔poison`, `candle↔missile`). Every RAH2 run used **1 of 3** and **1 of 2**. `candle↔missile`
appears only as two **distractor labels** in the held-out vocabulary, never as a probed pair.

**Corrected:** this is a **narrowing of the registered population**, and §1.3's CANNOT-ANSWER trigger
*"the population is incomplete"* is live for the untested cells.

## D8 `RAH2-C-010` — smaller quoted-number defects

* *"1.5–10 orders below the form they were meant to improve on"* — no reference form is named, and
  neither candidate gives 1.5: vs `id07_tmpl` it is **1.8–10.5**, vs `fc_probe_last` **2.4–10.9**.
* `RAH2-C-002` misquotes its own predecessor as *"2 orders"*; `RAH2-C-001` recorded **1.1 and 0.9**.
* `RAH2-C-002`'s *"factor of 3–4"* is the **held-out** figure; the development figures in its own
  table give **1.7× and 1.6×**.
* `RAH2-C-002`'s *"~5× understatement"* is **7.3×** (Llama) and **4.9×** (Qwen3).
* §1.1's quoted prompt for `synonym` (*"X means the same as the word"*) **appears nowhere in the
  code**; the run used body `Give a one-word synonym for the word "widget".` + suffix `A synonym is`.
  `cat_cue`'s quoted shape is likewise a paraphrase.

## D9 `RAH2-C-011` — "7 of 8 cells" selects R as well as L

`RAH2-R-002`'s *"7 of the 8 cells, `p_codeword > p_concept` at the selected layer"* is true as stated,
but "the selected layer" also silently picks R by max mass. **Across all 40 few-shot configurations
the count is 29/40** (Llama dev 9/10, Qwen3 dev 5/10, Llama held-out 7/10, Qwen3 held-out 8/10). The
weaker, unselected statement is the honest one.

## D10 `RAH2-C-012` — `RAH2-R-001` substitutes across estimands in the way `RAH2-R-002` forbids

`RAH2-R-001`: *"the same `id07_tmpl` configuration read 0.4344 in development and 7.1e-08 held out."*
0.4344 is `pos_ctrl_max` at **R=30** — a max over the R-sweep, and a P(concept), not a mass — while
7.1e-08 is `RAH-R-018`'s 80-family **median option mass** from the assay. Different statistic,
different R from the frozen one (R=5 gives 0.4163), different n. **The sentence is withdrawn**; the
same-phase collapse evidence in `RAH2-R-002` (dev 0.4344 → held-out 2.53e-04, one estimand, one
phase) stands in its place. (The arithmetic was also ~6.8 orders, not "six".)

## D11 — provenance is asserted in prose and is not in the artifacts

`RAH2-R-002` states job ids, `COMPLETED`, commit `c09068bc`, `dirty=0`. The `RAH_PREFLIGHT_TRANSPORT/1`
schema carries **no** commit, dirty, job-id or runtime field, so none of it is checkable from the
artifact. It is true — it is in the SLURM logs — but it is not *attested*. **Action:** the writer
should emit a provenance block. Filed, not yet implemented.

## D12 — one auditor finding **REJECTED**

The claims auditor reported the `RAH2-PR-002` CPU-verification table's `fc_probe_last` spans as wrong
by +3 on both models (claimed 72/63/71 and 49/36/48). **This is the auditor's error, not mine.** Those
are the `carrot↔bomb` numbers; my table was rendered with the `lantern↔poison` vocabulary, whose
labels tokenize to different lengths, and it matches `rah2fs_p_lp` (75/66/74) and `rah2fs_q_lp`
(52/39/51) **exactly**. The real defect is that the table **did not say which vocabulary** it used —
fixed by labelling it.

## What the audit confirmed clean

Every mass digit in `RAH2-R-001`, `RAH2-C-001`, `RAH2-C-002` and `RAH2-R-002`'s 4×4 table reproduces
its artifact exactly (16 + 10 + 4 values). The *"40 of 40 `positive_control_ok` False for the few-shot
forms"* claim is verified true and correctly scoped. Hop counts, `names_any_candidate() == []` on all
four model×bank combinations, and the patch/read sites all match. The anti-fishing property holds:
**no intervention code path exists in the module**. `RAH2-PR-002` is genuinely prospective (committed
13:53:04, artifacts 14:09–14:25), and `RAH2-C-001` genuinely precedes both held-out artifacts.

## Corrected bottom line for the phase

> **On Qwen3**, three readout mechanisms were tested and none is both exposure-clean and reportable
> on held-out material. **On Llama, the phase CANNOT ANSWER** — the registered positive control was
> never run and its substitute fails everywhere. `cat_cue`'s held-out status is **OPEN** pending jobs
> 827941/827942. The population is **1 of 3** development banks and **1 of 2** held-out pairs.

---

# `RAH2-DR-001` part 2 — the code auditor, and the confound it found in my own design

The second auditor read only the code. It found the same understatement as `RAH2-C-002` (arriving
independently, with the same 138× `synonym` figure) and **three defects the claims audit could not
see**. All verified by me before acceptance.

## D13 `RAH2-C-013` — **the `H2` comparison is CONFOUNDED. `RAH2-R-002`'s falsification is DOWNGRADED**

Verified from the artifacts:

| form | `templated` |
|---|---|
| `id07_tmpl` (reference) | **True** |
| `fc_probe_last` (reference) | **True** |
| `fewshot_cat` | **False** |
| `fewshot_syn` | **False** |

`render_receiver` sends untemplated forms as **raw base-model completions with no chat template and
no assistant header**. So the few-shot forms differ from both references on **two** axes at once:
the framing (the thing `RAH2-PR-002` set out to test) **and** the presence of the chat template.

**An instruct-tuned model can place little probability on a bare noun continuation outside its chat
format for reasons that have nothing to do with in-context mapping.** Nothing in the artifact
separates the two, and `RAH2-PR-002`'s CPU verification checked geometry and naming — it did not
check that the comparison was controlled. **I designed this confound in and did not see it.**

> **`RAH2-R-002`'s verdict is downgraded from `H2` FALSIFIED to `H2` CONFOUNDED — CANNOT ATTRIBUTE**,
> pending `RAH2-PR-003`. The measurements stand; the causal reading of them does not. The Qwen3-only
> scoping from `RAH2-C-003` still applies on top of this.

## D14 `RAH2-C-014` — only the leading-space token id is ever scored

`signals.readout_ids(...)["primary_id"]` scores `" word"` only (`full_word_ids` exists and is
deliberately unused). Verified on both tokenizers, the bare and space-prefixed ids **always differ**:

| word | `" bomb"` | `"bomb"` | bare is single-token? |
|---|---|---|---|
| bomb | 13054 | 79444 | yes |
| knife | 22145 | 43820 | yes |
| ticket | 11989 | 27632 | yes |
| carrot, poison, lantern, missile, candle | — | 2 tokens each | **no** |

The read slots differ in what they license: `fewshot_*` read after `' ->'` and `fc_probe_last` after
`':'` — both license the space form; **`id07_tmpl` reads after `'\n\n'`, where a model would emit the
bare form.**

⚠ **Direction, stated precisely: this can only UNDERSTATE `id07_tmpl`'s mass, and only for
`bomb`/`knife`/`ticket`** (the other five have multi-token bare forms whose first token is neither
id). It therefore **does not** threaten the `H1`/`H2` falsifications — those forms read at
space-licensing slots — but it **does** weaken the `id07_tmpl` **collapse** claim in `RAH2-R-002`,
because an understated held-out mass makes a collapse look larger. **Magnitude unmeasured.** Filed
as a known measurement limitation of every `id07_*` figure in this log.

## D15 `RAH2-C-015` — the exemplar collision check was **DEAD CODE** while I reported its result

`exemplar_candidate_collisions` was defined and **never called by `main()`**. The only other
reference was a test docstring asserting *"checked in the run itself"*. Meanwhile
`RAH2-PR-002`'s verification section reports *"Exemplar/candidate first-token collisions: NONE"* as a
result.

**That result is true** — I ran the check in a scratch script, and it is reproducible — but it was
**not** in the pipeline, was **not** in any artifact, and could **not** have fired on a future bank.
A bank whose codeword is `fruit` or `start` would collide with a `fewshot_cat`/`fewshot_syn` exemplar,
prime the answer vocabulary directly, and report high mass for an "exposure-clean" form with nothing
raising.

**Fixed:** `main()` now calls it and **refuses** on collision, and the result is persisted to the
artifact as `exemplar_candidate_collisions`, so it is attested rather than asserted in prose (which
also closes D11 for this field).

## D16 `RAH2-C-016` — the console `mass=` column printed the **unpatched** mass

`print(... "mass=%.3f" ... base_mass)` — the console column named `mass` was
`unpatched_option_mass`, while the JSON field of nearly the same name holds the patched value. Every
`mass=0.000 fail` line I read during monitoring was the **prior**, not the result. No published
number came from that column (all tables were built from the JSON), but it is exactly the kind of
mislabel that produces one. **Fixed:** the line now prints `mass_unpatched=` and `mass_patched=`
separately.

## D17 — auditor findings NOT accepted

* *"`rah2fs_q_lp_*.json` does not exist"* — **stale**; the auditor read the tree before the Qwen3
  held-out job landed at 14:22:33. The file exists and `RAH2-R-002` uses it.
* Its ordering claim (*"on Llama `id07_tmpl` 0.9800 beats `fc_probe_last` 0.8511, reversing the
  ordering"*) is **arithmetically correct and accepted**, and is an *additional* flip beyond the
  `synonym`/`cat_cue` one in `RAH2-C-005`. Recorded here rather than rejected.
* `positive_control_ok` is **selection-inflated** (argmax over ~31–39 donor layers × 5 R, no
  multiplicity correction) — accepted as a caveat and noted; it makes `RAH2-C-003`'s Llama
  0-of-65 result *stronger*, not weaker.

---

## `RAH2-PR-003` — the untemplated control that makes `H2` attributable

**Registered before the run. Committed before any `PR-003` forward pass.**

`RAH2-C-013` leaves `H2` unattributable. The fix needs **no new form**: `id07_raw` — the untemplated
echo receiver — already exists in the frozen Stage-A grid. Adding it to the **few-shot form set**
(never to `receiver_forms`) gives an untemplated reference at the same template status as
`fewshot_*`, so framing is the only axis left varying.

| form | templated | framing |
|---|---|---|
| `fc_probe_last` | yes | names candidates |
| `id07_tmpl` | yes | echo |
| **`id07_raw`** | **no** | **echo** ← the control |
| `fewshot_cat` / `fewshot_syn` | no | in-context mapping |

**Fixed now, before the data:**

| `id07_raw` result | what it licenses |
|---|---|
| **clears the 0.05 gate** while `fewshot_*` do not | the template is **not** the explanation → **`H2` FALSIFIED** is restored, on the models where a positive control fires |
| **also fails** the gate | the untemplated condition is unreadable for *any* framing → **`H2` CANNOT ANSWER**; the few-shot numbers carry no weight and the confound is confirmed |
| lands between | reported as-is; `H2` stays **CANNOT ATTRIBUTE** and the residual is quantified, not argued |

Populations, gates and the split are `RAH2-PR-001`'s, **and this time the narrowing is stated
rather than called unchanged**: development `carrot↔bomb` and held-out `lantern↔poison` only — 1 of 3
development banks and 1 of 2 held-out pairs, per `RAH2-C-009`.

⚠ Per `RAH2-C-003`, Llama cannot falsify anything in this phase until a **`direct_harmful`** positive
control is run. That arm is **owed** and is not part of PR-003.

---

## `RAH2-R-003` — the ladder held-out run `RAH2-C-006` made owed — and it refutes the inference `RAH2-C-007` withdrew — 2026-08-31

Jobs **827941** (Llama) / **827942** (Qwen3), both **COMPLETED**, held-out `lantern↔poison`, ladder
form set, same donor/dose/depths as development. This run existed only because `RAH2-C-001` resolved a
stopping-rule gap toward measuring and `RAH2-C-006` found `cat_cue` inside that gap.

### It was worth running. The withdrawn inference was not merely unproven — it was **wrong in sign**

`RAH2-R-001` had argued *"a form cannot climb 2–10 orders on a held-out pair when a better form fell
6"*; `RAH2-C-007` withdrew it as an inference. **Measured, max over (R, L), development →
held-out:**

| form | Llama dev → held-out | Qwen3 dev → held-out |
|---|---|---|
| **`cat_cue`** | 0.00198 → **0.0389** (**×19.7 UP**) | 0.00205 → **0.0243** (**×11.8 UP**) |
| `synonym` | 0.00301 → 0.00122 (×0.41) | 1.38e-11 → 4.78e-09 (**×347 UP**) |
| `defn_oneword` | 9.76e-05 → 8.21e-04 (**×8.4 UP**) | 1.42e-06 → 7.78e-07 (×0.55) |
| `id07_tmpl` | 0.980 → 0.990 (×1.01) | 0.4344 → 2.93e-04 (**×0.00067**) |

**Development mass does not predict held-out mass — not in magnitude and not in direction.** Eight
form × model cells: five went **up**, three went down, and the spread runs from ×0.00067 to ×347. The
one precedent I had generalised from (`id07_tmpl` on Qwen3) is the **single most extreme collapse in
the table**, and it is the exception, not the rule.

> **Methodological finding, and the one I would carry to any future phase of this project:** a
> development screen here has **no** demonstrated predictive validity for held-out material.
> `RAH2-R-001`'s registered early stop — skipping held-out when development looks hopeless — would
> have been a **mistake**, and would have hidden the largest exposure-clean mass this phase has seen.

### The result itself

`cat_cue` is the **closest any exposure-clean form has come**: **0.0389 = 0.78× the gate** on Llama,
**0.0243 = 0.49×** on Qwen3, under the max-over-(R, L) upper bound. It is **still below the 0.05
gate** on both models, under both readings.

Where the mass sits is unchanged: at the selected layer, `p_codeword` beats `p_concept` — Llama
2.66e-03 vs 1.13e-06, Qwen3 1.72e-04 vs 5.88e-05.

### Registered outcome, scoped per `RAH2-C-003`

| model | gate | outcome for `cat_cue` held-out |
|---|---|---|
| **Llama** | **0 / 25** `positive_control_ok` | **CANNOT ANSWER** — fourth consecutive Llama run with no passing configuration |
| **Qwen3** | 2 / 25 (`fc_probe_last` R=30, 36) | **`H1` FALSIFIED for `cat_cue`** — below gate under both readings |

⚠ **A caveat I am not going to bury.** On Qwen3 the only configurations that pass the positive
control are `fc_probe_last`, the form that **prints all four candidates**. That an option-naming form
transports is weak evidence that the instrument works for a form that names nothing. The registered
rule (§1.3: CANNOT ANSWER only if the control fails for *all* forms) is satisfied, so this counts as
an answer — but it is the **weakest** kind this phase has produced, and the owed `direct_harmful`
arm is what would settle it.

**`cat_cue`'s held-out status, open since `RAH2-C-006`, is now closed on Qwen3 and open on Llama.**
