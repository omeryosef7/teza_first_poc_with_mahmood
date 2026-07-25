"""
Stage 4 — Deterministic hidden-state replay via per-layer forward pre-hooks.

For each row in a generation shard (written by run_ae_generation.py), reconstructs
full_ids = input_token_ids + generation_token_ids, loads the model (same loader
as generation), and runs a SINGLE forward pass that captures hidden states at
ALL layers using forward pre-hooks registered on every decoder layer — adapted
from the pattern in poc_stage4/analyze_stage6_token_dynamics.py
(get_residual_projection_pre_hook / compute_projections_for_example), except
here we keep the raw hidden vector (detached, moved to CPU, cast to fp16)
rather than a scalar projection.

Layer-0 convention: register_forward_pre_hook on transformer layer i captures
the RESIDUAL STREAM INPUT to layer i, which is:
  - layer 0's hook input  == embedding output (token + position embeddings,
    pre-layer-0)               -> stored as hidden-state index 0
  - layer i's hook input  == output of layer (i-1)
                              -> stored as hidden-state index i
  - the final hidden state after the LAST layer (index n_layers) is captured
    via a forward hook (not pre-hook) on the last layer's output.
This is numerically identical (up to bf16 rounding) to the `hidden_states`
tuple returned by `model(..., output_hidden_states=True)`, which is exactly
what --verify-equivalence checks (torch.allclose, bf16 tolerance).

At each row's cached position indices (from Stage 2's `positions` dict; a
None or errored position is skipped and stored as a null placeholder — never
crashes the row), extracts the [n_layers+1, d_model] hidden vector across all
layers for that one absolute token position.

Output: per-shard fp16 tensor `[n_rows, n_positions, n_layers+1, d_model]`
saved via torch.save, plus a metadata index (row_key, position_name -> shard
path, row offset, position offset, token_id, decoded token, layer_count,
hidden_dim). Metadata index is written as parquet if pyarrow is available,
otherwise falls back to CSV (documented in docs/IMPLEMENTATION_AUDIT.md).

Resumable: row_keys already present in the shard's existing metadata index are
skipped.

Usage:
  python -m poc_stage_ae.replay_hidden_states \
      --model qwen3 --generation-shard <path to one shard jsonl> \
      --output-dir <RUN_DIR> [--verify-equivalence] [--verify-n-examples 2]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from poc_stage_ae.thinking_position_utils import position_names_for_condition

_MAX_POSITIONS = 7  # A/D schema is the superset (7 named positions); E/G use 5 of these slots + 2 null.
_ALL_POSITION_NAMES_UNION = (
    "prefill_last",
    "startofthink", "think_content_1", "think_content_2", "think_content_3", "endofthink",
    "answer_content_1", "answer_content_2", "answer_content_3",
    "endofresponse",
)


def _load_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _shard_output_paths(output_dir: Path, model: str, condition: str, goal_index: int) -> dict[str, Path]:
    base = output_dir / "hidden_states" / "shards"
    stem = f"{model}_{condition}_goal{goal_index}"
    return {
        "tensor": base / f"{stem}.pt",
        "metadata_parquet": base / f"{stem}_metadata.parquet",
        "metadata_csv": base / f"{stem}_metadata.csv",
    }


def _existing_row_keys(metadata_csv: Path, metadata_parquet: Path) -> set[str]:
    """Read whichever metadata index exists to determine already-processed row_keys."""
    if metadata_csv.exists():
        import csv as csv_mod
        keys = set()
        with open(metadata_csv, newline="", encoding="utf-8") as f:
            for row in csv_mod.DictReader(f):
                if row.get("row_key"):
                    keys.add(row["row_key"])
        return keys
    if metadata_parquet.exists():
        try:
            import pandas as pd
            df = pd.read_parquet(metadata_parquet)
            return set(df["row_key"].unique().tolist())
        except Exception:
            return set()
    return set()


def _find_final_norm_module(model: Any) -> Any:
    """Locate the base text model's final-norm submodule (Qwen3RMSNorm /
    Gemma4RMSNorm), applied after the last decoder layer and before the last
    `output_hidden_states` entry (verified against modeling_qwen3.py line 434
    and modeling_gemma4.py line 1729: `hidden_states = self.norm(hidden_states)`)."""
    for attr_path in ("model.norm", "model.language_model.norm", "language_model.model.norm", "norm"):
        obj = model
        try:
            for part in attr_path.split("."):
                obj = getattr(obj, part)
            return obj
        except AttributeError:
            continue
    raise RuntimeError(f"Unable to find final-norm module in {type(model).__name__}")


def _register_layer_hooks(model: Any, model_family: str):
    """Register forward pre-hooks on every decoder layer plus a forward hook on the
    final layer's output (raw, pre-final-norm). Returns (handles, captured, n_layers,
    norm_module) where captured[i] is a CPU fp16 tensor [seq_len, d_model] for
    hidden-state index i (0..n_layers-1); captured[n_layers] holds the RAW
    (pre-final-norm) last-layer output and must have `norm_module` applied to it
    by the caller to match HF's output_hidden_states[-1] convention — see
    _hook_capture_forward."""
    import torch

    # Locate the layers list the same way Qwen3Model.layers does.
    layers = None
    for attr_path in ("model.layers", "model.language_model.layers", "language_model.model.layers", "layers"):
        obj = model
        try:
            for part in attr_path.split("."):
                obj = getattr(obj, part)
            layers = obj
            break
        except AttributeError:
            continue
    if layers is None:
        raise RuntimeError(f"Unable to find transformer layers in {type(model).__name__}")

    norm_module = _find_final_norm_module(model)

    n_layers = len(layers)
    captured: dict[int, Any] = {}
    handles = []

    def make_pre_hook(layer_idx: int):
        def _hook(module: Any, hook_input: Any) -> None:
            act = hook_input[0] if isinstance(hook_input, tuple) else hook_input
            captured[layer_idx] = act[0].detach().to(dtype=torch.float16, device="cpu")
        return _hook

    def make_post_hook(layer_idx: int):
        def _hook(module: Any, hook_input: Any, hook_output: Any) -> None:
            out = hook_output[0] if isinstance(hook_output, tuple) else hook_output
            captured[layer_idx] = out[0].detach().to(dtype=torch.float16, device="cpu")
        return _hook

    for i in range(n_layers):
        handles.append(layers[i].register_forward_pre_hook(make_pre_hook(i)))
    # Final hidden state (index n_layers) = RAW output of the last layer; caller
    # must apply norm_module to this before treating it as HF hidden_states[-1].
    handles.append(layers[n_layers - 1].register_forward_hook(make_post_hook(n_layers)))

    return handles, captured, n_layers, norm_module


def _hook_capture_forward(model: Any, model_family: str, full_ids: list[int]) -> dict[int, Any]:
    """Run one forward pass, returning {layer_idx (0..n_layers): [seq_len, d_model] fp16 CPU tensor}.
    layer_idx == n_layers (the final entry) has the base model's final-norm module
    applied, matching HF's `output_hidden_states=True` convention exactly (verified
    by --verify-equivalence)."""
    import torch

    handles, captured, n_layers, norm_module = _register_layer_hooks(model, model_family)
    input_ids = torch.tensor(full_ids, dtype=torch.long).unsqueeze(0)
    device = next(model.parameters()).device
    try:
        with torch.inference_mode():
            model(input_ids=input_ids.to(device), use_cache=False)
            try:
                norm_dtype = next(norm_module.parameters()).dtype
            except StopIteration:
                norm_dtype = next(model.parameters()).dtype
            raw_final = captured[n_layers].to(device=device, dtype=norm_dtype)
            normed_final = norm_module(raw_final.unsqueeze(0))[0]
            captured[n_layers] = normed_final.detach().to(dtype=torch.float16, device="cpu")
    finally:
        for h in handles:
            h.remove()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return captured


def _standard_output_hidden_states(model: Any, full_ids: list[int]) -> list[Any]:
    """Reference path for --verify-equivalence: a single output_hidden_states=True call."""
    import torch
    input_ids = torch.tensor(full_ids, dtype=torch.long).unsqueeze(0)
    device = next(model.parameters()).device
    with torch.inference_mode():
        out = model(input_ids=input_ids.to(device), use_cache=False, output_hidden_states=True)
    return [hs[0].detach().to(dtype=torch.float16, device="cpu") for hs in out.hidden_states]


def _extract_position_vectors(
    captured: dict[int, Any],
    n_layers: int,
    d_model: int,
    positions: dict[str, int | None],
    position_names: tuple[str, ...],
) -> Any:
    """Build a [len(_ALL_POSITION_NAMES_UNION), n_layers+1, d_model] fp16 tensor for one row.
    Positions not in `position_names` (schema mismatch, e.g. E/G rows lack thinking
    positions) or with a None index are left as NaN placeholders."""
    import torch
    n_all_positions = len(_ALL_POSITION_NAMES_UNION)
    out = torch.full((n_all_positions, n_layers + 1, d_model), float("nan"), dtype=torch.float16)
    for slot_idx, name in enumerate(_ALL_POSITION_NAMES_UNION):
        if name not in position_names:
            continue
        pos = positions.get(name)
        if pos is None:
            continue
        for layer_idx in range(n_layers + 1):
            layer_tensor = captured.get(layer_idx)
            if layer_tensor is None or pos >= layer_tensor.shape[0]:
                continue
            out[slot_idx, layer_idx, :] = layer_tensor[pos]
    return out


def _load_replay_model(model_family: str):
    """Load (tokenizer, model, n_layers, d_model) for `model_family` once. Factored
    out so a driver can load the model a SINGLE time and replay many shards through it
    (avoids re-downloading/re-loading 15GB weights per shard — critical under the
    §31.3 node-local-cache constraint where repeated downloads thrash a small /tmp)."""
    print(f"Loading model {model_family} ...")
    from poc_stage4.qwen3_model import load_qwen3_model, load_gemma4_model
    if model_family == "gemma4":
        wrapped = load_gemma4_model(require_cuda=True)
    elif model_family == "deepseek_r1":  # Qwen2 backbone → generic wrapper; §31.3 node-local cache
        from poc_stage4.model_family_utils import DEFAULT_MODEL_BY_FAMILY
        wrapped = load_qwen3_model(model_name=DEFAULT_MODEL_BY_FAMILY["deepseek_r1"], require_cuda=True)
    elif model_family == "phi4":  # Phi3ForCausalLM (hidden 3072, 32 layers); §31.3-B offline project cache
        from poc_stage4.model_family_utils import DEFAULT_MODEL_BY_FAMILY
        wrapped = load_qwen3_model(model_name=DEFAULT_MODEL_BY_FAMILY["phi4"], require_cuda=True)
    elif model_family == "deepseek_llama":  # LlamaForCausalLM (hidden 4096, 32 layers); §31.3-B offline
        from poc_stage4.model_family_utils import DEFAULT_MODEL_BY_FAMILY
        wrapped = load_qwen3_model(model_name=DEFAULT_MODEL_BY_FAMILY["deepseek_llama"], require_cuda=True)
    else:
        wrapped = load_qwen3_model(require_cuda=True)
    n_layers = wrapped.num_layers
    d_model = wrapped.hidden_size
    print(f"Model loaded. n_layers={n_layers} d_model={d_model}")
    return wrapped.tokenizer, wrapped.model, n_layers, d_model


def replay_shard(
    *,
    model_family: str,
    generation_shard_path: Path,
    output_dir: Path,
    verify_equivalence: bool,
    verify_n_examples: int,
    recompute_positions: bool = False,
    preloaded: tuple | None = None,
) -> None:
    import torch

    rows = _load_jsonl(generation_shard_path)
    ok_rows = [r for r in rows if r.get("status") == "ok"]
    if not ok_rows:
        print(f"No successful rows in {generation_shard_path}; nothing to replay.")
        return

    condition = ok_rows[0]["condition"]
    goal_index = ok_rows[0]["goal_index"]
    paths = _shard_output_paths(output_dir, model_family, condition, goal_index)
    paths["tensor"].parent.mkdir(parents=True, exist_ok=True)

    existing_keys = _existing_row_keys(paths["metadata_csv"], paths["metadata_parquet"])
    remaining = [r for r in ok_rows if r["row_key"] not in existing_keys]
    print(f"{len(existing_keys)} row_keys already replayed; {len(remaining)} remaining of {len(ok_rows)} ok rows.")
    if not remaining and not verify_equivalence:
        print("Nothing to do.")
        return

    if preloaded is not None:
        tokenizer, model, n_layers, d_model = preloaded
    else:
        tokenizer, model, n_layers, d_model = _load_replay_model(model_family)

    # --- optional equivalence smoke check ---
    if verify_equivalence:
        print(f"--verify-equivalence: checking hook-capture vs output_hidden_states on up to {verify_n_examples} examples")
        n_checked = 0
        all_pass = True
        for row in ok_rows:
            if n_checked >= verify_n_examples:
                break
            full_ids = row["input_token_ids"] + row["generation_token_ids"]
            if len(full_ids) == 0:
                continue
            hook_captured = _hook_capture_forward(model, model_family, full_ids)
            ref_hidden_states = _standard_output_hidden_states(model, full_ids)
            if len(ref_hidden_states) != n_layers + 1:
                print(f"  WARN: output_hidden_states returned {len(ref_hidden_states)} tensors, expected {n_layers + 1}")
            row_pass = True
            # Check a few sampled positions to keep this cheap.
            check_positions = sorted(set(row.get("positions", {}).values()) - {None})[:3] or [0]
            for pos in check_positions:
                for layer_idx in range(min(n_layers + 1, len(ref_hidden_states))):
                    hook_vec = hook_captured.get(layer_idx)
                    if hook_vec is None or pos >= hook_vec.shape[0]:
                        continue
                    ref_vec = ref_hidden_states[layer_idx]
                    if pos >= ref_vec.shape[0]:
                        continue
                    close = torch.allclose(
                        hook_vec[pos].float(), ref_vec[pos].float(), rtol=1e-2, atol=1e-2
                    )
                    if not close:
                        row_pass = False
                        print(f"  MISMATCH row={row['row_key']} pos={pos} layer={layer_idx}")
            status = "PASS" if row_pass else "FAIL"
            print(f"  [{status}] row_key={row['row_key']}")
            all_pass = all_pass and row_pass
            n_checked += 1
        print(f"--verify-equivalence summary: {'PASS' if all_pass else 'FAIL'} ({n_checked} examples checked)")

    if not remaining:
        return

    all_tensors = []
    metadata_rows = []
    row_offset_start = len(existing_keys)

    for offset, row in enumerate(remaining):
        row_key = row["row_key"]
        full_ids = row["input_token_ids"] + row["generation_token_ids"]
        if not full_ids:
            print(f"SKIP {row_key}: empty full_ids")
            continue

        enable_thinking = bool(row.get("enable_thinking"))
        position_names = position_names_for_condition(enable_thinking)
        if recompute_positions:
            # Repair path: derive positions from the SAVED token IDs (same tokens →
            # same success labels) using the current (fixed) marker config. boundary =
            # number of prompt tokens = input_token_count.
            from poc_stage_ae.thinking_position_utils import locate_positions
            boundary_index = int(row.get("input_token_count") or len(row["input_token_ids"]))
            positions, _pos_errors = locate_positions(
                full_token_ids=full_ids,
                model_family=model_family,
                tokenizer=tokenizer,
                boundary_index=boundary_index,
                enable_thinking=enable_thinking,
            )
        else:
            positions = row.get("positions", {}) or {}

        try:
            captured = _hook_capture_forward(model, model_family, full_ids)
            row_tensor = _extract_position_vectors(captured, n_layers, d_model, positions, position_names)
        except Exception as exc:
            print(f"FAILED replay for {row_key}: {exc}")
            continue

        all_tensors.append(row_tensor)
        row_idx = row_offset_start + len(all_tensors) - 1
        for slot_idx, name in enumerate(_ALL_POSITION_NAMES_UNION):
            pos = positions.get(name) if name in position_names else None
            token_id = None
            token_str = None
            if pos is not None and pos < len(full_ids):
                token_id = full_ids[pos]
                try:
                    token_str = tokenizer.decode([token_id], skip_special_tokens=False)
                except Exception:
                    token_str = None
            metadata_rows.append({
                "row_key": row_key,
                "model": model_family,
                "condition": condition,
                "goal_index": goal_index,
                "seed": row.get("seed"),
                "position_name": name,
                "position_applicable": name in position_names,
                "token_index": pos,
                "token_id": token_id,
                "token_str": token_str,
                "shard_path": str(paths["tensor"]),
                "row_offset": row_idx,
                "position_offset": slot_idx,
                "layer_count": n_layers + 1,
                "hidden_dim": d_model,
            })
        print(f"Replayed {row_key} ({offset + 1}/{len(remaining)})")

    if not all_tensors:
        print("No rows successfully replayed.")
        return

    stacked = torch.stack(all_tensors, dim=0)  # [n_rows, n_positions, n_layers+1, d_model]

    if paths["tensor"].exists():
        existing_tensor = torch.load(paths["tensor"])
        stacked = torch.cat([existing_tensor, stacked], dim=0)
    torch.save(stacked, paths["tensor"])
    print(f"Saved hidden-state tensor {tuple(stacked.shape)} -> {paths['tensor']}")

    _write_metadata(metadata_rows, paths)


def _write_metadata(new_rows: list[dict], paths: dict[str, Path]) -> None:
    try:
        import pandas as pd
        df_new = pd.DataFrame(new_rows)
        if paths["metadata_parquet"].exists():
            df_existing = pd.read_parquet(paths["metadata_parquet"])
            df_out = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_out = df_new
        df_out.to_parquet(paths["metadata_parquet"], index=False)
        print(f"Wrote metadata index (parquet) -> {paths['metadata_parquet']}")
        return
    except ImportError:
        pass

    import csv as csv_mod
    write_header = not paths["metadata_csv"].exists()
    paths["metadata_csv"].parent.mkdir(parents=True, exist_ok=True)
    with open(paths["metadata_csv"], "a", newline="", encoding="utf-8") as f:
        writer = csv_mod.DictWriter(f, fieldnames=list(new_rows[0].keys()))
        if write_header:
            writer.writeheader()
        for row in new_rows:
            writer.writerow(row)
    print(f"Wrote metadata index (csv fallback, pyarrow unavailable) -> {paths['metadata_csv']}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Stage 4 — deterministic hidden-state replay.")
    p.add_argument("--model", required=True, choices=["qwen3", "gemma4", "deepseek_r1", "phi4", "deepseek_llama"])
    p.add_argument(
        "--generation-shard",
        required=True,
        type=Path,
        nargs="+",
        help="One or more generation-shard JSONLs. Multiple shards load the model ONCE "
        "and replay all of them through it (efficient + avoids §31.3 download thrash).",
    )
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--verify-equivalence", action="store_true", default=False)
    p.add_argument("--verify-n-examples", type=int, default=2)
    p.add_argument(
        "--recompute-positions",
        action="store_true",
        default=False,
        help="Recompute segmentation positions from the saved token IDs via "
        "locate_positions (boundary=input_token_count) instead of trusting the "
        "stored per-row 'positions'. Needed to repair shards generated before a "
        "marker-config fix (e.g. deepseek_r1 <think>-in-prefill). Deterministic — "
        "uses the SAME saved generation tokens, so success labels are unchanged.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    shards = args.generation_shard
    if isinstance(shards, Path):
        shards = [shards]

    # Single-shard path: preserve the original fail-loud behavior exactly — call
    # replay_shard directly (no model preload, no exception swallowing), so the
    # existing phase-5 pipeline still crashes the SLURM task on any replay error.
    if len(shards) == 1:
        replay_shard(
            model_family=args.model,
            generation_shard_path=shards[0],
            output_dir=args.output_dir,
            verify_equivalence=args.verify_equivalence,
            verify_n_examples=args.verify_n_examples,
            recompute_positions=args.recompute_positions,
        )
        return 0

    # Batch path: load the model a SINGLE time, replay each shard through it (one 15GB
    # download, not one per shard). Tolerate per-shard failures so one bad shard doesn't
    # sink the batch; exit non-zero if ANY shard failed so the caller still sees it.
    preloaded = _load_replay_model(args.model)
    n_ok = 0
    n_fail = 0
    for shard in shards:
        try:
            replay_shard(
                model_family=args.model,
                generation_shard_path=shard,
                output_dir=args.output_dir,
                verify_equivalence=args.verify_equivalence,
                verify_n_examples=args.verify_n_examples,
                recompute_positions=args.recompute_positions,
                preloaded=preloaded,
            )
            n_ok += 1
        except Exception as exc:  # keep going; one bad shard shouldn't sink the batch
            print(f"[replay] SHARD FAILED {shard}: {exc}")
            n_fail += 1
    print(f"[replay] batch done: ok={n_ok} fail={n_fail} of {len(shards)} shards")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
