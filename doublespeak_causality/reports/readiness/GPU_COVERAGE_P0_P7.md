# GPU Coverage Audit — P0…P7

**Question (Omer's):** is any plan phase that *requires a GPU* (a real model forward pass) reported as
done **without** an actual GPU run behind it — skipped, stubbed, or faked on the login node?

**Method:** for each phase I read its §5 header in `reports/CAUSAL_CONTINUATION_MASTER_PLAN.md`
(the header states GPU/CPU), mapped it to its run dir(s) via `CONTINUATION_PROGRESS.md` and the
`reports/` files, and inspected `RUNMETA.json` (schema, hostname, gpu, job id) plus the committed run log
(`logs/*.out`, which carries `git=<sha>` and a `GPU ok: <name>` line) to confirm the run executed on a
GPU compute node — not the login node.

**Provenance tiers used below**
- **Tier A (gold):** committed `RUNMETA.json` with schema `RUNMETA/1` (written live by the run) naming a
  GPU node + GPU model.
- **Tier B (reconstructed):** `RUNMETA.json` with schema `RUNMETA/1-reconstructed` — backfilled from the
  dir name / log, *not* written by the run. Names a GPU node but is weaker evidence.
- **Tier C (log-only):** no `RUNMETA.json` in the dir, but the run's committed/on-disk `logs/*.out` shows
  `GPU ok: NVIDIA L40S/A5000/3090` and a `git=` line — the GPU run demonstrably happened, but the run dir
  itself carries no provenance file.

---

## Headline answer

**No GPU phase is faked on CPU, and no GPU phase is reported done without a real GPU run behind it.**

- Every phase **claimed complete** that needs a GPU (**P2, P3, P4a, P4b-demo, P7**) has a run log showing
  execution on a GPU node (L40S / A5000 / 3090). Verified per dir below.
- The three GPU phases with **no** GPU run (**P1, P5, P6**) are **not claimed done** — they are honestly
  `todo` (P1 not started; P5 blocked on an Omer scope decision) or `built-but-not-run` (P6 Jacobian harness
  exists + passes a CPU closed-form correctness proof, but the real-model GPU pass has never been launched).
  This is "not-yet-run", **not** "reported-done-but-faked".

**Two provenance weaknesses worth flagging (not fakery, but they weaken the paper trail):**
1. **P2 / P3 / P4a run dirs carry no `RUNMETA.json` at all** — their only GPU proof is the run log, and for
   P3/P4a that log is **not even git-committed** (P2's log *is* committed). A fresh clone could not prove
   those phases ran on a GPU. The committed `summary.json`/result JSON carries only `model`+`n_rows`
   (per §0.2), no host/gpu field.
2. **P4b-demo's `RUNMETA.json` is Tier B (`RUNMETA/1-reconstructed`)** — backfilled, not written by the run.
   It names L40S/n-802, but it is weaker than P7's live record.

**P7 is the only phase with gold (Tier A) committed provenance** (`RUNMETA/1`, n-801, L40S, + `DONE.json`).

---

## Per-phase table

| Phase | Header says | Needs GPU? | Status in tracker | GPU run behind it? | Provenance | Verdict |
|---|---|---|---|---|---|---|
| **P0** — trust the repo | (no GPU) | No | done (ticks 1–5) | n/a — CPU provenance/repo work | CPU | **CPU-PHASE-ok** |
| **P1** — corrected baseline + drift | (GPU, small) | **Yes** | `☐` not started | **No run** — no `phase1/baseline/drift` log, no run dir | none | **GPU-PHASE-NOT-RUN** (= todo, not claimed done) |
| **P1b** — ClearHarm v3 dataset | (CPU + small API) | No | done (n=324, $0.14) | n/a — CPU + OpenAI API only | CPU/API | **CPU-PHASE-ok** |
| **P2** — all codeword occurrences | (GPU) | **Yes** | done (ticks 5, 29) | **Yes** — `phase6_KO_clearharm_mlp_out_all_layer_…_718027` (+ `714997/8/9`) | **Tier C**: log `ds_mlpko_718027.out` = `GPU ok: NVIDIA L40S`, committed; **no RUNMETA in dir** | **OK-ran-on-gpu** |
| **P3** — attention causality (edgeKO) | (GPU) | **Yes** | done (tick 62) | **Yes** — `phase4_edgeKO_clearharm_…_728189` (+ 726211/726616/727983 decision-token cell) | **Tier C**: log `ds_edgeko_728189.out` = `GPU ok: NVIDIA L40S`; **no RUNMETA; log not committed** | **OK-ran-on-gpu** |
| **P4a** — induction-head ID (attn_retrieval) | (GPU) | **Yes** | done (tick 70) | **Yes** — `attn_retrieval_Llama-3.1-8B-Instruct_…_728475/728476` | **Tier C**: logs `ds_p4aid_728475/6.out` = `GPU ok: NVIDIA L40S`; **no RUNMETA; log not committed** | **OK-ran-on-gpu** |
| **P4b** — head-z necessity (phase5_headz demo) | (GPU) | **Yes** | demo done (tick 75); query confirmatory still running | **Yes** — demo `phase5_headz_clearharm_demo_…_728619/728710/728711`; query `…_729249/50` (3090), `…_729356/57` (A5000) *incomplete* | **Tier B** demo: `RUNMETA/1-reconstructed`, n-802, L40S; query logs show A5000/3090 | **OK-ran-on-gpu** |
| **P5** — head→MLP path matrix | (GPU) | **Yes** | not started — **blocked on Omer scope decision** (tick 53) | **No run** — no `path/p5` log, no continuation run dir (`path_patch_…_697419` is the old pre-continuation circuit sprint) | none | **GPU-PHASE-NOT-RUN** (= todo, awaiting `k` decision) |
| **P6** — Jacobian / projection readout | (GPU) | **Yes** | "built" (tick 13) — **not** in the phase status table | **No run** — `scripts/phase6_jacobian_readout.py` + `slurm/run_jacobian.sh` (job-name `ds_jacobian`) exist; **no `ds_jacobian` log, no readout/jacobian output dir**. Only a CPU closed-form correctness proof on a toy model was done | none (CPU synthetic test only) | **GPU-PHASE-NOT-RUN** (harness built + CPU-verified; real-model GPU pass never launched) |
| **P7** — refusal-direction validation (refval) | (GPU) | **Yes** | done, all 32 layers (ticks 42, 46) | **Yes** — headline `refval_clearharm_…_720463` (+ 718937, 721957, 722611, 724931) | **Tier A (gold)**: `RUNMETA/1` (live), host **n-801**, gpu **NVIDIA L40S**, job 720463, git `d9e0a2c`, + `DONE.json` (wall 2875 s), committed | **OK-ran-on-gpu** |

---

## Notes / evidence detail

**P0** — the provenance-repair phase itself (un-ignore outputs, `write_runmeta`, backfill, registry,
validators, judge module, synthetic tests). Pure CPU. Done and self-audited. No GPU expected or needed.

**P1** — never launched. No `logs/*phase1*|*baseline*|*drift*`, no run dir. Tracker: `☐ needs GPU`.
The "P1 audit done" (tick 7) refers to `audit_phase21_baseline.py` re-checking the *existing* Phase-2.1
baseline numbers, **not** running the new P1 baseline/drift-envelope experiment. Correctly `todo`.

**P2** — `--positions all` (the free cell). GPU run confirmed on L40S (job 718027). The dir has no
`RUNMETA.json`, but its run log **is** git-committed and shows the GPU + git sha. Result (all-occurrence L9
write ≈ 2× demo-only) is backed by a real GPU run.

**P3** — decision-token destination cell + the eager-attention assertion the plan demanded. GPU-run on
L40S (job 728189 and the 726xxx/727xxx relaunches). Weakest committed trail of the completed phases: no
`RUNMETA.json` in the dir **and** the `ds_edgeko_*.out` log is not tracked by git — GPU proof is on disk
only. Recommend committing the log or writing a live RUNMETA before this number goes in the paper.

**P4a** — token-identity retrieval (2.0× on ClearHarm, tick 70). GPU-run on L40S (728475/728476). Same
gap as P3: result JSON committed, no `RUNMETA.json`, log uncommitted.

**P4b (P4b-1)** — demo z-channel result (distributed necessity; robust pair L13H18/L14H13) is done and
GPU-backed on L40S with a Tier-B reconstructed RUNMETA (n-802). The **query** position-set is the
confirmatory second cell and was **still running** on A5000/3090 at audit time (`…_729250/729357` have only
`raw.jsonl`, no `summary.json`/`DONE.json`) — that is in-progress, not a gap. The headline P4b claim rests
on the completed demo cell.

**P5** — genuinely **not started**. The plan and tick 53 flag it as needing an explicit Omer decision
(AtP-rank everything vs exact-patch top-k; "I need your k"). The only `path_patch`/`head_attr` dirs on disk
are from **2026-07-31** (the earlier CAUSAL_CIRCUIT sprint), not this continuation. No fakery — awaiting a
scope call.

**P6** — the Jacobian readout is **built and CPU-verified only**. `scripts/phase6_jacobian_readout.py`
(`fits_nothing: true`, correctness proven against a closed-form derivative on a **toy** model to atol 1e-9)
and `slurm/run_jacobian.sh` exist, but **no `ds_jacobian` job ever ran** — no log, no readout/jacobian
output dir. So the real-Llama per-layer concept/refusal Jacobian (the actual paper result) has **not** been
produced on GPU. The tracker's ✅ is for the *harness build + correctness proof*, and the phase status table
does not list P6 as complete — so this is honestly "built, GPU run pending", not "reported done". Flagging
it because P6 is the one place where a ✅ could be misread as a finished GPU result.

**P7** — the strongest case. Live `RUNMETA/1` (not reconstructed), n-801, L40S, job 720463, git
`d9e0a2c`, plus a committed `DONE.json`. All refval dirs reconcile (tick 44: 1702 values recomputed, 0
mismatches). This is the provenance standard the other GPU phases should meet.

---

## Bottom line for Omer

The gap you were worried about — a GPU phase marked done but skipped/stubbed/faked on the login node —
**does not exist in P0–P7.** Every completed GPU phase ran on a real GPU node. The three GPU phases without
a GPU run (P1, P5, P6) are correctly un-claimed (todo / scope-blocked / built-not-run).

The real, lesser issue is **committed provenance quality**: only **P7** has a gold live `RUNMETA/1`;
**P4b-demo** is reconstructed; **P2/P3/P4a run dirs have no `RUNMETA.json` at all** and rely on the run log
(uncommitted for P3/P4a). Before these numbers go in the paper, either write a live RUNMETA on rerun or
commit the corresponding `logs/*.out`, so GPU execution is provable from a fresh clone.
