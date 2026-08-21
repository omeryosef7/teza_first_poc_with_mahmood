"""analyze_phase_d.py -- plan §6 Decision Gate D: does prompt-level Boombness predict ASR, cleanly?

WHAT MAKES THIS DIFFERENT FROM G2, WHICH WAS RETRACTED. G2's positive correlation died of three
things, and the design here answers each by construction rather than by argument:

  * pseudo-replication -- rows that SHARED demonstrations counted as independent. Here every level
    carries 120 families that are pairwise disjoint within the level (`PHASE_D_SLOTS_N2`), and the
    bank fixes `n_examples=2` precisely to buy that.
  * designed-variance rows mixed with core rows -- here the whole bank IS the designed variance,
    one factor per block, with a single shared baseline cell.
  * unsafe filtering and a self-fit direction -- the extraction reports
    `n_self_fit_rows: 0 / n_cross_fit_rows: 2160`, so every Boombness value is read off the
    COMMITTED 2x2 direction, never one fitted on the prompt being scored.

THE SELECTION PROBLEM, AND THE ONLY HONEST ANSWER TO IT. There are 3 positions x 35 layer choices
x 2 readouts = 210 candidate metrics per direction. Reporting the best of 210 is how a null becomes
a finding. So the gate is NESTED and uses the bank's own split:

    choose the single best metric on `dev`  ->  test THAT ONE metric on `heldout`.

The heldout test has a family of exactly one, so its p-value needs no correction and means what it
says. The full dev grid is reported too, with Holm over all 210, but the dev grid is *selection*,
not evidence.

NEGATIVE CONTROLS ARE OTHER DIRECTIONS, NOT NOISE. `d_context` and `d_naive` were extracted on the
same rows and go through the identical pipeline. If `d_surface` predicts ASR and they do not, that is
specificity; if all three predict equally, the metric is reading prompt structure, which is what
Phase B's retraction F-2 already showed for the token-level gradient.

INFERENCE. The unit is the DOMAIN (6 clusters). Pooled Spearman is reported because it is what G2
reported and it must be comparable, but it is NOT the estimand: prompts within a domain share demo
sentences and a harm topic. The estimand is the per-domain rho aggregated across domains, with a
WITHIN-DOMAIN permutation null (labels shuffled inside each domain, so the null preserves the domain
structure the alternative is not allowed to borrow).

NO SCIPY in this environment; ranks, Pearson, the t-reference and the permutation are done here.

SAFETY: reads judge scalars and extraction scalars only. Never opens gens.jsonl.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import random
import statistics as st
import zlib
import subprocess
import sys
from typing import Dict, List, Optional, Sequence, Tuple

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


BANDS = {"L6_12": list(range(6, 13)), "L14_21": list(range(14, 22)), "Lall": list(range(32))}


def ranks(xs: Sequence[float]) -> List[float]:
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    out = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            out[order[k]] = avg
        i = j + 1
    return out


def pearson(a: Sequence[float], b: Sequence[float]) -> Optional[float]:
    n = len(a)
    if n < 3:
        return None
    ma, mb = st.mean(a), st.mean(b)
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    if va <= 0 or vb <= 0:
        return None
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(va * vb)


def spearman(a: Sequence[float], b: Sequence[float]) -> Optional[float]:
    return pearson(ranks(a), ranks(b))


def within_domain_rho(vals: Dict[str, Tuple[List[float], List[float]]]) -> dict:
    """Per-domain Spearman, then a cluster-level mean with G-1 df. The estimand."""
    per = {}
    for dom, (x, y) in sorted(vals.items()):
        r = spearman(x, y)
        if r is not None:
            per[dom] = {"rho": r, "n": len(x)}
    if not per:
        return {"per_domain": {}, "degenerate": True, "degenerate_reason": "no domain is estimable"}
    cl = cluster_mean_ci({d: [v["rho"]] for d, v in per.items()}, n_effective=len(per))
    return {"per_domain": per, "mean_rho": cl.get("mean"), "se": cl.get("se"),
            "ci95": cl.get("ci"), "p_vs_0": cl.get("p_vs_0"), "n_domains": cl.get("n_clusters"),
            "degenerate": cl.get("degenerate", False)}


def perm_p_within_domain(vals: Dict[str, Tuple[List[float], List[float]]], observed: float,
                         n_perm: int, seed: int) -> float:
    """Two-sided permutation p, shuffling the OUTCOME inside each domain.

    Shuffling globally would let the null be broken by between-domain differences in both the metric
    and the ASR -- which is exactly the confound clustering exists to price -- and would return an
    optimistically small p. Shuffling within domain holds the domain structure fixed.
    """
    rng = random.Random(seed)
    hits = 0
    for _ in range(n_perm):
        shuffled = {}
        for dom, (x, y) in vals.items():
            yy = list(y)
            rng.shuffle(yy)
            shuffled[dom] = (x, yy)
        r = within_domain_rho(shuffled).get("mean_rho")
        if r is not None and abs(r) >= abs(observed):
            hits += 1
    return (hits + 1) / (n_perm + 1)


def holm(pvals: Dict[str, float], alpha: float = 0.05) -> dict:
    items = sorted(((k, v) for k, v in pvals.items() if v is not None), key=lambda kv: kv[1])
    m, out, running = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return {"m": m, "adjusted": out, "rejects": sorted(k for k, v in out.items() if v <= alpha)}


def build_metrics(ex_rows: List[dict], direction: str) -> Dict[str, Dict[str, float]]:
    """-> {prompt_id: {metric_name: value}} for one direction.

    Positions: `demo_mean` and `demo_max` over the non-query occurrences, `query` at the single
    query occurrence (which is also the final one in this bank). Layer choices: every layer, plus
    the two bands the sprint has causal evidence about and an all-layer mean.
    """
    by_pid: Dict[str, List[dict]] = collections.defaultdict(list)
    for r in ex_rows:
        by_pid[r["prompt_id"]].append(r)
    out: Dict[str, Dict[str, float]] = {}
    for pid, rs in by_pid.items():
        demos = [r for r in rs if not r.get("is_query_occurrence")]
        query = [r for r in rs if r.get("is_query_occurrence")]
        m: Dict[str, float] = {}
        for readout in ("proj", "cos"):
            per_layer_demo, per_layer_query = {}, {}
            for L in range(32):
                key = f"{direction}|L{L}|{readout}"
                dv = [r[key] for r in demos if r.get(key) is not None]
                qv = [r[key] for r in query if r.get(key) is not None]
                if dv:
                    m[f"demo_mean|L{L}|{readout}"] = st.mean(dv)
                    m[f"demo_max|L{L}|{readout}"] = max(dv)
                    per_layer_demo[L] = st.mean(dv)
                if qv:
                    m[f"query|L{L}|{readout}"] = qv[0]
                    per_layer_query[L] = qv[0]
            for band, layers in BANDS.items():
                dvals = [per_layer_demo[L] for L in layers if L in per_layer_demo]
                qvals = [per_layer_query[L] for L in layers if L in per_layer_query]
                if dvals:
                    m[f"demo_mean|{band}|{readout}"] = st.mean(dvals)
                    m[f"demo_max|{band}|{readout}"] = max(dvals)
                if qvals:
                    m[f"query|{band}|{readout}"] = st.mean(qvals)
        out[pid] = m
    return out


def evaluate(metrics: Dict[str, Dict[str, float]], outcome: Dict[str, float],
             domain: Dict[str, str], pids: List[str], names: List[str],
             n_perm: int, seed: int, do_perm: bool) -> Dict[str, dict]:
    res = {}
    for name in names:
        pool: Dict[str, Tuple[List[float], List[float]]] = collections.defaultdict(
            lambda: ([], []))
        xs, ys = [], []
        for p in pids:
            v = metrics.get(p, {}).get(name)
            o = outcome.get(p)
            if v is None or o is None:
                continue
            d = domain[p]
            pool[d][0].append(v)
            pool[d][1].append(o)
            xs.append(v)
            ys.append(o)
        if len(xs) < 10:
            res[name] = {"n": len(xs), "degenerate": True}
            continue
        wd = within_domain_rho({k: (list(a), list(b)) for k, (a, b) in pool.items()})
        entry = {"n": len(xs), "pooled_rho": spearman(xs, ys), "within_domain": wd}
        if do_perm and wd.get("mean_rho") is not None:
            entry["perm_p_within_domain"] = perm_p_within_domain(
                {k: (list(a), list(b)) for k, (a, b) in pool.items()},
                wd["mean_rho"], n_perm, seed)
        res[name] = entry
    return res


def family_bootstrap(metrics: Dict[str, Dict[str, float]], outcome: Dict[str, float],
                     domain: Dict[str, str], family: Dict[str, str], pids: List[str],
                     name: str, n_boot: int, seed: int) -> dict:
    """Resample FAMILIES with replacement; refit the within-domain estimand each replicate.

    WHY (R5-4). The 15 strength levels are built from the SAME 120 families, so prompts sharing a
    family are not independent across levels and the domain-clustered SE prices only the domain
    layer. Measured, that makes the within-level SEs ~11% too small. Resampling at the family level
    prices the dependence the design actually has.

    Reported as a percentile interval plus the count of replicates at or below zero -- the latter is
    the one-sided evidence the sprint quoted, and it was markdown-only until review #8 (F2) caught
    that no artifact carried it.
    """
    by_fam: Dict[str, List[str]] = collections.defaultdict(list)
    for p in pids:
        by_fam[family.get(p, p)].append(p)
    fams = sorted(by_fam)
    if len(fams) < 3:
        return {"degenerate": True, "reason": f"only {len(fams)} families; a family bootstrap "
                                              f"needs >=3 or the interval is degenerate"}
    # GUARD (review #10). The `len(fams) < 3` check above catches the ALL-COLLAPSED failure
    # (every prompt in one family). It cannot catch the ALL-UNIQUE failure -- one family per
    # prompt -- which silently degrades this into an iid bootstrap and UNDERSTATES the SE by
    # ~1.7x here. That is the failure that actually shipped, so it is now an explicit error.
    if len(fams) >= len(pids):
        raise SystemExit(f"[phaseD] family bootstrap has {len(fams)} families for {len(pids)} "
                         f"prompts -- one family per prompt is an iid bootstrap, not a family "
                         f"bootstrap. Check the family key.")
    rng = random.Random(seed)
    reps: List[float] = []
    for _ in range(n_boot):
        draw: List[str] = []
        for _ in range(len(fams)):
            draw.extend(by_fam[fams[rng.randrange(len(fams))]])
        pool: Dict[str, Tuple[List[float], List[float]]] = collections.defaultdict(
            lambda: ([], []))
        for p in draw:
            v = metrics.get(p, {}).get(name)
            o = outcome.get(p)
            if v is None or o is None:
                continue
            pool[domain[p]][0].append(v)
            pool[domain[p]][1].append(o)
        r = within_domain_rho({k: (list(a), list(b)) for k, (a, b) in pool.items()}).get("mean_rho")
        if r is not None:
            reps.append(r)
    if len(reps) < n_boot // 2:
        return {"degenerate": True, "reason": f"only {len(reps)}/{n_boot} replicates estimable"}
    reps.sort()
    lo = reps[int(0.025 * (len(reps) - 1))]
    hi = reps[int(0.975 * (len(reps) - 1))]
    centre = st.mean(reps)
    # Sign-aware: count replicates that cross zero AGAINST the observed sign. Hard-coding
    # "<= 0" reported 1.0 for d_inter (mean rho -0.27, every replicate negative) -- i.e. "no
    # evidence" for the strongest effect in the table, with the sign flipped. Review #10.
    opposite = (sum(1 for r in reps if r <= 0.0) if centre >= 0
                else sum(1 for r in reps if r >= 0.0))
    return {"n_families": len(fams), "n_prompts": len(pids), "n_replicates": len(reps),
            "se_family_bootstrap": st.pstdev(reps) if len(reps) > 1 else None,
            "ci95_percentile": [lo, hi],
            "n_replicates_crossing_zero_against_observed_sign": opposite,
            "evidence_frac_crossing_zero": opposite / len(reps),
            "scope": "domains are held FIXED (families are resampled globally, and all domains "
                     "appear in every replicate), so this prices WITHIN-domain sampling error. "
                     "The domain-clustered SE prices BETWEEN-domain heterogeneity of rho. The two "
                     "are different variance components and neither is a corrected version of the "
                     "other -- do not compare them directly (review #10).",
            "not_a_p_value": "the bootstrap distribution is centred on the observed estimate, not "
                             "on the null, so the crossing fraction is CI-inversion evidence and "
                             "is sign-aware; it is not a permutation p"}


def load_cfg(run_dir: str) -> Optional[dict]:
    p = os.path.join(run_dir, "config.json")
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        raw = json.load(fh)
    return raw.get("args") if isinstance(raw.get("args"), dict) else raw


def level_of(r: dict) -> str:
    """The designed-variance LEVEL a row belongs to. One factor varies per block."""
    b = r.get("bank_block")
    return {"phase_d_base": "base",
            "phase_d_strength": "str:" + str(r.get("strength")),
            "phase_d_consistency": "con:" + str(r.get("consistency")),
            "phase_d_position": "pos:" + str(r.get("example_position")),
            "phase_d_role": "role:" + str(r.get("role_style"))}.get(b, "?" + str(b))


def between_vs_within_level(metrics: Dict[str, Dict[str, float]], outcome: Dict[str, float],
                            level: Dict[str, str], pids: List[str], name: str) -> dict:
    """Split the correlation into the part the DESIGN put there and the part it did not.

    THIS IS THE TEST THAT DECIDES WHAT THE CORRELATION MEANS, and without it a designed-variance
    bank is a trap rather than an improvement. The bank deliberately makes ASR differ across levels
    -- `str:aggressive` is at 0.46 and `con:mixed` at 0.008 -- so ANY metric that also differs across
    levels will correlate with ASR when the levels are pooled, whether or not it tracks anything
    within a level. That is the same shape as the between-domain trap in this module's self-test,
    one grain up, and it is the shape G2 died of.

      * BETWEEN-level: rho over the 15 level means. Reads the manipulation.
      * WITHIN-level: rho inside each level (fixed manipulation, 120 independent families), then a
        cluster mean over levels with G-1 df. This is prompt-to-prompt variance the design did not
        create, and it is the only part that could support a per-prompt objective.

    Also reports COVERAGE: a demo-based metric is undefined wherever there are no demo occurrences
    of the codeword -- `consistency=irrelevant` teaches a different word, so its 120 prompts have the
    codeword only at the query. Those rows are legitimately absent, but a headline rho computed on
    14 of 15 levels must say so.
    """
    per_level: Dict[str, Tuple[List[float], List[float]]] = collections.defaultdict(
        lambda: ([], []))
    for p in pids:
        v = metrics.get(p, {}).get(name)
        o = outcome.get(p)
        if v is None or o is None:
            continue
        per_level[level[p]][0].append(v)
        per_level[level[p]][1].append(o)
    all_levels = sorted({level[p] for p in pids})
    covered = sorted(per_level)
    lm = [st.mean(per_level[l][0]) for l in covered]
    la = [st.mean(per_level[l][1]) for l in covered]
    within = {}
    for l in covered:
        r = spearman(*per_level[l])
        if r is not None:
            within[l] = r
    cl = cluster_mean_ci({l: [r] for l, r in within.items()}, n_effective=len(within))
    return {
        "n_levels_total": len(all_levels),
        "n_levels_metric_available": len(covered),
        "levels_metric_unavailable": sorted(set(all_levels) - set(covered)),
        # AVAILABLE IS NOT ESTIMABLE, and conflating them hid a real gap (review #5). A level can
        # carry the metric on all 120 prompts and still contribute NOTHING to the mean, because
        # Spearman is undefined when the OUTCOME is constant inside it -- e.g. every heldout
        # `con:mixed` prompt scores StrongReject 0.000. The old field said 15/15 while the mean was
        # taken over 14, and for the refusal comparison it said 15/15 while the mean used 6.
        "n_levels_rho_estimable": len(within),
        "levels_rho_not_estimable": sorted(set(covered) - set(within)),
        "coverage_note": "metric_available: a demo-based metric is undefined where the codeword "
                         "never appears in a demonstration (consistency=irrelevant teaches a "
                         "different word). rho_estimable: additionally requires the OUTCOME to vary "
                         "inside the level. The mean below is over rho_estimable levels ONLY.",
        "n_prompts_used": sum(len(v[0]) for v in per_level.values()),
        "between_level_rho": spearman(lm, la) if len(lm) > 2 else None,
        "level_means": {l: {"metric": st.mean(per_level[l][0]),
                            "outcome": st.mean(per_level[l][1]),
                            "n": len(per_level[l][0])} for l in covered},
        "within_level_rho_by_level": within,
        "within_level_mean_rho": cl.get("mean"), "within_level_se": cl.get("se"),
        "within_level_p_vs_0": cl.get("p_vs_0"), "within_level_n_levels": cl.get("n_clusters"),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--extract", required=True, help="extract_boombness run dir (phase_d bank)")
    ap.add_argument("--judge", required=True, action="append",
                    help="judge run dir over the phase_d generations. Repeatable: the judge loop is "
                         "sequential so the run was SHARDED with --offset/--limit, and the shards "
                         "are read together here rather than merged into a fake single run dir. "
                         "The union is asserted complete and duplicate-free below.")
    ap.add_argument("--condition", default="natural_doublespeak")
    ap.add_argument("--directions", default="d_surface,d_context,d_naive")
    ap.add_argument("--outcome", default="malicious_at_0.5,strongreject_score")
    ap.add_argument("--n-perm", type=int, default=2000)
    ap.add_argument("--n-boot", type=int, default=2000,
                    help="family-level bootstrap replicates for the heldout estimand (R5-4)")
    ap.add_argument("--seed", type=int, default=20260820)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    ex = [r for r in read_jsonl(os.path.join(args.extract, "results.jsonl"))
          if r.get("condition") == args.condition]
    ju: Dict[str, dict] = {}
    shard_rows, dupes = {}, []
    for jd in args.judge:
        rs = [r for r in read_jsonl(os.path.join(jd, "results.jsonl"))
              if r.get("judge_status") == "ok" and r.get("condition") == args.condition]
        shard_rows[os.path.basename(jd.rstrip("/"))] = len(rs)
        for r in rs:
            if r["prompt_id"] in ju:
                dupes.append(r["prompt_id"])
            ju[r["prompt_id"]] = r
    if dupes:
        raise SystemExit(f"[phaseD] {len(dupes)} prompt_id appear in more than one judge shard "
                         f"(e.g. {dupes[:3]}); the shards overlap and the union is not a partition")

    domain = {r["prompt_id"]: str(r.get("domain")) for r in ex}
    level = {r["prompt_id"]: level_of(r) for r in ex}
    # `family_id` is a 9-part pipe-delimited CELL key and is UNIQUE PER PROMPT (1800 ids for
    # 1800 prompts). Using it whole made the "family bootstrap" an iid prompt bootstrap -- the
    # exact defect it existed to correct. The family is the first three parts
    # (domain|split|stem): 120 keys x 15 levels. Found by review #10.
    family = {r["prompt_id"]: "|".join(str(r.get("family_id")).split("|")[:3]) for r in ex}
    split = {r["prompt_id"]: str(r.get("split")) for r in ex}
    block = {r["prompt_id"]: str(r.get("bank_block")) for r in ex}
    ex_pids = sorted({r["prompt_id"] for r in ex})
    common = sorted(set(ex_pids) & set(ju))
    accounting = {
        "n_extract_prompts": len(ex_pids), "n_judged_prompts": len(ju),
        "n_joined": len(common),
        "n_extract_only": len(set(ex_pids) - set(ju)),
        "n_judge_only": len(set(ju) - set(ex_pids)),
        "by_split": dict(collections.Counter(split[p] for p in common)),
        "by_domain": dict(collections.Counter(domain[p] for p in common)),
        "by_block": dict(collections.Counter(block[p] for p in common)),
    }
    # STALE-JOIN GUARD. prompt_id does not hash the prompt text (R1); prompt_sha16 does.
    #
    # THE FIRST VERSION OF THIS GUARD WAS A NO-OP, found by review #5. `judge_boombness` does not
    # copy `prompt_sha16` into its result rows -- its `base` dict names fifteen fields and that is
    # not one of them -- so `ju_sha.get(p) is not None` was False for every prompt, `mism` was
    # always empty, and the artifact wrote `n_prompt_sha16_mismatch: 0` unconditionally. The
    # write-up then cited that zero as evidence. A guard that cannot fail is worse than no guard,
    # because it is quoted.
    #
    # Fixed by refusing to be silent about which check actually ran: if no judge row carries the
    # hash, fall back to bank-PATH equality between the two runs' configs and SAY SO in the
    # artifact; if neither check is available, raise.
    ex_sha = {r["prompt_id"]: r.get("prompt_sha16") for r in ex}
    n_ju_with_sha = sum(1 for p in common if ju[p].get("prompt_sha16") is not None)
    accounting["n_judge_rows_with_prompt_sha16"] = n_ju_with_sha
    if n_ju_with_sha:
        mism = [p for p in common if ju[p].get("prompt_sha16") is not None
                and ex_sha.get(p) != ju[p]["prompt_sha16"]]
        accounting["stale_join_check"] = "prompt_sha16 compared per row"
        accounting["n_prompt_sha16_mismatch"] = len(mism)
        if mism:
            raise SystemExit(f"[phaseD] {len(mism)} prompts join on prompt_id but differ in "
                             f"prompt_sha16 -- extraction and judge scored DIFFERENT text")
    else:
        ex_bank = (load_cfg(args.extract) or {}).get("bank")
        ju_banks = {(load_cfg(j) or {}).get("bank") for j in args.judge}
        accounting["extract_bank"] = ex_bank
        accounting["judge_banks"] = sorted(str(b) for b in ju_banks)
        if ex_bank and ju_banks == {ex_bank}:
            accounting["stale_join_check"] = (
                "prompt_sha16 ABSENT from every judge row, so the per-row content check was "
                "IMPOSSIBLE; fell back to bank-path equality, which passed. Weaker: it certifies "
                "the same bank FILE, not the same bytes.")
            accounting["n_prompt_sha16_mismatch"] = None
        else:
            raise SystemExit(f"[phaseD] no judge row carries prompt_sha16 AND the bank paths differ "
                             f"(extract {ex_bank!r} vs judge {sorted(str(b) for b in ju_banks)}); "
                             f"nothing establishes the two runs scored the same prompts")

    dev = [p for p in common if split[p] == "dev"]
    hel = [p for p in common if split[p] == "heldout"]

    out = {
        "script": "src/boombness/analyze_phase_d.py",
        "plan_section": "§6 -- Decision Gate D",
        "git_commit": git_commit_safe(),
        "inputs": {"extract": os.path.relpath(args.extract, REPO),
                   "judge_shards": [os.path.relpath(j, REPO) for j in args.judge],
                   "judge_shard_rows": shard_rows},
        "condition": args.condition,
        "estimand": "per-domain Spearman rho aggregated over 6 domain clusters (G-1 df); the "
                    "pooled rho is reported for comparability with G2 but is NOT the estimand",
        "selection_protocol": "best |within-domain mean rho| chosen on dev; that ONE metric tested "
                              "on heldout, where the family size is 1 and no correction applies",
        "row_accounting": accounting,
        "bank_refusal_context": {
            "kw_refusal_rate": (sum(1.0 for p in common if ju[p].get("refused")) / len(common))
                               if common else None,
            "asr_at_0.5": (sum(1.0 for p in common if ju[p].get("malicious_at_0.5")) / len(common))
                          if common else None,
            "note": "if the refusal rate is near zero the refusal GATE is not the mechanism on this "
                    "bank, and a metric predicting ASR here is predicting content, not compliance -- "
                    "the opposite regime from AdvBench, where Phase E4 found every point of "
                    "StrongReject movement was a refusal flip",
        },
        "n_dev": len(dev), "n_heldout": len(hel),
        "directions": {},
    }

    for direction in args.directions.split(","):
        met = build_metrics(ex, direction)
        names = sorted({k for m in met.values() for k in m})
        out["directions"][direction] = {"n_candidate_metrics": len(names), "outcomes": {}}
        for oc in args.outcome.split(","):
            outcome = {p: float(ju[p][oc]) for p in common if ju[p].get(oc) is not None}
            dev_res = evaluate(met, outcome, domain, dev, names, args.n_perm, args.seed,
                               do_perm=False)
            usable = {k: v for k, v in dev_res.items()
                      if not v.get("degenerate") and v["within_domain"].get("mean_rho") is not None}
            if not usable:
                out["directions"][direction]["outcomes"][oc] = {"error": "no estimable metric"}
                continue
            best = max(usable, key=lambda k: abs(usable[k]["within_domain"]["mean_rho"]))
            hel_res = evaluate(met, outcome, domain, hel, [best], args.n_perm, args.seed,
                               do_perm=True)[best]
            dev_ps = {k: v["within_domain"].get("p_vs_0") for k, v in usable.items()}
            out["directions"][direction]["outcomes"][oc] = {
                "selected_on_dev": best,
                "dev": usable[best],
                "HELDOUT_TEST": hel_res,
                "HELDOUT_family_bootstrap": family_bootstrap(
                    met, outcome, domain, family, hel, best, args.n_boot,
                    args.seed + (zlib.crc32(f"{direction}|{oc}".encode()) % 100000)),
                "HELDOUT_between_vs_within_level": between_vs_within_level(
                    met, outcome, level, hel, best),
                "ALL_between_vs_within_level": between_vs_within_level(
                    met, outcome, level, common, best),
                # GATE REQUIREMENT 3: "the metric is not just refusalness". Testable here with no
                # refusalness direction, because the judge records a keyword refusal flag per row.
                # If the metric predicts ASR only by predicting refusal, it is the refusal channel
                # wearing a different name.
                "vs_refusal_within_level": between_vs_within_level(
                    met, {p: (1.0 if ju[p].get("refused") else 0.0) for p in common
                          if ju[p].get("refused") is not None},
                    level, common, best),
                "dev_grid_holm": holm(dev_ps),
                "dev_top5": sorted(
                    ({"metric": k, "within_domain_mean_rho": v["within_domain"]["mean_rho"],
                      "p_cl": v["within_domain"].get("p_vs_0"), "pooled_rho": v["pooled_rho"]}
                     for k, v in usable.items()),
                    key=lambda d: -abs(d["within_domain_mean_rho"]))[:5],
            }

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"[phaseD] wrote {args.out}  joined={len(common)} dev={len(dev)} heldout={len(hel)}")
    for d, dd in out["directions"].items():
        for oc, r in dd["outcomes"].items():
            if "error" in r:
                print(f"  {d:10s} {oc:22s} {r['error']}")
                continue
            h = r["HELDOUT_TEST"]
            wd = h.get("within_domain", {})
            bw = r["ALL_between_vs_within_level"]
            print(f"  {d:10s} {oc:22s} sel={r['selected_on_dev']:22s} "
                  f"HELDOUT rho={wd.get('mean_rho'):+.4f} p_cl={wd.get('p_vs_0'):.2g} "
                  f"| BETWEEN-level {bw['between_level_rho']:+.4f} "
                  f"WITHIN-level {bw['within_level_mean_rho']:+.4f} "
                  f"p={bw['within_level_p_vs_0'] and round(bw['within_level_p_vs_0'],4)} "
                  f"estimable={bw['n_levels_rho_estimable']}/{bw['n_levels_total']}")


if __name__ == "__main__":
    main()
