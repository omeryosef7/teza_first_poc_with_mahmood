#!/usr/bin/env python3
"""`DCS-PR-059` PHASE 11 -- the INDEPENDENT verifier. Checklist item **U7**.

⛔ THIS FILE IMPORTS NOTHING FROM `scripts/dcs_ts_pr059_localisation.py`, and that is the whole
point of it. A verifier that reuses the analyzer's parsers, its scope table, its arm-tag builder or
its draw function does not verify the analyzer -- it re-runs it and agrees with itself. Every
quantity below is RE-DERIVED here: the frozen preregistration is read with `json.load` and parsed
by this file's own offset parser, the scope family is re-read from `scopes.family`, the arm tags
are re-built from a rule stated here, the random-row draws are re-drawn here from `seeds`, and the
outcome rows are re-counted out of each arm directory's `results.jsonl`. Where this file and the
analyzer agree, two independent derivations agree; where they disagree, one of them is wrong and
the disagreement is the finding.

The only shared objects are the FROZEN CONFIG (a data file, not code) and the ARM DIRECTORIES.

WHAT IT CLOSES. `scripts/dcs_verify_kladder_rowlevel.py` names five check classes, distilled from
an adversarial red-team of the first K-ladder verifier. Their CODE cannot be reused -- it binds
`PR-032`'s `dcsk*` directories, `EXPECT_N = 380` and a rung set this phase does not have -- but
their CLASSES are exactly the ones that matter here, so they are re-implemented against this
population and keep their names:

  R1 SILENT DENOMINATOR   the outcome nulled on most rows while the line count and DONE.json are
                          untouched, so a delta computed over 113 readouts is reported as 1130.
  R2 ROW-LEVEL IDENTITY   arm directories swapped, or one arm's rows copied into another's, with
                          all the directory furniture intact. Rows carry the arm they were SCORED
                          under, so the rows are asked, not the directory name.
  R3 ANCHOR / BAND BY COPY  a "band" of three control draws whose outputs are byte-identical --
                          this project has twice published a control band that was secretly n=1.
  R4 POPULATION SWAP/DRIFT  the scored rows do not join the declared bank, or were relabelled off
                          the declared cell / channel / dose.
  P5 CANNOT ANSWER AS AN ESCAPE HATCH  an arm complete on disk is dropped from the producer's
     `arms` under a CANNOT ANSWER label this verifier cannot re-derive -- or, in the other
     direction, an arm this verifier CAN re-derive as below the option-mass gate is reported as
     an ordinary result. DCS-PR-065 lets a below-gate arm be omitted from `arms`; P5 is what
     stops that permission from becoming a way to omit anything.
  R5 VACUOUS BY OMISSION  the producer reports less and the comparisons evaporate instead of
                          failing. THE EXPECTED ARM SET IS DECLARED HERE, in `expected_arms()`,
                          from the frozen file -- never iterated out of the producer's own keys.

And four classes that are specific to PHASE 11 and have no K-ladder ancestor:

  P1 REALISED != DECLARED  the defect this entire phase exists to fix. For every scored row,
                           `surface_span_positions` must equal `seq_len + rel_end` for the arm's
                           DECLARED offsets, and the decoded tokens must be persisted. An absolute
                           index that happens to be right on the first prompt and wrong on the rest
                           is invisible in a mean and obvious here.
  P2 DEAD OR LEAKY HOOK    `n_prefill_edits > 0` and `n_decode_edits == 0` on every row, and
                           `eager` ON THE LOADED CONFIG. Under SDPA the additive mask edit is
                           discarded and the arm scores as a clean null.
  P3 WRONG CHANNEL         a `semantic_forced_choice` number reported as a mechanism result. That
                           channel names the answer in its own question on 100% of rows; the
                           frozen file calls it SECONDARY DISPLAY ONLY.
  P4 PR059-D1              `S_D` (22 rows) and `S_E` (23) leave pools of 6 and 5 in a 28-row query
                           span, so their dose-matched random-row control is ARITHMETICALLY
                           IMPOSSIBLE. A directory claiming to be one is a SMALLER draw wearing the
                           label "dose-matched", and it is refused by name rather than accepted.

USAGE
    python3 scripts/dcs_ts_pr059_verifier.py --self-test
    python3 scripts/dcs_ts_pr059_verifier.py --mutate
    python3 scripts/dcs_ts_pr059_verifier.py --producer outputs/.../pr059_localisation.json

CPU only. Reads no GPU, submits nothing, and writes only inside its own temp sandbox.
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import io
import json
import os
import random
import re
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# =============================================================================================
# 0. DECLARED HERE -- so the producer cannot make this verifier vacuous by reporting less
# =============================================================================================
#: The frozen preregistration. Read as DATA with `json.load`; nothing in `scripts/` is imported to
#: read it, so a bug in a shared loader cannot make the design and the check agree by construction.
PREREG = "configs/dcs_ts_pr059_phase11.json"

#: The producer's own output, when it exists. `R5` iterates THIS FILE'S expected set against it,
#: never the other way round.
DEFAULT_PRODUCER = "outputs/dcs_ts/pr059_localisation.json"

#: Where score_behavior writes its run directories, and where the committed argsfiles live.
DEFAULT_ARM_ROOT = "outputs/boombness/score_behavior"
DEFAULT_ARGSROOT = "runargs"

#: THE CONFIRMATORY BANKS. Stated here rather than fetched from a `confirmatory` field, and
#: cross-checked against `population.banks` by `V0`: a verifier that learns which banks matter from
#: the same sentence the producer reads has not checked anything.
DECLARED_CONFIRMATORY_BANKS = ("button_bomb", "basket_bomb")

#: The declared population of every arm in this phase. `population.cell`, `query_kind_primary`,
#: `n_examples_primary`. NOT `condition` -- `population._cell_note` records that selecting on
#: `condition == 'natural_doublespeak'` selects the wrong rows.
DECLARED_POPULATION = {"cell": "C", "query_kind": "semantic_one_word", "n_examples": 4}

#: `population.query_kind_display`. Any arm on this channel is DISPLAY ONLY (P3).
FORBIDDEN_MECHANISM_CHANNEL = "semantic_forced_choice"

#: The scopes that get a dose-matched random-row control, and the ones that provably cannot.
#: Re-derived by `expected_arms()` from the span and the scope sizes -- these two tuples are the
#: ANSWER this file expects to re-derive, kept so `V0` can refuse when the frozen file has moved
#: underneath a verifier that still believes them.
EXPECT_RANDOM_ROW_CONSTRUCTIBLE = ("S_A", "S_C", "S_F", "S_F2")
EXPECT_RANDOM_ROW_IMPOSSIBLE_D1 = ("S_D", "S_E", "S_G")

#: Every block the producer must carry. A missing block is `R5`, not a skipped check.
DECLARED_PRODUCER_KEYS = ("scopes", "arms", "family", "reference", "controls", "liveness",
                          "population", "channel")

CHECK_IDS = ("V0", "R1", "R2", "R3", "R4", "R5", "P1", "P2", "P3", "P4", "P5")


# =============================================================================================
# 1. THIS FILE'S OWN PARSERS -- deliberately not the analyzer's
# =============================================================================================
def parse_offsets(spec):
    """`[-28..-6] minus [-10]`, `[-5,-4]`, `"-28..-1"`, `[-9]` -> a sorted list of offsets.

    The frozen file states its scopes in three different shapes (a JSON list, a range string, and
    a range string with an exclusion clause), and this parser handles all three FROM SCRATCH. It
    refuses a non-negative offset for the same reason everything else in this phase does:
    `token_map._absolute_indices_are_void`.
    """
    if isinstance(spec, (list, tuple)):
        vals = [int(x) for x in spec]
    else:
        txt = str(spec)
        keep, drop = [], []
        # "minus" splits the expression into an INCLUDE part and one or more EXCLUDE parts.
        for i, part in enumerate(txt.split("minus")):
            cur = keep if i == 0 else drop
            body = part.replace("[", " ").replace("]", " ").replace(",", " ")
            for tok in body.split():
                tok = tok.strip()
                if not tok:
                    continue
                if ".." in tok:
                    a, b = tok.split("..", 1)
                    try:
                        a, b = int(a), int(b)
                    except ValueError:
                        continue
                    if a > b:
                        a, b = b, a
                    cur.extend(range(a, b + 1))
                else:
                    try:
                        cur.append(int(tok))
                    except ValueError:
                        continue
        vals = [v for v in keep if v not in set(drop)]
    bad = sorted(v for v in vals if v >= 0)
    if bad:
        raise ValueError("ABSOLUTE INDEX REFUSED in %r: %s are not negative" % (spec, bad))
    return sorted(set(vals))


def load_prereg(path=PREREG):
    fp = path if os.path.isabs(path) else os.path.join(REPO, path)
    with open(fp) as f:
        return json.load(f)


def scope_table(cfg):
    """`scope id -> sorted rel_end offsets`, re-parsed here from `scopes.family`."""
    out = collections.OrderedDict()
    for s in cfg["scopes"]["family"]:
        out[str(s["id"])] = parse_offsets(s.get("rel_end_rows", []))
    return out


def query_span_offsets(cfg):
    """The whole query span, re-derived from `token_map.rel_end_layout`'s KEYS."""
    rows = []
    for key in cfg["token_map"]["rel_end_layout"]:
        rows.extend(parse_offsets(str(key)))
    return sorted(set(rows))


