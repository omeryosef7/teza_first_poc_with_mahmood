"""
Stage 9a — Paired A/E(+D/G) deltas and failure-taxonomy shifts, per model.

Reads a model's scoring shard (`{run_dir}/{model}/scoring/{model}_scores.jsonl`)
and computes per-goal, per-seed-averaged deltas between condition A (puzzle,
thinking-on) and condition E (bare goal, thinking-off), and between D (puzzle,
thinking-off) and G (bare goal, thinking-off) where present, for
strongreject_is_success and every boolean taxonomy field. Descriptive only —
no causal claim is made from these deltas (a goal succeeding more under A than
E just means the paired outcome differs, not that puzzle-framing "caused" it
for that specific row, since A and E are drawn from different generation
episodes, not counterfactual pairs of the same sample).
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

MODEL_DIR_NAME = {"qwen3": "qwen", "gemma4": "gemma"}

TAXONOMY_FIELDS = [
    "strongreject_is_success",
    "puzzle_solved",
    "harmful_goal_identified",
    "explicit_refusal",
    "implicit_refusal",
    "harmful_compliance",
    "safe_but_relevant_answer",
    "irrelevant_or_confused",
    "truncated",
    "empty_or_malformed",
    "marker_parsing_error",
]


def _load_scores(path: Path) -> list[dict]:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _rate_by_goal(rows: list[dict], condition: str, field: str) -> dict[int, float]:
    by_goal: dict[int, list[float]] = {}
    for r in rows:
        if r.get("condition") != condition:
            continue
        if r.get("generation_status") != "ok":
            continue
        v = r.get(field)
        if v is None:
            continue
        by_goal.setdefault(r["goal_index"], []).append(1.0 if v else 0.0)
    return {g: sum(vs) / len(vs) for g, vs in by_goal.items() if vs}


def _pair_deltas(rows: list[dict], cond_a: str, cond_b: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for field in TAXONOMY_FIELDS:
        rate_a = _rate_by_goal(rows, cond_a, field)
        rate_b = _rate_by_goal(rows, cond_b, field)
        goals = sorted(set(rate_a) & set(rate_b))
        per_goal = [
            {"goal_index": g, f"{cond_a}_rate": rate_a[g], f"{cond_b}_rate": rate_b[g],
             "delta": rate_a[g] - rate_b[g]}
            for g in goals
        ]
        deltas = [row["delta"] for row in per_goal]
        out[field] = {
            "n_goals": len(goals),
            "mean_delta": sum(deltas) / len(deltas) if deltas else None,
            "n_goals_a_higher": sum(1 for d in deltas if d > 0),
            "n_goals_b_higher": sum(1 for d in deltas if d < 0),
            "n_goals_tied": sum(1 for d in deltas if d == 0),
            "per_goal": per_goal,
        }
    return out


def _write_csv(path: Path, cond_a: str, cond_b: str, deltas: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["field", "goal_index", f"{cond_a}_rate", f"{cond_b}_rate", "delta"])
        for field, d in deltas.items():
            for row in d["per_goal"]:
                w.writerow([field, row["goal_index"], row[f"{cond_a}_rate"],
                            row[f"{cond_b}_rate"], row["delta"]])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=["qwen3", "gemma4"])
    ap.add_argument("--run-dir", required=True)
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    model_dir = MODEL_DIR_NAME[args.model]
    scores_path = run_dir / model_dir / "scoring" / f"{args.model}_scores.jsonl"
    rows = _load_scores(scores_path)
    print(f"Loaded {len(rows)} scored rows from {scores_path}")

    out_dir = run_dir / model_dir / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    ae_deltas = _pair_deltas(rows, "A", "E")
    _write_csv(out_dir / "paired_A_vs_E_deltas.csv", "A", "E", ae_deltas)

    conditions_present = {r["condition"] for r in rows}
    dg_deltas = None
    if "D" in conditions_present and "G" in conditions_present:
        dg_deltas = _pair_deltas(rows, "D", "G")
        _write_csv(out_dir / "paired_D_vs_G_deltas.csv", "D", "G", dg_deltas)

    summary = {
        "model": args.model,
        "n_rows_scored": len(rows),
        "A_vs_E": {f: {k: v for k, v in d.items() if k != "per_goal"} for f, d in ae_deltas.items()},
    }
    if dg_deltas is not None:
        summary["D_vs_G"] = {f: {k: v for k, v in d.items() if k != "per_goal"} for f, d in dg_deltas.items()}

    with (out_dir / "paired_ae_summary.json").open("w") as f:
        json.dump(summary, f, indent=2)

    print(f"A_vs_E strongreject_is_success mean_delta="
          f"{ae_deltas['strongreject_is_success']['mean_delta']}")
    print(f"Wrote summary to {out_dir / 'paired_ae_summary.json'}")


if __name__ == "__main__":
    main()
