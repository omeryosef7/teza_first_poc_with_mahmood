#!/usr/bin/env python
"""dcs_generality.py -- `DCS-PR-013`'s second/third-concept replication, as CODE.

WRITTEN AND COMMITTED BEFORE ANY PR-013 ARM FINISHED. Same reason as
`scripts/dcs_cell_interaction.py`: a replication whose analysis is written after seeing which way
the arms went is not a replication.

THE ESTIMAND (`PR-013`).
    PRIMARY   per domain d, cell C (natural_doublespeak):
                  delta_d = mean_rows[ semantic_logodds(KO) - semantic_logodds(baseline) ]
              two-sided SIGN TEST over the 20 domains. Predicted NEGATIVE (reading moves back
              toward the literal codeword).
    SECONDARY (a) specificity DiD: mean delta_d^C - mean delta_d^B, predicted negative.
              (b) control inertness: the same statistic with `control` in place of `KO`.

PAIRING. Within a cell the three arms run the SAME bank rows, so KO/control/baseline are paired
BY `prompt_id` and the pairing is asserted, not assumed. Across cells C and B the prompts differ
by construction (a natural_doublespeak row and a direct_harmful row never share a prompt_id), so
the C-vs-B comparison pairs BY DOMAIN ONLY -- strictly weaker, and labelled as such, exactly as
`dcs_cell_interaction.py` does for the same reason.

REFUSES rather than reports when: an arm is missing, arms cover different prompt_id sets within a
cell, a domain set differs across cells, or a row count is not the expected 80 per cell. A
replication that silently analysed a different population than the headline would be worse than
no replication.

Stdlib only. Reads `results.jsonl` (logit-derived, judge-free) -- PR-013 never needed the API,
which is why `C-024` did not block it.
"""
from __future__ import annotations
import argparse, collections, json, os, statistics as st, sys
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = "DCS_GENERALITY/1"
ALPHA = 0.05
CELLS = {"C": "natural_doublespeak", "B": "direct_harmful"}


def two_sided_sign_p(x: int, n: int) -> float:
    """Exact binomial sign test at p=0.5, two-sided. Fractions => no float drift."""
    if n == 0:
        return 1.0
    k = min(x, n - x)
    tail = sum(Fraction(_c(n, i)) for i in range(0, k + 1)) / Fraction(2) ** n
    return min(1.0, float(2 * tail))


def _c(n: int, k: int) -> int:
    r = 1
    for i in range(k):
        r = r * (n - i) // (i + 1)
    return r


def load(run_dir: str) -> dict:
    p = os.path.join(run_dir, "results.jsonl")
    if not os.path.isfile(p):
        sys.exit(f"REFUSING: no results.jsonl in {run_dir}")
    if not os.path.isfile(os.path.join(run_dir, "DONE.json")):
        sys.exit(f"REFUSING: {run_dir} carries no DONE.json")
    rows = {}
    for line in open(p):
        d = json.loads(line)
        rows[d["prompt_id"]] = d
    return rows


def cell_view(rows: dict, cell: str) -> dict:
    cond = CELLS[cell]
    return {k: v for k, v in rows.items() if v["condition"] == cond}


def paired_domain_deltas(treat: dict, base: dict, cell: str, expect: int):
    t, b = cell_view(treat, cell), cell_view(base, cell)
    if set(t) != set(b):
        sys.exit(f"REFUSING cell {cell}: arms cover different prompt_id sets "
                 f"({len(set(t) - set(b))} only in treat, {len(set(b) - set(t))} only in base)")
    if expect and len(t) != expect:
        sys.exit(f"REFUSING cell {cell}: {len(t)} rows, expected {expect}")
    per = collections.defaultdict(list)
    for pid, tr in t.items():
        per[tr["domain"]].append(tr["semantic_logodds"] - b[pid]["semantic_logodds"])
    return {dom: st.mean(v) for dom, v in per.items()}, len(t)


