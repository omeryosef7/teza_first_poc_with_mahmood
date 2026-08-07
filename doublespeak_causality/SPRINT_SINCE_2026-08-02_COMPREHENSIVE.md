# Doublespeak Causality — Comprehensive Sprint Report (2026-08-02 → 2026-08-06)

**What this document is.** A single self-contained account of *everything* done on the
`behavioral-causality-sprint` branch from **2 August 2026** through **6 August 2026**. It is written so an
external reader (human or LLM) with no other access to the repo can understand the goal, the method, every
headline number, the corrections we made to our own work, and — bluntly — what is still not done. It supersedes
`SPRINT_2026-08-02_TO_08-05_FULL_SUMMARY.md` (which stopped at 08-05) by folding that content in and adding the
08-05→08-06 "continuation / tick" sprint.

**Verification provenance.** Every quantitative claim below was cross-checked against the raw committed output
files (`outputs/*/summary.json`, `raw.jsonl`, `*.npz`) and the harness code that produced them — first by the
14-auditor pass that produced the earlier summary, and again on 2026-08-07 by a 7-agent verification workflow
that re-opened the JSON for each phase and, where a report cited a Holm/Wilcoxon computation, **re-ran the
analysis script in the `poc_stage2` conda env**. Claims are tagged:

- **[V]** VERIFIED — numbers reproduced from an output file or by re-running the analyzer.
- **[R]** REPORT-ONLY — stated in an in-repo report, not independently recomputed in this pass.
- **[W]** WITHDRAWN / SUPERSEDED — a claim we made and then retracted (kept here for honesty).

Where a report and its raw disagree, this document uses the **recomputed-from-raw** value.

---

## 0. The one-paragraph takeaway

We set out to map the complete causal circuit of the **Doublespeak** in-context jailbreak
(arXiv:2512.03771), in which a benign codeword is bound by in-context demonstrations to a harmful concept, so a
request phrased with the codeword elicits harmful output. **We succeeded at mapping the concept circuit — and
then showed that circuit does not cause the jailbreak.** The elaborate token→concept remap
(demo-codeword retrieval L8–L11 + an L9 MLP write → L14–L21 "carry" heads → L30–31 output) is real,
distributed, necessary-and-partially-sufficient *for the internal concept readout* — but ablating it through
harmful generation leaves attack success statistically unchanged. What *is* behaviorally potent is a single,
orthogonal **refusal direction**: ablate it and ASR rises +0.43–0.48 (a stronger attack than Doublespeak);
re-inject it and ASR falls to 0.000 with fluent refusals. **Doublespeak is, mechanistically, an imperfect
in-context refusal-suppression technique; the concept remap is a causally-decoupled, behaviorally
epiphenomenal bystander. Defense implication: monitor/scrub the refusal axis, not the concept subspace.**
Everything is **Llama-3.1-8B-Instruct only.**

The 08-05→08-06 continuation sprint did not overturn this. It (a) hardened the evidence (provenance on 397
run-dirs, a data-integrity validator that recomputes 4,909 summary values from raw with 0 mismatches, test
suite 113→205), (b) **corrected several of our own overstatements** — most importantly it withdrew a "P8.0
sub-additive interaction (p=0.045)" claim as a ceiling artifact and confirmed the interaction is null at the
decisive strong dose, and it downgraded the item-level "behaviorally necessary" reading of the carry heads to
"undetermined" after its specificity control failed — and (c) added new causal tests (all-occurrence patching,
decision-token attention edges, induction-head identification, 32-layer refusal-direction validation) that all
reinforce the "distributed, refusal-is-the-lever" picture. Several capstone phases (Jacobian readout, the
GCG/MAC attack-objective evaluation, cross-model replication, paper assembly) remain **not done** — see §11.

---

## 1. System under study, model, environment

| item | value |
|---|---|
| Model | `meta-llama/Llama-3.1-8B-Instruct`, **bf16**, 32 layers × 32 heads (8 KV heads, GQA), d_model 4096 |
| Hardware | NVIDIA **L40S** primary; later backfilled onto **a5000 / 3090** (killable partition) — see §10 | 
| Stack | torch 2.7.1+cu126, transformers 5.12.1; CPU analysis in conda env `poc_stage2` (numpy 2.4.6, scipy 1.17.1) |
| Attention | default SDPA; **eager forced** wherever attention patterns/edges are hooked (SDPA fuses softmax@V and silently no-ops the hook) |
| Decoding | greedy (`do_sample=False`); `max_new_tokens` 200 (baseline) / 220 (behavioral) / 180 (calibrated inject) / 120 (trajectory) |
| Harm judge | **StrongREJECT** rubric grader; `MALICIOUS` iff score ≥ **0.25**; `ASR` = fraction malicious. Measured judge noise floor ≈ **2 pp** label-flip on byte-identical text |
| Concept readout | **forced-choice `DE_context`**: append a question to the demo block, read `p_concept = P(concept)/(P(concept)+P(codeword))` at the answer position (a *representational* metric, not behavior) |
| Attack source | ClearHarm, revision `79464fb6…`; demos generated with `gpt-4o-mini`, `openai_seed=7`, 12 demonstrations per prompt |

**Two metrics, kept strictly separate throughout:**
- **`p_concept`** (forced-choice) = does the model internally *read* the codeword as the harmful concept? — Part A.
- **ASR** (StrongREJECT on generated text) = does the model actually *emit* harmful content? — Part B.
The entire finding is that these two dissociate.

**The six matched prompt conditions per item:** `doublespeak` (attack), `neutral` (codeword, no demos),
`direct` (plain harmful request), `benign` (codeword bound to benign demos), `shuffled`, `unrelated`.

---

## 2. Data: the locked splits

### 2.1 v1 locked split — `data/splits/clearharm_doublespeak_v1.json` (frozen 08-02) — **[V]**
137 records, two cohorts, split at the intent-cluster level: **clearharm** (primary) 86 = 44 train / 42 test,
43 concepts; **curated** (replication) 51 = 30 train / 21 test, 17 concepts ×3. Integrity recomputed from the
artifact: 0 example / cluster / prompt overlap across train/test in all six conditions; 137/137 concepts and
codewords single-token. ⚠ **The curated test cell is n=21** — one above the ≥20 floor, the direct cause of the
sprint's one acknowledged power failure (Phase 5 curated-heldout = 0 significant heads).

### 2.2 v2 expanded bench — `data/bench/bench_clearharm_v2.json` (08-04) — **[V]**
116 examples = 86 clearharm + 30 new gpt-4o-mini single-token concepts (73 unique), dev 59 / heldout 55–57,
**0 test leak** vs v1. (Caveat: `_meta.n_examples=86` is stale metadata; the 30 new items carry only 4 of 6
conditions.)

