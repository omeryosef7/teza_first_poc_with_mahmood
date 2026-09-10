# DCS continuation — REVIEW-1 (5-part adversarial) and adjudication
2026-09-10 · covers `CONT-ENTRY 000`–`009` and commits since `7c5153a4`

Five independent adversarial reviewers (CODE / DATA / OUTPUT / STATISTICAL / SCIENTIFIC), each
instructed that "a review that finds nothing is a failed review", followed by an adjudicator who
re-verified every BLOCKER and IMPORTANT finding with its own command output rather than accepting
the reviewers' evidence. 6 agents, 0 errors, 370 tool calls, ~80 min.

Full agent transcripts: workflow `wf_953ebb40-026`.

---

## TIER 0 — landed in commit alongside this report. All CONFIRMED by the adjudicator.

### T0-1 · The family-wise permutation null was not a null · `dcs_cont_layerpos_map.py:288`
Found independently by **three** reviewers (CODE-01, S1, SCI-2).

The direction was fitted on permuted `y` and then correlated against the **observed** `y`. The
statistic is *"fit to labels L, score against L"*, so a null draw must recompute **both halves**
under the same permutation.

Adjudicator's verification (not the reviewers'):

```
single cell, 300 pure-noise datasets, permutation p-value uniformity
  CORRECT  (vs permuted y)   P(p<=0.05)=0.063   P(p<=0.10)=0.130   P(p<=0.50)=0.497
  ANALYZER (vs true y)       P(p<=0.05)=0.193   P(p<=0.10)=0.263   P(p<=0.50)=0.653

map level, 150 pure-noise datasets, 24 cells, n=67, 200 perms
  family-wise false-positive rate, ANALYZER  : 71/150 = 0.473
  family-wise false-positive rate, CORRECTED : 11/150 = 0.073   (nominal 0.05)
```

And on **real** inherited states the broken threshold tracks the effect it is supposed to be blind
to — `cw_query|L12`, `C_minus_B`: analyzer p95 **0.628** vs correct p95 **0.324**. It is neither
conservative nor anti-conservative; **it is a function of the observed effect**, which is why no
amount of `--n-perm` could have fixed it.

My own reproduction before fixing: broken flagged **3/8** pure-noise datasets, corrected **1/8**.

> ⛔ The analyzer written specifically to prevent a manufactured discovery manufactured one about
> 40 % of the time.

### T0-2 · `interaction` was the token MAIN effect · `dcs_cont_layerpos_map.py:228`
Found by **one** reviewer (SCI-1).

Verified symbolically:

```
true interaction   (C-A)-(B-E) = -A - B + C + E
CONT-ENTRY 003     (C-B)-(A-E) = -A - B + C + E   ✅ the log's prose was right
CODE               (C-B)-(E-A) =  A - B + C - E   ❌
                               = (C+A)-(B+E)      = 2x the SURFACE MAIN EFFECT
```

`C = (harm, ' button')` and `B = (harm, ' bomb')`, so `C−B` is a **button↔bomb token swap**;
`E−A` is the same swap in the **opposite polarity**. Measured `cos(mean C−B, mean E−A) = −0.87`.
Hence `cb + ea` cancels the lexical part and is the interaction; `cb − ea` doubles it.

The log's prose and the frozen convention in `dcs_succ_bombness_candidates.py:449` were both
correct. **Only the code disagreed.**

### T0-3 · The two blockers COMPOSE — no reviewer said this
Fixing T0-1 alone makes the phase **worse**. Corrected family-wise p95 at `cw_query` ≈ **0.33**,
while the real `C_minus_B` cell reads **0.71–0.76**. So the corrected pipeline does not report
nothing — **it fires hard, on a whole-prompt lexical swap**, and would have stamped FWER-95
significance on a cell labelled `interaction` that is really 2× the main lexical effect.

⇒ Both landed in one change, and the main effect is now **reported under its own name**
(`token_main_effect_LEXICAL`) rather than deleted, because it is the confound this map most needs
to print. The two register-matched contrasts are renamed `C_minus_B_LEXICAL` / `E_minus_A_LEXICAL`
for the same reason: **being register-matched does not make a contrast concept-informative.**

### T0-4 · The declared join key was not constructible
The log declared `(bank_file_sha16, domain, family_slot)`. Readout **rows carry no
`bank_file_sha16`**, so nothing was checking the bank. A `basket_*` readout joins **all 670 TRAIN
keys** of a `button` corpus silently — the only structurally differing keys live in
`school_campus`, a domain the analyzer drops *before* it would notice — swapping the target mean
from **0.678 → 0.045** and violating never-pool-button-and-basket.

Worse and **live**: two sibling corpora now exist one word apart in the directory name, identical
in rows/cells/domains/sites/layers. Passing `cont1_semantic_one_word_*` as the predictor would
reinstate exactly the output-adjacency circularity `CONT-ENTRY 002` exists to forbid, invisibly.

Fixed and verified to fire, **fast**:

```
REFUSING: the predictor corpus must be the BEHAVIOURAL population; ... carries
  query_kind ['semantic_one_word']. The semantic prompt's next token IS the target ...
REFUSING: BANK MISMATCH: corpus bank_file_sha16=dcd92d723f3e6d00 but readout
  bank=79511d9e254571e6 (from metadata.json:bank_file_sha16) ...
```

Every cheap refusal now runs **before** the 12 GB `torch.load`; rejecting a one-word mistake used
to cost 30 minutes of NFS I/O.

### Also landed · S7 — the confounded family no longer taxes the threshold
`C_minus_A_CONFOUNDED`'s 380 cells were entering the global maximum that gates every reportable
family, despite being a quantity that "must never be quoted as a result".

---

## TIER 1 — before any candidate is promoted

