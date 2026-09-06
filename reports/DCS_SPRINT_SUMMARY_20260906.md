# DCS sprint summary — state of the phase as of 2026-09-06

**Scope.** The DCS phase (Doublespeak Concept-Specific Bombness + surgical causal validation) as
recorded in `external_md/DCS_BOMBNESS_SPECIFICITY_AND_CAUSAL_VALIDATION_PLAN_AND_PROGRESS_20260905.md`,
§§1–71. This file is a **new dated version**. It does not edit and does not delete
`reports/SPRINT_SUMMARY_2026-09-02_TO_09-05.md`, which covers the earlier window and stops before
every headline below.

**Reading rule.** Every result here carries its caveats **in the same block**. The caveats are not
decoration: in three cases (`R-086`, `R-092`, `R-093`) the caveat changes what the number is allowed
to mean. §9 lists sentences that must never be written, and it is binding on any document derived
from this one.

**Reproduction note.** `A-031` DECISION 1: any re-run intended to reproduce a **published** number
uses `OMP_NUM_THREADS=4`. `OMP_NUM_THREADS=1` elsewhere, for speed only.

---

## 0. The phase in one line

> Doublespeak installs a concept-specific state at the codeword that a linear probe can read on
> held-out domains; the demonstration→query attention path is **necessary for the model to report**
> that mapping, and **not necessary for the state to remain decodable**.
> (`R-093` §64.5)

---

## 1. `R-086` — the concept-identity probe. POSITIVE, verified four times.

**Status: `POSITIVE — concept-specific`** (`PR-035`, restored by `R-089` after `C-058` was retracted).

> On **held-out domains**, a linear probe on the codeword's **L6–14** hidden state identifies **which
> of bomb / knife / gun** the demonstrations installed — **0.7485** against a **0.3333** chance,
> **6/6** leave-one-domain-out folds, permutation **p = 0.004975** from a test measured to reject
> noise at **0.030**. ⚠ **`p = 0.004975` IS the attainable floor** at `n_perm = 200` (`1/201`), i.e.
> the smallest value this test can emit — not a measured tail. §44.1.

| element | value |
|---|---|
| primary accuracy | **0.7485380116959064** |
| per-domain | city_bridge .77193 · farm_storage .842105 · game_manual .54386 · instructional .929825 · lab_safety .77193 · news_report .631579 |
| bomb-absent control (knife vs club) | **0.8596**, p = 0.0498, test FPR 0.020, power 0.760 |
| length-only control | 0.336 vs null q95 0.488 (does not match) |
| blocking null (`n_examples = 0`) | 0.3333 at chance, 0/6 domains, p = 1.0 (`R-084`) |

**Four independent reproductions** (the producer run is the SOURCE, not one of them):

1. job **854618**, an independent recomputation from banks and caches — **all 16 digits** (§44.1);
2. `A-029`'s full verification pass once `V2` was made a real check (`A-028` retracted the earlier
   vacuous `V2 PASS`). ⚠ Its `V4` re-ran the permutation on a **different seed (90613)** and matched
   **inside a stated Monte-Carlo band** (0.0050 vs 0.004975) — ⛔ **not** to 16 digits, and a
   different event from (1) (§50.2);
3. `A-031` §57.1's thread-invariance recomputation at both `OMP=4` and `OMP=1` — **identical to 16
   digits**;
4. the `PR-043` re-run (§68.1), a **fifth** exact hit on `0.7485380116959064`.

**Why the bomb-absent control matters:** `R-078` measured installation strength as +13.08 (bomb),
+6.435 (club), +4.089 (knife), +4.098 (gun, and gun installs in only 4/6 domains). Bomb installs **3.20×** knife
and **3.19×** gun — but only **2.03×** club (13.084 / 6.435). ⚠ The "~3× harder than any hard
negative" phrasing inherited from §21 is **wrong against club**; club is the nearest hard negative on
strength, which is precisely why it is the control. A 3-way probe could in principle separate on
*strength* rather than *identity*. Knife-vs-club has similar strengths and **contains no bomb term at all**, and it
separates. That is what licenses "identity, not strength alone".

**Caveats — all of them travel:**

- ⛔ **Decodability, not causality.** `A-025` `F-3` (arXiv 2605.04061) reports 0 % task transfer
  across all 28 layers of Llama-3.2-3B *despite 100 % probing accuracy*. The causal gate is `R5`,
  and `R5` is now run: see §4 — the signal **survives** the knockout.
- ⛔ **Not "bomb vs generic remapping"** on the cell-`F` comparator: its p is invalid (`C-057`) and it
  is block-confounded (`C-053` §28.5). `A-031` DECISION 3 makes it **permanently descriptive on this
  bank** — cell `F` is the only benign-remap cell that exists (24 rows, one block), so no disjoint
  selection population can ever exist for it.
- ⛔ **`P1` is UNINFORMATIVE**, not a concept negative — 504 `literal` rows vs 144. `A-031` `C2`:
  once re-run with a balanced fit it would publish a **floor** p-value regardless of signal, so
  `P1` must be reported with **no p-value at all**.
- ⛔ **Lexical transfer is bounded by `R-092`/`C-066`** (§3): the classifier does not transfer by
  accuracy across codewords, though the direction does by ranking.
- ⚠ The 2-class control is **underpowered by construction** (power 0.760 where a symmetry-free null
  reaches 0.940) — clearing 0.0498 was *harder* than the number looks, not easier.
- ⛔ **The capability gate is VACUOUS.** `train-fold accuracy = 1.0 everywhere`: at 4096 dimensions
  the probe separates its own training fold perfectly, so `PR-031` §6.6's capability gate is
  **trivially passed and carries no information** (§44.4).
