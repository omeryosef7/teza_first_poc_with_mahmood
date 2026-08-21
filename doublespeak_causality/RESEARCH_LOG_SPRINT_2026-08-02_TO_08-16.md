# Doublespeak Causality — Unified Research Log (2026-08-02 → 2026-08-16)

**What this is.** A single, self-contained research-log narrative of the *entire* sprint on the
`behavioral-causality-sprint` branch, from **Sunday 2 August 2026** (the sprint's first commit,
`3cb44050 Phase 0: master plan`) through **16 August 2026** (`dceab3e8`; the last substantive commit is `d25a81db`, Phase 10 complete). It is written so an
external reader — human or LLM — with no repo access can understand the goal, the method, every headline
number, the corrections we made to our own work, and what is still open. It supersedes and folds in the
prior partial summaries (`SPRINT_2026-08-02_TO_08-05_FULL_SUMMARY.md`,
`SPRINT_SINCE_2026-08-02_COMPREHENSIVE.md` [→08-06], `SPRINT_SUMMARY_2026-08-02_TO_08-09.md`,
`docs/ASYMMETRY_FINAL_SYNTHESIS.md`, `docs/SECTION20_RESULTS.md`,
`docs/ROLE_CONFUSION_DOUBLESPEAK_CAUSAL_SYNTHESIS.md`) **and its own predecessor
`RESEARCH_LOG_SPRINT_2026-08-02_TO_08-14.md`, which stopped at commit `1e364973` and is now
superseded in full by this file.**

