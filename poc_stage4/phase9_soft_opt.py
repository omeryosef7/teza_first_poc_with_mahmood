"""§Phase 8+9 (§12/§13) — SOFT-OPTIMIZATION upper-bound test of the success-direction objective (Gate 4).

The plan's Gate 3 (is the success direction causal?) = No (activation-addition + attention-temperature
steering nulls, Qwen3 & DeepSeek). The user directed us into the optimization branch anyway. This is the
cleanest entry: the Phase-9 SOFT-OPTIMIZATION UPPER-BOUND test.

For each clean harmful prompt we prepend K trainable "soft" embedding vectors (a continuous prefix, the
STRONGEST/upper-bound input manipulation — unconstrained, off the token manifold) and optimize them by
gradient descent to MAXIMIZE the projection of the residual stream (at the direction's position/layer)
onto the unit success direction. Then we free-generate from the optimized soft prefix and StrongREJECT-score.

Gate-4 read (§25):
  - If soft-opt drives the projection UP (toward/beyond the natural success mean) but ASR does NOT rise
    above the un-optimized baseline → the direction is not manipulable-into-behavior from the input →
    CONFIRMS predictive-not-causal from the OPTIMIZATION side (complements the steering nulls).
  - If ASR rises with the projection → the direction IS manipulable → revives the §12.3 objective.

REUSE (no duplication): `poc_stage4.qwen3_model.load_qwen3_model`, the fitted success direction
(`outputs/phase7_causal/success_dir__*/{direction.pt,selected_direction.json}`), the goal loader +
think/answer split from `poc_stage4.phase7_steer_generate`. Output rows feed the existing
`scripts/phase7_analyze_causal.py`-style StrongREJECT pipeline (two rows per goal: arm=baseline|optimized).

Usage (see slurm_scripts/run_phase9_softopt.slurm):
  python -m poc_stage4.phase9_soft_opt \
    --direction-dir outputs/phase7_causal/success_dir__prefill_last__L16 \
    --n-tasks 25 --k-soft 8 --steps 100 --lr 0.05 --max-new-tokens 2048 \
    --out outputs/phase9_softopt/pfl_L16/generations.jsonl
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from poc_stage4.qwen3_model import load_qwen3_model
from poc_stage4.phase7_steer_generate import (
    DEV25, _load_goals, _first_index, _split_think_answer,
)
from poc_stage_ae.thinking_position_utils import (
    get_thinking_start_token_ids, get_thinking_end_token_ids,
)


def _read_hook(store):
    """forward_pre_hook that captures the residual stream ENTERING the layer at store['read_pos'].
    Keeps the graph (no detach/no_grad) so gradients flow to the soft prefix during optimization."""
    def hook(module, inputs):
        act = inputs[0] if isinstance(inputs, tuple) else inputs  # [batch, seq, d]
        store["h"] = act[0, store["read_pos"], :]
        return inputs
    return hook


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--direction-dir", required=True)
    ap.add_argument("--manifest", default=DEV25)
    ap.add_argument("--n-tasks", type=int, default=25)
    ap.add_argument("--model-name", default="Qwen/Qwen3-14B")
    ap.add_argument("--k-soft", type=int, default=8, help="number of trainable soft-prefix embeddings")
    ap.add_argument("--steps", type=int, default=100)
    ap.add_argument("--lr", type=float, default=0.05)
    ap.add_argument("--max-new-tokens", type=int, default=2048)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    ddir = Path(args.direction_dir)
    direction = torch.load(ddir / "direction.pt", map_location="cpu").float()  # unit-norm [d]
    meta = json.loads((ddir / "selected_direction.json").read_text())
    layer = int(meta["selected_layer"])
    sigma = float(meta.get("projection_sigma") or 1.0)
    succ_mean = meta.get("proj_success_mean")
    fail_mean = meta.get("proj_failure_mean")
    print(f"[phase9] direction {meta['position_name']} L{layer} d={direction.numel()} "
          f"sigma={sigma:.3f} succ_mean={succ_mean} fail_mean={fail_mean}", flush=True)

    goals = _load_goals(args.manifest, args.n_tasks)
    model_base = load_qwen3_model(args.model_name, require_cuda=True, log_device_placement=True)
    model = model_base.model
    tok = model_base.tokenizer
    emb = model.get_input_embeddings()
    dev = emb.weight.device
    mdtype = emb.weight.dtype
    d_unit = direction.to(dev)  # fp32
    target_layer = model_base.layers[layer]

    start_ids = get_thinking_start_token_ids(tok, "qwen3")
    end_ids = get_thinking_end_token_ids(tok, "qwen3")
    _gc_eos = getattr(model.generation_config, "eos_token_id", None)
    eos_ids = set(_gc_eos if isinstance(_gc_eos, (list, tuple)) else [_gc_eos])
    if tok.eos_token_id is not None:
        eos_ids.add(tok.eos_token_id)
    eos_ids.discard(None)

    def _proj_at(inputs_embeds, read_pos):
        """Forward inputs_embeds [1,S,d]; return the projection scalar of the layer-L input residual at
        read_pos onto the unit success direction. Graph retained (caller controls no_grad)."""
        store = {"read_pos": read_pos}
        h = target_layer.register_forward_pre_hook(_read_hook(store))
        try:
            model(inputs_embeds=inputs_embeds,
                  attention_mask=torch.ones(inputs_embeds.shape[:2], device=dev, dtype=torch.long))
        finally:
            h.remove()
        return torch.dot(store["h"].float(), d_unit)

    def _generate(inputs_embeds):
        am = torch.ones(inputs_embeds.shape[:2], device=dev, dtype=torch.long)
        with torch.no_grad():
            out = model.generate(inputs_embeds=inputs_embeds, attention_mask=am,
                                 max_new_tokens=args.max_new_tokens, do_sample=False,
                                 temperature=None, top_p=None, pad_token_id=tok.eos_token_id)
        # With inputs_embeds (no input_ids) generate returns NEW tokens only — do NOT slice a prompt_len.
        return out[0].tolist()

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    done = {}  # (task_id, arm) -> projection (so a resumed run can still report the baseline proj)
    if Path(args.out).exists():
        for line in open(args.out, encoding="utf-8"):
            line = line.strip()
            if line:
                r = json.loads(line)
                done[(r["task_id"], r["arm"])] = r.get("projection")

    def _emit(fout, goal, arm, proj, gen_ids):
        full, think, answer = _split_think_answer(gen_ids, tok, start_ids, end_ids)
        row = {
            "task_id": goal["task_id"], "category": goal.get("category", ""),
            "instruction": goal["instruction"], "arm": arm,
            # 'alpha' alias so the existing prep/curve tooling groups by arm (baseline=0, optimized=1).
            "alpha": 0.0 if arm == "baseline" else 1.0,
            "projection": round(float(proj), 4),
            "proj_success_mean": succ_mean, "proj_failure_mean": fail_mean,
            "final_text": answer, "think_text": think, "generation_text": full,
            "generation_token_count": len(gen_ids),
            "think_closed": _first_index(gen_ids, end_ids) is not None,
            "answer_present": bool(answer.strip()),
        }
        fout.write(json.dumps(row, ensure_ascii=False) + "\n"); fout.flush()

    n_done = 0
    with open(args.out, "a", encoding="utf-8") as fout:
        for goal in goals:
            tid = goal["task_id"]
            if (tid, "baseline") in done and (tid, "optimized") in done:
                continue
            formatted = model_base.format_prompts([goal["instruction"]], enable_thinking=True)[0]
            prompt_ids = tok(formatted, return_tensors="pt").input_ids[0].to(dev)
            P = prompt_ids.shape[0]
            with torch.no_grad():
                prompt_emb = emb(prompt_ids).detach()  # [P, d] (model dtype)

            # --- baseline projection + generation (no soft prefix) ---
            base_proj_val = done.get((tid, "baseline"))  # defined even when baseline was written on a prior run
            if (tid, "baseline") not in done:
                with torch.no_grad():
                    base_proj = _proj_at(prompt_emb.unsqueeze(0), P - 1)
                    base_gen = _generate(prompt_emb.unsqueeze(0))
                base_proj_val = float(base_proj.item())
                _emit(fout, goal, "baseline", base_proj_val, base_gen)
            if (tid, "optimized") in done:
                continue  # baseline done + optimized done handled above; nothing left for this goal

            # --- optimize a K-soft continuous prefix to MAXIMIZE the projection ---
            K = args.k_soft
            # init soft embeddings from the mean token embedding (in-distribution scale), fp32 + grad.
            soft = (emb.weight.detach().float().mean(0, keepdim=True)
                    .repeat(K, 1) + 0.01 * torch.randn(K, prompt_emb.shape[1], device=dev)).requires_grad_(True)
            opt = torch.optim.Adam([soft], lr=args.lr)
            read_pos = K + P - 1  # K_eff == K by construction (soft is [K,d])
            last_proj = None
            for step in range(args.steps):
                opt.zero_grad()
                inp = torch.cat([soft.to(mdtype), prompt_emb], dim=0).unsqueeze(0)  # [1, K+P, d]
                proj = _proj_at(inp, read_pos)
                loss = -proj
                loss.backward()
                opt.step()
                last_proj = float(proj.detach())
            with torch.no_grad():
                opt_inp = torch.cat([soft.detach().to(mdtype), prompt_emb], dim=0).unsqueeze(0)
                opt_gen = _generate(opt_inp)
            _emit(fout, goal, "optimized", last_proj if last_proj is not None else float("nan"), opt_gen)
            n_done += 1
            _bp = "n/a" if base_proj_val is None else f"{base_proj_val:.2f}"
            _op = "n/a" if last_proj is None else f"{last_proj:.2f}"
            print(f"  {tid}: base_proj={_bp} opt_proj={_op} "
                  f"(succ_mean={succ_mean} fail_mean={fail_mean}) opt_ans_chars={len(_split_think_answer(opt_gen, tok, start_ids, end_ids)[2])}",
                  flush=True)
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

    print(f"[phase9] wrote {n_done} optimized goals → {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
