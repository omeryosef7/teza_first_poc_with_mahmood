# DCS continuation — CLAIM TABLE
**BOMB representation search → causal ASR.** 2026-09-10 / 09-11. **Revised 2026-09-11 after REVIEW-2** (eleven corrections, `C-CONT-038`…`C-CONT-054`).
Mandate: `external_md/DCS_BOMBNESS_REPRESENTATION_TO_CAUSAL_ASR_CONTINUATION_20260910.md`

⛔ **Everything here is TRAIN-only and EXPLORATORY.** No confirmation freeze has happened and the
frozen TEST split has not been read. `button` and `basket` are never pooled. The independence unit
is the **DOMAIN** throughout.

---

## A. WHAT WE CAN TELL MATAN AND MAHMOOD

| # | claim | status | n | statistic | source |
|---|---|---|---|---|---|
| **A1** | Cutting the query codeword's row access to the demonstrations, in the retrieval band, **removes ~31 % of concept-free semantic installation** | **MEASURED, REPLICATED CROSS-CODEWORD** | 67 domains each | **button** −0.2150, CI [−0.235, −0.196], **67/67**; **basket** −0.2435, CI [−0.273, −0.213], **67/67** (never pooled) | `CONT-ENTRY 049`, `054` · `DR-071` |
| **A2** | The **same cut does not change attack success** | **NULL, POWERED, REPLICATED CROSS-CODEWORD** | 67 domains each | **button** +0.0030, CI [−0.030, +0.036], MDE 0.053; **basket** −0.0090, CI [−0.0254, +0.0090], p=0.40, MDE 0.025 (never pooled) | `CONT-ENTRY 044` · `DR-070`; `CONT-ENTRY 071` · `DR-073a` |
| **A3** | ⇒ semantic installation and behavioural attack success are **dissociable under intervention** — qualitatively | **MEASURED, EXPLORATORY, NOW TWO-CODEWORD** | 67 domains × 2 codewords | A1 ∧ A2 on **both** button and basket. ⚠️ same scope and bands; **"same dose" is NOT true across the pair** — the installation and ASR arms use different query templates and persisted dose totals 346,329 vs 1,385,316 (`REVIEW-2/SCIENTIFIC 1.3a`) | `CONT-ENTRY 049 §2`, `071` |
| **A4** | The same cut **halves refusal**, and the effect is **band-specific** | **MEASURED** | 670 rows | refusal 0.115→0.040 (`ko`) vs 0.112 (`ctrl`, identical dose) | `CONT-ENTRY 044 §1` |
| **A5** | Installation predicts attack success **within domain**, topic held fixed | **MEASURED** | 670 slots / 67 domains | slope +0.140, perm p=0.0006 | `CONT-ENTRY 050 §1` |
| **A6** | The observational installation→ASR link **survives regeneration on different hardware** | **ROBUST TO GENERATION CHURN** (not "replicated" — see note) | 67 domains | corrected ρ 0.5312 vs 0.5260. The two runs share byte-identical prompts (`prompt_sha16` 670/670) yet **573/670 completions differ**, because one ran on a V100 and one on an L40S | `CONT-ENTRY 047 §1`, `070` |
| **A7** | StrongREJECT scores **literal-codeword essays** as jailbreaks | **MEASURED, VERIFIED BY INSPECTION** | 670 rows | 131/131 button removals correct, 27/27 basket removals correct | `CONT-ENTRY 038`, `039`, `060` |
| **A7b** | ⚠️ **The correction is NOT valid in both directions.** Its *kept* rows were never audited until `REVIEW-2`, and **63 of 100** sampled button kept-positives contain no bomb content (`casing` fires on *"plastic or metal casing for the button's back"* — 1303 rows) | **NARROWED — every corrected number is an UPPER BOUND** | 100 hand-labelled | Wilson 95 % [0.53, 0.72]; basket 11/22 spurious | `C-CONT-038` · `REVIEW-2/OUTPUT` |
| **A12** | 🆕 **The doublespeak remap is strongly concept-dependent** — it installs `bomb` ~12× more readily than `gun` | **MEASURED** | 1080 slots × 6 banks / 90 domains | mean `y_install`: bomb 0.5636 (button) / 0.3808 (basket); knife 0.1322 / 0.0196; gun 0.0470 / 0.0462 | `CONT-ENTRY 079` |
| **A13** | 🆕 §15's matched reference: cell C's demonstration-side state aligns with the **explicit-BOMB** state as installation rises, beating the matched context-only prototype | **MEASURED, REPLICATED CROSS-CODEWORD** | 900 slots / 90 domains each | button B−ctx **+0.4053**; basket **+0.3317**; both perm p=0.00050. ⚠️ §15's harmful non-BOMB control is **INCONCLUSIVE** — gun does not install | `CONT-ENTRY 077`, `078`, `079` |
| **A8** | The transplant instrument **can** transfer, token-matched | **MEASURED** | 16 domains | +10.7 %, CI [+3.5, +19.5], p=0.010 | `CONT-ENTRY 021`, `023` |
| **A9** | 🆕 **The ASR instrument's false-positive floor is codeword-dependent, and 111 prior judge runs are exposed** | **MEASURED** | 58,468 rows / 111 runs | `button` ASR 0.2984→0.1169, factor **2.55, CI [2.46, 2.66]** (design effect 24.9, run-clustered); `basket` 0.1172→0.0379. Split-clean: button train+val 0.3146→0.1243 | `CONT-ENTRY 063`, `066` · `C-CONT-048` |
| **A10** | 🆕 **Greedy decoding is not byte-reproducible across GPU architectures**, and that sets a noise floor under every ASR contrast | **MEASURED** | 670 prompts / 67 domains | same condition, V100 vs L40S: raw Δ +0.0149 CI [−0.018, +0.048], corrected Δ **+0.0015 CI [−0.015, +0.019]**. The `DR-070` primary (+0.0030) sits **inside** that band | `CONT-ENTRY 070` · `C-CONT-052` |
| **A11** | 🆕 A ridge probe on the demonstration-side state predicts installation **within domain** | **CONFIRMED ON TEST** — but it **cannot be a mechanism** (`C-CONT-040`) | 900 fit / 230 test slots | TRAIN +0.6241 → VALIDATION +0.6784 → **TEST +0.6054**, 23/23 domains, p=0.00050. Beats a size-matched demo-span control by **+0.3960** | `CONT-ENTRY 059`, `061`, `075` · `DR-072` |

