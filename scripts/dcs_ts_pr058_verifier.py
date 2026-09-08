#!/usr/bin/env python3
"""`DCS-PR-058` PHASE 10 -- the INDEPENDENT verifier (checklist item T9).

WHY THIS FILE EXISTS, AND WHAT WOULD MAKE IT WORTHLESS
------------------------------------------------------
`scripts/dcs_ts_pr058_symmetry.py` is the analyzer. It has its own `--self-test` and its own
`--mutate`, and both are necessary. Neither is sufficient, because a producer's self-test shares
the producer's assumptions: if the analyzer believes an arm directory carries 1130 usable rows
because the arm's own summary says so, its self-test will happily confirm that it believes it.

So this file IMPORTS NOTHING FROM THE ANALYZER. Not a constant, not a helper, not the run-finder,
not the split loader, not the bank loader, not the arm-tag rule. Every quantity is RE-DERIVED here
from (a) the frozen preregistration, read as plain JSON, and (b) the arm directories on disk. Where
the analyzer and this file agree, they agree from two independent derivations; where they disagree,
one of them is wrong and the disagreement is visible. `--self-test` asserts the no-import property
against this file's own source text, so the claim in this docstring is CHECKED rather than made.

  ⛔ The one thing that would make this file worthless is a shortcut into the analyzer. There is
     an `assert_independent_of_analyzer()` that reads this source and fails on one.

THE CHECK CLASSES, INHERITED FROM `scripts/dcs_verify_kladder_rowlevel.py`
-------------------------------------------------------------------------
Its R1-R5 vocabulary is reused; its code is not (it binds `PR-032`'s rung set, its `EXPECT_N` is
380 and it resolves arms by the `dcsk*` glob, none of which can bind this population).

  R1 SILENT DENOMINATOR   count USABLE readouts, never JSON lines. `X1`: `semantic_logodds` nulled
                          on 9/10 rows leaves the line count and `DONE.json` untouched, so a delta
                          computed over 113 readouts is reported as 1130.
  R2 SIGN INVERSION       every row must carry its OWN arm identity, cell, dose, scope and read
                          position, and they must match the directory's declared arm. A swap of
                          two arms' `results.jsonl` is internally consistent and flips the sign of
                          every delta with nothing else changing.
  R3 ANCHOR BY COPY       a knockout arm whose rows are a byte-copy of its baseline makes
                          `delta == 0` true by construction, and three control DRAWS that share an
                          output hash are a control band that is secretly n=1 -- published twice in
                          this project, once with a fake between-draw sd of 0.0048.
  R4 POPULATION SWAP      join every scored row to the PINNED bank by `prompt_id` AND
     / DRIFT              `prompt_sha16`, and to the frozen split manifest by domain. A verifier
                          that never joins cannot see a bank substitution or a relabelled row.
  R5 VACUOUS BY OMISSION  the expected arm set and the expected summary keys are declared HERE,
     / PRODUCER PICKS     from the preregistration, so a producer that reports LESS fails instead
                          of shrinking the comparison. This is the general lesson of `C-055`: a
                          verifier that iterates the producer's own key set can be made vacuous by
                          the producer.

  R6 VOID BEFORE OUTCOME  re-derived independently of the analyzer's `liveness_gate`: eager
                          attention READ BACK from the loaded config, `hook_fired_count > 0`,
                          `n_decode_edits == 0`, realised == expected cells, a non-zero realised
                          dose, `index == len(input_ids) + rel_end` with no absolute index reused
                          across differing sequence lengths, and NO outcome computed at the
                          refused `position_NOT_USED` read site. Each of these makes a null VOID
                          rather than negative, so each is evaluated BEFORE any outcome is read.
  R7 DOMAIN UNIT          the independence unit is the domain. A row-level p-value has a MEASURED
                          false-positive rate of 0.2000 on this design; a producer summary that
                          reports one is refused outright.

STATE OF THE WORLD, 2026-09-08: NO PR-058 ARM HAS EVER RUN. Cells B and E have never been scored
on any channel by any run (checklist `T2`). So the only honest thing this file can verify TODAY is
itself: `--self-test` builds a synthetic arm tree that satisfies every check and confirms the
verifier PASSES it, and `--mutate` corrupts that tree in named ways and confirms each corruption is
CAUGHT BY THE NAMED CHECK. A verifier that has never been shown to fail is not evidence.

USAGE
    python3 scripts/dcs_ts_pr058_verifier.py --self-test
    python3 scripts/dcs_ts_pr058_verifier.py --mutate
    python3 scripts/dcs_ts_pr058_verifier.py --runs outputs/boombness/score_behavior
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import os
import random
import re
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREREG_DEFAULT = "configs/dcs_ts_pr058_phase10.json"
#: DCS-PR-063. The AMENDMENT that repairs the cells-B/E answer set. Named here, with the same
#: reasoning as F_ROWS above: a producer must not be able to make a check evaporate by not
#: mentioning the file that declares it.
AMENDMENT_DEFAULT = "configs/dcs_ts_pr063_phase10_amendment.json"
PR_ID = "DCS-PR-058"

#: The producer artifacts this verifier reads. Named here so that a producer cannot rename one and
#: have the corresponding check quietly evaporate.
F_ROWS = "results.jsonl"
F_DONE = "DONE.json"
F_ARM = "PR058_ARM.json"
F_LIVENESS = "PR058_LIVENESS.jsonl"

#: Summary keys the producer MUST report (R5). Declared here, not iterated from the producer.
DECLARED_SUMMARY_KEYS = ("arm_id", "bank", "cell", "query_kind", "n_examples", "knockout_scope",
                         "intervene", "attn_implementation", "n_rows")

#: The forbidden independence unit. Row-level permutation has a measured FPR of 0.2000 on this
#: design (`primary._row_level_permutation_is_forbidden`).
FORBIDDEN_UNITS = ("row", "prompt", "prompt_id")

#: THE INDEPENDENCE PROPERTY, enforced against this file's own text by `--self-test`.
FORBIDDEN_IMPORT_RE = re.compile(r"^\s*(?:from\s+dcs_ts_pr058_symmetry\b|import\s+dcs_ts_pr058_symmetry\b)",
                                 re.M)


class VerifierError(RuntimeError):
    pass


# ============================================================================================
# 0. INDEPENDENCE
# ============================================================================================
def assert_independent_of_analyzer(path=None):
    """The verifier must not import the producer. Checked, not asserted in a docstring."""
    p = path or os.path.abspath(__file__)
    with open(p) as fh:
        src = fh.read()
    # The regex literal that DEFINES the ban necessarily contains the module name, so the ban is
    # tested against import STATEMENTS at line start, not against any mention of the name.
    hits = [m.group(0).strip() for m in FORBIDDEN_IMPORT_RE.finditer(src)]
    if hits:
        raise VerifierError(
            "this verifier imports the analyzer (%s). A verifier that shares the producer's "
            "assumptions verifies nothing." % hits)
    return {"ok": True, "source": os.path.relpath(p, REPO)}


# ============================================================================================
# 1. THE FROZEN FILE, READ AS PLAIN JSON -- no loader shared with the analyzer
# ============================================================================================
def load_prereg(path):
    full = path if os.path.isabs(path) else os.path.join(REPO, path)
    with open(full) as fh:
        pr = json.load(fh)
    if pr.get("id") != PR_ID:
        raise VerifierError("preregistration id is %r, expected %r" % (pr.get("id"), PR_ID))
    if pr.get("status") != "FROZEN":
        raise VerifierError("preregistration status is %r, not FROZEN" % pr.get("status"))
    return pr


def _agree(a, b, what):
    if a != b:
        raise VerifierError("the frozen file disagrees with itself about %s: %r vs %r"
                            % (what, a, b))
    return a


def declared_population(pr):
    """Everything this verifier needs about WHO is in the population -- derived here."""
    p = pr["population"]
    excl = sorted({e["domain"] for e in p["preregistered_exclusions"] if e.get("whole_population")})
    return {
        "cells": sorted({v["cell"] for v in p["cells"].values()}),
        "banks": {k: v["path"] for k, v in p["banks"].items()},
        "bank_file_sha16": {k: v["bank_file_sha16"] for k, v in p["banks"].items()},
        "query_kind": p["query_kind_primary"],
        "n_examples": int(p["n_examples_primary"]),
        "n_examples_replication": int(p["n_examples_replication"]),
        "n_examples_null": int(p["n_examples_null"]),
        "excluded_domains": excl,
        # `n_domains_analysed` lives in the `split` block, and `primary` repeats it. BOTH are
        # read and a disagreement is a refusal: two fields that must agree and are never compared
        # are how a stale count survives a freeze.
        "n_domains": _agree(int(pr["split"]["n_domains_analysed"]),
                            int(pr["primary"]["n_domains_analysed"]),
                            "n_domains_analysed"),
        "rows_per_domain_per_cell": int(p["rows_per_domain_per_cell"]),
        "n_rows_per_bank_per_cell": int(p["n_rows_per_bank_per_cell"]),
        "selector_field": "cell",
        "split_manifest": pr["split"]["manifest"],
        "split_field": pr["split"]["field"],
        "n_control_draws": int(pr["seeds"]["n_control_draws"]),
        "attn_impl": pr["model"]["attn_impl"],
        "knockout_scope": pr["intervention"]["scope"],
        "read_position": pr["read_site"]["position_PRIMARY_REPRESENTATION"],
        "refused_read_position": pr["read_site"]["position_NOT_USED"],
        "control_ids": [c["id"] for c in pr["controls"]["arms"]],
        "independence_unit": pr["primary"]["independence_unit"],
    }


def declared_instrument(amend_path=None, repo=None):
    """R9. THE ANSWER SET THE ROWS MUST HAVE BEEN SCORED AGAINST -- re-derived HERE.

    WHY THIS CHECK EXISTS. Every other class in this file asks whether the right rows were
    compared. R9 asks whether the right QUESTION was asked of them, and it is the class job
    869869 walked straight through: 2784 rows, 0 failures, a healthy DONE.json, and a forced
    choice whose second option (` button`) occurs ZERO times in the stimulus and carries 5e-6 of
    the answer mass. Every one of R1-R8 would have passed that run. `option_mass` caught it and
    then MIS-NAMED it, because a mass gate cannot tell a disengaged model from a wrong option set.

    Returns None when the amendment is absent, which makes R9 bind zero rows and report EMPTY --
    never PASS (C-074).
    """
    repo = repo or REPO
    fp = amend_path or os.path.join(repo, AMENDMENT_DEFAULT)
    if not os.path.isabs(fp):
        fp = os.path.join(repo, fp)
    if not os.path.exists(fp):
        return None
    with open(fp) as fh:
        am = json.load(fh)
    inst = am.get("instrument") or {}
    pool_rel = ((inst.get("remap_pool") or {}).get("path") or "")
    pool_fp = pool_rel if os.path.isabs(pool_rel) else os.path.join(repo, pool_rel)
    if not pool_rel or not os.path.exists(pool_fp):
        raise VerifierError("amendment %s names remap pool %r, which is not on disk; the option "
                            "set cannot be re-derived and R9 will not be faked"
                            % (fp, pool_rel))
    with open(pool_fp) as fh:
        pj = json.load(fh)
    return {"amendment": fp,
            "mode": inst.get("semantic_options_mode"),
            "valence": inst.get("remap_valence"),
            "pool_path": pool_fp,
            "pool_pinned_sha16": (inst.get("remap_pool") or {}).get("content_sha16"),
            "pool_actual_sha16": (pj.get("_meta") or {}).get("content_sha16"),
            "pools": pj.get("pools") or {},
            "gate_scope": inst.get("option_mass_gate_scope"),
            "gate_min_dose": inst.get("option_mass_gate_min_dose")}


def declared_arm_tags(pop, banks=None):
    """THE EXPECTED ARM SET, DECLARED HERE (R5).

    Derived from the preregistration's own control list x cells x banks x the dose each control
    declares -- NOT read from whatever the producer happened to write to disk. A producer that
    silently drops an arm therefore fails a check instead of shrinking the comparison.

    The tag SHAPE is re-derived rather than imported: `pr058_<bank>_<control>_<cell>_n<dose>`,
    lowercase. If the analyzer's tag rule and this one ever disagree, `--runs` finds nothing and
    that disagreement is loud, which is the correct failure mode for two independent derivations.

    A RECORDED DIVERGENCE FROM THE ANALYZER. `dcs_ts_pr058_symmetry.build_arm_manifest` defaults
    to the two CONFIRMATORY bomb banks (38 arms). This file declares all SIX, because
    `installation.THE_ASYMMETRY...what_is_still_run` says in terms that "the knife and gun arms ARE
    run and ARE reported, as REGISTERED DESCRIPTIVE arms ... because their absence would itself be
    a selection". An arm that is run and reported is an arm a verifier must be able to see. The two
    derivations disagreeing about SCOPE is not a bug in either: it is exactly what two independent
    derivations are for, and `--banks` narrows this one when only the confirmatory pair is on disk.
    """
    tags = collections.OrderedDict()
    bank_keys = sorted(banks) if banks else sorted(pop["banks"])
    for cid in pop["control_ids"]:
        if cid == "K4":
            doses = [pop["n_examples_null"]]
        elif cid == "K7":
            doses = [pop["n_examples_replication"]]
        else:
            doses = [pop["n_examples"]]
        cells = ["B"] if cid == "K5" else pop["cells"]
        for bank in bank_keys:
            for cell in cells:
                for d in doses:
                    tag = "pr058_%s_%s_%s_n%d" % (bank, cid.lower(), cell.lower(), d)
                    tags[tag] = {"bank": bank, "cell": cell, "control_id": cid, "n_examples": d,
                                 "expect_enabled": cid not in ("K1", "K3")}
    if not tags:
        raise VerifierError("the declared arm set is EMPTY -- the expectation would be vacuous")
    return tags


# ============================================================================================
# 2. DISK -- run discovery, bank join, split join, all re-derived
# ============================================================================================
def find_complete_run(root, tag):
    """Newest COMPLETE run for a tag. Complete means DONE.json, not merely newest.

    A producer that takes the newest hit with no DONE.json filter reads a PARTIAL run: rows are
    flushed per row, so a killed job leaves a judgeable results.jsonl and no DONE.json.
    """
    hits = sorted(glob.glob(os.path.join(root, tag + "_*"))) + \
        ([os.path.join(root, tag)] if os.path.isdir(os.path.join(root, tag)) else [])
    for d in reversed(sorted(hits)):
        if os.path.exists(os.path.join(d, F_DONE)):
            return d
    return None


def read_jsonl(path):
    if not os.path.exists(path):
        return None
    out = []
    with open(path) as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line))
    return out


def sha16_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()[:16]


def sha256_rows(rows):
    """A content hash over the SCORED CONTENT of an arm, for the anchor-by-copy check."""
    h = hashlib.sha256()
    for r in rows:
        h.update(json.dumps(r, sort_keys=True).encode())
        h.update(b"\n")
    return h.hexdigest()


def load_bank_index(pr, bank_key, pop, bank_root=None):
    """prompt_id -> the bank's own row, restricted to the declared cell/channel/dose."""
    rel = pop["banks"][bank_key]
    path = os.path.join(bank_root or REPO, rel)
    idx = {}
    with open(path) as fh:
        for line in fh:
            d = json.loads(line)
            idx[d["prompt_id"]] = d
    return idx, path


