#!/bin/bash
# Build the DCS thesis-scale ALIGNED concept banks.  `DCS-PR-046`, 2026-09-06.
#
# SIX BANKS: {button, basket} x {bomb, knife, gun}, 116 domains, 22,272 rows each.
#
# WHAT MAKES THEM ALIGNED, and why it is worth a script rather than six ad-hoc commands.
# The estimand is Matan's: hold the codeword, the context skeleton and the benign baseline
# fixed and vary ONLY the installed concept. That property is produced by three things that
# must be IDENTICAL across all six invocations, and is destroyed if any one of them drifts:
#
#   1. the same pools file       -- demo_pools_116dom.json, pools_sha16 976aa2b0b617118d
#   2. the same seed             -- 20260901, which fixes which sentences each family draws
#   3. THE SAME REPAIR MAP       -- the union of every codeword's and every concept's
#                                   incidental collisions, applied to every build
#
# (3) is the subtle one and the reason this file exists. `apply_incidental_repairs` rewrites
# the pools IN MEMORY before generation. A per-concept map therefore produces per-concept
# pools -- byte-alignment gone, in exactly the contrast the phase exists to measure, with no
# downstream guard that would notice. Measured collisions on this pools file:
#     button 16 (filler)   basket 74 (66 remap, 8 benign)   knife 2 (benign)
#     gun    1  (benign)   bomb   0
# so the union map is button=switch, basket=hamper, knife=peeler, gun=beacon, and it is passed
# to all six builds. The three concept collisions were invisible until `DCS-C-072` extended
# main()'s screen from the codeword to the concept.
#
# VERIFIED OUTPUT, all four concept contrasts, case-preserving whole-word swap:
#     button: bomb vs knife  22272/22272 aligned
#     button: bomb vs gun    22272/22272 aligned
#     basket: bomb vs knife  22272/22272 aligned
#     basket: bomb vs gun    22272/22272 aligned
# and the n_examples=0 null is EXACTLY byte-identical across concepts in both concept-free
# channels (928 rows = 2 cells x 2 query kinds x 232).
#
# THE ROWS ARE NOT COMMITTED. Six banks x 70 MB = 420 MB against a .git that is already
# 4.3 GB, for content that regenerates byte-identically in seconds. What IS committed is each
# bank's `_meta.json`, which pins `bank_rows_sha16`, the pools hash, the seed, the preset and
# the repair map -- so the content is fully determined and independently checkable. Run this
# script to materialise them; `--check` verifies what is on disk against the recorded hashes.
#
# ⚠ THE PRICE OF ALIGNMENT, and it must appear in the write-up. The harm pools' natural word is
# `bomb` in all 116 domains, so `--concept knife` produces bomb-demonstration text with the
# word swapped: "a suspicious package resembling a knife". The predicates stay bomb-affording.
# Naturalness is exactly what separately-generated per-concept pools would buy, at the cost of
# the cross-concept corpus confound that voids the comparison. You cannot have both from this
# generator. We take alignment, and INSTALLATION IS MEASURED PER CONCEPT rather than assumed --
# if knife and gun do not install, that is a finding about the population, not a nuisance to
# quietly drop (MANDATE §15).
set -euo pipefail
cd "$(dirname "$0")/.."

POOLS=data/boombness_prompts/demo_pools_116dom.json
PRESET=main_longpre_cds_ts
SEED=20260901
REPAIRS='button=switch,basket=hamper,knife=peeler,gun=beacon'

MODE="${1:-build}"   # `build` regenerates then verifies; `check` verifies what is on disk
fail=0
for cw in button basket; do
  for cc in bomb knife gun; do
    out="data/boombness_prompts/boombness_prompt_bank_ts116_${cw}_${cc}.jsonl"
    if [[ "$MODE" == "build" ]]; then
      PYTHONPATH=src python3 -m boombness.prompt_families \
        --pools "$POOLS" --preset "$PRESET" --codeword "$cw" --concept "$cc" \
        --seed "$SEED" --strict --incidental-replace "$REPAIRS" --out "$out" >/dev/null
    fi
    if [[ ! -s "$out" ]]; then
      echo "MISSING $out" >&2; fail=1; continue
    fi
    meta="${out%.jsonl}_meta.json"
    want=$(python3 -c "import json;print(json.load(open('$meta'))['stats']['bank_rows_sha16'])")
    # Re-derive with the repo's OWN canonical helper -- sha256 over the per-row prompt_sha16
    # ordered by prompt_id -- rather than reimplementing it. A second implementation that
    # disagreed would be indistinguishable from bank drift, which is the failure this check
    # exists to detect. Pairs, not a mapping: a duplicated prompt_id must not be able to make
    # two banks agree by losing a row (`common.rows_sha16`).
    got=$(PYTHONPATH=src python3 -c "
import json
from boombness.common import rows_sha16
pairs=[]
for l in open('$out'):
    r=json.loads(l); pairs.append((r['prompt_id'], r['prompt_sha16']))
print(rows_sha16(pairs))")
    if [[ "$want" == "$got" ]]; then
      printf 'OK   %-14s rows_sha16=%s\n' "${cw}_${cc}" "$got"
    else
      printf 'DRIFT %-13s meta=%s disk=%s\n' "${cw}_${cc}" "$want" "$got" >&2; fail=1
    fi
  done
done
[[ $fail -eq 0 ]] || { echo "[build-banks] FAILED" >&2; exit 1; }
echo "[build-banks] 6/6 banks present and matching their recorded bank_rows_sha16"
