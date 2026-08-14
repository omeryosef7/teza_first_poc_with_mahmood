# BOMBNESS CAUSAL INTERVENTION — Phase 4

Required deliverable (plan §8, §20). The decisive causal test: does *manipulating*
Bombness change jailbreak behavior?

**Verdict: STORY A, causally confirmed.** Ablating Bombness provably collapses the
concept readout yet leaves harmful ASR unchanged, while the refusal-ablation positive
control moves ASR at the same n. The semantic-identity confusion is real, decodable,
and causally manipulable — but **behaviorally epiphenomenal**. Refusal suppression is
the lever.

| | |
| --- | --- |
| Run | job 757931, `outputs/phase4_bombness_full_20260814_160640_757931/` |
| Harness | `scripts/phase4_bombness_intervention.py` (reuses LayerPatch + StrongREJECT) |
| Prompts | 42 test-split clearharm Doublespeak prompts (codeword/concept-disjoint holdout) |
| Intervention | project_out v_bomb at the query codeword over the write+carry band L8-18 |
| Outcome | StrongREJECT ≥ 0.5 (D2) |

---

## 1. Manipulation check (§8.3) — the ablation works, and specifically

Downstream Bombness readout at UNPATCHED layers (mean over 42 prompts), ablate − base:

| L20 | L24 | L28 | L31 |
| --- | --- | --- | --- |
| **−1.32** | **−1.30** | **−1.39** | **−1.62** |

Ablating v_bomb at L8-18 propagates to collapse the concept readout at every downstream
layer. The norm-matched random ablation leaves it unchanged. **The intervention removes
Bombness, and specifically** — so any behavioral null below is about a real manipulation,
not a dead hook.

## 2. Behavioral result (n=42)

| arm | ASR | refusal rate | mean StrongREJECT |
| --- | --- | --- | --- |
| ds_base | 0.238 | 0.643 | 0.220 |
| **ds_bomb_ablate** | **0.190** | **0.643** | 0.179 |
| ds_bomb_random | 0.238 | 0.667 | 0.211 |
| **ds_refusal_ablate** | **0.476** | **0.048** | 0.449 |

Paired contrasts (McNemar exact + paired bootstrap 10k):

| contrast | ΔASR | 95% CI | b/c | McNemar p |
| --- | --- | --- | --- | --- |
| **Bombness ablation vs base** (necessity) | **−0.048** | **[−0.143, +0.048]** | 1/3 | 0.625 |
| Bombness ablation vs random (specificity) | −0.048 | [−0.143, +0.048] | 1/3 | 0.625 |
| **Refusal ablation vs base** (positive control) | **+0.238** | **[+0.071, +0.405]** | 13/3 | 0.021 |

## 3. Reading

- **Bombness is not behaviorally necessary.** Removing it — an intervention that
  provably collapses the concept readout by ~1.3–1.6 — changes ASR by −0.05, CI
  [−0.14, +0.05], indistinguishable from a random ablation of the same norm. The
  **refusal rate is identical** (0.643 → 0.643): the ablation does not touch the
  refusal decision.
- **This is not an underpowered null.** At the same n=42 the refusal-ablation positive
  control moves ASR by +0.24 [+0.07, +0.41] (p=0.02) and collapses the refusal rate
  (0.643 → 0.048). The design detects effects of that magnitude; the Bombness null
  **excludes any effect larger than ~0.14 ASR**, well below the refusal effect.
- **Refusal is the lever.** The only arm that moves behavior is the one that suppresses
  refusal.

## 4. Convergent evidence — three independent lines, one conclusion (Story A)

| line | Bombness | Refusal |
| --- | --- | --- |
| **Decodability** (Gate 1) | AUC 0.997 | — |
| **Geometry** (Gate 1) | ⊥ refusal at codeword (cos 0.09) | — |
| **Prediction** (Phase 3) | AUC 0.59 (chance) | AUC 0.98 |
| **Causal necessity** (Phase 4) | ΔASR −0.05 [−0.14,+0.05] | ΔASR +0.24 [+0.07,+0.41] |

Doublespeak induces a strong, decodable, causally-manipulable semantic-identity
confusion (the codeword becomes internally BOMB-like) that is orthogonal to refusal,
does not predict which prompts jailbreak, and — when removed — does not change whether
they jailbreak. A separable refusal-suppressed state predicts and causally controls the
behavior. **Being placed in the adversarial latent identity is not the security failure.**

This extends *Prompt Injection as Role Confusion*: their result is that latent confusion
tracks attack success; ours is that a latent confusion axis can be real, decodable, and
causally manipulable while being behaviorally inert — the tracking is not automatic, and
the causal locus is a separate control state.

## 5. What this does and does NOT establish

**Establishes:** Bombness necessity is causally null under a strong, specific,
manipulation-check-verified intervention, at a power that excludes the refusal-magnitude
effect. Combined with the prediction null and the orthogonal geometry, the
representation≠behavior dissociation is now supported causally, not just observationally.

**Does NOT establish:**
- **Sufficiency** (§8.5): whether *adding* Bombness to a non-jailbreaking (e.g. neutral)
  prompt induces harm. Necessity ≠ sufficiency; the sufficiency arm is the natural next
  run (add α·v_bomb from neutral, ± refusal).
- ~~**The 2×2 interaction** (§8.6)~~ **DONE (run 757943):** all four cells from one run —
  ASR (bomb high/low × refusal intact/suppressed) = 0.214 / 0.214 / 0.571 / 0.571.
  main-effect Bombness **+0.00** [−0.07,+0.07]; main-effect refusal **+0.36** [+0.20,+0.50];
  **interaction +0.00** [−0.14,+0.14]. Bombness is inert whether refusal is intact OR
  suppressed — **Story B refuted**; Story A holds in its strongest form. Manipulation check
  fired (readout −1.3 to −1.6), so this is a verified null.
- **Robustness**: single dose (α=1, full ablation), single band (L8-18), single cohort
  (clearharm), single seed. The manipulation check confirms the ablation was strong; a
  dose/band/cohort sweep would harden the null.

## 6. Reproduce

```
# directions (CPU)
python -m src.probes.build_intervention_directions --run <extraction> \
  --band 8,...,31 --out outputs/phase4_directions/v_bomb_clearharm.pt
# intervention (SLURM/GPU)
sbatch --export=ALL,MODE=full,WITH_REFUSAL=1 slurm_scripts/run_phase4_bombness.slurm
# verdict (CPU)
python -m src.probes.analyze_phase4 --run <run_dir>
```
Artifacts: `raw.jsonl`, `gens.jsonl`, `phase4_analysis.json`, `DONE.json`.
