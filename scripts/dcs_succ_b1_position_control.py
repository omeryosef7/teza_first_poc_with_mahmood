#!/usr/bin/env python3
"""Is `B1` LOCALISED at the codeword? Successor plan section 8.

Plan section 8 is explicit that this is "one of the most important pieces", and equally explicit
about the trap: *"Do NOT declare localization because one position has high absolute accuracy.
Localization requires a relative comparison against meaningful nearby and role-matched positions."*
`R-112` is the inherited instance of exactly this — a probe reading 0.9446 at the codeword and
0.9261 nine tokens downstream, which is why the thesis-scale phase could not call its signal
localised.

`B1` has never had that comparison. Everything in `S-002` … `S-007` is read at `codeword_last`.
This computes the SAME construction at two control positions extracted for the purpose:

    codeword_last   rel_end -10   the queried CODEWORD itself      (the treatment site)
    following       rel_end  -9   ' actually'                      the frozen neutral read site,
                                  token-IDENTICAL across all cells, carrying no concept token
    last            rel_end  -1   '\\n\\n', the final prompt token   maximally downstream

Both control positions are token-identical across cells A, C and E, so `v_lex` there is NOT a
token-substitution direction — it is whatever the *prompt-level* difference propagates to that
token. That difference in meaning is the point: if `B1` is as large at a neutral downstream token
as at the codeword, then what `B1` measures is a global prompt state and the word "codeword" does
no work in describing it.

REUSE: the loader, the leave-one-out direction, the unit-normaliser, the sign test and the domain
bootstrap are IMPORTED from `scripts/dcs_succ_bombness_candidates.py`, so this comparison and the
headline number are computed by the same code.

USAGE
  python scripts/dcs_succ_b1_position_control.py
  python scripts/dcs_succ_b1_position_control.py --selftest
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

import dcs_succ_bombness_candidates as CAND   # noqa: E402  -- REUSED, not reimplemented

POSITIONS = [("codeword_last", "ts116m_full", "rel_end -10, the queried CODEWORD"),
             ("following", "ts116m_posfollowing", "rel_end -9, ' actually', token-identical"),
             ("last", "ts116m_poslast", "rel_end -1, the final prompt token")]


def b1_per_domain(bank, tag_prefix, train_domains, torch, rng):
    """-> (per-domain B1 in gap units, meta). Bomb bank only: needs cells A, C, E."""
    old = CAND.TAG_PREFIX
    CAND.TAG_PREFIX = tag_prefix
    try:
        meta, rows, reps = CAND.load_bank(bank, torch, keep_domains=set(train_domains))
    finally:
        CAND.TAG_PREFIX = old
    means, kept, dropped = CAND.domain_cell_means(rows, reps, torch, set(train_domains))
    del reps
    layers = meta["layers"]
    out = {}
    for L_i, L in enumerate(layers):
        dEA = {d: means[("E", d)][L_i] - means[("A", d)][L_i] for d in kept}
        dCA = {d: means[("C", d)][L_i] - means[("A", d)][L_i] for d in kept}
        gap = float(torch.linalg.vector_norm(
            torch.stack([dEA[d] for d in kept]).mean(dim=0)))
        vals = {}
        for d in kept:
            vhat = CAND._unit(CAND.loo_direction(dEA, kept, d, torch), torch)
            vals[d] = float(torch.dot(dCA[d], vhat)) / gap
        out[L] = {"per_domain": vals, "gap_norm": gap}
    return out, {"run": meta["run"], "position": meta["position"], "layers": layers,
                 "n_rows_analysed": meta["n_rows_analysed"], "n_domains": len(kept),
                 "dropped": dropped, "token_text_by_cell": meta["token_text_by_cell"]}


def selftest() -> int:
    ok = True

    def chk(n, c):
        nonlocal ok
        print("  %-46s %s" % (n, "PASS" if c else "FAIL"))
        ok = ok and bool(c)

    chk("imports the candidate module's LOO", callable(CAND.loo_direction))
    chk("imports the candidate module's sign test", callable(CAND.sign_test_two_sided))
    chk("TAG_PREFIX is restored after a swap", CAND.TAG_PREFIX == "ts116m_full")
    p, f = CAND.sign_test_two_sided(67, 67)
    chk("sign test at n=67 hits its floor", abs(p - f) < 1e-30)
    chk("three positions declared", len(POSITIONS) == 3)
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--banks", default="button_bomb,basket_bomb")
    ap.add_argument("--out", default=os.path.join(REPO, "outputs/dcs_succ/b1_position_control.json"))
    ap.add_argument("--seed", type=int, default=20260910)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        print("=== selftest ===")
        return selftest()

    import torch
    torch.set_num_threads(4)
    rng = random.Random(a.seed)

    assign, _ = CAND.split_map()
    train = sorted(d for d, s in assign.items()
                   if s == "train" and d not in CAND.EXCLUDED_DOMAINS)
    res = {"_label": "B1 POSITION CONTROL -- plan section 8. EXPLORATORY, TRAIN ONLY.",
           "n_train_domains": len(train), "positions": {p[0]: p[2] for p in POSITIONS},
           "by_bank": {}}

    for bank in [b.strip() for b in a.banks.split(",") if b.strip()]:
        got, metas = {}, {}
        for name, tag, _desc in POSITIONS:
            try:
                got[name], metas[name] = b1_per_domain(bank, tag, train, torch, rng)
            except CAND.Refusal as e:
                metas[name] = {"REFUSED": str(e)}
                print("[pos] %s %s REFUSED: %s" % (bank, name, e), file=sys.stderr)
        rec = {"meta": metas, "layers": {}}
        common_layers = sorted(set.intersection(*[set(got[n]) for n in got])) if got else []
        for L in common_layers:
            doms = sorted(set.intersection(*[set(got[n][L]["per_domain"]) for n in got]))
            row = {"n_domains": len(doms)}
            for n in got:
                v = [got[n][L]["per_domain"][d] for d in doms]
                row[n] = {"mean_gap_units": CAND.mean(v), "sd": CAND.sd(v),
                          "ci95": CAND.boot_ci(v, rng), "gap_norm": got[n][L]["gap_norm"]}
            # PAIRED contrasts -- the comparison plan section 8 requires
            for ctrl in [n for n in got if n != "codeword_last"]:
                if "codeword_last" not in got:
                    continue
                d = [got["codeword_last"][L]["per_domain"][x] - got[ctrl][L]["per_domain"][x]
                     for x in doms]
                k = sum(1 for x in d if x > 0)
                p, fl = CAND.sign_test_two_sided(k, len(d))
                row["paired_codeword_minus_%s" % ctrl] = {
                    "mean": CAND.mean(d), "ci95": CAND.boot_ci(d, rng),
                    "n_positive": k, "n_domains": len(d), "sign_p": p, "sign_p_floor": fl,
                    "ratio_codeword_over_control": (
                        row["codeword_last"]["mean_gap_units"] / row[ctrl]["mean_gap_units"]
                        if row[ctrl]["mean_gap_units"] else float("nan"))}
            rec["layers"]["L%d" % L] = row
        res["by_bank"][bank] = rec

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)

    for bank, rec in res["by_bank"].items():
        print("\n=== %s ===" % bank)
        for n, m in rec["meta"].items():
            print("  %-14s %s" % (n, m.get("REFUSED") or
                                  "run=%s pos=%s rows=%d doms=%d tokens=%s"
                                  % (m["run"][:44], m["position"], m["n_rows_analysed"],
                                     m["n_domains"], m["token_text_by_cell"])))
        print("  %-5s %11s %11s %11s | %-22s %-22s" % ("L", "codeword", "following", "last",
                                                       "cw-following", "cw-last"))
        for Lk, row in rec["layers"].items():
            f = row.get("paired_codeword_minus_following", {})
            l = row.get("paired_codeword_minus_last", {})
            print("  %-5s %11.4f %11.4f %11.4f | %+.4f %2d/%d p=%.2g | %+.4f %2d/%d p=%.2g"
                  % (Lk, row["codeword_last"]["mean_gap_units"],
                     row.get("following", {}).get("mean_gap_units", float("nan")),
                     row.get("last", {}).get("mean_gap_units", float("nan")),
                     f.get("mean", float("nan")), f.get("n_positive", -1), f.get("n_domains", -1),
                     f.get("sign_p", float("nan")),
                     l.get("mean", float("nan")), l.get("n_positive", -1), l.get("n_domains", -1),
                     l.get("sign_p", float("nan"))))
    print("\nwrote %s" % a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
