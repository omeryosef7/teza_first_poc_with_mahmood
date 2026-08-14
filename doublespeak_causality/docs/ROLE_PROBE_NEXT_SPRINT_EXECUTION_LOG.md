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
| Gate 1 | Contextual Bombness probe validity | ☐ |
| Gate 2 | Outcome probe beats trivial baselines; refusal direction still better-supported causally | ☐ |
| Gate 3 | Frozen latent-state prediction report written | ☐ |
| Gate 4 | Bombness causal claim admissible (manipulation check + controls + holdout) | ☐ |
| Gate A–F | Decision tree §18 | ☐ |

### Phases

| Phase | Plan § | Status | Note |
| --- | --- | --- | --- |
| Upstream import | 2A.1 | ☑ | commit `ec333c40`, no `.git`, MIT retained |
| Upstream code review | 2A.2 | ☑ | Appendix A of the plan |
| **Phase 0 — governance repair** | 4 | ☑ | registry 395→573, bug log B6–B18, manifest frozen |
| Phase 1 — Bombness probe | 5 | ◐ | dataset builder done+tested (CPU); extraction/fit await GPU |
| Phase 2 — refusal/compliance readout | 6 | ☐ | |
| Phase 3 — latent-state experiments | 7 | ☐ | |
| Phase 4 — causal interventions | 8 | ☐ | **highest value** |
| Phase 5 — component patching | 9 | ☐ | |
| Phase 6 — D3 scope-matched control | 10 | ☐ | |
| Phase 7 — Phi concept completion | 11 | ☐ | |
| Phase 8 — cross-model replication | 12 | ☐ | |
| Phase 9 — attack objective | 13 | ☐ | gated on Phase 4 outcome |
| Phase 10 — second corpus / power | 14 | ☐ | |
| Phase 11 — Section 20 hygiene | 15 | ☐ | partly running (see E4) |

### Compute

| | |
| --- | --- |
| SLURM concurrency cap | 6 (project rule) |
| Currently running | 6 / 6 — **at cap, cannot launch** |
| GPU work permitted | **No** — Gate 0 unmet AND cap reached |

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
