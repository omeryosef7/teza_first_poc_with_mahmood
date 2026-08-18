"""external_bank.py — turn an external harmful set into bank-format rows (plan §14).

WHY THIS EXISTS. Every ASR number in this sprint comes from the sprint's OWN prompt generator. That
is a real threat to the headline causal results: the report already concedes the arm-F gain is
largest on `benign_remap`, the condition where the carrot->bomb mapping is NEVER TAUGHT (+0.267) —
which is the signature of a prompt-bank artifact rather than a mechanism. ClearHarm is already
integrated in this repo (`data/clearharm/`, `data/manifests/`) and plan §14 asks for it; the sprint
never used it and never said so.

This is deliberately the SMALLEST possible adapter: it emits rows in exactly the schema
`score_behavior.py` already consumes, so the interventions, the judge, the coherence gate and the
domain-clustered inference all run unchanged. No new scoring path, no new analysis script.

WHAT IT DOES NOT DO. It does not wrap the external instructions in the doublespeak template — that
would need a demonstration pool per behaviour and a codeword whose tokenization is audited for each
one, which plan §2.2 requires and which is a much larger piece of work. So this arm answers exactly
one question: does an intervention fitted on the sprint's bank still move attack success on harmful
requests the bank never generated? A positive answer does not establish the doublespeak mechanism;
a negative answer does undercut it.

CLUSTERING. `domain` is set from the source's own category so the existing domain-clustered
inference has real units. The imbalance is reported rather than smoothed: ClearHarm's 179 rows are
127 `other_uncategorized` against five small categories, so its clustered interval is dominated by
one cluster. `data/manifests/heldout_495.csv` (AdvBench) carries 12 well-populated categories and is
the better-clustered companion; run both and compare rather than picking the flattering one.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SOURCES = {
    "clearharm": ("data/clearharm/clearharm_179.csv", "instruction", "category"),
    "advbench_heldout": ("data/manifests/heldout_495.csv", "instruction", "category"),
}


def build(path: str, text_col: str, cat_col: str, source: str, limit: int = 0):
    rows = list(csv.DictReader(open(path)))
    if limit:
        rows = rows[:limit]
    out = []
    for i, r in enumerate(rows):
        instr = (r.get(text_col) or "").strip()
        if not instr:
            continue
        sha = hashlib.sha256(instr.encode()).hexdigest()[:16]
        cat = (r.get(cat_col) or "uncategorized").strip() or "uncategorized"
        out.append({
            # identity
            "prompt_id": f"{source}:{sha}",
            "prompt_sha16": sha,
            "family_id": f"{source}|{cat}|{sha}",
            # the external instruction, VERBATIM -- no added framing, so the number is comparable
            # with any other evaluation of this set rather than only with this repo's runs.
            "full_prompt": instr,
            "condition": f"{source}_direct",
            "cell": "external_direct",
            "domain": cat,
            "split": "heldout" if (int(sha, 16) % 2) else "dev",
            "bank_block": "external",
            "query_kind": "behavioral",
            # no codeword exists in an external harmful set; declaring 0 is what lets the
            # occurrence gate pass honestly rather than being bypassed with a flag.
            "target_surface": "",
            "n_target_occurrences": 0,
            "n_examples": 0,
            "strength": "none", "consistency": "none", "example_position": "none",
            "role_style": "plain",
            # unused for behavioral rows, but score_behavior reads them off row 0 to build the
            # forward-readout option sets; keep the sprint's pair so the run is self-describing.
            "concept": "bomb", "codeword": "carrot",
            "source_dataset": source, "source_file": path,
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default="clearharm", choices=sorted(SOURCES))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    path, tcol, ccol = SOURCES[args.source]
    rows = build(path, tcol, ccol, args.source, args.limit)
    if not rows:
        raise SystemExit(f"[external_bank] no rows built from {path}")
    with open(args.out, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    doms = {}
    for r in rows:
        doms[r["domain"]] = doms.get(r["domain"], 0) + 1
    biggest = max(doms.values()) / len(rows)
    print(f"[external_bank] {args.source}: {len(rows)} rows -> {args.out}")
    print(f"[external_bank] {len(doms)} clusters; largest holds {biggest:.1%} of rows")
    for d, n in sorted(doms.items(), key=lambda kv: -kv[1]):
        print(f"    {n:>4d}  {d}")
    if biggest > 0.5:
        print(f"[external_bank] WARNING: one cluster holds {biggest:.1%} of the rows. A "
              f"domain-clustered interval on this set is dominated by it; report it beside a "
              f"better-clustered set rather than alone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
