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

## Tick log (most recent first)

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
