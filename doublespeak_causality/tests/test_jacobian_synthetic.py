"""GPU-free correctness gate for the Jacobian / projection-matrix readout
(scripts/phase6_jacobian_readout.py, plan §5 P6).

No model, no GPU, deterministic — same toy-module pattern as
tests/test_allposmlp_synthetic.py / tests/test_attribution_patching.py.

The toy is a LINEAR stack of blocks, so every derivative the script computes has a CLOSED FORM:

    resid[L]   = resid[L-1] @ W_L                (block L, position-wise, no nonlinearity)
    logits     = resid[n-1] @ U
    hs[L+1]    = resid[L]                        (house convention: block-L output)
    S_concept  = mean_i logits[-1, c_i] - mean_j logits[-1, k_j]
    S_refusal  = < hs[R][-1], u_ref >

so, with P(L, M) = W_{L+1} W_{L+2} ... W_M the product of the blocks strictly above L,

    dS_concept / d resid[L][last] = P(L, n-1) @ U @ (mean_i e_{c_i} - mean_j e_{k_j})
    dS_refusal / d resid[L][last] = P(L, R-1) @ u_ref

and at any non-final position the gradient is EXACTLY ZERO (the toy blocks are position-wise, so
no information flows forward) — which is also how we pin the position convention. A second toy
adds CAUSAL position mixing (prefix mean) and pins the direction of information flow.

Asserted here:
  (a) the computed gradient EQUALS the closed-form derivative (float64, atol 1e-9) for BOTH
      targets and EVERY layer — the correctness proof that makes the readout trustworthy;
  (b) the layer convention: acts[L] (block-output hook) == hidden_states[L+1], and grads are
      returned for exactly the requested layers;
  (c) the position convention: gradients live at the readout position (offset 0 from the end)
      and are zero elsewhere for a position-wise stack; with causal mixing they are non-zero at
      p <= readout and exactly zero at p > readout;
  (d) CONCEPT and REFUSAL targets produce DIFFERENT gradients — different tensors, different
      values, at every layer (they must never be accidentally the same object);
  (e) the degenerate self-layer readout (differentiating the refusal projection at the row it is
      read from) returns the refusal direction itself, and layer_sweep_for_target EXCLUDES it;
  (f) first-order Taylor: adding eps*unit(J) at (L, pos) changes S by exactly eps*||J|| in the
      linear toy — the same gate the script runs on the real model;
  (g) the reported summary rows (grad_norm / jac_proj / proj_* / cos_jac_*) match hand-computed
      values, and the plain-projection columns are the plain lens (not the Jacobian one).

Run:  python -m pytest doublespeak_causality/tests/test_jacobian_synthetic.py -q
      python doublespeak_causality/tests/test_jacobian_synthetic.py
"""
import importlib.util
import os
import sys
import types

import torch
import torch.nn as nn

_HERE = os.path.dirname(os.path.abspath(__file__))
_DC = os.path.dirname(_HERE)
sys.path.insert(0, _DC)

_spec = importlib.util.spec_from_file_location(
    "phase6_jacobian_readout", os.path.join(_DC, "scripts", "phase6_jacobian_readout.py"))
jac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(jac)

torch.manual_seed(0)
DT = torch.float64


# --------------------------------------------------------------------------- #
# Toy model: linear blocks + a linear unembedding, HF-shaped outputs
# --------------------------------------------------------------------------- #
class ToyBlock(nn.Module):
    """resid_post = resid_pre @ W  (position-wise, exactly linear). Tuple output like HF."""

    def __init__(self, hidden, seed):
        super().__init__()
        g = torch.Generator().manual_seed(seed)
        self.W = nn.Parameter(torch.randn(hidden, hidden, generator=g, dtype=DT) / hidden ** 0.5)

    def forward(self, x):
        return (x @ self.W, None)


class ToyCausalBlock(nn.Module):
    """resid_post[p] = (prefix mean over q <= p of resid_pre[q]) @ W — CAUSAL position mixing."""

    def __init__(self, hidden, seed):
        super().__init__()
        g = torch.Generator().manual_seed(seed)
        self.W = nn.Parameter(torch.randn(hidden, hidden, generator=g, dtype=DT) / hidden ** 0.5)

    def forward(self, x):
        csum = torch.cumsum(x, dim=1)
        denom = torch.arange(1, x.shape[1] + 1, dtype=x.dtype, device=x.device).view(1, -1, 1)
        return ((csum / denom) @ self.W, None)


