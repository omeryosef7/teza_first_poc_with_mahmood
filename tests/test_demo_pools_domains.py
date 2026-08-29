"""Guard tests for `demo_pools.generate_pools(domains=...)` and its `--domains` CLI flag.

RBD sprint, 2026-08-29. The flag exists because a confirmatory design needing 12 domains had to
generate all 38, and `lantern` reached only 25/40 benign sentences in `sports_stadium` after 8
rounds -- aborting a run that had already paid for 37 other domains, none of which the experiment
would ever use.

§22 requires, for every research-critical guard: a normal pass test; an EXECUTED mutation test that
makes it fail; a minimum-count assertion so matching zero rows cannot pass; a test that the guard is
WIRED to the production path; and a test that expected-zero counters really exist.

The four properties pinned here:

1.  a subset generates EXACTLY the requested domains, in the requested order;
2.  an unknown / duplicate / empty selection is REFUSED, not silently skipped -- a typo'd domain
    that quietly produced a smaller pools file would be indistinguishable from a deliberate subset;
3.  `domains=None` is byte-identical to the pre-flag behaviour, so every committed pools file still
    regenerates;
4.  the CLI flag actually reaches `generate_pools` -- testing the parser is not testing the wiring.

No network: the OpenAI client and `prepare_demos.gen_demos` are replaced with deterministic fakes,
so these are CPU tests that assert on structure, never on generated text.
"""
from __future__ import annotations

import json
import os
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))

import demo_pools as dp  # noqa: E402


# --------------------------------------------------------------------------- #
# Fakes. `_clean` keeps only sentences containing exactly one whole-word `word`,
# and `_clean_filler` drops any sentence containing a forbidden word, so the
# fake has to satisfy both filters or the real code would raise on a short pool.
# --------------------------------------------------------------------------- #
def _install_fakes(monkeypatch, n_per_pool):
    calls = []

    def fake_gen_demos(client, model, word, n, seed, style_hint=""):
        calls.append({"word": word, "n": n, "seed": seed, "style_hint": style_hint})
        if word == "the":
            # filler: must contain none of concept / codeword / REMAP_SOURCE_WORD
            return [f"Sentence number {i} was logged during the shift." for i in range(n)]
        return [f"Item {i} shows one {word} on the bench." for i in range(n)]

    fake_openai = types.ModuleType("openai")
    fake_openai.OpenAI = lambda api_key=None: object()
    fake_prepare = types.ModuleType("prepare_demos")
    fake_prepare.gen_demos = fake_gen_demos

    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    monkeypatch.setitem(sys.modules, "prepare_demos", fake_prepare)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-a-real-key")
    return calls


TWO = ["hospital_supply", "airport_ground"]


# --------------------------------------------------------------------------- #
# 1. Normal pass, plus the minimum-count assertion (§22.3)
# --------------------------------------------------------------------------- #
def test_a_subset_generates_exactly_those_domains_in_order(monkeypatch):
    _install_fakes(monkeypatch, 2)
    obj = dp.generate_pools("missile", "candle", n_per_pool=2, verbose=False, domains=TWO)

    assert obj["_meta"]["domains"] == TWO, "meta must record the SELECTED domains, not all of them"

    got = sorted({v["domain"] for v in obj["pools"].values()})
    assert got == sorted(TWO)

    # Minimum-count: a subset that produced zero pools must not read as success.
    assert len(obj["pools"]) == len(TWO) * 4, "expected 4 valences (benign, harm, remap, filler)"
    assert len(obj["pools"]) > 0

    for d in TWO:
        for val in ("benign", "harm", "remap", "filler"):
            key = f"{d}|{val}"
            assert key in obj["pools"], f"missing pool {key}"
            assert obj["pools"][key]["n"] == 2


def test_the_subset_is_strictly_smaller_than_the_full_roster(monkeypatch):
    """Anti-vacuity: if DOMAINS ever shrank to 2, test 1 would pass while proving nothing."""
    assert len(dp.DOMAINS) > len(TWO) + 5, "the roster must be materially larger than the subset"
    _install_fakes(monkeypatch, 2)
    obj = dp.generate_pools("missile", "candle", n_per_pool=2, verbose=False, domains=TWO)
    assert len(obj["_meta"]["domains"]) < len(dp.DOMAINS)


def test_order_is_the_callers_order_not_declaration_order(monkeypatch):
    _install_fakes(monkeypatch, 2)
    reversed_two = list(reversed(TWO))
    assert reversed_two != TWO
    obj = dp.generate_pools("missile", "candle", n_per_pool=2, verbose=False,
                            domains=reversed_two)
    assert obj["_meta"]["domains"] == reversed_two


# --------------------------------------------------------------------------- #
# 2. Executed mutation / refusal tests (§22.2)
# --------------------------------------------------------------------------- #
def test_REFUSES_an_unknown_domain(monkeypatch):
    _install_fakes(monkeypatch, 2)
    with pytest.raises(ValueError) as e:
        dp.generate_pools("missile", "candle", n_per_pool=2, verbose=False,
                          domains=["hospital_supply", "no_such_domain"])
    assert "no_such_domain" in str(e.value)


