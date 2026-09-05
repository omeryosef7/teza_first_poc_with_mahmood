#!/usr/bin/env python3
"""DCS-R-065 / R-066 / B-007: are per-row control-draw key positions recoverable?

B-007 recorded that the draw positions are not persisted. `R-066` scoped that: it is TRUE on
readout arms (`--query-kinds semantic_forced_choice`) and FALSE on all 46 behavioural arms, which
write the positions verbatim into `control_draw[...]["positions"]`.

This checks BOTH routes on a behavioural arm:
  * IDENTITY -- regeneration from (spans, seq_len, seed) reproduces the persisted position set
    EXACTLY, not merely a draw of the same size;
  * MUTATION -- the same check under `seed + 1` must FAIL, otherwise the identity pass is vacuous
    (any seed yields a count-matched draw, so counting alone cannot verify anything).

Usage:  python3 scripts/dcs_verify_draw_regenerable.py [ARM_GLOB] [--n N]
"""
import argparse, glob, importlib.util, json, os, statistics as st, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_score_behavior():
    """Import score_behavior for its draw helpers without running its CLI."""
    path = os.path.join(REPO, "src", "boombness", "score_behavior.py")
    sys.path.insert(0, os.path.dirname(path))
    spec = importlib.util.spec_from_file_location("sb_for_verify", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["sb_for_verify"] = mod
    try:
        spec.loader.exec_module(mod)
    except SystemExit:  # argparse in a __main__ guard we are not using
        pass
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("arm_glob", nargs="?",
                    default="outputs/boombness/score_behavior/dcsp24_d1_*")
    ap.add_argument("--n", type=int, default=200, help="rows to regenerate")
    ap.add_argument("--draw-index", type=int, default=1)
    ap.add_argument("--control-seed", type=int, default=20260901)
    a = ap.parse_args()

    sb = _load_score_behavior()
    done = sorted(d for d in glob.glob(os.path.join(REPO, a.arm_glob))
                  if os.path.isfile(os.path.join(d, "DONE.json")))
    if not done:
        sys.exit(f"no finished arm matches {a.arm_glob}")
    arm = done[-1]
    meta = json.load(open(os.path.join(arm, "metadata.json")))
    seeds = meta.get("knockout_feasibility", {}).get("control_draw_seeds", {})
    print(f"arm: {os.path.basename(arm)}")
    print(f"recorded control_draw_seeds: {seeds}")

    seed = sb.nondemo_draw_seed(a.control_seed, a.draw_index)
    if seeds and seed not in set(seeds.values()):
        print(f"WARN: derived seed {seed} is not among the recorded {sorted(seeds.values())}")

    ok = bad = 0
    exact = mutant_exact = 0
    ratios = []
    for i, line in enumerate(open(os.path.join(arm, "results.jsonl"))):
        if i >= a.n:
            break
        r = json.loads(line)
        lo, hi = r["demo_span_bounds"]
        qlo, qhi = r["query_span_bounds"]
        # the demo keys are the contiguous span itself -- asserted, not assumed
        assert (hi - lo + 1) == r["n_demo_span_positions"], (
            f"row {i}: demo_span_bounds {[lo, hi]} does not span "
            f"n_demo_span_positions={r['n_demo_span_positions']}; the keys are NOT contiguous "
            "and this regeneration route does not apply")
        persisted = r.get("control_draw")
        if not persisted:
            sys.exit("this arm carries no per-row control_draw (readout arm? see R-066) -- "
                     "point this verifier at a --query-kinds behavioral arm")
        prec = list(persisted.values())[0]
        kw = dict(protected=set(range(qlo, qhi + 1)), policy="strict")
        pos, rec = sb.nondemo_control_draw(
            list(range(lo, hi + 1)), r["seq_len"], seed=prec["draw_seed"], **kw)
        ratios.append(rec.get("match_ratio"))
        ok, bad = (ok + 1, bad) if len(pos) == (hi - lo + 1) else (ok, bad + 1)
        exact += (sorted(pos) == sorted(prec["positions"]))
        # MUTATION: a wrong seed must not reproduce the persisted set.
        mpos, _ = sb.nondemo_control_draw(
            list(range(lo, hi + 1)), r["seq_len"], seed=prec["draw_seed"] + 1, **kw)
        mutant_exact += (sorted(mpos) == sorted(prec["positions"]))

    print(f"regenerated {ok + bad} rows from persisted fields alone")
    print(f"  count-matched: {ok}   mismatched: {bad}")
    print(f"  match_ratio: min={min(ratios)} median={st.median(ratios)}")
    n = ok + bad
    print(f"  IDENTITY vs persisted positions : {exact}/{n} exact")
    print(f"  MUTATION seed+1 (must be 0)     : {mutant_exact}/{n} exact")
    verdict = bad == 0 and min(ratios) == 1.0 and exact == n and mutant_exact == 0
    print(f"\nB-007 regenerable (identity-verified): {'PASS' if verdict else 'FAIL'}")
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
