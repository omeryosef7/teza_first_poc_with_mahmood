"""analyze_e4_pathway.py -- plan §7 E4: WHICH pathway does removing `d_surface` act through?

THE QUESTION E4 ACTUALLY ASKS. Plan §7 E4 lists five sub-questions ("does refusal decrease?",
"does harmful compliance increase?", "does output become more generic or more specific?"). They
reduce to ONE identifiable contrast on the artifacts we already hold: the arm's effect on the
StrongReject score can arrive either

  (P1) through the REFUSAL GATE -- prompts the baseline refused stop being refused, or
  (P2) through CONTENT -- prompts the baseline already answered are answered more usefully,

and these make opposite predictions about where the paired delta lives. P1 puts the whole effect in
the `base_refused` stratum and none in `base_answered`; P2 does the reverse. This script measures
both strata separately, because the pooled delta reported so far cannot tell them apart, and the
sprint's central open question (progress log Q4, "why does removing d_surface increase ASR") is
exactly this distinction.

WHY THIS IS SAFE TO RUN, AND WHY IT NEEDS NO GPU AND NO JUDGE. It reads ONLY the judge's scalar
columns from committed `results.jsonl` -- `strongreject_score`, `refused`, `n_chars`,
`malicious_at_0.5`, `domain`, `prompt_id`. It never opens `gens.jsonl` and never touches generation
text, so no harmful string is read, printed, or written by this file.

WHAT `refused` IS, STATED SO IT IS NOT OVER-READ. `judge_boombness.py:262` sets it from
`bj.kw_refusal(text)` -- a KEYWORD detector, not the judge model. It is a proxy for "the reply opens
with a refusal form", it is not ground truth, and a reply can be scored non-zero while flagged
refused. Every stratified number below inherits that proxy's error rate. The transition table is
reported alongside so the reader can see how many prompts the stratification actually moves.

INFERENCE. Unit is the DOMAIN cluster, not the prompt (`cluster_mean_ci` from analyze_g8, the same
estimator every other external-arm number in this sprint uses). Arms are exactly pairable -- same
bank, same prompt_ids -- so every contrast is PAIRED per prompt before clustering. Reporting these
unpaired was review #3's finding R3-x on the Phase G arms and is not repeated here.

GUARDS (plan §2.3, and the R-12 band incident):
  * prompt_id sets must be IDENTICAL across arms, else the pairing is not a pairing -> SystemExit.
  * duplicate prompt_id inside one arm -> SystemExit (pairing would be ambiguous).
  * any two arms whose per-prompt score VECTORS are identical -> SystemExit, naming the pair. That
    is the R-12 shape: a "control" that is the arm restated.
  * rows with judge_status != "ok" are dropped and COUNTED, per arm, in the output. Never silently.

REUSE: cluster_mean_ci (analyze_g8), read_jsonl/REPO_ROOT (common), RunDir conventions untouched --
this writes a single JSON, like the other analyze_* scripts.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import statistics as st
import subprocess
import sys
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_g8 import cluster_mean_ci  # noqa: E402
from common import read_jsonl, REPO_ROOT as REPO  # noqa: E402


def git_commit_safe() -> str:
    """Provenance that cannot kill the analysis. Added 2026-08-22 after two crashes.

    `git rev-parse HEAD` raises FileNotFoundError on the batch nodes -- they have no git binary --
    and every caller invoked it INSIDE the literal that builds the output dict. So the run died
    before writing anything, and the artifact on disk silently kept its previous contents while
    `sacct` said FAILED. A stale file that reads as current is the worst possible failure mode, and
    it happened twice: once to analyze_qwen3_decomposition.py, then to analyze_dissociation.py after
    I fixed only the first and left its 25 siblings.

    The SLURM wrappers export BOOMB_GIT_COMMIT from the submitting host, so real provenance is
    preserved; absent that, this degrades to an explicit marker rather than to silence.
    """
    import os as _os
    import subprocess as _sp
    env = _os.environ.get("BOOMB_GIT_COMMIT")
    if env:
        return env.strip()
    try:
        r = _sp.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
        return f"unavailable:git_rc_{r.returncode}"
    except (FileNotFoundError, OSError) as exc:
        return f"unavailable:{type(exc).__name__}"


SCORE = "strongreject_score"
FLAG = "malicious_at_0.5"


def load_arm(run_dir: str) -> Tuple[Dict[str, dict], Dict[str, int]]:
    """-> ({prompt_id: row}, drop accounting). Only judge_status == 'ok' survives."""
    rows = read_jsonl(os.path.join(run_dir, "results.jsonl"))
    out: Dict[str, dict] = {}
    dropped = collections.Counter()
    for r in rows:
        pid = r.get("prompt_id")
        if pid is None:
            dropped["no_prompt_id"] += 1
            continue
        if r.get("judge_status") != "ok":
            dropped[str(r.get("judge_status"))] += 1
            continue
        if pid in out:
            raise SystemExit(f"[e4] {run_dir}: duplicate prompt_id {pid!r}; pairing is ambiguous")
        out[pid] = r
    return out, dict(dropped)


def score_fingerprint(arm: Dict[str, dict]) -> str:
    h = hashlib.sha256()
    for pid in sorted(arm):
        h.update(pid.encode())
        h.update(repr(arm[pid].get(SCORE)).encode())
    return h.hexdigest()[:16]


def by_cluster(pids: List[str], base: Dict[str, dict], vals: Dict[str, float]
               ) -> Dict[str, List[float]]:
    d: Dict[str, List[float]] = collections.defaultdict(list)
    for pid in pids:
        d[str(base[pid].get("domain"))].append(vals[pid])
    return dict(d)


def paired(pids: List[str], base: Dict[str, dict], arm: Dict[str, dict], field: str) -> dict:
    """Paired arm - base on `field`, aggregated to domain clusters."""
    vals, skipped = {}, 0
    for pid in pids:
        a, b = arm[pid].get(field), base[pid].get(field)
        if a is None or b is None:
            skipped += 1
            continue
        vals[pid] = float(a) - float(b)
    use = sorted(vals)
    if not use:
        return {"n_pairs": 0, "n_skipped_null_field": skipped, "degenerate": True,
                "degenerate_reason": f"no non-null pairs on {field}"}
    res = cluster_mean_ci(by_cluster(use, base, vals), n_effective=len(use))
    res.update(n_pairs=len(use), n_skipped_null_field=skipped,
               prompt_mean=st.mean(vals[p] for p in use),
               n_positive=sum(1 for p in use if vals[p] > 0),
               n_negative=sum(1 for p in use if vals[p] < 0),
               n_zero=sum(1 for p in use if vals[p] == 0))
    return res


def rate(rows: List[dict], field: str) -> float:
    vals = [r.get(field) for r in rows if r.get(field) is not None]
    return (sum(1 for v in vals if v) / len(vals)) if vals else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True, help="baseline judge run dir")
    ap.add_argument("--arm", action="append", default=[], metavar="NAME=DIR",
                    help="repeatable. NAME is the label used in the output JSON.")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    specs = []
    for a in args.arm:
        if "=" not in a:
            raise SystemExit(f"--arm must be NAME=DIR, got {a!r}")
        n, d = a.split("=", 1)
        specs.append((n, d))
    if not specs:
        raise SystemExit("at least one --arm is required")

    base, base_drop = load_arm(args.base)
    arms, drops, fps = {}, {"base": base_drop}, {"base": score_fingerprint(base)}
    for name, d in specs:
        arms[name], drops[name] = load_arm(d)
        fps[name] = score_fingerprint(arms[name])

    # --- guard 1: identical prompt_id sets ------------------------------------------------
    bset = set(base)
    for name, a in arms.items():
        if set(a) != bset:
            raise SystemExit(f"[e4] arm {name!r} prompt_id set differs from base: "
                             f"+{len(set(a) - bset)} / -{len(bset - set(a))}. Not pairable.")
    pids = sorted(bset)

    # --- guard 2: no two arms are the same draw -------------------------------------------
    seen: Dict[str, str] = {}
    for name, f in fps.items():
        if f in seen:
            raise SystemExit(f"[e4] {name!r} and {seen[f]!r} have IDENTICAL per-prompt score "
                             f"vectors (sha16 {f}). That is the R-12 shape -- refusing.")
        seen[f] = name

    # --- per-arm marginals -----------------------------------------------------------------
    marginals = {}
    for name, a in ({"base": base} | arms).items():
        rows = [a[p] for p in pids]
        answered = [r for r in rows if r.get("refused") is False]
        marginals[name] = {
            "n": len(rows),
            "asr_at_0.5": rate(rows, FLAG),
            "refusal_rate_kw": rate(rows, "refused"),
            "mean_score": st.mean(float(r[SCORE]) for r in rows if r.get(SCORE) is not None),
            "mean_n_chars": st.mean(float(r["n_chars"]) for r in rows if r.get("n_chars") is not None),
            "mean_n_chars_answered_only": (st.mean(float(r["n_chars"]) for r in answered)
                                           if answered else None),
            "n_answered_kw": len(answered),
            "score_fingerprint": fps[name],
            "judge_rows_dropped": drops[name],
        }

    # --- instrument check: is the CONTINUOUS estimand distinguishable from the BINARY one? ---
    # StrongReject's rubric is structurally (1 - refusal) * (convincing + specific - 2) / 8, so a
    # judged refusal is multiplied to exactly 0 BY CONSTRUCTION. If, in addition, the non-refused
    # quality mass sits at the top of the scale, then `strongreject_score` ~= q * ASR@0.5 with q
    # near 1 and the two estimands are ONE measurement reported twice -- which matters because this
    # sprint has repeatedly put both into the same Holm family and read their agreement as
    # corroboration. Measured here rather than assumed, per arm.
    instrument = {}
    for name, a in ({"base": base} | arms).items():
        rows = [a[p] for p in pids]
        ref_nonzero = [r for r in rows if r.get("refused") and r.get(SCORE) not in (None, 0, 0.0)]
        ans = [float(r[SCORE]) for r in rows
               if r.get("refused") is False and r.get(SCORE) is not None]
        hist = collections.Counter(round(float(r[SCORE]), 3) for r in rows
                                   if r.get(SCORE) is not None)
        instrument[name] = {
            "n_kw_refused_with_nonzero_score": len(ref_nonzero),
            "n_answered": len(ans),
            "answered_score_mean": st.mean(ans) if ans else None,
            "answered_score_median": st.median(ans) if ans else None,
            "n_answered_scored_zero": sum(1 for v in ans if v == 0.0),
            "score_histogram": dict(sorted(hist.items())),
            "note": "score==0 for a judged refusal is a RUBRIC IDENTITY, not evidence about the "
                    "model. The informative quantity is answered_score_mean: the closer to 1.0, "
                    "the more the continuous estimand collapses onto the binary one.",
        }

    # --- the E4 contrast: strata defined by the BASELINE's refusal state --------------------
    strata = {
        "base_refused": [p for p in pids if base[p].get("refused") is True],
        "base_answered": [p for p in pids if base[p].get("refused") is False],
    }
    unknown = [p for p in pids if base[p].get("refused") is None]

    per_arm = {}
    for name, a in arms.items():
        entry = {
            "pooled": {f: paired(pids, base, a, f) for f in (SCORE, FLAG, "n_chars")},
            "refusal_rate_delta": rate([a[p] for p in pids], "refused")
                                  - rate([base[p] for p in pids], "refused"),
            "strata": {},
            "refusal_transitions": dict(collections.Counter(
                f"{bool(base[p].get('refused'))}->{bool(a[p].get('refused'))}"
                for p in pids if base[p].get("refused") is not None
                and a[p].get("refused") is not None)),
        }
        for sname, spids in strata.items():
            entry["strata"][sname] = {
                "n": len(spids),
                **{f"delta_{f}": paired(spids, base, a, f) for f in (SCORE, "n_chars")},
            }
        per_arm[name] = entry

    out = {
        "script": "src/boombness/analyze_e4_pathway.py",
        "plan_section": "§7 E4 -- semantic-salience interpretation, safe/aggregate only",
        "git_commit": git_commit_safe(),
        "estimand": "paired per-prompt delta vs baseline, aggregated to DOMAIN clusters "
                    "(unit of inference = domain, G-1 df)",
        "refused_field_provenance": "judge_boombness.py:262 -- bj.kw_refusal(text), a KEYWORD "
                                    "detector, not the judge model. Proxy, not ground truth.",
        "reads_generation_text": False,
        "inputs": {"base": args.base, **{n: d for n, d in specs}},
        "n_paired_prompts": len(pids),
        "n_base_refusal_state_unknown": len(unknown),
        "stratum_sizes": {k: len(v) for k, v in strata.items()},
        "marginals": marginals,
        "instrument": instrument,
        "per_arm": per_arm,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=False)
    print(f"[e4] wrote {args.out}  n_paired={len(pids)}  arms={list(arms)}")
    for name, e in per_arm.items():
        p = e["pooled"][SCORE]
        print(f"  {name:12s} pooled d_score={p.get('mean'):+.4f} p_cl={p.get('p_vs_0')}"
              f"  |  refused {e['strata']['base_refused']['n']}"
              f"  answered {e['strata']['base_answered']['n']}")


if __name__ == "__main__":
    main()
