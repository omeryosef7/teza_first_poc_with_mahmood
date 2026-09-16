#!/usr/bin/env python3
"""The causal POSITION MAP and POSITION LADDER, as committed code producing a committed artifact.

*** WHY THIS FILE EXISTS (review R4-M2). ***
Every number in sprint entries S-059, S-063, S-066, S-069 and S-072 -- the ladder's linearity, the
single-position map, the codeword row's 46.6 % -- was computed in ad-hoc shell heredocs and survived
only as prose in the log. There was **one** grep hit for those arms repo-wide, and it was the
launcher. That means the sprint's most-cited mechanistic result bypassed `strict_run_dir`, the
cross-arm key intersection, and every VOID check that the subspace analyser applies as a matter of
course. This reproduces them under those guards and writes a machine-readable artifact.

WHAT IT ENFORCES, reusing the sprint's own machinery rather than restating it:
  * `strict_run_dir` -- anchored tag matching, DONE.json, ledger-vs-file row agreement;
  * ONE (domain, slot) key set across every arm, intersected before any averaging;
  * per-arm assertion that a named-position arm really restored exactly ONE position, that the
    position it declares matches the arm's name, and that the rescue fired on every row;
  * `KO_POS<k>` arms assert their own `n_rescue_positions == k`;
  * the k = 28 ladder arm must reproduce `KO_FULL` exactly, on a DIFFERENT run directory.
"""
from __future__ import annotations
import argparse, importlib.util, json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))


def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s); sys.modules[mod] = m; s.loader.exec_module(m); return m


rd = _load("rderive", "scripts/dcs_csi_rederive_patch.py")
lpm = _load("lpm", "scripts/dcs_cont_layerpos_map.py")