**⚠ Read this first: there are two "Section 20"s on this branch.** From 2026-08-14 two sprints ran
*concurrently on the same branch*, and their commits interleave in `git log`. **Asymmetry §20.x**
(`docs/ASYMMETRY_SPRINT_PLAN_2026_08_11.md` §20 → `docs/SECTION20_RESULTS.md`) is the *bounding-the-negatives*
programme of Parts G and I. **Role-probe §20** (`docs/ROLE_PROBE_NEXT_SPRINT_PLAN.md` §20 "REQUIRED
DELIVERABLES" → nine files under `reports/`) is the deliverable list of the role-confusion sub-sprint in
Part J. The rule adopted in `22c52931`, and used throughout this document: **"20.x" always means the
asymmetry plan; anything naming `reports/`, Gate 1, Bombness, role probes, or Phases 1–10 belongs to the
role-probe sprint.** Neither renames the other; they touch disjoint files.

**Verification provenance.** Every quantitative claim in the Aug-02→09 part was cross-checked against the
committed raw outputs (`outputs/*/summary.json`, `*.json`, `raw.jsonl`) — first by a 14-auditor pass, then a
7-agent re-verification, then two 12-agent adversarial audits (`wf_8333d36e`, `wf_383ca171`), and the
machine-regenerated claim table (`reports/CLAIM_AUDIT_TABLE.md`: **95 claims, 77 VERIFIED, 0 CHECK-FAIL, 173
numeric recompute checks / 0 failures**). The Aug-09→14 part (Next-Sprint, Asymmetry Sprint, Section 20) was
re-verified for this log by a 4-agent workflow (`wf_92ba16b8`) that re-opened the committed JSON for each
headline number. **Revision 2 (2026-08-14):** the whole document was then re-audited end-to-end by a
14-agent completeness + soundness workflow (`wf_9c6abc32`) whose findings are in
`RESEARCH_LOG_AUDIT_2026-08-14.md`; 17 numeric/scope defects were corrected and 15 omitted results added.
Everything that pass changed is marked **[c2]** inline. **Revision 3 (2026-08-15) — this revision:** the
**164 commits** between `1e364973` and `aba6b69b` (Parts I and J, plus every correction they force on Parts
A–H) were read by a 19-agent workflow (`wf_e6bf3b59`, 737 tool calls): nine readers over disjoint
deliverable clusters, nine adversarial verifiers that re-opened the cited JSON/CSV for **122 findings**
(108 CONFIRMED, 8 CORRECTED, 6 OVERSTATED, 0 fabricated), and a completeness critic that walked the full
commit range and the `outputs/` trees for work no reader had covered. Everything new or changed in this
revision is marked **[c3]**; where a verifier corrected a reader, this document carries the *verifier's*
number. **Revision 4 (2026-08-16), marked [c5]:** a 7-agent panel (`wf_662fa693`) reconstructed the research
*flow* from the plan documents and git history, enumerated **all 188 named gates/phases/sections** with a
single verdict each, ranked every result under four independent lenses (novelty / evidence / what changed our
own minds / transferable methodology), and adjudicated the merge adversarially. Output: the new **§0.1–§0.4**
front block. **Two of its findings were verified directly against the artifacts and are material corrections
to headline framing** — §10's specificity result does not reproduce on its own frozen test split, and a
significant concept-circuit behavioural effect on `cohort_clearharm_test` appears nowhere in this log. Both are
in **§0.4**, at the front, not buried. **Revision 3.1 (2026-08-16), marked [c4]:** the 49 further commits to `dceab3e8` (31 of them idle
ticks) were read directly and their artifacts re-opened. **They are not a postscript — they close Phase 10:**
the second-corpus replication is complete, Story A replicates at ~2× power with the refusal lever now
*significant* rather than CI-bounded, and a genuine position/length confound in our own AdvBench probe was
found and fixed. §31 is rewritten from "zero results" to the completed result; §21–§25 follow. Tags: **[V]** verified from an output file / recompute · **[R]** report-only · **[W]**
withdrawn/superseded (kept for honesty) · **[B]** bounded null · **[BLK]** blocked-as-specified.

---

## 0. One-paragraph takeaway (the whole sprint)

We set out to map the complete causal circuit of the **Doublespeak** in-context jailbreak (arXiv:2512.03771),
in which a benign codeword is bound by in-context demonstrations to a harmful concept so that a request phrased
with the codeword elicits harmful output. **We mapped the concept circuit in full — and then showed that circuit
does not cause the jailbreak.** The elaborate token→concept remap (demo-codeword K/V retrieval L8–L10 + an L9
MLP write → L14–L21 "carry" heads → L30–31 output) is real, distributed, and necessary-and-partially-sufficient
*for the internal concept readout* — but ablating it through harmful generation leaves attack success
statistically unchanged, while a count-matched *random* ablation moves ASR ~3× more. What *is* behaviorally
potent is a single, orthogonal **refusal direction**: ablate it and ASR rises +0.43–0.48 (a stronger attack than
Doublespeak); re-inject it and ASR falls to 0.000 with fluent refusals; its decision-token projection *predicts*
which prompts jailbreak (AUC 0.87). **Doublespeak is, mechanistically, an imperfect in-context
refusal-suppression technique; the concept remap is a causally-decoupled, behaviorally epiphenomenal bystander.**
The dissociation reproduces on **Qwen3-14B** and survives 8-/4-bit quantization and an independent from-scratch
implementation. The final two sub-sprints turned to the sharpest question — *can the mechanism be turned into an
attack?* — and found a precise answer: the refusal direction is **causal in activation space**, **reachable and
steerable by a continuous input optimizer** (soft-prompt ASR 0.784 vs 0.153 control), yet **discrete GCG token
optimization toward the same coordinate fails** (+0.009 ΔASR, sign-unstable, below judge noise). *The medium, not
the mechanism, is what fails.* Section 20 then bounded every behavioral negative honestly (±0.19–0.27 ASR at
n=37) and separated the **objective-space** claim (a 78 % change in the optimized quantity) from the
**behavioral** claim (unmeasurable) it must never be conflated with.

**[c3] The last two days closed the programme's two biggest open controls, and each closed against a claim we
had been making.** (1) **D3, "the single cleanest missing control"** — the same refusal ablation held to the
budget a token attack actually has (one layer, the decision position, prefill only) — **ran, and the
"activation > continuous > discrete" ladder turns out to be largely a statement about intervention SCOPE,
not about the activation-vs-token MEDIUM**: at token-reachable scope the ablation retains **0–3 %** of its
full-scope effect (+0.024/+0.000 vs +0.810/+0.571 refusal-rate reduction, n=42). The token-space negatives
themselves are measurements and stand; what changes is their *explanation*. (2) A **role-confusion
sub-sprint** rebuilt the whole representation-vs-behaviour dissociation from scratch on a new construct —
a contextual-identity ("Bombness") probe imported from *Prompt Injection as Role Confusion* — and produced
the cleanest version of the result in the programme: Bombness is **near-perfectly decodable** (held-out AUC
**0.997**, token-identity control exactly **0.500**), **orthogonal to refusal** at the codeword (cos 0.09),
**replicates on three model families**, and is **behaviourally inert under five independent designs** —
prediction (AUC 0.59 vs refusal 0.98), ablation (−0.048), injection (+0.048), a **2×2 factorial**
(main effect **+0.000**, interaction **+0.000**, refusal main effect **+0.357**) and **per-example component
surgery** (±18.7 readout units, ΔASR +0.048) — while refusal ablation moves ASR **+0.238/+0.357** in the same
runs. **Neither necessary, nor sufficient, nor gated.** Meanwhile asymmetry §20 closed: the μ sweep shows the
78 % CE cost is **sharply convex** (76.5 % of the coordinate's movement is removable for 19.5 % of the cost),
a **random-token floor** ate ~60 % of §20.5's apparent best-of-2 gain, and the pre-registered 3-seed
200→600 read **reversed a single-seed null of ours into a real (if small and inefficient) gain**.

**[c4] And then the second corpus landed, which is what the whole power argument was for.** On **AdvBench**
(n=399, test **n=88** ≈ 2× ClearHarm, leakage-0, *not* pooled), **Story A replicates and the refusal lever is
now significant rather than CI-bounded: ΔASR +0.295, p=0.0** (refusal rate 0.636 → 0.193; 2×2 main effect
+0.284 [0.188, 0.381]), while **Bombness stays null and, decisively, indistinguishable from a norm-matched
random direction** (+0.057 n.s., vs random +0.034 p=0.375; no interaction). The prediction dissociation
replicates too (**Refusalness AUC 0.862 vs Bombness 0.489**). In the process **we caught a real confound in our
own probe** — the v1 AdvBench build did not length-match the demo blocks, so codeword position and prompt
length leaked the label (`position_only` 0.785, `length_only` 0.752); a length-matched **v2** collapses the
position gap to 1.1 tokens and Gate 1 passes **cleanly at AUC 0.9995 with every control at chance**, on which
the Bombness main effect shrinks to **+0.017 [−0.023, +0.057]**. **The honest summary of what a second corpus
bought: it made the lever significant; it did not make the null exact** — ~n=305 is still needed to resolve a
ΔASR of 0.10.

---

## 0.1 The flow — the chain of questions that forced each other [c5]

This programme was not a grab-bag of experiments. Each sub-sprint exists because the previous one's answer
made it unavoidable, and the chain is short enough to state in full. *(Reconstructed by a dedicated agent
against the plan documents and git history rather than from this log's own narrative, precisely so that
abandoned branches and forced detours survive the retelling.)*

| # | stage | the question | what came back | **what forced the next stage** |
|---|---|---|---|---|
| 1 | **Part A** 08-02→04 | By what circuit does the model read the codeword as the harmful concept? | The full circuit: retrieval L8–L10 → L9 MLP write → L14–L21 carry → L30–31, Holm-significant at every stage, carry partially sufficient | Sufficiency was ≈0 everywhere else, and the plan's own **Gate 6/Gate 7 forbade optimizing an internal signal without behavioural evidence.** The circuit had to be tested on generation, which had never been done |
| 2 | **Part B** 08-04→05 | Ablate it through actual harmful generation — is any of it behaviourally necessary? | **Nothing.** Carry ΔASR +0.091/+0.071/−0.100/0.000 (p ≥ 0.289); write ∈ [−0.023,+0.067] (p ≥ 0.688). In the same harness a single orthogonal refusal direction moves **+0.432/+0.476** | This inverted the subject of the project — on thin ground (n≤86, v1 split, a p=0.045 interaction, unaudited numbers). Before rebuilding around refusal, everything already claimed had to be recomputed from raw |
| 3 | **Part C** 08-05→06 | Do our own numbers survive recomputation and an adversarial bug hunt? | Mostly — with three withdrawals, and one that mattered most: **the GCG mechanism objective entered the gradient but not candidate selection**, so every prior "mechanism-derived GCG is net-negative" claim was made with the objective effectively *off* | (a) The refusal circuit was now the headline and had never been mapped with the rigour the concept circuit got. (b) The bug fix made Gate 7 **testable for the first time** |
| 4 | **Part D** 08-06→09 | Is refusal-suppression localizable, behaviourally causal, powered, predictive, defensible, cross-model? | 28/28 sections. Gate A localizes it (L15–L18, frozen test 0.926); Gate B PASS-not-STRONG; ~100 % mediation; **the powered n=324 specificity result**; loss geometry blind to the concept channel (0.583 vs 0.807); defense **fails** on over-refusal | The Gate-7 first cut — the result that decides whether the mechanism is *actionable* — was 2 seeds, 50 steps, no CI, **and on a split later found to carry ~90 % train/test leakage** |
| 5 | **Part E** 08-09→11 | With leakage-0 data, a fixed off-by-one, 4× compute and 3 seeds, does the mechanism objective beat its random control? | **No — a definitive non-specific negative.** 0.297 vs 0.279, ΔASR +0.018, sign-flipping, no seed significant, between-seed swing ~0.24 ≫ the mean. Dissociation replicates on Phi and under 8-/4-bit | Bugs, leakage and underpowering were all eliminated and **the contradiction survived all three**: the same direction worth +0.43 in activation space is worth +0.018 as a token objective. That is a *why* question, not another ASR table |
| 6 | **Part F** 08-11→12 | Is the direction unreachable from tokens (H1), or is discrete search the bottleneck (H2′)? | **H1 rejected, H2′ supported.** Reachability 4.71× covariance-matched (subspace 148.5×); a *continuous* optimizer on the same coordinate reaches 0.784 vs 0.153; discrete gains +0.009. Cause found: suffixes do **generic** depth-graded suppression, r=0.9965 with random, deepest at L24 not L18 | Every one of those numbers was a **point estimate on n=37 binary ASR**, and the sprint had just retired its own +0.018 using a judge-noise floor it had only hand-counted. *What can these negatives actually exclude?* had no answer |
| 7 | **Parts G+I** 08-12→15 | What do our negatives exclude, once noise and power are measured rather than assumed? | Much less than claimed. Sampling SD dominates judge SD 3.5–7.4×; TOST bounds **±0.19–0.27 ASR**; **power 0.05** against our own effect; a **random-token floor** ate 58 % of §20.5's headline; the μ sweep re-scoped §20.1; a pre-registered read **reversed our own null** | §20.8 named the binding constraint out loud — *"only a second corpus buys real behavioural power."* And the thesis had only ever been tested on constructs **we ourselves designed** |
| 8 | **Part J** 08-14→16 | Rebuild the dissociation on an *imported* construct whose own authors ran no causal test — Story A or Story B? | **Story A, in the cleanest form the programme produced** (§29), Story B refuted by a 2×2, Phase 9 cancelled by its own gate. **D3** ran and turned a headline against us. **AdvBench** replicated Story A at ~2× power and caught a confound in our own probe | What remains is a **decision, not a job**: the queue is empty, and pooling to n≈308 needs a joint re-split |

**The five moments that redirected the work** — note that **three of the five are a control or a code audit,
not an experiment**: (1) the Part-B behavioural nulls, which changed the object of study (`CONTINUATION_MASTER_
PLAN_V2` §2 is literally titled *"MAIN SCIENTIFIC PIVOT"*); (2) the **candidate-selection bug**, which reset
Gate 7 to a blank slate and is why Parts E, F and G exist at all; (3) **P8.0's train-split interaction
reversing on held-out test**, which named the recurring failure mode and installed the ≥3-seeds-or-both-splits
rule that caught four later instances; (4) **Gate C+D positive while Gate E stayed negative**, which isolated
the failure to discreteness itself; (5) **D3**, which retired the ladder those gates had built.

**The method pattern, stated plainly, because it is the thing worth copying.** *Most of the compute goes into a
control designed to produce the same number without the mechanism, and the claim is carried by **specificity**
rather than by a p-value.* Norm-matched random directions, count-matched random heads/positions/edges,
covariance-matched gradient nulls (and the discovery that the naive version is rank-1 degenerate, deflating
Gate C from 6.74× to 4.71×), dose-matched continuous controls, in-run positive controls, and an un-optimised
random-token suffix floor. The clearest statement of it is §31.1: **an AdvBench Bombness effect whose CI
excludes zero (+0.046 [0.011, 0.085]) is still reported as no effect, because a norm-matched random direction
produces +0.034 — the specificity control, not the CI, decides.** Around that sit pre-committed endpoints
(frozen splits read once, decision rules written into code before the data lands), nulls reported as
equivalence bounds against measured noise floors, and gates that are permitted to cancel planned work.

## 0.2 What succeeded and what did not — the honest tally [c5]

An agent enumerated **every named gate, phase, question and section across all eight sub-sprints — 188 items** —
and assigned each a single verdict, with `UNDERPOWERED_NULL` kept strictly separate from `INFORMATIVE_NULL`,
and `NEVER_RUN` / `BLOCKED` / `DESCOPED_BY_RULE` kept strictly apart from each other.

| verdict | n | what it means here |
|---|---|---|
| POSITIVE_RESULT | **70** | a real, specific, controlled effect |
| SUCCEEDED | 30 | planned work that delivered what it set out to |
| **UNDERPOWERED_NULL** | **26** | a null that excludes nothing useful |
| INFORMATIVE_NULL | 17 | a null whose bound excludes the effect size that mattered |
| NEVER_RUN | 14 | simply not done |
| WITHDRAWN | 11 | claimed, then retracted |
| INFRASTRUCTURE_ONLY | 9 | built, not a finding |
| FAILED | 4 | the gate's own criterion was not met |
| BLOCKED | 4 | genuinely prevented |
| DESCOPED_BY_RULE | 3 | killed by a rule fixed in advance |

**The shape of that table is the honest headline: 43 of the 188 items are nulls, and 26 of the 43 — 60 % — are
underpowered rather than informative.** That is essentially every behavioural null measured at n=37–42 on
ClearHarm. **Only three behavioural nulls in the entire programme exclude a Doublespeak-sized effect:** the two
n=88 AdvBench Bombness bounds and the n=42 2×2 main effect. The 17 informative nulls are otherwise concentrated
in *representational* and *objective-space* endpoints, where power was never the constraint.

**What genuinely succeeded.** The concept circuit is completely mapped and the mapping holds. The refusal
direction is established as the behavioural lever by every test that exists — bidirectional, dose-responsive,
specificity-controlled, cross-model, cross-precision, cross-corpus, and reproduced by an independent
from-scratch implementation. The dissociation between them was then re-derived *from scratch on someone else's
construct* and held under five designs, three families and two corpora. Two of the programme's own biggest
exposures were closed **against** the authors (D3; the random-token floor). Four confounds were caught by the
team's own controls rather than by a reviewer: the P8 saturation artifact, the rank-1 degenerate covariance
control, the GCG candidate-selection bug, and the AdvBench position/length leak.

**What failed, in its own words.** The sprint set out to turn a mapped mechanism into an **attack** and into a
**defense**, and did neither: every attack-objective route ends in a measured or by-rule negative, and no
defense survived its utility cost (over-refusal exceeded |ΔASR| at every layer and dose). Four items are
`FAILED` on their own criteria — **Gate 6** (concept objective, 9/10 on the checklist, failed criterion 4),
**Gate F/G** (the defense), the **generated-cohort causal run** (manipulation check moved the readout the wrong
way; machine-stamped INCONCLUSIVE), and **AdvBench v1 Gate 1** (our own trivial controls at 0.785/0.752).

**Three different kinds of not-done, which the summary must not blur.** `DESCOPED_BY_RULE` = 3 (§20.7's
2000-step point, Phase 9, Phi Phase 6). `BLOCKED` = 4 (§20.6, §20.8, Gate D's confirmatory dose, the pooled
n≈308 analysis). `NEVER_RUN` = **14** — including the 13-arm GCG/MAC matrix (0 of 13 arms), **B16** (the Phi
concept-ablation arm, so "cross-family dissociation" is still not licensed by the plan's own Gate E), a true
2nd-order Jacobian loss, DeepSeek-R1, the quantized attack arms, and **§20.0's dev-split decision**. *Most of
what did not happen was simply not done — and the ratio 14 : 4 : 3 is the corrective to any narrative in which
this programme's gaps are all principled descopes.*

## 0.3 The results that carry the paper [c5]

Four independent agents ranked every result under four different lenses — **novelty**, **strength of evidence**,
**what changed our own minds**, and **transferable methodology** — and an adjudicator merged and attacked the
merge. Ranked by cross-lens support, with the limitation that must travel with each claim.

**1. The contextual-identity construct: decodable at ceiling, orthogonal to refusal, behaviourally inert under
five designs, three families and two corpora.** *(Gate 1 AUC 0.9972 with token-identity exactly 0.500; 2×2 main
effect +0.000 [−0.071,+0.071] and interaction +0.000 against refusal +0.357, p=0.00027; AdvBench v2 Bombness
+0.017 [−0.023,+0.057] vs refusal +0.335.)* **The only result all four lenses agree on.** It imports a
published method, fills a gap that method's own repository provably cannot fill — it contains no causal
intervention at all — and answers it with a **pre-registered discriminator** (Story A vs Story B) rather than a
single test, with every arm carrying its own random control *and* its own positive control in the same run.
⚠ **Travels with:** every arm is a bound, never a zero; the causal story is single-cohort (the generated
replication is INCONCLUSIVE); Gate 1 passes **3 of its 4** checks because the CARROT transfer value is `null`
and short-circuits to PASS; judge nondeterminism moves the positive control by the same magnitude as every
Bombness effect. **[c5] And one thing no report states: the AdvBench v2 manipulation check clears its own −0.5
gate by 0.086 at L20 (−0.586) and is ~2.3× weaker than ClearHarm's — where the manipulation is weak, "a tight
bound" and "we barely perturbed anything" produce identical statistics.**

**2. The L18 refusal direction is the behavioural lever.** *(+0.432/+0.476 ClearHarm; +0.352 AdvBench v2, b/c
33/2, p=0.0; +0.286/+0.262/+0.571 at bf16/8-bit/4-bit with random flat at every precision.)* Nothing else is
simultaneously this large, paired-significant on both splits and both corpora, specificity-controlled
everywhere, dose-responsive and cross-model — **and it is what makes every null in this document readable**,
because without a positive control firing in the same run the nulls would be indistinguishable from dead hooks.
⚠ **Travels with — and this is the ranking's warning sign, stated rather than hidden:** evidence ranked it #1
while **novelty, mind-changed and methodology all excluded it**, correctly, as a careful extension of
Arditi-style work rather than a challenge to the field's current belief. The axis is fit **off-distribution**
(60 harmful / 20 harmless generic instructions from `pair_carrot_bomb`, fit before this sprint) and "validated"
means validated at **all-layer scope — exactly the scope §30 shows is the only one where it does anything.**
The most-quoted form (re-inject → ASR 0.000) is **not specificity-controlled at its headline α=12**; quote α=8.

**3. D3: the programme's own "activation ≫ continuous ≫ discrete" ladder is largely an intervention-SCOPE
confound.** *(+0.810 → +0.452 → +0.024 refusal-rate gain across three scopes; random exactly +0.000 at all
three; `separation_heldout` identical at 0.174389 across arms.)* **The best-designed single experiment in the
log** — one factor varies, the random control is exactly zero everywhere, and the identical separation
independently rules out the obvious alternative. The decision rule was fixed in code before the read, and the
control was run *knowing it could only hurt.* It is also the most exportable correction here: a large
literature compares activation interventions with input-space attacks and concludes something about
representations being "more causal" than prompts; **that comparison is confounded unless layer × position ×
decode-step budget is matched.** ⚠ **Travels with:** the endpoint is keyword refusal rate, not StrongREJECT
ASR — carrying it across is an inference; the null arm is 1/42 flips; the `decision` arm is narrower than a
real suffix, so it may *overstate* the confound.

**4. The concept circuit is epiphenomenal by specificity, on three independent measures.** *(n=324: concept
+0.046 ns vs count-matched random +0.161, ~3×; gradient-norm AUC 0.583 vs 0.807; `d_DS` inert to 1e-05 while
`d_Direct` moves the readout +0.167→+0.971.)* The largest-n behavioural cell in the programme, making the
epistemically correct move — a *matched random* intervention producing a **larger** effect is a comparison a
power argument cannot defeat. ⚠ **Travels with three limitations, two of which were not in this log before
this revision and are the most serious findings of the audit — see §0.4 items 2–4.**

**5. The measurement-floor package** — random-token floor, judge-noise decomposition, equivalence bounds, power
from *observed* discordant rates. *(Floor ASR@1 0.2351 cutting our own best-of-2 gain from +0.084 to +0.035;
denoising made the bounds 6.4 % **wider**, proving they are sampling-limited; sampling SD 0.067 vs judge SD
0.009–0.019.)* This is the machinery that makes every other null quotable, and it is directly copyable — a
band-only replicate design validated by its own extreme control (0/40 flips) rather than by assumption.
⚠ **Travels with:** it is infrastructure, not a finding about models — and see §0.4 item 1, because the claim
that it was applied everywhere is false.

**6. A causal, reachable, continuously steerable coordinate is still not discretely optimizable — and we
measured why.** *(Reachability 4.71×, subspace 148.5×; continuous 0.784 vs 0.153; discrete +0.009; suffix depth
profile r=0.9965 with random, deepest at L24 not the optimized L18.)* The field assumes a validated causal
direction makes a better attack objective than a random one; this is the most complete dismantling of that
assumption available, and cause 3 converts a statistical negative into a **mechanistic** one. ⚠ **Travels
with — the sharpest disagreement in the whole adjudication:** novelty ranks it #3 while evidence and
methodology call it *"the weakest major evidence base"* and *"the sprint's worst methodological exhibit."*
All 20 per-seed run directories of the Gate-7 v3 matrix are **missing**, the cited manifest **does not exist**,
5 of 10 arms are single-seed — and **[c5] the sprint's own best null was never applied to its own headline
matrix**: every per-seed arm ASR (0.108–0.405, vanilla-DS 0.306) lies **inside the band ten un-optimised random
suffixes produce** (0.108–0.351). The conclusion is very likely correct; the evidence table is not yet one.

*Also ranked but demoted by consensus:* **§20.1's objective-vs-behaviour dissociation** (portable idea, but the
behavioural half is 0/3 significant on a soft prompt attacking at ≤0.24 ASR, so there was little behaviour
available to buy); and **the pre-registration machinery itself** (§20.7's read rule committed while seeds stood
at 30/37 and 12/37 is a genuinely exemplary artifact — but the programme demonstrates the *failures* of
governance more reliably than the practice: §20.0 never written, Q2 pending in a FROZEN manifest, the
role-probe plan's single commit postdating the run it claims to pre-register).

## 0.4 What this log is at risk of overselling [c5]

The adjudicating agent's brief was to find places where this document's own language outruns its evidence. It
found several, and **two of them were verified directly against the artifact for this revision and are
material.** They are recorded here, at the front, rather than buried.

1. **"Every behavioural negative is now an honest bound (~±0.2 ASR)" is FALSE as stated.**
   `outputs/asym_p204_equivalence.json` holds **exactly six rows**, all from one experiment family (the §7.5
   per-prompt GCG grid: mechanism / matched_random / vanilla × two budgets, n=37). **No TOST exists** for the
   concept-ablation null, the carry/write nulls, the Bombness nulls, Gate E, or the §20.1 follow-up. The honest
   sentence is: *"the §7.5 contrasts are bounded at 0.19–0.27 ASR; the remaining nulls are not
   equivalence-tested."* §24 item 6 and §20.4's own framing should be read with that correction.
2. **[V] §10's flagship specificity result does not reproduce on its own frozen test split — verified.**
   `phase10_powered_concept_L8_9_10_11_…732980/summary.json` carries ten groupings. `POOLED_all` (n=324,
   **train+dev+test**) gives concept +0.046 vs random +0.161, the ~3× gap that reached §0 and §24 item 2. On
   `FROZEN_test` (n=80) the same contrasts are concept **−0.0625** and random **+0.075**, and the artifact
   stamps **all four arms "underpowered"** — the gap is gone. *In a programme whose most-cited lesson (§8.5) is
   that a train-split effect reversed on held-out test, the pooled number that includes train is the one that
   became the headline.*
3. **[V] A significant, specificity-favourable concept-circuit behavioural effect exists in that same artifact
   and appears nowhere in this log — verified.** On `cohort_clearharm_test` (n=42 — the real-attack cohort's
   frozen split), **write-ablation ΔASR = −0.1905, verdict "significant"**: ASR *rises* 0.214 → 0.405 when the
   L8–11 concept write is ablated, while the count-matched random ablation on the same split is **−0.0238,
   underpowered**. On that cell **the specificity contrast runs the other way by ~8×.** Honest framing, because
   it matters in both directions: it is **one cell of ~40 in the file, uncorrected for multiplicity**, and its
   direction is counterintuitive (ablating the concept circuit makes the attack *more* successful, not less).
   But this log summarises that cohort as *"clearharm concept ablation is exactly 0.000 (b=22/c=22)"* — which
   is the pooled n=170 write+carry cell, **not this one. A reviewer who opens the artifact will find it.**
4. **The sign convention in §10 hides what the specificity comparison measures.** Positive ΔASR there means ASR
   **dropped** (0.333 → 0.173 in the random arm). So *"a count-matched random ablation moves ASR ~3× more"*
   means **random damage cuts ASR by 16 points** — and `P10_POWERED_CONCEPT_ABLATION.md`'s own caveat says that
   drop is *"likely degradation/incoherence rather than genuine refusal re-engagement"* (graded mean 0.263 →
   0.122). The load-bearing comparison is between a targeted ablation and a **coherence-destroying** one, with
   no coherence-matched control and no inferential test of the difference between the two arms. §0, §10 and §24
   quote the 3× without this caveat. **Relatedly:** §10's binary null has a **significant graded companion in
   the same artifact** (write+carry Wilcoxon p=0.0052) — the exact condition under which §8.6 retracted "carry
   heads behaviorally inert" to "undetermined". That treatment was never applied here.
5. **"~n=305 is still needed" is computed from the refusal arm and quoted about the null.**
   `PHASE10_POWER_ADVBENCH.json` (the *Bombness* arm) returns `required_n` **null** and `power` **NaN**, because
   p_disc is 0.057. The 305 comes from the *refusal* file — which also records **power 0.271 against a 0.10
   effect at n=88**, a number that appears in no report.
6. **"Replicates on three model families" does work across three different constructs.** For Bombness necessity
   it is genuine (3/3, each equal to its own random control). For the **refusal lever it is 2 of 3**, with Phi
   explained post-hoc by an untested floor and confounded by a direction the repo's own artifact rejects. For
   **prediction it is Llama-only** — no artifact exists for Phi or Qwen. §29.7 states all of this; §0 and §24
   carry the summary sentence without it.
7. **A withdrawn claim is still live in the shipped deliverable.** §21 item 19 withdraws D3's "independent
   replication by a concurrent session", but `reports/D3_SCOPE_COMPARISON.md` still opens with *"Both agree to
   the decimal, which is the strongest possible confirmation of a reviewer-critical control."* **The correction
   exists only in this log; the artifact a reader would cite is unrepaired** — the half-updated-document failure
   mode recurring in the very result it was named for.
8. **Decisions narrated with the cadence of findings, and infrastructure presented as results.** Phase 9's
   cancellation and §20.7's descope are correct *and are decisions*; the ledger's arithmetic is the corrective
   (3 descoped-by-rule against 14 never-run). §27's process items are the most quotable prose in this document,
   which is exactly the risk — **only the items that changed a number** (the candidate-selection bug, the rank-1
   degenerate control, the P8 saturation artifact, the §20.7 reversal) **have paper-level standing.**
9. **"Behaviourally inert" is both stronger and weaker than the evidence.** In run 757943 the Bombness ablation
   leaves only **23 of 42 completions byte-identical** to baseline (the random arm leaves 30/42). The
   intervention demonstrably changes *what the model writes* — a better "not a dead hook" argument than the
   readout check, and one this log never made — while changing nothing about whether the output is harmful.
   **The precise claim is "harm-neutral", not "inert".**
10. **The scale the bounds are divided by is unreconciled.** "2.1–2.3× the Doublespeak effect" uses +0.100 from
    an n=30 majority-vote cell; §4.1's own baseline gives DS − direct = **+0.233** at n=86, under which the same
    bounds are **~0.9–1.2×**. The log picks the framing that damages itself more, which is honest — but the two
    estimates of "the effect the paper is about" are never put side by side.

---

## 1. System under study, model, environment

| item | value |
|---|---|
| Primary model | `meta-llama/Llama-3.1-8B-Instruct`, **bf16**, 32 layers × 32 heads (8 KV heads, GQA), d_model 4096 |
| Cross-model | `Qwen3-14B` (thinking-OFF); `Phi-4-mini-reasoning` (reachability replication) |
| Hardware | NVIDIA **L40S** primary; backfilled onto **a5000 / 3090** (killable partition) via a VRAM-gated allowlist |
| Stack | torch 2.7.1+cu126, transformers 5.12.1; CPU analysis in conda env `poc_stage2` (numpy 2.4.6, scipy 1.17.1); bitsandbytes 0.50.0 for quant |
| Attention | default SDPA; **eager forced** wherever attention patterns/edges are hooked (SDPA fuses softmax@V and silently no-ops the hook) |
| Decoding | greedy (`do_sample=False`); gen_determinism measured **1.000** every cell |
| Harm judge | **StrongREJECT** rubric grader (gpt-4o-mini), `MALICIOUS` iff score ≥ **0.25** (`scripts/behav_judge.py:85 MAL_THRESHOLD`); `ASR` = fraction malicious. Judge-noise: see §20.3 — the corpus figure is **0.62 %** two-pass disagreement, superseding the earlier 3.4 % (one arm at n=37) |
| ⚠ Threshold conflict **[c2]** | 0.25 is what *ran*, but the paper-facing docs specify **≥ 0.5** as the standing binary-success contract (`docs/UPDATED_PAPER_CLAIM_TABLE.md:11`, `PAPER_OUTLINE_V2.md:61`, `RESEARCH_HANDOFF_V2.md:102`). The sprint never recorded which results were produced at which threshold. The one audit that checked (§20 item 2: 27 contrasts, 0 sign flips) found it conclusion-neutral, but **any number in this log may need re-reading at 0.5 before publication** |
| Concept readout | **forced-choice `DE_context`**: `p_concept = P(concept)/(P(concept)+P(codeword))` at the answer position (representational, not behavioral) |
| Attack source | ClearHarm rev `79464fb6…`; demos via `gpt-4o-mini`, `openai_seed=7`, 12 demonstrations per prompt |

**Two metrics, kept strictly separate throughout.** `p_concept` (does the model internally *read* the codeword
as the harmful concept?) vs **ASR** (does it *emit* harmful content?). The entire program is that these
dissociate. **Six matched conditions per item** exist in the data: `doublespeak` (attack), `neutral`
(codeword, no demos), `direct` (plain harmful request), `benign` (codeword bound to benign demos),
`shuffled`, `unrelated` — but **only 3 were run in the headline behavioral cell** (`direct`, `neutral`,
`doublespeak`; `outputs/behavioral_split_beh_clearharm/behavioral_summary.json`) and 4 in the drift runs
(`+benign`). **`shuffled` and `unrelated` were never run behaviorally [c2].**

**Provenance of the L18 refusal direction — a cross-distribution transfer [c2].** Every refusal number in
Parts B, D, E, F and G rests on an axis fit **not on ClearHarm** but on `pair_carrot_bomb.json`
(`outputs/stage_gcg_full/refusal_direction_llama_L18.json`: n_harmful **60** / n_harmless **20** generic
instructions, separation **0.9525**) and then applied to ClearHarm. This was first flagged in
`docs/UPDATED_PAPER_CLAIM_TABLE.md:51` (claim A6) and is stated here for the first time. Its bidirectional
validation, which is what licenses the word "validated" throughout: `refusal_direction_llama_SELECTED.json`
→ L18 `ablate_gain +0.4667, induce_gain +0.6667, score 1.1333`, selected over L12/L14/L16/L20.

---

## 2. Data — the locked splits

- **v1** `data/splits/clearharm_doublespeak_v1.json` (frozen 08-02) — **[V]** 137 records, two cohorts split at
  the intent-cluster level: **clearharm** 86 (44 train / 42 test, 43 concepts); **curated** 51 (30 / 21, 17
  concepts ×3). 0 example/cluster/prompt overlap across train/test; 137/137 single-token concepts+codewords.
  ⚠ curated-test n=21 is the source of the sprint's one acknowledged power failure.
- **v2** `data/bench/bench_clearharm_v2.json` (08-04) — **[V]** 116 examples (86 clearharm + 30 new), 0 test leak.
- **v3** `data/behavioral_v3/` (08-05) — **[V]** **N=324**, 224 single-token concepts, 224 pairwise-disjoint
  codewords; cohorts clearharm 170 / generated 154; train 162 / dev 82 / test 80; **0 straddling** (fixed v1's
  vacuous per-instruction leakage check). Built for **$0.1426** across 496 gpt-4o-mini calls. Confirmatory audit:
  N=324, leakage 0, cells ≥20, 324/324 real demos, pinned @79464fb6. **Cohorts are NOT exchangeable** (DS is
  net-positive on clearharm, net-negative/concept-diluting on generated).

---

## 3. Statistics & controls (apply to everything)

- **Paired designs throughout**; train(dev) and test(heldout) aggregated **separately** (a pooling bug was caught
  and fixed mid-sprint).
- **Representational significance:** two-sided **Wilcoxon signed-rank**, **Holm**-corrected across the 32-layer or
  32×32=1024-head family, per split. (Replaced a sign-flip permutation test whose 5.0e-5 resolution floor returned
  an artifactual p=0 — the "60–75 heads" figure was that artifact.)
- **Behavioral significance:** **exact McNemar** on paired discordant flips + percentile bootstrap CIs (2000–10000
  resamples, seeded).
- **Tripwire controls, verified exactly 0.0 in raw:** self-swap, self-check freeze, identity patch, α=0 no-op.
- **Specificity controls:** norm-matched random directions, count-matched random heads/positions/edges. **The
  program's core epistemic move is specificity, not just significance.**
- **Coherence guard:** `empty_rate` = 0.000 in every behavioral cell.
- **Data integrity:** `validate_all_outputs.py` recomputed **4,909 summary values from raw across 29 dirs → 0
  mismatches**; test suite grew **113 → 205** passing (two real primitive defects found & fixed).
  **Scope corrections [c2]:** (a) "0 mismatches" is true *of that 29-dir pass only* — the later claim-table
  sweep found exactly one, `reports/CLAIM_AUDIT_TABLE.md` META-03: `summary!=raw at
  by_split.heldout.monotone_decreasing` on `outputs/phase9_dose_curated_L9_…704861` (2 of 5 `phase9_dose`
  dirs); it is the only such mismatch in the corpus. (b) Neither the 4,909 count nor the 113→205 trajectory
  exists in a machine artifact — both are prose in `CONTINUATION_PROGRESS.md` **[R]**. (c) The suite at HEAD
  is **228 passed / 13 skipped** (241 collected); 205 was the Part-C endpoint, not the sprint's.

---

# PART A — the representational concept circuit (sub-sprint 1, 08-02 → 08-04)

All readouts are forced-choice `p_concept`. **Sign convention: a positive effect = the intervention DROPPED the
hijacked reading.**

## 4. The circuit, stage by stage — [V]

- **4.1 Behavioral baselines / Gate 1.** clearharm agg (n=86): direct **0.116** / neutral 0.256 / doublespeak
  **0.349** (DS beats direct **+0.233**); curated 0.255 / 0.039 / 0.235. Recomputes exactly from the label field.
- **4.2 Direction geometry — Concept ⊥ refusal.** mean cos(concept,refusal) = **0.012** clearharm (max |cos|
  0.078) / **0.061** curated (max 0.153) — orthogonal at every layer. The `doublespeak_signature` (DS−neutral) is
  *closer to refusal* (cos 0.127/0.151) than the concept direction is — the first hint of the headline.
- **4.3 Residual patching at the query codeword — NULL.** Logit-lens P(harm) at the query codeword is at floor;
  no patch beats random; identity control exactly 0.0 on all 137 items. The local codeword state carries nothing.
- **4.4 Demo-codeword K/V retrieval (L8–L10) is NECESSARY, not sufficient.** Neutralize demo-codeword K/V
  (donor = benign-remap): per-layer specific effect CI excludes 0 at L8–L10 both cohorts (L9 curated +0.220 /
  clearharm +0.082; L10 clearharm +0.113). Honest joint window **L8–L10** (clearharm L11 CI includes 0).
  Sufficiency ≤ 0 everywhere — the binding is **context-bound** at this stage.
- **4.5 Query→demonstration attention EDGES are NOT necessary — clean negative.** Surgical eager edge knockout,
  all heads L8–11: specific-vs-random +0.0020 [−0.0004, 0.0046] **ns** (clearharm), −0.0026 ns (curated).
  Blocking *all* query edges hurts 13×–49× more (general-attention effect). **Retrieval is distributed/redundant,
  not a single induction edge.**
- **4.6 The L9 MLP write.** Patch DS `mlp_out` with matched benign at the **demonstration** codeword positions.
  **L9 is the only layer Holm-significant on all four cells** (cur dev +0.049 [0.023,0.080]; cur heldout +0.097;
  clr dev +0.063; clr heldout +0.015). **Sufficiency ≈ 0.** Componential dissociation at the same token: `attn_out`
  at L9 is null while K/V and MLP-out are both necessary. ⚠ **[c2]** The write is *not* purely
  demonstration-position: the **query**-codeword MLP is not a clean null on clearharm (L9 **+0.0146** dev /
  +0.0046 heldout, and L15/L20 also survive Holm on both splits). The correct statement is that the query
  effect is **3–4× weaker**, not absent (`SPRINT_2026-08-02_TO_08-05_FULL_SUMMARY.md` §7.6).
- **4.7 Write granularity (143 windows, v2).** Single L9 +0.080; sliding-W4 **L8–11 +0.111** > best single layer ⇒
  the write is **distributed across L8–11**. (Corrected: "saturates at W8" is false.)
- **4.8 All-head z-patch necessity — the carry heads (L14–L21).** Wilcoxon+Holm over 1024 cells (re-running
  `phase5_analyze.py` reproduced counts exactly): Holm-sig positive-necessity heads = cur dev **58** / cur heldout
  **0** (power failure at n=21, *not* a null) / clr dev **31** / clr heldout **31** (25 heads sig on BOTH clearharm
  splits). Top: L17H27, L14H4/H5/H23, L15H8, L18H20, L21H10, L30H15, L31H0/H1. **No single head dominates** (top ≈5 %).
- **4.9 Carry heads are causal in their attention PATTERN.** Joint 7-head uniform-KO **+0.166** dev / **+0.134**
  heldout; benign-pattern transplant +0.46; per-head none individually necessary (superadditive). ⚠ **[c2]**
  the uniform-KO arm has **no specificity control**: an arbitrary non-candidate head's pattern (`C_rand`)
  already produces a **0.152 dev / 0.103 heldout** drop, so "uniform-KO is specific to the carry set" is
  **unsupported on dev** (source §7.9). The pattern-causality claim stands; the specificity claim does not.
- **4.10 Where the carry heads get the concept.** KO_all (firing control) +0.246/+0.207; **KO_demo +0.007/+0.003**
  (~2–3 %) ⇒ carry heads read from the **distributed residual context**, not fresh attention to demo codewords.
- **4.11 Carry vs proximal + closing the L9→carry edge.** (a) `direct_frac` ≈ **0.00** for L14–L21 carry heads vs
  0.47–0.76 for L30H15/L31H0 (readout-proximal). (b) L9→carry-band mediation **0.75–0.83 in 3 of 4 cells**
  (clr dev 0.751, cur dev 0.764, cur heldout 0.828); the 4th, **clearharm heldout, overshoots at 1.459**
  (n=9) — disclosed in `reports/PHASE7_PATH.md:67` and **[c2]** restored here. Random-head control 0;
  underpowered throughout (n=9–13). (c) **Carry head-set is PARTIALLY SUFFICIENT** — install DS carry-`z` into a benign prompt
  → +0.16/+0.24/+0.37/+0.41 (random install ~0). **Progression: context-bound at retrieval/write → transplantable
  once carried.** *(Sufficiency is representational only.)*
- **4.12 Readout ≠ mechanism.** Linear concept projection peaks at **L31** in all four cells while causality lives
  at **L9/L14–21** (projection ≈ 0 at L9). Logit-lens localizes readout proximity, not the write.
- **4.13 The write is a GRADED lever.** Interpolated `(1−α)·DS + α·benign` at demo `mlp_out`: monotone decreasing
  over α∈[0,1] in **8/8 cells**; α=0 bitwise-identical to baseline. (No inferential stats — descriptive.)

**Circuit summary (Part A):** demo-KV retrieval (L8–L10) → L9 MLP write (band L8–L13) → L14–L21 mediated carry
heads → L30–31 proximal output. Necessity Holm-sig at every stage; carry stage additionally partially sufficient.
**Distributed within concentrated bands — no single head, edge, or layer is a bottleneck.**

---

# PART B — the behavioral frontier (sub-sprint 1 cont., 08-04 → 08-05)

Everything StrongREJECT-judged **generation** (real behavior), paired exact McNemar, two cohorts, matched
controls, `empty_rate = 0.000`.

## 5. The dissociation — [V]

- **5.1 BEHAV-CARRY — ablate carry heads through generation: NULL.** ΔASR +0.091/+0.071/−0.100/0.000; every CI
  includes 0; McNemar p ≥ 0.289.
- **5.2 BEHAV-WRITE — ablate the L8–11 write through generation: NULL (flatter).** ΔASR ∈ [−0.023, +0.067]; every
  p ≥ 0.688. (Re-tested decode-safe in the continuation — still null.)
  > **⇒ The complete representation ≠ behavior dissociation.** The components causally necessary (and, for the
  > carry heads, sufficient) for the concept **readout** are **not behaviorally necessary** for the jailbreak.
- **5.3 Refusal ablation is a STRONGER attack than Doublespeak — sufficiency.** Arditi-style directional ablation of
  the validated L18 refusal direction: ΔASR vs direct base **+0.432 (p=4.0e-6)** ch-train, **+0.476 (p=2.0e-6)**
  ch-test, +0.433 cur-train, +0.429 cur-test. Norm-matched random direction does **nothing** (p ≥ 0.5). ≥
  Doublespeak on all four splits (sig 2/4 at α=.05, 4/4 at α=.10).
- **5.4 Re-injecting refusal kills the jailbreak — necessity.** +α·refusal at L18 through DS generation: ASR
  .386/.381 → **.000** at α=12 on clearharm (McNemar p=1.5e-5 / 3.1e-5). Coherence-audited: empty_rate 0.000,
  effect already strong at milder α=8, completions are **fluent natural refusals**. ⚠ curated-test ns (only 2/21
  malicious to flip). ⚠⚠ **[c2] the random control is NOT null at the headline dose.** It is null at α=8, but at
  the matched **α=12 a norm-matched random direction significantly RAISES ASR (+0.27 / +0.33, p ≤ 0.002)**
  (source §8.4). So the α=12 → 0.000 result is a *large-dose* effect whose specificity is only established at
  α=8. Quote the α=8 arm when specificity is the point.
- **5.5 Doublespeak SUPPRESSES the refusal axis — representational grounding.** Project last-prompt-token residual
  onto the per-layer refusal direction: clearharm-test direct−ds gap grows monotonically hs9 **+0.19** → hs32
  **+41.21**, zero violations in all four cells; onset ~hs8 (the L8–11 write band). ⇒ the demonstrations do two
  orthogonal things in the same band: remap codeword→concept (inert) and suppress refusal (the driver).
- **5.6 The refusal DECISION is read MID-LATE (~L22).** Calibrated-α injection (each layer's own gap): L9 null in
  both cohorts; **L22 −0.250 (p=0.001) ch-train, sig in both cohorts.** Suppression starts at L8–11 but the
  behavioral decision is read mid-late. ⚠ Later refined: L9 is not linearly decodable as a refusal axis at all, so
  "L9 null" is *uninformative*; anchor mid-late on the validated L16/L18/L22.
- **5.7 Concept-remap ⊥ refusal-suppression — causally decoupled.** Ablate the L8–11 write, then measure the
  refusal projection: positive control fires (p_concept .884→.799) yet refusal suppression is unmoved (restoration
  within |0.05| of the gap at every layer; where sig, negative & ≤5 %). **This is why the concept circuit is
  behaviorally epiphenomenal: the two L8–11 effects run on separate pathways.**
- **5.8 The refusal projection PREDICTS which prompts jailbreak.** clearharm **AUC 0.874** at decoder L21 (n=86, 32
  malicious), Mann-Whitney **p=3.8e-9**, r=−0.584; **train 0.863 / test 0.891 [c2]** (the previously-quoted
  0.867 is the *pooled* column of `reports/P6_JACOBIAN_READOUT.md:89`, not train; per-split AUCs are
  report-only — `outputs/rep_predicts_behavior_sweep.json` stores pooled). curated is a genuine null (AUC 0.42) —
  uniform suppression → concept-dilution. ⚠ [W] the "5-fold CV 0.887±0.106" was withdrawn (recompute 0.869±0.055).
- **5.9 Outcome fixed at the DECISION POINT.** Token-0 L30 refusal projection: Direct 13.6, DS→refuses 9.1,
  **DS→jailbreak −2.1** (stays low); zero trajectory crossings; token-0 separation AUC 0.936 test / 1.000 train
  (**[R] [c2]** — `outputs/refusal_traj_clearharm_…711956/summary.json` stores no AUC field; the trajectory
  numbers themselves are **[V]**). The hypothesis that refusal *re-engages* mid-generation is falsified.

- **5.10 The `doublespeak_signature` direction (d_DS) is causally INERT — the sprint's best-supported
  negative [c2].** Adding d_DS at matched relative strength moves the concept reading by at most **1e-05**
  across 9 control cells and **3e-05** across 175 dose cells, while `d_Direct` at the same strengths moves it
  **+0.167 / +0.533 / +0.971** (`SPRINT_2026-08-02_TO_08-05_FULL_SUMMARY.md` §9.2, bottom-line item 8). The
  DS−neutral contrast vector — the most obvious "the attack direction" candidate — does *nothing* causally.
  It survives in this program only as the cosine observation in §4.2.

- **5.11 Run-to-run ASR drift bounds every 2-decimal Δ [c2].** The same `ds_base` condition, greedy, yields
  test ASR **0.286–0.381** across four separate runs (source §10.4) — a ~0.1 envelope from resampling alone,
  independent of the judge-noise floor measured in §20.3. This is the empirical reason §20.4's bounds land
  where they do.

- **5.12 The refusal_rate ladder — why "imperfect suppressor" is the right phrase [c2].** direct 0.84–0.88 →
  `ds_base` **0.45–0.48** → full refusal-ablation 0.05–0.10 (source §8.3): Doublespeak moves the model
  *halfway* down the refusal ladder, which is exactly what §5.3's "ablation is a stronger attack" means
  mechanistically. Composite DS+ablation train ASR **0.727** vs 0.568 (ablation alone) vs 0.386 (DS alone),
  McNemar **+0.341, p=2.8e-4** — the additivity later formalized in §8.5/§11.

**5.13 What sub-sprint 1 explicitly did NOT establish — Gate 6 and Phase 11 [c2].** Two planned items closed
as *not run*, and the log's later Gate-7 discussion must be read against them: (a) **Gate 6** — the candidate
`concept_objective` scored **9/10** on the eligibility checklist and **failed criterion 4 (behavioral
sufficiency)**, so the gate was never passed (source §9.1); (b) **Phase 11** — the 13-arm GCG/MAC matrix was
**designed but never run, 0 of 13 arms executed**, and even the scaled-down decisive arm G1 was planned and
never launched (§9.2). The source is explicit at line 838: *"Gate 7 was never tested … treat it as a
well-motivated hypothesis, not a measured null."* Everything in Parts D/E that calls Gate 7 a measured
negative refers to the **later** first-cut and v3 matrix, not to anything from this window.

**Consolidated behavioral verdicts:** carry & write behaviorally NULL; refusal ablation CAUSAL (sufficient);
refusal re-injection CAUSAL (necessary); DS suppresses refusal CONFIRMED; decision read mid-late (~L22); the two
pathways INDEPENDENT; refusal projection PREDICTIVE (clearharm); outcome set at the DECISION POINT.

---

# PART C — the continuation "tick" sprint (sub-sprint 2, 08-05 → 08-06)

Run under a 30-minute cron loop (`reports/CAUSAL_CONTINUATION_MASTER_PLAN.md`, ticks 1–86). Job: **trust then
extend** — harden provenance, recompute every number from raw, hunt bugs adversarially, add the causal tests the
plan still demanded. Changed no Part-A/B headline but **corrected several of our own claims** and added five results.

- **6. Integrity hardening — [V].** Provenance RUNMETA/DONE across 397/412 dirs; `validate_all_outputs.py` 4,909
  values / 0 mismatch; test suite 113→205; single StrongREJECT judge contract (`scripts/behav_judge.py`)
  differential-tested against 6 copies (found the missing-EMPTY-label defect in `14_behavioral_eval.py`; audited to
  have zero exposure).
- **7.2 (P1) Baseline audit — SAFE.** 0 of 411 Phase-2.1 generations empty; all 6 malicious rates recompute
  exactly. Secondary: truncation heavy & cohort-asymmetric (`stop_reason=length` 25 % clearharm vs 72 % curated).
- **7.3 (P2) All-occurrence patching ~doubles the L9 write necessity.** Patching all codeword occurrences vs
  demo-only raises L9 necessity **1.38×–2.27×** across six cells, specificity-controlled. (Ratio is unpaired —
  descriptive.)
- **8.1 (P7) 32-layer refusal-direction validation.** Under both independent direction families, ablate+induce
  arms: **L9 FAILS both** (valid=False); **L18 validates strongly** (ablate_spec +0.60/+0.90, induce +1.00/+0.80).
  The refusal axis first becomes linearly decodable at **L13**; **11 layers validate in both families** ({13–20,
  24, 28, 29}). Consequence: every per-layer refusal claim leaning on an *early* direction is affected → the "L9
  null" depth contrast is uninformative, not evidence of late-reading.
- **8.2 (P3) Decision-token attention edges — NULL with a working control.** edge-KO refusal shift −0.0032 (CI incl
  0); firing control (block all incoming edges) moves the projection to −0.666 / +1.075 (hook fires). Concept
  retrieval reaches the decision token through **no identifiable query→demo edge.**
- **8.3 (P4a) Induction-head identification.** query codeword attends to demo codewords at ~2× count-matched random
  (correlational only).
- **8.4 (P4b-1) No single head bottlenecks concept-reading.** Confirmed set {L4H16, L10H2, L13H18, L14H13}; effects
  0.001–0.014 (near floor) — distributed and weak.
- **8.5 (P8) The interaction saga — sub-additive → NULL (three corrections).** **The single most instructive
  correction.** P8.0 reported sub-additive Î=−0.186 (p=0.045) → **[W] withdrawn** (saturation artifact: at α=1.0,
  62.8 % of items already jailbroken; 7.5 % judge label-flips in the signal arms). P8.1 at de-saturated α=0.25:
  clean null Î=−0.0233 (p=0.860); Î tracks the I_max ceiling (Spearman +0.991). P8 v3 (n=242): pooled **Î=−0.054
  (p=0.172) NULL**; train sub-additivity (−0.124) **reverses on held-out test (+0.088)** — "the pre-registered
  split is the only thing standing between this project and making the same error twice." At the strong dose
  α=0.20 (where refusal-ablation provably fires: **+0.1417 vs random, McNemar b=20/c=2, p=1.2e-04** —
  `outputs/p8_alpha020_clearharm.json`, **corrected [c2]** from a previously-quoted "+0.194, p<1e-12" that
  belongs to a *different run at a different dose*, `p8_v3_combined.json` pooled@0.25, n=242): interaction
  **exactly 0.000 (p=1.000)**. **⇒ Doublespeak and refusal-ablation ADD, never synergize.**
- **8.6 (P10 / P10.0) Decode-safe write null survives; graded re-analysis → "undetermined."** P10: BEHAV-WRITE null
  survives decode-safe re-test (n=86; **n≈275 is needed for ΔASR≈0.09 and n≈419 for ΔASR≈0.07 [c2]** — the
  "275 for 0.07" pairing is a mis-citation `P10_DECODE_SAFE_WRITE.md` made of its own source and
  `reports/CLAIM_AUDIT_TABLE.md` P100-05 already corrected). P10.0: the binary "behaviorally inert" carry
  claim is **[W] retracted** — the graded endpoint recovers a small carry effect (d=+0.074, p=0.034) **but its
  specificity control FAILS** (random-head ablation = 53 % of the effect). Honest status **"undetermined."**

- **8.7 (P9.0) The GCG candidate-selection bug — the correction that made Gate 7 testable at all [c2].** The
  mechanism objective was entering the *gradient* but **not candidate selection**, so it never influenced
  which suffix was kept. Consequence, stated by the sprint itself
  (`SPRINT_SINCE_2026-08-02_COMPREHENSIVE.md:553`): *"every prior 'mechanism-derived GCG is net-negative'
  statement was made with the objective DISABLED in candidate selection, so Gate 7 currently has NO valid
  evidence for or against."* Fixed in commits `84bf7a1e` / `76acb44a` (`CONTINUATION_PROGRESS.md:193`).
  **Everything in Parts D–F that reports a GCG negative post-dates this fix; nothing before it is citable.**

**Corrections ledger (Part C):** P8.0 interaction (→ saturation artifact); CV-AUC 0.887→0.869; Phase-5b Q/K/V
"clean null" retracted; "behaviorally inert" carry → undetermined; a FALSE "D_i=+2 zero times in every cohort"
claim (curated actually shows 4) demoted; "SLURM SOLVED" falsified. **Direction of every finding preserved;
stated ranges tightened.**

---

# PART D — Continuation V2: the refusal circuit, closed (sub-sprint 3, 08-06 → 08-09)

`CONTINUATION_MASTER_PLAN_V2.md` — **28 sections, all DONE** (audited by `wf_df3944cb`; a section counts DONE only
if a committed run-dir + report with real numbers backs it, several as honest negatives). This sub-sprint pivoted
from *mapping the concept circuit* to *mapping and behaviorally validating the refusal-suppression circuit*, then
tested attack-objective, prediction, defense, and cross-model generalization. All numbers **[V]** unless tagged.

## 9. The refusal circuit and its behavioral causality

- **§3 Gate A — refusal-suppression localized at the decision token.** Residual stream **L15–L18**; `resid_pre`
  L18 train frac **0.936** (Holm-p 0.0), dev 0.931, **frozen TEST 0.926 (p=.005)**; residual ≫ attn_out/mlp_out;
  onset ~L13; self-swap ≤5e-6. (Null on the generated cohort, as expected — DS net-negative there.)
- **§23 Gate B — behavioral causality of the decision-token refusal state (PASS).** Restoring the Direct
  decision-token residual during DS generation lowers ASR: train (n=85) direct L17 **ΔASR −0.1412 (p=.012)**;
  random control **+0.1412 (opposite sign)**; self +0.0118. dev replicates (−0.186, p=.008). ⚠ Reduction to
  ≈direct level, not zero; frozen test underpowered (base at floor). **Reverse (comply) arm is NULL** → the DS
  state is not *sufficient* to induce compliance. Gate B is **PASS, not STRONG.**
- **§25 Full mediation: demo → refusal → decision → behavior.** train: ds_base .282 / direct .129 /
  ds_dpatch_direct .118 → **mediated fraction 1.07** (McNemar p=.0013); dev **1.00** (p=.0039). The DS attack is
  ~100 % mediated by the decision-state refusal representation.
- **§24 Orthogonalization: control lives in the refusal component.** train (n=85): **refusal⊥concept −0.2118
  (p=.00012)**; concept⊥refusal +0.1059 (p=.049); both ns. The causal control is in the refusal component, not the
  concept component.
- **§4 / §7 / §8 refusal-circuit anatomy.** §7 refusal heads are **head-distributed but LAYER-concentrated at L13**
  (audit-2 corrected); §4 carry-vs-readout **72–88 % mediated** with a monotone depth gradient; §8 full head→MLP
  path patching is **NO-PATH** (candidate/control 1.44×, needs ≥2×) — the refusal signal is carried, not
  sparsely written, in both families.
- **§5 position-decomposition — NULL (powered).** No demonstration-position manipulation both restores refusal AND
  keeps the concept remap; suppression is broad/distributed over demo structure.
- **§6 demonstration-count dose response — STEP, not ramp.** Nearly all suppression at the first demo; refusal
  proj@L18 4.02→2.98 then flat; concept flat; ASR weakly coupled (dRefusal↔dASR −0.292).
- **§22 token-timing.** What matters is the decision *state*, not decode-persistence; additive steering does not
  reduce ASR.

## 10. Concept circuit is epiphenomenal — by SPECIFICITY (powered, n=324)

- **§9 carry-head behavioral sufficiency — NULL.** Installing DS carry-`z` through generation: ΔASR +0.023 train /
  −0.048 test ≈ random; carry−rand specificity ≈0. **Concept sufficiency was never established behaviorally.**
- **§10 powered concept-circuit ablation — the key specificity result.** Pooled **n=324** (ASR_base .333):
  write+carry ΔASR **+0.046 [−0.011,+0.104] p=.142 (ns)** while count-matched **random +0.161 [.110,.211] p≈0
  (~3×)**; clearharm concept ablation **exactly 0.000** (b=22/c=22) vs random +0.124. **Epiphenomenal by
  SPECIFICITY** — not "inert/equivalent" (the pooled-equivalence framing was **[W] withdrawn** in audit-2: CI
  upper 0.104 > the claimed 0.09 MDE).
- **§12 The Jacobian / gradient-sensitivity readout — the dissociation, restated by a THIRD measure [c2].**
  (Run 08-07; `reports/P6_JACOBIAN_READOUT.md`, `outputs/p6_predicts_behavior_clearharm.json`; plan §12
  marked DONE. Omitted from every prior summary.) Instead of asking *what the model represents*, this asks
  *what the loss is sensitive to* — the gradient norm of the harmful-continuation objective w.r.t. each
  direction. Sensitivity peaks at **L12 for refusal** and **L16 for concept**. As a jailbreak predictor
  (n=86, 32 malicious): **`refusal_gradnorm_peak` AUC pooled 0.8073 [0.696, 0.901], train 0.7996, test
  0.8148** vs **`concept_gradnorm_peak` pooled 0.5828 (CI spans 0.5)**. The linear-projection scalars
  behave the same way (refusal 0.8449 pooled / 0.8469 test; concept 0.5075 pooled, 0.4222 test). **⇒ The
  concept channel is invisible not only to ablation (§10) and to linear readout (§5.8) but to the loss
  geometry itself.** This is the strongest single-experiment statement of the program's thesis and it should
  be in the paper.

- **§11 joint 2×2: concept × refusal.** Pooled n=324: Δ_concept −0.006 ns, **Δ_refusal −0.102 (p=9e-6)**,
  interaction **Î=−0.0216 perm-p=.56 (additive, not floor-bound**, I_max .787). Refusal restoration collapses ASR
  regardless of concept state; concept ablation inert in both refusal states.

## 11. Attack objective, prediction, defense

- **§14–18 Gate-7 — mechanism-derived GCG objective is NEGATIVE / non-specific.** Multi-seed (42+43) held-out ASR:
  vanilla 0.357; **refusal@L18 mean 0.465 ≈ random@L18 0.464** (dead heat); large per-seed variance. First-cut
  scope (2 seeds, 50 steps, no CI). Knowing *where* refusal is read (a scalar decision variable) does not hand you
  a *token-space* lever. Cleanly separates "predicts" (works) from "optimizes" (fails).
- **§18 continuous sanity gate.** Every candidate direction has a committed continuous gate: refusal **PASSES**;
  carry-head + combined + concept **FAIL** — only the refusal axis was ever cleared for discrete optimization.
- **§13 prospective frozen-threshold predictor (leakage-free v3).** Train-frozen threshold → **TEST AUC 0.9714,
  acc 0.857, fn=0** (every test jailbreak caught, 7 tp / 6 fp / n=42). Always paired with **train AUC 0.80** (only
  7 test positives).
- **§19–21 defense with utility — NEGATIVE (Gate F FAIL).** Causal refusal-restoration genuinely lowers ASR
  (**−0.224 train** best-layer L18; random does not defend) **but over-refuses attack-structured benign** at every
  layer/dose (over-refusal +0.28→+0.40 > |ΔASR|); an intent-gate on the refusal projection fires on benign as much
  as on attacks. Redeeming datum: **ZERO over-refusal on 40 unrelated-normal prompts** (§20; 39/40 gens changed →
  not a no-op). The refusal circuit *drives* behavior but is *not intent-selective*; the concept circuit *is*
  intent but *epiphenomenal* — so no scalar/gate on the refusal axis can be selective.

## 12. Generalization & robustness

- **§26 within-Llama generalization** (cluster-disjoint v3 held-out): existence ✓ / causal control ✓ / prediction ✓
  generalize to unseen concepts+codewords; attack-optimization ✗ (Gate-7 negative); novel-benign-codeword transfer
  is the one thin axis (probes only the epiphenomenal concept channel).
- **§27 Cross-model Qwen3-14B (thinking-OFF) — X1–X5 all ✅.** X1 DS raises ASR (.143 > direct .095 > neutral
  .024); X2 refusal direction validates (5/5, best L32); X3 DS suppresses the validated projection at every layer;
  X4 refusal ablation raises harm (+0.17–0.19) while random is null; **X5-CAUSAL: concept ablation is causally
  INERT (+0.035/−0.02 ≈ random) vs refusal +0.19** → **the concept≠behavior dissociation generalizes to a second
  model family.**
- **§28 framework robustness.** An independent from-scratch implementation reproduces the refusal-ablation headline
  (+0.31 vs +0.33; label-agreement 0.88/0.83; token divergence isolated to bf16 reduction-order, ~1 ULP/layer —
  not a logic bug).
- **§29 quantization robustness.** Refusal ablation raises harm at bf16/8-bit/4-bit (**+0.286 / +0.262 /
  +0.571**, McNemar sig); random ns at all precisions. **The mechanism survives quantization.** *(**[c2]** the
  previously-printed "+0.26 / +0.29 / +0.52" had bf16 and 8-bit swapped and understated 4-bit; §15's table
  below was always right. Source: `direct_refabl_a1.0_vs_direct_base.delta_ASR`, test n=42.)*

**Two 12-agent adversarial audits (`wf_8333d36e`, `wf_383ca171`): no core conclusion reversed, no claim REFUTED**;
corrections were overclaim-tightening (DEF-01 ratio, §10 specificity basis, X5 orientation) plus 5 latent
code/verdict-logic bugs, none of which changed a committed result. Live tally: **95 claims / 77 VERIFIED / 0
CHECK-FAIL / 173 numeric checks passed.**

---

# PART E — the Next Sprint: fair GCG matrix, a third family, quantization (sub-sprint 4, 08-09 → 08-11)

Plan `docs/NEXT_SPRINT_PLAN_2026_08_09.md` (Q1–Q7). Having established the mechanism in activation space, this
sprint asked the hard practical questions: *(a) does a properly-budgeted, leakage-free GCG matrix still show the
attack-objective negative? (b) does the dissociation hold on a third model family? (c) does it survive
quantization?* All headline numbers below were re-opened from the committed JSON for this log (`wf_92ba16b8`,
agent `next-sprint`).

**Foundational decision — the v3 leakage-0 split + an off-by-one fix. [V]** The frozen 16-arm GCG matrix was
specced on v1, but `reports/P1B_V3_SPLIT.md` found v1 has **~90 % train/test leakage** (77/86 rows; 14/43
concepts + 17/21 codewords straddle — the per-instruction hashing had made the leakage check vacuous). The matrix
was moved to **v3.1 leakage-0** (N=324, 0 straddling), a cluster-diverse **train pool of 40**, universal suffix
evaluated on **v3 test n=37** (every arm in `GATE7_V3_MATRIX_STATS.json` carries `"n":37, "split":"test"`). A
**refusal-direction off-by-one** was also found and fixed: builders store `hidden_states[L+1]` labelled `L` but
`gcg_optimizer.py:173` read `hidden_states[layer]` → a 1-block shift (fix: pass `fit+1`). *(This is the same
absolute-position/index bug class that has now hit this repo repeatedly.)*

## 13. The fair GCG attack-objective matrix (Q1–Q4) — a definitive NON-SPECIFIC NEGATIVE [V]

Llama-3.1-8B bf16, GCG, suffix_len 16, **batch 32 × 200 steps** (4× the first-cut's 50), v3 test n=37.
Source `reports/GATE7_V3_MATRIX_STATS.json`. **Two scope corrections before the table [c2]:** (i) **"3 seeds"
is true of 5 of the 10 arms only** — `arm03`, `arm08`, `arm08r`, `arm10`, `arm10r` each carry **one** seed,
which means **Q2 (L12) and Q4b (combined), both quoted below, are single-seed results** in a section whose
whole argument is that a single seed swings ~0.24 ASR. (ii) `batch 32` is **[R]**: the only committed GCG
manifest (`configs/manifests/phase9_gcg_mac_matrix.json`) says `batch_size 64`; suffix_len 16 and 200 steps
are confirmed. **Headline — refusal↓@L18 vs its norm-matched random@L18 (3 seeds, [V]):**

| seed | refusal@L18 ASR | random@L18 ASR | ΔASR | McNemar p |
|---|---|---|---|---|
| 42 | 0.324 | 0.351 | **−0.027** | 1.000 |
| 43 | 0.405 | 0.243 | **+0.162** | 0.109 |
| 44 | 0.162 | 0.243 | **−0.081** | 0.508 |
| **mean** | **0.297** | **0.279** | **+0.018** | — (swing ~0.24 ≫ mean) |

**Sign flips across seeds, no seed significant, mean +0.018 dwarfed by the ~0.24 between-seed swing → the
validated refusal-suppression objective is statistically indistinguishable from a random direction as a GCG
signal.** Companion arms: **Q4** concept↑@L9 mean 0.252 = its random 0.252 (inert, 3 seeds); **Q4b** combined
0.216 < refusal-alone (adding concept *degrades*; single seed). **Q2** refusal↓@L12 (Jacobian
sensitivity-peak) ASR 0.216 < vanilla, vs its random **+0.108** — and this arm needs two caveats it was
previously reported without **[c2]**: (a) it is the **one arm where the mechanism objective beats its
norm-matched control**, and while McNemar is ns (p=0.125) the **bootstrap CI EXCLUDES zero, boot95 [0.027,
0.216]**; (b) **L12 is the single layer that FAILED the ablate+induce validation gate**
(`refusal_direction_llama_SELECTED.json`: L12 `ablate_gain 0.0, induce_gain −0.3333,
both_gains_positive=false`; L18 selected at score 1.1333) — so a negative *or* a positive at L12 says
nothing about whether a validated mechanism direction is reachable. Both readings rest on one seed. **Q5 mechanistic-validity** (`GATE7_V3_MECH_VALIDITY_seed42.json`): at seed 42 the
refusal-optimized suffix suppresses the refusal projection *less* than a random suffix (−1.66 vs −2.04) — but this
seed-42-only reading was **[W] withdrawn** by the Asymmetry sprint (seeds 43/44 reverse it on 37/37 & 35/37
prompts, mean −2.013 vs random −1.204; seed 42 drew an unusually strong random). The **ASR negative stands and
sharpens.** *(The earlier first-cut pair "refusal 0.465 ≈ random 0.464" is **[R]**: its run-dirs are not retained;
this committed 3-seed matrix is the citable replacement.)* ⚠ **Provenance limit of the replacement [c2]:** the
stats JSON reproduces every number above exactly, but **all 20 per-seed run directories it names are absent
from `outputs/`** (globbed 20/20 missing). The sprint's headline Gate-7 negative is **summary-JSON-backed but
not raw-reproducible** — the largest single verification gap in this log, and one §22 previously did not
disclose. **Not done:** MAC/TROPT arms 11–13; a true 2nd-order ‖J‖² Jacobian loss (the "Jacobian objective"
was a first-order L12 proxy — and see above, at a layer that failed validation).

## 14. Phi-4-mini-reasoning — a third family (Q6): dissociation REPLICATES [V]

`microsoft/Phi-4-mini-reasoning` (~3.8B, 32 layers). **X1 behavioral** (n=30/split, native reasoning): DS raises
ASR **+0.066 train / +0.100 test** — but Phi is **weakly aligned** (direct 0.567/0.700 vs Llama 0.116), so
neutral≈DS (limited headroom). **X2**: refusal direction strongly separable at every layer yet ablate+induce
validates at **only L14 (1/6 layers)** — representation ≫ behavioral potency. **X3** (test n=42): refusal-ablation
ASR 0.714 → **0.952** at α=1, refusal_rate → 0.000, random-ablation flat (0.714) → **ΔASR +0.238, McNemar
p=0.006** (causal, dose-dependent, specific). **X5**: neither concept nor refusal linear readout predicts jailbreak
(all AUC CIs span 0.5, n=42 underpowered). Geometry also replicates: **|cos(concept, refusal)| ≤ 0.056 at
every Phi layer [c2]**, matching Llama's §4.2 orthogonality.

⚠ **Scope correction — what "replicates" means here [c2].** `docs/THIRD_FAMILY_REPLICATION.md` contains X2
geometry, X3 refusal-ablation and X5 readout **only**: there is **no Phi concept-ablation arm with a
count-matched random control**. The plan's own Gate E says *"only claim cross-family dissociation after
**both** concept intervention and refusal intervention have appropriate random controls."* So what replicates
on Phi is the **refusal half plus the readout dissociation**; the concept half — the "epiphenomenal by
specificity" result that carries Part D §10 — was **never tested outside Llama and Qwen3**.
**Not done:** the Phi concept-ablation arm; Phi objective-transfer GCG; a DeepSeek-R1 secondary replication;
plan Phase 6 (powering up the Phi readout on a leakage-free ≥60-item cohort) was **consciously dropped**
(execution log, 08-12 01:06); Phi X3 is thinking-**off** (an original native-reasoning run was killed for a
projected ~50 h and rescoped).

## 15. Quantization extension (Q7): the mechanism survives bf16 / 8-bit / 4-bit [V]

Llama-3.1-8B, refusal axis L18, test n=42, activation-space ablation vs norm-matched random, α∈{0, 0.5, 1.0}.
Extends Continuation-V2 §29 with a full **dose-response + specificity control** at each precision:

| precision | refusal-abl ASR (α=0/0.5/1) | random-abl ASR | refusal_rate 0→1 | α=1 ΔASR | McNemar p |
|---|---|---|---|---|---|
| bf16 | 0.191 / 0.476 / 0.476 | 0.214 / 0.143 / 0.191 | 0.762→0.238 | **+0.286** | 4.9e-4 |
| 8-bit | 0.262 / 0.429 / 0.524 | 0.262 / 0.143 / 0.143 | 0.738→0.238 | **+0.262** | 7.4e-3 |
| 4-bit NF4 | 0.167 / 0.643 / 0.762 | 0.167 / 0.167 / 0.167 | 0.762→0.071 | **+0.571** | <1e-4 |

At every precision the refusal-ablation is causal, dose-dependent, and **specific** (random flat/drops); strongest
at 4-bit. **Not done:** quantized concept-geometry/predictor and the attack-objective GCG arms under quant.

---

# PART F — the Asymmetry Sprint: *the medium, not the mechanism, fails* (sub-sprint 5, 08-11 → 08-12)

`docs/ASYMMETRY_FINAL_SYNTHESIS.md`. This is the sprint's intellectual crux. It resolved the tension the whole
program had reached: **a refusal direction is causal in activation space, yet GCG suffixes optimized toward it
fail like random.** Two hypotheses — **H1** (the direction is not *reachable* from input tokens; the failure is
geometric) vs **H2′** (it *is* reachable, but *discrete* search can't find the tokens; the failure is the
optimizer). **Result: H1 is rejected, H2′ is supported, and we measured the boundary.** Verified for this log by
`wf_92ba16b8` agent `asymmetry`.

**Headline.** The refusal direction is **unusually easy to reach** from input tokens (**4.71×** a
covariance-matched control); a **continuous** input optimizer exploits this to jailbreak at **ASR 0.784 vs 0.153**
dose-matched control (ΔASR **+0.631**); **discrete** optimization toward the *same direction* gains **+0.009 ΔASR**,
sign-unstable and below the judge's noise floor. **The medium, not the mechanism, is what fails.**

## 16. Gate-by-gate

| gate | question | verdict | key numbers | verification |
|---|---|---|---|---|
| **A** | is the published token objective correctly configured? | **NEGATIVE — defect** | read a fixed absolute index from `train_tasks[0]`: correct for **1 of 40** prompts, 5 template tokens from where the axis was fitted | [R] code-audit |
| **B** | is the linear surrogate valid at token scale? | **NEGATIVE (Llama) — and worse than a null** | Pearson r **0.8395 → −0.0015** (train) and **0.8104 → −0.3242** (test) from ε=0.1 to ε=1.0, vs random directions **+0.041 / +0.129** and activation-random **+0.204 / +0.334** at ε=1.0 | **[V] [c2]** recomputed from `asym_p1_reach_{train,test}_…7503{61,62}/eps_scan.jsonl` |
| **C** | is the direction reachable from suffix tokens? | **POSITIVE — strongly** | ‖Jᵀv‖ **4.71×/4.91×** (train/test) covariance-matched, pct 0.990; **~15×** isotropic; mech norm 22.04/19.79 byte-exact | **[V]** (ratio has a control-aggregation caveat; test 4.89×≈4.91×) |
| **D** | does continuous input control work, specifically? | **POSITIVE — at one dose, read on test (EXPLORATORY)** | **ASR 0.784 vs 0.153**, ΔASR **+0.631**, 3 seeds, **0 sign flips**, all p<1e-4 — but see the inverted-U below | **[V]** `ASYM_P2_DOSEMATCHED/SEED43/SEED44.json`, reproduces to 3rd decimal |
| **E** | does mechanism-derived *token* optimization work? | **NEGATIVE, unstable** | position-corrected ΔASR **+0.009** (legacy +0.018); sign-unstable; below ±0.03–0.08 judge floor | **[R/log]** heldout-ASR run-dirs not retained |
| **F** | does the causal locus generalize across concepts? | **PARTIAL** (the artifact's own verdict — refusal half yes, concept half underpowered) | refusal ablation raises ASR **5/5** pairs, median specific ΔASR **+0.414**, **4/5** Holm-sig (chlorine ns); but **only 1 of 5 pairs (grenade) had concept-half attack headroom** — chlorine/pistol floor-limited, bomb/cocaine marginal | **[V] [c2]** `ASYM_P4_MULTICONCEPT.json` → `GATE_F.verdict = "PARTIAL … Do NOT claim 'general across concepts'"` |
| **G** | does a mechanism-derived defense follow? | **NEGATIVE (honest) — but floor-limited on test** | test: **no arm** reduces ASR (gate_two +0.024 ns); gate_concept ≡ gate_two (refusal half fires ~always). **[c2]** test DS ASR *without any defense* is **0.143**, so the test arm cannot demonstrate a reduction at all; on **train** the two-signal gate **Pareto-dominates** its random control (none 0.282 → gate_two 0.129, Δ **−0.153**, p=0.0010; over-refusal +0.141 vs unconditional +0.365) — EXPLORATORY | **[V]** `defense_2signal_…751316`; caveats `docs/TWO_SIGNAL_DEFENSE.md` §3–4 |
| **E′** | does removing the UNIVERSALITY constraint rescue it? | **NEG behaviourally, POS mechanistically** | per-prompt ΔASR 0/3 sig; projection **3/3 consistent** mean **−0.354** (Holm-survives s44) | **[R]** scalars consistent across 3 docs |

**Replication beyond the primary setting:** Gate C replicates on **Phi-4-mini** (isotropic 5.53×≈doc 5.56×,
covariance 4.10×) and under **4-bit NF4** (isotropic 13.62×≈13.25×) — the reachability asymmetry is **not a Llama
or bf16 artifact [V]**. Gate B does *not* fully replicate: on Phi the surrogate degrades but does not collapse — so
H2′'s **qualitative core** holds in both families while its **sharp form** (mechanism ends up worse-predicted than
a matched null) is **Llama-only** (stated in the paper body, not buried). *(A Phi Gate-B "inverts" claim was
retracted — train-split-only.)*

**Two Gate-C companion results, previously unreported [c2]** (both in
`asym_p1_reach_train_…750361/ANALYSIS.json`, cell `decision|hs19`, 15,360 substitutions):
1. **The reachable subspace R(v) is enormous for refusal** — `refusal_L18 R = 0.5846` vs random-direction
   mean **0.003936** and isotropic null **0.003906**, i.e. **148.5×**, `percentile_among_random = 1.0`. This
   is a far sharper statement of Gate C than the 4.71× gradient-norm ratio the log leads with.
2. **…but refusal gradients are barely more cross-prompt coherent than random — a NEGATIVE for the
   universality story.** `mean_pairwise_cosine 0.3482`, participation ratio 5.18, 92.9 % of pairs positive —
   against **8 random directions at mean 0.2680, max 0.3831**. Refusal is inside the random spread. This is
   the direct answer to the plan's flagged-HIGH-VALUE §5.5 hypothesis (*"a universal suffix should exist
   because the refusal gradient points the same way for every prompt"*): **it does not, particularly.**

## 17. The three-capability picture (the organizing claim)

| capability | works? | evidence |
|---|---|---|
| **intervene** on the direction in activation space | **yes** | Gate F, 5/5 pairs |
| **steer** it from the input, continuously | **yes** | Gate D, ΔASR +0.631 |
| **optimize discrete tokens** toward it | **no** | Gate E, +0.009, sign-unstable |

The first two working is what makes the third's failure *informative*: because the direction is reachable and
demonstrably exploitable by a continuous optimizer with the *same* objective on the *same* coordinate, the discrete
failure isolates **the discreteness itself**. **Four measured causes** (1–2 as previously reported, 3–4
restored **[c2]** from `docs/TOKEN_REACHABILITY_ANALYSIS.md`):

1. The first-order surrogate **collapses before one-token step size** (r 0.84 → −0.002 train / −0.324 test —
   past zero, and *below* both random controls).
2. A perfect solution inside the token simplex **retains only 5.7 %** of its effect once rounded to real
   tokens. *(Caveat: this measures **projection** retention only — no generation was ever run with the
   rounded suffix.)*
3. **§19.2 — what discrete suffixes actually do is GENERIC suppression, not the targeted intervention.**
   Sweeping the fit layer L10–L24, the refusal drop is ~0 before L14, grows monotonically with depth, and is
   **deepest at L24 — not at the L18 the objective optimized**. The refusal-suffix and random-suffix depth
   profiles are near-identical in shape, **Pearson r = 0.9965** (refusal vs plain doublespeak r = 0.9968).
   The suffixes differ in the *magnitude* of one shared profile, not in *where* they act — strong support
   for H4 (generic adversarial suppression). **This is the mechanistic content of the Gate-E negative:** GCG
   is not failing to hit the coordinate, it is hitting a generic direction that happens to include it.
4. **§6.1(c) — and it is not an overfitting failure.** Transfer ratio (test drop / train drop) is **> 1 in
   all 9 cells (1.17–2.00)**: the universal suffix suppresses refusal *more* on held-out prompts than on the
   pool it was optimized on. The "universal suffix overfits its suppression" hypothesis is **rejected**,
   independently of §19's per-prompt result.

⚠ **The one control that would qualify this whole hierarchy was never run [c2].** The activation intervention
is **all-position / all-layer** while the soft prompt is **16 input positions** — so the "activation >
continuous > discrete" ordering is **not budget-matched**. `docs/RESEARCH_HANDOFF_V2.md` §5.2 calls the
scope-matched activation arm (**D3**) *"the single cleanest missing control"* and ranks it the control a
reviewer will ask for first. Until it runs, the ladder is confounded with intervention scope.

> **[c3] SUPERSEDED — D3 ran on 2026-08-15 and the confound is CONFIRMED and quantified.** See **§30**
> (Part J). The scope-matched arm retains **0–3 %** of the full-scope refusal reduction. **The table above
> must be read as an ordering over intervention SCOPES that happens to correlate with medium, not as
> evidence that the activation medium is privileged.** What survives unchanged: the token-space negatives
> of §13/§18/§19 and §20.5/§20.7 are *measurements* on the ASR endpoint and are untouched by D3, which is
> measured on refusal rate.

## 17b. Gate D's dose response is an INVERTED U — and probe displacement is not mechanism control [c2]

Gate D is reported above as a clean positive, which is how it was carried through the sprint. The full dose
sweep (`docs/CONTINUOUS_VS_DISCRETE.md` §5, held-out) says something more interesting and more cautionary:

| budget_rel | Δ refusal proj | resulting proj | in natural range? | **ASR** | refusal_rate |
|---|---|---|---|---|---|
| 0.05 | −1.07 | +3.35 | yes | 0.135–0.162 | 0.730 |
| **0.10** | **−8.22** | −3.80 | no | **0.757–0.838** | **0.027** |
| 0.25 | −8.95 | −4.53 | no | *(not judged)* | — |
| **1.00** | **−20.09** | **−15.68** | no | **0.000** | **0.000** |
| random @0.10 | −2.21 | +2.21 | yes | 0.081 | 0.460 |

Too little suppression and the model still refuses; the right dose jailbreaks; **too much drives the residual
so far off-manifold that the model neither refuses nor complies** — ASR 0.000 *and* refusal_rate 0.000 at the
largest displacement of the whole sprint (verified independently:
`asym_p2_soft_refusal_free_b1.0_seed42_…750364/projections.json`, n=37, baseline 4.4170 → final −15.6751,
Δ **−20.0921**, per-prompt sd collapsing 2.532 → 0.252). Note also the plateau between 0.10 and 0.25 (−8.22
vs −8.95) before the jump.

**Two consequences the paper must carry.** (1) **Probe displacement is not evidence of mechanism control** —
the run that moved the coordinate furthest produced *zero* behavior. This is the same lesson as §20.1's
objective-vs-behavior dissociation, arrived at from the opposite direction, and it independently indicts any
mechanistic result reported as a projection shift. (2) **Gate D is EXPLORATORY, not confirmatory**: 0.10 was
selected as optimal *by reading the dose sweep on test*. A confirmatory dose needs freezing on the untouched
v3 dev split. The headline 0.784 vs 0.153 is real and 3-seed sign-stable — but it is the peak of a curve that
was chosen after seeing it.

## 18. The λ=10 probe — the negative survives a meaningful objective weight [R/log]

Gate E's negative carried one caveat: at the published λ=0.25 the refusal term is only **0.37 %** of the total
GCG-selection loss, so the negative could mean merely "the position fix alone doesn't rescue it." **Re-run at
λ=10 (~40× published), 3 seeds:** ΔASR **+0.622 / −0.162 / +0.189**; McNemar 1.55e-6 / 0.109 / 0.065.
**Sign-consistency 2/3 → FAILS. The negative STANDS and is stronger:** at λ=10 the objective *works internally*
(carries 24–34 % of selection loss, drives held-out projection past zero in all 3 seeds) yet behaviour does not
follow stably; all three |ΔASR| exceed the judge floor yet disagree in sign. **Do not quote the mean (+0.216)** —
three seeds that disagree in sign estimate nothing. This rules out the "discrete negative was an implementation
artifact" alternative on two independent grounds (position fix changed nothing: +0.009 vs +0.018; a 40× λ increase
produced no seed-stable gain). *(Verification note: the λ=10 and position-corrected Gate-E heldout-ASR run-dirs
were pruned from `outputs/`; these two numbers are backed by three mutually-consistent committed `.md` files but
were **not JSON-reproducible** in this pass — the only such gap in Part F besides E′.)*

## 19. Per-prompt vs universal (§7.5, added mid-sprint per Mahmood) [V/R]

Tests whether the token-space negative is a *universality* failure. One suffix optimized **per prompt** (vs one
universal suffix), 3 arms × 3 seeds × 2 budgets. **The two endpoints dissociate:** projection (internal target)
**3/3 sign-consistent, mean −0.354** (the objective moves its coordinate further than random); behaviour (ΔASR)
**inconsistent, 0/3 significant.** **Answer: NO** — the universal negative is *not* a universality/prompt-specificity
failure (per-prompt suffixes even transfer off-diagonally ≥ the universal arm's own held-out; their specificity is
matched by a random direction; the projection moves so the objective is not inert). **The failure sits downstream
of the representation.** A methodological result that outlives it: **compute dominates direction** — the
matched-*random* arm alone gains **+0.216 ASR** from 5→200 steps/prompt, larger than every direction effect in the
sprint. Had §7.5 been run only at full budget, "per-prompt beats universal" would have followed, produced entirely
by compute using a random direction; the compute-matched arm was added pre-registration on exactly this reasoning.

## 20. Methodological findings that stand on their own (Asymmetry) [V]

1. **A representation objective reading one absolute token index** (Gate A) — produced a published negative;
   correcting it changed the result +0.009 vs +0.018 (i.e. nothing), which *is* the finding: the defect was a
   confound, not the cause.
2. **Two ASR thresholds (0.25 / 0.5) reported under one name** — conclusion-neutral here (27 contrasts, 0 sign
   flips) but only because it was checked.
3. **A judge that flips labels between runs at temperature 0** → ±0.03–0.08 on ASR at n=37, *larger than
   several previously-reported effects including the +0.018 it retired.* Any n≈37 ASR paper without a measured
   judge-noise floor is reporting effects it cannot distinguish from resampling. ⚠ **[c2] the flip rate quoted
   here has been superseded twice — use §20.3's numbers, not this section's.** The "~3.4 %" was an n≈148
   hand-count (execution log, not an artifact, **[R]**); the measured replicate design gives **35.5 % inside
   the 4.65 % boundary band and 1.65 % corpus-wide** (`outputs/asym_p203_judge_replicates.json`), and the
   two-pass corpus disagreement is **0.62 %**. The ±0.03–0.08 floor derived from the retired figure is what
   Part F used to retire the +0.018 and the λ probe; §20.3's variance decomposition (judge = 1.8–7.5 % of
   total variance, sampling SD 0.067 dominating judge SD 0.009–0.019 by 3.5–7.4×) **reaches the same verdict
   for a different reason** — those effects are below the *sampling* floor, not the judge floor.
4. **The naive covariance-matched random control is rank-1 degenerate** (E[|cos|] 0.97–0.998, ~1 effective
   direction because the activation covariance is dominated by one mode). Dropping the top component gives mean
   |cos| 0.094 and moved the headline Gate-C ratio from an inflated **6.74× → 4.71×**.

**The sprint's own errors (kept as a record):** a **Gate-E clause-(ii) POSITIVE on one seed (08:52) was
RETRACTED 10:05** when seed 43 reversed it — "the sprint's main judgment error"; a Gate-F verdict was published on
partial `raw.jsonl` from a still-running job (aggregator now requires `DONE.json`); a Phi Gate-B "inverts" claim
retracted (train-split-only); the covariance-control 6.74×→4.71× correction. **Every gate that survived did so on
≥3 seeds or both splits — the rule the λ probe is bound by.**

---

# PART G — Section 20: bounding the negatives honestly (sub-sprint 6, 08-12 → 08-14)

`docs/SECTION20_RESULTS.md`. The final sub-sprint took the program's *behavioral negatives* — which had been
reported as point estimates — and asked what they can actually exclude, separating the **objective-space** claim
from the **behavioral** claim it must never be conflated with. Verified for this log by `wf_92ba16b8` agent
`section20`; almost every number reproduces from JSON (exceptions flagged).

- **20.1 The refusal coordinate is necessary — in objective space. [V]** Two soft-prompt objectives at matched
  budget, 3 seeds: `task` (minimise target CE) vs `task_orth` (CE + a penalty pinning the refusal projection at
  baseline). **Pinning the refusal projection costs 78.0 % of the achievable CE reduction** (mean progress 12.7 %
  vs 57.4 %), 3/3 sign-consistent. Manipulation checks pass: the pin holds the projection (Δproj ≈ −0.03 mean —
  *report says −0.026; JSON −0.032, a minor mismatch that doesn't change the conclusion*) while plain `task` moves
  it **−3.09** as a pure side effect. (All CE-table numbers JSON-confirmed exactly.)
- **20.1 follow-up: that necessity does NOT transfer to behaviour. [B]** 222 generations (0 empty, 0 judge-fail):
  ΔASR(task − task_orth) = **+0.135 / −0.027 / +0.108** — **2/3 sign-consistent, 0/3 significant, every CI spans 0.**
  A 78 % change in what the optimizer minimises produces a behavioural change we cannot distinguish from zero.
  **This is the program's central dissociation one level down: objective vs behaviour, not representation vs
  behaviour — §20.1 must never be cited as a behavioural result.** *(ΔASR per seed JSON-confirmed; the McNemar/
  Wilcoxon p-values and CIs in the report are not stored in the artifact — [R].)*
- **20.2 Per-prompt mediation is MODALITY-SPECIFIC. [R]** In the unconfounded vanilla-discrete arm, more refusal
  suppression → more jailbreak: partial r **−0.291** (n=74, p=0.012). It does **not** replicate for continuous soft
  prompts (r −0.008, n=111) — and at n=111 the soft arm *excludes* an effect as strong as the discrete one, despite
  a larger drop range. Consistent with the coordinate acting as a **gate, not a dose** (the stratified saturation
  test is underpowered). *(Verification gap: no `asym_p202` artifact exists; the partial-r values are not
  reproducible from any committed §20 JSON — treat as report-only pending the mediation artifact. The soft-arm
  Δproj means that motivate the framing **are** JSON-confirmed.)* **One well-powered side finding from the
  same analysis, previously unreported [c2]:** in the `task_orth` (pinned) arm, per-prompt success correlates
  with the *baseline* refusal projection at **r = −0.512, p = 9.6e-09**, versus **−0.037** in the unpinned
  `task` arm (`SECTION20_RESULTS.md` §3b). That is the only **behavioural** evidence anywhere that the §20.1
  pin actually did what it claims — when the optimizer is forbidden to move the coordinate, whether a prompt
  jailbreaks falls back on where its refusal projection already sat.
- **20.3 Judge reliability — the "5.4 %" figure is superseded. [V]** Band-only replicate design (M=5, 665 calls,
  15× cheaper): intermediate band flips **35.48 %** (n=93) while the **extreme control flips 0/40** (SD 0.0023) —
  validating the band-only design rather than assuming it. Corpus-level two-pass disagreement ≈ **0.62 %**, not
  5.4 % (that was one arm at n=37). **Variance decomposition:** sampling SD 0.067 (92–98 %) dominates judge noise
  (0.009–0.019) by **3.5–7.4×**. The denoising was *carried out*: re-running all 18 §7.5 contrasts on the majority
  vote moved **7/18 ΔASR** (max 0.054 = exactly 2 rows of 37) and **flipped 0/18 significance**. Practical
  consequence: individual ΔASR carry ~±0.05 of judge-attributable uncertainty — 54 % of the whole Doublespeak
  effect — so **do not quote ASR to three decimals.**
- **20.4 Every behavioural negative is bounded at ~±0.2 ASR. [B]** TOST equivalence bounds (paired bootstrap): the
  nulls rule out **only effects larger than ~0.19–0.27 ASR.** For scale, **the Doublespeak effect itself is +0.100
  ASR** (test split, majority-vote, n=30: DS 0.800 vs direct 0.700 — `baseline_drift_…741427`). **So the bounds are
  1.9–2.7× the size of the phenomenon the paper is about:** our behavioural nulls cannot exclude an effect two-to-
  three times larger than Doublespeak. Every "no effect" must read "no effect larger than ~0.2 ASR at this n." (All
  six bound rows JSON-confirmed.)
- **20.4 pass 2 — the bounds are SAMPLING-limited, not judge-limited. [V] [c2]** *(Ran after this log's first
  revision; `outputs/asym_p204_equivalence_pass2.json`, commit `c04d556b`.)* The plan's specified pass 2 (a
  multi-direction SD supplied by §20.6) is unreachable because §20.6 is corpus-blocked, so the bounds were
  instead recomputed on the **judge-denoised endpoint** (majority vote over M=5 on the 4.65 % band) — the
  other stated motivation. Result: **the bounds got 6.4 % WIDER, not tighter** (mean worst bound **0.2117 →
  0.2252**; `full mech−random 0.1892→0.2432`, `full random−vanilla 0.2162→0.2432`, the other four rows
  unchanged; every change an exact multiple of 1/37, i.e. 1–2 rows). This is not a defect in the denoising —
  it is the demonstration that **no amount of better judging tightens these bounds**: the bound is
  max(|CI_lo|,|CI_hi|), so removing judge noise shifts point estimates without shrinking sampling variance,
  and here the denoised estimates landed slightly *further* from zero. Exactly what §20.3's variance
  decomposition predicted. The artifact is written **`provisional: false`** — §20.4 is a finished deliverable
  and the bounds stand at **2.1–2.3× the Doublespeak effect**. Only more prompts help; the ceiling is 179.
- **20.7 Compute dominates; the direction term buys ≤23 %. [V]** §7.5's central negative was measured on binary
  ASR at **0.05 power** (an uninformative null). Re-asked on the optimization objective (best-so-far GCG loss;
  continuous, paired, judge-free, full n=37): 5→200 steps improves **37/37 prompts** at **p=1.1e-07** for all three
  arms — a demonstrably sensitive endpoint. On it, **0 of 18 arm contrasts are significant**, and they are
  *bounded*: the mechanism−vanilla advantage is at most **22.7 %** of the compute effect (mechanism−random 17.1 %).
  **This converts the program's weakest claim from "we found nothing, with 5 % power" into "we found nothing, on an
  endpoint able to find something 4× smaller than what we sought."** **200→600 update [V] [c2]:** the seed-42
  extension has since completed at full n — `outputs/asym_p207_objective_curve_seed42_FINAL37.json`
  (`n_paired 37, n_expected 37, interim false`, commit `dce44a92`) gives **mean Δ −0.0723, p=0.2515, 22/37
  prompts improved: a NULL.** This *supersedes* the earlier "the estimate oscillates −0.079/−0.122/−0.062 as n
  fills in" reading — the oscillation was interim noise and the full-n answer is that tripling compute past
  200 steps buys nothing detectable. (Seeds 43/44 still filling in; see §23.) *(Compute effect
  and 0/18 nulls JSON-confirmed; the specific loss-unit bounds 0.2151/0.1618 are report-only but their ratios are
  internally consistent. Objective space only — licenses no behavioural claim.)*
  > **[c3] [W] The seed-42 "NULL" above is WITHDRAWN; the bounds' provenance gap is CLOSED. See §26.3.**
  > All three seeds reached 37/37 and the **pre-registered** pooled read (per-seed deltas averaged per
  > prompt, then Wilcoxon over 37 prompts) gives **Δ −0.1303, 26/37 improved, p=0.0023 — a real gain.**
  > Seed 42 alone was underpowered, not right; the 2000-step point is **descoped on efficiency** (14.9×
  > worse per step), not on absence of gain. Separately the report-only bounds now have a deterministic
  > artifact (`asym_p207_arm_bounds.json`): **0.2145 (22.7 %)** and **0.1637 (17.3 %, not 17.1 %)**, plus a
  > **third contrast the original omitted — matched_random−vanilla 0.2284 (24.1 %), the largest of the
  > three.** The honest headline is **"every arm contrast is bounded at ≤24 % of the compute effect."**
- **20.8 is BLOCKED, and no endpoint change fixes it. [BLK]** The corpus ceiling is **179** items (→ ~139 held-out
  after a disjoint 40-item train pool), not the 300 the plan assumes; at n=37 the paired-McNemar **power against
  §7.5's own reported effect is 0.05 — the false-positive rate.** The **graded endpoint does not rescue it**:
  0/18 significant either way, only **2.2 % tighter → effective-n multiplier 1.04×** (because 92.7 % of rows sit at
  exactly 0/1). *(An earlier "1.34×" was a standardization bug — binary width standardized by an assumed binomial
  SD vs graded by its empirical SD; corrected.)* **Resolution: report behavioural results as equivalence bounds,
  not point estimates; only a second corpus buys real behavioural power.** *(Endpoint-compare numbers **and**
  the corpus ceiling are JSON/CSV-confirmed: `data/clearharm/clearharm_179.csv` exists at the **repo root**,
  179 data rows, cols `instruction, category, clearharm_native_target, clf_label`. A previous revision of this
  log called the file missing — that was a search-scope error confined to `doublespeak_causality/`; the
  caveat is **withdrawn [c2]**.)*
- **20.5 / 20.6 / 20.9 — NOT STARTED; and §20.1's headline needs one more run. [BLK] [c2]** Previously absent
  from this log entirely, in either direction. Per `docs/OWED_SUBMISSIONS.md`: **§20.5, §20.6, §20.9 were
  never started**; §20.6 specifically is **blocked by the same 179-item corpus ceiling** as §20.4 pass 2
  (`SECTION20_RESULTS.md:207` — *"§20.6 and §20.4-pass-2 are blocked by the corpus, not the endpoint"*), which
  is the link that explains why §20.4 stopped at one planned pass. Separately, the **§20.1 μ sweep**
  (μ ∈ {0.1, 0.3, 1, 3, 10}) was **not run** (0 matching output dirs) and is *required before §20.1's "78 %
  cost" can go in the paper*: 78 % is the price of a **near-total pin** (Δproj ≈ −0.03), not the price of the
  coordinate as such. And §20.7 is delivered at **half its planned span** — the plan
  (`ASYMMETRY_SPRINT_PLAN_2026_08_11.md:607`) specifies **600 *and* 2000 steps**; the 2000-step point was
  deferred by decision.
  > **[c3] SUPERSEDED — three of these five items closed within 24 h; see PART I (§26).** The **μ sweep RAN**
  > in full (5 μ × 3 seeds + 3 free arms) and answers its question: the trade-off is **sharply convex**.
  > **§20.5 RAN and is non-provisional** — and its random-token floor *cut its own headline by 60 %*.
  > **§20.7's 2000-step point is formally DESCOPED by a pre-registered rule**, not merely deferred.
  > Still open exactly as stated: **§20.0's unwritten dev-split decision, §20.6 and §20.9** (both blocked
  > behind §20.8's corpus ceiling, on which see §26.5 and §31).

**What §20 changes about the paper:** (1) a **necessity/usefulness distinction** — the refusal coordinate is
necessary for the continuous attack yet useless as an optimization target (plain task optimization already moves it
−3.09 for free, ~9× further than the discrete mechanism objective managed), reconciling §20.1/§20.2/§7.5 without
any being wrong; (2) an **objective-vs-behaviour dissociation** distinct from representation-vs-behaviour; (3)
**every behavioural negative restated as a ±0.2 ASR bound**; (4) two methodological figures corrected (judge-flip
rate, graded-endpoint power); (5) a **powered null replaces an uninformative one** (≤23 % of the compute effect on
a sensitive endpoint).

---

# PART I — Section 20 closed: the μ sweep, the random-token floor, the pre-registered compute read (sub-sprint 6 cont., 08-14 → 08-15) [c3]

Part G left §20 with five items open and a standing warning that §20.7 and §23 "will move". They moved. This
part is the asymmetry sprint's closing ledger, verified for this log by `wf_e6bf3b59` agents `sec20-completion`
and `sec20-p207-final` plus two adversarial verifiers who re-opened every artifact. **Everything here is
objective-space or process; not one item in Part I licenses a behavioural claim.**

## 26. Section 20, item by item, at close

- **26.0 §20.0 governance was never executed — and the sprint says so in its own words. [BLK] [V]**
  §20.0 required *writing down the dev-split allocation decision* (which single contrast gets the untouched
  dev split) **before anything ran**. No such decision exists in `SECTION20_RESULTS.md`, `OWED_SUBMISSIONS.md`,
  or 8,700 lines of execution log. What the closing audit (`ccc1ae0a`) could do is verify that **dev was not
  spent**: the manifest holds **dev 37 / train 74 / test 37** of the 148 ClearHarm items used, all 31
  soft-prompt runs record `test_split=test`, all 111 per-prompt GCG runs ran `SPLIT=test`, and every §20.4 cell
  and μ-sweep arm reports `n_test=37` / `n_train=40`. The commit's own verdict: *"The process step was skipped
  and the risk did not materialise, which is luck and is labelled as luck."* **Dev remains the programme's only
  clean one-shot out-of-sample surface, and the decision is still owed before anything touches it.**

- **26.1 §20.1's μ sweep RAN — and the 78 % cost is the price of a *near-total pin*, on a sharply convex
  curve. [V]** 5 values of μ × 3 seeds (15 `task_orth` arms) plus 3 free `task` arms, all CE-scored under a
  single model load (`outputs/asym_p201_ce_musweep.json`, independently recomputed and reproducing to every
  printed digit; n_train 40 / n_test 37 in every arm, budget_rel 0.1, read at hs19/L18):

  | μ | mean Δproj (test) | suppression vs free | mean CE cost | sd of cost |
  |---|---|---|---|---|
  | *free* (`task`) | **−3.0903** | — | — | — |
  | 0.1 | −0.726 | 76.5 % | **19.5 %** | 37.9 |
  | 0.3 | −0.336 | 89.1 % | 34.5 % | 21.1 |
  | 1.0 | −0.032 | **99.0 %** | **76.9 %** | 11.1 |
  | 3.0 | −0.104 | 96.6 % | 98.0 % | 0.9 |
  | 10.0 | −0.004 | 99.9 % | **100.7 %** | 0.4 |

  **Reading: three quarters of the refusal coordinate's free movement can be removed for a fifth of the
  achievable CE reduction; the last percent costs everything.** Past μ=1 the penalty is pure damage (μ=10 makes
  *no* CE progress). This is exactly the question Part G said had to be answered before §20.1's "78 % cost"
  could go in the paper, and the answer **preserves the direction while re-scoping the headline**: 78 % is the
  price of pinning the coordinate *dead*, not the price of the coordinate. ⚠ The weak-μ end is noisy —
  per-seed costs at μ=0.1 are [62.6, 4.5, **−8.6**] %, i.e. **one seed's pinned run beat its own free arm** —
  and μ∈{1,3,10} are mutually indistinguishable on suppression. **[V] doc-vs-artifact:** `SECTION20_RESULTS.md`
  §1 still prints Δproj **−0.026** and free **−3.087**; the artifact says **−0.0321** and **−3.0903** (§1b of
  the same file quotes them correctly). §1's "78.0 %" is a *ratio of means* while §1b's 76.9 % is a *mean of
  per-seed ratios*; both are defensible, the document does not say they differ.

- **26.2 §20.5 RAN, is non-provisional — and its own random-token floor ate 60 % of its headline. [NULL] [V]**
  Two halves. (a) **Best-of-k from disk, zero GPU:** the §7.5 transfer runs had already left a source×target
  grid, so the pool statistic cost nothing — **1,110 off-diagonal rows across 6 cells** (mechanism ×
  matched_random × seeds 42/43/44; diagonal pairs dropped), ASR@k computed *exactly* via
  1−C(n_fail,k)/C(n,k). Majority-vote denoised: **ASR@1 0.2026 → ASR@2 0.2865, gain +0.0839.** (b) **The
  floor** — the arm that reframes it: 10 *un-optimised* 16-token random suffixes on the same 37 test prompts
  and the same evaluator (K=10 × 37 = 370 generations) give **ASR@1 0.2351** (per-suffix range 0.108–0.351,
  sd 0.0687, SE 0.0217) and **ASR@2 0.2840, gain +0.0489**. **So 58 % of the apparent best-of-2 advantage is
  max-statistic inflation that random tokens produce for free; the genuine excess is +0.0350.** Worse for the
  optimised arms: **every transferred cell (0.171–0.230) sits at or below the random-token floor (0.2351).**
  **[W] This forced a withdrawal in the paper-facing synthesis:** `ASYMMETRY_FINAL_SYNTHESIS.md` §7.5 point 2
  — *"per-prompt suffixes transfer (off-diagonal ASR 0.173–0.200 ≥ the universal arm's held-out 0.162)"* — is
  now marked **SUPERSEDED by §20.5**; against the floor it is no longer supported. The companion claim
  "compute dominates direction" is *refined*, not withdrawn: the matched-random 5→200 diagonal runs
  0.126 → 0.270, i.e. from **below** the floor to just above it. ⚠ Balanced k caps at **2** (off-diagonal pool
  sizes are 2–11 because the grid was sharded for eval cost), the vanilla arm has **no** transfer rows at all,
  and majority-vote denoising is valid **only** at threshold 0.5. **[V] doc-vs-artifact:** §8's table prints
  arm means 0.2074/0.2913; recomputation gives **0.2026/0.2865** — both 0.0048 high, which makes the arms sit
  *further* below the floor, i.e. the document errs conservatively. The gain and the excess are unaffected.

- **26.3 §20.7's endgame: a pre-registered read that reversed our own null. [POSITIVE, objective space] [V]**
  This is the single most instructive episode of the window.
  - **What was fixed in advance** (`69b7941e`, 2026-08-14 15:03:42, committed while seed 43 stood at 30/37 and
    seed 44 at 12/37 — i.e. auditable, not asserted): arm = vanilla; all three seeds at **37/37 or the script
    hard-exits**; exactly two budgets; **unit of analysis = the prompt, with per-seed deltas averaged *before*
    testing**; Wilcoxon signed-rank. Plus a three-part descope rule for the 2000-step point, anchored on seed
    42's then-only efficiency estimate of 27.4× — nearly 2× outside the threshold it set, so the rule was not
    tuned to the answer. A second guard was added because the default `--budgets 5,200,600` would silently
    return a 5→600 min/max contrast.
  - **The read** (`4cf662a3`, 20:28:41, 5 h 25 m later): per seed **−0.0723 (p=0.2515, 22/37) / −0.2224
    (p=0.0025, 25/37) / −0.0963 (p=0.0714, 25/37)**; **pooled Δ −0.1303, 26/37 improved, p=0.0023.**
    Sensitivity anchor on the same prompts: **5→200 gives Δ −0.9463, 37/37, p=1.46e-11, significant in 3/3
    seeds.** The 200→600 effect is **7.3× smaller** than the 5→200 jump.
  - **The verdict: 1 of 3 criteria met** — pooled p **PASS** (0.0023); ≥2/3 seeds individually significant
    **FAIL** (1/3, though all three are sign-consistent); per-step efficiency within 10× **FAIL** (0.004853 vs
    0.000326 loss/step = **14.9×**). **The 2000-step point is DESCOPED by rule — on measured inefficiency, not
    on absence of gain.**
  - **[W] What this withdraws is ours:** Part G's "the full-n answer is that tripling compute past 200 steps
    buys nothing detectable" was seed 42 alone. The sprint's own commit names it: *"my seed-42 null at 18:00
    was underpowered, not right… fourth time in this sprint a single-seed read misled, and the first where the
    correction runs the opposite way."*
  - **Run integrity, verified independently at full coverage:** 111 `asym_p75_vanilla_s600_pp_*` dirs (37 per
    seed), **111/111** with `FINAL_CANDIDATES.jsonl`, ITERATION_LOG row histogram exactly `{600: 111}`, set of
    `n_train_tasks` = `{1}`. Total per-prompt inventory under the **project-level** `outputs/stage_gcg_perprompt/`
    is **778 directories** (777 §20.7-shaped + 1 stray `mechanism_s10`) — **none of them registered** (§22).
  - **The bounds' provenance gap is closed [V]:** §20.7's headline equivalence bounds had, for days, **no file
    anywhere** — a scan of 1,881 JSONs found the quoted 0.2151/0.1618 only as coincidental matches in unrelated
    studies. Recomputed and persisted (`asym_p207_arm_bounds.json`, rng_seed 20260815, n_boot 10000; re-running
    the script reproduces the committed JSON **bitwise**): mechanism−vanilla **0.2145 (22.7 %)**,
    mechanism−matched_random **0.1637 (17.3 %)**, and **a third contrast the original omitted —
    matched_random−vanilla 0.2284 (24.1 %), the largest of the three.** All 18 underlying arm contrasts remain
    **0/18 significant** (min p 0.0896). *A headline number survived multiple audits before anyone checked it
    had a file.*
  - **[c3] Two defects still live in `SECTION20_RESULTS.md` §7:** its extrapolation warning says the log-linear
    fit "predicts ≈−0.55 over 200→600" — the fit predicts **−0.250** over 200→600 (slope −0.22794 × ln 3);
    **−0.525 is its prediction for 200→2000**. The qualitative point (do not extrapolate the fit) survives; the
    overprediction is 1.9×, not ~4×. And §7's provenance line still cites `asym_p207_objective_curve.json`,
    which is the **n=18 interim seed-42 file** (`interim: true`, 200→600 p=0.133), not the full-coverage
    artifacts its numbers come from.

- **26.4 §20.4 is closed — on a *substituted* pass 2. [B] [V]** Restating Part G precisely: the plan's pass 2
  required a multi-direction SD from §20.6, which is corpus-blocked and therefore unreachable; the artifact
  says so itself (`why_not_the_planned_pass2`). What ran instead was the judge-denoised endpoint, and it made
  the bounds **6.4 % wider** (0.2117 → 0.2252). **Do not report this as the planned pass 2.** The
  bounds-vs-Doublespeak ratio was corrected in the same pass from "1.9–2.7×" to **2.1–2.3×**.

- **26.5 §20.6 and §20.9 are still BLOCKED, and the block is now a *decision*, not compute. [BLK]** Both sit
  behind §20.8's n=300, which ClearHarm's 179-item ceiling cannot supply. The closing ledger reclassifies them
  and puts a recommendation on record — **Option 3: move to continuous endpoints**, which are adequately
  powered at n=37 where binary ASR is not. ⚠ **Nobody has weighed that recommendation against the one
  measurement bearing on it:** `asym_p208_endpoint_compare` found the graded endpoint only **1.04×** better
  powered than binary ASR *here* (0/18 significant either way, widths 0.598 vs 0.585), because 92.7 % of rows
  sit at exactly 0/1. §20.9's four sub-items (collateral-displacement decomposition; a discretization ladder
  with a discretization-aware optimizer; a 20-direction displacement-matched behavioural null for Gate D; a
  cross-family port with per-model direction validation) were never started. **§20.9's cross-family item is
  *not* discharged by Part J's Phi/Qwen replication** — different construct, different gate.

## 27. Asymmetry-sprint process findings that stand on their own [c3]

1. **A shell GPU guard that could not report its own failure.** Under `set -e`,
   `VRAM_MB=$(nvidia-smi … 2>/dev/null | awk …)` aborts the job **at the assignment**, so the `if [ -z
   "$VRAM_MB" ] … echo ERROR` branch below it was unreachable dead code and `2>/dev/null` discarded the only
   diagnostic. Job 757702 landed on an 8×V100 DGX and died in **14 s with exit 13 and an empty stderr**. Fixed
   in `run_gcg_perprompt.slurm` (`dce44a92`) and `run_perprompt_eval.slurm` (`c5dc5d84`) by splitting the probe
   from the assignment. ⚠ Both files are project-level and shared with pipelines outside this sprint; **any
   other script using the same idiom still carries the bug.**
2. **A benchmark computed, believed, caught, and deliberately kept as a warning.** With no floor on disk,
   ASR@2 was compared against 1−(1−p)² as an independence reference and sat *above* it in all six cells — first
   read as clustering. Wrong: ASR@k here is exact sampling **without** replacement from pools of 2–11 while
   1−(1−p)² is **with** replacement, so on tiny finite pools the former is mechanically larger. Kept in the
   artifact under the field name `…_with_replacement_ref_NOT_a_floor`. No result depended on it — the real
   floor superseded it before it propagated.
3. **A concurrency-cap breach, self-corrected in the right direction.** Another session's job took the account
   to 7 running against the ≤6 rule; the asymmetry session cancelled **its own newest job**, not the other
   session's, and because the eval is resume-safe and row-keyed all 111 existing rows survived. In the same
   episode the **B9 absolute-position guard fired for the third time in this repo** (`capture=179` vs
   `corpus_query_last=209`), catching the mismatch before anything was written — the same check that
   `50b7ee93` subsequently relaxed to a soft warn (§28.5).
4. **The execution log's clock is wrong by 7–18 hours and dates 50+ entries to 2026-08-16, a day that has not
   occurred.** The log ticks a fixed 30 min per entry while real ticks ran faster, so drift accumulates
   monotonically (`dce44a92` at 11:38 logged as 18:45; `cd08f722` at 17:37 logged as "2026-08-16 11:15").
   Ordering *within* the log is internally consistent; **absolute stamps and calendar dates are not, and
   cross-references inside commit messages resolve against log-time, not wall-time.** No post-cutoff entry in
   that log can be ordered against `sacct`.
5. **21 % of the post-cutoff commit history carries no content** — 34 of 164 commits are `idle tick` /
   `quiet tick` / `short tick`. Harmless as process hygiene, but they inflate any commit-count read of
   activity, and they are the entries carrying the clock drift above. **[c4] In the 08-15 → 08-16 window the
   ratio is worse: 31 of 49.**
6. **[c4] A monitoring command that could not distinguish "empty" from "failed" — and the recognition of the
   trap did not prevent walking into it.** During a `slurmctld` outage (controller down, `slurmdbd` up, so
   `sacct` liveness was unusable too) the per-tick queue check returned no output and exit 0, and was read as
   *"controller recovered, queue empty."* It was neither. **Two failure modes stacked in a command used every
   tick for days:** `squeue -h` suppresses the header, so *no jobs* and *died before printing* are
   byte-identical; and an `rc` read **after a pipe** reports `head`'s status, not `squeue`'s, so the failing
   command's exit code was never visible. The log's own note is the finding: *"one tick after writing that
   count=0 is a failed query rather than an empty queue, I ran that one-liner and believed it. Recognising the
   trap in principle did not stop me walking into its concrete instance."* **Fix: drop `-h` so the header
   proves the controller answered, capture `out=$(squeue …); rc=$?` rather than testing a pipeline, and claim
   emptiness only when the header is present.** *Three consecutive ticks were recorded as queue-state UNKNOWN
   rather than empty — which is the right behaviour and is why this is a finding rather than an incident.*

---

# PART J — the Role-Probe sub-sprint: role confusion × Doublespeak, and the cleanest dissociation in the programme (sub-sprint 7, 08-14 → 08-15) [c3]

`docs/ROLE_PROBE_NEXT_SPRINT_PLAN.md` → `docs/ROLE_CONFUSION_DOUBLESPEAK_CAUSAL_SYNTHESIS.md`. Opened
2026-08-14 **on the same branch, running concurrently with the asymmetry sprint** (see the disambiguation
note at the top of this document). Verified for this log by `wf_e6bf3b59` agents `role-probe-sprint`,
`factorial-storyB`, `crossmodel-gate1`, `phase4-5-behavioral`, `d3-scope` and their verifiers; **every
load-bearing number below was re-derived from `acts.npy` / `raw.jsonl` by at least two independent agents
in addition to the sprint's own audit.**

## 28. What the sub-sprint is, and how the probe was built

- **28.1 The imported hypothesis.** *Prompt Injection as Role Confusion* (third-party snapshot below) argues
  that a model infers **who is speaking from how text sounds**, not from its role label, and that an injection
  succeeds by relocating text into another role's latent representation — measurable **pre-generation** by a
  controlled linear probe. **Our analogue replaces "role" with "contextual semantic identity":** same surface
  codeword, different contextual binding. The sharp question the upstream design leaves open — and which its
  own repository cannot answer, because **it contains no causal intervention at all** (verified by grep, plan
  Appendix A9.9) — is whether the latent confusion **causes** the jailbreak or merely accompanies it. *That gap
  is the sub-sprint's entire scientific opening.*
- **28.2 The third-party snapshot.** `third_party/prompt_injection_role_confusion/` is a frozen, deliberately
  **non-git** source snapshot at commit `ec333c40` (2026-05-31, **MIT**), 110 files / 7.3 MB, imported as a
  reference implementation with an explicit reuse-mapping table in `SOURCE_INFO_LOCAL.md` (port as-is /
  adapt / concept-reused-code-rewritten / explicitly not reused). ⚠ **Compliance gap [V]:** that file mandates
  an `Adapted from: … ec333c40 … MIT` header on adapted code; `grep -rn 'Adapted from' src/probes/` returns
  **nothing**, and the planned `src/probes/probe_projection.py` was never written. In practice our probe was
  written fresh against the upstream *design*, so **the honest statement is "independent reimplementation of a
  published method", and the log says so rather than leaving the attribution requirement silently unmet.**
- **28.3 The probe ("Probe B", contextual-binding Bombness).** For the **same single-token codeword X**:
  positive = the Doublespeak prompt (demos bind X → its harmful target), negative = the Benign prompt (X →
  a benign concept). Read `resid_post` = `hidden_states[L+1]` at the **query codeword** (`codeword_last`) and
  the **decision token** (`final_prompt`). L2 logistic regression (C grid 1e-4…1e1), **fit on train, C/layer/
  position selected on dev, evaluated exactly once on the frozen test holdout**; bootstrap CIs resample
  **examples**, not token rows; `fit_and_eval` raises if any train example id appears in eval. Extraction is
  batch-1 (no left-pad/arange drift — bug class B9), chat-templated. **[V] Split, because a reader will hit
  the ambiguity:** the claim table's "train 162 / dev 82 / test 80" is the *whole* v3 corpus (324 = 170
  clearharm + 154 generated); **every probe and behavioural number in this part is the clearharm cohort:
  train 85 / dev 43 / test 42** (generated: 77 / 39 / 38). **Frozen decision D1:** our raw post-block space,
  *not* upstream's normalized mid-block space, because Phase 4 must steer in the space the hooks write to —
  a choice separately shown not to matter (§28.6).
- **28.4 Gate 1 — the pre-registered validity gate. [V]** Four checks: holdout AUC ≥ 0.70 **and** CI_lo > 0.55;
  all five trivial controls below holdout−0.10 **and** below 0.65; |dev − holdout| ≤ 0.15; CARROT
  cross-codeword transfer ≥ 0.60. **Llama-3.1-8B: holdout AUC 0.9972 [0.9898, 1.000] @L11** (C=10, dev
  0.99946, n_train 85 / n_holdout 42, verdict PASS), decision token 0.9643 [0.9297, 0.9932]. **Controls:**
  label-shuffle 0.4649, random-direction 0.5286, position 0.5782, length 0.5873, and **token-identity exactly
  0.5000 — exact by matched-pair construction, because the positive and negative share the codeword.**
  Geometry: **cos(Bombness, refusal_L18) = 0.0912 at the codeword** (per-layer 0.0062–0.1475) versus **0.4675
  at the decision token** — the two constructs are orthogonal where the remap happens and entangle only where
  the decision is read. ⚠ **[V] Audit gap the reports do not state: the CARROT transfer check never ran.** The
  corpus holds 3 carrot rows (2 labelled) against a threshold of 4, so `transfer` is `null` and `transfer_ok`
  passes by short-circuit in **all four** Gate-1 runs. **Every Gate-1 PASS here rests on 3 of its 4 checks.**
  What carries the generalization claim instead is genuine and was verified independently: **the holdout is
  codeword-disjoint — 22 test codewords, zero overlap with the 27 train codewords** — so Gate 1 *is* a
  cross-codeword generalization test, it is simply not the one the docstring advertises.
- **28.5 The preflight that was relaxed, and what it cost. [c3]** The extraction preflight originally
  hard-aborted on a mismatch between the resolved codeword position and the corpus's precomputed templated
  span. It aborted — correctly — and the root cause proved to be a **data-quality defect in the v3 corpus, not
  a bug**: `codeword_occurrences_templated` spans were computed on a different rendering than the stored
  prompt (counts differ for ~65 % of clearharm and ~50 % of generated examples). Since extraction resolves
  positions per example on the *actual* templated prompt, and Gate 1's controls come out clean, `50b7ee93`
  downgraded the corpus-span cross-check to a **soft warn-only match rate** (B19). **Correctness impact: none.
  Cost impact: not none** — that weakened guard is the direct reason AdvBench extraction 758599 burned **19
  GPU-minutes** before crashing on a codeword missing from a *neutral* prompt, a condition the relaxed
  preflight does not anchor (§30). *The corpus-span anchor was the only external cross-check on position
  resolution; the guarantee now rests entirely on per-example resolution.*
- **28.6 Robustness to the residual-space choice. [V]** Re-extracting in **upstream's** normalized mid-block
  space (`post_attention_layernorm`) and refitting gives **holdout AUC 0.9943 [0.9841, 1.000] @L7** versus
  0.9972 @L11 in our space — the headline is not a cherry-picked space. Llama-only, Gate-1-only (geometry,
  Phase 3 and Phase 4 were not repeated there, by design).

## 29. The five independent designs — and Bombness fails all five [V]

Every arm: Llama-3.1-8B-Instruct, clearharm **test n=42**, α=1.0 full `project_out` at the query codeword over
**L8–18**, readout at unpatched layers 20/24/28/31, StrongREJECT ≥ 0.5, greedy decoding, `empty_rate` 0.000,
each with its own **norm-matched random-direction control** and its own **refusal-ablation positive control in
the same run**.

| # | design | Bombness result | refusal control in the same run |
|---|---|---|---|
| 1 | **prediction** (Phase 3, frozen holdout) | AUC **0.592** [0.506, 0.855] | **0.976** [0.921, 1.000] |
| 2 | **necessity** — ablate (757931) | ΔASR **−0.048**, p=0.625 (= its random control) | **+0.238**, b/c 13/3, **p=0.021** |
| 3 | **sufficiency** — inject into neutral at on-manifold dose 0.25 (757992) | ΔASR **+0.048**, p=0.50; refusal rate unchanged 0.667 | **+0.333**, b/c 16/2, **p=0.0013** |
| 4 | **2×2 factorial** Bombness × refusal (757943) | main effect **+0.000** [−0.071, +0.071]; **interaction +0.000** [−0.143, +0.143] | main effect **+0.357** [+0.202, +0.500], b/c 16/1, **p=0.00027** |
| 5 | **per-example component surgery** (Phase 5, 758162/758163) | ΔASR **+0.048** [−0.048, +0.143] **both ways**, at readout ±18.7/+18.9 vs ±0.2/0.65 random | (Phase-4 controls above) |

- **29.1 Prediction (Phase 3) — the dissociation before any intervention.** n=170 fit / **42 holdout with 7
  successes**. Nested models: Bombness-only 0.5918, **Refusalness-only 0.9755**, both 0.9592
  (**Bombness adds −0.016 after conditioning on refusal**). Paired gap **+0.3837 [0.1135, 0.4815]**, excludes 0.
  Success by Refusalness quintile is **monotone** (0.50 / 0.53 / 0.21 / 0.00 / 0.00); by Bombness **flat**
  (0.21 / 0.27 / 0.24 / 0.35 / 0.18). Outcomes joined by `example_id` from an *independent* behavioural run.
  ⚠ **Two scope corrections [c3]:** (a) the reports call Bombness "at chance", but its CI is [0.506, 0.855] at
  n=42 — **the defensible claim is the paired gap, not "chance"**; (b) **these CIs are pre-fix.** The bootstrap
  took `max(a, 1−a)` per resample (a bias toward 0.5-inflation), fixed on 2026-08-15 16:57 — *after* both
  JSONs were written (08-14) and **never recomputed**. The bias is conservative for the gap (a debiased
  Bombness CI sits lower, the gap's exclusion of 0 gets *more* conservative), so no verdict moves, but the
  published intervals are stale.
- **29.2 Necessity, sufficiency, and the 2×2 — Story A vs Story B, adjudicated.** The plan pre-registered two
  endpoints (§22): **Story A** — the identity confusion is real but behaviourally epiphenomenal, with a
  separable refusal-suppressed control state as the lever; **Story B** — Bombness becomes causal *only* under
  low refusal (a **gated** interaction), which would have made the programme's earlier "epiphenomenal concept
  circuit" conclusion *incomplete rather than wrong*. The 2×2 is the direct discriminator: all four cells in
  one paired run on the same 42 prompts — **0.2143 / 0.2143** (refusal intact, Bombness high/low) and
  **0.5714 / 0.5714** (refusal suppressed). **Bombness is inert in both refusal states. Story B is refuted;
  Story A holds in its strongest form: neither necessary, nor sufficient, nor gated.** *(Pre-registration
  scope, honestly: the plan file has a single commit at 2026-08-14 16:36, which is **before the 2×2 ran**
  (757943, 16:47) but **after** the necessity run launched (757931, 16:06). "Pre-registered before the 2×2" is
  supportable; "before any Phase-4 GPU ran" is not.)*
- **29.3 The manipulation checks fired — these are verified nulls, not dead hooks.** Ablation drops the
  downstream readout **−1.32 / −1.30 / −1.39 / −1.62** at L20/24/28/31 (gate: all < −0.5) while the
  norm-matched random arm leaves it untouched; injection raises it **+5.20 / +4.84 / +5.27 / +7.79** (gate: all
  > +0.5) and lands **on-manifold**, at the natural Doublespeak level. ⚠ The readout is *the same direction
  being ablated*, so it certifies removal of the **probe-readable linear component**, not of every
  BOMB-related computation — a non-linear or off-direction remnant would be invisible. **That is the residual
  escape hatch for Story B, and Phase 5 is what narrows it.**
- **29.4 Phase 5 — the sharpest form, and the one that could not have been a re-run.** A *mean-field* Phase 5
  would have been Phase 4 again: `v_bomb` **is** the unit mean diff-of-means (**cos = 1.00000** at every band
  layer, verified before spending GPU). So Phase 5 did the non-redundant thing — **per-example** surgery,
  installing or removing *each example's own* Bombness component of its own donor shift. Result: readout moves
  **−18.7 / +18.9** (random: −0.16 / +0.65) and **ΔASR is +0.048 in both directions**, identical to random.
  **And the ~80 % example-specific orthogonal remainder is inert too** (0.000 / −0.024) — so there is no hidden
  lever the mean direction missed. Two things the reports do not say and this log must: (a) **the under-reported
  `full` arm is the strongest statement in the sub-sprint** — substituting the *entire* codeword-position state
  from Doublespeak to benign across L8–18 (readout −10.5) gives **ΔASR −0.048, n.s.**: *the whole
  representational difference at that position is behaviourally inert*; (b) **[c3] the Phase-5 dose is ~10×
  off-manifold by the sprint's own §8.2 criterion** — its ±13…19 readout regime is *exactly* what E23 rejected
  when calibrating Phase 4's dose to 0.25. This does not overturn the null (a null under a 10× overshoot is a
  stronger no-effect statement) but it changes its wording: *a large, off-distribution perturbation of the
  Bombness coordinate does not move behaviour*, with the on-manifold case covered by Phase 4.
- **29.5 The representational precondition (zero-GPU energy decomposition).** Over 170 (doublespeak, benign,
  neutral) triples, the codeword-position donor shift carries **frac_bomb 0.216 / frac_refusal 0.0021 /
  remainder 0.784** in the write band L8–11 (index-alignment self-check cos = 1.000 at every layer). **Invariant
  across families:** the refusal axis carries **≤ 0.6 %** of that energy in Llama, Phi and Qwen. **Divergent:**
  the Bombness share *falls* with depth in Llama (0.216 → 0.133) and Phi (0.190 → 0.075) but *rises* in Qwen
  (0.167 → 0.253) — read qualitatively only, since the bands are absolute layer indices and Qwen has 40 layers.
  *(Corrections to the report's own bounds: its "frac ≤ 0.002, cos ≤ 0.05 everywhere" is false for Llama —
  band 0.0048, per-layer max 0.0055, cos max 0.059 — and contradicts its own table; the correct bound is
  ≤ 0.006. The claim table's "frac_bomb 0.13–0.25" should read 0.075–0.253.)*
- **29.6 Cross-cohort (generated) — the probe generalizes, the *predictor* does not, the causal arm is
  BLOCKED. [B]** Gate 1 replicates strongly on a distributionally different cohort (**0.9972 [0.9896, 1.000]**,
  n=38, token-identity 0.500) and **Bombness is non-predictive there too** (0.51 oriented / 0.49 directional).
  But the frozen ClearHarm refusal direction predicts at only **0.525** with the refusal−Bombness gap CI
  spanning 0 [−0.214, +0.157], and a *native* decision-token probe reaches only 0.60–0.63 versus ClearHarm's
  0.98. **The directional dissociation survives; the effect size is ClearHarm-specific** — attributable to the
  cross-distribution transfer of the refusal direction (B17) and to generated jailbreaks being inherently less
  predictable. **The generated *causal* run (757967) is machine-stamped INCONCLUSIVE**: its manipulation check
  moved the readout **the wrong way** (+0.30 to +0.68), so `manipulation_check_passed = false`. ⚠ **Its one
  nominally non-zero cell (+0.105 under intact refusal) must not be quoted as a Bombness effect** — the
  identical shift appears in the norm-matched random arm (specificity exactly 0.000), the check failed anyway,
  and its *direction* is opposite to Story B's prediction. The refusal positive control does replicate there
  (+0.2105, p=0.021). **So the causal story is single-cohort**; the synthesis line calling that run "deferred"
  is stale — it ran, and it failed its check.
- **29.7 Cross-model — three families, and an honest tension. [V]** No per-model code: `MODEL`/`QUANTIZE`
  env passthrough only.

  | model | hidden | Gate 1 holdout AUC | Bombness necessity ΔASR | refusal ablation ΔASR | base refusal |
  |---|---|---|---|---|---|
  | Llama-3.1-8B-Instruct (bf16) | 4096 | **0.9972** [0.9898,1.000] @L11 | **−0.048** (p=0.625) | **+0.238 (p=0.021)** | 0.643 |
  | Phi-4-mini-reasoning (bf16) | 3072 | **0.9853** [0.9665,0.9983] @L10 | **−0.071** (p=0.581) | +0.095 (p=0.388) | **0.048** |
  | Qwen3-14B (**8-bit**) | 5120 | **0.9989** [0.9949,1.000] @L15 | **+0.048** (p=0.625) | **+0.167 (p=0.039)** | 0.119 |

  **Bombness necessity is null on 3/3 families, each equal to its own random control, with the manipulation
  check passing on all three** (Phi −6.2…−8.4, Qwen −4.0…−5.8 — both *stronger* manipulations than Llama's
  −1.3…−1.6). **The representation-≠-behaviour dissociation is cross-family.** The refusal lever is where the
  honesty is required: commit `6e3569ae` first concluded *"refusal-lever is Llama-specific"*, and ~1.5 h later
  `acd9a996` **superseded it** — with Qwen added, refusal is significant on 2 of 3 families and Phi's null is
  re-read as a **base-refusal floor artifact** (Phi's Doublespeak base refusal is 0.048 = 2/42 prompts: there
  is almost nothing to ablate). We carry the second reading, **flagged as post-hoc**, with four caveats the
  synthesis does not state: (1) **the floor hypothesis was never tested** — no Phi arm with high baseline
  refusal was run; (2) **[c3] an alternative explanation exists and is nowhere recorded — the Phi run used
  refusal direction L16, which the repo's *own* selection artifact rejects** (`both_gains_positive: false`;
  it selects **L14**), so Phi's null may be a wrong-direction artifact rather than a floor; (3) **Qwen's
  p=0.039 rests on 9 discordant pairs and would not survive Bonferroni across three families** — no
  multiplicity correction is applied anywhere; (4) **every Qwen number is 8-bit** (generation too, not just
  activation reading), while the quantization-robustness evidence licensing that is Llama-only, so Qwen's
  position on the "susceptibility spectrum" is confounded with precision. **Also: the intervention band
  (L8–18) and readout layers (20/24/28/31) are Llama-32-layer constants applied unchanged to Qwen's 40 layers —
  absolute, not depth-matched.** Finally, **Phase 3 is a Llama-only result**: no `dual_state_predict.json`
  exists for Phi or Qwen, and the Phi AUCs quoted in prose (0.525 / 0.575) are **[R]** and not recomputable —
  the Phase-4 `raw.jsonl` carries no `refusal_proj` column despite the script docstring promising one.
  *(Commit `683aad3d`'s title "all Phi/Qwen numbers raw-reproducible" should read "all Phi/Qwen **Gate-1 and
  Phase-4** numbers".)*
- **29.8 Judge nondeterminism — an audit finding in no report. [c3] [V]** Runs 757931 and 757943 produced
  **byte-identical greedy generations** for all 42 examples in all four shared arms, yet **the StrongREJECT
  judge disagreed on 3–6 examples per arm**, moving the refusal positive control from **+0.238 (p=0.021) to
  +0.357 (p=0.00027)** and the Bombness necessity estimate from −0.048 to 0.000. **Judge noise alone is the
  same magnitude as every Bombness "effect" in this part.** Direction of the correction is favourable — it
  widens the noise floor around zero, so the nulls are if anything more robust — but **the refusal control's
  point estimate and the 2×2's CI must be read as judge-noise-inflated**, and no report states this. It also
  means commit `5d27bf23`'s aside ("neu_base 0.214 ≈ ds_base 0.214: the doublespeak framing itself doesn't
  raise ASR") is a **cross-run** comparison inside the noise band and should be downgraded to "no detectable
  difference at n=42".

**29.9 What Phase 9 did — nothing, by rule.** Because Gate D resolved to **Story A**, the plan's §13 decision
rule ("do **not** optimize an epiphenomenal coordinate") fired and **Phase 9, the attack-objective phase, was
formally CANCELLED — a pre-registered phase killed by its own gate**, structurally the same as §20.7's
2000-step descope. ⚠ State it precisely: **"Bombness is not attackable" is NOT established** — no GCG/TROPT run
was ever executed against a Bombness objective. What is established is *"not worth attacking, given
epiphenomenality."*

## 30. D3 — the scope-matched activation control, and what it does to the ladder [V] [c3]

The control Part F called *"the single cleanest missing control"* and *"the control a reviewer will ask for
first"* ran on 2026-08-15 in a ~90-minute window. **Same axis (L18), same α=1.0, same held-out split (n=42
harmful / 10 benign, VALN=0, nothing tuned on eval), three narrowing intervention scopes:**

| scope | clearharm refusal-rate gain | existing family | retained vs all-layers | p vs random |
|---|---|---|---|---|
| **all layers / all positions / all decode steps** (the published Arditi configuration) | 0.881 → 0.071, **+0.810** | **+0.571** | 100 % | ≈ 0.0 |
| **single layer L18 / all positions** | 0.881 → 0.429, **+0.452** | **+0.429** | 56 % / 75 % | 4e-06 / 8e-06 |
| **L18 / decision position / prefill only** — *scope-matched to a token attack* | 0.881 → 0.857, **+0.024** | **+0.000** | **3 % / 0 %** | **1.0** |

The norm-matched random control is **exactly +0.000 at every scope**, and `separation_heldout` is **identical
across all three arms** (0.1744 / 0.2213) — *the direction is equally readable at every scope; only the
behavioural effect collapses.* The decision rule was fixed in code before the read (`retained < 0.34` →
verdict "LARGELY SCOPE").

**What it means, stated carefully.** **The layer restriction is cheap (−25 % to −44 %); the position
restriction is total.** So the programme's "activation ≫ continuous ≫ discrete" hierarchy is **largely the
intervention-scope confound made quantitative, not evidence that the activation medium is privileged.**
**What it does NOT do:** it does not overturn the token-space negatives of §13/§18/§19, §20.5 or §20.7 —
those are *measurements* on the behavioural endpoint — and it does not revive the mechanism-guided objective,
which §20.5's random-token floor independently killed. **It changes the explanation of the gap, not the gap.**
⚠ **Endpoint caveat, load-bearing:** D3 is measured on the direction-validation **keyword refusal rate**, not
on StrongREJECT Doublespeak ASR; carrying it to ASR is currently an *inference*. Single model, single layer,
single α, single split; the `decision` arm is **one position at one layer**, narrower than a real 16–20-token
suffix propagating through all layers — **the genuinely budget-matched arm (multi-position, or all-layer at
suffix positions) has not even been proposed.** And the null is bounded loosely: 1/42 flips at n=42 excludes a
large effect, not a small one.

**Two process items from the same 90 minutes, kept because they are the record.** (a) **[W] A 4-prompt smoke
run was written up as a held-out finding** — the 04:15 entry (`12aa2141`) presented run 758209 with a table and
an interpretation ("ablation is exactly zero where a token attack reads"); `fb442d0c` withdrew *everything
substantive* in it on discovering `VALN=4`, and the smoke's `valid=False` — the entry's sharpest sub-claim —
**flipped to `valid=True` at full n**. The correction also fixed the reading rule *before* the real data landed.
⚠ The smoke run sits in `EXPERIMENT_REGISTRY.csv` as **COMPLETE with nothing recording n_eval=4** — a reader
mining the registry could repeat exactly this error. (b) **[c3] The report's claim of an "independent
replication" by a concurrent session does not hold.** `D3_SCOPE_COMPARISON.md`'s provenance box says two
sessions ran D3 and "both agree to the decimal"; the other session's own commit (`98a28eba`) states it
**launched no D3 job**. There is **one** set of GPU results (a single launch lineage: 758248/9/50 cancelled
while PENDING, resubmitted as 758290/1/2). What *is* true, and worth keeping: **two sessions independently
analysed and scored the same artifacts and reached identical numbers and verdicts** — and the reconciliation
caught a real defect, a *half-annotated document* asserting both "resolved" and "NOT RUN" about D3 in two
places of the same file. The rule adopted: *"before annotating a claim, search the whole file for every
statement of the same fact."*

## 31. Phase 10 — the second corpus: **COMPLETE. Story A replicates at ~2× power.** [V] [c4]

§20.8's diagnosis was that the binding constraint is the **corpus**, not the endpoint. Phase 10 executes the
plan's Option 2 — an **independent** second corpus, deliberately *not pooled* with ClearHarm.
`scripts/build_advbench_doublespeak.py` rebuilds the locked Doublespeak pipeline on **public AdvBench** (520
goals, sha256 `6cd1a5c6…`) → `advbench_doublespeak_v1.json`: **n=399, train 230 / dev 81 / test 88** (≈2×
ClearHarm's 42), 108 concepts, 20 codewords, leakage-0 (concept- and codeword-disjoint; re-verified
independently: PASS, 1,197 items, 0 straddles, 0 locatability failures). **This is the third revision of the
corpus** (417 @ 244/87/86 → 417 @ 241/91/85 → 399 @ 230/81/88), so `OWED_SUBMISSIONS.md`, which still prints
the first, is stale. **Deliverable: `reports/PHASE10_REPLICATION.md`.**

**31.1 The behavioural core — the refusal lever replicates and is now *significant*, not CI-bounded. [V]**
Phase 4 on the AdvBench test split (n=88, base ASR 0.205, run 758657), same harness, same StrongREJECT ≥0.5:

| arm | ΔASR | McNemar (b = losses, c = gains) | manipulation check |
|---|---|---|---|
| **refusal ablation (the lever)** | **+0.295** | b=3, c=29, **p=0.0** | refusal rate **0.636 → 0.193** |
| Bombness necessity (ablate v_bomb) | +0.057 | b=5, c=0, p=0.0625 **n.s.** | readout −0.76…−1.57, **passed** |
| Bombness **vs norm-matched random** | +0.034 | b=4, c=1, p=0.375 **n.s.** | — (bomb ≈ random) |

**2×2 factorial (n=88):** main effect refusal **+0.284 [0.188, 0.381]**; main effect Bombness **+0.046**;
interaction **−0.023 [−0.102, +0.057]** — no gating. **This is Story A reproduced on an independent harmful
corpus, with the refusal effect now at p=0.0 rather than a bound.** ⚠ **The one number that needs saying
carefully:** on v1 the Bombness 2×2 main effect is +0.0455 with CI **[0.0114, 0.0852] — which excludes zero.**
The report handles this correctly and so must the paper: **it is exactly the size of the random-direction
effect (+0.034, p=0.375), so it is non-specific, not a causal Bombness channel** — *the specificity control,
not the CI, is what carries the claim.* On the clean v2 corpus it shrinks to **+0.017 [−0.023, +0.057]**,
which does include zero.

**31.2 A real confound was found in our own probe — and fixed. [c4]** Gate 1 on AdvBench v1 gave holdout AUC
**0.982**, but **`position_only` 0.785 and `length_only` 0.752** — nowhere near chance. Cause: the v1 builder
did **not length-match the Doublespeak vs benign demo blocks**, so the codeword's absolute position (mean gap
**−18 tokens**) and the prompt length correlated with the label. *That is a property of the corpus, not of the
readout* — but it fails Gate 1 as written. **Fix (E64): `--equalize-demos` pads the shorter demo block with
neutral filler**, collapsing the position gap to **1.1 tokens** → `advbench_doublespeak_v2_lenmatched.json`.
**On v2, Gate 1 PASSES cleanly: holdout AUC 0.9995 with every control at chance** (position 0.531, length
0.529, token-identity 0.500, label-shuffle 0.494, random-direction 0.472). **So the decodability result now has
confound-free external validity, and the ClearHarm probe's own controls (0.578 / 0.587) are retrospectively
vindicated as the thing that should always have been checked.** *(This is the fourth instance in the programme
of a control catching us rather than a reviewer.)*

