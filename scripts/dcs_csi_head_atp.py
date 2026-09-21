"""W1 -- AtP on the per-head z channel, with THE A1 KNOCKOUT as the corruption.

Plan section 8.2 / design section 3.2-3.3. Screens which ATTENTION HEAD INDICES carry the installed
meaning from the demonstrations into the query, so section 4's causal arms have a candidate set.

    AtP[L, h, p*] = < g_z[L, h, p*] ,  z_ko[L, h, p*] - z_clean[L, h, p*] >
    S[h]          = sum over L in the band of AtP[L, h, p*]        <- SIGNED, section 3.3

WHY SIGNED: a head whose z-change under the knockout RAISES M is not a writer of the installed
meaning, and folding it in by |.| would let a protective head be promoted. Magnitude is kept as a
diagnostic and as the ranking for the true-patch gate (where magnitude is what is being validated),
never as the selection statistic.

WHY HEAD INDEX AND NOT (L, h) -- design section 0: `--knockout-heads` takes a FLAT list of head
indices applied to every layer of the band (score_behavior.py:2540-2542, pair_common.py:958). An
attribution that ranked (L, h) cells would propose a candidate the instrument CANNOT EXPRESS.

THIS FILE IMPORTS score_behavior AND REUSES ITS SPAN RESOLUTION (S-178). It does not re-derive
spans. Re-deriving them is the prompt/mask-mismatch hazard score_behavior.py:2903ff refuses by name:
two resolvers in two files can disagree, and only one of them is the one the arms ran under.
IMPORTING IS NOT EDITING -- PR-CSI-003's VOID condition prohibits MODIFYING score_behavior.py.

Scalars only. No prompt text and no generations are persisted.
"""
import argparse, json, os, sys, tempfile, importlib.util
from contextlib import contextmanager

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
os.chdir(REPO)
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))
sys.path.insert(0, os.path.join(REPO, "doublespeak_causality"))

import torch
import ds_common as dc
import pair_common as pc
import signals as sg

_spec = importlib.util.spec_from_file_location(
    "sb", os.path.join(REPO, "src", "boombness", "score_behavior.py"))
sb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sb)


def atomic_write_json(path, obj):
    """Temp + fsync + size check + re-parse OF THE TEMP FILE + chmod + os.replace (S-130 shape)."""
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_atomic_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=False); fh.write("\n")
            fh.flush(); os.fsync(fh.fileno())
        if os.path.getsize(tmp) == 0:
            raise OSError("temp file is 0 bytes after a flush+fsync that reported success")
        with open(tmp, "r", encoding="utf-8") as fh:
            json.load(fh)
        try:
            mode = os.stat(path).st_mode & 0o7777
        except OSError:
            mode = 0o644
        os.chmod(tmp, mode); os.replace(tmp, path)
        # os.replace makes the CONTENT visible; the DIRECTORY ENTRY is not durable until the
        # directory itself is synced. Best-effort: some filesystems refuse an O_RDONLY dir
        # fsync, and failing to sync is not a reason to discard a file already in place.
        try:
            dfd = os.open(d, os.O_RDONLY)
            try: os.fsync(dfd)
            finally: os.close(dfd)
        except OSError:
            pass
    except Exception as e:
        try: nb = os.path.getsize(tmp)
        except OSError: nb = -1
        try: os.unlink(tmp)
        except OSError: pass
        raise OSError("atomic_write_json FAILED for %s -- %d bytes reached the temp file; the "
                      "destination is UNCHANGED. Cause: %r" % (path, nb, e)) from e
    return os.path.getsize(path)


@contextmanager
def frozen_params(model):
    """requires_grad=False on every parameter, flags restored on exit.

    MIRRORED VERBATIM from doublespeak_causality/scripts/phase6_jacobian_readout.py:365, which
    documents exactly why: "with the graph rooted at `inputs_embeds` instead of the weights,
    backward populates ONLY the retained activation grads -- no [n_params] gradient buffer is
    ever allocated (a ~16GB saving on an 8B bf16 model)". Without this, `M.backward()` allocates
    a .grad for all 8B parameters ON TOP of the 16 GB of weights and OOMs a 24 GB 3090 -- and an
    OOM here is the GOOD case; the bad one is a smaller model where it silently fits and every
    arm pays 2x the memory for a buffer nothing reads.

    COPIED RATHER THAN IMPORTED, deliberately: phase6 executes `atp = _load_atp()` at module
    scope (line 154), which importlib-loads 48_attribution_patching.py. Importing a second
    script's side effects to borrow eight lines is the worse dependency.
    """
    saved = [(q, q.requires_grad) for q in model.parameters()]
    try:
        for q, _ in saved:
            q.requires_grad_(False)
        yield
    finally:
        for q, flag in saved:
            q.requires_grad_(flag)


