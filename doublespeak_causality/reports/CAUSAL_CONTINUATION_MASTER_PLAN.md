# Doublespeak Causal Continuation — Master Plan

**Canonical, single source of truth.** This file absorbs and replaces the earlier v1 draft of 2026-08-05.
It was written after a 7-agent reconnaissance of the repo verified what exists, what was already tried, and
what is broken — **read §0 first; several of its findings change things we currently believe.**

**Project:** Tel Aviv University · Prof. Mahmood Sharif · mechanistic interpretability + red-teaming of the
Doublespeak in-context jailbreak (arXiv:2512.03771).
**Model:** Llama-3.1-8B-Instruct, bf16. **Dataset:** ClearHarm. **Judge:** StrongREJECT (MALICIOUS iff ≥ 0.25).
**Status:** planning document, 2026-08-05. Nothing in §5 has been run.

**This is a paper project.** Every phase below is written so that its output is a table or figure in a
manuscript, with a pre-registered hypothesis, a power calculation, a control, and a preserved artifact. If a
phase cannot state which paper table it produces, it does not belong in this plan.

---

# Core current result to respect

The previous sprint found a real **representational concept circuit**:

> demo-codeword K/V retrieval around **L8–L10** → **L9 / L8–11 MLP write** → **L14–L21 carry heads** →
> **L30–31 readout-proximal output**.

But **behaviorally**, ablating the concept write or the carry heads did not significantly reduce ASR, while
**refusal suppression** did everything: refusal-direction ablation raises ASR by +0.43–0.48, re-injection
drives it to 0.000, and the two pathways are causally decoupled.

⚠ **§0.5 and §0.9 below show that the behavioral half of this is not yet safe to publish** — the null was
underpowered (power 0.13/0.08) and one of the two ablations was prefill-only. P10 exists to settle it.

# Main research question

Can we turn the mechanism into either:

- **A.** a stronger controlled Doublespeak-style attack under causal intervention, **or**
- **B.** a validated optimization objective for GCG / MAC / TROPT,

while proving whether the relevant causal handle is **concept remap**, **refusal suppression**,
**attention retrieval**, or **their interaction**?

# Deliverables

1. This master plan.
2. Machine-readable manifests for every phase under `configs/manifests/` *(today: empty)*.
3. New scripts under `scripts/`.
4. SLURM wrappers under `slurm/`.
5. Raw outputs under `outputs/`, **under the §2.1 run-directory contract**.
6. Analysis reports under `reports/`, one per phase.
7. Paper-ready summary table and figures under `figures/`, each with committed plot-data JSON.
8. `reports/CLAIM_AUDIT_TABLE.md` — the final "what is established / not established" report.

---

# §0 Reality check — ten findings that change the plan

A reconnaissance pass (7 parallel auditors, ~354 tool calls) verified the repo against v1's assumptions.
Ten findings are load-bearing. **Read this section before anything else; several of them invalidate claims we
currently believe.**

### 0.1 🔴 The evidence is not preserved — 9.0 GB of results are invisible to git
`.gitignore:12` is a bare `outputs/`. Result: **367 run directories / 9.0 GB, of which 3 files are tracked**
(0.8%). `logs/` is ignored twice — 510 files, **4.0 MB** — even though 207 of its 239 `.out` files contain the
`git=<sha>` line that is *the only per-run record of which code produced which number*. The shared filesystem
is at **98% capacity** (490 GB free of 20 TB). Nothing deletes results — the risk is non-preservation of a
single unbacked copy, not destruction.

### 0.2 🔴 There is no provenance inside the artifacts
All **91** `summary.json` files carry at most `model` and `n_rows`. Across all 91: **seed = 0 recorded,
git_commit = 0, job_id = 0, timestamp = 0, argv = 0, dtype = 0, attn_impl = 0, library versions = 0.**
`ds_common.env_metadata()` (ds_common.py:82–93) already produces exactly this block and **is called by zero of
the 21 sprint scripts**. `EXPERIMENT_REGISTRY.csv` stops at 2026-07-30 — **~120 Aug 1–5 runs, including every
headline result, have no registry row.** Only 10 of 91 run dirs are named verbatim in any committed `.md`.

### 0.3 🔴 No model generations were ever saved
Every behavioral `raw.jsonl` stores scores and labels only. The one `--save-gen` flag
(`phase_behav_refusal_inject.py:66`) is **off by default and was never used in a retained run**. Consequence:
**no judge decision can ever be re-scored or audited, and the paper cannot show a single qualitative example.**

### 0.4 🔴 The "locked, zero-leakage" split leaks at the concept level
`intent_cluster` for the ClearHarm cohort is `f"clearharm::{cat}::{sha16(instr)[:8]}"` — a **per-instruction
hash**, so 86 examples produce 86 clusters and the validator's "zero intent_cluster overlap" FATAL check is
**vacuously true**. Recomputed from the artifact: **14 of 43 concepts and 17 of 21 codewords appear in both
train and test; 55 of 86 rows (64%) belong to a straddling concept.** No "generalizes to unseen concepts or
codewords" claim is currently supported.

### 0.5 🔴 The carry-head behavioral "null" is a POWER FAILURE, not a null
Post-hoc power to detect its own observed effect, at the empirically measured flip-noise level (p₀ = 0.093,
estimated from the random-ablation control arms): **0.129 (train), 0.083 (test)**. A test with ~10% power
cannot distinguish a true 0.08 effect from zero. Required n at 80% power: **n ≈ 300 for ΔASR = 0.09, n ≈ 450
for 0.07.** Worse/better: re-analysing the *same data* with the **graded 0–1 StrongREJECT score** already
stored in `raw.jsonl` gives pooled carry-head effect **+0.074, permutation p = 0.035** (control arm null,
p = 0.36) — significant where binary McNemar gave p = 0.29. **Our headline "the concept circuit is
behaviorally inert" may be an artifact of a binary outcome and n = 42.** This must be resolved before publication.

### 0.6 🟠 The Phase-8 interaction already exists — and it is significantly NEGATIVE
`phase_behav_refusal.py` already ran a complete within-item 2×2 (direct_base / ds_base / direct_refabl /
ds_refabl). The difference-in-differences estimator gives:

| split | Δ_concept | Δ_refusal | Δ_combined | **Î (interaction)** | perm p |
|---|---|---|---|---|---|
| train (44) | +0.250 | +0.432 | +0.591 | −0.091 [−0.310, +0.128] | 0.545 |
| test (42) | +0.286 | +0.476 | +0.476 | −0.286 [−0.538, −0.033] | 0.049 |
| **pooled (86)** | +0.267 | +0.454 | +0.535 | **−0.186 [−0.353, −0.019]** | **0.043** |

`D_i = +2` **never occurs** while `D_i = −2` does. Doublespeak and refusal-down are **sub-additive** — exactly
what a *shared refusal bottleneck* predicts. **Planning Phase 8 to detect a positive +0.10/+0.15 interaction is
aimed in the wrong direction.** Re-aim it as a pre-registered sub-additivity test.

### 0.7 🟠 The ceiling makes a positive interaction arithmetically undetectable at α = 1.0
`I_max = 1 − ASR(1,0) − ASR(0,1) + ASR(0,0)` = **+0.182 (train) / +0.167 (test)**. A +0.15 target consumes
83–90% of the entire headroom. 62–64% of items are already jailbroken by one manipulation alone and can only
contribute `D_i ≤ 0`. **Fix: run a sub-saturating α that lands refusal-alone ASR in 0.20–0.40** — this restores
`I_max ≥ +0.33` at no cost in n. **Only α = 1.0 has ever been run for ablation**, so the α→ASR curve must be
calibrated first.

### 0.8 🔴 The GCG evidence behind "mechanism-derived optimization fails" is invalid
Confirmed bug in `poc_stage_gcg_early/gcg_optimizer.py`: `_evaluate_candidates` calls `composite_loss`
**without** `candidate_hs`, so `repr_loss` is **identically 0.0 for every candidate**. Therefore
`selection_mode='weighted'` reduces to task-loss-only, and `'lexicographic'` picks the first eligible
candidate. **The representation objective only ever influenced the gradient, never the selection.** A second
bug drops `repr_layers` and the reference-cache identity from `CONFIG.json` and `config_hash()`, so arms
differing only in objective wiring **share a hash and can silently cross-resume each other's checkpoints**.
Additionally: of 373 GCG configs on disk, **344 are Qwen3-14B, 24 Gemma-4, 2 DeepSeek — zero Llama**, and every
Doublespeak arm used **seed 42 only**. Gate 7 has no valid evidence for or against.