**31.3 The prediction dissociation replicates on the clean corpus. [V]** Re-extracting on v2 and generating
base outcomes on both splits (runs 758955 / 758963 / 758964), a probe fit on train and read once on the n=88
test holdout: **Bombness AUC 0.489, Refusalness AUC 0.862.** *(Artifact nit: `PHASE10_V2_DUALSTATE.json` stores
the **oriented** value 0.5106; 0.489 is its directional complement. Both mean "chance" — the same
oriented-vs-directional slip flagged for the generated cohort in §29.6.)* **Bombness neither predicts (§31.3)
nor causally controls (§31.1) behaviour on the second corpus, while refusal does both.**

**31.4 The v2 behavioural re-confirmation is the tightest version of the result in the programme. [V]** On the
length-matched v2 test split (758963, base ASR 0.159): refusal necessity **ΔASR +0.352, p=0.0**; 2×2 main
effect refusal **+0.335 [0.239, 0.438]**; **2×2 main effect Bombness +0.017 [−0.023, +0.057]**; bomb vs random
**+0.023, p=0.69**. **A clean corpus, a confound-free probe, n=88, and the Bombness CI now straddles zero while
the refusal effect is 20× larger.**

**31.5 Power, measured from the actual discordant rates rather than assumed. [V]** Paired-McNemar power at
n=88, from the observed b/c: the **refusal** arm has p_disc **0.364** → minimum detectable ΔASR **0.186**, so
the +0.295 effect is comfortably powered; the **Bombness** arm has p_disc **0.057** (only 5 of 88 pairs move at
all) → **the null is a tight bound by construction.** For a ΔASR = 0.10 effect at 80 % power **~n=305 is still
required** — so even the doubled corpus cannot resolve a 0.10 effect, and **the Bombness null remains a bound,
never "exactly zero."** *This is the honest version of what a second corpus buys: it made the **lever**
significant; it did not make the **null** exact.*

