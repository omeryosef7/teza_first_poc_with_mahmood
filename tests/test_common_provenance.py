"""Regression tests for the 2026-08-19 `src/boombness/common.py` defects (a)-(d).

  (a) plan §2.1 requires "random seed" AND "tokenizer name and revision" in every run record.
      Measured before the fix: `seed` appeared in **0 of 171** committed metadata.json (it lived
      only inside `config.json["args"]`, indistinguishable from any other CLI knob), and
      `tokenizer_revision` appeared in **0 of 189** config.json and **0 of 171** metadata.json.
      `model_revision` appeared in 103 of them with the value `null` in every one.
      The fix records the RESOLVED commit -- never the branch name "main", which drifts and would
      make the field a lie -- and, when it cannot be resolved, records null plus a reason under a
      field name that says so.
  (a2) retraction R-12: a run recorded the seed it was ASKED for; nothing recorded the seeds it
      APPLIED, so three "independent" band draws with byte-identical generations looked like three
      draws on disk. `SEED_LOG` + `metadata["seed_never_applied"]` make that state expressible.
  (b) defect T11's residual half: `compare_bank_hashes` raised on a MISMATCH but said nothing when
      NOTHING could be compared -- the state 97 of 114 bank-carrying artifacts are in.
  (c) the class docstring has always claimed "a run's summary.json is only allowed to be written
      through RunDir.finish", and `write_json` would happily write it. An invariant asserted at one
      end of a contract and never checked at the other is this sprint's five dead guards exactly.
  (d) `clustered_proportion_ci` audited against scipy: the arithmetic is clean, but it truncated
      silently on a length mismatch, counted a NaN outcome as an attack SUCCESS (`bool(nan)` is
      True), counted a None outcome as a failure, and returned **zero-width 95% intervals** --
      10 of them are in two committed summary.json files.

STANDING RULE (project): a guard that has never been tested against a case it should FAIL is not a
guard. Every test marked `PRE-FIX` below is executed against the pre-fix module, exported from git
and imported alongside the fixed one, so "it fails the old code" is demonstrated in-process.

Responsible handling: this file reads no generation text and no prompt text. The bank checks touch
`prompt_id` and `prompt_sha16` only (ids and hashes); the artifact checks read numeric fields.
"""
import importlib.util
import json
import math
import os
import re
import subprocess
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRCB = os.path.join(REPO, "src", "boombness")
sys.path.insert(0, SRCB)
sys.path.insert(0, os.path.join(REPO, "doublespeak_causality"))

import common                                    # the FIXED module        # noqa: E402

HF_CACHE = os.path.join(REPO, ".cache", "huggingface", "hub")
LLAMA = "meta-llama/Llama-3.1-8B-Instruct"
HEX40 = re.compile(r"^[0-9a-f]{40}$")


# --------------------------------------------------------------------------- #
# Pre-fix module, imported live (same harness as tests/test_silent_failures.py)
# --------------------------------------------------------------------------- #
def _git(*args):
    return subprocess.run(["git", *args], cwd=REPO, check=True,
                          capture_output=True, text=True).stdout


def _pre_fix_rev(target: str, marker: str) -> str:
    """The revision of `target` from BEFORE `marker` existed.

    While this fix is uncommitted no commit contains the marker and HEAD *is* the pre-fix file;
    once it is committed this pins the parent of the commit that introduced it, so committing the
    fix does not turn its own test red by diffing the fixed file against itself.
    """
    shas = _git("log", "--format=%H", "-S", marker, "--", target).split()
    return (shas[-1] + "^") if shas else "HEAD"


@pytest.fixture(scope="module")
def old_common(tmp_path_factory):
    # `resolve_hf_revision` is introduced by this fix and by nothing before it, so it identifies
    # the pre-fix revision by CONTENT rather than by a date or a filename.
    marker = "resolve_hf_revision"
    target = "src/boombness/common.py"
    rev = _pre_fix_rev(target, marker)
    src = os.path.join(str(tmp_path_factory.mktemp("pre_common")), "old_common_prov.py")
    with open(src, "w") as fh:
        subprocess.run(["git", "show", f"{rev}:{target}"], cwd=REPO, check=True, stdout=fh)
    text = open(src).read()
    assert marker not in text, (
        f"{target}@{rev} already contains {marker!r}: this fixture is not the pre-fix file, so "
        f"'fails against the old code' would be unverifiable")
    spec = importlib.util.spec_from_file_location("old_common_prov", src)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["old_common_prov"] = mod
    spec.loader.exec_module(mod)
    return mod


class Args:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def _run(mod, tmp_path, name, **kw):
    return mod.RunDir("exp", Args(**kw), tag=name, out_root=str(tmp_path))


def _read(run, name):
    with open(os.path.join(run.path, name)) as f:
        return json.load(f)


# =========================================================================== #
# (a) seed + resolved tokenizer revision
# =========================================================================== #
def test_a_config_json_records_the_seed_at_top_level(tmp_path, old_common):
    """PRE-FIX: config.json is {experiment, run_id, args} — the plan §2.1 "random seed" exists
    only as one key among the CLI knobs inside `args`, and is absent entirely for a caller that
    builds a RunDir from a mapping."""
    old = _run(old_common, tmp_path, "old", seed=4321, limit=3)
    cfg_old = _read(old, "config.json")
    assert "seed" not in cfg_old and "seed_source" not in cfg_old      # the defect, executed

    new = _run(common, tmp_path, "new", seed=4321, limit=3)
    cfg = _read(new, "config.json")
    assert cfg["seed"] == 4321
    assert cfg["seed_source"] == "args.seed"
    assert cfg["args"]["seed"] == 4321                                 # and still where it was