class ToyLM(nn.Module):
    """Exposes model.model.layers (so ds_common._get_layers finds it) and returns an HF-shaped
    output with .logits and .hidden_states, where hidden_states[0] = embeddings and
    hidden_states[L+1] = output of block L (the house convention)."""

    def __init__(self, n_layers=4, hidden=6, vocab=11, block=ToyBlock, seed=0):
        super().__init__()
        self.model = nn.Module()
        self.model.layers = nn.ModuleList(block(hidden, seed + i) for i in range(n_layers))
        g = torch.Generator().manual_seed(seed + 100)
        self.U = nn.Parameter(torch.randn(hidden, vocab, generator=g, dtype=DT))
        self.num_layers = n_layers
        self.hidden = hidden

    def forward(self, x):
        hs = [x]
        h = x
        for blk in self.model.layers:
            h = blk(h)[0]
            hs.append(h)
        return types.SimpleNamespace(logits=h @ self.U, hidden_states=tuple(hs))


def _toy(n_layers=4, hidden=6, vocab=11, seq=5, block=ToyBlock, seed=0):
    lm = ToyLM(n_layers=n_layers, hidden=hidden, vocab=vocab, block=block, seed=seed)
    g = torch.Generator().manual_seed(seed + 7)
    x = torch.randn(1, seq, hidden, generator=g, dtype=DT).requires_grad_(True)
    return lm, x, (lambda: lm(x))


def _prod_above(lm, L, upto):
    """P(L, upto) = W_{L+1} ... W_{upto} (identity when upto <= L)."""
    P = torch.eye(lm.hidden, dtype=DT)
    for m in range(L + 1, upto + 1):
        P = P @ lm.model.layers[m].W
    return P


# --------------------------------------------------------------------------- #
# (a) gradient == closed-form derivative
# --------------------------------------------------------------------------- #
def test_concept_gradient_equals_closed_form():
    lm, x, fwd = _toy()
    n = lm.num_layers
    c_ids, k_ids = [2, 5], [7]
    scalar = jac.make_concept_scalar(c_ids, k_ids)
    layers = jac.layer_sweep_for_target(n, "concept", n)
    acts, grads, S, diag = jac.capture_jacobian(lm, fwd, scalar, layers, check_hs_rows=True)

    # closed form of the scalar itself
    out = lm(x)
    e = torch.zeros(lm.U.shape[1], dtype=DT)
    for i in c_ids:
        e[i] += 1.0 / len(c_ids)
    for j in k_ids:
        e[j] -= 1.0 / len(k_ids)
    assert abs(S - float(out.logits[0, -1, :] @ e)) < 1e-9, S

    for L in layers:
        want = _prod_above(lm, L, n - 1) @ (lm.U.detach() @ e)      # [hidden]
        got = grads[L][-1]
        assert torch.allclose(got.to(DT), want, atol=1e-9), (L, got, want)


def test_refusal_gradient_equals_closed_form():
    lm, x, fwd = _toy()
    n = lm.num_layers
    R = n                                                          # readout row = last
    g = torch.Generator().manual_seed(3)
    u = torch.randn(lm.hidden, generator=g, dtype=DT)
    u = u / u.norm()
    scalar = jac.make_refusal_scalar(u, R)
    layers = jac.layer_sweep_for_target(n, "refusal", R)
    acts, grads, S, _ = jac.capture_jacobian(lm, fwd, scalar, layers)

    out = lm(x)
    assert abs(S - float(out.hidden_states[R][0, -1, :] @ u)) < 1e-9, S
    for L in layers:
        want = _prod_above(lm, L, R - 1) @ u
        assert torch.allclose(grads[L][-1].to(DT), want, atol=1e-9), (L, grads[L][-1], want)


def test_refusal_gradient_closed_form_at_an_intermediate_readout_row():
    """Same proof with R strictly inside the stack (R=2): only layers 0 are non-degenerate."""
    lm, x, fwd = _toy(n_layers=4)
    R = 2
    g = torch.Generator().manual_seed(11)
    u = torch.randn(lm.hidden, generator=g, dtype=DT)
    u = u / u.norm()
    layers = jac.layer_sweep_for_target(lm.num_layers, "refusal", R)
    assert layers == [0], layers                                   # [0 .. R-2]
    _, grads, S, _ = jac.capture_jacobian(lm, fwd, jac.make_refusal_scalar(u, R), layers)
    want = _prod_above(lm, 0, R - 1) @ u
    assert torch.allclose(grads[0][-1].to(DT), want, atol=1e-9)


