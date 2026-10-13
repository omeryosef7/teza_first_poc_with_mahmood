# Phase B — native last-position Heretic ARA as a control: `button` (`reports/heretic_csi/phaseB/PHASEB_native_ara_button_job1023251_r0_1791924143.json`)

Freeze rule (predeclared): COMPLETE trials with KL<=1.0: max opt_A y_install (tie: lower KL); else min KL. Chosen trial 13 (feasible=True); Pareto front: [1, 2, 8, 9, 13, 14, 15]
Readout impl: whole_answer_bs1_logits_to_keep/v2; readout xcheck vs frozen score_behavior: {'n_common': 565, 'max_abs_dy': 0.07933111982498564, 'mean_abs_dy': 0.006836946215718096, 'max_abs_dlogp_concept': 0.5331859588623047}

## Optuna trials (TRAIN objectives)

| trial | params | scores | s |
|---|---|---|---|
| 0 | `{"start_layer_index": 6, "end_layer_index": 23, "preserve_good_behavior_weight": 0.8775630370093042, "steer_bad_behavior_weight": 0.07203645744877606, "overcorrect_relative_weight": 0.15923029404371317, "neighbor_count": 5}` | y_install[button] - A=0.6865, KL divergence=0.8688, y_install[button] - C=0.8205 | 116 |
| 1 | `{"start_layer_index": 5, "end_layer_index": 24, "preserve_good_behavior_weight": 0.8116654542543745, "steer_bad_behavior_weight": 0.47641600562599296, "overcorrect_relative_weight": 1.084291774882365, "neighbor_count": 7}` | y_install[button] - A=0.9979, KL divergence=9.608, y_install[button] - C=0.9979 | 105 |
| 2 | `{"start_layer_index": 7, "end_layer_index": 30, "preserve_good_behavior_weight": 0.833096158481096, "steer_bad_behavior_weight": 0.0005609675501520819, "overcorrect_relative_weight": 0.11051466306039866, "neighbor_count": 7}` | y_install[button] - A=0.7028, KL divergence=0.3969, y_install[button] - C=0.5796 | 120 |
| 3 | `{"start_layer_index": 7, "end_layer_index": 17, "preserve_good_behavior_weight": 0.694585714797717, "steer_bad_behavior_weight": 0.0006193903767423291, "overcorrect_relative_weight": 0.19609375147499628, "neighbor_count": 3}` | y_install[button] - A=0.008623, KL divergence=0.4465, y_install[button] - C=0.5637 | 85.5 |
| 4 | `{"start_layer_index": 9, "end_layer_index": 18, "preserve_good_behavior_weight": 0.8770535249084971, "steer_bad_behavior_weight": 0.004091319293540519, "overcorrect_relative_weight": 0.5474445908754897, "neighbor_count": 2}` | y_install[button] - A=0.1996, KL divergence=0.5027, y_install[button] - C=0.5642 | 81.8 |
| 5 | `{"start_layer_index": 6, "end_layer_index": 30, "preserve_good_behavior_weight": 0.4195895270056811, "steer_bad_behavior_weight": 0.0005855383641820595, "overcorrect_relative_weight": 0.4887847678665711, "neighbor_count": 3}` | y_install[button] - A=0.6961, KL divergence=0.5821, y_install[button] - C=0.5106 | 118 |
| 6 | `{"start_layer_index": 15, "end_layer_index": 16, "preserve_good_behavior_weight": 0.2578610976836281, "steer_bad_behavior_weight": 0.007838529613212153, "overcorrect_relative_weight": 0.6745540780210377, "neighbor_count": 8}` | y_install[button] - A=0.2951, KL divergence=0.3486, y_install[button] - C=0.5357 | 63 |
| 7 | `{"start_layer_index": 7, "end_layer_index": 26, "preserve_good_behavior_weight": 0.9493721107687194, "steer_bad_behavior_weight": 0.2933296441835878, "overcorrect_relative_weight": 1.1533490554783525, "neighbor_count": 9}` | y_install[button] - A=0.4219, KL divergence=12, y_install[button] - C=0.2888 | 104 |
| 8 | `{"start_layer_index": 6, "end_layer_index": 31, "preserve_good_behavior_weight": 0.9799689146095754, "steer_bad_behavior_weight": 0.0002509718629192008, "overcorrect_relative_weight": 0.30267103738856244, "neighbor_count": 9}` | y_install[button] - A=0.7247, KL divergence=0.4168, y_install[button] - C=0.5903 | 74.7 |
| 9 | `{"start_layer_index": 4, "end_layer_index": 32, "preserve_good_behavior_weight": 0.9935202759722745, "steer_bad_behavior_weight": 0.0001269442101505416, "overcorrect_relative_weight": 0.4372228679841403, "neighbor_count": 15}` | y_install[button] - A=0.00332, KL divergence=0.01608, y_install[button] - C=0.5976 | 64.1 |
| 10 | `{"start_layer_index": 0, "end_layer_index": 29, "preserve_good_behavior_weight": 0.9787036617044556, "steer_bad_behavior_weight": 0.02724534016207697, "overcorrect_relative_weight": 0.19642100937068024, "neighbor_count": 10}` | y_install[button] - A=0.3892, KL divergence=2.664, y_install[button] - C=0.341 | 145 |
| 11 | `{"start_layer_index": 4, "end_layer_index": 27, "preserve_good_behavior_weight": 0.9297651953889531, "steer_bad_behavior_weight": 0.00022264144774492765, "overcorrect_relative_weight": 0.808472538501801, "neighbor_count": 6}` | y_install[button] - A=0.4978, KL divergence=0.4875, y_install[button] - C=0.5435 | 63.7 |
| 12 | `{"start_layer_index": 0, "end_layer_index": 21, "preserve_good_behavior_weight": 0.6331111593617398, "steer_bad_behavior_weight": 0.30618845558101676, "overcorrect_relative_weight": 1.2597343698912953, "neighbor_count": 7}` | y_install[button] - A=0.9968, KL divergence=11.19, y_install[button] - C=0.9968 | 102 |
| 13 | `{"start_layer_index": 9, "end_layer_index": 31, "preserve_good_behavior_weight": 0.6221254486133758, "steer_bad_behavior_weight": 0.0029802574363172085, "overcorrect_relative_weight": 0.6350475268658392, "neighbor_count": 11}` | y_install[button] - A=0.8073, KL divergence=0.8326, y_install[button] - C=0.5346 | 120 |
| 14 | `{"start_layer_index": 10, "end_layer_index": 29, "preserve_good_behavior_weight": 0.8807927583291325, "steer_bad_behavior_weight": 0.0003394504414916668, "overcorrect_relative_weight": 0.0475564552391073, "neighbor_count": 2}` | y_install[button] - A=0.2582, KL divergence=0.2709, y_install[button] - C=0.5737 | 83.4 |
| 15 | `{"start_layer_index": 7, "end_layer_index": 28, "preserve_good_behavior_weight": 0.5082172213255284, "steer_bad_behavior_weight": 0.001097568058003711, "overcorrect_relative_weight": 0.03343034650990806, "neighbor_count": 11}` | y_install[button] - A=0.6874, KL divergence=0.3017, y_install[button] - C=0.6957 | 118 |

