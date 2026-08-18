"""Regression tests for the five 2026-08-18 SILENT-FAILURE defects.

They share one shape: **the run looks successful and is not**. No exception, no non-zero exit
that survives into the artifact, no entry in the failure ledger — just a number that is not what
its label says, or a guard that cannot fire.

  T8   (extract_boombness ~484)  every `--fit-dir` consumer torch.loads the direction payload and
       never reads `payload["meta"]`, which records the position / model / layers the directions
       were FITTED on. The 2026-08-17 per-row assert proves where h was READ, not where d was
       FITTED, so the phantom cell (fit at one position, read at another) and its cross-MODEL
       cousin still walk past every guard. Same blind load at aggressive_patching.py ~404 and
       surgical_knockout.py ~240 — owned by other agents, NOT touched here; the validator lives in
       common.py so those two can adopt it without a third copy.
  T8b  (extract_boombness ~361)  `d = payload[name].get(L); if d is None: continue` drops the
       COLUMN, writes the ROW, calls ledger.ok(), and reports n_failed = 0 — for a run in which
       the headline metric does not exist at some of its layers.
  T12  (judge_boombness ~199)  DONE.json was written BEFORE the null-judgement abort gate, so an
       aborted judge run still satisfied `require_done`; and (~92) the judge never checked that
       the generation run it judges had finished.
  T13  (coherence_gate ~99)  `coherent: True` for an EMPTY or all-short sample: `degeneracy()`
       returns None under 8 words, and nan fails no threshold.
  T11  (prompt_families ~568 vs common ~235)  TWO DIFFERENT FUNCTIONS under ONE key name,
       `bank_content_sha16` — sha of the concatenated per-row shas (7002854cf834e9f9) and sha of
       the FILE BYTES (71bea179345ed118) — never compared, though note_bank's docstring says the
       whole point is that "a content hash makes a mismatched join detectable instead of
       invisible".

STANDING RULE (project): a guard that has never been tested against a case it should fail is not a
guard. Every test below is written to FAIL against the pre-fix source, which is exported from git
and imported alongside the fixed module so the failure is demonstrated IN-PROCESS rather than
asserted in a comment. `_pre_fix_rev` pins the revision by CONTENT (the parent of the commit that
first introduced the fix marker), falling back to HEAD while the fix is still uncommitted — the
lesson of test_patching_readout's `_rev_before`, where "HEAD" silently became the FIXED file the
moment the fix landed and the suite started comparing a file to itself.

Responsible handling: this file never reads gens.jsonl or any bank prompt text. The coherence
tests build their own synthetic short/empty strings; the artifact-backed checks read numeric and
hash fields only.
"""
import importlib.util
import json
import math
import os
import subprocess
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRCB = os.path.join(REPO, "src", "boombness")
sys.path.insert(0, SRCB)
sys.path.insert(0, os.path.join(REPO, "doublespeak_causality"))

import torch  # noqa: E402

import common                                  # the FIXED module          # noqa: E402
import coherence_gate                          # the FIXED module          # noqa: E402
import extract_boombness                       # the FIXED module          # noqa: E402
import prompt_families                         # the FIXED module          # noqa: E402


# --------------------------------------------------------------------------- #
# Pre-fix modules, imported live
# --------------------------------------------------------------------------- #
def _git(*args):
    return subprocess.run(["git", *args], cwd=REPO, check=True,
                          capture_output=True, text=True).stdout


def _pre_fix_rev(target: str, marker: str) -> str:
    """Revision of `target` as it stood BEFORE `marker` was introduced.

    While the fix is uncommitted, no commit contains the marker and HEAD *is* the pre-fix file —
    which is asserted, not assumed, by `_module_at` below. Once the fix is committed, this pins
    the parent of the commit that introduced it, so the suite keeps testing against the defect
    instead of quietly diffing the fixed file against itself.
    """
    shas = _git("log", "--format=%H", "-S", marker, "--", target).split()
    return (shas[-1] + "^") if shas else "HEAD"


