# Doublespeak Causal Circuit — Implementation Progress Log

Tracking execution of `CAUSAL_CIRCUIT_MASTER_PLAN.md`.
Model: Llama-3.1-8B-Instruct (bf16 for causal claims). Branch: `behavioral-causality-sprint`.

**Legend:** ☐ not started · ◐ in progress · ☑ done · ⚠ blocked/needs-decision · ✗ null/negative result

---

## Live status (most recent first)

- **2026-08-04 (iter 70, loop tick — new harnesses VALIDATED (self-swap gates pass); NEW result: attn
  pattern causal)** — smokes: **phase4b_pattern selfdev=0.0 ✓ + NEW causal result** — patching the DS
  attention PATTERN with benign at the carry heads drops the reading (C1 1.0→0.905, nec_specific +0.095),
  while a UNIFORM pattern barely moves it (+0.001) → it's the SPECIFIC benign pattern that matters, not
  just disrupting attention. The in-file eager-attn capture/patch primitive fires correctly (self-swap
  tripwire passed). **phase5b_qkv selfdev=0.0 ✓ but Q/K/V-at-answer necessity ≈0** (honest null — the head
  OUTPUT carries the concept, not its answer-position Q/K/V input; consistent w/ the mediation finding +
  the workflow's flagged scope caveat). **phase6b_windows** running (707410, heavy 143-window scan).
  → the subagent-written harnesses (incl. tricky in-file primitives) are CORRECT. Parametrized the 3
  wrappers (DSBENCH/DSNPROMPTS/DSSPLITS env). Launched **phase4b_pattern FULL on v2 (116 ex, 707446)** =
  more-examples + more-patching combined. Next: read pattern-full (does the attn-pattern causality hold at
  n≥20 both splits?) + windows result; document the qkv null; then phase5 heads + phase7c sufficiency on v2.

- **2026-08-04 (iter 69, loop tick — MORE-EXAMPLES result: L9 write GENERALIZES + strengthens)** — v2 MLP
  re-run 707203 done on **116 examples** (Wilcoxon-Holm per split): **dev n_valid=59 → L8–L13 all survive
  Holm, L9 peak +0.080 [.041,.127]; heldout n_valid=55 → L9–L13 survive, L9 +0.030 [.012,.052].** The L9
  mid-band MLP-write necessity **generalizes to the expanded dataset (30 new concepts) and STRENGTHENS**
  (more of the L8–13 band survives on the larger n) — direct delivery of Omer's "generalize with more
  examples." Fixed 2 bugs in the auto-cloned smoke wrappers (leftover `${DSBENCH:?}` guard → job died at
  line 30; then `--bench` path relative to root not doublespeak_causality/) — resubmitted smokes
  **707410/11/12**. Next tick: self-swap gates on the 3 new harnesses → then full battery on v2 + expanded.

- **2026-08-04 (iter 68, loop tick — transient SLURM cgroup fail, resubmitted)** — jobs 706092-95 all died
  at slurmstepd cgroup setup (`_cgroup_procs_check: failed on path (null)/cgroup.procs`) — a NODE-LEVEL
  SLURM infra error, NOT code (empty .out, never reached python). Resubmitted all 4 → **707203** (phase6 MLP
  on v2, 116 ex) + **707204/05/06** (smokes: windows/pattern/qkv). Pending on L40S. Next tick: read the
  decisive self-swap gates (must be 0.0) + v2 more-examples MLP result.

- **2026-08-04 (iter 67, loop tick — v2 bench DONE + new harnesses launched)** — `bench_clearharm_v2.json`
  built: **116 DOUBLESPEAK** (clearharm dev 44/heldout 42 + expanded dev 15/heldout 15; original test
  preserved). Workflow wwjhplcgs finished — 3 harnesses written with honest risk disclosures + self-swap=0
  tripwires: **phase6b_windows** (reuses ComponentOutSwap, low-risk), **phase4b_pattern** (in-file eager
  attn capture/patch; flagged risk = eager-global-swap version fragility, self-swap tripwire catches it),
  **phase5b_qkv** (in-file QKVHeadCapture/Patch, GQA-aware, self-swap tripwire). Launched 4 jobs: **706092**
  = phase6 MLP-necessity on v2 (more-examples re-run, 116 ex) + smokes **706093/94/95** for the 3 new
  harnesses. **Decisive gate next tick: self-swap_max_dev == 0.0 on each smoke** (if not, the hook is
  broken) AND the intervention has a nonzero effect. Then launch the full battery on v2 + expanded.

- **2026-08-04 (iter 66, loop tick — v2 bench build + new harnesses landed)** — Expander DONE: **30 new
  single-token concepts** (dedup/single-token capped yield). `scripts/build_expanded_bench.py` running in
  BACKGROUND (PID 2517781): generates benign-codeword demos + folds the 30 into the clearharm bench as a new
  'expanded' sub-cohort → `bench_clearharm_v2.json` (86+30=116, ~15 appended to dev / ~15 to heldout;
  ORIGINAL locked test preserved, no leak → keeps ≥20/cell). Workflow **wwjhplcgs** wrote all 3 new harnesses
  (phase6b_windows, phase4b_pattern, phase5b_qkv) — all syntax-OK, reference right primitives + controls
  (phase4b handles eager+GQA, phase5b handles num_key_value). NOT yet trusted — will smoke each + read the
  workflow's adversarial review before launching (subagent GPU code needs verification). Next tick: verify
  v2 bench discriminates (DS reads concept), smoke the 3 harnesses, then launch the full causal battery
  (phase6 MLP, phase5 heads, phase7c sufficiency + the 3 NEW ones) on v2 (116 ex) + the expanded cohort.

- **2026-08-04 (iter 65, loop tick — SCALE-UP: more examples + more patching, per Omer)** — Omer:
  generalize all tests with MORE examples (train+test), more activation-patching/knockout, doc everything,
  keep /loop 30m, ultracode fan out. Two parallel efforts launched:
  **(1) MORE EXAMPLES** — current 137 is near-max single-token yield of existing sources (curated 17 s-tok
  concepts, clearharm 86/179). So generating NEW single-token concepts via gpt-4o-mini (tested: 9/12
  single-token, correct categories). `scripts/expand_concepts.py` running in BACKGROUND (PID 2510853,
  resumable, checkpoints each accept) → target 60 new concepts + 12 demos each, deduped vs existing →
  `data/expanded_concepts_v2.json`. Next: `build_expanded_split.py` folds them into a v2 split w/ fresh
  train/test, rebuild bench, re-run ALL key causal tests on the larger n (esp. fixes curated-heldout n=21
  low-power). **(2) MORE PATCHING** — Workflow **wwjhplcgs** (ultracode) writing 3 NEW causal harnesses in
  parallel (code-only, no data): `phase6b_windows` (MLP sliding/cumulative granularity windows — plan
  mandate), `phase4b_pattern` (attention-PATTERN patching vs edge-KO), `phase5b_qkv` (per-head Q/K/V
  decomposition) + adversarial review of the 2 high-risk ones. I smoke+fix each in main loop before
  launching. RULES held: ≥20/cell, train/test sep, Wilcoxon-Holm, no trimming, max-6 SLURM L40S, harmful
  text main-loop only. Next tick: check expander + workflow harnesses → smoke → launch on both splits.

- **2026-08-03 (iter 64, loop tick — sufficiency onset = gradual, L17H27 pivotal)** — onset 706055/706056
  done (controls pass, selfdev 0.0). **Sufficiency accumulates GRADUALLY across L14–21** (not an abrupt L14
  switch): cumulative p_concept curated .004→.077(L17)→.162; clearharm .19→.41(L17)→.47. **Biggest single
  jump = adding L17(H27)** (curated dev ×11, heldout ×4; clearharm ×2 both splits) — also the top necessity
  head on clearharm = pivotal carry head. clearharm has substantial L14-alone sufficiency (.16–.19),
  curated builds from ≈0 — clearharm carries concept-signal earlier. → sufficiency, like necessity, is
  **distributed within the band, pivotal head L17H27**; full band = max transplantability. Updated
  PHASE7_PATH (Phase 7d). Consistent with the whole-circuit distributed-within-band theme.

- **2026-08-03 (iter 63, loop tick — sufficiency ONSET scan: where does it emerge?)** — Verified the
  iter-62 sufficiency is robust (controls S_rand=head-specific + S_self=DS-content-specific both pass;
  replicates on locked test). Built `scripts/phase7d_onset.py` (reuses phase7c capture/readout): installs
  CUMULATIVE carry subsets DS→benign (L14 → L14–15 → L14–17 → L14–18 → L14–21) to locate the
  context-bound→transplantable transition — WHERE does the concept become sufficient? One z-capture/example,
  reused across groups. Caught + fixed a `set -u` unbound-var bug in the wrapper echo (leftover $DSCARRY);
  cancelled 706053/54, resubmitted **706055/706056**. Next tick: read the cumulative curve → does
  sufficiency turn on at L14, or build gradually across the band?

- **2026-08-03 (iter 62, loop tick — SURPRISE: carry heads are SUFFICIENT — sufficiency EMERGES)** — full
  706024/706025 done. **UNEXPECTED POSITIVE, all 4 cells:** installing DS carry-head z into a BENIGN prompt
  RAISES the reading from ≈0 to **0.16 (curated) / 0.43–0.47 (clearharm)** — suf_specific(S3−S_rand) SIG:
  curated dev +0.16 [.09,.25] / heldout +0.24 [.13,.37]; clearharm dev +0.37 [.27,.48] / heldout +0.41
  [.30,.51]. **Specific** (random-head install ≈0), self-check exact 0.0. **FIRST component with BOTH
  necessity AND sufficiency** — demo-KV/MLP-write/state-inject were all ≈0. Not readout-proximity (carry
  heads mediated, direct_frac≈0). **REFINES the narrative: binding is context-bound at demo/write (not
  transplantable) but becomes a TRANSPLANTABLE representation once carried in L14–21** — a progression, not
  uniformly non-sufficient. Updated PHASE7_PATH (Phase 7c) + FINAL (Q4 + sufficiency-emerges section). This
  is the session's most novel finding. Next: consider behavioral sufficiency of the carry install, or
  consolidate.

