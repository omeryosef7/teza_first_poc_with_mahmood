"""PR-CSI-007 PREFLIGHT -- run BEFORE the family is read.

REVIEW R11 MINOR-4 measured that this file contained NO assert, NO sys.exit and no failure list: it
printed "*** CIRCULAR -- STOP ***" and then exited 0, and its sibling gates (dcs_csi_pr005_gate0.py,
dcs_csi_pr006_gate0.py) all sys.exit. Every verdict below is now asserted, and the vacuous-comparison
shapes R11 named are refused: a comparison over ZERO keys or ZERO fit domains is a FAILURE, not a pass
(S-134 -- this sprint has already shipped a gate that printed PASS on zero rows).

R11 MAJOR-4 measured that EXPECT_BLOB in runargs/dcs_csi_pr007_read.txt is assigned once and read by
NOTHING -- the PR-CSI-007 code-identity VOID condition existed only as prose pasted into log entries.
Section 5 now checks it for real.
"""
import sys
import json, os, collections, torch

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
os.chdir(REPO)

fail = []
EXPECT_BLOB = "11d2c61747e9401e2d2cb8f4123dd1188674d61b"

print("=== 1. POPULATION: NKEEP, domains, leakage ===")
BANK = "data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl"
EXCL = "runargs/dcs_cont/exclude_button_bomb_sow_validation.txt"
ex = {l.strip() for l in open(EXCL) if l.strip() and not l.startswith("#")}
doms = collections.Counter()
n = 0
for l in open(BANK):
    r = json.loads(l)
    if (r.get("query_kind") == "semantic_one_word" and r.get("bank_block") == "cds_n4_sow"
            and r.get("condition") == "natural_doublespeak" and r["prompt_id"] not in ex):
        n += 1
        doms[r["domain"]] += 1
print("   NKEEP = %d   distinct domains = %d   rows per domain = %s"
      % (n, len(doms), dict(collections.Counter(doms.values()))))

split = json.load(open("data/boombness_prompts/dcs_ts116_domain_split.json"))
assign = split if isinstance(split, dict) and all(isinstance(v, str) for v in split.values()) else None
if assign is None:
    for k in ("assign", "domains", "split"):
        if isinstance(split.get(k), dict):
            assign = split[k]; break
lab = collections.Counter(assign.get(d, "MISSING") for d in doms)
print("   split labels of those domains: %s" % dict(lab))
if n == 0 or not doms:
    sys.exit("VACUOUS: NKEEP=%d over %d domains -- refusing to report a preflight pass" % (n, len(doms)))
EXPECT_NKEEP, EXPECT_DOMS = 230, 23
if n != EXPECT_NKEEP:
    fail.append("NKEEP is %d, expected %d" % (n, EXPECT_NKEEP))
if len(doms) != EXPECT_DOMS:
    fail.append("population spans %d domains, expected %d" % (len(doms), EXPECT_DOMS))
if set(lab) != {"validation"}:
    fail.append("population is not purely VALIDATION domains: %s" % dict(lab))

print()
print("=== 2. CIRCULARITY: was the axis fit on TRAIN only? ===")
pt = torch.load("configs/dcs_csi_axis_button_behavioral_L18.pt", map_location="cpu")
m = pt["meta"]
fp = m.get("fit_population", {})
print("   meta.selected_layer=%s codeword=%r" % (m.get("selected_layer"), m.get("codeword")))
print("   fit_population.split=%r n_domains=%s" % (fp.get("split"), fp.get("n_domains")))
fitd = fp.get("domains") or m.get("fit_domains") or []
print("   fit domains: %d, split labels = %s"
      % (len(fitd), dict(collections.Counter(assign.get(d, "MISSING") for d in fitd))))
overlap = sorted(set(fitd) & set(doms))
print("   INTERSECTION(fit domains, validation population) = %d  %s" % (len(overlap), overlap))
ho = m.get("held_out_validation_domains") or []
print("   meta.held_out_validation_domains == this population? %s (n=%d)"
      % (set(ho) == set(doms), len(ho)))
print("   -> %s" % ("NOT CIRCULAR" if not overlap else "*** CIRCULAR -- STOP ***"))
# R11: the more load-bearing vacuity is HERE, not in section 4 -- an empty fit-domain list makes
# "NOT CIRCULAR" print for the wrong reason.
if not fitd:
    sys.exit("VACUOUS: the axis reports ZERO fit domains, so 'NOT CIRCULAR' would be meaningless")
if overlap:
    fail.append("CIRCULAR: %d fit domain(s) are in the validation population: %s" % (len(overlap), overlap))
if fp.get("split") != "train":
    fail.append("axis fit_population.split is %r, expected 'train'" % fp.get("split"))

print()
print("=== 3. THE DEFAULT --out COLLISION ===")
p = "reports/DCS_CSI_SUBSPACE_button_validation.json"
print("   %s exists=%s size=%s" % (p, os.path.exists(p), os.path.getsize(p) if os.path.exists(p) else "-"))
if os.path.exists(p):
    d = json.load(open(p))
    c = d["control_recovery_distribution"]
    print("   it is the committed L20 K=%d read: rank %s of %s, floor %s"
          % (c["n_controls"], c["candidate_rank_among_controls"], c["n_controls"] + 1, c["rank_p_floor"]))

print()
print("=== 4. THE SWAP ARM CAN SHARE THESE CONTROLS ===")
sw = torch.load("configs/dcs_csi_axis_button_L18_PLUS_basket_swap.pt", map_location="cpu")["bases"]
base = pt["bases"]
shared = sorted(set(sw) & set(base))
bad = [k for k in shared if not torch.equal(sw[k], base[k])]
print("   keys compared: %d   mismatches: %d" % (len(shared), len(bad)))
print("   swap key present: %s" % ("swap_cand_from_basket" in sw))
if not shared:
    sys.exit("VACUOUS: the swap and native bases share ZERO keys -- 'mismatches: 0' would be empty")
if bad:
    fail.append("swap/native basis MISMATCH on %d shared key(s): %s" % (len(bad), bad[:5]))
if "swap_cand_from_basket" not in sw:
    fail.append("swap artifact is missing its donor key 'swap_cand_from_basket'")

print()
print("=== 5. BLOB / WORKTREE STATE FOR THE LAUNCH ===")
import subprocess
h = subprocess.run(["git", "hash-object", "src/boombness/score_behavior.py"],
                   capture_output=True, text=True, cwd=REPO).stdout.strip()
st = subprocess.run(["git", "status", "--porcelain", "src/boombness/score_behavior.py",
                     "doublespeak_causality/ds_common.py"],
                    capture_output=True, text=True, cwd=REPO).stdout.strip()
print("   score_behavior.py blob : %s" % h)
print("   worktree porcelain     : %r  (empty == clean, required by PR-CSI-007)" % st)
print("   EXPECT_BLOB            : %s" % EXPECT_BLOB)
if h != EXPECT_BLOB:
    fail.append("BLOB DRIFT -- score_behavior.py is %s, PR-CSI-007 requires %s. This is the VOID "
                "condition; the family cannot be read against a different scorer." % (h, EXPECT_BLOB))
if st:
    fail.append("worktree NOT clean for score_behavior.py / ds_common.py: %r" % st)

print()
if fail:
    print("=== PREFLIGHT FAILURES ===")
    for f in fail:
        print("   -", f)
    sys.exit(1)
print("=== PREFLIGHT PASS -- every verdict above was asserted, not printed ===")
