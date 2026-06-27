"""
Exact replication of Arditi et al. (arXiv:2406.11717) refusal direction method
on Qwen3-14B, with four bugs from the prior attempt corrected.

Bugs fixed vs. `replicate_standard_refusal_direction.py`:
  Bug 1 — Single-layer ablation → all-layer ablation (3 × num_layers hooks)
  Bug 2 — KL computed with addition hooks → KL computed with all-layer ablation hooks
  Bug 3 — steer_alpha=20.0 → coeff=1.0 for steering
  Bug 4 — Pruned first 20% of layers → prunes LAST 20% of layers (as in upstream)

Execution order (per EXACT_QWEN_RD_REPLICATION_SPEC.md):
  Phase A — single target (pos=-1, layer=26)  [run first]
  Phase B — ±2 neighborhood sweep around L26  [if A fails]
  Phase C — full 4×40=160 sweep               [if B fails]

Prerequisites:
  python -m poc_stage4.validate_intervention_hooks   # must pass first

Usage:
  python -m poc_stage4.replicate_qwen_rd_exact [--phase A|B|C] [--smoke] [--output-dir PATH]

Output:
  outputs/stage4/qwen_rd_exact_replication/phase_A/selection_result.json
  outputs/stage4/qwen_rd_exact_replication/phase_A/all_candidates.json
  docs/QWEN_RD_EXACT_REPLICATION_RESULTS.md
"""
from __future__ import annotations

import argparse
import contextlib
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import torch
import torch.nn.functional as F

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_DEFAULT_OUTPUT = _REPO_ROOT / "outputs" / "stage4" / "qwen_rd_exact_replication"
_DEFAULT_MODEL = "Qwen/Qwen3-14B"
_MODEL_REVISION = "40c069824f4251a91eefaf281ebe4c544efd3e18"

# Exact Arditi parameters
_EOI_POSITIONS = [-1, -2, -3, -4]
_KL_THRESHOLD = 0.1        # test both 0.1 and 1.0
_STEER_THRESHOLD = 0.0     # steering score must be > 0
_COEFF = 1.0               # upstream: coeff = torch.tensor(1.0)
_PRUNE_LAST_PCT = 0.20     # discard last 20% of layers (NOT first 20%)
_BATCH_SIZE = 8
_MAX_NEW_TOKENS = 1

# Qwen3 refusal tokens: ['I', 'As'] — verified from qwen3_model.py:13
_REFUSAL_TOKS = [40, 2121]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


# ── Prompt loading ─────────────────────────────────────────────────────────────

def _load_prompts(n_harmful: int, n_harmless: int, seed: int = 42):
    from poc_stage4.default_prompts import load_prompt_sets
    harmful, harmless, _ = load_prompt_sets(
        num_harmful=n_harmful, num_harmless=n_harmless, seed=seed
    )
    return harmful[:n_harmful], harmless[:n_harmless]


# ── Model / tokenizer ─────────────────────────────────────────────────────────

def _load_model_and_tokenizer(model_name: str, revision: str | None):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    print(f"Loading {model_name} (revision={revision}) ...")
    tok = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    tok.padding_side = "left"
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        revision=revision,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        device_map="auto",
    ).eval()
    model.requires_grad_(False)
    return model, tok


def _tokenize(tokenizer, instructions: list[str], device: str) -> dict:
    prompts = []
    for inst in instructions:
        messages = [{"role": "user", "content": inst}]
        p = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
        )
        prompts.append(p)
    enc = tokenizer(prompts, padding=True, truncation=False, return_tensors="pt")
    return {k: v.to(device) for k, v in enc.items()}


def _get_eoi_positions(tokenizer) -> list[int]:
    """Determine the EOI token positions (-1 through -4)."""
    placeholder = "__QWEN3_EOI_PROBE__"
    messages = [{"role": "user", "content": placeholder}]
    formatted = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    suffix = formatted.split(placeholder, 1)[-1]
    eoi_ids = tokenizer.encode(suffix, add_special_tokens=False)
    return eoi_ids   # positions -len(eoi_ids) to -1 in the tokenized input


