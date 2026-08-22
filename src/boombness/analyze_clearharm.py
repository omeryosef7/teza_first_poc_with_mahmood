"""analyze_clearharm.py — the two §14 ClearHarm numbers that had no script behind them.

WHY THIS FILE EXISTS. The 2026-08-20 audit found that two numbers this session put in the log and
the report are **in no committed artifact**:

  * the super-additivity excess of arm D over arms B + C (+0.0922, CI [−0.1474, +0.1332]);
  * cos(d_surface, refusalness) = 0.019 at L18, the evidence that arm B is not arm C by proxy.

Both were computed in ad-hoc shell heredocs and never written anywhere. That is precisely the
"no script regenerates this" provenance failure this project retracted a role-statistics claim for,
and the standing rule is that a number without a committed script AND a committed artifact does not
go in the report. This script closes it for both.

Run:
  PY src/boombness/analyze_clearharm.py --judge-dir outputs/boombness/judge \\
     --fit-dir outputs/boombness/extract_boombness/full_20260816_185942_1008673 \\
     --out outputs/boombness/clearharm_supplement.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import subprocess
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_jsonl  # noqa: E402


def git_commit_safe() -> str:
    """Provenance that cannot kill the analysis. Added 2026-08-22 after two crashes.

    `git rev-parse HEAD` raises FileNotFoundError on the batch nodes -- they have no git binary --
    and callers invoke it INSIDE the literal that builds the output dict, so the run dies before
    writing anything and the artifact on disk silently keeps its previous contents while `sacct`
    says FAILED. A stale file that reads as current is the worst failure mode available, and it
    happened twice: to analyze_qwen3_decomposition.py, then to analyze_dissociation.py after only
    the first was fixed and its siblings left alone.

    The SLURM wrappers export BOOMB_GIT_COMMIT from the submitting host, so real provenance is
    preserved; absent that this degrades to an explicit marker rather than to silence.
    """
    import os as _os
    import subprocess as _sp
    env = _os.environ.get("BOOMB_GIT_COMMIT")
    if env:
        return env.strip()
    try:
        _kw = {"capture_output": True, "text": True}
        _repo = globals().get("REPO")
        if _repo:
            _kw["cwd"] = _repo
        r = _sp.run(["git", "rev-parse", "HEAD"], **_kw)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
        return f"unavailable:git_rc_{r.returncode}"
    except (FileNotFoundError, OSError) as exc:
        return f"unavailable:{type(exc).__name__}"


def git_dirty_safe(*args) -> object:
    """Companion for the `git status --porcelain` dirty-flag calls. Never raises."""
    import subprocess as _sp
    try:
        _kw = {"capture_output": True, "text": True}
        _repo = globals().get("REPO")
        if _repo:
            _kw["cwd"] = _repo
        return bool(_sp.run(["git", "status", "--porcelain", *args], **_kw).stdout.strip())
    except (FileNotFoundError, OSError):
        return None



def _load(judge_dir: str, pat: str, condition: str) -> Dict[str, Dict]:
    hits = sorted(glob.glob(os.path.join(judge_dir, pat)))
    if not hits:
        raise SystemExit(f"[clearharm] no judge run matching {pat!r} under {judge_dir}")
    d = hits[-1]
    return d, {r["prompt_id"]: r for r in read_jsonl(os.path.join(d, "results.jsonl"))
               if r.get("condition") == condition and r.get("strongreject_score") is not None}


def super_additivity(base, B, C, D, seed: int, n_boot: int) -> Dict:
    """(D − base) − [(B − base) + (C − base)], bootstrapped over DOMAINS, not prompts.

    The cluster is the domain because prompts within a ClearHarm category are not independent
    draws; resampling prompts would understate the interval, which is the defect this project
    already corrected once for the family-level bootstrap.
    """
    ids = sorted(set(base) & set(B) & set(C) & set(D))
    s = lambda m, i: m[i]["strongreject_score"]
    exc = [(s(D, i) - s(base, i)) - ((s(B, i) - s(base, i)) + (s(C, i) - s(base, i))) for i in ids]
    by: Dict[str, List[float]] = {}
    for i, e in zip(ids, exc):
        by.setdefault(base[i].get("domain"), []).append(e)
    doms = sorted(by)
    rng = random.Random(seed)
    boot = []
    for _ in range(n_boot):
        flat = [v for _ in doms for v in by[rng.choice(doms)]]
        boot.append(sum(flat) / len(flat))
    boot.sort()
    m = sum(exc) / len(exc)
    return {"n": len(ids), "n_clusters": len(doms), "mean_excess": m,
            "ci95_domain_clustered": [boot[int(0.025 * len(boot))], boot[int(0.975 * len(boot))]],
            "frac_boot_le_zero": sum(1 for b in boot if b <= 0) / len(boot),
            "sum_of_singles": sum((s(B, i) + s(C, i) - 2 * s(base, i)) for i in ids) / len(ids),
            "joint": sum((s(D, i) - s(base, i)) for i in ids) / len(ids),
            "n_boot": n_boot, "seed": seed,
            "note": "established only if the CI excludes 0; it does not"}


def direction_cosines(fit_dir: str, model_id: str) -> Dict:
    """cos(d_surface_L, refusal_L) at every layer where BOTH are fitted.

    The caveat is part of the number: arm B acts at L8, where the house refusal set has no
    direction, so the cosine is reported only where both exist and cannot speak for L8 directly.
    """
    import torch
    import refusalness as rf
    p = os.path.join(fit_dir, "directions_fit_dev.pt")
    if not os.path.exists(p):
        p = os.path.join(fit_dir, "directions_fit_heldout.pt")
    pay = torch.load(p, map_location="cpu", weights_only=False)
    ds = pay["d_surface"]
    dim = int(next(iter(ds.values())).numel())
    # ASK ONLY FOR LAYERS THAT EXIST. `load_refusal_dirs` refuses a partial set by design -- "a layer
    # profile must not silently run on a subset of the layers it was asked for" -- so requesting all
    # 32 d_surface layers is a request it is right to reject. Discover the available set first, then
    # intersect; the caveat below records that L8 is not among them.
    import re as _re
    avail = sorted({int(m.group(1)) for f in glob.glob(rf.refusal_glob_for(model_id))
                    for m in [_re.search(r"_L(\d+)", os.path.basename(f))] if m})
    want = sorted(set(ds) & set(avail))
    if not want:
        raise SystemExit(f"[clearharm] no layer has BOTH a d_surface and a refusal direction "
                         f"(d_surface {sorted(ds)[:6]}..., refusal {avail})")
    rd = rf.load_refusal_dirs(want, model_id, expect_dim=dim)
    out = {}
    for L in sorted(set(ds) & set(rd)):
        a, b = ds[L].float(), rd[L].float()
        out[str(L)] = float(torch.dot(a, b) / (a.norm() * b.norm()))
    return {"fit_dir": os.path.abspath(fit_dir), "direction_file": os.path.abspath(p),
            "model": model_id, "d_model": dim,
            "cos_by_layer": out,
            "layers_with_refusal_direction": sorted(int(k) for k in out),
            "refusal_layers_available": avail,
            "caveat": "arm B projects at L8, where no house refusal direction exists; the cosine "
                      "is measured only at layers where BOTH are fitted and does not speak for L8."}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--judge-dir", default="outputs/boombness/judge")
    ap.add_argument("--fit-dir", required=True)
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--condition", default="clearharm_direct")
    ap.add_argument("--seed", type=int, default=20260818)
    ap.add_argument("--n-boot", type=int, default=10000)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    runs = {}
    data = {}
    for key, pat in (("base", "ch_base_*"), ("B", "ch_B_*"), ("C", "ch_C_*"), ("D", "ch_D_*")):
        runs[key], data[key] = _load(args.judge_dir, pat, args.condition)

    res = {
        "plan_section": "14",
        "condition": args.condition,
        "judge_runs": {k: os.path.abspath(v) for k, v in runs.items()},
        "arms": {"B": "d_surface:project_out:8-8", "C": "refusalness:project_out:18-18",
                 "D": "both"},
        "super_additivity": super_additivity(data["base"], data["B"], data["C"], data["D"],
                                             args.seed, args.n_boot),
        "provenance": {
            "argv": sys.argv,
            "git_commit": git_commit_safe(),
            "python": sys.executable,
        },
    }
    try:
        res["direction_cosines"] = direction_cosines(args.fit_dir, args.model)
    except Exception as e:                                     # torch/refusal dirs unavailable
        res["direction_cosines"] = {"error": f"{type(e).__name__}: {e}"}

    with open(args.out, "w") as f:
        json.dump(res, f, indent=2)
    sa = res["super_additivity"]
    print(f"[clearharm] super-additivity {sa['mean_excess']:+.4f} "
          f"CI [{sa['ci95_domain_clustered'][0]:+.4f}, {sa['ci95_domain_clustered'][1]:+.4f}] "
          f"n={sa['n']} G={sa['n_clusters']}  (established: "
          f"{'NO' if sa['ci95_domain_clustered'][0] <= 0 <= sa['ci95_domain_clustered'][1] else 'yes'})")
    dc = res["direction_cosines"]
    if "cos_by_layer" in dc:
        print("[clearharm] cos(d_surface, refusalness): " +
              "  ".join(f"L{k}={v:+.4f}" for k, v in sorted(dc["cos_by_layer"].items(),
                                                            key=lambda kv: int(kv[0]))))
    print(f"[clearharm] -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
