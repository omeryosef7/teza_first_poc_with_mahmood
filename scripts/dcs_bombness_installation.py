#!/usr/bin/env python3
"""DCS-PR-033 — the installation gate, and Matan's prompt-validation table.

FROZEN BEFORE ITS DATA. Implements §14 of
`external_md/DCS_BOMBNESS_SPECIFICITY_AND_CAUSAL_VALIDATION_PLAN_AND_PROGRESS_20260905.md`.

THE QUESTION IT ANSWERS is Matan's: *do these prompts even work?* If `knife` never installs, cell C
of the knife bank is approximately cell A of the knife bank, and a bomb-vs-knife classifier separates
them easily FOR THE WRONG REASON. That would look like concept specificity and be nothing of the kind.

INPUT is `results.jsonl` from `extract_boombness.py` -- the logit-lens readout computed on the SAME
forward pass as the hidden states, so this gate costs no additional GPU:
    ll|L{0,4,8,12,16,20,24,28,31}|{p_concept, p_codeword, rank_concept, boombness}

⛔ The gate layer is L16, PRE-DECLARED and deliberately OUTSIDE the L6-14 probe band, so the gate is
not the same measurement as the thing it gates.
"""
from __future__ import annotations
import argparse, collections, glob, json, os
import numpy as np

CODEWORDS = ("button", "basket")
CONCEPTS = ("bomb", "knife", "gun", "club")
GATE_LAYER = 16                      # PR-033 §14.3, pre-declared, outside L6-14
REPORT_LAYERS = (0, 4, 8, 12, 16, 20, 24, 28, 31)
PRIMARY_NEXAMPLES = (4, 8)
CHANNEL = "semantic_one_word"
MIN_DOMAINS_POSITIVE = 5             # of 6
N_DOMAINS = 6


def load_results(run_dir):
    p = os.path.join(run_dir, "results.jsonl")
    if not os.path.exists(p):
        return None
    return [json.loads(l) for l in open(p)]


def installation(rows, layer):
    """Per-domain paired C-minus-A difference in the logit-lens boombness at `layer`.

    Paired at the DOMAIN level (cell means within domain), which is the declared independence unit.
    """
    key = f"ll|L{layer}|boombness"
    byc = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        if r.get("query_kind") != CHANNEL or r.get("n_examples") not in PRIMARY_NEXAMPLES:
            continue
        if not r.get("is_final_occurrence", True):
            continue
        if r.get("cell") in ("A", "C") and key in r:
            byc[r["domain"]][r["cell"]].append(float(r[key]))
    per_domain = {}
    for dom, cells in byc.items():
        if cells.get("A") and cells.get("C"):
            per_domain[dom] = float(np.mean(cells["C"]) - np.mean(cells["A"]))
    return per_domain


def descriptives(rows):
    """The prompt-validation table Matan asked for: distributions, not means alone."""
    out = {}
    for layer in REPORT_LAYERS:
        kb, kp, kc = (f"ll|L{layer}|boombness", f"ll|L{layer}|p_concept",
                      f"ll|L{layer}|p_codeword")
        per_cell = collections.defaultdict(lambda: collections.defaultdict(list))
        for r in rows:
            if r.get("query_kind") != CHANNEL or r.get("n_examples") not in PRIMARY_NEXAMPLES:
                continue
            if kb not in r:
                continue
            per_cell[r["cell"]]["boombness"].append(float(r[kb]))
            if kp in r:
                per_cell[r["cell"]]["p_concept"].append(float(r[kp]))
            if kc in r:
                per_cell[r["cell"]]["p_codeword"].append(float(r[kc]))
        stat = {}
        for cell, d in per_cell.items():
            stat[cell] = {k: dict(n=len(v), mean=float(np.mean(v)), sd=float(np.std(v)),
                                  q10=float(np.quantile(v, .1)), q50=float(np.quantile(v, .5)),
                                  q90=float(np.quantile(v, .9)))
                          for k, v in d.items() if v}
        out[f"L{layer}"] = stat
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-root", default="outputs/boombness/extract_boombness")
    ap.add_argument("--run-prefix", default="bombspec")
    ap.add_argument("--out", default="outputs/boombness/dcs_analysis/dcs_bombness_installation.json")
    a = ap.parse_args()

    res = dict(preregistration="DCS-PR-033", gate_layer=GATE_LAYER, channel=CHANNEL,
               n_examples=list(PRIMARY_NEXAMPLES),
               min_domains_positive=MIN_DOMAINS_POSITIVE, banks={})
    verdicts = {}
    for cw in CODEWORDS:
        for cc in CONCEPTS:
            hits = sorted(glob.glob(os.path.join(a.runs_root, f"{a.run_prefix}_{cw}_{cc}_*")))
            if not hits:
                continue
            rows = load_results(hits[-1])
            if rows is None:
                continue
            pd = installation(rows, GATE_LAYER)
            npos = sum(1 for v in pd.values() if v > 0)
            mean = float(np.mean(list(pd.values()))) if pd else None
            passed = bool(pd and npos >= MIN_DOMAINS_POSITIVE and mean is not None and mean > 0)
            entry = dict(run_dir=hits[-1], per_domain=pd, n_domains=len(pd),
                         n_domains_positive=npos, mean_delta=mean, passed=passed,
                         profile={f"L{L}": (lambda p: dict(
                             n_domains=len(p), n_positive=sum(1 for v in p.values() if v > 0),
                             mean=float(np.mean(list(p.values()))) if p else None))(
                                 installation(rows, L)) for L in REPORT_LAYERS},
                         descriptives=descriptives(rows))
            res["banks"][f"{cw}_{cc}"] = entry
            verdicts[f"{cw}_{cc}"] = passed

    # ---- the declared consequences (PR-033 §14.4)
    prim = {c: verdicts.get(f"button_{c}") for c in ("bomb", "knife", "gun")}
    failed = [c for c, v in prim.items() if v is False]
    if prim.get("bomb") is False:
        verdict = "VOID — bomb does not install; there is no mapping to be specific about"
    elif len(failed) >= 2:
        verdict = "CANNOT ANSWER — >=2 of 3 primary concepts do not install"
    elif failed:
        verdict = (f"PARTIAL — {failed} NOT INSTALLED; PR-031 primary must be reported BOTH with "
                   f"and without {failed}, neither promoted")
    elif all(v is True for v in prim.values()):
        verdict = "PASS — bomb, knife and gun all install; PR-031 primary stands as written"
    else:
        verdict = "INCOMPLETE — not all primary banks extracted yet"
    res["gate_verdict"] = verdict
    res["primary_concept_pass"] = prim

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1, default=str)
    print(f"[write] {a.out}\n")
    print(f"{'bank':<16} {'n_dom':>5} {'n_pos':>5} {'mean_delta':>11}  passed")
    for k, v in sorted(res["banks"].items()):
        md = "None" if v["mean_delta"] is None else f"{v['mean_delta']:+.4f}"
        print(f"  {k:<14} {v['n_domains']:>5} {v['n_domains_positive']:>5} {md:>11}  {v['passed']}")
    print(f"\nGATE VERDICT: {res['gate_verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
