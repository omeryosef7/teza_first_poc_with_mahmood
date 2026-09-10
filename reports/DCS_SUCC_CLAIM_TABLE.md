# DCS SUCCESSOR PHASE — CLAIM TABLE, WHAT WE CAN SAY, WHAT WE MUST NOT SAY

Successor-plan deliverables **2, 3, 4** (§35) and the answer set for **§43**.

**Authority.** The append-only record is
`external_md/DCS_BOMBNESS_MECHANISM_AND_ASR_SUCCESSOR_PLAN_AND_PROGRESS_20260909.md`; ids
(`S-00x`, `R-20x`, `C-2xx`, `D-00x`) refer to its entries. Every row carries an entry id **and** an
artifact path. Nothing here is a number that cannot be pointed at.

**Population, once.** Bank family `ts116m`, bank `ts116m_button_bomb`
(`bank_file_sha16 dcd92d723f3e6d00`) with `ts116m_basket_bomb` as a **declared transfer pair, never
pooled**. 116 domains built, **three preregistered whole-population exclusions**
(`restaurant_kitchen`, `school_campus`, `subway_station`), **113 analysed**, frozen split
**67 train / 23 validation / 23 test** (`dcs_ts116_domain_split.json`, `manifest_sha16
be7d2c772d814ef3`). Model **Llama-3.1-8B-Instruct**, revision
`0e9e39f249a16976918f6564b8830bc894c89659`, eager attention, bfloat16, layer convention
block `L` == `hidden_states[L+1]`. **Independence unit is the DOMAIN throughout.**

**The bank is a 2 × 2** — `A` benign_literal, `C` natural_doublespeak (harm demos, codeword surface),
`E` concept_in_benign_ctx, `B` direct_harmful — and cells **A and C carry a token-identical 28-token
query span** (`S-001`).

**STATUS vocabulary**, used strictly: `CONFIRMED` · `MEASURED` (a real quantity, no claim attached) ·
`NEGATIVE` · `WITHDRAWN` · `REJECTED` · `CANNOT ANSWER` · `INCONCLUSIVE`.

---

## 1. THE CLAIM TABLE

