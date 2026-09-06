#!/usr/bin/env python3
"""DCS-PR-040 analyzer (PHASE 5, gate R5) — does the demonstration→query knockout destroy the
CONCEPT-IDENTITY signal that `R-086` established?

FROZEN BEFORE ITS DATA, per §55 (`PR-040`) and §58 (`PR-040a`) of
`external_md/DCS_BOMBNESS_SPECIFICITY_AND_CAUSAL_VALIDATION_PLAN_AND_PROGRESS_20260905.md`.

`PR-040a` §58.3 is the load-bearing amendment: the primary compares **bridge to bridge**
(`ko_off` vs `ko_on`), never bridge against the published extractor cache, so the ~1.4 % bf16 /
kernel offset between code paths CANCELS instead of masquerading as an effect. The published cache
is used ONLY for the §55.7 reproduction check, which the bridge already passed (§58.2).

⛔ ONE significance test (§55.3). At n = 6 domains the two-sided sign-test floor is 2/2⁶ = 0.03125,
so ANY Holm family with m ≥ 2 is UNINFORMATIVE BY CONSTRUCTION. The §55.5 "re-based" secondary
therefore carries NO p-value and is read on magnitude only.

REUSE: the population builder, the §28.1 exclusion, the cache loader and the whole probe procedure
are IMPORTED from `dcs_verify_pr035_primary.py` — the independent reimplementation that verified
`R-086` (`A-029`). Nothing here re-derives them, so the probe applied to knocked-out states is
demonstrably the same probe that produced 0.7485 on baseline states.
"""
from __future__ import annotations

import argparse, glob, hashlib, json, os, sys
from math import comb

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dcs_verify_pr035_primary as vp          # noqa: E402  (reuse; do NOT re-derive)

CLASSES = vp.CLASSES                            # ("bomb","knife","gun")
CODEWORD = vp.CODEWORD
N_DOMAINS = 6
ALPHA = 0.05
CHANCE = 1.0 / len(CLASSES)
BIG, SMALL = 0.50, 0.20                         # §55.4 bars, as FRACTIONS of the measured drop
KO_ROOT = "outputs/boombness/extract_boombness"


def sign_test_two_sided(vals):
    v = [x for x in vals if x != 0]
    n = len(v)
    if n == 0:
        return None, 0, 0, 0, None
    neg = sum(1 for x in v if x < 0)
    pos = n - neg
    k = min(neg, pos)
    p = min(1.0, 2.0 * sum(comb(n, i) for i in range(k + 1)) / (2 ** n))
    return p, neg, pos, n, min(1.0, 2.0 / (2 ** n))


def find_ko_run(state, cc):
    """Newest COMPLETE koextract run. ⛔ ABORTED.json means the bridge's liveness gate fired and the
    cache is half-knocked-out; such a run is refused, never silently skipped."""
    hits = sorted(glob.glob(os.path.join(KO_ROOT, f"koextract_{state}_{CODEWORD}_{cc}_*")))
    aborted = [h for h in hits if os.path.exists(os.path.join(h, "ABORTED.json"))]
    for h in reversed(hits):
        if os.path.exists(os.path.join(h, "DONE.json")):
            return h, aborted
    return None, aborted


