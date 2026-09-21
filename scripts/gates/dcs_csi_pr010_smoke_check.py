"""Adjudicate design section 7.3's smoke. Every PASS condition is checked EXPLICITLY and named.

WHY EACH CONDITION IS PRINTED SEPARATELY. A single "SMOKE PASSED" line is the shape of gate that
S-168 caught printing PASS over zero rows. Here each of section 7.3's clauses gets its own line with
the measured value beside it, and a missing input is a REFUSAL rather than a skipped check.

THE CENTRAL ONE IS THE 1/4 DOSE IDENTITY. `median_prefill_edits` for 8 of 32 heads must be exactly
a quarter of the all-head arm's. S-175 re-derived why it is 1/4 and not 1/32: the counter measures
MASK WRITES, and the all-head arm (heads=None) never expands -- it writes ONE row that broadcasts to
all 32 heads -- while a K-head arm expands to 32 and writes K explicit rows. So the ratio is
K/32 * (rows written per arm), and with the all-head arm recording 1 per row the comparison the
design asks for is on the MEDIAN PREFILL EDITS, which scale as K/32 only after the expansion. This
check therefore reports BOTH the raw ratio and the design's expected value, and refuses to call a
mismatch a pass.
"""
import argparse, glob, json, os, sys


def newest_run(root, tag, job=None):
    """The run dir for `tag`, refusing if the filter leaves anything but exactly one candidate.
    S-104/S-127: a re-run recreates the same tag under a new job id, and picking 'the newest'
    silently admits the wrong arm."""
    cands = []
    for d in sorted(glob.glob(os.path.join(root, "*"))):
        cfg = os.path.join(d, "config.json")
        if not os.path.exists(cfg):
            continue
        try:
            c = json.load(open(cfg))
        except Exception:
            continue
        args = c.get("args", c)
        if args.get("tag") != tag:
            continue
        if job is not None:
            rm = os.path.join(d, "RUNMETA.json")
            jid = None
            if os.path.exists(rm):
                try:
                    jid = str(json.load(open(rm)).get("slurm_job_id"))
                except Exception:
                    jid = None
            if jid != str(job):
                continue
        cands.append(d)
    if len(cands) != 1:
        sys.exit("REFUSING: tag %r resolved to %d run dirs%s -- the filter must leave exactly one"
                 % (tag, len(cands), (" for job %s" % job) if job else ""))
    return cands[0]


def load(d):
    out = {}
    for f in ("config.json", "summary.json", "DONE.json"):
        p = os.path.join(d, f)
        out[f] = json.load(open(p)) if os.path.exists(p) else None
    if out["DONE.json"] is None:
        sys.exit("REFUSING: %s has no DONE.json -- an unfinished run is not evidence" % d)
    return out


def dig(obj, *keys):
    for k in keys:
        if isinstance(obj, dict) and k in obj:
            obj = obj[k]
        else:
            return None
    return obj


