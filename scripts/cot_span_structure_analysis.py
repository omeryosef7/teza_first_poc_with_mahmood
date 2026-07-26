#!/usr/bin/env python3
"""Descriptive STRUCTURE analysis of CoT span annotations.

SAFETY: This script deliberately uses ONLY numeric / boolean / structural fields.
It NEVER reads, prints, stores, or passes around the top-level `goal` field or any
span instance `preview` field. Those are explicitly excluded when parsing each record
(see ALLOWED_INSTANCE_FIELDS and the goal-drop in load_records). Do not add code that
touches `goal` or `preview`.

Torch-free, CPU-only, stdlib-only. Produces a tidy per-(model, component, success_bool)
table plus a plain-English markdown summary, to inform the Phase-F1 attention-measurement
design.
"""
import argparse
import json
import os
import statistics
from collections import defaultdict

# The seven span components annotated per record.
COMPONENTS = [
    "harmful_instruction",
    "benign_puzzle_scaffold",
    "injected_reasoning",
    "final_answer_cue",
    "system_prompt",
    "chat_template_tokens",
    "assistant_generation_marker",
]

# Only these instance fields are ever read. `preview` is intentionally absent.
ALLOWED_INSTANCE_FIELDS = ("char_start", "char_end", "tok_start", "tok_end")

# Forbidden fields — asserted-never-touched by the loader.
FORBIDDEN_TOP = ("goal",)
FORBIDDEN_INSTANCE = ("preview",)


def _safe_instance(inst):
    """Return a numeric-only copy of a span instance. Never copies `preview`."""
    out = {}
    for k in ALLOWED_INSTANCE_FIELDS:
        v = inst.get(k)
        out[k] = v if isinstance(v, (int, float)) else None
    return out


def load_records(path):
    """Yield safe, numeric-only record dicts. Drops `goal` and all `preview` fields."""
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            # Explicitly drop forbidden top-level text before doing anything else.
            for k in FORBIDDEN_TOP:
                raw.pop(k, None)

            rec = {
                "is_success": bool(raw.get("is_success")),
                "n_tokens": raw.get("n_tokens"),
                "judge_score": raw.get("judge_score"),
                "content_char_len": raw.get("content_char_len"),
                "coverage_misses": list(raw.get("coverage_misses") or []),
                "spans": {},
            }
            spans = raw.get("spans") or {}
            for comp in COMPONENTS:
                cv = spans.get(comp) or {}
                located = bool(cv.get("located"))
                instances = [
                    _safe_instance(inst) for inst in (cv.get("instances") or [])
                ]
                rec["spans"][comp] = {"located": located, "instances": instances}
            yield rec


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.fmean(xs) if xs else None


def _median(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def analyze_model(records):
    """Return dict keyed by (component, success_bool) -> metrics, plus denominators."""
    by_success = {True: [], False: []}
    for rec in records:
        by_success[rec["is_success"]].append(rec)

    results = {}  # (component, success_bool) -> metrics
    denom = {True: len(by_success[True]), False: len(by_success[False])}

    for success in (True, False):
        recs = by_success[success]
        n = len(recs)
        # coverage_misses frequency per component across records in this split.
        miss_counts = defaultdict(int)
        for rec in recs:
            for name in rec["coverage_misses"]:
                miss_counts[name] += 1

        for comp in COMPONENTS:
            present = 0
            norm_starts = []
            norm_ends = []
            tok_lens = []
            counts = []
            for rec in recs:
                cv = rec["spans"][comp]
                counts.append(len(cv["instances"]))
                if cv["located"]:
                    present += 1
                nt = rec["n_tokens"]
                for inst in cv["instances"]:
                    ts, te = inst["tok_start"], inst["tok_end"]
                    if ts is not None and te is not None:
                        tok_lens.append(te - ts)
                        if nt:
                            norm_starts.append(ts / nt)
                            norm_ends.append(te / nt)

            results[(comp, success)] = {
                "presence_rate": (present / n) if n else None,
                "mean_norm_tok_start": _mean(norm_starts),
                "median_norm_tok_start": _median(norm_starts),
                "mean_norm_tok_end": _mean(norm_ends),
                "median_norm_tok_end": _median(norm_ends),
                "mean_tok_len": _mean(tok_lens),
                "mean_count": _mean(counts),
                "miss_rate": (miss_counts.get(comp, 0) / n) if n else None,
                "n": n,
            }
    return results, denom


def _fmt(v, nd=4):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.{nd}f}"
    return str(v)


