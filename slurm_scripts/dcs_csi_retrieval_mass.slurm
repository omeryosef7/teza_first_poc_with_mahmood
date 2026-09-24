#!/bin/bash
# S-331: the ATTENTION-MASS measurement that S-316 blocked the source-side family on.
#
# WHY THIS SCRIPT EXISTS. src/boombness/retrieval_strength.py has been run under slurm before
# (job 777320, n-801) but NO COMMITTED SLURM SCRIPT LAUNCHES IT -- the invocation lived somewhere
# uncommitted, which is the same provenance gap S-302 records for a witness taken inside a job.
# A measurement that decides whether a whole family may run must be reproducible from the repo.
#
# WHAT IT MEASURES, and the criterion is FROZEN IN S-325 BEFORE any number exists:
#   per row, band 6-14, at the readout position:
#     m_d = the demonstration block's attention mass
#     m_c = the STRICT, PROTECTED nondemo_matched_d{1,2,3} draws' mass
#   rho_median = m_c / m_d, reported WITH the per-row count of rows where m_d > m_c
#     (C-CONT-019's own statistic was a per-row count and must stay one)
#   rho >= 1.0 and m_d > m_c on < 50% of rows -> the source-side family may run as CONFIRMATORY
#   rho <= 1.0 and m_d > m_c on > 50% of rows -> ONLY as a REFUTATION test
#   straddling                                -> CANNOT ANSWER; no source-side family is licensed
#
# ⛔ FORWARD-ONLY. output_attentions=True, use_cache=False, NO generation. It reads no endpoint and
#    writes no arm; it cannot affect any family's GATE 0.
# ⛔ THE EXCLUSION LIST IS MANDATORY. S-325 added --exclude-prompt-ids and a refusal: without it, a
#    ts116m bank is read POOLED, which includes all 23 TEST domains (S-314: spent AND contaminated).
#SBATCH --job-name=csi_retrmass
#SBATCH --output=outputs/boombness/logs/csi_retrmass_%j.out
#SBATCH --error=outputs/boombness/logs/csi_retrmass_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=killable
#SBATCH --account=gpu-research
#SBATCH --nodes=1
#SBATCH --gpus=geforce_rtx_3090:1
set -euo pipefail
cd /home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood
source /home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh
conda activate poc_stage2
echo "HOST=$(hostname) JOB=${SLURM_JOB_ID:-none} $(date -Is)"
nvidia-smi --query-gpu=name,compute_cap --format=csv,noheader || true
echo "BLOB ${CSI_GIT_BLOB:-unset}  PORCELAIN [${CSI_GIT_PORCELAIN:-unset}]"

CW="${CW:?set CW=basket|button}"
MODEL=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659

python src/boombness/retrieval_strength.py \
  --bank "data/boombness_prompts/boombness_prompt_bank_ts116m_${CW}_bomb.jsonl" \
  --exclude-prompt-ids "runargs/dcs_cont/exclude_${CW}_bomb_sow_validation.txt" \
  --query-kinds semantic_one_word \
  --conditions natural_doublespeak \
  --bank-blocks cds_n4_sow \
  --n-examples 4 \
  --expect-n 230 \
  --band-lo 6 --band-hi 14 \
  --late-lo 20 --late-hi 31 \
  --model "$MODEL" \
  --dtype bfloat16 \
  --seed 20260913 \
  --tag "retrmass_${CW}_validation"
