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
  p_concept / p_codeword  next-token mass on the two words (the safe semantic readout; the
                          `semantic_one_word` query makes the next token BE the answer)
  boombness               <h, d_surface> at the readout layers, measured UNDER the intervention
  logit-lens              logit(concept) - logit(codeword) at the readout layers
  comprehension           the same next-token readout on the `comprehension_usage` query
  generation/ASR          only with --generate, on a subset, judged downstream

TWO DEFECTS FOUND IN THE 2026-08-18 AUDIT, BOTH FIXED HERE
----------------------------------------------------------
T9a  THE CONTROL "CI" WAS A SINGLE DRAW DRESSED UP AS A BAND. The `random` and `orthogonal`
     control directions were built once per layer as `seed=args.seed + L`, i.e. ONE vector per
     layer reused across every family and every domain. The domain bootstrap downstream then
     resampled that one vector 24 times, so the interval it printed contained prompt- and
     domain-level variance and exactly ZERO direction-level variance: the quantity the control
     is supposed to bound (how much a random axis of this norm moves the readout) was never
     varied at all. Retraction #7 established the same failure for the G4 steering band, where
     the BETWEEN-DRAW sd was 0.0301 — larger than several effects that had been called
     "outside the control band" — and the conclusion was never propagated to this module.
     FIX: `--n-control-draws` (default 12) independent draws per control family, each row
     tagged with `control_draw`/`n_control_draws`, plus an explicit per-cell band row
     (`intervention="add_control_band"`) carrying the mean AND the between-draw sd under
     `between_draw_sd|<metric>`. Draw 0 keeps the historical seed (`args.seed + L`) so the old
     numbers reappear as one member of the new band rather than being silently replaced.

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


def readout_window_flags(dc, wlayers: Sequence[int],
                         readout_layers: Sequence[int]) -> Dict[str, object]:
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
    return {
        "readout_inside_patched_window": bool(inside),
        "readout_layers_inside_window": inside,
        "readout_layers_valid": valid,
        "n_readout_layers_inside_window": len(inside),
    }


def per_layer_inside_flags(readout_layers: Sequence[int],
                           inside: Sequence[int]) -> Dict[str, bool]:
    """Per-metric companion flags so a single readout column can be filtered on its own."""
    ins = set(int(x) for x in inside)
    return {f"boombness|L{int(R)}|inside_patched_window": int(R) in ins for R in readout_layers}