def test_a_config_seed_is_null_not_zero_when_there_is_no_seed(tmp_path):
    run = _run(common, tmp_path, "noseed", limit=3)
    cfg = _read(run, "config.json")
    assert cfg["seed"] is None and cfg["seed_source"] is None


def test_a_metadata_json_records_seed_and_the_seeds_actually_applied(tmp_path, old_common):
    """PRE-FIX: metadata.json carried no seed at all — verified over the committed artifacts as
    0 of 171."""
    ledger = old_common.FailureLedger(); ledger.ok(2)
    old = _run(old_common, tmp_path, "old", seed=777)
    old.finish(summary={}, ledger=ledger)
    assert "seed" not in _read(old, "metadata.json")                   # the defect, executed

    n0 = len(common.SEED_LOG)
    new = _run(common, tmp_path, "new", seed=777)
    common.seed_everything(777, label="main")
    led = common.FailureLedger(); led.ok(2)
    new.finish(summary={}, ledger=led)
    meta = _read(new, "metadata.json")
    assert meta["seed"] == 777 and meta["seed_source"] == "args.seed"
    assert {"label": "main", "seed": 777} in meta["seeds_applied"]
    assert meta["n_seeds_applied"] >= 1
    assert meta["seed_never_applied"] is False
    assert len(common.SEED_LOG) > n0


def test_a_seed_never_applied_fires_on_the_R12_shape(tmp_path, capsys):
    """The guard, tested against the case it must FAIL: retraction R-12 is a run launched with
    `--seed 20260901` whose composed recursion fell back to the default 20260824. Requested and
    applied disagree; before this fix nothing on disk could say so."""
    run = _run(common, tmp_path, "r12", seed=20260901)
    common.seed_everything(20260824, label="control_draw_0")           # the R-12 fallback
    common.seed_everything(20260834, label="control_draw_1")
    led = common.FailureLedger(); led.ok(1)
    run.finish(summary={}, ledger=led)
    meta = _read(run, "metadata.json")
    assert meta["seed_never_applied"] is True
    assert [r["seed"] for r in meta["seeds_applied_after_run_start"]] == [20260824, 20260834]
    assert {"label": "control_draw_0", "seed": 20260824} in meta["seeds_applied"]
    assert "R-12" in capsys.readouterr().out


def test_a_seed_log_covers_the_ORDER_PRODUCTION_ACTUALLY_USES(tmp_path, capsys):
    """THE GUARD, TESTED IN THE ORDER ITS CALLERS USE (verifier fix, 2026-08-19).

    All eight scripts in this package call `seed_everything(args.seed)` BEFORE constructing their
    RunDir (judge_boombness 134/171, score_behavior 280/310, probes 662/676, extract_boombness
    681/688, refusalness 137/145, surgical_knockout 626/641, aggressive_patching 1164/1195,
    tokenization_audit 181/189). The first version of `_seed_meta` recorded only the seeds applied
    AFTER construction, so in production `seeds_applied` was `[]`, `n_seeds_applied` was 0, and
    `bool(applied) and ...` published `seed_never_applied: False` -- an affirmative claim that the
    seed WAS applied, computed from an empty collection, in exactly the R-12 case the field exists
    to catch. It passed its own test only because the test seeded after constructing the RunDir."""
    n0 = len(common.SEED_LOG)
    common.seed_everything(31337, label="main")                 # <-- production order: seed FIRST
    run = _run(common, tmp_path, "prodorder", seed=31337)
    led = common.FailureLedger(); led.ok(1)
    run.finish(summary={}, ledger=led)
    meta = _read(run, "metadata.json")
    assert {"label": "main", "seed": 31337} in meta["seeds_applied"]
    assert meta["n_seeds_applied"] >= len(common.SEED_LOG) - n0
    assert meta["seed_never_applied"] is False
    assert meta["seeds_applied_after_run_start"] == []          # the window that used to be all


def test_a_seed_never_applied_fires_in_production_order_too(tmp_path, capsys):
    """The R-12 shape as it actually occurs: the process applies its fallback seed BEFORE the run
    directory exists. Pre-fix this printed nothing and wrote `seed_never_applied: False`."""
    common.seed_everything(20260824, label="control_draw_0")    # applied before the RunDir exists
    run = _run(common, tmp_path, "r12prod", seed=20260902)      # a seed nothing ever applied
    led = common.FailureLedger(); led.ok(1)
    run.finish(summary={}, ledger=led)
    meta = _read(run, "metadata.json")
    assert meta["seed_never_applied"] is True
    assert "R-12" in capsys.readouterr().out


def test_a_seed_never_applied_is_true_when_nothing_was_seeded_at_all(tmp_path):
    """The empty-collection short circuit, stated as its own case: a run that requests a seed and
    calls `seed_everything` zero times has NOT applied it. `bool(applied) and ...` said False."""
    run = _run(common, tmp_path, "unseeded", seed=987654321)    # nobody ever applies this
    led = common.FailureLedger(); led.ok(1)
    run.finish(summary={}, ledger=led)
    assert _read(run, "metadata.json")["seed_never_applied"] is True


