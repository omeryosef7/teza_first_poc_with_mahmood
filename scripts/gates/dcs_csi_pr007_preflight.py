import json, os, collections, torch

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
os.chdir(REPO)

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