def reference_scope_id(cfg):
    """The REFERENCE scope (the denominator), re-derived HERE and not read off a key.

    The reference is defined by WHAT IT COVERS -- it is the family scope whose row set IS the
    whole query span -- so it is recomputed from `scopes.family` and `token_map.rel_end_layout`
    rather than taken from any field the analyzer also reads. Two files agreeing because they
    read the same string is not two derivations.
    """
    span = set(query_span_offsets(cfg))
    hits = [sid for sid, rel in scope_table(cfg).items() if rel and set(rel) == span]
    if len(hits) != 1:
        raise SystemExit("[pr059-verifier] REFUSING: %d scope(s) cover the whole %d-row query "
                         "span (%s); the denominator of every fraction this phase reports is "
                         "not identifiable." % (len(hits), len(span), hits))
    return hits[0]


def _draw_seed(seed, scope_id, draw_index):
    """The same three fields, hashed the same way the producer hashes them -- and written out
    here rather than imported, so 'the draw is reproducible' is a claim two files make
    independently instead of one file making it twice."""
    h = hashlib.sha256(("%d|%s|%d" % (int(seed), str(scope_id), int(draw_index))).encode())
    return int.from_bytes(h.digest()[:8], "big")


def redraw_random_rows(cfg, scope_id, rel_end, draw_index):
    """Re-draw one dose-matched random-row control. Returns None when it is NOT CONSTRUCTIBLE."""
    span = query_span_offsets(cfg)
    own = set(int(x) for x in rel_end)
    m = len(own)
    pool = [r for r in span if r not in own]
    if m <= 0 or len(pool) < m:
        return None
    rng = random.Random(_draw_seed(int(cfg["seeds"]["random_row_draws"]), scope_id, draw_index))
    return sorted(rng.sample(pool, m))


def arm_tag(bank, scope_id, kind, draw=None):
    """The arm-directory tag, built from a rule STATED HERE.

    `R5` compares this file's expected tags against what is on disk and what the producer
    reported. If the producer names its arms differently, the mismatch is the finding -- a
    verifier that adopts the producer's naming can never notice a missing arm.
    """
    base = "pr059_%s_%s_%s" % (bank, scope_id.lower(), kind)
    if draw is not None:
        base += str(int(draw))
    return base + "_n4"


def expected_arms(cfg, banks=DECLARED_CONFIRMATORY_BANKS):
    """THE EXPECTED ARM SET. Declared here, re-derived from the frozen file, never from the
    producer.

    One baseline and one reference scope per bank; one arm per family member; and for each scope
    the two REQUIRED controls -- the dose-matched RANDOM-ROW draws (`n_random_row_draws` of them,
    and only where constructible: `P4`) and the NON-DEMONSTRATION KEY draws (`n_nondemo_draws`).
    """
    scopes = scope_table(cfg)
    ref = reference_scope_id(cfg)
    n_rr = int(cfg["seeds"]["n_random_row_draws"])
    n_nd = int(cfg["seeds"]["n_nondemo_draws"])
    arms = collections.OrderedDict()

    def add(bank, scope_id, kind, draw=None, rel_end=None, required=True):
        tag = arm_tag(bank, scope_id, kind, draw)
        arms[tag] = {"tag": tag, "bank": bank, "scope_id": scope_id, "kind": kind,
                     "draw": draw, "rel_end": (list(rel_end) if rel_end else []),
                     "required": bool(required)}

    for bank in banks:
        add(bank, "S_0", "baseline", rel_end=[])
        # ---- PR059-D5, RESOLVED HERE (this file was the wrong one, for the -2) --------------
        # `nulls_required` L-N1 -- "disabled-hook bridge", `blocking: true` -- is a DECLARED,
        # BLOCKING arm of this design, and it has to be RUN to be reported: it is the arm that
        # shows the intervention code path is inert with the hook off. The analyzer's manifest
        # carried one bridge arm per bank; this expected set did not know about it, so a complete
        # run would have been reported as containing two "arms nobody preregistered". The analyzer
        # was right about these two. Declared HERE, from `nulls_required`, and not adopted from
        # the producer's naming -- a verifier that takes its arm set from the thing it verifies
        # can never notice a missing arm.
        if any(str(n.get("id")) == "L-N1" for n in cfg.get("nulls_required", [])):
            add(bank, ref, "bridge", rel_end=scopes.get(ref, []))
        for sid, rel in scopes.items():
            if sid == "S_0" or not rel:
                continue                       # S_0 has no rows; S_B is UNCONSTRUCTIBLE
            add(bank, sid, "scope", rel_end=rel)
            for d in range(n_nd):
                add(bank, sid, "nondemo_control", d, rel_end=rel)
            for d in range(n_rr):
                rr = redraw_random_rows(cfg, sid, rel, d)
                if rr is None:
                    continue                   # PR059-D1: not constructible; NOT an expected arm
                add(bank, sid, "random_row_control", d, rel_end=rr)
    return arms


# =============================================================================================
# 2. READING ARM DIRECTORIES -- re-derived, never taken from a producer summary
# =============================================================================================
def option_mass_gate_from_cfg(cfg):
    """THIS FILE'S OWN parse of the option-mass gate, out of the frozen file's own prose. The
    analyzer has its own; that they agree is the point of having two."""
    texts = []
    for path in (("outcome_variables", "O1_semantic_readout", "cannot_answer_if"),
                 ("primary", "cannot_answer"), ("kill_condition",)):
        node = cfg
        for k in path:
            node = (node or {}).get(k) if isinstance(node, dict) else None
        if isinstance(node, str):
            texts.append(node)
    for t in texts:
        m = re.search(r"below the (0?\.\d+) gate", t) or re.search(
            r"option_mass\s+below\s+the\s+(0?\.\d+)", t)
        if m:
            return float(m.group(1))
    raise SystemExit("[pr059-verifier] REFUSING: no option_mass gate could be parsed out of the "
                     "frozen preregistration's own prose. A gate this file cannot read is a gate "
                     "it cannot check.")


def arm_median_option_mass(run_dir, cfg):
    """The arm's TRUE median option mass, re-derived from its own summary.json. Returns None when
    the readout is ABSENT (no summary, no block, NaN) -- absent is not low, and an absent
    measurement is never dispositioned as a disengaged channel."""
    if not run_dir:
        return None
    fp = os.path.join(run_dir, "summary.json")
    if not os.path.exists(fp):
        return None
    try:
        summ = json.load(open(fp))
    except ValueError:
        return None
    chan = ((cfg.get("population") or {}).get("query_kind_primary")
            or (cfg.get("population") or {}).get("primary_channel")
            or "semantic_one_word")
    blocks = summ.get("option_mass") or {}
    key = next((k for k in blocks if k.endswith("/" + chan)), None)
    if key is None:
        return None
    blk = blocks[key] or {}
    if blk.get("n_nan"):
        return None
    v = blk.get("median_true")
    return None if v is None else float(v)


