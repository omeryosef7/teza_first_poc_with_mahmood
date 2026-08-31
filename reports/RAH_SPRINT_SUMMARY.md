# Representation Access & Headroom (RAH) — sprint summary

**2026-08-30 → 2026-08-31 · branch `behavioral-causality-sprint` · `fe8fd610..35d4737e`**

Every number here is re-read from its raw artifact by `reports/RAH_REPRO_MANIFEST.json`, which was
**executed on a clean tree**: 17 numbers, **2 independent verifiers + 3 replay checks**, 0 failures. The main table
(`reports/RAH_MAIN_TABLE.md`) is **generated** from artifacts, not typed.

---

## 1. The question

The predecessor sprint (`reports/RBD_SPRINT_SUMMARY.md`) tested whether an attention knockout
(`demo_processing_only`) removes a "doublespeak" jailbreak **while leaving the installed
codeword→concept mapping intact**. On held-out material the dissociation **did not replicate**:
binding fell 78→61 on Llama and **75→9 on Qwen3**. Its behavioural half was **declined** for
insufficient headroom.

It left one question and named the route to it:

> When forced-choice binding collapses, was the representation **destroyed**, or is it still present
> and merely **unreportable**? No behavioural readout can settle this. **Go activation-level.**

This sprint built that instrument and ran it to a held-out conclusion. It also asked whether the
behavioural half could be rescued on a properly powered population.

**Both tracks returned negative or non-answerable outcomes — by rules registered in advance.**

---

## 2. What was found

### 2.1 The mapping is installed and is not used *(the strongest positive result)*

Measured on the **same** families, readout, options and implementation, comparing the doublespeak
condition against the **no-mapping** control:

| | binding lift | mapping-use lift |
|---|---|---|
| Qwen3 × `lantern↔poison` | **+0.9375** [+0.8491, +0.9730] | −0.0375 [−0.1421, +0.0666] |
| Qwen3 × `candle↔missile` | **+0.5000** [+0.3836, +0.6070] | +0.0250 [−0.0243, +0.0866] |
| Llama × `lantern↔poison` | **+0.9750** [+0.8982, +0.9931] | −0.1000 [−0.2318, +0.0371] |
| Llama × `candle↔missile` | **+0.6500** [+0.5316, +0.7455] | +0.0375 [−0.0145, +0.1045] |

**Binding lift ESTABLISHED on 4/4 cells; mapping-use lift NOT ESTABLISHED on 4/4.** n = 80 families,
20 domains per cell, paired, domain-cluster bootstrapped, independently re-derived.

This is not a power failure: on `candle↔missile` the readout has a **76-row dynamic range** and the
doublespeak arm sits at **2.6 % / 3.9 %** of it; on `lantern↔poison` the arm sits **at or below its
own no-mapping floor**.

**It also closed an open question from the predecessor sprint.** Qwen3's headline "69/80 mapping use"
was never controlled. Its no-mapping base rate is **72/80 — higher**. So the large Llama-vs-Qwen3
difference (24/80 vs 69/80) is a difference in the models' **base rates for the option words**
(0.40 vs 0.90), not in how much they use an installed mapping.

### 2.2 The 80-row design cannot detect a behavioural effect of any size

Power analysis reusing the repository's own paired-McNemar-with-judge-noise simulator, with domain
clustering and a **measured** judge flip rate. `n/a` = *even reducing ASR to zero does not reach 80 %
power*:

| design | baseline 0.0875 | 0.1375 | 0.20 |
|---|---|---|---|
| k=20 × m=4 (**n=80**, the design used throughout this project) | **n/a** | **n/a** | **n/a** |
| k=20 × m=8 (n=160) | n/a | n/a | MDE 0.95 relative |
| k=38 × m=16 (n=608) | 0.91 rel | **0.70 rel** | **0.61 rel** |

> **This is a retrospective explanation of why the behavioural half kept failing**, and it is
> *independent* of the headroom gate that formally declined it: at n=160 and baseline 0.15 the MDE is
> still `n/a`, so meeting the old floor of 14 attacks would not have rescued it.

Two consequences: **domains, not rows, are the binding lever**; and a higher-headroom population does
**not** buy proportional power, because the measured judge flip rate **rises with ASR** (0.021 at
ASR 0.013 → 0.085 at ASR 0.27).

### 2.3 Patchscope in this repository failed for a fixable reason

