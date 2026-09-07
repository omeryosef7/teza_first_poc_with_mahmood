# DCS THESIS-SCALE PHASE — CLAIM TABLE, WHAT WE CAN SAY, WHAT WE MUST NOT SAY

Mandate deliverables **12, 13, 14** of
`external_md/DCS_THESIS_SCALE_MANDATE_20260906.md` (§34).

**Sources of every number below.** The authoritative record is the append-only log
`external_md/DCS_THESIS_SCALE_BOMBNESS_CAUSAL_CONFIRMATION_PLAN_AND_PROGRESS_20260906.md`;
entry ids (`R-xxx`, `C-xxx`, `A-xxx`, `PR-xxx`, `B-xxx`, `Q-xxx`) refer to it. Every cell in the
table carries either an entry id or an artifact path. Nothing here is a number I could not point at.

**The population, once, so the table can be read.** Bank family `ts116m`: six banks,
{`button`,`basket`} x {`bomb`,`knife`,`gun`}, 116 domains built, **three whole-population
exclusions** — `restaurant_kitchen` (`C-082`), `subway_station` (`C-087`), `school_campus`
(`R-108`) — leaving **113 domains analysed**, split **67 train / 23 validation / 23 test** by the
frozen manifest `data/boombness_prompts/dcs_ts116_domain_split.json`
(`manifest_sha16 = be7d2c772d814ef3`, seed `202609061`, `R-099`). Only the **harmful
demonstrations** differ across concepts; benign / remap / filler / preamble / skeleton / query are
byte-identical (`C-074`'s fix, `R-101`/`R-102`). All results are on **Llama-3.1-8B-Instruct**,
revision `0e9e39f249a16976918f6564b8830bc894c89659`, one model, one band, one layer convention
(`R-104`).

**STATUS vocabulary** — exactly the six the mandate allows, used as follows:
`CONFIRMED` (preregistered, powered, passed on untouched test) · `NARROWED` (the effect is real but
the claim as originally worded is not what was measured) · `UNSUPPORTED` (measured, and the
measurement does not support it) · `CANNOT ANSWER` (no adequately powered valid instrument exists on
this corpus) · `UNTESTED` (no experiment was run) · `VOID` (the instrument cannot answer the
question by construction; the claim is withdrawn).

---

## 1. THE CLAIM TABLE

| CLAIM | EVIDENCE | N_DOMAINS | TEST POPULATION | CAVEAT | STATUS |
|---|---|---|---|---|---|
| **A (as worded in mandate §32)** — the **codeword representation** contains the identity of the concept installed by the demonstrations | `R-113` (`PR-048`, `outputs/dcs_ts/pr048_result.json`) + `R-112` (`PR-051`, `reports/DCS_TS_PR051_POSITIONAL.md`) | 113 analysed; **23 test** | `ts116m` cell C, 23 untouched test domains, 67/23/23 frozen split | The decodability is real but is **not localised at the codeword**: a control **nine tokens downstream**, token-identical across concepts and carrying no concept token, decodes the same labels at **0.9261** vs the codeword's **0.9446** (`R-112`). Under the preregistered Holm within the SECONDARY family (8 members, first step α/8 = 0.00625) **both p-values fail** → codeword ≈ control | **NARROWED** |
| **A′ (the narrowed, defensible form)** — on an aligned 113-domain population the **installed concept is linearly decodable from the residual stream at layer 9**, above a measured surface baseline | `R-113`: domain-mean 3-way accuracy **0.9399** (chance 1/3), **23/23 test domains above chance**; selection layer 9, C=0.01, `n_tied=1/36`, `inert=False` (**not** the `C-070` degenerate selection); nuisance floor **0.9217** (concept-masked TF-IDF bag-of-words over the demo block, `A-041` G5 N5c) cleared by **0.0182** | **23 test** (of 113) | 23 untouched test domains, read **once** (job 862952); validation-only selection | Margin over the surface floor is **1.8 accuracy points**, and the floor is a **point estimate with no interval** — point compared to point. **Both p-values are AT their floors** and are statements about design resolution, not measurements: sign test p = 2.38419e-07 [floor 2.384e-07, k=23/23]; permutation p < 9.999e-05 [0/10000 exceedances]. Test (0.9399) came in **above** validation (0.9130) — flagged, no weight placed on it. This is a statement about **what is decodable from the prompt at this depth**, not about the codeword | **CONFIRMED** |
| **A″** — the codeword position is **special** / more concept-bearing than nearby positions | `R-112`: paired difference **+0.0185**, CI(t) [+0.0042, +0.0328], bootstrap [+0.0054, +0.0326]; permutation p = 0.0157 [floor 9.999e-05, 156 exceedances — **not** at floor]; sign p = 0.0129 with **9 of 23 domains exact ties** | **23 test** | Both sites bound to identical row sets: 4,520 rows, 113 domains, keyed on `(bank, prompt_id)`; 12 absent rows, **0 unexplained** | Uncorrected the difference is significant and that branch is reported, not withdrawn — but under preregistered Holm both fail; the effect is **under half the conjunctive MDE** of a design with power ≈1.000 at its declared δ=0.15; it closes only **25 %** of the headroom above a control that already decodes at 0.9261. Nuisance floor here is **0.0 by construction** (both arms see the same prompt, so every surface confound differences out) — **the cleanest instrument the phase owns, and it says gist** | **UNSUPPORTED** |
| **B (mandate §32)** — remapping and concept identity correspond to **separable** representational axes | `R-111` (`PR-053`, `scripts/dcs_ts_pr053_diffmeans.py`, `reports/DCS_TS_PR053_DIFFMEANS.md`), preregistered question **D** | 113; **23 test** | `ts116m`, train-only directions, 23 untouched test domains | `v_bomb_specific` was required to read identity and stay **weak** on generic remapping. It does not: **0.8309** polarity-free on C_knife/C_gun vs A (21/23 domains) and **0.8236** on C_bomb vs A, both clearing the surface floor. **The residual axis carries remapping and identity together — residualising changed the mixture, it did not decompose it.** `PR-053` required C *and* D precisely so this could be caught; a p-value cannot rescue a design whose question D failed | **UNSUPPORTED** |
| **B′ (the part that did hold)** — `v_bomb_specific` separates C_bomb from the hard negatives {C_knife, C_gun} | `R-111`: band-mean L6–14 domain-mean **AUROC 0.9764**, CI [0.9622, 0.9906], d = 3.03, **23/23 domains**, clearing the measured surface floor 0.7479 by 0.2285; permutation **p = 0.0454** [floor 9.999e-05, 453/10,000 — **not** at floor]. Holm across the PRIMARY family (`PR-048`, `PR-053`): **both REJECT** | **23 test** | 23 untouched test domains; directions fit on train only (the `D1` leak in `dcs_diffmeans_directions.py` was **fixed in `PR-053`, not inherited**) | **The null is BIMODAL** (sd 0.409): **4.5 % of arbitrary concept relabellings reach 0.9764**. The effect is enormous *and* the label-permutation evidence that it is specifically **BOMB** is thin — which is why p = 0.0454 sits beside an AUROC of 0.9764. Quoting the AUROC without that sentence badly overstates the case. The sign-test p (2.384e-07) **is** its own floor. This row does **not** rescue CLAIM B | **CONFIRMED** (as a discrimination result only) |
| **Inherited claim that the raw `v_bomb` axis does *not* read concept identity (~0.574)** | `R-111`: with the A term genuinely cancelling, **B = 0.8856**; A (remapping axis) = 0.9969; E button→basket transfer 0.9747, Spearman ρ = 0.9921 on per-domain ranks; F (n_ex=0 null) fires exactly — ‖v‖ = 0.0, all contrasts 0.5000 | **23 test** | `ts116m` | The old ~0.574 was an artifact of each concept having its **own unaligned baseline**. ⚠ The concept-relabelling null is **only properly centred for the residual family** (C null mean 0.4943, D 0.5065); for the raw family it is structurally off-centre (A 0.8794, B 0.2230) because `mean_j w_j = 0` exactly while `mean_j u_j` is the grand remapping direction. **A's and B's permutation p-values are not calibrated and must not be quoted.** The point estimates stand; their p-values do not | **VOID** (the inherited negative is withdrawn) |
| **C (mandate §32)** — the concept-specific direction **is / is not causally used** | none | 0 | none | **No intervention has been run in this phase.** There is no direct intervention on the concept axis, no matched control, no downstream semantic outcome. Nothing in `R-111`/`R-112`/`R-113` speaks to causal use in either direction | **UNTESTED** |
| **Installation** — the demonstrations actually install their concept **in the model** (as opposed to in the text) | none in this phase; a readout run (job **865335**) is in flight at the time of writing and has produced no result | 0 | none | This is currently an **assumption inherited from the design**, not a measurement. Every decodability number above is compatible with the model merely encoding what the demonstration text says. It must be stated as an assumption wherever CLAIM A′ is used | **UNTESTED** |
| **D (mandate §32)** — a specific **demonstration→query pathway** is required for the model's semantic report | none in this phase | 0 | none | Not run: this phase built and read representations, not attention interventions. The inherited instrument is separately compromised (next row) | **UNTESTED** |
| **Inherited "the whole-query pathway was removed" (`R-093`)** | `C-068`: **0 differing fp16 bit patterns over 2,520 rows in all three banks** at the L6 read site | 6 (inherited) | old 6-domain banks | The read site is degenerate by construction, so gate R6 is uninformative and the "whole-query knockout" is **arithmetically identical to blocking one row**. Mandate §33 already forbids the sentence | **VOID** |
| **E (mandate §32)** — **representation destruction predicts behavioural change** | PHASE 7 / R8, log §A-034.2 D | — | — | Two independent disqualifiers: **no behavioural outcome exists on the bank `x` was measured on**, and power is **0.2501 against a 0.50 bar under a perfectly monotone truth**. ρ = +0.60 is **not citable in either direction**. No behaviour, ASR or representation→behaviour mediation was run in this phase | **CANNOT ANSWER** |
| **Register was controlled** (hedging / threat-lexicon / sentence-structure differences between the concept arms) | `A-043`, `C-078`, `C-098`, `C-100`, `C-101`, `R-106`, `PR-050` WITHDRAWN, `PR-052` EXPLORATORY | 113 built; the cleanest contrast has **23 test** | `ts116m` | **Three instruments failed for one underlying reason.** N5 reads the **treatment** (`C-078`). `PR-047` **never existed** and no data was captured that could support it (`C-098`). `PR-049` (knife-vs-gun) is underpowered at its own Holm α — **0.793 / 0.905, not the published 0.900 / 0.963** (`C-101`) — and surface still reaches **0.7065** there. `PR-050` rests on a **false premise**: a partition cannot change pooled accuracy (0.5913 / 0.6630 under every one of 17 stratifications; refit-within 0.4986 / 0.5609) — **binning removes confidence, not information** (`C-100`). **Register is produced BY the manipulation**: natural bomb text hedges **13.72 %**, knife **0.20 %**, gun **2.33 %** (`R-106`). **No re-analysis of this corpus can fix it.** The costed fix is a **design** fix belonging to the next data build: regenerate the harm pools under an explicit register constraint (matched hedge rate, matched threat-lexicon density, matched sentence structure) — a new generation campaign with per-sentence constraints and a much stricter accept filter (`Q-014`) | **CANNOT ANSWER** |
| **INFRA — an aligned thesis-scale concept bank exists** | `R-102` / `R-105` / `R-109`: `ts116m`, six banks, **0 alignment violations, 19/19 gates PASS, 4/4 mutations RED**, per-bank `bank_rows_sha16` pinned; twelve extractions complete at two read sites, **0 unexplained missing rows** | 116 domain roster; **115** carried into the `ts116m` build (`R-102`) after the `restaurant_kitchen` exclusion; **113 analysed** | 67/23/23 frozen split, `manifest_sha16 be7d2c772d814ef3` | Only the harmful demonstrations differ; the codeword-substitution leak is closed (**0/6900 probe rows print their own concept word**, against 30/3680 before, `C-076`). Length is a **permanent stated nuisance**: the length-matching remedy **did not work** (N4 accuracy 0.4174 → 0.4014 but macro AUROC 0.5750 → **0.5793**, i.e. slightly up), and by a rule recorded before N4 was measured there is **no third round** (`R-102`). Cross-split verbatim leakage got **worse**, 3/2,760 → **15/2,760 (0.543 %)** (`C-083`) | **CONFIRMED** |
| **INFRA — the cell-A baseline is byte-identical across concepts, and cancels in arithmetic** | `R-111` gate V2: **3,616 / 3,616** cell-A prompts byte-identical across bomb ∧ knife ∧ gun at matched `prompt_id` in all six codeword×dose cells; and cell-A **hidden states from three separate extraction runs agree to `max|diff| = 0.000e+00`** | 113 | all six `ts116m` banks | This is the payoff of the aligned rebuild, **measured rather than argued** — the A term cancels in arithmetic, not merely in text. It is what makes the diff-in-means contrasts interpretable at all | **CONFIRMED** |
| **INFRA — the first aligned bank (`ts116`, `R-098`) had NO manipulation** | `C-074`: cell C × `semantic_one_word` (the primary) **1,856 / 1,856 = 100 % identical** across bomb ∧ knife ∧ gun; whole bank 7,424 / 22,272 = 33.3 %; extended by an adversarial agent to **14,848/14,848 triples over 44,544 rows**. 6,960 probe rows collapse to 2,320 distinct texts each carrying the full label multiset → **Bayes-optimal accuracy exactly 1/3, by arithmetic** | 116 | `ts116` | The word swap removed the concept word from a cell whose demo surface is already the codeword, so *"identical up to a swap of W"* and *"identical"* coincided when W did not occur. The files are **byte-exact and not deleted** — they remain valid for the narrower question *"is the doublespeak concept lexically separable at the codeword?"*, whose measured answer is **no, by construction**. Caught by the pre-GPU audits at **~2 hours wall-clock and zero GPU**; without them the phase would have reported a 0.333 pinned by arithmetic as a negative result **about the model** | **VOID** (as a concept-identity contrast) |
| **INFRA — an eight-instance occurrence-counting bug class, now named and closed by one shared rule** | `C-075` (right-permissive: `basketball` counts), `C-076` (singular-only vs `knives`), `C-079` (case-insensitive vs three enumerated case forms — *and* a plural-only sentence contributing **zero** codeword occurrences), `C-080` (**the same blindness inside the GATE** — `R-101`'s "19/19 PASS" **retracted**; re-run: `ts116n` 18/19 FAIL, `ts116m` 19/19 PASS), `C-087` (**the substituter itself**: `str.replace` has no word-boundary notion, so *"the gun … a large, black handgun"* ships as `handbutton`), `C-090` (the same defect **inside the `C-087` fix**, triplicated across three files; `gunfire`/`bombardment`/`knifepoint` all passed), plus `R-108` (30 extraction refusals, all `school_campus`, always exactly one more token occurrence than text occurrence) and `C-095` (a mutation harness printing "4/4 RED" while carrying **no mutation for either newly added gate**) | 116 scanned | all pool files and all six banks | **The rule that subsumes every special case: the checker's notion of "an occurrence" must be exactly the transformer's — and the substring count must equal the whole-word count.** Now implemented once and shared across generator, length matcher and gate. Measured live scope: **exactly one compound occurrence across all three pools** (`subway_station`, excluded, in TRAIN) and **1 hit in 13,920** on rescan for the `C-090` direction — the defects were caught **latent**, and the shipped banks are unaffected. Every instance was silent until something downstream refused | **CONFIRMED** (as a finding about the pipeline, not about the model) |
| **INFRA — the domain split is frozen and was built before any outcome existed** | `R-099`: `manifest_sha16 be7d2c772d814ef3`, `pools_sha16 976aa2b0b617118d`, seed `202609061`, field name **`dsplit`** (not the banks' existing within-domain `split`, which **all 116/116 domains straddle**); `--write` refuses to overwrite; **5 mutations, 5 RED** | 116 → 113 analysed | 67/23/23 | A join hazard found while verifying and binding on every analysis in the phase: the `button` and `basket` banks **share all 22,272 `prompt_id`s** — `prompt_id` does not encode the codeword, so joining on it alone silently pairs the wrong rows. The compound key `(bank_file_sha16, prompt_id)` is load-bearing, not a nicety | **CONFIRMED** |
| **INFRA — published thresholds are now machine-read, not prose** | `B-020` / `C-097`: `dcs_ts_prereg.py` defined `require_gate()`/`require_null()` and **the analyzer called neither**; 8 nulls declared, 1 implemented. **A knife-vs-gun result of 0.60 would have PASSED the frozen success rule while sitting below a 17-feature bag of surface counts.** Fixed: the floor is a machine-read field (`primary.nuisance_floor` = **0.9217** for the 3-way, **0.7065** for knife-vs-gun) fetched through `require()`, so a preregistration that forgets to declare one **cannot be analysed at all** | — | all `ts116m` analyses | `B-020` **recurred inside the code written to fix `B-020`**, one window later, by the same author. Amended **before any outcome existed**, which is the only reason the fix is believable | **CONFIRMED** |
| **`PR-049` knife-vs-gun as a register-clean co-primary** | `R-106` called it CO-PRIMARY on power 0.900; `C-101` recomputed the variance components (reproducing `PR-048`'s icc/deff/n_eff to four decimals, so this is a correction and not double-counting) and got **0.905 / 0.793** | 23 test | `ts116m` | **0.793 is below 0.80 at the Holm α `PR-049` itself declares.** The `R-106` CO-PRIMARY verdict is **withdrawn**; by `PR-049`'s own demotion rule it is **EXPLORATORY** and must not be promoted. Within the one clean stratum, power is **0.721** | **CANNOT ANSWER** (underpowered at its own α) |
| **`PR-050` surface-matched re-analysis** | `C-100`, `Z1`: 17 candidate stratifications, 100 strata scored for the 3-way and 74 for knife-vs-gun, **zero usable strata reach chance on either contrast** even under the weaker CI-covers rule | 23 test | `ts116m` | **WITHDRAWN, not amended** — its central premise ("within a surface-matched stratum the surface classifier is at chance by construction") is mathematically false. The file stays byte-frozen as the record of a design that did not survive its own first check; the loader now refuses it on `status != FROZEN`. `PR-052` carries the one construction that does balance (arm-balanced joint simplex cells, knife-vs-gun, surface accuracy **0.5054** CI [0.4629, 0.5479], 552 rows, 23 test domains) and is declared **EXPLORATORY before being run**, with `success` and `negative` both marked NOT AVAILABLE | **VOID** |

---

## 2. WHAT WE CAN SAY TO MATAN

Sentences Omer can speak as written. Each carries its number and its qualification **inline**;
none of them is safe with a clause removed.

1. "On a 113-domain aligned population where only the harmful demonstrations differ between arms —
   benign, remap, filler, preamble, skeleton and query are byte-identical, verified 3,616/3,616,
   and the cell-A hidden states from three separate extraction runs agree to max absolute
   difference 0.000e+00 — the installed concept is linearly decodable from the residual stream at
   layer 9, at 0.9399 domain-mean three-way accuracy over 23 test domains we had never read before,
   with 23 of 23 domains above chance." *(`R-113`, `outputs/dcs_ts/pr048_result.json`)*

2. "That 0.9399 clears a measured surface baseline — a concept-masked TF-IDF bag of words over the
   demonstration block, which reaches 0.9217 — by 1.8 accuracy points, and I want to say in the
   same sentence that the floor is a point estimate with no interval, so the honest claim is 'above
   the surface baseline', not 'far above' it." *(`R-113`; floor from `A-041` G5 N5c)*

3. "Both p-values on that result are at their floors — the sign test is exhausted at k=23/23 with
   p = 2.38419e-07 and the permutation has 0 exceedances in 10,000 — so they tell you the design
   cannot resolve further, not how extreme the effect is, and I am not quoting them as
   measurements." *(`R-113`; and this is exactly the `C-069` failure the phase was built to avoid)*

4. "It is a statement about the prompt, not about the codeword. A control position nine tokens
   downstream, token-identical across the three concepts and carrying no concept token, decodes the
   same labels at 0.9261 against the codeword's 0.9446 — a paired difference of +0.0185 which is
   significant uncorrected (permutation p = 0.0157) but fails the preregistered Holm correction
   within its eight-member secondary family, and which closes only 25 % of the headroom above a
   control that already decodes concept identity nearly as well." *(`R-112`,
   `reports/DCS_TS_PR051_POSITIONAL.md`)*

5. "I trust that positional result more than any absolute number in the phase, because its nuisance
   floor is 0.0 by construction: both arms read the same prompt, so register, length and every
   TF-IDF-recoverable confound is common to both and differences out — and that cleanest instrument
   says gist, not binding." *(`R-112`)*

6. "So CLAIM A has to be narrowed: the concept is decodable at this depth, and it is not
   meaningfully more decodable at the codeword than nine tokens later, so on this evidence the
   codeword position is not special." *(`R-112` + `R-113`)*

7. "The difference-in-means direction separates the bomb arm from the knife and gun hard negatives
   at AUROC 0.9764, CI [0.9622, 0.9906], d = 3.03, in 23 of 23 test domains — and the permutation
   null for that statistic is bimodal, with 4.5 % of arbitrary concept relabellings reaching 0.9764,
   which is why p = 0.0454 sits next to an AUROC of 0.976; the effect is huge and the evidence that
   it is specifically BOMB rather than 'one of the three' is thin." *(`R-111`,
   `reports/DCS_TS_PR053_DIFFMEANS.md`)*

8. "CLAIM B is unsupported and I would rather say so than show you the 0.976 alone. The residual
   direction was supposed to read identity and stay quiet on generic remapping; it separates
   knife/gun from the benign baseline at 0.8309 and bomb from benign at 0.8236, both above the
   surface floor — so residualising changed the mixture of remapping and identity, it did not
   decompose them. That check was preregistered as question D precisely so we could not report C
   alone." *(`R-111`, `PR-053`)*

9. "One inherited result reverses in our favour and I am flagging it as a correction rather than a
   finding: the raw `v_bomb` axis reads concept identity at 0.8856, against the ~0.574 on record,
   once the baseline term genuinely cancels — the old number was an artifact of each concept having
   its own unaligned baseline. The point estimate stands; its permutation p-value does not, because
   the relabelling null is structurally off-centre for the raw family, so I am not quoting a p there
   at all." *(`R-111`, caveat 1)*

10. "Whether any of this is causally used by the model is untested. We ran no intervention in this
    phase, so the correct statement is 'decodable, causal use untested' — not 'decodable but not
    causally used', which would be a claim we did not earn." *(mandate §32 CLAIM C; nothing in the
    log speaks to it)*

11. "Whether the demonstrations install the concept in the model, as opposed to merely writing it in
    the text, is an assumption we have not yet measured; the readout run is in flight (job 865335)
    and has no result yet. Everything above is compatible with the model encoding what the
    demonstration text says." *(no log entry claims installation)*

12. "Register is a stated scope limit of this bank family and I want to be the one who says it:
    natural bomb text hedges at 13.72 %, knife at 0.20 %, gun at 2.33 %, so register is produced by
    the manipulation rather than layered on top of it, and no re-analysis of this corpus fixes that
    — three separate instruments failed, each for that same reason." *(`R-106`, `A-043`, `C-078`,
    `C-100`, `C-101`)*