def between_draw_band(recs: Sequence[Dict[str, float]]) -> Dict[str, float]:
    """Mean and BETWEEN-DRAW sd of every numeric readout key across independent control draws.

    This is the number T9a says must exist and be stated. With one draw it is undefined, and the
    pre-fix code had exactly one draw per layer for the whole run — so the "control band" the
    bootstrap printed was a band over prompts and domains around a single fixed vector. sd is the
    sample sd (ddof=1); with n<2 it is reported as None rather than 0.0, because 0.0 would read
    as "no direction-level variance" instead of "not measured".
    """
    keys = [k for k in recs[0] if all(isinstance(r.get(k), (int, float)) and
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
            probe_pos: int) -> Dict[str, float]:
    """One patched forward -> next-token semantics + boombness + logit lens at `probe_pos`.

    `cap` must already be entered, AFTER the patch contexts, so its hooks see patched values.
    """
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
    rec: Dict[str, float] = {
        "logp_concept": lse_c, "logp_codeword": lse_w,
        "semantic_logodds": lse_c - lse_w,
        "p_concept": float(torch.tensor(lse_c).exp()),
        "p_codeword": float(torch.tensor(lse_w).exp()),
        "semantic_margin_p_diff": float(torch.tensor(lse_c).exp() - torch.tensor(lse_w).exp()),
    }
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
             dose_unit: str = "gap") -> int:
    """Every intervention for one donor/recipient family. Returns rows written."""
    try:
        _, d_ids, d_last, _, d_nsub = resolve_occurrences(dc, lm.tokenizer, donor)
        _, r_ids, r_last, _, r_nsub = resolve_occurrences(dc, lm.tokenizer, recip)
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
    )

    # T10: resolve the readout/window overlap ONCE per window, from ds_common.patch_layer_sweep.
    # "" is the no-window case (baseline / donor ceiling): nothing is patched, so nothing is
    # compromised, but the flag is still emitted so every row is self-describing.
    wflags = {wn: readout_window_flags(dc, wl, readout_layers) for wn, wl in windows.items()}
    wflags[""] = readout_window_flags(dc, [], readout_layers)
    for wn, f in wflags.items():
        f.update(per_layer_inside_flags(readout_layers, f["readout_layers_inside_window"]))

    n = 0
    # -- baseline (no intervention) ------------------------------------------ #
    with contextlib.ExitStack() as st:
        cap = st.enter_context(BlockCapture(lm.model, readout_layers))
        rec = readout(lm, r_ids, cap, concept_ids, codeword_ids, readout_layers, d_surface, probe_pos)
    run.log_row({**base, "intervention": "none", "scope": "", "window": "", "alpha": 0.0,
                 "direction": "", **wflags[""], **rec})
    n += 1

    # -- donor ceiling: what the readout looks like on the donor prompt itself - #
    with contextlib.ExitStack() as st:
        cap = st.enter_context(BlockCapture(lm.model, readout_layers))
        rec = readout(lm, d_ids, cap, concept_ids, codeword_ids, readout_layers, d_surface, probe_pos)
    run.log_row({**base, "intervention": "donor_ceiling", "scope": "", "window": "", "alpha": 0.0,
                 "direction": "", **wflags[""], **rec})
    n += 1

    # -- self-swap no-op assertion (the house invariant, checked live) --------- #
    recip_hs = forward_hidden(lm, r_ids)
    all_layers = list(range(lm.num_layers))
    src_self = {L: recip_hs[L + 1, r_last, :].clone() for L in all_layers}
    with contextlib.ExitStack() as st:
        st.enter_context(pc.ComponentOutSwap(lm.model, r_last, src_self, component="resid_post"))
        cap = st.enter_context(BlockCapture(lm.model, readout_layers))
        rec_self = readout(lm, r_ids, cap, concept_ids, codeword_ids, readout_layers, d_surface, probe_pos)
    run.log_row({**base, "intervention": "self_swap_noop_check", "scope": "all", "window": "all",
                 "alpha": 0.0, "direction": "", **wflags["all"], **rec_self})
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
                                      readout_layers, d_surface, probe_pos)
                except Exception as e:
                    ledger.fail(f"transplant:{type(e).__name__}", recip["prompt_id"])
                    continue
                run.log_row({**base, "intervention": "transplant", "scope": scope,
                             "window": wname, "n_positions": len(pos), "alpha": 0.0,
                             "direction": "", **wflags[wname], **rec})
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
                                          readout_layers, d_surface, probe_pos)
                    except Exception as e:
                        ledger.fail(f"add:{type(e).__name__}", recip["prompt_id"])
                        continue
                    eff = [round(a, 4) for (_, _, _, a) in patches]
                    fam_name, draw = split_direction_name(dname)
                    run.log_row({**base, "intervention": "add", "scope": scope, "window": wname,
                                 "n_positions": len(pos), "alpha": alpha,
                                 # `direction` stays the FAMILY name so every downstream filter
                                 # written against the pre-fix artifacts (direction == "random")
                                 # keeps selecting the right rows; the draw index is a new column.
                                 "direction": fam_name, "direction_draw_name": dname,
                                 "control_draw": draw, "is_control_draw": draw is not None,
                                 "dose_unit": dose_unit,
                                 "effective_alpha_min": min(eff), "effective_alpha_max": max(eff),
                                 **wflags[wname], **rec})
                    n += 1
                    if draw is not None:
                        band[(scope, wname, float(alpha), fam_name)].append(rec)

    # -- T9a control band: one row per cell, across the independent draws ------ #
    for (scope, wname, alpha, fam_name), recs in sorted(band.items(), key=lambda kv: str(kv[0])):
        agg = between_draw_band(recs)
        run.log_row({**base, "intervention": "add_control_band", "scope": scope, "window": wname,
                     "alpha": alpha, "direction": fam_name, "control_draw": None,
                     "is_control_draw": True, "n_control_draws": len(recs),
                     "dose_unit": dose_unit, **wflags[wname], **agg})
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
    ap.add_argument("--readout-ids", default="primary", choices=["primary", "full_word"])
    ap.add_argument("--dose-unit", default="gap", choices=["gap", "absolute"],
                    help="'gap' (default): alpha is in units of the layer's diff-of-means norm, "
                         "so alpha=1 injects one natural gap. 'absolute': alpha is a raw "
                         "residual-space magnitude on a unit vector (the old, badly-scaled "
                         "behaviour; kept only to reproduce it).")
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--seed", type=int, default=20260816)
    ap.add_argument("--tag", default="smoke")
    args = ap.parse_args()
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
    control_underpowered = (n_control_draws < 10 and
                            any(d in args.add_directions for d in STOCHASTIC_CONTROLS))
    if control_underpowered:
        print(f"[patch] WARNING (T9a): --n-control-draws={n_control_draws} < 10; the between-draw "
              f"sd this run reports is itself too noisy to be used as a control band.")

    # T10: state the readout/window overlap in the run metadata BEFORE any rows are written, so a
    # reader of the artifact does not have to re-derive it. The rule comes from
    # ds_common.patch_layer_sweep; see readout_window_flags.
    overlap = {wn: readout_window_flags(dc, wl, readout_layers) for wn, wl in windows.items()}
    n_bad = sum(1 for f in overlap.values() if f["readout_inside_patched_window"])
    print(f"[patch] T10 readout guard: {n_bad}/{len(windows)} windows contain at least one "
          f"readout layer; those cells are flagged readout_inside_patched_window=True and are "
          f"tautological (zero propagation), not evidence of an effect.")

    concept_ids, codeword_ids, id_meta = sg.readout_id_pair(
        lm.tokenizer, rows[0]["concept"], rows[0]["codeword"], mode=args.readout_ids)
    run.note(readout_layers=readout_layers, windows={k: v for k, v in windows.items()},
             alphas=alphas, concept_token_ids=concept_ids, codeword_token_ids=codeword_ids,
             readout_ids=id_meta, fit_dir=args.fit_dir,
             n_control_draws=n_control_draws, add_directions_expanded=add_dirs,
             control_draw_seed_stride=CONTROL_DRAW_SEED_STRIDE,
             control_draws_underpowered=control_underpowered,
             readout_window_overlap={wn: {k: v for k, v in f.items()
                                          if not k.startswith("boombness|")}
                                     for wn, f in overlap.items()})
    print(f"[patch] model={lm.model_id} readout_layers={readout_layers} windows={len(windows)}")

    total = 0
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
                              scales=scales, dose_unit=args.dose_unit)
            print(f"  {fam[:60]} -> {total} rows")

    run.finish(summary={"model": lm.model_id, "n_rows": total, "pairs": list(PAIRS),
                        "scopes_requested": args.scopes.split(","),
                "family_accounting": family_accounting, "alphas": alphas,
                        "readout_layers": readout_layers, "windows": sorted(windows),
                        "n_control_draws": n_control_draws,
                        "control_draws_underpowered": control_underpowered,
                        "windows_with_readout_inside": sorted(
                            wn for wn, f in overlap.items()
                            if f["readout_inside_patched_window"]),
                        "query_kind": args.query_kind}, ledger=ledger)
    print(f"[patch] {total} rows -> {run.path}")
    print(f"[patch] failures: {ledger.as_dict()['failure_reasons']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
