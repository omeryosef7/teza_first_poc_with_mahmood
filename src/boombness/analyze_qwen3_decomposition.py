"""analyze_qwen3_decomposition.py -- decompose Qwen3's +0.3476 remove-both effect.

WHY. The committed Qwen3 internal-bank design has three cells and is missing the one that
decomposes the effect:

    remove refusalness @ L20 alone .......... -0.0048  (inert)
    remove BOTH (d_surface L11 + refusal L20) +0.3476  (p 0.00028)
    norm-matched double random .............. +0.0143  (inert)
    remove d_surface @ L11 alone ............ NEVER RUN  <-- this script

PRE-REGISTERED before judging (see the log): if arm B is also ~0, then neither leg moves ASR alone
while the pair moves it +0.35 -- a strong INTERACTION rather than a decomposition, and not what the
final report's phrasing implies.

THE INTERACTION IS TESTED DIRECTLY, not inferred from three marginal p-values. Plan section 8 asks
"does removing both exceed the sum of each alone?", which is a contrast, not a comparison of
significance verdicts:

    interaction = (D - base) - (B - base) - (C - base) = D - B - C + base,  paired per prompt

Positive => super-additive (the legs help each other). Zero => additive. This is the same
difference-of-two-significances trap review #4 flagged and review #9 caught the report committing.

ESTIMAND. Paired per prompt, aggregated over the 6 domain clusters (G-1 = 5 df), identical to
consolidate_deliverables.py, whose helpers this script imports verbatim so the numbers stay
comparable to the committed block.

SESSION MATCHING. --tag-prefix selects ONE judging session for all arms. R6-6 established that
comparing arms judged in different sessions produced a real artifact; the default prefix is the
new single-session batch.

SAFETY: judge scalars only; never opens gens.jsonl.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import statistics as st
import subprocess

from consolidate_deliverables import (REPO, judge_rows, paired_delta, asr, newest)
from analyze_g8 import cluster_mean_ci

import glob


def load_shards(prefix: str, tag: str, session: str) -> tuple:
    """Union every judge SHARD for one arm within ONE judging session.

    WHY THIS EXISTS. `consolidate_deliverables.newest()` returns a SINGLE directory, which was
    correct when each arm was judged in one 960-row run. This batch shards each arm into two
    480-row runs, so `newest()` would have returned half the rows and produced a perfectly
    plausible number from 480 prompts instead of 960 -- the same silent-half-run failure review #6
    caught (`abgL6_B` at 40 rows returning delta 0.0).

    `session` pins ONE batch. Two batches were accidentally run over these same generations
    (a SLURM job and a stray foreground invocation); unioning across them would double-count every
    prompt id. Duplicates are therefore a hard error, not a dedup.
    """
    dirs = sorted(glob.glob(os.path.join(REPO, "outputs", "boombness", "judge",
                                         f"{prefix}{tag}_{session}*")))
    if not dirs:
        raise SystemExit(f"[q3dec] no judge shards for {prefix}{tag} in session {session!r}")
    rows, offsets, dupes = {}, [], []
    for d in dirs:
        rp = os.path.join(d, "results.jsonl")
        if not os.path.exists(rp):
            raise SystemExit(f"[q3dec] shard has no results.jsonl: {d}")
        with open(os.path.join(d, "config.json")) as fh:
            offsets.append(json.load(fh).get("args", {}).get("offset"))
        for line in open(rp):
            r = json.loads(line)
            pid = r.get("prompt_id")
            if pid is None:
                continue
            if pid in rows:
                dupes.append(pid)
            if r.get("judge_status") == "ok":
                rows[pid] = r
    if dupes:
        raise SystemExit(f"[q3dec] {len(dupes)} duplicate prompt_id across shards of {tag} -- "
                         f"two judging batches almost certainly overlap; pin --session")
    return rows, [os.path.relpath(d, REPO) for d in dirs], sorted(o for o in offsets if o is not None)

FIELDS = ("malicious_at_0.5", "strongreject_score")


def interaction(base, arm_b, arm_c, arm_d, field: str) -> dict:
    """(D - B - C + base) per prompt, then domain-clustered. Super-additivity of the two legs."""
    pids = sorted(set(base) & set(arm_b) & set(arm_c) & set(arm_d))
    f = (lambda v: (1.0 if v else 0.0)) if field == "malicious_at_0.5" else float
    d = {}
    for p in pids:
        vals = [x[p].get(field) for x in (arm_d, arm_b, arm_c, base)]
        if any(v is None for v in vals):
            continue
        D, Bv, C, S = (f(v) for v in vals)
        d[p] = (D - S) - (Bv - S) - (C - S)
    if not d:
        return {"n": 0, "error": "no shared prompt_id with all four arms"}
    cl = collections.defaultdict(list)
    for p in d:
        cl[str(base[p].get("domain"))].append(d[p])
    r = cluster_mean_ci(dict(cl), n_effective=len(d))
    return {"n": len(d), "interaction_cluster_mean": r.get("mean"), "se": r.get("se"),
            "ci95_domain_clustered": r.get("ci"), "p_cl": r.get("p_vs_0"),
            "n_domains": r.get("n_clusters"),
            "meaning": "(D-base) - (B-base) - (C-base); >0 = removing both exceeds the sum of "
                       "each alone (super-additive), 0 = additive"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag-prefix", default="q3dec_",
                    help="ONE judging session for every arm (R6-6)")
    ap.add_argument("--arms", default="base,C20,D20,D20ctrl,B11,B11ctrl")
    ap.add_argument("--session", required=True,
                    help="judging-session stamp, e.g. 20260821_182849; pins ONE batch")
    ap.add_argument("--expect-rows", type=int, default=0,
                    help="per-arm judged row count; 0 disables the check")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    tags = [t for t in a.arms.split(",") if t]
    runs, rows, offs = {}, {}, {}
    for t in tags:
        rows[t], runs[t], offs[t] = load_shards(a.tag_prefix, t, a.session)

    # GUARD: every arm must carry the same prompt ids, or a "paired" delta is not paired.
    ref = set(rows[tags[0]])
    for t in tags:
        if a.expect_rows and len(rows[t]) != a.expect_rows:
            raise SystemExit(f"[q3dec] {t}: {len(rows[t])} judged rows, expected {a.expect_rows}")
        if set(rows[t]) != ref:
            raise SystemExit(f"[q3dec] {t}: prompt-id set differs from {tags[0]} "
                             f"({len(set(rows[t]) ^ ref)} symmetric-difference ids)")

    by = {}
    for cond in ("natural_doublespeak", "benign_literal"):
        by[cond] = {t: {p: r for p, r in rows[t].items() if r.get("condition") == cond}
                    for t in tags}

    out = {
        "script": "src/boombness/analyze_qwen3_decomposition.py",
        "purpose": "decompose Qwen3's +0.3476 remove-both effect with the never-run d_surface-only "
                   "arm, and test super-additivity directly rather than by comparing p-values",
        "estimand": "paired per prompt vs the same baseline, domain-clustered (G-1 df)",
        "session_matching": f"all arms from judging session {a.tag_prefix!r} (R6-6)",
        "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO,
                                     capture_output=True, text=True).stdout.strip(),
        "runs": runs,
        "shard_offsets": offs,
        "n_judged_rows": {t: len(rows[t]) for t in tags},
        "conditions": {},
    }
    for cond, pools in by.items():
        blk = {"n_rows": len(pools[tags[0]]), "arms": {}}
        for t in tags:
            if t == "base":
                blk["arms"][t] = {"asr": asr(pools[t])}
                continue
            blk["arms"][t] = {
                "asr": asr(pools[t]),
                **{f: paired_delta(pools["base"], pools[t], f) for f in FIELDS},
            }
        if all(k in pools for k in ("base", "B11", "C20", "D20")):
            blk["INTERACTION_super_additivity"] = {
                f: interaction(pools["base"], pools["B11"], pools["C20"], pools["D20"], f)
                for f in FIELDS}
        out["conditions"][cond] = blk

    # ---- doublespeak-specificity: (delta on natural_doublespeak) - (delta on benign_literal),
    # per domain. benign_literal is zero by construction, so ANY movement there is non-specific.
    # Same estimand as consolidate_deliverables' specificity block.
    spec = {}
    for t in tags:
        if t == "base":
            continue
        per = {}
        for cond in ("natural_doublespeak", "benign_literal"):
            bp, ap_ = by[cond]["base"], by[cond][t]
            cl = collections.defaultdict(list)
            for pid in sorted(set(bp) & set(ap_)):
                cl[str(bp[pid].get("domain"))].append(
                    (1.0 if ap_[pid]["malicious_at_0.5"] else 0.0)
                    - (1.0 if bp[pid]["malicious_at_0.5"] else 0.0))
            per[cond] = {d: st.mean(v) for d, v in cl.items()}
        doms = sorted(set(per["natural_doublespeak"]) & set(per["benign_literal"]))
        exc = cluster_mean_ci(
            {d: [per["natural_doublespeak"][d] - per["benign_literal"][d]] for d in doms},
            n_effective=len(doms))
        spec[t] = {"doublespeak_specific_excess": exc.get("mean"), "se": exc.get("se"),
                   "ci95": exc.get("ci"), "p_cl": exc.get("p_vs_0"),
                   "n_domains": exc.get("n_clusters"),
                   "note": "benign_literal is zero by construction; anything it moves is "
                           "NON-specific, so this excess is the doublespeak-attributable part"}
    out["specificity"] = spec

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[q3dec] wrote {a.out}")
    for t, v in out.get("specificity", {}).items():
        e, pv = v.get("doublespeak_specific_excess"), v.get("p_cl")
        if e is not None:
            print(f"  SPECIFIC {t:9s} excess {e:+.4f}  p {'n/a' if pv is None else format(pv,'.4g')}")
    for cond, blk in out["conditions"].items():
        print(f"  == {cond} (n={blk['n_rows']})")
        for t, v in blk["arms"].items():
            m = v.get("malicious_at_0.5") or {}
            dm, pv = m.get("delta_cluster_mean"), m.get("p_cl")
            if dm is None:
                # benign_literal is zero by construction: every delta can be identically 0, which
                # makes the clustered p undefined rather than 1.0. Print it as such instead of
                # crashing -- and note that a None p here is EXPECTED, not a failure.
                print(f"     {t:9s} asr {v['asr']:.4f}  "
                      f"{'(baseline)' if t == 'base' else 'dASR n/a (degenerate)'}")
            else:
                print(f"     {t:9s} asr {v['asr']:.4f}  dASR {dm:+.4f} "
                      f"p {'n/a' if pv is None else format(pv, '.4g')}")
        it = blk.get("INTERACTION_super_additivity", {}).get("malicious_at_0.5")
        if it and it.get("interaction_cluster_mean") is not None:
            ip = it.get("p_cl")
            print(f"     INTERACTION {it['interaction_cluster_mean']:+.4f}  "
                  f"p {'n/a' if ip is None else format(ip, '.4g')}")


if __name__ == "__main__":
    main()