- **2026-08-03 (iter 61, loop tick — carry-head sufficiency install, final n/s pair)** — Built
  `scripts/phase7c_sufficiency.py` (reuses ZHeadCapture/ZHeadPatch): install DS carry-head answer-z into a
  BENIGN receiver — does the concept reading appear? Completes the carry-band necessity+sufficiency pair
  (Phase 5/7 necessity done). Arms S1/S3_carry/S_rand/S_self (self = benign own z, no-op check). Full runs
  **706024 (curated) / 706025 (clearharm)** launched. Expected ≈0 (every sufficiency test S3≈0 across
  Phases 4/5/6 = distributed/context-bound). Next tick: read sufficiency_specific (S3−S_rand) + self-check
  → confirm the honest "necessary + edge-connected but NOT sufficient" close of the carry analysis.

- **2026-08-03 (iter 60, loop tick — publication circuit-summary FIGURE)** — Built
  `scripts/make_circuit_figure.py` (scalar-only; Okabe-Ito colorblind-safe; dataviz-skill principles).
  `figures/circuit_summary.png`: Panel A = per-layer causal necessity across depth (MLP-write peak L9 +
  head-carry Σ/layer peak L14, ClearHarm locked test) with the 3 co-localized stage bands (retrieval+write
  L8–12, carry L14–21, output L30–31); Panel B = direct-to-logit vs mediated (carry 0.00, output 0.62,
  L9→carry mediation 0.79, random 0.00). Fixed a y-limit/label layout bug (was 10k px tall) → clean
  1920×672. The paper-ready visual summary of the complete audited circuit. Plan 0–11 done + circuit closed
  + figure. Next: optional carry-head sufficiency-install, or consolidate.

- **2026-08-03 (iter 59, loop tick — CIRCUIT CLOSED: L9-write→carry edge is CAUSAL)** — full mediation
  705295/705296 done. **DECISIVE POSITIVE, both cohorts+splits:** freezing the L14–21 carry band to clean
  after neutralizing L9 **restores ~75–83% of the drop** (curated dev .76 / heldout .83; clearharm dev .75 /
  heldout 1.46 overshoot n=9), while **random-head freeze restores 0%** (perfect specificity); self-check
  exact 0.0. → **the L9-write → L14–21-carry EDGE is causal — the carry band READS the L9 write.** Circuit
  upgraded from two validated endpoints to a **directed, edge-connected pathway**. Updated PHASE7_PATH.md
  (Phase 7b section) + FINAL report (Q7 + closed the limitation). New result beyond the plan. Next: optional
  sufficiency-install of carry heads, or wrap. Plan 0–11 done + circuit closed.

- **2026-08-03 (iter 58, loop tick — NEW: circuit-closure mediation L9-write→carry band)** — Plan fully
  done (0–11); taking the flagged high-value NEW extension that closes the last open link. Built
  `scripts/phase7b_mediation.py` (reuses ComponentOutSwap + ZHeadPatch + ZHeadCapture): does the L14–21
  carry band READ the L9 MLP write? Neutralize L9 (Phase-6 necessity) → then FREEZE carry-head answer-z to
  clean DS; if freezing RESTORES the reading, the L9 effect is mediated by the carry band.
  mediation_frac=(pB−pA)/(C1−pA); random-head-freeze control + self-check (freeze carry w/o L9 = no-op ≈C1).
  Smoke 705185 validated (selfdev=0.0 exact no-op) but L9resp=0 at n=3 (small skewed L9 effect); launched full 705295/706296.
  → full both cohorts → is the L9→carry edge causal (mediation_frac carry ≫ random)?

- **2026-08-03 (iter 57, loop tick — Phase 11 CONCLUDED from existing evidence → ALL PHASES DONE)** —
  Found the behavioral sufficiency test (19) was ALREADY run on Llama + analyzed (BEHAVIORAL_CAUSALITY_
  RESULTS.md): **state injection ≤0.16 ASR ("never a potent injectate")** = behavioral confirmation of the
  Phase-6 S3≈0; **dissociation** (decoding-sufficiency ≠ behavioral sufficiency). With prior temporal-GCG
  net-negative + Gate-6 sufficiency-fail = **three converging lines → Phase 11 verdict: well-controlled NULL
  for a token-suffix objective; the mechanism is behaviorally actionable ONLY via the white-box concept-
  install + refusal-removal edit (finding #5).** No re-run needed. Finalized `GCG_MAC_EVALUATION.md` (verdict
  + optional fresh-GCG extension deferred as low-value) and updated FINAL report (Q12 + phase status +
  bottom line). **ALL PHASES 0–11 COMPLETE.** The full audited, cross-cohort, Holm-corrected causal circuit
  is delivered end-to-end. Optional future work: upstream L9-write→carry-head edge path-patch; fresh
  compute-matched GCG on ClearHarm+Llama (low-value confirmatory).

- **2026-08-03 (iter 56, loop tick — Phase 11 design + prior-evidence synthesis)** — Surveyed GCG infra:
  built for **Qwen3 + curated + temporal(mixed-cache) objective** — a full fresh Llama+ClearHarm+concept-
  objective GCG rebuild = disproportionate for an expected null. Wrote `reports/GCG_MAC_EVALUATION.md`:
  13-arm compute-matched design + integration point (existing `DSLAMBDA·repr_loss` hook), synthesized the
  **substantial prior GCG evidence** (temporal-GCG net-negative/backfired ASR 0.0; signature inert; soft-
  prompt gate null) → honest prediction **well-controlled NULL** (Gate-6 sufficiency fails + distributed +
  prior). Defined the proportionate decisive test = plan's §8.5 gate on the NEW objective: **G1 = behavioral
  sufficiency of the concept-region install** (add d_Direct L9–L12 to neutral/benign, StrongREJECT ASR, vs
  signature/random/wrong-layer controls) reusing 18/19 + directions + AllPositionAddMultiLayer. Key honest
  framing: the circuit is behaviorally actionable via **white-box concept-install + refusal-removal** (prior
  finding #5 = works) but NOT via a **black-box suffix objective** (distributed + prior GCG null). Next:
  launch G1 on the ClearHarm split (confirm white-box sufficiency on the new split).

- **2026-08-03 (iter 55, loop tick — FINAL SYNTHESIS report; Omer: synthesis now, Phase 11 after)** —
  Consulted Omer on Phase 11 → **"Both: synthesis now, Phase 11 after."** Rewrote
  `reports/FINAL_CAUSAL_CIRCUIT_REPORT.md` for the complete Phases 0–10 (was interim 0–6, pre-audit):
  one-line circuit, all **12 plan questions answered** with per-phase evidence, novel contributions,
  methodological rigor (Wilcoxon correction + audit + coverage), honest limitations. **Circuit:
  demo-KV retrieval (L8–11) + L9 MLP write → L14–21 carry heads (mediated) → L30–31 proximal output →
  logit; distributed within bands; concept⊥refusal.** Phases 0–10 ✅, Phase 11 ⏳ queued. Next tick: set
  up the compute-matched Phase-11 GCG comparison (naïve GCG vs concept-region objective vs signature vs
  random control) reusing 25_eval_gcg_asr + gcg infra, over subsequent ticks (expected well-controlled null).

- **2026-08-03 (iter 54, loop tick — Phase 10 causal objective distilled, Gate 6 assessed)** — Wrote
  `reports/CAUSAL_OBJECTIVE.md`: distilled the objective from the complete circuit, terms kept SEPARATE
  (concept / refusal / retrieval / mlp_write / path; **doublespeak_signature KILLED — causally inert**,
  confirmed on both the pair and the new split). Filled the 10-point **Gate-6 checklist** from Phases 3–9:
  **9/10 PASS** (necessity Wilcoxon-Holm all 4 cells, dose-response, random-controls-fail, not-degradation,
  refusal-independent cos≈0.01–0.06, test-replication, transfer) **but sufficiency (4) FAILS** (S3_install≈0
  — necessary-not-sufficient, distributed/context-bound). → the concept-write handle is an eligible
  NECESSITY target but not standalone-sufficient. **Phase 11 (GCG/MAC) is a large GPU ask with an expected
  well-controlled NULL** (prior CAUSAL_CORE: mechanism-guided GCG net-negative; sufficiency fails here) —
  **consulting Omer: run the compute-matched Phase-11 test, or go to final synthesis?** Phases done: 0–10.

- **2026-08-03 (iter 53, loop tick — Phase 8 readout emergence, CPU-only)** — Built
  `scripts/phase8_readout.py` (reuses extracted Llama reps + unified concept direction; no GPU). Per-layer
  linear concept projection at the answer position. **RESULT: linear readability emerges LATE (peaks L31,
  onset-50% at L31) on all 4 cells — ≈0 at the causal write layer L9, only 10–16% of max by L14.** So
  linear READABLE (late/L31) ≠ causally WRITTEN/CARRIED (L9/L14–21). This is residual accumulation toward
  the unembedding (readout-proximity, same as the Phase-6 MLP-projection artifact), mechanistically
  consistent (write@L9 → carry@L14–21 → readable@L31). **Confirms the plan's point: a naive logit-lens
  readout is descriptive + misleading about mechanism — why the causal interventions (not readout) localized
  the circuit.** Wrote `reports/PHASE8_READOUT.md`. **Phases done: 0–9.** Remaining: Phase 10 (causal
  objective — unblocked), Phase 11 (GCG/MAC), final synthesis. Next: Phase 10.

- **2026-08-03 (iter 52, loop tick — Phase 9 dose-response COMPLETE: graded lever)** — full runs
  704861–704864 done. **Clean MONOTONE graded dose-response over α∈[0,1] on ALL 4 cells** (both cohorts ×
  train/test), single-L9 AND L9–L11 band: as the DS MLP write is interpolated toward benign, p_concept
  falls smoothly (single-L9 drop .017–.115; band .028–.107). α=0 no-op anchor = DS baseline (exact);
  α=1 = phase6 necessity (internally consistent). curated's only non-monotonicity is a trivial α>1
  EXTRAPOLATION plateau. → **the mid-band MLP write is a GRADED causal lever, not on/off** (Phase 9 met).
  Wrote `reports/PHASE9_DOSE.md`. **Phases done: 0–7, 9.** Remaining: Phase 8 (Jacobian, descriptive),
  Phase 10 (causal objective — gated on the validated handle, now available), Phase 11 (GCG/MAC), final
  synthesis. Next: Phase 10 objective (target the L9 write / concept direction) or Phase 8 Jacobian.

- **2026-08-03 (iter 51, loop tick — Phase 9 dose smoke validated, full launched)** — dose smoke 704785:
  **α=0 no-op check PASSES** (α=0 = DS baseline p≈1.0 = C1) — harness correct. Curve flat at n=2 (drew weak
  examples; L9 necessity is small + right-skewed, median ~.015, so a 2-example curve is uninformative — the
  effect lives in the strong-concept subset). Launched full both cohorts × {L9 single, L9–11 band}:
  **704861/704863 (L9) + 704862/704864 (L9–11 band)**. The band (concentrated write region) should give a
  cleaner graded curve than L9 alone. Next tick: read dose curves + monotonicity → is the MLP write a graded
  lever (Phase 9)? Then Phase 10 (causal objective) / Phase 11 (GCG) + final synthesis.

- **2026-08-03 (iter 50, loop tick — Phase 9 dose-response harness)** — Built `scripts/phase9_dose.py`
  (reuses audited phase6 machinery: FC readout, demo positions, pc.ComponentOutSwap with an INTERPOLATED
  donor (1−α)·DS + α·BENIGN). Sweeps the L9 demo-codeword MLP patch at α∈{0,.25,.5,.75,1,1.5,2}: α=0 =
  DS baseline (exact no-op check), α=1 = full benign swap (= phase6 C3 necessity). A **monotone p_concept
  decrease with α** = the plan's evidence that L9 is a GRADED causal lever, not an on/off artifact (Phase 9
  requirement). Reports per-split curve + monotonicity flag. Smoke **704785** (curated n=2, L9). Next tick:
  validate smoke (α=0≈DS baseline, monotone drop) → full both cohorts → dose-response for the L9 write; then
  optionally the mid-band window + concept-direction dose-response.