# ── Hook factories (exact Arditi implementation) ───────────────────────────────

def _ablation_pre_hook_fn(direction: torch.Tensor):
    def hook_fn(module, input):
        h = input[0] if isinstance(input, tuple) else input
        d = direction.to(h) / (direction.norm() + 1e-8)
        h = h - (h @ d).unsqueeze(-1) * d
        return (h, *input[1:]) if isinstance(input, tuple) else h
    return hook_fn


def _ablation_post_hook_fn(direction: torch.Tensor):
    def hook_fn(module, _input, output):
        h = output[0] if isinstance(output, tuple) else output
        d = direction.to(h) / (direction.norm() + 1e-8)
        h = h - (h @ d).unsqueeze(-1) * d
        return (h, *output[1:]) if isinstance(output, tuple) else h
    return hook_fn


def _addition_pre_hook_fn(direction: torch.Tensor, coeff: float = _COEFF):
    """Single-layer addition at source_layer (upstream steering evaluation)."""
    def hook_fn(module, input):
        h = input[0] if isinstance(input, tuple) else input
        d = direction.to(h) / (direction.norm() + 1e-8)
        h = h + coeff * d
        return (h, *input[1:]) if isinstance(input, tuple) else h
    return hook_fn


def _get_all_ablation_hooks(model, direction: torch.Tensor):
    """Return (fwd_pre_hooks, fwd_hooks) for all-layer direction ablation.

    Exact Arditi protocol (hook_utils.py:80-88):
      - Pre-hook on model.model.layers[l]  × num_hidden_layers   (input to block)
      - Post-hook on model.model.layers[l].self_attn × num_hidden_layers
      - Post-hook on model.model.layers[l].mlp       × num_hidden_layers
    """
    n = model.config.num_hidden_layers
    fwd_pre = [
        (model.model.layers[l], _ablation_pre_hook_fn(direction))
        for l in range(n)
    ]
    fwd_post = [
        (model.model.layers[l].self_attn, _ablation_post_hook_fn(direction))
        for l in range(n)
    ]
    fwd_post += [
        (model.model.layers[l].mlp, _ablation_post_hook_fn(direction))
        for l in range(n)
    ]
    return fwd_pre, fwd_post


@contextlib.contextmanager
def _add_hooks(pre_hooks, post_hooks):
    handles = []
    try:
        for module, fn in pre_hooks:
            handles.append(module.register_forward_pre_hook(fn))
        for module, fn in post_hooks:
            handles.append(module.register_forward_hook(fn))
        yield
    finally:
        for h in handles:
            h.remove()


# ── Scoring utilities ─────────────────────────────────────────────────────────

def _refusal_score_batch(logits: torch.Tensor, refusal_toks: list[int]) -> torch.Tensor:
    """log P(refusal) - log P(non-refusal) at last token position."""
    logits_f = logits[:, -1, :].to(torch.float64)
    probs = F.softmax(logits_f, dim=-1)
    p_ref = probs[:, refusal_toks].sum(dim=-1)
    p_nonref = 1.0 - p_ref
    eps = 1e-8
    return torch.log(p_ref + eps) - torch.log(p_nonref + eps)


def _get_refusal_scores(model, tokenizer, instructions: list[str],
                        device: str, fwd_pre=(), fwd_post=()) -> float:
    scores = []
    for i in range(0, len(instructions), _BATCH_SIZE):
        batch = instructions[i:i + _BATCH_SIZE]
        enc = _tokenize(tokenizer, batch, device)
        with _add_hooks(fwd_pre, fwd_post):
            with torch.no_grad():
                out = model(**enc)
        s = _refusal_score_batch(out.logits, _REFUSAL_TOKS)
        scores.append(s.mean().item())
    return sum(scores) / len(scores) if scores else float("nan")


