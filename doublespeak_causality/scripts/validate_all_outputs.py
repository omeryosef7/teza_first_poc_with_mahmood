#!/usr/bin/env python3
"""Summary-vs-raw reconciliation validator (plan §P0: "recompute every `summary.json` number from its
`raw.jsonl`, verify train/test disjointness, verify all manifest cells present, fail on a missing cell").

For every run dir given it:
  1. loads `raw.jsonl` + `summary.json` and detects the row schema (reuses
     `validate_experiment_coverage.detect`, so the two validators can never disagree about a schema);
  2. **recomputes** the aggregates in `summary.json` directly from `raw.jsonl` and asserts they match to
     `--tol` (or to the rounding the summary itself used) -- any mismatch is a hard FAIL, because it means
     the committed number does not follow from the preserved rows;
  3. asserts the train/test (dev/heldout) example ids are **disjoint**;
  4. if `configs/manifests/<phase>.json` exists, asserts every expected cell / arm / split is present and
     **FAILS on a missing one** (extras are warnings);
  5. reports how many summary leaves it could not recompute, so the coverage of this check is auditable
     instead of implicit.

Exit code is non-zero if any dir FAILS. `--json PATH` writes the machine-readable per-dir result.

What is recomputed, by family:
  behav (`{id, split, cohort, <arm>_label, <arm>_score}` and its non-judged numeric-arm variants):
      n, ASR/refusal_rate/empty_rate per arm (flat `ASR_<arm>` and nested `ASR: {<arm>: ..}` layouts),
      `delta_*` necessity/control deltas, `<a2>_vs_<a1>` and `vs_ds_base` / `by_layer_vs_ds_base`
      McNemar blocks (delta_ASR, flip counts, exact p), `per_layer.<h>.mean.<arm>` projections and their
      paired-difference point estimates, `pconcept_control`, `max_suppression*`, trajectory means.
  phase6: n_rows, per-window n_valid, mean_C1/C3/S3 p_concept, nec/suf self-swap max dev,
      necessity/sufficiency point estimates (bootstrap CI *bounds* are RNG-dependent -> not checked).
  phase5: n_rows, per-split n_valid, selfswap_max_dev, top10_by_mean values.

Manifest format (`configs/manifests/<phase>.json`, all keys optional):
  {"phase": "behav_carry",
   "expected_splits": ["train", "test"], "min_n_per_split": 20,
   "expected_arms":  ["baseline", "carry_abl", "rand_abl"],     # behavioral arm prefixes
   "expected_cells": ["C1", "C3", "C1_selfswap"],               # phase5/6 `cell` column values
   "expected_windows": ["L8", "L9"]}                            # phase6 `window` column values
The phase key is resolved from the run-dir basename by trying successively shorter `_`-separated
prefixes (`behav_carry_curated` -> `behav_carry` -> `behav`), first hit wins; `--manifest` forces one.

Usage:
  python scripts/validate_all_outputs.py outputs/behav_* [--tol 5e-4] [--manifest-dir configs/manifests]
Runs on the LOGIN NODE (stdlib only; reads raw.jsonl, which carries no free text -- but it does carry
concept/codeword fields, so this is a MAIN-LOOP tool).
"""
from __future__ import annotations
import argparse, glob, json, math, os, sys
from collections import defaultdict
from math import comb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_experiment_coverage import detect, behav_arms, load   # noqa: E402  (single source of truth)

DEFAULT_TOL = 5e-4
MAL = "MALICIOUS"

# `delta_<name>` aggregates whose definition is not derivable from the key alone.
# value = ASR[a] - ASR[b]
DELTA_MAP = {
    "delta_necessity_carry":  ("baseline", "carry_abl"),
    "delta_necessity_write":  ("baseline", "write_abl"),
    "delta_rand_ctrl":        ("baseline", "rand_abl"),
    "delta_rand_pos_ctrl":    ("baseline", "rand_pos_abl"),
}
# per_layer paired-difference blocks: key -> (arm_a, arm_b); stored value is [mean, lo, hi]
PAIRDIFF_MAP = {
    "direct_minus_ds":          ("direct", "doublespeak"),
    "direct_minus_ds_RANDCTRL": ("direct_rand", "doublespeak_rand"),
    "writeabl_minus_dsbase":    ("ds_writeabl", "ds_base"),
}


