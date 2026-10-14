#!/bin/bash
# HERETIC-CSI P6 Stage 0 (GPU), ONE codeword per allocation: (1) base y_install readout, (2) SLIM behavioral
# extraction (layer 18 ONLY; the incumbents' 19-layer grid is 12 GB/codeword and would breach the 200 GB home cap).
# Commands are the incumbents' recovered argv (RUNMETA of ts116m_readout_basket_bomb_20260907_152329_3191150 and
# cont1_behavioral_basket_bomb_20260910_113902_3966018) with ONLY: bank/tag -> codeword, --model -> staged local
# copy, extraction --layers 18. HARDWARE NOTE: incumbents' extraction ran on V100 (emulated bf16); P6 runs on native
# bf16 — a declared provenance difference (S-054).
# GPU = L40S (48 GB), MATCHING the incumbent readout (ts116m_readout_basket_bomb_20260907_152329_3191150 ran on
# L40S, job 865335). Pilot 1038879 on a5000 (24 GB) OOM'd on 381+ long semantic_forced_choice rows under eager
# attention and failed the option-mass tail gate on the surviving (dose-0-dominated) rows — SUPERSEDED pilot,
# run dir ts116m_readout_candle_bomb_20261014_160945_2569772 kept, not used.
# The extraction run dir is MOVED to /specific/scratches/.../hcsi_p6/extract/ and symlinked back (home-quota).
#SBATCH --job-name=hcsi_p6s0
#SBATCH --output=outputs/heretic_csi/logs/p6s0_%j.out
#SBATCH --error=outputs/heretic_csi/logs/p6s0_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=l40s:1
#SBATCH --no-requeue
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
export PYTHONUNBUFFERED=1
PY=/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python
CW="${1:?usage: sbatch p6_stage0.slurm <codeword> [--dry-run]}"
DRY="${2:-}"
BANK=data/boombness_prompts/boombness_prompt_bank_ts116m_${CW}_bomb.jsonl
META=data/boombness_prompts/boombness_prompt_bank_ts116m_${CW}_bomb_meta.json
SCR=/specific/scratches/scratch/omeryosef/models/llama31_0e9e39f2
XDST=/specific/scratches/scratch/omeryosef/hcsi_p6/extract
MAN=outputs/heretic_csi/p6/stage0_${CW}.json
mkdir -p outputs/heretic_csi/logs outputs/heretic_csi/p6 "$XDST"
[ -s "$BANK" ] || { echo "MISSING bank $BANK"; exit 2; }
[ -s "$META" ] || { echo "MISSING meta $META"; exit 2; }
[ -f "$SCR/VERIFIED" ] || { echo "MISSING verified model mirror $SCR"; exit 2; }
# bank integrity vs its meta BEFORE any GPU work
WANT=$($PY -c "import json;print(json.load(open('$META'))['stats']['bank_rows_sha16'])")
GOT=$(PYTHONPATH=src $PY -c "
import json
from boombness.common import rows_sha16
print(rows_sha16([(json.loads(l)['prompt_id'],json.loads(l)['prompt_sha16']) for l in open('$BANK')]))")
[ "$WANT" == "$GOT" ] || { echo "BANK DRIFT meta=$WANT disk=$GOT"; exit 3; }
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} CW=$CW bank_rows_sha16=$GOT $(date -Is)"
READ_ARGS=(src/boombness/score_behavior.py --bank "$BANK" --query-kinds semantic_one_word,semantic_forced_choice
  --conditions natural_doublespeak,benign_literal --n-examples 0,4 --max-new 8 --attn-impl eager --arm base
  --tag ts116m_readout_${CW}_bomb)
EXT_ARGS=(scripts/dcs_extract_under_ko.py --bank "$BANK" --no-knockout --layers 18 --position codeword_last
  --only-query-kind behavioral --only-n-examples 4 --only-split train,validation --capture-rel-end=-16..-1
  --capture-codeword-occ --tag cont1_behavioral_${CW}_bomb)
if [ "$DRY" == "--dry-run" ]; then
  echo "DRY readout: $PY ${READ_ARGS[*]} --model <staged>"; echo "DRY extract: $PY ${EXT_ARGS[*]} --model <staged>"
  echo "DRY_OK $CW"; exit 0
fi
nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader
export TMPDIR="${SLURM_TMPDIR:-/tmp/${USER}/${SLURM_JOB_ID}}"; mkdir -p "$TMPDIR/llama31"
trap 'rm -rf "$TMPDIR/llama31" 2>/dev/null || true' EXIT TERM INT
SNAPDIR="outputs/heretic_csi/p6/code_${SLURM_JOB_ID}"; mkdir -p "$SNAPDIR"
cp src/boombness/score_behavior.py scripts/dcs_extract_under_ko.py research/heretic_csi/slurm/p6_stage0.slurm "$SNAPDIR/"
(cd "$SNAPDIR" && sha256sum * > SHA256SUMS)
echo "STAGE_IN start $(date -Is)"; cp -L "$SCR"/*.safetensors "$SCR"/*.json "$TMPDIR/llama31/"; echo "STAGE_IN done $(date -Is)"
MODEL="$TMPDIR/llama31"
"$PY" "${READ_ARGS[@]}" --model "$MODEL"; echo "READOUT_DONE rc=$? $(date -Is)"
RD=$(ls -dt outputs/boombness/score_behavior/ts116m_readout_${CW}_bomb_* | head -1)
# READOUT HEALTH GATE (mechanical; mirrors the incumbent's healthy run: gate PASS, no resource failures).
# Stop BEFORE extraction if any row failed with OOM/CUDA errors or score_behavior's own option-mass gate != PASS.
"$PY" - "$RD" <<'PYG'
import json, sys
s = json.load(open(sys.argv[1] + "/summary.json"))
fr = (s.get("failures") or {}).get("failure_reasons", {}) or {}
oom = {k: v for k, v in fr.items() if "OutOfMemory" in k or "CUDA" in k}
print("READOUT_HEALTH gate=%s n_failed=%s oom_rows=%d" % (s.get("option_mass_gate"), (s.get("failures") or {}).get("n_failed"), sum(oom.values())))
sys.exit(0 if (not oom and s.get("option_mass_gate") == "PASS") else 5)
PYG
"$PY" "${EXT_ARGS[@]}" --model "$MODEL"; echo "EXTRACT_DONE rc=$? $(date -Is)"
XD=$(ls -dt outputs/boombness/extract_boombness/cont1_behavioral_${CW}_bomb_* | head -1)
[ -L "$XD" ] && { echo "unexpected symlink $XD"; exit 4; }
mv "$XD" "$XDST/"; ln -s "$XDST/$(basename "$XD")" "$XD"
$PY - "$MAN" "$CW" "$RD" "$XD" "$GOT" <<'PY'
import json, sys, os
man, cw, rd, xd, sha = sys.argv[1:]
json.dump({"codeword": cw, "readout_dir": rd, "extract_dir": xd, "extract_realpath": os.path.realpath(xd),
           "bank_rows_sha16": sha, "slurm_job": os.environ.get("SLURM_JOB_ID")}, open(man, "w"), indent=1)
PY
echo "DONE_MARKER p6_stage0 cw=$CW readout=$RD extract=$XD rc=0 $(date -Is)"
