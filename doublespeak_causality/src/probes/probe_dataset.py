"""probe_dataset.py -- build the contextual-identity ("Bombness") probe dataset
from the frozen v3 corpus.

This is the corpus -> labeled-extraction-spec step. It is deliberately PURE PYTHON
(no torch, no model): it decides *which* (example, condition, position) triples to
extract activations from and *what label* each carries, with the split discipline
and the "hold CARROT out" rule baked in. The actual activation extraction (which
needs the model) is a separate module.

Design (plan §5.2, "Probe B -- contextual-binding Bombness probe", the headline
probe; and Appendix A5/A9). The role-confusion paper holds *content* byte-identical
and varies the *role*; we hold the *surface codeword* identical and vary the
*contextual binding*:

    doublespeak condition : codeword X is bound (by demos) to its harmful target
                            concept  -> "Bombness HIGH"  (label 1)
    benign     condition  : the SAME codeword X is bound to a benign concept
                            -> "Bombness LOW"   (label 0)

The probe reads the hidden state at the codeword token position and must decode the
*contextually assigned* identity, not the lexical identity of X (which is identical
across the pair). `neutral` is available as a no-binding baseline; `direct` contains
no codeword and is excluded from codeword-position probing.

Confound controls this construction is built to survive (Gate 1, plan §5.4):
  - token-identity baseline: X is surface-identical across the labelled pair, so the
    surface codeword alone carries no label information *within a matched pair*.
  - split leakage: split key is the normalized target concept; CARROT is in dev,
    BOMB in no split; codewords are pairwise-disjoint across splits.
  - position/length: reported per-example so the extraction layer can length-match
    and pass explicit position_ids (D5 / Appendix A9.2); this module surfaces the
    precomputed codeword token spans rather than re-deriving them.

Corpus: data/splits/clearharm_doublespeak_v3.json (md5 in the manifest). Every
example carries all six conditions, single-token codewords, and precomputed
`codeword_occurrences_templated` spans.

NOTE: this module never reads or emits prompt *text*. It emits ids, splits, labels,
codeword tokens, and integer token spans only. Prompt text is loaded by the
extraction step, on the GPU node, from the same corpus.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from typing import Optional

# Conditions in the v3 corpus. `direct` has no codeword (uses the real concept),
# so it is not a codeword-position probing condition.
BINDING_CONDITIONS = ("doublespeak", "neutral", "benign")
ALL_CONDITIONS = ("doublespeak", "neutral", "direct", "benign", "shuffled", "unrelated")

# Headline Bombness label: which conditions are the positive/negative class.
POSITIVE_CONDITION = "doublespeak"   # codeword bound to harmful target -> Bombness high
NEGATIVE_CONDITION = "benign"        # same codeword bound to benign concept -> Bombness low

PROMPT_FIELD = {c: f"{c}_prompt" for c in ALL_CONDITIONS}


@dataclass(frozen=True)
class ProbeItem:
    """One (example, condition) unit to extract activations from.

    Positions are token spans into the *templated* prompt for `condition`, as
    precomputed in the corpus. `label` is the Bombness label for the headline probe
    (1 = bound-to-harmful, 0 = bound-to-benign); None for conditions that are not
    part of the labelled headline pair (e.g. neutral), which are still useful as
    baselines and for the trajectory analysis.
    """
    example_id: str
    cohort: str
    split: str                    # train / dev / test
    condition: str                # doublespeak / neutral / benign / ...
    codeword: str                 # surface codeword (benign vocabulary, e.g. "dossier")
    codeword_token_id: Optional[int]
    target_concept: str
    normalized_concept: str       # split key (cluster)
    harm_category: str
    single_token: bool
    label: Optional[int]          # 1 / 0 / None (headline Bombness label)
    n_codeword_occurrences: int
    codeword_spans: tuple         # tuple of (start, end) token spans in the templated prompt
    prompt_field: str             # which corpus field holds the templated prompt text

    def query_span(self) -> Optional[tuple]:
        """The LAST codeword occurrence == the query codeword (primary probe position,
        plan §5.2). Demos come first; the query is the final occurrence."""
        if not self.codeword_spans:
            return None
        return self.codeword_spans[-1]


def _spans(occ_list) -> tuple:
    out = []
    for o in occ_list or []:
        sp = o.get("span") if isinstance(o, dict) else o
        if sp and len(sp) == 2:
            out.append((int(sp[0]), int(sp[1])))
    return tuple(out)


def load_corpus(path: str) -> dict:
    with open(path) as fh:
        return json.load(fh)


def build_items(
    corpus: dict,
    conditions=BINDING_CONDITIONS,
    cohort: Optional[str] = None,
    splits: Optional[tuple] = None,
) -> list[ProbeItem]:
    """Expand the corpus into ProbeItems for the given conditions.

    Args:
      conditions: which conditions to emit (default: the binding conditions with a
                  codeword; `direct` has no codeword and is excluded by default).
      cohort:     restrict to one cohort ("clearharm" / "generated"), or None for all.
      splits:     restrict to these splits, or None for all.
    """
    items: list[ProbeItem] = []
    for ex in corpus["examples"]:
        if cohort is not None and ex["cohort"] != cohort:
            continue
        if splits is not None and ex["split"] not in splits:
            continue
        tok = ex.get("tokenized_codeword") or []
        cw_tok_id = int(tok[0]) if len(tok) == 1 else None
        for cond in conditions:
            if cond not in ALL_CONDITIONS:
                raise ValueError(f"unknown condition {cond!r}")
            label = None
            if cond == POSITIVE_CONDITION:
                label = 1
            elif cond == NEGATIVE_CONDITION:
                label = 0
            items.append(ProbeItem(
                example_id=str(ex["example_id"]),
                cohort=ex["cohort"],
                split=ex["split"],
                condition=cond,
                codeword=ex["codeword"],
                codeword_token_id=cw_tok_id,
                target_concept=ex["target_concept"],
                normalized_concept=ex["normalized_concept"],
                harm_category=ex["harm_category"],
                single_token=bool(ex.get("single_token_primary")),
                label=label,
                n_codeword_occurrences=int(ex.get("n_codeword_occurrences_templated") or 0),
                codeword_spans=_spans(ex.get("codeword_occurrences_templated")),
                prompt_field=PROMPT_FIELD[cond],
            ))
    return items


def labelled_pairs(items: list[ProbeItem]) -> list[ProbeItem]:
    """The headline probe's labelled subset: the positive/negative binding conditions
    only (label in {0,1}). Matched by example_id -> one positive + one negative each."""
    return [it for it in items if it.label is not None]


def split_stats(items: list[ProbeItem]) -> dict:
    """Summary for a sanity/leakage check, used by the unit test and the extraction
    entrypoint's preflight. No prompt text touched."""
    from collections import defaultdict
    per_split = defaultdict(lambda: {"n": 0, "codewords": set(), "concepts": set(),
                                     "pos": 0, "neg": 0, "single_tok": 0})
    for it in items:
        s = per_split[it.split]
        s["n"] += 1
        s["codewords"].add(it.codeword.lower())
        s["concepts"].add(it.normalized_concept.lower())
        s["single_tok"] += int(it.single_token)
        if it.label == 1:
            s["pos"] += 1
        elif it.label == 0:
            s["neg"] += 1
    # freeze sets to counts + keep the sets for disjointness checks
    return {k: {"n": v["n"], "n_codewords": len(v["codewords"]),
                "n_concepts": len(v["concepts"]), "pos": v["pos"], "neg": v["neg"],
                "single_tok": v["single_tok"],
                "_codewords": v["codewords"], "_concepts": v["concepts"]}
            for k, v in per_split.items()}


