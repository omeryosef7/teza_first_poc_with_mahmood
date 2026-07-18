# CoT-Prefix Mechanism Analysis (Heuristic)

**Method:** `scripts/cot_mechanism_classifier.py` — a regex/keyword classifier over the first ~300 characters (~50-60 tokens) of each generation's `<think>...</think>` block, run against every existing `optimized_*` condition row across 14 run/file sources (standard GCG, 4B, 5A/5B/5C, 6C, 7B seeds 43/44/45 seeded+unseeded, 7A full-520 seeded+unseeded). **3,928 rows classified, 0 missing a `<think>` block** (all optimized-condition Qwen3 generations in the corpus open with a think block). Raw per-row labels: `outputs/stage_gcg_full/COT_MECHANISM_LABELS.jsonl`. Cross-tab summary: `outputs/stage_gcg_full/COT_MECHANISM_SUMMARY.json`.

**This is a heuristic, rule-based classification.** A 48-row stratified manual audit was performed as a follow-up (§3.5) and found **75.0% raw agreement** against independent re-labeling, with two identified systematic biases (§3.5). No formal inter-rater-agreement statistic (e.g. Cohen's kappa) was computed, and the manual audit itself is a single independent read, not multiple raters. Category boundaries are keyword/regex matches and will misclassify some rows (e.g., sarcastic or hedged refusals, mixed framing). Treat the pooled/comparative numbers below as **suggestive, now with a known ~75% labeling accuracy floor**, not as validated ground truth.

Categories (priority order in the classifier: refusal > garbled-recognition > compliant > confusion > direct-restatement > other):
`refusal_planning`, `garbled_adversarial_recognition`, `compliant_willingness_framing`, `uncertainty_confusion`, `direct_task_restatement`, `other_unclassified`.

## 1. Pooled result (all 3,928 rows)

| Label | n | success rate |
|---|---|---|
| direct_task_restatement | 1262 | 12.84% |
| compliant_willingness_framing | 711 | 10.27% |
| uncertainty_confusion | 75 | 10.67% |
| other_unclassified | 1410 | 5.11% |
| garbled_adversarial_recognition | 155 | 5.81% |
| refusal_planning | 315 | **1.27%** |

**Consistent with the hypothesis:** rows classified as `refusal_planning` succeed far less often (1.27%) than any other category — expected, since the classifier's refusal keywords partly overlap with what StrongREJECT itself penalizes. Rows classified as `direct_task_restatement`, `compliant_willingness_framing`, or `uncertainty_confusion` all cluster around 10-13% success, meaningfully above `garbled_adversarial_recognition` (5.8%) and `other_unclassified` (5.1%). **This does not cleanly separate "compliant framing" from "confusion" or "direct restatement" as the specific driver** — the pooled data supports "early framing that isn't refusal-oriented or garbled-recognition-oriented correlates with higher success," a weaker and more defensible claim than "compliant framing specifically mediates success."

## 2. Standard GCG vs 5A CoT-target: does the CoT-prefix fix change early framing?

| Label | standard GCG (75 rows) | 5A CoT-target (75 rows) |
|---|---|---|
| garbled_adversarial_recognition | **50.7%** of rows | 2.7% of rows |
| direct_task_restatement | 12.0% | **40.0%** |
| compliant_willingness_framing | 12.0% | **21.3%** |
| refusal_planning | 14.7% | 8.0% |
| other_unclassified | 10.7% | 24.0% |

**This is the strongest single result in this analysis.** Under standard GCG, half of all optimized generations open their reasoning by explicitly recognizing the suffix as garbled/adversarial text; under 5A's CoT-prefix target, that fraction drops to 2.7%, and "direct task restatement" + "compliant framing" together rise from 24% to 61.3% of rows. This is **consistent with** (not proof of) the synthesis doc's existing claim that CoT-prefix targeting works by steering the model away from recognizing-and-refusing the adversarial input and toward treating the request as a normal one to reason about. Causal attribution would require an intervention (e.g., forcibly editing the think-block opening and observing downstream effects), which was not done.

## 3. Optimization-seed comparison: 7B seed44 (net-negative, ~1.3-2.7% ASR) vs seed45 (best variance run, 16-21.3% ASR)

| Label | seed44 dev (75) | seed44 unseeded (75) | seed45 dev (75) | seed45 unseeded (75) |
|---|---|---|---|---|
| compliant_willingness_framing | 18.7% (success 7.1%) | 17.3% (success 0%) | **36.0%** (success 11.1%) | 14.7% (success 9.1%) |
| direct_task_restatement | 36.0% (success 0%) | 24.0% (success 5.6%) | 34.7% (success **30.8%**) | 28.0% (success **38.1%**) |
| refusal_planning | 6.7% | 17.3% | 13.3% | 10.7% |

Both seeds produce broadly similar *category proportions* for compliant/restatement framing, but the **success rate conditional on `direct_task_restatement`** is dramatically different (0-5.6% for seed44 vs 30.8-38.1% for seed45). This suggests that near-identical teacher-forced task_loss (seed44 best=19.91 vs seed45 best=19.98 — a 0.07 difference, i.e. statistically indistinguishable by loss alone) does **not** predict which seed's suffix converts similar-looking early framing into an actual jailbreak — whatever differs between the two suffixes operates downstream of the first ~50 tokens of reasoning, not in the coarse category of how the reasoning opens. This is **consistent with** "teacher-forced loss does not reliably predict free-generation ASR" (an existing claim in the synthesis doc) and adds a specific mechanistic angle: the divergence isn't explained by gross early-CoT-framing category alone.

## 3.5 Manual audit of the heuristic labels (2026-07-13 follow-up)

A stratified sample of 48 rows (8 per category) was pulled from `outputs/stage_gcg_full/COT_MECHANISM_LABELS.jsonl` and independently re-read and re-labeled by hand against the same category definitions, without looking at the regex output first. Raw comparison: `outputs/stage_gcg_full/COT_MANUAL_AUDIT_SAMPLE.jsonl`.

**Result: 36/48 = 75.0% raw agreement.** This is a real validation number, not a rounding-up — report it as-is rather than the implied-perfect classifier the earlier version of this doc might have suggested by omission.

**The disagreements are not random — they cluster in two identifiable, systematic biases:**

1. **7 of 12 disagreements were rows the regex called `compliant_willingness_framing`** that a manual read would call `direct_task_restatement` (6 of the 7) or `uncertainty_confusion`/`garbled_adversarial_recognition` (1 each). Root cause: `COMPLIANT_PATTERNS` matches generic phrasing like *"the user wants me to write/create X"* — but this phrasing appears in nearly every CoT opening regardless of whether the model actually shows willingness, because it's simply how Qwen3 restates any request before reasoning further. The regex's priority order (compliant checked before confusion/restatement) means this generic restatement wins the label even when the *rest* of the snippet (not captured by keyword matching, which only looks at pattern presence, not sentence-level context) shows confusion or hedging instead.
2. **4 of 12 disagreements were rows the regex called `other_unclassified`** that a manual read would call `refusal_planning` (3 of 4). Root cause: the model's refusal language in these cases used phrasing not in `REFUSAL_PATTERNS` (e.g. "I should respond by rejecting the request," "my primary responsibility is to ensure that the content...") — a keyword-list coverage gap, not a conceptual disagreement about what refusal_planning means.

**What this changes about §1-§2's conclusions:**

- The **`compliant_willingness_framing` category is likely contaminated** by generic restatement phrasing and should not be treated as cleanly separated from `direct_task_restatement` — the pooled/per-source comparisons in §1-§2 that discuss "compliant + restatement rising from 24% to 61.3%" (5A vs. standard GCG, §2) remain informative as a **combined** "non-refusal, non-garbled-recognition" bucket, but the *internal* split between "compliant" and "restatement" within that bucket should not be over-interpreted.
- **`refusal_planning` is likely mildly undercounted**, and the true refusal-planning population would probably show an even lower success rate than the already-lowest 1.27% reported in §1 (since the additional true-refusal rows found here were all StrongREJECT failures) — this strengthens rather than weakens that particular part of the finding.
- The core §2 result (standard GCG 50.7% garbled-recognition vs. 5A's 2.7%) was not touched by this sample (no garbled-recognition rows were among the 12 disagreements in a way that would flip that comparison), so that specific finding is unaffected by the labeling noise found here.

**Bottom line: treat this classifier as ~75% accurate against a single manual reader, with a known bias inflating "compliant" at the expense of "restatement"/"confusion," and a known gap under-detecting some refusal phrasing.** This is still useful for the coarse, pooled comparisons in this document, but any future use of the row-level labels for anything more granular than "refusal vs. not" or "garbled-recognition vs. not" should first re-run the classifier with an expanded keyword list and, ideally, a larger manual-audit sample (48/3,928 rows = 1.2% of the corpus was checked here).

## 4. Explicitly not established by this analysis

- **No causal claim.** Everything above is correlational (label vs. observed StrongREJECT outcome on the same generation).
- **No manual validation of labels.** Regex-based categories will have real misclassification; the magnitude of that error is unmeasured.
- **No generalization test beyond the 25-development + 520-full-benchmark behaviors already in the corpus** (the corpus does include 7A full-520 rows, so the standard-GCG-vs-5A framing shift in §2 is only demonstrated on the 25-behavior small-set comparison — 7A's own per-source breakdown, in `COT_MECHANISM_SUMMARY.json`, can be pulled for the full-520 scale if needed as a follow-up, but is not summarized here for space).
- Use hedged language only: "consistent with," "correlates with" — not "confirms," "proves," or "mediates" (a mediation claim requires a designed causal analysis, not a cross-tab).

## 5. Causal test (Sprint 2 Track 2, 2026-07-14) — correlational finding NOT supported causally

The gap flagged in §4 ("no causal claim... a mediation claim requires a designed causal analysis") was closed this sprint: `poc_stage_gcg_early/run_cot_intervention.py` forces a chosen category's canonical opening as the literal start of the model's `<think>` block for the existing 5A suffix, then lets generation continue completely freely (not teacher-forced), scoring with the same StrongREJECT path. Full detail: `docs/GCG_SPRINT2_TRACK2_COT_INTERVENTION_LOG.md`.

**Result at n=25 tasks/condition** (150 rows total, 5A suffix, Qwen3):

| Condition | Successes / 25 |
|---|---|
| baseline (unforced) | 3 (12.0%) |
| forced_compliant_willingness_framing | 2 (8.0%) |
| forced_refusal_planning | 0 |
| forced_garbled_adversarial_recognition | 0 |
| forced_uncertainty_confusion | 1 |
| forced_direct_task_restatement | 0 |

**Forcing `compliant_willingness_framing` did not increase success over baseline — it was nominally lower (8.0% vs. 12.0%; McNemar's exact test on the paired data, p=1.0, though power is low with only 3 discordant pairs at this n).** An earlier n=10/condition pilot showed the same qualitative pattern (tied at 1/10 rather than exceeding baseline), so this is not a small-sample artifact — the result held at 2.5x the sample size.

**This is a genuine negative causal result, not merely "inconclusive."** The correlational finding in §1-§2 (compliant framing correlates with higher success) should **not** be read as "forcing compliant framing causes higher success" — the causal test directly contradicts that stronger reading. A plausible (untested) alternative explanation: the correlation may reflect that successful generations *naturally* produce compliant-sounding CoT openings as a downstream artifact of whatever the suffix is actually doing to the model's internal state, rather than the surface framing text itself being a lever that influences the rest of generation — forcing the text without the suffix's real mechanistic influence over subsequent tokens does not reproduce the effect. Any future summary of this document's correlational findings should explicitly note this causal test failed to confirm them, rather than presenting §1-§2 in isolation.