13. "The fix for register is a design fix and it costs a generation campaign: regenerate the harm
    pools under an explicit register constraint — matched hedge rate, matched threat-lexicon
    density, matched sentence structure — with per-sentence constraints and a much stricter accept
    filter. That is the decision I need from you: fund it, or accept register as a permanent stated
    limit of this bank family." *(`Q-014`)*

14. "Behaviour is a CANNOT ANSWER here, for two independent reasons rather than one: there is no
    behavioural outcome on the bank the representation measure was taken on, and the power for the
    representation-to-behaviour link is 0.2501 against a 0.50 bar even under a perfectly monotone
    truth — so the ρ = +0.60 on record is not citable in either direction." *(log §A-034.2 D)*

15. "A large part of what this phase produced is infrastructure, and I count that as a result. The
    first aligned bank I built had no manipulation at all — 1,856 of 1,856 primary-cell prompts were
    byte-identical across bomb, knife and gun, which pins any probe there to exactly 1/3 by
    arithmetic — and the pre-GPU audits caught it in about two hours of wall clock and zero GPU. If
    the mandate had not required those audits before GPU, we would have spent GPU hours measuring a
    quantity fixed by arithmetic and reported the 0.333 as a negative result about the model."
    *(`C-074`)*

16. "We found and closed one bug class eight times: every time our checker's notion of 'an
    occurrence' differed from what the string substituter actually did — plurals, case forms,
    compounds like `handgun` becoming `handbutton`, and once inside the gate itself, which retracted
    a '19/19 PASS'. Each instance was silent until something downstream refused. The rule we now
    enforce from one shared implementation is that the substring count must equal the whole-word
    count, and the rescan says the shipped banks are unaffected — 1 hit in 13,920, in an
    already-excluded domain." *(`C-075`/`C-076`/`C-079`/`C-080`/`C-087`/`C-090`/`C-095`, `R-108`)*

