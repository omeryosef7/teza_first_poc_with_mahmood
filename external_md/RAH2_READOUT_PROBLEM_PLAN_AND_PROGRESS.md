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

> ✅ **CLOSED by `RAH2-R-003`** — they reported. `cat_cue` reads **0.0389 (Llama) / 0.0243
> (Qwen3)** held-out, below the 0.05 mass gate under both readings. Per the standing scoping
> (`RAH2-C-017`, reinstated by `RAH2-C-020`) that is a falsification on the model where an
> exposure-clean positive control fires and CANNOT ANSWER on the other. **This marker is here so
> a reader stopping at `RAH2-C-006` does not carry away "OPEN"** — the same defect `RAH2-C-024`
> fixed at `RAH2-R-003`.

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

> ✅ **IMPLEMENTED by `RAH2-R-008`.** `provenance()` now writes `git_commit` · `git_dirty` ·
> `slurm_job_id` · `slurm_nodelist` · `hostname` · `argv` · `started_utc` · `finished_utc` ·
> `python` into every artifact. ⚠ The **16 RAH2 artifacts already on disk cannot be back-filled**
> and keep prose provenance, so this claim's own artifacts remain unattested — it helps the next
> phase, not this one.

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
> never run and its substitute fails everywhere. `cat_cue`'s held-out status is **OPEN** [✅ closed by
`RAH2-R-003`] pending jobs
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
control is run. That arm is **owed** and is not part of PR-003. [✅ run and reported at
`RAH2-C-017`.]

---

> 🛑 **SUPERSEDED IN PART — read `RAH2-C-024` before quoting anything in this entry.** Its
> registered-outcome table counts `positive_control_ok` on a **`natural_doublespeak`** run, i.e. the
> test arm's own P(concept), and labels it "the positive control". No positive control existed in
> this run. The **dev→held-out finding below is unaffected and stands**; the outcome table does not.

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

---

## `RAH2-C-017` — the owed positive control was run, and it **INVERTS** `RAH2-C-003`'s verdict

`RAH2-C-003` found the registered `direct_harmful` arm had never been run and concluded, from the
substitute field, **Llama = CANNOT ANSWER, Qwen3 = answerable**. The arm has now been run — jobs
**828 (rah2pc_p_cb / rah2pc_q_cb)**, both COMPLETED — and the conclusion is **the wrong way round for
the class of form the whole phase is about.**

`p_concept` under a donor that carries the concept **on its surface**, best over donor layers, gate
0.1:

| form | names candidates | **Llama** | **Qwen3** |
|---|---|---|---|
| `fc_probe_last` | **yes** | **0.9087 PASS** | **1.0000 PASS** |
| `id07_tmpl` | no | **0.5011 PASS** | 0.0142 fail |
| `cat_cue` | no | 0.0091 fail | 0.0354 fail |
| `synonym` | no | 0.0013 fail | 1.48e-08 fail |
| `defn_oneword` | no | 3.53e-05 fail | 2.57e-08 fail |

| | passing configs |
|---|---|
| Llama | **4/25** — `id07_tmpl` @ R=4, 8 **and** `fc_probe_last` @ R=4, 8 |
| Qwen3 | 3/25 — **`fc_probe_last` only** @ R=5, 10, 20 |

**Corrected scoping, replacing `RAH2-C-003`'s:**

> On **Llama** the instrument is demonstrated for an **exposure-clean** receiver (`id07_tmpl`, 0.50,
> `p_code` 1.9e-06) — so Llama's `H1`/`H2` results **are** answerable, and `RAH2-C-003`'s
> CANNOT ANSWER is **WITHDRAWN**.
> On **Qwen3** the only form that passes is the one that **prints all four candidates**. No
> exposure-clean receiver is demonstrated to transport anything on Qwen3, so for exposure-clean forms
> **Qwen3 is CANNOT ANSWER** — the reverse of what `RAH2-C-003` said, and it propagated into
> `RAH2-R-002` and `RAH2-R-003`.

Those two entries are **SUPERSEDED on their model scoping** and stand on everything else. I got this
backwards because I read a field named `pos_ctrl_max` as the positive control when it was the test
arm's own P(concept) — and then corrected confidently in the wrong direction.

### The finding this sharpens — and it is stronger than the one it replaces

In the positive control the concept is **literally present in the donor**. The semantic forms still
cannot report it: `cat_cue` 0.0091 / 0.0354, `synonym` 0.0013 / 1.5e-08, `defn_oneword` 3.5e-05 /
2.6e-08 — **all below the gate on both models**.

> `RAH2-R-001` read as *"a semantic-constraint framing cannot recover the mapped concept"*. The
> positive control shows the weaker premise is what is true: **a semantic-constraint framing cannot
> report a concept that is sitting right there.** These forms are unreportable **per se**, not
> unreportable-for-doublespeak. That is a cleaner claim, and it makes `H1`'s falsification about the
> **readout**, not about the mapping.

### ⚠ An anomaly recorded, not explained

On **Qwen3**, `id07_tmpl` reads **0.4344** from a `natural_doublespeak` donor (codeword on the
surface) but only **0.0142** from a `direct_harmful` donor (concept on the surface) — **the positive
control is ~30× WEAKER than the test condition** for that form. A control that underperforms the
condition it is meant to validate is not a working control. **I do not have an explanation**, and I am
not going to invent one; it is filed as an open defect in the Qwen3 positive-control arm and it is
part of why Qwen3 is now CANNOT ANSWER for exposure-clean forms.

### A gap this exposed, and the run that closes it

`RAH2-PR-003`'s control form `id07_raw` has **no positive control of its own** — the `pc_*` runs used
the **ladder** form set, which does not contain it. Submitted: **828393 (Llama), 828395 (Qwen3)**,
`direct_harmful` × `fewshot` form set. Until they report, `id07_raw`'s readings are uncontrolled.

---

## `RAH2-R-004` — `RAH2-PR-003`: the chat template is **NOT** the explanation. `H2` restored to FALSIFIED on Llama

Jobs 827991 / 827993 (Llama dev / held-out), 828085 / 828070 (Qwen3 dev / held-out), all COMPLETED,
all carrying the `RAH2-C-015` fix (`exemplar_candidate_collisions: []` now **persisted in every
artifact**) and the `RAH2-C-016` console fix.

`RAH2-C-013` downgraded `H2` because the few-shot forms are untemplated and both references were
templated. `id07_raw` — **untemplated**, echo framing — settles it. Max over (R, L):

| form | templated | Llama dev | Llama held-out | Qwen3 dev | Qwen3 held-out |
|---|---|---|---|---|---|
| `fc_probe_last` | yes | 0.851 | 0.897 | 1.000 | 1.000 |
| `id07_tmpl` | yes | 0.980 | 0.990 | 0.434 | 2.93e-04 |
| **`id07_raw`** | **no** | **0.899** | **0.750** | **0.780** | **0.941** |
| `fewshot_syn` | no | 0.0293 | 0.0117 | 0.0308 | 0.0163 |
| `fewshot_cat` | no | 0.0177 | 0.00815 | 0.00129 | 0.00181 |

**`id07_raw` clears the gate by 15–19× in all four cells.** The untemplated condition supports
option mass of 0.75–0.94; it is not unreadable. **`RAH2-C-013`'s alternative explanation is refuted
on both models**, and this is the branch `RAH2-PR-003` registered in advance:

> *"`id07_raw` clears the 0.05 gate while `fewshot_*` do not → the template is **not** the
> explanation → **`H2` FALSIFIED** is restored, on the models where a positive control fires."*

