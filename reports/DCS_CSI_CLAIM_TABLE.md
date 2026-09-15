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

---

## B. EXPLORATORY / DIRECTIONALLY CONSISTENT BUT UNDERPOWERED

| # | claim | statistic | why it is not in section A | source |
|---|---|---|---|---|
| E1 | Restoring the clean query span under the live knockout partially recovers refusal | Δ = +0.0278 [+0.0056, +0.0556]; recovery fraction 0.417 [0.133, 0.714] | rests on **5 of 90 domains**, all same-signed; exact sign-flip p = **0.0625 = its attainable floor**, so it **cannot reach α = 0.05**. The bootstrap CI excluded 0 essentially by construction — (85/90)^90 = 0.6 % | **S-002 (CORRECTION to `c029b4fb`)** |
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
10. "We found the Doublespeak phenomenon / the representation-convergence story." — published: Yona et al., *In-Context Representation Hijacking* (ACL 2026). What remains open is the **causal** chain, not the phenomenon.
11. Any bare ASR number — the literal-codeword false-positive floor and the 0.137 judge-flip rate must travel with it.
12. Anything marked A16, A17, K1, or WITHDRAWN in the predecessor audit.
13. **"The axis generalises across templates."** — D4 is *sentence*-level, not template-level (C3).
14. **"The axis differs across nodes / is hardware-sensitive."** — refuted; see D8 and S-019.
