#!/usr/bin/env python
"""RAH3 Stage-1 selection: freeze ONE configuration from the DEVELOPMENT positive control.

⚠ COMMITTED BEFORE THE DEVELOPMENT ARTIFACTS EXIST. That is the whole point. `RAH2-C-002` and
`RAH2-C-018` were both raised because a maximum over free parameters was quoted as an effect
estimate; the defence is a rule written down before the numbers, applied mechanically afterwards.
The RAH precedent is `scripts/rah_select_config.py`, committed before the rates existed.

THE RULE (`RAH3-PR-001` §2.6), in order:

  1. ELIGIBILITY, all required and non-negotiable:
       names_candidates == []          (requirement 1, exposure-clean)
       hops > 0                        (requirement 3, not a token decoder)
       capture_mode == "offset"        (requirement 4, not a copy test)
     -> `rah3_eligible`, persisted per cell by the producer.
  2. Among eligible cells: positive_control_ok (level > 0.10 AND uplift > 0.10 AND p_c > p_k).
  3. Tie-break, in this order, each fully deterministic:
       (a) larger  p_concept - p_codeword     penalises codeword copying
       (b) larger  uplift_over_unpatched      penalises the receiver's lexical prior
       (c) smaller spread of p_concept across donors   penalises unstable donor-specific behaviour
       (d) lower   receiver depth R
       (e) lower   donor layer L
  4. If NO eligible cell passes (2): the exposure-clean route FAILED on development. `fc_probe_last`
     is then selected SEPARATELY and ONLY to answer "does the transport machinery work off-surface
     at all?", and the outcome routes to P-B -- never to P-A.

⚠ The selected cell's value is NOT an effect estimate. It is `selection_max` over
donor-layer x receiver-depth, an instrument-selection statistic. The estimate is what the FROZEN
cell does on HELD-OUT material, and only that.

Usage:
  python scripts/rah3_select_config.py --dev outputs/boombness/rah_preflight/rah3nc_p_cb_*.json \
                                       --dev outputs/boombness/rah_preflight/rah3nc_q_cb_*.json \
                                       --out reports/RAH3_FROZEN_CONFIG.json
"""
import argparse
import glob
import json
import sys


def one(pattern):
    """FAIL-CLOSED. Never `newest()`: a later run under a matching prefix must not silently
    redefine which artifact a frozen decision was made from."""
    hits = sorted(glob.glob(pattern))
    if len(hits) != 1:
        raise SystemExit("expected exactly 1 artifact for %r, found %d: %r"
                         % (pattern, len(hits), hits))
    return hits[0]


def donor_spread(cell):
    """Spread of p_concept across DONORS at the selected layer. The producer persists per-donor
    values only as mean/max per layer, so the available proxy is (max - mean) at the best layer.
    ⚠ Named as a proxy rather than presented as a standard deviation."""
    best = max(cell["per_layer"], key=lambda x: x["p_concept_mean"])
    return best["p_concept_max"] - best["p_concept_mean"]


def rank_key(cell):
    """The tie-break, as a sort key. Negated where LARGER is better."""
    return (-(cell["pos_ctrl_max"] - cell["p_codeword_at_best"]),   # (a)
            -cell["uplift_over_unpatched"],                          # (b)
            donor_spread(cell),                                      # (c)
            cell["R"],                                               # (d)
            cell["best_donor_L"])                                    # (e)


