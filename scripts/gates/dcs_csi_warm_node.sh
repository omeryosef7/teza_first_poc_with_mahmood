#!/bin/sh
# Which node should a RELAUNCH pin to, if any? S-266.
#
# THE TRADEOFF IS MEASURED ON BOTH SIDES, so this is decidable rather than a judgement call.
#   COST OF A COLD LOAD (a node that does not hold the snapshot in page cache):
#     n-303 1311.6 s | n-301 1851.5 s | n-302 >2600 s | n-307 6008.8 s        (S-258, S-261, S-264)
#   COST OF A WARM LOAD (the same node, minutes later):
#     n-307 47.5 s -- 126x cheaper                                            (S-261)
#   COST OF PINNING:
#     S-148 measured that a hard --nodelist waits for ONE NAMED node and is strictly worse than
#     waiting for ANY node when every GPU is allocated -- four jobs PENDED INDEFINITELY.
#     S-2142's entry records a --nodelist=n-303 pin costing 25 min of PENDING (Resources) before the
#     job was resubmitted unpinned.
#
# SO THE RULE IS CONDITIONAL, AND THE CONDITION IS CHECKABLE BEFORE SUBMITTING:
#   pin ONLY if the candidate node has a FREE GPU RIGHT NOW. Otherwise submit unpinned and pay the
#   cold load, which is bounded (22-100 min) where an indefinite PEND is not.
#
# ⚠ S-274: THIS CHECKED GPUs ONLY, AND MEMORY IS THE BINDING CONSTRAINT. It returned "PIN n-307" for a
# node with 6 free GPUs and 12 GB of free memory, against a job requesting --mem=64G. SLURM scheduled the
# pinned job to start 10 HOURS LATER (StartTime=2026-09-23T12:18:18) and it had to be cancelled.
# S-147's entire lesson was that memory is the variable, and the helper written to apply that lesson
# ignored it. Both GPUs AND memory are now required.
#
# usage:  dcs_csi_warm_node.sh <node> [node...]   [--mem-gb N]   (default 64, the launcher's --mem)
#   prints  "PIN <node>"  -> that node has a free GPU AND enough free memory; pass --nodelist=<node>
#           "DO NOT PIN"  -> no candidate qualifies; submit unpinned
set -eu
MEM_GB=64
case "${1:-}" in --mem-gb) MEM_GB="$2"; shift 2 ;; esac
[ $# -ge 1 ] || { echo "usage: $0 [--mem-gb N] <node> [node...]" >&2; exit 2; }
for N in "$@"; do
  INFO=$(scontrol show node "$N" 2>/dev/null) || { echo "  $N: no such node"; continue; }
  CFG=$(printf '%s' "$INFO" | tr ' ' '\n' | grep '^CfgTRES=' | sed 's/.*gres\/gpu=\([0-9]*\).*/\1/')
  ALC=$(printf '%s' "$INFO" | tr ' ' '\n' | grep '^AllocTRES=' | sed 's/.*gres\/gpu=\([0-9]*\).*/\1/')
  case "$ALC" in ''|*[!0-9]*) ALC=0 ;; esac
  case "$CFG" in ''|*[!0-9]*) CFG=0 ;; esac
  FREE=$((CFG - ALC))
  RM=$(printf '%s' "$INFO" | tr ' ' '\n' | grep '^RealMemory=' | cut -d= -f2)
  AM=$(printf '%s' "$INFO" | tr ' ' '\n' | grep '^AllocMem=' | cut -d= -f2)
  case "$RM" in ''|*[!0-9]*) RM=0 ;; esac
  case "$AM" in ''|*[!0-9]*) AM=0 ;; esac
  FREE_MB=$((RM - AM)); FREE_MEM_GB=$((FREE_MB / 1024))
  echo "  $N: gpus $ALC/$CFG allocated, $FREE free | mem ${FREE_MEM_GB}G schedulable, need ${MEM_GB}G"
  if [ "$FREE" -gt 0 ] && [ "$FREE_MEM_GB" -ge "$MEM_GB" ]; then
    echo "PIN $N"
    exit 0
  fi
done
echo "DO NOT PIN -- no candidate has BOTH a free GPU and ${MEM_GB}G of schedulable memory; an unpinned submit is bounded, a pin is not (S-148, S-274)"
exit 1
