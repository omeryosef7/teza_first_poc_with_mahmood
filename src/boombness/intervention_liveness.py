"""intervention_liveness.py — did the hook MATTER, not merely did it FIRE?

THE DISTINCTION THIS MODULE EXISTS FOR. Every intervention arm in this repo records a liveness
block: `fired: true`, `n_positions_written: 28`, `frac_rows_decode_live: 1.0`. Those fields are
honest and they answer a real question. They answer the WRONG one.

A concurrent session's **C-20** is the case that proves it: a rescue arm reported `fired: true` and
`n_positions_written: 28` for a patch that wrote *the value already present*. Below the knockout
band the clean and knocked-out activations are bit-identical, so the hook fired, wrote, and changed
nothing. **Three published claims cited that arm as a specificity control and none of them had run
one.** Liveness told the truth; the truth it told was narrower than the question being asked.

    liveness  answers  "did the hook execute?"
    THIS      answers  "did the hook change what the model wrote?"

The second is the one that licenses an intervention claim, and it is one comparison: an arm's
generations against its own control's, joined on `prompt_id` and hashed. Cheap, and it is the check
that would have caught C-20 before three claims rested on it.

THE TWO FAILURE MODES IT SEPARATES, which `fired: true` cannot tell apart:

    hook fires, changes computation, no behavioural effect  -> a real DISSOCIATION
    hook fires, changes NOTHING,     no behavioural effect  -> a NO-OP ARM (C-20)

Both report `fired: true`. Both show a null. Only this comparison distinguishes them, and the
difference decides whether a null is a finding or an artifact.

Text is read only to hash it. Nothing but scalars and ids is emitted. Run in the MAIN loop or a
SLURM/CPU job, NEVER in a subagent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FailureLedger, RunDir  # noqa: E402

SCHEMA = "INTERVENTION_LIVENESS/1"

#: THE PREDICATE IS EXACT ZERO, NOT A THRESHOLD — and the first draft got this wrong.
#:
#: A draft refused any arm below 0.10. A peer session then measured divergence across all 18
#: intervention contrasts in its phase: sixteen legitimate arms span **0.8187–1.0000**, both known
#: no-ops are **exactly 0.0000**, and NOTHING lands in between. So 0.10 refused nothing real — but
#: it was calibrated on a sample containing no small-but-real arms, and that is the problem. Every
#: arm in that sample is a broad-span mask or patch. A single-position patch,
#: `--rescue-n-positions 1`, or an intervention gated on a rare row property could legitimately
#: touch 3 rows in 96, and a threshold tuned on broad-span arms would refuse it *authoritatively*.
#:
#: Exact zero needs no calibration. Under GREEDY decoding an arm that changed anything at all
#: cannot land on 0.0000 across a whole population; only a bit-identical computation does that.
#: So zero REFUSES and the ambiguous region WARNS.
ZERO_DIVERGENCE = 0.0
#: Below this, an arm is flagged for inspection but NOT refused. It is a warning band, not a gate.
SMALL_DIVERGENCE = 0.10


class NoOpArmError(AssertionError):
    """An intervention arm whose generations are BIT-IDENTICAL to its control's."""


def diagnose(frac_differing: Optional[float], fired: Optional[bool] = None) -> Dict[str, Any]:
    """Divergence alone under-determines the diagnosis; pair it with the liveness `fired` field.

    Three cases that a single number cannot separate, and only the middle one is the bug:

        fired=False, div=0          -> the hook NEVER RAN. Instrument failure, not a no-op arm.
        fired=True,  div=0          -> C-20. The hook ran and wrote the value already present.
        fired=True,  0 < div < 0.10 -> a legitimately SMALL intervention. Warn, do not refuse.

    This is R-85's lesson arriving from the other side: there, a request needed its matching
    outcome field; here, an outcome field needs its matching request field.
    """
    if frac_differing is None:
        return {"verdict": "NO_COMPARISON", "refuse": True,
                "reading": "arm and control share no prompt_ids; nothing was compared"}
    if frac_differing == ZERO_DIVERGENCE:
        if fired is False:
            return {"verdict": "HOOK_NEVER_RAN", "refuse": True,
                    "reading": "liveness says the hook did not fire AND generations are identical: "
                               "this is an instrument failure, not a no-op arm"}
        return {"verdict": "NOOP_ARM", "refuse": True,
                "reading": ("generations are BIT-IDENTICAL across the population. Under greedy "
                            "decoding only an unchanged computation does that" +
                            (" — and liveness says the hook DID fire, which is exactly C-20: it "
                             "wrote the value already present" if fired else ""))}
    if frac_differing < SMALL_DIVERGENCE:
        return {"verdict": "SMALL_BUT_REAL", "refuse": False,
                "reading": ("the arm changed something, but on few rows. Legitimate for a "
                            "single-position patch or a rarely-triggered intervention; suspicious "
                            "for a broad-span mask. NOT refused — inspect it.")}
    return {"verdict": "OK", "refuse": False, "reading": "the arm changed what the model wrote"}


def _sha(t: str) -> str:
    return hashlib.sha256((t or "").encode("utf-8")).hexdigest()


