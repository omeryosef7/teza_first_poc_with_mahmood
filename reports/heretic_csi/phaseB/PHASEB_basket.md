# Phase B — native last-position Heretic ARA as a control: `basket` (`reports/heretic_csi/phaseB/PHASEB_native_ara_basket_job1023185_r0_1791923138.json`)

Freeze rule (predeclared): COMPLETE trials with KL<=1.0: max opt_A y_install (tie: lower KL); else min KL. Chosen trial 5 (feasible=True); Pareto front: [0, 2, 5, 7, 8, 11, 12]
Readout impl: whole_answer_bs1_logits_to_keep/v2; readout xcheck vs frozen score_behavior: {'n_common': 565, 'max_abs_dy': 0.10581753407978478, 'mean_abs_dy': 0.006685805778382799, 'max_abs_dlogp_concept': 0.4257211685180664}

## Optuna trials (TRAIN objectives)

| trial | params | scores | s |
|---|---|---|---|
| 0 | `{"start_layer_index": 6, "end_layer_index": 23, "preserve_good_behavior_weight": 0.8775630370093042, "steer_bad_behavior_weight": 0.07203645744877606, "overcorrect_relative_weight": 0.15923029404371317, "neighbor_count": 5}` | y_install[basket] - A=0.9303, KL divergence=1.425, y_install[basket] - C=0.9186 | 105 |
| 1 | `{"start_layer_index": 5, "end_layer_index": 24, "preserve_good_behavior_weight": 0.8116654542543745, "steer_bad_behavior_weight": 0.47641600562599296, "overcorrect_relative_weight": 1.084291774882365, "neighbor_count": 7}` | y_install[basket] - A=0.004559, KL divergence=10.89, y_install[basket] - C=0.004475 | 108 |
| 2 | `{"start_layer_index": 7, "end_layer_index": 30, "preserve_good_behavior_weight": 0.833096158481096, "steer_bad_behavior_weight": 0.0005609675501520819, "overcorrect_relative_weight": 0.11051466306039866, "neighbor_count": 7}` | y_install[basket] - A=0.479, KL divergence=0.4043, y_install[basket] - C=0.4071 | 120 |
| 3 | `{"start_layer_index": 7, "end_layer_index": 17, "preserve_good_behavior_weight": 0.694585714797717, "steer_bad_behavior_weight": 0.0006193903767423291, "overcorrect_relative_weight": 0.19609375147499628, "neighbor_count": 3}` | y_install[basket] - A=0.11, KL divergence=0.4927, y_install[basket] - C=0.5025 | 81.8 |
| 4 | `{"start_layer_index": 9, "end_layer_index": 18, "preserve_good_behavior_weight": 0.8770535249084971, "steer_bad_behavior_weight": 0.004091319293540519, "overcorrect_relative_weight": 0.5474445908754897, "neighbor_count": 2}` | y_install[basket] - A=0.6501, KL divergence=1.208, y_install[basket] - C=0.3102 | 81.9 |
| 5 | `{"start_layer_index": 6, "end_layer_index": 30, "preserve_good_behavior_weight": 0.4195895270056811, "steer_bad_behavior_weight": 0.0005855383641820595, "overcorrect_relative_weight": 0.4887847678665711, "neighbor_count": 3}` | y_install[basket] - A=0.9126, KL divergence=0.939, y_install[basket] - C=0.2617 | 116 |
| 6 | `{"start_layer_index": 15, "end_layer_index": 16, "preserve_good_behavior_weight": 0.2578610976836281, "steer_bad_behavior_weight": 0.007838529613212153, "overcorrect_relative_weight": 0.6745540780210377, "neighbor_count": 8}` | y_install[basket] - A=0.07116, KL divergence=0.6694, y_install[basket] - C=0.2002 | 57.6 |
| 7 | `{"start_layer_index": 7, "end_layer_index": 26, "preserve_good_behavior_weight": 0.9493721107687194, "steer_bad_behavior_weight": 0.2933296441835878, "overcorrect_relative_weight": 1.1533490554783525, "neighbor_count": 9}` | y_install[basket] - A=0.9999, KL divergence=11.12, y_install[basket] - C=0.9999 | 104 |
| 8 | `{"start_layer_index": 3, "end_layer_index": 27, "preserve_good_behavior_weight": 0.29125367512040223, "steer_bad_behavior_weight": 0.00015244950046150427, "overcorrect_relative_weight": 0.5620051496487033, "neighbor_count": 2}` | y_install[basket] - A=0.01305, KL divergence=0.08477, y_install[basket] - C=0.6082 | 59.3 |
| 9 | `{"start_layer_index": 12, "end_layer_index": 32, "preserve_good_behavior_weight": 0.22970455456786804, "steer_bad_behavior_weight": 0.00023948162919821024, "overcorrect_relative_weight": 0.6188054677799601, "neighbor_count": 1}` | y_install[basket] - A=0.06184, KL divergence=0.374, y_install[basket] - C=0.3285 | 63.8 |
| 10 | `{"start_layer_index": 7, "end_layer_index": 32, "preserve_good_behavior_weight": 0.4319021383405692, "steer_bad_behavior_weight": 0.03219299666842102, "overcorrect_relative_weight": 0.19297831244583596, "neighbor_count": 4}` | y_install[basket] - A=0.1389, KL divergence=1.755, y_install[basket] - C=0.2488 | 129 |
| 11 | `{"start_layer_index": 9, "end_layer_index": 32, "preserve_good_behavior_weight": 0.8623385017569396, "steer_bad_behavior_weight": 0.0002561765955517839, "overcorrect_relative_weight": 0.1739461893661412, "neighbor_count": 6}` | y_install[basket] - A=0.3067, KL divergence=0.3373, y_install[basket] - C=0.4 | 75.2 |
| 12 | `{"start_layer_index": 5, "end_layer_index": 27, "preserve_good_behavior_weight": 0.8799530072818589, "steer_bad_behavior_weight": 0.0017417184184730426, "overcorrect_relative_weight": 0.15751953613297826, "neighbor_count": 12}` | y_install[basket] - A=0.6482, KL divergence=0.7112, y_install[basket] - C=0.3443 | 120 |
| 13 | `{"start_layer_index": 5, "end_layer_index": 31, "preserve_good_behavior_weight": 0.3507836616015763, "steer_bad_behavior_weight": 0.0004622422918789675, "overcorrect_relative_weight": 0.577952325025122, "neighbor_count": 12}` | y_install[basket] - A=0.5592, KL divergence=1.362, y_install[basket] - C=0.0812 | 119 |
| 14 | `{"start_layer_index": 3, "end_layer_index": 32, "preserve_good_behavior_weight": 0.6145155772600787, "steer_bad_behavior_weight": 0.004618936990333101, "overcorrect_relative_weight": 0.7013166009566715, "neighbor_count": 4}` | y_install[basket] - A=0.8779, KL divergence=1.64, y_install[basket] - C=0.5408 | 141 |
| 15 | `{"start_layer_index": 2, "end_layer_index": 32, "preserve_good_behavior_weight": 0.29381147955436004, "steer_bad_behavior_weight": 0.0003129554125661372, "overcorrect_relative_weight": 0.06293222591131781, "neighbor_count": 7}` | y_install[basket] - A=0.1989, KL divergence=0.3626, y_install[basket] - C=0.4043 | 84.3 |