# --------------------------------------------------------------------------- helpers

def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(0, k + 1)) / (2 ** n))


def _dec(v):
    s = repr(float(v))
    if "e" in s or "E" in s:
        return 12
    return min(12, len(s.split(".")[1]) if "." in s else 0)


def close(a, b, tol):
    """a = recomputed, b = value stored in summary.json."""
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, str) or isinstance(b, str):
        return a == b
    if isinstance(a, float) and math.isnan(a):
        return isinstance(b, float) and math.isnan(b)
    if abs(a - b) <= tol:
        return True
    return round(float(a), _dec(b)) == float(b)


def redact(v):
    """Values printed by the validator are numbers; anything else is shown as a type tag."""
    if v is None or isinstance(v, (int, float)) and not isinstance(v, bool):
        return v
    if isinstance(v, str) and len(v) <= 16 and v.replace("_", "").replace("-", "").isalnum():
        return v                      # short identifiers (cell / head names) are safe
    return f"<{type(v).__name__}>"


def leaves(v, path=""):
    """Flatten a summary into {path: scalar}. Lists index as `key[i]`, `None` is kept."""
    out = {}
    if isinstance(v, dict):
        for k, x in v.items():
            out.update(leaves(x, f"{path}.{k}" if path else str(k)))
    elif isinstance(v, (list, tuple)):
        for i, x in enumerate(v):
            out.update(leaves(x, f"{path}[{i}]"))
    else:
        out[path] = v
    return out


def mean(xs):
    xs = [x for x in xs if x is not None]
    return float(sum(xs)) / len(xs) if xs else None


def split_container(summary):
    """-> (prefix_fn, {split: node}) for both `by_split.<sp>` and top-level `<sp>` layouts."""
    if isinstance(summary.get("by_split"), dict):
        return (lambda sp: f"by_split.{sp}"), summary["by_split"]
    node = {k: v for k, v in summary.items()
            if k in ("train", "test", "dev", "heldout") and isinstance(v, dict)}
    return (lambda sp: sp), node


# --------------------------------------------------------------------------- behavioral

