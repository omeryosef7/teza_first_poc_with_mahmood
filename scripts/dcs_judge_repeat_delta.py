#!/usr/bin/env python
"""dcs_judge_repeat_delta.py -- `DCS-PR-020`/`B-014`: how many judge labels move when the SAME arm
is judged twice at byte-identical settings?

WRITTEN AND COMMITTED BEFORE THE REPEAT PASS RAN, and before `PR-014` had any attack contrast.

WHAT IT MEASURES, AND WHAT IT DOES NOT. Same arm, same configuration, SECOND INVOCATION. That is an
UPPER BOUND on call-level nondeterminism: it necessarily contains whatever cross-invocation drift
exists, so it CANNOT isolate within-call variation and must never be called "the judge's intrinsic
noise" (`PR-020`). It is the right comparator for `PR-014` anyway -- `PR-014`'s eight arms went
through ONE invocation, so a bound that is conservative for that comparison is exactly what the
caveat needs.

THREE ENDPOINTS, all declared in `PR-020`:
  (a) `malicious_at_0.5` labels that flip, of 380;
  (b) the same as a paired count, with direction (0->1 vs 1->0);
  (c) whether `refused` flips AT ALL -- `C-023` measured its band as 0, and this is a direct test of
      that claim on new data. `PR-014`'s entire bounding construction counts induced refusals, so a
      single flip here is consequential and the artifact says so.

It also verifies the two passes really are the same rows: identical `prompt_id` sets AND identical
`completion_sha256_16` on every row. A "repeat" over different completions would measure generation,
not judging.

Stdlib only.
"""
from __future__ import annotations
import argparse, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = "DCS_JUDGE_REPEAT/1"


def load(d: str) -> dict:
    if not os.path.isfile(os.path.join(d, "DONE.json")):
        sys.exit(f"REFUSING: {d} carries no DONE.json")
    rows = {}
    for line in open(os.path.join(d, "results.jsonl")):
        r = json.loads(line)
        rows[r["prompt_id"]] = r
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pass1", required=True)
    ap.add_argument("--pass2", required=True)
    ap.add_argument("--expect-rows", type=int, default=380)
    ap.add_argument("--tag", default="dcs_judge_repeat")
    ap.add_argument("--out", default=os.path.join(ROOT, "outputs/boombness/dcs_analysis"))
    a = ap.parse_args()

    p1, p2 = load(a.pass1), load(a.pass2)
    if set(p1) != set(p2):
        sys.exit(f"REFUSING: different prompt_id sets ({len(set(p1) ^ set(p2))} symmetric diff)")
    if a.expect_rows and len(p1) != a.expect_rows:
        sys.exit(f"REFUSING: {len(p1)} rows, expected {a.expect_rows}")
    bad_sha = [k for k in p1
               if p1[k].get("completion_sha256_16") != p2[k].get("completion_sha256_16")]
    if bad_sha:
        sys.exit(f"REFUSING: {len(bad_sha)} rows differ in completion_sha256_16 -- these are not "
                 "the same completions, so this would measure GENERATION, not judging")

    def flips(field):
        up = [k for k in p1 if not p1[k].get(field) and p2[k].get(field)]
        dn = [k for k in p1 if p1[k].get(field) and not p2[k].get(field)]
        return {"n_flipped": len(up) + len(dn), "n_0_to_1": len(up), "n_1_to_0": len(dn),
                "pass1_positives": sum(1 for k in p1 if p1[k].get(field)),
                "pass2_positives": sum(1 for k in p2 if p2[k].get(field)),
                "net_change": sum(1 for k in p2 if p2[k].get(field))
                              - sum(1 for k in p1 if p1[k].get(field))}

    out = {"schema": SCHEMA, "n_rows": len(p1),
           "pass1": a.pass1, "pass2": a.pass2,
           "completions_identical": True,
           "judge_models": sorted({r.get("judge_model_used") for r in p1.values()}
                                  | {r.get("judge_model_used") for r in p2.values()}),
           "malicious_at_0.5": flips("malicious_at_0.5"),
           "refused": flips("refused"),
           "MEASURES": ("same arm, same configuration, SECOND INVOCATION => an UPPER BOUND on "
                        "call-level nondeterminism. It contains cross-invocation drift and cannot "
                        "isolate within-call variation (PR-020). Never 'the judge's intrinsic "
                        "noise'.")}
    r = out["refused"]
    if r["n_flipped"]:
        out["C023_STATUS"] = ("RETRACTS C-023's 'measured judge band on refused is 0': "
                              f"{r['n_flipped']} of {len(p1)} refusal labels moved. PR-014's "
                              "bounding construction counts induced refusals and must be "
                              "re-examined.")
    else:
        out["C023_STATUS"] = f"C-023 holds on new data: 0 of {len(p1)} refusal labels moved."

    os.makedirs(a.out, exist_ok=True)
    dst = os.path.join(a.out, f"{a.tag}.json")
    json.dump(out, open(dst, "w"), indent=2, sort_keys=True)
    m = out["malicious_at_0.5"]
    print(f"rows={len(p1)}  completions byte-identical on all rows")
    print(f"malicious_at_0.5: {m['n_flipped']} flipped "
          f"({m['n_0_to_1']} up, {m['n_1_to_0']} down)  "
          f"{m['pass1_positives']} -> {m['pass2_positives']}  net {m['net_change']:+d}")
    print(f"refused         : {r['n_flipped']} flipped  "
          f"{r['pass1_positives']} -> {r['pass2_positives']}")
    print(out["C023_STATUS"])
    print(f"-> {dst}")


if __name__ == "__main__":
    main()
