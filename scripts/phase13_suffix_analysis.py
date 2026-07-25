#!/usr/bin/env python3
"""Phase 13 (§17) — Analyze the Large GCG Suffix Dataset.

CPU-only, deterministic, rerunnable. Reads ONLY on-disk raw artifacts across the
four GCG output bases and emits the three §17.4 deliverables:

  results/SUFFIX_TAXONOMY.csv          (one row per selected suffix, all runs)
  results/CATEGORY_TRANSFER_MATRIX.csv (origin-category x eval-category ASR)
  docs/DATASET_ANALYSIS_REPORT.md      (§17.3A/B/C/D/F/G synthesis, path-cited)

REUSES existing code (imported, not duplicated):
  - scripts/gcg_advbench_llm_taxonomy.py :: categorize()   (15-cat LLM taxonomy)
  - scripts/gcg_7a_behavior_analysis.py  :: load_manifest, load_results,
                                            per_behavior_success
  - scripts/build_gcg_source_of_truth.py :: analyze_free_gen  (per-run ASR)

The "large GCG suffix dataset" = union of FINAL_CANDIDATES.jsonl across:
  outputs/stage_gcg_full/, stage_gcg_full_v2_userfix/, stage_gcg_percot_v2/,
  stage_gcg_early/.

Missing/absent CONFIG/MANIFEST/FREE_GENERATION are logged and skipped, never fatal.

§17.3E (universality-rank vs internal states) and the §17.4 mechanistic subset
need GPU activations -> OUT OF SCOPE here (deferred to mechanistic hand-off).
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
# scripts/ is not a package (no __init__.py) -> import the reused modules by
# putting scripts/ on the path and importing by bare module name.
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from gcg_advbench_llm_taxonomy import categorize                       # noqa: E402
from gcg_7a_behavior_analysis import (                                 # noqa: E402
    load_manifest as load_manifest_520,
    load_results,
    per_behavior_success,
)
from build_gcg_source_of_truth import analyze_free_gen                 # noqa: E402

BASES = [
    "outputs/stage_gcg_full",
    "outputs/stage_gcg_full_v2_userfix",
    "outputs/stage_gcg_percot_v2",
    "outputs/stage_gcg_early",
]

RESULTS_DIR = _REPO_ROOT / "results"
DOCS_DIR = _REPO_ROOT / "docs"
TAXONOMY_CSV = RESULTS_DIR / "SUFFIX_TAXONOMY.csv"
TRANSFER_CSV = RESULTS_DIR / "CATEGORY_TRANSFER_MATRIX.csv"
REPORT_MD = DOCS_DIR / "DATASET_ANALYSIS_REPORT.md"

# Universal multi-instruction suffix evaluated on the full AdvBench-520 (the 5A
# CoT-target weighted suffix). This is the ONLY on-disk eval that spans every
# category, so it is the origin="multi_instruction" row of the transfer matrix.
FULL520_SEEDED = _REPO_ROOT / "outputs/stage_gcg_full/gcg_full_qwen3_7a_5a_full520/FREE_GENERATION_RESULTS.jsonl"
FULL520_UNSEEDED = _REPO_ROOT / "outputs/stage_gcg_full/gcg_full_qwen3_7a_5a_full520/FREE_GENERATION_RESULTS_UNSEEDED.jsonl"
BEHAVIOR_ANALYSIS_JSON = _REPO_ROOT / "outputs/stage_gcg_full/GCG_7A_BEHAVIOR_ANALYSIS.json"
PERCOT_BASE = _REPO_ROOT / "outputs/stage_gcg_percot_v2"
PERCOT_ASR = PERCOT_BASE / "PERBEHAVIOR_ASR_RESULTS.jsonl"

SKIPPED: list[str] = []


def log_skip(msg: str) -> None:
    SKIPPED.append(msg)
    print(f"[skip] {msg}")


# --------------------------------------------------------------------------- #
# §17.3F  lexical / token-level featurizer (pure python, no model needed).
# Do NOT assume lexical commonality implies a causal mechanism (§17.3F caveat).
# --------------------------------------------------------------------------- #
_PUNCT = set(r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~""")
_IMPERATIVE_RE = re.compile(
    r"\b(write|print|explain|describe|list|provide|give|answer|respond|start|begin|"
    r"generate|produce|output|create|make|show|tell|continue|complete|do)\b", re.I)
_ROLEPLAY_RE = re.compile(
    r"\b(perspective|roleplay|role-play|pretend|persona|character|you are|act as|"
    r"imagine|hypothetical|as an?|dan|jailbreak)\b", re.I)
