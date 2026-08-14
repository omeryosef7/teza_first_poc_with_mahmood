# CROSS-MODEL PROBE REPLICATION (Phi-4-mini, Qwen3-14B) — Phase 7/8

Required deliverable slot (plan §20 `PHI_CONCEPT_COMPLETION.md`). The plan's original Phi
item (B16) was the Phi *concept-ablation* behavioral arm; this sprint instead executed the
**contextual-Bombness probe replication** on Phi-4-mini-reasoning and Qwen3-14B, which is
the role-probe analogue and a stronger cross-family test of the representation result.
This report covers what was done and what remains.

**Result: the Bombness probe (Gate 1) + geometry replicate on THREE model families.**

---

## 1. Cross-model Gate 1

Same corpus construction and pipeline (`capture_components` / `resolve_positions` /
`gate1_eval`), no per-model code — only `MODEL`/`QUANTIZE` parameters.

| model | hidden | run | Gate 1 holdout AUC | max control | cos(Bombness, refusal) |
| --- | --- | --- | --- | --- | --- |
| Llama-3.1-8B-Instruct | 4096 | 757886 | 0.997 [0.990,1.000] | 0.587 | 0.06–0.15 |
| Phi-4-mini-reasoning | 3072 | 758022 | 0.985 [0.967,0.998] | 0.562 | 0.01–0.04 |
| Qwen3-14B (8-bit) | 5120 | 758030 | 0.999 [0.995,1.000] | 0.591 | 0.03–0.12 |

On every model: contextual Bombness is decodable at the query codeword with all trivial
controls near chance (token-identity exactly 0.500 by matched-pair design, position/length
~0.56–0.59), and the Bombness direction is **orthogonal to that model's refusal direction**
(existing `refusal_phi` / `refusal_qwen3` artifacts). The decodable, refusal-orthogonal
semantic-remapping representation is a **cross-family property**, not a Llama quirk.

## 2. Engineering notes

- The **B19 preflight relaxation** was essential: the corpus `codeword_occurrences_templated`
  spans are Llama-tokenized and match no other model, but `resolve_positions` locates the
  codeword in each model's own tokenization (correct by construction), so the soft
  corpus-span check reports 0.0 and the hard check passes.
- Qwen3-14B (~28GB) used 8-bit quantization (`--quantize 8bit`); acceptable for reading
  activations (the prior sprint studied quantization robustness).
- Phi-4-mini and Qwen3 are thinking models; `apply_template(add_generation_prompt=True)`
  handles their templates, and the codeword position (in the user turn) is unaffected by
  the `<think>` region.

## 3. What is NOT established (honest scope)

- **Phi/Qwen behavioral Phase 3/4** (does refusal predict / cause jailbreak there, and is
  Bombness epiphenomenal?) is **not run** — it needs model-specific doublespeak generations
  scored by StrongREJECT on the v3 corpus, which do not exist (the existing Phi/Qwen screens
  are a different, curated cohort). So Story A's **representation** half is cross-family
  (3 models); its **behavioral causal** half is the audited Llama result.
- The original **B16 Phi concept-ablation** behavioral arm (count-matched random control on
  Phi) is likewise a behavioral experiment that remains open.

## 4. Next steps to complete the cross-family behavioral claim

1. Generate Phi/Qwen doublespeak completions on the v3 test split, StrongREJECT-scored →
   enables cross-model Phase 3 (dual-state prediction).
2. Build Phi/Qwen v_bomb directions (already have the extractions) + run the Phase-4
   intervention harness (parameterize the harness by model; expect the generated-cohort
   manipulation-check caveat, E22 — smoke the manip check first, calibrate on-manifold).
3. Compare normalized depth (not raw layer): the best Bombness layer is L11 (Llama, 32L),
   L10 (Phi, 32L), L15 (Qwen, 40L) — all early-mid, ~0.3–0.4 normalized depth.

## 5. Reproduce

```
sbatch --export=ALL,MODE=full,COHORT=clearharm,MODEL=microsoft/Phi-4-mini-reasoning slurm_scripts/run_probe_extract.slurm
sbatch --export=ALL,MODE=full,COHORT=clearharm,MODEL=Qwen/Qwen3-14B,QUANTIZE=8bit slurm_scripts/run_probe_extract.slurm
python -m src.probes.gate1_eval --run <run_dir> --position codeword_last
```
