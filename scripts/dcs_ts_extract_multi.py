#!/usr/bin/env python3
"""Extract several banks SEQUENTIALLY inside one GPU allocation.

WHY THIS EXISTS — a scheduling fact, not a scientific one. The six per-bank extractions were
submitted as six jobs at the phase's concurrency cap. Two started; the other four sat PENDING for
32 minutes with SLURM estimating starts 5–8 hours out (10:09, 10:37, 12:04, 12:34) because
`killable` was saturated. Four jobs waiting for four scarce slots is the wrong shape when each
unit of work is ~30 minutes: one slot held for two hours beats four slots that never arrive.

The house rule is to cancel and resubmit with a different configuration when a job is pending past
30 minutes, measured by `SUBMIT_TIME` rather than by elapsed. The nodelist is already all six L40S
nodes, so there is nothing to widen — the change available is the JOB SHAPE, and this is it.

NOTHING SCIENTIFIC CHANGES. Each bank is extracted by exactly the same
`scripts/dcs_extract_under_ko.py` with exactly the same flags it would have received as its own
job. This driver only chooses when they run. It shells out per bank rather than importing, so each
bank gets a clean interpreter and a clean CUDA context — the ~25 s reload is a rounding error
against a 30-minute extraction, and a leaked hook or a mutated global cannot cross from one bank
to the next.

FAIL-CLOSED. A non-zero exit from any bank stops the run and is reported; the driver never
continues past a failure and never reports success it did not observe. Each bank's own stdout is
streamed through unmodified so `head` on the log still answers "did this run what I meant?" for
every bank, per mandate §26.10.

USAGE
    python3 scripts/dcs_ts_extract_multi.py --banks basket_bomb,basket_knife --tag-prefix ts116m_full
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXTRACT = os.path.join(REPO, "scripts", "dcs_extract_under_ko.py")
BANK_TMPL = "data/boombness_prompts/boombness_prompt_bank_{family}_{name}.jsonl"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--banks", required=True, help="comma list, e.g. button_gun,basket_bomb")
    ap.add_argument("--family", default="ts116m")
    ap.add_argument("--tag-prefix", default="ts116m_full")
    ap.add_argument("--layers", default="6,7,8,9,10,11,12,13,14")
    ap.add_argument("--position", default="codeword_last")
    a = ap.parse_args()

    names = [b for b in a.banks.split(",") if b]
    if not names:
        print("ERROR --banks resolved to an empty list; refusing a no-op run", file=sys.stderr)
        return 2

    print(f"=== extract-multi: {len(names)} bank(s) sequentially in one allocation ===", flush=True)
    for n in names:
        print(f"    {n}", flush=True)

    for i, name in enumerate(names, 1):
        bank = os.path.join(REPO, BANK_TMPL.format(family=a.family, name=name))
        if not os.path.exists(bank):
            print(f"ERROR bank does not exist: {bank}", file=sys.stderr)
            return 2
        cmd = [sys.executable, "-u", EXTRACT,
               "--bank", bank, "--no-knockout",
               "--layers", a.layers, "--position", a.position,
               "--tag", f"{a.tag_prefix}_{name}"]
        print(f"\n=== [{i}/{len(names)}] {name} ===", flush=True)
        print("    " + " ".join(cmd), flush=True)
        t0 = time.time()
        rc = subprocess.call(cmd, cwd=REPO)
        dt = time.time() - t0
        print(f"=== [{i}/{len(names)}] {name} exit={rc} elapsed={dt/60:.1f} min ===", flush=True)
        if rc != 0:
            print(f"ERROR bank {name} exited {rc}; STOPPING rather than continuing past a failure",
                  file=sys.stderr)
            return rc

    print(f"\n[extract-multi] all {len(names)} bank(s) completed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
