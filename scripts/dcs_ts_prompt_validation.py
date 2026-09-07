#!/usr/bin/env python3
"""MANDATE SECTION 15 -- the prompt-validation table for the PHASE 7 semantic readout.

WHAT THIS ANSWERS, AND WHY IT IS NOT AN EXTRA.  Every claim this phase has published so far --
R-113's 0.9399 three-way probe, R-111's separability geometry, R-112's positional contrast --
rests on the ASSUMPTION that the demonstrations install their concept IN THE MODEL.  `A-037`
established only that the demonstration POOLS carry the right affordances; it could not establish
uptake.  Installation has never been measured.  Job 865335 (`DCS-PR-054`) is the first
measurement, and this script is its consumer.

It emits, for every concept x codeword x domain x split x n_examples x template:

    the intended mapping, the concept whole-answer logP, the literal whole-answer logP,
    concept_binary_prob, semantic_logodds, option_mass, the decoded answer, installation status,
    whether the concept word leaks into `full_prompt`, and failures.

FIELD NAMES ARE NOT INVENTED HERE.  `logp_concept`, `logp_codeword`, `p_concept`, `p_codeword`,
`semantic_logodds`, `option_mass`, `top1_id`, `n_variants_concept`/`_codeword` are written by
`src/boombness/score_behavior.py` (via `signals.string_option_readout`); `concept`, `codeword`,
`target_semantic`, `full_prompt`, `n_concept_occurrences`, `demo_valence`, `role_style`,
`example_position`, `consistency`, `strength`, `family_slot` are written by the prompt-bank
generator.  Two columns are DERIVED and are labelled as such in the header:
`concept_binary_prob` (= p_concept / (p_concept + p_codeword)) and `installation_status`.
`decoded_answer` is the detokenisation of `top1_id`, i.e. the single most likely FIRST token of
the forced answer -- NOT a sampled generation: these runs wrote a zero-byte `gens.jsonl` and
`summary.json` reports `n_generations: 0`, so no free-text answer exists to report and this
script will not pretend one does.

THREE THINGS IT REFUSES TO DO
  * It does not hardcode a gate.  Every threshold is loaded through `scripts/dcs_ts_prereg.py`
    (which refuses on a null `*_sha16`, an unfrozen status, or a missing field) or, for the
    option-mass gate, read back off the RUN's own `config.json` -- the value the run actually
    enforced.  Where the preregistration declares no threshold at all (installation), the script
    REFUSES rather than inventing one; an unregistered cut must be passed explicitly and is
    stamped into every row as `installation_rule_source=unregistered_cli`.
  * It does not drop non-installing domains.  Mandate section 15 is explicit that installation is
    a preregistered STRATIFICATION variable and a reported descriptive limit, never a post-hoc
    exclusion.  The only rows removed are the three whole-population preregistered exclusions, and
    removing a domain that is NOT on that list is a refusal.
  * It does not pool concepts.  Mandate section 3 asks specifically that bomb / knife / gun be
    reported separately; every stratified table here keys on concept, and `--pool-concepts` does
    not exist.

FAIL-LOUD SURFACE (`--mutate` proves each refusal is reachable):
  bank file hash disagrees with the pinned `bank_file_sha16`; a manifest domain missing from a run
  without being a preregistered exclusion; a domain present that the manifest does not know; a
  duplicate `prompt_id` in a bank; a results row whose `prompt_id` is not in the bank; a results
  row whose `prompt_sha16`/`concept`/`codeword` disagrees with the bank row it joined to; a
  recount of concept occurrences that disagrees with the bank's `n_concept_occurrences`; a
  results row count that disagrees with `DONE.json:rows_written`; a NaN or out-of-range
  `option_mass`; an option-mass gate that differs between runs; any stratum that binds ZERO rows.

USAGE
    python3 scripts/dcs_ts_prompt_validation.py
    python3 scripts/dcs_ts_prompt_validation.py --installation-threshold 0.5 \
        --ack-unregistered-threshold
    python3 scripts/dcs_ts_prompt_validation.py --mutate
"""
from __future__ import annotations

import argparse
import collections
import copy
import glob
import hashlib
import json
import math
import os
import random
import re
import statistics
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))

from dcs_ts_prereg import load as load_prereg  # noqa: E402

#: The two readout channels this run covers.  `semantic_one_word` is the PRIMARY channel; PR-057
#: section `outcome_variables` says in terms that if `option_mass` shows it disengaged that is a
#: CANNOT ANSWER on the primary, NOT a licence to fall back on `semantic_forced_choice`, which is
#: the DISPLAY channel.
PRIMARY_CHANNEL = "semantic_one_word"
DISPLAY_CHANNEL = "semantic_forced_choice"

#: Mandate section 15's column list, in order.  `condition`/`cell`/`query_kind` are carried too
#: because a row without them is not addressable; everything else is exactly the section's list.
COLUMNS = [
    "bank", "concept", "codeword", "domain", "dsplit", "n_examples", "template",
    "cell", "condition", "query_kind",
    "intended_mapping",
    "logp_concept", "logp_codeword",
    "concept_binary_prob",
    "semantic_logodds",
    "option_mass",
    "decoded_answer",
    "installation_status",
    "concept_leaks_into_full_prompt", "n_concept_occurrences",
    "failures",
    "installation_rule_source",
]

DERIVED_COLUMNS = {"concept_binary_prob", "installation_status", "intended_mapping",
                   "decoded_answer", "concept_leaks_into_full_prompt", "template",
                   "dsplit", "installation_rule_source"}


class ValidationError(RuntimeError):
    """Every refusal in this file.  Raised, never printed-and-continued."""


def _fail(msg: str):
    raise ValidationError(msg)


