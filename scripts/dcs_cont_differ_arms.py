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
import argparse, glob, importlib.util, json, os, random, statistics, sys
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


def _atomic_json_dump(obj, path, **kw):
    """Atomic, VERIFIED JSON write. Fix for sprint entry S-124.

    Replaces `json.dump(x, open(p, "w"), ...)`, whose handle is never closed: `open` truncates the
    destination immediately and the buffered bytes are flushed only in the GC finaliser, where
    CPython PRINTS and then SWALLOWS an EDQUOT. A full quota therefore produced a 0-byte file at a
    real artifact name, with "wrote <path>" on stdout and exit status 0 -- indistinguishable from a
    finished report. Temp file + fsync + size check + re-parse + os.replace makes the write ATOMIC
    as well as checked: a half-written file never appears at the real name, and whatever was there
    before survives a failure. On any error this RAISES, naming the path and the byte count.
    """
    import tempfile                        # local: keeps this helper drop-in and import-order-free
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_atomic_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, **kw)
            fh.flush()
            os.fsync(fh.fileno())          # EDQUOT surfaces HERE, not in a GC finaliser
        n = os.path.getsize(tmp)
        if n == 0:
            raise OSError("temp file is 0 bytes after a flush+fsync that reported success")
        with open(tmp, "r", encoding="utf-8") as fh:
            json.load(fh)                  # a truncated write does not re-parse
        try:
            mode = os.stat(path).st_mode & 0o7777   # keep the artifact's existing permissions:
        except OSError:                             # mkstemp makes the temp file 0600 and
            mode = 0o644                            # os.replace would carry that onto the report
        os.chmod(tmp, mode)
        os.replace(tmp, path)              # atomic within the directory
    except Exception as e:
        try:
            n = os.path.getsize(tmp)
        except OSError:
            n = -1
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise OSError("atomic_json_dump FAILED for %s -- %d bytes reached the temp file; the "
                      "destination is UNCHANGED (never truncated). Cause: %r" % (path, n, e)) from e
    return os.path.getsize(path)


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

    # map prompt_id -> (domain, slot) from ctrl rows; ko shares prompt_ids (same bank)
    meta = {r["prompt_id"]: (r["domain"], lpm.family_slot(r["family_id"]), r["cell"]) for r in rc}

    def slc(mp, pid, site, layer):
        # index each cache by ITS OWN site/layer order -- the slim ko cache has a different site
        # set and layer subset than cont1's full grid, so a shared index would read the wrong cell.
        t = mp["reps"].get(pid)
        if t is None or site not in mp["sites"] or layer not in mp["layers"]:
            return None
        return t[mp["sites"].index(site), mp["layers"].index(layer)].float()

    def fit_w(site, layer, permute_seed=None):
        """Ridge direction on the CTRL cache, TRAIN, within-domain-centred cell-C -- the F8/F5 probe.
        permute_seed != None shuffles the target = a placebo direction (specificity control)."""
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
        if permute_seed is not None:                        # PLACEBO: shuffle target -> non-installation direction
            g = random.Random(permute_seed); random.Random(permute_seed).shuffle(ys)
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
    # SPECIFICITY control: because ||Delta|| at the query side is large, a random direction of the
    # SAME norm as w_q, at the SAME query site, must NOT show a comparable projection shift -- else the
    # shift is a generic consequence of the perturbation, not alignment with the installation code.
    _wq = W["query_winner_%s_L%d" % (wsite, wlayer)]
    _g = torch.Generator().manual_seed(20260914)
    _rand = [torch.randn(_wq.shape[0], generator=_g, dtype=torch.float64) for _ in range(5)]
    _rand = [r / r.norm() * _wq.norm() for r in _rand]   # match ||w_q||

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

    # ---- CONT-165 decisive controls: separate installation-specificity from an activation-energy artifact
    _pv = []
    for pid, d in pairs:
        hc = slc(mc, pid, wsite, wlayer); hk = slc(mk, pid, wsite, wlayer)
        if hc is not None and hk is not None:
            _pv.append((d, hc.double(), hk.double()))
    _wq = W["query_winner_%s_L%d" % (wsite, wlayer)]

    def _pdmean(scalars, doms):
        from collections import defaultdict as _dd2
        g = _dd2(list)
        for sc, d in zip(scalars, doms):
            g[d].append(sc)
        return {d: sum(v) / len(v) for d, v in g.items()}

    def _shift_on(vec):
        dm = _pdmean([float((hk - hc) @ vec) for _, hc, hk in _pv], [d for d, _, _ in _pv])
        vals = list(dm.values())
        return sum(vals) / len(vals), dm

    real_shift, real_dm = _shift_on(_wq)
    # (a) PLACEBO-TARGET ridge: same fit on a SHUFFLED target; if its shift ~ real, not installation-specific
    placebo = []
    for seed in range(8):
        wp = fit_w(wsite, wlayer, permute_seed=20260915 + seed)
        placebo.append(_shift_on(wp)[0])
    # (b) MEAN-STATE projection-out: remove the mean activation axis from w_q; energy artifact would collapse
    mu = torch.stack([hc for _, hc, _ in _pv], 0).mean(0)
    uhat = mu / mu.norm()
    w_perp = _wq - (_wq @ uhat) * uhat
    perp_shift, _ = _shift_on(w_perp)
    norm_ctrl = float(torch.stack([hc.norm() for _, hc, _ in _pv]).mean())
    norm_ko = float(torch.stack([hk.norm() for _, _, hk in _pv]).mean())
    cos_wq_mu = float((_wq @ mu) / (_wq.norm() * mu.norm()))
    # (c) TRAIN/VAL breakout (w_q fit on TRAIN ctrl only)
    tr_vals = [v for d, v in real_dm.items() if d in TR]
    va_vals = [v for d, v in real_dm.items() if d in (KEEP - TR)]
    out["controls_cont165"] = {
        "real_query_shift": round(real_shift, 5),
        "placebo_target_shifts": [round(x, 5) for x in placebo],
        "placebo_mean": round(sum(placebo) / len(placebo), 5),
        "placebo_max_abs": round(max(abs(x) for x in placebo), 5),
        "specificity_ratio_real_over_placebo_maxabs": round(abs(real_shift) / max(1e-9, max(abs(x) for x in placebo)), 2),
        "mean_state_projout_shift": round(perp_shift, 5),
        "projout_retained_fraction": round(perp_shift / real_shift, 3) if real_shift else None,
        "norm_ctrl": round(norm_ctrl, 3), "norm_ko": round(norm_ko, 3),
        "norm_ratio_ko_over_ctrl": round(norm_ko / norm_ctrl, 4),
        "cos_wq_meanstate": round(cos_wq_mu, 4),
        "train_shift": round(sum(tr_vals) / len(tr_vals), 5) if tr_vals else None, "n_train_dom": len(tr_vals),
        "val_shift": round(sum(va_vals) / len(va_vals), 5) if va_vals else None, "n_val_dom": len(va_vals),
        "reading": "installation-SPECIFIC iff |real| >> placebo AND survives mean-state projection-out "
                   "(retained fraction near 1) AND holds on VAL; if placebo matches or projout collapses "
                   "it, it is an activation-energy artifact (energy-reduction rival)."}
    print("[CONT165] real=%.5f placebo(max|.|)=%.5f ratio=%.1fx | projout=%.5f (retain %.2f) | "
          "norm ko/ctrl=%.3f cos(wq,mu)=%.3f | train=%.5f val=%.5f"
          % (real_shift, out["controls_cont165"]["placebo_max_abs"],
             out["controls_cont165"]["specificity_ratio_real_over_placebo_maxabs"], perp_shift,
             out["controls_cont165"]["projout_retained_fraction"] or 0.0,
             out["controls_cont165"]["norm_ratio_ko_over_ctrl"], cos_wq_mu,
             out["controls_cont165"]["train_shift"] or 0.0, out["controls_cont165"]["val_shift"] or 0.0))

    # OOD adversarial check + domain leverage, at the query winner site/layer.
    from collections import defaultdict as _dd
    _wq = W["query_winner_%s_L%d" % (wsite, wlayer)]
    pc_all, pk_all, y_all, dof_all = [], [], [], []
    for pid, d in pairs:
        hc = slc(mc, pid, wsite, wlayer); hk = slc(mk, pid, wsite, wlayer)
        yv = inst.get((d, meta[pid][1]))
        if hc is None or hk is None or yv is None:
            continue
        pc_all.append(float(hc.double() @ _wq)); pk_all.append(float(hk.double() @ _wq))
        y_all.append(float(yv)); dof_all.append(d)

    def _wdc(vals, dof):
        g = _dd(list)
        for v, d in zip(vals, dof):
            g[d].append(v)
        mean = {d: statistics.mean(g[d]) for d in g}
        return [v - mean[d] for v, d in zip(vals, dof)]
    _pc, _pk, _y = _wdc(pc_all, dof_all), _wdc(pk_all, dof_all), _wdc(y_all, dof_all)
    out["ood_check"] = {"site": wsite, "layer": wlayer,
        "rho_ctrl_proj_vs_install": round(lpm.spearman(_pc, _y), 4),
        "rho_ko_proj_vs_install": round(lpm.spearman(_pk, _y), 4),
        "note": "within-domain; if rho_ko ~ rho_ctrl the ridge readout still reads installation on "
                "the ko states, so the negative projection shift is a real installation reduction, "
                "not an off-manifold extrapolation artifact. If rho_ko collapses, the shift is suspect."}
    # domain leverage: per-domain query-probe shift sign distribution
    _ds = _dd(list)
    for pid, d in pairs:
        hc = slc(mc, pid, wsite, wlayer); hk = slc(mk, pid, wsite, wlayer)
        if hc is not None and hk is not None:
            _ds[d].append(float((hk.double() - hc.double()) @ _wq))
    _dm = {d: statistics.mean(v) for d, v in _ds.items() if v}
    out["domain_leverage"] = {"n_domains": len(_dm),
        "n_negative": sum(1 for v in _dm.values() if v < 0),
        "n_positive": sum(1 for v in _dm.values() if v > 0)}
    print("[OOD] rho(proj,install) within-domain: ctrl=%.4f  ko=%.4f"
          % (out["ood_check"]["rho_ctrl_proj_vs_install"], out["ood_check"]["rho_ko_proj_vs_install"]))
    print("[leverage] per-domain query shift negative in %d/%d domains"
          % (out["domain_leverage"]["n_negative"], out["domain_leverage"]["n_domains"]))

    # random-direction control at the query winner site (same norm as w_q), 5 draws
    rand_shifts = []
    for ri, rvec in enumerate(_rand):
        per_dom = {}
        for pid, d in pairs:
            hc = slc(mc, pid, wsite, wlayer); hk = slc(mk, pid, wsite, wlayer)
            if hc is None or hk is None:
                continue
            per_dom.setdefault(d, []).append(float((hk.double() - hc.double()) @ rvec))
        dm = [statistics.mean(v) for v in per_dom.values() if v]
        rand_shifts.append(statistics.mean(dm))
    out["random_direction_control"] = {
        "site": wsite, "layer": wlayer, "n_draws": len(rand_shifts),
        "mean_abs_random_shift": round(sum(abs(x) for x in rand_shifts) / len(rand_shifts), 5),
        "random_shifts": [round(x, 5) for x in rand_shifts],
        "query_probe_shift_for_comparison": out["projection_shift"]["query_winner_%s_L%d" % (wsite, wlayer)]["mean_per_domain_shift"]}
    print("  random-dir control (|shift| mean of %d, same norm as w_q) = %.5f  vs query-probe %.5f"
          % (len(rand_shifts), out["random_direction_control"]["mean_abs_random_shift"],
             out["random_direction_control"]["query_probe_shift_for_comparison"]))
    _atomic_json_dump(out, a.out, indent=1)
    print("wrote %s" % os.path.relpath(a.out, REPO))
    print("INTERPRETATION: control ||Delta|| at cw_demo_mean must be ~0 (validates C-CONT-040 & "
          "pairing). A query-side projection shift whose CI excludes 0 AND is the RIGHT SIGN (the "
          "knockout moving the installation-coded component) is the §44 #10 signal; demo-side F5 "
          "shift ~0 is the inert control.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
