#!/usr/bin/env python3
"""HERETIC-CSI P6: installer strength per codeword from an existing BASE readout (CPU, no GPU).
install_strength = domain-mean over TRAIN domains of [mean y_install(cell C natural_doublespeak)
 - mean y_install(cell A benign_literal)], semantic_one_word channel, n_examples=4,
y_install = sigmoid(logp_concept - logp_codeword) (the frozen CSI readout). Unit = domain.
Usage: p6_install_strength.py <codeword> <readout_dir> [split=train]"""
import json, math, os, random, statistics, sys
REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cw, rd = sys.argv[1], sys.argv[2]; split = sys.argv[3] if len(sys.argv) > 3 else "train"
sp = json.load(open(os.path.join(REPO, "data/boombness_prompts/dcs_ts116_domain_split.json")))["assign"]
EX = {"restaurant_kitchen", "school_campus", "subway_station"}
acc = {}
for ln in open(os.path.join(REPO, rd, "results.jsonl")):
    r = json.loads(ln)
    if r["query_kind"] != "semantic_one_word" or r["n_examples"] != 4 or r["cell"] not in "AC": continue
    if sp.get(r["domain"]) != split or r["domain"] in EX: continue
    y = 1 / (1 + math.exp(-(r["logp_concept"] - r["logp_codeword"])))
    acc.setdefault(r["domain"], {"A": [], "C": []})[r["cell"]].append(y)
d = {k: statistics.mean(v["C"]) - statistics.mean(v["A"]) for k, v in acc.items() if v["A"] and v["C"]}
vals = list(d.values()); rng = random.Random(0)
bs = sorted(statistics.mean(rng.choice(vals) for _ in vals) for _ in range(2000))
print(json.dumps({"codeword": cw, "split": split, "n_domains": len(vals),
                  "install_strength_C_minus_A": round(statistics.mean(vals), 4),
                  "ci95": [round(bs[50], 4), round(bs[1949], 4)],
                  "mean_y_C": round(statistics.mean(statistics.mean(v["C"]) for v in acc.values()), 4),
                  "mean_y_A": round(statistics.mean(statistics.mean(v["A"]) for v in acc.values()), 4)}))
