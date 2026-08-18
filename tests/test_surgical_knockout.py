"""Pins the selection logic of src/boombness/surgical_knockout.py (defects T3/T3b/T7/T7b).

Every `test_prefix_*` case here execs the corresponding snippet of the PRE-FIX source in a
stub namespace and asserts the old behaviour was wrong. That is what makes these regression
tests rather than tautologies: they run the defective bytes and would fail if the defect
were imaginary. No GPU, no model, no torch forward pass is involved.

BASELINE PINNING BUG, FOUND AND FIXED 2026-08-18 — the defect that silently disarmed this
entire file. The first version resolved the baseline as `git show HEAD:src/boombness/
surgical_knockout.py`. `HEAD` is a MOVING REF. It named the pre-fix file only for the few
minutes between writing these tests and committing the fix; the instant the fix landed (as
a8251ffa) `HEAD` became the FIXED file, the snippet anchors (`dst = dsts[0]`,
`[:args.n_families]`, `payload = None`) no longer existed in it, and all four
`test_prefix_*` cases died with StopIteration. Measured before this repair: `pytest -q` gave
4 failed, 12 passed. A regression test whose baseline is a moving ref does not decay
gracefully into a weaker test — it decays into a red suite, or worse (had an anchor still
matched inside the new docstrings, which `dst  = dsts[0]  # for ranking/reporting` very
nearly does) into a green test asserting nothing. The baseline is now the IMMUTABLE BLOB
hash of the pre-fix file, and `prefix_source()` asserts the blob really is pre-fix before
any test uses it, so an unreachable or wrong blob fails loudly instead of vacuously passing.
"""
from __future__ import annotations

import collections
import contextlib
import os
import subprocess
import sys
import textwrap
import types
import unittest
from typing import Sequence

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "src", "boombness")
sys.path.insert(0, SRC)

import surgical_knockout as sk  # noqa: E402


# Immutable blob of src/boombness/surgical_knockout.py as of a8251ffa^ — the last commit
# BEFORE the T3/T3b/T7/T7b fix. A blob hash, not a ref: it survives rebases, new commits and
# branch moves, which `HEAD` did not (see module docstring).
PREFIX_BLOB = "0b27dab02c22d9102afb83130e374ed68580860d"

# Bytes that must be present in the baseline. If the blob ever resolves to something that
# lacks these, the pre-fix snippets below would be exec'ing the wrong source and every
# `test_prefix_*` assertion would be meaningless, so we refuse to run instead.
PREFIX_MARKERS = (
    "dst = dsts[0]                        # for ranking/reporting",
    "[:args.n_families]",
    "and i < dst]",
)


def prefix_source() -> str:
    """Return the PRE-FIX file, by immutable blob hash, verified to actually be pre-fix."""
    try:
        src = subprocess.check_output(["git", "cat-file", "blob", PREFIX_BLOB],
                                      cwd=REPO, stderr=subprocess.PIPE).decode()
    except subprocess.CalledProcessError as e:                       # pragma: no cover
        raise AssertionError(
            f"pre-fix baseline blob {PREFIX_BLOB} is unreachable ({e.stderr.decode().strip()}). "
            "These regression tests cannot be evaluated without it; do not skip them.") from e
    missing = [m for m in PREFIX_MARKERS if m not in src]
    assert not missing, (f"blob {PREFIX_BLOB} is not the pre-fix source; missing {missing!r}. "
                         "Refusing to assert against the wrong baseline.")
    return src


def prefix_snippet(first: str, last: str) -> str:
    """Return the pre-fix source lines from the line containing `first` through `last`."""
    lines = prefix_source().splitlines()
    i = next(n for n, ln in enumerate(lines) if first in ln)
    j = next(n for n, ln in enumerate(lines) if last in ln and n >= i)
    return textwrap.dedent("\n".join(lines[i:j + 1]))


def fake_rows():
    """Two example-counts x two splits x three families per domain, over four domains."""
    rows = []
    for dom in ("aviation", "biology", "chemistry", "diving"):
        for f in range(3):
            fam = f"{dom}_fam{f}"
            for n_ex in (4, 8):
                rows.append({"family_id": fam, "domain": dom, "n_examples": n_ex,
                             "split": "dev" if f % 2 == 0 else "heldout",
                             "prompt_id": f"{fam}_{n_ex}"})
    return rows


class TestDestinationChoice(unittest.TestCase):
    """T3: the RANKING destination must be the readout token, not the codeword token."""

    def test_both_ranks_at_readout(self):
        dsts, rank = sk.choose_destinations("both", 104, 113)
        self.assertEqual(dsts, [104, 113])      # knockout still cuts into both
        self.assertEqual(rank, 113)             # but ranking happens at the readout

    def test_readout_and_codeword_modes(self):
        self.assertEqual(sk.choose_destinations("readout", 104, 113), ([113], 113))
        self.assertEqual(sk.choose_destinations("codeword", 104, 113), ([104], 104))

    def test_degenerate_equal_positions(self):
        self.assertEqual(sk.choose_destinations("both", 113, 113), ([113], 113))

    def test_unknown_mode_raises(self):
        with self.assertRaises(ValueError):
            sk.choose_destinations("nonsense", 1, 2)

    def test_prefix_ranked_at_the_codeword(self):
        ns = {"args": types.SimpleNamespace(dst="both"), "last": [30, 60, 104], "ids": [0] * 114}
        exec(prefix_snippet("readout_pos = len(ids) - 1", "# for ranking/reporting"), ns)
        self.assertEqual(ns["dst"], 104)            # pre-fix ranked at the codeword ...
        self.assertEqual(ns["readout_pos"], 113)    # ... 9 tokens before the readout
        self.assertNotEqual(ns["dst"], sk.choose_destinations("both", 104, 113)[1])


class TestDemoSourceBound(unittest.TestCase):
    """T3b: the source-position bound is max(dsts), not the codeword position."""

    def test_prefix_dropped_tokens_between_codeword_and_readout(self):
        offsets = [(i, i + 1) for i in range(120)]
        lo, hi = 0, 120
        self.assertEqual(sk.demo_source_bound([104, 113]), 113)
        self.assertEqual(sk.demo_source_bound([113]), 113)
        new = [i for i, (a, b) in enumerate(offsets)
               if a >= lo and b <= hi and b > a and i < sk.demo_source_bound([104, 113])]
        ns = {"enc": {"offset_mapping": offsets}, "lo": lo, "hi": hi, "dst": 104}
        src = prefix_snippet("demo_pos = [i for i, (a, b) in enumerate", "and i < dst]")
        exec("demo_pos = " + src.split("demo_pos = ", 1)[1], ns)
        old = ns["demo_pos"]
        self.assertEqual(len(old), 104)
        self.assertEqual(len(new), 113)
        self.assertEqual(sorted(set(new) - set(old)), list(range(104, 113)))


