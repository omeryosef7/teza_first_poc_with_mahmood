#!/usr/bin/env python3
"""The differ-across-arms causal test (§44 #10): does the A1 knockout move the QUERY-SIDE state, and
does it move it ALONG the installation-predictive direction? (CONT-155 proposal.)

F5/A11 is causally inert because its demo-side site is bit-identical across ko/ctrl (C-CONT-040). The
query codeword row (cw_query == rel-11) and the query-span positions (rel-6 is the F8 winner) ARE
downstream of the band-6-14 knockout, so their states can change. This pairs the ko cache
(cont1ko_behavioral_<cw>_bomb) with the ctrl cache (cont1_behavioral_<cw>_bomb, no-knockout) by
prompt_id and asks:

  1. POSITIVE CONTROL: mean ||h_ko - h_ctrl|| at cw_demo_mean must be ~0 (C-CONT-040's invariance). If
     it is not, the pairing/extraction is wrong and the test is void.
  2. EFFECT PRESENT: ||h_ko - h_ctrl|| at cw_query / rel-6 -- non-zero is near-certain (edited row).
  3. DECISIVE: project the paired state difference onto the installation-predictive direction w (refit
     by ridge on the ctrl cache TRAIN at that site/layer, the F8/F5 machinery). Mean per-domain
     (h_ko - h_ctrl).w. If systematically NEGATIVE at the query side, the knockout REDUCES the query-
     side installation-coded component -> the query-side representation is on the causal path of the
     A1 installation reduction (a §44 #10 candidate). The demo-side w (cw_demo_mean) is the control:
     its projection shift must be ~0 (inert).

DOMAIN unit; button and basket never pooled; TRAIN+VALIDATION only (no TEST); mmap (low RAM). Power
caveat (CONT-150): any per-domain correlation at N~67 has MDE ~0.337, so a null tracking result means
"no effect above MDE", not "no effect". The magnitude/sign of the projection shift is not correlation-
limited and is the primary read.
"""
from __future__ import annotations
import argparse, glob, importlib.util, json, os, statistics, sys
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

CTRL = {"button": "outputs/boombness/extract_boombness/cont1_behavioral_button_bomb_20260910_152806_272296",
        "basket": "outputs/boombness/extract_boombness/cont1_behavioral_basket_bomb_20260910_113902_3966018"}
READOUT = {"button": "outputs/boombness/score_behavior/ts116m_readout_button_bomb_20260907_133811_3183103",
           "basket": "outputs/boombness/score_behavior/ts116m_readout_basket_bomb_20260907_152329_3191150"}
WINNER = {"button": ("rel-6", 20), "basket": ("rel-6", 18)}   # F8 query-side winner (CONT-152)
F5 = ("cw_demo_mean", 24)                                      # demo-side inert control (C-CONT-040)
LAM = 100.0


def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s); sys.modules[mod] = m; s.loader.exec_module(m); return m


