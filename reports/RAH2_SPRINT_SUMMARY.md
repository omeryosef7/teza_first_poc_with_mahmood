# RAH2 "readout problem" phase — sprint summary

**2026-08-31 – 2026-09-01 · branch `behavioral-causality-sprint` · `4284e68c..4456ae35` (23 RAH2-authored
commits).** Full append-only log:
`external_md/RAH2_READOUT_PROBLEM_PLAN_AND_PROGRESS.md`. Handoff: `RESEARCH_HANDOFF.md` §
*ADDENDUM — RAH2*.

**The §2.1 table is re-derived from the raw artifacts by `scripts/rah2_verify_r005.py`** (39
assertions, stdlib-only, imports nothing from the producer, 0 failures): its 16 `pos_ctrl_max`
values, its 16 verdicts, four selected-layer option masses, two held-out gate counts and
`RAH2-C-018`'s 2348× bound. ⚠ **The numbers in §2.2, §2.3, §3 and §4 are NOT covered by that
script** — it opens only `rah2pcf_*`, `rah2pc_*` and `rah2p3_*` — and were re-derived by hand from
the named artifact and field. Note §3's **0.3886** is `p_concept_mean` while the verifier's 0.3887
for the same cell is `option_mass_mean` (`RAH2-C-022`). Each assertion is
proven able to fail by mutation — `RAH2-C-023` records why the first version of that verifier could
**not** fail on 6 of its own checks. Artifacts: **16** JSON files in
`outputs/boombness/rah_preflight/` (`rah2dev_*`, `rah2fs_*`, `rah2ld_*`, `rah2p3_*`, `rah2pc_*`,
`rah2pcf_*`).

**4 preregistrations · 8 results · 32 corrections · 3 deep reviews · 16 artifacts · 0 corrections
to a value produced by a run.** ⚠ The RAH2 addendum in `RESEARCH_HANDOFF.md` reads 3 / 7 / 29 / 2 —
counts written before `RAH2-PR-004`, `RAH2-R-007`, `RAH2-R-008`, `RAH2-DR-003` and
`RAH2-C-030`…`RAH2-C-032` existed.
**These are the current ones.**

---

## 1. The question

The predecessor sprint (`reports/RAH_SPRINT_SUMMARY.md` §6) closed by handing on two open problems —
a 38-domain bank for Track B, and, for Track A:

> *"Track A needs a receiver that is both exposure-clean and high-mass on held-out material. No such
> readout exists in this project's inventory at either the behavioural or the activation level."*

RAH2 attacked it with two new receiver framings, and — mid-phase — believed it had solved it.

---

## 2. What was found

