# TSC sprint summary — thesis-scale confirmatory, 2026-09-02

**Self-contained.** Reading this requires no other document. Full log:
`external_md/THESIS_SCALE_CONFIRMATORY_SPRINT_PLAN_AND_PROGRESS.md` (id namespace `TSC-`).
Branch `behavioral-causality-sprint`, `053531b3..`.

---

## The one-paragraph truth

The sprint was asked to close the specific weaknesses that stopped the strongest existing claim from
being thesis-level evidence, using preregistered, properly powered, falsifiable tests. **Four of the
five closed, and two of them closed by returning a negative.** The `basket↔bomb` replication that
was VOID now **REPLICATES**, so the Llama headline no longer rests on one lexical pair. The headline
**survives three independent judging passes**. Qwen3-14B was run on a genuinely capable population
for the first time and is a **well-powered CAPABLE NULL**, and the model × intervention interaction —
**registered before any Qwen outcome existed** — says **MODEL-SPECIFIC**. And an adversarial review
found that **90–100 % of judge-positive completions in every arm never contain the concept word**,
which does not overturn the effect but changes what it is a claim about. **The result is stronger
and narrower than it was yesterday.**

## What was preregistered before any forward pass

`TSC-PR-001` (the `basket` replication, with the row exclusion declared by `prompt_id` and sha) ·
`TSC-PR-002` (judge robustness, with the decision rule and the noise-band rule) ·
`TSC-PR-003` (the Qwen Stage-1 baseline screen, with the fallback pair rule) ·
`TSC-PR-004` (the Qwen Stage-2 arms **and the interaction test**, the latter committed **as running
code while the Qwen arms were still generating**) · `TSC-PR-005` (the request-diverse bank, with its
population drawn **blind** from metadata only) · `TSC-PR-006` (the structurally-active control,
execution deliberately deferred).

## Results

