#!/bin/bash
# HERETIC-CSI Phase A (mandate §5): audit Heretic's own Model+ARA (identity / modify / reset / replay /
# dW rank / deployed-vs-objective gap / Optuna resume). One small allocation, model staged node-local.
#SBATCH --job-name=hcsi_phaseAB
#SBATCH --output=outputs/heretic_csi/logs/phaseAB_%j.out
#SBATCH --error=outputs/heretic_csi/logs/phaseAB_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=l40s:1
#SBATCH --exclude=n-803
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
PY=/specific/scratches/scratch/omeryosef/envs/heretic_csi/bin/python
export PYTHONUNBUFFERED=1
export HF_HUB_OFFLINE=1 HF_DATASETS_OFFLINE=1
export HF_DATASETS_CACHE=/specific/scratches/scratch/omeryosef/cache/hf_datasets
# verified mirror (SHA256SUMS) of matanbentov HF snapshot 0e9e39f249a16976918f6564b8830bc894c89659
SNAP=/specific/scratches/scratch/omeryosef/models/llama31_0e9e39f2
ATT="${SLURM_JOB_ID:-none}_r${SLURM_RESTART_COUNT:-0}_$(date +%s)"
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} RESTART=${SLURM_RESTART_COUNT:-0} ATT=$ATT $(date -Is)"
nvidia-smi --query-gpu=name,compute_cap,driver_version --format=csv,noheader || true

export TMPDIR="${SLURM_TMPDIR:-/tmp/${USER}/${SLURM_JOB_ID:-$$}}"
mkdir -p "$TMPDIR" 2>/dev/null || { export TMPDIR=/specific/scratches/scratch/omeryosef/tmp/job_${SLURM_JOB_ID:-$$}; mkdir -p "$TMPDIR"; echo "node /tmp unusable -> TMPDIR=$TMPDIR"; }
trap 'rm -rf "$TMPDIR/llama31" 2>/dev/null || true' EXIT TERM INT
AVAIL_KB=$(df --output=avail -k "$TMPDIR" 2>/dev/null | tail -1 || echo 0)
if [ "${AVAIL_KB:-0}" -lt 18000000 ]; then
  echo "STAGE_IN SKIPPED: node-local ${AVAIL_KB}KB < 18G -> loading directly from the scratch mirror $SNAP"
else
  mkdir -p "$TMPDIR/llama31"
  echo "STAGE_IN start $(date -Is)"
  if cp -L "$SNAP"/*.safetensors "$SNAP"/*.json "$SNAP"/tokenizer* "$TMPDIR/llama31/" 2>/dev/null; then
    SNAP="$TMPDIR/llama31"; echo "STAGE_IN done $(date -Is) model=$SNAP"
  else echo "STAGE_IN FAILED -- loading from mirror $SNAP"; fi
fi

WORK=/specific/scratches/scratch/omeryosef/hcsi_work/phaseA_$ATT
set +e
"$PY" research/heretic_csi/phaseA_heretic_audit.py --model "$SNAP" \
  --bank data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl \
  --split-file data/boombness_prompts/dcs_ts116_domain_split.json \
  --out reports/heretic_csi/PHASE_A_heretic_audit --workdir "$WORK" \
  --xcheck-run-dir outputs/boombness/score_behavior/hcsi_p2a_basket_BASE_20261003_171346_1694534 \
  --rank 8 --start-layer 12 --end-layer 16 --n-prompts 16 --optuna-trials 2
RCA=$?
set -e
echo "---- PHASEA EXIT rc=$RCA $(date -Is)"
AJ=$(ls -t reports/heretic_csi/PHASE_A_heretic_audit_job${SLURM_JOB_ID}_r${SLURM_RESTART_COUNT:-0}.json 2>/dev/null | head -1 || true)
GATE=$("$PY" - "$AJ" <<'PYEOF'
import json, sys
try:
    v = json.load(open(sys.argv[1]))["verdicts"]
except Exception as e:
    print("FAIL_NOJSON"); sys.exit()
ok = (v["load_eager_bf16"] and v["base_deterministic"] and v["identity_within_bf16"] and v["reset_exact_to_identity"]
      and v["modify_nonzero"] and v.get("readout_xcheck_mean_dy_le_0.015") is True)
print("PASS" if ok else "FAIL " + json.dumps(v))
PYEOF
)
echo "PHASEA_GATE $GATE"
if [ "$RCA" = "0" ] && [ "${GATE%% *}" = "PASS" ]; then
  echo "DONE_MARKER phaseA att=$ATT"
  CW="${1:-basket}"
  case "$CW" in
    basket) XC=outputs/boombness/score_behavior/hcsi_p2a_basket_BASE_20261003_011736_2629822,outputs/boombness/score_behavior/hcsi_p2a_basket_BASE_20261003_095601_2131856 ;;
    button) XC=outputs/boombness/score_behavior/hcsi_p2a_button_BASE_20261003_012037_2630629,outputs/boombness/score_behavior/hcsi_p2a_button_BASE_20261003_095601_2131858 ;;
  esac
  "$PY" research/heretic_csi/phaseB_native_ara.py --codeword "$CW" --model "$SNAP" \
    --workdir /specific/scratches/scratch/omeryosef/hcsi_work/phaseB_$CW \
    --blob-dir /specific/scratches/scratch/omeryosef/hcsi_blobs/phaseB_$CW \
    --out-dir reports/heretic_csi/phaseB --rank 50 --n-trials 16 --n-startup 8 --n-rand 39 --n-shuffle 3 \
    --extra-ranks 1,8 --xcheck-run-dirs "$XC"
  echo "---- PHASEB EXIT $(date -Is)"
  echo "DONE_MARKER phaseB cw=$CW att=$ATT"
else
  echo "PHASE B SKIPPED: Phase A gate failed (rc=$RCA gate=$GATE)"
fi
