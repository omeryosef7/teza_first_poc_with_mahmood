#!/usr/bin/env python3
"""Turn analyze_sweep SUMMARY jsons into the P2a deliverable: a rescue-vs-rank markdown table (+ ascii
plot) comparing basket vs button. GPU-free; reads only the SUMMARY_{split}.json files.

Usage:
  python make_rank_table.py --split train \
    --summaries reports/heretic_csi/hcsi_p2a_basket_SUMMARY_train.json:basket \
                reports/heretic_csi/hcsi_p2a_button_SUMMARY_train.json:button \
    --out reports/heretic_csi/RANK_TABLE_train.md
"""
from __future__ import annotations
import argparse, json, os


def verdict_tag(v: str) -> str:
    v = (v or "").upper()
    if "DOES NOT PASS" in v or "FAIL" in v: return "FAIL"
    if "PASS" in v and "NOT" not in v.split("PASS")[0][-6:]: return "PASS"
    if "INCONCLUSIVE" in v or "NOT a pass" in (v or ""): return "INCONCLUSIVE"
    if "CANNOT ANSWER" in v: return "CANNOT_ANSWER"
    return (v[:24] or "?")


def load(summ):
    d = json.load(open(summ))
    by_rank = {}
    for row in d.get("rows", []):
        by_rank[row.get("rank")] = row
    return d.get("codeword"), by_rank


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True)
    ap.add_argument("--summaries", nargs="+", required=True, help="path:label pairs")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    series = {}
    ranks = set()
    for spec in a.summaries:
        path, _, label = spec.partition(":")
        if not os.path.exists(path):
            print(f"WARN missing {path}"); continue
        cw, by_rank = load(path)
        series[label or cw] = by_rank
        ranks |= set(by_rank)
    ranks = sorted(r for r in ranks if r is not None)
    labels = list(series)
    lines = [f"# P2a rescue-vs-rank ({a.split})  —  recovery fraction (of whole-state) and verdict\n",
             "recovery = candidate recovery fraction of KO_FULL; verdict from the rank test vs the "
             "rank-matched 46+10 control family (floor 0.0213).\n"]
    header = "| rank | " + " | ".join(f"{l} recovery | {l} cand−ko | {l} verdict" for l in labels) + " |"
    sep = "|" + "---|" * (1 + 3 * len(labels))
    lines += [header, sep]
    for r in ranks:
        cells = [f"{r}"]
        for l in labels:
            row = series[l].get(r, {})
            rec = row.get("recovery_fraction")
            cmk = row.get("candidate_minus_ko")
            vt = verdict_tag(row.get("verdict"))
            cells += [f"{rec:.4f}" if isinstance(rec, (int, float)) else "—",
                      f"{cmk:+.4f}" if isinstance(cmk, (int, float)) else "—", vt]
        lines.append("| " + " | ".join(cells) + " |")
    # ascii plot of recovery vs rank per label
    lines.append("\n```")
    for l in labels:
        row = [f"{l:>8}:"]
        for r in ranks:
            rec = series[l].get(r, {}).get("recovery_fraction")
            row.append(f"r{r}={rec:.3f}" if isinstance(rec, (int, float)) else f"r{r}=—")
        lines.append(" ".join(row))
    lines.append("```")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    open(a.out, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print("\nwrote", a.out)


if __name__ == "__main__":
    main()
