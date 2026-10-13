"""Small LoRA-factor helpers for the HERETIC-CSI drivers (pure torch; unit-tested in tests/test_lora_utils.py)."""
import torch


def factor_svals(Bw, Aw, scaling=1.0):
    """Singular values of dW = scaling * B @ A without forming dW.
    B = Qb Rb, A^T = Qa Ra  =>  dW = scaling * Qb (Rb Ra^T) Qa^T, so svals(dW) = svals(scaling * Rb Ra^T)."""
    Bw, Aw = Bw.detach().float(), Aw.detach().float()
    _, Rb = torch.linalg.qr(Bw)
    _, Ra = torch.linalg.qr(Aw.T)
    return torch.linalg.svdvals(float(scaling) * (Rb @ Ra.T)).cpu()


def spectrum_matched_factors(S, out_dim, in_dim, scaling=1.0, generator=None):
    """Random LoRA factors (B: out x r, A: r x in) with scaling * B @ A == U diag(S) V^T, U/V random orthonormal."""
    r = S.numel()
    U, _ = torch.linalg.qr(torch.randn(out_dim, r, generator=generator))
    V, _ = torch.linalg.qr(torch.randn(in_dim, r, generator=generator))
    S = S.float().clamp_min(0)
    return (U * S.sqrt()) / float(scaling), S.sqrt()[:, None] * V.T