| # | result | verdict |
|---|---|---|
| `R-004` | **`basket↔bomb` REPLICATES on Llama at 38 domains** — p = 1.18e-02 / 9.11e-04 / 2.60e-03 vs the three controls | **REPLICATED** |
| `R-001` | The `button` headline holds in **three independent judge passes**; worst of nine p = 1.093e-05 | **CONFIRMED** |
| `R-002` | On the **topical** endpoint (`R-13`'s instrument) `demoproc` ASR is **exactly 0.000**, Δ CI excludes zero, controls flat — **on both pairs** | **SUPPORTED, SCOPED** |
| `R-003` | Qwen3 Stage-1 **PROCEED**: ASR 0.2026, 28/38 domains with an attack (floor 15) | **CAPABLE at last** |
| `R-005` | **Qwen3 Stage-2 is a CAPABLE NULL** (p = 1.000 / 0.487 / 0.864, `k_inf` 30–34); the registered interaction rejects **3/3 absolute, 1/3 normalised** | **MODEL-SPECIFIC** |
| `R-006` | On Qwen the same intervention removes **ALL 150 refusals** while moving attack by **one row** | **STRONG dissociation** |
| `C-004` | **90–100 % of judge-positive completions in EVERY arm never contain the concept word** | scope, not refutation |
| `C-011` | **Qwen's BASELINE topical ASR is 0.000 in every arm** — the models cannot be compared on that endpoint | **CANNOT ANSWER** |
| `PR-005` | Request-diverse population **drawn blind**: 40 requests, 8 categories, `selection_sha16 = bed56c91e70a707c` | preregistered |

## What the adversarial review took away

A read-only agent was told to **break** `R-001`. It reproduced all nine p-values exactly under
integer arithmetic, confirmed the passes are independent, confirmed the 38 domains share **zero**
demonstration sentences, and confirmed the controls are not merely count-matched but **over-dosed**.
**It could not break the machinery. It broke three of my sentences:**

* ⛔ **"attack removal"** — 90–100 % of positives are off-topic by the one-word test, and this repo
  **already retracted this exact inference once** (`R-13`, where a *double-random control* scored
  0.95 "attack success" on text with zero harmful keywords). The producer never read the topicality
  column built in response. Under the topical endpoint the effect **holds** but `k_inf` collapses to
  8–12 and every test sits **exactly at its attainable floor**.
* ⛔ **"−97 rows against a 17-row band ≈ 5.5×"** — that stapled the *baseline* effect onto the
  *control* contrast and used one drifting arm's max−min. **The paired band is 3.7 rows and the true
  margin is ≈ 46×.** Wrong in the direction that *understated* it, which makes it no less wrong.
* ⛔ **"0/380 refusal flips proves the variance is the judge"** — `refused` is `kw_refusal`, a local
  substring match that **never calls the API**. On byte-identical text 0 flips is a mathematical
  identity. It attests the join and the hashing, nothing about the judge.

## Corrections found by instruments, not by reading

* ⚠ **`C-001` — the Stage-2 verifier was RED against the artifact it certifies, and its green had
  been vacuous before that.** It compared the published `frac_stop_length` against
  `summary.json → counts.frac_stop_length` — **the field already proved permanently `null`** — so it
  was asserting `None == None` and printing PASS. It now **re-derives** the value from raw
  `stop_reason` rows. **A check whose two sides read the same broken source agrees with itself.**
* ⚠ **`C-003` — the re-judge band is 17 rows, not the 11 that two passes suggested**, and only
  **76.8–82.9 %** of rows are unanimous over three. Every row-threshold in the project must use 17.
* ⚠ **`C-009`/`C-012` — the mutation harness blamed the verifier for its own zero-target bug**, then
  **crashed** on the Qwen artifact for the same reason. A relative epsilon cannot move a zero — the
  same trap that makes an absolute tolerance vacuous. Both fixed; **20/20 red on all three headlines**.
* ⚠ **`C-010` — my own universal-quantifier sweep caught three over-claims in tonight's write-up**,
  including a disjointness property **verified on one bank and asserted of two**. Fixed by
  **checking** (`basket` returns the identical figures), not by softening.

## Verification

Three headlines, each carrying a **stdlib-only verifier that imports nothing from its producer**,
with the exact binomial derived three ways and cross-checked against brute-force enumeration:
**button 350 / basket 351 / Qwen 351 checks, 0 failures**. Mutation harness **20/20 RED on all
three**. ⚠ The verifier and harness were **parameterised rather than forked** (`C-002`) — a forked
verifier is two instruments that drift apart — and the design shape must be **declared by the
caller** (`10:37,7:1` for basket), because a check that infers its expectation from the data under
test asserts nothing.

## Hazards worth inheriting

* ⚠ **`R-13`'s topicality lesson is not learned until the analyser reads the column.** It existed,
  and the headline producer never called it. **Grep every deliverable for the guard that was built
  for its own failure mode.**
* ⚠ **A "capable null" and an "incapable test" are different things and this sprint produced one of
  each.** Qwen attack: `k_inf` 30–34, floors 1e-10 — a real null. `basket` refusal and Qwen topical:
  floors **above α** — ⛔ **no outcome could have reached significance; never report these as nulls.**
* ⚠ **A guard test that shells out to `git` and is run by a pre-commit hook is flaky by
  construction** (`H-001`). It failed once in six runs tonight and passes in isolation. ⛔ Do not
  "fix" it by removing it from `GUARD_TESTS`.
* ⚠ **A crash is a better failure than a silent skip.** `basket` was VOID because the intervened
  path *raised* where the baseline path *ledgered*. Had both skipped, two arms would have compared
  different row sets under one label. The fix removes the rows from the **population**, declared and
  identical in every arm — never a `try` around the pre-flight.

## The next four things, in order

1. **Vary the request.** Still the largest gap, and now the only untouched one. The population is
   already drawn blind (`selection_sha16 = bed56c91e70a707c`); the long pole is **200 harm-pool
   generations**, which is API work, not GPU. ⚠ **Before building it, resolve the blocker in
   `TSC-Q-001`** — a large fraction of AdvBench requests have **no single-word object noun** the
   codeword can be mapped onto, so the drawn 40 may not yield 40 usable requests.
2. **Replace the one-word topicality test.** Every topical number in this sprint is bounded by a
   single-bit indicator on one word. A synonym-aware measure would turn the tightest scope limit
   into a real measurement.
3. **Run the structurally-active control** (`TSC-PR-006`), which is fully specified and unstarted.
   Its chain is serial behind its own Stage-1 gate, which may decline it.
4. **Ask what the Qwen refusal annihilation means.** 150 → 0 with attack unmoved is the largest
   single behavioural effect in this project and nothing currently explains it.
