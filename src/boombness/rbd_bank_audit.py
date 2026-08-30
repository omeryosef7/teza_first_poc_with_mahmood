"""Independent bank audit for the RBD confirmatory sprint. 2026-08-29.

DELIBERATELY DOES NOT IMPORT `prompt_families`.

§22: "For independent verification, write a separate analysis that does NOT import the producing
analysis module. The purpose is to detect the same bug twice, not reproduce it twice." Every count,
id, hash and invariant below is re-derived from the SHIPPED `.jsonl` alone. If this module imported
the generator's own `check_alignment`, a bug in that function would be reproduced rather than
caught -- and `RBD-R-004` is a live example of the generator's alignment guard being blind to a real
defect in its own output.

`RBD-DR-001` found the following §4.2 audits MISSING from the repo, and they are implemented here:
post-hoc recomputation of every count from the shipped rows; demo-pool independence; duplicate
prompt-TEXT detection; in-bank lexical collision; condition / n_examples balance with a stated
expected design; prompt-length distributions and cross-condition length matching; and Readout
coverage per family stem.

Token-level checks (alignment, occurrence positions, single-token options) are NOT duplicated here:
`tokenization_audit.py` already performs them on both models and is reused rather than rewritten.

CLI
    python src/boombness/rbd_bank_audit.py --bank <bank.jsonl> [--bank <other.jsonl> ...] \
        --expect rows=960,domains=20,stems=80,attack_rows=80 [--out <path.json>]

Exit 0 if every check passes, 1 otherwise. There is no lenient mode: a check that cannot certify
returns FAIL rather than a warning.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import statistics
import sys
from typing import Any, Dict, List, Optional, Sequence

SCHEMA = "RBD_BANK_AUDIT/1"

#: Orthographic-vowel false positives: correct English `a` before a /juː/ onset. `RBD-C-005` --
#: every committed bank in this repo carries this class, so a bare "zero bad articles" gate would
#: fail them all. The substantive clause is that the CODEWORD and CONCEPT must not appear here.
ARTICLE_FALSE_POSITIVES = {"unique", "uniform", "uniformed", "unicorn", "union", "unit", "united",
                           "universal", "university", "usage", "use", "used", "useful", "user",
                           "usual", "utility", "european", "one", "once"}

VOWELS = set("aeiouAEIOU")

#: Correct English `an` before an orthographic consonant (silent h, letter names). Without this,
#: a single `an hour` in any pool sentence fails every bank with no escape hatch, and the failure
#: reads as a real article defect. `RBD-C-007` (F9).
#: `RAH-R-003`: "led" added 2026-08-30. The pool sentence "An LED lantern provided crisp
#: illumination ..." is CORRECT English -- "LED" is a letter-name onset /el/, the same class as the
#: "x-ray"/"mba"/"fbi" entries already here. It surfaces only at n_examples=16 (`rbd12_n16`), which
#: draws deeper into the 20-sentence pool than n=8 ever did, so no committed n=8 bank contains it.
#: Adding it CANNOT weaken the substantive clause: `target_hit` is computed from the raw counters,
#: not from the allowlisted remainder, so a codeword or concept after a wrong article still fails
#: even if that word is on this list. `test_allowlisting_a_word_cannot_suppress_clause_3` proves it.
AN_BEFORE_CONSONANT_OK = {"hour", "hours", "honest", "honestly", "honour", "honourable", "honor",
                          "honorable", "heir", "heirloom", "x-ray", "mba", "fbi", "hourly", "led"}

READOUTS = ("behavioral", "semantic_forced_choice", "mapping_use_forced_choice")


def _stem(row: Dict[str, Any]) -> str:
    """family_id minus its trailing query_kind field. One stem spans all four 2x2 cells."""
    return row["family_id"].rpartition("|")[0]


def _mask(text: str, word: str) -> str:
    return re.sub(r"\b%s\b" % re.escape(word), "@@", text, flags=re.IGNORECASE)


def load_rows(path: str) -> List[Dict[str, Any]]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


# --------------------------------------------------------------------------- #
# Individual checks. Each returns (ok: bool, detail: dict).
# --------------------------------------------------------------------------- #
def check_ids_and_hashes(rows) -> tuple:
    """Re-derive prompt_sha16 from full_prompt, and prompt_id from family_id|condition."""
    bad_sha, bad_pid = [], []
    for r in rows:
        if hashlib.sha256(r["full_prompt"].encode()).hexdigest()[:16] != r["prompt_sha16"]:
            bad_sha.append(r["prompt_id"])
        want = hashlib.sha256((r["family_id"] + "|" + r["condition"]).encode()).hexdigest()[:16]
        if want != r["prompt_id"]:
            bad_pid.append(r["prompt_id"])
    return (not bad_sha and not bad_pid), {
        "n_rows": len(rows), "n_bad_prompt_sha16": len(bad_sha), "n_bad_prompt_id": len(bad_pid),
        "examples_bad_sha": bad_sha[:5], "examples_bad_pid": bad_pid[:5]}


def check_duplicates(rows) -> tuple:
    """Duplicate prompt_id AND duplicate prompt TEXT. The second is not checked anywhere else."""
    ids = collections.Counter(r["prompt_id"] for r in rows)
    dup_ids = {k: v for k, v in ids.items() if v > 1}
    texts = collections.defaultdict(list)
    for r in rows:
        texts[r["full_prompt"]].append(r["prompt_id"])
    dup_text = {v[0]: len(v) for v in texts.values() if len(v) > 1}
    return (not dup_ids and not dup_text), {
        "n_duplicate_prompt_ids": len(dup_ids), "n_duplicate_prompt_texts": len(dup_text),
        "examples_duplicate_text": list(dup_text)[:5]}


def check_balance(rows, expect_query_kinds=READOUTS) -> tuple:
    """Every categorical axis must be exactly balanced; the design has no unbalanced axis."""
    out, ok = {}, True
    for field in ("condition", "query_kind", "split", "n_examples", "domain", "family_slot"):
        c = collections.Counter(str(r[field]) for r in rows)
        out[f"by_{field}"] = dict(sorted(c.items()))
        if len(set(c.values())) != 1:
            ok = False
            out.setdefault("unbalanced", []).append(field)
    got = set(out["by_query_kind"])
    if got != set(expect_query_kinds):
        ok = False
        out["query_kind_mismatch"] = {"expected": sorted(expect_query_kinds), "got": sorted(got)}
    return ok, out


def check_readout_coverage(rows, expect_stems: Optional[int] = None) -> tuple:
    """BC-C-24: every behavioural family stem must also carry every readout.

    F3. The expectation MUST come from outside the rows. The first version computed
    `expect = n_domains * n_splits * n_slots` from the rows being checked, so deleting an entire
    domain moved both sides of the identity and the whole audit certified a 19-domain bank as
    PASS -- a 5% power loss against a design pre-registered at 20 domains. EXECUTED: dropping all
    48 rows of one domain left all nine checks True.

    A self-derived expectation is not an expectation.
    """
    by = collections.defaultdict(set)
    for r in rows:
        by[_stem(r)].add(r["query_kind"])
    missing = {s: sorted(set(READOUTS) - k) for s, k in by.items() if set(READOUTS) - k}
    ok = (not missing) and len(by) > 0
    detail = {"n_stems": len(by), "n_stems_missing_a_readout": len(missing),
              "examples": {k: missing[k] for k in list(missing)[:5]}}
    if expect_stems is None:
        detail["expect_stems"] = None
        detail["NOT_ASSERTED"] = ("no pre-registered stem count supplied; coverage is reported "
                                  "but NOT certified")
        ok = False
    else:
        detail["expect_stems"] = expect_stems
        detail["stems_match_design"] = (len(by) == expect_stems)
        ok = ok and len(by) == expect_stems
    return ok, detail


#: The ONLY contrasts the 2x2 claims are single-factor. The four cells cross demo VALENCE with
#: target SURFACE, so cells drawn from different pools legitimately differ in demonstration text --
#: requiring all four to be identical after masking is a stronger invariant than the design ever
#: asserted, and it was my first version of this check (`RBD-C-006`).
ALIGNED_PAIRS = (("direct_harmful", "natural_doublespeak"),
                 ("concept_in_benign_ctx", "benign_literal"))


def check_single_factor(rows) -> tuple:
    """PROMPT-TEMPLATE EQUIVALENCE, re-derived independently of the generator's own guard.

    Within a family stem and query kind, each ALIGNED PAIR (same demonstration valence, differing
    only in the target surface) must be byte-identical after masking each cell's own
    `target_surface`. This is the invariant `apple` failed with 12 violations.

    Query kinds that name BOTH words cannot satisfy it -- cell B's query reads
    "... poison ... lantern or ... poison" where cell C's reads "... lantern ... lantern or ...
    poison" -- so they are reported as NOT CHECKED rather than as passing. That distinction is
    `tokenization_audit`'s own hard-won lesson ("returning [] for an unchecked family made the
    summary read '540 families, 0 violations' when only 216 had been examined").
    """
    # F1/F2. Two defects fixed here, both EXECUTED against the shipped bank before the fix:
    #   (1) computing `unsafe_kinds` over the whole bank meant ONE stray row with the flag False
    #       silently removed that entire query kind from the check while `ok` stayed True -- an
    #       injected real violation went undetected at 160 pairs checked instead of 480;
    #   (2) `.get(..., True)` meant a producer that OMITS the field is treated as safe.
    # The flag must be PRESENT on every row and CONSTANT within a query kind; anything else is a
    # malformed bank and is refused rather than silently reshaping the coverage.
    flags: Dict[str, set] = collections.defaultdict(set)
    for r in rows:
        if "occurrence_analysis_safe" not in r:
            raise ValueError(f"row {r.get('prompt_id')!r} has no occurrence_analysis_safe field; "
                             f"refusing to guess (a missing flag must not default to 'safe')")
        flags[r["query_kind"]].add(bool(r["occurrence_analysis_safe"]))
    inconsistent = {k: sorted(v) for k, v in flags.items() if len(v) != 1}
    if inconsistent:
        raise ValueError(f"occurrence_analysis_safe is not constant within query kind(s) "
                         f"{inconsistent}; one stray row would silently disable a whole kind")
    unsafe_kinds = {k for k, v in flags.items() if v == {False}}

    by = collections.defaultdict(dict)
    for r in rows:
        by[(_stem(r), r["query_kind"])][r["condition"]] = r
    bad, checked, skipped = [], 0, 0
    for (stem, qk), cells in by.items():
        if qk in unsafe_kinds:
            skipped += 1
            continue
        for hi, lo in ALIGNED_PAIRS:
            if hi not in cells or lo not in cells:
                skipped += 1
                continue
            checked += 1
            a = _mask(cells[hi]["full_prompt"], cells[hi]["target_surface"])
            b = _mask(cells[lo]["full_prompt"], cells[lo]["target_surface"])
            if a != b:
                bad.append({"stem": stem, "query_kind": qk, "pair": [hi, lo]})
    return (not bad and checked > 0), {
        "n_aligned_pairs_checked": checked, "n_violations": len(bad),
        "n_skipped_not_checkable": skipped,
        "skipped_query_kinds": sorted(unsafe_kinds),
        "skipped_note": "NOT CHECKED is not the same as passed",
        "examples": bad[:5]}


def check_articles(rows, codeword: str, concept: str) -> tuple:
    """RBD-C-005's corrected gate. Orthographic test, so /juu/ onsets are expected false positives."""
    bad_a, bad_an = collections.Counter(), collections.Counter()
    for r in rows:
        # RE.IGNORECASE on the ARTICLE too (F8): without it the SENTENCE-INITIAL form of the very
        # defect this exists for -- "A apple" -- never matches, and the audit is blind exactly
        # where a regression of the generator's repair would land.
        for m in re.finditer(r"\b(an?)\s+([A-Za-z][A-Za-z-]*)", r["full_prompt"], re.IGNORECASE):
            art, w = m.group(1).lower(), m.group(2).lower()
            if art == "a" and w[0] in VOWELS:
                bad_a[w] += 1
            elif art == "an" and w[0] not in VOWELS:
                bad_an[w] += 1
    unexpected = {w: n for w, n in bad_a.items() if w not in ARTICLE_FALSE_POSITIVES}
    unexpected_an = {w: n for w, n in bad_an.items() if w not in AN_BEFORE_CONSONANT_OK}
    target_hit = {w: n for w, n in list(bad_a.items()) + list(bad_an.items())
                  if w in (codeword.lower(), concept.lower())}
    ok = not unexpected_an and not unexpected and not target_hit
    return ok, {"an_before_consonant_total": sum(bad_an.values()),
                "an_before_consonant_by_word": dict(bad_an),
                "a_before_vowel_total": sum(bad_a.values()),
                "a_before_vowel_by_word": dict(bad_a),
                "unexpected_words": unexpected,
                "unexpected_an_words": unexpected_an,
                "codeword_or_concept_flagged": target_hit,
                "note": ("clause 3 (codeword/concept must not appear after EITHER article) is the "
                         "substantive one; the two allowlists are the instrument's calibration")}


