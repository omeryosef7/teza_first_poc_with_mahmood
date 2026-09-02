#!/usr/bin/env python
"""tsc_model_interaction.py -- `TSC-PR-004`'s model x intervention test, as CODE.

WRITTEN AND COMMITTED BEFORE ANY QWEN INTERVENTION OUTCOME EXISTS. That is the only reason it is
worth anything: an interaction test chosen after seeing which way the two models went is not a test.

⛔ THE RULE IT ENFORCES. "Significant in Llama, non-significant in Qwen" is NOT a model interaction
and must never be written as one. Two tests that disagree about significance can easily have
effects that do not differ; the difference has to be tested directly, on paired material.

WHAT MAKES THE PAIRING LEGITIMATE HERE. Both models were run on the SAME bank
(`cds38_button_bomb`), the SAME 380 prompt ids, the SAME 38 domains, the same dose, band, scope,
seed, cap and judge. So domain d has a per-domain effect under each model and the two are paired by
domain identity, not merely by rank.

THE ESTIMAND. Per domain d and model m:

    delta_d^m = attacks(d | control arm) - attacks(d | demoproc arm)      # rows REMOVED

and the interaction is an exact paired sign test on `delta_d^Llama - delta_d^Qwen` over the 38
domains, with `k_informative` and the attainable floor `2/2**k_inf` reported beside it -- because a
design with few informative domains is UNINFORMATIVE BY CONSTRUCTION and must not be read as a
null (`C-95`).

⚠ BASELINE HEADROOM IS NOT EQUAL BETWEEN THE MODELS (Llama 0.39-0.42, Qwen 0.2026), so the RAW
difference of deltas confounds "the intervention does less on Qwen" with "there was less to remove".
Both are therefore reported and neither is allowed to stand alone:
  * ABSOLUTE  -- delta in rows, the registered primary;
  * NORMALISED -- delta as a fraction of that domain's own baseline attacks, which is scale-free but
    undefined on domains with a zero baseline (those are dropped and COUNTED, never imputed).

Stdlib only. Reads scalar judge columns; never opens `gens.jsonl`.
"""
from __future__ import annotations
import argparse, collections, json, math, os
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = "TSC_MODEL_INTERACTION/1"
ALPHA = 0.05
PIN = "openai/gpt-4o-mini"


def two_sided_sign_p(x, n):
    """Exact two-sided binomial sign test, integer arithmetic. `x` = smaller tail count."""
    if n == 0:
        return Fraction(1)
    tot = sum(math.comb(n, k) for k in range(0, x + 1))
    return min(Fraction(2 * tot, 1 << n), Fraction(1))