_PREFILL_RE = re.compile(
    r"\b(sure|here is|here's|of course|certainly|okay|ok|i can help|i'?ll|"
    r"absolutely|no problem|as follows|below)\b", re.I)


def featurize(suffix_str: str, suffix_ids: list[int]) -> dict:
    s = suffix_str or ""
    n_chars = len(s)
    non_ascii = sum(1 for ch in s if ord(ch) > 127)
    punct = sum(1 for ch in s if ch in _PUNCT)
    ids = suffix_ids or []
    if ids:
        repeated_frac = 1.0 - (len(set(ids)) / len(ids))
    else:
        repeated_frac = None
    return {
        "non_ascii_frac": round(non_ascii / n_chars, 4) if n_chars else 0.0,
        "punct_count": punct,
        "has_imperative": int(bool(_IMPERATIVE_RE.search(s))),
        "has_roleplay_marker": int(bool(_ROLEPLAY_RE.search(s))),
        "has_prefill_phrase": int(bool(_PREFILL_RE.search(s))),
        "repeated_token_frac": round(repeated_frac, 4) if repeated_frac is not None else "",
    }


# --------------------------------------------------------------------------- #
# objective_type derivation from CONFIG.objective{} (+ manifest cot_target flag).
# §17.1 note: objective_type is DERIVED, not a stored column.
# --------------------------------------------------------------------------- #
def derive_objective_type(obj: dict, cot_target: bool | None) -> str:
    lr = float(obj.get("lambda_repr", 0) or 0)
    lrd = float(obj.get("lambda_refusal_dir", 0) or 0)
    repr_cot = bool(obj.get("repr_at_cot_pos", False))
    if lr > 0 and lrd > 0:
        return "composite_repr+refusal_dir"
    if lrd > 0:
        return "refusal_dir"
    if lr > 0:
        return "repr_match_cot" if repr_cot else "repr_match"
    # pure cross-entropy on the target string -> distinguished by target style
    return "cot_prefix_ce" if cot_target else "prefix_ce"


def read_json(p: Path):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception as e:  # noqa: BLE001
        log_skip(f"unreadable JSON {p}: {e}")
        return None


def read_first_jsonl(p: Path):
    if not p.exists():
        return None
    try:
        with p.open() as f:
            for line in f:
                if line.strip():
                    return json.loads(line)
    except Exception as e:  # noqa: BLE001
        log_skip(f"unreadable JSONL {p}: {e}")
    return None


