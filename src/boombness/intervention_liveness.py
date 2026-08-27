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

#: An intervention that changes fewer than this fraction of generations is not doing enough to
#: support a causal claim about it. It is deliberately NOT 0: a hook that moves 1 row in 96 has
#: fired and mattered on 1 row, which is not an intervention, it is a rounding error.
MIN_DIVERGENCE = 0.10


class NoOpArmError(AssertionError):
    """An intervention arm whose generations do not differ from its control's."""


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


def generation_divergence(arm_dir: str, control_dir: str, label: str = "") -> Dict[str, Any]:
    """How many rows did this intervention actually change?

    Returns hashes-only counts. `frac_differing` is the number that matters; `n_common` is its
    denominator and travels with it.
    """
    A, B = _gens(arm_dir), _gens(control_dir)
    common = sorted(set(A) & set(B))
    differing = [p for p in common if A[p] != B[p]]
    n = len(common)
    frac = (len(differing) / n) if n else None
    return {
        "label": label or os.path.basename(arm_dir),
        "arm_dir": os.path.abspath(arm_dir), "control_dir": os.path.abspath(control_dir),
        "n_common": n, "n_arm_rows": len(A), "n_control_rows": len(B),
        "n_identical": n - len(differing), "n_differing": len(differing),
        "frac_differing": frac,
        "is_noop_arm": (frac is not None and frac < MIN_DIVERGENCE),
        "min_divergence": MIN_DIVERGENCE,
        "NOTE": ("`fired: true` cannot distinguish an arm that changes the computation and has no "
                 "behavioural effect (a real dissociation) from one that changes NOTHING and has "
                 "no behavioural effect (a no-op, cf. C-20). This can."),
    }


def assert_changed_generations(result: Dict[str, Any]) -> None:
    """Refuse an intervention claim whose arm did not change what the model wrote."""
    if result["n_common"] == 0:
        raise NoOpArmError(
            f"{result['label']}: arm and control share no prompt_ids — nothing was compared.")
    if result["is_noop_arm"]:
        raise NoOpArmError(
            f"{result['label']}: the intervention changed only "
            f"{result['n_differing']}/{result['n_common']} generations "
            f"(frac {result['frac_differing']:.4f} < {MIN_DIVERGENCE}). A liveness block reporting "
            "`fired: true` does NOT license a causal claim about an arm that wrote the value "
            "already present (C-20). Either the hook is a no-op at this site, or the arm is not "
            "the intervention it is labelled as.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pair", action="append", default=[], metavar="LABEL:ARM_DIR:CONTROL_DIR",
                    help="colon-separated; repeat per arm")
    ap.add_argument("--pairs-file", default="", help="JSON list of {label, arm, control}")
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
        r = generation_divergence(sp["arm"], sp["control"], sp.get("label", ""))
        rows.append(r)
        run.log_row(r)
        try:
            assert_changed_generations(r)
            ledger.ok()
            verdict = "OK"
        except NoOpArmError as e:
            ledger.fail("noop_arm", r["label"])
            verdict = "NO-OP ARM"
        print(f"  {r['label'][:34]:34s} differing={r['n_differing']}/{r['n_common']} "
              f"frac={r['frac_differing']}  {verdict}")

    out = {"schema": SCHEMA, "min_divergence": MIN_DIVERGENCE, "arms": rows,
           "VERDICT_NOTE": ("An arm passing this check has changed what the model wrote. An arm "
                            "FAILING it may still report `fired: true` truthfully -- that is "
                            "exactly the C-20 failure, where a hook wrote the value already "
                            "present and three claims cited the arm as a specificity control.")}
    p = os.path.join(run.path, "intervention_liveness.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    run.finish(summary={"n_arms": len(rows),
                        "n_noop": sum(1 for r in rows if r["is_noop_arm"])}, ledger=ledger)
    print(f"[ivlive] wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
