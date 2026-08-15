# D3 — Intervention-scope-matched activation control (Phase 6 / gap-matrix §D3)

Closes the pre-registered but previously-deferred D3 control (ASYMMETRY_GAP_MATRIX §D3;
"NOT RUN" in ASYMMETRY_FINAL_SYNTHESIS §caveats / CONTINUOUS_VS_DISCRETE §202-207).

> **Provenance / independent reproduction.** This control was run *concurrently by two
> sessions* on 2026-08-15. A parallel session resolved it first (commits `f2384ceb` /
> `9bed50de`, ~13:02) and annotated the framing docs; this session built the reusable
> tooling (`pair_common.SinglePositionProjectOut` + 4 unit tests, `run_d3_activation_scope.slurm`,
> `analyze_d3_scope.py`) and ran an independent replication (runs 758290/1/2). **Both agree to
> the decimal**, which is the strongest possible confirmation of a reviewer-critical control.
> The duplicate GPU was unintended (the two sessions' commits interleaved on one branch); noted
> for honesty.

**Question.** The published control hierarchy is
`activation intervention > continuous soft-prompt > discrete GCG`. But the activation
arm ablates the refusal axis at **every layer, every position, every decode step**
(`AllPositionProjectOutMultiLayer`), whereas a token attack touches **one layer, one
position**. Is the activation advantage the *medium*, or just the *scope*?

**Design.** The SAME refusal-direction activation ablation (α=1.0, L18 axis) run at three
narrowing scopes on the held-out `test` split (n=42, nothing selected on it for the
activation arm), with a norm-matched random control at each scope:

| scope | what is ablated |
| --- | --- |
| `all_layers` | every layer / every position / every decode step (Arditi ablation) |
| `single_layer` | one layer (L18) / all positions / all steps |
| `decision` | one layer (L18) / **decision position only / prefill only** — scope-matched to a token attack |

New code: `pair_common.SinglePositionProjectOut` (4 GPU-free unit tests). Runs 758290 /
758291 / 758292.

## Result — refusal-reduction (base_refusal − ablated_refusal) = attack strength

| scope | clearharm gain | existing gain | random (both) | proj. separation |
| --- | --- | --- | --- | --- |
| `all_layers` | **+0.81** (0.88→0.07) | **+0.57** (0.88→0.31) | +0.00 | 0.17 / 0.22 |
| `single_layer` L18 | +0.45 (0.88→0.43) | +0.43 (0.88→0.45) | +0.00 | 0.17 / 0.22 |
| `decision` L18 | **+0.02** (0.88→0.86) | **+0.00** (0.88→0.88) | +0.00 | 0.17 / 0.22 |

**The scope-matched (`decision`) activation attack retains 0–3 % of the full-scope
refusal-reduction** (+0.02/+0.00 vs +0.81/+0.57). Narrowing from all-layer to single-layer
already halves it; narrowing to a single position erases it.

## Reading

1. **The "activation ≫ token" advantage is largely SCOPE, not medium.** An activation
   intervention restricted to the same budget a token attack has (one layer, one position)
   barely dents refusal (gain ≤ 0.02). The published activation dominance comes
   overwhelmingly from operating at every layer / every position / every decode step —
   a budget no input-space attack (continuous or discrete) can match. This is the R3/D3
   confound made quantitative, exactly as pre-registered.

2. **Not a direction/medium artifact.** The held-out projection separation is identical
   across scopes (0.17 clearharm / 0.22 existing) — the refusal axis is equally readable
   regardless of ablation scope; only the *behavioral* effect collapses with scope. And
   every random control is +0.00, so the effect is specific at every scope.

3. **Consequence for the asymmetry paper.** The headline
   `activation > continuous > discrete` hierarchy must be read as *partly a statement about
   intervention scope*, not purely about the reachability of the activation vs input
   medium. A fair medium comparison holds scope fixed; when scope is matched to the input
   attack, the activation arm loses its advantage. This strengthens, not weakens, the
   paper's honesty: the token-space "unreachability" is in large part a scope limitation.

## Limitations

- Refusal readout is keyword-based (`kw_refusal`), the same behavioral proxy the existing
  activation rung used; StrongREJECT ASR not re-scored here (the scope effect is on
  refusal rate, which is unambiguous: 0.88→0.86 vs 0.88→0.07).
- `test` split (held-out for the activation arm; α fixed, nothing tuned). The full
  cross-medium Figure A on the `dev` confirmatory split (soft-prompt + GCG re-run at
  budget_rel=0.10 × seeds 42/43/44) is the remaining §10.1/§10.2 piece.
- Single model (Llama), single axis layer (L18).

## Reproduce

```
for sc in all_layers single_layer decision; do
  sbatch --export=ALL,SCOPE=$sc,LAYER=18,SPLIT=test,VALN=0 slurm_scripts/run_d3_activation_scope.slurm
done
python scripts/analyze_d3_scope.py --runs <all_layers_dir> <single_layer_dir> <decision_dir> \
   --family clearharm --layer 18 --out reports/D3_SCOPE_COMPARISON.json
```
