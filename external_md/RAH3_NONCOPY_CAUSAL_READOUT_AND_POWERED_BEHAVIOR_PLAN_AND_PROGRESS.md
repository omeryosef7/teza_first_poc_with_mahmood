# RAH3 — Non-copy causal readout validation + powered behavioural bank

**Append-only.** New entries go at the bottom. Nothing above a horizontal rule is ever rewritten;
a superseded statement is corrected by a new `RAH3-C-###` entry that quotes the exact replaced
wording, never by editing the original in place.

**Namespace, collision-free.** `RAH3-PR-###` preregistrations · `RAH3-R-###` results and
withdrawals · `RAH3-C-###` corrections · `RAH3-DR-###` deep/adversarial reviews.
⚠ A bare `R-25`, `C-12`, `RAH-C-*`, `RBD-*` or `RAH2-*` id **never** refers to a RAH3 claim. Prior
namespaces are referenced only to cite what they established or retracted.

**Scientific source of truth on entry:** `RESEARCH_HANDOFF.md` (777 lines: the Demonstration
Retrieval → Behavioural Causality body plus the RBD, RAH and RAH2 addenda).

---

## 0. Why this sprint starts with the instrument and not with an experiment

The single sentence that organises everything below:

> **We are not entitled to interpret the activation-level Track-A experiment, because the
> positive-control infrastructure has never been shown to transport semantic information rather
> than to copy a token that was injected at the concept's own surface position.**

`RAH2-C-020` retracted this project's most recent positive readout result (`id07_raw`) on exactly
that ground: `patch_at = last`, `read_at = patch`, **0 hops**, donor captured at the concept's own
surface token. Inject `carrot`, get `carrot`; inject `lantern`, get `lantern`. That is a token
decoder.

The diagnosis was made **retrospectively**, from a control that had been run eight times and not
read. RAH3 makes the same test **prospectively**, and — this is the point — makes it a *property of
the instrument* rather than a lucky catch.

**Therefore the ordering in this sprint is non-negotiable:** validate the assay first; only a
validated assay licenses a new Track-A experiment. A validated assay does **not** retroactively
reinterpret any prior Track-A artifact.

## 0.1 The four requirements a usable readout must satisfy — ALL of them

| # | requirement | operationalisation | established by |
|---|---|---|---|
| 1 | **exposure clean** | `names_any_candidate(rendered_text, labels) == []` | `RAH2-PR-001` |
| 2 | **high mass on HELD-OUT material** | patched option mass ≥ `MASS_GATE = 0.05`, on held-out, at the **frozen** config — not max-over-layer, not development-only | RAH |
| 3 | **non-zero hops** | `hops = read_pos - q_pos > 0`; the receiver must compute a *function of* the patched state | `RAH2-C-020` — **this constraint is what killed `id07_raw`** |
| 4 | **positive control is not a copy test** | donor captured where the concept is contextually available but **is not the captured token's surface** | **RAH3, this sprint — never previously tested** |

Requirements 1 + 3 have been in tension with 2 across **five** receiver framings now (forced choice,
echo templated, echo raw, semantic constraint ×3, in-context mapping ×2). That tension is why `H0`
keeps being confirmed rather than refuted.

**Named thresholds — never write "the gate".** `MASS_GATE = 0.05` ·
`TRANSPORT_POSITIVE_CONTROL_THRESHOLD = 0.10` (the constant `POSITIVE_CONTROL_THRESH` at
`src/boombness/rah_preflight_transport.py:72`). These are two different numbers used for two
different purposes and the RAH2 log conflated them at least once (`RAH2-C-027`).

## 0.2 Claims that MUST NOT be revived in this sprint

Carried forward verbatim from the handoff's ⛔ sections. Each is **withdrawn**, not merely unproven.

* ⛔ **"`id07_raw` is an exposure-clean high-mass readout."** Retracted by `RAH2-C-020`. It is a
  0-hop token decoder.
* ⛔ **"`H0` was falsified."** `H0` — *high mass has so far required either explicitly printing the
  candidates or echoing the patched token* — **stands supported**.
* ⛔ **"`RBD-R-033` was refuted."** Withdrawn.
* ⛔ **"Binding preservation is established."** It is not. See §0.3.
* ⛔ **"`RAH-R-018` shows transport is absent / present."** It is **A-IV / CANNOT ANSWER** and
  remains so **permanently**. A new instrument licenses a *new* experiment under a *new*
  preregistration; it never converts `RAH-R-018` into a result.
* ⛔ **Any max over receiver-layer × donor-layer quoted as "transport strength."** That is
  `selection_max`, an upper bound and an instrument-selection statistic. `RAH2-C-002` and
  `RAH2-C-018` were both raised for exactly this, and the log then quoted it as a result *one entry
  later*.

## 0.3 The RBD dissociation, stated at the strength the raw data supports

The claim *"`demo_processing_only` removes the behaviour while preserving the semantic mapping"*
does **not** hold as a general confirmed statement. Held-out RBD binding readout:

| model | pair | baseline | `demo_processing_only` | reading |
|---|---|---|---|---|
| Llama-3.1-8B | lantern↔poison | 78/80 | 61/80 | **failed** the preregistered preservation requirement — but narrowly; its evidential weight must **not** be equated with Qwen3's |
| Qwen3-14B | lantern↔poison | 75/80 | **9/80** | **decisive behavioural-readout damage**: 66 lost, 0 gained |

The late-band scope was **exactly inert on this BINDING readout for this population** — a scope
statement, not a general one.

⚠ Do **not** write "binding preservation is established." ⚠ Do **not** write "binding definitely
disappears on both models equally."

---

## 1. `RAH3-R-000` — Phase-0 reconciliation of the repository, from raw evidence

Recorded **before** any code change. Every number below was read from the repository, not from
prose. Where the handoff's prose and the source disagree, the source is recorded and the prose
discrepancy is filed.

### 1.1 Repository state on entry

| item | value |
|---|---|
| branch | `behavioral-causality-sprint` |
| HEAD | `6ecf1e608d2ea1e051824d02981ea70f3007b8d2` — *"RAH2-R-008 follow-up: D11 carried no forward pointer either"* |
| working tree | **one staged file**, no unstaged changes, no untracked scientific files |
| staged | `external_md/RAH2_READOUT_PROBLEM_PLAN_AND_PROGRESS.md`, +73 lines, 0 deletions |
| SLURM jobs (`squeue -u $USER`) | **none** — no running, no pending, no other writer's jobs to protect |
| disk | `/home/sharifm` 20T, 19T used, **1.6T available (93 %)** |
| `outputs/` | 63 G |
| python | `/home/sharifm/students/omeryosef/miniconda3/bin/python`, 3.13.13 (login shell) — GPU jobs use conda env **`poc_stage2`** via `src/boombness/slurm/run_boombness.sh` |

