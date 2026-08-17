"""analyze_role.py — plan §11: does role framing change Boombness, or only ASR?

The bank varies `role_style` over {plain, tool, user_like, assistant_like, cot_like,
system_like_quoted} while holding the demonstration content, the domain, the demo count and the
final query FIXED. That is the content-constancy design §11 asks for, and it is the same idea the
Role-Confusion codebase uses (`utils/role_templates.render_single_message`) — identical text,
different role markup.

The question §11 poses is a mediation question, and it has three distinguishable answers:

  (a) role → Boombness → ASR     role framing works by making the codeword more concept-like
  (b) role → ASR directly        role framing works by some other route; Boombness is unmoved
  (c) role changes neither       the axis is irrelevant to role framing

Reported per role style: mean Boombness at the layers G2 found predictive, mean ASR, and the
partial association of role with ASR after conditioning on Boombness. Committed, because the last
three ad-hoc tables in this sprint were all wrong.

NOTE ON WHAT THIS CANNOT DO. There is no trained Userness/CoTness probe here yet
(`role_probes.py` ports the machinery but has not been fitted on this model), so `role_style` is
used as a CATEGORICAL PROXY for role, exactly as the plan's §9 permits — and it is labelled as a
proxy rather than presented as a measured role signal.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import statistics as st
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_jsonl, require_done  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--extract", required=True)
    ap.add_argument("--judge", default=None)
    ap.add_argument("--arm", default="natural_doublespeak")
    ap.add_argument("--layers", default="8,12,31")
    ap.add_argument("--out", default=None)
    ap.add_argument("--allow-partial", action="store_true",
                    help="analyse a run with no DONE.json (output must not be reported)")

    args = ap.parse_args()
    if args.extract:
        require_done(args.extract, allow_partial=args.allow_partial)
    if args.judge:
        require_done(args.judge, allow_partial=args.allow_partial)
    layers = [int(x) for x in args.layers.split(",")]

    E = [r for r in read_jsonl(os.path.join(args.extract, "results.jsonl"))
         if r.get("is_final_occurrence") and r.get("condition") == args.arm
         and (r.get("n_examples") or 0) > 0]
    asr = {}
    if args.judge:
        asr = {r["prompt_id"]: r["strongreject_score"]
               for r in read_jsonl(os.path.join(args.judge, "results.jsonl"))
               if r.get("strongreject_score") is not None and r.get("condition") == args.arm}

    by_role: Dict[str, List[Dict]] = collections.defaultdict(list)
    for r in E:
        by_role[r.get("role_style", "?")].append(r)

    print(f"[role] arm={args.arm}; {len(E)} extract rows across "
          f"{len(by_role)} role styles; ASR available for {len(asr)} prompts")
    print("[role] role_style is a CATEGORICAL PROXY for role — no fitted Userness/CoTness probe yet\n")

    cols = [f"d_surface|L{L}|cos" for L in layers]
    hdr = f"{'role_style':22s} {'n':>4s} " + " ".join(f"{c.split('|')[1]:>9s}" for c in cols)
    if asr:
        hdr += f" {'n_asr':>6s} {'mean_ASR':>9s}"
    print(hdr)
    report: Dict[str, object] = {"arm": args.arm, "layers": layers,
                                 "extract": os.path.abspath(args.extract),
                                 "judge": os.path.abspath(args.judge) if args.judge else None,
                                 "proxy_note": "role_style is a categorical proxy; no fitted role probe",
                                 "by_role": {}}
    for role in sorted(by_role):
        rs = by_role[role]
        vals = {c: [r[c] for r in rs if c in r] for c in cols}
        line = f"{role:22s} {len(rs):>4d} " + " ".join(
            f"{(st.mean(vals[c]) if vals[c] else float('nan')):>+9.4f}" for c in cols)
        rec = {"n": len(rs), **{c: (st.mean(vals[c]) if vals[c] else None) for c in cols}}
        aa = [asr[r["prompt_id"]] for r in rs if r["prompt_id"] in asr]
        if asr:
            line += f" {len(aa):>6d} {(st.mean(aa) if aa else float('nan')):>9.4f}"
            rec["n_asr"] = len(aa)
            rec["mean_asr"] = st.mean(aa) if aa else None
        report["by_role"][role] = rec
        print(line)

    # Is the role effect on ASR mediated by Boombness? Compare a role-only model with a
    # role+Boombness model, on the rows that have both.
    if asr:
        try:
            import numpy as np
            from sklearn.linear_model import LinearRegression
            rows = [r for r in E if r["prompt_id"] in asr]
            roles = sorted({r.get("role_style", "?") for r in rows})
            if len(rows) > 10 and len(roles) > 1:
                X_role = np.array([[1.0 if r.get("role_style") == q else 0.0 for q in roles[1:]]
                                   for r in rows])
                b = np.array([[r.get(f"d_surface|L{L}|cos", 0.0) for L in layers] for r in rows])
                y = np.array([asr[r["prompt_id"]] for r in rows])
                r_role = LinearRegression().fit(X_role, y).score(X_role, y)
                r_b = LinearRegression().fit(b, y).score(b, y)
                r_both = LinearRegression().fit(np.column_stack([X_role, b]), y).score(
                    np.column_stack([X_role, b]), y)
                print(f"\n  R2 role-only {r_role:.4f} | Boombness-only {r_b:.4f} | both {r_both:.4f}")
                print(f"  role adds over Boombness: {r_both - r_b:+.4f}; "
                      f"Boombness adds over role: {r_both - r_role:+.4f}  (n={len(rows)})")
                report["mediation"] = {"n": len(rows), "r2_role": r_role, "r2_boombness": r_b,
                                       "r2_both": r_both,
                                       "role_adds_over_boombness": r_both - r_b,
                                       "boombness_adds_over_role": r_both - r_role}
        except Exception as e:
            print(f"  (mediation skipped: {type(e).__name__}: {e})")

    out = args.out or os.path.join(args.extract, "role_analysis.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n[role] -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
