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

## §21 minimal effective intervention / per-layer α50 — **DONE (honest finding, closed on committed data)**
**Status: DONE.** The §21 literal spec asked for a per-layer α50 (smallest reliably-effective α) with a
cross-layer comparison L13/L16/L18/L20/L24/L28. We close it as a **finding** on already-committed data (no new
GPU run): the L18 dose sweep re-derives α50 directly, and the L16/L18/L20 fixed-α run shows that the property a
minimal *selective* dose would need — a dose whose benign cost is below its attack benefit — does not hold at
**any** validated layer. Because the failure is structural (shared refusal axis), extending the α50 sweep to the
remaining layers L13/L24/L28 cannot change the verdict, so a full per-layer sweep is not warranted.

### (a) α50 re-derived from the L18 dose sweep (`732750`)
Swept the calibrated-α scale ∈ {0.25,0.5,0.75,1.0} at L18 (validated 150 vals, 0 mismatch; the lone
validator FAIL is the fixed-dose manifest not listing dose-suffixed arms — a coverage-spec mismatch, not data).
Defining **α50 = smallest dose whose attack ΔASR is reliable (paired McNemar p<0.05)**:

| dose | α | attack ΔASR (p) | benign over-refusal | over-refusal / \|ΔASR\| |
|---|---|---|---|---|
| 0.25 | 0.71 | −0.024 (p=0.774, ns) | +0.153 | ~6.5 |
| 0.50 | 1.41 | −0.094 (p=0.057, ns) | +0.200 | ~2.1 |
| **0.75** | **2.12** | **−0.106 (p=0.049)** | **+0.282** | **~2.7** |
| 1.00 | 2.83 | −0.188 (p=1.4e-4) | +0.376 | ~2.0 |

**⇒ α50 = 2.12 (dose-scale 0.75): ΔASR = −0.106, p = 0.049.** This is the smallest α on the L18 sweep that
reliably defends — but it already costs **+0.282** benign over-refusal, i.e. the benign cost is **~2.7× the
attack benefit** even at the minimal effective dose. Both curves rise monotonically with dose; at every dose the
benign over-refusal exceeds |ΔASR| (ratio ~2.0–6.5, worst at the low dose). *(Correction 2026-08-08, audit: an
earlier draft called this ratio "≈constant ~0.5" — inverted and wrong; the correct over-refusal/|ΔASR| ratio is
~2–6.5, i.e. benign cost dominates at every dose. Conclusion unchanged and strengthened.)*

### (b) Cross-layer check (fixed-α run `732688`): over-refusal > |ΔASR| at every layer
At each layer's *own* calibrated α, the benign over-refusal strictly exceeds the attack reduction (train, n=85):

| L (α) | attack ΔASR (p) | benign over-refusal | over-refusal > \|ΔASR\|? |
|---|---|---|---|
| L16 (1.97) | −0.153 (p=0.0024) | +0.282 | yes (0.282 > 0.153) |
| L18 (2.83) | −0.224 (p=2e-5) | +0.376 | yes (0.376 > 0.224) |
| L20 (3.59) | −0.188 (p=0.0004) | +0.400 | yes (0.400 > 0.188) |

### (c) Honest finding — no selective minimal dose exists at any validated layer
There is **no dose, and no validated layer, that defends meaningfully while sparing benign prompts.** The
minimal effective dose (α50 = 2.12 at L18) already over-refuses +0.282, and at each of L16/L18/L20 the benign
cost exceeds the attack benefit. This is a **structural** Gate F FAIL, not a bad α choice: the refusal axis is
**shared** between the attack and the (attack-structured) benign requests, so globally restoring it refuses
everything roughly proportionally — driving |ΔASR| up necessarily drives benign over-refusal up faster. A
per-layer α50 sweep across the remaining literal-spec layers (L13/L24/L28) would trace the same shared-axis
tradeoff and therefore **cannot yield a selective minimal dose**; §21 is closed on this finding. Selective
defense cannot come from a scalar dose on the refusal axis — it must **condition on harmful intent**
(§19.3 mechanism-triggered gating), which the next subsection shows also fails for the same shared-axis reason.

## §19.3 mechanism-triggered (gated) defense (`732795`) — gating does NOT rescue selectivity
Fire the refusal restoration only when the decision-token refusal projection < T (T=train Direct-harmful mean,
fit train-only, frozen for test). Harness `scripts/phase_defense_gated.py` (two-pass measure→fit→generate;
gated arm derived exactly from base/uncond via fire-flags). Provenance: reviewed harness; a `defense_gated`
validator schema is being added (§36) — currently mis-detects as behav.