### 2.3 v3 split — `data/behavioral_v3/` (built 08-05, continuation P1b) — **[V]**
The dataset the continuation sprint built to fix v1's leakage and reach interaction-power. Verified from the
file's `_meta`: **N=324 examples, 224 single-token concepts, 224 pairwise-disjoint codewords**, cohorts
**clearharm 170 / generated 154**, splits **train 162 / dev 82 / test 80**, **0 straddling** concepts/codewords/
clusters (vs v1's 14 concepts / 17 codewords straddling — v1's per-instruction hashing had made the leakage
check vacuous). Built for **$0.1426** across 496 gpt-4o-mini calls; every demo is model-generated (0
placeholders); 9 ClearHarm rows dropped each with a logged reason. **Important status:** v3 was *built* in this
sprint, but almost all causal/behavioral headline results below still run on **v1/v2** — the v3 downstream
re-runs are future work (§11). The one exception is the P8 interaction factorial (§8.3), which runs on v3.

---

## 3. Statistics & controls (apply to everything)

- **Paired designs throughout.** Per-example matched differences; train(dev) and test(heldout) aggregated
  **separately** (a pooling bug was caught and fixed mid-sprint).
- **Representational significance:** two-sided **Wilcoxon signed-rank**, **Holm**-corrected across the 32-layer
  family or the full 32×32 = 1024-cell head family, per split. *This replaced a sign-flip permutation test whose
  resolution floor (5.0e-5) was coarser than the Holm threshold (4.88e-5) and returned an artifactual p=0 — see
  §9.*
- **Behavioral significance:** **exact McNemar** on paired discordant flips + percentile bootstrap CIs
  (2000–10000 resamples, seeded).
- **Tripwire controls, verified exactly 0.0 in raw:** self-swap, self-check freeze, identity patch, α=0 no-op.
- **Specificity controls:** norm-matched random directions, count-matched random heads/positions, random-edge
  donors, random-head installs.
- **Coherence guard:** `empty_rate` = 0.000 in every behavioral cell; plus `--save-gen` inspection passes.

---

# PART A — the representational concept circuit (08-02 → 08-04)

All readouts here are forced-choice `p_concept`. **Sign convention: a positive effect = the intervention
DROPPED the hijacked reading.** Every number in this part was re-checked against the committed `summary.json`
and, for the head/Holm tables, by re-running `phase5_analyze.py`.

## 4. The circuit, stage by stage

### 4.1 Behavioral baselines / Gate 1 — **[V]**
StrongREJECT malicious rate (greedy, `max_new_tokens=200`): clearharm aggregate **direct 0.116 / neutral 0.256
/ doublespeak 0.349** (n=86); curated **0.255 / 0.039 / 0.235** (n=51). Doublespeak beats direct on clearharm
by **+0.233**. (All six rates recompute exactly from the per-example label field — re-verified in continuation
P1, §7.2.)

### 4.2 Direction geometry — **[V]**
Per-layer directions at `resid_post` / codeword-last, 32 layers, train-only. `mean cos(concept, refusal)` =
**0.012** (clearharm, max |cos| 0.078) / **0.061** (curated, max |cos| 0.153). **Concept ⊥ refusal is real
(|cos| ≤ 0.153 at every layer).** The `doublespeak_signature` (DS−neutral vector) is *closer to refusal*
(cos 0.127/0.151) than the concept direction is — an early hint of the headline.

### 4.3 Residual patching at the query codeword — **NULL [V]**
Logit-lens P(harm) at the query codeword is at the floor for clean Doublespeak; no patch beats the random
control (best necessity drop ≤ +0.015, random-control ≈ equal). Identity control exactly 0.0 for all 137 items.
**The local codeword state carries nothing.**

### 4.4 Demo-codeword K/V retrieval (L8–L10) is NECESSARY, not sufficient — **[V]**
Neutralize the demo-codeword K/V (donor = benign-remap), forced-choice readout. Per-layer specific effect
(random_control − C3), CI excludes 0: **L8** +0.176 (cur) / +0.069 (ch); **L9** +0.220 / +0.082; **L10** +0.213
/ +0.113; **L11** +0.112 (cur ✓) / +0.022 (ch **ns**). ⇒ honest joint statement **L8–L10 on both cohorts**
(the reports say L8–L11; clearharm L11 CI includes 0). Sufficiency ≤ 0 at every window (installing DS demo-K/V
into a benign prompt creates nothing) — the binding is **context-bound** at this stage.

### 4.5 Query→demonstration attention EDGES are NOT necessary — clean negative **[V]**
Surgical edge knockout (eager), all heads L8–11, destination = query codeword + answer position, source = demo
codewords: specific-vs-random-edge effect **+0.0020 [−0.0004, 0.0046] ns** (clearharm), **−0.0026 ns**
(curated). Blocking *all* query edges hurts 13×–49× more (a general-attention effect). ⇒ **retrieval is
distributed/redundant, not a single induction edge.** (This is re-confirmed and sharpened by continuation P3, §7.4.)

### 4.6 The L9 MLP write (the concept-write location) — **[V]**
Patch DS `mlp_out` with matched benign `mlp_out` at the **demonstration** codeword positions. **L9 is the only
layer Holm-significant on all four cells** (values re-extracted from `summary.json`):

| cell | L9 necessity | 95% CI |
|---|---|---|
| curated dev (n=30) | +0.0493 | [0.023, 0.080] |
| curated heldout (n=21) | +0.097 | [0.040, 0.166] |
| clearharm dev (n=44) | +0.0625 | [0.021, 0.113] |
| clearharm heldout (n=41) | +0.0153 | [0.006, 0.029] |
| v2 clearharm dev (n=59) | +0.080 | Holm band L8–L13 |
| v2 clearharm heldout (n=55) | +0.030 | Holm band L9–L13 |

**Sufficiency ≈ 0 at every layer** (max |install − random| ≤ 0.014). **Componential dissociation at the same
token:** `attn_out` at L9 is null on all four cells while K/V and MLP-out are both necessary. Self-swap exactly
0.0 everywhere. ⚠ The query-codeword MLP is **3–4× weaker** than the demo effect on clearharm, **not** an
absolute null (L9/L15/L20 survive Holm on clearharm) — corrected from the report's "inert".

### 4.7 Write granularity — the one place the A–G mandate was met — **[V/R]**
143 windows on v2, self-swap 0.0 across all: single L9 +0.080; sliding-W4 **L8–11 +0.111** > best single layer
⇒ **the write is distributed across L8–11**, one layer is not sufficient. ⚠ The report's "saturates at W8,
wider adds nothing" is **wrong**: best-W8 window L2–9 = +0.192, ~1.7× the best W4 (holds only within the fixed
L8-start family). *(This granularity table is [R] — not re-opened from raw in the 08-07 pass.)*

### 4.8 All-head z-patch necessity — the carry heads (L14–L21) — **[V]**
Patch each (layer, head) answer-position `z` with matched benign; Wilcoxon + Holm over 1024 cells. Re-running
`phase5_analyze.py` on the committed halves reproduced the counts **exactly**:

| cell | n | Holm-sig positive-necessity heads |
|---|---|---|
| curated dev | 30 | **58** |
| curated heldout | 21 | **0** ← low power, *not* a structural null |
| clearharm dev | 44 | **31** |
| clearharm heldout | 41 | **31** (25 heads sig on BOTH clearharm splits) |
| v2 dev | 59 | 58 |
| v2 heldout | 55 | 44 |

