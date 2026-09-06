#!/usr/bin/env python3
"""DCS-PR-041 — gate R3 (lexical transfer), implemented as §6.8(3) actually specifies it.

FROZEN BEFORE ITS DATA, per §60. `C-064` §57.2 established that the frozen analyzer's
`P2_basket_lexical_transfer` trains AND tests on basket, so it is not a transfer at all. This runs
the declared instrument instead — TRAIN ON BUTTON, TEST ON BASKET — in a separate file, because the
published analyzer must not be edited (brief §33).

⛔ ONE significance test (§60.3): held-out basket accuracy vs chance, exact two-sided sign test over
the 6 shared domains. At n = 6 the floor is 2/2⁶ = 0.03125, so m ≥ 2 is uninformative by construction.

REUSE: the population builder, the §28.1 exclusion, the cache loader, `select`, `fit` and the bank
binding are all imported from `dcs_verify_pr035_primary.py` — the reimplementation that verified
`R-086`. The probe is therefore demonstrably the same one, applied across codewords.
"""
from __future__ import annotations

import argparse, hashlib, json, os, sys
from math import comb

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dcs_verify_pr035_primary as vp          # noqa: E402

CLASSES = vp.CLASSES
N_DOMAINS = 6
ALPHA = 0.05
CHANCE = 1.0 / len(CLASSES)
R086 = 0.7485380116959064                       # the button result this transfer is measured against
BIG = CHANCE + 0.50 * (R086 - CHANCE)           # §60.4  -> 0.5409
SMALL = CHANCE + 0.20 * (R086 - CHANCE)         # §60.4  -> 0.4164
EXPECT_PER_CLASS = 228


def sign_test_two_sided(vals):
    v = [x for x in vals if x != 0]
    n = len(v)
    if n == 0:
        return None, 0, 0, 0, None
    neg = sum(1 for x in v if x < 0)
    pos = n - neg
    k = min(neg, pos)
    return (min(1.0, 2.0 * sum(comb(n, i) for i in range(k + 1)) / (2 ** n)),
            neg, pos, n, min(1.0, 2.0 / (2 ** n)))


