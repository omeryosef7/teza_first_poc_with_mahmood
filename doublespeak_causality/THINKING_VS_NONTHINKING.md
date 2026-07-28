# Thinking vs Non-Thinking (Level 6)

**Deliverable (plan §23, Workstream G / Phase 7).** Within-model (same weights) comparison of thinking
vs non-thinking behavior on the Doublespeak attack. Model: **Qwen3-14B** (the correct within-model test —
identical weights, only the chat template differs). Benchmark: curated harm-in-noun (first 90 conditions,
15 bases). Judge: corrected StrongReject + refusal-language. Scripts: `17` (--enable-thinking), `analyze_thinking.py`.

---

## 0. Mode configuration (verified, plan §11.1)
Qwen3 same checkpoint; `enable_thinking` via the official chat template. **Gotcha (verified):** Qwen3
default is thinking-ON; `enable_thinking=False` must be passed explicitly (injects an empty `<think></think>`)
— see `ds_common.apply_template`. thinking-ON generates a full `<think>…</think>` CoT before the answer
(max_new_tokens raised to 400 to fit CoT+answer); thinking-OFF max 200. Matched conditions, same judge.

## 1. Result — paired comparison (n=90 matched conditions)

| metric | non-thinking | thinking | Δ (think−nothink) [95% CI] |
|---|---|---|---|
| DS **malicious** rate | 0.244 | 0.222 | −0.022 [−0.122, 0.078] — NS |
| DS **rejected** (refused) rate | 0.000 | 0.067 | **+0.067 [+0.022, +0.122] — significant** |
| Direct refused rate | 1.000 | 0.933 | −0.067 [−0.122, −0.022] — significant |
| Neutral benign rate | 0.833 | 0.633 | (lower — thinking judges more Neutrals non-benign) |

**DS-malicious rate by demo count (context length):**
- non-thinking: 4→0.09, 8→0.16, 12→0.16
- **thinking: 4→0.14, 8→0.23, 12→0.36** — a STEEPER dose-response.

Paired DS transitions (nothink→think): BENIGN→BENIGN 56, MALICIOUS→MALICIOUS 11, BENIGN→MALICIOUS 9,
MALICIOUS→BENIGN 8, MALICIOUS→REJECTED 3, BENIGN→REJECTED 3.

## 2. Interpretation (plan §11.6 hypotheses)
- **H-A (thinking amplifies the attack): NOT supported overall** — DS-malicious rate is unchanged
  (0.22 vs 0.24, NS). Reasoning does not, on net, make the attack more successful.
- **H-B (thinking improves safety): WEAKLY supported** — thinking introduces DS refusals (0.00→0.067,
  significant); reasoning lets the model catch *some* hijacks and refuse (MALICIOUS→REJECTED, BENIGN→REJECTED).
- **Newly observed:** thinking **steepens the dose-response** (more demonstrations → more jailbreak:
  0.14/0.23/0.36 vs 0.09/0.16/0.16). Reasoning appears to retrieve/aggregate the demonstrations more with
  more context — an *amplifying* effect that grows with demo count, offsetting the small safety gain.
- Net effect is **small and mixed**: a significant but tiny increase in refusals + a steeper dose-response,
  with no significant change in overall success.

## 3. Level 6 assessment (honest)
A **detectable within-model thinking difference exists** (significant increase in DS refusals; steeper
dose-response) — Level 6 partially met. But the magnitude is **modest** (single-digit pp), and it is a
*behavioral* comparison, **not** a causal thinking-time intervention (plan §11.7, not yet run). The
"robust" bar (§24 Level 6) is not fully cleared — it needs larger N and a thinking-time intervention.

## 4. Limitations / next
- n=90 (15 bases), Qwen3 only. Thinking generation is slow (CoT) → small N under preemption.
- No thinking-time intervention yet (§11.7: remove/add the harmful direction during early vs late thinking;
  does refusal onset shift?) — this is the causal test that would connect thinking to the TOCTOU timing law.
- No representation-level thinking trajectories yet (§11.5) — where in the CoT the hijacked meaning forms.
- Larger matched N + Phi-4-mini-reasoning replication pending.
