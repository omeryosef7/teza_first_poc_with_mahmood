#!/usr/bin/env python3
"""Build the admissible patch-test population for a codeword and emit the --exclude-prompt-ids file that
makes score_behavior score EXACTLY the slot0 / non-TEST / non-excluded, behavioural, natural_doublespeak,
dose-4 (cds_n4) rows -- identical in every arm. Reuses the sanctioned filters: dcs_cont_scope.filter_rows
(Scope.PRIMARY = slot0, Population.TRAIN_VAL = leaves TEST unspent) + layerpos_map.load_split /
EXCLUDED_DOMAINS -- exactly the selection dcs_cont_differ_arms.py used, so the behavioural endpoint sits on
the same rows the causal signal was measured on. The exclude list is PROMPT-SIDE only (slot token, domain
split, excluded domain); no outcome information enters it. Prints the census and asserts no TEST domain survives.
"""
from __future__ import annotations
import argparse, importlib.util, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(mod, path):
    s = importlib.util.spec_from_file_location(mod, os.path.join(REPO, path))
    m = importlib.util.module_from_spec(s); sys.modules[mod] = m; s.loader.exec_module(m); return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--codeword", required=True, choices=("button", "basket"))
    ap.add_argument("--out-dir", default=os.path.join(REPO, "runargs/patch"))
    a = ap.parse_args()
    scope = _load("scope", "scripts/dcs_cont_scope.py")
    lpm = _load("lpm", "scripts/dcs_cont_layerpos_map.py")
    assign = lpm.load_split()
    EX = set(lpm.EXCLUDED_DOMAINS)

    bank = os.path.join(REPO, "data/boombness_prompts",
                        "boombness_prompt_bank_ts116m_%s_bomb.jsonl" % a.codeword)
    rows = [json.loads(l) for l in open(bank)]
    # pre-filter = exactly what score_behavior selects with the arm flags below
    pop = [r for r in rows if r.get("query_kind") == "behavioral"
           and r.get("condition") == "natural_doublespeak"
           and str(r.get("n_examples")) == "4"
           and r.get("bank_block") == "cds_n4"]
    if not pop:
        raise SystemExit("empty pre-filter -- check bank field names")
    # sanctioned narrowing: slot0 + train_val (drops TEST domains)
    kept, prov = scope.filter_rows(pop, scope.Scope.PRIMARY, scope.Population.TRAIN_VAL, assign)
    # also drop the 3 globally-excluded domains (differ-arms did this separately from filter_rows)
    kept = [r for r in kept if r.get("domain") not in EX]
    keep_ids = sorted(r["prompt_id"] for r in kept)
    keep_set = set(keep_ids)
    pop_ids = sorted(r["prompt_id"] for r in pop)
    exclude_ids = [pid for pid in pop_ids if pid not in keep_set]

    # HARD hygiene asserts
    keep_doms = sorted({r["domain"] for r in kept})
    test_leak = [d for d in keep_doms if assign.get(d) == "test"]
    if test_leak:
        raise SystemExit("TEST LEAK: %s" % test_leak)
    ex_leak = [d for d in keep_doms if d in EX]
    if ex_leak:
        raise SystemExit("EXCLUDED-DOMAIN LEAK: %s" % ex_leak)
    # every exclude id must be in the population (score_behavior enforces this too)
    assert set(exclude_ids) <= set(pop_ids)
    assert len(keep_ids) + len(exclude_ids) == len(pop_ids)

    os.makedirs(a.out_dir, exist_ok=True)
    exfile = os.path.join(a.out_dir, "exclude_%s.txt" % a.codeword)
    with open(exfile, "w") as f:
        f.write("\n".join(exclude_ids) + "\n")

    census = {}
    for d in keep_doms:
        census[assign.get(d, "UNASSIGNED")] = census.get(assign.get(d, "UNASSIGNED"), 0) + 1
    print("codeword:", a.codeword)
    print("pre-filter rows (behavioral/ND/n4/cds_n4):", len(pop_ids))
    print("KEEP (slot0, non-TEST, non-excluded):", len(keep_ids), "rows across", len(keep_doms), "domains")
    print("EXCLUDE ids:", len(exclude_ids))
    print("keep domain split census:", census)
    print("provenance:", json.dumps(prov))
    print("expect_n =", len(keep_ids))
    print("exclude file:", os.path.relpath(exfile, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