def _module_at(tmpdir, target: str, marker: str, modname: str):
    src = os.path.join(str(tmpdir), modname + ".py")
    rev = _pre_fix_rev(target, marker)
    with open(src, "w") as fh:
        subprocess.run(["git", "show", f"{rev}:{target}"], cwd=REPO, check=True, stdout=fh)
    text = open(src).read()
    assert marker not in text, (
        f"{target}@{rev} already contains {marker!r}: this fixture is not the pre-fix file, so "
        f"'fails against the old code' would be unverifiable")
    spec = importlib.util.spec_from_file_location(modname, src)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def old_common(tmp_path_factory):
    return _module_at(tmp_path_factory.mktemp("pre_t8"), "src/boombness/common.py",
                      "validate_direction_payload", "old_common")


@pytest.fixture(scope="module")
def old_coherence(tmp_path_factory):
    return _module_at(tmp_path_factory.mktemp("pre_t13"), "src/boombness/coherence_gate.py",
                      "MIN_SCORABLE_FRAC", "old_coherence_gate")


@pytest.fixture(scope="module")
def old_extract(tmp_path_factory):
    return _module_at(tmp_path_factory.mktemp("pre_t8b"), "src/boombness/extract_boombness.py",
                      "direction_layer_coverage", "old_extract_boombness")


@pytest.fixture(scope="module")
def old_prompt_families(tmp_path_factory):
    return _module_at(tmp_path_factory.mktemp("pre_t11"), "src/boombness/prompt_families.py",
                      "bank_rows_sha16", "old_prompt_families")


def _old_judge_src(tmp_path_factory):
    d = tmp_path_factory.mktemp("pre_t12")
    p = os.path.join(str(d), "old_judge.py")
    rev = _pre_fix_rev("src/boombness/judge_boombness.py", "allow_partial_gens")
    with open(p, "w") as fh:
        subprocess.run(["git", "show", f"{rev}:src/boombness/judge_boombness.py"],
                       cwd=REPO, check=True, stdout=fh)
    return open(p).read()


@pytest.fixture(scope="module")
def old_judge_src(tmp_path_factory):
    return _old_judge_src(tmp_path_factory)


# --------------------------------------------------------------------------- #
# T8 — the fit payload's own provenance was never read
# --------------------------------------------------------------------------- #
def _payload(position="codeword_last", model="Llama-3.1-8B-Instruct", layers=(0, 1, 2), meta=True):
    p = {"layers": list(layers),
         "d_surface": {L: torch.ones(4) for L in layers},
         "gap": {}, "n_per_cell": {}}
    if meta:
        p["meta"] = {"position": position, "model": model, "split_fitted_on": "dev"}
    return p


def test_t8_position_mismatch_is_refused():
    """The phantom cell itself: directions fitted at `last`, applied at `codeword_last`."""
    with pytest.raises(SystemExit) as e:
        common.validate_direction_payload(_payload(position="last"), path="fake.pt",
                                          position="codeword_last")
    assert "position" in str(e.value)


def test_t8_model_mismatch_is_refused():
    """A Llama-fitted direction projected onto Qwen3 activations gives plausible cosines and
    means nothing; nothing in the repo noticed."""
    with pytest.raises(SystemExit) as e:
        common.validate_direction_payload(_payload(model="Llama-3.1-8B-Instruct"),
                                          path="fake.pt", model="Qwen/Qwen3-14B",
                                          position="codeword_last")
    assert "model" in str(e.value)


def test_t8_model_id_basename_is_not_a_mismatch():
    """A local snapshot path and the bare repo id are the SAME weights. A guard that cries wolf
    here would be routed around with a --skip flag within a day."""
    v = common.validate_direction_payload(
        _payload(model="/local/snapshots/Qwen3-14B"), path="fake.pt",
        model="Qwen/Qwen3-14B", position="codeword_last")
    assert v["problems"] == []


def test_t8_unlabelled_payload_is_refused():
    with pytest.raises(SystemExit):
        common.validate_direction_payload(_payload(meta=False), path="fake.pt",
                                          position="codeword_last")