def expect_behav(rows, summary):
    """-> {summary_path: recomputed_value}"""
    exp = {}
    labelled, numeric = behav_arms(rows)
    if "n_rows" in summary:
        exp["n_rows"] = len(rows)
    pref, cont = split_container(summary)
    by_split = defaultdict(list)
    for r in rows:
        by_split[r.get("split")].append(r)

    for sp, node in cont.items():
        sr = by_split.get(sp)
        if not sr:
            continue
        P = pref(sp)
        asr = {a: mean([r.get(f"{a}_label") == MAL for r in sr]) for a in labelled}
        rej = {a: mean([r.get(f"{a}_label") == "REJECTED" for r in sr]) for a in labelled}
        emp = {a: mean([r.get(f"{a}_label") == "EMPTY" for r in sr]) for a in labelled}
        exp[f"{P}.n"] = len(sr)

        for a in labelled:                                    # flat layout
            exp[f"{P}.ASR_{a}"] = asr[a]
            exp[f"{P}.empty_{a}"] = emp[a]
            exp[f"{P}.refused_{a}"] = rej[a]
        for key, tbl in (("ASR", asr), ("refusal_rate", rej), ("empty", emp), ("empty_rate", emp)):
            for a in labelled:                                # nested layout
                exp[f"{P}.{key}.{a}"] = tbl[a]
        for k, (a, b) in DELTA_MAP.items():
            if a in asr and b in asr:
                exp[f"{P}.{k}"] = asr[a] - asr[b]
        for k in node:                                        # mean_<rawfield>
            if k.startswith("mean_") and k[5:] in rows[0]:
                exp[f"{P}.{k}"] = mean([r.get(k[5:]) for r in sr])

        def mcn(a1, a2, base, names):
            """paired McNemar block: a1 = reference arm, a2 = compared arm."""
            b = sum(1 for r in sr if r.get(f"{a1}_label") != MAL and r.get(f"{a2}_label") == MAL)
            c = sum(1 for r in sr if r.get(f"{a1}_label") == MAL and r.get(f"{a2}_label") != MAL)
            exp[f"{base}.delta_ASR"] = asr[a2] - asr[a1]
            exp[f"{base}.{names[0]}"] = b
            exp[f"{base}.{names[1]}"] = c
            exp[f"{base}.mcnemar_p"] = mcnemar_exact(b, c)

        for k, v in node.items():
            if "_vs_" in k and isinstance(v, dict):           # "<a2>_vs_<a1>"
                a2, a1 = k.split("_vs_", 1)
                if a1 in asr and a2 in asr:
                    nm = ("flip_gain", "flip_loss") if "flip_gain" in v else ("flip_on", "flip_off")
                    mcn(a1, a2, f"{P}.{k}", nm)
            if k == "vs_ds_base" and isinstance(v, dict) and "ds_base" in asr:
                for a, blk in v.items():
                    if a in asr:
                        nm = ("flip_on", "flip_off") if "flip_on" in blk else ("flip_gain", "flip_loss")
                        mcn("ds_base", a, f"{P}.{k}.{a}", nm)
            if k == "by_layer_vs_ds_base" and isinstance(v, dict) and "ds_base" in asr:
                for L, blk in v.items():
                    a, ar = f"ds_cal_L{L}", f"ds_calrand_L{L}"
                    if a in asr:
                        mcn("ds_base", a, f"{P}.{k}.{L}", ("flip_on", "flip_off"))
                        exp.pop(f"{P}.{k}.{L}.flip_on", None); exp.pop(f"{P}.{k}.{L}.flip_off", None)
                    if ar in asr:
                        exp[f"{P}.{k}.{L}.rand_delta_ASR"] = asr[ar] - asr["ds_base"]

        # ---- non-judged numeric arms: per-layer projections / trajectories
        pl = node.get("per_layer")
        if isinstance(pl, dict):
            for h, blk in pl.items():
                md = blk.get("mean", {})
                for a in md:
                    if a in numeric:
                        exp[f"{P}.per_layer.{h}.mean.{a}"] = mean([r[a][h] for r in sr])
                for k, (a, b) in PAIRDIFF_MAP.items():
                    if k in blk and a in numeric and b in numeric:
                        exp[f"{P}.per_layer.{h}.{k}[0]"] = mean([r[a][h] - r[b][h] for r in sr])
                if "frac_of_direct_gap_restored" in blk and {"direct", "ds_base", "ds_writeabl"} <= set(numeric):
                    m = {a: round(mean([r[a][h] for r in sr]), 4) for a in ("direct", "ds_base", "ds_writeabl")}
                    gap = m["direct"] - m["ds_base"]
                    exp[f"{P}.per_layer.{h}.frac_of_direct_gap_restored"] = (
                        round((m["ds_writeabl"] - m["ds_base"]) / gap, 3) if abs(gap) > 1e-6 else None)
            if "max_suppression_hs_row" in node:
                d = {h: mean([r["direct"][h] - r["doublespeak"][h] for r in sr]) for h in pl}
                best = max(d, key=lambda h: round(d[h], 4))
                exp[f"{P}.max_suppression_hs_row"] = int(best)
                exp[f"{P}.max_suppression[0]"] = d[best]
        pc = node.get("pconcept_control")
        if isinstance(pc, dict):
            exp[f"{P}.pconcept_control.ds"] = mean([r.get("pconcept_ds") for r in sr])
            exp[f"{P}.pconcept_control.writeabl"] = mean([r.get("pconcept_writeabl") for r in sr])
            exp[f"{P}.pconcept_control.drop_ci[0]"] = mean(
                [r["pconcept_ds"] - r["pconcept_writeabl"] for r in sr
                 if r.get("pconcept_ds") is not None and r.get("pconcept_writeabl") is not None])
        bl = node.get("by_layer")
        if isinstance(bl, dict) and any(k.endswith("_traj") for k in rows[0]):
            k_len = summary.get("k") or max(len(v) for r in sr for v in r["direct_traj"].values())
            ds_ref = [r for r in sr if r.get("ds_refused")]
            ds_cmp = [r for r in sr if not r.get("ds_refused")]
            exp[f"{P}.ds_refused_rate"] = len(ds_ref) / len(sr)
            exp[f"{P}.direct_refused_rate"] = mean([bool(r.get("direct_refused")) for r in sr])
            for L, blk in bl.items():
                for name, rs, arm in (("direct", sr, "direct"), ("ds_all", sr, "ds"),
                                      ("ds_complied", ds_cmp, "ds"), ("ds_refused", ds_ref, "ds")):
                    if blk.get(name) is None:
                        continue
                    for i in range(k_len):
                        vals = [r[f"{arm}_traj"].get(L, [])[i] for r in rs
                                if i < len(r[f"{arm}_traj"].get(L, []))]
                        exp[f"{P}.by_layer.{L}.{name}[{i}]"] = mean(vals)
    return exp


