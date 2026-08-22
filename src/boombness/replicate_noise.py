"""replicate_noise.py — how much do two runs of the SAME configuration differ, end to end?

WHY THIS MATTERS MORE THAN THE JUDGE DRIFT I HAVE BEEN QUOTING.

Every margin in this report has been calibrated against `judge_session_drift` -- the spread from
re-judging byte-identical generations, which after audit #14 is **1 prompt in 495**. But an arm and a
control are not the same generations judged twice. They are two separate end-to-end runs: generate,
then judge. The relevant noise for "arm exceeds control" is therefore run-to-run variability of the
WHOLE pipeline, and judge drift is only its last and smallest component.

That number had never been measured, and the data for it was already on disk. `in_subspace_orth:
project_out:12-12:1.0` was run twice -- same spec, same seed (20260901), same `fit_dir` -- and the two
runs differ by **7 prompts**. At L8 the same-spec pair differs by 3. Against margins of 4 (L6), 12
(L8), 13 (L12) and 16 (L10) prompts, a replicate noise of that size is not a footnote.

WHAT COUNTS AS A REPLICATE PAIR. Same model, same bank, same declared `--intervene` spec, same seed,
same `fit_dir` -- differing only in when the job ran. Anything varying in a field that could change the
result is not a replicate and is excluded, with the differing field named.

HOW IT IS SCORED. On the INTERSECTION of prompt ids, for the same reason the drift script now does:
a denominator difference must never be able to masquerade as noise.

WHAT THIS CANNOT SAY. It measures the spread of *pairs*, not a variance with a known distribution; with
a handful of pairs the maximum is an unstable statistic and is reported alongside the median rather
than instead of it. It also cannot separate generation nondeterminism (GPU kernels, batching) from
sampling, since both runs used the same seed.

Numeric/categorical fields only.
"""
from __future__ import annotations

import argparse
import glob
import itertools
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from unanalysed_inventory import git_commit_safe  # noqa: E402

N = 495
KEY_FIELDS = ("intervene", "bank", "seed", "fit_dir", "max_new", "query_kinds", "enable_thinking")


