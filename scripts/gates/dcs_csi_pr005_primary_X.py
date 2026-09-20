"""PR-CSI-005 PRIMARY statistic X -- the exceedance count among the 36 BLIND, never-read controls.

The pooled rank R47 is a MEASUREMENT, not a test: seven of button's ten stage-1 controls already beat
the candidate before a single new arm ran, so R47 >= 8 deterministically and rank <= 2 is unreachable
(sprint entry S-131). X is the only unread quantity and the only one with a reachable rejection region.

Thresholds fixed in configs/dcs_csi_pr005_button_L18_family.json BEFORE the data:
  X <= 12  (P <= 2.297e-02)  -> WITHDRAW the dissociation analysis section 4.2 and its sentence
                                "extending button's family cannot manufacture a pass"
  X <=  4  (P <= 2.055e-04)  -> resurrect C3 (unequal families); a clean 46-draw family becomes mandatory
  X  =  0                    -> must be reported as X = 0, NEVER as "rank 8, unchanged"
Predictive: X ~ BetaBinom(36, 7.5, 3.5), E[X] = 24.5455, sd 5.5307, 95% predictive [13, 34].
"""
import json, os, sys

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
REP = os.path.join(REPO, "reports/DCS_CSI_SUBSPACE_button_train_L18_n46.json")

STAGE1 = set(["KO_SHUF%d" % i for i in range(0, 4)] + ["KO_RAND%d" % i for i in range(0, 6)])
NEW = set(["KO_SHUF%d" % i for i in range(4, 24)] + ["KO_RAND%d" % i for i in range(6, 22)])

# THE REPORT THIS SCRIPT IS ABOUT, pinned by its CONTENT (REVIEW R10 MAJOR-1) ---------------------
# Aimed at either PR-CSI-006 swap report, the previous version satisfied EVERY assert it had --
# the swap reports carry the identical 46 control names -- and printed "X = 2" / "X = 9" and
# "VERDICT: a falsification threshold FIRED" (mutations P2/P3). Nothing checked the codeword, the
# split, the run set, or WHICH ARM was the candidate. These four facts are what make a report the
# PR-CSI-005 read rather than some other read that happens to share a control family.
EXPECT_CODEWORD, EXPECT_SPLIT, EXPECT_LAYER = "button", "train", 18
EXPECT_JOBS = ["902004", "902005", "912835", "912836", "912837"]   # I1, I2, K + the two stage-1
EXPECT_CANDIDATE_ARM = "KO_AXIS"

d = json.load(open(REP))
crd = d["control_recovery_distribution"]
cand = crd["candidate"]
ctrl = crd["controls"]

print("report      : %s" % os.path.basename(REP))
print("n_domains   : %s   n_keys_common: %s" % (d["n_domains"], d["n_keys_common"]))
print("candidate   : %+.5f   reported rank %s of %s   floor %s"
      % (cand, crd["candidate_rank_among_controls"], crd["n_controls"] + 1, crd["rank_p_floor"]))
print("orientation : %s" % crd.get("rank_orientation", "(rank 1 = largest recovery)"))

# --- REPORT IDENTITY, asserted before a single number is read (REVIEW R10 MAJOR-1) ---------------
print()
print("REPORT IDENTITY (asserted, not assumed):")
print("  codeword=%r split=%r require_rescue_layer=%r reference_arm=%r"
      % (d.get("codeword"), d.get("split"), d.get("require_rescue_layer"), d.get("reference_arm")))
print("  require_slurm_job=%s" % (sorted(map(str, d.get("require_slurm_job") or []))))
assert d.get("codeword") == EXPECT_CODEWORD, (
    "this report is about codeword %r, not %r -- WRONG REPORT" % (d.get("codeword"), EXPECT_CODEWORD))
assert d.get("split") == EXPECT_SPLIT, (
    "this report is about split %r, not %r -- WRONG REPORT" % (d.get("split"), EXPECT_SPLIT))
assert int(d.get("require_rescue_layer")) == EXPECT_LAYER, (
    "this report pins layer %r, not %d -- WRONG REPORT" % (d.get("require_rescue_layer"), EXPECT_LAYER))
