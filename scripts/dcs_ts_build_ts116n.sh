#!/bin/bash
# Build the DCS thesis-scale ALIGNED concept banks, corrected.  `DCS-PR-046` / `DCS-C-074`.
#
# SIX BANKS: {button, basket} x {bomb, knife, gun}, 116 domains.
#
# HOW THIS DIFFERS FROM `dcs_ts_build_banks.sh`, and it is the whole point.
# That script built all six banks from ONE pools file whose harm pool has natural_word="bomb",
# asking prompt_families for a different --concept each time. Because cell C draws the harm pool
# at demo_surface="codeword", the concept word is substituted away before assembly, so the three
# arms came out byte-identical and the probe was pinned to 1/3 by arithmetic (C-074).
#
# Here each concept gets its OWN pools file, in which:
#   * the HARM pool is generated for that concept -- this is the manipulation, and it survives
#     the codeword substitution because it lives in the PREDICATES ("confiscated a knife before
#     boarding") rather than in a word that gets replaced;
#   * benign / remap / filler are copied BYTE-FOR-BYTE from demo_pools_116dom.json -- this is the
#     alignment, and it is what the old 6-domain banks lacked when they regenerated every valence
#     per concept (A-034.1).
# All three harm pools were generated in ONE family: same generator, same domain style hints,
# same seed 20260906, differing only in the concept word passed to gen_demos. The bomb pool is
# regenerated too rather than inherited from the shared file, because inheriting it would make
# the bomb arm differ from the other two in WHEN and UNDER WHICH SEED it was produced -- a
# concept x generation-run confound that would make any bomb-vs-rest asymmetry uninterpretable.
#
# THE REPAIR MAP IS STILL THE UNION AND STILL IDENTICAL ACROSS ALL SIX BUILDS.
# apply_incidental_repairs rewrites the pools in memory before generation, so a per-concept map
# produces per-concept pools and destroys the alignment. It never rewrites a pool's OWN natural
# word, so knife=peeler does not touch the knife harm pool.
#
# AFTER BUILDING, RUN THE GATES. `dcs_ts_verify_ts116n.py` checks the matched pair: G2 (cell C
# DIFFERS across concepts in 116/116 domains -- the manipulation exists) and G3 (cell A is
# byte-identical -- everything else is shared). Neither is allowed to pass alone. An alignment
# check on its own can only fail in one direction, which is exactly how C-074 got through.
set -euo pipefail
cd "$(dirname "$0")/.."

PRESET=main_longpre_cds_ts
SEED=20260901
# TAG selects the pools/bank family. ts116n = the first per-concept-harm build; ts116m = the same
# with the C-076 inflection filter and the C-077 length matching applied. Parameterised rather
# than copied so the two families cannot drift apart in the build recipe.
POOLS_TAG="${POOLS_TAG:-ts}"      # demo_pools_116dom_<POOLS_TAG>_<concept>.json
BANK_TAG="${BANK_TAG:-ts116n}"    # boombness_prompt_bank_<BANK_TAG>_<cw>_<cc>.jsonl
REPAIRS='button=switch,basket=hamper,knife=peeler,gun=beacon'

MODE="${1:-build}"   # build | check
fail=0
for cw in button basket; do
  for cc in bomb knife gun; do
    pools="data/boombness_prompts/demo_pools_116dom_${POOLS_TAG}_${cc}.json"
    out="data/boombness_prompts/boombness_prompt_bank_${BANK_TAG}_${cw}_${cc}.jsonl"
    if [[ ! -s "$pools" ]]; then echo "MISSING pools $pools" >&2; fail=1; continue; fi
    if [[ "$MODE" == "build" ]]; then
      PYTHONPATH=src python3 -m boombness.prompt_families \
        --pools "$pools" --preset "$PRESET" --codeword "$cw" --concept "$cc" \
        --seed "$SEED" --strict --incidental-replace "$REPAIRS" --out "$out" >/dev/null
    fi
    if [[ ! -s "$out" ]]; then echo "MISSING bank $out" >&2; fail=1; continue; fi
    meta="${out%.jsonl}_meta.json"
    want=$(python3 -c "import json;print(json.load(open('$meta'))['stats']['bank_rows_sha16'])")
    got=$(PYTHONPATH=src python3 -c "
import json
from boombness.common import rows_sha16
print(rows_sha16([(r['prompt_id'], r['prompt_sha16']) for r in map(json.loads, open('$out'))]))")
    nviol=$(python3 -c "import json;print(json.load(open('$meta'))['stats']['n_alignment_violations'])")
    if [[ "$want" == "$got" && "$nviol" == "0" ]]; then
      printf 'OK   %-14s rows_sha16=%s violations=%s\n' "${cw}_${cc}" "$got" "$nviol"
    else
      printf 'DRIFT %-13s meta=%s disk=%s violations=%s\n' "${cw}_${cc}" "$want" "$got" "$nviol" >&2
      fail=1
    fi
  done
done
[[ $fail -eq 0 ]] || { echo "[build-${BANK_TAG}] FAILED" >&2; exit 1; }
echo "[build-${BANK_TAG}] 6/6 banks present and matching their recorded bank_rows_sha16"
echo
echo "NEXT, and required before any extraction:"
echo "  python3 scripts/dcs_ts_verify_ts116n.py --mutate     # gates G1-G3 + falsifiability"
echo "  (then re-run the G4 concept-backing and G5 leakage audits against ts116n)"