def test_a_seed_type_mismatch_is_not_reported_as_R12(tmp_path):
    """A RunDir built from a mapping carries "42" while `seed_everything` records 42; a string/int
    difference must not be published as a run labelled with a seed it never used."""
    run = common.RunDir("exp", {"seed": "42"}, tag="strseed", out_root=str(tmp_path))
    common.seed_everything(42, label="main")     # inside the run's window AND the process log, so
    led = common.FailureLedger(); led.ok(1)      # only the string/int normalisation decides this
    run.finish(summary={}, ledger=led)
    assert _read(run, "metadata.json")["seed_never_applied"] is False


def test_a_seed_log_is_capped_without_lying_about_the_count(tmp_path):
    """A per-draw seeding loop (what score_behavior's composed arm needs, R-12) applies thousands
    of seeds. The list is truncated so metadata.json stays readable; the COUNT and the
    never-applied test must still be computed over all of them, or the cap becomes the next place
    a seed hides."""
    run = _run(common, tmp_path, "manyseeds", seed=555)
    for i in range(300):
        common.seed_everything(1000 + i, label=f"draw_{i}")
    common.seed_everything(555, label="main")     # the requested seed, INSIDE the elided window
    for i in range(300, 400):
        common.seed_everything(1000 + i, label=f"draw_{i}")
    led = common.FailureLedger(); led.ok(1)
    run.finish(summary={}, ledger=led)
    meta = _read(run, "metadata.json")
    assert meta["seeds_applied_truncated"] is True
    assert len(meta["seeds_applied"]) < 400
    assert meta["n_seeds_applied"] >= 401                       # counted, not truncated
    # the requested seed is NOT in the rendered list -- which is exactly why the membership test
    # must run over the full log
    assert {"label": "main", "seed": 555} not in meta["seeds_applied"]
    assert meta["seed_never_applied"] is False                  # found past the cap


def test_a_note_seed_overrides_and_rewrites_config(tmp_path):
    run = _run(common, tmp_path, "noteseed", seed=1)
    run.note_seed(99, source="derived:control_seed")
    cfg = _read(run, "config.json")
    assert cfg["seed"] == 99 and cfg["seed_source"] == "derived:control_seed"


@pytest.mark.skipif(not os.path.isdir(HF_CACHE), reason="repo-local HF cache not present")
def test_a_tokenizer_revision_is_a_resolved_commit_never_a_branch_name(tmp_path, old_common):
    """PRE-FIX: `note_model(revision="main")` wrote `model_revision: "main"` and NO tokenizer
    revision at all. A field named `*_revision` holding a branch name is not provenance: `main`
    moves, so the artifact looks pinned and is not."""
    old = _run(old_common, tmp_path, "old", seed=1)
    old.note_model(LLAMA, revision="main", tokenizer_id=LLAMA)
    old.finish(summary={}, ledger=old_common.FailureLedger())
    m_old = _read(old, "metadata.json")
    assert m_old["model_revision"] == "main"                           # drifty value...
    assert not any("tokenizer_revision" in k for k in m_old)           # ...and no tokenizer one

    new = _run(common, tmp_path, "new", seed=1)
    new.note_model(LLAMA, revision="main", tokenizer_id=LLAMA)
    led = common.FailureLedger(); led.ok(1)
    new.finish(summary={}, ledger=led)
    m = _read(new, "metadata.json")
    assert m["tokenizer_revision_requested"] == "main"
    sha = m["tokenizer_revision_resolved_commit"]
    assert sha and HEX40.match(sha) and sha != "main"
    assert m["tokenizer_revision_resolution_source"].startswith("hf_cache_ref:")
    assert m["tokenizer_revision_unresolved_reason"] is None
    assert m["model_revision_resolved_commit"] == sha
    # content-addressed provenance that cannot drift even if the ref moves
    assert m["tokenizer_files_sha16"] and len(m["tokenizer_files_sha16"]) == 16
    assert "tokenizer.json" in m["tokenizer_files_hashed"]
    # and the ref file on disk really is that commit
    ref = open(os.path.join(HF_CACHE, "models--meta-llama--Llama-3.1-8B-Instruct",
                            "refs", "main")).read().strip()
    assert ref == sha


def test_a_unresolvable_revision_is_null_plus_a_reason_not_a_plausible_string(tmp_path):
    """"Record what CAN be obtained and say so in the field name" — the one thing that must never
    happen is a null-looking-authoritative value."""
    run = _run(common, tmp_path, "unres", seed=1)
    run.note_model("nope/does-not-exist-anywhere", revision="main")
    led = common.FailureLedger(); led.ok(1)
    run.finish(summary={}, ledger=led)
    m = _read(run, "metadata.json")
    assert m["tokenizer_revision_resolved_commit"] is None
    assert m["model_revision_resolved_commit"] is None
    assert "no HF cache entry" in m["tokenizer_revision_unresolved_reason"]
    assert m["tokenizer_files_sha16"] is None
    # nothing anywhere in the record claims a revision it does not have
    for k, v in m.items():
        if k.endswith("_resolved_commit"):
            assert v is None or HEX40.match(str(v))