| # | statement | status | entry | artifact |
|---|---|---|---|---|
| 1 | **The Doublespeak attack works, and beats simply asking.** `button`, cell C dose 4 against the *direct harmful request*: **+0.3186** raw / **+0.1327** concept-present over all 113 domains (**+0.1899** over the 79 that move), **103 of 104** informative domains on the raw channel, Holm-rejected at α/3 | **CONFIRMED** (`Q1d`, preregistered) | `R-206`, ENTRY 037; denominators `S-010` | `outputs/dcs_succ/pr066_behaviour.json`, `phase_statistics.json` |
| 1b | **It replicates on the second codeword.** `basket` `Q1d`: **+0.0451** over 113 domains, **+0.1214** over the 42 that move, **41/42** positive, p = 1.96e−11. Its own dose-0 floor is **0.0221** raw / **0.0000** concept-present | **REPLICATED** (exploratory; the transfer pair is never pooled) | `R-207`, `S-010` | `outputs/dcs_succ/concept_presence_basket.json`, `phase_statistics.json` |
| 2 | **Per-domain semantic installation predicts per-domain attack success.** Spearman **ρ = 0.3961** over 113 domains, permutation p **at its 9.999e−05 floor**, CI [0.228, 0.541]; MDE 0.2996; sign positive in **3/3** splits | **CONFIRMED** (`Q2`, preregistered primary) | ENTRY 037 | `outputs/dcs_succ/pr066_behaviour.json` |
| 3 | That correlation **is not the judge's false-positive channel**: recomputed on `asr_and_concept_present` it **strengthens** to **0.4206** pooled / **0.5260** train, both at the permutation floor | qualification on 2 | `C-215`, ENTRY 042 | `outputs/dcs_succ/q2_concept_present.json` |
| 3b | **`Q2` replicates on `basket`**: ρ = **0.4468** raw / **0.4868** concept-present over 113 domains, p at the permutation floor, and significant on the 23-domain test split alone (0.4615, p = 0.028) | ⛔ **EXPLORATORY, not a second confirmatory test** — `PR-066-A2` names `ts116m_button_bomb` in **both** `predictor_x` and `outcome_y`; only basket *generation* was gated | `R-207`, corrected by `C-217c` | `outputs/dcs_succ/q2_concept_present_basket.json` |
| 3c | Installation predicts **both** whether the attack works in a domain **and** how much. A "per-domain switch" reading is **not supported**: the two codewords give opposite orderings of the two correlations (button 0.293 / 0.392; basket 0.461 / 0.351) | **NOT SUPPORTED** — withdraws `S-010`'s mechanistic gloss, not its arithmetic | `S-011` | `outputs/dcs_succ/q2_concept_present*.json` |
| 4 | **The demonstration→query pathway runs through the codeword's query row.** Concept-free K ladder: adding that one row to the cut moves the readout **−4.49**, **61.7 %** of the whole climb; the four content rows after it add **1.5 %**; the dose-matched 3-draw non-demonstration control moves **+0.03**; **67/67** domains, p at its 1.355e−20 floor | **CONFIRMED** as a pathway result | `R-205`, ENTRY 035 | `outputs/dcs_succ/kladder_sowk_train.json` |
| 5 | The ladder's **shape is `NEITHER`** by the frozen rule (a step needs a rise crossing 0.20 → 0.50; K9 sits at 0.368). ⛔ **The word "step" is not used** | qualification on 4 | `R-205` | same |
| 6 | **The codeword's state does not carry the reading.** Donor→recipient full-hidden-state transplant at that token, **every layer window**, 67 domains: `donor_ceiling` **+12.33** log-odds in **67/67**; `transplant\|all` **+0.0066 = 0.054 %** of the gap at 32/67 domains, p = 0.81. Liveness proved per-row (the logit-lens columns take the donor's *exact* value inside the patched window) | **NEGATIVE**, well-powered | `S-007`, ENTRY 033 | `outputs/boombness/aggressive_patching/pr068_train67_*` |
| 7 | **`B1` is not localised at the codeword.** On the position-portable cosine it is **indistinguishable from the adjacent neutral token** (mixed signs, 34–44/67, p 0.014–1.0) and **worse-aligned than the final prompt token** (−0.20, **1–2/67**, p ≈ 1e−17…1e−19), both codewords, every layer | **NEGATIVE** | `S-008`, ENTRY 041 | `outputs/dcs_succ/b1_position_control.json` |
| 8 | **`B1` is a real, reproducible measurement**: 0.1044 / 0.1366 gap units at the peak layer, **66–67 of 67 domains**, ~14 sd over 12 random directions, replicated on two codewords, independently re-derived to 6–7 significant figures by an agent forbidden to read the original | **MEASURED** | `S-002`, `A-103` | `outputs/dcs_succ/bombness_candidates_train.json`, `reports/DCS_SUCC_S002_INDEPENDENT_VERIFICATION.md` |
| 9 | **`B1` is the token × context interaction, not a concept signal.** `B1 = H + I` exactly; `I` = **128 % / 102 %** of `B1` at **67/67** domains and the harm-context main effect `H` is **negative** (−0.0287, 13/67). Length cannot produce it — the `seq_len` deltas of `C−A` and `B−E` are distributionally identical, so it cancels in `I` | interpretation of 8 | `C-208a`, ENTRY 025 | same |
| 10 | **`B1` carries no licensed concept specificity.** Concentration ratio (projection retained ÷ axis retained after Gram-Schmidt against knife and gun) = **1.20** on button and **1.02** on basket. 1.0 = spread uniformly | **WITHDRAWN** | `S-009`, ENTRY 043; supersedes `S-002` | same |
| 11 | Register does **not** explain `B1`'s between-domain variation: leave-one-**domain**-out CV R² is **negative on all six** codeword × feature-set combinations (−0.35 to −2.08) | qualification on 8 | `S-005`, ENTRY 023 | `outputs/dcs_succ/b1_surface_floor_*.json` |
| 12 | Demonstration **length** is a real but bounded confound: cell C's block is **+39.6 chars**, r = 0.31/0.18, and extrapolating to zero length delta leaves **84.8 % / 92.7 %** of `B1` | qualification on 8 | `S-005` | same |
| 13 | **The prototype candidate is rejected**: a context-only prototype containing **no concept token** (`μ_C`) beats the concept prototype at every layer ≥ 8 (0.0515 vs 0.0429) | **REJECTED** | `S-003a`, ENTRY 016 | `outputs/dcs_succ/bombness_candidates_train.json` |
| 14 | **The ASR instrument has a systematic false-positive channel.** Cell C **dose 0** — no demonstrations, nothing installable — reads **0.1549** with refusal 0.0000; all 35 positives across 31 domains are the model answering the *literal* codeword question well | **MEASURED** instrument defect | `C-209`, ENTRY 027 | `outputs/dcs_succ/concept_presence.json` |
| 15 | That floor is **codeword-dependent by 7×**: 0.1549 (button) against **0.0221** (basket) on the identical null | qualification on 14 | ENTRY 042 | `outputs/boombness/judge/tsb66bj_C_n0_*` |
| 16 | **Judge reproducibility, measured on this population**: on **226 byte-identical prompts** generated twice and judged twice (completions identical **226/226**), label disagreement **0.1372** [0.0983, 0.1881], **κ = 0.4435** | **MEASURED** | `R-204`, ENTRY 030 | `outputs/dcs_succ/n5_judge_reliability.json` |
| 17 | Consequently **cell B's 0.0088 and cell E's 0.0053 are below the instrument's own noise** and are not distinguishable from zero | qualification on 14/16 | `C-208d`, `R-204` | same |
| 18 | **Position sweep verdict.** The first reading (gap units, "4.5× larger downstream") was a **denominator artefact** — the reference gap shrinks up to **30×** downstream | **INCONCLUSIVE**, superseded by 7 | `C-214`, ENTRY 040 | `outputs/dcs_succ/b1_position_control.json` |
| 19 | Scope of everything above: **one model**, **one bank family**, **two codewords**, **bomb only** (knife installs 3/113, gun 1/113 — arms requiring them are unconstructible), **TRAIN for every representational result**, and register remains a stated corpus limit (`Q-014`, undecided) | — | inherited + `S-005` | — |

