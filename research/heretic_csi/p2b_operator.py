#!/usr/bin/env python3
"""P2b: position-aware WEIGHT-space operator (ΔW = B@A on attn.o_proj / mlp.down_proj).

What this adds on top of `operator_ara.py` (which it reuses: `mean_distance_to_knn`,
`random_orthogonal_operator`, `identity_operator`):

1. A FACTORED objective. The captured module output IS `x @ W_base.T` (bf16, as the model computed it),
   so the edited output is `out + (x @ A.T) @ B.T` -- exactly what the forward hook below adds at run
   time. No dense W_base is materialised (down_proj is 4096x14336) and the fit and the application use
   the same arithmetic.
2. Objective VARIANTS (mandate §8), compared on TRAIN by a fitting-side CV criterion, never on the
   endpoint: `knn` (ARA's original kNN steer), `mse` (paired), `cos` (paired angular), `whiten` (paired,
   per-dim whitened by the TARGET std).
3. `OperatorHooks`: a weight edit implemented as a forward hook on each Linear (fp32 delta, cast to the
   module's dtype) -- active at EVERY position, like a real weight edit / Heretic's LoRA adapter. A plain
   in-place `W += BA` in bf16 would round small ΔW entries away (bf16 has ~3 significant digits).
4. `CaptureHooks`: reads module input/output rows at explicit per-example positions (never `[:, -1]`
   unless asked), batch row 0 only, first forward per arming only.

Naming: TARGET = clean (no-knockout) codeword-row state; SOURCE = knockout codeword-row state
(Heretic's good -> target, bad -> source; plan §6).
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, asdict
from types import SimpleNamespace
from typing import Dict, List, Optional, Sequence, Tuple

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from operator_ara import mean_distance_to_knn, random_orthogonal_operator, identity_operator  # noqa: E402

OBJECTIVES = ("knn", "mse", "cos", "whiten")
COMPONENTS = {"o_proj": "self_attn.o_proj", "down_proj": "mlp.down_proj"}


def module_name(layer: int, comp: str) -> str:
    return f"L{layer}.{comp}"


def parse_module_name(name: str) -> Tuple[int, str]:
    l, c = name.split(".", 1)
    return int(l[1:]), c


def get_linear(model, name: str) -> torch.nn.Linear:
    layer, comp = parse_module_name(name)
    mod = model.model.layers[layer]
    for part in COMPONENTS[comp].split("."):
        mod = getattr(mod, part)
    return mod


# ----------------------------------------------------------------------------------------------
# Data for one module: paired rows (row i of source <-> row i of target = the SAME prompt).
# ----------------------------------------------------------------------------------------------
@dataclass
class PairedIO:
    name: str
    s_in: torch.Tensor     # [n, in]   SOURCE (KO) module input at the fit position
    s_out: torch.Tensor    # [n, out]  SOURCE module output
    t_in: torch.Tensor     # [n, in]   TARGET (clean) module input, same prompts, same position
    t_out: torch.Tensor    # [n, out]
    p_in: torch.Tensor     # [m, in]   PRESERVE set inputs (clean states that must not move)

    @property
    def shape(self) -> Tuple[int, int]:      # (out, in), Linear convention
        return (self.s_out.shape[1], self.s_in.shape[1])


@dataclass
class FitCfg:
    rank: int = 1
    objective: str = "mse"
    preserve_weight: float = 1.0
    steer_weight: float = 1.0
    overcorrect_weight: float = 0.0     # knn only (ARA's push-away term)
    neighbor_count: int = 1             # knn only
    n_steps: int = 15
    lbfgs_max_iter: int = 20
    seed: int = 0
    device: str = "cpu"


def _delta(X, A, B):
    return (X @ A.t()) @ B.t()


def _steer(cfg: FitCfg, new_s, t_out, s_out, inv_std):
    if cfg.objective == "mse":
        return ((new_s - t_out) ** 2).sum(1).mean()
    if cfg.objective == "whiten":
        return (((new_s - t_out) * inv_std) ** 2).sum(1).mean()
    if cfg.objective == "cos":
        return (1.0 - torch.nn.functional.cosine_similarity(new_s, t_out, dim=1)).mean()
    if cfg.objective == "knn":
        st = mean_distance_to_knn(new_s, t_out, cfg.neighbor_count)
        if cfg.overcorrect_weight > 0:
            st = st - cfg.overcorrect_weight * mean_distance_to_knn(new_s, s_out, cfg.neighbor_count)
        return st
    raise ValueError(f"unknown objective {cfg.objective!r}")


def _norms(m: PairedIO, cfg: FitCfg, dev):
    """Per-module scale so every module/objective term is O(1) at ΔW=0: steer and preserve are both
    divided by the SOURCE->TARGET gap at the start (mse/whiten: mean squared gap; knn: initial kNN
    distance; cos: initial 1-cos). Preserve is divided by the same gap energy as mse so 'preserve 1,
    steer 1' means 'damage measured in units of the gap you are closing'."""
    s_out, t_out = m.s_out.to(dev).float(), m.t_out.to(dev).float()
    gap2 = ((s_out - t_out) ** 2).sum(1).mean().clamp_min(1e-12)
    inv_std = 1.0 / t_out.std(0).clamp_min(1e-3)
    with torch.no_grad():
        st0 = _steer(cfg, s_out, t_out, s_out, inv_std).abs().clamp_min(1e-12)
    return gap2, st0, inv_std


