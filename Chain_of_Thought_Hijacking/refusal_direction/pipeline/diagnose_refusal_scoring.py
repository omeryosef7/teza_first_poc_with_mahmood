import argparse
import json
import math
import os
import random
import statistics

import torch

from dataset.load_dataset import load_dataset_split
from pipeline.model_utils.model_factory import construct_model_base
from pipeline.submodules.select_direction import get_last_position_logits, get_refusal_scores


def parse_arguments():
    parser = argparse.ArgumentParser(description="Diagnose upstream-native refusal scoring before filtering.")
    parser.add_argument("--model-path", type=str, required=True, help="Path or HF name of the model to load.")
    parser.add_argument("--output-json", type=str, required=True, help="Where to write the diagnostic JSON.")
    parser.add_argument("--n-train", type=int, default=64, help="Number of harmful and harmless train prompts to sample.")
    parser.add_argument("--n-val", type=int, default=32, help="Number of harmful and harmless val prompts to sample.")
    parser.add_argument("--sample-count", type=int, default=5, help="Number of prompts per split/harmtype to include in detailed token diagnostics.")
    parser.add_argument("--top-k", type=int, default=10, help="How many next-token predictions to record per sampled prompt.")
    return parser.parse_args()


def sample_datasets(n_train, n_val):
    random.seed(42)
    return {
        "harmful_train": random.sample(load_dataset_split(harmtype="harmful", split="train", instructions_only=True), n_train),
        "harmless_train": random.sample(load_dataset_split(harmtype="harmless", split="train", instructions_only=True), n_train),
        "harmful_val": random.sample(load_dataset_split(harmtype="harmful", split="val", instructions_only=True), n_val),
        "harmless_val": random.sample(load_dataset_split(harmtype="harmless", split="val", instructions_only=True), n_val),
    }


def token_info(tokenizer, token_id):
    token_text = tokenizer.decode([int(token_id)], skip_special_tokens=False)
    return {
        "token_id": int(token_id),
        "token_text": token_text,
        "token_text_repr": repr(token_text),
    }


def stats_for_scores(scores):
    values = [float(x) for x in scores]
    finite_values = [x for x in values if math.isfinite(x)]
    if len(finite_values) == 0:
        return {
            "count": len(values),
            "finite_count": 0,
            "non_finite_count": len(values),
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "positive_count": 0,
            "negative_count": 0,
            "zero_count": 0,
        }

    return {
        "count": len(values),
        "finite_count": len(finite_values),
        "non_finite_count": len(values) - len(finite_values),
        "min": min(finite_values),
        "max": max(finite_values),
        "mean": sum(finite_values) / len(finite_values),
        "median": statistics.median(finite_values),
        "positive_count": sum(x > 0 for x in finite_values),
        "negative_count": sum(x < 0 for x in finite_values),
        "zero_count": sum(x == 0 for x in finite_values),
    }


def next_token_summary(model_base, instructions, top_k):
    logits = get_last_position_logits(
        model=model_base.model,
        tokenizer=model_base.tokenizer,
        instructions=instructions,
        tokenize_instructions_fn=model_base.tokenize_instructions_fn,
        fwd_pre_hooks=[],
        fwd_hooks=[],
        batch_size=32,
    )
    probs = torch.softmax(logits.to(torch.float64), dim=-1)
    top_ids = torch.topk(probs, k=1, dim=-1).indices[:, 0].tolist()
    top1_counts = {}
    refusal_in_topk = 0

    for row_idx in range(probs.shape[0]):
        topk_ids = torch.topk(probs[row_idx], k=top_k, dim=-1).indices.tolist()
        top1_counts[top_ids[row_idx]] = top1_counts.get(top_ids[row_idx], 0) + 1
        if any(int(tok) in topk_ids for tok in model_base.refusal_toks):
            refusal_in_topk += 1

    top1_distribution = []
    for token_id, count in sorted(top1_counts.items(), key=lambda item: item[1], reverse=True)[:10]:
        entry = token_info(model_base.tokenizer, token_id)
        entry["count"] = count
        top1_distribution.append(entry)

    return {
        "count_prompts_with_any_refusal_token_in_top_k": refusal_in_topk,
        "top1_token_distribution": top1_distribution,
    }