def check_lexical_collisions(rows, codeword: str, concept: str) -> tuple:
    """The word that should NOT be in a cell must not be there.

    `benign_literal` and `natural_doublespeak` carry the codeword surface; `direct_harmful` and
    `concept_in_benign_ctx` carry the concept. The OTHER word must not appear in the demo block --
    an incidental occurrence would leak the mapping.
    """
    bad = []
    for r in rows:
        other = concept if r["target_surface"].lower() == codeword.lower() else codeword
        db = r.get("demo_block") or ""
        n = len(re.findall(r"\b%s\b" % re.escape(other), db, flags=re.IGNORECASE))
        if n:
            bad.append({"prompt_id": r["prompt_id"], "condition": r["condition"],
                        "leaked_word": other, "count": n})
    return (not bad), {"n_rows_with_leak": len(bad), "examples": bad[:5]}


def check_occurrences(rows, codeword: str, concept: str) -> tuple:
    """Codeword/concept occurrence counts, re-counted from the text rather than trusted."""
    mism = []
    dist = collections.Counter()
    for r in rows:
        n = len(re.findall(r"\b%s\b" % re.escape(r["target_surface"]), r["full_prompt"],
                           flags=re.IGNORECASE))
        dist[n] += 1
        rec = r.get("n_target_occurrences")
        if rec is not None and rec != n:
            mism.append({"prompt_id": r["prompt_id"], "recorded": rec, "recounted": n})
    return (not mism), {"n_recorded_vs_recounted_mismatches": len(mism),
                        "target_occurrence_distribution": dict(sorted(dist.items())),
                        "examples": mism[:5]}


