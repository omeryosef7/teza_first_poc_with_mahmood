# DCS / Bombness / semantic-installation — CLAIM STATE AUDIT

**Read-only document audit, 2026-09-15, at repo HEAD `0a8c7e6d`.** Purpose: an authoritative,
sourced registry of the current scientific claim state, so a new sprint does not accidentally
revive a withdrawn claim. Every row cites `file:line`. Quotes are exact. Where the record is
ambiguous the row says **AMBIGUOUS** and both entries are quoted. No scientific opinion of the
auditor is added; where a status is stated weakly in the source it is reproduced weakly here.

Abbreviation used below: `CONT` = `external_md/DCS_BOMBNESS_REPRESENTATION_TO_CAUSAL_ASR_CONTINUATION_20260910.md`
(the authoritative, append-only log, 11,891 lines). `TABLE` = `reports/DCS_CONT_CLAIM_TABLE.md`
(195 lines). `SUCC` = `external_md/DCS_BOMBNESS_MECHANISM_AND_ASR_SUCCESSOR_PLAN_AND_PROGRESS_20260909.md`.
`TS` = `external_md/DCS_THESIS_SCALE_BOMBNESS_CAUSAL_CONFIRMATION_PLAN_AND_PROGRESS_20260906.md`.
`MANDATE` = `external_md/DCS_THESIS_SCALE_MANDATE_20260906.md`.
`REG` = `configs/dcs_cont_candidate_registry.json`. `PROP` = `reports/DCS_CONT_CAUSAL_TEST_PROPOSAL.md`.

---

## 1. Method

**Greps run (all case-sensitive unless noted), over the six text sources:**

| grep | scope | hits used |
|---|---|---|
| `WITHDRAWN\|VOID\|CANNOT ANSWER\|CORRECTION\|SUPERSEDED\|RETRACT\|must not say\|do not say\|no longer` | `CONT` | 33 lines, all read in context |
| same pattern | `SUCC`, `TS`, `MANDATE` | 23 / 47 / 11 lines; read selectively (prior-phase carry-over) |
| `^### ` (entry headers) | `CONT` | 172 `CONT-ENTRY` headers enumerated; last is `CONT-ENTRY 172` at `CONT:11863` |
| `^\*\*C-CONT-[0-9]+` and `C-CONT-(09[0-9]\|10[0-9])` | `CONT` | 62 numbered own-work defect headers located |
| `DR-0[0-9]{2}[a-z]?` | `CONT` | 8 distinct ids: `DR-069`(2) `DR-070`(49) `DR-071`(26) `DR-072`(37) `DR-073`(3) `DR-073a`(5) `DR-074`(14) `DR-075`(33) |
| `CR-0[0-9]+` | `CONT` | 1 distinct id, `CR-002`, 60 occurrences |
| `PR-[0-9]+` | all `external_md` | prior-phase ids (`PR-001`…`PR-068`) live in `SUCC`/`TS`, **not** in `CONT` except as back-references |
| `off-by-one\|denominator\|leak\|latest_dir\|nondetermin\|comma\|--export\|matcher\|floor\|ceiling\|silently\|judge flip\|0\.137\|position mismatch\|token identity\|py_compile` | `CONT` | ~90 lines; used for §5 |

**Ordering rule applied:** later entries override earlier ones. For each claim the cited line is
the **last** entry in `CONT` (or in `TABLE`, which was revised after `REVIEW-9`) that set the status.

**Coverage caveats.**
1. `CONT` is append-only and ~11.9k lines; this audit read roughly 1,600 lines in full (every
   entry flagged by the greps plus entries 147–172 end-to-end) and relied on grep for the rest.
   A claim never touched by any of the grep patterns above could be missed.
2. `TABLE` is dated *"Revised 2026-09-12 after REVIEW-2 … REVIEW-8"* (`TABLE:2`) and therefore
   **predates** `CONT-ENTRY 147`–`172`. Where `TABLE` and a later `CONT` entry disagree, the
   `CONT` entry governs; `TABLE`'s A17 row was nonetheless updated to WITHDRAWN (`TABLE:32`).
3. Claim ids `B1`, `F2`, `F5`, `F6`, `F8`, `K1`, `Q1`, `S15` are **family/candidate/section** ids,
   not `A#` claim-table rows; they are registered in `REG` and in §14/§15 of the mandate. They are
   carried in the registry below with that distinction marked.
4. Prior-phase ids (`PR-0##`, `R-0##`, `C-1##`, `C-2##`, CLAIM A–E) belong to `SUCC`/`TS`, a
   **different bank generation** (`ts116` vs `ts116m`); they are summarised, not re-audited.
5. Per instruction, no jailbreak prompt text or model completion is quoted anywhere below; only
   counts, rates and intervals.

---

## 2. CLAIM REGISTRY

Statuses use the log's own vocabulary (`TS:28-29` defines CANNOT ANSWER and VOID; `CONT:1263-1267`
reproduces the list). **DEFENSIBLE** = the record states it as MEASURED/CONFIRMED with its
caveats attached; **EXPLORATORY** = the record explicitly labels it exploratory, train/validation,
or candidate.