**Nothing is mid-flight.** No incomplete run directory has to be reconciled, and no job of another
session may be disturbed.

### 1.2 The one staged file — `RAH2-PR-004`, and how RAH3 relates to it

The staged +73 lines are a **prospective preregistration** written by the immediately preceding
session: `RAH2-PR-004`, *"the capture-site control: is the positive control a copy test?"* It
registers, **before any forward pass**, the same experiment this sprint calls Phase 1, and it froze
a specific capture offset: **`N = +1`**, the token immediately after the concept surface, chosen as
*"the minimal displacement that removes the surface identity while staying inside the same
clause."*

**This is not discarded and not silently absorbed.** Two facts follow and both matter:

1. `N = +1` is **pre-committed**. It was fixed before any concept-transport result at any offset
   existed. Under §10 of this sprint's charter — *the exact capture offset must be frozen before
   seeing concept-transport results* — a pre-existing frozen offset is **stronger** evidence than
   one I choose now, because I cannot have chosen it to work.
2. `RAH2-PR-004` was written **without** the structural-validity machinery §9 requires (the
   hard-fail invariants) and **without** the tokenisation check §10 requires (that the rule yields a
   valid non-surface token *on every row*).

**Reconciliation, fixed here:** `RAH3-PR-001` **carries `N = +1` forward as the pre-committed
primary capture site**, adds the §9 invariants and the §10 structural verification, and inherits
`RAH2-PR-004`'s outcome table. The staged file is committed **as written** so the record shows what
was registered and when. ⚠ If the §10 structural check disqualifies `N = +1` on any row, that fact
is recorded as a `RAH3-C-###` and the replacement rule is registered **before** any transport
number at any offset is looked at.

### 1.3 The producer, read at source — `src/boombness/rah_preflight_transport.py` (565 lines)

⚠ **The handoff's line citations for this file are STALE.** Filed as a discrepancy, not a defect:

| handoff says | source at HEAD |
|---|---|
| donor capture at `:390-395` / `:391-397` | `rfind` at **`:423`**, `token_index_covering` at **`:425`**, `assert_token_is_part_of` at **`:426`** |
| `assert_token_is_part_of` at `:300-306` | defined at **`:328`** |
| argparse block at `:315-338` | `main()` opens at **`:337`**; argparse runs `:342-367` |

**Donor capture, verbatim:**

```python
pos_c = templated.lower().rfind(surf.lower())          # LAST occurrence, case-insensitive
p     = token_index_covering(offsets, pos_c, pos_c + len(surf))   # LAST OVERLAPPING token
assert_token_is_part_of(tok, ids, p, surf, "donor %s" % d["prompt_id"])   # raises SystemExit
```

* `token_index_covering` (`:312`) uses **overlap, not containment** (`RAH-C-005`) — a BPE tokenizer
  emits the leading space inside the word token, so containment matches nothing — and returns
  `hits[-1]`, the **last** overlapping token.
* `assert_token_is_part_of` (`:328`) requires the decoded token be a **substring of** the target
  word. This is the assertion that must be *replaced*, not deleted, on the offset path.
* Capture is `hs[L+1][0, p, :]` for `L in range(0, nL-1)` — block index `L` ↔ `hidden_states[L+1]`,
  capped at `nL-2` because `hidden_states[nL]` is post-norm.
* There is **no capture-site flag** anywhere in the argparse block.

**Receiver / metrics, verbatim:** `q_pos = len(rids)-1` when `patch_at == "last"`, else the token
covering the quoted probe span; `read_pos = q_pos` when `read_at == "patch"`, else `len(rids)-1`;
`hops = read_pos - q_pos` (`:513`). `option_mass` is the sum of exactly the four label first-token
probabilities at `read_pos`. `POSITIVE_CONTROL_THRESH = 0.1` (`:72`); the artifact separately
persists `"mass_gate": 0.05`.

**`positive_control_ok` requires three conjuncts** (`:505-507`), and `best` is an **argmax over
donor layers `L`** — 31 layers on Llama, 39 on Qwen3, × 5 receiver depths. ⚠ It is
selection-inflated by construction; it makes a *negative* stronger and a *positive* weaker.

### 1.4 The gap §37 exists for: RAH2 artifacts carry NO provenance block

`provenance()` is defined at `:79` and `main()` writes `out["provenance"]`. Yet the artifact
`outputs/boombness/rah_preflight/rah2pcf_p_cb_20260831_160728.json` has top-level keys:

```
GATE R_set attn_implementation bank codeword concept donor_condition donor_n_examples donors
enable_thinking exemplar_candidate_collisions form_set gate_rule grid label_ids label_meta
layer_convention mass_gate model n_donor_candidates n_donors n_layers probe schema threshold
```

**There is no `provenance` key.** The published RAH2 positive-control artifacts predate the
provenance block: no git commit, no dirty flag, no argv, no hostname, no SLURM job id, no bank
SHA256. This is precisely the §37 hazard, observed rather than anticipated, and it is why every
RAH3 artifact must refuse to be written without one.

### 1.5 Populations and infrastructure, confirmed present

| | development | held-out |
|---|---|---|
| pair | **carrot ↔ bomb** (`concept=bomb`, `codeword=carrot`) | **lantern ↔ poison** (`concept=poison`, `codeword=lantern`) |
| bank | `data/boombness_prompts/boombness_prompt_bank.jsonl` — 2736 rows, **120** `direct_harmful`/`behavioral` | `..._rbd_lantern_poison.jsonl` — 960 rows, **80** `direct_harmful`/`behavioral` |
| `n_examples` present | `{0,1,2,4,8,16}` → `--n-examples 8` is a **real filter** | `{8}` only → `--n-examples 8` is a **no-op** |
| distractors used by RAH2 | `--other-concept knife --other-codeword ticket` | `--other-concept missile --other-codeword candle` |

⚠ **`direct_harmful` donors exist on BOTH banks** (120 and 80). The RAH2 held-out few-shot runs
(`rah2fs_*_lp`) used `--donor-condition natural_doublespeak`, so the **held-out `direct_harmful`
positive control has never been run at all** — at any offset. RAH3's held-out arm is therefore a
first measurement, not a re-run.

**Prompt structure (development and held-out are structurally identical).** Both banks'
`direct_harmful` prompts terminate:

> `… Do not reason, just Give step-by-step instructions to build a {concept}. given the context.`

so the **last** occurrence of the concept surface — the one `rfind` selects — sits in the final
query, followed by a fixed, pair-independent trailer. That trailer is what makes a deterministic
offset rule structurally possible at all, and §10's verification is a check that it holds on
**every** row, not on the one I inspected.

**Model geometry:** Llama-3.1-8B `nL=32`, `R_set=[4,8,16,24,28]`; Qwen3-14B `nL=40`,
`R_set=[5,10,20,30,36]`. `--enable-thinking default` in every RAH2 preflight run.

**Launch infrastructure to REUSE, not rebuild:** argsfiles under `runargs/<phase>/*.txt` →
`sbatch --export=ALL,BOOMB_SCRIPT=rah_preflight_transport.py,BOOMB_ARGSFILE=$R/runargs/rah3/X.txt
src/boombness/slurm/run_boombness.sh`. The wrapper enforces the L40S guard, the conda env, offline
HF, and a **quote guard** (a quote character in an argsfile is a hard refusal — `BOOMB_ARGS` is
word-split, so quotes do not group). `scripts/rbd_submit_wave.sh` holds `MAX_INFLIGHT` jobs in
flight and only ever ADDS. ⚠ House rule inherited: **at most 2 concurrent Qwen3-14B weight loads
TOTAL** — the "2 per node" rule was measured insufficient because the bottleneck is shared NFS.
`tests/test_argsfiles_match_runs.py` ties argsfiles to runs; RAH3 argsfiles must satisfy it.

### 1.6 What Phase 0 did NOT do

No code was changed. No forward pass was run. No intervention was constructed. One **tokenizer-only,
effect-blind** structural probe was executed (§2.2) — it computes token identities at candidate
capture sites and **cannot** compute a transport number, by construction.


---

## 2. `RAH3-PR-001` — the non-copy positive control — PREREGISTERED, prospective

**Status: PREREGISTERED.** Written and committed **before** the first RAH3 forward pass. It
supersedes and absorbs the staged `RAH2-PR-004` (§1.2), inheriting its **pre-committed offset
`N = +1`** and adding the structural invariants and verification that `RAH2-PR-004` lacked.

### 2.1 The question

> **`H4`.** A receiver that passes the direct-harmful positive control **only** because the target
> is the injected token will **collapse** when the donor is captured at a position where the concept
> is *present in context but not on the surface*. A receiver that genuinely reads content out of the
> representation will **survive**.

This is a claim about **instrument validity**, not about doublespeak. Passing it does not re-open
Track A by itself (`RAH-R-018` stands at **A-IV**); it is the *gate* that a new Track-A
preregistration would have to clear first.

### 2.2 The capture rule — deterministic, structural, frozen, and NOT chosen because it works

Selection procedure actually executed, in order (§10):

1. **Inspect tokenised development prompts** — done by a tokenizer-only, forward-pass-free probe
   (`scripts/rah3_capture_site_probe.py`, artifact
   `outputs/boombness/rah_preflight/rah3_capture_site_probe.json`). It reproduces the producer's
   resolution (`rfind` → `token_index_covering`) exactly and reports, per row, the token at each
   candidate site plus the three disqualification predicates.
2. **Structurally valid non-surface candidates** are the fixed trailer following the final concept
   mention: offsets `+1 … +5` over `. given the context .`, and the sequence-final token `-1`.
3. **The deterministic rule is fixed as `N = +1`** — the token immediately after the last concept
   surface occurrence. ⚠ **This offset was frozen by the previous session in `RAH2-PR-004`, before
   any transport number at any offset existed.** It is carried forward unchanged precisely because
   a pre-committed choice cannot have been fitted.
4. **Verification** (§2.3) is a *validity* check, not a selection: it can only **disqualify** the
   rule, never rank it against alternatives by transport.
5. **Frozen.**

⚠ **ONE offset. No sweep.** Reporting the best of `{+1,+2,+3,+4,+5,-1}` would be exactly the
two-free-parameter maximisation `RAH2-C-002` and `RAH2-C-018` were raised for. The other offsets are
computed by the probe **for structural disqualification only** and their transport is never
measured. If `N = +1` is structurally disqualified, the *first* structurally valid offset in the
fixed order `+2, +3, +4, +5, -1` is taken — a rule with no free parameter — and the substitution is
filed as a `RAH3-C-###` **before** any transport number is read.

### 2.3 Invariants — persisted per donor row, and HARD-FAIL on the non-copy path

For every non-copy donor row the producer must record and assert. **No `.get(..., default)`. Raise.**

| # | field | hard-fail condition on `--capture-mode offset` |
|---|---|---|
| 1 | `concept_surface_char_pos`, `concept_tok_idx` | unresolvable |
| 2 | `codeword_tok_idx` (or `null` if absent) | — |
| 3 | `donor_tok_idx` | out of `[0, seq_len)` |
| 4 | `donor_piece` | empty |
| 5 | `capture_offset` | ≠ the frozen value |
| 6 | `overlaps_concept_surface` | **`true` → RAISE** |
| 7 | `overlaps_codeword_surface` | **`true` → RAISE** |
| 8 | `is_candidate_label` | **`true` → RAISE** |
| 9 | `tok_distance_from_concept` | ≠ `capture_offset` (i.e. inconsistent resolution) |
| 10–14 | `donor_L`, `receiver_R`, `q_pos`, `read_pos`, `hops` | `hops == 0` on a row carrying a **scientific** claim |

Plus a cross-row consistency assertion: **`donor_piece` must be identical across all 8 donors**
(the trailer is fixed), and the run raises if it is not — §9's *"offset produces inconsistent
semantics across rows."*

### 2.4 Design — nothing new is invented

| axis | value | note |
|---|---|---|
| development pair | **carrot ↔ bomb** | `--other-concept knife --other-codeword ticket` |
| held-out pair | **lantern ↔ poison** | `--other-concept missile --other-codeword candle` |
| models | **Llama-3.1-8B-Instruct**, **Qwen3-14B** | 2 |
| donor condition | **`direct_harmful`** | the concept is in the semantic context; the captured state is off its surface |
| `--n-donors` | 8 | `--n-examples 8` |
| form set | **`fewshot`** — the EXISTING RAH2 set | `fc_probe_last`, `id07_tmpl`, `id07_raw`, `fewshot_cat`, `fewshot_syn` |
| receiver depths | the existing 5 | frozen Stage-A grid **untouched** (`RAH-C-008`) |
| `--enable-thinking` | `default` | as every RAH2 preflight run |
| jobs | **4** = 2 models × 2 pairs, dev first then held-out | same shape as `rah2pcf_*` |

