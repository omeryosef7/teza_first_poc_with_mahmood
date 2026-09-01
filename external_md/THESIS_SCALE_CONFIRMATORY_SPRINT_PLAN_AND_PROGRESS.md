# THESIS-SCALE CONFIRMATORY SPRINT — plan and append-only progress

**Id namespace `TSC-`.** Branch `behavioral-causality-sprint`. Opened 2026-09-02.
Predecessor log: `external_md/CONFIRMATORY_DEFENSIBILITY_SPRINT_PLAN_AND_PROGRESS.md` (`CDS-`).
Predecessor summary: `reports/CDS_SPRINT_SUMMARY.md`.

**This file is the scientific provenance for this sprint. Chat context is not.** Another session
must be able to recover the full state from this file alone.

---

## §0 — CURRENT SCIENTIFIC TRUTH (inherited, not re-derived)

The state below is what the previous sprint left standing *after* its own adversarial audit. Where
an older claim conflicts with a later correction, **the later correction wins**. No headline is
revived because its old number was large.

### 0.1 The strongest standing result — `CDS-R-018` / `CDS-DR-002`

**Demonstration-specific attack removal on Llama-3.1-8B-Instruct**, on the new capable population:

| item | value |
|---|---|
| bank | `data/boombness_prompts/boombness_prompt_bank_cds38_button_bomb.jsonl` |
| lexical pair | `button ↔ bomb` |
| population | `behavioral` × `natural_doublespeak` × `cds_n4` × `n_examples=4` = **380 rows** |
| clusters | **38 domains × 10 verified-disjoint demonstration pools** |
| dose | n=4 demonstrations |
| band | layers **6–14**, `attn_knockout`, α=1.0 |
| scope | `demo_processing_only` |
| cap | **640** new tokens, `--attn-impl eager` |
| judge | `openai/gpt-4o-mini`, pinned, one manifest for all five arms |
| baseline ASR | **0.3895 (148/380)** under judge pass 1 · **0.4184 (159/380)** under judge pass 2 |
| `demo_processing_only` | **0.1447 (55/380)** — **−104 rows** vs the pass-2 baseline |
| controls (attack rows) | `A`=159 · `d1`=159 · `d2`=150 · `d3`=148 → **0 / −9 / −11** |
| primary test | exact paired **domain** sign test, demoproc vs **each** control |
| p-values | **2.556e-06 / 1.309e-07 / 6.938e-08** (floors 4.66e-10 / 2.33e-10 / 1.16e-10) |
| informative domains | 32 / 33 / 34 |
| verification | `scripts/cds_verify_stage2.py` — 349 checks, 0 failures; `scripts/cds_mutate_stage2.py` — 18/18 red |

**Verdict: STRONG.** It is preregistered (`CDS-PR-001`), independently verified, and adversarially
audited.

### 0.2 The scope limits that this sprint exists to close

1. **ONE lexical pair.** `button↔bomb` only. The `basket↔bomb` replication is **VOID**, not
   negative — see 0.3.
2. **ONE harmful request.** All 380 rows carry an identical `final_query_text` (`CDS-C-020`,
   verified from the bank). The 38 clusters are **38 demonstration pools around one request**, not
   38 harmful behaviours. **Nothing here is generality over requests.**
3. **The controls are neutral-filler controls.** Per-row `control_draw` shows
   **99.79 % / 99.70 % / 98.31 %** of drawn keys lie strictly *before* the demo block, inside the
   `n_preamble = 10` neutral filler that `main_longpre_cds` adds solely to make count-matching
   feasible. `query_span_positions` protects the request by construction. So the established
   contrast is **"masking demonstrations ≫ masking neutral preamble filler of equal masked-key
   count"** — real, and narrower than "demonstrations vs any structurally active context"
   (`CDS-C-019`).
4. **The 0 / −9 / −11 control deltas are inside the instrument's noise.** The same 380 completions
   judged twice flip **51 labels (13.4 %)**, ±11 rows (`CDS-C-018`). Those cells must be stated as
   *within judge re-run variance*, **never** as informative negatives. The **−104** headline is
   ≈ 9× that noise and survives.
5. **ONE model.** The old Qwen3 `C7` population does **not** support the claim at its stated
   domain-level independence unit — every cell is incapable-by-construction or capable-and-null
   (`CDS-R-005`). A **capable** Qwen replication on the **new** design is still needed.

### 0.3 `CDS-R-020` — the `basket↔bomb` replication is VOID FOR A BANK DEFECT

All four `basket` intervention arms **crashed**:

```
ValueError: occurrence_count_mismatch:text=5,tokens=6
```

on exactly the three `school_campus` prompt ids **named in the log by `prompt_id` before any
generation ran** (`CDS-C-002`): `566c998c6df83a30`, `56c76e11095a5d48`, `f953fbbb2376f8db`.

