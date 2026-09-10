#!/usr/bin/env python3
"""N_B1: does a candidate add information BEYOND the inherited B1? Mandate sections 17, 27, 44.

B1 is registered in this phase as a NEGATIVE CONTROL, not a candidate (registry F0). It is
reproducible, context-sensitive and non-specific, which makes it exactly the right thing for a new
candidate to have to beat. Section 44 criterion 3 is "stronger than B1"; section 27 asks whether a
candidate "adds predictive information beyond B1 and surface features".

  B1(d, L) = < h_C(d,L) - h_A(d,L), vhat_lex(L) >,  v_lex = mean_domains[h_E - h_A],  ALL LOO,
             read at codeword_last on the SEMANTIC prompt (the inherited definition, unchanged).

The candidate's score is read on the BEHAVIOURAL prompt at its own site and layer. Mixing the two
populations is deliberate: the question is not "which prompt is better" but "does the candidate
tell you something about this DOMAIN that B1 does not already".

Reported: rho(candidate), rho(B1), and the partial correlation of each given the other. A candidate
whose partial collapses is re-describing B1.
"""
from __future__ import annotations
import argparse, glob, importlib.util, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location("lpm", os.path.join(REPO, "scripts",
                                                                "dcs_cont_layerpos_map.py"))
lpm = importlib.util.module_from_spec(_s); _s.loader.exec_module(lpm)
_s2 = importlib.util.spec_from_file_location("llc", os.path.join(REPO, "scripts",
                                                                 "dcs_cont_logitlens_control.py"))
llc = importlib.util.module_from_spec(_s2); _s2.loader.exec_module(llc)