def test_t8_layer_subset_is_reported_but_not_fatal():
    """A deliberately layer-subsetted fit (the Qwen3 depth sweep fits 14 of 40 blocks) is legal to
    consume — but it is the upstream cause of T8b, so it must be COUNTED, not discovered later as
    a column of blanks."""
    v = common.validate_direction_payload(_payload(layers=(0, 1)), path="fake.pt",
                                          position="codeword_last", layers=[0, 1, 2, 3])
    assert v["problems"] == []
    assert v["n_layers_missing_from_fit"] == 2
    assert v["layers_missing_from_fit"] == [2, 3]
    assert v["problems_nonfatal"]


def test_t8_guard_did_not_exist_before(old_common):
    """The defect, in-process: the pre-fix module has no validator at all, so every test above
    fails against it — there is nothing to call."""
    assert not hasattr(old_common, "validate_direction_payload")


def test_t8_extract_now_validates_before_scoring(old_extract):
    """`extract_boombness.main` must call the validator on every payload it loads. The pre-fix
    module's source never mentions `meta` on the payload it loads at all."""
    fixed = open(os.path.join(SRCB, "extract_boombness.py")).read()
    assert "validate_direction_payload" in fixed
    assert "validate_direction_payload" not in open(old_extract.__file__).read()


# --------------------------------------------------------------------------- #
# T8 — LATENCY, on the committed artifacts (this is why no number moves)
# --------------------------------------------------------------------------- #
def _fit_dir_runs():
    import glob
    out = []
    for cfg in glob.glob(os.path.join(REPO, "outputs", "boombness", "*", "*", "config.json")):
        try:
            o = json.load(open(cfg))
        except Exception:
            continue
        fd = (o.get("args") or {}).get("fit_dir")
        if fd:
            out.append((os.path.dirname(cfg), fd, (o.get("args") or {})))
    return out


def test_t8_is_latent_on_every_committed_run():
    """Verified before the fix was written and re-verified here: of the committed runs carrying a
    `fit_dir`, every one consumes a payload fitted at the SAME position on the SAME model it runs
    on. The guard closes a hole; it does not correct a published number."""
    runs = _fit_dir_runs()
    if not runs:
        pytest.skip("no committed fit_dir runs on this checkout")
    checked = mismatched = 0
    for run_dir, fit_dir, args in runs:
        meta_p = os.path.join(run_dir, "metadata.json")
        run_model = json.load(open(meta_p)).get("model") if os.path.exists(meta_p) else None
        for split in ("dev", "heldout"):
            p = os.path.join(fit_dir, f"directions_fit_{split}.pt")
            if not os.path.exists(p):
                continue
            meta = (torch.load(p, map_location="cpu", weights_only=False) or {}).get("meta") or {}
            assert meta, f"{p} has no meta block"
            checked += 1
            pos = args.get("position")
            if pos and meta.get("position") and meta["position"] != pos:
                mismatched += 1
            if run_model and meta.get("model") and \
                    os.path.basename(str(meta["model"])) != os.path.basename(str(run_model)):
                mismatched += 1
    assert checked > 0
    assert mismatched == 0, f"{mismatched} phantom fit/read combinations among committed runs"


# --------------------------------------------------------------------------- #
# T8b — a dropped COLUMN is invisible to a ledger that counts ROWS
# --------------------------------------------------------------------------- #
class _Tok:
    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": [10, 11, 12, 13, 14]}


class _LM:
    model_id = "fake/Model"
    tokenizer = _Tok()
    num_layers = 4
    hidden_size = 4


class _Hit:
    last_idx = [3]
    spans = [(3, 4)]


class _DC:
    @staticmethod
    def apply_template(tok, text, enable_thinking=None):
        return "TEMPLATED"

    @staticmethod
    def find_word_occurrences_in_text(tok, text, needle, add_special_tokens=False):
        return _Hit()


class _Run:
    """Minimal stand-in for RunDir: collects rows and notes without touching the filesystem."""
    def __init__(self):
        self.rows, self.notes = [], {}
        self.cache = "/tmp/does-not-exist"

    def log_row(self, r):
        self.rows.append(r)

    def note(self, **kw):
        self.notes.update(kw)