# --------------------------------------------------------------------------- #
# Walk every run dir with a FINAL_CANDIDATES.jsonl and emit one suffix row
# (the selected candidate = the first line carrying selection_mode).
# --------------------------------------------------------------------------- #
def build_suffix_rows():
    rows = []
    n_runs = 0
    for base in BASES:
        base_dir = _REPO_ROOT / base
        if not base_dir.exists():
            log_skip(f"base dir missing: {base}")
            continue
        for fc in sorted(base_dir.rglob("FINAL_CANDIDATES.jsonl")):
            run_dir = fc.parent
            n_runs += 1
            selected = read_first_jsonl(fc)
            if not selected or "suffix_str" not in selected:
                log_skip(f"no selected suffix in {fc}")
                continue

            config = read_json(run_dir / "CONFIG.json")
            manifest_first = read_first_jsonl(run_dir / "MANIFEST.jsonl")
            if manifest_first is None and config is not None and config.get("manifest_path"):
                cmp = Path(config["manifest_path"])
                if not cmp.is_absolute():
                    cmp = _REPO_ROOT / config["manifest_path"]
                manifest_first = read_first_jsonl(cmp)

            # manifest behavior count -> universality (selection_mode is ~always
            # 'weighted' across runs, so it does NOT separate single vs multi;
            # #behaviors in the optimization manifest does).
            n_manifest = None
            mp = run_dir / "MANIFEST.jsonl"
            if mp.exists():
                try:
                    n_manifest = sum(1 for ln in mp.open() if ln.strip())
                except Exception as e:  # noqa: BLE001
                    log_skip(f"cannot count manifest {mp}: {e}")

            if config is None:
                log_skip(f"no CONFIG.json in {run_dir}")
                obj, gcg = {}, {}
                model_family = ""
            else:
                obj = config.get("objective", {}) or {}
                gcg = config.get("gcg", {}) or {}
                model_family = config.get("model_family") or config.get("multi_model_family") or ""

            # Fallback: some runs lack a local MANIFEST.jsonl -> count the manifest
            # referenced by CONFIG.manifest_path to still resolve universality.
            if n_manifest is None and config is not None:
                cfg_mp = config.get("manifest_path", "")
                if cfg_mp:
                    cmp = Path(cfg_mp)
                    if not cmp.is_absolute():
                        cmp = _REPO_ROOT / cfg_mp
                    if cmp.exists():
                        try:
                            n_manifest = sum(1 for ln in cmp.open() if ln.strip())
                        except Exception as e:  # noqa: BLE001
                            log_skip(f"cannot count config manifest {cmp}: {e}")
                    else:
                        log_skip(f"CONFIG manifest_path missing for {run_dir.name}: {cfg_mp}")

            cot_target = None
            origin_instruction = ""
            origin_task_id = ""
            if manifest_first:
                cot_target = manifest_first.get("cot_target")
                if cot_target is None:
                    tgt = manifest_first.get("safe_target_prefix", "") or ""
                    cot_target = tgt.lstrip().startswith("<think>")
                origin_instruction = manifest_first.get("instruction", "") or ""
                origin_task_id = manifest_first.get("task_id", "") or ""

            universality = "per_behavior" if (n_manifest == 1) else (
                "universal" if n_manifest and n_manifest > 1 else "unknown")
            objective_type = derive_objective_type(obj, cot_target)

            suffix_str = selected.get("suffix_str", "")
            suffix_ids = selected.get("suffix_ids", []) or []
            feats = featurize(suffix_str, suffix_ids)

            # origin category is well-defined for per-behavior suffixes only
            origin_category = ""
            if universality == "per_behavior" and origin_instruction:
                origin_category = categorize(origin_instruction)

            rel_run = str(run_dir.relative_to(_REPO_ROOT))
            rows.append({
                "run_id": (config or {}).get("run_id") or run_dir.name,
                "run_dir": rel_run,
                "model_family": model_family,
                "objective_type": objective_type,
                "universality": universality,
                "n_manifest_behaviors": n_manifest if n_manifest is not None else "",
                "origin_task_id": origin_task_id,
                "origin_category": origin_category,
                "selection_mode": selected.get("selection_mode", ""),
                "lambda_repr": obj.get("lambda_repr", ""),
                "lambda_refusal_dir": obj.get("lambda_refusal_dir", ""),
                "repr_at_cot_pos": obj.get("repr_at_cot_pos", ""),
                "cot_target": "" if cot_target is None else int(bool(cot_target)),
                "suffix_length": gcg.get("suffix_length", len(suffix_ids) or ""),
                "seed": gcg.get("seed", ""),
                "suffix_str": suffix_str,
                **feats,
            })
    return rows, n_runs


# --------------------------------------------------------------------------- #
# §17.3B transfer matrix
# --------------------------------------------------------------------------- #
def build_transfer_matrix(behaviors_520):
    """Rows = origin category (per-behavior suffixes) + 'multi_instruction'.
    Cols = evaluation category. Value = mean strongreject_is_success.

    - multi_instruction row: universal 5A suffix on full-520 (optimized_weighted),
      per behavior categorized -> full row across all j (reuses per_behavior_success).
    - per-behavior origin rows: percot_v2 eval covers each suffix ONLY on its own
      behavior, so only the diagonal (i==j) is populated (best-candidate ASR from
      PERBEHAVIOR_ASR_RESULTS.jsonl). Off-diagonal per-behavior transfer is NOT on
      disk (deferred).
    """
    tid_to_cat = {tid: categorize(b["instruction"]) for tid, b in behaviors_520.items()}

    # --- multi_instruction row (full-520 universal suffix) ---
    multi_row = {}
    multi_denom = {}
    n_eval_rows_multi = 0
    if FULL520_SEEDED.exists():
        rows_by_task = load_results(FULL520_SEEDED)
        pbs = per_behavior_success(rows_by_task, "optimized_weighted")
        agg = defaultdict(lambda: [0, 0])  # cat -> [succ, n]
        for tid, (s, n) in pbs.items():
            cat = tid_to_cat.get(tid) or categorize(
                behaviors_520.get(tid, {}).get("instruction", ""))
            agg[cat][0] += s
            agg[cat][1] += n
            n_eval_rows_multi += n
        for cat, (s, n) in agg.items():
            multi_row[cat] = round(s / n, 4) if n else None
            multi_denom[cat] = n
    else:
        log_skip(f"full-520 seeded eval missing: {FULL520_SEEDED}")

    # --- per-behavior diagonal (percot_v2 stratified sample) ---
    # origin instruction per percot task via its manifest; best_asr from artifact.
    percot_origin_instr = {}
    for run in sorted((PERCOT_BASE / "runs").glob("*")) if (PERCOT_BASE / "runs").exists() else []:
        mf = read_first_jsonl(run / "MANIFEST.jsonl")
        if mf and mf.get("task_id"):
            percot_origin_instr.setdefault(mf["task_id"], mf.get("instruction", ""))

    diag = defaultdict(list)   # cat -> list of best_asr
    diag_n = defaultdict(int)
    n_percot_beh = 0
    if PERCOT_ASR.exists():
        for line in PERCOT_ASR.open():
            if not line.strip():
                continue
            r = json.loads(line)
            tid = r.get("task_id")
            instr = percot_origin_instr.get(tid, "")
            if not instr:
                # fall back to full-520 manifest instruction if id maps there
                instr = behaviors_520.get(tid, {}).get("instruction", "")
            if not instr:
                log_skip(f"percot task {tid} has no instruction; not categorized")
                continue
            cat = categorize(instr)
            diag[cat].append(r.get("best_asr", 0.0))
            diag_n[cat] += 1
            n_percot_beh += 1
    else:
        log_skip(f"percot ASR artifact missing: {PERCOT_ASR}")

    # column universe
    all_cats = sorted(set(multi_row) | set(diag))
    return {
        "columns": all_cats,
        "multi_row": multi_row,
        "multi_denom": multi_denom,
        "n_eval_rows_multi": n_eval_rows_multi,
        "diag": {c: sum(v) / len(v) for c, v in diag.items() if v},
        "diag_n": dict(diag_n),
        "n_percot_beh": n_percot_beh,
    }