# --------------------------------------------------------------------------- #
# (b) layer indexing convention
# --------------------------------------------------------------------------- #
def test_layer_convention_acts_equal_hidden_states_L_plus_1():
    lm, x, fwd = _toy()
    n = lm.num_layers
    layers = jac.layer_sweep_for_target(n, "concept", n)
    acts, grads, _, diag = jac.capture_jacobian(
        lm, fwd, jac.make_concept_scalar([1], [2]), layers, check_hs_rows=True)
    assert diag["hs_match_maxabs"] == 0.0, diag
    ref = lm(x).hidden_states
    for L in layers:
        assert torch.equal(acts[L], ref[L + 1][0].detach().to(acts[L].dtype)), L
    assert sorted(grads) == sorted(layers), (sorted(grads), layers)


def test_layer_sweeps_stop_below_the_readout():
    n = 32
    assert jac.layer_sweep_for_target(n, "concept", n) == list(range(31))
    assert jac.layer_sweep_for_target(n, "refusal", 32) == list(range(31))
    assert jac.layer_sweep_for_target(n, "refusal", 22) == list(range(21))
    assert 21 not in jac.layer_sweep_for_target(n, "refusal", 22), "L=R-1 is degenerate"
    try:
        jac.layer_sweep_for_target(n, "bogus", n)
    except ValueError:
        pass
    else:
        raise AssertionError("unknown target must raise ValueError")


# --------------------------------------------------------------------------- #
# (c) position convention
# --------------------------------------------------------------------------- #
def test_position_convention_positionwise_stack_only_readout_position_has_gradient():
    lm, x, fwd = _toy(seq=6)
    n = lm.num_layers
    layers = jac.layer_sweep_for_target(n, "concept", n)
    _, grads, _, _ = jac.capture_jacobian(lm, fwd, jac.make_concept_scalar([0], [3]), layers)
    for L in layers:
        g = grads[L]
        assert g.shape == (6, lm.hidden), g.shape
        assert g[-1].norm() > 0, L
        assert torch.allclose(g[:-1], torch.zeros_like(g[:-1])), \
            "position-wise blocks: only the readout position can influence the scalar"
        prof = jac.position_profile(g)
        assert prof["argmax_offset_from_end"] == 0, prof


def test_position_convention_causal_mixing_gradient_flows_backwards_only():
    """With causal mixing and the scalar read at a MIDDLE position, positions after the readout
    must have exactly zero gradient and positions at/before it must be non-zero."""
    lm, x, fwd = _toy(seq=6, block=ToyCausalBlock, seed=5)
    n = lm.num_layers
    read_at = 3
    scalar = jac.make_concept_scalar([1], [4], pos=read_at)
    layers = jac.layer_sweep_for_target(n, "concept", n)
    _, grads, _, _ = jac.capture_jacobian(lm, fwd, scalar, layers)
    for L in layers:
        g = grads[L]
        assert torch.allclose(g[read_at + 1:], torch.zeros_like(g[read_at + 1:])), \
            f"L{L}: no gradient may flow to positions AFTER the readout position"
        assert (g[: read_at + 1].norm(dim=-1) > 0).all(), \
            f"L{L}: every position up to the readout must influence it under causal mixing"


def test_position_profile_offsets_are_relative_to_the_end():
    g = torch.zeros(5, 3, dtype=DT)
    g[2] = torch.tensor([3.0, 4.0, 0.0], dtype=DT)                 # norm 5 at index 2 of 5
    prof = jac.position_profile(g, topk=2)
    assert prof["argmax_offset_from_end"] == -2, prof
    assert prof["max_grad_norm"] == 5.0, prof
    assert prof["top"][0] == {"offset_from_end": -2, "grad_norm": 5.0}, prof


# --------------------------------------------------------------------------- #
# (d) the two targets are DIFFERENT objects
# --------------------------------------------------------------------------- #
def test_concept_and_refusal_gradients_differ_at_every_layer():
    lm, x, fwd = _toy()
    n = lm.num_layers
    g = torch.Generator().manual_seed(21)
    u = torch.randn(lm.hidden, generator=g, dtype=DT)
    u = u / u.norm()
    layers = jac.layer_sweep_for_target(n, "concept", n)
    _, gc, sc, _ = jac.capture_jacobian(lm, fwd, jac.make_concept_scalar([2, 5], [7]), layers)
    _, gr, sr, _ = jac.capture_jacobian(lm, fwd, jac.make_refusal_scalar(u, n), layers)
    assert abs(sc - sr) > 1e-6, (sc, sr)
    for L in layers:
        assert gc[L] is not gr[L], f"L{L}: the two targets must not share a tensor"
        assert not torch.allclose(gc[L], gr[L], atol=1e-8), f"L{L}: gradients must differ"
        cos = float(jac.unit(gc[L][-1]) @ jac.unit(gr[L][-1]))
        assert abs(cos) < 0.999, f"L{L}: concept and refusal Jacobians are collinear (cos={cos})"


