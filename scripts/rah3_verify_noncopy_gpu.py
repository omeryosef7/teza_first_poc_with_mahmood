#!/usr/bin/env python
"""RAH3 independent verifier B -- re-derives the PROBABILITIES with its own patch implementation.

Verifier A (`rah3_verify_noncopy_independent.py`) re-derives the SEMANTICS -- capture site, token
ids, positions, hops, gates -- and says plainly that it cannot check p_concept, p_codeword or
option_mass, because those need a forward pass. This file does that half.

⚠ INDEPENDENCE IS THE POINT, so this file does NOT import `rah_preflight_transport`. It does not
call `ds_common.LayerPatch`. It re-implements the capture and the patch with its own forward hook,
re-renders the receiver from a TRANSCRIBED form body, and only then compares. `RAH2-C-022` is the
precedent: re-running the producer's own code to check the producer verifies nothing.

⚠ It verifies ONE cell -- the frozen configuration -- not the whole grid. That is deliberate: the
grid's value is a selection maximum, and the scientific claim rests on the frozen cell alone. A
verifier that re-ran 975 cells would cost a second full sweep to check a number nobody quotes.

Usage:
  python scripts/rah3_verify_noncopy_gpu.py --artifact outputs/.../rah3nc_p_cb_*.json \
                                            --form fewshot_cat --R 8 --L 26
"""
import argparse
import glob
import json
import sys

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

FAILS, CHECKS = [], []


def check(label, ok, detail=""):
    CHECKS.append(label)
    if not ok:
        FAILS.append("%s -- %s" % (label, detail))
    print("  %-56s %s%s" % (label, "ok" if ok else "FAIL", ("" if ok else " | " + detail)))
    return ok


def rel_close(got, want, rel=1e-5):
    """RELATIVE. ⚠ Absolute tolerance is vacuous against 1e-08 values (`RAH2-C-023`). 1e-5 rather
    than 1e-9 because this is a SEPARATE forward pass: kernel non-determinism on a different
    allocation is real, and a tolerance tighter than the arithmetic is a false alarm generator."""
    return abs(got - want) <= rel * abs(want) + 1e-300


#: The two exposure-clean form bodies, TRANSCRIBED (not imported) from the producer. If a
#: transcription is wrong, the token-length and position assertions below catch it -- they are
#: checked against the artifact's own recv_seq_len / q_pos / read_pos before any probability is
#: compared, so a divergence fails loudly rather than producing a wrong number quietly.
FORM_BODIES = {
    "fewshot_cat": 'apple -> fruit\nhammer -> tool\nsparrow -> bird\n"{p}" ->',
    "fewshot_syn": 'big -> large\nswift -> fast\nbegin -> start\n"{p}" ->',
}