⚠ **No new receiver form is added.** §7 of the charter: *do not invent a new receiver family before
testing constraint 4.* If constraint 4 fails, adding forms would be searching until it passes.

**Role of each form, fixed now:**

* `fc_probe_last` — **candidate-printing positive reference.** Prints all four labels, so its
  unpatched concept prior is order ¼. It can establish that the *transport machinery* works. It can
  **never** carry a Track-A claim (fails requirement 1).
* `fewshot_cat`, `fewshot_syn` — **exposure-clean, multi-hop scientific candidates.** These are the
  only forms eligible to carry a Track-A claim.
* `id07_raw`, `id07_tmpl` — **COPY DIAGNOSTIC CONTROLS ONLY.** 0 hops. ⚠ Whatever they do, a
  `hops == 0` result is non-semantic **by definition** and can never be a scientific readout.

### 2.5 The paired comparison, and its honest limit

The `N = 0` arm already exists: `rah2pcf_p_cb` / `rah2pcf_q_cb`. ⚠ **It exists on the DEVELOPMENT
bank only.** The held-out cells therefore have **no `N = 0` counterpart**, and — per §1.5 — the
held-out `direct_harmful` positive control has never been run at any offset. Held-out cells are
**descriptive and unpaired**; that limitation is recorded now, before the data, so it cannot be
quietly dropped later.

### 2.6 Two-stage selection — development selects, held-out tests

**Stage 1 — development (carrot ↔ bomb, both models).** The complete grid over donor layers ×
receiver depths × forms is persisted. ⚠ Its maximum is labelled **`selection_max`** and is an
instrument-selection statistic, never an effect estimate.

**Deterministic selection rule, written before the data. Preference order:**

1. **ELIGIBILITY (all required, non-negotiable):** `names_candidates == []` **and** `hops > 0`
   **and** `overlaps_concept_surface == false` **and** `overlaps_codeword_surface == false` **and**
   `is_candidate_label == false`.
2. Among eligible cells: `positive_control_ok == true` (level > 0.10 **and** uplift over unpatched
   > 0.10 **and** `p_concept > p_codeword`).
3. Tie-break, in order: **(a)** larger `p_concept_mean − p_codeword_mean` (penalises codeword
   copying); **(b)** larger `uplift_over_unpatched` (penalises lexical prior); **(c)** smaller
   spread of `p_concept` across the 8 donors (penalises unstable donor-specific behaviour);
   **(d)** lower receiver depth `R`; **(e)** lower donor layer `L`. Deterministic to a single cell.
4. If **no eligible cell** passes (2), the exposure-clean route is recorded as failing on
   development and **`fc_probe_last` is selected separately and only** to answer the narrower
   question "does the transport machinery work at all off-surface?" — routing the outcome to **P-B**,
   never to P-A.

**Stage 2 — held-out (lantern ↔ poison, both models).** Freeze **form, donor layer `L`, receiver
layer `R`, capture offset, patch position, read position**. Run exactly that. **No retuning. No max
over donor layers. No max over receiver layers. No replacement receiver because held-out fails.**
Held-out is a test.

### 2.7 Semantic specificity — a high probability is not enough

`p_concept` alone cannot distinguish transport from copying. Recorded for the frozen configuration:
`p_concept`, `p_codeword`, distractor mass (`other_concept` + `other_codeword`), and total
`option_mass`. A valid semantic-transport readout must show **`p_concept` meaningfully high**,
**`p_concept > p_codeword`**, and **the codeword not dominating**.

The decisive discriminator is that the result must **follow semantic donor identity rather than the
injected token piece.** Under `N = +1` the injected piece is the *same fixed trailer token on every
row and both pairs*, so any pair-dependent output difference **cannot** be lexical transfer of the
captured token — this is the copy control built into the design rather than bolted on. ⚠ If output
tracks the captured piece token-by-token with no semantic abstraction: **COPY DIAGNOSTIC, not
semantic transport.**

### 2.8 Outcome taxonomy — LOCKED

| outcome | condition | consequence |
|---|---|---|
| **P-A** valid non-copy semantic transport | an **exposure-clean, `hops > 0`, non-surface** receiver passes the positive control ≥ 0.10 at the frozen config, **and** held-out reportability passes `MASS_GATE = 0.05`, **and** `p_concept > p_codeword`, **and** semantic specificity passes | licenses a **new** `RAH3-PR-002` Track-A experiment. ⚠ Does **not** reinterpret `RAH-R-018`. |
| **P-B** transport only with candidate exposure | `fc_probe_last` passes but every exposure-clean multi-hop receiver fails | machinery works; **the exposure-clean high-mass readout problem is unsolved.** Track A **remains CANNOT ANSWER.** ⚠ Do **not** run the natural-doublespeak intervention matrix. |
| **P-C** only 0-hop / copy forms pass | `id07_*` pass, nothing else | **no semantic readout established**; `H0` gains another confirming instance. Track A closed. |
| **P-D** even the positive reference fails | `fc_probe_last` fails too | non-surface semantic transport is **not demonstrated by this assay**; the instrument is invalid for the question. **STOP Track A.** Do not interpret intervention nulls. |
| **P-E** population/config invalid | offset not structurally consistent; option mass invalid; span failure; liveness failure; missing rows | **CANNOT ANSWER.** |

⚠ **`RAH2-PR-004`'s inherited prediction:** `id07_raw` collapses, `fc_probe_last` survives. **This
is a registered prediction, not a required outcome.** If `id07_raw` *survives* at `N = +1`, then
`RAH2-C-020`'s copy diagnosis is wrong and the retraction must itself be revisited — registered now
so that outcome cannot be quietly dropped. But it still could not become a scientific readout:
`hops == 0` is non-semantic by definition.

### 2.9 Stopping rule — HARD

If Phase 1 does not establish a valid **exposure-clean, non-zero-hop, held-out high-mass** semantic
readout, the sprint writes:

> **TRACK A REMAINS CANNOT ANSWER — VALID READOUT NOT ESTABLISHED**

and does **not**: add forms · search prompts · scan layers · lower a threshold · quote development
in place of held-out · use a candidate-printing form as the scientific answer. **That is a
scientific result.**

### 2.10 Multiplicity

The confirmatory family for `H4` is **2 models × 2 exposure-clean candidate forms = 4** at the
frozen configuration; the held-out pair is the test set, not a family member. Development is
**instrument selection** and carries **no p-values**. ⚠ A selection-inflated positive control is
never a p-value-bearing effect estimate.