**Seven** recorded positive-control failures had led to the method being dropped
(*"unusable as configured — late-layer read, no positive control"*). **Only the one archived `46`
configuration was re-run here**; the receiver injection layer explains **that one**, and the other
six are *consistent with*, not demonstrated by, this result.

On **Llama**, moving injection from R=28 to R=4 of 32 takes the archived configuration from
**0.0088 → 0.2771 (31×)** and the best form from **0.0065 → 0.8421 (130×)** — same model, same
receiver form, same readout. ⚠ **Each endpoint is a maximum over 31 donor layers and the argmax
donor layer differs** (L=19→2 and L=21→3), so these are **not** same-donor comparisons. Held at a
**fixed** donor layer the ratio is **16.5×–321.8×** across the four (form, L) combinations.

⚠ **The R-profile is LLAMA'S, and it does not hold on Qwen3.** On Llama every passing form dies at
R ≥ 16 and `id07_tmpl` fails at all five R. On Qwen3 `fc_probe_last` clears the gate at **all five
depths including R = 36 = `n_layers − 4`** — the very depth blamed for the archived failures — and
`id07_tmpl` clears it only at R = 20. So *"an early injection layer is necessary"* is **false on
Qwen3**. The selected depth fraction is 0.125 on both models, but both `R_set`s were laid out at
**identical depth fractions by construction** and the selection rule tie-breaks on the lowest — that
is agreement of a **selection rule**, not demonstrated transfer of a depth effect.

### 2.4 Track A — **A-IV, CANNOT ANSWER**

The assay captures internal state at the **codeword** position of an attack prompt with the
intervention **live**, and transplants it into a separate, never-intervened receiver.

Two configurations were viable and both closed:

1. the configuration selected on the **positive control** transports the **codeword**, not the mapped
   concept — its baseline transport precondition fails;
2. the configuration selected on **baseline transport** works on its selection bank (P(concept)
   0.4344) and is **unreportable on held-out material**: median option mass **7.147e-08** against a
   0.05 gate, **0 of 80 rows** above gate, on every arm.

**No Δ was computed and no equivalence test was run** — the precondition, registered before the data
existed, forbids it.

> **The methodological finding:** *validating an instrument on a positive control does not establish
> that it is the right instrument for the phenomenon.* The positive control captures where the concept
> is literally present — close to a copy test — and it selected the form that is **worst** for the
> real question.

### 2.5 Track B — **B-BLOCKED-BY-MATERIAL**, no causal arm run

| screening cell (n=152, 38 domains) | attacks | baseline ASR | qualifies |
|---|---|---|---|
| **Llama × `carrot↔bomb`** | 25 | **0.1645** | **YES** |
| Llama × `ticket↔knife` | 14 | 0.0921 | no |
| Qwen3 × `carrot↔bomb` | 11 | 0.0724 | no |
| Qwen3 × `ticket↔knife` | 5 | 0.0329 | no |

**One cell of four qualifies, and it is the discovery pair on a single model.** There is **no
qualifying cell on Qwen3 at all** — the model whose binding collapse motivated the sprint.

The blocker is **material, not the models**: the frozen requirement of ≥30 domains is met by **5 of 37
banks**, covering **two** lexical pairs, and the only non-discovery pair fails the ASR floor on both
models. **The confirmatory matrix was not run and ≈20 GPU-hours were not spent.**

---

## 3. What was NOT concluded

* **Not** that the representation does not exist. The mapping is demonstrably installed — level-A
  binding 12/12 (Llama) and 10/12 (Qwen3) at the assay's own dose; level-B 78/80 and 75/80. Both
  Track-A findings are about the **instrument**.
* **Not** that `demo_processing_only` does or does not suppress the attack. That estimand remains
  **DECLINED**, and no intervened arm was interpreted on either track.
* **Not** that the exposure/mass dilemma is general at the activation level. It was observed **once**,
  on one model and one bank.
* One striking-looking number is recorded explicitly as **NOT USED**: the held-out argmax shifts from
  `poison 36` under `base` to `poison 0` under the intervention — computed over probabilities of
  order **1e-8**, six orders below the reportability gate.

---

## 4. Integrity record

