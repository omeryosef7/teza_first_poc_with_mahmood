#!/usr/bin/env python3
"""The N_surface floor, ACTUALLY COMPUTED. Continuation mandate sections 6, 13, 44.

WHY THIS FILE EXISTS
--------------------
`CONT-ENTRY 003 §F` and `CONT-ENTRY 006 §4` both call N_surface "a measured floor, LOO r = 0.526".
REVIEW-1/T1-2 established that **no script and no artifact backed that number** -- the only
surface-floor artifact in the repo targets `B1`, not `y_install`, and its LOO CV R^2 are negative.
The value may have been a transcription of an unrelated correlation. Until the floor is computed,
the mandate section 44 gate "a candidate must beat surface" is not enforceable, so this computes it.

COMPARABILITY IS THE WHOLE POINT
--------------------------------
A floor is only a floor if it is the SAME statistic as the thing it gates. This file therefore
reuses `dcs_cont_layerpos_map.loo_scores` and `.spearman` verbatim and runs the identical pipeline
-- per-domain feature vector -> leave-one-domain-out covariance direction -> score the held-out
domain -> Spearman against y_install -- differing ONLY in what the per-domain vector contains:
surface counts computed from the prompt TEXT, with no model and no hidden state.

It also reports the same family-wise permutation null, so "beats the floor" and "beats noise" are
measured on one scale.

DISCIPLINE
  * TRAIN domains only. EXPLORATORY.
  * The feature list and both lexicons are written out in full below and are frozen by being in
    this file; they were not chosen by looking at which features predicted y.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_spec = importlib.util.spec_from_file_location(
    "lpm", os.path.join(REPO, "scripts", "dcs_cont_layerpos_map.py"))
lpm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lpm)

HEDGES = ("may", "might", "could", "perhaps", "possibly", "seems", "appears", "likely",
          "apparently", "somewhat", "roughly", "about", "around")
MODALS = ("can", "could", "may", "might", "must", "shall", "should", "will", "would")
HARM = ("threat", "threats", "threatening", "threatened", "attack", "attacked", "attacker",
        "terror", "terrorism", "terrorist", "sabotage", "hoax", "scare", "danger", "dangerous",
        "hazard", "hazardous", "unsafe", "risk", "risks", "risky", "emergency", "evacuate",
        "evacuated", "evacuation", "alarm", "alarms", "alert", "alerted", "lockdown", "police",
        "security", "patrol", "squad", "disposal", "defuse", "defused", "cordon", "suspicious",
        "explosion", "blast", "detonate", "detonated", "casualty", "casualties", "injured")

FEATURES = ("n_chars", "n_words", "n_sentences", "mean_sent_len", "hedge_per_100w",
            "modal_per_100w", "harm_per_100w", "punct_per_100c", "type_token_ratio",
            "digit_per_100c", "upper_per_100c", "n_newlines")


def surface_vector(text: str):
    words = re.findall(r"[A-Za-z']+", text)
    lw = [w.lower() for w in words]
    nw = max(1, len(words))
    nc = max(1, len(text))
    sents = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    return [
        float(len(text)),
        float(len(words)),
        float(len(sents)),
        float(nw) / max(1, len(sents)),
        100.0 * sum(1 for w in lw if w in HEDGES) / nw,
        100.0 * sum(1 for w in lw if w in MODALS) / nw,
        100.0 * sum(1 for w in lw if w in HARM) / nw,
        100.0 * sum(1 for ch in text if ch in ".,;:!?'\"()-") / nc,
        float(len(set(lw))) / nw,
        100.0 * sum(1 for ch in text if ch.isdigit()) / nc,
        100.0 * sum(1 for ch in text if ch.isupper()) / nc,
        float(text.count("\n")),
    ]


def main() -> int:
    import torch
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", default="data/boombness_prompts/"
                                      "boombness_prompt_bank_ts116m_button_bomb.jsonl")
    ap.add_argument("--readout-run", required=True)
    ap.add_argument("--query-kind", default="behavioral",
                    help="the population the PREDICTOR is read on, so the floor is computed on "
                         "the same prompts the representation is")
    ap.add_argument("--split", default="train", choices=["train", "validation"])
    ap.add_argument("--n-perm", type=int, default=200)
    ap.add_argument("--seed", type=int, default=20260910)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    # ---- REVIEW-2/CODE-03: ENFORCE BANK AGREEMENT -------------------------------------- #
    # This script had no bank check at all. Executed by the reviewer: a BASKET bank against a
    # BUTTON readout returned rho=+0.1791 with exit 0; button_gun gave 0.0884 and button_knife
    # -0.0297. The never-pool-button-and-basket rule was unenforced in one of the two scripts that
    # produce the section 44 gate numbers, and a silently wrong N_surface is a silently LOWER
    # floor -- permissive in exactly the direction that admits a bad candidate.
    import hashlib
    _bank_path = os.path.join(REPO, a.bank)
    with open(_bank_path, "rb") as _fh:
        _bank_sha = hashlib.sha256(_fh.read()).hexdigest()[:16]
    _ro_sha, _ro_src = lpm.readout_bank_sha(os.path.join(REPO, a.readout_run))
    if _bank_sha != _ro_sha:
        raise lpm.Refusal("BANK MISMATCH: --bank hashes to %s but the readout run is %s (from %s). "
                          "button and basket are never pooled." % (_bank_sha, _ro_sha, _ro_src))
    print("[surface] bank agreement: %s == %s (%s)" % (_bank_sha, _ro_sha, _ro_src))
    assign = lpm.load_split()
    inst, n_inst, kinds = lpm.load_installation(os.path.join(REPO, a.readout_run))
    keep = {d for d, s in assign.items() if s == a.split} - set(lpm.EXCLUDED_DOMAINS)

    per_key = {}
    with open(os.path.join(REPO, a.bank), encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("query_kind") != a.query_kind or r.get("n_examples") != 4:
                continue
            if r.get("cell") != "C" or r.get("domain") not in keep:
                continue
            k = (r["domain"], lpm.family_slot(r["family_id"]))
            if k in per_key:
                raise lpm.Refusal("surface key %r binds two rows" % (k,))
            per_key[k] = surface_vector(r["full_prompt"])

    doms = sorted({d for d, _ in per_key})
    missing = [k for k in per_key if k not in inst]
    if missing:
        raise lpm.Refusal("%d keys have surface features but no installation target" % len(missing))

    X, ys = [], []
    for d in doms:
        ks = [k for k in per_key if k[0] == d]
        v = [sum(per_key[k][i] for k in ks) / len(ks) for i in range(len(FEATURES))]
        X.append(v)
        ys.append(sum(inst[k] for k in ks) / len(ks))
    n = len(doms)
    Xt = torch.tensor(X, dtype=torch.float32)
    # z-score each feature so the covariance direction is not dominated by n_chars' scale.
    mu = Xt.mean(0, keepdim=True)
    sd = Xt.std(0, keepdim=True).clamp_min(1e-8)
    Xz = (Xt - mu) / sd
    yt = torch.tensor(ys, dtype=torch.float32)

    scores = [float(v) for v in lpm.loo_scores(Xz, yt)]
    rho = lpm.spearman(scores, ys)

    g = torch.Generator().manual_seed(a.seed)
    Yp = torch.stack([yt[torch.randperm(n, generator=g)] for _ in range(a.n_perm)], 0)
    S = lpm.loo_scores(Xz, Yp)
    null = sorted(abs(lpm.spearman([float(v) for v in S[b]], [float(z) for z in Yp[b]]))
                  for b in range(a.n_perm))
    p95 = null[int(0.95 * len(null))]
    # per-feature univariate Spearman, for the record
    uni = {FEATURES[i]: lpm.spearman([float(Xt[j, i]) for j in range(n)], ys)
           for i in range(len(FEATURES))}

    res = {"schema": "dcs_cont_surface_floor/1", "status": "EXPLORATORY",
           "bank": a.bank, "readout_run": a.readout_run, "query_kind": a.query_kind,
           "split": a.split, "n_domains": n, "n_features": len(FEATURES),
           "features": list(FEATURES),
           "hedges": list(HEDGES), "modals": list(MODALS), "harm_lexicon": list(HARM),
           "statistic": ("identical pipeline to dcs_cont_layerpos_map: per-domain vector -> "
                         "leave-one-domain-out covariance direction -> score held-out domain -> "
                         "Spearman vs y_install"),
           "rho_loo_surface": rho,
           "permutation_null": {"n_perm": a.n_perm, "seed": a.seed, "p95_abs_rho": p95,
                                "beats_own_null": bool(abs(rho) > p95)},
           "univariate_spearman": uni,
           "installation_rows_used": n_inst, "installation_channels_present": kinds}
    out = os.path.join(REPO, a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, "w", encoding="utf-8"), indent=1)

    print("[surface] n_domains=%d features=%d query_kind=%s split=%s"
          % (n, len(FEATURES), a.query_kind, a.split))
    print("[surface] N_surface  rho_loo = %+.4f   (own permutation p95 = %.4f, beats it: %s)"
          % (rho, p95, abs(rho) > p95))
    print("[surface] strongest univariate features: %s"
          % ", ".join("%s=%+.3f" % (k, v) for k, v in
                      sorted(uni.items(), key=lambda kv: -abs(kv[1]))[:5]))
    print("[surface] wrote %s" % a.out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except lpm.Refusal as e:
        print("REFUSING: %s" % e, file=sys.stderr)
        raise SystemExit(2)
