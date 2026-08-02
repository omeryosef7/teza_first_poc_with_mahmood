# Deck provenance — every number, and where it was verified

Verified by a 6-agent pass that opened the artifact JSON and read the producing code.
Paths are relative to `doublespeak_causality/`.

## Slide 2–3 · CoT-Hijacking objective (different project)
| number | artifact | status |
|---|---|---|
| 81.8% (18/22 goals, Qwen3-14B) vs 45.0% (9/20, GCG) | CoT-Hijacking attack run + TROPT baseline report | both real, **not a matched protocol** — slide says so |
| 44 runs, 22 goals (16 with both classes), **24 success / 20 fail** | `phase6_length_identifiability.json`, `docs/MECHANISTIC_DATASET_CARD.md:26` | **corrected** (deck said 18/26 — that is the row-level split of the attack run, not the AUC dataset) |
| AUC 0.904 prefill_last L16 · 0.906 think_content_1 L20 | LOGO CV output | MATCH |
| length-only AUC 0.827; residualized 0.756–0.773; gain CI includes 0 | `phase6_CvsD_confound_bootstrap.csv` | MATCH + strengthened |
| 0/45 sufficiency (α=0 also 0/5) | `steer_pilot__tc1_L20/asr_vs_alpha.csv` | MATCH, floor noted |
| necessity ASR 1.00 at −3σ, n=6 | `steer_attacked_necessity__tc1_L20` | MATCH |
| robustness sweeps L12 / L28, prefill-only, generation-only | steer_* dirs (L8, L24 dirs are **empty**) | **corrected** — deck no longer says "across layers" |
| soft prompt 2/25 → 4/25 | `asr_vs_arm.csv` | MATCH; "projection rose strongly" **dropped** (not in any retained artifact); Fisher p ≈ 0.67 and 8/25 empty answers added |

## Slide 4 · Setup
All rows from `PAPER_REPRODUCTION_NOTES.md`, `ENV_AUDIT.md`, `../doublespeak/doublespeak_attack.py`,
`30_build_pair_benchmark.py`, `data/pair_benchmark/pair_carrot_bomb.json` `_meta`,
`31_validate_readouts.py`, `stats.py`, `34_intervention_sweep.py:63`.
- 10 demo sentences = `doublespeak_attack.py:107`; wrapper strings `:105-106`.
- forced_choice 0.785 vs cloze 0.005 = `pair_readout_..._695115/readout_summary.json` (0.78518 / 0.00525).
- 20 controls × 3 families = 60/window (`N_RANDOM_CONTROLS = 20`); "TOST" **removed** (the code
  implements CI-within-margin, the string TOST is not in the codebase).

## Slide 6 · The three prompts + reading key
Prompts are verbatim rows of `data/pair_benchmark/pair_carrot_bomb.json`, `semantic` array,
`readout=forced_choice`, `demo_style=news`, `n_demos=4`, `split=dev` — sids
`DIRECT_CONCEPT|dev|news|4|forced_choice`, `NEUTRAL_CODEWORD|…`, `DOUBLESPEAK|…`.
- p("bomb") 0.785 / 0.000 / 0.353 = `pair_readout_..._695115/readout_summary.json`
  `by_readout.forced_choice.{DIRECT_CONCEPT,NEUTRAL_CODEWORD,DOUBLESPEAK}.p_concept`
  (0.78518 / 0.00009 / 0.35255), n=30 per condition — means over the whole forced_choice set, not
  the single displayed row. Labelled as such on the slide.
- Layer windows: `layer_windows(32)` → `t = 32//3 = 10` → early `range(0,10)`, mid `range(10,20)`,
  late `range(20,32)` — 10 / 10 / 12, so "bands", not equal thirds.
