"""ADVERSARIAL VERIFIER round on the 2026-08-19 silent-failure patch.

Four defects the patch itself shipped. Each test below FAILS against the patched-but-defective
source (a snapshot of it is loaded out of the working tree by `_defective`, because the patch was
never committed and `git show HEAD:` therefore returns the PRE-patch file, not the defective one).

  V1  extract_boombness.validate_fit_identity  downgraded a `bank_file_sha16` MISMATCH to
      non-fatal UNCONDITIONALLY. Its own justification ("same prompts, different bytes") is
      `bank_rows_sha16` agreeing, and it never checked whether it had. On an EXTERNAL bank
      (plan 14 / ClearHarm / AdvBench) the rows hash is None on BOTH sides by construction, so
      `fit on ClearHarm -> score on AdvBench` passed strict=True with an empty problems list.
  V2  the same function could not see `--limit`. `RunDir.note_bank` hashes the bank FILE and
      `--limit` truncates the rows after it, so a 24-row smoke fit over the 2352-row bank stamps
      the FULL bank's rows hash and a later full score run is certified `checked` against it.
      Both committed smoke extract runs are `limit: 24` on that bank.
  V3  the bank identity was read as `getattr(run, "_extra_meta", {})` -- a private attribute of a
      class in a file this module does not own -- defaulting to `{}`, i.e. to "every field
      unknown", on a rename. A guard that dies quietly on an attribute rename is the sprint's
      dead-guard shape keyed on an incidental property.
  V4  coherence_gate.assess listed the three ratio criteria in `checks_applied` even when every
      one of them is nan and therefore inert.

Responsible handling: every string here is synthetic and written by this file. No gens.jsonl,
results.jsonl or bank prompt text is read.
"""
import importlib.util
import json
import os
import sys

import pytest

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRCB = os.path.join(REPO, "src", "boombness")
sys.path.insert(0, SRCB)
sys.path.insert(0, os.path.join(REPO, "doublespeak_causality"))

import torch  # noqa: E402

import coherence_gate            # noqa: E402
import extract_boombness         # noqa: E402

# The patched-but-defective snapshot taken before this verifier edited anything. Present only in
# the verifier's scratchpad; the tests that need it skip rather than fail when it is gone, so this
# file stays green on a fresh checkout while still being an executed demonstration today.
DEFECTIVE_DIR = os.environ.get("BOOMBNESS_DEFECTIVE_SNAPSHOT", "")


def _defective(modname: str, filename: str):
    src = os.path.join(DEFECTIVE_DIR, filename)
    if not DEFECTIVE_DIR or not os.path.exists(src):
        pytest.skip("no patched-but-defective snapshot on this checkout "
                    "(set BOOMBNESS_DEFECTIVE_SNAPSHOT)")
    spec = importlib.util.spec_from_file_location(modname, src)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------- #
# V1 / V2 — validate_fit_identity
# --------------------------------------------------------------------------- #
MODEL = "meta-llama/Llama-3.1-8B-Instruct"


def _payload(**meta):
    m = {"position": "codeword_last", "model": MODEL, "split_fitted_on": "dev"}
    m.update(meta)
    return {"layers": [0, 1], "d_surface": {0: torch.ones(4), 1: torch.ones(4)},
            "gap": {}, "n_per_cell": {}, "meta": m}


def _validate(mod, payload, bank, dtype="torch.bfloat16", strict=True, **kw):
    return mod.validate_fit_identity(payload, path="fake.pt", model=MODEL,
                                     position="codeword_last", layers=[0, 1],
                                     bank_meta=bank, dtype=dtype, strict=strict, **kw)


# An external harmful bank (plan 14): no per-row prompt_sha16, so note_bank records
# bank_rows_sha16=None. TWO DIFFERENT such banks.
EXT_CLEARHARM = {"bank_path": "/banks/clearharm.jsonl", "bank_rows_sha16": None,
                 "bank_file_sha16": "cccccccccccccccc", "n_bank_rows_used": 179}
EXT_ADVBENCH = {"bank_path": "/banks/advbench.jsonl", "bank_rows_sha16": None,
                "bank_file_sha16": "aaaaaaaaaaaaaaaa", "n_bank_rows_used": 179}
# The sprint bank, hashed both ways.
SPRINT = {"bank_path": "/banks/sprint.jsonl", "bank_rows_sha16": "7002854cf834e9f9",
          "bank_file_sha16": "71bea179345ed118", "n_bank_rows_used": 2352}
SPRINT_RESERIALISED = {**SPRINT, "bank_file_sha16": "ffffffffffffffff"}


def _stamp(bank):
    """The meta a fit run over `bank` writes into its payload."""
    return {"bank_rows_sha16": bank["bank_rows_sha16"],
            "bank_file_sha16": bank["bank_file_sha16"],
            "n_bank_rows_used": bank["n_bank_rows_used"],
            "fit_dtype": "torch.bfloat16"}


def test_v1_a_cross_external_bank_join_is_now_FATAL():
    with pytest.raises(SystemExit) as e:
        _validate(extract_boombness, _payload(**_stamp(EXT_CLEARHARM)), EXT_ADVBENCH)
    assert "bank_file_sha16" in str(e.value)