⚠ **Scope of everything in this section**, and it is narrow: **1 of the 3 registered development
banks** (`carrot↔bomb`) and **1 of the 2 registered held-out pairs** (`lantern↔poison`);
`basket↔bomb` and `ticket↔knife` were **never probed by RAH2** (the predecessor's `sA_*` runs did probe them); `candle↔missile` was **never probed at all** (`RAH2-C-009`). 8 donors per
cell, all carrying one concept. Masses are **means over donors, not the registered medians**
(`RAH2-C-008`). *"Both models"* means both models, **not** both banks.

### 2.1 Two readout framings are ruled out — they cannot report a concept that is *present*

Under a `direct_harmful` donor — the concept **literally on the donor's surface token** — with the
0.1 positive-control gate. Source: `rah2pc_{p,q}_cb`, `rah2pcf_{p,q}_cb`, field `pos_ctrl_max`:

| form | names candidates? | Llama | Qwen3 | passes 0.1 gate |
|---|---|---|---|---|
| `fc_probe_last` | **yes** (all 4) | 0.9087 | 0.999999 | yes — but exposure-confounded by construction |
| `id07_raw` | no | 0.8409 | 0.8404 | yes — **but see §2.2** |
| `id07_tmpl` | no | 0.5011 | 0.0142 | Llama only |
| **`fewshot_syn`** | no | **0.0196** | **0.0965** | **no** |
| **`fewshot_cat`** | no | **0.0657** | **0.0087** | **no** |
| **`cat_cue`** | no | **0.00910** | **0.0353** | **no** |
| **`synonym`** | no | **0.00131** | **1.48e-08** | **no** |
| **`defn_oneword`** | no | **3.52e-05** | **2.57e-08** | **no** |

**`H1` (semantic constraint) and `H2` (in-context mapping) are FALSIFIED as readout claims on both
models** — `H1` on the selected-layer estimator and excluding the 0-hop echo readouts
(`RAH2-C-028`); `H2` with the template axis controlled **by inference, not by a matched semantic
control** (`fewshot_*` are `templated: False` against `templated: True` references), the basis on
which `RAH2-C-013` downgraded `RAH2-R-002` to **CONFOUNDED — CANNOT ATTRIBUTE**. The peak across all five candidate forms is **0.0965**, below the gate. These framings are
unreportable **per se** — not unreportable-for-doublespeak.

The copy confound of §2.2 does **not** reach them: they read at **non-zero hops** (few-shot 2;
semantic 9–17) and must compute a *function of* the patched token. That is why `H1`/`H2` survive the
retraction below while the phase's positive result does not.

⚠ `pos_ctrl_max` is a **maximum over ~31–39 donor layers × 5 receiver depths**, selection-inflated
with no multiplicity correction. It makes a negative *stronger* and a positive *weaker*. The
`direct_harmful` control was **never run on the held-out pair** for these form sets.

### 2.2 The phase's positive result was RETRACTED — `id07_raw` is a token decoder

`RAH2-R-005` reported `id07_raw` as *"the first readout in this project that is both exposure-clean
and high-mass"* (0.84 on both models, naming no candidate), declared `H0` falsified, and propagated
that into two published deliverables. **An auditor asked to refute it did so, and the refutation was
confirmed against the artifacts** (`RAH2-C-020`).

`id07_raw` is `ID_PROMPT = "hello hello\nworld world\ncat cat\nX"` with `patch_at="last"`,
`read_at="patch"` — **0 hops**: the donor vector is written into the residual at the final position
and the logits are read **at that same position**. In the positive control the donor is captured at
the concept's own surface token, so **transport and copying are confounded by construction**.

The discriminating evidence was already in the phase's own artifacts. Under a `natural_doublespeak`
donor the captured surface is the **codeword**. Source: `rah2p3_*`, field
`per_layer[].p_codeword_mean`, **max over (R, L)** — the peaks sit at early donor layers (R=4/L=0,
R=8/L=4, R=5/L=4, R=5/L=6). The row-level `p_codeword_at_best` maxes 3–5 orders lower:

| run | injected token | **P(codeword)** |
|---|---|---|
| Llama dev | ` carrot` | **0.899** |
| Llama held-out | ` lantern` | **0.750** |
| Qwen3 dev | ` carrot` | **0.780** |
| Qwen3 held-out | ` lantern` | **0.941** |

> **Inject `bomb` → get `bomb` at 0.84. Inject `carrot` → get `carrot` at 0.90.** The output is a
> deterministic function of *which token was injected*, at the **same order** as its own "positive
> control" — above it in 2 of 4 runs (Llama dev 0.899, Qwen3 held-out 0.941 vs controls 0.8409 /
> 0.8404) and just below in the other 2 (Llama held-out 0.750, Qwen3 dev 0.780).

**Consequences:** `H0` is **CONFIRMED, not falsified** — `H0` states that mass requires *printing the
candidates or echoing the patched token*, and `id07_raw` is the second disjunct, so a confirming
instance had been filed as a refutation. `RBD-R-033` **stands**. Both deliverable edits were
**retracted in place**.

### 2.3 A development screen has no predictive validity for held-out material

Max over (R, L), development `carrot↔bomb` → held-out `lantern↔poison`. Source: `rah2dev_*_cb` →
`rah2ld_*_lp`, field `per_layer[].option_mass_mean`:

| form | Llama | Qwen3 |
|---|---|---|
| `cat_cue` | 0.00198 → 0.0389 (**×19.7 UP**) | 0.00205 → 0.0243 (**×11.8 UP**) |
| `synonym` | 0.00301 → 0.00122 (×0.40) | 1.38e-11 → 4.78e-09 (**×347 UP**) |
| `defn_oneword` | 9.76e-05 → 8.21e-04 (**×8.4 UP**) | 1.42e-06 → 7.78e-07 (×0.55) |
| `id07_tmpl` | 0.980 → 0.990 (×1.01) | 0.4344 → 2.93e-04 (**×0.00067**) |

**Five of the eight candidate-free cells went UP; the spread is ×0.00067 to ×347.**
(`fc_probe_last` is excluded throughout as exposure-confounded; it ran in both sweeps and is the
most stable pair in them, ×1.05 and ×1.00 — which does not rescue predictive validity.) The single precedent this project
had generalised from (`id07_tmpl` on Qwen3) is the **most extreme collapse in the table** — the
exception, not the rule. A registered early-stop that skips held-out on a hopeless-looking
development screen would have been a **mistake**.

⚠ What this buys is the **unpredictability** finding, **not mass**: in that held-out run
`id07_tmpl`'s 0.990 is 0.9904 `p_codeword` against `p_concept` 1.3e-09, and `cat_cue`'s 0.0389
carries `p_concept` 1.1e-06.

---

## 3. What was NOT concluded

* **Not** that the readout problem is solved. It is **not**: `RBD-R-033` and the RAH summary's open
  problem both **stand**.
* **Not** that the doublespeak mapping is absent. Every `H1`/`H2` verdict is about the **readout
  form**, not the mapping; as a claim about the mapping the result is **CANNOT ANSWER**.
* **Not** that the trade-off is escapable. `H0` is confirmed.
* One observation is registered as an **observation only**: on **Qwen3 development**, at donor layer
  **L=34**, the *codeword* representation decodes to the **concept** — P(concept) **0.3886**,
  P(codeword) **7.46e-07** (`rah2p3_q_cb`, `id07_raw`, R=30). It collapses to **2.38e-04** held-out
  (`rah2p3_q_lp`, R=36, same field). One model, one bank, development, 8 donors, **no interval, no
  test.** Any work on it **requires its own preregistration**.

---

## 4. Integrity record

| | |
|---|---|
| preregistrations | **4**; `RAH2-PR-004` registered and **never executed** — superseded by a concurrent session's RAH3, recorded at `RAH2-C-031` so no promise dangles |
| corrections | **32** (`RAH2-C-001`…`C-032`) |
| deep reviews | **3**, using read-only auditors |
| guard tests | `tests/test_rah_preflight_spans.py` 7 → **11**, every new one RED-checked by mutation |
| ASR filtering | **none**, at any point |
| **corrections that changed a value produced by a run** | **0** |

**Defects this phase found in its own work:**

* **`RAH2-C-020`** — the retraction above. The phase's headline result was an artifact of its own
  test, and it had reached two published deliverables **within one tick**.
* **`RAH2-C-023`** — the verifier built to catch such things **could not fail on 6 of its own
  assertions** (absolute tolerance against values orders of magnitude smaller; the headline held-out
  figure passed when mutated 2.2× wrong, another passed 33 784× wrong). Its "proven able to fail"
  test had mutated the value with the **most headroom in the file**.
* **`RAH2-C-021`** — *"never given a positive control"* was false: **eight artifacts dated
  2026-08-30** (`sA_*`, `rahpf_*`) already contained it — `id07_raw`'s `pos_ctrl_max` maxed over R
  runs **0.602–0.922** across the eight. The same failure as `RAH-C-002` a phase earlier.
* **`RAH2-C-003` → `C-017` → `C-018` → `C-020`** — a correction, its inversion, its withdrawal, and
  its reinstatement. **Each was written with full confidence**, and each rested on a control not yet
  run — or, at the end, on one run eight times and not read.
* **`RAH2-C-015`** — the exemplar anti-priming check was **dead code**, never called, while the log
  reported its result as a verification.