def prompt_position_checks(model_base, instructions, sample_count):
    sampled = instructions[:sample_count]
    tokenized = model_base.tokenize_instructions_fn(instructions=sampled)
    eoi_toks = [int(tok) for tok in model_base.eoi_toks]
    checks = []

    for idx, instruction in enumerate(sampled):
        input_ids = tokenized.input_ids[idx].tolist()
        attention_mask = tokenized.attention_mask[idx].tolist()
        actual_ids = [tok for tok, mask in zip(input_ids, attention_mask) if mask == 1]
        suffix_ids = actual_ids[-len(eoi_toks):] if len(eoi_toks) > 0 else []
        checks.append({
            "instruction": instruction,
            "actual_prompt_token_count": len(actual_ids),
            "last_input_token": token_info(model_base.tokenizer, actual_ids[-1]),
            "prompt_suffix_token_ids": suffix_ids,
            "prompt_suffix_tokens": [token_info(model_base.tokenizer, tok) for tok in suffix_ids],
            "assistant_suffix_matches_eoi_toks": suffix_ids == eoi_toks,
        })

    return checks


def sampled_prompt_predictions(model_base, instructions, scores, sample_count, top_k):
    sampled = instructions[:sample_count]
    sampled_scores = scores[:sample_count].tolist()
    tokenized = model_base.tokenize_instructions_fn(instructions=sampled)
    logits = get_last_position_logits(
        model=model_base.model,
        tokenizer=model_base.tokenizer,
        instructions=sampled,
        tokenize_instructions_fn=model_base.tokenize_instructions_fn,
        fwd_pre_hooks=[],
        fwd_hooks=[],
        batch_size=32,
    )
    probs = torch.softmax(logits.to(torch.float64), dim=-1)
    results = []

    for idx, instruction in enumerate(sampled):
        actual_ids = [tok for tok, mask in zip(tokenized.input_ids[idx].tolist(), tokenized.attention_mask[idx].tolist()) if mask == 1]
        topk = torch.topk(probs[idx], k=top_k, dim=-1)
        predicted = []
        for token_id, prob in zip(topk.indices.tolist(), topk.values.tolist()):
            info = token_info(model_base.tokenizer, token_id)
            info["probability"] = float(prob)
            predicted.append(info)

        refusal_token_details = []
        for refusal_token_id in model_base.refusal_toks:
            refusal_prob = float(probs[idx, int(refusal_token_id)].item())
            refusal_rank = int((probs[idx] > probs[idx, int(refusal_token_id)]).sum().item()) + 1
            refusal_info = token_info(model_base.tokenizer, refusal_token_id)
            refusal_info["probability"] = refusal_prob
            refusal_info["rank"] = refusal_rank
            refusal_info["in_top_k"] = any(item["token_id"] == int(refusal_token_id) for item in predicted)
            refusal_token_details.append(refusal_info)

        results.append({
            "instruction": instruction,
            "refusal_score": float(sampled_scores[idx]),
            "last_input_token": token_info(model_base.tokenizer, actual_ids[-1]),
            "top_predicted_first_tokens": predicted,
            "refusal_token_details": refusal_token_details,
        })

    return results


