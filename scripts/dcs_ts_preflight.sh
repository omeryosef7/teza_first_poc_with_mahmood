#!/bin/bash
# DCS thesis-scale GPU PREFLIGHT.  Mandate §27 (model cache / scratch) and §26.9-11 (launcher).
# Run this BEFORE every sbatch in this phase. Exit 0 means it is safe to submit.
#
# WHY IT EXISTS — two failures this repository has already paid for.
#
# 1. THE DANGLING SYMLINK (`DCS-B-019`). `/vol/scratch` is purged BY POLICY. The purge removed the
#    target of `.cache/huggingface -> /vol/scratch/omeryosef/hf_cache`, leaving the symlink itself
#    intact. The SLURM wrapper's `mkdir -p .cache/huggingface` then failed with
#        mkdir: cannot create directory ... : File exists
#    because `mkdir -p` reports EEXIST on a DANGLING symlink rather than creating through it, and
#    under `set -euo pipefail` all three PR-038 arms died in 4-47 seconds behind a message that
#    says nothing about a missing model cache. The home-directory copy is an 8.9 MB config-only
#    stub, so there is NO FALLBACK: when scratch is purged the weights are simply gone.
#    This script resolves the link and reports the real cause in one line.
#
# 2. THE SILENT DEFAULT (`DCS-C-047`). Jobs 853040-853045 exported `ARGSFILE=` -- a variable the
#    runner never reads -- fell through to `BOOMB_SCRIPT`'s default, ran the wrong script and
#    exited `COMPLETED 0:0`. `DCS-C-073` added an opt-in `BOOMB_EXPECT` assertion to the wrapper;
#    this script checks that a submission is actually using it.
#
# USAGE
#   bash scripts/dcs_ts_preflight.sh                       # cache + env + capacity
#   bash scripts/dcs_ts_preflight.sh <script.py> <argsfile> # + verify a specific submission
set -uo pipefail
cd "$(dirname "$0")/.."
PROJECT_DIR="$PWD"
MODEL_DIR_HINT="models--meta-llama--Llama-3.1-8B-Instruct"
fail=0
note() { printf '  %-6s %s\n' "$1" "$2"; [ "$1" = "FAIL" ] && fail=1; return 0; }

echo "=== DCS-TS PREFLIGHT  $(date -Is)  $(hostname) ==="

echo "[1] cache symlinks"
for sub in huggingface torch triton; do
  p="$PROJECT_DIR/.cache/$sub"
  if [ -L "$p" ]; then
    tgt=$(readlink -f "$p" 2>/dev/null || true)
    if [ -z "$tgt" ] || [ ! -d "$tgt" ]; then
      # THE case this script exists for. Say the real cause, not "File exists".
      note FAIL ".cache/$sub is a DANGLING symlink -> $(readlink "$p"). Target is gone (scratch purge?)."
      note ""   "         mkdir -p will report 'File exists' and every job will die in seconds."
    else
      note OK ".cache/$sub -> $tgt"
    fi
  elif [ -d "$p" ]; then
    note OK ".cache/$sub is a real directory"
  else
    note WARN ".cache/$sub does not exist yet (the wrapper will create it)"
  fi
done