def test_a_loaded_object_snapshot_path_beats_the_cache_ref(tmp_path):
    """The authoritative source is where the bytes came from. A tokenizer loaded from an OLDER
    snapshot must not be recorded as whatever refs/main points at today — that is precisely the
    drift the resolved-commit field exists to exclude."""
    sha = "a" * 40
    snap = tmp_path / "hub" / "models--org--m" / "snapshots" / sha
    snap.mkdir(parents=True)
    (snap / "tokenizer.json").write_text('{"x":1}')
    refs = tmp_path / "hub" / "models--org--m" / "refs"
    refs.mkdir(parents=True)
    (refs / "main").write_text("b" * 40)

    class FakeTok:
        vocab_file = str(snap / "tokenizer.json")
        name_or_path = "org/m"

    os.environ["HF_HUB_CACHE"] = str(tmp_path / "hub")
    try:
        v = common.resolve_hf_revision("org/m", requested="main", obj=FakeTok())
        assert v["resolved_commit"] == sha                     # the object wins
        assert v["resolution_source"] == "loaded_snapshot_path"
        w = common.resolve_hf_revision("org/m", requested="main")
        assert w["resolved_commit"] == "b" * 40                # the ref, when nothing else
        assert w["resolution_source"] == "hf_cache_ref:main"
    finally:
        os.environ.pop("HF_HUB_CACHE", None)


def test_a_ambiguous_cache_refuses_to_guess(tmp_path):
    """Two snapshots, no ref: the honest answer is "unknown", not "probably the newer one"."""
    base = tmp_path / "hub" / "models--org--m" / "snapshots"
    (base / ("c" * 40)).mkdir(parents=True)
    (base / ("d" * 40)).mkdir(parents=True)
    os.environ["HF_HUB_CACHE"] = str(tmp_path / "hub")
    try:
        v = common.resolve_hf_revision("org/m")
        assert v["resolved_commit"] is None
        assert "2 snapshots cached" in v["unresolved_reason"]
    finally:
        os.environ.pop("HF_HUB_CACHE", None)


def test_a_tokenizer_files_sha16_is_content_addressed(tmp_path):
    d = tmp_path / "snap"
    d.mkdir()
    (d / "tokenizer.json").write_text('{"a":1}')
    (d / "tokenizer_config.json").write_text("{}")
    h1 = common.tokenizer_files_sha16(str(d))
    assert h1["tokenizer_files_hashed"] == ["tokenizer.json", "tokenizer_config.json"]
    (d / "tokenizer.json").write_text('{"a":2}')
    h2 = common.tokenizer_files_sha16(str(d))
    assert h2["tokenizer_files_sha16"] != h1["tokenizer_files_sha16"]
    assert common.tokenizer_files_sha16(None)["tokenizer_files_sha16"] is None
    assert common.tokenizer_files_sha16(str(tmp_path / "nope"))["tokenizer_files_sha16"] is None


# =========================================================================== #
# (b) bank identity: the comparison, run for real
# =========================================================================== #
BANK = os.path.join(REPO, "data", "boombness_prompts", "boombness_prompt_bank.jsonl")
BANK_META = os.path.join(REPO, "data", "boombness_prompts", "boombness_prompt_bank_meta.json")


@pytest.mark.skipif(not os.path.exists(BANK), reason="committed bank not present")
def test_b_the_two_functions_really_do_differ_on_the_committed_bank():
    """The check the project never performed: recompute BOTH hashes of the committed bank from
    scratch and compare them to what the bank meta records. They differ (which is why one key name
    could never have detected a mismatch), and the bank meta's legacy value is the ROWS one — so
    `bank_hashes(legacy=...)` is calibrated the right way round on each side."""
    import hashlib
    h, pairs = hashlib.sha256(), []
    with open(BANK, "rb") as f:
        for line in f:
            h.update(line)
            if not line.strip():
                continue
            r = json.loads(line)
            pairs.append((str(r["prompt_id"]), str(r["prompt_sha16"])))   # ids/hashes only
    file_sha, rows_sha = h.hexdigest()[:16], common.rows_sha16(pairs)
    # THE POINT OF THIS TEST is that the two functions compute DIFFERENT things from the same file --
    # that is the defect (`bank_content_sha16` meant file-bytes in a run metadata and row-content in a
    # bank meta, and nothing compared them). It is NOT about the specific digests.
    #
    # An earlier version pinned `file_sha == "71bea179345ed118"` and `rows_sha == "7002854cf834e9f9"`,
    # which were the 2352-row bank's values. Adding the `core2x2_slot3` power block (R-18) changed
    # both, and this test failed — correctly, and for a reason that had nothing to do with what it
    # is testing. Pinning a derived digest makes every legitimate bank change edit a magic string,
    # and the magic string gets pasted without thought the second time. The structural properties
    # are asserted instead, against the committed meta, which moves with the bank.
    assert file_sha != rows_sha, "the two hash functions must not agree, or the distinction is moot"
    assert len(file_sha) == len(rows_sha) == 16
    stats = json.load(open(BANK_META))["stats"]
    assert stats["n_rows"] == len(pairs), "bank meta row count disagrees with the bank file"
    assert stats.get("bank_rows_sha16", stats.get(common.LEGACY_BANK_HASH_KEY)) == rows_sha, \
        "the committed bank meta's rows hash does not match the bank on disk"
    # The legacy key is only present on banks written before `prompt_families` was fixed to emit the
    # unambiguous name. Assert it WHEN PRESENT (that is the calibration claim: on a bank meta the
    # legacy value means ROWS), and never require it — requiring it would fail every bank generated
    # after the fix, i.e. the test would punish the repair.
    if common.LEGACY_BANK_HASH_KEY in stats:
        assert stats[common.LEGACY_BANK_HASH_KEY] == rows_sha, \
            "on a bank meta the legacy key must carry the ROWS hash, not the file hash"
    else:
        assert stats["bank_rows_sha16"] == rows_sha
    assert common.bank_hashes(stats, legacy="rows")["bank_rows_sha16"] == rows_sha
    assert common.bank_hashes({common.LEGACY_BANK_HASH_KEY: file_sha},
                              legacy="file")["bank_file_sha16"] == file_sha