def _get_last_logits(model, tokenizer, instructions: list[str],
                     device: str, fwd_pre=(), fwd_post=()):
    """Return [n_instructions, d_vocab] last-position logits."""
    all_logits = []
    for i in range(0, len(instructions), _BATCH_SIZE):
        batch = instructions[i:i + _BATCH_SIZE]
        enc = _tokenize(tokenizer, batch, device)
        with _add_hooks(fwd_pre, fwd_post):
            with torch.no_grad():
                out = model(**enc)
        all_logits.append(out.logits[:, -1, :].to(torch.float64))
    return torch.cat(all_logits, dim=0)


def _kl_div(logits_a: torch.Tensor, logits_b: torch.Tensor) -> float:
    """KL(p_a || p_b) — mean over batch."""
    eps = 1e-6
    p_a = F.softmax(logits_a.to(torch.float64), dim=-1)
    p_b = F.softmax(logits_b.to(torch.float64), dim=-1)
    kl = (p_a * (torch.log(p_a + eps) - torch.log(p_b + eps))).sum(dim=-1)
    return kl.mean().item()


# ── Direction extraction (DiM) ─────────────────────────────────────────────────

def _extract_directions(model, tokenizer, harmful: list[str], harmless: list[str],
                        device: str) -> torch.Tensor:
    """
    Compute mean_diff[position, layer, d_model] = mean_harmful - mean_harmless
    at EOI positions -1..-4 for all layers.
    Uses register_forward_pre_hook on each transformer block.
    """
    n_layers = model.config.num_hidden_layers
    d_model = model.config.hidden_size
    n_pos = len(_EOI_POSITIONS)

    def _accumulate(instructions: list[str]) -> torch.Tensor:
        cache = torch.zeros(n_pos, n_layers, d_model, dtype=torch.float64, device=device)
        n = len(instructions)

        def make_hook(layer_idx):
            def hook_fn(module, input):
                h = input[0] if isinstance(input, tuple) else input
                # h: [batch, seq_len, d_model]
                for pi, pos in enumerate(_EOI_POSITIONS):
                    cache[pi, layer_idx] += (1.0 / n) * h[:, pos, :].sum(dim=0).double()
            return hook_fn

        handles = []
        for l in range(n_layers):
            handles.append(model.model.layers[l].register_forward_pre_hook(make_hook(l)))
        try:
            for i in range(0, n, _BATCH_SIZE):
                enc = _tokenize(tokenizer, instructions[i:i + _BATCH_SIZE], device)
                with torch.no_grad():
                    model(**enc)
        finally:
            for h in handles:
                h.remove()
        return cache

    print(f"  Extracting directions from {len(harmful)} harmful ...")
    mean_harmful = _accumulate(harmful)
    print(f"  Extracting directions from {len(harmless)} harmless ...")
    mean_harmless = _accumulate(harmless)
    return (mean_harmful - mean_harmless).float()


# ── Direction selection ───────────────────────────────────────────────────────

