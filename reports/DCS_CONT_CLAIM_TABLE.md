# DCS continuation — CLAIM TABLE
**BOMB representation search → causal ASR.** 2026-09-10 / 09-11.
Mandate: `external_md/DCS_BOMBNESS_REPRESENTATION_TO_CAUSAL_ASR_CONTINUATION_20260910.md`

⛔ **Everything here is TRAIN-only and EXPLORATORY.** No confirmation freeze has happened and the
frozen TEST split has not been read. `button` and `basket` are never pooled. The independence unit
is the **DOMAIN** throughout.

---

## A. WHAT WE CAN TELL MATAN AND MAHMOOD

| # | claim | status | n | statistic | source |
|---|---|---|---|---|---|
| **A1** | Cutting the query codeword's row access to the demonstrations, in the retrieval band, **removes ~31 % of concept-free semantic installation** | **MEASURED, REPLICATED CROSS-CODEWORD** | 67 domains each | **button** −0.2150, CI [−0.235, −0.196], **67/67**; **basket** −0.2435, CI [−0.273, −0.213], **67/67** (never pooled) | `CONT-ENTRY 049`, `054` · `DR-071` |
| **A2** | The **same cut does not change attack success** | **NULL, POWERED** | 67 domains | +0.0030, CI [−0.030, +0.036], MDE 0.053 | `CONT-ENTRY 044` · `DR-070` |
| **A3** | ⇒ semantic installation and behavioural attack success are **dissociable under intervention** — qualitatively | **MEASURED, EXPLORATORY** | 67 domains | A1 ∧ A2, both arms same scope/bands/rows | `CONT-ENTRY 049 §2` |
| **A4** | The same cut **halves refusal**, and the effect is **band-specific** | **MEASURED** | 670 rows | refusal 0.115→0.040 (`ko`) vs 0.112 (`ctrl`, identical dose) | `CONT-ENTRY 044 §1` |
| **A5** | Installation predicts attack success **within domain**, topic held fixed | **MEASURED** | 670 slots / 67 domains | slope +0.140, perm p=0.0006 | `CONT-ENTRY 050 §1` |
| **A6** | The observational installation→ASR link **reproduces on an independent pipeline** | **REPLICATED** | 67 domains | corrected ρ 0.5312 vs inherited 0.5260 | `CONT-ENTRY 047 §1` |
| **A7** | StrongREJECT scores **literal-button essays** as jailbreaks; the correction is valid in both directions | **MEASURED, VERIFIED BY INSPECTION** | 670 rows | 131/131 removals correct; false-negative rate 0.36 % | `CONT-ENTRY 038`, `039` |
| **A8** | The transplant instrument **can** transfer, token-matched | **MEASURED** | 16 domains | +10.7 %, CI [+3.5, +19.5], p=0.010 | `CONT-ENTRY 021`, `023` |

## B. WHAT WE MUST NOT SAY

| ⛔ | why |
|---|---|
| "the pathway **is** the behaviour" | A1/A2 are **necessity** interventions; a null licenses only "not required" |
| "we found a BOMB representation" | **`K1` is WITHDRAWN** (`C-CONT-013`); the registry has **no candidate** |
| "installation causally drives ASR" | A3 is **qualitative only**; the quantitative version was **downgraded** (`C-CONT-032`) — the within-domain prediction (−0.030) sits *on* the measured CI bound |
| "the transplant result is replicated" | it is a **numerical re-execution** of a deterministic computation (`C-CONT-026`) |
| "a localized state was transplanted" | +10.7 % is the **all-layer** window; the best localized window is 8 % (`C-CONT-027`) |
| any ASR number bare | the **0.155** false-positive floor and **0.137** judge flip rate must travel with it |
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

**The recurring shape:** *a quantity that could not have told you it was wrong* — and it appeared
**inside the repair for itself** three times. What caught things: adversarial re-derivation, the
commit-time completeness guard, and persisted intervention dose.

## E. OPEN, WITH COST

| what | why it matters | cost |
|---|---|---|
| **Power on A2/A3** | the decisive gap. Distinguishing −0.030 from 0 needs ~4× rows/domain; generation is **deterministic** (`do_sample=False`) so re-runs add nothing — it needs **new prompts** | new bank rows + ~12 GPU-h |
| basket replication of A1–A3 | one codeword only | ~8 GPU-h |
| §7 template transfer | **no held-out readout template exists** | cheap (CPU) + 1 run |
| §46 accounting | which of the seven no-representation prerequisites are met — **not yet answered** | analysis only |
| re-score 127 prior judge runs | `C-209` reaches them; **none revised** | ~1 h, no GPU |

## F. ARTIFACTS

`configs/`: `dcs_cont_dr070_intervened_asr.json` (+`amendment1`, `amendment2`),
`dcs_cont_dr071_installation.json`, `dcs_cont_candidate_registry.json`
`outputs/dcs_cont/`: `dr070_primary.json`, `layerpos_train_button_bomb.json`,
`layerpos_train_BASKET_bomb.json`, `within_domain_train_button_bomb.json`,
`surface_floor_*.json`, `logitlens_control_*.json`, `nb1_control_*.json`, `cp_per_arm.json`
`reports/`: `DCS_CONT_REVIEW1_ADJUDICATION.md`, `DCS_CONT_LITERATURE_UPDATE_20260910.md`
