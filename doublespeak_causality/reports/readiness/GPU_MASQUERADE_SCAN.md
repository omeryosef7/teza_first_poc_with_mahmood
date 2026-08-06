# GPU MASQUERADE SCAN — is any GPU result faked on CPU?

**Date:** 2026-08-06. **Auditor:** code/provenance inventory only. No job launched, no existing file
modified, no `gens.jsonl` / prompt / generation / codeword text read. Only source code, numeric columns,
and RUNMETA/DONE provenance metadata were inspected. All paths relative to
`/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/doublespeak_causality/`.

---

## HEADLINE ANSWER

**NO.** There is **no faked-on-CPU GPU result** in the committed artifacts. Across all 395 run
directories with a RUNMETA.json:

- **Zero** artifacts record `"device": "cpu"` (or `mps`). Grep of every committed `*.json` (excluding
  gens): **0 hits**.
- **Zero** RUNMETA records `"cuda_available": false`. Every RUNMETA that carries the flag records
  `true` (381 occurrences).
- **Zero** committed RUNMETA carries a login-node hostname. The 26 live-schema RUNMETAs are all on
  **compute nodes** (`n-801` ×5, `n-802` ×6, `n-803` ×4, `n-805` ×11), all `cuda_available: true`.
- **251** model-forward result files embed `"device": "cuda:0"` (written by the run itself via
  `LoadedModel.device`), and none embed a CPU device.
- The SLURM wrappers **hard-guard** the GPU: `nvidia-smi --query-gpu=name ... case ... *L40S*) ok ;;
  *) echo "ERROR need L40S"; exit 1` (e.g. `slurm/run_beh_necessity.sh:44-45`,
  `run_behav_carry.sh:57-58`, `run_beh_sufficiency.sh:45-46`, and every other wrapper). A run
  submitted the normal way **aborts** on a non-GPU node before loading the model.

So the affirmative masquerade the task looked for (a GPU number produced on CPU and reported as real)
**did not happen** — every trace that a CPU run would leave (device=cpu, cuda=false, login hostname)
is absent, and the one legitimate launch path is guarded.

Two caveats below are about **weakness of provenance and a missing in-code guard**, not about any
detected fake.

---

## 1. Code-path gap: `load_model` has NO GPU assertion (task item 1)

`ds_common.load_model` (`ds_common.py:368-415`) loads with `device_map="auto"` and **never asserts a
GPU is present**. On a CPU-only node, `device_map="auto"` silently places the model on CPU and
`LoadedModel.device` becomes `"cpu"` — plausible-but-slow output, not a crash.

I grepped every model-forward caller (all `scripts/phase*.py`, the numbered legacy scripts
`01_`, `05`–`52`, `next5_*`, `next7_*`, `build_refusal_direction_llama.py`) for a GPU assertion:

> `grep -rn "require_gpu | assert torch.cuda | cuda.is_available()"` across `scripts/*.py`, the
> numbered scripts, `pair_common.py`, `ds_common.py` → **no script asserts a GPU**. The only
> `cuda.is_available()` uses are `ds_common.py:143` (provenance-record the flag) and `:338`
> (seed the CUDA RNG *if* present). Neither is a guard.

**Consequence.** A script run **directly** on the login node (`python 01_map_representations.py ...`,
bypassing the sbatch wrapper) would run on CPU and produce output, with **no in-code stop**. The only
two things that catch this are external to the model code:
1. the SLURM wrapper's `nvidia-smi`/`L40S` check (`exit 1`) — but only if launched via sbatch, and
2. provenance: `RUNMETA.cuda_available` and the in-file `LoadedModel.device` would both record the CPU
   fact.

Both are **detection**, not prevention. Recommendation (not applied — read-only task): add
`assert torch.cuda.is_available()` (or a `--allow-cpu` opt-in) at the top of `load_model`. As of this
scan the detectors show the gap was never exercised — nothing on disk records a CPU device.

---

## 2. Provenance strength of the committed model-forward results (task item 2)

RUNMETA schema split across 395 run dirs:

| schema | count | meaning |
|---|---|---|
| `RUNMETA/1` (live, written at run start) | **26** | strong: real hostname + cuda flag, all compute nodes |
| `RUNMETA/1-reconstructed` (backfilled from dir name) | **369** | **weaker**: `hostname` is `null`; host/GPU not written by the run |

