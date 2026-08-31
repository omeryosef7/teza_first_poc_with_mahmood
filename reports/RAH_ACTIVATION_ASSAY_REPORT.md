# The activation-level donor→receiver assay — construction, controls, and why it returned CANNOT ANSWER

**RAH sprint deliverable 4 (§12.4).** Every number here is protected by
`reports/RAH_REPRO_MANIFEST.json`, which re-reads it from its raw artifact and fails if it has moved.

---

## 1. Why this instrument was built

The predecessor sprint closed `RBD-R-033` on a structural claim about **behavioural** readouts:

> A readout that names its options is high-mass and **exposure-confounded**; one that does not is
> exposure-clean and **unreportable**. No readout in this project's inventory is both.

> ⚠ **THIS CLAIM STANDS. A correction posted here on 2026-08-31 was itself WRONG and is RETRACTED**
> (`RAH2-C-020`, see `external_md/RAH2_READOUT_PROBLEM_PLAN_AND_PROGRESS.md`).
>
> I briefly recorded this claim as falsified by `id07_raw`, which reads 0.84 under a positive control
> while naming no option. **That was an artifact of my own test.** `id07_raw` is a 0-hop read at the
> patched position on a repetition prompt, so it decodes the **token identity** of whatever was
> injected. Injecting the *codeword* representation yields the **codeword** at **0.90 (Llama) / 0.94
> (Qwen3)** — at or above the "positive control" value. It is a token decoder, not a concept readout,
> and it is a **confirming instance** of the trade-off above (the "echo the patched token" disjunct),
> not a counterexample. No part of `RBD-R-033` is refuted.

Its recommendation was to go **activation-level**: measure the internal state directly, so the
options can live in a *different prompt* from the one whose state is measured and therefore cannot
have created it. This report documents building that instrument and running it to a held-out
conclusion.

---

## 2. Construction

```
DONOR      a bank row, hooks LIVE, NO answer options anywhere
             |  capture resid_post at (donor block L, a chosen token position)
             v
RECEIVER   a separate prompt, ALWAYS unintervened
             |  LayerPatch(replace) at (receiver layer R, a chosen slot)
             v
           read option first-token probabilities at the read position
```

| component | choice | source |
|---|---|---|
| capture | `donor_patch.ActivationCapture` on the decoder block → `resid_post` | reused |
| patch | `ds_common.LayerPatch(mode="replace")` | reused |
| arm-active capture | the `score_behavior.py:1892-1928` pattern — the **only** place in the repository where a capture forward runs under live intervention hooks | reused |
| interventions | `score_behavior.make_intervention`, `KNOCKOUT_ARMS` key sets | reused |
| receiver + span resolution | `rah_preflight_transport` (imported, not copied) | new |

**Layer convention, pinned once:** donor block index `L` means `hidden_states[L+1]`, which is the
coordinate `LayerPatch(layer_idx=L)` writes. `L` is capped at `n_layers − 2` because
`hidden_states[n_layers]` is the **post-final-norm** state — a different coordinate.

---

## 3. The four receiver forms, and the one thing that separates them

| form | names its options? | patch site | read site | hops |
|---|---|---|---|---|
| `id07_raw` | no | last token | same position | **0** |
| `id07_tmpl` | no | last token | same position | **0** |
| `fc_probe_last` | **yes** (4-way) | probe token | after `Answer:` | 8–12 |
| `fc46` | **yes** (4-way) | probe token | final | 46–52 |

---

## 4. The finding that made the instrument work at all

`46_forced_choice_patchscope.py` had been run **once** in this repository and its positive control
failed by ~712× (`pos_ctrl_max` 1.404e-04 against a 0.1 gate), flat across all 33 donor layers. **Six
further recorded failures existed** on other model families; **none of those six was re-run here.**
The method had been dropped.

**For the one configuration that was re-run, the cause was the receiver injection layer, not the
concept.** P(concept), best over donor layers, **Llama** — ⚠ each cell is a **maximum over 31 donor
layers** and the argmax layer differs between cells, so column-to-column ratios are **not**
same-donor comparisons:

| form | R=4 | R=8 | R=16 | R=24 | R=28 |
|---|---|---|---|---|---|
| `fc_probe_last` | **0.8421** | 0.6999 | 0.0168 | 0.0201 | 0.0065 |
| `fc46` | 0.2771 | 0.0877 | 0.0133 | 0.0117 | **0.0088** |

`fc46 @ R=28` is exactly `46`'s default (`n_layers − 4`) and reproduces the archived failure.
**Moving the injection from R=28 to R=4 takes `fc46` from 0.0088 to 0.2771 (31×) and
`fc_probe_last` from 0.0065 to 0.8421 (130×)** on the same model and readout.

⚠ **On Llama** an early injection layer is necessary but not sufficient: `id07_tmpl` fails at
*every* R. Held at a **fixed** donor layer the R=28→R=4 ratio is **16.5×–321.8×**.

⚠ **This profile is LLAMA'S and is falsified on Qwen3.** There `fc_probe_last` clears the gate at all
five depths **including R = 36 = `n_layers − 4`**, the depth blamed for the archived failures, and
`id07_tmpl` clears it only at R = 20. **No R-profile statement here may be quoted as model-general.**

⚠ **Only the `46` configuration was re-run here.** The other six are *consistent with* this
explanation, not demonstrated by it.

---

## 5. Controls, and which of them were informative