def arm(tag_prefix, name, expect_n, split, assign, allow_short):
    d = rd.strict_run_dir("%s_%s" % (tag_prefix, name), expect_n, row_file="results.jsonl",
                          allow_short=allow_short)
    rows = [json.loads(l) for l in open(os.path.join(d, "results.jsonl"))]
    inst = lpm.load_installation(d)[0]
    kv = {k: v for k, v in inst.items() if assign.get(k[0]) == split}
    meta = {"dir": os.path.basename(d), "n_rows": len(rows),
            "n_rescue_positions": sorted({r.get("n_rescue_positions") for r in rows}),
            "rel_end_rows": sorted({r.get("rescue_rel_end_rows") for r in rows}),
            "fired": sum(1 for r in rows if (r.get("rescue_liveness") or {}).get("fired")),
            "layer": sorted({r.get("rescue_layer") for r in rows if r.get("rescue_layer")})}
    return kv, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", default="button")
    ap.add_argument("--tag-prefix", default="csi1_button_train")
    ap.add_argument("--expect-n", type=int, default=670)
    ap.add_argument("--split", default="train")
    ap.add_argument("--allow-short", type=int, default=2)
    ap.add_argument("--positions", default="1,2,3,4,5,6,7,8,9,10,11,12,15,20,25,28")
    ap.add_argument("--ladder", default="1,2,4,8,14,20,28")
    ap.add_argument("--n-boot", type=int, default=20000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    assign = lpm.load_split()
    POS = [int(x) for x in a.positions.split(",") if x]
    LAD = [int(x) for x in a.ladder.split(",") if x]

    names = ["KO", "KO_FULL"] + ["KO_AT%d" % p for p in POS] + ["KO_POS%d" % k for k in LAD]
    kv, meta, problems = {}, {}, []
    for n in names:
        try:
            kv[n], meta[n] = arm(a.tag_prefix, n, a.expect_n, a.split, assign, a.allow_short)
        except SystemExit as e:
            problems.append("%s: %s" % (n, str(e)[:110])); continue
    have = [n for n in names if n in kv]
    common = set.intersection(*[set(kv[n]) for n in have])
    # ---- per-arm integrity -------------------------------------------------------------------
    for p in POS:
        n = "KO_AT%d" % p
        if n not in meta: continue
        if meta[n]["n_rescue_positions"] != [1]:
            problems.append("%s restored %s positions, expected exactly [1]" % (n, meta[n]["n_rescue_positions"]))
        if meta[n]["rel_end_rows"] != ["-%d" % p]:
            problems.append("%s declares rel_end_rows %s, expected ['-%d']" % (n, meta[n]["rel_end_rows"], p))
        if meta[n]["fired"] != meta[n]["n_rows"]:
            problems.append("%s: rescue fired on %d of %d rows" % (n, meta[n]["fired"], meta[n]["n_rows"]))
    for k in LAD:
        n = "KO_POS%d" % k
        if n in meta and meta[n]["n_rescue_positions"] != [k]:
            problems.append("%s restored %s positions, expected [%d]" % (n, meta[n]["n_rescue_positions"], k))
    if "KO_POS28" in kv and "KO_FULL" in kv:
        if meta["KO_POS28"]["dir"] == meta["KO_FULL"]["dir"]:
            problems.append("KO_POS28 and KO_FULL resolve to the SAME directory -- the consistency "
                            "check would be vacuous (S-042)")
        ks = sorted(set(kv["KO_POS28"]) & set(kv["KO_FULL"]))
        mx = max(abs(kv["KO_POS28"][k] - kv["KO_FULL"][k]) for k in ks) if ks else None
        if mx != 0.0:
            problems.append("KO_POS28 != KO_FULL (max|diff| = %r)" % mx)

    def dmean(n):
        by = {}
        for k in common: by.setdefault(k[0], []).append(kv[n][k])
        return {d: sum(v) / len(v) for d, v in by.items()}
    D = {n: dmean(n) for n in have}
    doms = sorted(D["KO"])
    full = rd.boot_paired_diff(doms, D["KO_FULL"], D["KO"], a.n_boot, 20260915)["point"]

    out = {"schema": "dcs_csi_position_map/1", "codeword": a.codeword, "split": a.split,
           "n_domains": len(doms), "n_keys_common": len(common),
           "KO_FULL_minus_KO": round(full, 6), "arm_meta": meta, "PROBLEMS": problems,
           "single_positions": {}, "ladder": {}}
    for p in POS:
        n = "KO_AT%d" % p
        if n not in D: continue
        b = rd.boot_paired_diff(doms, D[n], D["KO"], a.n_boot, 20260915)
        out["single_positions"]["rel-%d" % p] = {
            "recovery": round(b["point"], 6), "ci95": [round(b["ci95"][0], 6), round(b["ci95"][1], 6)],
            "n_pos": b["n_pos"], "n_neg": b["n_neg"], "frac_of_full": round(b["point"] / full, 4)}
    for k in LAD:
        n = "KO_POS%d" % k
        if n not in D: continue
        b = rd.boot_paired_diff(doms, D[n], D["KO"], a.n_boot, 20260915)
        out["ladder"]["k=%d" % k] = {"recovery": round(b["point"], 6),
                                     "ci95": [round(b["ci95"][0], 6), round(b["ci95"][1], 6)],
                                     "frac_of_full": round(b["point"] / full, 4),
                                     "obs_over_linear": round((b["point"] / full) / (k / 28.0), 3)}
    sp = out["single_positions"]
    out["sum_measured_positions"] = round(sum(v["recovery"] for v in sp.values()), 6)
    out["sum_as_frac_of_full"] = round(out["sum_measured_positions"] / full, 4)
    out["n_positions_measured"] = len(sp)
    out["n_positions_unmeasured"] = 28 - len(sp)
    # R4-M3: the unmeasured remainder is NOT 1 - sum; that would assume the additivity it is cited
    # to support. It is simply unmeasured, and is reported as such.
    out["unmeasured_remainder_note"] = (
        "NOT computed as 1 - sum: that would assume the additivity this map is cited to support. "
        "The %d unmeasured positions have not been measured; the measured ones sum to %.1f%% of "
        "KO_FULL." % (28 - len(sp), 100 * out["sum_as_frac_of_full"]))
    if LAD:
        ks = [k for k in LAD if "k=%d" % k in out["ladder"]]
        rec = [out["ladder"]["k=%d" % k]["recovery"] for k in ks]
        sxx = sum(k * k for k in ks); sxy = sum(k * r for k, r in zip(ks, rec))
        sl = sxy / sxx
        my = sum(rec) / len(rec); syy = sum((r - my) ** 2 for r in rec)
        out["ladder_fit_through_origin"] = {
            "slope": round(sl, 8), "r2": round(1 - sum((r - sl * k) ** 2 for k, r in zip(ks, rec)) / syy, 5),
            "slope_times_28": round(sl * 28, 6), "ratio_to_KO_FULL": round(sl * 28 / full, 4)}
    outp = a.out or os.path.join(REPO, "reports/DCS_CSI_POSITION_MAP_%s_%s.json" % (a.codeword, a.split))
    json.dump(out, open(outp, "w"), indent=1)
    print("arms: %d  keys: %d  domains: %d  KO_FULL=%+.5f" % (len(have), len(common), len(doms), full))
    for k, v in sorted(sp.items(), key=lambda kv: -kv[1]["recovery"])[:6]:
        print("  %-8s %+.5f  %5.1f%%  %d/%d" % (k, v["recovery"], 100 * v["frac_of_full"], v["n_pos"], v["n_neg"]))
    print("  sum of %d measured = %+.5f = %.1f%% of KO_FULL" % (len(sp), out["sum_measured_positions"], 100 * out["sum_as_frac_of_full"]))
    if out.get("ladder_fit_through_origin"): print("  ladder:", json.dumps(out["ladder_fit_through_origin"]))
    print("PROBLEMS:", problems if problems else "none")
    print("wrote", os.path.relpath(outp, REPO))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
