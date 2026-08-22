"""depth_profile_matched.py — the refusal-channel depth profile, from WITHIN-SESSION arm/control pairs.

WHY THIS ONE IS BETTER THAN THE ONES BEFORE IT.

`judge_session_drift.py` showed the judge moves 0.0057 between sessions on byte-identical text, and
that every delta in the in-subspace null is cross-session. That is a real limit on precision, and the
previous two analyses had to work around it by reporting drift-scaled readings instead of tests.

These arms do not need the workaround. Judging session 20260819_194551 contains the `refusalness:
project_out` arms at L14/L16/L20 **and their magnitude-matched random controls**, and the `fu2_*`
batch pairs `d_surface:project_out:15` with its own control. Arm and control judged together, on the
same prompts, means the session term cancels in the contrast -- which is the comparison the design
was always supposed to make.

WHAT IT SHOWS. Projecting out `refusalness` has a strong depth profile with a mid-late peak, while
projecting out `d_surface` at L15 and beyond is flat null. Both measured against controls judged
alongside them.

WHAT IT DOES NOT SHOW. `d_surface` at L29/L30/L31 has NO control in its session, so those three are
reported as cross-session deltas with drift as the scale, and are not given a paired test. Marked
`matched: false` -- the distinction is in the artifact, not just in this docstring.

Paired per prompt_id, domain-clustered with G-1 df, exact cluster sign-flip. Numeric/categorical only.
"""
from __future__ import annotations

import argparse
import glob
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from unanalysed_inventory import git_commit_safe  # noqa: E402


def load(prefix, root="outputs/boombness/judge"):
    """Union disjoint shards of one logical run -> {prompt_id: (malicious, domain)}."""
    out, dirs = {}, sorted(glob.glob(os.path.join(root, prefix + "*")))
    for d in dirs:
        f = os.path.join(d, "results.jsonl")
        if not os.path.exists(f):
            continue
        for line in open(f, encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            pid, v = r.get("prompt_id"), r.get("malicious_at_0.5")
            if pid is not None and v is not None:
                out[pid] = (1 if v else 0, r.get("domain"))
    return out, [os.path.basename(x) for x in dirs]


def signflip_p(by_dom):
    """Exact two-sided cluster sign-flip over informative domains."""
    vals = [v for v in by_dom.values() if abs(v) > 1e-12]
    k = len(vals)
    if k == 0:
        return None, 0, None
    obs = abs(sum(vals))
    hits = 0
    for signs in itertools.product((1, -1), repeat=k):
        if abs(sum(s * v for s, v in zip(signs, vals))) >= obs - 1e-12:
            hits += 1
    return hits / (2 ** k), k, 2.0 / (2 ** k)


def contrast(a_rows, b_rows):
    """Paired arm-minus-reference on common prompts, plus per-domain means."""
    common = set(a_rows) & set(b_rows)
    if not common:
        return None
    diffs, dom = [], {}
    for pid in common:
        d = a_rows[pid][0] - b_rows[pid][0]
        diffs.append(d)
        dom.setdefault(a_rows[pid][1], []).append(d)
    by_dom = {k: sum(v) / len(v) for k, v in dom.items()}
    p, k, floor = signflip_p(by_dom)
    return {"n_common": len(common), "delta": sum(diffs) / len(diffs),
            "delta_domain_clustered": sum(by_dom.values()) / len(by_dom),
            "n_domains": len(by_dom), "n_informative_clusters": k,
            "p_cluster_signflip": p, "min_attainable_cluster_p": floor}


# (label, layer, arm prefix, control prefix or None, family)
PAIRS = [
    ("refusalness L14", 14, "k_fuR14_C_",  "k_fuR14_Cctrl_",  "refusalness"),
    ("refusalness L16", 16, "k_fuR16_C_",  "k_fuR16_Cctrl_",  "refusalness"),
    ("refusalness L20", 20, "k_fuR20_C_",  "k_fuR20_Cctrl_",  "refusalness"),
    ("d_surface L15",   15, "fu2_abL15_B_", "fu2_abL15_Bctrl_", "d_surface"),
    ("d_surface L29",   29, "dsL29J",      None,               "d_surface"),
    ("d_surface L30",   30, "dsL30J",      None,               "d_surface"),
    ("d_surface L31",   31, "dsL31J",      None,               "d_surface"),
    ("refusalness L12", 12, "fu2_abR12_C_", None,              "refusalness"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline-prefix", default="abg_base_")
    ap.add_argument("--drift-json", default="outputs/boombness/judge_session_drift.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    try:
        drift = json.load(open(a.drift_json))["advbench_baseline_drift"]
    except Exception:
        drift = None
    base, base_dirs = load(a.baseline_prefix)

    rows = []
    for label, L, armp, ctlp, fam in PAIRS:
        arm, arm_dirs = load(armp)
        if not arm:
            continue
        rec = {"label": label, "layer": L, "family": fam, "arm_shards": arm_dirs,
               "arm_n": len(arm), "arm_asr": sum(v[0] for v in arm.values()) / len(arm)}
        if ctlp:
            ctl, ctl_dirs = load(ctlp)
            c = contrast(arm, ctl)
            rec.update({"matched": True, "control_shards": ctl_dirs,
                        "control_asr": sum(v[0] for v in ctl.values()) / len(ctl),
                        "vs_matched_control": c,
                        "why": "arm and control judged in the same session; the session term cancels"})
        else:
            c = contrast(arm, base)
            rec.update({"matched": False, "vs_baseline_CROSS_SESSION": c,
                        "delta_over_drift": (abs(c["delta"]) / drift) if (c and drift) else None,
                        "why": "no control judged in this arm's session; cross-session, drift-scaled, "
                               "no paired test quoted as a result"})
        rows.append(rec)

    out = {
        "question": "how do refusalness- and d_surface-projection effects vary with DEPTH, measured "
                    "against controls judged alongside them?",
        "judge_session_drift": drift,
        "baseline": {"prefix": a.baseline_prefix, "n": len(base), "shards": base_dirs},
        "design_note": (
            "the matched rows are the only ones in this sprint's late-layer work where arm and "
            "control share a judging session. For them the session term cancels and a paired "
            "cluster test is legitimate. The unmatched rows are reported drift-scaled and are NOT "
            "given a test."),
        "rows": rows,
        "provenance": {"argv": sys.argv, "git_commit": git_commit_safe()},
    }
    with open(a.out, "w") as f:
        json.dump(out, f, indent=2)

    print(f"drift={drift}\n")
    print(f"{'arm':<20}{'matched':>8}{'armASR':>8}{'refASR':>8}{'delta':>9}{'clust':>9}"
          f"{'p':>9}{'floor':>8}{'k':>3}")
    for r in rows:
        c = r.get("vs_matched_control") or r.get("vs_baseline_CROSS_SESSION") or {}
        g = lambda k, w, p=4: (f"{c[k]:>{w}.{p}f}" if isinstance(c.get(k), float) else f"{'':>{w}}")
        ref = r.get("control_asr")
        ref_s = f"{ref:.4f}" if isinstance(ref, float) else ""
        k_s = str(c.get("n_informative_clusters", ""))
        print(f"{r['label']:<20}{str(r['matched']):>8}{r['arm_asr']:>8.4f}{ref_s:>8}"
              f"{g('delta',9)}{g('delta_domain_clustered',9)}{g('p_cluster_signflip',9)}"
              f"{g('min_attainable_cluster_p',8)}{k_s:>3}")
    print("\n  matched=False rows are cross-session; their p is NOT quoted as a result.")
    print(f"\n[depth-profile] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