Top heads: L17H27, L14H4/H5/H23, L15H8, L18H20, L21H10, L30H15, L31H0/H1. **No single head dominates** (top head
≈ 5% of total necessity). **The curated-heldout 0 is a power failure, not a null** — its per-head raw effects
are the *largest of any cell* (L15H4 +0.106) but cannot clear a 1024-cell Holm threshold at n=21. *(Caveat: the
frequently-quoted v2 "dev 58 / heldout 44" answer-position count could not be reproduced from a committed dir in
the 08-07 pass — the committed v2 phase5 dirs are demo-position (yield 6/7) and the v2 query dirs lack a
`summary.json`; treat that specific pair as [R].)*

### 4.9 Carry heads are causal in their attention PATTERN — **[V]**
Uniform-pattern knockout (v2): joint 7-head KO **+0.166 [0.097, 0.238]** dev / **+0.134 [0.077, 0.199]**
heldout; benign-pattern transplant +0.46; self-swap exactly 0.0. Per-head: **no head individually necessary**
(L14H5 is even negative → others compensate); joint effect strongly superadditive. ⚠ The uniform-KO arm has
**no specificity control** (an arbitrary non-candidate head's pattern already produces most of the drop) — cite
the joint necessity, not "uniform-KO is more specific."

### 4.10 Where the carry heads get the concept — **[V]**
KO of the carry heads' answer→demo-codeword edges: **KO_all** (firing control) +0.246 / +0.207; **KO_demo**
(demo keys only) **+0.007 / +0.003** (~2–3% of KO_all). ⇒ **the carry heads read the concept from the
distributed residual context by the answer position, not from fresh attention to the demo codewords.** (Self-
caught caveat: KO_all also blocks the forced-choice question, so it is a firing control, not a retrieval measure.)

### 4.11 Carry vs proximal, and closing the L9→carry edge — **[V]**
**(a) DIRECT-vs-TOTAL:** `direct_frac` (logit effect surviving downstream freeze) ≈ **0.00** for L14–L21 carry
heads (24 of 32 mid-band cells exactly 0.000) vs **0.47–0.76** for L30H15/L31H0 (readout-proximal). Freeze-
consistency and self-swap = 0.0 across all 1370 head-rows.
**(b) L9-write → carry-band edge is causal (mediation):** neutralize L9, freeze L14–21 carry `z` to clean,
measure restoration — median mediation fraction **0.764 / 0.828 / 0.751 / 1.459** (cur dev / cur held / ch dev /
ch held), random-head control **0.0**. ⚠ Medians over the L9-responsive subset (n=9–13, below the ≥20 mandate);
the headline "75–83%" excludes the fourth cell (1.459, an overshoot at n=9).
**(c) Carry head-set is PARTIALLY SUFFICIENT (first component that is):** install DS carry-`z` into a benign
prompt → specific effect **+0.162 / +0.239 / +0.369 / +0.406** (random-head install does nothing; self-install
0.0). **⇒ progression: context-bound at retrieval/write → transplantable once carried.** *(Sufficiency is
representational only; behavioral sufficiency of the carry heads was never tested — §11.)*
**(d) Sufficiency accumulates GRADUALLY** across L14→L14-21; the largest single increment is adding L17(H27).

### 4.12 Readout ≠ mechanism — **[V]**
Per-layer linear concept projection: **peak = L31 in all four cells**; at the causal write layer L9 the
projection is **≈ 0** (|fraction of max| 0.008–0.163). ⇒ **linear readability peaks at the very last layer while
causality lives at L9/L14–21** — logit-lens localizes readout proximity, not the write. ⚠ The report's "grows
monotonically" is false (11–14 of 31 steps decrease); correct phrasing: *flat/noisy through L0–L30, sharp
terminal spike at L31.*

### 4.13 The write is a GRADED lever — **[V]**
Interpolated donor `(1−α)·DS + α·benign` at the demo-codeword `mlp_out`, α ∈ {0, .25, .5, .75, 1, 1.5, 2}.
Single-L9 `p_concept` α0→1: .811→.762 / .690→.575 / .884→.819 / .879→.862. **Monotone decreasing over α ∈ [0,1]
in 8/8 cells**; α=0 bitwise-identical to the unpatched baseline, α=1 bitwise-identical to the necessity patch.
⚠ Phase 9 has **no inferential statistics** (no CI/p) — the claim rests on the ordering of point-means. ⚠ **Live
disk mismatch (META-03):** the `phase9_dose_curated_L9` summary stores `monotone_decreasing=False` for heldout
(it included the α>1 uptick); the curve over [0,1] *is* monotone — cite the curve, not the stale boolean.

### 4.14 Circuit summary (Part A)
```
demo-codeword K/V retrieval (L8–L10, peak L9–L10)   ──┐  necessary both cohorts, NOT sufficient
L9 demo-codeword MLP write (band L8–L13)            ──┘  Holm-sig 4/4 cells, graded, NOT sufficient
                    │  edge causal: ~75–83% mediation, random control 0%
                    ▼
L14–L21 answer-position CARRY heads
    necessary (distributed; 25 heads sig on both clearharm splits, 58 v2-dev)
    causal in attention PATTERN (+0.13 to +0.17), fully downstream-mediated (direct_frac ≈ 0)
    PARTIALLY SUFFICIENT (+0.16 to +0.47) ← first component with both
    reads from distributed residual context, NOT fresh demo attention
                    ▼
L30–L31 readout-proximal output (direct_frac 0.47–0.76) → logit
```
**Distributed within concentrated bands — no single head, edge, or layer is a bottleneck.**

---

# PART B — the behavioral frontier (the headline, 08-04 → 08-05)

Everything here is StrongREJECT-judged **generation** (real behavior), paired exact McNemar, two cohorts,
locked splits, matched controls, `empty_rate = 0.000`. Fully corroborated against raw outputs in the 08-07 pass.

## 5. The dissociation

### 5.1 BEHAV-CARRY — ablating the carry heads through generation: **NULL [V]**
Zero the 9 carry heads' `z` at every position on every forward pass (prefill + each decode step). ΔASR
**+0.091 / +0.071 / −0.100 / 0.000** (ch train / ch test / cur train / cur test); every CI includes 0; McNemar
p ≥ 0.289. The clearharm trend is ~3–4× the random-head control but not significant.

### 5.2 BEHAV-WRITE — ablating the L8–11 write through generation: **NULL (flatter) [V]**
Zero `mlp_out` at L8–11 at the ~12 demo-codeword positions. All ΔASR ∈ [−0.023, +0.067]; every CI includes 0;
every McNemar p ≥ 0.688. *(Implementation note: the original `ComponentOutSwap` position guard fired during
**prefill only** — continuation P10, §8.4, re-tests this decode-safe.)*

> **⇒ The complete representation ≠ behavior dissociation.** The very components causally necessary (and, for
> the carry heads, sufficient) for the concept **readout** are **not behaviorally necessary** for the jailbreak.

### 5.3 Refusal ablation is a STRONGER attack than Doublespeak — sufficiency **[V]**
Arditi-style directional ablation of the validated L18 refusal direction at every layer/position (α=1.0).
Paired exact McNemar, **refusal-ablation vs direct base**: **+0.432 (p=4.0e-6)** ch-train, **+0.476 (p=2.0e-6)**
ch-test, **+0.433 (p=9.8e-4)** cur-train, **+0.429 (p=3.9e-3)** cur-test. Norm-matched random direction does
**nothing** (p ≥ 0.5). ⇒ **refusal suppression alone is behaviorally sufficient (+0.43 to +0.48), and ≥
Doublespeak on all four splits.** Refusal direction was bidirectionally validated before use (ablate_gain
+0.467, induce_gain +0.667, separation 0.9525 at L18). ⚠ "≥ DS significantly on 3/4 splits" corrected to
**2/4 at α=.05** (4/4 only at α=.10) — the 3/4 came from a preempted run.

### 5.4 Re-injecting refusal kills the jailbreak — necessity **[V]**
Add +α·refusal at every position/timestep at L18 through DS generation. ASR **.386/.381 → .000 at α=12** on
clearharm (McNemar −0.386, p=1.5e-5 / −0.381, p=3.1e-5); curated train → .000 (p=2.0e-3). **Coherence audit
(key confound closed):** empty_rate 0.000 at every α, effect already strong at milder α=8, and inspected
completions are **fluent natural refusals** while the random control at the same α produces coherent *harmful*
text. ⚠ **curated test is p=0.50 (ns)** — only 2/21 malicious at baseline, nothing to flip; the reports' stated
range silently drops it. ⚠ At the matched α=12 a random direction *does* significantly raise ASR — the
specificity claim is about *direction of effect* (only the refusal axis ever lowers ASR).

### 5.5 Doublespeak SUPPRESSES the refusal axis — representational grounding **[V]**
Project the last-prompt-token residual onto the per-layer refusal direction. clearharm-test direct−ds gap:
hs9(~L8) **+0.19 [0.16,0.22]**, hs25 +6.98, **hs32(~L31) +41.21 [33.3,49.4]**. **Gap grows monotonically from
hs9 to hs32 with zero violations in all four cells; suppression onsets at ~hs8 (the L8–11 write band).** ⚠ The
norm-matched random control is <1% of signal in magnitude but its CI excludes 0 at 20–25 of 32 layers.
⇒ **the demonstrations, in the same L8–11 band, do two orthogonal things:** remap codeword→concept (inert) and
suppress the refusal representation (the driver).

### 5.6 The refusal DECISION is read MID-LATE — depth localization **[V]**
The first attempt (fixed α=12) was confounded (α is absolute magnitude; residual norm grows with depth) and was
honestly reported and discarded. The **calibrated-α** version injects each layer's own direction at its measured
direct−ds gap (α = 0.470/1.968/5.106/7.590 at L9/L16/L22/L28); random control null at every layer. ΔASR:
**L9 null in both cohorts**; **L22 −0.250 (p=0.001) ch-train, −0.167 (p=0.039) ch-test, −0.200 (p=0.031)
cur-train** — the one layer significant in both cohorts. ⇒ **suppression starts at L8–11 but the behavioral
refusal decision is read mid-late (~L16–L22); restoring the signal only early is not enough.** ⚠ Defensible
claim = "L22 sig in both cohorts, L9 null everywhere," not the report's "L16/22/28 sig both cohorts" (that
holds only on clearharm-train). **⚠ AT RISK (see §8.1, §11):** this contrast leans on the L9 refusal direction
being *valid*; continuation P7 finds L9 is **not linearly decodable as a refusal axis at all** — which makes
"L9 null" uninformative rather than a real early-vs-late contrast. This is a genuine open thread.

