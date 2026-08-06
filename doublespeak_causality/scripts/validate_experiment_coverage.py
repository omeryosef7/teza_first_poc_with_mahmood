#!/usr/bin/env python3
"""Coverage + integrity validator for the causal-KO / head-patch / behavioral output dirs (plan
deliverable `scripts/validate_experiment_coverage.py`). Institutionalizes the ad-hoc checks from the audit.

For each output dir it detects the experiment type from the row schema and checks:
  - no duplicate rows within a cell (phase6: (sid,split,window,cell); phase5: (sid,split,layer,head,cell))
  - n_valid >= MIN (default 20) per split
  - self-swap control is an (near) exact no-op (|patched - baseline| ~ 0)
  - all required cells present (phase6) / benign+selfswap present (phase5)
  - per-split separation (dev/heldout both present; sids disjoint across splits)

BEHAVIORAL dirs (plan §P0: `outputs/behav_*`, `write_refusal_intx_*`, `refusal_traj_*`, `refproj_*`,
`refinject_cal_*`) use a different row schema, `{id, split, cohort, <arm>_label, <arm>_score}`, and used to
crash this script with `KeyError: 'cell'`. They are now a first-class type with these checks:
  - no duplicate `id` within a split                                        FAIL
  - every arm present on every row (arm completeness)                       FAIL
  - no null / NaN score on a non-EMPTY arm (nested numeric arms too)        FAIL
  - label <-> score consistency at MAL_THRESHOLD (judge desync guard)       FAIL
  - ids disjoint across splits                                              FAIL
  - n per split >= MIN (--min, promote to FAIL with --strict-n)             warn
  - empty_rate (max over arms) reported in the detail column

A directory whose schema cannot be parsed is a **FAIL**, not a silent SKIP (the old `SKIP unrecognized
schema` line reported exit-0 "ok" for every behavioral dir in the repo). `--skip-unknown` restores the old
lenient behavior for exploratory use.

Runs in the MAIN LOOP only (reads raw.jsonl, which carries concept/codeword fields). Emits a table
and exits nonzero if any dir FAILS a hard check.

Usage: python scripts/validate_experiment_coverage.py <dir> [<dir> ...] [--min 20]
"""
from __future__ import annotations
import argparse, json, math, os, sys
from collections import Counter, defaultdict

MIN_DEFAULT = 20
PHASE6_CELLS = {"C1", "C1_selfswap", "random_control", "S1", "S1_selfswap", "S3_install", "S_random"}
# necessity cell is C3 or legacy C3_mlpout

try:                          # single-source the judge threshold if the §P0 judge module is present
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from behav_judge import MAL_THRESHOLD
except Exception:             # pragma: no cover - fallback mirrors scripts/phase_behav_*.py
    MAL_THRESHOLD = 0.25
# row fields that identify the example, not an experimental arm
BEHAV_META = {"id", "split", "cohort", "harmful_word", "concept", "codeword", "example_id",
              "n_cw_pos", "genlen"}


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


# ----------------------------------------------------------------------------- behavioral schema

def behav_arms(rows):
    """Arms of a behavioral dir.

    Returns (labelled_arms, numeric_arms). `labelled_arms` are judged generation arms carrying
    `<arm>_label` (+ usually `<arm>_score`, `<arm>_refused`); `numeric_arms` are non-judged payload
    columns (per-layer projection dicts, trajectories, scalars) keyed by their own top-level name.
    """
    labelled, numeric = set(), set()
    for r in rows:
        for k in r:
            if k.endswith("_label"):
                labelled.add(k[:-len("_label")])
    for r in rows:
        for k in r:
            if k in BEHAV_META or k.endswith(("_label", "_score", "_refused")):
                continue
            if k.rsplit("_", 1)[0] in labelled:      # e.g. <arm>_genlen
                continue
            numeric.add(k)
    return sorted(labelled), sorted(numeric)


