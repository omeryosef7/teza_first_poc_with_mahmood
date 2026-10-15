#!/bin/bash
# HERETIC-CSI P2a: activation-space rescue rank-sweep for ONE codeword, ONE allocation.
# Pays the (cold) model load ONCE; every arm after the first warm-loads from page cache.
# Reuses src/boombness/score_behavior.py (KO + rescue + y_install readout) UNCHANGED — the exact
# arm invocation is the validated dcs_csi_p1_smoke recipe, extended to the rank-matched sweep arms.
#
# Arms: liveness (BASE, KO, KO_SELF, KO_FULL) then, per rank in $RANKS, the candidate + its
# rank-matched random/shuffled controls (keys resolved by emit_sweep_arms.py from the axis .pt).
#
# GENERIC powered P2a re-test (PR-HCSI-S199 onward; generalizes p2a_powered_r4ext.slurm of S-084): runs ONLY the NEW
# extended rank-R random controls KO_RAND_r{R}_{START..END} on VALIDATION from an extension basis file, plus
# (OVL=1) four overlap arms re-running the original job's BASE/KO/candidate/first-control under distinct labels.
# Liveness, candidate and the original 56 controls are REUSED from the original job (analyzer combines jobs).
# Everything else (COMMON flags, KO, rescue layer/positions, staging, arm_runner) is byte-identical in intent.
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
#SBATCH --gpus=a5000:1
#SBATCH --no-requeue
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
export PYTHONUNBUFFERED=1
PY=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python
CW="${1:?usage: sbatch p2a_powered_ext.slurm CW RANK CANDKEY EXT_PT START END OVL}"
R="${2:?}"
CANDKEY="${3:?}"
PT="${4:?}"
START="${5:?}"
END="${6:?}"
OVL="${7:-0}"   # 1 => also run the overlap arms (first job only)
RANKS=$R; LIMIT=0; BATCH=1
LIMITARG=""
SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
SCR=/specific/scratches/scratch/omeryosef/models/llama31_0e9e39f2
[ -f "$SCR/VERIFIED" ] && SNAP="$SCR" && echo "STAGE_SOURCE scratch-verified $SCR" || echo "STAGE_SOURCE netapp $SNAP"
BANK="data/boombness_prompts/boombness_prompt_bank_ts116m_${CW}_bomb.jsonl"
EXCL=runargs/dcs_cont/exclude_${CW}_bomb_sow_validation.txt
LAYER=18
TAGP="hcsi_p2a_${CW}"
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} CW=$CW RANK=$R CAND=$CANDKEY EXT_PT=$PT EXT_RANGE=$START..$END OVL=$OVL $(date -Is)"
echo "PT_SHA256 $(sha256sum $PT | cut -c1-64)"
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
ARMS=$(mktemp)
for i in $(seq "$START" "$END"); do printf "KO_RAND_r%d_%d\tctrl_random_r%d_%d\t%s\tcontrol_random\t%d\n" "$R" "$i" "$R" "$i" "$CANDKEY" "$R" >> "$ARMS"; done
"$PY" - "$PT" "$ARMS" <<'PYEOF'
import sys, torch
keys = set(torch.load(sys.argv[1], map_location="cpu", weights_only=False)["bases"])
miss = [l.split("\t")[1] for l in open(sys.argv[2]) if l.split("\t")[1] not in keys]
if miss: sys.exit("MISSING keys: %s" % miss[:5])
PYEOF
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
ARGV=$(mktemp)
emit () { echo "python src/boombness/score_behavior.py $*" >> "$ARGV"; }
# PR-HCSI-S084 AMENDMENT_1: OVERLAP arms re-run identical interventions from job 1022698 under distinct labels
# (so they never collide with that job's run dirs in the analyzer); they must reproduce 1022698 per row.
ORIG=configs/heretic_csi/hcsi_ranksweep_${CW}.pt
if [ "$OVL" = "1" ]; then
  emit $COMMON                                --arm OVL_BASE --tag ${TAGP}_OVL_BASE
  emit $COMMON $KO                            --arm OVL_KO   --tag ${TAGP}_OVL_KO
  emit $COMMON $KO $RESC --rescue-donor clean --rescue-basis $ORIG --rescue-basis-key $CANDKEY --arm OVL_CAND_r${R} --tag ${TAGP}_OVL_CAND_r${R}
  emit $COMMON $KO $RESC --rescue-donor clean --rescue-basis $ORIG --rescue-basis-key ctrl_random_r${R}_0 --rescue-norm-match-key $CANDKEY --arm OVL_RAND_r${R}_0 --tag ${TAGP}_OVL_RAND_r${R}_0
fi
while IFS=$'\t' read -r ARM KEY NM ROLE RANK; do
  [ -z "$ARM" ] && continue
  emit $COMMON $KO $RESC --rescue-donor clean --rescue-basis $PT --rescue-basis-key $KEY --rescue-norm-match-key $NM --arm "$ARM" --tag "${TAGP}_${ARM}"
done < "$ARMS"
echo "ARGV_FILE lines=$(wc -l < "$ARGV")  (model loads ONCE via arm_runner)"
set +e
"$PY" scripts/dcs_csi_arm_runner.py --argv-file "$ARGV" --expect-n 0 \
  --out "outputs/heretic_csi/arm_runner_${CW}_r${R}ext_${SLURM_JOB_ID:-0}.json"
RC=$?
set -e
echo "---- SWEEP DONE rc=$RC CW=$CW $(date -Is) HOST=$(hostname)"
echo "DONE_MARKER sweep_arms=$(wc -l < "$ARMS") argv_lines=$(wc -l < "$ARGV") codeword=$CW rank=${R}ext range=$START..$END ovl=$OVL rc=$RC"
rm -f "$ARMS" "$ARGV"
