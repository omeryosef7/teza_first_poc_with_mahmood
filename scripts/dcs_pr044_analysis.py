#!/usr/bin/env python3
"""DCS-PR-044 — gate R6 (KO-1 vs the concept probe) and §13 (the explicit-concept row).

FROZEN BEFORE ITS DATA, per §67. ⛔ BOTH READOUTS ARE DESCRIPTIVE AND CARRY NO p-VALUE: `PR-040`'s
single significance test is spent, and at n = 6 a second corrected test is uninformative by
construction (floor 2/2⁶ = 0.03125, so m ≥ 2 cannot clear α).

The two gates share one arm set because `target_surface_row_only` blocks the row of whatever the
prompt's `target_surface` is, and the capture site follows the same field. Verified in the artifacts:

  cell C  ->  token_text ' button'  (the CODEWORD)          => gate R6
  cell B  ->  token_text ' bomb'    (the EXPLICIT CONCEPT)  => §13

so one knocked-out run per bank yields both, read at the very row it blocked.

SELECTION DISCIPLINE. Each readout picks (layer, C) on a population that is NOT its test set:
  R6  tests cell C  -> selects on cell B   (as PR-035 does)
  §13 tests cell B  -> selects on cell C   (the mirror; selecting on cell B would be the §28.2 defect)

REUSE: population builder, §28.1 exclusion, cache loader, select/fit imported from
`dcs_verify_pr035_primary.py`; run resolution and bank binding follow `dcs_pr040_analysis.py`.
"""
from __future__ import annotations

import argparse, glob, hashlib, json, os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dcs_verify_pr035_primary as vp          # noqa: E402

CLASSES = vp.CLASSES
CODEWORD = vp.CODEWORD
CHANCE = 1.0 / len(CLASSES)
KO_ROOT = "outputs/boombness/extract_boombness"


def find_run(tag, cc, res):
    hits = sorted(glob.glob(os.path.join(KO_ROOT, f"koextract_{tag}_{CODEWORD}_{cc}_*")))
    for h in hits:
        if os.path.exists(os.path.join(h, "ABORTED.json")):
            res["void"].append(f"{tag}/{cc}: an ABORTED run is present ({os.path.basename(h)})")
    for h in reversed(hits):
        if os.path.exists(os.path.join(h, "DONE.json")):
            return h
    return None


def load(tag, cells, res):
    """Populations for one arm + cell set, with per-class bank binding asserted."""
    out, layers_ref = {}, None
    for cc in CLASSES:
        run = find_run(tag, cc, res)
        if run is None:
            res["void"].append(f"{tag}/{cc}: no complete run")
            continue
        meta_p = os.path.join(run, "metadata.json")
        want = hashlib.sha256(open(vp.bank_path(cc), "rb").read()).hexdigest()[:16]
        if not os.path.exists(meta_p) or json.load(open(meta_p)).get("bank_file_sha16") != want:
            res["void"].append(f"{tag}/{cc}: bank binding failed")
            continue
        layers, reps = vp.load_cache(run)
        layers_ref = layers_ref or layers
        if layers != layers_ref:
            res["void"].append(f"{tag}/{cc}: layers differ")
            continue
        out[cc] = vp.attach(vp.build(cc, cells, vp.NEXAMPLES), layers, reps, cc)
        res.setdefault("runs", {})[f"{tag}/{'+'.join(cells)}/{cc}"] = os.path.basename(run)
    return out, layers_ref