def test_b_row_count_mismatch_is_detected(old_common):
    """PRE-FIX: the verdict had no row-count check, so two same-hash-less artifacts over a
    1464-row and a 2352-row bank compared as merely `unknown`. 102 of the 114 bank-carrying
    artifacts record `bank_n_rows`, including legacy ones whose hashes cannot be compared at all."""
    run_meta = {"bank_path": "/b", "bank_n_rows": 1464}
    bank_meta = {"stats": {"n_rows": 2352, "bank_rows_sha16": "aaaaaaaaaaaaaaaa"}}
    v_old = old_common.compare_bank_hashes(run_meta, bank_meta, strict=True)   # no raise, no check
    assert v_old["mismatched"] == [] and "n_rows" not in v_old                 # the defect

    with pytest.raises(SystemExit):
        common.compare_bank_hashes(run_meta, bank_meta, strict=True)
    v = common.compare_bank_hashes(run_meta, bank_meta, strict=False)
    assert v["mismatched"] == ["bank_n_rows"] and v["ok"] is False
    assert v["n_rows"] == {"run": 1464, "bank": 2352}


def test_b_require_checked_refuses_an_uncertifiable_join(old_common):
    """PRE-FIX: `strict=True` raised only on a MISMATCH. A pre-2026-08-18 artifact, which records
    the file hash while the bank meta records the rows hash, could be joined to ANY bank and the
    strict guard stayed silent — 97 of 114 committed artifacts are in that state."""
    legacy_run = {"bank_path": "/b", common.LEGACY_BANK_HASH_KEY: "71bea179345ed118"}
    bank_meta = {"stats": {common.LEGACY_BANK_HASH_KEY: "7002854cf834e9f9"}}
    v_old = old_common.compare_bank_hashes(legacy_run, bank_meta, strict=True)
    assert v_old["checked"] == [] and v_old["ok"] is False        # nothing checked, nothing raised
    with pytest.raises(TypeError):
        old_common.compare_bank_hashes(legacy_run, bank_meta, require_checked=True)

    v = common.compare_bank_hashes(legacy_run, bank_meta, strict=True)     # default: still silent
    assert v["checked"] == [] and v["ok"] is False
    with pytest.raises(SystemExit) as e:
        common.compare_bank_hashes(legacy_run, bank_meta, require_checked=True)
    assert "asserted by prompt_id alone" in str(e.value)


def test_b_a_matching_join_still_passes_with_require_checked():
    v = common.compare_bank_hashes(
        {"bank_rows_sha16": "7002854cf834e9f9", "bank_file_sha16": "71bea179345ed118",
         "bank_n_rows": 2352},
        {"stats": {"bank_rows_sha16": "7002854cf834e9f9", "n_rows": 2352}},
        require_checked=True)
    assert v["ok"] is True and v["checked"] == ["bank_rows_sha16"]
    assert v["checked_weak"] == ["bank_n_rows"]


# =========================================================================== #
# (c) finish() cannot be bypassed
# =========================================================================== #
def test_c_finish_refuses_without_a_ledger(tmp_path):
    run = _run(common, tmp_path, "noledger", seed=1)
    with pytest.raises(ValueError):
        run.finish(summary={"x": 1})
    assert not os.path.exists(run.p("summary.json"))
    assert not os.path.exists(run.p("DONE.json"))


def test_c_finish_refuses_a_placeholder_before_writing_anything(tmp_path, old_common):
    """PRE-FIX one-of-two-paths: the ledger check was `ledger is None`, so ANY other object got
    past it — and `metadata.json` was written BEFORE `ledger.as_dict()` was ever called. The run
    therefore left a metadata.json behind and then died with an AttributeError."""
    old = _run(old_common, tmp_path, "old", seed=1)
    with pytest.raises(AttributeError):
        old.finish(summary={}, ledger=object())
    assert os.path.exists(old.p("metadata.json"))              # the defect: half-written run

    new = _run(common, tmp_path, "new", seed=1)
    with pytest.raises(TypeError):
        new.finish(summary={}, ledger=object())
    assert not os.path.exists(new.p("metadata.json"))
    assert not os.path.exists(new.p("summary.json"))


def test_c_summary_json_cannot_be_written_around_finish(tmp_path, old_common):
    """PRE-FIX: the class docstring says "a run's summary.json is only allowed to be written
    through RunDir.finish" and `write_json` wrote it happily — a run could publish an ASR with no
    failure ledger anywhere near it, which is exactly what plan §2.2 forbids."""
    old = _run(old_common, tmp_path, "old", seed=1)
    old.write_json("summary.json", {"asr": 0.9})               # the bypass, executed
    assert _read(old, "summary.json") == {"asr": 0.9}
    assert "failures" not in _read(old, "summary.json")

    new = _run(common, tmp_path, "new", seed=1)
    for name in ("summary.json", "metadata.json", "DONE.json", "ABORTED.json"):
        with pytest.raises(PermissionError):
            new.write_json(name, {"asr": 0.9})
        assert not os.path.exists(new.p(name))
    # a path-y spelling of the same file is refused too (identity, not a string prefix)
    with pytest.raises(PermissionError):
        new.write_json(os.path.join(".", "summary.json"), {})
    new.write_json("decision_gate.json", {"ok": True})         # ordinary files unaffected
    assert _read(new, "decision_gate.json") == {"ok": True}