class TestDirectionCrossFit(unittest.TestCase):
    """T7: rank each row with the direction fitted on the OTHER split."""

    def test_cross_fit_both_directions(self):
        self.assertEqual(sk.choose_direction_split(["dev", "heldout"], "dev"), ("heldout", False))
        self.assertEqual(sk.choose_direction_split(["dev", "heldout"], "heldout"), ("dev", False))

    def test_self_fit_flagged_when_other_split_missing(self):
        self.assertEqual(sk.choose_direction_split(["dev"], "dev"), ("dev", True))
        self.assertEqual(sk.choose_direction_split(["heldout"], "heldout"), ("heldout", True))

    def test_unknown_split_is_conservatively_self_fit(self):
        split, self_fit = sk.choose_direction_split(["dev", "heldout"], "train")
        self.assertEqual(split, "dev")
        self.assertTrue(self_fit)

    def test_no_directions_raises(self):
        with self.assertRaises(ValueError):
            sk.choose_direction_split([], "dev")

    def test_prefix_used_one_direction_for_every_row(self):
        """The pre-fix loop takes the first existing file and never consults row['split']."""
        snippet = prefix_snippet("payload = None", 'raise SystemExit(f"no directions_fit')
        ns = {
            "os": types.SimpleNamespace(path=types.SimpleNamespace(
                join=os.path.join, exists=lambda p: True)),
            "torch": types.SimpleNamespace(load=lambda p, **kw: {"path": p}),
            "args": types.SimpleNamespace(fit_dir="/fit"),
            "run": types.SimpleNamespace(note=lambda **kw: None),
            "SystemExit": SystemExit,
        }
        exec(snippet, ns)
        self.assertTrue(ns["payload"]["path"].endswith("directions_fit_dev.pt"))
        self.assertEqual(ns["split"], "dev")     # chosen once, before any row is seen
        # A dev row scored with the dev fit is in-sample; the fix returns heldout instead.
        self.assertEqual(sk.choose_direction_split(["dev", "heldout"], "dev")[0], "heldout")


class TestFamilySelection(unittest.TestCase):
    """T7b: --n-families counts families, and the sample is round-robin over domains."""

    def test_counts_families_not_prompts(self):
        sel, acct = sk.select_families(fake_rows(), 6)
        self.assertEqual(acct["n_families_selected"], 6)
        self.assertEqual(acct["effective_G"], 6)
        self.assertEqual(len({r["family_id"] for r in sel}), 6)
        self.assertEqual(len(sel), 12)           # 6 families x 2 example-counts

    def test_spans_domains(self):
        _, acct = sk.select_families(fake_rows(), 4)
        self.assertEqual(acct["n_domains_selected"], 4)
        self.assertEqual(sorted(acct["families_per_domain"]),
                         ["aviation", "biology", "chemistry", "diving"])

    def test_accounting_records_the_old_behaviour(self):
        _, acct = sk.select_families(fake_rows(), 6)
        self.assertEqual(acct["prior_head_truncation_would_give"],
                         {"n_rows": 6, "n_families": 3, "n_domains": 1})
        self.assertEqual(acct["selection"], "round_robin_over_domains_split_balanced")
        self.assertEqual(acct["requested_n_families"], 6)
        self.assertEqual(acct["n_families_eligible"], 12)

    def test_request_larger_than_pool_is_clamped(self):
        rows = fake_rows()
        sel, acct = sk.select_families(rows, 999)
        self.assertEqual(acct["n_families_selected"], 12)
        self.assertEqual(len(sel), len(rows))

    def test_prefix_head_truncation(self):
        rows = fake_rows()
        snippet = prefix_snippet("rows = [r for r in read_jsonl(args.bank)", "[:args.n_families]")
        ns = {
            "read_jsonl": lambda p: rows,
            "args": types.SimpleNamespace(bank="b", query_kind="q", condition="c", n_families=6),
            "want_n": {4, 8},
        }
        for r in rows:
            r.update(query_kind="q", condition="c", bank_block="core2x2")
        exec(snippet, ns)
        old = ns["rows"]
        self.assertEqual(len(old), 6)                                    # 6 PROMPTS
        self.assertEqual(len({r["family_id"] for r in old}), 3)          # only 3 families
        self.assertEqual(len({r["domain"] for r in old}), 1)             # from 1 domain
        new, acct = sk.select_families(rows, 6)
        self.assertEqual(acct["n_families_selected"], 6)
        self.assertGreater(acct["n_domains_selected"], 1)