The asymmetry is the whole story: in a **baseline** arm the failure ledger catches the exception
(`score_behavior.py:1861`) and the run continues at **377/380**; in an **intervened** arm the same
exception is raised from the pre-flight loop at `score_behavior.py:1642`, which is **not** inside a
`try`, and it kills the job.

⛔ **This is NOT a failed replication and must never be reported as one.**

### 0.4 Other conclusions this sprint must preserve

* `d_surface` / Boombness is **not** a valid attack objective.
* Mapping installation is **not sufficient** for behavioural attack — but the clean evidence is the
  matched-skeleton contrast (2/24 vs 12/24, Fisher p = 0.0034), scoped to one pair, not `C7`.
* Refusal restoration is **not** a universal explanation of attack removal. On the button bank the
  same scope makes refusal **FALL** (−20 rows, p = 0.0034) while attack falls by 104 — the
  strongest available evidence against "attack dies because refusal returns".
* `C1` ("`demo_processing_only` restores refusal") is **BANK-SCOPED**: it restores refusal on `d10`
  (both models) and `carrot↔bomb`, and **reduces** it on `button↔bomb`.
* The clean activation-readout problem remains **unresolved** (`RAH3`, Track A = CANNOT ANSWER).
* **GCG / MAC stay closed** until a stable, causal, transferable low-dimensional objective exists.

---

## §1 — WHAT WE CAN DEFEND TODAY, BEFORE THIS SPRINT ADDS ANYTHING

* Masking demonstration processing at layers 6–14 removes attack on Llama, `button↔bomb`, at
  **38 demonstration-pool clusters around one harmful request**, against three count-matched
  neutral-preamble controls, domain sign test **p ≤ 2.6e-06**.
* The removal is **not** explained by refusal returning: refusal falls on the same rows.
* The domain ICC of that population is **0.1583** (button baseline ASR); `carrot` measured
  **−0.0123**.
* Judge re-run noise on byte-identical text is **13.4 %** of rows on this exact population.

## §2 — WHAT WE CANNOT DEFEND TODAY

* Anything **cross-lexical** — one pair only.
* Anything **cross-model** — the Qwen population that exists is incapable at the claimed unit.
* Anything **across requests** — one request.
* "Demonstrations are special relative to *any* context" — the live controls are neutral filler.
* Any control-vs-baseline difference of magnitude ≤ ~11 rows — that is inside judge noise.
* That the headline survives **independent re-judging** — measured on the Stage-1/Stage-2 pair only,
  not as a designed robustness test.

---

## §3 — PRIORITY ORDER (fixed; changed only for a scientific blocker, and only with a logged reason)

| # | task | status |
|---|---|---|
| **P1** | Complete the independent lexical-pair replication on Llama, `basket↔bomb`, via a generic `--exclude-prompt-ids` | see §5 |
| **P2** | Run the new capable 38-cluster design on **Qwen3**, Stage-1 baseline screen first | see §6 |
| **P3** | Re-judge the headline populations; quantify judge robustness | see §7 |
| **P4** | Build (and if feasible launch) the **request-diverse** confirmatory bank | see §8 |
| **P5** | Design a **structurally active** count-matched control | see §9 |
| **P6** | Strengthen installation ≠ sufficiency — only if P1–P4 are done or blocked | not started |

**Explicitly NOT tonight:** Boombness correlation sweeps · new readout searches · GCG · MAC ·
arbitrary layer searches · low-rank decomposition · a third model family · unrelated mechanistic
exploration.

---

## §4 — STANDING RULES FOR THIS SPRINT

### 4.1 Preregistration
Every confirmatory forward pass gets a `TSC-PR-nnn` entry appended **and committed** here **before**
generation, containing: hypothesis · null/alternative · model · bank + hash · lexical pair ·
population · dose · arm definitions · mask scope/band · expected sample count · **true independence
unit** · baseline-headroom criterion · capability/power analysis · primary endpoint · secondary
endpoints · exact statistical test · alpha · control arms · exclusion rules · tokenization/liveness
requirements · generation cap · judge model · stop/decline conditions · artifact paths · expected
verdict categories.

### 4.2 Verdict vocabulary — closed set, never extended after seeing a result
`CONFIRMED` · `REPLICATED` · `CAPABLE NULL` · `DECLINED FOR POWER` · `VOID` · `CANNOT ANSWER`

### 4.3 Independence units
* Current 38-domain banks: the unit is the **demonstration-pool domain**, k=38. It is **not** the
  request and **not** the row.
* Request-diverse bank (P4): the unit is the **harmful request**. Rows and demo pools are nested
  inside it. *"N=800 independent examples" is forbidden when there are 40 requests.*
* Row-level McNemar is reported **descriptively only**, never promoted to a headline.

