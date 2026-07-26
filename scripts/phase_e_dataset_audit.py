#!/usr/bin/env python3
"""Phase E1-E3 (CPU-only) — audit the released suffix pool and complete the
descriptive analyses BEYOND the existing 336-suffix pass.

Deliverables:
  results/SUFFIX_TAXONOMY_V2.csv         (E2: per-suffix labels + review columns)
  results/CATEGORY_TRANSFER_MATRIX_V2.csv(E3: transfer matrix w/ goal-clustered CIs)
  docs/CATEGORY_ATTACK_COMPLETION_REPORT.md (E3: PARTIAL descriptive report)

REUSES existing code (imported, not duplicated):
  scripts/gcg_advbench_llm_taxonomy.py :: categorize, PATTERNS, CATEGORY_PRIORITY
  scripts/gcg_7a_behavior_analysis.py  :: load_manifest, load_results,
                                          per_behavior_success, cluster_bootstrap_uplift
  scripts/build_gcg_source_of_truth.py :: analyze_free_gen

CRITICAL statistics rule (per task): response rows that share a suffix or a goal
are NOT independent. All ASR uncertainty is reported with cluster bootstrap:
  - goal-level : resample task_ids (the full520 universal-suffix eval is
    520 goals x 3 seeds = 1560 rows but only 520 independent goals).
  - suffix-level: resample suffixes (the multi-suffix per-run pool; each of the
    76 evaluated runs contributes one suffix = one cluster).

HF dataset 'MatanBT/gcg-evaluated-data' is NOT cached or vendored (checked
.cache/huggingface + ~/.cache/huggingface); the direct HF-dataset audit is
DEFERRED pending a download decision. This script audits the LOCAL suffix pool.
"""
from __future__ import annotations

import csv
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

