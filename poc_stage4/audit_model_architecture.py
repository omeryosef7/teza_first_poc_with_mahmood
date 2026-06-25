"""
Phase 0: Extract and record model architecture facts for Qwen3-14B and Gemma4-E4B-IT.

In fast mode (--from-artifacts, default): reads from existing Stage 4 extraction_metrics.json
files without loading the model. This runs in <1s on CPU.

In full mode (--load-model): loads the model to get authoritative facts including
EOS token IDs and thinking token IDs. Requires GPU.

Outputs:
  outputs/audits/model_architecture_audit.json
  docs/MODEL_ARCHITECTURE_AUDIT.md

Usage (fast, no GPU):
  python -m poc_stage4.audit_model_architecture

Usage (full, GPU required):
  python -m poc_stage4.audit_model_architecture --load-model --model qwen3
  python -m poc_stage4.audit_model_architecture --load-model --model gemma4
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

_OUTPUT_DIR = _REPO_ROOT / "outputs" / "audits"
_DOCS_DIR = _REPO_ROOT / "docs"


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


def _read_from_artifacts() -> dict:
    """
    Read architecture facts from existing Stage 4 extraction_metrics.json files.
    No model loading required.
    """
    facts = {}

    # Qwen3-14B
    qwen_metrics = _REPO_ROOT / "outputs" / "stage4" / "qwen3-14b" / "refusal_direction" / "extraction_metrics.json"
    if qwen_metrics.exists():
        with open(qwen_metrics) as f:
            m = json.load(f)
        facts["qwen3-14b"] = {
            "model_name": m.get("model_name", "Qwen/Qwen3-14B"),
            "num_hidden_layers": m.get("num_layers", 40),
            "hidden_size": m.get("hidden_size", 5120),
            "candidate_tensor_shape": m.get("candidate_tensor_shape"),
            "source": str(qwen_metrics),
            "source_type": "extraction_metrics",
        }
    else:
        facts["qwen3-14b"] = {
            "model_name": "Qwen/Qwen3-14B",
            "num_hidden_layers": 40,
            "hidden_size": 5120,
            "source": "hardcoded (extraction_metrics.json not found)",
            "source_type": "hardcoded",
        }

    # Gemma4-E4B-IT — use behavioral variant (most complete)
    gemma_metrics = _REPO_ROOT / "outputs" / "stage4" / "gemma4-e4b-it" / "refusal_direction_behavioral" / "extraction_metrics.json"
    if gemma_metrics.exists():
        with open(gemma_metrics) as f:
            m = json.load(f)
        facts["gemma4-e4b-it"] = {
            "model_name": m.get("model_name", "google/gemma-4-E4B-it"),
            "num_hidden_layers": m.get("num_layers", 42),
            "hidden_size": m.get("hidden_size", 2560),
            "candidate_tensor_shape": m.get("candidate_tensor_shape"),
            "source": str(gemma_metrics),
            "source_type": "extraction_metrics",
        }
    else:
        facts["gemma4-e4b-it"] = {
            "model_name": "google/gemma-4-E4B-it",
            "num_hidden_layers": 42,
            "hidden_size": 2560,
            "source": "hardcoded (extraction_metrics.json not found)",
            "source_type": "hardcoded",
        }

    # Thinking markers (from model_family_utils.py, no GPU needed)
    try:
        from poc_stage4.model_family_utils import THINKING_MARKERS_BY_FAMILY
        for key, model_family in [("qwen3-14b", "qwen3"), ("gemma4-e4b-it", "gemma4")]:
            markers = THINKING_MARKERS_BY_FAMILY.get(model_family, {})
            facts[key]["thinking_start_marker"] = markers.get("start")
            facts[key]["thinking_end_marker"] = markers.get("end")
    except ImportError:
        pass

    return facts


def _load_from_model(model_family: str) -> dict:
    """Load the actual model and extract authoritative architecture facts."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model_names = {
        "qwen3": "Qwen/Qwen3-14B",
        "gemma4": "google/gemma-4-E4B-it",
    }
    key_names = {
        "qwen3": "qwen3-14b",
        "gemma4": "gemma4-e4b-it",
    }
    model_name = model_names[model_family]
    key = key_names[model_family]

    print(f"  Loading tokenizer: {model_name}")
    tok = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

    # EOS token IDs (full list)
    eos_ids = tok.eos_token_id
    if isinstance(eos_ids, int):
        eos_ids = [eos_ids]

    print(f"  Loading model: {model_name}")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )

    # EOS from generation_config (may be different from tokenizer eos)
    gen_config = getattr(model, "generation_config", None)
    gen_eos = getattr(gen_config, "eos_token_id", None) if gen_config else None
    if gen_eos is not None:
        if isinstance(gen_eos, int):
            gen_eos = [gen_eos]

    # Thinking token IDs
    thinking_tokens = {}
    try:
        from poc_stage4.model_family_utils import THINKING_MARKERS_BY_FAMILY
        markers = THINKING_MARKERS_BY_FAMILY.get(model_family, {})
        for marker_name, marker_text in [("start", markers.get("start")), ("end", markers.get("end"))]:
            if marker_text:
                ids = tok.encode(marker_text, add_special_tokens=False)
                thinking_tokens[marker_name] = {"text": marker_text, "token_ids": ids}
    except ImportError:
        pass

    cfg = model.config
    facts = {
        model_family: {
            "model_name": model_name,
            "num_hidden_layers": cfg.num_hidden_layers,
            "hidden_size": cfg.hidden_size,
            "num_attention_heads": getattr(cfg, "num_attention_heads", None),
            "num_key_value_heads": getattr(cfg, "num_key_value_heads", None),
            "vocab_size": cfg.vocab_size,
            "model_class": type(model).__name__,
            "tokenizer_class": type(tok).__name__,
            "eos_token_ids_tokenizer": list(eos_ids) if eos_ids else None,
            "eos_token_ids_generation_config": list(gen_eos) if gen_eos else None,
            "eos_tokens_decoded": [tok.decode([i]) for i in (gen_eos or eos_ids or [])],
            "thinking_markers": thinking_tokens,
            "source": f"loaded from {model_name}",
            "source_type": "model_load",
        }
    }

    del model
    import gc
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return {key_names[model_family]: facts[model_family]}