def _score_with(mod, mp, fit_layers, score_layers):
    """Drive `stage_score` on a fake model whose fit covers only `fit_layers`.

    STUBS GO THROUGH `monkeypatch` (2026-08-19). `mod.sg` is the SHARED `signals` module object,
    so the bare `mod.sg.readout_id_pair = ...` this helper used to do was a process-global
    mutation that outlived the test: in a full-suite run it left `signals.readout_id_pair`
    stubbed and failed 8 tests in `tests/test_patching_readout.py` that pass in isolation. A test
    file that breaks other test files is the same never-checked-at-the-other-end shape this suite
    exists to catch.
    """
    rows = [{"prompt_id": "p1", "prompt_sha16": "s", "family_id": "f", "condition": "c",
             "cell": "C", "domain": "d", "split": "dev", "bank_block": "b",
             "query_kind": "behavioral", "n_examples": 1, "strength": 1, "consistency": 1,
             "example_position": 0, "role_style": "r", "target_surface": "carrot",
             "n_target_occurrences": 1, "concept": "bomb", "codeword": "carrot",
             "full_prompt": "PROMPT"}]
    payload = {"layers": list(fit_layers),
               "d_surface": {L: torch.ones(4) for L in fit_layers},
               "meta": {"position": "codeword_last", "model": "fake/Model"}}
    run, ledger = _Run(), common.FailureLedger()
    mp.setattr(mod, "forward_hidden",
               lambda lm, ids, _diag=None: torch.ones(_LM.num_layers + 1, 5, 4))
    mp.setattr(mod.sg, "readout_id_pair",
               lambda tok, c, w, mode="primary": (
                   [1], [2], {"concept": {"full_word_pieces": []},
                              "codeword": {"full_word_pieces": []}}))
    out = mod.stage_score(_LM(), _DC(), rows, list(score_layers), {"dev": payload}, run, ledger,
                          ["d_surface"], [], cache_final_reps=False)
    return out, run, ledger


def test_t8b_head_reports_a_clean_run_with_a_missing_metric(old_extract, monkeypatch):
    """THE DEFECT, executed. The fit covers 2 of 4 scored layers; the pre-fix stage_score writes
    the row, calls ledger.ok(), reports n_failed = 0 — and results.jsonl simply has no
    `d_surface|L2|cos` / `|L3|cos` key at all. Nothing in the run says so."""
    out, run, ledger = _score_with(old_extract, monkeypatch, [0, 1], [0, 1, 2, 3])
    assert ledger.as_dict()["n_failed"] == 0
    assert out["n_scored_rows"] == 1
    rec = run.rows[0]
    assert "d_surface|L1|cos" in rec and "d_surface|L2|cos" not in rec
    assert not any("coverage" in k for k in out), \
        "pre-fix summary already reports coverage; this fixture is not the pre-fix module"


def test_t8b_coverage_is_counted_and_visible(monkeypatch):
    """Same input through the fixed module: the missing layers are a NUMBER in the summary."""
    out, run, ledger = _score_with(extract_boombness, monkeypatch, [0, 1], [0, 1, 2, 3])
    cov = out["direction_layer_coverage"]["d_surface"]
    assert cov["n_layers_requested"] == 4
    assert cov["n_layers_with_no_direction"] == 2
    assert cov["layers_with_no_direction"] == [2, 3]
    assert cov["n_row_layer_cells_missing"] == 2
    assert cov["n_row_layer_cells_written"] == 2
    assert out["n_missing_direction_layer_cells"] == 2
    # The row itself is unchanged: the point is that the ABSENCE is now recorded elsewhere,
    # because a missing column is not a row failure and the ledger can never see it.
    assert ledger.as_dict()["n_failed"] == 0
    assert "d_surface|L2|cos" not in run.rows[0]


