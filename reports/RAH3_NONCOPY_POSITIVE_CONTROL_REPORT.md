# RAH3 — Non-copy positive control: does the transport assay measure semantics or copying?

**Verdict: TRACK A REMAINS CANNOT ANSWER — VALID READOUT NOT ESTABLISHED.**
Llama-3.1-8B = **P-B**. Qwen3-14B = **P-D**. Held-out **NOT RUN — GATED OFF**.

Generated from `reports/RAH3_CLAIM_LEDGER.json`. ⚠ No sentence here is stronger than its ledger entry.

---

## 1. The question, and why it had to come first

Every `direct_harmful` positive control in this project's activation-transport infrastructure
captured the donor at **the concept's own surface token**. A receiver could therefore "succeed" by
carrying lexical token identity rather than semantic content, and **transport and copying were
indistinguishable by construction.** `RAH2-C-020` retracted that phase's headline on exactly this
ground — retrospectively, from a control that had been run eight times and not read.

`RAH3-PR-001` asked the question prospectively:

> **`H4`.** A receiver that passes only because the target *is* the injected token will **collapse**
> when the donor is captured where the concept is present in context but not on the surface. A
> receiver that genuinely reads content from the representation will **survive**.

## 2. Design

| | |
|---|---|
| capture | `--capture-mode offset --capture-offset +1` — the token immediately after the last concept-surface occurrence |
| **the captured token** | **`'.'`** on all 8 donors × 2 models × 2 banks; not the concept, not the codeword, not a candidate label |
| offset provenance | **pre-committed** in `RAH2-PR-004` before any transport number at any offset existed; carried forward unchanged |
| donors | `direct_harmful` / behavioral / `n_examples=8`, first 8 by `prompt_id` |
| development | carrot ↔ bomb, both models |
| held-out | lantern ↔ poison — **registered, argsfiles committed, NOT RUN** |
| forms | the existing RAH2 `fewshot` set; **no new receiver form was invented** |
| thresholds | `TRANSPORT_POSITIVE_CONTROL_THRESHOLD = 0.10`, `MASS_GATE = 0.05` — two different numbers, never "the gate" |

**The selection rule (`scripts/rah3_select_config.py`) was committed at `8e9ca447`, before either
development artifact existed**, and was applied without modification.

## 3. The result — `H4` SUPPORTED, and the effect is enormous

Moving the donor capture **one token**, `' bomb'` → `'.'`, nothing else changed:

| form | hops | exposure-clean | Llama N=0 → N=+1 | collapse | Qwen3 N=0 → N=+1 | collapse |
|---|---|---|---|---|---|---|
| `id07_raw` | **0** | yes | 0.8409 → 0.001223 | **688×** | 0.8404 → 0.0001042 | **8 062×** |
| `id07_tmpl` | **0** | yes | 0.5011 → 1.17e-05 | **42 809×** | 0.01419 → 0.000101 | **141×** |
| `fc_probe_last` | 8 | **no** | 0.9087 → **0.1932** | **4.7× — PASSES** | **1.000** → 0.000539 | **1 855×** |
| `fewshot_cat` | 2 | yes | 0.06565 → 0.0001009 | **651×** | 0.00871 → 8.952e-05 | **97×** |
| `fewshot_syn` | 2 | yes | 0.01965 → 0.0001283 | **153×** | 0.09645 → 0.0002094 | **461×** |

**Every cell collapses.** The 0-hop token decoders fall by 2.8–4.6 orders — `RAH2-C-020`'s copy
diagnosis, confirmed **prospectively**.

### ⚠ The single most important number

**Qwen3's `fc_probe_last` positive control was `p_concept = 1.000` at offset 0 and is `0.000539` at
offset +1 — a 1 855× collapse.** A perfect score, the kind on which an instrument is declared
validated, was **essentially entirely a copy effect** — and this is the **multi-hop** reference, not
one of the 0-hop forms already retracted.

## 4. What Llama's P-B does and does not establish

**Does:** off-surface activation transport is real on Llama. `fc_probe_last`, `R=4`, donor `L=11`,
**8 hops**: `p_concept = 0.1932` against an unpatched prior of `0.005278` (uplift **+0.1879**),
`p_codeword = 0.0023`, option mass **0.746**. **A period token one position after the concept
carries enough of the concept for a receiver to name it**, and the concept beats the codeword ~84×.

**Does not:** ⚠ `fc_probe_last` **prints all four candidate labels in its prompt.** It fails
requirement 1 by construction and can never carry a Track-A claim. The best **exposure-clean** cell
is `fewshot_syn R=16`: `p_concept = 1.283e-04`, option mass **1.329e-04 — 376× below `MASS_GATE`**.

**So `H0` is confirmed again, now off-surface:** mass comes from printing the candidates. Remove them
and the readout falls 3–4 orders on both models.

## 5. Why held-out was not run

`held_out_may_run = False`, computed by the committed script after Qwen3 returned **P-D**. Running a
frozen configuration on held-out material would have measured an instrument that failed its own
development validation. ⚠ Per §61 nothing was added, searched, or lowered to avoid this outcome:
**no new forms, no layer scan, no offset sweep, no threshold change, and `fc_probe_last` was not
promoted to the scientific answer.** The held-out argsfiles remain committed and unrun.

⚠ **`RAH-R-018` is untouched** — **A-IV / CANNOT ANSWER**, permanently. This was a *new* experiment
returning a *new* negative.

## 6. Verification

| | scope | result |
|---|---|---|
| verifier **A**, imports **no** producer helper | semantics re-derived from bank + tokenizer | **289 checks, 0 failures** on each artifact |
| verifier **A**, mutation-tested | **17 distinct** assertion classes | **17/17 RED**, incl. a **0.0001 %** relative perturbation |
| verifier **B**, own forward hook | the frozen cell `fc_probe_last R=4 L=11` | job 831512 |
| guard list / targeted / **full suite** | — | 341 / 39 / **1644 passed, 7 skipped**, tree clean before and after |

Two defects were caught **before** the first job and would each have corrupted the result:
**`MASS_GATE` was a dead literal** enforced by nothing (`RAH3-C-003`), and **a patch that never
applied would have been scored as a scientific null** (`RAH3-C-004`).

## 7. ⚠ Limits — the result is narrower than it sounds

* **Development only.** carrot↔bomb, 8 donors, one condition, no held-out cell. A statement about
  the **instrument**, not about doublespeak.
* **One offset.** `N = +1` is one pre-committed site, deliberately not swept. A richer non-surface
  site — `' context'` at `+4` — might transport more. ⚠ Testing that needs a **new preregistration**;
  doing it now would be the search-until-it-passes §61 forbids.
* **The collapse is not decomposed.** *"Off-surface transport is weak"* and *"`'.'` is a poor
  carrier"* are **not distinguished** by this design.
* **`0.1932` is `selection_max`** over 31 × 5 cells, unpenalised — an upper bound, not an estimate.
* **Qwen3's P-D is about this assay on that model**, not about Qwen3.

## 8. What this licenses

**Nothing in Track A.** No intervention matrix, no relocation diagnostic, no equivalence test — all
were gated on P-A, which did not occur.

**One genuinely new question it does raise**, stated as a question and not begun here: *the concept
is demonstrably present off-surface on Llama and readable when candidates are printed. Is the
exposure-clean readout failure a property of the representation, or of every decoder tried so far?*
⚠ That needs a new preregistration, and `RAH3-R-006`'s own limits say the honest first step is to
distinguish "weak off-surface transport" from "`'.'` is a poor carrier" — which the current design
cannot.
