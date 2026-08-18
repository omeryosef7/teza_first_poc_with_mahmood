"""surgical_knockout.py — plan §10.1/§10.2: cut the edges that actually carry the meaning.

MOTIVATED DIRECTLY BY GATE G1. The §5 pilot showed the doublespeak reading is driven by the
DEMONSTRATION positions, not by the codeword token's own representation: transplanting the demos
moves the semantic readout +71–84% of the baseline→ceiling span, while transplanting the query
token moves it ~76% the WRONG way. That says the codeword's meaning is *retrieved from the
demonstration block at answer time* rather than stored in the codeword token.

This module tests that directly, and surgically. If the meaning is retrieved by attention from the
final codeword token to the demonstration tokens, then cutting exactly those edges should collapse
the semantic readout — and cutting the same NUMBER of other edges should not.

TWO INGREDIENTS, BOTH ALREADY BUILT AND VERIFIED
  * `dominance.py` (ported from the hijacking paper) ranks edges: `D_dir[h, src]` is how much of
    the Boombness arriving at the final codeword token was supplied by source position `src`
    through head `h`. That is what makes this *surgical* rather than "ablate the demo block and
    report that something happened".
  * `pair_common.AttentionKnockout` cuts specific (query_pos → key_pos) edges per layer and head.
    It REQUIRES `attn_implementation="eager"`; under SDPA a custom 4-D mask is silently ignored and
    the knockout becomes a no-op that still reports a number. The loader here forces eager and the
    self-check below would catch it anyway.

CONTROLS (plan §10.1 asks for all of these, and they are the difference between a result and a
story):
  `topk_demo`        cut the k highest-|D_dir| demonstration edges          — the hypothesis
  `random_demo`      cut k RANDOM demonstration edges                       — is it these edges?
  `bottomk_demo`     cut the k lowest-|D_dir| demonstration edges           — is the ranking real?
  `random_nondemo`   cut k random edges to NON-demonstration positions      — is it the demos?
  `same_head_random` cut k edges in the SAME heads but random positions     — head or position?
  `all_demo`         cut every demonstration edge                           — the ceiling
  `none`             no intervention                                        — the floor

Every arm cuts the SAME NUMBER of edges except `all_demo` and `none`, which is what makes them
comparable; the count is recorded per row so that can be checked rather than assumed.
"""
from __future__ import annotations

import argparse
import collections
import contextlib
import json
import math
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_DIR, FailureLedger, RunDir, ds, pair, read_jsonl, seed_everything  # noqa: E402
import signals as sg  # noqa: E402
from dominance import dominance_at  # noqa: E402
from extract_boombness import resolve_occurrences  # noqa: E402

DEFAULT_BANK = os.path.join(DATA_DIR, "boombness_prompt_bank.jsonl")
ARMS = ("none", "topk_demo", "bottomk_demo", "random_demo", "random_nondemo",
        "same_head_random", "all_demo", "positive_control",
        "all_layers_demo", "no_demo_text",
        # edge-count-matched pair added 2026-08-17 to identify depth-redundancy vs edge count
        "subsampled_all_layers_demo", "dense_two_layer")

# THE TWO DYNAMIC-RANGE CONTROLS THE FIRST VERSION LACKED.
# `positive_control` (block every pre-query key at the CHOSEN layers) turned out to move the
# readout LESS than `all_demo`, so it established no dynamic range and made the §10 null
# uninterpretable. Two stronger ceilings are now measured on every run:
#   all_layers_demo  cut query->demo edges at EVERY layer, not just the chosen few. If the
#                    demonstration influence is distributed over depth, a 2-layer cut can do
#                    nothing while an all-layer cut does a lot; that distinction is the whole
#                    question and the first design could not see it.
#   no_demo_text     evaluate the prompt with the demonstration block DELETED. This is the true
#                    ceiling: it is what "the demonstrations are not there" actually means, in
#                    text space, with no attention machinery involved. If even this does not move
#                    the readout, the readout is not measuring the demonstrations' influence and
#                    nothing else in §10 can be interpreted.

