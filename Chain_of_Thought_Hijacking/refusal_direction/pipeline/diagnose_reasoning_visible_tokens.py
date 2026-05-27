import argparse
import json
import os
import random
from collections import Counter

import torch
from transformers import GenerationConfig

from dataset.load_dataset import load_dataset_split
from pipeline.model_utils.model_factory import construct_model_base


def parse_arguments():
    parser = argparse.ArgumentParser(description="Diagnose visible post-reasoning answer tokens for upstream-native Qwen3.")
    parser.add_argument("--model-path", type=str, required=True, help="Path or HF name of the model to load.")
    parser.add_argument("--output-json", type=str, required=True, help="Where to write the diagnostic JSON.")
    parser.add_argument("--n-harmful", type=int, default=16, help="Number of harmful prompts to sample.")
    parser.add_argument("--n-harmless", type=int, default=16, help="Number of harmless prompts to sample.")
    parser.add_argument("--split", type=str, default="val", choices=["train", "val", "test"], help="Dataset split to sample.")
    parser.add_argument("--max-new-tokens", type=int, default=256, help="Maximum tokens to generate per prompt.")
    parser.add_argument("--sample-count", type=int, default=5, help="Number of sample rows to keep per harmtype in the JSON.")
    parser.add_argument("--top-k", type=int, default=10, help="Top-k first visible token frequencies to report.")
    return parser.parse_args()


def token_info(tokenizer, token_id):
    token_text = tokenizer.decode([int(token_id)], skip_special_tokens=False)
    return {
        "token_id": int(token_id),
        "token_text": token_text,
        "token_text_repr": repr(token_text),
    }


def sample_instructions(split, n_harmful, n_harmless):
    random.seed(42)
    harmful = random.sample(load_dataset_split(harmtype="harmful", split=split, instructions_only=True), n_harmful)
    harmless = random.sample(load_dataset_split(harmtype="harmless", split=split, instructions_only=True), n_harmless)
    return harmful, harmless


def find_subsequence(sequence, subsequence):
    if len(subsequence) == 0 or len(sequence) < len(subsequence):
        return None
    for start in range(0, len(sequence) - len(subsequence) + 1):
        if sequence[start:start + len(subsequence)] == subsequence:
            return start
    return None


def is_skippable_visible_token(tokenizer, token_id):
    text = tokenizer.decode([int(token_id)], skip_special_tokens=False)
    return text.strip() == ""


def first_visible_token_after_reasoning(tokenizer, generated_token_ids, think_open_ids, think_close_ids):
    think_open_start = find_subsequence(generated_token_ids, think_open_ids)
    think_close_start = find_subsequence(generated_token_ids, think_close_ids)

    start_index = 0
    if think_open_start is not None and think_close_start is not None and think_close_start >= think_open_start:
        start_index = think_close_start + len(think_close_ids)

    visible_index = None
    for idx in range(start_index, len(generated_token_ids)):
        if not is_skippable_visible_token(tokenizer, generated_token_ids[idx]):
            visible_index = idx
            break

    if visible_index is None:
        return {
            "has_think_open": think_open_start is not None,
            "has_think_close": think_close_start is not None,
            "visible_start_index": None,
            "first_visible_token_id": None,
            "first_visible_token": None,
            "visible_token_ids_preview": [],
            "visible_tokens_preview": [],
        }

    visible_preview_ids = generated_token_ids[visible_index:visible_index + 8]
    return {
        "has_think_open": think_open_start is not None,
        "has_think_close": think_close_start is not None,
        "visible_start_index": visible_index,
        "first_visible_token_id": int(generated_token_ids[visible_index]),
        "first_visible_token": token_info(tokenizer, generated_token_ids[visible_index]),
        "visible_token_ids_preview": visible_preview_ids,
        "visible_tokens_preview": [token_info(tokenizer, tok) for tok in visible_preview_ids],
    }


def generate_for_instructions(model_base, instructions, max_new_tokens):
    tokenized = model_base.tokenize_instructions_fn(instructions=instructions)
    generation_config = GenerationConfig(
        max_new_tokens=max_new_tokens,
        do_sample=False,
        pad_token_id=model_base.tokenizer.pad_token_id,
    )
    outputs = model_base.model.generate(
        input_ids=tokenized.input_ids.to(model_base.model.device),
        attention_mask=tokenized.attention_mask.to(model_base.model.device),
        generation_config=generation_config,
    )

    prompt_len = tokenized.input_ids.shape[-1]
    return [row[prompt_len:].tolist() for row in outputs]