### 4.4 Power / capability
Sample size is **frozen before intervention outcomes**. No sequential N increases after seeing a
p-value. Every design states rows · clusters · what a cluster is · requests · demo pools · lexical
pairs · models · doses. Capability uses the **measured** ICC (`scripts/cds_power_domain.py`), the
**measured** judge-flip rate, the actual cluster count and the measured baseline headroom. The
attainable p-floor `2/2^k_inf` is reported next to every p-value and **never in an adjacent column
without a label** — that is how `< 1e-9` got published for `2.6e-06`.
**A design that cannot answer its question at its own independence unit is DECLINED, not run.**

### 4.5 Bug-resistance gates, all mandatory
**A. Liveness** — the intervention fired on every intended row; expected positions edited; expected
edit count; no silent skips; no out-of-range patches; mask count correct; counters persisted.
**B. Row matching** — same intended prompt ids, same exclusion list, same bank hash, same dose, same
generation settings across arms. **Analysis is refused if arms silently differ.**
**C. Tokenization** — the span audit runs **before** expensive intervention arms; any structural
row exclusion is declared **before** outcomes.
**D. Batch matching** — baseline and intervention arms use matched batch behaviour.
**E. Truncation** — released cap; report `frac_stop_length` per arm and the arm differential
against the **0.02** gate, computed from each run's own `stop_reason` rows.
**F. Judge provenance** — every judged row hash-joins to its completion by `completion_sha256_16`;
persist pinned judge model, completion hash, source run, judge run id.
**G. No filtering** — no ASR filtering, no dropping "weird" generations, no post-hoc domain removal,
no outcome-based exclusion. Ever.
**H. Controls cannot be vacuous** — the byte-identical no-op guard (`NOOP_GUARD = 0.99`) must show
the control actually changed completions.

### 4.6 Verification
Every **new** headline gets a **stdlib-only independent verifier** that imports nothing from the
producer and re-derives row counts, attack counts, per-cluster outcomes, `k_informative`, the
primary p-value, the effect, the capability rule and the verdict from raw artifacts — then a
**mutation harness** that corrupts each load-bearing input and shows the verifier goes RED.
"The script ran successfully" is not evidence. Use **relative** tolerance: an absolute tolerance
already swallowed corruption down to 3e-19 once (`CDS`).

### 4.7 Adversarial review
Every candidate headline gets a read-only agent told to **refute** it, hunting specifically for:
wrong independence unit · pseudo-replication · lexical-pair selection leakage · baseline-headroom
selection leakage · request duplication · demo-pool dependence · mask-count mismatch · neutral-filler
confound · batch mismatch · truncation · judge drift · parser inconsistency · intervention not firing
· tokenization mismatch · wrong sign · wrong denominator · wrong p-floor · post-hoc exclusion ·
cross-session artifact mismatch · claim broader than the population.

### 4.8 Shared-tree hygiene
This working tree has **other writers**. **Never** `git add -A`. **Never** `git stash`. Commit only
with explicit path limiting. Do not run the full test suite concurrently with a job that mutates
artifacts.

---

## §5 — P1 — `basket↔bomb`, the independent lexical-pair replication

**Status:** in progress. Preregistration `TSC-PR-001` below.

## §6 — P2 — capable Qwen3 replication
**Status:** recon in progress.

## §7 — P3 — judge robustness on the headline populations
**Status:** recon in progress.

## §8 — P4 — the request-diverse confirmatory bank
**Status:** design in progress.

## §9 — P5 — structurally active matched control
**Status:** design in progress.

## §10 — PROGRESS LOG (append-only)

* **2026-09-02, session open.** Read `reports/CDS_SPRINT_SUMMARY.md`, the `CDS` log §13/§14/§15,
  `score_behavior.py`, `cds_domain_test.py`, `cds_stage1_gate.py`, `cds_power_domain.py`,
  `judge_p2.sh`, `cds_submit_judge.sh` and every `cds*` run config. Confirmed from the raw
  artifacts, independently of the log:
  * the basket baseline `cds1A_basket_20260901_191635_1462938` holds **377** result rows;
  * the basket bank's selected population is **380** rows;
  * the three missing ids are **exactly** `566c998c6df83a30`, `56c76e11095a5d48`,
    `f953fbbb2376f8db`, all `domain=school_campus`, `example_position=near`,
    `n_target_occurrences=5`, `target_surface=basket`;
  * the baseline `summary.json → failures` records
    `{"resolve:occurrence_count_mismatch:text=5,tokens=6": 3}` and names those same three ids.
  * the crash site in an intervened arm is the pre-flight loop at `score_behavior.py:1642`
    (`resolve_occurrences` called outside any `try`), whereas the main loop catches the same
    exception at `score_behavior.py:1861`. **The remedy is therefore an up-front population
    exclusion, not a `try` around the pre-flight** — a `try` there would reintroduce exactly the
    silent-skip asymmetry that made this crash informative.
* **2026-09-02.** Cluster idle (`squeue -u` empty). Six L40S nodes up in `killable`.
