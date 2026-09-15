#!/usr/bin/env python3
"""P4-a: does the installation axis depend on the particular DEMONSTRATION SENTENCES?

THE QUESTION, STATED PRECISELY SO IT IS NOT OVERSOLD. The bank carries a prompt-level `dev`/
`heldout` split inside `family_id`, orthogonal to the ts116m DOMAIN split: same domains, same
template family, DIFFERENT demonstration sentences. Fitting the axis on `dev` rows and scoring it
on `heldout` rows therefore asks whether the axis generalises across the specific sentences used to
install the mapping.

WHAT THIS IS NOT. It is **not** template generalisation (plan section 9.1). The corpus contains
exactly one template family -- `example_position=near`, `role_style=plain` on every row -- so a
train-on-template-A / test-on-template-B experiment is not analysable here at all and needs a new
extraction. Reporting this test as template transfer would be the weaker claim wearing the
stronger claim's name.

Everything heavy is imported from `dcs_csi_axis`: the same build, the same ridge, the same
leave-one-DOMAIN-out, the same within-domain centring. Only the row filter differs.
"""
from __future__ import annotations
import argparse, importlib.util, json, os, statistics, sys
import torch

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))


def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s); sys.modules[mod] = m; s.loader.exec_module(m); return m


axis = _load("csi_axis", "scripts/dcs_csi_axis.py")
lpm = _load("lpm", "scripts/dcs_cont_layerpos_map.py")


def bank_split(family_id):
    """field 1 of family_id: the bank-internal prompt split (dev|heldout). RAISES if absent --
    a silently-missing field here would make both arms the same population."""
    p = family_id.split("|")
    if len(p) < 2 or p[1] not in ("dev", "heldout"):
        raise SystemExit("family_id %r has no dev/heldout field" % family_id)
    return p[1]


def build_filtered(mp, rows, inst, sites_all, layers_all, keep_doms, want_split, site, layer):
    sub = [r for r in rows if bank_split(r["family_id"]) == want_split]
    if not sub:
        raise SystemExit("no rows for bank split %r" % want_split)
    return axis.build(lpm, mp, sub, inst, sites_all, layers_all, keep_doms, site, layer)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", required=True)
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--readout", required=True)
    ap.add_argument("--site", default="rel-6")
    ap.add_argument("--layer", type=int, default=20)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    assign = lpm.load_split(); EX = set(lpm.EXCLUDED_DOMAINS)
    TR = {d for d, v in assign.items() if v == "train"} - EX
    inst, _, _ = lpm.load_installation(os.path.join(REPO, a.readout))
    mp, rows, csha = lpm.load_corpus(os.path.join(REPO, a.corpus), mmap=True)
    if any(assign.get(r["domain"]) == "test" for r in rows):
        raise SystemExit("REFUSING: corpus contains TEST rows")
    sites_all, layers_all = list(mp["sites"]), list(mp["layers"])

    keep = {r["domain"] for r in rows} & TR

    out = {"schema": "dcs_csi_prompt_transfer/1", "codeword": a.codeword, "site": a.site,
           "layer": a.layer, "fit_population": "TRAIN domains only",
           "n_train_domains": len(keep),
           "WHAT_THIS_IS_NOT": "NOT template generalisation -- the corpus has one template family "
                               "(example_position=near, role_style=plain on every row)"}

    res = {}
    for fit_on, score_on in (("dev", "heldout"), ("heldout", "dev")):
        Xa, ya, da, doa, _ = build_filtered(mp, rows, inst, sites_all, layers_all, keep,
                                            fit_on, a.site, a.layer)
        Xb, yb, db, dob, _ = build_filtered(mp, rows, inst, sites_all, layers_all, keep,
                                            score_on, a.site, a.layer)
        # within-fit-set LOO (the honest in-family number) and the cross-prompt transfer
        loo_rho, _ = axis.loo_rho(lpm, Xa, ya, da, doa)
        al = torch.linalg.solve(Xa @ Xa.T + axis.LAM * torch.eye(len(ya), dtype=torch.float64), ya)
        tr_rho = lpm.spearman((Xb @ Xa.T @ al).tolist(), yb.tolist())
        res["fit_%s_score_%s" % (fit_on, score_on)] = {
            "fit_rows": len(ya), "fit_domains": len(doa),
            "score_rows": len(yb), "score_domains": len(dob),
            "within_fit_loo_rho": round(loo_rho, 4),
            "cross_prompt_transfer_rho": round(tr_rho, 4),
            "retention": round(tr_rho / loo_rho, 4) if loo_rho else None}
        print("fit=%-8s score=%-8s  within-fit LOO rho=%+.4f   cross-prompt rho=%+.4f  (%d->%d rows)"
              % (fit_on, score_on, loo_rho, tr_rho, len(ya), len(yb)))

    out["results"] = res
    vals = [v["cross_prompt_transfer_rho"] for v in res.values()]
    loos = [v["within_fit_loo_rho"] for v in res.values()]
    out["summary"] = {"mean_cross_prompt_rho": round(sum(vals) / len(vals), 4),
                      "mean_within_fit_loo_rho": round(sum(loos) / len(loos), 4),
                      "mean_retention": round((sum(vals) / len(vals)) / (sum(loos) / len(loos)), 4)}
    outp = a.out or os.path.join(REPO, "reports/DCS_CSI_PROMPT_TRANSFER_%s.json" % a.codeword)
    json.dump(out, open(outp, "w"), indent=1)
    print("\nsummary:", json.dumps(out["summary"]))
    print("wrote", os.path.relpath(outp, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
