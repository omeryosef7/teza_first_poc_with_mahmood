#!/usr/bin/env python3
"""P3 gate: exit 0 only if <verdict_json> is a p2b_analyze VALIDATION output for <codeword> whose rank-<R> row's verdict
starts with 'PASS'. Anything else (other codeword, TRAIN split, DOES NOT PASS, INCOMPLETE, VOID, missing row) -> exit 1."""
import json, sys


def gate(path, cw, r):
    d = json.load(open(path))
    if d.get("codeword") != cw or d.get("split") != "validation":
        return False, f"{path} is not a {cw} VALIDATION verdict (codeword={d.get('codeword')}, split={d.get('split')})"
    row = [x for x in d.get("rows", []) if int(x.get("rank", -1)) == r]
    if not row or not str(row[0].get("verdict", "")).startswith("PASS"):
        return False, f"{cw} r{r} did not PASS on validation: {row[0].get('verdict') if row else 'no row'}"
    return True, row[0]["verdict"]


if __name__ == "__main__":
    ok, msg = gate(sys.argv[1], sys.argv[2], int(sys.argv[3]))
    print(("P3_GATE_OK " if ok else "P3_GATE_REFUSED ") + msg)
    sys.exit(0 if ok else 1)
