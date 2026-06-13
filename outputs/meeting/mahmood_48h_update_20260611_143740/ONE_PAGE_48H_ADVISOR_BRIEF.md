# From Refusal Direction to Reasoning-Path Hijacking: 48h Update

_Omer Yosef — June 11, 2026 — For: Mahmood_

---

## 1. What We Already Knew (Stage 4 baseline)

Chain-of-Thought attacks on Qwen3-14B succeed when a puzzle wrapper forces the model
into extended thinking. The Layer-22 "harmful-vs-harmless" direction has separation 14.17
but does NOT predict behavioral compliance (it tracks thinking depth, not attack success).

---

## 2. New Paper-Style Behavioral Result (Stage 4.7 + 4.8)

**Stage 4.7** — Cleanest test: 12 source prompts, 4 conditions, greedy decoding.

| Condition | ASR% | Thinking Tokens (median) |
|-----------|------|------------------------|
| A — Full puzzle + thinking | **83.3%** | 13,592 |
| D — No puzzle + thinking | 45.5%* | 2,574 |
| F — Benign wrapper + thinking (same length) | 27.3%* | 821 |
| E — Full puzzle, thinking off | 33.3% | 0 |

_*complete-case, one censored row each_

**Key contrasts (sign test):**
- A vs F: +58.3 percentage points (p = 0.016) — puzzle is not just a length effect
- A vs D: +41.7 pp (p = 0.063) — puzzle amplifies above bare target
- A vs E: +50.0 pp (p = 0.031) — thinking is load-bearing for the attack

**Stage 4.8** — Independent stochastic replication (temperature=0.7, 5 seeds each):
A=60%, D=50%, F=40% — ordering preserved; gaps smaller under stochastic sampling.

---

## 3. New Onset/Timing Analysis (Provisional Heuristic)

To address "when does the model first engage with the harmful target?"

**Method:** Keyword-overlap proxy on thinking traces. No LLM annotation (blocked by safety filters).

**Preliminary finding:** 92/94 examples show onset in early (0–33%) portion of trace.
**Caveat:** This likely reflects keyword over-extraction — too many terms appear early.
Manual validation of 20+ examples is the immediate next step before strong claims.

**What to do:** Review `manual_onset_review_packet.csv` (66 redacted examples) to validate
whether early-onset classification is genuine or artifactual.

---

## 4. Stage 4.8 Extension Status

Current: 3 matched-outcome cells (need ≥4 for behavior-conditioned direction extraction).
Extension plan: Goals 0 and 2, seeds 106–115, 60 additional generations.
Manifest created at: `outputs/stage4_8/runs/run_array_extension_20260611_143945/`
**Ready to submit with:** `sbatch slurm_scripts/stage4_8_repeated_generations_array.slurm`
ETA: 4–8 hours of cluster time.

---

## 5. Why RL Is Not Yet the Right Immediate Experiment

| Pre-condition | Status |
|--------------|--------|
| Primary reward (SR score) defined | ✅ Ready |
| Secondary rewards calibrated | ⚠️ Partial |
| Onset timing validated | ❌ Needs manual annotation |
| Behavior-conditioned direction | ❌ 3/4 matched cells |
| RL training infrastructure | ❌ Not implemented |

The immediate contribution is **defining and validating measurable reward components**
from existing experiments — itself a novel contribution that grounds the RL roadmap.

---

## 6. Proposed Next Decision for Mahmood

**Decision A:** Approve Stage 4.8 extension job submission (60 gens, ~4–8h).

**Decision B:** Allocate time for manual onset annotation (20–50 examples) to validate
the timing hypothesis before making it central to the paper.

**Decision C:** Confirm framing: "Delayed Safety Commitment / Reasoning-Path Hijacking"
as the unified hypothesis connecting CoT Hijacking, Doublespeak, and Safety-before-CoT.

**Key message:**
> The behavioral effect is real and confirmed at scale with a length-matched control.
> The simple refusal-direction mechanism is not the explanation.
> The new hypothesis (delayed safety commitment) is grounded in three related papers.
> The next best experiment is measuring onset/timing, then controlled difficulty or
> constrained RL — not RL without the mechanistic understanding.

---

## 7. AutoInject-Based Optimization POC [NEW]

I inspected the existing AutoInject implementation (GRPO-based RL — genuine policy gradient,
not black-box search) and built a safe adapter for reasoning-model hijacking.

**What was done:**
- Audited AutoInject's GRPO training loop, reward utilities, and evaluation structure
- Built an offline replay POC using existing Stage 4.7/4.8 cells as the candidate pool
- Treated A/D/F/E structural wrappers as candidate actions
- Compared 8 policies: always-A/D/F/E, empirical best, AutoInject-style greedy, ε-greedy, UCB1
- Ran reward sensitivity grid (64 combinations of α_onset, α_thinking, β_censoring)

**Key result:** All policies consistently select Condition A. This is robust across all
reward weight combinations tested. This is a feasibility bridge toward the original goal:
adapting AutoInject for reasoning-model hijacking.

**What this is NOT:**
- Not a real online optimization
- Not proof that RL improves ASR
- Does not generate harmful content
- L22 projection is used only as a diagnostic term, not a primary reward

**Next decision for Mahmood:** Approve a constrained online AutoInject-style run (~40 evals,
same research prompts, actions = {A,D,F,E}, reward = sr_success).

See: `AUTOINJECT_POC_MEETING_SUMMARY.md`, `autoinject_poc/` directory.