def judge_rows(d):
    out = {}
    f = os.path.join(d, "results.jsonl")
    if not os.path.exists(f):
        return out
    for line in open(f, encoding="utf-8"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        pid, v = r.get("prompt_id"), r.get("malicious_at_0.5")
        if pid is not None and v is not None:
            out[pid] = 1 if v else 0
    return out


def gens_of(d):
    try:
        a = json.load(open(os.path.join(d, "config.json")))
        a = a.get("args", a)
        g = str(a.get("gens") or "").rstrip("/")
        return os.path.dirname(g) if g.endswith("gens.jsonl") else g
    except Exception:
        return None


def gcfg(g):
    try:
        c = json.load(open(os.path.join(g, "config.json")))
        return c.get("args", c) or {}
    except Exception:
        return {}


def model_of(g):
    try:
        return os.path.basename(str(json.load(open(os.path.join(g, "metadata.json"))).get("model") or ""))
    except Exception:
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-rows", type=int, default=400)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    # one judged result per GENERATION run (union its judge shards); require DONE on both stages
    per_gens = {}
    meta = {}
    for d in sorted(glob.glob("outputs/boombness/judge/*")):
        if not os.path.isdir(d) or not os.path.exists(os.path.join(d, "DONE.json")):
            continue
        g = gens_of(d)
        if not g or not os.path.isdir(g) or not os.path.exists(os.path.join(g, "DONE.json")):
            continue
        rows = judge_rows(d)
        if not rows:
            continue
        # SHARDS, NOT RE-JUDGINGS -- the C-11 class, and this script had it too (third occurrence in
        # this repo). The first version kept only the FIRST judge dir per generation run, on the
        # reasoning that a second judging would inject judge drift into a replicate estimate. But
        # `vL12J0` + `vL12J1` are DISJOINT halves (248 + 247) of one judged run, not two judgings, so
        # keeping one left 248 rows, which then fell under --min-rows and the run vanished silently.
        # That dropped exactly the in_subspace_orth pairs that motivated writing this script.
        #
        # Correct rule: union judge dirs whose prompt ids are DISJOINT (shards); only an OVERLAP means
        # the same prompts were judged twice, and there the first judging wins.
        prev = per_gens.get(g)
        if prev:
            if set(prev) & set(rows):
                continue                      # genuine re-judging: keep the first
            prev.update(rows)                 # disjoint shard: union it
        else:
            per_gens[g] = rows
        c = gcfg(g)
        meta[g] = {k: c.get(k) for k in KEY_FIELDS}
        meta[g]["model"] = model_of(g)
        meta[g]["judge"] = os.path.basename(d)

    groups = defaultdict(list)
    for g, rows in per_gens.items():
        if len(rows) < a.min_rows:
            continue
        m = meta[g]
        if not m.get("intervene"):
            key = ("BASELINE", m["model"], os.path.basename(str(m.get("bank"))), m.get("seed"))
        else:
            key = (m["intervene"], m["model"], os.path.basename(str(m.get("bank"))), m.get("seed"),
                   str(m.get("fit_dir")))
        groups[key].append(g)

    pairs = []
    for key, gs in sorted(groups.items()):
        if len(gs) < 2:
            continue
        for x, y in itertools.combinations(sorted(gs), 2):
            rx, ry = per_gens[x], per_gens[y]
            common = set(rx) & set(ry)
            if len(common) < a.min_rows:
                continue
            ax = sum(rx[i] for i in common) / len(common)
            ay = sum(ry[i] for i in common) / len(common)
            diff_fields = {k: (meta[x].get(k), meta[y].get(k))
                           for k in KEY_FIELDS + ("model",)
                           if meta[x].get(k) != meta[y].get(k)}
            pairs.append({
                "spec": key[0], "model": key[1], "bank": key[2], "seed": key[3],
                "run_a": os.path.basename(x), "run_b": os.path.basename(y),
                "n_common": len(common), "asr_a": ax, "asr_b": ay,
                "abs_diff": abs(ax - ay), "abs_diff_prompts": abs(ax - ay) * len(common),
                "config_fields_that_differ": diff_fields or None,
            })

    clean = [p for p in pairs if not p["config_fields_that_differ"]]
    dif = sorted(p["abs_diff_prompts"] for p in clean)
    med = (dif[len(dif) // 2] if len(dif) % 2 else
           (dif[len(dif) // 2 - 1] + dif[len(dif) // 2]) / 2) if dif else None

    out = {
        "question": "how much do two runs of the SAME configuration differ end to end?",
        "why": "margins have been calibrated against judge drift (1 prompt), but an arm and a control "
               "are two separate generate-then-judge runs. Run-to-run variability of the whole "
               "pipeline is the relevant scale; judge drift is only its last component.",
        "replicate_definition": list(KEY_FIELDS) + ["model"],
        "scored_on": "intersection of prompt ids",
        "n_replicate_pairs": len(clean),
        "median_abs_diff_prompts": med,
        "max_abs_diff_prompts": (dif[-1] if dif else None),
        "all_diffs_prompts": dif,
        "caveat": "the spread of a handful of pairs, not a variance with a known distribution. The "
                  "maximum is unstable at this n and is reported next to the median, not instead of "
                  "it. Cannot separate GPU/batching nondeterminism from sampling: both runs share a "
                  "seed.",
        "pairs": sorted(clean, key=lambda p: -p["abs_diff_prompts"]),
        "excluded_not_true_replicates": [p for p in pairs if p["config_fields_that_differ"]],
        "provenance": {"argv": sys.argv, "git_commit": git_commit_safe()},
    }
    with open(a.out, "w") as f:
        json.dump(out, f, indent=2)

    print(f"replicate pairs (identical config): {len(clean)}")
    if dif:
        print(f"  abs diff in prompts: median {med}, max {dif[-1]}, all {dif}")
    print(f"\n{'spec':<46}{'seed':>10}{'n':>6}{'|diff|p':>9}")
    for p in out["pairs"][:12]:
        print(f"{str(p['spec'])[:46]:<46}{str(p['seed']):>10}{p['n_common']:>6}"
              f"{p['abs_diff_prompts']:>9.0f}")
    print(f"\n[replicate-noise] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
