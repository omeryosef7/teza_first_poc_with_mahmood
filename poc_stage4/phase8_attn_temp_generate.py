"""§C1 (Claude extension, user-authorized 2026-07-23) — CAUSAL attention-concentration intervention.

Tests whether attention *concentration* is a causal lever on CoT-Hijacking jailbreak success (not merely
the length-confounded correlate found observationally in §10.1-D). We rescale each targeted
`Qwen3Attention.self_attn.scaling` by γ = 1/τ, an attention-logit TEMPERATURE applied pre-softmax:
    τ < 1 (γ > 1)  → SHARPEN  attention (more concentrated — the §10.1-D "success" direction)
    τ > 1 (γ < 1)  → FLATTEN  attention (more diffuse)
    τ = 1          → un-intervened baseline (context manager is a no-op)

`Qwen3Attention.forward` reads `self.scaling` fresh on every prefill AND decode step and forwards it to
the active backend (eager/SDPA/flash), so this is backend-agnostic — it works under the default fast SDPA
(no eager needed) and, crucially, holds the PROMPT (hence its LENGTH) FIXED while perturbing only the
attention distribution → structurally immune to the length confound that clouds every predictive analysis.
Verified against transformers 5.12.1 (Qwen3Attention.__init__ sets scaling = head_dim**-0.5; forward
passes scaling=self.scaling to eager_attention_forward / sdpa_attention_forward pre-softmax).

Protocol (§11 mirror): SUFFICIENCY (sharpen clean harmful prompts → does ASR rise above ~0?) and
NECESSITY (flatten attacked CoT-Hijacking prompts → does ASR fall below ~1?), swept over τ, with §11.6
format-integrity controls (think_closed / answer_present) so a coherence collapse from an extreme τ is not
misread as a causal ASR move.

REUSE (no duplication): all generation plumbing (goal/prompt loaders, think/answer split, resume-safety,
row schema, eos handling) is imported from `poc_stage4.phase7_steer_generate`; the only new logic is the
attention-temperature context manager. Rows carry `attn_temp`=τ AND `alpha`=round(1−τ,4) so the EXISTING
`scripts/phase7_analyze_causal.py` prep+curve run UNCHANGED (τ=1→α=0 baseline; sharpen→α>0, flatten→α<0).

Usage (see slurm_scripts/run_phase8_attntemp.slurm):
  python -m poc_stage4.phase8_attn_temp_generate \
    --taus 0.5 0.7 1.0 1.4 2.0 --attn-layers targeted \
    --n-tasks 25 --max-new-tokens 2048 \
    --out outputs/phase8_attn_causal/suff_targeted/generations.jsonl
"""
from __future__ import annotations

import argparse
import contextlib
import json
from pathlib import Path

import torch

from poc_stage4.qwen3_model import load_qwen3_model
from poc_stage4.phase7_steer_generate import (
    DEV25,
    _load_goals,
    _load_prompt_rows,
    _first_index,
    _split_think_answer,
)
from poc_stage_ae.thinking_position_utils import (
    get_thinking_start_token_ids,
    get_thinking_end_token_ids,
)


@contextlib.contextmanager
def attention_temperature(model_base, tau: float, layer_idxs: list[int]):
    """Temporarily rescale `self_attn.scaling` by γ=1/τ on the targeted layers (pre-softmax attention
    temperature). Restores the original scaling in `finally` — so a preempt/exception can never leave a
    module permanently rescaled."""
    gamma = 1.0 / tau
    saved: dict[int, float] = {}
    try:
        for li in layer_idxs:
            attn = model_base.layers[li].self_attn
            saved[li] = attn.scaling
            attn.scaling = attn.scaling * gamma
        yield
    finally:
        for li, s in saved.items():
            model_base.layers[li].self_attn.scaling = s


