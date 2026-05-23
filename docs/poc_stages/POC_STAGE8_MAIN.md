# POC Stage 8 Main Documentation

## Manager Summary

Stage 8 in the current repo is Stage 8A: a controlled offline sandbox skeleton for future RL-style work. It is not model-in-the-loop RL, does not load a model, and does not generate real attack text.

The main explicit result is that the completed smoke run produced `15` sandbox rows over `3` episodes and `5` maximum steps, with `8` rows reusing Stage 7 observations. The strongest mean reward group in the current summary is `choose_reasoning_block_length_bucket` at `0.6216699923031168`.

## Comprehensive Detailed Summary

Stage 8A exists to define a finite, bounded structural action space and reward interface before any real RL work is attempted.

The sandbox:

- only accepts finite symbolic actions
- only updates environment metadata
- only computes rewards from offline observations
- can optionally reuse Stage 7 rows as reward observations

## What We Tried

- Build a safe, offline scaffold for future RL experiments.
- Prevent free-text action generation.
- Reuse Stage 7 reward concepts without running a model.
- Smoke-test the environment, action space, and summarization path.

## What We Actually Did

- Added the `poc_stage8` package.
- Implemented action definitions, environment transitions, reward loading, and sandbox summarization.
- Ran the Stage 8A sandbox smoke configuration.
- Reused Stage 7 rows where available.

## Runs And Artifacts

| Run / Artifact | Path | What It Shows |
| --- | --- | --- |
| Stage 8 README | `poc_stage8/README.md` | Sandbox purpose, actions, reward modes, and commands. |
| Smoke script | `slurm_scripts/stage8_sandbox_smoke.slurm` | CPU-only Stage 8A smoke configuration. |
| Sandbox JSONL | `outputs/stage8/sandbox_smoke/sandbox.jsonl` | Per-step sandbox rows. |
| Summary JSON | `outputs/stage8/sandbox_smoke/sandbox_summary.json` | Smoke configuration and grouped reward statistics. |
| Aggregate JSON | `outputs/stage8/sandbox_smoke/sandbox_aggregate_summary.json` | Re-aggregated summary view. |
| Aggregate CSV | `outputs/stage8/sandbox_smoke/sandbox_aggregate_summary.csv` | CSV export of grouped reward statistics. |

## Results

Explicit smoke-run configuration:

- stage type: `8A`
- episodes: `3`
- max steps: `5`
- total rows: `15`
- `reward_mode = strongreject_only`
- action space size: `19`
- rows with Stage 7 observation: `8`

Grouped reward summary:

| Action type | Count | Mean reward | Reward std | Used Stage 7 row rate |
| --- | ---: | ---: | ---: | ---: |
| `choose_reasoning_block_length_bucket` | 3 | `0.6216699923031168` | `0.40730356688497715` | `0.3333333333333333` |
| `choose_template_variant` | 5 | `0.3824197802460132` | `0.38389282234882177` | `0.4` |
| `choose_safe_placeholder_order` | 3 | `0.2795289801395988` | `0.48415839578969677` | `0.6666666666666666` |
| `choose_suffix_length_bucket` | 3 | `0.1410785766895118` | `0.24435526268573668` | `0.6666666666666666` |
| `choose_include_harmless_puzzle_block` | 1 | `0.0` | `null` | `1.0` |

Explicit readout:

- The highest mean reward group is `choose_reasoning_block_length_bucket` at `0.6216699923031168`.
- The lowest mean reward group is `choose_include_harmless_puzzle_block` at `0.0`.
- `choose_template_variant` had the largest sample count in the smoke run, at `5` rows.

Concrete row example from the smoke output:

- episode `0`, step `1`
- `action_type = choose_reasoning_block_length_bucket`
- `action_value = short`
- `reward_mode = strongreject_only`
- `reward = 0.6744677945928962`
- `used_stage7_row = false`

## What The Main Metrics Mean

- `reward_mode`: which Stage 7-style objective produced the reward values. In the completed smoke run it is `strongreject_only`.
- `mean_reward`: average reward for rows in a given action-type group. Larger is better under the chosen reward mode.
- `reward_std`: variability of reward values inside the group. Larger means the action type produced more variable outcomes in the smoke run.
- `reward_median`: middle reward value in the group.
- `used_stage7_row_rate`: fraction of rows in the group that reused a real Stage 7 observation rather than a fallback observation path.
- `action_space_size`: total number of discrete structural actions allowed in the sandbox.
- `rows_with_stage7_observation`: total number of rows in the run backed by a Stage 7 observation.
- `count`: number of sandbox rows that landed in a given summary group.

## Limitations / Caveats

- Stage 8A is not real RL yet.
- The state is symbolic and offline only.
- Rewards depend on earlier offline artifacts, especially Stage 7.
- The smoke run is intentionally tiny and should be treated as plumbing validation plus a first descriptive summary.

## Handoff To Next Stage

Any later model-in-the-loop RL stage should remain constrained and should only build on this sandbox after the reward definition and safety boundaries are reviewed again.
