# RAH3 — Track B: power, bank, and the baseline screen

**Verdict: TRACK B BLOCKED BY MATERIAL AND POWER.** No confirmatory matrix was costed or launched;
the ~20 GPU-hour gate **cannot be reached** because the population that would justify it does not
exist yet.

Every number was recomputed at current HEAD by importing `scripts/rah_power_trackb.py` and running
its own simulator (`paired_test_noise_sensitivity.simulate`), **not** read out of the handoff.

---

## 1. ⚠ The sprint's premise was partly mistaken — corrected before acting on it

The charter asked to *"build a NEW bank with approximately 38 independent domains"* and warned
against manufacturing 38 by renaming the old 20. **The 38-domain material already exists and has
already been screened:**

* `demo_pools.py:60` `DOMAINS` holds **38** entries (its section comment still reads `# Six domains.`);
* `data/boombness_prompts/demo_pools_29dom.json` holds **152 pools over 38 distinct domains** —
  ⚠ the filename and `scripts/gen_pools_29dom.sh` say **29**; **the data wins**;
* all four screened cells already carry `n_domains = 38`.

**Building another 38-domain bank would rebuild something that exists and would not move the gate.**

## 2. The screening table — every cell, failures included

| cell | baseline ASR | domains | rows/domain | k_informative | frac_at_cap | qualifies | reason |
|---|---|---|---|---|---|---|---|
| **Llama × carrot_bomb** | **0.16447** | 38 | **[4]** | 20 | `None` | **yes** | QUALIFIES |
| Llama × ticket_knife | 0.09211 | 38 | [4] | 10 | `None` | no | ASR 0.0921 < 0.1375 |
| Qwen3 × carrot_bomb | 0.07237 | 38 | [4] | 8 | `None` | no | ASR 0.0724 < 0.1375 |
| Qwen3 × ticket_knife | 0.03289 | 38 | [4] | 3 | `None` | no | ASR 0.0329 < 0.1375; k_inf 3 < 6 |

⚠ **The one qualifying cell is the DISCOVERY pair, on one model.** Using it would be the forbidden
move: *choose the pair where the effect was found.*

## 3. Power, recomputed

`p0 = 0.16447`, `flip_for_asr(p0) = 0.078234`, `SIM_REPS = 4000`, `alpha = 0.05`, target power 0.80.

| design k × m | n | ICC 0.09 → MDE abs / **rel** | ICC 0.19 → MDE abs / **rel** |
|---|---|---|---|
| **38 × 4 — the material that EXISTS** | 152 | 0.16095 / **0.9786** | **NONE** |
| 38 × 8 | 304 | 0.13148 / 0.7994 | 0.15520 / 0.9436 |
| **38 × 16 — the handoff's design** | 608 | 0.11347 / **0.6899** | 0.14065 / **0.8552** |
| 38 × 24 | 912 | 0.10708 / 0.6511 | 0.13709 / 0.8335 |
| 20 × 4 — the RBD arm shape | 80 | **NONE** | **NONE** |

⚠ **`NONE` means NOT DETECTABLE AT ALL — including a 100 % wipeout.** It does not mean "small".

1. **At the material that exists, nothing is resolvable.** 38 × 4 needs a **97.9 %** relative
   reduction at the optimistic ICC and detects **nothing** at the pessimistic one.
2. **The handoff's ≈ 0.70 reproduces exactly — and only at ICC 0.09.** 0.6899 vs **0.8552**.
3. **RAH's "no more 80-family confirmations" is confirmed independently:** 20 × 4 returns `NONE` at
   both ICCs.

**Reaching the handoff's design requires 608 rows where 152 exist — 12 more per domain — on a pair
that has not yet cleared a baseline screen.**

## 4. Three defects found in the power/screening path

**`RAH3-C-005` — the judge-noise model is NON-MONOTONIC.** Its own docstring,
`RESEARCH_HANDOFF.md:378` and the sprint charter all say the flip rate **rises** with baseline ASR.
`MEASURED_FLIP_BY_ASR` **falls twice**: 0.0500→0.0625 gives 0.0369→**0.0289** (−22 %), and
0.2708→0.3125 gives 0.0851→**0.0658** (−23 %). The *mechanism* is well argued and the repo's own
`FLIP_RATE_BY_CONFIDENCE` supports it; **"rises" is simply not what the eight measured points do.**
⚠ And `flip_for_asr` clamps above ASR 0.3125 to **0.0658 — below the 0.0851 maximum measured** —
anti-conservative at exactly the end where a high-headroom population would be argued for.

**`RAH3-C-006` — `ICC = 0.09` has no estimator anywhere in the repository.** A grep across
`scripts/`, `doublespeak_causality/` and `src/boombness/`, excluding the power module, returns
nothing. ⚠ **The single most load-bearing input to the GO/NO-GO is an assumption with no
measurement** — and it is the difference between 0.6899 and 0.8552, and between 0.9786 and
undetectable. **Never quote 0.70 without 0.86 beside it.**

**`RAH3-C-007` — the truncation gate is published and enforced by nothing.**
`max_frac_at_cap = 0.02` appears in `rah_screen_table.py`'s `thresholds` block; `frac_cap = None` is
hardcoded at `:91`, the path computed beside it is never used, and no qualification branch
references it. ⚠ **A cell with 100 % truncation would still report `qualifies: true`.** Same defect
class as `RAH3-C-003`'s dead `mass_gate` — **a threshold published in an artifact and enforced by
nothing, found twice in one sprint, in two different files.** Given the cap rule, a screen that
cannot see truncation cannot certify a baseline.

## 5. ⚠ k = 38 is an upper bound on independent clusters

Three of the 38 (`news_report`, `game_manual`, `instructional`) are **register/genre**, not settings
— against `demo_pools.py:57-58`'s own rule that presentation wrappers belong on `role_style`. The
other 35 are largely workplace variants from near-identical templates, and all 152 pools came from
**one model at one un-offset base seed**. **The count entering `deff` is an upper bound**, which
pushes the true ICC toward the pessimistic column. ⚠ Do not quote k = 38 as 38 independent
experimental clusters.

## 6. What an unblock would require — so the cost is explicit and the decision is the user's

1. a new bomb-class lexical pair clearing a **baseline-only** screen at ≥ 0.1375 on **non-discovery**
   material (`RAH3-PR-003` would register it; screening must be structurally incapable of loading an
   intervention spec);
2. **608 rows** across the existing 38 domains — 16/domain, not 4;
3. a **measured** ICC rather than an assumed one;
4. `RAH3-C-007`'s truncation gate made live before any screen is trusted.

⚠ **None of that is behavioural-matrix compute.** It is bank generation plus a baseline screen, and
it is a **separate authorisation** from the ~20 GPU-hour matrix, which remains **NOT REACHED**.

⚠ Per §62 this sprint did **not** use the highest-but-inadequate pair, reduce required power, pool
domains, reuse development rows, or add an intervention arm to see what happens.
