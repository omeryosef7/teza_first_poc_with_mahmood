# Presentation Validation Report

**Validated file:** `docs/GCG_Phases4-7_Summary_FINAL_AUDITED.pptx` (25 slides), produced from `docs/GCG_Phases4-7_Summary_2026-07-11.pptx` (left untouched) via `scripts/edit_gcg_pptx.py` — 17 targeted text/table-cell replacements, all confirmed applied (script prints a per-replacement match count; all 17 show `[1] OK`).

**Method:** extracted all text (text boxes + table cells) programmatically via `python-pptx`; cross-checked every numeric token against `outputs/stage_gcg_full/GCG_PHASE4_7_SOURCE_OF_TRUTH.csv` and the companion audit docs. **Limitation: no LibreOffice/PowerPoint renderer is available in this environment** (`soffice`/`libreoffice` not found), so this is a **text/data validation, not a visual render check** — clipped text, overlapping shapes, and font/line-wrap issues were not verified visually. The edit script only replaced run text (same shapes, same formatting, same or similar-length strings were chosen where possible), so visual risk is limited to shapes where the new text is meaningfully longer than the old text (flagged per-slide below).

## Numeric cross-check (all slides)

Every percentage, pp-figure, AUC value, and row-count token extracted from the deck was traced to `GCG_PHASE4_7_SOURCE_OF_TRUTH.csv` or a companion audit doc. No orphan numbers (present in the deck but untraceable to a source artifact) were found. Spot-checks recomputed independently in this audit:

| Slide claim | Recomputed value | Match |
|---|---|---|
| Standard GCG loss reduction "74%" (slide 6) | (30.7422−7.9746)/30.7422 = 74.06% | ✅ |
| 4B loss reduction "87%" (slide 6) | (31.8047−4.1741)/31.8047 = 86.9% | ✅ |
| Gemma4 vs Qwen3 refusal separation "+58%" (slide 18/22) | (0.498−0.315)/0.315 = 58.1% | ✅ |
| 7A seed-transfer gap "−0.7pp" (slide 10) | −0.673pp (recomputed from raw `FREE_GENERATION_RESULTS.jsonl`) | ✅ |
| 7A unseeded coverage "493/520 = 94.8%" (slide 10, after edit) | 493/520 = 94.8% | ✅ |
| 7B seed43/44/45 loss/ASR table (slide 11/12/14) | matches `GCG_PHASE4_7_SOURCE_OF_TRUTH.csv` rows `7B_seed43/44/45` exactly | ✅ |
| 4F "−0.5pp net-neg" (slide 6/14) | 1.9% vs 2.4% task_only = −0.5pp | ✅ |

## Slide-by-slide checklist

