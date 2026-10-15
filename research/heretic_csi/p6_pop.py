#!/usr/bin/env python3
"""Single definition of the P6 rescue BASE-arm TRAIN population (used by p6_g3.py AND p6_g2.py so the two gates can
never disagree on it): bank rows semantic_one_word / natural_doublespeak (cell C) / n_examples 4 / cds_n4_sow, minus the
codeword's TRAIN exclusion file — exclude_<cw>_bomb_sow_train_occ.txt when it exists (bottle/cushion, AMENDMENT_1),
else exclude_<cw>_bomb_sow_train.txt; incumbents basket/button use runargs/dcs_cont/."""
import json, os
REPO = os.environ.get("P6_REPO", "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood")


def exclusion_path(cw):
    if cw in ("basket", "button"):
        return os.path.join(REPO, f"runargs/dcs_cont/exclude_{cw}_bomb_sow_train.txt")
    occ = os.path.join(REPO, f"runargs/heretic_csi/p6/exclude_{cw}_bomb_sow_train_occ.txt")
    return occ if os.path.exists(occ) else os.path.join(REPO, f"runargs/heretic_csi/p6/exclude_{cw}_bomb_sow_train.txt")


def population(cw):
    ex = exclusion_path(cw)
    excl = {l.strip() for l in open(ex) if l.strip() and not l.startswith("#")}
    pop = set()
    for l in open(os.path.join(REPO, f"data/boombness_prompts/boombness_prompt_bank_ts116m_{cw}_bomb.jsonl")):
        r = json.loads(l)
        if (r["query_kind"] == "semantic_one_word" and r["condition"] == "natural_doublespeak" and int(r["n_examples"]) == 4
                and r["bank_block"] == "cds_n4_sow" and r["prompt_id"] not in excl):
            pop.add(r["prompt_id"])
    return pop, ex


def bank_guard(rundir, cw):
    """[] if the run's RUNMETA references THIS codeword's bank, else a list with the reason."""
    try:
        rm = json.load(open(os.path.join(rundir, "RUNMETA.json")))
    except Exception as e:
        return [f"codeword_guard: unreadable RUNMETA in {rundir} ({e})"]
    s = str(rm.get("argv", "")) + " " + str(rm.get("args", ""))
    return [] if f"boombness_prompt_bank_ts116m_{cw}_bomb.jsonl" in s else [f"codeword_guard: {rundir} was not run on the {cw} bank"]