class TestSplitBalance(unittest.TestCase):
    """The regression the T7b fix ITSELF introduced: domain round-robin collapsed the split.

    `bank_shaped_rows` reproduces the real eligible pool for every reported G3 run
    (query_kind=semantic_one_word, condition=natural_doublespeak, bank_block=core2x2,
    n_examples=4), whose shape was recomputed from the bank on 2026-08-18: 12 rows, 12
    distinct families, 6 domains, exactly one dev and one heldout family per domain, and the
    dev family sorting first alphabetically in all six. That last property is what made the
    first fix's `by_dom[d].pop(0)` return 6 dev families and 0 heldout.
    """

    @staticmethod
    def bank_shaped_rows():
        rows = []
        for dom in ("aviation", "biology", "chemistry", "diving", "electrical", "forestry"):
            for split in ("dev", "heldout"):           # "dev" < "heldout", so dev sorts first
                rows.append({"family_id": f"{dom}_{split}_fam", "domain": dom,
                             "n_examples": 4, "split": split, "concept": "C", "codeword": "W",
                             "prompt_id": f"{dom}_{split}"})
        return rows

    def test_fix_keeps_both_splits(self):
        sel, acct = sk.select_families(self.bank_shaped_rows(), 6)
        self.assertEqual(acct["n_families_selected"], 6)
        self.assertEqual(acct["n_domains_selected"], 6)      # domain stratification kept ...
        self.assertEqual(acct["rows_per_split"], {"dev": 3, "heldout": 3})   # ... and split too
        self.assertEqual(sorted(acct["families_per_split"]), ["dev", "heldout"])
        self.assertEqual(len(sel), 6)

    def test_naive_pop0_round_robin_would_have_collapsed_to_one_split(self):
        """Runs the first fix's own rule and shows it returns an all-dev sample."""
        rows = self.bank_shaped_rows()
        by_family = {}
        for r in rows:
            by_family.setdefault(r["family_id"], []).append(r)
        by_dom = {}
        for fam in sorted(by_family):
            by_dom.setdefault(by_family[fam][0]["domain"], []).append(fam)
        doms = sorted(by_dom)
        fams, i = [], 0
        while len(fams) < 6:                      # verbatim: by_dom[d].pop(0)
            d = doms[i % len(doms)]
            if by_dom[d]:
                fams.append(by_dom[d].pop(0))
            i += 1
        naive_splits = collections.Counter(by_family[f][0]["split"] for f in fams)
        self.assertEqual(dict(naive_splits), {"dev": 6})       # zero heldout families
        _, acct = sk.select_families(rows, 6)
        self.assertEqual(acct["rows_per_split"], {"dev": 3, "heldout": 3})

    def test_prefix_head_truncation_clumped_domains_not_splits(self):
        """The ORIGINAL defect on this shape: splits were fine, domains were not."""
        rows = self.bank_shaped_rows()
        head = rows[:6]
        self.assertEqual(len({r["domain"] for r in head}), 3)      # 3 of 6 domains
        self.assertEqual(dict(collections.Counter(r["split"] for r in head)),
                         {"dev": 3, "heldout": 3})                 # but split WAS balanced
        _, acct = sk.select_families(rows, 6)
        self.assertEqual(acct["n_domains_selected"], 6)
        self.assertEqual(acct["prior_head_truncation_would_give"]["n_domains"], 3)
        self.assertEqual(acct["prior_head_truncation_would_give_splits"],
                         {"dev": 3, "heldout": 3})

    def test_head_truncation_already_counted_families_correctly_here(self):
        """Refutes T7b claim (b): family_id is 1:1 with rows, so rows[:6] gave 6 families."""
        rows = self.bank_shaped_rows()
        _, acct = sk.select_families(rows, 6)
        self.assertEqual(acct["n_families_eligible"], 12)
        self.assertEqual(acct["prior_head_truncation_would_give"],
                         {"n_rows": 6, "n_families": 6, "n_domains": 3})

    def test_shared_concept_codeword_is_recorded(self):
        _, acct = sk.select_families(self.bank_shaped_rows(), 6)
        self.assertEqual(acct["effective_G"], 6)
        # ... but all six clusters share one semantic pair, so G=6 is an upper bound.
        self.assertEqual(acct["n_concept_codeword_pairs"], 1)


if __name__ == "__main__":
    unittest.main()


# ===========================================================================
# 2026-08-19 — CORRECTION C-6 (the readout) and the END-TO-END verification of
# T3/T7 that the 2026-08-18 fix never had.
#
# WHY A HARNESS AND NOT MORE UNIT TESTS. Everything above tests the PURE helpers
# `choose_destinations` / `choose_direction_split` / `select_families`. Those tests
# pass whether or not `main()` calls them, and whether or not it passes them to the
# ranking path — which is precisely this project's most repeated bug shape (fix
# applied to one of two paths: five occurrences, most recently R-12). The continuation
# log therefore recorded T3 as "code fixed, UNVERIFIED".
#
# `run_main()` below drives the module's ACTUAL `main()` with stubs (no GPU, no model,
# no torch forward) and captures the `dst` that reaches `dominance_at` — the ranking
# call itself — plus the `query_positions` that reach `AttentionKnockout` and the
# context string that reaches the readout. The same harness is then run against TWO
# immutable pre-fix blobs, so each claim is measured against the defective bytes
# rather than argued from the diff.
# ===========================================================================

import importlib.util                                                  # noqa: E402
import tempfile                                                        # noqa: E402
from unittest import mock                                              # noqa: E402

import torch                                                           # noqa: E402

# Baseline #2: the file as committed at 547ce76f — AFTER the T3/T3b/T7/T7b fix and
# BEFORE C-6. This is the version whose G3 numbers stand in the report: it ranks at
# the last PROMPT token with the single-next-token readout and no answer prefix.
PREFIX_BLOB_C6 = "547ce76f0ee8ea31c231dc4772cc303534cb7d31"
PREFIX_C6_MARKERS = (
    "val = semantic_logodds(lm, ids, c_ids, w_ids)",       # the invalid instrument
    "query_positions=dsts,",                               # no answer window
    'rows[0]["concept"]',                                  # readout ids from example[0]
    "readout_pos = len(ids) - 1",                          # readout at the prompt's end
)

# ---------------------------------------------------------------- synthetic prompt
# A char-level tokenizer makes every token index a character index, so the fixture's
# positions are readable and the prefix property (tok(a+b)[:len(tok(a))] == tok(a))
# holds by construction — which is what lets the harness assert on exact positions.
DEMO_BLOCK = "aaa bbb ccc"                       # chars 0..10
TEMPLATED = DEMO_BLOCK + " ddd eee fff ggg hhh iii jjj kkk"
PROMPT_LEN = len(TEMPLATED)                      # 43
CODEWORD_LAST = 34                               # the final codeword occurrence
ANSWER_PREFIX = "Answer:"                        # 7 chars
CTX_LEN = PROMPT_LEN + len(ANSWER_PREFIX)        # 50
READOUT_POS = CTX_LEN - 1                        # 49 -- the position C-6 reads at
PRE_C6_DST = PROMPT_LEN - 1                      # 42 -- where 547ce76f ranked
assert (PROMPT_LEN, READOUT_POS, PRE_C6_DST) == (43, 49, 42)
# Row p0's options are "bomb"/"watch" -> longest variant " Watch" is 6 chars; p1's are
# "bug"/"wasp" -> 5. The answer window is therefore per row, which is the point.
WINDOW = {"p0": [CODEWORD_LAST] + list(range(READOUT_POS, READOUT_POS + 6)),
          "p1": [CODEWORD_LAST] + list(range(READOUT_POS, READOUT_POS + 5))}