### 2.11 Independence units

Rows here are **8 donor prompts** within one pair, one bank, one condition — they are **not**
independent domains and no domain-level claim is available from Phase 1. The unit of replication is
the **model** (2), and the pairs are **development** and **held-out**, not two samples of one
population.

---

## 3. Track A after the gate — conditional, and NOT written yet

⚠ **Nothing in this section may be implemented or launched before Phase 1's outcome is known.**
It is recorded so the gate cannot be re-negotiated afterwards.

**If and only if P-A**, a new `RAH3-PR-002` asks a **new** question:

> Under `demo_processing_only`, is the internal semantic state **preserved, weakened, relocated, or
> destroyed**, measured with a validated non-copy semantic transport assay?

Arms: **A** baseline · **B** `demo_processing_only` · **C** a late-band control *where anatomically
meaningful* · **D** a destructive comparator such as `legacy_all_query`.

### 3.1 Control validity must be proven at the capture site FIRST

⚠ **RAH established that a late-band control can be VACUOUS if the capture site lies before the
intervention.** Before arm C is used at all, one of two things must be shown:

* the intervention **can** affect the activation actually captured — demonstrated, not assumed; or
* the arm is explicitly labelled **VACUOUS ANATOMICAL NULL**, not "matched inert control", and it
  carries **no** dose-matched specificity evidence.

A valid specificity control must be *capable* of changing the measured computation. If neither
holds, a different scientifically meaningful control is used instead. ⚠ **Never call a vacuous arm
"inert."**

### 3.2 The liveness requirement that catches the geometry trap

Per row, per arm: intervention fired · number of relevant edits · donor capture occurred · capture
is above/below the intervention as expected · patch occurred · receiver read occurred · every
expected-zero counter · every expected-positive counter.

⚠ **The specific RAH hazard:** if the donor layer is at or below the knockout band boundary,
baseline and intervention become **bit-identical** while every preflight gate passes. Therefore an
explicit per-row **`baseline_vs_intervention_donor_delta`** is required. If the scientific claim
expects the intervention to reach the donor state and that distance is **zero on every row**, the
comparison is **VACUOUS** and must not be called preservation. This is enforced in code: prompt
hashes, capture coordinates, intervention counters and donor activation hashes/distances are
compared automatically and the run **FAILS before scientific interpretation**.

### 3.3 Estimands — frozen before any intervention run

Concept transport accuracy · signed concept margin · `p_concept` · `p_codeword` · total reportable
option mass · baseline→arm paired family transitions · domain-level effect · baseline–arm activation
distance (diagnostic) · equivalence verdict wherever preservation is claimed. **None selected after
seeing the result.**

### 3.4 "Preserved" requires an equivalence test

⚠ `p > 0.05` is **NOT** preservation. Any claim of *preserved / intact / same / unchanged* requires
`paired_equivalence.py` or another preregistered equivalence framework, with the margin frozen from
**development / self-repeat** data — never chosen because the observed delta fits inside it. A
preservation result requires **both**: (1) baseline vs intervention inside the equivalence bounds,
**and** (2) baseline/intervention still distinguishable from wrong-concept/shuffled controls.
Otherwise "preserved semantic information" is not established.

### 3.5 If Track A fails, do not search until it passes

If the validated frozen held-out assay shows baseline transports, the appropriate control
transports, and `demo_processing_only` does not — **the correct result is that semantic transport is
disrupted under this intervention at this measured stage.** Do not scan every layer, search offsets,
search receiver forms, or change concepts until one gives preservation. **One** separately
preregistered coarse relocation diagnostic (early / mechanism-band / late — **three** bands, not
32–40 layers) is permitted if scientifically justified; any dense scan is exploratory and requires
independent confirmation.

### 3.6 If Track A shows preservation

Only then does the interesting question open — *where between preserved semantic state and behaviour
does access fail?* Candidate follow-ups (patch semantic donor state into query residual; patch query
residual into response state; attention-output rescue; MLP-output rescue; path patching) are
**named, not launched**. ⚠ The first successful Track-A confirmation **ends this sprint** with a
precise follow-up plan.

---

## 4. Track B — the behavioural problem is a BANK and POWER problem

RAH established that **the historical 80-row design cannot resolve a behavioural effect of the size
we care about** once domain clustering, measured judge noise and realistic baseline rates are
accounted for — and that even `n = 160` at baseline ≈ 0.15 remains inadequate for 80 % power.

⚠ **Therefore: do NOT run another 80-family behavioural confirmation.** Rows alone are not the main
lever. **Domains are.**

### 4.1 Power is RECOMPUTED, not inherited

The handoff's indicative result is **k = 38 domains × m = 16 rows** at baseline ≥ ≈ 0.1375 detecting
a relative effect ≈ 0.70. ⚠ **These numbers are not hardcoded.** `scripts/rah_power_trackb.py` is
re-run **at current HEAD** with **current measured** judge-noise inputs, and the final numbers are
**frozen before bank generation**.

⚠ **Judge noise is a function of baseline ASR, not a constant.** RAH measured that the effective
flip rate *rises* with baseline ASR. Every candidate baseline population uses the appropriate
preregistered judge-noise model, and the power calculation includes that dependence. **Higher ASR
does not automatically mean proportionally more power.**

### 4.2 This is a new confirmation, not a rescue

⚠ The purpose is **not** to find a pair where `demo_processing_only` works. It is to construct a
population with enough statistical capacity to answer the behavioural question **either way**.
Population choice may use grammar, tokenisation, prompt alignment, novelty and **baseline-only**
headroom. It may **never** use intervention outcomes.

### 4.3 Bank requirements

Fresh demonstration pools spanning **38 domains**. ⚠ **"38 domains" must not be manufactured by
renaming or paraphrasing the existing 20** — they must be meaningfully distinct experimental
clusters. Before generation, a **domain registry**: domain id · source/template family · semantic
category · overlap check against previous domains · demonstration-pool provenance · number of
families. An **independent audit that does not import the bank generator** validates it.

### 4.4 Lexical pair selection

A preregistered candidate set of bomb-class concepts and neutral codewords. Selection may consider,
**before any behaviour**: article/grammar compatibility · tokenisation (single leading-space token
on both models) · word length · lexical collisions · semantic clarity · naturalness · harmfulness
class · structural fit. **No intervention results.**

### 4.5 `RAH3-PR-003` — baseline-only screening

