#!/usr/bin/env python3
"""A12 through the exact sign test, RE-DERIVED — closes C-CONT-093 / trap #8 ("asserted, not run").

A12 (CONT-ENTRY 079/080): the doublespeak remap installs `bomb` far more readily than `knife` or
`gun`, on both codewords. The effect was reported with sign counts (button bomb−knife 89/90, bomb−gun
87/90; basket 88/90, 88/90) and "sign-flip p < 1e-9", but the p-values were ASSERTED — never run
through `dcs_cont_exact_tests.py`, and the counts were carried from the entry, not re-derived
(C-CONT-093; the phase's trap #8 = "asserted counts / no committed artifact").

This re-derives the per-domain concept-installation from the raw one-word/cell-C readout channel
(`lpm.load_installation`, the same concept-free target used everywhere) for all three concepts on
each codeword, counts the domain-level signs itself, and runs the EXACT sign test
(`exact_tests.exact_sign_test`). Independence unit = DOMAIN. TRAIN+VALIDATION only (TEST excluded via
the split). Button and basket never pooled. No model, no GPU, no big cache — reads only the small
readout results.jsonl files.
"""
from __future__ import annotations
import argparse, importlib.util, json, os, statistics, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

READOUTS = {
    "button": {"bomb":  "outputs/boombness/score_behavior/ts116m_readout_button_bomb_20260907_133811_3183103",
               "knife": "outputs/boombness/score_behavior/ts116m_readout_button_knife_20260907_141654_3185383",
               "gun":   "outputs/boombness/score_behavior/ts116m_readout_button_gun_20260907_144944_3187822"},
    "basket": {"bomb":  "outputs/boombness/score_behavior/ts116m_readout_basket_bomb_20260907_152329_3191150",
               "knife": "outputs/boombness/score_behavior/ts116m_readout_basket_knife_20260907_160248_3193990",
               "gun":   "outputs/boombness/score_behavior/ts116m_readout_basket_gun_20260907_164158_3200370"},
}
ASSERTED = {"button": {"bomb_minus_knife": "89/90", "bomb_minus_gun": "87/90"},
            "basket": {"bomb_minus_knife": "88/90", "bomb_minus_gun": "88/90"}}


def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s)
    sys.modules[mod] = m           # dataclass in exact_tests needs the module registered first
    s.loader.exec_module(m); return m


def per_domain_mean(inst, keep):
    """(domain,slot)->p  ==>  domain->mean p over that domain's slots, kept domains only."""
    by = {}
    for (d, _slot), p in inst.items():
        if d in keep:
            by.setdefault(d, []).append(p)
    return {d: statistics.mean(v) for d, v in by.items()}


def signs(a, b):
    """Across domains present in both, count sign(a-b): pos / neg / tied (exact 0)."""
    npos = nneg = ntie = 0
    for d in sorted(set(a) & set(b)):
        diff = a[d] - b[d]
        if diff > 0: npos += 1
        elif diff < 0: nneg += 1
        else: ntie += 1
    return npos, nneg, ntie


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(REPO, "reports/DCS_CONT_A12_EXACT.json"))
    a = ap.parse_args()
    lpm = _load("lpm", "scripts/dcs_cont_layerpos_map.py")
    ex = _load("ex", "scripts/dcs_cont_exact_tests.py")
    assign = lpm.load_split(); EX = set(lpm.EXCLUDED_DOMAINS)
    keep = {d for d, v in assign.items() if v in ("train", "validation")} - EX
    if any(assign.get(d) == "test" for d in keep):
        print("REFUSING: a test domain reached the kept set"); return 2

    out = {"schema": "dcs_cont_a12_exact/1", "claim": "A12: bomb installs more readily than "
           "knife/gun under the doublespeak remap", "unit": "DOMAIN", "population": "train+val (no TEST)",
           "re_derived": True, "note": "per-domain mean concept-installation from the one-word/cellC "
           "channel; exact two-sided sign test; button and basket never pooled", "by_codeword": {}}
    for cw in ("button", "basket"):
        inst = {co: per_domain_mean(lpm.load_installation(os.path.join(REPO, p))[0], keep)
                for co, p in READOUTS[cw].items()}
        res = {}
        for label, (x, y) in {"bomb_minus_knife": (inst["bomb"], inst["knife"]),
                              "bomb_minus_gun": (inst["bomb"], inst["gun"])}.items():
            npos, nneg, ntie = signs(x, y)
            t = ex.exact_sign_test(npos, nneg)
            res[label] = {"n_pos": npos, "n_neg": nneg, "n_tied": ntie,
                          "n_domains": npos + nneg + ntie,
                          "p_two_sided": t["p_two_sided"], "p_exact": t.get("p_exact_fraction"),
                          "asserted_in_079_080": ASSERTED[cw][label]}
            print("[%s] %-16s  %d+/%d-/%d tied of %d  exact p=%.3g  (asserted %s)"
                  % (cw, label, npos, nneg, ntie, npos + nneg + ntie, t["p_two_sided"],
                     ASSERTED[cw][label]))
        out["by_codeword"][cw] = res
    json.dump(out, open(a.out, "w"), indent=1)
    print("wrote %s" % os.path.relpath(a.out, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