def make_assessment(model_base, dataset_stats, position_checks, aggregate_next_token_stats):
    harmful_positive = dataset_stats["harmful_train"]["positive_count"] + dataset_stats["harmful_val"]["positive_count"]
    harmless_negative = dataset_stats["harmless_train"]["negative_count"] + dataset_stats["harmless_val"]["negative_count"]
    refusal_hits = (
        aggregate_next_token_stats["harmful_train"]["count_prompts_with_any_refusal_token_in_top_k"]
        + aggregate_next_token_stats["harmful_val"]["count_prompts_with_any_refusal_token_in_top_k"]
    )
    suffix_ok = all(item["assistant_suffix_matches_eoi_toks"] for item in position_checks["harmful_val"] + position_checks["harmless_val"])

    if harmful_positive == 0 and refusal_hits == 0 and suffix_ok:
        return {
            "primary_issue": "refusal_tokens_or_refusal_style_mismatch",
            "summary": "Sampled harmful prompts never score as refusals and refusal tokens do not appear among likely first generated tokens. The current upstream Qwen refusal tokens are likely invalid for Qwen3 under this chat template.",
        }
    if harmful_positive == 0 and not suffix_ok:
        return {
            "primary_issue": "chat_template_or_scoring_position_mismatch",
            "summary": "The sampled prompts do not preserve the expected assistant suffix tokens at the scored final prompt position, so the next-token refusal score may be reading the wrong position.",
        }
    if harmful_positive == 0 and harmless_negative > 0:
        return {
            "primary_issue": "harmful_prompt_scoring_mismatch",
            "summary": "Harmless prompts look non-refusal under the current score, but harmful prompts never register as refusals. The current scoring definition appears mismatched to Qwen3 harmful refusals more than to the prompts themselves.",
        }
    return {
        "primary_issue": "mixed_or_prompt_dependent",
        "summary": "The diagnostic does not isolate a single cause. Inspect the sampled token predictions and score distributions directly.",
    }


def main():
    args = parse_arguments()
    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)

    model_base = construct_model_base(args.model_path)
    datasets = sample_datasets(args.n_train, args.n_val)

    dataset_scores = {}
    dataset_stats = {}
    aggregate_next_token_stats = {}
    for name, instructions in datasets.items():
        scores = get_refusal_scores(
            model_base.model,
            instructions,
            model_base.tokenize_instructions_fn,
            model_base.refusal_toks,
            batch_size=32,
        )
        dataset_scores[name] = scores
        dataset_stats[name] = stats_for_scores(scores.tolist())
        aggregate_next_token_stats[name] = next_token_summary(model_base, instructions, args.top_k)

    position_checks = {
        "harmful_val": prompt_position_checks(model_base, datasets["harmful_val"], args.sample_count),
        "harmless_val": prompt_position_checks(model_base, datasets["harmless_val"], args.sample_count),
    }

    sample_predictions = {
        name: sampled_prompt_predictions(model_base, datasets[name], dataset_scores[name], args.sample_count, args.top_k)
        for name in ("harmful_train", "harmless_train", "harmful_val", "harmless_val")
    }

    refusal_tokens = [token_info(model_base.tokenizer, tok) for tok in model_base.refusal_toks]
    eoi_tokens = [token_info(model_base.tokenizer, tok) for tok in model_base.eoi_toks]

    diagnostic = {
        "model_path": args.model_path,
        "diagnostic_type": "upstream_native_refusal_scoring_pre_filter",
        "sampled_prompt_counts": {name: len(items) for name, items in datasets.items()},
        "refusal_tokens": refusal_tokens,
        "assistant_suffix_eoi_tokens": eoi_tokens,
        "score_position": {
            "description": "refusal_score uses logits[:, -1, :], i.e. the next-token distribution after the final input token of the chat-templated prompt.",
            "scored_token_source": "first assistant token predicted immediately after the chat-template assistant prefill",
        },
        "score_distributions": dataset_stats,
        "pre_filter_sign_checks": {
            "harmful_train_score_gt_zero": dataset_stats["harmful_train"]["positive_count"],
            "harmful_val_score_gt_zero": dataset_stats["harmful_val"]["positive_count"],
            "harmless_train_score_lt_zero": dataset_stats["harmless_train"]["negative_count"],
            "harmless_val_score_lt_zero": dataset_stats["harmless_val"]["negative_count"],
        },
        "aggregate_next_token_stats": aggregate_next_token_stats,
        "prompt_position_checks": position_checks,
        "sample_prompt_predictions": sample_predictions,
    }
    diagnostic["assessment"] = make_assessment(model_base, dataset_stats, position_checks, aggregate_next_token_stats)

    with open(args.output_json, "w") as f:
        json.dump(diagnostic, f, indent=4)


if __name__ == "__main__":
    main()