### 0.9 🟠 Four core patching primitives are silently PREFILL-ONLY
`ComponentOutSwap` (:407), `SubmodulePatch` (:322), `ZHeadPatch` (:535) and `dc.LayerPatch` (:689) all
`keep = [k for k,p in enumerate(pos) if 0 <= p < seq]` — on a KV-cached decode step `seq == 1`, so they
**contribute nothing after prefill**. **The BEHAV-WRITE behavioral null was therefore a prompt-side-only
ablation**, not an ablation "throughout generation" as the reports state. Only `AllPositionZHeadAblate`,
`AllPositionProjectOut(MultiLayer)` and `AllPositionAdd(MultiLayer)` are genuinely decode-safe. Also:
`AttentionKnockout` **silently no-ops under SDPA** and `ds_common.load_model` defaults to `sdpa`.

### 0.10 🟠 Per-layer refusal directions are unvalidated; ASR ≠ compliance
The 32 `refusal_direction_llama_L*.pt` in `outputs/refusal_alllayers/` carry **zero validation metadata** —
only a tautological separation cosine. Only **5** layers were ever generation-validated, and **L12 FAILED**
(induce_gain = −0.333). Every calibrated per-layer claim rests on unvalidated directions.
Separately, a definitional trap worth a paper paragraph: **ASR = `label == MALICIOUS`, not "did not refuse".**
In the combined arm the model **complies on 95.5% (train) / 90.5% (test)** of items while ASR is only
0.727/0.548 — i.e. **23–36% of items are complied-but-benign**. That residual is an *off-target capability
limit*, not a refusal limit, and it explains the ceiling.

---

# §1 Standing rules — normative, complete

These are the accumulated rules of this project. They are binding on every phase. *(Extracted from
`CAUSAL_CIRCUIT_MASTER_PLAN.md`, the SLURM wrappers, `BUG_AND_DEVIATION_LOG.md`, `ENV_AUDIT.md`, and prior
operator instructions.)*

## 1.1 Safety and responsible handling
- All attack optimization is framed and reported as **controlled ASR measurement for defensive security
  research**. Every report states the defensive motivation.
- **Harmful prompt text and model generations never enter git, never enter a figure, and never appear in a
  `*summary*` file.** They live in `gens.jsonl` inside the run dir, which is archived, not committed.
- Any quoted qualitative example in the paper is **redacted** (truncated, harmful specifics elided) and
  reviewed by a human before inclusion.
- **Subagents must not read generation text or harmful prompts.** A cyber-safeguard classifier terminates
  agents that do. Delegate scalar/numeric work only; do text work in the main loop.
- No new harmful capability is created: we measure an existing published attack on an existing benchmark.

## 1.2 Artifact and provenance (see §2 for the full contract)
- **Every run emits** `raw.jsonl`, `summary.json`, `RUNMETA.json`, `DONE.json`, and (for generation phases)
  `gens.jsonl`. A run without `DONE.json` is not a result.
- **Never overwrite.** All output dirs are `{phase}_{cohort}_{YYYYMMDD_HHMMSS}_{jobid}`. Fixed-name dirs are
  banned (62 currently exist and are clobber-on-rerun).
- Every numeric claim in a report cites its **exact run-dir basename**.
- `EXPERIMENT_REGISTRY.csv` gets one row per run, generated automatically.

## 1.3 SLURM execution
- **No SLURM dependencies** (`--dependency` is forbidden). **Maximum 6 parallel jobs.** **L40S only** —
  keep the `nvidia-smi` guard that exits 1 on any other GPU. **Never trim the dataset to save compute.**
- Partition `killable`, account `gpu-research`, `--gpus=1`, `mem=64G`, `cpus=8`,
  `--nodelist=n-801..n-805,t-806`.
- **`--export` silently truncates comma-containing values** (`DSSPLITS=dev,heldout` becomes `dev`). Put
  comma-lists in the wrapper's defaults, never in `--export`. Verify row counts after every "COMPLETED".
- Smoke test on 2 examples before every full launch. A smoke run writes to a `*_smoke_*` dir.
- Transient `slurmstepd cgroup` failures are node infrastructure, not code — resubmit, and log that you did.

