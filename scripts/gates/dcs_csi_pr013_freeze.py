"""Emit PR-CSI-013 MECHANICALLY from the PR-CSI-012 census, per the rule frozen in S-248.

WHY THIS FILE EXISTS AND WHY IT IS WRITTEN BEFORE THE CENSUS LANDS. S-248 froze the RULE that picks the
head to replicate on `button`, precisely so that picking it later would not be a judgement. A rule in
prose is still executed by a person. This file executes it instead: it READS the census report, computes
h* by Rule 1, applies Rule 2's go/no-go, and emits (or refuses to emit) the preregistration. Written and
tested while the census is at 11 of 44 arms and reports/DCS_CSI_PR012_CENSUS_validation.json does not
exist, so nothing in it can have been shaped by the numbers it will consume.

⚠ ONE AMBIGUITY IN THE FROZEN RULE, RESOLVED HERE AND DECLARED. Rule 3 says the controls are drawn
"seeded 20261101 + i for i in 0..19, REJECTING and re-seeding any draw already drawn" -- and does NOT say
by how much to re-seed. That is under-specified at exactly the point where a choice could enter. The
reading implemented is the simplest one: A SINGLE SEED COUNTER STARTING AT 20261101, INCREMENTED BY 1 PER
ATTEMPT, accepting a draw iff its head has not already been drawn, until 20 distinct heads are held. The
ambiguity is recorded in the emitted prereg (`control_draw_rule_disambiguation`) and in S-250. It cannot
be tuned to the outcome because this file is frozen before the census exists -- which is the whole reason
it is written now.
"""
import argparse, hashlib, json, os, random, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dcs_csi_pr010_freeze import atomic_write_json      # reuse; never re-implement the writer

N_HEADS = 32
SEED_START = 20261101
N_CONTROLS = 20


def nominate(cen):
    """RULE 1. h* = argmin over ALL 32 heads of E(SINGLE_h); ties by more negative ci95 lower bound,
    then lower index. Returns (h_star, ordered_table)."""
    E, CI = cen["E"], cen["ci95"]
    rows = []
    for h in range(N_HEADS):
        k = "SINGLE_%02d" % h
        if k not in E:
            sys.exit("REFUSING: census has no %s -- it is not a complete 32-head census" % k)
        rows.append((E[k], CI[k][0], h))
    rows.sort()                     # (E asc = most negative first, then lower ci bound, then index)
    return rows[0][2], rows


def go_no_go(cen, h_star):
    """RULE 2. (a) is checked by the census reader itself (it refuses to write on a GATE 0 failure).
    (b) |E(SINGLE_h*)| > |E(HD_BOTK)| AND E(SINGLE_h*)'s ci95 excludes 0."""
    k = "SINGLE_%02d" % h_star
    e, ci = cen["E"][k], cen["ci95"][k]
    botk = cen["E"]["HD_BOTK"]
    bigger = abs(e) > abs(botk)
    excl = (ci[0] < 0 and ci[1] < 0) or (ci[0] > 0 and ci[1] > 0)
    return {"head": h_star, "E": e, "ci95": ci, "E_HD_BOTK": botk,
            "abs_exceeds_HD_BOTK": bool(bigger), "ci95_excludes_0": bool(excl),
            "GO": bool(bigger and excl)}


def draw_controls(h_star):
    """RULE 3, with the disambiguation declared in this module's docstring."""
    pool = sorted(h for h in range(N_HEADS) if h != h_star)
    picked, seeds, s = [], [], SEED_START
    while len(picked) < N_CONTROLS:
        h = random.Random(s).sample(pool, 1)[0]
        if h not in picked:
            picked.append(h); seeds.append(s)
        s += 1
        if s - SEED_START > 100000:
            sys.exit("REFUSING: control draw failed to reach %d distinct heads" % N_CONTROLS)
    return picked, seeds


