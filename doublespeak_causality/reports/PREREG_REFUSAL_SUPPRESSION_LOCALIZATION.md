# PRE-REGISTRATION — §3 Refusal-suppression causal localization (Master Plan V2)

**Registered 2026-08-07 (loop iteration 1, before any run). Estimand and design are frozen here; any change
after seeing results is recorded as a separate correction (§0.1 / §37).**

## Hypothesis
There exists a component × layer-window × prompt-position at which patching the Doublespeak (DS) activation
back to the matched **Direct-harmful** donor **restores the refusal representation** at the decision token —
i.e. a causal *origin* of the refusal suppression that is distinct from the (behaviorally inert) concept write.
Null-compatible alternative: suppression is fully distributed and no single component/window survives
specificity (Gate A FAIL → characterize as distributed).

## Primary estimand (representational)
Per (split, layer-window W, component C, position-set P):
`necessity(W,C,P) = mean_i [ refproj_dec(DS) − refproj_dec( DS with C at positions P over layers W ← Direct donor ) ]`
where `refproj_dec` = projection of the **decision-token** residual onto the **validated** per-layer refusal
direction (readout layer chosen from the P7-validated set **{L13–L20, L24, L28, L29}**; anchor **L18**, never
L9). Positive = intervention **restored** refusal. Paired within-item (matched DS/Direct), Wilcoxon signed-rank.

## Secondary / confirmatory estimand (behavioral)
For any component that passes necessity with specificity on train+dev: `ΔASR` during generation (StrongREJECT
MALICIOUS ≥ 0.25), paired exact McNemar, on the **locked test** — the full confirmatory arm, not best-cell-only.

## Dataset / split
Discovery on **v3 clearharm** train (n=85) + dev (n=43); locked-test confirmation on v3 clearharm test (n=42).
Cohort **generated** reported separately (not pooled). v1/v2 only for historical comparison. (Falls back to
v1-clearharm 44/42 if a v3 donor cell is not yet demo-complete — but §1.3 says v3.1 benign demos are complete,
so v3 is preferred.) **≥20 examples per cell enforced**; any cell < 20 flagged underpowered, never pooled.

## Intervention (Direct↔DS component patch)
- **Components C:** `resid_pre`, `attn_out`, `mlp_out`, `resid_post` (via `pair_common.SubmodulePatch` /
  `ComponentOutSwap` / `ComponentCapture` — all batch-dim-asserted).
- **Layer windows W (coarse first):** L0–7, L8–12, L13–16, L17–20, L21–24, L25–28, L29–31; refine to single
  layers only inside an active band.
- **Position groups P:** A system · B demo-concept · C demo-codeword · D demo-answer · E separators/template ·
  F query-codeword · G query-instruction · H decision token. (Position resolver reused from
  `phase3_demo_neutralize.py` / `phase6_mlp_causal.py`.)
- **Direction of patch:** replace DS activation with the matched **Direct** donor (necessity/restoration). A
  later sufficiency arm (insert DS activation into Direct) is a separate pre-registration.

## Controls (mandatory, §0.4)
1. **Self-swap / identity** (patch DS with its own captured value) → must be **exactly 0.0** (locality).
2. **α=0 / no-op anchor** where applicable.
3. **Firing / movability control:** an all-position or whole-window patch must move `refproj_dec` far from 0
   (proves the hook fires and the readout is movable) — analogous to P3's all-query-edges control.
4. **Specificity:** count-matched **random-position** donor (same |P|, non-target positions) and, for the
   band claim, a matched **non-candidate window**. A component "matters specifically" only if it beats these.
5. Readout uses a **validated** refusal direction only; a run that reads at an unvalidated layer is invalid.

## Significance test
Wilcoxon signed-rank, **Holm over the actual family tested** (the W×C×P grid, per split). Report per cell:
n, effect, bootstrap 95% CI (fixed seed, paired diffs saved), and **MDE / post-hoc power beside every
non-significant cell**. Behavioral confirmation: exact McNemar + bootstrap CI on locked test.

## Pass/fail gate (Gate A, Master Plan §32)
- **PASS:** ≥1 (C,W,P) cell restores `refproj_dec` significantly (Holm), beats both specificity controls, and
  **replicates on the locked test**.
- **STRONG PASS:** the same cell also lowers ASR (behavioral necessity) with the random control null.
- **FAIL:** nothing survives specificity → stop chasing sparse components; report distributed suppression and
  pivot to §5 (demo-position content decomposition) as the causal handle.

## Implementation path (reuse — no new primitives expected)
Generalize `scripts/phase_write_refusal_interaction.py` (already: Direct↔DS component patch + decision-token
refusal projection + FC `p_concept` firing control) from its fixed L8–11/`mlp_out`/demo-position cell to the
full **W × C × P** grid, swapping the readout to a **validated-layer** refusal direction and adding the
random-position + non-candidate-window specificity controls and the whole-window firing control. Position
resolution and the Direct-donor capture reuse `phase6_mlp_causal.py` / `phase3_demo_neutralize.py`. Endpoint
projection reuses `phase_refusal_projection.py` with `outputs/refusal_alllayers/refusal_direction_llama_L{val}`.

## Engineering (Appendix A)
`poc_stage2`; patching job → ≥23 GB VRAM allowlist (backfill idle 3090/a5000, ≥2 h walltime for cold load);
**eager attention** when patching `attn_out`; RUNMETA first / DONE last; `--add-special-tokens false`; ≤6
parallel, ≤2/node, `--nodelist` not `--exclude`; smoke (DSN=2, self-swap=0 gate) before the full run.

## Next-fire deliverable
Implement the harness `scripts/phase_refusal_suppression_localize.py` + wrapper
`slurm/run_refusal_localize.sh`, unit-test the hook (self-swap=0, firing control moves), smoke it, then launch
the coarse W×C×P grid on v3-clearharm train+dev.
