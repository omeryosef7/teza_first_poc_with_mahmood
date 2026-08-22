"""Guard for the angle->tag resolver in insubspace_null_test.angle_glob.

A guard that has never been tested against a case it should FAIL is not a guard, so this checks
three things, not one:

  1. EQUIVALENCE  -- the same physical direction, requested through different denominators
                     (k/4 == 2k/8 == 3k/12 == 6k/24), resolves to the SAME directory on disk.
  2. BACK-COMPAT  -- every angle the old hard-coded n=4/8/12 resolver got right, the new one still
                     gets right. The old logic is reimplemented here as the oracle.
  3. THE FAILURE  -- a synthetic angle with two DIFFERENT directories under two spellings must RAISE,
                     not quietly pick one.

Run: python src/boombness/test_angle_resolver.py
"""
import glob as _glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import insubspace_null_test as M   # noqa: E402

JUDGE = M.JUDGE
fails = []


def dirs(g):
    return tuple(sorted(_glob.glob(g)))


def old_resolver(layer, k, n_angles):
    """Verbatim reimplementation of the pre-fix resolver, as the back-compat oracle."""
    if n_angles == 4:
        return f"{JUDGE}/angJ{layer}k{k}_*"
    if n_angles == 12 and k % 3 == 0:
        return f"{JUDGE}/angJ{layer}k{k // 3}_*"
    if n_angles == 8:
        return (f"{JUDGE}/angJ{layer}k{k // 2}_*" if k % 2 == 0
                else f"{JUDGE}/a8J{layer}k{k}_*")
    return f"{JUDGE}/angJ{layer}k{k}of{n_angles}_*"


LAYERS = (6, 8, 10, 12)

# --- 1. equivalence across denominators -------------------------------------------------------
n_equiv = 0
for L in LAYERS:
    for k4 in range(4):
        got = {n: dirs(M.angle_glob(L, k4 * (n // 4), n)) for n in (4, 8, 12, 24)}
        live = {n: v for n, v in got.items() if v}
        if len(set(live.values())) > 1:
            fails.append(f"[equiv] L{L} angle {k4}/4 resolves differently by denominator: {live}")
        elif live:
            n_equiv += 1

# --- 2. back-compat on the families the old resolver handled ----------------------------------
n_compat = 0
for L in LAYERS:
    for n in (4, 8, 12):
        for k in range(n):
            old, new = dirs(old_resolver(L, k, n)), dirs(M.angle_glob(L, k, n))
            if old and old != new:
                fails.append(f"[compat] L{L} {k}/{n}: old={old} new={new}")
            elif old:
                n_compat += 1

# --- 3. n=24 aliases must now find the runs the generic spelling missed -----------------------
n_rescued = 0
for L in LAYERS:
    for k in range(24):
        generic = dirs(f"{JUDGE}/angJ{L}k{k}of24_*")
        now = dirs(M.angle_glob(L, k, 24))
        if now and not generic:
            n_rescued += 1

# --- 4. THE CASE IT MUST FAIL ON: one angle, two spellings, two different dirs ----------------
raised = False
_real = M.glob.glob


def _fake(pattern):
    if "angJ99k1_" in pattern:
        return ["FAKE/angJ99k1_20260101_000000_1"]
    if "angJ99k3of12_" in pattern:
        return ["FAKE/angJ99k3of12_20260101_000000_2"]   # same angle (3/12 == 1/4), other dir
    return []


M.glob.glob = _fake
try:
    M.angle_glob(99, 3, 12)
except RuntimeError as e:
    raised = "MULTIPLE DISTINCT" in str(e)
finally:
    M.glob.glob = _real
if not raised:
    fails.append("[failcase] duplicate-spelling angle did NOT raise -- the guard cannot fail, "
                 "so it is not a guard")

print(f"[angle-resolver] equivalence groups checked: {n_equiv}")
print(f"[angle-resolver] back-compat angles with data: {n_compat}")
print(f"[angle-resolver] n=24 angles rescued from the generic spelling: {n_rescued}")
print(f"[angle-resolver] duplicate-spelling case raises: {raised}")
if fails:
    print(f"\n[angle-resolver] FAIL ({len(fails)}):")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("\n[angle-resolver] PASS")
