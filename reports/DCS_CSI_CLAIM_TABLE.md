# DCS Causal-Semantic-Installation sprint — claim table

**Maintained live. Opened 2026-09-15.** Supersedes nothing: `reports/DCS_CONT_CLAIM_TABLE.md`
remains the predecessor phase's frozen record. This file covers what *this* sprint has established,
corrected or withdrawn, and is the file to read before writing any sentence for Matan or Mahmood.

Sourced to the sprint log
`external_md/DCS_CAUSAL_SEMANTIC_INSTALLATION_MECHANISM_AND_REPLICATION_PLAN_AND_PROGRESS_20260915.md`
(entries `S-###`) and to the artifacts named in each row.

---

## A. WHAT WE CAN DEFEND

| # | claim | statistic | population | caveats | source |
|---|---|---|---|---|---|
| D1 | The A1 knockout reduces semantic installation | ko − ctrl = **−0.2150** [−0.234, −0.196] button; **−0.2435** [−0.273, −0.213] basket; **67/67 domains** each | 670 rows / 67 TRAIN domains per codeword, `semantic_one_word`, cell C, dose 4 | inherited from CONT-054, not re-run this sprint; `ctrl` is a dose-matched placebo band (20–28), `base` is the no-knockout arm | S-003 |
| D2 | A query-side state at rel-6 predicts installation, and the result reproduces under independently written code | TRAIN LOO ρ = **0.5935** (rel-6, L20); VALIDATION transfer **+0.645** button / **+0.653** basket | 670 slots / 67 TRAIN domains; 230 slots / 23 VALIDATION domains | the layer is a **plateau** (L18 0.5931 vs L20 0.5935) — L20 is a consistent choice, not an identified peak; the site rel-6 is frozen from prior work, not re-searched | S-013, S-009 |
| D3 | The basket QPROBE validation figure is a genuine held-out number, not an aliasing artifact | 0.65252 validation vs 0.65245 train (full precision); fit/score populations share **0 keys and 0 prompt_ids** | 230 slots / 23 VALIDATION domains | quote both figures together so the 4-dp near-equality is not read as identity | S-009 |
| D4 | The installation axis is **not sentence-specific** | cross-prompt ρ = **+0.598** (mean of both directions) vs within-fit LOO 0.546; retention **1.095** | TRAIN domains, bank-internal `dev`/`heldout` prompt split, 335 → 335 rows | **not** template generalisation, **not** domain generalisation, **not** causal; retention > 1 is an artifact of the halved fit set | S-018 |
| D5 | The A1 knockout de-refuses on the behavioural endpoint | CTRL 0.1111 → KO 0.0444; Δ = **+0.0667** [+0.0333, +0.1000]; exact sign-flip p = 4.88e−4 | 180 rows / 90 domains (67 train + 23 val), slot0, dose 4 | p is **exactly at its attainable floor** (12 informative domains) — the test exhausted its resolution | S-002 |
| D6 | Greedy generation is not reproducible across GPU architectures, but the refusal endpoint is stable | **42/180 = 23.3 %** byte-identical completions; **1/180 = 0.6 %** refusal-label flips | CTRL arm, identical prompts/seed/dtype/attention, L40S vs RTX 3090 | paired, same-prompt measurement | S-016 |
| D7 | The button patch run is mechanically sound | same `prompt_sha16` across arms; 67 train + 23 val + **0 TEST**; eager/bf16; knockout live every row with 0 decode edits; rescue fired 180/180; target token `" button"` ×180; all arms L40S; two refusal detectors agree on 100 % of 720 labels | 180 rows / 90 domains | this is a statement about the **run**, not about the effect | S-002 |
| D8 | The axis build is bit-reproducible | max elementwise diff **0.000e+00** across 4 builds on 2 nodes | — | one earlier build under a different script revision differed; its tensors were overwritten, so that difference is **unexplained**, not attributed | S-014, **S-019** |