## B. WHAT WE MUST NOT SAY

| ⛔ | why |
|---|---|
| "the pathway **is** the behaviour" | A1/A2 are **necessity** interventions; a null licenses only "not required" |
| "we found a BOMB representation" | **`K1` is WITHDRAWN** (`C-CONT-013`); the registry has **no candidate** |
| "installation causally drives ASR" | A3 is **qualitative only**; the quantitative version was **downgraded** (`C-CONT-032`) — the within-domain prediction (−0.030) sits *on* the measured CI bound |
| "the transplant result is replicated" | it is a **numerical re-execution** of a deterministic computation (`C-CONT-026`) |
| "a localized state was transplanted" | +10.7 % is the **all-layer** window; the best localized window is 8 % (`C-CONT-027`) |
| any ASR number bare | the floor and the **0.137** judge flip rate must travel with it — and the floor is **codeword-specific**: 0.155 `button`, 0.022 `basket` |
| any **corrected** ASR number as an *estimate* | it is an **UPPER BOUND** — `C-CONT-038`, 63/100 kept positives spurious on button, 11/22 on basket |
| "greedy decoding reproduces byte-identically" | true **only within a GPU architecture**; across V100→L40S, 573/670 completions differ on identical prompts (`C-CONT-052`) |
| "the basket null is tighter, so stronger" | its base rate is ~3× smaller; in **relative** terms the two intervals are comparable (`DR-073a` froze this caveat in advance) |
| "A11/`F5` is the mechanism" | `F5`'s site is causally **upstream** of the only intervention this phase owns — its input is **bit-identical** across `ko`/`ctrl` (`C-CONT-040`) |
| "the low-rank structure is one-dimensional" | an artifact of a **missing PLS deflation**; corrected, it rises to rank 4 (`C-CONT-043`) |
| "conduit, not store" as established | the instrument was validated only **after** two structurally invalid controls (`C-CONT-019`, `C-CONT-010`) |
| "cross-codeword transfer **of a representation**" | basket **does not clear** its own ceiling (0.628 vs 0.693). ⚠️ NOTE: the *intervention* effect (A1) **does** replicate cross-codeword; it is the *correlational map* that does not |

## C. WITHDRAWN / NARROWED

