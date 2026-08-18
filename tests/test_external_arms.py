"""Tests for analyze_external_arms — chiefly that the control-band guard FAILS a case it should fail.

House rule: a guard that has never been tested against a case it should fail is not a guard. This
project shipped SIX dead guards, and twice published a control band that was one draw repeated
(retraction #7, then R-12). The band guard below is tested against exactly that input.
"""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "boombness")
sys.path.insert(0, SRC)

import analyze_external_arms as X  # noqa: E402


def _rows(scores, domains=None, flags=None):
    """scores: {prompt_id: score}"""
    domains = domains or {p: ("d%d" % (i % 4)) for i, p in enumerate(sorted(scores))}
    out = {}
    for p, s in scores.items():
        out[p] = {"prompt_id": p, "strongreject_score": s,
                  "malicious_at_0.5": bool(s >= 0.5), "refused": bool(s < 0.5),
                  "domain": domains[p]}
    return out


def _write(tmp, name, rows, gens_text=None):
    """Write a judge-run-shaped dir.

    `gens_text` writes a SOURCE GENERATIONS dir and points this judge run's config at it, which is
    what the band guard fingerprints. Pass the same text for two draws to simulate R-12 (identical
    generations); pass different text for genuinely distinct draws. Omit it to simulate a judge run
    whose source cannot be resolved, which the guard must also refuse.
    """
    d = os.path.join(tmp, name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        for r in rows.values():
            f.write(json.dumps(r) + "\n")
    if gens_text is not None:
        g = os.path.join(tmp, name + "_gens")
        os.makedirs(g, exist_ok=True)
        with open(os.path.join(g, "gens.jsonl"), "w") as f:
            f.write(gens_text)
        with open(os.path.join(d, "config.json"), "w") as f:
            json.dump({"experiment": "judge", "args": {"gens": g}}, f)
    return d


BASE = {f"p{i}": (0.9 if i < 2 else 0.1) for i in range(12)}
ARM = {f"p{i}": (0.9 if i < 6 else 0.1) for i in range(12)}


def test_score_fingerprint_distinguishes_draws_that_differ():
    a = _rows({"p1": 0.1, "p2": 0.2})
    b = _rows({"p1": 0.1, "p2": 0.3})
    assert X.draw_fingerprint(a) != X.draw_fingerprint(b)


def test_source_gens_fingerprint_catches_what_the_score_fingerprint_MISSES(tmp_path):
    """THE REASON THE GUARD IS AT THE GENERATION LEVEL.

    R-12's three band draws had byte-identical generations, but StrongReject is not bitwise
    deterministic, so re-judging them produced three DIFFERENT score vectors. A score-level check
    therefore reports three distinct draws for a band that has one. This test pins that: same gens,
    different scores -> score fingerprints differ (useless), gens fingerprints match (correct).
    """
    tmp = str(tmp_path)
    same_gens = '{"prompt_id": "p1", "generation": "identical text"}\n'
    d1 = _write(tmp, "j1", _rows({"p1": 0.10, "p2": 0.20}), gens_text=same_gens)
    d2 = _write(tmp, "j2", _rows({"p1": 0.11, "p2": 0.19}), gens_text=same_gens)
    assert X.draw_fingerprint(X.load(d1)) != X.draw_fingerprint(X.load(d2))   # the weak check fails
    assert X.source_gens_fingerprint(d1) == X.source_gens_fingerprint(d2)     # the real one holds


def test_source_gens_fingerprint_is_none_when_unresolvable(tmp_path):
    d = _write(str(tmp_path), "nocfg", _rows({"p1": 0.1}))
    assert X.source_gens_fingerprint(d) is None


def _run(tmp, extra):
    out = os.path.join(tmp, "res.json")
    cmd = [sys.executable, os.path.join(SRC, "analyze_external_arms.py"),
           "--baseline", _write(tmp, "base", _rows(BASE)),
           "--arm", "A=" + _write(tmp, "arm", _rows(ARM)),
           "--label", "t", "--out", out] + extra
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr
    with open(out) as f:
        return json.load(f), r.stdout


def test_band_REFUSED_when_the_three_draws_are_identical(tmp_path):
    """THE GUARD. Three 'draws' with identical score vectors -- exactly R-12 -- must be refused,
    and must NOT report a mean or an sd. Against a guardless implementation this returns sd=0.0,
    which reads as an extraordinarily reproducible control."""
    tmp = str(tmp_path)
    same = '{"prompt_id": "p0", "generation": "one draw, three labels"}\n'
    # scores deliberately PERTURBED per draw, as real judge nondeterminism would perturb them.
    draws = ["s1=" + _write(tmp, "b1", _rows(BASE), gens_text=same),
             "s2=" + _write(tmp, "b2", _rows({p: v + 0.01 for p, v in BASE.items()}),
                            gens_text=same),
             "s3=" + _write(tmp, "b3", _rows({p: v + 0.02 for p, v in BASE.items()}),
                            gens_text=same)]
    res, out = _run(tmp, [x for d in draws for x in ("--band", d)])
    band = res["control_band"]
    assert band["REFUSED"] is True
    assert band["between_draw_sd"] is None and band["mean"] is None
    assert "IDENTICAL GENERATIONS" in band["reason"]
    assert "BAND REFUSED" in out
    # and it names the clashing draws rather than just complaining
    assert all(s in band["reason"] for s in ("s1", "s2", "s3"))


def test_band_REFUSED_with_fewer_than_three_draws(tmp_path):
    tmp = str(tmp_path)
    res, _ = _run(tmp, ["--band", "s1=" + _write(tmp, "b1", _rows(BASE), gens_text="a\n"),
                        "--band", "s2=" + _write(tmp, "b2", _rows(
                            {p: v + 0.01 for p, v in BASE.items()}), gens_text="b\n")])
    assert res["control_band"]["REFUSED"] is True
    assert ">=3" in res["control_band"]["reason"]


def test_band_ACCEPTED_when_draws_genuinely_differ(tmp_path):
    """The guard must not refuse a real band -- otherwise it is merely a different dead guard."""
    tmp = str(tmp_path)
    ds = []
    for i, off in enumerate((0.00, 0.02, 0.05)):
        ds += ["--band", f"s{i}=" + _write(tmp, f"b{i}",
                                           _rows({p: v + off for p, v in BASE.items()}),
                                           gens_text=f'{{"draw": {i}}}\n')]
    res, _ = _run(tmp, ds)
    band = res["control_band"]
    assert band["REFUSED"] is False
    assert band["between_draw_sd"] is not None
    assert len(set(band["source_gens_fingerprints"].values())) == 3
    assert band["gens_unresolved"] == []


def test_band_REFUSED_when_the_source_generations_cannot_be_resolved(tmp_path):
    """No silent fallback to the weak check: unverifiable distinctness is refused."""
    tmp = str(tmp_path)
    ds = []
    for i, off in enumerate((0.00, 0.02, 0.05)):
        ds += ["--band", f"s{i}=" + _write(tmp, f"u{i}",
                                           _rows({p: v + off for p, v in BASE.items()}))]
    res, out = _run(tmp, ds)
    band = res["control_band"]
    assert band["REFUSED"] is True
    assert "cannot resolve source generations" in band["reason"]
    assert band["between_draw_sd"] is None
    assert len(band["gens_unresolved"]) == 3


def test_duplicate_prompt_id_is_refused_not_silently_overwritten(tmp_path):
    d = os.path.join(str(tmp_path), "dup")
    os.makedirs(d)
    with open(os.path.join(d, "results.jsonl"), "w") as f:
        for _ in range(2):
            f.write(json.dumps({"prompt_id": "p1", "strongreject_score": 0.5,
                                "malicious_at_0.5": True, "refused": False, "domain": "d"}) + "\n")
    with pytest.raises(SystemExit):
        X.load(d)


def test_super_additivity_reports_not_established_when_the_ci_spans_zero(tmp_path):
    """A joint arm exactly equal to the sum of its singles must not be called super-additive."""
    tmp = str(tmp_path)
    base = _rows({f"p{i}": 0.1 for i in range(16)})
    b = _rows({f"p{i}": 0.1 + (0.2 if i % 2 else 0.0) for i in range(16)})
    c = _rows({f"p{i}": 0.1 + (0.3 if i % 3 else 0.0) for i in range(16)})
    d = {}
    for p in base:
        d[p] = dict(base[p])
        d[p]["strongreject_score"] = (b[p]["strongreject_score"] + c[p]["strongreject_score"]
                                      - base[p]["strongreject_score"])
    out = os.path.join(tmp, "sa.json")
    cmd = [sys.executable, os.path.join(SRC, "analyze_external_arms.py"),
           "--baseline", _write(tmp, "sbase", base),
           "--arm", "B=" + _write(tmp, "sb", b),
           "--arm", "C=" + _write(tmp, "sc", c),
           "--arm", "D=" + _write(tmp, "sd", d),
           "--super-additive", "B,C,D", "--label", "sa", "--out", out]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    assert r.returncode == 0, r.stderr
    with open(out) as f:
        sa = json.load(f)["super_additivity"]
    assert abs(sa["excess"]) < 1e-9
    assert sa["established"] is False
    assert "NOT established" in r.stdout
