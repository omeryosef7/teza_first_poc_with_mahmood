# Mid-session sanity check — 2026-08-17

Requested explicitly. Parts 1–2 are written from session state; parts 3–4 are being verified by an
independent 12-agent sweep (smoke tests + confound checks) and are filled in from its findings, not from
my assumptions. Part 5 is the honest issues list.

---

## 1. Current progress

### Code — `src/boombness/`, 27 tracked files, all committed
| file | role |
|---|---|
| `common.py` | `RunDir` output contract (config/metadata/results/summary/DONE + house RUNMETA), `FailureLedger` (`finish()` refuses without it), `note_bank()` content hashing |
| `prompt_families.py` | the 2×2 bank generator; `check_alignment`, `prompt_sha16`, `bank_content_sha16` |
| `signals.py` | `logit_lens`, `estimate_directions`, `readout_id_pair`, random/orthogonal controls |
| `extract_boombness.py` | `forward_hidden` (hook-based, last-layer tie fix), `stage_fit`/`stage_score`, `resolve_occurrences`, `--position {codeword_last,last,following}` |
| `score_behavior.py` | forward readouts (semantic / comprehension) + generation; `--intervene` (now multi-spec via `+`), `--enable-thinking` |
| `judge_boombness.py` | StrongReject rubric judge; refuses to start without an API key |
| `aggressive_patching.py` | §5 transplant / additive arms, gap-unit dosing |
| `surgical_knockout.py` | §10 attention-edge arms incl. the edge-matched pair |
| `dominance.py` | HF-eager port of the edge-attribution method |
| `coherence_gate.py` | degeneracy gate (now condition/prompt-scoped, reports `n_dropped_short`) |
| `probes.py` | §6.3 probes incl. the new surface-matched regimes `d5`/`d6` |
| `refusalness.py` | refusal-direction readout; `--position`, fail-fast on systematic failure |
| `role_probes.py` | Role-Confusion port (machinery only — no probe fitted; disclosed) |
| `analyze_g2.py` | G2 + clustered inference + per-domain + mediation; **refuses** on position mismatch |
| `analyze_position.py` | **new** — the predictor×position 2×2 with provenance; **refuses** on unverifiable readout position |
| `analyze_g1_g3.py` | G1 spans + paired bootstrap; G3 arms + movability whitelist |
| `analyze_steering.py` | G4 arms, paired contrasts, suppression routes, random-control band |
| `analyze_role.py`, `reanalyze_corrected.py`, `tokenization_audit.py`, `compare_runs.py`, `demo_pools.py`, `diagnose_*.py`, `make_manual_review.py`, `analyze_boombness.py`, `slurm/run_boombness.sh` | supporting |

### Docs / reports / data
`docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md` (the plan, verbatim) ·
`docs/BOOMBNESS_SPRINT_PROGRESS.md` (phase board, gate table, 5 retractions, 8 corrections, 6 audits) ·
`reports/boombness_objective_sprint_report.md` (§15 main report, all 18 required contents) ·
`reports/boombness_objective_sprint_short_update.md` (rev 5) ·
`outputs/boombness/aggressive_patching/*/decision_gate.md` (§5.4, added today) ·
`notes/{interp_jailbreak_best_practices,boombness_reuse_inventory,three_codebase_adoption}.md` ·
`data/boombness_prompts/boombness_prompt_bank.jsonl` (2352 rows, sha `71bea179345ed118`) ·
10 committed analysis artifacts under `outputs/boombness/*.json`.

### Which phase
Plan §17's phases 1–6 are complete. **We are past the plan's linear path and in a
verification-and-gap-closing phase**, driven by two independent audits that found requirements the
board had marked done. Specifically in flight: **§10.4's missing arms** and **§14's second-model
replication**.

### Runnable now
Every script runs; every gate-bearing number comes from a committed script; three scripts carry
deliberate refusals (position mismatch, unverifiable readout position, missing coherence assessment).

### Incomplete, with status
| item | state |
|---|---|
| §10.4 arm B ASR (`projout_beh`, job 762169) | running — comprehension already known preserved |
| §10.4 arms C/F **ASR** | **launched** (762187/762188); comprehension already verified intact — arm C +0.207 (p=0.0012), arm F +0.863 (p=0.0020) |
| §14 Qwen3 ASR replication | generation done (960, thinking-off verified); **judge running** |
| §10.4 arms D/E | not run |
| Userness/CoTness probes (§11) | machinery ported, **never fitted** — `role_style` used as a disclosed proxy |
| 3-predictor regression ASR ~ boombness + role + refusalness (§9) | **DONE** (`analyze_g9.py`) — 2-predictor model fitted (joint R²=0.250, both p<1e-4); **role dropped as unidentifiable** (collinear with `bank_block`, zero family overlap with `plain`) |
| comprehension by `n_examples` (§8) | not aggregated |
| `probe_boombness` in the §6.4 three-way metric comparison | absent |
| model/tokenizer **revision** pinning | never recorded (see Risks) |

---

## 2. Alignment with the research goal — explicit confirmation

