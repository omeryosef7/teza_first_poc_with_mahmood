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
import traceback
import glob
import json
import os
import sys
from typing import Dict, List, Optional, Sequence

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_DIR, FailureLedger, REPO_ROOT, RunDir, ds, read_jsonl, seed_everything  # noqa: E402
from extract_boombness import resolve_occurrences  # noqa: E402

DEFAULT_BANK = os.path.join(DATA_DIR, "boombness_prompt_bank.jsonl")
# TWO house folders hold refusal directions and they are NOT interchangeable:
#   doublespeak_causality/outputs/stage_gcg_full/  -> refusal_direction_llama_L{12..20}.pt   (4096-d)
#   outputs/stage_gcg_full/                        -> refusal_direction_qwen3_L{20,25,28}.pt (5120-d)
#                                                     refusal_direction_gemma4_L{25,31}.pt
# Searched in order; the first root holding a match for the model family wins.
_REFUSAL_DIRS = [
    os.path.join(REPO_ROOT, "doublespeak_causality", "outputs", "stage_gcg_full"),
    os.path.join(REPO_ROOT, "outputs", "stage_gcg_full"),
    os.path.join(REPO_ROOT, "doublespeak_causality", "outputs", "refusal_qwen3"),
]
_REFUSAL_DIR = _REFUSAL_DIRS[0]          # kept for the llama default below
REFUSAL_GLOB = os.path.join(_REFUSAL_DIR, "refusal_direction_llama_L*.pt")

# The house refusal directions are PER MODEL and live side by side in one folder:
#   refusal_direction_llama_L{12,14,16,18,20}.pt   (4096-d, Llama-3.1-8B)
#   refusal_direction_qwen3_L{20,25,28}.pt         (5120-d, Qwen3-14B)
#   refusal_direction_gemma4_L{25,31}.pt
# The glob above was HARDCODED to llama. Nothing checked the model, so a Qwen3 run would have loaded
# Llama's 4096-d vector into a 5120-d residual stream. Found 2026-08-18 while preparing the §14
# second-model arms, BEFORE any such job was submitted -- so no run is affected. `model_key` selects
# the family and `expect_dim` makes a mismatch a hard failure instead of a shape surprise.
_MODEL_KEYS = (("llama", "llama"), ("qwen", "qwen3"), ("gemma", "gemma4"))


def refusal_glob_for(model_id: Optional[str]) -> str:
    key = "llama"
    if model_id:
        low = model_id.lower()
        for needle, k in _MODEL_KEYS:
            if needle in low:
                key = k
                break
    for root in _REFUSAL_DIRS:
        cand = os.path.join(root, f"refusal_direction_{key}_L*.pt")
        if glob.glob(cand):
            return cand
    return os.path.join(_REFUSAL_DIR, f"refusal_direction_{key}_L*.pt")