17. "Every threshold we publish is now read by code. We had a preregistration that declared eight
    nulls and an analyzer that implemented one, where a knife-vs-gun result of 0.60 would have
    passed the frozen success rule while sitting below a 17-feature bag of surface counts — the
    floor is now a machine-read field, and a preregistration that forgets to declare one cannot be
    analysed at all. That was fixed before any outcome existed, which is the only reason it should
    count for anything." *(`B-020`, `C-097`)*

18. "The scope of everything above, stated once: one model (Llama-3.1-8B-Instruct, one pinned
    revision), one bank family, two codewords, one layer band, 113 domains with 23 held out — and a
    test split that was read exactly once." *(`R-099`, `R-109`, `R-113`)*

---

## 3. WHAT WE MUST NOT SAY

### 3.1 Mandate §33, verbatim

Do not say:

- "The model represents button as BOMB" without scope/decodability qualification.
- "Probe accuracy proves causal use."
- "The whole-query pathway was removed" if the read site only sees the first-layer row-local mask.
- "R3 passed" — it did not under its preregistered accuracy gate.
- "The concept signal does not transfer" — ranking transfer exists.
- "KO-3 restores the literal meaning" on Llama.
- "The codeword row is unnecessary" generally.
- "K=1/2 are query rows" — they were scaffold.
- "K=7 proves bomb token is the mechanism" — old instrument named bomb.
- "Gun does not remap" — it is inconsistent across domains.
- "Club is a clean harmful hard negative" on the old pools.
- "n=6 proves thesis-scale generality."
- "The K=8 behavioural negative proves no behavioural effect."
- "The attack is ours."
- "Representation hijacking is ours."
- "We are first to intervene on demo→query attention."
- "ASR defines Bombness."
- "A significant row-level p-value establishes a domain-level claim."