def find_liveness(summary):
    """knockout_liveness may sit at the top level or under a readout block."""
    if not isinstance(summary, dict):
        return None
    if "knockout_liveness" in summary:
        return summary["knockout_liveness"]
    for v in summary.values():
        if isinstance(v, dict) and "knockout_liveness" in v:
            return v["knockout_liveness"]
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="outputs/boombness/score_behavior")
    ap.add_argument("--ko-tag", default="csi3_smoke_basket_SMOKE_HD_KO")
    ap.add_argument("--h8-tag", default="csi3_smoke_basket_SMOKE_HD_8")
    ap.add_argument("--atp", required=True, help="the SMOKE_ATP artifact")
    ap.add_argument("--job", default=None, help="restrict both tags to this slurm job id")
    ap.add_argument("--max-wall-ratio", type=float, default=1.5,
                    help="design 7.2: above this the cost table is re-derived and nothing launches")
    a = ap.parse_args()

    fail = []

    def chk(ok, label, detail=""):
        print("  %-4s %-58s %s" % ("PASS" if ok else "FAIL", label, detail))
        if not ok:
            fail.append(label)

    ko = load(newest_run(a.root, a.ko_tag, a.job))
    h8 = load(newest_run(a.root, a.h8_tag, a.job))
    lk, l8 = find_liveness(ko["summary.json"]), find_liveness(h8["summary.json"])
    if lk is None or l8 is None:
        sys.exit("REFUSING: knockout_liveness absent from a summary -- cannot adjudicate liveness")

    print("section 7.3 SMOKE ADJUDICATION")
    print("  SMOKE_HD_KO rows=%s  SMOKE_HD_8 rows=%s"
          % (ko["DONE.json"].get("rows_written"), h8["DONE.json"].get("rows_written")))
    print()
    print("[1] both arms completed over the SAME non-zero row set")
    nk, n8 = ko["DONE.json"].get("rows_written"), h8["DONE.json"].get("rows_written")
    chk(bool(nk) and nk == n8 == 24, "rows_written == 24 on both", "%s vs %s" % (nk, n8))
    chk(ko["DONE.json"].get("status") == "ok" and h8["DONE.json"].get("status") == "ok",
        "both DONE.json status == ok")

    print()
    print("[2] the head restriction reached the hook -- THE 1/4 DOSE IDENTITY")
    mk, m8 = lk.get("median_prefill_edits"), l8.get("median_prefill_edits")
    ratio = (m8 / mk) if (mk not in (None, 0) and m8 is not None) else None
    chk(ratio is not None and abs(ratio - 0.25) < 1e-9,
        "median_prefill_edits(8 heads) == 1/4 of all-head",
        "%s / %s = %s" % (m8, mk, ("%.6f" % ratio) if ratio is not None else "N/A"))

    print()
    print("[3] liveness, on BOTH arms")
    for nm, l in (("SMOKE_HD_KO", lk), ("SMOKE_HD_8", l8)):
        chk(l.get("scope_violations") == {}, "%s scope_violations == {}" % nm,
            repr(l.get("scope_violations")))
        chk(l.get("frac_rows_scope_live") == 1.0, "%s frac_rows_scope_live == 1.0" % nm,
            repr(l.get("frac_rows_scope_live")))
        chk((l.get("total_prefill_edits") or 0) > 0, "%s total_prefill_edits > 0" % nm,
            repr(l.get("total_prefill_edits")))
        chk((l.get("total_decode_edits") or 0) == 0, "%s total_decode_edits == 0" % nm,
            repr(l.get("total_decode_edits")))

    print()
    print("[4] provenance persisted")
    got = dig(h8["config.json"], "args", "knockout_heads")
    chk(got == "0,1,2,3,4,5,6,7", "config.json args.knockout_heads is the placeholder set", repr(got))
    chk(dig(ko["config.json"], "args", "knockout_heads") in ("", None),
        "the all-head arm recorded NO head list", repr(dig(ko["config.json"], "args", "knockout_heads")))

    print()
    print("[5] the 8-head arm is NOT a no-op -- y_install must differ from the all-head arm")
    yk, y8 = dig(ko["summary.json"], "y_install"), dig(h8["summary.json"], "y_install")
    if yk is None or y8 is None:
        chk(False, "y_install present in both summaries", "%r / %r" % (yk, y8))
    else:
        chk(abs(float(yk) - float(y8)) > 1e-9, "y_install differs between the arms",
            "%.6f vs %.6f" % (float(yk), float(y8)))

    print()
    print("[6] the section 7.2 COST RISK, measured rather than assumed")
    wk, w8 = ko["DONE.json"].get("wall_seconds"), h8["DONE.json"].get("wall_seconds")
    wr = (w8 / wk) if (wk not in (None, 0) and w8) else None
    chk(wr is not None and wr <= a.max_wall_ratio,
        "head-restricted wall ratio <= %.2f" % a.max_wall_ratio,
        "%s / %s = %s" % (w8, wk, ("%.3f" % wr) if wr is not None else "N/A"))
    if wr is not None and wr > a.max_wall_ratio:
        print("       -> section 7.2's table MUST be re-derived from %.3f before anything launches" % wr)

    print()
    print("[7] SMOKE_ATP")
    if not os.path.exists(a.atp):
        chk(False, "the SMOKE_ATP artifact exists", a.atp)
    else:
        at = json.load(open(a.atp))
        lv = at.get("liveness", {})
        chk((lv.get("ko_delta_total") or 0) > 0,
            "z_ko != z_clean (a no-op knockout makes AtP identically zero)",
            repr(lv.get("ko_delta_total")))
        chk((lv.get("g_norm_total") or 0) > 0, "the backward is live", repr(lv.get("g_norm_total")))
        chk(at.get("attn_implementation_loaded") == "eager", "AtP ran under LOADED eager")
        chk((at.get("n_rows_used") or 0) > 0, "AtP used a non-zero row set",
            repr(at.get("n_rows_used")))

    print()
    print("  NOT CHECKED HERE: section 7.3 clause 3's 'M equals results.jsonl semantic_logodds to")
    print("  < 1e-3' and 'a ZHeadPatch moves M' -- the first needs the AtP script to emit per-row M")
    print("  alongside the arm's rows, which it does not yet; the second is what W2's gate already")
    print("  measures at scale (916044). Both are named so neither is silently assumed.")

    print()
    if fail:
        print("SMOKE FAILED: %d condition(s) -- %s" % (len(fail), "; ".join(fail)))
        print("NOTHING IN SECTION 7.2 MAY BE LAUNCHED.")
        sys.exit(1)
    print("SMOKE PASSED -- section 7.2 may be costed. THE PLACEHOLDER HEAD SET 0..7 IS DISCARDED;")
    print("the real arms use PR-CSI-010's frozen HD_TOPK.")


if __name__ == "__main__":
    main()