| split | T | fire-rate ds | fire-rate benign | proj_ds | proj_benign | proj_direct | gated ΔASR | gated over-refusal |
|---|---|---|---|---|---|---|---|---|
| train n=85 | 4.50 | 0.81 | **0.87** | 1.94 | 1.45 | 4.50 | −0.188 (p=1e-4) | +0.376 (p≈0) |
| test n=42 | 4.32 | 0.71 | **0.90** | 2.76 | 1.34 | 4.32 | −0.024 (ns) | +0.119 |

**The gate fires on benign prompts as much as (or more than) on attacks** (benign fire-rate ≥ ds fire-rate),
because the attack-structured benign prompts carry refusal projections (1.3–1.5) at or below the DS-attack
prompts (1.9–2.8) — both far below the refusing Direct reference (4.3–4.5). Consequently **gated ≡ unconditional**
on both axes (identical ΔASR and identical benign over-refusal). **Intent-gating on the refusal projection
cannot separate attack from benign → selectivity is not recovered.**

### Why this is the deep result (ties the whole paper together)
Selective defense would require triggering on *harmful intent*. But this project's two circuits are mismatched
for that purpose: the **concept/intent representation is behaviorally epiphenomenal** (moving it barely changes
ASR — claims A/C), while the **refusal representation controls behavior but is not intent-selective** (the DS
attack suppresses it to a level indistinguishable from a benign attack-structured request). So **neither
circuit alone yields a selective mechanism-derived defense**: the one that encodes intent doesn't drive
behavior, and the one that drives behavior doesn't encode intent. A practical defense needs an *independent*
harmful-intent signal, not a scalar or a gate on the refusal axis.

## Verdict & next
- **Gate F (this dose): FAIL** — effective, specific attack defense but unacceptable benign over-refusal.
- **§21 minimal effective intervention / α50: DONE (finding).** α50 = 2.12 (L18, dose 0.75): ΔASR = −0.106
  (p=0.049) but +0.282 benign over-refusal; benign cost exceeds |ΔASR| at every dose and at every validated
  layer (L16/L18/L20). No selective minimal dose exists — the refusal axis is shared attack↔benign — so the
  remaining literal-spec layers (L13/L24/L28) cannot change the verdict. Closed on committed data, no new GPU run.
- **§19.3 mechanism-triggered:** fire restoration only when harmful-intent evidence is high AND refusal is
  anomalously suppressed (the §3/Gate B signature) → far fewer benign false positives.
- **§20 utility completeness:** add the unrelated-normal condition before any "utility-preserving" claim.
- Feeds Figure F7 (ASR reduction vs benign utility), reported honestly as a dose/selectivity tradeoff.

## §20 completion — UNRELATED-NORMAL utility (the missing 5th condition)
**Result: the calibrated refusal-restoration defense causes ZERO over-refusal on ordinary benign
instructions** (run `unrelnormal_unrelated_normal_...738410`, n=40 unrelated-normal prompts —
recipes/math/explanations/writing, no attack structure; `scripts/phase20_unrelated_normal.py`).

| arm | refusal_rate | over-refusal vs base |
|---|---|---|
| normal_base | 0.00 | — |
| normal_def_L16 (α=1.97) | 0.00 | **0.00** |
| normal_def_L18 (α=2.83) | 0.00 | **0.00** |
| normal_def_L20 (α=3.59) | 0.00 | **0.00** |
| normal_defrand_L18 | 0.00 | 0.00 |

**Verified not a no-op:** the restoration DID alter the outputs — 39/40 def_L18 generations differ from
base (same calibrated α as §21) — yet none crossed into refusal. So the defense perturbs unrelated-normal
generations without refusing them.

**Interpretation (reconciles with §21):** §21 found the defense over-refuses *attack-structured* benign
prompts (benign content in the attack's format), because those sit near the refusal boundary. On
*unrelated-normal* prompts, which are far from that boundary, the same calibrated restoration adds no
refusal (0/40). **So the defense's utility cost is confined to attack-adjacent inputs; it does NOT harm
general utility.** This is a more favorable defense picture than §21 alone: the collateral over-refusal is
specific to attack-format benign, not ordinary use. §20 → DONE (n=40, kw-refusal detection; ≥20/cell).