def _evaluate_candidate(
    model, tokenizer, direction: torch.Tensor, layer: int, device: str,
    harmful_val: list[str], harmless_val: list[str],
    baseline_harmful_score: float, baseline_harmless_logits: torch.Tensor,
) -> dict:
    """Evaluate one (direction, layer) candidate per exact Arditi protocol."""
    direction = direction.to(device)

    # Bug 1+2 fix: KL and ablation refusal score both use ALL-LAYER ablation hooks
    fwd_pre, fwd_post = _get_all_ablation_hooks(model, direction)

    # Ablation refusal score on harmful (should drop if direction mediates refusal)
    ablation_score = _get_refusal_scores(
        model, tokenizer, harmful_val, device, fwd_pre=fwd_pre, fwd_post=fwd_post
    )

    # KL divergence on harmless with all-layer ablation (Bug 2 fix)
    ablated_logits = _get_last_logits(
        model, tokenizer, harmless_val, device, fwd_pre=fwd_pre, fwd_post=fwd_post
    )
    kl = _kl_div(baseline_harmless_logits, ablated_logits)

    # Steering refusal score on harmless — single-layer addition, coeff=1.0 (Bug 3 fix)
    # Only pre-hook at source_layer (as in upstream select_direction.py:222)
    addition_fn = _addition_pre_hook_fn(direction, coeff=_COEFF)
    h = model.model.layers[layer].register_forward_pre_hook(addition_fn)
    try:
        steering_score = _get_refusal_scores(model, tokenizer, harmless_val, device)
    finally:
        h.remove()

    return {
        "ablation_refusal_score": ablation_score,
        "ablation_delta": ablation_score - baseline_harmful_score,
        "steering_refusal_score": steering_score,
        "kl_div": kl,
    }


def _is_pruned(layer: int, n_layers: int) -> bool:
    # Bug 4 fix: prune LAST 20%, not first 20%
    return layer >= int(n_layers * (1.0 - _PRUNE_LAST_PCT))