def fit_factored(mods: Sequence[PairedIO], cfg: FitCfg) -> Dict[str, Tuple[torch.Tensor, torch.Tensor]]:
    """Joint L-BFGS fit of per-module rank-r factors (A [r,in], B [out,r]); B=0 start => identity."""
    torch.manual_seed(cfg.seed)
    dev = cfg.device
    st, params = {}, []
    for m in mods:
        o, i = m.shape
        A = torch.empty(cfg.rank, i, device=dev)
        torch.nn.init.kaiming_uniform_(A, a=5 ** 0.5)
        B = torch.zeros(o, cfg.rank, device=dev)
        A.requires_grad_(True); B.requires_grad_(True)
        params += [A, B]
        gap2, st0, inv_std = _norms(m, cfg, dev)
        st[m.name] = dict(A=A, B=B, s_in=m.s_in.to(dev).float(), s_out=m.s_out.to(dev).float(),
                          t_out=m.t_out.to(dev).float(), p_in=m.p_in.to(dev).float(),
                          gap2=gap2, st0=st0, inv_std=inv_std)
    opt = torch.optim.LBFGS(params, lr=1.0, max_iter=cfg.lbfgs_max_iter, history_size=10,
                            line_search_fn="strong_wolfe")

    def closure():
        opt.zero_grad()
        tot = torch.zeros((), device=dev)
        for s in st.values():
            new_s = s["s_out"] + _delta(s["s_in"], s["A"], s["B"])
            preserve = (_delta(s["p_in"], s["A"], s["B"]) ** 2).sum(1).mean() / s["gap2"]
            steer = _steer(cfg, new_s, s["t_out"], s["s_out"], s["inv_std"]) / s["st0"]
            tot = tot + cfg.preserve_weight * preserve + cfg.steer_weight * steer
        tot.backward()
        return tot

    for _ in range(cfg.n_steps):
        opt.step(closure)
    return {n: (s["A"].detach().cpu(), s["B"].detach().cpu()) for n, s in st.items()}


# ----------------------------------------------------------------------------------------------
# Fitting-side diagnostics (objective-NEUTRAL; used for the CV selection, never the endpoint).
# ----------------------------------------------------------------------------------------------
@torch.no_grad()
def gap_closure(mods: Sequence[PairedIO], factors, device="cpu") -> Dict[str, float]:
    """Pooled over modules: GC = 1 - sum||s_out+Δ(s_in) - t_out||^2 / sum||s_out - t_out||^2 and
    damage PD = sum||Δ(p_in)||^2 / (n_p/n_s * sum||s_out - t_out||^2) (preserve-set movement in units of
    the gap). Net = GC - PD."""
    num = den = dmg = 0.0
    for m in mods:
        A, B = (x.to(device).float() for x in factors[m.name])
        s_in, s_out, t_out = (x.to(device).float() for x in (m.s_in, m.s_out, m.t_out))
        p_in = m.p_in.to(device).float()
        num += float(((s_out + _delta(s_in, A, B) - t_out) ** 2).sum())
        g = float(((s_out - t_out) ** 2).sum())
        den += g
        dmg += float((_delta(p_in, A, B) ** 2).sum()) * (s_in.shape[0] / max(1, p_in.shape[0]))
    gc = 1.0 - num / max(den, 1e-12)
    pd = dmg / max(den, 1e-12)
    return {"gap_closure": gc, "preserve_damage": pd, "net": gc - pd}


def fro_norm(A: torch.Tensor, B: torch.Tensor) -> float:
    """||B@A||_F without forming it: sqrt(trace((A A^T)(B^T B)))."""
    A, B = A.double(), B.double()
    return float(torch.sqrt(torch.clamp(torch.trace((A @ A.t()) @ (B.t() @ B)), min=0.0)))


