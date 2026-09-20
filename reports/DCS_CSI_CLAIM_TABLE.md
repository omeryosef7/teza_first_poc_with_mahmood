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
