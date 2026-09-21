"""Incremental GATE 0 over whatever PR-CSI-010 arms have landed so far.

WHY, GIVEN W4 ALREADY DOES GATE 0. W4 resolves all 24 arms through `strict_run_dir` and therefore
cannot run until the family is complete -- roughly six hours after the first arm lands. A liveness
failure on arm 7 should stop the family at arm 7, not be discovered when arm 24 finishes: every arm
after a VOID is GPU time spent on a result that cannot be reported.

⛔ IT READS LIVENESS AND DOSE ONLY. No endpoint field (`logp_concept`, `logp_codeword`,
`semantic_logodds`, `y_install`) is touched, so running it repeatedly while the family is in flight
cannot become a peek at the answer. The frozen read still governs what may be reported, and the
order there is GATE 0, then GATE 1, then the candidate.
"""
import argparse, glob, json, os, re, statistics, sys

ENDPOINT_FIELDS = ("logp_concept", "logp_codeword", "semantic_logodds", "y_install")


def assert_reads_no_endpoint():
    """Prove the claim above instead of asserting it in a comment.

    This script's whole licence to be run repeatedly WHILE THE FAMILY IS IN FLIGHT rests on it not
    touching the endpoint. A promise in a docstring is not a guard -- and a constant listing the
    forbidden fields, declared and never used, is the shape of a check that was intended and never
    written. So the module re-reads its own source and refuses if any endpoint field is ACCESSED
    (`r.get("...")` or `r["..."]`) anywhere in it. The declaration lines below are excluded because
    naming a field is not reading it.
    """
    src = open(os.path.abspath(__file__), encoding="utf-8").read().splitlines()
    bad = []
    for i, line in enumerate(src, 1):
        if line.lstrip().startswith(("#", '"', "'")) or "ENDPOINT_FIELDS" in line:
            continue
        for f in ENDPOINT_FIELDS:
            if ('get("%s")' % f) in line or ('["%s"]' % f) in line:
                bad.append("%d: %s" % (i, line.strip()))
    if bad:
        raise SystemExit("REFUSING: this sweep accesses an ENDPOINT field, so running it during a "
                         "live family would be a peek at the answer:\n  " + "\n  ".join(bad))


def arm_liveness(d):
    rows = [json.loads(l) for l in open(os.path.join(d, "results.jsonl"), encoding="utf-8")]
    sel = [r for r in rows if r.get("query_kind") == "semantic_one_word" and r.get("cell") == "C"]
    pre = [int(r.get("hook_n_prefill_edits") or 0) for r in sel]
    return {
        "rows": len(sel),
        "domains": len({r.get("domain") for r in sel}),
        "total_prefill": sum(pre),
        "median_prefill": float(statistics.median(pre)) if pre else 0.0,
        "decode": sum(int(r.get("hook_n_decode_edits") or 0) for r in sel),
        "violations": sum(1 for r in sel if r.get("hook_liveness_violations")),
        "heads": (json.load(open(os.path.join(d, "config.json")))["args"].get("knockout_heads") or ""),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--tag-prefix", required=True)
    ap.add_argument("--split", required=True, choices=("train", "validation"))
    ap.add_argument("--root", default="outputs/boombness/score_behavior")
    a = ap.parse_args()

    assert_reads_no_endpoint()
    pr = json.load(open(a.prereg))
    hs = pr["head_sets"]
    K = pr["K"]
    want_rows = pr["population"]["%s_expect_n" % a.split]
    want_doms = pr["population"]["%s_domains" % a.split]
    arms = ["HD_BASE", "HD_KO", "HD_TOPK", "HD_BOTK"] + sorted(k for k in hs if k.startswith("HD_RAND"))

    landed, fails = {}, []
    for arm in arms:
        # ANCHORED, for the reason strict_run_dir gives at dcs_csi_rederive_patch.py:116 --
        # an unanchored glob also matches every SIBLING ARM whose tag EXTENDS this one, and
        # S-042 records that exact form resolving arm "KO" to the "KO_SELF" directory and
        # turning an identity gate into a comparison that could not fail. No PR-CSI-010 arm
        # name extends another (checked: zero prefix-extending pairs), so this is latent
        # here -- but a gate should not be weaker than the tool it imitates, least of all
        # one whose weaker form has already cost this repo a silent false pass.
        _tag = "%s_%s" % (a.tag_prefix, arm)
        _pat = re.compile(r"^" + re.escape(_tag) + r"_\d{8}_\d{6}_\d+$")
        cands = sorted(d for d in glob.glob(os.path.join(a.root, _tag + "_*"))
                       if _pat.match(os.path.basename(d)))
        cands = [d for d in cands if os.path.exists(os.path.join(d, "DONE.json"))
                 and json.load(open(os.path.join(d, "DONE.json"))).get("status") == "ok"
                 and json.load(open(os.path.join(d, "DONE.json"))).get("rows_written") == want_rows]
        if len(cands) > 1:
            fails.append("%s resolves to %d complete runs (duplicate tag)" % (arm, len(cands)))
            continue
        if cands:
            landed[arm] = arm_liveness(cands[0])

    print("PR-CSI-010 GATE 0 SWEEP -- %s | landed %d of %d arms" % (a.split, len(landed), len(arms)))
    print("%-11s %6s %5s %14s %12s %7s %5s  %s" %
          ("arm", "rows", "dom", "total_prefill", "median_pre", "decode", "viol", "verdict"))
    mk = landed.get("HD_KO", {}).get("median_prefill")
    for arm in arms:
        L = landed.get(arm)
        if L is None:
            print("%-11s %6s" % (arm, "-- not landed --")); continue
        bad = []
        if L["rows"] != want_rows: bad.append("rows!=%d" % want_rows)
        if L["domains"] != want_doms: bad.append("domains!=%d" % want_doms)
        if L["decode"] != 0: bad.append("decode!=0")
        if L["violations"]: bad.append("violations")
        if arm == "HD_BASE":
            if L["total_prefill"] != 0: bad.append("BASE IS INTERVENED")
        else:
            if L["total_prefill"] <= 0: bad.append("no prefill edits")
            # the realised-dose identity: a K-head arm records K x the all-head arm (S-175)
            if arm != "HD_KO":
                # AN ABSENT DENOMINATOR IS "UNCHECKED", NOT "FINE". The previous form was
                # `if mk and ...`, so before HD_KO landed every K=8 arm printed PASS with its dose
                # never compared -- absence reading as a pass, which is the shape of S-168's gate
                # and of the vacuous provenance witness (S-182). The row now says so out loud.
                if not mk:
                    bad.append("DOSE UNCHECKED (HD_KO has not landed; no denominator)")
                else:
                    want = mk * K
                    if abs(L["median_prefill"] - want) > 1e-6:
                        bad.append("dose %.1f != %.1f (K x)" % (L["median_prefill"], want))
            if arm in hs and L["heads"] != ",".join(str(h) for h in hs[arm]):
                bad.append("HEAD SET DRIFT vs prereg")
        print("%-11s %6d %5d %14d %12.1f %7d %5d  %s"
              % (arm, L["rows"], L["domains"], L["total_prefill"], L["median_prefill"],
                 L["decode"], L["violations"], "PASS" if not bad else "FAIL: " + "; ".join(bad)))
        if bad:
            fails.append("%s: %s" % (arm, "; ".join(bad)))

    print()
    if fails:
        print("GATE 0 FAILURES (%d) -- the family is heading for VOID:" % len(fails))
        for f in fails:
            print("   " + f)
        return 1
    print("GATE 0: every landed arm passes. No endpoint field was read.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