def _write_docs(facts: dict, output_dir: Path) -> None:
    doc_path = _DOCS_DIR / "MODEL_ARCHITECTURE_AUDIT.md"
    _DOCS_DIR.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Model Architecture Audit",
        "",
        f"Generated: {_utc_now()}",
        "Source: `poc_stage4/audit_model_architecture.py`",
        "",
        "## Summary",
        "",
        "| Model | Layers | d_model | Thinking start | Thinking end |",
        "|-------|--------|---------|----------------|--------------|",
    ]
    for key, f in sorted(facts.items()):
        start = f.get("thinking_start_marker") or (f.get("thinking_markers", {}).get("start", {}) or {}).get("text", "—")
        end = f.get("thinking_end_marker") or (f.get("thinking_markers", {}).get("end", {}) or {}).get("text", "—")
        layers = f.get("num_hidden_layers", "?")
        d_model = f.get("hidden_size", "?")
        lines.append(f"| {key} | {layers} | {d_model} | `{start}` | `{end}` |")

    lines += ["", "## Key Corrections vs Prior Sprint Summary", ""]

    # Compare against known incorrect claims
    corrections = []
    if "gemma4-e4b-it" in facts:
        g = facts["gemma4-e4b-it"]
        if g.get("num_hidden_layers") == 42:
            corrections.append(
                "- **Gemma4-E4B-IT layers**: Sprint summary `SPRINT_SUMMARY_JUN14_24.md` "
                "claimed 36 layers. **Actual: 42 layers** (d_model=2560). "
                "The '36' likely came from a Gemma3 checkpoint or MoE active-parameter confusion."
            )

    if not corrections:
        corrections.append("- No corrections needed vs prior sprint summary.")

    lines.extend(corrections)

    lines += ["", "## Full Details", ""]
    for key, f in sorted(facts.items()):
        lines.append(f"### {key}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps(f, indent=2, default=str))
        lines.append("```")
        lines.append("")

    with open(doc_path, "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines))

    print(f"  Wrote {doc_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--load-model", action="store_true",
                        help="Load actual model weights (requires GPU); default: read from existing artifacts")
    parser.add_argument("--model", choices=["qwen3", "gemma4"],
                        help="Which model to load (required with --load-model)")
    parser.add_argument("--output-dir", default=str(_OUTPUT_DIR))
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=== Model Architecture Audit ===")

    if args.load_model:
        if not args.model:
            print("ERROR: --model is required with --load-model")
            sys.exit(1)
        print(f"  Mode: load model ({args.model})")
        new_facts = _load_from_model(args.model)
        # Merge with existing artifact-based facts
        artifact_facts = _read_from_artifacts()
        artifact_facts.update(new_facts)
        facts = artifact_facts
    else:
        print("  Mode: read from existing Stage 4 artifacts (fast, no GPU)")
        facts = _read_from_artifacts()

    # Print summary
    print("\nArchitecture facts:")
    for key, f in sorted(facts.items()):
        print(f"  {key}:")
        print(f"    num_hidden_layers: {f.get('num_hidden_layers')}")
        print(f"    hidden_size:       {f.get('hidden_size')}")
        print(f"    source_type:       {f.get('source_type')}")
        print(f"    thinking_start:    {f.get('thinking_start_marker') or '—'}")
        print(f"    thinking_end:      {f.get('thinking_end_marker') or '—'}")

    # Write outputs
    audit = {
        "created_utc": _utc_now(),
        "mode": "model_load" if args.load_model else "artifacts",
        "models": facts,
    }
    out_path = output_dir / "model_architecture_audit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, default=str)
    print(f"\nJSON → {out_path}")

    _write_docs(facts, output_dir)
    print("Done.")


if __name__ == "__main__":
    main()