| # | finding | status |
|---|---|---|
| **T1-1** | `N_neighbour` was declared in **semantic** coordinates (`−9 ' actually'`, `−11 ' word'`) while the predictor is the **behavioural** prompt, where `rel_end −11` **is the codeword**. The mandated neutral control *was the predictor site* and could not fail. | ✅ **FIXED** in the registry, per template, with the note that the two templates are *not* equivalent controls (semantic +1 is a content word, behavioural +1 is punctuation) |
| **T1-2** | ⛔ **`N_surface = 0.526` is backed by no artifact.** No script and no output exist; the only surface-floor artifact (`b1_surface_floor_button.json`) has LOO CV R² of **−0.48 / −0.35 / −0.42** and targets `B1`, not `y_install`. The value may be a transcription of `q2_concept_present.json:/rows/train/asr_and_concept_present/rho = 0.5260319859594348`. | ⛔ **OPEN — the log calls it "a measured floor"; it is not reproducible.** Corrected in `CONT-ENTRY 010` |
| **T1-3** | `dcs_ts_make_exclusions.py` default `--split ""` is still unguarded: executed with no `--split` → `rc=0`, `domains_remain=113`, i.e. all 23 test domains retained. Only `== "test"` is guarded. | ⛔ **OPEN — "the three gaps are closed" is half true for gap 1** |
| **T1-4** | `pr057 --plan` reaches `split_bind` at `:1466` before `run_stage`'s guard at `:1756`; `--split` defaults to `test`. `CONT-ENTRY 004` recorded that closure as "verified present in `--help`", which exercises no behaviour. | ⛔ **OPEN** |
| **T1-5** | `--split validation` has no confirm gate — typing the word is the gate, on the population reserved for selection. | ⛔ **OPEN** |

---

## TIER 2 — the log says something the artifacts do not. No number moves.

* **OUT-01.** `CONT-ENTRY 004` justified role-relative capture with *"A and C are token-identical for
  ≥28 trailing tokens in 930/930 pairs"*. Re-tokenized with the pinned `0e9e39f2`:

  | population | trailing-identical | ≥28 |
  |---|---|---|
  | `semantic_one_word` | min 28, median 29, max 32 | **930/930** |
  | **`behavioral`** | **min 24, median 25, max 28** | **1/930** |

  It is a **semantic-template number stated about the behavioural population the phase extracts**.
  The design conclusion is unaffected and the capture is safe — the grid stops at `rel_end −16`,
  leaving **8 tokens of headroom** — but it becomes a live trap past `−24`. Same error class as the
  near-miss `CONT-ENTRY 005` congratulates itself for catching, one entry earlier.
* **S2.** Measured single-cell null sd is **0.171–0.174** (se ≈ 0.007) against the log's quoted
  **0.160** — ~1.5 se on a 200-draw estimate, i.e. sampling noise quoted to three digits. The
  dependent "max of 1520 ≈ 0.64" becomes ≈ 0.61 under independence and lower under correlation. The
  qualitative point survives; the arithmetic chain does not.
* **S4.** Validation, n = 23, Fisher-z: **MDE at 80 % power = ρ 0.556**; power at the train effect
  (0.4836) = **0.655**; observed ρ = 0.1435, 95 % CI **[−0.286, 0.525]** — which contains 0 **and**
  0.4836 **and** 0.3961. ⇒ **"not split-replicated" is supported; "failed to replicate" is not.**

---

## TIER 3 — latent, verified, not firing

* `load_installation` lacked the duplicate-key refusal `load_corpus` has (**fixed**). The
  adjudicator downgraded severity: the 232 last-wins keys are all dose-0, which the analyzer never
  looks up, so the dose field was a second line of defence.
* `cache[pid] = vec.half()` precedes the `too_few_codeword_occurrences` `continue`, so a skipped row
  would land in the frozen primary payload but not in `results.jsonl`. Both launched runs show
  `skip_reasons {}`, so it has not fired — but it breaks the "additive, byte-identical" guarantee
  the moment it does.
* Layer 0 is in the grid and Llama-3 has no additive positional embedding, so the layer-0 codeword
  contrast carries no between-domain information. Wants a degenerate-cell refusal.

---

## REFUTED, and one that matters

* **"`rho_loo` is satisfiable by contrast magnitude alone" — REFUTED on this data.** Despite
  concentration 0.96, the **norm-only** baseline runs −0.25…+0.29 while `rho_loo` is 0.42–0.76. The
  predictive signal lives in the y-weighted residual direction, not the magnitude.
* **The capture geometry is sound.** The adjudicator suspected `rel_end` misalignment wherever
  `seq_len(C) ≠ seq_len(B)` and **self-refuted**: the last-16 window differs *exactly* at `rel-11`
  (the codeword) in **670/670** pairs for both `C−B` and `E−A`. Two prompts do differ in length,
  caused by an uppercase demonstration token (`"BUTTON"` is 1 token, `"BOMB"` is 2), but because the
  sites are end-relative the captured window is untouched.

> ⇒ **Every confirmed defect in this phase lives in the analysis layer, not the data layer.
> Nothing needs re-extracting.**

---

## What five reviewers collectively missed

1. **Nobody ran the pipeline on real data to see what it would report.** All five reasoned about the
   null abstractly or on synthetic noise. On real states the corrected p95 ≈ 0.33 and `C_minus_B`
   reads 0.71–0.76. `CONT-ENTRY 007`'s controlling expectation — *"the best cell in the map is
   noise"* — is **empirically false on this corpus**, in the direction nobody checked.
2. **Nobody noticed the two blockers compose** (T0-3).
3. **Nobody checked the clock.** The extraction had already finished and the analyzer was mid-run
   writing the artifact the §44 gate consumes.
