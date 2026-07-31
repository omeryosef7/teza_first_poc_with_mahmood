# NEXT4 — Bug-check + low-hanging generalization

## Bug-check (adversarial audit: 4 auditors → verify). Outcome: NO headline result invalidated; 4 defects found + FIXED.
Verdict: S2 dissociation, S4 TOCTOU, T1 cross-arch all clean. Fixes committed:
- **C1 (HIGH, output bug) — T4 attribution localization was WRONG (my error).** I had claimed "L0 dominant + demonstration-codewords"; that was a reshape bug in my ad-hoc analysis. Recomputed from the artifact by explicit layer/pos: L0 is the *smallest* early layer (Σ|atp| 1.16); the effect concentrates at **late/mid layers (L24–L30, L13/L18/L21) at the query/readout position** (bomb pos-115 Σ|atp| 84.6; true-patch validation cells all pos-115), consistent across 3 pairs. **Corrected** in NEXT3_FINDINGS.md + PAPER_CONTRIBUTION.md; the demonstration-localization claim is **withdrawn**. (The AtP *technique* remains validated: pearson 0.89/0.95/0.92.)
- **C2 (MEDIUM, latent) — `significant_corrected` not gated on `ci_reliable`** in 43/44 (45/47 already gated). A degenerate/thin cell could be flagged significant. Audit confirmed 0/57 committed cells were actually affected, so no claim changed. **Fixed:** `bool(pa<alpha and ci_reliable)` in 43+44.
- **C3 (code) — `44_kv_mediation.run()` NameError** on the thinking path (`think` defined in main, used in run). Would have crashed the Qwen3 KV run. **Fixed:** compute `think` inside `run()`.
- **C4 (HIGH, estimand) — `47_repr_toctou` headlined `early_vs_late`, which is mechanically degenerate** (late window is causally after the L18 readout ⇒ late arm == baseline ⇒ early_vs_late == install_effect(early)). The genuine test is `early_vs_mid` (both windows propagate to the readout). **Fixed:** added `early_vs_mid` + based the generalization verdict on it. Recomputed from existing raw: **bomb +1.17 [0.78,1.57], grenade −0.72 [−1.06,−0.38], chlorine −0.68 [−1.05,−0.31]** — all CIs exclude 0, **confirming** the pair-dependent dominant-depth conclusion (the science held; only the estimand was mis-named).

## T4 attribution generalization (grenade + chlorine): technique validated on 3 pairs.
pearson AtP-vs-true: bomb 0.89, grenade 0.95, chlorine 0.92 (all trustworthy). Localization consistent across pairs: late/mid layers at the readout position (see C1 correction). The validated technique generalizes; the (retracted) demonstration-localization does not apply to any pair.

## S3 KV mediation on Qwen3 — pending (first run cancelled on the C3 NameError; resubmitting with the fix).