def test_v1_defective_source_accepted_the_cross_external_bank_join():
    """THE DEFECT, EXECUTED. strict=True, two demonstrably different bank files, no exception."""
    old = _defective("defective_extract", "extract_boombness.py")
    v = _validate(old, _payload(**_stamp(EXT_CLEARHARM)), EXT_ADVBENCH)
    assert v["problems"] == []                       # survived strict=True
    assert "bank_file_sha16" in v["checked"]         # and was recorded as CHECKED
    assert v.get("problems_nonfatal")                # the mismatch existed and was downgraded


def test_v1_a_re_serialisation_is_still_only_non_fatal():
    """The downgrade must survive for the case it was written for: same rows, different bytes."""
    v = _validate(extract_boombness, _payload(**_stamp(SPRINT)), SPRINT_RESERIALISED)
    assert v["problems"] == []
    assert v["n_nonfatal_identity_problems"] == 1
    assert "bank_rows_sha16" in v["checked"] and "bank_file_sha16" in v["checked"]


def test_v1_a_rows_hash_mismatch_is_still_fatal():
    with pytest.raises(SystemExit) as e:
        _validate(extract_boombness, _payload(**_stamp(SPRINT)),
                  {**SPRINT, "bank_rows_sha16": "0123456789abcdef"})
    assert "bank_rows_sha16" in str(e.value)


def test_v1_a_fully_matching_external_bank_still_passes():
    v = _validate(extract_boombness, _payload(**_stamp(EXT_CLEARHARM)), EXT_CLEARHARM)
    assert v["problems"] == [] and v["n_nonfatal_identity_problems"] == 0
    assert "bank_rows_sha16" in v["unknown_identity"]     # never counted as agreement


def test_v1_cross_bank_is_expressible_and_recorded_not_hidden():
    """A guard with no way to say "yes, on purpose" gets a bypass hack bolted on. The committed
    run roleblk_20260818_114425_1408585 is exactly this: --stage score --fit-dir <2x2 fit>
    --bank role_style_block.jsonl. Declaring it must RECORD it, never silence it."""
    v = _validate(extract_boombness, _payload(**_stamp(EXT_CLEARHARM)), EXT_ADVBENCH,
                  allow_cross_bank=True)
    assert v["problems"] == []
    assert v["cross_bank_fit"] is True and v["bank_identity_mismatch"] is True
    assert any("DECLARED" in m for m in v["problems_nonfatal"])


def test_v1_declaring_cross_bank_does_not_relax_model_position_or_dtype():
    """The opt-in must downgrade the BANK and nothing else, or it becomes a --skip-all flag."""
    for kw in ({"position": "last"}, {"model": "Qwen/Qwen3-14B"},
               {"fit_dtype": "torch.float32"}):
        m = _stamp(EXT_CLEARHARM); m.update(kw)
        with pytest.raises(SystemExit):
            _validate(extract_boombness, _payload(**m), EXT_ADVBENCH, allow_cross_bank=True)


def test_v2_a_limited_fit_consumed_by_a_full_score_is_FATAL():
    """`--limit 24` over the 2352-row bank stamps the FULL file's rows hash; only the row COUNT
    can see it. smoke_20260816_183101_1000604 and smoke_20260816_183822_1001753 are that run."""
    smoke = {**SPRINT, "n_bank_rows_used": 24}
    with pytest.raises(SystemExit) as e:
        _validate(extract_boombness, _payload(**_stamp(smoke)), SPRINT)
    assert "n_bank_rows_used" in str(e.value)


def test_v2_defective_source_certified_the_limited_fit_as_a_bank_match():
    old = _defective("defective_extract2", "extract_boombness.py")
    smoke = {**SPRINT, "n_bank_rows_used": 24}
    v = _validate(old, _payload(**_stamp(smoke)), SPRINT)
    assert v["problems"] == []
    assert "bank_rows_sha16" in v["checked"]      # affirmatively certified, on 24 of 2352 rows


def test_v2_a_row_count_difference_across_DIFFERENT_banks_is_not_fatal():
    """Two different banks are expected to differ in size; the size is not the finding. Without
    this the cross-bank opt-in would still die on the row count and be useless."""
    v = _validate(extract_boombness, _payload(**_stamp(EXT_CLEARHARM)),
                  {**EXT_ADVBENCH, "n_bank_rows_used": 495}, allow_cross_bank=True)
    assert v["problems"] == []
    assert any("expected, because the bank identity already differs" in m
               for m in v["problems_nonfatal"])


def test_v2_the_limit_mixup_is_fatal_EVEN_WITH_the_cross_bank_opt_in():
    """--allow-cross-bank-fit must not become a way to smuggle a 24-of-2352 smoke fit in."""
    smoke = {**SPRINT, "n_bank_rows_used": 24}
    with pytest.raises(SystemExit) as e:
        _validate(extract_boombness, _payload(**_stamp(smoke)), SPRINT, allow_cross_bank=True)
    assert "n_bank_rows_used" in str(e.value)


