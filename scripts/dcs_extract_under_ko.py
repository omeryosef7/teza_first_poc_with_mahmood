"""dcs_extract_under_ko.py — the GATE-R5 CAPTURE BRIDGE (DCS `B-021` / `Q-005`, plan §53).

WHAT THIS IS, IN ONE SENTENCE
    It writes a `cache/final_occurrence_reps.pt` in EXACTLY the format the FROZEN `PR-035`
    analyzer (`scripts/dcs_bombness_specificity.py`) already consumes, but captured while a
    demonstration→query ATTENTION KNOCKOUT is LIVE. Nothing else. It fits no directions, computes
    no probe, and reports no accuracy: the frozen probe procedure is then applied UNCHANGED —
    train on BASELINE cell `B`, test on KNOCKED-OUT cell `C`.

WHY IT EXISTS (plan §53.1). `extract_boombness.py` persists multi-layer hidden states and has no
`--intervene`; `score_behavior.py` applies the knockout and persists only `hnorm|L*` NORMS, and a
norm cannot train a probe. The two capabilities have never met. §54.3 is the consequence: `R-086`
is a DECODABILITY result and gate `R5` — does `KO-3` destroy it? — is NOT RUN.

⛔ THIS FILE REIMPLEMENTS NOTHING. Every load-bearing piece is imported from the file that owns it:

  capture site + layer convention   extract_boombness.resolve_occurrences / forward_hidden
                                    (block L == hidden_states[L+1]; hidden_states[0] == embeddings)
  which KEYS are blocked            score_behavior.demo_key_positions + knockout_key_set("demo_all")
  which QUERY span is protected     score_behavior.query_span_positions
  the HOOK itself                   score_behavior.make_intervention -> pair_common
                                    .AllQueryAttentionKnockout, the class EVERY committed knockout
                                    artifact was produced with (score_behavior.py:1035-1037)
  the LIVENESS gate                 score_behavior.new_knockout_live / record_knockout_row /
                                    knockout_liveness_summary / assert_knockout_live
  the run contract                  common.RunDir (config/metadata/results/summary/DONE.json)

SCOPE IS `legacy_all_query`, HARD-CODED, AND THAT IS THE POINT. `AllQueryAttentionKnockout` blocks
attention onto the demonstration keys from EVERY query row. This capture is a SINGLE FORWARD PASS —
there is no decode step at all — so "every query row" is exactly "every prefill row", which is the
whole-query `KO-3` scope for a forward-only readout. Exposing `--knockout-scope` here would only
create the chance to file a run under a scope name whose decode half can never fire.

⛔ THE FAILURE THIS FILE IS MOST AFRAID OF is a mask that never fires. A silent no-op writes a cache
that looks perfect, is not knocked out at all, and would be read as "the knockout does not destroy
the signal" — the strongest possible wrong answer. The repo has been bitten by exactly this
(`C-047`; and `AttentionKnockout` vs `AllQueryAttentionKnockout`, pair_common.py:495-536). So:

  * `attn_implementation='eager'` is FORCED whenever the knockout is live, and re-checked on the
    loaded config. Under SDPA/flash a custom additive mask is discarded silently.
  * EVERY row is checked against an EXACT, CLOSED-FORM prediction of how many mask cells the key
    set implies (`expected_prefill_edit_rows` below), not merely against "> 0". A hook that fired
    on the wrong rows, on a truncated key set, or at a subset of the band, fails here.
  * the per-row verdict is `score_behavior.record_knockout_row(..., readout=True)` — the SAME
    accumulator the committed forward-only readout runs use — and the run-level verdict is
    `assert_knockout_live`, called BEFORE `finish()`. A run that cannot prove liveness aborts and
    writes ABORTED.json, so no analyzer will ever read it (they require DONE.json).

⛔ ROWS WITH NO DEMONSTRATION BLOCK (`n_examples == 0`) CANNOT BE KNOCKED OUT and are LEDGERED AND
SKIPPED, never captured un-hooked. Mixing hooked and un-hooked vectors into one cache under one
run name is the same silent-no-op failure wearing a different hat. The consequence is declared:
the `C_n0` blocking-null cell is EMPTY in a knocked-out run, by construction and on purpose.

Responsible handling: no generation, no prompt text in results.jsonl beyond the single decoded
token at the capture position (which is the provenance answer to "which token did you read?").
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from typing import Dict, List, Optional, Sequence

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
_BOOMB = os.path.join(_REPO, "src", "boombness")
if _BOOMB not in sys.path:
    sys.path.insert(0, _BOOMB)          # importing `common` also bootstraps doublespeak_causality/

import torch                                                                  # noqa: E402

from common import DATA_DIR, FailureLedger, RunDir, ds, pair, read_jsonl, seed_everything  # noqa: E402
import signals as sg                                                          # noqa: E402
from ds_common import parse_enable_thinking as dc_parse_thinking              # noqa: E402
import extract_boombness as eb                                                # noqa: E402
import score_behavior as sb                                                   # noqa: E402

DEFAULT_BANK = os.path.join(DATA_DIR, "boombness_prompt_bank.jsonl")

#: `PR-035` band. Kept as a default, never as an assumption: it is echoed and bounds-checked
#: against the loaded model's depth (score_behavior.py:1700 records why — a band copied from a
#: model of a different depth is the silent-weaker-knockout bug, and no exception can catch it).
DEFAULT_BAND = "6-14"

#: The ONLY scope this file runs. See the module docstring.
KNOCKOUT_SCOPE = sb.DEFAULT_KNOCKOUT_SCOPE          # == "legacy_all_query"


# --------------------------------------------------------------------------- #
# Two pure functions, so the self-test can drive the REAL ones
# --------------------------------------------------------------------------- #
def pick_layer_rows(hs: torch.Tensor, layers: Sequence[int], pos: int) -> torch.Tensor:
    """`[len(layers), H]` at token `pos`, under the house layer convention.

    THE OFF-BY-ONE IS THE WHOLE FUNCTION. `hs[0]` is the EMBEDDING; block `L` is `hs[L+1]`
    (extract_boombness.py:21, sg.LAYER_CONVENTION). Get it wrong and every layer of the cache is
    shifted by one while every shape, every norm and every downstream accuracy stays plausible.
    Written as one testable function rather than inline, so `--self-test` can prove the shift on a
    tensor whose contents encode their own index.

    Byte-for-byte the expression extract_boombness.stage_score caches with (`hs[L + 1, pos, :]`),
    stacked in the same order and halved the same way — that identity is what makes the frozen
    analyzer able to consume this file's output without knowing it exists.
    """
    return torch.stack([hs[L + 1, pos, :] for L in layers], dim=0)


def expected_prefill_edit_rows(blocked_keys: Sequence[int], seq_len: int) -> int:
    """How many (query row, key) cells `AllQueryAttentionKnockout` MUST edit on ONE prefill pass.

    Derived from the hook's own index algebra (pair_common.py:562-574), not guessed:

        past = kv_len - n_q = 0 at prefill, so n_q == kv_len == seq_len;
        for each blocked key kp < kv_len the first causally-legal query row is lo = max(0, kp),
        and every row from lo onward is blocked  ->  (seq_len - kp) rows.

    The hook multiplies that by the mask's head dimension and accumulates over the band, so the
    observed counter is `len(band) * head_mult * this`. `head_mult` is INFERRED from the first row
    (it is 1 for a broadcast [1,1,q,k] eager mask and n_heads for an expanded one) and then held
    FIXED and asserted on every later row — inferring it per row would make the check unfalsifiable.

    THIS IS THE DIFFERENCE BETWEEN A LIVENESS CHECK AND A LIVENESS GATE. `n_edits > 0` passes for a
    hook that fired on one layer, on one key, on one row. This does not.
    """
    n = int(seq_len)
    return int(sum(n - int(kp) for kp in blocked_keys if 0 <= int(kp) < n))


def assert_row_edits(stats: Dict, *, n_band_layers: int, expected_rows: int, head_mult: Optional[int],
                     prompt_id: str) -> int:
    """Check ONE row's hook counters against the closed form; return the head multiplier.

    Raises RuntimeError (not SystemExit) so the caller decides whether one bad row aborts the run
    or is charged to the ledger — SystemExit is a BaseException and would sail past a per-row
    `except Exception`, which is the failure mode `knockout_key_set`'s own comment records.
    """
    ks = sb.knockout_row_stats(stats)
    pf = int(ks.get("n_prefill_forward", 0))
    df = int(ks.get("n_decode_forward", 0))
    pe = int(ks.get("n_prefill_edits", 0))
    de = int(ks.get("n_decode_edits", 0))
    if pf != n_band_layers:
        raise RuntimeError(f"{prompt_id}: hook entered at prefill {pf} times, expected exactly "
                           f"{n_band_layers} (one per band layer, one forward). A band layer whose "
                           f"hook never fired is a partial knockout reported as a whole one.")
    if df or de:
        raise RuntimeError(f"{prompt_id}: this is a SINGLE-FORWARD capture, but the hook recorded "
                           f"n_decode_forward={df} n_decode_edits={de}. Something generated.")
    if expected_rows <= 0:
        raise RuntimeError(f"{prompt_id}: the key set implies ZERO editable mask cells; a no-op "
                           f"knockout must never be captured.")
    if pe <= 0:
        raise RuntimeError(f"{prompt_id}: THE MASK NEVER FIRED (n_prefill_edits=0) while "
                           f"{expected_rows} cells x {n_band_layers} layers were implied by the "
                           f"key set. This is the silent no-op (C-047); refusing.")
    denom = n_band_layers * expected_rows
    if pe % denom:
        raise RuntimeError(f"{prompt_id}: n_prefill_edits={pe} is not a whole multiple of "
                           f"{n_band_layers} layers x {expected_rows} implied cells; the hook did "
                           f"not edit the rows the key set implies.")
    got = pe // denom
    if head_mult is not None and got != head_mult:
        raise RuntimeError(f"{prompt_id}: mask head multiplier changed mid-run ({got} vs "
                           f"{head_mult}); the mask shape is not stable and the counter no longer "
                           f"means what row 0 established it means.")
    return got


# --------------------------------------------------------------------------- #
# The capture
# --------------------------------------------------------------------------- #
def select_rows(rows: List[Dict], smoke: int, limit: int, knockout: bool) -> List[Dict]:
    """The prompt set this process will attempt, in BANK ORDER.

    `--smoke N` picks rows that CAN carry the knockout (non-empty `demo_block`) — and it does so
    WHETHER OR NOT the knockout is live, deliberately. Two reasons, and the second is the one that
    matters: a pre-flight over N rows that all skip is a pre-flight of nothing; and the smoke's
    other job is the THREE-WAY comparison (committed baseline / local `--no-knockout` / local
    knocked-out), which is only a comparison if all three ran the SAME prompts. A `--no-knockout`
    smoke over a different row set would answer "does it reproduce" and "did it change" about two
    different populations, which is not an answer.

    `knockout` is still taken, and still selects the fallback: with no demo-block rows in range
    (e.g. a bank slice that is all `n_examples == 0`) a knocked-out run must select nothing and say
    so, while a baseline run may legitimately proceed on what is there.
    """
    out = list(rows)
    if limit:
        out = out[:limit]
    if smoke:
        pool = [r for r in out if (r.get("demo_block") or "")]
        if not pool and not knockout:
            pool = out
        out = pool[:smoke]
    return out


def capture(lm, dc, pc, rows, layers, band, run, ledger, args) -> Dict:
    tok = lm.tokenizer
    knockout = not args.no_knockout
    spec = ({"direction": args.arm, "mode": "attn_knockout", "layers": list(band), "alpha": 1.0}
            if knockout else None)
    knock_live = sb.new_knockout_live() if knockout else None
    cache: Dict[str, torch.Tensor] = {}
    head_mult: Optional[int] = None
    n_ok = 0
    n_keys_hist: List[int] = []
    skip_reasons: Dict[str, int] = collections.defaultdict(int)
    diag = {}

    for row in rows:
        pid = row["prompt_id"]
        try:
            templated, ids, last, following, n_sub = eb.resolve_occurrences(
                dc, tok, row, enable_thinking=args._enable_thinking)
        except ValueError as e:
            ledger.fail(f"resolve:{e}", pid)
            skip_reasons[f"resolve:{e}".split(":")[1]] += 1
            continue
        if args.position != "last" and not last:
            ledger.fail(f"capture:no_occurrence_at_position:{args.position}", pid)
            skip_reasons["no_occurrence_at_position"] += 1
            continue

        dk: List[int] = []
        prot = None
        keys: List[int] = []
        stats = None
        exp_rows = 0
        if knockout:
            dk, why = sb.demo_key_positions(tok, row, templated)
            if why:
                # `no_demo_block` is the n_examples == 0 rows. DECLARED, LEDGERED, SKIPPED — see
                # the module docstring. Capturing them un-hooked would put un-knocked-out vectors
                # into a cache whose name says every vector in it is knocked out.
                ledger.fail(f"demokeys:{why}", pid)
                skip_reasons[why] += 1
                if args.on_no_demo_block == "fail":
                    raise SystemExit(f"REFUSING: {pid} has no usable demonstration block ({why}) "
                                     f"and --on-no-demo-block=fail")
                continue
            prot = sb.query_span_positions(tok, row, templated, dk)
            keys = sb.knockout_key_set(args.arm, dk, len(ids), args.seed, protected=prot)
            if not keys:
                ledger.fail("keys:empty_key_set", pid)
                skip_reasons["empty_key_set"] += 1
                continue
            exp_rows = expected_prefill_edit_rows(keys, len(ids))
            stats = {}

        try:
            if knockout:
                ctxs = sb.make_intervention(dc, pc, lm, spec, None, control_seed=args.seed,
                                            demo_keys=dk, seq_len=len(ids), knock_stats=stats,
                                            protected=prot, knock_heads=None,
                                            knock_scope=KNOCKOUT_SCOPE)
                if not ctxs:
                    raise RuntimeError("make_intervention produced NO hooks for an attn_knockout "
                                       "spec; the forward would be an un-knocked-out baseline "
                                       "captured under a knockout run name.")
                import contextlib
                with contextlib.ExitStack() as st:
                    for c in ctxs:
                        st.enter_context(c)
                    hs = eb.forward_hidden(lm, ids, _diag=diag)
                head_mult = assert_row_edits(stats, n_band_layers=len(band),
                                             expected_rows=exp_rows, head_mult=head_mult,
                                             prompt_id=pid)
                ks, bad = sb.record_knockout_row(knock_live, KNOCKOUT_SCOPE, stats,
                                                 n_demo_positions=len(dk), readout=True)
                if bad:
                    raise RuntimeError(f"{pid}: liveness contract violated: {bad}")
            else:
                hs = eb.forward_hidden(lm, ids, _diag=diag)
                ks = {}
        except RuntimeError as e:
            # A liveness failure is NOT a row to skip past. One row whose mask did not fire means
            # the wiring is wrong for every row, and a shrunken-but-clean cache is precisely the
            # artifact that gets read as a result. Abort the whole run.
            run.abort(f"knockout_liveness_row_failure: {e}", ledger=ledger)
            raise SystemExit(f"REFUSING (run aborted, no DONE.json): {e}")

        pos = (len(ids) - 1) if args.position == "last" else last[-1]
        # The SAME self-check extract_boombness makes on every row (the phantom-cell guard).
        if args.position == "codeword_last" and pos not in last:
            raise SystemExit(f"{pid}: capture index {pos} is not a codeword occurrence")
        if args.position == "last" and pos != len(ids) - 1:
            raise SystemExit(f"{pid}: capture index {pos} != seq_len-1")

        vec = pick_layer_rows(hs, layers, pos)
        cache[pid] = vec.half()

        rec: Dict[str, object] = {
            "prompt_id": pid, "prompt_sha16": row.get("prompt_sha16"),
            "family_id": row.get("family_id"), "cell": row.get("cell"),
            "domain": row.get("domain"), "split": row.get("split"),
            "condition": row.get("condition"), "bank_block": row.get("bank_block"),
            "query_kind": row.get("query_kind"), "n_examples": row.get("n_examples"),
            "strength": row.get("strength"), "consistency": row.get("consistency"),
            "target_surface": row.get("target_surface"),
            # ---- capture provenance: WHERE was this vector read from? ----------------------- #
            "position": args.position, "token_pos": int(pos), "seq_len": len(ids),
            "token_text": tok.decode([ids[pos]]),
            "n_occurrences": len(last), "n_subtokens": (n_sub[-1] if n_sub else None),
            "layer_convention": sg.LAYER_CONVENTION, "layers": list(layers),
            # ---- knockout provenance: WHAT was blocked, and did it fire? -------------------- #
            "ko_applied": bool(knockout), "arm": (args.arm if knockout else None),
            "knockout_scope": (KNOCKOUT_SCOPE if knockout else None),
            "band": (list(band) if knockout else None),
            "band_str": (args.band if knockout else None),
            "seed": int(args.seed),
            "n_demo_keys": len(dk), "n_blocked_keys": len(keys),
            "demo_key_min": (min(dk) if dk else None), "demo_key_max": (max(dk) if dk else None),
            "blocked_key_min": (min(keys) if keys else None),
            "blocked_key_max": (max(keys) if keys else None),
            "n_query_span_positions": (len(prot) if prot else 0),
            "expected_prefill_edit_rows": int(exp_rows),
            "mask_head_mult": (int(head_mult) if head_mult else None),
            "hook_n_forward": int(ks.get("n_forward", 0)) if ks else 0,
            "hook_n_prefill_forward": int(ks.get("n_prefill_forward", 0)) if ks else 0,
            "hook_n_decode_forward": int(ks.get("n_decode_forward", 0)) if ks else 0,
            "hook_n_edits": int(ks.get("n_edits", 0)) if ks else 0,
            "hook_n_prefill_edits": int(ks.get("n_prefill_edits", 0)) if ks else 0,
            "hook_n_decode_edits": int(ks.get("n_decode_edits", 0)) if ks else 0,
            "hook_liveness_readout_only": bool(knockout),
            "bank_file_sha16": args._bank_file_sha16,
        }
        # `hnorm|L*`, the SAME column name extract_boombness writes. `dcs_verify_pr035_primary`'s
        # V6 binds a rep cache to its own run by comparing ||rep|| against these, so writing them
        # is what lets an independent verifier prove this cache is not another bank's.
        for j, L in enumerate(layers):
            rec[f"hnorm|L{L}"] = float(vec[j].float().norm())
        run.log_row(rec)
        n_keys_hist.append(len(keys))
        ledger.ok()
        n_ok += 1
        if n_ok % 100 == 0:
            print(f"[ko-extract] {n_ok}/{len(rows)} captured", flush=True)

    if cache:
        os.makedirs(run.cache, exist_ok=True)
        # ⛔ BYTE-FOR-BYTE THE EXTRACTOR'S PAYLOAD (extract_boombness.py:729). Any extra key is
        # fine; a missing or renamed one silently breaks `load_reps` in the FROZEN analyzer, which
        # this file is not allowed to edit.
        torch.save({"layers": list(layers), "layer_convention": sg.LAYER_CONVENTION,
                    "position": args.position, "dtype": "float16", "reps": cache},
                   os.path.join(run.cache, "final_occurrence_reps.pt"))
        print(f"[ko-extract] cached {len(cache)} rep stacks -> {run.cache}/"
              f"final_occurrence_reps.pt")

    out: Dict[str, object] = {
        "n_rows_attempted": len(rows), "n_rows_captured": n_ok, "n_cached": len(cache),
        "skip_reasons": dict(skip_reasons),
        "knockout_applied": bool(knockout),
        "arm": (args.arm if knockout else None),
        "knockout_scope": (KNOCKOUT_SCOPE if knockout else None),
        "band": (list(band) if knockout else None),
        "mask_head_mult": head_mult,
        "median_n_blocked_keys": (sorted(n_keys_hist)[len(n_keys_hist) // 2] if n_keys_hist else 0),
        "layer_convention": sg.LAYER_CONVENTION,
        "last_layer_tied_vs_raw_relnorm": diag.get("last_layer_tied_vs_raw_relnorm"),
    }
    if knockout:
        # THE RUN-LEVEL GATE. `assert_knockout_live` raises SystemExit unless the mask demonstrably
        # fired where THIS scope says it must, on >= 99% of rows, and n_rows == 0 is a FAILURE.
        ksum = sb.knockout_liveness_summary(knock_live, "eager", scope=KNOCKOUT_SCOPE, readout=True)
        out["knockout_liveness"] = ksum
        sb.assert_knockout_live(ksum)
        print(f"[ko-extract] LIVENESS OK: {ksum['n_rows']} rows, "
              f"frac_rows_scope_live={ksum['frac_rows_scope_live']}, "
              f"total_prefill_edits={ksum['total_prefill_edits']}, "
              f"median_prefill_edits={ksum['median_prefill_edits']}, "
              f"total_decode_edits={ksum['total_decode_edits']}")
    return out


# --------------------------------------------------------------------------- #
# The two mandated sanity comparisons, computed in-process and persisted
# --------------------------------------------------------------------------- #
def compare_to_cache(run_cache_path: str, ref_run_dir: str) -> Dict:
    """||rep|| and full-vector agreement against a reference run's cache, per (prompt, layer).

    Two questions, one function:
      * with the knockout DISABLED, does this capture REPRODUCE the committed baseline? If it does
        not, the capture site or the layer convention is wrong and nothing downstream is readable.
      * with the knockout ENABLED, how many (prompt, layer) pairs actually CHANGED, and by how
        much? "It ran" is not evidence that it did anything.
    """
    ref_p = os.path.join(ref_run_dir, "cache", "final_occurrence_reps.pt")
    if not os.path.exists(ref_p):
        return {"error": f"no reference cache at {ref_p}"}
    a = torch.load(run_cache_path, map_location="cpu")
    b = torch.load(ref_p, map_location="cpu")
    if list(a["layers"]) != list(b["layers"]):
        return {"error": f"layer sets differ: {a['layers']} vs {b['layers']}"}
    if a.get("position") != b.get("position"):
        return {"error": f"positions differ: {a.get('position')} vs {b.get('position')}"}
    shared = sorted(set(a["reps"]) & set(b["reps"]))
    if not shared:
        return {"error": "no shared prompt_ids"}
    nl = len(a["layers"])
    import numpy as np

    def _agree(shift: int):
        """||rep||, vector and cosine agreement with the reference read `shift` layers over."""
        rn, rv, cs, changed, changed_big = [], [], [], 0, 0
        for pid in shared:
            x, y = a["reps"][pid].float(), b["reps"][pid].float()
            for j in range(nl):
                k = j + shift
                if not (0 <= k < nl):
                    continue
                ny = float(y[k].norm())
                rn.append(abs(float(x[j].norm()) - ny) / max(1e-9, ny))
                d = float((x[j] - y[k]).norm()) / max(1e-9, ny)
                rv.append(d)
                cs.append(float(torch.nn.functional.cosine_similarity(x[j], y[k], dim=0)))
                changed += int(d > 1e-3)
                changed_big += int(d > 1e-1)
        rn, rv, cs = np.array(rn), np.array(rv), np.array(cs)
        return {
            "n_pairs": int(rn.size),
            # TWO THRESHOLDS, BECAUSE ONE IS NOT ENOUGH. bf16 on two different GPU architectures
            # already disagrees by ~1.4% per element, so `> 1e-3` reads 1.0 even for a PERFECT
            # reproduction and can only ever be evidence of arithmetic, not of an intervention.
            # `> 1e-1` is the one that separates "the knockout changed the state" from "the kernels
            # rounded differently". Quote the cosine and the magnitudes, never the 1e-3 fraction.
            "frac_pairs_changed_gt_1e-1": float(changed_big) / float(rn.size),
            "relnorm_of_norm_max": float(rn.max()), "relnorm_of_norm_median": float(np.median(rn)),
            "relnorm_of_norm_q95": float(np.quantile(rn, 0.95)),
            "relnorm_of_vector_max": float(rv.max()), "relnorm_of_vector_median": float(np.median(rv)),
            "relnorm_of_vector_q95": float(np.quantile(rv, 0.95)),
            "cos_min": float(cs.min()), "cos_median": float(np.median(cs)),
            "cos_max": float(cs.max()),
            "frac_pairs_changed_gt_1e-3": float(changed) / float(rn.size),
        }

    out = {
        "reference_run": ref_run_dir,
        "n_shared_prompts": len(shared),
        "n_prompts_only_here": len(set(a["reps"]) - set(b["reps"])),
        "n_prompts_only_reference": len(set(b["reps"]) - set(a["reps"])),
    }
    out.update(_agree(0))
    # ⛔ THE OFF-BY-ONE CONTROL, AND IT IS THE POINT OF THIS FUNCTION. "max relative error 0.003"
    # is only evidence that the capture site is right if a WRONG capture site would have produced a
    # visibly worse number. Reading the reference one block over is the exact mistake the layer
    # convention exists to prevent (block L == hidden_states[L+1]), so it is measured rather than
    # argued: agreement at shift 0 must beat shift +/-1 by a wide margin, or the match at shift 0
    # is not informative about the convention at all.
    out["offbyone_control"] = {"shift_plus1": _agree(1), "shift_minus1": _agree(-1)}
    out["offbyone_verdict"] = (
        "PASS: shift 0 agrees far better than shift +/-1"
        if out["cos_median"] > max(out["offbyone_control"]["shift_plus1"]["cos_median"],
                                   out["offbyone_control"]["shift_minus1"]["cos_median"]) + 0.01
        else "INCONCLUSIVE: shift 0 is not clearly better than a one-block shift; this comparison "
             "cannot certify the layer convention")
    return out


# --------------------------------------------------------------------------- #
# --self-test: no GPU, no bank, no model
# --------------------------------------------------------------------------- #
def self_test() -> int:
    """Drive the REAL functions this file's correctness rests on, on CPU, with no bank.

    Each check is written so that BREAKING the thing it guards makes it fail — the repo's standing
    complaint about its own guards (a threshold mutated to `< 0.0` once left 44 tests green).
    """
    import types
    ok, fail = [], []

    def check(name, cond, detail=""):
        (ok if cond else fail).append(f"{name}{(' — ' + detail) if detail else ''}")

    # ---- T1  the layer convention, on a tensor that encodes its own index ------------------- #
    n_blocks, seq, H = 6, 4, 3
    hs = torch.stack([torch.full((seq, H), float(i)) for i in range(n_blocks + 1)], dim=0)
    got = pick_layer_rows(hs, [0, 2, 5], pos=1)
    check("T1 layer convention block L == hidden_states[L+1]",
          got.shape == (3, H) and [float(g[0]) for g in got] == [1.0, 3.0, 6.0],
          f"got {[float(g[0]) for g in got]}, want [1.0, 3.0, 6.0]")
    check("T1b convention string matches signals.LAYER_CONVENTION",
          "L+1" in sg.LAYER_CONVENTION or "hidden_states[L+1]" in sg.LAYER_CONVENTION,
          sg.LAYER_CONVENTION)

    # ---- T2  the key set is the demo block, deduplicated and sorted ------------------------- #
    keys = sb.knockout_key_set("demo_all", [9, 3, 5, 3], 20, 1234, protected={11, 12})
    check("T2 knockout_key_set('demo_all') == sorted(set(demo_keys))", keys == [3, 5, 9], str(keys))

    # ---- T3  the closed form vs the ACTUAL hook, on a synthetic 4-D mask -------------------- #
    pc = pair()
    stub_layers = [types.SimpleNamespace() for _ in range(4)]
    stub = types.SimpleNamespace(model=types.SimpleNamespace(layers=stub_layers),
                                 config=types.SimpleNamespace(num_attention_heads=8))
    S, blocked = 10, [2, 3, 7]
    stats: Dict[str, int] = {}
    hook = pc.AllQueryAttentionKnockout(stub, [0, 1], blocked_keys=blocked, heads=None, stats=stats)
    am = torch.zeros(1, 1, S, S)
    _, kw = hook._pre(None, (), {"attention_mask": am})
    # `AllQueryAttentionKnockout` writes no `n_prefill_edits`; score_behavior.knockout_row_stats
    # DERIVES it from `n_edits - n_decode_edits`, and that derivation is the one the gate reads.
    ks3 = sb.knockout_row_stats(stats)
    pred = expected_prefill_edit_rows(blocked, S)
    check("T3 expected_prefill_edit_rows matches the hook's own counter",
          ks3["n_prefill_edits"] == pred and pred == (10 - 2) + (10 - 3) + (10 - 7),
          f"hook={ks3['n_prefill_edits']} predicted={pred}")
    edited = kw["attention_mask"]
    mv = torch.finfo(am.dtype).min
    check("T3b the mask really was written (blocked cells are -inf, causal cells only)",
          bool((edited[0, 0, 2:, 2] == mv).all()) and bool(edited[0, 0, 0, 2] == 0.0) and
          bool((edited[0, 0, :, 4] == 0.0).all()),
          "blocked column not masked from its first causal row onward")

    # ---- T4  assert_row_edits FIRES on a dead hook, a partial band, and a wrong count -------- #
    dead = {"n_forward": 2, "n_prefill_forward": 2, "n_decode_forward": 0,
            "n_edits": 0, "n_decode_edits": 0}
    try:
        assert_row_edits(dead, n_band_layers=2, expected_rows=pred, head_mult=None, prompt_id="x")
        check("T4 dead mask is refused", False, "assert_row_edits ACCEPTED n_prefill_edits == 0")
    except RuntimeError as e:
        check("T4 dead mask is refused", "MASK NEVER FIRED" in str(e))
    partial = {"n_forward": 1, "n_prefill_forward": 1, "n_decode_forward": 0,
               "n_edits": pred, "n_decode_edits": 0}
    try:
        assert_row_edits(partial, n_band_layers=2, expected_rows=pred, head_mult=None, prompt_id="x")
        check("T4b a band layer whose hook never fired is refused", False, "accepted 1 of 2 layers")
    except RuntimeError as e:
        check("T4b a band layer whose hook never fired is refused", "band layer" in str(e))
    wrong = {"n_forward": 2, "n_prefill_forward": 2, "n_decode_forward": 0,
             "n_edits": 2 * pred - 1, "n_decode_edits": 0}
    try:
        assert_row_edits(wrong, n_band_layers=2, expected_rows=pred, head_mult=None, prompt_id="x")
        check("T4c an edit count the key set does not imply is refused", False, "accepted")
    except RuntimeError as e:
        check("T4c an edit count the key set does not imply is refused", "whole multiple" in str(e))
    good = {"n_forward": 2, "n_prefill_forward": 2, "n_decode_forward": 0,
            "n_edits": 2 * pred, "n_decode_edits": 0}
    check("T4d a correct row passes and reports head_mult == 1",
          assert_row_edits(good, n_band_layers=2, expected_rows=pred, head_mult=None,
                           prompt_id="x") == 1)
    decoded = {"n_forward": 3, "n_prefill_forward": 2, "n_decode_forward": 1,
               "n_edits": 2 * pred + 5, "n_decode_edits": 5}
    try:
        assert_row_edits(decoded, n_band_layers=2, expected_rows=pred, head_mult=1, prompt_id="x")
        check("T4e a decode step in a forward-only capture is refused", False, "accepted")
    except RuntimeError as e:
        check("T4e a decode step in a forward-only capture is refused", "SINGLE-FORWARD" in str(e))

    # ---- T5  the run-level gate: score_behavior's own accumulator and assertion -------------- #
    live = sb.new_knockout_live()
    for _ in range(4):
        sb.record_knockout_row(live, KNOCKOUT_SCOPE,
                               {"n_forward": 2, "n_prefill_forward": 2, "n_decode_forward": 0,
                                "n_edits": 2 * pred, "n_decode_edits": 0},
                               n_demo_positions=3, readout=True)
    s_ok = sb.knockout_liveness_summary(live, "eager", scope=KNOCKOUT_SCOPE, readout=True)
    check("T5 a live forward-only run passes assert_knockout_live",
          sb.assert_knockout_live(s_ok) is True and s_ok["frac_rows_scope_live"] == 1.0,
          json.dumps({k: s_ok[k] for k in ("n_rows", "frac_rows_scope_live", "total_prefill_edits")}))
    dead_live = sb.new_knockout_live()
    for _ in range(4):
        sb.record_knockout_row(dead_live, KNOCKOUT_SCOPE,
                               {"n_forward": 2, "n_prefill_forward": 2, "n_decode_forward": 0,
                                "n_edits": 0, "n_decode_edits": 0},
                               n_demo_positions=3, readout=True)
    s_dead = sb.knockout_liveness_summary(dead_live, "eager", scope=KNOCKOUT_SCOPE, readout=True)
    try:
        sb.assert_knockout_live(s_dead)
        check("T5b a run whose mask never fired is REFUSED", False, "assert_knockout_live passed")
    except SystemExit:
        check("T5b a run whose mask never fired is REFUSED", True)
    empty = sb.knockout_liveness_summary(sb.new_knockout_live(), "eager",
                                         scope=KNOCKOUT_SCOPE, readout=True)
    try:
        sb.assert_knockout_live(empty)
        check("T5c a run with zero rows is REFUSED", False, "zero rows passed")
    except SystemExit:
        check("T5c a run with zero rows is REFUSED", True)

    # ---- T6  the cache payload has exactly the keys the FROZEN analyzer reads ---------------- #
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "final_occurrence_reps.pt")
        torch.save({"layers": [6, 7], "layer_convention": sg.LAYER_CONVENTION,
                    "position": "codeword_last", "dtype": "float16",
                    "reps": {"a": torch.zeros(2, 4).half()}}, p)
        blob = torch.load(p, map_location="cpu")
        check("T6 cache payload keys match extract_boombness.py:729",
              set(blob) == {"layers", "layer_convention", "position", "dtype", "reps"},
              str(sorted(blob)))
        q = os.path.join(td, "ref")
        os.makedirs(os.path.join(q, "cache"))
        torch.save({"layers": [6, 7], "layer_convention": sg.LAYER_CONVENTION,
                    "position": "codeword_last", "dtype": "float16",
                    "reps": {"a": torch.zeros(2, 4).half(), "b": torch.ones(2, 4).half()}},
                   os.path.join(q, "cache", "final_occurrence_reps.pt"))
        cmp_ = compare_to_cache(p, q)
        check("T6b compare_to_cache reports identical states as identical",
              cmp_["relnorm_of_vector_max"] == 0.0 and cmp_["frac_pairs_changed_gt_1e-3"] == 0.0
              and cmp_["n_prompts_only_reference"] == 1, json.dumps(cmp_))
        # T6c: the off-by-one control must FIRE on a cache that really is shifted by one block.
        r2 = os.path.join(td, "ref2")
        os.makedirs(os.path.join(r2, "cache"))
        base = torch.stack([torch.randn(8) * (i + 1) for i in range(3)])
        torch.save({"layers": [6, 7, 8], "layer_convention": sg.LAYER_CONVENTION,
                    "position": "codeword_last", "dtype": "float16",
                    "reps": {"a": base.half()}}, os.path.join(r2, "cache",
                                                              "final_occurrence_reps.pt"))
        shifted = os.path.join(td, "shifted.pt")
        torch.save({"layers": [6, 7, 8], "layer_convention": sg.LAYER_CONVENTION,
                    "position": "codeword_last", "dtype": "float16",
                    "reps": {"a": torch.stack([base[1], base[2], base[0]]).half()}}, shifted)
        good = compare_to_cache(os.path.join(r2, "cache", "final_occurrence_reps.pt"), r2)
        bad_ = compare_to_cache(shifted, r2)
        check("T6c the off-by-one control PASSES on an aligned cache",
              good["offbyone_verdict"].startswith("PASS"), good["offbyone_verdict"])
        check("T6d the off-by-one control REFUSES a cache shifted by one block",
              bad_["offbyone_verdict"].startswith("INCONCLUSIVE"), bad_["offbyone_verdict"])

    # ---- T7  row selection ------------------------------------------------------------------ #
    rws = [{"prompt_id": f"p{i}", "demo_block": ("" if i % 2 else "D")} for i in range(10)]
    sel = select_rows(rws, smoke=3, limit=0, knockout=True)
    check("T7 --smoke picks rows that CAN carry the knockout",
          [r["prompt_id"] for r in sel] == ["p0", "p2", "p4"], str([r["prompt_id"] for r in sel]))
    check("T7b --smoke picks the SAME rows with and without the knockout (comparability)",
          [r["prompt_id"] for r in select_rows(rws, 3, 0, False)] == ["p0", "p2", "p4"],
          str([r["prompt_id"] for r in select_rows(rws, 3, 0, False)]))
    nodemo = [{"prompt_id": f"q{i}", "demo_block": ""} for i in range(4)]
    check("T7c a knocked-out smoke over demo-less rows selects NOTHING (and main() refuses)",
          select_rows(nodemo, 2, 0, True) == [] and len(select_rows(nodemo, 2, 0, False)) == 2)

    print("\n".join(f"  PASS  {t}" for t in ok))
    if fail:
        print("\n".join(f"  FAIL  {t}" for t in fail))
        print(f"SELF-TEST FAILED: {len(fail)} of {len(ok) + len(fail)}")
        return 1
    print(f"SELF-TEST PASSED: {len(ok)}/{len(ok)} checks")
    return 0


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true",
                    help="run every CPU-checkable guard in this file; no GPU, no bank, no model")
    # --- mirrors extract_boombness where they overlap ------------------------------------- #
    ap.add_argument("--bank", default=DEFAULT_BANK)
    ap.add_argument("--layers", default="6,7,8,9,10,11,12,13,14",
                    help="'all' or a comma list of BLOCK indices (PR-035 used 6..14)")
    ap.add_argument("--position", default="codeword_last", choices=["codeword_last", "last"])
    ap.add_argument("--model", default=None, help="default = ds_common.PRIMARY_MODEL")
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--seed", type=int, default=20260905)
    ap.add_argument("--tag", default="bombspecko",
                    help="run-dir tag. Keep it DISTINCT from `bombspec`: the frozen analyzer and "
                         "the verifier resolve baseline runs by globbing `bombspec_<cw>_<cc>_*`, "
                         "and a knocked-out run answering that glob would silently replace the "
                         "baseline it is meant to be compared against.")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--enable-thinking", default=None, choices=[None, "true", "false"])
    # --- this file's own ------------------------------------------------------------------- #
    ap.add_argument("--band", default=DEFAULT_BAND,
                    help="attention-knockout band as lo-hi BLOCK indices (default 6-14)")
    ap.add_argument("--arm", default="demo_all",
                    help=f"knockout arm; known: {sb.KNOCKOUT_ARMS}")
    ap.add_argument("--attn-impl", default="eager", choices=["eager", "sdpa"],
                    help="FORCED to eager whenever the knockout is live: under SDPA the additive "
                         "mask edit is discarded and the knockout is a silent no-op. `sdpa` is "
                         "accepted ONLY with --no-knockout, as a baseline-parity diagnostic.")
    ap.add_argument("--no-knockout", action="store_true",
                    help="capture with NO hooks. This is the baseline-reproduction control: it "
                         "must reproduce the committed extract_boombness cache.")
    ap.add_argument("--on-no-demo-block", default="skip", choices=["skip", "fail"],
                    help="n_examples==0 rows have no demonstrations to knock out. Default: ledger "
                         "and skip (they are ABSENT from the cache, by design).")
    ap.add_argument("--smoke", type=int, default=0,
                    help="run only N prompts (that can carry the knockout), as a pre-flight")
    ap.add_argument("--compare-baseline", default="",
                    help="an extract_boombness run dir; its cache is compared against this run's, "
                         "per (prompt, layer), and the numbers are written to summary.json")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    knockout = not args.no_knockout
    if knockout and args.attn_impl != "eager":
        raise SystemExit("REFUSING: --attn-impl sdpa with the knockout live. Under SDPA the custom "
                         "mask is discarded silently and the run would be an un-knocked-out "
                         "baseline filed under a knockout name.")
    attn_impl = "eager" if knockout else args.attn_impl
    args._enable_thinking = dc_parse_thinking(args.enable_thinking)
    seed_everything(args.seed)

    dc, pc = ds(), pair()
    all_rows = read_jsonl(args.bank)
    rows = select_rows(all_rows, args.smoke, args.limit, knockout)
    if not rows:
        raise SystemExit(f"no rows selected from {args.bank}")

    run = RunDir("extract_boombness", args, tag=args.tag, want_cache=True)
    ledger = FailureLedger()
    model_id = args.model or dc.PRIMARY_MODEL
    lm = dc.load_model(model_id, dtype=getattr(torch, args.dtype), attn_implementation=attn_impl)
    # RE-CHECK ON THE LOADED CONFIG, not on the string we asked for (score_behavior.py:1634). A
    # transformers version that silently substitutes an implementation must fail here.
    if knockout and getattr(getattr(lm.model, "config", None), "_attn_implementation",
                            "eager") != "eager":
        raise SystemExit("REFUSING: the model did not load with attn_implementation='eager'; the "
                         "mask edit would be discarded silently.")

    run.note_bank(args.bank)
    run.note_model(lm.model_id, revision=lm.revision, dtype=str(lm.dtype),
                   attn_implementation=attn_impl, num_layers=lm.num_layers,
                   hidden_size=lm.hidden_size, tokenizer_obj=lm.tokenizer, model_obj=lm.model)
    args._bank_file_sha16 = run._extra_meta.get("bank_file_sha16")

    layers = (list(range(lm.num_layers)) if args.layers == "all"
              else [int(x) for x in args.layers.split(",") if x.strip() != ""])
    lo, hi = (int(x) for x in args.band.split("-"))
    band = list(range(lo, hi + 1))
    # BAND RANGE CHECK AND ECHO (score_behavior.py:1700's finding S3): a band copied from a model
    # of a different depth fails SILENTLY as a weaker knockout, and no exception can catch that.
    if not (0 <= lo <= hi):
        raise SystemExit(f"REFUSING: malformed --band {args.band!r} (need 0 <= lo <= hi)")
    if hi >= lm.num_layers:
        raise SystemExit(f"REFUSING: --band {args.band!r} addresses block {hi} but {model_id} has "
                         f"only {lm.num_layers} blocks (0-{lm.num_layers - 1}).")
    if max(layers) >= lm.num_layers:
        raise SystemExit(f"REFUSING: --layers asks for block {max(layers)} of {lm.num_layers}")
    if knockout and args.arm not in sb.KNOCKOUT_ARMS:
        raise SystemExit(f"REFUSING: unknown arm {args.arm!r}; known: {sb.KNOCKOUT_ARMS}")

    print(f"[ko-extract] model={lm.model_id} blocks={lm.num_layers} hidden={lm.hidden_size} "
          f"attn={attn_impl}")
    print(f"[ko-extract] capture layers={layers} position={args.position}")
    if knockout:
        print(f"[ko-extract] KNOCKOUT LIVE: arm={args.arm} scope={KNOCKOUT_SCOPE} "
              f"band {args.band} -> blocks {lo}..{hi} of {lm.num_layers} "
              f"({hi - lo + 1} blocks, depth {lo / lm.num_layers:.3f}-"
              f"{(hi + 1) / lm.num_layers:.3f}); liveness required > 0: "
              f"{list(pc.LIVENESS_REQUIREMENT[KNOCKOUT_SCOPE])}", flush=True)
    else:
        print("[ko-extract] KNOCKOUT DISABLED (--no-knockout): baseline-reproduction control",
              flush=True)

    # `band` / `arm` are recorded as None on a baseline pass rather than echoing their argparse
    # defaults: a metadata block that names an arm and a band a run never applied is exactly the
    # kind of artifact that gets read three weeks later as evidence that it did.
    run.note(layers=layers, band=(band if knockout else None),
             band_str=(args.band if knockout else None), arm=(args.arm if knockout else None),
             knockout_applied=knockout, knockout_scope=(KNOCKOUT_SCOPE if knockout else None),
             position=args.position, attn_implementation=attn_impl,
             n_bank_rows_used=len(rows), smoke=int(args.smoke or 0),
             layer_convention=sg.LAYER_CONVENTION)

    summary = {"model": lm.model_id, "n_bank_rows": len(all_rows),
               "n_bank_rows_used": len(rows), "layers": layers, "position": args.position,
               "attn_implementation": attn_impl, "activation_dtype": str(lm.dtype),
               "bank_file_sha16": run._extra_meta.get("bank_file_sha16"),
               "bank_rows_sha16": run._extra_meta.get("bank_rows_sha16"),
               "bank_n_rows": run._extra_meta.get("bank_n_rows")}
    summary.update(capture(lm, dc, pc, rows, layers, band, run, ledger, args))

    if args.compare_baseline:
        cp = os.path.join(run.cache, "final_occurrence_reps.pt")
        if os.path.exists(cp):
            cmp_ = compare_to_cache(cp, args.compare_baseline)
            summary["baseline_comparison"] = cmp_
            print("[ko-extract] baseline comparison: " + json.dumps(cmp_, indent=2))

    run.finish(summary=summary, ledger=ledger)
    print(f"[ko-extract] -> {run.path}")
    print(f"[ko-extract] failures: {ledger.as_dict()['failure_reasons']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