def test_second_backward_does_not_accumulate_into_the_first():
    """Each target gets its own forward: the concept gradient must be identical whether or not a
    refusal backward has already been run (no .grad accumulation across targets)."""
    lm, x, fwd = _toy()
    n = lm.num_layers
    layers = jac.layer_sweep_for_target(n, "concept", n)
    concept = jac.make_concept_scalar([2, 5], [7])
    _, g1, _, _ = jac.capture_jacobian(lm, fwd, concept, layers)
    u = torch.ones(lm.hidden, dtype=DT) / lm.hidden ** 0.5
    jac.capture_jacobian(lm, fwd, jac.make_refusal_scalar(u, n), layers)
    _, g2, _, _ = jac.capture_jacobian(lm, fwd, concept, layers)
    for L in layers:
        assert torch.allclose(g1[L], g2[L], atol=1e-12), L


# --------------------------------------------------------------------------- #
# (e) the documented degeneracy
# --------------------------------------------------------------------------- #
def test_self_layer_refusal_readout_is_degenerate_and_is_excluded():
    """Differentiating the refusal projection at the row it is READ from gives back the refusal
    direction (norm 1, cos 1) — a tautological restatement of the plain lens. The sweep must
    exclude that layer; here we compute it explicitly to show WHY."""
    lm, x, fwd = _toy()
    n = lm.num_layers
    R = n
    g = torch.Generator().manual_seed(31)
    u = torch.randn(lm.hidden, generator=g, dtype=DT)
    u = u / u.norm()
    _, grads, _, _ = jac.capture_jacobian(lm, fwd, jac.make_refusal_scalar(u, R), [R - 1])
    got = grads[R - 1][-1]
    assert torch.allclose(got.to(DT), u, atol=1e-12), (got, u)
    assert abs(float(got.norm()) - 1.0) < 1e-12
    assert (R - 1) not in jac.layer_sweep_for_target(n, "refusal", R), \
        "the degenerate layer must not be in the reported sweep"


# --------------------------------------------------------------------------- #
# (f) first-order Taylor gate (exact on a linear stack)
# --------------------------------------------------------------------------- #
def test_taylor_check_is_exact_on_a_linear_stack():
    lm, x, fwd = _toy(seq=4)
    n = lm.num_layers
    layers = jac.layer_sweep_for_target(n, "concept", n)
    scalar = jac.make_concept_scalar([2, 5], [7])
    _, grads, S, _ = jac.capture_jacobian(lm, fwd, scalar, layers)
    for L in layers:
        res = jac.taylor_check(lm, fwd, scalar, L, 3, grads[L][3], S, eps=0.25, seq_len=4)
        assert res["pos_offset_from_end"] == 0, res
        assert abs(res["ratio_measured_over_predicted"] - 1.0) < 1e-6, (L, res)


def test_taylor_check_detects_a_wrong_direction():
    """Sanity of the gate itself: perturbing along a direction ORTHOGONAL to the Jacobian must
    move the scalar by ~0, i.e. a ratio far below 1 against the predicted eps*||J||."""
    lm, x, fwd = _toy(seq=4)
    n = lm.num_layers
    layers = jac.layer_sweep_for_target(n, "concept", n)
    scalar = jac.make_concept_scalar([2, 5], [7])
    _, grads, S, _ = jac.capture_jacobian(lm, fwd, scalar, layers)
    L = layers[0]
    j = grads[L][3]
    v = torch.randn(lm.hidden, generator=torch.Generator().manual_seed(9), dtype=DT)
    v = v - (v @ jac.unit(j)) * jac.unit(j)                        # orthogonal to J
    v = v / v.norm() * j.norm()                                    # norm-matched
    res = jac.taylor_check(lm, fwd, scalar, L, 3, v, S, eps=0.25, seq_len=4)
    assert abs(res["measured_delta"]) < 1e-9, res