# --------------------------------------------------------------------------- phase6 / phase5

def expect_phase6(rows, summary):
    exp = {"n_rows": len(rows)} if "n_rows" in summary else {}
    pref, cont = split_container(summary)
    nodes = list(cont.items()) if cont else ([(None, summary)] if "windows" in summary else [])
    for sp, node in nodes:
        sr = [r for r in rows if sp is None or r["split"] == sp]
        P = (pref(sp) + ".") if sp is not None else ""
        valid = {r["sid"] for r in sr if r["cell"] == "C1"
                 and r.get("benign_p_concept") is not None and r["p_concept"] > r["benign_p_concept"]}
        if "n_valid_examples" in node:
            exp[f"{P}n_valid_examples"] = len(valid)
        for w, blk in (node.get("windows") or {}).items():
            def cm(cell):
                return {r["sid"]: r["p_concept"] for r in sr if r["cell"] == cell and r["window"] == w}
            c1, c3, rc, ss = cm("C1"), cm("C3") or cm("C3_mlpout"), cm("random_control"), cm("C1_selfswap")
            s1, s3, srd, sss = cm("S1"), cm("S3_install"), cm("S_random"), cm("S1_selfswap")
            nec = [s for s in valid if s in c1 and s in c3 and s in rc]
            suf = [s for s in valid if s in s1 and s in s3 and s in srd]
            B = f"{P}windows.{w}"
            exp[f"{B}.n_valid"] = len(nec)
            exp[f"{B}.mean_C1_p_concept"] = mean([c1[s] for s in nec])
            if "mean_C3_p_concept" in blk:
                exp[f"{B}.mean_C3_p_concept"] = mean([c3[s] for s in nec])
            exp[f"{B}.necessity_specific_ci[0]"] = mean([rc[s] - c3[s] for s in nec])
            exp[f"{B}.nec_selfswap_max_dev"] = (max([abs(c1[s] - ss[s]) for s in nec if s in ss], default=None)
                                                if nec else None)
            if "sufficiency_specific_ci" in blk:
                exp[f"{B}.sufficiency_specific_ci[0]"] = mean([s3[s] - srd[s] for s in suf])
                exp[f"{B}.mean_S3_install_p_concept"] = mean([s3[s] for s in suf])
                exp[f"{B}.suf_selfswap_max_dev"] = (max([abs(s1[s] - sss[s]) for s in suf if s in sss],
                                                        default=None) if suf else None)
    return exp


def expect_phase5(rows, summary):
    exp = {"n_rows": len(rows)} if "n_rows" in summary else {}
    pref, cont = split_container(summary)
    for sp, node in cont.items():
        sr = [r for r in rows if r["split"] == sp]
        P = pref(sp)
        valid = {r["sid"] for r in sr if r["cell"] == "benign" and r.get("benign_p_concept") is not None
                 and r["C1"] > r["benign_p_concept"]}
        exp[f"{P}.n_valid"] = len(valid)
        exp[f"{P}.selfswap_max_dev"] = max([abs(r["C1"] - r["p_concept"]) for r in sr
                                            if r["cell"] == "selfswap"], default=0.0)
        for i, ent in enumerate(node.get("top10_by_mean") or []):
            name = ent[0]
            l, h = name[1:].split("H")
            d = [r["C1"] - r["p_concept"] for r in sr if r["cell"] == "benign"
                 and r["layer"] == int(l) and r["head"] == int(h) and r["sid"] in valid]
            exp[f"{P}.top10_by_mean[{i}][0]"] = name
            exp[f"{P}.top10_by_mean[{i}][1]"] = mean(d)
    return exp