def select(art):
    """Apply the rule to ONE model's development artifact. Returns (verdict, cell, audit)."""
    grid = art["grid"]
    audit = {"n_cells": len(grid),
             "n_eligible": sum(1 for c in grid if c["rah3_eligible"]),
             "n_eligible_and_passing": 0,
             "zero_hop_forms": sorted({c["form"] for c in grid if c["hops"] == 0}),
             "candidate_naming_forms": sorted({c["form"] for c in grid if c["names_candidates"]}),
             "vacuous_patch_cells": sum(1 for c in grid if not c["patch_live_at_best"])}
    if art["capture_mode"] != "offset":
        return "P-E", None, dict(audit, reason="capture_mode is %r, not 'offset' -- this artifact "
                                               "is a COPY TEST and cannot select anything"
                                               % art["capture_mode"])
    eligible = [c for c in grid if c["rah3_eligible"]]
    passing = [c for c in eligible if c["positive_control_ok"]]
    audit["n_eligible_and_passing"] = len(passing)
    if passing:
        best = sorted(passing, key=rank_key)[0]
        return "ELIGIBLE-PASS", best, dict(audit, reason="exposure-clean multi-hop cell passes")
    # rule 4 -- the reference form, routed to P-B, never P-A
    ref = [c for c in grid if c["form"] == "fc_probe_last" and c["positive_control_ok"]]
    if ref:
        return "P-B", sorted(ref, key=rank_key)[0], dict(
            audit, reason="no exposure-clean multi-hop cell passes; the candidate-PRINTING "
                          "reference does. Transport machinery works; the readout problem is "
                          "UNSOLVED. This can never be P-A.")
    zero = [c for c in grid if c["hops"] == 0 and c["positive_control_ok"]]
    if zero:
        return "P-C", None, dict(audit, reason="only 0-hop/copy forms pass -- non-semantic by "
                                               "definition; H0 gains another confirming instance")
    return "P-D", None, dict(audit, reason="even the candidate-printing positive reference fails; "
                                           "the assay is not validated for this question")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dev", action="append", required=True,
                    help="development artifact glob; repeat once per model")
    ap.add_argument("--out", default="reports/RAH3_FROZEN_CONFIG.json")
    a = ap.parse_args(argv)

    out = {"schema": "RAH3_FROZEN_CONFIG/1",
           "rule": "RAH3-PR-001 section 2.6, committed before the development artifacts existed",
           "warning": "the selected cell's value is selection_max over donor-layer x receiver-"
                      "depth -- an instrument-selection statistic, NOT an effect estimate",
           "models": {}}
    verdicts = []
    for pat in a.dev:
        path = one(pat) if any(ch in pat for ch in "*?[") else pat
        art = json.load(open(path))
        verdict, cell, audit = select(art)
        verdicts.append(verdict)
        print("\n=== %s (%s) -> %s" % (art["model"], path, verdict))
        print("    %s" % audit["reason"])
        print("    cells=%d eligible=%d eligible+passing=%d  0-hop=%r  naming=%r  vacuous=%d"
              % (audit["n_cells"], audit["n_eligible"], audit["n_eligible_and_passing"],
                 audit["zero_hop_forms"], audit["candidate_naming_forms"],
                 audit["vacuous_patch_cells"]))
        frozen = None
        if cell is not None:
            frozen = {"form": cell["form"], "R": cell["R"], "donor_L": cell["best_donor_L"],
                      "capture_mode": art["capture_mode"], "capture_offset": art["capture_offset"],
                      "q_pos": cell["q_pos"], "read_pos": cell["read_pos"], "hops": cell["hops"],
                      "selection_max_p_concept": cell["pos_ctrl_max"],
                      "p_codeword_at_best": cell["p_codeword_at_best"],
                      "uplift_over_unpatched": cell["uplift_over_unpatched"],
                      "option_mass_at_best": cell["patched_option_mass_at_best"],
                      "mass_gate_ok": cell["mass_gate_ok"],
                      "names_candidates": cell["names_candidates"]}
            print("    FROZEN: form=%s R=%d donor_L=%d hops=%d  (selection_max p_concept=%.6g)"
                  % (frozen["form"], frozen["R"], frozen["donor_L"], frozen["hops"],
                     frozen["selection_max_p_concept"]))
        out["models"][art["model"]] = {"artifact": path, "verdict": verdict,
                                       "audit": audit, "frozen": frozen}
    out["verdicts"] = verdicts
    out["held_out_may_run"] = all(v in ("ELIGIBLE-PASS", "P-B") for v in verdicts)
    print("\n%s\nheld_out_may_run = %s" % ("=" * 70, out["held_out_may_run"]))
    if not out["held_out_may_run"]:
        print("⚠ At least one model returned P-C/P-D/P-E. Per RAH3-PR-001 section 2.9 the stopping")
        print("  rule is HARD: do not add forms, search layers, or lower a threshold.")
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print("-> %s" % a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
