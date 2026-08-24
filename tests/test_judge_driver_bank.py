"""The judge driver must take its bank from the caller, and must refuse a missing one.

WHY (2026-08-24). scripts/judge_p2.sh hardcoded BANK to the MAIN prompt bank while MANIFEST /
EXPECTED / PREFIX / EXPECT_ROWS were already env-overridable. The first phase to run on one of the
crossed banks (basket_bomb) therefore pointed judge_boombness at the wrong bank.

It did NOT produce wrong numbers: judge_boombness's compare_bank_hashes refused the join outright --

    [compare_bank_hashes] REFUSING: the run consumed a DIFFERENT bank than the one it is being
    joined against: [('bank_rows_sha16', '113fc7b6f792f1c6', '4cd9157399aa1b3c')]

which is retraction R1's guard working. This test pins the FIX (parameterise) rather than the
workaround, and pins that the fallback default is still the main bank so existing phases are
unaffected.

Run:  python -m pytest tests/test_judge_driver_bank.py -q
"""
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRIVER = os.path.join(ROOT, "scripts", "judge_p2.sh")


def _src():
    return open(DRIVER).read()


def test_bank_is_overridable_by_the_caller():
    """THE REGRESSION TEST. Re-hardcode BANK and this goes red."""
    s = _src()
    assert re.search(r"BANK=\$\{P2_BANK:-", s), (
        "judge_p2.sh no longer takes its bank from P2_BANK; a run on a crossed bank would be "
        "judged against the main bank and refused by compare_bank_hashes")


def test_the_default_is_still_the_main_bank():
    """Parameterising must not change behaviour for the phases that were already correct."""
    s = _src()
    m = re.search(r"BANK=\$\{P2_BANK:-([^}]+)\}", s)
    assert m, "the BANK assignment changed shape"
    assert m.group(1).rstrip().endswith("boombness_prompt_bank.jsonl"), m.group(1)


def test_a_missing_bank_refuses_rather_than_running():
    """A bad path must die at second zero, not after three judge processes have started."""
    s = _src()
    assert "REFUSING: bank not found" in s, "the bank-existence check is gone"
    i = s.index("REFUSING: bank not found")
    assert s.index("BANK=${P2_BANK:-") < i, "the existence check runs before BANK is set"
    # and it must sit ABOVE the launch loop, or it cannot prevent the launches
    assert i < s.index("judge_boombness.py"), \
        "the bank check moved below the judge launch, where it no longer prevents anything"


def test_the_driver_is_valid_shell():
    r = subprocess.run(["bash", "-n", DRIVER], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_the_bank_is_echoed():
    """A driver that judges against an unstated bank is how this happened silently."""
    assert re.search(r'echo\s+"\[p2\] bank = \$BANK"', _src()), \
        "the resolved bank is not echoed, so a wrong bank stays invisible in the log"
