#!/usr/bin/env python
"""dcs_pr014_bound.py -- `DCS-PR-014`'s Qwen behavioural contrast, analysed by BOUNDING.

WRITTEN AND COMMITTED WHILE THE JUDGE WAS STILL RUNNING (arm 5 of 8), so the analysis is fixed
before six of the eight arms have an attack number. `PR-014` itself was frozen earlier still, when
NONE had been judged.

WHY BOUNDING AND NOT COMPARATOR SELECTION (`PR-014`, corrected by `C-023`).
    All 6 Qwen control draws induce refusal (+39 ... +47 on a 150 baseline). There is no
    refusal-neutral Qwen control in this pool, and drawing until one appears is selection on the
    nuisance variable. `C-023` also killed the tolerance-based fix: `refused` is `kw_refusal`,
    deterministic, with a MEASURED judge band of 0 -- there is no noise band to rescale.
    So the confound is not removed by design. It is BOUNDED by analysis.

PRIMARY. Row-paired exact McNemar on `malicious_at_0.5`, KO-3 vs each control, ALL SIX reported.
    McNemar because rows pair 1:1 by `prompt_id` -- the error `C-015` retracted `R-012` for.

THE BOUND. A control with extra refusals shows artificially FEWER attacks, so `KO-3 - control` is
    pulled toward zero and FACE VALUE already UNDERSTATES any reduction. The refusal-adjusted end
    credits the control with its induced refusals as WOULD-BE ATTACKS:
        n_flip = (control_refused - baseline_refused)      # PR-014: "add ALL induced refusals"
    and recomputes. ==> `DCS-C-030`: this end is the FAVOURABLE one, not the hostile one --
    it only ever adds attacks to the CONTROL, so it can only make the reduction look LARGER.
    PR-014 called it "maximally hostile" and that label is WITHDRAWN. The two ends BRACKET the
    effect; the conclusion is carried by the CONSERVATIVE (face-value) end.

    ASSIGNMENT, declared here because `PR-014` fixed the COUNT and not WHICH rows. The count is
    spent MAXIMALLY HOSTILELY: eligible rows are control rows with `refused=1, attack=0`, and they
    are spent FIRST on rows that are DISCORDANT IN KO-3's FAVOUR (KO-3 attacked, control did not),
    because flipping those destroys a discordant pair on KO-3's side and shrinks the contrast
    fastest. Any leftover flips go to concordant rows, which cannot help KO-3 either.
    => The reported bound is the worst case over assignments consistent with PR-014's count,
       not a random or convenient one.

SECONDARY, and declared inferior. Attack rate among non-refused rows is composition-free and
    tempting, and it conditions on a POST-TREATMENT variable -- a collider whose bias direction is
    unknown. Reported, and will not carry a conclusion the bound does not support.

REUSES `scripts/cds_domain_test.py` for `load_arm` and the exact binomial, rather than
re-implementing either. Stdlib only.
"""
from __future__ import annotations
import argparse, collections, importlib.util, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = "DCS_PR014_BOUND/1"
ALPHA = 0.05


