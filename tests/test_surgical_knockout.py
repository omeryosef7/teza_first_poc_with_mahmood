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
import os
import subprocess
import sys
import textwrap
import types
import unittest

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