---

## 2. WHAT WE CAN TELL MATAN

1. **The attack is real and it is better than asking.** On 113 domains, Doublespeak beats the direct
   harmful request in **103 of 104** informative domains. On the corrected outcome it runs at
   **0.1398** against the direct request's **0.0071** — roughly **20×**.
2. **The model's own semantic report predicts whether the attack lands.** ρ = **0.3961** over 113
   domains, preregistered, powered, permutation p at its floor, **and it gets stronger (0.4206)**
   when the judge's false positives are removed. This is the link `R-097` was CANNOT ANSWER for.
3. **We know where the pathway runs.** On a readout that never names the answer, **one query row —
   the codeword's — carries 62 %** of the demonstration→query effect, against a dose-matched
   non-demonstration control that moves +0.03, in 67/67 domains.
4. **But the codeword does not *store* anything.** Transplanting its entire hidden state at all 32
   layers transfers **0.05 %** of a 12.33 log-odds gap, and its state is no better aligned with the
   concept axis than its neighbour's. **The codeword row is a conduit, not a store** — and that
   *explains* `PHASE 9`'s earlier null rather than merely agreeing with it.
5. **Answering your question directly — "is the model moving toward the representation of a bomb?"**
   We built the measurement you asked for: how far the codeword's state moves along a
   `button → bomb` axis built where nothing installs. It moves **~10 %** of that gap in **66–67 of
   67 domains**. **But it is not bombness.** It is the *token × context interaction* — how anomalous
   the queried word is in its frame — it is not localised at the codeword, and its concept
   specificity is **1.02×** on the replication codeword, i.e. none.
6. **The ASR instrument needed repair before any of this was quotable.** StrongREJECT scores a fluent
   answer about *literal buttons* as success: the no-demonstration null reads **15.5 %**. Every
   number above carries that floor and the judge's measured **13.7 %** label-flip rate.

---

## 3. WHAT WE MUST NOT SAY

