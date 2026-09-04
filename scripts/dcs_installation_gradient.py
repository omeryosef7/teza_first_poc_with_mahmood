#!/usr/bin/env python
"""dcs_installation_gradient.py -- `DCS-PR-016`: is the causal effect GRADED by how much of the
remapping was installed in the first place?

WRITTEN AND COMMITTED BEFORE ANY HELD-OUT NUMBER WAS COMPUTED. The hypothesis was formed on
`candle`->`missile` (`R-039`, exploratory and labelled so); this script exists to test it on
concepts that played no part in forming it. Same discipline as `dcs_generality.py`.

THE ESTIMAND.
    Per domain d, in cell C (natural_doublespeak) of the BASELINE arm:
        install_d = fraction of rows whose ARGMAX answer decodes to the concept word
    Per domain d, row-paired by `prompt_id` between the knockout arm and the baseline arm:
        delta_d   = mean_rows[ semantic_logodds(KO) - semantic_logodds(baseline) ]
    PRIMARY   Spearman rho(install, delta) over domains. Predicted NEGATIVE: the more of the
              mapping was installed, the more of it there is to destroy.
    p-value   two-sided PERMUTATION test on the domain labels, seeded, stdlib only. Exact
              enumeration when n! is small enough, otherwise a fixed number of seeded shuffles.

THE CONTROL THAT MAKES IT NON-TRIVIAL (`R-039` confound 2). `delta` is measured against the same
baseline that supplies `install`, so part of any negative rho is regression to the mean. Passing
`--placebo` runs the IDENTICAL statistic on an arm that received the identical intervention at an
INERT-BY-INTENT layer band. Regression to the mean is present there and the mechanism is not, so
the placebo's rho is the mechanical component. The reported quantity is the CONTRAST.
    ==> `rho_knockout` alone is NOT the result. `rho_knockout` vs `rho_placebo` is.

REFUSES rather than reports when: an arm is missing or carries no DONE.json, the arms cover
different `prompt_id` sets within the cell, or fewer than 5 domains are informative.

Stdlib + a tokenizer (needed to decode `top1_id`). Judge-free: reads `results.jsonl` only.
"""
from __future__ import annotations
import argparse, collections, itertools, json, math, os, random, statistics as st, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = "DCS_INSTALLATION_GRADIENT/1"
CELL_C = "natural_doublespeak"
LOW, HIGH = 0.25, 0.75
MIN_GROUP = 3
N_PERM = 20000
PERM_SEED = 20260904


def load(run_dir: str) -> dict:
    p = os.path.join(run_dir, "results.jsonl")
    if not os.path.isfile(p):
        sys.exit(f"REFUSING: no results.jsonl in {run_dir}")
    if not os.path.isfile(os.path.join(run_dir, "DONE.json")):
        sys.exit(f"REFUSING: {run_dir} carries no DONE.json")
    rows = {}
    for line in open(p):
        d = json.loads(line)
        if d["condition"] != CELL_C:
            continue
        rows[d["prompt_id"]] = d
    if not rows:
        sys.exit(f"REFUSING: no {CELL_C} rows in {run_dir}")
    return rows


def installation(base: dict, tok, needle: str) -> dict:
    per = collections.defaultdict(list)
    for r in base.values():
        if "top1_id" not in r:
            sys.exit("REFUSING: baseline rows carry no top1_id; installation is undefined "
                     "without the surface answer (this run predates the field)")
        ans = tok.decode([r["top1_id"]]).strip().lower()
        per[r["domain"]].append(1.0 if needle in ans else 0.0)
    return {d: st.mean(v) for d, v in per.items()}


def paired_delta(treat: dict, base: dict, label: str) -> dict:
    if set(treat) != set(base):
        sys.exit(f"REFUSING {label}: arms cover different prompt_id sets "
                 f"({len(set(treat) - set(base))} only in treat, "
                 f"{len(set(base) - set(treat))} only in base)")
    per = collections.defaultdict(list)
    for pid, tr in treat.items():
        per[tr["domain"]].append(tr["semantic_logodds"] - base[pid]["semantic_logodds"])
    return {d: st.mean(v) for d, v in per.items()}


def _rank(xs):
    """Average ranks, so ties do not silently bias rho. Installation is heavily tied by
    construction (rows/domain is small), which is exactly when midranks matter."""
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    ranks = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def pearson(a, b) -> float:
    n = len(a)
    ma, mb = st.mean(a), st.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    if da == 0 or db == 0:
        return float("nan")
    return num / (da * db)


def spearman_perm(x, y, seed=PERM_SEED, n_perm=N_PERM):
    """Two-sided permutation p for Spearman rho. Exact when n <= 8, else seeded shuffles."""
    rx, ry = _rank(x), _rank(y)
    rho = pearson(rx, ry)
    if math.isnan(rho):
        return rho, 1.0, "DEGENERATE: a predictor with zero variance"
    n = len(rx)
    if n <= 8:
        perms = list(itertools.permutations(ry))
        hits = sum(1 for p in perms if abs(pearson(rx, list(p))) >= abs(rho) - 1e-12)
        return rho, hits / len(perms), f"exact over {len(perms)} permutations"
    rnd = random.Random(seed)
    shuf = list(ry)
    hits = 0
    for _ in range(n_perm):
        rnd.shuffle(shuf)
        if abs(pearson(rx, shuf)) >= abs(rho) - 1e-12:
            hits += 1
    return rho, (hits + 1) / (n_perm + 1), f"{n_perm} seeded shuffles (seed {seed})"