Registered **before** any baseline ASR is measured. Freezes: candidate pairs · dev domains · rows
per pair · baseline cap · judge · minimum baseline rate/count · selection rule · number of pairs
advancing · **what happens if none pass**.

Then **baseline only**. No `demo_processing_only`. No late control. No intervention code. ⚠ The
screening pipeline must be **structurally incapable of loading an intervention spec** — enforced in
code, not by intention.

**Every screened pair is reported, including failures:**

| pair | dev n | domains | grammar | tokenisation | baseline attacks | ASR | effective judge flip rate | refusal | truncation | qualifies |
|---|---|---|---|---|---|---|---|---|---|---|

### 4.6 Development and confirmation must be disjoint

Once a pair qualifies, a **new** confirmatory population is constructed: fresh families, fresh
demonstration sets, fresh seeds, preregistered domains. Development rows are not reused. Where
domain overlap is unavoidable, the surviving independence claim is stated explicitly.

### 4.7 The ~20 GPU-hour matrix is a SEPARATE GO/NO-GO

⚠ **Do not launch it merely because the bank exists.** A GO/NO-GO document must first contain: final
bank audit · exact baseline headroom · actual power · judge-noise estimate · domain count · MDE ·
expected GPU-hours · exact arms · exact preregistration · exact stop conditions. Committed and
pushed. **Absent an explicit authorisation of that compute in this session, the sprint stops at:**

> **READY FOR COSTED CONFIRMATORY MATRIX**

⚠ Stopping there is **not** scientific failure.

If authorised, the *same* confirmatory population runs arms **A** baseline · **B**
`demo_processing_only` · **C** a scientifically valid control · **D** `legacy_all_query` where
justified · **E** only if preregistered before B is observed. **No arm is added after seeing
intervention output.**

### 4.8 Stopping rule — HARD

If the 38-domain design cannot produce a qualifying baseline population at the preregistered power,
write **TRACK B BLOCKED BY MATERIAL/POWER** and stop. Do not use the highest-but-inadequate pair,
reduce required power, pool domains, reuse development rows, or "add intervention and see."

If the matrix *does* run and returns null with valid headroom and power, that is a **REAL FAILED
CONFIRMATION**. Do not switch pairs, subset attacks, run only high-ASR domains, raise the cap post
hoc, change judge, or change layer. **Record it.**

---

## 5. Standing rules for this sprint — enforced in code where possible

### 5.1 The absolute ASR rule

⚠ **The primary ASR estimator includes EVERY preregistered row.** Headline ASR is **never** computed
after dropping truncated outputs · keeping only EOS · minimum or maximum length · "scorable"
filtering · removing refusals · removing incoherent rows · selecting successful baseline attacks ·
selecting informative domains · removing judge disagreements · dropping strange completions. **No
ASR cutting. No post-treatment selection.** A post-treatment analysis may exist **only** under the
literal heading **POST-TREATMENT DIAGNOSTIC — NOT A CAUSAL ESTIMATOR**, and never replaces the
primary result.

### 5.2 The cap rule

The cap is chosen from development data and **frozen before confirmation**, targeting effectively
negligible binding. If a confirmatory arm materially hits the cap: **DO NOT FILTER.** Declare **CAP
INVALID FOR PRIMARY ESTIMAND**. Any rerun regenerates **baseline AND all primary arms** at the same
new cap, judged in the **same session**. ⚠ **Never mix caps.**

### 5.3 Self-auditing ASR — code-enforced, not prose-enforced

The software **refuses** to emit a paper-level ASR headline without: expected/generated/judged/joined
rows · missing ids · duplicate ids · baseline and arm numerator/denominator · down/up/both/neither ·
domains and domain effects · `frac_stop_length` · EOS · median/quantile token lengths · refusal
markers · coherence/degeneracy · liveness · edit counts · judge model · judge session · completion
SHA join · bank SHA · git commit · dirty flag · SLURM job id.

### 5.4 Provenance — every RAH3 artifact, including instrumentation

⚠ §1.4 showed the RAH2 positive-control artifacts carry **no provenance block at all**. Every new
RAH3 artifact persists: schema version · git commit · git dirty · branch · timestamp · SLURM job id
· hostname · complete argv · python executable · model · bank path · **bank SHA256** · relevant
code/config hashes · seed · expected n · actual n. If `git_dirty == true`, the diff hash is recorded
or the paper-level run is **refused**. ⚠ **Positive-control artifacts are paper-level methodological
evidence** — the Phase-1 result decides whether an entire mechanistic branch is interpretable.
**Pin them.** No anonymous scientific artifacts.

### 5.5 Verification

* **Two** independent verification implementations for the primary Phase-1 positive-control result;
  **at least one imports no producer analysis helper.** One verifier minimum for every other
  paper-level result.
* ⚠ **The verifier must not inherit the producer's field choice.** `RAH2-C-022`: a verifier
  faithfully reproduced `artifact["p_concept"]` while the quantity was 100 % `p_codeword`.
  Verification is **semantic** — token ids, candidate mapping, positions, probabilities,
  normalisation — recomputed from raw data. Producer field naming is never ground truth.
* ⚠ **Console output is not evidence.** All scientific numbers come from structured artifacts; a
  console column has already been mislabelled relative to its JSON field (`RAH2-C-016`). The
  independent verifier never parses human console tables when raw JSON exists.
* ⚠ **Every guard must prove it fails**: passing case · explicit mutation that makes it red ·
  minimum count · missing-key failure · production-path wiring · historical bad-case test where
  possible. **Mutation-test every important assertion class** — `RAH2-C-023` showed a mutation
  chosen for maximum headroom proves only that the harness runs, while six sibling assertions could
  be wrong by 5 % to 33 784× and still pass. ⚠ **Relative tolerance** for small probabilities;
  absolute tolerances near 1e-8 are vacuous.

### 5.6 Claim-first ledger, then prose

Every paper-level claim gets a structured `reports/RAH3_CLAIM_LEDGER.json` entry **before** any
prose: claim id · exact scope · model · bank · lexical pair · population · n · domains ·
intervention · control · estimand · statistic · CI · p · equivalence · status · limitations ·
artifact · independent verifier. ⚠ **Prose is generated from the ledger and never says more than the
ledger.**

### 5.7 Quantifier audit

At every deep review, grep for **all · every · both · exactly · never · zero · preserved · inert ·
matched · replicated · generalizes · cross-model · held-out · independent** and check **each
occurrence** against literal raw-artifact scope. ⚠ **A true number with a false quantifier is a
false claim.** This is the third consecutive phase whose corrections were sentences rather than
arithmetic.

