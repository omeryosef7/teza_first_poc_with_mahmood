"""WITHIN-FAMILY bridge: does the family whose ATTACK dies also lose its BINDING?

R-15 compared 48 probe rows against 96 behavioural rows in aggregate.  That is a between-population
comparison and it is the weaker design: it can say *"binding survived on average while behaviour
collapsed on average"*, but it cannot say whether the **same families** carry both.

The bank makes the stronger design free.  Every probe row joins **1:1** to a behavioural row on
``(family_id minus its trailing query_kind, condition)`` with a **byte-identical demo block**
(verified: 1584/1584, 0 orphans), and the 48 probe families are a strict **subset** of the 96
behavioural ones.  So for each of those 48 families we hold, under the *same* arm and the *same*
demonstrations:

* whether the behavioural row was jailbroken (StrongREJECT >= threshold), and
* whether the probe row recovered the mapped concept (``p_concept > p_codeword``).

That turns the dissociation into a **2x2 per family**, and lets the question be asked properly:

    among the families whose ATTACK the intervention killed, what happened to the BINDING?

If the mechanism ran *through* the mapping, the families that lost the attack should be the families
that lost the mapping.  If binding is intact exactly where behaviour died, the two are separable
**within the same demonstrations**, not merely on average.

Scalar fields only; no prompt or completion text is read.

Usage
-----
    python src/boombness/binding_behaviour_bridge.py \
        --beh-baseline outputs/boombness/judge/p1k_A_... \
        --beh-arm      demoproc=outputs/boombness/judge/p1k_demoproc_... \
        --probe-baseline outputs/boombness/score_behavior/p2A_... \
        --probe-arm    demoproc=outputs/boombness/score_behavior/p2_demo_processing_only_... \
        --bank data/boombness_prompts/boombness_prompt_bank.jsonl --tag bridge
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402


def family_stem(row):
    """`family_id` minus its trailing query_kind field -- the identity shared by a family's rows."""
    fid = str(row.get("family_id") or "")
    stem, _, last = fid.rpartition("|")
    if not stem or last != row.get("query_kind"):
        raise SystemExit(f"[bridge] REFUSING: family_id {fid!r} does not end in its query_kind "
                         f"{row.get('query_kind')!r}; the 1:1 join depends on exactly that.")
    return stem


def load_rows(path):
    with open(path) as fh:
        return [json.loads(l) for l in fh]