def test_c_finish_cannot_run_twice(tmp_path):
    run = _run(common, tmp_path, "twice", seed=1)
    led = common.FailureLedger(); led.ok(1)
    run.finish(summary={"a": 1}, ledger=led)
    with pytest.raises(RuntimeError):
        run.finish(summary={"a": 2}, ledger=led)
    assert _read(run, "summary.json")["a"] == 1                # the first verdict survives


def test_c_finish_after_abort_refuses(tmp_path, old_common):
    """PRE-FIX: nothing stopped `finish()` after `abort()`, so a run that had already declared
    itself unusable could write DONE.json back on top and pass `require_done` — the T12 defect
    reintroduced through the other door."""
    led_old = old_common.FailureLedger(); led_old.ok(1)
    old = _run(old_common, tmp_path, "old", seed=1)
    old.abort("null judgements", summary={}, ledger=led_old)
    old.finish(summary={}, ledger=led_old)                     # no complaint at all
    assert os.path.exists(old.p("DONE.json")) and os.path.exists(old.p("ABORTED.json"))

    led = common.FailureLedger(); led.ok(1)
    new = _run(common, tmp_path, "new", seed=1)
    new.abort("null judgements", summary={}, ledger=led)
    with pytest.raises(RuntimeError):
        new.finish(summary={}, ledger=led)
    assert os.path.exists(new.p("ABORTED.json"))
    assert not os.path.exists(new.p("DONE.json"))


def test_c_abort_after_finish_is_recorded_and_loses_nothing(tmp_path):
    """THE STATE MACHINE IN THE OTHER DIRECTION (verifier fix, 2026-08-19). `finish` refused to run
    after `abort`; `abort` had no state check at all, so `finish()` then `abort()` silently
    replaced the summary.json that carried the FailureLedger with one whose `failures` is null,
    removed DONE.json, and left nothing on disk saying a finished verdict had existed. The abort
    must still WIN (T12) -- a late gate has to be able to retract a DONE -- but not silently."""
    run = _run(common, tmp_path, "af", seed=1)
    led = common.FailureLedger(); led.ok(3)
    run.finish(summary={"asr": 0.9}, ledger=led)
    assert os.path.exists(run.p("DONE.json"))

    run.abort("late gate: null_frac 0.9")
    assert os.path.exists(run.p("ABORTED.json"))
    assert not os.path.exists(run.p("DONE.json"))               # the abort still wins
    meta = _read(run, "metadata.json")
    assert meta["aborted_after_finish"] is True                 # ...and says so
    assert "retracted" in meta["retracted_verdict"]
    # the ledger-bearing summary is kept, not overwritten into nothing
    assert os.path.exists(run.p("summary.json.retracted_by_abort"))
    kept = json.load(open(run.p("summary.json.retracted_by_abort")))
    assert kept["failures"]["n_succeeded"] == 3 and kept["asr"] == 0.9


def test_c_abort_cannot_run_twice(tmp_path):
    """A second abort overwrote the first abort's reason -- and the first is the one that stopped
    the run."""
    run = _run(common, tmp_path, "aa", seed=1)
    run.abort("first reason")
    with pytest.raises(RuntimeError):
        run.abort("second reason")
    assert json.load(open(run.p("ABORTED.json")))["reason"] == "first reason"


def test_c_abort_without_a_ledger_states_the_absence(tmp_path, old_common):
    """PRE-FIX: `abort(ledger=None)` wrote a summary.json with no `failures` key at all, and
    `_ledger_counts` reads a missing block (`{}` -> falsy) exactly the way it reads a clean one."""
    old = _run(old_common, tmp_path, "old", seed=1)
    old.abort("boom")
    assert "failures" not in _read(old, "summary.json")
    assert old_common._ledger_counts(old.path) == {}           # "unknown" indistinguishable from ok

    new = _run(common, tmp_path, "new", seed=1)
    new.abort("boom")
    s = _read(new, "summary.json")
    assert s["failures"] is None
    assert "without a FailureLedger" in s["failures_absent_reason"]


# =========================================================================== #
# (d) clustered_proportion_ci, audited against scipy
# =========================================================================== #
np = pytest.importorskip("numpy")
st = pytest.importorskip("scipy.stats")


def _clustered(n_per, ps, seed=0):
    rng = np.random.default_rng(seed)
    flags, clusters = [], []
    for gi, p in enumerate(ps):
        flags += [int(x) for x in (rng.random(n_per) < p)]
        clusters += [f"dom{gi}"] * n_per
    return flags, clusters


def test_d_percentile_extraction_matches_numpy_quantile():
    """ARITHMETIC IS CLEAN — pinned, not assumed. At the default n_boot=4000 the order statistics
    this function picks agree bit-for-bit with np.quantile under every interpolation method."""
    flags, clusters = _clustered(45, [0.2, 0.25, 0.3, 0.35, 0.4, 0.45], seed=3)
    lo, hi, G, diag = common.clustered_proportion_ci(flags, clusters, return_diag=True)
    assert G == 6 and diag["interval_source"] == "cluster_percentile_bootstrap"

    import random as _r
    by = {}
    for f, c in zip(flags, clusters):
        by.setdefault(c, []).append(float(f))
    keys = sorted(by, key=str)
    rng = _r.Random(20260818)
    means = []
    for _ in range(4000):
        tot = [v for _ in range(6) for v in by[keys[rng.randrange(6)]]]
        means.append(sum(tot) / len(tot))
    for method in ("inverted_cdf", "linear", "lower", "higher", "nearest", "midpoint"):
        a, b = np.quantile(means, [0.025, 0.975], method=method)
        assert abs(lo - a) < 1e-12 and abs(hi - b) < 1e-12, method