**31.6 What is still open on Phase 10.** The report says "nothing material remains", and for its own plan
§14 that is right. Three things nonetheless remain true and belong in the paper's limitations: (a) **the
behavioural v1 arms were run before the confound was found** — they are confound-*robust* (they use
interventions and the refusal lever, not the probe) and v2 reproduces them, but the v1/v2 distinction must be
stated, not smoothed; (b) **pooling ClearHarm + AdvBench is still not leakage-clean** (15 concept and 13 of 20
codeword straddles survive the rebuild), so the ≈308-item pooled analysis needs a **joint re-split**, not a
decision — Phase 10 reached its power by *replication*, not by pooling; (c) **AdvBench direction validation
was initially estimated as a short job and corrected to "not a short job"** (`ab2abf59`), and the AdvBench
runs use the ClearHarm-fit refusal axis — the same cross-distribution transfer (B17) already disclosed
everywhere else in this log.

## 31b. Phase 9, closed as a decision record; and the sub-sprint's capstone [c4]

- **`reports/PHASE9_ATTACK_OBJECTIVE_DECISION.md` now exists** — Phase 9 (build a mechanism-derived attack
  objective) is documented as a **by-design negative, not an omission**. The plan's §13 is explicitly
  conditional (*"IF a new causal state emerges"*), and the premise is falsified six ways over: necessity,
  sufficiency, the 2×2, per-example patching, three model families, and now the second corpus. Its own
  argument for not spending the GPU-hours is the sharpest one-line statement of the sprint: running it *"would
  be optimizing the **weaker** (epiphenomenal) of the two axes, under the **harder** (input-space,
  scope-limited) medium — a CI-backed negative before a single GPU-hour is spent."* **The §29.9 caveat still
  stands: "Bombness is not attackable" remains untested; "not worth attacking" is what is established.**
