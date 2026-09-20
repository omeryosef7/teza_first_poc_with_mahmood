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