## Frozen-ARA reads (domain-mean y_install; dY vs base, same rows)

| set | base y | ARA y | dY | n_rows/n_dom | median option mass base->ARA | mean logp concept base->ARA | mean logp codeword base->ARA |
|---|---|---|---|---|---|---|---|
| trainread_A | 9.579e-05 | 0.914 | 0.9139 | 335/67 | 0.08814 -> 0.1516 | -16.28 -> -2.428 | -2.771 -> -7.092 |
| trainread_C | 0.4804 | 0.2428 | -0.2375 | 335/67 | 0.08273 -> 0.03746 | -5.571 -> -7.999 | -4.68 -> -4.2 |
| val_A | 8.215e-06 | 0.9253 | 0.9253 | 230/23 | 0.1083 -> 0.1145 | -16.33 -> -2.425 | -2.656 -> -6.754 |
| val_C | 0.4023 | 0.2785 | -0.1238 | 230/23 | 0.07796 -> 0.03627 | -6.181 -> -7.546 | -4.534 -> -4.417 |

KL(base||ARA) on val_C first token: 0.8548
Keyword refusal (SECONDARY; Heretic KeywordRate, 46 behavioral val C prompts): base 0.06522 -> ARA 0.02174

## Primary (val_A) vs rank-matched controls

observed dY_val_A = **0.9253**; rank 1/43; one-sided p = 0.02326 (floor 0.02326); installation fraction of the base C-A gap = 2.3