| D9 | The knockout's effect on installation is carried predominantly by the **codeword row** | `rel −10` (token `' button'`) recovers **+0.03289 = 46.6 %** of the whole-state effect, 62/67 domains; 16 measured positions sum to **92.4 %**; top four carry 92.5 % | button TRAIN, 670 rows / 67 domains, L20, `semantic_one_word` | positions are **query-span**-relative; `rel −1`/`−2` (34.9 %) are the **readout site**, so their share is output adjacency and not storage; 12 positions unmeasured — the remainder is NOT inferred by subtraction | S-069, S-072, **S-077** (`reports/DCS_CSI_POSITION_MAP_button_train.json`) |
| D12 | On **basket**, the rank-1 installation axis is the causally strongest direction in its control family, on **both** splits | **BOTH SPLITS at the full 46-control family (S-100 TRAIN, S-102 VALIDATION).** TRAIN: `KO_AXIS − KO` = **+0.00264** [0.00068, 0.00471], 44 pos / 23 neg, **rank 1 of 47**, rank p = **0.0213**; shuffled-only **1 of 25** (floor 0.0400) and random-only **1 of 23** both pass separately. (Superseded figures at the 34-control family: +0.00265, rank 1 of 35, p = 0.0286.)  VALIDATION **+0.00401**, 215 keys / **23 held-out domains**, **rank 1 of 47**, rank p = **0.0213**, with shuffled-only **1 of 25** (floor 0.0400) and random-only **1 of 23** passing separately. (Superseded 30-control figures: +0.00400 [0.00098, 0.00774], rank 1 of 31, p = 0.0323.) Controls are norm-matched random subspaces and shuffled-label fits. Gates hold on both: `KO_FULL − KO` = +0.12131 (67/67 domains) TRAIN, +0.10306 (23/23) VALIDATION; `KO_SELF − KO` inside the preregistered 0.005 tol | 647 keys / **67 TRAIN domains** (41 arms); 218 keys / **23 VALIDATION domains** (37 arms); L18, site `rel-6`, `semantic_one_word`, cell C, dose 4 | **The effect is very small**: the axis recovers 0.0040 of a 0.229 knockout effect = **3.9 %**, and 3.9 % of what the whole state restores. Both rank p values are **at their attainable floors** (1/35, 1/31). The **shuffled-only** subfamily — the binding comparator per R5, whose sd is 1.9x the random family's at the same mean — is **rank 1 of 13 (floor 0.0769) TRAIN and rank 1 of 9 (floor 0.1111) VALIDATION**, i.e. **INCONCLUSIVE on its own, both splits**. **R6 (leave-one-DOMAIN-out on the RANK): the two splits are NOT equally sturdy.** VALIDATION holds rank 1 under **23 of 23** single-domain drops (candidate range +0.00275..+0.00438). TRAIN, **at the 46-control family (R7, supersedes R6 here)**, holds rank 1 under **65 of 67** drops and its **worst** single-domain deletion leaves **rank 2 of 47, p = 0.0426 — still passing**; the verdict is invariant to deleting any one domain. (At the superseded 34-control family the worst drop, `rail_depot`, gave rank 4 of 35, p = 0.1143 — failing. Enlarging the family lowered the floor faster than it raised the perturbed rank.) **Lead with VALIDATION**, which is both the held-out split and the robust one; never quote TRAIN's rank without this sensitivity. LOO probes this estimate on this sample — it is not a population property, not a replication, and does not lower the 1/31 floor. Independently re-derived by `dcs_csi_rederive_subspace.py` (no shared code): 34/34 and 30/30 controls agreeing to 1e-5, same ranks. Provenance audited (R6): of the 30 VALIDATION controls, **0 carry a CUDA failure** — the single fault-damaged arm, `KO_SHUF10`, is quarantined and excluded | S-079, S-082, **S-088**, R5, **R6** (`reports/DCS_CSI_SUBSPACE_basket_train_n34.json`, `reports/DCS_CSI_SUBSPACE_basket_validation_n30.json`, `reports/DCS_CSI_REDERIVE_*.json`) |
| D10 | Recovery is linear in the **number** of query-span positions restored | through-origin `recovery = 0.002482·k`, **R² = 0.9968** TRAIN / 0.9939 VALIDATION; slope × 28 / `KO_FULL` = 0.984 / 0.987; `KO_POS28` ≡ `KO_FULL` exactly on distinct run dirs, both splits | button, both splits | linearity under **random** subsets does **not** imply uniformity — a concentrated effect gives the same curve (S-066) | S-059, S-063, S-077 |
| D11 | The offset the axis was fit at is causally near-inert | `rel −6` recovers **+0.00071 = 1.0 %** (39/28 domains) against a random position's +0.00281 | button TRAIN | the axis was fit at `rel −6` of the **behavioural** prompt; this measures `rel −6` of the **semantic** prompt — state the offset AND the prompt type every time (prohibition 15) | S-066, S-070, S-072 |
| D13 | The button/basket dissociation is **not** explained by the layer each codeword was fit at | Button's axis at **basket's layer L18** ranks **8 of 11** (rank p = 0.7273), against **4 of 11** at its own L20. 7 of 10 controls beat it at L18 vs 3 of 10 at L20. The candidate is **−0.00027 [−0.00124, +0.00068], sign-flip p = 0.58, 35 pos / 32 neg domains — indistinguishable from zero**; the negative sign is NOT interpretable and must not be reported as a sign flip (R8). Instrument demonstrably live at L18, and **dose-normalised** rather than by the raw ratio (R8, per S-041's P1-g rule): the rank-1 axis spans **3.87 %** of the ‖clean − ko‖ delta at L18 vs **3.48 %** at L20 — *larger*, not smaller — while the delta itself is *smaller* (1.3009 vs 1.5207), so L18 is the higher-leverage site (0.0833 vs 0.0457 recovery per unit ‖delta‖). The linear-dose prediction is **+0.00420** at L18 vs +0.00242 at L20, i.e. the L18 axis had **1.7× more to win and returned less than nothing** (−7 % of prediction, vs +17 % at L20). Raw positive controls, both paths: `KO_FULL − KO` = **+0.10842 (67/67)** at 658 keys / **+0.10817** at 659 keys, vs +0.06955 (66/67) at L20; manipulation **−0.20730** at 658 keys / −0.20686 at 659 keys; identity inert; **no VOID conditions** | **658** keys (primary analyser, 17 arms) / **659** keys (independent re-derivation, 14 arms) / **67 TRAIN domains**, button, site `rel-6`, `semantic_one_word`, cell C, dose 4, 10-control family. The two key counts differ only because the re-derivation does not load `KO_ORTH`/`KO_PLS`; quote each figure with its own key count and never mix the two (R8) | **TRAIN only** — button has no held-out L18 arms. Family of 10, floor **0.0909**: this can show a candidate sitting inside its controls, and could **not** have certified a pass. **Only half the 2×2**: basket has never been run at L20, so *"basket's pass is not explained by its layer"* has **no evidence** and must not be said. The swap is fair because both layers are on each codeword's ρ plateau (button 0.5931/0.5935, basket 0.6525/0.6512 — D2). Outcome was **predicted in writing before the data** (S-103). `--allow-short` moved 3→4 for one control; dropping that control gives rank 7 of 10, same verdict | **S-104**, corrected and dose-normalised by **R8** (`reports/DCS_CSI_SUBSPACE_button_train_L18.json`, `reports/DCS_CSI_REDERIVE_button_train_L18.json`, `reports/DCS_CSI_REDERIVE_button_train_L20.json`) |

---

## B. EXPLORATORY / DIRECTIONALLY CONSISTENT BUT UNDERPOWERED

| # | claim | statistic | why it is not in section A | source |
|---|---|---|---|---|
| E1 | Restoring the clean query span under the live knockout partially recovers refusal | **l40s: Δ = +0.0278, k=5, p=0.0625 (twice, identically). 3090: Δ = +0.0389, k=7, p=0.0156.** Recovery fraction 0.42–0.58 | Positive and same-signed on two architectures, **every** informative domain in the predicted direction, none against — but the exact test is **at its attainable floor in all three runs** and clears 0.05 on **one architecture only**. Significance is hardware-contingent via a 2-domain change in k. Underpowered at D=90 (power 0.39); D≈145 needed | **S-002, S-026, S-032** |
| E2 | A rank-r PLS subspace is a candidate mediator | TRAIN LOO ρ: r1 0.5021 … r5 0.5767, all **below** the rank-1 ridge 0.5935; selected rank sits at the grid boundary | rank is not identified; no "the representation is r-dimensional" claim may be made | S-013 |

---

## C. CANNOT ANSWER — the design could not test it (NOT negatives)

| # | question | why | source |
|---|---|---|---|
| C1 | Does the clean query-span rescue recover refusal on **basket**? | the endpoint is at floor: CTRL 0.00556 / KO 0.000 / RESCUE 0.00556 — **one movable refusal event in 180 rows**, k = 1 informative domain, attainable p-floor **1.0**, and the recovery-fraction estimator returns CANNOT ANSWER from its degeneracy guard. ~540 domains would only make significance *attainable*. **It is a headroom problem, not a sample-size problem.** | S-002, S-004 |
| C2 | Does position **identity** matter beyond position **count** (the size-match control)? | the full-minus-size-match contrast rests on **2 domains**; attainable p-floor **0.50** | **S-002 (WITHDRAWS `0a8c7e6d`)** |
| C3 | Does the representation survive a **template** change? | the corpus contains exactly one template family (`example_position=near`, `role_style=plain` on every row). Needs one new GPU extraction | S-017 |
| C4 | Is the axis fit on the **semantic** forward causal? | `lpm.load_corpus` deliberately refuses a semantic corpus as a predictor population (frozen anti-circularity guard), and no multiposition cache exists for it. **Deferred, not withdrawn** | S-008 |

---

## D. WHAT WE MUST NOT SAY

Carried forward from the predecessor phase's audit (`reports/DCS_CSI_CLAIM_STATE_AUDIT.md`) plus
this sprint's additions. **These are prohibitions, not preferences.**

1. "We found the BOMB representation." — not supported by anything in section A.
2. "F5 / A11 is the mechanism." — its demo-side site is bit-identical across ko and ctrl and **cannot** mediate A1.
3. **"Basket failed to replicate."** — say **"basket could not test the behavioural recovery hypothesis"** (C1).
4. **"The size-match control passed."** — WITHDRAWN (C2).
5. **"The query-side rescue recovers 42 % of the de-refusal (CI excludes 0)"** *stated as a confirmed result* — it is E1, exploratory and underpowered, and the CI carries almost no information beyond "5 domains moved and none against".
6. "Installation does not affect ASR." — underpowered in content-true attack units.
7. "The knockout does nothing to behaviour." — it visibly rewrites completions and changes refusal.
8. "Greedy decoding reproduces byte-identically." — measured at **23.3 %** across architectures (D6).
9. **"First to causally intervene on demonstration→query attention in in-context learning."** — FALSE; Wang et al., *Label Words are Anchors* (EMNLP 2023, arXiv:2305.14160) already does layer-banded demo→query attention blocking.
10. "We found the Doublespeak phenomenon / the representation-convergence story." — published and **verified first-hand** (S-035): Yona, Sarid, Karasik & Gandelsman, *In-Context Representation Hijacking*, arXiv:2512.03771 — introduces "Doublespeak", the `carrot → bomb` construction, the layer-by-layer convergence, and 74 % ASR on Llama-3.3-70B. What remains open is the **causal** chain, not the phenomenon.
10b. **"They did no intervention."** — imprecise and forbidden. They use logit lens **and Patchscopes**, and Patchscopes *is* a forward-pass edit; it patches a state into a different sequence **to read out what it encodes**, which is interpretation machinery rather than an ablation. Say "read-only / no ablation, knockout or steering", not "no intervention".
10c. **"Our method is novel."** — it is not. Causal subspace patching of ICL concept representations is published (arXiv:2605.18830, *ICL Operates as Concept Subspace Learning*, incl. the complementary-subspace control), and causal representation→refusal analysis for jailbreaks is published (arXiv:2605.00123, LOCA, COLM 2026). Both read and verified in S-036. The surviving novelty is narrow: the demo→query attention edge as the causal locus **for semantic installation specifically**, the concept-free readout as an intervention-scorable DV, whatever Phase 1 finds (possibly a **dissociation** from 2605.18830's positive), and the fact that it is done on the model where the published descriptive account's tool failed.
11. Any bare ASR number — the literal-codeword false-positive floor and the 0.137 judge-flip rate must travel with it.
12. Anything marked A16, A17, K1, or WITHDRAWN in the predecessor audit.
13. **"The axis generalises across templates."** — D4 is *sentence*-level, not template-level (C3).
14. **"The axis differs across nodes / is hardware-sensitive."** — refuted; see D8 and S-019.
15. **"The probe site is causally inert"** without the prompt-type qualifier. The axis was fit at `rel -6` of the **behavioural** prompt; the causal test ran at `rel -6` of the **semantic** prompt, and the two prompt types do not align token-for-token (the codeword itself is at `rel -11` behaviourally and `rel -10` semantically — S-070). State the offset and the prompt type, every time.
16. **"Each query-span position contributes equally"** / **"there is no privileged position"** / **"is it localised? a quantified no."** — all WITHDRAWN (S-066). Linearity under random subsets cannot distinguish uniform from concentrated, and the position map shows strong concentration.
17. **"`cw_query` recovers nothing / the knockout's own target is causally inert."** — WITHDRAWN (S-068, S-069). That arm tested `rel −11`, the token *before* the codeword; the codeword row is the single **largest** contributor at 46.6 %.
19. **"The installation axis is causal."** — unqualified, forbidden. D12 establishes that it is the **top-ranked** direction in its control family on both splits, at an effect size of **3.9 %** of the knockout. Say "the strongest single direction tested, recovering 3.9 % of the knockout effect", never "the causal direction" or "the mechanism".
20. **"Basket's axis beats its fit-capacity-matched controls."** — **LIFTED ON BOTH SPLITS (S-100 TRAIN, S-102 VALIDATION).** With the full **46-control family on each split** (22 random + 24 shuffled), the candidate is **rank 1 of 25 among the shuffled-label controls alone** (floor 0.0400) and **1 of 47 pooled** (floor 0.0213) on **both** TRAIN (+0.00264) and held-out VALIDATION (+0.00401). **Zero** of the twelve (TRAIN) and sixteen (VALIDATION) newly added shuffled controls exceeded the candidate — the preregistered 0-above branch (S-083/S-095/S-096). The preregistered exchangeability re-test passes on both (p = 0.8311 TRAIN, 0.1353 VALIDATION), so the pooled rank is a legitimate single null on each. Every verdict reproduced by two independently written analysis paths. **This prohibition is retired**; what replaces it is prohibitions 19 and 21, which are unaffected — the effect is 3.9% of the knockout, concentrated (top 5 of 23 held-out domains carry 91.8%), and codeword-specific.
21. **"The Phase-1 negative is overturned" / "the axis is causal in general".** — button ranks **4 of 11** on both splits. The honest summary is a **codeword dissociation**: basket replicates, button does not. **S-104 de-confounded half of this**: "codeword" and "layer" were perfectly confounded across every comparison in D12 and S-097 (basket always L18, button always L20). Button at **L18** ranks **8 of 11** — it fails at basket's layer too, and fails worse, at a layer where the whole state recovers 56 % *more*. So button's failure is not a layer artifact (D13). **The symmetric arm is still missing**: basket has never been run at L20, so the phrase "codeword dissociation" is now supported on the failing side only. Until basket-at-L20 runs, do not write that the dissociation is *fully* de-confounded.
22. **"The volume / fileserver is degraded."** — WITHDRAWN (S-090). Measured from the login node and wrongly generalised; the same volume serves 309 MB/s to a node outside the `n-30x` rack. Say "the `n-30x` rack's NFS path is broken".
18. **Any predictive rho obtained from a `--fit-prompt semantic` fit.** That fit reads the state on the same forward whose next token is the target, so its only legitimate output is a **direction to intervene along** — never a prediction. (The shared loader's default still refuses such corpora; the Phase-1 opt-in is explicit and argued in S-025.)

---
---

# APPENDED 2026-09-20 — sprint entries S-108 … S-126

**Nothing above this line has been altered, reworded or deleted.** This project's convention is that
corrections are **ADDITIVE**: an existing row that is now wrong gets an amendment row below that names
it and says why, and it keeps its original text so the record of what was believed, and when, survives.
Verified mechanically: the 82 lines above are byte-identical to the file as committed at `be0e6818`.

Every number in this block was read by me out of the named artifact or recomputed by me from
`results.jsonl`, with the command given. Nothing here is taken from prose in the sprint log.

---

## A2. NEW ROWS — append to section A

| # | claim | statistic | population / split / codeword / layer | caveats | source |
|---|---|---|---|---|---|
| D14 | On **basket at L20** — button's layer — the rank-1 axis is again the **largest** recovery in its control family, but the family is too small to certify it | candidate `KO_AXIS − KO` = **+0.00294**, ci95 [+0.00146, +0.00455], **46 pos / 21 neg domains**, p = 1.70e−04; primary contrast `KO_AXIS − KO_ORTH` = **+0.00302** [+0.00145, +0.00470], 47/20, p = 3.35e−04; **rank 1 of 11**, attainable floor **0.0909**. Whole control family, all ten below it: KO_RAND2 +0.00129, KO_SHUF2 +0.00083, KO_RAND4 +0.00036, KO_SHUF3 +0.00002, KO_RAND5 −0.00005, KO_RAND3 −0.00012, KO_RAND1 −0.00015, KO_SHUF0 −0.00026, KO_SHUF1 −0.00029, KO_RAND0 −0.00057. Holm one-sided specificity rejects **all 10** (`specificity_all_controls_rejected = true`). Recovery fraction of the whole-state control **0.0313** [0.0165, 0.0466] | **657 keys / 67 TRAIN domains**, 17 arms, basket, **L20**, site `rel-6`, basis `dcs_csi_axis_basket_L20.pt`, `semantic_one_word`, cell C, dose 4 | **INCONCLUSIVE — NOT a pass and NOT a failure.** Ten controls cannot reach α = 0.05; certifying needs ≥ 19. The analyser's own verdict string says exactly this. **TRAIN only** — basket has no held-out L20 arms. **In-sample**: the axis was fit on these same 67 domains (`evaluation_is_in_sample: true`). PR-CSI-002's `prediction_fixed_before_data` was *"rank 1 of 11"*, so this is the **predicted** outcome and buys nothing until the family is extended to 46. `VOID` list empty; all 17 arms on n-303 / RTX 3090, no V100; every rescue row records layer 20 and nothing else; 0 TEST domains. **LOO reproduced by me**: rank stays 1 in **67 of 67** single-domain drops, histogram `{1: 67}`, candidate range +0.00249 … +0.00311, 0 sign flips | **S-125** (`reports/DCS_CSI_SUBSPACE_basket_train_L20.json`, `reports/DCS_CSI_REDERIVE_basket_train_L20.json`) |
| D15 | **The 2×2 across codeword × layer is complete, and the LAYER IS EXONERATED** as the explanation of the button/basket dissociation | **basket, own layer L18**: TRAIN cand +0.00264 [+0.00068, +0.00471], 44/23, **rank 1 of 47, p = 0.0213 — PASSES**; VALIDATION cand +0.00400 [+0.00098, +0.00774], 15/8, **rank 1 of 31, p = 0.0323 — PASSES**. **basket, other layer L20**: TRAIN cand +0.00294, **rank 1 of 11**, floor 0.0909 — top of distribution, floor-limited (D14). **button, own layer L20**: TRAIN cand +0.00040 [−0.00025, +0.00108], 41/26, **rank 4 of 11, p = 0.3636 — DOES NOT PASS**; VALIDATION cand +0.00132 [−0.00002, +0.00275], 14/9, **rank 4 of 11, p = 0.3636 — DOES NOT PASS**. **button, other layer L18**: TRAIN cand −0.00027 [−0.00124, +0.00068], 35/32, **rank 8 of 11, p = 0.7273 — DOES NOT PASS, further inside**. So **basket is top of its control distribution at BOTH layers; button is inside its controls at BOTH layers** | basket L18 TRAIN 642 keys / 67 dom, basket L18 VALIDATION 218 keys / 23 dom, basket L20 TRAIN 657 keys / 67 dom, button L20 TRAIN 666 keys / 67 dom, button L20 VALIDATION 229 keys / 23 dom, button L18 TRAIN 658 keys / 67 dom. `rescue_layers` read per report from `arm_meta.KO_AXIS`: 18, 18, 20, 20, 20, 18 respectively — the layer of each cell is **measured, not assumed** | **The cells are NOT matched on control-family size.** Basket's two passing cells carry **46 and 30** controls; the other three cells carry **10**. "rank 1 of 47" and "rank 1 of 11" are therefore not comparable as p-values — what is comparable, and what the row claims, is **top-of-family vs inside-family**. The instrument is live in every cell: `KO_FULL − KO` = +0.12041 (66/67) basket L18 TRAIN, +0.10306 (23/23) basket L18 VAL, **+0.09391 [+0.07898, +0.10897] (67/67)** basket L20, +0.06955 (66/67) button L20 TRAIN, +0.09508 (23/23) button L20 VAL, +0.10842 (67/67) button L18 — **no cell's outcome can be blamed on a dead instrument**. This does **not** de-confound the dissociation to a conclusion: it removes **one** candidate explanation. Still confounded with the axis's own fit, the codeword's token statistics, and everything else that differs between the two banks. Basket-at-L20 is floor-limited and TRAIN-only, so the exoneration rests on *both* diagonals being read the same way, not on a certified symmetric pass | **S-125**, with **S-104**/R8 for the button-at-L18 half (`reports/DCS_CSI_SUBSPACE_basket_train_n46.json`, `_basket_validation_n30.json`, `_basket_train_L20.json`, `_button_train_rank1.json`, `_button_validation.json`, `_button_train_L18.json`) |
| D16 | **Necessity is FEASIBLE**: removing the installed component from a **clean** forward moves installation down, on every domain | `KO_NEC_FULL − NEC_BASE` = **−0.11009** (full precision −0.110094), ci95 **[−0.12522, −0.09514]**, **67 neg / 0 pos / 0 tied of 67 domains**, sign-flip p at its MC floor 5.0e−06. Manipulation on the same arm set `NEC_KO − NEC_BASE` = **−0.23406** [−0.26369, −0.20438], 67/67 neg. Fraction of the clean→KO span removed = **0.47037 (47.0 %)**. Arm domain means: `KO_NEC_FULL` 0.363540, `NEC_BASE` 0.473635. Two independent estimators agree **exactly** on the point; bootstrap seed-stable across seeds 1 / 20260916 / 987654321 | **670 keys / 67 TRAIN domains**, basket, **L18**, `rescue_donor: ko`, whole-state (no basis), `semantic_one_word`, cell C, dose 4; SLURM 906433, n-307, RTX 3090, bf16 | **THIS IS THE WHOLE-STATE CONTROL, NOT THE AXIS.** It establishes that the instrument can move installation in the *removal* direction and nothing more. It says **nothing** about whether the rank-1 axis carries that effect — Gate 3 was deliberately not evaluated, `ranks` is `{}`, and the 9 control arms were still running when this row was written. **Do not compare 47.0 % to any sufficiency percentage**: the necessity arms are at **L18** and PR-CSI-002's sufficiency read is at **L20**, and D15 is the entry establishing that layer is a variable you check rather than assume. Gate 1's four legs pass on all three rescue arms (`violations {}`, `frac_rows_ok` 1.0 = 670/670, min donor-prefill edits 387, max readout-knockout edits **0**, min patch positions 112, min donor `delta_norm` 0.86104). `KO_NEC_FULL`'s `config.json` records `rescue_basis: ""` not `null` — falsy, so `DonorPatch` (whole-state) ran and all 670 rows carry `rescue_basis: null`; a literal-form discrepancy with the frozen instruction, recorded not hidden. The attainable floor even with half 2 is **1/10 = 0.10**, so the analyser's PASS branch is **unreachable by design** | **S-126** (`reports/DCS_CSI_PR003_GATE12_PARTIAL_HALF1.json`) |
| D17 | **PR-CSI-002's Gate-0 VOID condition is RETIRED — by measurement, not by argument** | `KO_AXIS` (ran post-edit, job 905990) vs `KO_AXIS_ANCHOR` (ran pre-edit, job 906001): **max abs diff = 0.0 on all six readout fields — `logp_concept`, `logp_codeword`, `semantic_logodds`, `p_concept`, `p_codeword`, `top1_id` — on all 670 shared rows** (670 vs 670 keys, 0 A-only, 0 B-only). Their `config.json` `args` dicts carry **57 keys each and differ in exactly 2**: `arm` and `tag`. `rescue_layer`, `rescue_basis`, `bank`, `exclude_prompt_ids` and `seed` all identical | 670 rows, basket TRAIN, L20, both arms on n-303 / RTX 3090 | The S-110c mid-run edit to `score_behavior.py` (21:53:36) **provably changed nothing on this path**. This retires the VOID condition **for PR-CSI-002's arms only** — it is not a general licence to edit that file mid-run, and PR-CSI-003 carries the same condition verbatim over the **currently running** necessity arms. This is determinism across two SLURM jobs on the **same node**, not across nodes (that is D6/D8's territory) | **S-125**, reproduced first-hand 2026-09-20 (see command block below) |

---

## A3. AMENDMENTS — corrections to rows above, additive and marked

Each amendment names the row it governs. **The original row is unchanged and still readable**; read the
row and its amendments together.

| id | marker | governs | what changed, and why |
|---|---|---|---|
| **AM-1** | **CORRECTION** | `runargs/dcs_csi_pr002_read.txt` (frozen read file) and **S-109**'s closing paragraph, both of which record basket-at-L20 as *"captured fraction 0.03001 at delta_norm 1.4012"* | Those two numbers **do not reproduce on the finished run**. The full-population values are **captured fraction 0.02820, displacement `delta_norm` 1.36796**, over **670 of 670 rows**. The superseded pair is a **prefix mean over the first 213 rows** — I located it independently by closest-prefix search: k = 213 gives 0.03001 / 1.40121 at relative-error sum **1.19e−04**. It was read off a partially-written `results.jsonl` while job 905990 was still running, exactly as the frozen file says it was. **The qualitative claim survives**: at button's layer basket's capture **drops** and its displacement **grows** (L20 0.02820 / 1.36796 vs L18 0.03237 / 1.17153, both over 670 rows). Only the two digits are superseded |
| **AM-2** | **CORRECTION (units)** | any prose attached to **D12**, **D13** or AM-1 that calls the captured fraction an *energy* fraction | `src/boombness/donor_patch.py:290` computes `captured_energy_frac_mean = mean(proj_norm / delta_norm)` — a ratio of **norms**, i.e. **AMPLITUDE**, despite the key name. The **energy** fraction is the square, of order **0.1 %**, not 3 %. Say *"spans ≈ 3 % of the displacement in amplitude (≈ 0.1 % in energy)"*. Further caveat this file adds: the persisted field is a **mean of per-row ratios**, so the exact mean energy fraction is **NOT recoverable** from it — the squared figure is order-of-magnitude only. The field is misleadingly named at source and is **not** renamed, because it has existing readers |
| **AM-3** | **STRENGTHENS / DISCHARGES a caveat** | **D13** ("The button/basket dissociation is not explained by the layer each codeword was fit at") and **prohibition 21** | D13 carries the caveat *"**Only half the 2×2**: basket has never been run at L20, so 'basket's pass is not explained by its layer' has **no evidence** and must not be said."* That caveat is now **discharged by D14/D15**: basket at L20 ranks **1 of 11**, top of its distribution, with the instrument live (`KO_FULL − KO` = +0.09391, 67/67). Prohibition 21's sentence *"Until basket-at-L20 runs, do not write that the dissociation is fully de-confounded"* is **partially** discharged — the arm has run, but at a **10-control family that could never certify**, TRAIN only. **The replacement rule is prohibition 23 below.** D13's own headline claim is **strengthened**, not contradicted |
| **AM-4** | **CORRECTION (arithmetic / denominator)** | **D12**'s caveat, **prohibition 19**, and **prohibition 20**, all three of which say the axis recovers *"3.9 % of the knockout"* | Two different denominators are being conflated. Measured from the artifacts: basket VALIDATION candidate **+0.00400** against the **knockout** `KO − BASE` = −0.22930 is **1.74 %**, and against **what the whole state restores** `KO_FULL − KO` = +0.10306 is **3.88 %** (the report's own `recovery_fraction_candidate_of_full` = 0.0388). **3.9 % is the whole-state denominator, not the knockout denominator.** D12's phrase *"recovers 0.0040 of a 0.229 knockout effect = 3.9 %"* is arithmetically wrong — 0.00400 / 0.22930 = 0.0174. The correct set, all first-hand: **basket L18 TRAIN** 0.00264 → 1.15 % of the knockout, **2.19 %** of the whole state; **basket L18 VALIDATION** 0.00400 → 1.74 %, **3.88 %**; **basket L20 TRAIN** 0.00294 → 1.25 %, **3.13 %**. **The direction of the error is conservative** (the true share of the knockout is *smaller* than the figure in circulation), so nothing that was said is overclaimed on this axis — but the sentence must not be repeated as written. Quote the fraction **with its denominator named**, every time |
| **AM-5** | **PROVENANCE AMENDMENT** | **D12**'s source column and one parenthetical | (a) D12's headline TRAIN figures (+0.00264, rank 1 of 47, p = 0.0213) come from **`reports/DCS_CSI_SUBSPACE_basket_train_n46.json`**, but the source column names `..._n34.json`, the **superseded** 34-control artifact whose figures D12's own text marks as superseded (+0.00265, rank 1 of 35). Cite **n46** for the TRAIN headline. (b) The caveat *"Both rank p values are at their attainable floors **(1/35, 1/31)**"* carries a stale numerator: at the 46-control family TRAIN's floor is **1/47 = 0.0213**. Both p-values **are** still at their floors; only the parenthetical is stale |
| **AM-6** | **OPERATIONAL — artifact integrity** | every row in this file that cites a `reports/*.json` artifact | S-124 found that both analysers use `json.dump(out, open(p, "w"))` with no explicit close, so on a full quota the `EDQUOT` is raised at GC finalisation, printed to stderr and **swallowed**: the script prints `wrote …` and **exits 0** having written a **0-byte file at a preregistered artifact name**. Two such files existed. **Consequence for this table**: an artifact's existence is not evidence it is complete — `json.load` it. The three artifacts new today were `json.load`-verified (478 798 B / 3 156 B / 121 796 B), and I re-verified all eight artifacts cited in A2 by `json.load` before writing these rows. The one-line fix is queued for S-128 and is **deliberately not applied**, because `score_behavior.py` may not be touched while the necessity arms run |

---

## D2. PROHIBITIONS ADDED 2026-09-20

Numbering continues section D. **The existing 22 prohibitions are unchanged**; 19, 20 and 21 are
additionally governed by AM-3 and AM-4 above.

23. **"Basket's axis passes at L20" / "the dissociation is now fully de-confounded."** — FORBIDDEN.
    Basket at L20 is **rank 1 of 11 with an attainable floor of 0.0909**; the analyser prints
    *"NOT a pass and NOT a failure"* and PR-CSI-002 predicted rank 1 of 11 **in writing before the
    data**. The defensible sentence is: *"basket is **top of its control distribution at both layers**
    and button is **inside its controls at both layers**, so the **layer** is refuted as the
    explanation"* — one candidate explanation removed, not a de-confounded conclusion. Extending the
    L20 family to 46 is the named, costed experiment that would change this.

24. **"Necessity shows the axis is necessary" / any necessity percentage attached to the axis.** —
    FORBIDDEN. D16 is the **whole-state** arm. Gate 3 was not evaluated, the control family did not
    exist when the number was read, and `ranks` is `{}`. **A candidate necessity figure of −0.00875
    was seen in stdout and is UNINTERPRETABLE**; it is written here only because a number that was
    seen must not be a number one pretends not to have seen. It must not be quoted as a result.
    Equally forbidden: comparing necessity's 47.0 % to any sufficiency percentage — necessity is at
    **L18**, PR-CSI-002's sufficiency read is at **L20**, and D15 is the whole reason that matters.

25. **Any captured-fraction figure called "energy", and any of the pair 0.03001 / 1.4012.** — the
    first is wrong by a square (AM-2), the second is a 213-row prefix of a live job (AM-1). Use
    **0.02820 / 1.36796** for basket at L20 and **0.03237 / 1.17153** for basket at L18, both over
    670 rows, both labelled **amplitude**.

---

## AUDIT — every existing row checked against today's results

Checked: D1–D13, E1–E2, C1–C4, prohibitions 1–22. Verdicts, with the entry that now governs each.

| row | verdict | note |
|---|---|---|
| D1 | **UNAFFECTED** | D16's manipulation `NEC_KO − NEC_BASE` = −0.23406 (basket, L18, 67/67) is a **different contrast** — ko vs **base**, where D1 is ko vs a dose-matched **ctrl** placebo band. Similar magnitude to D1's basket −0.2435; **do not equate them** |
| D2 | **UNAFFECTED, and load-bearing** | D2's L18/L20 **plateau** (basket 0.6525 / 0.6512) is what makes the layer swap in D15 a fair comparison rather than a handicap. Quote D2 whenever D15 is quoted |
| D3, D4, D5, D6, D7 | **UNAFFECTED** | nothing today touches the QPROBE validation figure, sentence-level generalisation, the behavioural endpoint, cross-architecture decoding, or the button run's mechanics |
| D8 | **UNAFFECTED, mildly strengthened** | D17 adds bit-identity of **670 readout rows across two SLURM jobs on one node**. That is run-to-run determinism, **not** the cross-node claim D8 makes; it does not touch D8's unexplained earlier build |
| D9, D10, D11 | **UNAFFECTED** | all three are **button** position/linearity results at L20; today's work adds no position-level measurement |
| **D12** | **NOT contradicted; 3 amendments** | **AM-4** (the "3.9 % of the knockout" denominator is wrong — it is 1.74 %), **AM-5** (source cites the superseded n34 artifact; "(1/35, 1/31)" is stale), **AM-2** (amplitude, not energy). Basket topping its family at a **second** layer (D14) is consistent with D12 and does not replicate it |
| **D13** | **STRENGTHENED; one caveat discharged** | **AM-3.** Its *"Only half the 2×2"* caveat is retired by D14/D15. Its claim — the dissociation is not explained by the layer — now rests on **both** diagonals rather than one |
| E1, E2 | **UNAFFECTED** | the refusal-recovery endpoint and the PLS rank question are untouched |
| C1 | **UNAFFECTED — and explicitly not answered by D16** | necessity is measured on **`y_install`**, not on refusal. Basket's behavioural endpoint is still at floor with one movable refusal event; D16 does **not** reopen C1 |
| C2, C3 | **UNAFFECTED** | |
| C4 | **UNAFFECTED** | the necessity arms still patch a **behavioural**-fit axis (`fit_prompt: behavioral` in every `basis_meta` I read); "is a semantic-fit axis causal?" remains deferred |
| prohibitions 1–18, 22 | **UNAFFECTED** | |
| **19, 20** | **governed by AM-4** | both repeat the conflated "3.9 % of the knockout"; the prohibitions themselves stand |
| **21** | **partially discharged; governed by AM-3 and replaced by prohibition 23** | the symmetric arm has now run, but floor-limited and TRAIN-only |

**The two questions this audit was specifically asked to answer:**

* **Does any existing row state or imply that the axis result is UNIFORM across codewords?**
  **No.** Rows D9–D11 are explicitly button-scoped, D12 is explicitly basket-scoped and names both
  splits, and prohibitions **19** and **21** already forbid the unqualified claim in as many words
  (*"the honest summary is a **codeword dissociation**"*). Nothing needed withdrawing on this count.
* **Does any existing row attribute the button/basket difference to the LAYER?**
  **No.** D13 is the only row that engages the layer hypothesis and it engages it to **refute** it for
  button; prohibition 21 flagged the missing symmetric arm rather than asserting a layer explanation.
  Today's result therefore **confirms** a position the table already held, and closes the gap the
  table itself had named.

---

## Commands run to produce this block, 2026-09-20

All read-only. No SLURM job launched, no file in `reports/` or `configs/` overwritten, no edit to
`src/boombness/score_behavior.py`.

```
# Artifact reads (json.load-verified, 8 reports):
#   DCS_CSI_SUBSPACE_{basket_train_L20, basket_train_n46, basket_validation_n30,
#                     button_train_rank1, button_validation, button_train_L18}.json
#   DCS_CSI_REDERIVE_basket_train_L20.json
#   DCS_CSI_PR003_GATE12_PARTIAL_HALF1.json

# Leave-one-domain-out, basket @ L20, re-run verbatim from the frozen read file:
python scripts/dcs_csi_rank_loo.py --tag-prefix csi1_basket_train --split train \
  --expect-n 670 --allow-short 4 --require-rescue-layer 20 --require-slurm-job 905990,906001
#   -> n_domains=67  full cand=+0.00293 rank=1 of 11; histogram {1: 67};
#      range +0.00249..+0.00311; 0 of 67 drops negative.

# Gate 0 bit-identity, recomputed by me from results.jsonl (not taken from S-125):
#   csi1_basket_train_KO_AXIS_20260917_222745_3184672  (job 905990, post-edit)
#   vs csi1_basket_train_KO_AXIS_ANCHOR_20260917_214756_3180097 (job 906001, pre-edit)
#   -> 670 common keys, 0 A-only, 0 B-only; max|diff| = 0.0 on all six readout fields;
#      config args 57 keys each, differing keys = {arm, tag}.

# Captured fraction / displacement, means over rescue_liveness across all 670 rows:
#   basket KO_AXIS @ L20 -> captured_frac 0.02820, delta_norm 1.36796
#   basket KO_AXIS @ L18 -> captured_frac 0.03237, delta_norm 1.17153
#   closest-prefix search for the superseded pair -> k = 213 of 670 gives
#   0.03001 / 1.40121 at relative-error sum 1.19e-04.
```

---
---

# APPENDED 2026-09-20 (second block) — sprint entries S-127 … S-134

**Nothing above this line has been altered, reworded or deleted.** Same additive convention as the
first appended block: an existing row that is now wrong gets an amendment row below that names it and
says why, and it keeps its original text. Verified mechanically before writing: the **218 lines above
are byte-identical** to the file as it stood at md5 `eee384beaf3c44130a7e53b1064c38cc` (40 981 B), and
that identity is re-checked by `diff` after this append.

Every number below was read by me out of the named artifact with `json.load`, or recomputed by me from
`results.jsonl` / the `.pt` bases, with the command given in the command block at the end. Numbers I
did **not** produce myself — the bootstrap Δz CIs, the Fisher exacts and the reweighting sweep, all of
which live only inside `reports/DCS_CSI_BUTTON_BASKET_DISSOCIATION_ANALYSIS.md` — are **labelled
`[READ, not reproduced]`** wherever they appear. Nothing here is taken from prose in the sprint log.

**Every comparison below prints the SIZE of the comparison beside its verdict** (S-134's rule: *a gate
that can pass on an empty comparison is not a gate*). The scripts that produced the rank cells and the
gate-0d cell `assert` the comparison size before any difference is believed; the assertions are shown
in the command block.

---

## A4. NEW ROWS — append to section A

| # | claim | statistic (with CI and n_domains) | population / split / codeword / layer | caveats | source |
|---|---|---|---|---|---|
| D18 | **NECESSITY, basket at L18: removing the rank-1 component from a CLEAN forward drops installation MORE than any of its controls** | `KO_NEC_AXIS − NEC_BASE` = **−0.00852**, ci95 **[−0.01127, −0.00592]**, **55 neg / 12 pos / 0 tied of 67 domains**. PRIMARY `candidate − comparator` (`KO_NEC_ORTH`) = **−0.00859** [−0.01131, −0.00603], same 55/12. **RANK 1 of 9 pooled** (`n_controls = 8`, `rank_p = rank_p_floor = 0.1111`); also **rank 1 of 5 shuffled-only** and **rank 1 of 5 random-only** (floor 0.2000 each) — comparison sizes 8 / 4 / 4, asserted non-empty before the rank was computed. The full control distribution, candidate first: **−0.00852** ≫ `SHUF3` −0.00478 · `SHUF2` −0.00317 · `RAND2` −0.00132 · `RAND3` −0.00025 · `RAND1` −0.00022 · `RAND0` +0.00001 · `SHUF1` +0.00002 · `SHUF0` +0.00013. Arm installation: `KO_NEC_AXIS` 0.46484 against `NEC_BASE` 0.47336, and **every one of the 8 controls sits within 0.005 of `NEC_BASE`** — the candidate is the only arm that moves. Holm one-sided specificity rejects **all 8** (`specificity_all_controls_rejected = true`; largest Holm p 8e−05) | **664 keys common to all 13 arms / 67 TRAIN domains**, basket, **L18**, direction `remove-under-clean`, reference arm `NEC_BASE`, basis `dcs_csi_axis_basket_behavioral_shuf24.pt` key `cand_rank1`, site `rel-6`, `fit_prompt: behavioral`, `semantic_one_word`, cell C, dose 4. SLURM **906433 + 912736**, all thirteen arms RTX 3090, eager/bf16 | **INCONCLUSIVE — FLOOR-LIMITED BY DESIGN, NOT A CERTIFIED RESULT.** With 8 controls the attainable rank-p floor is **0.1111**, above α = 0.05, so the analyser's PASS branch was **unreachable before the first arm ran**; its own verdict string says *"NOT a pass and NOT a failure"*. **TRAIN only**, and **in-sample** (`evaluation_is_in_sample: true`, `scored_domains_also_in_fit` 67/67 on all 13 arms). Every sign-flip p in the table is **at the Monte-Carlo sampler floor 5.00e−06** (200 000 draws; the exact floor 2⁻⁶⁷ ≈ 1.36e−20 is unreachable), so **no p here carries information beyond "the sampler saturated"**. The **identity gate is SKIPPED BY DESIGN** — no inert identity control exists for this direction (donor = clean, live = clean *is* the identity and the arm's own precondition refuses it); the four legs stand in its place and all pass: `necessity_violation_rows` **0** and `necessity_readout_knockout_edits` **0** on all 13 arms, `necessity_donor_delta_norm_min` **0.861038**, `necessity_patch_positions_min` **112**, `rescue_fired` 670, `decode_edits_total` 0. Three arms are short of 670 rows under the norm-match degeneracy guard — `KO_NEC_RAND0` 669, **`KO_NEC_RAND2` 666** (exactly on `--allow-short 4`), `KO_NEC_RAND3` 669. `VOID` list **empty**; `manipulation_check` and `instrument_capable` both true. Independently re-derived by `dcs_csi_rederive_subspace.py` (no shared analysis code): candidate **−0.00852** and **all 8 controls equal to the last printed digit**, same three ranks | **S-133** (`reports/DCS_CSI_SUBSPACE_NECESSITY_basket_train.json`, `reports/DCS_CSI_REDERIVE_NECESSITY_basket_train.json`) |
| D19 | **The BIDIRECTIONAL conjunction now exists for basket: the SAME rank-1 direction is top-of-family in BOTH directions, at the same codeword, layer and population** | **SUFFICIENCY** (add the component back under the live knockout), `KO_AXIS − KO`: TRAIN **+0.00264** [+0.00068, +0.00471], 44 pos / 23 neg of **67**, **rank 1 of 47**, p = **0.0213**; VALIDATION **+0.00401** [+0.00098, +0.00775], 15 pos / 8 neg of **23**, **rank 1 of 47**, p = **0.0213**. Subfamilies pass separately on **both** splits, recomputed by me: shuffled-only **1 of 25** (size 24, floor 0.0400), random-only **1 of 23** (size 22, floor 0.0435). **NECESSITY** (remove it from a clean forward), `KO_NEC_AXIS − NEC_BASE` = **−0.00852** [−0.01127, −0.00592], 55 of 67 domains negative, **rank 1 of 9** (D18). **The two directions use the SAME direction, and that is measured, not assumed**: the sufficiency arms load `configs/dcs_csi_axis_basket_behavioral.pt` (`basis_sha16 0c397a778db933ba`) and the necessity arms load `configs/dcs_csi_axis_basket_behavioral_shuf24.pt` (`basis_sha16 fad8b030ae93976e`) — **different files, different whole-file hashes — but their `cand_rank1` tensors are BIT-IDENTICAL**: shape (1, 4096), `max|diff| = 0.0`, `torch.equal` **True**, both `selected_layer` 18. Both directions carry the same `fit_domains_sha16 4614853e5636eb5f`, the same site `rel-6`, the same `fit_prompt: behavioral`, the same bank and the same L18 | sufficiency TRAIN 642 keys / **67 TRAIN domains**; sufficiency VALIDATION 215 keys / **23 held-out domains**; necessity 664 keys / **67 TRAIN domains**. basket, **L18** throughout, `semantic_one_word`, cell C, dose 4 | **THE AXIS MOVES ONLY 7.8 % OF WHAT WHOLE-STATE REMOVAL MOVES — 92 % OF THE EFFECT IS ELSEWHERE.** `removal_fraction_candidate_of_full` = **0.0778**, ci95 **[0.0560, 0.1009]**, i.e. −0.00852 / −0.10950 = 0.07781 (recomputed). This number must travel with the conjunction, every time. **The conjunction is NOT certified**: sufficiency clears its preregistered bar on held-out data, necessity **cannot clear any bar at `n_controls = 8`** because the bar is unreachable there (D18), so the two halves are **not equally strong**. Necessity is **TRAIN-only and in-sample**; sufficiency TRAIN is also in-sample (`evaluation_is_in_sample: true`) and only the **VALIDATION** cell is held out (`scored_domains_also_in_fit: 0`). **NO cross-direction fraction comparison is offered or permitted** — the two fractions are computed against different reference arms (`KO` vs `NEC_BASE`), and S-109 killed dose-normalised cross-comparisons for weaker reasons. **basket only**: nothing here has been run on button, and D21 is the reason not to assume it transfers | **S-133**, plan §6 (`reports/DCS_CSI_SUBSPACE_NECESSITY_basket_train.json`, `reports/DCS_CSI_SUBSPACE_basket_train_n46.json`, `reports/DCS_CSI_SUBSPACE_basket_validation_n46.json`) |
| D20 | **The instrument is capable in the REMOVAL direction — the positive control moves on every domain** | `KO_NEC_FULL − NEC_BASE` = **−0.10950**, ci95 **[−0.12482, −0.09451]**, **67 neg / 0 pos / 0 tied of 67 domains**. Manipulation on the same thirteen-arm key set, `NEC_KO − NEC_BASE` = **−0.23364** [−0.26346, −0.20408], **67 neg / 0 pos of 67**. Arm installation: `NEC_BASE` 0.47336 → `KO_NEC_FULL` 0.36386 → `NEC_KO` 0.23972. Fraction of the clean→KO span removed by the whole state = **0.46867** (−0.10950 / −0.23364), recomputed. Both contrasts re-derived independently to the same digits (**−0.10950** and **−0.23364**) by `dcs_csi_rederive_subspace.py` | **664 keys / 67 TRAIN domains**, basket, **L18**, whole-state donor patch (`rescue_basis: null` on the rows), `semantic_one_word`, cell C, dose 4; SLURM 906433 + 912736, RTX 3090 | **THIS IS THE WHOLE-STATE CONTROL, NOT THE AXIS** — it licenses only the sentence *"a removal-direction effect is detectable by this instrument"*. Both p values are **at the MC sampler floor 5.00e−06** and carry no information. It **supersedes D16's `−0.11009` only in key set, not in fact**: D16 read 670 keys over **5** arms, this reads **664** keys over **13**; the 6-key difference is the intersection with the eight new control arms, and `keys_dropped_by_intersection = 6`. Likewise D16's *"47.0 %"* of the clean→KO span becomes **46.9 %** at 664 keys. **Not a disagreement, and neither figure is withdrawn** | **S-133** (`reports/DCS_CSI_SUBSPACE_NECESSITY_basket_train.json`, `reports/DCS_CSI_REDERIVE_NECESSITY_basket_train.json`) |
| D21 | **The button/basket dissociation is REAL at MATCHED control-family size, composition, domains and prompts — it is not bought with extra controls** | Restricting basket's 46-control family to the **identical ten arm names button was run with** (`KO_RAND0..5`, `KO_SHUF0..3` — same 6 random / 4 shuffled composition), recomputed by me with the family size asserted at exactly 10 in every cell: **basket L18 TRAIN 1 of 11** (cand +0.00264 vs best control +0.00215, 0 exceedances); **basket L18 VALIDATION 1 of 11** (+0.00401 vs +0.00278, 0 exceedances); **basket L20 TRAIN 1 of 11** (+0.00294 vs +0.00129, native 10-control family). Against **button L20 TRAIN 4 of 11** (+0.00040 vs +0.00159, **3** exceedances); **button L20 VALIDATION 4 of 11** (+0.00132 vs +0.00266, **3**); **button L18 TRAIN 8 of 11** (**−0.00027** vs +0.00151, **7**). Attainable floor 0.0909 in all six cells, so **all six are the same test**. Standardised, family-size-free: `[READ, not reproduced]` z = +1.939 (basket TRAIN matched-10), +3.567 (basket VAL matched-10), +5.011 (basket L20), vs button 0.443 / 0.441 / −0.373 | six cells: basket L18 TRAIN 642 keys / 67 dom · basket L18 VAL 215 keys / 23 dom · basket L20 TRAIN 657 keys / 67 dom · button L20 TRAIN 666 keys / 67 dom · button L20 VAL 229 keys / 23 dom · button L18 TRAIN 658 keys / 67 dom. Populations are matched at the input: `fit_domains_sha16 = 4614853e5636eb5f` in all six, identical `domain_means` key sets, 670 family keys each with intersection 670 at prompt level `[READ, not reproduced]` — **the arms differ in exactly one input token** | **THREE caveats, two of which WEAKEN it, and all three must travel with the headline.** **(1) The TRAIN own-layer cell — the one the headline is usually quoted from — is the WEAKEST evidence in the set**: its paired-domain-bootstrap Δz CI **includes zero**, +2.023 [−0.226, +4.288], and its matched-10 Fisher exact is **p = 0.1053** `[READ, not reproduced]`. The dissociation is carried by the **held-out split** (Δz +4.209 [+0.630, +7.078]; matched-10 +2.871 [+0.267, +4.977]) and by the **shared-layer L18** comparison (Δz +2.832 [+0.606, +5.057], Fisher **p = 0.0015**) — **not** by the TRAIN headline. **(2) Basket's TRAIN rank-1 is NOT robust to per-domain reweighting**: under family-wide logit re-expression with trimming, **two of five schemes move it from rank 1 of 47 (p = 0.0213) to rank 3 of 47 (p = 0.0638)** — from PASSES to does-not-pass at α = 0.05. VALIDATION and basket@L20 are rank 1 under **all five** `[READ, not reproduced]`. **(3) NOTHING EXPLAINS IT.** Six candidate explanations removed by measurement (unequal families, headroom, population, axis geometry/dose, power, and C6 which **REVERSES** — button's axis tracks the causal carrier *better* and rescues *worse*), one **partial** (power contributes 1.2–2.4× of a **4.3–5.6× z gap**), and **exactly one survivor, unquantified**: C1, *"basket simply has a better probe"* — rank-1 LOO ρ **0.5629 vs 0.5021**, a **+12 % relative** gap that would have to explain the 4.3–5.6× z gap, with **no held-out ρ recorded anywhere (CANNOT MEASURE)** and **no ρ→z calibration anywhere in this sprint**. **The residual is still the codeword.** Also **TRAIN-only on the button-L18 side** — no button-L18 VALIDATION arm has ever been run | **S-128**, corrected by **S-131** (`reports/DCS_CSI_BUTTON_BASKET_DISSOCIATION_ANALYSIS.md` and the six `DCS_CSI_SUBSPACE_*.json` cells) |
| D22 | **PR-CSI-005 gate 0d PASSES: the +474/−7 `score_behavior.py` change is INERT on the norm-matched sufficiency path — measured, not argued** | `CODEANCHOR_R0` (job **912838**, node **n-350**, repo commit `dabfeb854ec6`, clean tree) vs `KO_RAND0` (job **902005**, node **n-306**, repo commit `bc8e77793633`, **`git_dirty = true`**): **670 rescue-fired rows each, 670 common keys, 0 A-only, 0 B-only**, and `max|diff| = 0` with **`nonzero_rows = 0 / 670`** on **all six** readout fields — `logp_concept`, `logp_codeword`, `semantic_logodds`, `p_concept`, `p_codeword`, `top1_id`. Both arms: `rescue_layer` 18, `rescue_basis_key` `ctrl_random0`, `rescue_norm_match_key` `cand_rank1`, `rescue_donor` clean, both on RTX 3090. The diff being tested is `git diff bc8e77793633 -- src/boombness/score_behavior.py` = **+474 / −7** (measured), against the current blob **`e94258bd5fc44c70629e707b00504b7acac2a7b7`** (measured, and equal to `HEAD:src/boombness/score_behavior.py`) | **670 rows / 67 TRAIN domains**, button, **L18**, `semantic_one_word`, cell C, dose 4, `ctrl_random0` arm | This discharges **one** VOID condition for **PR-CSI-005's pooled family only** — it is **not** a general licence to edit `score_behavior.py` mid-run, and the `score_behavior.py` **release point has NOT arrived** (PR-CSI-005's own VOID list includes blob drift off `e94258bd…` and its 36 arms are mid-flight). **Two things came free and neither was designed for**: the comparison is **cross-node (n-306 vs n-350)**, so it independently re-confirms cross-node bit-determinism for button on a second node pair; and because the anchor ran at commit `dabfeb85` — *after* the S-124/S-130 138-site atomic-write fix landed — it also proves **that** fix inert on the **producer** path by bit-identity of 670 rows (S-130 had proved it inert only on the **analyser** path). **PR-CSI-005 Part 3 remains SEALED**; this is Part 2, explicitly evaluable before any number is read, and **no interim read of the 36 arms was performed**. **The near-miss is part of the record**: the first version of this gate selected rows on a field name that does not exist (`rescue_positions_written` instead of `rescue_liveness.fired`), matched **0** rows, and printed **PASS** — caught only because the printout carried the comparison size next to the verdict | **S-134**, recomputed first-hand 2026-09-20 (see command block) |

---

## A5. AMENDMENTS — corrections to rows above, additive and marked

Each amendment names the row it governs. **The original row is unchanged and still readable**; read the
row and its amendments together. Numbering continues from AM-6.

| id | marker | governs | what changed, and why |
|---|---|---|---|
| **AM-7** | **CORRECTION (superseded artifact)** | **D12** (its VALIDATION figures, its key count and its source column), **D15** (the `basket, own layer L18` VALIDATION cell), and **AM-5**, which corrected D12's *TRAIN* citation but left the VALIDATION one standing | **Any row citing basket VALIDATION as *"+0.00400, rank 1 of 31, p = 0.0323, 218 keys"* is reading the SUPERSEDED `reports/DCS_CSI_SUBSPACE_basket_validation_n30.json` (30 controls).** The **authoritative** held-out read is **`reports/DCS_CSI_SUBSPACE_basket_validation_n46.json`**: candidate **+0.00401**, ci95 **[+0.00098, +0.00775]**, 15 pos / 8 neg of 23 domains, **rank 1 of 47**, rank p = **0.0213**, **215 keys / 23 domains** — the **same 46-control family as TRAIN**, which is the only thing that makes the two splits comparable. Three validation reads exist and the middle one was quoted; measured side by side: `..._validation.json` 10 ctrl / +0.00406 / 1 of 11 / 0.0909 / 225 keys · `..._validation_n30.json` 30 ctrl / +0.00400 / 1 of 31 / 0.0323 / 218 keys · **`..._validation_n46.json` 46 ctrl / +0.00401 / 1 of 47 / 0.0213 / 215 keys**. **The correction moves the result in the direction that STRENGTHENS it** — the floor drops from 0.0323 to 0.0213 and the candidate is unchanged to 5 dp. D12's subfamily claim is **confirmed at n46 on BOTH splits**, recomputed by me: shuffled-only **1 of 25** (size 24, floor 0.0400) and random-only **1 of 23** (size 22, floor 0.0435), TRAIN *and* VALIDATION. **Cite n46 for both splits; the n30 file is superseded and the 10-control file doubly so.** Note also that D12's caveat *"rank 1 of 13 (floor 0.0769) TRAIN and rank 1 of 9 (floor 0.1111) VALIDATION"* describes the **superseded** small shuffled families and is stale in the same way AM-5 found its `(1/35, 1/31)` parenthetical stale — the verdict *"INCONCLUSIVE on its own"* no longer holds at n46, where the shuffled-only floor is 0.0400 and the shuffled-only rank is 1 on both splits (S-128) |
| **AM-8** | **CORRECTION (arithmetic, twice)** | **D16**'s closing caveat — *"The attainable floor even with half 2 is **1/10 = 0.10**, so the analyser's PASS branch is unreachable by design"* — **prohibition 24**, and `runargs/dcs_csi_pr003_read.txt` lines 59–61, which state the same thing | **(a) The necessity floor is 0.1111, not 0.10, and the control count is 8, not 9.** `KO_NEC_ORTH` is **not matched** by the frozen read's mandatory `--control-prefixes KO_NEC_SHUF,KO_NEC_RAND`, so it never enters the control distribution: verified at the source (`scripts/dcs_csi_subspace_analyze.py:916` builds `ctrl_arms` by `str.startswith` on those prefixes; `:961` sets `rank_p_floor = round(1/(len(ctrl_rec)+1), 4)`) and by direct evaluation — **`"KO_NEC_ORTH".startswith(("KO_NEC_SHUF","KO_NEC_RAND")) is False`**. The committed read confirms it: `n_controls = 8`, `rank_p_floor = 0.1111`. **No verdict moves** (0.1111 and 0.10 are both ≫ 0.05) and the *conclusion* that the PASS branch was unreachable in advance is **unaffected and if anything more true** — but a stated floor the tool will not print is an assertion about a computation made without running the computation. **(b) "at least 19 controls" is off by one; the correct number is 20.** The analyser formats its INCONCLUSIVE text with a hardcoded `min_controls=19` (`:1026`) while the gate it describes is `attainable = dist["rank_p_floor"] < 0.05` (`:1018`), and **`round(1/20, 4) = 0.05` is NOT `< 0.05`** while `round(1/21, 4) = 0.0476` **is** — both evaluated by me. So K = 19 controls still prints INCONCLUSIVE and **K ≥ 20 is required**; the string is now visible inside a committed artifact (`DCS_CSI_SUBSPACE_NECESSITY_basket_train.json` → `VERDICT`). **REPORTED, NOT FIXED** — editing an analyser immediately after a committed read is the S-110c defect, and the analysers may not be touched while PR-CSI-005's 36 arms are in flight. This is a **defect in a tool's description of itself**, not in any number it computed |
| **AM-9** | **CORRECTION (prefix-of-a-live-job + units) — RESTATED and SCOPED** | **AM-1**, **AM-2** and **prohibition 25**, which already govern this, plus any future row that reaches for the pair | **The pair *"captured fraction 0.03001 / displacement 1.4012"* for basket at L20 is a PREFIX MEAN OVER THE FIRST 213 OF 670 ROWS of a job that was still running, and must not be used.** The full-population values are **captured fraction 0.02820, `delta_norm` 1.36796** over **670 of 670 rows** (basket `KO_AXIS` @ L20), and **0.03237 / 1.17153** over 670 rows at L18. **Both are AMPLITUDE, not energy** — `src/boombness/donor_patch.py` computes `captured_energy_frac_mean` as a mean of per-row `proj_norm / delta_norm`, a ratio of **norms**, despite the key name; the energy fraction is the square, of order **0.1 %**, and because the persisted field is a mean of ratios the exact mean energy fraction is **NOT recoverable** from it. **Scope, measured rather than assumed:** `grep` over this file finds the pair `0.03001` / `1.4012` in **exactly three places — AM-1, prohibition 25 and the first block's command log — and in ZERO rows of sections A, A2 or A4.** So this amendment adds no new correction to any claim row; it exists so that the rule is restated beside the new material rather than left three hundred lines up the file, and so that `0.03001 / 1.4012` never re-enters through a new row |

---

## D3. PROHIBITIONS ADDED 2026-09-20 (second block)

Numbering continues section D and D2. **The existing 25 prohibitions are unchanged**; 24 is
additionally governed by AM-8 and by prohibition 26 below.

26. **"Necessity is established" / "the axis is necessary" / "removal along the axis is certified."** —
    FORBIDDEN. **Prohibition 24's premise has changed — the read has now happened (D18) — and its
    conclusion has not.** What is now sayable, and the only thing that is: *"removing the rank-1
    component from a clean forward produces the largest installation drop in its control family —
    rank 1 of 9, on 55 of 67 domains — and the comparison is floor-limited to INCONCLUSIVE at an
    attainable floor of 0.1111 that was declared before the first arm ran."* Three clauses that must
    not be dropped from it: **floor-limited**, **TRAIN-only**, **in-sample**. Prohibition 24's ban on
    the stdout figure **−0.00875** stands as a matter of record — that number was never an artifact
    figure; **the artifact figure is −0.00852 on 664 keys**, and the two must not be conflated or the
    earlier one quoted. Prohibition 24's ban on comparing necessity's whole-state percentage to any
    sufficiency percentage **also stands, unchanged and for a second reason**: D19 measures the two
    directions at the **same** layer now, so the S-125/D15 layer objection no longer applies — but the
    two fractions still have **different reference arms** (`KO` vs `NEC_BASE`), which is by itself
    disqualifying.

27. **"Basket is rank 1 of 47 and button is rank 4 of 11"** quoted **without** the matched-family
    figure beside it. — FORBIDDEN. Those two are **not the same test** (floors 0.0213 vs 0.0909) and
    quoting them alone invites exactly the objection D21 was built to answer. The defensible form
    always carries the matched-10 pair: **"at the identical ten control arms, basket is rank 1 of 11
    and button is rank 4 of 11 — on both splits, and 1 of 11 vs 8 of 11 at the shared layer L18."**
    And it carries D21's caveat 1: **the TRAIN own-layer cell is the weakest evidence in the set**
    (Δz CI includes zero, matched Fisher p = 0.1053); lead with **VALIDATION** and with the
    **shared-layer L18** comparison.

28. **"The axis is the causal carrier" / any necessity result quoted without the 7.8 %.** — FORBIDDEN.
    The axis removal moves **0.0778 [0.0560, 0.1009]** of what whole-state removal moves, so **92 % of
    the removable effect is elsewhere**. The bidirectional conjunction (D19) is a statement about
    **one direction being top-of-family in both directions**, not about that direction carrying the
    effect.

---

## AUDIT — every existing row re-checked against S-127 … S-134

Checked: D1–D17, E1–E2, C1–C4, AM-1–AM-6, prohibitions 1–25. Verdicts, with the entry that now
governs each. **Rows not listed were checked and are UNAFFECTED.**

| row | verdict | note |
|---|---|---|
| D1, D2, D3, D4, D5, D6, D7, D8 | **UNAFFECTED** | D2 stays **load-bearing** for exactly the reason the first block gave: the L18/L20 ρ plateau is what makes the layer swap in D15 and the shared-layer L18 comparison in D21 fair rather than a handicap. Quote D2 whenever D21 is quoted |
| D9, D10, D11 | **UNAFFECTED** | all three are button position/linearity results at L20; nothing in S-127…S-134 adds a position-level measurement |
| **D12** | **STRENGTHENED on the VALIDATION side; a 4th amendment** | **AM-7.** Its VALIDATION figures (+0.00400, rank 1 of 31, p = 0.0323, 218 keys) are the **superseded n30 read**; authoritative is +0.00401, **rank 1 of 47, p = 0.0213, 215 keys**. The correction **lowers the floor** and leaves the candidate unchanged to 5 dp, so D12's headline is **strengthened, not weakened**. Its subfamily claim (shuffled-only 1 of 25, random-only 1 of 23) is **confirmed by me on both splits at n46**. Its caveat *"shuffled-only … rank 1 of 9 (floor 0.1111) VALIDATION … INCONCLUSIVE on its own, both splits"* describes the superseded small families and is **stale**. D12 already carries AM-2, AM-4 and AM-5 |
| **D13** | **STRENGTHENED further** | D21 adds what D13 could not have: the button-at-L18 cell is not merely *"8 of 11"* but **8 of 11 against a basket cell restricted to the identical ten arm names, which is 1 of 11** — and the shared-layer L18 comparison is the **strongest** cell in the dissociation set (Δz +2.832 [+0.606, +5.057], Fisher p = 0.0015), not the weakest. D13's *"TRAIN only — button has no held-out L18 arms"* caveat **still stands and is not discharged** |
| **D14, D15** | **NOT contradicted; D15 carries AM-7; one WORDING correction inherited** | **(a)** D15's VALIDATION cell quotes the superseded n30 read (**AM-7**). **(b)** S-127 corrects the *wording* of the 2×2 across D14/D15: every cell uses a probe **REFIT at that layer** — **four different `.pt` files** — not one axis transported. **The numbers, verdicts and claims are unaffected and the corrected reading is the STRONGER one**: a refit probe controls for *"wrong layer for this direction"*, which a transported axis would confound. Future citations must say **"basket's probe, refit at L20"**, never *"basket's axis at button's layer"*. **(c)** S-127 also records, and I am not waving it away, that the four probes differ in `selected_rank` by codeword (**5** for both button axes, **3** for both basket axes) while the candidate arm is `cand_rank1` in every cell — **NOT ESTABLISHED** whether that matters, and it is precisely the asymmetry that could masquerade as a codeword effect. It is handed to D21's surviving explanation C1 |
| **D16** | **NOT contradicted; 2 amendments; its central caveat is now DISCHARGED by D18** | **AM-8** (the floor is **0.1111** at **8** controls, not 1/10 at 9; and the "≥ 19 controls" in the tool's own string is off by one — 20 is required). **D20** supersedes its `−0.11009` **in key set only** (670 keys / 5 arms → **664** keys / **13** arms → **−0.10950**; its 47.0 % becomes **46.9 %**) — *not a disagreement, and neither figure is withdrawn*. D16's caveat *"It says **nothing** about whether the rank-1 axis carries that effect — Gate 3 was deliberately not evaluated, `ranks` is `{}`, and the 9 control arms were still running"* is now **DISCHARGED**: the arms landed, the ranks exist, and the answer is **rank 1 of 9** (D18). D16's other caveat — *"do not compare 47.0 % to any sufficiency percentage because necessity is at L18 and the sufficiency read is at L20"* — has **lost its stated reason** (D19 compares at the **same** L18) but **keeps its force** for a different and stronger reason: different reference arms. See prohibition 26 |
| **D17** | **UNAFFECTED, and STRENGTHENED by an independent instance** | D17 retired PR-CSI-002's Gate-0 VOID condition by 670-row bit-identity across two jobs on **one** node. **D22 is the same shape on a second, harder case**: 670 rows bit-identical **across two nodes** (n-306 vs n-350) and across a **+474/−7** change to `score_behavior.py`. D17's own scope limit is untouched — it remains same-node determinism — and D22 does **not** generalise either result into a licence to edit that file mid-run |
| E1, E2 | **UNAFFECTED** | the refusal-recovery endpoint and the PLS rank question are untouched. **E2 gains one relevant number**: D21's surviving explanation C1 is stated in E2's own currency — rank-1 LOO ρ **0.5629** (basket) vs **0.5021** (button), and E2 already records button's r1 as 0.5021 |
| **C1** | **UNAFFECTED — and explicitly NOT answered by D18/D19/D20** | necessity is measured on **`y_install`**, a concept-free one-word readout, **not on refusal**. Basket's behavioural endpoint is still at floor with one movable refusal event in 180 rows. Nothing in this block reopens C1 |
| C2, C3 | **UNAFFECTED** | |
| **C4** | **UNAFFECTED** | the necessity arms patch a **behavioural**-fit axis — `basis_meta.fit_prompt = "behavioral"` read directly off `KO_NEC_AXIS` — so *"is a semantic-fit axis causal?"* remains **deferred, not withdrawn** |
| AM-1, AM-2 | **UNAFFECTED; restated and scoped by AM-9** | measured: the pair `0.03001` / `1.4012` appears in **zero** rows of sections A, A2 and A4 |
| AM-3 | **UNAFFECTED** | |
| AM-4 | **UNAFFECTED and still binding** | D19 and D21 quote fractions **with the denominator named** in every instance, per AM-4 |
| **AM-5** | **COMPLETED by AM-7** | AM-5 corrected D12's **TRAIN** citation (n34 → n46) and left the **VALIDATION** citation (n30) standing. AM-7 closes that half |
| **AM-6** | **UNAFFECTED, and DISCHARGED as a live hazard** | the 0-byte-write bug AM-6 describes is **FIXED at 138 sites** (S-130), with a regression test **proven to fail on the old code**, and D22 independently proves the fix **inert on the producer path** by 670-row bit-identity. **AM-6's operational rule stands regardless**: an artifact's existence is not evidence it is complete. **Every artifact cited in A4 and A5 was `json.load`-verified by me before these rows were written** |
| prohibitions 1–23, 25 | **UNAFFECTED** | |
| **24** | **premise changed, conclusion intact; governed by AM-8, replaced in part by prohibition 26** | the necessity read has happened and the candidate is **not** the uninterpretable stdout figure. The ban on quoting **−0.00875** stands; the artifact figure is **−0.00852**. The ban on cross-direction percentage comparison stands **for a new reason** (different reference arms, not different layers) |

**The three questions this audit was specifically asked to answer:**

* **Does any existing row state or imply that the axis result is UNIFORM across codewords?**
  **No — and the new rows do not either.** D9–D11 are explicitly button-scoped; D12, D14, D16 are
  explicitly basket-scoped; D15 and D13 exist to *contrast* the codewords; prohibitions 19 and 21
  already forbid the unqualified claim. The new **D18/D19/D20 are basket-only and say so in their
  claim text**, and **D21 plus prohibition 27** make the dissociation harder to elide, not easier.
  **Nothing needed withdrawing on this count.**
* **Does any existing row attribute the button/basket difference to the LAYER?**
  **No.** D13 is the only row that engages the layer hypothesis and it engages it to **refute** it;
  D15 completes the 2×2 and exonerates the layer; prohibition 21 flagged the missing symmetric arm
  rather than asserting a layer explanation. **S-127 corrects the *wording* of D14/D15** (refit, not
  transported) and the corrected reading is the stronger one. **D21 strengthens the refutation
  further**: at the **shared layer L18**, with **matched ten-control families**, basket is 1 of 11 and
  button is 8 of 11 — a same-layer, same-family, same-domain contrast in which the layer is held
  fixed by construction.
* **Does any existing row treat NECESSITY as untested?**
  **Yes — and it is now amended rather than reworded.** **D16**'s caveat (*"Gate 3 was deliberately
  not evaluated, `ranks` is `{}`, and the 9 control arms were still running when this row was
  written"*) and **prohibition 24** were both written while the arms were in flight. Both are
  **correct as of their writing and superseded as of S-133**: the arms landed, `ranks` is populated,
  and the answer is **rank 1 of 9, floor-limited to INCONCLUSIVE** (D18). Neither is reworded;
  **D18, AM-8 and prohibition 26 govern them.**

---

## Commands run to produce this block, 2026-09-20

All read-only. **No SLURM job launched** (912835 / 912836 / 912837 untouched); **no analyser run**
(`dcs_csi_subspace_analyze.py` / `dcs_csi_rederive_subspace.py` never invoked — PR-CSI-005 Part 3
stays sealed); **no edit** to `src/boombness/score_behavior.py`, `slurm_scripts/dcs_csi_p1_arms.slurm`,
any script in `scripts/`, or any file in `configs/` or `runargs/`. The **only** file written is
`reports/DCS_CSI_CLAIM_TABLE.md`, and only by appending this block.

```
# --- artifacts read with json.load (9), all verified non-empty and parseable ---
#   DCS_CSI_SUBSPACE_NECESSITY_basket_train.json      372 417 B
#   DCS_CSI_REDERIVE_NECESSITY_basket_train.json        3 368 B
#   DCS_CSI_SUBSPACE_basket_train_n46.json          1 746 043 B
#   DCS_CSI_SUBSPACE_basket_validation_n46.json       705 625 B
#   DCS_CSI_SUBSPACE_basket_validation_n30.json  (for AM-7's side-by-side only)
#   DCS_CSI_SUBSPACE_basket_validation.json      (for AM-7's side-by-side only)
#   DCS_CSI_SUBSPACE_basket_train_L20.json            478 798 B
#   DCS_CSI_SUBSPACE_button_train_rank1.json          438 718 B
#   DCS_CSI_SUBSPACE_button_validation.json           180 750 B
#   DCS_CSI_SUBSPACE_button_train_L18.json            471 680 B

# --- D21 / AM-7: rank at the MATCHED ten-control family, recomputed ---
# The gate asserts the comparison size BEFORE any rank is believed (S-134):
#     assert len(sub) == 10 ; assert sorted(sub) == sorted(BUTTON10)
#     assert d["n_domains"] > 0 and d["n_keys_common"] > 0
# BUTTON10 = KO_RAND0..5 + KO_SHUF0..3
#   basket L18 TRAIN       n_dom= 67 n_keys=642  SIZE=10  cand=+0.00264 best=+0.00215 exceed=0 -> RANK 1 of 11
#   basket L18 VALIDATION  n_dom= 23 n_keys=215  SIZE=10  cand=+0.00401 best=+0.00278 exceed=0 -> RANK 1 of 11
#   basket L20 TRAIN       n_dom= 67 n_keys=657  SIZE=10  cand=+0.00294 best=+0.00129 exceed=0 -> RANK 1 of 11
#   button L20 TRAIN       n_dom= 67 n_keys=666  SIZE=10  cand=+0.00040 best=+0.00159 exceed=3 -> RANK 4 of 11
#   button L20 VALIDATION  n_dom= 23 n_keys=229  SIZE=10  cand=+0.00132 best=+0.00266 exceed=3 -> RANK 4 of 11
#   button L18 TRAIN       n_dom= 67 n_keys=658  SIZE=10  cand=-0.00027 best=+0.00151 exceed=7 -> RANK 8 of 11
#   (floor 1/11 = 0.0909 in all six -- the same test in every cell)

# --- D12 / AM-7: subfamily ranks at n46, recomputed on BOTH splits ---
#   basket_train_n46       shuffled_only SIZE=24 -> RANK 1 of 25 (floor 0.0400)
#   basket_train_n46       random_only   SIZE=22 -> RANK 1 of 23 (floor 0.0435)
#   basket_validation_n46  shuffled_only SIZE=24 -> RANK 1 of 25 (floor 0.0400)
#   basket_validation_n46  random_only   SIZE=22 -> RANK 1 of 23 (floor 0.0435)

# --- AM-7: the three basket VALIDATION reads, side by side ---
#   basket_validation      n_ctrl=10 rank 1 of 11 floor 0.0909 rank_p 0.0909 cand +0.00406 n_keys=225
#   basket_validation_n30  n_ctrl=30 rank 1 of 31 floor 0.0323 rank_p 0.0323 cand +0.00400 n_keys=218
#   basket_validation_n46  n_ctrl=46 rank 1 of 47 floor 0.0213 rank_p 0.0213 cand +0.00401 n_keys=215  <- AUTHORITATIVE

# --- D18 / D20: necessity ranks and fractions, recomputed with size assertions ---
#   pooled        SIZE=8 cand=-0.00852 most-neg ctrl=-0.00478 -> RANK 1 of 9 floor=0.1111
#   shuffled_only SIZE=4 cand=-0.00852 most-neg ctrl=-0.00478 -> RANK 1 of 5 floor=0.2000
#   random_only   SIZE=4 cand=-0.00852 most-neg ctrl=-0.00132 -> RANK 1 of 5 floor=0.2000
#   candidate/full = -0.00852 / -0.10950 = 0.07781   (artifact removal_fraction 0.0778 [0.0560, 0.1009])
#   full/manip     = -0.10950 / -0.23364 = 0.46867   (D16's 47.0 % at 664 keys)
#   re-derivation: candidate -0.00852 identical; 8 of 8 controls identical; same three ranks
#   VOID [] | gates {manipulation_check: true, instrument_capable: true} | 8 of 8 Holm-rejected
#   four legs, all 13 arms: violation_rows 0, readout_knockout_edits 0,
#                           donor_delta_norm_min 0.861038, patch_positions_min 112
#   rows: 670 on ten arms; KO_NEC_RAND0 669, KO_NEC_RAND2 666, KO_NEC_RAND3 669

# --- D19: are the two directions the SAME direction? measured, not assumed ---
#   sufficiency arms load configs/dcs_csi_axis_basket_behavioral.pt        basis_sha16 0c397a778db933ba
#   necessity   arms load configs/dcs_csi_axis_basket_behavioral_shuf24.pt basis_sha16 fad8b030ae93976e
#   torch.load both -> bases["cand_rank1"]: shape (1, 4096) both
#     max abs diff = 0.0 ; torch.equal = True ; meta.selected_layer = 18 / 18
#   => the differing basis_sha16 is a WHOLE-FILE hash, not the candidate tensor's.

# --- D22: GATE 0d recomputed by me from results.jsonl (not taken from S-134) ---
#   A csi1_button_train_CODEANCHOR_R0_20260920_135631_905054  job 912838 n-350 dabfeb854ec6 dirty=None
#   B csi1_button_train_KO_RAND0_20260916_223555_2963342      job 902005 n-306 bc8e77793633 dirty=True
#   both: rescue_layer 18, key ctrl_random0, normkey cand_rank1, donor clean, RTX 3090
#   rows selected on rescue_liveness.fired (NOT the nonexistent rescue_positions_written -- S-134)
#   non-vacuity asserted before any diff: assert fa >= 600; assert fb >= 600;
#     assert len(common) >= 600; and for each field assert present == len(common)
#   COMPARISON SIZE: A fired=670  B fired=670  common keys=670  A-only=0  B-only=0
#     logp_concept / logp_codeword / semantic_logodds / p_concept / p_codeword / top1_id
#     max|diff| = 0   nonzero_rows = 0 / 670   on all six
#   GATE 0d: PASS -- all six bit-identical on all 670 compared rows
#   git diff --numstat bc8e77793633 -- src/boombness/score_behavior.py   ->  474  7
#   git hash-object src/boombness/score_behavior.py -> e94258bd5fc44c70629e707b00504b7acac2a7b7
#   git rev-parse HEAD:src/boombness/score_behavior.py -> e94258bd5fc44c70629e707b00504b7acac2a7b7  (equal)

# --- AM-8: the floor and the off-by-one, evaluated rather than asserted ---
#   scripts/dcs_csi_subspace_analyze.py:916  ctrl_arms built by startswith(control_prefixes.split(","))
#   scripts/dcs_csi_subspace_analyze.py:961  "rank_p_floor": round(1.0/(len(ctrl_rec)+1), 4)
#   scripts/dcs_csi_subspace_analyze.py:1018 attainable = dist["rank_p_floor"] < 0.05
#   scripts/dcs_csi_subspace_analyze.py:1026 ... min_controls=19   (hardcoded in the message only)
#   "KO_NEC_ORTH".startswith(("KO_NEC_SHUF","KO_NEC_RAND")) -> False
#   round(1/9,4) = 0.1111 ; round(1/10,4) = 0.1
#   round(1/20,4) < 0.05 -> False ; round(1/21,4) < 0.05 -> True   => K >= 20, not 19

# --- AM-9 scope: where the superseded pair actually appears in this file ---
#   grep -n '0\.03001\|1\.4012' reports/DCS_CSI_CLAIM_TABLE.md
#     -> AM-1 (line 117), prohibition 25 (line 147), first block's command log (line 217)
#     -> ZERO hits in any row of sections A, A2, A4.
```

**Append verified per S-124 (EDQUOT is asynchronous; exit status is not evidence):** line count
**218 → 461** (+243, **0 deletions**), byte count **40 981 → 80 923**; `diff <(head -218 <new>) <old>`
returns **empty** and `grep -c '^| D'` confirms every pre-existing row is still present verbatim.

**Two things I believe need an edit and did NOT edit, reported instead, per the standing freeze:**
(1) `scripts/dcs_csi_subspace_analyze.py:1026`'s hardcoded `min_controls=19` is wrong — the gate at
`:1018` requires **K ≥ 20** (AM-8b), and the wrong string is now inside a committed artifact.
(2) `runargs/dcs_csi_pr003_read.txt` lines 59–61 state the necessity floor as `9 controls => 1/10 = 0.10`;
the analyser computes **8 controls, floor 0.1111** (AM-8a). Both are **descriptions**, not computations,
so **no committed number is affected** by either.

---
---

# APPENDED 2026-09-20 (third block) — sprint entries S-137 … S-143 and REVIEW R10

**Nothing above this line has been altered, reworded or deleted.** Same additive convention as the
first two appended blocks. Verified mechanically before writing: the **461 lines above are
byte-identical** to the file as it stood at md5 `e0b0074baf990b89977f9f03565a0b5b` (80 923 B), which
is the file as committed at `ad1288d6` (sprint entry **S-135**) — this block closes the gap
**S-137, S-138, REVIEW R10, S-139, S-141, S-142, S-143**. The identity is re-checked by `diff` after
this append.

## READ THIS FIRST — the one thing this block exists to get right

**S-138 was committed with the headline *"C1 is SUPPORTED and the STATE hypothesis is REFUTED"*.
REVIEW R10 WITHDREW that headline as BLOCKER-1.** It is recorded here **only** as `AM-10`, an
explicitly-marked WITHDRAWN amendment. **It does not appear as a live claim row anywhere in this
file and must never be entered as one.** What the claim row (`D25`) records instead is the
**preregistration's own output**: **CELL 4 on TRAIN, direction B NOT REPLICATED, C1 REFUTED by the
fixed rule.** The rank-36 → rank-4 contrast and the probe main effect are real and are recorded as
**SECONDARY, UNPREREGISTERED** observations (`D25` secondary block and `D26`), which is what they
always were.

**Measured before writing, so it is a fact rather than an assumption:** `grep -ic "STATE hypothesis"`
and `grep -ic "C1 is SUPPORTED"` over the 461 pre-existing lines both return **0**. The withdrawn
headline had never entered this file. This block does not remove it; it forecloses it.

Every number below was read by me out of the named artifact with `json.load`, recomputed by me from
the artifact's own `domain_means` / `controls` block, recomputed from `results.jsonl`, or produced by
running the committed script verbatim from the frozen read file — with the command given in the
command block at the end. Numbers that live only inside `reports/reviews/attack_the-swap-conclusion.md`
(the R10 lens artifact) — the factorial decomposition, the bootstrap Δz CIs, the cosine geometry and
the split-fragility resampling — are **labelled `[READ, not reproduced]`** wherever they appear.
Nothing here is taken from prose in the sprint log.

**PR-CSI-007 is RUNNING** (button L18 on the held-out validation split, the first button-L18 cell that
has ever existed off TRAIN). **[SUPERSEDED 2026-09-21: PR-CSI-007 has COMPLETED, 54 of 54
arms, and been read ONCE. The sentence above and every 'nothing from it here' caveat below were true
when written and are kept unaltered; the result is in section A8 (D29, D30) and the caveats they
supersede are amended in A9 (AM-15 … AM-19). S-160, S-161, S-163.]** Its read is frozen in `runargs/dcs_csi_pr007_read.txt` and is performed
**ONCE**, after all arms land. **No number from its run directories is read, reported or implied
anywhere in this block**, and every TRAIN-only caveat below is written as if it will never land.

---

## A6. NEW ROWS — append to section A

| # | claim | statistic (with CI and n_domains) | population / split / codeword / layer | caveats | source |
|---|---|---|---|---|---|
| D23 | **PR-CSI-005: button at L18 with 46 controls DOES NOT PASS ON TRAIN — and for the first time button's TRAIN failure is CERTIFIABLE rather than floor-limited.** *(split named per the PR-CSI-007 decision-rule obligation, S-165; the held-out cell is D29 and it does NOT replicate this result.)* The preregistered primary statistic landed inside a predictive interval fixed before the data, so the falsifier fired and the dissociation survived it | **Candidate** `KO_AXIS − KO` = **−0.00014**, ci95 **[−0.00111, +0.00081]**, **36 pos / 31 neg / 0 tied of 67 domains**, p = 0.7717. **RANK 36 of 47**, `n_controls` **46**, `rank_p` **0.766**, attainable floor **0.0213**. PRIMARY `candidate − comparator` (`KO_ORTH`) = **+0.00079** [−0.00021, +0.00178], 42/25, p = 0.1299. Identity `KO_SELF − KO` = −0.00075 [−0.00188, +0.00037], 32/35, p = 0.202 — inert. Manipulation `KO − BASE` = **−0.20682** [−0.22720, −0.18736], 0 pos / 67 neg. Positive control `KO_FULL − KO` = **+0.10938** [+0.09633, +0.12341], **67 pos / 0 neg**. `recovery_fraction_candidate_of_full` = **−0.0013** [−0.0106, +0.0073]. **PRIMARY STATISTIC, the only unread quantity**: `X` = exceedances among the **36 blind, never-read** controls. Recomputed by me from the report's own `controls` block: the 10 stage-1 controls contribute **7** exceedances (`KO_RAND1, KO_RAND2, KO_RAND3, KO_RAND5, KO_SHUF0, KO_SHUF1, KO_SHUF2`) and the 36 blind controls contribute **X = 28**; total 35 ⇒ **R47 = 36**, which reproduces the analyser's reported rank exactly. Against the pre-fixed `X ~ BetaBinomial(36, 7.5, 3.5)` — `E[X] = 24.5455`, sd 5.5307, median 25, **95 % predictive [13, 34]** — **X = 28 is INSIDE**. **No falsification threshold fired**: `X ≤ 12` (P = 2.297e−02) not fired, `X ≤ 4` (P = 2.055e−04) not fired, `X = 0` (P = 6.461e−07) not fired | **626 keys / 67 TRAIN domains**, 53 arms, **button**, **L18**, site `rel-6`, `semantic_one_word`, cell C, dose 4. `resolved_rescue_layers` = 18 on every rescue arm — measured per arm, not assumed. `VOID` **[]**; gates `manipulation_check` / `identity_check` / `instrument_capable` all **true** | **TRAIN ONLY**, and this is the caveat that governs the row: **no button-L18 VALIDATION arm existed when this was read**, and the dissociation analysis's own §13 holds held-out to be the strongest evidence in the set. **PR-CSI-007 is running to close exactly this gap and its result is NOT IN THIS FILE.** The verdict is a **negative** and is certified as one: independent re-derivation (`DCS_CSI_REDERIVE_button_train_L18_n46.json`, 7 136 B, 627 keys) gives `certifiable_at_0.05` **true** on **all three** families — pooled **36 of 47** (floor 0.0213), random-only **17 of 23** (floor 0.0435), shuffled-only **20 of 25** (floor 0.0400), every one **DOES NOT PASS**. `specificity_all_controls_rejected` is **false**, as a null requires. **A one-rank disagreement between the two paths is recorded, not smoothed**: the primary analyser's shuffled-only read (`..._L18_shufonly.json`, 976 770 B) gives candidate **−0.00025**, **rank 19 of 25** at **651** keys, while the re-derivation gives **20 of 25** at **627** keys. It is a **key-set** difference (651 vs 627, different `--arms` lists), not a contradiction; both say DOES NOT PASS. **Leave-one-domain-out — the null is immovable**, reproduced by me by running `scripts/dcs_csi_rank_loo.py` verbatim from the frozen read file: histogram **{31:1, 32:2, 33:3, 34:6, 35:12, 36:21, 37:22}** over 67 drops, **BEST attainable rank under ANY single deletion = 31 of 47** (`printing_works`) — no deletion reaches rank 1 — candidate range **−0.00029 … +0.00003**, **66 of 67** drops negative. **A REPRODUCIBILITY FOOT-GUN FOUND WHILE VERIFYING THIS, and it is new**: the report's `domain_means` are stored **rounded to 5 dp**, and the same LOO recomputed from them gives a **different histogram** — {30:1, 32:3, 33:6, 34:6, 35:16, 36:20, 37:15}, best rank **30**, **65** of 67 negative. The verdict is unchanged in every direction, but **the LOO histogram must be taken from the script on `results.jsonl`, never from `domain_means`** (see prohibition 33) | **S-137** (`reports/DCS_CSI_SUBSPACE_button_train_L18_n46.json` 1 759 285 B, `reports/DCS_CSI_REDERIVE_button_train_L18_n46.json` 7 136 B, `reports/DCS_CSI_SUBSPACE_button_train_L18_shufonly.json` 976 770 B, prereg `configs/dcs_csi_pr005_button_L18_family.json` 58 174 B) |
| D24 | **THE CODEWORD DISSOCIATION AT MATCHED POWER: same layer, same family size, same family composition, same procedure, same 67 TRAIN domains — basket is rank 1 of 47 and button is rank 36 of 47. It is NOT a sample-size artifact, and that is now a MEASUREMENT rather than a projection** | **basket L18 TRAIN**: candidate **+0.00264**, ci95 **[+0.00068, +0.00471]**, **44 pos / 23 neg of 67 domains**, **rank 1 of 47**, rank p **0.02128**, floor 0.0213 — **PASSES**. **basket L18 VALIDATION**: candidate **+0.00401**, ci95 **[+0.00098, +0.00775]**, **15 pos / 8 neg of 23 domains**, **rank 1 of 47**, rank p **0.02128**, floor 0.0213 — **PASSES**. **button L18 TRAIN**: candidate **−0.00014**, ci95 [−0.00111, +0.00081], **36 pos / 31 neg of 67 domains**, **rank 36 of 47**, rank p **0.766**, floor 0.0213 — **DOES NOT PASS, certified** (D23). The families are matched at the arm level, not merely at the count: **22 random (`KO_RAND0..21`) + 24 shuffled (`KO_SHUF0..23`) = 46 in every cell**, and `resolved_rescue_layers` is **18** on every rescue arm of every cell | basket L18 TRAIN **642 keys / 67 TRAIN domains**; basket L18 VALIDATION **215 keys / 23 held-out domains**; button L18 TRAIN **626 keys / 67 TRAIN domains**. All three: **L18**, site `rel-6`, `semantic_one_word`, cell C, dose 4, direction `sufficiency`, `VOID []`, all three gates true | **The matched-power comparison proper is TRAIN vs TRAIN, at 67 domains in both cells.** The basket VALIDATION cell is 23 domains and is a *held-out* strengthening, **not** part of the power match — do not quote "same 67 domains" while pointing at it. **Button has no held-out L18 cell**: the dissociation at matched power is TRAIN-only on the button side (PR-CSI-007 running; nothing from it here). The two sides are not symmetric in what they can certify: button's DOES NOT PASS is certifiable at α = 0.05 on pooled, random-only and shuffled-only, while **basket's PASS sits exactly at its attainable floor** (0.02128 vs floor 0.0213) in both splits — a pass at the floor is a pass, but it has no margin. This row removes "unequal control families" as an explanation **and nothing else**: it cannot say *why* the codewords differ, and D21's caveat 2 (basket's TRAIN rank 1 is not robust to per-domain reweighting — two of five schemes move it to rank 3 of 47, p = 0.0638) is **unaffected and still binding** | **S-137**, with **S-128**/**S-131** for the projection it replaces (`reports/DCS_CSI_SUBSPACE_button_train_L18_n46.json`, `reports/DCS_CSI_SUBSPACE_basket_train_n46.json`, `reports/DCS_CSI_SUBSPACE_basket_validation_n46.json`) |
| D25 | **THE CROSS-CODEWORD AXIS SWAP (PR-CSI-006), recorded as its PREREGISTRATION returns it: CELL 4 on TRAIN, direction B NOT REPLICATED, and C1 REFUTED BY THE FIXED RULE.** No cell of the 2×2 was cleanly attained and no direction cleared its preregistered bar | **The rule, quoted from `configs/dcs_csi_pr006_axis_swap.json`:** `definition_of_HELPS` = *"rank 1 or 2 among 46 controls … Rank 3 of 47 is p = 0.06383 and is NOT 'helps'"*; `decision_rule/step_6` = *"If they disagree, the direction is reported as **NOT REPLICATED** and **no cell is claimed for it**"*; `cell_neither_helps` (**CELL 4**) = *"**C1 is REFUTED** — a shared direction estimated BETTER should have transferred, and did not."* **All three cells, with the swap rank AND the recipient's own native rank computed inside ONE report on ONE key set — both ranks recomputed by me from each report's own `controls` block:** **(A) basket→BUTTON, TRAIN** — swap **+0.00150** ci95 **[+0.00047, +0.00256]**, **44 pos / 23 neg of 67**, p = 0.0070, **rank 4 of 47** (rank p **0.08511**); native `KO_AXIS` **−0.00014**, **rank 36 of 47**; PRIMARY cand − comparator +0.00243 [+0.00129, +0.00362], p = 1.65e−04. **(B) button→BASKET, TRAIN** — swap **+0.00090** ci95 **[−0.00029, +0.00217]**, **39 pos / 28 neg of 67**, p = 0.1606, **rank 13 of 47** (rank p **0.2766**); native **+0.00265**, **rank 1 of 47**. **(B) button→BASKET, VALIDATION** — swap **+0.00224** ci95 **[+0.00042, +0.00430]**, **16 pos / 7 neg of 23**, p = 0.0343, **rank 2 of 47** (rank p **0.04255**); native **+0.00401**, **rank 1 of 47**. **By the fixed rule read on TRAIN for both directions: A rank 4 = NOT helps, B rank 13 = NOT helps ⇒ CELL 4 ⇒ C1 REFUTED.** B train 13 and B validation 2 **DISAGREE**, so **no cell may be claimed for direction B** and it is **NOT REPLICATED**. Every one of the three reports prints the same `VERDICT`: *"PRIMARY DOES NOT PASS … It is INSIDE the controls, not above them."* **SECONDARY, UNPREREGISTERED, and labelled as such:** the rank-36 → rank-4 contrast is real — paired `XSWAP_FROM_BASKET − KO_AXIS` on the same 67 domains and the same `KO` baseline = **+0.001644**, ci95 **[+0.000664, +0.002605]**, p2 = **0.0014**, **47 of 67 domains positive**, sign test p = 6.5e−04 `[READ, not reproduced]` | **A**: 626 keys / **67 TRAIN domains**, recipient **button**, donor basket. **B train**: 641 keys / **67 TRAIN domains**, recipient **basket**, donor button. **B validation**: 215 keys / **23 held-out domains**, recipient **basket**, donor button. All three **L18**, site `rel-6`, `semantic_one_word`, cell C, dose 4, 46 controls, `VOID []`, `manipulation_check` / `identity_check` / `instrument_capable` all **true**. Instrument live in every cell: `KO_FULL − KO` = **+0.10938** (A) / **+0.12063** (B train) / **+0.10370** (B validation) — no cell's null is a headroom artifact | **THE HEADLINE THIS EXPERIMENT WAS COMMITTED WITH IS WITHDRAWN — see AM-10, and it is not restorable by any later outcome.** The secondary contrast may **never** be quoted without the preregistration's output beside it. **The swap arm's rank p is DESCRIPTIVE, not a valid permutation p** (D27) — this applies to rank 4, rank 13 **and** rank 2 alike. **Effect size, which must travel with the contrast**: the swap moves **+0.00150** against a whole-state **+0.10938** in button, i.e. **1.4 %** of what the whole clean state recovers, and **98.6 % is elsewhere**. **Direction B is the weaker test by construction** — basket's native already ranks 1 of 47, leaving a transplant almost no room — and in **both** B cells the swap sits **below** the native. Nothing here touches the **necessity** direction, which has only ever been run on basket. **TRAIN-only on direction A**: direction A has never had a validation split, so the *"no cell is claimed if the splits disagree"* clause has never been able to bind it | **S-138**, headline **WITHDRAWN by REVIEW R10 BLOCKER-1**; see **AM-10** (`reports/DCS_CSI_SWAP_button_train_L18_from_basket_n46.json` 1 759 838 B, `reports/DCS_CSI_SWAP_basket_train_L18_from_button_n46.json` 1 766 606 B, `reports/DCS_CSI_SWAP_basket_validation_L18_from_button_n46.json` 726 250 B, and the three `DCS_CSI_SWAP_REDERIVE_*.json` twins, which reproduce ranks **4 / 13 / 2** and candidates **+0.00149 / +0.00090 / +0.00224**) |
| D26 | **R10's FACTORIAL READ: a PROBE main effect is ESTABLISHED and replicated three times; the RECIPIENT main effect was NEVER TESTED. So "the STATE hypothesis is REFUTED" is ABSENCE OF EVIDENCE — only a PURE-state model with zero probe effect is refuted** | The 2×2 the swap design implies, both TRAIN reports carrying the **same 67 domain names** (intersection 67 of 67, so it pairs): recipient=button × probe=basket **+0.001499**, recipient=button × probe=button **−0.000145**, recipient=basket × probe=basket **+0.002649**, recipient=basket × probe=button **+0.000900**. **PROBE main effect +0.001696, ci95 [+0.000912, +0.002497], p2 < 1e−4 — ESTABLISHED.** **RECIPIENT main effect +0.001097, ci95 [−0.000569, +0.002890], p2 = 0.201 — NOT TESTED, not refuted.** **INTERACTION −0.000105, ci95 [−0.001482, +0.001230], p2 = 0.888 — flat**, which is what "both factors, additively" looks like. `|recipient| / |probe|` = **0.647**. The probe effect replicates in all three cells at near-constant magnitude: **+0.001644** [+0.00066, +0.00261] p = 0.0014 (recipient button, train, n = 67); **+0.001749** [+0.00069, +0.00288] p = 0.0007 (recipient basket, train, n = 67); **+0.001770** [+0.00024, +0.00367] p = 0.019 (recipient basket, validation, n = 23). All `[READ, not reproduced]` | 67 TRAIN domains (both button-recipient and basket-recipient train cells) and 23 VALIDATION domains; **L18** throughout; recipients button and basket; probes basket and button; `semantic_one_word`, cell C, dose 4 | **Basket is a better recipient than button for BOTH probes**, at a point estimate **65 %** of the probe effect, with a CI containing values **larger** than the probe effect. **The recipient contrast crosses button and basket, which §3.3 forbids pooling — and that cuts FOR this finding**: the experiment contains **no legitimate test of the recipient factor at all**, so "REFUTED" has no measurement standing behind it. **CORRECTED WORDING, and the only permitted form**: *"a pure-state model with no probe effect is refuted; the recipient factor is not estimated by this design."* **A state-flavoured alternative the original dichotomy did not contain (R10 MAJOR-3)**: `|cos(axis, the recipient's OWN knockout delta)|` over 670 rows is **0.056749** for basket's axis, **0.051459** for button's own axis, **0.036661** for the best control — **basket's axis fits BUTTON's own knockout delta better than button's own axis does**, which reads as *"button's probe mis-estimates a real state direction"*, a **state** reading. Not proven (alignment predicts recovery only weakly among controls, r = 0.19, n = 46) but live. **Everything in this row is UNPREREGISTERED and post-hoc**, built by a reviewer after the read | **REVIEW R10 MAJOR-1 and MAJOR-3** (`reports/reviews/attack_the-swap-conclusion.md`), over the three `DCS_CSI_SWAP_*_n46.json` reports |
| D27 | **The swap arm is NOT exchangeable with the control family it is ranked against, so its rank p is DESCRIPTIVE rather than a valid permutation p** | `\|cos\|` **with the recipient's native axis**: over the **46 controls** min **0.0001**, median **0.0156**, **max 0.1894**; the **swap axis 0.5569** (0.556893 at full precision, reproducing gate 0f's freeze-time expectation to four decimals). The swap axis is **2.9× more aligned with the native axis than ANY control**. `torch.equal(swap_cand_from_basket, basket cand_rank1)` = **True** — it really is basket's axis. The rank test's null requires the candidate to be drawn from the control family's directional distribution; **by construction the controls are near-orthogonal to the native axis while the "foreign" axis retains 56 % of it**, and `reports/DCS_CSI_EXCHANGEABILITY_basket_train_n46.json` tests shuffled-vs-random poolability only — **nothing tests candidate-vs-family exchangeability, and by construction nothing can**. All `[READ, not reproduced]` | the 46-control family of the **button TRAIN L18** cell (67 domains, 626 keys); the same construction holds in the two basket-recipient cells | **THE REVIEWER TRIED TO TURN THIS INTO AN EXPLANATION AND FAILED — and the failure is part of the record, not a footnote.** Pearson `r(|cos| with the native axis, recovery)` over the 46 controls = **−0.027**; a linear fit extrapolated to `|cos| = 0.5569` predicts **+0.000035** against an observed **+0.001499**, a residual of **+1.95 sd**. **No trend. The alignment asymmetry does NOT explain rank 4.** So this row **weakens the inferential standing of the swap ranks without explaining them away**, and both halves must be stated together or the row is misleading in whichever direction the reader is already leaning. It governs **every rank in D25** — 4, 13 and 2 alike — and it does **not** touch the **paired** contrast `XSWAP − KO_AXIS` (+0.001644, p = 0.0014), which is a within-report domain-paired bootstrap and makes no exchangeability assumption | **REVIEW R10 MAJOR-2** (`reports/reviews/attack_the-swap-conclusion.md`), from the `.pt` files directly |
| D28 | **The S-119 bf16 compute-capability guard and the `compute_capability` provenance field are INERT on the producer path — 230 rows bit-identical across the blob change. AND that inertness is NOT verifiable after the fact from the run directories, because `RUNMETA` does not record the blob and `git_commit` is not a valid witness of what code ran** | **Recomputed by me from `results.jsonl`, not taken from S-139**: `csi1_basket_validation_CODEANCHOR_139B_20260920_190627_488644` (job **913407**, `git_commit d515cc76`, `compute_capability 8.6`) vs `csi1_basket_validation_STAGEANCHOR_AXIS_20260920_170734_754715` (job **913232**, `git_commit 1cce381e`, `compute_capability` **absent**): **rescue-fired A = 230, B = 230, common keys = 230, A-only 0, B-only 0**, and on **all six** readout fields — `logp_concept`, `logp_codeword`, `semantic_logodds`, `p_concept`, `p_codeword`, `top1_id` — **`max|diff| = 0.000e+00` with `nonzero_rows = 0 / 230`**, each field present on 230 of 230 compared rows (non-vacuity asserted before any difference was believed, per S-134). **The provenance defect, verified and STRONGER than S-143 states**: `RUNMETA.json` carries **24 keys** on the newer anchor and **23** on the older, and **not one of them mentions a blob, hash or sha** — the set is `{args, argv, compute_capability, cuda_available, cwd, experiment, git_commit, git_dirty, gpu, hostname, output_dir, plan, python, python_executable, run_id, schema, script, seed, slurm_job_id, slurm_nodelist, start_epoch, start_ts, torch, transformers}`. At `git_commit d515cc76` the two files in question are `src/boombness/score_behavior.py` blob **`e94258bd`** and `doublespeak_causality/ds_common.py` blob **`557d8669`**, and **`compute_capability` occurs 0 times in EITHER** — yet that run's own `RUNMETA` carries `compute_capability: 8.6`. **And `git_dirty` is `None` on BOTH anchors**, not `true`: the dirty flag is not recorded either, so **nothing in the run directory witnesses the worktree state at all** | **230 rows / 23 VALIDATION domains**, basket, **L18**, `--rescue-donor clean` (the **sufficiency** path), norm-match key `cand_rank1`, staged model path. Guard located at `src/boombness/score_behavior.py` at the `dc.load_model` call site: refuses `--dtype bfloat16` when `torch.cuda.get_device_capability(0)[0] < 8`. The `compute_capability` field lives in a **different file**, `doublespeak_causality/ds_common.py` (blob **`95fb640b`** at HEAD `c146f36c`; **`557d8669`** at both `d515cc76` and `1cce381e`) | **THE MEASUREMENT STANDS; ITS PROVENANCE DOES NOT.** It is true as a statement about **those two outputs**, which is what was measured; it is **not recoverable as a statement about which code produced them**. **The inertness was measured on a SUFFICIENCY arm only** — the **necessity** path is `--rescue-donor ko`, a different branch with its own four-leg contract, and nothing has measured the new blob there (S-142(c)); reasoning from "inert there" to "inert here" is an argument about code, and this sprint has three entries about arguments about code that turned out to be wrong. **No committed number is touched**: every arm in PR-CSI-003, PR-CSI-005 and PR-CSI-006 ran under blob **`e94258bd`**; the current worktree blob is **`11d2c617`** (equal to `HEAD:src/boombness/score_behavior.py`, verified by `git hash-object`). **The tests are mostly source-text assertions** — they pass if the text is present even when the code never executes, and a guard made unreachable by an early return above it would survive most of them; R10 found the truth-table test **tautological** and S-141 **deleted and replaced** it with one that locates the guard in the AST and **executes** it (9 of 9 mutations now fail). **This limitation is not confined to this row — see AM-14, which extends it to D17 and D22** | **S-139**, corrected by **S-143**; guard test replacement **S-141** (run dirs above; `RUNMETA.json`; `git hash-object` / `git rev-parse`) |

---

## A7. AMENDMENTS — corrections to rows above, additive and marked

Each amendment names the row, entry or claim it governs. **The original is unchanged and still
readable.** Numbering continues from AM-9.

| id | marker | governs | what changed, and why |
|---|---|---|---|
| **AM-10** | **WITHDRAWN** | **S-138's headline claim, as it stands in the sprint log title and in `git log` at commit `d515cc76`**: *"Basket's axis rescues BUTTON 32 ranks better than button's own axis does … **C1 is SUPPORTED and the STATE hypothesis is REFUTED**."* Also governs **D25** and any future row reaching for the swap result | **WITHDRAWN as REVIEW R10 BLOCKER-1.** The preregistration `configs/dcs_csi_pr006_axis_swap.json` returns the **opposite** conclusion under its own decision rule: `definition_of_HELPS` is **rank ≤ 2 of 47** (*"Rank 3 of 47 is p = 0.06383 and is NOT 'helps'"*); measured outcome is **A = rank 4 (NOT helps)**, **B train = rank 13 (NOT helps)**, **B validation = rank 2 (helps)**; `decision_rule/step_6` says that when the splits disagree the direction is **NOT REPLICATED and no cell is claimed for it**; read on TRAIN for both directions the cell is **CELL 4**, whose preregistered meaning is verbatim *"**C1 is REFUTED** — a shared direction estimated BETTER should have transferred, and did not."* The withdrawn headline is the **CELL 1** reading — a cell attained in **neither** direction. **THE REPLACEMENT, and the only thing this table records as the experiment's output, is `D25`: CELL 4 on TRAIN, direction B NOT REPLICATED, C1 REFUTED by the fixed rule.** **The body of S-138 was honest** — it assigns CELL 4, it says *"no cell of the 2×2 was cleanly attained"*, it says *"direction A misses its own preregistered bar"*, it reports p = 0.085 and says it does not clear 0.05, and it contains the sentence *"the threshold does not get moved after the fact"* — **and then the title moved it**, and a downstream reader, `git log` and this claim table take the title. That is the exact failure the preregistration existed to prevent, committed by the author of the preregistration, in the title of the entry that quotes it. **The rank-36 → rank-4 contrast is NOT withdrawn**; it is demoted to what it always was, a **secondary, unpreregistered** observation (D25's secondary block, D26). **S-143 records that this headline is not restorable by any outcome of PR-CSI-007.** See prohibition **29** |
| **AM-11** | **CORRECTION (backwards)** | **S-138's own account of the direction-B split** — *"VALIDATION is n = 23 domains and 215 keys against TRAIN's 67 and 641 … at rank 2 of 47 with 23 domains the ordering is one control away from rank 3"* — and any statement anywhere that **the VALIDATION cell of direction B is the fragile one** | **It is BACKWARDS.** Measured `[READ, not reproduced]`: **TRAIN rank 13 sits in a dense pileup** — nearest control **above** the candidate **+4.0e−05** away, nearest **below** **+2.3e−05** away, **six controls within 1e−4** — and its rank under resampling of the 46 controls is **[7, 19]** (median 13). **VALIDATION rank 2 has gaps of +5.4e−04 on BOTH sides** and its rank under the same resampling is **[1, 4]** (median 2). **The TRAIN number is the fragile one.** And the two splits are **statistically indistinguishable**: `VALIDATION − TRAIN` = **+0.001336**, ci95 **[−0.000895, +0.003720]**, p2 = **0.254**, with **train/validation domain overlap = 0**. **Reporting the split rather than picking a side was right; the REASON given was wrong**, and the correct reason is that the two cannot be told apart. This does **not** rescue direction B — `decision_rule/step_6` keys on *disagreement of the cell assignments*, which stands (rank 13 is not "helps", rank 2 is), so **direction B remains NOT REPLICATED with no cell claimed**. See prohibition **32** |
| **AM-12** | **CORRECTION (one measurement printed twice)** | **S-135 and S-138**, both of which report gate 0f as *"`cos(swap key, recipient cand_rank1)` = **0.5569 in BOTH directions**"*, and read it as two independent confirmations | **Cosine is symmetric.** `cos(a, b) ≡ cos(b, a)`, so *"0.5569 in both directions"* is **ONE measurement printed twice**, not two. The gate's cosine check is nonetheless **real and load-bearing** and is what actually caught the failure mode it was built for: R10 mutations **M3** (`key` → `cand_rank1`) and **M9** (target → 0.9999) both **killed** it. What did **not** work is the same gate's `donor_sha` anchor — **R10 BLOCKER-2**: `c["donor_sha"]` appeared only inside a `print` at `dcs_csi_pr006_gate0.py:153-154` and **was never compared**, so the gate printed **PASS** while its own printed sha disagreed with its own printed expectation in **both** cells, and mutation M1 (constants → `deadbeef…`/`cafebabe…`) still printed ALL GATES PASS. **S-141 measured that the declared constants had never been computed by anyone**: the real added-key shas are **`679c76d2d0e8fe9e`** (button) and **`b2f266d711994013`** (basket); the literals `0c397a778db933ba` / `7d4e01f5475e6b53` match **neither** the tensor sha, nor the donor file sha, nor the recipient file sha. **FIXED and mutation-verified in S-141** (compute `t16(donor)` at runtime and assert sha **and** `torch.equal`; plus a `torch.equal(swap, own)` refusal). **No committed number moved**: X = 28 did not move, and ranks **4 / 36 / 13 / 2** all reproduce from `domain_means` at ~1e−6. This is R2-M5 / S-042 / S-134's pattern for the **fourth** time, in the gate S-138 called *"the one that mattered most"* |
| **AM-13** | **OPERATIONAL — a planned discharge that did NOT happen** | **D18**'s floor caveat, **D19**'s *"necessity cannot clear any bar at `n_controls = 8`"*, **AM-8**, and **prohibitions 24 and 26** — all of which are written as if the necessity family were about to grow | **PR-CSI-003-A's necessity family extension (4 → 24 shuffled controls) is BLOCKED by its own VOID condition 6, and was NOT LAUNCHED (S-142).** The condition, quoted from the file: *"`src/boombness/score_behavior.py` modified between arms of the same comparison. Half 1 (job 906433) and half 2 (job 912736) have already run against the current file; **the 20 new arms must run against that same [file]**."* Measured: the blob when halves 1 and 2 ran is **`e94258bd5fc44c70629e707b00504b7acac2a7b7`**; the blob now is **`11d2c61747e9401e2d2cb8f4123dd1188674d61b`** (verified by me by `git hash-object`, and equal to `HEAD:src/boombness/score_behavior.py` at `c146f36c`). The drift is **the author's own S-139 edit**, made three hours earlier. **8.7 GPU-hours were not spent** on twenty arms that would have been VOID by a condition the author wrote. **The launcher patch itself IS applied and verified** (`bash -n` OK; halves 4 and 5 yield 20 arm names, range 4..23, **no gaps, no repeats**, `subnec` reused verbatim, refusal message widened to name 1–5) — **only the launch waits**, escalated rather than self-approved, because amending a VOID condition after it fires to let one's own experiment proceed is **BLOCKER-1's exact shape one day later**. **CONSEQUENCE FOR THIS TABLE, which is the whole reason this amendment exists:** **the necessity floor remains 0.1111 at `n_controls = 8`**, AM-8's *"K ≥ 20 controls required to certify"* remains **unreachable**, and **S-133's rank 1 of 9 (D18) is still the last word in the necessity direction**. Prohibition 26's three inseparable clauses — **floor-limited, TRAIN-only, in-sample** — are not about to be dropped, and nothing in this block loosens them |
| **AM-14** | **PROVENANCE AMENDMENT — extends S-143's correction beyond the entry that raised it** | **D17** (*"`KO_AXIS` ran post-edit, job 905990, vs `KO_AXIS_ANCHOR` ran pre-edit, job 906001"*), **D22** (*"`CODEANCHOR_R0`, job 912838, node n-350, **repo commit `dabfeb854ec6`, clean tree**"* vs *"`KO_RAND0`, job 902005, commit `bc8e77793633`, **`git_dirty = true`**"*), and **D28** | **S-143 raised this against S-139; it reaches D17 and D22 too, and I checked rather than assumed.** `RUNMETA.json` **records no blob, hash or sha field in this schema at all** — verified on four run directories spanning three of these rows. Consequences, each measured: **(a)** `csi1_button_train_CODEANCHOR_R0_20260920_135631_905054` (job 912838, D22's anchor arm) records **`git_dirty: None`**, *not* `false` — so **D22's "clean tree" is NOT witnessed by the run directory**; it was a contemporaneous check whose evidence the artifact does not carry. **(b)** `csi1_button_train_KO_RAND0_20260916_223555_2963342` (job 902005, D22's other side) **does** record `git_dirty: true`, so **the direction that would falsify a clean-tree claim is recorded while the direction that would confirm it is not** — an asymmetry worth naming. **(c)** D22's identification of the diff under test (*"`git diff bc8e77793633 -- score_behavior.py` = +474/−7 against blob `e94258bd`"*) is an inference from `git_commit` plus the worktree, exactly the inference S-143 shows is unsound. **NOTHING IS WITHDRAWN.** D17's and D22's **measurements** — 670 rows bit-identical on six fields, twice — stand as statements about **those outputs**, which is what was measured. What is corrected is the **claim about which code produced them**: it is not recoverable from the run dirs. **The fix exists and was exercised for the first time at PR-CSI-007's launch**: print `git hash-object` **and** require `git status --porcelain` to be **empty** at every submission, both now VOID conditions. **The clean-worktree half is exactly what every previous run in this project was missing** |

---

## D4. PROHIBITIONS ADDED 2026-09-20 (third block)

Numbering continues sections D, D2 and D3. **The existing 28 prohibitions are unchanged**; 24 and 26
are additionally governed by AM-13, and 21 and 27 by D24.

29. **"C1 is SUPPORTED" / "the STATE hypothesis is REFUTED" / any CELL 1 or CELL 2 reading of
    PR-CSI-006 / "basket's axis rescues button".** — **FORBIDDEN, and WITHDRAWN rather than merely
    discouraged (AM-10).** The preregistration's output is: **CELL 4 on TRAIN, direction B NOT
    REPLICATED, C1 REFUTED by the fixed rule.** The defensible sentence, and the only one:
    *"basket's axis transplanted into button's knockout recovers +0.00150 where button's own axis
    recovers −0.00014 on the same 67 domains and the same 46 controls — a paired difference of
    +0.00164, ci95 [+0.00066, +0.00261], p = 0.0014 — but it ranks **4 of 47**, does **not** clear
    its preregistered bar of rank ≤ 2, and its rank p is descriptive rather than a valid permutation
    p."* The rank-36 → rank-4 contrast may be stated; it may **never** be stated without "CELL 4,
    C1 refuted by the fixed rule" beside it, and it must always be labelled **secondary and
    unpreregistered**.

30. **"The state hypothesis is refuted"**, in any wording, unqualified. — **FORBIDDEN (D26).** Only a
    **PURE**-state model with **zero** probe effect is refuted. The recipient main effect is
    **+0.001097, ci95 [−0.000569, +0.002890], p = 0.201 — NOT TESTED**, at 65 % of the probe effect
    with a CI containing values larger than it, and the interaction is flat (p = 0.888). The
    recipient contrast crosses codewords, which §3.3 forbids pooling, so **the design contains no
    legitimate test of the recipient factor at all.** Permitted form: *"a pure-state model with no
    probe effect is refuted; the recipient factor is not estimated by this design."* And carry
    MAJOR-3 with it: basket's axis is more aligned with **button's own** knockout delta (0.056749)
    than button's own axis is (0.051459), which is a **state**-side reading of the same data.

31. **Any swap rank p quoted as a permutation p, or any swap rank quoted as if the candidate were
    exchangeable with its controls.** — **FORBIDDEN (D27).** The swap axis retains `|cos| = 0.5569`
    with the native axis where **no control exceeds 0.1894**. Say **descriptive**. And carry the
    other half: the reviewer **tried** to convert the alignment into an explanation and **failed**
    (`r = −0.027`, fit predicts +0.000035 against an observed +0.001499, residual +1.95 sd) — the
    asymmetry is an assumption violation, **not** an explanation of rank 4.

32. **"The VALIDATION cell of direction B is the fragile one" / "rank 2 of 47 is one control away
    from rank 3".** — **FORBIDDEN, BACKWARDS (AM-11).** TRAIN rank 13 sits in a pileup of six
    controls within 1e−4 and resamples to **[7, 19]**; VALIDATION rank 2 has **+5.4e−04** gaps both
    sides and resamples to **[1, 4]**. The two splits are **statistically indistinguishable**
    (+0.001336, ci95 [−0.000895, +0.003720], p = 0.254). Report the split; give **this** reason.

33. **Any leave-one-domain-out histogram, LOO rank range or LOO sign count computed from a report's
    `domain_means` block.** — **FORBIDDEN.** `domain_means` is stored **rounded to 5 dp**, and at
    these effect sizes (1e−4) the rounding moves the histogram: button L18 n46 gives
    **{31:1, 32:2, 33:3, 34:6, 35:12, 36:21, 37:22}** with best rank **31** and 66 of 67 negative
    from `scripts/dcs_csi_rank_loo.py` on `results.jsonl`, against
    **{30:1, 32:3, 33:6, 34:6, 35:16, 36:20, 37:15}** with best rank **30** and 65 of 67 negative
    from `domain_means`. **The verdict is unchanged in both** — no deletion approaches rank 1 — but
    a histogram quoted from the wrong source is a number nobody can reproduce. Run the committed
    script; cite the command.

---

## AUDIT — every existing row re-checked against S-137 … S-143 and REVIEW R10

Checked: **D1–D22, E1–E2, C1–C4, AM-1–AM-9, prohibitions 1–28.** Verdicts, with the entry that now
governs each. **Rows not listed were checked and are UNAFFECTED.**

| row | verdict | note |
|---|---|---|
| D1, D3, D4, D5, D6, D7, D8 | **UNAFFECTED** | nothing in S-137…S-143 touches the knockout effect size, the QPROBE validation figure, sentence-level generalisation, the behavioural endpoint, cross-architecture decoding, the button run's mechanics or the axis build's bit-reproducibility |
| **D2** | **UNAFFECTED, and load-bearing for a THIRD time** | the L18/L20 ρ plateau (button 0.5931/0.5935, basket 0.6525/0.6512) is what makes **D24's** shared-layer L18 comparison and **D25's** cross-codeword transplant fair rather than handicapped. Quote D2 whenever D24 or D25 is quoted |
| D9, D10, D11 | **UNAFFECTED** | all three are button position/linearity results at **L20**; this block adds no position-level measurement |
| **D12, D19, D20** | **UNAFFECTED; basket's cells independently RE-VERIFIED at n46** | I re-read both basket L18 n46 artifacts for **D24** and they reproduce exactly: TRAIN **+0.00264** [+0.00068, +0.00471], 44/23 of 67, **rank 1 of 47**, rank p 0.02128, 642 keys; VALIDATION **+0.00401** [+0.00098, +0.00775], 15/8 of 23, **rank 1 of 47**, rank p 0.02128, 215 keys. D12 continues to carry AM-2, AM-4, AM-5 and AM-7 |
| **D13** | **STRENGTHENED; its CERTIFICATION caveat is DISCHARGED; superseded in family size** | D13 records button at L18 as **rank 8 of 11** with candidate **−0.00027** at **658 keys**, and caveats *"Family of 10, floor 0.0909: this … could **not** have certified a pass."* **D23 supersedes that read at 46 controls**: candidate **−0.00014**, **rank 36 of 47**, floor **0.0213**, **626 keys**, and `certifiable_at_0.05` **true** on pooled, random-only **and** shuffled-only. The candidate moves −0.00027 → −0.00014 on a **different key set and a different arm list** — a key-set difference of the S-125 class, **not a disagreement**; quote each figure with its own key count and family size and never mix them. D13's headline (the dissociation is not explained by the layer) is **strengthened**. **D13's *"TRAIN only — button has no held-out L18 arms"* caveat STILL STANDS and is NOT discharged** |
| **D14, D15** | **NOT contradicted; D15's button-L18 cell is superseded in family size** | D15's 2×2 quotes button L18 TRAIN as *"rank 8 of 11, cand −0.00027"* — the **10-control** read. The governing read is now **D23/D24's 46-control** cell: **rank 36 of 47, cand −0.00014, certified**. **The verdict does not move** (inside its controls at both layers, further inside at L18) and D15's claim is unchanged; only the family size, floor and key set are superseded. D15 also continues to carry **AM-7** (its VALIDATION cell quotes the superseded n30 read) and S-127's *refit-not-transported* wording correction |
| **D16, D18** | **NOT contradicted; governed by AM-13** | D18's *"FLOOR-LIMITED BY DESIGN"*, `n_controls = 8`, `rank_p_floor = 0.1111`, TRAIN-only and in-sample caveats are **not about to be lifted**: PR-CSI-003-A's 4 → 24 extension is **BLOCKED by VOID condition 6 and NOT LAUNCHED** (S-142). **S-133's rank 1 of 9 remains the last word in the necessity direction.** D16 continues to carry AM-8 |
| **D17** | **NOT contradicted; governed by AM-14** | D17's 670-row bit-identity across jobs 905990 / 906001 **stands as a statement about those outputs**. What is corrected is its provenance framing: `RUNMETA` records **no blob**, and `git_commit` is not a witness of what code ran (D28, AM-14). D17's scope limit — same-node determinism — is untouched |
| **D21** | **STRENGTHENED on its headline; its surviving-explanation caveat is now DIRECTLY TESTED and the result CUTS AGAINST the way that caveat reads** | **(a) Strengthened**: D21 refuted "unequal control families" by *projection and matched-subset argument*; **D24 replaces the projection with a measurement at the matched size the objection demanded** — 46 controls of identical composition in every cell, basket **1 of 47** vs button **36 of 47**, same layer, same 67 TRAIN domains. **(b) The tension, stated rather than smoothed**: D21 names **exactly one survivor, C1 — *"basket simply has a better probe"*** — as the residual explanation. PR-CSI-006 was built to test C1, and **by the preregistration's own decision rule it returns C1 REFUTED (CELL 4 on train, direction B NOT REPLICATED)** — AM-10, D25. What *is* established is a **probe main effect** (+0.001696, p < 1e−4, D26), which is C1-flavoured but is **secondary and unpreregistered**, and R10's MAJOR-3 supplies a **state**-flavoured alternative the dichotomy did not contain. **So D21's C1 caveat must now be read with D25, D26 and prohibitions 29–31, and must not be quoted as though C1 were still the unexamined survivor.** **(c)** D21's caveats 1 (the TRAIN own-layer cell is the weakest evidence in the set) and 2 (basket's TRAIN rank 1 moves to rank 3 of 47 under two of five reweighting schemes) are **UNAFFECTED and still binding**. **(d)** D21's *"TRAIN-only on the button-L18 side"* caveat **still stands** |
| **D22** | **NOT contradicted; governed by AM-14; reinforced by a third instance** | D22's 670-row cross-node bit-identity stands as a statement about those outputs. Its *"repo commit `dabfeb854ec6`, **clean tree**"* is **not witnessed by the run directory** — that arm's `RUNMETA` records `git_dirty: None`, not `false`, and carries no blob field (measured by me). **D28 is the same shape a third time** — 230 rows bit-identical across a blob change — and inherits the same limitation, which is why AM-14 is written once for all three |
| E1 | **UNAFFECTED** | the refusal-recovery endpoint is untouched |
| **E2** | **UNAFFECTED; gains a directly relevant number** | D21's C1 is stated in E2's currency (rank-1 LOO ρ **0.5629** basket vs **0.5021** button, and E2 records button's r1 as 0.5021). **D26 now supplies the effect that C1 would have to explain, measured**: a probe main effect of **+0.001696** [+0.000912, +0.002497]. **There is still no ρ→z calibration anywhere in this sprint and no held-out ρ recorded anywhere**, so the gap E2 and D21 name is narrowed by one measurement and **not closed** |
| **C1** | **UNAFFECTED — and explicitly NOT touched by anything in this block** | every result here is measured on **`y_install`**, the concept-free one-word readout, **not on refusal**. Basket's behavioural endpoint is still at floor with one movable refusal event in 180 rows |
| C2, C3 | **UNAFFECTED** | |
| **C4** | **UNAFFECTED** | every arm in this block patches a **behavioural**-fit axis; *"is a semantic-fit axis causal?"* remains **deferred, not withdrawn** |
| AM-1, AM-2, AM-3, AM-4, AM-9 | **UNAFFECTED** | the captured-fraction pair, the amplitude-vs-energy correction, D13's discharged half-2×2 caveat and the denominator rule are untouched. **AM-4 remains binding and is obeyed**: every fraction in this block names its denominator (D25's **1.4 %** is *of the whole-state* `KO_FULL − KO` = +0.10938 in button) |
| AM-5, AM-7 | **UNAFFECTED; AM-7's authoritative n46 reads re-verified** | both basket n46 artifacts reproduce to 5 dp (see D12 row above) |
| **AM-6** | **UNAFFECTED, and OBEYED** | *"an artifact's existence is not evidence it is complete."* **All nine artifacts cited in A6/A7 were `json.load`-verified by me with their byte counts before these rows were written**, and the two reports quoted at full precision were additionally recomputed from their own `controls` blocks |
| **AM-8** | **UNAFFECTED; its remedy is BLOCKED** | AM-8b's finding stands (the analyser's `min_controls=19` string is off by one; **K ≥ 20** is required because `round(1/20, 4) = 0.05` is not `< 0.05`). **AM-13 records that the family that would have reached K = 24 was not launched**, so the correction remains a statement about an unreachable threshold |
| prohibitions 1–18, 22, 25, 28 | **UNAFFECTED** | |
| **19, 20** | **UNAFFECTED; still governed by AM-4** | both remain correct; nothing in this block changes the basket effect size or its denominators |
| **21** | **STRENGTHENED on the button side** | *"button ranks 4 of 11 on both splits"* is a **L20** statement and is untouched. **At L18 button's failure is now certified at 46 controls (D23), which is a stronger form of the same prohibition's point.** Its *"do not write that the dissociation is fully de-confounded"* clause is **unaffected** |
| **23, 24, 26** | **UNAFFECTED; 24 and 26 governed by AM-13** | 26's three clauses — **floor-limited, TRAIN-only, in-sample** — are reinforced, not loosened, because the family extension did not run |
| **27** | **STANDS; its prescribed remedy is SUPERSEDED by a stronger one** | 27 forbids quoting *"basket rank 1 of 47 vs button rank 4 of 11"* without the **matched-10** figure beside it, because those two are not the same test. **D24 supplies a better answer than the matched-10 subset**: at L18, with **46 controls of identical composition on both sides and the same 67 TRAIN domains**, basket is **1 of 47** and button is **36 of 47** — one test, one floor (0.0213), measured rather than projected. **The prohibition is not retired**: the matched-10 pair and D21's caveat 1 remain the required companions whenever the **L20** cells are quoted, and the matched-46 measurement exists **only at L18 and only on TRAIN for button** |

**The four questions this audit was specifically asked to answer:**

* **Does any pre-existing row state, imply or leave room for the WITHDRAWN S-138 headline?**
  **No — measured, not assumed.** `grep -ic "STATE hypothesis"` and `grep -ic "C1 is SUPPORTED"` over
  the 461 pre-existing lines both return **0**. The table was last written at `ad1288d6` (**S-135**),
  which **predates** the swap read, so the gap was a gap and never a wrong claim. **The corrected
  version (D25) is what enters; the withdrawn version enters only as AM-10, marked WITHDRAWN.**
* **Is anything in the table CONTRADICTED by the new results?**
  **No row is contradicted.** Three are **superseded in family size or key set** without a change of
  verdict (D13, D15's button-L18 cell, and D22/D17's provenance framing), and those are recorded as
  amendments rather than rewordings. The only genuine **tension** is D21's *"exactly one survivor,
  C1"*, which PR-CSI-006 tested and the preregistration's rule answers **against** — flagged in the
  D21 audit row and governed by AM-10, D25, D26 and prohibitions 29–31.
* **Does the word "swap" already mean something else in this file?**
  **Yes, and it is a live collision.** All **three** pre-existing occurrences (lines 30, 161, 313)
  are the **LAYER swap** of D13/D15 (*"basket's probe, refit at L20"*), not the cross-codeword
  **AXIS swap** of D25. Every new row says **cross-codeword axis swap** in full, and any future row
  must disambiguate or the two experiments will be read as one.
* **Does anything in the table now rest on a provenance claim the artifacts cannot support?**
  **Yes: D17, D22 and D28.** All three are bit-identity anchors whose *measurements* are sound and
  whose *identification of the code that produced them* is not recoverable from the run directories,
  because `RUNMETA` carries `git_commit` and `git_dirty` but **no blob**, and `git_dirty` is `None`
  — unrecorded — on the arms whose cleanliness the claim depends on. **AM-14** governs all three. The
  fix (print `git hash-object`, require `git status --porcelain` empty) is a VOID condition of
  PR-CSI-007 and was exercised at its launch.

---

## Commands run to produce this block, 2026-09-20

All read-only. **No SLURM job launched and none disturbed** (PR-CSI-007's 914043–914048 untouched);
**no analyser run** — `dcs_csi_subspace_analyze.py` and `dcs_csi_rederive_subspace.py` were never
invoked, and **no number from any `csi1_button_validation_*_20260920_*` run directory was read,
reported or implied**; **no edit** to `src/`, `scripts/`, `configs/`, `runargs/`, `slurm_scripts/`
or the sprint log; **no `git commit` and no `git push`**. The **only** file written is
`reports/DCS_CSI_CLAIM_TABLE.md`, and only by appending this block.

```
# --- artifacts read with json.load (9), all verified non-empty, parseable, byte counts shown ---
#   DCS_CSI_SUBSPACE_button_train_L18_n46.json             1 759 285 B
#   DCS_CSI_REDERIVE_button_train_L18_n46.json                 7 136 B
#   DCS_CSI_SUBSPACE_button_train_L18_shufonly.json          976 770 B
#   DCS_CSI_SWAP_button_train_L18_from_basket_n46.json     1 759 838 B
#   DCS_CSI_SWAP_basket_train_L18_from_button_n46.json     1 766 606 B
#   DCS_CSI_SWAP_basket_validation_L18_from_button_n46.json  726 250 B
#   DCS_CSI_SWAP_REDERIVE_button_train_L18_from_basket.json    7 173 B
#   DCS_CSI_SWAP_REDERIVE_basket_train_L18_from_button.json    7 165 B
#   DCS_CSI_SWAP_REDERIVE_basket_validation_L18_from_button.json 7 445 B
#   (plus DCS_CSI_SUBSPACE_basket_train_n46.json and _basket_validation_n46.json, re-read for D24,
#    and configs/dcs_csi_pr006_axis_swap.json + configs/dcs_csi_pr005_button_L18_family.json 58 174 B)

# --- D23: the PRIMARY statistic X, recomputed by me from the report's own controls block ---
#   candidate = -0.00014 ; controls = 46 ; convention ">=" (the analyser's own)
#   STAGE1 = KO_RAND0..5 + KO_SHUF0..3   ->  7 exceedances
#       KO_RAND1 KO_RAND2 KO_RAND3 KO_RAND5 KO_SHUF0 KO_SHUF1 KO_SHUF2
#   36 NEW BLIND controls                ->  X = 28
#   total 35  =>  R47 = 36    (report says candidate_rank_among_controls = 36 : MATCH)
#   prereg: X ~ BetaBinomial(36, 7.5, 3.5) E[X]=24.5455 sd 5.5307 median 25 q2.5=13 q97.5=34
#           P(X<=12)=2.297e-02  P(X<=4)=2.055e-04  P(X=0)=6.461e-07     X=28 INSIDE [13,34]

# --- D23: leave-one-domain-out, run VERBATIM from runargs/dcs_csi_pr005_read.txt section 3.3 ---
python scripts/dcs_csi_rank_loo.py --tag-prefix csi1_button_train --split train \
  --expect-n 670 --allow-short 4 --require-rescue-layer 18 \
  --require-slurm-job 902004,902005,912835,912836,912837
#   -> n_domains=67  full cand=-0.00015 rank=36 of 47
#      histogram {31:1, 32:2, 33:3, 34:6, 35:12, 36:21, 37:22}
#      BEST attainable rank under any single deletion = 31 of 47 (printing_works)
#      cand range -0.00029 .. +0.00003   (66 of 67 drops negative)
#   CONTROL, and the reason prohibition 33 exists: the SAME LOO recomputed from the report's
#   domain_means (stored ROUNDED TO 5 dp) gives {30:1, 32:3, 33:6, 34:6, 35:16, 36:20, 37:15},
#   best rank 30, 65 of 67 negative. Same verdict, different histogram. Use the script.

# --- D25: BOTH ranks recomputed inside EACH swap report, from its own controls block ---
#   button/train  from basket : cand +0.00150 -> rank  4 of 47 (report says 4 : MATCH)
#                               native KO_AXIS -0.00014 -> rank 36 of 47 ; ctrl max +0.00179
#   basket/train  from button : cand +0.00090 -> rank 13 of 47 (report says 13 : MATCH)
#                               native KO_AXIS +0.00265 -> rank  1 of 47 ; ctrl max +0.00238
#   basket/valid  from button : cand +0.00224 -> rank  2 of 47 (report says 2 : MATCH)
#                               native KO_AXIS +0.00401 -> rank  1 of 47 ; ctrl max +0.00278
#   KO_ORTH is NOT in any control family (verified by name scan) -- it is the comparator.
#   VERDICT string on all three: "PRIMARY DOES NOT PASS ... INSIDE the controls, not above them."
#   re-derivation twins: ranks 4 / 13 / 2 and candidates +0.00149 / +0.00090 / +0.00224.

# --- D24: the three matched cells, read side by side ---
#   basket L18 TRAIN  n46  642 keys / 67 dom  cand +0.00264 [+0.00068,+0.00471] 44/23  rank  1 of 47
#   basket L18 VALID  n46  215 keys / 23 dom  cand +0.00401 [+0.00098,+0.00775] 15/ 8  rank  1 of 47
#   button L18 TRAIN  n46  626 keys / 67 dom  cand -0.00014 [-0.00111,+0.00081] 36/31  rank 36 of 47
#   family composition identical in all three: KO_RAND0..21 (22) + KO_SHUF0..23 (24) = 46
#   resolved_rescue_layers = 18 on every rescue arm of every cell (measured, not assumed)

# --- D28 / AM-14: the S-139 anchor pair recomputed by me from results.jsonl ---
#   A csi1_basket_validation_CODEANCHOR_139B_20260920_190627_488644  job 913407
#       git_commit d515cc76  git_dirty None  compute_capability 8.6   (24 RUNMETA keys)
#   B csi1_basket_validation_STAGEANCHOR_AXIS_20260920_170734_754715 job 913232
#       git_commit 1cce381e  git_dirty None  compute_capability ABSENT (23 RUNMETA keys)
#   rows selected on rescue_liveness.fired ; non-vacuity asserted before any diff (S-134)
#   COMPARISON SIZE: A fired=230  B fired=230  common=230  A-only=0  B-only=0
#     logp_concept / logp_codeword / semantic_logodds / p_concept / p_codeword / top1_id
#     max|diff| = 0.000e+00   nonzero_rows = 0 / 230   present 230/230 on all six
#   RUNMETA keys mentioning blob/hash/sha: []   on every run dir inspected
#   git rev-parse d515cc76:src/boombness/score_behavior.py     -> e94258bd5fc44c70629e707b00504b7acac2a7b7
#   git rev-parse d515cc76:doublespeak_causality/ds_common.py  -> 557d86698fa327e9678fb3c5a646e73edb13f8c3
#   git show d515cc76:<both files> | grep -c compute_capability -> 0 and 0
#     ... yet job 913407 records compute_capability 8.6  => git_commit is NOT a witness.
#   git rev-parse HEAD:doublespeak_causality/ds_common.py      -> 95fb640b... (5 occurrences)
#   AM-14 (a): csi1_button_train_CODEANCHOR_R0_20260920_135631_905054 job 912838
#              git_dirty = None  (NOT false)  -- D22's "clean tree" is not witnessed
#   AM-14 (b): csi1_button_train_KO_RAND0_20260916_223555_2963342     job 902005
#              git_dirty = True             -- the falsifying direction IS recorded

# --- AM-13: the blob that blocks PR-CSI-003-A, measured rather than quoted ---
#   git hash-object src/boombness/score_behavior.py -> 11d2c61747e9401e2d2cb8f4123dd1188674d61b
#   git rev-parse HEAD:src/boombness/score_behavior.py -> 11d2c617... (equal; HEAD = c146f36c)
#   blob under which PR-CSI-003 halves 1-2, PR-CSI-005 and PR-CSI-006 ran -> e94258bd...
#   => VOID condition 6 fires. 20 arms NOT LAUNCHED. Necessity floor stays 0.1111 at 8 controls.

# --- audit greps over the 461 pre-existing lines ---
#   grep -ic "STATE hypothesis"  -> 0      grep -ic "C1 is SUPPORTED" -> 0
#   grep -ic "swap"              -> 3      all three are the LAYER swap (lines 30, 161, 313)
```

**Append verified per S-124 (EDQUOT is asynchronous; exit status is not evidence):** line count
**461 → 751**, byte count **80 923 → 137386**;
`diff <(head -461 <new>) <pre-image>` returns **empty**, `cmp -n 80923` against the pre-image
returns **equal**, and the pre-existing `| D` rows are all still present verbatim.

**Reported and deliberately NOT acted on, per the standing freeze:** (1) `RUNMETA.json` records no
`score_behavior.py` blob, which is what makes D17, D22 and D28 unverifiable after the fact (AM-14) —
the fix is already a VOID condition of PR-CSI-007 but the schema itself is unchanged, and
`doublespeak_causality/ds_common.py` may not be touched while 914043–914048 run. (2) The one-rank
disagreement between the two shuffled-only paths at button L18 (19 of 25 at 651 keys vs 20 of 25 at
627 keys) is a key-set artifact that **no gate currently detects**; it is benign here because both
say DOES NOT PASS, and it would not be benign near a floor. (3) `domain_means` is persisted at 5 dp,
which silently changes any LOO recomputed from it (prohibition 33) — a **persistence-precision**
defect, not a computation defect, and no committed number is affected.


---

## A8. NEW ROWS — PR-CSI-007, the button L18 **VALIDATION** read (54 of 54 arms, read once, 2026-09-21)

| # | claim | statistic (with CI and n_domains) | population / split / codeword / layer | caveats | source |
|---|---|---|---|---|---|
| D29 | **PR-CSI-007: button at L18 on the HELD-OUT split ranks 6 of 47 — it DOES NOT PASS, and by the preregistration's own decision rule the TRAIN result DOES NOT REPLICATE.** The prespecified 95 % band was [24, 43] and the point prediction 32; the observation is **18 ranks below the bottom of the band** and is recorded as a **SURPRISE**, not absorbed | **R47 = 6 of 47**, `rank_p` **0.12766**, attainable floor **1/47 = 0.021277**, and **NO ARITHMETIC FLOOR** — every rank 1…47 was attainable, unlike PR-CSI-005 whose pooled rank was bounded at ≥ 8 before its experiment ran. Candidate `KO_AXIS − KO` = **+0.00218** ci95 **[+0.00030, +0.00406]**, **15 pos / 8 neg of 23 domains**, p = 0.0371. PRIMARY `candidate − comparator` (`KO_ORTH`) = **+0.00151** [−0.00017, +0.00309], 17/6, p = 0.0885. Gates: manipulation `KO − BASE` = **−0.28319** [−0.33649, −0.23910], **0 pos / 23 neg**, p at floor; identity `KO_SELF − KO` = **+0.00084** [−0.00092, +0.00253], p = 0.365, abs ≤ 0.005 — **inert**; positive control `KO_FULL − KO` = **+0.13326** [+0.11327, +0.15390], **23 pos / 0 neg**, p at floor. **S1** z = **+1.3999** (TRAIN L18 was −0.5702 — the sign is flipped). **S2** exceedance (R47−1)/46 = **5/46 = 0.10870**, Clopper-Pearson 95 % **[0.0362, 0.2357]**, against TRAIN's 35/46 = 0.76087 [0.6123, 0.8741] — **the two intervals do not overlap**. **S3** subfamilies: shuffled-only **4 of 25** (floor 0.0400), random-only **3 of 23** (floor 0.043478), both DOES NOT PASS. **S4** leave-one-domain-out **{3:2, 4:1, 5:4, 6:12, 7:3, 8:1}**, best attainable rank under any single deletion **3**, **no deletion reaches rank 1**, candidate sign negative in **0 of 23** drops. **S5** `specificity_holm`: **0 of 46** controls rejected at 0.05, smallest `p_holm` **0.05497** (`KO_SHUF13`), 33 of 46 at 1.0. **S6** = the candidate − comparator figure above. Independent re-derivation, sharing no code, reproduces **6 of 47**, random-only **3 of 23**, shuffled-only **4 of 25** | **221 keys** common to all arms / **23 VALIDATION domains**, **54 arms**, **button**, **L18**, site `rel-6`, `semantic_one_word`, cell C, dose 4, 46 controls. All 54 arms on **RTX 3090**; `expect_n` uniformly 230; rows 228–230, none below the `--allow-short 4` bound of 226; `rescue_layer` 18 on all 52 rescue arms; `norm_match_key` `cand_rank1` on all 46 controls; `VOID []`; all three gates **true** | **THIS IS NOT A PASS.** Only R47 ≤ 2 certifies; five controls recover at least as much as the candidate, which sits **inside** the control distribution. It is **NOT "nearly significant"** — p = R47/47 and the nearest certifying value is 2. The decision branch is quoted verbatim: *"3 ≤ R47 ≤ 12 → top quartile, does NOT certify. The train result does not replicate. NOT a pass, NOT 'nearly significant'."* **The pre-committed counterweight applies** (R47 = 6 ∈ [3, 15]) and its sentence, written before the data so it could not be upgraded, is the operative reading: *"the L18 validation cell is closer to button's own-layer behaviour than the L18 train cell was, and nothing certifies"* — button's axis at its **own** layer L20 ranks 4 of 11 on **both** splits (+0.00132 validation, +0.00040 train), certifying nothing either way. **Nothing here says button's axis is or is not causal** (prohibition 19). **Nothing pools** button with basket, or this family's controls with TRAIN's — disjoint domains, and the blobs differ: this family ran at `11d2c617`, the TRAIN family before the S-139 edit. The family is **not extended**; 46 is this preregistration's terminal K | **S-160**, **S-163** (`reports/DCS_CSI_SUBSPACE_button_validation_L18_n46.json` 722 373 B, `reports/DCS_CSI_REDERIVE_button_validation_L18_n46.json` 7 386 B, `reports/DCS_CSI_SUBSPACE_button_validation_L18_shufonly.json` 402 976 B, `reports/DCS_CSI_SUBSPACE_button_validation_L18_randonly.json` 373 772 B, prereg `configs/dcs_csi_pr007_button_L18_validation.json`) |
| D30 | **The direction-A swap at VALIDATION passes its bar at rank 1 of 47 — and by PR-CSI-006's fixed rule that makes direction A NOT REPLICATED with NO CELL CLAIMED, because TRAIN was rank 4. The swap and button's own axis are NOT statistically distinguishable on the same domains** | Swap `XSWAP_FROM_BASKET` **rank 1 of 47**, `rank_p` **0.02128** — *"strictly the largest of 46 controls"*. Recovery `XSWAP − KO` = **+0.00338** ci95 **[+0.00122, +0.00559]**, **18 pos / 5 neg of 23**, p = 0.00737; `candidate − comparator` **+0.00271** [+0.00055, +0.00489], p = 0.02566. Native `KO_AXIS` **inside the same report on the same key set**: **+0.00218**, **rank 6 of 47**. **THE REQUIRED PAIRED CONTRAST** `recovery(XSWAP) − recovery(KO_AXIS)` over the same 23 domains = **+0.00120**, domain-clustered bootstrap 95 % CI **[−0.00043, +0.00283]** (B = 20 000, seed 20260913), **13 pos / 10 neg / 0 tied**, **EXACT two-sided sign-flip p = 0.171858** over all 2²³ = 8 388 608 permutations — **the CI includes zero**. **S3 dose penalty** ‖P_recipient(δ)‖/‖P_donor(δ)‖ from `captured_frac`: swap 0.037871, native 0.038978, **ratio 1.0292 — near 1.0**, which by the preregistration's own rule means the two axes capture button's delta about equally and the dose-matching was **nearly inert**. **Degeneracy count 0** (required), `liveness_violations` 0, `basis_keys ['swap_cand_from_basket']` — the donor tensor, not a relabelled native one. Independent re-derivation: pooled **1 of 47**, random-only **1 of 23**, shuffled-only **1 of 25** | **221 keys / 23 VALIDATION domains**, 55 arms incl. the swap, recipient **button**, donor **basket**, **L18**, site `rel-6`, `semantic_one_word`, cell C, dose 4, 46 controls, `VOID []`, all gates true. Swap arm from job **914048**, admitted to PART 5 only | **THE RANK IS A PASS; THE DIRECTION IS NOT REPLICATED.** PR-CSI-006 `decision_rule/step_6`: TRAIN rank 4 (= **NOT** helps, by its own `definition_of_HELPS`) against VALIDATION rank 1 puts the two splits on **opposite sides of the R47 ≤ 2 bar**, so the direction is **NOT REPLICATED and no cell is claimed for it**. **This may NOT be reported as "basket's axis rescues button held-out"** — forbidden by name in the frozen read. **A passing swap moves the 2×2 further from resolution, not closer**, and no outcome here restores the headline R10 withdrew. **A rank gap is not an effect gap**: ranks 1 vs 6 with a paired contrast at p = 0.17 is R10's direction-B precedent repeating on direction A. **"Disagree" means which side of the bar**, not that the recoveries differ; TRAIN's swap was +0.00150 on 67 domains and VALIDATION's +0.00338 on 23, and **no two-sample test of that difference has been run**. **D27 governs this rank too** — the swap arm is not exchangeable with its control family, so rank 1's p is **descriptive**. **CANNOT ANSWER**: the prereg asks for the dose penalty's *median* over admitted rows; the per-row rescale factor is not persisted, only `captured_frac` mean/min/max, so the median is **not recoverable** without a re-run the prereg forbids | **S-161**, **S-163** (`reports/DCS_CSI_SWAP_button_validation_L18_from_basket_n46.json` 736 112 B, `reports/DCS_CSI_SWAP_REDERIVE_button_validation_L18_from_basket.json` 7 407 B, prereg `configs/dcs_csi_pr006_axis_swap.json` + `configs/dcs_csi_pr007_button_L18_validation.json`) |

---

## A9. AMENDMENTS — corrections to rows above, additive and marked

| # | amends | what changes | why | source |
|---|---|---|---|---|
| AM-15 | **D25 headline, and prohibition 29's mandatory companion sentence** | D25's headline reads *"CELL 4 on TRAIN, direction B NOT REPLICATED, and C1 REFUTED BY THE FIXED RULE"*, and prohibition 29 makes that sentence a **required companion** wherever the swap is mentioned. **It no longer holds, and the companion sentence must be restated as: "NO CELL IS CLAIMED FOR EITHER DIRECTION — direction B NOT REPLICATED (train 13 vs validation 2), direction A NOT REPLICATED (train 4 vs validation 1). The 2×2 is unresolved in both directions and C1 is neither refuted nor supported by it."** | CELL 4 was reached by reading **both** directions on TRAIN and finding neither helped. Direction A now **has** a validation split (D30) and its two splits fall on opposite sides of the R47 ≤ 2 bar, which fires `decision_rule/step_6` exactly as it fired for direction B. A cell requires both directions to yield a claimable reading; **neither does.** The withdrawal of the C1-SUPPORTED headline (AM-10) is **unaffected and still stands** — this amendment removes the *opposite* claim as well, leaving the 2×2 empty | **S-161**, **S-163**, REVIEW **R12** |
| AM-16 | **D25 caveat, last clause** | *"TRAIN-only on direction A: direction A has never had a validation split, so the 'no cell is claimed if the splits disagree' clause has never been able to bind it"* — **WITHDRAWN.** Direction A has had a validation split since 2026-09-21 and **the clause bound it on the first occasion it could** | The clause was described as structurally inapplicable; it was merely untested. Its first application produced NOT REPLICATED | **S-161**, REVIEW **R12** |
| AM-17 | **D23 caveat** | *"no button-L18 VALIDATION arm existed when this was read … PR-CSI-007 is running to close exactly this gap and its result is NOT IN THIS FILE"* — **superseded by D29.** D23's TRAIN statistics and its TRAIN-only certification are **unaffected**; what changes is the standing of the gap it names. **The held-out cell does NOT replicate the TRAIN failure**: rank 36 → 6, z −0.5702 → +1.3999, exceedance 35/46 → 5/46 with **non-overlapping** Clopper-Pearson intervals | The row correctly declared its own gap and correctly refused to speak for the held-out split. The gap is now closed, and closed against the direction D23's prediction implied | **S-160**, **S-163** |
| AM-18 | **D24 caveat** | *"Button has no held-out L18 cell: the dissociation at matched power is TRAIN-only on the button side (PR-CSI-007 running; nothing from it here)"* — **superseded by D29.** The matched-power TRAIN-vs-TRAIN comparison in D24 is **unchanged and still correct as a TRAIN statement**; what is no longer true is that the button side has no held-out cell. **The held-out button cell is rank 6 of 47, against basket's held-out rank 1 of 47** — both cells now exist, and they are **reported side by side and never pooled** (§3.3) | D24's own wording anticipated this ("nothing from it here"), so the row needs an amendment rather than a withdrawal | **S-160** |
| AM-19 | **D13 caveat, first clause** | *"TRAIN only — button has no held-out L18 arms"* — **superseded.** Button now has held-out L18 arms (D29). **D13's finding is unaffected**: it is a 10-control, floor-0.0909 comparison of button's axis at **L18 vs its own L20**, and D29 is a 46-control family at L18 only. **D13's second caveat still binds** — basket has never been run at L20, so the layer half of the 2×2 remains open | Different family size, different floor, different question; only the "no held-out arms" clause is stale | **S-160** |
| AM-20 | **D23 headline wording** | *"button at L18 with 46 controls DOES NOT PASS"* → **"DOES NOT PASS ON TRAIN"**, and *"button's failure is CERTIFIABLE"* → **"button's TRAIN failure is CERTIFIABLE"**. No statistic, caveat or source changes; the row's population cell already read *626 keys / 67 TRAIN domains* and its caveat already read *TRAIN ONLY*. **Only the headline was unqualified**, and a headline is what gets quoted | PR-CSI-007's decision branch obliges: *"Every sentence in the sprint that states button's L18 failure without naming the split is amended to name it."* A measured sweep found exactly one unqualified headline in this file (D23) and three sentences in the append-only log, which cannot be edited and are amended by restatement in S-165 | **S-165**, REVIEW **R12** |


---

## A10. NEW ROW — PR-CSI-009, the extraction-hardware A/B (2026-09-21)

| # | claim | statistic (with CI and n_domains) | population / split / codeword / layer | caveats | source |
|---|---|---|---|---|---|
| D31 | **The codeword dissociation's behavioural channel is NOT confounded with extraction hardware. Basket's fitted direction is the SAME direction whether its activations came from a Tesla V100 (emulated bf16) or an RTX 3090 (native).** REVIEW R11's MAJOR-1 is closed by measurement | **abs(cos(w_new, w_committed))** on `cand_rank1`: **L18 = 0.998406**, **L20 = 0.997866**. Residual 1 − abs(cos) = **0.001594** and **0.002134**, both inside bf16's ~2⁻⁸ = **0.0039** relative precision — float noise, and a cosine of exactly 1.0 would have been the surprising result. **Calibration scale, from D27's own committed numbers**: 46 controls against the native axis give min 0.0001 / median 0.0156 / **max 0.1894**, and the cross-codeword swap axis is 0.5569. All four vectors unit-norm, dim 4096. **Fit population identical on all four**: 670 fit rows / 67 TRAIN domains. **The A/B is one token**: `--layers 0,2,…,31` → `--layers 18,20`, with **33 non-exempt arguments verified identical**, bank sha16 `79511d9e254571e6` equal to the committed axis's own record, model revision `0e9e39f249a1` on **both** runs, and corpus population `3720 → 3714` on both | **670 fit rows / 67 TRAIN domains**, basket, **L18 and L20**, site `rel-6` (resolved BY NAME), `--fit-prompt behavioral`, seed 20260915. New corpus `cont1re_behavioral_basket_bomb_20260921_081723_897277`, job **914750**, RTX 3090 `compute_capability 8.6` read from RUNMETA and not the sbatch line. Gate 0 PASS on all 7 VOID conditions, incl. VOID 7 (both committed axes byte-unchanged) | **The threshold and the prediction were committed at 08:07:11, nine minutes before the job existed** — git history, not a sentence in a file. **This closes ONE candidate explanation and nothing else**: it is NOT evidence for any other, it says NOTHING about button (no button arm exists here; pooling forbidden by §3.3), and it does NOT mean basket's axis is *correct* — a direction unchanged under a hardware swap is not thereby a right direction. **The layer ARGMAX was NOT re-run**: the new corpus carries `layer_grid [18, 20]` against the committed `[16,18,20,22,24,26,28,30,31]`, so this asks whether the direction moved *at the layer each committed axis selected*, not whether the selection would have moved. **A code-identity difference was found and checked**: the new corpus captures **23 sites** against the committed 20 (three extra `cw_demo_*` sites appended after `cw_demo_mean`) with all 33 args identical, i.e. the extraction code changed — inert for the fit, because `dcs_csi_axis.py:67` resolves the site by NAME and `:68` the layer by VALUE, measured rather than assumed | **S-167**, **S-168**, **S-169** (`reports/DCS_CSI_PR009_HARDWARE_AB.json` 2 457 B, prereg `configs/dcs_csi_pr009_basket_reextract_3090.json`, axes `configs/dcs_csi_axis_basket_behavioral_RE3090_L18.pt` / `..._L20.pt`) |

| # | amends | what changes | why | source |
|---|---|---|---|---|
| AM-21 | **The live-candidate list carried by AM-15 … AM-20 and by S-144's status line** | REVIEW R11's MAJOR-1 — extraction hardware — is **no longer a live unrefuted candidate explanation** of the codeword dissociation. **One candidate remains live: the held-out non-replication of button's L18 TRAIN failure** (D29: rank 36 → 6, z −0.5702 → +1.3999, exceedance 35/46 → 5/46 with non-overlapping CIs, and a prespecified band [24, 43] missed by 18 ranks) | Measured by D31 at abs(cos) 0.998406 / 0.997866 against a threshold fixed before the data. The confound was never a claim in this table — it lived only in the sprint log and in `scripts/gates/dcs_csi_axis_hardware_provenance.py`, which is itself the reason it is being written down here now | **S-169**, REVIEW **R11** |