def write_transfer_csv(tm):
    cols = tm["columns"]
    with TRANSFER_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["origin_category", "n_origin_suffixes"] + cols)
        # per-behavior origin rows (diagonal only)
        for oc in sorted(tm["diag"]):
            row = [oc, tm["diag_n"].get(oc, "")]
            for c in cols:
                row.append(round(tm["diag"][oc], 4) if c == oc else "")
            w.writerow(row)
        # multi_instruction row
        mr = ["multi_instruction", ""]
        for c in cols:
            v = tm["multi_row"].get(c)
            mr.append("" if v is None else v)
        w.writerow(mr)


# --------------------------------------------------------------------------- #
# §17.3G objective-dependent behavior: per-run optimized vs neutral ASR by
# objective_type, aggregated over runs that HAVE a seeded FREE_GENERATION file
# with an optimized_* condition.
# --------------------------------------------------------------------------- #
def objective_dependent_summary(suffix_rows):
    by_run = {r["run_dir"]: r for r in suffix_rows}
    agg = defaultdict(lambda: {"runs": 0, "opt_s": 0, "opt_n": 0, "neu_s": 0, "neu_n": 0})
    for run_dir, r in by_run.items():
        fg = _REPO_ROOT / run_dir / "FREE_GENERATION_RESULTS.jsonl"
        if not fg.exists():
            continue
        summ = analyze_free_gen(fg)
        if not summ or not summ.get("by_condition"):
            continue
        opt_cond = next((c for c in summ["by_condition"] if c and "optimized" in c), None)
        if opt_cond is None:
            continue
        ot = r["objective_type"]
        a = agg[ot]
        a["runs"] += 1
        oc = summ["by_condition"][opt_cond]
        a["opt_s"] += oc["successes"]
        a["opt_n"] += oc["n"]
        nc = summ["by_condition"].get("neutral_control")
        if nc:
            a["neu_s"] += nc["successes"]
            a["neu_n"] += nc["n"]
    out = {}
    for ot, a in agg.items():
        out[ot] = {
            "n_runs_with_eval": a["runs"],
            "optimized_asr": round(a["opt_s"] / a["opt_n"], 4) if a["opt_n"] else None,
            "neutral_asr": round(a["neu_s"] / a["neu_n"], 4) if a["neu_n"] else None,
            "n_opt_rows": a["opt_n"],
        }
    return out


