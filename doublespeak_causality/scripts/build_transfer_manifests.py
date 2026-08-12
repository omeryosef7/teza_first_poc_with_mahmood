#!/usr/bin/env python3
"""Build the §7.5 TRANSFER-MATRIX plan: prompt i's per-prompt suffix applied to prompt j.

Scientific question: does a per-prompt suffix work ONLY on the prompt it was optimized for?
  diagonal (i->i) high, off-diagonal (i->j) low  => prompt-SPECIFIC route (H1/H4 + §5.5):
      the universal-suffix failure is explained, because there is no shared token move.
  diagonal ~= off-diagonal                       => the suffix is generic, and per-prompt
      optimization buys nothing a universal suffix could not have found.

NO EVAL CODE CHANGES ARE NEEDED. `26_eval_p9_gcg_heldout_asr.py` already applies ONE run-dir's
suffix to EVERY row of a manifest, and `evaluate_optimized_suffixes._row_key` is
(task_id, suffix_label, seed) -- so giving each source its own `--arm-label` keeps the rows
distinct and resume-safe. Transfer is therefore just: source i's run-dir x a manifest of target
prompts. This script only writes those target manifests and the plan.

SUBSAMPLING IS EXPLICIT (plan §3.15 -- no silent caps). The full matrix is 37x37 = 1369
generations per arm per seed. Default --k 5 samples 5 off-diagonal targets per source
(deterministic from --sample-seed), giving 37x6 = 222 -- ~6x cheaper and sufficient for a paired
diagonal-vs-off-diagonal estimate. `--k 0` requests the FULL matrix. The chosen k and the exact
sampled target ids are recorded in the plan so the coverage is auditable.

Safety: writes/prints task_ids and COUNTS only -- never instruction or suffix text (§3.14).
"""
from __future__ import annotations
import argparse, json, os, random
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, help="full v3 manifest")
    ap.add_argument("--split", default="test")
    ap.add_argument("--joblist", required=True,
                    help="per-prompt joblist (gives each source's run dir)")
    ap.add_argument("--k", type=int, default=5,
                    help="off-diagonal targets per source; 0 = FULL matrix")
    ap.add_argument("--sample-seed", type=int, default=20260812)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--arm-tag", required=True, help="e.g. asym_p75_mechanism_seed42")
    args = ap.parse_args()

    rows = [json.loads(l) for l in open(args.manifest) if l.strip()]
    sel = {r["task_id"]: r for r in rows if r.get("split") == args.split}
    if not sel:
        raise SystemExit(f"no rows with split=={args.split!r}")

    jobs = [json.loads(l) for l in open(args.joblist) if l.strip()]
    # Only sources whose optimization actually finished can donate a suffix.
    sources = [j for j in jobs
               if os.path.exists(os.path.join(j["output_dir"], "FINAL_CANDIDATES.jsonl"))]
    if not sources:
        raise SystemExit(f"no finished per-prompt runs in {args.joblist} -- nothing to transfer")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    all_ids = sorted(sel)
    rng = random.Random(args.sample_seed)

    plan, n_pairs = [], 0
    for j in sources:
        src = j["task_id"]
        others = [t for t in all_ids if t != src]
        if args.k and args.k < len(others):
            targets = sorted(rng.sample(others, args.k))
        else:
            targets = others
        # The DIAGONAL (i->i) is the reference the off-diagonal is compared against, so it is
        # always included -- never sampled away.
        targets = [src] + targets

        mpath = out_dir / f"targets_{src}.jsonl"
        tmp = mpath.with_suffix(f".tmp{os.getpid()}")
        with open(tmp, "w", encoding="utf-8") as fh:
            for t in targets:
                fh.write(json.dumps(sel[t]) + "\n")
        os.replace(tmp, mpath)

        plan.append({"source_task_id": src, "source_run_dir": j["output_dir"],
                     "target_manifest": str(mpath), "target_task_ids": targets,
                     "n_targets": len(targets), "split": args.split,
                     "arm_label": f"xfer_{args.arm_tag}_from_{src}"})
        n_pairs += len(targets)

    with open(args.plan, "w", encoding="utf-8") as fh:
        for p in plan:
            fh.write(json.dumps(p) + "\n")

    print(f"[transfer] sources with finished runs: {len(sources)}/{len(jobs)}")
    print(f"[transfer] k={args.k} ({'FULL matrix' if not args.k else 'subsampled'}) "
          f"-> {n_pairs} (source,target) generations, incl. {len(sources)} diagonal")
    print(f"[transfer] plan={args.plan}")


if __name__ == "__main__":
    main()
