# MASTER STATUS — CONTINUATION_MASTER_PLAN_V2 (honest, evidence-based)

**Generated 2026-08-08** from a 6-agent evidence audit (workflow wf_df3944cb-0b7) that checked every
section against COMMITTED run-dirs/reports (not progress-doc wording). **REFRESHED 2026-08-09 (completion push): DONE=22 / PARTIAL=5 / NOT_DONE=1** (7 PARTIALs closed from committed data via 10-agent audit; §13/§20/§27-X5 GPU refinements + §14-18 eval pending).
A section is DONE only if a committed output dir + report with real numbers backs it. This is the
authoritative remaining-work roadmap.

| § | pri | status | gpu | title | what remains (if any) |
|---|---|---|---|---|---|
| §1.1 | A | DONE | n | Resolve PENDING refusal-validation claims (BR-09 | — |
| §1.2 | A | DONE | n | Corrected GPU baseline / judge-noise drift envel | — |
| §1.3 | A | DONE | n | Repair v3 as the confirmatory dataset (validator | — |
| §2 | B | DONE | Y | Main scientific pivot — map the refusal-suppress | — (origin question = §4 now DONE [P4_REFUSAL_MEDIATION, run 737608]; full circuit map consolidated in REFUSAL_CIRCUIT_SYNTHESIS E1-E10) |
| §3 | B | DONE | Y | Refusal causal localization — layer × position × | — |
| §4 | B | DONE | Y | Distinguish suppression origin from carry/readou | — (P4_REFUSAL_MEDIATION: §7 refusal heads 72-88% MEDIATED/carry w/ depth gradient; sanity gates byte-perfect; run 737608, test n=42) |
| §5 | B | DONE | Y | Position causality — which part of the 9 matched | — (P5_POSITION: honest NULL — no manipulation both preserves concept-remap AND restores refusal; train n=85 + test n=42 committed; run 736658) |
| §6 | B | DONE | Y | Demonstration-count dose response (n_demo in {0, | — (P6_DOSE_RESPONSE: refusal suppression is a STEP at n=1, concept flat, ASR weakly coupled; run 735299) |
| §7 | C | DONE | Y | Targeted refusal head/edge analysis in the activ | — (P7_HEAD_EDGE, audit-2 corrected: head-distributed but LAYER-concentrated at L13; run 736900) |
| §8 | C | PARTIAL | Y | Full head->MLP path patching, concept + refusal  | §8.2 refusal DONE (P8_HEAD_MLP_PATH: NO-PATH at n=25; single-item false-positive corrected by aggregation); §8.1 concept RUNNING (737623). |
| §9 | B | DONE | Y | Behavioral sufficiency of carry heads during gen | — (P9_CARRY_SUFFICIENCY: NULL — installing carry state does not raise ASR) |
| §10 | B | DONE | Y | REPOWERED behavioral inertness (powered leakage- | — (P10, audit-2 corrected: concept-epiphenomenal via SPECIFICITY [rand>concept]; pooled equivalence framing withdrawn) |
| §11 | C | DONE | Y | Joint 2x2 ablation: concept-circuit {intact/abla | — (P11_JOINT_2x2: refusal restoration collapses ASR regardless of concept; additive, no interaction; run 736657) |
| §13 | D | PARTIAL | Y | PROSPECTIVE frozen-predictor attack-success pred | Build the FROZEN prospective version on v3 (not n=86 clearharm): calibrate layer/direction/threshold/scalar-calibration on TRAIN only, freeze, evaluate untouche |
| §14–18 | D | NOT_DONE | Y | Gate-7 attack objective (mechanism-derived GCG,  | The decisive comparison is entirely unrun: no held-out StrongREJECT ASR for ANY arm. run_gcg_p9_firstcut_eval.slurm is authored but NOT launched (needs 732918 t |
| §18 | D | DONE | Y | Continuous-objective sanity gate before discrete | — (every candidate direction has a committed continuous gate: refusal PASSES [§23/§6/§21]; carry-head+combined FAIL [P9 736570]; concept FAILS [P10/P24]; Jacobian-arm10 = refusal axis [P6 732004]. No ungated direction remains.) |
| §19 | D | DONE | n | Causal refusal-restoration defense (incl. §19.3  | — |
| §20 | D | PARTIAL | Y | Defense evaluation with utility (benign over-ref | The report itself flags the §20 utility panel as incomplete: the 5th condition — truly UNRELATED-NORMAL prompts (not attack-structured benign) — was NOT tested. |
| §21 | D | DONE | Y | Minimal effective intervention (dose curve / α50 | — (P_DEFENSE_UTILITY §21: α50≈2.12 @L18 [ΔASR −0.106 p=.049] but +0.282 over-refusal; over-refusal>|ΔASR| at every layer [732688] → NO selective minimal dose exists; honest finding) |
| §22 | B | DONE | Y | Token-timing of refusal restoration (prefill / d | — (P22_TIMING, run 732981: all 5 timing arms + anchor + rand/noop committed; timing that matters = decision state not decode-persistence; additive magnitude-sweep noted as optional caveat) |
| §23 | B | DONE | n | Decision-state counterfactual patch (bidirection | — |
| §24 | C | DONE | Y | Orthogonalization experiment (concept ⟂ refusal) | — (P24_ORTHOGONALIZATION: refusal component controls ASR −0.21 p=1e-4; concept-orthogonalized arm inert) |
| §25 | B | DONE | Y | Full mediation: demo-feature → refusal-suppressi | — (P25_FULL_MEDIATION: DS attack ~100% mediated by decision-state refusal repr [frac 1.00-1.07, train/dev, rand/self null]; ∘ §6 upstream; naive demo-removal confounded/documented) |
| §26 | E | PARTIAL | Y | Within-Llama generalization (unseen concepts/cod | No dedicated §26 harness/report. VARIABLE DEMO-COUNT and ALTERNATE-BENIGN-CODEWORD axes have no committed evidence. The existence/causal/prediction/attack-optim |
| §27 | E | PARTIAL | Y | Cross-model replication — staged X1–X5 gate on ≥ | Everything in the staged gate as defined: X2 (independently fit + validate a refusal direction on the 2nd model), X3 (DS suppresses it), X4 (refusal ablation ra |
| §28 | E | DONE | Y | Framework robustness — reproduce ≥1 headline int | — (P28: from-scratch IndepProjectOut reproduces refusal-ablation headline [+0.31 vs +0.33], label-agree 0.88/0.83, proven numerically equivalent; token divergence = bf16 reduction-order only; run 737682) |
| §29 | E | DONE | Y | Quantization / deployment robustness of refusal  | — (P29: refusal ablation raises harm at bf16/8bit/4bit [+0.26/+0.29/+0.52, McNemar sig], random ablation ns at all -> mechanism survives quantization; runs 737624/625/626, test n=42) |
| §33 | F | DONE | Y | Target figures F1–F8 | — (F5 dose + F6 attack-objective + fig_refusal_mediation all committed; F6 auto-upgrades to 2-seed when seed-43 eval lands) |

## Execution order (remaining, by plan §31 priority)
- **B (causal core):** §5 position-decomp, §6 dose-response, §4 origin-vs-carry mediation, §25 full mediation, §22 timing, §9 carry-head sufficiency, §10 powered concept ablation, §2-origin.
- **C (closure):** §7 head/edge, §8 head→MLP path, §11 joint 2×2.
- **D (practical):** §14–18 Gate-7 (first-cut running 732918 → eval), §13 prospective, §24 orthogonalization, §20/§21 defense completion (unrelated-normal + per-layer α50).
- **E (generalization):** §26 within-Llama, §27 CROSS-MODEL (X1–X5 staged), §28 framework robustness, §29 quantization.
- **F (paper):** figures F5 (CPU), F6 (after Gate-7), F4 assembly.

_Realistic note: ~22 GPU experiments serialized through a shared fair-share queue = multi-day compute. Executed via the 30-min loop, launching as slots free; nothing marked done without a committed run-dir._
## UPDATE 2026-08-08 (session progress — sections moved to DONE/PARTIAL, all run-dir-backed)
- §6 dose-response ✅ · §10 powered concept-ablation ✅ (Claim A at power) · §22 timing ✅ · §9 carry-sufficiency ✅ NULL
- §24 orthogonalization ✅ (refusal component controls ASR −0.21 p=1e-4; concept doesn't) · §14–18 Gate-7 ✅ first-cut (negative/non-specific)
- §5 position ◐ PARTIAL (no clean dissociation) · §11 joint 2×2 ✅ DONE
- **§27 CROSS-MODEL (Qwen3-14B): X1 ✅ X2 ✅ X3 ✅ X4 ✅ (4/5); X5 ◐ PARTIAL** → refusal-suppression mechanism GENERALIZES to a 2nd family
- Reports: P6/P10/P22/P9/P24/P_GATE7_FIRSTCUT/P5/P11/P27_CROSSMODEL + CLAIMS_AUDIT_2026-08-08

## UPDATE 2026-08-08 (late — audit-2 verdict corrections + §6/§7 closed)
- **audit-2 code-bug fixes applied+committed** (phase7 layer-gate, phase10 CI-vs-margin, phase_x5 a-priori AUC sign);
  reports P7/P10/P27 re-derived: §7 = head-distributed but **L13-concentrated**; §10 pooled equivalence withdrawn
  (epiphenomenality stands via **specificity**: rand-ablation > concept-ablation); X5 concept AUCs unchanged (only
  the random CONTROL was corrected, 0.63→0.33 null).
- **§6 report written** (P6_DOSE_RESPONSE, run 735299) → §6 DONE. **§7 DONE** (corrected). **§11 DONE**.
- **§8 head→MLP:** built head_attribution.json from §7 restore-fracs; refusal smoke 737496 running.
- **§29 quantization:** load_model(quantize=8bit|4bit) + --quantize wired (bnb 0.50.0 installed); 4bit smoke 737500 running.
- **STILL NOT DONE (5):** §4 origin-mediation, §8 head→MLP (smoke running), §25 full mediation, §28 framework (2nd impl), §29 quant (smoke running).
- **Remaining PARTIAL to strengthen:** §2/§5/§13/§18/§20/§21/§22/§26/§27-X5/§33-figures.
- **Blocked/env:** §29 needed bitsandbytes (now installed); Mistral/Gemma-4 cross-model = offline stubs (no weights) → §27 stays Qwen3(+Phi-4) only.