def newest_done(root, tag):
    for h in reversed(sorted(glob.glob(os.path.join(root, tag + "_*")))):
        if os.path.exists(os.path.join(h, "DONE.json")):
            return h
    return None


def read_rows(d):
    p = os.path.join(d, "results.jsonl")
    if not os.path.exists(p):
        return None
    out = []
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def read_json(d, name):
    p = os.path.join(d, name)
    if not os.path.exists(p):
        return None
    try:
        with open(p) as f:
            return json.load(f)
    except (ValueError, OSError):
        return None


def file_sha(d, name="results.jsonl"):
    p = os.path.join(d, name)
    if not os.path.exists(p):
        return None
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


def argsfile_flag(argsroot, tag, flag):
    """The value of `flag` in the committed argsfile for `tag`, or None.

    The argsfile is a THIRD source: the row says what was scored, the summary says what the run
    thought it did, and the argsfile says what was asked for. A defect that keeps two of the three
    consistent is common; keeping all three consistent is not.
    """
    for cand in (os.path.join(argsroot, tag + ".args"), os.path.join(argsroot, tag + ".txt"),
                 os.path.join(REPO, argsroot, tag + ".args"),
                 os.path.join(REPO, argsroot, tag + ".txt")):
        if os.path.exists(cand):
            toks = open(cand).read().split()
            if flag in toks:
                i = toks.index(flag)
                return toks[i + 1] if i + 1 < len(toks) else ""
            return None
    return None


