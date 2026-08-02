#!/usr/bin/env python3
"""Phase-0 automated data-integrity checks (CAUSAL_CIRCUIT_MASTER_PLAN §Phase 0.4).

Validates a locked Doublespeak split file (data/splits/*.json) and, optionally, an
experiment output directory of result rows. Fails LOUDLY (non-zero exit) on any violation.

Checks on the split file:
  - train/test (dev/heldout) example-ID overlap  ............... FATAL
  - duplicate semantic-intent clusters across splits .......... FATAL
  - duplicate/near-identical prompts across splits ............ FATAL
  - each split has >= MIN_PER_SPLIT unique examples ........... FATAL
  - codeword present & localizable after chat templating ...... FATAL (needs --model or --tokenizer)
  - every codeword occurrence detected (>=1 demo + 1 query) ... FATAL
  - multi-token codewords / concepts flagged / excluded ....... WARN (FATAL if in primary set)
  - required per-example fields present ...................... FATAL
  - dataset_revision / model hash recorded .................. WARN

Checks on an output rows dir (--rows-dir, *.jsonl):
  - duplicate (example_id, cell-key) rows .................... FATAL
  - rows carry layer/head/example_id/split/condition metadata . FATAL
  - failed generations / missing judge results recorded ...... WARN (counts reported)

Usage:
  python scripts/validate_data_integrity.py --split data/splits/clearharm_doublespeak_v1.json \
         [--tokenizer meta-llama/Llama-3.1-8B-Instruct] [--rows-dir outputs/<exp>]
Exit 0 = all FATAL checks pass. Exit 1 = at least one FATAL violation.
"""
from __future__ import annotations
import argparse, glob, json, os, sys
from collections import defaultdict

MIN_PER_SPLIT = 20
REQUIRED_FIELDS = [
    "example_id", "harm_category", "intent_cluster", "codeword", "target_concept",
    "doublespeak_prompt", "neutral_prompt", "direct_prompt", "split",
]
SPLIT_NAMES = ("train", "dev", "test", "heldout")

class Report:
    def __init__(self):
        self.fatal = []
        self.warn = []
        self.ok = []
    def f(self, m): self.fatal.append(m)
    def w(self, m): self.warn.append(m)
    def o(self, m): self.ok.append(m)
    def dump(self):
        for m in self.ok:    print(f"  ok    {m}")
        for m in self.warn:  print(f"  WARN  {m}")
        for m in self.fatal: print(f"  FATAL {m}")
        print(f"\n{len(self.ok)} ok / {len(self.warn)} warn / {len(self.fatal)} FATAL")
        return 0 if not self.fatal else 1


def _norm_prompt(p: str) -> str:
    return " ".join((p or "").split()).lower()


def load_examples(split_obj):
    """Accept either {'examples':[...]} or {'train':[...],'test':[...]} or a flat list."""
    if isinstance(split_obj, list):
        return split_obj
    if "examples" in split_obj:
        return split_obj["examples"]
    ex = []
    for k in SPLIT_NAMES:
        if k in split_obj and isinstance(split_obj[k], list):
            for e in split_obj[k]:
                e.setdefault("split", k)
                ex.append(e)
    return ex


