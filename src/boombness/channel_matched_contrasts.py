"""channel_matched_contrasts.py — d_surface vs a magnitude-matched random direction, at EQUAL DOSE,
in the SAME judging session.

WHY THIS IS THE COMPARISON THAT WAS MISSING.

Every late-layer result in this sprint so far has been either cross-session (and so carried a 0.0057
judge-drift uncertainty) or matched to a random direction at a different depth. The previous tick's
depth profile could say "refusal projection beats a matched random projection", but not which channel
is larger at equal dose, because nothing had been run that way.

It had. Judging session `20260819_231331` contains, together on the same prompts:

    n_fuF25_addS        d_surface:add:8-8:0.25
    n_fuF25_addCtrl8    random:add:8-8:0.25          <- same mode, same layer, same dose, same session
    n_fuF25_addBoth     d_surface:add:8-8:0.25 + refusalness:add:18-18:0.25
    n_fuF25_remR_addS   refusalness:project_out:18-18:1.0 + d_surface:add:8-8:0.25

and session `20260819_214330` contains `m_fuF_remS_addR` with two matched random controls at the two
layers it touches. Arm and control judged together means the session term cancels exactly, so these
are paired cluster tests rather than drift-scaled readings.

DOSE UNITS -- and a correction to what this docstring used to claim (audit #14).

It said the units were "verified from each run's own `summary.json`". That verification never
happened: the `dose_unit` field is written by `score_behavior` as an UNCONDITIONAL string literal on
every intervened run, before the intervention is even built, so it reads "gap (alpha=1 == one
diff-of-means) for mode=add" even on `refusalness:add` runs, which are dosed in their own unit norm
instead. The field is therefore wrong exactly where it matters, and the helper that read it was never
called. Both are recorded here rather than quietly deleted, because a field that contradicts the
analysis is worse than a missing one.

What actually protects this comparison is `applied_magnitude()`, which RECONSTRUCTS the injected
magnitude from the fit payload: refusalness at its own norm (alpha == magnitude), everything else at
alpha x gap(layer), with gap(L8)=6.0549 and gap(L18)=14.7925. That is what identifies the one
dose-matched contrast here and the two that are overdosed 6.05x and 14.79x -- the F-3 trap, which
exists because "the flag says 1.0 on both" is not evidence that the magnitudes match.

RELATION TO THE RETRACTED REFUSAL LADDER. Last tick I withdrew a claim about `d_surface:add` and
refusal rate: it was counted with a regex that only ran on short outputs, so it measured refusal
*shortening*. This measures judged ASR against a matched control in the same session, which is a
different and much better instrument. It is not a rehabilitation of that claim -- it is a different
claim that happens to concern the same arms.

Numeric/categorical fields only.
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


GAP_CACHE = {}


def gap_at(layer, fit_dir="outputs/boombness/extract_boombness/full_20260816_185942_1008673"):
    """The d_surface gap at `layer` -- the unit every non-refusalness `add` is dosed in."""
    if not GAP_CACHE:
        try:
            import torch
            pay = torch.load(os.path.join(fit_dir, "directions_fit_dev.pt"),
                             map_location="cpu", weights_only=False)
            for L, v in (pay.get("gap", {}).get("d_surface", {}) or {}).items():
                GAP_CACHE[int(L)] = float(v)
        except Exception:
            GAP_CACHE[-1] = None
    return GAP_CACHE.get(int(layer))


def applied_magnitude(spec_list):
    """EFFECTIVE injected magnitude per add-spec -- the number the F-3 retraction exists to protect.

    `score_behavior._report_add_magnitude`: refusalness is dosed in its OWN unit norm, so
    alpha == magnitude; EVERY OTHER direction is dosed in units of the d_surface gap, so
    magnitude = alpha * gap(layer). Identical-looking alphas therefore mean very different physical
    edits. These runs predate the ADD DOSE log line (added 2026-08-22), so the magnitude is
    reconstructed here from the fit payload rather than read from a log that does not exist.
    """
    out = []
    for s in spec_list or []:
        if s.get("mode") != "add":
            continue
        for L in s.get("layers") or []:
            a = float(s.get("alpha", 0.0))
            name = s.get("direction")
            if name == "refusalness":
                out.append({"direction": name, "layer": L, "alpha": a, "unit": 1.0,
                            "magnitude": a, "unit_basis": "own unit norm"})
            else:
                g = gap_at(L)
                out.append({"direction": name, "layer": L, "alpha": a, "unit": g,
                            "magnitude": (a * g) if g else None,
                            "unit_basis": "d_surface gap"})
    return out


def specs_of(prefix, root="outputs/boombness/judge"):
    for d in sorted(glob.glob(os.path.join(root, prefix + "*"))):
        try:
            cfg = json.load(open(os.path.join(d, "config.json")))
            g = str((cfg.get("args", cfg) or {}).get("gens") or "").rstrip("/")
            g = os.path.dirname(g) if g.endswith("gens.jsonl") else g
            m = json.load(open(os.path.join(g, "metadata.json")))
            return m.get("intervention_specs") or [], m.get("dose_unit")
        except Exception:
            continue
    return [], None



def signflip(by_dom):
    vals = [v for v in by_dom.values() if abs(v) > 1e-12]
    k = len(vals)
    if k == 0:
        return None, 0, None
    obs = abs(sum(vals))
    hits = sum(1 for s in itertools.product((1, -1), repeat=k)
               if abs(sum(x * v for x, v in zip(s, vals))) >= obs - 1e-12)
    return hits / (2 ** k), k, 2.0 / (2 ** k)


def contrast(a, b):
    common = set(a) & set(b)
    if not common:
        return None
    dom, diffs = {}, []
    for pid in common:
        d = a[pid][0] - b[pid][0]
        diffs.append(d)
        dom.setdefault(a[pid][1], []).append(d)
    by = {k: sum(v) / len(v) for k, v in dom.items()}
    p, k, floor = signflip(by)
    return {"n_common": len(common), "delta": sum(diffs) / len(diffs),
            "delta_domain_clustered": sum(by.values()) / len(by), "n_domains": len(by),
            "n_informative_clusters": k, "p_cluster_signflip": p,
            "min_attainable_cluster_p": floor,
            "p_is_at_floor": (p is not None and floor is not None and abs(p - floor) < 1e-12)}


CONTRASTS = [
    ("d_surface add 0.25  vs  magnitude-matched RANDOM add 0.25 (L8)  [THE dose-matched test]",
     "n_fuF25_addS_", "n_fuF25_addCtrl8_", "20260819_231331",
     "same mode, same layer, same dose, same session: the equal-dose channel test"),
    # ARM-vs-ARM, not arm-vs-control: the two differ by one added component, so `dose_matched`
    # is reported False (different numbers of add-specs) and that is correct, not a warning.
    ("add BOTH (d_surface+refusalness)  vs  d_surface alone  [arm-vs-arm]",
     "n_fuF25_addBoth_", "n_fuF25_addS_", "20260819_231331",
     "does adding refusalness on top of d_surface change anything? arm-vs-arm: the pair differs by "
     "one component, so a dose match is not the relevant property"),
    ("remove refusalness + add d_surface  vs  add d_surface alone  [arm-vs-arm]",
     "n_fuF25_remR_addS_", "n_fuF25_addS_", "20260819_231331",
     "is d_surface's effect gated by refusal being present?"),
    # ⛔ NOT DOSE-MATCHED. Kept, labelled, and excluded from any "matched" reading -- deleting them
    # would hide the trap instead of documenting it.
    ("remove d_surface + add refusalness  vs  random add 1.0 (L8) — DOSE-MISMATCHED 6.05x",
     "m_fuF_remS_addR_", "m_fuF_addCtrl8_", "20260819_214330",
     "arm injects refusalness at magnitude 1.0 (own norm); the control injects 1.0 x gap(L8)=6.0549. "
     "The control is overdosed 6.05x -- not a control."),
    ("remove d_surface + add refusalness  vs  random add 1.0 (L18) — DOSE-MISMATCHED 14.79x",
     "m_fuF_remS_addR_", "m_fuF_addCtrl18_", "20260819_214330",
     "same trap at L18: control magnitude 1.0 x gap(L18)=14.7925 vs arm 1.0. Overdosed 14.79x."),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rows = []
    for label, ap_, bp_, sess, why in CONTRASTS:
        A, ad = load(ap_)
        B, bd = load(bp_)
        if not A or not B:
            continue
        same_session = all(sess in x for x in ad + bd)
        sa, du_a = specs_of(ap_)
        sb, du_b = specs_of(bp_)
        ma, mb = applied_magnitude(sa), applied_magnitude(sb)
        gate_a = gate_b = None
        # matched only if every add-magnitude on both sides agrees to 1%
        va = sorted(x["magnitude"] for x in ma if x["magnitude"] is not None)
        vb = sorted(x["magnitude"] for x in mb if x["magnitude"] is not None)
        matched_dose = (len(va) == len(vb) and len(va) > 0
                        and all(abs(x - y) <= 0.01 * max(x, y) for x, y in zip(va, vb)))
        ratio = None
        if va and vb:
            ratio = (max(vb) / max(va)) if max(va) else None
        rows.append({
            "contrast": label, "why": why, "session": sess, "same_session": same_session,
            "arm_shards": ad, "ref_shards": bd,
            "arm_asr": sum(v[0] for v in A.values()) / len(A),
            "ref_asr": sum(v[0] for v in B.values()) / len(B),
            # RECORDED BUT NOT TRUSTED: see the docstring. `dose_unit` is a literal emitted on every
            # run regardless of direction, so it claims "gap" even for refusalness arms dosed in
            # their own norm. Kept only so the contradiction is visible next to the reconstruction.
            "dose_unit_arm_UNRELIABLE": du_a, "dose_unit_ref_UNRELIABLE": du_b,
            "arm_add_magnitudes": ma, "ref_add_magnitudes": mb,
            "dose_matched": matched_dose,
            "ref_over_arm_magnitude_ratio": ratio,
            "result": contrast(A, B),
        })

    out = {
        "question": "at equal dose, in the same judging session, does d_surface differ from a "
                    "magnitude-matched random direction?",
        "why_this_was_missing": (
            "every previous late-layer contrast was cross-session (carrying 0.0057 judge drift) or "
            "matched to a random direction at a different depth. These arms were run correctly and "
            "never analysed."),
        "dose_unit_field_is_unreliable": (
            "score_behavior writes `dose_unit` as an unconditional literal on every intervened run, "
            "so it reads 'gap' even on refusalness arms that are dosed in their own unit norm. The "
            "field is reported with an _UNRELIABLE suffix; the dose verdicts below come from "
            "reconstructed magnitudes, not from it. Found by audit #14."),
        "dose_checked_by_RECONSTRUCTED_MAGNITUDE_not_alpha": (
            "score_behavior dozes refusalness in its own unit norm (alpha == magnitude) and every "
            "other direction in d_surface-gap units (magnitude = alpha * gap). gap(L8)=6.0549, "
            "gap(L18)=14.7925. So `refusalness:add:18:1.0` injects 1.0 while `random:add:18:1.0` "
            "injects 14.79 -- identical-looking flags, a 14.79x overdose. Two of the five contrasts "
            "below are mismatched that way and are marked DOSE-MISMATCHED rather than deleted."),
        "only_dose_matched_contrast": (
            "d_surface:add:8:0.25 vs random:add:8:0.25 -- both gap-dosed, both magnitude 1.5137."),
        "relation_to_the_retracted_refusal_ladder": (
            "the withdrawn claim counted refusal with a regex that only ran on short outputs, so it "
            "measured refusal SHORTENING. This is judged ASR against a matched control in the same "
            "session -- a different instrument and a different claim, not a rehabilitation."),
        "rows": rows,
        "provenance": {"argv": sys.argv, "git_commit": git_commit_safe()},
    }
    with open(a.out, "w") as f:
        json.dump(out, f, indent=2)

    for r in rows:
        c = r["result"] or {}
        print(f"\n{r['contrast']}")
        rr = r.get("ref_over_arm_magnitude_ratio")
        print(f"   same_session={r['same_session']}  DOSE_MATCHED={r['dose_matched']}"
              + (f"  (control/arm magnitude = {rr:.2f}x)" if isinstance(rr, float) else ""))
        print(f"   arm ASR {r['arm_asr']:.4f}   ref ASR {r['ref_asr']:.4f}   "
              f"delta {c.get('delta', float('nan')):+.4f}   clustered "
              f"{c.get('delta_domain_clustered', float('nan')):+.4f}")
        print(f"   cluster p {c.get('p_cluster_signflip')}  floor {c.get('min_attainable_cluster_p')}"
              f"  k={c.get('n_informative_clusters')}  at_floor={c.get('p_is_at_floor')}")
    print(f"\n[channel-matched] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
