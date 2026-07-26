#!/usr/bin/env python3
"""Build disjoint, category-balanced ClearHarm manifests for the sprint (Phase B).

WARNING / LICENSING GATE
------------------------
ClearHarm is **NOT vendored** in this repository and this script does NOT download it.
It only *transforms* an already-obtained local ClearHarm file (CSV or parquet) into the
manifest CSVs used by the rest of the pipeline.

This script MUST NOT be run until the ClearHarm licensing / source decision is confirmed
by the user (see docs/CLEARHARM_STATUS.md). Obtaining the raw dataset is a separate,
manual, human-authorized step. Running this script implies you already hold a legitimately
licensed local copy at the path you pass to --input.

What it produces
----------------
Given --input <local ClearHarm CSV/parquet>, it writes four DISJOINT manifests under
data/manifests/ (override with --out-dir):

    clearharm_opt15.csv        optimization split      (default 15 rows)
    clearharm_val15.csv        validation split        (default 15 rows)
    clearharm_universal100.csv universal-trigger split (default 100 rows)
    clearharm_reserve.csv      everything else (reserve pool)

Split sizes follow the plan's 15 / 15 / 100 spec
(docs/SPRINT_COMPLETION_PLAN_MATAN_MAHMOOD.md sec "Phase B", lines 188-190 and 262-264).
If the licensed dataset is too small to honor 15/15/100 the script fails loudly rather
than silently shrinking a split; adjust --n-opt / --n-val / --n-universal explicitly and
document the change in docs/CLEARHARM_STATUS.md.

Column schema (must match data/manifests/dev_25.csv exactly)
------------------------------------------------------------
    task_id, source_dataset, split, category, instruction,
    target_prefix, target_style, duplicate_group, notes

Guarantees enforced
--------------------
* Disjoint splits (asserted; a row appears in at most one of opt/val/universal/reserve).
* Category-balanced allocation (round-robin over categories, largest-remainder).
* Near-duplicate detection: sentence-transformers embeddings if available, else a
  normalized-string / token-Jaccard fallback. Members of one duplicate cluster share a
  duplicate_group and are never split across opt/val/universal (they stay together or go
  to reserve) to prevent optimization<->validation leakage.
* Stable task_ids: content-hash based (clearharm_<12-hex>), deterministic across runs and
  independent of row ordering in the source file.
* Versioned target strings: target_prefix is generated from a named, versioned template
  (TARGET_TEMPLATE_VERSION) so the exact target text is reproducible and auditable.

Nothing is written under --dry-run; the allocation summary + overlap assertions still run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Versioning / constants
# ---------------------------------------------------------------------------

# Bump this whenever the target-string construction changes; it is recorded in the
# `notes` column so every produced target is traceable to a template version.
TARGET_TEMPLATE_VERSION = "v1"
TARGET_STYLE = "affirm_raw"  # matches dev_25.csv
SOURCE_DATASET = "clearharm"

# Exact header order of data/manifests/dev_25.csv. Do not reorder.
FIELDNAMES = [
    "task_id",
    "source_dataset",
    "split",
    "category",
    "instruction",
    "target_prefix",
    "target_style",
    "duplicate_group",
    "notes",
]

# Canonical category vocabulary already used by the AdvBench manifests
# (data/manifests/dev_25.csv, heldout_495.csv). Unknown ClearHarm categories are mapped
# to "other_uncategorized" and flagged in `notes`.
KNOWN_CATEGORIES = {
    "cyber_hacking_malware",
    "fraud_financial_crime",
    "misinformation_disinformation",
    "identity_theft_personal_data_theft",
    "weapons_explosives_mass_casualty",
    "violent_crime_physical_harm",
    "self_harm_suicide",
    "theft_property_crime",
    "hate_speech_discrimination",
    "harassment_bullying_stalking",
    "drugs_controlled_substances",
    "terrorism_extremism",
    "privacy_surveillance",
    "academic_minor_dishonesty_deception",
    "child_exploitation",
    "other_uncategorized",
}

# Candidate column names in a raw ClearHarm file, in priority order.
INSTRUCTION_COLS = ["instruction", "prompt", "goal", "behavior", "text", "query", "request"]
CATEGORY_COLS = ["category", "harm_category", "topic", "class", "label", "type"]
TARGET_COLS = ["target", "target_prefix", "affirmative_response", "target_response"]

NEAR_DUP_THRESHOLD = 0.92  # cosine sim (embedding) OR token-Jaccard (fallback)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_rows(input_path: Path) -> list[dict]:
    """Load the raw ClearHarm file (CSV or parquet) into a list of dict rows."""
    suffix = input_path.suffix.lower()
    if suffix in {".parquet", ".pq"}:
        try:
            import pandas as pd  # noqa: WPS433 (local import; optional dep)
        except ImportError as exc:  # pragma: no cover
            raise SystemExit(
                "Reading parquet requires pandas. Install pandas or export the "
                "ClearHarm file to CSV first."
            ) from exc
        df = pd.read_parquet(input_path)
        return df.to_dict(orient="records")
    if suffix in {".csv", ".tsv"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        with input_path.open(newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh, delimiter=delimiter))
    raise SystemExit(f"Unsupported input extension: {suffix!r} (use .csv/.tsv/.parquet)")


def pick_column(sample: dict, candidates: list[str]) -> str | None:
    """Return the first candidate column present in the row (case-insensitive)."""
    lowered = {k.lower(): k for k in sample.keys()}
    for cand in candidates:
        if cand in lowered:
            return lowered[cand]
    return None


# ---------------------------------------------------------------------------
# Normalization / target construction
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace — for dup detection + hashing."""
    text = (text or "").strip().lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_category(raw: str | None) -> tuple[str, str]:
    """Map a raw ClearHarm category onto the known vocabulary.

    Returns (category, note). If unknown, category='other_uncategorized' and a note
    records the original value so it is never silently dropped.
    """
    if not raw:
        return "other_uncategorized", "clearharm_category=<empty>"
    key = re.sub(r"[\s/\-]+", "_", str(raw).strip().lower())
    if key in KNOWN_CATEGORIES:
        return key, ""
    return "other_uncategorized", f"clearharm_category={raw!r}(unmapped)"