def assert_split_discipline(items: list[ProbeItem], carrot="carrot", bomb="bomb") -> dict:
    """Enforce the frozen split discipline (manifest D4, plan §3.5). Raises on any
    violation so a bug can never silently produce a leaky probe dataset.

    Checks:
      - codewords pairwise-disjoint across splits;
      - normalized concepts (the split key) pairwise-disjoint across splits;
      - CARROT is held out of TRAIN (it lives in dev); BOMB in no split.
    """
    st = split_stats(items)
    splits = list(st)
    problems = []

    for i in range(len(splits)):
        for j in range(i + 1, len(splits)):
            a, b = splits[i], splits[j]
            cw = st[a]["_codewords"] & st[b]["_codewords"]
            co = st[a]["_concepts"] & st[b]["_concepts"]
            if cw:
                problems.append(f"codeword leak {a}/{b}: {sorted(cw)[:5]}")
            if co:
                problems.append(f"concept leak {a}/{b}: {sorted(co)[:5]}")

    train_cw = st.get("train", {}).get("_codewords", set())
    if carrot in train_cw:
        problems.append(f"CARROT must be held out of train (plan §5.2)")
    all_cw = set().union(*(st[s]["_codewords"] for s in splits)) if splits else set()
    if bomb in all_cw:
        problems.append(f"BOMB must not appear as a codeword in any split")

    if problems:
        raise AssertionError("split discipline violated:\n  " + "\n  ".join(problems))
    return {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")}
            for k, v in st.items()}


def to_jsonl_records(items: list[ProbeItem]) -> list[dict]:
    """Serializable records for the extraction manifest (no prompt text)."""
    return [asdict(it) for it in items]


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", default=os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "splits",
        "clearharm_doublespeak_v3.json"))
    ap.add_argument("--cohort", default=None)
    args = ap.parse_args()
    corpus = load_corpus(os.path.abspath(args.corpus))
    items = build_items(corpus, cohort=args.cohort)
    stats = assert_split_discipline(items)
    print(f"built {len(items)} probe items over {len(labelled_pairs(items))} labelled")
    for s, v in sorted(stats.items()):
        print(f"  {s:5s}: n={v['n']:4d}  codewords={v['n_codewords']:3d}  "
              f"concepts={v['n_concepts']:3d}  pos={v['pos']:3d} neg={v['neg']:3d}  "
              f"single_tok={v['single_tok']:4d}")
    print("split discipline: OK")
