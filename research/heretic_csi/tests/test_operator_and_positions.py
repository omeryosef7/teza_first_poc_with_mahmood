#!/usr/bin/env python3
"""Synthetic unit tests for operator_ara.py and positions.py (CPU, no GPU, no HF download)."""
import os, sys
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(PKG))
for p in (ROOT, PKG):
    if p not in sys.path:
        sys.path.insert(0, p)

import operator_ara as oa          # noqa: E402
import positions as P              # noqa: E402


# ---------------- operator_ara ----------------
def _toy_modules(seed=0, in_dim=16, out_dim=12, n=24):
    g = torch.Generator().manual_seed(seed)
    W = torch.randn(out_dim, in_dim, generator=g)
    t_in = torch.randn(n, in_dim, generator=g)
    t_out = t_in @ W.t()
    # source input is the target input shifted along a 3-D subspace (so a low-rank edit can steer it)
    shift = torch.randn(n, in_dim, generator=g) * 0.0
    shift[:, :3] += torch.randn(n, 3, generator=g) * 2.0
    s_in = t_in + shift
    s_out = s_in @ W.t()
    return [oa.ModuleIO("m0", W, t_in, t_out, s_in, s_out)], W


def test_fit_reduces_loss_and_steers():
    mods, W = _toy_modules()
    cfg = oa.OperatorFitConfig(rank=4, preserve_weight=1.0, steer_weight=1.0, neighbor_count=1, n_steps=15)
    fit = oa.fit_operator(mods, cfg)
    assert len(fit.loss_history) > 0
    assert fit.loss_history[-1] <= fit.loss_history[0] + 1e-6, "loss did not decrease"
    # steer check: source->target distance shrinks vs the un-edited source output
    m = mods[0]
    W_eff = fit.effective_weight("m0", W)
    new_s = m.source_in @ W_eff.t()
    d_before = oa.mean_distance_to_knn(m.source_out, m.target_out, 1)
    d_after = oa.mean_distance_to_knn(new_s, m.target_out, 1)
    assert d_after < d_before, f"steer failed: before {d_before:.4f} after {d_after:.4f}"


def test_delta_rank_bounded():
    mods, W = _toy_modules()
    for r in (1, 2, 4):
        fit = oa.fit_operator(mods, oa.OperatorFitConfig(rank=r, n_steps=5))
        dW = fit.delta_w("m0")
        rk = int(torch.linalg.matrix_rank(dW.double(), tol=1e-6))
        assert rk <= r, f"rank {rk} exceeds configured {r}"


def test_identity_is_inert():
    mods, W = _toy_modules()
    fac = oa.identity_operator(mods, rank=3)
    A, B = fac["m0"]
    assert torch.allclose(B @ A, torch.zeros_like(W)), "identity adapter not zero"


def test_random_orthogonal_matches_fro_and_rank():
    mods, W = _toy_modules()
    target_fro = {"m0": 2.5}
    fac = oa.random_orthogonal_operator(mods, rank=4, target_fro=target_fro, seed=7)
    A, B = fac["m0"]
    dW = B @ A
    assert abs(float(dW.norm()) - 2.5) < 1e-3, f"fro {float(dW.norm()):.4f} != 2.5"
    rk = int(torch.linalg.matrix_rank(dW.double(), tol=1e-6))
    assert rk <= 4, f"control rank {rk} > 4"


def test_preserve_row_magnitudes_identity_at_zero():
    mods, W = _toy_modules()
    cfg = oa.OperatorFitConfig(rank=2, preserve_row_magnitudes=True, n_steps=0)
    fit = oa.fit_operator(mods, cfg)
    W_eff = fit.effective_weight("m0", W)   # B=0 -> normalize(W)*||W||_row == W exactly
    assert torch.allclose(W_eff, W, atol=1e-4), "row-norm-preserve not identity at ΔW=0"


# ---------------- positions ----------------
class StubTok:
    """Minimal tokenizer: id==char-code of a single-letter 'word'; decode maps id->' <word>' style."""
    def __init__(self):
        self.vocab = {" basket": 14351, "basket": 99001, " button": 3215, " bomb": 13054}
        self.rev = {14351: " basket", 99001: "basket", 3215: " button", 13054: " bomb", 7: " refer", 8: "?"}
    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": [self.vocab[text]] if text in self.vocab else [max(1, len(text))]}
    def decode(self, ids):
        return "".join(self.rev.get(int(i), f"<{int(i)}>") for i in ids)


def test_rel_end_to_abs():
    assert P.rel_end_to_abs(-10, 215) == 205
    try:
        P.rel_end_to_abs(-300, 10); assert False
    except ValueError:
        pass


def test_anchor_self_check_passes_and_fails():
    tok = StubTok()
    # build ids where position -10 is ' basket'
    ids = [7] * 20
    ids[-10] = 14351
    info = P.anchor_from_rel_end(ids, tok, "basket", -10, require_codeword_match=True)
    assert info.matches_codeword and info.abs_pos == len(ids) - 10
    # wrong token at -10 -> loud failure
    bad = [7] * 20
    try:
        P.anchor_from_rel_end(bad, tok, "basket", -10, require_codeword_match=True)
        assert False, "should have raised"
    except P.AmbiguousPosition:
        pass


def test_left_padded_anchor():
    tok = StubTok()
    real = [7] * 20
    real[-10] = 3215  # ' button'
    pad = [0] * 5 + real
    mask = [0] * 5 + [1] * 20
    info = P.anchor_in_padded_row(pad, mask, tok, "button", -10, require_codeword_match=True)
    assert info.abs_pos == 10 and info.abs_pos_padded == 15 and info.matches_codeword
    # right-padded mask must be rejected
    try:
        P.anchor_in_padded_row(real + [0]*5, [1]*20 + [0]*5, tok, "button", -10)
        assert False
    except P.AmbiguousPosition:
        pass


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn(); print(f"PASS {fn.__name__}"); passed += 1
    print(f"\nALL {passed}/{len(fns)} PASSED")