### 3.2 Newly unsayable after this phase

Each of these was sayable before and is not now. The banning entry is named.

**On localisation (`R-112`)**

- ✗ "The codeword is represented as BOMB." — The control nine tokens downstream decodes at 0.9261
  against the codeword's 0.9446, and the paired difference fails Holm.
- ✗ "The concept is encoded at the codeword position." / "…localised at the codeword." / "…bound to
  the codeword." — Same reason. Any wording that puts the representation *at a position* is banned.
- ✗ "Binding, not gist." — The phase's cleanest instrument, with a nuisance floor of 0.0 by
  construction, returned **gist**.
- ✗ Quoting the uncorrected +0.0185 / p = 0.0157 as the result. Both branches are reported; the
  Holm-corrected branch is the verdict. Reporting only the uncorrected one is promotion.
- ✗ "The signal localises entirely to the demonstration block." — Explicitly retracted by `C-081`:
  it was inferred from an `n_examples=0` null that is pinned to 1/3 by arithmetic and cannot fail.

**On separability (`R-111`)**

- ✗ "Remapping and concept identity are separable axes." / "We isolated a concept-identity axis."
  — Question D failed: 0.8309 and 0.8236, both above the surface floor.
- ✗ "A concept-identity axis exists, AUROC 0.976, 23/23 domains." — This is the exact sentence
  `PR-053` was written to prevent; it is false as a claim about identity specifically.