* **`RAH2-C-032`** — commit `7906faae`, whose message describes a provenance audit and ends *"PR-004
  unaffected"*, carries **226 lines of a concurrent session's implementation** (32 of the 258 lines
  it added to `src/boombness/rah_preflight_transport.py` are this phase's; the commit adds 384 across
  three files). `git add -- <path>` snapshots worktree **content**, scoped by path, not by
  author — so explicit paths give no protection when two writers edit the **same file**.

> **The recurring signature, and it held to the last entry: the numbers kept being right and the
> sentences around them kept being wrong.** Thirty-two corrections, **none** of which changed a
> measured value. The load-bearing practice was asking an auditor to **refute** rather than check —
> `RAH2-DR-002` took the phase's headline result down in one pass.

---

## 5. Reusable output

* `src/boombness/rah_preflight_transport.py` — `readout_ladder_forms()` and
  `fewshot_receiver_forms()` added **outside** the frozen Stage-A grid (`receiver_forms()` is still
  exactly 4 forms); `exemplar_candidate_collisions()` anti-priming check, now **called, refusing on
  collision **on `--form-set fewshot`** (other form sets write an unchecked `[]`), and persisted to
  the **8** artifacts written after `RAH2-C-015` — the 8 earlier `rah2dev_*` / `rah2fs_*` /
  `rah2ld_*`, including §2.3's source, predate it and do not carry the key; `provenance()` emitting
  `git_commit` / `git_dirty` (**tri-state** — a tree that cannot be read is not a clean tree) /
  `slurm_job_id` / `argv` / timestamps, sampled **before** the sweep so it attests the code that ran.
  ⚠ It landed at `080ce1cd`, **after this phase's last sweep**, so **none of RAH2's 16 artifacts
  carries the block** — it helps the next phase, not this one.
* `scripts/rah2_verify_r005.py` — 39 assertions, **relative** tolerance, verdicts checked against a
  transcription of the *published* column rather than the code's own rule.
* `tests/test_rah_preflight_spans.py` — 11 guards; the **4 added this phase** are each proven able
  to fail by mutation (the other 7 predate RAH2, from `6b280642`).

## 6. The exact next step

A usable readout must satisfy **four** constraints; RAH2 established that the fourth is not optional:

1. **exposure-clean** — `names_any_candidate() == []`;
2. **high-mass on held-out material** — still unmet by everything tested;
3. **non-zero hops** — it must compute a *function of* the patched representation, or it is a token
   decoder (`RAH2-C-020`). **This eliminates `id07_raw` and `id07_tmpl`**, the only two forms that
   ever cleared the **0.1 positive-control gate** (`POSITIVE_CONTROL_THRESH` — *not* the 0.05
   `MASS_GATE`, which this phase never applied: `mass_gate_ok` appears in **0 of 380** RAH2 grid
   records, `RAH2-C-027`) without printing candidates;
4. **validated on a positive control that is NOT a copy test** — a donor captured where the concept
   is **not** the surface token. All **12 pre-RAH3** `direct_harmful` artifacts in this directory
   (`rah2pc_*`, `rah2pcf_*`, `rahpf_*`, `sA_*`) were produced by the default surface-capture path,
   which is why `RAH2-C-020` was possible at all. ⚠ The directory now holds **15**: the three
   `rah3nc_*` / `rah3smoke_*` files are RAH3's non-copy control (`capture_mode: "offset"`,
   `capture_offset: 1`, `overlaps_concept_surface: false`) — i.e. constraint 4, already executed.

**Constraints 1 + 3 are in tension with 2 across all five framings tried** (forced choice, echo
templated, echo raw, semantic ×3, in-context mapping ×2) — which is why `H0` keeps being confirmed.

The capture-site test for constraint 4 was registered here as `RAH2-PR-004` and **executed by the
concurrent RAH3 session**, which inherited it by name — including the branch in which
`RAH2-C-020`'s retraction would itself be wrong (`RAH2-C-031` follow-up). **Cite RAH3's result, not
`RAH2-PR-004`.**