class FakeTok:
    pad_token_id = 0
    eos_token_id = 0

    def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
        out = {"input_ids": [ord(c) for c in text]}
        if return_offsets_mapping:
            out["offset_mapping"] = [(i, i + 1) for i in range(len(text))]
        return out


class FakeModel:
    device = "cpu"
    config = types.SimpleNamespace(num_attention_heads=2)
    # VERIFIER FIX 2026-08-19 (defect V-2). `Recorder.legacy_readouts` was initialised to 0 and
    # NEVER INCREMENTED, so `assertEqual(rec.legacy_readouts, 0)` was 0 == 0 in every test that
    # made it -- a dead assertion of exactly the shape this project has shipped five times, sitting
    # inside the file whose job is to prove the legacy instrument is gone. The counter is now
    # driven by the only thing that reaches a forward pass in this harness: `semantic_logodds`.
    # `dominance_at` and `AttentionKnockout` are stubbed out, so a call here is a legacy readout
    # and nothing else.
    _rec = None

    def __call__(self, input_ids=None, use_cache=False, **kw):
        if self._rec is not None:
            self._rec.legacy_readouts += 1
        t = input_ids
        v = torch.zeros(1, t.shape[1], 256)
        v[0, -1, ord("b")] = 3.0                 # concept id
        v[0, -1, ord("w")] = 1.0                 # codeword id
        return types.SimpleNamespace(logits=v)


class FakeLM:
    model_id = "meta-llama/Llama-3.1-8B-Instruct"
    revision = "rev0"
    dtype = "float32"
    num_layers = 4

    def __init__(self):
        self.model = FakeModel()
        self.tokenizer = FakeTok()


class FakeDC:
    PRIMARY_MODEL = "meta-llama/Llama-3.1-8B-Instruct"
    # Set by make_fake_dc(); a bare FakeDC (used by the override tests) simply counts nothing.
    REC = None

    def load_model(self, *a, **kw):
        lm = FakeLM()
        lm.model._rec = self.REC
        return lm

    def apply_template(self, tok, text, **kw):
        return text


def make_fake_dc(rec, base=FakeDC):
    """A DC whose model forwards are counted on `rec` (see FakeModel, defect V-2)."""
    return type("RecordingDC", (base,), {"REC": rec})


class Recorder:
    """Everything the harness observes about one `main()` call."""

    def __init__(self):
        self.dominance_dsts = []
        self.knockouts = []          # (layer, query_positions, blocked_keys, heads)
        self.readout_contexts = []   # ctx string handed to string_option_readout
        self.legacy_readouts = 0     # forward passes through the pre-C-6 instrument
        self.variant_words = []      # every word answer_variants() was asked for
        self.rows = []
        self.summary = None
        self.notes = {}


def make_fake_pc(rec):
    class FakeKnockout:
        def __init__(self, model, layer_idxs, query_positions, blocked_keys, heads=None):
            rec.knockouts.append((list(layer_idxs), list(query_positions),
                                  list(blocked_keys), None if heads is None else list(heads)))

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    return types.SimpleNamespace(AttentionKnockout=FakeKnockout)


def make_fake_sg(rec, option_mass=0.4):
    def readout_id_pair(tok, concept, codeword, mode=None):
        return [ord(concept[0])], [ord(codeword[0])], {"mode": mode}

    def answer_variants(word, spaced=True):
        rec.variant_words.append(word)
        return [" " + word, " " + word[:1].upper() + word[1:]]

    def string_option_readout(lm, context, options, max_batch=16):
        rec.readout_contexts.append((context, max_batch))
        return {"logp_concept": -1.0, "logp_codeword": -2.0,
                "p_concept": 0.36, "p_codeword": 0.13,
                "n_variants_concept": 2, "n_variants_codeword": 2,
                "option_mass": option_mass, "top1_id": 7}

    return types.SimpleNamespace(readout_id_pair=readout_id_pair,
                                 answer_variants=answer_variants,
                                 string_option_readout=string_option_readout)


def make_fake_run(rec):
    class FakeRun:
        path = "/dev/null/fake_run"

        def __init__(self, *a, **kw):
            pass

        def p(self, *parts):
            return os.path.join(self.path, *parts)

        def note(self, **kw):
            rec.notes.update(kw)

        def note_bank(self, *a, **kw):
            pass

        def note_model(self, *a, **kw):
            pass

        def log_row(self, row):
            rec.rows.append(dict(row))

        def finish(self, summary=None, ledger=None):
            rec.summary = dict(summary or {})
            rec.summary["_ledger"] = ledger.as_dict() if ledger is not None else None

    return FakeRun


def bank_rows(demo_block=DEMO_BLOCK):
    """Two domains x one family, and TWO DISTINCT (concept, codeword) pairs."""
    out = []
    for i, (dom, split, concept, codeword) in enumerate(
            [("aviation", "dev", "bomb", "watch"), ("biology", "heldout", "bug", "wasp")]):
        out.append({
            "prompt_id": f"p{i}", "prompt_sha16": f"s{i}", "family_id": f"{dom}_fam",
            "condition": "natural_doublespeak", "cell": "C", "domain": dom, "split": split,
            "n_examples": 4, "query_kind": "semantic_one_word", "bank_block": "core2x2",
            "concept": concept, "codeword": codeword, "demo_block": demo_block,
            "full_prompt": TEMPLATED, "final_query_text": TEMPLATED[12:],
            "target_surface": "kkk", "n_target_occurrences": 2,
        })
    return out


