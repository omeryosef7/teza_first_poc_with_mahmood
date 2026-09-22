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
# usage:  dcs_csi_warm_node.sh <node> [node...]
#   prints  "PIN <node>"        -> that node is warm-ish AND has a free GPU; pass --nodelist=<node>
#           "DO NOT PIN"        -> no candidate has a free GPU; submit unpinned
set -eu
[ $# -ge 1 ] || { echo "usage: $0 <node> [node...]" >&2; exit 2; }
for N in "$@"; do
  INFO=$(scontrol show node "$N" 2>/dev/null) || { echo "  $N: no such node"; continue; }
  CFG=$(printf '%s' "$INFO" | tr ' ' '\n' | grep '^CfgTRES=' | sed 's/.*gres\/gpu=\([0-9]*\).*/\1/')
  ALC=$(printf '%s' "$INFO" | tr ' ' '\n' | grep '^AllocTRES=' | sed 's/.*gres\/gpu=\([0-9]*\).*/\1/')
  case "$ALC" in ''|*[!0-9]*) ALC=0 ;; esac
  case "$CFG" in ''|*[!0-9]*) CFG=0 ;; esac
  FREE=$((CFG - ALC))
  echo "  $N: gpus $ALC/$CFG allocated, $FREE free"
  if [ "$FREE" -gt 0 ]; then
    echo "PIN $N"
    exit 0
  fi
done
echo "DO NOT PIN -- no candidate node has a free GPU; an unpinned submit is bounded, a pin is not (S-148)"
exit 1
