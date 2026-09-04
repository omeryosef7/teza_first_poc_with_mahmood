#!/usr/bin/env python
"""dcs_audit_r041.py -- ADVERSARIAL audit of `DCS-R-041`, the session's headline.

`A-006` audited the INSTRUMENT (midranks vs scipy, null calibration, mutants). Nobody has tried to
break the CLAIM. This phase gives its headlines an adversarial pass (`A-001`, `A-002`, `A-004`);
`R-041` has not had one.

THE CLAIM UNDER ATTACK. Per-domain baseline INSTALLATION predicts the size of the demo_all knockout's
effect on cell C, net of a dose-matched non-demonstration control:
    rho_KO = -0.594, rho_ctrl = +0.312, contrast = -0.907, permutation p = 2.0e-04 (38 domains).

FIVE ATTACKS, ALL DECLARED HERE BEFORE ANY OF THEM RUNS, and ALL reported whatever they show --
including the ones that damage the finding. An audit that only reports the checks that passed is
worse than no audit.

  A  LEAVE-ONE-DOMAIN-OUT. Recompute the contrast on all 38 subsets of size 37. If one domain can
     flip the sign or destroy significance, the result rests on that domain and must say so.
  B  ALTERNATIVE INSTALLATION MEASURES. Installation is defined by ARGMAX == concept. That choice
     was mine. Two alternatives that a reviewer would ask for: (i) p_concept > 0.5 per row,
     (ii) the continuous mean p_concept. If rho flips or collapses under a reasonable alternative,
     the finding is an artifact of the operationalisation.
  C  THE CEILING. 25 of 38 domains sit at installation == 1.0. Drop them: does the contrast survive
     on the 13 domains that actually vary? This is the attack I most expect to land, because a
     predictor that is constant on 2/3 of the sample is carried by the remaining third.
  D  THE CONTROL'S POSITIVE GRADIENT. rho_ctrl = +0.312 (p = 0.058) is marginally significant in
     the OPPOSITE direction, and I have never explained why a dose-matched control should show ANY
     installation gradient. If it is real and systematic, the contrast is a difference of two
     effects rather than an effect minus a nuisance.
  E  A HARSHER NULL. The permutation test shuffles installation. Also shuffle the KO/control LABEL
     within each domain -- a null under which the two arms are exchangeable. The contrast should
     die there; if it does not, the statistic responds to something other than the arm.

Stdlib + a tokenizer. Reuses `dcs_installation_gradient.py` for load/installation/rank/permutation
rather than re-implementing any of it.
"""
from __future__ import annotations
import argparse, glob, importlib.util, json, math, os, random, statistics as st, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = "DCS_AUDIT_R041/1"
SEED = 20260904