def select_direction(
    model, tokenizer, directions: torch.Tensor,
    harmful_val: list[str], harmless_val: list[str],
    device: str,
    kl_threshold: float = _KL_THRESHOLD,
    target_layers: list[int] | None = None,
    phase_label: str = "A",
) -> tuple[dict | None, list[dict]]:
    """Evaluate candidate directions; return (best, all_results)."""
    n_pos, n_layers, d_model = directions.shape
    print(f"\nPhase {phase_label}: evaluating candidates "
          f"(kl_threshold={kl_threshold}, coeff={_COEFF})")

    baseline_harmful_score = _get_refusal_scores(model, tokenizer, harmful_val, device)
    baseline_harmless_logits = _get_last_logits(model, tokenizer, harmless_val, device)
    print(f"  Baseline harmful refusal score:  {baseline_harmful_score:.4f}")
    print(f"  Baseline harmless mean log-prob: (computed)")

    all_results = []
    surviving = []

    for pos_i, pos in enumerate(_EOI_POSITIONS):
        for layer in (target_layers if target_layers is not None else range(n_layers)):
            pruned = _is_pruned(layer, n_layers)
            rec = {
                "position": pos,
                "layer": layer,
                "pruned": pruned,
                "baseline_harmful_score": baseline_harmful_score,
            }
            if pruned:
                rec.update({"skip_reason": "layer_pruned", "passes": False})
                all_results.append(rec)
                continue

            direction = directions[pos_i, layer]
            print(f"  Evaluating pos={pos}, layer={layer} ...", end=" ", flush=True)
            t0 = time.time()
            scores = _evaluate_candidate(
                model, tokenizer, direction, layer, device,
                harmful_val, harmless_val,
                baseline_harmful_score, baseline_harmless_logits,
            )
            rec.update(scores)
            t1 = time.time()
            print(f"abl={scores['ablation_refusal_score']:.3f} "
                  f"steer={scores['steering_refusal_score']:.3f} "
                  f"kl={scores['kl_div']:.4f}  ({t1-t0:.1f}s)")

            passes = (
                scores["kl_div"] < kl_threshold
                and scores["steering_refusal_score"] > _STEER_THRESHOLD
            )
            rec["passes"] = passes
            all_results.append(rec)
            if passes:
                surviving.append(rec)

    best = None
    if surviving:
        # Best = lowest ablation refusal score (most effective jailbreak)
        best = min(surviving, key=lambda x: x["ablation_refusal_score"])
        print(f"\n  SELECTED: pos={best['position']}, layer={best['layer']}, "
              f"abl={best['ablation_refusal_score']:.4f}, kl={best['kl_div']:.4f}")
    else:
        print(f"\n  No survivors at kl_threshold={kl_threshold}")

    return best, all_results


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["A", "B", "C"], default="A",
                        help="A=single target L26, B=±2 neighborhood, C=full sweep")
    parser.add_argument("--model-name", default=_DEFAULT_MODEL)
    parser.add_argument("--model-revision", default=_MODEL_REVISION)
    parser.add_argument("--output-dir", type=Path, default=_DEFAULT_OUTPUT)
    parser.add_argument("--smoke", action="store_true",
                        help="Smoke: use 8 train + 4 val prompts")
    parser.add_argument("--n-train-harmful", type=int, default=128)
    parser.add_argument("--n-train-harmless", type=int, default=128)
    parser.add_argument("--n-val", type=int, default=32)
    parser.add_argument("--kl-threshold", type=float, default=_KL_THRESHOLD)
    parser.add_argument("--also-test-kl-1p0", action="store_true",
                        help="Re-run selection at kl_threshold=1.0 (Arditi paper value)")
    parser.add_argument("--target-layer", type=int, default=26,
                        help="Phase A target layer (default 26 = Qwen3-14B behavioral direction)")
    args = parser.parse_args()

    if args.smoke:
        args.n_train_harmful = 8
        args.n_train_harmless = 8
        args.n_val = 4

    out_dir = args.output_dir / f"phase_{args.phase}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load prompts
    harmful_train, harmless_train = _load_prompts(args.n_train_harmful, args.n_train_harmless)
    harmful_val, harmless_val = _load_prompts(args.n_val, args.n_val, seed=99)
    print(f"Train: {len(harmful_train)} harmful, {len(harmless_train)} harmless")
    print(f"Val:   {len(harmful_val)} harmful, {len(harmless_val)} harmless")

    # Load model
    model, tokenizer = _load_model_and_tokenizer(args.model_name, args.model_revision)
    device = next(model.parameters()).device.type

    # Phase-specific target layers
    n_layers = model.config.num_hidden_layers
    if args.phase == "A":
        target_layers = [args.target_layer]
        print(f"Phase A: single target layer {args.target_layer}")
    elif args.phase == "B":
        center = args.target_layer
        target_layers = list(range(max(0, center - 2), min(n_layers, center + 3)))
        print(f"Phase B: neighborhood sweep layers {target_layers}")
    else:
        target_layers = None  # all layers (filtered by prune rule)
        print(f"Phase C: full sweep (all {n_layers} layers, pruning last 20%)")

    # Extract directions
    print(f"\nExtracting directions ...")
    directions = _extract_directions(model, tokenizer, harmful_train, harmless_train, device)
    print(f"Directions shape: {tuple(directions.shape)}")  # (4, 40, 5120)

    # Save directions
    torch.save(directions, out_dir / "mean_diffs.pt")

    # Select direction
    best, all_results = select_direction(
        model, tokenizer, directions,
        harmful_val, harmless_val, device,
        kl_threshold=args.kl_threshold,
        target_layers=target_layers,
        phase_label=args.phase,
    )

    # Optional: also test kl_threshold=1.0
    best_relaxed = None
    all_results_relaxed = None
    if args.also_test_kl_1p0 and args.kl_threshold != 1.0:
        print(f"\nRe-running selection at kl_threshold=1.0 ...")
        best_relaxed, all_results_relaxed = select_direction(
            model, tokenizer, directions,
            harmful_val, harmless_val, device,
            kl_threshold=1.0,
            target_layers=target_layers,
            phase_label=f"{args.phase}_kl1p0",
        )

    # Write results
    result = {
        "created_utc": _utc_now(),
        "phase": args.phase,
        "model_name": args.model_name,
        "model_revision": args.model_revision,
        "n_train_harmful": len(harmful_train),
        "n_train_harmless": len(harmless_train),
        "n_val_harmful": len(harmful_val),
        "n_val_harmless": len(harmless_val),
        "kl_threshold": args.kl_threshold,
        "coeff": _COEFF,
        "prune_last_pct": _PRUNE_LAST_PCT,
        "eoi_positions": _EOI_POSITIONS,
        "target_layers": target_layers,
        "n_candidates_evaluated": len([r for r in all_results if not r.get("pruned")]),
        "n_survivors": len([r for r in all_results if r.get("passes")]),
        "best": best,
        "status": (
            "SUCCEEDED" if best is not None
            else "FAILED_NO_SURVIVORS"
        ),
        "bugs_fixed": [
            "Bug1: single-layer ablation → all-layer ablation (3×num_layers hooks)",
            "Bug2: KL with addition hooks → KL with all-layer ablation hooks",
            "Bug3: steer_alpha=20.0 → coeff=1.0",
            "Bug4: pruned first 20% of layers → prunes LAST 20% of layers",
        ],
    }
    if best_relaxed is not None:
        result["best_at_kl_1p0"] = best_relaxed
        result["n_survivors_at_kl_1p0"] = len([r for r in all_results_relaxed if r.get("passes")])

    with (out_dir / "selection_result.json").open("w") as f:
        json.dump(result, f, indent=2)
    with (out_dir / "all_candidates.json").open("w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\n=== Phase {args.phase} Result ===")
    print(f"Status: {result['status']}")
    print(f"Survivors: {result['n_survivors']} / {result['n_candidates_evaluated']}")
    if best:
        print(f"Best: pos={best['position']}, layer={best['layer']}, "
              f"abl={best['ablation_refusal_score']:.4f}, kl={best['kl_div']:.4f}")
    print(f"\nOutputs → {out_dir}")

    _write_results_doc(result, out_dir)
    sys.exit(0 if best is not None else 1)


