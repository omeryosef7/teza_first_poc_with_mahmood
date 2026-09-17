#!/usr/bin/env python3
"""INDEPENDENT re-derivation of the subspace rank verdict (DCS-CSI-085).

Deliberately shares NO code with dcs_csi_subspace_analyze.py: it does not import lpm, does not use
`family_slot`, and does not read the split manifest. It re-implements each step from the raw
results.jsonl fields by a different route, so that agreement is evidence and disagreement is a bug
in one of the two paths.

THREE DELIBERATE DIVERGENCES from the primary analyser, each chosen to break a shared assumption:
  1. SPLIT was FIRST attempted from each row's own `split` field, to avoid sharing the manifest
     with the primary path. That divergence is INVALID and is recorded as refuted (DCS-CSI-085):
     `results.jsonl` rows carry `split` in {dev, heldout}, which is the BANK's own partition, not
     the ts116m train/validation/test assignment -- 335/335 within a single TRAIN arm. The rows do
     not carry the sprint's split at all, so the manifest is the only source and cannot be diverged
     from. What is done instead: the manifest is re-read here and every TEST domain is asserted
     ABSENT from the loaded keys, which is the property that actually matters.
  2. The (domain, slot) key is rebuilt from `family_id` inline rather than via `family_slot`.
  3. The sign-flip test enumerates exactly when n <= 20 and otherwise samples with its own RNG.

It reports the candidate's rank among the controls, which is the statistic the verdict rests on,
plus the per-family ranks (random-only, shuffled-only) that review R5 showed are the binding ones.
"""
from __future__ import annotations
import argparse, glob, itertools, json, math, os, random, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SB = os.path.join(REPO, "outputs", "boombness", "score_behavior")


def run_dir(tag: str, expect_n: int, allow_short: int, layer=None, jobs=None) -> str:
    """The ONE complete run dir for `tag`. Anchored regex: `KO` must not match `KO_SELF` (S-042).

    DISAMBIGUATION (S-104), implemented here independently of the primary path's version on purpose
    -- this file shares no code with it, so the two must reach the same directory by two routes.
    Since S-103 re-ran the button-TRAIN arms at a second layer under the SAME tags, a tag can resolve
    to two complete directories. `layer` narrows by the layer the run's own config.json says it
    patched (None for the no-rescue arms BASE/KO, where a layer is not a property of the run, so
    those pass through); `jobs` narrows by the SLURM allocation in RUNMETA.json, which is the only
    discriminator the no-rescue arms have. Recency is never a tie-break: if the filters leave more
    than one, this still refuses.
    """
    pat = re.compile(r"^%s_\d{8}_\d{6}_\d+$" % re.escape(tag))
    cands = []
    for d in sorted(glob.glob(os.path.join(SB, tag + "_*"))):
        if not pat.match(os.path.basename(d)):
            continue
        rp = os.path.join(d, "results.jsonl")
        if not os.path.isfile(rp):
            continue
        n = sum(1 for _ in open(rp, encoding="utf-8"))
        if n == expect_n or (n < expect_n and expect_n - n <= allow_short):
            cands.append((d, n))

    # REVIEW R8-B1 / R8-M1, fixed here INDEPENDENTLY of the primary path (this file shares no code
    # with it on purpose, so a fix applied to one and not the other would silently break the
    # two-path guarantee -- which is exactly what R8-M1 found: the primary path asserted the layer
    # against the ROWS while this one asserted nothing, so cross-path agreement could not detect a
    # config/rows disagreement, and S-084 and S-100 were both config/rows disagreements).
    # UNRECORDED is distinct from "no rescue": a config that is missing, or present without the
    # key, cannot verify anything and is refused rather than waved through.
    UNREC = "UNRECORDED"

    def _layer_of(d):
        p = os.path.join(d, "config.json")
        if not os.path.isfile(p):
            return UNREC
        args = json.load(open(p, encoding="utf-8")).get("args", {})
        if "rescue_layer" not in args:
            return UNREC
        v = args["rescue_layer"]
        return None if v is None else int(v)

    def _job_of(d):
        p = os.path.join(d, "RUNMETA.json")
        if not os.path.isfile(p):
            return UNREC
        j = json.load(open(p, encoding="utf-8"))
        if "slurm_job_id" not in j or j.get("slurm_job_id") is None:
            return UNREC
        return str(j["slurm_job_id"])

    def _row_layers(d):
        """The layers the ROWS actually record, and whether any row fired a rescue at all."""
        lays, fired = set(), 0
        with open(os.path.join(d, "results.jsonl"), encoding="utf-8") as fh:
            for line in fh:
                r = json.loads(line)
                if r.get("rescue_layer") is not None:
                    lays.add(int(r["rescue_layer"]))
                if r.get("rescue_liveness"):
                    fired += 1
        return lays, fired

    # UNCONDITIONAL, not len>1-guarded: a lone candidate from the wrong layer or the wrong
    # allocation is precisely the case a >1 guard skips.
    if layer is not None:
        cands = [(d, n) for d, n in cands if _layer_of(d) in (None, int(layer))]
    if jobs is not None:
        want = {str(x) for x in jobs}
        cands = [(d, n) for d, n in cands if _job_of(d) in want]
    if len(cands) != 1:
        cause = ""
        if not cands and (layer is not None or jobs is not None):
            cause = ("  CAUSE: candidates existed but all were rejected by the filters "
                     "(layer=%r, jobs=%r) -- this is NOT a missing run." % (layer, jobs))
        raise SystemExit("REFUSING %s: %d usable run dirs (need exactly 1): %s  layers=%s jobs=%s\n%s"
                         % (tag, len(cands), [os.path.basename(c) for c, _ in cands],
                            [_layer_of(c) for c, _ in cands], [_job_of(c) for c, _ in cands], cause))
    d0 = cands[0][0]
    # SURVIVOR ASSERTIONS on both axes, plus -- new here -- a check against the ROWS, so this path
    # can detect a config that does not describe what the run actually wrote.
    if layer is not None:
        got = _layer_of(d0)
        if got == UNREC:
            raise SystemExit("REFUSING %s: layer %s required but %s records no rescue_layer"
                             % (tag, layer, os.path.basename(d0)))
        if got is not None and got != int(layer):
            raise SystemExit("REFUSING %s: %s patched layer %d, not the required %s"
                             % (tag, os.path.basename(d0), got, layer))
        rl, fired = _row_layers(d0)
        if rl - {int(layer)}:
            raise SystemExit("REFUSING %s: %s has config rescue_layer=%r but its ROWS record "
                             "layer(s) %s -- the config does not describe what the run wrote"
                             % (tag, os.path.basename(d0), got, sorted(rl)))
        if fired and not rl:
            raise SystemExit("REFUSING %s: %s fired a rescue on %d rows but no row records a "
                             "rescue_layer, so the layer cannot be verified"
                             % (tag, os.path.basename(d0), fired))
    if jobs is not None:
        job = _job_of(d0)
        want = sorted({str(x) for x in jobs})
        if job == UNREC:
            raise SystemExit("REFUSING %s: allocation %s required but %s records no slurm_job_id"
                             % (tag, want, os.path.basename(d0)))
        if job not in want:
            raise SystemExit("REFUSING %s: %s came from SLURM job %s, not the required %s"
                             % (tag, os.path.basename(d0), job, want))
    return d0


