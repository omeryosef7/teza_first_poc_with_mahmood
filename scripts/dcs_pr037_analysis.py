#!/usr/bin/env python3
"""DCS-PR-037 analyzer — is K* the CODEWORD's row, or the readout template's CONCEPT-OPTION word?

FROZEN BEFORE ITS DATA, per §30 of
`external_md/DCS_BOMBNESS_SPECIFICITY_AND_CAUSAL_VALIDATION_PLAN_AND_PROGRESS_20260905.md`.
Every threshold below is fixed by §30.5/§30.6. Changing one requires a `C-xxx` correction in that
log, not an edit here.

THE BINDING CONSTRAINT (§30.3). Independence unit is DOMAIN, n = 6. A two-sided sign test on 6
domains has attainable floor 2/2^6 = 0.03125, so ANY Holm family with m >= 2 could not clear
alpha = 0.05 even if every domain moved the same way. This analyzer therefore performs EXACTLY ONE
significance test -- the K=9 -> K=10 paired increment -- and reports everything else descriptively
with NO p-value. That is not a stylistic choice; a second corrected test would be uninformative by
construction, and printing one would invite reading it as evidence.
"""
from __future__ import annotations

import argparse, glob, json, os, sys
from math import comb

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                "src", "boombness"))

# ---------------------------------------------------------------- preregistered constants (§30)
EXPECT_N = 168
EXPECT_DOMAINS = 6
ALPHA = 0.05
RUNGS = (5, 6, 9, 10)
REF_TAG = "ref"                 # query_prefill_only -- the 100% normaliser
KO1_TAG = "ko1"                 # target_surface_row_only -- KO-1 run on this template
CODEWORD_RUNG = 10              # ' button' enters here (verified 168/168, §30.2)
MATCHED_CONTROL_RUNG = 9        # ' actually' -- all trailing content EXCEPT the codeword
BIG = 0.5                       # §30.6 CODEWORD-ROW magnitude bar, x |delta_ref|
SMALL = 0.2                     # §30.6 NOT-THE-CODEWORD magnitude bar, x |delta_ref|
MIN_REF_MAGNITUDE = 1.0         # §30.6 VOID/CANNOT-ANSWER: too small to normalise against
BASE_TAG = "base"               # PR-037a §33.3: unintervened baseline replaces the infeasible ctrl
SCAFFOLD_CONTROL_RUNG = 5       # PR-037a §33.3: same 2754 keys, 180 rows, ALL chat scaffold
SCAFFOLD_VOID_FRAC = 0.2        # PR-037a §33.3 VOID: |delta_K5| >= 0.2*|delta_ref| => masking per se


def sign_test_two_sided(vals):
    """Exact two-sided sign test on nonzero values. Returns (p, n_neg, n_pos, n_used, floor)."""
    v = [x for x in vals if x != 0]
    n = len(v)
    if n == 0:
        return None, 0, 0, 0, None
    neg = sum(1 for x in v if x < 0)
    pos = n - neg
    k = min(neg, pos)
    tail = sum(comb(n, i) for i in range(0, k + 1))
    p = min(1.0, 2.0 * tail / (2 ** n))
    floor = min(1.0, 2.0 / (2 ** n))
    return p, neg, pos, n, floor


def find_arm(root, tag, skipped=None):
    """Newest COMPLETE arm dir for `tag` (C-051: completeness is part of the selection)."""
    hits = sorted(glob.glob(os.path.join(root, f"dcssow_{tag}_*")))
    for h in reversed(hits):
        if os.path.exists(os.path.join(h, "DONE.json")):
            if skipped is not None and hits and h != hits[-1]:
                skipped[tag] = [os.path.basename(x) for x in hits if x != h]
            return h
    if skipped is not None and hits:
        skipped[tag] = ["NO COMPLETE ARM: " + os.path.basename(x) for x in hits]
    return None


def load_arm(d):
    p = os.path.join(d, "results.jsonl")
    if not os.path.exists(p):
        return None
    return [json.loads(l) for l in open(p)]


