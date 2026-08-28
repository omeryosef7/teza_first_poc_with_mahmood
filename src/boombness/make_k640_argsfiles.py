"""make_k640_argsfiles.py — regenerate the cap-640 knockout reruns FROM THE ORIGINAL RUN CONFIGS.

WHY THIS IS A SCRIPT AND NOT TEN HAND-WRITTEN FILES. Ledger entry (2) — retrieval knockout
suppresses the doublespeak attack — rests on twenty runs that all used `max_new=192`, with
truncation from 0.073 to 0.698. Re-running them at a real cap means changing ONE field and nothing
else, and the trap is that the arms are not uniform across populations:

    main                     -> C_demo_all_L6_14
    ticket_bomb / knives     -> C_band_L6_14
    basket_gun               -> C_band_L6_14

Hand-writing ten argsfiles would have silently normalised those into a single arm name, producing a
DIFFERENT intervention under the old label — the one-word divergence that no output would show.
Deriving from each run's own `config.json` makes that impossible.

The argsfiles land under `outputs/`, which is gitignored, so this script IS the tracked artifact:
without it the "derived, not hand-written" claim in §12.14 is unverifiable from the repo.

Asserts before writing, so a mis-pointed source fails loudly rather than mislabelling a rerun:
  * `max_new == 192`  — the source really is one of the capped runs
  * `model in (None, "")` — Llama is the default; an explicit model here means a Qwen run got
    picked up and would be relabelled as Llama

Reads config.json files and writes text. No model, no GPU, no network.
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SB = os.path.join(ROOT, "outputs", "boombness", "score_behavior")
OUT = os.path.join(ROOT, "outputs", "boombness", "argsfiles")

#: The five Llama populations behind ledger entry (2), as (A-arm run, C-arm run).
RUNS = {
    "main":         ("p2A_20260823_212414_245187", "p2C_band_20260823_214819_248269"),
    "ticket_bomb":  ("lbA_ticket_bomb_20260824_120544_2283985",
                     "lbC_ticket_bomb_20260824_153015_684017"),
    "button_knife": ("lbA_button_knife_20260824_114612_2280721",
                     "lbC_button_knife_20260824_115545_2282473"),
    "window_knife": ("lbA_window_knife_20260824_153015_684018",
                     "lbC_window_knife_20260824_153015_684019"),
    "basket_gun":   ("gnLA_20260824_221640_2352538", "gnLC_20260824_222648_376555"),
}

NEW_CAP = 640


def build(run: str) -> tuple[str, str]:
    """Return (tag, argsfile line) for one source run, changing only the cap."""
    cfg = json.load(open(os.path.join(SB, run, "config.json"), encoding="utf-8"))["args"]
    if cfg["max_new"] != 192:
        raise SystemExit(f"{run}: max_new is {cfg['max_new']}, not 192 — wrong source run")
    if cfg.get("model") not in (None, ""):
        raise SystemExit(f"{run}: model is {cfg['model']!r}; Llama runs leave it unset, so this "
                         f"is a different model and would be relabelled")
    f = [f"--bank {cfg['bank']}",
         f"--query-kinds {cfg['query_kinds']}",
         f"--conditions {cfg['conditions']}",
         f"--bank-blocks {cfg['bank_blocks']}",
         f"--n-examples {cfg['n_examples']}",
         f"--expect-n {cfg['expect_n']}",
         f"--max-new {NEW_CAP}",
         f"--dtype {cfg['dtype']}",
         f"--seed {cfg['seed']}"]
    if cfg.get("attn_impl"):
        f.append(f"--attn-impl {cfg['attn_impl']}")
    if cfg.get("intervene"):
        f.append(f"--intervene {cfg['intervene']}")
    tag = f"k640_{cfg['tag']}"
    f.append(f"--arm {cfg['arm']}")
    f.append(f"--tag {tag}")
    return tag, " ".join(f)


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    for pop, runs in RUNS.items():
        for arm, run in zip(("A", "C"), runs):
            tag, line = build(run)
            open(os.path.join(OUT, tag + ".txt"), "w", encoding="utf-8").write(line + "\n")
            print(f"  {pop:13s} {arm}  {tag}")
    print(f"[k640] {2 * len(RUNS)} argsfiles written to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