def load_state(state, res):
    """Populations for one knockout state, with per-class bank binding asserted."""
    pools, sel, layers_ref = {}, {}, None
    for cc in CLASSES:
        run, aborted = find_ko_run(state, cc)
        res.setdefault("aborted_runs", {})[f"{state}/{cc}"] = [os.path.basename(a) for a in aborted]
        if run is None:
            res["void"].append(f"{state}/{cc}: no DONE.json run"
                               + (f" (ABORTED present: {aborted})" if aborted else ""))
            continue
        res.setdefault("runs", {})[f"{state}/{cc}"] = os.path.basename(run)
        # ⛔ bank binding. prompt_id collides 8-way across banks (§28.3), and find_ko_run resolves by
        # DIRECTORY NAME, so the name alone must never be trusted to say which bank a cache holds.
        mp = os.path.join(run, "metadata.json")
        if not os.path.exists(mp):
            res["void"].append(f"{state}/{cc}: no metadata.json; bank cannot be verified")
            continue
        meta = json.load(open(mp))
        want = hashlib.sha256(open(vp.bank_path(cc), "rb").read()).hexdigest()[:16]
        if meta.get("bank_file_sha16") != want:
            res["void"].append(f"{state}/{cc}: bank_file_sha16 {meta.get('bank_file_sha16')} != {want}")
            continue
        layers, reps = vp.load_cache(run)
        if layers_ref is None:
            layers_ref = layers
        elif layers != layers_ref:
            res["void"].append(f"{state}/{cc}: layers {layers} != {layers_ref}")
            continue
        pools[cc] = vp.attach(vp.build(cc, ("C",), vp.NEXAMPLES), layers, reps, cc)
        sel[cc] = vp.attach(vp.build(cc, ("B",), vp.NEXAMPLES), layers, reps, cc)
        res.setdefault("n_rows", {})[f"{state}/{cc}"] = dict(C=len(pools[cc]), B=len(sel[cc]))
    return pools, sel, layers_ref


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs/boombness/dcs_analysis/dcs_pr040.json")
    a = ap.parse_args()

    res = dict(preregistration="DCS-PR-040 + PR-040a (§55, §58)", alpha=ALPHA,
               independence_unit="domain", n_domains_declared=N_DOMAINS, holm_family_size=1,
               attainable_p_floor=2.0 / (2 ** N_DOMAINS), chance=CHANCE,
               note="PR-040a: primary is bridge-to-bridge (ko_off vs ko_on); the published extractor "
                    "cache is NOT used here. ONE significance test; the re-based secondary has no p.",
               void=[])

    off_pools, off_sel, layers = load_state("off", res)
    on_pools, on_sel, layers_on = load_state("on", res)
    if res["void"]:
        res["verdict"] = "VOID — " + "; ".join(res["void"])
        return _write(res, a.out)
    if layers != layers_on:
        res["verdict"] = f"VOID — layer lists differ between states: {layers} vs {layers_on}"
        return _write(res, a.out)

    C_off = [r for c in CLASSES for r in off_pools[c]]
    B_off = [r for c in CLASSES for r in off_sel[c]]
    C_on = [r for c in CLASSES for r in on_pools[c]]
    B_on = [r for c in CLASSES for r in on_sel[c]]

    # ---- BASELINE ANCHOR, measured on ko_off (PR-040a §58.3): the probe procedure is vp's, i.e.
    # PR-035's -- selection on cell B, leave-one-domain-out, no layer chosen on the test cell.
    per_off, picks_off = vp.loo(C_off, B_off, layers, CLASSES)
    acc_off = float(np.mean(list(per_off.values()))) if per_off else None
    res["baseline_ko_off"] = dict(per_domain=per_off, mean_acc=acc_off,
                                  picks={d: dict(layer=int(L), C=float(C)) for d, (L, C) in picks_off.items()},
                                  published_R086=0.7485380116959064)
    if acc_off is None:
        res["verdict"] = "VOID — the ko_off baseline produced no accuracy."
        return _write(res, a.out)
    # §58.3: if ko_off does not itself reproduce R-086, that is a finding about the BRIDGE.
    res["baseline_ko_off"]["abs_diff_vs_R086"] = abs(acc_off - 0.7485380116959064)
    if abs(acc_off - 0.7485380116959064) > 0.10:
        res["verdict"] = (f"VOID — the ko_off baseline is {acc_off:.4f}, more than 0.10 from R-086's "
                          f"0.7485. The bridge does not reproduce the published probe result on "
                          f"un-knocked states, so no R5 conclusion may be drawn from it (§58.3).")
        return _write(res, a.out)

    # ---- THE SINGLE PRIMARY: same probe, tested on KNOCKED-OUT cell C.
    # Train on ko_off cell C (the baseline manifold) and test on ko_on cell C, per fold.
    per_on = {}
    for d in sorted({r["domain"] for r in C_on}):
        tr = [r for r in C_off if r["domain"] != d]
        te = [r for r in C_on if r["domain"] == d]
        if d not in picks_off or not tr or not te:
            continue
        L, C = picks_off[d]
        acc = vp.fit(tr, te, L, layers, C, CLASSES)
        if acc is not None:
            per_on[d] = acc
    acc_on = float(np.mean(list(per_on.values()))) if per_on else None
    res["knockout_ko_on"] = dict(per_domain=per_on, mean_acc=acc_on)
    if acc_on is None:
        res["verdict"] = "VOID — the ko_on arm produced no accuracy."
        return _write(res, a.out)

    doms = sorted(set(per_off) & set(per_on))
    drop = {d: per_off[d] - per_on[d] for d in doms}
    p, neg, pos, n_used, floor = sign_test_two_sided(list(drop.values()))
    avail = acc_off - CHANCE
    frac = (acc_off - acc_on) / avail if avail > 0 else None
    res["primary"] = dict(
        estimand="drop(d) = acc(ko_off, d) - acc(ko_on, d); the probe is PR-035's, unchanged",
        per_domain=drop, n_domains=len(doms), mean_drop=float(np.mean(list(drop.values()))),
        n_positive=pos, n_negative=neg, sign_test_p=p, attainable_floor=floor,
        available_drop=avail, frac_of_available=frac, bar_big=BIG, bar_small=SMALL)

    # ---- §55.5 MANDATORY SECONDARY, no p-value: is the information GONE, or merely RE-BASED?
    per_onon, _ = vp.loo(C_on, B_on, layers, CLASSES)
    acc_onon = float(np.mean(list(per_onon.values()))) if per_onon else None
    res["rebased_secondary_no_p"] = dict(
        per_domain=per_onon, mean_acc=acc_onon,
        note="§55.5: train on KNOCKED-OUT, test on KNOCKED-OUT. If this ALSO collapses the concept "
             "information is GONE; if it still classifies, the information is PRESENT BUT RE-BASED "
             "and R5-PASS may NOT be reported as destroying the representation.")

    sig = (p is not None and p <= ALPHA)
    all_pos = (pos == len(doms) and len(doms) == N_DOMAINS)
    if sig and all_pos and frac is not None and frac >= BIG:
        res["verdict"] = (f"R5-PASS — the knockout destroys the concept signal: drop positive in "
                          f"{pos}/{len(doms)} domains (p={p:.4f}), {frac:.1%} of the available drop "
                          f"(bar {BIG:.0%}). {acc_off:.4f} -> {acc_on:.4f} against chance {CHANCE:.4f}.")
    elif (not sig) and frac is not None and frac < SMALL:
        res["verdict"] = (f"R5-FAIL — the concept signal SURVIVES the knockout: {pos}/{len(doms)} "
                          f"domains, p={p}, only {frac:.1%} of the available drop (bar {SMALL:.0%}). "
                          f"{acc_off:.4f} -> {acc_on:.4f}.")
    else:
        res["verdict"] = (f"CANNOT ANSWER — p={p} ({pos}/{len(doms)} positive), "
                          f"{frac if frac is None else format(frac, '.1%')} of the available drop, "
                          f"between the {SMALL:.0%} and {BIG:.0%} bars. NOT a null.")
    return _write(res, a.out)


