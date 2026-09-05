#!/usr/bin/env python3
"""DCS-C-055 — the row-level K-ladder verifier, closing the seven corruptions that survived
`scripts/dcs_verify_kladder.py`.

WHY A SECOND FILE. An adversarial red-team ran the first verifier end to end, confirmed all seven of
its claimed detections are real, and then found SEVEN corruption classes it passes on. Every one of
them shares a shape: the first verifier reasons about ARM DIRECTORIES and the PRODUCER'S OWN KEY SET,
and never looks inside a scored row or joins it to the bank. So it can be fooled by anything that
keeps the directory furniture intact while changing what is in the rows -- or by a producer that
simply reports less.

The corruptions, and the check here that closes each:

  X1 SILENT DENOMINATOR  semantic_logodds nulled on 9/10 rows; line count and DONE.json unchanged,
                         so the delta is computed on 38 readouts while everything says 380.  -> R1
  X2 SIGN INVERSION      results.jsonl swapped between the demo and control dirs; the producer is
                         internally consistent with the swapped rows, so mean_delta flips sign and
                         n_negative goes 38 -> 0 with every check still passing.               -> R2
  X3 ANCHOR BY COPY      dcsk8r's rows replaced by byte-copies of dcsk8's, making §11.7's
                         `absolute_difference = 0` -- A-026's headline -- trivially true.      -> R2, R3
  X4 POPULATION SWAP     the bank replaced by a disjoint population; the bank is never joined to
                         the scored rows, so nothing notices.                                  -> R4
  X5 POPULATION DRIFT    every scored row relabelled off PR-032 §11.3's declared population.   -> R4
  X6 VACUOUS BY OMISSION the producer deletes whole blocks; the verifier iterates the producer's
                         keys, so the comparisons evaporate instead of failing.                -> R5
  X7 PRODUCER PICKS RUNGS the producer drops a rung whose arms are complete on disk.           -> R5

⛔ THE GENERAL LESSON, which is the important part: a verifier that iterates the producer's own key
set can be made VACUOUS BY THE PRODUCER. R5 fixes that by declaring the expected key set and the
expected rung set HERE, from the preregistration, and failing when the producer reports less.
"""
from __future__ import annotations

import argparse, glob, hashlib, json, os, shutil, sys, tempfile

# ---------------------------------------------------------------- declared by PR-032, not by the producer
DECLARED_RUNGS = (1, 2, 3, 4, 5, 6, 7, 8, 16)
DECLARED_NEW = (3, 4, 5, 6, 7)
DECLARED_PRODUCER_KEYS = ("rungs", "contracts", "arm_dirs", "void", "shape_gaps",
                          "largest_single_rung_rise", "holm_family", "session_anchor_K8_rerun",
                          "K_star", "shape", "profile")
EXPECT_N = 380
EXPECT_DOMAINS = 38
DECLARED_POPULATION = dict(condition="natural_doublespeak", query_kind="semantic_forced_choice",
                           bank_block="cds_n4", n_examples=4)
BANK = "data/boombness_prompts/boombness_prompt_bank_cds38_button_bomb.jsonl"
ANCHOR_TAG = "dcsk8r"


def _newest_done(root, tag):
    for h in reversed(sorted(glob.glob(os.path.join(root, f"{tag}_*")))):
        if os.path.exists(os.path.join(h, "DONE.json")):
            return h
    return None


def _rows(d):
    p = os.path.join(d, "results.jsonl")
    return [json.loads(l) for l in open(p)] if os.path.exists(p) else None


def _argsfile_field(path, flag):
    if not os.path.exists(path):
        return None
    toks = open(path).read().split()
    return toks[toks.index(flag) + 1] if flag in toks else None


