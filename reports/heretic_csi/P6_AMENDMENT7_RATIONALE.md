# P6 Amendment 7 — rationale (DRAFT, for parent review; nothing committed)

Written 2026-10-15 in response to adversarial review #10 (M1–M4, L1), **before** the G2 results of whistle/chair (job 1042284) or
ribbon were read. Config: `configs/heretic_csi/PREREG_P6_AMENDMENT_7.json`.

**Why now.** Stage-0 is done for all 21 codewords: 14 untouched codewords pass G1+G2+G3; whistle, chair, ribbon pass G3+G1 and await G2;
yogurt, banana, balloon failed G3 (candle is outside the 20). So at most **17** survivors → at most **12** confirmation codewords after a
5-codeword DEV draw — exactly the CANNOT-ANSWER boundary. Whether to extend the pool must therefore be decided by a rule written *before* the
last three G2 outcomes exist, otherwise "extend / don't extend" is conditional on partial outcomes.

**(a) Contingent extension.** Trigger S < 17 (n_conf < 12); no extension at exactly 12 (UNDERPOWERED run instead; option B = also extend to 15
is parent decision D1). Replacements come from a mechanically screened, seeded, ordered list built with no Stage-0 data (62 seeds → 10
passers; skewed low-Zipf — declared), run through the identical frozen pipeline and gates, ≤3 per Stage-0 job, cap 8 attempts. Tertiles by
frozen Zipf cutpoints (reproduces the original 7/7/6). DEV draw once, after the extension is final.

**(b) Post-draw VOID.** A VOID (AMENDMENT_6) or NOT-ESTIMABLE codeword after confirmation GPU is spent can push n_conf below 12; the rule is
now pre-declared: one whole re-run, then n_conf_final < 12 ⇒ H6a CANNOT ANSWER (reported descriptively).

**(c) Power wording.** IUT power at n_conf = 12 is 0.43–0.60 (ρ 0.7) / 0.58–0.74 (ρ 0.8); at 15, 0.57–0.72 / 0.73–0.84. "~0.5–0.7" was loose;
"UNDERPOWERED for ρ < 0.8" never meant ρ = 0.8 is adequately powered. Upper bounds (iid model; compressed ranges; shared controls/domains).

**(d) VAL floor.** Record floor-surviving keys/domains per codeword from the rescue BASE arm itself (not from Stage-0, to avoid reading
before the rule exists); fewer than 15 of 23 domains with ≥1 key ⇒ z NOT ESTIMABLE ⇒ attrition (decision D3).

**(e) TEST wording.** "TEST never read" was not literally true (banks contain TEST rows; readouts score them as BASE option mass; a manifest
key included them; a review script printed them). New wording: no TEST rescue outcome and no TEST-based gate. Key removed from code and all
21 manifests.

**(f) A4 disclosure.** G3 was re-implemented to the frozen text after lamp and candle had been scored under the pooled gate; only lamp's
verdict changes (0.0285 → 0.0754). Pre-declared leave-lamp-out sensitivity S3.

Not addressed: review #10 M5–M7 (S-199 / P4 v2 analyzer).