| id | one-line statement | status | population | key statistic | LAST entry setting status |
|---|---|---|---|---|---|
| **A1** | Cutting the query codeword's row access to the demonstrations, in the retrieval band, removes ~31 % of concept-free semantic installation | **DEFENSIBLE** — *"MEASURED, REPLICATED CROSS-CODEWORD"* | train+val, 67 domains **each** codeword, button and basket **never pooled**; `ts116m`; `DR-071` | button −0.2150 CI [−0.235, −0.196], 67/67; basket −0.2435 CI [−0.273, −0.213], 67/67 | `CONT:5776` (`CONT-ENTRY 054`, basket replication) · `TABLE:16` |
| **A2** | The same cut does **not** change attack success | **DEFENSIBLE AS A NULL, BUT EXPLICITLY UNDERPOWERED** — *"NULL, REPLICATED CROSS-CODEWORD — but UNDERPOWERED in content-true units"* | 67 domains each; `slot0` PRIMARY scope; `DR-070` / `DR-073a` | button +0.0030 CI [−0.030, +0.036]; hardware-matched button −0.0075 [−0.0597, +0.0448]; basket −0.0090, p=0.40. CI half-width ~0.029 vs CR-002 ASR-arm base rate **0.0343** | `CONT:9588` (`CONT-ENTRY 121`) · status text `TABLE:17` |
| **A2b** | The cut rewrites the text; the endpoint cannot see it | **DEFENSIBLE (MEASURED)** | 670 rows, one codeword | `ko` differs from `base` on 669/670 completions, difflib 0.391; +8.5 pp [+4.3,+12.8] literal-codeword essays, −3.1 pp disclaimers, 7 of 8 shared refusals removed | `TABLE:18` (`REVIEW-3/OUTPUT`, `CONT-ENTRY 085`) |
| **A3** | Semantic installation and behavioural attack success are dissociable under intervention | **EXPLORATORY, QUALITATIVE ONLY. The quantitative version is WITHDRAWN TWICE** | 67 domains × 2 codewords | button gap +0.0221 → **−0.0044, P=0.59** on `slot0`; basket **+0.0116, P=0.29 NOT SUPPORTED** | `CONT:9440` (`DR-074` verdict) · `CONT:9343` (`C-CONT-083`) · `TABLE:19` |
| **A4** | The same cut cuts refusal to ~a third, band-specific | **DEFENSIBLE (MEASURED, REPLICATED ON MATCHED HARDWARE)** | 670 rows / 67 domains; `slot0` PRIMARY | ko 0.0403 vs ctrl 0.1119, diff −0.0716 [−0.0940, −0.0507]; exact sign test **p = 0.0078** (8−/0+/59 tied) | `CONT:10502` (`C-CONT-093` corrects the published 2.33e−10 to 0.0078) · `TABLE:20` |
| **A5** | Installation predicts attack success within domain, topic held fixed | **DEFENSIBLE (MEASURED)** | 670 slots / 67 domains | slope +0.140, perm p = 0.0006 | `TABLE:21` (`CONT-ENTRY 050 §1`) |
| **A6** | The observational installation→ASR link survives regeneration on different hardware | **DEFENSIBLE, but relabelled** — *"ROBUST TO GENERATION CHURN (not 'replicated')"* | 67 domains | corrected ρ 0.5312 vs 0.5260; prompts byte-identical 670/670 yet **573/670 completions differ** (V100 vs L40S) | `CONT:6868` (`CONT-ENTRY 070`) · `CONT:7073` (A6 relabelled) · `TABLE:22` |
| **A7** | StrongREJECT scores literal-codeword essays as jailbreaks | **DEFENSIBLE (MEASURED, VERIFIED BY INSPECTION)** | 670 rows | 131/131 button removals correct, 27/27 basket | `TABLE:23` |
| **A7b** | The correction is **not** valid in both directions; its failure rate is codeword-dependent by 4× | **DEFENSIBLE, NARROWED — every corrected number is an UPPER BOUND** | 40 blind + 100 + 91 hand-labelled | spurious among kept positives: button **0.717 [0.448, 0.866]**; basket **0.177 [0.100, 0.433]** | `TABLE:24` (`C-CONT-038`) |
| **A7c** | ~~A conservative rule brackets basket and has no analogue on button~~ | **SUPERSEDED** by `CR-002` | census of **all 129** CR-002 keeps on six arms | basket 48/48 = 1.000; button 78/81 = 0.963; pooled 126/129 = 0.977; blind relabel 98/100, κ = 0.953 | `TABLE:25` (`CONT-ENTRY 098`, `106`) |
| **A7d** | ~~The codeword-dependence is not a vocabulary problem~~ | **WITHDRAWN** → replaced by a **CANDIDATE, NEEDS OUT-OF-SAMPLE** | 40 labels | `MATERIAL ∧ ¬scope` precision 1.000 on both, but button rests on **4 tp, Wilson lower ≈ 0.51**, regex written after reading the rows | `CONT:8427` (`CONT-ENTRY 097`, `C-CONT-068`) · `TABLE:26` |
| **A8** | The transplant instrument **can** transfer, token-matched | **DEFENSIBLE (MEASURED), narrow** | 16 domains, pre-declared stratum | +10.7 %, CI [+3.5, +19.5], p = 0.010; sign test alone 11/16 p=0.21; all-families +4.1 % CI touching zero | `TABLE:33` · `REG` `instrument_status` |
| **A9** | Raw LLM-judge ASR overstates content-true attack success by close to an order of magnitude on codeword-remapping attacks | **DEFENSIBLE — the phase's strongest result** (`TABLE:44-52`) | 60,478 rows / **114 runs**; 129 keeps labelled | button raw 0.2984 → CR-002 0.0250 = **11.9× [9.6×, 15.6×]** domain-clustered; **≈8.1×** design-weighted; basket **6.6× [5.1×, 9.5×]**; 7.80× at SR≥0.75 | `CONT:8538` (`CONT-ENTRY 099`), `CONT-ENTRY 105`/`106` · `TABLE:34` |
| **A10** | Greedy decoding is not byte-reproducible across GPU architectures; that sets a noise floor under every ASR contrast | **DEFENSIBLE (MEASURED)** | 670 prompts / 67 domains | V100 vs L40S same condition: raw Δ +0.0149 [−0.018,+0.048]; corrected Δ +0.0015 [−0.015,+0.019]. `DR-070` primary (+0.0030) sits **inside** it | `CONT:6868` (`C-CONT-052`) · `TABLE:35` |
| **A11 / `F5`** | A ridge probe on the demonstration-side state predicts installation within domain | **DEFENSIBLE — CONFIRMED ON TEST**, but *"it **cannot mediate A1**"* | 900 fit / 230 TEST slots, 23 TEST domains; `DR-072`, single read | TRAIN +0.6241 → VAL +0.6784 → **TEST +0.6054 [+0.528, +0.678]**, 23/23 domains, p=0.00050 | `CONT:7147` (`CONT-ENTRY 075`) · caveat `CONT:6483` (`C-CONT-040`) · `TABLE:36` |
| **A12** | The doublespeak remap is strongly concept-dependent: `bomb` installs far more readily than `knife` or `gun`, on both codewords | **DEFENSIBLE (MEASURED, DOMAIN-PAIRED, exact test committed)** | 1080 shared slots / 90 domains, train+val, TEST excluded | button bomb−knife +0.4314 [+0.386,+0.475] 89/90; bomb−gun +0.5166 87/90; basket +0.3612 88/90, +0.3346 88/90; exact sign p = 1.5e−25 / 2.0e−22 / 6.6e−24 / 6.6e−24. ⚠️ knife/gun ordering **reverses** between codewords | `CONT:11373` (`CONT-ENTRY 157`), re-verified `CONT:11431` (`CONT-ENTRY 159`) · `TABLE:27` |
| **A13 / §15** | Cell C's demonstration-side state aligns with the explicit-BOMB state as installation rises | **EXPLORATORY, NARROWED — contrast-dependent, and the matched pairing does no work** | 900 slots / 90 domains each codeword | matched single reference +0.1598 / +0.1703, p=0.0005 both; **mismatched same-domain partner +0.4222 [+0.3879,+0.4510]**, beats matched in 98 % of 200 draws; knife +0.0623 **not significant** (p=0.0845), −0.0171 under the fair contrast | `TABLE:28` (`C-CONT-059`, `C-CONT-062`; `CONT:7660`, `CONT:7733`) |
| **A14** | Installation is delivered almost entirely by the first four demonstrations; the knockout removes about a quarter of the total | **DEFENSIBLE (MEASURED)** | 90 domains (ladder), 67 (share); matched-`slot0` | dose 0 ≈ 0 → dose 4 **+0.6728 [+0.610,+0.734]** 90/90 → dose 8 **+0.0632 [+0.029,+0.099]** 60/90; knockout share of the 0→8 span **25.4 % [20.8, 30.3]**; cross-run offset −0.0002 [−0.0025,+0.0020] | `CONT:8200` (`CONT-ENTRY 093`), `CONT-ENTRY 100`, `CONT:9142` (`CONT-ENTRY 112`) · `TABLE:29` |
| **A15** | The cut removes refusals and never adds them; what replaces them is mostly not an attack | **DEFENSIBLE for STRUCTURE; QUANTITIES ARE ALL-SLOTS (declared SECONDARY) ONLY** | 1340 paired prompts, two codewords, matched hardware | ko's refusal set is a strict **subset** of ctrl's: 27 ⊂ 75 (button), 1 ⊂ 8 (basket), **0 reversals**; de-refused 48/7, leak 10.4 %, domain-clustered CI [0.024, 0.192] over 33 domains. On the **primary** only 9 and 1 de-refusals, 0 content-true — *"too few events to analyse"* | `CONT:10623` (`CONT-ENTRY 141`, interval fixed to the DOMAIN unit) · `TABLE:30` |
| **A16** | ~~Installation gates REFUSAL, not capability~~ | ⛔ **WITHDRAWN** | — | *"no number from this row may be quoted"* | `CONT:10424` (`CONT-ENTRY 138`, `C-CONT-092`); re-affirmed `CONT:10616` · `TABLE:31` |
| **A17** | ~~The one-switch rival is excluded on both codewords~~ | ⛔ **WITHDRAWN** | — | *"no number from this row may be quoted"*; discriminating ratio measured **1.000 [0.630,1.625]** and **1.059 [0.583,1.900]** — *"**Undecided**, and honestly so"* | `CONT:10894` (`CONT-ENTRY 147`, `C-CONT-096`) · `TABLE:32` |
| **`K1`** (candidate `K1_interaction_at_demo_codewords_L13_14`) | ~~A BOMB-representation candidate at the demonstration codewords, L13–14~~ | ⛔ **WITHDRAWN** — *"Not a candidate."* | 67 TRAIN domains, button `ts116m` `dcd92d723f3e6d00` | K1 +0.6972 vs **contrast-free raw state +0.7504** at K1's own site; `mean4` +0.7005 also beats it | `CONT:3839` / `CONT:3863` (`CONT-ENTRY 024`, `C-CONT-013`) · `REG` candidate status field |
| **`Q1` / `F8`** (`Q1_query_side_probe_rel6`) | A query-side (rel-6) ridge probe predicts installation, and is the one site the A1 knockout edits | **EXPLORATORY — *"not a finalist"***; differs-across-arms and installation-axis specificity **ESTABLISHED observationally**; §44 #10 not yet declared | VALIDATION, 90 domains, both codewords, never pooled | VAL ρ +0.645 / +0.653 vs F5 +0.678 / +0.681; collinearity with F5 **0.696 / 0.740**; VAL increment over F5 **+0.041 / +0.023** (REVIEW-10: *"WITHIN NOISE at N=23"*) | `CONT:11165` (`CONT-ENTRY 152`), `CONT:11668` (`CONT-ENTRY 166`) · `REG` `Q1_query_side_probe_rel6.status` |
| **`F1`** raw state | the contrast-free null model | **the floor (0.546)** — *"F1 (raw-state) is the floor"* | TRAIN/VAL, both codewords | 0.546 | `CONT:11278` (`CONT-ENTRY 154`) |
| **`F2`** diff-in-means / interaction | a supervised direction predicts installation | ⛔ **NEGATIVE — *"F2 closes fully negative."*** | TRAIN LOO, `cw_demo_mean` L24, both codewords | `v_hi_lo` +0.544/+0.538 (at the floor); `v_resid` +0.182/−0.166 **sign-inconsistent**; `v_int` −0.158/−0.139 | `CONT:11271` (`CONT-ENTRY 154`) |
| **`F3`** pooled · **`F4`** trajectory · **`F7`** logit-lens | alternative representation families | **NEGATIVE — *"all fail to beat it [F5]"*** | TRAIN-select / VAL-transfer, both codewords | ≤ raw-state floor | `CONT:11278-11280` (`CONT-ENTRY 154`) |
| **`F6`** low-rank (PLS) | a low-rank subspace predicts installation better than rank-1 | ⛔ **EXPLORATORY-NEGATIVE — *"Family F6 closes as EXPLORATORY-NEGATIVE."*** | TRAIN-select rank, VALIDATION transfer, both codewords | best F6 VAL 0.659 vs F5 0.678 (button); 0.659 vs 0.681 (basket) | `CONT:11242` (`CONT-ENTRY 153`) |
| **`F6` rank-1 claim** | ~~the low-rank structure is one-dimensional~~ | ⛔ **WITHDRAWN** — artifact of a missing PLS deflation | — | corrected, rises to rank 4 | `CONT:6558` / `CONT:6766` (`C-CONT-043`) · `TABLE:52`, `TABLE:70` |
| **`CR-002`** (content rule v2) | A frozen content-true endpoint validates out of sample on both codewords | **DEFENSIBLE, bounding not estimating** | 24 fresh rows (12/codeword) + census of 129 keeps | precision **1.000 [0.76,1.00]**, 0 false positives; recall 0.92 / 0.80; design-weighted recall ≈ 0.71 | `CONT:8485` (`CONT-ENTRY 098`) · `TABLE:132` |
| **`DR-070`** | preregistered intervened-ASR primary | **NULL, all declared CANNOT ANSWER conditions evaluated and satisfied** | 670 rows, both arms `DONE` | +0.0030 [−0.030, +0.036] | `CONT:5460` (*"Every declared CANNOT ANSWER"* condition), `CONT:5104` |
| **`DR-071`** | preregistered installation manipulation check | **PASSES DECISIVELY** | 67 domains ×2 | see A1 | `CONT:5458` |
| **`DR-072`** | preregistered TEST confirmation of F5 | **CONFIRMED ON TEST; single read spent** — but *"two declared controls were run **after** the TEST read"* (`C-CONT-060`) | 230 TEST slots / 23 TEST domains | +0.6054 [+0.528,+0.678] | `CONT:7147`; defect `CONT:7699`; controls discharged `CONT:7801` |
| **`DR-073a`** | basket ASR primary (supersedes `DR-073`) | **NULL; sign not established** | 67 basket domains | −0.0090, p = 0.40; sign bracket **[−0.0090, +0.0030]** across three content rules | `TABLE:17`, `TABLE:78` (`C-CONT-063`) |
| **`DR-074`** | basket proportionality/dissociation test | ⛔ **NOT SUPPORTED** under its own frozen rule | basket, `slot0` primary | gap +0.0116, P = 0.29 | `CONT:9440` (`CONT-ENTRY 117`) |
| **`DR-075`** | A16's forward falsification test (refusal vs demonstration count) | **AMBIGUOUS — see §4/§6.** *"`DR-075` is simultaneously SUPPORTED under the rule as frozen and FAILING the honest form of the same comparison."* Narrow survivor: *"refusal is not a **linear** demonstration counter"* | 180/180/186 rows at dose 0/4/8, 90 domains | Δ +0.027778 (10↑/5↓/75 tied); non-inferiority upper bound +0.0630 vs margin +0.0555, **p = 0.098 → FAILS**; under true Δ=0 the frozen rule returns SUPPORTED **83 %** of the time | `CONT:10604-10614` (`CONT-ENTRY 141`); frozen-config TEST defect `CONT:10523` |
| **Patch test / §44 #10** (button) | The clean query-side rescue recovers ~42 % of the knockout's de-refusal | **EXPLORATORY — explicitly *"NOT yet a §44 #10 PASS"*** | 180 slot0 / non-TEST / non-excluded rows across 90 domains, button only, `ts116m`, L20 | CTRL 0.1111 / KO 0.0444 / RESCUE 0.0722; KO de-refusal +0.0667 [0.0333,0.1000]; recovery +0.0278 [0.0056,0.0556]; recovery fraction **0.417 [0.133,0.714]** | `CONT:11826` (`CONT-ENTRY 171`) |
| **Patch size-match control** (button) | Recovery is dose-dependent in query positions, not a fixed injection artifact | **EXPLORATORY — passes the pre-declared clause** | same 180 rows, K=12 of a 24-token query span | size-match 0.0611, +0.0167 [0.0000, 0.0389]; full−sizematch +0.0111 [0.0000, 0.0278] *"CI touching 0 — suggestive of monotonicity, not decisive at this n"* | `CONT:11863` (`CONT-ENTRY 172`) |
| **Inherited Q2** | ~~"confirmed"~~ | ⛔ **not split-replicated** | validation | ρ = 0.143, p = 0.51 | `TABLE:82` (`CONT-ENTRY 003`) |
| **Inherited `C-208`** negative harm main effect | — | **button-only** | — | basket H p = 0.33 | `TABLE:83` |

