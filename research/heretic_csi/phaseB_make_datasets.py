#!/usr/bin/env python3
"""HERETIC-CSI Phase B: freeze the native-ARA populations (CPU only; run BEFORE any GPU job).

Cells (recovered from src/boombness/prompt_families.py CONDITIONS, not invented):
  A = benign_literal        (benign demos, codeword surface)  -> codeword NOT installed
  C = natural_doublespeak   (harm demos, codeword surface)    -> concept installed (y_install high)
  B = direct_harmful, E = concept_in_benign_ctx (not used here).
Heretic ARA terminology renamed: "good" = TARGET = cell C, "bad" = SOURCE = cell A. Native ARA pulls the
SOURCE's last-prefill-position module outputs toward the TARGET's (kNN, unpaired) — i.e. it asks whether
a generic end-of-prompt operator edit INSTALLS the concept into not-installed (A) prompts.

Population: bank_block=cds_n4_sow (semantic_one_word, n_examples=4 — the CSI P2a block), codeword bank
ts116m_<cw>_bomb. Domain split = frozen dcs_ts116_domain_split.json (unit = domain); the 3 preregistered
whole-population exclusions (restaurant_kitchen, school_campus, subway_station) are applied => 67 TRAIN
domains. TEST is never read. Every A row has a C partner with the same family_id (same preamble, query,
slot; only the demo block differs) — domain-matched by construction.

Roles (declared before any number exists):
  fit_good / fit_bad : TRAIN domains, bank-split "dev" families (5/domain/cell)       -> ARA fitting
  opt_A / opt_C      : TRAIN domains, bank-split "heldout", slots {0,4} (2/domain/cell) -> Optuna objective
  trainread_A / _C   : TRAIN domains, bank-split "heldout", all 5 slots                 -> final TRAIN read
  val_A / val_C      : VALIDATION domains, all 10 families/domain/cell                  -> single predeclared read
  val_behav_C        : VALIDATION domains, cell C, query_kind=behavioral (bank_block cds_n4), bank-split
                       "dev", slots {0,4} (2/domain) -> SECONDARY refusal read (Heretic KeywordRate; a
                       keyword heuristic, NOT content-true success; never optimized)
"""
import argparse
import hashlib
import json
import os

EXCLUDED = {"restaurant_kitchen", "school_campus", "subway_station"}

ap = argparse.ArgumentParser()
ap.add_argument("--codeword", required=True)
ap.add_argument("--out-root", default="configs/heretic_csi/phaseB")
a = ap.parse_args()

split = json.load(open("data/boombness_prompts/dcs_ts116_domain_split.json"))
assign = split["assign"]
bank_path = f"data/boombness_prompts/boombness_prompt_bank_ts116m_{a.codeword}_bomb.jsonl"
rows = [json.loads(l) for l in open(bank_path)]
rows = [r for r in rows if r.get("bank_block") == "cds_n4_sow" and r["cell"] in ("A", "C")
        and assign.get(r["domain"]) in ("train", "validation") and r["domain"] not in EXCLUDED]
assert all(r["query_kind"] == "semantic_one_word" and r["n_examples"] == 4 for r in rows)
by = {(r["cell"], r["family_id"]): r for r in rows}
fams = sorted({r["family_id"] for r in rows})
for f in fams:  # every family must have both cells (domain-matched pairing)
    assert ("A", f) in by and ("C", f) in by, f

KEEP = ("prompt_id", "family_id", "domain", "family_slot", "cell", "condition", "split", "codeword", "concept",
        "full_prompt")


def sel(cell, dsplit, bank_split=None, slots=None):
    out = [by[(cell, f)] for f in fams
           if assign[by[(cell, f)]["domain"]] == dsplit
           and (bank_split is None or by[(cell, f)]["split"] == bank_split)
           and (slots is None or by[(cell, f)]["family_slot"] in slots)]
    return [{k: r[k] for k in KEEP} for r in out]


behav = [r for r in json.loads("[" + ",".join(open(bank_path).read().split("\n")[:-1]) + "]")
         if r.get("bank_block") == "cds_n4" and r["query_kind"] == "behavioral" and r["cell"] == "C"
         and assign.get(r["domain"]) == "validation" and r["split"] == "dev" and r["family_slot"] in (0, 4)]
behav = sorted(behav, key=lambda r: r["family_id"])

sets = {
    "fit_good": sel("C", "train", "dev"), "fit_bad": sel("A", "train", "dev"),
    "opt_A": sel("A", "train", "heldout", {0, 4}), "opt_C": sel("C", "train", "heldout", {0, 4}),
    "trainread_A": sel("A", "train", "heldout"), "trainread_C": sel("C", "train", "heldout"),
    "val_A": sel("A", "validation"), "val_C": sel("C", "validation"),
    "val_behav_C": [{k: r[k] for k in KEEP} for r in behav],
}
od = os.path.join(a.out_root, a.codeword)
os.makedirs(od, exist_ok=True)
man = {"schema": "hcsi_phaseB_datasets/1", "codeword": a.codeword, "bank": bank_path,
       "bank_sha256": hashlib.sha256(open(bank_path, "rb").read()).hexdigest(),
       "split_manifest_sha16": split.get("manifest_sha16"), "excluded_domains": sorted(EXCLUDED),
       "roles": {"good(TARGET)": "cell C", "bad(SOURCE)": "cell A"}, "sets": {}}
for name, rr in sets.items():
    p = os.path.join(od, f"{name}.jsonl")
    with open(p, "w") as fh:
        for r in rr:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    info = {"path": p, "n_rows": len(rr), "n_domains": len({r["domain"] for r in rr}),
            "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest()}
    if name.startswith("fit_") or name == "val_behav_C":  # Heretic local-dataset dir: train.jsonl with a "text" column
        dd = os.path.join(od, name)
        os.makedirs(dd, exist_ok=True)
        with open(os.path.join(dd, "train.jsonl"), "w") as fh:
            for r in rr:
                fh.write(json.dumps({"text": r["full_prompt"]}) + "\n")
        info["heretic_dir"] = dd
    man["sets"][name] = info
# role disjointness
ids = {n: {r["prompt_id"] for r in rr} for n, rr in sets.items()}
assert not (ids["fit_good"] | ids["fit_bad"]) & (ids["trainread_A"] | ids["trainread_C"] | ids["val_A"] | ids["val_C"])
assert ids["opt_A"] <= ids["trainread_A"] and ids["opt_C"] <= ids["trainread_C"]
json.dump(man, open(os.path.join(od, "MANIFEST.json"), "w"), indent=2)
print(json.dumps({k: (v["n_rows"], v["n_domains"]) for k, v in man["sets"].items()}))
