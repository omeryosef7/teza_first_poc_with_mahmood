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
    )

    n = 0
    # -- baseline (no intervention) ------------------------------------------ #
    with contextlib.ExitStack() as st:
        cap = st.enter_context(BlockCapture(lm.model, readout_layers))
        rec = readout(lm, r_ids, cap, concept_ids, codeword_ids, readout_layers, d_surface, probe_pos)
    run.log_row({**base, "intervention": "none", "scope": "", "window": "", "alpha": 0.0,
                 "direction": "", **rec})
    n += 1

    # -- donor ceiling: what the readout looks like on the donor prompt itself - #
    with contextlib.ExitStack() as st:
        cap = st.enter_context(BlockCapture(lm.model, readout_layers))
        rec = readout(lm, d_ids, cap, concept_ids, codeword_ids, readout_layers, d_surface, probe_pos)
    run.log_row({**base, "intervention": "donor_ceiling", "scope": "", "window": "", "alpha": 0.0,
                 "direction": "", **rec})
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
                 "alpha": 0.0, "direction": "", **rec_self})
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
                             "direction": "", **rec})
                n += 1

    # -- 5.2 additive direction ----------------------------------------------- #
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
                    run.log_row({**base, "intervention": "add", "scope": scope, "window": wname,
                                 "n_positions": len(pos), "alpha": alpha, "direction": dname,
                                 "dose_unit": dose_unit,
                                 "effective_alpha_min": min(eff), "effective_alpha_max": max(eff),
                                 **rec})
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

    concept_ids, codeword_ids, id_meta = sg.readout_id_pair(
        lm.tokenizer, rows[0]["concept"], rows[0]["codeword"], mode=args.readout_ids)
    run.note(readout_layers=readout_layers, windows={k: v for k, v in windows.items()},
             alphas=alphas, concept_token_ids=concept_ids, codeword_token_ids=codeword_ids,
             readout_ids=id_meta, fit_dir=args.fit_dir)
    print(f"[patch] model={lm.model_id} readout_layers={readout_layers} windows={len(windows)}")

    total = 0
    for pair_name, (donor_cond, recip_cond) in PAIRS.items():
        fams = [f for f, d in sorted(by_family.items())
                if donor_cond in d and recip_cond in d][:args.n_families]
        print(f"[patch] pair={pair_name} families={len(fams)}")
        for fam in fams:
            recip = by_family[fam][recip_cond]
            donor = by_family[fam][donor_cond]
            # Cross-fit: score with directions fitted on the OTHER split.
            other = "heldout" if recip["split"] == "dev" else "dev"
            payload = fitted.get(other) or fitted[recip["split"]]
            dirs: Dict[str, Dict[int, torch.Tensor]] = {
                k: payload[k] for k in ("d_surface", "d_context", "d_naive", "d_inter")
            }
            dirs["random"] = {L: sg.random_control_direction(v, seed=args.seed + L)
                              for L, v in payload["d_surface"].items()}
            dirs["orthogonal"] = {L: sg.orthogonal_control_direction(v, seed=args.seed + L)
                                  for L, v in payload["d_surface"].items()}
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
                              add_dirs=args.add_directions.split(","),
                              scales=scales, dose_unit=args.dose_unit)
            print(f"  {fam[:60]} -> {total} rows")

    run.finish(summary={"model": lm.model_id, "n_rows": total, "pairs": list(PAIRS),
                        "scopes": args.scopes.split(","), "alphas": alphas,
                        "readout_layers": readout_layers, "windows": sorted(windows),
                        "query_kind": args.query_kind}, ledger=ledger)
    print(f"[patch] {total} rows -> {run.path}")
    print(f"[patch] failures: {ledger.as_dict()['failure_reasons']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
