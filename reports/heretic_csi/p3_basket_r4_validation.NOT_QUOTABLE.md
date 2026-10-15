# NOT QUOTABLE — p3_basket_r4_validation.json

This P3 truncation/removal read is **VOID** under its frozen rules (S-176): the preregistered REEXP-reproduces-CAND
per-row tolerance failed (max 0.072 > 0.01). Every number in `p3_basket_r4_validation.json` is a measurement from an
invalid read and must not be quoted as a P3 result, a minimal subspace, or a component-necessity finding. The cause
(float32 SVD re-expression vs bf16 re-rounding) is an untested HYPOTHESIS. The JSON is kept unmodified for provenance.
