# DCS continuation — CLAIM TABLE
**BOMB representation search → causal ASR.** 2026-09-10 / 09-11. **Revised 2026-09-12 after REVIEW-2 and REVIEW-3** (`C-CONT-038`…`C-CONT-068`).
Mandate: `external_md/DCS_BOMBNESS_REPRESENTATION_TO_CAUSAL_ASR_CONTINUATION_20260910.md`

⛔ **Almost everything here is TRAIN/VALIDATION and EXPLORATORY.** **One** preregistered confirmation
has happened: `DR-072` (A11), read ONCE on TEST — see `CONT-ENTRY 075`, and `C-CONT-060` for the two
declared controls that were not run before it. Nothing else has touched TEST. `button` and `basket` are never pooled. The independence unit
is the **DOMAIN** throughout.

---

## A. WHAT WE CAN TELL MATAN AND MAHMOOD

| # | claim | status | n | statistic | source |
|---|---|---|---|---|---|
| **A1** | Cutting the query codeword's row access to the demonstrations, in the retrieval band, **removes ~31 % of concept-free semantic installation** | **MEASURED, REPLICATED CROSS-CODEWORD** | 67 domains each | **button** −0.2150, CI [−0.235, −0.196], **67/67**; **basket** −0.2435, CI [−0.273, −0.213], **67/67** (never pooled) | `CONT-ENTRY 049`, `054` · `DR-071` |
| **A2** | The **same cut does not change attack success** | **NULL, POWERED, REPLICATED CROSS-CODEWORD** | 67 domains each | **button** +0.0030, CI [−0.030, +0.036]; **basket** −0.0090, CI [−0.0254, +0.0090], p=0.40. ⚠️ the basket **sign is not established** — under three content rules it is −0.0090 / −0.0030 / +0.0030, bracket **[−0.0090, +0.0030]** spanning zero (`C-CONT-063`, `CONT-ENTRY 087/089`) | `DR-070`; `DR-073a` |
| **A2b** | 🆕 ⚠️ **The cut rewrites the text; the endpoint cannot see it.** The null is about the *instrument* as much as the mechanism | **MEASURED** | 670 rows | `ko` differs from `base` on **669/670** completions, difflib 0.391 — **larger divergence than the cross-GPU churn floor** (0.640); +8.5 pp [+4.3,+12.8] literal basket-weaving, −3.1 pp disclaimers, **7 of 8 shared refusals removed**; one *"I can't help with that."* → StrongREJECT **1.000** | `REVIEW-3/OUTPUT` · `CONT-ENTRY 085` |
| **A3** | ⇒ semantic installation and behavioural attack success are **dissociable under intervention** — qualitatively | **MEASURED, EXPLORATORY, NOW TWO-CODEWORD** | 67 domains × 2 codewords | A1 ∧ A2 on **both** button and basket. ⚠️ same scope and bands; **"same dose" is NOT true across the pair** — the installation and ASR arms use different query templates and persisted dose totals 346,329 vs 1,385,316 (`REVIEW-2/SCIENTIFIC 1.3a`) | `CONT-ENTRY 049 §2`, `071` |
| **A4** | The same cut **halves refusal**, and the effect is **band-specific** | **MEASURED** | 670 rows | refusal 0.115→0.040 (`ko`) vs 0.112 (`ctrl`, identical dose) | `CONT-ENTRY 044 §1` |
| **A5** | Installation predicts attack success **within domain**, topic held fixed | **MEASURED** | 670 slots / 67 domains | slope +0.140, perm p=0.0006 | `CONT-ENTRY 050 §1` |
| **A6** | The observational installation→ASR link **survives regeneration on different hardware** | **ROBUST TO GENERATION CHURN** (not "replicated" — see note) | 67 domains | corrected ρ 0.5312 vs 0.5260. The two runs share byte-identical prompts (`prompt_sha16` 670/670) yet **573/670 completions differ**, because one ran on a V100 and one on an L40S | `CONT-ENTRY 047 §1`, `070` |
| **A7** | StrongREJECT scores **literal-codeword essays** as jailbreaks | **MEASURED, VERIFIED BY INSPECTION** | 670 rows | 131/131 button removals correct, 27/27 basket removals correct | `CONT-ENTRY 038`, `039`, `060` |
| **A7b** | ⚠️ **The correction is NOT valid in both directions**, and its failure rate is **codeword-dependent by 4×** | **NARROWED — every corrected number is an UPPER BOUND** | 40 blind-labelled (20/codeword) + 100 + 91 hand-labelled | spurious among kept positives: **button 0.717 [0.448, 0.866]** (independently 63/100); **basket 0.177 [0.100, 0.433]** (independently 17/91) | `C-CONT-038` · `CONT-ENTRY 089`, `090` |
| **A7c** | 🆕 **A conservative rule brackets the basket endpoint — and has no analogue on button** | **MEASURED** | 40 blind labels | same rule: **basket precision 1.00 / recall 0.77** (a true lower bound) vs **button precision 0.50 / recall 1.00** (a bound in *neither* direction). Basket ASR is bracketed; **button has an upper bound only** | `CONT-ENTRY 089`, `090` |
| **A7d** | ⚠️ ~~The codeword-dependence is not a vocabulary problem~~ — **WITHDRAWN** (`C-CONT-068`, `CONT-ENTRY 097`): both "refutations" were scored against a **corrupted label column**. On repaired labels a substance rule reaches **0.909/0.769 (basket)** and **0.800/0.800 (button)**, and `MATERIAL ∧ ¬scope` reaches **precision 1.000 on BOTH** — a candidate lower bound on button, post-hoc and unvalidated (4 tp, Wilson lower 0.51) | **CANDIDATE, NEEDS OUT-OF-SAMPLE** | 40 labels | the mechanism is partly lexical: a button **is** a switch, so literal and harmful answers share all hardware vocabulary and differ only in an energetic substance (composition ratio basket 3.6 vs button 0.71, **5.1×**) | `CONT-ENTRY 097` |
| **A12** | 🆕 **The doublespeak remap is strongly concept-dependent**: `bomb` installs far more readily than `knife` or `gun`, on both codewords | **MEASURED, DOMAIN-PAIRED** | 1080 shared slots / 90 domains | button: bomb−knife **+0.4314** [+0.386,+0.475] 89/90 domains; bomb−gun **+0.5166** 87/90. basket: **+0.3612** 88/90; **+0.3346** 88/90. All sign-flip p=0.00005. ⚠️ the `knife`/`gun` ordering **reverses** between codewords (+0.0852 vs −0.0267) and does not replicate | `CONT-ENTRY 079`, `080` · `C-CONT-057` |
| **A13** | 🆕 §15's matched reference: cell C's demonstration-side state aligns with the **explicit-BOMB** state as installation rises, beating the matched context-only prototype | **MEASURED, REPLICATED CROSS-CODEWORD** | 900 slots / 90 domains each | ⚠️ **contrast-dependent** (`C-CONT-059`): matched **single** reference **+0.1598** (button) / **+0.1703** (basket), p=0.0005 both; the *averaged* prototype gives +0.4053 but sits near zero by **cancellation**. Quoted conservatively. ⚠️ the token-level **matching does no work** — a *mismatched* same-domain partner scores **+0.4196** and a domain-mean prototype **+0.5057** (`C-CONT-062`), so §46 prerequisite 7 is **PARTIAL**. **Concept-DEPENDENT, not bomb-specific**: knife/button **+0.0623 is NOT significant** against its own null (p=0.0845) and is **−0.0171** under the fair single-reference contrast; gun inconclusive. ⚠️ installability and geometry strength are confounded across only 3 concepts | `CONT-ENTRY 077`–`079`, `082` |
| **A14** | 🆕 **Installation is delivered almost entirely by the first four demonstrations**, and the knockout removes about a quarter of the total | **MEASURED** | 90 domains (ladder), 67 (share) | matched-`slot0`, probability scale: dose 0 ≈ 0 → **dose 4 +0.6728** [+0.610,+0.734] 90/90 → **dose 8 +0.0632** [+0.029,+0.099] 60/90, i.e. doubling the demos adds **9.4 %** of what the first four gave. Knockout share of the full 0→8 span: **25.4 % [20.8, 30.3]** — ~**three quarters survives the cut**. ⚠️ the 4→8 step is the ladder's only **cross-run** comparison (L40S/`16333dde` vs Quadro RTX 8000/`2c6fbff`), uncalibrated; a calibration run is in flight | `CONT-ENTRY 093`, `094`, `100` |
| **A8** | The transplant instrument **can** transfer, token-matched | **MEASURED** | 16 domains | +10.7 %, CI [+3.5, +19.5], p=0.010 | `CONT-ENTRY 021`, `023` |
| **A9** | 🆕 **Raw LLM-judge ASR overstates genuine attack success by an ORDER OF MAGNITUDE on codeword-remapping attacks** | **MEASURED, CORRECTION VALIDATED OUT OF SAMPLE** | 58,468 rows / 111 runs; 76 blind labels | `button` raw 0.3146 → lexicon 0.1243 → **CR-002 0.0263**: factor **11.4×, run-clustered CI [10.5×, 12.5×]** over 68 runs (**≈10.5×** adjusted for CR-002's 0.923 recall). `basket` 7.4× [5.2×, 10.0×], 6 runs. ⚠️ `carrot` unvalidated; basket's test cell is 1 row | `CONT-ENTRY 063`, `098`, `099` · `CR-002` |
| **A10** | 🆕 **Greedy decoding is not byte-reproducible across GPU architectures**, and that sets a noise floor under every ASR contrast | **MEASURED** | 670 prompts / 67 domains | same condition, V100 vs L40S: raw Δ +0.0149 CI [−0.018, +0.048], corrected Δ **+0.0015 CI [−0.015, +0.019]**. The `DR-070` primary (+0.0030) sits **inside** that band | `CONT-ENTRY 070` · `C-CONT-052` |
| **A11** | 🆕 A ridge probe on the demonstration-side state predicts installation **within domain** | **CONFIRMED ON TEST** — it **cannot mediate A1** (`C-CONT-040`); causal status at its own site **untested** | 900 fit / 230 test slots | TRAIN +0.6241 → VALIDATION +0.6784 → **TEST +0.6054, CI [+0.528, +0.678]**, 23/23 domains, p=0.00050. Beats a size-matched demo-span control by +0.3960, a random-direction floor's **max over 200 draws** by +0.2847, and is near-orthogonal to the logit lens (cos +0.076). ⚠️ two declared controls were run **after** the TEST read (`C-CONT-060`) | `CONT-ENTRY 059`, `061`, `075`, `086` · `DR-072` |

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
| any **button** content-true number | the published `HARD` rule is precision 0.50 there; a **candidate** lower bound exists (`MATERIAL ∧ ¬scope`, precision 1.000 on 4 tp) but is **post-hoc and unvalidated** (`CONT-ENTRY 097`) |
| "the basket cut reduced attack success" | the **sign is not established**; it flips across three content rules (`C-CONT-063`) |
| the §15 result as a **matched**-reference finding | a mismatched partner scores **higher**; the matching does no work (`C-CONT-062`) |
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
| `C-CONT-059` | §15's p-values | were the null of **ρ_B**, printed beside the **difference**. Bomb survives (p=0.0005 either way); **knife's "significant" +0.0623 is p=0.0845** and its fair contrast is **−0.0171** |
| `C-CONT-061` | "declines monotonically across populations" | 0.6241 → 0.6784 → 0.6054 **rises then falls**; the VALIDATION peak is noise |
| `C-CONT-062` | §15's matched pairing | does **no work** — mismatched +0.4196 > matched +0.3823; §46 prereq 7 → PARTIAL |
| `C-CONT-063` | the basket primary's **sign** | flips across content rules; "the direction the hypothesis predicts" withdrawn |
| `C-CONT-066` | the dose-0 "0.9 % concept-present floor" | bounds **dose 0 only** — it is 2 rows of 226, in a regime where the model emits almost no concept vocabulary |
| `C-CONT-067/068` | two proposed repairs to the instrument | both **refuted by my own tests** |
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
| ~~a content-true endpoint that works on button~~ | ✅ **DONE** — `CR-002` (`configs/dcs_cont_content_rule_v2.json`, FROZEN before its validation sample was drawn) validates **out of sample on both codewords**: 24 fresh rows, **0 false positives**, precision 1.000 [0.76,1.00], recall 0.92/0.80 (`CONT-ENTRY 098`) | — |
| **extend CR-002's validation** | precision 1.000 rests on 12 rows/codeword (lower bound 0.76) and recall 0.80–0.92 means it bounds rather than estimates. More labels tighten both | labelling only |
| **extend the labelled set** | 40 rows (20/codeword) now exist at `data/labels/`. Every endpoint claim should be scored against it; 40 is enough to reject a rule, not to certify one | labelling only |
| **Power on A2/A3 in content-true units** | **worse now that the endpoint exists**: against CR-002's button base rate of **0.0343**, the primary's CI half-width (~0.029) is ~85 % of the entire genuine attack rate. The endpoint is defensible; it is not powerful | new rows + ~12 GPU-h |
| **demonstration-dose ladder** (n=0/1/2/4, cell C) | `REVIEW-3/SCIENTIFIC`'s top recommendation: the missing behavioural positive control and the common-cause discriminator, acting on the one thing the `ko` cut provably cannot touch. **Gated behind the endpoint** | ~6 GPU-h |
| §15's harmful non-BOMB reference | `gun` cannot serve (does not install); `knife` shows **no excess** under the fair contrast. Needs a concept that installs — this bank family has none | new bank |
| within-domain demonstration-side patch | ⛔ **not constructible**: 0 of 4050 within-domain pairs share demo codeword positions (`CONT-ENTRY 076`). The **cell-to-cell** version exists and its benign control transfers *more* (`CONT-ENTRY 086`) | position-matched bank |

### Closed since the last revision
* ~~`DR-072`'s TEST read~~ → **CONFIRMED**, and its two missing controls now run (`CONT-ENTRY 086`)
* ~~the 18.7/25/36 % labelling disagreement~~ → **resolved at ~18 % on basket** (`CONT-ENTRY 089`)
* ~~§46 accounting~~ → all eight prerequisites addressed; **prereq 7 is PARTIAL** and the conclusion is **not taken**

## F. ARTIFACTS

`configs/`: `dcs_cont_dr070_intervened_asr.json` (+`amendment1`, `amendment2`),
`dcs_cont_dr071_installation.json`, `dcs_cont_dr072_f5_confirmation.json` (**FROZEN, HELD**),
`dcs_cont_dr073a_basket_asr.json` (supersedes `dr073`), `dcs_cont_candidate_registry.json`
`outputs/dcs_cont/`: `dr070_primary.json`, `layerpos_train_button_bomb.json`,
`layerpos_train_BASKET_bomb.json`, `within_domain_train_button_bomb.json`,
`surface_floor_*.json`, `logitlens_control_*.json`, `nb1_control_*.json`, `cp_per_arm.json`
`data/labels/`: `dcs_cont_content_true_labels_v1.json` (**40 blind labels**, 20/codeword)
`reports/`: `DCS_CONT_LABELLING_CRITERIA.md`, `DCS_CONT_REVIEW3_{CODE,STATISTICAL,SCIENTIFIC,DATA_OUTPUT}.md`,
`DCS_CONT_S15_v2_*.json` (all five contrasts, each against its own null),
`DCS_CONT_REVIEW1_ADJUDICATION.md`, `DCS_CONT_LITERATURE_UPDATE_20260910.md`,
`DCS_CONT_REVIEW2_{CODE,DATA,OUTPUT,STATISTICAL,SCIENTIFIC}.md`, `DCS_CONT_F5_RESULTS.json`,
`DCS_CONT_F5_ADJACENCY.json`, `DCS_CONT_F6_DEFLATED_L{14,24}.json`
`scripts/`: `dcs_cont_f5_probe.py` (reproduces A11), `dcs_cont_f5_confirm.py` (enforces `DR-072`)

---

## G. IF ONLY ONE THING IS REPORTED

The **methodological** result is the strongest thing here, and `REVIEW-2/SCIENTIFIC` ranked it above
every mechanistic finding: **an LLM-judge ASR pipeline on codeword-remapping jailbreaks mismeasures by
a factor of 2.55 [2.46, 2.66]**, its error channels are **codeword-dependent**, and the correction that
fixes the obvious channel has a large unaudited channel of its own. That is demonstrated on 58,468 rows
across 111 runs. Stronger now than when first written: the instrument's failure rate is **4× different
between two codewords of the same bank** (0.717 vs 0.177), the **same rule inverts its precision/recall
profile** between them, and the failure has a describable partly-lexical mechanism — a `button` **is** a switch, so literal
and harmful answers share all hardware vocabulary and differ only in an energetic substance, while a
`basket` shares neither (composition ratio 3.6 vs 0.71). 231 completions blind- or
hand-labelled across two codewords, with the labels published. The mechanistic results are a **clean
two-codeword null** (A2/A3, whose own sign is instrument-dependent), a **candidate that cannot be a
mechanism** (A11), and a **demonstration-side geometry** whose matched-pairing framing did not survive
(A13).