def load(codeword, cells, res, tag):
    """Populations for one codeword, with per-class bank binding asserted (prompt_id collides)."""
    saved, out, layers_ref = vp.CODEWORD, {}, None
    vp.CODEWORD = codeword
    try:
        for cc in CLASSES:
            run = vp.find_run(cc)
            if run is None:
                res["void"].append(f"{tag}/{cc}: no complete run")
                continue
            meta_p = os.path.join(run, "metadata.json")
            want = hashlib.sha256(open(vp.bank_path(cc), "rb").read()).hexdigest()[:16]
            if os.path.exists(meta_p):
                got = json.load(open(meta_p)).get("bank_file_sha16")
                if got != want:
                    res["void"].append(f"{tag}/{cc}: bank_file_sha16 {got} != {want}")
                    continue
            else:
                res["void"].append(f"{tag}/{cc}: no metadata.json; bank unverifiable")
                continue
            layers, reps = vp.load_cache(run)
            layers_ref = layers_ref or layers
            if layers != layers_ref:
                res["void"].append(f"{tag}/{cc}: layers differ")
                continue
            out[cc] = vp.attach(vp.build(cc, cells, vp.NEXAMPLES), layers, reps, cc)
            res.setdefault("runs", {})[f"{tag}/{cc}"] = os.path.basename(run)
            res.setdefault("n_rows", {})[f"{tag}/{cc}"] = len(out[cc])
    finally:
        vp.CODEWORD = saved
    return out, layers_ref


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs/boombness/dcs_analysis/dcs_pr041.json")
    a = ap.parse_args()

    res = dict(preregistration="DCS-PR-041 (§60)", alpha=ALPHA, chance=CHANCE,
               independence_unit="domain", n_domains_declared=N_DOMAINS, holm_family_size=1,
               attainable_p_floor=2.0 / (2 ** N_DOMAINS), bar_big=BIG, bar_small=SMALL,
               note="TRAIN on button cell C, TEST on basket cell C, selection on button cell B. "
                    "The frozen analyzer's P2_basket_lexical_transfer trains AND tests on basket "
                    "and is not this instrument (C-064 §57.2).",
               void=[])

    btn_C, layers = load("button", ("C",), res, "button_C")
    btn_B, l2 = load("button", ("B",), res, "button_B")
    bsk_C, l3 = load("basket", ("C",), res, "basket_C")
    if res["void"]:
        res["verdict"] = "VOID — " + "; ".join(res["void"])
        return _write(res, a.out)
    if not (layers == l2 == l3):
        res["verdict"] = f"VOID — layer lists differ: {layers} / {l2} / {l3}"
        return _write(res, a.out)
    for cc in CLASSES:
        for nm, pool in (("button_C", btn_C), ("basket_C", bsk_C)):
            if len(pool.get(cc, [])) != EXPECT_PER_CLASS:
                res["void"].append(f"{nm}/{cc}: {len(pool.get(cc, []))} rows != {EXPECT_PER_CLASS}")
    if res["void"]:
        res["verdict"] = "VOID — " + "; ".join(res["void"])
        return _write(res, a.out)

    TRAIN = [r for c in CLASSES for r in btn_C[c]]
    SEL = [r for c in CLASSES for r in btn_B[c]]
    TEST = [r for c in CLASSES for r in bsk_C[c]]

    # ⛔ leave-one-DOMAIN-out ACROSS codewords: train on button domains != d, test on basket domain d.
    # That removes the shared-domain channel as well as the shared-codeword one (§60.2).
    per, picks = {}, {}
    for d in sorted({r["domain"] for r in TEST}):
        tr = [r for r in TRAIN if r["domain"] != d]
        te = [r for r in TEST if r["domain"] == d]
        sel = [r for r in SEL if r["domain"] != d]
        if not tr or not te or not sel:
            continue
        pick = vp.select(sel, layers, CLASSES)
        if pick is None:
            continue
        L, C = pick
        acc = vp.fit(tr, te, L, layers, C, CLASSES)
        if acc is not None:
            per[d] = acc
            picks[d] = dict(layer=int(L), C=float(C))

    if not per:
        res["verdict"] = "VOID — no fold produced an accuracy."
        return _write(res, a.out)
    mean = float(np.mean(list(per.values())))
    p, neg, pos, n_used, floor = sign_test_two_sided([v - CHANCE for v in per.values()])
    res["transfer"] = dict(per_domain=per, picks=picks, n_domains=len(per), mean_acc=mean,
                           n_above_chance=pos, sign_test_p=p, attainable_floor=floor,
                           button_reference_R086=R086)

    sig = (p is not None and p <= ALPHA)
    all_above = (pos == len(per) and len(per) == N_DOMAINS)
    if sig and all_above and mean >= BIG:
        res["verdict"] = (f"R3-PASS — the concept signal transfers across the codeword: "
                          f"{mean:.4f} on basket, above chance in {pos}/{len(per)} domains "
                          f"(p={p:.4f}), bar {BIG:.4f}. Button reference {R086:.4f}.")
    elif (not sig) and mean < SMALL:
        res["verdict"] = (f"R3-FAIL — the signal does NOT transfer: {mean:.4f}, "
                          f"{pos}/{len(per)} domains, p={p}, below the {SMALL:.4f} bar.")
    else:
        res["verdict"] = (f"CANNOT ANSWER — {mean:.4f}, {pos}/{len(per)} domains, p={p}, between "
                          f"the {SMALL:.4f} and {BIG:.4f} bars. NOT a null.")
    return _write(res, a.out)


def _write(res, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w"), indent=1, default=str)
    print(f"[write] {out}\n")
    for v in res.get("void", []):
        print(f"  VOID: {v}")
    t = res.get("transfer")
    if t:
        print("GATE R3 — train on BUTTON cell C, test on BASKET cell C (§60.2)")
        print("  " + ", ".join(f"{d}={v:.4f}" for d, v in sorted(t["per_domain"].items())))
        print(f"  mean = {t['mean_acc']:.4f}   chance {CHANCE:.4f}   above chance in "
              f"{t['n_above_chance']}/{t['n_domains']}   sign-test p = {t['sign_test_p']} "
              f"(floor {t['attainable_floor']})")
        print(f"  bars: PASS >= {BIG:.4f}   FAIL < {SMALL:.4f}   button reference {R086:.4f}")
    print(f"\nVERDICT: {res['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
