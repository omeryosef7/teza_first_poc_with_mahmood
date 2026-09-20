"""The verification PR-CSI-003-A demands before any half-4/5 arm is launched:
`bash -n`, plus a dry read of the two new branches confirming 10 arm names each and
ctrl_shuffled4..23 with no gap and no repeat."""
import re

P = "slurm_scripts/dcs_csi_p1_arms.slurm"
s = open(P).read()

BRANCH = r'elif \[ "\$NEC_HALF" = "%s" \]; then(.*?)(?=\n  elif |\n  else)'
all_n, all_keys = [], []

for half in ("4", "5"):
    m = re.search(BRANCH % half, s, re.S)
    assert m, "half %s branch not found" % half
    body = m.group(1)
    loop = re.search(r"for j in ([0-9 ]+); do", body)
    assert loop, "half %s has no for-loop" % half
    nums = [int(x) for x in loop.group(1).split()]
    call = re.search(r'subnec "KO_NEC_SHUF\$\{j\}" "ctrl_shuffled\$\{j\}" (\w+)', body)
    assert call, "half %s does not call subnec with the expected arm/key shape" % half
    print("half %s: %2d arm names %s" % (half, len(nums), nums))
    print("         arm=KO_NEC_SHUF${j}  key=ctrl_shuffled${j}  norm-match=%s" % call.group(1))
    assert len(nums) == 10, "half %s emits %d arms, expected 10" % (half, len(nums))
    assert call.group(1) == "cand_rank1", "half %s norm-matches to %r, not cand_rank1" % (half, call.group(1))
    all_n += nums
    all_keys.append(call.group(1))

print()
print("union: %d values, range %d..%d" % (len(all_n), min(all_n), max(all_n)))
gaps = sorted(set(range(4, 24)) - set(all_n))
reps = sorted({x for x in all_n if all_n.count(x) > 1})
print("  gaps in ctrl_shuffled4..23 : %s" % (gaps or "NONE"))
print("  repeats                    : %s" % (reps or "NONE"))
assert not gaps and not reps and len(all_n) == 20

# the refusal message must name the new set -- "a refusal that names the wrong set is how a half
# gets silently defaulted" (PR-CSI-003-A)
ref = re.search(r"REFUSING: CSI_NEC_HALF=\$NEC_HALF is not ([^.]*)\.", s)
print("  refusal message names      : %s" % ref.group(1))
assert "4" in ref.group(1) and "5" in ref.group(1), "refusal message still names the old set"

# what the patch must NOT touch
for name in ("subnec()", "RNEC=", "NECCOMMON=", 'NEC_HALF" = "1"', 'NEC_HALF" = "2"', 'NEC_HALF" = "3"'):
    assert name.replace("()", "") in s, "the patch removed %s" % name
print("  subnec / RNEC / NECCOMMON / halves 1-3 : all still present")
print("\nLAUNCHER PATCH VERIFIED")
