#!/bin/bash
#SBATCH --job-name=ds_behref
#SBATCH --output=doublespeak_causality/logs/ds_behref_%j.out
#SBATCH --error=doublespeak_causality/logs/ds_behref_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=06:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=1
#SBATCH --nodelist=n-801,n-802,n-803,n-804,n-805,t-806
#
# RESOURCE FOOTPRINT -- measured 2026-08-05, do not re-litigate: cpus=4 mem=48G is the fast-allocating
# default (8cpu/64G sat PENDING 3h32m as 716187/716188; the SAME work at 4cpu/48G allocated in 6m32s as
# 717879/717880). Mechanism: node RealMemory=515600MB / 8 GPUs = 64450MB per GPU-share, so --mem=64G
# leaves only 7 of 8 GPUs memory-feasible per node while 48G leaves all 8. --time is NOT the lever.
# Every #SBATCH line below is a DEFAULT: the matching sbatch flag overrides it with no file edit, e.g.
#   sbatch --cpus-per-task=2 --mem=32G --time=00:40:00 --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/run_behav_refusal.sh
# n-801 is back in the nodelist (a full gpu:l40s:8 node = 1/6 of our L40S capacity). Caveat, measured
# over 232 logged runs: every weight-load slower than 15 min happened on n-801 (worst 79 min), while no
# other L40S node ever exceeded 14 min. To avoid a node, DO NOT use --exclude: passing --exclude on the
# sbatch line NULLIFIES this #SBATCH --nodelist and the job then lands anywhere in the partition. That
# happened on 2026-08-06 (jobs 721954/721955 -> n-306, an RTX 3090); only the GPU guard below caught it.
# Pass an explicit REDUCED NODELIST instead, e.g. to skip n-801:
#   sbatch --nodelist=n-802,n-803,n-804,n-805,t-806 slurm/<wrapper>.sh
#
# BEHAV-REFUSAL: is refusal-bypass the behaviorally sufficient locus of Doublespeak? Direct /
# Direct+refusal-ablation / Direct+random-ablation / DS / DS+refusal-ablation, StrongReject-judged.
# Now also runs the plan §5 P8.1 ALPHA CALIBRATION sweep (see DSALPHAS below).
# (n-801 was previously excluded for slow weight loading -- see the nodelist note above.)
#   sbatch --export=ALL,DSBENCH=doublespeak_causality/data/behavioral/beh_clearharm.json,DSMAXNEW=220,DSN=0 run_behav_refusal.sh
set -euo pipefail
PROJECT_DIR="/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
cd "$PROJECT_DIR"
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
if [ -f "$PROJECT_DIR/.env" ]; then set -a; source "$PROJECT_DIR/.env"; set +a; fi
mkdir -p doublespeak_causality/logs doublespeak_causality/outputs "$PROJECT_DIR/.cache"/{huggingface,torch,triton}
export HF_HOME="$PROJECT_DIR/.cache/huggingface"; export HF_HUB_CACHE="$PROJECT_DIR/.cache/huggingface/hub"
export HF_HUB_OFFLINE=1; export TORCH_HOME="$PROJECT_DIR/.cache/torch"; export TRITON_CACHE_DIR="$PROJECT_DIR/.cache/triton"
export PYTORCH_CUDA_ALLOC_CONF="${PYTORCH_CUDA_ALLOC_CONF:-expandable_segments:True}"; export PYTHONUNBUFFERED=1
: "${DSBENCH:=doublespeak_causality/data/behavioral/beh_clearharm.json}"
: "${DSMODEL:=meta-llama/Llama-3.1-8B-Instruct}"
: "${DSMAXNEW:=220}"
: "${DSN:=0}"
: "${DSSPLITS:=train,test}"   # comma-list kept as a DEFAULT here (not via --export, which truncates)
: "${DSREFPT:=doublespeak_causality/outputs/stage_gcg_full/refusal_direction_llama_L18.pt}"
: "${DSALPHA:=1.0}"
: "${DSSEED:=0}"
: "${DSQUANT:=}"              # §29: ""=full bf16 | 8bit | 4bit (bnb). Scalar, safe via --export.
# --- P8.1 alpha calibration grid (plan §5 P8.1: 0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0; a=0 is also the
# no-op positive control, §1.6). This is a comma-list, so it MUST be a DEFAULT here and can NEVER
# come through sbatch --export (which silently truncates at the first comma: "0.25,0.5" -> "0.25").
# Edit DSALPHAS_DEFAULT to change the grid; set it to "" for the historical single-DSALPHA run.
# Cost: 2 + 3*len(grid) generations per item (7 alphas = 23 arms; ~4.9 s/gen measured on job 708038,
# so 86 items ~= 2.7 h, inside the 6 h limit).
DSALPHAS_DEFAULT="0,0.25,0.5,0.75,1.0,1.5,2.0"
# DSALPHASET presets, so a grid can be chosen through --export WITHOUT hitting the comma-truncation
# bug (pass DSALPHASET=low, never DSALPHAS=0,0.05,...). Same idiom as DSLAYERSET in run_refusal_validate.sh.
#   wide : the P8.1 grid above (default)
#   low  : v3-native re-calibration. P8 showed alpha=0.25 qualifies on NEITHER v3 cohort --
#          ASR(direct_refabl) was 0.402 (clearharm) and 0.591 (generated) against the [0.20,0.40]
#          band -- because the dose was calibrated on clearharm v1. The operating point must be
#          BELOW 0.25 on v3, so this grid resolves that region.
case "${DSALPHASET:-wide}" in
  wide) : ;;
  low)  DSALPHAS_DEFAULT="0,0.05,0.1,0.15,0.2,0.25" ;;
  single) DSALPHAS_DEFAULT="" ;;   # §29: no sweep -> single --alpha (5 arms), keeps 3-precision cost low
  *)    echo "ERROR: unknown DSALPHASET='$DSALPHASET' (want: wide|low|single)"; exit 1 ;;
