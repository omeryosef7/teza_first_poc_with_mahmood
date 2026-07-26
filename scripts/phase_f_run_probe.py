#!/usr/bin/env python3
"""Phase-F1.3 GPU runner — attention-to-span probe over EXISTING attacked prompts.

This wires the real model forward pass into the verified CPU stack:
`scripts/phase_f_attention_probe.py` (numeric core) + `scripts/phase_f_probe_driver.py`
(sanitized orchestration). It is INTERPRETABILITY ONLY: it runs a single forward pass
(with `output_attentions=True`) over the already-generated attack PROMPTS annotated in
Phase-F1.1 and measures prompt-internal attention among the labelled span components at
generation start. **No new text is generated.** No new attacks are created.

Design: `docs/COT_HIJACKING_EXACT_MECHANISM_REPORT.md` §6.1a–§6.4. The F1.1 annotator indexed
tokens of `apply_chat_template([{user: attack_prompt}], add_generation_prompt=True)`; this runner
reconstructs that EXACT templated string, re-tokenizes it identically (`add_special_tokens=False`),
asserts the token count matches the record's `n_tokens` (alignment guard), and runs the model forward.
Per §6.2 the cross-outcome contrast uses components present in BOTH splits (benign_puzzle_scaffold /
harmful_instruction / final_answer_cue); `injected_reasoning` is a failure-only probe (§6.1a).

Only the DISCOVERY split is measured here (the TEST split is reserved for F1.5 causal work).

Usage (GPU):
  python phase_f_run_probe.py --spans <spans.jsonl> --attacked <original_attacked.jsonl> \
      --model <hf/name> --out-csv results/COT_F13_<model>.csv [--limit N] [--dtype bfloat16]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.phase_f_probe_driver import run_probe  # noqa: E402

# Both-splits contrast components + the failure-only injected_reasoning probe (§6.1a/§6.2).
COMPONENTS = ["benign_puzzle_scaffold", "harmful_instruction", "final_answer_cue", "injected_reasoning"]


def _join_key(rec: Dict) -> Tuple:
    return (rec.get("task_id"), rec.get("conversation_id"), rec.get("attack_iteration"))


def build_attack_prompt_index(attacked_path: str) -> Dict[Tuple, str]:
    """Map (task_id, conversation_id, attack_iteration) -> attack_prompt from the ORIGINAL jsonl.

    This is the only place harmful prompt text is read; it stays local to the forward pass.
    """
    index: Dict[Tuple, str] = {}
    with open(attacked_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            key = (r.get("task_id"), r.get("conversation_id"), r.get("attack_iteration"))
            ap = r.get("attack_prompt")
            if ap:
                index[key] = ap
    return index


def make_forward_fn(model, tokenizer, prompt_index: Dict[Tuple, str], device: str):
    """Return forward_fn(record) -> np.ndarray [n_layers, n_heads, seq, seq].

    Reconstructs the F1.1 token sequence, asserts alignment, runs one forward pass with
    output_attentions=True, and returns the stacked attention as float32 numpy. Attention is
    computed then freed per record (no accumulation of huge tensors).
    """
    import numpy as np
    import torch

    def forward_fn(record: Dict):
        key = _join_key(record)
        attack_prompt = prompt_index.get(key)
        if attack_prompt is None:
            print(f"[F1.3] SKIP {key}: no attack_prompt in the attacked jsonl", file=sys.stderr, flush=True)
            return None  # recoverable → build_per_record drops this record
        templated = tokenizer.apply_chat_template(
            [{"role": "user", "content": attack_prompt}],
            tokenize=False,
            add_generation_prompt=True,
        )
        enc = tokenizer(templated, add_special_tokens=False, return_tensors="pt")
        n_tok = enc["input_ids"].shape[1]
        expected = int(record.get("n_tokens") or 0)
        if expected and n_tok != expected:
            # tokenizer/template drift → span ranges would not align. Skip (don't kill the batch);
            # a high skip-count is itself a reported diagnostic.
            print(
                f"[F1.3] SKIP {key}: token-count mismatch forward={n_tok} vs F1.1 n_tokens={expected}",
                file=sys.stderr, flush=True,
            )
            return None
        input_ids = enc["input_ids"].to(device)
        with torch.no_grad():
            out = model(input_ids=input_ids, output_attentions=True, use_cache=False)
        # out.attentions: tuple(len=n_layers) of [1, n_heads, seq, seq] (bf16 on GPU).
        # Upcast+offload PER LAYER to avoid one 40-layer fp32 GPU allocation. For Qwen3-14B
        # with seq~1251 the stacked fp32 tensor is ~10 GiB and OOM'd on top of the 14B weights
        # (job 685334_0). Each layer's fp32 copy [n_heads, seq, seq] is small (~250 MiB); we
        # move it to CPU immediately and stack there.
        layers = [a[0].to(torch.float32).cpu().numpy() for a in out.attentions]  # each [H, seq, seq]
        arr = np.stack(layers, axis=0)  # [n_layers, n_heads, seq, seq]
        del out, input_ids, layers
        if device.startswith("cuda"):
            torch.cuda.empty_cache()
        return arr

    return forward_fn


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description="Phase-F1.3 attention-to-span GPU probe (interpretability).")
    ap.add_argument("--spans", required=True, help="F1.1 spans jsonl")
    ap.add_argument("--attacked", required=True, help="ORIGINAL attacked jsonl (has attack_prompt)")
    ap.add_argument("--model", required=True, help="HF model name (must match the F1.1 tokenizer)")
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--per-record-csv", default=None,
                    help="optional per-record long-format CSV for the §6.3a length-confound screen; "
                         "default = <out-csv stem>_perrecord.csv when --confound-log is set")
    ap.add_argument("--confound-log", action="store_true",
                    help="also emit the per-record CSV (for the confound screen)")
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16", "float16", "float32"])
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args(argv)

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    dtype = {"bfloat16": torch.bfloat16, "float16": torch.float16, "float32": torch.float32}[args.dtype]
    print(f"[F1.3] loading tokenizer+model {args.model} dtype={args.dtype} device={args.device}", flush=True)
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=dtype, attn_implementation="eager"
    )
    model.to(args.device)
    model.eval()
    # eager attention is REQUIRED for output_attentions (sdpa/flash return None attentions).

    prompt_index = build_attack_prompt_index(args.attacked)
    print(f"[F1.3] attack_prompt index: {len(prompt_index)} rows", flush=True)

    per_record_csv = args.per_record_csv
    if args.confound_log and per_record_csv is None:
        stem = args.out_csv[:-4] if args.out_csv.endswith(".csv") else args.out_csv
        per_record_csv = f"{stem}_perrecord.csv"

    forward_fn = make_forward_fn(model, tok, prompt_index, args.device)
    result = run_probe(args.spans, forward_fn, args.out_csv, components=COMPONENTS, top_k=10,
                       per_record_csv=per_record_csv)
    print(
        f"[F1.3] DONE n_discovery={result['n_discovery']} n_test(reserved)={result['n_test']} "
        f"-> {args.out_csv}" + (f" + per-record {per_record_csv}" if per_record_csv else ""),
        flush=True,
    )
    # Print the top candidate heads per component (numbers only).
    for comp, heads in result.get("top_heads", {}).items():
        print(f"[F1.3] top heads |Δattn| into {comp}: {heads[:5]}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