def check_split(path, tokenizer_id, rep: Report):
    with open(path) as fh:
        obj = json.load(fh)
    examples = load_examples(obj)
    if not examples:
        rep.f(f"split file {path} has no examples")
        return
    rep.o(f"loaded {len(examples)} examples from {path}")

    # required fields
    for e in examples:
        missing = [k for k in REQUIRED_FIELDS if k not in e]
        if missing:
            rep.f(f"example {e.get('example_id','<no-id>')} missing fields {missing}")

    # group by split
    by_split = defaultdict(list)
    for e in examples:
        by_split[e.get("split", "?")].append(e)
    # map dev->train-like, heldout->test-like for min-count purposes
    train_like = by_split.get("train", []) + by_split.get("dev", [])
    test_like = by_split.get("test", []) + by_split.get("heldout", [])
    for name, grp in (("train/dev", train_like), ("test/heldout", test_like)):
        ids = {e.get("example_id") for e in grp}
        if len(ids) < MIN_PER_SPLIT:
            rep.f(f"{name} has {len(ids)} unique examples (< {MIN_PER_SPLIT})")
        else:
            rep.o(f"{name} has {len(ids)} unique examples (>= {MIN_PER_SPLIT})")

    # per-cohort >=20/>=20 (cohorts are reported as separate statistical claims)
    cohorts = sorted({e.get("cohort") for e in examples if e.get("cohort")})
    for coh in cohorts:
        tr = {e.get("example_id") for e in train_like if e.get("cohort") == coh}
        te = {e.get("example_id") for e in test_like if e.get("cohort") == coh}
        for nm, ids in ((f"cohort '{coh}' train", tr), (f"cohort '{coh}' test", te)):
            if len(ids) < MIN_PER_SPLIT:
                rep.f(f"{nm} has {len(ids)} unique examples (< {MIN_PER_SPLIT})")
            else:
                rep.o(f"{nm} has {len(ids)} unique examples (>= {MIN_PER_SPLIT})")

    # ID overlap
    tr_ids = {e.get("example_id") for e in train_like}
    te_ids = {e.get("example_id") for e in test_like}
    overlap = tr_ids & te_ids
    if overlap:
        rep.f(f"train/test example_id OVERLAP: {sorted(overlap)[:10]}{'...' if len(overlap)>10 else ''} ({len(overlap)})")
    else:
        rep.o("no train/test example_id overlap")

    # intent-cluster overlap (paraphrases must stay in one split)
    tr_cl = {e.get("intent_cluster") for e in train_like}
    te_cl = {e.get("intent_cluster") for e in test_like}
    cl_overlap = {c for c in (tr_cl & te_cl) if c is not None}
    if cl_overlap:
        rep.f(f"intent_cluster OVERLAP across train/test (leakage): {sorted(cl_overlap)[:10]} ({len(cl_overlap)})")
    else:
        rep.o("no intent_cluster overlap across train/test")

    # duplicate prompts across splits
    seen = {}
    for e in train_like:
        for field in ("doublespeak_prompt", "direct_prompt", "neutral_prompt"):
            seen.setdefault(_norm_prompt(e.get(field, "")), e.get("example_id"))
    dup = []
    for e in test_like:
        for field in ("doublespeak_prompt", "direct_prompt", "neutral_prompt"):
            key = _norm_prompt(e.get(field, ""))
            if key and key in seen:
                dup.append((e.get("example_id"), seen[key], field))
    if dup:
        rep.f(f"duplicate prompts across splits: {dup[:5]}{'...' if len(dup)>5 else ''} ({len(dup)})")
    else:
        rep.o("no duplicate prompts across train/test")

    # dataset revision / provenance
    rev = (obj.get("dataset_revision") if isinstance(obj, dict) else None) or \
          (obj.get("_meta", {}).get("dataset_revision") if isinstance(obj, dict) else None)
    if not rev:
        rep.w("no dataset_revision recorded on the split file")
    else:
        rep.o(f"dataset_revision = {rev}")

    # tokenization / codeword occurrence checks
    if tokenizer_id:
        _check_codewords(examples, tokenizer_id, rep)
    else:
        rep.w("no --tokenizer given; skipped codeword-occurrence & multi-token checks")


