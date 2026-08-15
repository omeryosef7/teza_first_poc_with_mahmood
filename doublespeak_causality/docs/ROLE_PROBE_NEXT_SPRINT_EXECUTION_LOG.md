# ROLE_PROBE_NEXT_SPRINT — EXECUTION LOG

Required by `docs/ROLE_PROBE_NEXT_SPRINT_PLAN.md` §0. Every decision, job,
failure, deviation, correction, and result goes here as the sprint proceeds.

Append-only. Newest entries at the bottom of §3. Never edit a past entry to make
it look better — add a correction entry instead.

Sprint start: **2026-08-14**
Branch: `behavioral-causality-sprint`
Plan: `docs/ROLE_PROBE_NEXT_SPRINT_PLAN.md` (single source of truth, incl.
Appendix A = upstream code review)

---

## 1. STATUS DASHBOARD

Legend: ☐ not started · ◐ in progress · ☑ done · ⊘ blocked · ✗ failed/abandoned

### Gates

| Gate | What it tests | Status |
| --- | --- | --- |
| **Gate 0** | Jobs reconciled, threshold frozen, split policy explicit, registry/deviation logs current, manifest committed | ☑ **PASSED 2026-08-14** (see E6) |
| Gate 1 | Contextual Bombness probe validity | ☑ **PASSED 2026-08-14** (E15) |
| Gate 2 | Outcome probe beats trivial baselines; refusal direction still better-supported causally | ☑ **2026-08-14** (E16; frozen refusal_L18 projection = Refusalness readout) |
| Gate 3 | Frozen latent-state prediction report written | ☑ **2026-08-14** (E16, `DUAL_STATE_PREDICTION.md`) |
| Gate 4 | Bombness causal claim admissible (manipulation check + controls + holdout) | ☑ **PASSED 2026-08-14** (E19; + 2×2 E20, sufficiency E24) |
| Gate A–F | Decision tree §18 | ☑ A–D resolved: Gate A/B/C pass (Gate 1); Gate D = **Story A** (Bombness epiphenomenal) → §13.x says do NOT optimize Bombness as an attack objective |

### Phases

| Phase | Plan § | Status | Note |
| --- | --- | --- | --- |
| Upstream import | 2A.1 | ☑ | commit `ec333c40`, no `.git`, MIT retained |
| Upstream code review | 2A.2 | ☑ | Appendix A of the plan |
| **Phase 0 — governance repair** | 4 | ☑ | registry 395→573, bug log B6–B18, manifest frozen |
| Phase 1 — Bombness probe | 5 | ☑ | **GATE 1 PASSED**: holdout AUC 0.997, cross-codeword, ⊥ refusal at codeword |
| Phase 2 — refusal/compliance readout | 6 | ☑ | frozen refusal_L18 projection = Refusalness readout (E16) |
| Phase 3 — latent-state experiments | 7 | ☑ | **Refusalness predicts DS success (0.98), Bombness at chance (0.59)** |
| Phase 4 — causal interventions | 8 | ☑ **COMPLETE** | **STORY A**: necessity −0.05; 2×2 interaction +0.00; **sufficiency +0.05** (E24); refusal +0.24/+0.33/+0.36. Bombness neither necessary, sufficient, nor gated |
| Phase 5 — component patching | 9 | ☐ | follow-on |
| Phase 6 — D3 scope-matched control | 10 | ☐ | follow-on (asymmetry thread) |
| Phase 7 — Phi concept completion | 11 | ☐ | follow-on (B16) |
| Phase 8 — cross-model replication | 12 | ◐ | cross-COHORT done (E21/E22): Gate 1 replicates, prediction cohort-specific, generated causal inconclusive. Cross-MODEL (Phi/Qwen) open |
| Phase 9 — attack objective | 13 | ✗ N/A | Gate D = Story A → plan §13 says do NOT optimize Bombness (epiphenomenal) |
| Phase 10 — second corpus / power | 14 | ☐ | follow-on |
| Phase 11 — Section 20 hygiene | 15 | — | concurrent §20 session's thread; §20.7 seeds 42/43/44 all complete |

### Compute

| | |
| --- | --- |
| SLURM concurrency cap | 6 (project rule) |
| GPU work permitted | **Yes** — Gate 0 passed; slots vary (share with concurrent §20 session) |
| Session GPU jobs run | probe extractions (clearharm 757886, generated 757957), Phase-4 (757931/757943/757967/757992) |

---

## 2. FROZEN DECISIONS

Anything here changes only via a logged deviation entry in §3 **and** a row in
`BUG_AND_DEVIATION_LOG.md`.

| # | Decision | Set in | Status |
| --- | --- | --- | --- |
| D1 | Probe fit in **our raw post-block residual space** (`hidden_states[L+1]`), not upstream's RMSNorm-normalised mid-block space. Normalised space kept as a robustness arm. | Plan Appendix A §A3.1 | **FROZEN** — rationale: Phase 4 requires steering the direction; a direction is only steerable in the space our hooks write to. Deliberate deviation from upstream methodology. |
| D2 | Binary malicious = StrongREJECT ≥ 0.5 for all new work; continuous score always saved. | Plan §3.6 | pending Gate 0 confirmation that raw scores exist to rebuild the sensitivity table |
| D3 | Probe estimator: L2 logistic regression, `fit_intercept=True`, sklearn (not cuML). Secondary: difference-of-means. | Plan §5.1, App. §A8 | proposed, freeze in manifest |
| D4 | Split key = underlying item (codeword × template × harmful-instruction cluster), **never** the rendered prompt index. | Plan §3.5, App. §A9.1 | proposed, freeze in manifest |
| D5 | Explicit `position_ids` / length-matched pairs; position-only and length-only baselines are **blocking** Gate-1 controls. | App. §A9.2 | proposed, freeze in manifest |

---

## 3. CHRONOLOGICAL LOG

### E0 — 2026-08-14 — Sprint plan committed to repo

Plan written to `docs/ROLE_PROBE_NEXT_SPRINT_PLAN.md`. Sections 0–22 verbatim as
supplied.

### E1 — 2026-08-14 — Upstream reference implementation imported (§2A.1) ☑

Snapshot of `role-confusion/prompt-injection-as-role-confusion` at
`third_party/prompt_injection_role_confusion/`.

| | |
| --- | --- |
| Commit | `ec333c40fd43fe991e1ebf66765051b6d7e35784` (`master`, 2026-05-31) |
| Method | ZIP archive via curl → unzip → rsync; temp dir removed |
| Files / size | 110 / 7.3 MB |
| `.git` present | **No** — `find … -name .git` returns nothing; no gitlink in index |
| License | MIT, `LICENSE.md` retained unmodified |
| Provenance | `SOURCE_INFO_LOCAL.md` written |

Upstream source not modified. Treated as frozen.

### E2 — 2026-08-14 — Upstream code review completed (§2A.2) ☑

Full read of the pipeline: `demo/simple_test_helpers.py`, `demo/role-probe-demo.ipynb`,
`utils/probes.py`, `utils/loader.py`, all 11 `utils/pretrained_models/*.py`,
`experiments/role-analysis/02-train-role-probes.ipynb`,
`experiments/cot-forgery-role-confusion/03-project-role-probes.ipynb`,
`experiments/cot-forgery-role-confusion/04-analyze-injection-probe-results.ipynb`.

Review is **Appendix A** of the plan (single-file policy, per user request).
Ten numbered findings (§A9.1–§A9.10). The three that change our design:

1. **§A3 — different probed tensor.** Upstream probes
   `post_attention_layernorm(resid_mid_L)` — the RMSNorm-normalised, mid-block
   residual (the MLP's literal input), identical across all 11 architectures.
   Our refusal direction lives in the raw post-block residual. Cosines across the
   two spaces are meaningless without a change of basis, and RMSNorm is not
   linear so a hyperplane there is not a hyperplane here. → Decision **D1**.
2. **§A9.9 — no causal intervention exists upstream.** Verified by grep over
   `coef_`, `steer`, `ablat`, `patch`, `intervent`, `orthogonal`, hook-writes.
   `coef_` is never read; the only hooks are read-only extraction. Their result
   is measurement + correlation. Our Phases 4–5 are genuinely novel, and our
   existing representation≠behavior dissociation is exactly the confound their
   design cannot exclude.
3. **§A9.1 / §A9.2 — two confounds we cannot inherit.** Their split is on
   rendered-prompt index, so the same base text appears in train under one label
   and test under another (benign for them, fatal for us). And
   `position_ids = arange(0,N)` with left padding gives length-dependent RoPE
   positions — our already-twice-logged absolute-position bug class. → **D4, D5**.

Reuse plan recorded in Appendix A §A11 (Upstream → Our Implementation Mapping).
Their plumbing (`ReconstructableTextDataset`, `run_and_export_states`,
`run_projections`) is clean and will be **ported, not rewritten**.

### E3 — 2026-08-14 — Repo state confirms the audit's governance finding

Login-node inspection only.

| Quantity | Value |
| --- | --- |
| Entries under `outputs/` | **606** |
| `EXPERIMENT_REGISTRY.csv` rows | 395 (+ header) |
| Registry latest date | **2026-08-05** |
| `BUG_AND_DEVIATION_LOG.md` latest entry | **2026-08-08** |

⇒ The entire Asymmetry / Section-20 sprint (2026-08-11 → 08-14) is **unregistered**,
and post-08-08 deviations are **unlogged**. This is exactly what plan §4.2 exists
to repair. Confirms the 2026-08-14 audit rather than the prose status.

### E4 — 2026-08-14 — Live SLURM state (§4.1, partial)

Six jobs RUNNING, all named `gcg_perprompt` — **at the 6-job project cap**:

| Job ID | Node | Elapsed | Time left | Submitted |
| --- | --- | --- | --- | --- |
| 757741 | n-304 | 3:37 | 12:22 | 2026-08-14T12:34:32 |
| 757711 | n-301 | 4:37 | 11:22 | 2026-08-14T11:35:10 |
| 757709 | n-303 | 4:40 | 11:19 | 2026-08-14T11:32:08 |
| 757697 | n-302 | 5:09 | 10:50 | 2026-08-14T11:02:57 |
| 757672 | n-350 | 5:57 | 10:02 | 2026-08-14T10:14:51 |
| 757662 | n-305 | 6:09 | 9:50 | 2026-08-14T10:02:57 |

Consequences, both binding:
- **No new SLURM job may be launched** until one finishes (cap = 6).
- **No GPU science may be launched anyway** — Gate 0 is unmet.

⇒ Correct use of the current window is Phase 0, which is entirely login-node work.
Detailed per-job identification (seed/shard/what it produces) is in progress —
see E5.

**No duplicate jobs were submitted.** Nothing was cancelled.

### E5 — 2026-08-14 — Phase 0 audit fan-out launched (§4)

Seven independent read-only audits dispatched in parallel (workflow
`wf_7224d5d8-f29`). All login-node, no GPU, no writes.

| Agent | Question it answers | Feeds |
| --- | --- | --- |
| `inventory-outputs` | 606 entries: which have RUNMETA/config/manifest/DONE/raw? which have none? which are from 08-11→08-14? | §4.2 governance report |
| `registry-parse` | registry schema, date coverage, registered `output_dir` set, whether `update_registry.py` can backfill | §4.2 backfill |
| `slurm-reconcile` | what each of the 6 running jobs actually is (seed/shard/output), owed items, true §20.7 state from artifacts | §4.1, E4 completion |
| `threshold-audit` | every 0.25 vs 0.5 site; whether continuous scores persist so a sensitivity table is rebuildable offline | D2 freeze |
| `buglog-gaps` | which of the 8 required deviations are documented but unlogged, with exact source refs | §4.2 bug log backfill |
| `infra-catalogue` | canonical model loading / extraction / hook / refusal-direction APIs to reuse | Phase 1 (write little new code) |
| `splits-audit` | existing splits, leakage status, whether a genuinely unexposed holdout exists | D4 freeze, confirmatory design |

Subagents were explicitly constrained to metadata/schema/numeric work and
forbidden from reading or quoting harmful-prompt or generation text — this repo's
data files contain such text, and prior sessions have had subagents terminated by
the cyber-safeguard classifier for reading it. Structural/scalar delegation only.

### E6 — 2026-08-14 — Phase 0 audit returned; GATE 0 PASSED ☑

All 7 audit agents succeeded (491k subagent tokens, 0 errors). Acted on results:

**Registry backfill.** `scripts/update_registry.py --apply` (purpose-built,
idempotent, dry-run-default, writes `.bak`): **395 → 573 rows (+178)**, 168 with
git commits, 0 existing rows rewritten, 0 flagged-missing. asym coverage **1 → 47**.
Post-apply re-run = **0 to add** (idempotent). Verified: **545/545 on-disk output
dirs now registered, 0 missing.**

**Bug-log backfill.** Appended **B6–B18 + V1** to `BUG_AND_DEVIATION_LOG.md`
(95 → 260 lines), each with an immutable source citation. All 8 plan-§4.2-required
items captured (GCG candidate-selection bug B6, v1 leakage B7, refusal-layer
off-by-one B8, test-selected dose B12, missing GCG raw dirs B14, threshold conflict
B13, Section-20 deviations B15, stale claims B14/B15/B17). Plus the two open items
that ARE later sprint phases: B11 (D3 scope-match = Phase 6), B16 (Phi concept half
= Phase 7).

**Threshold contract frozen (D2 confirmed).** Two families found: legacy 0.25
(`behav_judge.py` + numbered scripts + `phase_behav_*`) vs newer 0.5 (`asym_p2_judge`,
`asym_p201`, `26_eval_p9`). **Continuous scores ARE persisted** → offline
sensitivity table is rebuildable. Freeze **0.5 for new work**; do NOT flip
`behav_judge.py`'s constant (a desync guard `validate_experiment_coverage.py` would
fire on every historical run). Logged B13.

