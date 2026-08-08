# §27 — Cross-Model Replication (staged X1–X5 gate)

**Central question:** is "refusal suppression, not concept remapping" general, or Llama-specific?
2nd model = **Qwen3-14B** (different family; the only viable non-Llama cached model with weights + repo infra;
Mistral/Gemma-4 are un-downloaded stubs). Thinking DISABLED for a clean behavioral readout (thinking-on
truncated CoT → confounded ASR; fixed via `--enable-thinking false`).

## X1 — does DS measurably alter ASR? ✅ PASS (modest)
`baseline_drift_...736516` (Qwen3-14B, v3b clearharm test n=42, thinking-off):
| condition | ASR | ntok | trunc |
|---|---|---|---|
| direct | 0.095 | 81 | 0.02 |
| **doublespeak** | **0.143** | 155 | 0.12 |
| neutral | 0.024 | 69 | 0.05 |
| benign(codeword) | 0.214 | 149 | 0.14 |

**DS ASR (0.143) > direct (0.095) > neutral (0.024)** → the Doublespeak attack raises harmful compliance on
Qwen3-14B (ΔASR vs direct ≈ +0.048). Qwen3-14B is more robust than Llama-3.1-8B (lower absolute ASR), but the
attack's behavioral signature replicates. gen-determinism=1.0; empty=0. **X1 PASS** (caveat: n=42, small
absolute effect — a fuller train/dev run would tighten the McNemar/CI).

## X2 — can a refusal direction be independently fit + validated on Qwen3? ✅ PASS
`build_refusal_direction_llama.py` (diff-of-means, thinking-off) fit Qwen3-14B refusal dirs at L16,20,24,28,32
(-> outputs/refusal_qwen3/); `validate_refusal_directions.py` (`refval_clearharm_...736569`, eval n=20) gives
**valid 5/5, best L32 (score 1.3), invalid=[]** — the ablation+induction gate passes at EVERY swept layer.
So the refusal representation exists and is causally manipulable on Qwen3-14B, just as on Llama (broad validated
band L16-32 vs Llama's L13-20/24/28/29). **X2 PASS** => the mechanism, not just the attack, is present cross-family.

## X3 — does DS suppress the validated Qwen3 refusal projection? ✅ PASS (strong)
`refproj_clearharm_...736629` (Qwen3-14B, thinking-off, test n=42): DS collapses the refusal projection vs
direct at EVERY validated layer — L16 9.5→8.4, L20 19.8→0.9, L24 55.9→21.9, L28 137→64, L32 214→55 (gap
direct−ds large-positive everywhere). **X3 PASS**: the Doublespeak attack suppresses the refusal representation
on Qwen3-14B, exactly as on Llama. (Raw pooled projections; the direct≫ds gap is unambiguous.)

## X4–X5 — PENDING
- **X4 (next):** on Qwen3, does refusal ABLATION raise harmful behavior AND refusal RESTORATION reduce DS ASR?
  (reuse the ablation/restoration recipe with the Qwen3 validated dir, thinking-off.)
- **X5:** does the concept readout again fail to explain behavior on Qwen3?

## Cross-model verdict so far
X1 ✅ (attack raises ASR) · X2 ✅ (refusal dir fits+validates, 5/5) · X3 ✅ (DS suppresses it). Three of five
gates PASS → "refusal-suppression, not concept remapping" is **generalizing to a second family (Qwen3), not
Llama-specific.** X4 (causal ablation/restoration) + X5 (concept fails) remain.
- **X3 (next):** does DS suppress the validated Qwen3 refusal projection (vs direct)? Reuse the projection
  readout with the Qwen3 dir (e.g. L24/L32) + Qwen3 model, thinking-off.
- **X4:** refusal ablation ↑harm AND restoration ↓DS on Qwen3. **X5:** concept readout fails to explain behavior.
- **X2:** independently fit + validate a refusal direction on Qwen3-14B (40 layers) — reuse
  `build_refusal_direction_llama.py` / `validate_refusal_directions.py`, generalized to the model's layer count.
- **X3:** does DS suppress that validated direction? **X4:** refusal ablation ↑harm AND restoration ↓DS.
- **X5:** concept readout again fails to explain behavior.
Only spend compute as each gate passes.