def load_split(pop, split_root=None):
    path = os.path.join(split_root or REPO, pop["split_manifest"])
    with open(path) as fh:
        man = json.load(fh)
    return man["assign"], path


# ============================================================================================
# 3. THE CHECKS
# ============================================================================================
class Report:
    def __init__(self):
        self.rows = []

    def check(self, cid, ok, why, bound=None):
        # A check that bound ZERO rows is not a PASS. That is the whole of C-074 and it is the
        # failure mode a "verifier" is most likely to have.
        if bound is not None and bound == 0:
            self.rows.append((cid, "EMPTY", "%s (bound 0)" % why))
            return False
        self.rows.append((cid, "PASS" if ok else "FAIL", why))
        return ok

    @property
    def failed(self):
        return sorted({c for c, s, _ in self.rows if s != "PASS"})

    def render(self, fh=sys.stdout):
        for cid, status, why in self.rows:
            if status != "PASS":
                fh.write("  %-3s %-5s %s\n" % (cid, status, why))
        n_ok = sum(1 for _, s, _ in self.rows if s == "PASS")
        fh.write("  %d/%d checks passed; failing classes: %s\n"
                 % (n_ok, len(self.rows), self.failed or "none"))


def verify(pr, runs_root, bank_root=None, split_root=None, producer_summary=None, rep=None,
           banks=None, instrument=None):
    """Re-derive everything from the arm directories and refuse on any of R1-R9."""
    rep = rep or Report()
    pop = declared_population(pr)
    # ---- R9 THE INSTRUMENT PIN, once per run rather than once per arm.
    if instrument:
        rep.check("R9", (instrument["pool_pinned_sha16"]
                         and instrument["pool_actual_sha16"] == instrument["pool_pinned_sha16"]),
                  "remap pool %s carries content_sha16 %r but the amendment pins %r -- the words "
                  "the forced choice was built from are not the words that were pinned"
                  % (instrument["pool_path"], instrument["pool_actual_sha16"],
                     instrument["pool_pinned_sha16"]), bound=1)
        rep.check("R9", instrument["mode"] == "per_cell_remap",
                  "the amendment declares semantic_options_mode=%r; PHASE 10 rows must be scored "
                  "per cell, because ONE answer set built from rows[0] gives cells B/E a second "
                  "option that occurs zero times in their own stimulus"
                  % instrument["mode"], bound=1)
        rep.check("R9", instrument["gate_scope"] == "per_cell_dose",
                  "the amendment declares option_mass_gate_scope=%r; a pooled median is a "
                  "statement about population composition, not about any cell"
                  % instrument["gate_scope"], bound=1)
    expected = declared_arm_tags(pop, banks)
    assign, _split_path = load_split(pop, split_root)

    # ---- R5 FIRST. The producer does not get to choose its own coverage, and a producer that
    #      reports nothing must FAIL rather than produce an empty, all-passing report.
    on_disk = {t: find_complete_run(runs_root, t) for t in expected}
    present = {t: d for t, d in on_disk.items() if d}
    rep.check("R5", bool(present),
              "no declared arm has a COMPLETE run under %r (%d declared). Refusing to report an "
              "empty PASS: every number would be over a set that bound zero rows."
              % (runs_root, len(expected)))
    if not present:
        return rep
    missing = sorted(t for t, d in on_disk.items() if not d)
    rep.check("R5", not missing,
              "declared arm(s) absent from disk: %s" % missing[:6], bound=len(expected))
    if producer_summary is not None:
        miss_keys = [k for k in DECLARED_SUMMARY_KEYS if k not in producer_summary]
        rep.check("R5", not miss_keys,
                  "producer summary omits declared key(s) %s -- the verifier declares its own "
                  "expected key set so omission fails instead of shrinking the comparison"
                  % miss_keys, bound=len(DECLARED_SUMMARY_KEYS))
        rep.check("R7", str(producer_summary.get("independence_unit",
                                                 pop["independence_unit"])).lower()
                  not in FORBIDDEN_UNITS,
                  "the producer reports independence_unit=%r; row-level inference has a MEASURED "
                  "false-positive rate of 0.2000 on this design and the unit is the domain"
                  % producer_summary.get("independence_unit"), bound=1)

    # ---- bank pins, re-hashed here from the files on disk.
    for bank_key in sorted({v["bank"] for v in expected.values()}):
        _idx, bpath = load_bank_index(pr, bank_key, pop, bank_root)
        got = sha16_file(bpath)
        want = pop["bank_file_sha16"][bank_key]
        rep.check("R4", got == want,
                  "bank %s file sha16 %s != pinned %s" % (bank_key, got, want), bound=1)

    row_hash_by_arm, per_arm_ids = {}, {}
    for tag, d in sorted(present.items()):
        spec = expected[tag]
        rows = read_jsonl(os.path.join(d, F_ROWS))
        if not rows:
            rep.check("R1", False, "%s: %s is absent or empty" % (tag, F_ROWS))
            continue

        # ---- R1  THE DENOMINATOR. Usable readouts, never JSON lines.
        usable = [r for r in rows if r.get("semantic_logodds") is not None
                  and r.get("readout") == "semantic"]
        rep.check("R1", len(usable) == pop["n_rows_per_bank_per_cell"],
                  "%s: %d usable semantic readouts among %d JSON lines; the preregistration "
                  "declares %d rows per (bank, cell). A nulled readout leaves the line count and "
                  "DONE.json untouched."
                  % (tag, len(usable), len(rows), pop["n_rows_per_bank_per_cell"]),
                  bound=len(rows))
        per_dom = collections.Counter(r.get("domain") for r in usable)
        rep.check("R1",
                  len(per_dom) == pop["n_domains"]
                  and set(per_dom.values()) == {pop["rows_per_domain_per_cell"]},
                  "%s: %d domains with usable rows (declared %d), rows/domain=%s (declared %d)"
                  % (tag, len(per_dom), pop["n_domains"],
                     sorted(set(per_dom.values()))[:4], pop["rows_per_domain_per_cell"]),
                  bound=len(usable))

        # ---- R2  ROW-LEVEL ARM IDENTITY. Every row carries its own arm, cell, dose and scope.
        for field, want in (("cell", spec["cell"]),
                            ("query_kind", pop["query_kind"]),
                            ("n_examples", spec["n_examples"])):
            seen = {r.get(field) for r in usable}
            rep.check("R2", seen == {want},
                      "%s: rows carry %s=%s, the declared arm is %r. An arm whose ROWS disagree "
                      "with its directory is a swap, and a swap is internally consistent."
                      % (tag, field, sorted(map(str, seen))[:4], want), bound=len(usable))
        scopes = {str(r.get("knockout_scope") or "") for r in usable}
        want_scope = pop["knockout_scope"] if spec["expect_enabled"] else ""
        rep.check("R2", scopes == {want_scope} or (not spec["expect_enabled"] and scopes <= {""}),
                  "%s: rows carry knockout_scope=%s, expected %r for control %s"
                  % (tag, sorted(scopes)[:3], want_scope, spec["control_id"]), bound=len(usable))

        # ---- R6  VOID BEFORE OUTCOME. Liveness re-derived here, not read from a producer verdict.
        live = read_jsonl(os.path.join(d, F_LIVENESS)) or []
        if spec["expect_enabled"]:
            rep.check("R6", bool(live),
                      "%s: %s is absent or empty. A null behind an unrecorded hook is VOID, not a "
                      "negative." % (tag, F_LIVENESS))
        if live:
            impls = {str(r.get("attn_implementation", "")) for r in live}
            rep.check("R6", impls == {pop["attn_impl"]},
                      "%s: attn_implementation on the LOADED config is %s, not %r. Under SDPA the "
                      "additive mask edit is DISCARDED and the knockout is a silent no-op that "
                      "scores as a clean null." % (tag, sorted(impls), pop["attn_impl"]),
                      bound=len(live))
            if spec["expect_enabled"]:
                fired = sum(1 for r in live if int(r.get("hook_fired_count", 0)) > 0)
                rep.check("R6", fired == len(live),
                          "%s: %d/%d rows show a firing hook" % (tag, fired, len(live)),
                          bound=len(live))
                rep.check("R6", sum(int(r.get("n_decode_edits", 0)) for r in live) == 0,
                          "%s: n_decode_edits != 0 -- the scoping LEAKED and the mode is secretly "
                          "a larger intervention than the one reported" % tag, bound=len(live))
                rep.check("R6", sum(int(r.get("n_prefill_edits", 0)) for r in live) > 0,
                          "%s: n_prefill_edits == 0" % tag, bound=len(live))
                exp = sum(int(r.get("n_cells_edited_expected", 0)) for r in live)
                real = sum(int(r.get("n_cells_edited_realised", 0)) for r in live)
                rep.check("R6", exp > 0 and exp == real,
                          "%s: realised %d != expected %d cells (expected==0 would make the "
                          "comparison vacuous)" % (tag, real, exp), bound=len(live))
                zero = sum(1 for r in live if int(r.get("surface_span_n_tokens", 0)) <= 0)
                rep.check("R6", zero == 0,
                          "%s: %d row(s) with a REALISED DOSE of 0 -- the arm cut nothing"
                          % (tag, zero), bound=len(live))
            # end-relative index audit (P-N7), re-derived
            bad = [r for r in live
                   if int(r.get("rel_end", 0)) >= 0
                   or int(r.get("seq_len", 0)) + int(r.get("rel_end", 0))
                   != int(r.get("resolved_absolute_index", -1))]
            rep.check("R6", not bad,
                      "%s: %d record(s) whose index is not len(input_ids)+rel_end"
                      % (tag, len(bad)), bound=len(live))
            lens = {int(r.get("seq_len", 0)) for r in live}
            absi = {int(r.get("resolved_absolute_index", -1)) for r in live}
            rep.check("R6", not (len(lens) > 1 and len(absi) == 1),
                      "%s: ONE absolute index across %d distinct sequence lengths -- an absolute "
                      "index reads a different token in each arm" % (tag, len(lens)),
                      bound=len(live))
            positions = {str(r.get("read_position", "")) for r in live if r.get("read_position")}
            rep.check("R6", pop["refused_read_position"] not in positions,
                      "%s: an outcome was computed at read position %r, which the frozen file "
                      "lists as position_NOT_USED -- the INVALID naive probe at the concept token"
                      % (tag, pop["refused_read_position"]), bound=len(live) or 1)

        # ---- R4  JOIN TO THE BANK AND TO THE SPLIT. A verifier that never joins cannot see a
        #          bank substitution or a relabelled row.
        bank_idx, _ = load_bank_index(pr, spec["bank"], pop, bank_root)
        miss = [r["prompt_id"] for r in usable if r.get("prompt_id") not in bank_idx]
        rep.check("R4", not miss,
                  "%s: %d scored row(s) whose prompt_id is absent from the pinned bank %s -- the "
                  "population was swapped" % (tag, len(miss), spec["bank"]), bound=len(usable))
        drift, sha_bad = [], []
        for r in usable:
            b = bank_idx.get(r.get("prompt_id"))
            if b is None:
                continue
            if (b.get("cell") != spec["cell"] or b.get("query_kind") != pop["query_kind"]
                    or int(b.get("n_examples", -1)) != spec["n_examples"]
                    or b.get("domain") != r.get("domain")):
                drift.append(r.get("prompt_id"))
            if r.get("prompt_sha16") and b.get("prompt_sha16") and \
                    r["prompt_sha16"] != b["prompt_sha16"]:
                sha_bad.append(r.get("prompt_id"))
        rep.check("R4", not drift,
                  "%s: %d row(s) whose bank entry disagrees on cell/query_kind/dose/domain -- "
                  "population drift off the declared cell" % (tag, len(drift)), bound=len(usable))
        rep.check("R4", not sha_bad,
                  "%s: %d row(s) whose prompt_sha16 differs from the bank's" % (tag, len(sha_bad)),
                  bound=len(usable))
        off = sorted({r.get("domain") for r in usable} & set(pop["excluded_domains"]))
        rep.check("R4", not off,
                  "%s: rows from whole-population EXCLUDED domain(s) %s" % (tag, off),
                  bound=len(usable))
        unassigned = sorted({r.get("domain") for r in usable} - set(assign))
        rep.check("R4", not unassigned,
                  "%s: %d domain(s) absent from the frozen split manifest: %s"
                  % (tag, len(unassigned), unassigned[:4]), bound=len(usable))

        # ---- R9  THE OPTION SET, RE-DERIVED PER ROW FROM THE PINNED BANK AND THE PINNED POOL.
        #          Nothing here is imported from the producer: the expected contrast word comes
        #          from the bank row's own `query_surface` and, for a concept-query row, from the
        #          benign pool's `natural_word` for that row's own demonstration domain.
        if instrument:
            miss, wrong, dead = [], [], []
            for r in usable:
                b_ = bank_idx.get(r.get("prompt_id"))
                if b_ is None:
                    continue
                qs = b_.get("query_surface")
                got = r.get("semantic_contrast_word")
                if qs == "concept":
                    dom = b_.get("demo_pool_domain") or b_.get("domain")
                    want = ((instrument["pools"].get("%s|%s" % (dom, instrument["valence"]))
                             or {}).get("natural_word"))
                    if got is None:
                        miss.append(r.get("prompt_id"))
                    elif want is None or got != want:
                        wrong.append((r.get("prompt_id"), got, want))
                    if got is not None and str(got).lower() == str(b_.get("codeword", "")).lower():
                        dead.append(r.get("prompt_id"))
                elif qs == "codeword":
                    if got is not None and got != b_.get("codeword"):
                        wrong.append((r.get("prompt_id"), got, b_.get("codeword")))
            rep.check("R9", not miss,
                      "%s: %d concept-query row(s) carry no `semantic_contrast_word`, so the run "
                      "cannot show WHICH two words its forced choice was between"
                      % (tag, len(miss)), bound=len(usable))
            rep.check("R9", not wrong,
                      "%s: %d row(s) scored against the wrong contrast word, e.g. %s"
                      % (tag, len(wrong), wrong[:2]), bound=len(usable))
            rep.check("R9", not dead,
                      "%s: %d concept-query row(s) scored against the BANK CODEWORD, which occurs "
                      "zero times in their stimulus (n_codeword_occurrences == 0). One live "
                      "option is not a forced choice -- this is job 869869's defect exactly"
                      % (tag, len(dead)), bound=len(usable))

        row_hash_by_arm[tag] = sha256_rows(
            [{k: v for k, v in r.items() if k in ("prompt_id", "semantic_logodds",
                                                  "logp_concept", "logp_codeword")}
             for r in sorted(usable, key=lambda x: str(x.get("prompt_id")))])
        per_arm_ids[tag] = sorted(str(r.get("prompt_id")) for r in usable)

    # ---- R3  ANCHOR BY COPY, and the control band that is secretly n=1.
    dupes = collections.defaultdict(list)
    for tag, h in row_hash_by_arm.items():
        dupes[h].append(tag)
    collided = [v for v in dupes.values() if len(v) > 1]
    rep.check("R3", not collided,
              "arm(s) share a byte-identical scored-content hash: %s. A knockout arm that is a "
              "COPY of its baseline makes delta == 0 true by construction, and control draws that "
              "share an output hash are a control band that is secretly n=1 (published twice in "
              "this project, once with a fake between-draw sd of 0.0048)." % collided[:3],
              bound=len(row_hash_by_arm))
    n_draws = pop["n_control_draws"]
    k2 = sorted(t for t in row_hash_by_arm if "_k2_" in t)
    if k2:
        rep.check("R3", len({row_hash_by_arm[t] for t in k2}) == len(k2),
                  "the %d dose-matched nondemo control arms produce %d distinct output hashes; "
                  "the frozen file requires %d DISTINCT hashes"
                  % (len(k2), len({row_hash_by_arm[t] for t in k2}), n_draws), bound=len(k2))

    # ---- R8  EQUAL POPULATIONS ACROSS ARMS (P-N8): the ledgered prompt_ids must be replayed into
    #          every arm, or a delta is computed on two different populations.
    by_cell = collections.defaultdict(list)
    for tag in per_arm_ids:
        by_cell[(expected[tag]["bank"], expected[tag]["cell"],
                 expected[tag]["n_examples"])].append(tag)
    for key, tags in sorted(by_cell.items()):
        sets = {t: per_arm_ids[t] for t in tags}
        rep.check("R8", len({tuple(v) for v in sets.values()}) == 1,
                  "arms %s do not share one population: sizes %s. A delta computed on unequal "
                  "populations is void." % (sorted(sets), {t: len(v) for t, v in sets.items()}),
                  bound=len(tags))
    return rep


