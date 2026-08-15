# BOMBNESS PROBE VALIDATION — Gate 1

Required deliverable (plan §20). Reports the Gate-1 validity verdict for the
contextual-identity ("Bombness") probe on Llama-3.1-8B-Instruct.

**Verdict: GATE 1 PASSES** — contextual Bombness is a real, cleanly decodable
latent variable that generalizes across held-out codewords and is not explained by
any trivial surface confound.

| | |
| --- | --- |
| Model | meta-llama/Llama-3.1-8B-Instruct (bf16, sdpa) |
| Extraction | job 757886, `outputs/probe_bombness_full_clearharm_20260814_150624_757886/` |
| Corpus | `clearharm_doublespeak_v3.json` (leakage-0), clearharm cohort |
| Space | `resid_post` == `hidden_states[L+1]` (D1 raw residual) |
| Probe | L2 logistic, C on dev; diff-of-means for directions (manifest D3) |
| n | train 85 ex / dev 43 / **test (holdout) 42** — codeword- & concept-disjoint |
| Contrast | doublespeak (codeword→harmful, label 1) vs benign (same codeword→benign, label 0) |

---

## 1. Held-out discrimination (criterion 1)

Fit on train, layer/C selected on **dev only**, evaluated once on the frozen test
holdout.

| position | selected layer | holdout AUC | 95% CI | dev AUC |
| --- | --- | --- | --- | --- |
| **query codeword** (`codeword_last`) | L11 | **0.997** | [0.990, 1.000] | 0.9995 |
| **decision token** (`final_prompt`) | L11 | **0.964** | [0.930, 0.993] | — |

dev and holdout agree (0.9995 vs 0.997) — no dev/holdout collapse (criterion 4).

## 2. Transfer to held-out codewords (criterion 2)

**The holdout IS a cross-codeword generalization test.** The clearharm test split has
**22 codewords with zero overlap** with the 27 train codewords (and concepts are
cluster-disjoint too). So holdout AUC 0.997 already demonstrates the probe generalizes
to codewords it never saw during training — it reads the *binding relation*, not
memorized codeword→topic associations. This is the control that rules out the
"content-of-demos" confound (execution log E14).

(The CARROT-specific named test did not run: CARROT is a single dev example — 2 items,
below the n≥4 transfer threshold. It is subsumed by the codeword-disjoint holdout.)

## 3. Trivial controls cannot explain it (criterion 3)

All at the selected (L11, codeword_last), on the holdout:

| control | AUC | reading |
| --- | --- | --- |
| label-shuffle (10-seed mean) | 0.465 | chance — probe learns nothing from permuted labels |
| random direction (10-seed mean) | 0.529 | chance |
| **position-only** (codeword token index) | 0.578 | weak — matches the offline preview (0.557) |
| **length-only** (sequence length) | 0.587 | weak — doublespeak/benign length-matched by corpus design |
| **token-identity** (codeword token id) | **0.500** | exactly chance **by construction**: within a matched pair, doublespeak and benign share the same codeword, so token-id is perfectly balanced across labels |

Max control AUC **0.587**, far below the probe's 0.997 (margin 0.41). The probe is not
riding length, position, or surface token identity.

## 4. Geometry vs the validated refusal direction (criterion 5)

cos(Bombness diff-of-means direction, validated refusal_L18) — refusal_L18 is
`hidden_states[19]`, the same D1 space:

| position | cos vs refusal_L18 |
| --- | --- |
| **query codeword** (L18) | **+0.091** — essentially orthogonal |
| decision token (L18) | +0.468 — moderate alignment |

Per-layer |cos| at the codeword position stays **0.06–0.15** across all layers.

**Interpretation (the sprint-relevant point).** At the *codeword* position, Bombness
is a clean semantic-identity signal **orthogonal to refusal** — exactly as §5.3
predicts (Bombness aligns with concept identity, not with the refusal/compliance
axis). By the *decision token*, the representation has integrated the
refusal decision, so Bombness-at-decision partially entangles with refusal (0.47).
This is the geometry the sprint's central question needs: a strong, refusal-orthogonal
semantic state at the codeword, whose behavioral causality is now the open question.

## 5. What this does and does NOT establish

**Establishes:** the model computes a real, robustly decodable representation of "this
codeword is (contextually) bound to a harmful concept." It generalizes to unseen
codewords, survives every trivial control, and is geometrically distinct from the
refusal axis at the codeword position. This confirms and sharpens §1.1 (the
concept-remapping representation is real) with a controlled linear probe in the
role-confusion tradition.

**Does NOT establish:** that Bombness *causes* jailbreak behavior. A probe is not a
mechanism (plan §3.11). AUC 0.997 measures decodability, not behavioral causality —
and the sprint's established prior (§1.2) is that the concept representation is
largely epiphenomenal for behavior while refusal suppression is the lever. Whether
this strong, refusal-orthogonal Bombness signal is behaviorally causal is exactly what
Phases 3–4 (dual-probe prediction; Bombness causal intervention; the 2×2 Bombness ×
refusal factorial) test.

## 6. Reproduce

```
# extraction (SLURM/GPU)
sbatch --export=ALL,MODE=full,COHORT=clearharm slurm_scripts/run_probe_extract.slurm
# gate-1 (CPU)
python -m src.probes.gate1_eval --run <run_dir> --position codeword_last
python -m src.probes.gate1_eval --run <run_dir> --position final_prompt
```

Artifacts in the run dir: `acts.npy`, `items.jsonl`, `gate1_codeword_last.json`,
`gate1_final_prompt.json`, `geometry_vs_refusal.json`, `RUNMETA.json`, `DONE.json`.

## 6b. Space-choice robustness (normalized mid-block, upstream's space) — run 758099

We fit the headline probe in the raw post-block residual (D1) so Phase-4 steering is
well-defined. As a robustness check (§A3.1) we re-extracted in **upstream's own space** —
`post_attention_layernorm` output (RMSNorm-normalized mid-block = upstream's
`all_pre_mlp_hidden_states`) — and refit Gate 1:

| space | holdout AUC | layer | max control |
| --- | --- | --- | --- |
| raw post-block residual (D1, headline) | 0.997 [0.990,1.000] | L11 | 0.587 |
| **normalized mid-block (upstream)** | **0.994 [0.984,1.000]** | L7 | 0.587 |

Bombness decodes essentially identically in both (controls near chance, token-id 0.500 in
both). **The Gate-1 result is not an artifact of the residual-space choice**; it holds in
upstream's own space too (best layer slightly earlier, L7 vs L11, consistent with the
mid-block being one sub-block upstream).

## 7. Limitations / next

- Single cohort (clearharm) for the headline; the generated cohort is a held-out
  replication (§9 synthesis) and Phi/Qwen are cross-family replications.
- Normalized-space robustness arm: **DONE** (§6b, decodes at 0.994).
- Bombness vs Refusalness *predictive* comparison (which predicts DS success) is
  Phase 3; causal intervention is Phase 4. Gate 1 is the precondition, now met.