def _finite_leaves(v, path=""):
    """Yield (path, value) for every scalar leaf under v, and (path, None) for null leaves."""
    if isinstance(v, dict):
        for k, x in v.items():
            yield from _finite_leaves(x, f"{path}.{k}" if path else str(k))
    elif isinstance(v, (list, tuple)):
        for i, x in enumerate(v):
            yield from _finite_leaves(x, f"{path}[{i}]")
    elif isinstance(v, bool) or isinstance(v, str):
        return
    else:
        yield path, v


def check_behavioral(rows):
    issues, warns = [], []
    labelled, numeric = behav_arms(rows)
    if not labelled and not numeric:
        issues.append("no experimental arm columns found")

    # duplicate ids within a split
    keys = Counter((r.get("split"), r.get("id")) for r in rows)
    dups = sum(c - 1 for c in keys.values() if c > 1)
    if dups:
        issues.append(f"{dups} duplicate (split,id) rows")
    if any(r.get("id") is None for r in rows):
        issues.append("rows missing 'id'")
    if any(r.get("split") is None for r in rows):
        issues.append("rows missing 'split'")

    # arm completeness: every arm on every row
    miss = Counter()
    for r in rows:
        for a in labelled:
            for suf in ("_label", "_score"):
                if f"{a}{suf}" not in r:
                    miss[f"{a}{suf}"] += 1
        for a in numeric:
            if a not in r:
                miss[a] += 1
    if miss:
        issues.append("incomplete arms: " + ", ".join(f"{k}(missing {v})" for k, v in sorted(miss.items())[:6]))

    # null / NaN scores, and label<->score consistency
    nnull, nbad, nlabel = 0, 0, 0
    for r in rows:
        for a in labelled:
            lab, sc = r.get(f"{a}_label"), r.get(f"{a}_score")
            fin = isinstance(sc, (int, float)) and not isinstance(sc, bool) and math.isfinite(sc)
            if not fin:
                if lab != "EMPTY":
                    nnull += 1
            elif (sc >= MAL_THRESHOLD) != (lab == "MALICIOUS"):
                nlabel += 1
        for a in numeric:
            for p, v in _finite_leaves(r.get(a), a):
                if v is None or not math.isfinite(v):
                    nbad += 1
    if nnull:
        issues.append(f"{nnull} null/NaN scores on non-EMPTY arms")
    if nbad:
        issues.append(f"{nbad} null/NaN numeric leaves in non-judged arms")
    if nlabel:
        issues.append(f"{nlabel} label/score inconsistencies at MAL_THRESHOLD={MAL_THRESHOLD}")

    # per-split n and split separation
    by_split = defaultdict(list)
    for r in rows:
        by_split[r.get("split")].append(r)
    ns = {sp: len(v) for sp, v in sorted(by_split.items())}
    for sp, n in ns.items():
        if n < MIN:
            (issues if STRICT_N else warns).append(f"{sp}: n={n} < {MIN}")
    if len(by_split) < 2:
        warns.append(f"only {len(by_split)} split(s) present: {sorted(by_split)}")
    ids = {sp: {r.get("id") for r in v} for sp, v in by_split.items()}
    sps = sorted(ids)
    for i in range(len(sps)):
        for j in range(i + 1, len(sps)):
            sh = ids[sps[i]] & ids[sps[j]]
            if sh:
                issues.append(f"{len(sh)} ids shared between {sps[i]} and {sps[j]}")

    # empty_rate per split per arm (reported, not gated)
    empty = {}
    for sp, v in sorted(by_split.items()):
        for a in labelled:
            e = sum(1 for r in v if r.get(f"{a}_label") == "EMPTY") / max(1, len(v))
            empty[f"{sp}/{a}"] = round(e, 4)
    emax = max(empty.values()) if empty else None
    hot = sorted((k for k, v in empty.items() if v > 0), key=lambda k: -empty[k])[:4]
    if hot:
        warns.append("nonzero empty_rate: " + ", ".join(f"{k}={empty[k]}" for k in hot))
    return issues, warns, {"n_valid": ns, "selfswap_dev": None, "dup_rows": dups,
                           "arms": len(labelled) + len(numeric), "empty_rate_max": emax,
                           "empty_rate": empty, "labelled_arms": labelled, "numeric_arms": numeric}


