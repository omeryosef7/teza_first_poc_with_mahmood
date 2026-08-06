# GPU-Coverage Audit — P8, P9, P10, P11, P12, P13, P14

**Question (Omer):** is any plan phase that REQUIRES a GPU (a model forward pass) reported as *done* without
an actual GPU run behind it — skipped, stubbed, or faked on the login node?

**Rule applied:** a result is legitimate only if it traces to a run dir whose `RUNMETA.json` shows execution
on a GPU compute node (hostname `n-8xx`/`n-3xx`/`n-5xx`/`t-806`, a real `gpu`/`cuda_available` field), NOT the
login node. `schema: "RUNMETA/1-reconstructed"` = backfilled from a dir name, **weaker provenance** — flagged
explicitly wherever it occurs.

**Audit date:** 2026-08-06. **Method:** read-only inventory of `outputs/`, `RUNMETA.json`, `DONE.json`,
committed `p8_*.json`, and the per-phase reports. No job launched, no file edited, no generation/harmful text
read. Plan reference: `reports/CAUSAL_CONTINUATION_MASTER_PLAN.md` §5.

---

## Verdict table

| Phase | Needs GPU? | Has real (non-reconstructed) GPU run? | Verdict |
|---|---|---|---|
| **P8** DS × refusal-down factorial (centrepiece) | **Yes** | **Yes — all cohorts, L40S, RUNMETA/1** | ✅ OK-ran-on-gpu |
| **P9** GCG / MAC Gate-7 | **Yes** | **No P9 run dir exists (0/16 arms)** | 🔴 GPU-PHASE-NOT-RUN (honest todo, not faked) |
| **P10** decode-safe write null | **Yes** | **Yes (write half) — 718938, L40S, RUNMETA/1** | ✅ OK-ran-on-gpu (carry half not re-run) |
| **P11** framework robustness | **Yes** | **Not started** | 🔴 GPU-PHASE-NOT-RUN (todo, not faked) |
| **P12** quantized exploration | **Yes** | **Not started** | 🔴 GPU-PHASE-NOT-RUN (todo, not faked) |
| **P13** cross-model replication | **Yes** | **Not started** | 🔴 GPU-PHASE-NOT-RUN (todo, not faked) |
| **P14** paper assembly / claim audit | **No (CPU)** | n/a — CPU analysis over committed artifacts | ✅ CPU-PHASE-ok |

**Bottom line: nothing is faked.** Every phase that ran on GPU has real L40S provenance; every phase without a
GPU run is openly marked NOT-STARTED / NO-GO in its own tracker, never reported as a completed GPU result.
The one weaker-provenance artifact in scope (`outputs/gcg/`) is *reconstructed* Qwen3 work from a prior sprint
and is **not** cited as a P9 result.

---

## P8 — CENTREPIECE — every cohort result traces to a real L40S GPU run ✅

The six committed `p8_*.json` (all git-tracked) each carry a `run_dir` + `slurm_job_id`. Each was traced to
its run dir's `RUNMETA.json`. **All are `schema: RUNMETA/1` (live, not reconstructed), `gpu: NVIDIA L40S`,
`cuda_available: true`, hostname = a compute node — none is the login node.** Each has a matching `DONE.json`
`status: ok` with row counts equal to the `n_rows_used` in the committed JSON.

| Committed artifact | cohort / alpha | run dir | job | node | GPU | RUNMETA schema | DONE | rows |
|---|---|---|---|---|---|---|---|---|
| `p8_generated_v3.json` | generated, α0.25 | `behav_refusal_generated_asweep0.25_20260806_035601_720725` | 720725 | n-801 | L40S | RUNMETA/1 | ok | 115 |
| `p8_clearharm_v3.json` | clearharm, α0.25 | `behav_refusal_clearharm_asweep0.25_20260806_051610_721956` | 721956 | n-801 | L40S | RUNMETA/1 | ok | 127 |
| `p8_alpha005_clearharm.json` | clearharm, α0.05 | `behav_refusal_clearharm_asweep0.05_20260806_150026_728310` | 728310 | n-802 | L40S | RUNMETA/1 | ok | 127 |
| `p8_alpha020_clearharm.json` | clearharm, α0.20 | `behav_refusal_clearharm_asweep0.2_20260806_150026_728311` | 728311 | n-802 | L40S | RUNMETA/1 | ok | 127 |
| `p8_lowalpha_clearharm.json` | clearharm, α-sweep 0–0.25 | `behav_refusal_clearharm_asweep0.0-0.05-0.1-0.15-0.2-0.25_20260806_111104_725172` | 725172 | n-802 | L40S | RUNMETA/1 | (present) | 50 |
| `p8_v3_combined.json` | clearharm+generated pooled | scratchpad concat of **720725 + 721956** | — | (derived) | (derived) | — | — | 242 |

