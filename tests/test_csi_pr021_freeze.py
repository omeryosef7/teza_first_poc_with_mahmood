"""PR-CSI-021's freeze script: it must REFUSE to emit a prereg naming anything that does not exist.

S-167c is the rule ("do not freeze a prereg naming anything that does not exist") and this sprint
has broken it before. Here it is enforced in CODE, and these tests drive every refusal.
"""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
SCRIPT = os.path.join(ROOT, "scripts", "gates", "dcs_csi_pr021_freeze.py")
ART = os.path.join(ROOT, "reports", "DCS_CSI_RUNG2_TRAIN_basket_full.json")


def _code():
    """Source with comment lines stripped -- S-385: a file that documents its own history always
    contains the string naming the defect it removed."""
    out = []
    for line in open(SCRIPT, encoding="utf-8").read().splitlines():
        out.append("" if line.lstrip().startswith("#") else line.split("#")[0])
    return "\n".join(out)


def test_it_refuses_without_the_train_measurement():
    """The power table is COMPUTED from the train artefact. Emitting a prereg that names a power
    table it cannot compute is exactly S-167c's error."""
    if os.path.exists(ART):
        pytest.skip("the train artefact exists; this refusal cannot be driven without moving it")
    r = subprocess.run([PY, SCRIPT], capture_output=True, text=True)
    both = r.stdout + r.stderr
    assert r.returncode != 0
    assert "REFUSING TO EMIT" in both and "S-167c" in both, both[:400]


def test_it_refuses_a_SMOKE_artefact_as_a_power_source(tmp_path, monkeypatch):
    """A power table from a limited, domain-contiguous sample is not a power table. S-395's smoke
    was 3 prompts over ONE domain and carries IS_SMOKE: true."""
    code = _code()
    assert 'art.get("⚠ IS_SMOKE")' in code, "the smoke flag is not checked"
    assert 'art.get("split") != "train"' in code, "the discovery split is not enforced"
    assert '(670, 67)' in code, "the train population is not pinned"


def test_the_STATISTIC_is_IMPORTED_not_reimplemented():
    """🔴 S-389/S-350. The rungs are only comparable if the statistic is the SAME one applied to a
    DIFFERENT quantity -- and S-350 measured that two 'independent implementations' of this very
    statistic agreed ONLY at M=K, a difference that would have published a PASS against a prereg
    saying it could not certify. The way to make two things identical is to make them one thing."""
    code = _code()
    assert "dcs_csi_pr020_freeze.py" in code, "the statistic is no longer shared with PR-CSI-020"
    # ⚠ only the three the FREEZE uses. perm_tail and certifies belong to the READ and are
    # exercised by dcs_csi_pr016_argmax_test.py; asserting them here caught an earlier docstring
    # that claimed all five were imported by this file, which was an overclaim.
    for fn in ("binom_ge", "power_mc", "n_assign"):
        assert "m.%s" % fn in code or "m.%s(" % fn in code, (
            "%s is not taken from the PR-CSI-020 module -- it may have been reimplemented" % fn)
    # and it must not define its own copies
    for fn in ("def binom_ge", "def perm_tail", "def power_mc", "def n_assign", "def certifies"):
        assert fn not in code, "%s is REDEFINED here; it must be imported (S-350)" % fn


def test_the_direct_path_limitation_is_in_BOTH_prohibition_lists():
    """R35-A finding 6, unresolved BY DESIGN: this is a direct-path attribution that ignores 17-25
    blocks of downstream processing. It must fence a POSITIVE (do not claim total contribution) and
    a NULL (a necessary cell can have near-zero direct projection), because it cuts both ways."""
    code = _code()
    i = code.find("MUST_NOT_BE_SAID_IF_POSITIVE")
    j = code.find("MUST_NOT_BE_SAID_IF_NULL")
    k = code.find("VOID_CONDITIONS")
    assert 0 < i < j < k, "the prohibition lists are missing or out of order"
    assert "DIRECT-PATH" in code[i:j], "a POSITIVE is not fenced against the direct-path limit"
    assert "direct-path" in code[j:k], "a NULL is not fenced against the direct-path limit"


def test_it_fences_the_rung_confusion_AM34_exists_to_prevent():
    code = _code()
    i, j = code.find("MUST_NOT_BE_SAID_IF_POSITIVE"), code.find("MUST_NOT_BE_SAID_IF_NULL")
    # ⚠ S-397: this phrase is written CONTIGUOUS in the source on purpose. Python's implicit
    # string concatenation means a quote split across lines exists at RUNTIME but not in the
    # source a grep sees -- which is how this test first failed against text that was present.
    assert "readable at a site without being used there" in code[i:j], (
        "the ladder's own separability warning is not quoted where a positive would be written up")
    k = code.find("VOID_CONDITIONS")
    assert "D40" in code[j:k], "a NULL is not fenced against being read as retracting rung 1"


def test_K_is_fixed_and_the_head_set_is_disclosed_as_NOT_held_out():
    code = _code()
    assert "K_IS_FIXED_AT_8" in code
    assert "NOT held out" in code, "the rung-1 selection of the head set is not disclosed"


