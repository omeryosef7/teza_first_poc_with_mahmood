"""demo_deletion_control.py — a ROW-SPECIFIC demonstration-deletion control (plan §7, Phase 2C).

WHY THIS EXISTS (prev-REVIEW-2 M1). The old `score_behavior.py --demo-deleted` arm generated from
`row["final_query_text"]`. That field takes exactly TWO distinct values across all 1152 behavioral
rows of the committed bank, so a 96-row "deletion ceiling" was ONE prompt, ONE generation, ONE judge
score, reported as a 96-row population estimate. The headline it produced ("demonstration knockout
recovers 100% of the deletion ceiling") was a single Bernoulli draw wearing a confidence interval.

WHAT THIS MODULE DOES INSTEAD. `delete_demonstrations(row)` operates on the row's OWN
`full_prompt`, excising exactly the recorded `demo_block` span and nothing else:

        full_prompt == prefix + demo_block + suffix          (verified, by hash)
        deleted_prompt := prefix + suffix

so the row's own query, wrapper, role framing and answer scaffold survive byte-for-byte, and the
row's identity fields (prompt_id, family_id, domain, n_examples) travel with the transformed record.
No whitespace is normalised and no separator is repaired: any such repair would edit NON-demo text,
which is the one thing this control is not allowed to do.

DIVERSITY IS MEASURED ON TEXT HASHES, NEVER ON LENGTHS OR ON ROW IDENTITY. Both blind spots have
already cost this project a retraction: the `uniq_frac` defect counted distinct LENGTHS and called
them distinct TEXT, and the `--demo-deleted` arm inferred diversity from the 96 distinct SOURCE rows
while every TRANSFORMED prompt was identical. `_diversity_key` therefore keys on the sha16 of the
TRANSFORMED prompt and on nothing else, and every hash is written into the artifact so the claim is
auditable after the fact.

PRE-REGISTERED THRESHOLD
    MIN_DISTINCT_FRAC = 0.90
        A deletion arm of N rows must yield at least ceil(0.90 * N) DISTINCT transformed prompts,
        i.e. accidental duplication introduced by the deletion may not exceed 10% of the arm.
        Exposed as `--min-distinct-frac`; lowering it is a deliberate, recorded act, and 0.0 is
        still refused as a way to switch the guard off. Below the threshold the run ABORTS (no
        DONE.json) rather than emitting a ceiling.

MEASURED ON THE COMMITTED BANK (data/boombness_prompts/boombness_prompt_bank.jsonl, 2736 rows),
canonical Phase-1 population (query_kind=behavioral, condition=natural_doublespeak,
bank_block in {core2x2, core2x2_slot3}, n_examples in {1,2,4,8}, n=96), all counts by sha256 hash:

        distinct full_prompt        96      (the rows really are 96 different prompts)
        distinct demo_block         96      (they differ in their demonstrations)
        distinct final_query_text    1      (the old arm's source field: ONE value)
        distinct prefix              1
        distinct suffix              1
        distinct deleted_prompt      1      <-- THE FINDING

    The 96 rows of the canonical population differ ONLY inside the demo block; the demo block is
    ~68% of the prompt by characters, and everything outside it is byte-identical across all 96.
    Across the whole behavioral bank (1152 rows) the demo-free residue takes just 9 distinct values.

    CONSEQUENCE FOR THE PLAN: on this bank the demonstration-deletion ceiling is NOT
    RECONSTRUCTIBLE, by this or by any other deletion rule. Deleting the demonstrations is exactly
    the operation that deletes all between-row variation, so the ceiling is one Bernoulli draw no
    matter how carefully the deletion is implemented. This is a property of the BANK, not of the
    old code. Phase 2C cannot produce a population ceiling until a bank exists whose rows differ
    OUTSIDE their demo blocks (varied queries / wrappers / domains). Running this module on the
    current bank ABORTS, by design and on purpose: that abort IS the deliverable.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import os
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import FailureLedger, RunDir, read_jsonl, DATA_DIR  # noqa: E402

# Pre-registered; see module docstring.
MIN_DISTINCT_FRAC = 0.90

#: Fields that make a transformed record joinable back to its source row.
IDENTITY_FIELDS = ("prompt_id", "family_id", "domain", "n_examples")

#: The canonical Phase-1 behavioural population (plan §7).
CANONICAL_POPULATION = {
    "query_kinds": ("behavioral",),
    "conditions": ("natural_doublespeak",),
    "bank_blocks": ("core2x2", "core2x2_slot3"),
    "n_examples": (1, 2, 4, 8),
}


class DeletionControlRefusal(RuntimeError):
    """Raised when a deletion arm is not a population: too few DISTINCT transformed prompts."""


def sha16(text: str) -> str:
    """sha256 of the UTF-8 bytes, truncated to 16 hex chars. Never returns text."""
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]


def select_canonical(rows: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The plan §7 population filter, kept in one place so the measurement is reproducible."""
    c = CANONICAL_POPULATION
    return [r for r in rows
            if r.get("query_kind") in c["query_kinds"]
            and r.get("condition") in c["conditions"]
            and r.get("bank_block") in c["bank_blocks"]
            and _as_int(r.get("n_examples")) in c["n_examples"]]


