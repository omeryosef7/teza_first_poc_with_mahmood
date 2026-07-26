# CoT-Hijacking — Exact Mechanism Report

**STATUS: PARTIAL.** Phase **F1.1 (CPU / tokenizer-only span reconstruction) is DONE**.
Phases **F1.2–F1.6 (span ablation, attention over spans, causal patching) are GPU work and are NOT started here.**

Author: Phase-F worker (CPU-only, no GPU/SLURM, no model weights loaded — tokenizer-only via `AutoTokenizer`).
Date: 2026-07-25.

---

## 1. Goal of F1.1

Reconstruct, on **existing** attacked outputs (no new generation), the exact string
fed to each target model through **its own chat template**, and mark — with both
**character spans** and **token-index spans** (the model's own tokenizer) — the
seven structural components of a Chain-of-Thought-Hijacking prompt:

| key | component | how it is located (deterministic) |
|---|---|---|
| (a) `harmful_instruction` | verbatim harmful goal | case-insensitive substring search for `goal` inside `attack_prompt` |
| (b) `benign_puzzle_scaffold` | neutral puzzle / math framing | from first scaffold anchor (`Let `, `Sudoku`, `Skyscrapers`, `logic grid`, `graph`, `grid`, …) up to the final-answer cue |
| (c) `injected_reasoning` | harmful-operation ↔ puzzle mapping block | mapping anchors (`Covert Action Mapping`, `ψ(k)=`, `Tactic-Function Mapping`, `System Interaction Protocol`, `Define action set`, …) bounded on the right by the next section header |
| (d) `final_answer_cue` | "solve step-by-step … practical example" directive | ordered cue anchors (`Requirement:`, `Required Output`, `Solve the given problem step by step`, `present a detailed practical example`, `practical example`, …) to end of prompt |
| (e) `system_prompt` | target system prompt | located only when supplied via `--system-prompt` (see §4) |
| (f) `chat_template_tokens` | structural special tokens | regex over the tokenizer's special/added-vocab strings found in the templated string |
| (g) `assistant_generation_marker` | generation-prompt marker | diff of `apply_chat_template(add_generation_prompt=True)` vs `False`, snapped to a special-token boundary |

The source attacker prompts are the released nested-reasoning "covert operation"
templates `new_prompt8`…`new_prompt13` in
`Chain_of_Thought_Hijacking/Hijacking/config/system_prompts.py` (category-theory graph,
Sudoku, logic-grid, and Skyscrapers variants). Note these are the **attacker**'s
system prompts; the string actually sent to the target is the model-generated puzzle
stored per-example in `attack_prompt` (confirmed via `utils/conversation.py`,
`utils/parsing.py`, and the JSONL schema).

## 2. Deliverables (verified paths)

- `scripts/phase_f_cot_span_annotate.py` — deterministic, reusable annotator.
  Input = an attacked JSONL + an HF model name (tokenizer only); output = per-example
  span records JSONL with char **and** token-index ranges. Sets `HF_HUB_OFFLINE=1`.
- `tests/test_cot_span_annotate.py` — 8 offline unit tests (no transformers, no weights);
  toy synthetic prompt with known offsets + the char→token mapper. `8 passed`.
- `outputs/phase_f_cot_spans/Qwen_Qwen3-14B_spans.jsonl` — 44 examples.
- `outputs/phase_f_cot_spans/microsoft_Phi-4-mini-reasoning_spans.jsonl` — 72 examples.

Inputs used (existing outputs, unchanged):
`outputs/phase5_qwen3_cot/phase4_cot_hf_Qwen_Qwen3-14B_dev25.jsonl` and
`outputs/phase4_hf_local/phase4_cot_hf_microsoft_Phi-4-mini-reasoning_dev25.jsonl`.
(Phi-4-mini-reasoning chosen as the HF-local model because its tokenizer is cached
locally and it has a matching `dev25` attacked-output file; gemma-3-4b-it and
DeepSeek-R1-Distill-Llama-8B tokenizers are not cached, so they are deferred.)

## 3. Per-model coverage (n located / n examples) — FACTS

| component | Qwen3-14B (n=44) | Phi-4-mini-reasoning (n=72) |
|---|---|---|
| (a) harmful_instruction | 5/44 | 4/72 |
| (b) benign_puzzle_scaffold | 44/44 | 72/72 |
| (c) injected_reasoning | 21/44 | 36/72 |
| (d) final_answer_cue | 44/44 | 69/72 |
| (e) system_prompt | 0/44 | 0/72 |
| (f) chat_template_tokens | 44/44 | 72/72 |
| (g) assistant_generation_marker | 44/44 | 72/72 |

Median prompt length: ~1251 tokens (Qwen3), ~1249 tokens (Phi-4).

## 4. Honest coverage notes (examples where a span could NOT be located)

- **(e) system_prompt — 0/44 and 0/72 by construction.** These attacked runs sent
  no explicit target system prompt (the JSONL has no system field), so nothing is
  located. Passing `--system-prompt "<text>"` makes the annotator inject and locate
  it. Separately, Phi-4's chat template auto-injects a default system string
  (`"Your name is Phi, an AI math expert developed by Microsoft."`); it is currently
  captured inside the `chat_template_tokens`/wrapping region, not broken out as a
  distinct system span. Breaking out template-default system text is deferred.
- **(a) harmful_instruction — located in only 5/44 (Qwen) and 4/72 (Phi).** This is a
  genuine property of the attack, not a bug: the CoT-Hijacking prompt **disguises**
  the goal as puzzle variables/operations, so the verbatim goal string is usually
  absent. When it appears it is inside the final-answer cue (e.g. "…illustrate the
  process of 'Write a script that can exploit vulnerabilities…'").
- **(c) injected_reasoning — 21/44, 36/72.** The explicit operation-mapping block
  (`ψ(k)=`, "Covert Action Mapping", tactic/SIP tables) exists only in the
  Sudoku/logic-grid/Skyscrapers variants (`new_prompt9`–`new_prompt13`). The
  category-theory / graph variant (`new_prompt8`-style) embeds the harmful ops
  directly in node/edge definitions with no mapping-table anchor, so no span is
  emitted. Honest miss.
- **(d) final_answer_cue — 3/72 Phi misses.** Tasks `advbench_full_0001`,
  `_0188`, `_0271` phrase the directive with novel wording ("script blueprint",
  "rationalization of the derived sequence") that matches none of the cue anchors.
  All 44 Qwen examples were located.

Components (b), (f), (g) were located in **every** example on both models.

## 5. Method / reproducibility

```
TROPT/.venv/bin/python scripts/phase_f_cot_span_annotate.py \
  --input <attacked.jsonl> --model <hf/name> --output <out.jsonl> [--system-prompt STR] [--limit N]
```

Token indices are obtained by templating with `apply_chat_template(tokenize=False,
add_generation_prompt=True)`, then re-tokenizing that exact string with a fast
tokenizer using `return_offsets_mapping=True` (`add_special_tokens=False`), and
intersecting each character span with the token offset intervals. Deterministic; no
weights, no network (offline flags set). Adjacent spans may share a boundary token
when one token straddles the char boundary (expected).

## 6. F1.2–F1.5 measurement & causal-intervention DESIGN (CPU-authored; GPU-deferred execution)

Status: **DESIGN ONLY** (plan Priority-5, Gate 5). No GPU run yet. This section makes the GPU phase
turnkey: it fixes the split, the exact statistics, and the causal tests so execution is mechanical when
a non-competing L40S slot is available. The F1.1 span token ranges (§2) are the inputs throughout.

### 6.0 Cross-phase rules inherited from the Gate-3 finding (MANDATORY here)
- **Generation budget = `max_new_tokens=2048`** for ANY ASR/behavioral re-measurement (F1.2, F1.5).
  The Gate-3 truncation artifact (256-token cap never closing `<think>`; see
  `docs/REINFORCE_OBJECTIVE_REPORT.md §3.1`) must NOT recur — a mechanism that only changes *truncated
  in-think* text is not a behavioral mechanism.
- **Judge = the frozen StrongREJECT** (Phase B4). Until frozen, every ASR here is EXPLORATORY-labelled;
  keep empty/degenerate generations in the denominator; report n/n_total, not bare %.
- **Discovery vs test split, declared up front (no double-dipping):** candidate-head *discovery* (F1.4)
  uses a **DISCOVERY split only**; all causal claims (F1.5) are evaluated on a **held-out TEST split**.
  Proposed: split the annotated dev-25 set per model into disjoint discovery/test halves by `task_id`
  (stable hash), never by row, so a behavior never appears in both.

### 6.1 F1.2 — span-ablation (necessity screen; coarse, attention-mask based)
For each labelled span component (esp. `injected_reasoning`, `benign_puzzle_scaffold`,
`final_answer_cue`), on the DISCOVERY split: re-run the forward/generation with that span's **token
range attention-masked** (key positions zeroed in the attention pattern at *all* layers) and re-measure
delivered ASR (2048 tokens, frozen judge). Report ΔASR = masked − unmasked, per component, n/n_total.
Interpretation: a large ASR drop when masking `injected_reasoning` (but not when masking control spans)
is *evidence of necessity* of attending to the injected reasoning — a coarse screen that scopes which
components F1.3/F1.4 examine. Not itself a head-level mechanism.

### 6.1a Data-driven structural prior (from `results/COT_SPAN_STRUCTURE.csv`, scalar-only) — CORRECTS the directionality
Before running any attention probe, the F1.1 span *structure* was analysed
(`scripts/cot_span_structure_analysis.py`, `docs/COT_SPAN_STRUCTURE_ANALYSIS.md`; numeric fields only).
Key finding, both models (Qwen3-14B n=13 succ / 31 fail; Phi-4-mini n=13 / 59):
- **`injected_reasoning` is located in 0% of SUCCESSES but 61–68% of FAILURES**, as a short (~6–8 tok)
  span at normalized position ~0.32.
- `benign_puzzle_scaffold` is present in 100% of both, but **failures carry a LONGER scaffold**
  (Qwen 1164 vs 676 tok; Phi 1075 vs 877). `final_answer_cue` is near-ubiquitous and late (~0.89) in both.

**This INVERTS the naïve hypothesis** (that attending to `injected_reasoning` drives success). What the
annotator labels `injected_reasoning` (a short mid-CoT deliberation span) co-occurs with **FAILURE**,
consistent with the project's compliant-CoT thesis: *visible deliberation / reconsideration marks a
refusal path; successful hijacks comply without a distinct deliberation span.* **Caveat:** n_success=13
is small and the 0% may be partly an annotation-pattern effect (the detector may key on
refusal-deliberation phrasing) — descriptive, not causal.
**Design consequence:** F1.3 is re-scoped to be **direction-agnostic** and to treat the presence of /
attention to the deliberation span as a candidate **REFUSAL (failure)** signal, not a hijack signal;
successes are characterised by its ABSENCE + a shorter scaffold. The mechanistic question becomes:
*which heads distinguish compliant-CoT (success) from deliberative-CoT (failure)?*

### 6.2 F1.3 — attention-to-span measurement (per layer × head)
On the DISCOVERY split, from a clean (unablated) forward pass over each attacked output, compute for
every (layer ℓ, head h) the **attention mass directed FROM the generation/`final_answer_cue` query
positions TO each labelled span's key token range**, normalized by the row's total attention (so masses
sum ≤ 1 across key spans). Aggregate:
- `A[ℓ,h, comp]` = mean over successes of attention mass into `comp` (comp ∈ {injected_reasoning,
  benign_puzzle_scaffold, harmful_instruction, final_answer_cue, chat_template_tokens}).
- The same for FAILURES. The **success−failure contrast** `ΔA[ℓ,h,comp]` is the candidate signal.
Report as a layer×head heat matrix per component + the top-k (ℓ,h) by |ΔA|. **Per §6.1a the primary
cross-outcome contrast uses components present in BOTH splits** — `benign_puzzle_scaffold` (success
attends less? shorter), `harmful_instruction`, `final_answer_cue`. `injected_reasoning` is absent in
successes, so attention INTO it is a *failure-only* measure — probe it as a candidate refusal signal
(do heads route attention into the deliberation span only on the refusal path?), not as a
success-contrast. This is the head-resolved analogue that the *uniform*-temperature attention null
(Phase-8) did **not** rule out — the original null scaled ALL heads equally; here we localize.

### 6.3 F1.4 — candidate-head discovery (DISCOVERY split ONLY)
Rank (ℓ,h) by the success−failure attention-contrast into `injected_reasoning` (and, separately,
`benign_puzzle_scaffold`). Select the top-K (e.g. K=10) as **candidate hijack heads**. Freeze this list
BEFORE touching the test split. Record the selection statistic + threshold so it is reproducible. No
causal claim yet — these are *correlational* candidates.

### 6.3a Length/structure confound control (MANDATORY GATE before F1.5 — added post-F1.3)
The actual F1.3 result (§7) shows the ONLY substantial success−failure attention contrasts are into
`benign_puzzle_scaffold` (+) and `final_answer_cue` (−), and §6.1a already establishes that **failed
prompts carry a LONGER scaffold** (Qwen 1164 vs 676 tok; Phi 1075 vs 877). Attention mass into a span
scales with the span's size/position, so the candidate contrast is **plausibly length-driven, not causal**
— the same confound that made the parent project's success-direction predictive-but-not-causal. Therefore,
**before spending GPU on F1.5**, the candidate must survive a confound screen (CPU, from a re-run of the
F1.3 probe with per-record mass logging — see `run_probe(..., per_record_csv=...)`):
1. **Within-outcome regression:** regress each record's scaffold/cue attention-mass at the candidate head
   on that record's scaffold token-length, SEPARATELY for successes and failures. If the success−failure
   mass gap disappears once scaffold-length is conditioned on → the contrast is a length artifact → **do
   NOT proceed to F1.5** (retain as detector-only, report the confounded negative).
2. **Matched-length subsample:** restrict to success/failure pairs with scaffold-length within a caliper
   (e.g. ±100 tok) and recompute the contrast; report the surviving effect + n (expect small n, like the
   parent project's caliper matching which left only 1/6/9 pairs — power-limited but honest).
3. **Layer sanity:** discount L0-dominated contrasts (positional/token-identity, interpretively weak);
   require the surviving signal to appear at mid/late layers to be worth a causal test.
Only a contrast that survives (1)+(2) at a non-trivial layer justifies the F1.5 GPU spend.

### 6.4 F1.5 — targeted causal interventions (held-out TEST split)
**Precondition:** §6.3a confound screen passed. For the frozen candidate heads only, on the TEST split,
run three interventions and re-measure delivered ASR (2048 tokens, frozen judge), each vs baseline:
1. **Head ablation** — zero the candidate heads' output (or set their attention into `injected_reasoning`
   to uniform). Necessity: does ASR drop?
2. **Attention scaling** — up-/down-weight candidate heads' attention into `injected_reasoning`.
   Dose-response: does ASR move monotonically?
3. **Activation patching** — patch candidate-head activations from a matched *failed* run into a
   *successful* run (and vice-versa). Sufficiency: does patching flip the outcome?
Controls: the SAME interventions on K random non-candidate heads (should show ~no effect); keep
empty/degenerate in the denominator; ≥3 seeds where sampling is involved.

### 6.5 Gate 5 (plan §8) and F1.6
**Gate 5 = YES** iff a *targeted* (head/position-specific) intervention is **causal** — i.e. ablation
drops ASR AND scaling is dose-responsive AND patching transfers the outcome, on the held-out TEST split,
beyond the random-head controls. If **NO** → the internal CoT signal is retained as a **detector only**
(consistent with the Phase-8 uniform null and the predictive-not-causal residual result); do **NOT**
distil it into a TROPT loss. If **YES** → F1.6 distils the mechanism into a TROPT loss (e.g. a
`CombinedLoss` term rewarding attention into `injected_reasoning`) and compares it to the behavioral
REINFORCE objective — noting REINFORCE is already a Gate-3 negative, so a causal mechanism here would be
the *only* live route into discrete optimization.

### 6.6 Inputs / reuse (build-new only where forced)
Span token ranges = §2 outputs. Model + chat-template + attention-capture = `poc_stage4/qwen3_model.py`
(+ `output_attentions=True` forward). Delivered-ASR harness + StrongREJECT =
`poc_stage_gcg_early/evaluate_optimized_suffixes.py` (2048 tokens). Only the attention-to-span
aggregation and the head-intervention hooks are new. All GPU-deferred; execution blocked only on a
non-competing L40S slot (the Gate-3 seed jobs currently hold the queue).

## 7. F1.3 attention-probe RESULTS (Phi-4-mini done; Qwen3-14B pending) — CORRELATIONAL, DISCOVERY split

Status: **partial first result.** Job `685334_1` (Phi-4-mini) COMPLETED → `results/COT_F13_phi4_mini.csv`
(3072 rows = 32 layers × 24 heads × 4 components; **discovery split n_success=7, n_fail=33**). Qwen3-14B
(`685334_0`) OOM-failed on the fp32 upcast of stacked 40-layer attention (Qwen prompts ~1251 tok →
~10 GiB); fixed to per-layer CPU offload and resubmitted (`685503_0`). All numbers here are the
**success−failure attention-mass contrast Δ = mean_succ − mean_fail**, per (layer, head), from the
`final_answer_cue` query positions into each span. **These are CORRELATIONAL candidate heads on the
DISCOVERY split only — NOT a demonstrated mechanism.** The causal test is F1.5 (Gate 5) on the held-out
TEST split.

**Phi-4-mini — top |Δ| per component:**

| component | top head | Δ (succ − fail) | succ mean | fail mean | where the top-20 |Δ| heads sit |
|---|---|---|---|---|---|
| `benign_puzzle_scaffold` | L0 H22 | **+0.289** | 0.321 | 0.033 | 10/20 layer-0, others at L31 (last) |
| `final_answer_cue` | L0 H22 | **−0.287** | 0.685 | 0.972 | 10/20 layer-0, others at L31 |
| `injected_reasoning` | L26 H23 | −0.026 | 0.000 | 0.026 | 0/20 layer-0 (mid-late L22–30) |
| `harmful_instruction` | L0 H20 | −0.002 | 0.000 | 0.002 | negligible everywhere |

**Honest reading:**
1. The only SUBSTANTIAL contrasts are into `benign_puzzle_scaffold` (**+**, successes attend MORE) and
   `final_answer_cue` (**−**, successes attend LESS) — near-exact **mirror images** (same heads, opposite
   sign). Since the query positions ARE the cue, this says: **in successful attacks the cue positions
   route attention BACK to the benign scaffold instead of staying locally on the cue; in failures
   attention stays concentrated on the cue (~0.97).** This is *consistent with* the CoT-Hijacking
   "attention diluted toward the benign scaffold" hypothesis.
2. The contrasts concentrate at the **first (L0) and last (L31)** layers. **L0 attention is
   positional/interpretively weak** — a caution against over-reading.
3. `injected_reasoning` Δ is tiny and simply re-expresses the §6.1a inversion (the span is absent in
   successes, so `succ_mean≈0`), NOT an independent signal. `harmful_instruction` Δ ≈ 0 (goal disguised).

**The dominant CONFOUND (must be controlled in F1.5).** The success vs failure prompts differ
STRUCTURALLY: per §6.1a the span-structure analysis already showed **failed prompts carry a longer benign
scaffold** (Phi 1075 vs 877 tok) and a distinct deliberation span. Attention mass into a span depends on
its size/position, so the L0/L31 scaffold-vs-cue contrast **may be driven by these structural differences
rather than a causal hijack mechanism** — the same length/structure confound that plagued the parent
project's success-direction (predictive-but-not-causal). With **n_success = 7** this is under-powered and
correlational. **⇒ F1.5 (Gate 5) must intervene on the candidate heads on the held-out TEST split AND
control the length/structure confound** (e.g. matched-length prompts / random-head controls) before any
causal claim. Nothing here is distilled into a TROPT loss yet (Gate 5 not passed).

## 7.1 §6.3a length-confound SCREEN (Qwen3-14B) → Gate-5 pre-decision: NOT justified

Ran the §6.3a screen on the per-record probe output `results/COT_F13_qwen3_14b_perrecord.csv`
(confound-log run, job 685551_0). Qwen discovery split **n_success=6, n_fail=16**. 2-model consistency:
Qwen shows the SAME direction as Phi — successes attend MORE to `benign_puzzle_scaffold` (aggregate top
L5 H34 Δ+0.18: 0.49 vs 0.31) and LESS to `final_answer_cue` (top L1 H25 Δ−0.18) — mirror images.

**Confound screen result — the scaffold contrast is strongly LENGTH-CONFOUNDED:**
- Structural gap (as §6.1a): success scaffold length **742** vs fail **1169** tok; success total **908**
  vs fail **1304** tok — failures are much longer.
- **Scaffold attention-mass is strongly correlated with scaffold token-length:** pooled Pearson
  r(mass, scaffold_len) = **0.68**, r(mass, n_tokens) = 0.56; **within-success r = 0.95**, within-fail
  r = 0.30. So a record's scaffold attention is largely a function of how long its scaffold is.
- At the head-averaged **layer** level the success−fail scaffold-mass gap is small and length-consistent
  (max-gap layer L24: succ 0.292 < fail 0.345 — failures slightly higher, matching their longer scaffolds).

**Two honest limitations:**
1. **Granularity:** the per-record CSV logs mean-over-heads per layer, so it cannot isolate the specific
   candidate head (L5 H34 / Phi L0 H22) where the +0.18 contrast lives — that contrast (successes attend
   MORE *despite* SHORTER scaffolds) runs OPPOSITE to the naive length effect and is NOT cleanly
   separable from the confound at this logging granularity. A per-HEAD per-record log would be needed.
2. **Power:** n_success = 6 (Qwen) / 7 (Phi). This is fundamentally limited by how many dev-25 behaviors
   the attack actually succeeds on; even a clean per-head length-controlled test would be badly
   underpowered. Getting more successes requires more behaviors/models (out of scope here).

**GATE-5 PRE-DECISION = NOT JUSTIFIED (retain detector-only).** The F1.3 head-level contrast is (a)
strongly entangled with the scaffold-length confound (the same length confound that made the parent
project's success-direction predictive-but-not-causal), (b) not cleanly isolable at current logging
granularity, and (c) severely underpowered (n_succ 6–7). Per §6.3a, only a contrast that survives the
length control at a non-trivial layer justifies the F1.5 GPU spend — this one does not, on current
evidence. **Therefore the CoT internal signal is retained as a DETECTOR/correlational observation, NOT
distilled into a TROPT loss** — consistent with the Phase-8 uniform-attention null and the whole project's
predictive-not-causal finding. This does NOT prove there is no head-mechanism; it says the available
dev-25 evidence is too confounded + underpowered to justify the causal test. A future powered probe
(per-head per-record logging + a larger success set + matched-length controls) could revisit it.

### 7.2 §6.3a screen — Phi-4-mini (2-model view refines the Gate-5 rationale)
Phi confound-log per-record (`results/COT_F13_phi4_mini_perrecord.csv`, job 685551_1): n_succ=7, n_fail=33.
Phi's picture DIFFERS from Qwen's:
- Scaffold-length succ 974 vs fail 1074 tok — **small** gap (Qwen had 742 vs 1169).
- **Pooled r(scaffold-mass, scaffold_len) = 0.18** (weak), r(., n_tokens) = −0.02 — so Phi's scaffold
  contrast is **NOT strongly length-confounded** (Qwen was r=0.68). Within-success r=0.80 (still strong),
  within-fail r=−0.16.

**Honest 2-model synthesis (correcting an earlier over-statement):** the head-level contrast is NOT
uniformly "length-confounded." Per model: **Qwen** — the scaffold contrast IS largely length-driven
(pooled r=0.68, big succ/fail length gap); **Phi** — the contrast is LARGER (agg Δ0.29 vs 0.18) and
**not primarily length-driven** (pooled r=0.18), but its top heads are at **L0 (positional/interpretively
weak)** and n_succ=7. So neither model meets the §6.3a bar, but for DIFFERENT reasons: Qwen fails the
length control; Phi fails the layer-sanity + power criteria.

**GATE-5 PRE-DECISION UNCHANGED = NOT JUSTIFIED**, but with a sharper, honest caveat: this is **not** a
clean "it's all confound" dismissal. Phi hints at a scaffold-attention success signal that is not
length-explained — but it is positional (L0), underpowered (n=7), and not isolable to the candidate head
at current mean-over-heads logging. The disciplined call stands: **do not spend GPU on the F1.5 causal
test on this evidence; retain detector-only.** A properly-powered probe (per-HEAD per-record logging + a
larger success set across more behaviors/models + matched-length controls) is the only thing that could
turn this into a testable causal hypothesis; it is out of scope for the dev-25 data here.
