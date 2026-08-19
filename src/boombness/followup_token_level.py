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


def _finite(xs):
    return [x for x in xs if x is not None and isinstance(x, (int, float)) and math.isfinite(x)]


def clustered_sem(vals_by_cluster: Dict[str, List[float]]) -> float:
    """SEM over CLUSTER means, not over rows. Occurrences within a prompt, and prompts within a
    domain, are not independent draws; a row-level sem understates by ~sqrt(rows/clusters).
    R-16 was an instance of quoting iid where it gave the friendlier answer."""
    cm = [sum(v) / len(v) for v in vals_by_cluster.values() if v]
    return sem(cm)


def curve(rows: List[Dict], metric: str, layers: Sequence[int]) -> Dict[str, Dict]:
    """{layer: {mean, sem, sem_by_prompt, sem_by_domain, n}} for one already-filtered row set.

    `n` counts FINITE contributions only — counting before the finite filter would let a NaN row
    exit the mean while still inflating the reported sample size."""
    out = {}
    for L in layers:
        c = col(metric, L)
        vs = _finite([r.get(c) for r in rows if c in r])
        by_p: Dict[str, List[float]] = collections.defaultdict(list)
        by_d: Dict[str, List[float]] = collections.defaultdict(list)
        for r in rows:
            v = r.get(c)
            if c in r and v is not None and isinstance(v, (int, float)) and math.isfinite(v):
                by_p[r["prompt_id"]].append(v)
                by_d[r["domain"]].append(v)
        out[str(L)] = {"mean": mean(vs), "sem_rowlevel_UNDERSTATES": sem(vs),
                       "sem_by_prompt": clustered_sem(by_p), "sem_by_domain": clustered_sem(by_d),
                       "n_rows": len(vs), "n_prompts": len(by_p), "n_domains": len(by_d)}
    return out


def band_mean(rows: List[Dict], metric: str, band: Sequence[int]) -> Dict:
    """Per-row mean across a layer band, then aggregated over rows.

    Records `layers_used` because metrics do NOT all cover the same layers: the logit-lens columns
    exist at only 9 of 32 depths, so a band that averages 8 layers of `d_surface` averages 2 of
    `ll|boombness`. Presenting those side by side without saying so is a real defect."""
    used = [L for L in band if any(col(metric, L) in r for r in rows[:64])]
    per_row, by_p, by_d = [], collections.defaultdict(list), collections.defaultdict(list)
    for r in rows:
        vs = _finite([r.get(col(metric, L)) for L in band if col(metric, L) in r])
        if vs:
            v = sum(vs) / len(vs)
            per_row.append(v)
            by_p[r["prompt_id"]].append(v)
            by_d[r["domain"]].append(v)
    return {"mean": mean(per_row), "sem_rowlevel_UNDERSTATES": sem(per_row),
            "sem_by_prompt": clustered_sem(by_p), "sem_by_domain": clustered_sem(by_d),
            "n_rows": len(per_row), "n_prompts": len(by_p), "n_domains": len(by_d),
            "layers_used": used, "n_layers_used": len(used)}


def prompt_weighted_mean(rows: List[Dict], metric: str, L: int) -> float:
    """Mean of PROMPT means. `demo_all` pools 1-17 rows per prompt while `query` contributes
    exactly one, so a row-weighted demo_all vs a query mean compares two different units and the
    long-demo-block prompts dominate. This is the unit-matched version."""
    c = col(metric, L)
    by_p: Dict[str, List[float]] = collections.defaultdict(list)
    for r in rows:
        v = r.get(c)
        if c in r and v is not None and isinstance(v, (int, float)) and math.isfinite(v):
            by_p[r["prompt_id"]].append(v)
    return mean([sum(v) / len(v) for v in by_p.values() if v])


