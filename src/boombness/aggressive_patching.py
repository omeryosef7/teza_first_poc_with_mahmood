"""aggressive_patching.py — plan §5: can we force `carrot` to be `bomb`-like, and does it matter?

This is the sprint's first decision gate. Before building a GCG objective we test whether
controlling the representation has ANY effect at all; if aggressive interventions do nothing,
the plan says stop and report that, and this module is what produces that verdict.

WHY THE 2x2 MAKES THIS CLEAN
----------------------------
The donor and recipient of a hidden-state transplant must be token-aligned or the transplant
is comparing positions that mean different things. In our bank, `direct_harmful` (B) and
`natural_doublespeak` (C) are the SAME token sequence except inside the target spans — the
tokenization audit verifies this per family and every occurrence is exactly one token — so
occurrence i of the donor and occurrence i of the recipient sit at the SAME absolute index,
and a transplant is exactly the counterfactual "what if this carrot token carried the bomb
token's representation". The same holds for the benign-context pair (E -> A), which is the
matched control: it applies an identically-sized surface-word transplant in a context where no
mapping is being taught, so any behavioural change it produces is NOT about doublespeak.

Positions are still resolved PER PROMPT and asserted to agree between donor and recipient;
nothing here trusts alignment it has not just checked (feedback_absolute_position_index_bug).

TWO INTERVENTIONS (plan §5.1, §5.2)
  transplant : h_recipient[L, pos] := h_donor[L, pos]      (house pair_common.ComponentOutSwap,
               which has a synthetic self-swap no-op test — we run that assertion live too)
  add        : h_recipient[L, pos] += alpha * d            for d in {d_surface, d_context,
               d_naive, random, orthogonal} (plan §2.5 controls)

READOUTS (plan §5.3) — all forward-only unless --generate:
  p_concept / p_codeword  whole-answer mass on the two words (C-6; teacher-forced surface
                          forms after `--answer-prefix`, NOT a single next token)
  boombness               <h, d_surface> at the readout layers, measured UNDER the intervention
  logit-lens              logit(concept) - logit(codeword) at the readout layers
  comprehension           the same next-token readout on the `comprehension_usage` query
  generation/ASR          only with --generate, on a subset, judged downstream

DEFECTS FOUND IN THE 2026-08-18/19 AUDITS, ALL FIXED HERE
---------------------------------------------------------
T9a  THE CONTROL "CI" WAS A SINGLE DRAW DRESSED UP AS A BAND. The `random` and `orthogonal`
     control directions were built once per layer as `seed=args.seed + L`, i.e. ONE vector per
     layer reused across every family and every domain. The domain bootstrap downstream then
     resampled that one vector 24 times, so the interval it printed contained prompt- and
     domain-level variance and exactly ZERO direction-level variance: the quantity the control
     is supposed to bound (how much a random axis of this norm moves the readout) was never
     varied at all. Retraction #7 established the same failure for the G4 steering band, where
     the BETWEEN-DRAW sd was 0.0301 — larger than several effects that had been called
     "outside the control band" — and the conclusion was never propagated to this module.
     FIX: `--n-control-draws` (default 12) independent draws per control family, each per-draw
     row tagged with `control_draw` / `direction_draw_name` / `is_control_draw` (the run-level
     count lives in metadata, in the summary, and on the band row as `n_control_draws`; it is
     NOT on the per-draw rows), plus an explicit per-cell band row
     (`intervention="add_control_band"`) carrying the mean AND the between-draw sd under
     `between_draw_sd|<metric>`. Draw 0 keeps the historical seed (`args.seed + L`) so the old
     numbers reappear as one member of the new band rather than being silently replaced. BOTH
     stochastic families are replicated, not just `random`: draw k of `random` uses seed base
     `seed + k*CONTROL_DRAW_SEED_STRIDE` and draw k of `orthogonal` the same base shifted by
     `signals.ORTHOGONAL_SEED_OFFSET`, and for STRIDE=1000003, OFFSET=977777 and layer depths
     under 1000 no (draw, layer) seed of one family collides with the other's.

T9b  THE T9a FIX WAS ITSELF A ONE-OF-TWO-PATHS FIX (found 2026-08-19 while verifying it, and it
     is R-12's shape verbatim). `--n-control-draws` is the REQUEST. The number of draws a cell
     actually ends with is `len(recs)`, and a draw can be dropped mid-cell by the ledgered `add:`
     failure. Two consequences, both of which reinstate exactly the artefact T9a exists to
     prevent: (i) a cell left with one surviving draw was still emitted as
     `intervention="add_control_band"`, i.e. a single observation carrying a band's NAME, which is
     retraction #7 and R-12 in one row; (ii) `summary.json`'s `control_draws_underpowered` was a
     pure function of `args.n_control_draws`, so a run that asked for 12 and achieved 1 reported
     "not underpowered". FIX: a cell with <2 surviving draws is emitted under a DIFFERENT
     `intervention` identity (`add_control_single_draw`), so no downstream filter on
     `add_control_band` can select a fake band; every band row carries `band_reportable`; and the
     run-level flag is now the OR of the request and the observed per-cell counts, with
     `n_control_draws_observed_min/max`, `n_band_cells_single_draw` and
     `n_band_cells_underpowered` in the summary. `between_draw_band` also stopped averaging
     id-like columns (`top1_id`, `n_variants_*`), which C-6 introduced: the mean of twelve token
     ids is a token no draw emitted.

T10  READOUT LAYERS OVERLAPPED THE PATCHED WINDOW, MAKING THE PLAN's OWN §5.3 METRIC
     TAUTOLOGICAL. The default readout layers {8,12,16,18,20,24,28,31} intersect the patched
     windows (the singletons L8/L12/L18/L24, every band, `write_carry_8-21`, and `all`). At a
     readout layer INSIDE the patched window, BlockCapture — correctly, after the (a)/(b) fix
     below — reports the value the intervention has just written. There is zero propagation:
     for `transplant` the captured vector IS the donor's, so the "direction projection score"
     equals the donor ceiling by construction; for `add` it is h + alpha*d, so the projection
     moves by exactly alpha*<d,d_surface> whether or not the model does anything with it.
     Measured on the committed run outputs/boombness/aggressive_patching/
     g1strat_20260818_133953_3374345: `boombness|L18|proj` under `transplant|query_only|L18`
     equals the donor-ceiling value BIT-FOR-BIT on all 48/48 recipient prompts, and the same
     holds for all 1200 in-window cells of `transplant|scope=all`. Across that run 30960 of
     55680 emitted readout cells (55.6%) sit inside their own patched window, touching 6720 of
     6960 intervention rows. Nothing in the artifact flagged it. `semantic_logodds` — the
     statistic the headlines actually use — reads the LM head at the final position and is NOT
     affected; only the `boombness|L*|{cos,proj}` and `ll|L*|boombness` families are.
     FIX: the rule is not restated here. `ds_common.patch_layer_sweep(R)` is the house single
     source of truth for it (it exists because defects C1/C3 were the same bug) and returns the
     patch layers that are valid for a readout at R, namely [0 .. R-1]; this module calls it and
     derives the flags from its answer. Every emitted row now carries
     `readout_inside_patched_window` (row-level bool) plus `readout_layers_inside_window`,
     `readout_layers_valid` and a per-layer `boombness|L{R}|inside_patched_window`, so old
     artifacts can be filtered by re-deriving the flag and new ones are self-describing. The
     values are still emitted, not dropped: a tautological cell is a useful positive control
     for "the patch actually landed", it just is not evidence of propagation.

T10b THE FIRST T10 FIX WAS LAYER-ONLY AND THEREFORE OVER-FLAGGED (found while reviewing the T10
     patch, same day). A patch has a POSITION extent as well as a layer extent, and the readout
     has exactly ONE position: `probe_pos` = the last (== query) occurrence. The first fix tested
     only "is R a patched layer", so it marked the three demo-only scopes (`demos_only`,
     `first_demo`, `last_demo`) as compromised even though those scopes never touch `probe_pos`
     (`select_positions` gives them `r_last[:-1]` slices) and their in-window cells are ordinary
     evidence. Measured on the same committed run, over its 6000 in-window transplant
     `boombness|L*|proj` cells: the 2400 from scope in {query_only, all} tie the donor ceiling
     2400/2400 bit-for-bit, while the 3600 from the demo-only scopes tie it 0/3600 (240 of them
     tie the BASELINE instead -- the singleton windows, where a patch at exactly L==R at some
     other position cannot reach the probe position inside block R at all: a guaranteed null, so
     also uninterpretable, but for the opposite reason). The layer-only flag was thus wrong on
     3600 of 6000 cells, always in the conservative direction: it would have discarded real
     evidence, and there is no cell for which it is False while the cell is tautological.
     FIX: `readout_window_flags` now also takes the patched positions and the probe position and
     emits `readout_probe_pos_patched` and `readout_tautological` (= inside AND probe patched),
     with a per-layer companion `boombness|L{R}|tautological`. `readout_inside_patched_window` is
     unchanged and retained as the pure LAYER predicate. Flags are cached per (scope, window)
     rather than per window. A caller that supplies no positions gets None -- never False -- so
     "not asked" cannot be misread as "clean".

C-6  THE SEMANTIC READOUT COULD NOT SPELL THE CODEWORD (fixed 2026-08-19; this is the one G1
     rests on). `semantic_logodds` was `log p(concept ids) - log p(codeword ids)` at the FINAL
     next-token position with no forcing prefix. Three separate faults, established by
     continuation-log corrections C-1/C-5/C-6 and re-measured here:
       1. The two options hold a MEDIAN 5.6e-06 of next-token mass on the committed baseline
          (0 of 516 rows above 1%). An ordering inside a 1e-5 tail is not a forced choice.
       2. The model CAPITALISES its answer (argmax after a forced "Answer:" is ' Car' 8/12,
          ' Bomb' 1/12).
       3. The capitalised codeword is MULTI-TOKEN: ' Carrot' = ' Car' + 'rot', and ' Car' is
          rejected by `signals.readout_ids` by design because `car` is the generic English word.
          On Llama-3.1-8B `bomb` has four single-token variants and `carrot` exactly one, so the
          instrument was biased 4-ids-to-1 toward the concept and STRUCTURALLY could not
          represent the model's preferred spelling of the codeword. Summing `full_word_ids`
          is the same bias with a larger constant, which is why `full_word` is not the fix.
     FIX: score the ANSWER, not a token. `signals.string_option_readout` teacher-forces each
     option's whole surface form and logsumexps over an identically-built variant set
     (`signals.answer_variants`, 2 per option by one rule), so symmetry is a property of the
     construction rather than of tokenizer luck; P("Carrot") = P(' Car')*P('rot'|' Car') is a
     joint probability, so no length normalisation is wanted. This is the SAME helper and the
     same contract `score_behavior.py` already runs as
     `--readout-ids whole_answer --answer-prefix "Answer:"`, ported here, together with its
     per-row `option_mass` and its fatal `--min-option-mass` gate. Smoke 764744 measured the
     option pair rising from 1.7e-04 to 0.541 of the answer mass -- 3,200x.
     THE OLD READOUT IS NOT DELETED. `--readout-ids primary|full_word` still selects it, and in
     `whole_answer` mode it is computed anyway from the same forward and emitted under the
     `nexttok|` prefix, so every new row is a paired old-vs-new diff at zero extra cost.
     THE RECORD IS VERSIONED, not silently redefined: `ROW_SCHEMA_VERSION`=2 in metadata and
     `semantic_readout_mode` on every row. A row with no `semantic_readout_mode` is v1 and must
     be read as mode="primary" -- that is the whole set of committed artifacts, including
     outputs/boombness/g1_stratified.json, whose `readout` field says `semantic_logodds`.
     ONE SEQUENCE PER FORWARD IS LOAD-BEARING, see WHOLE_ANSWER_MAX_BATCH: both house patch
     context managers edit batch row 0 only, so a batched variant forward under a patch would
     compare a patched concept against an UNPATCHED codeword.

V-1..V-4  FOUR DEFECTS IN THE C-6/T9b PATCH ITSELF (adversarial verification, 2026-08-19).
     V-1  THE TAIL GATE COULD NOT FAIL ON THE CASE IT EXISTS FOR. It was written inline in
          main() as a loop over the buckets it SAW, so a run whose families were all skipped --
          by `resolve:`, by `multi_subtoken_target:`, or by C-6's own new
          `answer_prefix_shifts_positions:` guard -- wrote `option_mass_gate: "PASS"` and exited
          0. resolve_occurrences documents jobs 764745-747, where that shape killed 179/179 rows
          under SLURM COMPLETED 0:0. The sibling port `surgical_knockout.option_mass_gate`
          already carried the missing-bucket check; it was dropped crossing into this module.
          FIX: `option_mass_gate()`, a module-level (therefore testable) function that reports a
          gating bucket's ABSENCE as fatal.
     V-2  THE GATE PICKED ITS BUCKETS BY THE KEY'S SPELLING (`bucket.rsplit("/",1)[-1] in
          (...)`) -- the incidental-property match all five of this project's dead guards used.
          FIX: `semantic_mass_bucket()` builds the key once, for the emitter and for the gate,
          and the gated set is the identities derived from this run's own --query-kind.
     V-3  `rows[0]["concept"], rows[0]["codeword"]` built the ids AND the teacher-forced answer
          STRINGS for the whole run -- the example[0]-reused-across-examples class, named on the
          same day by `surgical_knockout.readout_for`. Inert on today's bank (one pair in 2352
          rows), so FIX is a loud refusal: `assert_single_concept_codeword_pair`.
     V-4  `--query-kind comprehension_usage` is occurrence-safe, a live 288-row slice, and
          declares `scores: "comprehension"` -- its answers are "literal"/"coded".
          score_behavior.py carries a second variant set for it; the C-6 port took only the
          semantic half, so that run would teacher-force " bomb"/" Carrot" as the answer to a
          literal-or-coded question. FIX: `assert_query_kind_answers_with_the_pair`, keyed on
          the bank's own declared answer space, and scoped to `whole_answer` so the legacy
          single-token modes still reproduce the pre-C-6 runs exactly.
     (also) `control_draws_underpowered` returned False when NO band cell existed, because
          `any([])` is False -- the same never-evaluated-is-not-passed shape as V-1.

Responsible handling: forward-only by default; generations (when enabled) are written to a
separate gens.jsonl and never echoed to stdout.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_DIR, FailureLedger, RunDir, ds, pair, read_jsonl, seed_everything  # noqa: E402
import signals as sg  # noqa: E402
from extract_boombness import forward_hidden, resolve_occurrences  # noqa: E402

DEFAULT_BANK = os.path.join(DATA_DIR, "boombness_prompt_bank.jsonl")

# Donor -> recipient pairs. Both are exact word swaps of each other, so positions match.
#   harm_ctx : the doublespeak counterfactual  (does making carrot bomb-like change anything?)
#   benign_ctx: the matched control            (same transplant, no mapping being taught)
PAIRS = {
    "harm_ctx": ("direct_harmful", "natural_doublespeak"),
    "benign_ctx": ("concept_in_benign_ctx", "benign_literal"),
}

# Plan §5.1 scopes. Note the final occurrence IS the query occurrence in this bank, so the
# plan's "last carrot" and "final query carrot" are the same set; we name it once and add
# `last_demo` so the plan's five distinct scopes are all covered.
SCOPES = ("query_only", "all", "demos_only", "first_demo", "last_demo")

# Plan §5.1 layer windows, as (name, [block indices]). Filled in against the model depth.
def build_windows(n_layers: int, extra_singletons: Sequence[int] = ()) -> Dict[str, List[int]]:
    bands = [(0, 4), (5, 8), (9, 12), (13, 16), (17, 20), (21, 24), (25, n_layers - 1)]
    out: Dict[str, List[int]] = {}
    for lo, hi in bands:
        hi = min(hi, n_layers - 1)
        if lo <= hi:
            out[f"L{lo}-{hi}"] = list(range(lo, hi + 1))
    out["all"] = list(range(n_layers))
    # The write/carry band this repo has repeatedly localized (v_bomb uses range(8,22)).
    out["write_carry_8-21"] = [L for L in range(8, 22) if L < n_layers]
    for L in extra_singletons:
        if 0 <= L < n_layers:
            out[f"L{L}"] = [L]
    return out


def select_positions(last_idx: List[int], scope: str) -> List[int]:
    """Map a plan §5.1 scope name to token indices. The query occurrence is always the last."""
    if not last_idx:
        return []
    if scope == "query_only":
        return [last_idx[-1]]
    if scope == "all":
        return list(last_idx)
    demos = last_idx[:-1]
    if scope == "demos_only":
        return list(demos)
    if scope == "first_demo":
        return demos[:1]
    if scope == "last_demo":
        return demos[-1:]
    raise ValueError(f"unknown scope {scope!r}")


# --------------------------------------------------------------------------- #
# T10 guard: a readout layer may not sit inside the layers being patched
# --------------------------------------------------------------------------- #
#: Control families that are drawn at random and must therefore be REPLICATED (T9a). Everything
#: else in `directions` is a fitted, deterministic vector for which one "draw" is all there is.
STOCHASTIC_CONTROLS = ("random", "orthogonal")
#: Stride between the per-draw seed bases. Large and prime so that base_k + L never collides with
#: base_j + L' for any layer pair we use; draw 0 keeps the historical base (= args.seed).
CONTROL_DRAW_SEED_STRIDE = 1_000_003
#: Fewer draws than this and the between-draw sd is too noisy to bound anything; the run proceeds
#: but says so, per cell and at run level.
MIN_CONTROL_DRAWS_FOR_BAND = 10
#: A "band" over ONE draw is retraction #7 and R-12's shape: a single observation restated as a
#: spread. Such a cell keeps its mean but is emitted under a DIFFERENT `intervention` identity, so
#: no downstream filter on `intervention == "add_control_band"` can ever select it.
BAND_ROW_INTERVENTION = "add_control_band"
SINGLE_DRAW_ROW_INTERVENTION = "add_control_single_draw"


def control_draw_name(family: str, k: int) -> str:
    """Name of the k-th draw of a stochastic control family, e.g. random -> 'random#3'."""
    return f"{family}#{k}"


def split_direction_name(dname: str) -> Tuple[str, Optional[int]]:
    """Inverse of `control_draw_name`. Returns (family, draw_index or None)."""
    if "#" in dname:
        fam, _, k = dname.partition("#")
        return fam, int(k)
    return dname, None


def expand_add_directions(spec: str, n_draws: int) -> List[str]:
    """Turn the --add-directions spec into concrete direction names, replicating the controls.

    T9a: `random` and `orthogonal` become `random#0..#K-1` / `orthogonal#0..#K-1`; the fitted
    directions pass through unchanged because there is nothing stochastic to replicate about them.
    Pre-fix this function did not exist and the spec was used verbatim, which is what made the
    control a single draw.
    """
    out: List[str] = []
    for dname in spec.split(","):
        dname = dname.strip()
        if not dname:
            continue
        if dname in STOCHASTIC_CONTROLS:
            out.extend(control_draw_name(dname, k) for k in range(max(1, int(n_draws))))
        else:
            out.append(dname)
    return out


def build_control_directions(sg_mod, d_surface: Dict[int, "torch.Tensor"], seed: int,
                             n_draws: int) -> Dict[str, Dict[int, "torch.Tensor"]]:
    """K independent draws of each stochastic control, per layer (T9a).

    Draw k uses seed base `seed + k*CONTROL_DRAW_SEED_STRIDE`, so draw 0 is bit-identical to the
    single pre-fix vector (`seed + L`) and the committed numbers reappear as one member of the
    band instead of being quietly replaced by a different single draw.
    """
    out: Dict[str, Dict[int, "torch.Tensor"]] = {}
    for k in range(max(1, int(n_draws))):
        base_seed = seed + k * CONTROL_DRAW_SEED_STRIDE
        out[control_draw_name("random", k)] = {
            L: sg_mod.random_control_direction(v, seed=base_seed + L) for L, v in d_surface.items()}
        out[control_draw_name("orthogonal", k)] = {
            L: sg_mod.orthogonal_control_direction(v, seed=base_seed + L)
            for L, v in d_surface.items()}
    return out


def band_row_intervention(n_draws: int) -> str:
    """The `intervention` IDENTITY a control-aggregate row is allowed to claim.

    T9b. A row named `add_control_band` is, to every downstream filter, a between-draw spread.
    With one surviving draw there is no spread -- `between_draw_band` correctly reports sd None,
    but the NAME still says band, and both times this project shipped a fake band (retraction #7,
    then R-12) the fake was found by noticing agreement to four decimals, not by reading the sd.
    So the guard is placed on the identity rather than on a field: a single-draw cell is emitted
    under a different `intervention` and cannot be selected as a band at all.
    """
    return BAND_ROW_INTERVENTION if int(n_draws) >= 2 else SINGLE_DRAW_ROW_INTERVENTION


def control_draws_underpowered(requested: int, observed: Sequence[int],
                               any_stochastic: bool) -> bool:
    """Is this run's control band too thin to bound anything -- as REQUESTED or as ACHIEVED?

    T9b / R-12's shape. `requested` is `--n-control-draws`; `observed` is the number of draws each
    band cell actually ended with, which is smaller whenever a draw died in the ledgered `add:`
    failure. A summary computed from `requested` alone certifies a band no cell achieved, which is
    the same class of statement as the fake band itself. Both paths are consulted here so neither
    can be updated without the other.
    """
    if not any_stochastic:
        return False
    if int(requested) < MIN_CONTROL_DRAWS_FOR_BAND:
        return True
    # VERIFIER FIX 2026-08-19: stochastic controls were requested and NO band cell was produced.
    # `any([])` is False, so this returned "not underpowered" for a run whose band was never
    # measured at all -- the same never-evaluated-is-not-passed shape as the tail gate's missing
    # bucket. A band that does not exist cannot bound anything.
    if not list(observed):
        return True
    return any(int(k) < MIN_CONTROL_DRAWS_FOR_BAND for k in observed)


def assert_control_draws_consistent(add_dirs: Sequence[str],
                                    directions: Dict[str, Dict[int, "torch.Tensor"]]) -> None:
    """Every replicated control NAME must have a matching replicated control VECTOR.

    THE R-12 SHAPE, GUARDED. `n_control_draws` is threaded into two independent paths:
    `expand_add_directions` decides which draw NAMES get scored, `build_control_directions`
    decides which draw VECTORS exist. R-12 (and the 2026-08-17 fix before it) was one parameter
    threaded into one of two paths, twice. If that happens here, `run_pair`'s
    `directions.get(dname) is None -> continue` swallows the missing draws in SILENCE and the band
    quietly shrinks -- to one draw in the limit, which is exactly the artefact T9a removed. Checked
    once per family, loudly.
    """
    missing = [d for d in add_dirs
               if split_direction_name(d)[1] is not None and d not in directions]
    if missing:
        raise ValueError(
            "control draw names and control draw vectors disagree: "
            f"{missing[:6]}{'...' if len(missing) > 6 else ''} were expanded from "
            "--add-directions but no vector was built for them. expand_add_directions and "
            "build_control_directions must receive the SAME n_control_draws (R-12: the same "
            "parameter threaded into one of two paths).")


def readout_window_flags(dc, wlayers: Sequence[int],
                         readout_layers: Sequence[int],
                         patched_positions: Optional[Sequence[int]] = None,
                         probe_pos: Optional[int] = None) -> Dict[str, object]:
    """Flags recording, per row, which readout layers are compromised by this patch window.

    THE RULE IS NOT REIMPLEMENTED HERE. `ds_common.patch_layer_sweep(R)` is the house single
    source of truth (written for defects C1/C3, which were this same bug in the patchscope and
    activation-patching drivers): a LayerPatch at L edits hidden_states[L+1] and a readout at R
    reads hidden_states[R+1], so the only patch layers that leave R measurable are [0 .. R-1] and
    the sweep must stop at R-1. We ask it for that list and classify each readout layer against it:

      inside  : R is itself patched -> the captured vector IS what we just wrote (zero
                propagation, tautological: transplant reproduces the donor ceiling exactly,
                `add` moves the projection by exactly alpha*<d, d_surface>).
      valid   : every patched layer is in patch_layer_sweep(R) -> the whole intervention is
                strictly upstream of R and the readout measures real propagation.
      neither : the window straddles R or lies entirely above it. Layers above R cannot affect
                a readout at R at all, so such a cell is a guaranteed null by construction and
                is no more interpretable than an `inside` one — it is simply not `valid`.

    R=0 is a legitimate readout layer for which no valid patch window exists at all;
    patch_layer_sweep raises there, so we treat it as "no valid layers" rather than crashing a
    16-hour sweep over a flag.

    T10b (2026-08-18 review of the T10 fix): THE LAYER TEST ALONE OVER-FLAGS, because the patch
    also has a POSITION extent and the readout has exactly one position. `readout` projects the
    captured hidden state at `probe_pos` == the LAST occurrence == the query occurrence
    (see `select_positions`), while a patch touches only `select_positions(r_last, scope)`. The
    demo-only scopes (`demos_only`, `first_demo`, `last_demo`) never contain the probe position,
    so at a readout layer R inside such a window the captured vector was NOT written by the
    intervention and the cell is ordinary evidence, not a tautology. Measured on the committed run
    g1strat_20260818_133953_3374345, per scope, over its 1200 in-window `boombness|L*|proj`
    transplant cells (48 prompts x the windows containing that readout layer):

        scope=query_only  1200/1200 tie the donor ceiling bit-for-bit   -> tautological
        scope=all         1200/1200 tie the donor ceiling bit-for-bit   -> tautological
        scope=demos_only     0/1200 tie the ceiling (240 tie BASELINE)  -> NOT tautological
        scope=first_demo     0/1200 tie the ceiling (240 tie BASELINE)  -> NOT tautological
        scope=last_demo      0/1200 tie the ceiling (240 tie BASELINE)  -> NOT tautological

    (the 240 baseline ties are the SINGLETON windows: a patch at exactly L==R at some other
    position cannot reach the probe position within block R at all, so that cell is a guaranteed
    null rather than a tautology -- also uninterpretable, but for the opposite reason.)

    So `readout_inside_patched_window` is kept as the LAYER predicate it has always been, and the
    conjunction the analyst actually wants is emitted alongside it:

      readout_probe_pos_patched : the readout position is one of the patched positions.
      readout_tautological      : R is patched AND at the readout position -> the captured vector
                                  IS what the intervention wrote. This is the flag to filter on.

    When positions are not supplied both are reported as None (unknown) rather than False, so a
    caller that has not been updated cannot silently read "not tautological" out of "not asked".
    """
    ws = set(int(x) for x in wlayers)
    inside, valid = [], []
    for R in readout_layers:
        R = int(R)
        try:
            allowed = set(dc.patch_layer_sweep(R))
        except AssertionError:
            allowed = set()
        if R in ws:
            inside.append(R)
        if ws and ws <= allowed:
            valid.append(R)
    if patched_positions is None or probe_pos is None:
        probe_patched = None
        tautological = None
        taut_layers = None
    else:
        probe_patched = int(probe_pos) in {int(x) for x in patched_positions}
        taut_layers = inside if probe_patched else []
        tautological = bool(taut_layers)
    return {
        "readout_inside_patched_window": bool(inside),
        "readout_layers_inside_window": inside,
        "readout_layers_valid": valid,
        "n_readout_layers_inside_window": len(inside),
        "readout_probe_pos_patched": probe_patched,
        "readout_tautological": tautological,
        "readout_layers_tautological": taut_layers,
    }


def per_layer_inside_flags(readout_layers: Sequence[int],
                           inside: Sequence[int],
                           tautological: Optional[Sequence[int]] = None) -> Dict[str, object]:
    """Per-metric companion flags so a single readout column can be filtered on its own.

    T10b: `inside_patched_window` is the LAYER predicate; `tautological` is the conjunction with
    the position predicate (see readout_window_flags) and is the one to filter on. It is None when
    the caller did not supply positions, never False, so "not asked" cannot read as "clean".
    """
    ins = set(int(x) for x in inside)
    out: Dict[str, object] = {
        f"boombness|L{int(R)}|inside_patched_window": int(R) in ins for R in readout_layers}
    taut = None if tautological is None else {int(x) for x in tautological}
    for R in readout_layers:
        out[f"boombness|L{int(R)}|tautological"] = None if taut is None else (int(R) in taut)
    return out


def is_averageable_key(key: str) -> bool:
    """Is this numeric column a QUANTITY, i.e. is its mean a thing that exists?

    C-6 added `top1_id` (the token the model actually wants next) and `n_variants_*` to every row.
    Both are numeric and neither is a quantity: the mean of twelve token ids is a token id that no
    draw emitted, and the mean of a variant COUNT hides a per-draw mismatch instead of surfacing
    it. `between_draw_band` averaged every numeric non-bool column, so without this predicate the
    T9a control band would have published a fabricated `top1_id` alongside its real means -- the
    same shape of defect as the fabricated band T9a is about. Matched on the column's own TAIL
    name so the `nexttok|` prefixed copies are covered by identity, not by an incidental spelling.
    """
    tail = key.rsplit("|", 1)[-1]
    return not (tail == "top1_id" or tail.startswith("n_variants_"))


def between_draw_band(recs: Sequence[Dict[str, float]]) -> Dict[str, float]:
    """Mean and BETWEEN-DRAW sd of every numeric readout key across independent control draws.

    This is the number T9a says must exist and be stated. With one draw it is undefined, and the
    pre-fix code had exactly one draw per layer for the whole run — so the "control band" the
    bootstrap printed was a band over prompts and domains around a single fixed vector. sd is the
    sample sd (ddof=1); with n<2 it is reported as None rather than 0.0, because 0.0 would read
    as "no direction-level variance" instead of "not measured".
    """
    keys = [k for k in recs[0]
            if is_averageable_key(k) and all(isinstance(r.get(k), (int, float)) and
                                             not isinstance(r.get(k), bool) for r in recs)]
    out: Dict[str, float] = {}
    n = len(recs)
    for k in keys:
        vals = [float(r[k]) for r in recs]
        m = sum(vals) / n
        out[k] = m
        if n >= 2:
            var = sum((v - m) ** 2 for v in vals) / (n - 1)
            out[f"between_draw_sd|{k}"] = var ** 0.5
        else:
            out[f"between_draw_sd|{k}"] = None
    return out


# --------------------------------------------------------------------------- #
# C-6: the semantic readout instrument
# --------------------------------------------------------------------------- #
#: Row-schema version, written into metadata and onto every row.
#:   v1  rows whose `semantic_logodds` is the single-next-token statistic C-1/C-5/C-6 invalidated.
#:       They carry NO `semantic_readout_mode` key; a reader that finds none is looking at v1 and
#:       must read it as mode="primary". Every committed artifact is v1, including the run behind
#:       outputs/boombness/g1_stratified.json.
#:   v2  rows carrying `semantic_readout_mode`, `option_mass` and `top1_id`; in `whole_answer`
#:       mode the canonical semantic keys are whole-surface-form scores and the v1 numbers are
#:       preserved verbatim under the `nexttok|` prefix.
ROW_SCHEMA_VERSION = 2

#: `primary` / `full_word` are the v1 single-next-token instrument, kept for back-compat and for
#: the per-row diff; `whole_answer` is the default for new runs (C-6).
SEMANTIC_READOUT_MODES = ("primary", "full_word", "whole_answer")
DEFAULT_ANSWER_PREFIX = "Answer:"

#: ONE SEQUENCE PER FORWARD, and this is not a performance knob.
#: `signals.string_option_readout` batches its variants into a single forward. Both house patch
#: context managers edit BATCH ROW 0 ONLY -- `ds_common.LayerPatch._hook` writes `hidden[0, p, :]`
#: and `pair_common.ComponentOutSwap._hook` writes `h[self.bi, ...]` with `bi=0` -- so under a
#: patch a batched call would leave rows 1..n-1 UNPATCHED. The concept and the codeword occupy
#: different rows of that batch, so `semantic_logodds` would become a patched-vs-unpatched
#: comparison and every intervention effect would be confounded with which row a variant landed
#: in. With one sequence per forward, row 0 is the only row. (Lifting this needs an all-rows mode
#: in the two patch helpers, which live outside this module.)
WHOLE_ANSWER_MAX_BATCH = 1


#: The buckets whose option mass measures the INSTRUMENT rather than an arm. An intervened arm
#: that destroys the answer is a finding about the arm; a baseline that cannot represent either
#: answer is a broken readout. Only the second gates the run.
GATED_INTERVENTIONS = ("none", "donor_ceiling")


def semantic_mass_bucket(query_kind: str, intervention: str) -> str:
    """The option-mass bucket key for one row. ONE definition, used by the emitter and the gate.

    The gate used to decide which buckets it governs by splitting the key on "/" and testing the
    tail -- i.e. by an incidental property of the key's spelling. It now compares against the
    bucket IDENTITIES this function builds from `args.query_kind`, which is also what makes the
    "gating bucket never appeared" case detectable at all (see `option_mass_gate`).
    """
    return f"semantic/{query_kind}/{intervention}"


def option_mass_gate(mass_by_bucket: Dict[str, Sequence[float]], min_mass: float,
                     gating_buckets: Sequence[str]) -> Tuple[Dict[str, dict], List[str]]:
    """Per-bucket option-mass summary + the FATAL failures. C-6.

    VERIFIER FIX 2026-08-19 -- THE PORTED GATE COULD NOT FAIL ON THE CASE IT EXISTS FOR.
    The first version of this gate was written inline in `main()` as

        for bucket, vals in sorted(option_mass.items()):
            if not vals: continue
            ...
        if tail_fail and not args.allow_tail_readout: return 4

    so a run in which the gating buckets NEVER APPEARED -- every family skipped by `resolve:`, by
    `multi_subtoken_target:`, or by this very patch's new `answer_prefix_shifts_positions:` guard
    -- produced `tail_fail == []`, wrote `option_mass_gate: "PASS"` into summary.json and exited
    0. That is not hypothetical in this repo: `extract_boombness.resolve_occurrences` documents
    jobs 764745-747, where the same shape killed 179/179 rows in three arms while SLURM reported
    COMPLETED 0:0. A gate that never saw its own bucket has not passed; it has not run. The
    sibling C-6 port (`surgical_knockout.option_mass_gate`) already carries this check; it was
    dropped on the way into this module -- the project's one-of-two-paths shape, across scripts.

    `gating_buckets` are IDENTITIES built by `semantic_mass_bucket` from the run's own
    `--query-kind`, so a row emitted under a different query kind cannot satisfy the gate by
    accident, and its absence is reported rather than skipped.
    """
    summary: Dict[str, dict] = {}
    fatal: List[str] = []
    gating = list(dict.fromkeys(gating_buckets))
    gating_set = set(gating)
    for bucket in sorted(mass_by_bucket):
        vals = [float(x) for x in mass_by_bucket[bucket] if x is not None]
        if not vals:
            continue
        v = sorted(vals)
        med = v[len(v) // 2]
        summary[bucket] = {
            "n": len(v), "median": med, "p10": v[int(0.10 * len(v))],
            "p90": v[int(0.90 * len(v))], "max": v[-1], "min": v[0],
            "frac_above_1pct": sum(1 for m in v if m > 0.01) / len(v),
            "gated": bucket in gating_set, "gates_the_run": bucket in gating_set,
            "reportable": med >= min_mass}
        if bucket in gating_set and med < min_mass:
            fatal.append(f"{bucket}: median option mass {med:.4g} < {min_mass}")
    missing = [b for b in gating if b not in summary]
    if missing:
        fatal.append(f"no option mass recorded for gating bucket(s) {missing} -- the gate was "
                     f"never evaluated, which is not the same as passing it (check "
                     f"summary.json's failure_reasons: every family was skipped)")
    return summary, fatal


def assert_single_concept_codeword_pair(rows: Sequence[Dict]) -> Tuple[str, str]:
    """The (concept, codeword) pair the whole run is scored against, checked over ALL rows.

    VERIFIER FIX 2026-08-19. `main()` took `rows[0]["concept"], rows[0]["codeword"]` and built the
    readout ids AND the whole-answer variant strings from them once for the entire run. That is
    the example[0]-reused-across-examples shape this repo has been hit by twice, and the sibling
    C-6 port called it out by name on the same day (`surgical_knockout.readout_for`: "READOUT IDS
    AND ANSWER VARIANTS ARE PER (concept, codeword), NOT PER rows[0] ... inert on today's bank
    only because all eligible rows share one pair, which is an incidental property of the bank,
    not a contract"). C-6 makes the consequence worse than it was: the variants are literal
    strings that are TEACHER-FORCED as the answer, so a second pair in the bank would have every
    row of it scored on another family's words with a perfectly healthy-looking option mass.
    Measured on the committed bank the slice has exactly one pair, so this refuses nothing today
    and turns the silent-wrong-number into a loud refusal the day the bank grows.
    """
    pairs = sorted({(str(r["concept"]), str(r["codeword"])) for r in rows})
    if len(pairs) != 1:
        raise SystemExit(
            f"the selected bank slice carries {len(pairs)} distinct (concept, codeword) pairs, "
            f"but the readout ids and the whole-answer variant strings are built ONCE per run. "
            f"Scoring rows of one pair against another pair's words is silent and looks healthy. "
            f"Filter to one pair, or teach run_pair a per-pair readout (see "
            f"surgical_knockout.readout_for, which caches one per pair).")
    return pairs[0]


def assert_query_kind_answers_with_the_pair(query_kind: str, qk_table: Dict[str, Dict]) -> None:
    """The whole-answer readout may only be pointed at a query whose ANSWER is the pair.

    VERIFIER FIX 2026-08-19. `--query-kind` accepts every kind in `prompt_families.QUERY_KINDS`,
    and `comprehension_usage` is `occurrence_analysis_safe=True`, so it passes the refusal above
    and is a live 288-row slice of the bank. Its declared answer vocabulary is "literal"/"coded"
    (`scores: "comprehension"`), not the concept/codeword pair -- score_behavior.py carries a
    SECOND variant set, `comp_variants`, for exactly this and dispatches on the query kind. The
    C-6 port into this module took only the semantic half, so `--query-kind comprehension_usage`
    would teacher-force " bomb"/" Carrot" as the answer to a literal-or-coded question, label the
    result `semantic_logodds`, and die in the tail gate with a number that looks like a broken
    instrument rather than a mis-aimed one. Refused by the bank's OWN declared answer space
    (`scores`), not by a hard-coded list of kind names. Scoped to `whole_answer`: the legacy
    single-token modes reproduce the pre-C-6 runs exactly and are not narrowed here.
    """
    scores = str(qk_table.get(query_kind, {}).get("scores", ""))
    if scores != "semantic":
        ok = sorted(k for k, v in qk_table.items()
                    if str(v.get("scores", "")) == "semantic"
                    and v.get("occurrence_analysis_safe", True))
        raise SystemExit(
            f"--query-kind {query_kind!r} declares scores={scores!r}: its answer space is not the "
            f"(concept, codeword) pair, so the whole-answer readout would teacher-force words the "
            f"prompt never asks for and report them as `semantic_logodds`. Use one of {ok}, or "
            f"--readout-ids primary to reproduce the pre-C-6 single-token behaviour deliberately.")


def answer_prefix_preserves_positions(tokenizer, templated: str, answer_prefix: str,
                                      ids: Sequence[int]) -> bool:
    """Does appending `answer_prefix` leave every PROMPT token index unchanged?

    The patch positions are indices into `tokenize(templated)`, while the whole-answer readout
    forwards `tokenize(templated + answer_prefix)`. If the concatenation re-tokenizes across the
    join, index k stops denoting the same token in the two sequences and every patch lands one or
    more tokens off -- the absolute-position-index bug class that has hit this repo twice. The
    invariant is therefore checked LIVE per prompt against the tokenizer, never assumed from the
    fact that appending text "obviously" appends tokens.
    """
    if not answer_prefix:
        return True
    ext = tokenizer(templated + answer_prefix, add_special_tokens=False)["input_ids"]
    return len(ext) >= len(ids) and list(ext[:len(ids)]) == list(ids)


@torch.no_grad()
def whole_answer_semantic(lm, context: str,
                          variants: Dict[str, Sequence[str]]) -> Dict[str, float]:
    """C-6's readout: `signals.string_option_readout` under score_behavior.py's contract.

    REUSE, NOT REIMPLEMENTATION. The variant construction (`signals.answer_variants`), the
    teacher-forced joint probability of the whole surface form, and `option_mass` all come from
    signals.py -- the same functions `score_behavior.py` runs as
    `--readout-ids whole_answer --answer-prefix "Answer:"`. The only thing this wrapper adds is
    `max_batch=WHOLE_ANSWER_MAX_BATCH`, which is required HERE and not there because here the
    forward happens under a patch (see that constant), plus the mapping onto this module's row
    keys so `semantic_logodds` keeps its name and every downstream filter keeps working.
    """
    r = sg.string_option_readout(lm, context, variants, max_batch=WHOLE_ANSWER_MAX_BATCH)
    return {
        "logp_concept": r["logp_concept"], "logp_codeword": r["logp_codeword"],
        "p_concept": r["p_concept"], "p_codeword": r["p_codeword"],
        "semantic_logodds": r["logp_concept"] - r["logp_codeword"],
        "semantic_margin_p_diff": r["p_concept"] - r["p_codeword"],
        "option_mass": r["option_mass"], "top1_id": r["top1_id"],
        "n_variants_concept": r["n_variants_concept"],
        "n_variants_codeword": r["n_variants_codeword"],
    }


# --------------------------------------------------------------------------- #
# Readouts
# --------------------------------------------------------------------------- #
class BlockCapture:
    """Capture the TRUE output of chosen decoder blocks, after any patch hooks have run.

    Two bugs in one, both found by the §5 smoke and both silent:

    (a) READS AT THE PATCHED LAYER WERE PRE-PATCH. `out.hidden_states[L+1]` is filled by the
        framework's own capture, which is registered before ours, so at the very layer being
        patched it reports the value the patch was about to overwrite. Measured: patching
        window `L8` left the L8 readout bit-identical to baseline (-0.2294) while a window
        containing layers *below* 8 moved it (+0.1477) — i.e. the readout only ever saw
        upstream effects and reported "no effect at the intervened layer" by construction.

    (b) THE LAST LAYER WAS IN THE WRONG COORDINATES. transformers 5.12 ties
        `hidden_states[-1]` to `last_hidden_state` (post final norm), while the directions are
        fitted on RAW block outputs, so the L31 projection mixed two coordinate systems.

    Registering our own forward hooks on the blocks fixes both: they run after the patch hooks
    (later registration = later execution on the same module), and they read the block's own
    output rather than the framework's tied tuple.
    """

    def __init__(self, model, layer_idxs: Sequence[int]):
        self.layers = ds()._get_layers(model)
        self.idxs = list(layer_idxs)
        self.buf: Dict[int, torch.Tensor] = {}
        self._handles: List[object] = []

    def _hook(self, li: int):
        def f(mod, inp, out):
            h = out[0] if isinstance(out, tuple) else out
            self.buf[li] = h.detach()
        return f

    def __enter__(self):
        self.buf.clear()
        for li in self.idxs:
            self._handles.append(self.layers[li].register_forward_hook(self._hook(li)))
        return self

    def __exit__(self, *exc):
        for h in self._handles:
            h.remove()
        self._handles = []
        return False

    def at(self, layer: int, pos: int) -> torch.Tensor:
        if layer not in self.buf:
            raise KeyError(f"block {layer} was not captured (hook did not fire)")
        return self.buf[layer][0, pos, :].float().cpu()


@torch.no_grad()
def readout(lm, ids: List[int], cap: "BlockCapture",
            concept_ids: Sequence[int], codeword_ids: Sequence[int],
            readout_layers: Sequence[int], d_surface: Dict[int, torch.Tensor],
            probe_pos: int, semantic_mode: str = "whole_answer",
            templated: Optional[str] = None, answer_prefix: str = "",
            sem_variants: Optional[Dict[str, Sequence[str]]] = None) -> Dict[str, float]:
    """One patched forward -> semantics + boombness + logit lens at `probe_pos`.

    `cap` must already be entered, AFTER the patch contexts, so its hooks see patched values.

    C-6: `semantic_mode` selects the INSTRUMENT the semantic keys are computed on.
      whole_answer (default)  teacher-forced whole surface forms after `answer_prefix`, via
                              `whole_answer_semantic`. The v1 single-token numbers are still
                              computed from this same forward and emitted under `nexttok|`, so
                              every row is a paired old-vs-new diff for free.
      primary / full_word     the v1 instrument, unchanged and bit-comparable with the committed
                              artifacts. `option_mass` and `top1_id` are now recorded for it too
                              -- their absence is what let a 1e-5 readout ship for two months.
    """
    if semantic_mode not in SEMANTIC_READOUT_MODES:
        raise ValueError(f"unknown semantic readout mode {semantic_mode!r}; "
                         f"expected one of {SEMANTIC_READOUT_MODES}")
    # Argument validity is settled BEFORE the first forward, not between the forward and the
    # scoring: a mode wired into one call site and not another must die at the smoke's first row,
    # which is how job 764743's identical slip was caught.
    if semantic_mode == "whole_answer" and (templated is None or not sem_variants):
        raise ValueError("semantic_mode='whole_answer' needs `templated` and `sem_variants`")
    t = torch.tensor([ids], device=lm.model.device)
    out = lm.model(input_ids=t, use_cache=False)
    logits = out.logits[0, -1, :].float().cpu()
    lp = torch.log_softmax(logits, dim=-1)
    ci = torch.tensor(list(concept_ids), dtype=torch.long)
    wi = torch.tensor(list(codeword_ids), dtype=torch.long)
    # LOG-ODDS IS THE PRIMARY STATISTIC. Both candidates sit deep in the tail (p ~ 1e-6..1e-13)
    # because a chat model does not open with the bare answer word, so a difference of
    # probabilities discards the signal entirely - see next_token_readout in score_behavior.py.
    # Computed in log space directly, never by exponentiating and re-logging.
    lse_c = float(lp[ci].logsumexp(0))
    lse_w = float(lp[wi].logsumexp(0))
    # OPTION MASS -- the statistic whose absence let this readout ship (C-1). A log-odds between
    # two options is a decision margin only if the options are plausibly what comes next.
    opt_idx = torch.tensor(sorted(set(int(x) for x in concept_ids) |
                                  set(int(x) for x in codeword_ids)), dtype=torch.long)
    nexttok: Dict[str, float] = {
        "logp_concept": lse_c, "logp_codeword": lse_w,
        "semantic_logodds": lse_c - lse_w,
        "p_concept": float(torch.tensor(lse_c).exp()),
        "p_codeword": float(torch.tensor(lse_w).exp()),
        "semantic_margin_p_diff": float(torch.tensor(lse_c).exp() - torch.tensor(lse_w).exp()),
        "option_mass": float(lp[opt_idx].logsumexp(0).exp()),
        "top1_id": int(lp.argmax()),
    }

    rec: Dict[str, float] = {}
    # THE PER-LAYER READOUTS ARE HARVESTED FROM `cap` BEFORE the whole-answer forwards run.
    # `cap`'s hooks are still registered, so each whole-answer forward overwrites `cap.buf`; the
    # context is a prefix of every variant sequence and attention is causal, so the value at
    # `probe_pos` would be unchanged -- but relying on that would be relying on a coincidence of
    # the readout position, and the first version of BlockCapture already shipped one silent
    # ordering bug (see (a) above). Read first, then score.
    hs = torch.stack([cap.at(L, probe_pos) for L in readout_layers], dim=0)
    lls = sg.logit_lens_boombness_batch(lm, hs, concept_ids, codeword_ids)
    for i, L in enumerate(readout_layers):
        h = hs[i]
        d = d_surface.get(L)
        if d is not None:
            s = sg.direction_boombness(h, d)
            rec[f"boombness|L{L}|cos"] = s["cosine"]
            rec[f"boombness|L{L}|proj"] = s["projection"]
        rec[f"ll|L{L}|boombness"] = lls[i]["logit_lens_boombness"]

    if semantic_mode == "whole_answer":
        rec.update(whole_answer_semantic(lm, templated + answer_prefix, sem_variants))
        rec.update({f"nexttok|{k}": v for k, v in nexttok.items()})
    else:
        rec.update(nexttok)
    rec["semantic_readout_mode"] = semantic_mode
    return rec


# --------------------------------------------------------------------------- #
# Sweep
# --------------------------------------------------------------------------- #
def run_pair(lm, dc, pc, donor: Dict, recip: Dict, windows: Dict[str, List[int]],
             scopes: Sequence[str], alphas: Sequence[float], directions: Dict[str, Dict[int, torch.Tensor]],
             readout_layers: Sequence[int], concept_ids: Sequence[int], codeword_ids: Sequence[int],
             run: RunDir, ledger: FailureLedger, pair_name: str,
             do_transplant: bool, add_dirs: Sequence[str],
             scales: Optional[Dict[str, Dict[int, float]]] = None,
             dose_unit: str = "gap", semantic_mode: str = "whole_answer",
             answer_prefix: str = "", sem_variants: Optional[Dict[str, Sequence[str]]] = None,
             option_mass: Optional[Dict[str, List[float]]] = None,
             band_draw_counts: Optional[List[int]] = None) -> int:
    """Every intervention for one donor/recipient family. Returns rows written."""
    try:
        d_text, d_ids, d_last, _, d_nsub = resolve_occurrences(dc, lm.tokenizer, donor)
        r_text, r_ids, r_last, _, r_nsub = resolve_occurrences(dc, lm.tokenizer, recip)
    except ValueError as e:
        ledger.fail(f"resolve:{e}", recip["prompt_id"])
        return 0

    # Alignment is asserted here, live, not assumed from the generator.
    if len(d_ids) != len(r_ids):
        ledger.fail(f"pair_len_mismatch:{len(d_ids)}vs{len(r_ids)}", recip["prompt_id"])
        return 0
    if d_last != r_last:
        ledger.fail("pair_occurrence_positions_differ", recip["prompt_id"])
        return 0
    if any(n != 1 for n in d_nsub + r_nsub):
        ledger.fail(f"multi_subtoken_target:{sorted(set(d_nsub + r_nsub))}", recip["prompt_id"])
        return 0

    # C-6 + the absolute-position-index bug class. The whole-answer readout forwards
    # `templated + answer_prefix`, while every patch position is an index into `templated` alone.
    # If the tokenizer merges across that join the two index spaces diverge and the patch lands on
    # the wrong tokens -- silently, with plausible numbers. Checked live, per prompt, on BOTH
    # sides of the pair, and a failure is a counted skip rather than a wrong row.
    if semantic_mode == "whole_answer":
        for who, txt, tok_ids in (("donor", d_text, d_ids), ("recipient", r_text, r_ids)):
            if not answer_prefix_preserves_positions(lm.tokenizer, txt, answer_prefix, tok_ids):
                ledger.fail(f"answer_prefix_shifts_positions:{who}", recip["prompt_id"])
                return 0

    donor_hs = forward_hidden(lm, d_ids)          # [n_blocks+1, seq, H]
    probe_pos = r_last[-1]
    d_surface = directions["d_surface"]

    base = dict(
        pair=pair_name, donor_condition=donor["condition"], recipient_condition=recip["condition"],
        family_id=recip["family_id"], recipient_prompt_id=recip["prompt_id"],
        donor_prompt_id=donor["prompt_id"], domain=recip["domain"], split=recip["split"],
        n_examples=recip["n_examples"], query_kind=recip["query_kind"],
        n_occurrences=len(r_last), seq_len=len(r_ids), probe_pos=probe_pos,
        layer_convention=sg.LAYER_CONVENTION,
        readout_layers=list(readout_layers),
        # C-6: the record is VERSIONED, not silently redefined. A row without these keys is v1,
        # i.e. the single-next-token instrument, and must be read as mode="primary".
        row_schema_version=ROW_SCHEMA_VERSION,
        semantic_readout_mode=semantic_mode,
        answer_prefix=answer_prefix,
    )

    # C-6 tail-gate feed. Bucketed per (readout, query_kind, intervention) rather than per run:
    # an intervention that destroys the answer legitimately drives option mass down, and that is a
    # FINDING about the arm, not a defect in the instrument. Only the no-intervention buckets
    # answer "can this readout represent both answers at all", which is what the gate is for.
    # (The coarse-bucket lesson is score_behavior.py tick 27: a gate keyed too coarsely condemned
    # a healthy comprehension readout because a different arm dipped.)
    def emit(row: Dict[str, object]) -> None:
        run.log_row(row)
        if option_mass is None:
            return
        m = row.get("option_mass")
        if isinstance(m, (int, float)) and not isinstance(m, bool):
            option_mass[semantic_mass_bucket(str(recip["query_kind"]),
                                             str(row["intervention"]))].append(float(m))

    # T10: resolve the readout/window overlap from ds_common.patch_layer_sweep. T10b: the overlap
    # is a function of the SCOPE as well as the window -- a patch that never touches `probe_pos`
    # cannot overwrite the readout however many readout layers it spans -- so the flags are cached
    # per (scope, window) and the positions of that scope are handed to the helper.
    # scope "" / window "" is the no-intervention case (baseline / donor ceiling): nothing is
    # patched, so nothing is compromised, but the flags are still emitted so every row is
    # self-describing.
    _wf_cache: Dict[Tuple[str, str], Dict[str, object]] = {}

    def wf(scope: str, wname: str) -> Dict[str, object]:
        hit = _wf_cache.get((scope, wname))
        if hit is None:
            wl = windows.get(wname, []) if wname else []
            pos = select_positions(r_last, scope) if scope else []
            hit = readout_window_flags(dc, wl, readout_layers,
                                       patched_positions=pos, probe_pos=probe_pos)
            hit.update(per_layer_inside_flags(readout_layers,
                                              hit["readout_layers_inside_window"],
                                              hit["readout_layers_tautological"]))
            _wf_cache[(scope, wname)] = hit
        return hit

    n = 0
    # -- baseline (no intervention) ------------------------------------------ #
    with contextlib.ExitStack() as st:
        cap = st.enter_context(BlockCapture(lm.model, readout_layers))
        rec = readout(lm, r_ids, cap, concept_ids, codeword_ids, readout_layers,
                      d_surface, probe_pos, semantic_mode, r_text, answer_prefix,
                      sem_variants)
    emit({**base, "intervention": "none", "scope": "", "window": "", "alpha": 0.0,
                 "direction": "", **wf("", ""), **rec})
    n += 1

    # -- donor ceiling: what the readout looks like on the donor prompt itself - #
    with contextlib.ExitStack() as st:
        cap = st.enter_context(BlockCapture(lm.model, readout_layers))
        rec = readout(lm, d_ids, cap, concept_ids, codeword_ids, readout_layers,
                      d_surface, probe_pos, semantic_mode, d_text, answer_prefix,
                      sem_variants)
    emit({**base, "intervention": "donor_ceiling", "scope": "", "window": "", "alpha": 0.0,
                 "direction": "", **wf("", ""), **rec})
    n += 1

    # -- self-swap no-op assertion (the house invariant, checked live) --------- #
    recip_hs = forward_hidden(lm, r_ids)
    all_layers = list(range(lm.num_layers))
    src_self = {L: recip_hs[L + 1, r_last, :].clone() for L in all_layers}
    with contextlib.ExitStack() as st:
        st.enter_context(pc.ComponentOutSwap(lm.model, r_last, src_self, component="resid_post"))
        cap = st.enter_context(BlockCapture(lm.model, readout_layers))
        rec_self = readout(lm, r_ids, cap, concept_ids, codeword_ids, readout_layers,
                           d_surface, probe_pos, semantic_mode, r_text, answer_prefix,
                           sem_variants)
    emit({**base, "intervention": "self_swap_noop_check", "scope": "all", "window": "all",
                 "alpha": 0.0, "direction": "", **wf("all", "all"), **rec_self})
    n += 1

    # -- 5.1 transplants ------------------------------------------------------ #
    if do_transplant:
        for scope in scopes:
            pos = select_positions(r_last, scope)
            if not pos:
                continue
            for wname, wlayers in windows.items():
                src = {L: donor_hs[L + 1, pos, :].clone() for L in wlayers}
                try:
                    with contextlib.ExitStack() as st:
                        st.enter_context(pc.ComponentOutSwap(lm.model, pos, src, component="resid_post"))
                        cap = st.enter_context(BlockCapture(lm.model, readout_layers))
                        rec = readout(lm, r_ids, cap, concept_ids, codeword_ids,
                                      readout_layers, d_surface, probe_pos, semantic_mode,
                                      r_text, answer_prefix, sem_variants)
                except Exception as e:
                    ledger.fail(f"transplant:{type(e).__name__}", recip["prompt_id"])
                    continue
                emit({**base, "intervention": "transplant", "scope": scope,
                             "window": wname, "n_positions": len(pos), "alpha": 0.0,
                             "direction": "", **wf(scope, wname), **rec})
                n += 1

    # -- 5.2 additive direction ----------------------------------------------- #
    # T9a: the stochastic controls arrive here as several independent draws (random#0, random#1,
    # ...). Each draw is logged as its own row so nothing is hidden, and the draws for one cell
    # are additionally collapsed into a single `add_control_band` row that states the mean and
    # the between-draw sd. `band[(scope, window, alpha, family)] -> [rec per draw]`.
    band: Dict[Tuple[str, str, float, str], List[Dict[str, float]]] = collections.defaultdict(list)
    for dname in add_dirs:
        dmap = directions.get(dname)
        if dmap is None:
            continue
        for scope in ("query_only", "all"):
            pos = select_positions(r_last, scope)
            if not pos:
                continue
            for wname in ("write_carry_8-21", "all"):
                wlayers = windows[wname]
                for alpha in alphas:
                    patches = []
                    for L in wlayers:
                        d = dmap.get(L)
                        if d is None:
                            continue
                        # alpha is in GAP UNITS by default (see main()): the effective
                        # residual-space magnitude is alpha * ||diff-of-means at this layer||.
                        k = 1.0
                        if dose_unit == "gap" and scales is not None:
                            k = scales.get(dname, {}).get(L, 1.0)
                        patches.append((L, pos, d, alpha * k))
                    if not patches:
                        continue
                    try:
                        with contextlib.ExitStack() as st:
                            for L, p, d, a in patches:
                                st.enter_context(dc.LayerPatch(lm.model, L, p, vector=d,
                                                               mode="add", alpha=a))
                            cap = st.enter_context(BlockCapture(lm.model, readout_layers))
                            rec = readout(lm, r_ids, cap, concept_ids, codeword_ids,
                                          readout_layers, d_surface, probe_pos, semantic_mode,
                                          r_text, answer_prefix, sem_variants)
                    except Exception as e:
                        ledger.fail(f"add:{type(e).__name__}", recip["prompt_id"])
                        continue
                    eff = [round(a, 4) for (_, _, _, a) in patches]
                    fam_name, draw = split_direction_name(dname)
                    emit({**base, "intervention": "add", "scope": scope, "window": wname,
                                 "n_positions": len(pos), "alpha": alpha,
                                 # `direction` stays the FAMILY name so every downstream filter
                                 # written against the pre-fix artifacts (direction == "random")
                                 # keeps selecting the right rows; the draw index is a new column.
                                 "direction": fam_name, "direction_draw_name": dname,
                                 "control_draw": draw, "is_control_draw": draw is not None,
                                 "dose_unit": dose_unit,
                                 "effective_alpha_min": min(eff), "effective_alpha_max": max(eff),
                                 **wf(scope, wname), **rec})
                    n += 1
                    if draw is not None:
                        band[(scope, wname, float(alpha), fam_name)].append(rec)

    # -- T9a control band: one row per cell, across the independent draws ------ #
    # THE COUNT THAT MATTERS IS THE ONE THAT SURVIVED, not the one that was requested. A draw can
    # be dropped mid-cell (the `add:` ledger failure above `continue`s), so `--n-control-draws 12`
    # does not entail 12 recs here. R-12's shape is exactly this: the seed fix was threaded into
    # one path and the other path silently produced a 1-draw band anyway. A cell with fewer than 2
    # surviving draws has NO between-draw spread, so it is not emitted as a band at all -- it gets
    # its own `intervention` IDENTITY, which no `intervention == "add_control_band"` filter can
    # reach -- and the per-cell counts go back to the caller so the RUN-LEVEL underpowered flag is
    # derived from what happened rather than from what was asked for.
    for (scope, wname, alpha, fam_name), recs in sorted(band.items(), key=lambda kv: str(kv[0])):
        agg = between_draw_band(recs)
        k = len(recs)
        if band_draw_counts is not None:
            band_draw_counts.append(k)
        emit({**base,
              "intervention": band_row_intervention(k),
              "scope": scope, "window": wname,
              "alpha": alpha, "direction": fam_name, "control_draw": None,
              "is_control_draw": True, "n_control_draws": k,
              "band_reportable": k >= MIN_CONTROL_DRAWS_FOR_BAND,
              "dose_unit": dose_unit, **wf(scope, wname), **agg})
        n += 1
    ledger.ok()
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", default=DEFAULT_BANK)
    ap.add_argument("--fit-dir", required=True, help="extract_boombness run dir with directions_fit_*.pt")
    ap.add_argument("--model", default=None)
    # Choices are DERIVED from the generator's own table, not restated here: a hardcoded copy
    # silently desynced when `semantic_forced_choice` was added and killed job 760715 at launch.
    from prompt_families import QUERY_KINDS as _QK
    ap.add_argument("--query-kind", default="semantic_forced_choice",
                    choices=sorted(_QK))
    ap.add_argument("--n-families", type=int, default=4, help="matched families per pair (smoke=2)")
    ap.add_argument("--n-examples", default="4", help="comma list")
    ap.add_argument("--scopes", default=",".join(SCOPES))
    ap.add_argument("--alphas", default="0.25,0.5,1,2,4,8")
    ap.add_argument("--add-directions", default="d_surface,d_context,d_naive,random,orthogonal")
    ap.add_argument("--n-control-draws", type=int, default=12,
                    help="T9a: independent draws of each stochastic control direction "
                         "(random, orthogonal). The pre-fix code used ONE vector per layer for "
                         "the entire run, so the control interval the bootstrap reported "
                         "contained prompt/domain variance and no direction variance at all. "
                         "Draw 0 reproduces the historical seed. Fewer than 10 draws gives a "
                         "between-draw sd too noisy to bound anything; the run still proceeds "
                         "but records `control_draws_underpowered` in its summary.")
    ap.add_argument("--readout-layers", default="")
    ap.add_argument("--singletons", default="8,9,10,14,15,16,17,18,19,20,21")
    ap.add_argument("--no-transplant", action="store_true")
    # C-6. `whole_answer` is the DEFAULT for new runs and is the same contract score_behavior.py
    # already runs (`--readout-ids whole_answer --answer-prefix "Answer:"`). The old instrument is
    # still selectable, and is emitted alongside the new one under `nexttok|` regardless, so the
    # committed artifacts stay readable and every new row is a paired diff.
    ap.add_argument("--readout-ids", default="whole_answer", choices=list(SEMANTIC_READOUT_MODES),
                    help="whole_answer (default from 2026-08-19) teacher-forces each option's "
                         "WHOLE surface form and logsumexps over an identically-built variant "
                         "set, so the capitalised MULTI-TOKEN codeword (' Carrot' = ' Car'+'rot') "
                         "is representable and the two arms are symmetric by construction. "
                         "primary/full_word are the pre-C-6 single-next-token instrument, which "
                         "structurally could not spell the codeword and was biased 4-ids-to-1 "
                         "toward the concept.")
    ap.add_argument("--answer-prefix", default=DEFAULT_ANSWER_PREFIX,
                    help='assistant-side text appended before the forward readout position, so '
                         'the scored continuation is the answer word rather than a preamble. '
                         'Pass "none" to reproduce the pre-C-6 unprefixed position.')
    ap.add_argument("--min-option-mass", type=float, default=0.05,
                    help="refuse (exit 4) if the MEDIAN option mass on a NO-INTERVENTION bucket "
                         "is below this. A forced choice decided inside a 1e-5 tail is not a "
                         "forced choice; it is an ordering of two things the model was never "
                         "going to say. Intervened arms are measured and reported but never "
                         "gated -- a destroyed answer there is a finding about the arm.")
    ap.add_argument("--allow-tail-readout", action="store_true",
                    help="override --min-option-mass deliberately (the run is then NOT reportable "
                         "as a semantic result, and says so in summary.json)")
    ap.add_argument("--dose-unit", default="gap", choices=["gap", "absolute"],
                    help="'gap' (default): alpha is in units of the layer's diff-of-means norm, "
                         "so alpha=1 injects one natural gap. 'absolute': alpha is a raw "
                         "residual-space magnitude on a unit vector (the old, badly-scaled "
                         "behaviour; kept only to reproduce it).")
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--seed", type=int, default=20260816)
    ap.add_argument("--tag", default="smoke")
    args = ap.parse_args()
    # SHELL-SAFE EMPTY, copied from score_behavior.py: the SLURM wrapper word-splits its argument
    # string, so `--answer-prefix ""` silently becomes the NEXT flag. The pre-C-6 behaviour has to
    # be reachable by a literal sentinel.
    if args.answer_prefix.strip().lower() in ("none", "''", '""'):
        args.answer_prefix = ""
    seed_everything(args.seed)

    dc, pc = ds(), pair()
    rows = read_jsonl(args.bank)
    want_n = {int(x) for x in args.n_examples.split(",")}
    rows = [r for r in rows if r["query_kind"] == args.query_kind and r["n_examples"] in want_n
            and r["bank_block"] == "core2x2"]
    by_family: Dict[str, Dict[str, Dict]] = collections.defaultdict(dict)
    for r in rows:
        by_family[r["family_id"]][r["condition"]] = r

    # A transplant is position-matched: it copies donor state at occurrence i into recipient
    # occurrence i. That is only meaningful when donor and recipient have the SAME occurrence
    # positions, which a query naming BOTH words breaks by construction (cell B's query contains
    # bomb...carrot...bomb, cell C's carrot...carrot...bomb). Job 760722 was launched on
    # semantic_forced_choice and every one of its 16 families was rejected by the live position
    # assertion - correct behaviour, but it should never have been launchable. Refuse up front.
    if not _QK.get(args.query_kind, {}).get("occurrence_analysis_safe", True):
        raise SystemExit(
            f"--query-kind {args.query_kind!r} names both the concept and the codeword, so donor "
            "and recipient occurrence positions do not correspond and a position-matched "
            "transplant is undefined. Use an occurrence-safe kind: "
            + ", ".join(sorted(k for k, v in _QK.items() if v.get("occurrence_analysis_safe", True))))

    # C-6 (verifier fix): the whole-answer readout teacher-forces the concept/codeword surface
    # forms AS THE ANSWER, so it may only be pointed at a query whose declared answer space is
    # that pair. `comprehension_usage` is occurrence-safe and therefore survives the refusal
    # above, but its answers are "literal"/"coded".
    if args.readout_ids == "whole_answer":
        assert_query_kind_answers_with_the_pair(args.query_kind, _QK)

    run = RunDir("aggressive_patching", args, tag=args.tag)
    ledger = FailureLedger()

    model_id = args.model or dc.PRIMARY_MODEL
    lm = dc.load_model(model_id, dtype=getattr(torch, args.dtype), attn_implementation="sdpa")
    run.note_bank(args.bank)
    run.note_model(lm.model_id, revision=lm.revision, dtype=str(lm.dtype),
                   attn_implementation="sdpa", num_layers=lm.num_layers)

    fitted = {}
    for split in ("dev", "heldout"):
        p = os.path.join(args.fit_dir, f"directions_fit_{split}.pt")
        if os.path.exists(p):
            fitted[split] = torch.load(p, map_location="cpu", weights_only=False)
    if not fitted:
        raise SystemExit(f"no directions_fit_*.pt under {args.fit_dir}")

    readout_layers = ([int(x) for x in args.readout_layers.split(",") if x.strip()]
                      if args.readout_layers
                      else sorted({8, 12, 16, 18, 20, 24, 28, lm.num_layers - 1}))
    windows = build_windows(lm.num_layers, [int(x) for x in args.singletons.split(",") if x.strip()])
    alphas = [float(x) for x in args.alphas.split(",") if x.strip()]

    # T9a: expand the stochastic control families requested on the command line into K named
    # draws. Anything that is not a stochastic control passes through untouched.
    n_control_draws = max(1, int(args.n_control_draws))
    add_dirs = expand_add_directions(args.add_directions, n_control_draws)
    # Matched on the EXPANDED direction IDENTITIES, not by substring on the raw spec string: the
    # old `any(d in args.add_directions ...)` test was a substring match on an incidental spelling
    # (a family named `orthogonalized` would have set it, and one reached only through the
    # expansion would not).
    requested_stochastic = sorted({split_direction_name(d)[0] for d in add_dirs}
                                  & set(STOCHASTIC_CONTROLS))
    control_underpowered = (n_control_draws < MIN_CONTROL_DRAWS_FOR_BAND
                            and bool(requested_stochastic))
    if control_underpowered:
        print(f"[patch] WARNING (T9a): --n-control-draws={n_control_draws} < "
              f"{MIN_CONTROL_DRAWS_FOR_BAND}; the between-draw sd this run reports is itself too "
              f"noisy to be used as a control band.")

    # T10: state the readout/window overlap in the run metadata BEFORE any rows are written, so a
    # reader of the artifact does not have to re-derive it. The rule comes from
    # ds_common.patch_layer_sweep; see readout_window_flags.
    overlap = {wn: readout_window_flags(dc, wl, readout_layers) for wn, wl in windows.items()}
    n_bad = sum(1 for f in overlap.values() if f["readout_inside_patched_window"])
    print(f"[patch] T10 readout guard: {n_bad}/{len(windows)} windows contain at least one "
          f"readout layer; those cells are flagged readout_inside_patched_window=True and are "
          f"tautological (zero propagation), not evidence of an effect.")

    # `whole_answer` is a SCORING mode, not an id-SELECTION mode, so the id pair is still built
    # under `primary` -- exactly as score_behavior.py:391 does it. Those ids remain in use for the
    # per-layer LOGIT LENS (`ll|L*|boombness`), which reads an intermediate hidden state through
    # the unembedding and has no continuation to teacher-force; and `readout_id_pair`'s metadata
    # (which variants are single-token, which first-ids were rejected) is the evidence that
    # motivated whole_answer, so it is worth recording on every run. Passing "whole_answer"
    # straight through would raise `unknown readout id mode` -- deliberately, since that is the
    # one-of-two-paths slip that killed job 764743.
    # NOT rows[0]: the pair is a property of the SLICE, checked over every row (see the helper).
    concept, codeword = assert_single_concept_codeword_pair(rows)
    concept_ids, codeword_ids, id_meta = sg.readout_id_pair(
        lm.tokenizer, concept, codeword,
        mode=("primary" if args.readout_ids == "whole_answer" else args.readout_ids))
    # WHOLE-ANSWER variant sets, built by ONE rule for every option so the count is equal by
    # construction (2 each) rather than by tokenizer luck.
    sem_variants = {"concept": sg.answer_variants(concept, True),
                    "codeword": sg.answer_variants(codeword, True)}
    print(f"[patch] semantic readout={args.readout_ids!r} prefix={args.answer_prefix!r} "
          f"variants={sem_variants}")
    run.note(readout_layers=readout_layers, windows={k: v for k, v in windows.items()},
             alphas=alphas, concept_token_ids=concept_ids, codeword_token_ids=codeword_ids,
             readout_ids=id_meta, fit_dir=args.fit_dir,
             row_schema_version=ROW_SCHEMA_VERSION,
             semantic_readout_mode=args.readout_ids,
             answer_prefix=args.answer_prefix,
             semantic_variants=sem_variants,
             whole_answer_max_batch=WHOLE_ANSWER_MAX_BATCH,
             min_option_mass=args.min_option_mass,
             n_control_draws=n_control_draws, add_directions_expanded=add_dirs,
             control_draw_seed_stride=CONTROL_DRAW_SEED_STRIDE,
             # METADATA IS WRITTEN BEFORE ANY ROW, so this can only be the REQUEST. It is named
             # for what it is; the flag derived from the draws actually achieved is
             # `control_draws_underpowered` in summary.json, which is the one to read (T9b).
             control_draws_underpowered_as_requested=control_underpowered,
             readout_window_overlap={wn: {k: v for k, v in f.items()
                                          if not k.startswith("boombness|")}
                                     for wn, f in overlap.items()})
    print(f"[patch] model={lm.model_id} readout_layers={readout_layers} windows={len(windows)}")

    total = 0
    option_mass: Dict[str, List[float]] = collections.defaultdict(list)
    band_draw_counts: List[int] = []
    family_accounting = []          # A11-11: the truncation was never recorded anywhere
    for pair_name, (donor_cond, recip_cond) in PAIRS.items():
        eligible = [f for f, d in sorted(by_family.items())
                    if donor_cond in d and recip_cond in d]
        # AUDIT 11 (A11-10): this was `eligible[:n_families]`. `family_id` is PREFIXED BY DOMAIN and
        # the list is sorted, so a plain head-truncation selects whole domains in alphabetical order
        # -- the committed G1 pilot's 8 families came from 2 of 6 domains, and the reported interval
        # ("+57% to +105%") therefore treats 2 domains as 8 independent units. Round-robin over
        # domains instead, so a truncated sample spans the domain space.
        by_dom = collections.defaultdict(list)
        for f in eligible:
            by_dom[by_family[f][recip_cond].get("domain")].append(f)
        fams, doms = [], sorted(by_dom, key=str)
        i = 0
        while len(fams) < min(args.n_families, len(eligible)):
            d = doms[i % len(doms)]
            if by_dom[d]:
                fams.append(by_dom[d].pop(0))
            elif all(not by_dom[x] for x in doms):
                break
            i += 1
        n_dom_used = len({by_family[f][recip_cond].get("domain") for f in fams})
        print(f"[patch] pair={pair_name} families={len(fams)} of {len(eligible)} eligible, "
              f"spanning {n_dom_used} domain(s) (round-robin; head-truncation gave "
              f"{len({by_family[f][recip_cond].get('domain') for f in eligible[:args.n_families]})})")
        ledger_note = {"pair": pair_name, "n_eligible": len(eligible), "n_used": len(fams),
                       "n_domains": n_dom_used}
        family_accounting.append(ledger_note)
        for fam in fams:
            recip = by_family[fam][recip_cond]
            donor = by_family[fam][donor_cond]
            # Cross-fit: score with directions fitted on the OTHER split.
            other = "heldout" if recip["split"] == "dev" else "dev"
            payload = fitted.get(other) or fitted[recip["split"]]
            dirs: Dict[str, Dict[int, torch.Tensor]] = {
                k: payload[k] for k in ("d_surface", "d_context", "d_naive", "d_inter")
            }
            # T9a: K INDEPENDENT draws per stochastic control family, not one. Draw k uses seed
            # base (args.seed + k*CONTROL_DRAW_SEED_STRIDE), so draw 0 is bit-identical to the
            # pre-fix single vector and the old numbers survive as one member of the new band.
            # The draws are deliberately the SAME across families and domains: a control draw is
            # a fixed axis whose effect we want measured over the whole bank, and the quantity
            # T9a says was missing is the variance BETWEEN axes, which only per-draw replication
            # can produce.
            dirs.update(build_control_directions(sg, payload["d_surface"], args.seed,
                                                 n_control_draws))
            assert_control_draws_consistent(add_dirs, dirs)
            # Dose scale, per direction and per layer. estimate_directions stores UNIT vectors
            # and keeps the effect size in `gap`, so `h += alpha * d_unit` would treat alpha as
            # an absolute residual-space magnitude. The measured gaps are ||d_surface|| ~ 8.6 at
            # L12 and ~27 at L24, so the nominal sweep alpha<=8 would inject well under ONE
            # natural gap while the transplant arm moves the full donor-recipient distance —
            # and the run would then report "adding the direction does nothing" as an artifact
            # of the dose, which is exactly the false negative this gate must not produce.
            # So alpha is expressed in GAP UNITS: alpha=1 means "one diff-of-means".
            # Controls are scaled by the SAME gap so they stay norm-matched to the real arm.
            gaps = payload.get("gap", {})
            scales: Dict[str, Dict[int, float]] = {}
            for dname in dirs:
                src = dname if dname in gaps else "d_surface"
                scales[dname] = {L: float(gaps.get(src, {}).get(L, 1.0))
                                 for L in dirs[dname]}
            total += run_pair(lm, dc, pc, donor, recip, windows,
                              args.scopes.split(","), alphas, dirs, readout_layers,
                              concept_ids, codeword_ids, run, ledger, pair_name,
                              do_transplant=not args.no_transplant,
                              add_dirs=add_dirs,
                              scales=scales, dose_unit=args.dose_unit,
                              semantic_mode=args.readout_ids,
                              answer_prefix=args.answer_prefix,
                              sem_variants=sem_variants,
                              option_mass=option_mass,
                              band_draw_counts=band_draw_counts)
            print(f"  {fam[:60]} -> {total} rows")

    # -- C-6 TAIL GATE ------------------------------------------------------- #
    # A log-odds between two options is a decision margin ONLY if the options are plausibly what
    # the model is about to say. On the committed baseline the pair held a MEDIAN 5.6e-06 of
    # next-token mass with 0 of 516 rows above 1%, and NOTHING recorded it -- which is how G1's
    # +68%-of-span headline came to be an ordering inside a 1e-5 tail. It is recorded per row now,
    # summarised per (readout, query_kind, intervention) here, and FATAL by default on the
    # no-intervention buckets.
    # The gating buckets are IDENTITIES derived from this run's own --query-kind, so their
    # ABSENCE is a gate failure rather than an empty loop (see option_mass_gate).
    gating_buckets = [semantic_mass_bucket(args.query_kind, iv) for iv in GATED_INTERVENTIONS]
    mass_summary, tail_fail = option_mass_gate(option_mass, args.min_option_mass, gating_buckets)
    for bucket, st in sorted(mass_summary.items()):
        print(f"[patch] option mass {bucket}: n={st['n']} median={st['median']:.4g} "
              f"max={st['max']:.4g} frac>1%={st['frac_above_1pct']:.3f} "
              f"{'OK' if st['reportable'] else 'BELOW GATE'}"
              f"{'' if st['gates_the_run'] else ' (not gated: intervened arm)'}")

    run.finish(summary={"model": lm.model_id, "n_rows": total, "pairs": list(PAIRS),
                        "scopes_requested": args.scopes.split(","),
                "family_accounting": family_accounting, "alphas": alphas,
                        "readout_layers": readout_layers, "windows": sorted(windows),
                        "n_control_draws": n_control_draws,
                        # RUN-LEVEL FLAG, DERIVED FROM WHAT WAS ACTUALLY DRAWN. `n_control_draws`
                        # is the request; a cell can end with fewer after a ledgered failure, and
                        # a summary that reported only the request would certify a band that no
                        # cell achieved.
                        "control_draws_underpowered": control_draws_underpowered(
                            n_control_draws, band_draw_counts, bool(requested_stochastic)),
                        "control_draws_underpowered_as_requested": control_underpowered,
                        "n_band_cells": len(band_draw_counts),
                        "n_control_draws_observed_min": (min(band_draw_counts)
                                                         if band_draw_counts else None),
                        "n_control_draws_observed_max": (max(band_draw_counts)
                                                         if band_draw_counts else None),
                        "n_band_cells_single_draw": sum(1 for k in band_draw_counts if k < 2),
                        "n_band_cells_underpowered": sum(
                            1 for k in band_draw_counts if k < MIN_CONTROL_DRAWS_FOR_BAND),
                        "min_control_draws_for_band": MIN_CONTROL_DRAWS_FOR_BAND,
                        "row_schema_version": ROW_SCHEMA_VERSION,
                        "semantic_readout_mode": args.readout_ids,
                        "answer_prefix": args.answer_prefix,
                        "option_mass": mass_summary,
                        "option_mass_gating_buckets": gating_buckets,
                        "min_option_mass": args.min_option_mass,
                        "option_mass_gate": ("PASS" if not tail_fail else
                                             "OVERRIDDEN — NOT REPORTABLE: " + "; ".join(tail_fail)),
                        "windows_with_readout_inside": sorted(
                            wn for wn, f in overlap.items()
                            if f["readout_inside_patched_window"]),
                        "query_kind": args.query_kind}, ledger=ledger)
    print(f"[patch] {total} rows -> {run.path}")
    print(f"[patch] failures: {ledger.as_dict()['failure_reasons']}")

    # THE GATE FIRES *AFTER* run.finish(), DELIBERATELY (score_behavior.py tick 27): a gate placed
    # above finish() throws away the very evidence that documents the failure. The rows are
    # written and the healthy buckets are usable; the process still exits NON-ZERO so that
    # DONE.json plus a row count cannot be mistaken for success.
    if tail_fail and not args.allow_tail_readout:
        print("[patch] TAIL GATE FAILED — the run is written and its healthy readouts are usable, "
              "but these are NOT reportable:", file=sys.stderr)
        for t in tail_fail:
            print(f"  - {t}", file=sys.stderr)
        print(f"[patch] readout mode={args.readout_ids!r} prefix={args.answer_prefix!r}. "
              f"Pass --allow-tail-readout to accept deliberately.", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