def find_ko(cw):
    hits = sorted(glob.glob(os.path.join(REPO, "outputs/boombness/extract_boombness/cont1ko_behavioral_%s_bomb_*" % cw)))
    hits = [h for h in hits if os.path.exists(os.path.join(h, "cache", "multiposition_reps.pt"))
            and os.path.exists(os.path.join(h, "DONE.json"))]
    return hits[-1] if hits else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", default="button", choices=("button", "basket"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    cw = a.codeword
    if a.out is None:
        a.out = os.path.join(REPO, "reports/DCS_CONT_DIFFER_ARMS_%s.json" % cw)
    lpm = _load("lpm", "scripts/dcs_cont_layerpos_map.py")
    ko_dir = find_ko(cw)
    if ko_dir is None:
        print("REFUSING: no finished ko cache for %s yet" % cw); return 3

    assign = lpm.load_split(); EX = set(lpm.EXCLUDED_DOMAINS)
    TR = {d for d, v in assign.items() if v == "train"} - EX
    KEEP = {d for d, v in assign.items() if v in ("train", "validation")} - EX
    inst, _, _ = lpm.load_installation(os.path.join(REPO, READOUT[cw]))
    mc, rc, shc = lpm.load_corpus(CTRL[cw], mmap=True)
    mk, rk, shk = lpm.load_corpus(ko_dir, mmap=True)
    if shc != shk:
        print("REFUSING: ko/ctrl bank mismatch %s vs %s" % (shc, shk)); return 2
    if any(assign.get(r["domain"]) == "test" for r in rc + rk):
        print("REFUSING: a test-split row is present"); return 2

    sites, layers = list(mc["sites"]), list(mc["layers"])
    # map prompt_id -> (domain, slot) from ctrl rows; ko shares prompt_ids (same bank)
    meta = {r["prompt_id"]: (r["domain"], lpm.family_slot(r["family_id"]), r["cell"]) for r in rc}

    def slc(mp, pid, site, layer):
        t = mp["reps"].get(pid)
        if t is None:
            return None
        return t[sites.index(site), layers.index(layer)].float()

    def fit_w(site, layer):
        """Ridge direction on the CTRL cache, TRAIN, within-domain-centred cell-C -- the F8/F5 probe."""
        byk = {}
        for r in rc:
            d, s, c = meta[r["prompt_id"]]
            if d in TR:
                v = slc(mc, r["prompt_id"], site, layer)
                if v is not None:
                    byk[((d, s), c)] = v
        comp = [k for k in sorted({k for k, _ in byk}) if all((k, cc) in byk for cc in "ABCE")]
        doms = sorted({d for d, _ in comp}); xs, ys = [], []
        for d in doms:
            ks = [k for k in comp if k[0] == d]
            V = torch.stack([byk[(k, "C")] for k in ks], 0).double()
            xs.append(V - V.mean(0, keepdim=True))
            yv = [inst[k] for k in ks]; m = statistics.mean(yv); ys += [y - m for y in yv]
        X = torch.cat(xs, 0); y = torch.tensor(ys, dtype=torch.float64)
        al = torch.linalg.solve(X @ X.T + LAM * torch.eye(len(y), dtype=torch.float64), y)
        return (X.T @ al)                                   # w in R^d

    # paired cell-C prompts present in BOTH arms, kept domains
    pairs = []
    for pid, (d, s, c) in meta.items():
        if d in KEEP and c == "C" and mk["reps"].get(pid) is not None:
            pairs.append((pid, d))
    print("[%s] ko_dir=%s  %d paired cell-C prompts / %d domains"
          % (cw, os.path.basename(ko_dir), len(pairs), len({d for _, d in pairs})))

    out = {"schema": "dcs_cont_differ_arms/1", "codeword": cw, "ko_dir": os.path.relpath(ko_dir, REPO),
           "n_pairs": len(pairs), "lambda": LAM, "sites": {},
           "power_caveat": "per-domain effects at N~67 have MDE ~0.337 (CONT-150); a null shift is "
                           "'no effect above MDE', not 'no effect'. The projection-shift sign/size "
                           "is the primary, non-correlation-limited read."}

    wsite, wlayer = WINNER[cw]
    probes = {"query_winner_%s_L%d" % (wsite, wlayer): (wsite, wlayer),
              "demo_F5_%s_L%d" % F5: F5}
    W = {name: fit_w(site, layer) for name, (site, layer) in probes.items()}

    # per-site ||Delta|| (magnitude) at treatment sites and the demo-side control
    mag_sites = {"cw_query": ("cw_query", wlayer), "rel-6": ("rel-6", wlayer),
                 "cw_demo_mean(control)": ("cw_demo_mean", F5[1])}
    for label, (site, layer) in mag_sites.items():
        per_dom = {}
        for pid, d in pairs:
            hc = slc(mc, pid, site, layer); hk = slc(mk, pid, site, layer)
            if hc is None or hk is None:
                continue
            per_dom.setdefault(d, []).append(float((hk.double() - hc.double()).norm()))
        dom_means = [statistics.mean(v) for v in per_dom.values() if v]
        out["sites"][label] = {"site": site, "layer": layer,
                               "mean_domain_delta_norm": round(statistics.mean(dom_means), 4),
                               "n_domains": len(dom_means)}
        print("  ||Delta|| %-22s = %.4f  (%d domains)" % (label, statistics.mean(dom_means), len(dom_means)))

    out["projection_shift"] = {}
    for name, (site, layer) in probes.items():
        w = W[name]
        per_dom = {}
        for pid, d in pairs:
            hc = slc(mc, pid, site, layer); hk = slc(mk, pid, site, layer)
            if hc is None or hk is None:
                continue
            per_dom.setdefault(d, []).append(float((hk.double() - hc.double()) @ w))
        dom_means = {d: statistics.mean(v) for d, v in per_dom.items() if v}
        vals = list(dom_means.values())
        mean_shift = statistics.mean(vals)
        # domain-clustered bootstrap CI on the mean per-domain projection shift
        import random
        g = random.Random(20260914); dl = list(vals); bs = []
        for _ in range(20000):
            s = [dl[g.randrange(len(dl))] for _ in dl]; bs.append(sum(s) / len(s))
        bs.sort()
        lo, hi = bs[int(.025 * len(bs))], bs[int(.975 * len(bs))]
        out["projection_shift"][name] = {"site": site, "layer": layer,
                                         "mean_per_domain_shift": round(mean_shift, 5),
                                         "ci95": [round(lo, 5), round(hi, 5)], "n_domains": len(vals),
                                         "excludes_zero": bool(lo > 0 or hi < 0)}
        print("  proj-shift onto %-28s = %+.5f  [%+.5f, %+.5f]  (excl0=%s)"
              % (name, mean_shift, lo, hi, out["projection_shift"][name]["excludes_zero"]))

    json.dump(out, open(a.out, "w"), indent=1)
    print("wrote %s" % os.path.relpath(a.out, REPO))
    print("INTERPRETATION: control ||Delta|| at cw_demo_mean must be ~0 (validates C-CONT-040 & "
          "pairing). A query-side projection shift whose CI excludes 0 AND is the RIGHT SIGN (the "
          "knockout moving the installation-coded component) is the §44 #10 signal; demo-side F5 "
          "shift ~0 is the inert control.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