def check_lengths(rows, codeword: str, concept: str) -> tuple:
    """Prompt-length distribution, and length matching WITHIN each aligned pair.

    A length difference the masked-identity test cannot see would be a confound: masking compares
    AFTER substitution, so a longer target word is invisible to it. But the comparison must be
    within an ALIGNED PAIR -- across valences the demonstration pools differ by design, so a
    cross-valence spread is a property of the 2x2, not a defect (`RBD-C-006`).

    The expected gap is exact, not a tolerance: (len(codeword) - len(concept)) x occurrences.
    """
    delta_w = len(codeword) - len(concept)
    out: Dict[str, Any] = {}
    ok = True
    for qk in sorted({r["query_kind"] for r in rows}):
        sub = [r for r in rows if r["query_kind"] == qk]
        per: Dict[str, Any] = {}
        for cond in sorted({r["condition"] for r in sub}):
            L = sorted(len(r["full_prompt"]) for r in sub if r["condition"] == cond)
            per[cond] = {"n": len(L), "min": L[0], "p50": statistics.median(L), "max": L[-1],
                         "mean": round(statistics.fmean(L), 2)}
        # F5. The expected gap is driven by the occurrences that actually DIFFER between the two
        # cells. `semantic_forced_choice` names BOTH words in its query, so each prompt also
        # carries one occurrence of the NON-target word, and the true gap is
        # delta_w * (occ_target - occ_other), not delta_w * occ_target. Counting both words from
        # the text makes the model general instead of per-kind, and removes the need for slack:
        # before this fix the shipped bank showed residual 1.0 on that kind, absorbed only by a
        # 2.0-char tolerance, so any pair with |len(cw)-len(cn)| > 2 would have FALSE-FAILED.
        occ_t, occ_o = [], []
        for r in sub:
            tgt = r["target_surface"]
            other = concept if tgt.lower() == codeword.lower() else codeword
            occ_t.append(len(re.findall(r"\b%s\b" % re.escape(tgt), r["full_prompt"], re.I)))
            occ_o.append(len(re.findall(r"\b%s\b" % re.escape(other), r["full_prompt"], re.I)))
        mean_occ = (statistics.fmean(occ_t) - statistics.fmean(occ_o)) if occ_t else 0.0
        pairs_ok = True
        for hi, lo in ALIGNED_PAIRS:
            if hi not in per or lo not in per:
                continue
            # `lo` carries the codeword surface, `hi` the concept surface.
            observed = per[lo]["mean"] - per[hi]["mean"]
            expected = delta_w * mean_occ
            gap = abs(observed - expected)
            per[f"aligned_gap:{lo}-{hi}"] = {
                "observed_chars": round(observed, 2), "expected_chars": round(expected, 2),
                "residual_chars": round(gap, 2), "ok": gap <= 0.5}
            pairs_ok = pairs_ok and gap <= 0.5
        per["mean_differing_occurrences"] = round(mean_occ, 2)
        per["cross_valence_spread_chars_EXPECTED_BY_DESIGN"] = round(
            max(v["mean"] for k, v in per.items() if isinstance(v, dict) and "mean" in v)
            - min(v["mean"] for k, v in per.items() if isinstance(v, dict) and "mean" in v), 2)
        per["aligned_pairs_ok"] = pairs_ok
        ok = ok and pairs_ok
        out[qk] = per
    return ok, out


