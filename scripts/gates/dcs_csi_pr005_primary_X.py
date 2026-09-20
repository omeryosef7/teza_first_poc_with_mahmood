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

d = json.load(open(REP))
crd = d["control_recovery_distribution"]
cand = crd["candidate"]
ctrl = crd["controls"]

print("report      : %s" % os.path.basename(REP))
print("n_domains   : %s   n_keys_common: %s" % (d["n_domains"], d["n_keys_common"]))
print("candidate   : %+.5f   reported rank %s of %s   floor %s"
      % (cand, crd["candidate_rank_among_controls"], crd["n_controls"] + 1, crd["rank_p_floor"]))
print("orientation : %s" % crd.get("rank_orientation", "(rank 1 = largest recovery)"))

# --- non-vacuity, asserted before anything is believed (S-134) -----------------------------------
names = set(ctrl)
assert len(ctrl) == 46, "expected 46 controls, report has %d" % len(ctrl)
assert STAGE1 <= names, "stage-1 controls missing from the report: %s" % sorted(STAGE1 - names)
assert NEW <= names, "new controls missing from the report: %s" % sorted(NEW - names)
assert len(STAGE1) == 10 and len(NEW) == 36
print("partition   : 10 stage-1 + 36 new = %d, and both subsets are fully present" % len(ctrl))

ex_all = [k for k, v in ctrl.items() if v >= cand]
ex_s1 = sorted(k for k in ex_all if k in STAGE1)
ex_new = sorted(k for k in ex_all if k in NEW)
X = len(ex_new)

print()
print("exceedances (control recovery >= candidate):")
print("  among the 10 STAGE-1 (already known before this experiment): %d  %s" % (len(ex_s1), ex_s1))
print("  among the 36 NEW, BLIND controls  ->  X = %d" % X)
print("  total = %d  =>  R47 = %d  (matches reported rank %s: %s)"
      % (len(ex_all), len(ex_all) + 1, crd["candidate_rank_among_controls"],
         len(ex_all) + 1 == crd["candidate_rank_among_controls"]))

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
