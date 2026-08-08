#!/usr/bin/env python
"""Build a norm-matched RANDOM direction at L18 for the Gate-7 first-cut specificity control.

CPU-only. Loads the validated L18 refusal direction, draws a Gaussian vector of the same
shape, and rescales it to the SAME L2 norm. Fixed RNG seed for reproducibility. Saves a bare
float32 tensor (same format the GCG optimizer expects: torch.load(..., weights_only=True)).

The output is the specificity control for arm07-rand: optimizing GCG against a random unit
direction should NOT reproduce the refusal-suppression effect of the true L18 direction.
"""
import argparse
import torch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--src",
        default="doublespeak_causality/outputs/refval_clearharm_20260806_051728_721957/refusal_direction_clearharm_L18.pt",
        help="validated L18 refusal direction (bare tensor) to norm-match against",
    )
    ap.add_argument(
        "--out",
        default="doublespeak_causality/outputs/gate7_firstcut/refusal_rand_L18_normmatched_seed20260808.pt",
    )
    ap.add_argument("--seed", type=int, default=20260808)
    args = ap.parse_args()

    v = torch.load(args.src, map_location="cpu", weights_only=True)
    assert torch.is_tensor(v), f"expected bare tensor, got {type(v)}"
    src_norm = float(v.float().norm())
    print(f"[build_rand] src={args.src} shape={tuple(v.shape)} dtype={v.dtype} norm={src_norm:.6f}")

    g = torch.Generator().manual_seed(args.seed)
    r = torch.randn(v.shape, generator=g, dtype=torch.float32)
    r = r / r.norm() * src_norm  # norm-match exactly
    r = r.to(v.dtype)

    cos = float(torch.dot(r.float(), v.float()) / (r.float().norm() * v.float().norm()))
    print(f"[build_rand] out={args.out} shape={tuple(r.shape)} dtype={r.dtype} "
          f"norm={float(r.float().norm()):.6f} cos_with_src={cos:.4f} seed={args.seed}")

    torch.save(r, args.out)
    # round-trip check exactly as the optimizer loads it
    back = torch.load(args.out, map_location="cpu", weights_only=True)
    assert torch.is_tensor(back) and back.shape == v.shape and back.dtype == v.dtype
    assert abs(float(back.float().norm()) - src_norm) < 1e-5
    print("[build_rand] round-trip OK (weights_only=True load matches)")


if __name__ == "__main__":
    main()
