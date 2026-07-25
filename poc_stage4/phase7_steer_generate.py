"""Phase-7 (§11) — activation-addition causal test of the attack-success direction.

Loads the Fisher success direction produced by `scripts/phase7_extract_success_direction.py` and, for a
sweep of coefficients α (§11.1), generates from Qwen3-14B on the dev-25 CLEAN harmful prompts while
steering the residual stream at the selected layer:
    h_L' = h_L + (α·σ)·d_unit         (σ = natural projection std, so α is in std units)

Prediction (§11.5): if the direction is a *compliance/success* direction, +α should increase attack
success / reduce refusal and −α should do the reverse. α=0 is the un-steered baseline (the clean-prompt
control, §11.4 condition 1). Free generations are written per (goal, α); StrongREJECT scoring + the
ASR-vs-α curve + specificity (§11.6) are done downstream by the scoring/analysis step.

REUSE (no duplication): `poc_stage4.qwen3_model.load_qwen3_model` (+ `Qwen3Model` wrapper),
`poc_stage4.intervention_selection.{build_steering_hooks, add_hooks}` (the h+αd hook), and
`poc_stage_ae.thinking_position_utils` token helpers for think/answer splitting.

Usage (see slurm_scripts/run_phase7_steer.slurm):
  python -m poc_stage4.phase7_steer_generate \
    --direction-dir outputs/phase7_causal/success_dir__think_content_1__L20 \
    --alphas -3 -2 -1 -0.5 0 0.5 1 2 3 \
    --n-tasks 5 --max-new-tokens 2048 \
    --out outputs/phase7_causal/steer__think_content_1__L20/generations.jsonl
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import torch

from poc_stage4.qwen3_model import load_qwen3_model
from poc_stage4.intervention_selection import build_steering_hooks, add_hooks
from poc_stage_ae.thinking_position_utils import (
    get_thinking_start_token_ids,
    get_thinking_end_token_ids,
)

DEV25 = "data/manifests/dev_25.csv"


def _timed_addition_pre_hook(direction, coeff, timing):
    """§11.2 timing-restricted activation addition — same add as
    intervention_selection.get_activation_addition_input_pre_hook, gated by decode phase:
      timing='all'        → every forward (prefill + each decode step) [== the reused default]
      timing='prefill'    → only the prompt forward (activation.shape[1] > 1): steer the INPUT rep
      timing='generation' → only decode steps (activation.shape[1] == 1): steer each GENERATED token
    (With KV cache, prefill sees seq_len=prompt_len; each decode step sees seq_len=1.)"""
    def hook(module, inputs):
        activation = inputs[0] if isinstance(inputs, tuple) else inputs
        seqlen = activation.shape[1]
        apply = (timing == "all") or (timing == "prefill" and seqlen > 1) or \
                (timing == "generation" and seqlen == 1)
        if not apply:
            return inputs
        vector = direction.to(device=activation.device, dtype=activation.dtype)
        patched = activation + coeff * vector
        return (patched, *inputs[1:]) if isinstance(inputs, tuple) else patched
    return hook


def _load_goals(manifest: str, n_tasks: int | None):
    rows = []
    with open(manifest, newline="") as f:
        for r in csv.DictReader(f):
            rows.append({"task_id": r["task_id"], "instruction": r["instruction"],
                         "category": r.get("category", "")})
    return rows if n_tasks is None else rows[:n_tasks]


def _load_prompt_rows(path: str, n_tasks: int | None):
    """Pre-formatted prompts (§11.4 attacked-context test). Each row must carry `formatted_prompt`
    (the full chat-formatted attack prompt); extra keys (condition/ae_success/row_key) pass through."""
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                r = json.loads(line)
                r.setdefault("category", r.get("condition", ""))
                r.setdefault("instruction", r.get("row_key", r.get("task_id", "")))
                rows.append(r)
    return rows if n_tasks is None else rows[:n_tasks]


def _first_index(haystack: list[int], needle: list[int], start: int = 0) -> int | None:
    if not needle:
        return None
    for i in range(start, len(haystack) - len(needle) + 1):
        if haystack[i:i + len(needle)] == needle:
            return i
    return None


def _split_think_answer(gen_ids: list[int], tok, start_ids, end_ids) -> tuple[str, str, str]:
    """Return (full_text, think_text, answer_text). answer_text is everything after </think>."""
    end_at = _first_index(gen_ids, end_ids)
    full_text = tok.decode(gen_ids, skip_special_tokens=False)
    if end_at is None:
        # never closed thinking → whole thing is 'think', no separable answer
        think_text = tok.decode(gen_ids, skip_special_tokens=True)
        return full_text, think_text, ""
    answer_ids = gen_ids[end_at + len(end_ids):]
    think_ids = gen_ids[:end_at]
    return (full_text,
            tok.decode(think_ids, skip_special_tokens=True),
            tok.decode(answer_ids, skip_special_tokens=True))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--direction-dir", required=True)
    ap.add_argument("--alphas", nargs="+", type=float, required=True)
    ap.add_argument("--manifest", default=DEV25)
    ap.add_argument("--n-tasks", type=int, default=None)
    ap.add_argument("--model-name", default="Qwen/Qwen3-14B")
    ap.add_argument("--model-family", default="qwen3",
                    help="thinking-marker family for get_thinking_*_token_ids (qwen3 | gemma4 | "
                         "deepseek_r1). §C2 cross-model steering: DeepSeek uses the same '</think>' "
                         "end marker (encoded with its own tokenizer), so this is mainly for hygiene.")
    ap.add_argument("--max-new-tokens", type=int, default=2048)
    ap.add_argument("--max-seq-len", type=int, default=30000)
    ap.add_argument("--prompts-jsonl", default=None,
                    help="pre-formatted prompts (rows with formatted_prompt) for §11.4 attacked-context")
    ap.add_argument("--timing", choices=["all", "prefill", "generation"], default="all",
                    help="§11.2 timing-restricted steering: all positions / prefill-only / generated-tokens-only")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    ddir = Path(args.direction_dir)
    direction = torch.load(ddir / "direction.pt", map_location="cpu")
    meta = json.loads((ddir / "selected_direction.json").read_text())
    layer = int(meta["selected_layer"])
    sigma = float(meta["projection_sigma"])
    print(f"[phase7] direction {meta['position_name']} L{layer} sigma={sigma:.3f} "
          f"sep={meta.get('separation_in_sigma')}", flush=True)

    preformatted = args.prompts_jsonl is not None
    goals = (_load_prompt_rows(args.prompts_jsonl, args.n_tasks) if preformatted
             else _load_goals(args.manifest, args.n_tasks))
    print(f"[phase7] {len(goals)} goals × {len(args.alphas)} alphas = "
          f"{len(goals)*len(args.alphas)} generations (preformatted={preformatted})", flush=True)

    model_base = load_qwen3_model(args.model_name, require_cuda=True, log_device_placement=True)
    tok = model_base.tokenizer
    try:
        input_device = model_base.model.get_input_embeddings().weight.device
    except Exception:
        input_device = next(model_base.model.parameters()).device
    start_ids = get_thinking_start_token_ids(tok, args.model_family)
    end_ids = get_thinking_end_token_ids(tok, args.model_family)
    # Qwen3 stops on either <|im_end|>(151645) or <|endoftext|>(151643); pull the full stop set from
    # generation_config so a valid EOS is never mislabeled as max_new_tokens.
    _gc_eos = getattr(model_base.model.generation_config, "eos_token_id", None)
    eos_ids = set(_gc_eos if isinstance(_gc_eos, (list, tuple)) else [_gc_eos])
    if tok.eos_token_id is not None:
        eos_ids.add(tok.eos_token_id)
    eos_ids.discard(None)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    # Resume-safety (§23.4): this job runs on the preemptible partition. Pre-load completed
    # (identity, alpha) rows and append, so a preempt+requeue never truncates finished generations.
    def _ident(g):
        return g.get("row_key") or g["task_id"]
    done = set()
    if Path(args.out).exists():
        with open(args.out, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                done.add((r.get("row_key") or r.get("task_id"), float(r["alpha"])))
        if done:
            print(f"[phase7] resume: {len(done)} (row,alpha) already done — skipping", flush=True)
    n_written = 0
    with open(args.out, "a", encoding="utf-8") as fout:
        for goal in goals:
            # Attacked-context (§11.4): use the row's pre-formatted attack prompt verbatim; else format
            # the clean instruction with the chat template.
            formatted = (goal["formatted_prompt"] if preformatted
                         else model_base.format_prompts([goal["instruction"]], enable_thinking=True)[0])
            prompt_ids = tok(formatted, return_tensors="pt", padding=False,
                             truncation=False).input_ids[0].tolist()
            prompt_len = len(prompt_ids)
            input_tensor = torch.tensor(prompt_ids, dtype=torch.long).unsqueeze(0).to(input_device)

            for alpha in args.alphas:
                if (_ident(goal), float(alpha)) in done:
                    continue  # already generated (resume)
                coeff = alpha * sigma
                if alpha == 0.0:
                    pre_hooks, hooks = [], []  # baseline: no steering
                elif args.timing == "all":
                    pre_hooks, hooks = build_steering_hooks(  # reuse audited path for the default
                        model_base, direction, source_layer=layer, coeff=coeff)
                else:
                    pre_hooks = [(model_base.layers[layer],
                                  _timed_addition_pre_hook(direction, coeff, args.timing))]
                    hooks = []
                with torch.no_grad(), add_hooks(pre_hooks, hooks):
                    out = model_base.model.generate(
                        input_tensor,
                        max_new_tokens=args.max_new_tokens,
                        do_sample=False, temperature=None, top_p=None,
                        pad_token_id=tok.eos_token_id,
                    )
                full_ids = out[0].tolist()
                gen_ids = full_ids[prompt_len:]
                finish = "eos_token" if (gen_ids and gen_ids[-1] in eos_ids) else "max_new_tokens"
                full_text, think_text, answer_text = _split_think_answer(gen_ids, tok, start_ids, end_ids)
                think_closed = _first_index(gen_ids, end_ids) is not None
                row = {
                    "task_id": goal["task_id"], "category": goal["category"],
                    "instruction": goal["instruction"],
                    "alpha": alpha, "coeff": coeff, "layer": layer, "timing": args.timing,
                    "position_name": meta["position_name"], "direction_dir": str(ddir),
                    "generation_text": full_text, "think_text": think_text,
                    # 'answer' is scored for harmful assistance (§6.1); mirrors phase6 final_text.
                    "final_text": answer_text,
                    "generation_token_count": len(gen_ids),
                    "finish_reason": finish, "steered": alpha != 0.0,
                    # §11.6 format-integrity controls: separate true refusal from steering-induced
                    # format breakage (no </think> / empty answer). Downstream ASR-vs-α must not read
                    # an empty answer caused by broken format as a "refusal".
                    "think_closed": think_closed,
                    "answer_present": bool(answer_text.strip()),
                    # attacked-context provenance (present only for --prompts-jsonl runs)
                    "condition": goal.get("condition"),
                    "ae_success": goal.get("ae_success"),
                    "row_key": goal.get("row_key"),
                    "prompt_token_count": prompt_len,
                }
                fout.write(json.dumps(row, ensure_ascii=False) + "\n")
                fout.flush()
                n_written += 1
                print(f"  {goal['task_id']} α={alpha:+} tok={len(gen_ids)} ans_chars={len(answer_text)}",
                      flush=True)
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

    print(f"[phase7] wrote {n_written} generations → {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