| | |
|---|---|
| preregistrations | **9 registered**, each committed **before** the data it governs. Two further ids (`RAH-PR-005` the Track-A freeze, `RAH-PR-008` the Track-B confirmatory arms) were planned in the phase map and **never reached** — their phases stopped first |
| corrections | 15 (`RAH-C-001`…`RAH-C-015`) |
| deep reviews | 3, using 15 read-only auditor agents |
| verification | **2 independent verifiers** (re-implement the statistics, import nothing from the producer) **+ 3 replay checks** (re-run the producing rule and **diff its decision** against the committed artifact). `RAH-DR-004` B4 found the replays originally discarded their output, proving only that a script had not crashed; they now diff, and the diff is **proven able to fail** |
| reproduction manifest | **executed on a clean tree**: 17 numbers, 5 verifiers, **0 failures** |
| guard tests | 294 → **309** (see below) |
| ASR filtering | **none**, at any point |

**Defects found in this sprint's own work, by its own machinery:**

* **`RAH-DR-002`** — 5 FATAL defects in code I had written, including a gate that could have returned
  **GO with zero transport** (it tested an absolute probability in a receiver that prints its options,
  so the unpatched prior already cleared the threshold). A running GPU job was cancelled mid-flight.
* **`RAH-DR-003`** — 6 published claims overstated; **0 arithmetic errors**. One correction made the
  main result *stronger* by replacing a level-B binding figure with the level-A one that actually
  applied.
* **`RAH-C-007`** — a correction that created a vacuous guard (it tested for the wrong constant, so it
  skipped **8 of 8** interval comparisons while printing PASS).
* **`RAH-R-016`** — every commit printed "294 passed" and **the number never moved**: the mutation
  tests proving my own new guards could fail had **never been in the hook's list**. Fixed, and proven
  by reverting a guard and watching it go red.
* **Three crashed smokes** (`RAH-R-011`, `RAH-C-009`, `RAH-C-013`), each a genuine defect that was
  **loud rather than silent** — because in this codebase resolvers raise and required fields are
  referenced by key, never `.get(k, default)`.

**The recurring signature, stated plainly: the numbers kept being right and the sentences around them
kept being wrong.** Every claim-level defect this sprint found in its own work was a **scope** error —
a property of one configuration written as a property of a position, a level-B number defending a
level-A null, a pooled rate quoted as a subset rate. Not one was an arithmetic error.

---

## 5. Reusable output

* `rah_preflight_transport.py` — donor×receiver×layer sweep with a three-conjunct gate (level **and**
  uplift over the unpatched prior **and** dominance). **Contains no intervention code path**, so any
  selection made with it is structurally effect-blind.
* `rah_transport_assay.py` — arm-active donor capture with per-row vacuity measurement, liveness with
  key-presence assertions, and receiver-variant deduplication on rendered text.
* `rah_power_trackb.py` — clustered power with a **measured, ASR-dependent** judge flip rate.
* `rah_verify_phase1.py`, `rah_verify_dose.py` — stdlib-only independent verifiers.
* `rah_select_config.py`, `rah_select_transport_config.py`, `rah_screen_table.py`,
  `rah_make_gatesub.py` — deterministic, unit-tested rules over committed inputs, re-runnable as
  audits; each **refuses** rather than degrades.
* **The receiver-layer finding**, which is what makes patchscope usable in this repository at all.

---

## 6. The exact next step

**Track B is blocked by a bank, not by an experiment.** The unblocking action is a **38-domain bank
on a new lexical pair with a bomb-class concept**, which needs fresh demonstration pools across 38
domains. With it, `k=38 × m=16` at baseline ≥0.1375 reaches an MDE of 0.70 relative — enough for the
73 % reduction the discovery bank showed, with little to spare.

**Track A needs a receiver that is both exposure-clean and high-mass on held-out material.** No such
readout exists in this project's inventory at either the behavioural or the activation level. That is

> ⚠ **STATUS UPDATE, 2026-08-31 (`RAH2-R-005`, as corrected by `RAH2-C-020`).** This sentence
> **STANDS, unrefuted.** An earlier note here claimed the accompanying *structural* claim had been
> falsified by `id07_raw`; that was **wrong and is retracted** — `id07_raw` decodes token identity
> (inject the codeword, get the codeword at 0.90/0.94), so it is an instance of the trade-off, not a
> counterexample. What the RAH2 phase adds is narrower: the semantic-constraint and in-context-mapping
> framings **cannot report a concept that is literally present** (peak 0.0965 against a 0.1 control),
> so they are ruled out as candidate readouts — the search space is reduced, not solved.
the open problem this sprint hands on, and it is now a *characterised* one rather than a suspicion.