- **A capstone figure** (`figures/roleprobe_causal_summary.png`, `scripts/make_roleprobe_causal_figure.py`)
  puts Bombness-vs-refusal across every condition on one panel — the natural Figure 1 for the role-probe
  contribution.
- **An independent `ultracode` verification pass (E64) re-derived every headline from raw and found
  0 code bugs** — P5 +0.048, P10 refusal +0.295 / bomb +0.057, D3 +0.809/+0.452/+0.024 all reproduce — plus
  5 documentation nits, all fixed (the b/c convention, a missing refusal-power JSON, the P5a bound stated as
  ≤0.011, a stale synthesis next-step, a duplicated bullet). **The role-probe plan is marked substantively
  COMPLETE** (`83b39ab5`).

---

# PART H — cross-cutting: corrections, verification gaps, backlog, bottom line

*(Section numbers 21–25 are retained from revision 2 for citation stability; Parts I and J above use 26–31.)*

## 21. The honesty ledger (claims we changed about our own work)

The machine-regenerated `reports/CLAIM_AUDIT_TABLE.md` tracks the Aug 2–9 tally (**95 claims: 77 VERIFIED, 8
WITHDRAWN, 4 SUPERSEDED, 6 UNDERPOWERED, 0 CHECK-FAIL, 173 numeric checks / 0 failures**). Across the whole sprint
the load-bearing corrections were:

1. **[W] P8.0 sub-additive interaction (p=0.045)** → saturation artifact; null at the decisive dose (§8.5). *The
   pre-registered held-out split is what caught it — train sub-additivity reversed to test additivity.*
2. **[W] "5-fold CV AUC 0.887±0.106"** → non-reproducing recompute 0.869±0.055.
3. **[W] "carry heads behaviorally inert" (binary)** → "undetermined" after the specificity control failed.
4. **[W] §10 "informative-null MDE ≤0.09"** → epiphenomenality re-grounded on **specificity** (random +0.161 >
   concept +0.046), not equivalence.
5. **[W] Gate-E clause-(ii) single-seed POSITIVE** → retracted when seed 43 reversed it (the Asymmetry sprint's
   main judgment error).
6. **[W] Q5 seed-42 "mechanism non-specific at the mechanism level"** → withdrawn; seeds 43/44 reverse it.
7. **Covariance control 6.74× → 4.71×** (rank-1 degeneracy fixed).
8. Numerous scope tightenings (L8–L11→L8–L10; "monotone readout"→terminal L31 spike; "3/4"→"2/4"; DS "triples"→
   "~2–3× on clearharm train, no effect on the small v3 test split"). **Direction of every finding preserved.**
9. **[c2] The GCG candidate-selection bug (P9.0)** — the mechanism objective entered the gradient but not
   candidate selection, so *every* pre-fix "mechanism-derived GCG is net-negative" statement was made with the
   objective effectively off. Fixed in `84bf7a1e`/`76acb44a`; nothing before it is citable (§8.7).