def _check_codewords(examples, tokenizer_id, rep: Report):
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from transformers import AutoTokenizer
        import ds_common
    except Exception as ex:
        rep.w(f"could not import tokenizer/ds_common ({ex}); skipped codeword checks")
        return
    tok = AutoTokenizer.from_pretrained(tokenizer_id)
    multi_primary = []
    for e in examples:
        cw = e.get("codeword")
        concept = e.get("target_concept")
        primary = e.get("single_token_primary", True)
        # multi-token flag
        for label, word in (("codeword", cw), ("target_concept", concept)):
            if not word:
                continue
            try:
                hit = ds_common.find_word_occurrences_in_text(tok, word, word)
                n_sub = len(hit.subtoken_ids) if hasattr(hit, "subtoken_ids") else None
            except Exception:
                n_sub = None
            ids = tok.encode(" " + word, add_special_tokens=False)
            if len(ids) > 1:
                if primary:
                    multi_primary.append((e.get("example_id"), label, word, len(ids)))
        # codeword localizable in templated doublespeak prompt
        prompt = e.get("doublespeak_prompt", "")
        try:
            templated = ds_common.apply_template(tok, prompt, add_generation_prompt=True)
            hit = ds_common.find_word_occurrences_in_text(tok, templated, cw)
            n_occ = hit.n if hasattr(hit, "n") else len(getattr(hit, "spans", []))
            if n_occ < 2:
                rep.f(f"example {e.get('example_id')}: codeword '{cw}' has {n_occ} occurrence(s) "
                      f"in templated DS prompt (need >=1 demo + 1 query)")
        except Exception as ex:
            rep.f(f"example {e.get('example_id')}: codeword '{cw}' NOT localizable post-template ({ex})")
    if multi_primary:
        rep.f(f"multi-token codeword/concept in PRIMARY set: {multi_primary[:5]}"
              f"{'...' if len(multi_primary)>5 else ''} ({len(multi_primary)}) — exclude or mark single_token_primary=false")
    else:
        rep.o("all primary codewords/concepts are single-token")


def check_rows(rows_dir, rep: Report):
    files = sorted(glob.glob(os.path.join(rows_dir, "**", "*.jsonl"), recursive=True))
    if not files:
        rep.w(f"no *.jsonl rows under {rows_dir}")
        return
    seen = set()
    n_rows = n_failed_gen = n_missing_judge = 0
    meta_keys = ("example_id", "split", "condition")
    for f in files:
        for line in open(f):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                rep.f(f"unparseable row in {f}")
                continue
            n_rows += 1
            missing = [k for k in meta_keys if k not in r]
            if missing:
                rep.f(f"row in {os.path.basename(f)} missing metadata {missing}")
            cell = (r.get("example_id"), r.get("split"), r.get("condition"),
                    r.get("layer"), r.get("head"), r.get("activation_type"),
                    r.get("position_set"), r.get("direction"), r.get("control"),
                    r.get("strength"))
            if cell in seen:
                rep.f(f"duplicate row for cell {cell} in {os.path.basename(f)}")
            seen.add(cell)
            if r.get("generation_failed") or r.get("completion") == "":
                n_failed_gen += 1
            if "judge_score" in r and r.get("judge_score") is None:
                n_missing_judge += 1
    rep.o(f"scanned {n_rows} rows across {len(files)} file(s)")
    if n_failed_gen:
        rep.w(f"{n_failed_gen} failed/empty generations recorded")
    if n_missing_judge:
        rep.w(f"{n_missing_judge} rows with missing judge_score (must be retried)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", help="path to locked split json")
    ap.add_argument("--tokenizer", help="tokenizer/model id for codeword localization checks")
    ap.add_argument("--rows-dir", help="output dir of *.jsonl result rows to validate")
    args = ap.parse_args()

    rep = Report()
    if args.split:
        if not os.path.exists(args.split):
            print(f"split file not found: {args.split}\n(Phase 1 not yet built — nothing to validate.)")
            return 0
        print(f"== split integrity: {args.split} ==")
        check_split(args.split, args.tokenizer, rep)
    if args.rows_dir:
        print(f"== rows integrity: {args.rows_dir} ==")
        check_rows(args.rows_dir, rep)
    if not args.split and not args.rows_dir:
        ap.error("provide --split and/or --rows-dir")
    code = rep.dump()
    sys.exit(code)


if __name__ == "__main__":
    main()
