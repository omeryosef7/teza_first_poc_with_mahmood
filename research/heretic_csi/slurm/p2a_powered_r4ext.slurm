#!/bin/bash
# HERETIC-CSI P2a: activation-space rescue rank-sweep for ONE codeword, ONE allocation.
# Pays the (cold) model load ONCE; every arm after the first warm-loads from page cache.
# Reuses src/boombness/score_behavior.py (KO + rescue + y_install readout) UNCHANGED — the exact
# arm invocation is the validated dcs_csi_p1_smoke recipe, extended to the rank-matched sweep arms.
#
# Arms: liveness (BASE, KO, KO_SELF, KO_FULL) then, per rank in $RANKS, the candidate + its
# rank-matched random/shuffled controls (keys resolved by emit_sweep_arms.py from the axis .pt).
#
# PR-HCSI-S084 (F6): THIN COPY of rescue_sweep.slurm that runs ONLY the NEW extended rank-4 random controls
# KO_RAND_r4_{START..END} for button on VALIDATION, from configs/heretic_csi/hcsi_ranksweep_button_r4ext.pt.
# Liveness (BASE/KO/KO_SELF/KO_FULL), the candidate and the original 56 controls are REUSED from job 1022698
# (the frozen analyzer combines run dirs across jobs via --require-slurm-job "1022698,<this>,<other>").
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
CW=button
START="${1:?usage: sbatch p2a_powered_r4ext.slurm START END}"
END="${2:?}"
OVL="${3:-0}"   # 1 => also run the AMENDMENT_1 overlap arms (job 1 only)
RANKS=4; LIMIT=0; BATCH=1
LIMITARG=""
PT=configs/heretic_csi/hcsi_ranksweep_button_r4ext.pt
SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
SCR=/specific/scratches/scratch/omeryosef/models/llama31_0e9e39f2
[ -f "$SCR/VERIFIED" ] && SNAP="$SCR" && echo "STAGE_SOURCE scratch-verified $SCR" || echo "STAGE_SOURCE netapp $SNAP"
BANK="data/boombness_prompts/boombness_prompt_bank_ts116m_${CW}_bomb.jsonl"
EXCL=runargs/dcs_cont/exclude_button_bomb_sow_validation.txt
LAYER=18
TAGP="hcsi_p2a_${CW}"
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} CW=$CW RANKS=$RANKS EXT_RANGE=$START..$END $(date -Is)"
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
for i in $(seq "$START" "$END"); do printf "KO_RAND_r4_%d\tctrl_random_r4_%d\tcand_pls4\tcontrol_random\t4\n" "$i" "$i" >> "$ARMS"; done
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
ORIG=configs/heretic_csi/hcsi_ranksweep_button.pt
if [ "$OVL" = "1" ]; then
  emit $COMMON                                --arm OVL_BASE --tag ${TAGP}_OVL_BASE
  emit $COMMON $KO                            --arm OVL_KO   --tag ${TAGP}_OVL_KO
  emit $COMMON $KO $RESC --rescue-donor clean --rescue-basis $ORIG --rescue-basis-key cand_pls4 --arm OVL_CAND_r4 --tag ${TAGP}_OVL_CAND_r4
  emit $COMMON $KO $RESC --rescue-donor clean --rescue-basis $ORIG --rescue-basis-key ctrl_random_r4_0 --rescue-norm-match-key cand_pls4 --arm OVL_RAND_r4_0 --tag ${TAGP}_OVL_RAND_r4_0
fi
while IFS=$'\t' read -r ARM KEY NM ROLE RANK; do
  [ -z "$ARM" ] && continue
  emit $COMMON $KO $RESC --rescue-donor clean --rescue-basis $PT --rescue-basis-key $KEY --rescue-norm-match-key $NM --arm "$ARM" --tag "${TAGP}_${ARM}"
done < "$ARMS"
echo "ARGV_FILE lines=$(wc -l < "$ARGV")  (model loads ONCE via arm_runner)"
set +e
"$PY" scripts/dcs_csi_arm_runner.py --argv-file "$ARGV" --expect-n 0 \
  --out "outputs/heretic_csi/arm_runner_${CW}_r4ext_${SLURM_JOB_ID:-0}.json"
RC=$?
set -e
echo "---- SWEEP DONE rc=$RC CW=$CW $(date -Is) HOST=$(hostname)"
echo "DONE_MARKER sweep_arms=$(wc -l < "$ARMS") argv_lines=$(wc -l < "$ARGV") codeword=$CW ranks=4ext range=$START..$END ovl=$OVL rc=$RC"
rm -f "$ARMS" "$ARGV"
