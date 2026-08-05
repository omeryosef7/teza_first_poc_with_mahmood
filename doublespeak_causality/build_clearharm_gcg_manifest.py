"""
build_clearharm_gcg_manifest.py — P9.0 item 4: the Llama + ClearHarm GCG manifest.

WHY THIS EXISTS
    Gate 7 (plan §P9) cannot run because there is no DATA path for it: every existing GCG
    config is Qwen3-14B / Gemma / DeepSeek, and the Doublespeak ClearHarm split
    (`data/splits/clearharm_doublespeak_v1.json`, cohort=='clearharm', 44 train / 42 test)
    carries the six prompt conditions but **no affirmative-target field**, which GCG's
    `task_loss` requires. The affirmative targets exist in `data/manifests/clearharm_*.csv`
    (`instruction`, `target_prefix`), but the two id schemes are disjoint
    (`example_id` vs `task_id`: 0/86 overlap). The only sound key is the **instruction text**.

WHAT IT DOES
    1. Reads the split, keeps `--cohort` (default clearharm) and uses the split's OWN
       `split` field verbatim ("train" / "test") — no re-hashing, no re-splitting.
    2. Reads every `clearharm_*.csv` target manifest and joins
       split.original_request  <->  csv.instruction
       exact first, then an optional normalized tier (casefold + whitespace collapse +
       trailing-period strip). A normalized key whose CSV rows disagree on `target_prefix`
       is treated as UNMATCHED — a target is never invented, guessed, or defaulted.
    3. Emits one SurrogateTask-schema JSONL per prompt condition (default: direct,
       doublespeak) — the schema consumed by `poc_stage_gcg_early/run_optimization.py`
       (`config.SurrogateTask.from_dict` silently drops the extra provenance keys).
    4. Writes `<out>/JOIN_REPORT.json` + a `.sha256` beside each manifest, and RUNMETA /
       DONE via ds_common.

    If ANY item fails to join, the manifests are NOT written and the exit code is 2
    (override with --allow-unjoined, which then simply drops the unjoined items and
    records their ids). The join report lists unjoined items **by id only**.

SAFETY
    Instruction / prompt / target text is copied file->file and is NEVER printed. Every
    stdout line from this script is a count, an id, a path or a hash.

USAGE (CPU, login node; this builds a manifest and launches nothing)
    python doublespeak_causality/build_clearharm_gcg_manifest.py \
        --out doublespeak_causality/data/gcg/clearharm_llama
    python doublespeak_causality/build_clearharm_gcg_manifest.py --report-only
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, ".."))

DEFAULT_SPLIT = os.path.join(HERE, "data", "splits", "clearharm_doublespeak_v1.json")
DEFAULT_TARGET_GLOB = os.path.join(REPO, "data", "manifests", "clearharm_*.csv")
DEFAULT_OUT = os.path.join(HERE, "data", "gcg", "clearharm_llama")

# split field -> manifest condition name. The instruction written into the manifest is the
# prompt for that condition; the affirmative target is the SAME joined target_prefix in every
# condition (it anchors task_loss on the harmful completion, which is condition-independent).
CONDITION_FIELDS = {
    "direct": "direct_prompt",
    "doublespeak": "doublespeak_prompt",
    "neutral": "neutral_prompt",
    "benign": "benign_prompt",
    "shuffled": "shuffled_prompt",
    "unrelated": "unrelated_prompt",
}

# Provenance keys carried alongside the SurrogateTask fields. SurrogateTask.from_dict keeps
# only the dataclass fields, so these are free metadata for the eval / audit side.
_EXTRA_KEYS = ("cohort", "harm_category", "intent_cluster", "codeword", "single_token_primary",
               "n_codeword_occurrences_templated", "dataset_revision")


def _norm(s: str) -> str:
    """Normalization tier 2 key: casefold, collapse whitespace, drop a trailing period."""
    return " ".join(s.split()).casefold().strip().rstrip(".")


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_split(path: str, cohort: str) -> list:
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    ex = [e for e in doc.get("examples", []) if e.get("cohort") == cohort]
    return doc.get("_meta", {}), ex


def load_targets(pattern: str) -> tuple:
    """Return (exact_index, norm_index, files, n_rows).

    Each index maps key -> list of {task_id, target_prefix, target_style, source_file}.
    """
    files = sorted(glob.glob(pattern))
    if not files:
        raise SystemExit(f"[build_clearharm_gcg_manifest] no target CSVs matched: {pattern}")
    exact, normed, n_rows = {}, {}, 0
    for fp in files:
        with open(fp, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                for col in ("instruction", "target_prefix", "task_id"):
                    if col not in row:
                        raise SystemExit(f"[build_clearharm_gcg_manifest] {fp} lacks column '{col}'")
                rec = {"task_id": row["task_id"], "target_prefix": row["target_prefix"],
                       "target_style": row.get("target_style"),
                       "source_file": os.path.basename(fp)}
                exact.setdefault(row["instruction"], []).append(rec)
                normed.setdefault(_norm(row["instruction"]), []).append(rec)
                n_rows += 1
    return exact, normed, [os.path.basename(f) for f in files], n_rows


def _pick(cands: list) -> tuple:
    """(record, reason). Ambiguous = the candidate rows disagree on target_prefix -> no target."""
    prefixes = {c["target_prefix"] for c in cands}
    if len(prefixes) != 1:
        return None, f"ambiguous:{len(prefixes)}_distinct_target_prefix"
    if not cands[0]["target_prefix"].strip():
        return None, "empty_target_prefix"
    return cands[0], "ok"


def join(examples: list, exact: dict, normed: dict, use_norm_fallback: bool) -> tuple:
    """Join each example to a target. Returns (matched, unmatched, tier_counts)."""
    matched, unmatched, tiers = [], [], {"exact": 0, "normalized": 0}
    for e in examples:
        instr = e.get("original_request")
        rec, tier, reason = None, None, "no_key_in_target_csvs"
        if instr is None:
            reason = "example_has_no_original_request"
        else:
            if instr in exact:
                rec, reason = _pick(exact[instr])
                tier = "exact"
            elif use_norm_fallback and _norm(instr) in normed:
                rec, reason = _pick(normed[_norm(instr)])
                tier = "normalized"
        if rec is None:
            unmatched.append({"example_id": e.get("example_id"), "split": e.get("split"),
                              "reason": reason})
        else:
            tiers[tier] += 1
            matched.append((e, rec, tier))
    return matched, unmatched, tiers


def build_rows(matched: list, condition: str, model_family: str, enable_thinking: bool,
               seed: int, control_suffix: str) -> list:
    field = CONDITION_FIELDS[condition]
    rows = []
    for e, rec, tier in matched:
        instruction = e.get(field)
        if not instruction:
            raise SystemExit(f"[build_clearharm_gcg_manifest] {e.get('example_id')} lacks '{field}'")
        row = {
            # --- config.SurrogateTask schema ---
            "task_id": e["example_id"],
            "instruction": instruction,
            "safe_target_prefix": rec["target_prefix"],
            "early_prefix": None,
            "neutral_control_suffix": control_suffix,
            "split": e["split"],                 # verbatim from the split file: train | test
            "seed": seed,
            "model": model_family,
            "enable_thinking": bool(enable_thinking),
            # --- provenance (dropped by SurrogateTask.from_dict, kept for eval/audit) ---
            "prompt_condition": condition,
            "prompt_field": field,
            "target_task_id": rec["task_id"],
            "target_source_file": rec["source_file"],
            "target_style": rec["target_style"],
            "join_key": "instruction_text",
            "join_tier": tier,
        }
        for k in _EXTRA_KEYS:
            if k in e:
                row[k] = e[k]
        rows.append(row)
    rows.sort(key=lambda r: r["task_id"])
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the Llama+ClearHarm GCG manifest (P9.0 item 4)")
    ap.add_argument("--split-file", default=DEFAULT_SPLIT)
    ap.add_argument("--targets-glob", default=DEFAULT_TARGET_GLOB)
    ap.add_argument("--cohort", default="clearharm")
    ap.add_argument("--conditions", default="direct,doublespeak",
                    help="comma-separated; any of " + ",".join(CONDITION_FIELDS))
    ap.add_argument("--out", default=DEFAULT_OUT, help="output DIRECTORY")
    ap.add_argument("--model-family", default="llama",
                    choices=["qwen3", "gemma4", "deepseek_r1", "llama"])
    ap.add_argument("--enable-thinking", action="store_true",
                    help="Llama has no thinking channel; leave off for the P9 arms.")
    ap.add_argument("--seed", type=int, default=42, help="per-task seed field; arm seeds live in the matrix")
    ap.add_argument("--control-suffix", default=" ", help="matched no-op control suffix")
    ap.add_argument("--no-normalized-fallback", action="store_true",
                    help="exact instruction match only (no casefold/whitespace tier)")
    ap.add_argument("--allow-unjoined", action="store_true",
                    help="write manifests even if some items have no target (they are DROPPED)")
    ap.add_argument("--report-only", action="store_true", help="compute the join, write nothing")
    args = ap.parse_args(argv)

    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    bad = [c for c in conditions if c not in CONDITION_FIELDS]
    if bad:
        raise SystemExit(f"[build_clearharm_gcg_manifest] unknown condition(s): {bad}")

    meta, examples = load_split(args.split_file, args.cohort)
    exact, normed, target_files, n_target_rows = load_targets(args.targets_glob)
    matched, unmatched, tiers = join(examples, exact, normed, not args.no_normalized_fallback)

    n_tot = len(examples)
    n_ok = len(matched)
    rate = (n_ok / n_tot) if n_tot else 0.0
    id_overlap = len({e["example_id"] for e in examples} &
                     {r["task_id"] for recs in exact.values() for r in recs})

    split_counts = {}
    for e, _, _ in matched:
        split_counts[e["split"]] = split_counts.get(e["split"], 0) + 1

    report = {
        "split_file": os.path.abspath(args.split_file),
        "split_meta": meta,
        "cohort": args.cohort,
        "target_files": target_files,
        "n_target_rows": n_target_rows,
        "n_target_unique_instructions": len(exact),
        "join_key": "instruction_text (split.original_request <-> csv.instruction)",
        "id_scheme_overlap_example_id_vs_task_id": id_overlap,
        "n_examples": n_tot,
        "n_matched": n_ok,
        "match_rate": round(rate, 6),
        "match_tiers": tiers,
        "n_unmatched": len(unmatched),
        "unmatched": unmatched,          # ids + reason only; never text
        "matched_by_split": split_counts,
        "conditions": conditions,
        "model_family": args.model_family,
        "enable_thinking": bool(args.enable_thinking),
        "seed_field": args.seed,
    }

    print(f"[join] cohort={args.cohort} examples={n_tot} target_csv_rows={n_target_rows} "
          f"unique_instructions={len(exact)}")
    print(f"[join] id-scheme overlap (example_id vs task_id) = {id_overlap}/{n_tot}")
    print(f"[join] MATCH RATE = {n_ok}/{n_tot} = {rate:.4f}  "
          f"(exact={tiers['exact']}, normalized={tiers['normalized']}, unmatched={len(unmatched)})")
    print(f"[join] matched by split: {split_counts}")
    if unmatched:
        print(f"[join] UNJOINED ({len(unmatched)}) — no target invented: "
              + ", ".join(f"{u['example_id']}({u['reason']})" for u in unmatched))

    if args.report_only:
        print("[out] --report-only: no files written")
        return 0 if not unmatched else 2

    if unmatched and not args.allow_unjoined:
        print("[out] REFUSING to write: unjoined items present and --allow-unjoined not given.")
        return 2

    os.makedirs(args.out, exist_ok=True)

    runmeta = None
    try:
        sys.path.insert(0, HERE)
        import ds_common as dc
        runmeta = dc.write_runmeta(args.out, args, extra={"phase": "P9.0-item4",
                                                          "join_key": "instruction_text"})
    except Exception as exc:                                  # provenance must never kill a build
        print(f"[runmeta] ds_common unavailable ({exc!r}); continuing without RUNMETA")

    written, total_rows = [], 0
    for cond in conditions:
        rows = build_rows(matched, cond, args.model_family, args.enable_thinking,
                          args.seed, args.control_suffix)
        path = os.path.join(args.out, f"clearharm_{args.model_family}_{cond}.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        digest = _sha256_file(path)
        with open(path + ".sha256", "w", encoding="utf-8") as f:
            f.write(digest + "  " + os.path.basename(path) + "\n")
        per_split = {}
        for r in rows:
            per_split[r["split"]] = per_split.get(r["split"], 0) + 1
        written.append({"condition": cond, "path": os.path.abspath(path), "n_rows": len(rows),
                        "by_split": per_split, "sha256": digest})
        total_rows += len(rows)
        print(f"[out] {os.path.basename(path)}  rows={len(rows)}  by_split={per_split}  "
              f"sha256={digest[:16]}...")

    report["manifests"] = written
    rp = os.path.join(args.out, "JOIN_REPORT.json")
    with open(rp, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[out] {rp}")

    if runmeta is not None:
        try:
            import ds_common as dc
            dc.write_done(args.out, rows_written=total_rows,
                          extra={"n_manifests": len(written), "match_rate": rate})
        except Exception as exc:
            print(f"[done] write_done failed ({exc!r})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