def one(pattern):
    hits = sorted(glob.glob(pattern))
    if len(hits) != 1:
        raise SystemExit("expected exactly 1 artifact for %r, found %d" % (pattern, len(hits)))
    return hits[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--artifact", required=True)
    ap.add_argument("--form", required=True, choices=sorted(FORM_BODIES))
    ap.add_argument("--R", type=int, required=True)
    ap.add_argument("--L", type=int, required=True)
    a = ap.parse_args()

    path = one(a.artifact) if any(c in a.artifact for c in "*?[") else a.artifact
    art = json.load(open(path))
    print("artifact: %s\nverifying cell: form=%s R=%d donor_L=%d" % (path, a.form, a.R, a.L))

    cells = [c for c in art["grid"] if c["form"] == a.form and c["R"] == a.R]
    if len(cells) != 1:
        raise SystemExit("expected 1 cell for form=%s R=%d, found %d" % (a.form, a.R, len(cells)))
    cell = cells[0]
    layer = [x for x in cell["per_layer"] if x["L"] == a.L]
    if len(layer) != 1:
        raise SystemExit("no per_layer entry for L=%d" % a.L)
    layer = layer[0]

    tok = AutoTokenizer.from_pretrained(art["model"])
    model = AutoModelForCausalLM.from_pretrained(art["model"], dtype=torch.bfloat16,
                                                 device_map="auto", attn_implementation="eager")
    model.eval()
    dev = next(model.parameters()).device

    concept, codeword = art["concept"], art["codeword"]
    labels = art["label_words"]
    lab_ids = {}
    for w in labels:
        ids = tok(" " + w, add_special_tokens=False)["input_ids"]
        if len(ids) != 1:
            raise SystemExit("label %r is not a single token" % w)
        lab_ids[w] = ids[0]
    check("label ids re-derived match the artifact", lab_ids == art["label_ids"],
          "%r vs %r" % (lab_ids, art["label_ids"]))

    # ---- 1. capture the donors, own hook, own index arithmetic ------------------------------- #
    print("\n[1] donor capture (own implementation)")
    rows = [json.loads(l) for l in open(art["bank"])]
    cand = [r for r in rows if r["condition"] == art["donor_condition"]
            and r["query_kind"] == "behavioral"
            and (art["donor_n_examples"] is None or r["n_examples"] == art["donor_n_examples"])]
    donors = sorted(cand, key=lambda r: r["prompt_id"])[:art["n_donors"]]

    reps = []
    for d, ad in zip(donors, art["donors"]):
        msgs = [{"role": "user", "content": d["full_prompt"]}]
        templated = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        enc = tok(templated, return_tensors="pt", add_special_tokens=False,
                  return_offsets_mapping=True)
        offs = enc.pop("offset_mapping")[0].tolist()
        ids = enc["input_ids"][0].tolist()
        surf = d["target_surface"]
        pc = templated.lower().rfind(surf.lower())
        hits = [k for k, (x, y) in enumerate(offs) if y > pc and x < pc + len(surf) and y > x]
        idx = hits[-1] + art["capture_offset"]
        check("  %s capture index == artifact" % d["prompt_id"], idx == ad["donor_tok_idx"],
              "%d vs %d" % (idx, ad["donor_tok_idx"]))
        with torch.no_grad():
            out = model(input_ids=enc["input_ids"].to(dev), output_hidden_states=True)
        # block index L <-> hidden_states[L+1]
        reps.append(out.hidden_states[a.L + 1][0, idx, :].detach().clone())
    check("captured %d donor vectors" % len(reps), len(reps) == art["n_donors"])

    # ---- 2. receiver, re-rendered from the transcribed body ---------------------------------- #
    print("\n[2] receiver geometry (own implementation)")
    body = FORM_BODIES[a.form].format(p=art["probe"])
    # both eligible forms are UNTEMPLATED with add_special_tokens=True at the producer's call site
    renc = tok(body, return_tensors="pt", add_special_tokens=True, return_offsets_mapping=True)
    roffs = renc.pop("offset_mapping")[0].tolist()
    rids = renc["input_ids"][0].tolist()
    check("receiver token length == artifact recv_seq_len", len(rids) == cell["recv_seq_len"],
          "%d vs %d -- TRANSCRIPTION MISMATCH" % (len(rids), cell["recv_seq_len"]))
    needle = '"%s"' % art["probe"]
    i = body.find(needle)
    lo, hi = i + 1, i + 1 + len(art["probe"])
    q_hits = [k for k, (x, y) in enumerate(roffs) if y > lo and x < hi and y > x]
    q_pos = q_hits[-1]
    read_pos = len(rids) - 1          # read_at == "final" for both eligible forms
    check("q_pos == artifact", q_pos == cell["q_pos"], "%d vs %d" % (q_pos, cell["q_pos"]))
    check("read_pos == artifact", read_pos == cell["read_pos"],
          "%d vs %d" % (read_pos, cell["read_pos"]))
    check("hops > 0 (requirement 3)", read_pos - q_pos > 0, str(read_pos - q_pos))
    check("hops == artifact", read_pos - q_pos == cell["hops"],
          "%d vs %d" % (read_pos - q_pos, cell["hops"]))
    check("receiver names NO candidate (requirement 1)",
          not [w for w in labels if w.casefold() in body.casefold()], body[:60])

    inp = {"input_ids": renc["input_ids"].to(dev)}
    with torch.no_grad():
        base = model(**inp)
    bp = torch.softmax(base.logits[0, read_pos, :].float(), dim=-1)
    check("unpatched p_concept == artifact", rel_close(float(bp[lab_ids[concept]]),
                                                       cell["p_concept_unpatched"]),
          "%.10g vs %.10g" % (float(bp[lab_ids[concept]]), cell["p_concept_unpatched"]))
    check("unpatched option mass == artifact",
          rel_close(float(sum(bp[i] for i in lab_ids.values())), cell["unpatched_option_mass"]),
          "%.10g vs %.10g" % (float(sum(bp[i] for i in lab_ids.values())),
                              cell["unpatched_option_mass"]))

    # ---- 3. the patch, own hook -- NOT ds_common.LayerPatch ----------------------------------- #
    print("\n[3] patched readout (own hook)")
    blocks = model.model.layers if hasattr(model, "model") else model.transformer.h
    pcs, pks, masses, changed = [], [], [], 0
    for v in reps:
        vv = v.to(dev, dtype=next(model.parameters()).dtype)
        applied = {"n": 0}

        def hook(_mod, _inp, output):
            hs = output[0] if isinstance(output, tuple) else output
            hs[0, q_pos, :] = vv
            applied["n"] += 1
            return output

        h = blocks[a.L].register_forward_hook(hook)
        try:
            with torch.no_grad():
                o = model(**inp)
        finally:
            h.remove()
        # ⚠ the liveness the producer's LayerPatch could not report (`RAH3-C-004`)
        if applied["n"] != 1:
            raise SystemExit("patch hook fired %d times, expected 1" % applied["n"])
        pr = torch.softmax(o.logits[0, read_pos, :].float(), dim=-1)
        if float(torch.max(torch.abs(pr - bp))) > 0.0:
            changed += 1
        pcs.append(float(pr[lab_ids[concept]]))
        pks.append(float(pr[lab_ids[codeword]]))
        masses.append(float(sum(pr[i] for i in lab_ids.values())))

    mine_pc, mine_pk = sum(pcs) / len(pcs), sum(pks) / len(pks)
    mine_mass = sum(masses) / len(masses)
    check("patch was LIVE on every donor", changed == len(reps), "%d/%d" % (changed, len(reps)))
    check("p_concept_mean == artifact", rel_close(mine_pc, layer["p_concept_mean"]),
          "%.10g vs %.10g" % (mine_pc, layer["p_concept_mean"]))
    check("p_codeword_mean == artifact", rel_close(mine_pk, layer["p_codeword_mean"]),
          "%.10g vs %.10g" % (mine_pk, layer["p_codeword_mean"]))
    check("option_mass_mean == artifact", rel_close(mine_mass, layer["option_mass_mean"]),
          "%.10g vs %.10g" % (mine_mass, layer["option_mass_mean"]))

    # ---- 4. the scientific reading of THIS cell, re-derived ----------------------------------- #
    print("\n[4] the four requirements, re-derived on this cell")
    check("requirement 1 exposure-clean", not cell["names_candidates"],
          repr(cell["names_candidates"]))
    check("requirement 3 non-zero hops", cell["hops"] > 0, str(cell["hops"]))
    check("requirement 4 non-surface capture", art["capture_mode"] == "offset",
          art["capture_mode"])
    print("  requirement 2 MASS_GATE=%.4g : option_mass=%.6g -> %s"
          % (art["MASS_GATE"], mine_mass, "REPORTABLE" if mine_mass >= art["MASS_GATE"]
             else "BELOW GATE"))
    print("  p_concept=%.6g  p_codeword=%.6g  p_concept > p_codeword = %s"
          % (mine_pc, mine_pk, mine_pc > mine_pk))

    print("\n%d checks, %d FAILURES" % (len(CHECKS), len(FAILS)))
    for f in FAILS:
        print("  FAIL: %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