- ✗ Quoting the 0.9764 without the bimodal-null sentence (4.5 % of arbitrary relabellings reach it).
- ✗ Any use of the **A or B permutation p-values** from the raw `v_bomb` family — they are **not
  calibrated** (null means 0.8794 and 0.2230). The point estimates may be quoted; the p-values may
  not, in either direction.

**On p-values at their floors (`R-113`, `C-069`)**

- ✗ "p = 2.4e-07" or "p < 1e-04" quoted as a measurement of effect strength for `PR-048`. Both are
  **at their floors** (k = 23/23 exhausts the sign test; 0/10,000 exhausts the permutation) and are
  statements about design resolution. Any p in this phase must be printed beside its floor.
- ✗ Likewise for `R-111`'s sign-test p = 2.384e-07, which is its own floor. (`R-111`'s primary
  permutation p = 0.0454 and `R-112`'s p = 0.0157 are **not** at their floors and may be quoted.)

**On the margin over the surface floor (`R-113`)**

- ✗ "The probe far exceeds the surface baseline." / "…beats bag-of-words comfortably." — The margin
  is **0.0182**, and 0.9217 is a point estimate with no interval.
- ✗ Comparing the probe to **chance** as the headline. The preregistered comparator is the measured
  nuisance floor.
- ✗ Reading anything into test (0.9399) exceeding validation (0.9130). It is flagged and carries no
  weight; it is not evidence that the effect is stronger than estimated.