| id | what | why |
|---|---|---|
| `C-CONT-013` | **`K1` withdrawn** | the contrast-free raw state beat it at its own site (0.7504 vs 0.6972); the map measured **topic** |
| `C-CONT-012` | `CONT-ENTRY 012`'s "instrument not validated" | rested on `E→A`, structurally incapable of showing transfer |
| `C-CONT-025` | "signal specific to the doublespeak cell" | **false** — cell **B** is indistinguishable from the `mean4` control. The signal tracks **harm demonstrations**; C adds a real increment (p=0.0017) |
| `C-CONT-032` | the quantitative dissociation | the within-domain slope puts the prediction **at** the CI bound, not outside |
| `C-CONT-022` | `CONT-ENTRY 034`'s "at the reproducibility floor" | wrong three ways; implied MDE is 0.0256, less than half the declared |
| `C-CONT-037` | **WITHDRAWN IN FULL** — the "bare word `bomb`" false-negative channel | **it does not exist**: 0 of 38 counted rows are bomb content. With it falls entry 063's headline, *"both error channels are codeword-dependent in opposite directions"* — only the false-**positive** channel varies |
| `C-CONT-038` | "the correction is valid in both directions" (old A7) | the *kept* rows were never audited; 63/100 spurious |
| `C-CONT-043` | `F6`'s rank curve and "one-dimensional" | `pls_predict` applied components to the **undeflated** X |
| `C-CONT-046` | "regularisation buys 0.078" | **inverted** — the "unregularised comparator" **is** ridge at λ→∞ (verified: λ=1e9/1e12/1e15 all give +0.6135, the comparator exactly). *Less* shrinkage buys it |
| `C-CONT-047` | `F5` "beats the comparator" | difference +0.0650, CI **[−0.0031, +0.1312]**, wins in only 13/23 domains |
| `C-CONT-049` | entry 049/050's dissociation strength | within-domain p=0.069, between p=0.011; power to detect −0.0301 is **0.414**; 173 domains needed |
| `C-CONT-053` | amendment-2's `ko` vs `ctrl3` comparison | crosses GPU architectures (A5000 vs L40S). Bounded by A10, not fatal; the **primary** `ko`/`ctrl` pair is same-GPU and clean |
| `C-CONT-028` | `DR-070`'s stated reason for re-running the baseline | **false and frozen** — both runs used eager |
| — | inherited Q2 "confirmed" | **not split-replicated**: validation ρ=0.143, p=0.51 (`CONT-ENTRY 003`) |
| — | inherited `C-208` negative harm main effect | **button-only**; basket H p=0.33 |

## D. DEFECT LEDGER (own work)

| id | shape |
|---|---|
| `C-CONT-002` | the family-wise null **was not a null** — FWER false-positive rate 0.47 vs nominal 0.05 |
| `C-CONT-003` | `interaction` was twice the **main effect** (sign error) |
| `C-CONT-009` | `NameError` that `py_compile` and a 35-check self-test both passed |
| `C-CONT-013` | five nuisance controls built, **the null model omitted** |
| `C-CONT-016` | `--n-perm` declared and **never used** |
| `C-CONT-019` | chose a control **this repo had already refuted**, in a file that exists to record it |
| `C-CONT-020` | the `non_refusal` conjunct **silently dead** (wrong field name) |
| `C-CONT-024` | "differing only in the band" — bands had **different widths** |
| `C-CONT-031` | a run reported **`ok` after losing 98 % of its rows**, and its gate **PASSED** on the remainder |
| `C-CONT-015` | fourteen entries dated three days in the future |
| `C-CONT-034/035` | an **asserted count** beside the list it counts — and I reproduced it one entry after correcting it, then a third time in 069 |
| `C-CONT-036` | a completion read from a field that does not exist → every row scored empty → a clean, plausible, **fabricated** 0.0000 |
| `C-CONT-039` | a **regex count read as a rate** without reading the rows |
| `C-CONT-041` | the confirmatory script built fit and TEST from **one** corpus — it would have spent `DR-072`'s single read on a stack trace |
| `C-CONT-042` | "FROZEN" was an **unpinned string**; a modified copy printed FROZEN and stamped `config_id: DR-072` |
| `C-CONT-051` | the commit-time guard audited **536 of 1023** finished runs and announced "every finished run" |
| `C-CONT-054` | my own freeze omitted a field its script requires; superseded, not edited |

**The recurring shape:** *a quantity that could not have told you it was wrong* — and it appeared
**inside the repair for itself** five times now (`C-CONT-035` one entry after `034`; the zero-row
branch gated backwards inside the fix for `051`; a 9m51s hook inside the same fix). What caught things: adversarial re-derivation, the
commit-time completeness guard, and persisted intervention dose.

