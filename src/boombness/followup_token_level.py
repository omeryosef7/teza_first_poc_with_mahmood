"""followup_token_level.py — Phase B of the d_surface follow-up: occurrence-resolved readouts.

WHY THIS EXISTS, GIVEN analyze_boombness.py ALREADY DOES §7.1
`analyze_boombness.py` answers "does the FINAL occurrence become more concept-like than the
earlier ones" by splitting occurrences into {final, earlier}. The follow-up plan needs a finer
split — first demo / middle demo / last demo / query — because the previous sprint's G1 result
(the meaning lives in the demonstration block, not the query token) predicts that those four
roles behave differently, and a {final, earlier} split cannot see it. Everything else is reused:
the stats helpers, the column discovery, the cell semantics and the direction sanity gate are all
imported from analyze_boombness rather than reimplemented.

WHAT IT EMITS
  <out>/token_level_occurrence_readouts.jsonl.gz
      one row per (prompt_id, occurrence, layer) carrying every requested metric.
      The plan asks for one row per (prompt, occurrence, layer, METRIC); this collapses the
      metric axis into a dict on the row, which is the same information at ~6x fewer bytes.
      DEVIATION IS DELIBERATE AND RECORDED HERE so a reader does not think a metric was dropped.
  <out>/token_level_dynamics_summary.json
      layer x occurrence_role curves, band aggregates, the role contrasts, the direction
      comparison, the refusalness join, and the full row accounting.

OCCURRENCE ROLES — and the assumption they rest on
The query codeword is the LAST occurrence in the prompt. This is VERIFIED, not assumed: the
loader asserts that in every prompt exactly one occurrence carries is_query_occurrence and that
it sits at the highest occurrence_index. If that ever stops holding the run aborts rather than
silently mislabelling demo tokens as query tokens.

  query        is_query_occurrence
  demo_first   occurrence_index == 0 and not query
  demo_last    the highest non-query occurrence_index
  demo_middle  everything else
A 2-occurrence prompt has one demo that is both first and last; primary role resolves to
demo_first, and the booleans is_first_demo / is_last_demo are BOTH set so nothing is lost.

REFUSALNESS IS A PROMPT-LEVEL JOIN, NOT AN OCCURRENCE-LEVEL ONE
The refusalness producer reads ONE position per prompt (codeword_last or last). It has no
per-occurrence resolution. It is therefore attached to every occurrence row of a prompt with an
explicit `refusalness_readout_position` field, and the summary reports it separately from the
occurrence-resolved metrics. Confusing the two is the ~9-token gap that caused three retractions
in the previous sprint (handover ch. 0.6).
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json
import math
import os
import sys
from typing import Dict, List, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import read_jsonl  # noqa: E402
from analyze_boombness import (  # noqa: E402  -- reuse, do not reimplement
    CELL_LABEL, CONCEPT_CELLS, SANITY_CELLS, SANITY_CODEWORD_CELLS,
    col, cohens_d, direction_sanity, discover_columns, mean, sem,
)

# Layer bands the plan asks about explicitly (§4 "Key questions" 3).
BANDS = {"L6_L12": range(6, 13), "L14_L21": range(14, 22), "late_L22_L31": range(22, 32)}

ROLES = ["demo_first", "demo_middle", "demo_last", "query"]

# family_id layout, verified to be 9 fields on every row of both extracts:
#   domain|split|slotN|nX|strength|consistency|example_position|role_style|query_kind
FAMILY_FIELDS = ["fam_domain", "fam_split", "fam_slot", "fam_n", "fam_strength",
                 "fam_consistency", "fam_example_position", "fam_role_style", "fam_query_kind"]


def parse_family_id(fid: str) -> Dict[str, str]:
    """Explode family_id into columns. family_slot is REQUIRED by the plan and is only
    recoverable from here — R-18 was caused by an analyzer that had no slot filter."""
    parts = fid.split("|")
    if len(parts) != len(FAMILY_FIELDS):
        raise ValueError(f"family_id_field_count:{len(parts)}!={len(FAMILY_FIELDS)}:{fid}")
    out = dict(zip(FAMILY_FIELDS, parts))
    slot = out["fam_slot"]
    if not slot.startswith("slot"):
        raise ValueError(f"family_slot_not_slotN:{slot}:{fid}")
    out["family_slot"] = int(slot[4:])
    return out


def assign_roles(rows: List[Dict]) -> None:
    """Attach occurrence_role / is_first_demo / is_last_demo in place, per prompt.

    Aborts on any prompt whose query occurrence is not the unique highest index — see the
    module docstring. This is the guard, not a comment about one."""
    by_prompt: Dict[str, List[Dict]] = collections.defaultdict(list)
    for r in rows:
        by_prompt[r["prompt_id"]].append(r)

    for pid, rs in by_prompt.items():
        rs.sort(key=lambda r: r["occurrence_index"])
        q = [r for r in rs if r.get("is_query_occurrence")]
        if len(q) != 1:
            raise ValueError(f"expected exactly 1 query occurrence, got {len(q)} for {pid}")
        if q[0]["occurrence_index"] != rs[-1]["occurrence_index"]:
            raise ValueError(f"query occurrence is not the last index for {pid}")
        if len(rs) != rs[0]["n_occurrences"]:
            raise ValueError(f"occurrence_count_mismatch:{len(rs)}!={rs[0]['n_occurrences']}:{pid}")

        demos = rs[:-1]
        first_i = demos[0]["occurrence_index"] if demos else None
        last_i = demos[-1]["occurrence_index"] if demos else None
        for r in rs:
            oi = r["occurrence_index"]
            if r.get("is_query_occurrence"):
                r["occurrence_role"] = "query"
                r["is_first_demo"] = False
                r["is_last_demo"] = False
                continue
            r["is_first_demo"] = (oi == first_i)
            r["is_last_demo"] = (oi == last_i)
            r["occurrence_role"] = ("demo_first" if r["is_first_demo"]
                                    else "demo_last" if r["is_last_demo"]
                                    else "demo_middle")
        r0 = rs[0]
        for r in rs:
            r["n_demo_occurrences"] = len(demos)
            r["prompt_n_occurrences"] = r0["n_occurrences"]


def load_refusalness(path: Optional[str]) -> Dict[str, Dict]:
    if not path:
        return {}
    rows = read_jsonl(os.path.join(path, "results.jsonl"))
    out = {}
    for r in rows:
        keep = {k: v for k, v in r.items() if k.startswith("refusalness|")}
        keep["refusalness_readout_position"] = r.get("readout_position")
        keep["refusalness_readout_token_index"] = r.get("readout_token_index")
        out[r["prompt_id"]] = keep
    return out


def curve(rows: List[Dict], metric: str, layers: Sequence[int]) -> Dict[str, Dict]:
    """{layer: {mean, sem, n}} for one already-filtered row set."""
    out = {}
    for L in layers:
        c = col(metric, L)
        vs = [r[c] for r in rows if c in r and r[c] is not None]
        out[str(L)] = {"mean": mean(vs), "sem": sem(vs), "n": len(vs)}
    return out


def band_mean(rows: List[Dict], metric: str, band: Sequence[int]) -> Dict:
    """Per-row mean across a layer band, then aggregated. Averaging per row first keeps the
    unit of analysis the occurrence, not the (occurrence, layer) cell."""
    per_row = []
    for r in rows:
        vs = [r[col(metric, L)] for L in band
              if col(metric, L) in r and r[col(metric, L)] is not None]
        if vs:
            per_row.append(sum(vs) / len(vs))
    return {"mean": mean(per_row), "sem": sem(per_row), "n": len(per_row)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, help="extract_boombness run directory")
    ap.add_argument("--refusalness", default=None, help="refusalness run directory (prompt-level)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--metrics", default="d_surface|proj,d_surface|cos,d_naive|proj,"
                                         "d_context|proj,d_inter|proj,ll|boombness")
    ap.add_argument("--condition", default="natural_doublespeak",
                    help="condition whose occurrence dynamics the headline curves describe")
    ap.add_argument("--query-kind", default="", help="restrict to one query kind; '' = keep all "
                                                     "but NEVER pool them in a summary cell")
    ap.add_argument("--bank-blocks", default="", help="comma list; '' = all, but the summary "
                                                      "always reports the composition")
    ap.add_argument("--slot", default="", help="restrict to one family_slot (R-18 hygiene)")
    ap.add_argument("--strict", action="store_true",
                    help="non-zero exit if the direction sanity gate fails")
    ap.add_argument("--no-jsonl", action="store_true", help="summary only, skip the row dump")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    metrics = [m.strip() for m in args.metrics.split(",") if m.strip()]

    ledger = collections.Counter()
    skips: Dict[str, int] = collections.Counter()

    raw = read_jsonl(os.path.join(args.run, "results.jsonl"))
    ledger["attempted"] = len(raw)

    rows: List[Dict] = []
    for r in raw:
        try:
            r.update(parse_family_id(r["family_id"]))
        except ValueError as e:
            skips[str(e).split(":")[0]] += 1
            continue
        if r["fam_query_kind"] != r["query_kind"]:
            # the plan's audit: family_id must not be stripped of its query kind
            skips["family_id_query_kind_disagrees_with_column"] += 1
            continue
        if args.query_kind and r["query_kind"] != args.query_kind:
            skips["filtered_query_kind"] += 1
            continue
        if args.bank_blocks and r["bank_block"] not in set(args.bank_blocks.split(",")):
            skips["filtered_bank_block"] += 1
            continue
        if args.slot != "" and r["family_slot"] != int(args.slot):
            skips["filtered_family_slot"] += 1
            continue
        if r.get("is_self_fit"):
            skips["self_fit_direction_excluded"] += 1
            continue
        rows.append(r)
    ledger["kept"] = len(rows)

    assign_roles(rows)

    refus = load_refusalness(args.refusalness)
    matched = sum(1 for r in rows if r["prompt_id"] in refus)
    ledger["refusalness_matched_rows"] = matched
    ledger["refusalness_unmatched_rows"] = len(rows) - matched
    for r in rows:
        r.update(refus.get(r["prompt_id"], {}))

    layers = sorted(discover_columns(rows).get(metrics[0], []))
    if not layers:
        print(f"FATAL: no layers found for metric {metrics[0]}", file=sys.stderr)
        return 2

    # ---- the gate that must pass before any curve is read ------------------------------- #
    sanity = direction_sanity(rows, "d_surface|cos", layers)
    sanity_ok = sanity["n_layers_positive"] > sanity["n_layers"] / 2

    # ---- summary ------------------------------------------------------------------------ #
    cond_rows = [r for r in rows if r["condition"] == args.condition]
    summary: Dict = {
        "label": "Phase B — occurrence-resolved token-level Boombness",
        "inputs": {"extract_run": os.path.abspath(args.run),
                   "refusalness_run": os.path.abspath(args.refusalness) if args.refusalness else None},
        "filters": {"query_kind": args.query_kind or "ALL (reported per cell, never pooled)",
                    "bank_blocks": args.bank_blocks or "ALL",
                    "family_slot": args.slot or "ALL",
                    "self_fit": "excluded"},
        "row_accounting": dict(ledger),
        "skips": dict(skips),
        "composition": {
            "bank_block": dict(collections.Counter(r["bank_block"] for r in rows)),
            "query_kind": dict(collections.Counter(r["query_kind"] for r in rows)),
            "family_slot": dict(collections.Counter(r["family_slot"] for r in rows)),
            "condition": dict(collections.Counter(r["condition"] for r in rows)),
            "occurrence_role": dict(collections.Counter(r["occurrence_role"] for r in rows)),
            "n_prompts": len({r["prompt_id"] for r in rows}),
        },
        "direction_sanity_d_surface_cos": {
            "passes": sanity_ok, "n_layers_positive": sanity["n_layers_positive"],
            "n_layers": sanity["n_layers"], "best_layer": sanity["best_layer"],
            "note": "concept-surface cells {B,E} must exceed codeword-surface {A,C} on the "
                    "fitting contrast; if not, d_surface is not measuring what its name says",
        },
        "headline_condition": args.condition,
        "layers": layers,
        "by_role": {},
        "bands": {},
        "role_contrasts": {},
        "direction_comparison": {},
        "refusalness": {},
    }

    for m in metrics:
        summary["by_role"][m] = {}
        summary["bands"][m] = {}
        for role in ROLES:
            rs = [r for r in cond_rows if r["occurrence_role"] == role]
            summary["by_role"][m][role] = {"n": len(rs), "layers": curve(rs, m, layers)}
            summary["bands"][m][role] = {b: band_mean(rs, m, [L for L in rng if L in layers])
                                         for b, rng in BANDS.items()}
        # all demo occurrences pooled — the plan's "all demo codewords aggregate"
        rs_demo = [r for r in cond_rows if r["occurrence_role"] != "query"]
        summary["by_role"][m]["demo_all"] = {"n": len(rs_demo), "layers": curve(rs_demo, m, layers)}
        summary["bands"][m]["demo_all"] = {b: band_mean(rs_demo, m, [L for L in rng if L in layers])
                                           for b, rng in BANDS.items()}

    # Q1 does Boombness grow across demo occurrences?  Q2 is the query more or less bomb-like?
    for m in metrics:
        c = {}
        for L in layers:
            cc = col(m, L)
            g = {role: [r[cc] for r in cond_rows
                        if r["occurrence_role"] == role and cc in r and r[cc] is not None]
                 for role in ROLES}
            g["demo_all"] = [r[cc] for r in cond_rows
                             if r["occurrence_role"] != "query" and cc in r and r[cc] is not None]
            c[str(L)] = {
                "last_minus_first_demo": mean(g["demo_last"]) - mean(g["demo_first"]),
                "d_last_vs_first_demo": cohens_d(g["demo_last"], g["demo_first"]),
                "query_minus_demo_all": mean(g["query"]) - mean(g["demo_all"]),
                "d_query_vs_demo_all": cohens_d(g["query"], g["demo_all"]),
                "n": {k: len(v) for k, v in g.items()},
            }
        summary["role_contrasts"][m] = c

    # Q4 does d_surface differ from d_naive / d_context?
    for role in ROLES + ["demo_all"]:
        rs = ([r for r in cond_rows if r["occurrence_role"] != "query"] if role == "demo_all"
              else [r for r in cond_rows if r["occurrence_role"] == role])
        summary["direction_comparison"][role] = {
            m: {b: band_mean(rs, m, [L for L in rng if L in layers]) for b, rng in BANDS.items()}
            for m in metrics}

    # Q5 is refusalness independent at these positions?  Prompt-level, stated as such.
    if refus:
        rlayers = sorted({int(k.split("|")[1][1:]) for v in refus.values() for k in v
                          if k.startswith("refusalness|") and "|cos" in k})
        pos = {v.get("refusalness_readout_position") for v in refus.values()}
        summary["refusalness"] = {
            "join": "PROMPT-LEVEL. The refusalness producer reads ONE position per prompt and "
                    "has no per-occurrence resolution; it is NOT an occurrence-resolved metric.",
            "readout_position": sorted(p for p in pos if p),
            "n_prompts_with_refusalness": len({r["prompt_id"] for r in rows
                                               if r["prompt_id"] in refus}),
            "n_prompts_without": len({r["prompt_id"] for r in rows if r["prompt_id"] not in refus}),
            "layers": rlayers,
            "by_condition": {
                cond: curve([r for r in rows if r["condition"] == cond and r.get("is_query_occurrence")],
                            "refusalness|cos", rlayers)
                for cond in sorted({r["condition"] for r in rows})},
        }

    with open(os.path.join(args.out_dir, "token_level_dynamics_summary.json"), "w") as f:
        json.dump(summary, f, indent=1)

    # ---- the row dump -------------------------------------------------------------------- #
    if not args.no_jsonl:
        keep_meta = ["prompt_id", "family_id", "family_slot", "condition", "cell", "domain",
                     "split", "bank_block", "query_kind", "n_examples", "strength", "consistency",
                     "example_position", "role_style", "target_surface", "occurrence_index",
                     "n_occurrences", "n_demo_occurrences", "occurrence_role", "is_first_demo",
                     "is_last_demo", "is_final_occurrence", "is_query_occurrence", "token_pos",
                     "seq_len", "n_subtokens", "is_single_token", "directions_fitted_on",
                     "is_self_fit", "refusalness_readout_position"]
        path = os.path.join(args.out_dir, "token_level_occurrence_readouts.jsonl.gz")
        n_out = 0
        with gzip.open(path, "wt") as f:
            for r in rows:
                base = {k: r[k] for k in keep_meta if k in r}
                for L in layers:
                    mv = {}
                    for m in metrics:
                        c = col(m, L)
                        if c in r and r[c] is not None and math.isfinite(r[c]):
                            mv[m] = round(float(r[c]), 6)
                    if not mv:
                        continue
                    f.write(json.dumps({**base, "layer": L, "metrics": mv}) + "\n")
                    n_out += 1
        ledger["jsonl_rows_written"] = n_out
        summary["row_accounting"] = dict(ledger)
        with open(os.path.join(args.out_dir, "token_level_dynamics_summary.json"), "w") as f:
            json.dump(summary, f, indent=1)

    print(json.dumps({"attempted": ledger["attempted"], "kept": ledger["kept"],
                      "skips": dict(skips), "jsonl_rows": ledger.get("jsonl_rows_written"),
                      "sanity_passes": sanity_ok,
                      "roles": summary["composition"]["occurrence_role"]}, indent=1))

    if args.strict and not sanity_ok:
        print("FATAL: direction sanity gate failed", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