# ============================================================================================
# 4. A SYNTHETIC ARM TREE -- the only thing that exists to verify today
# ============================================================================================
def _synth_tree(pr, root, n_domains=4, rows_per_domain=2, banks=None, cells=None):
    """Build a CLEAN arm tree that satisfies every check, plus the bank and split it joins to.

    It is deliberately SMALL and the population numbers are overridden in a COPY of the frozen
    file: the point is to exercise the checks, and a fixture that reproduced the real 1130-row
    population would take minutes to build and would still be synthetic.
    """
    pop = declared_population(pr)
    banks = banks or ["button_bomb"]
    cells = cells or pop["cells"]
    pr2 = json.loads(json.dumps(pr))
    pr2["population"]["banks"] = {k: v for k, v in pr["population"]["banks"].items()
                                  if k in banks}
    pr2["split"]["n_domains_analysed"] = n_domains
    pr2["primary"]["n_domains_analysed"] = n_domains
    pr2["population"]["rows_per_domain_per_cell"] = rows_per_domain
    pr2["population"]["n_rows_per_bank_per_cell"] = n_domains * rows_per_domain
    pr2["split"]["manifest"] = "split.json"
    doms = ["dom%02d" % i for i in range(n_domains)]

    os.makedirs(root, exist_ok=True)
    with open(os.path.join(root, "split.json"), "w") as fh:
        json.dump({"assign": {d: ("train" if i % 3 else "test") for i, d in enumerate(doms)},
                   "field_name": pop["split_field"]}, fh)

    # DCS-PR-063 R9. A synthetic remap pool, so the CLEAN tree exercises the instrument check
    # rather than skipping it. `natural_word` is deliberately NOT any bank's codeword.
    synth_pool = {"_meta": {"content_sha16": None},
                  "pools": {"%s|benign" % d: {"domain": d, "valence": "benign",
                                              "natural_word": "carrot"} for d in doms}}
    pool_rel = os.path.join(root, "pool.json")
    with open(pool_rel, "w") as fh:
        json.dump(synth_pool, fh)
    synth_pool["_meta"]["content_sha16"] = sha16_file(pool_rel)
    with open(pool_rel, "w") as fh:
        json.dump(synth_pool, fh)
    instrument = {"amendment": "<synthetic>", "mode": "per_cell_remap", "valence": "benign",
                  "pool_path": pool_rel,
                  "pool_pinned_sha16": synth_pool["_meta"]["content_sha16"],
                  "pool_actual_sha16": synth_pool["_meta"]["content_sha16"],
                  "pools": synth_pool["pools"], "gate_scope": "per_cell_dose",
                  "gate_min_dose": 1}

    bank_rows, rng = {}, random.Random(20260908)
    for bank in banks:
        rel = "bank_%s.jsonl" % bank
        pr2["population"]["banks"][bank]["path"] = rel
        rows = []
        for cell in cells:
            for dose in sorted({pop["n_examples"], pop["n_examples_replication"],
                                pop["n_examples_null"]}):
                for d in doms:
                    for k in range(rows_per_domain):
                        pid = "%s_%s_%s_n%d_%d" % (bank, cell, d, dose, k)
                        rows.append({"prompt_id": pid,
                                     "prompt_sha16": hashlib.sha256(pid.encode()).hexdigest()[:16],
                                     "domain": d, "cell": cell, "condition": "synthetic",
                                     "query_kind": pop["query_kind"], "n_examples": dose,
                                     "codeword": bank.split("_")[0], "concept": bank.split("_")[1],
                                     # DCS-PR-063 R9: the fields the option set is re-derived from.
                                     "query_surface": ("concept" if cell in ("B", "E")
                                                       else "codeword"),
                                     "demo_pool_domain": d,
                                     "target_surface": "bomb"})
        with open(os.path.join(root, rel), "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        pr2["population"]["banks"][bank]["bank_file_sha16"] = sha16_file(
            os.path.join(root, rel))
        bank_rows[bank] = rows

    runs = os.path.join(root, "runs")
    os.makedirs(runs, exist_ok=True)
    tags = declared_arm_tags(declared_population(pr2))
    for tag, spec in tags.items():
        d = os.path.join(runs, tag + "_20260908T000000")
        os.makedirs(d, exist_ok=True)
        sel = [r for r in bank_rows[spec["bank"]]
               if r["cell"] == spec["cell"] and r["n_examples"] == spec["n_examples"]]
        with open(os.path.join(d, F_ROWS), "w") as fh:
            for r in sel:
                jitter = rng.random()  # distinct arms must not be byte-identical
                fh.write(json.dumps({
                    "prompt_id": r["prompt_id"], "prompt_sha16": r["prompt_sha16"],
                    "domain": r["domain"], "cell": r["cell"], "query_kind": r["query_kind"],
                    "n_examples": r["n_examples"], "readout": "semantic",
                    "knockout_scope": (pop["knockout_scope"] if spec["expect_enabled"] else ""),
                    "logp_concept": -1.0 + jitter, "logp_codeword": -2.0,
                    "semantic_logodds": 1.0 + jitter,
                    "option_mass_core_pair": 0.20,
                    # DCS-PR-063 R9.
                    "semantic_concept_word": r["concept"],
                    "semantic_contrast_word": ("carrot" if r["cell"] in ("B", "E")
                                               else r["codeword"]),
                    "semantic_options_source": ("benign_pool_natural_word"
                                                if r["cell"] in ("B", "E") else "bank_pair"),
                }) + "\n")
        with open(os.path.join(d, F_LIVENESS), "w") as fh:
            for i, r in enumerate(sel):
                fh.write(json.dumps({
                    "arm_id": tag, "prompt_id": r["prompt_id"],
                    "enabled": spec["expect_enabled"],
                    "hook_fired_count": 1 if spec["expect_enabled"] else 0,
                    "n_forward": 1,
                    "n_prefill_edits": 3 if spec["expect_enabled"] else 0,
                    "n_decode_edits": 0,
                    "keys_masked": 40 if spec["expect_enabled"] else 0,
                    "surface_span_n_tokens": 1,
                    "n_cells_edited_expected": 1 if spec["expect_enabled"] else 0,
                    "n_cells_edited_realised": 1 if spec["expect_enabled"] else 0,
                    "attn_implementation": pop["attn_impl"],
                    "seq_len": 200 + i, "rel_end": -10,
                    "resolved_absolute_index": 200 + i - 10,
                    "read_position": pop["read_position"],
                }) + "\n")
        with open(os.path.join(d, F_ARM), "w") as fh:
            json.dump({"arm_id": tag, **spec}, fh)
        with open(os.path.join(d, F_DONE), "w") as fh:
            json.dump({"ok": True, "n_rows": len(sel)}, fh)

    summary = {k: None for k in DECLARED_SUMMARY_KEYS}
    summary["independence_unit"] = declared_population(pr2)["independence_unit"]
    return pr2, runs, root, summary, instrument


