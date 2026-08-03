# reports/PHASE6_MLP.md — MLP Write-Location (in progress)

Does an MLP write the retrieved harmful concept into the residual stream, and where?

## Representational projection (COMPLETE) — late-dominated = readout-proximity artifact, NOT causal

`scripts/phase6_mlp_projection.py` on the extracted reps (means.npz mlp_out) + directions.npz. Per layer,
MLP write update = mean(DS mlp_out) − mean(NEUTRAL mlp_out) at codeword_last, projected onto the concept
direction (d_Direct in mlp_out space). Split=dev.

Top concept-write layers (proj_concept, cos):
- clearharm: **L31 11.5 (cos 0.69)**, L30 3.97, L29 3.59, L27 1.06 … band: early 1.7 / mid 4.4 / **late 25.3**
- curated: **L31 6.2 (cos 0.45)**, L30 1.64, L29 1.18, L28 0.51, L11 0.47, L13 0.42 … band: early 1.4 / mid 2.3 / **late 11.1**

**This is the readout-proximity confound, NOT the causal write.** The projection peaks at the last layers
(L29–31) on both cohorts. But a large projection late is exactly what the master plan warns about ("a write
layer must satisfy MORE than a large projection") and what prior N7-C established: late MLP output aligns
with the concept direction because the residual is accumulating toward the unembedding, while the validated
attribution-patching (AtP, pearson 0.93–0.95 vs true SubmodulePatch(mlp)) put the *causal* MLP write in the
**mid-band L9–14** (late MLP AtP ≈ 0 despite large mechanical patch effects). curated shows a faint mid-band
bump (L11, L13) consistent with the true mid-band write, swamped in raw projection by the late proximity term.

**Conclusion:** the projection metric reproduces the known late-proximity artifact on the new split and must
NOT be read as the write location. The causal write requires exact MLP intervention (next).

## Causal MLP write (demo positions) — NECESSARY mid-band L8–L12 (peak L9), NOT sufficient

> **PROVISIONAL (iter 35):** the iter-34 runs below patched demo (12) + question (2) codeword tokens due to
> a token-index-vs-char-offset classification bug in `build_fc` (now fixed). Because the effect localized to
> **L9 (mid), not the late/proximate layers**, it is very likely demo-driven; a clean demo-only re-run
> (703531/703532, layer, both cohorts) is in flight to confirm, alongside the real query-codeword write test
> (703533/703534). Numbers below to be reconfirmed.


`scripts/phase6_mlp_causal.py` (exact intervention, not projection): patch DS `mlp_out` ← matched BENIGN
`mlp_out` at demonstration-codeword positions, per layer & per canonical window, FC DE_context readout,
paired bootstrap CIs, dev(train)/heldout(test) reported SEPARATELY, self-swap = exact no-op (dev 0.0),
random-non-codeword-position control. Jobs 703456–703459 (both cohorts × window/layer). Primitive
`pc.ComponentOutSwap` (per-position mlp/attn-output swap; 4/4 synthetic tests; code-reviewed clean).

**Per-layer necessity (specific = random_control − C3, paired CI; SIG = CI excludes 0):**
- curated: dev peak **L9 +0.103 [.037,.189]** (also L6/L8/L12); heldout peak **L9 +0.179 [.097,.274]** (also L8).
- clearharm: dev **L8–L12 all SIG** (peak L9 +0.084 [.039,.141], L10 .046, L11 .030, L12 .034);
  heldout peak **L9 +0.030 [.010,.058]** (also L5/L7/L12).
- **Localized to a contiguous mid band L8–L12, sharply peaking at L9, on BOTH cohorts, replicating
  dev→heldout.** This is the SAME band as the demo-KV (resid_pre) retrieval necessity (PHASE4, L8–11 peak
  L9–10) — the MLP write and the K/V retrieval co-localize at the demonstration codeword.

**Sufficiency ≈ 0 at every layer** (installing DS `mlp_out` into a benign receiver does NOT create the
reading). → the demo-position MLP write is **necessary but not sufficient**, exactly mirroring demo-KV:
the binding is context-bound / distributed, not a transplantable local write.

**Confound resolved (honest):** the broad canonical `early` WINDOW (L0–9 jointly) gave a much larger
necessity (+0.42) but with NEGATIVE sufficiency (−0.18) — a broad-intervention degradation signature. The
per-layer curve isolates the real, clean, replicating driver at L8–L12/L9 (effect ~0.03–0.18); the inflated
window number is degradation from replacing 10 layers of MLP output and is NOT the effect size. Report the
per-layer L9 necessity, not the window value.

**Gate 4 status:** an MLP in the mid band (L8–L12, peak L9) contributes causally (necessity, both cohorts,
locked-test replication, matched controls, self-swap 0) — but it is a necessity-only, non-sufficient,
distributed contribution at the DEMO position, not a sufficient "concept write." Pairs with the demo-KV
retrieval necessity: the mid-band demo-position computation (its exposed K/V AND its MLP contribution) is
the causal locus; neither transplants.

### Limitation — query-codeword MLP write not testable in the FC readout (n=0)
The `--positions query` run (703460) produced **0 rows**: in the forced-choice question the codeword is
QUOTED (`the word "banana"`), so `find_word_occurrences_in_text` does not detect it, and the FC readout has
NO unquoted request-line query codeword (the request was replaced by the question). The paper's
"MLP writes the concept when it sees the QUERY codeword" therefore needs the FULL doublespeak-prompt readout
(request line present), reusing the Phase-3 query-position machinery (05/mlp_out) — flagged for next tick.