EXPECT = {"behav": expect_behav, "phase6": expect_phase6, "phase5": expect_phase5}


# --------------------------------------------------------------------------- manifest

def find_manifest(d, mdir, forced):
    if forced:
        return forced, json.load(open(forced))
    base = os.path.basename(os.path.normpath(d))
    parts = base.split("_")
    for i in range(len(parts), 0, -1):
        p = os.path.join(mdir, "_".join(parts[:i]) + ".json")
        if os.path.exists(p):
            return p, json.load(open(p))
    return None, None


def check_manifest(rows, man, typ):
    issues, warns = [], []
    got_splits = {r.get("split") for r in rows}
    exp_splits = set(man.get("expected_splits") or [])
    for s in sorted(exp_splits - got_splits):
        issues.append(f"manifest: split '{s}' MISSING from raw.jsonl")
    for s in sorted(got_splits - exp_splits) if exp_splits else []:
        warns.append(f"manifest: unexpected split '{s}'")
    minn = man.get("min_n_per_split")
    if minn:
        key = "id" if typ == "behav" else "sid"
        for s in sorted(got_splits):
            n = len({r.get(key) for r in rows if r.get("split") == s})
            if n < minn:
                issues.append(f"manifest: split '{s}' has n={n} < min_n_per_split={minn}")
    if man.get("expected_arms"):
        labelled, numeric = behav_arms(rows) if typ == "behav" else ([], [])
        got = set(labelled) | set(numeric)
        for a in man["expected_arms"]:
            if a not in got:
                issues.append(f"manifest: arm '{a}' MISSING")
            else:
                miss = sum(1 for r in rows if f"{a}_label" not in r and a not in r)
                if miss:
                    issues.append(f"manifest: arm '{a}' MISSING on {miss} rows")
        for a in sorted(got - set(man["expected_arms"])):
            warns.append(f"manifest: unexpected arm '{a}'")
    for field, col in (("expected_cells", "cell"), ("expected_windows", "window")):
        if man.get(field):
            got = {r.get(col) for r in rows}
            for c in man[field]:
                if c not in got:
                    issues.append(f"manifest: {col} '{c}' MISSING")
            for c in sorted(x for x in got - set(man[field]) if x is not None):
                warns.append(f"manifest: unexpected {col} '{c}'")
    return issues, warns


# --------------------------------------------------------------------------- driver

