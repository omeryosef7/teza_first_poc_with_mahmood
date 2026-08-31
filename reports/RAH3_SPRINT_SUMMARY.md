# RAH3 sprint summary — non-copy causal readout validation + powered behavioural bank

**Self-contained.** Reading this requires no other document.

---

## The one-paragraph truth

RAH3 asked whether this project's activation-transport assay measures **semantics** or merely
**copies a token injected at the concept's own surface position** — because until that is settled,
no Track-A intervention result is interpretable. The answer is that **it was largely copying** — on Llama, where the comparison is clean.
Moving the donor capture **one token** off the concept surface, to the `'.'` that follows it,
collapses every receiver form on both models — the two 0-hop token decoders by **688×** and
**42 809×** on Llama and by **8 062×** and **141×** on Qwen3, ⚠ The Qwen3 **templated**-form comparisons — including the once-headline
**0.999999 → 0.000539** — are **CONFOUNDED** and withdrawn as clean measurements (`RAH3-C-013`:
the offset-0 comparator ran at `--enable-thinking false`, mine at the default). On Llama a genuine off-surface
transport signal survives — a period token carries enough of the concept for a receiver to name it
at `p = 0.1932` against a `0.0053` prior — **but only into a receiver that prints all four candidate
labels in its prompt.** Every exposure-clean multi-hop receiver fails, the best by **376×** below the
mass gate. **Track A therefore remains CANNOT ANSWER, and the held-out arm was correctly never run.**
Track B was independently found **blocked by material and power** before any behavioural compute was
spent.

## What was asked

Validate the instrument before running another intervention matrix; then, if and only if it
validates, reopen Track A; separately, recompute Track-B power and build a 38-domain behavioural
bank, stopping at a costed GO/NO-GO before ~20 GPU-hours.

## What was preregistered — before any forward pass

