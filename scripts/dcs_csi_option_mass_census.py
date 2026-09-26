#!/usr/bin/env python3
"""Per-arm OPTION-MASS (readout-validity) distribution census.

WHY THIS EXISTS (S-487). The results draft quotes an option-mass distribution per arm -- the
fraction of scored rows below 0.05, the median and the minimum -- and those figures had NO
committed artefact (S-481, S-483, S-486). The axis analyser reads `option_mass` but only to
APPLY a floor; it never reports the distribution, and no other script reads the field at all
(S-472: the shared loader has no option_mass concept). Nothing fits, so this emits it.

⛔ THIS IS A DESCRIPTIVE CENSUS, NOT A TEST. It carries no verdict, no p and no threshold. The
   0.05 it counts against is the number PR-CSI-001 declares as a readout-validity gate and that
   the draft quotes; it is a REPORTING boundary here, not a decision rule.

⚠ THE SELECTION PREDICATE IS COPIED FROM THE ANALYSER, DELIBERATELY AND IDENTICALLY:
  `query_kind == "semantic_one_word" and cell == "C"`, keyed on (domain, family_slot), with a
  duplicate-key refusal and a missing-field refusal. If it ever diverges from
  `installation_with_option_mass` the census stops describing the rows the read used. The
  --assert-keys flag checks the key set against that function at floor 0 rather than trusting it.

⚠ MEDIAN. `statistics.median` -- NOT `om[n//2]`, which is the upper-middle element for even n and
  is the bug S-468 had to correct across eight published figures.
"""
import argparse, json, math, os, statistics, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import importlib.util


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


sub = _load("sub", os.path.join(REPO, "scripts", "dcs_csi_subspace_analyze.py"))
lpm = _load("lpm", os.path.join(REPO, "scripts", "dcs_cont_layerpos_map.py"))
rederive = _load("rederive", os.path.join(REPO, "scripts", "dcs_csi_rederive_patch.py"))


def census(run_dir, boundary):
    """Every scored row's option mass, under the analyser's own selection predicate."""
    oms, seen = [], set()
    with open(os.path.join(run_dir, "results.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("query_kind") != "semantic_one_word" or r.get("cell") != "C":
                continue
            om = r.get("option_mass")
            if om is None:
                raise SystemExit("row %r has no option_mass -- missing is not zero"
                                 % r.get("prompt_id"))
            k = (r["domain"], lpm.family_slot(r["family_id"]))
            if k in seen:
                raise SystemExit("installation key %r binds two rows" % (k,))
            seen.add(k)
            oms.append(float(om))
    if not oms:
        raise SystemExit("VACUOUS: the selection matched ZERO rows in %s. A census over nothing is "
                         "not a census (S-134/S-480)." % run_dir)
    below = [x for x in oms if x < boundary]
    return {
        "n_rows": len(oms),
        "n_below_boundary": len(below),
        "frac_below_boundary": round(len(below) / len(oms), 6),
        "median": round(statistics.median(oms), 8),
        "min": round(min(oms), 8),
        "max": round(max(oms), 8),
        "p05": round(statistics.quantiles(oms, n=20)[0], 8) if len(oms) >= 20 else None,
        "boundary": boundary,
        "median_convention": "statistics.median (true median; NOT om[n//2] -- see S-468)",
    }, set(seen)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag-prefix", required=True)
    ap.add_argument("--arms", required=True, help="comma-separated arm names")
    ap.add_argument("--split", required=True, choices=("train", "validation"))
    ap.add_argument("--boundary", type=float, default=0.05,
                    help="the REPORTING boundary rows are counted against (default 0.05, the value "
                         "PR-CSI-001 declares and the draft quotes). Not a decision rule.")
    ap.add_argument("--allow-short", type=int, default=4,
                    help="preregistered value is 4 (PR-CSI-003-A .population.allow_short); the "
                         "analysers default to 0/3 and NONE of them reads the prereg (R39 N-5)")
    ap.add_argument("--expect-n", type=int, required=True)
    ap.add_argument("--require-slurm-job", default=None,
                    help="comma-separated slurm job ids that disambiguate the tag. ⚠ REQUIRED IN "
                         "PRACTICE: 'csi1_basket_train_BASE' matches TWO complete run dirs (jobs "
                         "897145 and 905990); the second landed AFTER the committed read was "
                         "produced, so a tag that was unique then is ambiguous now (S-487).")
    ap.add_argument("--assert-keys", action="store_true",
                    help="cross-check the key set against the analyser's own "
                         "installation_with_option_mass(run_dir, 0.0)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    arms = [x for x in a.arms.split(",") if x]
    out = {"schema": "dcs_csi_option_mass_census/1",
           "WHAT_THIS_IS": ("a DESCRIPTIVE per-arm option-mass distribution. No verdict, no p, no "
                            "threshold. The boundary is a reporting boundary."),
           "tag_prefix": a.tag_prefix, "split": a.split, "boundary": a.boundary,
           "allow_short": a.allow_short, "expect_n": a.expect_n,
           "require_slurm_job": a.require_slurm_job,
           "argv": sys.argv,           # S-484: an artefact that cannot be reproduced from itself
           "per_arm": {}, "run_dirs": {}}

    for arm in arms:
        # ⚠ KEYWORDS, NOT POSITIONAL: strict_run_dir's 3rd positional is `row_file`, so
        # passing allow_short there would silently look for a file named "4". And row_file
        # must be "results.jsonl" -- the default "gens.jsonl" is NOT what the analyser reads.
        _jobs = [x for x in (a.require_slurm_job or "").split(",") if x] or None
        rd = rederive.strict_run_dir("%s_%s" % (a.tag_prefix, arm), a.expect_n,
                                     row_file="results.jsonl", allow_short=a.allow_short,
                                     require_slurm_jobs=_jobs)
        out["run_dirs"][arm] = os.path.basename(rd)
        st, keys = census(rd, a.boundary)
        if a.assert_keys:
            ref, _ = sub.installation_with_option_mass(rd, 0.0)
            if set(ref) != keys:
                raise SystemExit("%s: census key set differs from the analyser's loader at floor 0 "
                                 "(%d vs %d)" % (arm, len(keys), len(ref)))
            st["key_set_matches_analyser_at_floor_0"] = True
        out["per_arm"][arm] = st
        print("  %-10s n=%-5d below %.2f: %-5d (%.1f%%)  median %.6f  min %.3e"
              % (arm, st["n_rows"], a.boundary, st["n_below_boundary"],
                 100 * st["frac_below_boundary"], st["median"], st["min"]))

    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
    print("wrote %s" % a.out)


if __name__ == "__main__":
    main()
