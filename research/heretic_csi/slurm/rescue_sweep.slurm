#!/bin/bash
# HERETIC-CSI P2a: activation-space rescue rank-sweep for ONE codeword, ONE allocation.
# Pays the (cold) model load ONCE; every arm after the first warm-loads from page cache.
# Reuses src/boombness/score_behavior.py (KO + rescue + y_install readout) UNCHANGED — the exact
# arm invocation is the validated dcs_csi_p1_smoke recipe, extended to the rank-matched sweep arms.
#
# Arms: liveness (BASE, KO, KO_SELF, KO_FULL) then, per rank in $RANKS, the candidate + its
# rank-matched random/shuffled controls (keys resolved by emit_sweep_arms.py from the axis .pt).
#
#SBATCH --job-name=hcsi_sweep
#SBATCH --output=outputs/heretic_csi/logs/sweep_%j.out
#SBATCH --error=outputs/heretic_csi/logs/sweep_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=20:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=geforce_rtx_3090:1
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
export PYTHONUNBUFFERED=1
PY=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python

CW="${1:?usage: sbatch rescue_sweep.slurm <basket|button> [RANKS] [NRAND] [NSHUF] [LIMIT]}"
RANKS="${2:-1,2,4,8,16,32}"
NRAND="${3:-46}"
NSHUF="${4:-10}"
LIMIT="${5:-24}"      # 0 => no --limit (full population)
BATCH="${6:-1}"       # --readout-max-batch; 1 matches the validated smoke, raise (e.g. 8/16) for speed
LIMITARG=""; [ "$LIMIT" != "0" ] && LIMITARG="--limit $LIMIT"
PT=configs/heretic_csi/hcsi_ranksweep_${CW}.pt
SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
# S-058: prefer the VERIFIED byte-identical copy on /specific/scratches (different server than the contended netapp;
# shard sha256 == HF LFS blob names). Falls back to the netapp snapshot if the VERIFIED marker is absent.
SCR=/specific/scratches/scratch/omeryosef/models/llama31_0e9e39f2
[ -f "$SCR/VERIFIED" ] && SNAP="$SCR" && echo "STAGE_SOURCE scratch-verified $SCR" || echo "STAGE_SOURCE netapp $SNAP"
BANK="data/boombness_prompts/boombness_prompt_bank_ts116m_${CW}_bomb.jsonl"
EXCL="${7:-runargs/dcs_cont/exclude_${CW}_bomb_sow_train.txt}"  # arg7: override to a K-per-domain exclusion for faster subset runs
LAYER=18
TAGP="hcsi_p2a_${CW}"

echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} CW=$CW RANKS=$RANKS NRAND=$NRAND NSHUF=$NSHUF LIMIT=$LIMIT $(date -Is)"
nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader || true

# TMPDIR: prefer SLURM_TMPDIR (SLURM auto-cleans it on job end, incl. scancel) so a killed job does NOT
# leave a ~30G stage behind filling the node's /tmp (that littering filled n-803 and ENOSPC'd S-028).
# mktemp + the stage both live here. Trap TERM/INT/EXIT to also clean the fallback /tmp path.
export TMPDIR="${SLURM_TMPDIR:-/tmp/${USER}/${SLURM_JOB_ID:-$$}}"
mkdir -p "$TMPDIR"
trap 'rm -rf "$TMPDIR/llama31" 2>/dev/null || true' EXIT TERM INT
AVAIL_KB=$(df --output=avail -k "$TMPDIR" 2>/dev/null | tail -1 || echo 0)
echo "TMPDIR=$TMPDIR avail_kb=${AVAIL_KB} host=$(hostname)"
if [ "${AVAIL_KB:-0}" -lt 18000000 ]; then
  echo "INSUFFICIENT_TMP: need ~18G node-local, have ${AVAIL_KB}KB on $(hostname):$TMPDIR -- exiting fast (no GPU wasted)"
  exit 1
fi

# PRE-FLIGHT (no GPU): resolve + validate every arm's basis key BEFORE the expensive model load.
ARMS=$(mktemp)
"$PY" research/heretic_csi/emit_sweep_arms.py --pt "$PT" --ranks "$RANKS" --nrand "$NRAND" --nshuf "$NSHUF" > "$ARMS"
echo "PREFLIGHT_OK n_sweep_arms=$(wc -l < "$ARMS")"