got_jobs = sorted(map(str, d.get("require_slurm_job") or []))
assert got_jobs == sorted(EXPECT_JOBS), (
    "this report's run set is %s, not the PR-CSI-005 set %s -- WRONG REPORT. (The PR-CSI-006 swap "
    "reads are the same 46 controls with ONE extra job id appended, which is exactly how mutations "
    "P2/P3 got a verdict printed out of the wrong file.)" % (got_jobs, sorted(EXPECT_JOBS)))
bad_arms = sorted(a for a in d.get("arms", []) if str(a).startswith("XSWAP"))
assert not bad_arms, ("this report contains cross-codeword SWAP arms %s -- it is a PR-CSI-006 swap "
                      "read, not the PR-CSI-005 family read" % bad_arms)

# WHICH ARM IS THE CANDIDATE. The report does not carry the name, so it is RESOLVED from the data:
# the candidate arm is the non-control arm whose own recovery against the reference reproduces
# crd["candidate"]. In the swap reports this resolves to XSWAP_FROM_* and the assert below fires.
dm = d["domain_means"]
ref_arm = d["reference_arm"]
DOMS = sorted(dm[ref_arm])
assert len(DOMS) == int(d["n_domains"]), (
    "domain_means carries %d domains but the report says n_domains=%s" % (len(DOMS), d["n_domains"]))
for a in dm:
    assert sorted(dm[a]) == DOMS, "arm %s does not carry the same domain set as %s" % (a, ref_arm)


def recovery(arm):
    """Recovery of `arm` against the reference, recomputed from domain_means.

    REVIEW R10 MAJOR-2. X used to be recounted from crd["controls"], which the analyser has already
    ROUNDED TO 5 dp -- and at 5 dp there is a LIVE TIE (KO_SHUF16 rounds to exactly the candidate's
    -0.00014), so `>=` vs `>` decided one unit of the PRIMARY statistic by rounding (mutation P1
    gave X = 27). domain_means is 5 dp PER DOMAIN averaged over n domains, i.e. ~1e-6 -- two orders
    finer than the scalars, and the finest precision the committed artifact carries.
    """
    return (sum(dm[arm][x] for x in DOMS) - sum(dm[ref_arm][x] for x in DOMS)) / float(len(DOMS))


non_ctrl = [a for a in dm if a not in ctrl and a != ref_arm]
cand_arms = sorted(a for a in non_ctrl if round(recovery(a), 5) == cand)
print("  candidate arm resolved from domain_means: %s   (non-control arms: %d)"
      % (cand_arms, len(non_ctrl)))
assert len(cand_arms) == 1, (
    "could not resolve the candidate arm uniquely -- %d arms reproduce crd['candidate']=%+.5f: %s"
    % (len(cand_arms), cand, cand_arms))
assert cand_arms[0] == EXPECT_CANDIDATE_ARM, (
    "the candidate of this report is %r, not %r -- WRONG REPORT (this is what mutations P2/P3 walked "
    "straight through: the swap reads' candidate is XSWAP_FROM_*, and the script printed a verdict "
    "about it as if it were the native axis)" % (cand_arms[0], EXPECT_CANDIDATE_ARM))
print("  -> this IS the PR-CSI-005 button/train L18 read, candidate %s." % EXPECT_CANDIDATE_ARM)

# --- non-vacuity, asserted before anything is believed (S-134) -----------------------------------
print()
names = set(ctrl)
assert len(ctrl) == 46, "expected 46 controls, report has %d" % len(ctrl)
assert STAGE1 <= names, "stage-1 controls missing from the report: %s" % sorted(STAGE1 - names)
assert NEW <= names, "new controls missing from the report: %s" % sorted(NEW - names)
assert len(STAGE1) == 10 and len(NEW) == 36
print("partition   : 10 stage-1 + 36 new = %d, and both subsets are fully present" % len(ctrl))

# --- X, RECOMPUTED AT FULL PRECISION, with every tie made EXPLICIT (REVIEW R10 MAJOR-2) ----------
cand_hp = recovery(EXPECT_CANDIDATE_ARM)
rec = {c: recovery(c) for c in ctrl}
print()
print("PRECISION. The analyser ranks on UNROUNDED means and then writes round(v, 5); recounting")
print("from those 5-dp scalars is a LOSSIER path than the one that produced the committed rank.")
print("  candidate   5-dp %+.5f  vs  recomputed from domain_means %+.10f" % (cand, cand_hp))
assert round(cand_hp, 5) == cand, (
    "the recomputed candidate %+.10f does not round to the report's %+.5f -- domain_means and "
    "control_recovery_distribution disagree, STOP" % (cand_hp, cand))
