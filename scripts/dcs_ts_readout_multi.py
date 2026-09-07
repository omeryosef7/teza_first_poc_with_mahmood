#!/usr/bin/env python3
"""Run `score_behavior.py` over several banks SEQUENTIALLY in one GPU allocation.

`DCS-PR-054`, PHASE 7. Sibling of `dcs_ts_extract_multi.py`, for the same scheduling reason
(`C-102`): fair-share is spent, so one allocation held for a while beats six that never start.

WHY THIS RUN EXISTS, and it is a prerequisite rather than an extra. Three things depend on it:

  * MANDATE section 15 -- the prompt-validation table. Every claim in this phase so far rests on
    the ASSUMPTION that the demonstrations install their concept. That has never been measured.
    `A-037` established the pools carry the right affordances; it could not establish that the
    MODEL takes them up.
  * PHASE 9's outcome variable. A causal intervention needs something to move. Without a semantic
    readout there is nothing to measure the intervention against, and `R-097`'s CANNOT ANSWER --
    "no behavioural outcome exists on the bank x was measured on" -- would repeat exactly.
  * The `option_mass` diagnostic that decides whether `semantic_one_word` is even engaged. The
    preregistration says in terms that a disengaged channel is a CANNOT ANSWER on the primary, not
    a licence to fall back on the display channel.

Nothing scientific differs from running each bank alone: same script, same flags, a clean
interpreter and CUDA context per bank, fail-closed on any non-zero exit, and each bank's stdout
streamed through so section 26.10 stays answerable per bank.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORE = os.path.join(REPO, "src", "boombness", "score_behavior.py")
BANK_TMPL = "data/boombness_prompts/boombness_prompt_bank_{family}_{name}.jsonl"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--banks", required=True)
    ap.add_argument("--family", default="ts116m")
    ap.add_argument("--tag-prefix", default="ts116m_readout")
    ap.add_argument("--query-kinds", default="semantic_one_word,semantic_forced_choice")
    ap.add_argument("--conditions", default="natural_doublespeak,benign_literal")
    ap.add_argument("--n-examples", default="0,4")
    ap.add_argument("--max-new", type=int, default=8)
    ap.add_argument("--attn-impl", default="eager")
    ap.add_argument("--arm", default="base")
    ap.add_argument("--intervene", default="")
    ap.add_argument("--fit-dir", default="")
    a = ap.parse_args()

    names = [b for b in a.banks.split(",") if b]
    if not names:
        print("ERROR --banks resolved to an empty list; refusing a no-op run", file=sys.stderr)
        return 2

    print(f"=== readout-multi: {len(names)} bank(s), arm={a.arm} ===", flush=True)
    print(f"    query_kinds={a.query_kinds}  conditions={a.conditions}  n_examples={a.n_examples}",
          flush=True)

    for i, name in enumerate(names, 1):
        bank = os.path.join(REPO, BANK_TMPL.format(family=a.family, name=name))
        if not os.path.exists(bank):
            print(f"ERROR bank does not exist: {bank}", file=sys.stderr)
            return 2
        cmd = [sys.executable, "-u", SCORE,
               "--bank", bank,
               "--query-kinds", a.query_kinds,
               "--conditions", a.conditions,
               "--n-examples", a.n_examples,
               "--max-new", str(a.max_new),
               "--attn-impl", a.attn_impl,
               "--arm", a.arm,
               "--tag", f"{a.tag_prefix}_{name}"]
        if a.intervene:
            cmd += ["--intervene", a.intervene]
            if not a.fit_dir:
                print("ERROR --intervene requires --fit-dir", file=sys.stderr)
                return 2
            cmd += ["--fit-dir", a.fit_dir]
        print(f"\n=== [{i}/{len(names)}] {name} ===", flush=True)
        print("    " + " ".join(cmd), flush=True)
        t0 = time.time()
        rc = subprocess.call(cmd, cwd=REPO)
        print(f"=== [{i}/{len(names)}] {name} exit={rc} elapsed={(time.time()-t0)/60:.1f} min ===",
              flush=True)
        if rc != 0:
            print(f"ERROR bank {name} exited {rc}; STOPPING rather than continuing past a failure",
                  file=sys.stderr)
            return rc

    print(f"\n[readout-multi] all {len(names)} bank(s) completed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
