# Third-Family Replication — Phi-4-mini-reasoning (Q6 / Phase 5)

Goal: test whether the paper's **representation ≠ behavior** dissociation replicates on a third
model family (beyond Llama-3.1-8B and Qwen3-14B): the refusal/concept axes are linearly present &
separable in activations, but do NOT convert into a specific behavioral/optimization lever.

Model: `microsoft/Phi-4-mini-reasoning` (~3.8B, 32 layers, bf16). Benches reused verbatim from
the Llama/Qwen pipeline (model-agnostic prompts) → apples-to-apples cross-family comparison.

## X2 — refusal direction: representation strong, behavioral validity weak (DONE, job 744772)
Diff-of-means harmful(=direct) vs harmless(=neutral) on Phi's own activations, `pair_carrot_bomb.json`
(n_harmful=60, n_harmless=20), captured at `hidden_states[L+1]`. Induced-refusal `--validate`
(ablate + induce gains, 20 harmful / 20 neutral, alpha=8).

| layer | separation | ablate_gain | induce_gain | validate score | valid? |
|---|---|---|---|---|---|
| L12 | +0.337 | −0.250 | +0.000 | −0.250 | no |
| **L14** | **+0.513** | **+0.100** | **+0.100** | **+0.200** | **YES (selected)** |
| L16 | +0.535 | +0.100 | +0.000 | +0.100 | no |
| L18 | +0.503 | +0.100 | +0.000 | +0.100 | no |
| L20 | +0.532 | −0.050 | +0.000 | −0.050 | no |
| L22 | +0.579 | −0.050 | +0.000 | −0.050 | no |

**Read:** the refusal direction is **strongly linearly separable at every layer** (sep 0.50–0.58 for
L14–L22), yet only **one layer (L14)** passes the behavioral ablate+induce validation and even there
the gains are small (+0.10/+0.10). Representation presence ≫ behavioral potency — the same signature
found on Llama, now on a third family. (SELECTED = L14, used as the refusal axis downstream.)

## X1 + X3 — behavioral drift & refusal-ablation dose (RUNNING, job 744801)
`phase_behav_refusal.py` on Phi, bench `behavioral_v3b/beh_clearharm.json`, refusal-pt = L14 (validated),
alphas 0.0/0.5/1.0, splits train+test, StrongREJECT-judged. Produces (a) baseline jailbreak labels
(alpha=0) for the X5 AUC join, and (b) the refusal-necessity dose-response vs a norm-matched random
control. _Results pending._

## X5 — concept vs refusal readout AUC (PENDING)
`phase_x5_concept_qwen3.py` (model-generic) with `--model Phi-4-mini-reasoning --refusal-dir
outputs/refusal_phi --beh <X1 run>`: fit a diff-of-means concept direction on Phi, then compare
concept-proj AUC vs refusal-proj AUC for predicting jailbreak on held-out doublespeak items, plus
geometry cos(concept, refusal). Endpoint mirrors Qwen X5: concept AUC ≈ 0.5 (fails), refusal AUC > 0.5.
_Pending X1 behavioral labels._