**Split policy frozen (D4 confirmed).** v3 (`clearharm_doublespeak_v3.json`) is the
leakage-0 corpus: train 162 / dev 82 / test 80, **0 straddling** concepts/codewords/
clusters, **104/60/60 disjoint codewords** each used once. **CARROT is in DEV
(held out from train fitting); BOMB in no split** — satisfies §5.2's "hold CARROT
out." The v3 schema already carries the two-key structure this sprint needs:
`codeword` (declared) vs `target_concept`/`normalized_concept` (decoded), all six
conditions materialized, `wrong_concept`/`wrong_codeword` controls, and
**precomputed `codeword_occurrences_templated` token positions** — so no substring
heuristic is needed (upstream's brittle span-finding is unnecessary for us).

**Infra catalogue (Phase 1 will write almost no new extraction code).**
- `ds_common.load_model` — bfloat16, sdpa, revision **not pinned by default** → the
  sprint pins the resolved HF sha in RUNMETA (manifest).
- `pair_common.capture_components(lm, templated_text, probe_word, components, positions)`
  — one forward pass → `{resid_pre, attn_out, mlp_out, resid_post}` × `{codeword_last,
  following, final_prompt, first_generated}`. **`resid_post` == `hidden_states[L+1]`
  == our D1 space.** This IS the Bombness extraction primitive.
- `ds_common.LayerPatch(model, layer_idx, positions, vector, mode, alpha)` — modes
  `replace`/`add`/`project_out` = activation-patch / steering / ablation, per-position,
  with alpha. This IS the Phase-4 intervention primitive.
- Indexing convention confirmed in 3 independent places (D1/B8 regression test).

**Deliverables committed this gate:**
`reports/GOVERNANCE_REPAIR_2026_08_14.md`, `configs/manifests/role_probe_sprint_v1.json`
(FROZEN, JSON-validated), backfilled registry + bug log.

**GATE 0: all five conditions met.** Jobs reconciled (E4/§5), threshold frozen,
split policy explicit, registry+bug log current, manifest committed. GPU science
still blocked only by the 6/6 concurrency cap — the §2A.5 sanity reproduction
launches on the first free slot.

**New open question raised → Q2 below** (confirmatory holdout: is v3 test
probe-unexposed enough to serve, or construct a fresh one?).

### E7 — 2026-08-14 — Phase 1 foundation: corpus supports the probe with zero new data ◐

Verified offline (structure only, no prompt text) that the v3 corpus already
provides the headline paired-binding construction (plan §5.2), so **no new data
generation is needed** for the Bombness probe:

- All **324 examples** carry all six conditions.
- The codeword appears in **doublespeak / neutral / benign** (surface-identical
  across them); absent from `direct` (which uses the real concept).
- **All 324 codewords are single-token** (`single_token_primary`) — clean
  position-anchored probing.
- Token positions are **precomputed** (`codeword_occurrences_templated` spans), so
  upstream's brittle substring/heuristic span-finding (App. §A6) is unnecessary.
- Two-key structure is native: `codeword` (declared) vs `target_concept` /
  `normalized_concept` (decoded), plus `wrong_concept` / `wrong_codeword` = the
  shuffled/unrelated controls.

**Headline label (frozen in `probe_dataset.py`):** positive = `doublespeak`
(codeword bound to harmful target → Bombness high), negative = `benign` (same
codeword bound to a benign concept → Bombness low). Within a matched pair the
surface codeword is byte-identical, so the token-identity control is satisfied by
construction — the probe must decode the *contextually assigned* identity, exactly
the role-confusion analogue.

**Built `src/probes/probe_dataset.py`** (pure Python, no torch — the
corpus→labeled-extraction-spec step; extraction that needs the model is separate).
Emits ids/splits/labels/codeword-token-ids/integer spans only, never prompt text.
Includes `assert_split_discipline()` which **raises** on any codeword/concept leak,
CARROT-in-train, or BOMB-as-codeword (D4 enforced in code, not just prose).

CLI output: 972 items / 648 labelled; train 162+162 (104 cw / 97 concepts), dev
82+82 (60 cw, incl. CARROT), test 80+80 (60 cw); all single-token; discipline OK.

**Tests `tests/test_probe_dataset.py` — 7 passed** (GPU-free). Includes a
planted-leak test proving the discipline guard actually fires (not vacuous). One
self-caught bug: initial test assertion had the label→condition mapping reversed
(pair[1]=doublespeak, not benign); fixed the test, module was correct.

Reuse so far (plan §2A.9 / App. §A11): extraction will wrap
`pair_common.capture_components` (resid_post = D1 space); no upstream extraction
code needed to be copied for this step. `activation_extraction.py` +
`contextual_identity_probe.py` are the next modules — the first needs a GPU node to
run, so it is authored-then-SLURM-launched once a slot frees.

### E8 — 2026-08-14 — Phase 1 code complete (CPU-tested); GPU extraction queued ◐

Authored the rest of the Phase 1 pipeline. All reuse existing infra (plan §2A.9);
no new hooks written.

**`src/probes/contextual_identity_probe.py`** (fit + eval, numpy/sklearn, no torch):
L2 logistic (default penalty; `penalty='l2'` is deprecated in sklearn 1.9 → rely on
the default) + difference-of-means; C selected on dev; **bootstrap AUC CI resamples
EXAMPLES not rows** (App. §A9.6); ROC-AUC + balanced accuracy; a **train/eval
example-leak guard that raises**; and the Gate-1 controls (label-shuffle,
norm-matched random direction, scalar-nuisance baseline, cosine geometry).

**`src/probes/activation_extraction.py`** (SLURM/GPU entrypoint): wraps
`ds_common.load_model` + `pair_common.capture_components` to pull `resid_post`
(= `hidden_states[L+1]`, D1) at `codeword_last` (query codeword) and `final_prompt`
(decision token), all layers. **Single-example forward passes (batch 1, no padding)**
→ sidesteps the left-pad/`arange(0,N)` position drift entirely (D5 / B9). A
**preflight cross-checks** `capture_components`' resolved `codeword_last` against the
corpus's precomputed query span and **aborts on mismatch** — the regression test for
the absolute-position bug class. Emits `acts.npy` + `items.jsonl` (no prompt text) +
`RUNMETA.json` + `DONE.json`. Verified the corpus was tokenized with the same Llama
tokenizer (`_meta.tokenizer`), so the cross-check is well-posed.

**`src/probes/smoke_fit.py`**: the §2A.5 pipeline sanity check — grouped half/half
split, **fixed C** (a mechanics check must not tune C on its own eval slice),
per-layer AUC at the query position. Self-review caught the C-on-eval leak and fixed
it to fixed C before commit.

**`slurm_scripts/run_probe_extract.slurm`**: MODE=smoke|full, reuses the
`run_gcg_perprompt` env + GPU-guard idioms (incl. the unreachable-error-branch fix
that killed 757702). Smoke mode extracts a slice then runs `smoke_fit`.

**Tests: 22 GPU-free, all passing.** `test_probe_dataset` (7) + `test_contextual_
identity_probe` (8, incl. smoke_fit on a synthetic run dir). Synthetic activations
with a planted signal verify: probe recovers signal (AUC>0.9), label-shuffle and
random-direction at chance, leak guard fires, no-signal at chance, best-layer
localization. Two self-caught bugs this tick (both test-side, modules correct):
signal=0 made pos/neg bit-identical (degenerate diff-of-means) → added independent
noise; missing `json` import in the test.

Env note: tests run under conda env **`poc_stage2`** (numpy 2.4.6, sklearn 1.9.0);
the login `python3` has no numpy. Recorded for the loop.

**Ready to launch the moment a GPU slot frees** (still 6/6): `sbatch
slurm_scripts/run_probe_extract.slurm --export=ALL,MODE=smoke,COHORT=clearharm`.
If the preflight aborts on a position offset, that is the corpus-span vs
`resolve_positions` tokenization reconciliation point — investigate before trusting
any extraction (do NOT paper over it).

### E9 — 2026-08-14 — Threshold sensitivity table built (Gate-0 §3.6 deliverable) ☑

GPU still 6/6, so did the flagged GPU-free Gate-0 item: the 0.25/0.5/continuous
StrongREJECT sensitivity table for the headline behavioral claims, rebuilt offline
from persisted continuous scores.

**`scripts/threshold_sensitivity.py`** — reuses `mcnemar_exact` from
`phase_behav_refusal.py`; paired bootstrap 10k; reads only `*_score`/`*_label`
columns, never generation text. Verified ΔASR = (b−c)/n by hand against output.
py_compile clean. Self-caught one bug: a malformed f-string in `render_md` (an
`f|...replace()` hack) — fixed to a clean row before running.

**`reports/THRESHOLD_SENSITIVITY_2026_08_14.md`** over the three quantization
precisions (clearharm test, n=42). Findings:

1. **Refusal ablation is threshold-robust:** `direct_refabl_a1.0` vs `direct_base`
   ΔASR is identical/near-identical at 0.25 vs 0.5 (bf16 +0.286/+0.286, 8bit
   +0.262/+0.262, 4bit +0.571/+0.548), continuous CIs exclude 0. The recompute
   **matches the audit's A4 corrected numbers exactly** → confirmed raw-reproducible.
2. **New paired result: `ds_base` vs `direct_base` ≈ 0 at both thresholds** (all
   McNemar p=1.00, continuous CIs straddle 0) — on ClearHarm the doublespeak
   framing alone does not raise ASR over the direct ask; the behavioral lever is
   refusal suppression. A clean behavioral restatement of the representation≠
   behavior thesis, threshold-robust. Bounded (n=42), not exact-zero.
3. **Score↔label integrity: 84/84 agreement** in every contrast — no silent
   corruption in these files.

**Implication (B13):** freezing 0.5 for new work changes no headline conclusion
here. Gate-0 §3.6's "sensitivity table for major historical claims" requirement is
now satisfied for the refusal-ablation headline; extend to other RAW-reproducible
claims as those files are touched.

Lesson logged: the script rewrites the whole report file, so the findings section
must be re-added after the final run (or moved into the script) — did the latter by
hand this time.

### E10 — 2026-08-14 — Slot-contention decision: WAIT, do not cancel (user)

User asked whether to cancel non-plan SLURM jobs and launch what we need. Checked:
the 6 running `gcg_perprompt` jobs are **§20.7 600-step work = Phase 11 §15.1 of
THIS plan** (finish seeds 43/44), not off-plan; seed 42 done 37/37, **seed 43
35/37 (both shards on their last prompt)**, seed 44 24/37; and a **concurrent
session is actively babysitting them** (`quiet tick:` commits). So the user's
condition ("not in the plan and we don't need it") is not met.

Presented the options; **user chose "Wait ~1h" (recommended).** Nothing cancelled.
Seed 43's two shards are on their final prompt, so 2 slots free on their own within
~1h with zero wasted compute and no disruption to the concurrent §20 loop. The
probe smoke extraction (1 slot, ~2h) launches on the first free slot.

Contention note: the concurrent session's OWED launch order queues the §20.1 μ
sweep for freed slots, so there is a mild race. The probe smoke needs only ONE
slot; if the μ sweep grabs both first, the next slot-free cycle catches the probe.
Arming a Monitor on `squeue < 6` to launch promptly rather than waiting for the
30-min cron tick.

### E11 — 2026-08-14 — First GPU job launched: probe smoke extraction 757877 ◐

While waiting on the slot, authored `gate1_eval.py` (the full Gate-1 verdict) and
its tests (25 GPU-free tests total now), and fixed a self-review gap: extraction
now persists `codeword_last_idx` + `seq_len` per item so the position-only /
length-only Gate-1 controls (D5) are computable. Self-caught bug: the label-shuffle
control was a single noisy permutation (0.79 on strong signal) → averaged over 10
seeds (0.48), matching the random-direction convention.

Slot freed as predicted: both seed-43 shards finished, freeing 2 slots. The
concurrent session took one for `asym_p2` (757867); I launched the probe smoke
extraction into the other. **`sbatch --export=ALL,MODE=smoke,COHORT=clearharm
run_probe_extract.slurm` → job 757877** (PENDING/Priority). Total 6/6, at cap,
respected.

757877 will: extract `resid_post` at query-codeword + decision token for the first
24 clearharm items (all 6 GPU-guard idioms), run the position preflight against the
corpus spans, then `smoke_fit` for a per-layer above-chance AUC. This is the §2A.5
pipeline sanity check AND the first real Bombness signal. **Watch for:** (a)
preflight ABORT = corpus-span vs `resolve_positions` tokenization offset to
reconcile before trusting extraction; (b) smoke_fit "mechanics_only" if the 24-item
slice is single-split (expected — smoke slice is dev-heavy); (c) an above-chance
best-layer AUC = green light for the full extraction. Completion waiter armed.

### E12 — 2026-08-14 — Smoke 757877 FAILED at preflight (by design); root-caused + fixed ☑

**The preflight did exactly its job.** 757877 aborted with
`position mismatch ... capture=179 corpus_query_last=209 (B9 -- aborting)` — the
absolute-position bug class the plan flags, caught before any wrong-position
activation was extracted. (Also: it landed on a V100 node; my fixed GPU guard
passed cleanly — the 757702 V100 death was the old guard's unreachable-error
branch, since fixed.)

Root cause (diagnosed offline, tokenizer only, no GPU, no harmful text printed):
- The corpus `*_prompt` fields are **raw** (no chat template); I was passing the raw
  string to `capture_components`. Raw → last codeword at token 179.
- The corpus `codeword_occurrences_templated` spans are in **chat-templated** token
  space. Chat-templating the user message (35-token template prefix) puts the last
  codeword at **209 = the corpus span exactly**.
- Further: the corpus spans are **doublespeak-specific** (n_occ≈13 = demos+query).
  Benign/neutral are different strings, so the codeword lands elsewhere and there is
  **no corpus anchor** for them — my first preflight wrongly compared all 3 conditions
  to the doublespeak span (24/36 spurious mismatches).

**Fix (reuses canonical infra, plan §2A.9):**
1. `_templated_prompt` now applies `ds_common.apply_template` (single user turn,
   `add_generation_prompt=True`) before extraction — matching the corpus spans AND
   how the model is actually attacked (the behavioral harness templates the same way).
2. `preflight_positions` anchors **only doublespeak** against corpus spans; benign/
   neutral are confirmed to resolve via `resolve_positions` (the same validated infra),
   with no corpus anchor. Returns `(n_ds_checked, n_other_resolved)`.

Verified offline over 36 items: **12 doublespeak anchored (all match), 24 benign/
neutral resolved.** New regression test `tests/test_extraction_positions.py` (2
tests, loads the real tokenizer offline, skips if uncached) locks this and proves the
anchor is load-bearing (raw prompt fails it). **Full probe suite: 20 GPU-free tests
passing.**

Scientific note: extracting from the chat-templated prompt is the correct choice on
its own merits — the probe now reads the codeword representation as the model
processes it under attack, comparable to the refusal-direction work. Relaunching the
smoke on the next free slot.

### E13 — 2026-08-14 — Smoke 757883 PASSES: pipeline works end-to-end (§2A.5) ☑ — with an honest caveat

757883 COMPLETED (48s on V100 after model load). Preflight passed (8 doublespeak
anchored to corpus spans, 16 benign/neutral resolved). Extraction produced
`acts[24, 32, 2, 4096]` (24 items × 32 layers × 2 positions × 4096 hidden) + RUNMETA
+ DONE. `smoke_fit`: per-layer AUC at the query codeword, best **L1 AUC 1.000**,
near-1.0 at almost every layer. Artifact:
`outputs/probe_bombness_smoke_clearharm_20260814_145913_757883/`.

**§2A.5 pipeline sanity check: PASS.** The extraction → probe pipeline runs
end-to-end and the signal is decodable.

**Honest caveat — this is NOT a validity result, and AUC≈1.0 is a FLAG not a win:**
- n = **4 eval examples** (grouped half/half on the 24-item smoke slice). Perfect
  separation is trivial at this n and says nothing about generalization.
- Near-perfect AUC even at **L0** (0.875) is suspicious: the doublespeak (positive)
  and benign (negative) prompts differ in the ENTIRE demonstration block — demos,
  structure, and **length** (e.g. example 0: doublespeak codeword at tok 209 vs
  benign at 223). So the probe may be reading "is this a doublespeak-structured
  prompt" (trivial surface confound) rather than "is the codeword bound to a harmful
  concept" (the real Bombness question). This is exactly the confound §5.2 / App.
  §A9.1 warn about.
- **This is what the Gate-1 blocking controls are for.** The position-only and
  length-only baselines (D5) will reveal whether the seq-length / codeword-position
  difference between doublespeak and benign explains the signal. If those controls
  approach the probe AUC, the naive contrast is confounded and Gate 1 correctly FAILS
  — at which point the fix is a length/structure-matched contrast, not a probe tweak.

Do NOT report "Bombness is decodable" off this smoke. The claim awaits the full
extraction (train 162 / dev 82 / test 80) + all 9 controls + CARROT transfer.

The extraction stores per-condition activations regardless of which contrast Gate 1
ultimately uses, so the full extraction is not wasted even if the positive/negative
definition is later refined.

**Next:** launch MODE=full COHORT=clearharm (170 ex × 3 cond = 510 items, ~20-25 min
on V100), then run `gate1_eval.py` on the login node (CPU). 6/6 now (concurrent
session took the slot); slot-waiter armed for the full launch.

### E14 — 2026-08-14 — Offline confound preview: length/position are near-chance ☑

Before spending the full GPU extraction, computed the two most mechanical Gate-1
controls **offline** (tokenizer only, no GPU) over the full n=340 clearharm labelled
set (170 doublespeak / 170 benign):

| control | AUC | detail |
| --- | --- | --- |
| **length-only** | **0.554** | doublespeak median len 232 vs benign 236; ranges overlap heavily ([150,281] vs [197,284]) |
| **position-only** | **0.557** | doublespeak median codeword pos 219 vs benign 220 |

Both near chance. So:
- The smoke's AUC≈1.0 (E13) was **n=4 overfitting, not a length/position confound** —
  the corpus (P8.5 matched-condition build) length-matches doublespeak and benign by
  design.
- The Gate-1 length/position controls will sit ~0.55, well below any real probe
  signal → a high full-n probe AUC would reflect something beyond surface length.

**Remaining (subtler) confound the smoke can't rule out:** even length-matched, the
doublespeak vs benign demo BLOCKS differ in content (harmful-concept demos vs
benign-concept demos). A probe could read "the demos were about a harmful topic"
rather than "THIS codeword is bound to a harmful concept." This is adjudicated by the
**CARROT cross-codeword transfer** (train without CARROT, test on it — held-out
binding must generalize) and the **token-identity control** — both already in
`gate1_eval`. That is the real Gate-1 question; the mechanical confounds are handled.

Net: Phase-1 design is materially de-risked. Proceeding to the full extraction is
warranted. Slot-waiter armed.

### E15 — 2026-08-14 — GATE 1 PASSED: contextual Bombness is real ☑ (headline result)

Full clearharm extraction (757886) COMPLETED: `acts[510, 32, 2, 4096]`, preflight
passed. Ran `gate1_eval` (CPU) at both primary positions. **All five Gate-1 criteria
met.** Full report: `reports/BOMBNESS_PROBE_VALIDATION.md`.

| criterion | result |
| --- | --- |
| 1. held-out discrimination | query codeword **AUC 0.997** [0.990,1.000] @L11; decision token 0.964 |
| 2. cross-codeword transfer | holdout has **22 codewords, 0 overlap with 27 train** → the holdout IS the transfer test |
| 3. trivial controls near chance | label-shuffle 0.465, random 0.529, position 0.578, length 0.587, token-id **0.500** (exact, by matched-pair design); max 0.587 vs probe 0.997 |
| 4. dev/holdout agree | 0.9995 vs 0.997 |
| 5. geometry interpretable | **cos(Bombness, refusal_L18) = +0.091 at codeword (⊥), +0.468 at decision token** |

**Scientific reading.** Bombness — the model's internal encoding of "this codeword is
contextually bound to a harmful concept" — is a real, robustly decodable latent
variable that generalizes to unseen codewords and is geometrically **orthogonal to the
refusal axis at the codeword position** (0.09), entangling with it only by the decision
token (0.47). This confirms and sharpens §1.1 with a controlled role-confusion-style
probe, and sets up the sprint's central question exactly: a strong, refusal-orthogonal
semantic state whose *behavioral causality* is unknown (§1.2 prior: likely
epiphenomenal). Phases 3–4 test that.

**Honesty guardrails held:** did NOT claim decodability off the n=4 smoke (E13);
previewed the length/position confounds offline before spending GPU (E14, 0.55); the
preflight caught a real position bug before any bad data (E12). AUC 0.997 is
decodability, NOT causality — stated explicitly in the report §5.

Token-identity = 0.500 exact is a nice construction check: within a matched pair,
doublespeak and benign share the codeword, so token-id is perfectly balanced → the
probe cannot be reading surface codeword identity.

**Deliverables:** `reports/BOMBNESS_PROBE_VALIDATION.md`; run-dir artifacts
`gate1_codeword_last.json`, `gate1_final_prompt.json`, `geometry_vs_refusal.json`.
Registered extraction 757886.

**Next (Phase 2/3):** the Refusalness outcome probe + the dual-probe prediction (which
latent state predicts DS success). Generated-cohort extraction is a cheap cross-cohort
replication when a slot frees.

### E16 — 2026-08-14 — Phase 2+3: Refusalness predicts DS success, Bombness does not ☑ (headline)

Entirely offline (CPU) — behavioral outcomes for all 170 clearharm doublespeak
prompts join to the extraction by example_id (`ds_base_score`, stable across 3 runs
at 94–96% agreement). No GPU needed.

**Phase 2 (§6):** froze the validated refusal_L18 direction as the Refusalness readout
(decision-token residual · refusal_dir; not refit). Primary causal coordinate per §6.1.

**Phase 3 (§7.3):** nested logistic models predicting DS jailbreak (score≥0.5), fit on
train / C-selected on dev / evaluated on the frozen test holdout (n=42):

| model | holdout AUC |
| --- | --- |
| A. Bombness only | **0.592** [0.506, 0.855] |
| B. Refusalness only | **0.976** [0.921, 1.000] |
| C. both | 0.959 (Δ over B **−0.016**) |
| D. + interaction | 0.955 |

Refusalness − Bombness AUC gap **+0.384, CI [0.114, 0.482] excludes 0.** Bombness
quantiles→success flat `[.21,.27,.24,.35,.18]`; Refusalness monotone
`[.50,.53,.21,.00,.00]`. Bombness adds nothing to discrimination after conditioning on
refusal (only a small log-loss/calibration gain).

**The dissociation, in latent-state form:** Bombness is near-perfectly *decodable*
(Gate 1, 0.997) yet carries **no predictive information** about which doublespeak
prompts jailbreak (0.59); the refusal state predicts almost perfectly (0.98). The
semantic-identity confusion is real but is not the behavioral security failure — a
separable refusal-suppressed state is. This is Story A (§22), and it *extends* the
role-confusion result: latent confusion tracking success is not automatic — the
semantic-confusion axis here does NOT track success, a distinct control axis does.

**Honesty:** this is PREDICTIVE, not causal (report §5). Prediction≠causation; Phase 4
(Bombness necessity/sufficiency + the 2×2 factorial) is the decisive causal test.
n=42 holdout is small (7 successes) — the pooled n=170 (Refusalness 0.849) is the
stabler estimate; the *direction* is robust across pooled/holdout and 3 outcome runs.

**Deliverable:** `reports/DUAL_STATE_PREDICTION.md`; `src/probes/dual_state_predict.py`
(+ 2 unit tests); `dual_state_predict.json` in the run dir. **22 GPU-free probe tests**
(2 tokenizer-dependent skip without HF_HOME set).

Note: Gate 2/3 reached without a separately-fitted outcome-state probe — the frozen
refusal projection already predicts strongly and is the better-supported causal
coordinate (§6.1). A fitted 3-class outcome probe (REFUSAL/MALICIOUS/OTHER) is a
secondary readout, deferred (would need per-example 3-way labels; not on the critical
path to Phase 4).

### E17 — 2026-08-14 — Phase 4 harness built (causal intervention) ◐

Built the decisive causal test infrastructure (§8), reusing existing intervention
infra (no new hooks).

- `src/probes/build_intervention_directions.py` → `outputs/phase4_directions/
  v_bomb_clearharm.pt`: per-layer v_bomb (diff-of-means db−benign at codeword, L8-31),
  natural dose gap (2.1→10.9 with depth, gap/sd≈1.7), refusal-orthogonalized variant,
  norm-matched random. cos(v_bomb, refusal) 0.02-0.15 everywhere (orthogonal).
- `scripts/phase4_bombness_intervention.py` (SLURM/GPU): ablate v_bomb at the codeword
  over the write+carry band (L8-18) via stacked `LayerPatch(project_out)`, vs a
  norm-matched random ablation (specificity), with a **manipulation check** = the
  downstream Bombness readout at UNPATCHED layers L20/24/28/31 (must drop if the
  ablation propagated). Optional refusal-ablation positive control. Reuses
  `dc.load_model`/`LayerPatch`/`AllPositionProjectOutMultiLayer`/`strongreject_scoring`.
- `slurm_scripts/run_phase4_bombness.slurm`: MODE=smoke (manip-check only, the §8.3
  gate) / full (judged + refusal arm).

Self-review caught a real bug pre-launch: v_bomb built L8-21 but the readout needs
L20-31 → rebuilt over L8-31. py_compile clean; reused symbols verified.

**Manipulation-check gate first (§8.3):** if ablating v_bomb does NOT reduce the
downstream Bombness readout, the intervention is invalid and no behavioral conclusion
follows. Only if it moves Bombness do I run the judged behavioral arm. Given Phase 3
(Bombness doesn't predict), the expected outcome is: ablation moves Bombness but ASR
stays ~ baseline ~ random → Story A confirmed causally. But that must be measured.

6/6 at cap; slot-waiter armed to launch the manip-check smoke.

### E18 — 2026-08-14 — Phase 4 manipulation check PASSES (§8.3 gate) ☑

Relaunched smoke 757930 (after the no_grad fix) COMPLETED. Manipulation check on 6 DS
prompts — the downstream Bombness readout (mean) at UNPATCHED layers under each arm:

| layer | ds_base | ds_bomb_ablate | ds_bomb_random | ablate−base | random−base |
| --- | --- | --- | --- | --- | --- |
| L20 | +0.99 | −0.88 | +1.00 | **−1.87** | +0.005 |
| L24 | +1.88 | −0.04 | +1.88 | **−1.92** | −0.000 |
| L28 | +1.00 | −0.98 | +1.01 | **−1.98** | +0.008 |
| L31 | +5.35 | +2.90 | +5.30 | **−2.45** | −0.042 |

Ablating v_bomb at the write band (L8-18) **propagates to collapse the Bombness readout
at every downstream unpatched layer** (readout goes from BOMB-like positive to
≈0/negative), while the norm-matched random ablation leaves it unchanged (≤0.04). The
intervention is **valid and specific** — §8.3 gate PASSED. The first no_grad-crash run
(757928) wasted no behavioral compute (died at 32s in setup).

⇒ Cleared to run the decisive behavioral experiment: does removing Bombness (which we
now know collapses the concept readout) change ASR? Launching MODE=full (all 42 test DS
prompts, judged, + the refusal-ablation positive control). Given Phase 3, the expected
outcome is Story A (ASR unchanged vs base and vs random, while refusal ablation moves
it), but this is the measurement that makes the claim causal rather than predictive.

### E19 — 2026-08-14 — GATE 4 PASSED: Bombness is behaviorally epiphenomenal (causal) ☑ (HEADLINE)

Full Phase 4 run 757931 COMPLETED (42 test DS prompts × 4 arms, judged, 29 min).
Verdict via `analyze_phase4`: **STORY A, causally confirmed.** Deliverable:
`reports/BOMBNESS_CAUSAL_INTERVENTION.md`.

**Manipulation check (full n):** ablate−base Bombness readout drops −1.32/−1.30/−1.39/
−1.62 at L20/24/28/31. The ablation collapses the concept readout on all 42 prompts;
random ablation leaves it unchanged.

**Behavioral (n=42):**

| arm | ASR | refusal rate |
| --- | --- | --- |
| ds_base | 0.238 | 0.643 |
| ds_bomb_ablate | 0.190 | **0.643** |
| ds_bomb_random | 0.238 | 0.667 |
| ds_refusal_ablate | 0.476 | **0.048** |

| contrast | ΔASR | 95% CI | McNemar p |
| --- | --- | --- | --- |
| Bombness ablation vs base | **−0.048** | [−0.143, +0.048] | 0.625 |
| vs random (specificity) | −0.048 | [−0.143, +0.048] | 0.625 |
| Refusal ablation vs base (pos. control) | **+0.238** | [+0.071, +0.405] | 0.021 |

**The clincher — refusal rate:** Bombness ablation leaves it identical (0.643→0.643);
refusal ablation collapses it (0.643→0.048). Bombness ablation does not touch the
refusal decision or the behavior; it is indistinguishable from a random ablation.

**Not underpowered:** the positive control detects +0.24 (p=0.02) at the same n, so the
design has power for that magnitude; the Bombness null CI [−0.14,+0.05] **excludes** it.

**Three convergent lines → Story A:**
| | Bombness | Refusal |
|---|---|---|
| decodable (Gate 1) | 0.997 | — |
| geometry | ⊥ refusal (0.09) | — |
| predicts success (Ph 3) | 0.59 | 0.98 |
| causal necessity (Ph 4) | −0.05 [−0.14,+0.05] | +0.24 [+0.07,+0.41] |

Doublespeak creates a real, decodable, causally-manipulable BOMB-like semantic identity
that is orthogonal to refusal, does not predict jailbreak, and — when removed — does not
change jailbreak. A separable refusal-suppressed state predicts AND causally controls
behavior. **Being placed in the adversarial latent identity is not the security failure.**
This is the sprint's paper-level result and a genuine extension of the role-confusion
paper (latent confusion tracking success is not automatic; the causal locus is a
separate control state).

**Honesty:** necessity only, not sufficiency (§8.5) or the 2×2 (§8.6) — both optional
follow-ons; the refusal-intact necessity null argues against Story B's gated version but
the 2×2 is the direct test. Single dose/band/cohort/seed; the manipulation check confirms
the ablation was strong. One bug caught pre-behavioral-compute (no_grad, E18).

**Bugs caught by guards this phase, none reaching a result:** no_grad crash (E18, 32s in
setup); v_bomb band L8-21→L8-31 (self-review, pre-launch); the position preflight (E12).

Registered 757931. Gates 1-4 all passed; the sprint's core causal question is answered.

### E20 — 2026-08-14 — 2×2 factorial: Story B refuted; sprint core complete ☑

Run 757943 (5 arms × 42 prompts, judged, 37 min) → the 2×2 Bombness × refusal factorial:

| | refusal intact | refusal suppressed |
| --- | --- | --- |
| Bombness high | 0.214 | 0.571 |
| Bombness low | 0.214 | 0.571 |

- main-effect Bombness **+0.000** [−0.071, +0.071]
- main-effect refusal **+0.357** [+0.202, +0.500]
- **interaction +0.000 [−0.143, +0.143]**

Bombness is behaviorally inert in BOTH refusal states — exactly zero effect whether
refusal is intact or suppressed. **Story B (gated causality) is refuted**; Story A holds
in its strongest form. Manipulation check confirmed the ablation fired (readout −1.3 to
−1.6), so this is a verified null, not a dead intervention. (Base ASR 0.214 vs the prior
run's 0.238 = run-to-run drift B15; qualitative result identical.)

Process bug caught pre-compute: the first 2×2 launch passed `--factorial` to sbatch,
which doesn't forward positional args → would have silently produced 3 cells. Cancelled
(PENDING, no loss), added a `FACTORIAL` env var, relaunched as 757943.

**Capstone deliverables written:**
- `docs/ROLE_CONFUSION_DOUBLESPEAK_CAUSAL_SYNTHESIS.md` — the 13-section synthesis (§20).
- `reports/ROLE_PROBE_CLAIM_AUDIT_TABLE.md` — every claim VERIFIED with provenance (§21);
  D5 (2×2) now VERIFIED.
- `reports/BOMBNESS_CAUSAL_INTERVENTION.md` updated with the 2×2.

**Sprint core complete: Gates 0-4 all passed.** The central question is answered
definitively across three convergent lines (decodability, prediction, causal
intervention incl. 2×2). Remaining items (sufficiency, cross-cohort, Phi/Qwen, second
corpus, normalized-space arm) are follow-ons per §19, not required for the core result.
Registered 757943.

### E21 — 2026-08-14 — Cross-cohort (generated) replication: probe generalizes, prediction is cohort-dependent ◐

Ran the generated-cohort replication (extraction 757957, `acts[462,32,2,4096]`, after the
B19 preflight fix unblocked it). Honest, nuanced result — **not** a clean full replication:

**Gate 1 REPLICATES strongly.** Generated holdout AUC **0.9972** [0.990, 1.000] @L11;
controls near chance (label-shuffle 0.406, position 0.579, length 0.586, token-id 0.500).
The Bombness probe generalizes to a second, distributionally-different cohort
(gpt-4o-mini one-line requests). Solid external validity for the decodability result.

**Phase 3 prediction is WEAKER / does not cleanly replicate.** On generated (n=38 holdout,
success 0.29):
- Bombness predicts jailbreak at **0.49** (chance) — the epiphenomenal half of Story A
  **holds** cross-cohort.
- Frozen clearharm refusal direction predicts at **0.525** (chance); the refusal−Bombness
  gap CI [−0.21, +0.16] **includes 0**. A native decision-token→outcome probe fit ON
  generated does better (0.60–0.63 across L14-24) but still far below clearharm's 0.98.

**Interpretation (honest boundary):** the "refusal-state strongly predicts jailbreak"
result is **clearharm-specific in strength**. Two contributing causes: (a) the refusal
direction is fit cross-distribution on carrot_bomb (B17) and transfers poorly to the
generated distribution (0.525); (b) even a native-fit probe only reaches ~0.63, so
generated-cohort jailbreaks are inherently **less predictable** than clearharm's. The
directional dissociation survives (native refusal-state 0.63 > Bombness 0.49), but the
effect size does not.

**What this does and does not change:**
- Story A's Bombness-is-epiphenomenal half **replicates** (decodable everywhere;
  non-predictive everywhere).
- The refusal-is-the-strong-predictor half is **distribution-dependent** — strong on
  clearharm, modest on generated.
- The clearharm CAUSAL result (Gate 4, 2×2) is unaffected (it is causal, not predictive,
  and clearharm-specific by design). Whether the causal story replicates on generated
  would need a generated-cohort Phase-4 run (v_bomb directions + intervention) — deferred.

This is a genuine, reportable limitation, not a failure — kept per §3.11. Updating the
synthesis §9 and the claim audit to state the cross-cohort boundary precisely.
Registered 757957.

### E22 — 2026-08-14 — Generated Phase 4: manip-check FAILS (Bombness inconclusive); refusal control replicates ◐

Ran the generated-cohort Phase 4 (757967, 5 arms × 38 test prompts). Honest, mixed result:

**Manipulation check FAILED (the key caveat).** ablate−base Bombness readout is POSITIVE
on generated (+0.30/+0.33/+0.40/+0.68 @L20/24/28/31) — the readout went UP, not down
(clearharm: −1.3 to −1.6). `manip_check_passed: False`. The project_out ablation did not
cleanly reduce the generated Bombness readout, so **the generated Bombness behavioral
numbers are INCONCLUSIVE** (the analysis verdict flags this). Process lesson: I skipped
the manip-check smoke for the new cohort and went straight to full — should always
smoke-check the manipulation on a new cohort first (the intervention doesn't transfer for
free). Likely cause: generated v_bomb is less clean (cos_vs_refusal up to 0.21 vs
clearharm 0.15) and/or the generated concept binding is weaker at the codeword.

**What IS interpretable:**
- `ds_bomb_ablate` ASR == `ds_bomb_random` ASR **exactly** (0.368) — the "ablation" is
  behaviorally indistinguishable from a random perturbation (consistent with Story A, but
  not cleanly demonstrated given the failed manip check).
- **Refusal positive control WORKS on generated:** ablation ΔASR **+0.21** [+0.03,+0.29],
  p=0.02; refusal rate 0.237→0.026; 2×2 main-effect refusal +0.158 [0.026, 0.290].

**This resolves last tick's open question.** The weak generated *prediction* (E21,
refusalness 0.525) is NOT because refusal doesn't matter — it causally does (+0.21). It is
a **frozen-direction transfer artifact** (the carrot_bomb-fit refusal direction predicts
generated jailbreak poorly, B17), not a mechanism difference. The refusal MECHANISM
replicates causally cross-cohort; the refusal DIRECTION does not transfer as a predictor.

**Net cross-cohort status:**
- Gate 1 (Bombness decodable): replicates (0.997). [E21]
- Bombness non-predictive: replicates (0.49). [E21]
- Bombness causal necessity on generated: **INCONCLUSIVE** (manip check failed). [E22]
- Refusal causal on generated: **replicates** (+0.21, p=0.02). [E22]

So the clearharm causal Story A stands; its generated causal replication for the Bombness
half is unproven (a clean generated intervention would need better-conditioned directions
— e.g. a narrower band or a dose that keeps the readout on-manifold). Reported as an
honest limitation, not a positive. Registered 757967.

### E23 — 2026-08-14 — Sufficiency arm calibrated on-manifold; full run launched ◐

Built the §8.5 sufficiency arm (add Bombness to neutral prompts). Manipulation-check
smokes FIRST (E22 lesson):
- dose=1.0 (757990): ADD works + specific, but OVERSHOOTS — readout +13 to +19 vs the
  natural doublespeak level ~+0.3 to +1.8 (adding gap·v_bomb across 11 layers compounds).
  Off-manifold — rejected per §8.2.
- **dose=0.25 (757991): on-manifold** — bomb_add readout +0.4 to +2.7 (≈ natural
  doublespeak), random unchanged. add−base +4.6 to +7.2. Clean, calibrated injection.

So the sufficiency intervention now brings the neutral codeword to the natural doublespeak
Bombness level. Full judged run launched (757992, dose 0.25, + refusal control). Question:
does making the neutral codeword BOMB-like (to doublespeak level) induce harm? Given Story
A, expected null (Bombness not sufficient); refusal-ablation-from-neutral is the control.

Discipline note: two 90s smokes + §8.2 on-manifold check avoided a 40-min judged run at an
off-manifold dose. The manipulation-check-first rule (E22) is now standing practice.

---

## 4. DEVIATIONS FROM THE PLAN

Every entry here must have a matching row in `BUG_AND_DEVIATION_LOG.md`.

| # | Plan says | We did | Why | Logged in bug log |
| --- | --- | --- | --- | --- |
| V1 | §2A.2 deliverable is `docs/ROLE_CONFUSION_CODE_REVIEW.md` | Folded into the plan as Appendix A; separate file deleted | User requested a single tracking file | n/a — documentation location only, no scientific effect |

---

## 5. OPEN QUESTIONS FOR THE USER

| # | Question | Blocking? | Status |
| --- | --- | --- | --- |
| Q2 | **Confirmatory holdout for the Bombness probe.** v3 test (80 ex, 60 disjoint codewords, leakage-0) is exposed to prior *behavioral* work but NOT to any *probe* analysis. Accept it as probe-unexposed and use it once as the Gate-1 holdout, or construct a fresh probe holdout? | Not blocking Phase 1 (fit=train, select=dev). Blocks only the final Gate-1 confirmatory claim. | OPEN — recommend (a) accept v3 test, since the probe construction is genuinely new and the split is codeword-disjoint. Will proceed under (a) unless told otherwise. |
| Q1 | GitHub PAT is live in `.git/config` plaintext (`ghp_…`, confirmed real). Rotate + move to SSH/credential-helper. | Security, not sprint-blocking | OPEN — awaiting user |

### E24 — 2026-08-14 — Sufficiency NULL: Bombness neither necessary, sufficient, nor gated ☑

Full sufficiency run 757992 (dose 0.25 on-manifold) COMPLETED. Manipulation check PASSED
(add−base readout +5.2/+4.8/+5.3/+7.8 — injected to natural doublespeak level). Behavioral
(n=42):

| arm | ASR | refusal rate |
| --- | --- | --- |
| neu_base | 0.214 | 0.667 |
| neu_bomb_add | 0.262 | 0.667 |
| neu_bomb_random | 0.167 | 0.667 |
| neu_refusal_ablate | 0.548 | 0.071 |

- Sufficiency (add vs base): **ΔASR +0.048, p=0.50** — not significant; refusal rate
  identical. Injecting doublespeak-level Bombness into a neutral prompt does NOT induce harm.
- vs random: +0.095, p=0.125 (bomb_add ≈ random).
- Refusal-from-neutral control: **+0.333, p=0.001**; refusal rate collapses 0.667→0.071.

**Phase 4 COMPLETE on clearharm.** Bombness is **neither necessary (−0.05), nor sufficient
(+0.05), nor gated (2×2 interaction 0.00)** — fully epiphenomenal for behavior from both
intervention directions plus the factorial. Refusal is the entire causal lever (necessity
+0.24, sufficiency-control +0.33, 2×2 main +0.36). Story A holds in the strongest possible
form. Note neu_base ASR 0.214 ≈ ds_base 0.214 — the doublespeak framing/binding does not
itself raise ASR (consistent with E9's ds vs direct ≈ 0); the behavioral action is refusal.

Deliverables updated: BOMBNESS_CAUSAL_INTERVENTION.md §5, synthesis §7/§11/§12/§13, claim
audit D6. On-manifold dosing (§8.2) + manip-check-first (E22) both applied. Registered 757992.

### E25 — 2026-08-14 — Final independent audit (§21): all load-bearing numbers raw-reproducible ☑

Recomputed every headline number from raw artifacts with FRESH code (not the analysis
scripts): Gate 1 AUC 0.9972 (from acts.npy), token-id 0.500, necessity −0.048, refusal
+0.238, 2×2 (main_bomb +0.000 / main_refusal +0.357 / interaction +0.000), sufficiency
+0.048, refusal control +0.333 — ALL match the reported values exactly. The analysis
scripts have no bugs affecting reported numbers. §21 checklist (15 items) passed; 7/7
probe+phase4 runs registered, all dirs unique (no overwrites). Report:
`reports/ROLE_PROBE_FINAL_AUDIT_2026_08_14.md`. The result is trustworthy for write-up;
the one material boundary (cross-cohort) is documented, not hidden.

**Sprint status: core COMPLETE and audited.** Gates 0-4 passed; Phase 4 complete
(necessity + 2×2 + sufficiency); cross-cohort Gate 1 replicated with honest prediction
boundary; final audit passed. Remaining are non-core follow-ons (Phi/Qwen cross-family,
second corpus, component patching, D3).

### E26 — 2026-08-14 — Cross-MODEL Gate 1 replicates on Phi-4-mini-reasoning ☑

Extended the probe to a second model family (Phase 8), parameterizing the extraction by
MODEL. Phi-4-mini-reasoning (acts[510,32,2,3072]):
- **Gate 1 PASS**: holdout AUC **0.985** [0.967, 0.998] @L10; controls near chance
  (label-shuffle 0.514, random 0.487, position 0.562, length 0.559, token-id 0.500 exact).
- **Geometry**: cos(Bombness codeword, Phi refusal) = **+0.01 to +0.04** (L12-20) — even
  more orthogonal than Llama. The decodable, refusal-orthogonal semantic representation is
  a CROSS-FAMILY property.

The B19 preflight relaxation was load-bearing here: Phi tokenization ≠ the Llama-tokenized
corpus spans (soft match rate 0.0), but the hard check passed and resolve_positions found
the codeword in Phi's own tokenization (correct by construction). Had the original
hard-abort anchor still been in place, cross-model extraction would have been impossible —
the honest B19 fix (E21) directly enabled this result.

Scope: Phi's Phase 3/4 (prediction/causal) need Phi behavioral outcomes on v3 doublespeak,
which don't exist (existing Phi/Qwen screens are a different cohort). So Story A's
REPRESENTATION half is cross-family (Llama + Phi); its BEHAVIORAL half is Llama-only so far.
Qwen3-14B probe replication open. Synthesis §9 + registry updated (758021/758022).

### E27 — 2026-08-14/15 — Cross-model Gate 1 confirmed on THREE families (Phi + Qwen3) ☑

Added Qwen3-14B (8-bit, via the new --quantize passthrough; acts[510,40,2,5120]) to the
cross-model set. Gate 1 + geometry now replicate across three model families:

| model | hidden | Gate 1 AUC | max control | cos(Bombness,refusal) |
| --- | --- | --- | --- | --- |
| Llama-3.1-8B | 4096 | 0.997 | 0.587 | 0.06–0.15 |
| Phi-4-mini-reasoning | 3072 | 0.985 | 0.562 | 0.01–0.04 |
| Qwen3-14B (8bit) | 5120 | 0.999 | 0.591 | 0.03–0.12 |

Token-identity control exactly 0.500 in all three (matched-pair design). The decodable,
refusal-orthogonal semantic-remapping representation is a CROSS-FAMILY property — 3
architectures, 3 hidden sizes, no per-model code (just MODEL/QUANTIZE params; the reused
capture_components/resolve_positions/gate1_eval pipeline). The B19 preflight relaxation
(E21) was essential — it lets the Llama-tokenized corpus spans be ignored while
resolve_positions finds the codeword in each model's own tokenization.

Scope held honest: representation half cross-family (3 models); behavioral Phase 3/4 half
is the audited Llama result (Phi/Qwen behavioral outcomes on v3 doublespeak don't exist).
Synthesis §9 = 3-family table. Registry 602. Phase 8 (probe replication) essentially done.

### E28 — 2026-08-15 — §20 deliverable completeness pass

Checked the §20 required-deliverables list. Filled the two gaps I have complete data for:
- `reports/BOMBNESS_REFUSAL_FACTORIAL.md` — the 2×2 (run 757943), previously folded into
  BOMBNESS_CAUSAL_INTERVENTION; now the standalone deliverable the plan names.
- `reports/PHI_CONCEPT_COMPLETION.md` — repurposed to the cross-model probe replication
  (3-family Gate 1 + geometry), which is this sprint's role-probe analogue of the original
  B16 Phi concept arm; honestly scopes what is NOT done (Phi/Qwen behavioral Phase 3/4).

Two remaining §20 files correspond to genuinely UNRUN phases and are NOT written (writing
empty stubs would misrepresent status): `PROBE_COMPONENT_PATCHING.md` (Phase 5) and
`D3_SCOPE_MATCHED_CONTROL.md` (Phase 6, an asymmetry-thread control). Both are documented as
deferred follow-ons in the synthesis §12/§13.

Deliverable status: 7 of 9 §20 reports present + synthesis + claim audit + manifest + audit;
the 2 absent are unrun phases, deferred with rationale.

### E29 — 2026-08-15 — Phi behavioral Phase 3/4: epiphenomenal-Bombness replicates; refusal-lever does NOT (Phi pre-collapsed) ◐

Full Phi Phase 4 (758057, manip check PASSED: ablate−base −6 to −8) + Phi Phase 3.
Nuanced, honest cross-family behavioral result — NOT a clean full Story-A replication.

Phi Phase 4 (n=42):
| arm | ASR | refusal rate |
| --- | --- | --- |
| ds_base | 0.262 | **0.048** |
| ds_bomb_ablate | 0.190 | 0.048 |
| ds_bomb_random | 0.214 | 0.048 |
| ds_refusal_ablate | 0.357 | 0.000 |

- **Bombness necessity NULL replicates**: ΔASR −0.071 (p=0.58), = random (−0.024, p=1.0).
  The epiphenomenal half of Story A holds behaviorally on Phi (with the partial-ablation
  caveat: Phi re-accumulates Bombness, so late-layer readout only partly drops).
- **Refusal-lever does NOT cleanly replicate**: refusal-ablation ΔASR +0.095 (p=0.39, ns).
  Root cause: **Phi's baseline doublespeak refusal rate is 0.048** (Llama 0.64) — the
  attack ALREADY collapses Phi's refusal, so the positive control has almost no headroom
  (floor issue, cf B7).

Phi Phase 3 (n=42, jailbreak 0.262): refusal-projection AUC **0.525**, Bombness AUC
**0.575** — NEITHER predicts Phi jailbreak. Because Phi barely refuses doublespeak,
refusal state doesn't vary in a way that separates jailbreak from non-jailbreak; the
residual jailbreak variation is driven by something else (compliance vs off-target
output at already-low refusal).

**Honest cross-family behavioral net:**
- Bombness-epiphenomenal: replicates on Phi (necessity null + non-predictive).
- Refusal-is-the-behavioral-lever: **Llama-specific in this form** — Phi is far more
  susceptible to doublespeak at baseline (refusal pre-collapsed), so refusal is neither
  the discriminating predictor nor a headroom-having lever there.

Interesting substantive finding: **doublespeak's behavioral mechanism differs by model** —
on Llama it works by suppressing an otherwise-strong refusal; on Phi refusal is weak
against doublespeak to begin with. The semantic-remapping REPRESENTATION is cross-family
(3 models); the refusal-CONTROL behavioral story is model-dependent. Reported as an honest
boundary (§3.11). Registered 758057. Updating synthesis §9 + PHI report + claim audit.

### E30 — 2026-08-15 — Qwen behavioral Phase 4 running (INTERIM note, not a result)

Full Qwen Phase 4 (758075, 8-bit) in progress (~2h run; 22/42 at this tick). **Interim
read (n=22, NOT final, do not cite):** Qwen ds_base refusal_rate ≈ 0.23, ASR ≈ 0.045.
Preliminary placement: Qwen sits BETWEEN Llama (base refusal 0.64) and Phi (0.048) —
suggesting the doublespeak behavioral-susceptibility is a **spectrum** across families, not
Phi as a binary outlier. Caveat forming: Qwen base ASR ≈ 0.045 is very low, so the
refusal-lever positive control will likely be floor-limited (little jailbreak headroom to
raise). Awaiting the full n=42 before recording anything. No result committed this tick;
claim-audit CM5 stays PENDING.

### E31 — 2026-08-15 — Qwen behavioral Phase 4 completes the 3-family picture ☑

Full Qwen Phase 4 (758075, n=42, manip check passed −4 to −6):
| arm | ASR | refusal |
| --- | --- | --- |
| ds_base | 0.071 | 0.119 |
| ds_bomb_ablate | 0.119 | 0.071 |
| ds_bomb_random | 0.119 | 0.024 |
| ds_refusal_ablate | 0.238 | 0.000 |
- Bombness necessity **NULL** (ΔASR +0.048, p=0.63, = random) — epiphenomenal replicates.
- Refusal ablation **+0.167, p=0.039 (SIGNIFICANT)** — refusal IS the lever on Qwen.

Qwen Phase 3: only 3 jailbreaks (ASR 0.071) → underpowered; refusal-proj AUC 0.82 but noisy
(3 positives). Directionally consistent, not citable as a prediction result.

**Completed three-family behavioral picture:**
| model | base refusal | base ASR | Bombness necessity | refusal ablation |
| --- | --- | --- | --- | --- |
| Llama-3.1-8B | 0.64 | 0.24 | −0.05 (null) | **+0.24, p=0.02** |
| Phi-4-mini | 0.048 | 0.26 | −0.07 (null) | +0.10, p=0.39 (ns, floor) |
| Qwen3-14B | 0.119 | 0.071 | +0.05 (null) | **+0.17, p=0.04** |

**Two clean cross-family conclusions:**
1. **Bombness is behaviorally epiphenomenal on ALL THREE families** — necessity null (= random)
   everywhere, manip check passed everywhere. The strongest form of the representation≠behavior
   dissociation, now cross-family.
2. **Refusal is the causal lever on Llama AND Qwen** (both refusal-ablation significant,
   p<0.05) — the two families that RETAIN refusal headroom against doublespeak. Phi's ns
   result is a **floor artifact** (base refusal 0.048; doublespeak already collapsed it), NOT
   a mechanism difference. So Qwen RESCUES the generality that Phi alone made ambiguous: refusal
   is causal wherever there is refusal to ablate.

This is a cleaner, stronger story than after Phi alone. The behavioral susceptibility to
doublespeak is a spectrum (Phi most susceptible, Qwen least, Llama middle), but the mechanism
is invariant: Bombness never matters, refusal always does (when present). Registered 758075.
Updating synthesis §9 + claim audit CM5/E3.

### E32 — 2026-08-15 — §21 audit extended to cross-family (all numbers raw-reproducible) ☑

Independently recomputed the Phi/Qwen headline numbers from raw with fresh code (Gate 1
from acts.npy, Phase-4 ΔASRs from raw.jsonl): Phi Gate 1 0.9858, Qwen 0.9989; Phi necessity
−0.071 / refusal +0.095; Qwen necessity +0.048 / refusal +0.167 — ALL match reported exactly.
The analysis scripts are bug-free for the cross-family runs too. The ENTIRE body of work
(Llama core + cross-cohort + 3-family cross-model) is now §21-audit-covered.
`reports/ROLE_PROBE_FINAL_AUDIT_2026_08_14.md` §1b added.

### E33 — 2026-08-15 — Deliverable coherence pass (fixed 2 stale limitation lines)

Ran a cross-doc consistency check of the headline numbers (Gate 1 0.997, necessity nulls,
cross-family refusal +0.24/+0.17/+0.10). Numbers consistent everywhere. Caught and fixed 2
STALE "not run" lines (the doc-drift the prior sprint's audit flagged):
- synthesis §11: "sufficiency (§8.5) not run" → sufficiency WAS run (E24/D6); corrected.
- claim audit limitations: "Cross-family (Phi/Qwen) ... not yet run" → 3-family Gate 1 +
  Phi/Qwen behavioral ARE done (CM1–CM7); corrected, with the genuinely-open items listed.
No numeric claim changed; documentation now internally consistent.

### E34 — 2026-08-15 — Normalized-space robustness arm: Gate 1 robust to space choice (D1) ☑

Re-extracted in upstream's normalized mid-block space (post_attention_layernorm, run 758099)
and refit Gate 1: holdout AUC **0.994** [0.984,1.000] @L7, controls near chance (token-id
0.500). Compared to raw post-block residual (D1 headline, 0.997 @L11): Bombness decodes
essentially identically in BOTH spaces. **The Gate-1 result is not an artifact of the
residual-space choice** — it holds in upstream's own space too. This validates D1 (chosen
for steerability) and pre-empts the "cherry-picked the space" question; full-circle to §2A.
BOMBNESS_PROBE_VALIDATION §6b + synthesis updated. Registered 758099. The last
clearly-in-scope autonomous item is complete.

---

### E35 — cross-deliverable consistency audit: fixed two stale self-contradictions (2026-08-15)

Ran a programmatic headline-number + stale-phrasing scan across all role-probe
`reports/*.md` + docs (scalar-only, no GPU, no generation text). The headline numbers
(0.997 / 0.994 / 0.985 / 0.999 / −0.048 / 0.357 / 0.238 / 0.333) are consistent across
files. The scan caught **two genuine doc-drift contradictions** (E33-class), both now fixed:

1. `ROLE_PROBE_FINAL_AUDIT_2026_08_14.md` §3 said "Cross-model (Phi/Qwen) not run," but
   §1b of the SAME file (appended 2026-08-15) recomputes the Phi/Qwen numbers from raw and
   §1's checklist covers them. The limitation line was stale from before §1b was appended.
   → rewritten to state Phi/Qwen representation+epiphenomenality arms ARE run and audited,
   with the Phi refusal-lever floor (0.048) as the true, disclosed boundary.
2. `ROLE_PROBE_CLAIM_AUDIT_TABLE.md` "Known limitations" said "generated-cohort replication
   not yet run," but rows CC1–CC5 in the SAME table report that replication in detail
   (Gate 1 + epiphenomenality replicate; refusal causal replicates; predictor transfer-
   limited; Bombness-causal inconclusive). → rewritten to say "single cohort" applies to
   the *predictive* Gate 3 only, not Gate 1, cross-referencing CC1–CC5.

No numeric claim changed; both edits only correct stale prose that contradicted the file's
own body. This is the "self code-review for bugs" arm — found and fixed, no new GPU spent.

---

### E36 — Phase 5 started: donor-shift energy decomposition (zero-GPU slice) (2026-08-15)

First slice of Phase 5 (plan §9), chosen because it needs NO generation and NO new
GPU — pure numpy on activations already on disk (`acts.npy` 757886, `v_bomb_clearharm`,
`refusal_direction_llama_L18`). New reusable module `src/probes/phase5_decompose.py`.

For 170 matched (doublespeak, benign, neutral) triples, partition the donor shift
Δh(L)=h_ds−h_donor at the codeword position into energy along v_bomb[L], along refusal
(L18), and orthogonal remainder (QR-orthonormalised plane so the split is exact under
the ~0.09 non-orthogonality).

Built-in B9 index-alignment guard: recompute benign diff-of-means from acts, compare to
stored v_bomb → **cos=1.000 every layer** (axis aligned). The guard also correctly
REJECTED applying codeword-built v_bomb at final_prompt (cos→0.004–0.18); that invalid
output was deleted, only codeword_last reported.

Findings (codeword position):
- **Refusal axis ≈ absent from the codeword shift**: frac_refusal ≤ 0.011, cos ≤ 0.10 in
  every band, both donors. Upgrades §4 direction-orthogonality to an energy statement —
  refusal is a downstream/decision variable, not written at the codeword. Explains why
  refusal (not Bombness) is the behavioral lever.
- **v_bomb is a coherent MINORITY summary**: ~14–22% of ‖Δh‖² at concept-write L8–11,
  falling to ~10–13% at decision; ~80% orthogonal remainder (topic-specific). So whole-Δh
  patching ≠ v_bomb patching — motivates the component lens.

This is a REPRESENTATION-energy result, NOT behavioral mediation (Q3). Q3/Q4 (patch each
component + generate + score ΔASR) reuse the Phase-4 harness + existing corpus (no new
harmful authoring) and need GPU + explicit go-ahead — NOT launched autonomously.
Report: reports/PHASE5_DECOMPOSITION.md. Self-reviewed: QR basis, matched triples by
example_id (170/170 complete), donor-independent selfcheck, invalid-position rejection.

---

### E37 — Phase 5 decomposition extended cross-family (zero-GPU) (2026-08-15)

Re-ran phase5_decompose on Phi (758022, refusal_phi L18) and Qwen (758030, refusal_qwen3
L24), 170 triples each, benign donor, codeword position. Index guard cos=1.000 every layer
both (module auto-adapted to Qwen's 40-layer stack).

- **Refusal axis ~absent from the codeword shift in ALL 3 families**: frac_refusal
  Llama ≤0.005 / Phi ≤0.0004 / Qwen ≤0.0017; cos ≤0.05 everywhere. The
  "refusal is downstream, not written at the codeword" geometry is family-invariant —
  same mechanistic-invariance signature as the representation itself.
- **Honest cross-family nuance on the Bombness axis**: v_bomb energy share FALLS with
  depth in Llama/Phi (0.22→0.13, 0.19→0.07) but RISES in Qwen (0.17→0.25). Reported as a
  genuine difference, not smoothed over. Bands are absolute layer indices (32 vs 40-layer
  stacks), so trajectory is qualitative.
Report §"Cross-family" updated. Still representation-energy only; Q3/Q4 behavioral remain
GPU-gated + go-ahead-gated.

---

### E38 — unit test hardening phase5_decompose (zero-GPU) (2026-08-15)

Added tests/test_phase5_decompose.py (4 tests, GPU-free, 0.32s). Plants a known donor
shift Δh = a·v_bomb + b·refusal + c·perp in synthetic activations and asserts:
- decompose() recovers the planted energy fractions exactly (bomb/refusal/remainder);
- the QR plane split is exact (frac_bomb+frac_refusal == 1-remainder for orthogonal axes);
- the B9 index-alignment selfcheck returns cos≈1 when v_bomb == normalized diff-of-means,
  and ~0 when handed a misaligned axis (both OK and WARN paths verified).
Locks in the E36/E37 numbers against future refactors. All pass.

---

### E39 — Phase 5 scope clarification: mean-field Q3 == Phase-4 sufficiency (zero-GPU) (2026-08-15)

Self-review of the Q3/Q4 build surfaced (and I verified numerically) that v_bomb[L] IS the
unit mean diff-of-means: cos(mean full-shift, v_bomb) = 1.00000 at every band layer
(L8/11/14/18/21). Therefore a fixed-direction mean-field Q3 ("add the mean bomb component,
measure ΔASR") is IDENTICAL to the Phase-4 sufficiency arm (add v_bomb), already run = null
(+0.05). A naive fixed-direction Q3/Q4 on the existing harness would just re-run Phase 4.

The only NON-redundant behavioral content in Phase 5 is PER-EXAMPLE component patching
(install each example's own Δh_bomb / Δh_refusal / Δh_remainder / complement / full / random),
which needs a new per-example-keyed patch capability + GPU. Documented this in the report so
we don't burn GPU re-deriving the Phase-4 null. This is the "self code-review prevents a
wasted experiment" outcome. Per-example harness build deferred to greenlight (will
CPU-unit-test the vector construction before any GPU).

---

### E40 — Phase 5 per-example patch-vector construction + tests (zero-GPU) (2026-08-15)

Built src/probes/build_phase5_perexample.py — the NON-redundant Phase-5 input (E39):
per-example, per-band decomposition of each example's donor shift Δhᵢ into arms
{full, bomb, refusal, remainder, random(norm-matched)} at the codeword position, saved
as a tensor artifact keyed by example_id for a future per-example-keyed GPU patch harness.

Self-review caught a real BUG before it could bias results: with raw dual projection,
bomb+refusal+remainder ≠ full because v_bomb ⟂ refusal only ~cos 0.09 (real build showed
6e-2 additivity error). Fix: orthogonalise refusal against v_bomb per layer → exact
additive orthogonal decomposition (recon rel-err 6e-17 on real data). The 'refusal' arm
is thus refusal-⊥-bomb (documented). Added a regression test with deliberately
non-orthogonal axes (cos 0.3) that fails under the old math and passes now.

8/8 Phase-5 tests pass. Real artifact built (170 ex, band 8-21, frac_bomb 0.22→0.13,
consistent with E36). The GPU generation-loop change (add ±arm_i keyed per example) is the
only remaining piece and stays GPU + greenlight gated. No GPU spent; no generation.

---

### E41 — Phase 5 per-example patch-spec builder (pure, tested, zero-GPU) (2026-08-15)

Added src/probes/phase5_patch_spec.py — the B9-critical piece isolated from torch so it
is fully unit-testable: maps a corpus example to the RIGHT row of the per-example vector
artifact (lookup by example_id, never by enumeration index) and emits the per-layer patch
spec {layer, vector, mode:add, alpha:±1}. Sign convention: -1 subtract (necessity, base
doublespeak), +1 add (sufficiency, base donor). Pre-scaled per-example vectors keep the
dose on-manifold (§8.2) with no gap rescale.

6 new tests (row-by-id not position; missing-id guard raises; sign/arm/layer encoding;
band filtering; invalid arm/sign; spec_norm). Full Phase-5 suite: 14/14 pass.

End-to-end on the REAL artifact (comp_clearharm_benign): full |spec|=31.5, bomb=8.2,
refusal=0.68 (near-null — codeword-Δh has ~no refusal component, consistent E36/E37),
remainder=30.4 (dominant), random=8.2 (norm-matched to bomb); spec additivity holds.

Only the GPU generation wrapper remains (consume spec → dc.LayerPatch → generate → judge,
reusing the phase4 path). Deliberately NOT written un-smoked: it will be built + smoked +
launched together on greenlight. No GPU spent; no generation.

---

### E42 — Phase 5 GPU harness built + smoke launched (user greenlit GPU) (2026-08-15)

User greenlit GPU. Built scripts/phase5_component_patch.py (per-example component patch
generation) + slurm_scripts/run_phase5_component.slurm, reusing the phase4 path
(dc.load_model / LayerPatch add-mode / ComponentCapture readout / strongreject judge) and
the tested phase5_patch_spec builder. Patch band L8-18 (disjoint from readout 20/24/28/31);
necessity subtracts (sign -1) each example's own component, sufficiency adds (+1).

Preflight: harness compiles; patch_spec imports; slurm bash -n clean; example_id alignment
42/42 test in artifact (B9 guard will pass not skip). Smoke gate launched: job 758159
(MODE=smoke necessity LIMIT=6, --no-judge) — the gate is whether per-example subtraction
MOVES the downstream Bombness readout (bomb arm should lower it). If it doesn't manipulate,
do not scale to full/judged.

---

### E43 — Phase 5 smoke gate PASSED; full necessity+sufficiency launched (2026-08-15)

Smoke 758159 (necessity, manip-check) row 1 — mean downstream Bombness readout Δ vs base:
  bomb -29.9 | full -26.6 | remainder -6.8 | refusal -0.05 | random -0.40
Textbook-clean: per-example bomb subtraction moves the readout STRONGLY and SPECIFICALLY
(norm-matched random -0.40 ≈ 0; refusal ≈ 0 consistent with ~no refusal energy at codeword,
E36/E41). Manipulation check PASSES → valid to scale + judge.

Cancelled smoke; launched FULL judged runs on L40S (--constraint=l40s):
  758162 necessity  (base doublespeak, subtract each example's component)
  758163 sufficiency (base benign, add each example's component)
Both all-arms {base,full,bomb,refusal,remainder,random}, 42 test prompts, StrongREJECT.
The behavioral question: does per-example component subtraction/addition move ASR, or is
the manipulated Bombness still epiphenomenal (predicted: null bomb arm, refusal already
known to be the lever)? Results pending.

---

### E44 — Phase 5 necessity result: per-example Bombness patching = NULL (2026-08-15)

Full necessity run 758162 DONE (n=42, base ASR 0.167). Per-example subtraction of each
example's OWN component at codeword L8-18:

  arm        ΔASR     McNemar b/c   manip readoutΔ
  bomb       +0.048   b=1 c=3       -18.68  (strong, specific manipulation)
  random     +0.048   b=0 c=2       -0.16
  full       -0.048   b=4 c=2       -10.48
  refusal     0.000   b=1 c=1       +0.07
  remainder   0.000   b=3 c=3       +1.21

DECISIVE: bomb subtraction removed Bombness STRONGLY and SPECIFICALLY (readout -18.7 vs
norm-matched random -0.16) yet produced the SAME ΔASR as random (+0.048, both n.s.,
McNemar discordant tiny). A potent, specific manipulation of Bombness → no behavioral
effect beyond random noise. This is Story A (Bombness behaviorally epiphenomenal) confirmed
by the SHARPEST causal test in the sprint — per-example component patching, not mean-
direction ablation. Base ASR 0.167 limits necessity headroom, but the manip check proves
the representation WAS moved, so the null is a real dissociation. Sufficiency run 758163
(add into benign, higher headroom) pending.

---

### E45 — Phase 5 sufficiency NULL; Phase 5 COMPLETE (2026-08-15)

Sufficiency run 758163 DONE (n=42, base ASR 0.286). Adding each example's own component
into the benign prompt:
  bomb ΔASR +0.048 [−0.048,+0.143], McNemar b=1 c=3, readout +18.9 (strong install)
  random +0.000, full +0.000, remainder −0.024, refusal 0.000
Same NULL as necessity: strong specific manipulation (readout +18.9 vs random +0.65),
no behavioral effect (bomb CI includes 0 and random; upper bound +0.143 << refusal lever
+0.24/+0.36).

PHASE 5 COMPLETE. Both directions confirm per-example Bombness component patching is
behaviorally epiphenomenal — the sharpest causal test in the sprint. Report:
reports/PHASE5_BEHAVIORAL.md. Runs registered (registry 612). Decomposition report
"what remains" updated to DONE. Bootstrap CIs computed. All GPU done for Phase 5.