---

## 3. EXPLICITLY WITHDRAWN OR FORBIDDEN — must not be revived

### 3a. Withdrawn claims (each with the sentence that withdrew it)

| claim | the withdrawing sentence (exact) | file:line |
|---|---|---|
| **`K1`** — the phase's only BOMB-representation candidate | *"**`K1` is withdrawn.** The registry now records it as `WITHDRAWN`, with the reason, and `candidates` is effectively empty again."* | `CONT:3863` |
| `K1`'s **positional dissociation** (`cw_query` fails, demo codewords clear) | *"⛔ **not a dissociation about information.** Contrast-free, `cw_query` reads **0.665**"* | `CONT:3870-3871` |
| `K1`'s **`N_random` "PASSED decisively"** | *"⛔ the random pool's raw state reads **0.664**. The pool is not an uninformative site"* | `CONT:3873` |
| **`C-CONT-037`** — a bare-word-`bomb` false-negative channel in the lexicon | *"**C-CONT-039 — `C-CONT-037` is WITHDRAWN. The bare-word-`bomb` false-negative channel does not exist, and the conclusion I drew from it was wrong.**"* | `CONT:6458-6459` |
| **"both error channels of the ASR instrument are codeword-dependent, in opposite directions"** | *"is **UNSUPPORTED and withdrawn**. Only the false-**positive** channel is shown to vary by codeword. This was the headline of that entry and it does not survive."* | `CONT:6475-6476` |
| **`C-CONT-068`** — the "energetic material" refutation, and with it *"the codeword-dependence is not a vocabulary problem"* | *"`C-CONT-068` is **WITHDRAWN IN FULL**."* and *"**And the conclusion I drew from it is withdrawn with it.**"* | `CONT:8448`, `CONT:8450` |
| **"no lower bound on button can exist"** (entries 090/092) | *"6. \"**no lower bound on button**\" — a candidate now exists."* | `CONT:8463` |
| **`C-CONT-083`** — the quantitative dissociation (button) | *"**The quantitative dissociation is withdrawn.**"* | `CONT:9359` |
| **"the basket route is closed"** | *"**C-CONT-084 — and entry 113's \"the basket route is closed\" is false.**"* | `CONT:9380` |
| **A16** — "installation gates refusal, not capability" | *"A16 is withdrawn in the claim table with all three defects recorded. `C-CONT-092` entered in the ledger. **No number from that row may be quoted.**"* | `CONT:10491-10492` |
| **A17** — the one-switch exclusion, incl. "content-true, if anything, goes up" | *"**The entire excess was mechanical.** \"Content-true, if anything, goes up\" is withdrawn."* | `CONT:10919` |
| **A17's "strongest cross-codeword agreement"** | *"It was two confounds summing to the same number twice."* | `CONT:10926` |
| **CONT-164's "causally-relevant / OOD-answered" framing** (query-side) | *"So \"first CAUSALLY-RELEVANT representation\" and \"reduces the installation-coded component\" (CONT-162/163/164) are **retracted**"* | `CONT:11650-11651` |
| **CONT-164's OOD check as an answer to the energy rival** | *"CONT-164's \"the concern that most threatened the result is answered\" is **withdrawn** — that check cannot discriminate signal from the scale artifact."* | `CONT:11643-11644` |
| **`C-CONT-012`** — "the instrument is not validated" | *"⛔ **WITHDRAWN** (`C-CONT-012`)"*; *"rested on `E→A`, structurally incapable of showing transfer"* | `CONT:3697`, `TABLE:64` |
| **`S-003c`** (prior phase) — "a non-trivial part of `B1_benref`'s magnitude is the incongruity/context component" | *"⛔ **`S-003c` (entry 016) is SUPERSEDED.** … The correct statement is **all of it, and more.**"* | `SUCC:3068-3069` |
| **`C-208b`** (prior phase) — "90.8 % bomb-specific" | *"**WITHDRAWN.** … is arithmetically true and **is not evidence of concept specificity**. It is withdrawn as such."* | `SUCC:3083`, `SUCC:3101-3102` |
| **`C-208c`** (prior phase) — entry 011's Link-3 sentence | *"is **SUPERSEDED** by entry 020"* | `SUCC:3104` |
| **`C-208d`** (prior phase) — "the direct harmful baseline is 0.88 %" | *"is **WITHDRAWN** … All ten of cell B's \"successes\" are in one domain"* | `SUCC:3112`, `SUCC:3123` |
| **`PR-050`** (prior phase) | *"**`PR-050` is WITHDRAWN, not amended.** Its central premise is false (`C-100`)"* | `TS:2458` |
| **`R-101`'s "19/19 PASS"** (prior phase) | *"the G1 gate was itself blind. `R-101`'s \"19/19 PASS\" is RETRACTED."* | `TS:1442` |