# =============================================================================================
# 3. THE VERIFIER
# =============================================================================================
def verify(cfg, arm_root, producer_path, bank_dir, argsroot, banks=DECLARED_CONFIRMATORY_BANKS):
    fails, notes = [], []

    def check(cid, ok, why):
        if not ok:
            fails.append(cid)
            notes.append("  %-3s FAIL  %s" % (cid, why))
        return ok

    # ---- V0 -- IS THIS VERIFIER STILL BOUND TO THE DESIGN IT WAS WRITTEN AGAINST? -----------
    # Everything below is derived from `cfg`, so a `cfg` that has moved makes the derivations
    # right and the CONSTANTS at the top of this file wrong. Checked first, and loudly.
    check("V0", str(cfg.get("status", "")).upper() == "FROZEN",
          "the preregistration's status is %r, not FROZEN; a design that can still move is not "
          "something a verifier can bind" % cfg.get("status"))
    cfg_banks = set(cfg.get("population", {}).get("banks", {}))
    check("V0", set(banks) <= cfg_banks,
          "this verifier expects banks %s but the frozen file declares %s; the verifier is bound "
          "to a population that no longer exists" % (sorted(banks), sorted(cfg_banks)))
    for field, want in DECLARED_POPULATION.items():
        got = {"cell": cfg.get("population", {}).get("cell"),
               "query_kind": cfg.get("population", {}).get("query_kind_primary"),
               "n_examples": cfg.get("population", {}).get("n_examples_primary")}[field]
        check("V0", got == want,
              "this verifier's declared population %s=%r disagrees with the frozen file's %r"
              % (field, want, got))
    scopes = scope_table(cfg)
    span = query_span_offsets(cfg)
    check("V0", len(span) == 28,
          "the query span re-derived from token_map.rel_end_layout is %d rows, not the 28 this "
          "verifier's PR059-D1 arithmetic assumes" % len(span))
    got_ok = tuple(sid for sid in scopes
                   if scopes[sid] and redraw_random_rows(cfg, sid, scopes[sid], 0) is not None)
    got_no = tuple(sid for sid in scopes
                   if scopes[sid] and redraw_random_rows(cfg, sid, scopes[sid], 0) is None)
    check("V0", got_ok == EXPECT_RANDOM_ROW_CONSTRUCTIBLE,
          "the scopes with a CONSTRUCTIBLE dose-matched random-row control re-derive as %s, not "
          "the %s this verifier declares" % (list(got_ok), list(EXPECT_RANDOM_ROW_CONSTRUCTIBLE)))
    check("V0", got_no == EXPECT_RANDOM_ROW_IMPOSSIBLE_D1,
          "the scopes whose dose-matched control is ARITHMETICALLY IMPOSSIBLE re-derive as %s, "
          "not the %s this verifier declares as PR059-D1"
          % (list(got_no), list(EXPECT_RANDOM_ROW_IMPOSSIBLE_D1)))

    exp = expected_arms(cfg, banks)
    n_rows_expected = int(cfg["population"]["n_rows_per_bank"])
    n_domains_expected = len(parse_domains(cfg))

    # ---- R5 -- COVERAGE, EVALUATED FIRST ---------------------------------------------------
    prod = None
    if producer_path and os.path.exists(producer_path):
        try:
            prod = json.load(open(producer_path))
        except ValueError:
            prod = None
        check("R5", prod is not None,
              "the producer output %s is not valid JSON" % producer_path)
    if prod is not None:
        missing = [k for k in DECLARED_PRODUCER_KEYS if k not in prod]
        check("R5", not missing,
              "the producer omits declared block(s) %s. A verifier that iterates the producer's "
              "own keys goes VACUOUS when a block is deleted; this one iterates its own."
              % missing)
        reported = set(prod.get("arms", {}) or {})
        on_disk = {t for t in exp if newest_done(arm_root, t)}
        # ---- P5 -- DCS-PR-065's one permitted omission, and its price -----------------------
        # An arm whose median option mass is below the declared gate is CANNOT ANSWER, so it does
        # not appear in `arms` as a result. That permission is the ONLY reason a complete arm may
        # be missing, and it is honoured here ONLY where THIS verifier can re-derive the shortfall
        # from the arm's OWN summary.json -- never from the producer saying so. Re-derived with
        # this file's own gate parse and its own median, sharing no code with the analyzer.
        declared_ca = dict((prod.get("cannot_answer_arms") or {})) \
            if isinstance(prod.get("cannot_answer_arms"), dict) \
            else {str(x.get("arm_id") or x.get("tag")): x
                  for x in (prod.get("cannot_answer_arms") or [])}
        gate_v = option_mass_gate_from_cfg(cfg)
        rederived_below, rederived_above = set(), set()
        for t in sorted(on_disk):
            m = arm_median_option_mass(newest_done(arm_root, t), cfg)
            if m is None:
                continue
            (rederived_below if m < gate_v else rederived_above).add(t)
        # (a) an omission this verifier CANNOT re-derive as below-gate is R5, exactly as before.
        dropped = sorted(on_disk - reported - rederived_below)
        check("R5", not dropped,
              "arm(s) %s are COMPLETE on disk and absent from the producer's `arms`; the producer "
              "chose its own arm set" % dropped[:8])
        # (b) an omission this verifier CAN re-derive must still be DECLARED as CANNOT ANSWER.
        #     Silently missing and correctly missing are not the same thing.
        undeclared = sorted((rederived_below & on_disk) - reported - set(declared_ca))
        check("P5", not undeclared,
              "arm(s) %s are below the option-mass gate (%.4g) on their OWN summary.json and are "
              "absent from BOTH the producer's `arms` and its `cannot_answer_arms`. DCS-PR-065 "
              "permits a below-gate arm to be omitted from `arms`; it does not permit it to "
              "vanish." % (undeclared[:8], gate_v))
        # (c) the reverse laundering: an arm this verifier re-derives as ABOVE the gate may not be
        #     labelled CANNOT ANSWER to make an inconvenient result disappear.
        false_ca = sorted(set(declared_ca) & rederived_above)
        check("P5", not false_ca,
              "arm(s) %s are declared CANNOT ANSWER on option-mass grounds, but their OWN "
              "summary.json puts the median at or above the gate (%.4g). A gate verdict "
              "re-derived from the producer's label is not a verdict." % (false_ca[:8], gate_v))
        # (d) and a below-gate arm may not ALSO be reported as an ordinary result.
        both = sorted(set(declared_ca) & reported)
        check("P5", not both,
              "arm(s) %s are reported BOTH in `arms` and in `cannot_answer_arms`. An arm is one "
              "or the other; a number that appears in both places will be quoted from the first."
              % (both[:8],))
        unexpected = sorted(reported - set(exp))
        check("R5", not unexpected,
              "the producer reports arm(s) %s that this verifier's declared arm set does not "
              "contain; an arm nobody preregistered is not evidence" % unexpected[:8])

    # ---- per-arm re-derivation --------------------------------------------------------------
    bank_rows = {}
    for bank in banks:
        bp = cfg["population"]["banks"][bank]["path"]
        fp = bp if os.path.isabs(bp) else os.path.join(bank_dir, os.path.basename(bp))
        if not os.path.exists(fp):
            fp = os.path.join(REPO, bp)
        if os.path.exists(fp):
            d = {}
            with open(fp) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        r = json.loads(line)
                        d[r["prompt_id"]] = r
            bank_rows[bank] = d

    seen_sha, present = {}, {}
    for tag, spec in exp.items():
        d = newest_done(arm_root, tag)
        if d is None:
            continue                    # not run yet: absence is U8/GPU work, not a verifier fail
        present[tag] = d
        rows = read_rows(d)
        if rows is None:
            check("R1", False, "%s: DONE.json but no results.jsonl" % tag)
            continue

        # ---- R1 -- THE DENOMINATOR. Usable readouts, not JSON lines.
        live = [r for r in rows if r.get("semantic_logodds") is not None]
        check("R1", len(live) == n_rows_expected,
              "%s: %d NON-NULL semantic_logodds among %d lines (declared %d). The delta's "
              "denominator is not the line count." % (tag, len(live), len(rows), n_rows_expected))
        per_domain = collections.Counter(r.get("domain") for r in live)
        check("R1", len(per_domain) == n_domains_expected and len(set(per_domain.values())) == 1,
              "%s: usable readouts are not uniform over %d analysed domains -- %d domain(s), "
              "counts %s" % (tag, n_domains_expected, len(per_domain),
                             sorted(set(per_domain.values()))[:5]))

        # ---- R2 -- ROW-LEVEL IDENTITY. The rows carry the arm they were SCORED under.
        scope_ids = {r.get("knockout_scope_id") for r in rows}
        if spec["kind"] == "baseline":
            check("R2", scope_ids <= {None},
                  "%s is the untouched baseline but its rows carry knockout_scope_id %s; an arm "
                  "that names a scope it never cut is exactly the artifact that later reads as "
                  "evidence that it did"
                  % (tag, sorted(x for x in scope_ids if x is not None)))
        else:
            want_id = spec["scope_id"] + ("_randomrow_d%d" % spec["draw"]
                                          if spec["kind"] == "random_row_control" else "")
            check("R2", scope_ids == {want_id},
                  "%s: rows carry knockout_scope_id %s, expected %r. The directory name and the "
                  "rows disagree -- a swap or a copy keeps the furniture intact and changes the "
                  "rows." % (tag, sorted(x for x in scope_ids if x is not None), want_id))
            af = argsfile_flag(argsroot, tag, "--knockout-rel-end-rows")
            if af is None:
                af = argsfile_flag(argsroot, tag, "--declared-rel-end")
            if af is not None:
                try:
                    want_rel = parse_offsets(af)
                except ValueError as e:
                    want_rel = None
                    check("R2", False, "%s: committed argsfile offsets are invalid (%s)" % (tag, e))
                if want_rel is not None:
                    check("R2", want_rel == sorted(spec["rel_end"]),
                          "%s: the committed argsfile asks for %d offset(s) %s but this verifier "
                          "re-derives %d %s from the frozen file"
                          % (tag, len(want_rel), want_rel[:6], len(spec["rel_end"]),
                             sorted(spec["rel_end"])[:6]))

        # ---- R4 -- BANK JOIN and DECLARED POPULATION.
        bk = bank_rows.get(spec["bank"])
        if bk is not None:
            miss = [r["prompt_id"] for r in rows if r.get("prompt_id") not in bk]
            check("R4", not miss,
                  "%s: %d scored prompt_id(s) are absent from bank %r; the scored rows and the "
                  "declared bank are different populations" % (tag, len(miss), spec["bank"]))
            bad = []
            for r in rows:
                b = bk.get(r.get("prompt_id"))
                if b is None:
                    continue
                for f in ("cell", "query_kind", "n_examples", "domain", "split"):
                    if r.get(f) != b.get(f):
                        bad.append((r.get("prompt_id"), f, r.get(f), b.get(f)))
            check("R4", not bad,
                  "%s: %d row/bank field disagreement(s), e.g. %s; the scored rows were "
                  "relabelled away from the bank they claim to come from" % (tag, len(bad), bad[:3]))
        off = [(f, sorted({r.get(f) for r in rows}))
               for f, v in DECLARED_POPULATION.items() if {r.get(f) for r in rows} != {v}]
        check("R4", not off,
              "%s: rows are OFF the declared population on %s (declared %s). "
              "`population._cell_note`: select on `cell`, never on `condition`."
              % (tag, off, DECLARED_POPULATION))

        # ---- P3 -- THE CHANNEL. `semantic_forced_choice` is SECONDARY DISPLAY ONLY.
        kinds = {r.get("query_kind") for r in rows}
        check("P3", FORBIDDEN_MECHANISM_CHANNEL not in kinds,
              "%s carries %r rows. That channel contains the concept word in the QUESTION on "
              "100%% of its rows, so a knockout effect measured on it is instrument leakage; the "
              "frozen file marks it SECONDARY DISPLAY ONLY and forbids it as a mechanism result."
              % (tag, FORBIDDEN_MECHANISM_CHANNEL))

        # ---- P1 -- REALISED == DECLARED. The defect this phase exists to fix.
        if spec["kind"] != "baseline":
            want_rel = sorted(spec["rel_end"])
            n_bad_pos, n_bad_dec, ex = 0, 0, []
            for r in rows:
                sl, pos = r.get("seq_len"), r.get("surface_span_positions")
                if sl is None or pos is None:
                    n_bad_pos += 1
                    if len(ex) < 3:
                        ex.append((r.get("prompt_id"), "no seq_len / surface_span_positions"))
                    continue
                want = sorted(int(sl) + o for o in want_rel)
                if sorted(int(x) for x in pos) != want:
                    n_bad_pos += 1
                    if len(ex) < 3:
                        ex.append((r.get("prompt_id"), "realised %s want %s"
                                   % (sorted(pos)[:4], want[:4])))
                dec = r.get("surface_span_decoded")
                if not dec or len(dec) != len(want_rel):
                    n_bad_dec += 1
            check("P1", n_bad_pos == 0,
                  "%s: %d/%d row(s) realised a row set that is NOT seq_len+rel_end for the "
                  "declared offsets, e.g. %s. An absolute index that is right on one prompt and "
                  "wrong on the rest is invisible in a mean; `primary.void` VOIDS the arm."
                  % (tag, n_bad_pos, len(rows), ex))
            check("P1", n_bad_dec == 0,
                  "%s: %d/%d row(s) carry no (or a wrong-length) `surface_span_decoded`. "
                  "Positions alone cannot answer WHICH TOKEN was cut -- a 9-token shift looks "
                  "identical in the integers." % (tag, n_bad_dec, len(rows)))

        # ---- P2 -- LIVENESS AND THE ATTENTION BACKEND, per row and on the LOADED config.
        summ = read_json(d, "summary.json") or {}
        meta = read_json(d, "metadata.json") or {}
        live_blk = summ.get("knockout_liveness") or {}
        if spec["kind"] != "baseline":
            impl = live_blk.get("attn_implementation") or meta.get("attn_implementation")
            check("P2", impl == "eager",
                  "%s ran with attn_implementation=%r. Under SDPA the additive mask edit is "
                  "DISCARDED and the knockout is a silent no-op that scores as a clean null; the "
                  "frozen file calls such an arm VOID, not a negative." % (tag, impl))
            n_pre = [int(r.get("hook_n_prefill_edits") or 0) for r in rows]
            n_dec = [int(r.get("hook_n_decode_edits") or 0) for r in rows]
            check("P2", n_pre and min(n_pre) > 0,
                  "%s: %d row(s) recorded ZERO prefill edits -- the hook did not fire and the arm "
                  "is a baseline filed under a knockout name"
                  % (tag, sum(1 for x in n_pre if x <= 0)))
            check("P2", not [x for x in n_dec if x != 0],
                  "%s: %d row(s) recorded NON-ZERO decode edits. Every scope in this family is "
                  "prefill-only; a decode edit means the scoping leaked and the arm is secretly a "
                  "LARGER intervention than the one being reported"
                  % (tag, sum(1 for x in n_dec if x != 0)))
        sha = file_sha(d)
        if sha is not None:
            seen_sha.setdefault(sha, []).append(tag)

    # ---- R3 -- NOTHING IS A BYTE-COPY OF ANYTHING ELSE -------------------------------------
    dupes = {s: t for s, t in seen_sha.items() if len(t) > 1}
    check("R3", not dupes,
          "arm(s) share a BYTE-IDENTICAL results.jsonl: %s. Two arms that produced the same bytes "
          "did not run twice; whichever contrast reads them is true by construction."
          % [t for t in dupes.values()])

    # ---- R3 -- THE CONTROL BAND MUST BE THREE DRAWS, NOT ONE REPEATED ----------------------
    n_rr = int(cfg["seeds"]["n_random_row_draws"])
    bands = collections.defaultdict(list)
    for tag, spec in exp.items():
        if spec["kind"] == "random_row_control" and tag in present:
            bands[(spec["bank"], spec["scope_id"])].append((spec["draw"], present[tag]))
    for (bank, sid), draws in sorted(bands.items()):
        if len(draws) != n_rr:
            check("R3", False,
                  "%s/%s: the random-row control band has %d of the %d declared draws on disk; a "
                  "band that is short is not the declared band" % (bank, sid, len(draws), n_rr))
            continue
        shas = [file_sha(d) for _, d in draws]
        check("R3", len(set(shas)) == n_rr,
              "%s/%s: %d draw(s) produced %d DISTINCT output hash(es). Identical hashes mean the "
              "seed never reached the draw and the control band is secretly n=1 -- published "
              "twice in this project already." % (bank, sid, n_rr, len(set(shas))))

    # ---- P4 -- PR059-D1: the impossible controls must be ABSENT, not smaller --------------
    for bank in banks:
        for sid in EXPECT_RANDOM_ROW_IMPOSSIBLE_D1:
            if sid not in scopes:
                continue
            for d_i in range(n_rr):
                tag = arm_tag(bank, sid, "random_row_control", d_i)
                d = newest_done(arm_root, tag)
                check("P4", d is None,
                      "PR059-D1: %s exists on disk. Scope %s cuts %d of the %d query-span rows, "
                      "leaving a pool of %d -- FEWER than the dose it must match, so a "
                      "dose-matched random-row control is ARITHMETICALLY IMPOSSIBLE for it. Any "
                      "directory bearing this name holds a SMALLER draw wearing the label "
                      "'dose-matched'." % (tag, sid, len(scopes[sid]), len(span),
                                           len(span) - len(scopes[sid])))
        if prod is not None:
            for sid in EXPECT_RANDOM_ROW_IMPOSSIBLE_D1:
                blk = (prod.get("controls") or {}).get(bank, {}).get(sid, {})
                check("P4", not blk.get("random_row_control"),
                      "PR059-D1: the producer reports a random-row control for %s/%s, which "
                      "cannot be built on this template." % (bank, sid))

    return fails, notes, {"n_expected_arms": len(exp), "n_arms_on_disk": len(present),
                          "n_rows_expected": n_rows_expected,
                          "n_domains_expected": n_domains_expected,
                          "scopes": {k: len(v) for k, v in scopes.items()},
                          "query_span_rows": len(span)}


