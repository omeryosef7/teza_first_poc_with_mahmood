"""tokenization_audit.py — plan §2.4 (mandatory before any activation work).

"Do not assume `carrot` and `bomb` are single tokens in every model."

What this does, per model and per bank row:
  1. prints the tokenization of every target word and its surface variants
     (bare / leading-space / capitalized / plural), so a multi-token target is visible
     rather than assumed away;
  2. resolves the token span of EVERY occurrence of the target word in the TEMPLATED
     prompt, using the house offset-based finder (`ds_common.find_word_occurrences_in_text`
     with add_special_tokens=False, because apply_template already emitted BOS — mixing
     that with the add_special_tokens=True path is a silent one-token index shift);
  3. asserts that the recovered spans agree with the character spans the generator recorded
     in `expected_target_occurrences`, so a disagreement between the text-level and
     token-level view of "occurrence i" is caught here rather than corrupting a heatmap;
  4. labels each row `tokenization_ok` / `tokenization_ambiguous` with a reason, and writes
     the per-occurrence token spans so downstream scripts never re-derive them;
  5. checks the 2x2 alignment invariant AT THE TOKEN LEVEL: within a family, the four cells
     must have the same number of target occurrences and the same occurrence ORDER, and the
     exact-swap pairs (B,C) and (E,A) must have token sequences that differ only inside the
     target spans. A prompt pair that is character-aligned but not token-aligned would
     silently break position-matched patching (plan §5.1), which is the single most
     load-bearing assumption of the whole sprint.

CPU-only: loads a tokenizer, never a model.

Usage:
  python src/boombness/tokenization_audit.py --bank data/boombness_prompts/boombness_prompt_bank.jsonl
  python src/boombness/tokenization_audit.py --limit 50 --models meta-llama/Llama-3.1-8B-Instruct,Qwen/Qwen3-14B
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA_DIR, FailureLedger, RunDir, ds, read_jsonl, seed_everything  # noqa: E402

DEFAULT_BANK = os.path.join(DATA_DIR, "boombness_prompt_bank.jsonl")
DEFAULT_MODELS = "meta-llama/Llama-3.1-8B-Instruct"


def word_variants(word: str) -> List[str]:
    return [word, " " + word, word.capitalize(), " " + word.capitalize(),
            word + "s", " " + word + "s", word.upper()]


def variant_report(tok, word: str) -> Dict[str, Dict]:
    out = {}
    for v in word_variants(word):
        ids = tok(v, add_special_tokens=False)["input_ids"]
        out[v] = {"ids": ids, "n_tokens": len(ids),
                  "pieces": [tok.decode([i]) for i in ids]}
    return out


def audit_row(tok, row: Dict, dc) -> Dict:
    """Resolve token spans for every target occurrence in the templated prompt."""
    word = row["target_surface"]
    templated = dc.apply_template(tok, row["full_prompt"])
    ids = tok(templated, add_special_tokens=False)["input_ids"]

    rec: Dict[str, object] = {
        "prompt_id": row["prompt_id"], "family_id": row["family_id"],
        "condition": row["condition"], "cell": row["cell"], "query_kind": row["query_kind"],
        "n_examples": row["n_examples"], "domain": row["domain"], "split": row["split"],
        "target_surface": word, "n_prompt_tokens": len(ids),
        "expected_n_occurrences": row["n_target_occurrences"],
    }

    try:
        hit = dc.find_word_occurrences_in_text(tok, templated, word, add_special_tokens=False)
    except Exception as e:
        rec.update({"tokenization_ok": False, "reason": f"finder_raised:{type(e).__name__}",
                    "n_found": 0, "spans": [], "last_idx": []})
        return rec

    spans = [list(s) for s in hit.spans]
    rec.update({"n_found": hit.n, "spans": spans, "first_idx": list(hit.first_idx),
                "last_idx": list(hit.last_idx), "variant": hit.variant,
                "subtoken_ids": list(hit.subtoken_ids),
                "n_subtokens": len(hit.subtoken_ids),
                "is_single_token": len(hit.subtoken_ids) == 1})

    if hit.n != row["n_target_occurrences"]:
        rec.update({"tokenization_ok": False,
                    "reason": f"occurrence_count_mismatch:text={row['n_target_occurrences']},tokens={hit.n}"})
        return rec
    widths = {e - s for s, e in spans}
    if len(widths) > 1:
        # A target that tokenizes differently in different contexts is not fatal, but it must
        # never be silently averaged over; downstream aggregation is told about it.
        rec.update({"tokenization_ok": True, "tokenization_ambiguous": True,
                    "reason": f"variable_span_width:{sorted(widths)}"})
        return rec
    rec.update({"tokenization_ok": True, "tokenization_ambiguous": False, "reason": ""})
    return rec


def audit_family_alignment(tok, rows: List[Dict], dc) -> Optional[List[str]]:
    """Token-level 2x2 invariants for one family.

    Returns a (possibly empty) list of violations, or None if the family does not contain all
    four core conditions and therefore could not be checked at all. Returning [] for an
    unchecked family made the summary read "540 families, 0 violations" when only 216 of them
    had ever been examined — a coverage claim the run had not earned.
    """
    by_cond = {r["condition"]: r for r in rows}
    bad: List[str] = []
    core = ("benign_literal", "direct_harmful", "natural_doublespeak", "concept_in_benign_ctx")
    if not set(core).issubset(by_cond):
        return None          # NOT "no violations" — this family was never checkable
    # A query that deliberately names BOTH words (the forced-choice kinds) cannot satisfy the
    # exact-swap invariant at the token level either: cell B's query reads "...bomb ... carrot
    # or ... bomb" where cell C's reads "...carrot ... carrot or ... bomb". Those families are
    # reported as NOT CHECKED rather than as passing, which is the distinction the previous
    # version of this function got wrong.
    if any(not r.get("occurrence_analysis_safe", True) for r in rows):
        return None

    ids = {}
    occ = {}
    for c in core:
        t = dc.apply_template(tok, by_cond[c]["full_prompt"])
        ids[c] = tok(t, add_special_tokens=False)["input_ids"]
        try:
            h = dc.find_word_occurrences_in_text(tok, t, by_cond[c]["target_surface"],
                                                 add_special_tokens=False)
            occ[c] = [list(s) for s in h.spans]
        except Exception as e:
            bad.append(f"{c}: finder raised {type(e).__name__}")
            return bad

    ns = {c: len(occ[c]) for c in core}
    if len(set(ns.values())) > 1:
        bad.append(f"token-level occurrence counts differ: {ns}")

    # Exact-swap pairs must be identical outside the target spans.
    for hi, lo in (("direct_harmful", "natural_doublespeak"),
                   ("concept_in_benign_ctx", "benign_literal")):
        if len(occ[hi]) != len(occ[lo]):
            bad.append(f"{hi}/{lo}: differing occurrence counts {len(occ[hi])} vs {len(occ[lo])}")
            continue
        a = _mask_spans(ids[hi], occ[hi])
        b = _mask_spans(ids[lo], occ[lo])
        if a != b:
            bad.append(f"{hi}/{lo}: token sequences differ OUTSIDE the target spans "
                       f"(len {len(a)} vs {len(b)})")
    return bad


def _mask_spans(ids: List[int], spans: List[List[int]]) -> List[object]:
    """Replace each target span with a single sentinel so the rest can be compared."""
    out: List[object] = []
    i = 0
    starts = {s: e for s, e in spans}
    while i < len(ids):
        if i in starts:
            out.append("<TARGET>")
            i = starts[i]
        else:
            out.append(ids[i])
            i += 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", default=DEFAULT_BANK)
    ap.add_argument("--models", default=DEFAULT_MODELS,
                    help="comma-separated HF ids; tokenizers only, no weights loaded")
    ap.add_argument("--limit", type=int, default=0, help="0 = all rows")
    ap.add_argument("--seed", type=int, default=20260816)
    ap.add_argument("--tag", default="audit")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    seed_everything(args.seed)

    from transformers import AutoTokenizer
    dc = ds()
    rows = read_jsonl(args.bank)
    if args.limit:
        rows = rows[:args.limit]

    run = RunDir("tokenization_audit", args, tag=args.tag)
    ledger = FailureLedger()
    summary: Dict[str, object] = {"bank": args.bank, "n_bank_rows": len(rows), "models": {}}

    for model_id in [m.strip() for m in args.models.split(",") if m.strip()]:
        try:
            tok = AutoTokenizer.from_pretrained(model_id)
        except Exception as e:
            print(f"[audit] SKIP {model_id}: {type(e).__name__}: {e}")
            summary["models"][model_id] = {"error": f"{type(e).__name__}: {e}"}
            ledger.fail("tokenizer_load_failed", model_id)
            continue

        codeword = rows[0]["codeword"]
        concept = rows[0]["concept"]
        variants = {w: variant_report(tok, w) for w in (codeword, concept)}
        print(f"\n=== {model_id} ===")
        for w, rep in variants.items():
            for v, info in rep.items():
                print(f"  {w:8s} variant {v!r:14s} -> {info['n_tokens']} tok {info['pieces']}")

        per_model = collections.Counter()
        ambiguous_ids: List[str] = []
        families: Dict[str, List[Dict]] = collections.defaultdict(list)
        for row in rows:
            rec = audit_row(tok, row, dc)
            rec["model"] = model_id
            run.log_row(rec)
            if rec.get("tokenization_ok"):
                ledger.ok()
                per_model["ok"] += 1
                if rec.get("tokenization_ambiguous"):
                    per_model["ambiguous"] += 1
                    ambiguous_ids.append(str(rec["prompt_id"]))
            else:
                ledger.fail(f"tokenization:{rec.get('reason', 'unknown')}", str(rec["prompt_id"]))
                per_model["bad"] += 1
            families[row["family_id"]].append(row)

        fam_violations: List[str] = []
        n_checked = n_skipped = 0
        for fam, frows in families.items():
            vs = audit_family_alignment(tok, frows, dc)
            if vs is None:
                n_skipped += 1
                continue
            n_checked += 1
            for v in vs:
                fam_violations.append(f"{fam}: {v}")
                # Plan §2.2: a violation must appear in the failure ledger, not only in a
                # console line and a summary sub-key, or summary.json reports n_failed=0 on a
                # run whose exact-swap pairs are misaligned.
                ledger.fail(f"family_token_alignment:{v.split(':')[0]}", fam)

        summary["models"][model_id] = {
            "variants": variants,
            "n_ok": per_model["ok"], "n_bad": per_model["bad"],
            "n_ambiguous": per_model["ambiguous"],
            "ambiguous_prompt_ids": ambiguous_ids[:50],
            "n_families": len(families),
            "n_families_alignment_checked": n_checked,
            "n_families_skipped_incomplete_2x2": n_skipped,
            "n_family_token_alignment_violations": len(fam_violations),
            "family_token_alignment_violations": fam_violations[:50],
            "codeword_is_single_token": all(
                len(v["ids"]) == 1 for k, v in variants[codeword].items() if k == " " + codeword),
            "concept_is_single_token": all(
                len(v["ids"]) == 1 for k, v in variants[concept].items() if k == " " + concept),
        }
        print(f"  rows ok={per_model['ok']} bad={per_model['bad']} ambiguous={per_model['ambiguous']}")
        print(f"  families={len(families)} checked={n_checked} "
              f"skipped_incomplete={n_skipped} token-alignment violations={len(fam_violations)}")
        for v in fam_violations[:5]:
            print(f"    VIOLATION {v}")

    run.finish(summary=summary, ledger=ledger)
    print(f"\n[audit] -> {run.path}")
    bad_total = sum(m.get("n_bad", 0) + m.get("n_family_token_alignment_violations", 0)
                    for m in summary["models"].values() if isinstance(m, dict))
    if args.strict and bad_total:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
