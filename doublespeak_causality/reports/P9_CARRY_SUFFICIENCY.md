# §9 — Behavioral Sufficiency of the Carry Heads (during generation) — NULL

**Status:** NULL. Installing the DS carry-head state into a matched context during generation does **not** raise
ASR → the L14-21 carry heads are **not behaviorally sufficient** (they move the representation, not behavior).
Another clean confirmation of concept-circuit epiphenomenality (with §10).

**Run:** `phase9_carry_sufficiency.py` (`...736570`), v3 clearharm (train 44 / test 42), receiver=neutral.
Reuses pc.ZHeadCapture/ZHeadPatch (phase7c) + behav_judge.

## Result — ΔASR vs baseline (paired McNemar)
| arm | train (n=44) | test (n=42) |
|---|---|---|
| carry_install (DS carry-z @ decision) | +0.023 (p=1.0) | −0.048 (p=0.5) |
| rand_install (count-matched random heads) | 0.000 | −0.024 |
| self_install (no-op) | 0.000 | 0.000 |
| write_carry (L9 write + carry combined) | −0.091 (p=0.29) | −0.071 (p=0.25) |
carry−rand specificity: +0.023 (train) / −0.024 (test) ≈ 0.

## Interpretation
carry_install ΔASR is null and not distinguishable from the random-head control; combined write+carry is if
anything slightly negative (ns). So the concept carry-heads — which the earlier work showed are partially
sufficient for the *representational* p_concept readout (+0.16–0.47) — are **behaviorally inert**: installing
them does not induce compliance. Consistent with §10 (concept circuit behaviorally negligible at power) and the
concept-vs-refusal dissociation. Caveat: decision-position install propagates via KV cache (not per-token);
n=44/42 per split (>=20/cell) but small — a null at this n is informative given the effect-of-interest was
"install makes it comply", which does not happen.