def check_pool_independence(bank_rows_by_name: Dict[str, List[Dict[str, Any]]]) -> tuple:
    """Demo-pool independence.

    (a) WITHIN a bank: two different family slots in the same (domain, split) must not share a
        demonstration sentence -- that is what `slots=[0, 3]` at n=8 is supposed to guarantee, and
        it is the property G2 was retracted for assuming.
    (b) ACROSS banks: the two lexical pairs were generated from separate pools, so they must share
        no demonstration sentence at all.
    """
    detail: Dict[str, Any] = {}
    ok = True

    for name, rows in bank_rows_by_name.items():
        overlaps = []
        by = collections.defaultdict(dict)
        for r in rows:
            # F4. The first version filtered to natural_doublespeak only, which draws from the
            # HARM pool. benign_literal and concept_in_benign_ctx draw from a DIFFERENT pool with
            # an independent length, and `_take` starts at (slot*3) % len(pool) -- so slot
            # disjointness there was never verified. EXECUTED: copying slot 0's demo_block onto
            # the other slot for benign_literal rows left this check reporting 0 overlaps.
            # Keying on condition and n_examples too, because disjointness is dose-dependent.
            if r["query_kind"] != "behavioral":
                continue
            key = (r["domain"], r["split"], r["condition"], r["n_examples"])
            by[key][r["family_slot"]] = set(
                ln for ln in (r.get("demo_block") or "").split("\n") if ln.strip())
        for key, slots in by.items():
            ks = sorted(slots)
            for i in range(len(ks)):
                for j in range(i + 1, len(ks)):
                    shared = {s for s in (slots[ks[i]] & slots[ks[j]]) if s.strip()}
                    if shared:
                        overlaps.append({"domain": key[0], "split": key[1], "condition": key[2],
                                         "n_examples": key[3],
                                         "slots": [ks[i], ks[j]], "n_shared": len(shared)})
        detail[f"{name}:within_bank_slot_overlaps"] = len(overlaps)
        detail[f"{name}:within_bank_examples"] = overlaps[:5]
        detail[f"{name}:n_groups_checked"] = len(by)
        detail[f"{name}:conditions_covered"] = sorted({k[2] for k in by})
        if overlaps or not by:
            ok = False

    names = sorted(bank_rows_by_name)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = {s for r in bank_rows_by_name[names[i]]
                 for s in (r.get("demo_block") or "").split("\n") if s.strip()}
            b = {s for r in bank_rows_by_name[names[j]]
                 for s in (r.get("demo_block") or "").split("\n") if s.strip()}
            shared = a & b
            detail[f"{names[i]}|{names[j]}:shared_demo_sentences"] = len(shared)
            if shared:
                ok = False
                detail[f"{names[i]}|{names[j]}:examples"] = sorted(shared)[:3]
    return ok, detail


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def audit_bank(path: str, rows: Optional[List[Dict[str, Any]]] = None,
               expect: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
    """Audit one shipped bank. `expect` is the PRE-REGISTERED design, and without it the bank is
    reported but NOT certified (F3)."""
    rows = load_rows(path) if rows is None else rows
    if not rows:
        return {"bank": path, "PASS": False, "why": "no rows"}
    cw = sorted({r["codeword"] for r in rows})
    cn = sorted({r["concept"] for r in rows})
    expect = expect or {}

    res: Dict[str, Any] = {"bank": path, "codewords": cw, "concepts": cn}
    res["one_pair_per_bank"] = {"ok": len(cw) == 1 and len(cn) == 1,
                                "codewords": cw, "concepts": cn}
    ok_all = res["one_pair_per_bank"]["ok"]
    if not ok_all:
        res["PASS"] = False
        return res

    for name, fn, args in (
        ("ids_and_hashes", check_ids_and_hashes, (rows,)),
        ("duplicates", check_duplicates, (rows,)),
        ("balance", check_balance, (rows,)),
        ("readout_coverage", check_readout_coverage, (rows, expect.get("stems"))),
        ("single_factor", check_single_factor, (rows,)),
        ("articles", check_articles, (rows, cw[0], cn[0])),
        ("lexical_collisions", check_lexical_collisions, (rows, cw[0], cn[0])),
        ("occurrences", check_occurrences, (rows, cw[0], cn[0])),
        ("lengths", check_lengths, (rows, cw[0], cn[0])),
    ):
        ok, detail = fn(*args)
        res[name] = {"ok": bool(ok), **detail}
        ok_all = ok_all and bool(ok)

    # F3. Absolute, pre-registered counts. A self-derived expectation is not an expectation.
    observed = {"rows": len(rows),
                "domains": len({r["domain"] for r in rows}),
                "stems": len({_stem(r) for r in rows}),
                "attack_rows": sum(1 for r in rows if r["query_kind"] == "behavioral"
                                   and r["condition"] == "natural_doublespeak")}
    if expect:
        bad = {k: {"expected": v, "observed": observed.get(k)}
               for k, v in expect.items() if observed.get(k) != v}
        res["design"] = {"ok": not bad, "expected": expect, "observed": observed,
                         "mismatches": bad}
    else:
        res["design"] = {"ok": False, "expected": None, "observed": observed,
                         "NOT_ASSERTED": ("no --expect supplied; the bank is REPORTED but NOT "
                                          "CERTIFIED. Deleting a whole domain passes every "
                                          "row-derived check.")}
    ok_all = ok_all and res["design"]["ok"]

    res.update(observed)
    res["n_rows"] = observed["rows"]
    res["n_domains"] = observed["domains"]
    res["n_family_stems"] = observed["stems"]
    res["n_behavioural_attack_rows"] = observed["attack_rows"]
    res["PASS"] = ok_all
    return res


def _parse_expect(spec: str) -> Dict[str, int]:
    """`rows=960,domains=20,stems=80,attack_rows=80`."""
    out: Dict[str, int] = {}
    for part in (spec or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"--expect item {part!r} is not key=value")
        k, v = part.split("=", 1)
        k = k.strip()
        if k not in ("rows", "domains", "stems", "attack_rows"):
            raise ValueError(f"--expect key {k!r} unknown; use rows/domains/stems/attack_rows")
        out[k] = int(v)
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", action="append", required=True)
    ap.add_argument("--expect", default="",
                    help="PRE-REGISTERED design, e.g. rows=960,domains=20,stems=80,"
                         "attack_rows=80. Applied to EVERY --bank. Without it the audit reports "
                         "but does not certify: a bank missing a whole domain passes every "
                         "row-derived check (F3).")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    expect = _parse_expect(args.expect)
    rows_by_name = {os.path.basename(b): load_rows(b) for b in args.bank}   # read once (F15)
    per = [audit_bank(b, rows=rows_by_name[os.path.basename(b)], expect=expect)
           for b in args.bank]
    pool_ok, pool_detail = check_pool_independence(rows_by_name)

    report = {"schema": SCHEMA, "expect": expect or None, "banks": per,
              "pool_independence": {"ok": pool_ok, **pool_detail},
              "PASS": all(p.get("PASS") for p in per) and pool_ok}

    for p in per:
        print(f"\n=== {os.path.basename(p['bank'])} ===")
        print(f"  rows={p.get('n_rows')} domains={p.get('n_domains')} "
              f"stems={p.get('n_family_stems')} attack_rows={p.get('n_behavioural_attack_rows')} "
              f"{p.get('codewords')}|{p.get('concepts')}")
        for k, v in p.items():
            if isinstance(v, dict) and "ok" in v:
                print(f"  [{'PASS' if v['ok'] else 'FAIL'}] {k}")
                if not v["ok"]:
                    for kk, vv in v.items():
                        if kk != "ok":
                            print(f"        {kk}: {vv}")
    print(f"\n=== pool independence === [{'PASS' if pool_ok else 'FAIL'}]")
    for k, v in pool_detail.items():
        print(f"  {k}: {v}")
    print(f"\nOVERALL: {'PASS' if report['PASS'] else 'FAIL'}")

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(report, f, indent=1)
        print(f"wrote {args.out}")
    return 0 if report["PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
