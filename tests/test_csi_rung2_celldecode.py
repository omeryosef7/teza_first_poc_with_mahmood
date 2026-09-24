"""The RUNG 2 instrument's direction and its refusals, tested without a GPU.

⚠ WHY THE REFUSAL TESTS MATTER MORE THAN THEY LOOK. The token ids are REQUIRED ARGUMENTS with no
defaults for one reason: `scripts/dcs_cont_logitlens_control.py` hardcodes ' button'/' Button'
while the entire CSI cell line is BASKET (S-380). Run unchanged it computes a well-formed,
plausible number for a question nobody asked. That is this sprint's most persistent defect class --
a family-specific literal surviving a widening (R29/S-322, S-308, S-357) -- and a default here
would reintroduce it.
"""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
SCRIPT = os.path.join(ROOT, "scripts", "dcs_csi_rung2_celldecode.py")


def _code(path=None):
    """Source with comment lines stripped.

    ⚠ R35-C/S-385: five tests in this session broke or passed wrongly because a grep matched the
    COMMENT that documents a fix rather than the code that performs it. A file that explains its
    own history will always contain the string naming the defect it removed, so `"<old code>" not
    in src` is not a test of anything once the fix is documented. These greps run on code only."""
    src = open(path or SCRIPT, encoding="utf-8").read()
    out = []
    for line in src.splitlines():
        t = line.split("#")[0] if not line.lstrip().startswith("#") else ""
        out.append(t)
    return "\n".join(out)