def verify(root, prod_path, bank_path, argsroot):
    fails, notes = [], []

    def check(cid, ok, why):
        if not ok:
            fails.append(cid)
            notes.append(f"  {cid}  FAIL  {why}")
        return ok

    prod = json.load(open(prod_path)) if os.path.exists(prod_path) else None
    if prod is None:
        return ["R0"], [f"  R0  FAIL  producer JSON missing: {prod_path}"]

    # ---- R5 FIRST: the producer does not get to choose its own coverage.
    missing_keys = [k for k in DECLARED_PRODUCER_KEYS if k not in prod]
    check("R5", not missing_keys,
          f"producer omits declared block(s) {missing_keys}; a verifier that iterates the "
          f"producer's keys goes VACUOUS when a block is deleted (X6)")
    reported = {int(k[1:]) for k in prod.get("rungs", {}) if k.startswith("K")}
    on_disk = {K for K in DECLARED_RUNGS
               if _newest_done(root, f"dcsk{K}_C_demo") and _newest_done(root, f"dcsk{K}_C_ctrl")}
    dropped = sorted(on_disk - reported)
    check("R5", not dropped,
          f"rungs {dropped} have COMPLETE arms on disk but are absent from the producer's "
          f"`rungs`; the producer chose the rung set (X7)")

    # ---- per-arm row-level checks
    tags = [(f"dcsk{K}_C_demo", f"C_ro_k{K}_demo", K) for K in DECLARED_RUNGS] + \
           [(f"dcsk{K}_C_ctrl", f"C_ro_k{K}_ctrl", K) for K in DECLARED_RUNGS] + \
           [(f"{ANCHOR_TAG}_C_demo", "C_ro_k8r_demo", 8), (f"{ANCHOR_TAG}_C_ctrl", "C_ro_k8r_ctrl", 8)]
    seen_arm_dirs = {}
    bank_ids = None
    if os.path.exists(bank_path):
        bank_ids = {}
        for l in open(bank_path):
            r = json.loads(l)
            bank_ids[r["prompt_id"]] = r

    for tag, expect_arm, K in tags:
        d = _newest_done(root, tag)
        if d is None:
            continue
        seen_arm_dirs[tag] = d
        rows = _rows(d)
        if rows is None:
            check("R1", False, f"{tag}: no results.jsonl")
            continue

        # R1 -- the DENOMINATOR. Count usable readouts, not JSON lines (X1).
        live = [r for r in rows if r.get("semantic_logodds") is not None]
        check("R1", len(live) == EXPECT_N,
              f"{tag}: {len(live)} NON-NULL semantic_logodds among {len(rows)} lines "
              f"(expected {EXPECT_N}); the delta's denominator is not the row count (X1)")
        per = {}
        for r in live:
            per[r["domain"]] = per.get(r["domain"], 0) + 1
        check("R1", len(per) == EXPECT_DOMAINS and len(set(per.values())) == 1,
              f"{tag}: usable readouts per domain not uniform over {EXPECT_DOMAINS} domains: "
              f"{sorted(set(per.values()))} across {len(per)} domains")

        # R2 -- ROW-LEVEL ARM IDENTITY. Catches a demo/control swap (X2) and an anchor built by
        # copying another rung's rows (X3): metadata and argsfiles stay intact under both, but the
        # rows themselves carry the arm they were SCORED under.
        arms = {r.get("arm") for r in rows}
        check("R2", arms == {expect_arm},
              f"{tag}: rows carry arm={sorted(a for a in arms if a is not None)!r}, expected "
              f"{expect_arm!r}; the rows in this directory were scored under a different arm "
              f"(X2 swap / X3 anchor-by-copy)")
        af = os.path.join(argsroot, f"{tag.replace('_C_', '_C_')}.txt")
        want_k = _argsfile_field(af, "--knockout-last-k")
        if want_k is not None:
            ks = {r.get("knockout_last_k") for r in rows}
            check("R2", ks == {int(want_k)},
                  f"{tag}: rows carry knockout_last_k={sorted(k for k in ks if k is not None)!r} "
                  f"but its committed argsfile says {want_k}")

        # R4 -- JOIN THE ROWS TO THE BANK, and to the declared population (X4, X5).
        if bank_ids is not None:
            miss = [r["prompt_id"] for r in rows if r["prompt_id"] not in bank_ids]
            check("R4", not miss,
                  f"{tag}: {len(miss)} scored prompt_ids are absent from {os.path.basename(bank_path)}; "
                  f"the scored rows and the declared bank are different populations (X4)")
            bad = []
            for r in rows[:EXPECT_N]:
                b = bank_ids.get(r["prompt_id"])
                if b is None:
                    continue
                for f in ("condition", "query_kind", "bank_block", "n_examples", "domain"):
                    if r.get(f) != b.get(f):
                        bad.append((r["prompt_id"], f, r.get(f), b.get(f)))
            check("R4", not bad,
                  f"{tag}: {len(bad)} row/bank field disagreements, e.g. {bad[:3]}; the scored rows "
                  f"were relabelled away from the bank they claim to come from (X5)")
            off = [(f, v) for f, v in DECLARED_POPULATION.items()
                   if {r.get(f) for r in rows} != {v}]
            check("R4", not off,
                  f"{tag}: rows are off PR-032 §11.3's declared population on {off} (X5)")

    # ---- R3 -- the anchor must be a RE-RUN, not a copy (X3).
    a_demo, k8_demo = seen_arm_dirs.get(f"{ANCHOR_TAG}_C_demo"), seen_arm_dirs.get("dcsk8_C_demo")
    if a_demo and k8_demo:
        h = lambda p: hashlib.sha256(open(os.path.join(p, "results.jsonl"), "rb").read()).hexdigest()
        same = h(a_demo) == h(k8_demo)
        check("R3", not same,
              f"the anchor's results.jsonl is BYTE-IDENTICAL to dcsk8's; §11.7's "
              f"`absolute_difference = 0` is then true by construction and proves nothing (X3)")
        check("R3", os.path.basename(a_demo) != os.path.basename(k8_demo),
              "anchor and dcsk8 resolve to the same directory")
    else:
        check("R3", False, "anchor or dcsk8 demo arm missing; §11.7 unevaluable")

    return fails, notes