# Leading imperative verbs to strip when synthesizing an affirmation from an
# instruction, so "Write a script that ..." -> "Sure, here is a script that ..."
# (matches the dev_25.csv target style, which drops the imperative verb).
_LEAD_VERBS = {
    "write", "create", "develop", "give", "provide", "explain", "describe",
    "generate", "produce", "compose", "draft", "list", "outline", "design",
    "make", "build", "detail", "share", "tell", "show", "demonstrate",
}


def build_target_prefix(
    instruction: str, provided_target: str | None, strategy: str
) -> str:
    """Construct a versioned affirmative target prefix.

    strategy:
      - "source": use the dataset's own target verbatim; RAISE if the row has none
        (F2 fix — never silently emit a malformed synthetic target).
      - "affirm_verbstrip": synthesize "Sure, here is <instr minus leading imperative
        verb>" — grammatical, matches dev_25.csv style.
      - "affirm_raw": legacy "Sure, here is <lowercased instr>" (may be ungrammatical;
        opt-in only).
    """
    if strategy == "source":
        if not provided_target:
            raise SystemExit(
                "target-strategy=source but a row has no target column/value. "
                "Re-run with --target-strategy affirm_verbstrip to synthesize targets, "
                "and document the choice in docs/CLEARHARM_STATUS.md.\n"
                f"  offending instruction: {instruction[:80]!r}"
            )
        return str(provided_target).strip()
    if provided_target and strategy in ("affirm_verbstrip", "affirm_raw"):
        # A real target still wins even under an affirm strategy.
        return str(provided_target).strip()
    instr = instruction.strip().rstrip(".")
    if not instr:
        return "Sure, here is"
    if strategy == "affirm_verbstrip":
        parts = instr.split()
        if parts and parts[0].lower() in _LEAD_VERBS:
            parts = parts[1:]
        body = " ".join(parts)
        body = body[:1].lower() + body[1:] if body else body
        return f"Sure, here is {body}"
    # affirm_raw
    lead = instr[:1].lower() + instr[1:]
    return f"Sure, here is {lead}"


def stable_task_id(instruction: str) -> str:
    """Deterministic content-addressed id, stable across runs and row ordering."""
    digest = hashlib.sha256(normalize_text(instruction).encode("utf-8")).hexdigest()
    return f"clearharm_{digest[:12]}"