**Registered outcome, with `RAH2-C-017`'s corrected scoping:**

| model | positive control for an exposure-clean form | `H2` |
|---|---|---|
| **Llama** | **fires** (`id07_tmpl` 0.50) | **FALSIFIED** — restored from CONFOUNDED |
| **Qwen3** | does **not** fire | **CANNOT ANSWER** |

**`H2` is falsified on Llama and cannot be answered on Qwen3** — the exact opposite of the model
scoping I published two entries ago. The measurements never changed; my reading of which model could
support a claim was wrong twice, in opposite directions, and is now anchored to a control that was
actually run.

---

## `RAH2-C-018` — `RAH2-R-004` quoted the upper bound as if it were the result. The template conclusion survives; the table does not

Jobs **828393 / 828395** COMPLETED gave `id07_raw` its own positive control, and checking it exposed
that `RAH2-R-004`'s headline table (*"`id07_raw` clears the gate by 15–19× in all four cells"*) is the
**max over (R, L)** — the quantity `RAH2-C-002` labelled *"NOT AN ESTIMATOR"*, an upper bound
maximised over two free parameters. Those maxima sit at donor layers **L = 0, 4, 6** — the very
bottom of the stack.

At the **`p_concept`-argmax layer**, `id07_raw` under the doublespeak donor reads:

| | best over R, at the selected layer | gate |
|---|---|---|
| Llama dev | 0.0353 | fail (0/5 depths) |
| **Llama held-out** | **0.00673** | fail (0/5) |
| Qwen3 dev | **0.3887** | **PASS at all 5 depths**, concept ≫ codeword (7.5e-07) |
| **Qwen3 held-out** | **0.000401** | fail (0/5) |

**`id07_raw` collapses held-out exactly as `id07_tmpl` did** — Qwen3 0.3887 → 0.000401, three orders.
I used the upper bound to make a claim one tick after writing down that it is not an estimator.

**What survives, and on a better footing than before.** `RAH2-C-013`'s alternative explanation was
*"an instruct model puts little mass on a bare continuation outside its chat format"*. That is refuted
**by the positive control, not by the table**: untemplated `id07_raw` reads **0.8409 (Llama)** and
**0.8404 (Qwen3)** when the concept is present. The untemplated condition supports mass ~0.84. The
template is **not** the explanation, and this now rests on a controlled measurement.

---

## `RAH2-R-005` — the phase's result, with every form finally carrying its own positive control

**`P(concept)` under a concept-bearing donor, gate 0.1 — the control `RAH2-PR-001` registered and
`RAH2-C-003` found had never been run:**

| form | exposure-clean | Llama | Qwen3 | validated readout? |
|---|---|---|---|---|
| `fc_probe_last` | **no** — prints all 4 | 0.9087 | 1.0000 | yes, but confounded by construction |
| **`id07_raw`** | **yes** | **0.8409** | **0.8404** | **YES, on both models** |
| `id07_tmpl` | yes | 0.5011 | 0.0142 | Llama only |
| `fewshot_syn` | yes | 0.0197 | 0.0965 | **no** |
| `fewshot_cat` | yes | 0.0658 | 0.0087 | **no** |
| `cat_cue` | yes | 0.0091 | 0.0354 | **no** |
| `synonym` | yes | 0.0013 | 1.48e-08 | **no** |
| `defn_oneword` | yes | 3.53e-05 | 2.57e-08 | **no** |

### `RAH2-C-017`'s Qwen3 verdict is WITHDRAWN

C-017 concluded *"no exposure-clean receiver is demonstrated to transport anything on Qwen3"*. **False:
`id07_raw` passes on Qwen3 at 0.8404, at three depths.** C-017 was computed on the **ladder** form
set, which does not contain `id07_raw`. Qwen3 is answerable. That is the **third** time this phase's
model scoping moved, and **all three moves came from a control I had not yet run — never from a number
changing.**

### The two questions the phase confused, now separated

**(a) "Is there an exposure-clean, high-mass readout at all?"** — the question `RBD-R-033` and the RAH
sprint summary both recorded as having **no** instance in this project's inventory.

> **ANSWERED, and positively: `id07_raw`.** Names no candidate, and transports a present concept at
> **0.84 on both models** with `p_codeword` at 1.2e-05 / 5.2e-07. It is the **first** readout in this
> project that is both exposure-clean and demonstrably high-mass, and it was **already sitting in the
> frozen Stage-A grid, never having been given a positive control.**

**(b) "Does the doublespeak mapping survive in the codeword representation, readably?"**

> **NO, on held-out material, on both models — and now with a validated instrument.** `id07_raw`
> reads 0.00673 (Llama) and 0.000401 (Qwen3) held-out, failing the gate at every depth, *after*
> passing its positive control at 0.84 on the same model, same receiver, same layers.

**This is the first held-out negative in the phase that a working readout produced.** Every earlier
one was confounded with the readout being broken. That is what changes here.

### Registered outcomes, final for this phase

| hypothesis | as a claim about the READOUT FORM | as a claim about the MAPPING |
|---|---|---|
| **`H1`** (semantic constraint can be clean + high-mass) | **FALSIFIED, both models** — the semantic forms cannot report a concept that is *literally present* | CANNOT ANSWER through those forms |
| **`H2`** (in-context mapping can be clean + high-mass) | **FALSIFIED, both models** — `fewshot_*` peak at 0.0965 with the concept present, below the 0.1 control | CANNOT ANSWER through those forms |
| **`H0`** (the trade-off is unavoidable) | **FALSIFIED by `id07_raw`** — exposure-clean *and* 0.84 | — |

⚠ **`H2`'s verdict has now moved three times** (FALSIFIED → CONFOUNDED → FALSIFIED-on-Llama →
FALSIFIED-as-a-readout-claim-on-both). Each move was a control arriving, not a measurement changing.
The stable statement is the two-column split above, which I should have drawn at `RAH2-PR-001`.

⚠ **Scope, unchanged and still narrow:** 2 models, 1 development bank of 3 registered, 1 held-out
pair of 2, 8 donors per cell, means not medians (`RAH2-C-008`), best-over-R not frozen-R for the
mass figures, and `id07_*` figures carry the leading-space-only limitation (`RAH2-C-014`).

---

## `RAH2-C-019` — `RAH2-R-005` cited two prior claims as if they were one. Only **one** of them is refuted

Found while checking `RAH2-R-005` against the deliverables it bears on. There are **two** distinct
prior statements and they have **different truth values** after R-005:

**(A) the STRUCTURAL claim — `RBD-R-033`, quoted at `reports/RAH_ACTIVATION_ASSAY_REPORT.md:13` and
`RESEARCH_HANDOFF.md:279`:**

> *"A readout that names its options is high-mass and exposure-confounded; one that does not is
> exposure-clean **and unreportable**. No readout in this project's inventory is both."*

**REFUTED.** `id07_raw` names no option and reports at **0.8409 / 0.8404**. "Exposure-clean implies
unreportable" is false, and the counterexample was inside the frozen Stage-A grid the whole time.

**(B) the HELD-OUT requirement — `reports/RAH_SPRINT_SUMMARY.md:211` and `RESEARCH_HANDOFF.md:450`:**

> *"Track A needs a receiver that is both exposure-clean and high-mass **on held-out material**. No
> such readout exists in this project's inventory."*

**STANDS, UNREFUTED.** `id07_raw` is exposure-clean and reads **0.00673 / 0.000401** on held-out
material — 0/5 depths at gate on both models. It does **not** satisfy (B).

