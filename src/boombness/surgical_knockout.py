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

THE READOUT — CORRECTION C-6, 2026-08-19. Every published G3 number was computed with
`semantic_logodds` below: `log p(concept) - log p(codeword)` over ONE leading-space token id per
side, at the last prompt token, with no forced answer position. That instrument is invalid, and
not by a little:

  * the two options together held a MEDIAN 5.6e-06 of the next-token mass (0 of 516 rows above
    1%), so every G3 verdict was an ordering inside a tail the model was never going to emit;
  * the model CAPITALISES a forced answer, and the capitalised codeword is MULTI-TOKEN
    (` Car` is the first subtoken of ` Carrot`), so no single-next-token readout can represent
    the model's preferred spelling of the codeword at all. Adding id variants makes it worse,
    not better: `bomb` has four single-token variants on Llama-3.1-8B and `carrot` exactly one.

This module now uses `signals.string_option_readout` — the SAME helper, called the SAME way as
`score_behavior.py --readout-ids whole_answer --answer-prefix "Answer:"` — which teacher-forces
each option's whole surface form over an identically-built variant set (2 per option, one rule).
On §4b that took the option mass from 1.7e-04 to 0.541, a 3,200x change, and flipped the sign of
the headline. `option_mass` is recorded PER ROW and gated per arm (see `option_mass_gate`).

Consequences for the destinations, which are what makes this module different from a scorer:
the whole-answer readout reads log-probabilities at the last CONTEXT position AND at every
answer token after it, and the context now ends with the answer prefix rather than with the
prompt. So both the ranking destination and the knockout's query set move — see
`choose_destinations` (T3) and `readout_query_positions` (C-6b). Cutting into the old position
while scoring at the new one is exactly the defect retraction #3 was declared for.
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
from ds_common import parse_enable_thinking as dc_parse_thinking  # noqa: E402
from common import (DATA_DIR, FailureLedger, RunDir, ds, pair, read_jsonl,  # noqa: E402
                    seed_everything, validate_direction_payload)
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


def normalize_answer_prefix(raw: str) -> str:
    """Shell-safe empty prefix, byte-identical to score_behavior.main()'s rule.

    The SLURM wrapper word-splits its args deliberately, so a quoted empty argument cannot
    survive the round trip: `--answer-prefix ""` silently swallows the NEXT flag. The three
    spellings below therefore mean "no prefix" here exactly as they do there. Kept as a named
    function so the two scripts can be shown to agree rather than assumed to.
    """
    return "" if str(raw).strip().lower() in ("none", "''", '""') else str(raw)


def readout_query_positions(dsts: Sequence[int], ctx_len: int,
                            max_answer_tokens: int) -> List[int]:
    """Every position the WHOLE-ANSWER readout reads a next-token distribution at.

    DEFECT C-6b — the destination set that T3 fixed is still incomplete once the readout stops
    being a single next token. `string_option_readout` teacher-forces `context + variant`, so
    the scored log-probabilities come from positions

        ctx_len-1                       -> predicts the variant's FIRST token
        ctx_len .. ctx_len+m-2          -> predict its remaining tokens

    Cutting attention only into `ctx_len-1` (which is what `query_positions=dsts` does) leaves
    every later answer token free to re-read the demonstration block directly, so a "cut the
    edges that carry the meaning" arm can be undone one token later by the very edges it cut.
    That is T3's failure mode — intervention and measurement at different tokens — displaced by
    one position rather than by nine. The knockout's query set must therefore span the whole
    answer window. Positions past the end of a shorter variant are simply skipped by
    `AttentionKnockout` (`qp >= am.shape[2]: continue`), so one generous range is correct for
    every variant and the arms stay edge-count-matched (the blocked KEY set is unchanged).

    THE WINDOW IS ADDED BY IDENTITY, NOT BY MODE. It is appended only when the readout
    destination `ctx_len-1` is actually one of `dsts`. `--dst codeword` exists to reproduce the
    retracted pre-T3 behaviour exactly; silently widening ITS query set to the answer window
    would make the reproduction arm a different intervention wearing the old flag's name — the
    one-of-two-paths shape, inverted. `readout` and `both` both contain the readout destination
    and both get the window.
    """
    if ctx_len <= 0:
        raise ValueError("ctx_len must be positive")
    d = sorted(set(int(x) for x in dsts))
    if (ctx_len - 1) not in d:
        return d
    m = max(1, int(max_answer_tokens))
    return sorted(set(d) | set(range(ctx_len - 1, ctx_len - 1 + m)))