- ⚠ **The gun-excluded form, which `R-078` mandated be reported alongside.** The 2-way
  `{bomb, knife}` primary is **0.9078947368421053**, 6/6 domains, permutation
  **p = 0.04975124378109453**. §21 requires the primary be reported *both with and without gun*,
  **neither promoted**. ⛔ It is **not** one of `C-057`'s two invalid instruments.
- ⛔ **Two pre-declared instruments are ABSENT and are reported as absent, not quietly dropped**
  (§28.9, §38): §9.3's **4-way-with-`club` secondary** (deleted by the `C-050` edit) and §21.2(2)'s
  **installation-strength covariate** — which was control (2) of three fixed in advance against the
  very strength confound this section relies on the club control to answer.
- ⚠ **`R-082` bounds the K-ladder reading** (§31): over the same 380 prompts, 380/380 with zero
  variation, **neither occurrence of the codeword ` button` enters the cut until `K = 11`**, while
  the effect has already reached 100 % of Δ-8 by `K = 8`. ⇒ ⛔ The codeword's own rows are **not in
  the cut at `K*`**, which is what makes §5's reading precise.
- ⚠ **One model, one codeword, 6 domains, one layer band.**
- ⚠ **How close this came to being lost:** a correct, verified headline was overturned by the log's
  own author on a sign error (`C-058`), committed and reported, and recovered only because a
  *measured* false-positive rate is mandatory before a null is trusted — and the first measurement
  was itself wrong. Two successive measurements were needed to undo one piece of bad reasoning.

---

## 2. `R-091` — remapping axis ≠ concept axis, and this reconciles `R-002`

`scripts/dcs_diffmeans_directions.py`, 44 s CPU, zero GPU. Directions estimated on **train domains
only**, leave-one-domain-out over n = 6, paired on `family_id`. **No layer selection and no
hyper-parameter anywhere** — the statistic is the mean over the inherited L6–14 band. Four numbers
were independently re-derived to 10 significant figures by a verifier with its own loader.

| direction | *is it remapped?* (`C_bomb` vs `A_bomb`) | *which concept?* (`C_bomb` vs pooled `C_{knife,gun,club}`) |
|---|---|---|
| **`v_bomb`** (raw diff-in-means) | **AUROC 0.9987**, d 5.755, 6/6 | **0.5743** — vs `gun` **0.4978**, i.e. chance |
| **`v_bomb_specific`** (= `v_bomb` − mean of the three) | 0.6070, 3/6 | **AUROC 0.8964**, d 1.786, **6/6** |

⇒ The two axes are **nearly complementary**. The raw difference-in-means is a **remapping** axis and
is almost blind to *which* concept; the residualized direction is a **concept-identity** axis and
barely registers remapping.

**Primary:** `v_bomb_specific`, held-out `C_bomb` vs pooled negatives, band-mean AUROC vs 0.5, exact
two-sided sign test over 6 domains ⇒ **6/6, p = 0.03125 = the attainable floor.** Per-layer profile
is **flat** (0.880–0.912) ⇒ not a single-layer artifact.

**Controls:** bomb-absent `v_knife − v_club` on held-out `C_knife` vs `C_club` ⇒ **AUROC 0.9815**,
d 4.796, 6/6 (basket 0.9657) — the strongest single row in the result, and immune to a bomb-anchored
strength axis. Blocking null passes exactly (‖`v_bomb`‖ = 0.000, AUROC 0.5000, 0/6; `A` vs `C`
byte-identical 12/12). Synthetic calibration: 50 replicates carrying a shared remap but no concept
component ⇒ FPR **0.040**. Cache binding q95 rel-err 5.8e-07 on all 8 runs.

### 2.1 `C-065` — what this does to the inherited `R-002` negative

`R-002` found the `toward_B_frac` geometry proxy **not bomb-specific**, with knife/gun/club matching
or exceeding bomb, and the phase has carried it as "a negative under one instrument" since it opened.
`R-091` says **why**: that proxy measured movement along the **remapping** axis, and `v_bomb` versus
the hard negatives is **0.5743, with `gun` at exactly chance**.

⇒ ⛔ `R-002` was **not** a failure to find concept specificity; it was a correct measurement of an
axis that does not carry it. ⛔ `R-002` is **not retracted** — its measurement stands. What changes is
its **interpretation**.

**Caveats:**

- ⛔ **The strength confound is not fully closed by the primary.** `v_bomb_specific` subtracts a mean
  over three concepts of very unequal installation strength; the z-projections show it (`C_club`
  −4.218, `C_gun` −0.621). A strength component is **present inside the primary** and this instrument
  cannot decompose it. Only the **bomb-absent** control is immune — and that control is descriptive.
- ⚠ Cell-`A` overlap on the exact families used: bomb/knife 6/168, bomb/gun 12/168, bomb/club 18/168.
  On those the cell-`A` term cancels exactly; on the other ~90 % a benign-corpus difference survives
  as a nuisance term.
- ⛔ **n = 6.** Only 6/6 or 0/6 can clear α; 5/6 gives p = 0.21875. Declared before the data.
- ⚠ Its descriptive lexical-transfer number (0.9204; 0.8754 with the shared-domain channel removed)
  must be read next to §3 — a **different instrument** from `R-092`'s classifier.
- ⛔ Still a **decodability** result.

---

## 3. `R-092` + `C-066` — gate `R3` FAILS on accuracy; the DIRECTION transfers at AUROC 0.795

⛔ **These two must never be reported one without the other.** Reporting `R-092` alone publishes a
false sentence; reporting `C-066` alone rescues a gate that failed.

### 3.1 `R-092` — the gate, as preregistered

`scripts/dcs_pr041_lexical_transfer.py`, committed before it ran. Train on **button** cell `C`, test
on **basket** cell `C`, selection on **button** cell `B`, leave-one-domain-out across codewords.
Populations verified 228/class both sides.