def summarize_group(model_base, instructions, generated_rows, think_open_ids, think_close_ids, refusal_token_ids, sample_count, top_k):
    first_visible_counter = Counter()
    first_visible_refusal_hits = 0
    any_refusal_in_visible_prefix_hits = 0
    has_think_open_count = 0
    has_think_close_count = 0
    examples = []

    for instruction, generated_ids in zip(instructions, generated_rows):
        visible = first_visible_token_after_reasoning(
            tokenizer=model_base.tokenizer,
            generated_token_ids=generated_ids,
            think_open_ids=think_open_ids,
            think_close_ids=think_close_ids,
        )
        has_think_open_count += int(visible["has_think_open"])
        has_think_close_count += int(visible["has_think_close"])

        first_token_id = visible["first_visible_token_id"]
        if first_token_id is not None:
            first_visible_counter[first_token_id] += 1
            if first_token_id in refusal_token_ids:
                first_visible_refusal_hits += 1
            if any(tok in refusal_token_ids for tok in visible["visible_token_ids_preview"]):
                any_refusal_in_visible_prefix_hits += 1

        if len(examples) < sample_count:
            examples.append({
                "instruction": instruction,
                "generated_token_ids": generated_ids,
                "generated_text_raw": model_base.tokenizer.decode(generated_ids, skip_special_tokens=False),
                "generated_text_stripped": model_base.tokenizer.decode(generated_ids, skip_special_tokens=True),
                "visible_analysis": visible,
            })

    top_first_visible_tokens = []
    for token_id, count in first_visible_counter.most_common(top_k):
        entry = token_info(model_base.tokenizer, token_id)
        entry["count"] = count
        top_first_visible_tokens.append(entry)

    return {
        "prompt_count": len(instructions),
        "count_with_think_open": has_think_open_count,
        "count_with_think_close": has_think_close_count,
        "count_first_visible_token_is_current_refusal_token": first_visible_refusal_hits,
        "count_any_current_refusal_token_in_visible_prefix_preview": any_refusal_in_visible_prefix_hits,
        "top_first_visible_tokens": top_first_visible_tokens,
        "sample_examples": examples,
    }


def assess_reasoning_results(harmful_summary, harmless_summary, refusal_token_ids):
    harmful_top = harmful_summary["top_first_visible_tokens"][0] if harmful_summary["top_first_visible_tokens"] else None
    harmless_top = harmless_summary["top_first_visible_tokens"][0] if harmless_summary["top_first_visible_tokens"] else None

    harmful_refusal_first = harmful_summary["count_first_visible_token_is_current_refusal_token"]
    harmless_refusal_first = harmless_summary["count_first_visible_token_is_current_refusal_token"]

    if harmful_refusal_first == 0 and harmless_refusal_first == 0:
        return {
            "primary_issue": "current_refusal_tokens_invalid_after_reasoning",
            "summary": "With reasoning enabled, the first visible post-</think> answer token is not one of the current refusal tokens for either harmful or harmless prompts. The refusal token definition should be adapted for reasoning-on Qwen3.",
            "current_refusal_token_ids": refusal_token_ids,
            "harmful_top_first_visible_token": harmful_top,
            "harmless_top_first_visible_token": harmless_top,
        }

    return {
        "primary_issue": "current_refusal_tokens_partially_match_visible_answer_start",
        "summary": "Current refusal tokens appear at the first visible answer token for at least some prompts. Inspect the sampled outputs to decide whether the refusal token set is sufficient.",
        "current_refusal_token_ids": refusal_token_ids,
        "harmful_top_first_visible_token": harmful_top,
        "harmless_top_first_visible_token": harmless_top,
    }


def main():
    args = parse_arguments()
    os.makedirs(os.path.dirname(args.output_json), exist_ok=True)

    model_base = construct_model_base(args.model_path)
    harmful, harmless = sample_instructions(args.split, args.n_harmful, args.n_harmless)

    think_open_ids = model_base.tokenizer.encode("<think>", add_special_tokens=False)
    think_close_ids = model_base.tokenizer.encode("</think>", add_special_tokens=False)
    refusal_token_ids = [int(tok) for tok in model_base.refusal_toks]

    harmful_rows = generate_for_instructions(model_base, harmful, args.max_new_tokens)
    harmless_rows = generate_for_instructions(model_base, harmless, args.max_new_tokens)

    harmful_summary = summarize_group(
        model_base=model_base,
        instructions=harmful,
        generated_rows=harmful_rows,
        think_open_ids=think_open_ids,
        think_close_ids=think_close_ids,
        refusal_token_ids=refusal_token_ids,
        sample_count=args.sample_count,
        top_k=args.top_k,
    )
    harmless_summary = summarize_group(
        model_base=model_base,
        instructions=harmless,
        generated_rows=harmless_rows,
        think_open_ids=think_open_ids,
        think_close_ids=think_close_ids,
        refusal_token_ids=refusal_token_ids,
        sample_count=args.sample_count,
        top_k=args.top_k,
    )

    diagnostic = {
        "model_path": args.model_path,
        "diagnostic_type": "upstream_native_reasoning_visible_tokens",
        "split": args.split,
        "sampled_prompt_counts": {
            "harmful": len(harmful),
            "harmless": len(harmless),
        },
        "current_refusal_tokens": [token_info(model_base.tokenizer, tok) for tok in refusal_token_ids],
        "reasoning_tokens": {
            "think_open_ids": think_open_ids,
            "think_open_tokens": [token_info(model_base.tokenizer, tok) for tok in think_open_ids],
            "think_close_ids": think_close_ids,
            "think_close_tokens": [token_info(model_base.tokenizer, tok) for tok in think_close_ids],
        },
        "generation_config": {
            "max_new_tokens": args.max_new_tokens,
            "do_sample": False,
        },
        "harmful_summary": harmful_summary,
        "harmless_summary": harmless_summary,
    }
    diagnostic["assessment"] = assess_reasoning_results(harmful_summary, harmless_summary, refusal_token_ids)

    with open(args.output_json, "w") as f:
        json.dump(diagnostic, f, indent=4)


if __name__ == "__main__":
    main()