def load(judge_dir, dose):
    out = {}
    with open(os.path.join(judge_dir, "results.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("n_examples") != dose:
                continue
            if r["judge_model_used"] != PIN:
                raise SystemExit(f"REFUSING: {judge_dir} used {r['judge_model_used']!r}, not {PIN}")
            if str(r.get("judge_status")) != "ok":
                raise SystemExit(f"REFUSING: {judge_dir} has judge_status {r.get('judge_status')!r}")
            out[r["prompt_id"]] = (r["domain"], bool(r["malicious_at_0.5"]))
    return out


def per_domain(rows):
    c = collections.Counter()
    for _, (dm, m) in rows.items():
        c[dm] += int(m)
        c.setdefault(dm, c[dm])
    return c


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for m in ("llama", "qwen"):
        ap.add_argument(f"--{m}-baseline", required=True)
        ap.add_argument(f"--{m}-demoproc", required=True)
        ap.add_argument(f"--{m}-control", action="append", required=True,
                        help="repeatable; the registered primary uses all three")
    ap.add_argument("--dose", type=int, default=4)
    ap.add_argument("--tag", default="tsc_model_interaction")
    ap.add_argument("--out", default=os.path.join(ROOT, "outputs/boombness/cds_analysis"))
    a = ap.parse_args()

    arms = {}
    for m in ("llama", "qwen"):
        arms[m] = {"A": load(getattr(a, f"{m}_baseline"), a.dose),
                   "demoproc": load(getattr(a, f"{m}_demoproc"), a.dose),
                   "controls": [load(d, a.dose) for d in getattr(a, f"{m}_control")]}

    # ---- THE ROW SETS MUST BE THE SAME ROWS, or "paired by domain" is a coincidence of labels.
    ref = set(arms["llama"]["A"])
    for m in ("llama", "qwen"):
        for name, rows in [("A", arms[m]["A"]), ("demoproc", arms[m]["demoproc"])] + \
                          [(f"ctrl{i}", r) for i, r in enumerate(arms[m]["controls"])]:
            if set(rows) != ref:
                raise SystemExit(f"REFUSING: {m}/{name} covers a different prompt_id set "
                                 f"({len(set(rows) ^ ref)} symmetric difference). The interaction "
                                 f"is paired BY DOMAIN and that requires the same rows.")
            for pid in ref:
                if rows[pid][0] != arms["llama"]["A"][pid][0]:
                    raise SystemExit(f"REFUSING: {m}/{name} disagrees about the domain of {pid}.")

    doms = sorted({d for d, _ in arms["llama"]["A"].values()})
    results = {}
    for ci in range(len(arms["llama"]["controls"])):
        if ci >= len(arms["qwen"]["controls"]):
            break
        d_abs, d_norm, dropped = {}, {}, 0
        for m in ("llama", "qwen"):
            dp = per_domain(arms[m]["demoproc"])
            ct = per_domain(arms[m]["controls"][ci])
            base = per_domain(arms[m]["A"])
            d_abs[m] = {d: ct[d] - dp[d] for d in doms}
            d_norm[m] = {d: ((ct[d] - dp[d]) / base[d]) for d in doms if base[d] > 0}
        common_norm = sorted(set(d_norm["llama"]) & set(d_norm["qwen"]))
        dropped = len(doms) - len(common_norm)

        block = {}
        for scale, table, keys in (("absolute", d_abs, doms),
                                   ("normalised", d_norm, common_norm)):
            hi = sum(1 for d in keys if table["llama"][d] > table["qwen"][d])
            lo = sum(1 for d in keys if table["llama"][d] < table["qwen"][d])
            k = hi + lo
            p = two_sided_sign_p(min(hi, lo), k)
            floor = Fraction(2, 1 << k) if k else Fraction(1)
            block[scale] = {
                "k_domains": len(keys), "llama_larger": hi, "qwen_larger": lo,
                "k_informative": k, "p_value": float(p),
                "attainable_p_floor": float(floor),
                "CAPABLE": bool(floor <= ALPHA),
                "total_llama": sum(table["llama"][d] for d in keys),
                "total_qwen": sum(table["qwen"][d] for d in keys),
            }
        block["normalised"]["domains_dropped_zero_baseline"] = dropped
        results[f"vs_control_{ci + 1}"] = block

    doc = {"schema": SCHEMA, "alpha": ALPHA, "dose": a.dose, "k_domains": len(doms),
           "estimand": "delta_d^m = attacks(d|control) - attacks(d|demoproc); "
                       "interaction = exact paired sign test on delta^llama - delta^qwen over domains",
           "preregistered": "TSC-PR-004, before any Qwen intervention outcome existed",
           "baseline_headroom_note": ("Llama and Qwen baselines differ (0.39-0.42 vs 0.2026), so the "
                                      "ABSOLUTE contrast confounds effect size with headroom. The "
                                      "NORMALISED contrast is scale-free but undefined on zero-baseline "
                                      "domains, which are dropped and counted, never imputed."),
           "results": results}
    os.makedirs(a.out, exist_ok=True)
    p = os.path.join(a.out, f"{a.tag}.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)

    print(f"[tsc] model x intervention, k_domains={len(doms)}, dose={a.dose}")
    for name, block in results.items():
        for scale in ("absolute", "normalised"):
            b = block[scale]
            verdict = ("MODEL-SPECIFIC" if b["CAPABLE"] and b["p_value"] < ALPHA else
                       "no detectable interaction" if b["CAPABLE"] else
                       "UNINFORMATIVE BY CONSTRUCTION")
            print(f"  {name:16s} {scale:11s} llama_total={b['total_llama']:8.3f} "
                  f"qwen_total={b['total_qwen']:8.3f} l>q {b['llama_larger']:2d} q>l {b['qwen_larger']:2d} "
                  f"k_inf={b['k_informative']:2d} p={b['p_value']:.4e} floor={b['attainable_p_floor']:.2e} "
                  f"-> {verdict}")
    print(f"[tsc] -> {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