The reconstructed records explicitly self-flag as weaker (`schema_note`: "NOT the live RUNMETA/1
contract … reconstructed after the fact") and carry `hostname: null` — you cannot read a compute-node
name off them. Per Omer's rule these are **weaker provenance**. Classifying the 369 by what GPU
evidence *does* survive:

| reconstructed dir class | count | GPU evidence |
|---|---|---|
| result file embeds `"device": "cuda:0"` (written by the run) | **239** | strong-in-file: the run recorded a CUDA device |
| GPU name recovered from a matched log | 2 | log shows an NVIDIA GPU |
| **unverifiable** — no host, no gpu-from-log, no in-file device | **130** | none positive, **and none negative** |

The **130 unverifiable** dirs are the genuine weak spot: we cannot *positively* confirm they ran on a
GPU. But there is equally **no CPU evidence** for any of them (no `device:cpu`, no `cuda:false`). They
are "provenance-thin," not "faked." Many are superseded duplicates (e.g. several
`beh_necessity_*`/`beh_sufficiency_*` timestamps for the same phase) or intermediates.

### 2b. 28 run dirs are RUNMETA/DONE-only (empty — no result data)

These hold only `RUNMETA.json` (+ sometimes `DONE.json`), no result file — so they **cannot be the
source of any reported number**; a report citing that phase must resolve to a different, non-empty dir.
Examples: `emergence_Qwen3-14B_20260727_061950`, `toctou_Llama-3.1-8B-Instruct_20260731_175413_697393`,
several `beh_necessity_*` / `beh_sufficiency_*`, and the recent live-schema in-flight ClearHarm sprint
dirs (`behav_refusal_*_20260806_*`, `refval_clearharm_20260806_102007_*` — RUNMETA-only, no DONE =
started/crashed jobs, not claimed results). None of these constitutes a claimed-but-unbacked GPU
number; they are empty, not fabricated.

### 2c. The reconstructed `gpu` field never shows CPU

Recovered `gpu` values across reconstructed RUNMETA: `NVIDIA GeForce GTX TITAN X` (×51), plus
"no log matched", "not printed", and "ambiguous: N logs write this dir" markers — the honest
backfill outputs when a single producer could not be established. **No value is a CPU.** (The
TITAN-class name is consistent with this cluster's GPU dev nodes; the current audit node `c-004`
reports `NVIDIA TITAN Xp`.)

---

## 3. Reports marking a phase "done" via a CPU-only analyzer (task item 3)

The recent readiness reports (`reports/readiness/P3_READINESS.md`, `P4_READINESS.md`,
`P5_READINESS.md`, `P9_READINESS.md`, `P9_UNBLOCK_PLAN.md`) are **explicit "no job launched" inventories
for phases that are NOT yet run** ("0 of 16 arms launchable", "~85% built", "NOT launchable"). They do
**not** claim a GPU result is done — so there is nothing to fake there.

`SELF_REVIEW_2026-08-06.md` audits the **CPU analysis/reconciler scripts**
(`analyze_rep_predicts_behavior.py`, `validate_all_outputs.py`, `build_claim_audit.py`) — these are
legitimately CPU-only: they read `summary.json`/`raw.jsonl` that GPU runs produced. Its findings are
about statistical rigor (selection over 32 layers, "cross-validated" ambiguity, a near-vacuous
disjointness check), **not** about a missing GPU run. Relevant to the present question: it confirms
these analyzers consume committed GPU-run outputs, it does not allege any of those outputs were
CPU-produced.

The P9.0 optimizer unit tests being run "CPU only, 57s" (`P9_READINESS.md`) is correct and not a
masquerade — they are logic tests (`test_repr_in_selection.py`), not a claimed model-forward result.

---

## 4. Sanity: could a GPU job have secretly run on the login node? (task item 4)

The sanity command was run, but **on this audit's node it does NOT hold**:

```
$ hostname                         -> c-004
$ python -c "import torch; print(torch.cuda.is_available())"  -> True
$ nvidia-smi --query-gpu=name ...  -> NVIDIA TITAN Xp
```

**This subagent was scheduled on a GPU-equipped node (`c-004`), not the login node.** I therefore
**could not personally confirm the premise** "the login node has no GPU/torch" from here — the check
returns `True` because `c-004` genuinely has a GPU. This is a transparency caveat, not a hole in the
conclusion: the conclusion rests on the **committed provenance** (all live RUNMETA on `n-80x` compute
nodes; zero login hostnames; zero CPU device markers; the SLURM `nvidia-smi`/L40S guard), none of which
depends on which node this audit ran on. No committed RUNMETA hostname is `c-004` or any login-style
name.

---

## Bottom line

- **Faked-on-CPU GPU result in committed artifacts: NONE FOUND.** No `device:cpu`, no
  `cuda_available:false`, no login-node hostname anywhere; SLURM launch path is GPU-guarded; 251
  result files carry an in-file `cuda:0` device marker.
- **Real weaknesses (provenance, not fakery):**
  1. `load_model` (`ds_common.py:368`) has **no in-code GPU assertion** — a direct login-node run
     *could* silently use CPU; only the SLURM wrapper and after-the-fact provenance would catch it.
     No evidence it was ever exercised.
  2. **369/395 RUNMETA are `RUNMETA/1-reconstructed`** (hostname null) = weaker provenance by Omer's
     rule; of these **130 have no positive GPU evidence at all** (but also no CPU evidence).
  3. **28 run dirs are empty** (RUNMETA/DONE only) and cannot back any number.
- **Confidence: HIGH** that nothing was faked on CPU; **MEDIUM** that every reported number is
  positively GPU-traceable (130 dirs are provenance-thin, and the reconstructed schema is weaker than
  a run-time RUNMETA).