def _write_results_doc(result: dict, out_dir: Path) -> None:
    status = result["status"]
    best = result.get("best")
    n_surv = result["n_survivors"]
    n_eval = result["n_candidates_evaluated"]

    lines = [
        f"# Qwen3 Refusal Direction Exact Replication — Phase {result['phase']}",
        f"\n**Date:** {result['created_utc'][:10]}  ",
        f"**Model:** {result['model_name']}  ",
        f"**Status:** `{status}`  ",
        f"**Survivors:** {n_surv} / {n_eval} candidates  ",
        "",
        "## Parameters",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| kl_threshold | {result['kl_threshold']} |",
        f"| steer_coeff | {result['coeff']} |",
        f"| prune_last_pct | {result['prune_last_pct']} |",
        f"| eoi_positions | {result['eoi_positions']} |",
        f"| n_train | {result['n_train_harmful']} harmful + {result['n_train_harmless']} harmless |",
        f"| n_val | {result['n_val_harmful']} + {result['n_val_harmless']} |",
        "",
        "## Result",
    ]
    if best:
        lines += [
            f"Direction found at **position={best['position']}, layer={best['layer']}**.",
            f"- Ablation refusal score: {best['ablation_refusal_score']:.4f} "
            f"(baseline: {best.get('baseline_harmful_score', '?')})",
            f"- Steering score: {best['steering_refusal_score']:.4f}",
            f"- KL divergence: {best['kl_div']:.4f} < {result['kl_threshold']}",
            "",
            "**Gate C conclusion:** REPLICATION SUCCEEDED — "
            "Arditi et al. method finds a refusal direction in Qwen3-14B.",
        ]
    else:
        lines += [
            "No candidate direction survived the selection filters.",
            "",
            "**Gate C conclusion:** REPLICATION FAILED at this phase — "
            "see EXACT_QWEN_RD_REPLICATION_SPEC.md for next steps.",
        ]

    doc_path = out_dir.parent / "QWEN_RD_EXACT_REPLICATION_RESULTS.md"
    with doc_path.open("w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Results doc → {doc_path}")


if __name__ == "__main__":
    main()