| domain | held-out basket accuracy |
|---|---|
| city_bridge | 0.6754 |
| instructional | 0.3509 |
| news_report | 0.3509 |
| farm_storage | **0.3333** ⇐ exactly chance |
| game_manual | **0.3333** ⇐ exactly chance |
| lab_safety | **0.3333** ⇐ exactly chance |
| **mean** | **0.3962** (chance 0.3333; `R3-FAIL` bar 0.4164) |

⇒ **`R3-FAIL`**, on the **magnitude** criterion `PR-041` §60.4 declared in advance.

⚠ **The significance half is uninformative by construction:** three domains sit at *exactly* chance,
their signed deviations are zero, the sign test drops them, n falls 6 → 3, and the attainable floor
rises **0.03125 → 0.25**. "The sign test fails" here is arithmetic, not evidence.

### 3.2 `C-066` — the retraction, and the corrected statement

Scoring the **same** button-trained classifier (same folds, same `(L=6, C=0.01)` every fold picked)
by macro one-vs-rest AUROC, which is pure ranking and invariant to any per-class offset:

| domain | argmax acc | macro OvR AUROC |
|---|---|---|
| city_bridge | 0.6754 | 0.8691 |
| farm_storage | **0.3333** | **0.9317** |
| game_manual | 0.3333 | 0.5185 |
| instructional | 0.3509 | 0.8668 |
| lab_safety | **0.3333** | **0.8386** |
| news_report | 0.3509 | 0.7462 |
| **mean** | **0.3962** (chance 0.333) | **0.7951** (chance 0.500) |

⛔ `R-092` §61.2's sentence — *"the concept signal is codeword-specific: present in both, encoded in
different directions"* — is **WRONG and RETRACTED.** The directions are **shared**. What fails to
transfer is the **decision offset**: the button-fitted boundary sits in the wrong place for basket
states, so `argmax` collapses even though the ordering is preserved.

> **The corrected scientific statement:** *the concept direction is shared across codewords and
> transfers by ranking (AUROC 0.795 macro OvR; 0.9204 by the independent diff-in-means instrument);
> the absolute decision boundary is codeword-specific and does not transfer.*

**Caveats:**

- ✅⛔ **Gate `R3` still FAILS as preregistered.** §60.3 declared held-out **accuracy**; 0.3962 is what
  it is. We are **not** switching to AUROC to rescue the gate — that is metric-shopping, and it is the
  second time in one day a better-behaved metric became available after a failure (§58.1 was the
  first, on the bridge).
- ⚠ `C-066` is a **descriptive diagnostic with no p-value.** It changes no verdict.
- ⛔ The frozen analyzer's `P2_basket_lexical_transfer` = **0.6974, 6/6 domains** is **basket-trained
  and basket-tested** (`C-064` §57.2). It is **mislabelled** and may **not** be cited as transfer.
  `A-031` DECISION 2 records `R3` as **NOT IMPLEMENTED** in the frozen file; adding `train_rows=` to a
  frozen published file is a preregistration question, not an edit.
- ⚠ `game_manual` is the one genuinely weak domain (AUROC 0.5185) — and it is also weakest in the
  frozen basket-trained arm (0.500). That is a **domain** property, not a transfer property.
- ⇒ `R-086` is **bounded, not overturned**, and less bounded than `R-092` §61.4 first said: the
  signal is not confined to one lexical setting, but a classifier trained in one **cannot be applied
  unchanged** to another.
- ⚠ Method note worth keeping: a leave-one-group-out classifier's **accuracy conflates** whether the
  representation carries the label with whether the boundary is portable. Any transfer claim in this
  phase should report **both** an offset-free ranking statistic **and** the accuracy, and say which
  one the gate is defined on.

---

## 4. `R-093` — gate `R5`: `R5-FAIL`. The readout/representation dissociation.

`PR-040` / `PR-040a` / `PR-040b`. Six arms, **zero aborts**, 228/class both sides, 48 selection rows,
bank binding verified per class, every fold picking `(L=6, C=0.01)`. Analyzer committed at `8cc126b7`
⚠ **before any arm was analyzed** — five of six arms also landed after that commit; the sixth finished
writing 9 s earlier, so *"before the arms landed"* is the wrong phrasing for one of six —
**before** the arms landed. Probe is **`P2`**, clarified in `PR-040b` **before any number was read**
(`PR-040` §55.2's prose said "train on cell `B`", which is `P1`; the frozen analyzer implements `P2`,
and all three of `PR-040`'s operative quantities are `P2`'s).

### 4.1 The bridge validated itself

| | value |
|---|---|
| `ko_off` baseline (bridge, knockout disabled) | **0.7529** |
| `R-086` published (original extractor) | **0.7485** |
| difference | **0.0044** ⇐ VOID bar was 0.10 |

Disabled-vs-baseline cosine **0.999849**, knockout-enabled cosine **0.7639** (rel-L2 0.0140 vs
0.3764, a **27×** separation) ⇒ the knockout demonstrably fires. `PR-040a` amended the design
**pre-data** so the primary compares `ko_on` against `ko_off` **bridge-to-bridge**, which cancels the
1.4 % code-path offset exactly.

### 4.2 The result

| domain | `ko_off` | `ko_on` | drop |
|---|---|---|---|
| city_bridge | 0.7807 | 0.7632 | +0.018 |
| farm_storage | 0.8421 | 0.8596 | **−0.018** |
| game_manual | 0.5526 | 0.5263 | +0.026 |
| instructional | 0.9298 | 0.8509 | +0.079 |
| lab_safety | 0.7719 | 0.7018 | +0.070 |
| news_report | 0.6404 | 0.5263 | +0.114 |
| **mean** | **0.7529** | **0.7047** | **+0.0482** |

