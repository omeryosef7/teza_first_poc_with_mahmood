#!/usr/bin/env python3
"""PR-CSI RUNG 2 INSTRUMENT: is the CONCEPT readable from a single (layer, head) CELL?

⛔ EXPLORATORY. THIS FILE COMPUTES NO VERDICT AND NO p. It emits a measurement; a preregistered
reader decides what it means. Nothing here may be quoted as a result.

WHY IT EXISTS (S-378..S-382). Every claim in this sprint is RUNG 1 on AM-34's ladder -- ablation
damage, i.e. NECESSITY. Rung 2 is DECODABILITY, and the ladder's own warning is that the rungs are
separable: *"information may be readable at a site without being used there."* The sprint already
had a published probe result (D2/D3's QPROBE) and S-378 established it is NOT rung 2 for these
claims, on four grounds -- the decisive one being that its layer grid {16,18,20,22,24,26,28,30,31}
and the causal band {6..14} have EMPTY intersection.

WHAT IT COMPUTES. For each prompt, the contribution of cell (L, h) to the readout position, along
the model's own concept-minus-codeword direction, summed over the DEMONSTRATION BLOCK source
positions -- the ones `demo_all` knocks out:

    contrib(L, h) = sum over demo keys s of   A[L,h,dst,s] * <W_O[L,h] v[L,h,s], u_hat>

`dominance_at` supplies exactly that (`D_dir[L]` is [n_head, T]); this file supplies the direction,
the destination, the source set, and the per-DOMAIN aggregation.

THE DIRECTION, frozen in S-382 before any measurement so it cannot be tuned afterwards:

    u = g_final  *  [ mean(W[' bomb'], W[' Bomb'])  -  mean(W[' basket'], W[' Basket']) ]

  * g_final is the FINAL RMSNorm gain, FOLDED IN. S-380 verified to |diff| = 0.000e+00 that
    <norm(h), W> = (1/rms(h)) * <h, g*W>, so folding the gain makes the projection exact up to one
    POSITIVE scalar per destination -- which is common to every cell and therefore cannot reorder
    an argmax across cells at that destination.
  * MEAN of casings, not one casing. Both are LINEAR, which is what makes the per-cell
    decomposition exact (S-380: linear |diff| 7.58e-15, logsumexp |diff| 6.89e-01). Lowercase-only
    would add a free choice a later reader could not distinguish from tuning; the mean uses exactly
    the four rows the bank's own readout declares.
  * ⚠ The token ids are PARAMETERS here, not constants. `scripts/dcs_cont_logitlens_control.py`
    hardcodes ' button'/' Button' (S-380) and the entire CSI cell line is BASKET; running that file
    unchanged over basket cells would compute a well-formed number for a question nobody asked.
    That is this sprint's most persistent defect class -- a family-specific literal surviving a
    widening (R29/S-322, S-308, S-357) -- so the ids are required arguments with no defaults.

⚠⚠ WHAT THIS QUANTITY IS NOT (S-381/S-382). The endpoint `y_install` aggregates the casings with
LOGSUMEXP; this direction aggregates them LINEARLY. They are built from the same four unembedding
rows and the same two surfaces, and nothing more may be claimed. It MAY NOT be said that this
decomposes y_install, that the per-cell contributions sum to the endpoint, or that a cell's share
here is its share of the installation effect. The difference is UNMEASURED: the per-variant
log-probabilities are not recorded anywhere on disk (S-381 section 2, S-382 section 1).

⚠ `dominance_at` UNIT-NORMALIZES the direction (`u = u / u.norm()`). The same `u` is passed at every
band layer, so the constant is identical across layers and the cross-layer argmax is unaffected --
but the emitted magnitudes are in units of the UNIT direction and are NOT logit contributions.

DOMAIN IS THE STATISTICAL UNIT (PART I). Per-prompt values are averaged within a domain first, and
only domain means are emitted.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src"))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))


def _ids(s: str, what: str):
    try:
        v = tuple(int(x) for x in s.split(",") if x.strip())
    except ValueError:
        raise SystemExit("REFUSING: --%s must be a comma list of integer token ids, got %r"
                         % (what, s))
    if not v:
        raise SystemExit("REFUSING: --%s is empty. The direction cannot be built from no rows, and "
                         "a default here is how a button constant ends up in a basket family "
                         "(S-380)." % what)
    return v


def lm_tok_decode(_a, tid):
    """Decode one id for the witness line. Kept trivial and local: the point is that a wrong-family
    run becomes VISIBLE in the log, not that this is a general utility."""
    try:
        from transformers import AutoTokenizer
        global _TOK
        try:
            _TOK
        except NameError:
            _TOK = AutoTokenizer.from_pretrained(_a.model)
        return _TOK.decode([tid])
    except Exception as e:                      # a witness must never break the run
        return "<undecodable: %s>" % str(e)[:40]


def build_direction(norm_w, rows, concept_ids, codeword_ids):
    """u = g_final * (mean of concept rows - mean of codeword rows).

    Kept separate from any model call so it can be tested without a GPU."""
    import torch
    c = torch.stack([rows[t] for t in concept_ids], 0).mean(0)
    k = torch.stack([rows[t] for t in codeword_ids], 0).mean(0)
    return norm_w.float() * (c - k)


def load_unembed(snapshot_glob, want_ids):
    """The final RMSNorm weight and exactly the requested unembedding rows. Nothing else."""
    import torch
    from safetensors import safe_open
    snaps = sorted(glob.glob(snapshot_glob))
    if not snaps:
        raise SystemExit("REFUSING: no model snapshot matched %r" % snapshot_glob)
    snap = snaps[0]
    idx = json.load(open(os.path.join(snap, "model.safetensors.index.json")))["weight_map"]
    need = {}
    for key in ("model.norm.weight", "lm_head.weight"):
        if key not in idx:
            raise SystemExit("REFUSING: %s absent from the weight map; tied embeddings are not "
                             "handled and guessing one is not a substitute." % key)
        need.setdefault(idx[key], []).append(key)
    norm_w, rows = None, {}
    for shard, keys in need.items():
        with safe_open(os.path.join(snap, shard), framework="pt") as f:
            for key in keys:
                if key == "model.norm.weight":
                    norm_w = f.get_tensor(key).float()
                else:
                    sl = f.get_slice(key)
                    for tid in want_ids:
                        rows[tid] = sl[tid:tid + 1, :][0].float()
    if norm_w is None or len(rows) != len(set(want_ids)):
        raise SystemExit("REFUSING: failed to read the norm weight or every requested row")
    return norm_w, rows, snap


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bank", required=True)
    ap.add_argument("--split", required=True, choices=["train", "validation"],
                    help="TEST is never touched (PART I) and is not a choice here.")
    ap.add_argument("--exclude-prompt-ids", required=True,
                    help="the prompt-id exclusion file. S-381 measured that this FILE, not the "
                         "prereg, is what actually keeps TEST out -- the prereg's own leak check "
                         "is vacuous (S-375). It is therefore REQUIRED, not optional.")
    ap.add_argument("--model", required=True)
    ap.add_argument("--snapshot-glob", required=True)
    ap.add_argument("--band", default="6-14")
    ap.add_argument("--heads", required=True, help="comma list, e.g. 4,6,10,11,13,18,21,27")
    ap.add_argument("--concept-ids", required=True, help="e.g. 13054,33909 for ' bomb',' Bomb'")
    ap.add_argument("--codeword-ids", required=True, help="e.g. 14351,34217 for ' basket',' Basket'")
    # ⚠⚠ R35/S-384 -- THESE THREE EXIST BECAUSE THEIR ABSENCE WAS A TEST-TOUCHING BLOCKER.
    # The first draft filtered only on query_kind, cell and the exclusion file. That selects 926
    # rows over 116 DOMAINS -- the exclusion file only removes the non-validation part of ONE
    # bank_block/condition slice, so every OTHER slice survives untouched, and the 116 domains
    # include the TRAIN and TEST domains. The arms' real population is
    # cell C + semantic_one_word + bank_block cds_n4_sow + condition natural_doublespeak + NOT
    # excluded = 230 rows over 23 domains, which reproduces the arms exactly. Without these the
    # instrument would have read TEST and emitted a well-formed number while doing it.
    ap.add_argument("--bank-block", required=True,
                    help="e.g. cds_n4_sow. REQUIRED: without it the exclusion file leaves every "
                         "other block in, including TEST domains.")
    ap.add_argument("--condition", required=True,
                    help="e.g. natural_doublespeak. REQUIRED, same reason.")
    ap.add_argument("--expect-n", type=int, required=True,
                    help="rows the selection MUST yield. A population that does not match what "
                         "was declared is not the population (R20-6).")
    ap.add_argument("--expect-domains", type=int, required=True,
                    help="domains the selection MUST yield.")
    ap.add_argument("--answer-prefix", required=True,
                    help='⚠⚠ R35-B/S-385. REQUIRED, NO DEFAULT. The endpoint does NOT read at the '
                         'end of the templated prompt: score_behavior appends --answer-prefix '
                         '(default "Answer:") and reads the position AFTER it. The first draft '
                         'used seq_len-1 on the bare prompt -- 2 tokens upstream, across the '
                         '"Answer" ":" boundary -- which is the position score_behavior:3173 '
                         'MEASURED to hold a median 5.6e-06 of next-token mass and abandoned on '
                         '2026-08-18. Pass the SAME value the arms used, or "" to reproduce that '
                         'abandoned tail deliberately.')
    ap.add_argument("--dtype", required=True, choices=["bfloat16", "float32"],
                    help='⚠ REQUIRED, NO DEFAULT (S-388). The first draft hardcoded float32, which '
                         '(a) is ~32 GB for an 8B model and does not fit the partition\'s 24 GB '
                         '3090s, and (b) is NOT what the arms ran -- every PR-CSI-020 arm records '
                         'dtype bfloat16. Measuring a MORE precise forward than the family this '
                         'sits beside is a different computation, silently. Pass what the arms '
                         'passed unless you mean otherwise. NOTE dominance_at adapts its '
                         'reconstruction tolerance by weight dtype (1e-3 fp32, 3e-2 bf16) and the '
                         'decomposition itself is computed in float32 on CPU either way.')
    ap.add_argument("--limit", type=int, default=0, help="0 = all rows; >0 for a smoke run")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    import torch
    # ⚠ R35-B/C/S-385: THIS SAID `import common as dc` AND THE FILE COULD NOT RUN. `common` is
    # src/boombness/common.py, which defines NEITHER load_model NOR apply_template -- it exposes
    # ds() and inserts the ds path as a side effect. Every sibling CSI script imports ds_common.
    # The failure was an AttributeError AFTER load_unembed had read the safetensors shards, i.e.
    # minutes into a GPU job. It is loud, so it is not in the silent hazard class -- but it proves
    # the file had NEVER been executed end to end when S-383 described what it "computes".
    import common as _common          # side effect: puts doublespeak_causality on sys.path
    import ds_common as dc
    import score_behavior as sb
    from dominance import dominance_at

    lo, hi = (int(x) for x in a.band.split("-"))
    band = list(range(lo, hi + 1))
    heads = [int(x) for x in a.heads.split(",")]
    cids, kids = _ids(a.concept_ids, "concept-ids"), _ids(a.codeword_ids, "codeword-ids")
    if set(cids) & set(kids):
        raise SystemExit("REFUSING: the concept and codeword id sets overlap (%s). The direction "
                         "would be degenerate." % sorted(set(cids) & set(kids)))

    # ⚠ the exclusion files carry a `#` COMMENT HEADER naming the selection they were derived
    # from. Reading them without stripping comments silently adds two non-ids to the set -- inert
    # here, but it inflates any count taken from it, so it is dropped explicitly.
    # ⚠⚠ R35-B/C/S-385: `--split` WAS DECORATIVE -- recorded in the artefact, never compared to a
    # row. S-384's population gate compares COUNTS against numbers the OPERATOR TYPED, so a
    # test-bearing block with honestly-typed expectations passed it cleanly (measured:
    # --bank-block cds_n8_sow --expect-n 464 --expect-domains 116 -> all 23 TEST domains, gate
    # PASSES). The gate's PASS was fully consistent with having read TEST, which is the rule this
    # sprint states as "absence is not a check". The split manifest is now read and ENFORCED, so
    # TEST is unreachable regardless of what is declared.
    _sp = json.load(open(os.path.join(REPO, "data", "boombness_prompts",
                                      "dcs_ts116_domain_split.json")))
    _assign = _sp.get("assign") or _sp.get("assignments") or {}
    if not _assign:
        raise SystemExit("REFUSING: the domain split manifest carries no assignment map, so the "
                         "split cannot be enforced. Absence is not a guard (R20-6).")
    # the three preregistered whole-population domains, excluded by the endpoint at
    # dcs_cont_layerpos_map.py:49. S-385: they are absent from validation only BY ACCIDENT of the
    # split (all three are train), so relying on that would readmit them on any train run.
    EXCLUDED_DOMAINS = ("restaurant_kitchen", "school_campus", "subway_station")
    keep_dom = {d for d, sp in _assign.items() if sp == a.split} - set(EXCLUDED_DOMAINS)
    if not keep_dom:
        raise SystemExit("REFUSING: no domains are assigned to split %r." % a.split)
    excl = {l.strip() for l in open(a.exclude_prompt_ids)
            if l.strip() and not l.lstrip().startswith("#")}
    rows = []
    for line in open(a.bank):
        r = json.loads(line)
        if r.get("query_kind") != "semantic_one_word" or r.get("cell") != "C":
            continue
        if r.get("bank_block") != a.bank_block or r.get("condition") != a.condition:
            continue
        if r.get("prompt_id") in excl:
            continue
        if r.get("domain") not in keep_dom:      # ⚠ R35/S-385: TEST is structurally unreachable
            continue
        rows.append(r)
    n_sel, n_dom = len(rows), len({r["domain"] for r in rows})
    print("[rung2] population: %d rows over %d domains (block=%s condition=%s, %d ids excluded)"
          % (n_sel, n_dom, a.bank_block, a.condition, len(excl)), flush=True)
    if (n_sel, n_dom) != (a.expect_n, a.expect_domains):
        raise SystemExit(
            "REFUSING: the selection yields %d rows over %d domains, but --expect-n %d and "
            "--expect-domains %d were declared. The first draft of this file omitted the "
            "bank_block and condition filters and selected 926 rows over 116 DOMAINS -- which "
            "includes the TEST domains, because the exclusion file only removes the non-validation "
            "part of ONE slice. A population that does not match what was declared is not the "
            "population. (R35/S-384)" % (n_sel, n_dom, a.expect_n, a.expect_domains))
    if a.limit:
        rows = rows[:a.limit]
        print("[rung2] ⚠ --limit %d: this is a SMOKE sample, NOT the declared population, and the "
              "artefact records it as such." % a.limit, flush=True)
    if not rows:
        raise SystemExit("REFUSING: no rows survived. Absence is not a measurement (R20-6).")

    norm_w, urows, snap = load_unembed(a.snapshot_glob, list(cids) + list(kids))
    u = build_direction(norm_w, urows, cids, kids)
    print("[rung2] direction built from %d concept + %d codeword rows; |u| = %.6f"
          % (len(cids), len(kids), float(u.norm())), flush=True)
    print("[rung2] ids decode to: concept %r  codeword %r"
          % ([lm_tok_decode(a, t) for t in cids], [lm_tok_decode(a, t) for t in kids]), flush=True)

    _dt = {"bfloat16": torch.bfloat16, "float32": torch.float32}[a.dtype]
    _tload = time.time()
    lm = dc.load_model(a.model, dtype=_dt, attn_implementation="eager")
    print("[rung2] model loaded in %.1fs" % (time.time() - _tload), flush=True)
    _t0 = time.time()
    et = False
    per_dom = {}          # domain -> {(L,h): [values]}
    n_done, skipped, recon = 0, {}, None
    rms_seen = []
    RMS_EPS = float(getattr(lm.model.config, "rms_norm_eps", 1e-5))
    for i, r in enumerate(rows):
        templated = dc.apply_template(lm.tokenizer, r["full_prompt"], enable_thinking=et)
        dk, why = sb.demo_key_positions(lm.tokenizer, r, templated)
        if why:
            skipped[why] = skipped.get(why, 0) + 1
            continue
        # ⚠⚠ R35-B/S-385 -- THE FIRST DRAFT READ THE WRONG POSITION, and S-383's commit message
        # claimed the opposite. It took `dst = len(tokenize(templated)) - 1` from
        # retrieval_strength.py:178, which computes a DESCRIPTIVE ATTENTION-MASS SCALAR and has no
        # answer prefix and no readout ids. The endpoint reads `templated + answer_prefix`
        # (score_behavior.py:87 and :3914). Borrowing a "readout index" from a file that does not
        # do the readout is precisely the hazard this review existed to catch.
        ids_ctx = lm.tokenizer(templated + a.answer_prefix,
                               add_special_tokens=False)["input_ids"]
        ids = ids_ctx
        seq_len = len(ids)
        dst = seq_len - 1
        # A REAL check, not the tautology the first draft shipped (`assert dst == len(ids)-1`
        # restated the line above it and could not fail): the context must actually END with the
        # answer prefix, which is what makes `dst` the endpoint's position.
        if a.answer_prefix:
            _tail = lm.tokenizer.decode(ids[-4:])
            if a.answer_prefix.strip() and a.answer_prefix.strip() not in _tail:
                raise SystemExit(
                    "REFUSING: the tokenized context does not end with --answer-prefix %r (tail "
                    "decodes to %r). The readout position would not be the endpoint's. (R35-B/S-385)"
                    % (a.answer_prefix, _tail))
        # ⚠ R35-B/C/S-385: a `if not dk` branch stood here and was UNREACHABLE --
        # demo_key_positions returns ([], reason) on every failure path, so `why` already caught
        # it. Its skip counter could never appear, and a reader could have taken that absence as
        # evidence. Removed rather than left as a comforting no-op.
        # ⚠ R35-B/C/S-385: this was `check_invariants=(i == 0)`, and `i` enumerates rows INCLUDING
        # skipped ones. If row 0 skipped, the reconstruction check -- the ONLY thing standing
        # between this and a wrong GQA head map or o_proj slicing -- never ran for the whole run,
        # and nothing on disk said so. It is now keyed on the first row that actually REACHES the
        # call, and the error it returns is RECORDED rather than discarded.
        # ⚠⚠ R35-A/S-387 -- THE PER-PROMPT 1/rms IS **NOT** COMMON ACROSS THE AGGREGATION.
        # `D_dir` returns <Y, u_hat> = <Y,u>/||u||, while the TRUE logit-difference contribution is
        # <Y,u>/rms_p. So the emitted value is `true x rms_p/||u||`. ||u|| is one global constant
        # and is harmless; rms_p varies PER PROMPT, so averaging the raw values over ~230 prompts
        # gives an RMS-WEIGHTED mean of logit contributions, not a mean -- and R35-A exhibited a
        # two-cell, two-prompt case where that WEIGHTING FLIPS THE ARGMAX.
        # The docstring's units note defended the argmax on the grounds that 1/rms is shared "at
        # that destination", which is true WITHIN a prompt and false across the aggregation it
        # actually emits.
        # Fixed exactly rather than documented: capture rms_p from the model's own final norm --
        # a pre-hook on the module, firing inside dominance_at's forward, so it is the SAME
        # forward and the SAME dst -- and divide. The emitted numbers are then logit-difference
        # contributions and the aggregation is a plain mean.
        _cap = {}

        def _grab(_m, _inp):
            _cap["h"] = _inp[0].detach()[0, dst, :].float().cpu()

        _h = lm.model.model.norm.register_forward_pre_hook(_grab)
        try:
            res = dominance_at(lm, ids, dst=dst, layers=band,
                               direction={L: u for L in band},
                               check_invariants=(n_done == 0))
        finally:
            _h.remove()
        if "h" not in _cap:
            raise SystemExit(
                "REFUSING: the final-norm pre-hook never fired, so rms could not be captured and "
                "the emitted values would be RMS-WEIGHTED rather than logit contributions. "
                "Absence is not a normalisation (R20-6). (R35-A/S-387)")
        _rms = float((_cap["h"].pow(2).mean() + RMS_EPS).sqrt())
        if not (_rms > 0):
            raise SystemExit("REFUSING: captured rms = %r at dst; cannot normalise." % _rms)
        rms_seen.append(_rms)
        if n_done == 0:
            recon = {("L%d" % L): float(v) for L, v in (res.get("recon_rel_err") or {}).items()}
        d = per_dom.setdefault(r["domain"], {})
        for L in band:
            Dd = res["D_dir"][L]                      # [n_head, T]
            for h in heads:
                # /_rms converts <Y,u_hat> into the logit-difference contribution.
                d.setdefault((L, h), []).append(float(Dd[h, dk].sum()) / _rms)
        n_done += 1
        _el = time.time() - _t0
        if n_done == 1 or n_done % 5 == 0:
            print("[rung2] %d/%d prompts  elapsed %.1fs  %.2fs/prompt  (proj. %.1f min for %d)"
                  % (n_done, len(rows), _el, _el / n_done,
                     (_el / n_done) * n_sel / 60.0, n_sel), flush=True)

    if not per_dom:
        raise SystemExit("REFUSING: every row was skipped (%s). Absence is not a measurement."
                         % skipped)

    domains = sorted(per_dom)
    cell_mean = {}
    for L in band:
        for h in heads:
            vals = [statistics.fmean(per_dom[dm][(L, h)]) for dm in domains
                    if (L, h) in per_dom[dm]]
            cell_mean["L%d_h%d" % (L, h)] = statistics.fmean(vals) if vals else None

    out = {
        "schema": "DCS_CSI_RUNG2/1",
        "⛔ STATUS": "EXPLORATORY MEASUREMENT. No verdict, no p, no preregistration. "
                    "Nothing here may be quoted as a result.",
        "bank": a.bank, "split": a.split, "model_snapshot": snap,
        "bank_block": a.bank_block, "condition": a.condition,
        "declared_expect_n": a.expect_n, "declared_expect_domains": a.expect_domains,
        "selection_n_rows": n_sel, "selection_n_domains": n_dom,
        "limit_applied": a.limit or None,
        "⚠ IS_SMOKE": bool(a.limit),
        "exclude_prompt_ids": a.exclude_prompt_ids, "n_excluded_ids": len(excl),
        "band": band, "heads": heads,
        "concept_ids": list(cids), "codeword_ids": list(kids),
        "direction": "g_final * (mean(concept rows) - mean(codeword rows)); FROZEN S-382",
        "⚠ NOT_THE_ENDPOINT": "y_install aggregates the casings with LOGSUMEXP; this direction is "
                              "LINEAR. This does NOT decompose y_install and no cell's share here "
                              "is its share of the installation effect (S-381/S-382).",
        "⚠ UNITS": "values are DIVIDED BY the per-prompt rms captured from the model's own final "
                   "norm, so they ARE logit-difference contributions up to the single global "
                   "constant ||u|| (dominance_at unit-normalizes the direction). ||u|| is shared "
                   "by every cell at every layer and cannot reorder anything. ⚠ Before S-387 the "
                   "raw <Y,u_hat> was averaged, which is an RMS-WEIGHTED mean and can flip an "
                   "argmax across prompts (R35-A).",
        "dtype": a.dtype,
        "u_norm": float(u.norm()),
        "rms_at_dst": ({"n": len(rms_seen), "min": min(rms_seen), "max": max(rms_seen),
                        "mean": statistics.fmean(rms_seen)} if rms_seen else None),
        "statistical_unit": "domain", "n_domains": len(domains), "domains": domains,
        "n_prompts_used": n_done, "skipped": skipped,
        "timing": {"model_load_s": round(_t0 - _tload, 1),
                   "measure_s": round(time.time() - _t0, 1),
                   "per_prompt_s": (round((time.time() - _t0) / n_done, 3) if n_done else None),
                   "projected_full_population_min":
                       (round((time.time() - _t0) / n_done * n_sel / 60.0, 1) if n_done else None)},
        "answer_prefix": a.answer_prefix,
        "readout_position": "len(tokenize(templated + answer_prefix)) - 1 -- the position the "
                            "ENDPOINT reads (score_behavior.py:87). NOT the end of the bare "
                            "prompt, which score_behavior measured at ~5.6e-06 option mass and "
                            "abandoned 2026-08-18. (R35-B/S-385)",
        "recon_rel_err_first_row": recon,
        "split_enforced_from": "data/boombness_prompts/dcs_ts116_domain_split.json",
        "cell_mean_over_domains": cell_mean,
        "per_domain": {dm: {"L%d_h%d" % k: statistics.fmean(v) for k, v in per_dom[dm].items()}
                       for dm in domains},
    }
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=False)
    print("[rung2] %d prompts over %d domains -> %s" % (n_done, len(domains), a.out))
    if skipped:
        print("[rung2] skipped: %s" % skipped)
    print("[rung2] ⛔ EXPLORATORY. No verdict computed and none may be inferred.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