### 5.7 Concept-remap ⊥ refusal-suppression — causally decoupled **[V]**
Ablate the L8–11 write, then measure the refusal-axis projection. The positive control fires in all four cells
(p_concept e.g. .884→.799, CI excludes 0), yet the refusal suppression is **completely unmoved**: at every one
of 128 layer-cells the restoration is within |0.05| of the gap, and where significant it is *negative*. ⚠ "CIs
include 0 throughout" is false — 33 of 128 cells are significant (all negative, ≤5% of gap) — use the fractional
statement. ⇒ **this is why the concept circuit is behaviorally epiphenomenal:** the two L8–11 effects run on
separate pathways.

### 5.8 The refusal projection PREDICTS which prompts jailbreak — item-level link **[V, with corrections]**
Join each DS item's decision-token refusal projection with its ds_base StrongREJECT outcome (no new GPU — a join
of two committed runs). **clearharm: AUC 0.874 at decoder L21 (n=86, 32 malicious), Mann-Whitney p=3.8e-9,
point-biserial r=−0.584**; per split train 0.867 / test 0.891; bootstrap 95% CI [0.797, 0.940]. curated is a
**genuine null** (AUC 0.42) — its refusal suppression is uniform, so the projection cannot discriminate
(concept-dilution, not a contradiction). ⇒ **the items DS jailbreaks are precisely those it most suppresses on
the refusal axis**, identifying two sources of the partial ~0.36 base ASR: under-suppression (clearharm) and
concept-dilution (curated). **⚠ [W] corrections in `REP_PREDICTS_BEHAVIOR.md`:** the "5-fold CV AUC
0.887 ± 0.106" is **withdrawn** (recompute = 0.869 ± 0.055); "L16/L18 beat L21" is **withdrawn** (ΔAUC CI
straddles 0 — the supportable claim is "at least as good as L21"). Also: L21 is family-specific under P7
validation; the report recommends re-anchoring the headline at **L16 (AUC 0.888)** or **L18 (0.882)**, both
P7-validated in both direction families — the result is robust to the choice. *(A lower "Robustness" paragraph
in that report still prints the withdrawn 0.887±0.106 — treat the recompute section as authoritative.)*

### 5.9 Outcome fixed at the DECISION POINT — trajectory **[V]**
Track the refusal projection along generated tokens. Direct-harmful (refuses) token-0 L30 = 13.6; DS→refuses =
9.1; **DS→jailbreak = −2.1 (stays low throughout)**. Zero trajectory crossings; token-0 separation AUC 0.936
(test)/1.000 (train). ⇒ the earlier hypothesis that refusal *re-engages* mid-generation is **falsified** — the
outcome is set at the decision position. curated confirms the second mechanism (ds_refused_rate = 0.000 on both
splits, yet ASR ~0.10 — non-jailbreaks are benign codeword-dilution, not refusals).

### 5.10 Consolidated behavioral verdicts
| # | Claim | Verdict |
|---|---|---|
| 1a | Carry heads behaviorally inert (ΔASR CIs include 0, p ≥ 0.289) | **NULL** |
| 1b | L8–11 write behaviorally inert (p ≥ 0.688) | **NULL** |
| 2 | Refusal ablation **sufficient** (+0.43–0.48 > DS; random null) | **CAUSAL** |
| 3 | Refusal re-injection **necessary** (→0.000; coherence-audited; curated-test ns) | **CAUSAL** |
| 4 | DS **suppresses** the refusal axis (onset hs8, monotone growth) | **CONFIRMED** |
| 5 | Refusal decision read **mid-late (L22)**; L9 null | **CAUSAL** (⚠ L9-direction validity, §8.1) |
| 6 | Concept-remap ⊥ refusal-suppression (frac restored ≤5%) | **INDEPENDENT** |
| 7 | Refusal proj **predicts** jailbreak (AUC 0.874; curated null) | **PREDICTIVE (clearharm)** |
| 8 | Outcome set at **decision point** (0 crossings) | **DECISION-POINT** |

