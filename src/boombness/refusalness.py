"""refusalness.py — plan §9 Q6/Q7: does Boombness beat, or merely proxy for, refusal suppression?

THIS IS THE MEASUREMENT THAT DECIDES THE SPRINT'S OUTCOME LABEL (plan §18).
  outcome A  Boombness is the story.
  outcome C  refusal suppression is the story and Boombness is a correlate of it.

G2 established that the semantic readout predicts ASR within the doublespeak arm (ρ=+0.42) while
the representation Boombness does not (|ρ|≤0.10 at L4–L20). But the ASR table also showed refusal
collapsing from **95.8% on direct requests to 7.4% under doublespeak and 0.0% under a stated
mapping**. If refusalness carries the same information, the honest label is C, not A.

WHAT IS MEASURED
`refusalness = <h[final prompt token, layer L], unit(v_refusal[L])>`, using the HOUSE refusal
direction (`doublespeak_causality/outputs/stage_gcg_full/refusal_direction_llama_L{L}.pt`), which is
the same direction every previous refusal result in this repo was computed against — so the numbers
are comparable to prior work rather than to a private re-derivation.

Crucially this is a PREDICTOR measured on the prompt *before generation*, not the observed refusal
in the output. Using the observed refusal would be near-circular: refusal and ASR are close to
complementary by construction, so "refusal predicts ASR" would be a tautology rather than a finding.

The analysis then asks the three questions §9 actually poses:
  1. does refusalness predict ASR?
  2. does semantic Boombness predict ASR *controlling for* refusalness (partial correlation, and
     ΔR² over a refusalness-only model)?
  3. does refusalness explain the Boombness→ASR relationship (mediation)?
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import sys
from typing import Dict, List, Optional, Sequence

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_DIR, FailureLedger, REPO_ROOT, RunDir, ds, read_jsonl, seed_everything  # noqa: E402

DEFAULT_BANK = os.path.join(DATA_DIR, "boombness_prompt_bank.jsonl")
REFUSAL_GLOB = os.path.join(REPO_ROOT, "doublespeak_causality", "outputs", "stage_gcg_full",
                            "refusal_direction_llama_L*.pt")


def load_refusal_dirs(layers: Optional[Sequence[int]] = None) -> Dict[int, torch.Tensor]:
    """Load the house refusal directions, keyed by block layer."""
    out: Dict[int, torch.Tensor] = {}
    for p in sorted(glob.glob(REFUSAL_GLOB)):
        base = os.path.basename(p)
        try:
            L = int(base.split("_L")[-1].split(".")[0])
        except ValueError:
            continue
        if layers is not None and L not in layers:
            continue
        v = torch.load(p, map_location="cpu", weights_only=True)
        if isinstance(v, dict):
            v = v.get("direction", next(iter(v.values())))
        out[L] = v.float().reshape(-1)
    if not out:
        raise SystemExit(f"no refusal directions matched {REFUSAL_GLOB}")
    return out


@torch.no_grad()
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", default=DEFAULT_BANK)
    ap.add_argument("--model", default=None)
    ap.add_argument("--layers", default="12,14,16,18,20")
    ap.add_argument("--query-kind", default="behavioral",
                    help="behavioural rows are the ones with an ASR to join against")
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--seed", type=int, default=20260816)
    ap.add_argument("--tag", default="base")
    args = ap.parse_args()
    seed_everything(args.seed)

    dc = ds()
    rows = [r for r in read_jsonl(args.bank) if r["query_kind"] == args.query_kind]
    layers = [int(x) for x in args.layers.split(",")]
    dirs = load_refusal_dirs(layers)
    print(f"[refusal] {len(rows)} rows, refusal directions at layers {sorted(dirs)}")

    run = RunDir("refusalness", args, tag=args.tag)
    ledger = FailureLedger()
    lm = dc.load_model(args.model or dc.PRIMARY_MODEL, dtype=getattr(torch, args.dtype),
                       attn_implementation="sdpa")
    run.note_model(lm.model_id, revision=lm.revision, dtype=str(lm.dtype),
                   attn_implementation="sdpa",
                   refusal_direction_source=REFUSAL_GLOB,
                   refusal_layers=sorted(dirs),
                   note="refusalness is measured on the PROMPT before generation, so it is a "
                        "predictor and not a restatement of the observed refusal")

    units = {L: (v / v.norm()) for L, v in dirs.items()}
    for i, row in enumerate(rows):
        try:
            templated = dc.apply_template(lm.tokenizer, row["full_prompt"])
            ids = lm.tokenizer(templated, add_special_tokens=False)["input_ids"]
            t = torch.tensor([ids], device=lm.model.device)
            out = lm.model(input_ids=t, output_hidden_states=True, use_cache=False)
        except Exception as e:
            ledger.fail(f"forward:{type(e).__name__}", row["prompt_id"])
            continue
        rec = {k: row.get(k) for k in ("prompt_id", "prompt_sha16", "family_id", "condition",
                                        "cell", "domain", "split", "bank_block", "n_examples",
                                        "strength", "consistency", "example_position",
                                        "role_style", "query_kind")}
        rec["seq_len"] = len(ids)
        for L, u in units.items():
            h = out.hidden_states[L + 1][0, -1, :].float().cpu()   # final prompt token
            rec[f"refusalness|L{L}|cos"] = float(torch.dot(h / h.norm(), u))
            rec[f"refusalness|L{L}|proj"] = float(torch.dot(h, u))
        run.log_row(rec)
        ledger.ok()
        if (i + 1) % 100 == 0:
            print(f"[refusal] {i+1}/{len(rows)}")

    by_cond = collections.defaultdict(list)
    # summary uses the canonical L18 direction, the house default everywhere else in this repo
    for r in read_jsonl(run.p("results.jsonl")):
        if "refusalness|L18|proj" in r:
            by_cond[r["condition"]].append(r["refusalness|L18|proj"])
    summary = {"model": lm.model_id, "layers": sorted(dirs), "n_rows": len(rows),
               "refusal_direction_glob": REFUSAL_GLOB,
               "mean_refusalness_L18_proj_by_condition":
                   {k: sum(v) / len(v) for k, v in sorted(by_cond.items())}}
    run.finish(summary=summary, ledger=ledger)
    for k, v in summary["mean_refusalness_L18_proj_by_condition"].items():
        print(f"  {k:24s} mean refusalness(L18) = {v:+.4f}")
    print(f"[refusal] -> {run.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