def _cds():
    spec = importlib.util.spec_from_file_location(
        "cds", os.path.join(ROOT, "scripts", "cds_domain_test.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def mcnemar(a_rows: dict, b_rows: dict, two_sided) -> dict:
    """Exact McNemar on 1:1 `prompt_id`-paired binary outcomes. `a` = KO-3, `b` = control.
    b_only = rows where the CONTROL attacked and KO-3 did not; a_only = the reverse."""
    ids = sorted(set(a_rows) & set(b_rows))
    a_only = sum(1 for p in ids if a_rows[p]["attack"] and not b_rows[p]["attack"])
    b_only = sum(1 for p in ids if b_rows[p]["attack"] and not a_rows[p]["attack"])
    n_disc = a_only + b_only
    return {"n_paired": len(ids), "ko_attacks": sum(a_rows[p]["attack"] for p in ids),
            "ctrl_attacks": sum(b_rows[p]["attack"] for p in ids),
            "ko_only": a_only, "ctrl_only": b_only, "n_discordant": n_disc,
            "delta_attacks": sum(a_rows[p]["attack"] for p in ids)
                             - sum(b_rows[p]["attack"] for p in ids),
            "mcnemar_p": two_sided(min(a_only, b_only), n_disc) if n_disc else 1.0,
            "attainable_p_floor": two_sided(0, n_disc) if n_disc else 1.0,
            "significant": bool(n_disc and two_sided(min(a_only, b_only), n_disc) < ALPHA)}


def apply_bound(ko: dict, ctrl: dict, n_flip: int) -> tuple[dict, dict]:
    """Spend `n_flip` control non-attacks as would-be attacks, MOST HOSTILE FIRST.

    Eligibility is `refused=1, attack=0` in the control -- only an induced refusal can be argued
    to have concealed an attack. A row that was not refused has no such excuse and is never
    flipped, which is what keeps this a bound on the REFUSAL confound rather than a free gift."""
    eligible = [p for p in sorted(ctrl) if ctrl[p]["refused"] and not ctrl[p]["attack"]]
    hostile = [p for p in eligible if p in ko and ko[p]["attack"]]      # kills a discordant pair
    rest = [p for p in eligible if p not in hostile]
    order = hostile + rest
    flipped = order[:max(0, n_flip)]
    out = {p: dict(r) for p, r in ctrl.items()}
    for p in flipped:
        out[p]["attack"] = 1
    return out, {"n_flip_requested": n_flip, "n_flip_applied": len(flipped),
                 "n_eligible": len(eligible), "n_hostile_available": len(hostile),
                 "SHORTFALL": max(0, n_flip - len(eligible))}


def non_refused_rate(rows: dict) -> dict:
    kept = [r for r in rows.values() if not r["refused"]]
    return {"n_non_refused": len(kept),
            "attack_rate_among_non_refused": (sum(r["attack"] for r in kept) / len(kept))
                                             if kept else None}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True, help="judge dir of the baseline arm")
    ap.add_argument("--knockout", required=True, help="judge dir of the KO-3 arm")
    ap.add_argument("--control", action="append", required=True,
                    help="label=judge_dir; repeat. ALL draws must be passed -- PR-014 reports "
                         "every one, and passing a subset would be the comparator selection the "
                         "whole design exists to avoid")
    ap.add_argument("--expect-rows", type=int, default=380)
    ap.add_argument("--tag", default="dcs_pr014_bound")
    ap.add_argument("--out", default=os.path.join(ROOT, "outputs/boombness/dcs_analysis"))
    a = ap.parse_args()

    cds = _cds()
    two_sided = cds._binom_cdf_two_sided

    def load(d, what):
        if not os.path.isfile(os.path.join(d, "DONE.json")):
            sys.exit(f"REFUSING: {what} ({d}) carries no DONE.json")
        rows = cds.load_arm(d)
        if a.expect_rows and len(rows) != a.expect_rows:
            sys.exit(f"REFUSING {what}: {len(rows)} rows, expected {a.expect_rows}")
        pins = {r["judge_model_used"] for r in rows.values()}
        if len(pins) != 1:
            sys.exit(f"REFUSING {what}: {len(pins)} distinct judge models in one arm: {pins}")
        return rows, pins.pop()

    base, pin_b = load(a.baseline, "baseline")
    ko, pin_k = load(a.knockout, "knockout")
    base_refused = sum(r["refused"] for r in base.values())

    out = {"schema": SCHEMA, "alpha": ALPHA,
           "baseline": {"dir": a.baseline, "refused": base_refused,
                        "attacks": sum(r["attack"] for r in base.values())},
           "knockout": {"dir": a.knockout, "refused": sum(r["refused"] for r in ko.values()),
                        "attacks": sum(r["attack"] for r in ko.values())},
           "judge_models_seen": sorted({pin_b, pin_k}), "controls": {}}

    print(f"baseline  refused={base_refused:4d}  attacks={out['baseline']['attacks']:4d}")
    print(f"KO-3      refused={out['knockout']['refused']:4d}  "
          f"attacks={out['knockout']['attacks']:4d}")
    print()
    for spec in a.control:
        label, _, d = spec.partition("=")
        ctrl, pin_c = load(d, label)
        out["judge_models_seen"] = sorted(set(out["judge_models_seen"]) | {pin_c})
        c_ref = sum(r["refused"] for r in ctrl.values())
        induced = c_ref - base_refused
        bounded, bookkeeping = apply_bound(ko, ctrl, induced)
        entry = {"dir": d, "refused": c_ref, "induced_refusals": induced,
                 "face_value": mcnemar(ko, ctrl, two_sided),
                 "bounded": mcnemar(ko, bounded, two_sided),
                 "bound_bookkeeping": bookkeeping,
                 "SECONDARY_non_refused": {"knockout": non_refused_rate(ko),
                                           "control": non_refused_rate(ctrl),
                                           "WARNING": "conditions on a POST-TREATMENT variable; "
                                                      "collider bias of unknown direction; "
                                                      "PR-014 declares it cannot carry a "
                                                      "conclusion the bound does not support"}}
        out["controls"][label] = entry
        f, b = entry["face_value"], entry["bounded"]
        print(f"{label:22s} refused={c_ref:4d} (induced {induced:+4d})  "
              f"face: KO-ctrl={f['delta_attacks']:+4d} p={f['mcnemar_p']:.4f}"
              f"{' *' if f['significant'] else '  '}   "
              f"bounded: KO-ctrl={b['delta_attacks']:+4d} p={b['mcnemar_p']:.4f}"
              f"{' *' if b['significant'] else ''}"
              + ("   SHORTFALL!" if bookkeeping["SHORTFALL"] else ""))

    # DCS-C-030: PR-014 called the corrected end "maximally hostile". IT IS NOT. The correction
    # only ever ADDS attacks to the CONTROL and never to KO-3, so it can only make `KO - ctrl`
    # MORE negative -- i.e. it makes the reduction look LARGER. The conservative end of the
    # interval is FACE VALUE, and the survival criterion is therefore evaluated there.
    surv = [l for l, e in out["controls"].items()
            if e["face_value"]["delta_attacks"] < 0 and e["face_value"]["significant"]]
    favourable = [l for l, e in out["controls"].items()
                  if e["bounded"]["delta_attacks"] < 0 and e["bounded"]["significant"]]
    out["VERDICT"] = {
        "controls_total": len(out["controls"]),
        "CONSERVATIVE_END_is_face_value": sorted(surv),
        "n_surviving_conservative": len(surv),
        "favourable_end_bounded": sorted(favourable),
        "n_surviving_favourable": len(favourable),
        "DIRECTION_NOTE": ("DCS-C-030. The refusal-adjusted end is the FAVOURABLE end, not the "
                           "hostile one: the control refuses MORE than KO-3, so its raw attack "
                           "count is suppressed, so `KO - ctrl` is already biased TOWARD ZERO and "
                           "face value already understates any reduction. Crediting the control "
                           "with its induced refusals as attacks can only enlarge the reduction. "
                           "=> The two ends BRACKET the effect; the conclusion is carried by the "
                           "conservative (face-value) end, and the bounded end is reported as an "
                           "upper bound on the magnitude, never as robustness."),
        "READING": ("PR-014's declared outcomes: effect survives / face-value effect present but "
                    "the confound is not excluded (report as CONFOUND-LIMITED, NOT as a "
                    "positive) / no face-value effect (Qwen behavioural is a capable null). The "
                    "branch is chosen from these numbers, not softened.")}

    os.makedirs(a.out, exist_ok=True)
    dst = os.path.join(a.out, f"{a.tag}.json")
    json.dump(out, open(dst, "w"), indent=2, sort_keys=True)
    print(f"\nCONSERVATIVE end (face value, negative AND significant): "
          f"{len(surv)} of {len(out['controls'])}  {sorted(surv)}")
    print(f"favourable end (refusal-adjusted): {len(favourable)} of {len(out['controls'])}  "
          f"{sorted(favourable)}   <- C-030: this end is NOT the hostile one")
    print(f"-> {dst}")


if __name__ == "__main__":
    main()
