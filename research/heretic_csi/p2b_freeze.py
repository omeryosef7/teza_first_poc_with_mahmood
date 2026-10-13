#!/usr/bin/env python3
"""Pool the per-codeword TRAIN CV tables and freeze ONE (objective, steer_weight) for all codewords:
argmax of the mean held-out `net` across codewords (fitting-side criterion; endpoint never read)."""
import json, sys
tabs = [json.load(open(p))["cv"] for p in sys.argv[1:]]
keys = set.intersection(*[set(t) for t in tabs])
pooled = {k: sum(t[k]["net"] for t in tabs) / len(tabs) for k in keys}
best = max(pooled, key=pooled.get)
print(json.dumps({"pooled_net": pooled, "frozen": best}), file=sys.stderr)
print(best)
