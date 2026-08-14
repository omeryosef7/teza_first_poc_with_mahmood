#!/usr/bin/env python
"""
ASYMMETRY SPRINT §20.5 — build the `randtok` noise floor pool. CPU only; submits nothing.

§20.5's one remaining mandatory condition is a random-token pool: without it, "+0.084 ASR at k=2"
cannot be separated from two draws of judge noise, because a max-statistic rises with k by
construction. Verified absent from disk (the only `neutral_control` rows are a different corpus,
0 of them clearharm), so it has to be generated -- but it is a SMALL job, not the 4-8 GPU-h the
ledger implied: balanced k caps at 2 on the existing grid, so K=3 suffixes x 37 test prompts =
111 generations.

WHY STUB DIRECTORIES
--------------------
`eval_perprompt_batched.py --mode transfer` reads each suffix via `final_suffix(source_run_dir)`,
i.e. from a `FINAL_CANDIDATES.jsonl` inside a real optimization directory; a random pool has no
such directory. Rather than add a code path to the evaluator, this writes K one-line stub dirs in
that exact shape. The scoring path is then byte-identical to the one every §7.5 number came
through -- which is the evaluator's stated design principle ("does NOT reimplement scoring") and
the only way the floor is comparable to the thing it is a floor for.

The stubs live under their OWN root (`outputs/stage_gcg_randtok_floor/`), never inside
`outputs/stage_gcg_perprompt/`, because several analyses glob that tree by prefix and a stub with
no ITERATION_LOG would be a partial-run-shaped object sitting in the middle of them.

WHAT THE SUFFIXES ARE
---------------------
16 token ids (matching §7.5's `suffix_len=16`) sampled uniformly from the tokenizer vocabulary,
excluding special/added tokens, then decoded. Uniform-over-vocab is the right null for "what does
an UNoptimized suffix of the same length buy": it is the distribution GCG's search starts from
before any gradient information is used. Each pool index is seeded deterministically, so the pool
is reproducible from this file alone.

Caveat inherited from the harness, stated rather than hidden: a decoded random string may
retokenize to a different id sequence than the one sampled (the same boundary-token issue
`suffix_token_manager` warns about). That is fine for a floor -- what is evaluated is the STRING,
exactly as for the real suffixes, which go through the same decode.

Scalars and ids only; the suffix strings are written to disk for the evaluator but never printed.
"""
import argparse, json, os, random
from pathlib import Path

DEFAULT_ROOT = "outputs/stage_gcg_randtok_floor"


def sample_suffix(tok, n_tokens, rng):
    """-> decoded string of n_tokens ids drawn uniformly from the ordinary vocabulary."""
    special = set(tok.all_special_ids or [])
    # added/reserved tokens are not reachable as ordinary suffix content
    added = {i for i in getattr(tok, "added_tokens_decoder", {})}
    vocab_size = len(tok)
    ids = []
    while len(ids) < n_tokens:
        i = rng.randrange(vocab_size)
        if i in special or i in added:
            continue
        ids.append(i)
    return tok.decode(ids, skip_special_tokens=True), ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--k", type=int, default=3,
                    help="pool size per target; balanced k caps at 2 on the real grid, "
                         "3 gives one spare draw")
    ap.add_argument("--suffix-len", type=int, default=16)
    ap.add_argument("--seed", type=int, default=20260814)
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--manifest",
                    default="doublespeak_causality/data/gcg/clearharm_llama_v3/"
                            "clearharm_llama_doublespeak.jsonl")
    ap.add_argument("--split", default="test")
    ap.add_argument("--plan-out",
                    default="doublespeak_causality/data/gcg/clearharm_llama_v3/"
                            "randtok_floor_plan.jsonl")
    args = ap.parse_args()

    # Same cache the SLURM runners export; without it an offline load hits the hub and fails.
    proj = Path(__file__).resolve().parents[2]
    os.environ.setdefault("HF_HOME", str(proj / ".cache/huggingface"))
    os.environ.setdefault("HF_HUB_CACHE", str(proj / ".cache/huggingface/hub"))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(proj / ".cache/huggingface/hub"))
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(args.model)

    n_targets = sum(1 for l in open(args.manifest)
                    if l.strip() and json.loads(l).get("split") == args.split)
    if not n_targets:
        raise SystemExit(f"no rows with split={args.split} in {args.manifest}")

    root = Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    plan_rows = []
    for j in range(args.k):
        rng = random.Random(args.seed + j)            # reproducible per pool index
        suffix, ids = sample_suffix(tok, args.suffix_len, rng)
        d = root / f"asym_p205_randtok_floor_pool{j}"
        d.mkdir(exist_ok=True)
        (d / "FINAL_CANDIDATES.jsonl").write_text(
            json.dumps({"suffix_str": suffix, "n_tokens": len(ids),
                        "provenance": "asym_p205_make_randtok_floor.py",
                        "sampling": "uniform over ordinary vocabulary, no optimization",
                        "rng_seed": args.seed + j}) + "\n")
        plan_rows.append({"source_run_dir": str(d.resolve()),
                          "target_manifest": str(Path(args.manifest).resolve()),
                          "split": args.split,
                          "arm_label": f"randtok_floor_pool{j}"})
        print(f"  pool{j}: {len(ids)} tokens -> {d}")

    Path(args.plan_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.plan_out).write_text("".join(json.dumps(r) + "\n" for r in plan_rows))

    print(f"\nwrote {args.plan_out}: {args.k} sources x {n_targets} {args.split} prompts "
          f"= {args.k * n_targets} generations")
    print("\nnext (needs a GPU slot; §3.1 -- the floor must share the 3090 class its pools do):")
    print(f"  sbatch --nodelist=<free 3090s> --export=ALL,MODE=transfer,"
          f"PLAN={args.plan_out},EVAL_SEED=42 slurm_scripts/run_perprompt_eval.slurm")
    print("\nthen fold into the pool statistic:")
    print(f"  python doublespeak_causality/scripts/asym_p205_bestofk_existing.py "
          f"--floor-root {args.root}")


if __name__ == "__main__":
    main()