`RAH2-R-005` §(a) wrote *"the question `RBD-R-033` **and the RAH sprint summary** both recorded as
having no instance"* and claimed it ANSWERED. **That is right for (A) and wrong for (B).** The two
sentences differ by the words "on held-out material", which is the entire difficulty of the phase.

**Corrected statement of what R-005 established:**

> The trade-off is **not structural** — an exposure-clean readout can be high-mass, demonstrated at
> 0.84 on both models. But the readout Track A actually needs, one that is exposure-clean **and
> high-mass on held-out doublespeak material**, **still does not exist**. R-005 converts an
> unexplained absence into a **located** one: the readout is fine; what is missing is on held-out
> material, downstream of a receiver that demonstrably works.

This is the same scope-error class the predecessor sprint closed on (*"the numbers kept being right
and the sentences around them kept being wrong"*) — a qualifier dropped between two nearly identical
sentences. The numbers in R-005 were and are correct: independently verified below.

## `RAH2-R-006` — independent verification of `RAH2-R-005`

`scripts/rah2_verify_r005.py` — **stdlib only, imports nothing from the producer**, re-derives every
published number from the committed `grid` records and **refuses (exit 1)** on mismatch.

| checked | result |
|---|---|
| 16 positive-control values across 4 artifacts | **all OK** |
| the validated/not-validated verdict, **recomputed** from the 0.1 gate rather than read | 6/6 OK |
| 4 `id07_raw` doublespeak masses | all OK |
| *"fails at every depth held-out"* — checked on **all 5 depths**, not the best | 0/5 pass, both models |
| `RAH2-C-018`'s upper-bound gap | selected-layer 4.01e-04 vs max-over-(R,L) 0.9408 = **2348×** |

**22 checks, 0 failures.** Proven able to fail: perturbing one published value to 0.9409 exits 1
naming that value; restored, exit 0.

⚠ This verifies that the **published tables match the artifacts**. It does **not** re-run the models,
and it inherits every measurement limitation already recorded — means not medians (`RAH2-C-008`),
best-over-R (`RAH2-C-008`), leading-space-only ids (`RAH2-C-014`), and 8 donors per cell.

---

# `RAH2-DR-002` — an adversarial auditor was asked to REFUTE the phase's one positive claim. It did.

`RAH2-R-005`'s positive result is **RETRACTED**. Every decisive point was re-verified by me against
the artifacts before acceptance; all three hold.

## `RAH2-C-020` — **RETRACTION.** `id07_raw` is a token decoder, not a readout

`id07_raw` is `ID_PROMPT = "hello hello\nworld world\ncat cat\nX"` with `patch_at="last"`,
`read_at="patch"` — **0 hops**. The donor vector is written into the residual at the final position
and the logits are read **at that same position**. It is a copy prompt, and the measurement is *"after
overwriting the residual with the representation of token T, does the model emit T?"*

In the positive control the donor is captured at the concept's own surface token (`piece == ' bomb'`
for all 8 donors). **Concept and injected token are the same object, so transport and copying are
confounded by construction.** The discriminating experiment already existed in my own artifacts — the
`natural_doublespeak` donor captures at the **codeword** surface:

| run | injected token | **P(codeword)** | P(concept) there |
|---|---|---|---|
| Llama dev | ` carrot` | **0.8989** | 4.79e-06 |
| Llama held-out | ` lantern` | **0.7495** | 3.56e-07 |
| Qwen3 dev | ` carrot` | **0.7805** | 6.44e-07 |
| Qwen3 held-out | ` lantern` | **0.9408** | 6.56e-08 |

> **Inject `bomb` → get `bomb` at 0.84. Inject `carrot` → get `carrot` at 0.90. Inject `lantern` →
> get `lantern` at 0.94.** Same shallow donor layers (L=0–6), same shallow receiver depths, same
> magnitude — **at or above the "positive control" value.** `id07_raw`'s output is a deterministic
> function of *which token was injected*. It reads token identity, and nothing else.

**Consequences, all retracted:**

