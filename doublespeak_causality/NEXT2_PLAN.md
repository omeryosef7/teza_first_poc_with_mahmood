# NEXT2 — Ranked follow-up plan (low-hanging, high-value + new techniques)

Extends the completed sprint (`HANDOFF.md`). From a 4-lens design panel + synthesis. Env: L40S n-801..805,t-806; `poc_stage2`; forced_choice. Findings → `NEXT2_FINDINGS.md`.

## Status
- **N1 depth-invariance** — ✅ DONE (free): IE_state inert at ALL 32 layers, DE_context flat, 4/4 pairs.
- **#5 cross-arch Qwen3-14B** — RUNNING (695089); Gemma-4 not cached (skipped). Thinking-model gate may fail → clean documented negative.

## Ranked items
1. **#1 Depth profile overlaid on TOCTOU depth-gate** (CPU, free). Unify S2/S3 depth-invariance with S4 depth-gating: does context switch on at the same depth the refusal check stops firing? Reuse per-layer transplant JSONs + toctou_summary. → extend `NEXT2_FINDINGS.md` N1 with the TOCTOU per-timing overlay.
2. **#2 TOCTOU cell-D specificity controls** (small code + ~1hr GPU). Close the S4 caveat: run rand/orth concept controls through cell D (not just B). `45_toctou_factorial.py`: `rand_c`/`orth_c` already built + wired to B; add the 2 emit lines to D + a reducer block. Report D-main vs D-control MALICIOUS. **Unblocks #6.**
3. **#3 Positive-control-gated, layer-scanned patchscope rescue** (small GPU <20min). Fix `44`'s fixed-late-layer patchscope (the dropped ps_concept=0): reuse `07.PatchscopeDecoder` + its layer-scan positive control (07:110-117). Payoff: (a) directly replicate the paper's "CARROT decodes as BOMB via Patchscopes" with a PASSING positive control; (b) confound-free cross-check of IE_state=0 (demo-free inspection prompt).
4. **#4 Attribution-patching map** (new technique; small GPU <20min; ~150-line `47_attribution_patching.py`). Turn S3's "distributed" into a layer×context-position map in one backward pass; validate top-k cells with true LayerPatch. Localizes WHERE the DS context installs the reading.
5. **#5 Cross-architecture** (medium GPU). Qwen3-14B (running) ∥ (Gemma deferred, not cached). MODEL override only. Report per-model, no pooling; thinking-model gate-fail = documented negative.
6. **#6 TOCTOU generalization** to grenade + chlorine (medium GPU; after #2). Reuse concept-agnostic L18 refusal `.pt` via `SKIP_REFUSAL=1` + per-pair dirs; B5 job-isolation. Per-pair INTERACTION+CI, no pooling; exclude pistol (weakest hijack, underpowered).
7. **#7 d_Direct dose-response reframe** (small GPU). `MODE=dose ALPHAS=1,2,4,8` — reframe "weak +0.03" (B4) as small-but-monotone concept-specific dose; formally decouple the transplant conclusion from d_Direct magnitude.

**Deferred:** forward DemoStateSwap sufficiency (inject DS demo-KV into Neutral receiver); superposition project-out probe; n=60 tighter IE_state equivalence; per-head (eager) patching; true KV-cache splice. Also **N2 cumulative multi-layer state replacement** (does replacing the codeword state at a full layer window ever install? decisive context-only test) — cheap, slot after #2/#3.

## Execution order
Start now: **N1-overlay (#1, free)**, **#2 cell-D (unblocks #6)**, **#5 Qwen3 (running)**. Then small-GPU wave: **#3 patchscope**, **#4 attribution**, **#7 dose**. Then **#6** (after #2 lands). Keep ≤6 concurrent L40S jobs; job-isolate captures (B5).
