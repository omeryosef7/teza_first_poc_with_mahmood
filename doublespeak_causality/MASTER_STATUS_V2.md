# MASTER STATUS — CONTINUATION_MASTER_PLAN_V2 (honest, evidence-based)

**Generated 2026-08-08** from a 6-agent evidence audit (workflow wf_df3944cb-0b7) that checked every
section against COMMITTED run-dirs/reports (not progress-doc wording). **DONE=6 / PARTIAL=10 / NOT_DONE=12.** A section is DONE only if a committed
output dir + report with real numbers backs it. This is the authoritative remaining-work roadmap.

| § | pri | status | gpu | title | what remains (if any) |
|---|---|---|---|---|---|
| §1.1 | A | DONE | n | Resolve PENDING refusal-validation claims (BR-09 | — |
| §1.2 | A | DONE | n | Corrected GPU baseline / judge-noise drift envel | — |
| §1.3 | A | DONE | n | Repair v3 as the confirmatory dataset (validator | — |
| §2 | B | PARTIAL | Y | Main scientific pivot — map the refusal-suppress | §2's actual OPEN causal question — 'what computation induced by the demonstrations SUPPRESSES the refusal representation' (the causal ORIGIN / source) — is NOT  |
| §3 | B | DONE | Y | Refusal causal localization — layer × position × | — |
| §4 | B | NOT_DONE | Y | Distinguish suppression origin from carry/readou | Build and run the refusal analogue: patch a candidate suppression component, freeze downstream refusal-carry states to the clean-DS trajectory, measure disappea |
| §5 | B | NOT_DONE | Y | Position causality — which part of the 9 matched | Build the 9 matched demo text variants (intent+format held constant), then run p_concept (forced-choice), decision-token refusal-direction projection, and Stron |
| §6 | B | NOT_DONE | Y | Demonstration-count dose response (n_demo in {0, | Construct nested paired demo subsets at n_demo in {0,1,2,4,6,8,10,12} and measure p_concept, decision-token refusal projection, and ASR simultaneously per item; |
| §7 | C | NOT_DONE | Y | Targeted refusal head/edge analysis in the activ | Run head-level and edge-level analysis restricted to the L13-L20 active refusal band: per-head refusal-projection contribution (Direct<->DS), attention destinat |
| §8 | C | NOT_DONE | Y | Full head->MLP path patching, concept + refusal  | Run the full head->MLP path-patching matrix for both families: 8.1 concept (retrieval heads -> L8-13 MLP write) and 8.2 refusal (demo-processing heads/component |
| §9 | B | NOT_DONE | Y | Behavioral sufficiency of carry heads during gen | Run behavioral sufficiency: install DS carry-head state/pattern into matched benign/neutral/direct context DURING generation and measure ASR. Arms: (1) carry-z  |
| §10 | B | NOT_DONE | Y | REPOWERED behavioral inertness (powered leakage- | Run the confirmatory powered comparison on v3: pre-register the minimum meaningful ΔASR before launch (≥0.10 → n≈275, ≥0.07 → n≈419 binary; OR the graded endpoi |
| §11 | C | NOT_DONE | Y | Joint 2x2 ablation: concept-circuit {intact/abla | Run the 2x2 on DS prompts: concept circuit {intact/ablated} (write/carry ablation) x refusal {restored/not}, measuring p_concept, refusal projection, AND ASR. W |
| §13 | D | PARTIAL | Y | PROSPECTIVE frozen-predictor attack-success pred | Build the FROZEN prospective version on v3 (not n=86 clearharm): calibrate layer/direction/threshold/scalar-calibration on TRAIN only, freeze, evaluate untouche |
| §14–18 | D | NOT_DONE | Y | Gate-7 attack objective (mechanism-derived GCG,  | The decisive comparison is entirely unrun: no held-out StrongREJECT ASR for ANY arm. run_gcg_p9_firstcut_eval.slurm is authored but NOT launched (needs 732918 t |
| §18 | D | PARTIAL | Y | Continuous-objective sanity gate before discrete | §18 is only satisfied for the refusal axis. Any NEW candidate objective direction (Jacobian arm10, carry-head, combined) must run its own controlled-perturbatio |
| §19 | D | DONE | n | Causal refusal-restoration defense (incl. §19.3  | — |
| §20 | D | PARTIAL | Y | Defense evaluation with utility (benign over-ref | The report itself flags the §20 utility panel as incomplete: the 5th condition — truly UNRELATED-NORMAL prompts (not attack-structured benign) — was NOT tested. |
| §21 | D | PARTIAL | Y | Minimal effective intervention (dose curve / α50 | Sweep is L18-only. §21 asks per validated layer for α50 / smallest reliably-effective α with a cross-layer comparison L13/L16/L18/L20(/L24/L28) to find the best |
| §22 | B | PARTIAL | Y | Token-timing of refusal restoration (prefill / d | Run the remaining timing arms at comparable integrated magnitude — prefill-only, first-generated-token, first-k, and all-decode-steps restoration — and compare  |
| §23 | B | DONE | n | Decision-state counterfactual patch (bidirection | — |
| §24 | C | NOT_DONE | Y | Orthogonalization experiment (concept ⟂ refusal) | Run the 5-arm causal intervention with validated layers + train-fitted directions: (1) concept only, (2) refusal only, (3) concept ⟂-orthogonalized against refu |
| §25 | B | PARTIAL | Y | Full mediation: demo-feature → refusal-suppressi | Run the integrated behavioral mediation chain: remove/patch a demo feature → observe refusal RESTORATION → then FREEZE the downstream refusal state back to the  |
| §26 | E | PARTIAL | Y | Within-Llama generalization (unseen concepts/cod | No dedicated §26 harness/report. VARIABLE DEMO-COUNT and ALTERNATE-BENIGN-CODEWORD axes have no committed evidence. The existence/causal/prediction/attack-optim |
| §27 | E | PARTIAL | Y | Cross-model replication — staged X1–X5 gate on ≥ | Everything in the staged gate as defined: X2 (independently fit + validate a refusal direction on the 2nd model), X3 (DS suppresses it), X4 (refusal ablation ra |
| §28 | E | NOT_DONE | Y | Framework robustness — reproduce ≥1 headline int | Re-run ≥1 headline intervention (refusal ablation / restoration / decision-state patch) under a second implementation (TransformerLens or nnsight, or a minimal  |
| §29 | E | NOT_DONE | Y | Quantization / deployment robustness of refusal  | Add a quantization_config path to load_model; run the corrected baseline + refusal ablation/restoration under 8-bit and 4-bit (optionally AWQ/GPTQ); test whethe |
| §33 | F | PARTIAL | Y | Target figures F1–F8 | Build F5 (dose vs demo-count from PHASE9_DOSE data — CPU plot), F6 (blocked on Gate-7 §14–18 GCG arms, GPU), assemble a combined F4 (add the Gate-B counterfactu |

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
- §5 position ◐ PARTIAL (no clean dissociation) · §11 joint 2×2 ◐ running
- **§27 CROSS-MODEL (Qwen3-14B): X1 ✅ X2 ✅ X3 ✅ X4 ✅ (4/5); X5 pending** → refusal-suppression mechanism GENERALIZES to a 2nd family
- Reports: P6/P10/P22/P9/P24/P_GATE7_FIRSTCUT/P5/P27_CROSSMODEL + CLAIMS_AUDIT_2026-08-08
- **STILL NOT DONE:** §27 X5, §4 origin-mediation, §7 head/edge, §8 head→MLP, §25 full mediation, §28 framework, §29 quant, figures F1/F4/F5/F6/F8, §20 unrelated-normal utility
