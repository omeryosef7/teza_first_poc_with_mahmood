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
    ap.add_argument("--limit", type=int, default=0, help="0 = all rows; >0 for a smoke run")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    import torch
    import common as dc
    import score_behavior as sb
    from dominance import dominance_at

    lo, hi = (int(x) for x in a.band.split("-"))
    band = list(range(lo, hi + 1))
    heads = [int(x) for x in a.heads.split(",")]
    cids, kids = _ids(a.concept_ids, "concept-ids"), _ids(a.codeword_ids, "codeword-ids")
    if set(cids) & set(kids):
        raise SystemExit("REFUSING: the concept and codeword id sets overlap (%s). The direction "
                         "would be degenerate." % sorted(set(cids) & set(kids)))

    excl = {l.strip() for l in open(a.exclude_prompt_ids) if l.strip()}
    rows = []
    for line in open(a.bank):
        r = json.loads(line)
        if r.get("query_kind") != "semantic_one_word" or r.get("cell") != "C":
            continue
        if r.get("prompt_id") in excl:
            continue
        rows.append(r)
    if a.limit:
        rows = rows[:a.limit]
    if not rows:
        raise SystemExit("REFUSING: no cell-C semantic_one_word rows survived the exclusion file. "
                         "Absence is not a measurement (R20-6).")

    norm_w, urows, snap = load_unembed(a.snapshot_glob, list(cids) + list(kids))
    u = build_direction(norm_w, urows, cids, kids)
    print("[rung2] direction built from %d concept + %d codeword rows; |u| = %.6f"
          % (len(cids), len(kids), float(u.norm())))

    lm = dc.load_model(a.model, dtype=torch.float32, attn_implementation="eager")
    et = False
    per_dom = {}          # domain -> {(L,h): [values]}
    n_done, skipped = 0, {}
    for i, r in enumerate(rows):
        templated = dc.apply_template(lm.tokenizer, r["full_prompt"], enable_thinking=et)
        dk, why = sb.demo_key_positions(lm.tokenizer, r, templated)
        if why:
            skipped[why] = skipped.get(why, 0) + 1
            continue
        ids = lm.tokenizer(templated, add_special_tokens=False)["input_ids"]
        seq_len = len(ids)
        dst = seq_len - 1                 # the position that emits the first generated token
        # ⚠ S-381 left this index UNVERIFIED and warned against matching the intervention's
        # `target_surface_row_only` scope by reflex. It is asserted here rather than assumed:
        # the readout is the NEXT token after the prompt, so its state is the LAST prompt position.
        assert dst == len(ids) - 1 and dst >= 0, "readout index is not the final prompt position"
        if not dk:
            skipped["no_demo_keys"] = skipped.get("no_demo_keys", 0) + 1
            continue
        res = dominance_at(lm, ids, dst=dst, layers=band,
                           direction={L: u for L in band}, check_invariants=(i == 0))
        d = per_dom.setdefault(r["domain"], {})
        for L in band:
            Dd = res["D_dir"][L]                      # [n_head, T]
            for h in heads:
                d.setdefault((L, h), []).append(float(Dd[h, dk].sum()))
        n_done += 1

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
        "exclude_prompt_ids": a.exclude_prompt_ids, "n_excluded_ids": len(excl),
        "band": band, "heads": heads,
        "concept_ids": list(cids), "codeword_ids": list(kids),
        "direction": "g_final * (mean(concept rows) - mean(codeword rows)); FROZEN S-382",
        "⚠ NOT_THE_ENDPOINT": "y_install aggregates the casings with LOGSUMEXP; this direction is "
                              "LINEAR. This does NOT decompose y_install and no cell's share here "
                              "is its share of the installation effect (S-381/S-382).",
        "⚠ UNITS": "dominance_at unit-normalizes the direction, so these are contributions along "
                   "the UNIT direction, not logit contributions. The same u is passed at every "
                   "band layer, so cross-layer comparison is unaffected.",
        "statistical_unit": "domain", "n_domains": len(domains), "domains": domains,
        "n_prompts_used": n_done, "skipped": skipped,
        "readout_position": "seq_len - 1 (the position that emits the first generated token)",
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
