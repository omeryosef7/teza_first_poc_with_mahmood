"""W2 -- the section 3.4 TRUE-PATCH GATE: does the AtP screen deserve to be believed at all?

WHAT THIS DECIDES. W1's screen is a FIRST-ORDER estimate of an intervention nobody performed.
This script performs the intervention. For each of the top-k cells (L,h) proposed by the screen it
patches the KNOCKOUT z for that single head at p* into an otherwise CLEAN forward with a real
`ZHeadPatch`, measures the true `delta M`, and correlates estimate against truth.

  Pearson AND Spearman both >= --min-corr  ->  the screen's ranking may be used.
  Either below                             ->  UNTRUSTWORTHY. The causal stage is NOT launched on
                                               this ranking; design 3.4 states the fallback in
                                               advance (select by true single-head patch effect on
                                               a 40-row subsample) so it cannot be invented later.

THE ESTIMATE BEING VALIDATED IS THE ROW'S OWN, NOT THE SCREEN'S SUM. Correlating a per-row truth
against a ranking summed over 670 rows would be a category error -- it would mix between-row
variation into a within-row comparison and could pass or fail for reasons having nothing to do with
the estimator. The screen is used ONLY to choose WHICH cells to test; every number correlated here
is computed in this process, for that row.

Lifted from 49_head_attribution.py:120-158 (the gate) with the arithmetic of W1.
"""
import argparse, json, os, sys, importlib.util
from contextlib import contextmanager

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "doublespeak_causality"))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))