def build(cen_path, cen, h_star, gate, controls, seeds, src_prereg):
    hs = {"BT_SINGLE": [h_star]}
    for i, h in enumerate(controls):
        hs["BT_CTRL_%02d" % i] = [h]
    return {
        "id": "PR-CSI-013",
        "title": "Does head %d's single-head effect, selected on BASKET by a rule frozen before the "
                 "census, replicate on the BUTTON codeword at rank 1 of 21?" % h_star,
        "frozen_utc_date": "2026-09-22",
        "EMITTED_MECHANICALLY_BY": "scripts/gates/dcs_csi_pr013_freeze.py, per the rule frozen in "
                                   "runargs/dcs_csi_pr013_nomination_rule.txt (S-248) BEFORE the "
                                   "census existed. No head was chosen by hand.",
        "nomination_rule": "runargs/dcs_csi_pr013_nomination_rule.txt",
        "nomination_rule_md5": hashlib.md5(
            open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                os.path.abspath(__file__)))), "runargs",
                "dcs_csi_pr013_nomination_rule.txt"), "rb").read()).hexdigest(),
        "census_source": cen_path,
        "census_md5": hashlib.md5(open(cen_path, "rb").read()).hexdigest(),
        "census_prereg_id": cen.get("prereg_id"),
        "h_star": h_star,
        "RULE_2_GATE": gate,
        "codeword": "button",
        "codeword_justification":
            "S-248 measured 84 existing button VALIDATION runs at the semantic endpoint, ALL at 230 "
            "rows, 82 of them with demo_all:attn_knockout:6-14:1.0 and target_surface_row_only -- and "
            "NONE has ever used --knockout-heads. The endpoint, band, scope and population are "
            "established on button and NO head-restricted button arm exists that could have informed "
            "the choice of h*. A head chosen on basket and tested on button is a replication across "
            "codewords, not a reused split.",
        "endpoint": "y_install; concept-free semantic_one_word; cell C; n_examples 4",
        "statistical_unit": "DOMAIN (never the row); button is NEVER pooled with basket",
        "intervention": {"intervene": "demo_all:attn_knockout:6-14:1.0",
                         "knockout_scope": "target_surface_row_only", "band": "6-14"},
        "split": "validation",
        "head_sets": hs,
        "control_prefix": "BT_CTRL_",
        "n_controls": N_CONTROLS,
        "n_arms_per_split": 2 + 1 + N_CONTROLS,
        "arms": {"BT_BASE": "no --intervene; the clean reference",
                 "BT_KO": "--knockout-heads omitted = all 32 band heads; the denominator",
                 "BT_SINGLE": "--knockout-heads %d; the nominated head" % h_star,
                 "BT_CTRL_ii": "--knockout-heads <one head>; 20 DISTINCT single heads from the 31 "
                               "heads other than h*"},
        "control_pool_note": "the 31 heads OTHER than h*. A control equal to h* would BE the candidate.",
        "control_draw_rule": "single seed counter from %d, +1 per attempt, accept iff the head is not "
                             "already drawn, until %d distinct heads" % (SEED_START, N_CONTROLS),
        "control_draw_rule_disambiguation":
            "runargs/dcs_csi_pr013_nomination_rule.txt Rule 3 says 'rejecting and RE-SEEDING any draw "
            "already drawn' without saying by how much. The reading implemented is a single counter "
            "incremented by 1 per attempt. Declared because an under-specified rule is a place a "
            "choice could enter; it could not enter HERE because this file was frozen before the "
            "census existed.",
        "control_seeds_used": seeds,
        "attainable_floor": {"n_controls": N_CONTROLS, "floor_p": 1.0 / (N_CONTROLS + 1),
                             "note": "rank 1 of 21 gives p = the floor = 0.047619 and is the ONLY "
                                     "certifying outcome at alpha = 0.05; rank 2 gives 0.095238 and "
                                     "does not clear it. The p is reported WITH its floor, always."},
        "population": {"validation_domains": 23, "validation_expect_n": 230,
                       "test_domains": 3, "test_note": "TEST is NEVER touched"},
        "DOSE_IDENTITY_IS_BLIND_HERE":
            "BT_SINGLE and every BT_CTRL_* is a ONE-head arm and records 2016 prefill edits -- exactly "
            "what the all-32 BT_KO records (S-246). The dose check cannot distinguish them. Arm "
            "identity MUST be asserted from each run's own knockout_heads against head_sets.",
        "WHAT_THIS_CANNOT_DO": [
            "revise D32, D33 or the PR-CSI-012 census -- it tests ONE head on ONE other codeword",
            "license 'head %d is the writer'. A PASS licenses only: head %d, selected on basket by a "
            "preregistered rule, is rank 1 of 21 against 20 arbitrary single heads on button"
            % (h_star, h_star),
            "say anything about the other 31 heads on button",
            "retract the census on a FAILURE -- the census is a basket measurement and D32/D33 are "
            "set-level results"
        ],
        "VOID_CONDITIONS": [
            "1. compared arms not all on one GPU architecture",
            "2. attn_implementation not eager on any arm",
            "3. any arm's recorded knockout_heads not equal to its head_sets entry",
            "4. src/boombness/score_behavior.py edited while any arm of this family is running",
            "5. a TEST domain appearing in any arm",
            "6. the read amended after any number from this family has been seen"
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", default="reports/DCS_CSI_PR012_CENSUS_validation.json")
    ap.add_argument("--src-prereg", default="configs/dcs_csi_pr012_head_census_basket.json")
    ap.add_argument("--out", default="configs/dcs_csi_pr013_button_head_replication.json")
    ap.add_argument("--check", action="store_true", help="compute and print; write nothing")
    a = ap.parse_args()

    if not os.path.exists(a.census):
        sys.exit("REFUSING: census %r does not exist. PR-CSI-013 is emitted FROM the census and "
                 "cannot be written before it." % a.census)
    cen = json.load(open(a.census))
    if not cen.get("NO_RANK_TEST"):
        sys.exit("REFUSING: %r is not a census report" % a.census)

    h_star, table = nominate(cen)
    gate = go_no_go(cen, h_star)
    print("[pr013] RULE 1  h* = %d   E = %+.6f  ci95 [%+.6f, %+.6f]"
          % (h_star, gate["E"], gate["ci95"][0], gate["ci95"][1]))
    print("[pr013]         next three: %s"
          % ["head %d E %+.6f" % (h, e) for e, _, h in table[1:4]])
    print("[pr013] RULE 2  |E| %.6f vs |E(HD_BOTK)| %.6f -> exceeds: %s | ci95 excludes 0: %s"
          % (abs(gate["E"]), abs(gate["E_HD_BOTK"]), gate["abs_exceeds_HD_BOTK"],
             gate["ci95_excludes_0"]))
    if not gate["GO"]:
        print("[pr013] RULE 2 GATE: NO-GO.")
        sys.exit("STOPPING, AS PREREGISTERED: Rule 2(b) fails, so nothing replicates and PR-CSI-013 "
                 "MUST NOT LAUNCH. This is a preregistered outcome (see the PR-CSI-012 read), NOT a "
                 "failure of the pipeline. No preregistration is written.")
    print("[pr013] RULE 2 GATE: GO.")
    controls, seeds = draw_controls(h_star)
    print("[pr013] RULE 3  20 distinct controls: %s" % controls)
    print("[pr013]         seeds consumed: %d..%d (%d attempts)"
          % (seeds[0], seeds[-1], seeds[-1] - seeds[0] + 1))
    if h_star in controls:
        sys.exit("REFUSING: h* entered its own control family")
    if len(set(controls)) != N_CONTROLS:
        sys.exit("REFUSING: controls are not distinct")
    pr = build(a.census, cen, h_star, gate, controls, seeds, a.src_prereg)
    if a.check:
        print("[pr013] --check: %d arms, floor %.6f, nothing written"
              % (pr["n_arms_per_split"], pr["attainable_floor"]["floor_p"]))
        return
    n = atomic_write_json(a.out, pr)
    print("[pr013] wrote+verified %s (%d bytes)" % (a.out, n))
    print("[pr013] md5 = %s" % hashlib.md5(open(a.out, "rb").read()).hexdigest())


if __name__ == "__main__":
    main()
