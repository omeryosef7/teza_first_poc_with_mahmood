# P3 truncation/removal of the FROZEN basket r4 CAND on VALIDATION (PREREG_P3_TRUNC.json). GATED by p3_gate.py on the P2b basket VALIDATION verdict.
CW=basket R=4 SPLIT=validation VAL_VERDICT_JSON=${VAL_VERDICT_JSON:-reports/heretic_csi/p2b_basket_primary_validation.json} NRAND=40 NRAND_N=20 bash outputs/heretic_csi/p2b/plans/p3_trunc_template.sh
