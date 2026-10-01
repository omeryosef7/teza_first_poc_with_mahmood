#!/usr/bin/env python3
"""Low-rank operator optimizer: a clean-room reimplementation of Heretic ARA's kNN-steer objective.

PROVENANCE / ATTRIBUTION. The optimization *algorithm* below is Arbitrary-Rank Ablation (ARA)
(Weidmann 2026), as audited from `external_repos/heretic/src/heretic/modifiers/ara.py` @ 662e4ba2
(see the plan log §9). This is a from-scratch reimplementation of the mathematics (a low-rank LoRA
edit `W_eff = W_base + B@A` fit by L-BFGS on a preserve/steer kNN-in-activation objective), NOT a copy
of Heretic's AGPL source. We reimplement because the Heretic env (torch 2.13 / transformers 5.6) could
not be installed under the shared-volume quota (log S-005), and because the headline experiment must run
in `poc_stage2` (eager attention) to be comparable to the inherited CSI rank-1 rescue. Heretic itself
(AGPL-3.0) is cited; the technique is attributed to Weidmann 2026 (ARA, PR #211).

RENAME (plan §6). Heretic's objective speaks of "good"/"bad" prompts (safety framing). Our semantic
design uses TARGET (the state we want to reach/preserve — the CLEAN codeword-row activation) and SOURCE
(the state we move from — the KNOCKOUT codeword-row activation). Mapping: good->target, bad->source.

OBJECTIVE (per modified linear module with weight W [out,in]; module output = X @ W.T):
    W_eff = W_base + B @ A                        (B:[out,r], A:[r,in]; B zero-init => starts at identity)
    [optional] W_eff = normalize(W_eff, dim=1) * row_norms(W_base)     (preserve per-output-row L2 norm)
    preserve_target = mean( (target_in @ W_eff.T  -  target_out_orig)^2 )
    steer           = mean_knn( source_in @ W_eff.T  ->  target_out_orig, k )
                      - overcorrect * mean_knn( source_in @ W_eff.T  ->  source_out_orig, k )
    loss(module)    = preserve_w * preserve_target + steer_w * steer
    total_loss      = sum over modules
Optimized jointly over all modules' (A,B) with torch.optim.LBFGS(line_search_fn="strong_wolfe").

This module is pure torch; it has NO dependency on Heretic, on the CSI knockout harness, or on a GPU
(works on CPU for tests). It takes already-captured activation tensors and returns the fitted factors +
the effective ΔW for SVD analysis (plan P3).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import torch


# --------------------------------------------------------------------------------------------
# kNN distance in activation space (ARA mean_distances_to_knn, ara.py:118-121)
# --------------------------------------------------------------------------------------------
def mean_distance_to_knn(X: torch.Tensor, Y: torch.Tensor, k: int) -> torch.Tensor:
    """For each row of X, the mean Euclidean distance to its k nearest rows in Y; averaged over X.

    k is clamped to [1, len(Y)]. Uses torch.cdist (differentiable in X), matching ARA's use of a
    kNN steer rather than a mean-to-mean pull (so a multi-modal target is not collapsed to its mean).
    """
    if X.numel() == 0 or Y.numel() == 0:
        return X.new_zeros(())
    k = max(1, min(int(k), Y.shape[0]))
    d = torch.cdist(X, Y)                      # [nX, nY]
    knn = torch.topk(d, k, dim=1, largest=False).values   # [nX, k]
    return knn.mean()


@dataclass
class ModuleIO:
    """Captured I/O for one linear module (one (layer, component)). All tensors [n, dim] on CPU/GPU.

    target_* = CLEAN forward; source_* = KNOCKOUT forward. `_in` is the module input (residual going
    into the matrix), `_out` is the ORIGINAL module output (= _in @ W_base.T, captured before any edit).
    """
    name: str
    W_base: torch.Tensor          # [out, in]
    target_in: torch.Tensor       # [n_t, in]
    target_out: torch.Tensor      # [n_t, out]
    source_in: torch.Tensor       # [n_s, in]
    source_out: torch.Tensor      # [n_s, out]


@dataclass
class OperatorFitConfig:
    rank: int = 1
    preserve_weight: float = 1.0
    steer_weight: float = 1.0
    overcorrect_weight: float = 0.0
    neighbor_count: int = 1
    preserve_row_magnitudes: bool = False
    n_steps: int = 20
    lbfgs_max_iter: int = 20
    lbfgs_history: int = 10
    lr: float = 1.0
    seed: int = 0
    dtype: torch.dtype = torch.float32   # fit in fp32 for L-BFGS stability even if model is bf16
    device: str = "cpu"


@dataclass
class FittedOperator:
    """Result: per-module LoRA factors + effective ΔW (for SVD / application)."""
    config: OperatorFitConfig
    factors: Dict[str, Tuple[torch.Tensor, torch.Tensor]] = field(default_factory=dict)  # name->(A,B)
    loss_history: List[float] = field(default_factory=list)
    final_loss: float = float("nan")

    def delta_w(self, name: str) -> torch.Tensor:
        """Effective ΔW for a module. For preserve_row_magnitudes=False this is exactly B@A; for
        True the true delta is normalize(W_base+BA)*row_norms - W_base and requires W_base (use
        delta_w_with_base)."""
        A, B = self.factors[name]
        return B @ A

    def effective_weight(self, name: str, W_base: torch.Tensor) -> torch.Tensor:
        A, B = self.factors[name]
        W_eff = W_base + B @ A
        if self.config.preserve_row_magnitudes:
            row_norms = W_base.norm(p=2, dim=1, keepdim=True)
            W_eff = torch.nn.functional.normalize(W_eff, p=2, dim=1) * row_norms
        return W_eff

    def delta_w_with_base(self, name: str, W_base: torch.Tensor) -> torch.Tensor:
        return self.effective_weight(name, W_base) - W_base


def _apply_weight(X: torch.Tensor, W_eff: torch.Tensor) -> torch.Tensor:
    # module output for a Linear with weight [out,in]: X[n,in] @ W_eff.T[in,out] -> [n,out]
    return X @ W_eff.t()


def fit_operator(modules: List[ModuleIO], cfg: OperatorFitConfig) -> FittedOperator:
    """Fit a shared-rank low-rank operator jointly across the given modules (ARA-style)."""
    torch.manual_seed(cfg.seed)
    dev, dt = cfg.device, cfg.dtype
    params: List[torch.Tensor] = []
    state: Dict[str, dict] = {}
    for m in modules:
        out_dim, in_dim = m.W_base.shape
        A = torch.zeros(cfg.rank, in_dim, device=dev, dtype=dt)
        torch.nn.init.kaiming_uniform_(A, a=5 ** 0.5)       # PEFT LoRA A init
        B = torch.zeros(out_dim, cfg.rank, device=dev, dtype=dt)  # B=0 => ΔW=0 => identity start
        A.requires_grad_(True); B.requires_grad_(True)
        params += [A, B]
        st = dict(
            A=A, B=B,
            W_base=m.W_base.to(dev, dt),
            t_in=m.target_in.to(dev, dt), t_out=m.target_out.to(dev, dt),
            s_in=m.source_in.to(dev, dt), s_out=m.source_out.to(dev, dt),
        )
        if cfg.preserve_row_magnitudes:
            st["row_norms"] = st["W_base"].norm(p=2, dim=1, keepdim=True)
        state[m.name] = st

    opt = torch.optim.LBFGS(params, lr=cfg.lr, max_iter=cfg.lbfgs_max_iter,
                            history_size=cfg.lbfgs_history, line_search_fn="strong_wolfe")
    loss_hist: List[float] = []

    def closure():
        opt.zero_grad()
        total = torch.zeros((), device=dev, dtype=dt)
        for st in state.values():
            W_eff = st["W_base"] + st["B"] @ st["A"]
            if cfg.preserve_row_magnitudes:
                W_eff = torch.nn.functional.normalize(W_eff, p=2, dim=1) * st["row_norms"]
            new_t = _apply_weight(st["t_in"], W_eff)
            new_s = _apply_weight(st["s_in"], W_eff)
            preserve = ((new_t - st["t_out"]) ** 2).mean()
            steer = mean_distance_to_knn(new_s, st["t_out"], cfg.neighbor_count)
            if cfg.overcorrect_weight > 0:
                steer = steer - cfg.overcorrect_weight * mean_distance_to_knn(new_s, st["s_out"], cfg.neighbor_count)
            total = total + cfg.preserve_weight * preserve + cfg.steer_weight * steer
        total.backward()
        return total

    last = float("nan")
    for _ in range(cfg.n_steps):
        loss = opt.step(closure)
        last = float(loss.detach().cpu())
        loss_hist.append(last)

    factors = {name: (st["A"].detach(), st["B"].detach()) for name, st in state.items()}
    return FittedOperator(config=cfg, factors=factors, loss_history=loss_hist, final_loss=last)


# --------------------------------------------------------------------------------------------
# Rank-matched CONTROLS (plan §10). Each returns per-module (A,B) with the SAME rank & (optionally)
# norm as a fitted operator, so a fitted result is scored against its own null family.
# --------------------------------------------------------------------------------------------
def random_orthogonal_operator(modules: List[ModuleIO], rank: int, target_fro: Dict[str, float],
                               seed: int, device="cpu", dtype=torch.float32
                               ) -> Dict[str, Tuple[torch.Tensor, torch.Tensor]]:
    """Random rank-k ΔW with orthonormal row/col factors, scaled to match a target Frobenius norm."""
    g = torch.Generator(device=device).manual_seed(seed)
    out: Dict[str, Tuple[torch.Tensor, torch.Tensor]] = {}
    for m in modules:
        o, i = m.W_base.shape
        U = torch.linalg.qr(torch.randn(o, rank, generator=g, device=device, dtype=dtype))[0]
        V = torch.linalg.qr(torch.randn(i, rank, generator=g, device=device, dtype=dtype))[0]
        dW = U @ V.t()                       # rank-r, ||dW||_F = sqrt(rank)
        scale = (target_fro[m.name] / (dW.norm() + 1e-12))
        # fold scale into B: A=V.T, B=scale*U
        out[m.name] = (V.t().contiguous(), (scale * U).contiguous())
    return out


def identity_operator(modules: List[ModuleIO], rank: int, device="cpu", dtype=torch.float32
                      ) -> Dict[str, Tuple[torch.Tensor, torch.Tensor]]:
    """No-op adapter (ΔW=0). Must be inert when applied (positive-control sanity)."""
    out = {}
    for m in modules:
        o, i = m.W_base.shape
        out[m.name] = (torch.zeros(rank, i, device=device, dtype=dtype),
                       torch.zeros(o, rank, device=device, dtype=dtype))
    return out
