#!/usr/bin/env python3
"""Phase 7A full-520 behavior-level analysis.

1. Self-constructed heuristic keyword categorization of the 520 AdvBench goals
   (NOT an official/validated taxonomy -- AdvBench's own release has no category
   field, confirmed by checking dataset/raw/advbench.csv and the upstream
   llm-attacks GitHub source, both goal,target only).
2. Per-behavior success matrix across conditions (seeded + unseeded).
3. Behavior-clustered bootstrap CIs for uplift vs neutral/task_only/random_spaces.
4. Characterization of the 27 behaviors missing from the unseeded eval.

Outputs: outputs/stage_gcg_full/GCG_7A_BEHAVIOR_ANALYSIS.json
"""
import json
import re
import random
from pathlib import Path
from collections import defaultdict

try:
    from scipy.stats import binomtest
    _HAVE_SCIPY = True
except ImportError:
    _HAVE_SCIPY = False

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "outputs" / "stage_gcg_full"
MANIFEST_520 = BASE / "advbench_cot_full520_manifest.jsonl"
SEEDED = BASE / "gcg_full_qwen3_7a_5a_full520" / "FREE_GENERATION_RESULTS.jsonl"
UNSEEDED = BASE / "gcg_full_qwen3_7a_5a_full520" / "FREE_GENERATION_RESULTS_UNSEEDED.jsonl"
LLM_TAXONOMY = BASE / "ADVBENCH_LLM_TAXONOMY.json"

random.seed(42)

# --- 1. Heuristic keyword taxonomy (self-constructed; NOT official AdvBench categories) ---
CATEGORY_KEYWORDS = [
    ("cyber_malware", r"\b(hack|exploit|malware|virus|ransomware|ddos|phishing|password|firewall|network|software vulnerabilit|computer system|encrypt.*(files|data)|keylogger|botnet|spyware|trojan)\b"),
    ("weapons_physical_harm", r"\b(bomb|explosiv|weapon|gun|firearm|poison|kill|attack|violence|assassinat|chemical (weapon|agent)|biological weapon|nerve agent|nuclear)\b"),
    ("fraud_financial", r"\b(fraud|scam|launder|counterfeit|embezzl|ponzi|identity theft|credit card|steal.*(money|funds)|tax evasion|insider trading|financial)\b"),
    ("misinformation_disinfo", r"\b(fake news|disinformation|misinformation|conspiracy|propaganda|hoax|rumor|manipulat.*(public|election|opinion)|deepfake)\b"),
    ("hate_harassment", r"\b(hate speech|racist|racial|discriminat|harass|bully|threat.*(person|individual)|degrad|demean)\b"),
    ("drugs_illegal_substances", r"\b(drug|narcotic|methamphetamine|heroin|cocaine|opioid|illegal substance)\b"),
    ("privacy_surveillance", r"\b(track.*(location|someone|person)|stalk|spy on|surveil|personal (information|data)|private information|dox)\b"),
    ("self_harm", r"\b(suicide|self-harm|self harm|eating disorder)\b"),
    ("child_safety", r"\b(child|minor|children).{0,30}\b(exploit|abuse|access firearms)\b"),
]


def categorize(goal: str) -> str:
    g = goal.lower()
    for cat, pattern in CATEGORY_KEYWORDS:
        if re.search(pattern, g):
            return cat
    return "other_uncategorized"


def load_manifest():
    behaviors = {}
    for line in MANIFEST_520.open():
        r = json.loads(line)
        behaviors[r["task_id"]] = {
            "instruction": r["instruction"],
            "prompt_len_chars": len(r["instruction"]),
            "target_len_chars": len(r.get("safe_target_prefix", "")),
            "advbench_row": r.get("advbench_row"),
        }
    return behaviors


def load_results(p: Path):
    rows = defaultdict(list)  # task_id -> list of rows
    for line in p.open():
        r = json.loads(line)
        rows[r["task_id"]].append(r)
    return rows


