"""phase7_gate_38dom.py — the §12.27 gate test, WRITTEN BEFORE THE OUTCOME EXISTED.

Pre-specifying the analysis code, not just the rule in prose. Committed while `d38beh` was still
generating and no ASR verdict existed, so the decision rule cannot be tuned to the result.

THE RULE (§12.27 as amended by §12.27.1):

  P = partial rank correlation of `d_surface|L8|proj` with ASR, controlling d_naive, d_context,
      n_examples, length and refusal, on the 32 domains the directions were NOT fitted on.

  PASS requires all three:
    1. P is non-zero      -- null-imposed WILD cluster bootstrap over domains, p < 0.05.
                             The pairs bootstrap is not trusted at k=32 (§12.27.1).
    2. |P| >= 0.10        -- declared usefulness floor. A judgment, not a statistical threshold.
    3. no degradation     -- bootstrap CI of (P_unseen - P_seen) contains zero.
  FAIL otherwise. A large P with an interval containing zero is a FAIL, not a promising signal.

  POSITIVE CONTROL, which decides what a fail MEANS: the same statistic for `d_naive`.
    d_naive transfers, d_surface does not  -> the failure is about boombness.
    NEITHER transfers                      -> "untestable on this bank"; the design cannot speak
                                              to the objective question at all.

Reads judged rows and extract rows. No model, no GPU, no network.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import clustered_stats as cs  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
#: the 6 domains the directions in full_20260816_185942_1008673 were fitted on
FIT_DOMAINS = {"city_bridge", "farm_storage", "game_manual",
               "instructional", "lab_safety", "news_report"}
CANDIDATE = "d_surface|L8|proj"
NAIVE = "d_naive|L8|proj"
CONTEXT = "d_context|L8|proj"
USEFULNESS_FLOOR = 0.10


def load(extract_dir: str, judge_tag: str, gens_dir: str) -> list[dict]:
    B = {}
    for line in open(os.path.join(extract_dir, "results.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        if (r.get("is_query_occurrence") and r.get("condition") == "natural_doublespeak"
                and r.get("query_kind") == "behavioral"
                and r.get("bank_block") in ("core2x2", "core2x2_slot3")):
            B[r["prompt_id"]] = r
    G = {}
    for line in open(os.path.join(gens_dir, "gens.jsonl"), encoding="utf-8"):
        g = json.loads(line)
        G[g["prompt_id"]] = g
    jd = sorted(glob.glob(os.path.join(ROOT, "outputs", "boombness", "judge", judge_tag + "_*")))[-1]
    rows = []
    for line in open(os.path.join(jd, "results.jsonl"), encoding="utf-8"):
        j = json.loads(line)
        b, g = B.get(j["prompt_id"]), G.get(j["prompt_id"])
        if not b or not g:
            continue
        rows.append({"dom": b["domain"], "seen": b["domain"] in FIT_DOMAINS,
                     "y": float(bool(j["malicious_at_0.5"])),
                     "cand": b[CANDIDATE], "naive": b[NAIVE], "ctx": b[CONTEXT],
                     "nex": float(j["n_examples"]), "ln": float(g["n_new_tokens"]),
                     "rf": float(bool(j.get("refused")))})
    return rows


def partial(rows, key, controls):
    return cs.multi_partial_spearman([r[key] for r in rows], [r["y"] for r in rows],
                                     [[r[c] for r in rows] for c in controls])


def evaluate(rows: list[dict], key: str, label: str) -> dict:
    ctrls = [c for c in ("naive", "ctx", "nex", "ln", "rf") if c != key]
    unseen = [r for r in rows if not r["seen"]]
    seen = [r for r in rows if r["seen"]]
    p_unseen = partial(unseen, key, ctrls)
    p_seen = partial(seen, key, ctrls) if len(seen) > 10 else float("nan")

    for r in rows:
        r["__y"] = r["y"]
    t, pval = cs.wild_cluster_bootstrap_p(unseen, lambda r: r["dom"], key, "y",
                                          control_keys=ctrls, n_boot=4000)
    # difference bootstrap, resampling domains within each half
    rng = random.Random(0)
    du = collections.defaultdict(list)
    ds = collections.defaultdict(list)
    for r in unseen:
        du[r["dom"]].append(r)
    for r in seen:
        ds[r["dom"]].append(r)
    ku, ksd = sorted(du), sorted(ds)
    diffs = []
    for _ in range(2000):
        ru = [x for k in (rng.choice(ku) for _ in ku) for x in du[k]]
        rs = [x for k in (rng.choice(ksd) for _ in ksd) for x in ds[k]]
        a, b = partial(ru, key, ctrls), partial(rs, key, ctrls)
        if a == a and b == b:
            diffs.append(a - b)
    diffs.sort()
    dlo, dhi = (diffs[int(.025 * len(diffs))], diffs[int(.975 * len(diffs))]) if diffs else (
        float("nan"), float("nan"))
    return {"label": label, "n_unseen": len(unseen), "k_unseen": len(ku),
            "P_unseen": p_unseen, "P_seen": p_seen, "wild_t": t, "wild_p": pval,
            "diff_lo": dlo, "diff_hi": dhi}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extract-dir", required=True)
    ap.add_argument("--gens-dir", required=True)
    ap.add_argument("--judge-tag", required=True)
    a = ap.parse_args()
    rows = load(a.extract_dir, a.judge_tag, a.gens_dir)
    print(f"[gate] {len(rows)} joined rows; "
          f"{len({r['dom'] for r in rows if not r['seen']})} unseen domains, "
          f"{len({r['dom'] for r in rows if r['seen']})} seen; "
          f"successes {sum(r['y'] for r in rows):.0f}")
    res = [evaluate(rows, "cand", "d_surface (CANDIDATE)"),
           evaluate(rows, "naive", "d_naive (POSITIVE CONTROL)")]
    for r in res:
        print(f"\n  {r['label']}")
        print(f"    P_unseen = {r['P_unseen']:+.4f}  (n={r['n_unseen']}, k={r['k_unseen']})   "
              f"P_seen = {r['P_seen']:+.4f}")
        print(f"    wild cluster bootstrap: t={r['wild_t']:+.3f}  p={r['wild_p']:.4f}")
        print(f"    (P_unseen - P_seen) 95% CI [{r['diff_lo']:+.4f}, {r['diff_hi']:+.4f}]"
              f"  -> {'no detectable degradation' if r['diff_lo'] <= 0 <= r['diff_hi'] else 'DEGRADES'}")
    c, n = res
    c1 = c["wild_p"] < 0.05
    c2 = abs(c["P_unseen"]) >= USEFULNESS_FLOOR
    c3 = c["diff_lo"] <= 0 <= c["diff_hi"]
    print(f"\n[gate] condition 1 (non-zero, wild p<0.05):        {'PASS' if c1 else 'FAIL'}")
    print(f"[gate] condition 2 (|P_unseen| >= {USEFULNESS_FLOOR}):          {'PASS' if c2 else 'FAIL'}")
    print(f"[gate] condition 3 (no degradation vs seen):       {'PASS' if c3 else 'FAIL'}")
    verdict = c1 and c2 and c3
    print(f"[gate] PHASE 7 GATE: {'PASSES' if verdict else 'CLOSED'}")
    if not verdict:
        if n["wild_p"] >= 0.05:
            print("[gate] POSITIVE CONTROL ALSO FAILS -> read as 'UNTESTABLE ON THIS BANK': neither "
                  "direction transfers to unseen domains, so this design cannot speak to the "
                  "objective question.")
        else:
            print("[gate] positive control TRANSFERS while the candidate does not -> the failure is "
                  "about boombness, which is the answer Phase 7 asks for.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