| retracted | status |
|---|---|
| *"the first readout that is both exposure-clean and high-mass"* | **FALSE** — it is a token decoder |
| *"`H0` is falsified by `id07_raw`"` | **WITHDRAWN — `H0` is CONFIRMED.** `H0` says mass requires printing the candidates **or echoing the patched token**. `id07_raw` *is* the second disjunct. I filed a confirming instance as a refutation |
| *"`RBD-R-033` (A) is REFUTED"* (`RAH2-C-019`) | **WITHDRAWN.** `RBD-R-033` stands entirely |
| *"first held-out negative a working readout produced"* | **not established** |
| `RAH2-C-018`'s withdrawal of `RAH2-C-017`'s Qwen3 verdict | **withdrawn in turn** — it rested on this form |

**Two deliverables were corrected on this wrong basis and have been RETRACTED in place**
(`reports/RAH_ACTIVATION_ASSAY_REPORT.md`, `reports/RAH_SPRINT_SUMMARY.md`). That is the worst defect
of the phase: I propagated an artifact of my own test into published documents within one tick.

### `RAH2-C-021` — *"never having been given a positive control"* is factually false

**Eight artifacts in the same directory, dated 2026-08-30**, are `form_set=grid` /
`donor_condition=direct_harmful` — `id07_raw`'s positive control, run and passed, the day before:

| artifact | `id07_raw` P(concept) | passing depths |
|---|---|---|
| `sA_q_ticket_knife` | **0.9225** | 2/5 |
| `sA_q_carrot_bomb`, `sA_q_basket_bomb` | 0.8492 | 3/5 |
| `sA_p_carrot_bomb`, `sA_p_basket_bomb` | 0.8459 | 2/5 |
| `sA_p_ticket_knife` | 0.8442 | 2/5 |
| `rahpf_qlp` / `rahpf_plp` | 0.6925 / 0.6019 | 2/5 |

Nothing was discovered on 2026-08-31; the control had been run **eight times** and I did not look.
`RAH2-R-005`'s framing (*"sitting in the frozen grid the whole time, never having been given a
positive control"*) is exactly backwards, and it is the same failure as `RAH-C-002` in the
predecessor sprint — asserting a run had never happened without checking the artifact directory.

### `RAH2-C-022` — `RAH2-R-006` verified the wrong quantity, and its verifier passed anyway

`scripts/rah2_verify_r005.py` re-derives from `option_mass_mean` and `pos_ctrl_max`. Its headline
*"selected-layer 4.01e-04 vs max-over-(R,L) 0.9408 = 2348×"* — **that 0.9408 is 100 % `p_codeword`**
(max `p_concept` over the same cells is **2.38e-04**). The number I published as the misleading
*concept* upper bound is the model echoing the codeword.

**22 checks, 0 failures, and it could not have caught this**: transcription was never the problem.
The verifier confirms the tables match the artifacts and is silent on whether the tables measure what
their column headings say. **A verifier that re-reads the producer's chosen field inherits the
producer's choice of field.**

## The one real signal, registered as an OBSERVATION and nothing more

Not all the `id07_raw` numbers are token identity. On **Qwen3 development**, at donor layer **L=34**
(deep, not shallow), the *codeword* representation decodes to the **concept**: P(concept) **0.3887**
with P(codeword) **7.5e-07** — the reverse of the shallow-layer behaviour in the table above, in the
same form and the same run.

⚠ **This is an OBSERVATION, not a finding, and it is NOT a new hypothesis.** It is one model, one
bank, development only, 8 donors, and it collapses to 4.0e-04 held-out. Per the standing rule, any
work on it requires **its own preregistration first**. It is recorded here so it is not lost and so
that nobody — including me — quotes it as a result.

## What survives `RAH2-DR-002` intact

* **`H1` and `H2` are still falsified as readout claims.** The semantic and few-shot forms read at
  **non-zero hops** and must compute a *function of* the patched token, so the copy confound does not
  apply to them. They peak at **0.0965** with the concept literally present, against a 0.1 control.
  Ruled out as candidate readouts, on both models.
* **`RAH2-R-003`** — development mass does not predict held-out mass, in magnitude or direction
  (×0.00067 to ×347). Untouched.
* **`RAH2-C-013`'s template question**: the untemplated condition supports mass 0.84 — but that is
  now known to be token identity, so the honest statement is weaker: *untemplated prompts are not
  intrinsically unreadable*, demonstrated only for a copy task.
* Every measured number. **Not one number in this phase has ever been wrong.** Twenty-two corrections
  and every one of them was a claim about what a correct number meant.

**Corrected bottom line for the phase:** the readout problem is **NOT solved**, `RBD-R-033` and the
RAH summary's open problem both **stand**, and what RAH2 contributes is a **reduction of the search
space** — semantic-constraint and in-context-mapping framings are ruled out, because they cannot
report a concept that is sitting right in front of them.

---

# `RAH2-DR-002` part 2 — the claims auditor. It found the defect in my *verifier*

The second auditor independently reached `RAH2-C-021` (the eight prior artifacts) and confirmed
**every quoted number in `RAH2-R-003`…`R-006` matches its artifact to the digits quoted** — it
re-derived all of them. The defects are again in scope words, and one is in the tool I built to catch
scope words.

## `RAH2-C-023` — **my verifier could not fail on 6 of its own assertions.** `RAH-C-007`, repeated

`check()` used an **absolute** tolerance of `5e-4` against published values orders of magnitude
smaller. Verified by mutation — each of these was a *wrong* value that the verifier passed:

| published | mutated to | wrong by | old verifier |
|---|---|---|---|
| Qwen3 `synonym` 1.48e-08 | 5.0e-04 | **33 784×** | **PASS** |
| Qwen3 `defn_oneword` 2.57e-08 | 4.9e-04 | 19 000× | **PASS** |
| Llama `defn_oneword` 3.53e-05 | 4.9e-04 | 14× | **PASS** |
| **Qwen3 held-out `id07_raw` 4.01e-04** | 9.0e-04 | 2.2× | **PASS** |
| Llama `synonym` 0.0013 | 0.0017 | 31 % | **PASS** |
| Qwen3 `fewshot_cat` 0.0087 | 0.0091 | 5 % | **PASS** |

The fourth is a **headline number of `RAH2-R-005` §(b)** and of the (now retracted) deliverable edit.

**And my fail-proof was the worst possible choice.** `RAH2-R-006` proved the verifier could fail by
perturbing **0.8409 → 0.9409** — the value with the **most headroom in the file**. It demonstrated
nothing about the six above. *A mutation test that picks the easiest value proves only that the
harness runs.*

**Three further defects in the same script:**

* the verdict loop covered **6 of the 16** verdicts and compared each against a **hardcoded literal**
  (`expect = (form == "id07_raw")`) rather than against R-005's published column — so it could not
  disagree with the claim. It skipped `id07_tmpl`, **the only verdict asymmetric across models** and
  therefore the only one where an error would matter;
* the `2348×` figure was **printed but not asserted** — the assertion was `ub > 100 * sel`, a
  **23×-loose** bound reported in the log as a checked result;
* **`RAH2-R-006`'s "22 checks" is wrong**; the script registered 29 fail-conditions.

**Fixed:** relative tolerance (1 % + denormal floor); all 16 verdicts checked against a transcription
of the published column, including `id07_tmpl`; the ratio asserted to ±1 %; the count printed by the
script rather than typed by me. Now **39 assertions**. **All six previously-vacuous mutations exit 1,
and flipping the `id07_tmpl` Qwen3 verdict exits 1.**

## `RAH2-C-024` — `RAH2-R-003`'s outcome table is wrong on more than model scoping

`RAH2-C-017` marked R-002/R-003 *"SUPERSEDED on their model scoping and stand on everything else"*.
Too generous for R-003: its gate column counts `positive_control_ok` on the **`natural_doublespeak`**
runs `rah2ld_p_lp` / `rah2ld_q_lp`, and C-017 itself established that this field is *the test arm's
own P(concept)*. **No positive control existed in that run**, so the label is a category error, not a
scoping slip. R-003 also carried **no inline marker** — a reader stopping there got two withdrawn
verdicts. **An inline `🛑 SUPERSEDED IN PART` header is now at the top of R-003.** Its dev→held-out
finding is untouched and stands.

## `RAH2-C-025` — *"the closest any exposure-clean form has come"* is refuted by its own table

`RAH2-R-003` says `cat_cue` at 0.0389 is *"the closest any exposure-clean form has come"*. §1.1 lists
`id07_tmpl` as naming **no** candidates, and R-003's own table **six lines above** gives it
**0.980 → 0.990** on Llama, same quantity, same artifacts. The population named was *"any
exposure-clean form"*; the population meant was *"the three new semantic-ladder forms"*.

## `RAH2-C-026` — `RBD-R-033` is scoped to **behavioural** readouts

`reports/RAH_ACTIVATION_ASSAY_REPORT.md:11` introduces it as *"a structural claim about **behavioural**
readouts"*. `id07_raw` is an activation-level patchscope. So `RAH2-C-019`'s attempt to refute (A) with
it crossed a population line **in a correction entry about crossing population lines** — while (B),
the claim that does span *"either the behavioural or the activation level"*, was the one I quoted with
that clause silently **truncated and unmarked by ellipsis**.

`RAH2-C-020` already retracted the refutation of (A) on other grounds, so nothing downstream changes.
Recorded because the reasoning was wrong for a **second, independent** reason I had not noticed.

## `RAH2-C-027` — "the gate" is ambiguous in every entry after `RAH2-R-003`

The artifacts carry **two**: `mass_gate: 0.05` (the registered option-mass metric) and
`threshold: 0.1` (the transport/positive-control gate). `positive_control_ok` is computed **only**
from the 0.1 threshold on `p_concept`; **the 0.05 mass gate is stored and never applied by the
producer.** Entries move between them unannounced — R-003's *"0.78× the gate"* is the 0.05 one, its
*"0/25 `positive_control_ok`"* four lines later is the 0.1 one. No conclusion flips. Every future
entry must name which gate.

## `RAH2-C-028` — `H1`'s registered population was narrowed without saying so

§1.3 registers `H1` FALSIFIED as *"**every exposure-clean form** is below the mass gate on held-out
material"*. `RAH2-R-005` writes *"the **semantic forms** cannot report a concept that is literally
present"*. Under the max-over-(R,L) estimator R-004 itself published, exposure-clean `id07_raw` reads
**0.750 / 0.941** held-out — above 0.05 — so the registered condition is met only on the
selected-layer estimator. Also `RAH2-R-003`'s *"`H1` FALSIFIED for `cat_cue`"* is a per-form verdict
where §1.3 defines `H1` **form-universally**.

**Corrected `H1` statement:** *on the selected-layer estimator, every exposure-clean form except the
0-hop echo readouts is below the mass gate on held-out material; the echo readouts are excluded not
by mass but because `RAH2-C-020` shows they decode token identity.*

## Also confirmed clean by this auditor

Every number in R-003/C-017/R-004/C-018/R-005/R-006, independently re-derived — ratios, gate counts,
`p_codeword` values, the "30× weaker" anomaly (30.6), "maxima at L = 0, 4, 6", "three orders" (969×),
"2348×". The `exemplar_candidate_collisions` provenance claim checks out: present from
`rah2p3_p_lp_20260831_154049` onward, absent in every earlier artifact. `n_donors: 8` in all 16 RAH2
artifacts. The verifier is genuinely stdlib-only and asserts `donor_condition` on every artifact it
opens.

---

## `RAH2-R-007` — the handoff, and the audit of the handoff

`RESEARCH_HANDOFF.md` now carries the **RAH2 addendum** (`## ADDENDUM — RAH2 "readout problem"
phase`), in the same 8-section format as the RBD and RAH addenda.

**It was adversarially audited before being appended**, by a 5-lens fan-out (numbers · retracted
claims stated as live · scope words · references/reproducibility · completeness vs house style), each
lens's findings passed to a **skeptical verifier** instructed to default to *not real*. 11 agents.
**22 findings survived verification and all 22 were applied.** The draft's central claims survived;
its supporting sentences did not. The worst four:

* **`RAH2-C-022` recurred inside the handoff itself.** The draft paired P(concept) **0.3886**
  (development) with **4.01e-04** (held-out) as one collapse — but 4.01e-04 is the *option mass*; the
  same-statistic held-out value is **2.38e-04**. I wrote the field-confusion correction and then
  committed the same confusion **in the document warning about it**.
* **The correction chain was written backwards.** The draft said `RAH2-C-017`'s scoping was
  *withdrawn*. It was withdrawn by `RAH2-C-018` and then **REINSTATED** by `RAH2-C-020`, which
  retracted the `id07_raw` reading the withdrawal rested on. `RAH2-C-017` is **standing**. A live
  claim was filed as dead, in three places.
* **The `H1`/`H2` survival argument was stated with a false warrant.** The draft justified survival
  by *"these read at 2 hops"* — true of the few-shot forms, **false of the semantic forms**, which
  read at **9–17** hops (`synonym` 9/13, `cat_cue` 12/16, `defn_oneword` 13/17). The conclusion
  holds — all are non-zero — but the sentence carrying it did not survive inspection.
* **"0 arithmetic errors" was false.** `RAH2-C-006`, `-010`, `-012`, `-023` each corrected a
  **derived magnitude in prose**. The defensible claim is *"not one correction changed a value
  produced by a run"*, which is what the handoff now says.

Also fixed: a nonexistent job-id boundary (`827989`), a commit range that **excluded its own
preregistration** (`4b42a596..` drops `RAH2-PR-001`; now `4284e68c..`), `0.602–0.923` → **0.602–0.922**,
a "next step" described as a re-run when it is a **producer change** (`--capture-offset`, plus
relaxing `assert_token_is_part_of`), and the absence of any bank-population statement.

⚠ **The handoff asserts no number that this log does not already carry**, and every number in it was
re-derived from the artifacts by the audit. It adds **no new claim** — only scoping, and the four
constraints in its §6, which are a restatement of `RAH2-C-020` plus the three prior requirements.

### `RAH2-C-029` — the handoff violated the rule it was stating, and a guard caught it

The `RAH2-R-007` commit was **REFUSED by the pre-commit hook**:
`test_findings_the_ledger_leans_on_reach_the_deliverable` failed with

```
findings the claim ledger leans on that the deliverable never states: ['R-5']
```

The addendum's own namespace warning read *"Never write a bare `C-20` or `R-5` when citing it"*. The
extractor in `tests/test_my_ledger_propagation.py:317` deliberately **ignores prefixed ids**
(`RAH2-R-005` is invisible to it) and matches only **unprefixed** ones — so it read my illustration of
the forbidden pattern as a genuine citation of finding `R-5`, a Doublespeak-namespace finding the
deliverable does not state.

**The guard was right and the document was wrong.** An unprefixed id in a handoff *is* a citation,
regardless of the author's intent to use it as an example. Rewritten to state the rule without
instantiating it, and the sentence now names the guard that enforces it.

Two things worth keeping from this:

* **A rule stated by example instantiates the thing it forbids.** This is the same shape as
  `RAH2-C-022` recurring inside the document warning about `RAH2-C-022` — the third time this phase
  that a warning contained its own violation.
* **The guard fired on a document, not on code, and it fired on a commit I was confident in.** It is
  the only defect this phase that was caught by automation rather than by an auditor or by me.

---

## `RAH2-R-008` — the two items the log left owed, closed

No registered gate remains and the queue is empty. Both outstanding **owed** items are now done; no
new hypothesis was opened and no new receiver form was added.

### 1. `RAH2-DR-002` D11 implemented — provenance is now ATTESTED, not asserted

D11 recorded that every job id, commit and `dirty=0` in this log is **prose**, checkable only against
SLURM logs that are not part of the record, and filed the fix as *"not yet implemented"*. It is now
implemented: `provenance()` in `rah_preflight_transport.py` emits, into every artifact,

`git_commit` · `git_dirty` · `slurm_job_id` · `slurm_nodelist` · `hostname` · `argv` ·
`started_utc` · `finished_utc` · `python`

⚠ **Into every `rah_preflight_transport.py` artifact — NOT every artifact in the project.**
`src/boombness/rah_transport_assay.py` (`RAH_TRANSPORT_ASSAY/1`) is the other transport writer in the
same package and still emits **no** provenance block (`RAH2-C-030` F6).

Design notes worth keeping:

* **Every field degrades to a string or `None` rather than raising.** A provenance block must never
  be the reason a completed multi-hour sweep fails to persist — the opposite of this repo's usual
  "resolvers should raise" rule, and deliberately so: this one is *metadata about* a result, not an
  input *to* it.
* `started_utc` is stamped **before the model load**, `finished_utc` at write. ⚠ Both are the
  **running node's** clock, which was measured ~3 min from the login node's during this phase — so
  they date the run, they do not order it against `squeue` output.
* **Retrospective limitation:** the 16 RAH2 artifacts already on disk **cannot** be back-filled and
  do not carry the block. Their provenance stays prose. This helps the next phase, not this one.

`+1` guard test (`tests/test_rah_preflight_spans.py` 9 → **10**), **RED-checked**: dropping
`"provenance": prov` from the written dict turns it red. ⚠ The wiring half is a **source check**, not
a round-trip — running `main()` needs a GPU and a model load — so it catches the key being dropped,
not a bug in what it holds. Stated here rather than left for an auditor to find.

### 2. A stale `OPEN` marker closed in place

`RAH2-C-006` ended *"`H1`'s held-out status for `cat_cue` is **OPEN, not falsified**"*. `RAH2-R-003`
closed it, but **`RAH2-C-006` itself carried no forward pointer**, so a reader stopping there carried
away "OPEN". A `✅ CLOSED by RAH2-R-003` marker is now inline at `RAH2-C-006` — the same defect
`RAH2-C-024` fixed at `RAH2-R-003`, found by grepping the log for its own unresolved-status phrases.

**That grep is worth inheriting**: `grep -n "is OPEN\|is owed\|not yet implemented\|filed, not"` over
an append-only log finds every promise the log made to itself and did not visibly keep.

---

## `RAH2-PR-004` — the capture-site control: is the positive control a copy test? — registered before any forward pass

**Status: PREREGISTERED (prospective).** Written and committed **before** any `PR-004` forward pass.
This is the step `RAH2-R-005` §6 named as *the cheapest decisive next test*, and §6 also says it must
be registered as a new `PR` id first. **No new receiver form is added** — the frozen Stage-A grid and
all three existing form sets are untouched. What changes is **where the donor is captured.**

### The question, and why it is not a rescue attempt

`RAH2-C-020` retracted this phase's positive result by showing `id07_raw` is a token decoder. That
diagnosis was made **retrospectively**, from a comparison I happened to have (inject the codeword,
get the codeword). `RAH2-PR-004` makes the same diagnosis **prospectively**, and generalises it into
a reusable validity check.

Every `direct_harmful` positive control in the RAH/RAH2 preflight — **12 artifacts** — captures the
donor at the **concept's own surface token** (`donors[].piece` == the concept), by construction at
`rah_preflight_transport.py:391-397`. **A positive control whose donor surface IS the target cannot
distinguish transport from copying.** That is not a hypothesis; it is a property of the construction,
and it is why `RAH2-C-020` was possible at all.

> **`H3`.** A receiver that passes the positive control **only** because the target is the injected
> token will **collapse** when the donor is captured at a position where the concept is *present in
> context but not on the surface*. A receiver that genuinely reads content from the representation
> will **survive**.

### The intervention: a capture-site offset, not a new form

`rah_preflight_transport.py:391-397` hardcodes `pos_c = templated.lower().rfind(surf.lower())` and
then **asserts** the captured token is part of `target_surface` (`assert_token_is_part_of`, :300-306,
raises `SystemExit`). Two changes, both narrow:

* add `--capture-offset N` (default **0** — so **every existing invocation is bit-identical**);
* when `N != 0`, capture at `p + N` and **relax that one assertion**, replacing it with a recorded
  `capture_piece` field plus a bounds check.

**Registered offset: `N = +1`** — the token immediately after the concept surface. Chosen because it
is the minimal displacement that removes the surface identity while staying inside the same clause,
and because "minimal" is the only principled choice available without fishing over offsets.
**⚠ One offset only. Sweeping N and reporting the best would be exactly the two-free-parameter
maximisation `RAH2-C-002` and `RAH2-C-018` were raised for.**

### Populations, gates, metrics — all inherited, none new

Donor `direct_harmful`; form set `fewshot` (which carries `id07_raw`, `id07_tmpl`, `fc_probe_last`,
`fewshot_cat`, `fewshot_syn`); development `carrot↔bomb` **and** held-out `lantern↔poison`; both
models; 8 donors; the same 5 receiver depths; the **0.1** positive-control gate (naming it explicitly,
per `RAH2-C-027`). **4 jobs**, same shape as the `rah2pcf_*` runs.

**The `N = 0` arm already exists** (`rah2pcf_{p,q}_cb`) and is the paired comparison. ⚠ It exists on
the **development** bank only, so the held-out cells have **no `N = 0` counterpart** and are
descriptive, not paired.

### Outcomes, fixed now

| result at `N = +1` | reading |
|---|---|
| **`id07_raw` collapses below the 0.1 gate while `fc_probe_last` survives** | `H3` SUPPORTED. The copy diagnosis of `RAH2-C-020` is confirmed **prospectively**, and the capture-site control becomes a **required** validity check for every future positive control in this project |
| **both collapse** | the offset destroyed the signal rather than isolating copying — the control is **uninformative** and `H3` is CANNOT ANSWER. ⚠ This is the most likely failure mode and it is **not** evidence for either side |
| **`id07_raw` survives** | **`RAH2-C-020`'s copy diagnosis is WRONG** and the retraction must itself be revisited. Registered now so that this outcome cannot be quietly dropped |
| any few-shot form rises above 0.1 | recorded, **not** interpreted — `H1`/`H2` are closed and a new preregistration would be required to reopen them |

### What this does NOT license

⚠ **`H3` says nothing about the doublespeak mapping.** It is a claim about **instrument validity**.
A pass does **not** re-open Track A (`RAH-R-018` stands at **A-IV**), does **not** revive
`RAH2-R-005`, and does **not** bear on `H0`, which `RAH2-C-020` confirmed.

⚠ **`N = 0` is the default and must stay so.** If `--capture-offset` ever silently changes the
default, every prior artifact becomes non-reproducible. A guard test pins the default before the
runs.

---

# `RAH2-DR-003` — the provenance block audited before it attests anything

`RAH2-R-008` shipped provenance and `RAH2-PR-004`'s runs would be the **first artifacts to carry
it** — auditing after running would defeat the point. One read-only auditor, scoped to commits
`080ce1cd` / `6ecf1e60`. **7 findings, all verified by me, all applied.** Registered as
`RAH2-C-030`.

## The two that would have corrupted every future artifact

* **F2 — provenance was sampled AFTER the sweep.** `prov = provenance()` sat at line 531, below the
  grid loop at 448, so `git_commit` / `git_dirty` described HEAD at **write** time. A multi-hour run
  launched at commit A and written after commit B would have **silently attested B** — precisely
  what D11 exists to prevent, and not theoretical: **8 commits landed here on 2026-08-31 alone** and
  a third writer shares the tree. Moved to line 387, before the sweep.
* **F1 — `git_dirty` reported a CLEAN TREE whenever it knew nothing.** `bool(_git(...))` collapsed
  *failure* and *empty output* to the same `False`. A node without `git` on PATH, a 20 s timeout on
  this NFS repo, or a dubious-ownership refusal in this shared tree would each have produced an
  artifact **asserting the code was unmodified, from a run that could not read the repo at all.**
  Now tri-state (`True` / `False` / `None`) plus a `git_ok` flag: **a tree we cannot read is not a
  clean tree.**

## The guard that was supposed to catch this could not

* **F3/F4 — 4 of 6 mutations the auditor tried stayed green**, including `prov = {}` (shipping a
  2-field block) and moving the timestamp after the model load. My assertion checked the stamp
  *existed*, never its *position*, and nothing tied the **written** object to the function's return.
  Fixed with index comparisons (`i_stamp < i_load`, `i_prov < i_sweep`) and a `prov = provenance()`
  check.
* **And my first fix for F1 was itself vacuous** — it asserted a literal substring was absent, so
  rewriting the same defect as `bool(status)` sailed straight past it. **I verified this by
  mutation and watched my own new guard pass.** Replaced with a **functional** test: `provenance()`
  now takes an injectable runner, and the guard drives a *failing* git (raising, and returning
  128 "dubious ownership") and demands `git_dirty is None`. That mutation now exits 1.

> **This is `RAH2-C-023` for the third time: a guard written against a defect, in the shape of the
> defect I happened to imagine, rather than against the property I actually wanted.** The fix that
> works is always the functional one — drive the failure, don't grep for it.

## Three smaller, all real

* **F5** — the new code's own comment said the timestamps were the **login** node's clock. They are
  the **compute** node's (`main()` runs in the job), which is what the log said four lines away. The
  comment contradicted the entry it pointed at, and would have made a reader read the ~3 min skew
  backwards. Corrected.
* **F6** — *"into every artifact"* overstates: `rah_transport_assay.py` is the other transport writer
  in the same package and still emits none. Scoped in place.
* **F7 — my "worth inheriting" grep missed two live instances of the very defect it was built to
  find.** `grep "is OPEN\|is owed"` is defeated by the log's own markdown emphasis (`is **OPEN**`),
  so line 637 (`cat_cue` "OPEN" after `RAH2-R-003` closed it) and line 763 (the positive-control arm
  "owed" after `RAH2-C-017` ran it) both survived. Both now carry inline ✅ pointers, and the
  inheritable form is the **case-insensitive, emphasis-tolerant** one:
  `grep -nEi 'is +\**(OPEN|owed)\b|not yet implemented|filed, not|remains? open'`.

## Clean, and worth recording as clean

`started_utc` scope (no `NameError` path that could lose a completed sweep), `HERE`/`subprocess`
imports, and **hang risk**: the auditor checked empirically that `subprocess.run` on `TimeoutExpired`
kills and reaps rather than blocking on a second `communicate()`, and that the `soft` NFS mount
returns EIO rather than parking git in unkillable D state. The residual exposure was never a hang —
it was the timeout being **misread as clean**, which is F1.

`+1` guard test (10 → **11**), and the two previously-green mutations now exit 1.

⚠ **`RAH2-PR-004` is unaffected** — it was registered before this audit and none of its gates,
populations or outcomes changed. What changed is that its artifacts will now carry provenance that
means what it says.

---

## `RAH2-C-031` — `RAH2-PR-004` is registered and will **NOT** be executed by this phase. A second writer is running the same question as RAH3

**Recorded so that a future reader does not find a registered preregistration with no result and
assume it is pending.** This is the dangling-promise defect `RAH2-C-006` / D11 / `RAH2-C-024` were
each raised for, caught this time **before** it became stale.

### What happened

`RAH2-PR-004` was registered at `4e3fab1d` (19:0x) for the capture-site control. Within the same
hour a **second session** — not this one — committed `f2a42a6c`
(`RAH3-PR-001 + R-001/R-002 + C-001/C-002`, *"the non-copy capture site, registered and
instrumented"*) onto this same branch, with its own log
(`external_md/RAH3_NONCOPY_CAUSAL_READOUT_AND_POWERED_BEHAVIOR_PLAN_AND_PROGRESS.md`), its own
guard tests, four `runargs/rah3/nc_*` argfiles and `scripts/rah3_capture_site_probe.py`.

**That is the same scientific question `RAH2-PR-004` registered**, reached independently from the
same `RAH2-C-020` copy diagnosis.

### Status, stated plainly

| | |
|---|---|
| `RAH2-PR-004` | **REGISTERED, NOT EXECUTED, and not to be executed under this id.** Superseded in practice by `RAH3-PR-001` |
| the design in it | still valid, and it differs from RAH3's: PR-004 proposed `--capture-offset` **inside** `rah_preflight_transport.py` with `N = 0` default; RAH3 built a **separate probe script**. RAH3's choice is the safer one — it leaves the shared producer untouched |
| what a future reader should cite | **`RAH3`'s result, not `RAH2-PR-004`** |

⚠ **A preregistration executed by a different session under a different id is a provenance gap.**
PR-004's registered outcome table — including the branch where *"`id07_raw` survives"* would mean
`RAH2-C-020`'s retraction is wrong — is **not** automatically inherited by RAH3, because RAH3
registered its own. Anyone reconciling the two must check that the "retraction is wrong" branch
survived into RAH3's outcome space; **this log cannot vouch that it did.**

### RAH2's record verified intact under the concurrent commit

`f2a42a6c` is **purely additive** — 8 new files, and `git diff 7906faae..f2a42a6c` over
`rah_preflight_transport.py`, `tests/test_rah_preflight_spans.py`, `scripts/rah2_verify_r005.py` and
this log is **empty**. Re-run after it landed: verifier **39/39**, guard tests **11/11**, the frozen
Stage-A grid still exactly 4 forms, and the `RAH2-C-030` provenance tri-state intact.

### The operational note worth inheriting

The sprint brief said **ONE WRITER ONLY**, and for a while there were two, on one branch. It
surfaced as a **stale `.git/index.lock`** (0 bytes, orphaned, no owning process) that refused my
commit — *not* as a content conflict. What made that recoverable rather than destructive:

* **back the changed files up before touching git state**, so nothing depends on the recovery going
  well;
* **check twice, minutes apart, for a live `git` process** before removing a lock — a lock with an
  owner must never be removed, and one without an owner is inert;
* **stage by explicit path, never `git add -A`** — an `-A` here would have swept the other session's
  in-flight, uncommitted RAH3 files into a RAH2 commit;
* **do not read, edit, stage or delete the other writer's files**, and do not push their unpushed
  commits — they may still be amending.

### `RAH2-C-031` follow-up — the provenance gap is **CLOSED**, verified by reading, not assumed

`RAH2-C-031` flagged that a preregistration executed by a different session under a different id does
not automatically carry its outcome table across, and named the branch that mattered: the one where
*"`id07_raw` survives"* would mean **`RAH2-C-020`'s retraction is itself wrong**. It said, in terms,
**"this log cannot vouch that it did"** survive into RAH3's outcome space.

**Checked (read-only; the RAH3 log was not edited, staged or touched). It did survive, explicitly.**
`external_md/RAH3_NONCOPY_CAUSAL_READOUT_AND_POWERED_BEHAVIOR_PLAN_AND_PROGRESS.md:388-390`:

> ⚠ **`RAH2-PR-004`'s inherited prediction:** `id07_raw` collapses, `fc_probe_last` survives. **This
> is a registered prediction, not a required outcome.** If `id07_raw` *survives* at `N = +1`, then
> `RAH2-C-020`'s copy diagnosis is wrong and the retraction must itself be revisited — registered now

RAH3 cites `RAH2-PR-004` **by name**, inherits its prediction, and marks it a *prediction* rather
than a required outcome — which is stronger than PR-004 stated it. RAH3 also carries `RAH2-C-020`
into its constraint table (`:44`, non-zero hops) and its own do-not-quote list (`:60`).

**So the cross-phase handoff is sound and `RAH2-C-031`'s ⚠ is discharged.** The correction I was most
worried about losing — the one that says *my own retraction could be wrong* — is the one the next
phase carried forward most explicitly.

> **The general point, worth inheriting:** when a phase hands a question to a *different* session,
> the thing to verify is not that the question survived — it is that **the branch where the handing
> phase was wrong** survived. A successor that inherits only the predicted outcome has inherited a
> hypothesis; one that inherits the refutation branch has inherited an experiment.

**`RAH2` has no remaining open item.** Every preregistration is resolved or explicitly superseded,
every correction is applied, every unresolved-status phrase in this log carries a forward pointer, and
the one claim this log could not vouch for has now been checked and closed.

---

## `RAH2-C-032` — commit `7906faae` carries 226 lines of another session's code under a RAH2 message, and `RAH2-C-031`'s staging rule is the advice that failed

**The last correction of this phase, and the only one about the repository rather than the science.**
Established by a 9-agent audit whose every finding was independently reproduced before being written
here; the commands are quoted so this is re-runnable.

### 1. What `7906faae` actually contains

Its message describes only the `RAH2-DR-003` / `C-030` provenance audit and ends **"PR-004
unaffected"**. It touches three files (+384 / −25):

| file | +/− | contents |
|---|---|---|
| `external_md/RAH2_..._PROGRESS.md` | +77 / −2 | **100 % RAH2** |
| `tests/test_rah_preflight_spans.py` | +49 / −1 | **100 % RAH2** — all 49 are `C-030` guards |
| `src/boombness/rah_preflight_transport.py` | **+258 / −22** | **32 RAH2, 226 RAH3** |

```
git diff --no-index --numstat <4e3fab1d:producer> <pre-commit backup>  ->  32  11
git diff --no-index --numstat <pre-commit backup>  <7906faae:producer> -> 226  11
git show --numstat 7906faae -- src/boombness/rah_preflight_transport.py -> 258  22
```

**32 + 226 = 258 and 11 + 11 = 22 — exact reconciliation with git.** The foreign 226 are
`resolve_donor_capture`, `assert_capture_consistent`, `_char_spans`, `_codeword_tok_idx`,
`sha256_file`, `_git_branch`, `_diff_sha256`, the `--capture-mode` / `--capture-offset` argparse
block, the donor loop rewritten onto them, `rah3_eligible`, and the extended `prov[...]` fields.
Ownership is corroborated **independently of the backup**:
`git log --all -S'resolve_donor_capture' -- <path>` returns **`7906faae` alone** as the introducing
commit, and RAH3's own §8 claims those symbols by name.

⚠ **Qualifications, all published rather than buried.** A stricter content-only reading (capture
mechanism + argparse + loop + cell fields only) gives **186**; the 40-line gap is `sha256_file`,
`_git_branch`/`_diff_sha256` and the `prov` extensions, which RAH3's §8 also claims — so the honest
band is **186–226, with 226 the figure git arithmetic forces**. One line,
`prov['python_executable']`, is claimed by **neither** log, so **225** is the count excluding it. The
pre-commit backup is an out-of-tree scratchpad file — **corroborating, not git-attested** — though
its parent-diff being 100 % provenance-only is strong internal corroboration.

### 2. RAH3's "14" is not a wrong measurement — it is a different one, and the distinction matters

Their `RAH3-C-002` says *"plus 14 added lines of RAH3's `resolve_donor_capture` / `NON-COPY
VIOLATION` implementation"*. Measured:

```
git show 7906faae | grep '^+' | grep -c 'RAH3\|NON-COPY'   ->  14   exactly
```

**14 is exactly right as a count of added lines that MENTION RAH3 markers. It is not a count of
implementation lines**, which is 186–226 — an understatement of **13–16×**. Their *substantive*
claim ("my uncommitted capture implementation was swept into your commit") is **correct, and
understated by its own number**. ⚠ Which computation produced their 14 is **not established** —
`capture_offset` also greps to 14, and two of their helpers happen to span 14 lines. Calling it an
estimate would be inference, so it is not called one.

> **The lesson, and it is a sharp one:** *that same grep is a sound TRIGGER and an unsound RULER.*
> Run **before** committing, a non-zero hit is a correct STOP. Run **after**, as a measure of what
> was swept, it undercounts by more than an order of magnitude. I published "~16× under" about a
> peer earlier in this session; the accurate statement is that they measured a different quantity
> correctly, and I should not have implied carelessness.

### 3. Scope of the contamination — bounded, and clean in the other direction

`4e3fab1d`, `83179b60`, `a4f5d7c8` are **log-only and clean** (`RAH3` appears solely in RAH2 prose
*about* RAH3). Within `7906faae` the contamination is confined to the one producer file. The reverse
direction is clean: `f2a42a6c` is 8 files, all `A`, all `rah3`-namespaced, **no RAH2-owned path**.

And "RAH3 measured when their tree held less" is **ruled out**: the producer blob is byte-identical
between `7906faae` and `f2a42a6c` (`7a62d51b…`), so the sweep took **100 %** of the producer-side
changes. ⚠ Verified over these four commits only; nothing is claimed about earlier ones.

### 4. Why `RAH2-C-031`'s rule failed — it is the advice, not the discipline

`RAH2-C-031` states, verbatim:

> *"stage by explicit path, never `git add -A` — an `-A` here would have swept the other session's
> in-flight, uncommitted RAH3 files into a RAH2 commit."*

**Two defects.**

**(a) The tense is counterfactual and the event had already happened.** *"would have swept"* was
written at `83179b60`, **12 min 19 s after** `7906faae` had already swept — **via exactly the
explicit-path staging the bullet prescribes as the remedy.**

**(b) The neighbouring claim is false.** `RAH2-C-031` also says RAH3's separate-script choice *"leaves
the shared producer untouched"*. The producer is not untouched, and **RAH2 is who touched it**:
`git show HEAD:<producer> | grep -c 'capture_offset'` → **16**.

**The mechanism the bullet misses.** `git add -- <path>` snapshots the **current worktree content**
of that path. It is scoped **by path, not by author, session or hunk.** Two distinct leaks:

* **(a) shared-index leak** — a bare `git commit` commits whatever *anyone* staged. Fixed by
  `git commit -- <paths>`.
* **(b) same-file leak** — when two writers edit the *same* file, path scoping is **no protection at
  all**, because the foreign edits are inside the very blob being snapshotted. **`7906faae` is
  case (b), and `git commit -- <paths>` does not fix it.**

⚠ And the file set carried **no signal**: `rah_preflight_transport.py` and
`test_rah_preflight_spans.py` both **predate the RAH2/RAH3 split**. They are shared producers RAH2
was legitimately editing — not files RAH2 owned. `git diff --cached --stat` would have shown three
files, all plausibly in lane, and caught nothing.

### 5. The rule that would have caught it

**Structural, and the only convention-free one — use a separate worktree:**

```
git worktree add ../wt-rah2 behavioral-causality-sprint
```

A worktree has **its own index and its own checkout**, so leaks (a) and (b) are both impossible.

**If already sharing a tree — gate on the staged CONTENT, not the file set:**

```
git diff --cached -- <paths> | grep -nE 'RAH3|NON-COPY|resolve_donor_capture|capture_mode'   # any hit = STOP
git commit -m "..." -- <paths>
```

⚠ **This grep is sufficient only under a namespace-tagging discipline.** It fires here solely
because RAH3 tagged its docstrings `RAH3-PR-001`; **untagged** foreign edits to a shared file slip
straight past it. `git add -p` is hunk-scoped and would fix leak (b), but interactive add is
unavailable in this harness; `git stash push --` is barred by standing repo rule.

**Post-commit, verify what actually landed:**

```
git show --numstat HEAD
git log --all --oneline -S'<my new symbol>' -- <path>
```

### 6. What is NOT being done, and why

**History is not rewritten** — `7906faae` is public, RAH3 built on it, and its message stays
materially wrong with this entry as the correction. **`RAH2-C-031` is not edited**; it stands with
this entry superseding its staging bullet, per the append-only rule.

> **The signature holds to the end.** Thirty-two corrections in this phase and **not one changed a
> value produced by a run.** This last one is not about the science at all — it is about a commit
> message that describes 32 lines of work while carrying 258 — and it is still the same failure
> mode: *the numbers kept being right and the sentences around them kept being wrong.*

### `RAH2-C-029` recurrence — the same guard refused the same defect again, in the file that documents it

Committing `reports/RAH2_SPRINT_SUMMARY.md` was **REFUSED** by the pre-commit hook:

```
findings the claim ledger leans on that the deliverable never states: ['R-7', 'R-8']
```

The count-correction I had just written into both the summary and the handoff read *"Updated after
`RAH2-PR-004`, `R-007`, `R-008`, …"* — **unprefixed**, which `tests/test_my_ledger_propagation.py`
correctly reads as citing Doublespeak findings `R-7` and `R-8`.

`RAH2-C-029` recorded exactly this defect, and the handoff sentence that states the rule —
*"Always cite these ids with their full `RAH2-` prefix … the pre-commit hook refuses the commit"* —
sits **at line 493 of the same file whose line 509 broke it**. Fixed by prefixing; all 16
ledger-propagation guards pass.

> **Third occurrence of one pattern this phase**: `RAH2-C-022` recurred inside the entry warning
> about `RAH2-C-022`; `RAH2-C-029` was a rule stated by instantiating what it forbids; this is that
> rule broken 16 lines below where it is written. **Knowing the rule, and having just written it
> down, does not prevent breaking it — only the automated check does.** Both times the guard caught
> it and I did not.
