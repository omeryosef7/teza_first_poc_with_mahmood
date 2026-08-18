# Mid-session sanity check #2 — 2026-08-18

Requested explicitly, second time this sprint. Parts 1–2 are written from session state. Parts 3–4 are
verified by an independent 8-dimension workflow sweep (each dimension adversarially re-checked) plus the
text-dependent checks that must stay in the main loop, because a subagent reading prompt or generation
text is terminated by the cyber classifier. Part 5 is the honest issues list.

**Headline: this check found a retraction (#9) and a real hole in a guard.** Both are recorded below and
in the progress log, not smoothed over.

---

## 1. Current progress

### New this session
| file | what |
|---|---|
| `src/boombness/retraction_sweep.py` | **new** — makes the "grep every retracted figure across all docs" rule an executable, tested check (paragraph-scoped, deliverables-only, figure **and** claim patterns) |
| `src/boombness/analyze_g9.py` | **new** — §9 three-predictor model; refuses to fit an unidentifiable role term |
| `src/boombness/analyze_g8.py` | **new** — §8 comprehension vs demonstration count; computes `n_effective` and excludes degenerate levels |
| `src/boombness/analyze_g64.py` | **new** — §6.4 three-way metric comparison + its four named deliverables |
| `src/boombness/probes.py` | `--emit-scores`: out-of-fold per-prompt margins, which is what made `probe_boombness` exist as a metric at all |
| `src/boombness/common.py` | `require_done()` now refuses a run whose ledger records **0 successes** (see Part 5, issue 1) |
| `outputs/.../causal_claims.md` | §10.4's mandatory deliverable — did not exist |
| `data/boombness_prompts/role_style_block.jsonl` | 720-row filtered bank, sha16 `71ad78fec42eda71`, for the §11 full-coverage runs |

### Which phase
Past the plan's linear path. Sections **6.4, 8, 9 and 10.4 were closed this session**; §11 was unblocked
and its coverage runs launched. The work is now **gap-closing and verification**, driven by the repeated
finding that plan-mandated deliverables were missing while the board said DONE (three sets so far:
§5.4 `decision_gate.md`, §10.4 `causal_claims.md`, §6.4's three plots + CSV).

### Runnable now
All 30 scripts. Five GPU jobs in flight: 763594/763595 (§10.4 arm D + double-random control),
763891/763892 (§11 full role block), 763924 (re-extract over the current 2352-row bank).

### Incomplete
| item | state |
|---|---|
| §10.4 arm D ASR | generating (321/936 and 573/936); preempted twice, `Restarts=2` |
| §11 full-coverage role runs | 763891 running, 763892 pending |
| §6.4 at full power | **blocked on 763924** — see retraction #9 |
| Userness/CoTness probes (§11) | machinery ported, still never fitted; `role_style` used as a disclosed proxy |
| model/tokenizer **revision** pinning | still never recorded |

---

## 2. Alignment with the research goal — explicit confirmation

| target | still targeted? | evidence |
|---|---|---|
| **Aligned direct vs natural Doublespeak** | **YES — and now measured, not asserted** | Masking the target word out of `full_prompt`, the surface contrasts are **100% identical**: B vs C 288/288, A vs E 288/288. `d_surface = ½[(B−C)+(E−A)]` is therefore built from perfectly matched pairs. The context contrasts differ in text by construction (A vs C 6.7%) — that *is* the manipulation. |
| **Token-level Boombness per `carrot` occurrence** | **YES** | `occurrence_index` / `is_final_occurrence` / `token_pos` per row; §6.4's `metric_by_carrot_occurrence.png` is the token-level view and is kept separate from every prompt-level statistic. |
| **Prompt-level Boombness vs ASR** | **YES** | §9: joint model R²=0.250 on n=234, boombness +0.0889 (p=3.8e-5, perm 0.0065). ⚠ Outcome is the **continuous** StrongReject score, not binary ASR (C11b). |
| **Aggressive `carrot → bomb` patching sanity checks** | **YES** | §5.4 `decision_gate.md` answers 8 questions, 2 of them "not measured". |
| **Surgical knockout / patching** | **YES** | §10.4 arms A–G; **arm D was missing and is now running**; `causal_claims.md` written. |
| **Eventual GCG objective extraction** | **NO — deliberately not built** | §12 stays unbuilt. Arm F raises doublespeak ASR 0.243→0.548, but its specificity **reverses** on explicit harm (+0.000 for F vs +0.417 for the random composition), so no mechanism claim is made. |

---

## 3. Bug checks — run, not assumed

| check | result |
|---|---|
| **prompt generation** | `prompt_families.py` regenerates the bank **byte-identically**: 2352 rows, sha16 `71bea179345ed118` = the committed value. 240 families checked, **0 alignment violations**. |
| **tokenization audit** | The real §2.4 gate (`audit_20260817_013432`) is clean on the current bank: **2352/2352 rows ok, 0 bad, 0 ambiguous**, codeword and concept both single-token, 0 family-alignment violations. |
| **target token spans** | Same run: every occurrence resolved; `n_bad = 0`, `n_ambiguous = 0`. |
| **tensor shapes** | Rep cache: uniform `(32, 4096)` float16 over all entries, 32 blocks for a 32-layer model, d_model 4096, **0 non-finite**. The cache stores `layer_convention` and `position` inside itself, so a consumer cannot misread it. |
| **output dirs / JSON writing** | 116 DONE runs scanned; all carry config/metadata/summary/RUNMETA. **2 defects found — see Part 5 issue 1.** |
| **no silently skipped examples** | The `FailureLedger` *does* record drops (it caught the tokenizer 401 as `tokenizer_load_failed`, and 888 `no_cached_rep`). But the ledger was **not consulted by the consumer** — see Part 5 issue 1. |
| **plots don't crash** | `analyze_g64.py` regenerates all 3 PNGs + CSV cleanly; `analyze_g8`/`g9` rerun clean. |
| **imports / `--help`** | Verified across `src/boombness/` by the independent sweep. Note `numpy`/`torch`/`sklearn` need `conda activate poc_stage2`; the bare login-node python lacks them. |
| **configs load** | Every run's `config.json` parsed in the sweeps above. |

## 4. Scientific confounds — verified

| confound | verdict |
|---|---|
| **direct vs doublespeak structurally aligned** | **PASS, measured.** Masking the target word: B vs C **288/288 identical**, A vs E **288/288**. The surface contrasts that build `d_surface` are perfectly matched. Context contrasts differ in text by construction (A vs C 6.7%) — that is the manipulation, not a confound. |
| **domains not mixed** | **PASS.** 6 domains, balanced. Every current inference clusters on domain: CR1 + within-domain permutation (§2/§9), domain-clustered t(5) (§8), within-domain permutation (§6.4), domain-grouped CV folds (probes). §9 additionally refuses below 3 clusters. |
| **token- vs prompt-level separated** | **PASS.** Prompt-level statistics filter `is_final_occurrence`; the token-level view lives in its own deliverable (`metric_by_carrot_occurrence.png`). §9's two positions were checked to use **identical** 234-prompt sets. |
| **probe not learning lexical identity** | **KNOWN AND HANDLED, with a correction.** d1–d4 hit AUROC 1.000 by token identity — documented in `probes.py` as the stupid-probe problem, which is why surface-matched d5/d6 exist. I verified the cache stores `hs[L+1]`, so probe "layer 0" is **block 0's output, not the embedding**; the embedding is never cached. I also tested and **refuted** my own hypothesis that d5/d6 were separable by position (AUROC from `token_pos` alone = 0.504/0.527, i.e. chance). No PCA leakage (pipeline fits on the train fold only). |
| **ASR reduction not read as causal without comprehension controls** | **PASS, and the control fails in a way that is now stated.** §10.4's `causal_claims.md` explicitly declines the mechanism claim. §8 shows a norm-matched **random** direction perturbs comprehension ~3× more than `d_surface` at every demonstration count, so no §2.6 comprehension result may be attributed to the axis. |

## 5. Known Issues / Risks

**Ranked by whether a collaborator could be misled.**

1. **RETRACTION #9 — §6.4 compared metrics measured on different populations.** `probe_boombness`
   (n=72) was tabled beside `direction_boombness` (n=270) as like-for-like. The CSV recorded both n's;
   my prose ignored them. Cause: the probe's rep cache was built on a **1464-row** bank and the bank is
   now **2352** rows, so 888 rows have no cached rep — and the gap is not random (only `core2x2`
   survives). **Like-for-like on the common 72, no metric survives the `n_examples` control**
   (direction falls to +0.009, p=0.94). `analyze_g64` now defaults to `--common-subset`. Job **763924**
   re-extracts over the current bank to make the comparison possible at full power.
2. **`require_done()` accepted runs that produced nothing.** It returned as soon as `DONE.json` existed,
   never reading the failure ledger beside it. **Two zero-success runs are on disk**, one of them a
   §2.4 *mandatory gate* (0/1, tokenizer 401) that would have passed vacuously. Fixed: it now refuses
   `n_succeeded == 0` and I verified it still accepts every run currently in use. **This is the fifth
   dead-guard and the sixth one-of-two-paths bug this sprint.**
3. **Two runs backing current numbers are on the pre-expansion bank.** Blast radius checked, not
   assumed: `analyze_g2`/`analyze_g9` get **270/270** coverage on the judged population and §8 gets
   **288/288**, so only the probe was short. But directions were fitted on the 1464-row bank.
4. **§9's outcome is the continuous StrongReject score, not binary ASR** (C11b). Anywhere §9 is
   described as "R² of ASR" is wrong.
5. **No fitted role probe.** §11 rests on `role_style` as a proxy. New this session: the role block **is**
   a proper crossed design (identical content, 144/144 cells across 5 styles), so role *is* identifiable
   among styles — but every existing role claim rests on **6 prompts per style per condition**. Coverage
   runs 763891/763892 are in flight.
6. **Preemption debris.** 15 partial run dirs from `killable` preemptions (arm D restarted twice).
   Verified **0 committed artifacts reference any of them**, and `require_done` refuses them.
7. **Arm D coherence is a preview, not a verdict.** It generates at 0.6× the control's rate; on partial
   output it is coherent (uniq 0.619, trigram 0.026), so the slowness is longer-but-healthy text, not
   EOS failure. Must be re-checked on the finished run.
8. **Model/tokenizer revision pinning still absent**, and `git_dirty = True` on runs, so the recorded
   commit does not pin the code that ran. Unchanged from the first sanity check.