def contract(rows, name):
    """Checks read BEFORE any delta. A failing arm is VOID, not reinterpreted (§30.6)."""
    out = dict(arm=name, n_rows=len(rows), n_domains=len({r["domain"] for r in rows}))
    out["keys_masked_median"] = float(np.median([r.get("hook_n_keys_masked", 0) for r in rows]))
    out["query_rows_edited_median"] = float(np.median(
        [r.get("hook_n_query_rows_edited", 0) for r in rows]))
    out["liveness_violations"] = int(sum(int(r.get("hook_liveness_violations", 0) or 0)
                                         for r in rows))
    out["decode_edits_max"] = int(max([r.get("hook_n_decode_edits", 0) or 0 for r in rows] or [0]))
    om = [r["option_mass"] for r in rows if "option_mass" in r]
    out["option_mass_median"] = float(np.median(om)) if om else None
    # per-domain row counts, so a NON-UNIFORM domain loss (§30.6 VOID) is visible not averaged away
    per = {}
    for r in rows:
        per[r["domain"]] = per.get(r["domain"], 0) + 1
    out["rows_per_domain"] = per
    out["uniform_domains"] = bool(len(set(per.values())) == 1)
    out["ok_n"] = bool(len(rows) == EXPECT_N)
    out["ok_domains"] = bool(out["n_domains"] == EXPECT_DOMAINS)
    out["ok_liveness"] = bool(out["liveness_violations"] == 0 and out["decode_edits_max"] == 0)
    return out


