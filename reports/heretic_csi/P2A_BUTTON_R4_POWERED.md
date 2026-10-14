# PR-HCSI-S084 (+A1, + S-114 binding rule): powered re-test of button r4 on VALIDATION — FINAL: **PASS**

Frozen two-step read (configs/heretic_csi/ANALYSIS_COMMANDS_S084.md): `p2a_powered_analyze.py` (sha eb0da96d…) then
`p2a_powered_binding.py` (sha 6533f190…). Jobs: 1022698 (original: liveness, candidate, 46 RAND + 10 SHUF),
1027577 (RAND 46..117 + 4 overlap arms), 1032110 (RAND 118..189). All three a5000, single attempt each, 76/76 and 72/72
arms ok, 1 model load each.

| check | result |
|---|---|
| overlap OVL_{BASE,KO,CAND_r4,RAND_r4_0} vs 1022698 | max abs diff **0.0** on identical 230-id sets (bit-exact) |
| shared row set | **203** (deviation 0; no arm dropped keys) |
| gates | manipulation ✓ (KO−BASE −0.302), identity ✓, instrument ✓ (FULL−KO +0.142); VOID none |
| candidate statistic (mean_d KO_CAND_r4 − KO, unrounded) | **0.012916**; CI [0.00651, 0.01895]; 20/23 domains positive |
| recovery fraction | 0.0909 [0.0506, 0.1244] |
| rank among 200 controls | **1/201** (unrounded) = **1/201** (frozen analyzer, rounded) |
| p_ext | 1/201 = 0.004975 |
| Holm over {r1 0.2456, r16 0.1754, r4 0.004975} | r4 **0.0149** < 0.05; r1 = r16 = 0.3508 |
| beat every SHUF (n=10) | **yes** — max SHUF = KO_SHUF_r4_9 0.009244 (margin +0.0037) |
| best RAND (n=190) | KO_RAND_r4_120 0.008075; RAND mean 0.00049, sd 0.00309 (candidate ≈ 4.0 RAND-sd above the RAND mean) |
| unrounded vs rounded decision | both PASS ⇒ **FINAL_VERDICT: PASS** |

Scope (frozen in the prereg): SAME VALIDATION data re-analysed with a 200-control null; resolves the floor
limitation and corrects for the 3 declared button VAL looks only. Rank 4 was chosen on TRAIN K4. The SHUF null is
still only n=10 (the candidate beats all 10, but the SHUF-only floor is 1/11). Not a fresh test (needs P6 codewords);
activation-space PLS family only; semantic installation only; no behavioral claim. The descriptive basket-vs-button
interaction is control-family-dependent (v2: RAND −1.05, SHUF +2.96, pooled +6.09) ⇒ "dimensionality difference" is
NOT supported by a contrast.

Artifacts: reports/heretic_csi/P2A_BUTTON_R4_POWERED.json (sha 0c4507ab…), P2A_BUTTON_R4_POWERED_BINDING.json
(26f3c617…), hcsi_p2a_button_r4ext_validation_analyzer.json (485d9028…); log outputs/heretic_csi/logs/analyze_button_r4ext_val.log.