def binom_two_sided(k, n):
    if n == 0:
        return 1.0
    k = min(k, n - k)
    return min(1.0, 2.0 * sum(math.comb(n, i) for i in range(k + 1)) / (2.0 ** n))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", required=True)
    ap.add_argument("--beh-baseline", required=True)
    ap.add_argument("--beh-arm", action="append", default=[], metavar="LABEL=JUDGEDIR")
    ap.add_argument("--probe-baseline", required=True)
    ap.add_argument("--probe-arm", action="append", default=[], metavar="LABEL=RUNDIR")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--tag", default="bridge")
    ap.add_argument("--experiment", default="binding_behaviour_bridge")
    args = ap.parse_args()

    run = common.RunDir(args.experiment, args=args, tag=args.tag)
    ledger = common.FailureLedger()
    thr = args.threshold

    # prompt_id -> family stem, from the bank itself
    fam = {}
    for r in load_rows(args.bank):
        try:
            fam[r["prompt_id"]] = family_stem(r)
        except SystemExit:
            raise

    def beh(d):
        return {r["prompt_id"]: (1 if (r.get("strongreject_score") or 0) >= thr else 0)
                for r in load_rows(os.path.join(d, "results.jsonl"))}

    def probe(d):
        return {r["prompt_id"]: (1 if r["p_concept"] > r["p_codeword"] else 0)
                for r in load_rows(os.path.join(d, "results.jsonl"))}

    b0, p0 = beh(args.beh_baseline), probe(args.probe_baseline)

    # *** THE BANK MUST BE THE POPULATION THE RUNS CAME FROM ***
    # `fam` is keyed by prompt_id, and the join below silently skips any row whose id the bank does
    # not know. Measured 2026-08-26: the carrot bank's 2736 ids are a strict SUBSET of the d10
    # bank's 4560, so pointing this script at the carrot bank while handing it d10 judge dirs keeps
    # 96 of 160 rows and prints a complete-looking answer with different numbers. Nothing in the
    # original version noticed. A bank argument that silently subsets the population is the same
    # defect class as every other silent-subset bug this sprint has paid for, so it is now refused.
    for _name, _ids in (("beh_baseline", b0), ("probe_baseline", p0)):
        _missing = [q for q in _ids if q not in fam]
        if _missing:
            raise SystemExit(
                f"[bridge] REFUSING: {len(_missing)} of {len(_ids)} {_name} rows are not in "
                f"--bank {args.bank!r} (first: {_missing[:3]}). The bank must be the one those runs "
                f"were generated from; joining against a different bank silently drops rows and "
                f"still prints a plausible result.")
    beh_arms = {s.split("=", 1)[0]: beh(s.split("=", 1)[1]) for s in args.beh_arm}
    probe_arms = {s.split("=", 1)[0]: probe(s.split("=", 1)[1]) for s in args.probe_arm}

    out_arms = {}
    for lab in sorted(set(beh_arms) & set(probe_arms)):
        b1, p1 = beh_arms[lab], probe_arms[lab]
        # family -> (behavioural pid, probe pid), keeping only families present on BOTH sides
        by_fam = collections.defaultdict(dict)
        for pid in b0:
            if pid in b1 and pid in fam:
                by_fam[fam[pid]]["beh"] = pid
        for pid in p0:
            if pid in p1 and pid in fam:
                by_fam[fam[pid]]["probe"] = pid
        fams = sorted(f for f, v in by_fam.items() if "beh" in v and "probe" in v)
        for f, v in by_fam.items():
            if not ("beh" in v and "probe" in v):
                ledger.fail("family_missing_one_side", f)
        cell = collections.Counter()
        attack_killed, binding_lost_given_killed = [], []
        for f in fams:
            ledger.ok()
            bp, pp = by_fam[f]["beh"], by_fam[f]["probe"]
            killed = (b0[bp] == 1 and b1[bp] == 0)          # was jailbroken, now not
            lost = (p0[pp] == 1 and p1[pp] == 0)            # bound the concept, now not
            cell[(("attack_killed" if killed else "attack_not_killed"),
                  ("binding_lost" if lost else "binding_kept"))] += 1
            if killed:
                attack_killed.append(f)
                binding_lost_given_killed.append(lost)
        n_killed = len(attack_killed)
        n_lost_given_killed = sum(binding_lost_given_killed)
        # base rate of binding loss among families whose attack was NOT killed
        not_killed = [f for f in fams if f not in set(attack_killed)]
        n_lost_given_not = sum(1 for f in not_killed
                               if p0[by_fam[f]["probe"]] == 1 and probe_arms[lab][by_fam[f]["probe"]] == 0)
        out_arms[lab] = {
            "n_families": len(fams),
            "contingency": {f"{a}|{b}": n for (a, b), n in sorted(cell.items())},
            "n_attack_killed": n_killed,
            "n_binding_lost_given_attack_killed": n_lost_given_killed,
            "frac_binding_lost_given_attack_killed": (n_lost_given_killed / n_killed) if n_killed else None,
            "n_binding_lost_given_attack_not_killed": n_lost_given_not,
            "frac_binding_lost_given_attack_not_killed": (n_lost_given_not / len(not_killed)) if not_killed else None,
            "binomial_p_binding_lost_among_killed": binom_two_sided(n_lost_given_killed, n_killed),
            "VERDICT": (
                "If the mechanism ran THROUGH the mapping, families whose attack was killed should be "
                "the families that lost the binding. Compare frac_binding_lost_given_attack_killed "
                "against frac_binding_lost_given_attack_not_killed; equality means the two are "
                "independent WITHIN the same demonstrations."),
        }

    out = {"schema": "BINDING_BEHAVIOUR_BRIDGE/1", "threshold": thr,
           "design": ("WITHIN-FAMILY. Each family contributes one behavioural row and one probe row "
                      "sharing a byte-identical demonstration block, under the same arm."),
           "per_arm": out_arms}
    path = os.path.join(run.path, "binding_behaviour_bridge.json")
    with open(path, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    run.finish(summary={"n_arms": len(out_arms)}, ledger=ledger)
    print(f"[bridge] wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
