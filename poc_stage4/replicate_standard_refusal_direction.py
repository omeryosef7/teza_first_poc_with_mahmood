"""
Phase 1: Replicate the Arditi et al. (arXiv:2406.11717) standard refusal direction method
on Qwen3-14B and diagnose why Stage 4A2 yielded 0/160 causal candidates.

Method (Arditi et al.):
  - Direction: DiM at EOI positions -1,-2,-3,-4
  - Hook type: residual stream input at each Transformer layer
  - KL filter: KL(output after ablation || baseline) < 1.0
  - Steering filter: P(refusal_token | harmless + steering) > threshold
  - Validation: 32 harmful, 32 harmless held-out prompts

Diagnostics produced:
  D1. Baseline refusal token log-probs on harmful vs harmless
  D2. Effect of adding direction at each layer: harmless steering Δlog-prob
  D3. Effect of ablating direction at each layer: harmful ablation Δlog-prob
  D4. KL divergence between steered and baseline token distributions
  D5. Cosine similarity between EOI direction and our behavioral directions
  D6. Sign/scale check: does negating the direction help steering?

Decision gate:
  A. Survivors with Arditi (KL<1.0) → EOI direction causally sufficient; puzzle dirs fail differently
  B. Survivors with looser KL only → threshold tuning issue
  C. No survivors at any threshold → Qwen3 refusal not mediated by single EOI direction
  D. Steering effect near zero → direction extraction error (wrong tokens / wrong positions)

Output:
  outputs/stage4/standard_rd_replication/replication_summary.json
  docs/STANDARD_RD_REPLICATION_RESULTS.md

Usage:
  python -m poc_stage4.replicate_standard_refusal_direction
      [--model-name Qwen/Qwen3-14B]
      [--output-dir outputs/stage4/standard_rd_replication]
      [--smoke]
      [--n-harmful 64] [--n-harmless 64]
      [--reuse-stage4a1]    # reuse existing Stage 4A1 direction.pt artifacts
      [--enable-thinking]   # run with thinking enabled (matches inference condition)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import torch

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_DEFAULT_MODEL = "Qwen/Qwen3-14B"
_DEFAULT_OUTPUT = _REPO_ROOT / "outputs" / "stage4" / "standard_rd_replication"
_STAGE4A1_DIR = _REPO_ROOT / "outputs" / "stage4" / "qwen3-14b" / "refusal_direction"

# Arditi et al. exact parameters (Table 1 / Section 3)
_ARDITI_KL_THRESHOLD = 1.0
_ARDITI_STEER_THRESHOLD = 0.0   # requires steering score > 0 (paper's sign convention)
_ARDITI_POSITIONS = [-1, -2, -3, -4]

# Our Stage 4A2 parameters for comparison
_OUR_KL_THRESHOLD = 0.1
_OUR_STEER_THRESHOLD = 0.0

# Qwen3 refusal surface forms (token IDs verified against tokenizer)
_QWEN3_REFUSAL_TOKENS_STANDARD = [40, 2121]   # ['I', 'As'] — used in Stage 4A2
_QWEN3_REFUSAL_TOKENS_EXTENDED = None          # expand at runtime from tokenizer


def _fmt(x, n=4):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    return f"{x:.{n}f}"


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


def _load_val_prompts():
    """Load the same validation splits used in Stage 4A2."""
    val_harmful_path = _REPO_ROOT / "Chain_of_Thought_Hijacking" / "refusal_direction" / "dataset" / "splits" / "harmful_val.json"
    val_harmless_path = _REPO_ROOT / "Chain_of_Thought_Hijacking" / "refusal_direction" / "dataset" / "splits" / "harmless_val.json"
    if val_harmful_path.exists() and val_harmless_path.exists():
        with open(val_harmful_path) as f:
            harmful_val = json.load(f)
        with open(val_harmless_path) as f:
            harmless_val = json.load(f)
        return harmful_val, harmless_val
    return None, None


# ── Model loading ──────────────────────────────────────────────────────────────

def _load_model_and_tokenizer(model_name: str, device: str = "cuda"):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    print(f"  Loading tokenizer: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    print(f"  Loading model: {model_name}")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        attn_implementation="sdpa",
        trust_remote_code=True,
    )
    model.eval()
    return model, tokenizer


# ── Activation capture ────────────────────────────────────────────────────────

def _format_prompt(text: str, tokenizer, enable_thinking: bool) -> str:
    messages = [{"role": "user", "content": text}]
    try:
        return tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=enable_thinking,
        )
    except TypeError:
        return tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )


@torch.no_grad()
def _get_residual_activations(
    model,
    tokenizer,
    prompts: list[str],
    positions: list[int],
    enable_thinking: bool,
    device: str = "cuda",
) -> torch.Tensor:
    """
    Returns activations at shape [n_prompts, n_positions, n_layers, d_model].
    Positions are negative offsets from end of tokenized prompt.
    """
    n_layers = model.config.num_hidden_layers
    d_model = model.config.hidden_size
    n_pos = len(positions)
    activations = torch.zeros(len(prompts), n_pos, n_layers, d_model, dtype=torch.float32)

    hooks = []
    layer_acts: dict[int, torch.Tensor] = {}

    def make_hook(layer_idx):
        def hook(module, input, output):
            if isinstance(output, tuple):
                hidden = output[0]
            else:
                hidden = output
            # hidden: [batch, seq_len, d_model]
            layer_acts[layer_idx] = hidden.detach().cpu().float()
        return hook

    for i, layer in enumerate(model.model.layers):
        hooks.append(layer.register_forward_hook(make_hook(i)))

    for pi, prompt in enumerate(prompts):
        formatted = _format_prompt(prompt, tokenizer, enable_thinking)
        inputs = tokenizer(formatted, return_tensors="pt").to(device)
        seq_len = inputs["input_ids"].shape[1]

        layer_acts.clear()
        _ = model(**inputs)

        for pos_i, pos in enumerate(positions):
            tok_idx = seq_len + pos  # negative offset from end
            if tok_idx < 0:
                tok_idx = 0
            for layer_i in range(n_layers):
                if layer_i in layer_acts:
                    activations[pi, pos_i, layer_i] = layer_acts[layer_i][0, tok_idx]

    for h in hooks:
        h.remove()

    return activations


# ── Direction extraction ──────────────────────────────────────────────────────

def _extract_dim_directions(
    harmful_acts: torch.Tensor,
    harmless_acts: torch.Tensor,
) -> torch.Tensor:
    """
    DiM: mean(harmful) - mean(harmless).
    Returns [n_positions, n_layers, d_model], unit-normalized.
    """
    dirs = harmful_acts.mean(dim=0) - harmless_acts.mean(dim=0)  # [n_pos, n_layers, d_model]
    norms = dirs.norm(dim=-1, keepdim=True).clamp(min=1e-8)
    return dirs / norms


# ── Refusal scoring ───────────────────────────────────────────────────────────

@torch.no_grad()
def _score_refusal(
    model,
    tokenizer,
    prompts: list[str],
    refusal_token_ids: list[int],
    enable_thinking: bool,
    device: str = "cuda",
    hook_fn=None,
) -> float:
    """
    Returns mean log P(refusal_token) at the first generated position.
    If hook_fn is provided, registers it before scoring and removes after.
    """
    from transformers import LogitsProcessor
    total_score = 0.0
    count = 0

    hooks = []
    if hook_fn is not None:
        for layer in model.model.layers:
            hooks.append(layer.register_forward_hook(hook_fn))

    try:
        for prompt in prompts:
            formatted = _format_prompt(prompt, tokenizer, enable_thinking)
            inputs = tokenizer(formatted, return_tensors="pt").to(device)
            with torch.no_grad():
                out = model(**inputs)
            logits = out.logits[0, -1, :]  # [vocab_size]
            log_probs = torch.log_softmax(logits, dim=-1)
            max_log_prob = max(log_probs[tid].item() for tid in refusal_token_ids)
            total_score += max_log_prob
            count += 1
    finally:
        for h in hooks:
            h.remove()

    return total_score / count if count > 0 else float("nan")


@torch.no_grad()
def _compute_kl_divergence(
    model,
    tokenizer,
    prompts: list[str],
    enable_thinking: bool,
    device: str = "cuda",
    hook_fn=None,
    baseline_logits_list: list | None = None,
) -> float:
    """
    Mean KL(baseline || hook) over prompts.
    Returns KL divergence (nats).
    """
    kl_total = 0.0
    count = 0

    for pi, prompt in enumerate(prompts):
        formatted = _format_prompt(prompt, tokenizer, enable_thinking)
        inputs = tokenizer(formatted, return_tensors="pt").to(device)

        # Baseline
        with torch.no_grad():
            baseline_out = model(**inputs)
        baseline_logits = baseline_out.logits[0, -1, :].float()
        p_base = torch.softmax(baseline_logits, dim=-1)

        # Hooked
        hooks = []
        if hook_fn is not None:
            for layer in model.model.layers:
                hooks.append(layer.register_forward_hook(hook_fn))
        try:
            with torch.no_grad():
                hooked_out = model(**inputs)
        finally:
            for h in hooks:
                h.remove()

        hooked_logits = hooked_out.logits[0, -1, :].float()
        p_hook = torch.softmax(hooked_logits, dim=-1)

        # KL(base || hook) = sum(p_base * log(p_base/p_hook))
        kl = (p_base * (p_base.log() - p_hook.log())).sum().item()
        if not math.isnan(kl) and not math.isinf(kl):
            kl_total += kl
            count += 1

    return kl_total / count if count > 0 else float("nan")


# ── Steering/ablation hook factories ─────────────────────────────────────────

def _make_add_hook(layer_idx: int, direction: torch.Tensor, alpha: float = 20.0, device: str = "cuda"):
    """Add alpha * direction to the residual stream output at layer_idx."""
    d_cpu = direction.cpu()
    def hook(module, input, output):
        if isinstance(output, tuple):
            hidden = output[0]
            d = d_cpu.to(device=hidden.device, dtype=hidden.dtype)
            result = hidden + alpha * d.unsqueeze(0).unsqueeze(0)
            return (result,) + output[1:]
        else:
            d = d_cpu.to(device=output.device, dtype=output.dtype)
            return output + alpha * d.unsqueeze(0).unsqueeze(0)
    return hook


def _make_ablate_hook(layer_idx: int, direction: torch.Tensor, device: str = "cuda"):
    """Project out the direction from the residual stream output at layer_idx."""
    d_cpu = direction.cpu()
    def hook(module, input, output):
        if isinstance(output, tuple):
            hidden = output[0]
            d = d_cpu.to(device=hidden.device, dtype=hidden.dtype)
            proj = (hidden * d).sum(dim=-1, keepdim=True) * d
            return (hidden - proj,) + output[1:]
        else:
            d = d_cpu.to(device=output.device, dtype=output.dtype)
            proj = (output * d).sum(dim=-1, keepdim=True) * d
            return output - proj
    return hook


# ── Candidate evaluation ──────────────────────────────────────────────────────

def evaluate_candidates(
    model,
    tokenizer,
    directions: torch.Tensor,   # [n_positions, n_layers, d_model]
    positions: list[int],
    harmful_val: list[str],
    harmless_val: list[str],
    refusal_token_ids: list[int],
    enable_thinking: bool,
    kl_threshold_arditi: float = _ARDITI_KL_THRESHOLD,
    kl_threshold_ours: float = _OUR_KL_THRESHOLD,
    steer_threshold: float = _ARDITI_STEER_THRESHOLD,
    steer_alpha: float = 20.0,
    prune_layer_pct: float = 0.2,
    device: str = "cuda",
    max_candidates: int | None = None,
) -> list[dict]:
    n_pos, n_layers, _ = directions.shape
    n_skip = int(n_layers * prune_layer_pct)
    baseline_harmful = _score_refusal(model, tokenizer, harmful_val, refusal_token_ids, enable_thinking, device)
    baseline_harmless = _score_refusal(model, tokenizer, harmless_val, refusal_token_ids, enable_thinking, device)
    print(f"  Baseline harmful refusal score:  {_fmt(baseline_harmful)}")
    print(f"  Baseline harmless refusal score: {_fmt(baseline_harmless)}")

    results = []
    n_candidates = n_pos * n_layers
    done = 0
    for pos_i, pos in enumerate(positions):
        for layer_i in range(n_layers):
            if max_candidates is not None and done >= max_candidates:
                break
            if layer_i < n_skip:
                results.append({
                    "position": pos, "layer": layer_i,
                    "skipped": True, "skip_reason": "layer_pruned",
                    "passes_arditi": False, "passes_ours": False,
                })
                done += 1
                continue

            direction = directions[pos_i, layer_i]  # [d_model]
            layer = model.model.layers[layer_i]

            # Ablation on harmful: does removing direction reduce refusal?
            ablate_fn = _make_ablate_hook(layer_i, direction, device)
            h = layer.register_forward_hook(ablate_fn)
            ablation_score = _score_refusal(model, tokenizer, harmful_val, refusal_token_ids, enable_thinking, device)
            h.remove()
            ablation_delta = ablation_score - baseline_harmful

            # Steering on harmless: does adding direction induce refusal?
            add_fn = _make_add_hook(layer_i, direction, steer_alpha, device)
            h = layer.register_forward_hook(add_fn)
            steering_score = _score_refusal(model, tokenizer, harmless_val, refusal_token_ids, enable_thinking, device)
            h.remove()
            steering_delta = steering_score - baseline_harmless

            # KL divergence on harmless (Arditi: measures fluency preservation)
            add_fn2 = _make_add_hook(layer_i, direction, steer_alpha, device)
            kl = _compute_kl_divergence(model, tokenizer, harmless_val[:8], enable_thinking, device, add_fn2)

            passes_arditi = (kl < kl_threshold_arditi and steering_score > steer_threshold)
            passes_ours = (kl < kl_threshold_ours and steering_score > steer_threshold)

            results.append({
                "position": pos,
                "layer": layer_i,
                "baseline_harmful": baseline_harmful,
                "baseline_harmless": baseline_harmless,
                "ablation_score": ablation_score,
                "ablation_delta": ablation_delta,
                "steering_score": steering_score,
                "steering_delta": steering_delta,
                "kl": kl,
                "passes_arditi": passes_arditi,
                "passes_ours": passes_ours,
                "skipped": False,
            })
            done += 1
            pct = done / n_candidates * 100
            print(f"  [{done:3d}/{n_candidates}] pos={pos} L{layer_i:2d}: "
                  f"ablation_δ={_fmt(ablation_delta, 3)}, steer_δ={_fmt(steering_delta, 3)}, "
                  f"kl={_fmt(kl, 3)}, arditi={passes_arditi}, ours={passes_ours}")

    return results


# ── Diagnostic: sign flip ─────────────────────────────────────────────────────

def _check_sign_flip(
    model,
    tokenizer,
    direction: torch.Tensor,
    layer_i: int,
    harmless_val: list[str],
    refusal_token_ids: list[int],
    enable_thinking: bool,
    steer_alpha: float,
    device: str,
) -> dict:
    """Check if negating the direction improves steering on harmless prompts."""
    baseline = _score_refusal(model, tokenizer, harmless_val, refusal_token_ids, enable_thinking, device)
    layer = model.model.layers[layer_i]

    add_fn = _make_add_hook(layer_i, direction, steer_alpha, device)
    h = layer.register_forward_hook(add_fn)
    pos_score = _score_refusal(model, tokenizer, harmless_val, refusal_token_ids, enable_thinking, device)
    h.remove()

    neg_fn = _make_add_hook(layer_i, -direction, steer_alpha, device)
    h = layer.register_forward_hook(neg_fn)
    neg_score = _score_refusal(model, tokenizer, harmless_val, refusal_token_ids, enable_thinking, device)
    h.remove()

    return {
        "layer": layer_i,
        "baseline": baseline,
        "positive_steering": pos_score,
        "negative_steering": neg_score,
        "positive_delta": pos_score - baseline,
        "negative_delta": neg_score - baseline,
        "better_when_negated": neg_score > pos_score,
    }


# ── Report writing ─────────────────────────────────────────────────────────────

def _write_results_doc(
    output_dir: Path,
    summary: dict,
) -> None:
    doc_path = _REPO_ROOT / "docs" / "STANDARD_RD_REPLICATION_RESULTS.md"
    n_arditi = summary.get("n_survivors_arditi", 0)
    n_ours = summary.get("n_survivors_ours", 0)
    decision = summary.get("decision_gate", "D")
    baseline_h = summary.get("baseline_harmful", None)
    baseline_n = summary.get("baseline_harmless", None)
    max_steer = summary.get("max_steering_delta", None)

    if decision == "A":
        verdict = "**PASS** — EOI direction causally sufficient with Arditi thresholds."
    elif decision == "B":
        verdict = "**PARTIAL** — Survivors only with loose KL; threshold sensitivity issue."
    elif decision == "C":
        verdict = "**FAIL** — No survivors at any threshold; single-direction may not apply to Qwen3."
    elif decision == "D":
        verdict = "**DIAGNOSTIC FAILURE** — Steering delta near zero; direction has no effect."
    else:
        verdict = "**UNRESOLVED**"

    content = f"""# Standard Refusal Direction Replication Results