def paired_last_minus_first(rows: List[Dict], metric: str, L: int) -> Dict:
    """WITHIN-PROMPT last-demo minus first-demo, restricted to prompts with >=2 demos.

    The unpaired form draws demo_first and demo_last from different prompt populations: a prompt
    with exactly ONE demo contributes a demo_first and no demo_last, and that lone demo is also the
    demo nearest the query -- the position that drives the effect. Keeping it on one side only
    inflates the gap. The paired form removes the composition confound entirely."""
    c = col(metric, L)
    by_p: Dict[str, Dict[str, float]] = collections.defaultdict(dict)
    for r in rows:
        if r.get("is_query_occurrence"):
            continue
        v = r.get(c)
        if v is None or not isinstance(v, (int, float)) or not math.isfinite(v):
            continue
        if r.get("is_first_demo"):
            by_p[r["prompt_id"]]["first"] = v
        if r.get("is_last_demo"):
            by_p[r["prompt_id"]]["last"] = v
    diffs, doms = [], collections.defaultdict(list)
    dom_of = {r["prompt_id"]: r["domain"] for r in rows}
    for pid, d in by_p.items():
        if "first" in d and "last" in d and d["first"] != d["last"]:
            diffs.append(d["last"] - d["first"])
            doms[dom_of.get(pid, "?")].append(d["last"] - d["first"])
    return {"paired_mean": mean(diffs), "sem_by_prompt": sem(diffs),
            "sem_by_domain": clustered_sem(doms), "n_pairs": len(diffs),
            "n_domains": len(doms),
            "per_domain_mean": {k: mean(v) for k, v in sorted(doms.items())}}


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

    # Per-metric layer lists. The logit-lens columns exist at only 9 of 32 depths while the
    # direction columns exist at all 32; taking `layers` from metrics[0] alone would silently
    # apply one metric's depth coverage to every other metric.
    disc = discover_columns(rows)
    metric_layers = {m: sorted(disc.get(m, [])) for m in metrics}
    layers = metric_layers.get(metrics[0], [])
    if not layers:
        print(f"FATAL: no layers found for metric {metrics[0]}", file=sys.stderr)
        return 2
    for m, ls in metric_layers.items():
        if not ls:
            print(f"WARNING: metric {m} has no columns in this extract", file=sys.stderr)

    # ---- the gate that must pass before any curve is read ------------------------------- #
    sanity = direction_sanity(rows, "d_surface|cos", layers)
    sanity_ok = sanity["n_layers_positive"] > sanity["n_layers"] / 2

    # ---- summary ------------------------------------------------------------------------ #
    cond_rows = [r for r in rows if r["condition"] == args.condition]
    summary: Dict = {
        "label": "Phase B — occurrence-resolved token-level Boombness",
        "inputs": {"extract_run": os.path.abspath(args.run),
                   "refusalness_run": os.path.abspath(args.refusalness) if args.refusalness else None},
        # Stated exactly. An earlier revision claimed query kinds were "never pooled" while the
        # summary cells pooled them; a false provenance string on disk is worse than none.
        "filters": {
            "query_kind": args.query_kind or "ALL — POOLED INTO EVERY SUMMARY CELL",
            "bank_blocks": args.bank_blocks or "ALL — POOLED",
            "family_slot": args.slot if args.slot != "" else "ALL — POOLED (slots 1/2 are sibling "
                                                             "families sharing demonstrations; "
                                                             "this is the R-18 defect class)",
            "self_fit": "excluded",
            "pooling_warning": ("this run pools the axes marked POOLED; only a run with "
                                "--query-kind and --slot set is safe to quote per-cell")
            if (not args.query_kind or args.slot == "") else None},
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
        "metric_layers": metric_layers,
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
            ml = metric_layers[m]
            summary["by_role"][m][role] = {"n": len(rs), "layers": curve(rs, m, ml)}
            summary["bands"][m][role] = {b: band_mean(rs, m, [L for L in rng if L in ml])
                                         for b, rng in BANDS.items()}
        # all demo occurrences pooled — the plan's "all demo codewords aggregate"
        rs_demo = [r for r in cond_rows if r["occurrence_role"] != "query"]
        ml = metric_layers[m]
        summary["by_role"][m]["demo_all"] = {"n": len(rs_demo), "layers": curve(rs_demo, m, ml)}
        summary["bands"][m]["demo_all"] = {b: band_mean(rs_demo, m, [L for L in rng if L in ml])
                                           for b, rng in BANDS.items()}

    # Q1 does Boombness grow across demo occurrences?  Q2 is the query more or less bomb-like?
    #
    # THE CONTROL IS NOT OPTIONAL. A repetition gradient that also appears in `benign_literal` --
    # where no codeword->concept mapping is ever taught and there is nothing to "become" -- is a
    # general property of repeated tokens, not evidence about doublespeak. So every contrast is
    # computed for EVERY condition, and the doublespeak-specific quantity is the EXCESS over the
    # matched control, natural_doublespeak minus benign_literal.
    CONTROL_COND = "benign_literal"
    conds = sorted({r["condition"] for r in rows})
    for m in metrics:
        ml = metric_layers[m]
        per_cond = {}
        for cond in conds:
            crows = [r for r in rows if r["condition"] == cond]
            c = {}
            for L in ml:
                cc = col(m, L)
                g = {role: _finite([r.get(cc) for r in crows if r["occurrence_role"] == role])
                     for role in ROLES}
                demo_rows = [r for r in crows if not r.get("is_query_occurrence")]
                q_rows = [r for r in crows if r.get("is_query_occurrence")]
                g["demo_all"] = _finite([r.get(cc) for r in demo_rows])
                paired = paired_last_minus_first(crows, m, L)
                c[str(L)] = {
                    "last_minus_first_demo_UNPAIRED": mean(g["demo_last"]) - mean(g["demo_first"]),
                    "d_last_vs_first_UNPAIRED": cohens_d(g["demo_last"], g["demo_first"]),
                    "last_minus_first_demo_PAIRED": paired["paired_mean"],
                    "paired_n": paired["n_pairs"],
                    "paired_sem_by_domain": paired["sem_by_domain"],
                    "paired_per_domain_mean": paired["per_domain_mean"],
                    "query_minus_demo_all_ROWWEIGHTED": mean(g["query"]) - mean(g["demo_all"]),
                    "query_minus_demo_all_PROMPTWEIGHTED": (
                        prompt_weighted_mean(q_rows, m, L) - prompt_weighted_mean(demo_rows, m, L)),
                    "d_query_vs_demo_all": cohens_d(g["query"], g["demo_all"]),
                    "n": {k: len(v) for k, v in g.items()},
                }
            per_cond[cond] = c
        summary["role_contrasts"][m] = per_cond

        # the excess over the matched control -- the only doublespeak-specific quantity here
        if args.condition in per_cond and CONTROL_COND in per_cond:
            exc = {}
            for L in ml:
                a, b = per_cond[args.condition][str(L)], per_cond[CONTROL_COND][str(L)]
                exc[str(L)] = {
                    "paired_last_minus_first_EXCESS": (a["last_minus_first_demo_PAIRED"]
                                                       - b["last_minus_first_demo_PAIRED"]),
                    "query_minus_demo_all_EXCESS_promptweighted": (
                        a["query_minus_demo_all_PROMPTWEIGHTED"]
                        - b["query_minus_demo_all_PROMPTWEIGHTED"]),
                    "treated": args.condition, "control": CONTROL_COND,
                    "n_treated_pairs": a["paired_n"], "n_control_pairs": b["paired_n"],
                }
            summary.setdefault("matched_control_excess", {})[m] = exc

    # Q4 does d_surface differ from d_naive / d_context?
    for role in ROLES + ["demo_all"]:
        rs = ([r for r in cond_rows if r["occurrence_role"] != "query"] if role == "demo_all"
              else [r for r in cond_rows if r["occurrence_role"] == role])
        summary["direction_comparison"][role] = {
            m: {b: band_mean(rs, m, [L for L in rng if L in metric_layers[m]])
                for b, rng in BANDS.items()}
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