Notes on the two edge cases, both benign:

- **`p8_v3_combined.json`** lists `run_dir` = a scratchpad `/tmp/.../comb` path with `slurm_job_id: null`. This
  is **not** a login-node run — it is an offline concatenation of the raw.jsonl of the two real GPU runs
  (720725 + 721956); n_rows = 115 + 127 = 242 exactly. Its numbers inherit the two L40S runs' provenance.
  The pooled `run_dir` string is a merge scratch path, not a compute claim.
- **Empty-dir check (the specific thing asked):** the clearharm α0.25 job has an **aborted precursor dir**
  `behav_refusal_clearharm_asweep0.25_20260806_035033_720724` that contains **only `RUNMETA.json`** (no
  `DONE`, no `summary`, no `raw`). It is **not cited by any `p8_*.json`** — the analyzer used the completed
  re-run 721956 instead. So **no committed P8 result was produced by an analyzer reading an empty dir.** (Even
  the empty precursor's RUNMETA shows n-803 / L40S; it was a real allocation that produced no rows, correctly
  superseded.)

Cross-checks: the P8 report `reports/P8_INTERACTION_V3.md` cites only 720725 / 721956 / the three `p8_*.json`
and references **no** `*_login_*`, `*_validate*`, `/tmp`, or scratchpad dir. Model in every RUNMETA =
`meta-llama/Llama-3.1-8B-Instruct`, refusal vector = `stage_gcg_full/refusal_direction_llama_L18.pt`, seed 0,
torch 2.7.1+cu126 / transformers 5.12.1. `git_dirty: true` on every run (working-tree-dirty, expected for this
repo), but `git_commit` is recorded on each.

**P8 verdict: ✅ every cohort × alpha result is backed by a real GPU run. No stub, no login-node fake, no
empty-dir read.**

---

## P9 — GCG / MAC Gate-7 — NOT RUN (0/16 arms), and honestly labelled so 🔴

- **No P9 run directory exists.** `configs/manifests/phase9_gcg_mac_matrix.json` is `status:
  "FROZEN-SPEC / NOT LAUNCHED"`. `reports/readiness/P9_READINESS.md` states plainly: **"7 of 16 arms have all
  their scientific inputs on disk — but 0 of 16 are launchable as-is"** and **"No P9 run directory exists."**
- The only GCG output on disk is **`outputs/gcg/`** — and it is **not** a P9 arm:
  - `RUNMETA.json` is **`schema: RUNMETA/1-reconstructed`** (`reconstructed: true`, backfilled 2026-08-05 by
    `scripts/backfill_runmeta.py`). **Weaker provenance** — `gpu`, `slurm_job_id`, `git_commit`, `seed`, node
    are all listed `unknown`/"ambiguous: 8 logs write this dir, no single producer could be established."
  - Model = **`Qwen/Qwen3-14B`**, not Llama. `DONE.json` is `DONE/1-reconstructed`, 39 rows, from
    **2026-07-29** — i.e. prior-sprint Track-B Qwen3 work, predating the continuation plan.
  - The plan's own §0.8 flags this stack's optimizer as buggy and states **"zero Llama GCG runs exist today."**
- P9 genuinely **requires GPU** (GCG candidate forward passes) and has **none**. This is a real todo, not a
  faked completion: no report claims P9 as done; the tracker marks every arm GO-blocked / NO-GO.

**P9 verdict: 🔴 GPU-PHASE-NOT-RUN. The pre-existing `outputs/gcg/` is reconstructed-provenance Qwen3 and must
not be cited as P9 evidence.**

---