def load_prefix_module(blob: str, markers: Sequence[str]):
    """Import a pre-fix blob as a live module (verified pre-fix) so main() can be RUN."""
    src = subprocess.check_output(["git", "cat-file", "blob", blob], cwd=REPO).decode()
    missing = [m for m in markers if m not in src]
    assert not missing, f"blob {blob} is not the intended baseline; missing {missing!r}"
    d = tempfile.mkdtemp()
    path = os.path.join(d, "prefix_sk.py")
    with open(path, "w") as f:
        f.write(src)
    spec = importlib.util.spec_from_file_location("prefix_sk_" + blob[:8], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_main(module, argv_extra=(), rows=None, option_mass=0.4, demo_block=DEMO_BLOCK,
             overrides=None):
    """Drive `module.main()` end to end with stubs. Returns (rc, Recorder).

    `overrides` replaces one of the stubs by NAME, so a caller can swap in a broken
    tokenizer or an unresolvable row. Patching from outside would be silently undone
    by the `mock.patch.object` calls below -- which is itself the one-of-two-paths
    shape, and it produced two green-looking failures the first time this ran.
    """
    rec = Recorder()
    rows = bank_rows(demo_block) if rows is None else rows

    def fake_resolve(dc, tok, row, *a, **kw):
        ids = tok(row["full_prompt"])["input_ids"]
        return row["full_prompt"], ids, [2, CODEWORD_LAST], [], []

    def fake_dominance(lm, ids, dst, layers, direction=None, check_invariants=True):
        rec.dominance_dsts.append(dst)
        n = len(ids)
        return {"D_dir": {L: torch.arange(2 * n, dtype=torch.float32).reshape(2, n)
                          for L in layers}}

    payload = {"d_surface": {L: torch.ones(8) for L in range(4)},
               "layers": list(range(4)),
               "meta": {"position": "codeword_last", "split_fitted_on": "dev",
                        "model": "meta-llama/Llama-3.1-8B-Instruct"}}

    real_exists = os.path.exists

    def fake_exists(p):
        return True if str(p).endswith(".pt") else real_exists(p)

    argv = ["surgical_knockout.py", "--fit-dir", "/fit", "--layers", "0,1", "--topk", "2",
            "--n-families", "2", "--n-examples", "4", "--dst", "both",
            "--demo-scope", "block", *argv_extra]

    stubs = {"ds": lambda: make_fake_dc(rec)(), "pair": lambda: make_fake_pc(rec),
             "read_jsonl": lambda p: rows, "RunDir": make_fake_run(rec),
             "resolve_occurrences": fake_resolve, "dominance_at": fake_dominance,
             "sg": make_fake_sg(rec, option_mass)}
    stubs.update(overrides or {})

    with contextlib.ExitStack() as st:
        for name, obj in stubs.items():
            st.enter_context(mock.patch.object(module, name, obj))
        st.enter_context(mock.patch.object(module.torch, "load", lambda *a, **kw: payload))
        st.enter_context(mock.patch("os.path.exists", fake_exists))
        st.enter_context(mock.patch.object(sys, "argv", argv))
        rc = module.main()
    return rc, rec


class TestRankingPathEndToEnd(unittest.TestCase):
    """T3, VERIFIED AT LAST: the destination that reaches `dominance_at` is the readout.

    The 2026-08-18 fix was recorded as UNVERIFIED because the only evidence was a unit
    test of `choose_destinations`. These cases assert on the argument the RANKING CALL
    actually received, and contrast it with the same harness run against both pre-fix
    blobs.
    """

    def test_ranking_dst_is_the_true_readout_position(self):
        rc, rec = run_main(sk)
        self.assertEqual(rc, 0)
        # ctx = 40 prompt chars + "Answer:" -> the scored position is 46, not 39, not 34.
        self.assertEqual(set(rec.dominance_dsts), {READOUT_POS})
        self.assertEqual(set(rec.dominance_dsts), {49})
        self.assertNotIn(CODEWORD_LAST, rec.dominance_dsts)   # T3's retracted destination
        self.assertNotIn(PRE_C6_DST, rec.dominance_dsts)      # the pre-C-6 destination

    def test_prefix_T3_blob_ranked_at_the_codeword(self):
        """The bytes retraction #3 was declared for, RUN: dst == the codeword position."""
        old = load_prefix_module(PREFIX_BLOB, PREFIX_MARKERS)
        rc, rec = run_main(old)
        self.assertEqual(rc, 0)
        self.assertEqual(set(rec.dominance_dsts), {CODEWORD_LAST})
        # V-2: this counter is real now, and the pre-fix blob is the case that makes it non-zero.
        # 12 arms x 2 prompts, all through `semantic_logodds`; the fixed module must score 0 here.
        self.assertEqual(rec.legacy_readouts, 24)
        _, new = run_main(sk)
        self.assertEqual(new.legacy_readouts, 0)
        self.assertNotEqual(set(rec.dominance_dsts), set(new.dominance_dsts))

    def test_prefix_C6_blob_ranked_at_the_last_PROMPT_token(self):
        """Post-T3, pre-C-6: ranking moved to the readout, but the readout itself was wrong."""
        old = load_prefix_module(PREFIX_BLOB_C6, PREFIX_C6_MARKERS)
        rc, rec = run_main(old)
        self.assertEqual(rc, 0)
        self.assertEqual(set(rec.dominance_dsts), {PRE_C6_DST})            # 42
        self.assertEqual(rec.readout_contexts, [])   # never calls string_option_readout
        self.assertEqual(rec.legacy_readouts, 24)    # every arm went through the legacy forward
        _, new = run_main(sk)
        self.assertEqual(set(new.dominance_dsts), {READOUT_POS})           # 49

    def test_demo_source_bound_is_the_last_destination_in_the_live_path(self):
        _, rec = run_main(sk)
        # The block is chars 0..10 and the last destination is 46, so nothing is dropped;
        # the accounting says so explicitly instead of leaving it to be inferred.
        self.assertEqual(rec.rows[0]["n_demo_positions"], len(DEMO_BLOCK))
        self.assertEqual(rec.summary["source_truncation"]["example_prompt_ids"], [])

    def test_sources_after_the_last_destination_are_counted_not_dropped_silently(self):
        """--dst codeword bounds sources at 34, so a block spanning 20..37 loses 4 tokens."""
        long_block = TEMPLATED[20:38]
        rc, rec = run_main(sk, argv_extra=["--dst", "codeword"],
                           rows=bank_rows(long_block), demo_block=long_block)
        self.assertEqual(rc, 0)
        self.assertEqual(rec.rows[0]["n_demo_positions"], CODEWORD_LAST - 20)     # 14 of 18
        self.assertEqual(rec.summary["source_truncation"]["n_demo_tokens_after_last_dst"],
                         (38 - CODEWORD_LAST) * 2)                                # 4 per row
        self.assertEqual(rec.summary["source_truncation"]["n_rows_truncated"], 2)
        self.assertEqual(len(rec.summary["source_truncation"]["example_prompt_ids"]), 2)


class TestWholeAnswerReadoutPort(unittest.TestCase):
    """C-6: the readout is `signals.string_option_readout`, called as score_behavior calls it."""

    def test_every_arm_is_scored_through_string_option_readout(self):
        _, rec = run_main(sk)
        self.assertTrue(rec.readout_contexts)
        self.assertEqual(rec.legacy_readouts, 0)
        for ctx, max_batch in rec.readout_contexts:
            self.assertTrue(ctx.endswith(ANSWER_PREFIX), ctx[-12:])
            # batch>1 raises NotImplementedError inside AttentionKnockout: load-bearing.
            self.assertEqual(max_batch, 1)
        # one readout per logged row (12 arms x 2 prompts)
        self.assertEqual(len(rec.readout_contexts), len(rec.rows))

    def test_every_row_carries_option_mass_and_the_mode(self):
        _, rec = run_main(sk)
        for r in rec.rows:
            self.assertIn("option_mass", r)
            self.assertEqual(r["readout_mode"], "whole_answer")
            self.assertEqual(r["answer_prefix"], ANSWER_PREFIX)
            self.assertEqual(r["ctx_len"], r["prompt_len"] + len(ANSWER_PREFIX))
        self.assertIn("option_mass", rec.summary)
        self.assertEqual(rec.summary["option_mass_gate"], "PASS")
        self.assertTrue(rec.summary["reportable"])

    def test_prefix_C6_blob_recorded_no_option_mass_at_all(self):
        old = load_prefix_module(PREFIX_BLOB_C6, PREFIX_C6_MARKERS)
        _, rec = run_main(old)
        self.assertTrue(rec.rows)
        for r in rec.rows:
            self.assertNotIn("option_mass", r)
            self.assertNotIn("readout_mode", r)
        self.assertNotIn("option_mass", rec.summary)

    def test_answer_variants_are_built_PER_ROW_not_from_rows0(self):
        """The example[0] shape: pre-C-6 the id pair came from rows[0] for the whole run."""
        _, rec = run_main(sk)
        self.assertEqual(set(rec.variant_words), {"bomb", "watch", "bug", "wasp"})
        old = load_prefix_module(PREFIX_BLOB_C6, PREFIX_C6_MARKERS)
        _, rec_old = run_main(old)
        self.assertEqual(rec_old.variant_words, [])          # never called at all
        # and its ONE id pair came from rows[0]:
        self.assertEqual(rec_old.notes["readout_ids"], {"mode": None})

    def test_primary_mode_reproduces_the_old_instrument_and_is_not_reportable(self):
        rc, rec = run_main(sk, argv_extra=["--readout-ids", "primary", "--answer-prefix", "none"])
        self.assertEqual(rc, 0)
        self.assertEqual(rec.readout_contexts, [])
        self.assertEqual(rec.legacy_readouts, 24)     # V-2: primary really is the old forward
        self.assertFalse(rec.summary["reportable"])
        self.assertIn("NOT reportable", rec.summary["reportable_note"])
        self.assertEqual(set(rec.dominance_dsts), {PRE_C6_DST})   # no prefix -> 42
        for r in rec.rows:
            self.assertIsNone(r["option_mass"])


class TestKnockoutQueryWindow(unittest.TestCase):
    """C-6b: the cut must cover every position the whole-answer readout reads."""

    def test_query_positions_span_the_answer_window(self):
        _, rec = run_main(sk)
        self.assertTrue(rec.knockouts)
        seen = {tuple(qp) for _, qp, _, _ in rec.knockouts}
        self.assertEqual(seen, {tuple(WINDOW["p0"]), tuple(WINDOW["p1"])})
        for qp in seen:
            self.assertEqual(qp[:2], (CODEWORD_LAST, READOUT_POS))
            self.assertGreater(len(qp), 2, "answer tokens are not in the knockout query set")
        by_id = {r["prompt_id"]: r["query_positions"] for r in rec.rows}
        self.assertEqual(by_id, WINDOW)

    def test_prefix_C6_blob_cut_only_two_positions(self):
        old = load_prefix_module(PREFIX_BLOB_C6, PREFIX_C6_MARKERS)
        _, rec = run_main(old)
        for _, qp, _, _ in rec.knockouts:
            self.assertEqual(qp, [CODEWORD_LAST, PRE_C6_DST])

    def test_window_is_added_by_identity_not_by_mode(self):
        """--dst codeword must stay a faithful reproduction of the retracted behaviour."""
        self.assertEqual(sk.readout_query_positions([34], CTX_LEN, 6), [34])
        self.assertEqual(sk.readout_query_positions([49], 50, 3), [49, 50, 51])
        self.assertEqual(sk.readout_query_positions([34, 49], 50, 2), [34, 49, 50])
        _, rec = run_main(sk, argv_extra=["--dst", "codeword"])
        for _, qp, _, _ in rec.knockouts:
            self.assertEqual(qp, [CODEWORD_LAST])

    def test_bad_ctx_len_raises(self):
        with self.assertRaises(ValueError):
            sk.readout_query_positions([1], 0, 2)


class TestCrossFitInTheLivePath(unittest.TestCase):
    """T7 end to end: the row's ranking direction is the OTHER split's, per row."""

    def test_each_row_is_ranked_with_the_other_splits_fit(self):
        _, rec = run_main(sk)
        got = {(r["prompt_id"], r["split"], r["directions_fitted_on"], r["is_self_fit"])
               for r in rec.rows}
        self.assertEqual(got, {("p0", "dev", "heldout", False),
                               ("p1", "heldout", "dev", False)})

    def test_prefix_blobs_ranked_every_row_with_the_dev_fit(self):
        for blob, markers in ((PREFIX_BLOB, PREFIX_MARKERS),
                              (PREFIX_BLOB_C6, PREFIX_C6_MARKERS)):
            old = load_prefix_module(blob, markers)
            _, rec = run_main(old)
            fitted_on = {r.get("directions_fitted_on") for r in rec.rows}
            if blob == PREFIX_BLOB:
                # the original never recorded WHICH fit it used -- that is half the defect
                self.assertEqual(fitted_on, {None})
            else:
                self.assertEqual(fitted_on, {"dev", "heldout"})


class TestOptionMassGate(unittest.TestCase):
    """C-6's gate: fatal on the BASELINE arm only, and never vacuous."""

    def test_baseline_below_threshold_is_fatal(self):
        summary, fatal = sk.option_mass_gate({"none": [1e-5, 2e-5, 3e-5]}, 0.05)
        self.assertEqual(len(fatal), 1)
        self.assertFalse(summary["none"]["reportable"])
        self.assertTrue(summary["none"]["gates_the_run"])

    def test_intervention_arm_collapse_is_a_result_not_a_gate_failure(self):
        summary, fatal = sk.option_mass_gate(
            {"none": [0.4, 0.5, 0.6], "positive_control": [1e-9, 1e-9, 1e-9]}, 0.05)
        self.assertEqual(fatal, [])
        self.assertFalse(summary["positive_control"]["reportable"])
        self.assertFalse(summary["positive_control"]["gates_the_run"])
        self.assertTrue(summary["none"]["reportable"])

    def test_a_gate_with_no_baseline_arm_FAILS_rather_than_passing(self):
        """The dead-guard shape: five of this project's guards passed by never running."""
        summary, fatal = sk.option_mass_gate({"topk_demo": [0.4]}, 0.05)
        self.assertEqual(len(fatal), 1)
        self.assertIn("never evaluated", fatal[0])
        self.assertNotIn("none", summary)

    def test_a_NaN_median_on_the_gating_arm_is_fatal_not_a_pass(self):
        """V-3, the NaN short circuit: `>=` and `<` are not complements.

        Pre-fix `reportable = med >= min_mass` was False AND `med < min_mass` was False, so the
        per-arm verdict said NOT reportable while `fatal` came back empty and the run-level
        verdict said PASS / reportable: true. One statistic, two contradictory answers, the
        permissive one deciding — the dead-guard shape.
        """
        nan = float("nan")
        summary, fatal = sk.option_mass_gate({"none": [nan, nan, nan]}, 0.05)
        self.assertEqual(len(fatal), 1)
        self.assertIn("non-finite", fatal[0])
        self.assertNotIn("none", summary)      # no median can be quoted from nothing finite

    def test_one_NaN_among_good_masses_still_fails_the_gating_arm(self):
        """A single unusable value is not averaged away: the arm stops being reportable."""
        summary, fatal = sk.option_mass_gate({"none": [0.4, 0.5, float("nan")]}, 0.05)
        self.assertEqual(summary["none"]["n_nonfinite"], 1)
        self.assertFalse(summary["none"]["reportable"])
        self.assertEqual(len(fatal), 1)
        # ... and the per-arm verdict and the run-level verdict now agree, which is the fix.
        self.assertEqual(summary["none"]["reportable"], not fatal)

    def test_a_NaN_on_an_intervention_arm_is_recorded_but_not_fatal(self):
        summary, fatal = sk.option_mass_gate(
            {"none": [0.4, 0.5, 0.6], "topk_demo": [float("nan"), 0.4, 0.5]}, 0.05)
        self.assertEqual(fatal, [])
        self.assertFalse(summary["topk_demo"]["reportable"])
        self.assertEqual(summary["topk_demo"]["n_nonfinite"], 1)

    def test_all_none_masses_do_not_silently_pass(self):
        summary, fatal = sk.option_mass_gate({"none": [None, None]}, 0.05)
        self.assertEqual(summary, {})
        self.assertEqual(len(fatal), 1)

    def test_main_exits_4_when_the_baseline_readout_is_a_tail(self):
        rc, rec = run_main(sk, option_mass=1e-5)
        self.assertEqual(rc, 4)
        self.assertIn("NOT REPORTABLE", rec.summary["option_mass_gate"])
        self.assertFalse(rec.summary["reportable"])
        # the evidence is still written: the gate fires AFTER finish()
        self.assertEqual(len(rec.rows), 24)
        self.assertIsNotNone(rec.summary["_ledger"])

    def test_allow_tail_readout_exits_0_but_stays_not_reportable(self):
        rc, rec = run_main(sk, argv_extra=["--allow-tail-readout"], option_mass=1e-5)
        self.assertEqual(rc, 0)
        self.assertFalse(rec.summary["reportable"])


class TestArmCoverageGate(unittest.TestCase):
    """V-4: the mass gate watches the INSTRUMENT; nothing watched the INTERVENTION."""

    @staticmethod
    def _pc_that_refuses(exc):
        class K:
            def __init__(self, *a, **kw):
                raise exc

        return types.SimpleNamespace(AttentionKnockout=K)

    def test_a_run_where_the_knockout_never_fired_is_not_reportable(self):
        """The exact fault C-6 newly exposes: a 4-D-mask RuntimeError in AttentionKnockout.

        Pre-fix this finished rc=0 with `option_mass_gate: PASS` and `reportable: true` while
        carrying rows for `none` and `no_demo_text` ONLY — the two arms that never enter the
        knockout — i.e. a directory that looks like a clean G3 run and contains no attention
        evidence at all.
        """
        rc, rec = run_main(sk, overrides={
            "pair": lambda: self._pc_that_refuses(
                RuntimeError("expected a 4-D additive attention mask"))})
        self.assertEqual(rc, 4)
        self.assertFalse(rec.summary["reportable"])
        self.assertEqual({r["arm"] for r in rec.rows}, {"none", "no_demo_text"})
        self.assertEqual(rec.summary["arm_coverage"]["cutting_arms_with_rows"], [])
        self.assertTrue(rec.summary["arm_coverage"]["verdict"].startswith("FAILED"))
        self.assertIn("CUTS ATTENTION EDGES", rec.summary["reportable_note"])
        # the option-mass gate itself still PASSES: the instrument was healthy, the
        # intervention was not, and conflating the two is what let this through.
        self.assertEqual(rec.summary["option_mass_gate"], "PASS")

    def test_batch_gt_1_NotImplementedError_is_caught_by_the_same_gate(self):
        rc, rec = run_main(sk, overrides={
            "pair": lambda: self._pc_that_refuses(
                NotImplementedError("AttentionKnockout supports batch size 1 only"))})
        self.assertEqual(rc, 4)
        self.assertFalse(rec.summary["reportable"])

    def test_allow_tail_readout_cannot_wave_through_a_knockout_that_never_ran(self):
        """There is no deliberate version of 'the intervention did not happen'."""
        rc, rec = run_main(sk, argv_extra=["--allow-tail-readout"], overrides={
            "pair": lambda: self._pc_that_refuses(RuntimeError("boom"))})
        self.assertEqual(rc, 4)
        self.assertFalse(rec.summary["reportable"])

    def test_a_healthy_run_passes_coverage_and_names_every_arm(self):
        _, rec = run_main(sk)
        cov = rec.summary["arm_coverage"]
        self.assertEqual(cov["verdict"], "PASS")
        self.assertEqual(sorted(cov["rows_by_arm"]), sorted(sk.ARMS))
        self.assertEqual(cov["cutting_arms_with_rows"],
                         sorted(set(sk.ARMS) - {"none", "no_demo_text"}))
        self.assertTrue(all(v == 2 for v in cov["rows_by_arm"].values()))

    def test_one_dead_arm_alone_does_not_condemn_the_run(self):
        """The gate must not OVER-fire. `dense_two_layer` is legitimately INFEASIBLE on a real
        4-layer-chosen 32-layer run (it raises rather than under-deliver), so a single cutting
        arm with no rows has to stay a PASS — only ALL of them failing means the knockout never
        ran. Reproduced here by starving that one arm of edges, which ledgers it as
        `arm_dense_two_layer:no_edges`."""
        real_pick = sk.pick_edges

        def starve_one(D_dir, demo_positions, all_positions, k, arm, rng, **kw):
            if arm == "dense_two_layer":
                return {}
            return real_pick(D_dir, demo_positions, all_positions, k, arm, rng, **kw)

        rc, rec = run_main(sk, overrides={"pick_edges": starve_one})
        cov = rec.summary["arm_coverage"]
        self.assertEqual(cov["rows_by_arm"]["dense_two_layer"], 0)
        self.assertNotIn("dense_two_layer", cov["cutting_arms_with_rows"])
        self.assertEqual(cov["verdict"], "PASS")
        self.assertEqual(rc, 0)
        self.assertTrue(rec.summary["reportable"])
        self.assertEqual(
            rec.summary["_ledger"]["failure_reasons"]["arm_dense_two_layer:no_edges"], 2)


class TestAnswerPrefixGuards(unittest.TestCase):
    """The absolute-position-index bug class, pre-empted."""

    def test_prefix_that_disturbs_a_prompt_token_is_refused_not_silently_shifted(self):
        class MergingTok(FakeTok):
            def __call__(self, text, add_special_tokens=False, return_offsets_mapping=False):
                out = super().__call__(text, add_special_tokens, return_offsets_mapping)
                if text.endswith(ANSWER_PREFIX):        # a merge across the join
                    out["input_ids"] = [0] + out["input_ids"][1:]
                return out

        class MergingLM(FakeLM):
            def __init__(self):
                super().__init__()
                self.tokenizer = MergingTok()

        class MergingDC(FakeDC):
            def load_model(self, *a, **kw):
                return MergingLM()

        rc, rec = run_main(sk, overrides={"ds": lambda: MergingDC()})
        self.assertEqual(rec.rows, [])
        reasons = rec.summary["_ledger"]["failure_reasons"]
        self.assertEqual(reasons.get("answer_prefix_retokenizes_prompt"), 2)

    def test_shell_safe_empty_prefix(self):
        for raw in ("", "none", "NONE", "''", '""', " none "):
            self.assertEqual(sk.normalize_answer_prefix(raw), "")
        self.assertEqual(sk.normalize_answer_prefix("Answer:"), "Answer:")

    @staticmethod
    def _sg_that_refuses(rec, bad_codeword):
        """A signals stub whose `readout_id_pair` raises exactly as the real one does.

        `signals.readout_ids` raises ValueError for any word whose leading-space form is not a
        single token (' Carrot' -> [' Car', 'rot'] is the repo's own example), and
        `readout_id_pair` raises when the two options share an id. Neither is hypothetical: the
        C-6 patch moved that call from ONE start-up invocation on rows[0] into the per-row loop
        precisely because a second (concept, codeword) pair is expected.
        """
        base = make_fake_sg(rec)

        def readout_id_pair(tok, concept, codeword, mode=None):
            if codeword == bad_codeword:
                raise ValueError(f"readout_ids({codeword!r}): ' {codeword}' tokenizes to 2 "
                                 f"tokens, not 1.")
            return [ord(concept[0])], [ord(codeword[0])], {"mode": mode}

        return types.SimpleNamespace(readout_id_pair=readout_id_pair,
                                     answer_variants=base.answer_variants,
                                     string_option_readout=base.string_option_readout)

    def test_unbuildable_readout_ids_are_ledgered_not_a_mid_run_abort(self):
        """V-1: a bad (concept, codeword) pair must cost one ROW, not the whole run.

        Pre-fix this raised an uncaught ValueError out of `main()` AFTER the run directory
        existed: no summary.json, no DONE.json, no FailureLedger, and every already-completed
        row's forward passes thrown away -- the shape of the abandoned blockscope run dir.
        """
        rec = Recorder()
        rc, rec2 = run_main(sk, overrides={"sg": self._sg_that_refuses(rec, "wasp")})
        # p0 (bomb/watch) survives; p1 (bug/wasp) is charged, by prompt_id, with a reason.
        self.assertEqual({r["prompt_id"] for r in rec2.rows}, {"p0"})
        led = rec2.summary["_ledger"]
        reasons = led["failure_reasons"]
        key = ("readout_ids:ValueError:"
               + "readout_ids('wasp'): ' wasp' tokenizes to 2 tokens, not 1."[:60])
        self.assertEqual([k for k in reasons if k.startswith("readout_ids:")], [key])
        self.assertEqual(reasons[key], 1)
        self.assertEqual(led["failure_example_ids"][key], ["p1"])   # ids only, never text

    def test_a_bad_pair_on_rows0_is_also_ledgered_not_fatal(self):
        """The one-of-two-paths half: rows[0] goes through a SECOND call, before the loop."""
        rec = Recorder()
        rc, rec2 = run_main(sk, overrides={"sg": self._sg_that_refuses(rec, "watch")})
        self.assertEqual({r["prompt_id"] for r in rec2.rows}, {"p1"})   # p0 is the refused one
        self.assertIn("error", rec2.notes["readout_ids"])
        self.assertIsNone(rec2.notes["semantic_variants_first_pair"])
        self.assertEqual(sum(v for k, v in rec2.summary["_ledger"]["failure_reasons"].items()
                             if k.startswith("readout_ids:")), 1)

    def test_row_without_a_resolved_codeword_is_ledgered_not_an_IndexError(self):
        def no_occ(dc, tok, row, *a, **kw):
            return row["full_prompt"], tok(row["full_prompt"])["input_ids"], [], [], []

        rc, rec = run_main(sk, overrides={"resolve_occurrences": no_occ})
        self.assertEqual(rec.rows, [])
        self.assertEqual(rec.summary["_ledger"]["failure_reasons"]["no_codeword_occurrence"], 2)