# STAGE THE MODEL TO NODE-LOCAL DISK. The cross-user snapshot on netapp loads at ~30-50 s/tensor under
# contention (hours). A single SEQUENTIAL bulk copy (deref symlinks) to node-local /tmp is far faster,
# and the subsequent load reads from local disk. Standing rule for all GPU jobs (log S-014).
LOCAL="$TMPDIR"
mkdir -p "$LOCAL"
echo "STAGE_IN start $(date -Is) -> $LOCAL/llama31"
# Copy ONLY what from_pretrained needs (~16G safetensors + config/tokenizer). SKIP the `original/`
# subdir (the ~16G consolidated .pth duplicate) that made cp -rL 30G and ENOSPC'd marginal nodes (S-029).
mkdir -p "$LOCAL/llama31"
if cp -L "$SNAP"/*.safetensors "$SNAP"/*.json "$SNAP"/tokenizer* "$SNAP"/special_tokens_map.json "$LOCAL/llama31/" 2>/dev/null; then
  SNAP="$LOCAL/llama31"
  echo "STAGE_IN done $(date -Is) size=$(du -sh "$SNAP" | cut -f1) files=$(ls "$SNAP" | wc -l) model=$SNAP"
else
  echo "STAGE_IN FAILED -- falling back to NFS snapshot (slow) $(date -Is)"
fi

COMMON="--bank $BANK --model $SNAP --query-kinds semantic_one_word \
--conditions natural_doublespeak --n-examples 4 --readout-ids whole_answer --readout-max-batch $BATCH \
--exclude-prompt-ids $EXCL $LIMITARG --min-option-mass 0.05 --seed 20260913 \
--dtype bfloat16 --attn-impl eager"
KO="--intervene demo_all:attn_knockout:6-14:1.0 --knockout-scope target_surface_row_only"
RESC="--rescue-positions query --rescue-layer $LAYER"

# Build the argv-file: one full score_behavior command per arm. arm_runner memoizes dc.load_model so
# the model loads ONCE and every arm runs in-process (no per-arm reload). It also hook-leak-checks
# between arms and skips already-complete arms.
ARGV=$(mktemp)
emit () { echo "python src/boombness/score_behavior.py $*" >> "$ARGV"; }
# liveness arms
emit $COMMON                                --arm BASE    --tag ${TAGP}_BASE
emit $COMMON $KO                            --arm KO      --tag ${TAGP}_KO
emit $COMMON $KO $RESC --rescue-donor self  --arm KO_SELF --tag ${TAGP}_KO_SELF
emit $COMMON $KO $RESC --rescue-donor clean --arm KO_FULL --tag ${TAGP}_KO_FULL
# sweep arms (candidate + rank-matched controls)
while IFS=$'\t' read -r ARM KEY NM ROLE RANK; do
  [ -z "$ARM" ] && continue
  EXTRA="--rescue-basis $PT --rescue-basis-key $KEY"
  [ -n "$NM" ] && [ "$NM" != "NONE" ] && EXTRA="$EXTRA --rescue-norm-match-key $NM"
  emit $COMMON $KO $RESC --rescue-donor clean $EXTRA --arm "$ARM" --tag "${TAGP}_${ARM}"
done < "$ARMS"
echo "ARGV_FILE lines=$(wc -l < "$ARGV")  (model loads ONCE via arm_runner)"

# --expect-n 0 for fresh LIMIT=0 runs (skip-if-done disabled); for LIMIT>0 it enables resume/skip.
EXPECTN=0; [ "$LIMIT" != "0" ] && EXPECTN="$LIMIT"
set +e
"$PY" scripts/dcs_csi_arm_runner.py --argv-file "$ARGV" --expect-n "$EXPECTN" \
  --out "outputs/heretic_csi/arm_runner_${CW}_${SLURM_JOB_ID:-0}.json"
RC=$?
set -e
echo "---- SWEEP DONE rc=$RC CW=$CW $(date -Is) HOST=$(hostname)"
echo "DONE_MARKER sweep_arms=$(wc -l < "$ARMS") argv_lines=$(wc -l < "$ARGV") codeword=$CW ranks=$RANKS rc=$RC"
rm -f "$ARMS" "$ARGV"