def test_v2_equal_row_counts_are_not_a_problem():
    v = _validate(extract_boombness, _payload(**_stamp(SPRINT)), SPRINT)
    assert v["problems"] == [] and "n_bank_rows_used" in v["checked"]


def test_v2_an_unrecorded_row_count_is_unknown_not_agreement():
    m = _stamp(SPRINT)
    m.pop("n_bank_rows_used")
    v = _validate(extract_boombness, _payload(**m), SPRINT)
    assert v["problems"] == []
    assert "n_bank_rows_used" in v["unknown_identity"]
    assert "n_bank_rows_used" not in v["checked"]


# --------------------------------------------------------------------------- #
# V3 — the private-attribute read
# --------------------------------------------------------------------------- #
class _RunWithMeta:
    def __init__(self, meta):
        self._extra_meta = dict(meta)


class _RunRenamedAttr:
    """A RunDir whose private meta store has been renamed -- the file is owned by another agent."""
    def __init__(self, meta):
        self._meta = dict(meta)


def test_v3_a_renamed_private_meta_store_is_a_hard_stop():
    with pytest.raises(SystemExit) as e:
        extract_boombness.read_run_bank_meta(_RunRenamedAttr({"bank_path": "/b.jsonl"}),
                                             "/b.jsonl")
    assert "_extra_meta" in str(e.value)


def test_v3_note_bank_having_recorded_nothing_is_a_hard_stop():
    with pytest.raises(SystemExit) as e:
        extract_boombness.read_run_bank_meta(_RunWithMeta({}), "/b.jsonl")
    assert "bank_path" in str(e.value)


def test_v3_a_normal_run_reads_back_cleanly():
    out = extract_boombness.read_run_bank_meta(
        _RunWithMeta({"bank_path": "/b.jsonl", "bank_file_sha16": "f" * 16,
                      "bank_rows_sha16": None, "bank_n_rows": 179}), "/b.jsonl")
    assert out["bank_path"] == "/b.jsonl" and out["bank_rows_sha16"] is None


def test_v3_defective_source_silently_returned_all_unknown():
    """THE DEFECT, EXECUTED: the inline getattr default turned a renamed attribute into a payload
    stamped with `bank_rows_sha16: None`, i.e. into `unknown_identity` on every field, with no
    error anywhere."""
    old = _defective("defective_extract3", "extract_boombness.py")
    assert not hasattr(old, "read_run_bank_meta")
    run = _RunRenamedAttr({"bank_path": "/b.jsonl"})
    quiet = {k: getattr(run, "_extra_meta", {}).get(k)
             for k in ("bank_path", "bank_file_sha16", "bank_rows_sha16", "bank_n_rows")}
    assert quiet == {"bank_path": None, "bank_file_sha16": None,
                     "bank_rows_sha16": None, "bank_n_rows": None}
    v = _validate(old, _payload(**{k: v for k, v in _stamp(SPRINT).items()}), quiet)
    assert v["problems"] == []
    assert v["n_unknown_identity_fields"] == 2       # both bank hashes silently "unrecorded"


# --------------------------------------------------------------------------- #
# V4 — coherence_gate checks_applied
# --------------------------------------------------------------------------- #
LONG_OK = ("The mechanism proceeds through several distinct stages and each one contributes a "
           "different measurable quantity to the final outcome under study here today.")


def _run_dir(tmp_path, name, texts, truncated=False):
    d = tmp_path / name
    d.mkdir()
    with open(d / "gens.jsonl", "w") as f:
        for i, t in enumerate(texts):
            f.write(json.dumps({"prompt_id": f"p{i}", "condition": "natural_doublespeak",
                                "generation": t}) + "\n")
    with open(d / "results.jsonl", "w") as f:
        for i in range(len(texts)):
            f.write(json.dumps({"prompt_id": f"p{i}", "condition": "natural_doublespeak",
                                "readout": "generation", "gen_truncated": truncated}) + "\n")
    return str(d)


def test_v4_nan_ratios_are_reported_as_skipped_not_applied(tmp_path):
    a = coherence_gate.assess(_run_dir(tmp_path, "allshort", ["no."] * 50))
    assert a["coherent"] is False
    assert a["checks_applied"] == ["sample", "truncated_frac"]
    assert any("nan" in s for s in a["checks_skipped"])


def test_v4_defective_source_claimed_three_inert_checks_had_been_applied(tmp_path):
    old = _defective("defective_coherence", "coherence_gate.py")
    a = old.assess(_run_dir(tmp_path, "allshort2", ["no."] * 50))
    assert a["uniq_word_ratio"] != a["uniq_word_ratio"]        # nan
    assert a["checks_applied"] == ["sample", "uniq_word_ratio", "trigram_repeat",
                                   "top_word_frac", "truncated_frac"]
    assert a["checks_skipped"] == []


def test_v4_a_healthy_run_still_lists_every_criterion(tmp_path):
    a = coherence_gate.assess(_run_dir(tmp_path, "healthy", [LONG_OK] * 60))
    assert a["coherent"] is True
    assert a["checks_applied"] == ["sample", "uniq_word_ratio", "trigram_repeat",
                                   "top_word_frac", "truncated_frac"]
    assert a["checks_skipped"] == []