---

# PART C — the continuation "tick" sprint (08-05 → 08-06)

Run under a 30-minute cron loop (`reports/CAUSAL_CONTINUATION_MASTER_PLAN.md`, tracked in
`CONTINUATION_PROGRESS.md`, ticks 1–86). Its job was to **trust-then-extend**: harden provenance, recompute
every number from raw, hunt bugs adversarially, then add the causal tests the plan still demanded. It changed no
Part-A/B headline but **corrected several of our own claims** and added five new results.

## 6. What the continuation sprint hardened (integrity) — **[V]**
- **Provenance (P0):** `ds_common.write_runmeta/write_done` + backfill wrote RUNMETA/DONE across the tree —
  **397/412 dirs carry RUNMETA, 385 carry DONE**; reconstructed records are schema-tagged
  `RUNMETA/1-reconstructed` and never fabricate unsourceable fields (git commit recovered from `logs/*.out` for
  181 dirs; script recovered from the sbatch wrapper for 195). `EXPERIMENT_REGISTRY.csv` 45→395 rows. ⚠ These
  are **post-hoc reconstructions** for the Aug 2–5 runs, not a live at-run-start contract.
- **Data integrity:** `validate_all_outputs.py` recomputed **4,909 summary values from raw across 29 run dirs →
  0 mismatches.** Every ASR/refusal_rate/empty_rate/ΔASR/flip-count/McNemar-p reproduces exactly. Caught 1 hard
  FAIL (a duplicate aborted twin dir with no summary) and 1 §1.5 pooled-reporting violation.
- **Test suite:** **113 → 205 passing** across the sprint (78+ new tests). Two real primitive defects found &
  fixed: an empty-position `index_select` dtype bug in `ComponentCapture`, and an `UnboundLocalError` +
  silent mis-slice in `find_word_occurrences_in_text`.
- **Judge unification:** `scripts/behav_judge.py` now holds the single StrongREJECT contract, differential-
  tested against all 6 copies. Found a paper-relevant defect: `14_behavioral_eval.py` has **no EMPTY label** and
  no `empty_rate` guard (a blank generation is folded into BENIGN/MALICIOUS) — audited in P1 and found to have
  **zero exposure** (§7.2), but fixed as a latent trap.

## 7. Continuation foundations — P1 / P1b / P2

### 7.1 (P1b) v3 split — see §2.3. **[V]**

### 7.2 (P1) Baseline audit — VERDICT SAFE — **[V]**
Recomputed directly from raw: **0 of 411 Phase-2.1 generations are empty/whitespace-only** in either cohort, so
the missing-EMPTY defect never shifted a published number. All 6 malicious rates recompute exactly (clearharm
.1163/.2558/.3488; curated .2549/.0392/.2353). ⚠ **Secondary finding (carry-forward):** truncation is heavy and
cohort-asymmetric — `stop_reason=length` on **25% of clearharm but 72% of curated** at `max_new_tokens=200`.
Common-mode so it doesn't bias DS-vs-direct, but a plausible contributor to curated's "complied-but-benign" gap;
recommend raising max_new_tokens and recording stop_reason going forward.

### 7.3 (P2) All-occurrence patching ~doubles the L9 write necessity — **[V]**
The `--positions all` flag existed in `phase6_mlp_causal.py` and had **never been run** (zero new code). Patching
**all** codeword occurrences (demo + query) vs demo-only raises L9 write necessity by **1.38×–2.27× across six
cells**, specificity-controlled (necessity_specific = random_control − C3, count-matched non-codeword positions):

| cell | demo-only → all | ratio |
|---|---|---|
| clearharm dev (n=44) | +0.0625 → +0.0889 [0.036, 0.157] | 1.42× |
| clearharm heldout (n=41) | +0.0153 → +0.0348 [0.012, 0.067] | 2.27× |
| curated dev (n=30) | +0.0493 → +0.1003 [0.037, 0.184] | 2.03× |
| curated heldout (n=21) | +0.0970 → +0.1797 [0.094, 0.270] | 1.85× |
| v2 dev (n=59) | +0.0798 → +0.1101 [0.060, 0.168] | 1.38× |
| v2 heldout (n=55) | +0.0304 → +0.0649 [0.028, 0.107] | 2.13× |

Sufficiency stays ≤ 0 everywhere; self-swap 0.0. ⚠ The **ratio is an unpaired comparison of two independently-
estimated effects** (no CI on the increment, no per-occurrence resolution) — descriptive, not a paired test.

## 8. Continuation causal tests — P3 / P4 / P7 / P8 / P10

### 8.1 (P7) 32-layer refusal-direction validation — refusal decodable only from L13 — **[V]**
Re-validating all 32 per-layer refusal directions (a real blocker: none carried a `validation` key; only 5 were
ever generation-validated). Under **both** independently-fit direction families (existing + clearharm), ablate +
induce arms: **L9 FAILS both arms in both families (valid=False)**; **L18 validates strongly** (ablate_spec
+0.60/+0.90, induce_spec +1.00/+0.80). Across the 32-layer sweep, the refusal axis **first becomes linearly
decodable at L13** — layers 0–12 fail in both families without exception; a contiguous block 13–20 passes in
both. **11 layers validate in both families** ({13–20, 24, 28, 29}). ⚠ **Consequence:** every per-layer refusal
claim that leaned on an *early* direction is affected. Specifically it means the depth-localization "L9 null"
(§5.6) rests on a direction that isn't a refusal axis, so that early-vs-late contrast is weaker than stated —
this is why claims **BR-09** and **WR-02** are still PENDING (see §11). Earlier one-family qualifications at
L21/L22/L30 were **[W] withdrawn** as a protocol-asymmetry artifact (the "harmless" population was the family's
own fit set); a benign-population re-run (job 724931) exists but its table was not recomputed in the 08-07 pass.

### 8.2 (P3) Decision-token attention edges — **NULL with a working control** — **[V]**
The earlier edge-KO design (§4.5) was flagged as potentially unfalsifiable; P3 re-ran it targeting the **decision
token** with a genuine positive control. At L8–11: `edge_KO` refusal-axis shift **−0.0032, CI [−0.0078, +0.0010]
(includes 0)**; replicates on the L14–21 carry band (−0.0026, CI includes 0), n=86 both. **Firing control works:**
blocking *every* incoming edge to the decision token moves the projection to **−0.666 (L8–11) / +1.075 (L14–21)**
— far from zero — proving the hook fires and the readout is movable. The corrected paired contrast
`rand_edge − edge_KO` is null and sign-flips in both bands. ⇒ **concept retrieval reaches the decision token
through no identifiable query→demo attention edge.** ⚠ A pre-run smoke bug (constant random-axis shift ~−0.89)
was found and fixed before any result was read; the report withdraws its own inflated "specificity" cell.