def arm_values(d: str, split: str, assign: dict) -> dict:
    """(domain, slot) -> installation, for cell-C semantic_one_word rows of `split`."""
    out = {}
    with open(os.path.join(d, "results.jsonl"), encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("query_kind") != "semantic_one_word" or r.get("cell") != "C":
                continue
            if assign.get(r["domain"]) != split:
                continue
            fid = r["family_id"].split("|")        # divergence 2: inline key
            if len(fid) < 3:
                raise SystemExit("family_id %r has too few fields" % r["family_id"])
            k = (r["domain"], "|".join(fid[1:-1]))
            lc, lk = r["logp_concept"], r["logp_codeword"]
            if lc is None or lk is None:
                raise SystemExit("row %s has no logp fields" % r.get("prompt_id"))
            if k in out:
                raise SystemExit("key %r binds two rows in %s" % (k, d))
            out[k] = 1.0 / (1.0 + math.exp(lk - lc))   # two-way softmax, written as a logistic
    return out


def domain_means(vals: dict, keys: set) -> dict:
    by = {}
    for k in keys:
        by.setdefault(k[0], []).append(vals[k])
    return {dm: sum(v) / len(v) for dm, v in by.items()}


def signflip_p(diffs, seed=20260916, n_mc=200000):
    """Two-sided exact sign-flip when feasible, else Monte-Carlo. Returns (p, floor, mode)."""
    d = [x for x in diffs if x != 0.0]
    n = len(d)
    if n == 0:
        return 1.0, 1.0, "degenerate(no informative domains)"
    obs = abs(sum(d) / n)
    if n <= 20:
        hits = tot = 0
        for signs in itertools.product((1, -1), repeat=n):
            tot += 1
            if abs(sum(s * x for s, x in zip(signs, d)) / n) >= obs - 1e-15:
                hits += 1
        return hits / tot, 1.0 / tot, "exact(2^%d)" % n
    rng = random.Random(seed)
    hits = 0
    for _ in range(n_mc):
        if abs(sum(x if rng.random() < 0.5 else -x for x in d) / n) >= obs - 1e-15:
            hits += 1
    return (hits + 1) / (n_mc + 1), 1.0 / (n_mc + 1), "monte-carlo(%d)" % n_mc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag-prefix", required=True)
    ap.add_argument("--split", required=True, choices=("train", "validation"))
    ap.add_argument("--expect-n", type=int, required=True)
    ap.add_argument("--allow-short", type=int, default=3)
    ap.add_argument("--direction", default="sufficiency", choices=("sufficiency", "necessity"),
                    help="S-110 / PR-CSI-003, and re-implemented here rather than shared with the "
                         "primary analyser -- exactly as the run-dir filters were, because a "
                         "SIGN CONVENTION applied in one path and not the other would let the two "
                         "paths 'agree' on a rank that one of them read upside down. "
                         "`sufficiency` (default; what every committed number used): ADD the "
                         "component back under a live knockout, reference arm --ko, stronger = "
                         "MORE POSITIVE. `necessity`: REMOVE it from a clean forward, reference arm "
                         "--base, stronger = MORE NEGATIVE. Reported values keep their natural "
                         "sign in both directions; only the rank comparison and the capability "
                         "gate are oriented.")
    ap.add_argument("--candidate", default="KO_AXIS")
    ap.add_argument("--ko", default="KO")
    ap.add_argument("--base", default="BASE")
    ap.add_argument("--full", default="KO_FULL")
    ap.add_argument("--controls", required=True, help="space- or comma-separated control arm names")
    ap.add_argument("--require-rescue-layer", type=int, default=None,
                    help="S-104: admit only run dirs whose own config.json says they patched this "
                         "layer. Required whenever a tag has been run at more than one layer. "
                         "Arms that ran no rescue (BASE, KO) carry no layer and pass through.")
    ap.add_argument("--require-slurm-job", default=None,
                    help="S-104: comma list of SLURM job ids; admit only run dirs from those "
                         "allocations. The only discriminator the no-rescue arms have.")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    jobs = [x for x in re.split(r"[ ,]+", a.require_slurm_job or "") if x] or None
    ctl_names = [x for x in re.split(r"[ ,]+", a.controls) if x]
    arms = [a.base, a.ko, a.full, a.candidate] + ctl_names
    dirs = {arm: run_dir("%s_%s" % (a.tag_prefix, arm), a.expect_n, a.allow_short,
                         layer=a.require_rescue_layer, jobs=jobs) for arm in arms}
    mf = json.load(open(os.path.join(REPO, "data/boombness_prompts/dcs_ts116_domain_split.json"),
                        encoding="utf-8"))
    assign = mf["assign"]
    vals = {arm: arm_values(d, a.split, assign) for arm, d in dirs.items()}

    keys = set.intersection(*[set(v) for v in vals.values()])
    leaked = sorted({k[0] for k in keys if assign.get(k[0]) == "test"})
    if leaked:
        raise SystemExit("REFUSING: TEST domains present in a %s analysis: %s" % (a.split, leaked))
    if not keys:
        raise SystemExit("REFUSING: the arms share no keys")
    print("[rederive] %d arms, %d keys common to all, %d domains"
          % (len(arms), len(keys), len({k[0] for k in keys})))

    dm = {arm: domain_means(v, keys) for arm, v in vals.items()}
    doms = sorted(dm[a.ko])

    def paired(x, y):
        return [dm[x][d] - dm[y][d] for d in doms]

    def summarise(x, y):
        dd = paired(x, y)
        p, floor, mode = signflip_p(dd)
        return {"point": round(sum(dd) / len(dd), 5),
                "n_domains": len(dd), "n_pos": sum(1 for v in dd if v > 0),
                "n_neg": sum(1 for v in dd if v < 0), "n_tied": sum(1 for v in dd if v == 0),
                "p_two_sided": p, "p_floor": floor, "test_mode": mode,
                "p_at_its_floor": abs(p - floor) < 1e-12}

    # ---- DIRECTION. Resolved once; four consequences, each at one site below.
    #   1. the reference arm of the candidate/control/positive-control contrasts: KO -> BASE
    #   2. the KEY NAMES those values are reported under, so a key never lies about its subtrahend
    #   3. the rank comparison: `>=` (recovered at least as much) -> `<=` (dropped at least as much)
    #   4. the capability gate: the whole-state move must be clearly POSITIVE -> clearly NEGATIVE
    # The manipulation check is NOT a consequence: KO minus a clean forward must be negative either
    # way. NOTHING is multiplied by -1 -- a removal that drops installation is reported NEGATIVE.
    NEC = a.direction == "necessity"
    ref = a.base if NEC else a.ko
    ref_tag = "base" if NEC else "ko"
    gates = {"manipulation_ko_minus_base": summarise(a.ko, a.base),
             "positive_control_full_minus_%s" % ref_tag: summarise(a.full, ref)}
    _pc = gates["positive_control_full_minus_%s" % ref_tag]
    # The independent path has no bootstrap CI, so capability is read off the point estimate and the
    # sign-flip p -- a different route to the same demand as the primary path's CI check, which is
    # the point of this file. A failing gate is CANNOT ANSWER for the direction (plan section 15),
    # never a negative, so the per-family verdicts below are overwritten rather than printed.
    instrument_capable = ((_pc["point"] < 0) if NEC else (_pc["point"] > 0)) \
        and _pc["p_two_sided"] < 0.05
    cand = round(sum(paired(a.candidate, ref)) / len(doms), 5)
    ctls = {c: round(sum(paired(c, ref)) / len(doms), 5) for c in ctl_names}

    def rank_of(subset):
        vs = [ctls[c] for c in subset]
        at_least_as_strong = (sum(1 for v in vs if v <= cand) if NEC
                              else sum(1 for v in vs if v >= cand))
        return 1 + at_least_as_strong, len(vs) + 1, 1.0 / (len(vs) + 1)

    fam = {"pooled": ctl_names,
           "random_only": [c for c in ctl_names if "RAND" in c],
           "shuffled_only": [c for c in ctl_names if "SHUF" in c]}
    ranks = {}
    _cannot = ("CANNOT ANSWER -- the whole-state %s did not move installation %s (point %+.5f, "
               "p=%.4g), so there is no capable instrument for the %s question (plan section 15). "
               "This is NOT a negative result."
               % ("removal" if NEC else "rescue", "DOWN" if NEC else "UP",
                  _pc["point"], _pc["p_two_sided"], a.direction))
    for nm, sub in fam.items():
        if not sub:
            continue
        r, n, fl = rank_of(sub)
        ranks[nm] = {"rank": r, "of": n, "floor": round(fl, 4),
                     "certifiable_at_0.05": fl <= 0.05,
                     "verdict": (_cannot if not instrument_capable else
                                 "PASSES" if (r == 1 and fl <= 0.05) else
                                 "INCONCLUSIVE (floor-limited)" if r == 1 else
                                 "DOES NOT PASS")}

    out = {"schema": "dcs_csi_rederive_subspace/1", "tag_prefix": a.tag_prefix, "split": a.split,
           "n_keys_common": len(keys), "n_domains": len(doms), "gates": gates,
           # P0.4: the artifact says which direction produced it, which arm every contrast
           # subtracts and which way "stronger" points, beside the run-dir filters.
           "direction": a.direction, "reference_arm": ref,
           "stronger_candidate_is": "MORE NEGATIVE" if NEC else "MORE POSITIVE",
           "sign_policy": ("values keep their natural sign; nothing is negated. Only the rank "
                           "comparison and the capability gate are oriented by --direction."),
           "instrument_capable": instrument_capable,
           "identity_gate": ("SKIPPED -- no inert identity control exists for the necessity "
                             "direction: the natural one (donor = clean, live = clean) IS the "
                             "identity and is refused by the arm's own precondition (PR-CSI-003 "
                             "required_gates.no_inert_identity_control_exists, S-110). This path "
                             "never evaluated an identity gate in either direction; recorded so "
                             "its absence here is not mistaken for a pass." if NEC else
                             "not evaluated by this path in either direction (the primary "
                             "analyser owns it); see dcs_csi_subspace_analyze.py"),
           "candidate_minus_%s" % ref_tag: cand, "controls_minus_%s" % ref_tag: ctls,
           "ranks": ranks,
           "run_dirs": {k: os.path.basename(v) for k, v in dirs.items()},
           "require_rescue_layer": a.require_rescue_layer, "require_slurm_job": jobs,
           "resolved_rescue_layers": {
               k: (json.load(open(os.path.join(v, "config.json"), encoding="utf-8"))
                   .get("args", {}).get("rescue_layer")) for k, v in dirs.items()}}
    print(json.dumps({"direction": a.direction, "reference_arm": ref, "gates": gates,
                      "instrument_capable": instrument_capable,
                      "candidate_minus_%s" % ref_tag: cand, "ranks": ranks}, indent=1))
    if a.out:
        json.dump(out, open(a.out, "w"), indent=1)
        print("wrote", os.path.relpath(a.out, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