| control | construction | verdict |
|---|---|---|
| positive control | donor from `direct_harmful`, where the concept is **literally present** | Qwen3 `fc_probe_last @ R=5`: P(concept) **0.99999991**, P(codeword) **3.4e-12**, unpatched prior 0.0223 |
| vacuity | `‖v_dpo − v_base‖` per row | **0/80 bit-identical**, median relative delta **0.4073**, cos **0.9144** — the arms genuinely differ at the capture layer |
| liveness | knockout counters, key **presence** asserted before value | `n_prefill_edits` 86 625, `n_decode_edits` **0**, `n_keys_masked` 1 375 — prefill-only scope honoured |
| `exch` (derangement) | another family's base donor | ⚠ **UNINFORMATIVE BY CONSTRUCTION.** It is a *permutation* of `base`, so `sorted(base) == sorted(exch)` is **True** and it cannot differ on any aggregate. A paired per-family control only |
| `mean` | arm-mean donor | near-inert; every donor encodes the same surface word |
| `perm`, `rand` | direction destroyed, norm matched | **the informative floor** — base sits *below* them |
| key control | same band, same scope, count-matched | ⚠ **strict matching is INFEASIBLE** on this population: the demo block (125 keys) exceeds the entire protected complement (30). The capped policy masks **261/1125 = 23.2 %** of the dose and is **not** dose-matched |

**Two dose-matched controls are unavailable to this assay for two independent reasons**: a late band
is *vacuous* at a fixed mid-depth capture site (the arms cannot differ), and a count-matched key set
is *infeasible* on this stimulus geometry.

---

## 6. Positive control ≠ the right instrument

Stage A selected `fc_probe_last` at depth 0.125 by maximising the **minimum** uplift across six
level-A runs (0.8516) — a deliberately anti-fishing rule, over a committed grid, by a unit-tested
deterministic function.

**It selected the worst of the four forms for the actual question.** On a donor captured at the
**codeword** token of a `natural_doublespeak` prompt:

| form | Llama best | Qwen3 best |
|---|---|---|
| `fc_probe_last` (selected) | 0.0223 | 0.0933 |
| `fc46` | **0.2337** | 0.0000 |
| `id07_tmpl` | 0.0408 | **0.4344** |

> **Validating an instrument on a positive control does not establish that it is the right instrument
> for the phenomenon.** The positive control captures where the concept is *literally present*; that
> is close to a copy test, and it rewards a receiver that transports surface identity.

An untested hypothesis, recorded and **not** investigated: the option-naming receivers print the
codeword as one of their four labels, so a donor carrying that surface token can win by lexical
match; a receiver that names nothing cannot be won that way.

---

## 7. The held-out result: CANNOT ANSWER

Configuration `id07_tmpl`, R=30, donor L=34 — selected on level-A `carrot↔bomb` by a rule committed
before it was applied, with `L > lo` enforced. Run on **held-out** `lantern↔poison`, Qwen3, **80/80
families, 560 rows, `problems: 0`**, vacuity clean.

| arm | median option mass | rows ≥ 0.05 gate |
|---|---|---|
| `base` | **7.147e-08** | **0 / 80** |
| every other arm | 5.1e-08 – 3.6e-07 | 0 / 80 |

**Six orders of magnitude below the gate, on every arm.** The same configuration reached 0.4344 on
the selection bank. **It does not transfer.**

⚠ **A number recorded as NOT USED.** The argmax over the four options shifts sharply between arms —
`base` gives poison 36 / candle 26 / lantern 18, `dpo` gives lantern 61 / candle 19 with **poison 0**.
That looks like a large clean effect and is computed over probabilities of order **1e-8**. Quoting it
would be the below-gate reporting `RBD-C-019` was raised for. No Δ was computed; no equivalence test
was run.

---

## 8. What this establishes

**The exposure/option-mass dilemma reappeared at the activation level, on the populations tested
here.** Scoped exactly:

| receiver | names options | population tested | outcome |
|---|---|---|---|
| `fc_probe_last` | yes | 2 models × 3 level-A banks + 2 level-B banks | exposure-confounded — transports the **codeword**, not the mapped concept |
| `id07_tmpl` | no | selected on level-A `carrot↔bomb`; held out on **Qwen3 × `lantern↔poison` only** | exposure-clean — transports the concept on the selection bank, **unreportable** on held-out material |

⚠ **The held-out failure is ONE model on ONE bank, n = 80 families.** It is a single held-out test,
not a demonstration that the dilemma is general. The defensible statement is:

> *On the one held-out test this sprint ran, the exposure-clean receiver was unreportable and the
> option-naming receiver was exposure-confounded — the same trade-off `RBD-R-033` identified for
> behavioural readouts, now observed once at the activation level.*

Whether it **generalises** is open, and testing it would require the held-out test on further pairs
and models — a scoped follow-up, not a claim this sprint has earned. What the sprint *did* earn is
that the trade-off is **not obviously escaped** by going activation-level, which was the predecessor
sprint's stated route out.

**What is NOT established:** that the representation does not exist. The mapping is demonstrably
installed on both banks — level-A binding **12/12** (Llama) and **10/12** (Qwen3) at the assay's own
dose; level-B **78/80** and **75/80**. The finding is about the **instrument**.

---

## 9. Reusable outputs

* `src/boombness/rah_preflight_transport.py` — donor-layer × receiver-layer × form sweep with a
  three-conjunct gate (level **and** uplift over the unpatched prior **and** dominance). It has **no
  intervention code path**, so any selection made with it is structurally effect-blind.
* `src/boombness/rah_transport_assay.py` — arm-active donor capture with a per-row vacuity
  measurement, liveness with key-presence assertions, and receiver-variant deduplication on rendered
  text.
* `scripts/rah_select_config.py`, `scripts/rah_select_transport_config.py` — deterministic,
  unit-tested selection rules over committed grids, re-runnable as audits.
* **The receiver-layer finding itself**, which is what makes patchscope usable in this repository at
  all.
