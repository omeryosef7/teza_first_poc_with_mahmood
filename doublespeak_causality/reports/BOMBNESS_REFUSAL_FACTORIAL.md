# BOMBNESS × REFUSAL 2×2 FACTORIAL — Phase 4 §8.6

Required deliverable (plan §20). The single most paper-valuable causal experiment (§8.6):
cross Bombness (high/low) with refusal (intact/suppressed) to test whether Bombness is
causal *only* when refusal is suppressed (Story B's gated version) — or inert regardless
(Story A).

**Verdict: no interaction. Bombness is behaviorally inert in BOTH refusal states — Story B
(gated causality) refuted; Story A holds in its strongest form.**

| | |
| --- | --- |
| Run | job 757943, `outputs/phase4_bombness_full_clearharm_20260814_164727_757943/` |
| Model | Llama-3.1-8B-Instruct | Prompts | 42 test-split clearharm Doublespeak |
| Cells | one run, four arms; orthogonal interventions (v_bomb ⊥ refusal, cos 0.06–0.15) |
| Manipulation check | ablation collapses Bombness readout −1.3 to −1.6 downstream (passed) |

---

## 1. The 2×2 (ASR)

Bombness is manipulated at the codeword (project_out v_bomb over L8–18); refusal at all
positions (Arditi ablation).

| | refusal **intact** | refusal **suppressed** |
| --- | --- | --- |
| **Bombness high** (baseline / +refusal-ablate) | 0.214 | 0.571 |
| **Bombness low** (bomb-ablate / bomb+refusal-ablate) | 0.214 | 0.571 |

Cells come from one run: `ds_base` (hi/intact), `ds_bomb_ablate` (lo/intact),
`ds_refusal_ablate` (hi/suppressed), `ds_bomb_and_refusal_ablate` (lo/suppressed).

## 2. Estimands (paired bootstrap 10k)

| effect | estimate | 95% CI |
| --- | --- | --- |
| **Main effect of Bombness** (removing it) | **+0.000** | [−0.071, +0.071] |
| **Main effect of refusal** (suppressing it) | **+0.357** | [+0.202, +0.500] |
| **Interaction** | **+0.000** | [−0.143, +0.143] |
| Bombness effect when refusal **intact** | +0.000 | [−0.071, +0.071] |
| Bombness effect when refusal **suppressed** | +0.000 | [−0.143, +0.143] |

## 3. Reading

- **Removing Bombness does nothing to ASR in either refusal state** — exactly 0.000 both
  when refusal is intact (0.214 = 0.214) and when it is suppressed (0.571 = 0.571).
- **The interaction is null** (+0.000, CI [−0.14, +0.14]): there is no refusal state in
  which Bombness becomes behaviorally relevant. Story B (Bombness causal only under
  suppressed refusal) is refuted.
- **Refusal is the entire behavioral axis** (main effect +0.357). Suppressing refusal moves
  ASR by ~0.36 regardless of Bombness level.
- The manipulation check confirms the Bombness ablation *did* collapse the concept readout
  (−1.3 to −1.6 at unpatched downstream layers), so this is a verified null, not a failed
  intervention.

## 4. Corroboration

The 2×2 agrees with the separate necessity (`BOMBNESS_CAUSAL_INTERVENTION.md`: ΔASR −0.05)
and sufficiency (ΔASR +0.05) runs. Across all three designs Bombness is neither necessary,
sufficient, nor gated; refusal is the sole causal lever (necessity +0.24, sufficiency
control +0.33, 2×2 main +0.36). Base-run ASR drift (0.214 here vs 0.238 in the necessity
run) is the known ~±0.03 greedy run-to-run drift (B15); the qualitative result is identical.

## 5. Reproduce

```
sbatch --export=ALL,MODE=full,COHORT=clearharm,WITH_REFUSAL=1,FACTORIAL=1 slurm_scripts/run_phase4_bombness.slurm
python -m src.probes.analyze_phase4 --run <run_dir>   # -> factorial_2x2 block
```
Independently recomputed from raw in `reports/ROLE_PROBE_FINAL_AUDIT_2026_08_14.md` (§1):
main_bomb +0.000, main_refusal +0.357, interaction +0.000 — all match.