# POSITIVE CONTROL — the arm that makes a null interpretable.
# `positive_control` blocks EVERY key before the query position, in every head, at the chosen
# layers. The final token is then left attending only to itself, which must move the readout
# enormously. If it does not, the knockout is not firing and every other arm's "no effect" is a
# statement about the hook, not about the model. The first knockout smoke returned deltas of
# <=0.12 log-odds with three arms at exactly 0.000, which is exactly the pattern a dead
# intervention produces, so this arm is now mandatory rather than optional.


# ---------------------------------------------------------------------------
# PURE SELECTION LOGIC. Factored out of main() on 2026-08-18 so the three
# selection defects below (T3/T7/T7b) are testable without a GPU or a model.
# ---------------------------------------------------------------------------


def choose_destinations(dst_mode: str, last_codeword_pos: int,
                        readout_pos: int) -> Tuple[List[int], int]:
    """Return (destinations_to_cut_into, destination_to_RANK_at).

    DEFECT T3, FIXED 2026-08-18. The previous code was::

        dsts = sorted({last[-1], readout_pos})
        dst  = dsts[0]                        # for ranking/reporting

    Under `--dst both` — the mode every reported G3 run used — `last[-1]` is the
    final codeword occurrence and `readout_pos` the last token, typically ~9
    tokens later, so `dsts[0]` is ALWAYS the codeword position. The knockout
    itself was already fixed to cut into both destinations (query_positions=dsts),
    but the RANKING was not: `dominance_at(..., dst=dst)` therefore scored how
    much Boombness flowed into token ~104 while the readout is at ~113. Since
    that ranking is what defines topk_demo / bottomk_demo / same_head_random,
    the entire "surgical, not ablate-everything" claim was ordered at the wrong
    token — exactly the destination this project already retracted (retraction
    #3) as fatal to all of §10. Observable consequence: the near-null
    topk-vs-bottomk contrast (-0.078 vs -0.00004) could not distinguish "the
    ranking is real and these edges do not matter" from "the ranking was
    measured at a token the readout does not read". Ranking now happens at
    `readout_pos` whenever the readout is among the destinations.
    """
    if dst_mode == "readout":
        dsts = [readout_pos]
    elif dst_mode == "codeword":
        dsts = [last_codeword_pos]
    elif dst_mode == "both":
        dsts = sorted({last_codeword_pos, readout_pos})
    else:
        raise ValueError(f"unknown dst mode {dst_mode!r}")
    rank_dst = last_codeword_pos if dst_mode == "codeword" else readout_pos
    return dsts, rank_dst


def choose_direction_split(available: Sequence[str], row_split: Optional[str]) -> Tuple[str, bool]:
    """Pick which fitted-direction split to rank a row with. Returns (split, is_self_fit).

    DEFECT T7, FIXED 2026-08-18. The previous code took the FIRST of
    ('dev', 'heldout') that existed on disk, `break`-ed, and then used that one
    direction for every row regardless of `row['split']`. 1272 of the bank's
    2352 rows are dev, so ~54% of rows had their edge ranking chosen IN-SAMPLE,
    while the all_demo / random_demo / random_nondemo control arms are
    direction-independent by construction. That handed an in-sample advantage
    to precisely the targeted arm of the G3 contrast, and because no
    `is_self_fit` field was emitted the affected rows could not even be filtered
    post hoc. Directions are now cross-fitted per row (score a dev row with the
    heldout fit and vice versa), falling back to the row's own split only when
    the other file is absent — and that residual case is flagged row-wise via
    `is_self_fit` so it is auditable rather than invisible.
    """
    avail = list(available)
    if not avail:
        raise ValueError("no fitted directions available")
    other = {"dev": "heldout", "heldout": "dev"}.get(str(row_split))
    if other in avail:
        return other, False
    if str(row_split) in avail:
        return str(row_split), True
    # Row split unknown / not one of dev|heldout: fall back deterministically and
    # mark it self-fit-unknown-conservatively (True) so it is never silently
    # counted as a clean cross-fit row.
    pick = sorted(avail)[0]
    return pick, True