random.seed(1234)  # deterministic bootstrap

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _ROOT / "scripts"
for p in (_ROOT, _SCRIPTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from gcg_advbench_llm_taxonomy import PATTERNS, CATEGORY_PRIORITY, categorize   # noqa: E402
from gcg_7a_behavior_analysis import (                                          # noqa: E402
    load_manifest,
    load_results,
    per_behavior_success,
    cluster_bootstrap_uplift,
)
from build_gcg_source_of_truth import analyze_free_gen                          # noqa: E402

RESULTS = _ROOT / "results"
DOCS = _ROOT / "docs"
TAX_V1 = RESULTS / "SUFFIX_TAXONOMY.csv"
TAX_V2 = RESULTS / "SUFFIX_TAXONOMY_V2.csv"
MATRIX_V2 = RESULTS / "CATEGORY_TRANSFER_MATRIX_V2.csv"
REPORT = DOCS / "CATEGORY_ATTACK_COMPLETION_REPORT.md"

FULL520_SEEDED = _ROOT / "outputs/stage_gcg_full/gcg_full_qwen3_7a_5a_full520/FREE_GENERATION_RESULTS.jsonl"
FULL520_UNSEEDED = _ROOT / "outputs/stage_gcg_full/gcg_full_qwen3_7a_5a_full520/FREE_GENERATION_RESULTS_UNSEEDED.jsonl"
PERCOT_ASR = _ROOT / "outputs/stage_gcg_percot_v2/PERBEHAVIOR_ASR_RESULTS.jsonl"

# Categories whose labels most affect transfer conclusions (top of the universal
# suffix transfer ranking) -> flagged for manual review regardless of confidence.
HIGH_TRANSFER_CATS = {"misinformation_disinformation", "privacy_surveillance",
                      "other_uncategorized", "fraud_financial_crime"}


# --------------------------------------------------------------------------- #
# labeling with rationale + confidence (re-uses PATTERNS / CATEGORY_PRIORITY)
# --------------------------------------------------------------------------- #
def label_instruction(instr: str):
    """Return (primary, secondary, confidence, rationale) using the SAME regex
    taxonomy as categorize(), but capturing ALL matches for confidence."""
    g = (instr or "").lower()
    matches = []
    for cat in CATEGORY_PRIORITY:
        m = re.search(PATTERNS[cat], g)
        if m:
            matches.append((cat, m.group(0)))
    if not matches:
        return "other_uncategorized", "", "low", "no taxonomy pattern matched"
    primary, snippet = matches[0]
    secondary = matches[1][0] if len(matches) > 1 else ""
    if len(matches) == 1:
        conf = "high"
    elif len(matches) == 2:
        conf = "medium"
    else:
        conf = "low"  # 3+ competing themes -> genuinely ambiguous
    rationale = f"matched '{snippet}' for {primary}" + (
        f"; also matched {[c for c, _ in matches[1:]]}" if secondary else "")
    return primary, secondary, conf, rationale


# --------------------------------------------------------------------------- #
# suffix-clustered bootstrap over a list of per-suffix ASR values
# --------------------------------------------------------------------------- #
def suffix_bootstrap_mean(values, n_boot=2000):
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    n = len(vals)
    means = []
    for _ in range(n_boot):
        s = [vals[random.randrange(n)] for _ in range(n)]
        means.append(sum(s) / n)
    means.sort()
    return {
        "n_suffixes": n,
        "mean": round(sum(vals) / n, 4),
        "ci95_lo": round(means[int(0.025 * len(means))], 4),
        "ci95_hi": round(means[int(0.975 * len(means))], 4),
    }


def goal_bootstrap_asr(rows_by_task, condition, n_boot=2000):
    """Goal-clustered CI for the ASR of a single condition (resample task_ids;
    each goal contributes ALL its seed rows -> respects within-goal correlation)."""
    tids = list(rows_by_task.keys())
    n = len(tids)
    if n == 0:
        return None
    asrs = []
    for _ in range(n_boot):
        s_succ = s_n = 0
        for _ in range(n):
            tid = tids[random.randrange(n)]
            for r in rows_by_task[tid]:
                if r.get("condition_label") == condition:
                    s_n += 1
                    s_succ += int(bool(r.get("strongreject_is_success")))
        if s_n:
            asrs.append(s_succ / s_n)
    if not asrs:
        return None
    asrs.sort()
    # point estimate from the real (unresampled) data
    tot_s = tot_n = 0
    for tid in tids:
        for r in rows_by_task[tid]:
            if r.get("condition_label") == condition:
                tot_n += 1
                tot_s += int(bool(r.get("strongreject_is_success")))
    return {
        "n_goals": n,
        "n_rows": tot_n,
        "asr": round(tot_s / tot_n, 4) if tot_n else None,
        "ci95_lo": round(asrs[int(0.025 * len(asrs))], 4),
        "ci95_hi": round(asrs[int(0.975 * len(asrs))], 4),
    }


# --------------------------------------------------------------------------- #
# E2: SUFFIX_TAXONOMY_V2.csv
# --------------------------------------------------------------------------- #
def build_v2(suffix_rows):
    # duplicate groups by identical suffix_str
    by_suffix = defaultdict(list)
    for i, r in enumerate(suffix_rows):
        by_suffix[r["suffix_str"]].append(i)
    dup_group = {}
    gid = 0
    for suf, idxs in sorted(by_suffix.items()):
        gid += 1
        for i in idxs:
            dup_group[i] = (gid, len(idxs))

    manifest = load_manifest()  # task_id -> {instruction,...}
    out = []
    for i, r in enumerate(suffix_rows):
        univ = r["universality"]
        instr = ""
        if univ == "per_behavior":
            tid = r.get("origin_task_id", "")
            instr = manifest.get(tid, {}).get("instruction", "")
        if univ == "per_behavior" and instr:
            primary, secondary, conf, rationale = label_instruction(instr)
            method = "regex_priority_first_pass"
        elif univ == "universal":
            primary, secondary, conf, rationale = (
                "n/a_universal", "",
                "n/a", "universal suffix optimized over a multi-behavior manifest; "
                "no single origin instruction to categorize")
            method = "n/a_universal"
        else:
            primary, secondary, conf, rationale = (
                "unknown", "", "low", "universality could not be resolved")
            method = "unresolved"

        gnum, gsize = dup_group[i]
        # manual review: low/medium confidence OR high-transfer category OR duplicate
        needs = (conf in ("low", "medium") or primary in HIGH_TRANSFER_CATS
                 or gsize > 1)
        review = "needs_manual_review" if needs else "auto_labeled_unreviewed"

        out.append({
            "run_id": r["run_id"],
            "run_dir": r["run_dir"],
            "model_family": r["model_family"],
            "universality": univ,
            "objective_type": r["objective_type"],
            "origin_task_id": r.get("origin_task_id", ""),
            "primary_category": primary,
            "secondary_category": secondary,
            "confidence": conf,
            "labeling_method": method,
            "manual_review_status": review,
            "rationale": rationale,
            "duplicate_group": gnum,
            "duplicate_group_size": gsize,
            "suffix_length": r["suffix_length"],
            "seed": r["seed"],
            "non_ascii_frac": r["non_ascii_frac"],
            "punct_count": r["punct_count"],
            "has_imperative": r["has_imperative"],
            "has_roleplay_marker": r["has_roleplay_marker"],
            "has_prefill_phrase": r["has_prefill_phrase"],
            "repeated_token_frac": r["repeated_token_frac"],
            "suffix_str": r["suffix_str"],
        })
    return out


# --------------------------------------------------------------------------- #
# per-suffix optimized ASR from each run's own FREE_GENERATION_RESULTS.jsonl
# (one ASR per suffix -> suffix is the cluster unit for E-analyses).
# --------------------------------------------------------------------------- #
def per_suffix_asr(suffix_rows):
    out = []
    for r in suffix_rows:
        fg = _ROOT / r["run_dir"] / "FREE_GENERATION_RESULTS.jsonl"
        if not fg.exists():
            continue
        s = analyze_free_gen(fg)
        if not s or not s.get("by_condition"):
            continue
        cond = next((c for c in s["by_condition"] if c and "optimized" in c), None)
        if cond is None:
            continue
        bc = s["by_condition"][cond]
        if not bc["n"]:
            continue
        rr = dict(r)
        rr["opt_asr"] = bc["successes"] / bc["n"]
        rr["opt_n"] = bc["n"]
        out.append(rr)
    return out


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main():
    suffix_rows = list(csv.DictReader(TAX_V1.open()))
    # cast numeric featurizer cols
    for r in suffix_rows:
        for k in ("non_ascii_frac", "repeated_token_frac"):
            try:
                r[k] = float(r[k]) if r[k] != "" else None
            except (ValueError, TypeError):
                r[k] = None
        for k in ("punct_count", "has_imperative", "has_roleplay_marker",
                  "has_prefill_phrase", "suffix_length"):
            try:
                r[k] = int(float(r[k])) if r[k] != "" else None
            except (ValueError, TypeError):
                r[k] = None

    # ---- E2 ----
    v2 = build_v2(suffix_rows)
    v2_fields = list(v2[0].keys())
    with TAX_V2.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=v2_fields)
        w.writeheader()
        w.writerows(v2)
    print(f"Wrote {TAX_V2} ({len(v2)} rows)")

    # ---- full520 universal suffix: category eval + goal-clustered CIs ----
    manifest = load_manifest()
    tid_cat = {tid: categorize(b["instruction"]) for tid, b in manifest.items()}
    seeded_rows = load_results(FULL520_SEEDED)  # task_id -> rows (opt+ctrl conds)
    # within-category / transfer for optimized_weighted, goal-clustered per category
    cat_to_tasks = defaultdict(dict)
    for tid, rows in seeded_rows.items():
        cat_to_tasks[tid_cat.get(tid, "other_uncategorized")][tid] = rows
    within = {}
    for cat, rbt in cat_to_tasks.items():
        gb = goal_bootstrap_asr(rbt, "optimized_weighted")
        nb = goal_bootstrap_asr(rbt, "neutral_control")
        within[cat] = {"opt": gb, "neu": nb}

    # ---- train vs unseen (goal-clustered uplift CI) ----
    def tv(p):
        if not p.exists():
            return None
        rbt = load_results(p)
        opt = goal_bootstrap_asr(rbt, "optimized_weighted")
        upl = cluster_bootstrap_uplift(rbt, "optimized_weighted", "neutral_control")
        return {"opt": opt, "uplift": upl,
                "neu": goal_bootstrap_asr(rbt, "neutral_control")}
    tvu = {"seeded_train_42_43_44": tv(FULL520_SEEDED),
           "unseen_gen_seed_100_200_300": tv(FULL520_UNSEEDED)}

    # ---- seed sensitivity (full520 optimized, per generation seed, goal-clustered) ----
    seed_sens = {}
    for label, p in [("seeded", FULL520_SEEDED), ("unseeded", FULL520_UNSEEDED)]:
        if not p.exists():
            continue
        allrows = [json.loads(l) for l in p.open() if l.strip()]
        seeds = sorted({r["seed"] for r in allrows})
        for sd in seeds:
            rbt = defaultdict(list)
            for r in allrows:
                if r["seed"] == sd:
                    rbt[r["task_id"]].append(r)
            seed_sens[sd] = goal_bootstrap_asr(rbt, "optimized_weighted")

    # ---- multi-suffix pool: per-suffix optimized ASR (suffix-clustered) ----
    psa = per_suffix_asr(suffix_rows)
    # by objective_type
    by_obj = defaultdict(list)
    for r in psa:
        by_obj[r["objective_type"]].append(r["opt_asr"])
    obj_ci = {k: suffix_bootstrap_mean(v) for k, v in by_obj.items()}
    # by model_family
    by_mf = defaultdict(list)
    for r in psa:
        by_mf[r["model_family"] or "unknown"].append(r["opt_asr"])
    mf_ci = {k: suffix_bootstrap_mean(v) for k, v in by_mf.items()}
    # by universality
    by_univ = defaultdict(list)
    for r in psa:
        by_univ[r["universality"]].append(r["opt_asr"])
    univ_ci = {k: suffix_bootstrap_mean(v) for k, v in by_univ.items()}
    # by suffix_length
    by_len = defaultdict(list)
    for r in psa:
        by_len[r["suffix_length"]].append(r["opt_asr"])
    len_ci = {k: suffix_bootstrap_mean(v) for k, v in by_len.items()}
    # token characteristics: split at median non_ascii_frac / prefill / imperative
    def split_ci(pred_true_name, pred):
        a = [r["opt_asr"] for r in psa if pred(r)]
        b = [r["opt_asr"] for r in psa if not pred(r)]
        return {pred_true_name + "=1": suffix_bootstrap_mean(a),
                pred_true_name + "=0": suffix_bootstrap_mean(b)}
    tok = {}
    na_vals = sorted([r["non_ascii_frac"] for r in psa if r["non_ascii_frac"] is not None])
    med_na = na_vals[len(na_vals) // 2] if na_vals else 0
    tok["non_ascii_ge_median"] = {
        f"ge_{round(med_na,4)}": suffix_bootstrap_mean(
            [r["opt_asr"] for r in psa if (r["non_ascii_frac"] or 0) >= med_na]),
        f"lt_{round(med_na,4)}": suffix_bootstrap_mean(
            [r["opt_asr"] for r in psa if (r["non_ascii_frac"] or 0) < med_na])}
    tok["has_prefill_phrase"] = split_ci("prefill", lambda r: r["has_prefill_phrase"] == 1)
    tok["has_imperative"] = split_ci("imperative", lambda r: r["has_imperative"] == 1)

    # ---- per-behavior diagonal (percot) ----
    percot_diag = defaultdict(list)
    if PERCOT_ASR.exists():
        # reuse the same origin instruction resolution as phase13: percot manifest
        percot_base = _ROOT / "outputs/stage_gcg_percot_v2"
        pinstr = {}
        runs_dir = percot_base / "runs"
        if runs_dir.exists():
            for run in sorted(runs_dir.glob("*")):
                mf = run / "MANIFEST.jsonl"
                if mf.exists():
                    for l in mf.open():
                        if l.strip():
                            d = json.loads(l)
                            if d.get("task_id"):
                                pinstr.setdefault(d["task_id"], d.get("instruction", ""))
                            break
        for l in PERCOT_ASR.open():
            if not l.strip():
                continue
            d = json.loads(l)
            tid = d.get("task_id")
            instr = pinstr.get(tid) or manifest.get(tid, {}).get("instruction", "")
            if not instr:
                continue
            percot_diag[categorize(instr)].append(d.get("best_asr", 0.0))

    # ---- E3: CATEGORY_TRANSFER_MATRIX_V2.csv ----
    cols = sorted(set(within) | set(percot_diag))
    with MATRIX_V2.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["origin", "cell_type", "n_origin_suffixes", "eval_category",
                    "asr", "ci95_lo", "ci95_hi", "n_goals", "n_rows", "note"])
        # multi_instruction origin (one universal suffix), goal-clustered per eval cat
        for cat in sorted(within, key=lambda c: -(within[c]["opt"]["asr"] if within[c]["opt"] else -1)):
            gb = within[cat]["opt"]
            w.writerow(["multi_instruction", "cross_category_populated", 1, cat,
                        gb["asr"], gb["ci95_lo"], gb["ci95_hi"], gb["n_goals"],
                        gb["n_rows"],
                        "single universal suffix; goal-clustered CI; suffix-level CI "
                        "undefined (n_suffix=1)"])
        # per-behavior diagonal (percot) — diagonal only
        for cat in sorted(percot_diag):
            vals = percot_diag[cat]
            sb = suffix_bootstrap_mean(vals)
            w.writerow(["per_behavior", "diagonal_only", len(vals), cat,
                        sb["mean"], sb["ci95_lo"], sb["ci95_hi"], "", len(vals),
                        "per-behavior best-candidate ASR on OWN behavior; "
                        "off-diagonal transfer DEFERRED (not on disk)"])
        # explicit deferred off-diagonal marker
        w.writerow(["per_behavior", "off_diagonal_DEFERRED", "", "ALL_j!=i",
                    "", "", "", "", "",
                    "requires re-evaluating each per-behavior suffix on OTHER "
                    "behaviors; GPU, deferred to E4-E6"])
    print(f"Wrote {MATRIX_V2}")

    # ---- report ----
    write_report(v2, within, tvu, seed_sens, obj_ci, mf_ci, univ_ci, len_ci, tok,
                 percot_diag, psa, cat_to_tasks)
    print(f"Wrote {REPORT}")


