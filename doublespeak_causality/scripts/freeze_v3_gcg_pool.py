#!/usr/bin/env python3
"""Freeze a cluster-diverse ~40-item TRAIN optimization pool from the v3 leakage-0
ClearHarm GCG manifest, for the Gate-7 attack-objective matrix (NEXT sprint 2026-08-09).

Rationale (docs/NEXT_SPRINT_EXECUTION_LOG.md, 2026-08-09 decision):
- v1 has 90% train/test leakage -> cannot support a transfer claim.
- v3 is leakage-0 but its full 74-item clearharm train would make each universal-GCG run
  ~2x the first-cut compute (compute = steps*batch*n_train). We freeze a cluster-diverse
  pool of POOL_N items so optimization stays near first-cut cost while the HELD-OUT eval
  uses the FULL leakage-0 v3 test (37 items, all >=20 requirement).
- Selection is TRAIN-ONLY and deterministic; frozen BEFORE any layer/lambda/seed choice.

Writes (into --out dir):
  clearharm_llama_doublespeak_trainpool{N}.jsonl   (optimization pool, doublespeak condition)
  clearharm_llama_direct_trainpool{N}.jsonl        (same task_ids, direct condition)
  POOL_MANIFEST.json                               (sha256s, coverage, seed, git commit)

NO harmful text is printed. Deterministic: no RNG that varies across runs.
"""
import argparse, hashlib, json, os, subprocess, collections

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_rows(path, split):
    rows = []
    with open(path) as f:
        for line in f:
            r = json.loads(line)
            if r.get("split") == split:
                rows.append(r)
    return rows


def pick_cluster_diverse(rows, n):
    """Deterministic max-cluster-diversity pick of n rows.
    Group by intent_cluster; round-robin one row per cluster (rows sorted by task_id
    within cluster; clusters ordered by first task_id) until n selected."""
    by_cluster = collections.OrderedDict()
    for r in sorted(rows, key=lambda x: x["task_id"]):
        by_cluster.setdefault(r["intent_cluster"], []).append(r)
    cluster_order = list(by_cluster.keys())  # already first-seen == task_id sorted
    picked, ri = [], 0
    while len(picked) < n and any(by_cluster.values()):
        cl = cluster_order[ri % len(cluster_order)]
        if by_cluster[cl]:
            picked.append(by_cluster[cl].pop(0))
        ri += 1
        if ri > 100000:
            break
    return sorted(picked, key=lambda x: x["task_id"])


def write_jsonl(path, rows):
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gcg-dir", default=os.path.join(HERE, "data/gcg/clearharm_llama_v3"))
    ap.add_argument("--out", default=os.path.join(HERE, "data/gcg/clearharm_llama_v3"))
    ap.add_argument("--pool-n", type=int, default=40)
    args = ap.parse_args()

    ds_path = os.path.join(args.gcg_dir, "clearharm_llama_doublespeak.jsonl")
    dir_path = os.path.join(args.gcg_dir, "clearharm_llama_direct.jsonl")

    ds_train = load_rows(ds_path, "train")
    dir_train = {r["task_id"]: r for r in load_rows(dir_path, "train")}

    pool = pick_cluster_diverse(ds_train, args.pool_n)
    pool_ids = [r["task_id"] for r in pool]
    dir_pool = [dir_train[t] for t in pool_ids if t in dir_train]
    assert len(dir_pool) == len(pool), "direct manifest missing some pool task_ids"

    ds_out = os.path.join(args.out, f"clearharm_llama_doublespeak_trainpool{args.pool_n}.jsonl")
    dir_out = os.path.join(args.out, f"clearharm_llama_direct_trainpool{args.pool_n}.jsonl")
    write_jsonl(ds_out, pool)
    write_jsonl(dir_out, dir_pool)

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=HERE).decode().strip()
    except Exception:
        commit = "unknown"

    manifest = {
        "purpose": "Frozen train-only optimization pool for Gate-7 v3 attack-objective matrix",
        "source_manifest": os.path.relpath(ds_path, HERE),
        "source_sha256": sha256(ds_path),
        "pool_n_requested": args.pool_n,
        "pool_n_actual": len(pool),
        "selection": "deterministic cluster-diverse round-robin, train split only, sorted by task_id",
        "git_commit": commit,
        "coverage": {
            "n_items": len(pool),
            "distinct_intent_clusters": len(set(r["intent_cluster"] for r in pool)),
            "distinct_codewords": len(set(r["codeword"] for r in pool)),
            "distinct_harm_categories": len(set(r.get("harm_category") for r in pool)),
            "train_full_n": len(ds_train),
            "train_full_clusters": len(set(r["intent_cluster"] for r in ds_train)),
        },
        "files": {
            "doublespeak_pool": {"path": os.path.relpath(ds_out, HERE), "sha256": sha256(ds_out), "n": len(pool)},
            "direct_pool": {"path": os.path.relpath(dir_out, HERE), "sha256": sha256(dir_out), "n": len(dir_pool)},
        },
        "task_ids": pool_ids,
    }
    with open(os.path.join(args.out, "POOL_MANIFEST.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    # scalar-only report (no harmful text)
    print(f"[pool] n={len(pool)} clusters={manifest['coverage']['distinct_intent_clusters']} "
          f"codewords={manifest['coverage']['distinct_codewords']} "
          f"harm_cats={manifest['coverage']['distinct_harm_categories']}")
    print(f"[pool] from full train n={len(ds_train)} clusters={manifest['coverage']['train_full_clusters']}")
    print(f"[out] {os.path.relpath(ds_out, HERE)} sha={manifest['files']['doublespeak_pool']['sha256'][:16]}")
    print(f"[out] {os.path.relpath(dir_out, HERE)} sha={manifest['files']['direct_pool']['sha256'][:16]}")


if __name__ == "__main__":
    main()