# ============================================================================================
# 5. SELF-TEST
# ============================================================================================
def selftest(pr):
    ok = True

    def say(name, good, detail=""):
        nonlocal ok
        ok = ok and good
        print("  %-5s %s%s" % ("PASS" if good else "FAIL", name,
                               (" -- " + detail) if detail else ""))

    ind = assert_independent_of_analyzer()
    say("independence: this verifier imports nothing from the analyzer", ind["ok"], ind["source"])

    pop = declared_population(pr)
    say("the frozen file binds a population", pop["n_domains"] > 0 and bool(pop["banks"]),
        "n_domains=%d banks=%d cells=%s" % (pop["n_domains"], len(pop["banks"]), pop["cells"]))
    say("the selector field is `cell`, never `condition` (A-039)",
        pop["selector_field"] == "cell")
    say("the declared arm set is non-empty and is derived HERE",
        len(declared_arm_tags(pop)) > 0, "%d arm tag(s)" % len(declared_arm_tags(pop)))
    say("the independence unit is the domain (row-level FPR 0.2000)",
        str(pop["independence_unit"]).lower() not in FORBIDDEN_UNITS,
        repr(pop["independence_unit"]))
    say("row arithmetic is self-consistent in the frozen file",
        pop["n_rows_per_bank_per_cell"] == pop["n_domains"] * pop["rows_per_domain_per_cell"],
        "%d == %d x %d" % (pop["n_rows_per_bank_per_cell"], pop["n_domains"],
                           pop["rows_per_domain_per_cell"]))

    tmp = tempfile.mkdtemp(prefix="pr058_verifier_selftest_")
    try:
        pr2, runs, root, summary, inst = _synth_tree(pr, os.path.join(tmp, "clean"))
        rep = verify(pr2, runs, bank_root=root, split_root=root, producer_summary=summary,
                     instrument=inst)
        say("a CLEAN synthetic arm tree passes every check", not rep.failed,
            "failing=%s" % rep.failed)

        # An empty run root must FAIL R5, never pass vacuously.
        empty = os.path.join(tmp, "empty")
        os.makedirs(empty, exist_ok=True)
        rep2 = verify(pr2, empty, bank_root=root, split_root=root, instrument=inst)
        say("an EMPTY run root fails R5 rather than passing vacuously", "R5" in rep2.failed,
            "failing=%s" % rep2.failed)

        # A check that binds zero rows is EMPTY, not PASS.
        r3 = Report()
        r3.check("Rx", True, "bound nothing", bound=0)
        say("a check bound to ZERO rows is EMPTY, never PASS", r3.failed == ["Rx"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("[self-test] %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


# ============================================================================================
# 6. MUTATION HARNESS -- a verifier that has never been shown to fail is not evidence
# ============================================================================================
def _rows_of(d):
    return read_jsonl(os.path.join(d, F_ROWS))


def _write_rows(d, rows):
    with open(os.path.join(d, F_ROWS), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def _some_arm(runs, needle="_k1_"):
    hits = sorted(x for x in glob.glob(os.path.join(runs, "*")) if needle in os.path.basename(x))
    if not hits:
        hits = sorted(glob.glob(os.path.join(runs, "*")))
    return hits[0]


def _live(d):
    return read_jsonl(os.path.join(d, F_LIVENESS))


def _write_live(d, recs):
    with open(os.path.join(d, F_LIVENESS), "w") as fh:
        for r in recs:
            fh.write(json.dumps(r) + "\n")


def _mutations():
    """(id, target_check, description, fn(runs_root, repo_root)) -- each MUST be caught."""

    def X1(runs, root):
        d = _some_arm(runs)
        rows = _rows_of(d)
        for r in rows[1:]:
            r["semantic_logodds"] = None
        _write_rows(d, rows)

    def X2(runs, root):
        d = _some_arm(runs)
        rows = _rows_of(d)
        for r in rows:
            r["cell"] = "A"
        _write_rows(d, rows)

    def X3(runs, root):
        a = _some_arm(runs, "_k1_")
        b = _some_arm(runs, "_k2_")
        _write_rows(b, _rows_of(a))

    def X4(runs, root):
        d = _some_arm(runs)
        rows = _rows_of(d)
        for r in rows:
            r["prompt_id"] = "not_in_any_bank_" + str(r["prompt_id"])
        _write_rows(d, rows)

    def X5(runs, root):
        d = _some_arm(runs)
        rows = _rows_of(d)
        for r in rows:
            r["domain"] = "a_domain_the_split_never_heard_of"
        _write_rows(d, rows)

    def X6(runs, root):
        d = sorted(glob.glob(os.path.join(runs, "*")))[0]
        os.remove(os.path.join(d, F_DONE))

    def X7(runs, root):
        for d in sorted(glob.glob(os.path.join(runs, "*"))):
            if "_k5_" in os.path.basename(d):
                shutil.rmtree(d)

    def X8(runs, root):
        d = _some_arm(runs, "_k2_")
        recs = _live(d)
        for r in recs:
            r["attn_implementation"] = "sdpa"
        _write_live(d, recs)

    def X9(runs, root):
        d = _some_arm(runs, "_k2_")
        recs = _live(d)
        for r in recs:
            r["hook_fired_count"] = 0
        _write_live(d, recs)

    def X10(runs, root):
        d = _some_arm(runs, "_k2_")
        recs = _live(d)
        recs[0]["n_decode_edits"] = 1
        _write_live(d, recs)

    def X11(runs, root):
        d = _some_arm(runs, "_k2_")
        recs = _live(d)
        for r in recs:
            r["surface_span_n_tokens"] = 0
        _write_live(d, recs)

    def X12(runs, root):
        d = _some_arm(runs, "_k2_")
        recs = _live(d)
        for r in recs:
            r["resolved_absolute_index"] = 190      # a CONSTANT absolute index
        _write_live(d, recs)

    def X13(runs, root):
        d = _some_arm(runs, "_k2_")
        recs = _live(d)
        for r in recs:
            r["read_position"] = "codeword_last"    # the refused naive probe
        _write_live(d, recs)

    def X14(runs, root):
        d = _some_arm(runs, "_k1_")
        rows = _rows_of(d)
        _write_rows(d, rows[:-3])                   # unequal populations across arms

    def X15(runs, root):
        for f in sorted(glob.glob(os.path.join(root, "bank_*.jsonl"))):
            with open(f, "a") as fh:
                fh.write(json.dumps({"prompt_id": "planted", "domain": "dom00"}) + "\n")

    def X16(runs, root):
        d = _some_arm(runs, "_k2_")
        recs = _live(d)
        for r in recs:
            r["n_cells_edited_realised"] = 0
        _write_live(d, recs)

    def X17(runs, root):
        # DCS-PR-063. The cells-B/E rows are put back on the PRE-AMENDMENT answer set: the second
        # option becomes the bank codeword, which occurs zero times in their own stimulus. This is
        # job 869869's defect, replayed, and R1-R8 all pass on it.
        for d in sorted(glob.glob(os.path.join(runs, "*"))):
            if not ("_b_" in os.path.basename(d) or "_e_" in os.path.basename(d)):
                continue
            rows = _rows_of(d)
            if not rows:
                continue
            for r in rows:
                r["semantic_contrast_word"] = "button"
                r["semantic_options_source"] = "bank_pair"
            _write_rows(d, rows)
            return

    def X18(runs, root):
        # The rows do not say what they were scored against at all.
        for d in sorted(glob.glob(os.path.join(runs, "*"))):
            if not ("_b_" in os.path.basename(d) or "_e_" in os.path.basename(d)):
                continue
            rows = _rows_of(d)
            if not rows:
                continue
            for r in rows:
                r.pop("semantic_contrast_word", None)
            _write_rows(d, rows)
            return

    return [
        ("X1  silent denominator: null the readout on all but one row", "R1", X1),
        ("X2  arm identity: relabel every row into cell A", "R2", X2),
        ("X3  anchor by copy: the K2 control becomes a byte-copy of the baseline", "R3", X3),
        ("X4  population swap: prompt_ids that join to no bank row", "R4", X4),
        ("X5  population drift: a domain the split manifest never assigned", "R4", X5),
        ("X6  partial run: DONE.json removed, results.jsonl left judgeable", "R5", X6),
        ("X7  producer picks arms: delete a declared arm that was complete", "R5", X7),
        ("X8  SDPA on the loaded config -- the silent no-op", "R6", X8),
        ("X9  dead hook: hook_fired_count == 0 on every row", "R6", X9),
        ("X10 scope leak: n_decode_edits != 0 on a prefill-only scope", "R6", X10),
        ("X11 zero realised dose: the arm cut nothing", "R6", X11),
        ("X12 absolute index reused across differing sequence lengths", "R6", X12),
        ("X13 an outcome computed at the REFUSED concept-token read site", "R6", X13),
        ("X14 unequal populations across arms of one cell", "R8", X14),
        ("X15 bank substitution: the pinned file sha16 no longer matches", "R4", X15),
        ("X16 realised != expected cells", "R6", X16),
        ("X17 cells B/E scored against the BANK CODEWORD (job 869869's defect)", "R9", X17),
        ("X18 the rows do not record which two words the forced choice was between", "R9", X18),
    ]


def mutate(pr):
    base = tempfile.mkdtemp(prefix="pr058_verifier_mutate_")
    n_red = 0
    muts = _mutations()
    try:
        for name, target, fn in muts:
            root = os.path.join(base, re.sub(r"\W+", "_", name)[:40])
            pr2, runs, root, summary, inst = _synth_tree(pr, root)
            rep0 = verify(pr2, runs, bank_root=root, split_root=root, producer_summary=summary,
                          instrument=inst)
            if rep0.failed:
                print("  SETUP-FAIL %s -- the clean fixture already fails %s"
                      % (name, rep0.failed))
                continue
            fn(runs, root)
            rep = verify(pr2, runs, bank_root=root, split_root=root, producer_summary=summary,
                         instrument=inst)
            caught = target in rep.failed
            n_red += bool(caught)
            print("  %-5s %-70s -> %s (failing: %s)"
                  % ("RED" if caught else "GREEN", name, target, rep.failed or "none"))
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print("[mutate] %d/%d mutations were CAUGHT BY THE NAMED CHECK" % (n_red, len(muts)))
    if n_red != len(muts):
        print("  A MUTATION THAT IS NOT CAUGHT MEANS THAT CHECK CANNOT FAIL.", file=sys.stderr)
        return 1
    return 0


# ============================================================================================
# 7. MAIN
# ============================================================================================
def main():
    ap = argparse.ArgumentParser(description="DCS-PR-058 PHASE 10 independent verifier")
    ap.add_argument("--prereg", default=PREREG_DEFAULT)
    ap.add_argument("--runs", default="outputs/boombness/score_behavior")
    ap.add_argument("--banks", default=None,
                    help="comma-list of bank keys to expect on disk. Default: ALL SIX declared "
                         "banks, including the REGISTERED DESCRIPTIVE knife/gun arms, which the "
                         "frozen file says are run and reported. The analyzer's own manifest "
                         "defaults to the two confirmatory bomb banks; see declared_arm_tags().")
    ap.add_argument("--producer-summary", default=None,
                    help="the analyzer's own JSON summary, checked for OMISSION (R5)")
    ap.add_argument("--amendment", default=AMENDMENT_DEFAULT,
                    help="DCS-PR-063 amendment declaring the per-cell answer set (R9). If it is "
                         "absent from disk R9 binds nothing and reports EMPTY, never PASS.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--mutate", action="store_true")
    a = ap.parse_args()

    try:
        assert_independent_of_analyzer()
        pr = load_prereg(a.prereg)
        if a.self_test:
            return selftest(pr)
        if a.mutate:
            return mutate(pr)
        root = a.runs if os.path.isdir(a.runs) else os.path.join(REPO, a.runs)
        summary = None
        if a.producer_summary:
            with open(a.producer_summary) as fh:
                summary = json.load(fh)
        print("=== %s PHASE 10 independent verification ===" % PR_ID)
        bl = [b.strip() for b in a.banks.split(",")] if a.banks else None
        pop = declared_population(pr)
        tags = declared_arm_tags(pop, bl)
        print("  expecting %d arm(s) over bank(s) %s (the analyzer's manifest defaults to the two "
              "confirmatory bomb banks; this derivation is independent -- see declared_arm_tags)"
              % (len(tags), sorted({v["bank"] for v in tags.values()})))
        inst = declared_instrument(a.amendment)
        if inst is None:
            print("  R9 EMPTY: amendment %r is not on disk, so the option set cannot be "
                  "re-derived. R9 will NOT report PASS." % a.amendment)
        else:
            print("  R9 instrument: mode=%s valence=%s pool=%s sha16=%s gate=%s/min_dose=%s"
                  % (inst["mode"], inst["valence"], os.path.basename(inst["pool_path"]),
                     inst["pool_actual_sha16"], inst["gate_scope"], inst["gate_min_dose"]))
        rep = verify(pr, root, producer_summary=summary, banks=bl, instrument=inst)
        rep.render()
        return 0 if not rep.failed else 1
    except VerifierError as e:
        print("REFUSED: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