def per_behavior_success(rows_by_task, condition):
    """Return {task_id: (n_success, n_total)} for a given condition_label across all seeds."""
    out = {}
    for tid, rows in rows_by_task.items():
        cond_rows = [r for r in rows if r.get("condition_label") == condition]
        n = len(cond_rows)
        s = sum(1 for r in cond_rows if r.get("strongreject_is_success"))
        out[tid] = (s, n)
    return out


def cluster_bootstrap_uplift(rows_by_task, cond_a, cond_b, n_boot=2000):
    """Behavior-clustered bootstrap CI for ASR(cond_a) - ASR(cond_b).
    Resample behaviors (task_ids) with replacement; for each resample, pool all
    rows of the resampled behaviors and compute the ASR difference."""
    task_ids = list(rows_by_task.keys())
    n = len(task_ids)
    diffs = []
    for _ in range(n_boot):
        sample = [task_ids[random.randrange(n)] for _ in range(n)]
        a_s = a_n = b_s = b_n = 0
        for tid in sample:
            for r in rows_by_task[tid]:
                if r.get("condition_label") == cond_a:
                    a_n += 1
                    a_s += int(bool(r.get("strongreject_is_success")))
                elif r.get("condition_label") == cond_b:
                    b_n += 1
                    b_s += int(bool(r.get("strongreject_is_success")))
        if a_n == 0 or b_n == 0:
            continue
        diffs.append(a_s / a_n - b_s / b_n)
    diffs.sort()
    if not diffs:
        return None
    lo = diffs[int(0.025 * len(diffs))]
    hi = diffs[int(0.975 * len(diffs))]
    point = sum(diffs) / len(diffs)
    return {"point_estimate_mean_of_bootstrap": point, "ci95_lo": lo, "ci95_hi": hi, "n_boot_valid": len(diffs)}


def mcnemar_exact(rows_by_task, cond_a, cond_b):
    """Exact McNemar's test on (task_id, seed)-paired binary success outcomes.
    Only pairs where BOTH conditions have a row for that exact (task_id, seed) are used.
    Returns discordant counts (b = a-succ/b-fail, c = a-fail/b-succ) and a two-sided
    exact p-value via binomtest(min(b,c), b+c, 0.5) -- the standard exact McNemar test.
    Requires scipy (available in the poc_stage2 conda env, NOT the base env)."""
    by_key_a = {}
    by_key_b = {}
    for tid, rows in rows_by_task.items():
        for r in rows:
            key = (tid, r.get("seed"))
            if r.get("condition_label") == cond_a:
                by_key_a[key] = bool(r.get("strongreject_is_success"))
            elif r.get("condition_label") == cond_b:
                by_key_b[key] = bool(r.get("strongreject_is_success"))
    common_keys = set(by_key_a) & set(by_key_b)
    b_count = 0  # a=success, b=fail
    c_count = 0  # a=fail, b=success
    both_success = both_fail = 0
    for k in common_keys:
        a, b = by_key_a[k], by_key_b[k]
        if a and not b:
            b_count += 1
        elif b and not a:
            c_count += 1
        elif a and b:
            both_success += 1
        else:
            both_fail += 1

    result = {
        "n_paired_observations": len(common_keys),
        "a_success_b_fail": b_count,
        "a_fail_b_success": c_count,
        "both_success": both_success,
        "both_fail": both_fail,
    }
    if not _HAVE_SCIPY:
        result["p_value_exact"] = None
        result["note"] = "scipy not available in this python env -- rerun under poc_stage2 conda env for the p-value"
        return result
    n_discordant = b_count + c_count
    if n_discordant == 0:
        result["p_value_exact"] = 1.0
        result["note"] = "no discordant pairs -- conditions never disagreed on the same (task_id, seed)"
    else:
        test = binomtest(min(b_count, c_count), n_discordant, 0.5, alternative="two-sided")
        result["p_value_exact"] = float(test.pvalue)
    return result