def test_d_cluster_resampling_is_uniform_against_scipy_chisquare():
    import random as _r
    rng = _r.Random(20260818)
    counts = [0] * 6
    for _ in range(200000):
        counts[rng.randrange(6)] += 1
    assert st.chisquare(counts).pvalue > 0.01


def test_d_wilson_ci_matches_scipy_on_a_grid():
    """scipy ground truth. `analyze_g8.t_sf` was wrong for a year; nothing hand-rolled here is
    trusted until it has been diffed."""
    worst = 0.0
    for n in list(range(1, 61)) + [96, 179, 270, 495]:
        for k in range(0, n + 1):
            lo, hi = common.wilson_ci(k, n)
            ref = st.binomtest(k, n).proportion_ci(method="wilson")
            worst = max(worst, abs(lo - ref.low), abs(hi - ref.high))
    assert worst < 1e-9, worst
    assert all(math.isnan(x) for x in common.wilson_ci(0, 0))


def test_d_length_mismatch_raises(old_common):
    """PRE-FIX: `zip` truncated and the function returned an interval over a population nobody
    chose, saying nothing."""
    flags = [1] * 135 + [0] * 135
    clusters = [f"d{i // 45}" for i in range(269)]
    lo, hi, G = old_common.clustered_proportion_ci(flags, clusters)
    assert G == 6 and not math.isnan(lo)                       # the defect: a silent answer
    with pytest.raises(ValueError) as e:
        common.clustered_proportion_ci(flags, clusters)
    assert "270 flags but 269 cluster labels" in str(e.value)


def test_d_nan_outcome_was_counted_as_an_attack_success(old_common):
    """PRE-FIX and worse than it sounds: `1.0 if nan else 0.0` is 1.0, because `bool(nan)` is
    True. A prompt whose judge score is NaN — an unmeasured prompt — was counted as an ATTACK
    SUCCESS and inflated the ASR."""
    nan = float("nan")
    flags = [nan] * 90 + [0] * 90
    clusters = ["a"] * 90 + ["b"] * 90
    lo, hi, G = old_common.clustered_proportion_ci(flags, clusters)
    assert (lo, hi) == (0.0, 1.0)                              # 0.0 or 1.0 per cluster draw
    with pytest.raises(ValueError) as e:
        common.clustered_proportion_ci(flags, clusters)
    assert "NaN" in str(e.value) and "attack SUCCESS" in str(e.value)


def test_d_none_outcome_was_counted_as_a_failure(old_common):
    """PRE-FIX: `r.get("malicious_at_0.5")` returning None became 0.0 — an unmeasured prompt
    counted as a non-attack. Plan §2.2: it belongs in the FailureLedger, not in the denominator."""
    flags = [None] * 45 + [1] * 45 + [1] * 90
    clusters = ["a"] * 90 + ["b"] * 90
    lo, hi, G = old_common.clustered_proportion_ci(flags, clusters)
    assert not math.isnan(lo)                                  # the defect: a silent answer
    with pytest.raises(ValueError) as e:
        common.clustered_proportion_ci(flags, clusters)
    assert "FailureLedger" in str(e.value)
    with pytest.raises(ValueError):
        common.clustered_proportion_ci([0.5] * 90 + [1] * 90, clusters)   # not a 0/1 outcome


@pytest.mark.parametrize("k,n,per_cluster", [
    (0, 36, [0, 0, 0, 0, 0, 0]),          # judge/len_D_20260818_130635  benign_remap  -> [0,0]
    (72, 72, [12, 12, 12, 12, 12, 12]),   # judge/q3_C20_20260818_174110 role=tool     -> [1,1]
    (66, 96, [11, 11, 11, 11, 11, 11]),   # judge/q3_C20 n_examples=0  ASR .6875 -> [.6875,.6875]
])
def test_d_zero_width_intervals_on_disk_are_no_longer_returned(k, n, per_cluster, old_common):
    """PRE-FIX, AND IT IS IN THE COMMITTED ARTIFACTS: 10 of the 340 `ci95_domain_clustered` fields
    under outputs/boombness are zero-width. A cluster bootstrap can only re-weight clusters, so
    when every cluster has the same proportion — in particular at 0 or 1 — every replicate is
    identical and the "95% interval" collapses to a point. scipy's exact interval for k=0,n=36 is
    [0, 0.0974]; a zero-width 95% interval is not conservative, it is false."""
    per = n // len(per_cluster)
    flags, clusters = [], []
    for gi, kk in enumerate(per_cluster):
        flags += [1] * kk + [0] * (per - kk)
        clusters += [f"dom{gi}"] * per

    lo0, hi0, _ = old_common.clustered_proportion_ci(flags, clusters)
    assert lo0 == hi0                                          # the defect, executed

    lo, hi, G, diag = common.clustered_proportion_ci(flags, clusters, return_diag=True)
    assert diag["degenerate_bootstrap"] is True
    assert diag["interval_source"].startswith("wilson_iid_fallback")
    assert hi > lo
    ref = st.binomtest(k, n).proportion_ci(method="wilson")
    assert abs(lo - ref.low) < 1e-9 and abs(hi - ref.high) < 1e-9
    exact = st.binomtest(k, n).proportion_ci(method="exact")    # sanity: same order of magnitude
    assert abs(hi - exact.high) < 0.02 and abs(lo - exact.low) < 0.02


