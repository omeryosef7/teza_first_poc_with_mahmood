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
| **Gate 0** | Jobs reconciled, threshold frozen, split policy explicit, registry/deviation logs current, manifest committed | ◐ |
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
| **Phase 0 — governance repair** | 4 | ◐ | audit fan-out running |
| Phase 1 — Bombness probe | 5 | ☐ | blocked by Gate 0 |
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

_(results appended as E6 when the fan-out returns)_

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
| Q1 | _(none yet)_ | | |
