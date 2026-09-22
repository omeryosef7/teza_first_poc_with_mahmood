"""§A5-8 — bound the FALSE NEGATIVES the AtP screen may have missed.

WHY. AtP∗ (arXiv:2403.00745, LIT §C1) recommends two things: verify the top-K by true patching, AND use
the REMAINING unverified nodes for subset sampling to bound missed false negatives. §3.4's gate did the
first (top-40 cells, Pearson 0.7817 / Spearman 0.7852). The second was never done: **248 of 288 cells
were never patched and this sprint has no bound on what they contain.** AtP∗ also documents that
attention nodes suffer SEVERE false negatives from softmax saturation, so the gap is not hypothetical.

WHAT IT MEASURES. A seeded uniform sample of the unverified cells is patched for real -- `z_ko` for that
one head at `p*` into an otherwise clean forward -- giving the TRUE `ΔM` for cells the screen ranked
low. Two comparisons follow:

  * the largest |true ΔM| among sampled UNVERIFIED cells, against the smallest |true ΔM| among the
    VERIFIED top-40. If the unverified maximum sits below the verified minimum, no sampled cell would
    have displaced a selected one.
  * Welch's t-test on |true ΔM| between the two groups (unequal variances, as AtP∗ uses), plus a
    one-sided upper confidence bound on the unverified mean.

⛔ WHAT IT CANNOT DO. A sample bounds the sample. It cannot prove no unsampled cell is large, and the
bound is on the sampled distribution, not on the worst case over 248. It also inherits the screen's
own site choice: only `p*` and only the band are ever patched, so a head that matters at another
position or layer is invisible to this and to the screen alike.
"""
import argparse, importlib.util, json, math, os, random, statistics, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "doublespeak_causality"))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))

import torch                                   # noqa: E402
import ds_common as dc                         # noqa: E402
import pair_common as pc                       # noqa: E402
import signals as sg                           # noqa: E402


