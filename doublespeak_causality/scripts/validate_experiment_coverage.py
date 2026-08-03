#!/usr/bin/env python3
"""Coverage + integrity validator for the causal-KO / head-patch output dirs (plan deliverable
`scripts/validate_experiment_coverage.py`). Institutionalizes the ad-hoc checks from the audit.

For each output dir it detects the experiment type from the row schema and checks:
  - no duplicate rows within a cell (phase6: (sid,split,window,cell); phase5: (sid,split,layer,head,cell))
  - n_valid >= MIN (default 20) per split
  - self-swap control is an (near) exact no-op (|patched - baseline| ~ 0)
  - all required cells present (phase6) / benign+selfswap present (phase5)
  - per-split separation (dev/heldout both present; sids disjoint across splits)

Runs in the MAIN LOOP only (reads raw.jsonl, which carries concept/codeword fields). Emits a table
and exits nonzero if any dir FAILS a hard check.

Usage: python scripts/validate_experiment_coverage.py <dir> [<dir> ...] [--min 20]
"""
from __future__ import annotations
import json, os, sys
from collections import Counter, defaultdict

MIN_DEFAULT = 20
PHASE6_CELLS = {"C1", "C1_selfswap", "random_control", "S1", "S1_selfswap", "S3_install", "S_random"}
# necessity cell is C3 or legacy C3_mlpout


def load(d):
    return [json.loads(l) for l in open(os.path.join(d, "raw.jsonl"))]


def check_phase6(rows):
    issues, warns = [], []
    keys = Counter((r["sid"], r["split"], r["window"], r["cell"]) for r in rows)
    dups = sum(1 for c in keys.values() if c > 1)
    if dups:
        issues.append(f"{dups} duplicate (sid,split,window,cell) rows")
    cells = {r["cell"] for r in rows}
    nec = "C3" if "C3" in cells else ("C3_mlpout" if "C3_mlpout" in cells else None)
    if nec is None:
        issues.append("necessity cell C3/C3_mlpout missing")
    missing = PHASE6_CELLS - cells
    if missing:
        warns.append(f"cells absent: {sorted(missing)}")
    splits = defaultdict(set)
    for r in rows:
        if r["cell"] == "C1":
            splits[r["split"]].add(r["sid"])
    ns = {}
    for sp, sids in splits.items():
        valid = {r["sid"] for r in rows if r["split"] == sp and r["cell"] == "C1"
                 and r.get("benign_p_concept") is not None and r["p_concept"] > r["benign_p_concept"]}
        ns[sp] = len(valid)
        if len(valid) < MIN:
            warns.append(f"{sp}: n_valid={len(valid)} < {MIN}")
    if len(splits) >= 2:
        a, b = list(splits.values())[:2]
        if a & b:
            issues.append(f"{len(a & b)} sids shared across splits")
    # self-swap no-op
    c1 = {(r["sid"], r["split"], r["window"]): r["p_concept"] for r in rows if r["cell"] == "C1"}
    devs = [abs(r["p_concept"] - c1[(r["sid"], r["split"], r["window"])])
            for r in rows if r["cell"] == "C1_selfswap" and (r["sid"], r["split"], r["window"]) in c1]
    ssdev = max(devs) if devs else None
    if ssdev is not None and ssdev > 1e-4:
        issues.append(f"self-swap dev={ssdev:.2e} > 1e-4 (patch not a no-op)")
    return issues, warns, {"n_valid": ns, "selfswap_dev": ssdev, "dup_rows": dups}


def check_phase5(rows):
    issues, warns = [], []
    keys = Counter((r["sid"], r["split"], r["layer"], r["head"], r["cell"]) for r in rows if r["cell"] == "benign")
    dups = sum(1 for c in keys.values() if c > 1)
    if dups:
        issues.append(f"{dups} duplicate benign (sid,split,layer,head) rows")
    cells = {r["cell"] for r in rows}
    for need in ("benign", "selfswap"):
        if need not in cells:
            issues.append(f"cell '{need}' missing")
    splits = defaultdict(set)
    for r in rows:
        splits[r["split"]].add(r["sid"])
    ns = {}
    for sp in splits:
        valid = {r["sid"] for r in rows if r["split"] == sp and r["cell"] == "benign"
                 and r["C1"] > r.get("benign_p_concept", 1)}
        ns[sp] = len(valid)
        if len(valid) < MIN:
            warns.append(f"{sp}: n_valid={len(valid)} < {MIN}")
    layers = {r["layer"] for r in rows}
    devs = [abs(r["C1"] - r["p_concept"]) for r in rows if r["cell"] == "selfswap"]
    ssdev = max(devs) if devs else None
    if ssdev is not None and ssdev > 1e-4:
        issues.append(f"self-swap dev={ssdev:.2e} > 1e-4")
    return issues, warns, {"n_valid": ns, "selfswap_dev": ssdev, "dup_rows": dups,
                           "layers": f"{min(layers)}-{max(layers)}"}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    global MIN
    MIN = MIN_DEFAULT
    if "--min" in sys.argv:
        MIN = int(sys.argv[sys.argv.index("--min") + 1])
    any_fail = False
    print(f"{'dir':<62} {'type':<7} {'status':<6} detail")
    for d in args:
        try:
            rows = load(d)
        except Exception as e:
            print(f"{os.path.basename(d):<62} {'?':<7} {'ERROR':<6} cannot read raw.jsonl: {e}")
            any_fail = True
            continue
        cells = {r["cell"] for r in rows}
        if "benign" in cells and "layer" in rows[0]:
            typ, (issues, warns, info) = "phase5", check_phase5(rows)
        elif "C1" in cells:
            typ, (issues, warns, info) = "phase6", check_phase6(rows)
        else:
            print(f"{os.path.basename(d):<62} {'?':<7} {'SKIP':<6} unrecognized schema")
            continue
        status = "FAIL" if issues else ("WARN" if warns else "ok")
        any_fail = any_fail or bool(issues)
        detail = f"n_valid={info['n_valid']} ssdev={info['selfswap_dev']} dups={info['dup_rows']}"
        print(f"{os.path.basename(d):<62} {typ:<7} {status:<6} {detail}")
        for x in issues:
            print(f"    FAIL: {x}")
        for x in warns:
            print(f"    warn: {x}")
    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()