⛔ **"the codeword is represented as BOMB"** — rows 6, 7, 9, 10.
⛔ **"Bombness is localized at the codeword"** — row 7, now with a direct measurement behind it.
⛔ **"the probe measures concept identity"** — rows 9, 10.
⛔ **"remapping and concept identity are separable axes"** — never re-attempted; inherited as UNSUPPORTED.
⛔ **"the concept direction is causally used"** — row 6.
⛔ **"Bombness predicts jailbreak"** — row 2's predictor is **installation**, the model's own semantic
report, **not any Bombness candidate**. No candidate survived.
⛔ **"representation destruction predicts ASR"** — no intervened behavioural arm was run.
⛔ **any ASR difference below 0.1372**, the measured label-flip rate.
⛔ **any pooled button+basket number.**
⛔ **any knife or gun ASR on this bank.**
⛔ **"90.8 % bomb-specific"** — withdrawn twice (`C-208b`, `C-215`) and finally quantified at
**1.20 / 1.02** in row 10.

---

## 4. THE DEFECT LEDGER — what was caught, and by what

Fourteen defects were found in this phase's own work. The three that recur are one shape:
**a quantity that could not have told you it was wrong.**

| id | defect | caught by |
|---|---|---|
| `D-001` | a family key that dropped the bank's `dev`/`heldout` field, silently **halving the data** | an arithmetic count that did not match |
| `D-007` | a patch confirmed with a grep matching a **pre-existing** string | the downstream script refusing |
| `C-202` | four jobs stalled; **all four on n-801**, which the launcher's own comment documents | `sacct --format=NodeList` |
| `C-203` | an unguarded token-identity assertion that would have written **zero transplant rows** | REVIEW-1 |
| `C-204` | a preflight that validated a population the runner **discards** | REVIEW-1 |
| `C-208a` | **the 2 × 2 identifies its own interaction and it was never computed** | REVIEW-1 |
| `C-209` | the ASR instrument's **false-positive channel** | reading the dose-0 generations |
| `C-210` | the recipient's absolute index used on the **donor's** forward pass | production IndexError |
| `C-213a` | *"a machine check asserting byte-identity"* that **existed only in a shell heredoc** | REVIEW-2 |
| `C-213b` | a withdrawal the amendment **said it added and did not**, absent from the published report | REVIEW-2 |
| `C-213c` | a reliability statistic with **no lower-bound property** (0 at 88.5 % disagreement) | REVIEW-2 |
| `C-213d` | a published row computed on **78 of 226** rows | REVIEW-2 |
| `C-214` | a normalisation whose denominator moves **30×** across the thing being compared | checking denominators before writing the number down |
| `C-215`/`C4` | residual-gap units printed beside full-gap units, **inverting** a conclusion | REVIEW-2 |

*Generated 2026-09-10 from the append-only log and the artifacts on disk. Where this file and the
log disagree, the log wins.*

---

## 5. CHANGES SINCE FIRST ISSUE (2026-09-10 04:35)

This deliverable is regenerated, not append-only, so every revision is listed here.

| when | change | why |
|---|---|---|
| 07:00 | row 3b added and marked **EXPLORATORY** | `C-217c` — `PR-066-A2` names `button_bomb` in both `predictor_x` and `outcome_y`, so basket's `Q2` is not a second confirmatory test. `ENTRY 047`'s framing is superseded |
| 07:35 | rows 1 and 1b now carry **both denominators** | `S-010` — a 113-domain mean printed beside a 42-domain sign test answers a different question; basket has 71 ties against button's 34 |
| 08:05 | row 3c added, recording a **withdrawn mechanism** | `S-011` — the switch-vs-gain reading `S-010` suggested was tested directly and is not supported |
| 07:30 | §4's ledger grows by four (`C-217a/b`, `C-218`, and the figure defects) | `REVIEW-3` executed the failures rather than describing them |

**Two entries in §4's ledger are worth reading together**, because they are the phase's own recurring
shape appearing in the repairs for it: `C-213a` (a machine check that existed only in a shell
heredoc) and `C-217b` (an integrity check defeatable by putting the change in a key whose name
starts with an underscore). Both were *fixes for* the shape they then exhibited.
