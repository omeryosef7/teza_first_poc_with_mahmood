#!/usr/bin/env python3
"""EXPLORATORY Bombness candidate search on TRAIN. Successor plan sections 7, 8, 18, 19.

WHAT IS NEW HERE, AND WHY IT IS NOT THE PREVIOUS CONSTRUCTION
------------------------------------------------------------
`PR-053` / `R-111` built `v_bomb_specific = v_bomb - mean(v_knife, v_gun)` where each `v_concept`
is `mean_domains(h_C - h_A)` -- a CROSS-CONCEPT contrast between doublespeak cells. `R-116` then
showed knife installs in 0/113 domains and gun in 1/113, so that contrast is partly a contrast
between "which demonstrations are present", not between installed concepts. That is the standing
narrowing and it is not disputed here.

This module uses cells **B** and **E**, which `PR-053` never touched, and gets a concept reference
direction that DOES NOT REQUIRE THE CONCEPT TO INSTALL AT ALL:

        v_lex(concept, L) = unit( mean_domains [ h_E(L) - h_A(L) ] )

Cell A is `benign_literal` (benign demonstrations, the codeword `button`); cell E is
`concept_in_benign_ctx` (THE SAME benign demonstrations with the codeword replaced by the concept
word). Both are read at `codeword_last`, which resolves to the queried word at rel_end -10 in both.
So `v_lex` is the direction from the token ` button` to the token ` bomb` **at one fixed semantic
role, in a byte-identical benign context, with nothing installed and nothing to install.** It is a
pure lexical/semantic reference axis, and it is available for bomb, knife and gun alike because
building it needs no installation.

The Bombness candidate is then Matan's own phrasing made arithmetic -- *does the Doublespeak
manipulation move the codeword's state toward the concept's?*

        B1(d, L) = < h_C(d,L) - h_A(d,L) ,  v_lex_hat(concept, L) >

with `h_C - h_A` the within-domain, within-family Doublespeak shift at a token whose IDENTITY IS
HELD CONSTANT (` button` in both cells) and whose whole 28-token query span is byte-identical
(S-001). The specificity test is the 3x3: project each concept bank's shift onto each concept's
`v_lex`. Diagonal dominance is concept specificity WITHOUT the installation confound, because the
reference axes come from the benign cells.

EVERY REFERENCE DIRECTION IS LEAVE-ONE-DOMAIN-OUT. A domain never contributes to the direction it
is scored against; otherwise `B1` is partly an inner product of a vector with itself.

DISCIPLINE
  * TRAIN domains only. The frozen manifest's validation and test domains are NOT READ by this
    script; `--split` refuses anything but `train` unless `--i-am-the-frozen-analyzer` is passed,
    which nothing in this phase passes.
  * Everything here is EXPLORATORY. No p-value printed by this file may be promoted to a
    confirmatory claim; a finalist is frozen in a NEW preregistration and tested once elsewhere.

USAGE
  python3 scripts/dcs_succ_bombness_candidates.py --out outputs/dcs_succ/bombness_candidates.json
  python3 scripts/dcs_succ_bombness_candidates.py --selftest
  python3 scripts/dcs_succ_bombness_candidates.py --mutate
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import random
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPS_ROOT = os.path.join(REPO, "outputs", "boombness", "extract_boombness")
SPLIT_MANIFEST = os.path.join(REPO, "data", "boombness_prompts", "dcs_ts116_domain_split.json")
TAG_PREFIX = "ts116m_full"
CODEWORDS = ("button", "basket")
CONCEPTS = ("bomb", "knife", "gun")
CELLS = ("A", "B", "C", "E")
QUERY_KIND = "semantic_one_word"
DOSE = 4
#: The three whole-population exclusions, with the entries that authorise them.
EXCLUDED_DOMAINS = ("restaurant_kitchen", "school_campus", "subway_station")


class Refusal(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
# loading
# --------------------------------------------------------------------------- #
def _find_run(bank_name: str) -> str:
    pat = os.path.join(REPS_ROOT, "%s_%s_*" % (TAG_PREFIX, bank_name))
    hits = sorted(d for d in glob.glob(pat) if os.path.exists(os.path.join(d, "DONE.json")))
    if not hits:
        raise Refusal("no COMPLETED extraction run for %r under %s. A run without DONE.json is a "
                      "run that may have stopped mid-bank; it is not read." % (bank_name, pat))
    if len(hits) > 1:
        raise Refusal("%d completed runs match %r: %s. Refusing to pick one by mtime -- a silent "
                      "choice between two populations is how two arms end up on different data."
                      % (len(hits), bank_name, [os.path.basename(h) for h in hits]))
    return hits[0]


def load_bank(bank_name, torch, keep_domains=None):
    """-> (meta, rows_by_cell_domain_slot, reps) for ONE bank, filtered to the analysis cell.

    `keep_domains` filters AT SELECTION TIME. That is not tidiness: the independent verification
    of 2026-09-09 (reports/DCS_SUCC_S002_INDEPENDENT_VERIFICATION.md section 7.1) found that this
    function used to select all 113 analysed domains and let `domain_cell_means` drop the
    non-TRAIN ones afterwards. No statistic was ever computed on a validation or test row -- but
    the artifact published `n_selected_rows = 4520` (113 x 10 x 4) beside `n_train_domains = 67`,
    when the number of rows the metrics ran on was 2680 (67 x 10 x 4), and NOTHING IN THE ARTIFACT
    let a reader see that the held-out rows were untouched. The split rule exists precisely to
    make that visible from the outside, so the filter moved here."""
    run = _find_run(bank_name)
    cache = os.path.join(run, "cache", "final_occurrence_reps.pt")
    blob = torch.load(cache, map_location="cpu", weights_only=False)
    layers = [int(x) for x in blob["layers"]]
    reps = blob["reps"]

    rows = {}
    n_selected = 0
    seen_token_text = defaultdict(set)
    with open(os.path.join(run, "results.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r["query_kind"] != QUERY_KIND or int(r["n_examples"]) != DOSE:
                continue
            if r["cell"] not in CELLS or r["domain"] in EXCLUDED_DOMAINS:
                continue
            if keep_domains is not None and r["domain"] not in keep_domains:
                continue
            # family_slot: everything in family_id except the DOMAIN (first field) and the
            # QUERY_KIND (last field, constant here), so a cell-A row and a cell-C row of the same
            # structural slot pair up.
            #
            # A BUG CAUGHT HERE, RECORDED BECAUSE IT WOULD OTHERWISE HAVE BEEN INVISIBLE. The first
            # version of this line used parts[2:-1], dropping field 1 as well. Field 1 is the
            # bank's OWN `split` value (`dev` / `heldout`, 11136 rows each) -- NOT the domain-level
            # `dsplit` manifest. Dropping it made `dev|slot0` and `heldout|slot0` the same key, so
            # every second row silently overwrote the first and the analysis ran on HALF the rows
            # with no error at all. The count guard below is what turns that class of mistake into
            # a refusal instead of a quieter number.
            parts = r["family_id"].split("|")
            slot = "|".join(parts[1:-1])
            key = (r["cell"], r["domain"], slot)
            if key in rows:
                raise Refusal(
                    "family key %r binds two rows (%s and %s) in bank %r. A dict keyed by a "
                    "non-unique key silently keeps the LAST row and drops the rest; the analysis "
                    "would then run on a subset it never announced."
                    % (key, rows[key], r["prompt_id"], bank_name))
            rows[key] = r["prompt_id"]
            n_selected += 1
            seen_token_text[r["cell"]].add(r.get("token_text"))
    if len(rows) != n_selected:
        raise Refusal("bank %r: %d rows selected but only %d family keys survived -- the key is "
                      "not unique over the selection" % (bank_name, n_selected, len(rows)))
    meta = {"run": os.path.basename(run), "layers": layers, "n_selected_rows": n_selected,
            "layer_convention": blob.get("layer_convention"),
            "position": blob.get("position"),
            "token_text_by_cell": {c: sorted(v) for c, v in seen_token_text.items()},
            "n_rows_analysed": len(rows),
            "_n_rows_note": "rows actually bound AFTER the split filter -- 67 x 10 x 4 on TRAIN. "
                            "The field was called `n_rows` and reported 4520 (all 113 analysed "
                            "domains) until the S-002 independent verification found that a "
                            "reader could not tell the held-out rows were untouched."}
    return meta, rows, reps


def split_map():
    m = json.load(open(SPLIT_MANIFEST, encoding="utf-8"))
    return dict(m["assign"]), m


# --------------------------------------------------------------------------- #
# vector helpers (plain python lists of floats; the arrays are 9 x 4096)
# --------------------------------------------------------------------------- #
def _unit(v, torch):
    n = float(torch.linalg.vector_norm(v))
    if n == 0.0:
        raise Refusal("a zero-norm direction was asked to be normalised; a zero direction scores "
                      "every row identically and would read as a clean null")
    return v / n


def domain_cell_means(rows, reps, torch, domains):
    """(cell, domain) -> Tensor[n_layers, H] float32, the mean over that domain's family slots.

    A domain that is missing ANY of the four cells is dropped ENTIRELY and named, rather than
    contributing to some contrasts and not others -- an unbalanced domain makes `h_C - h_A` and
    `h_B - h_E` averages over different domain sets, which is exactly the kind of quiet
    population difference this project has been bitten by.
    """
    by = defaultdict(list)
    for (cell, dom, slot), pid in rows.items():
        if dom not in domains:
            continue
        t = reps.get(pid)
        if t is None:
            raise Refusal("prompt_id %s is in results.jsonl but absent from the rep cache" % pid)
        by[(cell, dom)].append(t.to(torch.float32))
    out, dropped = {}, []
    doms = sorted({d for (_, d) in by})
    for d in doms:
        if any((c, d) not in by for c in CELLS):
            dropped.append(d)
            continue
        for c in CELLS:
            out[(c, d)] = torch.stack(by[(c, d)]).mean(dim=0)
    return out, sorted(set(doms) - {d for d in dropped}), dropped


def loo_direction(per_domain_delta, domains, held_out, torch):
    """unit( mean over TRAIN domains EXCEPT `held_out` ). Leave-one-domain-out, always."""
    keep = [per_domain_delta[d] for d in domains if d != held_out]
    if len(keep) < 2:
        raise Refusal("a leave-one-out direction was asked for with fewer than 2 contributing "
                      "domains")
    m = torch.stack(keep).mean(dim=0)
    return m


# --------------------------------------------------------------------------- #
# statistics (domain is the independence unit)
# --------------------------------------------------------------------------- #
def sign_test_two_sided(k, n):
    if n == 0:
        return 1.0, 1.0
    k = max(k, n - k)
    tail = sum(math.comb(n, i) for i in range(k, n + 1))
    p = min(1.0, 2.0 * tail / (2.0 ** n))
    return p, min(1.0, 2.0 / (2.0 ** n))


def boot_ci(vals, rng, B=10000, alpha=0.05):
    if not vals:
        return (float("nan"), float("nan"))
    n = len(vals)
    ms = []
    for _ in range(B):
        ms.append(sum(vals[rng.randrange(n)] for _ in range(n)) / n)
    ms.sort()
    return (ms[int((alpha / 2) * B)], ms[min(B - 1, int((1 - alpha / 2) * B))])


def mean(v):
    return sum(v) / len(v) if v else float("nan")


def sd(v):
    if len(v) < 2:
        return float("nan")
    m = mean(v)
    return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))


def cohen_d_paired(vals):
    s = sd(vals)
    return (mean(vals) / s) if (s and not math.isnan(s) and s > 0) else float("nan")


# --------------------------------------------------------------------------- #
# the analysis
# --------------------------------------------------------------------------- #
def analyse(codeword, train_domains, torch, rng, n_random_draws=12, verbose=True):
    """The 3x3 for one codeword: each concept bank's Doublespeak shift against each concept's
    benign lexical reference axis."""
    banks, means, doms = {}, {}, {}
    for concept in CONCEPTS:
        name = "%s_%s" % (codeword, concept)
        meta, rows, reps = load_bank(name, torch, keep_domains=set(train_domains))
        m, kept, dropped = domain_cell_means(rows, reps, torch, set(train_domains))
        banks[concept] = meta
        means[concept] = m
        doms[concept] = kept
        del reps
        if verbose:
            print("[cand] %-16s run=%s rows=%d train_domains=%d dropped=%s token_text=%s"
                  % (name, meta["run"][:40], meta["n_rows"], len(kept), dropped,
                     meta["token_text_by_cell"]), file=sys.stderr)

    common = sorted(set(doms["bomb"]) & set(doms["knife"]) & set(doms["gun"]))
    if len(common) < 10:
        raise Refusal("only %d TRAIN domains are complete in all three concept banks" % len(common))

    layers = banks["bomb"]["layers"]

    # ---- STRUCTURAL CHECK, not an assumption: cell A must be the SAME prompt in all three
    # concept banks (the banks differ only in the harmful demonstrations). If it is not, `v_lex`
    # for two concepts would be measured against two different baselines and the 3x3 would be
    # comparing shifted origins.
    a_ident = {}
    for L_i in range(len(layers)):
        diffs = []
        for d in common:
            a_b = means["bomb"][("A", d)][L_i]
            for other in ("knife", "gun"):
                a_o = means[other][("A", d)][L_i]
                diffs.append(float(torch.linalg.vector_norm(a_b - a_o)))
        a_ident["L%d" % layers[L_i]] = {"max_abs_diff": max(diffs), "mean_abs_diff": mean(diffs)}

    # ---- per-domain deltas
    delta_EA = {c: {d: means[c][("E", d)] - means[c][("A", d)] for d in common} for c in CONCEPTS}
    delta_CA = {c: {d: means[c][("C", d)] - means[c][("A", d)] for d in common} for c in CONCEPTS}
    delta_BE = {c: {d: means[c][("B", d)] - means[c][("E", d)] for d in common} for c in CONCEPTS}

    out = {"codeword": codeword, "layers": layers, "n_train_domains": len(common),
           "domains": common, "banks": banks, "cellA_identity_across_concept_banks": a_ident,
           "cells": {"A": "benign_literal", "B": "direct_harmful", "C": "natural_doublespeak",
                     "E": "concept_in_benign_ctx"},
           "metrics": {}, "controls": {}}

    # ---- B1: projection of the Doublespeak shift onto the benign lexical axis, LOO.
    for L_i, L in enumerate(layers):
        # gap norm per reference concept: how far apart the two WORDS are, in this benign context
        gap = {}
        for c in CONCEPTS:
            g = torch.stack([delta_EA[c][d][L_i] for d in common]).mean(dim=0)
            gap[c] = float(torch.linalg.vector_norm(g))

        for shift_c in CONCEPTS:
            for ref_c in CONCEPTS:
                raw, gapu, cosv = [], [], []
                for d in common:
                    vref = loo_direction({k: v[L_i] for k, v in delta_EA[ref_c].items()},
                                         common, d, torch)
                    vhat = _unit(vref, torch)
                    s = delta_CA[shift_c][d][L_i]
                    p = float(torch.dot(s, vhat))
                    raw.append(p)
                    gapu.append(p / gap[ref_c] if gap[ref_c] else float("nan"))
                    cosv.append(p / float(torch.linalg.vector_norm(s)))
                k = sum(1 for x in raw if x > 0)
                pv, floor = sign_test_two_sided(k, len(raw))
                out["metrics"]["B1|L%d|shift_%s|ref_%s" % (L, shift_c, ref_c)] = {
                    "mean_proj": mean(raw), "sd_proj": sd(raw),
                    "mean_gap_units": mean(gapu), "sd_gap_units": sd(gapu),
                    "ci95_gap_units": boot_ci(gapu, rng),
                    "mean_cos": mean(cosv), "sd_cos": sd(cosv),
                    "d_paired": cohen_d_paired(gapu),
                    "n_domains": len(raw), "n_positive": k,
                    "sign_p": pv, "sign_p_floor": floor,
                    "ref_gap_norm": gap[ref_c],
                    "_reading": ("gap_units is the fraction of the benign %s->%s lexical gap that "
                                 "the Doublespeak manipulation traverses at the queried token"
                                 % (codeword, ref_c))}

        # ---- THE INCONGRUITY TEST (successor plan sections 2.1 and 33).
        #
        # `v_lex = E - A` contrasts the CONCEPT word with the CODEWORD in a BENIGN context. In
        # cell E, ` bomb` sits in a sentence about sterile store rooms: it is semantically
        # INCONGRUOUS, while cell A's ` button` is congruous. So `v_lex` may carry a large
        # "an out-of-place word is here" component, and cell C's codeword is ALSO made incongruous
        # by the harmful demonstrations -- which would make B1 a surprisal result wearing a
        # semantic label.
        #
        # A SECOND, INDEPENDENT OPERATIONALISATION OF THE SAME AXIS DISCRIMINATES THEM:
        #
        #     v_lex_harm = mean_d [ h_B - h_C ]
        #
        # is the same button -> bomb contrast measured in the HARMFUL context, where the roles are
        # REVERSED: ` bomb` (cell B) is now the congruous word and ` button` (cell C) the odd one.
        # The lexical/semantic component enters both axes with the SAME sign; the incongruity
        # component enters with OPPOSITE signs. Therefore:
        #
        #   cos(v_lex_benign, v_lex_harm) HIGH  -> the shared component dominates -> semantic
        #   cos(...) LOW or NEGATIVE            -> incongruity dominates
        #
        # And projecting the SAME shift `h_C - h_A` (whose own incongruity component is POSITIVE:
        # C's codeword is odd, A's is not) onto `v_lex_harm` (whose incongruity component is
        # NEGATIVE) puts the two accounts in direct opposition: incongruity SUBTRACTS here where it
        # ADDED before. A B1 that survives against this axis is not carried by incongruity.
        #
        # The direction is LEAVE-ONE-DOMAIN-OUT, which also removes the shared-term bias: h_C(d)
        # appears in the shift but NOT in the axis domain d is scored against.
        delta_BC_L = {d: (means["bomb"][("B", d)][L_i] - means["bomb"][("C", d)][L_i])
                      for d in common}
        vharm_full = torch.stack([delta_BC_L[d] for d in common]).mean(dim=0)
        gap_harm = float(torch.linalg.vector_norm(vharm_full))
        vben_full = torch.stack([delta_EA["bomb"][d][L_i] for d in common]).mean(dim=0)
        cos_two_ops = float(torch.dot(_unit(vben_full, torch), _unit(vharm_full, torch)))
        hvals = []
        for d in common:
            vhat = _unit(loo_direction(delta_BC_L, common, d, torch), torch)
            hvals.append(float(torch.dot(delta_CA["bomb"][d][L_i], vhat)) / gap_harm)
        k_h = sum(1 for x in hvals if x > 0)
        p_h, f_h = sign_test_two_sided(k_h, len(hvals))
        out["metrics"]["B1harmref|L%d|shift_bomb" % L] = {
            "mean_gap_units": mean(hvals), "sd_gap_units": sd(hvals),
            "ci95_gap_units": boot_ci(hvals, rng), "d_paired": cohen_d_paired(hvals),
            "n_domains": len(hvals), "n_positive": k_h, "sign_p": p_h, "sign_p_floor": f_h,
            "ref_gap_norm": gap_harm,
            "cos_benign_axis_vs_harm_axis": cos_two_ops,
            "_reading": "the SAME Doublespeak shift projected on the button->bomb axis measured "
                        "in the HARMFUL context, where incongruity enters with the opposite sign"}

        # ---- PROTOTYPE similarity (candidate family D), with the control that decides how to
        # read it. cos(h_C, mu) - cos(h_A, mu) asks whether the Doublespeak codeword state sits
        # closer to a prototype than the benign codeword state does. THREE prototypes are used,
        # because the obvious one has an obvious confound:
        #
        #   mu_B  the concept token in the HARMFUL context. h_C is also in a harmful context and
        #         h_A is not, so a positive score here could be CONTEXT similarity, not concept
        #         similarity. Reported, but it is not the evidence.
        #   mu_E  the concept token in the BENIGN context. Now h_A shares the context with the
        #         prototype and h_C does not, so context works AGAINST the predicted sign. A
        #         positive score here cannot be explained by shared context.
        #   mu_C  the CODEWORD in the harmful context -- no concept token anywhere in it. This is
        #         the pure context reference: it measures how large "same context" alone is on
        #         this metric, and it is the number mu_B has to beat to mean anything.
        #
        # Every prototype is leave-one-domain-out.
        protos = {"B": "mu_B_concept_in_harm_ctx", "E": "mu_E_concept_in_benign_ctx",
                  "C": "mu_C_codeword_in_harm_ctx_CONTEXT_ONLY"}
        for cell_p, pname in protos.items():
            pvals = []
            for d in common:
                keep = [means["bomb"][(cell_p, x)][L_i] for x in common if x != d]
                muh = _unit(torch.stack(keep).mean(dim=0), torch)
                hc, ha = means["bomb"][("C", d)][L_i], means["bomb"][("A", d)][L_i]
                cc = float(torch.dot(hc, muh) / torch.linalg.vector_norm(hc))
                ca = float(torch.dot(ha, muh) / torch.linalg.vector_norm(ha))
                pvals.append(cc - ca)
            k_p = sum(1 for x in pvals if x > 0)
            p_p, f_p = sign_test_two_sided(k_p, len(pvals))
            out["metrics"]["B3proto|L%d|shift_bomb|proto_%s" % (L, cell_p)] = {
                "prototype": pname,
                "mean_delta_cos": mean(pvals), "sd": sd(pvals), "ci95": boot_ci(pvals, rng),
                "d_paired": cohen_d_paired(pvals), "n_domains": len(pvals), "n_positive": k_p,
                "sign_p": p_p, "sign_p_floor": f_p,
                "_reading": "cos(h_C, mu) - cos(h_A, mu), mu leave-one-domain-out"}

        # ---- AXIS GEOMETRY. The off-diagonal of the 3x3 cannot be read without it: if
        # v_lex(bomb) and v_lex(knife) are nearly the same direction, "the bomb shift also aligns
        # with the knife axis" is a statement about the axes, not about the shift. Both are
        # reported; neither is inferred from the other.
        vfull = {c: torch.stack([delta_EA[c][d][L_i] for d in common]).mean(dim=0)
                 for c in CONCEPTS}
        vhatf = {c: _unit(vfull[c], torch) for c in CONCEPTS}
        cosmat = {}
        for c1 in CONCEPTS:
            for c2 in CONCEPTS:
                cosmat["%s|%s" % (c1, c2)] = float(torch.dot(vhatf[c1], vhatf[c2]))

        # ---- CELL COORDINATES on the bomb axis, in gap units, relative to cell A. This is the
        # table that stops "traverses 10% of the gap" from flattering itself: it shows where all
        # FOUR cells sit, so the reader can see that C is at 0.10 while B is at 0.84 and E at 1.00.
        # It also kills one whole account: if harmful demonstrations simply pulled everything into
        # a single attractor, C and B would sit at the SAME coordinate. They do not. (S-002 IV 8.6)
        vb_hat_full = _unit(torch.stack([delta_EA["bomb"][d][L_i] for d in common]).mean(dim=0),
                            torch)
        gapb = gap["bomb"]
        coords = {}
        for cell in ("A", "C", "B", "E"):
            vals = []
            for d in common:
                delta = means["bomb"][(cell, d)][L_i] - means["bomb"][("A", d)][L_i]
                vals.append(float(torch.dot(delta, vb_hat_full)) / gapb)
            coords[cell] = {"mean_gap_units": mean(vals), "sd": sd(vals)}
        out.setdefault("cell_coordinates_on_bomb_axis", {})["L%d" % L] = {
            "coords": coords,
            "_reading": "gap units relative to cell A, on the FULL (in-sample) bomb axis. A is 0 "
                        "by construction and E is ~1 by construction; the informative rows are C "
                        "and B."}

        # ---- B1_resid FOR ALL THREE SHIFTS, not only bomb. The independent verification (8.4)
        # pointed out that computing the residualised projection only for the bomb shift cannot
        # tell you whether "the shift lands in the concept-SPECIFIC part of its own axis" is a
        # general property of the manipulation or a bomb-only one. It costs nothing, so it is run
        # for all three and the answer is reported whichever way it comes out.
        # Gram-Schmidt v_lex(bomb) against span{v_lex(knife), v_lex(gun)}, then project the
        # Doublespeak shift on what is left. If the whole alignment survives, it is not carried by
        # a shared "some other weapon word is here" component; if it collapses, it is.
        frac_kept_by_concept = {}
        for target in CONCEPTS:
            others = [c for c in CONCEPTS if c != target]
            basis = []
            for c in others:
                u = vfull[c].clone()
                for bvec in basis:
                    u = u - float(torch.dot(u, bvec)) * bvec
                nrm = float(torch.linalg.vector_norm(u))
                if nrm > 1e-8:
                    basis.append(u / nrm)
            resid = vfull[target].clone()
            for bvec in basis:
                resid = resid - float(torch.dot(resid, bvec)) * bvec
            rnorm = float(torch.linalg.vector_norm(resid))
            frac_kept = rnorm / float(torch.linalg.vector_norm(vfull[target]))
            frac_kept_by_concept[target] = frac_kept
            rhat = _unit(resid, torch)
            rvals_spec = [float(torch.dot(delta_CA[target][d][L_i], rhat)) / rnorm for d in common]
            k_spec = sum(1 for x in rvals_spec if x > 0)
            p_spec, f_spec = sign_test_two_sided(k_spec, len(rvals_spec))
            out["metrics"]["B1resid|L%d|shift_%s|ref_%s_minus_others" % (L, target, target)] = {
                "mean_resid_units": mean(rvals_spec), "sd_resid_units": sd(rvals_spec),
                "ci95_resid_units": boot_ci(rvals_spec, rng),
                "d_paired": cohen_d_paired(rvals_spec),
                "n_domains": len(rvals_spec), "n_positive": k_spec,
                "sign_p": p_spec, "sign_p_floor": f_spec,
                "resid_norm": rnorm,
                "frac_of_axis_orthogonal_to_the_other_two": frac_kept,
                "_reading": ("units are the RESIDUAL gap, not the full %s gap: the denominator is "
                             "the length of the part of the %s axis the other two concepts cannot "
                             "express (%.4f of it here). A large number over a tiny residual is "
                             "not a large effect." % (target, target, frac_kept))}
        frac_kept = frac_kept_by_concept["bomb"]
        out.setdefault("axis_geometry", {})["L%d" % L] = {
            "cos_between_lex_axes": cosmat,
            "lex_axis_norms": {c: float(torch.linalg.vector_norm(vfull[c])) for c in CONCEPTS},
            "frac_of_axis_orthogonal_to_the_other_two": frac_kept_by_concept}

        # ---- CONTROLS at this layer, for the diagonal cell only (bomb shift vs bomb ref)
        # C1 random unit directions, matched by construction to nothing but dimensionality
        rvals = []
        for j in range(n_random_draws):
            g = torch.Generator().manual_seed(20260909 + 1000 * L + j)
            v = _unit(torch.randn(delta_EA["bomb"][common[0]][L_i].shape, generator=g), torch)
            per = [float(torch.dot(delta_CA["bomb"][d][L_i], v)) / gap["bomb"] for d in common]
            rvals.append(mean(per))
        # LOO-LEAKAGE PROBE -- NOT A CONTROL, AND IT IS NO LONGER FILED AS ONE.
        # The independent verification (section 7.2) proved what this quantity actually is:
        # permuting which domain sits in which slot and then taking the LOO mean excluding slot d
        # gives (sum_all delta - delta[perm[d]]) / 66 -- so the permutation only changes WHICH
        # SINGLE DOMAIN is dropped from a 67-term mean, and the projected domain is now INSIDE the
        # axis. It is mathematically obliged to return approximately the IN-SAMPLE value, which is
        # >= the real one. Measured: 0.105600 against an independently computed in-sample 0.105566.
        # It therefore measures the leave-one-out leakage (about 1%), which is genuinely useful,
        # and it CANNOT PRODUCE A NULL. Sitting in a block called "controls" beside a quantity
        # whose job IS to produce a null, it invited the reading "we shuffled and the effect
        # survived". It is renamed and moved out.
        shuf = []
        for j in range(n_random_draws):
            r2 = random.Random(20260909 + 7717 * L + j)
            perm = list(common)
            r2.shuffle(perm)
            mp = {d: delta_EA["bomb"][p][L_i] for d, p in zip(common, perm)}
            per = []
            for d in common:
                vhat = _unit(loo_direction(mp, common, d, torch), torch)
                per.append(float(torch.dot(delta_CA["bomb"][d][L_i], vhat)) / gap["bomb"])
            shuf.append(mean(per))
        # C3 the harm-context axis at the CONCEPT token, projected on the same reference. If the
        # Doublespeak shift aligns with button->bomb but the harm-demo shift measured AT ` bomb`
        # does not, the alignment is not simply "harm demonstrations move everything that way".
        be = []
        for d in common:
            vhat = _unit(loo_direction({k: v[L_i] for k, v in delta_EA["bomb"].items()},
                                       common, d, torch), torch)
            be.append(float(torch.dot(delta_BE["bomb"][d][L_i], vhat)) / gap["bomb"])
        out["controls"]["L%d" % L] = {
            "random_unit_gap_units": {
                "mean_of_draw_means": mean(rvals),
                "between_draw_sd_from_%d_draws" % n_random_draws: sd(rvals),
                "between_draw_sd_ANALYTIC": (
                    float(torch.linalg.vector_norm(
                        torch.stack([delta_CA["bomb"][d][L_i] for d in common]).mean(dim=0)))
                    / (math.sqrt(len(delta_CA["bomb"][common[0]][L_i])) * gap["bomb"])),
                "n_draws": n_random_draws, "draws": rvals,
                "_why_the_analytic_sd_is_here": "12 draws estimate a standard deviation to about "
                    "+/-21%, so two banks printing 0.0015 +/- 0.0072 and 0.0009 +/- 0.0098 invite "
                    "a between-bank reading that is pure sampling noise. The analytic value costs "
                    "nothing and is the one to quote (S-002 IV 7.3)."},
            "_domain_shuffled_ref_MOVED": "see leakage_probe -- it is not a control (S-002 IV 7.2)",
            "harm_context_at_concept_token_gap_units": {
                "mean": mean(be), "sd": sd(be), "ci95": boot_ci(be, rng),
                "n_positive": sum(1 for x in be if x > 0), "n_domains": len(be)},
            "gap_norms": gap}
        out.setdefault("leakage_probe", {})["L%d" % L] = {
            "domain_shuffled_ref_gap_units": {"mean_of_draw_means": mean(shuf),
                                              "between_draw_sd": sd(shuf),
                                              "n_draws": n_random_draws, "draws": shuf},
            "_what_this_is": "a LEAVE-ONE-OUT LEAKAGE estimate, NOT a null control. It is obliged "
                             "to return approximately the in-sample value; the gap between it and "
                             "the LOO estimate is the leakage. It may never be quoted as a "
                             "control that the effect survived."}
    return out


# --------------------------------------------------------------------------- #
def selftest(torch) -> int:
    """Synthetic checks of every arithmetic step that could be silently wrong."""
    ok = True

    def chk(name, cond):
        nonlocal ok
        print("  %-46s %s" % (name, "PASS" if cond else "FAIL"))
        ok = ok and bool(cond)

    # EXACT pins on the reducers. The tolerance-based checks below cannot catch a reducer that is
    # subtly wrong (the mutation harness proved it: "mean() drops the last element" survived a
    # 30-domain check with a 0.05 tolerance). A reducer gets an exact test.
    chk("mean is exact", mean([1.0, 2.0, 3.0]) == 2.0 and mean([2.0]) == 2.0)
    chk("mean uses every element", mean([0.0, 0.0, 3.0]) == 1.0)
    chk("mean of empty is nan", math.isnan(mean([])))
    chk("sd is exact", abs(sd([1.0, 2.0, 3.0]) - 1.0) < 1e-12 and math.isnan(sd([1.0])))
    chk("cohen d is exact", abs(cohen_d_paired([1.0, 2.0, 3.0]) - 2.0) < 1e-12)

    p, f = sign_test_two_sided(23, 23)
    chk("sign test 23/23 == 2/2^23", abs(p - 2.0 / 2 ** 23) < 1e-18 and abs(f - p) < 1e-18)
    p, _ = sign_test_two_sided(12, 23)
    chk("sign test 12/23 is not significant", p > 0.5)
    chk("sign test is symmetric", sign_test_two_sided(3, 10)[0] == sign_test_two_sided(7, 10)[0])

    # unit / zero refusal
    try:
        _unit(torch.zeros(8), torch)
        chk("zero direction refused", False)
    except Refusal:
        chk("zero direction refused", True)

    # LOO really leaves one out
    d = {"a": torch.tensor([1.0, 0.0]), "b": torch.tensor([0.0, 1.0]), "c": torch.tensor([1.0, 1.0])}
    m = loo_direction(d, ["a", "b", "c"], "c", torch)
    chk("LOO excludes the held-out domain", abs(float(m[0]) - 0.5) < 1e-6
        and abs(float(m[1]) - 0.5) < 1e-6)
    try:
        loo_direction({"a": torch.tensor([1.0])}, ["a"], "a", torch)
        chk("LOO refuses n<2", False)
    except Refusal:
        chk("LOO refuses n<2", True)

    # a planted signal is recovered at the right magnitude, in gap units
    H = 64
    g = torch.Generator().manual_seed(1)
    axis = _unit(torch.randn(H, generator=g), torch)
    doms = ["d%02d" % i for i in range(30)]
    dEA = {d: axis * 3.0 + 0.1 * torch.randn(H, generator=g) for d in doms}
    dCA = {d: axis * 1.5 + 0.1 * torch.randn(H, generator=g) for d in doms}
    gapn = float(torch.linalg.vector_norm(torch.stack([dEA[d] for d in doms]).mean(dim=0)))
    vals = [float(torch.dot(dCA[d], _unit(loo_direction(dEA, doms, d, torch), torch))) / gapn
            for d in doms]
    chk("planted 0.50 gap-unit signal recovered", abs(mean(vals) - 0.5) < 0.05)

    # an ORTHOGONAL shift scores ~0 in gap units
    orth = torch.randn(H, generator=g)
    orth = _unit(orth - float(torch.dot(orth, axis)) * axis, torch)
    dCA2 = {d: orth * 1.5 for d in doms}
    vals2 = [float(torch.dot(dCA2[d], _unit(loo_direction(dEA, doms, d, torch), torch))) / gapn
             for d in doms]
    chk("orthogonal shift scores ~0", abs(mean(vals2)) < 0.05)

    # cohen d of a constant-mean, zero-variance vector is not a finite number pretending to be one
    chk("d_paired on zero variance is nan", math.isnan(cohen_d_paired([1.0, 1.0, 1.0])))
    return 0 if ok else 1


def mutate(torch) -> int:
    """Every mutation must be caught by selftest. A verifier that survives its own sabotage is
    not a verifier (successor plan section 24.8)."""
    import copy
    g = globals()
    muts = []

    def add(name, target, repl):
        muts.append((name, target, repl))

    add("sign test drops the two-sided factor", "sign_test_two_sided",
        lambda k, n: (min(1.0, sum(math.comb(n, i) for i in range(max(k, n - k), n + 1)) / 2.0 ** n),
                      2.0 / 2 ** n))
    add("LOO stops leaving one out", "loo_direction",
        lambda pd, doms, held, t: t.stack([pd[d] for d in doms]).mean(dim=0))
    add("unit() stops normalising", "_unit", lambda v, t: v)
    add("mean() drops the last element", "mean",
        lambda v: (sum(v[:-1]) / (len(v) - 1)) if len(v) > 1 else float("nan"))

    red = 0
    for name, target, repl in muts:
        orig = g[target]
        g[target] = repl
        try:
            import io
            buf, old = io.StringIO(), sys.stdout
            sys.stdout = buf
            try:
                rc = selftest(torch)
            finally:
                sys.stdout = old
            caught = (rc != 0)
        except Exception:
            caught = True
        finally:
            g[target] = orig
        red += caught
        print("  MUTATION %-46s %s" % (name, "RED (caught)" if caught else "GREEN -- NOT CAUGHT"))
    print("  %d/%d mutations caught" % (red, len(muts)))
    return 0 if red == len(muts) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="train", choices=["train", "validation", "test"])
    ap.add_argument("--i-am-the-frozen-analyzer", action="store_true",
                    help="required to read anything but train; nothing in this phase passes it")
    ap.add_argument("--codewords", default="button,basket")
    ap.add_argument("--out", default=os.path.join(REPO, "outputs", "dcs_succ",
                                                  "bombness_candidates.json"))
    ap.add_argument("--n-random-draws", type=int, default=12)
    ap.add_argument("--seed", type=int, default=20260909)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--mutate", action="store_true")
    a = ap.parse_args()

    import torch
    torch.set_num_threads(4)

    if a.selftest:
        print("=== selftest ===")
        return selftest(torch)
    if a.mutate:
        print("=== mutation harness ===")
        return mutate(torch)

    if a.split != "train" and not a.i_am_the_frozen_analyzer:
        raise Refusal("this module is EXPLORATORY and reads TRAIN only. Reading %r would spend a "
                      "split that a later confirmatory test needs untouched." % a.split)

    assign, manifest = split_map()
    doms = sorted(d for d, s in assign.items()
                  if s == a.split and d not in EXCLUDED_DOMAINS)
    print("[cand] split=%s domains=%d (manifest assigns %d, minus %d exclusions)"
          % (a.split, len(doms), sum(1 for s in assign.values() if s == a.split),
             len(EXCLUDED_DOMAINS)), file=sys.stderr)

    rng = random.Random(a.seed)
    res = {"_label": "EXPLORATORY -- TRAIN ONLY. No number here may be quoted as confirmatory.",
           "split": a.split, "n_domains_requested": len(doms), "seed": a.seed,
           "split_manifest": os.path.relpath(SPLIT_MANIFEST, REPO),
           "query_kind": QUERY_KIND, "n_examples": DOSE, "position": "codeword_last",
           "by_codeword": {}}
    for cw in a.codewords.split(","):
        cw = cw.strip()
        if cw not in CODEWORDS:
            raise Refusal("unknown codeword %r" % cw)
        res["by_codeword"][cw] = analyse(cw, doms, torch, rng, a.n_random_draws)

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print("[cand] wrote %s" % a.out, file=sys.stderr)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Refusal as e:
        print("REFUSING: %s" % e, file=sys.stderr)
        raise SystemExit(2)