def per_domain_delta(demo, ctrl):
    """Paired per-domain mean of semantic_logodds(demo) - semantic_logodds(control).

    Pairing is on DOMAIN, the declared independence unit. Domains present in only one arm are
    excluded and reported -- never silently dropped, and never averaged as if paired.
    """
    def by_dom(rows):
        acc = {}
        for r in rows:
            v = r.get("semantic_logodds")
            if v is None:
                continue
            acc.setdefault(r["domain"], []).append(float(v))
        return {d: float(np.mean(v)) for d, v in acc.items()}
    dm, cm = by_dom(demo), by_dom(ctrl)
    shared = sorted(set(dm) & set(cm))
    return {d: dm[d] - cm[d] for d in shared}, dm, cm, sorted(set(dm) ^ set(cm))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="outputs/boombness/score_behavior")
    ap.add_argument("--out", default="outputs/boombness/dcs_analysis/dcs_pr037.json")
    a = ap.parse_args()

    res = dict(preregistration="DCS-PR-037 (§30)", alpha=ALPHA, expect_n=EXPECT_N,
               independence_unit="domain", n_domains_declared=EXPECT_DOMAINS,
               attainable_p_floor=2.0 / (2 ** EXPECT_DOMAINS),
               holm_family_size=1,
               note="EXACTLY ONE significance test (§30.3/§30.5). All other rungs are descriptive "
                    "with NO p-value: at n=6 domains any family with m>=2 has an attainable "
                    "adjusted floor above alpha and is uninformative by construction.",
               arms={}, contracts={}, void=[], skipped_incomplete={}, deltas={})

    # PR-037a §33.3: the comparator is the UNINTERVENED BASELINE, not a nondemo_matched control,
    # which is infeasible on this bank (B-018: 164/168 rows, match_ratio 0.048 / 0.000).
    bd = find_arm(a.root, f"{BASE_TAG}_demo", res["skipped_incomplete"])
    if not bd:
        res["verdict"] = ("CANNOT ANSWER — the unintervened baseline arm (PR-037a §33.3) is missing, "
                          "so no delta can be formed. This is NOT a null.")
        return _write(res, a.out)
    base_rows = load_arm(bd)
    cB = contract(base_rows, "baseline")
    res["arms"][BASE_TAG] = dict(demo=os.path.basename(bd))
    res["contracts"][BASE_TAG] = dict(baseline=cB)
    if not (cB["ok_n"] and cB["ok_domains"] and cB["uniform_domains"]):
        res["void"].append(dict(arm=BASE_TAG, reasons=["baseline contract failed"]))
        res["verdict"] = "VOID — the baseline arm fails its contract; every delta rests on it."
        return _write(res, a.out)

    tags = [f"k{K}" for K in RUNGS] + [REF_TAG, KO1_TAG]
    for tag in tags:
        dd = find_arm(a.root, f"{tag}_demo", res["skipped_incomplete"])
        if not dd:
            res["arms"][tag] = dict(demo=None, status="MISSING ARM")
            continue
        res["arms"][tag] = dict(demo=os.path.basename(dd))
        demo, ctrl = load_arm(dd), base_rows
        if demo is None:
            res["arms"][tag]["status"] = "UNREADABLE"
            continue
        cD, cC = contract(demo, f"{tag}_demo"), cB
        res["contracts"][tag] = dict(demo=cD, baseline=cC)
        bad = []
        if not (cD["ok_n"] and cC["ok_n"]):
            bad.append(f"n != {EXPECT_N} (demo {cD['n_rows']}, ctrl {cC['n_rows']})")
        if not (cD["ok_domains"] and cC["ok_domains"]):
            bad.append("domain count != 6")
        if not (cD["uniform_domains"] and cC["uniform_domains"]):
            bad.append("NON-UNIFORM domain loss")
        if not (cD["ok_liveness"] and cC["ok_liveness"]):
            bad.append("liveness violation or decode edit")
        # PR-037a §33.2: the increment is valid only because every rung masks the SAME keys.
        # Assert it rather than trusting it -- if two rungs differ in keys_masked, the between-rung
        # difference is no longer a pure "which query rows" contrast and the estimand is broken.
        res.setdefault("_keys_seen", {})[tag] = cD["keys_masked_median"]
        if bad:
            res["void"].append(dict(arm=tag, reasons=bad))
            continue
        delta, dmean, cmean, unpaired = per_domain_delta(demo, ctrl)
        if unpaired:
            res["void"].append(dict(arm=tag, reasons=[f"unpaired domains: {unpaired}"]))
            continue
        res["deltas"][tag] = dict(
            per_domain=delta, n_domains=len(delta),
            mean_delta=float(np.mean(list(delta.values()))),
            demo_mean=float(np.mean(list(dmean.values()))),
            ctrl_mean=float(np.mean(list(cmean.values()))),
            option_mass_demo=cD["option_mass_median"], option_mass_baseline=cC["option_mass_median"],
            query_rows_edited=cD["query_rows_edited_median"], keys_masked=cD["keys_masked_median"])

    # PR-037a §33.2: every rung must mask the SAME demonstration keys, or the increment is not a
    # pure query-row contrast. This is the assumption the amendment rests on; it is checked, not assumed.
    ks = res.pop("_keys_seen", {})
    res["keys_masked_by_arm"] = ks
    if ks and len(set(ks.values())) != 1:
        res["verdict"] = (f"VOID — rungs do not mask the same keys ({ks}); the between-rung "
                          f"increment is not a pure query-row contrast (PR-037a §33.2).")
        return _write(res, a.out)

    # ---------------- the 100% normaliser
    ref = res["deltas"].get(REF_TAG, {}).get("mean_delta")
    res["reference_delta_prefill"] = ref
    if ref is None:
        res["verdict"] = ("CANNOT ANSWER — the query_prefill_only reference arm is missing or VOID, "
                          "so no rung can be normalised. This is NOT a null.")
        return _write(res, a.out)
    if abs(ref) < MIN_REF_MAGNITUDE:
        res["verdict"] = (f"CANNOT ANSWER — |delta_prefill| = {abs(ref):.4f} < {MIN_REF_MAGNITUDE}: "
                          f"the full-query intervention barely moves this readout, so there is no "
                          f"effect to localise (§30.6). This is NOT a null.")
        return _write(res, a.out)

    for tag, d in res["deltas"].items():
        d["pct_of_reference"] = 100.0 * abs(d["mean_delta"]) / abs(ref)

    # ---------------- PR-037a §33.3: the scaffold negative control, now a VOID condition
    d5 = res["deltas"].get(f"k{SCAFFOLD_CONTROL_RUNG}")
    if d5 is not None:
        frac5 = abs(d5["mean_delta"]) / abs(ref)
        res["scaffold_control_K5"] = dict(mean_delta=d5["mean_delta"], frac_of_reference=frac5,
                                          bar=SCAFFOLD_VOID_FRAC, passes=bool(frac5 < SCAFFOLD_VOID_FRAC))
        if frac5 >= SCAFFOLD_VOID_FRAC:
            res["verdict"] = (
                f"VOID — the K=5 scaffold control moves the readout by {frac5:.1%} of "
                f"|delta_ref| (bar {SCAFFOLD_VOID_FRAC:.0%}). K=5 masks the same 2754 keys at rows "
                f"that are ALL chat scaffold, so masking per se moves this readout and no "
                f"between-rung comparison here is interpretable (PR-037a §33.3).")
            return _write(res, a.out)
    else:
        res["scaffold_control_K5"] = "MISSING — the PR-037a §33.3 negative control was not run"

    # ---------------- THE SINGLE PRIMARY (§30.5): the K=9 -> K=10 paired increment
    d9 = res["deltas"].get(f"k{MATCHED_CONTROL_RUNG}")
    d10 = res["deltas"].get(f"k{CODEWORD_RUNG}")
    if not d9 or not d10:
        res["verdict"] = ("CANNOT ANSWER — the K=9 and/or K=10 arm is missing or VOID, so the "
                          "single preregistered primary cannot be computed. This is NOT a null.")
        return _write(res, a.out)

    doms = sorted(set(d9["per_domain"]) & set(d10["per_domain"]))
    inc = {d: d10["per_domain"][d] - d9["per_domain"][d] for d in doms}
    p, neg, pos, n_used, floor = sign_test_two_sided(list(inc.values()))
    mag = abs(d10["mean_delta"]) - abs(d9["mean_delta"])
    res["primary"] = dict(
        estimand="per-domain inc(d) = delta_K10(d) - delta_K9(d); the codeword row's own increment",
        per_domain=inc, n_domains=len(doms), mean_inc=float(np.mean(list(inc.values()))),
        n_negative=neg, n_positive=pos, n_nonzero=n_used,
        sign_test_p=p, attainable_floor=floor,
        magnitude_gain=mag, magnitude_gain_frac_of_reference=mag / abs(ref),
        bar_big=BIG, bar_small=SMALL)

    sig = (p is not None and p <= ALPHA)
    all_neg = (neg == len(doms) and len(doms) == EXPECT_DOMAINS)
    frac = mag / abs(ref)

    if sig and all_neg and frac >= BIG:
        res["verdict"] = (
            f"CODEWORD-ROW — the codeword's own query row carries the effect "
            f"(inc negative in {neg}/{len(doms)} domains, p={p:.4f}; magnitude gain "
            f"{frac:.1%} of |delta_prefill| >= {BIG:.0%}). ⛔ This CONTRADICTS KO-1 (R-005/R-006) "
            f"and R-082, and per §30.6 it must be RECONCILED with them, not quietly replace them.")
    elif (not sig) and frac < SMALL:
        res["verdict"] = (
            f"NOT-THE-CODEWORD — the codeword's own query row does not carry the effect "
            f"(inc {neg}/{len(doms)} negative, p={p if p is None else round(p,4)}; magnitude gain "
            f"{frac:.1%} of |delta_prefill| < {SMALL:.0%}). KO-1 is CONFIRMED within-template, and "
            f"R-081's K*=7 is attributed to the forced-choice template's CONCEPT-OPTION word.")
    else:
        res["verdict"] = (
            f"CANNOT ANSWER — sign test p={p if p is None else round(p,4)} "
            f"({neg}/{len(doms)} negative) with magnitude gain {frac:.1%} of |delta_prefill|, "
            f"which falls between the {SMALL:.0%} and {BIG:.0%} bars. ⛔ This is NOT a null.")
    return _write(res, a.out)