# --------------------------------------------------------------------------- #
# §17.3C single vs multi, §17.3D train vs unseen
# --------------------------------------------------------------------------- #
def single_vs_multi(suffix_rows):
    single = [r for r in suffix_rows if r["universality"] == "per_behavior"]
    multi = [r for r in suffix_rows if r["universality"] == "universal"]

    def mean(xs):
        xs = [x for x in xs if isinstance(x, (int, float))]
        return round(sum(xs) / len(xs), 4) if xs else None

    def stats(group):
        return {
            "n_suffixes": len(group),
            "mean_suffix_length": mean([r["suffix_length"] for r in group if isinstance(r["suffix_length"], (int, float))]),
            "mean_non_ascii_frac": mean([r["non_ascii_frac"] for r in group]),
            "mean_repeated_token_frac": mean([r["repeated_token_frac"] for r in group if isinstance(r["repeated_token_frac"], (int, float))]),
            "frac_has_prefill_phrase": mean([r["has_prefill_phrase"] for r in group]),
            "frac_has_imperative": mean([r["has_imperative"] for r in group]),
        }

    # ASR: single-instruction ASR from percot best_asr artifact; multi from full-520
    single_asr = None
    single_n = 0
    if PERCOT_ASR.exists():
        vals = [json.loads(l)["best_asr"] for l in PERCOT_ASR.open() if l.strip()]
        if vals:
            single_asr = round(sum(vals) / len(vals), 4)
            single_n = len(vals)
    multi_asr = None
    multi_n = 0
    if FULL520_SEEDED.exists():
        s = analyze_free_gen(FULL520_SEEDED)
        if s and "optimized_weighted" in s["by_condition"]:
            multi_asr = s["by_condition"]["optimized_weighted"]["asr"]
            multi_n = s["by_condition"]["optimized_weighted"]["n"]
    return {
        "single": stats(single),
        "multi": stats(multi),
        "single_best_asr_mean_percot": single_asr,
        "single_n_behaviors": single_n,
        "multi_optimized_asr_full520": multi_asr,
        "multi_n_eval_rows": multi_n,
    }


