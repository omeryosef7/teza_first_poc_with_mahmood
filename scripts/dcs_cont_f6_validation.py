#!/usr/bin/env python3
"""F6 low-rank subspace, carried through VALIDATION selection -- the §14/§46 prerequisite that
`dcs_cont_lowrank.py` never completed.

WHY. `dcs_cont_lowrank.py` (C-CONT-043, deflation fixed) reports PLS TRAIN LOO by rank and, with
`--split validation`, a WITHIN-validation LOO. Neither is a train-select / validation-transfer:
the mandate (§14) requires the rank be selected under a PRE-DECLARED rule and the honest number be
the transfer of that fixed rank to held-out VALIDATION. This script does exactly that, reusing
`dcs_cont_lowrank.pls_fit` / `pls_predict` (the deflation-corrected pair) and `dcs_cont_layerpos_map`
loaders. TRAIN/VALIDATION only; TEST never read; bank_sha guarded; button and basket never pooled.

PRE-DECLARED SELECTION RULE (fixed here BEFORE any VALIDATION number is computed):
    selected_rank = the SMALLEST rank whose TRAIN LOO rho is within 0.010 of the best TRAIN LOO
                    rho over the ranks tried (parsimony-favouring). The VALIDATION transfer of
                    that rank is the headline; per-rank VALIDATION transfers are also reported for
                    transparency but are NOT used to choose.
The incumbent to beat is the F5 ridge probe (VALIDATION rho +0.6784 button / +0.6807 basket).
"""
from __future__ import annotations
import argparse, importlib.util, json, os, statistics, sys
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

CORPUS = "outputs/boombness/extract_boombness/cont1_behavioral_button_bomb_20260910_152806_272296"
READOUT = "outputs/boombness/score_behavior/ts116m_readout_button_bomb_20260907_133811_3183103"
TOL = 0.010   # pre-declared parsimony tolerance for rank selection on TRAIN LOO


