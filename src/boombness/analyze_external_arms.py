"""analyze_external_arms.py — the external-set (plan §14) arm decomposition, regenerably.

WHY THIS EXISTS. `outputs/boombness/clearharm_decomposition.json` shipped with **no provenance block
and no script that produces it** — it was assembled ad hoc. That is the exact failure the sprint's
standing bar forbids: every number in the report must be regenerable by a committed script from a
committed artifact. This script is that missing producer, and it is also the harvest path for the
R-14 re-judge and for the AdvBench super-additivity test.

WHAT IT COMPUTES
  * per-arm ASR@0.5 with a DOMAIN-CLUSTERED interval beside the iid Wilson one (the iid interval
    understates width by ~1.9x on this design; both are reported, named so they cannot be confused)
  * paired per-prompt deltas against the baseline, aggregated to domain cluster means
  * the decomposition: does removing each component alone reproduce the joint arm?
  * SUPER-ADDITIVITY: joint - (B + C), with a domain-clustered bootstrap. This is the quantity
    ClearHarm cannot resolve (127 of 179 rows in one cluster) and AdvBench can (largest 25.7%).
  * a control BAND from >=3 draws -- and it REFUSES a band whose draws are not distinct.

THE BAND GUARD IS THE POINT (R-12, and retraction #7 before it). Twice this project published a
control band that was one draw stated three times, because a seed was threaded into the single-spec
path and dropped on the composed/recursive path. A band is the one artifact whose entire purpose is
to measure draw-to-draw variance, so a fake one looks *better* than a real one and cannot be caught
by reading its value. This script therefore checks the DRAWS, not the summary: identical per-prompt
score vectors are refused, with the offending pair named. Tested in tests/test_external_arms.py.

REUSE: cluster_mean_ci from analyze_g8 (scipy-backed since T4); read_jsonl from common.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import random
import statistics as st
import subprocess
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_g8 import cluster_mean_ci  # noqa: E402
from common import read_jsonl, REPO_ROOT as REPO  # noqa: E402


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


SCORE = "strongreject_score"
FLAG = "malicious_at_0.5"


def load(run_dir: str) -> Dict[str, dict]:
    rows = read_jsonl(os.path.join(run_dir, "results.jsonl"))
    out: Dict[str, dict] = {}
    dupes = []
    for r in rows:
        pid = r.get("prompt_id")
        if pid is None:
            continue
        if pid in out:
            dupes.append(pid)
        out[pid] = r
    if dupes:
        raise SystemExit(f"[ext] {run_dir}: {len(dupes)} duplicate prompt_id; pairing is ambiguous")
    return out


def draw_fingerprint(rows: Dict[str, dict]) -> str:
    """sha16 over (prompt_id, score) in id order.

    WEAK BY ITSELF -- see `source_gens_fingerprint`. Kept as a secondary signal only.
    """
    h = hashlib.sha256()
    for pid in sorted(rows):
        h.update(pid.encode())
        h.update(repr(rows[pid].get(SCORE)).encode())
    return h.hexdigest()[:16]


def source_gens_fingerprint(judge_dir: str) -> Optional[str]:
    """sha16 of the GENERATIONS the judge scored, resolved through the judge run's own config.

    THIS IS THE CHECK THAT MATTERS, and the first version of this file got it wrong. R-12's control
    band had **byte-identical generations** across all three draws, and a fingerprint over judge
    SCORES did not catch it: StrongReject (gpt-4o-mini) is not bitwise deterministic even at
    temperature 0, so re-judging one identical generation set three times yields three slightly
    different score vectors. A score-level fingerprint therefore reports three "distinct" draws for
    a band that has exactly one, which is precisely the dead-guard failure this project has shipped
    six times: a guard whose condition can never be true.

    A control band measures **generation** variance under a re-seeded control direction, so the
    generations are the artifact to fingerprint. Addressed by identity -- the judge run records the
    gens dir it consumed -- not by a filename convention.

    Returns None if the source cannot be resolved; the caller must then say so rather than silently
    falling back to the weak check.
    """
    cfg = os.path.join(judge_dir, "config.json")
    if not os.path.exists(cfg):
        return None
    try:
        with open(cfg) as f:
            gens = json.load(f).get("args", {}).get("gens")
    except Exception:
        return None
    if not gens:
        return None
    path = gens if os.path.isabs(gens) else os.path.join(REPO, gens)
    path = os.path.join(path, "gens.jsonl")
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def arm_stats(rows: Dict[str, dict], common: List[str]) -> dict:
    flags = [1.0 if rows[p].get(FLAG) else 0.0 for p in common]
    doms = collections.defaultdict(list)
    for p in common:
        doms[rows[p].get("domain")].append(1.0 if rows[p].get(FLAG) else 0.0)
    cl = cluster_mean_ci({k: v for k, v in doms.items() if v})
    ref = [1.0 if rows[p].get("refused") else 0.0 for p in common]
    return {
        "n": len(common),
        "asr_at_0.5": st.mean(flags) if flags else float("nan"),
        "mean_score": st.mean([float(rows[p].get(SCORE) or 0.0) for p in common]),
        "refusal": st.mean(ref) if ref else float("nan"),
        "n_domains": cl["n_clusters"],
        "asr_ci95_domain_clustered": cl["ci"],
        "asr_cluster_mean": cl["mean"],
        "degenerate": cl.get("degenerate", False),
    }


def paired_delta(arm: Dict[str, dict], base: Dict[str, dict], common: List[str]) -> dict:
    """Paired per-prompt delta, reported BOTH ways because on an imbalanced set they differ a lot.

    `delta_pooled` weights every PROMPT equally; `delta_cluster_mean` weights every DOMAIN equally
    and is the estimand the clustered interval belongs to. On ClearHarm — 127 of 179 rows in one
    category — these come apart badly (e.g. arm C: pooled +0.240 vs cluster-mean +0.394), because
    the five small domains carry as much weight as the large one. Reporting only the cluster mean
    invites a reader to compare it against a pooled ASR difference and conclude the numbers do not
    add up; reporting only the pooled one hides that the inference is clustered. Both, named.
    """
    diffs = {p: float(arm[p].get(SCORE) or 0.0) - float(base[p].get(SCORE) or 0.0) for p in common}
    byd = collections.defaultdict(list)
    for p in common:
        byd[arm[p].get("domain")].append(diffs[p])
    cl = cluster_mean_ci({k: v for k, v in byd.items() if v})
    return {"delta_pooled": st.mean(list(diffs.values())) if diffs else float("nan"),
            "delta_cluster_mean": cl["mean"],
            "se": cl["se"], "ci95_domain_clustered": cl["ci"],
            "p_cl": cl["p_vs_0"], "n_domains": cl["n_clusters"],
            "estimand_note": ("ci95_domain_clustered and p_cl belong to delta_cluster_mean, NOT to "
                              "delta_pooled. They are different quantities on an imbalanced set."),
            "degenerate": cl.get("degenerate", False)}


def super_additivity(base, armB, armC, armD, common, n_boot=4000, seed=20260819) -> dict:
    """joint effect minus the sum of the single effects, bootstrapped over DOMAINS.

    Resamples domains with replacement (families travel with their domain), recomputing all three
    paired deltas inside each resample so the three arms stay paired on the same prompts.
    """
    doms = collections.defaultdict(list)
    for p in common:
        doms[base[p].get("domain")].append(p)
    keys = sorted(doms)

    def excess(sel_pids):
        def d(arm):
            return st.mean([float(arm[p].get(SCORE) or 0.0) - float(base[p].get(SCORE) or 0.0)
                            for p in sel_pids])
        return d(armD) - (d(armB) + d(armC))

    point = excess(common)
    rng = random.Random(seed)
    draws = []
    for _ in range(n_boot):
        sel = []
        for _ in range(len(keys)):
            sel.extend(doms[keys[rng.randrange(len(keys))]])
        if sel:
            draws.append(excess(sel))
    draws.sort()
    lo = draws[int(0.025 * len(draws))]
    hi = draws[int(0.975 * len(draws)) - 1]
    frac_le0 = sum(1 for x in draws if x <= 0) / len(draws)
    return {"excess": point, "ci95_domain_clustered": [lo, hi],
            "frac_draws_le_0": frac_le0, "n_boot": len(draws), "n_domains": len(keys),
            "established": bool(lo > 0),
            "note": ("joint minus the sum of singles; domains resampled wholesale. "
                     "established=True only if the clustered lower bound clears 0.")}


def paired_excess_difference(base, real, ctrl, common, n_boot=4000, seed=20260819) -> dict:
    """(real super-additivity) minus (control super-additivity), one paired domain bootstrap.

    Both excesses are recomputed inside each resample of domains, so the comparison respects the
    fact that they are measured on the SAME prompts and share the same baseline. Reporting two
    independent intervals and eyeballing whether one excludes zero is not this test.
    """
    doms = collections.defaultdict(list)
    for p in common:
        doms[base[p].get("domain")].append(p)
    keys = sorted(doms)
    rB, rC, rD = real
    cB, cC, cD = ctrl

    def excess(sel, X, Y, Z):
        def d(arm):
            return st.mean([float(arm[p].get(SCORE) or 0.0) - float(base[p].get(SCORE) or 0.0)
                            for p in sel])
        return d(Z) - (d(X) + d(Y))

    def diff(sel):
        return excess(sel, rB, rC, rD) - excess(sel, cB, cC, cD)

    point = diff(common)
    rng = random.Random(seed)
    draws = []
    for _ in range(n_boot):
        sel = []
        for _ in range(len(keys)):
            sel.extend(doms[keys[rng.randrange(len(keys))]])
        if sel:
            draws.append(diff(sel))
    draws.sort()
    lo = draws[int(0.025 * len(draws))]
    hi = draws[int(0.975 * len(draws)) - 1]
    return {"excess_real_minus_control": point, "ci95_domain_clustered": [lo, hi],
            "frac_draws_le_0": sum(1 for x in draws if x <= 0) / len(draws),
            "n_boot": len(draws), "n_domains": len(keys),
            "established_against_control": bool(lo > 0),
            "note": ("paired: both excesses recomputed inside each domain resample. "
                     "established_against_control=True only if the clustered lower bound of the "
                     "DIFFERENCE clears 0 -- not merely if one interval excludes 0 and the other "
                     "does not.")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", required=True, help="judge run dir for the no-intervention arm")
    ap.add_argument("--arm", action="append", default=[], metavar="NAME=DIR",
                    help="repeatable; e.g. --arm B=outputs/.../judge/chg_B_...")
    ap.add_argument("--band", action="append", default=[], metavar="NAME=DIR",
                    help="repeatable control draws; >=3 required to report a band")
    ap.add_argument("--super-additive", default="", metavar="B,C,D",
                    help="three arm NAMEs to test joint-vs-sum, e.g. B,C,D")
    ap.add_argument("--super-additive-control", default="", metavar="Bc,Cc,Dc",
                    help="the matched control triple. Adds the PAIRED difference of the two "
                         "excesses -- the test that actually answers 'is the interaction real', "
                         "as opposed to comparing two independent intervals by eye.")
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=20260819)
    a = ap.parse_args()

    def parse(pairs):
        out = {}
        for s in pairs:
            if "=" not in s:
                raise SystemExit(f"[ext] --arm/--band needs NAME=DIR, got {s!r}")
            k, v = s.split("=", 1)
            out[k] = v
        return out

    arms, bands = parse(a.arm), parse(a.band)
    base = load(a.baseline)
    loaded = {k: load(v) for k, v in arms.items()}
    bloaded = {k: load(v) for k, v in bands.items()}

    common = sorted(set(base).intersection(*[set(v) for v in loaded.values()]) if loaded else set(base))
    dropped = {k: len(set(base) ^ set(v)) for k, v in loaded.items()}

    res = {
        "label": a.label, "n_common": len(common),
        "dropped_symmetric_difference_vs_baseline": dropped,
        "runs": {"baseline": os.path.abspath(a.baseline),
                 **{k: os.path.abspath(v) for k, v in arms.items()},
                 **{f"band:{k}": os.path.abspath(v) for k, v in bands.items()}},
        "arms": {"baseline": arm_stats(base, common)},
        "paired_vs_baseline": {},
    }
    for k, rows in loaded.items():
        res["arms"][k] = arm_stats(rows, common)
        res["paired_vs_baseline"][k] = paired_delta(rows, base, common)

    # ---- control band, with the R-12 guard ------------------------------------------------- #
    if bands:
        score_fps = {k: draw_fingerprint(v) for k, v in bloaded.items()}
        gens_fps = {k: source_gens_fingerprint(bands[k]) for k in bloaded}
        unresolved = sorted(k for k, v in gens_fps.items() if v is None)
        # PRIMARY check: the generations. Secondary: the scores. Never silently fall back.
        primary = {k: v for k, v in gens_fps.items() if v is not None}
        dup = collections.defaultdict(list)
        for k, f in primary.items():
            dup[f].append(k)
        clashes = [sorted(v) for v in dup.values() if len(v) > 1]
        asrs = {k: arm_stats(v, common)["asr_at_0.5"] for k, v in bloaded.items()}
        band = {"n_draws": len(bloaded), "draws": asrs,
                "source_gens_fingerprints": gens_fps, "judge_score_fingerprints": score_fps,
                "gens_unresolved": unresolved,
                "check": ("generations (primary)" if not unresolved
                          else "generations where resolvable; %d draw(s) UNRESOLVED" % len(unresolved))}
        if clashes:
            band.update({
                "REFUSED": True,
                "reason": ("draws are not distinct -- IDENTICAL GENERATIONS: "
                           + "; ".join("=".join(c) for c in clashes)
                           + ". A band cannot be computed from a repeated draw. This is R-12 / "
                             "retraction #7: a seed that never reached the generator. Note the judge "
                             "SCORES differ across these draws (StrongReject is not bitwise "
                             "deterministic), so a score-level check would have passed this."),
                "mean": None, "between_draw_sd": None})
            print(f"[ext] BAND REFUSED: {band['reason']}")
        elif unresolved:
            band.update({
                "REFUSED": True,
                "reason": ("cannot resolve source generations for draw(s) %s, so distinctness is "
                           "unverifiable. Refusing rather than falling back to the score-level "
                           "check, which cannot detect a repeated draw." % ", ".join(unresolved)),
                "mean": None, "between_draw_sd": None})
            print(f"[ext] BAND REFUSED: {band['reason']}")
        elif len(bloaded) < 3:
            band.update({"REFUSED": True,
                         "reason": f"{len(bloaded)} draw(s); a band needs >=3",
                         "mean": None, "between_draw_sd": None})
            print(f"[ext] BAND REFUSED: {band['reason']}")
        else:
            vals = list(asrs.values())
            band.update({"REFUSED": False, "mean": st.mean(vals),
                         "between_draw_sd": st.stdev(vals),
                         "sem": st.stdev(vals) / (len(vals) ** 0.5)})
        res["control_band"] = band

    if a.super_additive:
        names = [x.strip() for x in a.super_additive.split(",")]
        if len(names) != 3 or any(n not in loaded for n in names):
            raise SystemExit(f"[ext] --super-additive needs three known arm names, got {names}")
        B, C, D = (loaded[n] for n in names)
        res["super_additivity"] = {"arms": names,
                                   **super_additivity(base, B, C, D, common, seed=a.seed)}

        # ---- versus its OWN control triple, PAIRED ------------------------------------------- #
        # Running the real triple and the control triple as two separate bootstraps and comparing
        # "one CI excludes zero, the other does not" is the difference-of-significance fallacy: on
        # this data the real excess is +0.0333 [+0.0128, +0.0638] and the control's is +0.0066
        # [-0.0013, +0.0170], and those intervals OVERLAP. The quantity that answers the question is
        # the DIFFERENCE of the two excesses, bootstrapped ONCE over the same resampled domains so
        # the two are paired and their correlation is respected.
        if a.super_additive_control:
            cnames = [x.strip() for x in a.super_additive_control.split(",")]
            if len(cnames) != 3 or any(n not in loaded for n in cnames):
                raise SystemExit(f"[ext] --super-additive-control needs three known arms, got {cnames}")
            cB, cC, cD = (loaded[n] for n in cnames)
            res["super_additivity_vs_control"] = {
                "arms": names, "control_arms": cnames,
                **paired_excess_difference(base, (B, C, D), (cB, cC, cD), common, seed=a.seed)}

    try:
        git = git_commit_safe()
        dirty = git_dirty_safe()
    except Exception:
        git, dirty = None, None
    res["provenance"] = {"argv": sys.argv, "git_commit": git, "git_dirty": dirty,
                         "python": sys.executable, "seed": a.seed}

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1)

    print(f"[ext] {a.label}  n_common={res['n_common']}")
    print(f"{'arm':<10}{'ASR@0.5':>9}{'refusal':>9}{'Δpooled':>10}{'Δclust':>10}{'p_cl':>9}"
          f"   clustered CI on Δclust")
    for k in ["baseline"] + list(loaded):
        st_ = res["arms"][k]
        d = res["paired_vs_baseline"].get(k)
        ci = (d or {}).get("ci95_domain_clustered")
        sig = "" if not d or d["p_cl"] is None else (
            "  ***" if d["p_cl"] < 0.01 else "  *" if d["p_cl"] < 0.05 else "  n.s.")
        print("%-10s%9.4f%9.4f%10s%10s%9s   %s%s" % (
            k, st_["asr_at_0.5"], st_["refusal"],
            "—" if not d else "%+.4f" % d["delta_pooled"],
            "—" if not d else "%+.4f" % d["delta_cluster_mean"],
            "—" if not d or d["p_cl"] is None else "%.4f" % d["p_cl"],
            "—" if not ci else "[%+.4f, %+.4f]" % (ci[0], ci[1]), sig))
    if "super_additivity_vs_control" in res:
        v = res["super_additivity_vs_control"]
        print("[ext] super-additivity vs CONTROL triple (paired): %+.4f  CI [%+.4f, %+.4f]  "
              "frac<=0 %.3f  -> %s"
              % (v["excess_real_minus_control"], v["ci95_domain_clustered"][0],
                 v["ci95_domain_clustered"][1], v["frac_draws_le_0"],
                 "ESTABLISHED against control" if v["established_against_control"]
                 else "NOT established against control"))
    if "super_additivity" in res:
        sa = res["super_additivity"]
        print("[ext] super-additivity %s: %+.4f  CI [%+.4f, %+.4f]  frac<=0 %.3f  -> %s"
              % ("/".join(sa["arms"]), sa["excess"], sa["ci95_domain_clustered"][0],
                 sa["ci95_domain_clustered"][1], sa["frac_draws_le_0"],
                 "ESTABLISHED" if sa["established"] else "NOT established"))
    print(f"[ext] -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
