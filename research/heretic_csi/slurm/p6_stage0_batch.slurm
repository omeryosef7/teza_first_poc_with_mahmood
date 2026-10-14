#!/bin/bash
# HERETIC-CSI P6 Stage 0, BATCHED: ONE L40S allocation, ONE stage-in, then for each codeword sequentially:
#   readout (incumbent argv; score_behavior exits rc=4 when ITS pooled tail gate fails — that is a recorded readout-health
#   statistic, NOT G3, so rc=4 with a healthy run is treated as "readout complete") -> HEALTH (job integrity: run DONE,
#   0 OOM/CUDA rows, no failure other than the declared occurrence_count_mismatch attrition) -> G3 per the FROZEN text
#   (research/heretic_csi/p6_g3.py: median one-word option mass of the BASE readout on the rescue BASE-arm TRAIN
#   population > 0.05; PREREG_P6_AMENDMENT_4 implementation note) -> ONLY if G3_PASS the SLIM layer-18 extraction ->
#   scratch + symlink -> per-codeword manifest + DONE marker. Failing codewords are recorded and the batch continues.
#   REUSE: if outputs/heretic_csi/p6/stage0_<cw>.json names a readout dir that p6_select_run --verify accepts for the
#   manifest's job (RUNMETA job + DONE), that readout is reused (no re-run). Dirs are never chosen by recency.
#SBATCH --job-name=hcsi_p6s0b
#SBATCH --output=outputs/heretic_csi/logs/p6s0b_%j.out
#SBATCH --error=outputs/heretic_csi/logs/p6s0b_%j.err
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
CWS="${1:?usage: sbatch p6_stage0_batch.slurm <cw1,cw2,...> [--dry-run]}"
DRY="${2:-}"
SCR=/specific/scratches/scratch/omeryosef/models/llama31_0e9e39f2
XDST=/specific/scratches/scratch/omeryosef/hcsi_p6/extract
mkdir -p outputs/heretic_csi/logs outputs/heretic_csi/p6 "$XDST"
[ -f "$SCR/VERIFIED" ] || { echo "MISSING verified model mirror $SCR"; exit 2; }
IFS=, read -ra LIST <<< "$CWS"
# pre-flight: every bank present and matching its meta, before any GPU work
for CW in "${LIST[@]}"; do
  BANK=data/boombness_prompts/boombness_prompt_bank_ts116m_${CW}_bomb.jsonl; META=${BANK%.jsonl}_meta.json
  [ -s "$BANK" ] && [ -s "$META" ] || { echo "MISSING bank/meta for $CW"; exit 2; }
  W=$($PY -c "import json;print(json.load(open('$META'))['stats']['bank_rows_sha16'])")
  G=$(PYTHONPATH=src $PY -c "
import json
from boombness.common import rows_sha16
print(rows_sha16([(json.loads(l)['prompt_id'],json.loads(l)['prompt_sha16']) for l in open('$BANK')]))")
  [ "$W" == "$G" ] || { echo "BANK DRIFT $CW meta=$W disk=$G"; exit 3; }
  echo "PREFLIGHT_OK $CW bank_rows_sha16=$G"
done
if [ "$DRY" == "--dry-run" ]; then echo "DRY_OK ${#LIST[@]} codewords: $CWS"; exit 0; fi
echo "HOST=$(hostname) JOB=$SLURM_JOB_ID CWS=$CWS $(date -Is)"
nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader
export TMPDIR="${SLURM_TMPDIR:-/tmp/${USER}/${SLURM_JOB_ID}}"; mkdir -p "$TMPDIR/llama31"
trap 'rm -rf "$TMPDIR/llama31" 2>/dev/null || true' EXIT TERM INT
SNAPDIR="outputs/heretic_csi/p6/code_${SLURM_JOB_ID}"; mkdir -p "$SNAPDIR"
cp src/boombness/score_behavior.py scripts/dcs_extract_under_ko.py research/heretic_csi/slurm/p6_stage0_batch.slurm research/heretic_csi/p6_select_run.py research/heretic_csi/p6_g3.py "$SNAPDIR/"
(cd "$SNAPDIR" && sha256sum * > SHA256SUMS)
AVAIL_KB=$(df --output=avail -k "$TMPDIR" 2>/dev/null | tail -1 || echo 0); MODEL="$SCR"
if [ "${AVAIL_KB:-0}" -ge 18000000 ] && cp -L "$SCR"/*.safetensors "$SCR"/*.json "$TMPDIR/llama31/"; then
  MODEL="$TMPDIR/llama31"; echo "STAGE_IN done avail_kb=$AVAIL_KB $(date -Is)"
else rm -rf "$TMPDIR/llama31"; echo "STAGE_IN SKIPPED/FAILED avail_kb=$AVAIL_KB — loading from mirror"; fi
for CW in "${LIST[@]}"; do
  BANK=data/boombness_prompts/boombness_prompt_bank_ts116m_${CW}_bomb.jsonl
  MAN=outputs/heretic_csi/p6/stage0_${CW}.json
  echo "==== CW=$CW start $(date -Is)"
  RD=""; RRC="reused"; XRC="none"
  if [ -s "$MAN" ]; then
    ORD=$("$PY" -c "import json;print(json.load(open('$MAN')).get('readout_dir') or '')")
    OJ=$("$PY" -c "import json;print(json.load(open('$MAN')).get('slurm_job') or '')")
    if [ -n "$ORD" ] && "$PY" research/heretic_csi/p6_select_run.py --job "$OJ" --verify "$ORD"; then
      RD="$ORD"; echo "REUSE_READOUT cw=$CW dir=$RD job=$OJ"
    fi
  fi
  if [ -z "$RD" ]; then
  "$PY" src/boombness/score_behavior.py --bank "$BANK" --query-kinds semantic_one_word,semantic_forced_choice \
    --conditions natural_doublespeak,benign_literal --n-examples 0,4 --max-new 8 --attn-impl eager --arm base \
    --tag ts116m_readout_${CW}_bomb --model "$MODEL"
  RRC=$?
  RD=$("$PY" research/heretic_csi/p6_select_run.py --job "$SLURM_JOB_ID" --glob "outputs/boombness/score_behavior/ts116m_readout_${CW}_bomb_*") \
    || { echo "STAGE0_RESULT cw=$CW status=ERROR_NO_READOUT_DIR rc=$RRC"; echo "DONE_MARKER p6_stage0 cw=$CW status=ERROR"; continue; }
  echo "READOUT_RC cw=$CW rc=$RRC (rc=4 = score_behavior pooled tail gate; recorded, not G3)"
  fi
  GATE=$("$PY" research/heretic_csi/p6_g3.py "$CW" "$RD")
  echo "STAGE0_GATE cw=$CW readout=$RD rc=$RRC $GATE"
  STATUS=$("$PY" -c "import json,sys;print(json.loads(sys.argv[1])['status'])" "$GATE")
  XD=""
  if [ "$STATUS" == "G3_PASS" ]; then
    "$PY" scripts/dcs_extract_under_ko.py --bank "$BANK" --no-knockout --layers 18 --position codeword_last \
      --only-query-kind behavioral --only-n-examples 4 --only-split train,validation --capture-rel-end=-16..-1 \
      --capture-codeword-occ --tag cont1_behavioral_${CW}_bomb --model "$MODEL"
    XRC=$?
    XD=$("$PY" research/heretic_csi/p6_select_run.py --job "$SLURM_JOB_ID" --glob "outputs/boombness/extract_boombness/cont1_behavioral_${CW}_bomb_*") || XD=""
    if [ -n "$XD" ]; then mv "$XD" "$XDST/" && ln -s "$XDST/$(basename "$XD")" "$XD"; else STATUS="ERROR_EXTRACT"; echo "extract rc=$XRC no DONE dir"; fi
  fi
  "$PY" - "$MAN" "$CW" "$RD" "$XD" "$STATUS" "$GATE" <<'PY'
import json, sys, os
man, cw, rd, xd, status, gate = sys.argv[1:]
prev = json.load(open(man)) if os.path.exists(man) else {}
rjob = json.load(open(os.path.join(rd, "RUNMETA.json"))).get("slurm_job_id")
json.dump({"codeword": cw, "status": status, "g3": json.loads(gate), "readout_dir": rd, "readout_slurm_job": str(rjob),
           "extract_dir": xd or None, "extract_realpath": os.path.realpath(xd) if xd else None,
           "extract_slurm_job": os.environ.get("SLURM_JOB_ID") if xd else None,
           "slurm_job": str(rjob), "previous_manifest": prev or None}, open(man, "w"), indent=1)
PY
  echo "DONE_MARKER p6_stage0 cw=$CW status=$STATUS readout=$RD extract=${XD:-none} $(date -Is)"
done
echo "BATCH_DONE job=$SLURM_JOB_ID cws=$CWS $(date -Is)"