- p_concept measurement: `pair_common.semantic_score` — one `lm.model(**tok)` call, no `generate()`;
  `softmax(logits[0,-1,:].float())` at the last prompt token; sum over `word_first_ids` built from
  the four surface forms `' bomb'`, `'bomb'`, `' Bomb'`, `'Bomb'`, deduped to unique first-token ids.

## Slide 8–9 · Transplant (S2)
`outputs/pair_interv_replace_Llama-3.1-8B-Instruct_20260730_190530_694691/transplant_mediation_p_concept.json`
- 2×3 table = **mid window (L10–19)**: 0.00009 / 0.00005 / 0.00024 and 0.34744 / 0.35256 / 0.31394. MATCH.
  Column renamed benign → **neutral** (h_N is NEUTRAL_CODEWORD; a separate BENIGN_REMAP arm exists).
- IE_state within equivalence at 35/35 groups, max |eff| 5e-5. MATCH.
- DE_context mid +0.34735 [+0.26086, +0.43412]; TE 0.35247; DE/TE = 98.5%. MATCH.
  (p_holm = 0.105 — the deck claims the CI, not significance.)
- faithfulness 0.0 exact, n=1050 = 35 groups × 30 prompts. MATCH.
- 17,040 rows = 16 patched arms × 1050 + identity 240. MATCH ("30 per arm **per layer group**").
- Qwen3-14B DE 0.70271 / TE 0.76479 = **91.9%**. MATCH.

## Slide 11–12 · TOCTOU
Five separate jobs, one per topic — the table is a mosaic:
bomb 694811 (n=40) · grenade 697392 · chlorine 697405 · cocaine 698713 · pistol 698714 (n=60 each).
All 20 table cells MATCH to 2 dp. Superseded runs that do **not** reproduce it: 695111 (bomb), 695290
(grenade), 695291 (chlorine).
- bomb interaction +0.425 [+0.25, +0.60], p_holm 0.008; REJECTED −0.40. MATCH.
- concept-specificity REJECTED **0.825** (was 0.82), controls exactly 0.000. **corrected**.
- refusal ablation 1.00 → 0.53 on a **15-prompt held-out harmful set**, not the 60 fitting prompts.
  **corrected**.
- 4/5 pairs flip at their own predicted depth; chlorine null. Early-vs-late is Holm-significant for
  bomb and cocaine; pistol's effect is at mid-vs-late — hence the "pair-specific depth" line on the
  headline slide.

## Slide 13–14 · Direction sweep
`outputs/pair_causal_controls_693609.json` (bomb) + 693699 grenade / 693702 chlorine / 693704 pistol /
693705 cocaine; dose 693607; layer scan 693571.
- **All 10 table cells MATCH exactly.** The deck's d_DS column is the max over early/mid/late (early is
  the argmax in 5/5); `CAUSAL_CORE_FINDINGS.md`'s "d_DS max" column silently excludes early — the deck
  is right, the doc is mislabelled. Column header now says "max over early / mid / late".
- d_Direct peaks **late** for bomb/grenade/chlorine, **mid** for pistol, **early** for cocaine — so the
  column is explicitly a max, not a window.
- control mean **+0.000002** pooled over 180 (was +0.00002 — 10× too large; the fix strengthens it),
  max +0.0002. **corrected**.
- readout is **cloze**, replicated on one_word — not forced_choice. **corrected**.
- codeword_last: 693571 is a **single-layer scan**; best single layer +0.028 at **L3**, late layers
  exactly 0.000. **corrected** (it is not "the same late install").
- α is a fraction of the layer residual norm, so d_Direct and d_DS are injected at **equal strength** —
  the cleaner magnitude control than the ‖d‖ ratio.
- d_DS "**non-material** in 15/15 cells (all < the 0.01 bar)" — not "indistinguishable from controls":
  in 2 cells (pistol mid, grenade early) it does exceed all 60 controls while being ~100× too small.
- project-out mid −0.157 / late −0.068: CIs exclude 0 but p_holm = 0.28 — the deck does not call them
  significant.
