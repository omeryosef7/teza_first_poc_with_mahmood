# Phase A — Heretic machinery audit (`reports/heretic_csi/PHASE_A_heretic_audit_job1023185_r0.json`)

Env: {'torch': '2.13.0+cu126', 'cuda': '12.6', 'transformers': '5.6.2', 'optuna': '4.8.0', 'gpu': 'NVIDIA L40S', 'compute_cap': [8, 9], 'slurm_job': '1023185', 'slurm_restart': '0'}
Params (fixed): `{"start_layer_index": 12, "end_layer_index": 16, "preserve_good_behavior_weight": 0.5, "steer_bad_behavior_weight": 0.1, "overcorrect_relative_weight": 0.5, "neighbor_count": 5}`, rank=8

| check | value | verdict |
|---|---|---|
| load | {'ok': True, 'dtype': 'torch.bfloat16', 'attn_implementation': 'eager', 'n_layers': 32} | eager+bf16=True |
| base determinism (base vs base) | max|dlogit|=0 | True |
| identity: LoRA-wrapped (B=0) vs unwrapped base | max|dlogit|=0.0625, max KL=4.237e-07, greedy16 identical=True | within bf16: True |
| modify changes model | max|dlogit|=12.84, mean KL=1.234 (n=16) | True |
| reset -> identity state | max|dlogit| vs identity=0, vs base=0.0625, greedy16 identical=True, max|dW|=0 | True |
| reset leaves lora_A changed (shipped Heretic) | max|A - A_init|=0.2006 | FINDING: True |
| replay, shipped reset (history-dependent) | rel||dW1-dW2||=1.08, max|dlogit|=4.195 | FINDING: not replayable |
| replay, lora_A restored | rel||dW1-dW3||=0, max|dlogit|=0 | True |
| Optuna resume | 2 -> loaded 2 -> 3; values ['0.07056', '10.34', '0.07056']; trial0 replay |diff|=0 | True |
| y_install readout vs frozen score_behavior | n=24, max|dy|=0.0822, mean|dy|=0.008801, max|dlogp_c|=0.3246 | mean|dy|<=0.015: True |

## Learned dW per module (ARA, preserve_row_magnitudes=True)

| layer | comp | ||dW||_F | ||dW||/||W|| | num. rank (cfg) | eff. rank | top-3 s | rel gap deployed vs objective-form | ARA loss base / deployed / objective-form |
|---|---|---|---|---|---|---|---|---|
| 12 | attn.o_proj | 2.828 | 0.06318 | 8 (8) | 1.98 | 2.57, 0.787, 0.66 | 0.04175 | 0.06893 / 0.0002473 / 0.0002176 |
| 12 | mlp.down_proj | 14.01 | 0.1524 | 8 (8) | 1.01 | 14.1, 0.228, 0.175 | 0.1265 | 0.07115 / 0.01896 / 0.01779 |
| 13 | attn.o_proj | 12.11 | 0.2764 | 8 (8) | 1.03 | 12.1, 0.702, 0.34 | 0.232 | 0.1189 / 0.01008 / 0.005167 |
| 13 | mlp.down_proj | 1.997 | 0.02171 | 8 (8) | 4.01 | 1.15, 1.06, 1.01 | 0.009947 | 0.1157 / -0.004212 / -0.004209 |
| 14 | attn.o_proj | 1.409 | 0.0323 | 8 (8) | 3.49 | 1.02, 0.625, 0.574 | 0.01745 | 0.1367 / -4.648e-05 / -4.767e-05 |
| 14 | mlp.down_proj | 5.878 | 0.06397 | 8 (8) | 1.18 | 5.81, 0.954, 0.415 | 0.04661 | 0.1379 / 0.008276 / 0.008157 |
| 15 | attn.o_proj | 2.157 | 0.04762 | 8 (8) | 3.43 | 1.7, 0.73, 0.702 | 0.01904 | 0.2369 / -0.01582 / -0.01583 |
| 15 | mlp.down_proj | 32.17 | 0.351 | 8 (8) | 1.03 | 32.2, 1.52, 0.969 | 0.2979 | 0.2067 / 0.02791 / 0.02465 |

max rel gap (deployed W+BA vs objective-form normalize(W+BA)*||W||_row): **0.2979**


## Findings (Heretic @ 662e4ba2, verified on Llama-3.1-8B-Instruct, L40S, job 1023185; earlier gate-failed run 1022919 kept as superseded record)
1. **Reset is not a full reset.** `ARA.reset_model` → `Model.reset_model` zeroes `lora_B` only; `lora_A` keeps the previous trial's optimized values (max|A−A_init| = 0.20). Because L-BFGS optimizes A and B jointly from their current values, re-running identical parameters after a reset gives a different operator (rel‖ΔW1−ΔW2‖ = 1.08, max|Δlogit| = 4.2). Shipped Optuna trials are therefore history-dependent and a stored trial is not exactly replayable (job 1022919: trial-0 value 0.0706 vs replay 0.0513). Restoring `lora_A` to its post-`apply_lora` snapshot makes replay **bit-exact** (ΔW diff 0, logits diff 0; Optuna trial-0 replay |diff| = 0). Our drivers restore A at every reset (documented deviation from shipped Heretic).
2. **Deployed ≠ optimized operator.** With the default `preserve_row_magnitudes=True`, ARA's loss is evaluated on `normalize(W+BA)·‖W‖_row`, but the PEFT adapter deploys `W+BA`. Per-module relative gap 1–30% (max 0.298, L15 `down_proj`); the ARA loss on the captured I/O is similar for both forms, so the gap is mostly in directions the captured last-position I/O does not constrain. Any SVD of "the ARA operator" must say which form it analyses (we analyse the DEPLOYED `B@A`).
3. **Learned ΔW is numerically full-rank-r but often effectively rank ≈1** (entropy effective rank 1.0–4.0 at r=8; the largest-norm modules, e.g. L15 `down_proj` ‖ΔW‖/‖W‖ = 0.35, are ≈ rank-1).
4. **Resume duplicates trials.** On resume, Heretic re-creates `TPESampler(seed=settings.seed)`, so the startup phase re-draws the same parameters: resumed trial 2 = trial 0's parameters exactly (value 0.07056 both). Resumed studies waste trials on duplicates.
5. **Identity / reset numerics.** Base logits are deterministic (base vs base: 0). The LoRA-wrapped model with B=0 differs from the unwrapped base by max|Δlogit| = 0.0625 (KL 4e-7, greedy-16 identical): bf16-level, from wrapping. Reset returns exactly to the B=0 identity state (Δ = 0).
6. **Readout port fidelity.** Our `y_install` port (whole-answer, batch 1) vs frozen `score_behavior` on the same 24 rows (different GPU type + torch 2.13 vs 2.7): mean|dy| = 0.0088, max 0.082. The frozen pipeline itself is bit-exact within one GPU type but differs **across GPU types** by mean|dy| 0.009–0.013 (max up to 0.25, |dlogp| up to 0.87; existing `hcsi_p2a_*_BASE` runs, n up to 670). The port is inside that envelope. Gate criterion mean|dy| ≤ 0.015 (set from the frozen pipeline's own noise, not from any endpoint).
7. Llama-3.1 chat template: empty system message == CSI no-system template, byte-identical (date stays "26 Jul 2024" in transformers 5.6.2).