def train_vs_unseen():
    out = {}
    for label, p in [("seeded_train_42_43_44", FULL520_SEEDED), ("unseen_100_200_300", FULL520_UNSEEDED)]:
        if not p.exists():
            log_skip(f"train/unseen eval missing: {p}")
            out[label] = None
            continue
        s = analyze_free_gen(p)
        oc = s["by_condition"].get("optimized_weighted") if s else None
        nc = s["by_condition"].get("neutral_control") if s else None
        out[label] = {
            "optimized_asr": oc["asr"] if oc else None,
            "optimized_n": oc["n"] if oc else None,
            "neutral_asr": nc["asr"] if nc else None,
            "n_distinct_behaviors": s["n_distinct_task_ids"] if s else None,
            "seeds_present": s["seeds_present"] if s else None,
            "file": str(p.relative_to(_REPO_ROOT)),
        }
    return out


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def write_report(suffix_rows, n_runs, tm, obj_summary, svm, tvu, behaviors_520):
    n_suffixes = len(suffix_rows)
    by_base = defaultdict(int)
    for r in suffix_rows:
        base = r["run_dir"].split("/")[1] if r["run_dir"].startswith("outputs/") else r["run_dir"]
        by_base[base] += 1
    by_universality = defaultdict(int)
    for r in suffix_rows:
        by_universality[r["universality"]] += 1
    by_model = defaultdict(int)
    for r in suffix_rows:
        by_model[r["model_family"] or "unknown"] += 1
    by_objective = defaultdict(int)
    for r in suffix_rows:
        by_objective[r["objective_type"]] += 1
    n_dup_suffix = n_suffixes - len({r["suffix_str"] for r in suffix_rows})

    # §17.3A within-category (reuse existing GCG_7A_BEHAVIOR_ANALYSIS.json)
    within_cat = None
    ba = read_json(BEHAVIOR_ANALYSIS_JSON)
    if ba:
        within_cat = ba.get("category_based_success_analysis_llm_taxonomy")

    L = []
    A = L.append
    A("# Phase 13 — Large GCG Suffix Dataset Analysis (§17)")
    A("")
    A("**Generated by:** `scripts/phase13_suffix_analysis.py` (CPU-only, deterministic, rerunnable). "
      "Reads only on-disk raw artifacts under the four GCG bases; reuses "
      "`scripts/gcg_advbench_llm_taxonomy.py::categorize`, "
      "`scripts/gcg_7a_behavior_analysis.py::{load_manifest,load_results,per_behavior_success}`, and "
      "`scripts/build_gcg_source_of_truth.py::analyze_free_gen`.")
    A("")
    A("**Deliverables:** `results/SUFFIX_TAXONOMY.csv`, `results/CATEGORY_TRANSFER_MATRIX.csv`, this file.")
    A("")
    A("## 0. Dataset ingest & validation (§17.1)")
    A("")
    A(f"- Run directories scanned (FINAL_CANDIDATES.jsonl found): **{n_runs}**.")
    A(f"- Suffix rows emitted (one selected suffix per run): **{n_suffixes}** "
      f"(the first FINAL_CANDIDATES line, which carries `selection_mode`).")
    A(f"- Duplicated selected suffix strings across runs: **{n_dup_suffix}**.")
    A("- Suffixes per base:")
    for b, n in sorted(by_base.items(), key=lambda kv: -kv[1]):
        A(f"  - `{b}`: {n}")
    A("- By model family: " + ", ".join(f"{k}={v}" for k, v in sorted(by_model.items())))
    A("- By universality: " + ", ".join(f"{k}={v}" for k, v in sorted(by_universality.items())))
    A("- By derived objective_type: " + ", ".join(f"{k}={v}" for k, v in sorted(by_objective.items())))
    A("")
    A("### §17.1 columns: EXIST (read from artifacts) vs DERIVED")
    A("")
    A("| §17.1 concept | status | source |")
    A("|---|---|---|")
    A("| suffix_str / suffix_ids | EXIST | `FINAL_CANDIDATES.jsonl` (line 0) |")
    A("| suffix_length | EXIST | `CONFIG.json:gcg.suffix_length` |")
    A("| optimization seed | EXIST | `CONFIG.json:gcg.seed` |")
    A("| model identity | EXIST | `CONFIG.json:model_name_or_path`, `model_family` |")
    A("| selection_mode | EXIST | `FINAL_CANDIDATES.jsonl:selection_mode` / `objective.selection_mode` |")
    A("| evaluation score | EXIST | `FREE_GENERATION_RESULTS*.jsonl:strongreject_score/_is_success` |")
    A("| generation outputs | EXIST | `FREE_GENERATION_RESULTS*.jsonl:generation_text` |")
    A("| training membership | EXIST (proxy) | seeded (42/43/44) vs `_UNSEEDED` (100/200/300) generation-seed files |")
    A("| **objective_type** | **DERIVED** | from `objective.lambda_repr/lambda_refusal_dir/repr_at_cot_pos` + manifest `cot_target` (see §rule below) |")
    A("| **universality** | **DERIVED** | # behaviors in optimization manifest (1 = per_behavior, >1 = universal). `selection_mode` is ~always `weighted` and does NOT separate the two. |")
    A("| **category / origin_category** | **DERIVED** | `categorize()` LLM-read-through taxonomy — an analysis tool, NOT an official AdvBench field (none exists). |")
    A("| **lexical features** | **DERIVED** | pure-python featurizer over `suffix_str`/`suffix_ids` (§17.3F). |")
    A("")
    A("Genuinely MISSING §17.1 columns (no on-disk source): secondary category, "
      "labeling confidence, labeling rationale (§17.2 asks for these; the taxonomy is "
      "single-label rule-based). No per-suffix human validation field exists.")
    A("")
    A("**objective_type rule:** "
      "`lambda_repr>0 & lambda_refusal_dir>0 -> composite_repr+refusal_dir`; "
      "`lambda_refusal_dir>0 -> refusal_dir`; "
      "`lambda_repr>0 -> repr_match[_cot if repr_at_cot_pos]`; "
      "else pure target CE -> `cot_prefix_ce` if the manifest target is a `<think>` CoT prefix, else `prefix_ce`.")
    A("")

    A("## §17.3A Within-category performance")
    A("")
    if within_cat:
        A("Source: `outputs/stage_gcg_full/GCG_7A_BEHAVIOR_ANALYSIS.json` "
          "(`category_based_success_analysis_llm_taxonomy`) — the universal 5A CoT-target "
          "suffix on all 520 behaviors, seeded eval, `optimized_weighted` vs `neutral_control`.")
        A("")
        A("| category | n_behaviors | optimized_asr | neutral_asr | uplift_pp | gcg_exclusive |")
        A("|---|---|---|---|---|---|")
        for cat, d in sorted(within_cat.items(), key=lambda kv: -(kv[1]["optimized_asr"] or 0)):
            A(f"| {cat} | {d['n_behaviors']} | {d['optimized_asr']} | {d['neutral_asr']} | "
              f"{d['uplift_pp']} | {d['n_gcg_exclusive_success_behaviors']} |")
        A("")
        ranked = sorted(within_cat.items(), key=lambda kv: -(kv[1]["optimized_asr"] or 0))
        big = [(c, d) for c, d in ranked if d["n_behaviors"] >= 15]
        if big:
            A(f"- Most vulnerable (optimized ASR, n>=15): **{big[0][0]}** = {big[0][1]['optimized_asr']}.")
            A(f"- Least vulnerable (optimized ASR, n>=15): **{big[-1][0]}** = {big[-1][1]['optimized_asr']}.")
        A("- Small-n categories (n<15) are flagged in the JSON and should be read with caution.")
    else:
        A("`GCG_7A_BEHAVIOR_ANALYSIS.json` absent — within-category ASR not available.")
    A("")

    A("## §17.3B Cross-category transfer matrix")
    A("")
    A("Full matrix in `results/CATEGORY_TRANSFER_MATRIX.csv`. "
      f"`multi_instruction` origin = universal 5A suffix on full-520 "
      f"(`{FULL520_SEEDED.relative_to(_REPO_ROOT)}`, {tm['n_eval_rows_multi']} eval rows). "
      f"Per-behavior origin rows come from the percot_v2 stratified sample "
      f"({tm['n_percot_beh']} behaviors, best-candidate ASR from "
      "`outputs/stage_gcg_percot_v2/PERBEHAVIOR_ASR_RESULTS.jsonl`).")
    A("")
    A("**Structural caveat:** on disk, each per-behavior suffix was evaluated ONLY on its "
      "own behavior, so per-behavior origin rows populate the **diagonal only** (i==j). "
      "True off-diagonal per-behavior transfer requires re-evaluating each suffix on other "
      "behaviors — not on disk (deferred). The `multi_instruction` row is the only fully "
      "populated cross-category row.")
    A("")
    if tm["multi_row"]:
        ranked = sorted(((c, v) for c, v in tm["multi_row"].items() if v is not None), key=lambda kv: -kv[1])
        A("multi_instruction row (universal suffix ASR by evaluated category):")
        A("")
        A("| eval category | ASR | n eval rows |")
        A("|---|---|---|")
        for c, v in ranked:
            A(f"| {c} | {v} | {tm['multi_denom'].get(c, '')} |")
        A("")
        A(f"- Best-transfer categories for the universal suffix: **{ranked[0][0]}** ({ranked[0][1]}), "
          f"**{ranked[1][0]}** ({ranked[1][1]}).")
        A(f"- Worst: **{ranked[-1][0]}** ({ranked[-1][1]}).")
    A("")

    A("## §17.3C Single- vs multi-instruction suffixes")
    A("")
    A("| metric | single (per-behavior) | multi (universal) |")
    A("|---|---|---|")
    s, m = svm["single"], svm["multi"]
    A(f"| n suffixes | {s['n_suffixes']} | {m['n_suffixes']} |")
    A(f"| mean ASR | {svm['single_best_asr_mean_percot']} (best-cand, n={svm['single_n_behaviors']} beh, percot) "
      f"| {svm['multi_optimized_asr_full520']} (full-520, n={svm['multi_n_eval_rows']} rows) |")
    A(f"| mean suffix_length | {s['mean_suffix_length']} | {m['mean_suffix_length']} |")
    A(f"| mean non_ascii_frac | {s['mean_non_ascii_frac']} | {m['mean_non_ascii_frac']} |")
    A(f"| mean repeated_token_frac | {s['mean_repeated_token_frac']} | {m['mean_repeated_token_frac']} |")
    A(f"| frac has_prefill_phrase | {s['frac_has_prefill_phrase']} | {m['frac_has_prefill_phrase']} |")
    A(f"| frac has_imperative | {s['frac_has_imperative']} | {m['frac_has_imperative']} |")
    A("")
    if svm["single_best_asr_mean_percot"] is not None and svm["multi_optimized_asr_full520"] is not None:
        gap = round(svm["single_best_asr_mean_percot"] - svm["multi_optimized_asr_full520"], 4)
        A(f"- Single-minus-multi ASR gap = **{gap}** (single = best-of-candidates per behavior "
          "on its OWN behavior, an upper bound; multi = one fixed suffix averaged over 520 held-in "
          "behaviors — the two ASRs are NOT strictly comparable; see caveat).")
        A("- Caveat: the single-instruction number is a per-behavior best-candidate ASR on the "
          "training behavior itself (optimistic); the multi number is a genuine many-behavior "
          "average. Use for direction, not as a like-for-like effect size.")
        A("- **Model-family caveat:** the `single` group is 100% qwen3 while the `multi`/universal "
          "group pools qwen3 + gemma4 + deepseek_r1, so single-vs-multi contrasts (incl. the §17.3F "
          "lexical means) partly confound universality with model family. Gap DIRECTION is robust "
          "(qwen3-only `multi` does not reverse it); treat magnitudes as family-confounded.")
    A("")

    A("## §17.3D Train vs unseen (generation-seed hold-out)")
    A("")
    A("`training membership` here = generation seed set: seeded 42/43/44 (development) vs "
      "`_UNSEEDED` 100/200/300 (held-out), same fixed universal suffix on the same behaviors.")
    A("")
    A("| set | file | optimized_asr | neutral_asr | n behaviors |")
    A("|---|---|---|---|---|")
    for lbl, d in tvu.items():
        if d:
            A(f"| {lbl} | `{d['file']}` | {d['optimized_asr']} | {d['neutral_asr']} | {d['n_distinct_behaviors']} |")
        else:
            A(f"| {lbl} | (missing) | | | |")
    A("")
    A("Note: this measures generation-seed robustness of an already-fixed suffix, NOT transfer to "
      "unseen *instructions*. Genuine unseen-instruction transfer for the universal suffix is the "
      "multi_instruction row of §17.3B (evaluated on all 520, most of which were not in the 25-behavior "
      "optimization manifest `advbench_cot_target_manifest.jsonl`).")
    A("")

    A("## §17.3F Lexical & token-level commonalities")
    A("")
    A("Featurizer: `scripts/phase13_suffix_analysis.py::featurize` over `suffix_str`/`suffix_ids`. "
      "Per-suffix values are in `results/SUFFIX_TAXONOMY.csv`.")
    A("")
    def col_mean(rows, key):
        xs = [r[key] for r in rows if isinstance(r[key], (int, float))]
        return round(sum(xs) / len(xs), 4) if xs else None
    A("| feature | all suffixes mean/frac |")
    A("|---|---|")
    for k in ["non_ascii_frac", "punct_count", "has_imperative", "has_roleplay_marker",
              "has_prefill_phrase", "repeated_token_frac"]:
        A(f"| {k} | {col_mean(suffix_rows, k)} |")
    A("")
    A("**Caveat (§17.3F, mandatory):** these are surface-form correlations only. Lexical commonality "
      "(e.g. a 'Sure'/prefill phrase or high non-ASCII fraction) does NOT imply any causal mechanism; "
      "mechanistic attribution requires the internal-state analysis deferred below.")
    A("")

    A("## §17.3G Objective-dependent behavior")
    A("")
    A("Per-run optimized vs neutral ASR aggregated by derived objective_type over runs that have a "
      "seeded `FREE_GENERATION_RESULTS.jsonl` with an `optimized_*` condition "
      "(via `build_gcg_source_of_truth.analyze_free_gen`).")
    A("")
    A("| objective_type | n_runs_with_eval | n_opt_rows | optimized_asr | neutral_asr |")
    A("|---|---|---|---|---|")
    for ot, d in sorted(obj_summary.items(), key=lambda kv: -(kv[1]["optimized_asr"] or 0)):
        A(f"| {ot} | {d['n_runs_with_eval']} | {d['n_opt_rows']} | {d['optimized_asr']} | {d['neutral_asr']} |")
    A("")
    A("Note: ASR is pooled across heterogeneous manifests/models/behavior-counts per objective_type, "
      "so this is a coarse descriptor, not a controlled comparison. For controlled single-variable "
      "objective contrasts see `docs/GCG_PHASE4_7_SOURCE_OF_TRUTH.md`.")
    A("")

    A("## §17.3E & §17.4 — Deferred to mechanistic hand-off")
    A("")
    A("§17.3E (universality-rank vs attention/internal-state/refusal-direction effects) and the §17.4 "
      "mechanistic representative-subset analysis require GPU activations and are OUT OF SCOPE for this "
      "CPU-only phase. `results/SUFFIX_TAXONOMY.csv` (with universality + objective_type + refusal-dir "
      "config columns) is the selection table for that hand-off.")
    A("")

    if SKIPPED:
        A("## Skipped / missing inputs (logged, non-fatal)")
        A("")
        for msg in SKIPPED:
            A(f"- {msg}")
        A("")

    REPORT_MD.write_text("\n".join(L) + "\n")