def test_t8b_full_coverage_reports_zero_missing(monkeypatch):
    out, _, _ = _score_with(extract_boombness, monkeypatch, [0, 1, 2, 3], [0, 1, 2, 3])
    assert out["n_missing_direction_layer_cells"] == 0
    assert out["direction_layer_coverage"]["d_surface"]["n_layers_with_no_direction"] == 0


# --------------------------------------------------------------------------- #
# T12 — an aborted judge run that still says DONE
# --------------------------------------------------------------------------- #
def _mainsrc(text):
    import ast
    tree = ast.parse(text)
    fn = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main"][0]
    finish = abort_gate = require = None
    for node in ast.walk(fn):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "finish":
            finish = node.lineno if finish is None else min(finish, node.lineno)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id == "require_done":
            require = node.lineno
        if isinstance(node, ast.If) and "max_null_frac" in ast.dump(node.test):
            abort_gate = node.lineno
    return {"finish": finish, "abort": abort_gate, "require_done": require}


def test_t12_head_writes_done_above_the_abort_gate(old_judge_src):
    """THE DEFECT: `run.finish()` (which writes DONE.json) runs BEFORE the null-judgement gate, so
    a run that trips plan §3.6 leaves a directory that `require_done` accepts. The abort existed
    only in the process exit code — the thing that gets lost first."""
    pos = _mainsrc(old_judge_src)
    assert pos["finish"] is not None and pos["abort"] is not None
    assert pos["finish"] < pos["abort"], "fixture is not the pre-fix judge"
    assert pos["require_done"] is None, "fixture already checks the generation run"


def test_t12_abort_gate_precedes_finish():
    pos = _mainsrc(open(os.path.join(SRCB, "judge_boombness.py")).read())
    assert pos["abort"] < pos["finish"], \
        "the null-judgement gate must run BEFORE DONE.json is written"


def test_t12b_judge_requires_the_generation_run_to_have_finished():
    pos = _mainsrc(open(os.path.join(SRCB, "judge_boombness.py")).read())
    assert pos["require_done"] is not None
    assert pos["require_done"] < pos["finish"]


def test_t12_abort_writes_aborted_not_done_and_require_done_refuses(tmp_path):
    """The artifact side of the same fix: an aborted run must be REFUSED by the consumer-side
    gate, not merely exit 1."""
    run = common.RunDir("judge", None, tag="t", out_root=str(tmp_path))
    run.abort("judge_null_frac 0.9000 > 0.05", summary={"x": 1}, ledger=common.FailureLedger())
    assert os.path.exists(run.p("ABORTED.json"))
    assert not os.path.exists(run.p("DONE.json"))
    assert json.load(open(run.p("summary.json")))["aborted"] is True
    with pytest.raises(SystemExit) as e:
        common.require_done(run.path)
    assert "ABORTED" in str(e.value)


def test_t12_abort_did_not_exist_before(old_common):
    assert not hasattr(old_common.RunDir, "abort")


# --------------------------------------------------------------------------- #
# T13 — coherence certified by an empty or all-short sample
# --------------------------------------------------------------------------- #
def _fake_run(tmp_path, texts):
    """A synthetic score_behavior run dir. The strings are written HERE — no real generation text
    is read by this suite."""
    d = tmp_path / ("run_%d" % len(texts))
    d.mkdir()
    with open(d / "gens.jsonl", "w") as f:
        for i, t in enumerate(texts):
            f.write(json.dumps({"prompt_id": f"p{i}", "condition": "natural_doublespeak",
                                "generation": t}) + "\n")
    return str(d)


SHORT = "I cannot help with that."                       # 5 words -> unscorable
LONG_OK = " ".join(f"word{i}" for i in range(40))        # healthy: all tokens unique


def test_t13_head_certifies_an_empty_sample(old_coherence, tmp_path):
    """THE DEFECT, executed: zero rows, every ratio nan, and `nan < MIN` is False in IEEE-754, so
    the verdict is `coherent: True`. An empty file certified the run."""
    a = old_coherence.assess(_fake_run(tmp_path, []))
    assert a["n_scored"] == 0
    assert math.isnan(a["uniq_word_ratio"])
    assert a["coherent"] is True