def _write(res, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w"), indent=1, default=str)
    print(f"[write] {out}\n")
    for v in res.get("void", []):
        print(f"  VOID: {v}")
    ab = {k: v for k, v in (res.get("aborted_runs") or {}).items() if v}
    if ab:
        print(f"  ABORTED runs present (bridge liveness gate fired): {ab}")
    b, k = res.get("baseline_ko_off"), res.get("knockout_ko_on")
    if b and b.get("mean_acc") is not None:
        print(f"BASELINE ko_off : {b['mean_acc']:.4f}   (R-086 published 0.7485, "
              f"|diff| {b.get('abs_diff_vs_R086', float('nan')):.4f})   chance {CHANCE:.4f}")
    if k and k.get("mean_acc") is not None:
        print(f"KNOCKOUT ko_on  : {k['mean_acc']:.4f}")
    pr = res.get("primary")
    if pr:
        print("\nPRIMARY (the ONLY significance test, §55.3): drop = ko_off - ko_on, per domain")
        print("  " + ", ".join(f"{d}={v:+.3f}" for d, v in sorted(pr["per_domain"].items())))
        print(f"  mean drop = {pr['mean_drop']:+.4f}   positive in {pr['n_positive']}/{pr['n_domains']}"
              f"   sign-test p = {pr['sign_test_p']}   (floor {pr['attainable_floor']})")
        print(f"  = {pr['frac_of_available']:.1%} of the available drop ({pr['available_drop']:.4f})")
    sec = res.get("rebased_secondary_no_p")
    if sec and sec.get("mean_acc") is not None:
        print(f"\nSECONDARY (no p, §55.5) train-on-KO / test-on-KO: {sec['mean_acc']:.4f}"
              f"   -> {'information GONE' if sec['mean_acc'] < 0.45 else 'information PRESENT BUT RE-BASED'}")
    print(f"\nVERDICT: {res['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
