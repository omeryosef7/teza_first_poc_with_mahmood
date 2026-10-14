#!/usr/bin/env python3
"""P6 gate G3, implemented to the FROZEN PREREG_P6 text: "option-mass gate PASS (median > 0.05 on BASE)".
BASE = the no-intervention Stage-0 readout; population = the rescue job's BASE-arm TRAIN population: bank rows with
query_kind=semantic_one_word, condition=natural_doublespeak (cell C), n_examples=4, bank_block=cds_n4_sow, MINUS the
ids in the codeword's TRAIN exclusion file (runargs/heretic_csi/p6/exclude_<cw>_bomb_sow_train.txt, or the _occ
version where it exists — bottle/cushion, PREREG_P6_AMENDMENT_1). Statistic: true median of per-row `option_mass` over
those rows that the readout scored. PASS iff median > 0.05. score_behavior's POOLED tail gate is a different readout-
health check: RECORDED here, never used for G3 (PREREG_P6_AMENDMENT_4).
Also reports (descriptive) the cell-C dose-4 one-word median over ALL splits and the health check (OOM/CUDA rows;
other failure reasons; occurrence_count_mismatch rows are the declared mechanical attrition of AMENDMENT_1).
Usage: p6_g3.py <codeword> <readout_dir>   -> one JSON line; exit 0 always (status in the JSON)."""
import json, os, statistics, sys
REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"


def main(cw, rd):
    rd = os.path.join(REPO, rd) if not os.path.isabs(rd) else rd
    ex = os.path.join(REPO, f"runargs/heretic_csi/p6/exclude_{cw}_bomb_sow_train_occ.txt")
    if not os.path.exists(ex):
        ex = os.path.join(REPO, f"runargs/heretic_csi/p6/exclude_{cw}_bomb_sow_train.txt")
    if cw in ("basket", "button"):
        ex = os.path.join(REPO, f"runargs/dcs_cont/exclude_{cw}_bomb_sow_train.txt")
    excl = {l.strip() for l in open(ex) if l.strip() and not l.startswith("#")}
    pop = set()
    for l in open(os.path.join(REPO, f"data/boombness_prompts/boombness_prompt_bank_ts116m_{cw}_bomb.jsonl")):
        r = json.loads(l)
        if (r["query_kind"] == "semantic_one_word" and r["condition"] == "natural_doublespeak" and int(r["n_examples"]) == 4
                and r["bank_block"] == "cds_n4_sow" and r["prompt_id"] not in excl):
            pop.add(r["prompt_id"])
    g3, alls, doms = [], [], set()
    for l in open(os.path.join(rd, "results.jsonl")):
        r = json.loads(l)
        if r.get("option_mass") is None:
            continue
        if r["query_kind"] == "semantic_one_word" and r["cell"] == "C" and int(r["n_examples"]) == 4:
            alls.append(r["option_mass"])
        if r["prompt_id"] in pop and r["query_kind"] == "semantic_one_word":
            g3.append(r["option_mass"]); doms.add(r["domain"])
    s = json.load(open(os.path.join(rd, "summary.json"))) if os.path.exists(os.path.join(rd, "summary.json")) else {}
    fr = (s.get("failures") or {}).get("failure_reasons", {}) or {}
    oom = sum(v for k, v in fr.items() if "OutOfMemory" in k or "CUDA" in k)
    other = {k: v for k, v in fr.items() if not ("OutOfMemory" in k or "CUDA" in k or "occurrence_count_mismatch" in k)}
    health = "HEALTH_OK" if (s and oom == 0 and not other and os.path.exists(os.path.join(rd, "DONE.json"))) else "HEALTH_FAIL"
    med = statistics.median(g3) if g3 else None
    out = {"codeword": cw, "readout_dir": os.path.relpath(rd, REPO), "health": health, "oom_rows": oom, "other_failures": other,
           "g3_population": f"TRAIN rescue BASE pop: semantic_one_word/natural_doublespeak(C)/n4/cds_n4_sow minus {os.path.relpath(ex, REPO)}",
           "g3_pop_size": len(pop), "g3_rows_scored": len(g3), "g3_domains": len(doms),
           "g3_median_option_mass": None if med is None else round(med, 5),
           "G3": "PASS" if (med is not None and med > 0.05) else "FAIL",
           "descriptive_C_dose4_all_splits_median": round(statistics.median(alls), 5) if alls else None,
           "pooled_tail_gate_RECORDED_NOT_USED": s.get("option_mass_gate")}
    out["status"] = ("G3_PASS" if out["G3"] == "PASS" else "G3_FAIL") if health == "HEALTH_OK" else "ERROR_HEALTH"
    print(json.dumps(out))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