## P10 — decode-safe write null — write half ran on GPU ✅; carry half not re-run

- **Authoritative run:** `outputs/behav_write_clearharm_L8_9_10_11_ds_20260805_232238_718938` —
  `RUNMETA/1` (live), **n-802 / NVIDIA L40S**, `cuda_available: true`, `DONE/1 status: ok`, **86 rows**, arms
  `[baseline, write_abl_prefill, rand_pos_abl_prefill, write_abl_decodesafe, rand_pos_abl_decodesafe]` — the
  decode-safe arms are present. `reports/P10_DECODE_SAFE_WRITE.md` cites job **718938**. Genuine GPU run.
- A precursor `..._ds_..._717879` (n-805 / L40S, `DONE ok` but only **4 rows**) is a preempted/aborted smoke;
  it is superseded by 718938 and not the cited result.
- **Gap (not a fake, a scope note):** the plan's P10 also asks for **BEHAV-CARRY re-run decode-safe on v3**.
  The `behav_carry_*` dirs on disk are all **2026-08-04** (jobs 707820/707831/707832) — the pre-decode-safe /
  pre-v3 era. So the decode-safe *carry* re-test is **not yet run**. The decode-safe *write* re-test (the P10
  headline) is done and GPU-backed.

**P10 verdict: ✅ OK-ran-on-gpu for the write null (718938, real L40S). Carry decode-safe re-run on v3 is
still todo-GPU.**

---

## P11 — framework robustness (TransformerLens / nnsight) — NOT STARTED 🔴

- No run dir: `outputs/` has no `*tlens*`, `*transformerlens*`, `*nnsight*`, or `*framework*` directory.
- No report: `reports/PHASE10_FRAMEWORK_ROBUSTNESS.md` (its planned name) does not exist.
- Needs GPU (five positive controls require forward passes). **Confirmed not started — todo-GPU, not faked.**

## P12 — quantized exploration (8-bit / 4-bit) — NOT STARTED 🔴

- No run dir: no `*quant*`, `*8bit*`, `*4bit*`, `*int8*` directory in `outputs/`.
- No `quantization_config` code path exists (plan §P12). No report.
- Needs GPU. **Confirmed not started — todo-GPU, not faked.**

## P13 — cross-model replication — NOT STARTED 🔴

- No new continuation-era cross-model run dir (`*70B*`, `*cross_model*`, or new Qwen continuation runs).
- No report. Plan explicitly sequences P13 "only after the main story is stable."
- Needs GPU. **Confirmed not started — todo-GPU, not faked.**

---

## P14 — paper assembly / claim audit — CPU, correctly ✅

- `reports/CLAIM_AUDIT_TABLE.md` (110 KB, regenerated 2026-08-06 22:12) is produced by
  `scripts/build_claim_audit.py`, which **recomputes from committed artifacts on disk** — no model forward
  pass. 90 claims catalogued (67 VERIFIED / 8 WITHDRAWN / 4 SUPERSEDED / 6 UNDERPOWERED / 3 UNVERIFIED /
  2 PENDING).
- P14 does **not** require a GPU. Running as CPU analysis is correct, not a shortcut.

**P14 verdict: ✅ CPU-PHASE-ok. No GPU obligation to fake.**

---

## Provenance-strength summary

- **Real live `RUNMETA/1` (strong):** all P8 cohort runs (720725, 721956, 728310, 728311, 725172), P10 write
  (718938). All L40S compute nodes; none on the login node.
- **Reconstructed `RUNMETA/1-reconstructed` (weak):** `outputs/gcg/` only — Qwen3, prior sprint, **not a P9
  result** and not cited as one.
- **No run dir (todo-GPU):** P9 (0/16), P11, P12, P13.
- **CPU by design:** P14.

**Direct answer to Omer's question: No GPU-required phase is reported as done without a real GPU run.** P8 —
the centrepiece — is fully GPU-backed on real L40S nodes with live (non-reconstructed) RUNMETA, and none of its
committed `p8_*.json` were produced from an empty or login-node dir (the one empty precursor dir 720724 was
correctly discarded). P9/P11/P12/P13 are genuinely not started and are labelled as such everywhere; they are
todo-GPU, not fakes. P14 is legitimately CPU-only.