## E. OPEN, WITH COST

| what | why it matters | cost |
|---|---|---|
| ~~`DR-072`'s TEST read~~ | ✅ **DONE, CONFIRMED** — ρ_test +0.6054, 23/23 domains, p=0.00050, inside the prespecified [0.55, 0.70]. The single read is spent (`CONT-ENTRY 075`) | — |
| **Power on A2/A3** | still the decisive gap. Power to detect the predicted −0.0301 is **0.414**; MDE(80 %) 0.0484; **173 domains** needed, 2.6× what exists. ⚠️ the old note here said re-runs add nothing because generation is deterministic — **that is now known to be false across GPU architectures** (`C-CONT-052`), but the divergence is *numerical*, not a fresh sample, so it still does not buy power | new bank rows + ~12 GPU-h |
| **the lexicon's false-positive channel** | every corrected number is an upper bound until it is fixed, and it cannot be fixed by editing the frozen lexicon | a **new** frozen instrument, scoring the materials block rather than term presence |
| §7 template transfer | **no held-out readout template exists** | cheap (CPU) + 1 run |
| §15's harmful non-BOMB reference | the control that would separate "toward BOMB" from "toward harm" or "toward any installed concept". ⚠️ **gun cannot serve — it does not install** (within-domain sd 0.085 vs bomb's 0.374), and restricting to gun slots that did install is post-hoc selection on the outcome, forbidden by §4 | needs a concept that installs |
| **within-domain demonstration-side patch** | `REVIEW-2/SCIENTIFIC`'s top recommendation and the discriminator between the dissociation account and a **common-cause** account. ⛔ **BLOCKED — not constructible on this bank**: of 4050 within-domain cell-C pairs, 172 agree on `(seq_len, token_pos, n_occ)` and **0** share their demonstration codeword positions (`CONT-ENTRY 076`) | needs a **position-matched bank** (generation change), then ~6 GPU-h |

### Closed since the last revision
* ~~basket replication of A1–A3~~ → **done**, `CONT-ENTRY 071` (A2 basket −0.0090, NULL POWERED)
* ~~re-score 127 prior judge runs~~ → **done**, and the count was wrong: **111 of 483**, `CONT-ENTRY 063`
* ~~`F5`, `F7` never fitted~~ → **done**, registry now 8 of 8 fitted, `CONT-ENTRY 059`

## F. ARTIFACTS

`configs/`: `dcs_cont_dr070_intervened_asr.json` (+`amendment1`, `amendment2`),
`dcs_cont_dr071_installation.json`, `dcs_cont_dr072_f5_confirmation.json` (**FROZEN, HELD**),
`dcs_cont_dr073a_basket_asr.json` (supersedes `dr073`), `dcs_cont_candidate_registry.json`
`outputs/dcs_cont/`: `dr070_primary.json`, `layerpos_train_button_bomb.json`,
`layerpos_train_BASKET_bomb.json`, `within_domain_train_button_bomb.json`,
`surface_floor_*.json`, `logitlens_control_*.json`, `nb1_control_*.json`, `cp_per_arm.json`
`reports/`: `DCS_CONT_REVIEW1_ADJUDICATION.md`, `DCS_CONT_LITERATURE_UPDATE_20260910.md`,
`DCS_CONT_REVIEW2_{CODE,DATA,OUTPUT,STATISTICAL,SCIENTIFIC}.md`, `DCS_CONT_F5_RESULTS.json`,
`DCS_CONT_F5_ADJACENCY.json`, `DCS_CONT_F6_DEFLATED_L{14,24}.json`
`scripts/`: `dcs_cont_f5_probe.py` (reproduces A11), `dcs_cont_f5_confirm.py` (enforces `DR-072`)

---

## G. IF ONLY ONE THING IS REPORTED

The **methodological** result is the strongest thing here, and `REVIEW-2/SCIENTIFIC` ranked it above
every mechanistic finding: **an LLM-judge ASR pipeline on codeword-remapping jailbreaks mismeasures by
a factor of 2.55 [2.46, 2.66]**, its error channels are **codeword-dependent**, and the correction that
fixes the obvious channel has a large unaudited channel of its own. That is demonstrated on 58,468 rows
across 111 runs, with 158 completions hand-inspected on two codewords, and it generalises beyond this
bank. The mechanistic results are a **clean two-codeword null** (A2/A3) and a **candidate that cannot be
a mechanism** (A11).
