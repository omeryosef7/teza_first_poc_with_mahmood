"""token_vs_prompt_level.py — are token-level and prompt-level Boombness the same object? (Phase 2)

THE BRIEF IS EXPLICIT: *"Do not merge token-level and prompt-level boombness. These are separate
objects and must be measured separately."* That is an instruction, not a finding — nothing in this
repo had ever measured whether they ARE separate. This does.

  TOKEN-LEVEL   how bomb-like is THIS codeword occurrence, at this layer/position?
  PROMPT-LEVEL  how much does the WHOLE prompt put the model into a mapped/attack-ready state?

They are computed from the same per-occurrence rows, so they are not independent by construction —
the question is whether the prompt-level aggregate carries anything the final-token reading does
not. Three outcomes, and they license different work:

  * r ~ 1.0        they are ONE object. A prompt-level "metric" is the final token wearing a hat,
                   and Phase 7 must not treat them as two candidate objectives.
  * r moderate     genuinely two objects; both are worth carrying into the objective gate.
  * r ~ 0          the aggregate is dominated by demo occurrences and says little about the query.

WHY THE ANSWER IS NOT OBVIOUS. A prompt with n_examples=8 has ~9 codeword occurrences; the final
query one is 1/9 of the mean. If the demo occurrences move together with the query occurrence the
mean is redundant; if they do not, the mean is measuring the demonstration block, not the query.
`n_examples=0` prompts have exactly ONE occurrence, where the two are identical by construction —
those are excluded from the correlation and reported separately, because including them would
manufacture agreement.

Scalars only in, scalars only out. No generation, no judge, no text.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FailureLedger, RunDir, read_jsonl  # noqa: E402

SCHEMA = "TOKEN_VS_PROMPT_LEVEL/1"


def spearman(xs: List[float], ys: List[float]) -> Optional[float]:
    """Rank correlation, average ranks for ties. No scipy in this environment."""
    n = len(xs)
    if n < 3:
        return None

    def ranks(v):
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    dx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    dy = math.sqrt(sum((b - my) ** 2 for b in ry))
    return (num / (dx * dy)) if dx > 0 and dy > 0 else None


def build_prompt_metrics(rows: List[Dict], field: str) -> Dict[str, Dict[str, Any]]:
    """Per prompt: the token-level reading and several prompt-level aggregates of the same field."""
    by: Dict[str, List[Dict]] = {}
    for r in rows:
        if r.get(field) is None:
            continue
        by.setdefault(r["prompt_id"], []).append(r)

    out = {}
    for pid, rs in by.items():
        rs = sorted(rs, key=lambda r: r.get("occurrence_index", 0))
        vals = [float(r[field]) for r in rs]
        final = next((float(r[field]) for r in rs if r.get("is_final_occurrence")), vals[-1])
        query = next((float(r[field]) for r in rs if r.get("is_query_occurrence")), None)
        demo = [float(r[field]) for r in rs if not r.get("is_query_occurrence")]
        out[pid] = {
            "n_occurrences": len(rs),
            "n_examples": rs[0].get("n_examples"),
            "domain": rs[0].get("domain"), "condition": rs[0].get("condition"),
            "split": rs[0].get("split"), "family_id": rs[0].get("family_id"),
            # TOKEN-LEVEL: the single occurrence the hypothesis is about
            "token_final": final,
            "token_query": query,
            # PROMPT-LEVEL candidates, all aggregates of the SAME per-occurrence field
            "prompt_mean": sum(vals) / len(vals),
            "prompt_max": max(vals),
            "prompt_last3_mean": sum(vals[-3:]) / len(vals[-3:]),
            "prompt_demo_mean": (sum(demo) / len(demo)) if demo else None,
        }
    return out


def analyse(rows: List[Dict], field: str) -> Dict[str, Any]:
    m = build_prompt_metrics(rows, field)
    multi = {k: v for k, v in m.items() if v["n_occurrences"] > 1}
    single = {k: v for k, v in m.items() if v["n_occurrences"] == 1}

    def corr(a: str, b: str, pool: Dict) -> Dict[str, Any]:
        xs, ys = [], []
        for v in pool.values():
            if v.get(a) is not None and v.get(b) is not None:
                xs.append(v[a])
                ys.append(v[b])
        return {"n": len(xs), "spearman": spearman(xs, ys)}

    pairs = [("token_final", "prompt_mean"), ("token_final", "prompt_max"),
             ("token_final", "prompt_last3_mean"), ("token_final", "prompt_demo_mean"),
             ("prompt_mean", "prompt_max")]
    return {
        "field": field,
        "n_prompts": len(m),
        "n_multi_occurrence": len(multi),
        "n_single_occurrence_EXCLUDED": len(single),
        "why_single_excluded": ("with one occurrence the token-level and prompt-level readings are "
                                "THE SAME NUMBER by construction; including them manufactures "
                                "agreement and would inflate every correlation below"),
        "correlations_multi_occurrence_only": {f"{a}~{b}": corr(a, b, multi) for a, b in pairs},
        "by_n_examples": {
            str(ne): {f"{a}~{b}": corr(a, b, {k: v for k, v in multi.items()
                                              if v["n_examples"] == ne})
                      for a, b in [("token_final", "prompt_mean")]}
            for ne in sorted({v["n_examples"] for v in multi.values() if v["n_examples"] is not None})
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--extract-dir", required=True)
    ap.add_argument("--fields", default="d_surface|L12|proj,d_surface|L8|proj,d_surface|L31|proj,"
                                        "ll|L12|boombness,ll|L31|boombness")
    ap.add_argument("--condition", default="natural_doublespeak")
    ap.add_argument("--query-kind", default="behavioral")
    ap.add_argument("--tag", default="tvp")
    args = ap.parse_args()

    rows = read_jsonl(os.path.join(args.extract_dir, "results.jsonl"))
    rows = [r for r in rows
            if (not args.condition or r.get("condition") == args.condition)
            and (not args.query_kind or r.get("query_kind") == args.query_kind)]
    ledger = FailureLedger()
    run = RunDir("token_vs_prompt_level", args, tag=args.tag)
    out = []
    for f in args.fields.split(","):
        r = analyse(rows, f.strip())
        out.append(r)
        run.log_row(r)
        c = r["correlations_multi_occurrence_only"]
        print(f"  {f.strip():24s} n_multi={r['n_multi_occurrence']:4d} "
              f"(excl {r['n_single_occurrence_EXCLUDED']} single)  "
              f"final~mean={c['token_final~prompt_mean']['spearman']}  "
              f"final~max={c['token_final~prompt_max']['spearman']}  "
              f"final~demo={c['token_final~prompt_demo_mean']['spearman']}")
        ledger.ok()

    res = {"schema": SCHEMA, "extract_dir": os.path.abspath(args.extract_dir),
           "condition": args.condition, "query_kind": args.query_kind, "fields": out,
           "READING_NOTE": (
               "A correlation near 1 means the prompt-level aggregate is the final token wearing a "
               "hat, and Phase 7 must NOT count them as two candidate objectives. Single-occurrence "
               "prompts are excluded because the two metrics are identical there by construction.")}
    p = os.path.join(run.path, "token_vs_prompt_level.json")
    with open(p, "w") as fh:
        json.dump(res, fh, indent=2, sort_keys=True)
    run.finish(summary={"n_fields": len(out)}, ledger=ledger)
    print(f"[tvp] wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