def write_csv(path, per_model):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cols = [
        "model", "component", "success_bool", "presence_rate",
        "mean_norm_tok_start", "mean_norm_tok_end", "mean_tok_len",
        "mean_count", "miss_rate", "n",
    ]
    lines = [",".join(cols)]
    for model in sorted(per_model):
        results, _ = per_model[model]
        for success in (True, False):
            for comp in COMPONENTS:
                m = results[(comp, success)]
                row = [
                    model, comp, str(success),
                    _fmt(m["presence_rate"]),
                    _fmt(m["mean_norm_tok_start"]),
                    _fmt(m["mean_norm_tok_end"]),
                    _fmt(m["mean_tok_len"]),
                    _fmt(m["mean_count"]),
                    _fmt(m["miss_rate"]),
                    _fmt(m["n"]),
                ]
                lines.append(",".join(row))
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def write_md(path, per_model):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    L = []
    L.append("# CoT Span Structure Analysis")
    L.append("")
    L.append(
        "Descriptive structural analysis of CoT span annotations, split by attack "
        "outcome (`is_success` True vs False). All figures are numeric / structural: "
        "component presence, normalized token position, span length, instance counts, "
        "and coverage-miss rates. No harmful content, no causal or PASS claims."
    )
    L.append("")
    for model in sorted(per_model):
        results, denom = per_model[model]
        L.append(f"## {model}")
        L.append("")
        L.append(f"- n(success)={denom[True]}, n(fail)={denom[False]}")
        L.append("")
        L.append(
            "| component | presence(succ) | presence(fail) | "
            "norm_tok_start(succ) | norm_tok_start(fail) | "
            "norm_tok_end(succ) | norm_tok_end(fail) | "
            "tok_len(succ) | tok_len(fail) | count(succ) | count(fail) | "
            "miss(succ) | miss(fail) |"
        )
        L.append("|" + "---|" * 13)
        for comp in COMPONENTS:
            s = results[(comp, True)]
            f = results[(comp, False)]
            L.append(
                f"| {comp} | {_fmt(s['presence_rate'],3)} | {_fmt(f['presence_rate'],3)} | "
                f"{_fmt(s['mean_norm_tok_start'],3)} | {_fmt(f['mean_norm_tok_start'],3)} | "
                f"{_fmt(s['mean_norm_tok_end'],3)} | {_fmt(f['mean_norm_tok_end'],3)} | "
                f"{_fmt(s['mean_tok_len'],1)} | {_fmt(f['mean_tok_len'],1)} | "
                f"{_fmt(s['mean_count'],2)} | {_fmt(f['mean_count'],2)} | "
                f"{_fmt(s['miss_rate'],3)} | {_fmt(f['miss_rate'],3)} |"
            )
        L.append("")

    # Implications section, generated from the numbers.
    L.append("## Implications for the attention-measurement design")
    L.append("")
    for model in sorted(per_model):
        results, denom = per_model[model]
        L.append(f"### {model}")
        for comp in ("injected_reasoning", "final_answer_cue"):
            s = results[(comp, True)]
            f = results[(comp, False)]
            sp = s["presence_rate"]
            fp = f["presence_rate"]
            pos = s["mean_norm_tok_start"]
            pos_txt = _fmt(pos, 2) if pos is not None else "n/a"
            L.append(
                f"- **{comp}**: present in {_fmt(sp,3)} of successes vs {_fmt(fp,3)} of "
                f"failures; in successes it sits at normalized token-start ~{pos_txt} "
                f"(mean span length {_fmt(s['mean_tok_len'],1)} tokens, "
                f"{_fmt(s['mean_count'],2)} instances/record). "
                f"-> Prioritize measuring attention mass DIRECTED AT the {comp} token "
                f"spans near this position."
            )
        L.append("")
    L.append(
        "General note: components with a large success-vs-failure gap in presence rate "
        "and a stable normalized position are the highest-value targets for the "
        "attention-mass probe; components with high coverage-miss rates are less "
        "reliably localizable and should be de-prioritized or re-annotated first."
    )
    L.append("")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


def print_summary(per_model):
    for model in sorted(per_model):
        results, denom = per_model[model]
        print(f"=== {model} === n(success)={denom[True]} n(fail)={denom[False]}")
        for comp in COMPONENTS:
            s = results[(comp, True)]
            f = results[(comp, False)]
            print(
                f"  {comp:28s} presence S/F={_fmt(s['presence_rate'],3)}/"
                f"{_fmt(f['presence_rate'],3)} "
                f"nstart S/F={_fmt(s['mean_norm_tok_start'],3)}/"
                f"{_fmt(f['mean_norm_tok_start'],3)} "
                f"toklen S/F={_fmt(s['mean_tok_len'],1)}/{_fmt(f['mean_tok_len'],1)} "
                f"count S/F={_fmt(s['mean_count'],2)}/{_fmt(f['mean_count'],2)} "
                f"miss S/F={_fmt(s['miss_rate'],3)}/{_fmt(f['miss_rate'],3)}"
            )


def discover_spans(spans_dir):
    files = []
    for fn in sorted(os.listdir(spans_dir)):
        if fn.endswith("_spans.jsonl"):
            files.append(os.path.join(spans_dir, fn))
    return files


def model_name_from_path(path):
    base = os.path.basename(path)
    return base[: -len("_spans.jsonl")] if base.endswith("_spans.jsonl") else base


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spans-dir", default="outputs/phase_f_cot_spans")
    ap.add_argument("--out-csv", default="results/COT_SPAN_STRUCTURE.csv")
    ap.add_argument("--out-md", default="docs/COT_SPAN_STRUCTURE_ANALYSIS.md")
    args = ap.parse_args()

    files = discover_spans(args.spans_dir)
    per_model = {}
    for path in files:
        model = model_name_from_path(path)
        records = list(load_records(path))
        per_model[model] = analyze_model(records)

    write_csv(args.out_csv, per_model)
    write_md(args.out_md, per_model)
    print_summary(per_model)
    print(f"\nWrote: {args.out_csv}")
    print(f"Wrote: {args.out_md}")


if __name__ == "__main__":
    main()