def parse_domains(cfg):
    """The ANALYSED domain set: the declared 116 minus `population.preregistered_exclusions`.

    Re-derived here from the two numbers the frozen file states (`n_rows_per_bank` /
    `rows_per_domain_per_cell`) and cross-checked against the exclusion list, rather than copied
    from `_row_arithmetic`'s prose. Prose that no program consults is a wish, not a check.
    """
    n_rows = int(cfg["population"]["n_rows_per_bank"])
    per_dom = int(cfg["population"]["rows_per_domain_per_cell"])
    if n_rows % per_dom:
        raise ValueError("n_rows_per_bank=%d is not a whole multiple of "
                         "rows_per_domain_per_cell=%d" % (n_rows, per_dom))
    return list(range(n_rows // per_dom))


# =============================================================================================
# 4. A SYNTHETIC BUT COMPLETE FIXTURE -- so --self-test and --mutate need no GPU run
# =============================================================================================
def build_fixture(tmp, cfg, banks=("button_bomb",)):
    """A clean, PASSING arm tree for `banks`, built from the frozen file's own declarations.

    ⛔ THE FIXTURE IS BUILT FROM THE DESIGN, NOT FROM THE VERIFIER'S EXPECTATIONS. It writes what
    a CORRECT producer would write -- realised positions computed as `seq_len + rel_end` with a
    per-row `seq_len` that VARIES, decoded tokens, per-row hook counters, an eager summary -- and
    the verifier is then run against it without being told any of that. A fixture generated by the
    checks it is about to satisfy proves nothing.
    """
    arm_root = os.path.join(tmp, "arms")
    bank_dir = os.path.join(tmp, "banks")
    argsroot = os.path.join(tmp, "runargs")
    for p in (arm_root, bank_dir, argsroot):
        os.makedirs(p, exist_ok=True)

    n_rows = int(cfg["population"]["n_rows_per_bank"])
    per_dom = int(cfg["population"]["rows_per_domain_per_cell"])
    n_dom = n_rows // per_dom
    exp = expected_arms(cfg, banks)

    bank_index = {}
    for bank in banks:
        rows = []
        for di in range(n_dom):
            for si in range(per_dom):
                pid = "%s_d%03d_s%02d" % (bank, di, si)
                rows.append({"prompt_id": pid, "domain": "dom%03d" % di,
                             "split": ("train" if di % 3 else "val"), "cell": "C",
                             "query_kind": "semantic_one_word", "n_examples": 4,
                             "prompt_sha16": hashlib.sha256(pid.encode()).hexdigest()[:16]})
        bank_index[bank] = rows
        fp = os.path.join(bank_dir, os.path.basename(
            cfg["population"]["banks"][bank]["path"]))
        with open(fp, "w") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")

    for tag, spec in exp.items():
        d = os.path.join(arm_root, tag + "_20260909_000000_1")
        os.makedirs(d, exist_ok=True)
        rel = sorted(spec["rel_end"])
        scope_id = (None if spec["kind"] == "baseline"
                    else spec["scope_id"] + ("_randomrow_d%d" % spec["draw"]
                                             if spec["kind"] == "random_row_control" else ""))
        out = []
        for i, b in enumerate(bank_index[spec["bank"]]):
            # SEQ_LEN VARIES ACROSS ROWS, deliberately: a constant one would let an absolute-index
            # producer pass P1 by accident, which is the bug class this phase exists to catch.
            seq_len = 300 + (i % 37)
            r = {"prompt_id": b["prompt_id"], "domain": b["domain"], "split": b["split"],
                 "cell": "C", "query_kind": "semantic_one_word", "n_examples": 4,
                 "arm": tag, "readout": "semantic",
                 "semantic_logodds": -1.0 + 0.001 * i + (0.01 * len(rel)),
                 "option_mass": 0.12, "knockout_scope": (None if not rel else "query_last_k_rows"),
                 "knockout_scope_id": scope_id, "seq_len": seq_len}
            if rel:
                r["surface_span_positions"] = sorted(seq_len + o for o in rel)
                r["surface_span_rel_end"] = rel
                r["surface_span_decoded"] = ["t%d" % o for o in rel]
                r["hook_n_prefill_edits"] = 100 * len(rel)
                r["hook_n_decode_edits"] = 0
            out.append(r)
        with open(os.path.join(d, "results.jsonl"), "w") as f:
            for r in out:
                f.write(json.dumps(r) + "\n")
        json.dump({"ok": True}, open(os.path.join(d, "DONE.json"), "w"))
        json.dump({"knockout_liveness": ({"attn_implementation": "eager"} if rel else None)},
                  open(os.path.join(d, "summary.json"), "w"))
        json.dump({"attn_implementation": ("eager" if rel else "sdpa")},
                  open(os.path.join(d, "metadata.json"), "w"))
        if rel:
            with open(os.path.join(argsroot, tag + ".args"), "w") as f:
                f.write("--knockout-scope query_last_k_rows --knockout-rel-end-rows %s\n"
                        % ",".join(str(o) for o in rel))

    prod = {"scopes": {}, "arms": {t: {} for t in exp}, "family": [], "reference": "S_G",
            "controls": {b: {} for b in banks}, "liveness": {}, "population": DECLARED_POPULATION,
            "channel": "semantic_one_word"}
    prod_path = os.path.join(tmp, "producer.json")
    json.dump(prod, open(prod_path, "w"))
    return arm_root, prod_path, bank_dir, argsroot


# =============================================================================================
# 5. SELF-TEST
# =============================================================================================
def self_test():
    n, bad = 0, []

    def check(name, ok, detail=""):
        nonlocal n
        n += 1
        print("  %-6s %s %s" % ("PASS" if ok else "FAIL", name, detail))
        if not ok:
            bad.append(name)

    cfg = load_prereg()

    # ---- the independence rule, enforced against this file's own source text
    # Two ways, because either alone is weak: the SOURCE must contain no import of the analyzer,
    # and after this module has been fully imported the analyzer must not be in `sys.modules` --
    # which also catches an indirect import through some third module.
    src = open(os.path.abspath(__file__)).read()
    ANALYZER = "dcs_ts_pr059" + "_localisation"
    imports = [ln for ln in src.splitlines()
               if ANALYZER in ln and (ln.strip().startswith("import ")
                                      or ln.strip().startswith("from ")
                                      or "import_module" in ln or "__import__" in ln)]
    check("T00a the SOURCE contains no import of the analyzer", not imports, str(imports[:2]))
    check("T00b the analyzer is not in sys.modules after this file is imported",
          ANALYZER not in sys.modules,
          "(a verifier sharing the analyzer's assumptions verifies nothing)")

    # ---- the offset parser, on all three shapes the frozen file uses
    check("T01 parse a JSON list", parse_offsets([-5, -4, -3, -2, -1]) == [-5, -4, -3, -2, -1])
    check("T02 parse a range string", parse_offsets("[-28..-6]") == list(range(-28, -5)))
    check("T03 parse a range MINUS an exclusion",
          parse_offsets("[-28..-6] minus [-10]") == [o for o in range(-28, -5) if o != -10])
    try:
        parse_offsets([3])
        check("T04 an absolute index is REFUSED", False, "accepted")
    except ValueError:
        check("T04 an absolute index is REFUSED", True)

    # ---- the scope table and the span, re-derived
    sc = scope_table(cfg)
    check("T05 scope sizes re-derive from the frozen file",
          [len(sc[k]) for k in ("S_A", "S_C", "S_D", "S_E", "S_F", "S_F2", "S_G")]
          == [5, 1, 22, 23, 1, 1, 28],
          str({k: len(sc[k]) for k in sc}))
    check("T06 S_B is empty (UNCONSTRUCTIBLE)", sc["S_B"] == [])
    span = query_span_offsets(cfg)
    check("T07 the query span is 28 rows, -28..-1",
          len(span) == 28 and span[0] == -28 and span[-1] == -1)
    check("T08 S_D and S_E differ by exactly the codeword row",
          sorted(set(sc["S_E"]) - set(sc["S_D"])) == [-10] and set(sc["S_D"]) < set(sc["S_E"]))

    # ---- PR059-D1, re-derived rather than believed
    ok = [s for s in sc if sc[s] and redraw_random_rows(cfg, s, sc[s], 0) is not None]
    no = [s for s in sc if sc[s] and redraw_random_rows(cfg, s, sc[s], 0) is None]
    check("T09 PR059-D1 re-derives: which scopes CAN have a dose-matched control",
          tuple(ok) == EXPECT_RANDOM_ROW_CONSTRUCTIBLE, str(ok))
    check("T10 PR059-D1 re-derives: which CANNOT, and why",
          tuple(no) == EXPECT_RANDOM_ROW_IMPOSSIBLE_D1,
          "%s (pools %s vs doses %s)" % (no, [len(span) - len(sc[s]) for s in no],
                                         [len(sc[s]) for s in no]))
    check("T11 the draw is reproducible across calls",
          redraw_random_rows(cfg, "S_A", sc["S_A"], 0)
          == redraw_random_rows(cfg, "S_A", sc["S_A"], 0))
    check("T12 the draw EXCLUDES the scope's own rows",
          not (set(redraw_random_rows(cfg, "S_A", sc["S_A"], 0)) & set(sc["S_A"])))
    check("T13 the draws are DISTINCT across draw indices",
          len({tuple(redraw_random_rows(cfg, "S_A", sc["S_A"], i)) for i in range(3)}) == 3)
    check("T14 the draw is DOSE-MATCHED",
          len(redraw_random_rows(cfg, "S_A", sc["S_A"], 0)) == len(sc["S_A"]))

    # ---- the arm set is this file's, and it is not empty
    exp = expected_arms(cfg)
    check("T15 the expected arm set is declared HERE and is non-empty", len(exp) > 0, str(len(exp)))
    check("T16 no random-row arm is expected for an impossible scope",
          not [t for t, s in exp.items()
               if s["kind"] == "random_row_control"
               and s["scope_id"] in EXPECT_RANDOM_ROW_IMPOSSIBLE_D1])
    # PR059-D5. The two derivations of the arm set now agree at 84, and each half of the
    # reconciliation is pinned HERE, on this file's own re-derivation.
    _ref = reference_scope_id(cfg)
    check("T15b PR059-D5 the REFERENCE scope carries its nondemo-key control on every bank "
          "('for EVERY scope'; its draw pool excludes the query span, so the 28-row span does "
          "not constrain it)",
          sum(1 for s in exp.values()
              if s["scope_id"] == _ref and s["kind"] == "nondemo_control")
          == int(cfg["seeds"]["n_nondemo_draws"]) * len(DECLARED_CONFIRMATORY_BANKS),
          "ref=%s" % _ref)
    check("T15c PR059-D5 the BLOCKING null L-N1 bridge arm is expected, one per bank",
          sum(1 for s in exp.values() if s["kind"] == "bridge")
          == len(DECLARED_CONFIRMATORY_BANKS),
          str(sorted(t for t, s in exp.items() if s["kind"] == "bridge")))
    check("T15d the reference is RE-DERIVED as the scope covering the whole query span, not "
          "read off a key the analyzer also reads",
          set(sc[_ref]) == set(span) and _ref == "S_G", _ref)
    check("T17 every family scope has its nondemo control band",
          all(sum(1 for s in exp.values()
                  if s["scope_id"] == sid and s["kind"] == "nondemo_control"
                  and s["bank"] == "button_bomb") == int(cfg["seeds"]["n_nondemo_draws"])
              for sid in ("S_A", "S_C", "S_D", "S_E", "S_F")))

    # ---- the CLEAN fixture must pass every check
    with tempfile.TemporaryDirectory() as tmp:
        ar, pp, bd, ag = build_fixture(tmp, cfg)
        fails, notes, info = verify(cfg, ar, pp, bd, ag, banks=("button_bomb",))
        check("T18 a CORRECT arm tree passes every check", not fails,
              ("clean, %d arms, %d rows/arm, %d domains"
               % (info["n_arms_on_disk"], info["n_rows_expected"], info["n_domains_expected"]))
              if not fails else str(notes[:2]))

    # ---- an EMPTY tree must not "pass" by having nothing to check
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "arms"))
        json.dump({}, open(os.path.join(tmp, "p.json"), "w"))
        fails, notes, _ = verify(cfg, os.path.join(tmp, "arms"), os.path.join(tmp, "p.json"),
                                 tmp, tmp, banks=("button_bomb",))
        check("T19 an EMPTY producer fails R5 rather than passing vacuously", "R5" in fails,
              str(sorted(set(fails))))

    # ---- V0 must fire when the design moves under the verifier
    moved = json.loads(json.dumps(cfg))
    moved["status"] = "DRAFT"
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "arms"))
        fails, _, _ = verify(moved, os.path.join(tmp, "arms"), "", tmp, tmp,
                             banks=("button_bomb",))
        check("T20 a non-FROZEN design is refused by V0", "V0" in fails)

    # ---- T21/T22: DCS-PR-065's option-mass gate, parsed by THIS FILE alone -------------------
    # The verifier imports nothing from the analyzer, so the only way its gate can be trusted is
    # if it re-derives the SAME number from each of the three independent prose sites the frozen
    # file states it in. Three sentences, written separately, agreeing.
    _g = option_mass_gate_from_cfg(cfg)
    _sites = [((cfg.get("outcome_variables") or {}).get("O1_semantic_readout") or {})
              .get("cannot_answer_if"),
              (cfg.get("primary") or {}).get("cannot_answer"),
              cfg.get("kill_condition")]
    _vals = []
    for _t_ in _sites:
        _m = re.search(r"below the (0?\.\d+) gate", _t_ or "") or re.search(
            r"option_mass\s+below\s+the\s+(0?\.\d+)", _t_ or "")
        if _m:
            _vals.append(float(_m.group(1)))
    check("T21 the option-mass gate is stated identically at all three prose sites",
          len(_vals) >= 3 and len(set(_vals)) == 1 and _vals[0] == _g,
          "sites=%s parsed=%r" % (_vals, _g))
    check("T22 the gate is a real fraction, re-derived and never a constant in this file",
          isinstance(_g, float) and 0.0 < _g < 1.0
          and ("%g" % _g) not in io.open(__file__, encoding="utf-8").read()
              .split("def option_mass_gate_from_cfg")[0],
          "gate=%r" % _g)

    print("\n[pr059-verifier] self-test: %d check(s), %d FAILED" % (n, len(bad)))
    if bad:
        print("  FAILED: %s" % bad)
    return 1 if bad else 0


