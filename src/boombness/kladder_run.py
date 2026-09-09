#!/usr/bin/env python3
"""The CONCEPT-FREE K ladder. Successor plan section 10 ("HIGHEST PRIORITY").

WHAT THIS ANSWERS AND WHY THE OLD LADDER COULD NOT
--------------------------------------------------
`PR-032` / `R-080` ran a `query_last_k_rows` ladder and found a sharp step at **K = 7**. On that
run's readout -- `semantic_forced_choice`, *"...does the word button refer to a button or to a
bomb?"* -- rung K = 7 is the rung at which the cut first reaches the literal option token ` bomb`.
Cutting the demonstrations off the token that IS the answer, in an instrument that supplied the
answer, is partly a result about the instrument. `R-083` closed as CANNOT ANSWER for that reason.

On the concept-free template -- *"...what does the word button actually refer to?"*, which contains
the concept word on **0 of 32,544** analysed rows -- the rungs are different objects
(`reports/DCS_TS116M_TOKEN_ROLE_MAP.md`, census constant in 6900/6900 prompts):

    K1..K5   response header + chat scaffold   ZERO query content
    K6  '?'      K7 ' to'      K8 ' refer'     K9 ' actually'   <- the neutral read site
    K10 ' button'  <- THE CODEWORD
    K11 ' word'  K12 ' the'  K13 ' does'  K14 ' what'

So the question the old ladder could not ask is askable by changing one flag: **is the step at the
codeword rung (K = 10), or somewhere else?** If it is at K = 10 on a readout that never names the
answer, that is mechanistic evidence about the codeword. If it is not, the ladder localises
whatever row actually matters and the codeword claim does not survive.

WHY A RUNNER RATHER THAN 30 sbatch JOBS
---------------------------------------
Measured this session: a cold weight load on this cluster took **>10 minutes** under NFS
contention when two jobs loaded at once. Thirty arms x one load each is dominated by IO and would
also thrash the share. This loads the weights ONCE (`ModelCache`, imported from the PHASE-11
runner rather than rewritten) and drives `score_behavior.main()` in-process with `sys.argv` set --
the same mechanism `pr057_run_causal.py` and `pr059_run_localisation.py` use, so the arms are
scored by the house readout and not by a second implementation of it.

CONTROLS
--------
`query_last_k_rows` raises the destination-row count and the cut-cell count TOGETHER, by
construction; `PR-032` says so itself. A rung's own dose-matched `nondemo_matched_d*` control --
the same number of keys blocked from the same rows, drawn from OUTSIDE the demonstration block --
is what separates "cutting the DEMONSTRATIONS matters" from "cutting that many keys matters".
It is constructible here for every rung (verified live on `ts116m` at S_G, option_mass 0.3112,
gate PASS).

DISCIPLINE
----------
EXPLORATORY on `--split train`. This file refuses `test` outright. The ladder's SHAPE is a
development observation; a rung comparison that becomes a claim is frozen in a preregistration and
tested elsewhere, once.

USAGE
  python -u src/boombness/kladder_run.py --plan
  python -u src/boombness/kladder_run.py --split train
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
from typing import Any, Dict, List

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for _p in ("scripts", os.path.join("src", "boombness"), "doublespeak_causality"):
    _f = os.path.join(REPO, _p)
    if _f not in sys.path:
        sys.path.insert(0, _f)

import score_behavior as SB  # noqa: E402
from pr059_run_localisation import ModelCache  # noqa: E402  -- REUSED, not reimplemented

SCORE_SCRIPT = "src/boombness/score_behavior.py"
STATE_ROOT = os.path.join(REPO, "outputs", "boombness", "kladder_runner")

#: The rung -> token map this ladder exists to exploit. Re-derived from the frozen token-role map,
#: NOT retyped from prose: the runner prints it and refuses if `--k-max` would run past the query
#: span. `K` cuts `sorted(query_span)[-K:]`, so rung K reaches rel_end -K.
REL_END_ROLE = {
    -1: "response_header '\\n\\n'", -2: "response_header '<|end_header_id|>'",
    -3: "response_header 'assistant'", -4: "response_header '<|start_header_id|>'",
    -5: "chat_scaffold '<|eot_id|>'", -6: "punctuation '?'",
    -7: "user_instruction_scaffold ' to'", -8: "user_instruction_scaffold ' refer'",
    -9: "user_instruction_scaffold ' actually'  <-- the neutral downstream read site",
    -10: "CODEWORD ' button' / ' basket'  <-- THE RUNG THIS LADDER EXISTS FOR",
    -11: "user_instruction_scaffold ' word'", -12: "user_instruction_scaffold ' the'",
    -13: "user_instruction_scaffold ' does'", -14: "user_instruction_scaffold ' what'",
}
#: 28 rows in the query span; a dose-matched non-demo key control needs a pool of 28-m >= m, so
#: rungs beyond 14 have no matched control and are NOT run by default.
QUERY_SPAN_ROWS = 28


class RunnerRefusal(RuntimeError):
    pass


def build_arms(a) -> List[Dict[str, Any]]:
    ks = [int(x) for x in a.k_list.split(",") if x.strip()]
    if any(k < 1 for k in ks):
        raise RunnerRefusal("K must be >= 1")
    if max(ks) > QUERY_SPAN_ROWS - max(ks):
        raise RunnerRefusal(
            "K = %d leaves a non-demonstration-row pool of %d in a %d-row query span, which is "
            "smaller than the dose. A rung whose dose-matched control cannot be built is not run "
            "silently -- reduce --k-list or state the exemption."
            % (max(ks), QUERY_SPAN_ROWS - max(ks), QUERY_SPAN_ROWS))
    ctrl_ks = set(int(x) for x in a.control_ks.split(",") if x.strip()) if a.control_ks else set(ks)
    draws = [d.strip() for d in a.controls.split(",") if d.strip()]

    arms = [{"arm_id": "K0_baseline", "kind": "baseline", "k": 0, "intervene": "", "draw": ""}]
    for k in ks:
        arms.append({"arm_id": "K%02d_demo" % k, "kind": "demo", "k": k,
                     "intervene": "demo_all:attn_knockout:%s:1.0" % a.band, "draw": "",
                     "rel_end_reached": -k, "role": REL_END_ROLE.get(-k, "BEYOND THE MAPPED SPAN")})
        if k in ctrl_ks:
            for d in draws:
                arms.append({"arm_id": "K%02d_%s" % (k, d), "kind": "control", "k": k,
                             "intervene": "%s:attn_knockout:%s:1.0" % (d, a.band), "draw": d,
                             "rel_end_reached": -k,
                             "role": REL_END_ROLE.get(-k, "BEYOND THE MAPPED SPAN")})
    return arms


def argv_for(a, arm) -> List[str]:
    argv = ["--bank", a.bank, "--query-kinds", a.query_kinds, "--conditions", a.conditions,
            "--n-examples", str(a.n_examples), "--readout-ids", "whole_answer",
            "--attn-impl", "eager", "--max-new", str(a.max_new),
            "--min-option-mass", str(a.min_option_mass),
            "--dtype", "bfloat16", "--model", a.model, "--seed", str(a.seed),
            "--exclude-prompt-ids", a.exclude_prompt_ids, "--expect-n", str(a.expect_n),
            "--arm", arm["arm_id"], "--tag", "%s_%s" % (a.tag_prefix, arm["arm_id"])]
    if arm["kind"] != "baseline":
        argv += ["--intervene", arm["intervene"],
                 "--knockout-scope", "query_last_k_rows", "--knockout-last-k", str(arm["k"])]
    return argv


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", default=os.path.join(
        REPO, "data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl"))
    ap.add_argument("--query-kinds", default="semantic_one_word")
    ap.add_argument("--conditions", default="natural_doublespeak")
    ap.add_argument("--n-examples", type=int, default=4)
    ap.add_argument("--band", default="6-14")
    ap.add_argument("--k-list", default="1,2,3,4,5,6,7,8,9,10,11,12,13,14")
    ap.add_argument("--controls", default="nondemo_matched_d1,nondemo_matched_d2,nondemo_matched_d3")
    ap.add_argument("--control-ks", default="8,9,10,11",
                    help="rungs that get the full control band; empty string = every rung")
    ap.add_argument("--exclude-prompt-ids", default=os.path.join(
        REPO, "runargs/dcs_succ/exclude_button_bomb_sow_cds_n4_sow_C_train.txt"))
    ap.add_argument("--expect-n", type=int, default=670)
    ap.add_argument("--split", default="train", choices=["train", "validation"],
                    help="LABEL ONLY -- it names the run and is recorded in the manifest. The "
                         "population is selected by --exclude-prompt-ids, which is derived from "
                         "the frozen manifest by scripts/dcs_ts_make_exclusions.py. The two are "
                         "cross-checked below; a mismatch is a refusal (F3).")
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--max-new", type=int, default=8)
    ap.add_argument("--min-option-mass", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=20260909)
    ap.add_argument("--tag-prefix", default="ts116m_sowk")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--allow-tail-readout", action="store_true")
    a = ap.parse_args()

    # F3: --split labelled the run but did not select it, so `--split validation` would have run
    # TRAIN data under a manifest saying validation. The exclusion file carries its own provenance
    # header naming the split it was derived for; it is checked against --split here rather than
    # trusted.
    if not os.path.exists(a.exclude_prompt_ids):
        raise RunnerRefusal("--exclude-prompt-ids file not found: %s" % a.exclude_prompt_ids)
    _hdr = "".join(l for l in open(a.exclude_prompt_ids, encoding="utf-8") if l.startswith("#"))
    if ("split=%s" % a.split) not in _hdr:
        raise RunnerRefusal(
            "--split %r does not match the exclusion file's own provenance header. The file is "
            "what selects the population; --split only labels it, so a disagreement means the run "
            "would be recorded as a split it did not use. Header:\n%s" % (a.split, _hdr))

    arms = build_arms(a)
    print("[kladder] %d arms; band %s; split %s; expect-n %d" % (len(arms), a.band, a.split,
                                                                 a.expect_n), flush=True)
    for arm in arms:
        print("[kladder]   %-22s k=%-3s %s" % (arm["arm_id"], arm["k"] or "-",
                                               arm.get("role", "(no knockout)")), flush=True)
    if a.plan:
        for arm in arms:
            print("[kladder] argv %s: %s" % (arm["arm_id"], " ".join(argv_for(a, arm))))
        return 0

    os.makedirs(STATE_ROOT, exist_ok=True)
    state = os.path.join(STATE_ROOT, "%s_%s_MANIFEST.json" % (a.tag_prefix, a.split))
    man = {"started": time.strftime("%Y-%m-%dT%H:%M:%S"), "host": socket.gethostname(),
           "label": "EXPLORATORY -- the ladder SHAPE is a development observation",
           "args": vars(a), "rung_roles": {str(k): v for k, v in REL_END_ROLE.items()},
           "arms": []}

    cache = ModelCache().install()
    rc_all = 0
    for i, arm in enumerate(arms, 1):
        argv = argv_for(a, arm)
        print("\n[kladder] === [%d/%d] %s ===\n[kladder]     %s"
              % (i, len(arms), arm["arm_id"], " ".join(argv)), flush=True)
        t0 = time.time()
        old = sys.argv
        sys.argv = [SCORE_SCRIPT] + argv
        try:
            rc = SB.main()
        except SystemExit as e:            # score_behavior refuses with SystemExit
            # `score_behavior` raises SystemExit with a STRING message on every refusal path, and
            # `int("[score] REFUSING: ...")` raises ValueError INSIDE this handler -- which Python
            # does NOT route to the sibling `except Exception`. The whole ladder would die on the
            # first refusing rung, which is exactly the PR-065 stop-scope failure this runner was
            # written to avoid. Found by the 2026-09-09 four-hourly code review, finding F4.
            code = e.code
            if code is None:
                rc = 0
            elif isinstance(code, int):
                rc = code
            else:
                rc = 2
                print("[kladder] arm %s refused: %s" % (arm["arm_id"], code), flush=True)
        except Exception as e:             # noqa: BLE001 -- an arm must not take down the ladder
            rc = 99
            print("[kladder] arm %s raised %r" % (arm["arm_id"], e), flush=True)
        finally:
            sys.argv = old
        dt = time.time() - t0
        rec = dict(arm)
        rec.update({"rc": rc, "seconds": round(dt, 1), "argv": argv})
        man["arms"].append(rec)
        # An arm that trips the option-mass gate exits 4. That is a CANNOT ANSWER for THAT ARM and
        # the ladder continues -- PR-065's stop-scope lesson, applied here by construction rather
        # than inherited: a fail-fast that destroys the other rungs is a scope error, not caution.
        print("[kladder] arm %s rc=%d in %.1fs%s"
              % (arm["arm_id"], rc, dt,
                 "  <- OPTION-MASS GATE: this rung is CANNOT ANSWER, the ladder continues"
                 if rc == 4 else ""), flush=True)
        if rc not in (0, 4):
            rc_all = rc
        with open(state, "w", encoding="utf-8") as fh:
            json.dump(man, fh, indent=1)

    man["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    man["model_loads"] = cache.n_loads
    man["model_cache_hits"] = cache.n_hits
    with open(state, "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=1)
    print("\n[kladder] wrote %s; model_loads=%d (MUST be 1) cache_hits=%d"
          % (state, cache.n_loads, cache.n_hits), flush=True)
    if cache.n_loads != 1:
        print("[kladder] REFUSING TO CALL THIS A SINGLE-LOAD RUN: %d loads" % cache.n_loads)
        return 5
    return rc_all


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RunnerRefusal as e:
        print("REFUSING: %s" % e, file=sys.stderr)
        raise SystemExit(2)