| control | dY_val_A |
|---|---|
| random_spectrum_matched #5 | 6.118e-05 |
| random_spectrum_matched #9 | 4.293e-05 |
| random_spectrum_matched #34 | 3.82e-05 |
| random_spectrum_matched #19 | 3.648e-05 |
| random_spectrum_matched #26 | 2.783e-05 |
| random_spectrum_matched #18 | 2.444e-05 |
| random_spectrum_matched #33 | 2.399e-05 |
| random_spectrum_matched #7 | 1.711e-05 |
| random_spectrum_matched #10 | 1.582e-05 |
| random_spectrum_matched #12 | 1.579e-05 |
| random_spectrum_matched #35 | 1.466e-05 |
| random_spectrum_matched #37 | 1.304e-05 |
| random_spectrum_matched #14 | 1.267e-05 |
| random_spectrum_matched #1 | 1.175e-05 |
| random_spectrum_matched #28 | 9.327e-06 |
| random_spectrum_matched #4 | 8.069e-06 |
| random_spectrum_matched #16 | 7.031e-06 |
| random_spectrum_matched #30 | 6.266e-06 |
| random_spectrum_matched #22 | 4.928e-06 |
| random_spectrum_matched #27 | 4.441e-06 |
| random_spectrum_matched #23 | 4.188e-06 |
| random_spectrum_matched #3 | 3.703e-06 |
| random_spectrum_matched #17 | 3.068e-06 |
| random_spectrum_matched #32 | 1.224e-06 |
| random_spectrum_matched #36 | 6.186e-07 |
| random_spectrum_matched #31 | 3.729e-07 |
| random_spectrum_matched #20 | 3.695e-07 |
| label_shuffled_ara #0 | 0 |
| label_shuffled_ara #1 | 0 |
| label_shuffled_ara #2 | 0 |
| random_spectrum_matched #38 | -7.55e-07 |
| random_spectrum_matched #11 | -7.694e-07 |
| random_spectrum_matched #2 | -1.014e-06 |
| random_spectrum_matched #15 | -1.71e-06 |
| random_spectrum_matched #25 | -1.829e-06 |
| random_spectrum_matched #13 | -2.453e-06 |
| random_spectrum_matched #21 | -2.46e-06 |
| random_spectrum_matched #24 | -2.859e-06 |
| random_spectrum_matched #8 | -3.018e-06 |
| random_spectrum_matched #29 | -3.049e-06 |
| random_spectrum_matched #6 | -3.91e-06 |
| random_spectrum_matched #0 | -4.048e-06 |

## Frozen params refit at other ranks (descriptive / MEASURED)

| rank | dY val_A | dY val_C | KL val_C |
|---|---|---|---|
| 1 | 0 | 0 | 6.129e-06 |
| 8 | 0.4262 | -0.07956 | 0.5811 |

