"""
43_transplant_mediation.py — NEXT_CAUSAL_SPRINT §Stage 2 (PRIMARY). CPU-only.

Turn the run_replace (34 --mode replace) transplant rows into the primary State x
Receiver-Context mediation decomposition. The 2x3 table is {Neutral, DS} receiver x
{h_N, h_DS, h_Direct} source, realized by six arms emitted by run_replace:

    receiver \\ source   h_N                    h_DS               h_Direct
    Neutral             Neutral_from_Neutral   Neutral_from_DS    Neutral_from_Direct
    DS                  DS_from_Neutral        DS_from_DS         DS_from_Direct

The two DIAGONAL self-transplant arms (Neutral_from_Neutral, DS_from_DS) are the
correct baselines: they route h through the SAME mode='replace' machinery as the
off-diagonal cells, so an estimand differences out the transplant machinery itself.
(The alpha=0 `identity` arm is used ONLY to validate that a self-transplant reproduces
the no-patch baseline — the faithfulness check.)

Pairing:
  * within-receiver estimands pair on the full item key
        (split, demo_style, n_demos, readout, group)
  * cross-receiver estimands (DE_context, TE, INT) pair the Neutral and DS versions of
    the SAME item on that same key. This is valid iff the matched Neutral/DS prompts
    share (split, demo_style, n_demos, readout) — i.e. the Stage-1 matched-pair design.
    Coverage (n pairs) is reported for EVERY estimand; a thin estimand (<MIN_N) is
    flagged, never silently averaged.

Estimands (metric Y defaults to p_concept = P(BOMB); also runs p_codeword and the
BOMB-vs-CARROT log-odds via --metric):

    PORT_Direct = Y(Neutral, h_Direct) - Y(Neutral, h_N)     # H1 positive control (large)
    IE_state    = Y(Neutral, h_DS)     - Y(Neutral, h_N)     # H2 local-state portability (small?)
    DE_context  = Y(DS, h_N)           - Y(Neutral, h_N)     # context effect, neutral local state
    RESID_ctx   = Y(DS, h_DS)          - Y(DS, h_N)          # H3 context keeps concept w/ neutral state
    INT         = [Y(DS,h_DS)-Y(DS,h_N)] - [Y(Neu,h_DS)-Y(Neu,h_N)]   # state x context interaction
    TE          = Y(DS, h_DS)          - Y(Neutral, h_N)     # total matched Doublespeak effect

Each estimand: paired-bootstrap CI (stats.paired_bootstrap_ci), paired permutation p,
paired Cohen's d; Holm correction over the estimand x window family. Inertness-style
estimands (IE_state) also get an EQUIVALENCE verdict against --equiv-margin.

Usage:
  python 43_transplant_mediation.py --interv-dir outputs/pair_interv_replace_... \\
      --out outputs/transplant_mediation.json [--metric p_concept|p_codeword|logodds] \\
      [--equiv-margin 0.05]
"""
import os
import sys
import json
import math
import argparse
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stats as st

N_BOOT, SEED, MIN_N = 10000, 0, 8

RECEIVER_ARMS = {
    ("Neutral", "h_N"): "Neutral_from_Neutral",
    ("Neutral", "h_DS"): "Neutral_from_DS",
    ("Neutral", "h_Direct"): "Neutral_from_Direct",
    ("DS", "h_N"): "DS_from_Neutral",
    ("DS", "h_DS"): "DS_from_DS",
    ("DS", "h_Direct"): "DS_from_Direct",
}

# (name, minuend arm, subtrahend arm). INT is handled specially (difference of diffs).
ESTIMANDS = [
    ("PORT_Direct", "Neutral_from_Direct", "Neutral_from_Neutral"),
    ("IE_state",    "Neutral_from_DS",     "Neutral_from_Neutral"),
    ("DE_context",  "DS_from_Neutral",     "Neutral_from_Neutral"),
    ("RESID_ctx",   "DS_from_DS",          "DS_from_Neutral"),
    ("TE",          "DS_from_DS",          "Neutral_from_Neutral"),
]
INERT_LIKE = {"IE_state"}          # estimands where the scientific claim is "≈ 0"


def item_key(r):
    return (r["split"], r.get("demo_style"), r.get("n_demos"), r.get("readout"),
            str(r.get("group")))


def metric_value(r, metric):
    if metric == "logodds":
        pc, pk = r.get("p_concept"), r.get("p_codeword")
        if pc is None or pk is None:
            return None
        eps = 1e-6
        return math.log(min(max(pc, eps), 1 - eps)) - math.log(min(max(pk, eps), 1 - eps))
    return r.get(metric)