**On causality and installation**

- ✗ "The concept direction is causally used." — **UNTESTED**; no intervention was run.
- ✗ "Decodable but not causally used under this intervention." — Also banned here. That sentence is
  the mandate's correct wording *for a negative causal result*, and we do not have one; there was no
  intervention.
- ✗ "The demonstrations install the concept in the model." — Never measured; job 865335 is in flight
  with no result. Say "the demonstrations define the concept in the prompt" and mark installation as
  an assumption.
- ✗ Any causal verb applied to the probe result: "drives", "causes", "makes the model treat",
  "is used by the model to".

**On register and controls**

- ✗ "Register was controlled." / "…matched." / "…ruled out." — **CANNOT ANSWER** on this corpus
  (`A-043`, `C-100`, `C-101`). Register is *produced by* the manipulation (hedge 13.72 / 0.20 /
  2.33 %).
- ✗ "The surface-matched analysis shows the effect survives." — `PR-050` is **WITHDRAWN** on a false
  premise: a partition cannot change pooled accuracy.
- ✗ "Knife-vs-gun is our register-clean confirmatory contrast." — `PR-049` is **EXPLORATORY** by its
  own demotion rule; power 0.793 is below the 0.80 at its own Holm α (`C-101`), and surface still
  reaches 0.7065 there. Citing `R-106`'s CO-PRIMARY verdict is citing a withdrawn verdict.