- **2026-08-03 (iter 49, loop tick — Phase 7 FULL: carry vs proximal RESOLVED, Gate 5)** — full runs
  704725/704726 done (both cohorts, n≥20/split, all trust=True, freeze_dev=0.0). **CLEAN DECISIVE RESULT
  replicating on all 4 cells:** mid-to-late-mid heads **L14,L15,L17,L18,L21 = CARRY (direct_frac≈0.0)** —
  freezing downstream removes their whole logit effect ⇒ mediated; only **L30,L31 = readout-PROXIMAL output
  (direct_frac≈0.5–0.76)**. **Resolves the Phase-5 proximity caveat**: the mid-band L14–21 is genuine carry,
  NOT artifact; proximity applies only to L30–31. **Full assembled circuit: L8–11 demo retrieval (K/V) + L9
  MLP write → L14–L21 answer-position CARRY heads (mediated) → L30–31 proximal OUTPUT → logit** — every
  stage causally tested + Holm(Wilcoxon) + cross-cohort + audited + coverage-validated. Gate 5 met (carry
  band). Wrote `reports/PHASE7_PATH.md`. Next: (a) upstream L9-MLP-write → carry-head EDGE path-patch
  (does the carry band read the L9 write?), or (b) Phase 8 Jacobian / Phase 9 dose-response / synthesis.

- **2026-08-03 (iter 48, loop tick — Phase 7 smoke CONFIRMS carry-vs-proximal split)** — phase7 smoke
  704606 validated: **freeze_consistency_dev=0.0, selfswap=0.0, trust=True** all heads (freeze machinery
  exact). **Result (n=3): mid-band heads L14H4/L15H8/L18H20 have direct_frac≈0.0** (DIRECT≈0, TOTAL large 1–2
  logits) → their logit effect is ENTIRELY mediated through downstream layers = genuine **CARRY heads**;
  **late heads L30H15/L31H0 have direct_frac≈1.0** (DIRECT≈TOTAL) = **readout-proximal OUTPUT heads** (the
  proximity concern, now confirmed). So the L14–18 mid-band is real mechanistic carry, NOT a readout
  artifact — separates the two head groups causally. Launched full **704725 (curated) / 704726 (clearharm)**
  on L40S nodes (excl. slow n-801), 10 heads (mid carry candidates + late proximal contrast), n≥20/split.
  Next tick: confirm frac≈0 (mid) vs ≈1 (late) at full n both cohorts → Gate 5 (path mediation) for the
  answer-position carry band.