def select_families(rows: Sequence[dict], n_families: int) -> Tuple[List[dict], dict]:
    """Select `n_families` DISTINCT families, round-robin over domain AND split.

    DEFECT T7b, FIXED 2026-08-18; the fix itself CORRECTED 2026-08-18 (below).

      (a) HEAD-TRUNCATION OF A DOMAIN-PREFIXED SORTED LIST — REAL, and the one
          thing that actually changed which prompts were measured. `family_id`
          carries its domain as a prefix and the bank is domain-ordered, so
          `rows[:n]` selects whole domains in alphabetical order. Recomputed
          from the bank on 2026-08-18 for the exact filter every reported G3 run
          used (query_kind=semantic_one_word, condition=natural_doublespeak,
          bank_block=core2x2, n_examples=4): the eligible pool is 12 rows over
          **6 domains**, and `rows[:6]` drew from only **3** of them. Same defect
          already fixed in aggressive_patching (audit A11-10), never ported here.

      (b) "--n-families COUNTED PROMPTS, NOT FAMILIES" — CLAIMED ON 2026-08-18
          AND **REFUTED** THE SAME DAY. The original note asserted that
          `--n-families 6` yielded "3 families x 2 example-counts ... effective
          G = 3". That is false on this bank. `family_id` is 1:1 with eligible
          rows here: the pool holds 12 rows / 12 distinct families at
          n_examples=4 (24 / 24 at n_examples=4,8), so `rows[:6]` returned 6
          rows AND 6 distinct families. Measured directly on the committed
          artifacts: dstfix and edgematch each carry 6 distinct `family_id`s
          over 3 domains. Effective G was **6, not 3**. Counting families rather
          than rows is still the right contract — it is a no-op on today's bank
          but stops silently mis-sizing G the moment a family gains a second
          eligible row — it just was not a live defect, and no G3 interval needs
          rescaling on account of (b).

    SPLIT COLLAPSE INTRODUCED BY THE (a) FIX, CAUGHT AND REPAIRED 2026-08-18.
    The first round-robin popped `by_dom[d].pop(0)`, i.e. the alphabetically
    first family of each domain. On this bank every domain holds exactly two
    eligible families, one dev and one heldout, and the dev one sorts first in
    all six domains — so the "fixed" selector returned **6 dev families and 0
    heldout**, where the pre-fix head-truncation had returned a balanced 3 dev /
    3 heldout (and the committed 60-row runs were 30/30). Stratifying on domain
    while de-stratifying on split is not an improvement: it deletes the held-out
    half of the sample outright, and it interacts badly with the T7 cross-fit
    (every row would take the heldout-fitted direction, leaving no dev-fitted
    row to compare against). Selection is now round-robin over domains that
    picks, within each domain, the family whose SPLIT is currently least
    represented, so the sample is balanced on both axes at once: 6 families / 6
    domains / 3 dev / 3 heldout.

    Families are the unit, all matching rows of a selected family are kept, and
    `family_accounting` records requested vs selected plus the full
    domain/family/split breakdown, so the effective G can never again be
    inferable only by reading the code.

    A CAVEAT `effective_G` CANNOT EXPRESS, recorded so nobody reads 6 as six
    independent semantic units: all 12 eligible rows share ONE (concept,
    codeword) pair. The families differ in domain dressing only, so the clusters
    have a common semantic cause and G=6 is an upper bound on the real number of
    independent units. `n_concept_codeword_pairs` is emitted for exactly this
    reason.
    """
    by_family: Dict[str, List[dict]] = collections.OrderedDict()
    for r in rows:
        by_family.setdefault(str(r["family_id"]), []).append(r)
    by_dom: Dict[str, List[str]] = collections.defaultdict(list)
    for fam in sorted(by_family):
        by_dom[str(by_family[fam][0].get("domain"))].append(fam)
    doms = sorted(by_dom)
    want = min(int(n_families), len(by_family))
    fam_split = {f: str(by_family[f][0].get("split")) for f in by_family}
    split_counts: Dict[str, int] = collections.Counter()
    fams: List[str] = []
    i = 0
    while len(fams) < want:
        d = doms[i % len(doms)]
        if by_dom[d]:
            # Within the domain take the family whose split is least represented so far;
            # ties break alphabetically so the whole selection stays deterministic. This is
            # what keeps the domain round-robin from silently collapsing onto one split.
            pick = min(by_dom[d], key=lambda f: (split_counts[fam_split[f]], f))
            by_dom[d].remove(pick)
            fams.append(pick)
            split_counts[fam_split[pick]] += 1
        elif all(not by_dom[x] for x in doms):
            break
        i += 1
    fams_set = set(fams)
    sel = [r for r in rows if str(r["family_id"]) in fams_set]
    head_fams = sorted({str(r["family_id"]) for r in list(rows)[:int(n_families)]})
    acct = {
        "unit": "family",
        "requested_n_families": int(n_families),
        "n_families_eligible": len(by_family),
        "n_families_selected": len(fams),
        "n_rows_selected": len(sel),
        "effective_G": len(fams),
        "selection": "round_robin_over_domains_split_balanced",
        "families_selected": sorted(fams),
        "domains_selected": sorted({str(r.get("domain")) for r in sel}),
        "n_domains_selected": len({str(r.get("domain")) for r in sel}),
        "families_per_domain": {d: sorted(f for f in fams
                                          if str(by_family[f][0].get("domain")) == d)
                                for d in sorted({str(by_family[f][0].get("domain")) for f in fams})},
        "rows_per_split": dict(collections.Counter(str(r.get("split")) for r in sel)),
        "rows_per_n_examples": dict(collections.Counter(int(r["n_examples"]) for r in sel)),
        "prior_head_truncation_would_give": {
            "n_rows": min(int(n_families), len(list(rows))),
            "n_families": len(head_fams),
            "n_domains": len({str(r.get("domain")) for r in list(rows)[:int(n_families)]}),
        },
        "families_per_split": {sp: sorted(f for f in fams if fam_split[f] == sp)
                               for sp in sorted({fam_split[f] for f in fams})},
        # All eligible families may share a single (concept, codeword) pair, in which case
        # effective_G overstates the number of independent semantic units. Emitted so the
        # reader of a results dir can see that without re-deriving it from the bank.
        "n_concept_codeword_pairs": len({(str(r.get("concept")), str(r.get("codeword")))
                                         for r in sel}),
        "prior_head_truncation_would_give_splits": dict(collections.Counter(
            str(r.get("split")) for r in list(rows)[:int(n_families)])),
        "note": "pre-2026-08-18 this was rows[:n_families]: head-truncated off a "
                "domain-prefixed sorted bank (real defect). The 'counted PROMPTS not "
                "families' half of the claim was refuted on 2026-08-18: family_id is 1:1 "
                "with eligible rows on this bank, so effective G was 6, not 3. The first "
                "round-robin fix then collapsed the sample to 6 dev / 0 heldout; selection "
                "is now balanced on domain and split simultaneously.",
    }
    return sel, acct