def numerical_rank(A: torch.Tensor, B: torch.Tensor, rtol: float = 1e-6) -> int:
    s = torch.linalg.svdvals((B.double() @ A.double()) if B.shape[0] * A.shape[1] <= 2e7
                             else _small_core(A, B))
    return int((s > rtol * s.max().clamp_min(1e-30)).sum())


def _small_core(A, B):
    # singular values of B@A equal those of R_B @ R_A^T where B=Q_B R_B, A^T=Q_A R_A
    _, Rb = torch.linalg.qr(B.double())
    _, Ra = torch.linalg.qr(A.double().t())
    return Rb @ Ra.t()


def rescale_to(factors, target_norms: Dict[str, float]):
    """Scale each module's B so ||B@A||_F equals target_norms[name] (norm matching)."""
    out = {}
    for n, (A, B) in factors.items():
        cur = fro_norm(A, B)
        out[n] = (A, B * (target_norms[n] / cur if cur > 0 else 0.0))
    return out


def random_norm_matched(shapes: Dict[str, Tuple[int, int]], rank: int, target_norms: Dict[str, float],
                        seed: int):
    """Reuses operator_ara.random_orthogonal_operator (rank-r, orthonormal factors, Fro-matched)."""
    mods = [SimpleNamespace(name=n, W_base=torch.empty(o, i, device="meta")) for n, (o, i) in shapes.items()]
    return random_orthogonal_operator(mods, rank, target_norms, seed=seed)


def identity_factors(shapes: Dict[str, Tuple[int, int]], rank: int):
    mods = [SimpleNamespace(name=n, W_base=torch.empty(o, i, device="meta")) for n, (o, i) in shapes.items()]
    return identity_operator(mods, rank)


# ----------------------------------------------------------------------------------------------
# Runtime hooks
# ----------------------------------------------------------------------------------------------
class OperatorHooks:
    """Apply ΔW=B@A to named Linear modules for the duration of a `with` block (all positions)."""

    def __init__(self, model, factors: Dict[str, Tuple[torch.Tensor, torch.Tensor]]):
        self.model, self.factors, self.handles = model, factors, []
        self.n_calls = 0
        self.delta_norm_sum = 0.0

    def __enter__(self):
        for name, (A, B) in self.factors.items():
            lin = get_linear(self.model, name)
            dev = lin.weight.device
            At, Bt = A.to(dev, torch.float32).contiguous(), B.to(dev, torch.float32).contiguous()

            def hook(mod, inp, out, At=At, Bt=Bt):
                d = (inp[0].float() @ At.t()) @ Bt.t()
                self.n_calls += 1
                self.delta_norm_sum += float(d[0, -1].norm())
                return out + d.to(out.dtype)
            self.handles.append(lin.register_forward_hook(hook))
        return self

    def __exit__(self, *exc):
        for h in self.handles:
            h.remove()
        self.handles = []
        return False


class CaptureHooks:
    """Record (input, output) of named Linear modules at explicit positions of batch row 0.

    `arm(positions)` sets the positions for the NEXT forward only; the first forward after arming is
    recorded into `self.records` (one dict per arming) and capture disarms itself, so the variant
    forwards of a multi-variant readout (which share the same prefix) are not recorded twice.
    """

    def __init__(self, model, names: Sequence[str]):
        self.model, self.names, self.handles = model, list(names), []
        self.pending: Optional[Dict[str, int]] = None
        self.current: Optional[Dict] = None
        self.records: List[Dict] = []
        self._seen = set()

    def arm(self, positions: Dict[str, int], meta: Dict):
        self.pending = dict(positions)
        self.current = {"meta": dict(meta), "acts": {}}
        self._seen = set()

    def __enter__(self):
        for name in self.names:
            lin = get_linear(self.model, name)

            def hook(mod, inp, out, name=name):
                if self.pending is None or name in self._seen:
                    return None
                x, y = inp[0], out
                rec = {}
                for tag, pos in self.pending.items():
                    if not (0 <= pos < x.shape[1]):
                        raise IndexError(f"capture position {pos} outside forward length {x.shape[1]}")
                    rec[tag] = (x[0, pos].detach().to("cpu", torch.bfloat16).clone(),
                                y[0, pos].detach().to("cpu", torch.bfloat16).clone())
                self.current["acts"][name] = rec
                self._seen.add(name)
                if len(self._seen) == len(self.names):
                    self.records.append(self.current)
                    self.pending, self.current = None, None
                return None
            self.handles.append(lin.register_forward_hook(hook))
        return self

    def __exit__(self, *exc):
        for h in self.handles:
            h.remove()
        self.handles = []
        return False
