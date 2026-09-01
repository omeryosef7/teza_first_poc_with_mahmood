#!/usr/bin/env python
"""tsc_judge_robustness.py -- `TSC-PR-002`'s analysis. Stdlib only; scalar judge columns only.

WHAT IT MEASURES AND WHY THE USUAL STATEMENT IS THE WRONG ONE.
`CDS-C-018` found that the SAME 380 completions, judged twice, give 148 and 159 attacks: 380/380
`completion_sha256_16` identical, both pinned, both all-`ok`, and 51 rows (13.4 %) flip
`malicious_at_0.5`. So "the judge agrees" is not available and is not the claim to defend. The
defensible claim is that **the intervention effect and its qualitative conclusion are invariant
across independent judging passes despite that row-level variability**, and this file computes both
halves: the noise, and the conclusion under each pass separately.

DENOMINATOR NOTE. `judge_boombness` keeps an in-process cache keyed on
`(pinned_model, goal_sha16, completion_sha16)`, so rows sharing a completion hash are scored once
and copied WITHIN a pass. Those rows are perfectly correlated inside a pass and independent across
passes, so a per-pass flip rate is reported over the DISTINCT-COMPLETION denominator as well as the
raw row denominator, and the two are printed side by side rather than one silently standing for the
other.

Never opens `gens.jsonl`. Reads only: prompt_id, domain, n_examples, malicious_at_0.5, refused,
completion_sha256_16, judge_model_used, judge_status.
"""
from __future__ import annotations
import argparse, collections, itertools, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = "TSC_JUDGE_ROBUSTNESS/1"
PIN = "openai/gpt-4o-mini"
KEYS = ("prompt_id", "domain", "n_examples", "malicious_at_0.5", "refused",
        "completion_sha256_16", "judge_model_used", "judge_status")