# =============================================================================================
# 6. MUTATION HARNESS -- every check must be REACHABLE, and each for its own reason
# =============================================================================================
def _rows_of(arm_root, tag):
    d = newest_done(arm_root, tag)
    return d, read_rows(d)


def _write(d, rows):
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _t(sid, kind="scope", draw=None, bank="button_bomb"):
    return arm_tag(bank, sid, kind, draw)


def m_silent_denominator(cfg, ar, pp, bd, ag):
    d, rows = _rows_of(ar, _t("S_E"))
    for i, r in enumerate(rows):
        if i % 10:
            r["semantic_logodds"] = None
    _write(d, rows)


def m_uneven_domains(cfg, ar, pp, bd, ag):
    d, rows = _rows_of(ar, _t("S_D"))
    for r in rows:
        if r["domain"] == "dom001":
            r["semantic_logodds"] = None
    _write(d, rows)


def m_arm_swap(cfg, ar, pp, bd, ag):
    da, ra = _rows_of(ar, _t("S_D"))
    db, rb = _rows_of(ar, _t("S_E"))
    _write(da, rb)
    _write(db, ra)


def m_baseline_claims_a_scope(cfg, ar, pp, bd, ag):
    d, rows = _rows_of(ar, _t("S_0", "baseline"))
    for r in rows:
        r["knockout_scope_id"] = "S_G"
    _write(d, rows)


