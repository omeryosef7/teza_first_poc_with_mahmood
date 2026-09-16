#!/bin/bash
#SBATCH --job-name=dcs_probe
#SBATCH --output=outputs/boombness/logs/dcs_probe_%j.out
#SBATCH --ntasks=1 --cpus-per-task=2 --mem=8G --time=00:10:00
#SBATCH --partition=killable --account=gpu-research --nodes=1
set -u
echo "HOST=$(hostname) $(date -Is)"
for d in /tmp /scratch /local /localscratch "$TMPDIR"; do
  [ -d "$d" ] && echo "DIR $d -> $(df -h "$d" 2>/dev/null | tail -1)"
done
SNAP=/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659
echo "--- sequential read of 300MB from NFS on this node ---"
dd if=$SNAP/model-00002-of-00004.safetensors of=/dev/null bs=1M count=300 2>&1 | tail -1
echo "--- copy 300MB NFS -> /tmp ---"
dd if=$SNAP/model-00002-of-00004.safetensors of=/tmp/dcs_probe_$$.bin bs=1M count=300 2>&1 | tail -1
echo "--- read back from /tmp ---"
dd if=/tmp/dcs_probe_$$.bin of=/dev/null bs=1M 2>&1 | tail -1
rm -f /tmp/dcs_probe_$$.bin
echo "DONE $(date -Is)"