def sign_report(deltas: dict, label: str) -> dict:
    vals = list(deltas.values())
    neg = sum(1 for v in vals if v < 0)
    pos = sum(1 for v in vals if v > 0)
    n_inf = neg + pos
    p = two_sided_sign_p(pos, n_inf)
    floor = two_sided_sign_p(0, n_inf) if n_inf else 1.0
    return {"label": label, "n_domains": len(vals), "k_informative": n_inf,
            "pos": pos, "neg": neg, "mean_delta": st.mean(vals) if vals else None,
            "median_delta": st.median(vals) if vals else None,
            "sign_p": p, "attainable_p_floor": floor,
            "significant": bool(p < ALPHA)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--knockout", required=True)
    ap.add_argument("--control", required=True)
    ap.add_argument("--concept", required=True, help="label only, e.g. lantern_poison")
    ap.add_argument("--expect-per-cell", type=int, default=80)
    ap.add_argument("--tag", default="dcs_generality")
    ap.add_argument("--out", default=os.path.join(ROOT, "outputs/boombness/dcs_analysis"))
    a = ap.parse_args()

    base, ko, ctrl = load(a.baseline), load(a.knockout), load(a.control)
    out = {"schema": SCHEMA, "concept": a.concept, "alpha": ALPHA,
           "arms": {"baseline": a.baseline, "knockout": a.knockout, "control": a.control},
           "cells": {}}

    dom_sets = {}
    for cell in ("C", "B"):
        ko_d, n = paired_domain_deltas(ko, base, cell, a.expect_per_cell)
        ct_d, _ = paired_domain_deltas(ctrl, base, cell, a.expect_per_cell)
        if set(ko_d) != set(ct_d):
            sys.exit(f"REFUSING cell {cell}: KO and control cover different domains")
        dom_sets[cell] = set(ko_d)
        out["cells"][cell] = {"condition": CELLS[cell], "n_rows": n,
                              "knockout": sign_report(ko_d, f"{cell}: KO - baseline"),
                              "control": sign_report(ct_d, f"{cell}: control - baseline"),
                              "_ko_deltas": ko_d, "_ctrl_deltas": ct_d}

    if dom_sets["C"] != dom_sets["B"]:
        sys.exit("REFUSING: cells C and B cover different domain sets; the DiD would not be paired")

    did = {d: out["cells"]["C"]["_ko_deltas"][d] - out["cells"]["B"]["_ko_deltas"][d]
           for d in dom_sets["C"]}
    out["specificity_did"] = sign_report(did, "DiD: (C: KO-base) - (B: KO-base)")
    out["specificity_did"]["PAIRING_NOTE"] = (
        "paired BY DOMAIN ONLY -- C and B are different prompts by construction, so this is "
        "strictly weaker than the within-cell row-paired tests above")

    for cell in ("C", "B"):
        out["cells"][cell].pop("_ko_deltas"); out["cells"][cell].pop("_ctrl_deltas")

    os.makedirs(a.out, exist_ok=True)
    dst = os.path.join(a.out, f"{a.tag}_{a.concept}.json")
    json.dump(out, open(dst, "w"), indent=2, sort_keys=True)

    c = out["cells"]["C"]
    print(f"=== {a.concept} ===")
    for cell in ("C", "B"):
        for arm in ("knockout", "control"):
            r = out["cells"][cell][arm]
            print(f"  {r['label']:34s} mean={r['mean_delta']:+8.3f}  "
                  f"{r['pos']}+/{r['neg']}-  p={r['sign_p']:.3e}  floor={r['attainable_p_floor']:.2e}")
    r = out["specificity_did"]
    print(f"  {r['label']:34s} mean={r['mean_delta']:+8.3f}  {r['pos']}+/{r['neg']}-  p={r['sign_p']:.3e}")
    print(f"  -> {dst}")


if __name__ == "__main__":
    main()