## Frozen-ARA reads (domain-mean y_install; dY vs base, same rows)

| set | base y | ARA y | dY | n_rows/n_dom | median option mass base->ARA | mean logp concept base->ARA | mean logp codeword base->ARA |
|---|---|---|---|---|---|---|---|
| trainread_A | 0.0001757 | 0.8054 | 0.8052 | 335/67 | 0.05139 -> 0.3462 | -14.7 -> -1.405 | -3.099 -> -3.172 |
| trainread_C | 0.6693 | 0.5218 | -0.1475 | 335/67 | 0.3477 -> 0.2102 | -2.817 -> -2.785 | -3.796 -> -2.885 |
| val_A | 0.000319 | 0.7965 | 0.7962 | 230/23 | 0.06088 -> 0.319 | -14.96 -> -1.541 | -3.188 -> -3.39 |
| val_C | 0.6733 | 0.5624 | -0.1109 | 230/23 | 0.2654 -> 0.2129 | -2.484 -> -2.534 | -3.64 -> -2.972 |

KL(base||ARA) on val_C first token: 1.022
Keyword refusal (SECONDARY; Heretic KeywordRate, 46 behavioral val C prompts): base 0.1957 -> ARA 0.08696

## Primary (val_A) vs rank-matched controls

observed dY_val_A = **0.7962**; rank 1/43; one-sided p = 0.02326 (floor 0.02326); installation fraction of the base C-A gap = 1.183

| control | dY_val_A |
|---|---|
| label_shuffled_ara #1 | 0.003532 |
| random_spectrum_matched #3 | 0.001817 |
| label_shuffled_ara #0 | 0.001525 |
| random_spectrum_matched #9 | 0.0009041 |
| random_spectrum_matched #24 | 0.0006654 |
| random_spectrum_matched #5 | 0.0005466 |
| random_spectrum_matched #14 | 0.000516 |
| random_spectrum_matched #31 | 0.0004889 |
| random_spectrum_matched #16 | 0.0004739 |
| label_shuffled_ara #2 | 0.0001499 |
| random_spectrum_matched #0 | 6.823e-05 |
| random_spectrum_matched #20 | 5.648e-05 |
| random_spectrum_matched #33 | 3.538e-05 |
| random_spectrum_matched #28 | 8.843e-06 |
| random_spectrum_matched #37 | 8.417e-06 |
| random_spectrum_matched #19 | 8.212e-06 |
| random_spectrum_matched #17 | -1.878e-05 |
| random_spectrum_matched #25 | -3.063e-05 |
| random_spectrum_matched #10 | -3.891e-05 |
| random_spectrum_matched #32 | -5.063e-05 |
| random_spectrum_matched #21 | -5.638e-05 |
| random_spectrum_matched #18 | -0.0001172 |
| random_spectrum_matched #6 | -0.0001338 |
| random_spectrum_matched #8 | -0.0001536 |
| random_spectrum_matched #36 | -0.0001595 |
| random_spectrum_matched #38 | -0.000162 |
| random_spectrum_matched #15 | -0.000196 |
| random_spectrum_matched #2 | -0.0002106 |
| random_spectrum_matched #30 | -0.0002183 |
| random_spectrum_matched #35 | -0.0002206 |
| random_spectrum_matched #34 | -0.0002217 |
| random_spectrum_matched #23 | -0.000228 |
| random_spectrum_matched #13 | -0.0002333 |
| random_spectrum_matched #4 | -0.0002424 |
| random_spectrum_matched #11 | -0.0002459 |
| random_spectrum_matched #29 | -0.0002509 |
| random_spectrum_matched #22 | -0.0002591 |
| random_spectrum_matched #12 | -0.0002616 |
| random_spectrum_matched #1 | -0.000273 |
| random_spectrum_matched #27 | -0.000276 |
| random_spectrum_matched #26 | -0.0002801 |
| random_spectrum_matched #7 | -0.0003026 |

## Frozen params refit at other ranks (descriptive / MEASURED)

| rank | dY val_A | dY val_C | KL val_C |
|---|---|---|---|
| 1 | 0.7532 | -0.1761 | 0.5547 |
| 8 | 0.4771 | -0.2329 | 1.23 |

