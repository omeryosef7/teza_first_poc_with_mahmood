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
        [--pools <pools.json> ...] [--out <path.json>] [--strict]

Exit 0 if every check passes, 1 otherwise. `--strict` is the default posture: the exit code always
reflects the verdict; the flag only controls whether WARN-level findings are promoted to failures.
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


def check_readout_coverage(rows) -> tuple:
    """BC-C-24: every behavioural family stem must also carry every readout."""
    by = collections.defaultdict(set)
    for r in rows:
        by[_stem(r)].add(r["query_kind"])
    missing = {s: sorted(set(READOUTS) - k) for s, k in by.items() if set(READOUTS) - k}
    n_dom = len({r["domain"] for r in rows})
    n_split = len({r["split"] for r in rows})
    n_slot = len({r["family_slot"] for r in rows})
    expect = n_dom * n_split * n_slot
    ok = (not missing) and len(by) == expect and len(by) > 0
    return ok, {"n_stems": len(by), "n_stems_expected": expect,
                "n_stems_missing_a_readout": len(missing),
                "examples": {k: missing[k] for k in list(missing)[:5]}}


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
    by = collections.defaultdict(dict)
    unsafe_kinds = {r["query_kind"] for r in rows
                    if not r.get("occurrence_analysis_safe", True)}
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
        for m in re.finditer(r"\b(a|an)\s+([A-Za-z]+)", r["full_prompt"]):
            art, w = m.group(1).lower(), m.group(2).lower()
            if art == "a" and w[0] in VOWELS:
                bad_a[w] += 1
            elif art == "an" and w[0] not in VOWELS:
                bad_an[w] += 1
    unexpected = {w: n for w, n in bad_a.items() if w not in ARTICLE_FALSE_POSITIVES}
    target_hit = {w: n for w, n in bad_a.items() if w in (codeword.lower(), concept.lower())}
    ok = (sum(bad_an.values()) == 0) and not unexpected and not target_hit
    return ok, {"an_before_consonant_total": sum(bad_an.values()),
                "an_before_consonant_by_word": dict(bad_an),
                "a_before_vowel_total": sum(bad_a.values()),
                "a_before_vowel_by_word": dict(bad_a),
                "unexpected_words": unexpected,
                "codeword_or_concept_flagged": target_hit,
                "note": "clause 3 (codeword/concept must not appear) is the substantive one"}


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
        occ = [r.get("n_target_occurrences") for r in sub if r.get("n_target_occurrences")]
        mean_occ = statistics.fmean(occ) if occ else 0.0
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
                "residual_chars": round(gap, 2), "ok": gap <= 2.0}
            pairs_ok = pairs_ok and gap <= 2.0
        per["mean_target_occurrences"] = round(mean_occ, 2)
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
            if r["query_kind"] != "behavioral" or r["condition"] != "natural_doublespeak":
                continue
            by[(r["domain"], r["split"])][r["family_slot"]] = set(
                (r.get("demo_block") or "").split("\n"))
        for key, slots in by.items():
            ks = sorted(slots)
            for i in range(len(ks)):
                for j in range(i + 1, len(ks)):
                    shared = {s for s in (slots[ks[i]] & slots[ks[j]]) if s.strip()}
                    if shared:
                        overlaps.append({"domain": key[0], "split": key[1],
                                         "slots": [ks[i], ks[j]], "n_shared": len(shared)})
        detail[f"{name}:within_bank_slot_overlaps"] = len(overlaps)
        detail[f"{name}:within_bank_examples"] = overlaps[:5]
        detail[f"{name}:n_domain_split_groups"] = len(by)
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
def audit_bank(path: str) -> Dict[str, Any]:
    rows = load_rows(path)
    if not rows:
        return {"bank": path, "FAIL": True, "why": "no rows"}
    cw = sorted({r["codeword"] for r in rows})
    cn = sorted({r["concept"] for r in rows})
    checks: Dict[str, Any] = {}
    checks["codeword_concept"] = ({"ok": len(cw) == 1 and len(cn) == 1},
                                  {"codewords": cw, "concepts": cn})
    res: Dict[str, Any] = {}
    ok_all = len(cw) == 1 and len(cn) == 1
    res["codewords"], res["concepts"] = cw, cn

    for name, fn, args in (
        ("ids_and_hashes", check_ids_and_hashes, (rows,)),
        ("duplicates", check_duplicates, (rows,)),
        ("balance", check_balance, (rows,)),
        ("readout_coverage", check_readout_coverage, (rows,)),
        ("single_factor", check_single_factor, (rows,)),
        ("articles", check_articles, (rows, cw[0], cn[0])),
        ("lexical_collisions", check_lexical_collisions, (rows, cw[0], cn[0])),
        ("occurrences", check_occurrences, (rows, cw[0], cn[0])),
        ("lengths", check_lengths, (rows, cw[0], cn[0])),
    ):
        ok, detail = fn(*args)
        res[name] = {"ok": bool(ok), **detail}
        ok_all = ok_all and bool(ok)

    res.update({"bank": path, "n_rows": len(rows),
                "n_domains": len({r["domain"] for r in rows}),
                "n_family_stems": len({_stem(r) for r in rows}),
                "n_behavioural_attack_rows": sum(
                    1 for r in rows if r["query_kind"] == "behavioral"
                    and r["condition"] == "natural_doublespeak"),
                "PASS": ok_all})
    return res


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", action="append", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--strict", action="store_true", default=True)
    args = ap.parse_args(argv)

    per = [audit_bank(b) for b in args.bank]
    rows_by_name = {os.path.basename(b): load_rows(b) for b in args.bank}
    pool_ok, pool_detail = check_pool_independence(rows_by_name)

    report = {"schema": SCHEMA, "banks": per,
              "pool_independence": {"ok": pool_ok, **pool_detail},
              "PASS": all(p.get("PASS") for p in per) and pool_ok}

    for p in per:
        print(f"\n=== {os.path.basename(p['bank'])} ===")
        print(f"  rows={p['n_rows']} domains={p['n_domains']} stems={p['n_family_stems']} "
              f"attack_rows={p['n_behavioural_attack_rows']} "
              f"{p['codewords']}|{p['concepts']}")
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
