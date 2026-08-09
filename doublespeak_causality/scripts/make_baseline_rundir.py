#!/usr/bin/env python3
"""Create a synthetic run-dir (FINAL_CANDIDATES.jsonl) so 26_eval can evaluate a no-optimization
baseline through the SAME eval path (compute-matched gen budget / judge / denominator).

Baselines for the v3 attack matrix:
  none     -> suffix_str = ""            (arm02 no-suffix doublespeak; arm01 uses direct manifest)
  random   -> suffix_str = 16 random-token string (arm15 length-matched random-suffix control)
"""
import argparse, json, os, random

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--mode", choices=["none", "random"], required=True)
    ap.add_argument("--suffix-length", type=int, default=16)
    ap.add_argument("--seed", type=int, default=20260809)
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    if args.mode == "none":
        suffix_str = ""
    else:
        from transformers import AutoTokenizer
        tok = AutoTokenizer.from_pretrained(args.model)
        rng = random.Random(args.seed)
        vocab = tok.vocab_size
        ids = [rng.randrange(vocab) for _ in range(args.suffix_length)]
        suffix_str = " " + tok.decode(ids, skip_special_tokens=True)
    with open(os.path.join(args.out_dir, "FINAL_CANDIDATES.jsonl"), "w") as f:
        f.write(json.dumps({"suffix_str": suffix_str, "rank": 0,
                            "note": f"synthetic baseline mode={args.mode}"}) + "\n")
    print(f"[baseline] mode={args.mode} suffix_len_chars={len(suffix_str)} -> {args.out_dir}")


if __name__ == "__main__":
    main()
