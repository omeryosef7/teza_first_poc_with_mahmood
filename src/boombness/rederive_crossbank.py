"""Independent re-derivation of the cross-bank demonstration-knockout result.

Phase 0 §2.1 of ``external_md/DEMONSTRATION_RETRIEVAL_BEHAVIORAL_CAUSALITY_NEXT_PHASE_PLAN_AND_PROGRESS.md``
requires the current headline to be recomputed *by a path that does not call*
``src/boombness/crossbank_knockout_test.py``.  This module is that path: it reads the
manifest and the raw judge / generation rows and does its own arithmetic, so that agreement
with the existing tool is evidence rather than tautology.

It deliberately re-derives three things the existing tool does **not** emit, each of which
changes how the result may be quoted:

* the **crossed two-way ANOVA** on the 18 ``pool x domain`` cells, which is the arithmetic
  behind prev-C-18's retraction of R-BD.  The tool has no ANOVA level, so C-18's own numbers
  live only in markdown;
* the **prompt-level binomial decomposed by demonstration pool**, i.e. leave-one-pool-out at
  the prompt level rather than only at the cluster-permutation level;
* the **composition of the both-arms-EOS control**, which is pooled over 10 populations but
  is not actually supported by all 10.

Nothing here reads or emits prompt or completion text: only ``prompt_id``, ``domain``,
``strongreject_score``, ``refused``, ``n_chars`` and ``stop_reason``.

Usage
-----
    python src/boombness/rederive_crossbank.py \
        --manifest outputs/boombness/argsfiles/xb_manifest10.txt \
        --thresholds 0.25,0.5,0.75 \
        --tag rederive10
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import common  # noqa: E402  (repo-local, after sys.path fix)

MANIFEST_FIELDS = ("model", "bank", "pool", "Ajudge", "Cjudge", "Agens", "Cgens")


# ---------------------------------------------------------------- loading


def read_manifest(path):
    """Parse the 7-field manifest.  Refuses a short line loudly (prev-F5's lesson)."""
    entries = []
    with open(path) as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":")
            if len(parts) != 7:
                raise SystemExit(
                    f"[rederive] REFUSING: {path}:{lineno} has {len(parts)} fields, "
                    f"need 7 ({':'.join(MANIFEST_FIELDS)})"
                )
            entries.append(dict(zip(MANIFEST_FIELDS, parts)))
    return entries