def split_report(install: dict, delta: dict) -> dict:
    lo = [d for d in delta if install[d] <= LOW]
    hi = [d for d in delta if install[d] >= HIGH]
    out = {"low_cut": LOW, "high_cut": HIGH,
           "n_low": len(lo), "n_high": len(hi)}
    if len(lo) < MIN_GROUP or len(hi) < MIN_GROUP:
        out["STATUS"] = "CANNOT_ANSWER"
        out["why"] = (f"the binary split needs >= {MIN_GROUP} domains per group; this bank has "
                      f"{len(lo)} low and {len(hi)} high. Declared UNAVAILABLE rather than run "
                      "at a group size that cannot support it.")
        return out
    out["STATUS"] = "OK"
    out["mean_delta_low"] = st.mean([delta[d] for d in lo])
    out["mean_delta_high"] = st.mean([delta[d] for d in hi])
    out["pos_low"] = sum(1 for d in lo if delta[d] > 0)
    out["pos_high"] = sum(1 for d in hi if delta[d] > 0)
    return out


def analyse(install, delta, label):
    doms = sorted(set(install) & set(delta))
    if len(doms) < 5:
        sys.exit(f"REFUSING {label}: only {len(doms)} shared domains")
    x = [install[d] for d in doms]
    y = [delta[d] for d in doms]
    rho, p, how = spearman_perm(x, y)
    return {"label": label, "n_domains": len(doms), "spearman_rho": rho,
            "perm_p": p, "perm_method": how,
            "install_mean": st.mean(x), "install_sd": st.pstdev(x),
            "delta_mean": st.mean(y),
            "binary_split": split_report(install, delta),
            "_per_domain": {d: {"install": install[d], "delta": delta[d]} for d in doms}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--knockout", required=True)
    ap.add_argument("--placebo", default="",
                    help="the SAME intervention at an inert-by-intent band; supplies the "
                         "regression-to-the-mean component. Omitting it makes rho "
                         "uninterpretable and the artifact says so.")
    ap.add_argument("--concept-token", required=True)
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--label", required=True)
    ap.add_argument("--held-out", action="store_true",
                    help="stamp the artifact as a held-out test of PR-016 rather than as the "
                         "exploratory source population (candle)")
    ap.add_argument("--tag", default="dcs_installation_gradient")
    ap.add_argument("--out", default=os.path.join(ROOT, "outputs/boombness/dcs_analysis"))
    a = ap.parse_args()

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model)

    base = load(a.baseline)
    ko = load(a.knockout)
    inst = installation(base, tok, a.concept_token.strip().lower())

    out = {"schema": SCHEMA, "label": a.label, "model": a.model,
           "concept_token": a.concept_token,
           "role": "HELD_OUT_TEST" if a.held_out else "EXPLORATORY_SOURCE",
           "arms": {"baseline": a.baseline, "knockout": a.knockout, "placebo": a.placebo},
           "knockout": analyse(inst, paired_delta(ko, base, "knockout"), "knockout")}

    if a.placebo:
        out["placebo"] = analyse(inst, paired_delta(load(a.placebo), base, "placebo"), "placebo")
        out["rho_contrast"] = out["knockout"]["spearman_rho"] - out["placebo"]["spearman_rho"]
    else:
        out["placebo"] = {"STATUS": "NOT_RUN",
                          "why": "without a placebo arm the regression-to-the-mean component of "
                                 "rho is unmeasured; rho_knockout alone is NOT the result"}
        out["rho_contrast"] = None

    os.makedirs(a.out, exist_ok=True)
    dst = os.path.join(a.out, f"{a.tag}_{a.label}.json")
    json.dump(out, open(dst, "w"), indent=2, sort_keys=True)

    print(f"=== {a.label}  [{out['role']}] ===")
    for k in ("knockout", "placebo"):
        r = out[k]
        if "STATUS" in r:
            print(f"  {k:9s} {r['STATUS']}")
            continue
        b = r["binary_split"]
        bs = (f"low n={b['n_low']} mean={b['mean_delta_low']:+.3f} | "
              f"high n={b['n_high']} mean={b['mean_delta_high']:+.3f}"
              if b["STATUS"] == "OK" else
              f"split {b['STATUS']} (low {b['n_low']}, high {b['n_high']})")
        print(f"  {k:9s} nD={r['n_domains']:3d} rho={r['spearman_rho']:+.3f} "
              f"p={r['perm_p']:.4f}  install sd={r['install_sd']:.3f}  {bs}")
    if out["rho_contrast"] is not None:
        print(f"  CONTRAST rho_ko - rho_placebo = {out['rho_contrast']:+.3f}")
    print(f"  -> {dst}")


if __name__ == "__main__":
    main()