def test_t13_head_certifies_an_all_short_sample(old_coherence, tmp_path):
    """400 refusals and 3 long generations: the pre-fix gate reports the 3."""
    a = old_coherence.assess(_fake_run(tmp_path, [SHORT] * 400 + [LONG_OK] * 3))
    assert a["n_dropped_short"] == 400 and a["n_scored"] == 3
    assert a["coherent"] is True


def test_t13_empty_sample_is_now_incoherent(tmp_path):
    a = coherence_gate.assess(_fake_run(tmp_path, []))
    assert a["coherent"] is False
    assert any("n_considered = 0" in f for f in a["failures"])


def test_t13_nothing_scorable_is_now_incoherent(tmp_path):
    a = coherence_gate.assess(_fake_run(tmp_path, [SHORT] * 50))
    assert a["coherent"] is False
    assert a["scorable_frac"] == 0.0


def test_t13_all_short_sample_is_now_incoherent(tmp_path):
    a = coherence_gate.assess(_fake_run(tmp_path, [SHORT] * 400 + [LONG_OK] * 3))
    assert a["coherent"] is False
    assert any("scorable_frac" in f for f in a["failures"])
    assert any("n_scored" in f for f in a["failures"])


def test_t13_a_healthy_run_still_passes(tmp_path):
    """The thresholds must not reclassify real runs: 100% scorable, healthy ratios."""
    a = coherence_gate.assess(_fake_run(tmp_path, [LONG_OK] * 100))
    assert a["coherent"] is True
    assert a["scorable_frac"] == 1.0


def test_t13_the_worst_committed_arm_still_passes(tmp_path):
    """len_A, the length-suppressed arm, scored 306/420 = 0.729. The floor is 0.50, so a real —
    if short — arm is not swept up by this gate. Modelled at the same proportion here."""
    a = coherence_gate.assess(_fake_run(tmp_path, [LONG_OK] * 306 + [SHORT] * 114))
    assert a["scorable_frac"] == pytest.approx(306 / 420)
    assert a["coherent"] is True


# --------------------------------------------------------------------------- #
# T11 — two functions, one key name, never compared
# --------------------------------------------------------------------------- #
def _synthetic_bank(tmp_path, n=5):
    p = tmp_path / "bank.jsonl"
    with open(p, "w") as f:
        for i in range(n):
            f.write(json.dumps({"prompt_id": f"id{i}", "prompt_sha16": f"{i:016x}",
                                "full_prompt": "x"}) + "\n")
    return str(p)


def _note_bank_meta(mod, tmp_path, bank, tag):
    run = mod.RunDir("t11", None, tag=tag, out_root=str(tmp_path / ("root_" + tag)))
    run.note_bank(bank)
    return dict(run._extra_meta)


def test_t11_head_writes_two_different_functions_under_one_name(old_common, old_prompt_families,
                                                                tmp_path):
    """THE DEFECT, executed: both writers emit `bank_content_sha16`, the values differ for the
    same bank, and no code path anywhere compares them — so the key can neither confirm nor deny a
    join. On the committed 2352-row bank the two values are 71bea179345ed118 (file bytes) and
    7002854cf834e9f9 (rows)."""
    bank = _synthetic_bank(tmp_path)
    meta = _note_bank_meta(old_common, tmp_path, bank, "old")
    rows = [json.loads(l) for l in open(bank)]
    import hashlib
    rows_hash = hashlib.sha256(
        "|".join(r["prompt_sha16"] for r in sorted(rows, key=lambda r: r["prompt_id"]))
        .encode()).hexdigest()[:16]
    assert "bank_content_sha16" in meta
    assert meta["bank_content_sha16"] != rows_hash          # same key, different function
    assert "bank_file_sha16" not in meta and "bank_rows_sha16" not in meta
    assert not hasattr(old_common, "compare_bank_hashes")   # the promised comparison never existed