def main() -> int:
    import torch
    ap = argparse.ArgumentParser()
    ap.add_argument("--beh-run", required=True)
    ap.add_argument("--readout-run", required=True)
    ap.add_argument("--b1-run", required=True, help="a codeword_last extraction with cells A,C,E")
    ap.add_argument("--site", default="cw_demo_mean")
    ap.add_argument("--layer", type=int, default=13)
    ap.add_argument("--b1-layer", type=int, default=12)
    ap.add_argument("--split", default="train", choices=["train", "validation"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    assign = lpm.load_split()
    inst, _, _ = lpm.load_installation(os.path.join(REPO, a.readout_run))
    keep = {d for d, s in assign.items() if s == a.split} - set(lpm.EXCLUDED_DOMAINS)

    # ---- B1, on the SEMANTIC prompt at codeword_last, exactly the inherited definition -------
    bd = os.path.join(REPO, a.b1_run)
    brows = [json.loads(l) for l in open(os.path.join(bd, "results.jsonl"), encoding="utf-8")]
    bc = torch.load(os.path.join(bd, "cache", "final_occurrence_reps.pt"), weights_only=False)
    if bc.get("position") != "codeword_last":
        raise lpm.Refusal("B1 must be read at codeword_last; %r is %r" % (a.b1_run, bc.get("position")))
    bli = bc["layers"].index(a.b1_layer)
    byk = {}
    for r in brows:
        if r.get("query_kind") != "semantic_one_word" or r.get("n_examples") != 4:
            continue
        if r["domain"] not in keep or r["cell"] not in ("A", "C", "E"):
            continue
        t = bc["reps"].get(r["prompt_id"])
        if t is not None:
            byk[((r["domain"], lpm.family_slot(r["family_id"])), r["cell"])] = t[bli].float()
    keys = sorted({k for (k, _) in byk})
    comp = [k for k in keys if all((k, c) in byk for c in ("A", "C", "E"))]
    doms = sorted({d for d, _ in comp})
    dCA, dEA = {}, {}
    for d in doms:
        ks = [k for k in comp if k[0] == d]
        dCA[d] = sum(byk[(k, "C")] - byk[(k, "A")] for k in ks) / len(ks)
        dEA[d] = sum(byk[(k, "E")] - byk[(k, "A")] for k in ks) / len(ks)
    tot = sum(dEA.values())
    b1 = []
    for d in doms:                      # LEAVE-ONE-DOMAIN-OUT lexical axis
        v = tot - dEA[d]
        nv = float(v.norm())
        b1.append(float(torch.dot(dCA[d], v)) / nv if nv > 0 else 0.0)

    # ---- the candidate, on the BEHAVIOURAL prompt at its own site/layer -----------------------
    mp, rows, bank_sha = lpm.load_corpus(os.path.join(REPO, a.beh_run))
    # ---- REVIEW-2/CODE-03: ENFORCE BANK AGREEMENT ON BOTH JOINS ------------------------- #
    # The corpus yielded bank_sha and it was never compared to anything. A basket readout
    # returned rho(candidate,y)=+0.6168 with exit 0, and a basket B1 run gave rho(B1,y)=+0.1900 --
    # silently changing the negative control this phase quotes as 0.092.
    _ro_sha, _ro_src = lpm.readout_bank_sha(os.path.join(REPO, a.readout_run))
    if _ro_sha != bank_sha:
        raise lpm.Refusal("BANK MISMATCH: corpus %s vs readout %s (%s)" % (bank_sha, _ro_sha, _ro_src))
    _b1_sha, _b1_src = lpm.readout_bank_sha(os.path.join(REPO, a.b1_run))
    if _b1_sha != bank_sha:
        raise lpm.Refusal("BANK MISMATCH: corpus %s vs B1 run %s (%s)" % (bank_sha, _b1_sha, _b1_src))
    print("[nb1] bank agreement: corpus %s == readout %s == B1 run %s" % (bank_sha, _ro_sha, _b1_sha))
    si, li = mp["sites"].index(a.site), mp["layers"].index(a.layer)
    ball = {}
    for r in rows:
        if r["domain"] not in keep:
            continue
        t = mp["reps"].get(r["prompt_id"])
        if t is not None:
            ball[((r["domain"], lpm.family_slot(r["family_id"])), r["cell"])] = t[si, li].float()
    k2 = sorted({k for (k, _) in ball})
    c2 = [k for k in k2 if all((k, c) in ball for c in ("A", "B", "C", "E"))]
    d2 = sorted({d for d, _ in c2})
    if d2 != doms:
        raise lpm.Refusal("B1 and candidate domain sets differ (%d vs %d)" % (len(doms), len(d2)))
    X, ys = [], []
    for d in doms:
        ks = [k for k in c2 if k[0] == d]
        cb = sum(ball[(k, "C")] - ball[(k, "B")] for k in ks) / len(ks)
        ea = sum(ball[(k, "E")] - ball[(k, "A")] for k in ks) / len(ks)
        X.append(cb + ea)                                  # the interaction
        ys.append(sum(inst[k] for k in ks) / len(ks))
    Xt = torch.stack(X, 0)
    cand = [float(v) for v in lpm.loo_scores(Xt, torch.tensor(ys, dtype=torch.float32))]

    r_c = lpm.spearman(cand, ys)
    r_b = lpm.spearman(b1, ys)
    r_cb = lpm.spearman(cand, b1)
    p_c = llc.partial_spearman(cand, ys, b1)
    p_b = llc.partial_spearman(b1, ys, cand)
    res = {"schema": "dcs_cont_nb1_control/1", "status": "EXPLORATORY", "split": a.split,
           "n_domains": len(doms), "site": a.site, "layer": a.layer, "b1_layer": a.b1_layer,
           "bank_file_sha16": bank_sha,
           "rho_candidate": r_c, "rho_B1": r_b, "rho_candidate_vs_B1": r_cb,
           "partial_candidate_given_B1": p_c, "partial_B1_given_candidate": p_b}
    op = os.path.join(REPO, a.out); os.makedirs(os.path.dirname(op), exist_ok=True)
    json.dump(res, open(op, "w", encoding="utf-8"), indent=1)
    print("[nb1] n=%d  site=%s L%d   B1 at codeword_last L%d" % (len(doms), a.site, a.layer, a.b1_layer))
    print("[nb1]   rho(candidate, y) = %+.4f" % r_c)
    print("[nb1]   rho(B1, y)        = %+.4f    <- the negative control" % r_b)
    print("[nb1]   rho(candidate, B1)= %+.4f" % r_cb)
    print("[nb1]   partial(candidate | B1) = %+.4f   %s"
          % (p_c, "ADDS beyond B1" if abs(p_c) > 0.5 * abs(r_c) else "COLLAPSES -> re-describes B1"))
    print("[nb1]   partial(B1 | candidate) = %+.4f" % p_b)
    print("[nb1] wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except lpm.Refusal as e:
        print("REFUSING: %s" % e, file=sys.stderr); raise SystemExit(2)