Sign test **5/6**, **p = 0.21875**, floor **0.03125**. The drop is **11.5 %** of the 0.4196 available,
below `PR-040` §55.4's 20 % `R5-FAIL` bar. ⇒ ⛔ **`R5-FAIL`: the concept signal SURVIVES.**

⚠ This is an **informative** negative, not an uninformative one: the floor was 0.03125 and the design
**could** have cleared α — unlike `R-092`, where ties raised the floor to 0.25. The test had the power
to detect a drop and found 11.5 %.

**Secondary (§55.5, no p):** train-on-KO / test-on-KO = **0.7120**. That branch existed to separate
*gone* from *re-based* **given a drop**; with no real drop it is confirmatory —
0.7120 ≈ 0.7047 ≈ 0.7529 ⇒ the representation is **intact and in the same basis**. ⛔ The script's
printed label *"PRESENT BUT RE-BASED"* is that branch's wording and **overstates**; the correct
reading is **PRESENT AND UNMOVED**.

### 4.3 The dissociation — same bank, same band, same `demo_all` scope

| measurement | baseline | whole-query knockout | |
|---|---|---|---|
| **readout** — `semantic_logodds` (`R-083`'s `ref` arm) | **+3.3696** | **−3.0151** | ⛔ **sign flip**, Δ −6.38 |
| **representation** — concept probe (this result) | **0.7529** | **0.7047** | ✅ **94 % retained** |

⇒ The same intervention, on the same bank, in the same layer band, **destroys the model's ability to
report the mapping while leaving which concept was installed decodable from the codeword's hidden
state.**

**Caveats:**

- ⛔ **Not "the knockout does nothing."** It abolishes the forced-choice preference; `R-010`/`R-011`
  and `R-083`'s `ref` arm stand entirely.
- ⛔ **Not a claim about behaviour.** `R-075` remains an underpowered negative; PHASE 7 / gate `R8` is
  unrun.
- ⛔ **No dose-matched control is feasible on this bank** (`B-018`) ⇒ this is a localisation
  **conditional on `R-080`**, not independent evidence about demonstration keys.
- ⚠ The two rows above are **different instruments at different sites** — a generated forced-choice
  answer vs a probe on `codeword_last` hidden states. The dissociation is between **what the model
  can report** and **what is linearly decodable**, ⛔ not between two measurements of one quantity.
- ⚠ It arrives one level earlier than the brief's §36 expected: it was posed as
  *representation vs behaviour*; this is *representation vs **readout***.
- ⚠ `game_manual` is weak throughout (0.5526 baseline); `farm_storage` moves the **wrong way**
  (−0.018). **n = 6.**

---

### 4.4 `R-093a` (§66) — the dissociation survives a MATCHED-POPULATION check

Restricting the probe to `PR-037`'s exact three blocks (`core2x2`, `core2x2_slot3`, `role_style`),
168 rows/class: `ko_off` **0.7361** → `ko_on` **0.6865**, drop **+0.0496** = **12.3 %** of available.
⚠ **Only 4/6 domains**, with `city_bridge` moving **−0.119** the wrong way. ⚠ On those rows the probe
retains **~88 %** of its available range, not the **94 %** §4.2 leads with. ⇒ The two arms are the
same intervention on the same rows; the dissociation is not a population artefact.

### 4.5 ⛔ `C-068` (§69) — `R-093`'s DESCRIPTION must be corrected, though its verdict stands

Gate `R6` re-ran the same probe against a knockout scoped to **only the codeword's own query row**
(`target_surface_row_only`, 1.7 % of the whole-query dose, exact closed-form liveness on 7560 rows).
It reproduced `R-093` **to sixteen digits** — every per-domain value. The cause is arithmetic, not
empirical:

* all six folds pick **`L = 6`**, the **first layer of the `6–14` knockout band**;
* at the band's first layer no lower layer is perturbed, so the read row's state is a function of
  unperturbed inputs masked by **its own query row** — and both scopes block the same keys there;
* measured: `ko_on` vs `ko1` at `L6`, **max abs elementwise difference 0.000e+00** over all 2520
  shared rows, rising to 0.36 at `L7` and 1.42 at `L14`.

⇒ ⛔ **Gate `R6` is CANNOT ANSWER / UNINFORMATIVE BY CONSTRUCTION** — not a null, not a confirmation.
⇒ ⚠ **And at `R-093`'s own expense:** at `L = 6`, the only layer any of its folds reads, `R-093`'s
"whole-query" manipulation is **arithmetically identical to blocking the single codeword row**. The
verdict (`R5-FAIL`, dissociation) is unchanged; ⛔ the sentence *"destroying the whole
demonstration→query pathway"* overstates what was in force at the site read.

⚠ **General trap, for the methods section:** *any* band-limited intervention read at the band's
**first** layer measures only the read row's own mask.

### 4.6 `R-096` (§71) — above the degenerate layer the scopes DO separate

Re-read on layers **7–14** (a structural exclusion derivable from the band definition, applied
uniformly to both arms and to selection, declared in `PR-045` **before** the numbers):

| | baseline | knockout | drop | domains | of available |
|---|---|---|---|---|---|
| `KO-1`, codeword row only | 0.6784 | 0.6594 | **+0.0190** | 4/6 | 5.5 % |
| `KO-legacy`, whole query | 0.6784 | 0.6418 | **+0.0365** | 5/6 | 10.6 % |

⚠ Dropping `L6` costs the baseline **0.0745** (below the declared 0.10 VOID bar, **narrowly**), so
these are weaker measurements on a weaker probe. ⛔ **No p-values.** The ratio **0.520** is
descriptive with no bar. ✅ What it buys: `R-093`'s dissociation **survives** on a grid `L6` cannot
influence — even the whole-query knockout removes only **10.6 %** of available accuracy.

### 4.7 PHASE 7 / `R8` (`PR-042`) — ⛔ CANNOT ANSWER, and the bound was computed before any ρ

The exact `n = 6` Spearman null over all **720** rank assignments: p-floor **2/720 = 0.002778**, and
of 18 attainable |ρ| levels **exactly three** reach α — 1.0000, 0.9429, 0.8857; the next rung
(0.8286) is p = 0.0583 and fails. ⇒ the bound is **Σd² ≤ 4**.

| | |
|---|---|
| predictor `x` (per-domain probe drop) reliability | **0.5758** vs 0.50 bar — ✅ **x is NOT at a floor** |
| outcome A (`mapping_use`) | ⛔ UNUSABLE — blind at baseline (`R-088`, GAP −0.0396 vs bar 1.0) |
| outcome B (semantic probe) | ⚠ available, but it is the model's **report**, not behaviour (§64.4) |
| outcome C (attack rate) | ⛔ NOT FEASIBLE — lives on `cds116`, whose shared-**name** domains share **0/672** byte-identical prompts and **3/960** demonstration sentences with this bank, at 10 judged rows/domain (binomial SE 0.158) |
| attenuation ceiling √(rel_x·rel_y) | **0.6039** < 0.8857, the smallest reachable |ρ| |
| power under a **perfectly monotone** truth | **0.2501** vs 0.50 bar — ⛔ FAIL |

⇒ ⛔ **`R8` is CANNOT ANSWER for two independent reasons**, the first of them design-level: **no
behavioural outcome exists on the bank `x` was measured on.** ⛔ ρ = +0.60 (p = 0.242) was computed
and is **NOT CITABLE IN EITHER DIRECTION**. ⛔ This is not a null; no null model was fitted.

---

## 5. `R-079` / `R-080` / `R-081` — the K ladder: `K* = 7`, `shape = STEP`, rungs 1–5 are chat scaffold

`R-079` first recovered, deterministically from the tokenizer over **all 380 prompts with zero
variation**, what `--knockout-scope query_last_k_rows` actually cuts: `query_span_positions` runs to
the true end of the **whole chat-templated prompt, generation header included**. `PR-036` then fixed
three predictions **in a git commit before any K = 4…7 row was read**; all three held.

| K | token newly cut | Δ (demo − control) | % of Δ₈ | domains − | p | Holm |
|---|---|---|---|---|---|---|
| 1 | `'\n\n'` (scaffold) | −0.0132 | 0.2 % | 23/38 | 2.56e-01 | — |
| 2 | `<\|end_header_id\|>` | −0.0115 | 0.2 % | 23/38 | 2.56e-01 | — |
| 3 | `assistant` | −0.0697 | 1.1 % | 35/38 | 6.68e-08 | ~0 |
| 4 | `<\|start_header_id\|>` | −0.0194 | 0.3 % | 21/38 | 6.27e-01 | 1.000 |
| 5 | `<\|eot_id\|>` | **+0.0225** | 0.3 % | 18/38 | 8.71e-01 | 1.000 |
| **6** | **`?`** — first user-text token | **−0.5015** | **7.6 %** | 34/38 | 6.04e-07 | ~0 |
| **7** | **`' bomb'`** — first content word | **−5.9849** | **90.5 %** | **38/38** | 7.28e-12 | ~0 |
| 8 | `' a'` | −6.6161 | 100 % | 38/38 | 7.28e-12 | — |

**`K* = 7`** (smallest K with Holm p ≤ 0.05 **and** |Δ| ≥ 0.5·|Δ₈|). **`shape = STEP`**, fired by the
declared criterion at K=6 → K=7 (0.076 → 0.905). Largest single-rung rise **+82.9 percentage points**.
The K=8 re-run three days later on a different node reproduced **−6.616111537245543** to the digit
(Δ = 0.000000), and K=1/2/16 reproduced inherited values as well.

> **Claimable, with its bound attached:** demonstration→query attention is **not required by the chat
> template's own scaffold tokens at all**; the requirement appears exactly where the cut reaches the
> question's content, and it is a **step, not a ramp** — 90 % of the full effect arrives with a single
> additional token.

**Caveats:**

- ⛔ **The decisive rung is structurally confounded, and this was declared before the numbers.** The
  token entering at K=7 is `' bomb'` **only because** the `semantic_forced_choice` question names both
  options. So this may **not** be written as *"blocking the codeword's query row breaks the mapping"*.
  An equally consistent reading is *"the question's concept-option token is where demonstration
  information is integrated for this readout"* — a fact about the **instrument** as much as the
  mechanism.
- ⛔ **Not "the mechanism is one token":** K=7 cuts K=1…6's tokens too, and row count and cut-cell
  count still rise together.
- ⛔ `R-021`/`R-022`'s bracketing ("the transition is between 3 and 8 rows") is **superseded**, and any
  sentence of the form *"one or two query rows do not need demonstration access"* must not be written
  — those rungs were **not query rows at all**.
- ⚠ **The profile is not monotone**: K=5 is **+0.0225**, the wrong sign, 18/38 domains.
- ⚠ **K=3 is significant at a 1.1 % magnitude** (35/38 domains, p = 6.7e-08) while K=4 and K=5 sit at
  chance. Significance at n = 38 domains does **not** imply a mechanistically meaningful effect; the
  K=3 rung is the phase's cleanest demonstration of that, and it has **no explanation**.
- ⚠ `option_mass` collapses across the transition (0.878 → 0.853 → **0.409** → 0.368), so the rungs
  carrying the effect are measured where the forced-choice options hold under half the probability
  mass — and the collapse **tracks Δ**, so it is not an independent check.
- ⚠ The separating follow-up — the same ladder on `semantic_one_word`, whose question never names the
  concept — was run as `PR-037` and returned **`CANNOT ANSWER` by 1.9 points** (`R-083`: 48.1 % of the
  full-query effect against a preregistered 50 % bar, 6/6 domains at the p-floor). The bar was not
  moved. That result also **corrects our own `KO-1`**: the codeword's query row *is* necessary on
  `semantic_one_word` and is not on the forced-choice template ⇒ `KO-1`'s null is bounded to its
  template.

---

## 6. `R-085` — the control masks are not row-independent. One seed per arm.

`scripts/dcs_mask_overlap.py`, **zero GPU**, 56–83 s, reusing the persisted `control_draw` positions
and importing `nondemo_control_draw` rather than reimplementing it. Provenance hard-checked and
**passed on all 9,280 rows**.

Primary: absolute-position Jaccard over all C(1160,2) = 672,220 row pairs per arm, against a
row-independent sampling null (mean 0.2459 ± 0.0003) ⇒ observed **0.4772–0.5095, ≈ 2.0× the null,
z = +715…+815, 8/8 arms**, sign test over arms **p = 0.0078 = the attainable floor** (floors declared
before any p).

**Mechanism, verified in source:** `nondemo_draw_seed(control_seed, draw_index)` depends only on the
run seed and the draw index — **not on the row** — and `knockout_key_set` calls the sampler once per
row with that same seed. Measured: `distinct_draw_seeds = 1` in all 8 arms, and on the 701 row pairs
per arm with identical `(n_pool, k)` the pool-**rank** sets are **byte-identical in 1.0000 of pairs
versus 0.0000 under the null**.

**What it explains:** `R-077`'s split-half ρ = +0.988 and 93.5 % draw-offset variance — a measurement
that had no mechanism; and `R-076`'s null, because the offset is not a row-level property at all.

**Caveats:**

- ⛔ It does **not** invalidate `R-075`, `R-076` or `R-077`. Each measured what it measured. What
  changes is the interpretation of the **between-control spread**: not sampling noise over
  row-independent draws, but variation among **8 distinct systematic maskings**.
- ⚠ This is a property of the **control construction**, not a finding about doublespeak. It belongs
  in a methods section.
- ⛔ It does not say the control is *wrong* — a fixed mask per arm is a defensible design — only that
  the eight arms are **not** eight independent samples, so the spread across them **cannot be read as
  an error bar**.
- ⇒ It opens `Q-004` (§8), which is a design decision for the humans.

---

## 7. `R-088` — the intuitive readout is blind. And `R-090` — where you select matters more than which permutations.

### 7.1 `R-088` (PHASE 4, `PR-038`) — `CANNOT ANSWER` at its gate, and the reason is the result

Jobs 854632/854633, 48/48 rows each, zero failures. `PR-038` §40.3 fixed, before the data, a
normaliser `GAP = mean(base, C) − mean(base, A)` and declared `GAP < 1.0` log-odds ⇒ `CANNOT ANSWER`.

| baseline, `comprehension_usage` | value |
|---|---|
| cell `C` (`natural_doublespeak`) | −3.0581 |
| cell `A` (`benign_literal`) | −3.0185 |
| **`GAP`** | **−0.0396** (3/6 domains with C > A) |

⇒ The primary was **not computed**, exactly as preregistered. Without that gate we would have
differenced two arms on a readout that measures nothing, and could have reported a manufactured null.

The same `core2x2` block, same bank, same conditions, through two questions:

| question put to the model | cell `A` | cell `C` | swing |
|---|---|---|---|
| `semantic_forced_choice` — *"…does `button` refer to a button or to a bomb?"* | −7.272 | **+5.812** | **+13.08** |
| `comprehension_usage` — *"…is `button` used literally, or as a code for something else?"* | −3.019 | −3.058 | **−0.04** |

**0/24** benign and **1/24** doublespeak rows answer `coded`; per-domain means negative in 6/6 domains
in **both** cells.

⇒ Asked what the codeword refers to, the model says `bomb`. Asked whether the codeword is being used
as a code, the same model on the same prompt says `literally`. This is a direct answer to the brief's
§11: an *intuitive* readout was requested on the theory it would be cleaner than ASR — **on this
instrument it is not cleaner, it is blind.**

**Caveats:**

- ⛔ Not *"the model is unaware of the remapping"* — the forced-choice readout on the same prompt shows
  it is not. This is a fact about the **metalinguistic question**, not the model's state.
- ⛔ Not *"`comprehension_usage` is broken"*: its `option_mass` is 0.22–0.41, far above the 0.05 bar,
  so the model engages the offered options and answers `literal`.
- ⚠ One asymmetry, not to be over-read: `option_mass` is 0.224 in `A` vs 0.414 in `C` ⇒ the doublespeak
  condition moves the model toward *considering* the literal/coded distinction without moving *which*
  answer it gives.
- ⛔ PHASE 4 is **CLOSED at `CANNOT ANSWER`** and is **not** re-run with a lower `GAP` bar. The live
  successor is a **3-way object-level** probe ("Bomb / Button / Neither"), which is a new experiment
  needing its own preregistration, not a rescue of this one.

### 7.2 `R-090` — the calibration table, and the design lesson

Job 854780, 3 h 14 m. All four selection/null procedures × 2 class-counts × {pure noise, planted
signal}, same synthetic data, same seeds, 100 reps.

| | | FPR (noise, must be ≤ .05) | power (planted) |
|---|---|---|---|
| **3-class** | **cell `B` + ORIGINAL** ⇐ *the primary, as run* | ✅ **0.030** | 1.000 |
| | cell `B` + EXCLUDING | 0.030 | 1.000 |
| | test set + ORIGINAL | ⛔ 0.100 | 1.000 |
| | test set + EXCLUDING | ⛔ 0.100 | 1.000 |
| **2-class** | **cell `B` + ORIGINAL** ⇐ *clause 4, as run* | ✅ **0.020** | 0.760 |
| | cell `B` + EXCLUDING | 0.050 | 0.940 |
| | test set + ORIGINAL | ⛔ 0.090 | 0.840 |
| | test set + EXCLUDING | ⛔ 0.140 | 0.930 |

> **The lesson, for the paper's methods section:** in a leave-one-group-out design with a
> group-permutation null, **where the hyper-parameters are selected matters far more than which
> permutations the null contains.** Selecting on the test population and then freezing those picks
> across the null inflates the false-positive rate **3–5×**. Selecting on an independent population
> makes the same test **conservative**.

**Caveats:**

- ⛔ At 3 classes the two nulls are **indistinguishable on all four measurements** — the symmetry fires
  with probability 1/7776. `C-058` was not merely wrong in direction; at the primary's class count it
  argued about an effect that does not exist.
- ⚠ The cost of the symmetry is **power, not validity** (2-class 0.760 vs 0.940).
- ⛔ `PR-039` remains **UNADOPTED**: it changes a preregistered statistic, was proposed after seeing
  outcomes, and is irrelevant at 3 classes. `EXCLUDE_GLOBAL_RELABELS` stays `False`.
- ⚠ It generalises beyond this repo: any probing paper that grid-searches a layer on its evaluation
  set and then permutation-tests it has this defect, and the inflation is large.
- ⚠ `A-031` `C1`: `dcs_null_calibration2.py` at HEAD is **self-defeating** (the `C-061` gate made the
  EXCLUDING arms bit-identical to the ORIGINAL ones). `R-090` itself is safe — job 854780 ran at
  `cd6dc033`, before the gate landed — but re-running from HEAD cannot reproduce it.

---

## 8. Standing gates, and the open questions for the humans

**Gate family (brief §12).** ⛔ It **cannot** be reported as fully passed.

| gate | status |
|---|---|
| `R3` — lexical transfer | ⛔ **FAIL** on the preregistered accuracy statistic (`R-092`); direction transfers by ranking (`C-066`). Previously recorded as **NOT IMPLEMENTED** in the frozen analyzer (`A-031` DECISION 2). |
| `R5` — does the knockout destroy the concept signal? | ⛔ **`R5-FAIL`** — the signal survives (`R-093`). Informative negative. |
| `R6` — representation readout under `KO-1` | ⛔ **CANNOT ANSWER.** `PR-044` reproduced `R-093` to 16 digits because all six folds pick `L = 6`, the band's **first** layer, where the whole-query and surface-row-only knockouts produce a **bit-identical** tensor at the read row (max abs diff **0.000e+00** over 2520 rows) — `C-068` §69.2. `PR-045`'s layers-7–14 re-read is **descriptive**: `KO-1` +0.0190 vs `KO-legacy` +0.0365, ratio 0.520 (`R-096` §71). ⛔ Neither is a null. `KO-2`'s **behavioural** answer is already published (`R-006`/`R-009`) and must not be regenerated. |
| §13 — concept signal read at the explicit concept word | ⛔ **CANNOT ANSWER** — baseline **1.0000** in 6/6 domains on both grids. The capture site *is* the token ` bomb`, so the probe reads **lexical identity**; no layer repairs it (§69.3, §71.4). |
| `R8` / PHASE 7 — does destruction predict behaviour? | ⛔ **CANNOT ANSWER** (`PR-042`, §PHASE 7). No behavioural outcome exists on the bank `x` lives on; power under a **perfectly monotone** truth is **0.2501** against a 0.50 bar, and the attenuation ceiling 0.6039 sits below the smallest |ρ| that can reach α at n = 6 (0.8857). `R-075` stands as an **underpowered negative**, never "no effect". |
| installation gate (`PR-034` / `R-078`) | **PARTIAL** — bomb/knife/club PASS 6/6; **gun installs inconsistently across domains** (4/6). State it that way, never "gun does not remap". ⛔ `C-060` §46.3 bounds the PASSes: they mean *the demonstrations move the readout toward the concept*, **NOT** *the mapping is installed* — 44/48 bank × domain × `n_examples` cells install, and **6 further cells PASS the paired rule while cell `C`'s own mean log-odds is still negative** (gun/farm_storage/n8 −3.169; club/farm_storage/n4 −1.468; knife/farm_storage/n4 −1.339). |
| PHASE 4 (`PR-038`) | **CANNOT ANSWER**, closed (`R-088`). |

**Open questions — decisions for Omer / Matan, not for the log:**

- **`Q-001`** — does the aligned rebuild get funded, and on what result? ⚠ Cell `A` differs across
  concept banks **modally, not universally** — `C-060` §46.1 measured it: bomb and club share a
  **byte-identical cell-`A` demonstration block on 104/696 design cells** and a byte-identical
  **whole prompt on 82**, every concept pair shows 42–82 whole-prompt collisions, and the cause is
  9/40 shared benign sentences per domain between `demo_pools.json` and `demo_pools_club.json`.
  ⛔ **The sentence *"cell `A` is a different corpus in each concept bank"* may not be written
  unqualified** (§46.1). Cells `C`/`F` do sit in disjoint template blocks, and `A-031` DECISION 3
  adds that **cell `F` cannot be fixed on this bank at all** (24 rows, one block). An aligned bank
  fixes both, costs real GPU time, and changes the population.
- **`Q-002`** — **paper positioning against arXiv 2609.02438**, submitted **2026-09-02**, which
  publishes the representation-vs-behaviour dissociation framing in almost exactly our design shape.
  It does not scoop us (logical validity, not concept remapping; no attack; no attention
  intervention), but if we lead with dissociation it is a **citation, not a contribution**. The
  novelty sentence also narrows for the second time this phase against **arXiv 2504.00132**
  (Bakalova et al.), which already ablates demonstration→query edges in ICL.
- **`Q-003`** — the scratch purge. `/vol/scratch/omeryosef` was purged mid-session (`B-019`); the
  Llama-3.1-8B weights lived only there, and the project's `.cache/huggingface` symlink points into
  it, so every GPU job died with a misleading `mkdir: File exists` error on a dangling symlink.
  Nothing on disk was invalidated and the weights were re-downloaded — but **this will recur by
  policy**. Move the cache somewhere durable, or add a pre-flight symlink check to the wrapper?
  Shared infrastructure was not repointed unilaterally.
- **`Q-004`** — should control draws be **re-seeded per row** (`seed + hash(prompt_id)`), making arms
  genuinely exchangeable, or **kept fixed per arm** with the between-arm spread reported as systematic
  rather than stochastic (`R-085`)? It changes what a "control draw" means across the whole
  behavioural half.
- **`Q-005`** — answered: the bridge was built, and it validated itself (§4.1).

---

## 9. ⛔ Sentences that must NOT be written

Binding on this document and on anything derived from it.

1. ⛔ *"We are the first to causally intervene on demonstration→query attention in ICL."* — **false**.
   arXiv **2504.00132** (Bakalova et al.) ablates exactly those edges, at every layer and head
   simultaneously. What survives is narrow: we *zero* attention rather than patch counterfactual K/V,
   in a **layer band**, on a **semantic-remapping** condition, with an **intervention × condition**
   interaction and a **query-row-count threshold** — none of which that paper does.
2. ⛔ *"The model represents the codeword as BOMB."* — over-general, unqualified. The licensed form is
   *"the state of **this** codeword, in **this** lexical setting, carries which concept was
   installed"* (`R-092` §61.4, weakened but not lifted by `C-066`).
3. ⛔ *"The concept signal does not transfer across codewords."* — **`C-066` refutes it.** The
   direction is shared and transfers by ranking (AUROC 0.795); only the decision offset fails. Report
   the gate failure and the AUROC together, or neither.
4. ⛔ *"`KO-3` restores the literal meaning."* — **Qwen only** (`R-032`).
5. ⛔ **Any causal reading of `R-086`.** It is a **decodability** result, and `R-093` shows the signal
   **survives** the knockout that destroys the readout. "The probe finds the concept" licenses
   nothing about the model using it.
6. ⛔ *"The codeword's query row is not necessary."* — template-bounded (`C-054`); false as stated,
   because `R-083` shows it *is* necessary on `semantic_one_word`.
7. ⛔ *"K=1 and K=2 show one or two query rows don't matter."* — **false** (`R-079`); those rungs are
   chat-template scaffold.
8. ⛔ *"48.1 % is essentially 50 %, so it's the codeword row."* — the goalpost move `R-083` refused.
9. ⛔ *"The knockout does nothing"* / *"the intervention had no effect"* — it flips the semantic readout
   from **+3.3696 to −3.0151**.
10. ⛔ *"Gun does not remap."* — it installs **inconsistently across domains** (4/6).
11. ⛔ *"The representation is present but re-based"* (the `R-093` script's printed label) — it is
    **present and unmoved** (0.7120 ≈ 0.7047 ≈ 0.7529).
12. ⛔ Any citation of the frozen analyzer's **0.6974** as lexical transfer — it is basket-trained and
    basket-tested (`C-064`).
13. ⛔ Any p-value for the cell-`F` contrast or for `P1`, ever, from these banks (`A-031` DECISIONS 3,
    `C2`).
14. ⛔ *"Cell `A` is a different corpus in each concept bank"* — unqualified. It holds **modally**
    (250/348 ids), not universally (`C-060` §46.1).
15. ⛔ *"Gate `R6` passes"* or *"gate `R6` is null"* — `R6` has **no verdict** (`C-068`).
16. ⛔ *"The codeword's own row accounts for half the causal effect"* — the 0.520 ratio is two drops
    of 0.019 and 0.037 on a weakened probe, with no p-value and no bar (§71.3).
17. ⛔ *"The concept survives even when its own word is blocked"* from §13 — that readout is at
    **ceiling** and measures lexical identity (§69.3).
18. ⛔ *"Bomb installs ~3× harder than any hard negative"* — it is **2.03×** against club.
19. ⛔ Any novelty claim resting on a search that returned nothing — the query-row-threshold axis
    returned nothing on target, and that is recorded as a **null search, not evidence of novelty**.

---

## 10. Provenance

Every number above is quoted from the phase log
`external_md/DCS_BOMBNESS_SPECIFICITY_AND_CAUSAL_VALIDATION_PLAN_AND_PROGRESS_20260905.md`:
§21 (`R-078`), §26–§29 (`R-079`/`R-080`/`R-081`), §32 (`A-025` literature), §34 (`R-083`), §41
(`B-019`), §43 (`R-085`), §44/§50/§51 (`R-086`, `C-058` retracted), §48 (`R-088`), §54 (`R-089`),
§56 (`R-090`), §57 (`A-031`/`C-064`), §58 (`PR-040a`), §59 (`R-091`), §61 (`R-092`), §62 (`C-066`),
§63 (`PR-040b`), §64 (`R-093`), §65 (`PR-043`), §66 (`R-093a`), §67 (`PR-044`), §68
(`R-094`/`C-067`), §69 (`R-095`/`C-068`), §70 (`PR-045`), §71 (`R-096`), plus PHASE 7 (`PR-042`).
No number in this file was recomputed for it; nothing here is a new result.

⚠ **`C-067` (§68.3), which §5 depends on:** the leave-one-block-out (template-family) probe is
**UNINTERPRETABLE**. Its null mean is **0.8494**, not chance 0.3333, because LOBO folds on
`bank_block` while `group_permute` relabels per **domain** — so the relabelling hits train and test
identically and the classifier simply learns it. ⛔ **The held-out template-family claim has NO VALID
INSTRUMENT in this phase**; only the held-out **domain** claim (`R-086`) does. ⛔ Its null was **not**
fixed after the fact (§33, and the `C-062` precedent).