def readout(name, train_pool, test_pool, sel_pool, layers, res, what):
    """Train on the ko_off population, test on the knocked-out one, select off a third cell."""
    TR = [r for c in CLASSES for r in train_pool[c]]
    TE = [r for c in CLASSES for r in test_pool[c]]
    SEL = [r for c in CLASSES for r in sel_pool[c]]
    # population identity between the two arms -- an unequal pairing is not a paired comparison
    for cc in CLASSES:
        a = {r["prompt_id"] for r in train_pool[cc]}
        b = {r["prompt_id"] for r in test_pool[cc]}
        if a != b:
            res["void"].append(f"{name}: population differs between arms for {cc} "
                               f"({len(a)} vs {len(b)}, symmetric diff {len(a ^ b)})")
            return None
    base, picks = vp.loo(TR, SEL, layers, CLASSES)
    ko = {}
    for d in sorted({r["domain"] for r in TE}):
        tr = [r for r in TR if r["domain"] != d]
        te = [r for r in TE if r["domain"] == d]
        if d not in picks or not tr or not te:
            continue
        L, C = picks[d]
        acc = vp.fit(tr, te, L, layers, C, CLASSES)
        if acc is not None:
            ko[d] = acc
    if not base or not ko:
        res["void"].append(f"{name}: no fold produced an accuracy")
        return None
    ab, ak = float(np.mean(list(base.values()))), float(np.mean(list(ko.values())))
    doms = sorted(set(base) & set(ko))
    drop = {d: base[d] - ko[d] for d in doms}
    avail = ab - CHANCE
    out = dict(what=what, n_rows_per_class={cc: len(train_pool[cc]) for cc in CLASSES},
               baseline_per_domain=base, knockout_per_domain=ko, drop_per_domain=drop,
               baseline=ab, knockout=ak, mean_drop=float(np.mean(list(drop.values()))),
               n_positive=int(sum(1 for v in drop.values() if v > 0)), n_domains=len(doms),
               frac_of_available=(ab - ak) / avail if avail > 0 else None,
               picks={d: dict(layer=int(L), C=float(C)) for d, (L, C) in picks.items()},
               NOTE="DESCRIPTIVE, NO p-VALUE (§67.3). PR-040's single test is spent and at n=6 a "
                    "second corrected test is uninformative by construction.")
    res[name] = out
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="outputs/boombness/dcs_analysis/dcs_pr044.json")
    a = ap.parse_args()
    res = dict(preregistration="DCS-PR-044 (§67)", chance=CHANCE, independence_unit="domain",
               note="Both readouts DESCRIPTIVE, no p-values. One arm set: target_surface_row_only "
                    "blocks the row the capture site reads -- ' button' in cell C (R6) and ' bomb' "
                    "in cell B (§13).", void=[])

    offC, layers = load("off", ("C",), res)
    offB, l2 = load("off", ("B",), res)
    koC, l3 = load("ko1", ("C",), res)
    koB, l4 = load("ko1", ("B",), res)
    if res["void"]:
        res["verdict"] = "VOID — " + "; ".join(res["void"])
        return _write(res, a.out)
    if not (layers == l2 == l3 == l4):
        res["verdict"] = "VOID — layer lists differ across arms"
        return _write(res, a.out)

    # gate R6 : test cell C (the CODEWORD row was blocked), select on cell B
    readout("R6_codeword_row", offC, koC, offB, layers, res,
            "KO-1: block the CODEWORD's own row from the demonstrations; read at the codeword.")
    # §13   : test cell B (the CONCEPT row was blocked), select on cell C (never the test cell)
    readout("S13_concept_row", offB, koB, offC, layers, res,
            "KO-2: block the EXPLICIT CONCEPT's own row from the demonstrations; read at the concept.")
    if res["void"]:
        res["verdict"] = "VOID — " + "; ".join(res["void"])
    else:
        res["verdict"] = ("REPORTED DESCRIPTIVELY — see the two blocks. No p-value is attached to "
                          "either, by §67.3.")
    return _write(res, a.out)


def _write(res, out):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w"), indent=1, default=str)
    print(f"[write] {out}\n")
    for v in res.get("void", []):
        print(f"  VOID: {v}")
    for name in ("R6_codeword_row", "S13_concept_row"):
        o = res.get(name)
        if not o:
            continue
        print(f"{name} — {o['what']}")
        print(f"  rows/class {o['n_rows_per_class']}")
        print(f"  baseline {o['baseline']:.4f}  ->  knockout {o['knockout']:.4f}   "
              f"chance {CHANCE:.4f}")
        print(f"  mean drop {o['mean_drop']:+.4f}  positive in {o['n_positive']}/{o['n_domains']}"
              f"   = {o['frac_of_available']:.1%} of the available drop")
        print("  per-domain drop: " + ", ".join(f"{d}={v:+.3f}"
                                                for d, v in sorted(o['drop_per_domain'].items())))
        print(f"  ⛔ {o['NOTE']}\n")
    print(f"VERDICT: {res['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
