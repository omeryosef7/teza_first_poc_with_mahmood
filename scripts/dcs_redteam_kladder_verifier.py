#!/usr/bin/env python3
"""dcs_redteam_kladder_verifier.py — an ADVERSARIAL harness against `scripts/dcs_verify_kladder.py`.

WHY THIS FILE EXISTS
--------------------
§28.9 of `external_md/DCS_BOMBNESS_SPECIFICITY_AND_CAUSAL_VALIDATION_PLAN_AND_PROGRESS_20260905.md`
records that **no `PR-035`-era result may be promoted until a real verifier exists**, because the
previous one passed on corruption it never detected (`C-049` §22.5) and because *"a verifier that
reads the producer's derived fields proves nothing"*.

`dcs_verify_kladder.py` was written to be that verifier. This file is the attack on it. It does not
verify anything about `R-080`; it verifies the VERIFIER, by constructing corruptions of the very
fixture world that `dcs_verify_kladder.py` builds for itself and asking whether the verifier still
prints `VERIFIED`.

⛔ NOTHING IN THIS FILE TOUCHES THE REPO. Every corruption is applied to a throwaway copy of the
verifier's own synthetic fixture inside a `TemporaryDirectory`.

WHAT WAS CONFIRMED ABOUT `dcs_verify_kladder.py` (its claims that HOLD, checked here in `--self-test`)
-----------------------------------------------------------------------------------------------
  ✅ It does **not** repeat `C-049` §22.5's defect. `run_mutations` binds each mutation to ONE
     designated check id, requires THAT id to be in `failed_ids`, and prints collateral separately
     (`all_ok &= caught`). A mutation deliberately bound to the WRONG check is reported
     `⛔ NOT CAUGHT` and the harness exits 1. Demonstrated by `_pin_designated_binding`.
  ✅ Its mutations are really applied. With the target arm directory deleted, `mut_N1` raises
     `TypeError` rather than silently doing nothing — the `C-049` "never applied at all" failure
     mode cannot occur silently. Demonstrated by `_pin_mutation_not_skippable`.
  ✅ It imports nothing from `scripts/dcs_kladder_analysis.py`.
  ✅ All seven of its declared mutations N1..N7 are caught by their designated checks (reproduced
     here in `--self-test`), and it reproduces `R-080` on the real artifacts.

WHAT IT DOES NOT CATCH (this file's finding — seven corruptions, all `verified_fails = false`)
----------------------------------------------------------------------------------------------
  X1  SILENT DENOMINATOR   — `semantic_logodds` nulled on 9 of 10 rows per domain in BOTH arms of
                             K=7. `by_domain_mean` skips null rows, so every published number is
                             bit-identical while the headline rung now rests on 38 readouts, not
                             380. `DONE.json` still says `rows_written = 380`; C1 counts JSON LINES,
                             never usable readouts. The producer JSON needs no edit at all.
  X2  SIGN INVERSION       — `results.jsonl` swapped between `dcsk7_C_demo` and `dcsk7_C_ctrl`.
                             Δ₇ becomes **+5.94** (demonstration knockout *raises* the bomb
                             readout), `n_negative` 38 → 0. C6 compares only |Δ|, so `K* = 7` and
                             `shape = STEP` survive. The rows' own `arm` field now reads
                             `dcsk7_C_ctrl` inside the demo directory — real rows carry exactly
                             this field (`C_ro_k7_demo` / `C_ro_k7_ctrl`) and the verifier never
                             reads it. ⛔ The DIRECTION of the effect is the whole of `R-080`.
  X3  ANCHOR BY COPY       — `dcsk8r_*/results.jsonl` replaced by byte-copies of `dcsk8`'s. §11.7's
                             kill criterion then reports `absolute_difference: 0` — the *strongest
                             possible pass* — for a re-run that never happened. C4 compares two
                             numbers and nothing that could distinguish a deterministic re-run from
                             `cp`. In the real repo the two files differ ONLY in the `arm` field
                             (`C_ro_k8_demo` vs `C_ro_k8r_demo`), which C1/C4 never read.
  X4  POPULATION SWAP      — the bank replaced by a DISJOINT 380-row / 38-domain population (0
                             family_ids in common with the scored rows), `bank_file_sha16`
                             recomputed so the join looks healthy. C7 then certifies "380/380
                             prompts newly cut ' bomb' at K=7" about prompts that were **never
                             scored**. ⛔ This is `C-053` §28.3's own lesson, re-opened on the token
                             claim: C7 checks the bank's shape, never its identity with the rows.
  X5  POPULATION DRIFT     — every scored row relabelled `cell A / n_examples 8 / cds_n8 /
                             literal_control / semantic_one_word`. `PR-032` §11.3's declared
                             population is cell C, `cds_n4`, n=4, `natural_doublespeak`,
                             `semantic_forced_choice`. No check reads the rows' population fields.
  X6  VACUOUS BY OMISSION  — the producer deletes `contracts`, `arm_dirs`, `largest_single_rung_rise`
                             and `shape_gaps`. Each is read behind `if con:` / `claimed is None or`
                             / `if pr:` / `or []`, so the producer makes those comparisons VANISH
                             and the verifier still prints `VERIFIED`. ⛔ A verifier whose coverage
                             the producer chooses is not independent of the producer.
  X7  RUNG SET BY PRODUCER — `verify()` derives the rungs under test from `prod["rungs"]` keys. The
                             producer drops K=16 (published in §27.2 as −7.8884, 37/38, p=2.8e-10);
                             K=16 is outside `PROFILE_KS`, so no gap appears and nothing complains.
                             The producer decides what gets verified.

USAGE
    python scripts/dcs_redteam_kladder_verifier.py --self-test   # exit 0: attack rig is sound
    python scripts/dcs_redteam_kladder_verifier.py --mutate      # exit 0: every declared outcome
                                                                 #  observed (survivors survived)
    python scripts/dcs_redteam_kladder_verifier.py --mutate --report out.json

EXIT SEMANTICS (read this before quoting a run)
    `--mutate` exits 0 when EVERY attack behaved EXACTLY as declared: each `SURVIVES` attack left
    ALL SEVEN of the verifier's checks PASSING (not merely its own designated one — this file
    refuses to repeat `C-049` §22.5 in its own harness), and each `CAUGHT` positive control failed
    its designated check. Exit 0 therefore means **the verifier is confirmed blind to X1..X7**,
    which is a finding against the verifier, not a pass for it.

LIMITATIONS OF THIS FILE
    It attacks `dcs_verify_kladder.py` on that file's OWN synthetic fixture, so it demonstrates
    missing CHECKS, not defects in the real `R-080` numbers (which the verifier does reproduce). It
    makes no claim about `PR-035`'s specificity analyzer, about external validity, or about §27.4's
    instrument confound. It does not attack the real Llama tokenizer path (`--self-test`/`--mutate`
    run on the verifier's `StubTokenizer`, as the verifier's own harness does).
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import shutil
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import dcs_verify_kladder as V  # noqa: E402  the verifier UNDER TEST

TARGET = os.path.join(_HERE, "dcs_verify_kladder.py")
ALL_CHECKS = list(V.CHECK_IDS)


# --------------------------------------------------------------------------- #
# FIXTURE PLUMBING
# --------------------------------------------------------------------------- #
def arm_path(env, tag):
    p, _skipped = V.resolve_arm_dir(env.arm_root, tag)
    if p is None:
        raise RuntimeError(f"attack precondition violated: no complete arm dir for {tag!r} "
                           f"(a corruption that cannot be applied must never be scored as a pass)")
    return p


def read_rows(path):
    with open(os.path.join(path, "results.jsonl")) as fh:
        return [json.loads(l) for l in fh if l.strip()]


def write_rows(path, rows):
    with open(os.path.join(path, "results.jsonl"), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def ladder_ks():
    return sorted(V.FIXTURE_TARGET_DELTA)


def rebuild_producer(env):
    """Regenerate the fixture's producer JSON from whatever is now on disk.

    This models the honest-but-wrong producer: an analyzer that faithfully summarises corrupt rows.
    It is exactly the adversary a verifier exists to catch, since a producer that disagreed with its
    own rows would be caught by C3's arithmetic alone.
    """
    made = {}
    for K in ladder_ks():
        for side in ("demo", "ctrl"):
            made[(K, side)] = os.path.basename(arm_path(env, f"dcsk{K}_C_{side}"))
    for side in ("demo", "ctrl"):
        made[("8r", side)] = os.path.basename(arm_path(env, f"dcsk8r_C_{side}"))
    prod = V._fixture_producer(env.arm_root, made, ladder_ks())
    with open(env.producer_json, "w") as fh:
        json.dump(prod, fh, indent=1)
    return prod


def load_producer(env):
    return V._load_json(env.producer_json)


def save_producer(env, prod):
    with open(env.producer_json, "w") as fh:
        json.dump(prod, fh, indent=1)


def restamp_bank_sha(env, bank_path):
    """Keep the bank->arm join looking healthy after editing the bank (as the verifier's own N7 does)."""
    sha = hashlib.sha256(open(bank_path, "rb").read()).hexdigest()[:16]
    n = sum(1 for l in open(bank_path) if l.strip())
    for d in sorted(glob.glob(os.path.join(env.arm_root, "dcsk*"))):
        mp = os.path.join(d, "metadata.json")
        if os.path.isfile(mp):
            m = V._load_json(mp)
            m["bank_file_sha16"] = sha
            m["bank_n_rows"] = n
            with open(mp, "w") as fh:
                json.dump(m, fh, indent=1)
    return sha


def effective_n(path):
    """Rows that actually carry a usable readout — the quantity C1 never counts."""
    return sum(1 for r in read_rows(path)
               if r.get("semantic_logodds") is not None)


# --------------------------------------------------------------------------- #
# THE ATTACKS. Each returns (detail, evidence-dict). `rebuild` says whether the producer is
# re-derived from the corrupted rows afterwards.
# --------------------------------------------------------------------------- #
def x1_silent_denominator(env):
    """X1 — null the readout on 9 of 10 rows per domain in BOTH K=7 arms. Numbers do not move."""
    before = json.dumps(load_producer(env), sort_keys=True)
    kept, nulled = 0, 0
    for side in ("demo", "ctrl"):
        p = arm_path(env, f"dcsk7_C_{side}")
        rows = read_rows(p)
        for r in rows:
            slot = r["family_id"].split("|")[2]          # slot0..slot9
            if slot != "slot0":
                r["semantic_logodds"] = None
                nulled += 1
            else:
                kept += 1
        write_rows(p, rows)
    after = json.dumps(load_producer(env), sort_keys=True)
    d = arm_path(env, "dcsk7_C_demo")
    return ("K=7 demo+ctrl: `semantic_logodds` set to null on 9 of every 10 rows per domain",
            {"rows_on_disk": len(read_rows(d)),
             "DONE.json rows_written": V._load_json(os.path.join(d, "DONE.json"))["rows_written"],
             "rows with a usable readout": effective_n(d),
             "readouts nulled (both arms)": nulled,
             "producer JSON edited": before != after,
             "why it is invisible": "by_domain_mean() skips null rows; the fixture's per-domain "
                                    "delta is slot-invariant, so every published number is "
                                    "bit-identical on 1/10 of the data"})


def x2_sign_inversion(env):
    """X2 — swap the K=7 demo and control row files. The effect's DIRECTION flips."""
    before = load_producer(env)["rungs"]["K7"]
    a, b = arm_path(env, "dcsk7_C_demo"), arm_path(env, "dcsk7_C_ctrl")
    ra, rb = read_rows(a), read_rows(b)
    write_rows(a, rb)
    write_rows(b, ra)
    stray = json.loads(open(os.path.join(a, "results.jsonl")).readline())["arm"]
    return ("K=7 `results.jsonl` exchanged between the demo and the control directory",
            {"clean  K7 mean_delta": before["mean_delta"],
             "clean  K7 n_negative": before["n_negative"],
             "`arm` field now inside dcsk7_C_demo/results.jsonl": stray,
             "unread evidence": "real rows carry arm='C_ro_k7_demo' / 'C_ro_k7_ctrl'; the verifier "
                                "reads neither the row `arm` field nor any demo-vs-nondemo key "
                                "signature (hook_n_blocked_keys, demo_key_min/max)",
             "why it is invisible": "C6 thresholds on |Δ| only; the sign test is symmetric, so "
                                    "Holm p is unchanged; K* and STEP survive a sign flip"})


def x3_anchor_by_copy(env):
    """X3 — make the `dcsk8r` re-run a byte-copy of `dcsk8`. §11.7's kill criterion then passes 0.0."""
    identical_before = []
    for side in ("demo", "ctrl"):
        src = arm_path(env, f"dcsk8_C_{side}")
        dst = arm_path(env, f"dcsk8r_C_{side}")
        sf = os.path.join(src, "results.jsonl")
        df = os.path.join(dst, "results.jsonl")
        identical_before.append(open(sf, "rb").read() == open(df, "rb").read())
        shutil.copyfile(sf, df)
    d = arm_path(env, "dcsk8r_C_demo")
    return ("dcsk8r_C_{demo,ctrl}/results.jsonl replaced by byte-copies of dcsk8's",
            {"files were identical before the copy": any(identical_before),
             "`arm` field now inside dcsk8r_C_demo/results.jsonl":
                 json.loads(open(os.path.join(d, "results.jsonl")).readline())["arm"],
             "metadata/DONE/argsfile/job-log": "untouched — still dcsk8r's own, so C1 is satisfied",
             "why it is invisible": "C4 compares recomputed(dcsk8r) with recomputed(dcsk8) and "
                                    "requires |d| <= 0.0. `cp` satisfies that criterion perfectly; "
                                    "the check cannot separate a deterministic re-run from a copy"})


def x4_population_swap(env):
    """X4 — substitute a disjoint bank population; C7's token claim is then about nothing."""
    arm = V.Arm("", arm_path(env, "dcsk8_C_demo"))
    bank = arm.meta["bank_path"]
    scored = {r["family_id"] for r in read_rows(arm_path(env, "dcsk8_C_demo"))}
    rows = [json.loads(l) for l in open(bank) if l.strip()]
    for r in rows:
        dom = "alt" + r["domain"][3:]
        r["family_id"] = dom + "|" + r["family_id"].split("|", 1)[1]
        r["domain"] = dom
        r["full_prompt"] = r["full_prompt"].replace("Site log for", "Alternate log for")
        r["prompt_sha16"] = hashlib.sha256(r["full_prompt"].encode()).hexdigest()[:16]
        r["prompt_id"] = hashlib.sha256(r["family_id"].encode()).hexdigest()[:16]
    V._write_bank(bank, rows)
    sha = restamp_bank_sha(env, bank)
    banked = {r["family_id"] for r in rows}
    return ("the bank replaced by a DISJOINT 380-row / 38-domain population, sha16 restamped",
            {"bank rows": len(rows),
             "bank domains": len({r["domain"] for r in rows}),
             "family_ids shared with the SCORED rows": len(scored & banked),
             "recomputed bank_file_sha16": sha,
             "why it is invisible": "C7 selects bank rows by metadata's population_filter and "
                                    "requires 380 rows / 38 domains; it never joins them to the "
                                    "arm's results rows on family_id or prompt_sha16 — C-053 "
                                    "§28.3's exact lesson, unapplied to the token claim"})


def x5_population_drift(env):
    """X5 — relabel every scored row's population fields away from `PR-032` §11.3's declared cell."""
    n = 0
    for K in ladder_ks() + ["8r"]:
        for side in ("demo", "ctrl"):
            tag = f"dcsk{K}_C_{side}" if K != "8r" else f"dcsk8r_C_{side}"
            p = arm_path(env, tag)
            rows = read_rows(p)
            for r in rows:
                r["cell"] = "A"
                r["n_examples"] = 8
                r["bank_block"] = "cds_n8"
                r["condition"] = "literal_control"
                r["query_kind"] = "semantic_one_word"
                n += 1
            write_rows(p, rows)
    return ("every scored row relabelled cell A / n_examples 8 / cds_n8 / literal_control / "
            "semantic_one_word",
            {"rows relabelled": n,
             "declared population (§11.3)": "cell C, cds_n4, n_examples 4, natural_doublespeak, "
                                            "semantic_forced_choice",
             "why it is invisible": "C1 asserts --conditions/--query-kinds on the ARGV only; no "
                                    "check reads cell / n_examples / bank_block / condition / "
                                    "query_kind off the result rows, nor cross-checks argv against "
                                    "metadata's population_filter"})


def x6_vacuous_by_omission(env):
    """X6 — the producer deletes the blocks whose absence makes checks vanish."""
    prod = load_producer(env)
    dropped = []
    for key in ("contracts", "arm_dirs", "largest_single_rung_rise", "shape_gaps"):
        if prod.pop(key, None) is not None:
            dropped.append(key)
    save_producer(env, prod)
    return ("producer strips " + ", ".join(dropped),
            {"blocks dropped": dropped,
             "checks silently skipped":
                 "C2 keys_masked/query_rows_edited/option_mass contract comparison (`if con:`); "
                 "C1 producer-claimed-dir vs independently-resolved dir (`claimed is None or ...`); "
                 "C6 largest_single_rung_rise (`if pr:`) and shape_gaps (`or []` == `[]`)",
             "why it matters": "the producer chooses the verifier's coverage — the same class of "
                               "defect as reading a producer field as ground truth"})


def x7_rung_set_by_producer(env):
    """X7 — the producer drops a published rung that lies outside PROFILE_KS."""
    prod = load_producer(env)
    for block in ("rungs", "contracts", "arm_dirs"):
        (prod.get(block) or {}).pop("K16", None)
    prod["profile"] = [p for p in prod.get("profile", []) if p[0] != 16]
    save_producer(env, prod)
    return ("producer silently drops the K=16 rung",
            {"K=16 arms still on disk": os.path.basename(arm_path(env, "dcsk16_C_demo")),
             "published in §27.2 as": "Δ = -7.8884, 37/38 domains, p = 2.84e-10",
             "why it is invisible": "verify() builds `wanted_arms` and `pairs` from prod['rungs'] "
                                   "keys; K=16 is outside PROFILE_KS so no gap appears in C6, and "
                                   "no check asserts which rungs must be present besides K=3..8"})


#: (id, expectation, one-line description, fn, rebuild-producer-after?)
#: expectation is "SURVIVES" (verifier must still pass ALL SEVEN checks) or "CAUGHT:<id>".
ATTACKS = [
    ("X1", "SURVIVES", "readout nulled on 342/380 rows; every published number unchanged",
     x1_silent_denominator, False),
    ("X2", "SURVIVES", "K=7 demo/control swapped — the effect's SIGN is inverted",
     x2_sign_inversion, True),
    ("X3", "SURVIVES", "the K=8 re-run is a byte-copy; §11.7 passes at |d| = 0.0",
     x3_anchor_by_copy, False),
    ("X4", "SURVIVES", "token identity certified on a bank disjoint from the scored rows",
     x4_population_swap, False),
    ("X5", "SURVIVES", "scored rows relabelled off the declared population",
     x5_population_drift, False),
    ("X6", "SURVIVES", "producer omits blocks, making four comparisons vanish",
     x6_vacuous_by_omission, False),
    ("X7", "SURVIVES", "producer drops a published rung; the rung set is producer-chosen",
     x7_rung_set_by_producer, False),
    # -- POSITIVE CONTROLS. If these do not fire, this file is broken and its survivors mean
    #    nothing. They are the verifier's OWN mutations, replayed through THIS harness.
    ("P1", "CAUGHT:C3", "positive control — the verifier's own N3 (domain unpairing)",
     V.mut_N3, False),
    ("P2", "CAUGHT:C4", "positive control — the verifier's own N4 (anchor nudged by +0.01)",
     V.mut_N4, False),
]


# --------------------------------------------------------------------------- #
# RUNNER
# --------------------------------------------------------------------------- #
def run_attack(name, fn, rebuild):
    """Build a clean fixture, corrupt it, and ask the verifier under test for a verdict."""
    with tempfile.TemporaryDirectory(prefix=f"dcs_redteam_{name}_") as root:
        env = V.build_fixture(root)

        # ⛔ The fixture derives env.published from the producer itself, so a fixture-only run
        #    cannot exercise the "recomputed vs the LOG's published constants" requires. Pin them
        #    to the CLEAN values, which is what repo_env() does with PUBLISHED_K8 / K_STAR / SHAPE.
        pinned = dict(env.published)

        base = V.verify(env, verbose=False)
        if not base.ok:
            return dict(name=name, precondition_ok=False, failed=base.failed_ids,
                        detail="clean fixture does not pass; attack result is meaningless",
                        evidence={})

        out = fn(env)
        detail, evidence = out if isinstance(out, tuple) else (str(out), {})
        if rebuild:
            rebuild_producer(env)
        env.published = pinned

        rep = V.verify(env, verbose=False)
        return dict(name=name, precondition_ok=True, failed=list(rep.failed_ids),
                    passed=[c for c in ALL_CHECKS if c not in rep.failed_ids],
                    detail=detail, evidence=evidence,
                    failure_text={cid: rep.checks[cid].failures[:3] for cid in rep.failed_ids})


def judge(expectation, res):
    if not res["precondition_ok"]:
        return False, "clean fixture failed before the corruption was applied"
    if expectation == "SURVIVES":
        if res["failed"]:
            return False, f"expected the verifier to be blind, but it failed {res['failed']}"
        return True, "the verifier printed VERIFIED on corrupted artifacts"
    want = expectation.split(":", 1)[1]
    if want in res["failed"]:
        return True, f"caught by its designated check {want}"
    return False, (f"positive control did NOT fire on {want} "
                   f"(failed instead: {res['failed'] or 'NOTHING'})")


def run_mutations(verbose=True, report_path=None):
    print("RED-TEAM HARNESS vs. scripts/dcs_verify_kladder.py")
    print("⛔ A `SURVIVES` line means the verifier under test printed VERIFIED on corrupted")
    print("   artifacts. This harness requires ALL SEVEN of its checks to pass for a survivor —")
    print("   it will not credit a survivor whose blindness is masked by an unrelated failure,")
    print("   which is C-049 §22.5's defect committed in the other direction.\n")

    results, ok = [], True
    for name, expectation, desc, fn, rebuild in ATTACKS:
        res = run_attack(name, fn, rebuild)
        good, why = judge(expectation, res)
        ok &= good
        res.update(expectation=expectation, description=desc, as_declared=good, verdict=why)
        results.append(res)

        tick = "AS DECLARED" if good else "⛔ NOT AS DECLARED"
        head = ("⛔ NOT CAUGHT — VERIFIER SAYS VERIFIED" if expectation == "SURVIVES" and good
                else ("CAUGHT" if expectation.startswith("CAUGHT") and good else "UNEXPECTED"))
        print(f"  {name}  [{expectation:>10}]  {head}   {tick}")
        print(f"        {desc}")
        print(f"        corruption: {res['detail']}")
        print(f"        verifier checks that FAILED: {res['failed'] or 'NONE — all 7 passed'}")
        if verbose:
            for k, v in (res.get("evidence") or {}).items():
                print(f"          . {k}: {v}")
            for cid, msgs in (res.get("failure_text") or {}).items():
                for m in msgs:
                    print(f"          ~ {cid}: {m[:150]}")
        print()

    surv = [r for r in results if r["expectation"] == "SURVIVES" and r["as_declared"]]
    ctrl = [r for r in results if r["expectation"].startswith("CAUGHT")]
    print(f"SURVIVING CORRUPTIONS: {len(surv)}/{sum(1 for a in ATTACKS if a[1] == 'SURVIVES')}"
          f"   — {', '.join(r['name'] for r in surv) or 'none'}")
    print(f"POSITIVE CONTROLS FIRING: {sum(1 for r in ctrl if r['as_declared'])}/{len(ctrl)}"
          f"   (if these do not fire, the survivors above prove nothing)")

    if report_path:
        with open(report_path, "w") as fh:
            json.dump(dict(target=TARGET, results=results), fh, indent=1)
        print(f"\n[write] {report_path}")

    print("\n" + ("⛔ VERIFIER BREACHED — every declared corruption behaved exactly as declared. "
                  "dcs_verify_kladder.py\n   is blind to X1..X7; §28.9's promotion gate is NOT yet "
                  "satisfied by it."
                  if ok else
                  "HARNESS INCONCLUSIVE — at least one attack did not behave as declared; the "
                  "findings above\n   may not be quoted until the discrepancy is explained."))
    return 0 if ok else 1


# --------------------------------------------------------------------------- #
# SELF-TEST — the rig itself, and the verifier's claims that DO hold.
# --------------------------------------------------------------------------- #
def _pin_designated_binding():
    """C-049 §22.5: does the target's harness credit a mutation caught by the WRONG check?"""
    saved = V.MUTATIONS
    try:
        def wrong(env):
            V._rewrite_rows(arm_path(env, "dcsk4_C_demo"), lambda rows: rows[:-1])
            return "row truncation deliberately mis-declared as a C7 mutation"
        V.MUTATIONS = [("MISBOUND", "C7", "bound to the wrong check", wrong)]
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = V.run_mutations(verbose=False)
        return rc == 1 and "NOT CAUGHT" in buf.getvalue()
    finally:
        V.MUTATIONS = saved


def _pin_mutation_not_skippable():
    """C-049 §22.5: with the input absent, is the mutation silently skipped?"""
    with tempfile.TemporaryDirectory(prefix="dcs_redteam_skip_") as root:
        env = V.build_fixture(root)
        shutil.rmtree(arm_path(env, "dcsk4_C_demo"))
        try:
            V.mut_N1(env)
            return False                      # returned normally == silently skipped
        except Exception:                     # noqa: BLE001  loud is the correct behaviour
            return True


def _pin_no_producer_import():
    src = open(TARGET).read()
    return "dcs_kladder_analysis" not in src.split('"""', 2)[-1]


def _pin_target_mutations_all_caught():
    """Reproduce the target's own N1..N7 claims through its own harness."""
    import io
    import contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = V.run_mutations(verbose=False)
    return rc == 0 and buf.getvalue().count("NOT CAUGHT") == 0


def _pin_clean_fixture_passes():
    with tempfile.TemporaryDirectory(prefix="dcs_redteam_clean_") as root:
        env = V.build_fixture(root)
        return V.verify(env, verbose=False).ok


def _pin_rebuild_producer_is_faithful():
    """Regenerating the producer from UNCORRUPTED rows must still verify clean.

    Without this pin, an attack could 'survive' merely because rebuild_producer() papered over the
    corruption with a producer the verifier would have accepted anyway.
    """
    with tempfile.TemporaryDirectory(prefix="dcs_redteam_rb_") as root:
        env = V.build_fixture(root)
        pinned = dict(env.published)
        rebuild_producer(env)
        env.published = pinned
        return V.verify(env, verbose=False).ok


def _pin_survivors_are_real_edits():
    """Every SURVIVES attack must actually change bytes on disk (no vacuous corruption)."""
    for name, expectation, _desc, fn, rebuild in ATTACKS:
        if expectation != "SURVIVES":
            continue
        with tempfile.TemporaryDirectory(prefix=f"dcs_redteam_edit_{name}_") as root:
            env = V.build_fixture(root)
            before = _tree_digest(root)
            fn(env)
            if rebuild:
                rebuild_producer(env)
            if _tree_digest(root) == before:
                return False
    return True


def _tree_digest(root):
    h = hashlib.sha256()
    for base, _dirs, files in sorted(os.walk(root)):
        for f in sorted(files):
            p = os.path.join(base, f)
            h.update(os.path.relpath(p, root).encode())
            h.update(open(p, "rb").read())
    return h.hexdigest()


def run_self_test(verbose=True):
    print("SELF-TEST — is this attack rig sound, and which of the verifier's claims hold?\n")
    pins = [
        ("the verifier's clean fixture passes all 7 checks", _pin_clean_fixture_passes),
        ("the verifier's own N1..N7 are each caught by their designated check",
         _pin_target_mutations_all_caught),
        ("✅ C-049 §22.5 NOT repeated: a mis-bound mutation is reported NOT CAUGHT, exit 1",
         _pin_designated_binding),
        ("✅ mutations are really applied: a missing input raises, it is not silently skipped",
         _pin_mutation_not_skippable),
        ("✅ the verifier imports nothing from the producer analyzer", _pin_no_producer_import),
        ("rebuild_producer() on UNCORRUPTED rows still verifies clean",
         _pin_rebuild_producer_is_faithful),
        ("every declared SURVIVES attack actually changes bytes on disk",
         _pin_survivors_are_real_edits),
    ]
    ok = True
    for label, fn in pins:
        try:
            good = bool(fn())
        except Exception as e:                                   # noqa: BLE001
            good, label = False, f"{label}  [raised {type(e).__name__}: {e}]"
        ok &= good
        print(f"  {'ok  ' if good else 'FAIL'} {label}")

    print("\n  declared attacks:")
    for name, expectation, desc, _fn, _rb in ATTACKS:
        print(f"    {name}  [{expectation:>10}]  {desc}")

    print("\n" + ("SELF-TEST OK — the rig is sound; run --mutate for the findings."
                  if ok else "⛔ SELF-TEST FAILED"))
    return 0 if ok else 1


# --------------------------------------------------------------------------- #
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true",
                    help="check the attack rig and reproduce the verifier's claims that hold")
    ap.add_argument("--mutate", action="store_true",
                    help="apply every declared corruption and require the declared outcome")
    ap.add_argument("--quiet", action="store_true", help="suppress the per-attack evidence")
    ap.add_argument("--report", default=None, help="optional path for a machine-readable report")
    a = ap.parse_args(argv)

    if a.self_test and a.mutate:
        print("⛔ --self-test and --mutate are separate runs; pass one.")
        return 2
    if a.self_test:
        return run_self_test(verbose=not a.quiet)
    if a.mutate:
        return run_mutations(verbose=not a.quiet, report_path=a.report)
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