def _gens(run_dir: str) -> Dict[str, str]:
    p = os.path.join(run_dir, "gens.jsonl")
    if not os.path.exists(p):
        raise FileNotFoundError(f"no gens.jsonl in {run_dir}")
    out = {}
    with open(p) as fh:
        for line in fh:
            line = line.strip()
            if line:
                g = json.loads(line)
                out[g.get("prompt_id")] = _sha(g.get("generation", ""))
    return out


def generation_divergence(arm_dir: str, control_dir: str, label: str = "",
                          fired: Optional[bool] = None) -> Dict[str, Any]:
    """How many rows did this intervention actually change?

    Returns hashes-only counts. `frac_differing` is the number that matters; `n_common` is its
    denominator and travels with it.
    """
    A, B = _gens(arm_dir), _gens(control_dir)
    common = sorted(set(A) & set(B))
    differing = [p for p in common if A[p] != B[p]]
    n = len(common)
    frac = (len(differing) / n) if n else None
    out = {
        "label": label or os.path.basename(arm_dir),
        "arm_dir": os.path.abspath(arm_dir), "control_dir": os.path.abspath(control_dir),
        "n_common": n, "n_arm_rows": len(A), "n_control_rows": len(B),
        "n_identical": n - len(differing), "n_differing": len(differing),
        "frac_differing": frac,
        "is_noop_arm": (frac is not None and frac == ZERO_DIVERGENCE),
        "zero_divergence": ZERO_DIVERGENCE, "small_divergence": SMALL_DIVERGENCE,
        "NOTE": ("`fired: true` cannot distinguish an arm that changes the computation and has no "
                 "behavioural effect (a real dissociation) from one that changes NOTHING and has "
                 "no behavioural effect (a no-op, cf. C-20). This can."),
    }
    out["diagnosis"] = diagnose(frac, fired)
    out["fired_reported_by_liveness"] = fired
    return out


def assert_changed_generations(result: Dict[str, Any]) -> None:
    """Refuse an intervention claim whose arm did not change what the model wrote."""
    # NOTE: the n_common==0 case is NOT special-cased here. It used to be, and that meant the
    # empty-comparison path raised with a different message than every other refusal and bypassed
    # the diagnosis entirely — two code paths for one decision. `diagnose(None)` returns
    # NO_COMPARISON, so there is now exactly one.
    d = result.get("diagnosis") or diagnose(result.get("frac_differing"),
                                             result.get("fired_reported_by_liveness"))
    if d["refuse"]:
        raise NoOpArmError(
            f"{result['label']} [{d['verdict']}]: "
            f"{result['n_differing']}/{result['n_common']} generations differ. {d['reading']}. "
            "A liveness block reporting `fired: true` does NOT license a causal claim about an arm "
            "that wrote the value already present (C-20).")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pair", action="append", default=[], metavar="LABEL:ARM_DIR:CONTROL_DIR",
                    help="colon-separated; repeat per arm")
    ap.add_argument("--pairs-file", default="",
                    help="JSON list of {label, arm, control, fired?} — `fired` is the liveness "
                         "block's report, which separates HOOK_NEVER_RAN from NOOP_ARM")
    ap.add_argument("--tag", default="ivlive")
    args = ap.parse_args()

    specs: List[Dict[str, str]] = []
    if args.pairs_file:
        specs.extend(json.load(open(args.pairs_file)))
    for s in args.pair:
        lab, a, c = s.split(":")
        specs.append({"label": lab, "arm": a, "control": c})
    if not specs:
        ap.error("give --pair or --pairs-file")

    ledger = FailureLedger()
    run = RunDir("intervention_liveness", args, tag=args.tag)
    rows = []
    for sp in specs:
        r = generation_divergence(sp["arm"], sp["control"], sp.get("label", ""),
                                  fired=sp.get("fired"))
        rows.append(r)
        run.log_row(r)
        try:
            assert_changed_generations(r)
            ledger.ok()
        except NoOpArmError:
            ledger.fail(r["diagnosis"]["verdict"].lower(), r["label"])
        print(f"  {r['label'][:32]:32s} differing={r['n_differing']}/{r['n_common']} "
              f"frac={r['frac_differing']}  {r['diagnosis']['verdict']}")

    out = {"schema": SCHEMA, "zero_divergence": ZERO_DIVERGENCE,
           "small_divergence": SMALL_DIVERGENCE, "arms": rows,
           "VERDICT_NOTE": ("An arm passing this check has changed what the model wrote. An arm "
                            "FAILING it may still report `fired: true` truthfully -- that is "
                            "exactly the C-20 failure, where a hook wrote the value already "
                            "present and three claims cited the arm as a specificity control.")}
    p = os.path.join(run.path, "intervention_liveness.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    import collections as _c
    verdicts = _c.Counter(r["diagnosis"]["verdict"] for r in rows)
    run.finish(summary={"n_arms": len(rows), "verdicts": dict(verdicts),
                        "n_refused": sum(1 for r in rows if r["diagnosis"]["refuse"])},
               ledger=ledger)
    print(f"[ivlive] wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
