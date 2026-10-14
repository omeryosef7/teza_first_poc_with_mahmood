# P3 truncation/removal of the FROZEN button r4 CAND on VALIDATION. GATED: requires VAL_VERDICT_JSON = p2b_analyze VALIDATION output where button r4 PASSES.
CW=button R=4 SPLIT=validation VAL_VERDICT_JSON=${VAL_VERDICT_JSON:?set VAL_VERDICT_JSON} NRAND=40 bash outputs/heretic_csi/p2b/plans/p3_trunc_template.sh