def option_mass_gate(mass_by_arm: Dict[str, Sequence[float]], min_mass: float,
                     fatal_arms: Sequence[str] = ("none",)) -> Tuple[Dict[str, dict], List[str]]:
    """Per-ARM option-mass summary + the list of FATAL failures. C-6 / plan §2.2.

    Same statistic and same threshold as score_behavior's tail gate, keyed per ARM instead of
    per (readout, query_kind) — and fatal on `fatal_arms` ONLY, which is the whole design point:

      * The baseline arm `none` measures the INSTRUMENT. If the options hold a 1e-5 tail there,
        every delta in the run is an ordering inside noise and nothing is reportable. Fatal.
      * `positive_control` is DESIGNED to destroy the readout, and `all_demo` / `no_demo_text`
        may legitimately do the same. Their mass collapsing is the RESULT, not an instrument
        failure. A gate that fired on them would condemn the run for succeeding — which is the
        mistake this project already made once (2026-08-18: a semantic dip on one arm destroyed
        a healthy comprehension readout on the same run).

    Every arm still gets a `reportable` flag so an intervention arm's collapse is visible in
    summary.json rather than inferable from the code.
    """
    summary: Dict[str, dict] = {}
    fatal: List[str] = []
    fatal_set = set(fatal_arms)
    unusable: set = set()
    for arm in sorted(mass_by_arm):
        raw = [float(x) for x in mass_by_arm[arm] if x is not None]
        # VERIFIER FIX 2026-08-19 (defect V-3): NaN SHORT-CIRCUIT, the dead-guard shape.
        # `med >= min_mass` and `med < min_mass` are NOT complements: a NaN median makes BOTH
        # False, so the per-arm verdict said `reportable: False` while `fatal` stayed empty and
        # the run-level verdict said PASS / reportable: true -- two contradictory answers from one
        # statistic, with the permissive one deciding. `option_mass` is exp(logsumexp(...)) over
        # logits that a knockout can drive to -inf, so NaN is reachable, and it is exactly the
        # kind of arm whose collapse must not be read as health. The verdict is now computed ONCE
        # and the fatal list is derived from it, so the two can never disagree again.
        vals = [x for x in raw if math.isfinite(x)]
        n_nonfinite = len(raw) - len(vals)
        if not vals:
            if n_nonfinite:
                # SEEN but unusable — a different failure from "never ran", and it must not be
                # reported as both. `unusable` keeps the `missing` check below honest.
                unusable.add(arm)
                if arm in fatal_set:
                    fatal.append(f"{arm}: every recorded option mass is non-finite "
                                 f"({n_nonfinite} values) — the readout produced no usable number")
            continue
        v = sorted(vals)
        med = v[len(v) // 2]
        reportable = math.isfinite(med) and med >= min_mass and n_nonfinite == 0
        summary[arm] = {"n": len(v), "median": med, "p10": v[int(0.10 * len(v))],
                        "p90": v[int(0.90 * len(v))], "max": v[-1], "min": v[0],
                        "n_nonfinite": n_nonfinite,
                        "frac_above_1pct": sum(1 for m in v if m > 0.01) / len(v),
                        "reportable": reportable,
                        "gates_the_run": arm in fatal_set}
        if arm in fatal_set and not reportable:
            fatal.append(f"{arm}: median option mass {med:.4g} < {min_mass}" if med < min_mass
                         else f"{arm}: {n_nonfinite} non-finite option mass value(s) recorded")
    missing = [a for a in fatal_set if a not in summary and a not in unusable]
    if missing:
        # A gate that never saw its own arm has not passed; it has not run. Five dead guards.
        fatal.append(f"no option mass recorded for gating arm(s) {sorted(missing)} — the gate "
                     f"was never evaluated, which is not the same as passing it")
    return summary, fatal


@torch.no_grad()
def semantic_logodds(lm, ids: List[int], c_ids: Sequence[int], w_ids: Sequence[int]) -> float:
    """LEGACY single-next-token readout — INVALID, reachable only via `--readout-ids primary`.

    RETAINED, NOT USED BY DEFAULT (correction C-6, 2026-08-18/19). This is
    `log p(concept) - log p(codeword)` over ONE leading-space token id per side at the last
    prompt position. Measured on the committed baseline, the two options together hold a MEDIAN
    5.6e-06 of the next-token mass, and decoding what the model actually wants there shows two
    compounding reasons it cannot be repaired by adding ids:

      1. the model CAPITALISES its forced answer (` Car`, ` Bomb`, ` Literal`), and
      2. the capitalised codeword is MULTI-TOKEN — ` Car` is the first subtoken of ` Carrot`,
         which `readout_ids` rejects by design because `car` is a generic English word. On
         Llama-3.1-8B `bomb` has four single-token variants and `carrot` exactly one, so the
         concept side is structurally advantaged in every number this function ever produced.

    G3's entire attention-edge result was computed with it. It is kept so the old number can be
    reproduced deliberately, and `--readout-ids primary` marks the run NOT reportable in
    summary.json rather than letting it look like a normal run.
    """
    t = torch.tensor([ids], device=lm.model.device)
    logits = lm.model(input_ids=t, use_cache=False).logits[0, -1, :].float().cpu()
    lp = torch.log_softmax(logits, dim=-1)
    ci = torch.tensor(sorted(set(c_ids)), dtype=torch.long)
    wi = torch.tensor(sorted(set(w_ids)), dtype=torch.long)
    return float(lp[ci].logsumexp(0) - lp[wi].logsumexp(0))


def semantic_readout(lm, mode: str, *, context: str, ids: Sequence[int],
                     variants: Dict[str, Sequence[str]], c_ids: Sequence[int],
                     w_ids: Sequence[int], max_batch: int = 1) -> Dict[str, float]:
    """Dispatch the semantic readout. `whole_answer` is the house instrument (C-5/C-6).

    `whole_answer` delegates to `signals.string_option_readout` — the SAME helper, called the
    SAME way as `score_behavior.py --readout-ids whole_answer --answer-prefix "Answer:"`, so
    G3's readout and §4b's readout are literally one function rather than two that agree by
    inspection.

    `max_batch=1` IS LOAD-BEARING, not a performance choice: `pair_common.AttentionKnockout`
    raises `NotImplementedError` on batch>1 (it edits row 0 of the mask only), so batching the
    variants would make every knocked-out arm crash while the baseline arm succeeded. It is
    also held at 1 for the UNINTERVENED arm on purpose — a padded batch and an unpadded single
    sequence are not guaranteed to produce bit-identical logits, and the baseline is the
    reference every delta is taken against.
    """
    if mode == "whole_answer":
        rec = dict(sg.string_option_readout(lm, context, dict(variants), max_batch=max_batch))
        rec["semantic_logodds"] = float(rec["logp_concept"] - rec["logp_codeword"])
        rec["readout_mode"] = "whole_answer"
        return rec
    if mode == "primary":
        return {"semantic_logodds": semantic_logodds(lm, list(ids), c_ids, w_ids),
                "option_mass": None, "readout_mode": "primary"}
    raise ValueError(f"unknown readout mode {mode!r}")


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
    ap.add_argument("--demo-scope", default="codeword",
                    choices=["codeword", "block", "first_codeword", "second_codeword", "last_codeword",
                             "first_neighbor"],
                    help="which source positions count as 'the demonstrations'. 'codeword' = the "
                         "demonstration CODEWORD occurrences only (the original scope). 'block' = "
                         "EVERY token of the demonstration block. The G3 result motivates this: "
                         "cutting all query->demo-codeword edges at every layer recovered only ~7%% "
                         "of the effect of deleting the demonstrations, which suggests the mapping "
                         "is carried by the PREDICATES ('exploded', 'defused') rather than by the "
                         "repeated codeword. 'block' is the direct test of that.")
    ap.add_argument("--enable-thinking", default=None, choices=[None, "true", "false"],
                    help="chat-template thinking mode. REQUIRED for Qwen3-class models. Measured "
                         "2026-08-20 on the button bank, identical code and prefix: the "
                         "unintervened arm's option mass is 0.273 on Llama-3.1-8B and 2.486e-05 on "
                         "Qwen3-14B, because Qwen3's template opens a <think> block in the "
                         "assistant prefix and the forced-answer readout then scores REASONING "
                         "tokens instead of the answer. The tail gate caught it and refused the run.")
    ap.add_argument("--readout-ids", default="whole_answer",
                    choices=["primary", "whole_answer"],
                    help="CORRECTION C-6 (2026-08-19). `whole_answer` (default) teacher-forces "
                         "each option's WHOLE surface form via signals.string_option_readout and "
                         "logsumexps over an identically-built variant set, exactly as "
                         "score_behavior.py does. `primary` reproduces the pre-C-6 "
                         "single-next-token readout that carried every published G3 number and "
                         "that cannot represent the model's preferred spelling of the codeword "
                         "(the capitalised form is multi-token); a `primary` run is marked NOT "
                         "REPORTABLE in summary.json.")
    ap.add_argument("--answer-prefix", default="Answer:",
                    help='assistant-side text appended before the readout position so the next '
                         'token is the answer word rather than a preamble. Pass "" (or none) to '
                         'reproduce the pre-2026-08-18 position, which scored a ~1e-5 tail.')
    ap.add_argument("--min-option-mass", type=float, default=0.05,
                    help="the run is NOT reportable if the BASELINE arm's median option mass is "
                         "below this. A forced choice decided inside a 1e-5 tail is not a forced "
                         "choice. Intervention arms are exempt by design — see option_mass_gate.")
    ap.add_argument("--allow-tail-readout", action="store_true",
                    help="exit 0 despite a failed tail gate (the run is then NOT reportable and "
                         "says so in summary.json)")
    ap.add_argument("--skip-arms", default="",
                    help="comma list of ARMS to skip. REQUIRES --skip-arms-reason. Exists because "
                         "`dense_two_layer` is structurally infeasible below 16 chosen layers and "
                         "the old code met that by silently truncating to 13%% of its target while "
                         "still reporting the arm as edge-count-matched. A skipped arm is counted "
                         "in the FailureLedger and named with its reason in summary.json; it is "
                         "never absent-and-unexplained.")
    ap.add_argument("--skip-arms-reason", default="",
                    help="why. Mandatory whenever --skip-arms is non-empty.")
    ap.add_argument("--dtype", default="float32", choices=["float32", "bfloat16"],
                    help="model weight dtype. DEFAULT float32, and float32 is what every "
                         "committed knockout number was produced in -- prefer it for any run that "
                         "will be compared against one. bfloat16 IS ADMISSIBLE since e0a3387b made "
                         "the dominance reconstruction tolerance dtype-aware (1e-3 fp32, 3e-2 "
                         "otherwise), with tests showing the guard still catches a wrong GQA head "
                         "map. Before that commit bf16 failed 24/24 rows against an fp32-calibrated "
                         "constant (job 769906) -- that was a MISCALIBRATED GUARD, not bad "
                         "arithmetic, and the earlier 'bf16 is refuted' note here was wrong. "
                         "A 14B model needs ~59 GiB in fp32: either shard it (--gpus=2, verified "
                         "working, jobs 769989-769991) or use bfloat16 and do not pool the two.")
    ap.add_argument("--tag", default="pilot")
    args = ap.parse_args()

    # --- deliberate arm skipping: validated BEFORE any model load ----------------------------- #
    # Argument validation runs first on purpose. Placed after the model load, a bad --skip-arms
    # would cost a weight load and a GPU allocation before saying so, and could not be tested
    # without one.
    skip_arms = tuple(a.strip() for a in args.skip_arms.split(",") if a.strip())
    _unknown = [a for a in skip_arms if a not in ARMS]
    if _unknown:
        raise SystemExit(f"[knockout] --skip-arms names arms that do not exist: {_unknown}. "
                         f"Known arms: {list(ARMS)}")
    if skip_arms and not args.skip_arms_reason.strip():
        raise SystemExit("[knockout] --skip-arms requires --skip-arms-reason. An arm that vanishes "
                         "without a recorded reason is indistinguishable from an arm that was "
                         "silently truncated, which is the defect this flag exists to replace.")
    if skip_arms:
        print(f"[knockout] SKIPPING arms {list(skip_arms)}: {args.skip_arms_reason}")
    # Same shell-safe-empty rule as score_behavior.main(); see normalize_answer_prefix.
    answer_prefix = normalize_answer_prefix(args.answer_prefix)
    args.answer_prefix = answer_prefix
    enable_thinking = dc_parse_thinking(args.enable_thinking)
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
    _DTYPES = {"float32": torch.float32, "bfloat16": torch.bfloat16}
    lm = dc.load_model(args.model or dc.PRIMARY_MODEL, dtype=_DTYPES[args.dtype],
                       attn_implementation="eager")
    run.note_bank(args.bank)
    run.note_model(lm.model_id, revision=lm.revision, dtype=str(lm.dtype),
                   attn_implementation="eager", num_layers=lm.num_layers,
                   note="eager required: AttentionKnockout is a no-op under SDPA")

    layers = [int(x) for x in args.layers.split(",")]

    # T7: load EVERY available fit so each row can be ranked with the direction
    # fitted on the OTHER split (cross-fit). The old code loaded exactly one.
    fitted: Dict[str, dict] = {}
    verdicts: Dict[str, dict] = {}
    for split in ("dev", "heldout"):
        p = os.path.join(args.fit_dir, f"directions_fit_{split}.pt")
        if os.path.exists(p):
            payload = torch.load(p, map_location="cpu", weights_only=False)
            # T8: `--fit-dir` consumers never read payload["meta"], so a direction fitted on
            # another MODEL (plausible cosines, no arithmetic complaint) or at another position
            # passed every guard in the repo. surgical_knockout is one of the three named
            # consumers. `position` is deliberately not checked here: this module does not read
            # h at a position, it uses d_surface as a projection direction for dominance.
            verdicts[split] = validate_direction_payload(
                payload, path=p, model=lm.model_id, layers=layers, strict=True)
            fitted[split] = payload
            run.note(**{f"direction_file_{split}": p})
    if not fitted:
        raise SystemExit(f"no directions_fit_*.pt under {args.fit_dir}")

    d_surface_by_split = {
        sp: {L: pl["d_surface"][L] for L in layers if L in pl["d_surface"]}
        for sp, pl in fitted.items()
    }
    # READOUT IDS AND ANSWER VARIANTS ARE PER (concept, codeword), NOT PER rows[0].
    # Pre-2026-08-19 both were built once from `rows[0]` and reused for every row. That is
    # inert on today's bank only because all 12 eligible rows share one pair
    # (`family_accounting["n_concept_codeword_pairs"] == 1`), which is an incidental property
    # of the bank, not a contract — the same shape as the absolute-position-index bug class
    # this repo has been hit by twice. Cached per pair so the cost is unchanged.
    _readout_cache: Dict[Tuple[str, str], dict] = {}

    def readout_for(row: dict) -> dict:
        key = (str(row["concept"]), str(row["codeword"]))
        if key not in _readout_cache:
            concept, codeword = key
            # `whole_answer` is a SCORING mode, not an id-selection mode, so the id pair is
            # still built under `primary` -- its metadata is the evidence that motivated
            # whole_answer and is worth recording. Same call shape as score_behavior.py:391.
            ci, wi, meta = sg.readout_id_pair(lm.tokenizer, concept, codeword, mode="primary")
            variants = {"concept": sg.answer_variants(concept, True),
                        "codeword": sg.answer_variants(codeword, True)}
            n_tok = [len(lm.tokenizer(v, add_special_tokens=False)["input_ids"])
                     for vs in variants.values() for v in vs]
            _readout_cache[key] = {"c_ids": ci, "w_ids": wi, "id_meta": meta,
                                   "variants": variants,
                                   "max_answer_tokens": max(n_tok) if n_tok else 1}
        return _readout_cache[key]

    # VERIFIER FIX 2026-08-19 (defect V-1). `readout_for` CAN RAISE, and moving it into the row
    # loop turned a deterministic start-up failure into a mid-run abort. `signals.readout_ids`
    # raises ValueError for any word whose leading-space form is not a single token, and
    # `readout_id_pair` raises when the two options share an id. Pre-C-6 that call happened ONCE,
    # on rows[0], before any GPU work; the C-6 patch made it per (concept, codeword) inside the
    # loop while leaving it unguarded, so one bad pair anywhere in the bank killed main() with an
    # uncaught ValueError AFTER the run directory existed -- no summary.json, no DONE.json, no
    # FailureLedger, and every completed row's forward passes discarded. That is the exact shape
    # of the abandoned `blockscope_20260817_003144_3066731` directory (config.json + RUNMETA.json
    # and nothing else) and it violates plan §2.2: a malformed row is COUNTED, never fatal.
    # Both call sites are guarded, and by the same rule, because guarding only the loop would
    # leave rows[0] fatal while every other row was ledgered -- the one-of-two-paths shape.
    try:
        r0 = readout_for(rows[0])
        id_meta, first_variants = r0["id_meta"], r0["variants"]
    except Exception as e:                                    # noqa: BLE001 - reason is recorded
        id_meta = {"error": f"{type(e).__name__}: {str(e)[:200]}",
                   "note": "readout ids for rows[0] could not be built; every affected row is "
                           "charged to the FailureLedger as readout_ids:* below"}
        first_variants = None
    run.note(readout_ids=id_meta, layers=layers, topk=args.topk, arms=list(ARMS),
             arms_skipped=list(skip_arms), arms_skipped_reason=args.skip_arms_reason or None,
             arms_run=[a for a in ARMS if a not in skip_arms],
             demo_scope=args.demo_scope, family_accounting=family_accounting,
             direction_splits_available=sorted(fitted),
             direction_payload_verdicts=verdicts,
             readout_mode=args.readout_ids, answer_prefix=answer_prefix,
             enable_thinking=enable_thinking,
             min_option_mass=args.min_option_mass,
             semantic_variants_first_pair=first_variants,
             readout_note=("whole_answer: signals.string_option_readout, called exactly as "
                           "score_behavior.py --readout-ids whole_answer --answer-prefix "
                           "'Answer:' (correction C-6)"))
    print(f"[knockout] {len(rows)} prompts / {family_accounting['n_families_selected']} families "
          f"over {family_accounting['n_domains_selected']} domain(s), "
          f"layers={layers}, k={args.topk} edges/layer/arm")

    n = 0
    option_mass_by_arm: Dict[str, List[float]] = collections.defaultdict(list)
    source_truncation: Dict[str, int] = collections.Counter()
    truncated_ids: List[str] = []
    for row in rows:
        try:
            # BOTH templating paths get the mode. The pre-2026-08-20 code passed it to NEITHER,
            # so `resolve_occurrences` used extract_boombness's module-level global — the sixth
            # instance of this project's one-of-two-paths shape, and the file's own comment below
            # had already noticed the argument was not being passed.
            templated, prompt_ids, last, _, _ = resolve_occurrences(
                dc, lm.tokenizer, row, enable_thinking=enable_thinking)
        except ValueError as e:
            ledger.fail(f"resolve:{e}", row["prompt_id"])
            continue
        if not last:
            # No resolved codeword occurrence => no `--dst codeword`, no demo-codeword scope.
            # This used to be an IndexError on `last[-1]`, i.e. it killed the whole run instead
            # of costing one row (the exact shape that killed 179/179 ClearHarm rows).
            ledger.fail("no_codeword_occurrence", row["prompt_id"])
            continue
        try:
            rd = readout_for(row)
        except Exception as e:                                # noqa: BLE001 - reason is recorded
            # See the guard on rows[0] above: an unbuildable readout is a COUNTED row failure,
            # not an abort. Reason carries the exception type so a multi-token codeword
            # (ValueError from signals.readout_ids) is distinguishable in summary.json from a
            # shared-id pair or a tokenizer fault.
            ledger.fail(f"readout_ids:{type(e).__name__}:{str(e)[:60]}", row["prompt_id"])
            continue
        # C-6: the readout is taken AFTER the answer prefix, so the CONTEXT the model is scored
        # on -- and hence the position the readout reads -- is prompt+prefix, not prompt. The
        # concatenation is re-tokenised (as score_behavior does) rather than having the prefix's
        # own ids appended, and the guard below refuses the row if that re-tokenisation disturbs
        # any PROMPT token: every demo and codeword position in this module is an ABSOLUTE index
        # into the prompt's ids, and this repo has been hit twice by absolute indices that moved.
        ctx = templated + answer_prefix
        ids = lm.tokenizer(ctx, add_special_tokens=False)["input_ids"]
        if list(ids[:len(prompt_ids)]) != list(prompt_ids):
            ledger.fail("answer_prefix_retokenizes_prompt", row["prompt_id"])
            continue
        # The destination MUST be the position the readout reads, or the intervention and the
        # measurement are about different tokens (see --dst).
        readout_pos = len(ids) - 1
        # T3: `dst` is the RANKING/reporting destination and must be the token the
        # readout actually reads (see choose_destinations); `dsts` is what gets cut.
        dsts, dst = choose_destinations(args.dst, last[-1], readout_pos)
        # C-6b: with a whole-answer readout the scored positions run past the context, so the
        # knockout's QUERY set must span the answer window too (see readout_query_positions).
        qpos = (readout_query_positions(dsts, len(ids), rd["max_answer_tokens"])
                if args.readout_ids == "whole_answer" else list(dsts))
        # T7: cross-fit the ranking direction on the row's own split.
        fit_split, is_self_fit = choose_direction_split(sorted(fitted), row.get("split"))
        d_surface = d_surface_by_split[fit_split]
        if args.demo_scope == "codeword":
            demo_pos = last[:-1]             # the demonstration codeword occurrences
        elif args.demo_scope in ("first_codeword", "second_codeword", "last_codeword",
                                 "first_neighbor"):
            # POSITION-RESOLVED demo scopes (follow-up sprint, plan §9 units 2-3).
            #
            # Motivated by this sprint's own Phase B result: the LAST demonstration codeword is
            # measurably more concept-like than the FIRST (paired family-matched excess +0.5414 at
            # L8, t = 3.26). That is a REPRESENTATIONAL gradient. These two scopes ask whether it
            # has a CAUSAL counterpart -- does cutting attention out of the last demonstration cost
            # more than cutting it out of the first?
            #
            # `last` holds the codeword occurrence indices with the QUERY occurrence last, so
            # last[:-1] are the demonstration occurrences. A prompt with no demonstrations has
            # len(last) == 1 and yields an empty scope, which the existing `if not demo_pos` guard
            # below charges to the FailureLedger by name rather than dropping silently.
            demos = last[:-1]
            # `second_codeword` discriminates two readings of the first/last result: if the effect is
            # specific to the FIRST demonstration, the second should already be small; if it decays
            # with position, the second should be intermediate. Rows with fewer than 2 demonstrations
            # yield an empty scope and are charged to the ledger by name.
            if args.demo_scope == "first_codeword":
                demo_pos = demos[:1]
            elif args.demo_scope == "second_codeword":
                demo_pos = demos[1:2]
            elif args.demo_scope == "first_neighbor":
                # SERIAL-POSITION CONTROL (review #3 identification limit 2).
                #
                # first/second/last give a monotone decay (+0.972 / +0.327 / -0.023), which is exactly
                # what "distance from BOS / attention-sink proximity" would produce as well as what
                # "demonstration ordinality" would. This arm cuts the token IMMEDIATELY BEFORE the
                # first demonstration codeword: same sequence region, same 1024 edges, but NOT the
                # codeword. If the decay is about position, this should behave like first_codeword.
                # If it is about the codeword, this should be near zero.
                demo_pos = [demos[0] - 1] if demos and demos[0] - 1 >= 0 else []
            else:
                demo_pos = demos[-1:]
        else:
            # Every token of the demonstration block. Located by character offset of the
            # recorded demo_block inside the TEMPLATED prompt, so it cannot drift from the
            # generator's own notion of what the demonstrations are.
            blk = row.get("demo_block") or ""
            if not blk:
                ledger.fail("no_demo_block", row["prompt_id"])
                continue
            # `templated` comes from resolve_occurrences, which is what `prompt_ids` was
            # tokenised from. Re-templating here (the pre-2026-08-19 code did) is a second
            # path that can disagree with the first — extract_boombness.resolve_occurrences
            # takes an `enable_thinking` argument this call did not pass.
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
            in_block = [i for i, (a, b) in enumerate(enc["offset_mapping"])
                        if a >= lo and b <= hi and b > a]
            demo_pos = [i for i in in_block if i < src_bound]
            n_dropped = len(in_block) - len(demo_pos)
            if n_dropped:
                # NOT a silent truncation any more (plan §2.2). Causality forbids a source at or
                # after the LAST destination, so these tokens genuinely CANNOT be cut and the row
                # is not a failure -- charging the FailureLedger here would mark a succeeding row
                # failed and break `n_attempted == n_succeeded + n_failed`. It is counted in its
                # own block instead, so an arm labelled "all demo edges" can never again be short
                # of the block by an amount nobody recorded.
                source_truncation["n_demo_tokens_after_last_dst"] += n_dropped
                source_truncation["n_rows_truncated"] += 1
                if len(truncated_ids) < 10:
                    truncated_ids.append(str(row["prompt_id"]))
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
                     "demo_scope": args.demo_scope,
                     # C-6 provenance, per row: which instrument produced semantic_logodds,
                     # where it was read, and how wide the knocked-out query window was.
                     "readout_mode": args.readout_ids, "answer_prefix": answer_prefix,
                     "prompt_len": len(prompt_ids), "ctx_len": len(ids),
                     "max_answer_tokens": rd["max_answer_tokens"],
                     "query_positions": qpos, "n_query_positions": len(qpos)})

        def _read(context: str, tok_ids: Sequence[int]) -> Dict[str, float]:
            """One readout, same instrument for every arm (C-6). max_batch=1: see semantic_readout."""
            return semantic_readout(lm, args.readout_ids, context=context, ids=tok_ids,
                                    variants=rd["variants"], c_ids=rd["c_ids"], w_ids=rd["w_ids"])

        def _emit(arm: str, rec: Dict[str, float], **extra) -> None:
            option_mass_by_arm[arm].append(rec.get("option_mass"))
            run.log_row({**base, "arm": arm, **extra, **rec})

        for arm in ARMS:
            if arm in skip_arms:
                # DELIBERATE, REASONED, AND RECORDED. `dense_two_layer` is structurally infeasible
                # below 16 chosen layers (see pick_edges), and the pre-2026-08-17 code met that by
                # SILENTLY TRUNCATING to 13% of the target while still labelling the arm
                # edge-count-matched. Refusing outright is right; but refusing the whole RUN because
                # one arm is infeasible would block G3 entirely, so an arm may be skipped -- only
                # with a reason, only counted, and only surfaced in summary.json.
                ledger.fail(f"arm_{arm}:skipped_by_request", row["prompt_id"])
                continue
            if arm == "none":
                _emit(arm, _read(ctx, ids), n_edges_cut=0)
                n += 1
                continue
            if arm == "no_demo_text":
                # The true ceiling: the same query with the demonstration block removed.
                q = row.get("final_query_text") or ""
                if not q:
                    ledger.fail("no_demo_text:missing_query", row["prompt_id"])
                    continue
                t2 = dc.apply_template(lm.tokenizer, q, enable_thinking=enable_thinking)
                ctx2 = t2 + answer_prefix
                ids2 = lm.tokenizer(ctx2, add_special_tokens=False)["input_ids"]
                _emit(arm, _read(ctx2, ids2), n_edges_cut=-1, seq_len_used=len(ids2))
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
                               args.topk, arm, rng, dsts_global=qpos,
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
                                lm.model, [L], query_positions=qpos,
                                blocked_keys=sorted(set(srcs)), heads=[h]))
                    rec = _read(ctx, ids)
            except Exception as e:
                ledger.fail(f"knockout_{arm}:{type(e).__name__}:{str(e)[:60]}", row["prompt_id"])
                continue
            _emit(arm, rec, n_edges_cut=n_cut)
            n += 1
        ledger.ok()

    # THE TAIL GATE (C-6), computed BEFORE finish so its verdict is written into summary.json,
    # and enforced AFTER finish so a failure never destroys the evidence that documents it.
    mass_summary, tail_fail = ({}, []) if args.readout_ids != "whole_answer" else option_mass_gate(
        option_mass_by_arm, args.min_option_mass, fatal_arms=("none",))
    for arm in sorted(mass_summary):
        m = mass_summary[arm]
        print(f"[knockout] option mass {arm}: median={m['median']:.4g} p90={m['p90']:.4g} "
              f"max={m['max']:.4g} frac>1%={m['frac_above_1pct']:.3f} "
              f"{'OK' if m['reportable'] else 'BELOW GATE'}"
              f"{'' if m['gates_the_run'] else '  (not gated: intervention arm)'}")

    # THE ARM-COVERAGE GATE — VERIFIER FIX 2026-08-19 (defect V-4).
    # The mass gate watches the INSTRUMENT; nothing watched the INTERVENTION. Every arm that
    # enters `AttentionKnockout` is wrapped in `except Exception -> ledger.fail`, and `none` /
    # `no_demo_text` are the two arms that never touch it — so a fault in the knockout itself
    # kills all ten cutting arms while the two uncut arms sail through, and the run still wrote
    # `option_mass_gate: PASS`, `reportable: true`, exit 0. Reproduced: with the knockout raising
    # on construction the run finished rc=0 / reportable=true carrying rows for `none` and
    # `no_demo_text` only. That is not a hypothetical fault mode for the FIRST C-6 run: C-6 made
    # the readout pass an explicit 2-D `attention_mask` into the forward, and `AttentionKnockout`
    # REFUSES anything but a 4-D additive mask (`RuntimeError`) and any batch > 1
    # (`NotImplementedError`) — a combination this repo has never executed on a GPU.
    # Addressed BY IDENTITY (the two arm names that skip the knockout), not by a row-count
    # threshold or a name prefix. Deliberately requires only that SOME cutting arm survived:
    # `dense_two_layer` is legitimately INFEASIBLE at >2 chosen layers and must not, alone,
    # condemn a run.
    NON_KNOCKOUT_ARMS = ("none", "no_demo_text")
    rows_by_arm = {a: len(option_mass_by_arm.get(a, ())) for a in ARMS}
    cutting_arms_with_rows = sorted(a for a in ARMS
                                    if a not in NON_KNOCKOUT_ARMS and a not in skip_arms
                                    and rows_by_arm[a])
    coverage_fail: List[str] = []
    if not cutting_arms_with_rows:
        coverage_fail.append(
            "no arm that CUTS ATTENTION EDGES produced a single row: every one of "
            f"{sorted(set(ARMS) - set(NON_KNOCKOUT_ARMS))} failed. The knockout did not run, so "
            "nothing in this directory is evidence about attention edges — see the FailureLedger "
            "for the per-arm reason (a 4-D-mask RuntimeError or a batch>1 NotImplementedError "
            "from AttentionKnockout is the expected cause).")
    arm_coverage = {"rows_by_arm": rows_by_arm,
                    "non_knockout_arms": list(NON_KNOCKOUT_ARMS),
                    "cutting_arms_with_rows": cutting_arms_with_rows,
                    "verdict": "PASS" if not coverage_fail else "FAILED — " + coverage_fail[0]}
    for c in coverage_fail:
        print(f"[knockout] ARM COVERAGE: {c}", file=sys.stderr)

    gate_fail = list(tail_fail) + coverage_fail
    reportable = (args.readout_ids == "whole_answer") and not gate_fail

    run.finish(summary={"model": lm.model_id, "n_rows": n, "arms": list(ARMS),
                        "family_accounting": family_accounting,
                        "direction_splits_available": sorted(fitted),
                        "direction_payload_verdicts": verdicts,
                        "cross_fit_note": "edge ranking uses the direction fitted on the OTHER "
                                          "split; per-row is_self_fit flags any residual "
                                          "in-sample row",
                        "positive_control_note": "positive_control blocks every pre-query key in "
                                                 "every head; if its delta is small the knockout "
                                                 "is not firing and all other arms are void",
                        "readout_mode": args.readout_ids,
                        "answer_prefix": answer_prefix,
                        "option_mass": mass_summary,
                        "option_mass_gate": ("PASS" if not tail_fail else
                                             "FAILED — NOT REPORTABLE: " + "; ".join(tail_fail)),
                        "arm_coverage": arm_coverage,
                        "reportable": reportable,
                        # V-4: the note now names the ACTUAL reason(s). It previously hard-coded
                        # "baseline option mass below --min-option-mass" for every whole_answer
                        # failure, which would have mislabelled a knockout that never fired as a
                        # tail readout — the wrong diagnosis printed with full confidence.
                        "reportable_note": (
                            "" if reportable else
                            "; ".join(
                                ([] if args.readout_ids == "whole_answer" else
                                 ["readout_mode=primary is the pre-C-6 single-next-token "
                                  "instrument: the option pair holds a median ~5.6e-06 of "
                                  "next-token mass and the capitalised codeword is multi-token, "
                                  "so this run reproduces the retracted G3 number and is NOT "
                                  "reportable"]) + list(gate_fail))),
                        "source_truncation": {**dict(source_truncation),
                                              "example_prompt_ids": truncated_ids,
                                              "note": "demonstration tokens at or after the last "
                                                      "destination cannot be cut (causal mask); "
                                                      "counted, never silently dropped"},
                        "layers": layers, "topk": args.topk,
                        "condition": args.condition, "query_kind": args.query_kind},
               ledger=ledger)
    print(f"[knockout] {n} rows -> {run.path}")
    print(f"[knockout] failures: {ledger.as_dict()['failure_reasons']}")
    if args.readout_ids != "whole_answer":
        print("[knockout] readout_mode=primary — this run reproduces the RETRACTED pre-C-6 "
              "readout and is NOT reportable.", file=sys.stderr)
    # `--allow-tail-readout` accepts a TAIL READOUT deliberately. It does NOT, and must not,
    # accept a knockout that never ran: there is no deliberate version of that (V-4).
    hard_fail = (list(tail_fail) if not args.allow_tail_readout else []) + coverage_fail
    if hard_fail:
        print("[knockout] GATE FAILED — the run is written and every arm's numbers are on "
              "disk, but the run is NOT reportable:", file=sys.stderr)
        for t in hard_fail:
            print(f"  - {t}", file=sys.stderr)
        if tail_fail:
            print(f"[knockout] readout position is after answer_prefix={answer_prefix!r}. "
                  f"Pass --allow-tail-readout to accept deliberately.", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
