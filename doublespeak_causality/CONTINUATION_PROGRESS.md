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
