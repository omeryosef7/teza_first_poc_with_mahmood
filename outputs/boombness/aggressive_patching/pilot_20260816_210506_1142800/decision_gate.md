# §5.4 Decision gate — `aggressive_patching/pilot_20260816_210506_1142800`

**Written 2026-08-17.** This file is a **mandatory named deliverable** of plan §5.4 and it was missing
while the progress board recorded P2.5 as DONE. The independent plan-coverage sweep found that
(finding 5.4a), and it also found that **two of the eight questions below had never been measured at
all** (5.4c → Q2, 5.4f → Q5). Both are answered honestly as *not measured* rather than argued around,
and the experiment that closes Q5 is now running.

Readout: `semantic_logodds` = log p(concept) − log p(codeword) at the answer position.
n = 8 families per pair, drawn from only **2 domains**. This is a **pilot**; every interval below
should be read with that in mind.

---

## 1. Can we make `carrot` internally more `bomb`-like by force? — **YES, but not where expected**

| arm | frac of baseline→ceiling span | paired-bootstrap CI |
|---|---|---|
| `transplant \| demos_only \| L18` (harm ctx) | **+0.839** | **[+0.574, +1.051]** |
| `transplant \| demos_only \| L8` (harm ctx) | +0.708 | [+0.538, +0.878] |
| `transplant \| demos_only \| L18` (benign ctx) | +0.821 | [+0.707, +0.936] |
| `transplant \| query_only \| L18` | **−0.584** | moves the WRONG way |
| `transplant \| demos_only \| all` (harm ctx) | **−0.764** | [−1.492, −0.210] |
| `self_swap_noop_check` | 0.000 max abs delta | — |

**The lever is the demonstration block, not the codeword token.** Transplanting the query codeword's
own states moves the reported meaning *away* from the concept.

⚠ **Arm-selection exposure:** +84% is one arm of ~130 in this run, and it is **not uniform over
windows** — the all-layer demonstration transplant in the same context pair goes strongly the wrong
way. The *direction* of the finding is robust; the *magnitude* is specific to the single-layer L18
window.

## 2. Does this change behavior? — **NOT MEASURED. Honest answer: unknown.**
No behavioural readout was ever taken under a §5.1 transplant or a §5.2 positional additive patch.
Every arm in this run scores `query_kind = semantic_one_word`, i.e. a forward-only semantic readout.
The behavioural evidence the sprint does have (G4) is a **different manipulation** — additive, single
layer L8, all-position, on `behavioral` prompts — so it cannot answer Q2 for *this* intervention.
**Closing it requires transplant arms run with `--query-kinds behavioral` plus the judge.**

## 3. Does it change ASR? — **NOT MEASURED for this intervention** (same reason as Q2)
For the *additive* intervention at L8, ASR is measured and reported in G4: baseline 0.219 → 0.081 at
α=+0.25 and 0.148 at α=−0.25. Both signs suppress, so ASR does not follow the sign of the axis.

## 4. Does it change refusal? — **NOT MEASURED for this intervention**
For the additive L8 intervention: refusal 0.074 → **0.696** at α=+0.25 and 0.067 at α=−0.25. Of the
prompts each arm suppressed, 90.1% are keyword refusals for +0.25 versus 0.0% for −0.25 — the two
signs suppress by different routes.

## 5. Does it preserve comprehension? — **NOT MEASURED ANYWHERE IN THE SPRINT until today**
This is the plan's **§2.6 mandatory control** and it is the single largest hole the coverage sweep
found. No intervened arm in §5, §10 or §12 carried a comprehension readout. `coherence_gate.py` was
used as a substitute, but it detects **degenerate text** (repetition, truncation), which is a weaker
and different property than *"does the model still understand the codeword mapping"*.

**Consequence for a claim already published:** G4 reports that +0.25 suppresses ASR by triggering
refusal. Without a comprehension control, an alternative reading is not excluded — that the
intervention damaged the model's grasp of the mapping and the refusal is downstream of confusion
rather than of recognised harm.

**Now running** (jobs 762155–762158): the +0.25, −0.25, `random`, and `project_out` arms re-scored with
`--query-kinds comprehension_usage,semantic_one_word`, which yields p(coded) vs p(literal) **under the
intervention**. This gate will be updated with the result, whichever way it falls.

## 6. Which token positions matter most? — **the DEMONSTRATION positions**
`demos_only` moves the readout +71–84% of span; `query_only` moves it −58%; `last_demo` alone +7–10%;
`first_demo` ≈ −2%. Meaning is retrieved from the demonstration block at answer time rather than stored
in the codeword token.

## 7. Which layers/windows matter most? — **L8 and L18, single-layer windows**
Best arms are the single layers L8 (+0.708) and L18 (+0.839). Wide windows are *worse*, and the
all-layer transplant reverses sign.
⚠ **Coverage gap (finding 5.1h):** individual layers L9, L10, L14–L17, L19–L21 were never run; L14–L21
exists only as coarse bands. Since the headline is a *single-layer* effect whose neighbouring band arm
reverses sign, the layer profile around L18 is under-sampled.

## 8. Is this promising enough for objective extraction? — **NO, and this was the right call**
It looked promising here — a large, well-controlled representational effect with a clean self-swap
no-op. It did not survive the behavioural test: G4 found **both signs of `d_surface` suppress ASR**, so
attack success does not follow the sign of the axis, and only +0.25 exceeds a 4-draw random-control
band (p=0.0014) — doing so by *triggering refusal*. §12 was therefore **not built**, which is the
decision this gate exists to force.

---

### What this gate cannot support
- Any behavioural claim about the **transplant** intervention (Q2/Q3/Q4 unmeasured for it).
- Any "preserves comprehension" claim (Q5 unmeasured until jobs 762155–762158 land).
- A magnitude for "transplanting the demonstrations", as opposed to for the L18 window specifically.
- Anything with 8 families from 2 domains treated as 8 independent units.
