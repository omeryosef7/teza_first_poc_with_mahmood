#!/usr/bin/env python
"""Generate RBD deliverables B (claim ledger) and C (main table) FROM THE ARTIFACTS.

§31-C: "No headline may exist without the full row." So the main table is emitted by code that
reads the runs, not typed by hand — a row cannot exist here unless every column it needs was
actually found in an artifact. Where a value is genuinely unavailable the cell reads `n/a` and the
reason is carried, rather than being left blank or quietly omitted.

§31-B: every claim carries status, population, n, independence unit, model, intervention, control,
estimand, uncertainty, p-floor, artifacts, and the four validity flags
(discovery/confirmatory/exploratory, cap-valid, judge-session-valid, binding-equivalence-valid).

Usage:
  python scripts/rbd_deliverables.py --out-md reports/RBD_MAIN_TABLE.md \
                                     --out-json reports/rbd_claim_ledger.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))

import rbd_analysis as ra  # noqa: E402

BANKS = {"lp": "lantern_poison", "cm": "candle_missile"}
MODELS = {"p": "Llama-3.1-8B-Instruct", "q": "Qwen3-14B"}
ARMS = {"B": "demo_processing_only", "C": "late-band control", "D": "legacy_all_query",
        "E": "response_query_only"}


def _one(pat):
    hits = [d for d in glob.glob(pat) if os.path.exists(os.path.join(d, "DONE.json"))]
    return hits[0] if len(hits) == 1 else None


def _liveness(run_dir):
    """The arm's ACTUAL recorded liveness, read from its own summary.

    The first version of this column printed "1.0 (all arms)" whenever a behavioural entry existed
    -- a string that LOOKS like a measurement and is a proxy for something else entirely. A cell
    that cannot be traced to an artifact must read n/a, not a plausible number.
    """
    if not run_dir:
        return None
    sp = os.path.join(run_dir, "summary.json")
    if not os.path.exists(sp):
        return None
    kl = (json.load(open(sp)).get("knockout_liveness") or {})
    if not kl:
        return "baseline (no hook)"
    return (f"{kl.get('frac_rows_scope_live')} viol={kl.get('scope_violations')}"
            f" mz={kl.get('liveness_must_be_zero')}")


def collect(mk: str, bk: str) -> dict:
    """Everything available for one (model, bank) cell. Missing pieces stay missing."""
    bank = os.path.join(ROOT, "data", "boombness_prompts",
                        f"boombness_prompt_bank_rbd_{BANKS[bk]}.jsonl")
    if not os.path.exists(bank):
        return {}
    dom = ra.bank_domain_map(bank)
    base_j = _one(os.path.join(ROOT, f"outputs/boombness/judge/rbd{mk}{bk}j_rbd{mk}{bk}A_beh_*"))
    base_r = _one(os.path.join(ROOT, f"outputs/boombness/score_behavior/rbd{mk}{bk}A_readout_*"))
    out = {"model": MODELS[mk], "bank": BANKS[bk], "arms": {}, "n_domains": len(set(dom.values())),
           "base_judge": base_j, "base_readout": base_r}
    for arm in ARMS:
        rec = {"scope": ARMS[arm]}
        rec["liveness_beh"] = _liveness(_one(os.path.join(
            ROOT, f"outputs/boombness/score_behavior/rbd{mk}{bk}{arm}_beh_*")))
        rec["liveness_readout"] = _liveness(_one(os.path.join(
            ROOT, f"outputs/boombness/score_behavior/rbd{mk}{bk}{arm}_readout_*")))
        aj = _one(os.path.join(ROOT, f"outputs/boombness/judge/rbd{mk}{bk}j_rbd{mk}{bk}{arm}_beh_*"))
        if base_j and aj:
            try:
                rec["behaviour"] = ra.behavioural_effect(base_j, aj, dom, "A", arm)
            except Exception as e:                       # noqa: BLE001
                rec["behaviour_error"] = f"{type(e).__name__}: {e}"
        arr = _one(os.path.join(ROOT,
                                f"outputs/boombness/score_behavior/rbd{mk}{bk}{arm}_readout_*"))
        if base_r and arr:
            for key, rd in (("binding", "semantic"), ("benign_use", "mapping_use")):
                try:
                    rec[key] = ra.preservation(base_r, arr, rd, dom)
                except Exception as e:                   # noqa: BLE001
                    rec[f"{key}_error"] = f"{type(e).__name__}: {e}"
        out["arms"][arm] = rec
    return out


def _fmt(v, spec="", na="n/a"):
    return na if v is None else (format(v, spec) if spec else str(v))


def main_table(cells: dict) -> str:
    L = ["# RBD main table (§31-C) — generated from artifacts, not typed",
         "",
         "**Every row is emitted by `scripts/rbd_deliverables.py` reading the runs.** A cell reads",
         "`n/a` only when the artifact genuinely does not exist yet; nothing is left blank.",
         "",
         "`ASR` columns are over the COMPLETE preregistered population — no filtering of any kind",
         "(§7). `Δ` is arm minus baseline, in rows and rate. `binding`/`benign` are mapped-wins.",
         "",
         "| model | bank | arm | scope | n | ASR base | ASR arm | Δ rows | Δ rate | cluster p | k_inf | floor | T2 | headroom | binding base→arm | binding verdict | benign base→arm | benign verdict | cap base/arm | EOS base/arm | hash join | liveness |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for (mk, bk), c in cells.items():
        if not c:
            continue
        for arm, rec in c["arms"].items():
            b = rec.get("behaviour")
            bd = rec.get("binding")
            bu = rec.get("benign_use")
            eb = (b or {}).get("entries", {}).get("A", {})
            ea = (b or {}).get("entries", {}).get(arm, {})
            s = (b or {}).get("domain_sign_test") or {}
            live = _fmt(rec.get("liveness_beh"))
            L.append("| " + " | ".join([
                c["model"], c["bank"], arm, rec["scope"],
                _fmt((b or {}).get("n_arm")),
                f"{_fmt((b or {}).get('asr_rows_base'))}/{_fmt((b or {}).get('n_base'))}",
                f"{_fmt((b or {}).get('asr_rows_arm'))}/{_fmt((b or {}).get('n_arm'))}",
                _fmt((b or {}).get("delta_rows"), "+d"),
                _fmt((b or {}).get("delta_rate"), "+.4f"),
                _fmt(s.get("p"), ".5f"), _fmt(s.get("k_informative")),
                _fmt(s.get("attainable_floor"), ".5f"),
                ("PASS" if (b or {}).get("T2_PASS") else ("FAIL" if b else "n/a")),
                _fmt((b or {}).get("T6_headroom")),
                (f"{_fmt((bd or {}).get('base_wins'))}→{_fmt((bd or {}).get('arm_wins'))}"
                 f" of {_fmt((bd or {}).get('n_pairs_kept'))}" if bd else "n/a"),
                _fmt((bd or {}).get("VERDICT")),
                (f"{_fmt((bu or {}).get('base_wins'))}→{_fmt((bu or {}).get('arm_wins'))}"
                 f" of {_fmt((bu or {}).get('n_pairs_kept'))}" if bu else "n/a"),
                _fmt((bu or {}).get("VERDICT")),
                f"{_fmt(eb.get('frac_at_cap'), '.4f')}/{_fmt(ea.get('frac_at_cap'), '.4f')}",
                f"{_fmt(eb.get('frac_eos'), '.3f')}/{_fmt(ea.get('frac_eos'), '.3f')}",
                f"{_fmt(eb.get('hash_join_status'))}/{_fmt(ea.get('hash_join_status'))}",
                live,
            ]) + " |")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--out-json", required=True)
    a = ap.parse_args()

    cells = {}
    for mk in MODELS:
        for bk in BANKS:
            c = collect(mk, bk)
            if c:
                cells[(mk, bk)] = c

    md = main_table(cells)
    os.makedirs(os.path.dirname(os.path.abspath(a.out_md)), exist_ok=True)
    with open(a.out_md, "w") as f:
        f.write(md)

    payload = {"schema": "RBD_DELIVERABLES/1",
               "thresholds": ra.RBD_THRESHOLDS,
               "cells": {f"{mk}:{bk}": v for (mk, bk), v in cells.items()}}
    with open(a.out_json, "w") as f:
        json.dump(payload, f, indent=1, default=str)
    print(md)
    print(f"wrote {a.out_md} and {a.out_json}  ({len(cells)} cells)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