def load_gradient_module():
    spec = importlib.util.spec_from_file_location(
        "g", os.path.join(ROOT, "scripts", "dcs_installation_gradient.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def pick(tag: str) -> str:
    ds = [d for d in glob.glob(os.path.join(ROOT, "outputs/boombness/score_behavior", tag + "_*"))
          if os.path.isfile(os.path.join(d, "DONE.json"))]
    if not ds:
        sys.exit(f"REFUSING: no completed run dir for {tag}")
    return sorted(ds)[-1]


def contrast_on(g, inst, d_ko, d_ct, doms):
    x = [inst[d] for d in doms]
    if len(set(x)) < 2:
        return None
    c, p, _ = g.contrast_perm(x, [d_ko[d] for d in doms], [d_ct[d] for d in doms],
                              seed=SEED, n_perm=20000)
    rk, _, _ = g.spearman_perm(x, [d_ko[d] for d in doms], seed=SEED, n_perm=20000)
    rc, _, _ = g.spearman_perm(x, [d_ct[d] for d in doms], seed=SEED, n_perm=20000)
    return {"n": len(doms), "rho_ko": rk, "rho_ctrl": rc, "contrast": c, "perm_p": p}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default="dcsro_C_baseline")
    ap.add_argument("--knockout", default="dcsro_C_qpo_demo")
    ap.add_argument("--control", default="dcsro_C_qpo_ctrl_d1")
    ap.add_argument("--concept-token", default="bomb")
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--tag", default="dcs_audit_r041")
    ap.add_argument("--out", default=os.path.join(ROOT, "outputs/boombness/dcs_analysis"))
    a = ap.parse_args()

    g = load_gradient_module()
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(a.model)

    base, ko, ct = g.load(pick(a.baseline)), g.load(pick(a.knockout)), g.load(pick(a.control))
    needle = a.concept_token.strip().lower()

    # three installation operationalisations; (i) is R-041's
    inst_argmax = g.installation(base, tok, needle)

    def per_domain_mean(rows, f):
        acc = {}
        for r in rows.values():
            acc.setdefault(r["domain"], []).append(f(r))
        return {k: st.mean(v) for k, v in acc.items()}

    inst_p50 = per_domain_mean(base, lambda r: 1.0 if r["p_concept"] > 0.5 else 0.0)
    inst_cont = per_domain_mean(base, lambda r: r["p_concept"])

    d_ko = g.paired_delta(ko, base, "knockout")
    d_ct = g.paired_delta(ct, base, "control")
    doms = sorted(set(inst_argmax) & set(d_ko) & set(d_ct))

    out = {"schema": SCHEMA, "claim": "R-041: installation predicts the knockout's effect size",
           "arms": {"baseline": a.baseline, "knockout": a.knockout, "control": a.control},
           "headline": contrast_on(g, inst_argmax, d_ko, d_ct, doms)}
    print("=== R-041 as published ===")
    h = out["headline"]
    print(f"  n={h['n']}  rho_ko={h['rho_ko']:+.3f}  rho_ctrl={h['rho_ctrl']:+.3f}  "
          f"contrast={h['contrast']:+.3f}  p={h['perm_p']:.5f}")

    # ---- A: leave-one-domain-out ----
    loo = {}
    for drop in doms:
        r = contrast_on(g, inst_argmax, d_ko, d_ct, [d for d in doms if d != drop])
        if r:
            loo[drop] = r
    cs = {k: v["contrast"] for k, v in loo.items()}
    ps = {k: v["perm_p"] for k, v in loo.items()}
    worst_c = max(cs, key=lambda k: cs[k])
    worst_p = max(ps, key=lambda k: ps[k])
    out["A_leave_one_out"] = {
        "n_subsets": len(loo), "contrast_min": min(cs.values()), "contrast_max": max(cs.values()),
        "worst_domain_by_contrast": worst_c, "worst_contrast": cs[worst_c],
        "worst_domain_by_p": worst_p, "worst_p": ps[worst_p],
        "any_sign_flip": bool(max(cs.values()) >= 0),
        "any_loses_alpha": bool(max(ps.values()) >= 0.05)}
    A = out["A_leave_one_out"]
    print(f"\nA  leave-one-out ({A['n_subsets']} subsets): contrast in "
          f"[{A['contrast_min']:+.3f}, {A['contrast_max']:+.3f}]  worst p={A['worst_p']:.5f} "
          f"(drop {A['worst_domain_by_p']})  sign flip={A['any_sign_flip']}  "
          f"loses alpha={A['any_loses_alpha']}")

    # ---- B: alternative installation measures ----
    out["B_alt_measures"] = {}
    print("\nB  alternative installation measures")
    for name, inst in (("argmax==concept (R-041)", inst_argmax),
                       ("p_concept>0.5", inst_p50),
                       ("mean p_concept (continuous)", inst_cont)):
        r = contrast_on(g, inst, d_ko, d_ct, doms)
        out["B_alt_measures"][name] = r
        print(f"   {name:30s} rho_ko={r['rho_ko']:+.3f} rho_ctrl={r['rho_ctrl']:+.3f} "
              f"contrast={r['contrast']:+.3f} p={r['perm_p']:.5f}")

    # ---- C: the ceiling ----
    nonceil = [d for d in doms if inst_argmax[d] < 1.0]
    r = contrast_on(g, inst_argmax, d_ko, d_ct, nonceil)
    out["C_ceiling"] = {"n_at_ceiling": len(doms) - len(nonceil),
                        "n_below_ceiling": len(nonceil), "result": r}
    print(f"\nC  ceiling: {len(doms)-len(nonceil)} of {len(doms)} domains at installation==1.0; "
          f"on the {len(nonceil)} that vary:")
    print(f"   {'' :30s} rho_ko={r['rho_ko']:+.3f} rho_ctrl={r['rho_ctrl']:+.3f} "
          f"contrast={r['contrast']:+.3f} p={r['perm_p']:.5f}" if r else "   DEGENERATE")

    # ---- D: the control's own gradient ----
    ctrl_loo = sorted(v["rho_ctrl"] for v in loo.values())
    out["D_control_gradient"] = {
        "rho_ctrl_full": h["rho_ctrl"],
        "rho_ctrl_loo_min": ctrl_loo[0], "rho_ctrl_loo_max": ctrl_loo[-1],
        "always_positive": bool(ctrl_loo[0] > 0)}
    D = out["D_control_gradient"]
    print(f"\nD  control gradient: rho_ctrl={D['rho_ctrl_full']:+.3f}, LOO range "
          f"[{D['rho_ctrl_loo_min']:+.3f}, {D['rho_ctrl_loo_max']:+.3f}], "
          f"always positive={D['always_positive']}")

    # ---- E: a harsher null -- swap the arm label within each domain ----
    rnd = random.Random(SEED)
    x = [inst_argmax[d] for d in doms]
    obs = h["contrast"]
    hits = 0
    N = 20000
    for _ in range(N):
        yk, yc = [], []
        for d in doms:
            if rnd.random() < 0.5:
                yk.append(d_ko[d]); yc.append(d_ct[d])
            else:
                yk.append(d_ct[d]); yc.append(d_ko[d])
        rx = g._rank(x)
        stat = g.pearson(rx, g._rank(yk)) - g.pearson(rx, g._rank(yc))
        if abs(stat) >= abs(obs) - 1e-12:
            hits += 1
    out["E_arm_exchangeable_null"] = {"n_perm": N, "p": (hits + 1) / (N + 1),
                                      "WHAT": "swaps the KO/control label within each domain; the "
                                              "contrast must die under arm exchangeability"}
    print(f"\nE  arm-exchangeable null ({N} draws): p = {out['E_arm_exchangeable_null']['p']:.5f}")

    os.makedirs(a.out, exist_ok=True)
    dst = os.path.join(a.out, f"{a.tag}.json")
    json.dump(out, open(dst, "w"), indent=2, sort_keys=True)
    print(f"\n-> {dst}")


if __name__ == "__main__":
    main()
