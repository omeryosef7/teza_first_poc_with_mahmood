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
echo "provenance: BLOB $BLOB  PORCELAIN clean"
exec sbatch --export=ALL,CSI_GIT_BLOB="$BLOB",CSI_GIT_PORCELAIN=clean "$@" "$S"