def test_it_refuses_without_a_READER_and_checks_that_FIRST():
    """🔴 S-398. The S-167c enforcement was PARTIAL: this script refused when the POWER SOURCE was
    missing and then emitted a prereg naming NO READ PATH. A preregistration must say how it will
    be read, and the rung-1 reader cannot substitute -- pr016 requires a CENSUS report
    (ON_PROTOCOL, GATE_0_and_identity.per_arm, E, ci95, CELL_FAMILY) and a rung-2 artefact has
    none of those.

    The check is ordered FIRST because an existence test is cheaper than reading and validating
    the train artefact (R35-C F14: every cheap refusal before the expensive one)."""
    code = _code()
    assert "READER = " in code, "the prereg no longer names a reader"
    assert '"reader": READER' in code, "the reader is not written into the prereg"
    assert '"reader_md5"' in code, "the reader is named but not pinned by content"
    i_reader = code.find("os.path.exists(reader_path)")
    i_art = code.find("os.path.exists(art_path)")
    assert 0 < i_reader < i_art, (
        "the reader check must come BEFORE the train-artefact check -- cheap refusals first")
    # ⚠ S-403: this test USED to drive the refusal by running the script -- valid while the
    # reader was absent, and the commit hook correctly went red the moment the reader was written,
    # because a precondition failure cannot be demonstrated once the precondition holds. The
    # refusal PATH is asserted by source (above); what is driven now is the live behaviour, which
    # is that both preconditions exist and the script EMITS. Deleting the test instead would have
    # thrown away the ordering guarantee, which is the part that still bites.
    assert "REFUSING TO EMIT" in code, "the refusal was removed rather than satisfied"
    assert "cannot substitute" in code, "the refusal no longer says why pr016 cannot be used"
    # ⚠⚠ S-405: this used to run the freeze with NO --out, so every test run RE-EMITTED the
    # frozen preregistration in place -- which is how the committed prereg came to carry a
    # reader_md5 naming a reader that no longer existed, and how the read recipe's md5 pin went
    # stale. A test must never regenerate a frozen artefact.
    import tempfile
    _td = tempfile.mkdtemp()
    r = subprocess.run([PY, SCRIPT, "--out", os.path.join(_td, "pr021_test_emission.json")],
                       capture_output=True, text=True)
    both = r.stdout + r.stderr
    if os.path.exists(os.path.join(ROOT, "scripts", "dcs_csi_pr021_rung2_read.py")):
        assert r.returncode == 0, "both preconditions exist but the freeze did not emit:\n" + both
        assert "[pr021] wrote " in both, both[:300]   # S-405: emitted to a TEMP path
    else:
        assert r.returncode != 0 and "S-398" in both, both[:300]


def test_the_freeze_REFUSES_to_overwrite_a_frozen_prereg():
    """🔴 S-405. This script had NO overwrite guard, and a test in this very file ran it with no
    --out -- so every test run, including the commit hook's, RE-EMITTED the preregistration in
    place. The committed prereg ended up carrying a reader_md5 naming a reader version that no
    longer existed, and the frozen read recipe's md5 pin went stale, because the file changed
    underneath both after they were written.

    A preregistration is the one artefact in this sprint that must not be regenerable by accident.
    """
    code = _code()
    assert '"--force"' in code, "the overwrite guard was removed"
    assert 'os.path.exists(outp) and not a.force' in code, "the guard no longer checks existence"
    assert '"--out"' in code, "tests cannot redirect the emission away from the frozen path"
    out = os.path.join(ROOT, "configs", "dcs_csi_pr021_rung2_decode_basket_validation.json")
    if not os.path.exists(out):
        pytest.skip("no frozen prereg in this checkout")
    r = subprocess.run([PY, SCRIPT], capture_output=True, text=True)
    both = r.stdout + r.stderr
    assert r.returncode != 0, "the freeze overwrote a frozen preregistration without --force"
    assert "S-405" in both and "FROZEN" in both, both[:300]


def test_the_read_recipes_md5_pins_are_CURRENT():
    """A stale pin is worse than none: it asserts a check that will fail, or -- unchecked --
    asserts nothing. S-405 found the prereg pin stale because a test had rewritten the file."""
    import hashlib
    import re as _re
    rec = os.path.join(ROOT, "runargs", "dcs_csi_pr021_read.txt")
    if not os.path.exists(rec):
        pytest.skip("read recipe absent")
    text = open(rec, encoding="utf-8").read()
    pairs = _re.findall(r"^#\s+\w+\s+(\S+)\s+md5 ([0-9a-f]{32})", text, _re.M)
    assert len(pairs) >= 4, "the recipe no longer pins four artefacts: %r" % pairs
    for path, pinned in pairs:
        f = os.path.join(ROOT, path)
        assert os.path.exists(f), "the recipe pins %s, which does not exist (S-167c)" % path
        live = hashlib.md5(open(f, "rb").read()).hexdigest()
        assert live == pinned, "%s: recipe pins %s but the file is %s" % (path, pinned, live)
