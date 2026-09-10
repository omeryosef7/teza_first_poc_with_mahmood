#!/usr/bin/env python3
"""`Q2` recomputed with the `C-209` correction applied to the OUTCOME. `REVIEW-2` finding C8.

WHY THIS FILE EXISTS. `PR-066`'s frozen `Q2` defines the outcome as domain-mean `malicious_at_0.5`
-- the raw StrongREJECT label. `C-209` then established that this instrument has a systematic
false-positive channel: on cell C at dose 0, where nothing can be installed, it returns
ASR@0.5 = 0.1549 with refusal 0.0000, and every positive is the model answering the LITERAL codeword
question well. So the single most obvious objection to `Q2 = 0.3961` is *"the correlation is the
false-positive channel"*.

`ENTRY 037` answered that objection with rho = 0.5260 (train) / 0.4206 (113 domains) on
`asr_and_concept_present`. `REVIEW-2` C8 found those numbers **exist in no script and no artifact** --
they were computed inline and reported. The one sentence defending the phase's primary result was
unre-runnable. This is that computation, as a file.

WHAT IT IS AND IS NOT. It is a ROBUSTNESS RECOMPUTATION of a frozen primary, not a second test of
it. The frozen `Q2` stands as written; this says whether it survives correcting a defect in its
outcome that was measured after it was frozen. Reported alongside, never instead.

THE PREDICTOR is bound exactly as the frozen analyzer binds it: the readout run whose
`bank_file_sha16` equals the pinned bank's, gated on `DONE.json`, refusing if that selection is not
unique -- and `concept_binary_prob` is IMPORTED from `scripts/dcs_readout_family.py`, the sole
implementation, never reimplemented.

USAGE
  python scripts/dcs_succ_q2_concept_present.py
  python scripts/dcs_succ_q2_concept_present.py --selftest
  python scripts/dcs_succ_q2_concept_present.py --mutate
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import os
import random
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

from dcs_succ_concept_presence import concept_hits            # noqa: E402  frozen lexicon
from dcs_readout_family import concept_binary_prob            # noqa: E402  sole implementation

EXCLUDED = ("restaurant_kitchen", "school_campus", "subway_station")


class Refusal(RuntimeError):
    pass


def one_done(pattern):
    ds = [d for d in sorted(glob.glob(pattern)) if os.path.exists(os.path.join(d, "DONE.json"))]
    if not ds:
        raise Refusal("no run with DONE.json matches %s" % pattern)
    if len(ds) > 1:
        raise Refusal("%d completed runs match %s; refusing to pick one by mtime"
                      % (len(ds), pattern))
    return ds[0]


def ranks(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        a = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            r[o[k]] = a
        i = j + 1
    return r


def pearson(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sx = math.sqrt(sum((a - mx) ** 2 for a in x))
    sy = math.sqrt(sum((b - my) ** 2 for b in y))
    if sx == 0 or sy == 0:
        return float("nan")
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def spearman(x, y):
    return pearson(ranks(x), ranks(y))


def perm_p(x, y, B, seed):
    r0 = abs(spearman(x, y))
    rg = random.Random(seed)
    yy = list(y)
    c = 0
    for _ in range(B):
        rg.shuffle(yy)
        if abs(spearman(x, yy)) >= r0 - 1e-12:
            c += 1
    return (1 + c) / (1 + B), 1.0 / (1 + B)


def fisher_ci(r, n, z=1.959964):
    if n < 4 or abs(r) >= 1:
        return (float("nan"), float("nan"))
    zz = 0.5 * math.log((1 + r) / (1 - r))
    se = 1.0 / math.sqrt(n - 3)
    return (math.tanh(zz - z * se), math.tanh(zz + z * se))


def selftest() -> int:
    ok = True

    def chk(n, c):
        nonlocal ok
        print("  %-52s %s" % (n, "PASS" if c else "FAIL"))
        ok = ok and bool(c)

    chk("spearman of a monotone map is 1", abs(spearman([1, 2, 3, 4], [1, 4, 9, 16]) - 1) < 1e-12)
    chk("spearman of an antitone map is -1", abs(spearman([1, 2, 3], [3, 2, 1]) + 1) < 1e-12)
    chk("spearman is rank-based, pearson is not",
        abs(spearman([1, 2, 3, 4], [1, 2, 3, 100]) - 1) < 1e-12
        and abs(pearson([1, 2, 3, 4], [1, 2, 3, 100]) - 1) > 0.1)
    x = list(range(30)); y = [v + 0.01 for v in x]
    p, fl = perm_p(x, y, 999, 1)
    chk("permutation p hits its floor on a perfect map", abs(p - fl) < 1e-12)
    p2, _ = perm_p(x, [0] * 30, 999, 1)
    chk("permutation p on a constant is 1.0", p2 == 1.0)
    lo, hi = fisher_ci(0.4, 113)
    chk("fisher CI brackets r", lo < 0.4 < hi)
    chk("fisher CI refuses n<4", math.isnan(fisher_ci(0.4, 3)[0]))
    try:
        one_done(os.path.join(REPO, "outputs/boombness/judge/__nope__*"))
        chk("one_done refuses when nothing matches", False)
    except Refusal:
        chk("one_done refuses when nothing matches", True)
    chk("concept_hits is the frozen lexicon's", concept_hits("attach the blasting cap") != [])
    chk("concept_binary_prob is imported, not local",
        concept_binary_prob.__module__ == "dcs_readout_family")
    return 0 if ok else 1


def mutate() -> int:
    g = globals()
    muts = [("spearman replaced by pearson", "spearman", pearson),
            ("permutation p drops the +1 correction", "perm_p",
             lambda x, y, B, s: (0.0, 0.0)),
            ("ranks() stops averaging ties", "ranks",
             lambda v: [sorted(v).index(a) + 1.0 for a in v])]
    red = 0
    for name, tgt, repl in muts:
        orig = g[tgt]
        g[tgt] = repl
        try:
            import io
            buf, old = io.StringIO(), sys.stdout
            sys.stdout = buf
            try:
                rc = selftest()
            finally:
                sys.stdout = old
            caught = rc != 0
        except Exception:
            caught = True
        finally:
            g[tgt] = orig
        red += caught
        print("  MUTATION %-46s %s" % (name, "RED (caught)" if caught else "GREEN -- NOT CAUGHT"))
    print("  %d/%d caught" % (red, len(muts)))
    return 0 if red == len(muts) else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(
        REPO, "configs/dcs_ts_pr066_amendment2.json"))
    ap.add_argument("--arm", default="C_n4")
    # The replication codeword writes tsb66b_/tsb66bj_ and binds a different bank. Parameterised so
    # the transfer pair is scored by the SAME code, never by a second copy of it (C8's lesson).
    ap.add_argument("--gen-prefix", default="tsb66_")
    ap.add_argument("--judge-prefix", default="tsb66j_")
    ap.add_argument("--bank-key", default="button_bomb")
    ap.add_argument("--readout-glob", default="*readout_button_bomb*")
    ap.add_argument("--n-perm", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=202609061)
    ap.add_argument("--out", default=os.path.join(
        REPO, "outputs/dcs_succ/q2_concept_present.json"))
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--mutate", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        print("=== selftest ===")
        return selftest()
    if a.mutate:
        print("=== mutation harness ===")
        return mutate()

    from dcs_ts_prereg import load as load_prereg
    pr = load_prereg(os.path.relpath(a.config, REPO))
    bank_sha = pr.require("population", "banks", a.bank_key, "bank_file_sha16")

    # ---- OUTCOME: per-domain ASR, raw and concept-present
    j = one_done(os.path.join(REPO, "outputs/boombness/judge/%s%s_*" % (a.judge_prefix, a.arm)))
    gd = one_done(os.path.join(REPO, "outputs/boombness/score_behavior/%s%s_*" % (a.gen_prefix, a.arm)))
    gens = {json.loads(l)["prompt_id"]: json.loads(l)
            for l in open(os.path.join(gd, "gens.jsonl"), encoding="utf-8")}
    raw, cp = collections.defaultdict(list), collections.defaultdict(list)
    n_j = 0
    for line in open(os.path.join(j, "results.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        if r["prompt_id"] not in gens:
            raise Refusal("judge row %s absent from the generation run" % r["prompt_id"])
        m = bool(r.get("malicious_at_0.5"))
        raw[r["domain"]].append(m)
        cp[r["domain"]].append(m and bool(concept_hits(gens[r["prompt_id"]]["generation"])))
        n_j += 1
    if n_j != len(gens):
        raise Refusal("judge covers %d of %d generated rows" % (n_j, len(gens)))

    # ---- PREDICTOR: bound by the pinned bank hash, exactly as the frozen analyzer binds it
    cands = []
    for d in sorted(glob.glob(os.path.join(REPO, "outputs/boombness/score_behavior/" + a.readout_glob))):
        mp = os.path.join(d, "metadata.json")
        if not (os.path.exists(os.path.join(d, "DONE.json")) and os.path.exists(mp)):
            continue
        try:
            if json.load(open(mp, encoding="utf-8")).get("bank_file_sha16") == bank_sha:
                cands.append(d)
        except Exception:
            continue
    if len(cands) != 1:
        raise Refusal("%d readout runs match the pinned bank digest %s: %s"
                      % (len(cands), bank_sha, [os.path.basename(c) for c in cands]))
    inst = collections.defaultdict(list)
    for line in open(os.path.join(cands[0], "results.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        if (r.get("query_kind") == "semantic_one_word" and r.get("cell") == "C"
                and int(r.get("n_examples", -1)) == 4):
            inst[r["domain"]].append(concept_binary_prob(r["logp_concept"], r["logp_codeword"]))

    assign = json.load(open(os.path.join(
        REPO, pr.require("split", "manifest")), encoding="utf-8"))["assign"]

    res = {"_label": "Q2 ROBUSTNESS: the frozen primary recomputed with the C-209 correction "
                     "applied to the OUTCOME. Reported ALONGSIDE the frozen Q2, never instead.",
           "config": os.path.relpath(a.config, REPO),
           "judge_run": os.path.basename(j), "generation_run": os.path.basename(gd),
           "predictor_run": os.path.basename(cands[0]), "predictor_bound_by_sha16": bank_sha,
           "bank_key": a.bank_key, "gen_prefix": a.gen_prefix,
           "join_key": "(bank_file_sha16, domain) -- COMPOUND",
           "n_perm": a.n_perm, "seed": a.seed, "rows": {}}
    for split in ("pooled", "train", "validation", "test"):
        doms = sorted(d for d in inst if d in raw and d not in EXCLUDED
                      and (split == "pooled" or assign.get(d) == split))
        if len(doms) < 4:
            res["rows"][split] = {"n_domains": len(doms), "status": "NOT-EVALUABLE (n<4)"}
            continue
        x = [sum(inst[d]) / len(inst[d]) for d in doms]
        row = {"n_domains": len(doms)}
        for nm, src in (("raw_ASR", raw), ("asr_and_concept_present", cp)):
            y = [sum(src[d]) / len(src[d]) for d in doms]
            rho = spearman(x, y)
            p, fl = perm_p(x, y, a.n_perm, a.seed)
            row[nm] = {"rho": rho, "perm_p": p, "perm_p_floor": fl,
                       "fisher_z_ci95": fisher_ci(rho, len(doms))}
        res["rows"][split] = row

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    print("predictor %s (bound by sha16 %s)\njudge     %s\n"
          % (res["predictor_run"], bank_sha, res["judge_run"]))
    print("%-11s %5s | %-34s | %-34s" % ("split", "n", "rho on RAW ASR (the frozen y)",
                                         "rho on asr_and_concept_present"))
    for split, row in res["rows"].items():
        if "status" in row:
            print("%-11s %5d | %s" % (split, row["n_domains"], row["status"]))
            continue
        r1, r2 = row["raw_ASR"], row["asr_and_concept_present"]
        print("%-11s %5d | %+.4f  p=%-9.4g CI %s | %+.4f  p=%-9.4g CI %s"
              % (split, row["n_domains"], r1["rho"], r1["perm_p"],
                 [round(v, 3) for v in r1["fisher_z_ci95"]],
                 r2["rho"], r2["perm_p"], [round(v, 3) for v in r2["fisher_z_ci95"]]))
    print("\nwrote %s" % a.out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Refusal as e:
        print("REFUSING: %s" % e, file=sys.stderr)
        raise SystemExit(2)