def load_refusal_dirs(layers: Optional[Sequence[int]] = None, model_id: Optional[str] = None,
                      expect_dim: Optional[int] = None) -> Dict[int, torch.Tensor]:
    """Load the house refusal directions for THIS model, keyed by block layer."""
    # BUGFIX 2026-08-19 (follow-up sprint, found by SLURM 767265/767266 failing).
    # `refusal_glob_for` returns the glob for the FIRST root holding ANY file for this model
    # family, and never falls through. Root[0] (stage_gcg_full) holds llama L{12,14,16,18,20};
    # root[2] (refusal_qwen3 -- misnamed, it also holds llama) holds llama L{16,20,24,28,32}.
    # So a request for L24 or L28 resolved to root[0]'s pattern, matched no requested layer, and
    # died with "no refusal directions matched" even though the file exists one directory away.
    # That silently capped every refusalness layer profile at L20.
    # Fix: search ALL roots and union PER LAYER, first root wins for a layer it actually has.
    # Root order is preserved, so every previously-resolvable layer resolves to the same file and
    # no existing number changes.
    key = "llama"
    if model_id:
        low = model_id.lower()
        for needle, k in _MODEL_KEYS:
            if needle in low:
                key = k
                break
    patterns = [os.path.join(root, f"refusal_direction_{key}_L*.pt") for root in _REFUSAL_DIRS]
    pattern = " | ".join(patterns)          # for the error message only
    seen_paths = []
    for pat in patterns:
        for cand in sorted(glob.glob(pat)):
            seen_paths.append(cand)

    out: Dict[int, torch.Tensor] = {}
    resolved_from: Dict[int, str] = {}
    for p in seen_paths:
        base = os.path.basename(p)
        try:
            L = int(base.split("_L")[-1].split(".")[0])
        except ValueError:
            continue
        if layers is not None and L not in layers:
            continue
        if L in out:                         # first root wins for this layer
            continue
        v = torch.load(p, map_location="cpu", weights_only=True)
        if isinstance(v, dict):
            v = v.get("direction", next(iter(v.values())))
        out[L] = v.float().reshape(-1)
        resolved_from[L] = p
    if not out:
        raise SystemExit(
            f"no refusal directions matched {pattern} — available across "
            f"{_REFUSAL_DIRS}: "
            f"{sorted({os.path.basename(x) for r in _REFUSAL_DIRS for x in glob.glob(os.path.join(r, 'refusal_direction_*.pt'))})}")
    if layers is not None:
        missing = sorted(set(layers) - set(out))
        if missing:
            raise SystemExit(
                f"refusal directions requested for layers {sorted(layers)} but MISSING {missing}. "
                f"Found {sorted(out)} across {_REFUSAL_DIRS}. A layer profile must not silently "
                f"run on a subset of the layers it was asked for -- fit the missing direction "
                f"(doublespeak_causality/build_refusal_direction_llama.py) or drop it explicitly.")
    if expect_dim is not None:
        bad = {L: tuple(v.shape) for L, v in out.items() if v.numel() != expect_dim}
        if bad:
            raise SystemExit(
                f"refusal direction dimension mismatch for model {model_id!r}: expected {expect_dim}, "
                f"got {bad} from {pattern}. A direction fitted on a DIFFERENT model was about to be "
                f"projected out of this one.")
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
    ap.add_argument("--position", default="last", choices=["last", "codeword_last"],
                    help="token position to read refusalness at. FAIR-CONTEST FIX (audit A4/B2, "
                         "2026-08-17): the sprint compared refusalness against d_surface as "
                         "predictors of ASR, but refusalness was read at the LAST prompt token "
                         "while d_surface is read at `codeword_last`. Part of 'Boombness beats "
                         "refusalness 3.7x' was therefore 'the codeword position beats the last "
                         "position' — a footing mismatch, not a result. `codeword_last` puts both "
                         "predictors at the same token so the contest is decidable.")
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
    run.note_bank(args.bank)
    run.note_model(lm.model_id, revision=lm.revision, dtype=str(lm.dtype),
                   attn_implementation="sdpa",
                   refusal_direction_source=REFUSAL_GLOB,
                   refusal_layers=sorted(dirs),
                   note="refusalness is measured on the PROMPT before generation, so it is a "
                        "predictor and not a restatement of the observed refusal")

    units = {L: (v / v.norm()) for L, v in dirs.items()}
    first_error, n_failed = None, 0
    for i, row in enumerate(rows):
        try:
            if args.position == "codeword_last":
                templated, ids, last_idx, _foll, _nsub = resolve_occurrences(
                    dc, lm.tokenizer, row)
                if not last_idx:
                    ledger.fail("no_occurrence", row["prompt_id"])
                    continue
                pos = last_idx[-1]           # final occurrence, same as extract_boombness
            else:
                templated = dc.apply_template(lm.tokenizer, row["full_prompt"])
                ids = lm.tokenizer(templated, add_special_tokens=False)["input_ids"]
                pos = len(ids) - 1
            t = torch.tensor([ids], device=lm.model.device)
            out = lm.model(input_ids=t, output_hidden_states=True, use_cache=False)
        except Exception as e:
            ledger.fail(f"forward:{type(e).__name__}", row["prompt_id"])
            # FAIL FAST AND LOUDLY. A run where EVERY row fails previously logged nothing, wrote no
            # results.jsonl, and then died 30 lines later on a FileNotFoundError reading the file it
            # never wrote — three steps removed from the actual cause, with the reason discarded.
            # A systematically broken run must announce itself on the first row, not be inferred.
            if first_error is None:
                first_error = f"{type(e).__name__}: {e}"
                print(f"[refusal] FIRST FAILURE on row {i} ({row.get('prompt_id')}): "
                      f"{first_error}", flush=True)
                traceback.print_exc()
            n_failed += 1
            if n_failed >= 20 and ledger.succeeded == 0:
                raise SystemExit(
                    f"[refusal] ABORTING: the first {n_failed} rows ALL failed and none "
                    f"succeeded. This is a broken configuration, not a bad subset.\n"
                    f"  first error: {first_error}")
            continue
        rec = {k: row.get(k) for k in ("prompt_id", "prompt_sha16", "family_id", "condition",
                                        "cell", "domain", "split", "bank_block", "n_examples",
                                        "strength", "consistency", "example_position",
                                        "role_style", "query_kind")}
        rec["seq_len"] = len(ids)
        rec["readout_position"] = args.position
        rec["readout_token_index"] = int(pos)
        for L, u in units.items():
            h = out.hidden_states[L + 1][0, pos, :].float().cpu()
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