import torch
import ds_common as dc
import pair_common as pc
import signals as sg


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sb = _load("sb", os.path.join(REPO, "src", "boombness", "score_behavior.py"))
# pearson/spearman are reused rather than rewritten: 49's gate uses exactly these (49:133-134).
atp48 = _load("atp48", os.path.join(REPO, "doublespeak_causality", "48_attribution_patching.py"))
w1 = _load("w1", os.path.join(REPO, "scripts", "dcs_csi_head_atp.py"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen", required=True, help="the W1 screen artifact whose cells are tested")
    ap.add_argument("--bank", default="data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl")
    ap.add_argument("--axis", default="configs/dcs_csi_axis_basket_behavioral.pt")
    ap.add_argument("--codeword", required=True)
    ap.add_argument("--concept", required=True)
    ap.add_argument("--allow-heldout", action="store_true",
                    help="required to touch VALIDATION; absent, --split validation refuses")
    ap.add_argument("--split", default="train")
    ap.add_argument("--bank-block", default="cds_n4_sow")
    ap.add_argument("--band", default="6-14")
    ap.add_argument("--answer-prefix", default=" Answer:")
    ap.add_argument("--row-sampling", choices=("stratified", "head"), default="stratified",
                    help="stratified = round-robin over domains; head = the first N rows")
    ap.add_argument("--gate-rows", type=int, default=40, help="row subsample the gate is measured on")
    ap.add_argument("--topk", type=int, default=40, help="cells taken from the screen")
    ap.add_argument("--min-corr", type=float, default=0.7, help="design 3.4: BOTH correlations")
    ap.add_argument("--model", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    scr = json.load(open(a.screen))

    # THE GATE MUST AGREE WITH THE SCREEN IT IS GATING (R14 finding 4).
    # Before this, the gate read topk_cells_by_abs and NOTHING ELSE: a `basket` screen could be
    # gated against `button` rows, a TRAIN screen against VALIDATION rows, or a screen from another
    # band, block or model -- and it would report a correlation. Worse, the artifact records the
    # GATE's own split/codeword, so the mismatch would be invisible to every later reader.
    for field, mine in (("split", a.split), ("band", a.band), ("bank_block", a.bank_block),
                        ("codeword", a.codeword), ("concept", a.concept)):
        theirs = scr.get(field)
        if theirs != mine:
            sys.exit("REFUSING: screen %s=%r but this gate was invoked with %r -- a gate that does "
                     "not match its screen measures nothing" % (field, theirs, mine))
    cells = [(int(c["layer"]), int(c["head"])) for c in scr["topk_cells_by_abs"][:a.topk]]
    if not cells:
        sys.exit("VACUOUS: the screen proposed no cells")
    lo, hi = (int(x) for x in a.band.split("-"))
    band = list(range(lo, hi + 1))
    if set(L for L, _ in cells) - set(band):
        sys.exit("REFUSING: the screen proposes cells outside the band under test")

    ax = torch.load(a.axis, map_location="cpu", weights_only=False)["meta"]
    if a.split == "validation" and not a.allow_heldout:
        sys.exit("REFUSING: --split validation touches HELD-OUT domains. Pass "
                 "--allow-heldout to say so deliberately.")
    keep = set(ax["fit_population"]["domains"] if a.split == "train"
               else ax["held_out_validation_domains"])
    rows = [json.loads(l) for l in open(a.bank)]
    rows = [r for r in rows
            if r.get("query_kind") == "semantic_one_word" and r.get("cell") == "C"
            and r.get("condition") == "natural_doublespeak" and r.get("n_examples") == 4
            and r.get("bank_block") == a.bank_block and r.get("domain") in keep]
    # THE STATISTICAL UNIT IS THE DOMAIN, SO THE SUBSAMPLE SPANS DOMAINS (R14 finding 1).
    # `rows[:40]` looked like "40 rows". The bank is ordered by domain at 10 consecutive rows each,
    # so it was the first FOUR domains -- power_substation, quarry_site, dairy_plant, textile_mill --
    # and "40 of 40 rows pass" was really n=4 units. Round-robin over domains instead: the k-th row
    # of every domain before the (k+1)-th of any, so any prefix covers as many domains as possible.
    if a.row_sampling == "stratified":
        by_dom = {}
        for r in rows:
            by_dom.setdefault(r.get("domain"), []).append(r)
        ordered = []
        for k in range(max(len(v) for v in by_dom.values())):
            for dom in sorted(by_dom):
                if k < len(by_dom[dom]):
                    ordered.append(by_dom[dom][k])
        rows = ordered[:a.gate_rows]
    else:
        rows = rows[:a.gate_rows]
    n_dom_gate = len({r.get("domain") for r in rows})
    print("[gate] domain coverage: %d domains over %d rows (sampling=%s)"
          % (n_dom_gate, len(rows), a.row_sampling), flush=True)
    print("[gate] SIZE rows = %d | cells = %d | band = %s | split = %s"
          % (len(rows), len(cells), a.band, a.split), flush=True)
    if not rows:
        sys.exit("VACUOUS: zero eligible rows")

    lm = dc.load_model(a.model or dc.PRIMARY_MODEL, dtype=torch.bfloat16,
                       attn_implementation="eager")
    attn_loaded = sb.loaded_attn_implementation(lm.model)
    sb.assert_eager_for_knockout(attn_loaded, "eager")
    if scr.get("model_id") and scr["model_id"] != lm.model_id:
        sys.exit("REFUSING: screen was produced on model %r, this gate loaded %r"
                 % (scr["model_id"], lm.model_id))
    n_heads, head_dim = pc._attn_head_dims(lm.model)
    c_l, w_l, id_meta = sg.readout_id_pair(lm.tokenizer, a.concept, a.codeword)
    dev = lm.model.device
    c_ids = torch.tensor(sorted(set(c_l)), dtype=torch.long, device=dev)
    w_ids = torch.tensor(sorted(set(w_l)), dtype=torch.long, device=dev)

    est, true, recs, skipped = [], [], [], []
    for i, row in enumerate(rows):
        templated = dc.apply_template(lm.tokenizer, row["full_prompt"],
                                      enable_thinking=sb.ENABLE_THINKING)
        try:
            dk, dk_why = sb.demo_key_positions(lm.tokenizer, row, templated)
            qs = sb.query_span_positions(lm.tokenizer, row, templated, dk)
            surf, surf_why = sb.target_surface_positions(lm.tokenizer, row, templated, qs)
        except Exception as e:
            skipped.append({"prompt_id": row.get("prompt_id"), "why": repr(e)}); continue
        if dk_why or not dk or surf_why or not surf or not qs:
            skipped.append({"prompt_id": row.get("prompt_id"),
                            "why": dk_why or surf_why or "empty span"}); continue
        p_star = int(max(surf))
        base_ids = lm.tokenizer(templated, add_special_tokens=False)["input_ids"]
        full_ids = lm.tokenizer(templated + a.answer_prefix, add_special_tokens=False)["input_ids"]
        if full_ids[:len(base_ids)] != base_ids or p_star >= len(base_ids):
            skipped.append({"prompt_id": row.get("prompt_id"), "why": "prefix/span"}); continue
        ids_t = torch.tensor([full_ids], device=dev)
        with torch.no_grad():
            embeds = lm.model.get_input_embeddings()(ids_t)
        embeds = embeds.detach().clone().requires_grad_(True)

        # clean: M_clean, g, z_clean
        lm.model.zero_grad(set_to_none=True)
        with w1.frozen_params(lm.model), pc.ZHeadCapture(lm.model, band) as cap:
            with torch.enable_grad():
                M = w1.metric_M(lm, embeds, c_ids, w_ids)
                M.backward()
            m_clean = float(M.detach())
            g, z_clean = {}, {}
            for L in band:
                z = cap.acts[L]
                if z.grad is None:
                    raise RuntimeError("no z-grad at layer %d" % L)
                g[L] = z.grad[0].detach().float().view(-1, n_heads, head_dim)[p_star]
                z_clean[L] = z[0].detach().float().view(-1, n_heads, head_dim)[p_star]

        # knockout: z_ko
        with pc.ScopedAttentionKnockout(lm.model, sorted(set(band)), blocked_keys=dk,
                                        mode="target_surface_row_only", query_span=qs,
                                        demo_span=dk, surface_span=surf):
            with pc.ZHeadCapture(lm.model, band) as cap2, torch.no_grad():
                lm.model(inputs_embeds=embeds, use_cache=False)
                z_ko = {L: cap2.acts[L][0].detach().float().view(-1, n_heads, head_dim)[p_star]
                        for L in band}

        # THE INTERVENTION: one head, one position, the knockout z patched into a CLEAN forward.
        for (L, h) in cells:
            atp = float((g[L][h] * (z_ko[L][h] - z_clean[L][h])).sum())
            with torch.no_grad():
                with pc.ZHeadPatch(lm.model, L, h, [p_star], z_ko[L][h]):
                    m_patched = float(w1.metric_M(lm, embeds, c_ids, w_ids).detach())
            td = m_patched - m_clean
            est.append(atp); true.append(td)
            recs.append({"row": i, "layer": L, "head": h,
                         "atp": round(atp, 8), "true_delta": round(td, 8)})
        if (i + 1) % 10 == 0:
            print("[gate] %d rows" % (i + 1), flush=True)

    print("[gate] SIZE pairs = %d (rows_used x cells)" % len(est), flush=True)
    if len(est) < 2:
        sys.exit("VACUOUS: fewer than 2 (estimate, truth) pairs -- no correlation is defined")

    pear = atp48.pearson(est, true)
    spear = atp48.spearman(est, true)
    trustworthy = bool(pear is not None and spear is not None
                       and pear >= a.min_corr and spear >= a.min_corr)
    out = {
        "schema": "dcs_csi_head_patch_gate/1",
        "screen": a.screen, "split": a.split, "band": a.band, "bank_block": a.bank_block,
        "codeword": a.codeword, "concept": a.concept,
        "n_rows_requested": a.gate_rows, "n_rows_used": len(rows) - len(skipped),
        "n_cells": len(cells), "n_pairs": len(est), "skipped": skipped[:20],
        "row_sampling": a.row_sampling, "n_domains_in_gate": n_dom_gate,
        "model_id": lm.model_id, "revision": lm.revision, "dtype": lm.dtype,
        "attn_implementation_loaded": attn_loaded,
        "pearson": pear, "spearman": spear, "min_corr": a.min_corr,
        "TRUSTWORTHY": trustworthy,
        "VERDICT": ("the screen's ranking MAY be used by the causal stage" if trustworthy else
                    "UNTRUSTWORTHY -- the causal stage is NOT launched on this ranking; design 3.4's "
                    "fallback is selection by true single-head patch effect on a 40-row subsample"),
        # EVERY pair, not a prefix. The truncated form stored the first 400 -- which is the
        # first 10 ROWS, not a sample of 400 -- so any post-hoc robustness check (drop the
        # dominant head, drop the largest cell) silently ran on a quarter of the rows while
        # the headline ran on all of them. ~1600 records is under 120 KB.
        "pairs": recs,
        "NOTE": ("every atp here is the ROW'S OWN first-order estimate, not the screen's summed "
                 "S[h]; the screen chose the cells and nothing else"),
    }
    n = w1.atomic_write_json(a.out, out)
    print("[gate] wrote+verified %s (%d bytes)" % (a.out, n))
    print("[gate] pearson = %s | spearman = %s | min_corr = %s | TRUSTWORTHY = %s"
          % (pear, spear, a.min_corr, trustworthy))


if __name__ == "__main__":
    main()
