"""Phase-6 §10.1-D: does ATTENTION HIJACKING predict CoT-Hijacking attack success?

The residual-stream success direction is non-causal (Phase 7). §10.1-D proposes the alternative signal
family: **attention allocation**. The CoT-Hijacking attack wraps the harmful goal in a puzzle scaffold;
the natural mechanism hypothesis is that SUCCESSFUL attacks divert attention AWAY from the harmful-goal
span (toward the puzzle) more than failed ones. This script tests that predictively.

METHOD NOTE — span-free metrics. The original plan was harmful-SPAN attention (does attention divert
from the harmful goal to the puzzle?). But this CoT-Hijacking attack does NOT quote the goal verbatim —
it abstractly encodes it into the puzzle scaffold, so the goal span is unlocatable (46/48 miss). We
therefore use SPAN-FREE §10.1-D metrics instead: per-layer ATTENTION ENTROPY (diffuse vs focused) and
MAX-CONCENTRATION at the last-K prompt (query) positions, computed on the head-averaged attention
distribution. Then per-layer raw AUC of each metric predicting attack success (D) vs failure (C).
(Raw AUC over ~48 examples — exploratory; n is small.)

Prompt-encoding attention only (one forward, output_attentions=True, eager attention). Labels from the
held-out/dev `phase6_scores.jsonl` (AE-regen StrongREJECT). GPU; ~1.5k-token prompts are memory-light.

Usage:
  python scripts/phase6_attention_signal.py \
    --manifest outputs/phase7scale_qwen3_cot_heldout25/heldout_mechanistic_manifest.jsonl \
    --scores   outputs/phase7scale_qwen3_cot_heldout25/phase6_scores.jsonl \
    --out      outputs/phase7scale_qwen3_cot_heldout25/attention_signal.csv
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import numpy as np
import torch


LAST_K = 16   # query positions = last K prompt tokens (the decision-relevant positions)


def _labels(scores_path: Path) -> dict:
    out = {}
    for line in open(scores_path):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r.get("generation_status") == "ok" and r.get("strongreject_is_success") is not None:
            out[r["row_key"]] = bool(r["strongreject_is_success"])
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, help="mechanistic manifest with C/D rows (row_key, goal, user_text)")
    ap.add_argument("--scores", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model-name", default="Qwen/Qwen3-14B")
    ap.add_argument("--max-seq-len", type=int, default=4096)
    args = ap.parse_args()

    labels = _labels(Path(args.scores))
    rows = [json.loads(l) for l in open(args.manifest) if l.strip()]
    rows = [r for r in rows if r["condition"] in ("C", "D") and r["row_key"] in labels]
    print(f"[attn] {len(rows)} C/D rows with labels", flush=True)

    from transformers import AutoModelForCausalLM, AutoTokenizer
    cache_dir = str(_REPO_ROOT / ".cache" / "huggingface")
    print("[attn] loading model (eager attention) ...", flush=True)
    tok = AutoTokenizer.from_pretrained(args.model_name, cache_dir=cache_dir)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_name, cache_dir=cache_dir, torch_dtype=torch.bfloat16,
        device_map="auto", attn_implementation="eager").eval()
    dev = model.get_input_embeddings().weight.device

    recs = []
    for i, r in enumerate(rows):
        prompt = r["user_message_text"]
        goal = r.get("goal", "")
        # chat-format the attack prompt as a user turn (same as generation), then tokenize
        formatted = tok.apply_chat_template([{"role": "user", "content": prompt}],
                                            tokenize=False, add_generation_prompt=True,
                                            enable_thinking=True)
        ids = tok(formatted, return_tensors="pt", truncation=True,
                  max_length=args.max_seq_len).input_ids.to(dev)
        seq = ids.shape[1]
        # NOTE: the CoT-Hijacking attack abstractly ENCODES the goal into the puzzle scaffold and does
        # not quote it verbatim (empirically 46/48 prompts have no locatable goal span), so a
        # harmful-SPAN attention analysis is not applicable. We instead use SPAN-FREE §10.1-D metrics:
        # attention ENTROPY (diffuse vs focused) and MAX CONCENTRATION at the last-K query positions.
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        try:
            with torch.no_grad():
                out = model(input_ids=ids, output_attentions=True, use_cache=False)
            attns = out.attentions  # tuple[n_layers] of [1, n_heads, seq, seq]
        except torch.cuda.OutOfMemoryError:
            print(f"  [{i}] {r['row_key']}: OOM at seq={seq} — skip", flush=True)
            torch.cuda.empty_cache()
            continue
        q0 = max(0, seq - LAST_K)
        ent_by_layer, maxc_by_layer = [], []
        for a in attns:
            am = a[0, :, q0:, :].mean(dim=0).to(torch.float32)  # [K, seq] avg over heads
            am = am / (am.sum(dim=-1, keepdim=True) + 1e-9)
            ent = -(am * (am + 1e-12).log()).sum(dim=-1)        # [K] per-query entropy (nats)
            ent_by_layer.append(float(ent.mean().item()))
            maxc_by_layer.append(float(am.max(dim=-1).values.mean().item()))  # mean top-attention mass
        rec = {"row_key": r["row_key"], "goal_index": r["goal_index"],
               "condition": r["condition"], "success": labels[r["row_key"]], "seq_len": seq}
        rec.update({f"attn_entropy_L{l}": v for l, v in enumerate(ent_by_layer)})
        rec.update({f"attn_maxconc_L{l}": v for l, v in enumerate(maxc_by_layer)})
        recs.append(rec)
        del out, attns
        if i % 10 == 0:
            print(f"  [{i}/{len(rows)}] {r['row_key']} seq={seq} "
                  f"entL20={ent_by_layer[20]:.3f} maxcL20={maxc_by_layer[20]:.3f}", flush=True)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    import pandas as pd
    df = pd.DataFrame.from_records(recs)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    print(f"[attn] {len(df)} examples → {args.out}", flush=True)

    # Predictive read: per-layer, per-metric AUC of the attention feature predicting success.
    # (Raw AUC over all examples; AUC far from 0.5 ⇒ the feature separates C/D. n≈48 → interpret loosely.)
    if len(df) >= 8 and df["success"].nunique() == 2:
        from sklearn.metrics import roc_auc_score
        y = df["success"].to_numpy().astype(int)
        for metric in ("attn_entropy", "attn_maxconc"):
            n_layers = sum(1 for c in df.columns if c.startswith(f"{metric}_L"))
            best = []
            for l in range(n_layers):
                x = df[f"{metric}_L{l}"].to_numpy()
                if np.std(x) == 0:
                    continue
                best.append((l, float(roc_auc_score(y, x))))
            best.sort(key=lambda t: abs(t[1] - 0.5), reverse=True)
            print(f"[attn] {metric}: top layers by |AUC−0.5| (raw AUC {metric}→success):")
            for l, auc in best[:5]:
                print(f"    L{l}: AUC={auc:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