def load_rows(dirs):
    rows = []
    for d in dirs:
        p = os.path.join(d, "interv_raw.jsonl")
        if not os.path.exists(p):
            print(f"[mediation] WARNING no interv_raw.jsonl in {d}")
            continue
        for line in open(p):
            rows.append(json.loads(line))
    return rows


def paired(a_map, b_map):
    """Paired arrays over the shared item keys, deterministically ordered."""
    keys = sorted(set(a_map) & set(b_map))
    x = [a_map[k] for k in keys]
    y = [b_map[k] for k in keys]
    return x, y, keys


def ci_block(x, y):
    d = st.paired_bootstrap_ci(x, y, n_boot=N_BOOT, seed=SEED)
    out = {"n": d["n"], "effect": round(d["mean_diff"], 5),
           "lo": round(d["lo"], 5), "hi": round(d["hi"], 5),
           "ci_reliable": d["ci_reliable"], "degenerate": d["degenerate"]}
    if d["n"] >= 2:
        out["p_raw"] = round(st.permutation_test_paired(x, y, n_perm=2000, seed=SEED)["p"], 6)
        out["cohens_d"] = round(st.paired_cohens_d(x, y), 4)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interv-dir", action="append", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--metric", default="p_concept",
                    choices=["p_concept", "p_codeword", "logodds"])
    ap.add_argument("--equiv-margin", type=float, default=0.05,
                    help="equivalence margin for inert-like estimands (plan §9)")
    ap.add_argument("--alpha-level", type=float, default=0.05)
    args = ap.parse_args()

    rows = load_rows(args.interv_dir)
    if not rows:
        raise SystemExit("no rows")

    # arm -> group -> {item_key -> metric value}   (identity kept separately)
    arm_vals = defaultdict(lambda: defaultdict(dict))
    ident = defaultdict(dict)          # (receiver_condition) -> {sid -> value} for faithfulness
    groups = set()
    for r in rows:
        v = metric_value(r, args.metric)
        if v is None:
            continue
        g = str(r.get("group"))
        if r["arm"] == "identity":
            ident[r["condition"]][r["sid"]] = v
            continue
        arm_vals[r["arm"]][g][item_key(r)] = v
        if r["arm"] in RECEIVER_ARMS.values():
            groups.add(g)
    groups = sorted(g for g in groups if g != "none")

    # ------------------------------------------------------------------ #
    # 1. 2x3 table of mean metric per (receiver, source, window)
    # ------------------------------------------------------------------ #
    table = {}
    for (recv, src), arm in RECEIVER_ARMS.items():
        for g in groups:
            vals = list(arm_vals.get(arm, {}).get(g, {}).values())
            if vals:
                table[f"{recv}|{src}|{g}"] = {
                    "arm": arm, "n": len(vals), "mean": round(float(np.mean(vals)), 5)}

    # ------------------------------------------------------------------ #
    # 2. estimands per window, paired
    # ------------------------------------------------------------------ #
    est = {}
    pgrid = []                          # (key) for Holm
    for g in groups:
        for name, a, b in ESTIMANDS:
            am, bm = arm_vals.get(a, {}).get(g, {}), arm_vals.get(b, {}).get(g, {})
            x, y, keys = paired(am, bm)
            if len(x) < 2:
                est[f"{name}|{g}"] = {"estimand": name, "window": g, "n": len(x),
                                      "insufficient": True}
                continue
            blk = ci_block(x, y)
            blk.update({"estimand": name, "window": g, "thin": bool(blk["n"] < MIN_N)})
            if name in INERT_LIKE:
                m = args.equiv_margin
                blk["equiv_margin"] = m
                blk["within_equivalence"] = bool(blk["lo"] > -m and blk["hi"] < m)
            est[f"{name}|{g}"] = blk
            if "p_raw" in blk:
                pgrid.append(f"{name}|{g}")

        # INT: difference of within-receiver diffs, per shared item
        keysets = [arm_vals.get(RECEIVER_ARMS[k], {}).get(g, {}) for k in
                   [("DS", "h_DS"), ("DS", "h_N"), ("Neutral", "h_DS"), ("Neutral", "h_N")]]
        shared = sorted(set.intersection(*[set(m) for m in keysets])) if all(keysets) else []
        if len(shared) >= 2:
            ds_dds, ds_dn, nu_dds, nu_dn = keysets
            int_items = [(ds_dds[k] - ds_dn[k]) - (nu_dds[k] - nu_dn[k]) for k in shared]
            zeros = [0.0] * len(int_items)
            blk = ci_block(int_items, zeros)
            blk.update({"estimand": "INT", "window": g, "thin": bool(blk["n"] < MIN_N)})
            est[f"INT|{g}"] = blk
            if "p_raw" in blk:
                pgrid.append(f"INT|{g}")
        else:
            est[f"INT|{g}"] = {"estimand": "INT", "window": g,
                               "n": len(shared), "insufficient": True}

    # Holm over the estimand x window family
    if pgrid:
        adj = st.holm_bonferroni([est[k]["p_raw"] for k in sorted(pgrid)])
        for k, pa in zip(sorted(pgrid), adj):
            est[k]["p_holm"] = round(float(pa), 6)
            est[k]["significant_corrected"] = bool(pa < args.alpha_level)

    # ------------------------------------------------------------------ #
    # 3. faithfulness: self-transplant vs identity (should be ~0), paired on sid
    # ------------------------------------------------------------------ #
    faith = {}
    for recv_cond, arm in [("NEUTRAL_CODEWORD", "Neutral_from_Neutral"),
                           ("DOUBLESPEAK", "DS_from_DS")]:
        # pair self-transplant value against identity value for the SAME sid+group
        xs, ys = [], []
        for r in rows:
            if r["arm"] != arm:
                continue
            v = metric_value(r, args.metric)
            b = ident.get(recv_cond, {}).get(r["sid"])
            if v is None or b is None:
                continue
            xs.append(v); ys.append(b)
        if len(xs) >= 2:
            blk = ci_block(xs, ys)
            blk["faithful"] = bool(abs(blk["effect"]) < 0.02 and abs(blk["lo"]) < 0.05
                                   and abs(blk["hi"]) < 0.05)
            faith[arm] = blk
        else:
            faith[arm] = {"n": len(xs), "insufficient": True}

    # ------------------------------------------------------------------ #
    # 4. verdicts (directional, artifact-backed; the JSON is the source of truth)
    # ------------------------------------------------------------------ #
    def eff(name, g):
        e = est.get(f"{name}|{g}")
        return e.get("effect") if e and "effect" in e else None

    verdicts = {}
    for g in groups:
        port, ie = eff("PORT_Direct", g), eff("IE_state", g)
        de, resid, te, it = (eff("DE_context", g), eff("RESID_ctx", g),
                             eff("TE", g), eff("INT", g))
        verdicts[g] = {
            "H1_direct_portable": (port is not None and port >= 0.05),
            "H2_ds_state_less_portable": (port is not None and ie is not None
                                          and ie < port and abs(ie) < 0.05),
            "H4_context_or_interaction_dominant": (de is not None and ie is not None
                                                   and abs(de) > abs(ie)),
            "effects": {"PORT_Direct": port, "IE_state": ie, "DE_context": de,
                        "RESID_ctx": resid, "INT": it, "TE": te},
        }

    out = {
        "plan": "NEXT_CAUSAL_SPRINT §Stage 2 (State x Receiver-Context transplant)",
        "interv_dirs": [os.path.abspath(d) for d in args.interv_dir],
        "metric": args.metric, "equiv_margin": args.equiv_margin,
        "windows": groups, "min_n_for_confirmatory": MIN_N,
        "table_2x3": table, "estimands": est, "faithfulness": faith,
        "verdicts": verdicts, "n_rows": len(rows),
        "status": "COMPLETE",
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    json.dump(out, open(args.out, "w"), indent=1)

    # console summary (numbers only, plan §5.12)
    print(f"[mediation] metric={args.metric} rows={len(rows)} windows={groups} -> {args.out}")
    for arm, f in faith.items():
        if "effect" in f:
            print(f"  faithful[{arm}]: self-transplant-vs-identity={f['effect']:+.4f} "
                  f"[{f['lo']:+.4f},{f['hi']:+.4f}] faithful={f.get('faithful')}")
    for g in groups:
        print(f"  --- window {g} ---")
        for name in ("PORT_Direct", "IE_state", "DE_context", "RESID_ctx", "INT", "TE"):
            e = est.get(f"{name}|{g}", {})
            if "effect" in e:
                extra = ""
                if name in INERT_LIKE:
                    extra = f" equiv={e.get('within_equivalence')}"
                sig = e.get("significant_corrected")
                print(f"    {name:12} eff={e['effect']:+.4f} [{e['lo']:+.4f},{e['hi']:+.4f}] "
                      f"n={e['n']}{' THIN' if e.get('thin') else ''} "
                      f"sig_holm={sig}{extra}")
            elif e.get("insufficient"):
                print(f"    {name:12} INSUFFICIENT (n={e.get('n', 0)})")


if __name__ == "__main__":
    main()
