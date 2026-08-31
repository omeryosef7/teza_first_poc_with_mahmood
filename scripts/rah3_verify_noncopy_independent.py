#!/usr/bin/env python
"""RAH3 independent verifier A -- re-derives the non-copy positive control from RAW inputs.

⚠ THIS FILE IMPORTS NO PRODUCER HELPER. Not `rah_preflight_transport`, not `ds_common`, not
`signals`. `RAH2-C-022` is why: that phase's verifier faithfully reproduced `artifact["p_concept"]`
while the quantity behind the label was 100 % `p_codeword`, and reported 0 failures over 29
registered fail-conditions. A verifier that re-reads the producer's chosen field inherits the
producer's choice of field. So this one re-derives the SEMANTICS -- token ids, capture site, surface
relationship, positions, hops, gates -- from the bank and the tokenizer, and only then compares.

⚠ It deliberately CANNOT check the probabilities: those need a forward pass, and re-running the
producer's own code to check the producer is not independent verification. Verifier B
(`rah3_verify_noncopy_gpu.py`) re-implements one frozen cell on GPU. This file states plainly which
assertions it cannot make rather than implying full coverage -- `RAH2-C-023`, where "22 checks" was
itself wrong and six assertions could not fail.

Tolerances are RELATIVE. An absolute tolerance around 1e-08 is vacuous (`RAH2-C-023`).

Usage:
  python scripts/rah3_verify_noncopy_independent.py outputs/boombness/rah_preflight/rah3nc_p_cb_*.json
"""
import glob
import json
import os
import sys

FAILS = []
CHECKS = []


def check(label, ok, detail=""):
    CHECKS.append(label)
    if not ok:
        FAILS.append("%s -- %s" % (label, detail))
    # ⚠ `RAH2-C-016`: a console column that does not hold what its text implies. The detail string
    # is the FAILURE explanation and must be printed ONLY on failure -- an earlier version printed
    # "ok | MISSING" for every present provenance field, which reads as the opposite of the truth.
    print("  %-58s %s%s" % (label, "ok" if ok else "FAIL", ("" if ok else " | " + detail)))
    return ok


def rel_close(got, want, rel=1e-9):
    """RELATIVE, with an epsilon floor so 0.0 vs 0.0 is equal and 1e-08 vs 2e-08 is NOT."""
    return abs(got - want) <= rel * abs(want) + 1e-300


def one(pattern):
    """FAIL-CLOSED glob. ⚠ `rah_repro_manifest.newest()` returns the LAST hit, so a new run under a
    matching prefix silently redefines what a published headline points at. Refuse instead."""
    hits = sorted(glob.glob(pattern))
    if len(hits) != 1:
        raise SystemExit("expected exactly 1 artifact for %r, found %d: %r"
                         % (pattern, len(hits), hits))
    return hits[0]