10. **[c2] The λ task-loss endpoint statistic** — summarised from a single endpoint, and in one comparison as a
   *ratio of two endpoints*, which swung **1.45×–34× across seeds** and was **withdrawn**. The standing rule
   (`RESEARCH_HANDOFF_V2.md` trap 7) is best-so-far only. Commits `f91acf6b`, `1b5b4d94`.
11. **[c2] Corrections made by the 08-14 re-audit** (`RESEARCH_LOG_AUDIT_2026-08-14.md`), all of them defects
   *in this document* rather than in the underlying work: Gate-B r **0.817→0.8395 and +0.140→−0.0015/−0.3242**
   (a sign error that erased the sprint's sharp H2′ claim); quant deltas **+0.26/+0.29/+0.52 → +0.286/+0.262/
   +0.571** (bf16↔8-bit swapped); P8 α=0.20 **+0.194/p<1e-12 → +0.1417/p=1.2e-04** (wrong run); Gate F
   **POSITIVE → PARTIAL** (the artifact's own verdict); §5.8 train AUC **0.867→0.863** (pooled column
   mislabelled); P10 power **275 for 0.07 → 275 for 0.09, 419 for 0.07**; and the withdrawal of a false
   "`clearharm_179.csv` missing" caveat.

**[c3] Corrections made in the 08-14 → 08-15 window (Parts I and J).** Twelve more, and one of them is the
first in the whole programme that runs *against* our own prior conclusion:

12. **[W] The §20.7 seed-42 "NULL" (Δ −0.0723, p=0.2515)** → the pre-registered 3-seed pooled read gives
    **Δ −0.1303, p=0.0023 — a real gain.** *The single-seed read was underpowered, not right.* **This is the
    fourth single-seed misread of the sprint and the first whose correction is unfavourable to us** (§26.3).
13. **[W] "Per-prompt suffixes transfer" (off-diagonal 0.173–0.200 ≥ universal 0.162)** → withdrawn against
    §20.5's random-token floor (0.2351): **every transferred cell sits at or below un-optimised random
    tokens** (§26.2). "Compute dominates direction" is *refined*, not withdrawn.
14. **§20.5's headline "+0.084 at k=2"** → **+0.035**; ~58 % of it is max-statistic inflation the floor
    reproduces for free.
15. **§20.1's "78 % cost"** → re-scoped, not withdrawn: it is the price of a **near-total pin** on a sharply
    convex curve (76.5 % of the coordinate's movement costs 19.5 %).
16. **§20.7's bounds 0.2151 / 0.1618** → **0.2145 (22.7 %) / 0.1637 (17.3 %)**, now artifact-backed, **plus a
    third contrast the original omitted (0.2284 = 24.1 %, the largest)**. *A headline number survived multiple
    audits before anyone checked it had a file.*
17. **[W] Part F/§17's "activation > continuous > discrete" ladder** → **largely a SCOPE ordering**; the
    scope-matched activation arm retains 0–3 % (§30). The token-space measurements are untouched.
18. **[W] A D3 "finding" published off a 4-prompt smoke run** → withdrawn entirely (`fb442d0c`); its sharpest
    sub-claim reversed at full n (§30).
19. **[W] D3's "independent replication by a concurrent session"** → not supported: one launch lineage, one
    set of GPU results; what was independent was the *analysis* (§30).
20. **[W] "Refusal-lever is Llama-specific"** → superseded ~1.5 h later once Qwen supplied a second positive;
    **carried as post-hoc, with an unresolved Phi refusal-direction confound** (§29.7).
21. **The role-probe Phase-3 "Bombness is at chance"** → the defensible claim is the **paired gap**
    [+0.114, +0.482]; the univariate CI is [0.506, 0.855] at n=42 (§29.1).
22. **§20.8's "AdvBench leakage-0 verified", n=417, test=86** → three corpus revisions later it is **n=399,
    230/81/88**, and **pooling with ClearHarm is *not* leakage-0** (15 concept / 13 codeword straddles) (§31).
23. **[c3] Judge nondeterminism, previously unmeasured at this level:** byte-identical greedy generations
    rescored **3–6/42 differently per arm**, swinging the refusal positive control +0.238 → +0.357 (§29.8).
24. **[c4] [W] Our own AdvBench Gate-1 result was confounded, and we found it.** The v1 build's unmatched demo
    blocks made codeword position and prompt length predict the label (`position_only` 0.785, `length_only`
    0.752 against a holdout AUC of 0.982) — **a Gate-1 FAIL by our own criterion.** Fixed by length-matching
    the demos (v2): position gap −18 → **1.1 tokens**, AUC **0.9995**, all controls at chance. *The trivial
    controls did their job; the corpus builder had not.* (§31.2)
25. **[c4] The AdvBench Bombness 2×2 main effect has a CI excluding zero (+0.046 [0.011, 0.085]) — and is
    still not a Bombness effect**, because it equals the random-direction effect (+0.034, p=0.375) and
    collapses to +0.017 [−0.023, +0.057] on the clean corpus. **Recorded because it is the clearest example in
    the programme of why this project reports specificity rather than significance.**
26. **[c4] "Phase 10 buys the power to fix §20.8" → half true, and the half matters.** It made the *lever*
    significant (p=0.0 vs a bound); it did **not** make the *null* exact — ~n=305 is still required for a
    ΔASR of 0.10, and pooling the two corpora to get there is still blocked on a joint re-split.

**The recurring failure mode, named:** *a single-seed or single-split quantity promoted to a verdict.* It appears
in P8.0, the Gate-E retraction, the Q5 withdrawal, **[c3] the §20.7 seed-42 null, and the 4-prompt D3 smoke.**
Every surviving claim rests on ≥3 seeds or both splits. **[c3] A second named failure mode has now earned its
place: *the half-updated document* — a claim annotated in one place and left contradicted in another (D3 in
`ASYMMETRY_FINAL_SYNTHESIS.md`; five stale phase rows in the role-probe dashboard; four different registry
row-counts across four governance files; two committed deliverables still saying "not run" about arms that
exist). None of it changed a number; all of it is what a reviewer diffs first.***

## 22. Verification gaps in THIS log (numbers not reproducible from committed JSON)

Stated plainly so an external reader knows exactly what is and isn't machine-backed:

- **Gate-E discrete +0.009** and the **λ=10 probe (+0.622/−0.162/+0.189)** — heldout-ASR run-dirs pruned from
  `outputs/`; backed by three mutually-consistent committed `.md` files but not JSON-reproducible here.
- **Gate-7 first-cut "refusal 0.465 ≈ random 0.464"** — run-dirs absent; **superseded** by the committed 3-seed v3
  matrix (0.297 vs 0.279), which backs the same conclusion.
- **§20.2 partial-r (−0.291 / −0.008 / −0.170)** — no `asym_p202` artifact; report-only.
- **§20.7 loss-unit bounds (0.2151 / 0.1618)** and **§20.1-followup p-values/CIs** — only the ratios/deltas they
  normalize are in the JSON.
- **Continuous soft-prompt seed-42 endpoints 0.757/0.081** — the scoring file was repurposed; the **3-seed
  0.784/0.153/+0.631 synthesis figure IS JSON-confirmed** (`ASYM_P2_DOSEMATCHED/SEED43/SEED44`), so the finding
  stands.
- **[c2] THE LARGEST GAP, previously undisclosed: all 20 per-seed run directories of the Gate-7 v3 matrix
  (§13) are absent from `outputs/`** (globbed 20/20 missing; `outputs/stage_gcg_full/` now holds only
  refusal-direction files). The sprint's headline attack-objective negative is backed by
  `GATE7_V3_MATRIX_STATS.json` — which reproduces every printed number exactly — but is **not raw-reproducible**.
- **[c2] `configs/manifests/phase9b_gcg_v3.json`** (cited in §25) **does not exist**; `configs/manifests/`
  holds 8 files and none is a v3 GCG manifest. Consequence: §13's `batch 32` is unverifiable and the one
  surviving GCG manifest says `batch_size 64`.
- **[c2] §5.9's token-0 AUCs (0.936 / 1.000)** — the run-dir summary stores no AUC field.
- **[c2] §5.8's per-split AUCs, §3's 4,909-value and 113→205 test counts** — prose-only, no machine artifact.
- **[c2] `EXPERIMENT_REGISTRY.csv` (last updated 08-05) and `BUG_AND_DEVIATION_LOG.md` (08-08) stopped being
  maintained mid-sprint** — the registry holds 395 rows against 605 output dirs and matches `asym` once
  against 65 such dirs, so **the entire Asymmetry sprint (Part F) and Section 20 (Part G) are unregistered and
  their deviations unlogged**, in a document that advertises provenance discipline. Relatedly the sprint's one
  formally logged pre-registration deviation — the Gate-7 (§14–18) decisive refusal arm having run at an
  **un-validated L22 vector on the leaky v1 GCG split**, resolved by running both directions — is recorded
  only in the bug log, though §11/§22 quote that run's numbers.
- **[c2] ~~`clearharm_179.csv` not in this checkout~~ — WITHDRAWN.** The file exists at the repo root
  (`data/clearharm/clearharm_179.csv`, 179 rows); the earlier search was scoped to `doublespeak_causality/`.
  The corpus-ceiling arithmetic in §20.8 is artifact-backed.

Everything else in Parts A–G that carries a **[V]** was reproduced from an opened output file (7/7 → in practice
6/7 of the whole-sprint load-bearing headline numbers PASS direct JSON re-verification; the 7th, Gate-7 first-cut,
is superseded by a committed replacement).

**[c3] Gaps CLOSED in this revision:** the **§20.7 loss-unit bounds** are no longer report-only
(`asym_p207_arm_bounds.json`, bitwise-reproducible); the **§20.7 interim reads** all survive in git even
though the file was overwritten on disk (`ea821e4d` holds the n=14 read at −0.0792, `143f9534` the n=18);
the **entire Asymmetry sprint is now registered** (§20.7's 111 vanilla-600 runs excepted — see below).

**[c3] Gaps OPENED or newly disclosed in this revision:**
- **The role-probe evidence base is outside version control.** All **27** probe / Phase-4 / Phase-5 / D3 run
  directories are untracked, and **the 2×2 factorial run — the sub-sprint's headline causal result — has no
  `RUNMETA.json` on disk at all.** `.gitignore` explicitly un-ignores `RUNMETA/DONE/summary.json` for exactly
  this purpose, so these are files that were *meant* to be committed. Registry rows for the Phase-4/5 runs
  read `INCOMPLETE … no git commit recoverable` — though the commits **are** recoverable from
  `logs/phase4_bomb_*.out`. *(The raw generations are ignored by design under the responsible-handling
  policy; the miss is the provenance files.)*
- **No `phase5_analysis.json` exists** for runs 758162/758163 — `PHASE5_BEHAVIORAL.md`'s entire result table
  is prose. It was reproduced from `raw.jsonl` for this log, but no committed analyzer produces it.
- **The Phase-4 sufficiency dose (0.25) has no machine provenance** — `DONE.json` records only `alpha: 1.0`;
  the dose survives in a commit message and an execution-log entry.
- **Phi/Qwen Phase-3 AUCs (0.525 / 0.575 / 0.82) have no artifact** and cannot be recomputed: the Phase-4
  `raw.jsonl` carries no `refusal_proj` column despite the script docstring promising one.
- **[c4] The dual-state CI situation is now split, and the split must be stated:** the **AdvBench v2**
  prediction numbers (§31.3) were produced *after* the orientation fix, but the **ClearHarm** ones (§29.1)
  were not and have never been recomputed. Quote them as coming from two different estimator versions.
- **The dual-state bootstrap CIs are pre-fix and unrecomputed** (biased `max(a,1−a)` per resample; the fix
  postdates both JSONs) — conservative for the headline gap, but stale as published.
- **The project-level compute block is still unregistered and it grew: 807 directories** (797 per-prompt GCG
  + 10 randtok-floor, ~900 GPU-h) have **zero** registry rows, because `update_registry.py` hardcodes the
  `doublespeak_causality/outputs` prefix. Declared a scope decision for the registry's owner.
- **`reports/CLAIM_AUDIT_TABLE.md` (machine-generated) has not been regenerated since 2026-08-09** and covers
  none of Parts I or J; the new hand-maintained `ROLE_PROBE_CLAIM_AUDIT_TABLE.md` (**36 rows: 33 VERIFIED, 1
  INCONCLUSIVE, 1 floor/boundary, 1 cohort-specific**) is not reconciled with it.
- **~11 defects found in this window were never entered in `BUG_AND_DEVIATION_LOG.md`** (7 from the two
  adversarial code sweeps + 4 corpus-integrity defects found by executing) — *a recurrence of exactly the
  lapse that B18 was written one day earlier to record.* The **4 findings each sweep rejected are recorded
  nowhere at all**; only the counts survive. `B11` still reads "D3 scope-matched arm NOT RUN — OPEN".
- **The confirmatory-holdout decision (Q2) is formally OPEN in a FROZEN manifest** — the manifest says
  "DECISION PENDING… resolve before any Gate-1 confirmatory claim", the log says "will proceed under (a)
  unless told otherwise", and **Gate 1's headline 0.997 was read on exactly that split**, with no deviation
  entry. Not a leakage claim (the split is codeword- and concept-disjoint and probe-unexposed) — a
  **pre-registration gap of the same class as §20.0**.
- **The 4-prompt D3 smoke (758209) is registered COMPLETE with nothing recording `n_eval=4`**, the precise
  registry gap that enabled the `fb442d0c` error.
- **Two empty output dirs (757942, 751402) and one run with no recoverable commit stamp (757711)** remain on
  disk as traps for anyone counting results; **three SLURM "ghost" jobs** (740944, 741053/4) have shown
  RUNNING in `sacct` since 2026-08-10 and are the only surviving trace of the Gate-7 v3 runs whose
  directories are gone (B14).
- **Two plan-named deliverables do not exist** (`reports/PROBE_COMPONENT_PATCHING.md`,
  `reports/D3_SCOPE_MATCHED_CONTROL.md`); the work lives under other filenames, against the plan's own
  no-aliases rule.

## 23. What is NOT done (the blunt backlog)

> **[c3] READ THIS BEFORE THE LIST BELOW — it is revision 2's backlog, and five of its items have since
> closed.** **CLOSED:** (1) **D3**, the scope-matched activation arm — ran, and the ladder is largely scope
> (§30); (2) the **§20.1 μ sweep** — ran, trade-off sharply convex (§26.1); (3) **§20.5** — ran and is
> non-provisional, with a random-token floor that cut its own headline 60 % (§26.2); (4) **§20.7's owed
> compute** — all three seeds at 37/37, read under a pre-registered rule, **2000-step point formally
> DESCOPED rather than deferred** (§26.3); (5) **behavioural sufficiency of the concept channel** — now
> tested twice more and NULL both times (Phase-4 injection and Phase-5 per-example addition, §29).
> **STILL OPEN exactly as written:** cross-family *circuit anatomy*; **B16, the Phi concept-ablation arm with
> a count-matched random control** — *the deliverable occupying its plan slot says so in its own words, and
> Part J's Bombness replication is a different construct that does not discharge it*; **Gate D's confirmatory
> dev dose** (blocked behind §20.0's unwritten dev decision); **§20.6 / §20.9**; the **§20.8 power fix** (see
> the new items below); the **entire attack-objective completeness list** — MAC/TROPT, a true 2nd-order
> Jacobian loss, quantized attack-objective arms, Phi objective-transfer GCG, DeepSeek-R1 — **untouched in
> this window**; and **no defense**.
>
> **[c3] NEW owed items from Parts I and J**, in rough value order:
> 1. ~~**Finish Phase 10.**~~ **[c4] DONE (§31)** — Gate 1 clean on v2, behavioural on v1 *and* v2, 2×2,
>    power from observed discordant rates, and the dual-probe replication are all complete, and
>    `PHASE10_POWER_ADVBENCH{,_REFUSAL}.json` supersede the stale `corpus_n=40` file. **What remains from this
>    item:** a **joint ClearHarm+AdvBench re-split** (pooling as-is still carries 15 concept / 13 codeword
>    straddles, so the ≈308-item pooled analysis is not executable), and **AdvBench-native direction
>    validation** — corrected from "~15 min" to *not a short job* (`ab2abf59`), so every AdvBench arm still
>    rides the ClearHarm-fit refusal axis (B17).
> 2. **Resolve the Phi refusal-direction confound** — rerun Phi Phase 4 with the repo-selected **L14**
>    direction (the run used L16, which the repo's own artifact rejects) before "floor, not mechanism" can
>    stand; and **test the floor hypothesis** with a high-baseline-refusal Phi arm. Add a **bf16 Qwen** arm.
> 3. **Carry D3 to the ASR endpoint** (it is measured on keyword refusal rate) and build the **genuinely
>    budget-matched** arm — multi-position, or all-layer at suffix positions. The cross-medium Figure A on the
>    **dev** split is the deliverable, and it is blocked behind §20.0.
> 4. **Re-condition the generated-cohort Phase 4** (narrower band / lower dose) — the existing run failed its
>    manipulation check, so the causal story is single-cohort.
> 5. **Dose / band / seed sweeps for Phase 4** and an **on-manifold per-example Phase 5**; a **2×2 on a second
>    family**. Persist bootstrap CIs and a `phase5_analysis.json`.
> 6. **Characterise the StrongREJECT judge's nondeterminism** (no seed or temperature is recorded anywhere);
>    every n=42 contrast in Part J inherits a ~±0.05 floor that no report states.
> 7. **Governance:** commit the 27 untracked run dirs' provenance files and reconstruct the 2×2's RUNMETA;
>    fix `update_registry.py`'s hardcoded prefix and index the 807 project-level dirs; annotate `n_eval` so a
>    4-prompt smoke cannot read as a full arm; enter the ~11 unlogged defects and close B11; regenerate
>    `CLAIM_AUDIT_TABLE.md` and reconcile the two claim tables; **write the §20.0 dev decision** and **ratify
>    or log a deviation for Q2**; fix the execution log's 7–18 h clock drift and the role-probe dashboard's
>    five stale phase rows.

- **Cross-family fine-grained circuit:** the retrieve→write→carry→readout map is **Llama-only**; Qwen3 and Phi-4
  confirm the *dissociation*, not the circuit anatomy. H2′'s sharp form (surrogate collapse to *worse-than-null*)
  is Llama-only. **[c2] And on Phi the *concept half* was never tested at all** — no concept-ablation arm with
  a count-matched random control exists, which is what the plan's Gate E requires before the phrase
  "cross-family dissociation" is licensed.
- **[c2] The D3 scope-matched activation arm** — the activation intervention is all-position/all-layer while
  the soft prompt is 16 input positions, so §17's "activation > continuous > discrete" ladder is **not
  budget-matched**. The handoff calls this *"the single cleanest missing control"* and *"the control a
  reviewer will ask for first."* Not run.
- **[c2] Gate D is exploratory** — its dose (0.10) was chosen by reading the sweep on **test**; a confirmatory
  run on the untouched v3 dev split is owed. The 5.7 % rounding-retention figure is projection-only; **no
  generation was ever run with a rounded suffix.**
- **[c2] The §20.1 μ sweep** (μ ∈ {0.1,0.3,1,3,10}) — not run; §20.1's "78 % cost" is the price of a
  near-total pin, not of the coordinate, until it is. **§20.5 / §20.6 / §20.9** never started (§20.6
  corpus-blocked). **§20.7's 2000-step point** deferred, so that curve covers half its planned span.
- **Behavioral sufficiency of the concept circuit** was never positively demonstrated (carry-install is NULL).
- **The behavioural power problem (§20.8):** at n=37 the design has 0.05 power against its own effect size; every
  behavioural null is a ±0.2 ASR bound, not a point null. Only a second corpus fixes this.
- **Attack-objective completeness:** MAC/TROPT arms never run; a true 2nd-order Jacobian loss never implemented;
  quantized attack-objective arms not run; Phi objective-transfer GCG and a DeepSeek-R1 reasoning replication not
  run.
- **No defense** survived (Gate F/G both honest negatives) — the redeeming datum is zero over-refusal on
  unrelated-normal prompts.
- **Owed compute (live as of 2026-08-14, [c2] — the previous "27/74" is stale):** the §20.7 200→600 extension
  has **seed 42 COMPLETE at 37/37 with a NULL result** (Δ −0.0723, p=0.2515); **seed 43** is filling in with
  all four shards launched; **seed 44** has only **shard 0** launched — which the owed-submissions doc flags
  as a **biased subset**, so seed 44 must not be read until its remaining shards land. Six `gcg_perprompt`
  jobs were running at the time of this revision, so these numbers move. Also: the soft-prompt A4 scored-ASR
  file appears overwritten (a live audit gap).

## 24. Bottom line for an external reader

**Solidly established (cross-cohort, locked-test, controlled, recomputed from raw, cross-model where noted):**
1. A complete, **distributed concept circuit** for Doublespeak on Llama-3.1-8B (demo-KV retrieval L8–L10 → L9 MLP
   write → L14–L21 mediated carry heads → L30–31 output), necessity Holm-significant at every stage, carry stage
   partially sufficient; no single head/edge/layer is a bottleneck; **readout ≠ mechanism** (readability peaks L31,
   causality at L9/L14–21).
2. **The concept circuit is behaviorally epiphenomenal by specificity** — ablating it moves ASR +0.046 ns while a
   count-matched random ablation moves +0.161 (~3×); clearharm concept ablation is exactly 0.000. **[c2]** Two
   independent measures agree: the concept channel is also invisible to the *loss geometry* (gradient-norm AUC
   0.583, CI spans 0.5, vs refusal 0.807 — §12), and the `doublespeak_signature` direction is causally inert
   to within 1e-05 while `d_Direct` moves the same readout +0.167→+0.971 (§5.10).
3. **A single orthogonal refusal direction is the behavioral lever** — ablate → ASR +0.43–0.48 (a stronger attack
   than Doublespeak); re-inject → 0.000 with fluent refusals; decision read mid-late (~L22); the two pathways are
   causally decoupled and **add, never synergize**; the refusal projection **predicts** jailbreak (AUC 0.87).
4. **The dissociation generalizes** to Qwen3-14B and Phi-4-mini, and survives 8-/4-bit quantization and an
   independent from-scratch implementation.
5. **The mechanism is causal, reachable, and continuously steerable, but not discretely optimizable** — continuous
   soft-prompt ASR 0.784 vs 0.153; discrete GCG toward the same coordinate +0.009 (sign-unstable, below judge
   noise; survives a 40× λ increase). *The medium, not the mechanism, fails.* **[c2]** And we now know *why*
   in mechanistic terms, not only statistically: what a discrete suffix achieves is **generic depth-graded
   suppression** whose profile is Pearson **0.9965** identical to a random suffix's and deepest at **L24**, not
   at the optimized L18 (§17 cause 3) — the suffix is not missing the coordinate, it is hitting a generic
   direction that contains it.
6. **Every behavioural negative is now an honest bound** (~±0.2 ASR at n=37); the objective-space direction-term
   null is powered (**[c3] ≤24 % of the compute effect** once the omitted third contrast is included, on a
   p=1.1e-07-sensitive endpoint) and must be reported separately from the behavioural claim.
7. **[c3] The dissociation reproduces from scratch on an independent construct, an imported method, and five
   independent designs.** A contextual-identity ("Bombness") probe built on the role-confusion methodology is
   **decodable at AUC 0.997 with a token-identity control of exactly 0.500**, **orthogonal to refusal at the
   codeword (cos 0.09)**, **replicates on three architectures** — and is **neither necessary (−0.048), nor
   sufficient (+0.048), nor gated (2×2 interaction +0.000 [−0.143, +0.143])**, including under **per-example
   component surgery at ±18.7 readout units**, while refusal ablation moves ASR **+0.238 / +0.357** in the
   same runs. The sharpest form is the under-reported `full` arm: **substituting the *entire* codeword-position
   state from Doublespeak to benign across L8–18 is behaviourally inert.** *Being placed in the adversarial
   latent identity is not the security failure; a separable refusal-suppressed control state is.*
   **[c4] And it replicates on a second, independent harmful corpus at ~2× power** — AdvBench n=88: refusal
   **+0.295 (p=0.0)**, Bombness **+0.057 n.s. and equal to random**, no interaction, Refusalness predicting at
   **AUC 0.862** against Bombness at **0.489**, on a length-matched corpus where the probe's own
   position/length controls sit at chance (Gate 1 AUC 0.9995).
8. **[c3] The "activation medium is privileged" reading is retired.** Scope-matched to a token attack, the same
   refusal ablation retains **0–3 %** of its effect. The programme's central asymmetry is now stated as: *a
   coordinate that is causal **at scale** in activation space, reachable and continuously steerable from the
   input, is neither reachable by discrete tokens nor potent at the scope a token attack actually has.*

**NOT established:** the fine-grained circuit in any non-Llama family; a usable attack objective from the mechanism
(the token-space negative is now definitive and mechanistically explained, not merely observed); a behaviorally
sufficient concept intervention; any working defense; and behavioural effects at the ±0.2-ASR resolution the n=37
corpus forbids. **[c2] Add four more:** the concept half of the dissociation **on Phi-4** (never run); the claim
that the causal locus is **general across concepts** (the multiconcept artifact's own verdict is PARTIAL — 1 of
5 pairs had concept-half headroom); the **budget-matched** version of the activation > continuous > discrete
ladder (D3 never run); and a **confirmatory** continuous dose (Gate D's optimum was read on test).
**[c4] The second-corpus item is now CLOSED as a replication** (§31): Story A holds on AdvBench at n=88 with
the refusal lever at p=0.0 and Bombness indistinguishable from random, and the prediction dissociation
replicates on a confound-free probe. **What that does *not* close** is the power problem itself — resolving a
ΔASR of 0.10 still needs ~n=305, and reaching it by pooling needs a joint re-split.
**[c3] Of those four, one is now RUN and one is now SHARPER:** D3 ran and **confirmed the scope confound**
(§30) — so the ladder is no longer merely unqualified, it is *qualified against us*; and "the concept half on
Phi-4" is still not run, because Part J's cross-family Bombness arm is a **different construct** and the
report occupying B16's slot says so explicitly. **[c3] Add three more NOT-established items** — **[c4] of which the first is now ESTABLISHED**: ~~any
behavioural measurement on the second corpus~~ → **Phase 10 is complete and replicates Story A at ~2× power
(§31)**; a **budget-matched cross-medium comparison** (the arm D3 motivates has not even been proposed); and
**"Bombness is not attackable"** — Phase 9 was *closed by rule as a documented by-design negative*, not
tested, so what is established is only *not worth attacking*. **[c4] Add two:** a **pooled** (as opposed to
replicated) behavioural analysis at n≈308, which needs a joint re-split; and an **AdvBench-native refusal
direction** — every AdvBench arm currently rides the ClearHarm-fit axis.

**One-line takeaway [c3].** *Doublespeak is an imperfect in-context refusal-suppression technique; the elaborate
token→concept remap — whether measured as a concept circuit, as a `doublespeak_signature` direction, or as a
decodable contextual identity that a role-confusion probe reads at AUC 0.997 — is a causally-decoupled,
behaviorally epiphenomenal bystander, and it is neither necessary, nor sufficient, nor gated by refusal on any
of three model families. The refusal direction is the genuine causal handle: you can intervene on it and steer
it continuously — but it does not become a discrete token attack, it did not become a defense, and its
apparent advantage over token attacks is mostly the **scope** an activation hook is allowed, not the medium it
works in. Defend the refusal axis, not the concept subspace; and treat every n≈37–42 behavioural number as a
±0.14–0.2-ASR bound sitting on a ±0.05 judge-noise floor.*

---

## 25. Artifact & figure index

**Consolidated summaries (chronological):** `SPRINT_2026-08-02_TO_08-05_FULL_SUMMARY.md` →
`SPRINT_SINCE_2026-08-02_COMPREHENSIVE.md` (→08-06) → `SPRINT_SUMMARY_2026-08-02_TO_08-09.md` →
`CONTINUATION_MASTER_PLAN_V2.md` + `MASTER_STATUS_V2.md` (28 §) → `docs/ASYMMETRY_FINAL_SYNTHESIS.md` →
`docs/SECTION20_RESULTS.md` → **[c3]** `docs/ROLE_CONFUSION_DOUBLESPEAK_CAUSAL_SYNTHESIS.md` →
`RESEARCH_LOG_SPRINT_2026-08-02_TO_08-14.md` (revision 2, → commit `1e364973`) → **this file** (unifies all of
the above).

**[c3] Part I — Section 20 closed (asymmetry).** `docs/SECTION20_RESULTS.md`, `docs/OWED_SUBMISSIONS.md`
(⚠ its closing table is itself stale on the AdvBench sizes — see §31);
`outputs/asym_p201_ce_musweep.json` + `asym_p201_ce_scores.json` (μ sweep);
`outputs/asym_p205_bestofk_existing.json` + the floor's raw rows under the **project-level**
`outputs/stage_gcg_randtok_floor/asym_p205_randtok_floor_pool{0..9}/FREE_GENERATION_RESULTS.jsonl`;
`outputs/asym_p207_curve_{5to200,200to600}_3seed.json`, `asym_p207_arm_bounds.json`,
`asym_p207_arm_contrasts.json`; `scripts/asym_p205_{bestofk_existing,make_randtok_floor}.py`,
`scripts/asym_p207_arm_bounds.py`. ⚠ Three superseded interim `asym_p207_objective_curve*.json` files
(n=18 / 22 / 11) sit in `outputs/` with no superseded marker, and the nine per-arm curve JSONs all carry a
stale `interim: true` despite being at n=37.

**[c3] Part J — the role-probe sub-sprint.** Plan + logs: `docs/ROLE_PROBE_NEXT_SPRINT_PLAN.md`,
`docs/ROLE_PROBE_NEXT_SPRINT_EXECUTION_LOG.md` (⚠ 35 of its 59 entries sit *below* the "OPEN QUESTIONS"
header, and its §1 dashboard is stale on five phases), `docs/ROLE_CONFUSION_DOUBLESPEAK_CAUSAL_SYNTHESIS.md`.
Reports: `reports/{BOMBNESS_PROBE_VALIDATION,BOMBNESS_CAUSAL_INTERVENTION,BOMBNESS_REFUSAL_FACTORIAL,
DUAL_STATE_PREDICTION,PHASE5_BEHAVIORAL,PHASE5_DECOMPOSITION,D3_SCOPE_COMPARISON,PHI_CONCEPT_COMPLETION,
ROLE_PROBE_CLAIM_AUDIT_TABLE,ROLE_PROBE_FINAL_AUDIT_2026_08_14,GOVERNANCE_REPAIR_2026_08_14,
THRESHOLD_SENSITIVITY_2026_08_14}.md` + `reports/D3_SCOPE_COMPARISON.json`, `reports/PHASE10_POWER.json`.
Code: `src/probes/{contextual_identity_probe,gate1_eval,dual_state_predict,probe_dataset,
activation_extraction,analyze_phase4,phase5_decompose,phase5_patch_spec,build_phase5_perexample,
build_intervention_directions}.py`; `scripts/{phase4_bombness_intervention,phase5_component_patch,
analyze_d3_scope,build_advbench_doublespeak,phase10_power_analysis,threshold_sensitivity}.py`;
`pair_common.SinglePositionProjectOut`; 10 new test files. Runs (⚠ **all 27 untracked**): probe
`757886` (Llama) / `757957` (generated) / `758022` (Phi) / `758030` (Qwen) / `758099` (norm-space);
Phase 4 `757931` (necessity) / `757943` (2×2) / `757992` (sufficiency) / `757967` (generated, INCONCLUSIVE) /
`758057` (Phi) / `758075` (Qwen); Phase 5 `758162` / `758163`; D3 `758290` / `758291` / `758292`
(+ the 4-prompt smoke `758209`, registered without an `n_eval` marker). Data: **`data/splits/
advbench_doublespeak_v1.json` (n=399, train 230 / dev 81 / test 88 — third revision)**; third-party
snapshot `third_party/prompt_injection_role_confusion/` (commit `ec333c40`, MIT) + `SOURCE_INFO_LOCAL.md`.
Manifest: `configs/manifests/role_probe_sprint_v1.json` (**FROZEN, with `confirmatory_holdout_OPEN` still
DECISION PENDING**).

**[c4] Part J / Phase 10 additions.** `reports/PHASE10_REPLICATION.md` (the deliverable),
`reports/PHASE10_PHASE4.json` (v1 behavioural + 2×2), `reports/PHASE10_V2_PHASE4.json` (clean-corpus
re-confirmation), `reports/PHASE10_V2_DUALSTATE.json` (prediction), `reports/PHASE10_POWER_ADVBENCH.json` +
`_REFUSAL.json` (power from observed discordant rates — these supersede `PHASE10_POWER.json`, which is still
computed at `corpus_n=40`), `reports/PHASE9_ATTACK_OBJECTIVE_DECISION.md` (the by-design negative),
`figures/roleprobe_causal_summary.png` + `scripts/make_roleprobe_causal_figure.py` (capstone figure), and
**`data/splits/advbench_doublespeak_v2_lenmatched.json`** — the length-matched corpus that fixes the
position/length confound; **v1 is preserved for run provenance, so always state which corpus a number comes
from.** Runs: extraction `758606` (v1) / `758955` (v2); Phase 4 `758657` (v1) / `758963`, `758964` (v2).

**Claim tables / audits:** `reports/CLAIM_AUDIT_TABLE.md` (machine-regenerated),
`reports/CLAIMS_AUDIT_2026-08-08.md` + `reports/CLAIMS_AUDIT_2026-08-08_wave2.md` **[c2 — both live under
`reports/`]**, `docs/UPDATED_PAPER_CLAIM_TABLE.md`, `docs/PAPER_OUTLINE_V2.md`, and this log's own re-audit
`RESEARCH_LOG_AUDIT_2026-08-14.md`.

**Part-A/B (circuit + behavior):** `reports/PHASE{2_DIRECTIONS,3_RESIDUAL,4_DEMO_RETRIEVAL,4B_PATTERN,5_HEADS,
6_MLP,7_PATH,8_READOUT,9_DOSE}.md`, `reports/PHASE_BEHAV_{CARRY,WRITE,REFUSAL}.md`, `REP_PREDICTS_BEHAVIOR.md`,
`FINAL_CAUSAL_CIRCUIT_REPORT.md`, `REFUSAL_CIRCUIT_SYNTHESIS.md`.
**Continuation-V2:** `reports/P{1,4,5,6,7,8,9,10,11,13,22,24,25,26,27,28,29}*.md`, `GATE7_EXECUTION_PLAN.md`,
`P_GATE7_FIRSTCUT.md`, `P_DEFENSE_UTILITY.md`, `P27_CROSSMODEL.md`.
**Next-Sprint:** `docs/{ATTACK_OBJECTIVE_FULL_MATRIX,THIRD_FAMILY_REPLICATION,QUANTIZATION_EXTENSION,
NEXT_SPRINT_PLAN_2026_08_09,NEXT_SPRINT_EXECUTION_LOG}.md`; `reports/GATE7_V3_MATRIX_STATS.json`,
`GATE7_V3_MECH_VALIDITY_seed42.json`.
**Asymmetry:** `docs/{ASYMMETRY_SPRINT_PLAN_2026_08_11,ASYMMETRY_SPRINT_EXECUTION_LOG,ASYMMETRY_GAP_MATRIX,
TOKEN_REACHABILITY_ANALYSIS,CONTINUOUS_VS_DISCRETE,ADVANCED_OPTIMIZER_RESULTS,MULTICONCEPT_CAUSAL_GENERALIZATION,
TWO_SIGNAL_DEFENSE,PERPROMPT_VS_UNIVERSAL}.md`; `reports/ASYM_P2_DOSEMATCHED.json`, `ASYM_P2_SEED4{3,4}.json`,
`ASYM_P4_MULTICONCEPT.json`; `outputs/asym_p1_reach_*`, `outputs/defense_2signal_…751316`.
**Section 20:** `docs/SECTION20_RESULTS.md`; `outputs/asym_p20{1,3,4,7,8}_*.json`.

**Key data:** `data/splits/clearharm_doublespeak_v1.json` (137), `data/bench/bench_clearharm_v2.json` (116),
`data/behavioral_v3/` (324), **`../data/clearharm/clearharm_179.csv` (179 — the corpus ceiling, at the REPO
ROOT not under `doublespeak_causality/`)**, `outputs/stage_gcg_full/refusal_direction_llama_{L18,SELECTED}.json`
(the L18 axis and its validation). ⚠ **[c2] `configs/manifests/phase9b_gcg_v3.json` does not exist** — the only
committed GCG manifest is `configs/manifests/phase9_gcg_mac_matrix.json`.
**Previously unindexed, added [c2]:** `reports/P6_JACOBIAN_READOUT.md` + `outputs/p6_predicts_behavior_clearharm.json`
(§12); `outputs/asym_p204_equivalence_pass2.json` (§20.4 pass 2);
`outputs/asym_p207_objective_curve_seed42_FINAL37.json` (§20.7 full-n 200→600 null);
`outputs/asym_p203_judge_replicates.json`; `outputs/p8_alpha020_clearharm.json`;
`outputs/asym_p2_soft_refusal_free_b1.0_seed42_…750364/projections.json` (the inverted-U endpoint);
`docs/OWED_SUBMISSIONS.md`.
**Figures:** `figures/{circuit_summary,behavioral_dissociation,refusal_depth_mechanism,causal_decoupling,
refusal_trajectory,rep_predicts_behavior,fig5_dose_response,fig6_attack_objective,fig7_defense_tradeoff,
fig_crossmodel_behavioral}.png`; `figures/asymmetry/{FIG_A_control_hierarchy,FIG_B_reachability_{train,test},
FIG_B2_eps_scan_{train,test},FIG_C_coherence_train,FIG_D_multiconcept,FIG_E_defense_pareto}.png`.

**Verification provenance of this log:** Aug 2–9 numbers inherit the 14-auditor + 7-agent + two 12-agent
adversarial passes and the machine claim table. Aug 9–14 numbers were re-verified for this document by a 4-agent
workflow (`wf_92ba16b8`) that re-opened the committed JSON; results and the flagged verification gaps are in §22.
**Revision 2 (2026-08-14):** a 14-agent completeness + soundness workflow (`wf_9c6abc32`, 690 tool calls) then
re-audited the document itself — six agents asking *what important work is missing* against the plan and status
docs, seven re-opening the JSON behind every headline number, and an adjudicator independently re-checking each
high/medium finding and discarding what it could not confirm. Output: `RESEARCH_LOG_AUDIT_2026-08-14.md`
(17 defects, 15 omissions, 5 staleness items). All are resolved in this revision and marked **[c2]**. **What
that pass did not change: no core conclusion, in either direction.** Every correction was a wrong number
transcribed into this summary, a verdict stated more strongly than its own artifact, a caveat dropped in
compression, or a result that was simply never written down.

**[c3] Verification provenance of revision 3.** The 164 commits `1e364973..aba6b69b` were covered by
`wf_e6bf3b59` (19 agents, 737 tool calls, ~1.7 M tokens): nine readers over disjoint deliverable clusters →
nine adversarial verifiers instructed to *refute* each finding by opening its cited artifact → one
completeness critic that walked the whole commit range and both `outputs/` trees for uncovered work. Of **122
findings: 108 CONFIRMED, 8 CORRECTED, 6 OVERSTATED, 0 unsupported.** Where a verifier corrected a reader, this
document carries the verifier's number — e.g. the §20.5 grid is **1,110 off-diagonal rows, not 1,332**; the
per-prompt tree is **778 dirs, not 555**; the Llama per-layer cosine floor is **0.0062, not 0.049**; the
Phase-5 arm norms are **corpus means at the patched band (remainder ~20.6 vs bomb ~9.4), not one example's at
a wider band**; the D3 report contains **no transposition** (that reader finding was refuted); and the AdvBench
`hack` straddle caveat was **stale** (the fix had landed). The completeness critic then corrected all nine
readers on the same point: **the repo had moved past them.** Two independent audits internal to the work
(`ROLE_PROBE_FINAL_AUDIT_2026_08_14.md` §1/§1b, `GOVERNANCE_REPAIR_2026_08_14.md`) re-derived the Part-J
numbers from raw with fresh code and matched — with one honest caveat this log carries rather than repeats:
that audit's headline *"all load-bearing numbers reproduce exactly… no discrepancy found"* matched against a
3-dp rounding of its own artifact (Phi Gate 1 recompute 0.9858 vs stored **0.9853**), and its own bookkeeping
row ("registry 598 rows") was stale on the day it was written.

**Standing cutoff [c4].** This revision reflects the repo as of commit **`dceab3e8` (2026-08-16 12:31:17)**;
the last substantive commit is **`d25a81db`** (Phase 10 dual-probe complete) and **the queue is empty — no
GPU work is in flight.** Both sprints are at a resting point: the asymmetry thread's §20 is closed except for
two owner decisions (§20.0's dev allocation, and Option 3 for §20.6), and the role-probe plan is marked
substantively **COMPLETE**. **What will move next is therefore a choice, not a job.** Re-read §26, §31 and §23
against `docs/OWED_SUBMISSIONS.md` before quoting either — **noting that that document is stale on the
AdvBench split sizes, and that `PHASE10_POWER.json` is superseded by the two `PHASE10_POWER_ADVBENCH*.json`
files.** ⚠ **When quoting any AdvBench number, state whether it is v1 or the length-matched v2** — both
corpora are on disk and the v1 probe result carries a position/length confound (§31.2).