def _file_sha16(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


# ----------------------------------------------------------------------------------------------
# loading
# ----------------------------------------------------------------------------------------------

BANK_FIELDS = ("prompt_id", "prompt_sha16", "domain", "cell", "condition", "query_kind",
               "n_examples", "concept", "codeword", "target_semantic", "demo_valence",
               "demo_surface", "query_surface", "role_style", "example_position", "consistency",
               "strength", "family_slot", "family_id", "bank_block", "full_prompt",
               "n_concept_occurrences", "n_codeword_occurrences", "final_query_text")


def load_bank(path: str) -> dict:
    """prompt_id -> the bank row.  A duplicate `prompt_id` is a refusal: the join below is by
    `prompt_id`, so a duplicate would silently make one of the two rows unreachable and give the
    other row's prompt text to both.  (Same shape as the compound-key collision the metadata
    sidecar tests for.)"""
    out: dict = {}
    with open(path) as f:
        for ln, line in enumerate(f, 1):
            o = json.loads(line)
            pid = o.get("prompt_id")
            if pid is None:
                _fail(f"{path}:{ln}: bank row has no prompt_id")
            if pid in out:
                _fail(f"{path}:{ln}: duplicate prompt_id {pid!r} -- the results join is by "
                      f"prompt_id and would bind one bank row to two different prompts")
            out[pid] = {k: o.get(k) for k in BANK_FIELDS}
    if not out:
        _fail(f"{path}: bank is EMPTY -- zero-row bind")
    return out


def discover_runs(pattern: str) -> list:
    """Every readout run directory, each tagged complete/incomplete.  Incompleteness is REPORTED,
    never silently skipped: 'which banks are missing' is part of the deliverable."""
    runs = []
    for d in sorted(glob.glob(os.path.join(REPO, pattern))):
        if not os.path.isdir(d):
            continue
        cfgp = os.path.join(d, "config.json")
        if not os.path.exists(cfgp):
            continue
        cfg = json.load(open(cfgp))
        bank_path = cfg.get("args", {}).get("bank", "")
        base = os.path.basename(bank_path)
        m = re.match(r"boombness_prompt_bank_([a-z0-9]+)_(.+)\.jsonl$", base)
        if not m:
            _fail(f"{d}: cannot parse a bank name out of {base!r}")
        family, bank_name = m.group(1), m.group(2)
        done = os.path.join(d, "DONE.json")
        runs.append({
            "dir": d, "cfg": cfg, "family": family, "bank": bank_name,
            "bank_path": bank_path,
            "complete": os.path.exists(done) and os.path.exists(os.path.join(d, "summary.json")),
            "done": json.load(open(done)) if os.path.exists(done) else None,
            "summary": (json.load(open(os.path.join(d, "summary.json")))
                        if os.path.exists(os.path.join(d, "summary.json")) else None),
        })
    if not runs:
        _fail(f"no readout run directories matched {pattern!r} -- zero-row bind")
    return runs


def load_results(run: dict) -> list:
    rows = []
    with open(os.path.join(run["dir"], "results.jsonl")) as f:
        for line in f:
            rows.append(json.loads(line))
    if not rows:
        _fail(f"{run['dir']}: results.jsonl is EMPTY -- zero-row bind")
    return rows


# ----------------------------------------------------------------------------------------------
# guards
# ----------------------------------------------------------------------------------------------

def check_bank_pin(run: dict, pr) -> str:
    """The bank a run actually scored must be the bank the preregistration pinned."""
    banks = pr.require("population", "banks")
    if run["bank"] not in banks:
        _fail(f"{run['dir']}: bank {run['bank']!r} is not declared in the preregistration's "
              f"population.banks ({sorted(banks)})")
    want = banks[run["bank"]].get("bank_file_sha16")
    if not want:
        _fail(f"prereg bank {run['bank']}: bank_file_sha16 is null")
    fp = run["bank_path"] if os.path.isabs(run["bank_path"]) else os.path.join(REPO, run["bank_path"])
    if not os.path.exists(fp):
        _fail(f"{run['dir']}: scored bank does not exist on disk: {fp}")
    got = _file_sha16(fp)
    if got != want:
        _fail(f"{run['dir']}: bank {run['bank']} hashes {got} on disk but the preregistration "
              f"pins {want} -- the scored artifact is not the frozen one")
    return got


def check_rows_written(run: dict, rows: list):
    if run["done"] is None:
        return
    want = run["done"].get("rows_written")
    if want is None:
        _fail(f"{run['dir']}: DONE.json declares no rows_written")
    if want != len(rows):
        _fail(f"{run['dir']}: DONE.json says rows_written={want} but results.jsonl carries "
              f"{len(rows)} rows -- a truncated or double-written ledger")
    if run["done"].get("status") != "ok":
        _fail(f"{run['dir']}: DONE.json status is {run['done'].get('status')!r}, not 'ok'")


def check_domain_coverage(run: dict, rows: list, split_map: dict, exclusions: set):
    """Every manifest domain must appear, unless it is a PREREGISTERED exclusion.  A missing row
    for any other reason is a refusal -- 'a missing row is acceptable only if its domain is a
    preregistered exclusion'."""
    seen = {r["domain"] for r in rows}
    unknown = seen - set(split_map)
    if unknown:
        _fail(f"{run['dir']}: {len(unknown)} domain(s) in the results are not in the split "
              f"manifest: {sorted(unknown)[:5]}")
    missing = set(split_map) - seen
    bad = sorted(missing - exclusions)
    if bad:
        _fail(f"{run['dir']}: {len(bad)} manifest domain(s) have NO rows and are not "
              f"preregistered exclusions: {bad[:8]}")

    # A WHOLLY-ABSENT domain is not the only way rows go missing, and it is the less likely one.
    # basket_bomb lost SIXTEEN rows to `resolve:occurrence_count_mismatch` -- the C-075 'basket'
    # inside 'basketball.' case -- and every one of them is school_campus, which is a
    # preregistered exclusion. A set-difference check would have seen school_campus present (32 of
    # its 48 rows survived) and passed. So count rows PER DOMAIN: any domain short of the modal
    # count is a refusal unless it is a preregistered exclusion.
    per_dom = collections.Counter(r["domain"] for r in rows)
    modal = collections.Counter(per_dom.values()).most_common(1)[0][0]
    short = sorted(d for d, n in per_dom.items() if n != modal and d not in exclusions)
    if short:
        _fail(f"{run['dir']}: {len(short)} domain(s) carry fewer than the modal {modal} rows and "
              f"are not preregistered exclusions: "
              + ", ".join(f"{d}={per_dom[d]}" for d in short[:8]))
    partial = sorted(d for d, n in per_dom.items() if n != modal)
    return sorted(missing & exclusions), partial, modal


def check_option_mass_gate(runs: list) -> float:
    """The gate the RUNS enforced, read back off their own config.  Refuse if they disagree: a
    table that pools runs scored under different gates is comparing different instruments."""
    vals = {}
    for r in runs:
        v = r["cfg"].get("args", {}).get("min_option_mass")
        if v is None:
            _fail(f"{r['dir']}: config.json declares no args.min_option_mass -- the gate the run "
                  f"enforced is unknown, so it cannot be reported")
        vals.setdefault(float(v), []).append(r["bank"])
    if len(vals) != 1:
        _fail(f"runs disagree on the option-mass gate they enforced: "
              + "; ".join(f"{k}={v}" for k, v in vals.items()))
    return next(iter(vals))


def join_and_validate(run: dict, rows: list, bank: dict, split_map: dict,
                      exclusions: set) -> list:
    """Join each results row to its bank row and check that the two agree about what the row IS.

    THE OCCURRENCE RECOUNT.  The bank carries `n_concept_occurrences`; this recounts the concept
    word in `full_prompt` with a WORD-BOUNDARY rule and refuses on disagreement.  That is the
    C-075/C-087 bug class -- a checker's notion of 'an occurrence' differing from the generator's
    ('basket' inside 'basketball', 'handgun' rewritten to 'handbutton' by a boundary-free
    str.replace).  It also counts bare substring occurrences: a substring count ABOVE the
    word-boundary count means the concept is present lexically in a form no whole-word leak check
    can see, and is reported as a leak.
    """
    out = []
    for r in rows:
        pid = r.get("prompt_id")
        b = bank.get(pid)
        if b is None:
            _fail(f"{run['dir']}: results prompt_id {pid!r} is not in the scored bank -- the "
                  f"join binds nothing for this row")
        for k in ("prompt_sha16", "domain", "cell", "condition", "query_kind", "n_examples"):
            if r.get(k) != b.get(k):
                _fail(f"{run['dir']}: prompt_id {pid}: results {k}={r.get(k)!r} but the bank row "
                      f"says {b.get(k)!r} -- the join is wrong or one artifact drifted")
        if r["domain"] in exclusions:
            continue
        dsplit = split_map[r["domain"]]

        concept, codeword = b["concept"], b["codeword"]
        wb = len(re.findall(r"\b" + re.escape(concept) + r"\b", b["full_prompt"], re.I))
        sub = b["full_prompt"].lower().count(concept.lower())
        if wb != b["n_concept_occurrences"]:
            _fail(f"{run['dir']}: prompt_id {pid}: bank says n_concept_occurrences="
                  f"{b['n_concept_occurrences']} but a word-boundary recount of {concept!r} in "
                  f"full_prompt finds {wb}. The checker's notion of an occurrence is not the "
                  f"generator's; refusing rather than reporting either number.")
        om = r.get("option_mass")
        if om is None or (isinstance(om, float) and math.isnan(om)) or not (0.0 <= om <= 1.0 + 1e-6):
            _fail(f"{run['dir']}: prompt_id {pid}: option_mass={om!r} is not a probability")
        p_c, p_w = r["p_concept"], r["p_codeword"]
        denom = p_c + p_w
        if denom <= 0:
            _fail(f"{run['dir']}: prompt_id {pid}: p_concept + p_codeword = {denom!r}; "
                  f"concept_binary_prob is undefined and must not be defaulted to 0.5")
        out.append({
            "bank": run["bank"], "run_dir": run["dir"],
            "prompt_id": pid,
            "concept": concept, "codeword": codeword,
            "domain": r["domain"], "dsplit": dsplit,
            "n_examples": r["n_examples"],
            "template": "|".join(str(b[k]) for k in ("role_style", "example_position",
                                                     "consistency", "strength", "family_slot",
                                                     "bank_block")),
            "cell": r["cell"], "condition": r["condition"], "query_kind": r["query_kind"],
            "intended_mapping": (f"{codeword}->{b['target_semantic']}" if r["cell"] == "C"
                                 else f"{codeword}->{codeword} (literal)"),
            "logp_concept": r["logp_concept"], "logp_codeword": r["logp_codeword"],
            "p_concept": p_c, "p_codeword": p_w,
            "concept_binary_prob": p_c / denom,
            "semantic_logodds": r["semantic_logodds"],
            "option_mass": om,
            "top1_id": r["top1_id"],
            "n_concept_occurrences": b["n_concept_occurrences"],
            "concept_leaks_into_full_prompt": bool(b["n_concept_occurrences"] > 0 or sub > wb),
            "n_concept_substring_occurrences": sub,
            "n_variants_concept": r.get("n_variants_concept"),
            "n_variants_codeword": r.get("n_variants_codeword"),
        })
    if not out:
        _fail(f"{run['dir']}: the join produced ZERO analysed rows -- zero-row bind")
    return out


def attach_decoded(rows: list, tokenizer) -> None:
    """`top1_id` -> its surface piece.  With no tokenizer the column is the id and says so, rather
    than a blank that would read as 'the model produced nothing'."""
    cache: dict = {}
    for r in rows:
        tid = r["top1_id"]
        if tokenizer is None:
            r["decoded_answer"] = f"<token_id:{tid}>"
            continue
        if tid not in cache:
            cache[tid] = tokenizer.decode([tid])
        r["decoded_answer"] = cache[tid]


# ----------------------------------------------------------------------------------------------
# installation
# ----------------------------------------------------------------------------------------------

def resolve_installation_rule(pr, args) -> dict:
    """Where the installation cut comes from.  If the preregistration declares one, it wins.  If
    it does not -- and as of this writing NO frozen config on disk declares an installation
    threshold, and there is no `configs/dcs_ts_pr054*.json` at all -- the script REFUSES unless an
    unregistered cut is passed explicitly AND acknowledged, and then stamps every row with
    `installation_rule_source=unregistered_cli` so no downstream reader can mistake it for a
    preregistered gate."""
    try:
        thr = pr.require("installation", "concept_binary_prob_threshold")
        return {"threshold": float(thr), "source": "prereg"}
    except Exception:
        pass
    if args.installation_threshold is None:
        _fail("no installation threshold is declared in the preregistration "
              f"({pr.path}: installation.concept_binary_prob_threshold) and none was passed. "
              "Refusing to invent one. Pass --installation-threshold T "
              "--ack-unregistered-threshold; it will be stamped unregistered_cli in every row.")
    if not args.ack_unregistered_threshold:
        _fail("--installation-threshold was passed but the preregistration declares none. "
              "Pass --ack-unregistered-threshold to record explicitly that this cut is NOT "
              "preregistered.")
    return {"threshold": float(args.installation_threshold), "source": "unregistered_cli"}


def label_installation(rows: list, rule: dict) -> None:
    """Per-row status.  Three labels, and NONE of them removes a row.

    INSTALLED / NOT_INSTALLED   cell C at a non-zero dose: the demonstrations assert the mapping,
                                so `concept_binary_prob` above/below the cut is uptake or its
                                absence.
    LITERAL_CONTROL             cell A: the demonstrations are benign and the intended answer is
                                the literal codeword.  'Installed' is not defined here; the row is
                                the contrast the C rows are read against.
    NULL_DOSE0                  n_examples == 0.  Per `C-081` there is no demonstration block at
                                all, so the arms are the SAME PROMPT and anything above chance is
                                a pipeline defect rather than a finding.  Labelled, never scored.
    """
    t = rule["threshold"]
    for r in rows:
        if r["n_examples"] == 0:
            r["installation_status"] = "NULL_DOSE0"
        elif r["cell"] == "C":
            r["installation_status"] = ("INSTALLED" if r["concept_binary_prob"] >= t
                                        else "NOT_INSTALLED")
        else:
            r["installation_status"] = "LITERAL_CONTROL"
        r["installation_rule_source"] = rule["source"]


# ----------------------------------------------------------------------------------------------
# statistics
# ----------------------------------------------------------------------------------------------

def quantiles(vals: list) -> dict:
    if not vals:
        _fail("quantiles() received ZERO values -- zero-row bind")
    s = sorted(vals)
    def q(p):
        if len(s) == 1:
            return s[0]
        i = p * (len(s) - 1)
        lo, hi = int(math.floor(i)), int(math.ceil(i))
        return s[lo] + (s[hi] - s[lo]) * (i - lo)
    return {"n": len(s), "min": s[0], "p10": q(.10), "p25": q(.25), "median": q(.50),
            "p75": q(.75), "p90": q(.90), "max": s[-1],
            "frac_ge_1pct": sum(v >= 0.01 for v in s) / len(s)}


def domain_means(rows: list, key: str) -> dict:
    acc = collections.defaultdict(list)
    for r in rows:
        acc[r["domain"]].append(r[key])
    if not acc:
        _fail("domain_means() bound ZERO domains -- zero-row bind")
    return {d: statistics.fmean(v) for d, v in acc.items()}


def paired_domain_permutation(a_by_domain: dict, b_by_domain: dict, n_perm: int, seed: int):
    """Group permutation at the DOMAIN level, arm-label flip within domain -- the test the
    preregistration names, and the only unit that is legitimate here (row-level FPR is 0.20 on
    this corpus).  Returns (observed delta, p, floor, n_domains).  p is ALWAYS reported beside
    its attainable floor 1/(B+1); on zero exceedances the caller prints 'p < floor'."""
    doms = sorted(set(a_by_domain) & set(b_by_domain))
    if not doms:
        _fail("paired_domain_permutation bound ZERO domains -- zero-row bind")
    d = [b_by_domain[x] - a_by_domain[x] for x in doms]
    obs = statistics.fmean(d)
    rng = random.Random(seed)
    n_ge = 0
    for _ in range(n_perm):
        m = statistics.fmean([v if rng.random() < 0.5 else -v for v in d])
        if abs(m) >= abs(obs) - 1e-12:
            n_ge += 1
    floor = 1.0 / (n_perm + 1)
    return obs, (n_ge + 1) / (n_perm + 1), floor, len(doms)


# ----------------------------------------------------------------------------------------------
# report
# ----------------------------------------------------------------------------------------------

def emit(args, pr, runs, all_rows, gate, rule, missing_by_run, banks_expected):
    W = print

    W("=" * 100)
    W("MANDATE SECTION 15 -- PROMPT-VALIDATION / INSTALLATION TABLE")
    W("=" * 100)
    W(f"preregistration      {pr.path}  (status {pr.obj.get('status')})")
    W(f"split manifest       {pr.require('split','manifest')}  field={pr.require('split','field')}")
    W(f"option-mass gate     {gate}  (read off each run's config.json args.min_option_mass)")
    W(f"installation rule    concept_binary_prob >= {rule['threshold']}  "
      f"source={rule['source']}")
    if rule["source"] != "prereg":
        W("                     ^^ NOT PREREGISTERED. There is no configs/dcs_ts_pr054*.json on "
          "disk and no")
        W("                        frozen config declares an installation cut. Treat this as a "
          "descriptive")
        W("                        stratification, never as a gate that anything passed or "
          "failed.")
    W("")

    W("--- RUN COVERAGE " + "-" * 83)
    have = {r["bank"] for r in runs if r["complete"]}
    for r in runs:
        st = "COMPLETE" if r["complete"] else "RUNNING/INCOMPLETE (no DONE.json)"
        W(f"  {r['bank']:14s} {st:34s} {os.path.basename(r['dir'])}")
    missing = [b for b in banks_expected if b not in have]
    if missing:
        W(f"  MISSING (not analysed below): {', '.join(missing)}")
    W(f"  analysed banks: {len(have)}/{len(banks_expected)}")
    for b, (ex, partial, modal) in sorted(missing_by_run.items()):
        W(f"  {b}: modal rows/domain={modal}; exclusion domains wholly absent: "
          f"{', '.join(ex) if ex else '(none)'}; domains short of modal (all preregistered "
          f"exclusions, else the run would have been refused): "
          f"{', '.join(partial) if partial else '(none)'}")
    W("")

    W("--- FAILURE LEDGERS (from each run's summary.json) " + "-" * 49)
    for r in runs:
        if not r["complete"]:
            continue
        f = r["summary"]["failures"]
        W(f"  {r['bank']:14s} attempted={f['n_attempted']} succeeded={f['n_succeeded']} "
          f"failed={f['n_failed']} reasons={f['failure_reasons'] or '{}'}")
    W("")

    # ---------- 1. OPTION MASS / ENGAGEMENT ----------
    W("=" * 100)
    W("1. OPTION MASS -- IS THE CHANNEL ENGAGED AT ALL?")
    W("=" * 100)
    W("PR-057: 'a disengaged primary channel is CANNOT ANSWER, not a licence to fall back on the")
    W("display channel.'  option_mass = P(the forced answer is one of {concept, literal}) --")
    W("the probability the two scored options are even what comes next.")
    W("")
    W(f"{'channel':22s} {'cell':5s} {'dose':5s} {'n':>6s} {'min':>9s} {'p10':>9s} {'p25':>9s} "
      f"{'median':>9s} {'p75':>9s} {'p90':>9s} {'max':>9s} {'>=1%':>7s} {'>=gate':>7s}")
    for ch in (PRIMARY_CHANNEL, DISPLAY_CHANNEL):
        for cell in ("A", "C"):
            for dose in (0, 4):
                sub = [r for r in all_rows if r["query_kind"] == ch and r["cell"] == cell
                       and r["n_examples"] == dose]
                if not sub:
                    _fail(f"stratum {ch}/{cell}/n={dose} bound ZERO rows -- zero-row bind")
                q = quantiles([r["option_mass"] for r in sub])
                fg = sum(r["option_mass"] >= gate for r in sub) / len(sub)
                W(f"{ch:22s} {cell:5s} {dose:<5d} {q['n']:6d} {q['min']:9.3g} {q['p10']:9.3g} "
                  f"{q['p25']:9.3g} {q['median']:9.3g} {q['p75']:9.3g} {q['p90']:9.3g} "
                  f"{q['max']:9.3g} {q['frac_ge_1pct']:7.3f} {fg:7.3f}")
    W("")
    W("per concept, primary channel, cell C, dose 4:")
    for c in sorted({r["concept"] for r in all_rows}):
        sub = [r for r in all_rows if r["concept"] == c and r["query_kind"] == PRIMARY_CHANNEL
               and r["cell"] == "C" and r["n_examples"] == 4]
        if not sub:
            _fail(f"concept {c} bound ZERO rows in the primary cell -- zero-row bind")
        q = quantiles([r["option_mass"] for r in sub])
        W(f"  {c:6s} n={q['n']:5d}  median={q['median']:.4g}  p10={q['p10']:.4g}  "
          f"p90={q['p90']:.4g}  frac>=1%={q['frac_ge_1pct']:.3f}")
    # THE VERDICT IS TAKEN IN THE PRIMARY ANALYSIS CELL, not over every row.  Pooling dose 0 into
    # the same median would mix a cell with no demonstration block at all into the engagement
    # statement, and the dose-0 rows sit BELOW the gate -- reporting one pooled number would hide
    # that engagement is dose-dependent.
    cell_c4 = [r["option_mass"] for r in all_rows if r["query_kind"] == PRIMARY_CHANNEL
               and r["cell"] == "C" and r["n_examples"] == 4]
    d0 = [r["option_mass"] for r in all_rows if r["query_kind"] == PRIMARY_CHANNEL
          and r["n_examples"] == 0]
    allp = [r["option_mass"] for r in all_rows if r["query_kind"] == PRIMARY_CHANNEL]
    q4, q0, qa = quantiles(cell_c4), quantiles(d0), quantiles(allp)
    W("")
    W(f"VERDICT (primary analysis cell = {PRIMARY_CHANNEL}, cell C, dose 4):")
    W(f"  median option_mass = {q4['median']:.4g} vs gate {gate}; "
      f"{q4['frac_ge_1pct']:.1%} of rows carry >= 1% of the next-token mass; "
      f"p10 = {q4['p10']:.4g}.")
    W(f"  => the channel is "
      f"{'ENGAGED' if q4['median'] >= gate else 'DISENGAGED (CANNOT ANSWER on the primary)'} "
      f"in the primary cell.")
    W(f"  dose-0 rows median {q0['median']:.4g} -- BELOW the gate; pooled over all doses the "
      f"median is {qa['median']:.4g}.")
    W("  This is three to four ORDERS OF MAGNITUDE above the ~1e-5 the phase recorded as its")
    W("  worry before running, so the pre-registered CANNOT-ANSWER trigger does NOT fire. It is")
    W("  still a minority of the next-token mass: most of the time the model's preferred answer")
    W("  is a THIRD word, which section 6 lists.")
    W("")

    # ---------- 2. INSTALLATION, PER CONCEPT ----------
    W("=" * 100)
    W("2. DOES THE CONCEPT INSTALL?  PER CONCEPT, NEVER POOLED (mandate section 3)")
    W("=" * 100)
    for ch in (PRIMARY_CHANNEL, DISPLAY_CHANNEL):
        W(f"--- channel {ch}")
        W(f"  {'concept':8s} {'cell':5s} {'dose':5s} {'split':11s} {'n':>5s} {'dom':>4s} "
          f"{'med cbp':>9s} {'mean cbp':>9s} {'med logodds':>12s} {'frac>=cut':>10s} "
          f"{'dom inst':>9s}")
        for c in sorted({r["concept"] for r in all_rows}):
            for cell in ("C", "A"):
                for dose in (4, 0):
                    for sp in ("train", "validation", "test", "ALL"):
                        sub = [r for r in all_rows if r["concept"] == c and r["query_kind"] == ch
                               and r["cell"] == cell and r["n_examples"] == dose
                               and (sp == "ALL" or r["dsplit"] == sp)]
                        if not sub:
                            _fail(f"stratum {c}/{ch}/{cell}/n={dose}/{sp} bound ZERO rows")
                        cbp = [r["concept_binary_prob"] for r in sub]
                        dm = domain_means(sub, "concept_binary_prob")
                        di = sum(v >= rule["threshold"] for v in dm.values()) / len(dm)
                        W(f"  {c:8s} {cell:5s} {dose:<5d} {sp:11s} {len(sub):5d} {len(dm):4d} "
                          f"{statistics.median(cbp):9.4f} {statistics.fmean(cbp):9.4f} "
                          f"{statistics.median([r['semantic_logodds'] for r in sub]):12.4f} "
                          f"{sum(v >= rule['threshold'] for v in cbp)/len(cbp):10.3f} "
                          f"{di:9.3f}")
        W("")

    # PER BANK, so the CODEWORD is not pooled either. bomb is carried by two banks (button_bomb
    # and basket_bomb); averaging them would hide a lexical-transfer difference in exactly the
    # column mandate section 15 asks to be keyed on.
    W("--- per bank (concept x codeword), cell C dose 4, domain-mean concept_binary_prob")
    W(f"  {'bank':14s} {'channel':22s} {'dom':>4s} {'median':>8s} {'p25':>8s} {'p75':>8s} "
      f"{'installing':>12s}")
    for bk in sorted({r["bank"] for r in all_rows}):
        for ch in (PRIMARY_CHANNEL, DISPLAY_CHANNEL):
            sub = [r for r in all_rows if r["bank"] == bk and r["query_kind"] == ch
                   and r["cell"] == "C" and r["n_examples"] == 4]
            if not sub:
                _fail(f"bank {bk} / {ch} bound ZERO rows in cell C dose 4 -- zero-row bind")
            dm = domain_means(sub, "concept_binary_prob")
            q = quantiles(list(dm.values()))
            n_i = sum(v >= rule["threshold"] for v in dm.values())
            W(f"  {bk:14s} {ch:22s} {q['n']:4d} {q['median']:8.4f} {q['p25']:8.4f} "
              f"{q['p75']:8.4f} {n_i:5d}/{q['n']:<6d}")
    W("")

    W("--- installation effect: cell C (doublespeak demos) vs cell A (benign demos) at dose 4")
    W("    domain-level paired permutation, arm-label flip within domain; DESCRIPTIVE, not a")
    W("    preregistered hypothesis and carrying no multiplicity claim.")
    n_perm = int(pr.require("primary", "n_perm"))
    alpha = pr.require("primary", "alpha")
    W(f"    n_perm={n_perm}  alpha={alpha}  attainable floor = 1/(B+1) = {1/(n_perm+1):.4g}")
    for ch in (PRIMARY_CHANNEL, DISPLAY_CHANNEL):
        for c in sorted({r["concept"] for r in all_rows}):
            A = [r for r in all_rows if r["concept"] == c and r["query_kind"] == ch
                 and r["cell"] == "A" and r["n_examples"] == 4]
            C = [r for r in all_rows if r["concept"] == c and r["query_kind"] == ch
                 and r["cell"] == "C" and r["n_examples"] == 4]
            obs, p, floor, nd = paired_domain_permutation(
                domain_means(A, "concept_binary_prob"),
                domain_means(C, "concept_binary_prob"), n_perm, args.seed)
            ps = f"< {floor:.4g}" if p <= floor + 1e-12 else f"= {p:.4g}"
            W(f"    {ch:22s} {c:6s} delta(C-A) = {obs:+.4f} over {nd} domains   p {ps} "
              f"(floor {floor:.4g})")
    W("")

    # ---------- 3. STRATIFICATION, NOT FILTERING ----------
    W("=" * 100)
    W("3. INSTALLATION AS A STRATIFIER -- NON-INSTALLING DOMAINS ARE NOT DROPPED")
    W("=" * 100)
    W("Mandate section 15: installation is a preregistered STRATIFICATION variable and a reported")
    W("descriptive limit, NEVER a post-hoc exclusion.  The distribution below is the deliverable;")
    W("no row anywhere in this script is removed for failing it.")
    W("")
    for ch in (PRIMARY_CHANNEL, DISPLAY_CHANNEL):
        W(f"--- channel {ch}: domain-mean concept_binary_prob, cell C dose 4")
        for c in sorted({r["concept"] for r in all_rows}):
            sub = [r for r in all_rows if r["concept"] == c and r["query_kind"] == ch
                   and r["cell"] == "C" and r["n_examples"] == 4]
            dm = domain_means(sub, "concept_binary_prob")
            q = quantiles(list(dm.values()))
            inst = sorted(d for d, v in dm.items() if v >= rule["threshold"])
            W(f"  {c:6s} domains={q['n']:3d}  min={q['min']:.4f} p10={q['p10']:.4f} "
              f"p25={q['p25']:.4f} med={q['median']:.4f} p75={q['p75']:.4f} p90={q['p90']:.4f} "
              f"max={q['max']:.4f}")
            W(f"         installing domains {len(inst)}/{q['n']}  "
              f"by split: " + ", ".join(
                  f"{sp}={sum(1 for d in inst if d in {r['domain'] for r in sub if r['dsplit']==sp})}"
                  f"/{len({r['domain'] for r in sub if r['dsplit']==sp})}"
                  for sp in ("train", "validation", "test")))
        W("")
    W("  sensitivity of the count to the (unregistered) cut, primary channel, cell C dose 4:")
    W(f"    {'cut':>6s} " + " ".join(f"{c:>10s}" for c in
                                     sorted({r['concept'] for r in all_rows})))
    for cut in (0.1, 0.25, 0.5, 0.75, 0.9):
        cells = []
        for c in sorted({r["concept"] for r in all_rows}):
            sub = [r for r in all_rows if r["concept"] == c
                   and r["query_kind"] == PRIMARY_CHANNEL and r["cell"] == "C"
                   and r["n_examples"] == 4]
            dm = domain_means(sub, "concept_binary_prob")
            cells.append(f"{sum(v>=cut for v in dm.values()):3d}/{len(dm):<3d}")
        W(f"    {cut:6.2f} " + " ".join(f"{x:>10s}" for x in cells))
    W("")

    # ---------- 4. THE DOSE-0 NULL ----------
    W("=" * 100)
    W("4. THE n_examples = 0 ROWS -- A NULL, NOT A RESULT (C-081)")
    W("=" * 100)
    W("At dose 0 no demonstration block is emitted, so the arms are the SAME PROMPT.  Anything")
    W("above chance here is a pipeline defect, not a finding.")
    W("")
    for ch in (PRIMARY_CHANNEL, DISPLAY_CHANNEL):
        for c in sorted({r["concept"] for r in all_rows}):
            A = [r for r in all_rows if r["concept"] == c and r["query_kind"] == ch
                 and r["cell"] == "A" and r["n_examples"] == 0]
            C = [r for r in all_rows if r["concept"] == c and r["query_kind"] == ch
                 and r["cell"] == "C" and r["n_examples"] == 0]
            da = domain_means(A, "concept_binary_prob")
            dc = domain_means(C, "concept_binary_prob")
            ident = sum(1 for d in da if abs(da[d] - dc[d]) < 1e-9)
            W(f"  {ch:22s} {c:6s} A median cbp={statistics.median(list(da.values())):.4f}  "
              f"C median cbp={statistics.median(list(dc.values())):.4f}  "
              f"domains with A==C to 1e-9: {ident}/{len(da)}")
    W("")

    # ---------- 5. LEAKAGE ----------
    W("=" * 100)
    W("5. DOES THE CONCEPT WORD LEAK INTO full_prompt?")
    W("=" * 100)
    W(f"  {'channel':22s} {'cell':5s} {'dose':5s} {'n':>6s} {'rows leaking':>13s} "
      f"{'median n_occ':>13s}")
    for ch in (PRIMARY_CHANNEL, DISPLAY_CHANNEL):
        for cell in ("A", "C"):
            for dose in (0, 4):
                sub = [r for r in all_rows if r["query_kind"] == ch and r["cell"] == cell
                       and r["n_examples"] == dose]
                if not sub:
                    _fail(f"leak stratum {ch}/{cell}/{dose} bound ZERO rows")
                lk = sum(r["concept_leaks_into_full_prompt"] for r in sub)
                W(f"  {ch:22s} {cell:5s} {dose:<5d} {len(sub):6d} {lk:6d} ({lk/len(sub):6.1%}) "
                  f"{statistics.median([r['n_concept_occurrences'] for r in sub]):13.1f}")
    W("")

    # ---------- 6. DECODED ANSWERS ----------
    W("=" * 100)
    W("6. THE DECODED ANSWER (argmax first token after the 'Answer:' prefix; NOT a generation --")
    W("   these runs wrote a zero-byte gens.jsonl and summary.json reports n_generations: 0)")
    W("=" * 100)
    for ch in (PRIMARY_CHANNEL, DISPLAY_CHANNEL):
        for c in sorted({r["concept"] for r in all_rows}):
            for cell in ("C", "A"):
                sub = [r for r in all_rows if r["query_kind"] == ch and r["concept"] == c
                       and r["cell"] == cell and r["n_examples"] == 4]
                cnt = collections.Counter(r["decoded_answer"] for r in sub)
                top = ", ".join(f"{k!r} {v}" for k, v in cnt.most_common(5))
                W(f"  {ch:22s} {c:6s} cell {cell} n=4: {top}")
    W("")

    # ---------- 7. THE ROW TABLE ----------
    W("=" * 100)
    W("7. SECTION-15 ROW TABLE")
    W("=" * 100)
    W("columns (derived columns marked *): " + ", ".join(
        (c + "*" if c in DERIVED_COLUMNS else c) for c in COLUMNS))
    W(f"rows analysed: {len(all_rows)}")
    if args.emit_csv:
        import csv
        with open(args.emit_csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
            w.writeheader()
            for r in all_rows:
                r = dict(r)
                r["failures"] = ""      # per-row: the runs report n_failed=0; the ledger is above
                w.writerow(r)
        W(f"written: {args.emit_csv}")
    else:
        W("(pass --emit-csv PATH to write the full per-row table; first 5 rows shown)")
        for r in all_rows[:5]:
            W("  " + " | ".join(f"{c}={r.get(c, '')}" for c in COLUMNS[:12]))
    W("")


# ----------------------------------------------------------------------------------------------
# mutation harness
# ----------------------------------------------------------------------------------------------

def mutate(pr, runs, split_map, exclusions) -> int:
    """Every refusal above must be REACHABLE.  A guard nobody has seen fire is not a guard."""
    run = next(r for r in runs if r["complete"])
    bank = load_bank(os.path.join(REPO, run["bank_path"]) if not os.path.isabs(run["bank_path"])
                     else run["bank_path"])
    rows = load_results(run)

    results = []

    def case(name, fn):
        try:
            fn()
        except ValidationError as e:
            results.append((name, True, str(e).split("\n")[0][:88]))
        else:
            results.append((name, False, "NO REFUSAL"))

    # 1 bank hash
    def m1():
        p2 = copy.deepcopy(pr.obj)
        p2["population"]["banks"][run["bank"]]["bank_file_sha16"] = "0" * 16
        from dcs_ts_prereg import Prereg
        check_bank_pin(run, Prereg(p2, "MUTANT"))
    case("bank sha disagrees with disk", m1)

    # 2 a non-excluded manifest domain has no rows
    def m2():
        victim = next(d for d in split_map if d not in exclusions)
        check_domain_coverage(run, [r for r in rows if r["domain"] != victim], split_map, exclusions)
    case("non-excluded domain missing", m2)

    # 3 a domain the manifest does not know
    def m3():
        r2 = copy.deepcopy(rows[:50]) + [dict(rows[0], domain="atlantis")]
        check_domain_coverage(run, r2, split_map, exclusions)
    case("domain absent from the manifest", m3)

    # 3b a NON-excluded domain short of the modal row count (the C-075 shape)
    def m3b():
        victim = next(d for d in split_map if d not in exclusions)
        seen = 0
        keep = []
        for r in rows:
            if r["domain"] == victim and seen < 3:
                seen += 1
                continue
            keep.append(r)
        check_domain_coverage(run, keep, split_map, exclusions)
    case("non-excluded domain short of modal rows", m3b)

    # 4 duplicate prompt_id in the bank
    def m4():
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            b = list(bank.values())[:3]
            for x in b + [b[0]]:
                f.write(json.dumps(x) + "\n")
            p = f.name
        try:
            load_bank(p)
        finally:
            os.unlink(p)
    case("duplicate prompt_id in bank", m4)

    # 5 results prompt_id not in the bank
    def m5():
        join_and_validate(run, [dict(rows[0], prompt_id="deadbeef")], bank, split_map, exclusions)
    case("results prompt_id absent from bank", m5)

    # 6 join disagreement
    def m6():
        join_and_validate(run, [dict(rows[0], prompt_sha16="0" * 16)], bank, split_map, exclusions)
    case("prompt_sha16 disagrees with bank", m6)

    # 7 occurrence recount disagreement
    def m7():
        b2 = copy.deepcopy(bank)
        b2[rows[0]["prompt_id"]]["n_concept_occurrences"] += 1
        join_and_validate(run, [rows[0]], b2, split_map, exclusions)
    case("n_concept_occurrences != recount", m7)

    # 8 option_mass NaN
    def m8():
        join_and_validate(run, [dict(rows[0], option_mass=float("nan"))], bank, split_map,
                          exclusions)
    case("option_mass is NaN", m8)

    # 9 rows_written disagreement
    def m9():
        check_rows_written(run, rows[:-1])
    case("results count != DONE.rows_written", m9)

    # 10 runs disagree on the gate
    def m10():
        r2 = copy.deepcopy([r for r in runs if r["complete"]][:2])
        if len(r2) < 2:
            _fail("fewer than two complete runs; the disagreement guard is trivially reachable")
        r2[1]["cfg"]["args"]["min_option_mass"] = 0.99
        check_option_mass_gate(r2)
    case("runs disagree on the option-mass gate", m10)

    # 11 gate missing entirely
    def m11():
        r2 = copy.deepcopy([r for r in runs if r["complete"]][:1])
        r2[0]["cfg"]["args"].pop("min_option_mass")
        check_option_mass_gate(r2)
    case("run declares no min_option_mass", m11)

    # 12 zero-row bind
    def m12():
        join_and_validate(run, [r for r in rows if r["domain"] in exclusions][:5] or
                          [dict(rows[0], domain=sorted(exclusions)[0])], bank, split_map,
                          exclusions)
    case("zero analysed rows after exclusions", m12)

    # 13 unregistered installation cut, unacknowledged
    def m13():
        ns = argparse.Namespace(installation_threshold=0.5, ack_unregistered_threshold=False)
        resolve_installation_rule(pr, ns)
    case("unregistered cut without acknowledgement", m13)

    # 14 no installation cut at all
    def m14():
        ns = argparse.Namespace(installation_threshold=None, ack_unregistered_threshold=False)
        resolve_installation_rule(pr, ns)
    case("no installation cut declared or passed", m14)

    # 15 empty quantile bind
    case("quantiles() on zero values", lambda: quantiles([]))
    # 16 empty domain bind
    case("domain_means() on zero rows", lambda: domain_means([], "concept_binary_prob"))
    # 17 empty run discovery
    case("no run directories match", lambda: discover_runs("outputs/does_not_exist_*"))

    print("=== MUTATION HARNESS: every refusal must be reachable ===")
    n_red = 0
    for name, red, detail in results:
        n_red += red
        print(f"  {'RED  ' if red else 'GREEN'}  {name:44s} {detail}")
    print(f"[mutate] {n_red}/{len(results)} mutations produced a refusal")
    if n_red != len(results):
        print("  A GREEN ROW IS AN UNREACHABLE REFUSAL, WHICH IS NOT A GUARD.", file=sys.stderr)
        return 1
    return 0


# ----------------------------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--prereg", default="configs/dcs_ts_pr057_phase9.json")
    ap.add_argument("--runs-glob", default="outputs/boombness/score_behavior/ts116m_readout_*")
    ap.add_argument("--installation-threshold", type=float, default=None,
                    help="concept_binary_prob cut for the installation STRATIFIER. Only used when "
                         "the preregistration declares none, and then only with "
                         "--ack-unregistered-threshold.")
    ap.add_argument("--ack-unregistered-threshold", action="store_true")
    ap.add_argument("--emit-csv", default=None)
    ap.add_argument("--seed", type=int, default=20260907)
    ap.add_argument("--no-tokenizer", action="store_true",
                    help="skip detokenising top1_id; the decoded_answer column becomes "
                         "<token_id:N> rather than a blank")
    ap.add_argument("--mutate", action="store_true")
    args = ap.parse_args()

    pr = load_prereg(args.prereg)          # refuses on unfrozen status / null sha / missing field

    manifest_rel = pr.require("split", "manifest")
    manifest = json.load(open(os.path.join(REPO, manifest_rel)))
    field = pr.require("split", "field")
    if manifest.get("field_name") != field:
        _fail(f"{manifest_rel}: field_name={manifest.get('field_name')!r} but the preregistration "
              f"declares split.field={field!r}")
    split_map = dict(manifest["assign"])
    if not split_map:
        _fail(f"{manifest_rel}: assign is EMPTY -- zero-row bind")
    exclusions = {e["domain"] for e in pr.require("population", "preregistered_exclusions")
                  if e.get("whole_population")}
    if not exclusions:
        _fail("the preregistration declares no whole-population exclusions; this phase has three "
              "and their absence would mean the wrong config was loaded")

    runs = discover_runs(args.runs_glob)
    banks_expected = sorted(pr.require("population", "banks"))

    if args.mutate:
        return mutate(pr, runs, split_map, exclusions)

    rule = resolve_installation_rule(pr, args)
    complete = [r for r in runs if r["complete"]]
    if not complete:
        _fail("no readout run has a DONE.json + summary.json -- nothing has landed yet")
    gate = check_option_mass_gate(complete)

    all_rows: list = []
    missing_by_run: dict = {}
    for run in complete:
        check_bank_pin(run, pr)
        rows = load_results(run)
        check_rows_written(run, rows)
        missing_by_run[run["bank"]] = check_domain_coverage(run, rows, split_map, exclusions)
        bank = load_bank(run["bank_path"] if os.path.isabs(run["bank_path"])
                         else os.path.join(REPO, run["bank_path"]))
        all_rows.extend(join_and_validate(run, rows, bank, split_map, exclusions))

    n_dom = len({r["domain"] for r in all_rows})
    want_dom = pr.require("split", "n_domains_analysed")
    if n_dom != want_dom:
        _fail(f"after the preregistered exclusions {n_dom} domains remain, but the "
              f"preregistration declares n_domains_analysed={want_dom}")

    tok = None
    if not args.no_tokenizer:
        try:
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            from transformers import AutoTokenizer
            models = {r["model"] for r in
                      (json.loads(l) for l in open(os.path.join(complete[0]["dir"],
                                                                "results.jsonl")))}
            if len(models) != 1:
                _fail(f"the run scored {len(models)} different models {sorted(models)}; "
                      f"one decoded_answer column cannot stand for two tokenizers")
            tok = AutoTokenizer.from_pretrained(next(iter(models)))
        except Exception as e:                      # noqa: BLE001
            print(f"[warn] tokenizer unavailable ({type(e).__name__}: {e}); decoded_answer will "
                  f"carry raw token ids", file=sys.stderr)
    attach_decoded(all_rows, tok)
    label_installation(all_rows, rule)

    emit(args, pr, runs, all_rows, gate, rule, missing_by_run, banks_expected)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValidationError as e:
        print(f"\nREFUSING: {e}", file=sys.stderr)
        raise SystemExit(2)