# --------------------------------------------------------------------------- #
# (g) the reported row: Jacobian columns vs PLAIN projection columns
# --------------------------------------------------------------------------- #
def test_layer_row_values_match_hand_computation_and_keep_lenses_separate():
    act = torch.tensor([[1.0, 2.0, 2.0]], dtype=DT)                # one position, norm 3
    grad = torch.tensor([[0.0, 3.0, 4.0]], dtype=DT)               # norm 5, unit (0,.6,.8)
    concept_dir = torch.tensor([2.0, 0.0, 0.0], dtype=DT)          # unit (1,0,0)
    refusal_dir = torch.tensor([0.0, 0.0, -1.0], dtype=DT)
    row = jac.layer_row(act, grad, 0, {"concept": concept_dir, "refusal": refusal_dir})
    assert row["grad_norm"] == 5.0, row
    assert row["act_norm"] == 3.0, row
    assert abs(row["jac_proj"] - (2 * 0.6 + 2 * 0.8)) < 1e-9, row      # 2.8
    assert abs(row["proj_concept"] - 1.0) < 1e-9, row                  # plain lens, NOT the Jacobian
    assert abs(row["proj_refusal"] + 2.0) < 1e-9, row
    assert abs(row["cos_jac_concept"] - 0.0) < 1e-9, row
    assert abs(row["cos_jac_refusal"] + 0.8) < 1e-9, row
    assert "proj_signature" not in row, "only the direction families supplied may appear"


def test_layer_row_columns_are_the_documented_set():
    act = torch.randn(2, 4, dtype=DT)
    grad = torch.randn(2, 4, dtype=DT)
    dirs = {"concept": torch.randn(4, dtype=DT), "refusal": torch.randn(4, dtype=DT),
            "signature": torch.randn(4, dtype=DT)}
    row = jac.layer_row(act, grad, -1, dirs)
    assert set(row) == {"grad_norm", "jac_proj", "act_norm",
                        "proj_concept", "cos_jac_concept",
                        "proj_refusal", "cos_jac_refusal",
                        "proj_signature", "cos_jac_signature"}, sorted(row)


def test_zero_gradient_row_is_finite_and_zeroed():
    act = torch.tensor([[1.0, 1.0]], dtype=DT)
    grad = torch.zeros(1, 2, dtype=DT)
    row = jac.layer_row(act, grad, 0, {"concept": torch.tensor([1.0, 0.0], dtype=DT)})
    assert row["grad_norm"] == 0.0 and row["jac_proj"] == 0.0 and row["cos_jac_concept"] == 0.0, row


# --------------------------------------------------------------------------- #
# guards on the scalar constructors
# --------------------------------------------------------------------------- #
def test_concept_scalar_rejects_empty_id_sets():
    for a, b in (([], [1]), ([1], [])):
        try:
            jac.make_concept_scalar(a, b)
        except ValueError:
            continue
        raise AssertionError("empty first-token id set must raise ValueError")


def test_capture_jacobian_rejects_a_non_scalar_target():
    lm, x, fwd = _toy()
    try:
        jac.capture_jacobian(lm, fwd, lambda out: out.logits[0, -1, :], [0])
    except ValueError:
        return
    raise AssertionError("a non-0-dim target must raise ValueError")


def test_aggregate_reports_peaks_and_bootstrap_triples():
    recs = []
    for i in range(4):
        recs.append({
            "item_key": f"i{i}", "pair_key": f"i{i}", "split": "train", "condition": "doublespeak",
            "target": "concept", "scalar": 1.0 + i, "layers": [0, 1, 2],
            "by_pos": {"final_prompt": [{"grad_norm": 1.0, "jac_proj": 0.5},
                                        {"grad_norm": 9.0, "jac_proj": -7.0},
                                        {"grad_norm": 2.0, "jac_proj": 1.0}]},
        })
    out = jac.aggregate(recs, ["final_prompt"], seed=0)
    node = out["train|doublespeak"]["by_position"]["final_prompt"]["concept"]
    assert node["n"] == 4 and node["scalar_mean"] == 2.5, node
    assert node["peak_layer_grad_norm"] == 1, node
    assert node["peak_layer_abs_jac_proj"] == 1, node
    assert node["per_layer"][1]["grad_norm"][0] == 9.0, node["per_layer"][1]
    assert len(node["per_layer"][1]["jac_proj"]) == 3, "bootstrap triple [mean, lo, hi]"


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]

if __name__ == "__main__":
    fails = 0
    for t in TESTS:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except Exception as e:                                     # noqa: BLE001
            fails += 1
            print(f"FAIL  {t.__name__}: {e}")
    print(f"\n{len(TESTS) - fails}/{len(TESTS)} passed")
    sys.exit(1 if fails else 0)
