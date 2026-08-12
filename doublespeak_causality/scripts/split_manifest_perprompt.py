#!/usr/bin/env python3
"""Split a v3 manifest into ONE 1-row manifest per prompt, for plan §7.5 per-prompt GCG.

§7.1 reuse: this writes DATA only. The optimizer, objective and eval code are untouched --
per-prompt optimization is expressible today by passing a 1-row manifest to the existing
`run_optimization` (verified: gcg_optimizer.py:617-619 derives train_tasks from manifest content;
no CLI/config field caps the task count).

Guards two SILENT failure modes found in audit (both exit 0 while producing garbage):

  1. EMPTY RUN. The optimizer keeps rows with split=="train", falling back to all rows only if
     that list is empty (gcg_optimizer.py:617-619). A row whose split is "test"/"dev" therefore
     needs `--split all` at the call site, or the train list is empty, grad_accum stays None, the
     loop breaks at step 0 (gcg_optimizer.py:884-885) and an EMPTY ITERATION_LOG is written with
     no error. We keep the TRUE split label (never rewrite it -- that would corrupt provenance)
     and emit the required `--split` value into the joblist so the caller cannot get it wrong.

  2. CROSS-PROMPT RESUME. config_hash() deliberately excludes run_id, output_dir AND
     manifest_path (config.py:192-224). Two prompts sharing an output_dir would load each other's
     checkpoint.pt with NO hash mismatch and silently optimize the wrong prompt. We assert every
     output_dir is unique.

Safety: prints COUNTS and task_ids only -- never instruction/target text (§3.14).
"""
from __future__ import annotations
import argparse, json, os
from pathlib import Path

# SurrogateTask.from_dict has no defaults -- every key must be present on every row (config.py:43-63)
REQUIRED = ["task_id", "instruction", "safe_target_prefix", "early_prefix",
            "neutral_control_suffix", "split", "seed", "model", "enable_thinking"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", required=True, help="which split to extract (train/dev/test)")
    ap.add_argument("--out-dir", required=True, help="dir for the 1-row manifests")
    ap.add_argument("--joblist", required=True, help="output joblist .jsonl")
    ap.add_argument("--run-root", required=True, help="root under which each prompt gets its own run dir")
    ap.add_argument("--arm", required=True, help="arm label, becomes part of run_id")
    ap.add_argument("--seed", type=int, required=True)
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.manifest) if l.strip()]
    sel = [r for r in rows if r.get("split") == args.split]
    if not sel:
        raise SystemExit(f"no rows with split=={args.split!r} in {args.manifest} "
                         f"(available: {sorted({r.get('split') for r in rows})})")

    missing = {k for r in sel for k in REQUIRED if k not in r}
    if missing:
        raise SystemExit(f"rows missing required SurrogateTask keys: {sorted(missing)}")

    ids = [r["task_id"] for r in sel]
    if len(set(ids)) != len(ids):
        raise SystemExit("duplicate task_id in selected rows -- would collide on disk")

    # The optimizer only auto-selects split=="train"; anything else relies on the empty-list
    # fallback and therefore REQUIRES --split all at the call site.
    split_flag = "train" if args.split == "train" else "all"

    out_dir, run_root = Path(args.out_dir), Path(args.run_root)
    out_dir.mkdir(parents=True, exist_ok=True)
    seen_dirs: set[str] = set()
    jobs = []
    for r in sel:
        tid = r["task_id"]
        mpath = out_dir / f"{tid}.jsonl"
        # Atomic write: several sharded jobs regenerate this same path concurrently. A plain
        # write_text can be read torn by a sibling job mid-write -- a silent data corruption.
        tmp = mpath.with_suffix(f".tmp{os.getpid()}")
        tmp.write_text(json.dumps(r) + "\n", encoding="utf-8")
        os.replace(tmp, mpath)
        odir = run_root / f"{args.arm}_pp_{tid}_seed{args.seed}"
        if str(odir) in seen_dirs:
            raise SystemExit(f"duplicate output_dir {odir} -- cross-prompt resume hazard")
        seen_dirs.add(str(odir))
        jobs.append({"task_id": tid, "manifest": str(mpath), "output_dir": str(odir),
                     "run_id": odir.name, "seed": args.seed, "split_flag": split_flag,
                     "arm": args.arm, "source_split": r["split"]})

    with open(args.joblist, "w", encoding="utf-8") as fh:
        for j in jobs:
            fh.write(json.dumps(j) + "\n")

    print(f"[split_perprompt] manifest={args.manifest} split={args.split} -> {len(jobs)} 1-row manifests")
    print(f"[split_perprompt] arm={args.arm} seed={args.seed} split_flag=--split {split_flag}")
    print(f"[split_perprompt] joblist={args.joblist}")
    print(f"[split_perprompt] task_ids: {', '.join(ids[:5])}{' ...' if len(ids) > 5 else ''}")


if __name__ == "__main__":
    main()