### 3b. Forbidden sentences — the "WHAT WE MUST NOT SAY" list

`TABLE:38-57` is the canonical list; each row below is quoted exactly with its stated reason.

| ⛔ forbidden sentence | reason as written | file:line |
|---|---|---|
| *"the pathway **is** the behaviour"* | *"A1/A2 are **necessity** interventions; a null licenses only \"not required\""* | `TABLE:42` |
| *"we found a BOMB representation"* | *"**`K1` is WITHDRAWN** (`C-CONT-013`); the registry has **no candidate**"* | `TABLE:43`; restated `CONT:5653-5654` |
| *"installation causally drives ASR"* | *"A3 is **qualitative only**; the quantitative version was **downgraded** (`C-CONT-032`)"* | `TABLE:44` |
| *"the transplant result is replicated"* | *"it is a **numerical re-execution** of a deterministic computation (`C-CONT-026`)"* | `TABLE:45` |
| *"a localized state was transplanted"* | *"+10.7 % is the **all-layer** window; the best localized window is 8 % (`C-CONT-027`)"* | `TABLE:46` |
| any ASR number **bare** | *"the floor and the **0.137** judge flip rate must travel with it — and the floor is **codeword-specific**: 0.155 `button`, 0.022 `basket`"* | `TABLE:47`; also `CONT:4165`, `CONT:5172` |
| any **corrected** ASR number as an *estimate* | *"it is an **UPPER BOUND** — `C-CONT-038`"* | `TABLE:48` |
| *"greedy decoding reproduces byte-identically"* | *"true **only within a GPU architecture**; across V100→L40S, 573/670 completions differ on identical prompts (`C-CONT-052`)"* | `TABLE:49` |
| *"the basket null is tighter, so stronger"* | *"its base rate is ~3× smaller; in **relative** terms the two intervals are comparable"* | `TABLE:50` |
| *"A11/`F5` is the mechanism"* | *"its input is **bit-identical** across `ko`/`ctrl` (`C-CONT-040`)"* | `TABLE:51`; source `CONT:6496` |
| *"the low-rank structure is one-dimensional"* | *"an artifact of a **missing PLS deflation**; corrected, it rises to rank 4"* | `TABLE:52` |
| any **button** content-true number | *"the published `HARD` rule is precision 0.50 there; a **candidate** lower bound exists … but is **post-hoc and unvalidated**"* | `TABLE:53` |
| *"the basket cut reduced attack success"* | *"the **sign is not established**; it flips across three content rules (`C-CONT-063`)"* | `TABLE:54` |
| the §15 result as a **matched**-reference finding | *"a mismatched partner scores **higher**; the matching does no work (`C-CONT-062`)"* | `TABLE:55` |
| *"conduit, not store"* as established | *"the instrument was validated only **after** two structurally invalid controls"* | `TABLE:56` |
| *"cross-codeword transfer **of a representation**"* | *"basket **does not clear** its own ceiling (0.628 vs 0.693)"* — but the *intervention* effect (A1) **does** replicate | `TABLE:57`; amendment at `CONT:5816-5825` |
| *"First to causally intervene on demo→query attention in ICL"* | *"is FALSE and **must never be written** — killed twice, most recently by arXiv 2504.00132"* | `TS:324-325` |
| *"decodable but not causally used"* (the mandate's own phrase) | *"no intervention exists to license it"* — banned for present use | `SUCC:3194-3196` |
| *"nothing else had touched TEST"* | *"the earlier claim that *nothing else had touched TEST* was false and is retracted here"* | `TABLE:7` (`C-CONT-094`; source `CONT:10516`) |

---

## 4. CANNOT ANSWER (the design could not test) — **distinct from a negative**

Definition in force: *"the design could not have answered the question either way — underpowered,
degenerate instrument, or the read site could not physically see the intervention. **This is not a
null.**"* (`TS:28`). Also *"If an instrument cannot physically answer the question, CANNOT ANSWER is
not a negative."* (`SUCC:1517`).

| item | why it cannot be answered (exact) | file:line |
|---|---|---|
| **The linking test** (installation loss → refusal loss, domain level) on `ts116m` | *"the existing `ts116m` bank **cannot** power it — not at the 67 knockout domains, and not even at the full 90 usable domains, because the MDE there (0.292) is still larger than the effect (0.176). This is not \"underpowered, tighten it later\"; it is \"un-answerable on this bank at any subset.\""* Power as run = **0.296**; 252 domains needed. | `CONT:11097-11100` |
| earlier form of the same test | *"This is a null that does not distinguish *\"installation loss and refusal loss are independent consequences of the same cut\"* from *\"they are linked, modestly, and 67 domains cannot show it\"*."* | `CONT:9764-9766` |
| **A2 / A3 in content-true units** | *"the MDE **exceeds the entire genuine attack rate**"* (CR-002 button ASR-arm base rate 0.0343 vs CI half-width ~0.029) | `TABLE:17`, `TABLE:131` |
| **The one-switch / threshold rival (post-A17)** | *"Measured: **1.000** and **1.059**, intervals spanning 0.58–1.9. **Undecided**, and honestly so. Breaking the tie needs a new measurement — a blind human rating … not another pass over these artifacts."* | `CONT:10957-10960` |
| **A15 on the declared primary** | *"On the declared **primary** there are **9 and 1** de-refusals and **0** content-true on button — too few events to analyse."* | `TABLE:30`; see also `CONT:9947` |
| **The query-side negative close, if it comes** | *"below it, \"no causal component\" is **indistinguishable from underpowered**, and the negative close must be stated as \"no effect detectable above MDE 0.337\", not \"no effect\"."* | `PROP:73-75` |
| **A15 basket leak rate replication** | *"**The 10 % leak rate does not replicate — and cannot, at this n.**"* … *"the data do not separate 10 % from 29 %"* | `CONT:9710`, `CONT:9723` |
| **Within-domain demonstration-side patch** | *"⛔ **not constructible**: 0 of 4050 within-domain pairs share demo codeword positions"* | `TABLE:135` (`CONT-ENTRY 076`) |
| **§15's harmful non-BOMB reference** | *"`gun` cannot serve (does not install); `knife` shows **no excess** under the fair contrast. Needs a concept that installs — this bank family has none"* | `TABLE:134` |
| **LLM-as-judge over the blind rating sheet** | *"an LLM judge cannot substitute for the human rater from a session (or a Claude subagent) that has the sheet content in scope"* — all three routes (Claude subagent panel, OpenAI, Gemini) blocked by the safety classifier | `CONT:11763` (`CONT-ENTRY 169(a)`, header `CONT:11751`) |
| **PHASE 13** (prior phase) | *"A correlation against a constant is **undefined, not underpowered** — which is a much stronger statement than \"we lack power\", and it cannot be fixed with more domains."* | `TS:4762-4763` |
| **PHASE 10 primary concept-free readout** (prior phase) | *"**A two-option forced choice cannot capture a categorical answer whichever two words are chosen.** So PHASE 10's primary concept-free readout is **CANNOT ANSWER on measured grounds**"* | `TS:5052-5054` |
| **PHASE 11 primary contrast** (prior phase) | *"The previous PHASE-11 primary contrast became CANNOT ANSWER because the intended dose-matched control was arithmetically impossible."* | `SUCC:740`; also `TS:4938` |
| **Gate R6, §13, PHASE 7 / R8** (prior phase) | *"Gate R6 CANNOT ANSWER. §13 CANNOT ANSWER. … PHASE 7 / R8 CANNOT ANSWER for two independent reasons … ρ=+0.60 is **not citable in either direction**."* | `TS:318-322` |
| **`basket_bomb` option-mass closure** (prior phase) | *"⛔ `basket_bomb`'s closure is **CANNOT ANSWER, not a null**, and may never be reported as one."* | `SUCC:3197-3198` |
| **Q2 on that bank** (prior phase) | *"Q2 is CANNOT ANSWER for lack of outcome variance"* | `SUCC:2060` |

**AMBIGUOUS — `DR-075`.** Both entries stand in the record and neither is deleted:

> *"**DR-075: SUPPORTED.** Refusal does not track demonstration count"* — `CONT:10334`

> *"So `DR-075` is *simultaneously* SUPPORTED under the rule as frozen and FAILING the honest form of
> the same comparison. … **Under a true Δ = 0 the frozen rule returns SUPPORTED 83 % of the time.**"*
> — `CONT:10610-10611`, `CONT:10534-10535`

The narrow survivor is stated as: *"**refusal is not a *linear* demonstration counter** — the design
has ~99 % power against that specific rival, and against nothing broader."* (`CONT:10613-10614`).

**AMBIGUOUS — the installation↔refusal dose link (ρ = +0.2376, button).** Entered as supported, then
undercut but never formally withdrawn:

> *"**On button the chain is supported**: the domains where demonstrations install the most are the
> domains where refusal rises the most."* — `CONT:10014-10015`

> *"The \"installation gain predicts refusal gain\" correlation is **identically** the correlation
> between installation and refusal *within the dose-4 arm*."* … *"ρ = 0.2376 is **below this design's
> own MDE** (≈0.29 at n = 90)"* — `CONT:10445-10446`, `CONT:10461-10462`

Basket does not replicate (ρ +0.0592, p = 0.699 on the primary; `CONT:10011`).

---

## 5. KNOWN BUG CLASSES AND INTEGRITY LESSONS

Each row is a failure mode the logs record as *recurring*, with a source line. The record's own
summary of the shape: *"**The recurring shape:** *a quantity that could not have told you it was
wrong* — and it appeared **inside the repair for itself** five times"* (`TABLE:119-121`).

| # | bug class | what happened (exact where short) | file:line |
|---|---|---|---|
| 1 | **Unstated slot scope (denominator/scope shopping)** | *"Four defects in this phase are the same defect (`C-CONT-072`, `083`, `088`, `089`): an inline `if 'slot0' in …`, or its absence, with the choice never written down."* Fix: `Scope.require()` raises; *"There is no default."* | `CONT:9989-9999` |
| 2 | **A headline p-value on the secondary scope, unlabelled** | primary 0.0078 vs secondary 2.33e−10 — *"**eight orders of magnitude** weaker … repeated *inside the entry that was fixing p-value defects*"* | `CONT:10502-10512` |
| 3 | **Mixed scopes inside one ratio** | *"the numerator −0.2082 is all-slots `ko − base`, the denominator +0.6719 is `slot0`"* | `CONT:9356` |
| 4 | **Wrong denominator / wrong numerator** | `C-CONT-070`: *"the 32 % used the wrong numerator. Corrected to 30.7 % [27.9, 33.7]"* | `CONT:8310` |
| 5 | **Wrong independence unit (row vs domain)** | A15's interval was *"a **row-level Wilson** on 5/48 where the declared independence unit is"* the domain | `CONT:10627` |
| 6 | **Sign-count denominators under a floor/ceiling** | *"The right denominator for a sign count is **the domains where the quantity can vary** — and where a floor or ceiling makes most units constant, a raw sign count reads as weak"* | `CONT:9866-9867` |
| 7 | **TEST split leakage into published populations** | *"`C-CONT-094` — TEST domains are inside two published populations."* and *"`DR-075`'s frozen config asserts `\"does_not_read_TEST\": true`. **That is false.**"* | `CONT:10516`, `CONT:10523` |
| 8 | **A population *label* that was never checked against the corpus** | *"`\"population\": \"train+val\"` **labels a train-only dataset**"*; *"a label is not a census"* | `CONT:10941`, `CONT:10968` |
| 9 | **Position / token index off-by-one and position mismatch** | the random draw *"is seeded on `prompt_id`, so it lands on **different positions in the two halves of the contrast** (positions equal in **0/930** pairs, versus 928/930 for every other site)"* | `CONT:3875-3877` |
| 10 | **Matcher / regex counted as a rate without reading rows** | *"The regex counted the **word**, and I read a count as a rate without reading the rows — the exact failure I had just caught in `C-CONT-036` and the same one as `C-CONT-034`."* | `CONT:6470-6471` |
| 11 | **Matcher scope: a clause that detects the wrong thing** | *"**CR-002's `SCOPE` clause is a disclaimer detector, and the knockout suppresses disclaimers**"* — vetoing 4 ctrl vs 1 ko (button), 3 vs 0 (basket) | `CONT:10903-10910` |
| 12 | **Wrong field name → silently empty / silently wrong** | *"a completion read from a field that does not exist → every row scored empty → a clean, plausible, **fabricated** 0.0000"*; *"**Twice now a wrong field name has produced a**"* number; four incidents total (`C-CONT-036/056/066/069`) | `TABLE:100`, `CONT:7260`, `CONT:8242` |
| 13 | **Key collision across arms** | *"`prompt_id` **repeats across the three arms**, so a `(codeword, prompt_id)` lookup silently scores the wrong arm's completion"* | `CONT:8432-8433` |
| 14 | **A corrupted/shuffled label column propagating through a whole cascade** | *"the published labels file had a **shuffled column**; 13 of 40 labels misaligned"* — six downstream items withdrawn | `TABLE:108`, `CONT:8372`, `CONT:8457-8463` |
| 15 | **Partial runs / `latest_dir`-style completeness failures** | *"a run reported **`ok` after losing 98 % of its rows**, and its gate **PASSED** on the remainder"*; *"the commit-time guard audited **536 of 1023** finished runs and announced \"every finished run\""* | `TABLE:97`, `CONT:6819` |
| 16 | **A requested-but-absent layer silently skipped** | *"**A requested-but-absent layer was silently skipped.**"* | `CONT:9121` |
| 17 | **Judge nondeterminism** | judge label flip rate **0.1372** (and 0.1556 on another arm) on byte-identical text; must travel with every ASR number | `CONT:1889`, `CONT:4165` |
| 18 | **ASR instrument false-positive floor, codeword-specific** | 0.155 on `button` vs 0.022 on `basket` | `CONT:4047`, `TABLE:47` |
| 19 | **Cross-GPU generation nondeterminism** | *"greedy decoding is NOT byte-reproducible across GPU architectures"*; 573/670 completions differ on identical prompts; readout offset only −0.0002 | `CONT:6868`, `CONT:6893` |
| 20 | **Letting the scheduler pick hardware for a job whose purpose was to fix a hardware confound** | *"`C-CONT-075` \| let the scheduler pick the hardware for a job whose purpose was to **fix a hardware confound**"* | `TABLE:117`, `CONT:8684` |
| 21 | **`sbatch --export` comma truncation** | *"`sbatch --export=ALL,DCS_CMD=\"… --layers 0,2,4,…\"` truncates at the first comma"* — the exported command became `python … --layers 0`. Fix: full command INLINE in the slurm script | `CONT:11497-11508` |
| 22 | **A p-value reported at its bootstrap resolution floor** | *"`p = 0.00005` is a bootstrap resolution floor throughout, not a"* measurement; *"The floor reported all three as identical. They differ by ten orders of magnitude."* | `CONT:9977`, `CONT:10155` |
| 23 | **A bootstrap that silently discards draws** | basket-PRIMARY intervals *"silently discarded **36 %** of their bootstrap draws through the zero-denominator guard"* | `CONT:10943-10944`, `CONT:10983` |
| 24 | **An unseeded resample reported to four decimals** | *"I reported resampling noise to four decimals from an unseeded run."* | `CONT:10600-10601` |
| 25 | **A declared CLI flag that was never read** | *"`--adjust-recall` … was declared, documented as printing a stratum table, and **never read** — passing it silently returned the unadjusted factor."*; also `--n-perm` *"declared and **never used**"* | `CONT:9393-9394`, `TABLE:93` |
| 26 | **"FROZEN" as an unpinned string** | *"\"FROZEN\" was an **unpinned string**; a modified copy printed FROZEN and stamped `config_id: DR-072`"* | `TABLE:103`, `CONT:6550` |
| 27 | **Missing null model — five controls against specific rivals, none against the generic one** | *"**I built five nuisance controls … and omitted the null model.** … the thing that was actually true was the most generic one available."* `N_contrastfree` is now mandatory and goes first | `CONT:3883-3890` |
| 28 | **Conditioning on a post-treatment variable (collider)** | *"Refusal is *caused by* the intervention, so conditioning on not-refused-in-that-arm is a collider"* | `CONT:10935-10936` |
| 29 | **A preregistered threshold set too loose to fail** | *"falsification required refusal above **0.1666**, which is **39 % above the highest button refusal ever recorded in this phase** (0.1195)."* | `CONT:10471-10473` |
| 30 | **Formalising a rival into the version your data can beat** | *"I formalised someone else's hypothesis into the version my data could beat, and did not notice I had done it."* | `CONT:10932-10933` |
| 31 | **Testing the confound you thought of and treating "insufficient" as "absent"** | *"**I tested the confound I thought of, found it insufficient, and treated \"insufficient\" as \"absent.\"**"* | `CONT:10953-10954` |
| 32 | **A synthesis written up as a claim without being tested as a hypothesis** | *"The numbers had each been checked; the *claim built across them* had not, and I wrote it up as a synthesis rather than testing it as a hypothesis."* | `CONT:10486-10488` |
| 33 | **A headline number with no committed script or artifact** | *"the headline ρ has **no committed script and no artifact**: I computed it in a shell and wrote the number into prose"* | `CONT:10466-10467` |
| 34 | **Asserting non-existence without opening the directory** | *"That is the **second time in three entries** I asserted non-existence without opening the directory"* | `CONT:9383-9384` |
| 35 | **Import/NameError invisible to `py_compile` and a self-test** | *"`random` was never imported. `py_compile` passed"*; repeated with `torch` (`C-CONT-050`) | `CONT:3154`, `CONT:6787` |
| 36 | **A guard that destroyed its own provenance** | *"the guard I shipped one entry ago silently destroyed half its own provenance"* — *"**This is the same lesson a third time in two days**"* | `CONT:10695`, `CONT:10702` |
| 37 | **A scale-invariant check used to rule out a scale artifact** | *"**the OOD rho check is scale-invariant**: within-domain-centred Spearman is unchanged by `h_ko=c·h_ctrl` … exactly what the artifact PREDICTS"* | `CONT:11641-11643` |
| 38 | **Dead symlink aborting every GPU job before the model loads** | *"`mkdir -p` on a symlink whose target does not exist reports \"File exists\" and, under `set -euo pipefail`, aborts the job BEFORE the model loads"* — earlier misdiagnosed as preemption | `CONT:11777-11779` (`CONT-ENTRY 169(b)`, header `CONT:11751`) |
| 39 | **Misdiagnosing a full disk quota as an infrastructure fault** | *"The \"NFS outage\" was my 200 GB quota, full."* / *"I spent several iterations calling the write failures a \"NetApp fault\""* | `CONT:11517`, `CONT:11519` |
| 40 | **An 11 GB cache OOM-killing the analysis on a shared node** | *"The 11 GB `multiposition_reps.pt` cache OOM-killed the"* analysis twice (`C-CONT-099`) | `CONT:11149` |

**What the record says actually caught these:** *"adversarial re-derivation, the commit-time
completeness guard, and persisted intervention dose"* — *"**procedures, not cleverness**"*
(`TABLE:121-122`, `CONT:5657-5658`).

---

## 6. OPEN THREADS at HEAD `0a8c7e6d`

Sourced from the last three log entries (`CONT-ENTRY 170`–`172`, `CONT:11789`, `CONT:11826`,
`CONT:11863`) plus the standing blocked lines.

### Running (launched, results not yet in the log)
| thread | detail | file:line |
|---|---|---|
| **Basket patch-test primary arms** | *"**Basket primary arms LAUNCHED** (full 180, `--requeue`): 895903 CTRL, 895904 KO, 895905 RESCUE_CLEAN (L18)."* | `CONT:11885-11887` |
| **Basket endpoint analysis + §44 #10 verdict** | *"When basket completes, run the endpoint analyzer on basket and weigh the §44 #10 verdict across both codewords"* | `CONT:11888` |

### Pending / owed before any §44 #10 PASS may be declared
| owed item | exact wording | file:line |
|---|---|---|
| cross-codeword replication | *"(2) **basket** has not replicated (the differ-arms signal only earned confidence by replicating cross-codeword, and button/basket are never pooled)"* | `CONT:11854-11855` |
| interventional norm/distribution rival | *"the remaining open item is the interventional norm-rival, controlled observationally in CONT-166 but not yet on the behavioural endpoint"* | `CONT:11890-11891` |
| small event counts | *"the CIs, while excluding 0, rest on few flips (~2.5 domains recovered) — replication is load-bearing"* | `CONT:11859` |
| secondary content endpoint | *"the secondary CR-002 content endpoint can be scored later in a clean session"* (the judge path is classifier-blocked) | `CONT:11816` |

### Blocked
| blocked line | blocker | file:line |
|---|---|---|
| **Blind human rating sheet** (the one measurement that can settle the open one-switch/A17 question) | *"blocked on a human rater"*; LLM-judge substitution blocked through all three routes; *"Treat a fresh session as required for further sheet-adjacent analysis."* | `CONT:11070-11071`, `CONT:11763`, `CONT:11769` |
| **Linking test (installation→refusal, domain level)** | bank-blocked: needs ~250–260 domains; *"un-answerable on this bank at any subset"* | `CONT:11097-11100` |
| **Within-domain demonstration-side patch** | *"⛔ not constructible"* on this bank; needs a position-matched bank | `TABLE:135` |
| **§15's harmful non-BOMB reference** | *"this bank family has none"* — needs a second concept that installs on both codewords | `TABLE:134` |
| **`git push`** | *"push blocked: the remote's embedded token is no longer accepted. Work continues locally; nothing is lost."* | `CONT:9017` |
| **Extending CR-002's validation / the labelled set** | *"precision 1.000 rests on 12 rows/codeword"*; *"40 is enough to reject a rule, not to certify one"* | `TABLE:129-130` |
| **Power on A2/A3 in content-true units** | *"The endpoint is defensible; it is not powerful"* — needs new rows + ~12 GPU-h | `TABLE:131` |

### Closed this session (no longer open)
* Phase-4 candidate sweep — *"The Phase-4 candidate sweep is now complete."* F5 sole positive, F1–F4/F6–F8 fail to beat it (`CONT:11273-11284`).
* The differ-across-arms observational line — replicated, adversarially reviewed, overclaim retracted, energy rival refuted (`CONT:11561`, `CONT:11628`, `CONT:11668`).
* A12's exact sign test (`C-CONT-093` / trap #8) — *"Counts reproduce exactly"* (`CONT:11373`), independently re-verified (`CONT:11431`).
* Identity smoke for the patch test — button 24/24 (`CONT:11789`) and basket at L18 24/24 (`CONT:11884-11885`).
* Button size-match control — passes the pre-declared clause (`CONT:11863`).

---

*Audit produced read-only. No source file was modified; no git command was run.*