echo "[2] model weights and tokenizer"
HUB="$PROJECT_DIR/.cache/huggingface/hub"
snap=$(ls -d "$HUB/$MODEL_DIR_HINT"/snapshots/*/ 2>/dev/null | head -1)
if [ -z "$snap" ]; then
  note FAIL "no snapshot under $HUB/$MODEL_DIR_HINT/snapshots/ -- HF_HUB_OFFLINE=1 means jobs hard-fail at load"
else
  note OK "snapshot $(basename "$snap")"
  # Follow the blob symlinks with -L: a snapshot full of dangling refs into a purged blob store
  # lists perfectly and loads not at all, which is exactly failure (1) one directory deeper.
  nshard=$(ls -L "$snap"/*.safetensors 2>/dev/null | wc -l)
  wbytes=$(du -Lsb "$snap" 2>/dev/null | cut -f1)
  [ "$nshard" -gt 0 ] && note OK "$nshard safetensors shard(s), $(( ${wbytes:-0} / 1024 / 1024 )) MB resolved" \
                      || note FAIL "0 readable safetensors shards (dangling blobs?)"
  for f in tokenizer.json config.json; do
    if [ -r "$snap/$f" ] && [ -s "$snap/$f" ]; then note OK "$f $(stat -Lc %s "$snap/$f") bytes"
    else note FAIL "$f missing or empty"; fi
  done
fi

echo "[3] writable output space"
# A real 10MB write, matching the wrapper's guard: the binding limit here is a user/qtree quota
# that `df` cannot see, and it is SIZE-DEPENDENT -- a 5-byte write has succeeded in the same
# second a 100-byte write returned EDQUOT. `touch` would report healthy and lie.
mkdir -p outputs/dcs_ts 2>/dev/null
g="outputs/dcs_ts/.preflight_$$"
if head -c 10000000 /dev/zero > "$g" 2>/dev/null && [ "$(stat -c %s "$g" 2>/dev/null)" = "10000000" ]; then
  note OK "10MB round-trip to outputs/"
else
  note FAIL "cannot write 10MB to outputs/ -- quota exhausted (EDQUOT); runs would not persist rows"
fi
rm -f "$g"
note INFO "df: $(df -h "$PROJECT_DIR" 2>/dev/null | tail -1 | awk '{print $4" free of "$2}')"

echo "[4] frozen artifacts"
# GATE THE LIVE FAMILY, NOT THE VOID ONE (DCS-C-080). This checked `ts116`, which C-074 voided as
# a concept contrast -- so a green preflight meant nothing about the bank a job would actually
# read, and deleting the void rows would have BLOCKED every submission while instructing the
# operator to regenerate them. ts116m is the live family: per-concept harm pools (C-074), the
# inflection- and case-aware filter (C-076/C-079), and length matching (C-077).
if POOLS_TAG=tsm BANK_TAG=ts116m bash scripts/dcs_ts_build_ts116n.sh check >/dev/null 2>&1; then
  note OK "6/6 ts116m banks match bank_rows_sha16"
else note FAIL "ts116m bank drift or missing -- run: POOLS_TAG=tsm BANK_TAG=ts116m bash scripts/dcs_ts_build_ts116n.sh build"; fi
if POOLS_TAG=tsm BANK_TAG=ts116m python3 scripts/dcs_ts_verify_ts116n.py >/dev/null 2>&1; then
  note OK "ts116m gates G1-G3 pass"
else note FAIL "ts116m FAILS gates G1-G3 -- do not extract from it"; fi
if python3 scripts/dcs_ts_split_manifest.py --check >/dev/null 2>&1; then note OK "domain split manifest verifies"
else note FAIL "domain split manifest FAILED its own check"; fi

echo "[5] cluster"
note INFO "our queue: $(squeue -u "$USER" -h 2>/dev/null | wc -l) job(s)"
note INFO "killable:  $(squeue -h -p killable -t RUNNING 2>/dev/null | wc -l) running / $(squeue -h -p killable -t PENDING 2>/dev/null | wc -l) pending"
nrun=$(squeue -u "$USER" -h -t RUNNING,PENDING 2>/dev/null | wc -l)
[ "$nrun" -le 6 ] && note OK "concurrency $nrun of the 6-job cap for this phase" \
                  || note FAIL "concurrency $nrun EXCEEDS the 6-job cap"

if [ $# -ge 1 ]; then
  echo "[6] submission"
  s="$1"
  if [ -f "src/boombness/$s" ]; then note OK "src/boombness/$s exists"
  else note FAIL "src/boombness/$s NOT FOUND. BOOMB_SCRIPT is a BARE FILENAME; the wrapper prepends src/boombness/. Use ../../scripts/x.py for scripts outside it."; fi
  if [ $# -ge 2 ]; then
    af="$2"
    case "$af" in
      /tmp/*|/var/tmp/*) note FAIL "argsfile $af is on NODE-LOCAL scratch; compute nodes cannot see it and the job dies in ~3s with 'argsfile not found'" ;;
    esac
    if [ ! -f "$af" ]; then note FAIL "argsfile not found: $af"
    else
      note OK "argsfile $af ($(wc -c < "$af") bytes)"
      grep -q "[\"']" "$af" && note FAIL "argsfile contains a quote character -- BOOMB_ARGS is word-split, so quotes become literal argv chars and multi-word values are torn apart" \
                            || note OK "argsfile is quote-free"
    fi
  fi
  echo
  echo "  Submit with BOOMB_EXPECT set, so a mistyped variable cannot silently default:"
  echo "    sbatch --export=ALL,BOOMB_SCRIPT=$s,BOOMB_EXPECT=$s,BOOMB_ARGSFILE=${2:-<argsfile>} \\"
  echo "           src/boombness/slurm/run_boombness.sh"
  echo "  Then READ the first log lines and confirm 'boombness: $s' and 'boomb_script_origin: PROVIDED'."
fi

echo
if [ $fail -eq 0 ]; then echo "=== PREFLIGHT PASS ==="; exit 0
else echo "=== PREFLIGHT FAIL -- do not submit ==="; exit 1; fi
