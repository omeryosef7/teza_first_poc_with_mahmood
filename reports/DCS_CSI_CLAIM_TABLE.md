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
| D12 | On **basket**, the rank-1 installation axis is the causally strongest direction in its control family, on **both** splits | TRAIN `KO_AXIS − KO` = **+0.00265** [0.00061, 0.00486], 44 pos / 23 neg, **rank 1 of 35**, rank p = **0.0286**; VALIDATION **+0.00400** [0.00098, 0.00774], 15 pos / 8 neg, **rank 1 of 31**, rank p = **0.0323**. Controls are norm-matched random subspaces and shuffled-label fits. Gates hold on both: `KO_FULL − KO` = +0.12131 (67/67 domains) TRAIN, +0.10306 (23/23) VALIDATION; `KO_SELF − KO` inside the preregistered 0.005 tol | 647 keys / **67 TRAIN domains** (41 arms); 218 keys / **23 VALIDATION domains** (37 arms); L18, site `rel-6`, `semantic_one_word`, cell C, dose 4 | **The effect is very small**: the axis recovers 0.0040 of a 0.229 knockout effect = **3.9 %**, and 3.9 % of what the whole state restores. Both rank p values are **at their attainable floors** (1/35, 1/31). The **shuffled-only** subfamily — the binding comparator per R5, whose sd is 1.9x the random family's at the same mean — is **rank 1 of 13 (floor 0.0769) TRAIN and rank 1 of 9 (floor 0.1111) VALIDATION**, i.e. **INCONCLUSIVE on its own, both splits**. Independently re-derived by `dcs_csi_rederive_subspace.py` (no shared code): 34/34 and 30/30 controls agreeing to 1e-5, same ranks | S-079, S-082, **S-088**, R5 (`reports/DCS_CSI_SUBSPACE_basket_train_n34.json`, `reports/DCS_CSI_SUBSPACE_basket_validation_n30.json`, `reports/DCS_CSI_REDERIVE_*.json`) |
| D10 | Recovery is linear in the **number** of query-span positions restored | through-origin `recovery = 0.002482·k`, **R² = 0.9968** TRAIN / 0.9939 VALIDATION; slope × 28 / `KO_FULL` = 0.984 / 0.987; `KO_POS28` ≡ `KO_FULL` exactly on distinct run dirs, both splits | button, both splits | linearity under **random** subsets does **not** imply uniformity — a concentrated effect gives the same curve (S-066) | S-059, S-063, S-077 |
| D11 | The offset the axis was fit at is causally near-inert | `rel −6` recovers **+0.00071 = 1.0 %** (39/28 domains) against a random position's +0.00281 | button TRAIN | the axis was fit at `rel −6` of the **behavioural** prompt; this measures `rel −6` of the **semantic** prompt — state the offset AND the prompt type every time (prohibition 15) | S-066, S-070, S-072 |

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
20. **"Basket's axis beats its fit-capacity-matched controls."** — NOT established on either split. The shuffled-label subfamily is floor-limited (1 of 13 TRAIN, 1 of 9 VALIDATION). Quoting the pooled rank without this is quoting the easier of two tests. Group K exists to resolve it and has **not run** (BLOCKER-S090).
21. **"The Phase-1 negative is overturned" / "the axis is causal in general".** — button ranks **4 of 11** on both splits. The honest summary is a **codeword dissociation**: basket replicates, button does not.
22. **"The volume / fileserver is degraded."** — WITHDRAWN (S-090). Measured from the login node and wrongly generalised; the same volume serves 309 MB/s to a node outside the `n-30x` rack. Say "the `n-30x` rack's NFS path is broken".
18. **Any predictive rho obtained from a `--fit-prompt semantic` fit.** That fit reads the state on the same forward whose next token is the target, so its only legitimate output is a **direction to intervene along** — never a prediction. (The shared loader's default still refuses such corpora; the Phase-1 opt-in is explicit and argued in S-025.)