def test_t11_note_bank_writes_both_hashes_under_distinct_names(tmp_path):
    bank = _synthetic_bank(tmp_path)
    meta = _note_bank_meta(common, tmp_path, bank, "new")
    assert meta["bank_file_sha16"] and meta["bank_rows_sha16"]
    assert meta["bank_file_sha16"] != meta["bank_rows_sha16"]
    assert "bank_content_sha16" not in meta                 # the ambiguous key is retired
    rows = [json.loads(l) for l in open(bank)]
    assert meta["bank_rows_sha16"] == common.rows_sha16(
        (r["prompt_id"], r["prompt_sha16"]) for r in rows)


def test_t11_prompt_families_and_common_agree_on_the_rows_hash():
    """One implementation, called from both ends of the join — so the two cannot drift apart by
    someone editing one of two copies (the one-of-two-paths shape, six instances this sprint)."""
    src = open(os.path.join(SRCB, "prompt_families.py")).read()
    assert "rows_sha16(" in src and '"bank_rows_sha16"' in src
    assert '"bank_content_sha16"' not in src
    assert prompt_families.rows_sha16 is common.rows_sha16


def test_t11_rows_sha16_reproduces_the_committed_bank_meta():
    """The committed bank meta records 7002854cf834e9f9 for the 2352-row bank; the shared helper
    must reproduce it exactly, or every legacy artifact becomes uncomparable."""
    meta_p = os.path.join(REPO, "data", "boombness_prompts",
                          "boombness_prompt_bank_meta.json")
    bank_p = os.path.join(REPO, "data", "boombness_prompts", "boombness_prompt_bank.jsonl")
    if not (os.path.exists(meta_p) and os.path.exists(bank_p)):
        pytest.skip("committed bank not present on this checkout")
    stats = json.load(open(meta_p))["stats"]
    legacy = common.bank_hashes(stats, legacy="rows")["bank_rows_sha16"]
    pairs = []
    with open(bank_p) as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                pairs.append((r["prompt_id"], r["prompt_sha16"]))
    assert common.rows_sha16(pairs) == legacy


def test_t11_rows_sha16_does_not_lose_a_duplicated_prompt_id():
    """'the two banks hash the same' must not be reachable by dropping a row."""
    a = common.rows_sha16([("id0", "aa"), ("id0", "bb")])
    b = common.rows_sha16([("id0", "aa")])
    assert a != b


def test_t11_legacy_key_is_read_with_an_explicit_flavour():
    run_meta = {"bank_content_sha16": "71bea179345ed118"}
    bank_meta = {"bank_content_sha16": "7002854cf834e9f9"}
    assert common.bank_hashes(run_meta, legacy="file")["bank_file_sha16"] == "71bea179345ed118"
    assert common.bank_hashes(run_meta, legacy="file")["bank_rows_sha16"] is None
    assert common.bank_hashes(bank_meta, legacy="rows")["bank_rows_sha16"] == "7002854cf834e9f9"


def test_t11_compare_bank_hashes_detects_a_mismatched_join():
    with pytest.raises(SystemExit) as e:
        common.compare_bank_hashes({"bank_rows_sha16": "aaaaaaaaaaaaaaaa", "bank_path": "/b"},
                                   {"stats": {"bank_rows_sha16": "bbbbbbbbbbbbbbbb"}})
    assert "DIFFERENT bank" in str(e.value)


def test_t11_compare_bank_hashes_never_reads_absence_as_agreement():
    """An old artifact that predates the rows hash must not be able to certify a join it never
    recorded."""
    v = common.compare_bank_hashes({"bank_path": "/b"},
                                   {"stats": {"bank_rows_sha16": "bbbbbbbbbbbbbbbb"}},
                                   strict=False)
    assert v["ok"] is False
    assert "bank_rows_sha16" in v["unknown"] and not v["mismatched"]


def test_t11_compare_bank_hashes_accepts_a_matching_join():
    v = common.compare_bank_hashes(
        {"bank_rows_sha16": "7002854cf834e9f9", "bank_file_sha16": "71bea179345ed118"},
        {"stats": {"bank_rows_sha16": "7002854cf834e9f9"}})
    assert v["ok"] is True and v["checked"] == ["bank_rows_sha16"]