n_ctrl_5dp_match = sum(1 for c, v in ctrl.items() if round(rec[c], 5) == v)
print("  controls whose recomputation round-trips to the report's 5-dp value: %d of %d"
      % (n_ctrl_5dp_match, len(ctrl)))

ties_5dp = sorted(c for c, v in ctrl.items() if v == cand)
ties_hp = sorted(c for c in ctrl if rec[c] == cand_hp)
print()
print("TIES, stated explicitly rather than left to `>=` to settle silently:")
print("  exact ties at the report's 5 dp   : %d %s" % (len(ties_5dp), ties_5dp))
for c in ties_5dp:
    print("      %-12s 5-dp %+.5f == candidate %+.5f | at full precision %+.10f vs %+.10f -> %s"
          % (c, ctrl[c], cand, rec[c], cand_hp,
             "counts as an exceedance (>=)" if rec[c] >= cand_hp else "does NOT exceed"))
print("  exact ties at domain_means precision: %d %s" % (len(ties_hp), ties_hp))
if ties_hp:
    print("      TIE RULE (analyser, dcs_csi_subspace_analyze.py): sufficiency counts controls that")
    print("      recovered AT LEAST AS MUCH, `>=`, so a genuine tie COUNTS AGAINST the candidate.")

ex_all = [k for k in ctrl if rec[k] >= cand_hp]
ex_s1 = sorted(k for k in ex_all if k in STAGE1)
ex_new = sorted(k for k in ex_all if k in NEW)
X = len(ex_new)

# The same count off the LOSSY path, printed side by side so a divergence is visible, never silent.
X_5dp = len([k for k, v in ctrl.items() if v >= cand and k in NEW])
print()
print("X recomputed from domain_means (full precision) = %d" % X)
print("X recounted from the 5-dp scalars               = %d   %s"
      % (X_5dp, "AGREE" if X_5dp == X else "*** DISAGREE -- the rounding decided a unit of the PRIMARY"))
if X_5dp != X:
    print("*** STOP: X depends on the precision of the path used to compute it. Do not read further.")
    print("*** The PRIMARY statistic is not a property of the data at this precision; a human must")
    print("*** decide which path is authoritative BEFORE any verdict is printed. REFUSING.")
    sys.exit(3)

print()
print("exceedances (control recovery >= candidate):")
print("  among the 10 STAGE-1 (already known before this experiment): %d  %s" % (len(ex_s1), ex_s1))
print("  among the 36 NEW, BLIND controls  ->  X = %d" % X)
print("  total = %d  =>  R47 = %d  (reported rank %s)"
      % (len(ex_all), len(ex_all) + 1, crd["candidate_rank_among_controls"]))
# REVIEW R10 MAJOR-2 minimal fix: this agreement used to be PRINTED as True and never asserted.
assert len(ex_all) + 1 == crd["candidate_rank_among_controls"], (
    "the recomputed rank %d does not match the report's %s -- the recount is not measuring the same "
    "thing the committed rank came from, STOP"
    % (len(ex_all) + 1, crd["candidate_rank_among_controls"]))

print()
print("PREDICTION, fixed before the data: X ~ BetaBinom(36, 7.5, 3.5), E[X]=24.5455, 95%% [13, 34]")
print("  observed X = %d   -> inside the 95%% predictive interval? %s" % (X, 13 <= X <= 34))
print("  E[rank] projected 32.4 of 47   -> observed R47 = %d" % (len(ex_all) + 1))
print()
print("FALSIFICATION THRESHOLDS, evaluated:")
print("  X <= 12  (withdraw section 4.2)                : %s" % ("FIRED" if X <= 12 else "not fired (X=%d)" % X))
print("  X <=  4  (resurrect C3, clean family mandatory) : %s" % ("FIRED" if X <= 4 else "not fired (X=%d)" % X))
print("  X  =  0                                        : %s" % ("FIRED" if X == 0 else "not fired"))
print()
if X > 12:
    print("VERDICT: the dissociation analysis's projection is CONFIRMED. Button's candidate sits deep")
    print("inside a 46-control family exactly as predicted from its own stage-1 exceedances. No")
    print("falsification threshold fired; section 4.2 stands.")
else:
    print("VERDICT: a falsification threshold FIRED. See the preregistration's binding consequence.")
