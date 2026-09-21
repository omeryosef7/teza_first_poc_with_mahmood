#!/bin/sh
# Submit a CSI slurm script WITH its provenance captured HERE, on the submitting host.
# `git` does not exist on the compute nodes, so a witness taken inside the job is always empty --
# and an empty porcelain reads exactly like a clean worktree. Refuses a dirty tree outright.
set -eu
[ $# -ge 1 ] || { echo "usage: $0 <slurm script> [sbatch args...]" >&2; exit 2; }
S="$1"; shift
BLOB=$(git rev-parse --short HEAD)
DIRTY=$(git status --porcelain --untracked-files=no | tr '\n' ';')
if [ -n "$DIRTY" ]; then
  echo "REFUSING TO SUBMIT: worktree is dirty -- the artifact could not be reproduced from any commit." >&2
  echo "  $DIRTY" >&2
  exit 1
fi
# A CALLER-SUPPLIED --export SILENTLY REPLACES OURS AND STRIPS THE PROVENANCE.
# Measured: job 915945 exited 3 because `--export=ALL,SCREEN=...` passed through here
# overrode `--export=ALL,CSI_GIT_BLOB=...`. sbatch takes the LAST --export and does not warn.
# Extra variables belong in the environment (they propagate via ALL), so this refuses instead.
for arg in "$@"; do
  case "$arg" in
    --export=*)
      echo "REFUSING: pass extra variables in the ENVIRONMENT, not --export -- a second" >&2
      echo "  --export replaces this script's and strips CSI_GIT_BLOB (see job 915945)." >&2
      echo "  Use:  VAR=value $0 <script>" >&2
      exit 2 ;;
  esac
done
echo "provenance: BLOB $BLOB  PORCELAIN clean"
exec sbatch --export=ALL,CSI_GIT_BLOB="$BLOB",CSI_GIT_PORCELAIN=clean "$@" "$S"