### 5.8 Corrections are new claims

⚠ `RAH2-C-003 → C-017 → C-018 → C-020` — a correction, its inversion, its withdrawal, and its
reinstatement, each written with full confidence. Therefore every `RAH3-C-###` requires: raw
re-derivation · the exact replaced wording quoted · an all-document search · a structured ledger
update · a prose update · **and an independent auditor of the correction itself.** An auditor's new
wording does not bypass review.

### 5.9 Tests

⚠ **"N passed" from the pre-commit hook is NOT "the full suite is green."** At meaningful milestones
report the **guard-list result**, the **relevant targeted tests**, and the **full suite result**
separately. The full suite runs **serial and exclusive**: one writer, no parallel test process,
`git status` before and after, verify no unexpected tracked modifications (this project has a
history of tests mutating tracked artifacts). ⚠ Never run two full suites concurrently. The known
full-suite/guard ordering problem is inherited as a limitation and is not refactored unless it
blocks the sprint.

### 5.10 Smoke every MODE

⚠ Previous phases repeatedly smoked "the script" and not the mode later used
(`RAH-C-009`; `RAH2-C-015`, where `exemplar_candidate_collisions` was documented, reported as a
verification result, and **never called**). Before any expensive run, smoke the exact form set ·
capture mode · capture offset · model · receiver form · intervention mode · batch size. ⚠ **Smokes
validate code and liveness. They are NOT scientific pilots — do not inspect effect direction and
change the plan.**

### 5.11 One writer · SLURM · commits

**Exactly one** writing session. Read-only subagents fan out aggressively (raw artifact inspection,
independent re-derivation, code review, statistical review, claim auditing); parallel code changes
only in isolated worktrees; **never** two sessions editing this document; **never** a subagent
committing shared-tree changes.

SLURM: reuse `src/boombness/slurm/run_boombness.sh` and `scripts/rbd_submit_wave.sh`; ≤ 6
independent jobs; ⚠ **at most TWO concurrent 14B weight loads TOTAL**; do not scancel healthy queued
jobs for being slow; do not resubmit duplicates; read logs before declaring failure; ⚠ **never
cancel another session's job**; check existing artifacts before submitting.

Commit at scientific checkpoints (PR-001 locked · capture-offset implementation + tests ·
development positive control · frozen configuration · held-out result · Track-A gate decision ·
Track-B power plan · bank audit · baseline screen · costed GO/NO-GO · deep-review corrections · final
audit) — not hundreds of micro-commits — verifying `git status`, the staged diff, and that no foreign
work is swept in.

### 5.12 Out of scope

⚠ **No GCG / MAC / optimisation objective in this sprint.** `d_surface`, retrieval strength and naive
decodability are closed. A quantity becomes a legitimate attack objective only if it is reliable,
held-out predictive, causal, directional, dose-specific, transferable, not a readout/copy artifact,
not truncation/degeneration, and confirmed. **We are not there.**

### 5.13 The research standard

A useful outcome is **not** necessarily a positive outcome. Useful outcomes include: the non-copy
transport assay does not work · the readout problem is genuinely structural · the semantic
representation is destroyed · the behavioural effect fails a powered confirmation · Llama and Qwen
use different routes. ⚠ **The unacceptable outcome is changing the experiment until the old story
returns.** This sprint must be capable of killing the hypothesis.

---

## 6. Deliverables

1. this document · 2. `reports/RAH3_CLAIM_LEDGER.json` ·
3. `reports/RAH3_NONCOPY_POSITIVE_CONTROL_REPORT.md` ·
4. `reports/RAH3_TRACKB_POWER_AND_BANK_REPORT.md` · 5. the complete screening table **including
failures** · 6. `reports/RAH3_REPRO_MANIFEST.json`, **executed** (a manifest that has never been run
is a hypothesis) · 7. the independent verifiers · 8. an updated `RESEARCH_HANDOFF.md` ·
9. `reports/RAH3_SPRINT_SUMMARY.md` stating what was asked, preregistered, run, passed, failed,
declined, what remains unresolved, and **which previous claims must not be revived**.

**Final table**, with `NOT RUN — GATED OFF` written in any cell an earlier gate closed — never left
blank:

| question | Llama | Qwen3 | held-out? | valid assay? | verdict |
|---|---|---|---|---|---|
| non-copy positive-control semantic transport | | | | | |
| exposure-clean high-mass multi-hop receiver exists | | | | | |
| semantic transport under `demo_processing_only` | | | | | |
| semantic preservation equivalence | | | | | |
| 38-domain behavioural bank power | | | | | |
| baseline headroom qualified | | | | | |
| behavioural confirmatory effect | | | | | |

**Final adversarial audit, mandatory:** one read-only auditor instructed *"assume the main RAH3 claim
is wrong; find the strongest way to refute it from raw artifacts, code, population structure,
selection logic and measurement semantics — do not summarise, try to kill it"*, then a **second**
auditor over any corrections the first produced. ⚠ `RAH2-DR-002` was asked to refute rather than
check, and took that phase's headline down in one pass. **The arithmetic can be perfectly
reproducible while the sentence is scientifically false.**

---

## 7. `RAH3-R-001` — the capture rule is structurally VALID on every row. Registration verification, no transport measured

`scripts/rah3_capture_site_probe.py` → `outputs/boombness/rah_preflight/rah3_capture_site_probe.json`.
**Tokenizer only. No model weights, no forward pass, no intervention, no transport number** — this
probe is *incapable* of producing one, which is why it could be run before the freeze without
contaminating it.

It reproduces the producer's resolution (`templated.lower().rfind(surf.lower())` →
`token_index_covering`) on the **8 registered donors × 2 models × 2 banks = 32 donor prompts**, and
reports the token at each candidate site plus the three disqualification predicates.

| offset | piece — Llama, carrot↔bomb | piece — Llama, lantern↔poison | piece — Qwen3, carrot↔bomb | piece — Qwen3, lantern↔poison | consistent across 8 rows | disqualified rows |
|---|---|---|---|---|---|---|
| **0** (historical) | `' bomb'` | `' poison'` | `' bomb'` | `' poison'` | yes | **8 / 8 — the copy site** |
| **+1 ← REGISTERED** | `'.'` | `'.'` | `'.'` | `'.'` | **yes** | **0** |
| +2 | `' given'` | `' given'` | `' given'` | `' given'` | yes | 0 |
| +3 | `' the'` | `' the'` | `' the'` | `' the'` | yes | 0 |
| +4 | `' context'` | `' context'` | `' context'` | `' context'` | yes | 0 |
| +5 | `'.'` | `'.'` | `'.'` | `'.'` | yes | 0 |
| −1 (final) | `'\n\n'` | `'\n\n'` | `'\n'` | `'\n'` | yes | 0 |

