#!/bin/bash
# HERETIC-CSI P6 gate G2 (KO liveness, PREREG_P6 gates_mechanical.G2; review #7 item 2): for each G3-passing codeword,
# BASE / KO / KO_SELF / KO_FULL on the TRAIN rescue population, with EXACTLY the incumbent rescue_sweep.slurm liveness
# invocation (COMMON / KO / RESC flags, seed 20260913, layer 18, KO demo_all:attn_knockout:6-14:1.0
# target_surface_row_only, rescue at query positions L18), batch size 1, all arms through dcs_csi_arm_runner (ONE model
# load). G2 itself is computed on CPU by research/heretic_csi/p6_g2.py (KO−BASE < 0 and KO_FULL−KO > 0, domain-cluster
# bootstrap 95% CI excluding 0, TRAIN). The Stage-0 readout is NOT reused as BASE (different invocation: seed, query
# kinds, dose mix), so BASE is re-scored here.
#SBATCH --job-name=hcsi_p6g2
#SBATCH --output=outputs/heretic_csi/logs/p6g2_%j.out
#SBATCH --error=outputs/heretic_csi/logs/p6g2_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=23:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=l40s:1
#SBATCH --no-requeue
#SBATCH --exclude=n-801,n-803,n-804
set -uo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
export PYTHONUNBUFFERED=1
PY=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python
CWS="${1:?usage: sbatch p6_g2.slurm <cw1,cw2,...> [--dry-run]}"
DRY="${2:-}"
SCR=/specific/scratches/scratch/omeryosef/models/llama31_0e9e39f2
IFS=, read -ra LIST <<< "$CWS"
for CW in "${LIST[@]}"; do
  ST=$("$PY" -c "import json;print(json.load(open('outputs/heretic_csi/p6/stage0_${CW}.json'))['status'])" 2>/dev/null || echo NONE)
  [ "$ST" == "G3_PASS" ] || { echo "REFUSING: $CW stage0 status=$ST (G2 only for G3-passers)"; exit 2; }
done
MODEL="$SCR"
if [ "$DRY" != "--dry-run" ]; then
  nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader
  export TMPDIR="${SLURM_TMPDIR:-/tmp/${USER}/${SLURM_JOB_ID}}"; mkdir -p "$TMPDIR/llama31"
  trap 'rm -rf "$TMPDIR/llama31" 2>/dev/null || true' EXIT TERM INT
  AVAIL_KB=$(df --output=avail -k "$TMPDIR" 2>/dev/null | tail -1 || echo 0)
  if [ "${AVAIL_KB:-0}" -ge 18000000 ] && cp -L "$SCR"/*.safetensors "$SCR"/*.json "$TMPDIR/llama31/"; then
    MODEL="$TMPDIR/llama31"; echo "STAGE_IN done avail_kb=$AVAIL_KB $(date -Is)"
  else rm -rf "$TMPDIR/llama31"; echo "STAGE_IN SKIPPED/FAILED avail_kb=$AVAIL_KB — loading from mirror"; fi
  SNAPDIR="outputs/heretic_csi/p6/code_${SLURM_JOB_ID}"; mkdir -p "$SNAPDIR"
  cp src/boombness/score_behavior.py scripts/dcs_csi_arm_runner.py research/heretic_csi/slurm/p6_g2.slurm research/heretic_csi/p6_g2.py "$SNAPDIR/"
  (cd "$SNAPDIR" && sha256sum * > SHA256SUMS)
fi
ARGV=$(mktemp)
emit () { echo "python src/boombness/score_behavior.py $*" >> "$ARGV"; }
for CW in "${LIST[@]}"; do
  BANK=data/boombness_prompts/boombness_prompt_bank_ts116m_${CW}_bomb.jsonl
  EXCL=runargs/heretic_csi/p6/exclude_${CW}_bomb_sow_train_occ.txt
  [ -s "$EXCL" ] || EXCL=runargs/heretic_csi/p6/exclude_${CW}_bomb_sow_train.txt
  COMMON="--bank $BANK --model $MODEL --query-kinds semantic_one_word --conditions natural_doublespeak --n-examples 4 --readout-ids whole_answer --readout-max-batch 1 --exclude-prompt-ids $EXCL --min-option-mass 0.05 --seed 20260913 --dtype bfloat16 --attn-impl eager"
  KO="--intervene demo_all:attn_knockout:6-14:1.0 --knockout-scope target_surface_row_only"
  RESC="--rescue-positions query --rescue-layer 18"
  T="hcsi_p6g2_${CW}"
  emit $COMMON                                --arm BASE    --tag ${T}_BASE
  emit $COMMON $KO                            --arm KO      --tag ${T}_KO
  emit $COMMON $KO $RESC --rescue-donor self  --arm KO_SELF --tag ${T}_KO_SELF
  emit $COMMON $KO $RESC --rescue-donor clean --arm KO_FULL --tag ${T}_KO_FULL
done
echo "ARGV_FILE lines=$(wc -l < "$ARGV") codewords=${#LIST[@]}"
if [ "$DRY" == "--dry-run" ]; then head -4 "$ARGV" | cut -c1-400; echo "DRY_OK"; rm -f "$ARGV"; exit 0; fi
"$PY" scripts/dcs_csi_arm_runner.py --argv-file "$ARGV" --expect-n 0 --out "outputs/heretic_csi/p6/g2_arm_runner_${SLURM_JOB_ID}.json"
RC=$?
for CW in "${LIST[@]}"; do
  "$PY" research/heretic_csi/p6_g2.py "$CW" --job "$SLURM_JOB_ID" || echo "G2_EVAL_FAILED cw=$CW"
done
echo "DONE_MARKER p6_g2 job=$SLURM_JOB_ID cws=$CWS arm_runner_rc=$RC $(date -Is)"
rm -f "$ARGV"
