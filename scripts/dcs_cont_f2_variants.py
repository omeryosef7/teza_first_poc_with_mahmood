#!/usr/bin/env python3
"""F2 diff-in-means, the two variants declared in the registry but NEVER fitted: v_hi_lo, v_resid.

Mandate §16. The registry records v_int (interaction) and C_minus_B as FITTED and NEGATIVE/TIE
(v_int loses to the raw state p=0.017; C_minus_B ties p=0.515). Two declared variants were left
unfitted; this closes them, TRAIN/VALIDATION only, both codewords, never pooled, reusing the lpm
loaders and the same within-domain LOO protocol F5/qprobe use so the numbers are comparable.

  v_hi_lo = mean[h_C | high y_install] - mean[h_C | low y_install], within-domain, split at the
            fold's own median of within-domain-centred y. This is the SUPERVISED diff-in-means
            direction -- a hard-split, binary-target cousin of the F5 ridge. Expected to be <= F5
            (a median split discards the graded target), and the point is to confirm that.
  v_resid = mean(h_C - h_A) orthogonalised against v_int. NOTE: the registry's v_resid also
            orthogonalises against "a generic-remap direction", which has no committed definition
            in this corpus; this run omits that term and is therefore a PARTIAL v_resid (states so).

SCORING (identical for both, and to F5/K1): each fold builds a direction vhat on the OTHER domains,
then reads out the held-out domain's within-domain-centred cell-C state as <z_C, vhat>, and the
pooled held-out readouts are Spearman-correlated with within-domain-centred y_install. LOO by domain.
Topic trap #1 is handled by within-domain centring; a positive here must still be read against the
raw-state floor (F1 ~+0.546 within-domain) and F5 (+0.624 TRAIN / +0.678 VAL button).
"""
from __future__ import annotations
import argparse, importlib.util, json, os, statistics, sys
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

CORPUS = "outputs/boombness/extract_boombness/cont1_behavioral_button_bomb_20260910_152806_272296"
READOUT = "outputs/boombness/score_behavior/ts116m_readout_button_bomb_20260907_133811_3183103"
SITE, LAYER = "cw_demo_mean", 24


def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m


def _unit(v):
    n = v.norm()
    return v / n if float(n) > 1e-9 else v


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=CORPUS)
    ap.add_argument("--readout", default=READOUT)
    ap.add_argument("--site", default=SITE)
    ap.add_argument("--layer", type=int, default=LAYER)
    ap.add_argument("--out", default=os.path.join(REPO, "reports/DCS_CONT_F2_VARIANTS.json"))
    a = ap.parse_args()

    lpm = _load("lpm", "scripts/dcs_cont_layerpos_map.py")
    assign = lpm.load_split(); EX = set(lpm.EXCLUDED_DOMAINS)
    TR = {d for d, v in assign.items() if v == "train"} - EX
    inst, _, _ = lpm.load_installation(os.path.join(REPO, a.readout))
    mp, rows, csha = lpm.load_corpus(os.path.join(REPO, a.corpus), mmap=True)
    if any(assign.get(r["domain"]) == "test" for r in rows):
        print("REFUSING: corpus contains test-split rows"); return 2
    rsha, rsrc = lpm.readout_bank_sha(os.path.join(REPO, a.readout))
    if rsha != csha:
        print("REFUSING: bank mismatch corpus %s vs readout %s (%s)" % (csha, rsha, rsrc)); return 2
    si, li = mp["sites"].index(a.site), mp["layers"].index(a.layer)

    # per-domain lists of within-domain-centred (zC, zA, zB, zE, zy) for complete ABCE slots
    byk = {}
    for r in rows:
        if r["domain"] in TR:
            t = mp["reps"].get(r["prompt_id"])
            if t is not None:
                byk[((r["domain"], lpm.family_slot(r["family_id"])), r["cell"])] = t[si, li].float()
    comp = [k for k in sorted({k for k, _ in byk}) if all((k, c) in byk for c in "ABCE")]
    doms = sorted({d for d, _ in comp})
    dom_slots = {}
    for d in doms:
        ks = [k for k in comp if k[0] == d]
        C = torch.stack([byk[(k, "C")] for k in ks]); A = torch.stack([byk[(k, "A")] for k in ks])
        B = torch.stack([byk[(k, "B")] for k in ks]); E = torch.stack([byk[(k, "E")] for k in ks])
        y = torch.tensor([inst[k] for k in ks], dtype=torch.float32)
        zC = (C - C.mean(0)).double(); zA = (A - A.mean(0)).double()
        zB = (B - B.mean(0)).double(); zE = (E - E.mean(0)).double()
        zy = (y - y.mean()).double()
        dom_slots[d] = (zC, zA, zB, zE, zy)

    def fit_dir(train_doms, kind):
        zc = torch.cat([dom_slots[d][0] for d in train_doms], 0)
        za = torch.cat([dom_slots[d][1] for d in train_doms], 0)
        zb = torch.cat([dom_slots[d][2] for d in train_doms], 0)
        ze = torch.cat([dom_slots[d][3] for d in train_doms], 0)
        zy = torch.cat([dom_slots[d][4] for d in train_doms], 0)
        if kind == "v_hi_lo":
            thr = zy.median()
            hi = zy > thr; lo = ~hi
            if hi.sum() == 0 or lo.sum() == 0:
                return None
            return _unit(zc[hi].mean(0) - zc[lo].mean(0))
        v_int = _unit(((zc - za) - (zb - ze)).mean(0))
        d_ca = (zc - za).mean(0)
        if kind == "v_int":
            return v_int
        if kind == "v_resid":                        # (C-A) orthogonalised against v_int
            return _unit(d_ca - (d_ca @ v_int) * v_int)
        raise ValueError(kind)

    def loo(kind):
        pred, ys = [], []
        for d in doms:
            vhat = fit_dir([x for x in doms if x != d], kind)
            if vhat is None:
                return None
            zC, _, _, _, zy = dom_slots[d]
            pj = (zC @ vhat).tolist()
            pred += pj; ys += zy.tolist()
        return lpm.spearman(pred, ys)

    out = {"schema": "dcs_cont_f2_variants/1", "corpus": a.corpus, "site": a.site,
           "layer": a.layer, "n_domains": len(doms),
           "reference": {"raw_state_floor_F1_within_domain": 0.546,
                         "F5_ridge_train_loo": 0.6241, "F5_ridge_val_transfer": 0.6784},
           "train_loo_rho": {}, "note":
           "TRAIN LOO-by-domain, within-domain-centred, scored <z_C, vhat>. v_resid omits the "
           "generic-remap term (no committed definition) and is a PARTIAL v_resid."}
    for kind in ("v_hi_lo", "v_int", "v_resid"):
        r = loo(kind)
        out["train_loo_rho"][kind] = round(r, 4) if r is not None else None
        print("  %-10s TRAIN LOO rho = %s" % (kind, ("%+.4f" % r) if r is not None else "n/a"))
    print("[F2-variants] site=%s L%d, %d domains; F5 ridge TRAIN LOO = +0.6241 for comparison"
          % (a.site, a.layer, len(doms)))
    json.dump(out, open(a.out, "w"), indent=1)
    print("[F2-variants] wrote %s" % os.path.relpath(a.out, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