### 8.3 (P4a) Induction-head identification — **[V]**
On ClearHarm, the query codeword attends to demo-codeword positions at **~2× count-matched random** (2.107×
dev / 2.039× heldout, both splits) — token-identity retrieval is real (about half the earlier single-pair 3.508×
estimate, which is downward-revised). Attention mass is **correlational only**. The reported "crash" was
cosmetic: both jobs raised `KeyError:'codeword'` *after* `json.dump` wrote the results, so the numbers are complete.

### 8.4 (P4b-1) No single head bottlenecks concept-reading — **[V]**
Patch head-`z` at the demo positions where the retrieval heads act, Wilcoxon-Holm over the 1024-cell family,
confirmation requiring significance on **both** dev and heldout. Re-running `phase5_analyze.py --expect-cells
1024` on both shards (88,408 rows) reproduced the confirmed set exactly: **{L4H16, L10H2, L13H18, L14H13}**,
largest effect L4H16 = 0.0142 dev / 0.0061 heldout; the robust carry-band pair **L13H18 (~0.0022) / L14H13
(~0.0028)**. ⇒ **no single head is a concept-reading bottleneck** (effects 0.001–0.014, near the measurement
floor — "distributed and weak," not "no effect"). A pre-registration estimand bug (a per-cell random-donor
subtraction the run doesn't emit) was found on the live run and corrected to the paired necessity mean before
any result was interpreted. ⚠ Per-shard summaries Holm-correct over only 512 cells (2× too lenient) — only the
pooled 1024-cell output is authoritative.

### 8.5 (P8) The interaction saga — sub-additive → **NULL** (three corrections) — **[V]**
This is the single most instructive correction of the sprint. Does Doublespeak + refusal-ablation *interact*?
Within-item 2×2, `D_i = Y(1,1) − Y(1,0) − Y(0,1) + Y(0,0)`.
- **P8.0 (α=1.0):** reported **sub-additive Î = −0.186, CI [−0.349, −0.023], p=0.045** ("shared refusal
  bottleneck"). **[W] WITHDRAWN.** Adversarial review found: (i) at α=1.0 the design is **saturated** (I_max
  +0.174; 62.8% of items already jailbroken by one factor), so a negative Î is *partly arithmetically forced*;
  (ii) a technical replicate shows **7.5% StrongREJECT label-flips in exactly the signal arms** → p=0.045 is
  fragile; (iii) the three "outcomes" are one measurement.
- **P8.1 (α-calibration):** at the de-saturated operating point **α=0.25** (sole qualifying dose on clearharm)
  the interaction is a **clean null Î = −0.0233, p=0.860** (n=86). Î tracks the I_max **ceiling** across the α
  grid (Spearman +0.991) — a real mechanism has no reason to track a marginal-only ceiling → the apparent
  sub-additivity is a saturation signature. **No α qualifies on curated.**
- **P8 v3 (the decisive run):** combined v3 factorial **n=242** (clearharm 127 + generated 115). Pooled
  **Î = −0.054, CI [−0.124, +0.017], p=0.172 — NULL.** The train split alone shows a significant sub-additive
  Î=−0.124 (p=0.0098) that the **held-out test split reverses (+0.088)** — "the pre-registered split is the only
  thing standing between this project and making the same error twice." **Dose robustness settles it:** at the
  strong dose **α=0.20**, where refusal-ablation *provably fires* (ΔASR vs random +0.142, p=1.2e-4), the
  interaction is **exactly Î=0.000, p=1.000** (29/127 items have non-zero within-item interaction and they
  cancel — a well-populated null, not degenerate). ⇒ **Doublespeak and refusal-ablation ADD, never synergize.**
  ⚠ The "manipulation works" McNemar: refusal-ablation beats count-matched random by **+0.194 combined
  (p < 10⁻¹²)** — the null has teeth. ⚠ Caveats: α=0.25 qualifies on neither v3 cohort; the two cohorts are not
  exchangeable (DS net-positive on clearharm, net-negative/concept-diluting on generated — they answer the
  "can we stack interventions?" question oppositely); pooled CI half-width ≈0.07 so effects <7pp are undetectable.

### 8.6 (P10) Decode-safe write null survives; (P10.0) graded re-analysis → "undetermined" — **[V/R]**
- **P10:** re-ran BEHAV-WRITE with the ablation applied through **every generated token** (not prefill-only),
  against a count-matched random control that absorbs decode damage. The null survives: ΔASR train +0.068
  (McNemar 0.508) / test −0.071 (0.581), specificity write−rand +0.023 / −0.071 (opposite signs), every Holm
  p=1.0, empty_rate 0.0. ⚠ Only clearharm v1 n=86; detecting ΔASR≈0.07 at 80% power needs **n≈275**.
- **P10.0 (graded re-analysis):** **[W]** the binary "behaviorally inert" claim for the carry heads is
  **retracted** (its own power is 8–14%). The graded endpoint recovers a small carry effect (d=+0.0741,
  p=0.034) **but its specificity control FAILS** — a size-matched random-head ablation produces 53% of the
  effect (contrast +0.0349, p=0.382, null). Only 1 of 24 graded tests reaches p<0.05; curated goes the wrong
  way; WRITE is null on the graded endpoint too. ⇒ **honest status: "undetermined," not "necessary."** n at 80%
  power for δ=0.09 → **≈275**. *(This result lives in `outputs_scratch/`, not committed under `outputs/` — [R].)*
  ⚠ It also flags an unresolved **split-leakage confound** (per-instruction intent_cluster, ~64% of rows
  straddle train/test) that must be fixed before train/test agreement is meaningful.

## 9. The corrections ledger (claims we changed about our own work)
The claim-audit table (`reports/CLAIM_AUDIT_TABLE.md`, machine-regenerated by `build_claim_audit.py`) catalogues
**90 paper-facing claims: 67 VERIFIED / 8 WITHDRAWN / 4 SUPERSEDED / 6 UNDERPOWERED / 3 UNVERIFIED / 2 PENDING.**
The corrections that matter:
1. **[W] P8.0 sub-additive interaction (p=0.045)** → saturation artifact; null at the decisive dose (§8.5).
2. **[W] "5-fold CV AUC 0.887 ± 0.106"** → recompute 0.869 ± 0.055; "L16 beats L21" → CI straddles 0 (§5.8).
3. **[W] Phase 5b Q/K/V "clean null"** → RETRACTED (positioning artifact, no positive control, n=2 smoke).
4. **[W] "behaviorally inert" carry heads (binary)** → "undetermined" after specificity control fails (§8.6).
5. **CRITICAL bughunt-F1:** a **FALSE** claim (P81-13, "D_i=+2 synergy occurs zero times in every cohort") had
   been marked **VERIFIED 8/8** — its checks tested only the clearharm dir while *citing curated as evidence*.
   Curated actually shows **4 occurrences** (α0.5:1, α1.5:1, α2.0:2). Demoted VERIFIED→UNDERPOWERED; 7 curated
   checks added with true counts. (The clearharm backstop "0/86" still holds — the ceiling-immune fact is
   cohort-specific, not universal.)
6. **[W] "SLURM SOLVED"** (a claimed 3h32m→6m allocation fix) → falsified same-day; real mechanism found (§10).
7. Numerous scope corrections (L8–L11 → L8–L10; "monotone" readout → terminal spike; "3/4" → "2/4"; etc.) —
   direction of every finding preserved, stated ranges tightened.

Three claims remain **UNVERIFIED** (never recomputed from raw): BR-12 (concept⊥refusal cosine, cross-convention
double-BOS comparison), FIN-03 (carry head-set partial sufficiency — the report cites no run dir), META-03 (the
phase9 `monotone_decreasing` flag — a confirmed live disk mismatch). Two remain **PENDING** on the in-flight
refval job 720463: BR-09 (L9-early refusal null) and WR-02 (write⊥refusal independence) — BR-09 is **AT RISK**
because a smoke suggested only ~15/32 directions validate and L9 may be invalid (§8.1).

## 10. Infrastructure / SLURM saga (context for the run metadata)
A standing **30-minute allocation rule** governs the loop (the `killable` partition is preemptible — allocation
≠ completion). The real blocker was **fair-share priority, not capacity**; resolved by backfilling onto free
non-L40S **a5000/3090** nodes with a VRAM-gated (≥23 GB) allowlist. A GPU-guard shell script cost ~4 self-
inflicted iterations before it worked: a **SIGPIPE silent death** under `set -o pipefail` (an unguarded
`nvidia-smi | head` pipe), an `nvidia-smi nounits` parsing bug ("24576 MiB" breaking a `-ge` test), and an
allowlist bug — all dry-run-tested against a *faked* multi-GPU `nvidia-smi` before resubmit. **Node contention
measured:** 3 model-loading jobs on one node = **16× slower** weight loading → policy became ≤2/node (1/node for
large jobs). A hung job (714997) sat in SLURM `R` state for ~3 h having produced nothing — **liveness must be
read from log mtime, not `squeue`.** A **GPU-coverage audit** (tick 85–86) found **no faked-on-CPU result**:
**251/395 result files embed `device:cuda:0`, 0 embed `device:cpu`**, and the not-yet-started GPU phases
genuinely have no output dirs (todo, not faked). *(That masquerade tally is [R] from the audit prose; the
"no output dir for unstarted phases" half was re-confirmed on disk.)*

---

## 11. What is NOT done (the blunt backlog)

**Capstone phases never run:**
1. **P6 — Jacobian / projection-matrix readout. ✅ RUN 2026-08-07, both cohorts** (clearharm `732004`,
   curated `732011` — localization replicates exactly). `reports/P6_JACOBIAN_READOUT.md`. Harness self-checks passed (hs-index maxabs 0.0; Taylor gate
   ratio 0.941). **Result:** the concept causal Jacobian ‖J‖ peaks mid-band **L12–L17** while the concept
   *readout* peaks **L30** — the Phase-8 "readout ≠ mechanism" dissociation reproduced by an independent
   gradient method; the refusal Jacobian peaks at **L12** (write band) and the refusal scalar drops under DS
   (65→28), independently corroborating refusal suppression. Two caveats remain open: (a) ‖J‖ peaks at similar
   mid layers for *both* targets (cos with semantic dirs ≤0.03), so it is a partly-generic sensitivity profile —
   the target-specific dissociation lives in the projection curves; (b) **the decisive behavioral-prediction
   arm is NOT yet run** — does the refusal Jacobian predict which items jailbreak while the concept Jacobian is
   inert? That join with the ASR outcomes is the P6 follow-on.
2. **P9 / Gate 7 — GCG / MAC / TROPT attack-objective evaluation.** **0 of 13 (up to 21) arms ever run.** The
   P9.0 optimizer-selection bug is fixed (the repr/refusal objective now enters candidate selection, not just
   the gradient; `llama` family added; GPU-free synthetic test only) — but **no arm has executed on GPU.**
   Critically: **every prior "mechanism-derived GCG is net-negative" statement was made with the objective
   DISABLED in candidate selection**, so **Gate 7 currently has NO valid evidence for or against.** The
   "objective does not convert into a token-suffix attack" claim is a *reasoned inference from converging prior
   evidence* (state-injection only weakly sufficient, max malicious rate 0.164; Gate-6 sufficiency fails), **not
   a measured null.** Arms 9/10 (Jacobian objectives) are additionally gated on P6.
3. **P5 — full head→MLP path matrix.** Not done as a sender×receiver sweep (existing `50_path_patching` is
   head→head only, L7–14, top-8).
4. **P1 — corrected GPU baseline + drift envelope.** The one "small GPU phase never actually run." Worth doing
   before any sub-0.10-ASR number is quoted (it defines the interpretability/judge-noise envelope). *(The P1
   empty-generation audit itself IS done and SAFE; it's the GPU baseline re-run that's missing.)*
5. **P11 framework robustness** (one framework only; no TransformerLens/nnsight replication), **P12 quantized**
   (no quantization code path exists), **P13 cross-model replication** (scheduled last; **everything is
   Llama-3.1-8B-Instruct only — no cross-architecture result exists**).
6. **P14 — paper assembly.** PARTIAL: the claim-audit half is built and maintained; the paper draft / figure
   plane / Gate-7 arm table / Jacobian-vs-causal figure are not assembled.

**Open threads on completed phases:**
7. **P4b other channels/cohorts:** the demo-position **and query-position** z channels on **clearharm** are now
   both done+committed (query confirmed heads {L11H4, L16H28, L21H10}, `PHASE4B_HEAD_Z_NECESSITY_DEMO.md §7`,
   RUNMETA/DONE backfilled — resolved 2026-08-07); the Q / K-V(group) / attention-pattern channels, the *all*
   position-set, and a curated replication remain (per `P4B_PREREGISTRATION.md §3`).
8. **BR-09 & WR-02 — RESOLVED 2026-08-07** off the landed refval (720463/721957/722611/724931). **BR-09
   reframed:** L9 is invalid as a refusal axis in every run/family (incl. the benign re-run), so the
   depth-localization "L9 null" is *uninformative* (not evidence of late-reading) — anchor mid-late on the
   validated L16/L18/L22, where the L22 rescue is significant in both cohorts. **WR-02 confirmed + strengthened:**
   `frac_of_direct_gap_restored` restricted to the validated refusal layers {L13–20,24,28,29} is ≤ |0.05|
   (≤ |0.025| clearharm), so the write⊥refusal independence is not an artifact of measuring on unvalidated axes.
9. **v3 downstream re-runs:** the v3 split (324 ex, 0 leakage) is built but **all causal/behavioral headlines
   still run on v1/v2** — only the P8 interaction uses v3. The v3 benign-condition demos are placeholders for 59
   of 138 rows (unusable there until regenerated). P8 v3 is powered short (n=242 vs the n≈324 the power table
   needs for an interaction of 0.15).
10. **Behavioral sufficiency of the carry heads never tested** — the +0.16–0.47 install is representational only.
11. **Granularity mandate A–G met for exactly one intervention family** (MLP-out necessity, 143 windows) and
    only for necessity; head z-patch ran granularity A only; the concept-granularity × refusal-granularity
    factorial the plan demanded was never run.
12. **P2 per-occurrence resolution** (each demo codeword individually) and a **paired within-item test** of the
    all-occurrence increment — not done (the 1.4–2.3× ratios are unpaired).
13. **P10.0 split-leakage confound** (per-instruction cluster, ~64% straddle) must be fixed before its train/
    test agreement means anything; its pre-registration (specificity contrast as primary) is future work.
14. **Coverage validator gaps:** it supports phase5/6 schemas and **crashes on behavioral dirs**; the P7 refval
    row schema is unknown to it (no P7 number has ever been machine-recomputed from its rows); `configs/
    manifests/` is empty, so it can never detect a cell that was *never launched*.
15. **3 UNVERIFIED + prose-staleness items** (§9): BR-12, FIN-03, META-03; and the `REP_PREDICTS_BEHAVIOR.md`
    robustness paragraph still prints the withdrawn CV-AUC.
16. `IMPLEMENTATION_PROGRESS.md` structured trackers are **stale** (still show Phases 4–11 "not started") —
    trust `CONTINUATION_PROGRESS.md`, `CLAIM_AUDIT_TABLE.md`, and this document.

---

## 12. Bottom line for an external reader

**Solidly established (cross-cohort, locked-test, controlled, recomputed from raw):**
1. A complete, **distributed concept circuit** for Doublespeak on Llama-3.1-8B: demo-KV retrieval L8–L10 + an
   L9 MLP write → L14–L21 mediated carry heads → L30–31 proximal output; necessity Holm-significant at every
   stage; carry stage additionally partially sufficient (+0.16–0.47). All-occurrence patching ~doubles the L9
   effect; no single head, edge, or layer is a bottleneck.
2. **Readout ≠ mechanism** — linear readability peaks at L31 while causality sits at L9/L14–21.
3. **The concept circuit is behaviorally inert** — ablating either control site through harmful generation
   leaves ASR statistically unchanged (and the decode-safe re-test confirms it; the graded re-analysis can only
   say "undetermined," not "necessary").
4. **A single orthogonal refusal direction is behaviorally necessary AND sufficient** — ablate → ASR +0.43–0.48
   (a stronger attack than Doublespeak); re-inject → 0.000 with fluent refusals.
5. **The two pathways are causally decoupled** — ablating the concept write moves refusal suppression ≤5% of the
   relevant gap; **Doublespeak and refusal-ablation add, never synergize** (interaction null at the decisive dose).
6. **The refusal decision is read mid-late (~L22)**, the outcome is **fixed at the decision token**, and
   per-item the refusal projection **predicts** jailbreak on clearharm at AUC ~0.87.
7. **`doublespeak_signature` is causally inert** — the observational difference vector is not a mechanism.

**NOT established:** anything about other model families; **whether the mechanism yields a usable attack
objective (Gate 7 untested — 0 of 13 GCG arms run; prior "net-negative" evidence was gathered with the objective
disabled in selection)**; the Jacobian readout (harness ready, never launched); behavioral sufficiency of the
carry heads; and full coverage at the granularities the plan demanded.

**One-line takeaway:** *Doublespeak is an imperfect in-context refusal-suppression technique; the elaborate
token→concept remap is a causally-decoupled, behaviorally epiphenomenal bystander. Defend the refusal axis, not
the concept subspace — and treat the GCG/attack-objective question as open, not answered.*

---

## 13. Artifact index

**This report supersedes** `SPRINT_2026-08-02_TO_08-05_FULL_SUMMARY.md` (08-02→08-05 only). Live status lives
in `CONTINUATION_PROGRESS.md` (ticks 1–86) and `reports/CLAIM_AUDIT_TABLE.md` (90 claims, machine-regenerated).

**Part-A reports:** `reports/PHASE{2_DIRECTIONS,3_RESIDUAL,4_DEMO_RETRIEVAL,4B_PATTERN,5_HEADS,6_MLP,7_PATH,
8_READOUT,9_DOSE}.md`, `reports/CAUSAL_OBJECTIVE.md`, `reports/FINAL_CAUSAL_CIRCUIT_REPORT.md`.
**Part-B reports:** `reports/PHASE_BEHAV_{CARRY,WRITE,REFUSAL}.md`, `reports/PHASE_{WRITE_REFUSAL_INTX,
REFUSAL_TRAJECTORY}.md`, `reports/REP_PREDICTS_BEHAVIOR.md`, `reports/BEHAVIORAL_RESULTS_TABLE.md`.
**Continuation reports:** `reports/{P1_BASELINE_AUDIT,P1B_DATASET_RECOVERY,P1B_V3_SPLIT,PHASE2_ALL_OCCURRENCES,
PHASE3_ATTENTION_CAUSALITY_TARGETED,PHASE4A_INDUCTION_IDENTIFICATION,PHASE4B_HEAD_Z_NECESSITY_DEMO,
P4B_PREREGISTRATION,P7_REFUSAL_DIRECTION_VALIDATION,P8_INTERACTION_V3,PHASE8_1_ALPHA_CALIBRATION,
P10_DECODE_SAFE_WRITE,P10_0_GRADED_REANALYSIS}.md`, `reports/CAUSAL_PATCHING_AUDIT.md`, `BUG_AND_DEVIATION_LOG.md`.

**Key harnesses** (`scripts/`, each with a `slurm/` wrapper): `phase3_demo_neutralize.py`,
`phase4_edge_knockout.py`, `phase4b_pattern.py`, `phase4c_carryedge.py`, `phase5_head_zpatch.py` (+`_analyze`),
`phase6_mlp_causal.py` (+`_analyze`), `phase6b_windows.py`, `phase6_jacobian_readout.py` *(dry-run only)*,
`phase7_direct_total.py`, `phase7b_mediation.py`, `phase7c_sufficiency.py`, `phase7d_onset.py`,
`phase8_readout.py`, `phase9_dose.py`, `phase_behav_{carry,write,refusal,refusal_inject}.py`,
`phase_refusal_{projection,inject_calibrated,trajectory}.py`, `phase_write_refusal_interaction.py`.
**Analyzers:** `analyze_interaction_2x2.py`, `analyze_alpha_calibration.py`, `analyze_graded_reanalysis.py`,
`analyze_rep_predicts_behavior.py`, `behav_judge.py`, `build_claim_audit.py`, `validate_all_outputs.py`,
`build_split_v3.py`, `recover_clearharm_concepts.py`, `audit_phase21_baseline.py`, `backfill_runmeta.py`.
**Primitives** (`pair_common.py`): `SubmodulePatch` (resid_pre), `ComponentOutSwap`, `AllPositionZHeadAblate`,
`AllPositionMLPAblate` (decode-safe), `AttentionKnockout`, `ZHeadPatch`, `AllPositionProjectOutMultiLayer`,
`AllPositionAdd`, `norm_matched_random`.
**Data:** `data/splits/clearharm_doublespeak_v1.json` (137), `data/bench/bench_clearharm_v2.json` (116),
`data/behavioral_v3/` (324). **Figures:** `figures/{circuit_summary,behavioral_dissociation,
refusal_depth_mechanism,causal_decoupling,refusal_trajectory,rep_predicts_behavior}.png`.