## 1.4 Environment and numerics
- Conda env `poc_stage2` (python 3.12, torch 2.7.1+cu126, transformers 5.12.1).
  `HF_HUB_OFFLINE=1`, `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.
  *(TROPT lives in its own venv: python 3.13 / torch 2.11 / transformers 5.8.1 — cross-env comparisons must
  re-verify tokenization.)*
- **bf16 for every primary causal conclusion.** Quantization is exploratory only and must reproduce the
  five positive controls (§5.P12) before any claim.
- **Default SDPA; do not disable flash.** **Force `attn_implementation='eager'` for, and only for, any hook
  touching attention patterns or edges** — `AttentionKnockout` silently no-ops under SDPA.
- Fixed seeds, and the seed value **must be written into `RUNMETA.json`** (today it never is).

## 1.5 Statistics
- **Paired designs throughout**; dev(train) and heldout(test) aggregated **separately**, never pooled.
- Representational per-layer/per-head families: **Wilcoxon signed-rank + Holm** over the full family
  (32 layers, or 32×32 = 1024 heads). *Never a sign-flip permutation* — its 1/n_perm resolution floor is
  coarser than the Holm threshold and returns artifactual p = 0.
- Behavioral binary outcomes: **exact McNemar** + bootstrap CI. **Behavioral graded outcomes: paired Wilcoxon
  / sign-flip permutation on the 0–1 StrongREJECT score** (new in v2 — see §0.5).
- Percentile bootstrap CIs, **fixed RNG seed**, all per-example paired differences saved.
- **Report post-hoc power beside every non-significant result**, and report the exact test's granularity floor
  (at n = 42 under m = 21, no result with fewer than 10 unanimous discordant pairs can ever be significant).
- **Pre-register** the primary family before looking at test data (§6).

## 1.6 Coverage
- **Every layer L0–L31 individually**; every head where head-level claims are made.
- **n ≥ 20 unique examples per cell.** Repeated seeds/generations are not new examples. A cell is
  split × condition × layer × head × activation × position-set × direction × control × strength.
- **Train/test separation is absolute.** Select on train/dev, freeze, then run the frozen configuration on
  locked test — always the *full* layer sweep on test, never best-layer-only.
- **No cherry-picking.** Save and report all layers, heads, controls, nulls, failures, and preempted runs.
- **A–G granularity grid** for each principal intervention family: A each layer · B canonical windows
  (early L0–9 / mid L10–19 / late L20–31 + unions) · C sliding widths 2/4/8, every valid window ·
  D cumulative prefixes · E cumulative suffixes · F mechanism-derived (train-frozen) · G all layers.
- **Machine-readable manifests first.** No job launches before `configs/manifests/<phase>.json` enumerates
  every expected cell. *(Today `configs/manifests/` is empty, which is why no missing cell is detectable.)*
- Every claim requires: self-swap/no-op = 0, a norm-matched random direction, count-matched random
  heads/positions/edges, and shuffled/unrelated/benign donors where relevant.

## 1.7 GCG / MAC-specific
- **Always pass `--no-filter-cand`.** `filter_cand=True` applies a BPE decode→re-encode round trip that
  rejects essentially every candidate and silently freezes optimization.
- **`--suffix-placement user`** (the fixed default). The `assistant` value exists only for exact v1 replay of
  the historical placement bug.
- Compute-matching is on **candidate forward passes per arm-seed**, and the number is reported.
- Every arm runs **≥ 3 seeds** before any comparative claim (all existing runs are seed 42 only).
- Suffix **text** (not token ids) is what transfers across models.

## 1.8 Honesty
- **Trust raw recomputation over report prose.** Where they disagree, the raw wins and the report is corrected.
- A retracted result stays retracted and is never silently rebuilt on (`phase5b_qkv.py` Q/K/V).
- Negative results are first-class deliverables and are reported with the same rigor as positives.

---

# §2 Artifact & provenance contract (P0 deliverable — do this first)

> This section exists because §0.1–0.3 found that the project currently cannot prove what produced any of its
> numbers. For a university paper this is the single highest-priority repair.

## 2.1 The run-directory contract
Every run emits, into `outputs/{phase}_{cohort}_{ts}_{jobid}/`:

| file | content | committed? |
|---|---|---|
| `RUNMETA.json` | **written first, before any compute** — run_id, script path, full `sys.argv`, resolved args, seed, model id + revision, tokenizer name + hash, dtype, `attn_implementation`, chat-template hash, git commit + dirty flag, SLURM job id, hostname, GPU name, torch/transformers versions, start ts | ✅ yes |
| `summary.json` | aggregates; **must** include model, cohort, n_rows, seed, and per-split blocks | ✅ yes |
| `DONE.json` | rows_written, end ts, wall seconds, exit status | ✅ yes |
| `raw.jsonl` | per-example numerics and labels — **no free text** | ⬛ archive |
| `gens.jsonl` | generated text, one row per (item, arm) | ⬛ archive, never committed |
| `slurm.out` / `slurm.err` | copied or hard-linked into the run dir | ✅ yes |

## 2.2 Immediate repairs (P0, hours not days)
1. **Un-ignore the evidence.** Replace the bare `outputs/` rule with ignore-then-unignore:
   `doublespeak_causality/outputs/**` + `!**/summary.json` + `!**/RUNMETA.json` + `!**/DONE.json`.
   Estimated committed size: well under 100 MB.
2. **Commit `logs/` wholesale** — 4.0 MB, and it holds the only per-run commit hashes. Remove the rule from
   both `.gitignore` files.
3. **`ds_common.write_runmeta(out_dir, args)`** — implement, and call as the first statement of all 21
   `scripts/phase_*.py`. Reuse the existing `env_metadata()`.
4. **Backfill.** `scripts/backfill_runmeta.py` reconstructs what it can for the 91 existing Aug 2–5 dirs from
   `logs/*.out` (207 contain `git=<sha>`), the dir name (ts + job id), and the wrapper defaults. Mark every
   reconstructed field `"source": "reconstructed"` — never fabricate a value silently.
5. **`--save-gen` ON by default** in all five generation harnesses, writing `gens.jsonl`.
6. **Ban fixed output names** — convert the 62 offenders, starting with `outputs/refusal_alllayers` (the
   default `DSREFDIR` for the whole behavioral chain; overwriting it would invalidate every downstream refusal
   result with no trace).
7. **Regenerate `EXPERIMENT_REGISTRY.csv`** from `RUNMETA.json` (`scripts/update_registry.py`), backfilling
   ~120 missing runs. Rebuild `ARTEFACT_MANIFEST.json` (path/bytes/sha256) over the full tree; one recorded
   hash is already stale.
8. **Make figures reproducible.** Every `make_*_figure.py` currently resolves inputs by
   `sorted(glob(...))[-1]` or a hardcoded job id — it silently re-points at whatever ran last. Replace with an
   explicit `--run-id` (or registry lookup), and have each figure write its **plot-data JSON** next to the PNG,
   committed. A fresh clone must be able to regenerate every figure.
9. **Archive.** `tar + zstd` the run dirs into `archive/` with a checksum manifest, and copy off the
   department NetApp (98% full). Regenerable activation dumps (`pair_reps_*`, ~5.4 GB of the 9.0 GB) may be
   pruned *after* archiving, never before.
10. **`scripts/audit_artifacts.py`** — one command, non-zero exit on regression: dirs missing any contract
    file, empty dirs (20 exist), registry-vs-disk drift, manifest hash drift, dirs with no matching log, free
    space on the mount. Run it in CI and before every report.

## 2.3 Disambiguate known collisions before publishing
Job **708038** produced two dirs (`..._125311_708038` = aborted, raw only, no summary; `..._133355_708038` =
complete, authoritative). Four `toctou` job ids and `head_attr` 697370/697371 likewise have two same-script
dirs each. Mark the authoritative one in the registry and in every citing report.

---

# §3 What we inherit, and at what confidence

The v2 plan must not re-derive what is already solid, and must not build on what is not. Corrected status:

| Result | Confidence | Note |
|---|---|---|
| Concept circuit: demo-KV L8–L10 → L9 MLP write → L14–21 carry → L30–31 output | **Solid** | Wilcoxon+Holm, locked test, self-swap = 0. Use **L8–L10** (clearharm L11 CI includes 0), not L8–L11 |
| Carry heads partially sufficient (install → reading +0.16…+0.47) | **Solid (representational)** | v2 bench +0.326/+0.348; behavioral sufficiency **never tested** |
| Query→demo **edge** knockout null | **Solid negative** | specific effect +0.002 [−0.0004, +0.0046] ns; all-query control 13–49× larger |
| Readout ≠ mechanism (readability peaks L31, causality at L9) | **Solid** | but "grows monotonically" is false — flat/noisy then terminal spike |
| Refusal ablation → ASR +0.43…+0.48, p ≤ 0.004 | **Solid** | largest, most robust effect in the study |
| Refusal re-injection → ASR 0.000 at α = 12, coherence-audited | **Solid** | except curated-test (p = 0.50, floor-limited) |
| DS suppresses the refusal axis from ~L8, grows with depth | **Solid** | but not "at all layers" — fails hs1–6; on curated DS sits ≥ neutral in hs16–31 |
| Concept ⊥ refusal (\|cos\| ≤ 0.153) | **Solid** | not "0.01–0.06 at every layer" (those are means) |
| Causal decoupling (write ablation leaves refusal unmoved) | **Solid** | frac restored ≤ 5% of gap everywhere |
| Refusal projection predicts jailbreak, AUC 0.874 | **Solid** | pooled; per split 0.867/0.891; CI [0.797, 0.940] |
| **Carry/write behaviorally inert** | **⚠ UNSAFE** | **power 0.13/0.08; graded score gives p = 0.035. Must be re-tested (§0.5)** |
| **BEHAV-WRITE was "ablated throughout generation"** | **⚠ FALSE** | prefill-only (§0.9). Must be re-run decode-safe |
| **Mechanism-derived GCG is net-negative** | **⚠ INVALID** | the objective never entered candidate selection (§0.8) |
| "Generalizes to unseen concepts/codewords" | **⚠ UNSUPPORTED** | 64% of rows straddle at concept level (§0.4) |
| Q/K/V null | **RETRACTED** | positioning artifact, n = 2, no positive control |

---

# §4 Coverage of the requested experiments

| # | Requested experiment | Prior status | Phase in v2 |
|---|---|---|---|
| B1 | Query→demo attention-edge knockout | **DONE** — clean controlled negative | P3 (extend destinations/sources only) |
| B2 | Activation patching on candidate **induction heads** | **PARTIAL** — 32×32 scan exists but no induction-head ID, and z is patched at the **answer position only** | **P4** |
| B3 | Head→MLP path patching to find the write | **PARTIAL** — direct/total + MLP→head mediation; **no sender×receiver sweep** | **P5** |
| B4 | Distill an attack objective, use it for GCG/MAC | **PARTIAL** — objective distilled + graded; **0 of 13 arms ever run** | **P9** |
| B5 | Targeted induction-head **path patch** | **NOT DONE** — flagged future work in 5 docs | **P4 + P5** |
| B6 | Patch **all** codeword occurrences | **PARTIAL** — all-demo done; `--positions all` implemented but **never launched**; per-occurrence never done | **P2** |
| B7 | Jacobian / projection-matrix readout | **NOT DONE** — zero Jacobian code in the repo | **P6** |
| B8 | Keep concept and refusal directions separated | **PARTIAL** — cosines + decoupling done; **zero orthogonalization code**, no factorial | **P7** |
| B9 | Re-run Doublespeak + GCG under corrected setup | **HALF** — DS re-run done; **GCG half not done, and its stack is buggy** | P1 + **P9** |
| B10 | Switch to ClearHarm | **DONE** since 2026-08-02 | P1 (+ v3 in P1b) |
| B11 | Quantized model | **NOT DONE** — no quantization code path at all | **P12** |
| B12 | Different frameworks | **NOT DONE** — one framework only, zero TransformerLens/nnsight | **P11** |
| B13 | **Refusal-down + Doublespeak, combinations to raise ASR** | **PARTIAL** — the combined arm exists (ds_base .386 → ds_refabl .727, p = 2.7e-4 train) but only 1 of 4 cells is significant, **no interaction test, no α grid** | **P8** (the centrepiece) |

---

# §5 Phases

Each phase states: **hypothesis → design → primary outcome → n and power → controls → exit criteria →
paper artifact.**

---

## P0 — Trust the repo (blocking, no GPU)

**Why:** §0.1–0.3. Nothing else may launch until this lands.

**Do:** all ten items of §2.2 and §2.3. Plus:
- Write `configs/manifests/` entries for every phase below **before** its first job.
- Extend `scripts/validate_experiment_coverage.py` to the **behavioral schema** (`{id, split, cohort,
  <arm>_label, <arm>_score}`) — it currently `KeyError`s on every behavioral dir, so *none* of our headline
  results is covered by the mandated validation. Add GCG and quantized schemas.
- Add `scripts/validate_all_outputs.py`: recompute every `summary.json` number from its `raw.jsonl`, verify
  train/test disjointness, verify all manifest cells present, **fail on a missing cell**.
- **Factor the judge into one module** `scripts/behav_judge.py` (`MAL_THRESHOLD`, `REFUSAL_MARKERS`,
  `kw_refusal`, `classify`, `judge`, `asr/refusal_rate/empty_rate`). It is currently copy-pasted verbatim into
  ≥ 5 files; a threshold change today silently desynchronizes them.
- **Synthetic tests for the untested footguns:** `AttentionKnockout` (must raise, not no-op, under SDPA),
  `ComponentCapture`, `resolve_positions`, and `SubmodulePatch`'s attn_out/mlp_out paths.

**Exit:** `audit_artifacts.py` green; every phase has a manifest; validators pass on the authoritative runs
and *fail loudly* on a deliberately corrupted copy.
**Paper artifact:** the reproducibility/artifact-availability statement.

---

## P1 — Corrected baseline + drift envelope (GPU, small)

**Why:** every effect below is measured against a baseline, and the same `ds_base` condition has produced
test ASR between **0.286 and 0.381** across four existing runs (~10 pp of greedy-decode drift).

**Design:** the 10 Phase-1 conditions of v1 (direct, neutral, doublespeak, benign-remap, shuffled-binding,
unrelated-binding, ±random-suffix placeholder, ±refusal ablation), both cohorts, both splits, **3 repeated
runs of the main baseline** with identical config.

**Primary outcome:** paired baseline table + a **measured drift envelope** (per-arm test–retest discordance;
the existing replicate pair gives 4.0% over 400 paired comparisons, vs 18.5% for control ablations — i.e.
**decode noise is only 22% of flip noise**; the rest is item × intervention heterogeneity that more seeds
cannot remove).

**Exit:** any later arm claiming a sub-0.10 ASR improvement is declared uninterpretable unless it exceeds this
envelope. **Report `PHASE1_CORRECTED_CLEARHARM_BASELINE.md`.**
**Paper artifact:** Table 1 (conditions × cohorts) + a methods paragraph on decode drift.

---

## P1b — ClearHarm v3 dataset (CPU + small API spend)

**Why:** §0.4 (concept-level leakage) and §0.5 (n ≈ 300–450 needed).

**Target: N = 200 examples, ~120 concepts, split 100 train / 50 dev / 50 test, 6 conditions = 1,200 rows.**
The 50/50 dev/test sizing is deliberate: it lets an analysis restricted to a 40% responsive subgroup still
clear the ≥ 20-per-cell mandate — which is exactly what killed Phase 5 curated-heldout (n = 21) and Phase 7b
(n = 9–13).

**Composition arithmetic (all verified against the source):**
| step | yield | cost |
|---|---|---|
| Lexicon-fallback extractor over the 62 silent-`None` rows | 86 → **119** examples / 45 concepts | **zero API calls** |
| Paraphrase-recover the 31 multi-token-concept drops (all are single *words* tokenizing to 2–4 tokens; 0/31 recoverable by sub-word) | +31 | small; record `provenance='paraphrased_for_single_token'` + the original ClearHarm string |
| Re-run the 62 `None` rows with gpt-4o and log the failure reason (`_llm_pick_concept` swallows every exception) | +up to 29 | small |
| Existing v2 expansion | +30 | done |
| New expansion with codewords drawn from a **pool** instead of asked from the LLM | +~50 | the joint single-token gate is why yield was 10.7%; concept-only rate is 73.5% |
| **Total** | **200–230** | |

**Also:**
- **Replace the codeword lexicon.** The hardcoded 42-item list yields only 21 single-token entries (two are
  junk: `lantern2`, `pebble2`). The real pool is **16,408** dictionary words that are single tokens at ≥ 4
  chars. Enforce **one codeword per concept**, and **disjoint codeword sets per split** if we want the
  "unseen codeword" claim.
- **Real intent clustering:** `intent_cluster = normalized target concept`, not a per-instruction hash.
  Concept identity is the dominant leakage channel.
  ⚠ **CORRECTED 2026-08-05 (this section originally claimed "zero ClearHarm instruction pairs exceed TF-IDF
  cosine 0.5" — that is FALSE).** Recomputed over all 179 instructions: **max pairwise cosine 0.690, with 3
  pairs above 0.5.** The recommendation stands, because the *built* v3 split's maximum **cross-split**
  cosine is below that and no concept straddles — but paraphrase leakage is not identically zero, so the
  post-split near-duplicate audit is **required**, not optional. Estimated true cluster count: ~45–60
  (v3 achieved 40 concept-level clusters over 45 concepts after plural collapse).
- **Complete the conditions** for the 30 expanded rows (they lack SHUFFLED_BINDING and UNRELATED_TARGET):
  **zero API cost**, pure reverse-substitution — verified that all 360 stored demos contain their codeword and
  none leak the original concept.
- **Fix v2's stale metadata** (`n_examples=86` → 116, `n_concepts=43` → 73) before any run uses it.
- **`scripts/validate_dataset_v3.py`** with FATAL checks: prompt reconstruction after chat template; exact
  codeword occurrence indices (each demo + query); single-token constraint; **zero concept overlap across
  splits**; **zero codeword overlap**; zero cross-split prompt pair above cosine 0.7; condition completeness;
  harmful-content masking in logs. Re-run it against v1 and **publish the v1 leakage numbers** as a documented
  limitation.

**Exit:** v3 frozen, validator green, leakage table published for both v1 and v3.
**Paper artifact:** the dataset section + a benchmark-construction appendix.

---

## P2 — All codeword occurrences (B6)

**Free win first:** `scripts/phase6_mlp_causal.py` **already implements `--positions all`** (lines 74–76) and
it was **never launched**. Run it on both cohorts and v2 before writing any new code.

**New:** `resolve_all_occurrences(lm, templated_text, word)` in `pair_common.py`, returning
`{demo_positions, per_demo_positions, query_position, all_positions, control_pool}` — lifting and unifying the
logic currently hand-rolled in `phase_behav_write.py:107–115`.

**Position sets:** all demo · **each demo occurrence individually** · first/second demo half · query ·
demo+query · final prompt token · answer position · unrelated-noun · punctuation · count-matched random.
**Intervention families:** resid_pre/resid_post/attn_out/mlp_out replace; concept add/remove; refusal
add/remove; combined.
**Readouts:** forced-choice `p_concept`, refusal projection, and behavioral ASR **only** for train-frozen sets.

**Hypothesis worth the paper:** *the concept remap and the refusal suppression are carried by the **same
demonstration tokens** (both onset at L8–11) but on **separate pathways** (already shown). If they are carried
by **different occurrences** — e.g. early demos vs late demos — that is a new, sharper dissociation.*

**Exit:** an occurrence × layer × family map for both readouts.
**Paper artifact:** the all-occurrence heatmap (a figure the original Doublespeak paper does not have).

---

## P3 — Attention causality, extended (B1)

B1 is **already a clean negative** and should be *presented*, not re-litigated. What is missing is destination
coverage: the existing knockout used the query codeword and the FC answer position, but **not the final prompt
token / first-generated-token decision point** — which is precisely where §8's refusal decision is read.

**Design:** destinations {query codeword, final prompt token, **decision token**}; sources {demo codewords,
demo binding spans, all previous keys (firing control), count-matched random}; heads {all, L8–11 band,
L14–21 band, train-selected induction candidates, random count-matched}. Eager attention, asserted.

**Exit:** either a causal edge appears at the decision token (new result), or the paper states with full
coverage that **retrieval is distributed/redundant with no single query→demo edge bottleneck**.
**Paper artifact:** `PHASE3_ATTENTION_CAUSALITY_TARGETED.md` + the layer×head edge-effect heatmap.

---

## P4 — Induction heads: identify, then patch properly (B2, B5)

**The decisive gap is the patch POSITION, not the head set.** `phase5_head_zpatch.py` patches `z` at the
**forced-choice answer position only**, and `PHASE5_HEADS.md:74` already concedes *"a head writing at an
EARLIER position the answer reads is not captured"* — so the L8–11 retrieval heads were **never patched where
they act**.

**P4a — identification (train only, descriptive).** No induction-head identification has *ever* been done on
ClearHarm; the only evidence is a **band-mean 3.508× attention ratio on n = 12 prompts of the old carrot/bomb
pair**. Compute per-head, per-layer, on train: attention mass from the query-codeword position and from the
decision position back to each demo-codeword position; a previous-token-head score; a repeated-token/induction
score; overlap with the L8–11 K/V necessity band. **Freeze the candidate set before touching test.**

**P4b — activation patching at the right positions.** All 32×32 heads × {pattern, Q, K, V, z, head-result} ×
{demo codewords, query codeword, decision token, answer position, all codewords}, both readouts, both splits.
- **Q/K/V must patch SOURCE positions with a positive control that fires**, or not be reported at all
  (§0.9 / the standing retraction).
- **Assert the hook fired** by measuring activation deltas — do not infer a null from a silent no-op.

**P4c — behavioral.** For train-frozen candidates: prefill-only vs decode-only vs both, using **decode-safe
primitives only**, graded score primary.

**Exit:** each candidate head classified as necessary / sufficient / behaviorally necessary / irrelevant /
refusal-related.
**Paper artifact:** `PHASE4_INDUCTION_HEAD_PATCHING.md` + the position × activation-type necessity matrix.

---

## P5 — Head→MLP path matrix (B3)

**Gap:** no sender-head × receiver-MLP sweep exists anywhere. What exists is direct-vs-total on 10 hand-picked
heads and one MLP→head mediation test.

**Design:** senders {all L8–11 heads, all L14–21 heads, train-selected induction heads, train-selected carry
heads, random count-matched} × receivers {every MLP from sender+1 to L31}. Six path tests (sender patched with
downstream frozen; sender ablated with receiver restored; receiver patched with sender clean; direct-vs-total;
edge necessity; edge sufficiency). Controls: self-freeze (must be exactly 0), random receiver, random sender,
**non-downstream impossible control**, norm-matched path.

**Reuse:** `50_path_patching.py` freeze primitives (already reused by `phase7_direct_total.py`), and the AtP
stack in `48_attribution_patching.py` for ranking only — **AtP never substitutes for exact patching in a
claim**.

**Exit:** a causal graph with quantified edges for the concept pathway, and — if it exists — a **separate
refusal-suppression graph**. That second graph is the genuinely novel object.
**Paper artifact:** `PHASE5_HEAD_TO_MLP_PATH_MATRIX.md` + the circuit figure.

---

## P6 — Jacobian / projection-matrix readout (B7)

**Gap:** zero Jacobian code exists (the single grep hit is a comment). What exists is a plain linear
projection lens.

**Build:** for each layer and position, the local linear map from a residual perturbation to a target scalar —
**both** targets: (a) concept logit difference (concept − codeword), (b) the refusal scalar. Build on
`48_attribution_patching._ActGradCapture` and `pc.ZHeadCapture`, which already retain graph nodes.

**Fit on train, freeze, then evaluate on locked test.** Compare, per layer: naive logit lens · plain projection
lens · Jacobian readout · actual causal intervention effect · behavioral predictive power.

**Pre-registered predictions (this is what makes it paper-worthy — it is falsifiable):**
1. The **concept** Jacobian peaks at **L9 / L14–21**, not L31 — i.e. it localizes the *mechanism* where the
   logit lens localizes only *readout proximity*.
2. The **refusal** Jacobian peaks at **L16–L22**, matching the calibrated behavioral rescue layer (L22).
3. The concept Jacobian remains **behaviorally inert**; the refusal Jacobian **predicts held-out ASR** better
   than the current projection (AUC > 0.874).

**Exit:** readout-peak-vs-causal-peak figure + a per-layer correlation table (readout score vs measured causal
effect).
**Paper artifact:** `PHASE6_JACOBIAN_PROJECTION_READOUT.md` — a methods contribution, not just a result.

---

## P7 — Concept ⊥ refusal, rigorously (B8)

**Gap:** cosines and one decoupling test exist; **zero orthogonalization code**, no whitened similarity
(listed as "queued" since Aug 2), no factorial, and the refusal direction is built from a **carrot/bomb** bench
rather than ClearHarm.

**Build seven direction families** per layer: concept · refusal · signature · concept ⊥ refusal ·
refusal ⊥ concept · Jacobian-concept · Jacobian-refusal.

**Blocking prerequisite (§0.10):** the 32 per-layer refusal directions have **zero validation metadata** and
only 5 layers were ever generation-validated (**L12 failed**, induce_gain = −0.333). **Re-build all 32 on a
ClearHarm-native harmful/harmless bench and generation-validate every layer** (ablate_gain, induce_gain)
before any per-layer refusal claim. This retroactively underwrites the calibrated depth-localization result.

**Tests:** cosine + **covariance-whitened** similarity across all layers, train and test; projection
separability; intervention separability (add/remove each, measure *both* readouts and ASR); and the 8-cell
factorial (concept↑/↓ × refusal↑/↓ × unchanged).

**Exit:** a 2D causal plane showing which axis controls `p_concept` and which controls ASR.
**Paper artifact:** `PHASE7_CONCEPT_REFUSAL_SEPARATION.md` + the causal-plane figure.

---

## P8 — Doublespeak × refusal-down: the combined causal ASR factorial ⭐ **CENTREPIECE**

This is the phase that answers *"what happens when we do refusal-down + Doublespeak, and can combinations make
ASR larger?"* — and §0.6/§0.7 mean it must be designed differently than v1 assumed.

### P8.0 — Free result, no GPU (do this in week 1)
The interaction is **already computable** from `outputs/behav_refusal_*_708038 / _708039`. Pooled
**Î = −0.186 [−0.353, −0.019], perm p = 0.043** — significantly **sub-additive**. Write it up as the pilot,
and let it set the hypothesis.

### P8.1 — Calibrate α (blocking)
**Only α = 1.0 has ever been run for ablation.** Sweep α ∈ {0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0} on Direct and
find the α landing refusal-alone ASR in **0.20–0.40**. This raises `I_max` from +0.17 to ≥ +0.33 and makes the
interaction detectable at n ≈ 200–215 instead of never.

### P8.2 — The full arm list
The 2 × 2 core is arms 1/3/4/6. **Arms 1–6 + 13 are the pre-registered primary set** (§6); the rest are run
and reported with CIs but labelled exploratory.

| # | arm | role |
|---|---|---|
| 1 | direct baseline | 2×2 cell (0,0) |
| 2 | neutral baseline | floor |
| 3 | doublespeak baseline | 2×2 cell (1,0) |
| 4 | direct + refusal-down | 2×2 cell (0,1) |
| 5 | neutral + refusal-down | floor control |
| 6 | **doublespeak + refusal-down** | 2×2 cell (1,1) — **the centrepiece** |
| 7 | doublespeak + concept-up | never run before |
| 8 | doublespeak + concept-up + refusal-down | never run before |
| 9 | doublespeak + concept-write install + refusal-down | never run before |
| 10 | doublespeak + carry-head install + refusal-down | **never run — highest priority extension** (the carry heads are the only component with both necessity and representational sufficiency, and their behavioral sufficiency has never been tested) |
| 11 | doublespeak + induction-head/path install + refusal-down | gated on P4/P5 validating a path |
| 12 | doublespeak + concept-up + carry-head install + refusal-down | full stack |
| 13 | doublespeak + random-direction ablation | **specificity control (primary)** |
| 14 | doublespeak + random concept install | specificity control |
| 15 | doublespeak + shuffled-donor install | donor control |
| 16 | doublespeak + unrelated-donor install | donor control |
| 17 | direct + GCG baseline | bridges to P9 |
| 18 | doublespeak + GCG baseline | bridges to P9 |
| 19 | doublespeak + GCG + refusal-objective | bridges to P9 |
| 20 | doublespeak + GCG + concept-objective | bridges to P9 |
| 21 | doublespeak + GCG + combined objective | bridges to P9 |

*(Arms 17–21 execute inside P9 once the optimizer bugs of §P9.0 are fixed; they are listed here so the
behavioral comparison is designed as one family.)*

**Intervention strengths**
- refusal-down α grid: **0, 0.25, 0.5, 1.0, 1.5, 2.0** — plus the **sub-saturating α selected in P8.1**,
  which is the one used for the primary interaction estimate.
- **calibrated per-layer α** based on the measured direct−DS projection gap.
- **Per-layer own refusal direction for the primary result** — *not* one L18 vector reused across all layers
  (the standing rule against reusing one layer's vector). The Arditi-style all-layer L18 vector is retained as
  a **replication/comparison arm only**. ⚠ Blocked on P7 re-validating all 32 per-layer directions (§0.10).
- concept α grid: **0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0**.
- **combined 2D grid** (concept α × refusal α) for train-frozen windows — requires the new
  `scripts/phase_alpha_grid.py` driver, since every existing sweep is strictly 1-D.

**Layer/window settings:** L9 · L16 · **L22** · L28 · early/mid/late · L8–11 · L16–22 · all layers ·
A–G granularity where feasible.

**Metrics (all recorded every arm):** graded StrongREJECT score (**primary**) · ASR (secondary) ·
**compliance rate, reported separately from ASR** (§0.10) · `refusal_rate` · `p_concept` · refusal projection ·
concept projection · output coherence · `empty_rate` · judge-failure count.

**Statistical tests**
- paired Wilcoxon / sign-flip permutation on the graded score vs the DS baseline (**primary**);
- paired exact McNemar vs the DS baseline (**secondary**, preserves comparability with existing runs);
- paired test vs **refusal-down alone** (the arm that matters for "does the concept add anything");
- **interaction:** `D_i = Y_i(1,1) − Y_i(1,0) − Y_i(0,1) + Y_i(0,0)`, tested by paired t / sign-flip
  permutation — **not** McNemar, since `D_i` is not binary;
- bootstrap CIs, fixed seed, all per-example differences saved;
- **Holm over the 5-arm primary family only** (§6), not over all 21.

**Note:** DS+concept-up, DS+carry-install and DS+write-install have **literally never been run in generation**
(`grep concept_up` returns zero hits), and **carry-head behavioral sufficiency has never been tested at all** —
despite the carry heads being the only component in the whole circuit with both necessity and representational
sufficiency. **Prioritize the behavioral carry-head install.**

### P8.3 — Estimator and statistics
- **Primary outcome: the graded 0–1 StrongREJECT score** (paired Wilcoxon / sign-flip permutation).
  This costs 63–65% less n than the binary indicator. Binary McNemar is retained as a **pre-registered
  secondary** so results stay comparable to existing runs.
- Interaction estimator (baselines cancel exactly because all four cells are within-item):
  `D_i = Y_i(1,1) − Y_i(1,0) − Y_i(0,1) + Y_i(0,0)`, `Î = mean(D_i)`; test by paired t or sign-flip
  permutation. **McNemar does not apply** — `D_i` is not binary. Measured `Var(D) = 0.624` pooled (pairing buys
  a 22.5% variance reduction vs independent arms — state this in the paper to justify the design).
- **Report ASR and COMPLIANCE as two separate outcomes.** At α = 1.0 the combined arm complies on 90–95% of
  items while ASR is 0.55–0.73: **23–36% are complied-but-benign**. That gap is an off-target capability
  limit, not a refusal limit — a genuine result, and the mechanism behind the ceiling.

### P8.4 — Ceiling-avoiding subgroup (pre-register or don't run)
Restricting to items where refusal-down **alone fails** restores full headroom and gives enormous effects
(train +0.684, test +0.474 on n ≈ 19). **But the subgroup is defined by an outcome** — selecting it on the
same data is selection-on-the-outcome and will inflate the estimate. It must be defined on a **separate
calibration split** and pre-registered, and the pool oversampled ~2.2× (the subgroup is ~45% of items).

### P8.5 — Power
| driver | requirement |
|---|---|
| binary McNemar, m = 5, p₀ = 0.093, ΔASR = 0.15 | n = 178 |
| graded score, m = 5, d = 0.075 | n = 208 |
| interaction I = 0.15, m = 5 | n = 324 |
| interaction I = 0.10 | n = 729 → **declared out of scope** |
| resistant subgroup of 150–200 analysable items | n = 334–445 |

**⇒ v3 at N = 200 (100/50/50) runs P8 at reduced but honest power; N = 350–450 is the number that makes the
interaction test properly powered.** Decide explicitly, and state the achieved power in the paper.
**Seeds: 3, used to average the graded score per item — not to add rows and not to chase power** (1→5 seeds
saves only ~10–12% of n at 5× the GPU and judge cost). **Spend GPU on items, not seeds.**

**Exit:** additive / redundant / synergistic verdict with a CI; whether concept-up adds anything once refusal
is suppressed; the strongest controlled-ASR arm and whether it is mechanistically interpretable.
**Paper artifact:** `PHASE8_COMBINED_CAUSAL_ASR.md` + the 2D α-grid heatmap + the causal-plane figure.

---

## P9 — GCG / MAC / TROPT: Gate 7, for real (B4, B9)

### P9.0 — Fix the optimizer before running anything (blocking)
1. **The selection bug (§0.8).** Pass `reference_hs` (and the direction tensors) into `_evaluate_candidates`
   so `repr_loss` actually enters candidate selection. Until this lands, **every "the mechanism objective
   doesn't help" statement in this project is unsupported** — the objective was never used for selection.
2. **The provenance bug.** Add `repr_layers`, `reference_cache_dir` (as a content hash) and `objective_name`
   to `ObjectiveWeights` so they land in `CONFIG.json` and `config_hash()`. Otherwise arms differing only in
   objective wiring share a hash and **silently cross-resume each other's checkpoints**.
3. **Add a `llama` model family** — ~10 lines across 4 files (`run_optimization.py:81`,
   `build_reference_cache.py:54`, `evaluate_cross_model_transfer.py:194`, `model_adapter.py`
   `_EMBED_PATHS_BY_FAMILY`). **Zero Llama GCG runs exist today.**
4. **Build the Llama+ClearHarm manifest.** The split has **no affirmative-target field**; targets exist in
   `data/manifests/clearharm_*.csv` but the id schemes don't match (0/86 exact overlap) — **join on
   instruction text (86/86 joinable)**.
5. **Objective registry** — one `--objective NAME` flag instead of ad-hoc lambda/cache combinations.
6. **Generalize the ASR evaluator** — `25_eval_gcg_asr.py` hardcodes exactly 3 arms.
7. **Seed driver** — 3 seeds (42, 43, 44) per arm; all existing evidence is single-seed.

### P9.1 — Freeze, then arms

**Before running, freeze:** (1) dataset and prompts, (2) judge, (3) suffix budget, (4) compute budget,
(5) all objective definitions, (6) train/test split, (7) `configs/manifests/phase9_gcg_mac_matrix.json`.

**Compute-matched arms (16)**

| # | arm |
|---|---|
| 1 | no suffix, direct |
| 2 | no suffix, doublespeak |
| 3 | vanilla GCG, direct |
| 4 | vanilla GCG, doublespeak |
| 5 | GCG optimizing harmful target logits only |
| 6 | GCG optimizing concept readout objective |
| 7 | **GCG optimizing refusal suppression objective** ← first to run |
| 8 | GCG optimizing combined concept-up + refusal-down |
| 9 | GCG optimizing Jacobian concept objective (gated on P6) |
| 10 | GCG optimizing Jacobian refusal objective (gated on P6) |
| 11 | MAC/TROPT concept objective |
| 12 | MAC/TROPT refusal objective |
| 13 | MAC/TROPT combined objective |
| 14 | GCG with attention/carry objective — **only if P3–P6 validate one** |
| 15 | random suffix control, same length |
| 16 | transfer: suffix learned on train, evaluated on locked test |

**Primary objective candidates**
- **A.** `refusal_projection_down` at **L22, decision token** ← start here; the only axis with demonstrated
  behavioral potency
- **B.** calibrated multi-layer refusal-down, L16–L22
- **C.** `concept_up` at the forced-choice answer position
- **D.** `concept_up` **orthogonalized against refusal** (needs P7)
- **E.** combined: maximize concept-readout, minimize refusal-projection, **plus a penalty for output
  degeneration**
- **F.** attention/carry objective **only if causally validated**: increase the train-frozen causal *path*
  activation, never the observational signature

**Do not optimize on**
- `doublespeak_signature` alone — **except as the designated negative control** (it is the best-supported
  causal null in the project: effect ≤ 3e-05)
- logit-lens P(harm) at the codeword
- any objective that previously failed sufficiency, without relabelling it a negative control

**TROPT reality:** installed and working (v0.1.1, own venv, MAC + GCG recipes, already run on ClearHarm), but
it has **no representation/direction loss** — a mechanistic MAC arm requires a new `Loss` subclass under
`TROPT/tropt/loss/`. That is a real implementation task, and the venv differs from `poc_stage2`, so
tokenization must be re-verified before any cross-stack comparison.

### P9.2 — Budget
Anchor: universal suffix, 44 train tasks, 200 steps, bs = 64 → **563,200 candidate forwards ≈ 1.60 GPU-h per
arm-seed on one L40S**. **Strategy: 16 arms × 1 seed as a screen (≈ 33 GPU-h, ~6 h wall at the 6-parallel
cap), then top-3 + naive baseline + signature control at 3 seeds (≈ 55 GPU-h total)** rather than 98.6 for the
full 3-seed matrix.

### P9.3 — Success criteria (pre-registered, decided before the run)
1. Held-out ASR improves over compute-matched vanilla GCG **and** over no-suffix DS, by more than the P1 drift
   envelope. 2. `refusal_rate` falls **without** `empty_rate` rising. 3. Survives ≥ 3 seeds. 4. Transfers to
locked test. 5. The mechanism metric moves in the intended direction. 6. A random-direction objective does not
match it. 7. Harmful content stays redacted.

**Pre-register the null.** Three independent lines predict failure. Writing the arm table, primary metric,
decision rule and controls **before** the run converts either outcome into a publishable result.

**Exit:** Gate 7 passes or fails **on data**. **Paper artifact:** `PHASE9_GCG_MAC_CORRECTED.md` + the arm table.

---

## P10 — Decode-safe re-test of the behavioral nulls ⭐ (new in v2, high priority)

**Why:** §0.5 + §0.9. Two independent defects point the same way — the concept-circuit "behavioral inertness"
result, which is currently the study's headline, may be wrong.

**Do:**
1. **Write `AllPositionMLPAblate(model, layer_idxs, mode='zero'|'project_out'|'scale', ...)`** — a forward hook
   on `layer.mlp` that edits the whole output on **every** forward, mirroring `make_project_out_hook`. Ship
   with synthetic tests proving it fires on a cached decode step.
2. **Re-run BEHAV-WRITE decode-safe** (the original was prefill-only) and BEHAV-CARRY on v3.
3. **Primary outcome = graded score**, one-sided, pre-registered from the pooled pilot (+0.074, p = 0.035).
4. Report **post-hoc power beside every null**, and the exact test's granularity floor.

**Exit:** a definitive, adequately powered statement — either the concept circuit *is* behaviorally inert (now
with power to say so), or it is **weakly but genuinely** behaviorally necessary, which is a different and more
nuanced paper. Either is publishable; the current underpowered null is not.
**Paper artifact:** the corrected dissociation figure + a power table.

---

## P11 — Framework robustness (B12)

**Gap:** one framework only; zero TransformerLens/nnsight in the repo. Mitigation that *does* exist: 19 test
files / 115 test functions including 8 synthetic hook tests.

**Design:** PyTorch hooks + eager · PyTorch hooks + SDPA (non-pattern hooks only) · TransformerLens ·
nnsight · a minimal custom forward wrapper. Each must reproduce **five positive controls** — self-swap = 0 ·
L9 MLP write reduces `p_concept` · refusal ablation raises ASR · refusal injection lowers ASR · random
direction does not mimic — **and one known negative** (query→demo edge knockout stays null).

**Rules:** identical prompts and token ids or no comparison; save activation deltas proving hooks fired; if
frameworks disagree, bisect with synthetic tests + one real example and **pause before any paper claim**.
**Paper artifact:** `PHASE10_FRAMEWORK_ROBUSTNESS.md` — a robustness appendix that materially strengthens
every hook-based claim.

---

## P12 — Quantized exploration (B11)

**Gap:** `ds_common.load_model` has no `quantization_config` path; zero quantization code anywhere; the
existing plans mostly *forbid* it for mechanistic comparisons.

**Design:** bf16 (primary) vs 8-bit vs 4-bit (vs AWQ/GPTQ if available). Run the corrected baseline, the two
readouts, L9 write necessity, carry-head necessity/sufficiency, refusal-down and refusal-up, and the combined
arm. **Gate every claim on reproducing the same five positive controls**, and verify hidden activations are
numerically comparable before interpreting any difference.

**Interesting hypothesis:** if quantization noise degrades the refusal representation more than the concept
representation, quantized deployment is *differentially* more jailbreakable — a deployment-relevant safety
finding.
**Status:** exploratory appendix. **Paper artifact:** `PHASE11_QUANTIZED_EXPLORATION.md`.

---

## P13 — Cross-model replication (only after the main story is stable)

Llama-3.1-8B (primary) · Llama-3.3-70B if resources allow · Qwen3-14B (relevant to the prior CoT/GCG work) ·
one small model for debugging. Minimal set: corrected baseline · refusal projection separation · refusal-down
sufficiency · refusal-up necessity · concept/refusal separation · the best P9 objective · the all-occurrence
check.
**Exit:** state plainly whether the result is Llama-specific or cross-architecture.

---

## P14 — Paper assembly and claim audit

**Figures:** concept circuit map · corrected behavioral dissociation (with power) · concept/refusal causal
plane · DS × refusal-down α grid · Gate-7 arm table · Jacobian readout vs causal effect · all-occurrence
heatmap · framework robustness · quantization appendix · **claim support matrix**.

**`reports/CLAIM_AUDIT_TABLE.md`** — one row per claim: claim · source script · **exact run dir** · raw file ·
recomputation command · status ∈ {verified, mismatch, partial, unverified}. **No claim enters the abstract
unless marked verified.** Explicitly separate: established causal claims · exploratory findings · negative
results · hypotheses · not-run items.

**Also publish the corrections** from the previous sprint's audit (43 mismatches) and from §0 — a paper that
documents its own corrections is stronger, not weaker.

---

# §6 Pre-registration

Before any locked-test data is touched, commit `reports/PREREGISTRATION.md` containing:

1. **Primary Holm family of exactly 5 arms** — at n = 42 a 21-arm family has MDE = 0.479, *larger than the
   refusal-ablation effect itself*. Proposed primary five:
   (1) carry-head ablation vs baseline (graded, one-sided);
   (2) write ablation vs baseline (graded, decode-safe);
   (3) calibrated refusal re-injection at L22;
   (4) the concept × refusal **interaction** contrast;
   (5) the concept effect within the pre-defined refusal-resistant subgroup.
   Everything else is **exploratory**, reported with CIs and explicitly labelled non-confirmatory.
2. Primary outcome = **graded StrongREJECT score**; binary McNemar as pre-registered secondary.
3. The **direction** of each hypothesis — including the **sub-additivity** prediction for the interaction
   (§0.6), not a positive-synergy prediction.
4. The α chosen in P8.1 and the rule that chose it.
5. The subgroup definition rule and the calibration split it is derived from.
6. Power for each primary arm at the achieved n.
7. The Gate-7 decision rule and its negative controls.
8. **Commit the power scripts** (`power_mcnemar.py`, `power_interaction.py`, `power_design.py`) into the repo
   so the power claims are reproducible artifacts.

---

# §7 Run order and budget

| # | Phase | Blocking? | GPU | Why here |
|---|---|---|---|---|
| 1 | **P0** artifact + validators + judge module | **BLOCKS ALL** | none | §0.1–0.3; without it nothing is provable |
| 2 | **P8.0** interaction from existing data | no | **none** | a publishable result for free, and it sets P8's hypothesis |
| 3 | **P1b** ClearHarm v3 | blocks P8/P10 | none | §0.4 leakage + §0.5 power |
| 4 | **P1** corrected baseline + drift envelope | blocks P8/P9 | small | every effect is measured against it |
| 5 | **P10** decode-safe re-test of the nulls | high | medium | the headline may be wrong — settle it early |
| 6 | **P8.1** α calibration → **P8** factorial | — | large | the centrepiece |
| 7 | **P9.0** GCG bug fixes → **P9** Gate 7 | — | ~55 GPU-h | the biggest missing claim |
| 8 | **P2** all occurrences | parallel | medium | cheap, one free cell already implemented |
| 9 | **P3–P5** attention / induction / path matrix | parallel if GPUs allow | large | mechanism depth |
| 10 | **P6** Jacobian · **P7** directions | — | medium | methods contribution; P7 unblocks per-layer refusal claims |
| 11 | **P11** frameworks · **P12** quantization | last | small | appendices |
| 12 | **P13** cross-model · **P14** paper | last | large | only after the story is stable |

**Standing constraint:** ≤ 6 parallel SLURM jobs, no dependencies, L40S only.

---

# §8 Risk register

| risk | severity | mitigation |
|---|---|---|
| 9 GB of evidence lost (gitignored, single copy, 98%-full volume) | **critical** | P0 §2.2 items 1–2, 9 — archive off-NetApp **this week** |
| Headline "behavioral inertness" is an artifact of power + a prefill-only ablation | **critical** | P10, pre-registered, graded outcome |
| Gate-7 conclusion rests on an optimizer that never used the objective | **critical** | P9.0 item 1 before any GCG run |
| Concept-level leakage invalidates generalization claims | high | P1b real clustering + published v1 leakage table |
| Per-layer refusal directions unvalidated (L12 failed) | high | P7 rebuild + generation-validate all 32 |
| Ceiling makes the interaction undetectable | high | P8.1 sub-saturating α |
| Under-powered arms mistaken for nulls | high | report power beside every null; n = 350+ if the interaction is primary |
| `AttentionKnockout` silently no-ops under SDPA | medium | assert eager in P0 tests |
| Judge duplicated in 5 files desynchronizes | medium | P0 judge module |
| TROPT venv ≠ poc_stage2 → tokenization mismatch | medium | verify token ids before any cross-stack claim |
| Harmful text leaking into git or a figure | medium | contract §2.1: `gens.jsonl` archived, never committed |

---

# §9 Concrete first tasks

1. **§2.2 items 1–3** — un-ignore `summary.json`/`RUNMETA.json`/`DONE.json`, commit `logs/`, implement
   `ds_common.write_runmeta()` and wire it into all 21 phase scripts.
2. `scripts/audit_artifacts.py` + `scripts/backfill_runmeta.py` + `scripts/update_registry.py`.
3. `scripts/behav_judge.py` — the single judge module (currently duplicated in ≥ 5 files).
4. **P8.0** — compute the interaction from the existing `behav_refusal_*` raw data. **No GPU. Do it first.**
5. `configs/manifests/phase1_corrected_baseline.json`
6. `configs/manifests/phase2_all_codeword_occurrences.json`
7. `configs/manifests/phase8_combined_causal_asr.json`
8. `configs/manifests/phase9_gcg_mac_corrected.json`
9. `scripts/validate_dataset_v3.py` and `scripts/validate_all_outputs.py`; extend
   `validate_experiment_coverage.py` to the behavioral/GCG/quantized schemas.
10. New primitives: `AllPositionMLPAblate` (decode-safe), `DualDirectionIntervention`,
    `resolve_all_occurrences`, each with synthetic tests **proving they fire on a cached decode step**.
11. `scripts/phase2_all_occurrence_patch.py`, `scripts/phase_alpha_grid.py`,
    `scripts/phase8_combined_causal_asr.py`, `scripts/phase9_gcg_mac_corrected.py`.
12. **Launch the free cell that already exists**: `phase6_mlp_causal.py --positions all` (implemented, never run).
13. SLURM wrappers for each — comma-lists in wrapper defaults, never in `--export`.
14. Smoke test on 2 examples before every full launch.
15. Run **P1** (baseline + drift envelope) and **P10** (decode-safe re-test) first; then P8.1 → P8.
16. Analyse with paired tests; write the phase report; **never overwrite old results** — timestamped dirs only.

---

# §10 Expected high-value outcomes

1. If **DS + refusal-down is sub-additive** (the pilot says Î = −0.186, p = 0.043), Doublespeak's behavioral
   effect is **entirely refusal-axis mediated** — a clean, strong paper result.
2. If it is **synergistic** after the ceiling is removed by a sub-saturating α, then the context attack and
   refusal suppression are **separate channels** — an equally strong, opposite result. Either way P8 delivers.
3. If **concept-up adds nothing** once refusal is suppressed, the concept remap is **behaviorally
   epiphenomenal** — and P10 will have established this *with power*, which the current data does not.
4. If **P10 flips the null** (graded score, decode-safe), the paper becomes "the concept circuit contributes
   weakly but measurably" — a more nuanced and more defensible claim than the current one.
5. If **GCG/MAC succeeds only on refusal objectives**, the optimization lesson is sharp and actionable.
6. If **no objective improves held-out ASR** on a *fixed* optimizer, Gate 7 fails **for real this time** —
   publishable as a clean, well-controlled negative.
7. If **quantization differentially degrades refusal**, that is a deployment-relevant safety finding.
8. If **framework differences change conclusions**, **pause and debug before any paper claim.**

---

# §11 Suggested paper-worthy final story (if the data supports it)

> Doublespeak creates a real concept-remapping circuit, but jailbreak behavior is governed by a **separable
> refusal-suppression axis**. Controlled causal interventions show that suppressing refusal is **sufficient**
> to exceed Doublespeak ASR, restoring refusal is **necessary** to kill the jailbreak, and concept-remap
> interventions mostly affect **interpretation readouts rather than behavior**. Mechanism-derived optimization
> only becomes useful if it targets the **behavioral refusal axis**, not the observational Doublespeak
> signature.

**Do not commit to this story before P10.** It is the current best reading, but its behavioral half rests on
an underpowered null and a prefill-only ablation. The plan is built so that either outcome is publishable.

---

# §12 End state

A paper-ready package with:
- a preserved, provenance-complete, independently auditable experiment corpus (§2);
- a leak-free ClearHarm v3 benchmark sized for the tests it must support;
- a corrected, adequately powered statement about whether the concept circuit drives behavior;
- the DS × refusal-down factorial with a real interaction estimate and CI;
- a real Gate-7 result on a fixed optimizer, pass or fail;
- all-occurrence, induction-head, path-matrix and Jacobian analyses;
- clean concept/refusal separation with validated per-layer directions;
- framework-robustness and quantization appendices;
- and a claim-audit table in which every abstract sentence is traceable to a run directory.