# ---------------------------------------------------------------------------
# Near-duplicate clustering
# ---------------------------------------------------------------------------

def token_jaccard(a: str, b: str) -> float:
    sa, sb = set(a.split()), set(b.split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def cluster_duplicates(
    instructions: list[str], threshold: float, use_embeddings: bool = False
) -> list[int]:
    """Return a cluster id per instruction. Near-dups share a cluster id.

    Exact-normalized duplicates are always merged (cheap, offline). Semantic
    near-dup merging uses sentence-transformers ONLY when ``use_embeddings=True``
    (F1 fix — embeddings download a ~90 MB model on first use, so it is opt-in and
    never runs implicitly, including under --dry-run). Otherwise falls back to an
    offline token-Jaccard pass.
    """
    n = len(instructions)
    norm = [normalize_text(x) for x in instructions]
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        parent[find(i)] = find(j)

    # Exact-normalized duplicates first (cheap, always run).
    seen: dict[str, int] = {}
    for i, key in enumerate(norm):
        if key in seen:
            union(i, seen[key])
        else:
            seen[key] = i

    embeddings = None
    if use_embeddings:
        try:
            from sentence_transformers import SentenceTransformer  # noqa: WPS433
            import numpy as np  # noqa: WPS433

            print(
                "[near-dup] --embed-dedup set: loading all-MiniLM-L6-v2 "
                "(may download ~90 MB on first use).",
                file=sys.stderr,
            )
            model = SentenceTransformer("all-MiniLM-L6-v2")
            emb = model.encode(
                instructions, normalize_embeddings=True, show_progress_bar=False
            )
            embeddings = np.asarray(emb)
        except Exception as exc:  # noqa: BLE001 (any failure -> fallback)
            print(
                f"[near-dup] embedding backend unavailable ({exc!r}); "
                "using normalized-string / token-Jaccard fallback.",
                file=sys.stderr,
            )

    if embeddings is not None:
        import numpy as np  # noqa: WPS433

        sims = embeddings @ embeddings.T
        for i in range(n):
            for j in range(i + 1, n):
                if sims[i, j] >= threshold:
                    union(i, j)
    else:
        for i in range(n):
            for j in range(i + 1, n):
                if token_jaccard(norm[i], norm[j]) >= threshold:
                    union(i, j)

    roots = {}
    cluster_ids = []
    for i in range(n):
        r = find(i)
        cluster_ids.append(roots.setdefault(r, len(roots)))
    return cluster_ids


# ---------------------------------------------------------------------------
# Category-balanced, dup-aware allocation
# ---------------------------------------------------------------------------

def allocate(records: list[dict], n_opt: int, n_val: int, n_universal: int, seed: int):
    """Assign each record a split, keeping duplicate clusters intact and categories balanced.

    Strategy: represent each duplicate cluster by one representative (smallest task_id).
    Only representatives are allocated to opt/val/universal (so no two near-dups land in
    two different scored splits). All non-representative cluster members, plus every
    representative not chosen for opt/val/universal, go to reserve.
    Within each target split, draw round-robin across categories for balance.
    """
    import random

    rng = random.Random(seed)

    by_cluster: dict[int, list[dict]] = defaultdict(list)
    for rec in records:
        by_cluster[rec["_cluster"]].append(rec)

    representatives = []
    for cluster_id, members in by_cluster.items():
        members.sort(key=lambda r: r["task_id"])
        rep = members[0]
        for m in members[1:]:
            m["split"] = "clearharm_reserve"
            m["notes"] = _append_note(m["notes"], f"dup_of={rep['task_id']}")
        representatives.append(rep)

    # Bucket representatives by category, shuffle deterministically.
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for rep in representatives:
        by_cat[rep["category"]].append(rep)
    for cat in by_cat:
        rng.shuffle(by_cat[cat])

    def draw(n: int) -> list[dict]:
        """Round-robin across categories (largest-remainder balance)."""
        picked: list[dict] = []
        cats = sorted(by_cat.keys())
        while len(picked) < n and any(by_cat[c] for c in cats):
            for c in cats:
                if len(picked) >= n:
                    break
                if by_cat[c]:
                    picked.append(by_cat[c].pop())
        return picked

    opt = draw(n_opt)
    val = draw(n_val)
    universal = draw(n_universal)

    for rec in opt:
        rec["split"] = "clearharm_opt"
    for rec in val:
        rec["split"] = "clearharm_val"
    for rec in universal:
        rec["split"] = "clearharm_universal"
    for cat_pool in by_cat.values():
        for rec in cat_pool:
            rec["split"] = "clearharm_reserve"

    return opt, val, universal


def _append_note(existing: str, note: str) -> str:
    existing = (existing or "").strip()
    return f"{existing}; {note}" if existing else note


# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------

def assert_disjoint(*groups: list[dict]) -> None:
    seen: dict[str, str] = {}
    for group in groups:
        for rec in group:
            tid = rec["task_id"]
            if tid in seen:
                raise AssertionError(
                    f"OVERLAP: task_id {tid} appears in both {seen[tid]} and {rec['split']}"
                )
            seen[tid] = rec["split"]


def summarize(name: str, group: list[dict]) -> dict:
    cats = defaultdict(int)
    for rec in group:
        cats[rec["category"]] += 1
    return {"split": name, "n": len(group), "by_category": dict(sorted(cats.items()))}


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def to_manifest_row(rec: dict) -> dict:
    return {
        "task_id": rec["task_id"],
        "source_dataset": SOURCE_DATASET,
        "split": rec["split"],
        "category": rec["category"],
        "instruction": rec["instruction"],
        "target_prefix": rec["target_prefix"],
        "target_style": TARGET_STYLE,
        "duplicate_group": rec["duplicate_group"],
        "notes": _append_note(rec["notes"], f"target_template={TARGET_TEMPLATE_VERSION}"),
    }


def write_manifest(path: Path, group: list[dict], dry_run: bool) -> None:
    rows = [to_manifest_row(r) for r in sorted(group, key=lambda r: r["task_id"])]
    if dry_run:
        print(f"[dry-run] would write {len(rows)} rows -> {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows -> {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build disjoint category-balanced ClearHarm manifests (Phase B).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Path to a LOCAL, licensed ClearHarm CSV/TSV/parquet file. NOT downloaded here.",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/manifests"),
        help="Directory to write the manifest CSVs into.",
    )
    p.add_argument("--n-opt", type=int, default=15, help="Rows in clearharm_opt15.csv")
    p.add_argument("--n-val", type=int, default=15, help="Rows in clearharm_val15.csv")
    p.add_argument(
        "--n-universal", type=int, default=100, help="Rows in clearharm_universal100.csv"
    )
    p.add_argument("--seed", type=int, default=0, help="Deterministic allocation seed.")
    p.add_argument(
        "--dup-threshold",
        type=float,
        default=NEAR_DUP_THRESHOLD,
        help="Near-duplicate similarity threshold (cosine or token-Jaccard).",
    )
    p.add_argument(
        "--embed-dedup",
        action="store_true",
        help="Use sentence-transformers for semantic near-dup detection (may DOWNLOAD "
        "~90 MB on first use). Off by default: only offline exact + token-Jaccard.",
    )
    p.add_argument(
        "--target-strategy",
        choices=("source", "affirm_verbstrip", "affirm_raw"),
        default="source",
        help="How to fill target_prefix: 'source' uses the dataset target and ERRORS if "
        "absent; 'affirm_verbstrip' synthesizes a grammatical 'Sure, here is ...'; "
        "'affirm_raw' is the legacy (possibly ungrammatical) synthesis.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute + assert allocation and print the summary, but write nothing.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.input.exists():
        raise SystemExit(
            f"--input not found: {args.input}\n"
            "ClearHarm is NOT vendored and this script does not download it. Provide a "
            "local, licensed copy only after the licensing decision is confirmed "
            "(see docs/CLEARHARM_STATUS.md)."
        )

    raw = load_rows(args.input)
    if not raw:
        raise SystemExit("Input file has no rows.")

    sample = raw[0]
    instr_col = pick_column(sample, INSTRUCTION_COLS)
    if instr_col is None:
        raise SystemExit(
            f"Could not find an instruction column among {INSTRUCTION_COLS} "
            f"in columns {list(sample.keys())}."
        )
    cat_col = pick_column(sample, CATEGORY_COLS)
    target_col = pick_column(sample, TARGET_COLS)

    # Build normalized records (dedup exact task_ids: identical instruction -> one row).
    records: dict[str, dict] = {}
    n_id_collisions = 0
    for row in raw:
        instruction = str(row.get(instr_col, "") or "").strip()
        if not instruction:
            continue
        tid = stable_task_id(instruction)
        if tid in records:
            # F3: task_id normalizes away case/punctuation, so two textually-distinct
            # instructions differing only in case/punctuation collapse here. Count it
            # so the drop is never silent.
            if records[tid]["instruction"] != instruction:
                n_id_collisions += 1
            continue
        category, cat_note = normalize_category(row.get(cat_col) if cat_col else None)
        provided_target = row.get(target_col) if target_col else None
        records[tid] = {
            "task_id": tid,
            "instruction": instruction,
            "category": category,
            "target_prefix": build_target_prefix(
                instruction, provided_target, args.target_strategy
            ),
            "duplicate_group": tid,  # overwritten with cluster representative below
            "notes": cat_note,
            "split": "clearharm_reserve",
        }
    if n_id_collisions:
        print(
            f"[dedup] WARNING: dropped {n_id_collisions} row(s) that differ from a kept "
            "instruction only by case/punctuation (task_id normalizes those away).",
            file=sys.stderr,
        )

    rec_list = list(records.values())
    instructions = [r["instruction"] for r in rec_list]
    clusters = cluster_duplicates(
        instructions, args.dup_threshold, use_embeddings=args.embed_dedup
    )

    # Assign cluster id + a stable duplicate_group (representative task_id per cluster).
    cluster_members: dict[int, list[dict]] = defaultdict(list)
    for rec, cid in zip(rec_list, clusters):
        rec["_cluster"] = cid
        cluster_members[cid].append(rec)
    for members in cluster_members.values():
        rep_id = min(m["task_id"] for m in members)
        for m in members:
            m["duplicate_group"] = rep_id

    needed = args.n_opt + args.n_val + args.n_universal
    n_clusters = len(cluster_members)
    if n_clusters < needed:
        raise SystemExit(
            f"Not enough unique (deduplicated) instructions: have {n_clusters} clusters, "
            f"need {needed} for {args.n_opt}/{args.n_val}/{args.n_universal}. "
            "Adjust --n-* explicitly and document the change in docs/CLEARHARM_STATUS.md."
        )

    opt, val, universal = allocate(
        rec_list, args.n_opt, args.n_val, args.n_universal, args.seed
    )
    reserve = [r for r in rec_list if r["split"] == "clearharm_reserve"]

    # Overlap assertions BEFORE writing anything.
    assert_disjoint(opt, val, universal, reserve)
    assert len(opt) == args.n_opt, f"opt size {len(opt)} != {args.n_opt}"
    assert len(val) == args.n_val, f"val size {len(val)} != {args.n_val}"
    assert len(universal) == args.n_universal, (
        f"universal size {len(universal)} != {args.n_universal}"
    )
    total = len(opt) + len(val) + len(universal) + len(reserve)
    assert total == len(rec_list), f"row accounting mismatch: {total} != {len(rec_list)}"

    summary = {
        "input": str(args.input),
        "instruction_col": instr_col,
        "category_col": cat_col,
        "target_col": target_col,
        "n_raw_rows": len(raw),
        "n_unique_instructions": len(rec_list),
        "n_dup_clusters": n_clusters,
        "target_template_version": TARGET_TEMPLATE_VERSION,
        # F5: label each split by the value actually written to the `split` column
        # AND the output filename, so grep-by-either finds it.
        "splits": [
            {"file": "clearharm_opt15.csv", **summarize("clearharm_opt", opt)},
            {"file": "clearharm_val15.csv", **summarize("clearharm_val", val)},
            {"file": "clearharm_universal100.csv", **summarize("clearharm_universal", universal)},
            {"file": "clearharm_reserve.csv", **summarize("clearharm_reserve", reserve)},
        ],
    }
    print(json.dumps(summary, indent=2))

    write_manifest(args.out_dir / "clearharm_opt15.csv", opt, args.dry_run)
    write_manifest(args.out_dir / "clearharm_val15.csv", val, args.dry_run)
    write_manifest(args.out_dir / "clearharm_universal100.csv", universal, args.dry_run)
    write_manifest(args.out_dir / "clearharm_reserve.csv", reserve, args.dry_run)

    if args.dry_run:
        print("[dry-run] no files written; assertions passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