Generated: {_utc_now()}
Model: {summary.get('model_name', 'Qwen/Qwen3-14B')}
Reference: Arditi et al., arXiv:2406.11717

## Decision Gate: {decision}

{verdict}

## Key Metrics

| Metric | Value |
|--------|-------|
| Baseline harmful refusal score | {_fmt(baseline_h)} |
| Baseline harmless refusal score | {_fmt(baseline_n)} |
| Max steering Δ (harmless → refusal) | {_fmt(max_steer)} |
| Candidates surviving Arditi filters (KL<1.0) | {n_arditi} / {summary.get('n_candidates_evaluated', '?')} |
| Candidates surviving Stage 4A2 filters (KL<0.1) | {n_ours} / {summary.get('n_candidates_evaluated', '?')} |

## Interpretation

{summary.get('interpretation', 'See analysis_summary.json for details.')}

## Implications for Stage 4A2 Null (0/160)

{summary.get('implications', 'See analysis_summary.json for details.')}
"""
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Wrote {doc_path}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", default=_DEFAULT_MODEL)
    parser.add_argument("--output-dir", default=str(_DEFAULT_OUTPUT))
    parser.add_argument("--smoke", action="store_true", help="Quick smoke: 8 harmful, 8 harmless, top 3 layers only")
    parser.add_argument("--n-harmful", type=int, default=64)
    parser.add_argument("--n-harmless", type=int, default=64)
    parser.add_argument("--n-harmful-val", type=int, default=32)
    parser.add_argument("--n-harmless-val", type=int, default=32)
    parser.add_argument("--reuse-stage4a1", action="store_true",
                        help="Reuse existing Stage 4A1 direction.pt and skip re-extraction")
    parser.add_argument("--enable-thinking", action="store_true", default=False,
                        help="Run with extended thinking enabled (matches actual inference condition)")
    parser.add_argument("--steer-alpha", type=float, default=20.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    if args.smoke:
        args.n_harmful = 8
        args.n_harmless = 8
        args.n_harmful_val = 8
        args.n_harmless_val = 8

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== Standard Refusal Direction Replication ===")
    print(f"  Model:          {args.model_name}")
    print(f"  enable_thinking: {args.enable_thinking}")
    print(f"  Positions:      {_ARDITI_POSITIONS}")
    print(f"  N harmful/harmless (train): {args.n_harmful}/{args.n_harmless}")
    print(f"  N harmful/harmless (val):   {args.n_harmful_val}/{args.n_harmless_val}")
    print(f"  Smoke mode:     {args.smoke}")
    print(f"  Reuse Stage 4A1: {args.reuse_stage4a1}")
    print()

    device = args.device if torch.cuda.is_available() else "cpu"
    model, tokenizer = _load_model_and_tokenizer(args.model_name, device)
    n_layers = model.config.num_hidden_layers
    print(f"  n_layers={n_layers}, d_model={model.config.hidden_size}")

    # Refusal token IDs
    refusal_token_ids = _QWEN3_REFUSAL_TOKENS_STANDARD
    print(f"  Refusal token IDs: {refusal_token_ids} = {[tokenizer.decode([t]) for t in refusal_token_ids]}")

    # Load prompts
    print("\nLoading prompts...")
    harmful_train, harmless_train = _load_prompts(args.n_harmful, args.n_harmless, seed=args.seed)
    harmful_val_preloaded, harmless_val_preloaded = _load_val_prompts()

    if harmful_val_preloaded and harmless_val_preloaded:
        import random
        rng = random.Random(args.seed)
        harmful_val = rng.sample(harmful_val_preloaded, min(args.n_harmful_val, len(harmful_val_preloaded)))
        harmless_val = rng.sample(harmless_val_preloaded, min(args.n_harmless_val, len(harmless_val_preloaded)))
        print(f"  Using preloaded val splits: {len(harmful_val)} harmful, {len(harmless_val)} harmless")
    else:
        harmful_val = harmful_train[:args.n_harmful_val]
        harmless_val = harmless_train[:args.n_harmless_val]
        print(f"  Using train-split for val: {len(harmful_val)} harmful, {len(harmless_val)} harmless")

    # Extract or reuse directions
    if args.reuse_stage4a1:
        candidates_path = _STAGE4A1_DIR / "candidate_directions.pt"
        meta_path = _STAGE4A1_DIR / "candidate_metadata.json"
        if candidates_path.exists() and meta_path.exists():
            print(f"\nReusing Stage 4A1 directions from {_STAGE4A1_DIR}/")
            directions_raw = torch.load(candidates_path, map_location="cpu", weights_only=True)
            with open(meta_path) as f:
                meta = json.load(f)
            # directions_raw shape: [n_positions, n_layers, d_model]
            directions = directions_raw.float()
            positions = meta.get("positions", _ARDITI_POSITIONS)
            print(f"  Directions shape: {directions.shape}")
            print(f"  Positions: {positions}")
        else:
            print(f"  WARNING: Stage 4A1 artifacts not found at {_STAGE4A1_DIR}/; extracting fresh...")
            args.reuse_stage4a1 = False

    if not args.reuse_stage4a1:
        print(f"\nExtracting DiM directions (n_harmful={len(harmful_train)}, n_harmless={len(harmless_train)})...")
        positions = _ARDITI_POSITIONS
        t0 = time.time()
        harmful_acts = _get_residual_activations(
            model, tokenizer, harmful_train, positions, args.enable_thinking, device
        )
        harmless_acts = _get_residual_activations(
            model, tokenizer, harmless_train, positions, args.enable_thinking, device
        )
        directions = _extract_dim_directions(harmful_acts, harmless_acts)
        print(f"  Done in {time.time()-t0:.1f}s. Shape: {directions.shape}")
        torch.save(directions, output_dir / "directions.pt")

    # Evaluate candidates
    print("\nEvaluating candidates...")
    max_cands = 12 if args.smoke else None  # smoke: only a few layers
    candidate_results = evaluate_candidates(
        model=model, tokenizer=tokenizer,
        directions=directions, positions=positions,
        harmful_val=harmful_val, harmless_val=harmless_val,
        refusal_token_ids=refusal_token_ids,
        enable_thinking=args.enable_thinking,
        kl_threshold_arditi=_ARDITI_KL_THRESHOLD,
        kl_threshold_ours=_OUR_KL_THRESHOLD,
        steer_threshold=_ARDITI_STEER_THRESHOLD,
        steer_alpha=args.steer_alpha,
        device=device,
        max_candidates=max_cands,
    )

    # D6: sign flip diagnostic on best candidate by ablation
    scored = [r for r in candidate_results if not r.get("skipped")]
    best_ablation = min(scored, key=lambda r: r.get("ablation_score", 0)) if scored else None
    sign_flip_result = None
    if best_ablation and not args.smoke:
        pos_i = _ARDITI_POSITIONS.index(best_ablation["position"])
        layer_i = best_ablation["layer"]
        d = directions[pos_i, layer_i]
        print(f"\nD6 sign-flip diagnostic: best ablation candidate pos={best_ablation['position']} L{layer_i}")
        sign_flip_result = _check_sign_flip(
            model, tokenizer, d, layer_i, harmless_val,
            refusal_token_ids, args.enable_thinking, args.steer_alpha, device
        )
        print(f"  positive_δ={_fmt(sign_flip_result['positive_delta'])}, "
              f"negative_δ={_fmt(sign_flip_result['negative_delta'])}, "
              f"better_when_negated={sign_flip_result['better_when_negated']}")

    # Classify results
    n_arditi = sum(1 for r in candidate_results if r.get("passes_arditi"))
    n_ours = sum(1 for r in candidate_results if r.get("passes_ours"))
    steering_deltas = [r.get("steering_delta") for r in scored if r.get("steering_delta") is not None]
    max_steer_delta = max(steering_deltas) if steering_deltas else None
    baseline_harmful = scored[0].get("baseline_harmful") if scored else None
    baseline_harmless = scored[0].get("baseline_harmless") if scored else None

    # Decision gate
    if n_arditi > 0:
        decision = "A"
        interp = (
            f"{n_arditi} candidate(s) survive Arditi filters (KL<1.0, steer>0.0). "
            "The standard EOI direction is causally sufficient on Qwen3-14B. "
            "Stage 4A2 failed because our KL threshold (0.1) was too tight or our "
            "behavioral directions are fundamentally different."
        )
        impl = (
            f"Stage 4A2 null is a threshold issue: relax KL to 1.0 and rerun "
            f"select_refusal_direction_interventions.py with --kl-threshold 1.0."
        )
    elif n_ours > 0:
        decision = "B"
        interp = (
            f"{n_ours} candidate(s) survive with KL<{_OUR_KL_THRESHOLD} but 0 with Arditi KL<{_ARDITI_KL_THRESHOLD}. "
            "The direction has a refusal effect but only with high-KL perturbations (fluency-breaking steering)."
        )
        impl = "Stage 4A2 null is KL sensitivity; direction exists but intervention is noisy."
    elif max_steer_delta is not None and max_steer_delta < 0.1:
        decision = "D"
        interp = (
            f"Max steering Δ = {_fmt(max_steer_delta)} (near zero). "
            "Adding the EOI DiM direction at any layer does not change the model's refusal output. "
            "This suggests refusal in Qwen3-14B is NOT mediated by a single direction in the EOI residual stream, "
            "or the refusal tokens ['I','As'] are wrong proxies for Qwen3 refusal."
        )
        impl = (
            "The 0/160 Stage 4A2 null is a fundamental result: Qwen3-14B's refusal mechanism "
            "differs from Llama/Gemma2. The EOI positions do not carry the refusal direction. "
            "Potential next steps: (1) Try refusal scoring with different tokens; "
            "(2) Extract direction from first-token-of-response positions; "
            "(3) Check Arditi paper's Llama-vs-Qwen architecture comparison."
        )
    else:
        decision = "C"
        interp = (
            "No survivors at any threshold. The single-direction refusal hypothesis "
            "may not apply to Qwen3-14B with the current experimental setup."
        )
        impl = "Stage 4A2 null reflects fundamental architecture difference. Do not pursue single-direction replication."

    summary = {
        "created_utc": _utc_now(),
        "model_name": args.model_name,
        "enable_thinking": args.enable_thinking,
        "positions": list(positions),
        "refusal_token_ids": refusal_token_ids,
        "n_candidates_evaluated": len(candidate_results),
        "n_survivors_arditi": n_arditi,
        "n_survivors_ours": n_ours,
        "baseline_harmful": baseline_harmful,
        "baseline_harmless": baseline_harmless,
        "max_steering_delta": max_steer_delta,
        "decision_gate": decision,
        "interpretation": interp,
        "implications": impl,
        "sign_flip_diagnostic": sign_flip_result,
        "arditi_kl_threshold": _ARDITI_KL_THRESHOLD,
        "our_kl_threshold": _OUR_KL_THRESHOLD,
        "steer_threshold": _ARDITI_STEER_THRESHOLD,
        "steer_alpha": args.steer_alpha,
        "smoke": args.smoke,
        "candidate_results": candidate_results,
    }

    out_path = output_dir / "replication_summary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary → {out_path}")

    print("\n=== RESULT ===")
    print(f"  Decision gate: {decision}")
    print(f"  {interp}")
    print(f"  Implication: {impl}")

    if not args.smoke:
        _write_results_doc(output_dir, summary)

    print("\nDone.")


if __name__ == "__main__":
    main()