* **`RAH3-PR-001`** — the non-copy positive control: capture offset **`N = +1`** (pre-committed by
  the prior session's `RAH2-PR-004` before any transport number at any offset existed), nine per-row
  hard-fail invariants, a cross-row consistency assertion, a two-stage development→held-out design,
  and a **locked five-outcome taxonomy** (P-A … P-E).
* **`scripts/rah3_select_config.py`** — the deterministic selection rule, committed **before either
  artifact existed** and applied unmodified.
* No new receiver form was invented. The frozen Stage-A grid was untouched.

## What was run

| | |
|---|---|
| tokenizer-only capture-site probe | 8 donors × 2 models × 2 banks = **32 prompts**, no weights, no forward pass |
| configuration smoke | job 831249, the exact registered mode at `n_donors=2` |
| **development positive control** | jobs **831434** (Llama, 14:41) and **831436** (Qwen3, 30:14) |
| verifier A (CPU, no producer import) | 289 checks × 2 artifacts; 17/17 mutation classes RED |
| verifier B (GPU, own forward hook) | job **831541** on the frozen cell |
| reproduction manifest | **executed**, 49 headlines |
| tests | guard list **341**; full suite **1644 passed, 7 skipped**, tree clean before and after |

## What passed

* **`H4` PARTIALLY SUPPORTED.** ⚠ *"Every form collapses"* is **FALSE** (`RAH3-C-014`): on matched
  `(form, R)` pairs **5 of 50 rise**, one flipping **FAIL → PASS**. What stands: **on Llama**, on a
  25/25 bit-identical comparison, the 0-hop decoders collapse **688×** and **42 809×** —
  `RAH2-C-020`'s copy diagnosis confirmed **prospectively**.
* **Real off-surface transport exists on Llama** — `fc_probe_last`, `R=4`, donor `L=11`, 8 hops:
  `p_concept 0.1932`, `p_codeword 0.0023`, option mass **0.746**, captured on a period token.
* **Both verifiers agree**, the manifest reproduces **49/49**, and every guard was proven able to
  fail.

## What failed

* **No exposure-clean multi-hop receiver passes on either model.** Llama's best is **376×** below
  `MASS_GATE`; Qwen3's best over *all* forms is `0.000539`, **186×** below the transport threshold.
* **Qwen3 = P-D**: even the candidate-printing positive reference fails off-surface. The assay is
  **not validated** for this question on that model.
* **Track B is blocked.** The one baseline cell clearing 0.1375 is the **discovery** pair on one
  model. ⚠ **The 608-row 38 × 16 material DOES exist** (`RAH3-C-019` — my first reading was wrong);
  but its `n_examples` is `{1,2,4,8} × 152`, so the blocker is an **estimand** problem, not a
  shortage. ⚠ And `ICC = 0.09` is at the **extreme optimistic end** of this repo's own measured
  range of **0.000–0.755** (`RAH3-C-020`).

## What was declined

* **Held-out (lantern↔poison) was NOT RUN.** The committed gate returned `held_out_may_run = False`.
  ⚠ Nothing was added, searched, or lowered to avoid that: **no new forms, no layer scan, no offset
  sweep, no threshold change**, and `fc_probe_last` was **not** promoted to the scientific answer.
  The argsfiles remain committed and unrun.
* **No Track-B confirmatory matrix was costed or launched.** The ~20 GPU-hour gate **cannot be
  reached** — the population that would justify it does not exist.
* **No new 38-domain bank was built**, because the sprint's own premise was wrong: **it already
  exists.**

## What remains unresolved

1. **The collapse is not decomposed.** *"Off-surface transport is weak"* vs *"`'.'` is a poor
   carrier"* — **not distinguished** by this design. ⚠ The honest next step, and it needs a new
   preregistration.
2. Whether the exposure-clean readout failure is a property of the **representation** or of **every
   decoder tried so far** — five framings now.
3. Track B needs a non-discovery pair clearing a baseline screen, a **single-dose** estimand over
   the existing 608 rows, an ICC taken from the repo's measured **0.000–0.755** range rather than
   assumed at 0.09, and a live truncation gate.

## ⚠ Claims that must NOT be revived

* *"`id07_raw` is an exposure-clean high-mass readout"* — a 0-hop token decoder (`RAH2-C-020`), and
  RAH3 now shows it collapses **688×** off-surface.
* *"`H0` was falsified"* — `H0` **stands supported**, now off-surface too.
* *"`RBD-R-033` was refuted"* — withdrawn.
* *"Binding preservation is established"* — it is not (Llama 78→61/80; Qwen3 75→**9**/80).
* *"`RAH-R-018` shows transport is present/absent"* — **A-IV / CANNOT ANSWER, permanently.** RAH3 was
  a *new* experiment; it does not reinterpret it.
* **Any max over receiver-layer × donor-layer quoted as "transport strength"** — that is
  `selection_max`, an upper bound. `0.1932` included.
* ⚠ *"Qwen3's positive control was 1.000"* — it is **0.999999** (`RAH3-C-012`), **and the
  comparison it anchors is confounded** (`RAH3-C-013`).
* ⚠ *"Every form collapses"* — **false** (`RAH3-C-014`).

## The final table

| question | Llama | Qwen3 | held-out? | valid assay? | verdict |
|---|---|---|---|---|---|
| non-copy positive-control semantic transport | **partial** — only with candidates printed | **no** | no — gated off | **no** | **P-B** / **P-D** |
| exposure-clean high-mass multi-hop receiver exists | **no** (376× below gate) | **no** (186× below threshold) | no — gated off | n/a | **NOT ESTABLISHED** |
| semantic transport under `demo_processing_only` | NOT RUN — GATED OFF | NOT RUN — GATED OFF | NOT RUN — GATED OFF | NOT RUN — GATED OFF | NOT RUN — GATED OFF |
| semantic preservation equivalence | NOT RUN — GATED OFF | NOT RUN — GATED OFF | NOT RUN — GATED OFF | NOT RUN — GATED OFF | NOT RUN — GATED OFF |
| 38-domain behavioural bank power | 38×4 → **0.9786** rel (ICC .09); **NONE** (ICC .19) | same design | n/a | ICC **assumed, never measured** | **INADEQUATE** |
| baseline headroom qualified | **yes, 0.16447 — but the DISCOVERY pair** | no (0.0724) | n/a | truncation gate **never evaluated** | **BLOCKED** |
| behavioural confirmatory effect | NOT RUN — GATED OFF | NOT RUN — GATED OFF | NOT RUN — GATED OFF | NOT RUN — GATED OFF | NOT RUN — GATED OFF |

## The twelve corrections, and their shape

`C-001` a mutation that could not go red (recorded, not contrived) · `C-002` a shared-tree sweep ·
`C-003` **`MASS_GATE` was a dead literal** · `C-004` a no-op patch would have scored as a null ·
`C-005` the judge-noise model is **non-monotonic** against its own docstring · `C-006` **ICC has no
estimator** · `C-007` the truncation gate is **never evaluated** · `C-008` the third sweep, inside
the correction for the second · `C-009` the verifier printed `ok | MISSING` · `C-010` verifier B
patched the donor layer instead of the receiver layer · `C-011` a SIGPIPE GPU guard killing jobs
before they could report · `C-012` **`1.000` was a rounded value presented as exact.**

⚠ **Two of the twelve — `C-003` and `C-007` — are the same defect in two different files: a
threshold published in an artifact and enforced by nothing.** That is the signature worth
inheriting. ⚠ **Three more — `C-001`, `C-009`, `C-010` — are defects found *inside the mechanism
built to detect defects.*** A verifier, a mutation test, and a guard each failed in the way they
existed to prevent.