def _load(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return m


sb = _load("sb", os.path.join(REPO, "src", "boombness", "score_behavior.py"))
w1 = _load("w1", os.path.join(REPO, "scripts", "dcs_csi_head_atp.py"))


def welch(a, b):
    """Welch's t and a conservative dof; returns (t, dof) or (None, None)."""
    if len(a) < 2 or len(b) < 2:
        return None, None
    ma, mb = statistics.fmean(a), statistics.fmean(b)
    va, vb = statistics.variance(a), statistics.variance(b)
    na, nb = len(a), len(b)
    se = math.sqrt(va / na + vb / nb)
    if se == 0:
        return None, None
    t = (ma - mb) / se
    num = (va / na + vb / nb) ** 2
    den = (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
    return t, (num / den if den else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen", required=True)
    ap.add_argument("--gate", required=True, help="the W2 artifact whose cells were VERIFIED")
    ap.add_argument("--bank", default="data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl")
    ap.add_argument("--axis", default="configs/dcs_csi_axis_basket_behavioral.pt")
    ap.add_argument("--codeword", required=True)
    ap.add_argument("--concept", required=True)
    ap.add_argument("--split", default="train")
    ap.add_argument("--bank-block", default="cds_n4_sow")
    ap.add_argument("--band", default="6-14")
    ap.add_argument("--answer-prefix", default=" Answer:")
    ap.add_argument("--n-cells", type=int, default=48, help="unverified cells to sample")
    ap.add_argument("--rows", type=int, default=40, help="rows per cell, stratified over domains")
    ap.add_argument("--seed", type=int, default=20260922)
    ap.add_argument("--model", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    scr = json.load(open(a.screen)); gate = json.load(open(a.gate))
    for f in ("split", "band", "bank_block", "codeword", "concept"):
        if scr.get(f) != getattr(a, f.replace("-", "_")):
            sys.exit("REFUSING: screen %s=%r but invoked with %r" % (f, scr.get(f), getattr(a, f.replace("-", "_"))))
    all_cells = [tuple(int(x) for x in k.split(",")) for k in scr["AtP_by_cell"]]
    verified = {(int(c["layer"]), int(c["head"])) for c in scr["topk_cells_by_abs"][:gate["n_cells"]]}
    unverified = sorted(set(all_cells) - verified)
    print("[fn] SIZE cells total = %d | VERIFIED by the gate = %d | UNVERIFIED = %d"
          % (len(all_cells), len(verified), len(unverified)))
    if len(unverified) < a.n_cells:
        sys.exit("REFUSING: only %d unverified cells, asked for %d" % (len(unverified), a.n_cells))
    sample = sorted(random.Random(a.seed).sample(unverified, a.n_cells))
    print("[fn] sampling %d of them, seed %d" % (len(sample), a.seed))

    lo, hi = (int(x) for x in a.band.split("-"))
    band = list(range(lo, hi + 1))
    ax = torch.load(a.axis, map_location="cpu", weights_only=False)["meta"]
    keep = set(ax["fit_population"]["domains"] if a.split == "train" else ax["held_out_validation_domains"])
    rows = [json.loads(l) for l in open(a.bank)]
    rows = [r for r in rows
            if r.get("query_kind") == "semantic_one_word" and r.get("cell") == "C"
            and r.get("condition") == "natural_doublespeak" and r.get("n_examples") == 4
            and r.get("bank_block") == a.bank_block and r.get("domain") in keep]
    by_dom = {}
    for r in rows:
        by_dom.setdefault(r.get("domain"), []).append(r)
    ordered = []
    for k in range(max(len(v) for v in by_dom.values())):
        for d in sorted(by_dom):
            if k < len(by_dom[d]):
                ordered.append(by_dom[d][k])
    rows = ordered[:a.rows]
    print("[fn] SIZE rows = %d over %d domains (stratified, matching the gate)"
          % (len(rows), len({r["domain"] for r in rows})), flush=True)

    lm = dc.load_model(a.model or dc.PRIMARY_MODEL, dtype=torch.bfloat16, attn_implementation="eager")
    attn = sb.loaded_attn_implementation(lm.model); sb.assert_eager_for_knockout(attn, "eager")
    n_heads, head_dim = pc._attn_head_dims(lm.model)
    c_l, w_l, _ = sg.readout_id_pair(lm.tokenizer, a.concept, a.codeword)
    dev = lm.model.device
    c_ids = torch.tensor(sorted(set(c_l)), dtype=torch.long, device=dev)
    w_ids = torch.tensor(sorted(set(w_l)), dtype=torch.long, device=dev)

    true_by_cell = {c: [] for c in sample}
    used = 0
    for i, row in enumerate(rows):
        templated = dc.apply_template(lm.tokenizer, row["full_prompt"], enable_thinking=sb.ENABLE_THINKING)
        try:
            dk, dkw = sb.demo_key_positions(lm.tokenizer, row, templated)
            qs = sb.query_span_positions(lm.tokenizer, row, templated, dk)
            surf, sw = sb.target_surface_positions(lm.tokenizer, row, templated, qs)
        except Exception:
            continue
        if dkw or sw or not dk or not surf or not qs:
            continue
        p_star = int(max(surf))
        base_ids = lm.tokenizer(templated, add_special_tokens=False)["input_ids"]
        full_ids = lm.tokenizer(templated + a.answer_prefix, add_special_tokens=False)["input_ids"]
        if full_ids[:len(base_ids)] != base_ids or p_star >= len(base_ids):
            continue
        ids_t = torch.tensor([full_ids], device=dev)
        with torch.no_grad():
            embeds = lm.model.get_input_embeddings()(ids_t)
        embeds = embeds.detach().clone()
        with torch.no_grad():
            m_clean = float(w1.metric_M(lm, embeds, c_ids, w_ids))
        with pc.ScopedAttentionKnockout(lm.model, sorted(set(band)), blocked_keys=dk,
                                        mode="target_surface_row_only", query_span=qs,
                                        demo_span=dk, surface_span=surf):
            with pc.ZHeadCapture(lm.model, band) as cap, torch.no_grad():
                lm.model(inputs_embeds=embeds, use_cache=False)
                z_ko = {L: cap.acts[L][0].detach().float().view(-1, n_heads, head_dim)[p_star]
                        for L in band}
        for (L, h) in sample:
            with torch.no_grad():
                with pc.ZHeadPatch(lm.model, L, h, [p_star], z_ko[L][h]):
                    mp = float(w1.metric_M(lm, embeds, c_ids, w_ids))
            true_by_cell[(L, h)].append(mp - m_clean)
        used += 1
        if used % 10 == 0:
            print("[fn] %d rows" % used, flush=True)

    print("[fn] SIZE rows used = %d | pairs = %d" % (used, used * len(sample)), flush=True)
    if used < 2:
        sys.exit("VACUOUS: fewer than 2 usable rows")

    unv = {("%d,%d" % c): statistics.fmean(v) for c, v in true_by_cell.items() if v}
    unv_abs = sorted(abs(v) for v in unv.values())
    ver_abs = sorted(abs(float(c["true_delta"])) for c in gate["pairs"]) if gate.get("pairs") else []
    # the gate stores per-(row, cell) pairs; collapse to per-cell means for a like-for-like comparison
    per_cell_ver = {}
    for p in gate.get("pairs", []):
        per_cell_ver.setdefault((p["layer"], p["head"]), []).append(float(p["true_delta"]))
    ver_cell_abs = sorted(abs(statistics.fmean(v)) for v in per_cell_ver.values())

    t, dof = welch(unv_abs, ver_cell_abs)
    n = len(unv_abs)
    mean_u = statistics.fmean(unv_abs)
    sd_u = statistics.stdev(unv_abs) if n > 1 else 0.0
    ub95 = mean_u + 1.645 * sd_u / math.sqrt(n)          # one-sided normal upper bound on the mean

    out = {
        "schema": "dcs_csi_head_fn_bound/1",
        "screen": a.screen, "gate": a.gate, "split": a.split, "band": a.band,
        "n_cells_total": len(all_cells), "n_verified_by_gate": len(verified),
        "n_unverified": len(unverified), "n_sampled": len(sample), "seed": a.seed,
        "rows_used": used, "n_domains": len({r["domain"] for r in rows}),
        "sampled_cells": ["%d,%d" % c for c in sample],
        "unverified_abs_true_delta": {"n": n, "mean": mean_u, "sd": sd_u,
                                      "median": statistics.median(unv_abs),
                                      "max": unv_abs[-1], "min": unv_abs[0],
                                      "upper_95_one_sided_on_mean": ub95},
        "verified_abs_true_delta": {"n": len(ver_cell_abs),
                                    "mean": statistics.fmean(ver_cell_abs) if ver_cell_abs else None,
                                    "median": statistics.median(ver_cell_abs) if ver_cell_abs else None,
                                    "min": ver_cell_abs[0] if ver_cell_abs else None,
                                    "max": ver_cell_abs[-1] if ver_cell_abs else None},
        "welch_t": t, "welch_dof": dof,
        "max_unverified_below_min_verified": (bool(unv_abs[-1] < ver_cell_abs[0])
                                             if ver_cell_abs else None),
        "per_cell_true_delta_mean": unv,
        "CANNOT_ANSWER": ("a sample bounds the sample: this does not prove no UNSAMPLED cell is large, "
                          "and the bound is on the sampled distribution rather than the worst case over "
                          "%d. It also inherits the screen's site choice -- only p* and only the band are "
                          "ever patched, so a head mattering elsewhere is invisible to this AND to the "
                          "screen alike" % len(unverified)),
    }
    nb = w1.atomic_write_json(a.out, out)
    print("[fn] wrote+verified %s (%d bytes)" % (a.out, nb))
    print("[fn] UNVERIFIED |true delta| per cell: mean %.6f sd %.6f median %.6f max %.6f"
          % (mean_u, sd_u, statistics.median(unv_abs), unv_abs[-1]))
    if ver_cell_abs:
        print("[fn] VERIFIED   |true delta| per cell: mean %.6f median %.6f min %.6f max %.6f"
              % (statistics.fmean(ver_cell_abs), statistics.median(ver_cell_abs),
                 ver_cell_abs[0], ver_cell_abs[-1]))
        print("[fn] max unverified %.6f %s min verified %.6f"
              % (unv_abs[-1], "<" if unv_abs[-1] < ver_cell_abs[0] else ">=", ver_cell_abs[0]))
    print("[fn] one-sided 95%% upper bound on the unverified mean |true delta| = %.6f" % ub95)
    print("[fn] Welch t = %s (dof %s)" % (None if t is None else round(t, 4),
                                          None if dof is None else round(dof, 1)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
