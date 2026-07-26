# Gate-3 Soft-Prompt Trajectory Diagnostic

Source: `outputs/phase_d_soft_prompt_gate3_conf`

Question: does the soft-prompt objective actually OPTIMIZE across steps (expected_reward / sampled_asr trending up), and how does the REINFORCE arm compare to the prefix_ce arm? Slope = OLS of the scalar vs step index; a slope near 0 (|slope| <= 0.0001) is treated as flat. Numbers only; no behavior text; no PASS/FAIL claim.

## Per-objective read

- prefix_ce: expected_reward slope mean = 0.000184054 (4 positive / 2 flat / 6 negative of 12 scored, 12 runs); mean first->last delta = 0.119792; sampled_asr slope mean = 0.000203634; greedy_asr_proxy hit 1.0 in 0 runs (0 at final step, 0 transient only).
- reinforce: expected_reward slope mean = 0.00165328 (6 positive / 1 flat / 4 negative of 11 scored, 11 runs); mean first->last delta = 0.15625; sampled_asr slope mean = 0.00218729; greedy_asr_proxy hit 1.0 in 4 runs (1 at final step, 3 transient only).

## Notes

- `exp_reward_slope` > 0 means expected_reward rises across steps (objective is moving the soft prompt toward higher reward).
- A flat/noisy expected_reward slope with sampled_asr staying near its start supports 'the objective is not effectively improving behavior at this budget.'
- A rising slope while sampled_asr lags supports 'it optimizes but the reported metric is a truncation proxy.'
- `greedy_proxy_transient` counts runs where greedy_asr_proxy hit 1.0 at some step but not the final step (transient spikes).

Per-run detail: see `results/GATE3_TRAJECTORY_DIAG.csv`.
