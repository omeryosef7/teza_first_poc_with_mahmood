"""Read a scoped-knockout liveness smoke as a WHOLE and emit a pass/fail artifact.

PR-1 of this phase fixes the smoke's pass conditions before the code exists, and says the smoke is
"read as a whole or not at all": a mode that silently collapsed into another looks perfectly healthy
arm-by-arm.  This module encodes exactly those conditions so the verdict is a committed artifact
rather than a sentence in a log.

The five checks, per PR-1:

1. **declared counters** — every arm satisfies its own mode's ``LIVENESS_REQUIREMENT`` (> 0) and
   ``LIVENESS_MUST_BE_ZERO`` (== 0).  Read from ``pair_common`` so this file cannot drift from the hook.
2. **the hook was asked** — a correctly-scoped hook and a DEAD hook both report zero edits.  What
   separates them is that the scoped one was *called*: its forward counters on the half where it
   edits nothing must still be positive.  This is the check that makes a zero meaningful.
3. **generations changed** vs the session's own baseline, by TEXT HASH (never by length -- that is the
   ``uniq_frac`` defect).
4. **disjointness and subset** — ``query_prefill_only`` and ``demo_processing_only`` edit disjoint
   query-row sets at prefill, and their union sits inside ``legacy_all_query``'s.  Checked as an
   inequality on prefill-edit totals: an equality would be wrong, because the arms generate different
   text and their totals legitimately differ.
5. **the primary arm spans both halves** — ``response_query_only`` is the only scoped mode with both
   counters positive.

Scalar fields only: no prompt or completion text is read out, and generation comparison is by hash.

Usage
-----
    python src/boombness/scoped_smoke_verdict.py \
        --baseline outputs/boombness/score_behavior/s1A_... \
        --arm legacy_all_query=outputs/boombness/score_behavior/s1_legacy_all_query_... \
        --arm decode_only=... [--arm ...] --tag s1verdict
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "doublespeak_causality"))

import common  # noqa: E402
import pair_common as pc  # noqa: E402


def _h(s):
    return hashlib.sha256((s or "").encode()).hexdigest()[:16]


def load_rows(run_dir):
    """prompt_id -> the scalar hook fields plus a HASH of the generation.  Never the text."""
    out = {}
    with open(os.path.join(run_dir, "gens.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            out[r["prompt_id"]] = {
                "gen_sha16": _h(r.get("generation")),
                "n_chars": r.get("n_chars"),
                "stop_reason": r.get("stop_reason"),
                "prefill_edits": r.get("hook_n_prefill_edits"),
                "decode_edits": r.get("hook_n_decode_edits"),
                "prefill_forward": r.get("hook_n_prefill_forward"),
                "decode_forward": r.get("hook_n_decode_forward"),
                "violations": r.get("hook_liveness_violations"),
            }
    return out


def check_arm(mode, rows, live):
    """PR-1 checks 1 and 2 for one arm."""
    req = list(pc.LIVENESS_REQUIREMENT[mode])
    zero = list(pc.LIVENESS_MUST_BE_ZERO[mode])
    fails = []

    # (1) the declared contract, per row -- reuse the hook's own gate, never restate the rule here.
    n_bad = 0
    for pid, r in rows.items():
        stats = {"n_prefill_edits": r["prefill_edits"] or 0,
                 "n_decode_edits": r["decode_edits"] or 0}
        if pc.scoped_liveness_violations(mode, stats):
            n_bad += 1
    if n_bad:
        fails.append(f"{n_bad}/{len(rows)} rows violate the {mode} liveness contract")

    # (2) THE CHECK THAT MAKES A ZERO MEANINGFUL: on the half where this mode edits nothing,
    #     the hook must still have been CALLED. Zero edits + zero forwards is a dead hook.
    asked = {}
    for key, fwd in (("n_prefill_edits", "prefill_forward"), ("n_decode_edits", "decode_forward")):
        if key in zero:
            mins = [r[fwd] or 0 for r in rows.values()]
            asked[fwd] = min(mins) if mins else 0
            if asked[fwd] <= 0:
                fails.append(f"{mode} edits nothing at {fwd} AND was never called there: DEAD, not scoped")
    return {
        "mode": mode,
        "n_rows": len(rows),
        "liveness_required": req,
        "liveness_must_be_zero": zero,
        "total_prefill_edits": sum(r["prefill_edits"] or 0 for r in rows.values()),
        "total_decode_edits": sum(r["decode_edits"] or 0 for r in rows.values()),
        "min_forwards_where_forbidden": asked,
        "frac_rows_scope_live": live.get("frac_rows_scope_live"),
        "scope_violations": live.get("scope_violations"),
        "fails": fails,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--arm", action="append", default=[], metavar="LABEL=MODE=RUNDIR",
                    help="LABEL=MODE=RUNDIR. LABEL is the KEY and must be unique; MODE is the "
                         "knockout scope. They are separate because two arms can legitimately run "
                         "the SAME mode at different bands -- the Phase-1 session has "
                         "C_response_query_only at 6-14 and D_response_query_late_control at 20-31. "
                         "Keying by mode alone would silently drop one of them, which is prev-C-18's "
                         "defect reproduced inside the tool written to catch it.")
    ap.add_argument("--tag", default="smokeverdict")
    ap.add_argument("--experiment", default="scoped_smoke_verdict")
    args = ap.parse_args()

    run = common.RunDir(args.experiment, args=args, tag=args.tag)
    ledger = common.FailureLedger()

    base = load_rows(args.baseline)
    arms, per_arm = {}, {}
    for spec in args.arm:
        parts = spec.split("=", 2)
        if len(parts) == 3:
            label, mode, d = parts
        elif len(parts) == 2:                    # back-compat: MODE=RUNDIR, label defaults to mode
            mode, d = parts
            label = mode
        else:
            raise SystemExit(f"[verdict] REFUSING: --arm needs LABEL=MODE=RUNDIR, got {spec!r}")
        if mode not in pc.SCOPED_KNOCKOUT_MODES:
            raise SystemExit(f"[verdict] REFUSING: unknown mode {mode!r}")
        if label in per_arm:
            raise SystemExit(f"[verdict] REFUSING: duplicate arm label {label!r}. Labels are the "
                             f"dict key; a collision would silently drop an arm.")
        rows = load_rows(d)
        live = (json.load(open(os.path.join(d, "summary.json"))).get("knockout_liveness") or {})
        arms[label] = rows
        rec = check_arm(mode, rows, live)
        rec["arm_label"] = label
        # (3) generations changed vs the session's own baseline, by hash
        common_ids = [p for p in base if p in rows]
        rec["n_common_with_baseline"] = len(common_ids)
        rec["n_generations_changed"] = sum(
            1 for p in common_ids if rows[p]["gen_sha16"] != base[p]["gen_sha16"])
        if rec["n_common_with_baseline"] and rec["n_generations_changed"] == 0:
            rec["fails"].append(f"{mode} changed NO generation: the edit never reached the computation")
        for p in base:
            ledger.ok() if p in rows else ledger.fail("prompt_missing_from_arm", f"{mode}:{p}")
        rec["run_dir"] = d
        per_arm[label] = rec

    checks = {}
    # (4) disjointness / subset, as an INEQUALITY (see the module docstring)
    def by_mode(m):
        """The arms running mode ``m``. A list, because two arms may share a mode at different bands."""
        return [r for r in per_arm.values() if r["mode"] == m]

    trio = {m: by_mode(m) for m in ("legacy_all_query", "query_prefill_only", "demo_processing_only")}
    if all(len(v) == 1 for v in trio.values()):
        lp = trio["legacy_all_query"][0]["total_prefill_edits"]
        qp = trio["query_prefill_only"][0]["total_prefill_edits"]
        dp = trio["demo_processing_only"][0]["total_prefill_edits"]
        checks["prefill_subset"] = {
            "legacy": lp, "query_prefill_only": qp, "demo_processing_only": dp,
            "sum_scoped": qp + dp, "slack": lp - (qp + dp), "holds": (qp + dp) <= lp,
            "NOTE": ("upper bound, not equality: the slack is prefill query rows in NEITHER span "
                     "(template/preamble). An equality would be wrong."),
        }
    # (5) the primary arm spans both halves
    rq = by_mode("response_query_only")
    if rq:
        # If two arms share this mode (arm vs late control), check EVERY one of them rather than
        # whichever happened to be written last.
        r = min(rq, key=lambda x: x["arm_label"])
        checks["primary_arm_spans_both"] = {
            "arm_labels_checked": sorted(x["arm_label"] for x in rq),
            "all_span_both": all(x["total_prefill_edits"] > 0 and x["total_decode_edits"] > 0
                                 for x in rq),
            "total_prefill_edits": r["total_prefill_edits"],
            "total_decode_edits": r["total_decode_edits"],
            "holds": all(x["total_prefill_edits"] > 0 and x["total_decode_edits"] > 0 for x in rq),
        }

    all_fails = [f for r in per_arm.values() for f in r["fails"]]
    all_fails += [f"check {k} FAILED" for k, v in checks.items() if not v.get("holds", True)]
    verdict = "PASS" if not all_fails else "FAIL"

    out = {"schema": "SCOPED_SMOKE_VERDICT/1", "verdict": verdict, "failures": all_fails,
           "baseline_run_dir": args.baseline, "per_arm": per_arm, "cross_arm_checks": checks,
           "PR": "PR-1: the smoke is read as a whole or not at all"}
    path = os.path.join(run.path, "scoped_smoke_verdict.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    run.finish(summary={"verdict": verdict, "n_arms": len(per_arm),
                        "n_failures": len(all_fails)}, ledger=ledger)
    print(f"[verdict] {verdict} — {len(per_arm)} arms, {len(all_fails)} failures -> {path}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