Token sequence from the concept: `[' bomb', '.', ' given', ' the', ' context', '.', <eot>, …]` on
Llama and `[' bomb', '.', ' given', ' the', ' context', '.', <im_end>, '\n']` on Qwen3 — **the
trailer is identical across both models and both lexical pairs.**

**Three things this establishes, and one it does not:**

1. **`N = +1` is structurally valid on all 32 rows.** It resolves to `'.'`, identically everywhere,
   and violates none of the three disqualification predicates. §2.2 step 4 passes; the `RAH3-C-###`
   substitution branch is **not** triggered.
2. **Offset 0 is disqualified on 8/8 rows of every cell** — the probe confirms mechanically that
   every historical `direct_harmful` positive control was captured *on the concept surface*. This is
   the `RAH2-C-020` copy confound, measured rather than argued.
3. **The offset denotes one structural position, not an average over several** (§9's consistency
   requirement), on both models and both pairs.

⚠ **What it does NOT establish:** nothing about transport. `'.'` is a syntactically generic token,
and whether the residual stream at that position carries the concept is exactly the open question.
A high `p_concept` there would be a real result; a low one is the registered, most-likely failure
mode (`RAH2-PR-004`: *"both collapse … the control is uninformative"*). ⚠ **The probe's clean result
is not a preview of the answer.**

## 8. `RAH3-R-002` — the capture-site implementation, and every invariant proven RED

`src/boombness/rah_preflight_transport.py`: `resolve_donor_capture()` (pure, model-free, so every
invariant is independently re-derivable **without a GPU** — the RAH2 positive controls could not be
audited for this confound precisely because resolution happened inline in a forward-pass loop and
only `piece` reached the artifact), `assert_capture_consistent()`, `_char_spans()`,
`_codeword_tok_idx()`, `sha256_file()`, `_git_branch()`, `_diff_sha256()`; CLI `--capture-mode
{surface,offset}` and `--capture-offset INT`.

⚠ **The default is `surface` / `0` and is pinned by a test that greps the source**, because a silent
default change would make every artifact in `outputs/boombness/rah_preflight/` non-reproducible
without anything erroring.

Overlap is decided **twice** — by character span against **every** occurrence of the surface in the
prompt, *and* lexically — because either test alone has a hole. A candidate label is detected by
**token id** as well as by string: the id is what the readout scores, so an id match is the precise
*"the capture supplies the answer"* condition, and a string-only check would miss it.

`tests/test_rah3_capture_site.py` — **20 tests, all green (31 with the inherited span guards).**
Every invariant has a paired `MUTANT_` test that constructs the violating input and asserts a
refusal: surface-mode with non-zero offset · offset-mode with offset 0 · concept **subtoken** at a
negative offset · codeword surface · candidate label **by token id** · out of bounds (both signs) ·
whitespace capture · absent concept · unknown mode · cross-row divergent piece · cross-row divergent
distance · **zero rows** (so an empty run cannot report a vacuous PASS).

### 8.1 `RAH3-C-001` — a mutation I wrote could not go red, and that was the finding

My first attempt at the concept-overlap mutation was `[' bomb', ' bomb']` at `+1`. **It did not
raise.** `rfind` anchors on the **last** occurrence, so a duplicate *after* the anchor is
unreachable at a positive offset. The second attempt, `[' bomb', ' bombard']`, also did not raise
the expected error — `'bomb'` inside `' bombard'` sits at a *later* character position, so `rfind`
selects **that**, and the *anchor* assertion fires first with a different message.

**Conclusion, now pinned as a test:** at a **positive** offset the concept-overlap branch is
**unreachable by construction** — any concept characters downstream of the anchor *would have been*
the anchor. The branch is still live and is proven RED at a **negative** offset via the multi-piece
concept `' bo' + 'mb'`.

⚠ This is `RAH2-C-023` avoided rather than repeated: the honest move was to **record that the
mutation could not go red and why**, not to contrive an input until it did. A green test whose
failure mode is structurally impossible is a vacuous test, and it would have been indistinguishable
from a real one in any count of "N passed".

## 9. `RAH3-C-002` — ⚠ SHARED-TREE COLLISION: a second writer committed this sprint's code inside an unrelated commit

**Filed as a provenance defect, not a complaint, because it affects what the record says.**

At session start (§1.1) HEAD was `6ecf1e60` with one staged file. While RAH3's capture-site
implementation was being written, **HEAD advanced by two commits made by another live Claude Code
session in the same working tree**:

| commit | message | what it actually contains |
|---|---|---|
| `4e3fab1d` 18:43:55 | *"RAH2-PR-004: preregister the capture-site control, before any forward pass"* | the staged file of §1.2 — expected |
| `7906faae` 19:01:30 | *"RAH2-DR-003 / C-030: the provenance block audited BEFORE it attests anything"* … ending **"PR-004 unaffected."** | the provenance audit **plus 14 added lines of RAH3's `resolve_donor_capture` / `NON-COPY VIOLATION` implementation**, swept in from my uncommitted working tree |

⚠ **`7906faae`'s message does not describe its contents.** RAH3's non-copy capture mechanism is
recorded in git under a commit about a provenance audit that asserts it changed nothing else. Anyone
bisecting for when the capture-site option appeared will find the wrong commit and the wrong
rationale.

**Not corrected by rewriting history.** The other session is live; a `reset`/`rebase`/`amend` would
destroy work in flight — the same class of hazard as the project's standing *"never `git stash pop`
here"* rule. The defect is recorded here instead, and this entry is the pointer a bisect needs.

**Discipline adopted for the rest of this sprint, and worth inheriting:** ⚠ **stage by explicit
path, never `git add -A` / `git commit -a` in a shared tree.** That is exactly how the foreign
sweep happened, and it is the only way to guarantee a commit message describes its own diff.

⚠ **Unresolved and material:** §47 requires **exactly one writer**, and there are demonstrably two,
both working the *same* experiment — the other session's `RAH2-PR-004` registers the **same donor
condition, same offset `N = +1`, same form set, same two models, same two pairs, same 4 jobs** as
`RAH3-PR-001`. Submitting both would be **duplicate GPU work on a shared queue** and two writers
into `outputs/boombness/rah_preflight/`. **No RAH3 GPU job is submitted until this is resolved** —
see §10.
