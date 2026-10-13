#!/usr/bin/env python3
"""HERETIC-CSI P6: codeword provenance table (CPU; no model forward).

Joins the frozen PR-CSI-008 lexical screen (reports/DCS_CSI_PR008_LEXICAL_SCREEN.json) with:
  - English Zipf frequency from wordfreq 3.1.1 (NOT used by PR-CSI-008, which screened no frequency;
    added here as the P6 covariate, frozen before any P6 GPU number exists),
  - the Llama-3.1 token id of ' '+word (pinned snapshot 0e9e39f2...) as a secondary BPE-rank proxy,
  - on-disk artifact availability (prompt banks / readouts / behavioral corpora),
  - selection-contamination flags supplied by the caller's audit (--contam JSON).
Run with PYTHONPATH=outputs/heretic_csi/pylib_wordfreq (isolated install; frozen env untouched).
"""
import glob, json, os, sys
REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
SNAP = "/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659"
from wordfreq import zipf_frequency
from transformers import AutoTokenizer

scr = json.load(open(os.path.join(REPO, "reports/DCS_CSI_PR008_LEXICAL_SCREEN.json")))
contam = json.load(open(sys.argv[1]))
tok = AutoTokenizer.from_pretrained(SNAP)
out = []
for r in scr["rows"]:
    w = r["word"]
    ids = tok.encode(" " + w, add_special_tokens=False)
    banks = sorted({os.path.basename(p).replace(".jsonl", "") for p in
                    glob.glob(os.path.join(REPO, "data/boombness_prompts", "boombness_prompt_bank*_%s_*.jsonl" % w))})
    rd = sorted(os.path.basename(p) for p in glob.glob(os.path.join(REPO, "outputs/boombness/score_behavior", "*_%s_bomb_*" % w)))
    cp = sorted(os.path.basename(p) for p in glob.glob(os.path.join(REPO, "outputs/boombness/extract_boombness", "*_%s_bomb_*" % w)))
    out.append({"word": w, "pr008_survivor": w in scr["survivors"],
                "L1_single_token": r["L1_pass"], "L2_incidence_rate": r["incidence_rate"],
                "zipf_en": zipf_frequency(w, "en"), "llama_token_ids": ids,
                "contamination": contam.get(w, "untouched (no GPU/selection use found)"),
                "banks_on_disk": banks, "n_readout_dirs": len(rd), "n_extract_dirs": len(cp)})
json.dump(out, open(sys.argv[2], "w"), indent=1)
for o in sorted(out, key=lambda o: -o["zipf_en"]):
    print("%-9s surv=%d zipf=%.2f id=%s banks=%d rd=%d ex=%d | %s" % (o["word"], o["pr008_survivor"], o["zipf_en"],
          o["llama_token_ids"], len(o["banks_on_disk"]), o["n_readout_dirs"], o["n_extract_dirs"], o["contamination"][:70]))
