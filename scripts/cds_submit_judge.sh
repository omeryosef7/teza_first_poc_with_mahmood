#!/bin/bash
# CDS Stage-1 / Stage-2 judging. ONE manifest per BANK, because `judge_p2.sh` takes a single
# `P2_BANK` and `compare_bank_hashes` REFUSES a cross-bank join (retraction R1's guard). Stage 1 has
# three banks, so three jobs; Stage 2 has one bank and all five arms go in ONE manifest / ONE
# invocation, which is what `CDS-PR-001` 2.5 requires to remove cross-session judge drift.
#
# Usage:  bash scripts/cds_submit_judge.sh <prefix> <bank.jsonl> <expect_rows> tag=rundir [tag=rundir ...]
set -euo pipefail
R=/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
cd "$R"
PREFIX="$1"; BANK="$2"; ROWS="$3"; shift 3
[ -f "$BANK" ] || { echo "REFUSING: bank not found: $BANK" >&2; exit 6; }
MAN="$R/outputs/boombness/argsfiles/${PREFIX}_arms.txt"
: > "$MAN"
n=0
for spec in "$@"; do
  tag="${spec%%=*}"; dir="${spec#*=}"
  [ -f "$dir/DONE.json" ] || { echo "REFUSING: $dir has no DONE.json" >&2; exit 7; }
  got=$(wc -l < "$dir/gens.jsonl")
  [ "$got" -eq "$ROWS" ] || { echo "REFUSING: $dir has $got gens, expected $ROWS" >&2; exit 8; }
  echo "${tag}:${dir}" >> "$MAN"
  n=$((n+1))
done
echo "[cds] manifest $MAN has $n rows, bank $(basename "$BANK"), expect $ROWS rows/arm"
sbatch --export=ALL,P2_MANIFEST="$MAN",P2_PREFIX="$PREFIX",P2_EXPECTED="$n",P2_EXPECT_ROWS="$ROWS",P2_BANK="$BANK",P2_PIN_JUDGE_MODEL=openai/gpt-4o-mini \
  src/boombness/slurm/run_p2_judge.sh