esac
if [ -n "${DSALPHAS+x}" ]; then
  # The hazard is specifically the COMMA: sbatch --export truncates a comma-list at the first
  # comma, so DSALPHAS=0,0.25,0.5 silently arrives as "0". A SINGLE alpha (no comma) is passed
  # through intact and is safe -- and is exactly what P8 needs (--alphas 0.25). Refusing it
  # unconditionally, as this guard originally did, blocked a legitimate use and failed two P8
  # jobs at 03:27/03:31 on 2026-08-06. Refuse only when a comma is actually present.
  case "$DSALPHAS" in
    *,*)
      echo "ERROR: DSALPHAS='$DSALPHAS' contains a comma and came from the environment/--export;"
      echo "       sbatch --export SILENTLY TRUNCATES comma-lists at the first comma."
      echo "       Edit DSALPHAS_DEFAULT in this wrapper instead, or pass a single alpha."
      exit 1 ;;
    *)
      echo "[ok] DSALPHAS='$DSALPHAS' from --export: single value, no comma, safe to pass through."
      DSALPHAS_DEFAULT="$DSALPHAS" ;;
  esac
fi
DSALPHAS="$DSALPHAS_DEFAULT"
# scalar vars must not contain a comma (same truncation bug); DSSPLITS/DSALPHAS are lists by design.
for v in DSBENCH DSMODEL DSMAXNEW DSN DSREFPT DSALPHA DSSEED DSQUANT; do
  case "${!v}" in *,*) echo "ERROR: $v='${!v}' has a comma; --export truncates comma-lists."; exit 1;; esac
done
case "$DSQUANT" in ""|8bit|4bit) : ;; *) echo "ERROR: DSQUANT='$DSQUANT' (want: ''|8bit|4bit)"; exit 1;; esac
echo "=== behav refusal: $DSMODEL bench=$DSBENCH maxnew=$DSMAXNEW n=$DSN splits=$DSSPLITS alpha=$DSALPHA alphas='$DSALPHAS' ==="; date; hostname; echo "git=$(git rev-parse HEAD 2>/dev/null||echo NA)"
GPU_ALL="$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || true)"; GPU_TYPE="${GPU_ALL%%$'\n'*}"
# GPU guard. DEFAULT: strict L40S (generation comparability). DSGPUALLOW=23gb relaxes to the >=23GB
# Ampere+ allowlist -- used by §29 quantization (all precisions fit 24GB; Ampere is MORE deployment-
# representative for a quant-robustness study) and any run that explicitly opts in.
if [ "${DSGPUALLOW:-}" = "23gb" ]; then
  GPU_MEM_RAW="$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1 || true)"
  GPU_MEM="$(printf '%s' "$GPU_MEM_RAW" | grep -oE '[0-9]+' | head -1 || true)"; GPU_MEM="${GPU_MEM:-0}"
  case "$GPU_TYPE" in
    *L40S*|*l40s*|*A5000*|*a5000*|*A6000*|*a6000*|*A100*|*A40*|*H100*|*H200*|*L40*|*3090*|*4090*)
      if [ "${GPU_MEM:-0}" -ge 23000 ]; then echo "GPU ok (23gb allowlist): $GPU_TYPE (${GPU_MEM}MiB)";
      else echo "ERROR: $GPU_TYPE has only ${GPU_MEM}MiB (<23GB)"; exit 1; fi ;;
    *) echo "ERROR: GPU '$GPU_TYPE' (${GPU_MEM}MiB) not in the 23GB allowlist"; exit 1 ;;
  esac
else
  case "$GPU_TYPE" in *L40S*|*l40s*) echo "GPU ok: $GPU_TYPE";; *) echo "ERROR need L40S got '$GPU_TYPE'"; exit 1;; esac
fi
# --save-gen is ON by default in the harness (gens.jsonl, gitignored); DSNOSAVEGEN=1 turns it off.
python -u doublespeak_causality/scripts/phase_behav_refusal.py \
  --bench "$DSBENCH" --model "$DSMODEL" --max-new "$DSMAXNEW" --refusal-pt "$DSREFPT" --alpha "$DSALPHA" ${DSALPHAS:+--alphas "$DSALPHAS"} ${DSQUANT:+--quantize "$DSQUANT"} ${DSNOSAVEGEN:+--no-save-gen} --n "$DSN" --splits "$DSSPLITS" --seed "$DSSEED"
echo "=== done ==="; date
