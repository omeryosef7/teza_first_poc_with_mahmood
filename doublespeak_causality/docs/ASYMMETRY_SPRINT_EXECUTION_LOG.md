# ASYMMETRY SPRINT — EXECUTION LOG

*Append-only. Started 2026-08-11. Plan: `docs/ASYMMETRY_SPRINT_PLAN_2026_08_11.md`.*
*Authoritative prior state: `docs/RESEARCH_HANDOFF.md` §5/§6.*

Conventions: every entry has a UTC-ish date stamp, the phase, what was done, the artifact
path, and a verdict. Nothing is deleted; corrections are appended as new entries.

---

## 2026-08-11 — PHASE 0 START

### E0.1 Environment / baseline state
- Branch `behavioral-causality-sprint`, clean tree at `f0ef1ccc`.
- SLURM: 0 jobs owned by user. `killable` partition has idle L40S-class nodes
  (`n-[203-205,305,501-502]` idle, 13 mix). Budget rule: **≤6 concurrent GPU jobs**.
- Conda envs: `base`, `poc_stage2`. `poc_stage2` is the torch/transformers env.
- Offline HF cache at `$ROOT/.cache/huggingface`.

### E0.2 Data inventory (verified directly)
`data/gcg/clearharm_llama_v3/clearharm_llama_doublespeak.jsonl`: **n=148**, splits
`train=74 / dev=37 / test=37`. Fields include `task_id` (unique id), `split`,
`intent_cluster` (cluster field), `instruction`, `safe_target_prefix`, `codeword`,
`neutral_control_suffix`, `harm_category`.
`..._trainpool40.jsonl`: **n=40**, all `split=train` (the frozen optimization pool).

**Note for train/test discipline:** there is an untouched **`dev` split (n=37)**. It is
cluster-disjoint from test by construction of v3. This sprint uses `dev` for any
hyperparameter / threshold / layer selection that the 40-item train pool cannot support,
so that **test (n=37) is never used for selection**.

`data/pair_benchmark/`: all five pairs present — `pair_carrot_{bomb,grenade,pistol,chlorine,cocaine}.json`.

---

## GATE A — REPRODUCTION INTEGRITY / CODE AUDIT

### E0.3 Position-convention audit of the refusal direction across the three code paths

The plan (§19.3) requires asserting the refusal *vector* is the same object across code
paths. Auditing the code paths surfaced a more serious issue: the vector is (probably) the
same, but the **position at which it is read differs across all three paths**, and one of
those positions is computed incorrectly.

The three code paths and the residual-stream position each uses:

| Path | File | Position read | Layer index |
|---|---|---|---|
| **(i) Direction fit** | `build_refusal_direction_llama.py:83` `hs[L+1][0,-1,:]` | **last token of the templated prompt** (i.e. after `<\|start_header_id\|>assistant<\|end_header_id\|>\n\n`) — the decision position | `hs[L+1]` |
| **(ii) Activation ablation (the causal result)** | `pair_common.py:637` `make_project_out_hook` | **EVERY position, EVERY decode step**, and (multilayer variant) every layer | block output = `hs[L+1]` |
| **(iii) GCG token objective** | `gcg_optimizer.py:687` `refusal_dir_positions = [init_spans_rd.suffix_slice.stop - 1]` | **one fixed absolute token index**, derived from `train_tasks[0]` only | `hs[layer_idx]` passed as `k+1` (off-by-one handled) |
| **(iv) Mech-validity readout (Q5)** | `scripts/phase_gate7_mech_validity.py:89` `hs[row][0,-1,:]` | last token of the templated prompt — matches (i) | `hs[k+1]` |

**DEFECT D1 — cross-task absolute-position misalignment in the GCG objective. CONFIRMED.**
`refusal_dir_positions` is computed ONCE from `train_tasks[0]` (`gcg_optimizer.py:680-687`)
and then passed unchanged as an **absolute token index** into `_token_gradients`
(`gcg_optimizer.py:812`) and into candidate selection (`:433,:440`) for *every* task.
Prompt lengths differ across the 40-item train pool, so the index is only correct for task 0.
`_token_gradients` silently drops out-of-range positions
(`gcg_optimizer.py:172` `if pos < lt.shape[1]`), and `refusal_direction_loss` returns
`0.0` when no position survives (`objectives.py:224`) — i.e. the mechanism term silently
contributes nothing for those tasks.

Measured on the actual frozen train pool (Llama-3.1-8B tokenizer, `suffix_placement=user`,
suffix_len=16, init `' !'×16`):

```
suffix_slice.stop across the 40 train prompts: min 161, max 276, mean 241.6, std 17.5
fixed position used for ALL tasks (from task 0): P = 233

P inside the task's own suffix span :  17 / 40
P before the suffix (in instruction):  12 / 40
P after the suffix (header/target)  :  10 / 40
P out of range -> term silently 0    :   1 / 40
|P - task's own last-suffix-token|  : mean 14.0, median 9.5, max 73
EXACT matches (P == own last suffix token) : 1 / 40   (task 0 itself)
```

So the refusal/concept representation objective was evaluated at the intended position for
**1 of 40** training prompts.

**DEFECT D2 — fit-position vs use-position mismatch. CONFIRMED.**
Even for task 0, the intended position (`suffix_slice.stop - 1`, the last *suffix* token,
which lives inside the **user** turn) is not the position the direction was fitted and
causally validated at (the last token of the templated prompt, after the assistant header).
Verified token layout for train-pool item 0:

```
suffix_slice = [218, 234)   target_slice = [239, 260)
tokens between suffix end and target: ['<|eot_id|>', '<|start_header_id|>', 'assistant',
                                       '<|end_header_id|>', '\n\n']
```

The decision position is index **238**; the GCG objective reads index **233** — five tokens
earlier, still inside the user turn.

**DEFECT D3 — intervention-scope asymmetry (not a bug, but must be stated).**
The activation-space causal result ablates the direction at **all positions, all decode
steps, and (multilayer) all layers**. The token-space objective touches **one position at
one layer**. Any comparison of "activation-space causality" vs "token-space optimizability"
is therefore also a comparison of intervention *scope*, not only of intervention *medium*.
This must be controlled for in Phase 2's control-hierarchy figure (Figure A), and is a
first-class alternative explanation alongside H1–H5.

**Scientific consequence (stated carefully, per plan §3.15).**
D1/D2 affect the *refusal* arm and its *norm-matched random* arm **identically** — both used
the same misaligned position. Therefore:
- the **comparison** "refusal ≈ random" is still an apples-to-apples comparison, and the
  reported ASR numbers stand as reported;
- but the **interpretation** "we optimized the validated refusal projection in token space
  and it did not help" is **NOT supported**, because for 39/40 training prompts the objective
  was not reading the validated refusal coordinate at all.

Gate D's negative is therefore downgraded from "the refusal objective fails" to
**"an objective that mostly did not measure the refusal coordinate fails"** — which is a much
weaker statement and re-opens H3 (objective/optimizer failure). This is recorded as a
**SUPERSEDED-PENDING** status for the Gate-D interpretation, not a withdrawal of the numbers.

**Actions taken:** see gap matrix rows R1–R3 in `docs/ASYMMETRY_GAP_MATRIX.md`. A
per-task position fix is required before any Phase 3 work, and a corrected-objective arm
becomes a *scientifically justified* Phase 3 candidate (it tests a hypothesis the old run
could not test).

---
