# Continuation Sprint — Progress Log

Tracking execution of `reports/CAUSAL_CONTINUATION_MASTER_PLAN.md`.
Branch: `behavioral-causality-sprint`. Model: Llama-3.1-8B-Instruct bf16.
Loop: every 30 min (cron `86decf2e`, session-only, expires after 7 days).

**Legend:** ☐ not started · ◐ in progress · ☑ done · ⚠ blocked/needs-decision · ✗ null/negative result

---

## Environment facts (established tick 1, reuse these)

- Login node has **no torch/numpy/scipy** on system `python3`.
  Use `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`
  (numpy 2.4.6, scipy 1.17.1, torch 2.7.1+cu126) for all CPU analysis.
- 26 `scripts/phase*.py` harnesses exist (the plan's "21" was an undercount).
- `ds_common.env_metadata()` exists at ds_common.py:82 and imports torch → must not be a hard
  dependency of any CPU-only provenance path.
- SLURM rules unchanged: no dependencies, ≤6 parallel, L40S only, comma-lists in wrapper defaults
  (never in `--export`).

---

## Phase status

| Phase | Status | Note |
|---|---|---|
| P0 — trust the repo | ◐ | tick 1 in progress |
| P8.0 — interaction from existing data (free) | ◐ | tick 1 in progress |
| P10.0 — graded re-analysis of the nulls (free) | ◐ | tick 1 in progress |
| P1b — ClearHarm v3 | ☐ | after P0 |
| P1 — corrected baseline + drift envelope | ☐ | needs GPU |
| P10 — decode-safe re-test | ☐ | needs new primitive + GPU |
| P8 — combined causal ASR factorial | ☐ | needs P1b + P8.1 α calibration |
| P9 — GCG/MAC Gate 7 | ☐ | needs P9.0 optimizer bug fixes |
| P2 — all codeword occurrences | ☐ | one free cell already implemented, never launched |
| P3/P4/P5 — attention, induction heads, path matrix | ☐ | |
| P6 — Jacobian readout | ☐ | |
| P7 — concept ⊥ refusal + re-validate 32 refusal dirs | ☐ | blocks per-layer refusal claims |
| P11 — framework robustness | ☐ | appendix |
| P12 — quantized | ☐ | appendix |
| P13 — cross-model | ☐ | last |
| P14 — paper assembly + claim audit | ☐ | last |

---

## Results so far

### ⭐ P8.0 — the Doublespeak × refusal-down interaction is significantly SUB-ADDITIVE
**Independently verified** (recomputed from scratch by the main agent; matches the analysis script to 4 dp).
`reports/PHASE8_0_PILOT_INTERACTION.md` · `scripts/analyze_interaction_2x2.py` · `outputs/interaction_2x2.json`

clearharm pooled, n=86, within-item `D_i = Y(1,1) − Y(1,0) − Y(0,1) + Y(0,0)`:

| outcome | Î | 95% CI | perm p |
|---|---|---|---|
| binary ASR | **−0.1860** | [−0.349, −0.023] | **0.0451** |
| graded score | **−0.1904** | [−0.340, −0.041] | **0.0162** |
| compliance | −0.1977 | [−0.337, −0.058] | 0.0115 |

Cell ASRs (pooled): Y(0,0) 0.105 · Y(1,0) 0.372 · Y(0,1) 0.558 · Y(1,1) 0.640.
curated pooled n=51: Î = **−0.3922** [−0.588, −0.196], **p = 0.0004** (same direction, stronger).

**The robust item-level fact:** `D_i = +2` occurs **0 times in 137 items** across both cohorts and all
splits, while `D_i = −2` occurs 5 times. This is immune to the averaging/ceiling confound below.

⚠ **Honest caveats (all in the report):** at α = 1.0 the design is saturated — `I_max` = +0.174 (clearharm)
and 62.8% of items are already jailbroken by one factor alone, so they can only contribute `D_i ≤ 0`; a
negative Î is therefore *partly arithmetically forced*. clearharm-test binary p = 0.0498 is knife-edge and
pooled significance depends on pooling train+test (defensible — no model selection on either — but must be
stated). **P8.1's α calibration is a genuine blocking prerequisite** before the magnitude of Î means anything.

**Reading:** Doublespeak and refusal-ablation are sub-additive, consistent with them acting on a *shared
refusal bottleneck* rather than independent channels. Plan §0.6's prediction is confirmed, not refuted.

### 🐛 Judge divergence — a real bug in the script that produced the Phase 2.1 baseline
`scripts/behav_judge.py` now holds the single judge contract, differential-tested against all 6 copies
(35 kw_refusal + 175 classify + 140 extended + 175 end-to-end cases per file). 4 of 6 agree exactly.

- **FINDING 1 (paper-relevant).** `14_behavioral_eval.py` has **no EMPTY label**. The four `phase_behav_*`
  harnesses short-circuit `if not completion.strip(): return None, "EMPTY"`; `14_behavioral_eval.py:88-101`
  does not, so a blank generation is sent to the judge and folded into BENIGN (or MALICIOUS), and its
  summary has **no `empty_rate` guard at all**. On a synthetic 5-row cohort this moves ASR by −0.40 and
  refusal_rate by +0.40. **`14_behavioral_eval.py` is what produced the Phase 2.1 baseline
  (clearharm DS 0.349 / direct 0.116).** Those numbers need an empty-generation audit — logged as an
  action item for P1.
- **FINDING 2 (low exposure).** `+inf` score handling drifts: `14` labels it MALICIOUS, the `phase_*` copies
  label it BENIGN/REJECTED. Only reachable if the StrongREJECT rubric returns a non-finite score.

### ⚠️ P10.0 — the graded re-analysis does NOT rescue the concept circuit (corrects plan §0.5)
`reports/P10_0_GRADED_REANALYSIS.md` · `scripts/analyze_graded_reanalysis.py`

Plan §0.5 claimed the graded score "already flips the carry-head verdict to p=0.033". **The point estimate
reproduces exactly, but the claim does not survive its own specificity control.**

| quantity | value |
|---|---|
| CARRY/clearharm pooled (n=86), graded | d = **+0.0741** [+0.009, +0.142], Wilcoxon p 0.0343, perm p 0.0337 |
| **random-head control, same cell** | d = **+0.0392** [−0.039, +0.119], perm p 0.359 |
| **specificity contrast (rand − carry)** | **+0.0349 [−0.039, +0.110], perm p 0.382** ← not significant |

**The targeted ablation is not demonstrably better than a size-matched random one.** The control's point
estimate is **53% of** the carry effect. The result is equally consistent with "ablating ~9 attention heads
slightly degrades completions". **Do not write 'the carry heads are behaviorally necessary' from this.**

Further: only 22 of 86 items are non-tied; leave-one-out permutation p reaches **0.0624** (dropping *one*
item crosses 0.05); dropping the 5 largest positive differences kills it (p = 0.466). **curated does not
replicate** (pooled d = −0.017, p = 0.794). **BEHAV-WRITE is null on the graded endpoint too**
(clearharm −0.004, p = 0.941). Exactly **1 of 24** graded tests has p < 0.05, and it is the pooled cell —
neither split is significant alone (0.114 / 0.208).

**Power confirmed** (p₀ = 0.0894 estimated from all random-control arms, b=25/c=24/n=274): carry
clearharm train power **0.135**, test **0.086**. n at 80% power for Δ = 0.09 → **n ≈ 275**.

⇒ **Net effect on the paper: the "behaviorally inert" conclusion stands, but for a better reason than
before** — not "we found nothing" but "what we find is not distinguishable from a random ablation of the
same size, and we now know the design needed n ≈ 275 to say otherwise." P10's decode-safe re-run on v3
remains necessary; §0.5 of the plan should be read with this correction.

### 📋 Artifact audit — tick-1 baseline (`scripts/audit_artifacts.py`, 0.5 s, exit 1)
367 run dirs · summary.json in 91 · **RUNMETA.json in 0 · DONE.json in 0** · 20 empty dirs ·
1 raw-without-summary (the job-708038 aborted twin) · 62 fixed-name (clobber-on-rerun) dirs ·
20 job ids shared by 69 dirs · 350 unregistered runs · outputs 8.9 GiB · disk 98% used.
**Manifest drift is 3, not the 1 the recon reported** — two `subsample.npz` files drift at *identical size*,
so the cheap size-only check misses them; only `--verify-hashes` catches it.

---

### ✅ Data integrity — every behavioral summary number recomputes from raw
`scripts/validate_all_outputs.py` + extended `scripts/validate_experiment_coverage.py`.
**4,909 summary values recomputed from raw across 29 run dirs → 0 mismatches.** Every ASR, refusal_rate,
empty_rate, ΔASR, flip count and exact McNemar p in every behavioral `summary.json` reproduces exactly.
Coverage: 24 behavioral dirs = 20 ok / 4 WARN / 0 FAIL; phase5/6 paths byte-identical to before.
6/6 negative controls fired (a validator that cannot fail is worthless).

Three findings:
- **1 hard FAIL:** `behav_refusal_clearharm_a1.0_20260804_125311_708038` has no summary.json and only 36
  test rows (vs 42 in the authoritative twin) — the §2.3 job-708038 collision, now caught automatically.
- **§1.5 violation:** `phase6_mlpKO_curated_layer_20260803_092718_703457` reports **pooled** dev+heldout
  (n=51 = 30+21, no `by_split` block). Any number cited from that dir is a pooled number.
- **4 smoke runs** (n=2–3) sit in the normal namespace with no `_smoke_` marker, contra §1.3.

### 🐛 Two primitive defects found by the new tests — both FIXED
Test suite: **113 → 191 passing** (78 new tests, 0 failures, 0 xfail).
- `pair_common.ComponentCapture._grab`: `torch.tensor([])` with no dtype → float32 → `index_select` raises
  for an empty position list. **Fixed** (`dtype=torch.long`).
- `ds_common.find_word_occurrences_in_text`: a stray trailing `ids = enc["input_ids"]` raised
  `UnboundLocalError` on the slow-tokenizer path — and, when `enc` *was* bound but failed the sanity check,
  silently mis-sliced `subtoken_ids` from a different-length id list. **Fixed** (line deleted). The second
  failure mode is worse than the crash the test was written for and was found during review.
Both tests kept as regression guards with the defect documented inline.

### 🗃 Provenance applied
`ds_common.write_runmeta/write_done` (torch-optional, never raises), `backfill_runmeta.py`,
`update_registry.py`. **734 RUNMETA.json/DONE.json written across all 367 run dirs** (idempotent: second
apply wrote 0). 181 dirs recovered a real git commit from `logs/*.out`; 195 recovered their script from the
sbatch wrapper. Every reconstructed field carries `{"source": "reconstructed", "evidence": ...}` and
unsourceable fields go to `unknown_fields` with a reason — nothing fabricated.
`EXPERIMENT_REGISTRY.csv`: **45 → 395 rows** (backup at `.bak`), original rows preserved.

---

### 🔴 P8.0 CORRECTED after adversarial review — the headline is weaker than first written
The review attacked the P8.0 result and found three things. All are now in the report; **the direction of
the finding survives, the strength does not.**

1. **Measurement instability (the biggest threat).** A technical replicate of the *same* condition exists
   (the preempted twin of job 708038, 80 overlapping items). Label flips between the two runs:
   `direct_randabl` **0/80**, `direct_base` 2/80, `ds_base` 2/80, **`direct_refabl` 6/80 (7.5%)**,
   **`ds_refabl` 6/80 (7.5%)**. On those same 80 items Î is **−0.150 (p=0.111)** in one run and
   **−0.100 (p=0.277)** in the other — a **swing of 0.050**, ~¼ of the headline and *larger than the gap
   from the published CI upper bound (−0.023) to zero*. The control arm being perfectly stable proves this
   is **StrongREJECT judge variance on borderline completions**, not hook nondeterminism, concentrated in
   exactly the arms that carry the signal. ⇒ **p = 0.045 is fragile.** (Verified independently by me.)
2. **The three outcomes are ONE measurement, not three.** The binary MALICIOUS label is a deterministic
   threshold of the graded score — 0 violations of `label ⟺ score ≥ 0.25` across all 5 arms × 137 rows.
   The earlier "six pooled estimates, all six p < 0.05" framing inflated the evidence and is withdrawn.
3. **The curated compliance cell is algebraically degenerate.** Compliance = 1.000 in both DS arms, so
   `D_i` collapses to `Y(0,0) − Y(0,1)` — that "interaction" is the main effect of refusal ablation, not an
   interaction. Removed from the supporting evidence.
Also: the sign-flip null assumes symmetry of `D_i`, which the ceiling structurally violates — p-values are
approximate.

**What still stands:** the direction (negative in all 12 split-level estimates, both replicates) and the
confound-immune item-level fact that **`D_i = +2` never occurs in 137 items**.

### ✅ P2 all-occurrence patching — launched (plan §5 P2, the free cell)
`--positions all` existed in `phase6_mlp_causal.py` and had **never been run**. Smoke (714854/714855) passed
the gate: `nec_selfswap_max_dev = 0.0`, `suf_selfswap_max_dev = 0.0`, 0 skips, 1024 rows, effects
non-degenerate. Full runs launched on all three benches: **714997** (clearharm v2, 116 ex), **714998**
(clearharm v1), **714999** (curated). Zero new code.

### ✅ P9.0 — the GCG selection bug is FIXED (unblocks Gate 7)
`_evaluate_candidates` now runs the candidate batch with `output_hidden_states=True`, slices the configured
layers/positions in sub-batches, and passes them to `composite_loss` — so the representation/refusal
objective finally enters **candidate selection**, not just the gradient. Opt-in
(`objective.repr_in_selection`, auto-ON only when a repr objective is configured) so **task-only arms stay
byte-identical and equally fast**. Provenance fixed too: `repr_layers`, `reference_cache_id`,
`objective_name` now reach `CONFIG.json` **and** `config_hash()`, so arms can no longer silently cross-resume
each other's checkpoints. `llama` model family added (3 files). Verified GPU-free with a synthetic test.
⇒ **Every prior "mechanism-derived GCG fails" statement was made with the objective disabled in selection.**

### 📈 P1b — dataset recovery is bigger than the plan estimated, with a caveat
Replaying the extractor from cache reproduces the v1 decomposition exactly (86 kept / 62 LLM-None /
31 multi-token / 0 not-verbatim). Lexicon fallback recovers **44/62 + 8/31 = 52 rows → 138 examples /
45 concepts** (+60.5%, vs the plan's estimated +33). A 50/25/25 concept-level bin-pack gives
**69/35/34, zero straddling concepts**, and survives singular/plural lemma collapse.
⚠ **Caveat that must reach the paper:** only **2 of the 45 concepts are new** (chlorine, mortar) — the other
50 recovered rows densify concepts v1 already had. **Concept-level effective N goes 43 → 45, essentially
unchanged.** The +60% may be used for item-level claims (per-item AUC, item-level rep→behavior) but **must
not** be reported as strengthening LOGO or cross-concept generalization. Recovery is also category-biased.

### ⭐ P2 NEW RESULT — patching ALL codeword occurrences roughly DOUBLES the L9 write necessity
`reports/PHASE2_ALL_OCCURRENCES.md`. Zero new code — `--positions all` existed and had never been run.

| cohort · split | n | demo-only L9 | **all-occurrence L9** | ratio |
|---|---|---|---|---|
| clearharm dev | 44 | +0.0625 [0.023, 0.113] | **+0.0889 [0.037, 0.153]** | 1.42× |
| clearharm heldout | 41 | +0.0153 [0.006, 0.029] | **+0.0348 [0.011, 0.069]** | 2.27× |
| curated dev | 30 | +0.0493 [0.021, 0.081] | **+0.1003 [0.033, 0.183]** | 2.03× |
| curated heldout | 21 | +0.0970 [0.038, 0.162] | **+0.1797 [0.092, 0.277]** | 1.85× |

L9 is Holm-significant and the argmax in **all four cells** under both modes; larger under `all` in all four.
**Not an artifact of patching more positions** — the reported effect is `random_control − C3` where the
random control is **count-matched** (`rlen = min(m, …)`, phase6_mlp_causal.py:198), so the control grows
with the intervention. Self-swap exactly 0.0; sufficiency still ≈ 0 (necessary, not sufficient).

⇒ **The concept write is not confined to the demonstration block.** The query-codeword occurrence carries an
independent share of the same L9 write and the two contributions add. This explains the previous sprint's
loose end (its audit found the query MLP "3–4× weaker but not absent", contradicting the report prose):
**the demo-only measurement was understating the write by ~2×.** The circuit description should say the
L8–L11/L9 write operates over *every codeword occurrence in context*.
⚠ The 1.4–2.3× ratios are comparisons of two independently-estimated effects, **not** a paired test of the
increment — a within-item paired contrast is needed before this goes in the paper. v2 (116-ex) replication
still running (714997). Per-occurrence resolution (each demo individually) not yet done.

### 🔧 Review defects fixed — all with reproduce-then-prove negative controls
- **Validator false positives GONE.** `validate_all_outputs` hardcoded the necessity cell name `C3`, so the
  whole phase3_demoKO family recomputed from an empty map: **462 false mismatches across 12 dirs → 0.**
  Now schema-driven (`C3` / `C3_mlpout` / `C3_demoKV` / any `C3_*`). Re-verified by me:
  **13,201 values recomputed across 63 recognized dirs, 0 mismatched.**
- **Tolerance hole closed.** `close()`'s decimal-adaptive fallback silently accepted ±0.05 on a 1-decimal
  stored value. Now a bounded half-ulp allowance (cap 5e-3). Proven with a corrupted fixture: a 0.0415
  perturbation passed before, FAILs now.
- **Deleted keys now caught.** A missing leaf or a whole missing split node exited 0 before; both FAIL now,
  with 0 new false positives corpus-wide.
- **Dead ratchets revived.** `empty_dirs` was pinned at 0 forever because the backfill wrote RUNMETA/DONE
  into every dir; EMPTY is now "no *payload* file" and correctly reports **20** again. `--baseline` mode no
  longer ignores FAILs that no counter measures (capacity, missing registry).
- **34 fabricated SLURM job ids removed.** `RE_JOBID` matched the timestamp's HHMMSS field; 25 of the 34
  contradicted the very log they cited. All reconstructed records deleted and re-written from scratch under
  a distinct schema tag (`RUNMETA/1-reconstructed`) so they can never be confused with live records.
  Verified by me: **0 of 369 RUNMETA now carry a job id equal to the dir's HHMMSS.** 9 dirs also had
  consumer-log mis-attribution corrected (a dataset *input* dir had been given a GPU and a model id).
- **Judge gate works.** The differential test exited 0 even with 13 disagreements; it now allowlists the 3
  documented `14_behavioral_eval` divergences and fails on any NEW one (`--strict` fails on all).
  Verified: default exit 0, `--strict` exit 1. `classify` renamed to remove a silent adoption hazard.
- **12 of 16 printed ">4000" power values were false** (doubling ladder skipped 2049–4000). Fixed and
  Table 5 regenerated; an automated re-parse checks all 240 table values against the JSON → 0 mismatches.

**Validator scope, honestly:** of 397 output dirs only 96 have `raw.jsonl`; 63 of those have a schema the
validator understands (all clean), 32 do not yet (phase4*/phase5b/phase7*/phase9*), and 1 is the known
job-708038 aborted twin. Teaching it the remaining 4 families is follow-up work, not a blocker.

---

### ✅ P10 blocker cleared — `pc.AllPositionMLPAblate` (decode-safe MLP ablation)
`pair_common.py:742-821` (pure addition), 14 new CPU-only tests. Suite **191 → 205 passed**, 13 skipped.
Hooks `layer.mlp` and rewrites the whole output on **every** forward, so the edit survives KV-cached decode
steps. Modes zero / scale / project_out are decode-safe; `mean` is explicitly marked PREFILL-ONLY and locked
in by a test (a seq-axis mean is an identity no-op at `seq==1`). Verified both primitives hook the
**identical module**, so the P10 re-run will be apples-to-apples with the old BEHAV-WRITE measurement,
differing only in position/timestep coverage. Also batch-safe (the old primitive was `batch_index=0` only).

**🔎 A second failure mode of the old guard — checked, and BEHAV-WRITE is NOT affected.**
The agent found that `ComponentOutSwap` is not always a clean no-op at `seq==1`: if position **0** is among
the targets it is the one index still "in range", so it writes the row captured for *prompt position 0* onto
**every generated token** — a misaligned ablation, not an absent one. I checked whether BEHAV-WRITE was hit:
under the Llama chat template token 0 is always `<|begin_of_text|>` (verified: id 128000 == `bos_token_id`),
so a codeword's `last_idx` can never be 0 and `cw_pos` never contained it. **⇒ the BEHAV-WRITE decode phase
was a clean no-op. The null is UNTESTED for generation, not CORRUPTED** — P10 is a genuine extension, not a
retraction. (Any *future* harness whose position set can include 0 must use the new primitive.)

### ✅ P1b — ClearHarm v3 split built, and the v1 leakage is worse than the plan said
`data/splits/clearharm_doublespeak_v3.json` · `scripts/build_split_v3.py` · `reports/P1B_V3_SPLIT.md`
**138 examples / 45 single-token concepts / 40 concept-level clusters · train 69 / dev 35 / test 34 ·
828 prompt rows (6 conditions) · zero OpenAI calls.** `validate_data_integrity.py`: 10 ok / 0 warn / 0 FATAL.

| | v1 | **v3** |
|---|---|---|
| concepts straddling train/test | 14 / 43 | **0 / 45** |
| codewords straddling | 17 / 21 | **0 / 45** |
| rows with a straddling concept | 55 / 86 | **0 / 138** |
| rows with a straddling codeword | **77 / 86 (90%)** | **0 / 138** |

Independently re-verified by me: concept overlap is 0 across all three split pairs. Codewords now come from
a 2,098-word dictionary∩vocabulary benign-noun pool, one per concept, each used once — so split codeword
sets are **disjoint**, which is what an "unseen codeword" claim needs and **v1 could not support at all**.

⚠ **Three documented gaps:** N = 138, not the planned 200 (the rest needs API calls); the **benign-condition
demos are placeholders for 59 of 138 rows** — that condition is unusable for those until regenerated; and
harm categories are unbalanced.
⚠ **A claim in our own plan was wrong:** §5 P1b asserts "zero ClearHarm instruction pairs exceed TF-IDF
cosine 0.5". False — max pairwise cosine is **0.690**, with 3 pairs above 0.5. The conclusion survives
(cross-split max in the built v3 is lower), but the plan text needs correcting.

### ✅ Validator schema coverage complete — and it found a real data defect
9 previously-unknown schemas taught (p4ko band+perhead, p4b, p4c, p5b, p7, p7b, p7c, p7d, p9).
**Tree-wide FAILs 308 → 5.** +917 recomputed values (**14,482 total**). "No raw.jsonl" is now a separate
SKIP-legacy status so the 275 legacy dirs no longer drown out real failures; unrecognized schema stays a
loud FAIL.
**REAL MISMATCH FOUND (reported, data untouched):** `monotone_decreasing` in 2 of the 5 `phase9_dose` dirs
was computed under the **pre-audit α>1-inclusive definition** and disagrees with its own rows under the
current [0,1] definition. This is exactly what the Aug-2–5 sprint audit predicted would be stale on disk.
Also: 2 dirs carry a committed `summary.json` over a **0-row `raw.jsonl`** (aborted runs).

### ✅ P1 audit is now a re-runnable gate
`scripts/audit_phase21_baseline.py` reproduces all 411-row numbers and **exits non-zero** both when a
fixture has a blanked response (MUST-RERUN) and when a published rate drifts (SUSPECT). Verified no
generation text reaches stdout or JSON by fragment-matching all 411 responses. It also fixed a bug in the
inline draft: the near-blank predicate was `<=20`, reporting 3 rows and contradicting the published 2 —
one row is exactly 20 chars. Now strict `<20`.

---

### 🧪 P10 harness — the agent correctly REFUSED to substitute a broader intervention
This is the design decision that matters most in the whole P10 re-run, so it is recorded in full.

`pc.AllPositionMLPAblate` **cannot express** the experiment we need: it rewrites the whole MLP output on
every forward, which at prefill would zero L8–11 `mlp_out` at **every prompt position**, not just the demo
codeword positions — a strictly broader and *different* experiment. Rather than silently swap it in, the
agent built **`PhasedMLPZero`** (local to `phase_behav_write.py`): during **prefill** zero `mlp_out` only at
the target codeword positions — **verified bit-identical to the historical `ComponentOutSwap(zeros)`** —
and on **every KV-cached decode step** zero the newly generated position. Absolute positions are tracked by
a per-layer row counter reset on `__enter__` (rule: `zero iff p in prompt_positions or p >= prompt_len`).
`AllPositionMLPAblate` remains reachable as the opt-in `--allpos-arm`, honestly labelled a broader
**upper bound**, never the write-locus measurement.

**The confound the agent flagged, and the control that handles it.** `write_abl_decodesafe` = the old arm
**plus** zeroing L8–11 on every generated token. The decode half is *necessarily* broad — generated
positions are not known in advance, so it cannot be codeword-selective the way the prefill half is.
A raw baseline-vs-decodesafe ASR drop therefore **confounds "the write is needed" with "zeroing 4 MLP
layers on every generated token damages generation."** Mitigation built into the design: the count-matched
random-position control runs in **both** phasings and carries the identical decode-side damage, so
`delta_write_vs_randpos_decodesafe` isolates position specificity with damage held constant, and
`delta_decode_damage` (baseline − rand_pos_decodesafe) measures the damage on its own. **Read those two
keys, not the raw baseline-vs-decodesafe delta.**

Both phasings run in one experiment (`write_abl_prefill` = the historical arm, `write_abl_decodesafe` = new)
so the difference is directly measurable. `summary.json` carries a `legacy_arm_name_map` so old numbers
stay traceable. **BEHAV-CARRY needed no ablation change** — `AllPositionZHeadAblate` was already
decode-safe; the agent checked and correctly left it alone rather than making a gratuitous edit.
Verification: 18/18 synthetic checks, 4/4 in-situ arm checks through a real prefill+decode loop, 5 CPU
dry runs, suite still 205 passed.

### 📋 P9 manifest — only 7 of 16 Gate-7 arms are launchable today
Target join confirmed **86/86 (100%, all exact-tier, 0 unmatched, 0 ambiguous)**, 44 train / 42 test —
the instruction-text join works, the id schemes genuinely share nothing. `configs/manifests/
phase9_gcg_mac_matrix.json` has 16 arms, seeds (42,43,44), 200×64×44 = **563,200 candidate forwards per
arm-seed**, one negative-control flag, and a per-arm blocking dependency.
⚠ **Only 7 arms are runnable now.** The rest are gated on P6 (Jacobian objectives) or on P3–P6 validating an
attention/carry objective. **Arm 7 — the refusal-suppression objective, which the plan names as the
first-to-run and the only axis with demonstrated behavioral potency — is among the 7.**

---

### ✅ P6 Jacobian readout built — with a closed-form correctness proof
`scripts/phase6_jacobian_readout.py` · `slurm/run_jacobian.sh` · `tests/test_jacobian_synthetic.py`
Suite **205 → 224 passed** (+19), 13 skipped.

Computes `J[L,p] = dS/d resid[L][p]` for **two strictly separate targets**:
- **concept:** `mean logit(concept forms) − mean logit(codeword forms)` — byte-for-byte the `logit_diff`
  metric `48_attribution_patching.py` already uses, so Jacobian / AtP / true patching all attribute the
  **same scalar**;
- **refusal:** `⟨hidden_states[R][-1], unit(refusal_direction_L{R-1})⟩` — numerically the same quantity
  `phase_refusal_projection.py` reports, so the new column is directly comparable to the existing one.

Reports per layer: `‖J‖`, the projection of the activation on `unit(J)`, **plus** the plain-lens columns
(concept / refusal / signature) and `cos(unit(J), each direction)` — three lenses in one table.
**Fits nothing** (`fits_nothing: true` in the summary): no matrix, normalization or threshold is estimated,
so the plan's "fit on train, freeze, then test" protocol collapses to a single leak-free pass.
Correctness is proven against the **closed-form derivative** on a toy model to `atol 1e-9` — and getting
that proof required a `hi_prec()` helper that promotes bf16/fp16 to fp32 but never demotes fp64, because a
blanket `.float()` silently truncated the very comparison that establishes correctness.
Two guards worth keeping: a **Taylor gate** (perturb by `ε·unit(J)`, report measured/predicted) so a
non-linear readout gets reported as sensitivity-only, and an explicit **degeneracy exclusion** — if the
refusal scalar is read at `R == L+1` the gradient *is* the refusal direction and the lens becomes a
tautology, so that layer is excluded and recorded.

### ⚠️ Double-BOS inconsistency — confirmed, scoped, and NOT an invalidation
The P6 agent found that `ds_common.forward_hidden_states` (ds_common.py:858) tokenizes with the default
`add_special_tokens=True`. On an already-templated Llama string that prepends a **second BOS** — verified:
`[128000, 128000]`, 38 ids vs 37.

**Affected** (all go through it): `build_refusal_direction_llama.py` → *all 32 refusal directions*;
`phase_refusal_projection.py` → REFPROJ and the item-level AUC-0.87 result;
`phase_write_refusal_interaction.py` → the causal-decoupling result.
**Not affected** (use `add_special_tokens=False`): `pair_common`/`ComponentCapture`, `48_attribution_patching`,
and hence the concept directions, the doublespeak signature, and all phase3–7 causal work.

**I checked the two ways this could actually bite, and it does neither:**
1. **Off-by-one in the readout position? No.** Both the direction builder
   (`build_refusal_direction_llama.py:77`) and the projection reader (`phase_refusal_projection.py:69`) take
   `hs[...][0, -1, :]` — the *last* position. An extra prepended token shifts indices but the last position
   is still the last prompt token.
2. **Bias in the paired deltas? No.** The extra BOS is applied identically to direct/ds/neutral, so it is
   common-mode and cancels — the Aug-2–5 audit's original judgment was right.

**What genuinely remains:** refusal vectors live in a 38-token forward and concept vectors in a 37-token
one, so the **cross-family cosine** — i.e. the `|cos(concept, refusal)| ≤ 0.153` orthogonality claim —
compares vectors from slightly different contexts. One extra BOS is a small perturbation and that claim has
a wide margin, so this is a **methods-section caveat, not an invalidation**. **Folded into P7**, which is
rebuilding the directions anyway: build under `add_special_tokens=False` and report both conventions, so
the actual impact is *measured* rather than argued. `phase6_jacobian_readout.py` defaults to `False` (the
house convention for anything position-indexed) and exposes `--add-special-tokens true` to reproduce the
old forward exactly; the choice is recorded in RUNMETA.

---

### 🔥 P8.1 PROVISIONAL (n=36/86) — the sub-additivity may be ENTIRELY a ceiling artifact
**This is the most consequential thing the sprint has produced, and it points AGAINST our own P8.0
headline.** Read from the partial `raw.jsonl` of the running sweep. **PROVISIONAL — do not cite.**

| α | ASR(0,1) direct+refabl | I_max | **Î** | D=+2 | D=−2 |
|---|---|---|---|---|---|
| **0.25** | **0.306** ✓ in band | **+0.472** ✓ ≥ target | **+0.000** | 0 | 0 |
| 0.5 | 0.528 | +0.250 | −0.111 | 0 | 2 |
| 0.75 | 0.528 | +0.250 | −0.083 | 0 | 3 |
| 1.0 | 0.556 | +0.222 | −0.083 | 0 | 1 |
| 1.5 | 0.722 | +0.056 | −0.139 | 0 | 1 |
| 2.0 | 0.833 | −0.056 | −0.361 | 0 | 1 |

**Î tracks the ceiling.** As `I_max` shrinks with rising α, Î becomes progressively more negative; at the
**non-saturating α = 0.25 it is exactly 0.000** — additive — with **zero** items at D=+2 *and* **zero** at
D=−2. That is precisely the signature of a ceiling artifact: at α=1.0 the design cannot express a positive
interaction, so the estimator is pushed negative regardless of mechanism.

**⇒ If this holds at full n, the P8.0 reading changes.** We reported "Doublespeak and refusal-ablation are
sub-additive ⇒ shared refusal bottleneck", with the ceiling flagged only as making the *magnitude* unclean.
This suggests the ceiling may account for **all** of it, and that at a non-saturating dose the two are
**additive — i.e. independent channels**, which is closer to the *opposite* conclusion.

**Restraint required:** n=36 of 86, and the partial α=1.0 estimate here (Î=−0.083) differs from the full-86
value (−0.186), so these point estimates are noisy. What is robust even now is the **monotone Î-vs-I_max
relationship**, which is a statement about the design rather than about any one cell. Re-derive on the
complete data before concluding anything.

**P8.1's operating point (provisional): α = 0.25** — ASR(0,1) = 0.306 (target band 0.20–0.40) and
`I_max` = +0.472 (target ≥ +0.33, and 2.1× the +0.222 available at α=1.0).

**Controls at every α (this is what the project never had before — previously only α=1.0 was tested):**
α=0.0 is an **exact no-op** (direct_refabl_a0.0 ASR 0.111 = direct_base 0.111; refusal_rate 0.861 = 0.861),
and the norm-matched **random control is flat across the entire grid** (ASR 0.083–0.139 vs base 0.111;
refusal_rate **0.861 at every single α**). Specificity is now demonstrated across the whole dose range.

---

### 🛑 Tick-15 self-correction: my own "sharper test" of the ceiling was INVALID
I tried to settle the tick-14 ceiling question by splitting items into those with *headroom* (neither
factor alone jailbreaks) and those already *saturated*. The prediction was: if the negative Î is purely
arithmetic, `Ihat_headroom` should be ≈ 0 at every α. Result (partial, n=46/86):

| α | Î all | n_head | **Î headroom** | n_sat | Î saturated |
|---|---|---|---|---|---|
| 0.25 | −0.022 | 22 | **+0.273** | 24 | −0.292 |
| 0.5 | −0.130 | 16 | **+0.500** | 30 | −0.467 |
| 1.0 | −0.152 | 14 | **+0.643** | 32 | −0.500 |
| 2.0 | −0.348 | 6 | **+0.833** | 40 | −0.525 |

**`Ihat_headroom` is strongly POSITIVE — and it is meaningless.** In that subgroup `Y(1,0)=Y(0,1)=0` by
construction, so `D_i = Y(1,1) − 0 − 0 + Y(0,0) = Y(1,1) + Y(0,0) ≥ 0` **mechanically**. It *cannot* be
negative, exactly mirroring how the saturated subgroup *cannot* be positive. **Both halves are forced by
the selection, so this decomposition cannot adjudicate the mechanism in either direction.** I nearly
reported "+0.83 synergy among headroom items", which would have been a serious error.

**What it does establish (weakly):** the aggregate Î is a mixture whose sign is driven by the saturated
fraction, which grows 24/46 → 40/46 as α rises. Consistent with the tick-14 ceiling reading, but not
independent evidence for it.

**⇒ This is exactly why plan §5 P8.4 requires the resistant subgroup to be defined on a SEPARATE
calibration split and pre-registered before being applied to fresh items.** Selecting it on the same data —
which is what I just did — is invalid no matter which direction the answer comes out. The plan's own design
requirement is vindicated; the shortcut is not available. **The tick-14 finding therefore stands exactly as
stated — provisional, resting on the monotone Î-vs-I_max relationship — and is NOT strengthened by this.**

---

### 📏 NEW METHODS RESULT — the StrongREJECT judge's irreducible noise floor, measured exactly
Chasing an anomaly produced a genuinely useful number. On curated, `direct_refabl_a0.0` (α = 0, which
should be an exact no-op) gave ASR 0.294 vs `direct_base` 0.314 — **1 of 51 labels and 2 of 51 scores
differed**, max |Δscore| = 0.75. On clearharm: 0/66 labels but 3/66 scores.

I traced it rather than assuming. The hook computes `h − alpha·proj·d`, which at α=0 is exactly `h` in
IEEE arithmetic — so either the hook was wrong or the judge was. **Settled by hashing the generations
(sha256, text never inspected): all 51 pairs are BYTE-IDENTICAL.**

⇒ **α=0.0 is a true numerical no-op; the hook is correct. The divergence is 100 % StrongREJECT judge
nondeterminism on byte-identical input.**

This is the cleanest possible measurement of the judge noise floor, because the generation is held exactly
constant — previous estimates (the 7.5 % replicate flip rate from tick 4) conflated judge noise with real
generation differences.

| quantity | measured |
|---|---|
| label flips on identical text | **1/51 = 2.0 %** (curated), 0/66 (clearharm) |
| score changes on identical text | 2/51 = 3.9 % (curated), 3/66 = 4.5 % (clearharm) |
| max \|Δscore\| on identical text | **0.75** |

**Consequence for every behavioral claim: a ΔASR below ~2 pp is indistinguishable from judge noise**, even
with the model and generation perfectly fixed. This belongs in the paper's methods section, and it sharpens
the tick-4 caveat: of the 7.5 % replicate flip rate, ~2 pp is irreducible judge variance and the remainder
is genuine generation difference.

### 📉 P8.1 curated (COMPLETE, n=51) — no usable operating point on this cohort
Full run-directory contract satisfied for the first time on a real run: RUNMETA + DONE + summary + raw + gens.

| α | ASR(0,1) | refusal | randASR | I_max | Î |
|---|---|---|---|---|---|
| 0.0 | 0.294 | 0.686 | 0.314 | 0.745 | −0.020 |
| 0.25 | 0.529 | 0.431 | 0.294 | 0.510 | −0.176 |
| 0.5 | 0.588 | 0.333 | 0.333 | 0.451 | −0.216 |
| 1.0 | 0.667 | 0.255 | 0.294 | 0.373 | −0.333 |
| 2.0 | 0.627 | 0.275 | 0.235 | 0.412 | −0.196 |

**No α lands in the 0.20–0.40 band except α=0 (the no-op).** ASR jumps 0.294 → 0.529 between α=0 and
α=0.25 — the dose response is too steep on curated; it would need α ≈ 0.1. **So the α=0.25 operating point
chosen from clearharm does NOT transfer to curated**, and a curated arm of Phase 8 would need its own
calibration.
Note also `DS ASR (0.275) < direct base ASR (0.314)` on curated — the attack is *net-negative* by ASR on
this cohort, which is the known concept-dilution weirdness and makes it a poor cohort for an interaction
test regardless of α. Its random control is also less flat than clearharm's (0.235–0.333 vs base 0.314).

---

### ⚠️ CORRECTION to tick 14 — "additive" was the wrong word
Tick 14 reported Î = +0.000 at α=0.25 and called it **"exactly additive."** That framing is wrong, and the
analyzer caught why: **the ~2 pp judge noise floor is measured PER ARM, but Î is a contrast of FOUR judged
arms**, so Î's own floor is *at least* 2 pp and plausibly larger. On the near-complete clearharm data
Î_binary at α=0.25 is **−0.013 (1.3 pp) — below that floor.**

**⇒ The correct statement is "no interaction is DETECTABLE at the sub-saturating dose", not "the
interaction is measured to be zero."** Those are different claims and only the first is supported.
The tick-14 direction of travel survives; the certainty does not.

### 🎯 P8.1 — operating point selected, and the ceiling relationship is now quantified
`reports/PHASE8_1_ALPHA_CALIBRATION.md` · `scripts/analyze_alpha_calibration.py` ·
`outputs/alpha_calibration.json`. Statistics are **reused** from `analyze_interaction_2x2.py` (same seed,
same 10 000 bootstrap / 50 000 permutation), not reimplemented — verified by reproducing the tick-16
curated numbers exactly through the reuse path.

**clearharm (PROVISIONAL, n=78/86): α = 0.25** — the *sole* qualifying dose. ASR(0,1) = 0.295,
`I_max` = **+0.487**, i.e. **2.1×** the +0.231 available at α = 1.0. Train, test and pooled each select it
independently; the tie-break never fires. `I_max` has drifted +0.472 (n=36) → +0.487 (n=78) as rows land,
so this is re-run when `summary.json` appears.
**curated (COMPLETE, n=51): NO α qualifies.** The dose response *steps over* the band — 0.294 at α=0 (the
no-op) straight to 0.529 at α=0.25 — so it would need α ≈ 0.1, which was not run. Every α>0 satisfies the
*ceiling* criterion (min `I_max` +0.353); it is the ASR band alone that fails.

**The ceiling relationship, quantified rather than eyeballed:** Spearman(`I_max`, Î) = **+0.955 curated /
+0.991 clearharm** (binary); +0.883 / +0.937 on the graded score. **The decisive detail: on curated the
ceiling REVERSES between α=1.5 and α=2.0 (`I_max` +0.353 → +0.412) and Î reverses with it
(−0.353 → −0.196).** I re-derived this myself: Î follows `I_max` even where `I_max` is **non-monotone in
α**, which rules out the benign explanation that both merely trend with dose. And `I_max` is a function of
the **marginal** cells only — it carries no information about the joint cell (1,1) — so a real mechanism
has no reason to track it. (My independent Spearman was +0.928 vs the report's +0.955, a grid-choice
difference; same conclusion.)

**Specificity now holds across the whole dose range** — the first time this project has had the
random-direction control at anything other than α = 1.0. At α = 0 the refusal and random arms agree to
within the noise floor (exactly as a no-op must); at every α > 0 the gap is +0.179 to +0.641 with paired
exact McNemar **p ≤ 0.0042 (curated) and ≤ 0.0005 (clearharm)** — 9× to 32× the floor. The random direction
leaves refusal_rate inert (0.667–0.725 vs 0.686 baseline curated; 0.846–0.872 vs 0.846 clearharm) while the
true direction drives it to 0.216 / 0.141.

**The judge floor is slightly WORSE than tick 16 measured:** clearharm 1/78 labels (1.3 %) but **5/78
scores (6.4 %)** and **max |Δscore| = 1.00** (vs 4.5 % / 0.75). Below-floor cells are flagged with ‡ in
every table of the report.

Verification the agent ran: 140 curated cell values cross-checked against the run's own `summary.json`
(independent code path) — 0 mismatches; 6 from-scratch hand recounts; McNemar validated against
`scipy.stats.binomtest` to 1e-12; truncated-file robustness tested with a deliberately corrupted record.

---

### 🏁 P8.1 FINAL (clearharm n=86, curated n=51) — **P8.0's sub-additivity is a saturation artifact**
This is the result the whole α sweep was for, and it overturns our own P8.0 headline.

**clearharm pooled, n=86, complete:**

| α | I_max | **Î (binary)** | 95 % CI | **p** | ref−rand ΔASR | McNemar p |
|---|---|---|---|---|---|---|
| 0.0 (no-op) | +0.651 | **+0.000** | [−0.047, +0.047] | 1.0000 | +0.000 ‡ | 1.0000 |
| **0.25 ← operating point** | **+0.477** | **−0.023** | [−0.151, +0.105] | **0.8597** | +0.186 | 0.0001 |
| 0.5 | +0.291 | −0.081 | [−0.244, +0.081] | 0.3838 | +0.395 | <1e-4 |
| 0.75 | +0.186 | −0.174 | [−0.337, +0.000] | 0.0644 | +0.465 | <1e-4 |
| **1.0 ← the dose P8.0 used** | +0.186 | **−0.209** | [−0.372, −0.047] | **0.0203** | +0.488 | <1e-4 |
| 1.5 | +0.105 | −0.256 | [−0.419, −0.093] | 0.0054 | +0.558 | <1e-4 |
| 2.0 | +0.023 | −0.314 | [−0.477, −0.151] | 0.0004 | +0.663 | <1e-4 |

**Spearman(I_max, Î) = +0.991** (pooled binary; +0.991 on the graded score).

**The verdict.** At the operating point — α = 0.25, where the design has ample headroom (I_max = +0.477) —
**Î = −0.023 with p = 0.86: no interaction is detectable**, and |Î| sits at the judge noise floor.
Sub-additivity only becomes significant **as headroom disappears**: p runs 0.86 → 0.38 → 0.064 → **0.020**
→ 0.005 → 0.0004 while I_max falls +0.477 → +0.023. At α = 1.0 — the dose P8.0 used — we reproduce the
P8.0 result exactly (Î = −0.209, p = 0.020; P8.0 reported −0.186, p = 0.045 with the same estimator).
`D_i = +2` occurs **0 times at every α**, as before.

⇒ **P8.0's "Doublespeak and refusal-ablation are sub-additive ⇒ shared refusal bottleneck" is NOT
supported.** The sub-additivity is a property of running the ablation at a saturating dose, not of the
mechanism. **The P8.0 report and any downstream text must be corrected.**

**What this does NOT establish.** Absence of a detectable interaction is **not** evidence of independence.
With n = 86 and a multi-arm noise floor ≥ 2 pp, an interaction of small-to-moderate size would be invisible;
the CI at α = 0.25 spans [−0.151, +0.105]. The honest claim is: *at a dose with real headroom, no
interaction is detectable, and the previously reported sub-additivity does not survive de-saturation.*

**curated: no α qualifies** (dose response steps 0.294 → 0.529 over the band; would need α ≈ 0.1).
Its Spearman(I_max, Î) is +0.955, the same ceiling signature.

**The α = 0 anchor is perfect on the full data:** Î = +0.000 exactly, p = 1.0, ref−rand ΔASR = +0.000,
33/86 items already saturated — the no-op behaves as a no-op in every column.
**Specificity at the operating point:** ref−rand ΔASR = +0.186, McNemar **p = 0.0001**, ~9× the noise floor,
with the random arm leaving refusal_rate at 0.872 vs the true arm's 0.674.
**Judge floor on the full clearharm cohort:** 1/86 labels (1.2 %), 5/86 scores (5.8 %), max |Δscore| = 1.00.

### 🐛 Analyzer CLI silently skipped on a malformed argument
`--run` takes `cohort=path`; I passed a bare path, so `run_dir` resolved to `""`, the script printed
`[skip] ... no raw.jsonl in ` and **still exited 0 after writing an empty report**. That is the same
"silent-skip false-OK" pattern we deliberately fixed in the validator in tick 5. Logged for the next tick —
a malformed `--run` spec must be a hard error, not a skip.

---

### 🎯 P1b COMPLETE — v3 expanded to the POWERED size (n=324) for $0.14
`data/splits/clearharm_doublespeak_v3.json` · `scripts/expand_concepts_v3.py` · `reports/P1B_V3_SPLIT.md`

| | before | **after** |
|---|---|---|
| examples | 138 | **324** (target hit exactly) |
| distinct concepts | 45 | **224** (+179) |
| intent clusters | 40 | **215** |
| placeholder benign demos | 59 | **0** |
| straddling concepts / codewords / clusters | 0 | **0** |

Split 162/82/80. `validate_data_integrity.py`: **12 ok / 0 warn / 0 FATAL**. Independently re-verified by
me: zero cross-split overlap on concept **and** codeword **and** cluster across all three split pairs;
6 conditions with 0 empty cells. **Total spend $0.14** (496 calls).

**This is the fix for P8.1's uninterpretable CI.** The plan's power table needs n=324 to detect an
interaction of 0.15 under Holm m=5; we were at 138 with CI [−0.151, +0.105].

**Four findings worth carrying forward:**
1. **The v1 drop mystery is settled — and my assumption was wrong.** Of the 62 rows where the v1 extractor
   returned `None`, gpt-4o now yields ok=52 / multi-token=7 / model-said-none=3 and **api_error = 0**. The
   `except Exception: return None` was **never firing**; the losses were simply gpt-4o-mini's weaker
   extraction. The plan (and my tick-9 note) treated the swallowed-exception as the likely cause.
2. **Recovery beats generation, by a lot.** Steps 1–2 cost **$0.026** and produced **+25 concepts** —
   **12× the concept yield of the entire previous expansion (+2)**. Always exhaust recovery first.
3. **Yield went 10.7 % → 35.0 %** from two fixes: don't make the model invent a single-token codeword (draw
   from the 2,059-word pool instead), and send the **full** avoid-list — the old `sorted(used)[:40]` was a
   real bug, and 254 of 382 rejects were still `already_used`.
4. **Concept supply, not budget, is now the binding constraint.** Accepts per batch decayed 14→1 over 29
   batches: common single-token harmful English nouns are near-exhausted at ~224. Reaching the plan's
   350–450 band needs a **relaxed tokenization contract**, not more money. (52 further concepts are already
   paid for and banked → n=376 / 276 concepts available on demand.)

⚠️ **NEW STRUCTURAL FACT the analysis must respect:** the split now has **two cohorts** — `clearharm` (170)
and `generated` (154). Both independently satisfy ≥20/≥20 at ~50/25/25. But the generated instructions are
shorter and more templated (cross-split instruction TF-IDF rose 0.489 → 0.621, still 0 pairs above the 0.7
threshold). **Every headline result must be reported per cohort as well as pooled** — a cohort × condition
interaction would mean the generated arm is *not* exchangeable with real ClearHarm and cannot be pooled.

---

### ✅ P2 COMPLETE — v2 replicates the all-occurrence doubling
`outputs/phase6_KO_clearharm_mlp_out_all_layer_20260805_220938_718027` (the relaunch of the job that hung
at tick 8). Wilcoxon + Holm over 32 layers:

| cell | demo-only L9 | **all-occurrence L9** | ratio |
|---|---|---|---|
| v2 dev (n=59) | +0.0798 | **+0.1101 [0.060, 0.170]** | 1.38× |
| v2 heldout (n=55) | +0.0304 | **+0.0649 [0.030, 0.108]** | **2.13×** |

L9 is the argmax and Holm-significant on **both** splits; Holm band dev L7–L12 (+L15, L20), heldout
L9/L12/L22. The 1.38–2.13× range sits inside the v1 range (1.42–2.27×), so **the finding now replicates on
all three benches.** P2 is done.

### ⚠️ P7 SMOKE — the refusal directions are NOT all valid, and L9 may undercut a headline
`outputs/refval_clearharm_20260805_215332_717880` — **smoke only, `DSVALN=3`.** The harness works: 64 rows
over 32 layers × 2 direction families, random controls **0.000 throughout**, per-layer validity computed
for both the shipped carrot/bomb-fit directions (`existing`) and a ClearHarm refit (`clearharm`).

**Preliminary validity: `existing` 15/32, `clearharm` refit 13/32.** Invalid layers are essentially all of
**L0–L14**, plus a mid-late band L24–L27.

| layer | why it matters | smoke verdict |
|---|---|---|
| **L18** | the direction used by *every* behavioral refusal arm | **VALID** (ablate +1.000, rand +0.000) ✓ |
| **L22** | the calibrated depth-localization headline layer | **VALID** (sep +0.413) ✓ |
| **L9** | one of the four calibrated injection layers | **INVALID** ⚠️ |

**The risk this creates.** The calibrated depth result concluded *"the refusal decision is read mid-late
(L22 significant) and NOT early (L9 ns)."* If the **L9 direction is not a valid refusal direction**, then
"L9 ns" is **uninformative** — injecting a direction that doesn't control refusal should produce no effect
regardless of depth. That would not overturn the L22 finding, but it would **remove the contrast that gives
the depth claim its force.**

🛑 **Do not act on this yet: `DSVALN=3` means every ablate/induce gain is a ±0.333 single-item flip**, so
each validity flag is a one-item decision. The full run (`DSVALN=20`) is launched as **718378**. The two
layers our headlines actually depend on (L18, L22) both pass even at this n, which is mildly reassuring.

---

### ✅ P10 COMPLETE — the concept-write null SURVIVES the decode-safe re-test
`reports/P10_DECODE_SAFE_WRITE.md` · job 718938, n=86, 1 h 23 m. **This closes the §0.9 defect.**

The original "behaviorally inert" null was measured with an ablation that **silently fired during prefill
only** (`ComponentOutSwap`'s position guard drops every position when `seq == 1`). Generation was never
tested. Now it is — both phasings in one experiment, on the same items.

| split | arm | ΔASR | 95 % CI | McNemar p | Holm |
|---|---|---|---|---|---|
| train | `write_abl_prefill` | −0.023 | [−0.114, +0.068] | 1.000 | 1.0 |
| train | **`write_abl_decodesafe`** | **+0.068** | [−0.068, +0.205] | 0.508 | 1.0 |
| test | `write_abl_prefill` | +0.095 | [−0.048, +0.238] | 0.344 | 1.0 |
| test | **`write_abl_decodesafe`** | **−0.071** | [−0.238, +0.095] | 0.581 | 1.0 |

**Every CI includes 0; every McNemar p ≥ 0.34; every Holm = 1.0; `empty_rate` = 0.0 in all 10 cells.**
Specificity-controlled (`write − rand`, decode damage held constant): **train +0.023, test −0.072 —
opposite signs.** The prefill arms also flip sign (−0.023 / +0.095). Sign-flipping across a pre-registered
split is the signature of noise, not of a small real effect.

**The confound was real and worth building for.** On train the random-position decode arm *alone* moves ASR
**+0.0455** — about **two thirds** of the apparent +0.0682 "necessity". Reading the raw delta would have
produced a reported effect that is mostly generic decode damage. This is exactly why the harness was built
to run the count-matched control in *both* phasings.

⇒ **The result is unchanged but the evidence is now real.** The dissociation is stronger than before,
because it finally rests on a measurement that did what it claimed. Limitation unchanged: a null at n=86,
where detecting ΔASR ≈ 0.07 needs n ≈ 275 — *"no effect detectable at this n"*, not *"no effect"*. The v3
benches (170 + 154) are the natural power upgrade.

---

## Tick log (most recent first)

### Tick 69 — 2026-08-06 — started P4b prerequisites: the hook-firing test (retraction-prevention gate)
Queue empty, so I began the **P4b/P5 max-scope program** the agents costed
(`P4B_P5_MAXSCOPE.md`: P4b ≈15.7 GPU-h, P5 ≈4.9 GPU-h — far below the 440 GPU-h the first estimate
feared; GQA verified from the config, K/V collapsed to group-level). Started with the **GPU-free
prerequisites that gate the GPU work**, per the plan's own ordering, rather than burning GPU on an
un-gated run.

**P4b-0.1 — the hook-firing assertion test (`tests/test_hook_firing_synthetic.py`).** The readiness
flagged that *"there is no activation-delta assertion anywhere in this repo"*, and that is the exact gap
behind the `phase5b_qkv.py` retraction: a patch whose hook silently did **not** fire produced a clean
null that got read as a scientific negative. The new test asserts, on the ToyModel harness (reused, not
duplicated): the hook fires once per forward **and moves the output**; a non-self donor moves the readout
while a self donor is an exact no-op; a zero donor (ablation) still moves a non-zero slice; and an
out-of-range position is a no-op *for the right reason* (paired with an in-range edit that does apply).

**Self-review caught a weak test and I fixed it.** My first `test_..._fires_once_per_forward` counted
forwards through `o_proj` with its *own* observer hook — so it passed even with a **dead** ZHeadPatch,
because the observer fires regardless. I verified this by monkeypatching ZHeadPatch to a no-op: 3 of 4
tests caught the dead hook, that one did not. Added an output-delta assertion; **now 4 of 4 catch a dead
hook**, confirmed by the same control. A firing test that can't detect a dead hook is exactly the trap
this file exists to close, so it had to actually fail.

**Fixed a real bug in my own P4a wrapper.** P4a (induction-head identification, zero new analysis code)
was cancelled in tick 55 for concurrency and never re-run. Relaunching it, **both jobs died at line 41**:
`DSBENCH: set DSBENCH`. When I built `run_p4a_identify.sh` in tick 53 by copying the edgeKO wrapper's
header, I left its `: "${DSBENCH:?set DSBENCH}"` block in place — and it fires *before* my P4a-specific
`: "${DSBENCH:=…default}"` line further down. So the wrapper had **never once run successfully**; the
tick-53 "launched P4a" was a submission that errored in seconds. Removed the entire leftover edgeKO block
(the `:?`, its comma-guard, the `LAYER_ARG` logic, the duplicate GPU check), `bash -n` clean, resubmitted
as **728475 / 728476** (dev + heldout). This is why a wrapper must be watched to first-row, not just to
"submitted".

**Remaining P4b-0 prerequisites** (next ticks, all GPU-free): 0.2 the `configs/manifests/p4b.json`
enumerating the 12 800 cells, 0.3 the Holm family pre-registration (one family per channel×position-set,
**not** one family of 12 800 — which would annihilate a real effect of the observed 0.0325 size), and 0.4
the v3 bench split for the leakage-clean replication.

### Tick 68 — 2026-08-06 — "DO BOTH" pays off: P8 is null at BOTH doses, and the strong dose is where it counts
**Both α doses now done at full n = 127, and the "run both instead of choosing" call from tick 63
converts the whole dose-rule dispute into a robustness result:**

| | α = 0.05 (rule-as-written) | **α = 0.20 (specificity-corrected)** |
|---|---|---|
| `Î` | **0.0000**, p = 1.0000 | **0.0000**, p = 1.0000 |
| CI | [−0.063, +0.063] | [−0.087, +0.087] |
| manipulation works? | ΔASR +0.032, p = 0.125 — **NO** | ΔASR +0.142, p = 1.2 × 10⁻⁴ — **YES** |

**This is the strongest form of the P8 null.** At α = 0.05 the ablation barely moves ASR and doesn't beat
its random control — a null there could be dismissed as "nothing was happening". At α = 0.20 the ablation
**unambiguously fires** (ΔASR +0.142, ~7× the judge floor) and the interaction is *still* exactly zero.
Both cells are exactly additive — I checked the arithmetic: α=0.20 additive-predicted (1,1) = (1,0)+(0,1)−(0,0)
= 0.402, observed **0.402**, diff 0.0000.

**Two independent exact zeros invited suspicion, so I verified them from raw labels** rather than trust
the analyzer. Genuine cancellations, not stuck values: α=0.20 has **29 of 127 items** with a non-zero
`D_i` (−2:1, −1:13, +1:15) averaging to exactly zero. A well-populated null.

**The methodological threat is now a footnote.** Whatever one thinks of the pre-registered dose rule,
`Î` = 0.000 at both the weakest and the strongest defensible dose. Written up as **§2b** of
`P8_INTERACTION_V3.md`. The report-vs-JSON checker passes it clean (0 near-misses).

**On the user's re-issued directive** ("implement the plan, reuse code, don't skip stages, fan out
subagents, commit often"): this is the standing loop instruction. The 30-min cron `86decf2e` is still
live, so I did **not** create a duplicate. Continuing the plan's phase order.

**What remains open, unchanged:** the max-scope plans for P4b / P5 / P9 (agents wrote
`P9_UNBLOCK_PLAN.md` and `P4B_P5_MAXSCOPE.md` — not yet acted on), and the remaining bug-hunt items
(B5, B7, B8, O4, and the `code-analysis` findings). Next tick triages those.

### Tick 67 — 2026-08-06 — α=0.05 is a perfect null but an INERT dose; built a report-vs-JSON checker (and hit its limit)
**α = 0.05 landed at full n = 127 (job 728310), and it is exactly what tick 59 predicted.**

| | value |
|---|---|
| `Î` | **0.0000 exactly**, CI [−0.063, +0.063], **p = 1.0000** |
| `I_max` | +0.7008 |
| specificity ΔASR ref−rand | **+0.0315, McNemar p = 0.125 — NOT significant** |
| cells | (0,0) 0.158 · (1,0) 0.276 · (0,1) **0.181** · (1,1) 0.299 |

**The cells are almost exactly additive**: 0.158 + 0.118 + 0.024 = 0.300 against an observed 0.299. And
that is the point — **refusal-ablation adds only +2.4 pp at this dose and does not beat its own random
control**, so there is nothing for Doublespeak to interact *with*. A perfect null from an inert
treatment. This is the concrete demonstration that the pre-registered tie-break selects a dose where the
experiment cannot fail. α = 0.20 (728311, 120/127) is the informative half of the pair.

**Fixed O1** — the two `phase9_dose` summaries ship `monotone_decreasing: false` while their own stored
curve is strictly decreasing (.6902 .6448 .6191 .5880 .5750). The curve and every ASR are correct; only
the derived boolean is wrong. Annotated both with `_STALE_VERDICT` explaining that and pointing at the
curve, since re-running a 3-day-old GPU job to fix a boolean is not warranted and the validator already
flags it as the corpus's only `summary!=raw` mismatch.

**Built `scripts/check_report_vs_json.py`** for the gap I named last tick: nothing checked *report prose*
against the JSON it quotes. **It immediately found a real defect** — `REP_PREDICTS_BEHAVIOR.md` still
carried **two claims I had already withdrawn**:
1. *"Both beat the historical L21 value of 0.874"* — withdrawn in tick 59 (ΔAUC = +0.0139, CI
   [−0.0148, +0.0446], straddles zero).
2. *"L21 validates in only one direction family"* — withdrawn in tick 57 (on the out-of-sample `benign`
   population L21 validates in **both**).
Both corrections had been applied to the claim audit and **never propagated to the report.** That is the
same failure as O2, and it is now fixed in place with the reasoning spelled out.

**But I have to report that the tool does NOT fully close the gap it was built for, because I tested it
against the defect that motivated it and it failed.** O2's signature is a report holding the correct
value in one place *and* a stale copy in another; a presence check passes that. I added a
`--contradictions` mode that does catch it — and it fires **11 times on a clean corpus, 10 of them
false**, because numeric proximity cannot distinguish "a stale copy of X" from "the correct value of a
different quantity Y sitting nearby" (curated's −0.2157 is 0.0064 from clearharm's −0.2093, while O2's
real defect was a 0.0103 gap — **narrowing the window kills the true positive before the false ones**).

So rather than ship a noisy checker and claim the gap is closed:
- the **default** mode is precise and low-noise, and it earned its keep by finding the withdrawn claims;
- `--contradictions` is **opt-in**, documented as a review aid with a high false-positive rate;
- and the docstring states plainly that **the real fix is prevention, not detection** — generate tables
  from JSON instead of transcribing them, which is why O2 cannot recur in PHASE8_1 specifically.

### Tick 66 — 2026-08-06 — O2 fixed: 13 of 14 stale cells in the report that WITHDREW P8.0, one flipping a claim
**O2 [HIGH] is the most embarrassing find of the audit, because I thought I had already fixed this file.**
In tick 40 I refreshed `PHASE8_1_ALPHA_CALIBRATION.md` from n=78 to n=86 — but only the header note and
the auto-generated tables. The **hand-written §2 side-by-side table was left stale**, and it is the one a
reader hits first. 13 of its 14 clearharm cells were wrong, while the generated tables further down
showed the correct values. **The document contradicted itself.**

**And one stale cell flipped a stated conclusion.** The bullet above the table read: *"clearharm α = 0.25
gives `Î_binary` = −0.013 (1.3 pp) — **below the floor**"*. The committed value is **−0.0233 (2.3 pp)**,
which is **above** the ~2 pp judge floor. The conclusion — "no interaction detectable" — survives, but it
was resting on the wrong argument. It now rests on the right one: that cell's **sign-flip permutation
p = 0.86** and its CI [−0.151, +0.105] straddles zero. *Not detectable because the test says so, not
because it hides under the noise floor.*

**Fixed structurally, not by hand.** The table is now **regenerated directly from
`outputs/alpha_calibration.json`** at 4 dp, so it cannot drift from its own source again. Hand-copying a
table out of a JSON is what created this, and doing it a second time would just reset the clock.

**Then I swept the whole file for other survivors of the same drift** rather than assuming one fix was
enough. Five occurrences of the stale figures remained; four are legitimate historical narrative
("+0.487→+0.4767" explaining the refresh) and one was a **genuine stale assertion** — §"Consequences"
item 3 still declared *"`I_max` = +0.487 is the arithmetic ceiling"*. Corrected to **+0.4767**.

**The general lesson, recorded because it will recur:** every number hand-copied from a JSON into a report
is a future inconsistency. The claim audit checks *JSON against raw*, and the validator checks
*summary against raw* — but **nothing checks report prose against JSON**, which is precisely the gap O2
lived in. A report-vs-JSON consistency checker is the right follow-up.

**Jobs:** 727984 (generated low-α) **finished, 50/50**. 728310 (α=0.05) at 83/127 and 728311 (α=0.20) at
49/127 — the "do both doses" runs from tick 63.

### Tick 65 — 2026-08-06 — all 5 agents in: the P3 design is UNFALSIFIABLE as built; audit pointed at an empty dir
All five agents returned. Two findings change what we can claim, and both are verified by me rather than
taken on trust.

**B4 — the `Δrefusal − Δrandom` design cannot falsify a specificity claim.** I had already downgraded it
in §3c as a "floor". It is worse than that. The random axis is **not** inert — it is inert only for
*mild* interventions:

| cell | \|Δrandom\| |
|---|---|
| `edge_KO` (mild) | **0.00001** |
| `all_query_edges` (maximal generic damage) | **0.16626** — 4 000× larger, **opposite in sign** |

Because it moves the *other way* under maximal damage, subtracting it **inflates** the number:
+1.0755 − (−0.1663) = **+1.2417**. So the cell designed as the *maximal-generic-damage control* scores as
the **largest and most "specific" effect in the table**. A design where the generic-damage control wins
the specificity contest cannot falsify specificity, so **no "CI excludes 0 ⇒ specific" conclusion may be
drawn from that column at all.** §3c now says so.
This is a second, independent reason the `rand_edge − edge_KO` contrast is the right quantity — it never
subtracts across axes, so it cannot be inflated this way. `all_query_edges` keeps exactly one valid
job: showing the hook fires. **Its "specificity" cell should be ignored.**

**O3 — the claim audit pointed the flagship n=242 result at an EMPTY run dir, and still called it
PENDING.** `p8_v3_ch` mapped to `…035033_720724`, which contains **only a RUNMETA** — that job stalled on
n-801 and the cohort was re-run as **721956** (127 rows). The pointer was never updated. Worse, the
audit *green-lit* it: a dir with no `raw.jsonl` is reported "SKIP-legacy", which is not a failure state,
so the check designed to catch exactly this looked clean. Meanwhile `P8_INTERACTION_V3.md` declares the
same result COMPLETE — **the two governance documents contradicted each other on the project's headline
negative.**

Fixed all three ways: repointed to 721956, promoted **P1b-06 PENDING → VERIFIED** with the stale note
rewritten, and **closed the loophole** — a cited dir containing *nothing but* `RUNMETA.json` is now a
hard MISSING-DIR failure.
**I had to tighten that check twice.** My first version tested for `raw.jsonl`/`summary.json` by name and
false-positived on three legitimate artifact dirs (`unified_directions` ships `.npz`;
`behavioral_split_*` ships `behavioral_raw.jsonl`). A check that cries wolf on valid dirs trains the
reader to ignore it, so it now tests precisely for "RUNMETA and nothing else". Negative-controlled:
repointing at the empty dir reproduces `MISSING DIR P1b-06`, and nothing else fires.

**O5 — the −0.89 cross-axis constant was still on disk.** The buggy smoke's `summary.json` (726211) is
uncommitted but still readable, and its numbers cannot be recomputed correctly because
`base_proj_random` was never stored. Marked with an `_INVALID` field explaining exactly why, and the
validator already FAILs it by design.

Audit now: **89 claims — VERIFIED 67, WITHDRAWN 8, SUPERSEDED 4, UNDERPOWERED 5, UNVERIFIED 3,
PENDING 2**; 128 checks, 0 failures.

**Still to triage from the hunt:** O1 (phase9_dose ships a `monotone_decreasing` verdict opposite to its
own curve), O2 (PHASE8_1 §2's 14 clearharm cells are stale n=78 and one flips a stated conclusion),
O4 (PHASE_WRITE_REFUSAL_INTX's four ranges wrong, one sign wrong), plus B5/B7–B12 and the two
max-scope plans.

### Tick 64 — 2026-08-06 — the bug hunt hit a published number: my P3 "specificity" answered the wrong question
**`BUGHUNT_P3_CODE.md` returned 13 findings — 1 CRITICAL, 2 HIGH — and one of them lands directly on a
number I published last tick.** This is the value of the hunt, so I am stating it plainly rather than
softening it.

**B3 [HIGH] — the reported contrast does not answer P3's question.**
- The forced-choice harness reports **`rand_edge − edge_KO`, paired per item**: control = a count-matched
  random **edge set** → *"is it the **demo** edges?"* — which is P3's question.
- The decision-form aggregator I wrote reports **`Δrefusal − Δrandom` within a cell**: control = a random
  **axis** → *"is the shift on the **refusal direction**?"* — a different question.
- I computed the `rand_edge` rows (86 of them, both bands) and then **never used them in a contrast.**

**B4 [MEDIUM] compounds it:** the random-*axis* control is a **floor** — `Δrandom` = +0.0002 and −0.0000.
A control that never moves cannot discriminate, so the number I printed as "specificity" is numerically
just the raw shift on the refusal axis.

**Recomputed the correct contrast from the same committed `raw.jsonl`** (paired item bootstrap, 10 000
resamples, seed 0):

| band | `rand_edge − edge_KO` (refusal axis) | 95 % CI | excludes 0? |
|---|---|---|---|
| L8–11 | −0.0539 | [−0.1258, **+0.0035**] | **no** |
| L14–21 | +0.1245 | [−0.0175, **+0.2722**] | **no** |

**The P3 conclusion is UNCHANGED and now correctly controlled** — both null, sign flipping between bands,
the same noise signature that settled `rand_edge` in §3b. But the *quantity* was wrong, so
`PHASE3_ATTENTION_CAUSALITY_TARGETED.md` now carries a **§3c CORRECTION** and a pointer to it from the
verdict line at the top. The `all_query_edges` firing control stands unaffected — it was never a
specificity, and it is what makes these nulls informative absences rather than dead hooks.

**Fixed in the script so no future run repeats it:**
- **B1 [CRITICAL]** — `--mode perhead` is the **default**, and the decision-form aggregator keys cells by
  name only, so it structurally collapses every `(layer,head)` into one entry per item. A user who forgot
  `--mode band` would have burned a full GPU scan and got silently-wrong aggregation. Now **refused up
  front** with an explicit message (verified it fires).
- **B3** — `demo_edge_contrast` is now computed and written into `summary.json` with its definition
  spelled out, so the right quantity is emitted rather than left implicit in the rows.
- **B4** — `random_axis_is_a_floor` is now recorded, so nobody can read the per-cell number as a
  specificity when the control did not move.
- **B6** — **neither** path wrote `RUNMETA.json` or `DONE.json`; every edgeKO run to date violates the
  plan §2.1 artifact contract and cannot be provenance-audited. RUNMETA is now the first action and DONE
  the last, on **all three** exit paths (decision, band, perhead).

**Still to triage from this hunt:** B7 (`all_query_edges` is not "all previous keys" when `len(qdest)>1`
— affects an already-published FC number), B8 (the random-source pool includes BOS/attention-sink,
empirically 47× the impact of demo edges — which likely *explains* the `rand_edge` anomaly), B5, B9–B12.
Four more agents still running.

**Jobs:** 727984 (42/50), 728310 (α=0.05) and 728311 (α=0.20) both generating on n-802.

### Tick 63 — 2026-08-06 — Omer's ruling: DO BOTH / take the more detailed option. Decisions resolved.
**Omer's instruction: "in every consideration you have — choose to do both things or the more detailed
decision", plus an explicit ask to hunt code bugs AND output bugs.** That resolves everything that was
blocked, and it resolves it in the direction of *more* work, not less.

**Decision 1 — the α-selection rule (tick 59). RESOLVED: run BOTH doses.**
Rather than pick between the rule-as-written (α = 0.05, where the treatment is indistinguishable from its
control) and my proposed specificity-corrected rule (α = 0.20), the confirmatory 2×2 now runs at **both**,
full n, on clearharm v3: **728310 (α=0.05)** and **728311 (α=0.20)**.
This is strictly better than choosing, and not just diplomatically — **it converts a contested
methodological choice into a robustness check.** If `Î` is null at both doses, the interaction conclusion
provably does not depend on the dose rule, and the whole dispute becomes a footnote instead of a
threat to the result. If the two disagree, that is itself the finding and we will have measured it rather
than argued it.

**Decision 2 — P4b / P5 / P9 scope (tick 53). RESOLVED: maximum feasible scope, nothing deferred.**
In particular **P9 is no longer deferred** — I had recommended dropping it, and that recommendation is
overridden. Agents are producing the concrete unblocking plans now.

**Fanned out 5 agents on disjoint files**, three of them adversarial bug hunts as asked:
| agent | scope |
|---|---|
| `code-p3` | the newest, least-exercised code — the P3 decision-token path (~2 GPU runs of exercise). Specifically: `build_decision`'s `rfind` fallback, whether `--mode perhead` is silently broken under `--prompt-form decision`, whether the aggregator's early `return` skips DONE/RUNMETA, hs-row indexing, and whether the random direction is re-drawn per item or once per run |
| `output-bugs` | **wrong numbers in committed artifacts**, not wrong code: impossible rates, CIs that exclude their own point estimate, constants masquerading as effects (we already had one at −0.89), non-monotone α sweeps, and any number that differs between a report and its JSON |
| `code-analysis` | the scripts that turn rows into published numbers — the 2×2 estimator's cell↔arm binding, whether items missing an arm are dropped or zero-filled (one changes n, the other biases `Î` toward 0), and whether `paired_bootstrap_ci` resamples **pairs** or the two samples independently |
| `p9-unblock` | exact change list for the 4 P9 blockers, plus verifying the two known GCG hazards (`--no-filter-cand`, `suffix_placement=user`) are handled in current code |
| `p4b-p5-scope` | verify the GQA claim from the model config myself rather than trusting it; then max-feasible job tables. Includes whether a **group-level** K/V patch is a valid substitute for the impossible per-head one |

**727984** (generated low-α calibration) at 37/50.

### Tick 62 — 2026-08-06 — **P3 COMPLETE: the null REPLICATES on the carry band, and `rand_edge` is settled noise**
**Job 728189 (L14–21) finished**, so P3 now has both bands the circuit story implicates.

| cell | L8–11 specificity | **L14–21 specificity** |
|---|---|---|
| `edge_KO` (→ demo codewords) | −0.0034 [−0.0078, **+0.0010**] | **−0.0026 [−0.0056, +0.0003]** |
| `rand_edge` | −0.0613 [−0.1379, −0.0007] | **+0.1169 [−0.0262, +0.2630]** |
| `all_query_edges` (firing control) | **−0.6161** [−0.77, −0.46] | **+1.2417** [+0.92, +1.55] |

**The null replicates.** `edge_KO` is −0.0026 against −0.0034 — essentially identical, both CIs including
zero. No query→demo edge bottleneck at the decision point, in either the concept-write band or the carry
band.

**The firing control fires in both bands and flips sign** (−0.62 → +1.24). Both are far from zero, so the
hook works in each; and the flip is interpretable rather than alarming — severing *all* context at the
carry band drives the residual **toward** refusal (a decision token with nothing to condition on defaults
to refusing), while at the write band it drives away. The point that matters: the machinery moves this
readout by 0.6–1.2 while the targeted demo-codeword edges move it by ~0.003.

**`rand_edge` is settled, and my tick-61 caution was right.** I flagged it then as barely excluding zero
(−0.061, upper bound −0.0007) and declined to call it real. On the carry band it **includes zero AND
changes sign** (+0.117, [−0.026, +0.263]). A quantity that reverses sign between bands and straddles zero
in one of them is not an effect. Had I reported it as a finding last tick, this tick would have been a
retraction.

**Both bands re-derived from `raw.jsonl` before writing** (all cells match to 1e-4) and both reconcile
through the validator at **0 mismatches**.

`reports/PHASE3_ATTENTION_CAUSALITY_TARGETED.md` updated: status now COMPLETE for both bands, §3b added,
the "L8–11 only" limitation struck and replaced with the honest residual one — two bands, not all 32
layers.

**727984** (generated low-α calibration) at 25/50, on track.

### Tick 61 — 2026-08-06 — **P3 RESULT: no query→demo edge bottleneck at the decision point** (n=86)
**Job 727983 finished.** This is the destination §5 P3 says was never covered, and it produces a clean,
publishable negative — written up as **`reports/PHASE3_ATTENTION_CAUSALITY_TARGETED.md`**.

| cell | Δ refusal axis | Δ random axis | **specificity** | 95 % CI |
|---|---|---|---|---|
| `edge_KO` (→ demo codewords) | −0.0032 | +0.0002 | **−0.0034** | **[−0.0078, +0.0010]** |
| `rand_edge` (count-matched random) | −0.0570 | +0.0042 | −0.0613 | [−0.1379, −0.0007] |
| **`all_query_edges`** (firing control) | **−0.6664** | −0.0503 | **−0.6161** | **[−0.7705, −0.4643]** |

**The firing control is what makes this an informative null.** Blocking every incoming edge to the
decision token moves the refusal projection by **−0.62**, CI nowhere near zero. The machinery works, the
readout is movable, the hook fires — so `edge_KO`'s −0.0034 with a CI including zero is a real absence,
not the silent no-op this project has twice had to retract.

**Something I am reporting rather than burying:** `rand_edge` (−0.061) is *larger* than `edge_KO`
(−0.003), with a CI whose upper bound is −0.0007 — barely excluding zero across three uncorrected cells at
n=86. I would **not** claim it is a real effect. But it points the wrong way for a demo-codeword story: if
the retrieval edges were special they would move the readout *more* than arbitrary positions, not ~20×
less.

**Plan exit condition met** (the second branch): with the decision point now covered, the paper can state
that **retrieval is distributed/redundant with no single query→demo edge bottleneck** — and can say so at
the position where the refusal decision is actually made, not only at a forced-choice probe.

**Every reported number re-derived from `raw.jsonl` before writing it down** — all three cells match to
1e-4. The two baselines differ sharply (refusal +1.756 vs random +0.113), which is exactly the offset that
caused the tick-59 bug.

**Taught the validator the decision-form schema.** `expect_p4ko` was reporting every key MISSING because
the decision-form summary has a `cells` map instead of the `band.*` layout — a schema mismatch dressed up
as a data defect, the same shape as the refval gap. Now reconciles: **14 values, 0 mismatched**; 131
values across all 7 edgeKO dirs with **0 mismatches** and no regression on the forced-choice ones.
Negative-controlled (a corrupted specificity → `CHECK-FAIL`).

**The new guard immediately paid for itself:** it retroactively flags the buggy first smoke **726211** —
*"base_p_concept and base_proj_random cover different sids; a specificity would mix axes"* — which is
precisely the cross-axis defect of tick 59. The validator can now catch that class of bug on its own.

**Launched 728189** (L14–21 carry band) to complete the destination coverage; **727984** (generated
low-α calibration) at 8/50.

### Tick 60 — 2026-08-06 — cross-axis bug CONFIRMED fixed; real P3 run launched
**The re-smoke (726616) confirms the tick-59 fix**, and the before/after is unambiguous:

| cell | `dRand` BEFORE (buggy) | `dRand` AFTER (same-axis) |
|---|---|---|
| `edge_KO` | −0.8893 | **+0.0012** |
| `rand_edge` | −0.8983 | **−0.0078** |
| `all_query_edges` | −0.9363 | **−0.0459** |

`dRef` is unchanged in every cell, which is the right signature: that side was always computed correctly,
and only the random-control arm was being differenced against the wrong baseline. The two baselines are
**−0.6079** (refusal axis) and **+0.2238** (random axis) — a gap of ~0.83, which is precisely the constant
that was showing up as a fake control effect.

**Everything else in the summary checks out:** `attn_implementation: eager` (the assertion I added in
tick 49 is recorded in the artifact, not just asserted at runtime), `hs18 → decoder L17`, both baseline
fields present per row.

**Launched the real runs** (queue was empty, so two jobs, spread across all six nodes per tick 55):
- **727983** — P3 decision-token cell, full bench, L8–11 band. This is the destination the plan says was
  never covered.
- **727984** — the generated-cohort low-α calibration owed since tick 55.

**One preliminary observation I am explicitly NOT treating as a result:** in the smoke, `edge_KO`
specificity is ≈ 0 (−0.0004), which would be consistent with the existing B1 negative extending to the
decision point. **n = 4.** That is a sanity signal that the pipeline produces plausible magnitudes, not
evidence of anything; 727983 is the run that can actually answer it.

**Still open and unanswered — both need Omer:**
1. The **α-selection rule** picks a dose where the treatment is indistinguishable from its control
   (tick 59). My proposed third clause gives α = 0.20, but it is a post-hoc change to a pre-registered
   rule, so I have not applied it.
2. The **three scope decisions** on P4b / P5 / P9 (tick 53).

### Tick 59 — 2026-08-06 — the smoke earned its keep (found a real bug); and the α-selection RULE is broken
**The P3 smoke did exactly what a smoke is for: it found a bug in code that looked fine.** 726211 ran to
completion and produced a well-formed decision-form summary — `attn_implementation: eager` recorded,
`proj_layer_hs 18 → decoder L17`, `valid: None`, both projection fields present. But the numbers were
impossible:

```
edge_KO          dRef=+0.0008   dRand=-0.8893   spec=+0.8901
rand_edge        dRef=+0.0194   dRand=-0.8983   spec=+0.9177
all_query_edges  dRef=+0.0488   dRand=-0.9363   spec=+0.9852
```

**A norm-matched random direction moving −0.89 in every cell, identically, is not a control effect — it is
a constant.** Cause: I computed `drnd = proj_random(KO) − base_ref`, where `base_ref` is the baseline on
the **refusal** axis. Subtracting one axis's baseline from another axis's projection measures the fixed
offset between two directions, not an intervention. I had computed `base_proj_random` in the first draft
and **dropped it when I refactored the cells through `emit()`** — a refactor that preserved every visible
field and silently broke the arithmetic.

Fixed: both baselines are now stored per item, `drnd` is a **same-axis** delta, and the aggregator
**refuses to run** if any item lacks `base_proj_random` rather than silently computing a cross-axis
difference. Re-smoke launched (726616).

---

### ⚠️ THE α-SELECTION RULE IS BROKEN — a decision for Omer

725172 finished (50/50). The v3-native low-α calibration works, and it exposes a flaw in the
**pre-registered** operating-point rule that could not show up before, because until now only one dose
ever qualified.

| α | `I_max` | ΔASR ref−rand | McNemar p | |
|---|---|---|---|---|
| 0.0 (no-op) | +0.780 | +0.020 | 1.000 | |
| **0.05** | +0.740 | **+0.040** | **0.500** | ← **the rule selects this** |
| 0.10 | +0.680 | +0.100 | 0.0625 | |
| 0.15 | +0.620 | +0.140 | 0.0391 | |
| 0.20 | +0.620 | +0.180 | 0.0117 | |
| 0.25 | +0.560 | +0.220 | **0.0010** | |

**Five doses satisfy the rule, and its tie-break — "larger `I_max` wins" — picks the weakest one.** That
is not bad luck, it is structural: `I_max = 1 − ASR(1,0) − ASR(0,1) + ASR(0,0)` is *maximised when the
marginals are smallest*, so "prefer more headroom" is equivalent to "prefer a weaker intervention". At the
selected α = 0.05 the refusal ablation is **statistically indistinguishable from a random direction**
(ΔASR +0.040, p = 0.50). **The rule selects a dose at which the treatment does not exist.**

**What I propose, and why I am not just doing it:** add a third clause — *the manipulation must be
specific*, i.e. refusal-ablation must beat its count-matched random control — then take the largest
`I_max` among the doses that pass. That yields **α = 0.20** (`I_max` +0.620, ΔASR +0.180, p = 0.0117;
α = 0.15 ties on `I_max` but has weaker specificity). This is **a post-hoc change to a pre-registered
rule**, and that is precisely the kind of thing that must be declared rather than quietly applied — so it
is Omer's call. The interaction estimate itself is unaffected; only the dose choice is.

**A validation worth recording:** at α = 0.25 this n = 50 subsample gives `ASR(0,1)` = **0.400** against
**0.402** from the full-n run. That is a 0.002 agreement, and it retroactively justifies the tick-53
decision to calibrate on a subsample instead of letting the job die at walltime.

**Still owed:** the generated-cohort low-α calibration (cancelled in tick 55 to cap concurrency) has not
been re-run.

### Tick 58 — 2026-08-06 — smoke-testing the P3 code I wrote but never ran; desk-checked its failure modes
One slot free under the 2-per-node policy, and the right thing to put in it is a **smoke of the P3
decision-token cell** — I wrote a substantial new code path in tick 54 and **it has never executed on a
GPU**. Running the full cell first is how a large job gets wasted on a typo.

**Submitted 726211**: `DSNPROMPTS=2, DSLAYERS=8-11, DSMODE=band, DSFORM=decision,
DSREADOUT=refusal_proj, DSDEST=answer, DSPROJ=18`, 45-min walltime, on the five nodes *not* running
725172 (tick 55's spread-don't-concentrate policy).

**Desk-checked the failure modes I could check without a GPU, rather than waiting to find out:**
- **The `.pt` contract.** `readout_proj` calls `torch.load(...).float()` and dots it directly, which
  breaks if the artifact is a state-dict. Verified: it is a bare `torch.float32` tensor of shape
  `(4096,)` with **norm exactly 1.0**. So `.float()` is safe, and my `v / (v.norm()+1e-8)` is a
  harmless no-op rather than a bug.
- **Prefill-only is correct here.** `pc.AttentionKnockout`'s position guard is prefill-only — the trap
  that has bitten this project twice. It is *safe* for P3 specifically because this cell never decodes:
  `readout_proj` does a single `lm.model(**tok, output_hidden_states=True)` forward and reads the last
  prompt position. No `generate()`, so there is no timestep the hook can silently skip.
- **Destination arithmetic under the decision form.** With `DSDEST=answer`, `qdest = [seqlen-1]`, so
  `first_dest`, the random-source `pool` and the `all_query_edges` control all span everything before the
  decision token — which is what those controls are supposed to cover.

**A naming wrinkle recorded so nobody misreads a row later:** under `--prompt-form decision` the
destination named `answer` **is** the decision token (last position). That is only unambiguous because
`prompt_form` is written into every row alongside `destination` — the pair `(decision, answer)` is
well-defined, the word `answer` alone is not.

**Also caught a false alarm in my own checking.** My first `.pt` verification reported *file not found*
and looked like a real defect; it was my shell sitting in the repo root while the path is relative to
`doublespeak_causality/`. The script itself builds that path from `DC` and is unaffected. Re-ran from the
right directory before concluding anything — worth noting because a cwd artifact that looks like a
missing artifact is exactly the kind of thing that gets written up as a bug.

**725172** (clearharm low-α) at 39/50 items, ~30 min from done. **726211** still `PD (Resources)`.

### Tick 57 — 2026-08-06 — D1 RESOLVED BY MEASUREMENT: the three one-family caveats were artifacts
**Job 724931 finished (1000 rows, reconciles at 256 values / 0 mismatched).** It answers the question
tick 50's self-review raised, and the answer is clean:

| layer | `harmless` pop (`existing` IN-SAMPLE) | **`benign` pop (both out-of-sample)** |
|---|---|---|
| **9** | NEITHER | **NEITHER** |
| 16 / 18 | BOTH | **BOTH** |
| **21** | *existing only* | **BOTH** |
| **22** | *clearharm only* | **BOTH** |
| **30** | *clearharm only* | **BOTH** |

**The one-family-only verdicts do not survive a fair population**, so the qualifications they forced onto
**RP-01, BR-08 and TR-01 in tick 47 are withdrawn.** Two independent reasons to call them artifact:
1. they vanish the moment the induce population stops being `existing`'s own fit set — exactly what
   defect D1 predicted; and
2. on the confounded population the splits ran in **opposite directions** (L21 existing-only, L22 and L30
   clearharm-only). A genuine family difference would be **directional**; a coin-flip pattern is not.

**What is robust across all three populations tested** (`neutral`, `harmless`, `benign`): **L9 fails in
both families every time; L16/L18 pass in both families every time.** The headline never depended on the
population choice — which is the thing I most wanted to know after tick 50.

**Caveat I am attaching everywhere this is quoted:** the v3 `benign` condition is **not a clean floor** —
the model refuses **45 %** of it, so induce headroom is **0.55**, not the 1.000 `harmless` gave.
`benign`-based induce gains are **not comparable** to `harmless`-based ones and must never be pooled.
n = 20 per cell, so one induce item = 0.05.

**Bookkeeping done properly rather than leaving two contradictory sections in one report:** the old
"consequence for three published claims" section is now explicitly **SUPERSEDED**, retained only as the
record of what the `harmless` run showed, with the L9 row flagged as the one line that still stands.

Audit: **89 claims — VERIFIED 66, WITHDRAWN 8, SUPERSEDED 4, UNDERPOWERED 5, UNVERIFIED 3, PENDING 3**;
128 checks, 0 failures. UNDERPOWERED fell 7→5 as BR-08 and TR-01 returned to VERIFIED.

**A mistake I repeated:** I used an *unquoted* heredoc again (to interpolate the run dir) and the shell ate
every backticked token. The script's own assertion caught it and **nothing was written** — atomic failure,
which is why those asserts are there. Redone with a quoted heredoc passing the path via an env var.

**725172** (clearharm low-α) at 20/50 items, on track.

### Tick 56 — 2026-08-06 — the 2-per-node policy works; D1 run half-done and L9 survives out-of-sample
**The scheduling fix is confirmed.** Both jobs loaded promptly on n-802 and are generating — 724931 at
**280→360 rows in 28 min**, 725172 at 3 items. Two model-loading jobs on one node is fine; three is what
broke it (tick 55). No `s/it` blow-up this time.

**724931 (the D1 resolution) is half complete, and the first thing it shows is a measurement about the
population itself, which I am reporting rather than glossing:**

| induce population | base refusal | headroom for `induce_gain` | out-of-sample for BOTH families? |
|---|---|---|---|
| `neutral` (job 720463) | 0.750 | 0.25 | n/a — it is disguised-harmful, not benign |
| `harmless` (721957/722611) | **0.000** | **1.000** | ✗ — in-sample for `existing` (D1) |
| **`benign` v3 (this run)** | **0.450** | **0.550** | **✓ — the point of the fix** |

So the v3 `benign` condition is **not** a clean-floor population: the model refuses **45 %** of it. That
is worse headroom than I expected when I chose it last tick. It is still the right choice — it is the only
population that is out-of-sample for *both* families, and 0.55 of headroom is more than double what
`neutral` allowed — but **`benign`-based induce gains are not directly comparable to the `harmless`-based
ones**, and I will label them accordingly rather than pooling the two.

**Cells finished so far (out-of-sample induce, `base_harm` 0.85 / `base_benign` 0.45):**

| family | L9 | L16 | L18 | L21 |
|---|---|---|---|---|
| `existing` abl / ind | **+0.000 / −0.050** ✗ | +0.250 / +0.600 | +0.600 / +0.800 | **+0.200 / +0.800** ✓ |

**The L9 headline survives the correction.** D1's worry was that `existing`'s induce arm had been scored
in-sample, making it look artificially good. On a population it was *never* fit against, L9 still induces
**nothing** (−0.050) and still ablates to **+0.000**. A direction that fails both arms in-sample *and*
out-of-sample is not a refusal direction — this is now the third independent way L9 has failed.

`existing` L21 also still validates (+0.200/+0.800). **The decisive cell is `clearharm` L21**, which has
not run yet: if it now passes, the "one family only" caveat on RP-01 dissolves and was an artifact of my
own holdout; if it still fails, the caveat was real. Same question for L22/L30 (BR-08, TR-01). I will not
call those until the clearharm half lands.

**725172** (clearharm low-α calibration) is generating at ~5 min/item → ≈4.2 h for 50 items, inside its
8 h window.

### Tick 55 — 2026-08-06 — MEASURED the node-contention cost: 3 jobs/node = 16× slower weight loading
Last tick I *suspected* the three n-805 jobs were contending. This tick the `.err` bar proved it, and the
number is much worse than I guessed:

```
724931 (n-805, 3 jobs on the node):  Loading weights: 2%|▏ | 5/291 [07:32<5:13:42, 65s/it]
724551 (n-805, 1 job  on the node):  Loading weights: 79%|███▉| 230/291 [22:04<05:30, 5.42s/it]
```

**65 s/it against 5.4 s/it — a ~16× slowdown, projecting 5 h 13 m to load weights alone.** Same node,
same model, same code. `squeue` shows `R` for both; only the `.err` bar distinguishes them, and the
distinguishing feature is the **`s/it` rate**, not just whether the bar moves.

**This changes the scheduling policy, and it reverses a decision I made two ticks ago.** I had narrowed
`--nodelist` to four nodes to dodge the intermittent n-801/n-803 stalls. That narrowing is what
*concentrated* three jobs onto n-805 and caused this. Weighed properly:
- stall risk: intermittent, and **detectable in minutes** from `.err`;
- contention risk: **certain** once >2 jobs share a node, and costs 16×.

So the right policy is **spread across all six L40S nodes and cap concurrency at ~2 model-loading jobs**,
not restrict the nodelist. Recorded as a memory so it does not get re-litigated.

**Also: 725172 and 725173 were PREEMPTED** (`slurmstepd: … CANCELLED`) and requeued — `killable` is
preemptible and does preempt. That is not a bug to fix, but it compounds the contention problem: a job
that needs 5 h to *load* will almost certainly be preempted before it produces anything.

**Action taken:** cancelled **725173** (generated calibration) and **725178** (P4a) to bring concurrency
down to **two** — keeping the two highest-value runs: **724931** (the D1 resolution, which unblocks four
claims) and **725172** (clearharm low-α calibration). The two cancelled jobs are cheap to re-launch and
will go back in once these land.

**Nothing was lost:** both cancelled jobs had `raw=0` and had not begun generating.

### Tick 54 — 2026-08-06 — P3's decision-token cell IMPLEMENTED (the genuinely new destination)
The three scope decisions from tick 53 are **still open — no answer has come back, and I am not treating my
own recommendation as approval.** So this tick went to the one piece of P3 that needs no scope decision:
the cell I deliberately left raising NOT-IMPLEMENTED last tick.

**What the plan actually asked for.** §5 P3's missing destination is the **first-generated-token decision
point**. In the forced-choice form that position does not exist — "final prompt token" there is just the FC
answer index — so it needs a second prompt build *and* a different readout, because **there is no
concept/codeword label at the decision token** and `p_concept` is undefined.

Implemented, reusing what already existed rather than writing new machinery:
- **`build_decision`** — `apply_template(..., add_generation_prompt=True)` on the bare DS prompt; its last
  token *is* the decision point.
- **`readout_proj`** — the 6-line last-token residual projection, mirroring
  `phase_write_refusal_interaction.py:65-71`, which is the readout this project already uses.
- **The norm-matched random axis is computed for every cell**, not just the true one. §0.10 requires it:
  a knockout effect on the refusal axis means nothing unless a random axis of the same norm is unmoved.
  The reported quantity is the **specificity** `Δrefusal − Δrandom`, never the raw shift — a raw shift
  confounds *"this edge carries refusal"* with *"masking attention perturbs the residual stream at all"*.

**Three bugs I found in my own implementation while wiring it, each caught before it could run:**
1. **Two cells would have kept the forced-choice readout.** `rand_edge` and `all_query_edges` still called
   `readout(tok, cid, kid, …)`; under `--prompt-form decision` that scores a concept label that does not
   exist at that position. Fixed by routing **every** cell through one `emit()` helper, so a cell
   physically cannot be left on the wrong readout.
2. **The aggregator would have produced a silently EMPTY summary.** It keys on `r["valid"]` and
   `r["p_concept"]`; under decision form `valid` is `None` and `p_concept` is absent, so
   `if r["valid"]` filters everything out and writes an empty result with no error. Gave decision form
   its own aggregation branch that returns before reaching it.
3. **`valid` is set to `None`, not `True`.** The DS-reads-concept validity filter cannot be applied
   without a concept label, so marking these rows `True` would claim they passed a filter that never ran.

**Verified, not assumed:** both form/readout mismatch guards fire with explicit messages; the default
`--proj-layer hs18` maps to **decoder L17**, confirmed inside P7's cross-validated set, and its `.pt`
exists; and the specificity contrast was unit-tested on synthetic data — it returns `−0.981` CI
`[−1.198, −0.766]` (excludes 0) for a real refusal-axis effect and `−0.008` CI `[−0.029, +0.013]`
(includes 0) when both axes move together, which is exactly the generic-damage case the control exists to
reject.

Wrapper flags added with a dash→comma expansion and a character-class reject (`bad!val` → REJECTED).

**Not launched yet, deliberately:** four jobs are already queued/running and three are on n-805, which is
plausibly why their weight loads are slow (three processes each streaming ~16 GB of shards). Adding a
fifth would make that worse for jobs I care about more. The smoke is staged for when the queue drains.

**Job state:** 724931 (26 min), 725172 (26 min), 725173 (17 min) all running on n-805 with **empty**
`.err` — note that is *not* the n-801 stall signature (`0/291`); the loader has not begun emitting.
725178 (P4a) still pending.

### Tick 53 — 2026-08-06 — resized a calibration that could not finish; launched P4a; ⚠ THREE SCOPE DECISIONS FOR OMER
**Caught a run that was going to die at walltime with nothing usable.** 724551 had 11 rows after 70 min of
*generation* — **6.41 min/item**, because the low-α grid is 6 alphas = **20 arms/item** at 220 new tokens,
4× the α=0.25 run. Projected **13.6 h against 4.2 h remaining**; 724930 was on the same trajectory. Neither
would have produced a complete calibration, and a walltime kill leaves no `summary.json` — exactly the
PROVISIONAL mess that already cost a tick with job 716014.

**Resized rather than extended.** `--n` truncates **per split** (`phase_behav_refusal.py:169`), so
`DSN=25` gives a balanced 25 train + 25 test = **50 items** → ≈5.3 h inside an 8 h window. Resubmitted as
**725172 / 725173**. This is defensible because **calibration is dose SELECTION, not the confirmatory
experiment**: at n=50 the SE of a proportion near 0.3 is 0.065, and the doses we must separate were 0.402
and 0.591 against a [0.20, 0.40] band — far outside that noise. The confirmatory run at the chosen α uses
full n, as P8 already did. I did **not** cut `DSMAXNEW` below 220, which would have been the cheaper lever
but would have broken comparability with the α=0.25 result.

**P4a LAUNCHED with zero new analysis code (job 725178).** The readiness agent found that
`next7_attention_retrieval.py` already computes exactly the per-head query→demo attention mass P4a needs —
it had simply never been pointed at a ClearHarm bench. **The project's only induction-head evidence is a
band-mean 3.508× ratio on n = 12 of the old carrot/bomb pair**; this replaces it with **n = 44 ClearHarm**.
Two things were needed first:
- **A latent crash fixed.** `36_pair_attention.source_positions:56` called `dc.find_word_occurrences`
  (strict id matching) with **no `try/except`**, so any ClearHarm codeword whose in-context tokenization
  differs from its standalone form would raise and kill the whole sweep mid-run. Applied the *same*
  fallback `pair_common.resolve_positions:70-82` already uses. It runs only where the strict finder
  already raised, so no existing caller changes behaviour.
- A wrapper (`slurm/run_p4a_identify.sh`), since GPU work goes through sbatch. All six flags verified
  against the script's own `--help` before submitting.

---

### ⚠️ THREE SCOPE DECISIONS I need from Omer — I am not deciding these unilaterally

The readiness agents found that **P4b, P5 and P9 cannot be run as the plan literally specifies.** Per the
plan's "never skip a stage without telling Omer", here they are:

| phase | finding | what I'd propose |
|---|---|---|
| **P4b** — full head sweep | **≈440 GPU-h** as specified, *and* contains a **structural impossibility**: the K/V cells cannot be patched per-head as written under **GQA** (Llama-3.1 shares K/V across query-head groups). | Drop the K/V-per-head cells as ill-posed and say so in the paper; run z/pattern/head-result only, at the corrected positions. Needs your call because it narrows a pre-registered design. |
| **P5** — head→MLP path matrix | **34–77 GPU-h per metric** for exact patching. The plan already anticipates this and says AtP may rank but **never substitutes for exact patching in a claim**. | AtP-rank everything (explicitly *not* a claim), exact-patch the top-k (the claim). I need your k. |
| **P9** — GCG Gate 7 | **0 of 16 arms launchable**, though 7 have their inputs on disk. The wrapper cannot express a refusal-direction objective, cannot vary the seed, the evaluator hardcodes 3 Qwen arms — and **arm 7's frozen direction is one P7 just failed**. | Fix the wrapper/evaluator (small), drop arm 7 or re-freeze it on a P7-validated layer. |

**My recommendation if you want one answer:** do P5's decomposition (it yields the novel circuit figure),
take the narrowed P4b, and defer P9 — its arm 7 is now known to rest on an invalid direction, and GCG has
been a repeatedly-negative line in this project.

### Tick 52 — 2026-08-06 — two n-801 stalls killed and resubmitted; the early-stall diagnostic, written down
**All three jobs looked identical from `squeue` and from stdout** — every one sat at `GPU ok` with
`raw.jsonl` empty. Three hypotheses fit that: slow load, hung load, or slow generation. `raw.jsonl` cannot
distinguish them, because the α-sweep writes a row only after **all 20 arms** of an item finish.

**The signal that does distinguish them is the HuggingFace weight-loading progress bar, which goes to
`.err`, not `.out`:**

| job | node | `.err` tail | verdict |
|---|---|---|---|
| 724551 | n-805 | `Loading weights: 79%\|███▉ \| 230/291 [22:04<05:30, 5.42s/it]` | **slow but PROGRESSING** — left alone |
| 724552 | n-801 | `Loading weights: 0%\| \| 0/291 [00:00<?, ?it/s]` after **1 h 04 m** | **HUNG** |
| 724778 | n-801 | no progress bar emitted at all in 24 min | **HUNG** |

**This is the diagnostic to use every time from now on**, and it is worth stating plainly because I have now
had to make this call three times: `tail -c 300 logs/*_<jobid>.err | tr '\\r' '\\n'`. A **slow** node prints
a moving bar with a per-shard rate; a **stalled** node prints `0/291` and stays there, or prints nothing.
`squeue` shows `R` in both cases and stdout is identical in both cases — neither can tell you anything.

**Cancelled 724552 and 724778, resubmitted off n-801** as 724930 / 724931 with
`--nodelist=n-802,n-804,n-805,t-806` (n-803 also excluded — it stalled on job 720724 earlier today with
`_cgroup_procs_check` failures on teardown). Empty run dirs removed.

**Honest note on n-801: it is intermittent, not simply bad.** Earlier today 720463 and 720725 both ran to
completion on it. So the fix is not to blacklist it permanently — it is 1/6 of our L40S capacity — but to
**detect the stall in minutes instead of hours** using the `.err` bar. I lost roughly an hour of 724552's
wall clock to not checking that file first.

**724551 (clearharm low-α) is fine on n-805** and was deliberately NOT cancelled: at 230/291 shards it was
demonstrably making progress, and killing a healthy 80-minute-old job to chase a faster node would have
cost more than it saved.

### Tick 51 — 2026-08-06 — D1 RESOLVED by design, not by caveat: a benign population out-of-sample for both
D1 (the protocol asymmetry) blocked four claims, so it was the right thing to fix rather than merely
document. The reviewer's proposed fix was to refit `existing` on `HARMLESS_FIT` — a whole extra family and
a GPU refit. **There is a cheaper and strictly better fix, and the data was already on disk.**

`HARMLESS_INSTRUCTIONS` can never be clean for both families: it is `existing`'s fit set. But the v3 split
carries a **`benign` condition on all 324 examples** — *"demos use `codeword` in its ordinary benign
meaning; codeword query, no harmful binding"* (`DATASET_AND_SPLIT_CONTRACT.md:44`). **That population is in
NEITHER fit** — `existing` was fit on carrot/bomb + harmless, `clearharm` on ClearHarm-direct + harmless.
So it makes both families out-of-sample *simultaneously*, and at the eval split's full n rather than 10.

Implemented as `--induce-eval benign`:
- `split_to_behavioral.py` now emits `benign_prompt`; regenerated into **`data/behavioral_v3b/`** (a NEW
  directory — the existing overwrite guard would have refused, and clobbering v1 is a mistake I have
  already made once in this sprint).
- `conditions_for` returns a 4-tuple; every unpack site updated and compile-checked.
- Dry-run confirms the metadata now reads **`induce_eval: benign`,
  `existing_family_induce_is_in_sample: False`** — the asymmetry is gone by construction, and
  `n_harmless_fit` is back to the full 20 because the refit no longer has to give up half its negatives.

**Launched job 724778** on exactly the layers whose family-split verdicts D1 confounded:
**L9** (the headline), **L16/L18** (validated in both), **L21** (RP-01), **L22** (BR-08), **L30** (TR-01).
This is the run that decides whether those three qualifications were real or an artifact of my own
holdout.

**A mistake I made and caught before it burned a job.** I first submitted with
`DSLAYERSET=9-16-18-21-22-30`, but the wrapper treats an unrecognised value as a literal comma list, so
`--layers` would have received `"9-16-18-21-22-30"` and died in `int()`. Cancelled 724775, added a
dash→comma expansion *inside* the script (dashes are required because `--export` truncates comma values),
plus a `*[!0-9,]*` reject for anything that is not a list of integers. Tested all five branches:
`9-16-18-21-22-30` → `9,16,18,21,22,30`, `headline` and `all` unchanged, a bare comma list still accepted,
and `bogus5x` **rejected** rather than silently passed through.

**Low-α jobs healthy:** 724551 (51 min), 724552 (36 min), both still in generation.

### Tick 50 — 2026-08-06 — the self-review found 4 HIGH defects in MY OWN work; three claims corrected
All 5 agents returned. The adversarial self-review earned its cost: **4 HIGH defects, three of them in
claims I wrote in the last two ticks.** Every one verified myself before acting.

**D1 [HIGH] — the protocol asymmetry, and the most consequential finding.** My `--harmless-holdout` fix
protects the `clearharm` refit from being scored on its own fit set. **It does nothing for `existing`.**
Those directions shipped from `outputs/refusal_alllayers/`, and I confirmed **every one of their 32 `.json`
files records `n_harmless: 20`** with `build_refusal_direction_llama.py` iterating the whole list — so
**`HARMLESS_EVAL` ⊂ the `existing` fit set, item for item.** `existing` is induce-tested **in-sample**;
`clearharm` is tested **out-of-sample**. Adding `α·v` to an in-sample negative is the easiest possible
induce test.
- **The 12/32 vs 15/32 counts are NOT commensurable** and must not be compared as though they were.
- **Every one-family-only verdict is confounded** — including the L21/L22/L30 splits I used in tick 47–48
  to qualify RP-01, BR-08 and TR-01. Those stand as *"not established in both families"* but are **not**
  evidence the direction is worse in the failing family.
- **The L9 headline gets STRONGER, not weaker.** `existing` had the *easier* in-sample test at L9 and still
  induced **+0.000**. A direction that cannot raise refusal on the very prompts it was fit against is not a
  refusal direction.
Documented as a prominent "PROTOCOL ASYMMETRY" block in the P7 report and in the harness docstring. The
clean fix — a third family, `existing` refit on `HARMLESS_FIT` only — is **not yet run**.

**D14 [HIGH] — RP-04 was wrong and I have withdrawn the superlative.** I claimed L16's AUC 0.888 was
"HIGHER" than L21's 0.874 and that "the result got stronger". That was selection: 0.888 is the **argmax
over 11 correlated layers** compared against a fixed one, with no paired test, and the 0.014 gap sits
inside the script's own measured noise (4 adjacent layers span 0.007; the 5-fold sd at L21 is 0.055).
**Measured it properly** with a paired **item**-bootstrap that recomputes *both* AUCs on each resample
(AUC is not a mean, so `stats.paired_bootstrap_ci` does not apply): **ΔAUC = +0.0139, 95 % CI
[−0.0148, +0.0446] — straddles zero.** The supportable claim is *"L16 is at least as good as L21 and is
validated in both families"* — which is still exactly what retires RP-01's caveat.

**D15 [HIGH] — terminology collision.** I was using "cross-validated" for two different things twenty lines
apart: *validated in both direction families* and *k-fold CV*. **There is no cross-validated 0.888** — the
5-fold runs at one layer only. Renamed the variable `cv` → `p7both` with a comment, and the audit note now
states the distinction.

**D12 [HIGH] — my own validator guard was near-vacuous.** The refval branch compared two argparse strings
and touched no data, so it was structurally blind to the contamination *I* had just introduced on the
harmless side. It now checks fit/eval-half disjointness from the recorded sizes, warns on
`induce_eval='neutral'`, refuses runs that mix induce populations, and surfaces the D1 asymmetry.
Negative-controlled both ways: a defeated holdout **FAILs**, proper disjoint halves **pass**.

**A real bug the new guard immediately caught (D3):** `plan.n_harmless_fit` recorded
`len(HARMLESS_INSTRUCTIONS)` = 20 even when the holdout meant the fit actually saw **10** — the committed
metadata misdescribed the run. Fixed to record `n_harmless_total` / `n_harmless_fit` /
`n_harmless_induce_eval` / `induce_eval` / `harmless_holdout`. Historical runs are treated as **legacy
metadata → warn**, not FAIL, so a metadata gap is never reported as a data defect.

Audit: **88 claims, 126 checks, 0 failures.** All refval dirs still reconcile (3050 values, 0 mismatched).
**Jobs healthy:** 724551 (32 min), 724552 (17 min).

### Tick 49 — 2026-08-06 — P3 started: destination coverage + the eager assertion the plan demanded
**Both low-α jobs running** (724551 clearharm on n-805, 724552 generated on n-801). **Grid verified to have
arrived intact** — the log shows `alphas='0,0.05,0.1,0.15,0.2,0.25'`, so the `DSALPHASET` preset defeats the
`--export` comma-truncation bug as designed. That is worth checking rather than assuming: a silently
truncated grid would have burned 6 GPU-hours producing a single-α run mislabelled as a sweep.

**Loop note:** cron `86decf2e` is still live with this exact prompt, so I did **not** create a second one.

**Fanned out 5 agents** (disjoint files) on the four phases the plan still has unstarted — P3, P4, P5, P9 —
plus an adversarial review of this session's own code. P3 returned first.

**P3 is ~85 % already built**, and the assessment found one thing that matters more than the missing
feature: **the plan requires "eager attention, asserted" and the assertion was ABSENT from the knockout
path.** `phase4_edge_knockout.py` *passes* `attn_implementation="eager"` but never verified it stuck.
Under SDPA/flash the softmax@V product is fused, `AttentionKnockout` silently no-ops, and the run would
report a clean null that means nothing. **Now asserted at load** (same check `phase4b_pattern.py:92` already
used) and the resolved implementation is printed.

**Implemented the destination selector.** The destination set was hard-coded as the *fused*
`query_pos + [seqlen-1]`, so a query-codeword effect and an answer-position effect could not be told apart.
`--destinations` now selects them and `destination` is emitted per row so the aggregator can group on it.
**Unit-tested that the default is byte-identical to the historical set** (`[41,42,96]` both ways) — every
previously-published edge-knockout number is unchanged unless a flag is passed. Unknown values are rejected
rather than silently ignored.

**One correction to the assessment, worth recording:** it proposed a `final_prompt` destination, but in the
forced-choice form that is *the same index* as `answer`. I did not add it — offering an alias as a separate
cell would have produced a duplicate arm masquerading as new coverage.

**⚠️ The genuinely new P3 cell is NOT done, and I made it fail loudly rather than pretend.**
`--prompt-form decision` / `--readout refusal_proj` are declared but not wired, so they now **exit with a
NOT-IMPLEMENTED error**. Accepting the flag and silently running the forced-choice cell would produce a
plausible number for an experiment that never ran — the exact failure class this project has already
retracted twice (prefill-only ablations; silent hook no-ops). Verified the guard fires.

**A cross-phase constraint I am carrying into that cell:** at the decision token there is no
concept/codeword label, so the readout must be the refusal projection — and **P7 §4c just established that
only decoder layers 13–20, 24, 28, 29 carry a validated refusal axis** (hs row h = decoder layer h−1). The
`--proj-layer` default is set to **hs18 = decoder L17**, inside that set, and the help text says explicitly
not to point it at an unvalidated layer. Projecting on a direction that neither ablates nor induces refusal
is not a refusal measurement — that is the same error BR-11 was just downgraded for.

**Still pending:** P4/P5/P9 readiness and the self-review (4 agents in flight).

### Tick 48 — 2026-08-06 — SLURM back; low-α submitted; RP-01's caveat RESOLVED (and it got stronger)
**SLURM controller is back** (26 nodes up in `killable`). Submitted the staged v3-native low-α
re-calibration immediately: **724551** (clearharm) and **724552** (generated), `DSALPHASET=low` →
grid `0,0.05,0.1,0.15,0.2,0.25`. Both queued.

**Then closed two audit items with zero GPU, because the data was already committed.** The `refproj`
rows carry **all 32 layers** per condition, so the layer sweep RP-03 needed was computable from disk.
Added `--sweep` to `analyze_rep_predicts_behavior.py`.

**Indexing, verified before trusting anything:** `refproj` keys are `hidden_states` rows **1..32** and
`hidden_states[k+1]` is post-block-`k`, so **hs h = decoder layer h−1** (hs22 = the historical "L21").
Getting this backwards would have silently mismapped every P7 comparison, so I checked it against
`phase_refusal_projection.py:44` rather than assuming.

**RP-03 UNVERIFIED → VERIFIED (the stability half).** Decoder L17–L31 span **AUC 0.844–0.884**, inside
the quoted 0.84–0.89. **20/32** layers Holm-significant over the 32-layer family.

**RP-01's caveat is now RESOLVED, not merely flagged — and the result improved.** Tick 47 had to record
that L21, the published readout, validates in only one direction family. But **all 11 P7-cross-validated
layers are Holm-significant here**, and the best of them beats L21:

| decoder layer | 13 | 14 | 15 | **16** | 17 | **18** | 19 | 20 | 24 | 28 | 29 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AUC | 0.773 | 0.819 | 0.876 | **0.888** | 0.884 | **0.882** | 0.881 | 0.879 | 0.857 | 0.856 | 0.850 |

**L16 gives AUC 0.888 vs L21's 0.874 — higher, and validated in BOTH families.** L18 (0.882) is the
direction every behavioral arm in the project ablates. Recommended re-anchoring the paper's readout to
L16 or L18; logged as new claim **RP-04**. The finding does not depend on the one family-specific layer.

**⚠️ But the CV half does NOT reproduce, and I am not papering over it.** The quoted *"5-fold CV AUC =
0.887 ± 0.106"* is unrecoverable — the original fold assignment was never recorded. A deterministic
stratified 5-fold (seed 0) gives **0.869 ± 0.055** at L21. That is the number to cite. I also noted in
both the report and the audit that CV is near-meaningless here: the "classifier" is a single raw feature
with no fitted parameters, so CV measures subsample stability, not generalization. Quoting it as evidence
against "in-sample optimism" was never quite right.

**curated unchanged** — uniform null, 0/32 Holm-significant, AUC 0.364–0.605.

Audit: **88 claims — VERIFIED 63, WITHDRAWN 8, SUPERSEDED 4, UNDERPOWERED 7, UNVERIFIED 3, PENDING 3**;
125 checks, 0 failures. Negative-controlled again (`CHECK-FAIL RP-04` on a perturbed expectation).

### Tick 47 — 2026-08-06 — propagated the 32-layer verdict into the claim audit; ⚠ SLURM still down
**SLURM controller still unreachable** (checked at 07:39 and again at end of tick; `sinfo` and `squeue`
both fail). Queue empty, nothing to cancel. The low-α re-calibration stays staged and ready. CPU tick.

**Propagated §4c's consequences into `CLAIM_AUDIT_TABLE.md`** — the point of that table is that a finding
which qualifies a published claim actually *reaches* the claim, so this was the work worth doing:

| claim | layer | was | now |
|---|---|---|---|
| **BR-08** depth-localization | L22 | PENDING | **UNDERPOWERED** — validates in the ClearHarm refit only; the shipped `existing` L22 induces **+0.000**. Blocked from the abstract unless the family is named (or L16 quoted, which is valid in both). |
| **RP-01** rep→behavior AUC 0.874 | L21 | VERIFIED, blocked on a smoke | **still VERIFIED, block rewritten** — validates in `existing` only; the ClearHarm refit at L21 fails induce outright. The AUC is real; the *axis* is not cross-validated. |
| **TR-01** trajectory / decision point | L30 | PENDING | **UNDERPOWERED** — ClearHarm-only, and by exactly **one induce item**. |
| **BR-11** refusal-suppression signature | hs9 (~L8) | PENDING | **UNDERPOWERED** — see below. |

**BR-11 is the one that actually changes a story, and it is worth stating plainly.** The claim places the
onset of refusal suppression at **hs9 (~L8)**. But **L0–L12 have no valid refusal axis in *either*
family** — those directions neither ablate nor induce refusal. **A projection onto a direction that does
neither is not a refusal measurement**, so the *onset* half of that claim is not supportable as written.
The *depth-growth* half (L13 upward) is unaffected and stands. This is not a numerical error in the
original run — the projections are what they are — it is that the quantity was named "refusal" at layers
where nothing licenses that name.

**Added claim `P7-32`** recording the sweep itself (11/32 valid in both; L0–L12 fail in both without
exception; per-family 12/32 and 15/32), with three machine checks against the committed summary and the
induce-n=10 caveat attached so a `+0.100` is never read as more than the single item it is.

Audit now: **87 claims — VERIFIED 61, WITHDRAWN 8, SUPERSEDED 4, UNDERPOWERED 7, UNVERIFIED 4, PENDING 3**;
121 numeric checks, 0 failures, 38 dirs cited, 0 missing. **22 of 87 are abstract-eligible.** PENDING fell
6→3 and UNDERPOWERED rose 4→7 — that migration *is* the tick's output: three published claims moved from
"unknown" to "known and qualified". Negative-controlled again (perturbing `n_valid` to 99 produces
`CHECK-FAIL P7-32`, then restored).

**A process note on my own error:** I first ran the edits behind `cd doublespeak_causality && python3 …`
from a shell already in that directory. The `cd` failed, `&&` short-circuited, and **only the trailing
`py_compile` ran — which printed `COMPILE OK` on the unmodified file.** I nearly took that as success.
Verified by grepping for the new text before re-running, which is the check that caught it.

### Tick 46 — 2026-08-06 — P7 COMPLETE at all 32 layers; ⚠ SLURM CONTROLLER IS DOWN (cluster-wide)
**Job 722611 finished: 3870 rows, all 32 layers × 2 families.** Reconciled by the validator I taught the
schema last tick — **1348 values recomputed, 0 mismatched**, 64 cells, 0 dups, `empty_max` 0.0. Written up
as **§4c** of `reports/P7_REFUSAL_DIRECTION_VALIDATION.md`.

| set | layers |
|---|---|
| **valid in BOTH families** | **13–20, 24, 28, 29** (n=11) |
| `existing` only | 21 |
| `clearharm` only | 22, 23, 27, 30 |
| **invalid in BOTH** | **0–12**, 25, 26, 31 (n=16) |

**The depth story is a contiguous block, which is what makes it credible.** L0–L12 fail in **both**
families without exception; L13–L20 pass in **both** without exception. Two independently-built direction
families draw the same boundary in the same place, so this is not a threshold artifact of one fit.

**⚠️ This forced two corrections to my own earlier write-up:**
1. §4 said *"refusal becomes linearly available at **L16**"*. That was an artifact of the headline layer
   set containing **no layer between 9 and 16**. The true boundary is **L13**. Corrected in place, with a
   note explaining why the earlier number was wrong.
2. Of the layers carrying published claims, **only L18 is in the cross-validated set.** L21 (rep→behavior
   AUC), L22 (depth), L30 (trajectory) each validate in **exactly one family**, and in each case the
   failing side is a *hard* induce zero, not a near miss. Each of those three results must name the family
   it validates in, or be re-read at a layer inside 13–20.

**A limitation I added rather than let pass:** induce n is **10**, not 20 (the held-out harmless half), so
one induce item = 0.10 — and L22/L30 clear the bar on `clearharm` by exactly **+0.100, i.e. a single item**.
They are *technically* valid but must not be described as strongly validated. A larger benign eval set is
the cheap fix.

**⚠️ SLURM CONTROLLER UNREACHABLE — cluster-wide, not our configuration.** `sbatch` and `sinfo` both fail
with `Unable to contact slurm controller (connect failure)`. The queue is empty (everything we had
finished). There is nothing to cancel and nothing to re-tune, so the 30-minute rule does not apply here —
it governs jobs that sit PENDING, not a controller that is down. **Retry next tick.**

**Prepared and ready to submit the moment the controller returns:** the v3-native low-α re-calibration that
P8 §7 named as the clean follow-up (α = 0.25 qualifies on *neither* v3 cohort). Added a **`DSALPHASET`
preset** to `run_behav_refusal.sh` — same idiom as `DSLAYERSET` — because the grid is a comma-list and
therefore can never come through `--export`. `DSALPHASET=low` → `0,0.05,0.1,0.15,0.2,0.25`. Verified: the
preset resolves correctly, an unknown value exits 1, and the ordering still lets an explicit single
`DSALPHAS` override it. `bash -n` clean.

**A repeat of my own tcsh mistake, caught and fixed.** I built §4c with an *unquoted* heredoc, so the shell
ate every backticked token (`722611` → empty). Restored the file from `HEAD` and redid it with a quoted
`<<'PYEOF'`. This is the second time backticks have bitten in this session; the memory rule I wrote covers
`git commit -m` but I had not applied it to heredocs.

### Tick 45 — 2026-08-06 — P8 COMPLETE (n=242). No interaction — and the pre-registered split just saved us
**Job 721956 finished (127 rows).** Both v3 cohorts are in, so P8 is done: clearharm n=127 + generated
n=115 = **n = 242**, at the de-saturated α = 0.25. Report: **`reports/P8_INTERACTION_V3.md`**.
Combined ids verified disjoint before pooling (242 rows / 242 distinct ids; splits 162/80, matching the
v3 design). Every number in the report re-verified against the JSONs, including the `I_max` identity.

| split | n | `I_max` | **`Î`** | 95 % CI | perm p |
|---|---|---|---|---|---|
| train | 162 | +0.463 | **−0.124** | [−0.210, **−0.037**] | **0.0098** |
| **test (held out)** | 80 | +0.588 | **+0.088** | [−0.025, +0.212] | 0.214 |
| **pooled** | **242** | +0.504 | **−0.054** | [−0.124, +0.017] | **0.172** |

**THE NEAR-MISS, and I want this on the record.** Had I looked only at the train split — n=162, CI
excluding zero, **p = 0.0098** — the write-up would have read *"Doublespeak and refusal-ablation combine
sub-additively, consistent with a shared refusal bottleneck."* **That is verbatim the claim P8.0 made and
P8.1 withdrew.** The held-out test split does not merely fail to confirm it, it **reverses the sign**. The
pre-registration is the only thing that stopped this project making the same error twice, and §3 of the
report says so explicitly rather than quietly reporting the pooled null.

**And the disagreement is explained, not hand-waved.** The split with the lower ceiling has the more
negative `Î`, in **both** cohorts independently:

| dataset | split | `I_max` | sat. by one factor | `Î` |
|---|---|---|---|---|
| clearharm v3 | train / test | +0.447 / +0.619 | 57.6 % / 50.0 % | **−0.118 / +0.095** |
| generated v3 | train / test | +0.481 / +0.553 | 72.7 % / 65.8 % | **−0.130 / +0.079** |

Across the 4 independent cells the **train/test separation is perfect** — both low-ceiling cells negative,
both high-ceiling cells positive. Spearman(`I_max`, `Î`) = **+0.800**, short of +1.000 only because the two
*train* cells swap rank between themselves. **This is P8.1's saturation signature on a third independent
axis:** `Î` tracks `I_max` across α (ρ=+0.991), across cohorts, and now across the split. `I_max` depends
only on the marginal cells, so a real mechanism has no reason to track it.

**The null has teeth.** Refusal-ablation beats its count-matched random control by **ΔASR +0.194**
(McNemar 48/1, p < 10⁻¹²) — ~10× the judge noise floor. Both factors move behaviour; they just **add**.

**Directly answering the "stack interventions to raise ASR" question — the cohorts answer oppositely:**
- clearharm: DS net-**positive** (+9.5 pp); both = 0.449 is the best cell, +4.7 pp over ablation alone.
- generated: DS net-**negative** (−9.6 pp); ablation *alone* (0.591) beats the combination (0.435) by
  **15.6 pp**.
So **"refusal-dir down + Doublespeak" does not reliably stack.** With a zero interaction term the
combination buys the *sum* at best, never a synergy — and where Doublespeak dilutes the concept it buys
*less* than the single best lever.

**Limitation recorded, not buried:** α = 0.25 qualifies on **neither** v3 cohort
(`ASR(0,1)` = 0.402 vs the [0.20, 0.40] band — outside by 0.002 — and 0.591). The dose came from clearharm
**v1** and does not transfer. `I_max` ≈ +0.50 on both, so the interaction estimate is not ceiling-limited
and stands, but those ASR levels must not be quoted as a chosen operating point; a v3-native low-α
calibration is the clean follow-up.

**Still running:** 722611, the full 32-layer refusal validation, at 3450 rows.

### Tick 44 — 2026-08-06 — closed the P7 reconciliation gap; 1702 values recomputed, 0 mismatched
Both GPU jobs healthy (721956 at 111/127; 722611 at 1950 rows), so this tick went to the **stated
prerequisite** the claim audit flagged: *"`validate_all_outputs.py` does not recognise the `refval` row
schema, so no P7 number has ever been machine-recomputed from its rows — teaching it that schema is a
prerequisite for calling any P7 number VERIFIED."* That is now done.

**`validate_experiment_coverage.py`** — added `check_refval` + a detector keyed on `arm`+`refused`+`item`
(`family`/`layer` are `None` on baseline rows so they cannot discriminate). It checks arm completeness per
(family, layer), duplicate `(family,layer,arm,item)`, non-bool `refused`, and **pairs each arm only against
its own baseline** — because the induce arm may legitimately be *shorter* than the ablate arm under
`--induce-eval harmless`. Both P7 dirs now report `ok`, and the detail line makes the design visible:
720463 `base_b=20` (neutral) vs 721957 `base_b=10` (harmless holdout).

**`validate_all_outputs.py`** — added `expect_refval`, recomputing every rate, gain, specificity, ceiling,
empty-rate and `by_family` roll-up from `raw.jsonl`. Also special-cased the split-disjointness step:
refval rows carry no `split` column (fit/eval separation is enforced upstream and recorded in
`summary['plan']`), so the generic check would have compared `None` against `None` and emitted a
meaningless "only 0 split(s)" warning. Replaced with a **`fit_split == eval_split` guard**, which is the
failure that would actually matter — it would mean the ClearHarm refit was evaluated on its own fit items.

**Result: all completed refval dirs reconcile — 1702 summary values recomputed, 0 mismatched**, including
the 32-layer smoke (1284 values). The only FAIL in the sweep is 722611, which has no `summary.json` yet
because it is still running.

**A bug in my own recomputer, caught by not trusting the first red result.** My first pass reported 4
`summary!=raw` FAILs on 720463 and I nearly wrote them up as a defect in the run. They were mine: the
harness distinguishes two verdicts that I had conflated —
`both_gains_positive` = raw gains > 0, whereas `valid` = raw gains > 0 **and** both specificities > 0
(`validate_refusal_directions.py:560-562`). The two coincide only when the random controls are exactly
0.000, which is true in 721957 and **not** in 720463 — which is precisely why 721957 passed and 720463
"failed". Fixed, and the distinction is now commented at the site so it does not get re-conflated.

**Negative-controlled, because a validator that cannot fail is worse than none.** Corrupting a rate,
corrupting a roll-up, and flipping a verdict are each caught individually; forcing
`eval_split = fit_split` fires the new guard. Verified, then the scratch copy was deleted.

Claim audit regenerated: BR-10's "SECOND GAP" note now records the closure. 86 claims, 118 checks, 0
failures.

### Tick 43b — 2026-08-06 — P8 CORE result, generated v3 cohort: no interaction, and the combination HURTS
**Job 720725 finished (115 rows, DONE).** Analysed with `analyze_alpha_calibration.py` (which rebinds the
2×2 cells onto the α-suffixed arm names; `analyze_interaction_2x2.py` has its run dirs hardcoded and no
`--run` flag, so it is the wrong tool here).

| cell | arm | ASR |
|---|---|---|
| (0,0) | direct | 0.452 |
| (1,0) | doublespeak alone | **0.357** |
| (0,1) | refusal-ablation alone | **0.591** |
| (1,1) | both | 0.435 |

**Î = −0.061, 95 % CI [−0.165, +0.043], sign-flip p = 0.338**; graded score Î = −0.053, CI
[−0.147, +0.038], p = 0.273. `I_max` = **+0.504**, so this is **not** ceiling-limited — a genuine null,
not a saturation artifact. `D_i` = {−2: 1, −1: 20, **0: 79**, +1: 15, +2: 0}.

**This corroborates P8.1 on a second, independent cohort.** clearharm gave Î = −0.023 (p = 0.860) at
n=86; generated v3 gives Î = −0.061 (p = 0.338) at n=115. Two cohorts, both null, both de-saturated.
The "shared refusal bottleneck" reading stays withdrawn.

**The manipulation is real, so this is a null with teeth.** Refusal-ablation beats its own
count-matched random control by **ΔASR = +0.139, McNemar p = 0.0000**. The intervention demonstrably
works; it just does not interact with Doublespeak.

**Two findings that bear directly on Omer's "combine interventions to raise ASR" question:**
1. **Doublespeak alone is net-NEGATIVE on this cohort** — 0.357 vs 0.452 for the plain direct request.
   That is the known concept-dilution effect, now measured on v3.
2. **Combining is WORSE than refusal-ablation alone** — (1,1) = 0.435 < (0,1) = **0.591**. On this
   cohort the best single lever is refusal-ablation by itself, and adding Doublespeak *costs* 15.6 pp.
   So "refusal-dir down + doublespeak" does **not** stack; it is an evaluated negative for raising ASR.

**A dose caveat, recorded not buried.** `ASR(direct_refabl)` = 0.591 is **outside** the pre-registered
[0.20, 0.40] band, so α = 0.25 does **not** qualify as the operating point for *this* cohort — the dose
was calibrated on clearharm and does not transfer (the same failure curated showed). The interaction
estimate is still readable because `I_max` = +0.504 is far from the ceiling, but the cohort would need its
own lower-α calibration before its ASR levels are quoted as a chosen operating point.

Written to `outputs/p8_generated_v3.json`. The full P8 report waits on 721956 (clearharm v3) so both
cohorts land together.

### Tick 43 — 2026-08-06 — the corrected induce arm lands: L9 fails BOTH arms in BOTH families
**Job 721957 finished in ~20 min (630 rows) and the fix is confirmed in its own log:**
```
harmless set: 20 total -> fit/alpha n=10, induce-eval n=10, disjoint=True
baselines: harmful refusal=0.950  induce-base (harmless) refusal=0.000  [headroom = 1.000]
```
**The induce base went 0.750 → 0.000.** The arm is now a real test instead of one capped at +0.25.

| family | L9 | L16 | L18 | L22 | L28 |
|---|---|---|---|---|---|
| `existing` ablate / **induce** | −0.050 / **+0.000** ✗✗ | +0.450 / **+1.000** | +0.600 / **+1.000** | +0.250 / **+0.000** ✗ | +0.250 / +0.100 |
| `clearharm` ablate / **induce** | −0.100 / **+0.000** ✗✗ | +0.300 / +0.900 | +0.900 / +0.800 | +0.350 / +0.100 | +0.300 / +0.400 |

**L9 is the only layer invalid in both families, and it now fails on BOTH arms.** With a full +1.000 of
headroom, adding the L9 direction to benign prompts induces **zero** refusal, while the same operation at
L16/L18 flips 8–10 of 10 benign prompts into refusals. That is strictly stronger than the ablate result
alone: L9 is not merely *unnecessary* for refusal, it is *insufficient* to produce it.

**Controls are clean** — `induce_gain_rand` = 0.000 in **all ten** cells, `ablate_gain_rand` ∈ {0.00, 0.05},
`empty_induced` = 0.0 everywhere. Nothing here is generic perturbation damage.

**A caveat I am flagging rather than averaging away.** The two families **disagree at L22**: the shipped
`existing` L22 direction passes ablate (+0.250) but induces **nothing** (+0.000), so it is not a validated
refusal axis; the ClearHarm refit passes both but weakly (+0.100 = 1 of 10). **The published depth result
leans on "L22 significant", so that claim rests on a direction validated in only one of two families.**
L16 and L18 are the only layers that validate strongly and unambiguously in both — depth statements should
be anchored there and should state the L22 asymmetry.

**Cross-run consistency checked, not assumed.** The `existing` ablate column is byte-identical across
720463 and 721957 (as it must be — those vectors are loaded, not fitted). Only `clearharm` L16
(+0.350→+0.300) and L22 (+0.450→+0.350) moved, because `--harmless-holdout` halves that family's negative
class from 20 to 10. **No cell changes sign or validity status** — the intended cost of the holdout.

**Gap this exposed, now being closed.** The headline layer set (9/16/18/22/28) **omits L21 and L30**, which
are exactly the layers carrying the rep→behavior AUC result (L21) and the trajectory result (L30). Both
still rest on unvalidated directions. Launched **job 722611**, the full 32-layer sweep — it covers L21/L30
and is also the appendix deliverable.

**Claim audit updated:** BR-10 goes PENDING → **VERIFIED** with the real numbers and both caveats (the L22
asymmetry, and that 720463's induce arm is defective so 721957 is the one to cite). 86 claims:
VERIFIED 60, WITHDRAWN 8, SUPERSEDED 4, UNDERPOWERED 4, UNVERIFIED 4, PENDING 6. 118 checks, 0 failures.

**Other jobs:** 720725 (P8 generated) at 111/115 — nearly done. 721956 (P8 clearharm v3) running, 23 rows.

### Tick 42 — 2026-08-06 — P7 COMPLETE and written up; a stalled node killed+resubmitted; --exclude trap fixed
**P7 finished** (job 720463, 840 rows, `DONE.json`). Full ablate table, all 10 cells, every value
re-derived from `raw.jsonl` before writing it down — base_harmful refusal 0.950, n=20/cell:

| family | L9 | L16 | L18 | L22 | L28 |
|---|---|---|---|---|---|
| `existing` (carrot/bomb fit) | **−0.050** ✗ | +0.450 | **+0.600** | +0.250 | +0.250 |
| `clearharm` (native refit) | **−0.100** ✗ | +0.350 | **+0.900** | +0.450 | +0.300 |

**L9 is the only failing cell, and it fails in both families.** At L18/clearharm ablation drops refusal
from 0.95 to **0.05** while the norm-matched random control does nothing. Written up as
**`reports/P7_REFUSAL_DIRECTION_VALIDATION.md`**, including the §4 recommendation that the prose **"L9
ns" be replaced everywhere** with the positive claim it now supports: *no linearly-decodable refusal axis
exists at L9; refusal becomes linearly available at L16 and peaks at L18.* Limitations stated: n=20 means
L9's estimate is 1–2 items and is not distinguishable from zero alone — the claim rests on the contrast
with L16–L28 (5 to 18 items of 20) and on replication across two independent fits.

**720724 was hung, not slow — killed and resubmitted.** Its stderr showed
`Loading weights: 0%| | 0/291` frozen for **1 h 26 m**, while its sibling 720725 (same script, same
settings) was 47 items in. On teardown n-803 emitted `_cgroup_procs_check: failed on path
(null)/cgroup.procs` — a broken cgroup on that node, which is why the load never progressed. That is the
diagnosis, not a guess: a slow node prints progress, a broken one prints nothing.

**A trap I walked into, and then removed from all 54 wrappers.** My first two resubmissions
(721954/721955) used `--exclude=n-803` — advice the wrapper headers themselves gave. Both landed on
**n-306 with an RTX 3090** and died in ~10 s. **Passing `--exclude` on the sbatch line NULLIFIES the
script's `#SBATCH --nodelist`**, so the job becomes eligible for the whole partition. Only the wrappers'
`ERROR need L40S` guard caught it — worth noting that the guard did its job and cost us seconds, not
GPU-hours. Fixed by passing an explicit reduced nodelist instead, and by rewriting the advice in **all 54
wrappers** (10 advice lines + 54 example commands) so nobody repeats it. All 54 re-checked with `bash -n`.

**Resubmitted and queued:** `721956` (P8 clearharm v3, α=0.25) and `721957` (P7 headline re-run with the
corrected `--induce-eval harmless` default). `720725` still running, 47/115 items.

### Tick 41 — 2026-08-06 — P7 ANSWERS THE HEADLINE QUESTION: L9 is not a refusal axis, by either fit
**The tick-28 risk has resolved, and it resolved in a way that HELPS the paper rather than hurting it.**

`ablate_specific = (base − ablate) − (base − ablate_rand)`, n=20/cell, base_harmful refusal = 0.950:

| family | L9 | L16 | L18 | L22 | L28 |
|---|---|---|---|---|---|
| `existing` (carrot/bomb fit) | **−0.050** ✗ | +0.450 | **+0.600** | +0.250 | +0.250 |
| `clearharm` (native refit) | **−0.100** ✗ | +0.350 | *(running)* | *(running)* | *(running)* |

**L9 fails ablation in BOTH families.** Removing the L9 "refusal direction" does not reduce refusal at
all — refusal goes to 1.00, i.e. at or above baseline — while at L16/L18/L22/L28 the same operation
moves 5–12 of 20 items against a norm-matched random control that moves ~0. L18, the direction every
behavioral refusal arm downstream uses, is the strongest at **+0.600**. That validates the load-bearing
artifact.

**Why this strengthens rather than weakens the depth claim.** The worry at tick 28 was that if L9's
direction is invalid, then "L9 ns" is uninformative and the depth-localization contrast loses its force.
But L9 now fails under **two independently-fit directions** — the original carrot/bomb fit *and* a
ClearHarm-native refit built here from scratch. Two independent fits failing at the same layer is not a
measurement accident; it is evidence that **no linearly-decodable refusal axis exists at L9**. That
converts an uninformative null ("we injected something at L9 and nothing happened") into a positive
claim ("refusal is not linearly represented at L9, and is at L16–L28"). The honest framing for the paper
is the latter, and it should be stated that way rather than as "L9 ns".

**Caveat, stated plainly:** n=20 per cell, so one item = 0.05. L9's −0.050/−0.100 are 1–2 items and are
*not* distinguishable from zero on their own. The claim rests on the **contrast** with L16–L28 (9–12
items), which is large, and on its replication across two fits — not on the L9 point estimate.

---

**A REAL DEFECT I FOUND IN THE P7 HARNESS'S INDUCE ARM — the ablate numbers above are unaffected.**

The induce arm was evaluated on `neutral`, and `neutral` **is not benign**: it is the harmful request with
the harmful word swapped for the codeword (`ds_common.build_conditions:797`), i.e. a *disguised harmful*
prompt. Measured on this very run it refuses at **0.750**. Two consequences:
1. **Ceiling.** `induce_gain` cannot exceed +0.25, so a perfectly good direction can fail the induce
   criterion from the ceiling alone. (L9 existing scored +0.200 of that +0.250 — it looks *strong* on
   induce, which is precisely why the arm cannot be read as-is.)
2. **Dose/population mismatch.** `alpha_induce` is calibrated as
   `mean_proj(direct) − mean_proj(HARMLESS_INSTRUCTIONS)`, then applied to a population whose projection
   is already elevated.

The **ablate arm always ran on `direct`** (base refusal 0.950, full headroom to drop), so **everything in
the table above stands.** I did **not** cancel job 720463 — it is 1.6 h in and its ablate arm is the
direct test.

**Fix implemented** in `scripts/validate_refusal_directions.py` for the follow-up run:
- `--induce-eval {harmless,neutral}`, **default `harmless`** — evaluates on `brd.HARMLESS_INSTRUCTIONS`,
  the same negative class used for the fit *and* the alpha calibration, so all three finally share one
  convention. `neutral` is kept solely to reproduce 720463 and earlier.
- **`--harmless-holdout` (default on)** — I caught a contamination hazard *in my own fix*:
  `HARMLESS_INSTRUCTIONS` is also the clearharm refit's negative class and the gap-alpha reference, so
  evaluating induce on it would score the refit direction on its own fit set, where it would induce
  refusal by construction. The set is now split into disjoint halves (fit/alpha = first 10, induce-eval =
  last 10); verified disjoint by unit test.
- **No cycling to pad the arm.** My first version repeated prompts to reach n=20; under greedy decoding a
  repeated prompt gives a byte-identical generation, so that would have inflated n with duplicate rows and
  shrunk every CI/McNemar on a sample that never grew. The induce arm now uses distinct prompts only and
  may legitimately be shorter than the ablate arm.
- Row ids, `inlen`, and all paired McNemar inputs rewired to the induce population (`harmless_<i>`), since
  those rows are no longer bench items; an assert guards the lengths.
- `induce_eval`, `refusal_base_benign` and `induce_gain_ceiling` now recorded in `summary.json`, so an
  `induce_gain` can never again be read without its ceiling.
Compile-clean; dry-run green; dry-run dirs cleaned up.

**Other jobs:** 720725 (P8 generated) is generating, raw=21. 720724 (P8 clearharm) still at raw=0 after
1 h 11 m on n-803 — that is now well past n-803's documented 14-min worst load, so it is the one to watch
next tick.

### Tick 40 — 2026-08-06 — P14 lands and immediately pays for itself: the P8.0 withdrawal had no artifact
**P14 `reports/CLAIM_AUDIT_TABLE.md` is DONE** (commit `97da0bd2`) — 86 claims, each traced to its run dir,
producing script and recompute command, with 118 numeric checks that re-derive the headline numbers from
committed artifacts and a non-zero exit on any failure. 37 run dirs cited, 0 missing.

| status | n | |
|---|---|---|
| VERIFIED | 59 | recomputed from raw this sprint |
| WITHDRAWN | 8 | actively retracted |
| SUPERSEDED | 4 | replaced by a better measurement |
| UNDERPOWERED | 4 | number right, design can't support the inference |
| UNVERIFIED | 4 | asserted in a report, never recomputed |
| PENDING | 7 | run still in flight |

**Only 19 of 86 are abstract-eligible.** All five mandated corrections are carried explicitly.

**THE FIND, and it is the reason this deliverable was worth doing: the evidence that WITHDRAWS P8.0's
sub-additivity claim existed only as prose in this progress file.** `outputs/alpha_calibration.json` held
the **curated cohort only** — no clearharm block at all — and `reports/PHASE8_1_ALPHA_CALIBRATION.md` on
disk was still the **n=78 PROVISIONAL** version carrying its own "do not cite" banner. I had been citing
α=0.25 numbers that no committed artifact contained.

I verified this myself before acting, rather than taking the auditor's word, and the cause turned out to be
benign: **job 716014 had in fact completed** (86/86 rows, 86 distinct ids, `DONE.json` + `summary.json`) —
a stale-artifact problem, not missing data. Re-ran the analyzer over both cohorts. **Every prose number
reproduces exactly:**

| quantity | prose claim | regenerated (n=86) |
|---|---|---|
| Î at α=0.25 | −0.023 | **−0.023256** |
| 95 % CI | [−0.151, +0.105] | **[−0.15116, +0.10465]** |
| sign-flip permutation p | 0.8597 | **0.859743** |
| Spearman(I_max, Î) | +0.991 | **+0.991031** |

`D_i` is symmetric — −2:1, −1:14, **0:57**, +1:14, +2:0 — a textbook null, not a suppressed effect.
**The n=78→86 refresh did move `I_max`** (α=0.25: +0.487→**+0.4767**; α=1.0: +0.231→**+0.1860**), but
α=0.25 stayed the *sole* qualifying dose at every n, so no conclusion ever rested on the partial file.

**A mistake I made and caught: `--md` emits tables only**, so my first regeneration clobbered the report's
interpretive prose (444→195 lines). Recovered from `HEAD`, spliced the FINAL tables in, then fixed the six
stale n=78 passages by hand.

**Two bugs in the audit's own check harness, fixed before trusting its green result** — a checker that
can't fail is worse than none:
- `_dig` split paths on `.`, so the literal alpha key `"0.25"` walked to `["0"]["25"]`. List paths now
  supported; otherwise my new checks would have failed for a bogus reason.
- a boolean `expect` went through `float()`, where `float(False) == float(0)`, so `provisional: 0` would
  have passed a check asserting literal `false`. Booleans now compare by identity.
Both confirmed by negative control: perturbing either expected value produces `CHECK-FAIL`.

**Still untraceable to a run dir (4 UNVERIFIED, down from 5):** BR-12 (concept⊥refusal cosine — never
measured, *and* a cross-convention comparison, since refusal vectors use a double-BOS forward and concept
vectors do not), RP-03 (`REP_PREDICTS_BEHAVIOR.md`'s L17–L32 AUC sweep and 5-fold CV — the shipped script
emits only the single L21 result), FIN-03, META-03.

**Three other findings worth acting on:**
- `P10_DECODE_SAFE_WRITE.md` §5 mis-cites its own power source: n≈275 is for ΔASR=0.09, not 0.07 (that is
  **n≈419**).
- The **trajectory** result reads at **L30**, which the P7 smoke also flags INVALID — so **two** headline
  readouts sit on directions the smoke rejects, not one. (RP-01's L21 and BR-08's L22 do pass.)
- `validate_all_outputs.py` does not recognise the P7 `refval` row schema, so **no P7 number can be called
  VERIFIED until that reconciler is taught the schema** — a prerequisite, not a nicety.

**GPU: all three jobs healthy and now past setup into real work.**
- **720463 (P7)** — all five ClearHarm refit directions written 04:45 (`L9/16/18/22/28.pt`); `raw.jsonl`
  created 04:46. The refit stage is done and generation has started.
- **720725 (P8 generated)** — `gens.jsonl` at 5 lines = the first item's 5 arms complete, so the first raw
  row is imminent. That also confirms the 5-arm/item structure, ≈24 s/item ⇒ ~46 min for 115 items.
- **720724 (P8 clearharm)** — RUNMETA 04:31, still in setup on n-803.

### Tick 39 — 2026-08-06 — all three GPU jobs healthy and in setup; started P14 (claim audit)
**No SLURM problem this tick — nothing to cancel or resubmit.** All three jobs are `R`, all three cleared
their pre-flight gates, and each is in weight-load/setup:

| job | phase | node | elapsed | time left | state |
|---|---|---|---|---|---|
| 720463 | P7 refusal-direction validation (L9/16/18/22/28) | n-801 | 58 m | 3 h 02 m | RUNMETA written 04:10 — progressing |
| 720724 | P8 2×2 interaction, clearharm v3 | n-803 | 30 m | 2 h 30 m | run dir minted 03:50, still loading |
| 720725 | P8 2×2 interaction, generated v3 | n-801 | 27 m | 2 h 33 m | run dir minted 03:56, still loading |

**The gates I actually checked, rather than assuming:**
- 720724/720725 both logged `[ok] DSALPHAS='0.25' from --export: single value, no comma, safe` — the guard
  fix from tick 38 works, and the de-saturated dose really did arrive (this is the exact thing that failed
  last tick, so it is worth verifying rather than trusting).
- Both P8 jobs are reading `data/behavioral_v3/beh_{clearharm,generated}.json` — the v3 benches, **not** the
  v1 file I clobbered and restored. Confirmed from the log's `bench=` line.
- All three: `GPU ok: NVIDIA L40S`.

**Why `raw.jsonl` is still empty is expected, not a hang.** Two of the three are on **n-801**, the node
documented (over 232 logged runs) as owning every weight load slower than 15 min, worst 79 min. 720463's
dir was minted 03:33 and its RUNMETA landed 04:10 — a 37-min gap that is *progress*, not a stall, so a
22-min empty dir on the younger P8 jobs sits inside the same envelope. I am not cancelling healthy jobs
to chase a faster node; the 30-min rule governs time-to-**allocation**, and all three allocated.

**Started P14 — `reports/CLAIM_AUDIT_TABLE.md` (a required plan deliverable, still unstarted at tick 38).**
Pure CPU, so it costs nothing against the running jobs. The auditor traces every quantitative claim in the
paper-facing reports to its run dir, producing script, and a recomputation command, and is explicitly
required to carry this sprint's retractions rather than quietly drop them: P8.0's sub-additivity
(WITHDRAWN), P10.0's graded carry effect (fails its specificity control), the concept-write null
(UNDERPOWERED, n=86 vs n≈275 needed), and every per-layer refusal claim (PENDING on 720463). It must also
flag every row whose effect sits under the measured ~2 pp judge noise floor.

### Tick 38 — 2026-08-06 — P8 failed on a false-positive guard (my error); fixed; P7 RUNNING
**P7 (720463) is RUNNING** on n-801 — the headline-layer validation is finally underway.

**P8's two jobs FAILED, and the cause was my own reasoning error.** They allocated quickly (submitted
03:08, started **03:27** — 19 min) and then died in ~3 min on the wrapper's own guard:

> `ERROR: DSALPHAS='0.25' came from the environment/--export; sbatch --export SILENTLY TRUNCATES comma-lists.`

At tick 31 I reasoned *"a single `DSALPHAS=0.25` has no comma, so it survives `--export`"*. That was correct
about **truncation** and wrong about **the guard**, which refused `DSALPHAS` from the environment
**unconditionally** — comma or not. I asserted safety from the hazard's mechanism without checking the
check.

**Fixed precisely rather than by weakening it:** the guard now refuses only when a comma is *actually*
present, and accepts a single value with an explicit `[ok]` line. Verified both branches — comma → REFUSED,
single → ACCEPTED — plus `bash -n`. Relaunched as **720724 / 720725**.

**Cost:** ~6 minutes of GPU and one tick. **Cheap, because the guard failed FAST and LOUD** — it printed
the exact variable, the exact mechanism, and the exact remedy, and exited before loading the model. That is
the failure mode you want: a silent pass-through would have run the whole 1.6 h job on a truncated α and
produced plausible-looking numbers at the wrong dose.

**One genuinely useful datum:** these jobs went from submit to start in **19 minutes**, the first sub-30-min
allocation since the cluster jammed. So the queue *is* moving, and tick 37's pessimism about ~19 h
reservation estimates was — as suspected — an artifact of `--test-only` ignoring backfill.

### Tick 37 — 2026-08-06 — right-sized P8's walltime; could NOT show it helps allocation
**Applied §1.3.0** to 720320/720321 (pending 59 min) → resubmitted as **720598 / 720599**.

**Right-sized the walltime from 10 h to 3 h**, from a measured estimate rather than a guess: the α-sweep
reference was 24 arms × 86 items ≈ 3.5 h, so 5 arms × 127 items ≈ **1.1 h** plus ~0.5 h model load. A 10 h
request for a ~1.6 h job is bad hygiene regardless of scheduling, and the plan already asks for `--time` to
match real need.

⚠️ **But I could not demonstrate that it improves allocation, and I should not imply otherwise.** My
reasoning was that on a fully-saturated cluster backfill is the only way in and backfill favours short jobs.
Testing it: `--test-only` returns the **identical** start estimate for `--time=03:00:00` and
`--time=10:00:00` (both `2026-08-06T22:09`). That is consistent with tick 22's finding that wait time has
**no relationship to `--time`**. So the change is defensible as hygiene, **not** as a fix — the plausible
mechanism remains unmeasured, and I have one piece of evidence against it.

**The cluster is genuinely jammed**, which is the real story: the scheduler's reservation estimate is
**~19 h out**, 85 jobs pending on `killable`, all 48 L40S allocated. Per §1.3.0 case 3 this is the
"switch to CPU work and say so" situation, and repeated resubmission is following the letter of the
30-minute rule without being able to change the outcome.

**Nothing new landed this tick.** Queue: 720463 (P7 headline layers), 720598/720599 (P8 core).

### Tick 36 — 2026-08-06 — corrected a false claim I made about the P7 harness; no code change needed
Went to add incremental writing to `validate_refusal_directions.py` — the fragility I asserted at tick 34 —
and **found it already had it.** `scripts/validate_refusal_directions.py:440` calls `fh.flush()` after every
(family, layer) block, so partial results survive an interruption. **My tick-34 statement that the harness
"writes `raw.jsonl` only at the END" was false**, and it was one of three reasons I gave for killing the
full sweep. Tick 34 is corrected in place and the "needs an incremental writer" follow-up is withdrawn.

The retarget decision itself still stands on its remaining grounds: ~7 h of work against an 8 h walltime is
genuinely tight, and the five headline layers answer the actual question ~6× faster. But it is worth being
clear that I acted partly on something I had not verified — and that **checking before writing the fix is
what caught it**, at the cost of nothing but a grep.

**Why the dir really was empty at 2 h 15 m:** the job had not finished *setup* — base-condition generation
plus the `clearharm` family refit — so it had never reached the per-layer loop where the flush lives.

**SLURM:** 720175 had been pending 58 min, so per §1.3.0 it was cancelled and resubmitted as **720463**.
P8's 720320/720321 are at 28 min, inside the window, and were left alone. Cluster still saturated
(85 pending on `killable`, all 48 L40S allocated).

### Tick 35 — 2026-08-06 — 30-min rule applied to P8; v3 benches pre-flighted; an n caveat found
**Cluster is worse, not better:** all 48 L40S allocated and the `killable` queue has grown **66 → 89**
pending. P8's jobs had sat **119 min**, so per §1.3.0 they were cancelled and resubmitted as **720320**
(v3 clearharm) / **720321** (v3 generated). The rule was followed, but it cannot manufacture a GPU — this
is the §1.3.0 case-3 situation, and the honest note is that we are simply waiting on other groups.

**Pre-flighted the v3 benches before burning a 10 h job on them.** Both are structurally sound: correct
field schema for `phase_behav_refusal`, **170 / 154** items, **all ids unique**, **all demos non-empty**,
**all `harmful_word`s single-token**, splits sane.

⚠️ **But the check surfaced a caveat that changes the P8 power arithmetic.** The wrapper defaults to
`DSSPLITS=train,test`, and v3 has **three** splits (train / dev / test). So P8 will process
**train + test only**:

| cohort | train | test | **P8 n** | (dev held back) |
|---|---|---|---|---|
| clearharm | 85 | 42 | **127** | 43 |
| generated | 77 | 38 | **115** | 39 |
| **total** | | | **242** | 82 |

That is **242, not the 324** the power table targets — because dev is reserved for selection **by design**,
which is correct methodology, not a bug. It is still **2.8× the n=86** that made P8.1 uninterpretable, so
the run is well worth doing; but the write-up must quote **n=242** and not imply 324. If the interaction CI
is still too wide at 242, the options are to fold dev in for a final confirmatory pass (only after the
analysis is frozen) or to state the residual width honestly.

### Tick 34 — 2026-08-06 — traded P7's full sweep for the answer we actually need
**Cancelled 718937 at 2 h 15 m and relaunched as 720175 with a targeted layer set.** This was a judgement
call, so the reasoning is recorded.

**The risk:** the full 32-layer × 2-family × 4-arm × 20-item sweep is ~5,100 generations ≈ 7 h against an
**8 h walltime**. At 2 h 15 m it had produced only `RUNMETA.json`, so there was no partial result to
salvage.
⚠️ **CORRECTED at tick 36:** I also justified the kill by claiming the harness "writes `raw.jsonl` only at
the END". **That was wrong** — `validate_refusal_directions.py:440` calls `fh.flush()` after every
(family, layer) block, so results *do* persist incrementally. The reason nothing was on disk at 2 h 15 m is
that the job had not finished **setup** (base-condition generation plus the `clearharm` family refit) and
so had not yet reached the per-layer loop at all. The decision to retarget still stands on its other
grounds — ~7 h against an 8 h limit is genuinely tight, and 5 layers answer the actual question ~6× faster
— but one of the three reasons I gave was false.

**The trade:** the paper question is not "are all 32 directions valid" — it is *"are the specific directions
our published claims rest on valid?"* That is **five** layers: **L9/L16/L22/L28** (the four calibrated
depth-localization injection layers, with L9 the contested one) and **L18** (the direction every behavioral
refusal arm uses). Five layers is ~6× cheaper — ~1 h, comfortably inside a 4 h walltime — and answers the
question tonight instead of possibly never.

**Made repeatable rather than ad-hoc:** added a `DSLAYERSET` preset to the wrapper
(`headline` → `9,16,18,22,28`, `all` → unchanged default). This also sidesteps the `--export`
comma-truncation bug: you pass `DSLAYERSET=headline`, never `DSLAYERS=9,16,...`. Verified with `bash -n`
plus a direct check that `headline` expands correctly and the default is byte-unchanged.

**Follow-up owed:** the full 32-layer sweep is still worth having for the appendix — re-run it at leisure
with a longer walltime. (The "needs an incremental writer" follow-up I recorded here is **withdrawn**: it
already has one.)

### Tick 33 — 2026-08-06 — P10 COMPLETE: the §0.9 defect is closed and the null holds
Read out 718938 with the existing paired analyzer (McNemar + bootstrap + Holm), wrote
`reports/P10_DECODE_SAFE_WRITE.md`. The concept-write behavioral null survives a genuinely decode-safe
ablation. P7 (718937) still running at 1 h 45 m of a ~7 h workload; P8 core (719260/719261) queued.

### Tick 32 — 2026-08-06 — P10 nearly done; P7 is large but alive; a liveness false-alarm corrected
**718938 (P10 decode-safe) at 78/86 rows** — minutes from completion.

**718937 (P7 validation): I nearly called a hang that wasn't one.** Its `.out` had been silent for
39 minutes after only the 6 header lines, and it is running on **n-801** — precisely the node with the
documented pathological weight-load tail (owns 100 % of >900 s loads, worst 79 min) that I overrode at
tick 25. That is exactly the profile the §1.3.1 hung-job rule targets, and I was one step from cancelling.

**Checked before acting, and it is alive:** its run dir `refval_clearharm_20260806_003052_718937` was
created at **00:30:52** and touched at **00:32:47**, i.e. minutes ago — so the process is past weight
loading and writing. The silence is the harness's own design (the smoke likewise emitted its `[refval]`
lines only at the end), not a stall.

**Why it is slow is arithmetic, not pathology:** 32 layers × 2 direction families × 4 arms
(ablate / induce / 2 random controls) × 20 items ≈ **5,100 generations**. At ~5 s each that is ~7 h against
an 8 h walltime — feasible but tight. **If it approaches the limit it should be resubmitted with a smaller
`DSVALN` or a layer subset rather than killed blind**, since the layers that matter for our headlines
(L18, L22, and the contested L9) are a handful, not all 32.

**The generalisable lesson:** "log silent for N minutes" is *necessary but not sufficient* evidence of a
hang. The tick-8 job was genuinely stuck (frozen mid-progress-bar, run dir never created); this one is
merely quiet. **Check the run-dir mtime, not just the log**, before cancelling.

### Tick 31 — 2026-08-06 — near-miss confirmed harmless; **P8 CORE LAUNCHED** at the corrected dose
**The tick-30 bench overwrite caused no contamination — verified definitively, not assumed.** Rather than
wait for the run to finish and count rows, I checked the *identities*: all **17/17** ids written so far by
718938 are in the **v1** bench and **0** are in v3, with **0 ids v3-only**. Job 718938 read the correct
bench. Verdict: **CLEAN**.

### ⭐ P8 core launched — the measurement the whole sprint has been building toward
**719260** (v3 clearharm, n=170) and **719261** (v3 generated, n=154), `--alphas 0.25`, full n.
**Zero new code** — `phase_behav_refusal.py` already produces the 2×2 (direct_base / ds_base /
direct_refabl / ds_refabl) plus the norm-matched random control at each α.

Both prerequisites are finally satisfied *together*, which has not been true before now:
1. **The dose is right.** P8.1 showed α = 1.0 saturates the design (`I_max` = +0.186) and manufactures
   sub-additivity; **α = 0.25 gives `I_max` = +0.477**, 2.6× the headroom.
2. **The n is right.** P8.1's interaction CI at n = 86 was **[−0.151, +0.105]** — too wide to distinguish
   independence from a real effect. v3 gives **n = 170 + 154**, against the power table's n ≈ 324.

*(A single `DSALPHAS=0.25` has no comma, so it survives `--export` — the known comma-truncation bug does
not bite here.)*

⚠️ **Analysis requirement carried from P1b:** report **per cohort as well as pooled.** `clearharm` (170,
real ClearHarm instructions) and `generated` (154, gpt-4o-mini) are launched as **separate jobs** precisely
so a cohort × condition interaction is detectable; if one appears, the two cannot be pooled.

### Tick 30 — 2026-08-05 — 🛑 I nearly destroyed the v1 behavioral bench; caught, restored, guarded
**My mistake, recorded in full.** Building the v3 behavioral bench for P8, I ran
`split_to_behavioral.py --split ...v3.json` with the **default `--out-dir data/behavioral`**. The output
filename is derived from the **cohort**, and v3 *also* has a cohort called `clearharm` — so it silently
**overwrote `beh_clearharm.json` from 86 v1 items to 170 v3 items.** That is the file **every completed
behavioral result was computed against**: the α sweeps, BEHAV-CARRY/WRITE/REFUSAL, P8.0, P8.1.

**Caught immediately, restored from git** (`git checkout --`), verified back at **86 items**. v3 benches
now live in a separate `data/behavioral_v3/` (170 clearharm + 154 generated); `data/behavioral/` is
untouched at 86 + 51.

**The running job was not affected** — 718938 wrote its `RUNMETA.json` at **23:30:03** and the harness
writes RUNMETA before loading the bench, ~10 min ahead of the overwrite. It recorded
`bench=data/behavioral/beh_clearharm.json`. I will confirm definitively when `raw.jsonl` appears:
**86 rows = v1 (correct), 170 = v3 (contaminated).**

**Guard added so it cannot recur:** `split_to_behavioral.py` now **refuses to overwrite** an existing
`beh_<cohort>.json` unless `--force`, with an error naming the collision. Negative controls: clobber
attempt → **exit 1** with v1 still at 86 items; fresh `--out-dir` → **exit 0** and both benches written.

**The lesson worth keeping:** the file was git-tracked, which is the *only* reason a one-command recovery
existed. Had `data/behavioral/` been gitignored like `outputs/` was before P0.1, this would have been an
unrecoverable loss of the baseline underlying every published behavioral number.

Both full runs are healthy: **718937** (P7 validation) RUNNING 15 min, **718938** (P10 decode-safe)
RUNNING 20 min — allocated after 3 and 9 min respectively, inside the 30-minute rule.

### Tick 29 — 2026-08-05 — 30-min rule applied; P2 report finalised with the v2 replication
**Applied §1.3.0 at 29 min:** cancelled 718378/718379 and resubmitted as **718937** (P7 full validation,
`DSVALN=20`) and **718938** (P10 full decode-safe). The wrappers now carry the fast config by default
(cpus=4, mem=48G, n-801 included), so the resubmit needed no manual flags.

**Finalised `reports/PHASE2_ALL_OCCURRENCES.md`** — it still said "v2 still running". Added §2b with the
completed replication and closed the matching limitation.

**The ratio replicates on every bench tested:** 1.42× / 2.27× (clearharm v1), 2.03× / 1.85× (curated),
1.38× / 2.13× (v2). **All six cells fall in 1.38–2.27×**, across three independently-built benches
including 30 novel concepts. So "the demo-only measurement understates the write by ~2×" is not a
single-bench artifact — which is what makes it safe to put in the paper.
One new detail from v2: the dev Holm band now reaches **L7**, a layer earlier than the v1 benches showed,
consistent with the write being distributed across a band rather than pinned to L9.

### Tick 28 — 2026-08-05 — P2 complete; P7 smoke flags a risk to the depth-localization headline
All three GPU jobs completed. **P2 replicated on v2** (2.13× on heldout) — phase closed. **P10 smoke
validated** the decode-safe harness with the decode-damage confound visibly quantified (raw necessity 0.0
while the random control moved 0.5 — exactly why the count-matched control is read instead). **P7 smoke**
shows only ~15/32 refusal directions validate, including an invalid **L9** that may undercut the
depth-localization contrast; full runs launched as **718378** (P7, DSVALN=20) and **718379** (P10, full n).

### Tick 27 — 2026-08-05 — v3 hits n=324; the dataset blocker is cleared
P1b complete and independently verified. All three GPU jobs still running. The interaction test that P8.1
left uninterpretable is now adequately powered on paper — pending the per-cohort exchangeability check.

### Tick 26 — 2026-08-05 — three jobs running past the preemption point; analyzer silent-skip fixed
**All three GPU jobs RUNNING at 15 min** on n-805 (717879 P10 decode-safe, 717880 P7 direction validation,
718027 P2 v2) — past the ~13 min mark where the previous pair was preempted. Each wrote `RUNMETA.json`
**before** compute, per the §2.1 contract; no `raw.jsonl` yet, so they are still in model load.

**Fixed the analyzer defect logged at tick 19.** `analyze_alpha_calibration.py --run` takes `COHORT=PATH`;
a bare path left `run_dir=""`, printed `[skip] ... no raw.jsonl in `, and **still exited 0 after writing an
empty report** — the identical silent-skip false-OK pattern we removed from `validate_all_outputs` at
tick 5, reintroduced in a *paper-analysis* script where an empty report masquerading as success is worse.
Two guards now: a malformed/nonexistent `--run` is an `argparse` hard error, and **a run that analyses
zero cohorts exits 2 rather than writing an empty report as success.**
Negative controls (exit codes captured directly, not through a pipe — my first attempt measured `tail`'s
status and wrongly showed 0): bare path → **2**, bad dir → **2**, valid dir with no `raw.jsonl` → **2**,
valid run → **0** with the α table intact.

### Tick 25 — 2026-08-05 — 🛑 I was wrong about "SLURM SOLVED"; the real mechanism found
An adversarial wrapper audit falsified my tick-23 verdict **the same day**, and I verified every point.

**1. "SLURM SOLVED" is WITHDRAWN.** 717879/717880 — the exact pair I cited as proof — were **PREEMPTED off
n-805 ~13 min after starting** and are back to PENDING at the same 4cpu/48G footprint. Confirmed by
`squeue`. **`killable` is preemptible, so time-to-first-allocation is not the metric; time-to-completion
is.** I measured the wrong thing and declared victory on it.

**2. My A/B was worthless as evidence** — n=2 vs n=2, confounded with 3.5 h of cluster churn. All ~1,500
historical jobs used cpu=8/mem=64G, so there was no variance to test the claim against.

**3. But `--mem=48G` IS right, for a reason I hadn't found.** L40S nodes have `RealMemory=515600 MB` and
8 GPUs ⇒ **64450 MB per GPU-share**. At `--mem=64G` (65536 MB) only **7 of 8 GPUs are memory-feasible** —
**the 8th GPU on every L40S node was structurally unreachable**, i.e. we were locked out of **6 L40S GPUs,
12.5 % of the pool**, by one flag. Verified against `scontrol show node`. That is a hard scheduling
mechanism and it is the real justification.
⚠️ Conversely **`cpus 8→4` has no mechanism** (128 CPUs / 8 GPUs = 16 per share; 8 was never binding).
Harmless, but not the fix — and I had presented it as one.

**4. I was wrong that n-801 was excluded "for no stated reason."** It was a documented, measured decision:
`IMPLEMENTATION_PROGRESS.md:694` records smoke 704416 spending **1 h 09 m** loading weights there. Across
232 parsed job logs, n-801's median load (389 s) is unremarkable **but it owns 100 % of the catastrophic
tail** — every load > 900 s in the corpus, worst **4741 s (79 min)** — while no other L40S node exceeded
811 s; ~9 % of n-801 runs stall. Restored anyway (capacity is real), **with the caveat preserved in every
wrapper header and `--exclude=n-801` recommended for short smokes**, where a 79-min load burns the whole
allocation. I should have read the exclusion note before calling it unjustified.

**5. The actual fix remains partition access, not `#SBATCH` tuning** — `gpu-sharifm` (lab partition, 5-day
limit, non-preemptible, currently an idle a5000) rejects this account. Worth one email to Mahmood.

**Wrappers:** all 54 pass `bash -n`; 50 at `mem=48G`, 4 at 64G (the Qwen3-14B GCG harnesses, justified);
54/54 keep the L40S guard, `HF_HUB_OFFLINE`, `set -euo pipefail` and conda activate; n-801 in all 54.

### Tick 24 — 2026-08-05 — GPU pipeline restarted; P2 v2 replication relaunched
With the fast config proven, put the freed capacity to work. **717879 (P10 decode-safe) and 717880 (P7
direction validation) running cleanly** on n-805 (7 min in, past the L40S guard, at commit `bfa7795`).

**Relaunched the P2 v2 replication as 718027** using the measured fast config
(`cpus=4 mem=48G`, all six L40S nodes). This is the run I had to cancel at tick 8 when it hung for 3 h in
weight-loading with zero output — the one piece of P2 left incomplete. Zero new code; `--positions all`
already exists. It completes the P2 finding on the 116-example v2 bench, where the v1 benches showed
all-occurrence patching roughly doubles the L9 write necessity.

Still in flight: the v3 expansion on the OpenAI budget (targeting n ≈ 324 for a powered interaction test),
and the agent applying the fast config across every wrapper in `slurm/`.

### Tick 23 — 2026-08-05 — ⚠️ "SLURM SOLVED" — **THIS CLAIM WAS WRONG, see tick 25**
**Target met.** 717879 (P10 decode-safe) and 717880 (P7 direction validation) **allocated in 6 m 32 s**
and are running on n-805, past the L40S guard, at commit `bfa7795`.

**The lever, established by direct A/B on the same work:**

| config | outcome |
|---|---|
| `cpus=8, mem=64G, time=1:00/1:30` | PENDING **3 h 32 m** |
| `cpus=4, mem=48G, time` matched | **ALLOCATED 6 m 32 s** ✅ |

**What I ruled out along the way, so it isn't retried:**
- **`--time` is not the lever** — no correlation across the day (14 h job → 5 min wait; 20 min job →
  319 min wait).
- **Concurrency is not the limit** — `sacctmgr` shows `MaxJobs=50`.
- **3090/a5000 nodes don't help** — `--test-only` returns the *identical* ~24 h estimate for every config
  including 1 CPU/8 G on an idle 3090. That estimate just reports when current jobs hit the partition's
  1-day limit; it ignores backfill and is **not actionable**. Six probe configs (3090 / a5000 / n-801 /
  6-node L40S / unconstrained / large) were submitted and **all six stayed PENDING while our two real jobs
  ran** — which also showed the probes were **competing with our own work**, so I cancelled them.
- **`gpu-sharifm`** (the lab partition, with an idle a5000 node) refuses us: *"User's group not permitted."*

**Two concrete fixes:**
1. **cpus 8→4, mem 64G→48G** as the default in every wrapper — ample for single-GPU 8B bf16 inference.
2. **n-801 restored to the nodelist.** Several wrappers listed only `n-802..805,t-806`, silently giving up
   an equally valid `gpu:l40s:8` node — **1/6 of our L40S capacity** — for no stated reason.

Codified as the "MEASURED FAST CONFIG" block in plan §1.3, with the A/B table, so it is never re-derived.
An agent is applying it across all wrappers in `slurm/` now.

### Tick 22 — 2026-08-05 — 30-minute allocation rule added and applied; found a partition we cannot use
**Omer's rule, now plan §1.3.0: a job must be ALLOCATED within 30 min of submission, else `scancel` and
resubmit with settings that have demonstrably worked.** Checked every tick from now on.

**Applied:** cancelled 716187/716188 (pending **3 h 32 m**) and resubmitted as **717879/717880** with a
smaller footprint (`--cpus-per-task=4 --mem=48G`, `--time` matched to real need) to fit backfill gaps.

**Measured which settings actually correlate with fast allocation — answer: none of ours.** Over all of
today's jobs, every single one used `killable / gpu-research / cpu=8 / mem=64G`, and wait time showed **no
relationship to `--time`**: a 14 h job waited 5 min while a 20 min job waited 319 min. The delay is
**cluster load at submit**, not our configuration. Recorded in the rule so nobody re-derives it.

**⚠️ Found something worth an email to Mahmood:** the cluster has a **`gpu-sharifm`** partition — n-804
L40S + a6000 and an **idle a5000 node**, `MaxTime=5 days` — i.e. the lab's own partition. Submitting to it
returns *"User's group not permitted to use this partition."* **All 1,551 of this project's jobs have gone
through the shared preemptible `killable` pool**, competing with ~64 queued jobs from other groups, while a
lab partition with idle capacity sits unusable. Getting the account added would likely remove the queueing
problem outright.

Also confirmed the current blockage is real scarcity, not misconfiguration: **all 48 L40S GPUs (6 nodes ×
8) are allocated**, zero idle L40S cluster-wide.

### Tick 21 — 2026-08-05 — SLURM stuck-job rule added; OpenAI budget unblocks the powered v3
**Omer added a standing rule** (now plan §1.3.1): *if a job is stuck, kill it and resubmit with corrected
settings and current scripts; copy settings from a run that demonstrably worked.* Written up with a
diagnose-first ordering, because the fix differs by cause — hung-but-`R` (scancel), fixable PENDING reason
(fix+resubmit), no-free-GPU (do **not** churn the queue; switch to CPU/API work), or semantically stale code
(resubmit against a known commit).

**Applied it to 716187/716188 — and the honest answer is that our settings are not the problem:**
- identical to jobs 714998/716014 which ran fine today (killable / gpu-research / 8 CPU / 64 G / L40S list);
- scripts on disk are current (the only commit touching them is the one that created them);
- **all 48 L40S GPUs — 6 nodes × 8 — are allocated; zero idle L40S cluster-wide** (idle capacity is
  2080/3090/A5000/V100). 64 jobs pending on `killable`, 18 running on our nodes.
- I also corrected an overstatement I nearly made: `sprio` shows AGE contributes **5 points** against a
  1e8 partition factor, so requeuing costs nothing — **but it also creates no GPU.**
⇒ Requeuing identical jobs would be theater. Rule §1.3.1 case 3 applies: **switch to CPU/API work.**
Also recorded in the rule: never relax `--nodelist`/L40S to escape a queue — the constraint exists for
numerical comparability and the wrapper's `nvidia-smi` guard would just exit 1, burning the allocation.

**Omer confirmed OpenAI budget is available**, which resolves the scoping question raised at tick 20.
Launched the **v3 expansion toward n ≈ 324**, the size the plan's own power table requires to detect an
interaction of 0.15 under Holm m=5. This is the direct fix for P8.1's uninterpretable CI [−0.151, +0.105].

**The instruction that matters most in that job:** optimise for **distinct concepts, not rows.** The last
expansion added +60 % rows but only **+2 concepts** (43 → 45), because recovered rows densified concepts
that already existed — and since the split is concept-clustered, every per-concept claim is limited by
cluster count, not row count. Also fixing the 59 placeholder benign-condition rows.

### Tick 20 — 2026-08-05 — propagated the P8.1 correction into every document that carried the claim
No GPU work possible: both smokes (716187 P10, 716188 P7) are still PENDING on **cluster** contention with
none of our own jobs running. Spent the tick closing the loop on tick 19 rather than starting anything new,
because a withdrawn claim left sitting in a plan is worse than one never made.

Corrected **4 locations across 2 documents**:
- `reports/PHASE8_0_PILOT_INTERACTION.md` — a SUPERSEDED banner at the top with the α table and the
  Spearman = +0.991 evidence, plus an inline withdrawal notice on §5.1/§5.2. Kept explicit about what
  survives (the arm tables, the ceiling analysis in §2.4 — which turned out to be the whole story — the
  judge-instability caveat, and `D_i = +2` never occurring) and what is *not* established (independence).
- `reports/CAUSAL_CONTINUATION_MASTER_PLAN.md` §0.6 — superseded banner; the instruction to "re-aim Phase 8
  as a pre-registered sub-additivity test" is withdrawn.
- **§6 pre-registration clause 3 — the dangerous one.** It required pre-registering a *sub-additivity*
  prediction, which would have **baked the artifact into Phase 8's confirmatory design**. Now: register the
  interaction **two-sided with no directional prediction**, and register the **ceiling diagnostic**
  (report `I_max` beside Î at every dose) as a standing check, since that correlation is exactly what
  exposed the artifact and is what would catch a recurrence.
- §6 clause 4 and §10 outcome 1 — α = 0.25 settled for clearharm, no α for curated, and the sub-additivity
  outcome struck.

**A consequence worth stating plainly:** with the sub-additivity gone, the live hypothesis is the *opposite*
one (separate channels), and P8.1 already tested it at α = 0.25 on n = 86 — finding no detectable
interaction with **CI [−0.151, +0.105]**. That interval is far too wide to claim independence. **This is now
the strongest single argument for the v3 dataset**: the plan's own power table says detecting an interaction
of 0.15 under Holm m=5 needs **n = 324**, and v3 currently stands at 138.

### Tick 19 — 2026-08-05 — P8.1 FINAL: the P8.0 headline does not survive de-saturation
clearharm sweep completed (86/86). Ran the final calibration on both cohorts: **α = 0.25 selected**
(I_max +0.477, 2.6× the +0.186 at α = 1.0), no α qualifies on curated. The decisive finding: at the
de-saturated dose **Î = −0.023, p = 0.86 — no detectable interaction** — while the P8.0 dose (α = 1.0)
reproduces P8.0's significant sub-additivity exactly. Spearman(I_max, Î) = +0.991. **P8.0's mechanistic
reading is withdrawn as a saturation artifact**, with the limits of the negative result stated explicitly.
Also logged an analyzer CLI defect that silently skips and exits 0.

### Tick 18 — 2026-08-05 — P8.1 operating point selected; tick-14's "additive" corrected
α = 0.25 selected for clearharm (I_max 2.1× the α=1.0 value); **no α qualifies for curated**. Corrected my
own tick-14 wording: Î below the multi-arm judge floor means *not detectable*, not *zero*. Independently
re-derived the ceiling reversal at α=1.5→2.0, which is the strongest evidence yet that the P8.0
sub-additivity is a design artifact rather than a mechanism.

### Tick 17 — 2026-08-05 — P8.1 analyzer being written ahead of the clearharm data
clearharm at 75/86 (~30 min out); curated done, which freed a GPU slot — but the P10 and P7 smokes are
still PENDING on **cluster** priority, not our 6-job limit (we hold only 1 running job), so there is
nothing to launch.

Used the tick to write `analyze_alpha_calibration.py` so it is ready the moment the data lands, rather
than writing it afterwards. Explicitly instructed to **reuse** `analyze_interaction_2x2.py`'s estimator,
bootstrap and permutation code rather than reimplement the statistics — two independent implementations of
the same test is how numbers drift apart.

Two constraints carried into the analyzer so they cannot be forgotten at write-up time:
1. **The judge noise floor (~2 pp) must sit next to the numbers, not in a footnote** — any ΔASR below it is
   indistinguishable from judge nondeterminism.
2. **Î and I_max must be reported side by side at every α**, so the ceiling relationship is visible to a
   reader. And the headroom-vs-saturated decomposition is explicitly **forbidden as evidence** — it is
   mechanically forced in both directions (tick 15), and the analyzer should not resurrect it.

### Tick 16 — 2026-08-05 — curated α sweep COMPLETE; judge noise floor measured exactly
Curated finished (51/51). Two results: (a) no usable sub-saturating α exists on curated — the α=0.25 point
chosen from clearharm does not transfer, and curated is a poor interaction cohort anyway since its DS ASR
is *below* its direct-base ASR; (b) chasing the α=0 anomaly produced a clean methods number — by hashing
generations I showed all 51 pairs are byte-identical while 1 label still flipped, isolating the
StrongREJECT judge's irreducible noise floor at ~2 pp with generation held exactly constant.
clearharm sweep at 62/86, ETA ~21:00.

### Tick 15 — 2026-08-05 — attempted to sharpen the ceiling finding; the test was invalid, self-corrected
Sweeps at 46/86 and 40/51 (~2.8 min/item; curated ETA ~19:40, clearharm ~21:00). No launches possible.
Tried to adjudicate the tick-14 ceiling question with a headroom-vs-saturated decomposition of Î; the
headroom half came back strongly positive, but the subgroup algebra forces `D_i ≥ 0` there, so both halves
are selection artifacts and the test proves nothing either way. Recorded as a self-correction rather than
quietly dropped, since the positive number is superficially exciting and would have been easy to misreport.
Net: tick-14's provisional finding is unchanged, and plan §5 P8.4's pre-registration requirement is
confirmed as necessary rather than bureaucratic.

### Tick 14 — 2026-08-05 — provisional α curve read; it challenges our own P8.0 headline
Sweeps healthy (clearharm 36/86, curated 29/51, ~2.6 min/item, ETA ~20:50). GPU saturated, so no launches.
Mined the partial `raw.jsonl` for the α curve rather than idling — and it produced the sprint's most
consequential provisional finding: **Î tracks the ceiling**, reaching exactly 0.000 (additive) at the
non-saturating α = 0.25 where `I_max` = +0.472. If that survives full n, the P8.0 sub-additivity result is
a ceiling artifact and the honest reading flips toward *independent channels*. Flagged, not concluded.

### Tick 13 — 2026-08-05 — P6 landed; double-BOS inconsistency confirmed and scoped
P6 Jacobian readout complete with a closed-form correctness proof (suite 205 → 224). Confirmed the
double-BOS finding myself and scoped it: no off-by-one, no bias in paired deltas, but a real
cross-convention wrinkle in the concept-vs-refusal cosine — folded into P7 to be measured, not argued.
α sweeps still running (ETA ~20:45); P10/P7 smokes still PENDING behind them.

### Tick 12 — 2026-08-05 — α sweeps confirmed alive by direct measurement; P6 Jacobian being written
**Liveness measured, not assumed.** The α sweeps had written no log line for 53 min, which by the tick-8
rule is exactly the signature I now distrust. Rather than guess, I found the live run dir and measured the
artifacts directly:
- `RUNMETA.json` present and written **before compute** — **the §2.1 provenance contract firing on a live
  run for the first time.** `gens.jsonl` present too, so `--save-gen` works end-to-end.
- `gens.jsonl` = **529 lines = 23 items × 23 arms**, `raw.jsonl` = 23 rows ⇒ gens is written per
  (item, arm), raw per item. **23 of 86 items done.**
- Rate: 23 items in 57 min ≈ **2.5 min/item**, so a 45 s sample window has only ~30 % chance of catching a
  write — which is why the first check showed zero growth and was *not* evidence of a hang.
- Confirmed over a 200 s window: **23 → 24 items.** Alive. **ETA ≈ 2.5 h (~20:45).**

GPU is saturated until then (the P10 and P7 smokes are PENDING behind the two sweeps on cluster priority),
so this tick went to the last big CPU-writable piece: **P6, the Jacobian / projection-matrix readout** —
a methods contribution with currently **zero code in the repo**. Instructed to build on the existing
`_ActGradCapture` (48_attribution_patching.py) rather than reinvent, to keep the concept and refusal targets
**strictly separate** (the project's cardinal rule), to stay directly comparable to the existing plain
projection lens (`phase8_readout.py`, same layer/position conventions), and to prove correctness against a
**closed-form derivative on a toy model** — that analytic check is what will make the readout trustworthy.

### Tick 11 — 2026-08-05 — P10 + P7 smokes launched; all 3 prep agents landed
Launched the **P10 decode-safe smoke** (716187) and the **P7 refusal-direction validation smoke** (716188)
alongside the two α sweeps. P7's harness validates all 32 layers for **two direction families side by
side** — `existing` (the shipped carrot/bomb-fit files, read-only) and `clearharm` (refit on the ClearHarm
train split) — using the *same* ablate/induce scopes the downstream harnesses actually use
(`AllPositionProjectOutMultiLayer` @ α=1.0, byte-identical to `phase_behav_refusal.py:145`; `AllPositionAdd`
@ layer L as in `phase_refusal_inject_calibrated.py:96`), with norm-matched random controls and a held-out
eval split. That side-by-side is what will tell us whether the carrot/bomb-fit directions were ever
appropriate for ClearHarm claims.

### Tick 10 — 2026-08-05 — α sweeps running; next GPU phases being wired
**P8.1 α sweeps are RUNNING** (716014 clearharm on n-802, 716015 curated on n-803, ~25 min in). Liveness
checked properly this time: their `.err` ends with a *completed* post-model-load tokenizer warning, i.e.
they are inside the (silent by design) generation loop — unlike the hung 714997, whose last `.err` line was
a *partial* weight-loading progress bar frozen at 54%. That distinction is the tick-8 lesson applied.

**Corrected a false claim in our own plan** (§5 P1b): it asserted "zero ClearHarm instruction pairs exceed
TF-IDF cosine 0.5". Recomputed: **max pairwise cosine 0.690, 3 pairs above 0.5.** The recommendation still
stands (the built v3's cross-split max is lower and no concept straddles), but paraphrase leakage is not
identically zero, so the **post-split near-duplicate audit is now marked REQUIRED, not optional.**

Fanned out 3 builders for the next GPU phases (code only, no launches):
- **P10** — wire the decode-safe re-run into `phase_behav_write.py`, keeping the old prefill-only arm
  alongside the new one so the difference is measurable in a single experiment. Explicitly warned the agent
  not to silently substitute a broader intervention: zeroing the whole MLP output at every position is
  **not** the same experiment as zeroing the write at the demo-codeword positions.
- **P7** — re-validate all 32 per-layer refusal directions. This is a real blocker: none of the 32 carries
  a `validation` key, only 5 layers were ever generation-validated, and **L12 FAILED** (induce_gain −0.333).
  Every per-layer refusal claim — including the calibrated depth-localization headline — currently rests on
  unvalidated directions.
- **P9** — build the Llama+ClearHarm GCG manifest and the 16-arm cell manifest. The split has no
  affirmative-target field, so targets must be joined from `data/manifests/clearharm_*.csv` on instruction
  text (id schemes don't match: 0/86 exact overlap).

### Tick 9 — 2026-08-05 — all 4 builders landed; P10 unblocked; v3 split built
Re-ran after the session reset; all 4 succeeded. Cleared the P10 blocker, built the v3 split, completed
validator coverage, and turned the P1 audit into a gate. Independently verified the BEHAV-WRITE
position-0 question (not affected) and the v3 zero-straddling claim. Suite 205 green.
α sweeps 716014/716015 still PENDING on cluster priority.

### Tick 8 — 2026-08-05 — killed a hung GPU job; builders re-queued after the limit reset
**Cancelled job 714997 (P2 v2 replication) — it was HUNG, not slow.** Started 14:12, still "Loading
weights" at 54% of 291 shards after ~3 h wall clock, and its `.err` had not been written since **14:25**
(2 h 45 m of silence) while holding a GPU with the critical-path α sweeps queued behind it. The first
shard alone took 141 s — NFS thrash, almost certainly the 98 %-full volume plus my own heavy git traffic
last tick. **No data lost:** P2's finding rests on the two v1 benches, which are the apples-to-apples
comparison against demo-only; v2 was a nice-to-have replication. Resubmit when the cluster is calmer.

⚠️ **Operational lesson worth keeping:** a job can sit in SLURM `R` state for hours having produced
nothing. `squeue` says RUNNING; only the log mtime tells you it is alive. Check
`stat -c %y logs/<job>.err` before assuming progress.

Session limit reset at 17:00 → re-queued all 4 builders (P10 `AllPositionMLPAblate`, the v3 split,
`audit_phase21_baseline.py`, validator schemas). α sweeps 716014/716015 still PENDING on cluster priority.

### Tick 7 — 2026-08-05 — ⚠ SESSION LIMIT; P8.1 full sweep launched; P1 audit done solo
**BLOCKER: the API session limit was hit — all 4 builders from tick 6 died with
"You've hit your session limit · resets 5pm (Asia/Jerusalem)".** No subagent work is possible until then.
Re-queue after 5pm: `AllPositionMLPAblate` (P10 blocker), the v3 split builder (P1b), the validator's
remaining 4 schemas, and `scripts/audit_phase21_baseline.py`. I worked single-threaded instead.

**P8.1 smoke PASSED (job 715366, 16 min)** — the α-sweep harness is correct:
- **α = 0.0 is an exact no-op** — `direct_refabl_a0.0` ASR and refusal_rate are identical to
  `direct_base` on both splits. This is the anchor that proves the sweep is wired right.
- refusal_rate falls monotonically with α (train direct: 0.667 → 0.333 at α .25–.75 → 0.000 at α ≥ 1.0).
- **the norm-matched random control is FLAT at every α** (ASR and refusal_rate constant across all 7) —
  specificity now demonstrated across the whole grid, not just at α = 1.0 as before.
- all 24 arms present on every row.
⇒ **Full sweeps launched: 716014 (clearharm 86), 716015 (curated 51)**, α ∈ {0, .25, .5, .75, 1, 1.5, 2},
random control at each α, `--save-gen` on, ~14 h budget. This unblocks the real Phase 8.

**P1 empty-generation audit — VERDICT: SAFE** (`reports/P1_BASELINE_AUDIT.md`, done inline).
The Phase 2.1 raw retains `response`, so emptiness is directly reconstructible (tested programmatically;
no text read). **0 of 411 generations are empty or whitespace-only** in either cohort — the missing EMPTY
branch in `14_behavioral_eval.py` was never reached and cannot have shifted any published number. All
**6 of 6** published rates recompute exactly (clearharm .1163/.2558/.3488, curated .2549/.0392/.2353).
The defect is still worth fixing as a latent trap for future runs with stronger interventions, but P1 is
unblocked on these grounds.

⚠ **Secondary finding (carry into P1):** truncation is heavy and cohort-asymmetric — `stop_reason=length`
on **25% of clearharm but 72% of curated** generations at `max_new_tokens=200`. It is common-mode across
conditions so it does not bias the DS-vs-direct contrast, but it is a plausible contributor to curated's
"complied-but-benign" gap (P8.0 §2.1) and the concept-dilution reading: an answer cut off before its
payload scores low regardless of refusal. **Recommend raising max_new_tokens for the corrected baseline
(behavioral harnesses already use 220) and recording `stop_reason` in every future behavioral run.**

### Tick 6 — 2026-08-05 — P8.1 α-calibration launched; P10/P1/P1b builders out
**Disk pressure resolved:** the volume was expanded — now 29T / 5.4T free / 82% (was 20T / 467G / 98%,
and git actually hit "Disk quota exceeded" mid-commit last tick). Plan §2.2 item 9 (archive off-NetApp)
is still worth doing but is no longer urgent.

Launched the **P8.1 α-calibration smoke** (job 715366) on the harness prepped last tick —
`--alphas 0,0.25,0.5,0.75,1.0,1.5,2.0`, with the norm-matched random control at *every* α and
`--save-gen` on. This is the blocking prerequisite for the real Phase 8: at α = 1.0 the design is
saturated (`I_max` = +0.174) and the interaction is undetectable; we need the α that lands
refusal-alone ASR in the 0.20–0.40 band, which restores `I_max ≥ +0.33`.

P2's v2 (116-example) replication still running (714997, ~58 min).

Fanned out 4 builders on disjoint files:
- **P10 blocker** — `AllPositionMLPAblate`, the decode-safe MLP ablation. The old BEHAV-WRITE null used
  `ComponentOutSwap`, whose position guard drops every position when `seq == 1`, so it was **prefill-only**;
  the test set includes a negative control pinning exactly that defect.
- **P1 prerequisite** — audit the empty-generation exposure in `14_behavioral_eval.py` (no EMPTY label,
  no `empty_rate` guard) which produced the published Phase 2.1 baseline. Verdict required:
  SAFE / SUSPECT / MUST-RERUN.
- **P1b** — build the actual v3 split: concept-level `intent_cluster` (v1's per-instruction hash made the
  leakage check vacuous — 14/43 concepts and 17/21 codewords straddle), disjoint codewords per split,
  all 6 conditions, zero straddling.
- **Validator schema coverage** — teach it the 4 remaining families (phase4*/phase5b/phase7*/phase9*) so
  its exit code means something over the whole tree.

### Tick 5 — 2026-08-05 — P2 result lands; all review defects fixed and independently re-verified
Read out P2 on both v1 benches (v2 still running) → a new result: all-occurrence patching ~doubles the L9
write necessity, against a count-matched control. Wrote `reports/PHASE2_ALL_OCCURRENCES.md`. Collected all
4 fixers and re-verified every fix myself rather than trusting the reports: 462→0 false mismatches,
empty_dirs 0→20, judge gate 0/1, 34→0 fabricated job ids.

### Tick 4 — 2026-08-05 — adversarial review lands; P8.0 corrected; P2 full runs launched
6 agents returned. The review found a HIGH measurement-instability threat to P8.0 (verified by me), a
false-independence claim, and a degenerate curated cell — all now corrected in the report. P9.0's GCG
selection bug fixed. P1b recovery quantified (+60% items but only +2 concepts). P2 smoke passed and the
three full runs are on GPU. Launched 4 fixers for the review's HIGH/MEDIUM code defects: validator false
positives (44/91 dirs), tolerance fallback, dead ratchets, fabricated job ids in 34 RUNMETA, the
n_for_power truncation (12 of 16 printed ">4000" values are wrong), and two judge-adoption hazards.
**Good news from review:** the torch stub is clean (1464 attributes raise, 6 served) and adopting
`behav_judge` would change **no** published number (0 blank responses / 0 null scores across 1451 rows).

### Tick 3 — 2026-08-05 — all 7 agents in; 2 defects fixed; provenance applied; P2 smoke launched
Collected the remaining 4 agents. Fixed both newly-found primitive defects and cleared the xfail markers
(suite 191 green). Applied the provenance backfill and registry. **Corrected the P10.0 story** — the graded
re-analysis fails its specificity control, so §0.5's "the null flips" is too strong. Launched the P2
all-occurrence smoke (jobs 714854/714855, `DSPOS=all`, zero new code — the flag existed and was never run).
Fanned out 3 adversarial code reviewers + P9.0 GCG bug fixes + P1b lexicon recovery + P8.1 α-sweep prep.

### Tick 2 — 2026-08-05 — P8.0 verified; judge + audit landed
3 of 7 agents returned. Independently re-derived the P8.0 interaction from scratch before accepting it
(exact match). Recorded the artifact baseline. Found and documented the `14_behavioral_eval.py` EMPTY-label
bug. 4 agents still running (provenance core, validators, P10.0 graded re-analysis, primitive tests).

### Tick 1 — 2026-08-05 — P0.1 artifact preservation shipped (commit `27a4cfe`)
Set up the 30-min loop. **Un-ignored the evidence:** 287 summary files + 219 SLURM logs (13 MB) now in git;
raw.jsonl / gens / npz / pt remain archive-only. Three-pass safety filtering — the third pass (scanning the
actually-staged blobs) caught `ds_gcgopt_692819.out`, which echoes the evolving GCG suffix every step and
which the first two heuristics missed. 20 `.out` files and all `.err`/`.log` are held back pending manual
redaction. **Deviation from plan §2.2 item 2**, which said commit logs wholesale — reported to Omer.