def _write(res, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w"), indent=1, default=str)
    print(f"[write] {out}\n")
    ref = res.get("reference_delta_prefill")
    if res.get("void"):
        print("VOID ARMS:")
        for v in res["void"]:
            print(f"  {v['arm']}: {v['reasons']}")
        print()
    sc = res.get("scaffold_control_K5")
    if isinstance(sc, dict):
        print(f"K=5 scaffold control: delta={sc['mean_delta']:+.4f} = {sc['frac_of_reference']:.1%} "
              f"of |delta_ref|  bar={sc['bar']:.0%}  -> {'PASS' if sc['passes'] else 'VOID'}\n")
    print(f"{'arm':>6} {'mean_delta':>11} {'%of ref':>8} {'q_rows':>8} {'keys':>7} {'opt_mass':>9}")
    order = [f"k{K}" for K in RUNGS] + [KO1_TAG, REF_TAG]
    for tag in order:
        d = res["deltas"].get(tag)
        if not d:
            print(f"{tag:>6}   -- missing/VOID --")
            continue
        pct = d.get("pct_of_reference")
        print(f"{tag:>6} {d['mean_delta']:>11.4f} {('%.1f%%' % pct) if pct is not None else '  n/a':>8} "
              f"{d['query_rows_edited']:>8.0f} {d['keys_masked']:>7.0f} {d['option_mass_demo']:>9.4f}")
    pr = res.get("primary")
    if pr:
        print(f"\nPRIMARY (the ONLY significance test, §30.5): inc = delta_K10 - delta_K9")
        print(f"  per-domain: " + ", ".join(f"{d}={v:+.4f}" for d, v in sorted(pr['per_domain'].items())))
        print(f"  mean inc = {pr['mean_inc']:+.4f}   negative in {pr['n_negative']}/{pr['n_domains']}"
              f"   sign-test p = {pr['sign_test_p']}   (attainable floor {pr['attainable_floor']})")
        print(f"  magnitude gain |d10|-|d9| = {pr['magnitude_gain']:+.4f} "
              f"= {pr['magnitude_gain_frac_of_reference']:.1%} of |delta_prefill| ({ref:.4f})")
    print(f"\nVERDICT: {res['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