def _as_int(v: Any) -> Optional[int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------- #
# The transformation
# --------------------------------------------------------------------------- #
def delete_demonstrations(row: Dict[str, Any]) -> Dict[str, Any]:
    """Excise this row's OWN `demo_block` from its OWN `full_prompt`; change nothing else.

    Returns a record carrying the row's identity, the transformed prompt text, and the hashes
    that let a later auditor verify -- without ever seeing the text -- that the surrounding
    structure survived: `prefix_sha16`, `suffix_sha16`, `demo_block_sha16`,
    `source_prompt_sha16` (the ORIGINAL full_prompt) and `deleted_prompt_sha16`.

    Raises ValueError when the row cannot be transformed (no demo block, block absent from the
    prompt, block not unique in the prompt, or nothing left after deletion). Callers put those on
    the FailureLedger; none of them may be silently skipped.
    """
    pid = row.get("prompt_id")
    full = row.get("full_prompt") or ""
    blk = row.get("demo_block") or ""
    if not full:
        raise ValueError(f"no_full_prompt:{pid}")
    if not blk:
        raise ValueError(f"no_demo_block:{pid}")
    i = full.find(blk)
    if i < 0:
        raise ValueError(f"demo_block_not_in_full_prompt:{pid}")
    # A demo block occurring twice would make "delete the demonstrations" ambiguous: excising the
    # first occurrence leaves a copy behind, excising both may delete non-demo text. Refuse.
    if full.find(blk, i + 1) >= 0:
        raise ValueError(f"demo_block_not_unique_in_prompt:{pid}")
    prefix, suffix = full[:i], full[i + len(blk):]
    deleted = prefix + suffix
    if not deleted.strip():
        raise ValueError(f"empty_after_deletion:{pid}")

    rec = {k: row.get(k) for k in IDENTITY_FIELDS}
    rec.update({
        "deleted_prompt": deleted,               # text stays in memory; NEVER written to disk
        "deleted_prompt_sha16": sha16(deleted),
        "source_prompt_sha16": sha16(full),
        "demo_block_sha16": sha16(blk),
        "prefix_sha16": sha16(prefix),
        "suffix_sha16": sha16(suffix),
        "demo_char_offset": i,
        "n_chars_source": len(full),
        "n_chars_deleted": len(deleted),
        "n_chars_removed": len(blk),
        "bank_prompt_sha16": row.get("prompt_sha16"),
    })
    return rec


def transform_rows(rows: Sequence[Dict[str, Any]],
                   ledger: Optional[FailureLedger] = None):
    """Apply `delete_demonstrations` to every row, booking every failure on the ledger."""
    out: List[Dict[str, Any]] = []
    for r in rows:
        try:
            rec = delete_demonstrations(r)
        except ValueError as e:
            reason = str(e).split(":")[0]
            if ledger is not None:
                ledger.fail(f"deletion:{reason}", ident=str(r.get("prompt_id", "")))
            continue
        if ledger is not None:
            ledger.ok()
        out.append(rec)
    return out


# --------------------------------------------------------------------------- #
# Diversity, measured on TEXT HASHES
# --------------------------------------------------------------------------- #
def _diversity_key(rec: Dict[str, Any]) -> str:
    """THE diversity key: the sha16 of the TRANSFORMED prompt, and nothing else.

    Deliberately NOT `len(rec["deleted_prompt"])` (the uniq_frac defect: distinct LENGTHS are not
    distinct TEXT) and deliberately NOT `rec["source_prompt_sha16"]` (the --demo-deleted defect:
    distinct SOURCE rows are not distinct TRANSFORMED prompts). Tests mutate this function to each
    of those two and assert that a test goes red.
    """
    return rec["deleted_prompt_sha16"]


def diversity_report(records: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Distinct-transformed-prompt statistics, plus the full hash inventory for the artifact."""
    keys = [_diversity_key(r) for r in records]
    counts = collections.Counter(keys)
    n = len(keys)
    n_distinct = len(counts)
    largest = max(counts.values()) if counts else 0
    return {
        "n_rows": n,
        "n_distinct_transformed_prompts": n_distinct,
        "distinct_frac": (n_distinct / n) if n else 0.0,
        "largest_duplicate_group": largest,
        "duplicate_rows": n - n_distinct,
        "duplicate_frac": ((n - n_distinct) / n) if n else 0.0,
        "diversity_measured_on": "sha16(transformed_prompt_text)",
        "transformed_prompt_sha16_counts": dict(sorted(counts.items())),
        "n_distinct_source_prompts": len({r["source_prompt_sha16"] for r in records}),
        "n_distinct_demo_blocks": len({r["demo_block_sha16"] for r in records}),
        "n_distinct_prefixes": len({r["prefix_sha16"] for r in records}),
        "n_distinct_suffixes": len({r["suffix_sha16"] for r in records}),
        "n_distinct_lengths": len({r["n_chars_deleted"] for r in records}),
    }


def required_distinct(n_rows: int, min_distinct_frac: float = MIN_DISTINCT_FRAC) -> int:
    return int(math.ceil(min_distinct_frac * n_rows))


def check_diversity(report: Dict[str, Any],
                    min_distinct_frac: float = MIN_DISTINCT_FRAC) -> Dict[str, Any]:
    """REFUSE a deletion arm that is not a population. Returns the verdict block; raises on fail.

    `min_distinct_frac <= 0` is refused outright: an "off" setting for this guard is exactly the
    state that let a one-draw ceiling be published as a 96-row estimate.
    """
    if min_distinct_frac <= 0.0:
        raise DeletionControlRefusal(
            "REFUSING: --min-distinct-frac must be > 0. A deletion arm with no diversity floor is "
            "how a single Bernoulli draw gets reported as a population ceiling (prev-REVIEW-2 M1).")
    n = int(report["n_rows"])
    need = required_distinct(n, min_distinct_frac)
    got = int(report["n_distinct_transformed_prompts"])
    verdict = {
        "min_distinct_frac_preregistered": MIN_DISTINCT_FRAC,
        "min_distinct_frac_used": float(min_distinct_frac),
        "n_distinct_required": need,
        "n_distinct_observed": got,
        "passed": bool(n > 0 and got >= need),
    }
    if not verdict["passed"]:
        raise DeletionControlRefusal(
            f"REFUSING: the deletion arm has {got} DISTINCT transformed prompts over {n} rows "
            f"(distinct_frac={report['distinct_frac']:.3f}); the pre-registered floor requires "
            f"{need} (min_distinct_frac={min_distinct_frac}). Largest duplicate group: "
            f"{report['largest_duplicate_group']} rows. Diversity was measured on "
            f"{report['diversity_measured_on']}, not on lengths and not on source-row identity: "
            f"the arm carries {report['n_distinct_source_prompts']} distinct SOURCE prompts and "
            f"{report['n_distinct_lengths']} distinct lengths, and neither of those is a ceiling. "
            f"This bank's rows differ only inside their demo blocks, so the deletion ceiling is "
            f"not reconstructible here -- see the module docstring."
        )
    return verdict


def bank_diversity_census(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """By-hash census of the fields a deletion control could possibly draw diversity from."""
    def nd(fn):
        return len({sha16(fn(r)) for r in rows})
    census = {
        "n_rows": len(rows),
        "n_distinct_full_prompt": nd(lambda r: r.get("full_prompt") or ""),
        "n_distinct_demo_block": nd(lambda r: r.get("demo_block") or ""),
        "n_distinct_final_query_text": nd(lambda r: r.get("final_query_text") or ""),
        "n_distinct_prompt_id": len({r.get("prompt_id") for r in rows}),
        "census_measured_on": "sha256 hashes; no prompt text is read out",
    }
    return census


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bank", default=os.path.join(DATA_DIR, "boombness_prompt_bank.jsonl"))
    ap.add_argument("--min-distinct-frac", type=float, default=MIN_DISTINCT_FRAC,
                    help=f"pre-registered floor on DISTINCT transformed prompts / rows "
                         f"(default {MIN_DISTINCT_FRAC}); values <= 0 are refused")
    ap.add_argument("--tag", default="phase2c")
    ap.add_argument("--out-root", default=None)
    return ap


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    rows = select_canonical(read_jsonl(args.bank))
    run = RunDir("demo_deletion_control", args=args, tag=args.tag, out_root=args.out_root)
    run.note_bank(args.bank)
    ledger = FailureLedger()
    recs = transform_rows(rows, ledger=ledger)
    census = bank_diversity_census(rows)
    report = diversity_report(recs)
    for r in recs:
        run.log_row({k: r[k] for k in r if k != "deleted_prompt"})
    summary = {"population": {k: list(v) for k, v in CANONICAL_POPULATION.items()},
               "bank_census": census, "diversity": report}
    try:
        summary["diversity_verdict"] = check_diversity(report, args.min_distinct_frac)
    except DeletionControlRefusal as e:
        summary["diversity_verdict"] = {"passed": False, "reason": str(e)}
        run.abort("demo_deletion_control:insufficient_transformed_prompt_diversity",
                  summary=summary, ledger=ledger)
        print(str(e), file=sys.stderr)
        return 2
    run.finish(summary=summary, ledger=ledger)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