def demo_source_bound(dsts: Sequence[int]) -> int:
    """Exclusive upper bound on demonstration SOURCE positions (defect T3b).

    Pre-fix this bound was the ranking destination `dst`, which under --dst both was the
    final CODEWORD occurrence: every demonstration-block token between the codeword and the
    readout was silently dropped from the candidate edge set, so arms labelled "all demo
    edges" were missing a suffix of the block. Causality only forbids sources at or after the
    query position, so the bound is the LAST destination being cut into.
    """
    return max(dsts)


@torch.no_grad()
def semantic_logodds(lm, ids: List[int], c_ids: Sequence[int], w_ids: Sequence[int]) -> float:
    """The readout that G1 was decided on: log p(concept) - log p(codeword) at the answer position."""
    t = torch.tensor([ids], device=lm.model.device)
    logits = lm.model(input_ids=t, use_cache=False).logits[0, -1, :].float().cpu()
    lp = torch.log_softmax(logits, dim=-1)
    ci = torch.tensor(sorted(set(c_ids)), dtype=torch.long)
    wi = torch.tensor(sorted(set(w_ids)), dtype=torch.long)
    return float(lp[ci].logsumexp(0) - lp[wi].logsumexp(0))


def pick_edges(D_dir: Dict[int, torch.Tensor], demo_positions: Sequence[int],
               all_positions: Sequence[int], k: int, arm: str, rng,
               dsts_global: Sequence[int] = (), n_model_layers: int = 32,
               n_chosen_layers: int = 2) -> Dict[int, List[Tuple[int, int]]]:
    """Return {layer: [(head, src), ...]} for one arm. Every arm returns exactly k edges."""
    out: Dict[int, List[Tuple[int, int]]] = {}
    demo = set(demo_positions)
    for L, D in D_dir.items():
        nh, T = D.shape
        cand_demo = [(h, s) for h in range(nh) for s in range(T) if s in demo]
        cand_non = [(h, s) for h in range(nh) for s in range(T)
                    if s not in demo and s < T - 1]
        if arm == "all_layers_demo":
            out[L] = cand_demo          # caller widens the layer set for this arm
            continue
        if arm == "positive_control":
            # Exclude the destinations' own self-edges: blocking every key INCLUDING self makes
            # the whole softmax row -inf and the result is a degenerate uniform row, which is a
            # different (and uninterpretable) perturbation from "attend only to yourself".
            out[L] = [(h, s) for h in range(nh) for s in range(T)
                      if s < T - 1 and s not in set(dsts_global)]
            continue
        if arm == "all_demo":
            out[L] = cand_demo
            continue
        # EDGE-COUNT-MATCHED ARMS (audit B4a, 2026-08-17). `all_demo` (2 layers) and
        # `all_layers_demo` (32 layers) cut the SAME per-layer edge set, so layer spread and total
        # edge count move together by exactly 16x and the "distributed across depth" reading is not
        # identified: a plain total-edge threshold between 3552 and 56832 explains the data equally
        # well. These two arms break the tie by holding one factor fixed while moving the other.
        #   subsampled_all_layers_demo: 1/16 of the demo edges per layer, over ALL 32 layers
        #                               -> ~3552 total, same as all_demo, but spread over depth.
        #                               If this recovers ~84%, depth-redundancy is REAL.
        #   dense_two_layer:            all demo edges PLUS non-demo edges at 2 layers only, to
        #                               reach all_layers_demo's total at concentrated depth.
        #                               If this recovers ~84%, it was EDGE COUNT all along.
        if arm == "subsampled_all_layers_demo":
            # BUG FIXED 2026-08-17 (audit F1): the 1/16 was HARDCODED and is only correct when
            # num_layers/len(chosen_layers) == 16, i.e. exactly 2 chosen layers on a 32-layer model.
            # Under the script's own default --layers (4 layers) it silently produced HALF the
            # intended edges while still being labelled "edge-count-matched" — an arm whose entire
            # purpose is the edge-count match.
            n_keep = max(1, (len(cand_demo) * n_chosen_layers) // n_model_layers)
            out[L] = [cand_demo[i] for i in rng.permutation(len(cand_demo))[:n_keep]]
            continue
        if arm == "dense_two_layer":
            # BUG FIXED 2026-08-17 (audit F2). This asked for 16x the demo edges at the chosen
            # layers and SILENTLY TRUNCATED when the pool ran out — on the real run it delivered
            # 7,264 of a needed 56,832 (87% short) while still being reported as the layer-matched
            # dense arm. Two layers physically cannot hold 32 layers' worth of edges, so the arm is
            # INFEASIBLE at this layer count and must say so rather than quietly under-deliver:
            # an 8x-short arm licenses no conclusion about the edge-count-vs-depth tie.
            need = (n_model_layers // max(n_chosen_layers, 1)) * len(cand_demo)
            avail = len(cand_demo) + len(cand_non)
            if need > avail:
                raise ValueError(
                    f"dense_two_layer INFEASIBLE at layer {L}: needs {need} edges but only {avail} "
                    f"exist there ({len(cand_demo)} demo + {len(cand_non)} non-demo). Two layers "
                    f"cannot match an all-layer cut's edge count; widen --layers for this arm "
                    f"instead of silently cutting {100*avail/need:.0f}% of the target.")
            extra = [cand_non[i] for i in rng.permutation(len(cand_non))[:max(0, need - len(cand_demo))]]
            out[L] = cand_demo + extra
            continue
        if not cand_demo:
            out[L] = []
            continue
        if arm == "topk_demo":
            out[L] = sorted(cand_demo, key=lambda e: -abs(float(D[e[0], e[1]])))[:k]
        elif arm == "bottomk_demo":
            out[L] = sorted(cand_demo, key=lambda e: abs(float(D[e[0], e[1]])))[:k]
        elif arm == "random_demo":
            out[L] = [cand_demo[i] for i in rng.permutation(len(cand_demo))[:k]]
        elif arm == "random_nondemo":
            if not cand_non:
                out[L] = []
            else:
                out[L] = [cand_non[i] for i in rng.permutation(len(cand_non))[:k]]
        elif arm == "same_head_random":
            top = sorted(cand_demo, key=lambda e: -abs(float(D[e[0], e[1]])))[:k]
            heads = [h for h, _ in top]
            pool = [s for s in all_positions if s not in demo and s < D.shape[1] - 1]
            if not pool:
                out[L] = []
            else:
                out[L] = [(h, int(pool[rng.integers(len(pool))])) for h in heads]
        else:
            raise ValueError(f"unknown arm {arm!r}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", default=DEFAULT_BANK)
    ap.add_argument("--fit-dir", required=True)
    ap.add_argument("--model", default=None)
    ap.add_argument("--layers", default="8,12,18,24", help="layers to rank AND knock out")
    ap.add_argument("--topk", type=int, default=16, help="edges cut per layer per arm")
    ap.add_argument("--n-families", type=int, default=8)
    ap.add_argument("--n-examples", default="4,8")
    ap.add_argument("--query-kind", default="semantic_one_word")
    ap.add_argument("--condition", default="natural_doublespeak")
    ap.add_argument("--seed", type=int, default=20260816)
    ap.add_argument("--dst", default="readout", choices=["readout", "codeword", "both"],
                    help="WHICH DESTINATION the edges are cut into. This was a fatal design flaw "
                         "in the first version: it cut edges into the final CODEWORD occurrence "
                         "while the readout reads the next-token distribution at the LAST token, "
                         "typically 9 tokens later. Blocking attention arriving at a position the "
                         "readout does not directly depend on can only act indirectly, which is "
                         "why every arm read about zero. 'readout' (default) cuts into the "
                         "position actually being measured; 'codeword' reproduces the old, wrong "
                         "behaviour; 'both' cuts into each.")
    ap.add_argument("--demo-scope", default="codeword", choices=["codeword", "block"],
                    help="which source positions count as 'the demonstrations'. 'codeword' = the "
                         "demonstration CODEWORD occurrences only (the original scope). 'block' = "
                         "EVERY token of the demonstration block. The G3 result motivates this: "
                         "cutting all query->demo-codeword edges at every layer recovered only ~7%% "
                         "of the effect of deleting the demonstrations, which suggests the mapping "
                         "is carried by the PREDICATES ('exploded', 'defused') rather than by the "
                         "repeated codeword. 'block' is the direct test of that.")
    ap.add_argument("--tag", default="pilot")
    args = ap.parse_args()
    seed_everything(args.seed)

    import numpy as np
    rng = np.random.default_rng(args.seed)
    dc, pc = ds(), pair()
    want_n = {int(x) for x in args.n_examples.split(",")}
    eligible_rows = [r for r in read_jsonl(args.bank)
                     if r["query_kind"] == args.query_kind and r["condition"] == args.condition
                     and r["n_examples"] in want_n and r["bank_block"] == "core2x2"]
    # T7b: `--n-families` now counts DISTINCT families and the sample is drawn
    # round-robin over domains (see select_families).
    rows, family_accounting = select_families(eligible_rows, args.n_families)
    if not rows:
        raise SystemExit("no bank rows matched the selection filters")

    run = RunDir("surgical_knockout", args, tag=args.tag)
    ledger = FailureLedger()

    # eager is MANDATORY: under SDPA the 4-D mask is ignored and every knockout silently no-ops.
    lm = dc.load_model(args.model or dc.PRIMARY_MODEL, dtype=torch.float32,
                       attn_implementation="eager")
    run.note_bank(args.bank)
    run.note_model(lm.model_id, revision=lm.revision, dtype=str(lm.dtype),
                   attn_implementation="eager", num_layers=lm.num_layers,
                   note="eager required: AttentionKnockout is a no-op under SDPA")

    # T7: load EVERY available fit so each row can be ranked with the direction
    # fitted on the OTHER split (cross-fit). The old code loaded exactly one.
    fitted: Dict[str, dict] = {}
    for split in ("dev", "heldout"):
        p = os.path.join(args.fit_dir, f"directions_fit_{split}.pt")
        if os.path.exists(p):
            fitted[split] = torch.load(p, map_location="cpu", weights_only=False)
            run.note(**{f"direction_file_{split}": p})
    if not fitted:
        raise SystemExit(f"no directions_fit_*.pt under {args.fit_dir}")

    layers = [int(x) for x in args.layers.split(",")]
    d_surface_by_split = {
        sp: {L: pl["d_surface"][L] for L in layers if L in pl["d_surface"]}
        for sp, pl in fitted.items()
    }
    c_ids, w_ids, id_meta = sg.readout_id_pair(lm.tokenizer, rows[0]["concept"], rows[0]["codeword"])
    run.note(readout_ids=id_meta, layers=layers, topk=args.topk, arms=list(ARMS),
             demo_scope=args.demo_scope, family_accounting=family_accounting,
             direction_splits_available=sorted(fitted))
    print(f"[knockout] {len(rows)} prompts / {family_accounting['n_families_selected']} families "
          f"over {family_accounting['n_domains_selected']} domain(s), "
          f"layers={layers}, k={args.topk} edges/layer/arm")

    n = 0
    for row in rows:
        try:
            _, ids, last, _, _ = resolve_occurrences(dc, lm.tokenizer, row)
        except ValueError as e:
            ledger.fail(f"resolve:{e}", row["prompt_id"])
            continue
        # The destination MUST be the position the readout reads, or the intervention and the
        # measurement are about different tokens (see --dst).
        readout_pos = len(ids) - 1
        # T3: `dst` is the RANKING/reporting destination and must be the token the
        # readout actually reads (see choose_destinations); `dsts` is what gets cut.
        dsts, dst = choose_destinations(args.dst, last[-1], readout_pos)
        # T7: cross-fit the ranking direction on the row's own split.
        fit_split, is_self_fit = choose_direction_split(sorted(fitted), row.get("split"))
        d_surface = d_surface_by_split[fit_split]
        if args.demo_scope == "codeword":
            demo_pos = last[:-1]             # the demonstration codeword occurrences
        else:
            # Every token of the demonstration block. Located by character offset of the
            # recorded demo_block inside the TEMPLATED prompt, so it cannot drift from the
            # generator's own notion of what the demonstrations are.
            blk = row.get("demo_block") or ""
            if not blk:
                ledger.fail("no_demo_block", row["prompt_id"])
                continue
            templated = dc.apply_template(lm.tokenizer, row["full_prompt"])
            ci = templated.find(blk)
            if ci < 0:
                ledger.fail("demo_block_not_found_in_templated", row["prompt_id"])
                continue
            enc = lm.tokenizer(templated, add_special_tokens=False, return_offsets_mapping=True)
            lo, hi = ci, ci + len(blk)
            # DEFECT T3b, FIXED 2026-08-18. This filtered `i < dst` while `dst` was
            # the FINAL CODEWORD occurrence under --dst both, so every demonstration
            # token lying between the codeword and the readout was silently dropped
            # from the candidate edge set — the arms were then labelled "all demo
            # edges" while missing a suffix of the block. The bound must be the
            # LAST destination being cut into (causality only forbids sources at or
            # after the query position), which is `max(dsts)`.
            src_bound = demo_source_bound(dsts)
            demo_pos = [i for i, (a, b) in enumerate(enc["offset_mapping"])
                        if a >= lo and b <= hi and b > a and i < src_bound]
        if not demo_pos:
            ledger.fail(f"no_demo_positions:{args.demo_scope}", row["prompt_id"])
            continue

        try:
            dom = dominance_at(lm, ids, dst=dst, layers=layers, direction=d_surface,
                               check_invariants=True)
        except Exception as e:
            ledger.fail(f"dominance:{type(e).__name__}:{str(e)[:60]}", row["prompt_id"])
            continue

        base = {k: row[k] for k in ("prompt_id", "prompt_sha16", "family_id", "condition",
                                    "cell", "domain", "split", "n_examples", "query_kind")}
        base.update({"dst": dst, "dsts": dsts, "readout_pos": readout_pos,
                     "dst_mode": args.dst, "rank_dst": dst,
                     "codeword_last_pos": last[-1],
                     "directions_fitted_on": fit_split, "is_self_fit": is_self_fit,
                     "n_demo_positions": len(demo_pos), "seq_len": len(ids),
                     "demo_scope": args.demo_scope})

        for arm in ARMS:
            if arm == "none":
                val = semantic_logodds(lm, ids, c_ids, w_ids)
                run.log_row({**base, "arm": arm, "n_edges_cut": 0, "semantic_logodds": val})
                n += 1
                continue
            if arm == "no_demo_text":
                # The true ceiling: the same query with the demonstration block removed.
                q = row.get("final_query_text") or ""
                if not q:
                    ledger.fail("no_demo_text:missing_query", row["prompt_id"])
                    continue
                t2 = dc.apply_template(lm.tokenizer, q)
                ids2 = lm.tokenizer(t2, add_special_tokens=False)["input_ids"]
                val = semantic_logodds(lm, ids2, c_ids, w_ids)
                run.log_row({**base, "arm": arm, "n_edges_cut": -1,
                             "seq_len_used": len(ids2), "semantic_logodds": val})
                n += 1
                continue
            ALL_LAYER_ARMS = ("all_layers_demo", "subsampled_all_layers_demo")
            arm_layers = list(range(lm.num_layers)) if arm in ALL_LAYER_ARMS else layers
            dom_arm = dom["D_dir"]
            if arm in ALL_LAYER_ARMS:
                # D_dir was only computed at `layers`; for an all-layer cut we need an edge set
                # per layer, and the ranking is irrelevant because every demo edge is cut
                # (for the subsampled arm the edges are drawn at random, so also irrelevant).
                dom_arm = {L: dom["D_dir"][layers[0]] for L in arm_layers}
            edges = pick_edges(dom_arm, demo_pos, list(range(len(ids))),
                               args.topk, arm, rng, dsts_global=dsts,
                               n_model_layers=lm.num_layers, n_chosen_layers=len(layers))
            n_cut = sum(len(v) for v in edges.values())
            if n_cut == 0:
                ledger.fail(f"arm_{arm}:no_edges", row["prompt_id"])
                continue
            try:
                with contextlib.ExitStack() as st:
                    for L, es in edges.items():
                        if not es:
                            continue
                        # AttentionKnockout blocks (query_positions -> blocked_keys) per head.
                        by_head: Dict[int, List[int]] = collections.defaultdict(list)
                        for h, s in es:
                            by_head[h].append(s)
                        for h, srcs in by_head.items():
                            st.enter_context(pc.AttentionKnockout(
                                lm.model, [L], query_positions=dsts,
                                blocked_keys=sorted(set(srcs)), heads=[h]))
                    val = semantic_logodds(lm, ids, c_ids, w_ids)
            except Exception as e:
                ledger.fail(f"knockout_{arm}:{type(e).__name__}:{str(e)[:60]}", row["prompt_id"])
                continue
            run.log_row({**base, "arm": arm, "n_edges_cut": n_cut, "semantic_logodds": val})
            n += 1
        ledger.ok()

    run.finish(summary={"model": lm.model_id, "n_rows": n, "arms": list(ARMS),
                        "family_accounting": family_accounting,
                        "direction_splits_available": sorted(fitted),
                        "cross_fit_note": "edge ranking uses the direction fitted on the OTHER "
                                          "split; per-row is_self_fit flags any residual "
                                          "in-sample row",
                        "positive_control_note": "positive_control blocks every pre-query key in "
                                                 "every head; if its delta is small the knockout "
                                                 "is not firing and all other arms are void",
                        "layers": layers, "topk": args.topk,
                        "condition": args.condition, "query_kind": args.query_kind},
               ledger=ledger)
    print(f"[knockout] {n} rows -> {run.path}")
    print(f"[knockout] failures: {ledger.as_dict()['failure_reasons']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