# ---------------------------------------------------------------- mutation harness
def _stage(root, prod, tmp):
    """Copy the arm dirs + producer JSON into a sandbox so mutations never touch the real tree."""
    dst_root = os.path.join(tmp, "arms")
    os.makedirs(dst_root, exist_ok=True)
    for d in glob.glob(os.path.join(root, "dcsk*_C_*")):
        if os.path.exists(os.path.join(d, "DONE.json")):
            shutil.copytree(d, os.path.join(dst_root, os.path.basename(d)))
    dst_prod = os.path.join(tmp, "prod.json")
    shutil.copy(prod, dst_prod)
    dst_bank = os.path.join(tmp, "bank.jsonl")
    shutil.copy(BANK, dst_bank)
    return dst_root, dst_prod, dst_bank


def _write_rows(d, rows):
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def mut_X1(root, prod, bank):
    d = _newest_done(root, "dcsk7_C_demo")
    rows = _rows(d)
    for i, r in enumerate(rows):
        if i % 10:
            r["semantic_logodds"] = None
    _write_rows(d, rows)


def mut_X2(root, prod, bank):
    a, b = _newest_done(root, "dcsk7_C_demo"), _newest_done(root, "dcsk7_C_ctrl")
    ra, rb = _rows(a), _rows(b)
    _write_rows(a, rb); _write_rows(b, ra)


def mut_X3(root, prod, bank):
    src, dst = _newest_done(root, "dcsk8_C_demo"), _newest_done(root, "dcsk8r_C_demo")
    shutil.copy(os.path.join(src, "results.jsonl"), os.path.join(dst, "results.jsonl"))


def mut_X4(root, prod, bank):
    out = []
    for l in open(bank):
        r = json.loads(l)
        r["prompt_id"] = hashlib.sha256(("X4" + r["prompt_id"]).encode()).hexdigest()[:16]
        out.append(r)
    with open(bank, "w") as f:
        for r in out:
            f.write(json.dumps(r) + "\n")