REFVAL_ARMS = ("base_harmful", "base_benign", "ablate", "ablate_rand", "induce", "induce_rand")


def check_refval(rows):
    """P7 refusal-direction validation (scripts/validate_refusal_directions.py).

    Row schema: family, layer, arm, item, refused, empty, len. The two BASELINE arms
    (base_harmful / base_benign) are generated ONCE and carry family=None, layer=None; every other
    arm is per (family, layer). Note the induce arms may legitimately have FEWER rows than the
    ablate arms: with --induce-eval harmless the induce population is the held-out half of
    HARMLESS_INSTRUCTIONS, which is smaller than the bench eval split. That is not an error, so this
    checker compares induce against base_benign and ablate against base_harmful -- never across.
    """
    issues, warns = [], []
    arms = {r.get("arm") for r in rows}
    unknown = arms - set(REFVAL_ARMS)
    if unknown:
        issues.append(f"unknown arm(s): {sorted(unknown)}")
    for a in ("base_harmful", "base_benign", "ablate", "ablate_rand", "induce", "induce_rand"):
        if a not in arms:
            issues.append(f"missing arm {a!r}")

    base = [r for r in rows if r.get("family") is None]
    cell = [r for r in rows if r.get("family") is not None]
    if any(r.get("arm") not in ("base_harmful", "base_benign") for r in base):
        issues.append("family=None rows contain a non-baseline arm")
    if any(r.get("layer") is None for r in cell):
        issues.append("per-cell rows missing 'layer'")

    # duplicates: a (family, layer, arm, item) must be unique
    dups = sum(c - 1 for c in Counter(
        (r.get("family"), r.get("layer"), r.get("arm"), r.get("item")) for r in rows).values() if c > 1)
    if dups:
        issues.append(f"{dups} duplicate (family,layer,arm,item) rows")

    # `refused` must be a real boolean -- a None would be silently summed as 0 by the recomputer
    nbad = sum(1 for r in rows if not isinstance(r.get("refused"), bool))
    if nbad:
        issues.append(f"{nbad} rows whose 'refused' is not a bool")

    # every (family, layer) must carry all four intervention arms, at equal n within each PAIR
    per = defaultdict(lambda: defaultdict(int))
    for r in cell:
        per[(r["family"], r["layer"])][r["arm"]] += 1
    n_ab_base = sum(1 for r in base if r["arm"] == "base_harmful")
    n_in_base = sum(1 for r in base if r["arm"] == "base_benign")
    for k, c in sorted(per.items(), key=str):
        for a in ("ablate", "ablate_rand", "induce", "induce_rand"):
            if not c.get(a):
                issues.append(f"{k[0]}/L{k[1]}: missing arm {a!r}")
        if c.get("ablate") != c.get("ablate_rand"):
            issues.append(f"{k[0]}/L{k[1]}: ablate n={c.get('ablate')} != ablate_rand n={c.get('ablate_rand')}")
        if c.get("induce") != c.get("induce_rand"):
            issues.append(f"{k[0]}/L{k[1]}: induce n={c.get('induce')} != induce_rand n={c.get('induce_rand')}")
        # the paired McNemar in the summary pairs each arm against ITS OWN baseline
        if n_ab_base and c.get("ablate") not in (None, n_ab_base):
            issues.append(f"{k[0]}/L{k[1]}: ablate n={c.get('ablate')} != base_harmful n={n_ab_base}")
        if n_in_base and c.get("induce") not in (None, n_in_base):
            issues.append(f"{k[0]}/L{k[1]}: induce n={c.get('induce')} != base_benign n={n_in_base}")

    emax = 0.0
    for k, _ in per.items():
        for a in ("ablate", "induce"):
            v = [r for r in cell if (r["family"], r["layer"]) == k and r["arm"] == a]
            if v:
                emax = max(emax, sum(1 for r in v if r.get("empty")) / len(v))
    if emax > 0.5:
        warns.append(f"empty_rate up to {emax:.2f} in an intervention arm (decoder damage?)")

    info = {"n_valid": len(rows), "n_cells": len(per), "families": sorted({str(k[0]) for k in per}),
            "n_base_harmful": n_ab_base, "n_base_benign": n_in_base,
            "empty_rate_max": round(emax, 4), "dup_rows": dups}
    return issues, warns, info


