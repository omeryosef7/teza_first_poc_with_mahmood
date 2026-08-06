# P4b — Pre-registration (plan P4b-0.2 / 0.3)

**Written before any P4b GPU result is interpreted.** This fixes the multiple-comparison structure and the
decision rules *in advance*, so that a result cannot be rescued or killed by choosing the correction after
seeing it.

---

## 1. The multiple-comparison structure — the decision that matters most

**One Holm family per (channel × position-set), never one family across everything.**

The temptation is to Holm-correct all 12 800 (channel, layer, head, position-set) cells as a single
family. That would be wrong, and quantitatively fatal: the largest per-head necessity effect ever observed
in this project is **0.0325** (`logs/ds_headz_704131.out:8`). Holm over a 12 800-cell family sets the most
significant cell's threshold at α/12 800 ≈ 3.9 × 10⁻⁶; a real effect of size 0.03 at n = 44 cannot clear
that, so a single mega-family **guarantees a null regardless of the truth**. A test rigged to return null
is not a test.

The scientifically meaningful family is **"which heads carry channel C's effect at position-set P"** — a
32 × 32 = 1 024-cell family, corrected independently for each (C, P). This matches what
`scripts/phase5_analyze.py` already does (Holm over the 1 024-cell head grid).

| dimension | levels |
|---|---|
| channel C | z, Q, K/V (group-level), attention-pattern — **4** |
| position-set P | answer, demo, query, all — **4** (K/V and pattern use a reduced set, see §3) |
| within each (C, P) family | 32 layers × 32 heads = **1 024 cells** |

**Families are declared here and are not merged post hoc.** Reporting will state, per (C, P): the number of
Holm-significant heads, the argmax head, and its effect with CI. A head "survives P4b" only if it is Holm-
significant **in the same (C, P) cell on both dev and heldout** (the split is the replication gate, §4).

## 2. The estimand and its sign

> **⚠️ CORRECTED 2026-08-06, before any P4b-1 result was interpreted.** The first version of this section
> defined the estimand as a per-cell *difference* against a random-donor arm
> (`… − mean_i[same with a RANDOM donor]`). **That is not the established Phase-5 estimand, the analyzer
> does not compute it, and — decisively — the run does not emit a per-(l,h) random arm to subtract**
> (`normrand` is measured at a single probe head, as a sanity control, not per cell). I wrote a control
> the data cannot support. The corrected estimand below matches `PHASE5_HEADS.md` and
> `scripts/phase5_analyze.py:5,88` exactly. This changes no conclusion — it removes a phantom subtraction
> that was never computed — and the direction favours no outcome. The running demo-position jobs
> (728710/728711) emit precisely what the corrected estimand needs, so they are **not** affected.

Per cell, the reported quantity is **paired necessity**:

```
necessity(l,h,P) = mean_i [ p_concept(DS)                              # C1, the intact DS readout
                            − p_concept(DS with head (l,h)'s z at P ← BENIGN donor) ]
```

over the **valid** items (those where DS reads the concept above the benign floor,
`C1 > benign_p_concept`), tested with **Wilcoxon signed-rank** (robust to the right-skew of the diffs) and
**Holm-corrected across the 1 024-cell family, per split**.

A **positive** value means: replacing this head's output at position-set P with the **benign counterpart's
own z at the matched position** *reduces* the concept readout — i.e. the head is **necessary** for the
concept being read at those positions. The benign donor is **occurrence-order trailing-aligned** (DS and
benign codeword-occurrence counts differ; align from the last occurrence backward, use the last *k* of
each). **The benign donor IS the controlled counterfactual** — it is the same prompt with the concept
removed — which is what makes this a specificity measurement without a per-cell random subtraction.

**Controls (emitted, not subtracted per cell):**
- **self-swap** — DS's own z at the patched positions; must be **exactly 0.0** (locality; a non-zero value
  voids the run). This is the primary specificity guarantee.
- **norm-matched random donor** at one probe head — shows a same-norm *random* vector is not equivalent to
  the benign donor. Probe-level sanity, not a per-cell baseline.

**Honest limitation of this estimand (stated in advance).** A *per-(l,h)* norm-matched random arm — asking
whether a random vector of matched norm at **each** head reduces `p_concept` as much as that head's benign
donor — would be a strictly stronger specificity control. This run does **not** emit it (it would double
the 1 024-cell sweep). It is a defensible upgrade for a follow-up; the self-swap = 0 locality control plus
the matched-counterfactual benign donor is the same control structure every prior Phase-5 result used.

## 3. Position-set coverage per channel (the corrections the max-scope audit made)

- **z channel** — all four position-sets {answer, demo, query, all}. `answer` reproduces the historical
  TOTAL-effect run byte-for-byte; demo/query/all are the new P4b-1 cells at the positions the retrieval
  heads act.
- **Q channel** — same four (P4b-2).
- **K/V channel** — **group-level, at source positions only** (P4b-3). Per-head K/V patching is *ill-posed
  under GQA*: Llama-3.1-8B shares K/V across query-head groups (`num_key_value_heads` = 8 vs
  `num_attention_heads` = 32), so "head h's K" is not a well-defined object. The correct object is the
  key_value_head group, and the correct destination is the source positions. This is the repair for the
  §0.9 retraction, not a per-head map.
- **attention-pattern channel** — eager, 3 query-position sets (P4b-4); the expensive one.

## 4. The replication gate (pre-registered decision rule)

- **dev is exploratory, heldout is confirmatory.** A head is a **P4b candidate** iff Holm-significant in
  its (C, P) family on **dev**. A candidate is **confirmed** iff it is also Holm-significant in the *same*
  (C, P) cell on **heldout**.
- The **headline claim** for each channel is the set of confirmed heads. Dev-only survivors are reported as
  suggestive and explicitly labelled non-confirmed.
- **No result is interpreted without its firing check.** Every cell must pass the activation-delta
  assertion (`tests/test_hook_firing_synthetic.py`): a null from a cell whose hook did not fire is void,
  not negative. This is the standing retraction rule (`phase5b_qkv.py:38-43`).

## 5. Controls that must hold (pre-registered; a run failing any is discarded, not reported)

| control | expected | why |
|---|---|---|
| **self-swap** (DS's own z at the patched positions) | **exactly 0.0** | proves locality — the patch changes nothing when the donor equals the target |
| **norm-matched random donor** (probe head only) | different from the benign-donor effect | shows a same-norm random vector is not equivalent to the matched benign counterfactual (probe-level sanity, **not** subtracted per cell — see §2) |
| **zero-donor firing control** (on the probe grid) | non-zero delta | proves the hook fired (§4) |

A self-swap that is **not** exactly 0.0 means the patch machinery is broken and the whole run is void.

## 6. What is fixed and cannot change after seeing results

1. Family structure = one Holm family per (channel × position-set) of 1 024 cells (§1).
2. Estimand = paired necessity `mean_i[C1 − benign-patched]`, Wilcoxon/Holm per split, sign as in §2 (no per-cell random subtraction — that was a corrected error).
3. Confirmation = Holm-significant on **both** dev and heldout in the same cell (§4).
4. K/V is group-level at source positions; per-head K/V is not reported (§3).
5. Every reported cell passed its firing check (§4).

*Deviations from this document, if any prove necessary, will be recorded in `CONTINUATION_PROGRESS.md`
with the reason, before the affected numbers are quoted — never silently.*