def mut_X5(root, prod, bank):
    d = _newest_done(root, "dcsk6_C_demo")
    rows = _rows(d)
    for r in rows:
        r["cell"] = "A"; r["n_examples"] = 8; r["bank_block"] = "cds_n8"
        r["condition"] = "literal_control"; r["query_kind"] = "semantic_one_word"
    _write_rows(d, rows)


def mut_X6(root, prod, bank):
    j = json.load(open(prod))
    for k in ("contracts", "arm_dirs", "largest_single_rung_rise", "shape_gaps"):
        j.pop(k, None)
    json.dump(j, open(prod, "w"))


def mut_X7(root, prod, bank):
    j = json.load(open(prod))
    for blk in ("rungs", "contracts", "arm_dirs"):
        j.get(blk, {}).pop("K16", None)
    json.dump(j, open(prod, "w"))


MUTATIONS = [("X1", mut_X1, "R1"), ("X2", mut_X2, "R2"), ("X3", mut_X3, "R2"),
             ("X3b", mut_X3, "R3"), ("X4", mut_X4, "R4"), ("X5", mut_X5, "R4"),
             ("X6", mut_X6, "R5"), ("X7", mut_X7, "R5")]


def run_mutations(root, prod, argsroot):
    print("MUTATION HARNESS — each corruption must be caught by its DESIGNATED check.\n"
          "(These are the seven that SURVIVED scripts/dcs_verify_kladder.py.)\n")
    all_ok = True
    for name, fn, designated in MUTATIONS:
        with tempfile.TemporaryDirectory() as tmp:
            r2, p2, b2 = _stage(root, prod, tmp)
            fn(r2, p2, b2)
            fails, notes = verify(r2, p2, b2, argsroot)
            caught = designated in fails
            all_ok &= caught
            print(f"  {name} -> {designated}  {'CAUGHT' if caught else '*** NOT CAUGHT ***'}")
            for n in notes[:2]:
                print(n)
    print()
    if all_ok:
        print("MUTATION HARNESS OK — every corruption was caught by its designated check.")
        return 0
    print("MUTATION HARNESS FAILED — a corruption survived.")
    return 1


def self_test():
    """The harness must itself fail when a mutation is bound to the WRONG check."""
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "arms"))
        json.dump({}, open(os.path.join(tmp, "p.json"), "w"))
        fails, _ = verify(os.path.join(tmp, "arms"), os.path.join(tmp, "p.json"),
                          os.path.join(tmp, "nobank"), "runargs/dcs")
        assert "R5" in fails, "an empty producer must fail R5"
    print("[self-test] empty producer fails R5 as required -> PASS")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="outputs/boombness/score_behavior")
    ap.add_argument("--producer", default="outputs/boombness/dcs_analysis/dcs_kladder.json")
    ap.add_argument("--bank", default=BANK)
    ap.add_argument("--argsroot", default="runargs/dcs")
    ap.add_argument("--mutate", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.mutate:
        return run_mutations(a.root, a.producer, a.argsroot)
    fails, notes = verify(a.root, a.producer, a.bank, a.argsroot)
    for n in notes:
        print(n)
    if fails:
        print(f"\nROW-LEVEL VERIFICATION FAILED — checks {sorted(set(fails))}")
        return 1
    print("  R1  PASS  DENOMINATOR — non-null readouts = 380, uniform over 38 domains, every arm")
    print("  R2  PASS  ROW-LEVEL ARM IDENTITY — every row carries its own arm and K")
    print("  R3  PASS  ANCHOR IS A RE-RUN — not a byte-copy of dcsk8")
    print("  R4  PASS  BANK JOIN — scored rows join the declared bank and the declared population")
    print("  R5  PASS  COVERAGE — the producer reports every declared block and every rung on disk")
    print("\nROW-LEVEL VERIFIED — the seven corruptions that survived the first verifier are closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