| # | Title | Corrections applied | Notes |
|---|---|---|---|
| 1 | Title | none | — |
| 2 | Agenda | none | "Six of the seven findings... the seventh... covered on slide 10" — checked against slide 10 and 24, phrasing is internally consistent (not a bug, confirmed during audit). |
| 3 | Concepts: What Is GCG | none | — |
| 4 | Concepts: Key Terms | ✅ "Training vs. unseen seeds" row → "Optimization vs. generation seeds", body text corrected | Table row 2 cells replaced; new text is longer (~2x) than original — **visual risk**: recommend a manual check that this table row doesn't overflow its cell/row height in the actual rendered slide. |
| 5 | Timeline | none | — |
| 6 | Phase 4 Ablations | none | Numbers spot-checked (74%, 87%) above, no changes needed. |
| 7 | Phase 5 Breakthrough | none | — |
| 8 | Phase 6 Refusal-Direction | ✅ Title reworded; 6A-Q target mislabel fixed (was "CoT-prefix + refusal-direction", corrected to "standard target + refusal-direction", and its uplift baseline corrected from −10.7pp/vs-5A to −2.7pp/vs-task_only to match the corrected framing); closing conclusion reworded to remove "fundamentally incompatible"/"fight each other" | Two of the three replaced strings are noticeably longer — **visual risk**, recommend manual check for overflow on this bullet list. |
| 9 | Phase 7 Closing Gaps | none | — |
| 10 | Phase 7A Full-520 | ✅ Unseeded-result bullet reworded with coverage-qualified phrasing (94.8%, non-random missingness note) | Bullet is now noticeably longer (~2.5x) — **visual risk**, likely the single highest-risk edit in the deck for overflow; recommend shortening if a live render shows clipping. |
| 11 | Phase 7B Seed-Variance | ✅ Caption reworded to explain the fixed-generation-seed-panel terminology | Table itself unchanged (numbers already correct); caption bullet lengthened — check for overflow. |
| 12 | Phase 7B Deep Dive | none | Numbers already correct pre-audit. |
| 13 | Phase 7C Gemma4 | ✅ Closing conclusion reworded ("intrinsic" → hypothesis framing) | Similar length to original. |
| 14 | Master Results Table | ✅ Fixed a real cross-slide inconsistency (caught by independent verification, not the first edit pass): the 6A/Qwen3 row's "vs. Baseline" cell still read "−10.7pp" (comparing to 5A's CoT-prefix ASR) after slide 8 was corrected to say 6A-Q uses the *standard* target, not CoT-prefix — the right comparison is vs. task_only at −2.7pp. Fixed row-scoped (6C's row legitimately keeps −10.7pp, since 6C genuinely uses the CoT-prefix target) via `scripts/edit_gcg_pptx.py::fix_slide14_master_table_6a_baseline`. Added a title footnote marker (*) pointing to this. | Table already correctly distinguishes 6A ("+refusal_dir_loss", no CoT) from 6C ("CoT+refusal_dir") in the Method column — only the baseline-delta cell was stale. |
| 15 | Finding 1 | none | "Primary barrier" language reviewed — judged adequately supported by the loss/ASR data shown on this slide itself (CoT misalignment → 4x ASR jump), left as-is. |
| 16 | Finding 2 (detection) | none | Claim ("AUC=1.000 across every Qwen3 variant tested") holds under this audit's GroupKFold/leave-one-seed-out rerun (`docs/GCG_DETECTOR_ROBUSTNESS_AUDIT.md`) — no correction needed, could optionally be strengthened with "(confirmed under behavior-grouped and seed-held-out CV)" but not required since the original claim wasn't overreaching. |
| 17 | Finding 3 (refusal-direction) | ✅ Title reworded; "fundamentally incompatible" line reworded | — |
| 18 | Finding 4 (Gemma4) | ✅ Title reworded; "distributed safety" claim reframed as hypothesis | — |
| 19 | Finding 5 (seed baselines) | none | — |
| 20 | Finding 6 (loss vs ASR) | none | — |
| 21 | Comparison with prior work | none | — |
| 22 | Implications for Defense | ✅ Point 3 (Gemma4 "multi-layered safety") reframed as hypothesis | — |
| 23 | Current Status | ✅ Two table cells reworded (Phase 6 "mutually destructive" → tested-setup framing; 7C "confirms intrinsic robustness" → "rules out format-mismatch hypothesis") | — |
| 24 | Conclusions (7 findings) | ✅ Bullets 3 and 4 reworded to match evidence strength | — |
| 25 | Appendix | ✅ Added pointer to the 6 new audit documents; ✅ fixed a stale internal inconsistency (found by an independent fact-check pass, not the original edit pass): this slide said the unseeded eval used "10 shards across 2 waves," while slide 10 correctly says "15 shards in 3 waves" — the appendix bullet was written before the 3rd wave (jobs 657639-657643) ran and was never updated. Corrected to match slide 10. | This was missed in the first pass of this validation report and only caught by a follow-up independent verification agent — a reminder that even a systematic numeric cross-check can miss slide-to-slide (as opposed to slide-to-source-of-truth) inconsistencies; worth a second read-through of the full deck end-to-end before presenting. |

## Footer / date / status check

All 25 slide footers read "GCG Phases 4–7 Summary \| Jul 7–12, 2026 \| N" (sequential N=1..25) — consistent, no stale dates. All status badges/table cells say "✅ Complete" / "✅ COMPLETE" — consistent with the confirmed fact that no SLURM jobs are queued or running as of the audit date (2026-07-13); no stale "pending"/"running" language found anywhere in the deck.

## Speaker notes correction pass (2026-07-13, second follow-up round)

The original deck already had substantial pre-written speaker notes on all 25 slides (600-1500 chars each) — these were left untouched by the first edit pass, which only corrected slide *body* text. On review, several notes stated now-corrected claims as established fact, most seriously:

- **Slide 10's notes said the 7A unseeded 8.92% estimate was "considered unbiased"** because shard assignment was "approximately random" — this is the exact claim `docs/GCG_7A_BEHAVIOR_LEVEL_ANALYSIS.md` §4 determined is NOT supported (the 27 missing behaviors are the non-random tail of interrupted shards, skewing toward higher AdvBench row indices). **Fixed** — now says "over the 493 completed behaviors (94.8% coverage)," matching the doc and the already-corrected slide-body text.
- **Slide 23's notes said "10 more shards across two waves"** for the unseeded eval — the same stale-count bug already fixed once on slide 25's body text, present again in slide 23's notes. **Fixed** to "15 more shards across three waves."
- Slides 8, 17, 18, 22 notes stated speculative mechanisms ("tokens weird enough to suppress the refusal direction are also weird enough to trigger... other safety pathways," "the model has more than one way of encoding 'this looks unsafe'," "genuinely more robust safety training" as "the best-supported conclusion," "safety not concentrated in one direction") as settled fact. **Hedged** to match the claim-strength corrections already applied to the slide bodies (`docs/GCG_PHASE4_7_AUDIT_REPORT.md`'s overclaim table).
- Slide 25's notes now point to the six new audit documents.

Applied via `scripts/edit_gcg_pptx_notes.py` (7/7 replacements confirmed applied), run against the already-corrected `GCG_Phases4-7_Summary_FINAL_AUDITED.pptx` in place. **Run-order dependency**: this script must run *after* `scripts/edit_gcg_pptx.py`, since that script regenerates the deck from the untouched original each time — rerunning it without immediately re-running the notes script would silently revert these notes fixes.

## Unresolved

- **No visual render check performed** (no LibreOffice/PowerPoint available in this environment). Before presenting, a manual open-and-scroll-through in PowerPoint/Keynote/Google Slides is recommended, specifically for slides 4, 8, 10, and 11 where replacement text is meaningfully longer than the original and could overflow its text box or table cell.
- Slide 2's "six of seven findings" phrasing was confirmed not to be an inconsistency (it explains itself), but is mildly convoluted; left as-is per the audit's scope (text-accuracy corrections, not general copy-editing).