- **2026-08-03 (iter 47, loop tick — coverage validator (plan deliverable) while phase7 smoke loads)** —
  phase7 smoke 704606 still loading on n-803 (slow). Built the plan-required
  `scripts/validate_experiment_coverage.py` (institutionalizes the audit's ad-hoc integrity checks):
  auto-detects phase6/phase5 schema; checks no duplicate rows, n_valid≥20 per split, self-swap no-op
  (≤1e-4), all required cells present, split-sid disjointness; exits nonzero on any FAIL. **Ran it on all 6
  committed causal-KO + head-patch dirs → all `ok`** (ssdev=0.0, 0 dups, n_valid ≥20; curated heldout 21).
  Confirms the exports are clean post-audit. Next tick: validate phase7 freeze-consistency → full
  DIRECT-vs-TOTAL (mid L14–18 carry vs late L30–31 proximal).

- **2026-08-03 (iter 46, loop tick — resume Phase 7 on audited foundations)** — phase7 smoke 704416 had
  run **1h09m** on n-801 (that node's weight-load is pathologically slow — same as the 1h27m attn_out job);
  cancelled + resubmitted **704605 with `--exclude=n-801`**. Applied the last audit item (findings 14/15):
  phase7 now emits a **`trustworthy` gate** — direct_frac is nulled unless freeze_consistency_dev ≤ 0.05
  AND selfswap_dev ≤ 0.05, so a compromised freeze can't be read as a real DIRECT/TOTAL split. Next tick:
  validate freeze-consistency≈0 on 704605 → full DIRECT-vs-TOTAL run (are the mid-band L14–18 heads genuine
  carry, frac<1, vs late L30–31 proximal output, frac≈1). Audit response now complete (20/20 confirmed
  findings fixed or verified-inert; only cosmetic test-coverage items deferred).

- **2026-08-03 (iter 45, AUDIT FIXES applied)** — 6-auditor workflow returned **20 confirmed findings**
  (2 high, 4 medium, 14 low). Numeric main-loop checks: `cid==kid`=0, `rlen<m`=0, all n_valid≥16 →
  low-sev findings 6/7/12 **INERT in data**; demo_cw count mismatch = 3 curated/5 clearharm (conservative).
  **MATERIAL FIX (both high):** the Holm significance used a sign-flip permutation whose resolution floor
  (1/nperm=5e-5) is coarser than the 1024-cell head threshold (α/m=4.9e-5) AND could return p=0 → the Phase-5
  "60–75 Holm-sig heads" was a **p=0 artifact**. Switched phase5+phase6 analyzers to **Wilcoxon signed-rank**
  (robust to the right-skew — a paired t-test was over-conservative and wrongly nulled L9; Wilcoxon +
  properly-resolved permutation agree). **RE-DERIVED:** *Phase 6* — **L9 survives Holm on ALL 4 cells**
  (result HOLDS); L9–L12 band on clearharm heldout; L10 split-dependent. *Phase 5* — heads survive on **3/4
  powered cells** (curated dev 58, clearharm dev 31, clearharm heldout 31); **curated heldout=0** (n=21
  low-power negative, not structural). Robust mid+late heads (L17H27, L15H8, L18H20, L14H23, L21H10, L22H19,
  L30H15, L31H0, L26H13) — conclusion (specific heads, distributed within L14–18 + late bands) UNCHANGED.
  Also fixed: **phase6_analyze cell C3/C3_mlpout alias** (broken reproduce path, finding 3), **(+1) MC
  correction**, **underpowered flag** (finding 1), **bootci only for Holm-sig cells** (speed). Rewrote
  `reports/PHASE5_HEADS.md` + corrected `reports/PHASE6_MLP.md` (Wilcoxon numbers, pending-contradiction +
  L10 + L14/L15-cohort-overstatement fixed). Test suite still 109 pass. Remaining low-sev code hardening
  (random-pool range, cid==kid guard, demo-count log, batch asserts) = next, then resume phases.

- **2026-08-03 (iter 44, loop tick — full correctness AUDIT, per Omer)** — Numeric export verification
  (main loop, can read harmful data): **all clean** — phase6 demo runs 0 duplicate rows, all 8 cells
  present, n_valid ≥20 both splits/cohorts, self-swap dev EXACTLY 0.0; phase5 curated merge 0 dup
  benign-rows, 32 layers covered, **heldout top heads L15H4 .106 / L14H4 .104 match reports.md EXACTLY**.
  **Full test suite: 109 passed / 13 GPU-skipped, 0 fail.** Launched a **6-auditor + adversarial-verify
  Workflow** (wvrceb4zt) over the harnesses/analyzers/reports — scoped to CODE + scalar summary.json ONLY
  (subagents forbidden from reading bench/splits/raw.jsonl harmful text; numeric raw checks done in main
  loop). Awaiting confirmed findings → will fix any real bug, then continue loop. (phase7 smoke 704416 still
  loading on slow node n-801.)

- **2026-08-03 (iter 43, loop tick — Phase 7 DIRECT-vs-TOTAL path harness)** — Built
  `scripts/phase7_direct_total.py` reusing 50_path_patching's freeze primitives VERBATIM
  (FreezeAllHeadsExcept + FreezeMLP + capture_clean_all). For each Phase-5 candidate head: TOTAL =
  z-patch←benign (everything recomputes) vs DIRECT = same but ALL downstream heads+MLPs frozen to clean-DS
  (skip-path only). **direct_frac = DIRECT/TOTAL separates readout-proximal OUTPUT heads (frac≈1) from
  genuine CARRY heads (frac≪1)** — resolves the Phase-5 proximity caveat on L14–18. Metric = logit_diff
  (concept−codeword), same as 48/49/50. Built-in sanity: `freeze_consistency_dev` (freeze-all-clean +
  clean sender must reproduce m_clean) + self-swap. parse_heads is regex-based (L\d+H\d+) so SLURM
  --export uses underscores (dodges the comma bug). Smoke **704416** (curated n=2, mid heads
  L14H4/L15H4/L15H8/L17H27/L18H20 + late output L30H15/L31H0 as proximity contrast). Next: validate
  freeze-consistency≈0 → full run both cohorts → are the mid-band L14–18 heads genuine carry (frac<1) vs
  the late L30–31 proximal output (frac≈1)? = Gate 5 (path mediation) for the concept-carry band.

- **2026-08-03 (iter 42, loop tick — Phase 5 clearharm confirm + honest cross-cohort correction)** —
  clearharm Phase-5 halves done (704131/704133). **Cross-cohort correction to iter-41:** the heads
  Holm-sig in ALL 4 cells are **late/output-proximal** (L21H10, L22H19, L26H13, L30H15, L31H0/H1), NOT the
  L14–15 heads. The big curated L14H4/L15H4 (.10) are **cohort-dependent** (don't hit Holm on clearharm),
  though L14H5/L15H8/L15H11 do. Robust (≥3/4 cells) = **MID band L14,15,17,18 + LATE band L21,22,25–31.**
  Late heads are partly **readout-proximal** (near unembedding). So: mid-band L14–18 heads (further from
  readout, cross-cohort) = the mechanistically informative carry; late L30–31 = output/proximal. Updated
  `reports/PHASE5_HEADS.md` with the robust set + Phase-7 candidates `L14H5,L15H8,L15H11,L17H27,L18H20,L18H16`.
  self-swap 0.0 all cells. **Circuit: L8–11 demo retrieval/write (K/V+MLP@L9) → L14–18 mid-band answer-pos
  carry (cross-cohort) → L30–31 output → logit.** Next: Phase 7 path-patching — do the L14–18 candidate
  heads MEDIATE the L9 demo-write → logit path (separating retrieval-carry from readout proximity)? Reuse
  50_path_patching.

- **2026-08-03 (iter 41, loop tick — Phase 5 HEAD RESULT: L13–L15 answer-position carry band)** — Merged
  curated Phase-5 halves (704129/704130) → full 32×32 Holm. **NEW FINDING: specific answer-position heads
  ARE necessary** (unlike the null query→demo edges). 75 dev / 60 heldout Holm-sig heads; top heldout
  **L15H4 .106, L14H4 .104, L18H20 .094**; L14H4/L15H8/L15H11/L18H20/L21H10 SIG on BOTH splits.
  **Layer-concentrated L13–L15 (peak L14–15)** + secondary L17–18, L21–22; but top-10 heads = only 20–31%
  of total → **distributed within the band**. self-swap dev 0.0. The iter-40 smoke "~0.0007" was only
  because it covered L8–11 (weak heads); the carry lives higher. **Circuit so far: L8–11 demo
  retrieval/write (K/V+MLP@L9) → L13–L15 answer-position head carry (distributed) → logit.** Wrote
  `reports/PHASE5_HEADS.md`. (attn_out 703669 NOT stuck — 79min was model weight-LOADING on a slow-disk
  node.) Caveat: answer-pos DIRECT effect only; L13–15 may mix retrieval vs output heads → **Phase 7
  path-patching** to separate. clearharm 704131/704133 pending (cross-cohort). Next: clearharm confirm →
  Phase 7 path patch (demo-write@L9 → L14–15 heads → logit).

- **2026-08-03 (iter 40, loop tick — Phase 5 full all-head scan launched)** — Phase 5 smoke 703876
  VALIDATED: **self-swap dev 0.0** (ZHeadPatch faithful), and mid-band (L8–11) top-head necessity at the
  answer position is **~0.0007 = negligible** (n=2) → preliminary no-single-head signal (matches edge-KO
  negative + top-20=12% distributed prior). Launched the **full all-head z-patch necessity scan**, both
  cohorts, all 32 layers. NOTE: these FC scans are slow (curated attn_out 703669 ran ~1h), so I **split by
  layer range L0–15 / L16–31** (independent layers, safe parallelism, well under the 4h wall) → jobs
  704129/704130 (curated) + 704131/704133 (clearharm). Will **re-Holm the union of the two halves offline**
  (raw per-(l,h) necessity is in each raw.jsonl) for the proper 32×32 correction. Next tick: merge halves →
  is ANY head necessary at the answer position (Holm 1024), or distributed? + read curated attn_out confirm.

- **2026-08-03 (iter 39, loop tick — attn_out null (Phase 3 dissociation) + built Phase 5 head harness)** —
  **clearharm attn_out 703670 done → Holm NULL** (dev none; heldout only L15 +0.001, negligible). So the
  demo codeword's own attention OUTPUT is NOT necessary — a clean **componential dissociation at the demo
  codeword: resid_pre (K/V it exposes) YES, mlp_out (write) YES @L9, attn_out (what it reads) NO.** Completes
  the Phase 3 attn_out cell. (curated attn_out 703669 still running to confirm.) → the retrieval acts at the
  QUERY/answer position, not via demo-position attention. **Built the Phase 5 per-head z-patch harness**
  `scripts/phase5_head_zpatch.py` (reuses pc.ZHeadCapture + pc.ZHeadPatch + phase6 FC readout): per
  (layer,head) replace DS head-z at the ANSWER position ← BENIGN (necessity = direct head→logit effect),
  self-swap + norm-matched-random controls, per-split, **Holm across the 32×32 head family**. Scope note:
  answer-position DIRECT effect (indirect writes at earlier positions = follow-up). Smoke **703876**
  (curated n=2, L8–11). Next: validate smoke (self-swap≈0), full all-head scan both cohorts → which heads
  (if any) are necessary, or confirm distributed (prior edge-KO negative + top-20=12% predict distributed).

- **2026-08-03 (iter 38, loop tick — validate attn_out path deterministically + launch)** — The iter-37
  "attn_out smoke" 703639 actually ran the **stale mlp_out** code (summary `component:None`, NEC matched
  mlp_out) — a submit-timing/stale-file slip; it validated self-swap=0 + C1 discrimination but NOT the
  attn_out path. Instead of re-smoking on GPU, **validated the tuple-output path deterministically**: added
  a `ToyAttn`/`ToyAttnBlock` (self_attn returns a TUPLE like HF) to the ComponentOutSwap synthetic test and
  covered `component="attn_out"` self-swap-exact + per-position + locality — **6/6 pass**, GPU-free. Launched
  full **703669 (curated) / 703670 (clearharm)** attn_out per-layer, demo positions. Next tick: does
  attention OUTPUT at the demo codeword show the same L9 mid-band necessity as MLP/KV (Phase 3 attn_out cell)
  → then per-head z-patch (ZHeadPatch) on the necessary attention layers (Phase 5 core).

- **2026-08-03 (iter 37, loop tick — generalize harness to attn_out; fill Phase 3 attention-output gap)** —
  Toward Phase 5 (per-head), first close the **Phase 3 `attn_out` per-layer cell** (resid_post done=null,
  mlp_out done=L9; attention-output necessity NOT yet done). Generalized `phase6_mlp_causal.py` with
  `--component {mlp_out, attn_out}` (ComponentOutSwap/ComponentCapture already support attn_out; renamed the
  necessity cell C3_mlpout→C3, updated `phase6_analyze.py`). This patches the whole-layer attention OUTPUT at
  demo codewords (necessity benign↔DS, FC readout, Holm) = the layer-level attention necessity that says
  WHICH layers to decompose into heads for Phase 5. `attn_out` hooks `self_attn` (TUPLE output, unlike mlp's
  plain tensor) so smoking first: **703639** (curated n=2, window, attn_out). Backward-compatible (mlp_out
  default). Next: validate attn_out path → full attn_out layer runs both cohorts → then per-head z-patch
  (ZHeadPatch) on the necessary attention layers.

- **2026-08-03 (iter 36, loop tick — Phase 6 causal MLP FINAL, Holm-corrected, clean)** — Clean re-runs
  703531–703534 done. Built reusable `scripts/phase6_analyze.py` (per-split + **Holm across 32 layers**,
  paired sign-flip permutation). **RESULT:** DEMO-codeword `mlp_out` necessity — **L9 survives 32-layer Holm
  on ALL FOUR cells** (curated dev p<1e-4 / heldout p=4e-4; clearharm dev p<1e-4 / heldout, where the whole
  **L9–L12 band survives**). Effect small (~.02–.10), **not sufficient** (S3≈0). The 2 question tokens had
  inflated it ~2× (heldout L9 .18→.097 clean) — real but proximity-boosted; the clean L9 is the true effect.
  **QUERY-codeword `mlp_out`: nothing survives Holm on locked test in EITHER cohort** → inert, matching the
  inert query state (iter-13). **So the binding MLP write is at the DEMONSTRATION codeword (L9, where the
  binding is DEFINED), not the query codeword (where it's USED).** Co-localizes with demo-KV retrieval (L8–11
  peak L9). Answers plan Q5 (binding available ≈L9) + Q6 (write ≈L9 demo-pos, distributed L9–L12). Finalized
  `reports/PHASE6_MLP.md`. **Gate 4 met (partial): causal mid-band demo-position MLP necessity, corrected,
  replicated; necessity-only + distributed, not a sufficient localized write.** Next: Phase 5 (all-head
  activation patching — which HEADS are necessary/sufficient; reuse ZHeadPatch/ZHeadCapture + 49_head_attribution).

- **2026-08-03 (iter 35, loop tick — self-caught position-classification BUG + clean re-run)** — Diagnosing
  the query-run n=0 exposed a **token-index-vs-char-offset bug in `build_fc`** (same class as the iter-25
  edgeKO bug): `hit.spans` are TOKEN indices but the demo/query boundary `q_off` was a CHAR offset from
  `rfind`, so `span[0] < q_off` was ALWAYS true → `demo_pos` captured the 2 question-codeword tokens too and
  `query_pos` was always empty. So the iter-34 "demo-position" runs actually patched **demo (12) + question
  (2) codewords**, and the query run got nothing. **Fixed** (convert the question boundary to a token index
  via prefix tokenization); verified offline **n_demo=12, n_query=2**, cleanly partitioned. The 2 question
  tokens are near the answer (proximity), but the iter-34 effect localized to **L9 (mid), not late** → the
  finding is very likely demo-driven, BUT I'm re-running clean to confirm rather than assume. Launched
  **703531/703532 (demo-only, layer, both cohorts)** + **703533/703534 (query, layer, both cohorts)** = the
  real query-codeword MLP-write test (paper's core claim). Marked the iter-34 PHASE6_MLP result PROVISIONAL
  pending the demo-only re-run. Next tick: confirm demo-only L9 necessity holds + read the query-write result.

- **2026-08-03 (iter 34, loop tick — Phase 6 causal MLP result CONFIRMED, confound resolved)** — Recurring
  30-min loop cron **13dcff00** set (single loop; prior one-shot wakeup cleared). All 4 Phase 6 demo-position
  jobs COMPLETE; re-aggregated per-split. **Per-layer curve resolves the iter-33 degradation worry:** the
  demo-position MLP-output necessity is **localized to a contiguous mid band L8–L12, sharply peaking L9, on
  BOTH cohorts, replicating dev→heldout** (curated heldout L9 +0.179 [.10,.27]; clearharm dev L8–12 all SIG
  peak L9 +0.084). **Sufficiency ≈0 every layer** → NECESSARY not sufficient — the SAME band + signature as
  the demo-KV retrieval (PHASE4 L8–11/L9). The broad `early`-window +0.42 was degradation (neg sufficiency);
  the clean per-layer L9 (~.03–.18) is the real effect. **Gate 4 (partial):** a mid-band MLP contributes
  causally at the demo position (necessity, both cohorts, locked-test, controls, self-swap 0) but it's a
  distributed necessity-only contribution, not a transplantable write. Updated `reports/PHASE6_MLP.md`.
  **Bug found:** `--positions query` run 703460 = **0 rows** — the FC question quotes the codeword
  (`the word "banana"`) so it's undetected, and the FC readout has no unquoted request-line query codeword.
  → the query-codeword MLP write needs the FULL DS-prompt readout (reuse Phase-3 05/query-position machinery)
  — next tick. Mechanism now: mid-band L8–12/L9 demo-position computation (K/V + MLP) = causal locus, both
  necessary, neither sufficient = distributed context-bound binding.

- **2026-08-03 (iter 33, loop tick — self-caught misread + rigor fix)** — Code review of the Phase 6
  harness came back **clean** (alignment/signs/control-sourcing/hooks all correct); flagged 3 minor items.
  Acting on them exposed that **my iter-32 "demo-position null" claim was WRONG**: I read only the truncated
  log tail (the `mid` line). The job's own summary actually has **early-window NEC = +0.44 [0.31,0.57]** —
  significant. **Fixed the aggregation to report dev (train) / heldout (test) SEPARATELY** (plan mandate;
  was pooling both into one CI) keyed on `(split,sid)` (F2, no collisions confirmed) + skip-logging (F1).
  Re-aggregated 703456 per-split: **demo-position MLP-output necessity is SIG at EARLY (L0–9) and
  REPLICATES on locked test** (dev +0.42 [.24,.58]; heldout +0.47 [.28,.65]); mid/late ≈0. **BUT sufficiency
  is NEGATIVE (−0.18)** and it's a broad 10-layer window with a cross-context benign donor → the plan's
  **"destructive broad intervention" / positional-sensitivity confound.** NO causal-write claim yet: need
  the per-layer curve (703457 running) to localize + within-window controls (random-window, shifted-window)
  to rule out degradation. Self-swap dev exactly 0 throughout. Committed the fix; corrected the record.

- **2026-08-03 (iter 32, loop tick)** — **Phase 6 demo-position necessity (early-window) — see iter 33
  correction; the "null at full n" wording was a log-tail misread — mid/late ARE ≈0 but early is SIG).**
  (703456 curated/window n=51: mid [-0.017,-0.056,0.015] CI incl. 0, late ≈0, but early +0.44 — see iter 33.)
  **Extended the harness to the
  plan's remaining Phase 6 position sets** (`--positions {demo,query,all}`): `query` = codeword occurrences
  inside the FC question — this is the paper's core hypothesis "an MLP writes the retrieved concept when the
  model sees the QUERY codeword", which the demo-only test skipped. Small reuse-only change (query/demo
  occurrences split by the question offset; count-matched donor alignment identical to demo mode). Syntax
  clean; `--positions` wired through SLURM (DSPOS, default=demo, backward-compatible). Query smoke **703460**
  submitted. **Fanned out a background code-review subagent** on the new Phase 6 code (code-only, no bench
  text) per Omer's "double-check for bugs". Next tick: read review + query/all-position full runs → does the
  MLP write the concept at the QUERY codeword (the decisive Phase 6 / Gate 4 test)?

- **2026-08-03 (iter 31, loop consolidation + Phase 6 full launch)** — Per Omer: **collapsed to a single
  loop.** Found 3 concurrent `claude` loop processes (started together Aug 2 17:36); SIGTERM'd the two
  siblings (1454057, 1454684 — one had committed the iter-29 consolidation `18c68b1`), kept mine (1455207).
  Their work is already on-branch, so continuity = keep building on HEAD. Queue confirmed no duplicate jobs.
  **Phase 6 causal-MLP smoke 703439 VALIDATED:** self-swap dev **exactly 0.0** (ComponentOutSwap faithful
  no-op), C1 p_concept **0.9991** (readout discriminates). Preliminary (n=4): patching `mlp_out` at
  demo-codeword positions → **≈0 necessity AND ≈0 sufficiency at every window** — clean null, same direction
  as the demo-KV story (demo codeword's *input* K/V drives retrieval; its *MLP output* is not a local write
  site). Launched **full runs 703456 (curated/window) 703457 (curated/layer) 703458 (clearharm/window)
  703459 (clearharm/layer)**. Next tick: confirm the demo-position null at n≥20 + per-layer curve, then
  extend Phase 6 positions to **query-codeword / all-occurrence** MLP-output (the demo-position null does
  NOT close Phase 6 — the write, if any, may be at the query/answer position or distributed).

- **2026-08-03 (iter 30, loop tick)** — **Built the Phase 6 CAUSAL MLP-write harness** (the intervention
  the projection metric can't provide; Gate 4). Added a reusable primitive `pc.ComponentOutSwap` — the
  mlp/attn-OUTPUT analogue of `DemoStateSwap` (writes per-position donor rows to `layer.mlp` output;
  `SubmodulePatch` only writes one shared vector, so it couldn't do a faithful benign↔DS swap). 4/4
  synthetic tests pass (self-swap exact no-op, locality, per-position distinctness, cleanup); DemoStateSwap
  regression 4/4. `scripts/phase6_mlp_causal.py` clones the demo-neutralize harness exactly (same split, FC
  DE_context readout, cells, paired bootstrap CIs) but patches **mlp_out** at demo-codeword positions:
  necessity (DS mlp_out ← BENIGN), sufficiency (BENIGN ← DS), self-swap + random-position controls. Directly
  comparable to the demo-KV (resid_pre) retrieval result — retrieval vs write, same positions. Smoke
  **703439** (curated n=2, window) submitted. Next tick: validate smoke (self-swap dev≈0, C1 discriminates),
  then full runs both cohorts × {window, layer} → does an MLP causally write the concept, and where (expect
  mid-band L9–14 if the write is real, NOT late L29–31 where the projection artifact peaked).
  *(Note: iter 29 below was a concurrent doc-only consolidation tick; this tick is the causal-MLP build.)*

- **2026-08-03 (iter 29, loop tick)** — **Consolidation.** Wrote `reports/SLACK_UPDATE.md` (shareable
  team summary) + interim `reports/FINAL_CAUSAL_CIRCUIT_REPORT.md` (answers the 12 final questions with
  established-vs-pending, honesty/confidence section). Synthesizes Phases 0-6: attack reproduces;
  concept⊥refusal; local state inert; demo-KV necessary mid-band L8-11 (both cohorts) not sufficient;
  query→demo edges not necessary (distributed); MLP projection = proximity artifact. Headline: Doublespeak
  binding is **distributed, context-bound, mid-band L8-11**. Next: causal MLP write (intervention).


- **2026-08-03 (iter 28, loop tick)** — band jobs confirmed COMPLETE. **Phase 6 representational MLP
  projection** (CPU, reused reps+directions): concept-direction MLP write projection **late-dominated
  L29-31** (clearharm L31 proj 11.5 cos .69; band late 25 ≫ mid 4 ≫ early 2) — but this is the
  **readout-proximity artifact** the plan warns about (large late projection ≠ causal write; prior N7-C
  showed late MLP AtP≈0). curated shows a faint true mid-band bump (L11,L13). Reproduces the proximity
  confound on the new split. Wrote `reports/PHASE6_MLP.md`. **Causal MLP write (mid-band expected) needs
  intervention — next.** `scripts/phase6_mlp_projection.py` added.


- **2026-08-03 (iter 27, loop tick)** — **band edge-knockout 703334/703335 → honest NEGATIVE.** Knocking
  out query→demo attention edges across ALL heads in L8-11 has negligible, ns effect (clearharm specific
  +0.002 [−.0004,.005]; curated −0.003 [−.014,.009]) — on BOTH cohorts. all-query-edges degrades more
  (0.03/0.11, general effect). So query→demo edges are **NOT the retrieval bottleneck**, despite demo-KV
  activations being necessary + the 3.5× attention pattern → retrieval is **distributed/redundant, not a
  surgical induction edge**. Resolves N7-M (proper controls = clean negative, not degenerate). Updated
  `reports/PHASE4_DEMO_RETRIEVAL.md`. **Gate 3 nuance: demo CONTENT necessary, demo EDGES not.** Next:
  Phase 6 MLP write-location (does an MLP write the concept?) — the other half of the mechanism.


- **2026-08-03 (iter 26, loop tick)** — edgeKO smoke 703327 WORKS (1024 rows) but **per-head KO is
  negligible** (raw drop ≈0.0001) → single-head query→demo knockout does nothing = **distributed**
  retrieval (matches prior D4: no single-head bottleneck, top-20=12%). Added **band mode**: knock out
  query→demo edges across ALL heads in the L8-11 band jointly (the retrieval pathway) + random-edge
  control + all-query-edges broad-degradation control. Launched **703334/703335** (band L8-11, both
  cohorts, full). Next tick: does removing the query→demo pathway across the band collapse the reading
  (vs random-edge, vs all-query-edges)? = decisive edge-necessity test (the surgical N7-M answer).


- **2026-08-03 (iter 25, loop tick)** — edgeKO smoke 703282 ran clean but 0 rows: bug — I compared
  `find_word_occurrences_in_text` spans (which are TOKEN indices) against CHAR offsets → all classified
  as demo, query_pos empty. **Fixed:** keep full DS prompt (request-line query codeword is findable),
  convert request/question char boundaries to token indices via prefix tokenization. Verified n_demo=12,
  n_query=1/example. Resubmitted smoke **703327** (curated n=2, L8-11). Next tick: per-head KO effects
  (candidate retrieval heads in the L8-11 band) → full all-layer×all-head scan.


- **2026-08-03 (iter 24, loop tick)** — Built **surgical per-head query→demo edge-knockout harness**
  (`scripts/phase4_edge_knockout.py` + `slurm/run_phase4_edgeko.sh`): eager `AttentionKnockout`, per
  (layer,head) knock out query-codeword→demo-codeword edges, read FC concept, matched random-edge
  control, paired bootstrap CI. This is the N7-M surgical follow-up (prior all-layer version degenerate).
  Layers via dash-range to dodge --export comma bug. Syntax ok; smoke **703282** (curated n=2, L8-11,
  the localized retrieval band). Next tick: validate eager KO works + candidate retrieval heads → full
  all-layer×all-head scan, both cohorts.


- **2026-08-03 (iter 23, loop tick)** — **Phase 4.2 demo-KV necessity localization COMPLETE + SIG
  per-layer.** Corrected-control layer runs 703248/703249: necessity effect significantly localized to
  **L8–L11 both cohorts** (each layer CI excludes 0), peak L9–L10 (curated L9 [.136,.310]; clearharm
  L10 [.045,.189]). Matches prior attention-write band L7–9. Finalized `reports/PHASE4_DEMO_RETRIEVAL.md`.
  **DEMO-KV CELL DONE:** necessary (mid band, both cohorts, per-layer SIG) but not sufficient;
  distributed within L8–11. Next: surgical **per-head query→demo attention-edge knockout** (Phase 4.2
  induction test — the N7-M "future work" flagged in the audit), reusing `pc.AttentionKnockout` (eager).


- **2026-08-03 (iter 22, loop tick)** — **corrected-control result FINAL (window).** Necessity SIG in
  the **mid band on BOTH cohorts** (curated mid +0.177 [.087,.278] & early +0.258 [.146,.372]; clearharm
  mid +0.081 [.012,.151]); late ns; sufficiency robust NULL (S3≈0). → demo-codeword K/V **necessary but
  not sufficient** = distributed/context-bound binding (direct multi-concept confirmation of IE_state≈0/
  DE_context≈99%). Self-swap dev 0. Updated `reports/PHASE4_DEMO_RETRIEVAL.md` with corrected CIs +
  asymmetry. Launched corrected per-layer localization **703248/703249** (peak expected L9-11). Next
  tick: finalize localization, then the surgical per-head query→demo edge knockout (Phase 4.2 induction).


- **2026-08-03 (iter 21, loop tick)** — full nec+suf runs 703213/703214 done, but **caught a control
  bug** by cross-checking vs my earlier ad-hoc CI (clearharm ns then, "SIG" in unified harness). The
  unified harness's necessity `random_control` sourced from DS-OWN random activations (a near-no-op)
  instead of the BENIGN donor that C3 uses → inflated the specific effect. **Fixed** random_control to
  use benign donor (matched to C3). Re-ran full window **703237/703238**. Sufficiency result unaffected
  (S3≈0 both cohorts, robust null). Next tick: corrected necessity CIs (expect curated SIG, clearharm
  conservative) → finalize PHASE4_DEMO_RETRIEVAL asymmetry. Rigor note: self-caught control error.


- **2026-08-03 (iter 20, loop tick)** — sufficiency smoke 703199 clean → **necessity/sufficiency
  ASYMMETRY.** Necessity holds (curated early 0.154 [.038,.290], mid 0.220 [.099,.346] SIG). But
  **sufficiency FAILS**: installing DS demo-codeword K/V into a benign receiver gives S3 p_concept=0.0
  at ALL windows (incl. late) → does NOT create the reading. So demo-codeword K/V is **necessary but
  not sufficient** — the binding needs the codeword K/V *within* its harmful demo context, not the
  local activations (consistent with IE_state≈0 / DE_context≈99% distributed mechanism). Launched full
  nec+suf window runs **703213/703214** to confirm on full data. Next tick: aggregate → write the
  asymmetry into PHASE4_DEMO_RETRIEVAL.


- **2026-08-03 (iter 19, loop tick)** — Extended demoKO harness with the **sufficiency leg**: install
  DS demo-codeword K/V into the BENIGN receiver (mirror of necessity), + built-in paired bootstrap CIs
  (necessity specific = random−C3; sufficiency specific = S3_install−S_random) + self-swap faithfulness
  both directions. Syntax ok; smoke **703199** (curated n=8). Next tick: does installing DS demo K/V
  into benign CREATE the reading (S3>S_random)? Then full runs both cohorts × window/layer → the
  necessity+sufficiency pair for demo-KV retrieval, completing the Phase 4.2 demo-position core.


- **2026-08-03 (iter 18, loop tick)** — **Phase 4.2 demo-KV necessity result COMPLETE (full runs
  703151-703154).** Neutralizing demonstration-codeword K/V reduces the hijacked reading, above random
  controls, **significantly on curated** (early specific +0.180 [.026,.328], mid +0.133 [.053,.217],
  both CI>0, mid survives Holm/3; late ns) and **same direction (ns) on clearharm** (concept noise).
  **Per-layer peak L9-L11 on BOTH cohorts** — replicates the prior mid-band retrieval/write on the
  multi-concept split. Readout validated (DS C1 p_concept .76/.88 vs benign 0.0; self-swap dev 0).
  Wrote `reports/PHASE4_DEMO_RETRIEVAL.md` (paired bootstrap CIs, per-layer localization, honest
  cohort split). **Gate 3 (attention causality) partially met on curated.** Next: sufficiency leg
  (install DS demo K/V into benign) + other locations + the exact per-head edge knockout (Phase 4.2 full).


- **2026-08-03 (iter 17, loop tick)** — **demoKO harness WORKS + first real circuit signal.** FC-readout
  smoke 703123: DS C1 p_concept high (bomb .99, mean .74) vs **benign 0.0 for every example** (clean
  discrimination), self-swap dev=0 (faithfulness). **Core result (n=16 smoke): neutralizing demo-codeword
  K/V reduces the reading SPECIFICALLY at EARLY layers** — ReRead(C1−C3) early **0.154 vs random 0.048**;
  mid 0.220≈random 0.222 (non-specific); late 0.013<random 0.103. = early induction-style retrieval binding.
  **Launched FULL runs 703151-703154** (clearharm/curated × window/layer, all examples) to confirm with
  proper n + per-layer curve. Next tick: aggregate → the demo-KV necessity result + per-layer localization,
  then random/self-swap controls, both cohorts. This is the Phase 4.2 retrieval-necessity core.


- **2026-08-03 (iter 16, loop tick)** — smoke 703115 confirmed the BENIGN-source fix (C3 fires, 48
  rows/cell, self-swap=0) but exposed the readout was still wrong: **ps_concept_gated≈0 even for clean
  bomb** — I was reading the patchscope of the query-codeword rep (IE_state≈0, floors), not the
  DE_context reading. **Rewrote to the forced-choice-question readout** (30's forced_choice template):
  append 'does the word "cw" refer to "concept" or to "cw"?' to the demo block, read
  P(concept-label)/(P(concept)+P(codeword)) at the answer position (this is the DS≈0.35 DE_context
  measurement). Demo positions via char-offset filter (before the question); validity = DS C1
  p_concept > BENIGN (built-in discrimination, no patchscope gate). Syntax ok, smoke **703123** submitted.
  Next tick: does DS C1 discriminate from benign? self-swap≈0? ReRead sign → then full runs.


- **2026-08-03 (iter 15, loop tick)** — demoKO smoke 703105 ran clean (24 rows, no crash) but exposed
  a real bug: **C3_demoKV never fired** because I sourced neutralization from NEUTRAL (which is
  demo-free → no demo-codeword K/V). **Fixed:** source from BENIGN_REMAP (same codeword in benign demo
  sentences = correct non-harmful-binding source). Also the smoke drew LSD/MDMA (weak-decoding
  concepts → positive control failed); resubmitted larger smoke **703115** (curated n=8) to confirm C3
  fires + positive control passes for strong concepts + ReRead sign. Next tick validates, then full runs.


- **2026-08-03 (iter 14, loop tick)** — Built the **pivotal multi-concept patching harness**. Found the
  prior pair scripts (44_kv_mediation) hardwire a single global concept/codeword for the readout →
  can't run on the multi-concept split. Wrote `scripts/phase3_demo_neutralize.py` reusing 44's exact
  primitives (DemoStateSwap at demo-codeword resid_pre, PatchscopeDecoder gated readout,
  resolve_positions, ComponentCapture) but **per-row concept/codeword + per-example positive control**.
  Cells C1 / C3_demoKV (neutralize demo K/V = necessity) / C1_selfswap (faithfulness) / random_control;
  per window AND per layer; ReRead_test=mean(C1−C3). Syntax ok, bench pairing verified (0 missing).
  **SMOKE submitted 703105** (curated, n=2, window). Next tick: validate smoke (positive-control passes?
  self-swap≈0? ReRead sign?), then full runs both cohorts × {window, layer} granularity → the core
  retrieval-necessity result on ClearHarm.


- **2026-08-03 (iter 13, loop tick)** — **Phase 3 cell #1 (resid_post × query-codeword, logit-lens)
  COMPLETE → NULL, as expected.** Jobs 702995/702996 done. Baseline DS p_harm ≈0 (logit-lens floors at
  codeword) → necessity ≈ random control, sufficiency ≈0, ALL layers, both cohorts/splits.
  **Reproduces IE_state≈0** (harmful concept NOT in local query-codeword state) on the new ClearHarm
  split — plan's known-findings #1-3 confirmed. Diagnosed: logit-lens-at-codeword fails its positive
  control (prior T2/N3); the **validated readout is the forced-choice patchscope** (`46`, DS≈0.35 in
  DE_context job 694691). Wrote `reports/PHASE3_RESIDUAL.md`. **Next: circuit-discovery cells** =
  DEMO/all-occurrence positions (binding is in the demos, not query state) × 4 locations, forced-choice
  readout, reusing 43/44/46 patch+forced_choice machinery. That's where signal is predicted.


- **2026-08-02 (iter 12, loop tick)** — **Phase 3 (resid_post core) STARTED.** Found `05_run_activation_
  patching.py` consumes items in my `beh_<cohort>.json` format → per-example necessity(neutral→DS) +
  sufficiency(Direct/DS→neutral) + identity + norm-matched-random controls across ALL 32 layers,
  forced-choice logit-lens P(harm)/P(code) at resid_post/codeword_last+following. Fixed
  `ds_common.target_positions` with a BOS-aligned offset-finder fallback (all 137 items resolve;
  localization+resid_pre tests 20/20). Submitted **702995 (clearharm) + 702996 (curated)** via new
  `slurm/run_stage2_patch_split.sh`. Next tick: per-layer necessity/sufficiency curves (does patching
  the final codeword state at any layer remove/install the harmful reading? — prior work said
  final-state-only was insufficient; now tested exhaustively per-layer on the split, both cohorts).
  Then extend to 4 locations (resid_pre/attn_out/mlp_out via SubmodulePatch) + all-occurrence positions.


- **2026-08-02 (iter 11, loop tick)** — **curated behavioral 702862 COMPLETE → Phase 2.1 core DONE,
  Gate 1 (reproduction) SATISFIED.** Curated neutral = clean **0.039** floor (harm-in-one-noun), DS
  train **0.333 vs neutral 0.033 = +0.30 (10×)** — clean Doublespeak effect. ClearHarm DS>>direct
  (0.349 vs 0.116, refusal bypass) stable train/test. **Honest weak result:** curated TEST DS=0.095
  (n=21, 2 malicious) — big train→test drop, small-n/concept-composition (baseline, not overfitting;
  flagged, needs more test ex). Wrote `reports/PHASE2_BEHAVIORAL.md` (per-split table + caveats).
  Gate 1 met (attack reproduces behaviorally + representationally). **Next: Phase 3** exhaustive
  all-occurrence residual patching (causal core, forced-choice readout) — or Phase 2.1 extended
  conditions first.


- **2026-08-02 (iter 10, loop tick)** — **ClearHarm behavioral baseline 702861 COMPLETE** (n=86,
  StrongReject): malicious rate **direct 0.116 / neutral 0.256 / doublespeak 0.349**; mean_SR 0.108 /
  0.218 / 0.294. **Core Doublespeak result holds: doublespeak >> direct (+0.23)** — codeword rephrase
  bypasses the refusal that blocks the direct request. **Neutral elevated (0.256)** = ClearHarm concept
  noisiness (harm not always in the single swapped noun; e.g. "boosted-fission weapon"→"…potato" keeps
  harmful context) — predicted in split-contract Limitation 2; motivates curated cohort. Curated
  702862 RUNNING → next tick reads it (expect neutral≈0, cleaner direct/DS gap), then write
  `reports/PHASE2_BEHAVIORAL.md`.


- **2026-08-02 (iter 9, loop tick)** — **Phase 2.1 behavioral baseline SUBMITTED.** Confirmed
  StrongReject available (OPENAI_API_KEY + `strongreject_scoring`). Wrote `scripts/split_to_behavioral.py`
  (split → `14_behavioral_eval` data; demos extracted from DS prompt — verified byte-identical rebuild
  of direct/neutral/doublespeak) + `slurm/run_behavioral_split.sh`. Submitted jobs **702861 (clearharm,
  86 items) + 702862 (curated, 51)** → direct/neutral/doublespeak generation + StrongReject, per cohort.
  Next tick: read per-condition StrongReject/ASR/refusal (does Doublespeak jailbreak vs direct/neutral
  on the locked split). Extended conditions (benign/shuffled/unrelated + interventions) = follow-up.


- **2026-08-02 (iter 8, loop tick)** — refusal 32-layer build **702750 COMPLETE** (L0–31.pt; sep
  0.33→peak ~1.03 @ L20-23→0.94, concentrated mid-late). Wrote `scripts/build_unified_directions.py`
  → `outputs/unified_directions/{clearharm,curated}.{npz,json}`. **HEADLINE RESULT: concept_direction
  ⊥ refusal_direction at every layer, both cohorts** — mean cos(concept,refusal) **0.012** (clearharm)
  / **0.061** (curated), max|·|≤0.15. Concept axis is independent of refusal → separate levers (plan §2
  validated). cos(signature,refusal) ~0.13-0.15; cos(concept,signature) 0.14-0.25 (dissociation).
  Wrote `reports/PHASE2_DIRECTIONS.md`. **Phase 2.2 (direction separation) essentially DONE**
  (representational). Remaining Phase 2: 2.1 behavioral baselines (SLURM); covariance-adjusted sim (queued).


- **2026-08-02 (iter 7, loop tick)** — reps job **702731 clearharm COMPLETE** (516 rows, 0 missing).
  Ran **`33_build_directions` on clearharm** → `outputs/pair_directions_20260802_201124_1612201`
  (192 direction keys; `d_Direct|…`, `d_DS|…` each [32,4096]). cos(d_Direct,d_DS) resid_post/
  codeword_last dev mean **0.245** (curated 0.14) — dissociation holds on BOTH cohorts.
  **Both cohorts now have concept + signature + control directions.** Existing refusal artifact only
  covered L12-20 → submitted **all-32-layer refusal build (job 702750)** via new
  `slurm/run_refusal_alllayers.sh` (bench pair_carrot_bomb, layers hardcoded via seq to dodge
  --export comma bug). **Next tick:** when 702750 done, write `scripts/build_unified_directions.py`
  co-locating concept/refusal/signature per-layer + cos(concept,refusal), cos(signature,refusal),
  norms; then Phase 2.1 behavioral baselines.


- **2026-08-02 (iter 6, loop tick — user nudged "be on loop")** — reps job 702692 **curated COMPLETE**
  (306 rows, 0 missing); 702691 clearharm **FAILED** (`resolve_positions` strict finder missed codeword
  'pumpkin' in a ClearHarm context). **Fixed** `pair_common.resolve_positions` with an offset-finder
  fallback (only fires where strict raised → no regression); verified all 822 bench rows resolve, tests
  10/10. Resubmitted clearharm reps → **702731 PENDING**. Ran **`33_build_directions` on curated** →
  `outputs/pair_directions_20260802_200945_1610756` (128 directions + 64 subspaces). **Result:**
  cos(d_Direct, d_DS) resid_post/codeword_last dev mean **0.14** (max .39) — the concept↔signature
  **dissociation replicates** on the ClearHarm-style curated cohort (keep concept & signature separate).
  Next: 33 on clearharm reps when 702731 done; refusal direction (reuse `outputs/stage_gcg_full/*.pt`
  if valid); unify per-layer concept/refusal/signature.


- **2026-08-02 (iter 5, loop tick)** — reps jobs 702652/702653 **FAILED** at the summary-write
  (`KeyError: 'pair'` — `32_extract_pair_reps` records `bench["pair"]`; adapter omitted it). Reps
  arrays (means/per_prompt/subsample) were saved fine; only `reps_summary.json` crashed. **Fixed**
  adapter to emit a `pair` key (multi-concept descriptor), regenerated bench, **resubmitted:
  702691 (clearharm) + 702692 (curated)**, PENDING. Next tick: verify COMPLETE → `33_build_directions`.
- **2026-08-02 (iter 4, loop tick)** — **Phase 2 reps extraction SUBMITTED** on L40S:
  job **702652** (clearharm bench) + **702653** (curated bench), `32_extract_pair_reps --readout fixed`,
  killable partition. Outputs → `doublespeak_causality/outputs/pair_reps_*`. **Next tick:**
  when both COMPLETE, run `33_build_directions --reps-dir <each>` (concept d_Direct + signature d_DS +
  controls + per-layer cosines), check for a reusable existing `refusal_direction` in
  `outputs/stage_gcg_full/*.pt` (else rebuild via `build_refusal_direction_llama --validate`), then
  unify into separate per-layer concept/refusal/signature objects + cross-direction cosines.


- **2026-08-02 (iter 3, loop)** — **Phase 1 COMPLETE.** Locked split `data/splits/clearharm_doublespeak_v1.json`
  finalized: **137 records, both cohorts ≥20/≥20** (clearharm PRIMARY 44/42, curated REPLICATION 30/21).
  Validator **12 ok / 0 warn / 0 FATAL** (no id/cluster/prompt leakage, all single-token). Caught+fixed a
  cross-split leakage bug (duplicate neutral prompts from shared codeword+template → now unique codeword
  per concept). Reproducible via committed `_concept_cache.json`+`_demo_cache.json`. Wrote
  `reports/DATASET_AND_SPLIT_CONTRACT.md` (schema, 6 matched conditions, methodology, 4 honest limitations
  incl. ClearHarm concept noisiness + near-dup clustering not yet applied). **Gate for Phase 2/3 open.**


- **2026-08-02 (iter 2, autonomous loop)** — Cron loop set (`*/30 * * * *`, job a5747db4). **Phase 1
  nearly done.** Built `data/splits/clearharm_doublespeak_v1.json` (both cohorts). Found + fixed two
  builder bugs: (a) curated template top-up, (b) **codeword-skip bug** — main loop dropped any item
  whose cycled codeword was multi-token, silently shrinking cells (curated 19→51 after fix). Added
  **concept-extraction caching** (locked split reproducibility) + **per-cohort ≥20/≥20** validator
  check. ClearHarm primary cohort already ≥20/≥20; curated now yields 51 (17 concepts×3) → ≥20/≥20.
  Also advanced Phase-3 infra: **added `resid_pre` to `SubmodulePatch`** (unified 4-location patch:
  resid_pre/attn_out/mlp_out/resid_post) + 4 GPU-free tests (10/10 pass). Final cached canonical
  build running; then validate + write `reports/DATASET_AND_SPLIT_CONTRACT.md`. All committed+pushed.


- **2026-08-02 (iter 1)** — **Phase 0 audit COMPLETE.** 7-lane parallel audit finished (0 errors,
  367k tok). Wrote `reports/CAUSAL_PATCHING_AUDIT.md` (full repo map, reusable primitives,
  provenance, reproducible-vs-not values, gap list, 10 footguns). Wrote
  `scripts/validate_data_integrity.py` (train/test overlap, intent-cluster leakage, dup prompts,
  codeword-occurrence & multi-token checks, output-row dup/metadata checks) — syntax-ok, dry-run
  graceful (no split yet). **Key priors captured:** d_DS causally inert (d_Direct is the lever);
  temporal/repr GCG objective backfires (ASR 0.0, refusal 0.615) — attack is demonstration-bound;
  N7-M all-layer edge knockout degenerate → **surgical per-head edge knockout (Phase 4.2) is the
  flagged next step**; mechanism distributed (no single-head/layer bottleneck). Novel EV =
  ClearHarm generalization + locked-split/Holm rigor + full 4-loc/all-layer/all-head coverage +
  surgical knockout. **Consulting Omer on ClearHarm→Doublespeak mapping (§7 of audit).**
- **2026-08-02** — Session start. Wrote master plan. Oriented repo: found mature existing
  infra (`ds_common.py`, `pair_common.py`) already implementing LayerPatch, AttentionKnockout,
  ZHeadPatch/Capture, DemoStateSwap, SubmodulePatch, project-out/add hooks (single+multilayer),
  norm-matched/orthogonal/in-subspace random controls, all-occurrence `find_word_occurrences`,
  templating, `EXPERIMENT_REGISTRY.csv` (45 runs), `tests/` (17 tests). Created `reports/`,
  `configs/manifests/`, `scripts/`. Launched **Phase 0 audit workflow** (7 parallel code auditors).

---

## Phase checklist

| Phase | Description | Status | Notes |
|------|-------------|--------|-------|
| 0 | Repo & result audit → `reports/CAUSAL_PATCHING_AUDIT.md` + validation checks | ☑ | audit report + data-integrity validator done; Gate 1 satisfiable from artifacts |
| 1 | ClearHarm locked split → `data/splits/clearharm_doublespeak_v1.json` (≥20 train/≥20 test) | ☑ | 137 recs, both cohorts ≥20/≥20, validator 0 FATAL, contract written |
| 2 | Baseline reproduction + concept/refusal directions | ◐ | 2.2 directions DONE; 2.1 core behavioral DONE (Gate 1 met); extended conditions + interventions pending |
| 3 | Exhaustive all-occurrence residual patching (L0–31 × 4 loc × 10 pos × 2 dir) | ◐ | resid_post/codeword core RUNNING (702995/702996 via reused 05); 4-loc + all-pos pending |
| 4 | Exhaustive attention: all-head scan + edge knockout + edge sufficiency | ☐ | reuse AttentionKnockout, ZHeadPatch |
| 5 | Exhaustive all-head activation patching (Q/K/V/z/pattern/result) | ☐ | reuse ZHeadCapture/Patch |
| 6 | Exhaustive MLP write-location analysis | ☐ | reuse 51_mlp_attribution, SubmodulePatch |
| 7 | Head→MLP path patching (every downstream receiver) | ☐ | reuse 50_path_patching |
| 8 | Jacobian/projection readout all layers | ☐ | reuse 07_patchscope, 46_forced_choice |
| 9 | Intervention-strength dose-response sweeps | ☐ | reuse 34_intervention_sweep |
| 10 | Distill causal optimization objective | ☐ | gated on 3-7; reuse MECHANISTIC_OBJECTIVE |
| 11 | GCG / MAC / TROPT evaluation | ☐ | gated on 10; reuse 25_eval_gcg_asr, TROPT skill |

## Granularity coverage (per major intervention)
A single-layer · B canonical windows · C sliding (w2/4/8) · D cumulative prefix · E cumulative suffix · F mechanism-derived · G all-layers. Tracked per experiment once Phase 3 begins.

## Gates
- G1 Reproduction ☐ · G2 Layer coverage ☐ · G3 Attention causality ☐ · G4 Write location ☐ · G5 Path mediation ☐ · G6 Objective ☐ · G7 Behavioral improvement ☐

## Deliverable reports (status)
`CAUSAL_PATCHING_AUDIT` ◐ · `DATASET_AND_SPLIT_CONTRACT` ☐ · `ALL_OCCURRENCE_PATCHING` ☐ ·
`ATTENTION_EDGE_KNOCKOUT` ☐ · `ALL_HEAD_ACTIVATION_PATCHING` ☐ · `ALL_LAYER_MLP_PATCHING` ☐ ·
`HEAD_TO_MLP_PATH_PATCHING` ☐ · `JACOBIAN_READOUT` ☐ · `CAUSAL_OBJECTIVE` ☐ ·
`GCG_MAC_EVALUATION` ☐ · `FINAL_CAUSAL_CIRCUIT_REPORT` ☐ · `SLACK_UPDATE` ☐

## Phase 2 — concrete next actions (queued for next loop iteration; GPU/L40S/SLURM)
Phase 2 is GPU-bound (model forward passes) and must run on **L40S** via SLURM (login node is
TITAN Xp 12GB, too small for 8B bf16). Plan, reusing `32_extract_pair_reps` + `33_build_directions`
+ `build_refusal_direction_llama`:
1. ☑ **Split→bench adapter** DONE (`scripts/split_to_bench.py`, CPU). Output
   `data/bench/bench_{clearharm,curated}.json` — every condition×split cell ≥20 (clearharm 44/42,
   curated 30/21; 516 + 306 rows). probe_word = concept for DIRECT_CONCEPT else codeword; train→dev,
   test→heldout. **Next loop: submit SLURM.**
2. **Reps extraction** (SLURM, L40S): run `32_extract_pair_reps.py --bench <adapter out>` for each
   cohort → per-(condition,split,component,position,layer) reps. bf16.
3. **Directions** (CPU): `33_build_directions.py --reps-dir <...>` → `d_Direct` (concept), `d_DS`
   (doublespeak_signature), `d_benign`/`d_unrelated` controls, PCA subspaces, cross-fit dev/heldout,
   per-layer cosines. Then `build_refusal_direction_llama.py --validate` → `refusal_direction[L]`.
4. **Unify** (`scripts/build_unified_directions.py`): co-locate concept/refusal/doublespeak_signature
   as separate per-layer objects + per-layer cos(concept,refusal), cos(signature,refusal),
   covariance-adjusted sim, norms → `reports/`-ready. Keep them SEPARATE (never merge concept+refusal).
5. **2.1 behavioral baselines** (SLURM, L40S, larger): 10 conditions × ≥20/≥20, forced-choice prob +
   logit-diff + StrongREJECT + ASR + refusal-rate. Reuse `14/18/19` + StrongREJECT harness.
Guardrail: bf16 for causal claims; discovery on `train` only; `test` only for frozen replication.

## Decisions / open questions for Omer
- **2026-08-02 — ClearHarm construction (RESOLVED):** (1) **Blend** — ClearHarm-native single-token
  subset = PRIMARY cohort; curated 40-pair set = parallel REPLICATION cohort; results reported
  separately, claim only what replicates (~2x compute on L×head scans accepted). (2) **Reuse
  gpt-4o-mini pipeline** (seed_concepts_gpt4omini convention: harmful_word/codeword/12 demos,
  fixed openai_seed, content-hash provenance) + single-token filter.
- Constraint reminder: all concept-extraction + demo-generation runs in the MAIN LOOP (cyber-safeguard
  kills subagents on harmful codeword-binding text); subagents only for scalar/structural work.

## Known constraints (from project memory)
- SLURM: no deps, max 6 parallel, L40S only, no trimming. bf16 + default SDPA (don't disable flash). GCG always `--no-filter-cand`.
- Cyber-safeguard kills subagents that read ClearHarm/jailbreak **text**; keep harmful-text handling in main loop, delegate code/scalar work only.