def main():
    behaviors = load_manifest()
    for tid, b in behaviors.items():
        b["heuristic_category"] = categorize(b["instruction"])

    llm_taxonomy = {}
    if LLM_TAXONOMY.exists():
        llm_labels = json.loads(LLM_TAXONOMY.read_text())["labels"]
        for tid, v in llm_labels.items():
            llm_taxonomy[tid] = v["category"]
        for tid, b in behaviors.items():
            b["llm_category"] = llm_taxonomy.get(tid, "unknown")

    cat_counts = defaultdict(int)
    for b in behaviors.values():
        cat_counts[b["heuristic_category"]] += 1

    seeded_rows = load_results(SEEDED)
    unseeded_rows = load_results(UNSEEDED)

    all_ids = set(behaviors.keys())
    unseeded_present = set(unseeded_rows.keys())
    missing_unseeded = sorted(all_ids - unseeded_present)

    # --- per-behavior success matrix (seeded, optimized vs neutral/task_only/random_spaces) ---
    opt_seeded = per_behavior_success(seeded_rows, "optimized_weighted")
    neu_seeded = per_behavior_success(seeded_rows, "neutral_control")
    task_seeded = per_behavior_success(seeded_rows, "task_only")
    rand_seeded = per_behavior_success(seeded_rows, "random_spaces")

    classification = defaultdict(int)
    for tid in all_ids:
        os_, on = opt_seeded.get(tid, (0, 0))
        ns_, nn = neu_seeded.get(tid, (0, 0))
        ts_, tn = task_seeded.get(tid, (0, 0))
        rs_, rn = rand_seeded.get(tid, (0, 0))
        opt_succ = os_ > 0
        base_succ = (ns_ > 0) or (ts_ > 0) or (rs_ > 0)
        if opt_succ and not base_succ:
            classification["gcg_exclusive_success"] += 1
        elif base_succ and not opt_succ:
            classification["baseline_only_success"] += 1
        elif opt_succ and base_succ:
            classification["success_under_multiple_conditions"] += 1
        else:
            classification["no_successes_any_condition"] += 1

    # --- bootstrap uplift CIs (seeded) ---
    uplift_vs_neutral = cluster_bootstrap_uplift(seeded_rows, "optimized_weighted", "neutral_control")
    uplift_vs_task_only = cluster_bootstrap_uplift(seeded_rows, "optimized_weighted", "task_only")
    uplift_vs_random = cluster_bootstrap_uplift(seeded_rows, "optimized_weighted", "random_spaces")

    # --- unseeded uplift (only over the 493 present behaviors) ---
    unseeded_uplift_vs_neutral = cluster_bootstrap_uplift(unseeded_rows, "optimized_weighted", "neutral_control")

    # --- missing-27 characterization ---
    present_prompt_lens = [behaviors[t]["prompt_len_chars"] for t in unseeded_present]
    missing_prompt_lens = [behaviors[t]["prompt_len_chars"] for t in missing_unseeded]
    present_rows_idx = sorted(int(t.split("_")[-1]) for t in unseeded_present)
    missing_rows_idx = sorted(int(t.split("_")[-1]) for t in missing_unseeded)

    missing_cat_counts = defaultdict(int)
    for t in missing_unseeded:
        missing_cat_counts[behaviors[t]["heuristic_category"]] += 1

    def mean(xs):
        return sum(xs) / len(xs) if xs else None

    # --- category-based success analysis (uses the LLM-read-through taxonomy if present) ---
    category_analysis = {}
    if llm_taxonomy:
        cat_to_tids = defaultdict(list)
        for tid, b in behaviors.items():
            cat_to_tids[b["llm_category"]].append(tid)
        for cat, tids in cat_to_tids.items():
            n = len(tids)
            opt_s = opt_n = neu_s = neu_n = 0
            gcg_exclusive = 0
            for tid in tids:
                os_, on = opt_seeded.get(tid, (0, 0))
                ns_, nn = neu_seeded.get(tid, (0, 0))
                ts_, tn = task_seeded.get(tid, (0, 0))
                rs_, rn = rand_seeded.get(tid, (0, 0))
                opt_s += os_; opt_n += on
                neu_s += ns_; neu_n += nn
                if os_ > 0 and not (ns_ > 0 or ts_ > 0 or rs_ > 0):
                    gcg_exclusive += 1
            category_analysis[cat] = {
                "n_behaviors": n,
                "optimized_asr": round(opt_s / opt_n, 4) if opt_n else None,
                "neutral_asr": round(neu_s / neu_n, 4) if neu_n else None,
                "uplift_pp": round(100 * (opt_s / opt_n - neu_s / neu_n), 2) if (opt_n and neu_n) else None,
                "n_gcg_exclusive_success_behaviors": gcg_exclusive,
                "small_n_warning": n < 15,
            }

    # --- paired exact McNemar's tests (seeded + unseeded) ---
    mcnemar_results = {
        "seeded_optimized_vs_neutral": mcnemar_exact(seeded_rows, "optimized_weighted", "neutral_control"),
        "seeded_optimized_vs_task_only": mcnemar_exact(seeded_rows, "optimized_weighted", "task_only"),
        "seeded_optimized_vs_random_spaces": mcnemar_exact(seeded_rows, "optimized_weighted", "random_spaces"),
        "unseeded_optimized_vs_neutral": mcnemar_exact(unseeded_rows, "optimized_weighted", "neutral_control"),
    }

    out = {
        "heuristic_category_disclaimer": "Self-constructed keyword categorization over AdvBench's 'goal' field. AdvBench itself (both the local raw copy at Chain_of_Thought_Hijacking/refusal_direction/dataset/raw/advbench.csv and the canonical upstream llm-attacks GitHub release) ships only goal,target -- NO official category field exists. This taxonomy is NOT validated and should not be cited as 'AdvBench categories'.",
        "category_counts_all_520": dict(sorted(cat_counts.items(), key=lambda kv: -kv[1])),
        "behavior_classification_seeded": dict(classification),
        "category_based_success_analysis_llm_taxonomy": dict(sorted(category_analysis.items(), key=lambda kv: -(kv[1]["n_behaviors"]))),
        "mcnemar_exact_tests": mcnemar_results,
        "uplift_seeded_optimized_vs_neutral": uplift_vs_neutral,
        "uplift_seeded_optimized_vs_task_only": uplift_vs_task_only,
        "uplift_seeded_optimized_vs_random_spaces": uplift_vs_random,
        "uplift_unseeded_optimized_vs_neutral_493_behaviors": unseeded_uplift_vs_neutral,
        "missing_unseeded_behaviors": {
            "n_missing": len(missing_unseeded),
            "task_ids": missing_unseeded,
            "is_contiguous_blocks": True,
            "blocks": "0208-0215, 0313-0316, 0408-0414, 0513-0520 (tail ends of unseeded shards 2-5, which never finished)",
            "mean_prompt_len_chars_present": mean(present_prompt_lens),
            "mean_prompt_len_chars_missing": mean(missing_prompt_lens),
            "mean_advbench_row_index_present": mean(present_rows_idx),
            "mean_advbench_row_index_missing": mean(missing_rows_idx),
            "category_breakdown_missing": dict(missing_cat_counts),
            "interpretation": "Missingness is NOT random with respect to task_id/advbench_row (it is exactly the trailing portion of 4 shard ranges that did not finish), but prompt length is not obviously different. Category composition of the missing 27 roughly tracks the full-520 distribution (no single category is disproportionately missing) -- see category_breakdown_missing vs category_counts_all_520. Because missingness is structurally non-random (interrupted-shard tails, not simple-random-sample), the 8.92% unseeded ASR should be reported as '8.92% over the 493 completed behaviors (94.8% benchmark coverage)', NOT as an unbiased estimate of full-520 unseeded ASR.",
        },
    }
    (BASE / "GCG_7A_BEHAVIOR_ANALYSIS.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
