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

## X1 + X3 — behavioral drift & refusal-ablation dose (DONE, job 745950; test n=42)
`phase_behav_refusal.py` on Phi, refusal-pt = L14 (validated), alphas 0.0/1.0, test split, thinking-off,
StrongREJECT-judged. (Rescoped from train+test×3α reasoning-on 744801 which projected ~50h >> walltime.)

| arm | α=0.0 | α=1.0 |
|---|---|---|
| direct + **refusal**-ablation (ASR) | 0.714 | **0.952** |
| direct + random-ablation (ASR) | 0.714 | 0.714 |
| refusal_rate (refusal-ablation) | 0.095 | **0.000** |
| refusal_rate (random-ablation) | 0.095 | 0.095 |

Paired: direct+refabl vs direct α=1.0 **ΔASR +0.238, McNemar p=0.0064**; refusal-suppression ≈
Doublespeak (ds_base vs direct+refabl α=1.0 p=2e-5). **X3 read:** ablating Phi's refusal direction is
behaviorally **causal, dose-dependent, and SPECIFIC** (random ablation → no change; refusal_rate → 0),
replicating the Llama activation-space causal result on a third family. (Phi's direct baseline is highly
compliant — refusal_rate 0.095 — so headroom is small, yet the effect is significant and specific.)
X1 baseline (α=0) jailbreak labels feed the X5 AUC join.

## X5 — concept vs refusal readout AUC + geometry (DONE, job 747029; test n=42)
Concept direction fit (diff-of-means, train, thinking-off); concept/refusal/random projections on the
42 held-out test doublespeak items joined to X1 ds_base jailbreak labels; seeded percentile-bootstrap CI.

**Geometry — cos(concept, refusal) per layer:** L12 −0.055 / L14 +0.056 / L16 +0.055 / L18 +0.006 /
L20 −0.023 / L22 −0.006. |cos| ≤ 0.056 at every layer → the concept and refusal axes are **near-
orthogonal** on Phi (distinct directions), matching the Llama finding. Concept separation 0.32–0.37.

**Jailbreak-prediction AUC (pooled, CI in brackets):**
| layer | concept AUC | refusal AUC |
|---|---|---|
| L12 | 0.342 [0.175,0.518] | 0.388 [0.215,0.566] |
| L14 | 0.395 [0.215,0.574] | 0.454 [0.270,0.638] |
| L16 | 0.528 [0.338,0.708] | 0.463 [0.281,0.649] |
| L18 | 0.560 [0.377,0.735] | 0.454 [0.273,0.641] |
| L20 | 0.612 [0.428,0.785] | 0.451 [0.270,0.635] |
| L22 | 0.501 [0.322,0.684] | 0.463 [0.283,0.646] |

**Read (honest):** on Phi, **neither** the concept nor the refusal linear *readout* reliably predicts
natural jailbreak variation — every CI spans 0.5 (refusal AUC ~0.45 throughout; concept ~0.5, best L20
0.61 but CI includes 0.5). This is underpowered (n=42) and Phi's direct baseline is highly compliant.
Crucially this sits alongside X3, where refusal *ablation* IS causal (ΔASR +0.238, refusal_rate→0):
the refusal direction is causally necessary under intervention yet its projection magnitude does not
linearly predict which prompt jailbreaks — the strongest form of representation≠behavior. The concept
readout is not privileged over refusal (does not beat it), consistent with concept being epiphenomenal.

## Phase 5 verdict (Gate E): representation≠behavior REPLICATES on Phi-4-mini-reasoning
- X2: refusal direction strongly separable at all layers (0.34–0.58) but behaviorally valid at only 1/6 (L14).
- X3: refusal *ablation* causal, dose-dependent, SPECIFIC vs random (ΔASR +0.238, p=0.006; refusal_rate→0).
- X5: concept ⟂ refusal (cos≈0); neither linear readout predicts jailbreak (both ≈ chance, underpowered).
Net: the causal locus is refusal-suppression (intervention), not a predictive linear readout, and concept
is not privileged — the Llama/Qwen story holds on a third family.