| target | still targeted? | evidence / caveat |
|---|---|---|
| **Aligned direct vs natural Doublespeak prompts** | **YES** | The 2×2 is the sprint's core contribution; it exists precisely because the original contrast was confounded. Quantified: the naive direction inflates ~2× (replicated on Qwen3, median 1.74). ⚠ Alignment is verified for the *exact-swap invariant* on 216 of 912 families; the B-vs-C structural comparison is being re-checked by the sweep. |
| **Token-level Boombness per `carrot` occurrence** | **YES** | Every occurrence is a row (`occurrence_index`, `is_final_occurrence`, `token_pos`); §7 is reported separately from prompt-level. Result: the **final** occurrence is *lower* on the axis, and the benign control shows the same → positional, not semantic. Replicated on Qwen3. |
| **Prompt-level Boombness vs ASR correlation** | **YES** | ρ=+0.307 at L12, +0.302 norm-partialled, n=234, p<5e-4 (within-domain permutation), 6/6 domains positive (two near-null). |
| **Aggressive `carrot → bomb` patching sanity checks** | **YES** | §5 transplant/additive arms with a self-swap no-op control; `decision_gate.md` now written and answers 2 of its 8 questions as *not measured*. |
| **Surgical knockout / patching** | **YES** | §10 attention-edge arms plus the edge-matched pair that **corrected my own depth claim**; §10.4 arms B/C/F now runnable after two code gaps were fixed. |
| **Eventual GCG objective extraction** | **NO — deliberately not built, and that is the finding** | §12 is conditional on the gates; G4 returned a directional null (both signs suppress ASR; only +0.25 clears a 4-draw random band, via refusal). Documented negative. ⚠ **This is now under active re-test**: arm F (add Boombness + remove refusalness) checks whether that null is a *refusal ceiling effect*. If it is, §12 reopens. |

---

## 3. Bug checks

*Filled in from the independent sweep — see the section appended below once it lands. Not written from
assumption: the last two audits each found requirements this board had marked DONE.*

## 4. Scientific confounds

*Same — verified by the sweep, covering: B-vs-C structural alignment; domain pooling; token- vs
prompt-level separation; probe lexical triviality; and whether any ASR claim is still stated causally
without the comprehension caveat.*

## 5. Known Issues / Risks

**Ranked by whether a collaborator could be misled.**

1. **The −0.25 arm's ASR suppression is partly CONFUSION, not mechanism.** Today's §2.6 control showed
   it degrades comprehension to −0.088 (below zero: the model prefers "literal"), 50% still coded vs 68%
   baseline, p=0.040. Anywhere that arm is described as "removing concept-ness reduces attack success"
   is wrong. The reports have been updated; anyone quoting an earlier revision has this error.
2. **§18 = B may be a refusal ceiling effect.** Never tested until now. Arm F is the test. Until it
   returns, "Boombness is mechanistic but not causal" rests on an untested assumption that refusal is
   not masking a Boombness effect.
3. **The position finding has an estimation-quality confound (C8) — now DOWNGRADED, not withdrawn.**
   The direction is 13× (Llama) / 41× (Qwen3) better *separated* at the codeword token, so "carries
   more signal" and "is better estimated" are not separated by the design. L31 is unaffected (gaps
   converge to 1.1×). **§9 evidence against it:** refusalness, which is fitted for a last-token
   readout, should by that story do *better* at `last` — instead it is a flat null there (p=0.99)
   despite having the largest variance of any cell (sd 0.954). Partial caveat: 41% of that variance
   is between-`n_examples`, so it is not all prompt-specific signal.
4. **Reproducibility is weaker than the report implied.** Every run recorded `git_dirty = True`, so the
   recorded commit does not pin the code that ran; **model and tokenizer revisions were never
   recorded**; 53 of 68 finished runs predate `bank_content_sha16` and cannot be tied to a bank version
   by artifact alone (the bank was regenerated 1464 → 1752 → 2352). Now disclosed in both reports.
5. **The mid-layer negative band does not generalise.** Absent in behavioural prompts, fails the
   artifact's own Holm field, and the sign flips on Qwen3. Two independent reasons; narrowed in both
   reports.
6. **No fitted role probe.** §11's conclusions rest on `role_style` as a categorical proxy. The
   ⛔ The "tight null" (F=0.175, p=0.972) is **RETRACTED (#6)** — wrong error term. The paired within-stem
   test gives F(5,355)=20.30, p=8.1e-18: role framing **does** move Boombness, reliably but by ~4% of the
   grand mean. And it is still a claim about a *proxy*, since no role probe was ever fitted.
7. **G1 is a pilot and its headline is arm-selected.** n=8 families from **2 domains**; the +84% is one
   arm of ~130, and the all-layer variant of the same transplant goes the *opposite* way (−0.76).
8. **"Refusalness at the codeword token" is off-label.** Fitted for a last-token readout; its condition
   ordering degrades badly there (harmful−benign gap collapses ~16×). This is why outcome C is not
   claimed.
9. **Four bugs of one shape, so assume a fifth exists.** A flag or check threaded into one of two paths
   that must agree: `stage_score` missing `position`; `readout_position` written but never read;
   `dc.generate` missing `enable_thinking`; and a guard that validated the already-correct path. Three
   separate guards were also found never to have executed at all.
10. **Qwen3 ASR replication is not yet judged**, so §14's behavioural half is unknown; only the
    representational findings have replicated so far.
