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

## Tick log (most recent first)

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