def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=CORPUS)
    ap.add_argument("--readout", default=READOUT)
    ap.add_argument("--site", default="cw_demo_mean")
    ap.add_argument("--layer", type=int, default=24)
    ap.add_argument("--ranks", default="1,2,4,8,16")
    ap.add_argument("--out", default=os.path.join(REPO, "reports/DCS_CONT_F6_VALIDATION.json"))
    a = ap.parse_args()
    ranks = [int(x) for x in a.ranks.split(",") if x.strip()]

    lpm = _load("lpm", "scripts/dcs_cont_layerpos_map.py")
    lr = _load("lr", "scripts/dcs_cont_lowrank.py")   # reuse pls_fit / pls_predict
    assign = lpm.load_split(); EX = set(lpm.EXCLUDED_DOMAINS)
    TR = {d for d, v in assign.items() if v == "train"} - EX
    VA = {d for d, v in assign.items() if v == "validation"} - EX
    inst, _, _ = lpm.load_installation(os.path.join(REPO, a.readout))
    mp, rows, csha = lpm.load_corpus(os.path.join(REPO, a.corpus), mmap=True)
    if any(assign.get(r["domain"]) == "test" for r in rows):
        print("REFUSING: corpus contains test-split rows"); return 2
    rsha, rsrc = lpm.readout_bank_sha(os.path.join(REPO, a.readout))
    if rsha != csha:
        print("REFUSING: bank mismatch corpus %s vs readout %s (%s)" % (csha, rsha, rsrc)); return 2
    if a.site not in mp["sites"] or a.layer not in mp["layers"]:
        print("REFUSING: site/layer not captured"); return 3
    si, li = mp["sites"].index(a.site), mp["layers"].index(a.layer)

    def build(keep):
        byk = {}
        for r in rows:
            if r["domain"] in keep:
                t = mp["reps"].get(r["prompt_id"])
                if t is not None:
                    k = ((r["domain"], lpm.family_slot(r["family_id"])), r["cell"])
                    if k in byk:   # (REVIEW-10) match layerpos_map's duplicate-key refusal
                        raise SystemExit("duplicate key %r -- silent channel substitution" % (k,))
                    byk[k] = t[si, li].float()
        comp = [k for k in sorted({k for k, _ in byk}) if all((k, c) in byk for c in "ABCE")]
        doms = sorted({d for d, _ in comp}); xs = []; ys = []; dof = []
        for d in doms:
            ks = [k for k in comp if k[0] == d]
            mx = sum(byk[(k, "C")] for k in ks) / len(ks)
            my = statistics.mean([inst[k] for k in ks])
            for k in ks:
                xs.append(byk[(k, "C")] - mx); ys.append(inst[k] - my); dof.append(d)
        return torch.stack(xs, 0), torch.tensor(ys, dtype=torch.float32), dof, doms

    Xtr, ytr, dtr, domtr = build(TR)
    Xva, yva, dva, domva = build(VA)
    print("[F6-val] site=%s L%d  TRAIN %d slots/%d dom  VAL %d slots/%d dom"
          % (a.site, a.layer, len(ytr), len(domtr), len(yva), len(domva)))

    # ---- TRAIN LOO by rank (leave-one-domain-out PLS; same as dcs_cont_lowrank --split train)
    train_loo = {}
    for r in ranks:
        pred = [0.0] * len(ytr)
        for d in domtr:
            ho = [i for i, dd in enumerate(dtr) if dd == d]
            trn = [i for i, dd in enumerate(dtr) if dd != d]
            W, C, P = lr.pls_fit(Xtr[trn], ytr[trn], r)
            if W is None:
                continue
            p = lr.pls_predict(Xtr[ho], W, C, P)
            for j, i in enumerate(ho):
                pred[i] = float(p[j])
        train_loo[r] = lpm.spearman(pred, ytr.tolist())
        print("   TRAIN LOO rank %-2d = %+.4f" % (r, train_loo[r]))

    # ---- pre-declared selection: smallest rank within TOL of the best TRAIN LOO
    best = max(train_loo.values())
    selected = min(r for r in ranks if train_loo[r] >= best - TOL)
    print("[F6-val] best TRAIN LOO %+.4f; selected rank = %d (smallest within %.3f)"
          % (best, selected, TOL))

    # ---- VALIDATION transfer per rank (fit ALL TRAIN, predict VAL); headline = selected rank
    val_transfer = {}
    for r in ranks:
        W, C, P = lr.pls_fit(Xtr, ytr, r)
        val_transfer[r] = lpm.spearman(lr.pls_predict(Xva, W, C, P).tolist(), yva.tolist()) \
            if W is not None else None
        print("   VAL transfer rank %-2d = %s" % (r, ("%+.4f" % val_transfer[r]) if val_transfer[r] is not None else "n/a"))

    out = {"schema": "dcs_cont_f6_validation/1", "corpus": a.corpus, "site": a.site,
           "layer": a.layer, "ranks": ranks, "selection_rule":
           "smallest rank within %.3f of best TRAIN LOO (parsimony); VAL transfer is the headline" % TOL,
           "train_loo_by_rank": {str(r): round(v, 4) for r, v in train_loo.items()},
           "val_transfer_by_rank": {str(r): (round(v, 4) if v is not None else None)
                                    for r, v in val_transfer.items()},
           "selected_rank": selected,
           "selected_val_transfer": round(val_transfer[selected], 4) if val_transfer[selected] is not None else None,
           "f5_incumbent_val": {"button": 0.6784, "basket": 0.6807},
           "verdict_note": "F6 beats F5 on VALIDATION only if selected_val_transfer exceeds the "
                           "matching codeword's F5 incumbent; otherwise low-rank structure adds "
                           "nothing over the F5 ridge and F6 is closed as EXPLORATORY-negative."}
    json.dump(out, open(a.out, "w"), indent=1)
    svt = out["selected_val_transfer"]
    print("[F6-val] selected rank %d VAL transfer = %s  (F5 button 0.6784 / basket 0.6807)"
          % (selected, ("%+.4f" % svt) if svt is not None else "n/a (PLS degenerate at selected rank)"))
    print("[F6-val] wrote %s" % os.path.relpath(a.out, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
