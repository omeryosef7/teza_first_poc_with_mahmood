# Next Meeting Brief — Mahmood

**Status**: SKELETON — populate with actual results before meeting

---

## Progress Since Last Meeting

### Completed (Stage 4.5B)
- LLM onset annotation pipeline implemented (o4-mini two-pass consensus)
- Quality gate: TBD (PASS/FAIL)
- Annotation rate: TBD / 42 examples
- Event-aligned dynamics analysis: TBD

### In Progress (Stage 4.6)
- Controlled ablation: 4 goals × 5 conditions = 20 generations
- Puzzle-wrapper ablation (A=full, B=50%, C=25%, D=none) + thinking mode (E=off)
- SLURM jobs ready; pending GPU run

---

## Key Results to Discuss

### Stage 4 (frozen, confirmed)
- Layer-22 divergence: Hedges' g = 1.256 (strong effect, N=42)
- Refusal direction projection separates success/failure traces at Layer 22

### Stage 4.5B (LLM annotation — exploratory)
- Onset annotation rate: TBD%
- Two-pass consensus rate: TBD%
- Onset-aligned dynamics: TBD

### Stage 4.6 (ablation — pending GPU)
- Puzzle length effect (A vs D): TBD
- Thinking mode effect (A vs E): TBD

---

## Open Questions for Mahmood

1. Is the LLM onset annotation quality sufficient for the thesis, given human annotation is pending?
2. For Stage 4.6: should we expand beyond 4 source prompts? (Current: 1 per goal, deterministic selection)
3. Thesis writing timeline: which sections should be drafted before ablation results?

---

## Next Steps

1. Run Stage 4.5B annotation pipeline: `python -m poc_stage4_5.llm_annotate_harmful_interaction --all`
2. Run Stage 4.6 smoke: `sbatch slurm_scripts/stage4_6_controlled_ablation_smoke.slurm`
3. If smoke passes: `sbatch slurm_scripts/stage4_6_controlled_ablation_full.slurm`
4. Populate this brief with actual numbers from outputs