def detect(rows):
    """-> ('phase5'|'phase6'|'behav', checker) or (None, None) if the schema is unparseable."""
    if not rows:
        return None, None
    if all("cell" in r for r in rows):
        cells = {r["cell"] for r in rows}
        if "benign" in cells and "layer" in rows[0]:
            return "phase5", check_phase5
        if "C1" in cells:
            return "phase6", check_phase6
        return None, None
    if all(("id" in r and "split" in r) for r in rows):
        return "behav", check_behavioral
    # P7 refusal-direction validation. Keyed on 'arm' + 'refused', which no other phase emits;
    # 'family'/'layer' are None on the baseline rows so they cannot be part of the discriminator.
    if all(("arm" in r and "refused" in r and "item" in r) for r in rows):
        return "refval", check_refval
    return None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+", help="output run dirs (each must contain raw.jsonl)")
    ap.add_argument("--min", type=int, default=MIN_DEFAULT, help="minimum n (or n_valid) per split")
    ap.add_argument("--strict-n", action="store_true", help="treat n < --min as FAIL, not warn (behavioral)")
    ap.add_argument("--skip-unknown", action="store_true",
                    help="legacy: report SKIP instead of FAIL for an unrecognized row schema")
    ap.add_argument("--json", dest="as_json", metavar="PATH", default=None,
                    help="also write the per-dir result objects to PATH")
    args = ap.parse_args()

    global MIN, STRICT_N
    MIN, STRICT_N = args.min, args.strict_n
    any_fail = False
    out = []
    print(f"{'dir':<62} {'type':<7} {'status':<6} detail")
    for d in args.dirs:
        try:
            rows = load(d)
        except Exception as e:
            print(f"{os.path.basename(d):<62} {'?':<7} {'ERROR':<6} cannot read raw.jsonl: {e}")
            out.append({"dir": d, "type": None, "status": "ERROR", "issues": [str(e)]})
            any_fail = True
            continue
        typ, checker = detect(rows)
        if typ is None:
            if args.skip_unknown:
                print(f"{os.path.basename(d):<62} {'?':<7} {'SKIP':<6} unrecognized schema")
                out.append({"dir": d, "type": None, "status": "SKIP", "issues": []})
                continue
            keys = sorted(rows[0])[:8] if rows else []
            print(f"{os.path.basename(d):<62} {'?':<7} {'FAIL':<6} unrecognized schema; first-row keys={keys}")
            out.append({"dir": d, "type": None, "status": "FAIL",
                        "issues": ["unrecognized row schema"], "n_rows": len(rows)})
            any_fail = True
            continue
        issues, warns, info = checker(rows)
        status = "FAIL" if issues else ("WARN" if warns else "ok")
        any_fail = any_fail or bool(issues)
        if typ == "behav":
            detail = (f"n={info['n_valid']} arms={info['arms']} "
                      f"empty_max={info['empty_rate_max']} dups={info['dup_rows']}")
        elif typ == "refval":
            detail = (f"rows={info['n_valid']} cells={info['n_cells']} fam={','.join(info['families'])} "
                      f"base_h={info['n_base_harmful']} base_b={info['n_base_benign']} "
                      f"empty_max={info['empty_rate_max']} dups={info['dup_rows']}")
        else:
            detail = f"n_valid={info['n_valid']} ssdev={info['selfswap_dev']} dups={info['dup_rows']}"
        print(f"{os.path.basename(d):<62} {typ:<7} {status:<6} {detail}")
        for x in issues:
            print(f"    FAIL: {x}")
        for x in warns:
            print(f"    warn: {x}")
        out.append({"dir": d, "type": typ, "status": status, "issues": issues, "warns": warns,
                    "n_rows": len(rows), "info": info})
    if args.as_json:
        with open(args.as_json, "w") as fh:
            json.dump(out, fh, indent=2)
    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()
