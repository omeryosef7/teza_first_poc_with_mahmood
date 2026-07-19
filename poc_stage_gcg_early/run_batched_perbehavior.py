#!/usr/bin/env python3
"""
Batched per-behavior GCG driver (Option B) for the Native-CoT pilot.

Loads Qwen3-14B ONCE, then loops over a job-list of 1-row-manifest optimizations
(each a separate per-behavior suffix), calling the reusable optimizer core
gcg_optimizer.run_optimization(model, tokenizer, ...). Each job re-seeds from
config.gcg.seed (gcg_optimizer.py:68-71), so loop order does not affect results.
Idempotent/resume-safe: a job whose output_dir already has FINAL_CANDIDATES.jsonl
is skipped; an in-flight job resumes from checkpoint.pt.

suffix_placement="user" (FIXED v2), filter_cand=False (--no-filter-cand rule),
suffix_length=20, lambda_repr=0. Writes CONFIG.json (for the placement guardrail),
copies the manifest, and produces the standard bundle per run dir.

Usage: python -m poc_stage_gcg_early.run_batched_perbehavior <joblist.jsonl>
"""
from __future__ import annotations
import json, shutil, sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from poc_stage_gcg_early.config import RunConfig, GCGHyperparams, ObjectiveWeights
from poc_stage_gcg_early.build_safe_surrogate_manifest import load_manifest
from poc_stage_gcg_early.gcg_optimizer import run_optimization

MODEL = "Qwen/Qwen3-14B"


def build_config(job: dict) -> RunConfig:
    out = Path(job["output_dir"])
    return RunConfig(
        run_id=out.name,
        model_family="qwen3",
        model_name_or_path=MODEL,
        manifest_path=job["manifest"],
        gcg=GCGHyperparams(
            suffix_length=20, batch_size=64, topk=256,
            n_steps=int(job.get("n_steps", 500)), seed=int(job["seed"]),
            checkpoint_every=10, snapshot_every=50,
            filter_cand=False, suffix_placement="user",
        ),
        objective=ObjectiveWeights(lambda_repr=0.0, lambda_kl=0.0, selection_mode="weighted"),
        output_dir=str(out),
        enable_thinking=True,
    )


def main(joblist_path: str):
    jobs = [json.loads(l) for l in open(joblist_path) if l.strip()]
    print(f"[batched] {len(jobs)} jobs from {joblist_path}", flush=True)

    from poc_stage4.qwen3_model import load_qwen3_model
    wrapped = load_qwen3_model(MODEL, require_cuda=True, log_device_placement=True, device_map="auto")
    model, tokenizer = wrapped.model, wrapped.tokenizer
    print("[batched] model loaded once; starting loop", flush=True)

    done = skipped = failed = 0
    for i, job in enumerate(jobs):
        out = Path(job["output_dir"])
        out.mkdir(parents=True, exist_ok=True)
        if (out / "FINAL_CANDIDATES.jsonl").exists():
            skipped += 1
            print(f"[batched] ({i+1}/{len(jobs)}) SKIP done: {out.name}", flush=True)
            continue
        try:
            config = build_config(job)
            (out / "CONFIG.json").write_text(config.to_json(), encoding="utf-8")   # placement guardrail
            mcopy = out / "MANIFEST.jsonl"
            if not mcopy.exists():
                shutil.copy(job["manifest"], mcopy)
            tasks = [t for t in load_manifest(Path(job["manifest"])) if t.split == "train"]
            print(f"[batched] ({i+1}/{len(jobs)}) RUN {out.name}  seed={job['seed']} tasks={len(tasks)}", flush=True)
            run_optimization(model=model, tokenizer=tokenizer, model_family="qwen3",
                             tasks=tasks, config=config, reference_cache=None, output_dir=out)
            done += 1
        except Exception as e:
            failed += 1
            (out / "BATCHED_ERROR.txt").write_text(repr(e))
            print(f"[batched] ({i+1}/{len(jobs)}) FAILED {out.name}: {e!r}", flush=True)
    print(f"[batched] finished: done={done} skipped={skipped} failed={failed}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