- ✗ Quoting anything from `PR-052` as confirmatory. It is declared EXPLORATORY **before** running,
  with `success` and `negative` both NOT AVAILABLE.
- ✗ "`PR-047` shows the effect is localised." — **`PR-047` never existed** (`C-098`), and no data was
  captured at any control position that could have supported it. Any inherited document citing it
  is citing nothing.
- ✗ "Length was controlled." — The length remedy **did not work**: macro AUROC went from 0.5750 to
  **0.5793** (`R-102`), and by a pre-declared rule there is no third round. Length is a permanent
  stated nuisance.
- ✗ "Cross-split leakage was reduced." — It went from 3/2,760 to **15/2,760** (`C-083`).

**On the banks and the population**

- ✗ Citing `R-098` or any `ts116` result as a concept contrast. The bank is **VOID** for that
  purpose: the primary cell is 1,856/1,856 identical and any probe there is pinned to 1/3 by
  arithmetic (`C-074`). It remains a valid instrument only for the narrower lexical-separability
  question, whose answer is "no, by construction".
- ✗ "19/19 gates passed on `ts116n`." — **Retracted** (`C-080`); the gate was blind, and the
  corrected gate returns 18/19. The passing family is `ts116m`.
- ✗ "116 domains." — The analysed population is **113** after three preregistered whole-population
  exclusions; the split is **67 / 23 / 23**, not the 70/23/23 originally frozen in the roster.
- ✗ "`restaurant_kitchen` was excluded because the domain is unusable." — `C-082`: the two
  regeneration seeds shared 13 of 14 OpenAI seeds, so the second failure says little about the
  domain; the exclusion is **conservative rather than necessary** and is kept only because reversing
  a preregistered exclusion is worse.
- ✗ Joining across codeword banks on `prompt_id`. The two banks share all 22,272 ids, so this
  silently pairs the wrong rows (`R-099`); the compound key is required.

**On what this phase is**

- ✗ Presenting `R-111`/`R-112`/`R-113` as three converging confirmations. `R-112` **narrows**
  `R-113`, and `R-111` reports a **negative** on its own CLAIM-B question. Two of the three
  headline results are constraints on the third.
- ✗ Any sentence of the form "we showed the mechanism". This phase measured **decodability from the
  prompt**, under a stated register limit, on one model, with no intervention.

---

### A note on the boundary between sections 2 and 3

Where a sentence sat between "defensible" and "not", it was put in section 3. Specifically:
the uncorrected `PR-051` difference, the raw-axis A/B p-values, the `PR-049` knife-vs-gun contrast,
and every causal or installation verb were all available in a weakened form and were **not** written
into section 2.
