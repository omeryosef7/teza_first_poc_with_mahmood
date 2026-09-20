#!/usr/bin/env python3
"""Aggregate the LLM-judge panel, unblind via the sealed key, and compute the discriminating quantity
-- with the disclaimer-sensitivity diagnostic that decides whether the LLM judge is trustworthy.

The 91 sheet rows ARE the never-refused-in-both stratum (SR>=0.5, MATERIAL present), split
button 28 ko / 28 ctrl and basket 18 ko / 17 ctrl. The discriminating quantity (REVIEW-9/P3) is the
content-true ratio ko/ctrl in this stratum: threshold-one-switch predicts < 1, GATING predicts = 1.
The automated CR-002 endpoint gave 1.000 (button) / 1.059 (basket) but is confounded by disclaimers.
This computes the SAME ratio under the LLM-judge panel and asks whether THAT judge is disclaimer-
confounded too (does its score track cr002_scope_veto?). Independence unit = DOMAIN; button and basket
never pooled. This opens the sealed key -- legitimate now that the sheet is "returned filled in" (by
the LLM panel); the human sheet remains available for an independent human read later.
"""
from __future__ import annotations
import argparse, importlib.util, json, os, statistics, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s); sys.modules[mod] = m; s.loader.exec_module(m); return m


def consensus(scores):
    """Median of the panel's integer scores (odd panel -> majority-like)."""
    return int(round(statistics.median(scores)))