def m_argsfile_disagrees(cfg, ar, pp, bd, ag):
    tag = _t("S_C")
    with open(os.path.join(ag, tag + ".args"), "w") as f:
        f.write("--knockout-scope query_last_k_rows --knockout-rel-end-rows -11\n")


def m_band_is_secretly_n1(cfg, ar, pp, bd, ag):
    src = newest_done(ar, _t("S_A", "random_row_control", 0))
    for i in (1, 2):
        dst = newest_done(ar, _t("S_A", "random_row_control", i))
        shutil.copy(os.path.join(src, "results.jsonl"), os.path.join(dst, "results.jsonl"))


def m_arm_is_a_byte_copy(cfg, ar, pp, bd, ag):
    src = newest_done(ar, _t("S_D"))
    dst = newest_done(ar, _t("S_E"))
    shutil.copy(os.path.join(src, "results.jsonl"), os.path.join(dst, "results.jsonl"))


def m_band_is_short(cfg, ar, pp, bd, ag):
    d = newest_done(ar, _t("S_A", "random_row_control", 2))
    os.remove(os.path.join(d, "DONE.json"))


def m_population_swap(cfg, ar, pp, bd, ag):
    fp = os.path.join(bd, os.path.basename(
        cfg["population"]["banks"]["button_bomb"]["path"]))
    rows = [json.loads(l) for l in open(fp) if l.strip()]
    for r in rows:
        r["prompt_id"] = hashlib.sha256(("X" + r["prompt_id"]).encode()).hexdigest()[:16]
    with open(fp, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def m_population_drift(cfg, ar, pp, bd, ag):
    d, rows = _rows_of(ar, _t("S_C"))
    for r in rows:
        r["cell"] = "B"
        r["n_examples"] = 8
    _write(d, rows)


def m_display_channel(cfg, ar, pp, bd, ag):
    d, rows = _rows_of(ar, _t("S_E"))
    for r in rows:
        r["query_kind"] = FORBIDDEN_MECHANISM_CHANNEL
    _write(d, rows)


def _write_option_mass(cfg, ar, tag, median_true):
    """Give one arm on disk an option-mass block at a chosen median. Used ONLY by the mutation
    harness, to make P5's two directions reachable."""
    d = newest_done(ar, tag)
    fp = os.path.join(d, "summary.json")
    j = json.load(open(fp)) if os.path.exists(fp) else {}
    chan = ((cfg.get("population") or {}).get("query_kind_primary")
            or (cfg.get("population") or {}).get("primary_channel")
            or "semantic_one_word")
    j.setdefault("option_mass", {})["semantic/" + chan] = {
        "n": 230, "median_true": median_true, "p10": 0.0001146425711340271,
        "frac_above_1pct": 0.6478260869565218,
        "reportable": median_true >= option_mass_gate_from_cfg(cfg)}
    json.dump(j, open(fp, "w"))
    return d


def m_below_gate_arm_vanishes(cfg, ar, pp, bd, ag):
    """DCS-PR-065 lets a below-gate arm be omitted from `arms`. It does not let it VANISH: it must
    still be declared in `cannot_answer_arms`, carrying its own option mass."""
    _write_option_mass(cfg, ar, _t("S_D"), option_mass_gate_from_cfg(cfg) / 2.0)
    j = json.load(open(pp))
    j["arms"].pop(_t("S_D"), None)
    j.pop("cannot_answer_arms", None)
    json.dump(j, open(pp, "w"))


def m_healthy_arm_labelled_cannot_answer(cfg, ar, pp, bd, ag):
    """The other direction: an arm whose OWN summary.json is comfortably above the gate is
    labelled CANNOT ANSWER, which would let any inconvenient result be relabelled away."""
    _write_option_mass(cfg, ar, _t("S_D"), option_mass_gate_from_cfg(cfg) * 4.0)
    j = json.load(open(pp))
    j["arms"].pop(_t("S_D"), None)
    j["cannot_answer_arms"] = [{"arm_id": _t("S_D"), "median_option_mass": 0.001}]
    json.dump(j, open(pp, "w"))


def m_arm_reported_twice(cfg, ar, pp, bd, ag):
    """An arm in `arms` AND in `cannot_answer_arms`. Whichever a reader hits first becomes the
    number, and the other becomes deniable."""
    _write_option_mass(cfg, ar, _t("S_D"), option_mass_gate_from_cfg(cfg) / 2.0)
    j = json.load(open(pp))
    j["cannot_answer_arms"] = [{"arm_id": _t("S_D"), "median_option_mass": 0.02}]
    json.dump(j, open(pp, "w"))


def m_producer_drops_a_block(cfg, ar, pp, bd, ag):
    j = json.load(open(pp))
    for k in ("controls", "liveness", "reference"):
        j.pop(k, None)
    json.dump(j, open(pp, "w"))


def m_producer_drops_an_arm(cfg, ar, pp, bd, ag):
    j = json.load(open(pp))
    j["arms"].pop(_t("S_D"), None)
    json.dump(j, open(pp, "w"))


def m_producer_invents_an_arm(cfg, ar, pp, bd, ag):
    j = json.load(open(pp))
    j["arms"]["pr059_button_bomb_s_z_scope_n4"] = {}
    json.dump(j, open(pp, "w"))


def m_absolute_index(cfg, ar, pp, bd, ag):
    """THE bug class. Resolve the offsets ONCE, against the FIRST row's length, and reuse the
    resulting absolute indices on every row. Right on row 0, wrong on all the others, and
    completely invisible in a mean."""
    d, rows = _rows_of(ar, _t("S_D"))
    rel = sorted(scope_table(cfg)["S_D"])
    pinned = sorted(int(rows[0]["seq_len"]) + o for o in rel)
    for r in rows:
        r["surface_span_positions"] = list(pinned)
    _write(d, rows)


def m_off_by_one(cfg, ar, pp, bd, ag):
    d, rows = _rows_of(ar, _t("S_C"))
    for r in rows:
        r["surface_span_positions"] = [p + 1 for p in r["surface_span_positions"]]
    _write(d, rows)


def m_no_decoded_tokens(cfg, ar, pp, bd, ag):
    d, rows = _rows_of(ar, _t("S_F"))
    for r in rows:
        r.pop("surface_span_decoded", None)
    _write(d, rows)


def m_sdpa_arm(cfg, ar, pp, bd, ag):
    d = newest_done(ar, _t("S_G"))
    json.dump({"knockout_liveness": {"attn_implementation": "sdpa"}},
              open(os.path.join(d, "summary.json"), "w"))
    json.dump({"attn_implementation": "sdpa"}, open(os.path.join(d, "metadata.json"), "w"))


def m_dead_hook(cfg, ar, pp, bd, ag):
    d, rows = _rows_of(ar, _t("S_A"))
    for r in rows:
        r["hook_n_prefill_edits"] = 0
    _write(d, rows)


def m_leaky_scope(cfg, ar, pp, bd, ag):
    d, rows = _rows_of(ar, _t("S_A"))
    for r in rows:
        r["hook_n_decode_edits"] = 7
    _write(d, rows)


def m_impossible_control_shipped(cfg, ar, pp, bd, ag):
    """PR059-D1 defeated the wrong way: a SMALLER draw, shipped under the dose-matched name."""
    src = newest_done(ar, _t("S_C", "random_row_control", 0))
    dst = os.path.join(ar, _t("S_D", "random_row_control", 0) + "_20260909_000000_9")
    shutil.copytree(src, dst)


def m_producer_claims_the_impossible_control(cfg, ar, pp, bd, ag):
    j = json.load(open(pp))
    j["controls"]["button_bomb"] = {"S_D": {"random_row_control": {"m": 22}}}
    json.dump(j, open(pp, "w"))


MUTATIONS = [
    ("M01 outcome nulled on 9/10 rows",            m_silent_denominator,        "R1"),
    ("M02 one domain silently dropped",            m_uneven_domains,            "R1"),
    ("M03 two arms' rows swapped",                 m_arm_swap,                  "R2"),
    ("M04 the baseline claims a scope",            m_baseline_claims_a_scope,   "R2"),
    ("M05 argsfile offsets != declared offsets",   m_argsfile_disagrees,        "R2"),
    ("M06 control band is secretly n=1",           m_band_is_secretly_n1,       "R3"),
    ("M07 one arm is a byte-copy of another",      m_arm_is_a_byte_copy,        "R3"),
    ("M08 control band short of its declared draws", m_band_is_short,           "R3"),
    ("M09 bank replaced by a disjoint population", m_population_swap,           "R4"),
    ("M10 rows relabelled off the declared cell",  m_population_drift,          "R4"),
    ("M11 display channel as a mechanism result",  m_display_channel,           "P3"),
    ("M12 producer deletes whole blocks",          m_producer_drops_a_block,    "R5"),
    ("M13 producer drops an arm complete on disk", m_producer_drops_an_arm,     "R5"),
    ("M14 producer invents an unpreregistered arm", m_producer_invents_an_arm,  "R5"),
    ("M15 ABSOLUTE index pinned from row 0",       m_absolute_index,            "P1"),
    ("M16 realised row set off by one",            m_off_by_one,                "P1"),
    ("M17 decoded tokens not persisted",           m_no_decoded_tokens,         "P1"),
    ("M18 the arm ran under SDPA",                 m_sdpa_arm,                  "P2"),
    ("M19 the hook never fired at prefill",        m_dead_hook,                 "P2"),
    ("M20 the scope leaked into decode",           m_leaky_scope,               "P2"),
    ("M21 PR059-D1 impossible control SHIPPED",    m_impossible_control_shipped, "P4"),
    ("M22 producer CLAIMS the impossible control", m_producer_claims_the_impossible_control, "P4"),
    # DCS-PR-065: the one permitted omission, in both directions and doubled.
    ("M23 a below-gate arm VANISHES instead of being declared CANNOT ANSWER",
     m_below_gate_arm_vanishes, "P5"),
    ("M24 an ABOVE-gate arm relabelled CANNOT ANSWER", m_healthy_arm_labelled_cannot_answer, "P5"),
    ("M25 an arm reported BOTH as a result and as CANNOT ANSWER", m_arm_reported_twice, "P5"),
]


def run_mutations():
    cfg = load_prereg()
    print("MUTATION HARNESS -- each corruption must be caught by its DESIGNATED check.\n"
          "A refusal that fires for the wrong reason is not a refusal.\n")
    n_red, n_total = 0, len(MUTATIONS)
    for name, fn, designated in MUTATIONS:
        with tempfile.TemporaryDirectory() as tmp:
            ar, pp, bd, ag = build_fixture(tmp, cfg)
            fn(cfg, ar, pp, bd, ag)
            fails, notes, _ = verify(cfg, ar, pp, bd, ag, banks=("button_bomb",))
            caught = designated in fails
            n_red += int(caught)
            print("  %-6s %-46s -> %s %s"
                  % ("RED" if caught else "*GREEN*", name, designated,
                     "" if caught else "*** NOT CAUGHT (fired: %s) ***" % sorted(set(fails))))
    print("\n[pr059-verifier] mutations: %d/%d RED" % (n_red, n_total))
    return 0 if n_red == n_total else 1


# =============================================================================================
def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prereg", default=PREREG)
    ap.add_argument("--arm-root", default=DEFAULT_ARM_ROOT)
    ap.add_argument("--producer", default=DEFAULT_PRODUCER)
    ap.add_argument("--bank-dir", default=os.path.join(REPO, "data", "boombness_prompts"))
    ap.add_argument("--argsroot", default=DEFAULT_ARGSROOT)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--mutate", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if a.mutate:
        return run_mutations()

    cfg = load_prereg(a.prereg)
    fails, notes, info = verify(cfg, a.arm_root, a.producer, a.bank_dir, a.argsroot)
    print(json.dumps(info, indent=1))
    for n in notes:
        print(n)
    if info["n_arms_on_disk"] == 0:
        print("\nREFUSING TO VERIFY: %d declared arm(s) searched, %d present on disk. A verifier "
              "that binds ZERO arms and prints PASS is the vacuous-by-omission defect it exists "
              "to close. The arms are GPU work (checklist U8) and have not run."
              % (info["n_expected_arms"], info["n_arms_on_disk"]))
        return 2
    if fails:
        print("\nVERIFICATION FAILED -- checks %s" % sorted(set(fails)))
        return 1
    for cid in CHECK_IDS:
        print("  %-3s PASS" % cid)
    print("\nVERIFIED over %d arm(s)." % info["n_arms_on_disk"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