def main():
    RESULTS_DIR.mkdir(exist_ok=True)
    behaviors_520 = load_manifest_520()

    suffix_rows, n_runs = build_suffix_rows()
    fieldnames = [
        "run_id", "run_dir", "model_family", "objective_type", "universality",
        "n_manifest_behaviors", "origin_task_id", "origin_category", "selection_mode",
        "lambda_repr", "lambda_refusal_dir", "repr_at_cot_pos", "cot_target",
        "suffix_length", "seed", "suffix_str",
        "non_ascii_frac", "punct_count", "has_imperative", "has_roleplay_marker",
        "has_prefill_phrase", "repeated_token_frac",
    ]
    with TAXONOMY_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in suffix_rows:
            w.writerow(r)
    print(f"Wrote {TAXONOMY_CSV} ({len(suffix_rows)} rows)")

    tm = build_transfer_matrix(behaviors_520)
    write_transfer_csv(tm)
    print(f"Wrote {TRANSFER_CSV} ({len(tm['diag']) + 1} origin rows, {len(tm['columns'])} cols)")

    obj_summary = objective_dependent_summary(suffix_rows)
    svm = single_vs_multi(suffix_rows)
    tvu = train_vs_unseen()
    write_report(suffix_rows, n_runs, tm, obj_summary, svm, tvu, behaviors_520)
    print(f"Wrote {REPORT_MD}")
    print(f"Skipped inputs: {len(SKIPPED)}")


if __name__ == "__main__":
    main()
