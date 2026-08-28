"""margin_exposure.py — a forced-choice count, with the two numbers that make it readable.

WHY THIS EXISTS. `14/18` and `15/48` are not comparable, and nothing in this repo made that
visible. *18 rows at median |margin| 10.0* and *32 rows at median |margin| 1.075* are immediately
comparable, and they are the same two counts. A mapped-wins fraction says how many rows fell on
each side; it says nothing about how far from the line they fell, which is the only thing that
determines whether a perturbation can move them.

THE ERROR THIS MODULE REFUSES, which cost this sprint three separate corrections:

    C-33         a threshold carried across n as a RATE, when critical_k moves with n
    §5.18.1      the ≥0.667 installation screen applied at n=18, where critical_k is 14
    §5.20        a perturbation window measured on Qwen3-14B applied to LLAMA banks
    §5.20.1      then ONE Llama window (main, 0.4616) applied to the ticket_bomb bank (0.3202)

Four instances, one shape: **a scale quoted away from the population it was measured on.** The
last two are this module's business, and the fix is not documentation — it is that an at-risk
count cannot be computed from a window whose provenance does not match the run.

THE ASYMMETRY THAT MAKES A BORROWED WINDOW DANGEROUS. An over-large window is CONSERVATIVE for a
positive claim and ANTI-CONSERVATIVE for a null:

  * INSTALLED / effect-present — inflating the at-risk set only makes the bound harder to pass.
    Surviving on a borrowed window implies surviving on the right one. Measured: a peer's at-risk
    counts 10/5/12/6 became 4/1/2/0 at the correct scale and every verdict held either way.
  * "no degradation" — an inflated window MANUFACTURES exposure that is not there. This produced
    §5.20's −26, my `main` −10, and a peer's withdrawn "C5 does not survive its own worst case".

So a borrowed window cannot damage the results that carry effects and can only damage the nulls.
The claims most likely to be re-derived are exactly where the error is harmless. **A robustness
check that is silently one-sided in favour of the headline is worse than none**, which is why the
provenance check below is a hard refusal and not a warning.

Scalars and ids only. No generation, no judge, no text.
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
from typing import Any, Dict, List, Optional, Sequence

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FailureLedger, RunDir, read_jsonl  # noqa: E402

SCHEMA = "MARGIN_EXPOSURE/1"


class BorrowedScaleError(AssertionError):
    """An at-risk count was requested against a window measured on a DIFFERENT population."""


def _provenance(run_dir: str) -> Dict[str, Optional[str]]:
    """The population a scale is or is not valid for: RESOLVED model + bank CONTENT hash.

    THE FIRST VERSION OF THIS READ `config.args.model` AND THE BANK'S BASENAME, AND BOTH WERE
    WRONG — a peer found it by pointing the module at the very pair that produced the 0.3202
    window, and being refused:

        config.args.model is None when --model is not passed, so an identical model reads as
        "DEFAULT" from one launch and "meta-llama/Llama-3.1-8B-Instruct" from another. That is
        LAUNCH STYLE, not science, and it refused a valid measurement.

    That failure direction is the serious one. **The guard would have refused the measurement
    that DETECTED the error the guard exists to prevent** — 0.3202 came from exactly that pair,
    and it is what reversed the peer's R-111 and produced their C-37. An instrument that refuses
    the work that catches its own target bug is conservative in a direction that suppresses
    corrections, which is the same one-sidedness this module warns about for windows, one level
    up.

    The basename had the opposite and quieter failure: two DIFFERENT banks sharing a basename in
    different directories would have been silently ACCEPTED. A false refusal is loud; a false
    accept is not.

    `metadata.json` already records what identity actually requires, so both are fixed by reading
    the right field: the resolved `model`, the resolved weights commit, and `bank_rows_sha16` —
    a hash of the bank's ROWS, which is immune to path, basename and launch style alike.
    """
    meta: Dict[str, Any] = {}
    mp = os.path.join(run_dir, "metadata.json")
    if os.path.isfile(mp):
        try:
            meta = json.load(open(mp))
        except Exception:
            meta = {}
    cfg: Dict[str, Any] = {}
    cp = os.path.join(run_dir, "config.json")
    if os.path.isfile(cp):
        try:
            cfg = json.load(open(cp)).get("args") or {}
        except Exception:
            cfg = {}
    bank_id = meta.get("bank_rows_sha16")
    if not bank_id:
        # Fall back only when the hash is absent, and say so in the value itself so a
        # provenance printed in a refusal cannot be mistaken for a content-addressed one.
        bank_id = "basename:" + (os.path.basename(cfg.get("bank") or "") or "UNKNOWN")
    return {
        "model": meta.get("model") or cfg.get("model") or "UNKNOWN",
        "model_commit": meta.get("model_revision_resolved_commit") or None,
        "bank_rows_sha16": bank_id,
    }


def assert_complete(run_dir: str) -> int:
    """Refuse a run that silently lost rows. R-105 parity, and it was missing here.

    FOUND IN REVIEW, in this module, one tick after writing it. `margin_exposure` happily
    computed `median |margin|` and an at-risk count over an arm that had dropped **22 of 40 rows**
    to OOM, reporting `n=18` as though 18 were the population. Both of its two numbers describe
    the survivors and neither says so — which is precisely the failure the option-mass gate had
    (V-54) and that a peer's `mapping_installation_verdict` already refuses.

    It has a published consequence. The Qwen3 window quoted as **1.2499** was MEASURED from that
    attrited pair, i.e. on the 18 rows where the batch-16 arm survived — and those are the SHORT
    rows, because the perturbation being measured is what killed the long ones. So the scale was
    measured on a subset selected BY the perturbation, which is the sharpest form of the
    borrowed-scale error this module exists to refuse: not borrowed from another population, but
    from a biased sample of its own.

    Note this can make a window UNMEASURABLE rather than merely unmeasured — on Qwen3/longpreQ14B
    no complete batch-16 run exists or can exist, since batch 16 is what OOMs. That is the honest
    answer, and an honest blank beats an estimate.
    """
    sp = os.path.join(run_dir, "summary.json")
    if not os.path.isfile(sp):
        return 0
    try:
        n_failed = int(((json.load(open(sp)) or {}).get("failures") or {}).get("n_failed") or 0)
    except Exception:
        return 0
    if n_failed:
        raise BorrowedScaleError(
            f"{os.path.basename(run_dir)}: ATTRITED population — {n_failed} rows failed. "
            "median |margin| and the at-risk count would describe only the survivors, and when "
            "the attrition is caused by the very perturbation being measured the survivors are "
            "selected BY it. Refusing rather than reporting a subset as a population.")
    return 0


def margins(run_dir: str, query_kind: str = "semantic_forced_choice") -> Dict[str, float]:
    """Per prompt_id: logp_concept − logp_codeword, the quantity mapped-wins thresholds at 0.

    The margin is the decision-relevant statistic and neither logp is. Measured on one arm,
    |Δ logp_codeword| was 35× |Δ logp_concept| in absolute terms and 0.36× once normalised —
    because logp_concept sits at −0.006 (p≈0.994), so its absolute deltas are tiny by
    construction. Both readings are artifacts of scale; the margin has no such freedom.
    """
    out: Dict[str, float] = {}
    for r in read_jsonl(os.path.join(run_dir, "results.jsonl")):
        if r.get("query_kind") != query_kind:
            continue
        if r.get("logp_concept") is None or r.get("logp_codeword") is None:
            continue
        out[r["prompt_id"]] = float(r["logp_concept"]) - float(r["logp_codeword"])
    return out


def _raw(run_dir: str, query_kind: str) -> Dict[str, Any]:
    """Per prompt_id: the (concept, codeword) logp PAIR, for the did-the-computation-change count."""
    out: Dict[str, Any] = {}
    for r in read_jsonl(os.path.join(run_dir, "results.jsonl")):
        if r.get("query_kind") != query_kind:
            continue
        if r.get("logp_concept") is None or r.get("logp_codeword") is None:
            continue
        out[r["prompt_id"]] = (float(r["logp_concept"]), float(r["logp_codeword"]))
    return out


def measure_window(run_a: str, run_b: str,
                   query_kind: str = "semantic_forced_choice") -> Dict[str, Any]:
    """MEASURE a perturbation scale from two runs that differ only in the perturbation.

    Returns the scale WITH its provenance attached, because a scale without provenance is the
    thing this module exists to refuse. Both runs must share (model, bank) — measuring a window
    across two populations would produce a number belonging to neither.
    """
    assert_complete(run_a)
    assert_complete(run_b)
    pa, pb = _provenance(run_a), _provenance(run_b)
    if pa != pb:
        raise BorrowedScaleError(
            f"cannot MEASURE a window across different populations: {pa} vs {pb}. A perturbation "
            "scale is a property of one model-and-bank.")
    A, B = margins(run_a, query_kind), margins(run_b, query_kind)
    RA, RB = _raw(run_a, query_kind), _raw(run_b, query_kind)
    common = sorted(set(A) & set(B))
    n_identical_logps = sum(1 for p in common
                            if p in RA and p in RB and RA[p] == RB[p])
    if not common:
        raise BorrowedScaleError("the two runs share no prompt_ids; nothing was compared")
    d = [abs(A[p] - B[p]) for p in common]
    flips = [p for p in common if (A[p] > 0) != (B[p] > 0)]
    # NAME THE DEFINITION. A peer's count and mine disagreed (0/48 vs 1/48) and both were right:
    # they counted rows identical on BOTH logps ("did the computation change"), this counts rows
    # identical on the MARGIN ("could the decision change"). The discrepant row had both logps
    # shifted by exactly -9.091e-02 -- a COMMON-MODE shift that cancels in the difference. The
    # margin definition is the correct one for exposure, because the margin is what the predicate
    # thresholds; but calling it "bit_identical" reads as "the row did not change", and that row
    # changed measurably on both logits. So both are reported, each under its own name.
    return {
        "scale_max": max(d), "scale_median": statistics.median(d),
        "n_common": len(common),
        "n_identical_margin": sum(1 for x in d if x == 0.0),
        "n_identical_both_logps": n_identical_logps,
        "n_verdict_flips": len(flips),
        "provenance": pa, "measured_from": [os.path.basename(run_a), os.path.basename(run_b)],
        "NOTE": ("this scale is valid ONLY for this (model, bank). Quoting it elsewhere is the "
                 "error that produced three corrections in this sprint."),
    }


def exposure(run_dir: str, window: Dict[str, Any], scale_name: str,
             query_kind: str = "semantic_forced_choice") -> Dict[str, Any]:
    """The two numbers, against a NAMED window whose provenance is checked against the run.

    `scale_name` is required and free-text on purpose: an at-risk count is meaningless without
    saying at-risk-of-WHAT. The batch artifact (0.4616 on Llama/main, 1.2499 on Qwen3/longpreQ14B)
    and the judge noise floor are different numbers on different quantities, and a bare
    "at_risk=32" invites exactly the carry-over this module refuses.
    """
    if not scale_name or not scale_name.strip():
        raise BorrowedScaleError("scale_name is required: an at-risk count must say at-risk of WHAT")
    assert_complete(run_dir)
    pr, pw = _provenance(run_dir), window.get("provenance")
    if pr != pw:
        raise BorrowedScaleError(
            f"BORROWED SCALE: window was measured on {pw} but this run is {pr}. Measured windows "
            "differ by 3.9x across banks of the SAME model family (main 0.4616 vs ticket_bomb "
            "0.3202) and 2.7x across models. Measure it on this population.")
    m = margins(run_dir, query_kind)
    if not m:
        raise BorrowedScaleError(f"{os.path.basename(run_dir)}: no scorable {query_kind} rows")
    W = float(window["scale_max"])
    vals = sorted(m.values(), key=abs)
    at_risk = [p for p, v in m.items() if abs(v) < W]
    wins = [p for p, v in m.items() if v > 0]
    return {
        "run": os.path.basename(run_dir), "n": len(m),
        "wins": len(wins), "median_abs_margin": statistics.median(abs(v) for v in m.values()),
        "min_abs_margin": abs(vals[0]),
        "scale_name": scale_name, "scale_value": W, "scale_provenance": pw,
        "at_risk": len(at_risk),
        "at_risk_that_are_wins": sum(1 for p in at_risk if m[p] > 0),
        "at_risk_that_are_losses": sum(1 for p in at_risk if m[p] <= 0),
        "READING_NOTE": (
            f"{len(wins)}/{len(m)} is not comparable across banks; {len(m)} rows at median "
            f"|margin| {statistics.median(abs(v) for v in m.values()):.3f} with {len(at_risk)} "
            f"inside the {scale_name} scale ({W:.4f}) is. The at-risk split into wins and losses "
            "matters for a bound: at-risk LOSSES can only move a count UP, so they help a "
            "'preserved' claim and hurt a 'collapse' one."),
    }


def adversarial_bound(base_dir: str, arm_dir: str, window: Dict[str, Any], scale_name: str,
                      claim: str, query_kind: str = "semantic_forced_choice") -> Dict[str, Any]:
    """Flip EVERY at-risk row against `claim`, counting only the ones that can hurt.

    `claim` is "preserved" (the arm does not lower the count) or "collapse" (it does). Only rows
    that can damage the claim are flipped — at-risk rows already lying the wrong way can only
    help, and counting them would make the bound adversarial against itself.

    A FAILED BOUND IS UNINFORMATIVE, NOT ADVERSE. It assumes every at-risk row in both arms flips
    the worst way at once. Measured against that: on the one occasion a real perturbation was
    applied, exactly one at-risk row existed and exactly one flipped — and on two other banks the
    batch path changed every row's logits and moved NO verdict at all. A bound that fails means
    the bound cannot settle the claim, so the magnitude must be measured.
    """
    if claim not in ("preserved", "collapse"):
        raise ValueError("claim must be 'preserved' or 'collapse'")
    eb = exposure(base_dir, window, scale_name, query_kind)
    ea = exposure(arm_dir, window, scale_name, query_kind)
    A, B = margins(base_dir, query_kind), margins(arm_dir, query_kind)
    common = sorted(set(A) & set(B))
    W = float(window["scale_max"])
    wa = sum(1 for p in common if A[p] > 0)
    wb = sum(1 for p in common if B[p] > 0)
    if claim == "preserved":       # attack it: push the arm DOWN and the baseline UP
        wa_adv = wa + sum(1 for p in common if abs(A[p]) < W and A[p] <= 0)
        wb_adv = wb - sum(1 for p in common if abs(B[p]) < W and B[p] > 0)
    else:                          # attack a collapse: push the arm UP and the baseline DOWN
        wa_adv = wa - sum(1 for p in common if abs(A[p]) < W and A[p] > 0)
        wb_adv = wb + sum(1 for p in common if abs(B[p]) < W and B[p] <= 0)
    return {
        "claim": claim, "n": len(common),
        "observed": {"baseline": wa, "arm": wb, "delta": wb - wa},
        "adversarial": {"baseline": wa_adv, "arm": wb_adv, "delta": wb_adv - wa_adv},
        "baseline_exposure": eb, "arm_exposure": ea,
        "scale_name": scale_name, "scale_value": W,
        "ASYMMETRY_NOTE": (
            "An over-large window is CONSERVATIVE here if the claim carries an effect and "
            "ANTI-CONSERVATIVE if it is a null. A borrowed window cannot damage an effect-present "
            "result and can ONLY damage a 'no degradation' one -- so this check is silently "
            "one-sided in favour of headlines unless the scale is measured on THIS population."),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--measure-window", nargs=2, metavar=("RUN_A", "RUN_B"), required=True,
                    help="two runs differing ONLY in the perturbation, same model and bank")
    ap.add_argument("--scale-name", required=True,
                    help="what the scale IS, e.g. 'batch16-vs-batch1'. Required: a bare at-risk "
                         "count invites the carry-over error this module refuses.")
    ap.add_argument("--exposure", action="append", default=[], metavar="RUNDIR")
    ap.add_argument("--bound", action="append", default=[], metavar="CLAIM:BASELINE:ARM",
                    help="claim is 'preserved' or 'collapse'")
    ap.add_argument("--query-kind", default="semantic_forced_choice")
    ap.add_argument("--tag", default="margex")
    args = ap.parse_args()

    ledger = FailureLedger()
    run = RunDir("margin_exposure", args, tag=args.tag)
    win = measure_window(*args.measure_window, query_kind=args.query_kind)
    print(f"[margex] MEASURED scale '{args.scale_name}' on {win['provenance']}: "
          f"max {win['scale_max']:.4f} median {win['scale_median']:.4f} "
          f"({win['n_identical_margin']}/{win['n_common']} identical MARGIN, "
          f"{win['n_identical_both_logps']} identical on both logps, "
          f"{win['n_verdict_flips']} verdict flips)")
    run.log_row({"kind": "window", **win})

    rows: List[Dict[str, Any]] = []
    for d in args.exposure:
        try:
            e = exposure(d, win, args.scale_name, args.query_kind)
            rows.append(e)
            run.log_row({"kind": "exposure", **e})
            print(f"  {e['run'][:44]:44s} {e['wins']}/{e['n']}  median|margin| "
                  f"{e['median_abs_margin']:7.3f}  at-risk {e['at_risk']:3d} "
                  f"({e['at_risk_that_are_wins']}w/{e['at_risk_that_are_losses']}l)")
            ledger.ok()
        except BorrowedScaleError as ex:
            ledger.fail("borrowed_scale", str(ex)[:160])
            print(f"  REFUSED {os.path.basename(d)}: {ex}")
    for spec in args.bound:
        claim, base, arm = spec.split(":", 2)
        try:
            b = adversarial_bound(base, arm, win, args.scale_name, claim, args.query_kind)
            rows.append(b)
            run.log_row({"kind": "bound", **b})
            o, a = b["observed"], b["adversarial"]
            print(f"  BOUND[{claim}] {o['baseline']}/{b['n']}->{o['arm']}/{b['n']} "
                  f"({o['delta']:+d})  adversarial {a['baseline']}->{a['arm']} ({a['delta']:+d})")
            ledger.ok()
        except (BorrowedScaleError, ValueError) as ex:
            ledger.fail("bound_refused", str(ex)[:160])
            print(f"  REFUSED bound {spec}: {ex}")

    out = {"schema": SCHEMA, "window": win, "rows": rows}
    p = os.path.join(run.path, "margin_exposure.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    run.finish(summary={"n_rows": len(rows), "scale": args.scale_name}, ledger=ledger)
    print(f"[margex] wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
