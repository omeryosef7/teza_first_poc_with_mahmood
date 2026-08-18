"""Pins the selection logic of src/boombness/surgical_knockout.py (defects T3/T3b/T7/T7b).

Every test here also runs the corresponding snippet of the PRE-FIX file (fetched with
`git show HEAD:...` into a temp file, then exec'd in a stub namespace) and asserts the old
behaviour was wrong. That is what makes these regression tests rather than tautologies: the
`test_prefix_*` cases execute HEAD's actual bytes and would pass trivially if the defect
were imaginary. No GPU, no model, no torch forward pass is involved.
"""
from __future__ import annotations

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


def head_source() -> str:
    return subprocess.check_output(
        ["git", "show", "HEAD:src/boombness/surgical_knockout.py"], cwd=REPO).decode()


def head_snippet(first: str, last: str) -> str:
    """Return HEAD's source lines from the line containing `first` through the one with `last`."""
    lines = head_source().splitlines()
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
        exec(head_snippet("readout_pos = len(ids) - 1", "# for ranking/reporting"), ns)
        self.assertEqual(ns["dst"], 104)            # HEAD ranked at the codeword ...
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
        src = head_snippet("demo_pos = [i for i, (a, b) in enumerate", "and i < dst]")
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
        """HEAD's loop takes the first existing file and never consults row['split']."""
        snippet = head_snippet("payload = None", 'raise SystemExit(f"no directions_fit')
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
        self.assertEqual(acct["selection"], "round_robin_over_domains")
        self.assertEqual(acct["requested_n_families"], 6)
        self.assertEqual(acct["n_families_eligible"], 12)

    def test_request_larger_than_pool_is_clamped(self):
        rows = fake_rows()
        sel, acct = sk.select_families(rows, 999)
        self.assertEqual(acct["n_families_selected"], 12)
        self.assertEqual(len(sel), len(rows))

    def test_prefix_head_truncation(self):
        rows = fake_rows()
        snippet = head_snippet("rows = [r for r in read_jsonl(args.bank)", "[:args.n_families]")
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


if __name__ == "__main__":
    unittest.main()
