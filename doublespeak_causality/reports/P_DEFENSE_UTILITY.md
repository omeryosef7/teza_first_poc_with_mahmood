# §19–21 — Causal Refusal-Restoration Defense & Utility (Gate F)

**Status:** Attack defense **WORKS and is specific**, but **FAILS the utility bar at this calibrated dose**
(large benign over-refusal). Honest **Gate F: not utility-preserving as implemented** → motivates §21
(minimal-dose) and §19.3 (mechanism-triggered gating). Attack-side ASR reduction is a strong positive.

**Run:** `defense_util_clearharm_...732688` (127r, v3b clearharm train85/test42) · commit `81e0476e` ·
harness `scripts/phase_defense_utility.py` (reuses the calinj calibrated-restoration recipe + `behav_judge`).
Provenance note: the summary reconciles with raw (my reviewed harness), but `validate_all_outputs.py`
mis-detects it as `behav` schema — a **`defense_util` validator schema is being added (§36)**; not a data issue.

## Design
Per validated layer L∈{16,18,20}, calibrated α (direct−ds gap): apply `pc.AllPositionAdd` of the refusal
direction during generation. **Attack** (Doublespeak, judged): `ds_base`, `ds_def_L`, `ds_defrand_L`.
**Utility** (v3b `benign_prompt` — a codeword-benign, attack-structured prompt; refusal-only classified):
`benign_base`, `benign_def_L`, `benign_defrand_L`. Endpoints: attack ΔASR (paired McNemar) + benign
over-refusal (Δ REJECTED rate). Degeneration guards: empty rate + truncation (`len`).

## Result — train (n=85; ds_base ASR=0.318; benign_base refusal=0.377)
| L (α) | attack ΔASR (p) | rand ΔASR | benign over-refusal | rand over-refusal | def truncation |
|---|---|---|---|---|---|
| L16 (1.97) | **−0.153 (p=0.0024)** | −0.082 | **+0.282** | +0.106 | 0.19 |
| L18 (2.83) | **−0.224 (p=2e-5)** | +0.047 | **+0.376** | −0.071 | 0.16 |
| L20 (3.59) | **−0.188 (p=0.0004)** | −0.012 | **+0.400** | −0.012 | 0.16 |

**test (n=42; ds_base ASR=0.190, floor):** attack ΔASR all ns (attack already near floor); benign
over-refusal +0.10–0.12; truncation ~0.19.

## Interpretation
1. **The defense works and is specific to the refusal axis:** calibrated restoration lowers attack ASR by
   0.15–0.22 (p down to 2e-5) on train; the norm-matched **random** control does **not** defend (rand ΔASR
   ≈0). So the effect is the refusal direction, not generic perturbation — consistent with §3/Gate B.
2. **But it is NOT selective:** the same restoration raises **benign** refusal by +0.28–0.40 (0.38→0.75 at
   L18), and again this is **refusal-axis-specific** (random over-refusal ≈0). Restoring refusal at a dose
   calibrated to the *attack* gap over-refuses benign prompts → **Gate F FAIL** at this calibration ("a large
   refusal vector makes everything refuse," the §20 anti-pattern).
3. **Caveat on "benign":** v3b `benign_prompt` is attack-*structured* (benign codeword in the DS template), so
   baseline refusal is already high (0.38–0.45); over-refusal on truly *unrelated-normal* prompts (§20's fifth
   condition) was **not** tested and is likely lower. Truncation ~0.16–0.19 under defense (empty=0, coherent).

## Verdict & next
- **Gate F (this dose): FAIL** — effective, specific attack defense but unacceptable benign over-refusal.
- **§21 minimal-dose:** sweep α downward per layer to find the point that defends with tolerable over-refusal
  (α50 / smallest reliably-effective α); the attack effect at L18 is large, so a lower α may retain defense
  with less collateral.
- **§19.3 mechanism-triggered:** fire restoration only when harmful-intent evidence is high AND refusal is
  anomalously suppressed (the §3/Gate B signature) → far fewer benign false positives.
- **§20 utility completeness:** add the unrelated-normal condition before any "utility-preserving" claim.
- Feeds Figure F7 (ASR reduction vs benign utility), reported honestly as a dose/selectivity tradeoff.