def _atomic_json_dump(obj, path, **kw):
    """Atomic, VERIFIED JSON write. Fix for sprint entry S-124.

    Replaces `json.dump(x, open(p, "w"), ...)`, whose handle is never closed: `open` truncates the
    destination immediately and the buffered bytes are flushed only in the GC finaliser, where
    CPython PRINTS and then SWALLOWS an EDQUOT. A full quota therefore produced a 0-byte file at a
    real artifact name, with "wrote <path>" on stdout and exit status 0 -- indistinguishable from a
    finished report. Temp file + fsync + size check + re-parse + os.replace makes the write ATOMIC
    as well as checked: a half-written file never appears at the real name, and whatever was there
    before survives a failure. On any error this RAISES, naming the path and the byte count.
    """
    import tempfile                        # local: keeps this helper drop-in and import-order-free
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_atomic_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, **kw)
            fh.flush()
            os.fsync(fh.fileno())          # EDQUOT surfaces HERE, not in a GC finaliser
        n = os.path.getsize(tmp)
        if n == 0:
            raise OSError("temp file is 0 bytes after a flush+fsync that reported success")
        with open(tmp, "r", encoding="utf-8") as fh:
            json.load(fh)                  # a truncated write does not re-parse
        try:
            mode = os.stat(path).st_mode & 0o7777   # keep the artifact's existing permissions:
        except OSError:                             # mkstemp makes the temp file 0600 and
            mode = 0o644                            # os.replace would carry that onto the report
        os.chmod(tmp, mode)
        os.replace(tmp, path)              # atomic within the directory
    except Exception as e:
        try:
            n = os.path.getsize(tmp)
        except OSError:
            n = -1
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise OSError("atomic_json_dump FAILED for %s -- %d bytes reached the temp file; the "
                      "destination is UNCHANGED (never truncated). Cause: %r" % (path, n, e)) from e
    return os.path.getsize(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", default=os.path.join(REPO, "reports/DCS_CONT_LLM_JUDGE_PANEL.json"))
    ap.add_argument("--key", default=os.path.join(REPO, "data/labels/dcs_cont_blind_rating_key_R1.json"))
    ap.add_argument("--n-boot", type=int, default=20000)
    ap.add_argument("--out", default=os.path.join(REPO, "reports/DCS_CONT_LLM_JUDGE_RESULT.json"))
    a = ap.parse_args()
    scope = _load("scope", "scripts/dcs_cont_scope.py")

    panel = json.load(open(a.panel)); key = json.load(open(a.key))
    passes = [p for p in panel["passes"] if p.get("ratings")]
    # per-item panel scores
    by_item = {}
    for p in passes:
        for r in p["ratings"]:
            by_item.setdefault(r["item_id"], []).append(int(r["score"]))
    krec = {r["item_id"]: r for r in key["records"]}
    if set(by_item) != set(krec):
        print("WARNING: item mismatch panel=%d key=%d" % (len(by_item), len(krec)))

    # join: per item -> consensus score, codeword, arm, in_slot0, veto
    rows = []
    for iid, scs in by_item.items():
        k = krec[iid]
        rows.append({"item_id": iid, "scores": scs, "consensus": consensus(scs),
                     "codeword": k["codeword"], "arm": k["arm"], "domain": k["domain"],
                     "in_slot0": k["in_slot0"], "veto": bool(k["cr002_scope_veto"])})

    # inter-rater agreement
    n_pass = len(passes)
    allagree = sum(1 for r in rows if len(set(r["scores"])) == 1)
    spread = statistics.mean(max(r["scores"]) - min(r["scores"]) for r in rows) if rows else 0.0

    out = {"schema": "dcs_cont_llm_judge_result/1", "n_passes": n_pass, "n_items": len(rows),
           "framing": "LLM-judge PROXY for the human read; trustworthy only if disclaimer-insensitive "
                      "(see diagnostic). Does NOT replace the human sheet.",
           "inter_rater": {"passes": n_pass, "all_agree_frac": round(allagree / len(rows), 3),
                           "mean_score_spread": round(spread, 3)},
           "discriminating_prediction": "threshold-one-switch: ratio<1; GATING: ratio=1",
           "cr002_automated_reference": {"button": 1.000, "basket": 1.059},
           "by_codeword": {}, "disclaimer_diagnostic": {}}

    for cw in ("button", "basket"):
        cw_rows = [r for r in rows if r["codeword"] == cw]
        doms = sorted({r["domain"] for r in cw_rows})
        res = {"n_ko": sum(r["arm"] == "ko" for r in cw_rows),
               "n_ctrl": sum(r["arm"] == "ctrl" for r in cw_rows), "thresholds": {}}
        for tname, thr in (("content_ge1", 1), ("content_eq2", 2)):
            def per_dom_counts(d):
                ko = sum(1 for r in cw_rows if r["domain"] == d and r["arm"] == "ko" and r["consensus"] >= thr)
                ct = sum(1 for r in cw_rows if r["domain"] == d and r["arm"] == "ctrl" and r["consensus"] >= thr)
                return ko, ct
            ko_pos = sum(1 for r in cw_rows if r["arm"] == "ko" and r["consensus"] >= thr)
            ct_pos = sum(1 for r in cw_rows if r["arm"] == "ctrl" and r["consensus"] >= thr)
            counts = {d: per_dom_counts(d) for d in doms}

            def stat(sample):
                k = sum(counts[d][0] for d in sample); c = sum(counts[d][1] for d in sample)
                return (k / c) if c else None
            try:
                bs = scope.domain_bootstrap(doms, stat, a.n_boot, seed=20260914, max_drop=0.60)
                ci = [round(bs["lo"], 3), round(bs["hi"], 3)]; dropped = bs["draws_dropped"]
            except Exception as e:
                ci = None; dropped = "n/a (%s)" % str(e)[:60]
            res["thresholds"][tname] = {"ko_pos": ko_pos, "ctrl_pos": ct_pos,
                                        "ratio": round(ko_pos / ct_pos, 3) if ct_pos else None,
                                        "ci_domain_bootstrap": ci, "boot_draws_dropped": dropped}
        out["by_codeword"][cw] = res

    # disclaimer-sensitivity diagnostic: does the LLM score track the disclaimer (veto) flag?
    def mean_score(sel):
        v = [r["consensus"] for r in rows if sel(r)]
        return round(statistics.mean(v), 3) if v else None
    diag = {"overall_mean_score_veto_true": mean_score(lambda r: r["veto"]),
            "overall_mean_score_veto_false": mean_score(lambda r: not r["veto"]),
            "note": "if veto_true (disclaimer present) scores LOWER, the LLM judge is disclaimer-"
                    "SENSITIVE -> entangled like CR-002 -> its ratio is suspect. If similar -> the "
                    "LLM judge escapes the confound and its ratio is informative."}
    for cw in ("button", "basket"):
        for arm in ("ko", "ctrl"):
            diag["%s_%s_veto_true" % (cw, arm)] = mean_score(
                lambda r, cw=cw, arm=arm: r["codeword"] == cw and r["arm"] == arm and r["veto"])
            diag["%s_%s_veto_false" % (cw, arm)] = mean_score(
                lambda r, cw=cw, arm=arm: r["codeword"] == cw and r["arm"] == arm and not r["veto"])
    out["disclaimer_diagnostic"] = diag

    _atomic_json_dump(out, a.out, indent=1)
    print(json.dumps(out["by_codeword"], indent=1))
    print("inter-rater:", out["inter_rater"])
    print("disclaimer diagnostic (veto true/false mean score): overall %s / %s"
          % (diag["overall_mean_score_veto_true"], diag["overall_mean_score_veto_false"]))
    print("wrote %s" % os.path.relpath(a.out, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
