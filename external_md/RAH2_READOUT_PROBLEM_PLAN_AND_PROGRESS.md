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