def metric_M(lm, embeds, c_ids, w_ids):
    """M = logp_concept - logp_codeword at the next-token position, DIFFERENTIABLE.

    Mirrors score_behavior.next_token_readout:115-123 exactly -- log_softmax over the final
    position, logsumexp within each id group -- with two deliberate differences: the tensor stays
    on device and is NOT detached (AtP needs d M / d z), and logits_to_keep is not used because the
    graph must reach the captured z at every position, not only the last.
    """
    out = lm.model(inputs_embeds=embeds, use_cache=False)
    lp = torch.log_softmax(out.logits[0, -1, :].float(), dim=-1)
    return (lp[c_ids].logsumexp(0) - lp[w_ids].logsumexp(0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", default="data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl")
    ap.add_argument("--codeword", required=True)
    ap.add_argument("--concept", required=True)
    ap.add_argument("--allow-heldout", action="store_true",
                    help="required to touch VALIDATION; absent, --split validation refuses")
    ap.add_argument("--split", default="train", help="DOMAIN-level split: train/validation")
    ap.add_argument("--axis", default="configs/dcs_csi_axis_basket_behavioral.pt",
                    help="the committed axis whose fit_population defines the domain set")
    ap.add_argument("--bank-block", default="cds_n4_sow")
    ap.add_argument("--band", default="6-14", help="the A1 band; the knockout and the AtP sum share it")
    ap.add_argument("--answer-prefix", default=" Answer:")
    ap.add_argument("--limit", type=int, default=0, help="0 = every eligible row")
    ap.add_argument("--topk", type=int, default=40,
                    help="size of the convenience top-cell list; ALL cells are emitted regardless")
    ap.add_argument("--model", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    lo, hi = (int(x) for x in a.band.split("-"))
    band = list(range(lo, hi + 1))

    # ROW SELECTION. The bank's own `split` field is dev/heldout -- it is NOT the TRAIN/VALIDATION
    # split, which is a DOMAIN-level assignment held in an external manifest and applied by domain.
    # Caught by the 2-row smoke (job 915771), which selected ZERO rows and was refused by the
    # non-vacuity guard rather than producing a screen over nothing.
    # THE DOMAIN SET COMES FROM THE AXIS ARTIFACT, NOT FROM THE SPLIT MANIFEST.
    # Measured 2026-09-21 (S-179): the manifest labels restaurant_kitchen, school_campus and
    # subway_station as "train", but the committed axis's fit_population.domains has 67 domains and
    # excludes all three -- and the design states those three are "touched by nothing here".
    # Filtering on the manifest would put THREE RESERVED DOMAINS into the screen. The axis's own
    # fit_population is what every committed arm actually ran on, so it is the authority.
    import torch as _t
    _ax = _t.load(a.axis, map_location="cpu", weights_only=False)["meta"]
    if a.split == "train":
        keep_domains = set(_ax["fit_population"]["domains"])
    elif a.split == "validation":
        # HELD-OUT DATA IS SPENT ONCE. A typo should not be able to spend it, so the
        # flag is required and its absence is a refusal, not a warning (R14 finding 5).
        if not a.allow_heldout:
            sys.exit("REFUSING: --split validation touches HELD-OUT domains. Pass "
                     "--allow-heldout to say so deliberately.")
        keep_domains = set(_ax["held_out_validation_domains"])
    else:
        sys.exit("--split must be train or validation; TEST is touched by nothing here")
    assign = {d: a.split for d in keep_domains}
    rows = [json.loads(l) for l in open(a.bank)]
    rows = [r for r in rows
            if r.get("query_kind") == "semantic_one_word" and r.get("cell") == "C"
            and r.get("condition") == "natural_doublespeak" and r.get("n_examples") == 4
            and r.get("bank_block") == a.bank_block
            and assign.get(r.get("domain")) == a.split]
    doms = sorted({r.get("domain") for r in rows})
    if a.limit:
        rows = rows[:a.limit]
    # NON-VACUITY FIRST (S-134): a screen over zero rows is not a screen.
    print("[atp] SIZE rows = %d over %d domains | band = %s (%d layers) | split = %s | block = %s"
          % (len(rows), len(doms), a.band, len(band), a.split, a.bank_block))
    if not rows:
        sys.exit("VACUOUS: zero eligible rows -- refusing to emit a screen")

    # SIGNATURE READ FROM SOURCE, NOT ASSUMED (ds_common.load_model:384): the kwarg is
    # `attn_implementation`, not `attn_impl`, and `dtype` is a torch.dtype, not a string.
    lm = dc.load_model(a.model or dc.PRIMARY_MODEL,
                       dtype=torch.bfloat16, attn_implementation="eager")
    # THE REQUEST AND THE LOADED STATE ARE TWO DIFFERENT FACTS (score_behavior:3025-3042).
    # An attention-mask knockout under SDPA is a SILENT NO-OP that would score as a clean null:
    # every AtP number below would be a difference between two identical forwards. Refuse.
    attn_loaded = sb.loaded_attn_implementation(lm.model)
    sb.assert_eager_for_knockout(attn_loaded, "eager")
    print("[atp] attn_implementation loaded = %r (asserted eager)" % attn_loaded)
    n_heads, head_dim = pc._attn_head_dims(lm.model)
    print("[atp] n_heads = %d  head_dim = %d" % (n_heads, head_dim))

    # THE TOP LAYER HAS EXACTLY ZERO ATTRIBUTION AT A NON-FINAL SITE, AND IT IS STRUCTURAL.
    # d M / d z[L_top, p] == 0 for p != last, because the readout is at the LAST position and
    # no attention layer follows L_top to carry position p there. Measured on a tiny Llama
    # (scratchpad/w1_zerograd_probe.py): 2 layers band [0,1] p*=last -> {0:1.360, 1:1.626};
    # p*=4 -> {0:0.252, 1:0.0}; 4 layers band [0,1] p*=4 -> {0:0.265, 1:0.205}; band [2,3]
    # p*=4 -> {2:0.130, 3:0.0}. A band touching the top layer would therefore contribute a
    # guaranteed-zero column that is INDISTINGUISHABLE FROM "this head does nothing".
    if max(band) >= lm.num_layers - 1:
        sys.exit("REFUSING: band top layer %d is the model top layer %d; its AtP at p* != last "
                 "is identically zero by construction and would read as a null result"
                 % (max(band), lm.num_layers - 1))

    c_ids_l, w_ids_l, id_meta = sg.readout_id_pair(lm.tokenizer, a.concept, a.codeword)
    dev = lm.model.device
    c_ids = torch.tensor(sorted(set(c_ids_l)), dtype=torch.long, device=dev)
    w_ids = torch.tensor(sorted(set(w_ids_l)), dtype=torch.long, device=dev)

    S = torch.zeros(n_heads, dtype=torch.float64)          # signed, the selection statistic
    A = torch.zeros(n_heads, dtype=torch.float64)          # |.| diagnostic, never the selector
    per_cell = {}                                          # (L, h) -> summed AtP, for the gate
    # W1.1 -- THE UNIT OF ANALYSIS IS THE DOMAIN, SO THE SCREEN MUST EMIT PER-DOMAIN TOTALS.
    # Without these, S[h] is a point ranking with no interval: nothing distinguishes "h19 leads in
    # 60 domains" from "h19 leads in 12 with three outliers carrying it". A domain-clustered
    # bootstrap needs the per-domain terms, and they cannot be recovered from the sum afterwards.
    S_by_dom = {}                                          # domain -> [n_heads] signed totals
    rows_by_dom = {}                                       # domain -> rows actually used
    g_norm_total = 0.0        # LIVENESS: a dead hook and a null result look identical
    ko_delta_total = 0.0      # LIVENESS: a no-op knockout and a null result look identical
    n_used, skipped = 0, []

    for i, row in enumerate(rows):
        templated = dc.apply_template(lm.tokenizer, row["full_prompt"], enable_thinking=sb.ENABLE_THINKING)
        # THE THREE SPAN FUNCTIONS HAVE THREE DIFFERENT RETURN SHAPES, READ FROM SOURCE.
        #   demo_key_positions      -> (positions, reason)   tuple   (score_behavior:176)
        #   query_span_positions    -> set                   BARE    (score_behavior:1289)
        #   target_surface_positions-> (positions, reason)   tuple   (score_behavior:1317)
        # S-178's integration map verified every ARGUMENT list and no RETURN shape, so `surf[-1]`
        # read the REASON slot and `p_star` became None. The reason strings are the functions' own
        # designed failure channel ("empty_target_surface", "no_target_surface_occurrence_inside_
        # query_span", ...), so they are recorded as the skip cause rather than flattened into a
        # generic exception -- a blanket try/except would have turned each into "span resolution".
        try:
            dk, dk_why = sb.demo_key_positions(lm.tokenizer, row, templated)
            qs = sb.query_span_positions(lm.tokenizer, row, templated, dk)
            surf, surf_why = sb.target_surface_positions(lm.tokenizer, row, templated, qs)
        except Exception as e:
            skipped.append({"prompt_id": row.get("prompt_id"), "why": "span resolution raised: %r" % (e,)})
            continue
        if dk_why or not dk:
            skipped.append({"prompt_id": row.get("prompt_id"), "why": "demo span: %s" % (dk_why or "empty")})
            continue
        if not qs:
            skipped.append({"prompt_id": row.get("prompt_id"), "why": "empty query span"})
            continue
        if surf_why or not surf:
            skipped.append({"prompt_id": row.get("prompt_id"),
                            "why": "target_surface span: %s" % (surf_why or "empty")})
            continue
        p_star = int(max(surf))

        # THE ANSWER PREFIX IS APPENDED, SO EARLIER INDICES DO NOT MOVE -- asserted, not assumed.
        base_ids = lm.tokenizer(templated, add_special_tokens=False)["input_ids"]
        full_ids = lm.tokenizer(templated + a.answer_prefix, add_special_tokens=False)["input_ids"]
        if full_ids[:len(base_ids)] != base_ids:
            skipped.append({"prompt_id": row.get("prompt_id"),
                            "why": "answer_prefix is not a pure append: span indices would shift"})
            continue
        if p_star >= len(base_ids):
            skipped.append({"prompt_id": row.get("prompt_id"), "why": "p* outside the templated prompt"})
            continue
        ids_t = torch.tensor([full_ids], device=dev)

        # THE GRAPH IS ROOTED AT THE EMBEDDINGS, NOT THE WEIGHTS (phase6_jacobian_readout:387-396).
        # Integer input_ids cannot carry a graph, so with frozen params NOTHING downstream would
        # require grad and every retain_grad() would be a silent no-op -- z.grad None at every
        # layer. Detaching and re-marking the embedding output starts the graph one step below the
        # band and keeps the parameters grad-free.
        with torch.no_grad():
            embeds = lm.model.get_input_embeddings()(ids_t)
        embeds = embeds.detach().clone().requires_grad_(True)

        # ---- clean forward + backward: g_z and z_clean --------------------------------------
        lm.model.zero_grad(set_to_none=True)
        with frozen_params(lm.model), pc.ZHeadCapture(lm.model, band) as cap:
            with torch.enable_grad():
                M = metric_M(lm, embeds, c_ids, w_ids)
                M.backward()
            g, z_clean = {}, {}
            for L in band:
                z = cap.acts[L]
                if z.grad is None:
                    raise RuntimeError("no z-grad at layer %d -- ZHeadCapture did not retain it" % L)
                g[L] = z.grad[0].detach().float().view(-1, n_heads, head_dim)[p_star].cpu()
                z_clean[L] = z[0].detach().float().view(-1, n_heads, head_dim)[p_star].cpu()

        # ---- knockout forward, batch-1, no grad: z_ko ----------------------------------------
        with pc.ScopedAttentionKnockout(lm.model, sorted(set(band)), blocked_keys=dk,
                                        mode="target_surface_row_only",
                                        query_span=qs, demo_span=dk, surface_span=surf):
            with pc.ZHeadCapture(lm.model, band) as cap2, torch.no_grad():
                lm.model(inputs_embeds=embeds, use_cache=False)
                z_ko = {L: cap2.acts[L][0].detach().float().view(-1, n_heads, head_dim)[p_star].cpu()
                        for L in band}

        for L in band:
            g_norm_total += float(g[L].norm())
            ko_delta_total += float((z_ko[L] - z_clean[L]).abs().sum())
            contrib = (g[L] * (z_ko[L] - z_clean[L])).sum(dim=-1).double()   # [n_heads]
            S += contrib
            A += contrib.abs()
            _d = row.get("domain")
            if _d not in S_by_dom:
                S_by_dom[_d] = torch.zeros(n_heads, dtype=torch.float64)
                rows_by_dom[_d] = 0
            S_by_dom[_d] += contrib
            for h in range(n_heads):
                per_cell[(L, h)] = per_cell.get((L, h), 0.0) + float(contrib[h])
        n_used += 1
        rows_by_dom[row.get("domain")] = rows_by_dom.get(row.get("domain"), 0) + 1
        if n_used % 25 == 0:
            print("[atp] %d rows" % n_used, flush=True)

    print("[atp] rows used = %d | skipped = %d" % (n_used, len(skipped)))
    if n_used == 0:
        sys.exit("VACUOUS: every row was skipped -- refusing to emit a screen")

    # LIVENESS, BOTH HALVES (pair_common:1205 "A DEAD HOOK SCORES AS A CLEAN NULL").
    # AtP = <g_z, z_ko - z_clean> is zero if EITHER factor is dead, and a zeroed S[h] column is
    # exactly what "no head matters" looks like. Neither is inferred from the other: g comes from
    # the backward, the delta from the knockout, and each is refused on its own.
    print("[atp] LIVENESS g_norm_total = %.6f | ko_delta_total = %.6f" % (g_norm_total, ko_delta_total))
    if g_norm_total == 0.0:
        sys.exit("REFUSING: every captured z-gradient is exactly zero -- the backward is dead, "
                 "not the heads; this would emit an all-zero screen indistinguishable from a null")
    if ko_delta_total == 0.0:
        sys.exit("REFUSING: z_ko == z_clean at every band layer -- the knockout changed NOTHING. "
                 "An attention edit that never fires scores as a clean null (see PR-057/C-13)")

    order = sorted(range(n_heads), key=lambda h: float(S[h]))          # most negative first
    out = {
        "schema": "dcs_csi_head_atp/1",
        "bank": a.bank, "codeword": a.codeword, "concept": a.concept, "split": a.split,
        "band": a.band, "band_layers": band, "bank_block": a.bank_block,
        "n_domains": len(doms), "domain_source": a.axis, "n_heads": n_heads, "head_dim": head_dim,
        "n_rows_used": n_used, "n_rows_skipped": len(skipped), "skipped": skipped[:20],
        "readout_id_meta": id_meta,
        # PROVENANCE THE VERIFIER READS, AND IT RECORDS THE LOADED STATE, NOT THE REQUEST.
        "model_id": lm.model_id, "revision": lm.revision, "dtype": lm.dtype,
        "attn_implementation_loaded": attn_loaded,
        "grad_root": "inputs_embeds (params frozen; no [n_params] grad buffer)",
        "liveness": {"g_norm_total": round(g_norm_total, 8),
                     "ko_delta_total": round(ko_delta_total, 8),
                     "note": "both are > 0 or the run refuses; AtP is zero if either factor is dead"},
        "site": "p* = last target_surface position inside the query span",
        "S_signed_by_head": {str(h): round(float(S[h]), 8) for h in range(n_heads)},
        "abs_diagnostic_by_head": {str(h): round(float(A[h]), 8) for h in range(n_heads)},
        "ranking_most_negative_first": order,
        # THE GATE'S INPUT (design 3.4): per-CELL AtP, not per-head. 9 layers x 32 heads = 288.
        # Emitted in FULL -- a top-k written alone cannot be re-ranked by any other rule later,
        # and the screen must not quietly decide what a downstream gate is allowed to see.
        # W1.1: the per-domain terms a domain-clustered bootstrap needs. 67 x 32 numbers.
        "S_by_domain_head": {d: [round(float(v[h]), 8) for h in range(n_heads)]
                             for d, v in sorted(S_by_dom.items())},
        "rows_per_domain_used": {d: rows_by_dom[d] for d in sorted(rows_by_dom)},
        "AtP_by_cell": {("%d,%d" % lh): round(v, 8) for lh, v in sorted(per_cell.items())},
        "topk_cells_by_abs": [{"layer": L, "head": h, "atp": round(per_cell[(L, h)], 8)}
                              for (L, h) in sorted(per_cell, key=lambda c: -abs(per_cell[c]))[:a.topk]],
        "topk": a.topk,
        "SELECTION_RULE": ("S[h] SIGNED, summed over the band at p*. The |.| column is a DIAGNOSTIC "
                           "and the ranking for the true-patch gate only -- never the selector "
                           "(design section 3.3)."),
        "NOT_YET_RUN": ("the true-patch validation gate (design section 3.4). Attribution PROPOSES; "
                        "intervention DECIDES. No candidate head set may be frozen from this file "
                        "alone."),
    }
    n = atomic_write_json(a.out, out)
    print("[atp] wrote+verified %s (%d bytes)" % (a.out, n))
    print("[atp] most negative S[h]: %s" % [(h, round(float(S[h]), 5)) for h in order[:8]])


if __name__ == "__main__":
    main()