def _mod():
    spec = importlib.util.spec_from_file_location("rung2", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_direction_is_the_frozen_formula():
    """u = g_final * (mean(concept rows) - mean(codeword rows)), frozen in S-382 BEFORE any
    measurement so a later choice cannot masquerade as the original one."""
    torch = pytest.importorskip("torch")
    m = _mod()
    g = torch.tensor([2.0, 3.0, 4.0])
    rows = {1: torch.tensor([1.0, 0.0, 0.0]), 2: torch.tensor([3.0, 0.0, 0.0]),
            3: torch.tensor([0.0, 1.0, 0.0]), 4: torch.tensor([0.0, 3.0, 0.0])}
    u = m.build_direction(g, rows, (1, 2), (3, 4))
    # mean(concept) = [2,0,0]; mean(codeword) = [0,2,0]; diff = [2,-2,0]; * g = [4,-6,0]
    assert torch.allclose(u, torch.tensor([4.0, -6.0, 0.0])), u


def test_direction_is_LINEAR_which_is_what_makes_the_decomposition_exact():
    """S-380 measured linear |diff| 7.58e-15 vs logsumexp |diff| 6.89e-01. The whole design rests
    on the readout being linear, so the direction must be a fixed vector -- not a function of the
    activation it will be dotted with."""
    torch = pytest.importorskip("torch")
    m = _mod()
    g = torch.rand(64) + 0.5
    rows = {i: torch.randn(64) for i in range(4)}
    u = m.build_direction(g, rows, (0, 1), (2, 3))
    h1, h2 = torch.randn(64), torch.randn(64)
    assert torch.allclose((h1 + h2) @ u, (h1 @ u) + (h2 @ u), atol=1e-5)


def test_mean_of_casings_not_one_casing():
    """S-382 chose the MEAN over lowercase-only because both are linear but the latter adds a free
    choice a reader could not distinguish from tuning. If someone silently switches to the first
    row, this fails."""
    torch = pytest.importorskip("torch")
    m = _mod()
    g = torch.ones(3)
    rows = {1: torch.tensor([1.0, 0.0, 0.0]), 2: torch.tensor([5.0, 0.0, 0.0]),
            3: torch.zeros(3), 4: torch.zeros(3)}
    u = m.build_direction(g, rows, (1, 2), (3, 4))
    assert float(u[0]) == 3.0, "not the mean of the two concept rows: %r" % u


def _run(extra):
    base = [PY, SCRIPT, "--bank", "/nonexistent", "--split", "train",
            "--exclude-prompt-ids", "/nonexistent", "--model", "/m",
            "--snapshot-glob", "/s/*", "--heads", "4,6", "--out", "/tmp/x.json",
            # ⚠ every REQUIRED arg must be present, or argparse refuses for an UNRELATED reason
            # and the test below passes without exercising the check it names. R35-C was sent
            # hunting exactly this shape; adding --bank-block etc. broke two of these tests, which
            # is how it was found (S-384).
            "--bank-block", "cds_n4_sow", "--condition", "natural_doublespeak",
            "--expect-n", "230", "--expect-domains", "23", "--answer-prefix", "Answer:"]
    return subprocess.run(base + extra, capture_output=True, text=True)


def test_token_ids_have_NO_DEFAULTS():
    """A default is how ' button' ends up in a basket family (S-380)."""
    r = _run([])
    both = r.stdout + r.stderr
    assert r.returncode != 0
    assert "--concept-ids" in both and "required" in both.lower(), both


def test_overlapping_concept_and_codeword_ids_are_refused():
    r = _run(["--concept-ids", "13054,33909", "--codeword-ids", "33909,14351"])
    both = r.stdout + r.stderr
    assert r.returncode != 0
    assert "overlap" in both and "degenerate" in both, both


def test_empty_id_list_is_refused_not_defaulted():
    r = _run(["--concept-ids", "", "--codeword-ids", "14351"])
    both = r.stdout + r.stderr
    assert r.returncode != 0
    assert "is empty" in both, both


def test_TEST_split_is_not_even_a_choice():
    """PART I: TEST is never touched. It is not an option the operator can pass."""
    r = subprocess.run([PY, SCRIPT, "--help"], capture_output=True, text=True)
    assert "--split" in r.stdout
    seg = r.stdout.split("--split")[1][:200]
    assert "test" not in seg.split("}")[0], "TEST appears in the --split choices: %r" % seg


def test_the_exclusion_file_is_REQUIRED():
    """S-381 measured that this FILE, not the prereg, is what actually keeps TEST out -- the
    prereg's own leak check is vacuous (S-375). So it cannot be optional."""
    r = subprocess.run([PY, SCRIPT, "--help"], capture_output=True, text=True)
    assert "--exclude-prompt-ids" in r.stdout
    src = open(SCRIPT, encoding="utf-8").read()
    assert '"--exclude-prompt-ids", required=True' in src


def test_the_script_refuses_to_emit_a_verdict():
    """It is an INSTRUMENT. A preregistered reader decides what a measurement means."""
    src = open(SCRIPT, encoding="utf-8").read()
    assert "EXPLORATORY" in src
    # ⚠ NOT a grep for the WORD -- the docstring says "COMPUTES NO VERDICT", which a naive search
    # flags as a violation of itself. Look for verdict-EMITTING code instead: a JSON key, or a
    # comparison against a significance threshold.
    for forbidden in ('"VERDICT"', '"p_one_sided"', '"PASS"', '"FAIL"', "<= alpha", "> alpha"):
        assert forbidden not in src, "the instrument emits/decides %r; it must not" % forbidden


def test_it_records_that_this_is_NOT_the_endpoint():
    """y_install aggregates casings with logsumexp; this direction is linear. The artefact must
    carry that, because the distinction is invisible in the numbers (S-381/S-382)."""
    # ⚠ R35-C/S-385 PROVED THE FIRST VERSION OF THIS TEST COULD NOT FAIL. It asserted
    # `"does NOT decompose y_install" in src or "decomposes y_install" in src` -- and the second
    # disjunct is satisfied by the DOCSTRING SENTENCE THAT FORBIDS THE CLAIM ("It MAY NOT be said
    # that this decomposes y_install"). A mutant that published
    # "NOT_THE_ENDPOINT": "this fully decomposes y_install into per-cell shares" passed. The key's
    # existence was checked; its VALUE, which is the entire point, was not.
    src = open(SCRIPT, encoding="utf-8").read()
    i = src.find('"⚠ NOT_THE_ENDPOINT":')
    assert i > 0, "the artefact no longer carries the NOT_THE_ENDPOINT key"
    val = src[i:i + 500]
    assert "LOGSUMEXP" in val and "LINEAR" in val, (
        "the emitted VALUE no longer states the logsumexp-vs-linear distinction: %r" % val[:200])
    assert "does NOT decompose y_install" in val or "NOT decompose y_install" in val, (
        "the emitted VALUE no longer forbids the y_install claim: %r" % val[:200])


def test_population_filters_are_REQUIRED_because_their_absence_touched_TEST():
    """🔴 R35/S-384. The first draft filtered only query_kind + cell + the exclusion file. That
    selects 926 rows over 116 DOMAINS, because the exclusion file removes only the non-validation
    part of ONE bank_block/condition slice -- every other slice survives, and the 116 domains
    include TRAIN and TEST. The arms' real population is 230 rows over 23 domains. Without these
    filters the instrument would have read TEST and emitted a well-formed number while doing it."""
    src = open(SCRIPT, encoding="utf-8").read()
    for flag in ('"--bank-block", required=True', '"--condition", required=True',
                 '"--expect-n", type=int, required=True',
                 '"--expect-domains", type=int, required=True'):
        assert flag in src, "missing required population flag: %s" % flag
    assert 'r.get("bank_block") != a.bank_block' in src
    assert 'r.get("condition") != a.condition' in src


def test_a_population_that_does_not_match_the_declaration_is_REFUSED():
    """The declared (expect_n, expect_domains) must GATE, not merely be recorded."""
    # ⚠ R35-C/S-385 PROVED THE FIRST VERSION COULD NOT FAIL EITHER. It grepped for "REFUSING"
    # within 400 chars of the comparison -- so changing `raise SystemExit(` to `print(` left the
    # word in place and the test passed while the 926-row, 116-domain, TEST-bearing selection ran
    # to completion. This version RUNS the script against a synthetic bank and asserts the exit
    # code, which no source mutation can satisfy without actually refusing.
    src = open(SCRIPT, encoding="utf-8").read()
    assert "if (n_sel, n_dom) != (a.expect_n, a.expect_domains):" in src, \
        "the declared population is not compared at all"

    import tempfile
    sp = json.load(open(os.path.join(ROOT, "data", "boombness_prompts",
                                     "dcs_ts116_domain_split.json")))
    assign = sp.get("assign") or sp.get("assignments") or {}
    vdoms = sorted(d for d, v in assign.items() if v == "validation")[:2]
    assert vdoms, "premise changed: no validation domains in the split manifest"
    with tempfile.TemporaryDirectory() as td:
        bank = os.path.join(td, "bank.jsonl")
        with open(bank, "w") as fh:
            for j, dom in enumerate(vdoms):
                fh.write(json.dumps({
                    "prompt_id": "id%d" % j, "domain": dom, "cell": "C",
                    "query_kind": "semantic_one_word", "bank_block": "cds_n4_sow",
                    "condition": "natural_doublespeak", "full_prompt": "x",
                    "demo_block": "x"}) + "\n")
        exf = os.path.join(td, "ex.txt")
        open(exf, "w").write("# header\n")
        r = subprocess.run(
            [PY, SCRIPT, "--bank", bank, "--split", "validation", "--exclude-prompt-ids", exf,
             "--model", "/m", "--snapshot-glob", "/s/*", "--heads", "4",
             "--concept-ids", "1", "--codeword-ids", "2", "--out", os.path.join(td, "o.json"),
             "--answer-prefix", "Answer:", "--bank-block", "cds_n4_sow",
             "--condition", "natural_doublespeak",
             "--expect-n", "999", "--expect-domains", "999"],   # deliberately wrong
            capture_output=True, text=True)
        both = r.stdout + r.stderr
        assert r.returncode != 0, "a population that does not match the declaration was ACCEPTED"
        assert "REFUSING" in both and "expect-n" in both, both[:400]


def test_exclusion_file_comments_are_stripped():
    """The real exclusion files carry a `#` header naming the selection they came from; reading
    them raw silently adds non-ids to the set and inflates any count taken from it."""
    src = open(SCRIPT, encoding="utf-8").read()
    assert 'startswith("#")' in src
    f = os.path.join(ROOT, "runargs", "dcs_cont", "exclude_basket_bomb_sow_validation.txt")
    if os.path.exists(f):
        head = open(f, encoding="utf-8").readline()
        assert head.startswith("#"), "premise changed: the exclusion file no longer has a header"


def test_the_readout_is_the_ENDPOINTS_position_not_the_bare_prompt_end():
    """🔴 R35-B/S-385. The first draft used len(tokenize(templated))-1, taken from
    retrieval_strength.py -- which computes an attention-mass scalar and has NO answer prefix.
    The endpoint reads `templated + answer_prefix` (score_behavior.py:87, :3914), two tokens
    later across the 'Answer' ':' boundary. score_behavior.py:3173 MEASURED the bare-prompt
    position at ~5.6e-06 option mass and abandoned it on 2026-08-18."""
    code = _code()
    assert '"--answer-prefix", required=True' in code, "the answer prefix has a default again"
    assert "templated + a.answer_prefix" in code, "the context no longer includes the prefix"
    assert "assert dst == len(ids) - 1" not in code, (
        "the tautological assert is back: `dst` was just set to len(ids)-1, so it cannot fail")


def test_TEST_is_structurally_unreachable_not_merely_undeclared():
    """🔴 R35-B/C/S-385. --split was recorded and never compared to a row, and the population gate
    checks counts the OPERATOR typed -- so a test-bearing block with honest expectations passed
    it. The split manifest must be read and enforced."""
    code = _code()
    assert "dcs_ts116_domain_split.json" in code, "the split manifest is not read"
    assert 'r.get("domain") not in keep_dom' in code, "the split is read but not enforced per row"
    assert "EXCLUDED_DOMAINS" in code, "the 3 preregistered whole-population domains are not excluded"


def test_it_imports_the_module_that_actually_has_load_model():
    """🔴 R35-B/C/S-385. `import common as dc` then `dc.load_model(...)` -- common.py has neither
    load_model nor apply_template. The script could not run past model load, which is why the
    wrong-readout bug survived: nothing had ever executed it."""
    code = _code()
    assert "import ds_common as dc" in code
    assert "import common as dc" not in code, "the wrong module is still imported in CODE"


def test_the_reconstruction_check_cannot_be_consumed_by_a_skipped_row():
    """R35-B/C/S-385. It was `check_invariants=(i == 0)` over the PRE-SKIP enumeration, so a
    skipped row 0 disabled the only structural guard for the whole run, silently."""
    code = _code()
    assert "check_invariants=(n_done == 0)" in code
    assert "check_invariants=(i == 0)" not in code, "the pre-skip enumeration is back in CODE"
    assert "recon_rel_err_first_row" in code, "the reconstruction error is still discarded"


def test_dividing_by_rms_recovers_the_logit_difference_up_to_ONE_global_constant():
    """🔴 R35-A/S-387. `D_dir` gives <Y, u_hat> = <Y,u>/||u||, but the true logit-difference
    contribution is <Y,u>/rms_p. So the raw emitted value is `true x rms_p/||u||`, and averaging
    it over prompts with different rms is an RMS-WEIGHTED mean -- which R35-A showed can FLIP an
    argmax. This test verifies the corrected chain numerically:

        sum_i ( <Y_i, u_hat> / rms )  ==  <norm(h), Wc - Wk> / ||u||

    i.e. after dividing by rms the per-cell values are logit-difference contributions up to the
    single global constant ||u||, which is shared by every cell and cannot reorder anything."""
    torch = pytest.importorskip("torch")
    m = _mod()
    D, EPS = 256, 1e-5
    torch.manual_seed(387)
    g = (torch.rand(D, dtype=torch.float64) + 0.5)
    Wc, Wk = torch.randn(D, dtype=torch.float64), torch.randn(D, dtype=torch.float64)
    u = m.build_direction(g, {0: Wc, 1: Wk}, (0,), (1,))          # g * (Wc - Wk)
    u_hat = u / u.norm()

    Y = torch.randn(7, D, dtype=torch.float64)                    # 7 cell contributions
    h = Y.sum(0)
    rms = torch.sqrt((h * h).mean() + EPS)

    lens = (Wc @ (h / rms * g)) - (Wk @ (h / rms * g))            # the true logit difference
    emitted_sum = sum((Y[i] @ u_hat) / rms for i in range(7))     # what the script now accumulates

    assert torch.allclose(emitted_sum, lens / u.norm(), atol=1e-12), (
        "corrected values do not sum to the logit difference / ||u||: %r vs %r"
        % (float(emitted_sum), float(lens / u.norm())))

    # and the DEFECT is real: without the /rms the relation depends on rms, so two prompts with
    # different rms contribute on different scales.
    raw_sum = sum((Y[i] @ u_hat) for i in range(7))
    assert not torch.allclose(raw_sum, lens / u.norm(), atol=1e-6), (
        "premise broken: the raw value already equalled the logit difference, so there was "
        "nothing to correct")


def test_the_rms_normalisation_is_actually_applied_in_CODE():
    code = _code()
    assert "register_forward_pre_hook" in code, "the final-norm rms is never captured"
    assert "/ _rms)" in code, "the captured rms is never divided out"
    assert "rms_at_dst" in code, "the rms range is not recorded in the artefact"