def test_d_non_degenerate_intervals_are_bit_identical_to_the_pre_fix_code(old_common):
    """The 330 committed `ci95_domain_clustered` fields that are NOT degenerate must not move.
    This is the regression half of the fix: only the 10 zero-width cells change."""
    n_checked = 0
    for seed in range(25):
        rng = np.random.default_rng(seed)
        ps = list(rng.uniform(0.05, 0.95, size=int(rng.integers(2, 9))))
        flags, clusters = _clustered(int(rng.integers(8, 46)), ps, seed=seed)
        a = old_common.clustered_proportion_ci(flags, clusters)
        b, diag = common.clustered_proportion_ci(flags, clusters, return_diag=True)[:3], \
            common.clustered_proportion_ci(flags, clusters, return_diag=True)[3]
        if diag["degenerate_bootstrap"]:
            continue
        assert a == b, (seed, a, b)
        n_checked += 1
    assert n_checked >= 20


def test_d_small_cluster_count_caveat_is_recorded():
    """The measured limitation, made a field rather than a docstring claim: at G=6 the coverage of
    this nominal-95% interval is ~0.84-0.86 (Monte-Carlo, superpopulation estimand)."""
    flags, clusters = _clustered(45, [0.2, 0.3, 0.4, 0.5, 0.6, 0.7], seed=5)
    _, _, G, diag = common.clustered_proportion_ci(flags, clusters, return_diag=True)
    assert G == 6 and "0.84-0.86" in diag["coverage_caveat"]
    flags16, clusters16 = _clustered(20, [0.3] * 16, seed=5)
    _, _, G16, d16 = common.clustered_proportion_ci(flags16, clusters16, return_diag=True)
    assert G16 == 16 and d16["coverage_caveat"] is None


def test_d_fewer_than_two_clusters_is_undefined_not_zero():
    lo, hi, G, diag = common.clustered_proportion_ci([1, 0, 1], ["a"] * 3, return_diag=True)
    assert math.isnan(lo) and math.isnan(hi) and G == 1
    assert diag["interval_source"] == "undefined:fewer_than_2_clusters"


def test_d_return_signature_is_unchanged_for_existing_callers():
    """`judge_boombness` and `analyze_steering` unpack exactly three values."""
    flags, clusters = _clustered(30, [0.3, 0.4, 0.5], seed=1)
    lo, hi, G = common.clustered_proportion_ci(flags, clusters)
    assert G == 3 and 0.0 <= lo <= hi <= 1.0


# --------------------------------------------------------------------------------------------- #
# E10 / severity (2026-08-19). Giving the external banks a `*_meta.json` turned an inert guard live
# — and immediately produced a `bank_file_sha16` mismatch on every pre-R-14 run, because R-14's fix
# added `final_query_text` to every external row. Under the original all-mismatches-are-fatal rule
# that would have made every pre-R-14 generation permanently unjudgeable against the corrected bank:
# the guard would have blocked exactly the re-judging that fixed the defect it exists to prevent.
# --------------------------------------------------------------------------------------------- #
import pytest as _pytest


def _run_meta(file_sha, rows_sha, n=179):
    return {"bank_path": "/x/clearharm_179.jsonl", "bank_file_sha16": file_sha,
            "bank_rows_sha16": rows_sha, "bank_n_rows": n}


def _bank_meta(file_sha, rows_sha, n=179):
    return {"stats": {"bank_file_sha16": file_sha, "bank_rows_sha16": rows_sha, "n_rows": n}}


def test_file_only_mismatch_is_BENIGN_and_does_not_raise_under_strict():
    """Same rows, rewritten file. Must be accepted, loudly."""
    v = common.compare_bank_hashes(_run_meta("aaaa111122223333", "rrrr111122223333"),
                                   _bank_meta("bbbb444455556666", "rrrr111122223333"),
                                   strict=True)
    assert v["mismatched_fatal"] == []
    assert v["mismatched_benign"] == ["bank_file_sha16"]
    assert "benign_note" in v


def test_rows_mismatch_is_FATAL_under_strict():
    """THE GUARD. Different prompts is retraction R1 and must still refuse."""
    with _pytest.raises(SystemExit) as e:
        common.compare_bank_hashes(_run_meta("aaaa111122223333", "rrrr111122223333"),
                                   _bank_meta("aaaa111122223333", "SSSS999988887777"),
                                   strict=True)
    assert "REFUSING" in str(e.value)


def test_row_count_mismatch_is_also_FATAL():
    """n_rows is a weak identity but a difference in it is still a different bank."""
    with _pytest.raises(SystemExit):
        common.compare_bank_hashes(_run_meta("aaaa111122223333", "rrrr111122223333", n=179),
                                   _bank_meta("aaaa111122223333", "rrrr111122223333", n=495),
                                   strict=True)


def test_the_external_banks_now_ship_a_meta_file():
    """E10: without this the guard is inert for exactly the banks R-14 regenerated."""
    for name in ("clearharm_179", "advbench_heldout_495"):
        p = os.path.join(REPO, "data", "boombness_prompts", "external", f"{name}_meta.json")
        assert os.path.exists(p), f"{name} has no *_meta.json; compare_bank_hashes cannot run"
        st = json.load(open(p))["stats"]
        assert st["bank_file_sha16"] and st["bank_rows_sha16"] and st["n_rows"]
        assert st["bank_file_sha16"] != st["bank_rows_sha16"], \
            "the two hashes must be computed differently, or the distinction is decorative"
