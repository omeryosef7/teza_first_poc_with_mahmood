#!/usr/bin/env python3
"""Phase 1 (RESEARCH_PLAN_DISTILLING_JAILBREAKS.md sec 5): build the disjoint
25 / 495 dataset split, reusing existing artifacts (no data duplication):

  - Behaviors + targets: outputs/stage_gcg_full/advbench_cot_full520_manifest.jsonl
  - Category labels:      scripts/gcg_advbench_llm_taxonomy.categorize()
  - Canonical dev-25:     the SAME 25 evenly-spaced AdvBench rows historically used
                          for GCG development (scripts/detector_extended_audit.py
                          DEV_25_ADVBENCH_ROWS). We MUST reuse this exact set so the
                          held-out 495 is genuinely never-seen (plan sec 5.1 hard
                          criterion). Plan sec 5.2 asks for category coverage; we
                          verify/report it rather than re-drawing (which would leak).

Emits (plan sec 5.4 deliverables):
  data/manifests/dev_25.csv
  data/manifests/dev_train_20.csv
  data/manifests/dev_val_5.csv
  data/manifests/heldout_495.csv
  data/manifests/split_audit.md

Deterministic: same inputs -> same output. No GPU, no network.
Run: <env>/bin/python scripts/build_dataset_split.py
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from gcg_advbench_llm_taxonomy import categorize  # reuse existing taxonomy

MANIFEST = ROOT / "outputs" / "stage_gcg_full" / "advbench_cot_full520_manifest.jsonl"
OUT_DIR = ROOT / "data" / "manifests"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Canonical historical dev set (must match detector_extended_audit.py).
DEV_25_ADVBENCH_ROWS = [1, 21, 42, 63, 84, 105, 125, 146, 167, 188, 209, 229, 250,
                        271, 292, 313, 333, 354, 375, 396, 417, 437, 458, 479, 500]
DEV_25_TASK_IDS = {f"advbench_full_{r:04d}" for r in DEV_25_ADVBENCH_ROWS}

# 5 validation behaviors chosen for category spread (disjoint from the 20 train).
# Picked deterministically below by taking one behavior from each of the 5 most
# distinct categories present in the dev-25; recorded explicitly for reproducibility.
CSV_FIELDS = ["task_id", "source_dataset", "split", "category", "instruction",
              "target_prefix", "target_style", "duplicate_group", "notes"]


def load_manifest():
    rows = []
    with open(MANIFEST) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def norm_text(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def tokset(s: str):
    return set(norm_text(s).split())


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def assign_duplicate_groups(records, thr=0.85):
    """Union-find clustering on token Jaccard >= thr (lexical near-dup proxy).
    Embedding-based near-dup is a documented follow-up (needs a model)."""
    n = len(records)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    toks = [tokset(r["instruction"]) for r in records]
    for i in range(n):
        for j in range(i + 1, n):
            if jaccard(toks[i], toks[j]) >= thr:
                union(i, j)
    # canonical group id = smallest task_id in cluster
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    gid_of = {}
    for members in groups.values():
        gid = min(records[m]["task_id"] for m in members)
        for m in members:
            gid_of[m] = gid
    return gid_of, groups


def main():
    manifest = load_manifest()
    # Build unified records
    records = []
    for r in manifest:
        tid = r["task_id"]
        records.append({
            "task_id": tid,
            "source_dataset": "advbench",
            "split": "dev" if tid in DEV_25_TASK_IDS else "heldout",
            "category": categorize(r["instruction"]),
            "instruction": r["instruction"],
            "target_prefix": r.get("original_safe_target_prefix", ""),
            "target_style": "affirm_raw",
            "duplicate_group": "",
            "notes": "",
        })

    gid_of, groups = assign_duplicate_groups(records)
    for i, rec in enumerate(records):
        rec["duplicate_group"] = gid_of[i]

    dev = [r for r in records if r["split"] == "dev"]
    heldout = [r for r in records if r["split"] == "heldout"]
    assert len(dev) == 25, f"expected 25 dev, got {len(dev)}"
    assert len(heldout) == 495, f"expected 495 heldout, got {len(heldout)}"

    # dev_train_20 / dev_val_5 split: pick 5 validation behaviors, each from a
    # distinct category, deterministically (first task_id per category, take the
    # 5 categories with most dev members, then one each).
    dev_sorted = sorted(dev, key=lambda r: r["task_id"])
    by_cat = {}
    for r in dev_sorted:
        by_cat.setdefault(r["category"], []).append(r)
    cats_ranked = sorted(by_cat, key=lambda c: (-len(by_cat[c]), c))
    val_ids = []
    for c in cats_ranked:
        if len(val_ids) >= 5:
            break
        val_ids.append(by_cat[c][0]["task_id"])
    val_ids = set(val_ids)
    for r in dev_sorted:
        r["split"] = "dev_val" if r["task_id"] in val_ids else "dev_train"

    dev_train = [r for r in dev_sorted if r["split"] == "dev_train"]
    dev_val = [r for r in dev_sorted if r["split"] == "dev_val"]
    assert len(dev_train) == 20 and len(dev_val) == 5

    # --- write CSVs ---
    def write_csv(path, rows, split_label):
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            w.writeheader()
            for r in rows:
                out = dict(r)
                out["split"] = split_label if split_label else r["split"]
                w.writerow({k: out[k] for k in CSV_FIELDS})

    write_csv(OUT_DIR / "dev_25.csv", dev_sorted, None)
    write_csv(OUT_DIR / "dev_train_20.csv", dev_train, "dev_train")
    write_csv(OUT_DIR / "dev_val_5.csv", dev_val, "dev_val")
    write_csv(OUT_DIR / "heldout_495.csv",
              sorted(heldout, key=lambda r: r["task_id"]), "heldout")

    # --- overlap checks (plan sec 5.3) ---
    dev_norm = {norm_text(r["instruction"]): r["task_id"] for r in dev_sorted}
    held_norm = {norm_text(r["instruction"]): r["task_id"] for r in heldout}
    exact_overlap = sorted(set(dev_norm) & set(held_norm))

    dev_targets = {norm_text(r["target_prefix"]): r["task_id"] for r in dev_sorted}
    held_targets = {norm_text(r["target_prefix"]): r["task_id"] for r in heldout}
    target_overlap = sorted(set(dev_targets) & set(held_targets))

    # cross-split near-dup (same duplicate_group spanning dev & heldout)
    cross_group = []
    split_of = {r["task_id"]: ("dev" if r["task_id"] in DEV_25_TASK_IDS else "heldout")
                for r in records}
    for members in groups.values():
        tids = [records[m]["task_id"] for m in members]
        sides = {split_of[t] for t in tids}
        if len(tids) > 1 and "dev" in sides and "heldout" in sides:
            cross_group.append(sorted(tids))

    # dev category distribution
    dev_cat_counts = {}
    for r in dev_sorted:
        dev_cat_counts[r["category"]] = dev_cat_counts.get(r["category"], 0) + 1

    audit = []
    audit.append("# Dataset Split Audit (Phase 1)\n")
    audit.append("Generated by `scripts/build_dataset_split.py` (deterministic, no GPU).\n")
    audit.append("Source manifest: `outputs/stage_gcg_full/advbench_cot_full520_manifest.jsonl`\n")
    audit.append("Category labels: `scripts/gcg_advbench_llm_taxonomy.categorize()`\n")
    audit.append("\n## Sizes\n")
    audit.append(f"- dev_25: {len(dev_sorted)}\n")
    audit.append(f"- dev_train_20: {len(dev_train)}\n")
    audit.append(f"- dev_val_5: {len(dev_val)} (task_ids: {sorted(val_ids)})\n")
    audit.append(f"- heldout_495: {len(heldout)}\n")
    audit.append("\n## Disjointness (plan sec 5.1 hard criterion)\n")
    audit.append(f"- Exact-text dev/heldout overlap: {len(exact_overlap)} {exact_overlap}\n")
    audit.append(f"- Target-prefix dev/heldout overlap: {len(target_overlap)} {target_overlap}\n")
    audit.append(f"- Cross-split near-dup clusters (token Jaccard>=0.85): {len(cross_group)}\n")
    for c in cross_group:
        audit.append(f"    - {c}\n")
    audit.append("\n## Dev-25 category coverage (plan sec 5.2)\n")
    for c, n in sorted(dev_cat_counts.items(), key=lambda kv: -kv[1]):
        audit.append(f"- {c}: {n}\n")
    audit.append("\n## Known limitations / follow-ups\n")
    audit.append("- Near-dup check is lexical (token Jaccard); embedding-based "
                 "semantic near-dup is a documented follow-up (needs a sentence model).\n")
    audit.append("- external_transfer.csv is NOT built here; external benchmark "
                 "selection is deferred to Phase 15 (needs licensing/download decision).\n")
    audit.append("- Dev-25 is the historical evenly-spaced set (reused to preserve "
                 "held-out purity), not a freshly stratified draw.\n")
    (OUT_DIR / "split_audit.md").write_text("".join(audit))

    print(f"[ok] wrote manifests to {OUT_DIR}")
    print(f"[ok] dev_train={len(dev_train)} dev_val={len(dev_val)} heldout={len(heldout)}")
    print(f"[check] exact_overlap={len(exact_overlap)} target_overlap={len(target_overlap)} "
          f"cross_dup_clusters={len(cross_group)}")
    if cross_group:
        print("[WARN] near-duplicate behaviors span dev/heldout; see split_audit.md")


if __name__ == "__main__":
    main()
