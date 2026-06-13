"""
Define and document the safe structural action space for the AutoInject-style POC.

Actions are discrete choices over structural wrapper configurations.
No harmful content is generated or stored.

Outputs:
  outputs/meeting/mahmood_48h_update_20260611_143740/autoinject_poc/safe_structural_action_space.json
  outputs/meeting/mahmood_48h_update_20260611_143740/autoinject_poc/SAFE_STRUCTURAL_ACTION_SPACE.md
"""

import csv
import json
import os
from collections import Counter, defaultdict

DATASET_PATH = (
    "outputs/meeting/mahmood_48h_update_20260611_143740/autoinject_poc/autoinject_poc_dataset.csv"
)
OUT_DIR = "outputs/meeting/mahmood_48h_update_20260611_143740/autoinject_poc"
OUT_JSON = os.path.join(OUT_DIR, "safe_structural_action_space.json")
OUT_MD = os.path.join(OUT_DIR, "SAFE_STRUCTURAL_ACTION_SPACE.md")


def safe_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ("true", "1")
    return bool(val)


def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def infer_length_bucket(think_tokens):
    t = int(think_tokens) if str(think_tokens).strip().isdigit() else 0
    if t == 0:
        return "none"
    if t < 1000:
        return "short"
    if t < 5000:
        return "medium"
    if t < 15000:
        return "long"
    return "very_long"


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Load dataset
    rows = []
    with open(DATASET_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))

    # Infer length bucket for each row
    for row in rows:
        row["length_bucket"] = infer_length_bucket(row.get("think_token_count", "0"))

    # Define the primary action space: 4 main wrapper types
    primary_actions = {
        "A": {
            "action_id": "A",
            "wrapper_type": "A",
            "description": "Full puzzle wrapper + thinking enabled",
            "has_puzzle": True,
            "has_thinking": True,
            "is_length_matched": False,
            "is_bare_target": False,
            "thinking_mode": "on",
        },
        "D": {
            "action_id": "D",
            "wrapper_type": "D",
            "description": "Bare target only + thinking enabled",
            "has_puzzle": False,
            "has_thinking": True,
            "is_length_matched": False,
            "is_bare_target": True,
            "thinking_mode": "on",
        },
        "F": {
            "action_id": "F",
            "wrapper_type": "F",
            "description": "Full puzzle + thinking disabled (length-matched benign)",
            "has_puzzle": True,
            "has_thinking": False,
            "is_length_matched": True,
            "is_bare_target": False,
            "thinking_mode": "off",
        },
        "E": {
            "action_id": "E",
            "wrapper_type": "E",
            "description": "Bare target + thinking disabled",
            "has_puzzle": False,
            "has_thinking": False,
            "is_length_matched": False,
            "is_bare_target": True,
            "thinking_mode": "off",
        },
    }

    # Secondary action dimensions (not yet independently manipulable,
    # but observed in existing data and definable for future experiments)
    secondary_dimensions = {
        "choose_length_bucket": {
            "description": "Control reasoning length (short/medium/long/matched)",
            "values": ["short", "medium", "long", "very_long", "none"],
            "status": "observable_from_data_not_yet_independently_controllable",
            "notes": "Correlated with condition: A produces long thinking, F/E produce short/none",
        },
        "choose_reasoning_difficulty": {
            "description": "Puzzle difficulty level (easy/medium/hard/unknown)",
            "values": ["easy", "medium", "hard", "unknown"],
            "status": "not_yet_measured",
            "notes": "Would require puzzle complexity scoring; currently unknown",
        },
        "choose_target_placement": {
            "description": "Position of target task within wrapper (early/middle/late/unchanged)",
            "values": ["early", "middle", "late", "unchanged", "unknown"],
            "status": "not_yet_independently_manipulable",
            "notes": "Observable via onset_bucket proxy; not yet directly controlled",
        },
        "choose_answer_cue_strength": {
            "description": "Strength of answer guidance cue (weak/medium/strong)",
            "values": ["weak", "medium", "strong", "unchanged", "unknown"],
            "status": "not_yet_measured",
            "notes": "Requires semantic analysis of wrapper phrasing",
        },
        "choose_thinking_mode": {
            "description": "Whether extended thinking is enabled",
            "values": ["on", "off"],
            "status": "directly_controllable",
            "notes": "A/D = on, F/E = off. This is the main thinking mode lever.",
        },
    }

    # Compute observed statistics per condition from dataset
    cond_stats = defaultdict(lambda: {
        "n": 0, "n_success": 0, "sr_scores": [], "think_tokens": [],
        "onset_percents": [], "censored": 0, "length_buckets": Counter(),
    })

    for row in rows:
        c = row.get("condition", "?")
        cond_stats[c]["n"] += 1
        if safe_bool(row.get("sr_success", False)):
            cond_stats[c]["n_success"] += 1
        cond_stats[c]["sr_scores"].append(safe_float(row.get("sr_score", "0")))
        cond_stats[c]["think_tokens"].append(safe_float(row.get("think_token_count", "0")))
        op = row.get("onset_percent", "")
        if op:
            cond_stats[c]["onset_percents"].append(safe_float(op))
        if safe_bool(row.get("censored", False)):
            cond_stats[c]["censored"] += 1
        cond_stats[c]["length_buckets"][row.get("length_bucket", "?")] += 1

    def mean(lst):
        return sum(lst) / len(lst) if lst else None

    cond_summary = {}
    for cond, s in cond_stats.items():
        n = s["n"]
        cond_summary[cond] = {
            "n": n,
            "asr_percent": round(100.0 * s["n_success"] / n, 1) if n > 0 else None,
            "mean_sr_score": round(mean(s["sr_scores"]) or 0.0, 3),
            "mean_think_tokens": round(mean(s["think_tokens"]) or 0.0, 1),
            "mean_onset_percent": round(mean(s["onset_percents"]) or 0.0, 4) if s["onset_percents"] else None,
            "censored_count": s["censored"],
            "length_bucket_distribution": dict(s["length_buckets"]),
        }
        if cond in primary_actions:
            cond_summary[cond].update(primary_actions[cond])

    # Build full JSON output
    action_space = {
        "description": "Safe structural action space for AutoInject-style offline optimization POC",
        "domain": "CoT hijacking of reasoning models (Qwen3-14B)",
        "safety_note": (
            "This action space covers only structural wrapper modifications. "
            "No new harmful content is generated. All candidates are from existing Stage 4.7/4.8 runs. "
            "The space does NOT include: suffix token mutations, semantic content modifications, "
            "or any actions that would require generating new harmful prompts."
        ),
        "primary_actions": primary_actions,
        "secondary_dimensions": secondary_dimensions,
        "observed_condition_statistics": cond_summary,
        "total_candidates_in_pool": len(rows),
        "n_conditions": len(cond_stats),
        "recommended_primary_reward": "sr_success",
        "secondary_reward_components": [
            "sr_score",
            "onset_percent (diagnostic, unvalidated heuristic)",
            "think_token_count (correlated with ASR but not causal)",
        ],
        "do_not_use_as_primary_reward": [
            "think_token_count alone (optimises reasoning length, not task success)",
            "l22_projection (provisional diagnostic direction, not proven refusal mechanism)",
        ],
    }

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(action_space, f, indent=2)
    print(f"Written: {OUT_JSON}")

    # Write markdown documentation
    lines = [
        "# Safe Structural Action Space",
        "",
        "**Domain:** CoT hijacking of reasoning models (Qwen3-14B)  ",
        "**Purpose:** Define the discrete action space for AutoInject-style offline optimization POC  ",
        "**Safety:** All actions are structural wrapper choices over *existing* runs. No new content generated.",
        "",
        "---",
        "",
        "## Primary Actions (Directly Measurable)",
        "",
        "These are the 4 main structural conditions already tested in Stage 4.7/4.8:",
        "",
        "| Action | Wrapper Type | Puzzle | Thinking | Length Matched | Bare Target |",
        "|--------|-------------|--------|----------|----------------|-------------|",
        "| A | Full puzzle + thinking | Yes | On | No | No |",
        "| D | Bare target + thinking | No | On | No | Yes |",
        "| F | Full puzzle, no thinking | Yes | Off | Yes | No |",
        "| E | Bare target, no thinking | No | Off | No | Yes |",
        "",
        "## Observed Empirical Statistics Per Condition",
        "",
        "| Condition | N | ASR% | Mean SR Score | Mean Think Tokens | Censored |",
        "|-----------|---|------|--------------|------------------|---------|",
    ]
    for cond in sorted(cond_summary.keys()):
        s = cond_summary[cond]
        lines.append(
            f"| {cond} | {s['n']} | {s.get('asr_percent','?')}% "
            f"| {s.get('mean_sr_score','?')} "
            f"| {s.get('mean_think_tokens','?'):.0f} "
            f"| {s.get('censored_count','?')} |"
        )

    lines += [
        "",
        "## Secondary Dimensions (Future Experiments)",
        "",
        "These dimensions are observable or theoretically actionable but not yet",
        "independently manipulable in existing data:",
        "",
        "| Dimension | Values | Status |",
        "|-----------|--------|--------|",
        "| length_bucket | short/medium/long/very_long/none | observable from data |",
        "| reasoning_difficulty | easy/medium/hard/unknown | not yet measured |",
        "| target_placement | early/middle/late/unchanged/unknown | observed via onset_bucket proxy |",
        "| answer_cue_strength | weak/medium/strong/unchanged/unknown | not yet measured |",
        "| thinking_mode | on/off | directly controllable (A/D vs F/E) |",
        "",
        "## What NOT to Optimise",
        "",
        "- **think_token_count alone**: Condition A produces long reasoning AND high ASR, but",
        "  optimising for length alone does not cause success — it just selects condition A.",
        "  Reward should include sr_success as primary signal.",
        "",
        "- **L22 projection**: The Layer-22 'provisional harmful-vs-harmless contrast direction'",
        "  is a diagnostic tool, not a validated reward signal. It must NOT be used as the",
        "  primary optimization objective.",
        "",
        "## Recommended Next Action (Requires Mahmood Approval)",
        "",
        "A constrained online AutoInject-style run where:",
        "- Actions = choosing from {A, D, F, E} structural wrappers",
        "- Prompts = same existing research prompts from Stage 4.7 (no new harmful content)",
        "- Reward = sr_success (primary), sr_score (secondary)",
        "- Budget = 20–40 online evaluations",
        "- Goal = validate whether condition A is robustly optimal across goals",
        "",
        "---",
        "",
        "*Generated by `poc_meeting/mahmood_48h_update/autoinject_poc/build_safe_structural_action_space.py`*",
    ]

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Written: {OUT_MD}")

    print(f"\nSummary:")
    for cond in sorted(cond_summary.keys()):
        s = cond_summary[cond]
        print(f"  {cond}: n={s['n']}, ASR={s.get('asr_percent')}%, "
              f"mean_sr={s.get('mean_sr_score')}, mean_think={s.get('mean_think_tokens','?'):.0f}")


if __name__ == "__main__":
    main()