def _resolve_layers(spec: str, n_layers: int) -> list[int]:
    """'all' → every layer; 'targeted' → §10.1-D concentration-predictive band L22-30 (inclusive);
    else a comma-separated explicit list."""
    if spec == "all":
        return list(range(n_layers))
    if spec == "targeted":
        return [li for li in range(22, 31) if li < n_layers]
    return [int(x) for x in spec.split(",") if x.strip() != ""]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--taus", nargs="+", type=float, required=True,
                    help="attention temperatures; MUST include 1.0 (the un-intervened baseline)")
    ap.add_argument("--attn-layers", default="targeted",
                    help="'targeted' (L22-30) | 'all' | comma-list e.g. 22,23,24")
    ap.add_argument("--manifest", default=DEV25)
    ap.add_argument("--n-tasks", type=int, default=None)
    ap.add_argument("--model-name", default="Qwen/Qwen3-14B")
    ap.add_argument("--max-new-tokens", type=int, default=2048)
    ap.add_argument("--prompts-jsonl", default=None,
                    help="pre-formatted attacked prompts (rows with formatted_prompt) for the NECESSITY arm")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    if 1.0 not in [float(t) for t in args.taus]:
        print("[phase8] WARNING: --taus does not include 1.0; the analysis baseline (α=0) will be absent.",
              flush=True)

    preformatted = args.prompts_jsonl is not None
    goals = (_load_prompt_rows(args.prompts_jsonl, args.n_tasks) if preformatted
             else _load_goals(args.manifest, args.n_tasks))

    model_base = load_qwen3_model(args.model_name, require_cuda=True, log_device_placement=True)
    tok = model_base.tokenizer
    try:
        input_device = model_base.model.get_input_embeddings().weight.device
    except Exception:
        input_device = next(model_base.model.parameters()).device

    n_layers = len(model_base.layers)
    layer_idxs = _resolve_layers(args.attn_layers, n_layers)
    # Base scaling per targeted layer, to assert clean restoration after the run (preempt-safety guard).
    base_by_layer = {li: model_base.layers[li].self_attn.scaling for li in layer_idxs}
    print(f"[phase8] attn-temp intervention on {len(layer_idxs)} layers ({args.attn_layers}): {layer_idxs}",
          flush=True)
    print(f"[phase8] {len(goals)} prompts × {len(args.taus)} taus = {len(goals)*len(args.taus)} gens "
          f"(preformatted={preformatted})", flush=True)

    start_ids = get_thinking_start_token_ids(tok, "qwen3")
    end_ids = get_thinking_end_token_ids(tok, "qwen3")
    _gc_eos = getattr(model_base.model.generation_config, "eos_token_id", None)
    eos_ids = set(_gc_eos if isinstance(_gc_eos, (list, tuple)) else [_gc_eos])
    if tok.eos_token_id is not None:
        eos_ids.add(tok.eos_token_id)
    eos_ids.discard(None)

    def _ident(g):
        return g.get("row_key") or g["task_id"]

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    # Resume-safety (§23.4): preemptible partition — preload completed (identity, τ) rows and append.
    done = set()
    if Path(args.out).exists():
        with open(args.out, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                done.add((r.get("row_key") or r.get("task_id"), float(r["attn_temp"])))
        if done:
            print(f"[phase8] resume: {len(done)} (row,τ) already done — skipping", flush=True)

    n_written = 0
    with open(args.out, "a", encoding="utf-8") as fout:
        for goal in goals:
            formatted = (goal["formatted_prompt"] if preformatted
                         else model_base.format_prompts([goal["instruction"]], enable_thinking=True)[0])
            prompt_ids = tok(formatted, return_tensors="pt", padding=False,
                             truncation=False).input_ids[0].tolist()
            prompt_len = len(prompt_ids)
            input_tensor = torch.tensor(prompt_ids, dtype=torch.long).unsqueeze(0).to(input_device)

            for tau in args.taus:
                tau = float(tau)
                if (_ident(goal), tau) in done:
                    continue
                ctx = (contextlib.nullcontext() if tau == 1.0
                       else attention_temperature(model_base, tau, layer_idxs))
                with torch.no_grad(), ctx:
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
                    "task_id": goal["task_id"], "category": goal.get("category", ""),
                    "instruction": goal.get("instruction", ""),
                    # τ is the intervention; alpha=1−τ is the curve-compatible alias (τ=1→α=0 baseline,
                    # sharpen τ<1→α>0, flatten τ>1→α<0) so phase7_analyze_causal runs UNCHANGED.
                    "attn_temp": tau, "alpha": round(1.0 - tau, 4),
                    "attn_layers": args.attn_layers, "layer_idxs": layer_idxs,
                    "generation_text": full_text, "think_text": think_text,
                    "final_text": answer_text,
                    "generation_token_count": len(gen_ids),
                    "finish_reason": finish, "steered": tau != 1.0,
                    # §11.6 format-integrity controls.
                    "think_closed": think_closed,
                    "answer_present": bool(answer_text.strip()),
                    "condition": goal.get("condition"),
                    "ae_success": goal.get("ae_success"),
                    "row_key": goal.get("row_key"),
                    "prompt_token_count": prompt_len,
                }
                fout.write(json.dumps(row, ensure_ascii=False) + "\n")
                fout.flush()
                n_written += 1
                print(f"  {goal['task_id']} τ={tau} tok={len(gen_ids)} ans_chars={len(answer_text)}",
                      flush=True)
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

    # Preempt-safety guard: every targeted module's scaling must be back to its base value.
    for li, base in base_by_layer.items():
        cur = model_base.layers[li].self_attn.scaling
        assert abs(cur - base) < 1e-9, f"layer {li} scaling not restored: {cur} != base {base}"

    print(f"[phase8] wrote {n_written} generations → {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