def load(judge_dir, dose):
    """Scalar columns of one judge dir, keyed by prompt_id, restricted to one dose."""
    out = {}
    raw = 0
    with open(os.path.join(judge_dir, "results.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            raw += 1
            if dose is not None and r.get("n_examples") != dose:
                continue
            if r["prompt_id"] in out:
                raise SystemExit(f"REFUSING: duplicate prompt_id {r['prompt_id']} in {judge_dir}")
            out[r["prompt_id"]] = {k: r.get(k) for k in KEYS}
    return out, raw


def as_bool(v):
    """`malicious_at_0.5` is stored as int 0/1 in some dirs and bool in others.

    ⚠ An `is True` test silently returns 0 for every int-valued dir -- an audit of these very
    artifacts hit exactly that. Normalise once, here, and refuse anything that is neither.
    """
    if isinstance(v, bool):
        return v
    if isinstance(v, int) and v in (0, 1):
        return bool(v)
    raise SystemExit(f"REFUSING: non-boolean outcome value {v!r}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pass", dest="passes", action="append", required=True,
                    metavar="LABEL=JUDGE_DIR_GLOB_PREFIX",
                    help="repeatable; LABEL=<dir> for ONE arm, or use --arm-pass for a whole pass")
    ap.add_argument("--dose", type=int, default=4)
    ap.add_argument("--outcome", default="malicious_at_0.5", choices=["malicious_at_0.5", "refused"])
    ap.add_argument("--tag", default="tsc_judge_robustness")
    ap.add_argument("--out", default=os.path.join(ROOT, "outputs/boombness/cds_analysis"))
    a = ap.parse_args()

    loaded, raws = {}, {}
    for spec in a.passes:
        label, d = spec.split("=", 1)
        loaded[label], raws[label] = load(d, a.dose)
    labels = list(loaded)
    if len(labels) < 2:
        raise SystemExit("REFUSING: judge robustness needs >= 2 passes; a single pass measures nothing.")

    # ---- the passes must be judging THE SAME completions, or the flip rate is meaningless
    ref = labels[0]
    ids = set(loaded[ref])
    for k in labels[1:]:
        if set(loaded[k]) != ids:
            raise SystemExit(f"REFUSING: {k} and {ref} cover different prompt_id sets "
                             f"({len(set(loaded[k]) ^ ids)} symmetric difference).")
    hash_mismatch = {}
    for k in labels[1:]:
        n = sum(1 for p in ids
                if loaded[k][p]["completion_sha256_16"] != loaded[ref][p]["completion_sha256_16"])
        hash_mismatch[k] = n
        if n:
            raise SystemExit(f"REFUSING: {k} judged {n} completions that differ by "
                             f"completion_sha256_16 from {ref}. These are not re-judgements.")
    for k in labels:
        bad = sorted({loaded[k][p]["judge_model_used"] for p in ids} - {PIN})
        if bad:
            raise SystemExit(f"REFUSING: {k} used unpinned judge model(s) {bad}")
        bad = sorted({str(loaded[k][p]["judge_status"]) for p in ids} - {"ok"})
        if bad:
            raise SystemExit(f"REFUSING: {k} has judge_status {bad}")

    n_rows = len(ids)
    n_distinct = len({loaded[ref][p]["completion_sha256_16"] for p in ids})

    counts = {k: sum(as_bool(loaded[k][p][a.outcome]) for p in ids) for k in labels}
    pairwise = {}
    for x, y in itertools.combinations(labels, 2):
        flips = [p for p in ids if as_bool(loaded[x][p][a.outcome]) != as_bool(loaded[y][p][a.outcome])]
        # direction, because 31-up/20-down and 51-up are very different instruments
        up = sum(1 for p in flips if as_bool(loaded[y][p][a.outcome]))
        # distinct-completion denominator: a flip on a shared hash is ONE independent event
        distinct_flip_hashes = {loaded[ref][p]["completion_sha256_16"] for p in flips}
        pairwise[f"{x}|{y}"] = {
            "n_flips": len(flips), "flip_rate_rows": len(flips) / n_rows,
            "flip_rate_distinct_completions": len(distinct_flip_hashes) / n_distinct,
            "flips_to_true": up, "flips_to_false": len(flips) - up,
            "agreement_rows": 1 - len(flips) / n_rows,
            "count_delta": counts[y] - counts[x],
        }

    # ---- majority vote across the passes, and how much it differs from any single pass
    maj = {p: sum(as_bool(loaded[k][p][a.outcome]) for k in labels) * 2 > len(labels) for p in ids}
    maj_count = sum(maj.values())
    unanimous = sum(1 for p in ids
                    if len({as_bool(loaded[k][p][a.outcome]) for k in labels}) == 1)

    band = max(counts.values()) - min(counts.values())
    doc = {
        "schema": SCHEMA, "outcome": a.outcome, "dose": a.dose,
        "n_rows": n_rows, "n_distinct_completions": n_distinct,
        "passes": {k: {"judge_dir": d.split("=", 1)[1], "n_raw_rows": raws[k], "count": counts[k],
                       "rate": counts[k] / n_rows}
                   for k, d in zip(labels, a.passes)},
        "pairwise": pairwise,
        "majority_vote": {"count": maj_count, "rate": maj_count / n_rows,
                          "n_unanimous": unanimous, "frac_unanimous": unanimous / n_rows},
        "REJUDGE_BAND_rows": band,
        "REJUDGE_BAND_note": ("max-min count across independent passes on BYTE-IDENTICAL "
                              "completions. Any arm-to-arm difference of this magnitude or smaller "
                              "is WITHIN JUDGE RE-RUN VARIANCE and is NOT an informative negative."),
        "completion_hash_mismatches": hash_mismatch,
    }
    os.makedirs(a.out, exist_ok=True)
    p = os.path.join(a.out, f"{a.tag}.json")
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)

    print(f"[tsc] outcome={a.outcome} n_rows={n_rows} distinct_completions={n_distinct}")
    for k in labels:
        print(f"    {k:14s} count={counts[k]:4d}  rate={counts[k]/n_rows:.4f}")
    for k, v in pairwise.items():
        print(f"    {k:30s} flips={v['n_flips']:3d} ({v['flip_rate_rows']:.4f} rows / "
              f"{v['flip_rate_distinct_completions']:.4f} distinct)  "
              f"+{v['flips_to_true']}/-{v['flips_to_false']}  delta={v['count_delta']:+d}")
    print(f"    majority={maj_count} unanimous={unanimous}/{n_rows} "
          f"({unanimous/n_rows:.4f})   RE-JUDGE BAND = {band} rows")
    print(f"[tsc] -> {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
