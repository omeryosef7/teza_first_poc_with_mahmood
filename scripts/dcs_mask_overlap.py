#!/usr/bin/env python3
"""DCS PHASE-8 §16C: WITHIN A CONTROL DRAW, DO DIFFERENT ROWS GET SIMILAR MASKS?

WHY THIS EXISTS. `R-077` established that the between-control-draw spread in behaviour is REAL and
near-deterministic (split-half rho = +0.988; 93.5 % draw offset / 5.3 % row sampling / 1.2 % judge),
so *which positions a draw masks* dominates behaviour at constant dose. `R-076` then found NO
geometric predictor of that offset (7 index-summary features, best |rho| 0.238, n = 8). The
continuation plan's item #1(c) is the one piece never run: it asks the prior, structural question --
does a draw even HAVE a coherent mask identity across its 1160 rows, or is each row an independent
lottery ticket? A draw can only carry a stable arm-level offset if the thing that is constant within
it (the seed) actually makes its rows resemble each other.

⛔ WHAT THIS IS NOT. This is NOT a refusal/ASR predictor. §1.2 of the phase log CLOSES "mask geometry
as a refusal predictor" (`R-076`), and at n = 8 arms any such correlation excludes only |rho| ≳ 0.71
anyway. Nothing here is regressed on behaviour, and no such analysis may be grafted on without its
own preregistration.

────────────────────────────────────────────────────────────────────────────────────────────────
THE STATISTIC, AND EXACTLY HOW LENGTH IS NORMALISED
────────────────────────────────────────────────────────────────────────────────────────────────
Rows differ in prompt length (seq_len 78 distinct values here), in demo-block size (key count k
42-94) and in pool size (n_pool 117-179). Raw Jaccard between two rows' absolute key sets is
therefore length-confounded: two short prompts share a small index range and overlap more by
accident than two long ones.

⇒ THE NORMALISATION IS THE MATCHED NULL, NOT A RESCALING OF THE POSITIONS. Stated exactly:

  PRIMARY   J_abs(i,j) = |P_i ∩ P_j| / |P_i ∪ P_j| on ABSOLUTE token indices, unrescaled.
            Arm statistic = mean J_abs over all C(n_rows, 2) row pairs.
            NULL: every row is redrawn INDEPENDENTLY -- a distinct seed per (row, replicate) --
            from ITS OWN recorded pool with ITS OWN key count, using the repo's own
            `score_behavior.nondemo_control_draw`. Every consequence of differing prompt length,
            differing demo-span placement, differing protected-span placement and differing key
            count is therefore present in the null at exactly the magnitude it has in the data.
            Reported: EXCESS = J_obs - mean(J_null), RATIO = J_obs / mean(J_null), and
            z = (J_obs - mean(J_null)) / sd(J_null) across replicates.

  SECONDARY J_rank: each drawn absolute position is replaced by its RANK inside that row's own
            sorted pool (0 .. n_pool-1), then the same Jaccard and the same matched null. This is
            length-normalised by construction and isolates "the same RNG stream selects the same
            ORDINAL slots" from "the pools happen to overlap".

  TERTIARY  EXACT-CLONE RATE on the pairs where the mechanism makes a sharp prediction: rows with
            IDENTICAL (n_pool, k) are handed the same `random.Random(seed).sample(pool, k)` call
            shape, so a per-ARM seed predicts BYTE-IDENTICAL RANK SETS. Length normalisation is
            moot on these pairs -- the two rows have the same pool size and the same count.

  CONTROL   CROSS-ARM overlap: the same mean pairwise Jaccard taken between DIFFERENT rows of TWO
            DIFFERENT arms. Those rows share the prompt population and the pool geometry but NOT
            the seed. If the within-arm excess is really the shared seed, cross-arm overlap must
            sit AT the independent-sampling null; if cross-arm overlap is elevated too, the excess
            is a property of the prompt set rather than of the draw and the whole reading fails.
            This is the falsification arm of the test, not decoration.

────────────────────────────────────────────────────────────────────────────────────────────────
STATISTICS -- DECLARED BEFORE ANY NUMBER IS READ
────────────────────────────────────────────────────────────────────────────────────────────────
* THE INDEPENDENCE UNIT FOR ANY POPULATION-LEVEL CLAIM IS THE ARM (the draw). n = 8.
* PER-ARM test: the null fully specifies the row-wise draw law (independent sampling from the
  row's own recorded pool), so the Monte-Carlo test inside one arm is exact conditional on that
  arm's pools and counts. Its ATTAINABLE p-FLOOR is 1/(B+1) for B null replicates:
  B = 60 (default) -> 0.0164;  B = 100 -> 0.0099;  B = 200 -> 0.00498. All below 0.05.
* POPULATION test across arms: exact two-sided SIGN TEST on how many of the 8 arms show a positive
  excess. ATTAINABLE p-FLOOR at n = 8 is 2 / 2^8 = 0.0078 (one-sided 0.0039). Below 0.05, so the
  design is INFORMATIVE rather than uninformative-by-construction. If the arm count ever drops
  below 6, the two-sided floor is 2/2^5 = 0.0625 > 0.05 and the test becomes UNINFORMATIVE BY
  CONSTRUCTION -- the script says so and returns CANNOT ANSWER instead of a null.
* VACUOUS-vs-FALSE, declared before the data: this test can come back three ways.
    (1) excess ~ 0 in most arms  -> the hypothesis is FALSE: rows are an independent lottery.
    (2) excess large in all arms AND near-constant between them -> the hypothesis is TRUE as a
        statement about a single draw, but VACUOUS as an explanation of why draws DIFFER: a
        constant cannot explain a spread. Declared rule: "near-constant" iff the range of EXCESS
        across arms is < 10 % of its mean.
    (3) excess large and varying between arms -> a live candidate mechanism for the offset SPREAD;
        it would still need its own preregistered test against behaviour, which this is not.

────────────────────────────────────────────────────────────────────────────────────────────────
PROVENANCE (no draw is reimplemented here)
────────────────────────────────────────────────────────────────────────────────────────────────
`B-007`/`R-066`: behavioural arms persist the drawn positions verbatim in
`control_draw[...]["positions"]`, so the observed masks are READ, not regenerated. The NULL draws
call `src/boombness/score_behavior.py::nondemo_control_draw` directly, loaded through
`scripts/dcs_verify_draw_regenerable.py::_load_score_behavior`. The pool needed for the RANK
statistic is rebuilt with the same construction score_behavior uses and then HARD-CHECKED three
ways per arm: |pool| == recorded n_pool, every persisted position lies in the pool, and
regenerating with the persisted seed reproduces the persisted positions EXACTLY. Any failure is a
hard exit, not a warning.

Usage:
  python3 scripts/dcs_mask_overlap.py                    # the 8 K=8 control arms
  python3 scripts/dcs_mask_overlap.py --self-test        # synthetic draws with known overlap
  python3 scripts/dcs_mask_overlap.py --n-null 200 --out results.json
"""
import argparse, glob, importlib.util, json, math, os, random, statistics as st, sys

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The K = 8 control population of R-075/R-076/R-077 (see dcs_draw_offset_reliability.py's default).
DEFAULT_ARMS = ["dcsp24_d1", "dcsp24_d2", "dcsp24_d3",
                "dcsp28_s20260905_d1", "dcsp28_s20260905_d2", "dcsp28_s20260905_d3",
                "dcsp28_s20260906_d1", "dcsp28_s20260906_d2"]

MIN_ARMS_INFORMATIVE = 6          # two-sided sign-test floor 2/2^6 = 0.031 <= 0.05
NEAR_CONSTANT_FRAC = 0.10         # declared rule (2) above


# ---------------------------------------------------------------------------------------------
# repo reuse
# ---------------------------------------------------------------------------------------------
def load_score_behavior():
    """Reuse the verifier's loader rather than writing a third copy of it."""
    p = os.path.join(REPO, "scripts", "dcs_verify_draw_regenerable.py")
    spec = importlib.util.spec_from_file_location("dcs_verify_draw_regenerable", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["dcs_verify_draw_regenerable"] = mod
    spec.loader.exec_module(mod)
    return mod._load_score_behavior()


def newest_done(pattern):
    d = sorted(x for x in glob.glob(os.path.join(REPO, pattern))
               if os.path.isfile(os.path.join(x, "DONE.json")))
    return d[-1] if d else None


# ---------------------------------------------------------------------------------------------
# arm loading + provenance
# ---------------------------------------------------------------------------------------------
def load_arm(sb, arm_dir, max_rows=None):
    """Read one behavioural arm's persisted draws and rebuild each row's pool, verified."""
    rows = []
    for i, line in enumerate(open(os.path.join(arm_dir, "results.jsonl"))):
        if max_rows is not None and i >= max_rows:
            break
        r = json.loads(line)
        cd = r.get("control_draw")
        if not cd:
            sys.exit(f"{os.path.basename(arm_dir)} carries no per-row control_draw -- this is a "
                     "readout arm (R-066); point this at a behavioural arm")
        rec = list(cd.values())[0]
        dlo, dhi = r["demo_span_bounds"]
        qlo, qhi = r["query_span_bounds"]
        if (dhi - dlo + 1) != r["n_demo_span_positions"]:
            sys.exit(f"row {i}: demo keys are not the contiguous span; pool rebuild does not apply")
        demo_keys = list(range(dlo, dhi + 1))
        protected = set(range(qlo, qhi + 1))
        # SAME construction as score_behavior.nondemo_control_draw; verified below, never assumed.
        dks = set(demo_keys)
        pool = [x for x in range(1, max(0, int(r["seq_len"]) - 1))
                if x not in dks and x not in protected]
        rows.append({"prompt_id": r["prompt_id"], "seq_len": int(r["seq_len"]),
                     "demo_keys": demo_keys, "protected": protected, "pool": pool,
                     "pool_rank": {p: j for j, p in enumerate(pool)},
                     "k": int(rec["n_demo_keys"]), "n_pool": int(rec["n_pool"]),
                     "draw_seed": int(rec["draw_seed"]), "match_ratio": float(rec["match_ratio"]),
                     "positions": list(rec["positions"])})
    if not rows:
        sys.exit(f"{arm_dir}: no rows")

    # --- three hard provenance checks, per row -------------------------------------------------
    bad_pool = bad_member = bad_identity = 0
    for row in rows:
        if len(row["pool"]) != row["n_pool"]:
            bad_pool += 1
        if not set(row["positions"]).issubset(set(row["pool"])):
            bad_member += 1
        pos, _ = sb.nondemo_control_draw(row["demo_keys"], row["seq_len"],
                                         protected=row["protected"],
                                         seed=row["draw_seed"], policy="strict")
        if sorted(pos) != sorted(row["positions"]):
            bad_identity += 1
    if bad_pool or bad_member or bad_identity:
        sys.exit(f"{os.path.basename(arm_dir)}: PROVENANCE FAILED -- pool-size mismatches "
                 f"{bad_pool}, non-member positions {bad_member}, identity failures {bad_identity}")
    seeds = sorted({row["draw_seed"] for row in rows})
    mrs = sorted({row["match_ratio"] for row in rows})
    return rows, {"n_rows": len(rows), "distinct_draw_seeds": len(seeds), "draw_seeds": seeds[:4],
                  "match_ratio_values": mrs, "k_min": min(r["k"] for r in rows),
                  "k_max": max(r["k"] for r in rows),
                  "n_pool_min": min(r["n_pool"] for r in rows),
                  "n_pool_max": max(r["n_pool"] for r in rows)}


# ---------------------------------------------------------------------------------------------
# the overlap statistic
# ---------------------------------------------------------------------------------------------
def mean_pairwise_jaccard(sets, width):
    """Mean Jaccard over all C(n,2) pairs of index sets, via a boolean incidence matrix."""
    n = len(sets)
    M = np.zeros((n, width), dtype=np.float32)
    for i, s in enumerate(sets):
        M[i, np.asarray(s, dtype=np.int64)] = 1.0
    inter = M @ M.T
    k = M.sum(axis=1)
    union = k[:, None] + k[None, :] - inter
    iu = np.triu_indices(n, 1)
    j = inter[iu] / np.maximum(union[iu], 1.0)
    return float(j.mean())


def mean_cross_jaccard(sets_a, sets_b, width, exclude_same_index=True):
    """Mean Jaccard between rows of TWO arms. Row i of each arm is the SAME prompt, so the
    diagonal (same prompt, two seeds) is excluded by default: the control we want is
    DIFFERENT rows in DIFFERENT draws."""
    def inc(sets):
        M = np.zeros((len(sets), width), dtype=np.float32)
        for i, s in enumerate(sets):
            M[i, np.asarray(s, dtype=np.int64)] = 1.0
        return M
    A, B = inc(sets_a), inc(sets_b)
    inter = A @ B.T
    union = A.sum(1)[:, None] + B.sum(1)[None, :] - inter
    j = inter / np.maximum(union, 1.0)
    if exclude_same_index is not True and exclude_same_index is not False:
        pa, pb = exclude_same_index                     # (prompt-id codes a, prompt-id codes b)
        mask = np.asarray(pa)[:, None] != np.asarray(pb)[None, :]
        return float(j[mask].mean())
    if exclude_same_index:
        n = min(len(sets_a), len(sets_b))
        mask = np.ones_like(j, dtype=bool)
        mask[np.arange(n), np.arange(n)] = False
        return float(j[mask].mean())
    return float(j.mean())


def clone_rate(rank_sets, keys):
    """Fraction of same-(n_pool, k) pairs whose RANK sets are byte-identical. -1 if no such pair."""
    groups = {}
    for i, key in enumerate(keys):
        groups.setdefault(key, []).append(i)
    tot = same = 0
    for idxs in groups.values():
        if len(idxs) < 2:
            continue
        sig = {}
        for i in idxs:
            sig.setdefault(tuple(sorted(rank_sets[i])), 0)
            sig[tuple(sorted(rank_sets[i]))] += 1
        m = len(idxs)
        tot += m * (m - 1) // 2
        same += sum(c * (c - 1) // 2 for c in sig.values())
    return (same / tot if tot else -1.0), tot


def analyse_arm(sb, rows, n_null, seed, label, quiet=False):
    """Observed vs matched independent-sampling null, for one draw."""
    w_abs = max(r["seq_len"] for r in rows)
    w_rank = max(r["n_pool"] for r in rows)
    keys = [(r["n_pool"], r["k"]) for r in rows]

    obs_abs_sets = [r["positions"] for r in rows]
    obs_rank_sets = [[r["pool_rank"][p] for p in r["positions"]] for r in rows]
    obs_abs = mean_pairwise_jaccard(obs_abs_sets, w_abs)
    obs_rank = mean_pairwise_jaccard(obs_rank_sets, w_rank)
    obs_clone, n_clone_pairs = clone_rate(obs_rank_sets, keys)

    rng = random.Random(seed)
    null_abs, null_rank, null_clone = [], [], []
    for b in range(n_null):
        abs_sets, rank_sets = [], []
        for row in rows:
            s = rng.getrandbits(48)             # a distinct seed per (row, replicate) = INDEPENDENT
            pos, _ = sb.nondemo_control_draw(row["demo_keys"], row["seq_len"],
                                             protected=row["protected"], seed=s, policy="strict")
            abs_sets.append(pos)
            rank_sets.append([row["pool_rank"][p] for p in pos])
        null_abs.append(mean_pairwise_jaccard(abs_sets, w_abs))
        null_rank.append(mean_pairwise_jaccard(rank_sets, w_rank))
        null_clone.append(clone_rate(rank_sets, keys)[0])
        if not quiet and (b + 1) % 10 == 0:
            print(f"    [{label}] null replicate {b + 1}/{n_null}", flush=True)

    def summarise(obs, null):
        mu = st.fmean(null)
        sd = st.stdev(null) if len(null) > 1 else 0.0
        ge = sum(1 for v in null if v >= obs - 1e-15)
        return {"obs": obs, "null_mean": mu, "null_sd": sd,
                "excess": obs - mu, "ratio": (obs / mu) if mu > 0 else float("nan"),
                "z": ((obs - mu) / sd) if sd > 0 else float("inf"),
                "p_mc": (ge + 1) / (n_null + 1), "p_floor": 1.0 / (n_null + 1)}

    out = {"arm": label, "n_rows": len(rows), "n_pairs": len(rows) * (len(rows) - 1) // 2,
           "n_null": n_null,
           "abs": summarise(obs_abs, null_abs), "rank": summarise(obs_rank, null_rank),
           "clone": {"obs": obs_clone, "null_mean": st.fmean(null_clone),
                     "n_same_shape_pairs": n_clone_pairs}}
    return out


# ---------------------------------------------------------------------------------------------
# population-level (unit = arm)
# ---------------------------------------------------------------------------------------------
def sign_test_two_sided(n_pos, n):
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(max(n_pos, n - n_pos), n + 1))
    return min(1.0, 2.0 * tail / (2.0 ** n))


def report(results, stat="abs"):
    n = len(results)
    floor = sign_test_two_sided(n, n)
    print("\n" + "=" * 96)
    print(f"POPULATION LEVEL -- INDEPENDENCE UNIT = ARM (the draw), n = {n}")
    print(f"  attainable p-FLOOR, exact two-sided sign test at n={n}: p = {floor:.4f}"
          f"   (one-sided {floor / 2:.4f})")
    if n < MIN_ARMS_INFORMATIVE or floor > 0.05:
        print(f"  ⛔ the floor is ABOVE 0.05 -> the population test is UNINFORMATIVE BY "
              f"CONSTRUCTION at n = {n}. VERDICT: CANNOT ANSWER (not a null).")
        return "CANNOT ANSWER"
    print(f"  the floor is below 0.05 -> the population test is informative.")

    exc = [r[stat]["excess"] for r in results]
    n_pos = sum(1 for e in exc if e > 0)
    p = sign_test_two_sided(n_pos, n)
    print(f"  arms with positive excess: {n_pos}/{n}    sign-test p = {p:.4f}")

    mu = st.fmean(exc)
    rng_ = max(exc) - min(exc)
    frac = (rng_ / mu) if mu != 0 else float("inf")
    near_const = frac < NEAR_CONSTANT_FRAC
    sd_between = st.stdev(exc) if len(exc) > 1 else 0.0
    sd_mc = st.median([r[stat]["null_sd"] for r in results])
    print(f"  excess across arms: mean {mu:+.4f}  sd {sd_between:.4f}  range {rng_:.4f}  "
          f"range/mean {frac:.3f}  (declared near-constant iff < {NEAR_CONSTANT_FRAC})")
    print(f"  between-arm sd / within-arm Monte-Carlo sd = {sd_between / sd_mc:.0f}x"
          f"  -> the between-draw differences are {'REAL' if sd_between > 3 * sd_mc else 'NOT'} "
          f"resolvable above Monte-Carlo noise")
    if NEAR_CONSTANT_FRAC <= frac < 1.5 * NEAR_CONSTANT_FRAC:
        print(f"  ⚠ BORDERLINE: range/mean {frac:.3f} misses the pre-declared near-constant "
              f"threshold {NEAR_CONSTANT_FRAC} by a thin margin. The verdict below turns on that "
              f"threshold; read the dynamic range (ratio {min(r[stat]['ratio'] for r in results):.2f}"
              f"x - {max(r[stat]['ratio'] for r in results):.2f}x) before leaning on it.")

    if n_pos <= n // 2 or p > 0.05:
        verdict = ("HYPOTHESIS FALSE -- cross-row mask overlap sits at the independent-sampling "
                   "null; a draw's rows are an independent lottery, and #1(c)'s kill condition "
                   "in DCS_CONTINUATION_PLAN_20260905.md fires")
    elif near_const:
        verdict = ("TRUE-BUT-VACUOUS -- the overlap is real and large in every draw, but it is "
                   "NEAR-CONSTANT across draws, so it can explain why a draw HAS a coherent "
                   "arm-level identity and CANNOT explain why draws DIFFER. As an explanation of "
                   "the R-077 offset SPREAD it is vacuous (no variance to explain with), not false")
    else:
        verdict = ("TRUE AND VARYING -- overlap is above null in every draw and differs between "
                   "draws; a live candidate for the offset spread, which still needs its own "
                   "preregistered test against behaviour (NOT run here; see R-076 / §1.2)")
    print(f"\n  VERDICT ({stat}): {verdict}")
    return verdict


# ---------------------------------------------------------------------------------------------
# self-test
# ---------------------------------------------------------------------------------------------
def self_test(sb, args):
    """Synthetic draws with KNOWN overlap, laid over REAL row pools (so lengths really differ).

    CLONE       every row takes the same pool RANKS  -> maximal excess, clone rate 1.0
    HALF        half the ranks shared, half free     -> strictly intermediate excess
    INDEPENDENT every row drawn with its own seed    -> excess ~ 0, p must NOT be significant

    The INDEPENDENT arm is the calibration: an instrument that cannot come back null is not
    evidence (this project has had several fail their own audit).
    """
    arm_dir = newest_done(f"outputs/boombness/score_behavior/{args.arms[0]}_*")
    if not arm_dir:
        sys.exit(f"self-test needs one real arm for its row geometry; {args.arms[0]} not found")
    rows, prov = load_arm(sb, arm_dir, max_rows=args.self_test_rows)
    print(f"self-test geometry from {os.path.basename(arm_dir)}: {len(rows)} rows, "
          f"k {prov['k_min']}-{prov['k_max']}, n_pool {prov['n_pool_min']}-{prov['n_pool_max']}")

    rng = random.Random(args.seed)
    base_ranks = list(range(max(r["n_pool"] for r in rows)))
    rng.shuffle(base_ranks)

    def build(kind):
        out = []
        for r in rows:
            npool, k = r["n_pool"], r["k"]
            shared = [x % npool for x in base_ranks]
            shared = list(dict.fromkeys(shared))
            if kind == "clone":
                ranks = shared[:k]
            elif kind == "half":
                take = k // 2
                ranks = list(shared[:take])
                free = [x for x in range(npool) if x not in set(ranks)]
                ranks += random.Random(rng.getrandbits(48)).sample(free, k - take)
            else:
                ranks = random.Random(rng.getrandbits(48)).sample(range(npool), k)
            row = dict(r)
            row["positions"] = sorted(r["pool"][x] for x in ranks)
            out.append(row)
        return out

    res = {}
    for kind in ("clone", "half", "independent"):
        rr = analyse_arm(sb, build(kind), args.self_test_null, args.seed + 7, f"SELF:{kind}",
                         quiet=True)
        res[kind] = rr
        a, rk, cl = rr["abs"], rr["rank"], rr["clone"]
        print(f"  {kind:12s} J_abs {a['obs']:.4f} vs null {a['null_mean']:.4f} "
              f"(excess {a['excess']:+.4f}, z {a['z']:+.1f}, p {a['p_mc']:.4f}) | "
              f"J_rank excess {rk['excess']:+.4f} | clone {cl['obs']:.3f}")

    floor = 1.0 / (args.self_test_null + 1)
    checks = [
        ("CLONE excess > HALF excess",
         res["clone"]["abs"]["excess"] > res["half"]["abs"]["excess"]),
        ("HALF excess > INDEPENDENT excess",
         res["half"]["abs"]["excess"] > res["independent"]["abs"]["excess"]),
        ("CLONE fires at the Monte-Carlo floor",
         abs(res["clone"]["abs"]["p_mc"] - floor) < 1e-12),
        ("HALF fires at the Monte-Carlo floor",
         abs(res["half"]["abs"]["p_mc"] - floor) < 1e-12),
        ("INDEPENDENT does NOT fire (calibration: the test can come back null)",
         res["independent"]["abs"]["p_mc"] > 0.05),
        ("INDEPENDENT |z| < 3",
         abs(res["independent"]["abs"]["z"]) < 3.0),
        ("CLONE rank-clone rate == 1.0",
         res["clone"]["clone"]["obs"] > 0.999),
        ("INDEPENDENT rank-clone rate ~ 0",
         res["independent"]["clone"]["obs"] < 0.01),
    ]
    print()
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    allok = all(ok for _, ok in checks)
    print(f"\nSELF-TEST: {'PASS' if allok else 'FAIL'}")
    return 0 if allok else 1


# ---------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arms", nargs="+", default=DEFAULT_ARMS)
    ap.add_argument("--n-null", type=int, default=60,
                    help="null replicates per arm; the per-arm p-FLOOR is 1/(n_null+1)")
    ap.add_argument("--max-rows", type=int, default=None)
    ap.add_argument("--seed", type=int, default=20260906)
    ap.add_argument("--out", default=None, help="optional JSON path (nothing is written without it)")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--self-test-rows", type=int, default=200)
    ap.add_argument("--self-test-null", type=int, default=30)
    a = ap.parse_args()

    if os.environ.get("OMP_NUM_THREADS") != "1":
        print("WARN: OMP_NUM_THREADS is not 1; DCS-044 measured a 12x slowdown from BLAS threads",
              file=sys.stderr)

    sb = load_score_behavior()
    if a.self_test:
        return self_test(sb, a)

    print(f"PER-ARM p-FLOOR (Monte-Carlo, B={a.n_null}): {1.0 / (a.n_null + 1):.4f}")
    print(f"POPULATION p-FLOOR (exact two-sided sign test, n={len(a.arms)} arms): "
          f"{sign_test_two_sided(len(a.arms), len(a.arms)):.4f}\n")

    results = []
    arm_sets, arm_pids, pid_code = {}, {}, {}
    for tag in a.arms:
        d = newest_done(f"outputs/boombness/score_behavior/{tag}_*")
        if not d:
            sys.exit(f"missing finished arm {tag}")
        rows, prov = load_arm(sb, d, max_rows=a.max_rows)
        arm_sets[tag] = [r["positions"] for r in rows]
        arm_pids[tag] = [pid_code.setdefault(r["prompt_id"], len(pid_code)) for r in rows]
        print(f"[{tag}] {os.path.basename(d)}  rows={prov['n_rows']} "
              f"distinct_draw_seeds={prov['distinct_draw_seeds']} "
              f"match_ratio={prov['match_ratio_values']} k={prov['k_min']}-{prov['k_max']} "
              f"n_pool={prov['n_pool_min']}-{prov['n_pool_max']}  [provenance OK]", flush=True)
        r = analyse_arm(sb, rows, a.n_null, a.seed, tag)
        r["provenance"] = prov
        r["arm_dir"] = os.path.basename(d)
        results.append(r)
        A, R, C = r["abs"], r["rank"], r["clone"]
        print(f"    J_abs  obs {A['obs']:.4f}  null {A['null_mean']:.4f} +- {A['null_sd']:.4f}  "
              f"excess {A['excess']:+.4f}  ratio {A['ratio']:.2f}x  z {A['z']:+.1f}  "
              f"p {A['p_mc']:.4f}")
        print(f"    J_rank obs {R['obs']:.4f}  null {R['null_mean']:.4f} +- {R['null_sd']:.4f}  "
              f"excess {R['excess']:+.4f}  ratio {R['ratio']:.2f}x  z {R['z']:+.1f}  "
              f"p {R['p_mc']:.4f}")
        print(f"    exact-clone rate on same-(n_pool,k) pairs: obs {C['obs']:.4f}  "
              f"null {C['null_mean']:.4f}  ({C['n_same_shape_pairs']} such pairs)", flush=True)

    print("\n" + "=" * 96)
    print(f"{'arm':<26} {'J_abs':>8} {'null':>8} {'excess':>9} {'ratio':>7} {'z':>9} {'p':>8} "
          f"{'clone':>7}")
    for r in results:
        A = r["abs"]
        print(f"{r['arm']:<26} {A['obs']:8.4f} {A['null_mean']:8.4f} {A['excess']:+9.4f} "
              f"{A['ratio']:6.2f}x {A['z']:+9.1f} {A['p_mc']:8.4f} {r['clone']['obs']:7.4f}")

    # ---- CROSS-ARM FALSIFICATION CONTROL ------------------------------------------------------
    cross = []
    if len(a.arms) > 1:
        width = max(max(p for s in arm_sets[t] for p in s) for t in a.arms) + 1
        for i in range(len(a.arms)):
            for j in range(i + 1, len(a.arms)):
                ta, tb = a.arms[i], a.arms[j]
                cross.append(mean_cross_jaccard(arm_sets[ta], arm_sets[tb], width,
                                                exclude_same_index=(arm_pids[ta], arm_pids[tb])))
        null_mu = st.fmean(r["abs"]["null_mean"] for r in results)
        obs_mu = st.fmean(r["abs"]["obs"] for r in results)
        cm = st.fmean(cross)
        print("\n" + "=" * 96)
        print("CROSS-ARM FALSIFICATION CONTROL -- different rows, DIFFERENT draws (no shared seed)")
        print(f"  cross-arm mean J_abs over {len(cross)} arm pairs : {cm:.4f} "
              f"[{min(cross):.4f}, {max(cross):.4f}]")
        print(f"  independent-sampling null                        : {null_mu:.4f}")
        print(f"  within-arm observed                              : {obs_mu:.4f}")
        seed_specific = abs(cm - null_mu) < 0.25 * (obs_mu - null_mu)
        if seed_specific:
            print("  ⇒ SEED-SPECIFIC: cross-arm overlap sits AT the independent-sampling null, so "
                  "the\n    within-arm elevation is a property of the DRAW, not of the prompt set "
                  "or pool geometry.")
        else:
            print("  ⛔ NOT SEED-SPECIFIC: cross-arm overlap is ALSO elevated, so the excess is a "
                  "property\n    of the prompt set / pool geometry, NOT of the shared seed. The "
                  "within-arm reading FAILS.")

    v_abs = report(results, "abs")
    v_rank = report(results, "rank")

    if a.out:
        p = a.out if os.path.isabs(a.out) else os.path.join(REPO, a.out)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump({"results": results, "verdict_abs": v_abs, "verdict_rank": v_rank,
                   "cross_arm_mean_jaccard": cross, "arms": a.arms,
                   "n_arms": len(results), "n_null": a.n_null, "seed": a.seed},
                  open(p, "w"), indent=2)
        print(f"\nwrote {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