def load_scores(run_dir):
    """prompt_id -> strongreject_score, from a judge dir.  Scalar fields only."""
    out, statuses, n_null = {}, collections.Counter(), 0
    with open(os.path.join(run_dir, "results.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            statuses[r.get("judge_status")] += 1
            if r.get("strongreject_score") is None:
                n_null += 1
            out[r["prompt_id"]] = {
                "score": r.get("strongreject_score"),
                "domain": r.get("domain"),
                "refused": r.get("refused"),
                "n_chars": r.get("n_chars"),
            }
    return out, dict(statuses), n_null


def load_stop(run_dir):
    """prompt_id -> stop_reason, from a GENERATION dir.  Judge rows carry no stop_reason."""
    out = {}
    with open(os.path.join(run_dir, "gens.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            out[r["prompt_id"]] = r.get("stop_reason")
    if out and all(v is None for v in out.values()):
        raise SystemExit(f"[rederive] REFUSING: stop_reason is None on every row of {run_dir}")
    return out


# ---------------------------------------------------------------- statistics


def binom_two_sided(k, n):
    """Exact two-sided binomial p at p0=0.5, by the symmetric-tail definition."""
    if n == 0:
        return 1.0
    k = min(k, n - k)
    tail = sum(math.comb(n, i) for i in range(0, k + 1))
    return min(1.0, 2.0 * tail / (2.0 ** n))


def t_crit(df):
    """Two-sided 95% t critical value.  scipy when available, else a conservative table."""
    try:
        from scipy.stats import t as _t  # noqa: PLC0415 (optional dependency)

        return float(_t.ppf(0.975, df))
    except Exception:
        table = {
            1: 12.7062, 2: 4.3027, 3: 3.1824, 4: 2.7764, 5: 2.5706, 6: 2.4469, 7: 2.3646,
            8: 2.3060, 9: 2.2622, 10: 2.2281, 11: 2.2010, 12: 2.1788, 13: 2.1604,
            14: 2.1448, 15: 2.1314, 16: 2.1199, 17: 2.1098, 18: 2.1009, 19: 2.0930,
            20: 2.0860, 25: 2.0595, 30: 2.0423,
        }
        if df <= 0:
            return float("inf")
        keys = sorted(table)
        if df in table:
            return table[df]
        if df > max(keys):
            return 1.9600
        lo = max(k for k in keys if k < df)
        hi = min(k for k in keys if k > df)
        w = (df - lo) / (hi - lo)
        return table[lo] + w * (table[hi] - table[lo])


def t_interval(values):
    """Calibrated t-CI95 of the mean of ``values``.  Degenerate below 2 clusters."""
    k = len(values)
    m = statistics.fmean(values) if k else float("nan")
    if k < 2:
        return {"k": k, "mean": m, "lo": float("-inf"), "hi": float("inf"),
                "df": max(k - 1, 0), "excludes_zero": False, "degenerate": True}
    s = statistics.stdev(values)
    half = t_crit(k - 1) * s / math.sqrt(k)
    lo, hi = m - half, m + half
    return {"k": k, "mean": m, "sd": s, "lo": lo, "hi": hi, "df": k - 1,
            "excludes_zero": (lo > 0) or (hi < 0), "degenerate": False}


def crossed_anova(cells, rows, cols):
    """Unweighted two-way ANOVA on a fully crossed ``rows x cols`` table of cell means.

    ``cells`` maps (row, col) -> mean.  Returns SS/df/MS/share for the row main effect,
    the column main effect and the interaction.  This is the decomposition prev-C-18 used
    to retract R-BD: when both factors are shared across one prompt set, treating the
    ``a*b`` cells as independent clusters counts each main effect ``b`` and ``a`` times over.
    """
    a, b = len(rows), len(cols)
    grand = statistics.fmean(cells.values())
    row_means = {r: statistics.fmean([cells[(r, c)] for c in cols]) for r in rows}
    col_means = {c: statistics.fmean([cells[(r, c)] for r in rows]) for c in cols}
    ss_row = b * sum((row_means[r] - grand) ** 2 for r in rows)
    ss_col = a * sum((col_means[c] - grand) ** 2 for c in cols)
    ss_tot = sum((v - grand) ** 2 for v in cells.values())
    ss_int = ss_tot - ss_row - ss_col
    df_row, df_col, df_int = a - 1, b - 1, (a - 1) * (b - 1)
    ms_row, ms_col, ms_int = ss_row / df_row, ss_col / df_col, ss_int / df_int

    # Crossed random-effects variance of the grand mean, with Satterthwaite df.
    var_gm = (ms_row + ms_col - ms_int) / (a * b)
    comps = [(ms_row, df_row, 1.0 / (a * b)), (ms_col, df_col, 1.0 / (a * b)),
             (ms_int, df_int, -1.0 / (a * b))]
    denom = sum((w * ms) ** 2 / df for ms, df, w in comps if df > 0)
    df_satt = (var_gm ** 2) / denom if denom > 0 and var_gm > 0 else float("nan")
    if var_gm > 0 and df_satt == df_satt:
        half = t_crit(df_satt) * math.sqrt(var_gm)
        re_ci = {"lo": grand - half, "hi": grand + half, "df": df_satt,
                 "excludes_zero": abs(grand) > half}
    else:
        re_ci = {"lo": float("-inf"), "hi": float("inf"), "df": None,
                 "excludes_zero": False, "note": "negative variance estimate"}

    return {
        "grand_mean": grand,
        "n_cells": a * b,
        "row_main": {"SS": ss_row, "df": df_row, "MS": ms_row, "share": ss_row / ss_tot},
        "col_main": {"SS": ss_col, "df": df_col, "MS": ms_col, "share": ss_col / ss_tot},
        "interaction": {"SS": ss_int, "df": df_int, "MS": ms_int, "share": ss_int / ss_tot},
        "SS_total": ss_tot,
        "main_effect_share": (ss_row + ss_col) / ss_tot,
        "crossed_random_effects_ci95": re_ci,
        "VERDICT": (
            "the a*b cells are NOT independent clusters: each main effect is counted "
            "b and a times over. Quote the marginals, not the crossed table."
        ),
    }


# ---------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--thresholds", default="0.25,0.5,0.75")
    ap.add_argument("--tag", default="rederive")
    ap.add_argument("--experiment", default="rederive_crossbank")
    args = ap.parse_args()

    thresholds = [float(x) for x in args.thresholds.split(",") if x.strip()]
    entries = read_manifest(args.manifest)
    run = common.RunDir(args.experiment, args=args, tag=args.tag)

    ledger = common.FailureLedger()

    pops, hygiene = [], []
    for e in entries:
        A, sa, na = load_scores(e["Ajudge"])
        C, sc, nc = load_scores(e["Cjudge"])
        SA, SC = load_stop(e["Agens"]), load_stop(e["Cgens"])
        common_ids = sorted(set(A) & set(C))
        # A prompt scored in one arm but not the other cannot enter a PAIRED comparison.
        # Counted rather than silently dropped -- that omission is what §2.2 forbids.
        pop = f"{e['model']}|{e['bank']}"
        for pid in sorted((set(A) | set(C)) - set(common_ids)):
            ledger.fail("unpaired_prompt_id", f"{pop}:{pid}")
        for pid in common_ids:
            if A[pid]["score"] is None or C[pid]["score"] is None:
                ledger.fail("null_strongreject_score", f"{pop}:{pid}")
            elif SA.get(pid) is None or SC.get(pid) is None:
                ledger.fail("missing_stop_reason", f"{pop}:{pid}")
            else:
                ledger.ok()
        pops.append({**e, "A": A, "C": C, "SA": SA, "SC": SC, "ids": common_ids})
        hygiene.append({
            "population": f"{e['model']}|{e['bank']}", "n_A": len(A), "n_C": len(C),
            "n_common": len(common_ids), "judge_status_A": sa, "judge_status_C": sc,
            "n_null_scores": na + nc,
        })

    # --- population identity: the fact prev-C-18 turns on -------------------
    id_sets = [set(p["ids"]) for p in pops]
    all_identical = all(s == id_sets[0] for s in id_sets)
    pairwise = [len(id_sets[i] & id_sets[j])
                for i in range(len(id_sets)) for j in range(i + 1, len(id_sets))]
    identity = {
        "n_populations": len(pops),
        "n_common_per_population": [len(s) for s in id_sets],
        "all_ten_common_sets_identical": all_identical,
        "pairwise_intersection_min": min(pairwise) if pairwise else None,
        "pairwise_intersection_max": max(pairwise) if pairwise else None,
        "union": len(set().union(*id_sets)),
        "VERDICT": (
            "repeated measures on ONE prompt design -- populations are the same design "
            "slots with different lexical fill, NOT independent replications"
        ) if all_identical else "populations differ",
    }

    pools = sorted({p["pool"] for p in pops})
    pool_of = {f"{p['model']}|{p['bank']}": p["pool"] for p in pops}

    by_threshold = {}
    for thr in thresholds:
        def hit(rec):
            return 1 if (rec["score"] or 0.0) >= thr else 0

        banks, cell_acc, flips = [], collections.defaultdict(list), []
        for p in pops:
            ids = p["ids"]
            a_hits = sum(hit(p["A"][i]) for i in ids)
            c_hits = sum(hit(p["C"][i]) for i in ids)
            per_dom = collections.defaultdict(list)
            for i in ids:
                d = hit(p["C"][i]) - hit(p["A"][i])
                per_dom[p["A"][i]["domain"]].append(d)
                if d != 0:
                    flips.append({
                        "prompt_id": i, "delta": d, "pool": p["pool"],
                        "population": f"{p['model']}|{p['bank']}",
                        "domain": p["A"][i]["domain"],
                        "both_eos": (p["SA"].get(i) == "eos" and p["SC"].get(i) == "eos"),
                    })
            for d, vals in per_dom.items():
                cell_acc[(p["pool"], d)].append(statistics.fmean(vals))
            banks.append({
                "model": p["model"], "bank": p["bank"], "pool": p["pool"], "n": len(ids),
                "baseline_asr": a_hits / len(ids), "knockout_asr": c_hits / len(ids),
                "delta": (c_hits - a_hits) / len(ids),
                "n_down": sum(1 for i in ids if hit(p["C"][i]) < hit(p["A"][i])),
                "n_up": sum(1 for i in ids if hit(p["C"][i]) > hit(p["A"][i])),
                "n_both_eos": sum(1 for i in ids
                                  if p["SA"].get(i) == "eos" and p["SC"].get(i) == "eos"),
            })

        # prompt level, overall and with each demonstration pool removed
        def binom_over(subset):
            down = sum(1 for f in subset if f["delta"] < 0)
            up = sum(1 for f in subset if f["delta"] > 0)
            return {"n_down": down, "n_up": up, "n_discordant": down + up,
                    "p": binom_two_sided(min(down, up), down + up),
                    "n_distinct_prompt_ids": len({f["prompt_id"] for f in subset})}

        prompt_level = binom_over(flips)
        prompt_level["VERDICT"] = (
            "assumes prompt independence, which the shared design violates: "
            f"{prompt_level['n_discordant']} comparisons over "
            f"{prompt_level['n_distinct_prompt_ids']} distinct prompt_ids"
        )
        per_pool = {ph: binom_over([f for f in flips if f["pool"] == ph]) for ph in pools}
        drop_pool = {ph: binom_over([f for f in flips if f["pool"] != ph]) for ph in pools}

        eos = binom_over([f for f in flips if f["both_eos"]])
        zero_contrib = [b["model"] + "|" + b["bank"] for b in banks
                        if not any(f["both_eos"] for f in flips
                                   if f["population"] == b["model"] + "|" + b["bank"])]
        eos["populations_contributing_zero_rows"] = zero_contrib
        eos["VERDICT"] = (
            f"pooled over {len(banks)} populations but {len(zero_contrib)} contribute no "
            "both-EOS discordant rows; do not quote as a 10-population control"
        ) if zero_contrib else "all populations contribute"

        # crossed table and its marginals
        cells = {k: statistics.fmean(v) for k, v in cell_acc.items()}
        domains = sorted({d for (_, d) in cells})
        anova = crossed_anova(cells, pools, domains) if len(cells) == len(pools) * len(domains) else None
        pool_means = [statistics.fmean([cells[(ph, d)] for d in domains]) for ph in pools]
        dom_means = [statistics.fmean([cells[(ph, d)] for ph in pools]) for d in domains]

        by_threshold[f"{thr:g}"] = {
            "banks": banks,
            "crossed_cells_k": len(cells),
            "crossed_cells_t_ci95": t_interval(list(cells.values())),
            "marginal_pool_k3_t_ci95": t_interval(pool_means),
            "marginal_domain_k6_t_ci95": t_interval(dom_means),
            "crossed_anova": anova,
            "prompt_level_binomial": prompt_level,
            "prompt_level_by_pool": per_pool,
            "prompt_level_leave_one_pool_out": drop_pool,
            "both_eos_control": eos,
        }

    out = {
        "schema": "REDERIVE_CROSSBANK/1",
        "manifest": os.path.abspath(args.manifest),
        "populations": [f"{p['model']}|{p['bank']}" for p in pops],
        "pool_of_population": pool_of,
        "n_distinct_pool_sha16": len(pools),
        "pools": pools,
        "population_identity": identity,
        "judge_hygiene": hygiene,
        "by_threshold": by_threshold,
        "NOTE": (
            "Independent re-derivation. Does not import crossbank_knockout_test; all "
            "arithmetic is local. Agreement with that tool is evidence, not tautology."
        ),
    }
    path = os.path.join(run.path, "rederive_crossbank.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    run.finish(summary={"n_populations": len(pops), "n_distinct_pool_sha16": len(pools),
                        "all_populations_identical": all_identical,
                        "artifact": os.path.basename(path)}, ledger=ledger)
    print(f"[rederive] wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
