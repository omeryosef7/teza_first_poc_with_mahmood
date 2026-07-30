"""
tests_s0/test_integrity_fixes.py — Stage 0 integrity-repair unit tests
(NEXT_CAUSAL_SPRINT_PLAN.md §Stage 0).

Each test targets one repaired failure mode and FAILS on the pre-fix code:

  * C1 (07_patchscope_readout.py / ds_common.patch_layer_sweep): a patch-layer
    sweep must NEVER include the readout layer R (would overwrite the measured
    vector with zero propagation).
  * C2 (41_aggregate_pairs.py): a MISSING d_DS cell must never be counted as
    "inert"; and the install arm must be selected by SIGNED max, not max(abs),
    so a large negative control cell cannot mask a real +install.

Runnable two ways:
    pytest doublespeak_causality/tests_s0/test_integrity_fixes.py
    python doublespeak_causality/tests_s0/test_integrity_fixes.py   # prints PASS/FAIL, exit code
CPU-only, no model download.
"""
import os
import sys
import json
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DSC = os.path.dirname(HERE)                      # doublespeak_causality/
sys.path.insert(0, DSC)


# --------------------------------------------------------------------------- #
# C1 — patch sweep must exclude the readout layer
# --------------------------------------------------------------------------- #
def test_patch_layer_sweep_excludes_readout_layer():
    import ds_common as dc
    for R in (1, 2, 5, 12, 28, 31):
        layers = dc.patch_layer_sweep(R)
        assert R not in layers, f"readout layer {R} must not be patched, got {layers}"
        assert layers == list(range(R)), f"expected [0,{R}), got {layers}"
        assert max(layers) == R - 1, f"max patch layer must be R-1={R-1}, got {max(layers)}"


def test_patch_layer_sweep_rejects_degenerate_readout():
    import ds_common as dc
    for bad_R in (0, -1):
        try:
            dc.patch_layer_sweep(bad_R)
        except AssertionError:
            continue
        raise AssertionError(f"patch_layer_sweep({bad_R}) should have raised (no valid window)")


# --------------------------------------------------------------------------- #
# C2 — helpers to build a minimal 35_analyze_pair_causal.py-shaped analysis json
# --------------------------------------------------------------------------- #
def _cell(arm, group, effect, site="codeword_all", n=8):
    return {"arm": arm, "group": group, "site": site, "effect": effect,
            "lo": effect - 0.01, "hi": effect + 0.01, "n": n,
            "significant_corrected": abs(effect) >= 0.05}


def _write_analysis(per_cell):
    d = {"per_cell": {str(i): c for i, c in enumerate(per_cell)},
         "control_distribution": {}}
    fd, path = tempfile.mkstemp(suffix="_analysis.json"); os.close(fd)
    json.dump(d, open(path, "w"))
    return path


def _run_aggregate(analysis_path):
    fd, out = tempfile.mkstemp(suffix="_gen.json"); os.close(fd)
    r = subprocess.run(
        [sys.executable, os.path.join(DSC, "41_aggregate_pairs.py"),
         "--analysis", analysis_path, "--out", out],
        capture_output=True, text=True, cwd=DSC)
    assert r.returncode == 0, f"aggregate failed:\n{r.stderr}"
    return json.load(open(out))


def test_missing_dDS_cells_not_counted_inert():
    """A pair with d_Direct measured but ZERO valid d_DS cells (wrong `site`) must
    be quarantined, NOT counted inert, and must break the all-pairs dissociation."""
    per_cell = (
        [_cell("add_d_Direct", w, 0.30) for w in ("early", "mid", "late")]
        # d_DS present but on the wrong site -> zero matching codeword_all cells
        + [_cell("add_d_DS", w, 0.30, site="codeword_last") for w in ("early", "mid", "late")]
    )
    out = _run_aggregate(_write_analysis(per_cell))
    assert out["n_pairs_where_d_DS_inert"] == 0, "missing d_DS must not be scored inert"
    assert out["n_pairs_where_d_DS_measured_all_windows"] == 0
    assert out["pairs_d_DS_incomplete"], "pair with missing d_DS windows must be quarantined"
    assert out["dissociation_holds_in_all_pairs"] is False, \
        "an unmeasured d_DS pair must NOT let the dissociation stand"


def test_signed_max_install_not_masked_by_negative_control():
    """add_d_Direct|late has both a real +0.9 install and a -0.95 (control-ish) cell.
    Signed max must report +0.9 (install detected); max(abs) would report -0.95 (masked)."""
    per_cell = (
        [_cell("add_d_Direct", "early", 0.01), _cell("add_d_Direct", "mid", 0.02),
         _cell("add_d_Direct", "late", 0.90), _cell("add_d_Direct", "late", -0.95)]
        + [_cell("add_d_DS", w, 0.001) for w in ("early", "mid", "late")]
    )
    out = _run_aggregate(_write_analysis(per_cell))
    late = out["pairs"][0]["windows"]["add_d_Direct|late"]["effect"]
    assert late == 0.90, f"signed-max must pick +0.90 install, got {late}"
    assert out["n_pairs_where_d_Direct_installs"] == 1, "the +0.90 install must be detected"


def test_genuine_inert_still_recognized():
    """Sanity: a fully-measured pair with tiny d_DS and real d_Direct is the intended
    dissociation and must still be reported as install+inert."""
    per_cell = (
        [_cell("add_d_Direct", w, 0.40) for w in ("early", "mid", "late")]
        + [_cell("add_d_DS", w, 0.004) for w in ("early", "mid", "late")]
    )
    out = _run_aggregate(_write_analysis(per_cell))
    assert out["n_pairs_where_d_DS_inert"] == 1
    assert out["n_pairs_where_d_Direct_installs"] == 1
    assert out["dissociation_holds_in_all_pairs"] is True


TESTS = [
    test_patch_layer_sweep_excludes_readout_layer,
    test_patch_layer_sweep_rejects_degenerate_readout,
    test_missing_dDS_cells_not_counted_inert,
    test_signed_max_install_not_masked_by_negative_control,
    test_genuine_inert_still_recognized,
]

if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except Exception as e:
            fails += 1
            print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(TESTS) - fails}/{len(TESTS)} passed")
    sys.exit(1 if fails else 0)