def test_REFUSES_a_duplicated_domain(monkeypatch):
    _install_fakes(monkeypatch, 2)
    with pytest.raises(ValueError) as e:
        dp.generate_pools("missile", "candle", n_per_pool=2, verbose=False,
                          domains=["hospital_supply", "hospital_supply"])
    assert "duplicate" in str(e.value).lower()


def test_REFUSES_an_empty_selection(monkeypatch):
    """An empty list must not be read as 'all domains' -- that is the silent-superset bug."""
    _install_fakes(monkeypatch, 2)
    with pytest.raises(ValueError):
        dp.generate_pools("missile", "candle", n_per_pool=2, verbose=False, domains=[])


def test_an_unknown_domain_is_refused_BEFORE_any_api_call(monkeypatch):
    """Refuse on the cheap check, not after paying for the valid domains ahead of it.

    The bad name is placed SECOND, behind a valid one, deliberately. With the validation block
    deleted the executed mutant raises `KeyError: 'no_such_domain'` -- but only after generating
    every domain that preceded it in the list. A single-element `["no_such_domain"]` list would
    pass this test against a guard that validates lazily inside the loop, which is exactly the
    failure this test exists to exclude.
    """
    calls = _install_fakes(monkeypatch, 2)
    with pytest.raises(ValueError) as e:
        dp.generate_pools("missile", "candle", n_per_pool=2, verbose=False,
                          domains=["hospital_supply", "no_such_domain"])
    assert "no_such_domain" in str(e.value)
    assert calls == [], "the generator paid for a valid domain before validating the whole list"


# --------------------------------------------------------------------------- #
# 3. Backward compatibility -- the default path must be unchanged (§34)
# --------------------------------------------------------------------------- #
def test_default_None_selects_every_domain_in_declaration_order(monkeypatch):
    _install_fakes(monkeypatch, 2)
    obj = dp.generate_pools("missile", "candle", n_per_pool=2, verbose=False)
    assert obj["_meta"]["domains"] == list(dp.DOMAINS)
    assert len(obj["pools"]) == len(dp.DOMAINS) * 4


def test_explicitly_passing_every_domain_equals_the_default(monkeypatch):
    """The flag must be a pure restriction: full selection == no selection."""
    _install_fakes(monkeypatch, 2)
    a = dp.generate_pools("missile", "candle", n_per_pool=2, verbose=False)
    _install_fakes(monkeypatch, 2)
    b = dp.generate_pools("missile", "candle", n_per_pool=2, verbose=False,
                          domains=list(dp.DOMAINS))
    assert a["_meta"]["domains"] == b["_meta"]["domains"]
    assert a["pools"].keys() == b["pools"].keys()
    assert a["_meta"]["content_sha16"] == b["_meta"]["content_sha16"], \
        "the content hash must not depend on HOW the full roster was requested"


# --------------------------------------------------------------------------- #
# 4. Wiring: the CLI flag must REACH generate_pools (§22.4)
# --------------------------------------------------------------------------- #
def test_the_CLI_flag_is_WIRED_to_generate_pools(monkeypatch, tmp_path):
    """Testing the parser is not testing the wiring. Capture what main() actually passes."""
    seen = {}

    def spy(concept, codeword, model, seed, n_per_pool, domains=None, **kw):
        seen["domains"] = domains
        return {"_meta": {"content_sha16": "deadbeefdeadbeef", "domains": domains or []},
                "pools": {"hospital_supply|benign": {"n": n_per_pool}}}

    monkeypatch.setattr(dp, "generate_pools", spy)
    out = tmp_path / "pools.json"
    monkeypatch.setattr(sys, "argv", [
        "demo_pools.py", "--concept", "missile", "--codeword", "candle",
        "--domains", "hospital_supply, airport_ground", "--out", str(out), "--refresh",
    ])
    rc = dp.main()
    assert rc == 0
    assert seen["domains"] == TWO, "the CLI value did not reach generate_pools"
    assert json.loads(out.read_text())["_meta"]["domains"] == TWO


def test_the_wiring_test_is_not_vacuous(monkeypatch, tmp_path):
    """Isolation control: with no --domains, the spy must see None, not a stale value."""
    seen = {}

    def spy(concept, codeword, model, seed, n_per_pool, domains=None, **kw):
        seen["domains"] = domains
        return {"_meta": {"content_sha16": "deadbeefdeadbeef", "domains": []}, "pools": {}}

    monkeypatch.setattr(dp, "generate_pools", spy)
    out = tmp_path / "pools.json"
    monkeypatch.setattr(sys, "argv", [
        "demo_pools.py", "--concept", "missile", "--codeword", "candle",
        "--out", str(out), "--refresh",
    ])
    dp.main()
    assert seen["domains"] is None, "an absent --domains must stay None, not become []"