def validate_dir(d, args):
    res = {"dir": d, "status": "ok", "type": None, "issues": [], "warns": [],
           "n_checked": 0, "n_unchecked": 0, "mismatches": []}
    try:
        rows = load(d)
    except Exception as e:
        res.update(status="FAIL", issues=[f"cannot read raw.jsonl: {e}"])
        return res
    sp = os.path.join(d, "summary.json")
    if not os.path.exists(sp):
        res.update(status="FAIL", issues=["summary.json MISSING (run-dir contract §2.1)"])
        return res
    summary = json.load(open(sp))
    typ, _ = detect(rows)
    res["type"] = typ
    if typ is None:
        res.update(status="FAIL", issues=["unrecognized row schema"])
        return res

    # ---- 1. split disjointness
    key = "id" if typ == "behav" else "sid"
    ids = defaultdict(set)
    for r in rows:
        ids[r.get("split")].add(r.get(key))
    sps = sorted(x for x in ids if x is not None)
    for i in range(len(sps)):
        for j in range(i + 1, len(sps)):
            sh = ids[sps[i]] & ids[sps[j]]
            if sh:
                res["issues"].append(f"{len(sh)} {key}s shared between splits {sps[i]}/{sps[j]}")
    if len(sps) < 2:
        res["warns"].append(f"only {len(sps)} split(s) present: {sps}")
    res["splits"] = {s: len(ids[s]) for s in sps}

    # ---- 2. recompute summary from raw
    exp = EXPECT[typ](rows, summary)
    got = leaves(summary)
    checked = 0
    for path, want in exp.items():
        if path not in got:
            # a phase writes ONE of several equivalent layouts (`ASR_<arm>` vs `ASR: {<arm>: ..}`);
            # the recomputer proposes all of them, so an absent path is normally just the other layout.
            if args.warn_missing_keys:
                res["warns"].append(f"recomputed key absent from summary: {path}")
            continue
        checked += 1
        if not close(want, got[path], args.tol):
            res["mismatches"].append({"path": path, "summary": got[path], "recomputed": want})
    res["n_checked"] = checked
    unchecked = [p for p in got if p not in exp and isinstance(got[p], (int, float)) and not isinstance(got[p], bool)]
    res["n_unchecked"] = len(unchecked)
    res["unchecked_sample"] = sorted(unchecked)[:8]
    for m in res["mismatches"][:args.max_report]:
        # numbers only in the printed message: summary.json is a committed artifact and must never be
        # echoed as free text by a validator (project safety rule).
        s, w = (redact(m["summary"]), redact(m["recomputed"]))
        res["issues"].append(f"summary!=raw at {m['path']}: summary={s} recomputed={w}")
    if len(res["mismatches"]) > args.max_report:
        res["issues"].append(f"... and {len(res['mismatches']) - args.max_report} more mismatches")

    # ---- 3. manifest
    mpath, man = find_manifest(d, args.manifest_dir, args.manifest)
    res["manifest"] = mpath
    if man is None:
        res["warns"].append(f"no manifest under {args.manifest_dir} (plan §P0 requires one per phase)")
        if args.require_manifest:
            res["issues"].append("manifest REQUIRED but not found")
    else:
        mi, mw = check_manifest(rows, man, typ)
        res["issues"] += mi
        res["warns"] += mw

    res["status"] = "FAIL" if res["issues"] else ("WARN" if res["warns"] else "ok")
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--tol", type=float, default=DEFAULT_TOL, help="absolute tolerance (default 5e-4)")
    ap.add_argument("--manifest-dir", default="configs/manifests")
    ap.add_argument("--manifest", default=None, help="force one manifest file for every dir")
    ap.add_argument("--require-manifest", action="store_true", help="a missing manifest is a FAIL")
    ap.add_argument("--max-report", type=int, default=12, help="max mismatches printed per dir")
    ap.add_argument("--warn-missing-keys", action="store_true",
                    help="warn when a recomputable key is absent from summary.json (noisy: the "
                         "recomputer proposes every known summary layout)")
    ap.add_argument("--json", dest="as_json", metavar="PATH", default=None)
    ap.add_argument("--quiet", action="store_true", help="print only FAIL dirs")
    args = ap.parse_args()

    dirs = []
    for d in args.dirs:
        dirs.extend(sorted(glob.glob(d)) if any(c in d for c in "*?[") else [d])

    out, nfail = [], 0
    print(f"{'dir':<58} {'type':<7} {'status':<6} {'checked':>7} {'unchk':>6}  splits")
    for d in dirs:
        r = validate_dir(d, args)
        out.append(r)
        nfail += r["status"] == "FAIL"
        if args.quiet and r["status"] != "FAIL":
            continue
        print(f"{os.path.basename(os.path.normpath(d)):<58} {str(r['type']):<7} {r['status']:<6} "
              f"{r['n_checked']:>7} {r['n_unchecked']:>6}  {r.get('splits', {})}")
        for x in r["issues"]:
            print(f"    FAIL: {x}")
        for x in r["warns"]:
            print(f"    warn: {x}")
    print(f"\n{len(out)} dir(s): {sum(1 for r in out if r['status']=='ok')} ok, "
          f"{sum(1 for r in out if r['status']=='WARN')} warn, {nfail} FAIL; "
          f"{sum(r['n_checked'] for r in out)} summary values recomputed, "
          f"{sum(len(r['mismatches']) for r in out)} mismatched")
    if args.as_json:
        with open(args.as_json, "w") as fh:
            json.dump(out, fh, indent=2)
    sys.exit(1 if nfail else 0)


if __name__ == "__main__":
    main()