def main(argv):
    if len(argv) != 2:
        raise SystemExit(__doc__)
    path = one(argv[1]) if any(c in argv[1] for c in "*?[") else argv[1]
    art = json.load(open(path))
    print("artifact: %s" % path)

    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(art["model"])

    concept, codeword = art["concept"], art["codeword"]
    labels = art["label_words"]

    # ---- 1. label ids re-derived from the tokenizer, NOT read from the artifact -------------- #
    print("\n[1] label token ids, re-derived")
    mine = {}
    for w in labels:
        ids = tok(" " + w, add_special_tokens=False)["input_ids"]
        mine[w] = ids[0]
        check("label %r is a single leading-space token" % w, len(ids) == 1,
              "got %d tokens %r" % (len(ids), [tok.decode([i]) for i in ids]))
    check("re-derived label ids == artifact label_ids",
          mine == art["label_ids"], "mine=%r artifact=%r" % (mine, art["label_ids"]))
    check("label ids are pairwise disjoint", len(set(mine.values())) == len(labels))

    # ---- 2. the capture site, re-derived from the BANK, not from the artifact ---------------- #
    print("\n[2] donor capture, re-derived from the bank")
    bank = art["bank"]
    check("bank file still exists", os.path.exists(bank), bank)
    rows = [json.loads(l) for l in open(bank)]
    cand = [r for r in rows if r["condition"] == art["donor_condition"]
            and r["query_kind"] == "behavioral"
            and (art["donor_n_examples"] is None or r["n_examples"] == art["donor_n_examples"])]
    donors = sorted(cand, key=lambda r: r["prompt_id"])[:art["n_donors"]]
    check("donor count matches", len(donors) == len(art["donors"]),
          "bank gives %d, artifact has %d" % (len(donors), len(art["donors"])))

    mode, off = art["capture_mode"], art["capture_offset"]
    check("capture_mode is 'offset' (a surface capture is a COPY TEST)", mode == "offset", mode)
    check("capture_offset is the registered +1", off == 1, str(off))

    pieces, dists = set(), set()
    for d, a in zip(donors, art["donors"]):
        pid = d["prompt_id"]
        check("donor order matches on %s" % pid, pid == a["prompt_id"], a["prompt_id"])
        # re-render the template INDEPENDENTLY
        msgs = [{"role": "user", "content": d["full_prompt"]}]
        templated = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        enc = tok(templated, add_special_tokens=False, return_offsets_mapping=True)
        ids, offs = enc["input_ids"], enc["offset_mapping"]
        surf = d["target_surface"]
        pos_c = templated.lower().rfind(surf.lower())
        hits = [k for k, (x, y) in enumerate(offs) if y > pos_c and x < pos_c + len(surf) and y > x]
        anchor = hits[-1]
        idx = anchor + off
        piece = tok.decode([ids[idx]])
        pieces.add(piece); dists.add(idx - anchor)
        check("  %s capture index" % pid, idx == a["donor_tok_idx"],
              "mine=%d artifact=%d" % (idx, a["donor_tok_idx"]))
        check("  %s capture piece" % pid, piece == a["donor_piece"],
              "mine=%r artifact=%r" % (piece, a["donor_piece"]))
        check("  %s anchor is the concept surface" % pid,
              tok.decode([ids[anchor]]).strip().casefold() in surf.casefold(),
              tok.decode([ids[anchor]]))
        # THE non-copy conditions, re-derived
        bare = piece.strip().casefold()
        check("  %s piece is NOT part of the concept" % pid,
              bool(bare) and bare not in concept.casefold(), repr(piece))
        check("  %s piece is NOT part of the codeword" % pid,
              bool(bare) and bare not in codeword.casefold(), repr(piece))
        check("  %s piece id is NOT a candidate label id" % pid,
              ids[idx] not in set(mine.values()), repr(piece))
        check("  %s seq_len" % pid, len(ids) == a["seq_len"],
              "mine=%d artifact=%d" % (len(ids), a["seq_len"]))

    check("capture piece identical on every donor", len(pieces) == 1, repr(sorted(pieces)))
    check("capture distance identical on every donor", len(dists) == 1, repr(sorted(dists)))
    check("artifact's own consistency block agrees",
          art["capture_consistency"]["donor_piece"] in pieces
          and art["capture_consistency"]["n_rows"] == len(donors),
          repr(art["capture_consistency"]))

    # ---- 3. receiver geometry and the four requirements -------------------------------------- #
    print("\n[3] the four requirements, per cell")
    grid = art["grid"]
    for r in grid:
        hops_ok = (r["read_pos"] - r["q_pos"]) == r["hops"]
        check("%-14s R=%-3d hops arithmetic" % (r["form"], r["R"]), hops_ok,
              "read_pos-q_pos=%d hops=%d" % (r["read_pos"] - r["q_pos"], r["hops"]))
    zero_hop = sorted({r["form"] for r in grid if r["hops"] == 0})
    exposed = sorted({r["form"] for r in grid if r["names_candidates"]})
    print("  0-hop forms (COPY DIAGNOSTIC ONLY): %r" % zero_hop)
    print("  candidate-naming forms (NOT exposure-clean): %r" % exposed)
    for r in grid:
        want = bool(not r["names_candidates"] and r["hops"] > 0 and r["capture_mode"] == "offset")
        check("%-14s R=%-3d rah3_eligible re-derived" % (r["form"], r["R"]),
              r["rah3_eligible"] == want, "artifact=%s mine=%s" % (r["rah3_eligible"], want))
        check("%-14s R=%-3d mass_gate_ok re-derived" % (r["form"], r["R"]),
              r["mass_gate_ok"] == (r["patched_option_mass_at_best"] >= art["MASS_GATE"]),
              "mass=%.6g gate=%.6g flag=%s" % (r["patched_option_mass_at_best"],
                                               art["MASS_GATE"], r["mass_gate_ok"]))
        pc, pk = r["pos_ctrl_max"], r["p_codeword_at_best"]
        want_ok = bool(pc > art["TRANSPORT_POSITIVE_CONTROL_THRESHOLD"]
                       and r["uplift_over_unpatched"] > art["TRANSPORT_POSITIVE_CONTROL_THRESHOLD"]
                       and pc > pk)
        check("%-14s R=%-3d positive_control_ok re-derived" % (r["form"], r["R"]),
              r["positive_control_ok"] == want_ok,
              "p_conc=%.6g p_code=%.6g uplift=%.6g" % (pc, pk, r["uplift_over_unpatched"]))
        check("%-14s R=%-3d uplift arithmetic" % (r["form"], r["R"]),
              rel_close(r["uplift_over_unpatched"], pc - r["p_concept_unpatched"]),
              "%.10g vs %.10g" % (r["uplift_over_unpatched"], pc - r["p_concept_unpatched"]))
        # pos_ctrl_max must BE the max over per_layer, and best_donor_L must be its argmax
        best = max(r["per_layer"], key=lambda x: x["p_concept_mean"])
        check("%-14s R=%-3d pos_ctrl_max IS the max over L" % (r["form"], r["R"]),
              rel_close(r["pos_ctrl_max"], best["p_concept_mean"]),
              "%.10g vs %.10g" % (r["pos_ctrl_max"], best["p_concept_mean"]))
        check("%-14s R=%-3d best_donor_L is that argmax" % (r["form"], r["R"]),
              r["best_donor_L"] == best["L"], "%s vs %s" % (r["best_donor_L"], best["L"]))
        check("%-14s R=%-3d patch was LIVE on every donor" % (r["form"], r["R"]),
              r["n_patch_changed_at_best"] == best["n_donors_scored"],
              "%d/%d" % (r["n_patch_changed_at_best"], best["n_donors_scored"]))

    # ---- 4. provenance ------------------------------------------------------------------------ #
    print("\n[4] provenance (§37)")
    p = art.get("provenance", {})
    for f in ("git_commit", "git_dirty", "branch", "hostname", "argv", "python_executable",
              "bank_sha256", "expected_n_donors", "actual_n_donors", "slurm_job_id"):
        check("provenance carries %r" % f, f in p, "field ABSENT from the provenance block")
    check("expected_n_donors == actual_n_donors",
          p.get("expected_n_donors") == p.get("actual_n_donors"),
          "%r vs %r" % (p.get("expected_n_donors"), p.get("actual_n_donors")))
    import hashlib
    h = hashlib.sha256()
    with open(bank, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    check("bank_sha256 matches the bank on disk", p.get("bank_sha256") == h.hexdigest(),
          "artifact=%r recomputed=%r" % (p.get("bank_sha256"), h.hexdigest()))

    # ---- verdict ------------------------------------------------------------------------------ #
    print("\n" + "=" * 78)
    print("CANNOT CHECK HERE (needs a forward pass -- see verifier B): p_concept, p_codeword,")
    print("option_mass, unpatched distribution. This verifier re-derives SEMANTICS, not values.")
    print("=" * 78)
    print("%d checks, %d FAILURES" % (len(CHECKS), len(FAILS)))
    for f in FAILS:
        print("  FAIL: %s" % f)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
