#!/usr/bin/env python
"""Build norm-matched RANDOM directions at ARBITRARY layers for the v3 attack-objective matrix.

Generalizes scripts/build_random_dir_L18.py to any set of layers, matching each layer's own
source-direction L2 norm (so the random control is norm-matched PER LAYER, as plan §6 requires:
"If there are multiple vector magnitudes / layers, random controls must match those too").

CPU-only. Saves bare float32 tensors the GCG optimizer loads with weights_only=True.
Deterministic: per-layer generator seed = base_seed + layer (independent draws, like
phase_refusal_projection.norm_matched_random).
"""
import argparse, os, torch

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-dir", default=os.path.join(HERE, "outputs/refusal_alllayers"),
                    help="dir with refusal_direction_llama_L{k}.pt (fit-layer named)")
    ap.add_argument("--src-prefix", default="refusal_direction_llama_L")
    ap.add_argument("--layers", default="12,18", help="comma fit-layers to build randoms for")
    ap.add_argument("--out-dir", default=os.path.join(HERE, "outputs/gate7_v3_randdirs"))
    ap.add_argument("--base-seed", type=int, default=20260809)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    for L in [int(x) for x in args.layers.split(",")]:
        src = os.path.join(args.src_dir, f"{args.src_prefix}{L}.pt")
        v = torch.load(src, map_location="cpu", weights_only=True)
        assert torch.is_tensor(v), f"expected bare tensor at {src}, got {type(v)}"
        src_norm = float(v.float().norm())
        g = torch.Generator().manual_seed(args.base_seed + L)
        r = torch.randn(v.shape, generator=g, dtype=torch.float32)
        r = (r / r.norm() * src_norm).to(v.dtype)
        cos = float(torch.dot(r.float(), v.float()) / (r.float().norm() * v.float().norm() + 1e-8))
        out = os.path.join(args.out_dir, f"refusal_rand_L{L}_normmatched_seed{args.base_seed}.pt")
        torch.save(r, out)
        back = torch.load(out, map_location="cpu", weights_only=True)
        assert torch.is_tensor(back) and back.shape == v.shape and back.dtype == v.dtype
        assert abs(float(back.float().norm()) - src_norm) < 1e-4
        print(f"[rand] L{L} shape={tuple(r.shape)} norm={src_norm:.5f} cos_with_src={cos:.4f} -> {os.path.relpath(out, HERE)}")


if __name__ == "__main__":
    main()
