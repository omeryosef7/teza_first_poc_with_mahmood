#!/usr/bin/env python3
"""DCS-PR-034 — the installation gate, on the forced-choice instrument.

FROZEN BEFORE ITS DATA. Implements §18 of
`external_md/DCS_BOMBNESS_SPECIFICITY_AND_CAUSAL_VALIDATION_PLAN_AND_PROGRESS_20260905.md`.

WHY A SECOND INSTRUMENT (C-048). The first gate (`PR-033`) was pre-declared at logit-lens L16, where
the model holds ~1e-5 total probability across both option tokens -- the statistic there is a ratio
of two numbers the model does not hold, so that gate is VACUOUS, not failed. Rather than pick a
logit-lens layer after seeing the profile (L31 passes 6/6, L20 fails 2/6 -- two defensible rules,
opposite verdicts), the gate moves to the instrument this phase has calibrated all along:
`semantic_logodds` with `option_mass` beside it, the measure behind `R-050`.

⚠ ON THE APPARENT CONFLICT WITH §2.3. `semantic_forced_choice` is disqualified as the PROBE channel
because its question names the concept, so a classifier reading hidden states could read the answer
off the question. That objection does not apply to an ENDPOINT: here we ask the MODEL its own
answer, and "does the word button refer to a button or to a bomb?" IS the installation measurement.
Leakage disqualifies a channel for a probe, not for an endpoint.
"""
from __future__ import annotations
import argparse, collections, glob, json, os
import numpy as np

CODEWORDS = ("button", "basket")
CONCEPTS = ("bomb", "knife", "gun", "club")
PRIMARY_CODEWORD = "button"
PRIMARY_CONCEPTS = ("bomb", "knife", "gun")     # club excluded from the primary (A-020 §8.3)
MIN_DOMAINS_POSITIVE = 5
N_DOMAINS = 6
EXPECT_N = 48
MASS_FLOOR = 0.05                                # R-050 / PR-034 §18.3


def load(run_dir):
    if not os.path.exists(os.path.join(run_dir, "DONE.json")):
        return None                              # never read an in-progress run (C-047 / §17.3)
    p = os.path.join(run_dir, "results.jsonl")
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else None


def gate_one(rows):
    byc = collections.defaultdict(lambda: collections.defaultdict(list))
    mass = collections.defaultdict(list)
    for r in rows:
        if "semantic_logodds" not in r or r.get("cell") not in ("A", "C"):
            continue
        byc[r["domain"]][r["cell"]].append(float(r["semantic_logodds"]))
        if "option_mass" in r:
            mass[r["cell"]].append(float(r["option_mass"]))
    per_domain = {d: float(np.mean(c["C"]) - np.mean(c["A"]))
                  for d, c in byc.items() if c.get("A") and c.get("C")}
    cellmean = {cell: float(np.mean([v for d in byc.values() for v in d.get(cell, [])]))
                for cell in ("A", "C")
                if any(d.get(cell) for d in byc.values())}
    mm = {c: float(np.median(v)) for c, v in mass.items() if v}
    npos = sum(1 for v in per_domain.values() if v > 0)
    mean = float(np.mean(list(per_domain.values()))) if per_domain else None
    mass_limited = any(v < MASS_FLOOR for v in mm.values())
    passed = bool(per_domain and npos >= MIN_DOMAINS_POSITIVE and mean is not None and mean > 0)
    return dict(n_rows=len(rows), n_domains=len(per_domain), per_domain=per_domain,
                n_domains_positive=npos, mean_delta=mean, cell_means=cellmean,
                option_mass_median=mm, mass_limited=mass_limited, passed=passed,
                ok_n=(len(rows) == EXPECT_N))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="outputs/boombness/score_behavior")
    ap.add_argument("--out", default="outputs/boombness/dcs_analysis/dcs_installation_gate_fc.json")
    a = ap.parse_args()

    res = dict(preregistration="DCS-PR-034", instrument="semantic_forced_choice/semantic_logodds",
               min_domains_positive=MIN_DOMAINS_POSITIVE, expect_n=EXPECT_N,
               mass_floor=MASS_FLOOR, banks={})
    for cw in CODEWORDS:
        for cc in CONCEPTS:
            hits = sorted(glob.glob(os.path.join(a.root, f"inst_{cw}_{cc}_*")))
            if not hits:
                continue
            rows = load(hits[-1])
            if rows is None:
                continue
            e = gate_one(rows)
            e["run_dir"] = hits[-1]
            res["banks"][f"{cw}_{cc}"] = e

    prim = {c: res["banks"].get(f"{PRIMARY_CODEWORD}_{c}", {}).get("passed")
            for c in PRIMARY_CONCEPTS}
    res["primary_concept_pass"] = prim
    failed = [c for c, v in prim.items() if v is False]
    if any(v is None for v in prim.values()):
        verdict = "INCOMPLETE — not all primary banks have a finished arm yet"
    elif prim.get("bomb") is False:
        verdict = ("VOID — bomb does not install on the phase's own forced-choice instrument; "
                   "there is no mapping for a specificity test to be specific about")
    elif len(failed) >= 2:
        verdict = f"CANNOT ANSWER — {failed} do not install; no usable comparator set at 6 domains"
    elif failed:
        verdict = (f"PARTIAL — {failed} NOT INSTALLED. PR-031 primary MUST be reported both with "
                   f"and without {failed}; neither version promoted over the other.")
    else:
        verdict = "PASS — bomb, knife and gun all install; PR-031 primary stands as written"
    res["gate_verdict"] = verdict

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1, default=str)
    print(f"[write] {a.out}\n")
    print(f"{'bank':<15} {'n':>4} {'dom':>4} {'pos':>4} {'A_mean':>9} {'C_mean':>9} "
          f"{'delta':>9} {'massA':>7} {'massC':>7}  pass")
    for k, v in sorted(res["banks"].items()):
        cm, mm = v["cell_means"], v["option_mass_median"]
        f = lambda x: f"{x:+9.3f}" if x is not None else "     None"
        print(f"  {k:<13} {v['n_rows']:>4} {v['n_domains']:>4} {v['n_domains_positive']:>4} "
              f"{f(cm.get('A'))} {f(cm.get('C'))} {f(v['mean_delta'])} "
              f"{mm.get('A', float('nan')):>7.3f} {mm.get('C', float('nan')):>7.3f}  "
              f"{v['passed']}{'  ⚠MASS-LIMITED' if v['mass_limited'] else ''}")
    print(f"\nGATE VERDICT: {res['gate_verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