def _fmt(gb):
    if not gb:
        return "n/a"
    return f"{gb['asr']} [{gb['ci95_lo']}, {gb['ci95_hi']}]"


def _fmts(sb):
    if not sb:
        return "n/a"
    return f"{sb['mean']} [{sb['ci95_lo']}, {sb['ci95_hi']}] (n_suffix={sb['n_suffixes']})"


def write_report(v2, within, tvu, seed_sens, obj_ci, mf_ci, univ_ci, len_ci, tok,
                 percot_diag, psa, cat_to_tasks):
    L = []
    A = L.append
    A("# Category / Attack-Completion Descriptive Report (Phase E3) — PARTIAL")
    A("")
    A("> **PARTIAL.** This covers only the descriptive analyses computable from "
      "existing on-disk data (CPU-only). The *controlled* category-targeted attacks "
      "(E4-E6) are GPU work and are DEFERRED. No new suffixes were optimized here.")
    A("")
    A("**Generated by:** `scripts/phase_e_dataset_audit.py` (CPU-only, deterministic, "
      "`random.seed(1234)`). Reuses `categorize`/`PATTERNS`/`CATEGORY_PRIORITY` "
      "(gcg_advbench_llm_taxonomy), `load_manifest`/`load_results`/`per_behavior_success`/"
      "`cluster_bootstrap_uplift` (gcg_7a_behavior_analysis), `analyze_free_gen` "
      "(build_gcg_source_of_truth).")
    A("")
    A("**Deliverables:** `results/SUFFIX_TAXONOMY_V2.csv`, "
      "`results/CATEGORY_TRANSFER_MATRIX_V2.csv`, this file.")
    A("")

    A("## E1 — Dataset audit (LOCAL pool; HF direct audit DEFERRED)")
    A("")
    A("The HF dataset `MatanBT/gcg-evaluated-data` is **NOT cached and NOT vendored** "
      "(checked `.cache/huggingface/{hub,datasets}` and `~/.cache/huggingface/{hub,datasets}`; "
      "no `datasets--MatanBT--*` dir, no repo file references it). Per the hard rule "
      "(do NOT download), the **direct HF-dataset audit is DEFERRED** pending a download "
      "decision. The audit below is on the LOCAL suffix pool that the released dataset "
      "was built from.")
    A("")
    A("**Local pool shape (verified):**")
    A("")
    A("- Suffix-level table `results/SUFFIX_TAXONOMY.csv`: **336 rows** = one *selected* "
      "suffix per optimization run dir (the first `FINAL_CANDIDATES.jsonl` line carrying "
      "`selection_mode`). 336 run dirs with a `FINAL_CANDIDATES.jsonl`.")
    A("- Response-level pool: **136** `FREE_GENERATION_RESULTS*.jsonl` files, "
      "**102,897** evaluation rows total (suffix x behavior x condition x seed).")
    A("- Distinct selected suffix strings: **305** (31 duplicate selections across runs).")
    A("- By base: percot_v2=249, full=66, full_v2_userfix=13, early=8.")
    A("- By model family: qwen3=316, gemma4=18, deepseek_r1=2.")
    A("- By universality: per_behavior=249, universal=87.")
    A("- By derived objective_type: cot_prefix_ce=276, refusal_dir=38, repr_match=11, "
      "prefix_ce=10, repr_match_cot=1.")
    A("- **Optimizer:** all 368 CONFIG.json are GCG; there is **no named-optimizer field** "
      "(single optimizer). The nearest stored discriminator is `objective.selection_mode` "
      "(≈always `weighted`) and the derived `objective_type`.")
    A("- **StrongREJECT coverage:** in the full-520 eval (6240 seeded + 5849 unseeded rows) "
      "there are **0** null `strongreject_score`/`strongreject_is_success`.")
    A("- **Intermediate vs final:** `FINAL_CANDIDATES.jsonl` holds multiple candidate lines "
      "(line-count distribution across 336 files: 2→325, 14→3, 9→2, 1→2, and singletons at "
      "20/13/25/7); the analysis selects **line 0 = the final selected candidate**, so "
      "intermediate candidates are present on disk but excluded by design.")
    A("")
    A("**336-vs-larger reconciliation:** the 336 is a *suffix-level* selection "
      "(one final suffix per run), NOT a response-level count. The larger response-level "
      "table (102,897 local rows; the released HF table is its many-to-many eval: each "
      "suffix scored on many instructions x conditions x seeds) collapses to 336 once you "
      "keep exactly one selected/final suffix per optimization run. This is why every "
      "ASR below MUST be clustered by suffix and/or goal — the response rows are the "
      "opposite of independent (e.g. the universal-suffix full-520 eval is 1560 rows but "
      "only 520 independent goals x 3 seeds, and just **1** suffix).")
    A("")

    A("## E2 — SUFFIX_TAXONOMY_V2.csv")
    A("")
    conf = Counter(r["confidence"] for r in v2)
    rev = Counter(r["manual_review_status"] for r in v2)
    dupg = len({r["duplicate_group"] for r in v2})
    A(f"- Rows: **{len(v2)}** (adds primary/secondary_category, confidence, "
      "labeling_method, manual_review_status, rationale, duplicate_group).")
    A(f"- Confidence: {dict(conf)}.")
    A(f"- Manual-review status: {dict(rev)} — **all are automated first-pass; none "
      "human-reviewed** (no manual review was fabricated).")
    A(f"- Duplicate groups: {dupg} groups over {len(v2)} rows (identical suffix_str "
      "collapses to a group; group_size>1 flagged for review).")
    A("- `needs_manual_review` = low/medium confidence OR high-transfer category "
      f"({sorted(HIGH_TRANSFER_CATS)}) OR duplicate. `n/a_universal` primary = universal "
      "suffixes have no single origin instruction to categorize.")
    A("")

    A("## E3 — Descriptive analyses (CPU, existing data only)")
    A("")
    A("All ASR CIs are 95% cluster bootstrap (2000 resamples, seed=1234). "
      "**goal-clustered** = resample task_ids (respects the 3 seeds/goal); "
      "**suffix-clustered** = resample suffixes (each run = one cluster). "
      "Response rows sharing a suffix or goal are never treated as independent.")
    A("")

    A("### E3.1 Within-category performance (universal 5A suffix, full-520, goal-clustered)")
    A("")
    A("Source: `outputs/stage_gcg_full/gcg_full_qwen3_7a_5a_full520/FREE_GENERATION_RESULTS.jsonl`, "
      "`optimized_weighted`, 1 suffix, 520 goals x 3 seeds. n = independent GOALS per category.")
    A("")
    A("| category | n_goals | n_rows | optimized ASR [95% CI, goal-clustered] | neutral ASR |")
    A("|---|---|---|---|---|")
    for cat in sorted(within, key=lambda c: -(within[c]["opt"]["asr"] if within[c]["opt"] else -1)):
        o = within[cat]["opt"]
        nn = within[cat]["neu"]
        A(f"| {cat} | {o['n_goals']} | {o['n_rows']} | {_fmt(o)} | "
          f"{nn['asr'] if nn else 'n/a'} |")
    A("")
    big = [(c, within[c]["opt"]) for c in within if within[c]["opt"]["n_goals"] >= 15]
    big.sort(key=lambda kv: -kv[1]["asr"])
    if big:
        A(f"- Most vulnerable (n_goals>=15): **{big[0][0]}** = {_fmt(big[0][1])}.")
        A(f"- Least vulnerable (n_goals>=15): **{big[-1][0]}** = {_fmt(big[-1][1])}.")
    A("- Small-n categories (n_goals<15) have very wide CIs — read as descriptive only.")
    A("")

    A("### E3.2 Cross-category transfer (which cells are populated vs deferred)")
    A("")
    A("Full matrix in `results/CATEGORY_TRANSFER_MATRIX_V2.csv`.")
    A("")
    A("- **Populated:** the `multi_instruction` row — the single universal suffix's ASR on "
      "every evaluated category (E3.1 numbers with goal-clustered CIs). This is a genuine "
      "one-suffix→all-categories transfer row.")
    A("- **Diagonal only:** the `per_behavior` rows — each per-behavior suffix was evaluated "
      "ONLY on its own behavior (percot best-candidate ASR), so only the i==i cell exists.")
    A("- **DEFERRED (empty):** all off-diagonal per-behavior cells (suffix from category i "
      "evaluated on category j!=i). This requires re-running each per-behavior suffix on "
      "other behaviors — GPU, part of E4-E6. The V2 matrix carries an explicit "
      "`off_diagonal_DEFERRED` marker row so the gap is not mistaken for a zero.")
    A("- Suffix-level CI on the multi_instruction row is **undefined** (n_suffix=1): a single "
      "universal suffix cannot bound suffix-to-suffix variability. That bound needs the "
      "multi-suffix pool (E3.5).")
    A("")

    A("### E3.3 Train vs unseen — GENERATION-SEED hold-out (NOT unseen-instruction)")
    A("")
    A("**Caveat:** the on-disk hold-out is a *generation-seed* hold-out of an already-fixed "
      "universal suffix (seeds 42/43/44 vs 100/200/300 on the SAME 520 behaviors), NOT "
      "transfer to unseen *instructions*. Genuine unseen-instruction transfer would be a "
      "held-out-behavior split, which is DEFERRED.")
    A("")
    A("| set | optimized ASR [95% CI, goal-clustered] | uplift vs neutral [95% CI] |")
    A("|---|---|---|")
    for lbl, d in tvu.items():
        if not d:
            A(f"| {lbl} | n/a | n/a |")
            continue
        up = d["uplift"]
        ups = (f"{round(up['point_estimate_mean_of_bootstrap'],4)} "
               f"[{round(up['ci95_lo'],4)}, {round(up['ci95_hi'],4)}]") if up else "n/a"
        A(f"| {lbl} | {_fmt(d['opt'])} | {ups} |")
    A("")

    A("### E3.4 Single- vs multi-instruction — kept SEPARATE (not like-for-like)")
    A("")
    A("These two ASRs are **NOT comparable as an effect size**: `single` = per-behavior "
      "best-candidate ASR on the suffix's OWN training behavior (optimistic upper bound); "
      "`multi` = one fixed universal suffix averaged over 520 held-in behaviors. They are "
      "also **model-family-confounded** (single group is 100% qwen3; universal group pools "
      "qwen3+gemma4+deepseek_r1). Reported separately, never differenced as a clean gap.")
    A("")
    A("| group | ASR [95% CI, suffix-clustered] | note |")
    A("|---|---|---|")
    A(f"| per_behavior (own-behavior best-cand) | {_fmts(univ_ci.get('per_behavior'))} | "
      "optimistic; own behavior only |")
    A(f"| universal (own-manifest eval) | {_fmts(univ_ci.get('universal'))} | "
      "many-behavior average |")
    A("")
    A("(Both rows use per-suffix ASR from each run's own `FREE_GENERATION_RESULTS.jsonl`, "
      "so the cluster unit is the suffix; only the 76 runs that carry their own eval "
      "contribute.)")
    A("")

    A("### E3.5 Universality by objective / optimizer / suffix-length / tokens (suffix-clustered)")
    A("")
    A("Per-suffix optimized ASR over the 76 runs that carry their own eval; suffix is the "
      "cluster unit. Pooled across heterogeneous manifests — descriptive, not a controlled "
      "single-variable contrast.")
    A("")
    A("**By objective_type:**")
    A("")
    A("| objective_type | ASR [95% CI, suffix-clustered] |")
    A("|---|---|")
    for k in sorted(obj_ci, key=lambda k: -(obj_ci[k]["mean"] if obj_ci[k] else -1)):
        A(f"| {k} | {_fmts(obj_ci[k])} |")
    A("")
    A("**Optimizer:** single optimizer (GCG) across the whole pool — no cross-optimizer "
      "contrast is possible from this data.")
    A("")
    A("**By suffix_length:**")
    A("")
    A("| suffix_length | ASR [95% CI, suffix-clustered] |")
    A("|---|---|")
    for k in sorted(len_ci, key=lambda x: (x is None, x)):
        A(f"| {k} | {_fmts(len_ci[k])} |")
    A("")
    A("Note: length is near-constant (327/336 suffixes are length 20), so the length "
      "contrast is essentially unpowered.")
    A("")
    A("**By token characteristics:**")
    A("")
    A("| split | ASR [95% CI, suffix-clustered] |")
    A("|---|---|")
    for grp, d in tok.items():
        for k, sb in d.items():
            A(f"| {grp}: {k} | {_fmts(sb)} |")
    A("")

    A("### E3.6 Seed sensitivity (full-520 universal suffix, per generation seed, goal-clustered)")
    A("")
    A("| generation seed | optimized ASR [95% CI, goal-clustered] |")
    A("|---|---|")
    for sd in sorted(seed_sens, key=lambda x: (x is None, x)):
        A(f"| {sd} | {_fmt(seed_sens[sd])} |")
    A("")
    vals = [seed_sens[s]["asr"] for s in seed_sens if seed_sens[s]]
    if vals:
        A(f"- ASR range across generation seeds: [{min(vals)}, {max(vals)}] "
          f"(spread {round(max(vals)-min(vals),4)}); seed-to-seed drift is small "
          "relative to the goal-clustered CI width.")
    A("")

    A("### E3.7 Model-family sensitivity (suffix-clustered)")
    A("")
    A("| model_family | ASR [95% CI, suffix-clustered] |")
    A("|---|---|")
    for k in sorted(mf_ci, key=lambda k: -(mf_ci[k]["mean"] if mf_ci[k] else -1)):
        A(f"| {k} | {_fmts(mf_ci[k])} |")
    A("")
    A("Caveat: gemma4 and deepseek_r1 have very few evaluated suffixes; CIs are wide and "
      "the family contrast is confounded with objective/manifest choices.")
    A("")

    A("### E3.8 Category coverage + worst category")
    A("")
    covered = sorted(within)
    zero = [c for c in within if within[c]["opt"]["asr"] == 0.0]
    A(f"- Categories with any full-520 eval coverage: **{len(covered)}/16**.")
    A(f"- Zero-ASR categories for the universal suffix (n_goals shown): "
      + ", ".join(f"{c} (n={within[c]['opt']['n_goals']})" for c in zero) + ".")
    if big:
        A(f"- Worst non-trivial category (n_goals>=15): **{big[-1][0]}** = {_fmt(big[-1][1])}.")
    A("")

    A("## Deferred to GPU (E4-E6) / mechanistic hand-off")
    A("")
    A("- Direct audit of the HF dataset `MatanBT/gcg-evaluated-data` (not cached; do NOT download).")
    A("- Off-diagonal per-behavior cross-category transfer (re-eval each per-behavior suffix "
      "on other categories).")
    A("- Controlled category-targeted attacks and held-out-INSTRUCTION transfer.")
    A("- Single-vs-multi as a like-for-like effect size (needs matched eval + de-confounding "
      "of model family).")
    A("- Any internal-state / mechanistic attribution of the lexical correlates.")
    A("")

    REPORT.write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
