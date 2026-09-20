"""PR-CSI-006 Part 3 GATE 0 -- run BEFORE any number is read.

Every gate prints the SIZE of its comparison and asserts that size FIRST (sprint entry S-134).
A gate that can pass on an empty comparison is not a gate; a gate whose count is 0 ABORTS.

Gate 0f is the one that catches the worst failure mode: if cos(swap key, recipient cand_rank1)
comes back ~1.0 the WRONG TENSOR was copied and the swap arm is a relabelled NATIVE arm.
"""
import json, os, glob, re, sys, hashlib
import torch

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
SB = os.path.join(REPO, "outputs/boombness/score_behavior")
LOGS = os.path.join(REPO, "outputs/boombness/logs")
os.chdir(REPO)

SWAP_JOBS = ["913190", "913191", "913192"]
CELLS = [
    dict(cell="button/train", tag="csi1_button_train", arm="XSWAP_FROM_BASKET", expect_n=670,
         recip_pt="configs/dcs_csi_axis_button_behavioral_L18.pt",
         swap_pt="configs/dcs_csi_axis_button_L18_PLUS_basket_swap.pt",
         key="swap_cand_from_basket", donor_sha="0c397a778db933ba", n_keys=53, extra=[]),
    dict(cell="basket/train", tag="csi1_basket_train", arm="XSWAP_FROM_BUTTON", expect_n=670,
         recip_pt="configs/dcs_csi_axis_basket_behavioral.pt",
         swap_pt="configs/dcs_csi_axis_basket_L18_PLUS_button_swap.pt",
         key="swap_cand_from_button", donor_sha="7d4e01f5475e6b53", n_keys=41,
         extra=["configs/dcs_csi_axis_basket_behavioral_shuf24.pt"]),
    dict(cell="basket/validation", tag="csi1_basket_validation", arm="XSWAP_FROM_BUTTON", expect_n=230,
         recip_pt="configs/dcs_csi_axis_basket_behavioral.pt",
         swap_pt="configs/dcs_csi_axis_basket_L18_PLUS_button_swap.pt",
         key="swap_cand_from_button", donor_sha="7d4e01f5475e6b53", n_keys=41,
         extra=["configs/dcs_csi_axis_basket_behavioral_shuf24.pt"]),
]
fail = []


def rundir(tag, arm, jobs=None, layer=None):
    """Resolve a run dir. NEVER 'the newest dir': S-127 measured that every tag exists twice, once
    at L18 and once at L20, and the FIRST version of this gate silently picked basket's L20 twin as
    the 'native KO_AXIS' and reported a false gate failure. `layer` filters on args.rescue_layer."""
    hits = []
    for d in glob.glob(os.path.join(SB, "%s_%s_2026*" % (tag, arm))):
        rm = os.path.join(d, "RUNMETA.json")
        if not os.path.exists(rm):
            continue
        m = json.load(open(rm))
        if jobs and str(m.get("slurm_job_id")) not in jobs:
            continue
        if layer is not None and str(m.get("args", {}).get("rescue_layer")) != str(layer):
            continue
        hits.append(d)
    return sorted(hits)[-1] if hits else None


def t16(t):
    return hashlib.sha256(t.detach().cpu().numpy().tobytes()).hexdigest()[:16]


print("=" * 98)
print("GATE (c) -- all three swap arms FINISHED, no row collapse")
dirs, missing = {}, []
for c in CELLS:
    d = rundir(c["tag"], c["arm"], SWAP_JOBS)
    if d is None or not os.path.exists(os.path.join(d, "DONE.json")):
        missing.append((c["cell"], "no run dir from the swap jobs" if d is None else "no DONE.json -- STILL WRITING"))
        continue
    dirs[c["cell"]] = d
print("  3 expected | %d FINISHED (DONE.json present) | %d not" % (len(dirs), len(missing)))
for cell, why in missing:
    print("     NOT FINISHED: %-20s %s" % (cell, why))
if missing:
    print("\nABORTING. VOID conditions 9 and 11 forbid reading one direction without the other and")
    print("forbid any interim read. Re-run when all three have a DONE.json.")
    sys.exit(2)
for c in CELLS:
    j = json.load(open(os.path.join(dirs[c["cell"]], "DONE.json")))
    w, lo = j.get("rows_written", 0), c["expect_n"] - 4
    print("     %-20s rows=%-4s / expect %s (allow-short 4 => >= %d)  %s"
          % (c["cell"], w, c["expect_n"], lo, "OK" if w >= lo else "COLLAPSE"))
    if w < lo:
        fail.append("c:%s" % c["cell"])
    if w == 0:
        fail.append("c:%s ZERO ROWS (V100 degeneracy signature)" % c["cell"])
print("  GATE (c): %s" % ("PASS" if not [f for f in fail if f.startswith("c:")] else "FAIL"))

print("=" * 98)
print("GATE (a) -- architecture pin, from the RUNS")
gset, n = {}, 0
for c in CELLS:
    g = json.load(open(os.path.join(dirs[c["cell"]], "RUNMETA.json"))).get("gpu")
    gset[g] = gset.get(g, 0) + 1
    n += 1
assert n == 3, "inspected %d swap run dirs, expected 3 -- selector broken" % n
print("  swap run dirs checked: %d | distinct gpu strings: %d" % (n, len(gset)))
for g, k in gset.items():
    print("     %-34r %d" % (g, k))
ok = list(gset) == ["NVIDIA GeForce RTX 3090"]
print("  GATE (a): %s" % ("PASS" if ok else "FAIL -> VOID, family is re-run not patched"))
if not ok:
    fail.append("a")

print("=" * 98)
print("GATE (b) -- no [layer-override]; banner LAYER=18")
n = 0
for j in SWAP_JOBS:
    fs = glob.glob(os.path.join(LOGS, "csi_p1_%s.out" % j)) + glob.glob(os.path.join(LOGS, "csi_p1_%s.err" % j))
    assert fs, "no log file for job %s -- a grep over zero files would 'pass' (S-134)" % j
    txt = "".join(open(f, errors="replace").read() for f in fs)
    n += 1
    ov = "[layer-override]" in txt
    ban = re.findall(r"LAYER=(\d+)", txt)
    print("     job %s: layer-override=%-5s banner LAYER=%s" % (j, ov, (ban[:1] or ["NOT FOUND"])[0]))
    if ov or not ban or ban[0] != "18":
        fail.append("b:%s" % j)
assert n == 3, "grepped %d log sets, expected 3" % n
print("  log files grepped: %d" % n)
print("  GATE (b): %s" % ("PASS" if not [f for f in fail if f.startswith("b:")] else "FAIL"))

print("=" * 98)
print("GATE 0e -- basis byte-identity (THREE files for basket, not two)")
for c in CELLS:
    if c["cell"] == "basket/validation":
        continue
    rp = torch.load(c["recip_pt"], map_location="cpu")["bases"]
    sp = torch.load(c["swap_pt"], map_location="cpu")["bases"]
    shared = sorted(set(rp) & set(sp))
    print("     %-16s keys compared: %d (expected %d)" % (c["cell"], len(shared), c["n_keys"]))
    assert len(shared) == c["n_keys"], "expected %d shared keys, found %d" % (c["n_keys"], len(shared))
    mism = [k for k in shared if not torch.equal(rp[k], sp[k])]
    print("        mismatches: %d" % len(mism))
    if mism:
        fail.append("0e:%s" % c["cell"])
    if c["extra"]:
        fs = [c["recip_pt"]] + c["extra"] + [c["swap_pt"]]
        ts = [torch.load(f, map_location="cpu")["bases"]["cand_rank1"] for f in fs]
        same = all(torch.equal(ts[0], t) for t in ts[1:])
        print("        cand_rank1 across %d files: %d pairwise checks -> %s"
              % (len(fs), len(fs) - 1, "identical" if same else "DIFFER"))
        if not same:
            fail.append("0e:cand_rank1 across basket files")
print("  GATE 0e: %s" % ("PASS" if not [f for f in fail if f.startswith("0e")] else "FAIL"))

print("=" * 98)
print("GATE 0f -- SWAP TENSOR IDENTITY (the relabelled-native-arm catcher)")
for c in CELLS:
    if c["cell"] == "basket/validation":
        continue
    sp = torch.load(c["swap_pt"], map_location="cpu")["bases"]
    sw, own = sp[c["key"]], sp["cand_rank1"]
    a = sw.flatten().double()
    b = own.flatten().double()
    cos = float((a @ b) / (a.norm() * b.norm()))
    print("     %-16s key=%-24s sha16=%s (expect %s)"
          % (c["cell"], c["key"], t16(sw), c["donor_sha"]))
    print("        shape=%s dtype=%s norm=%.8f" % (tuple(sw.shape), sw.dtype, float(sw.norm())))
    print("        cos(swap, recipient cand_rank1) = %.4f   (expect 0.5569 +/- 0.0002)" % cos)
    if tuple(sw.shape) != (1, 4096) or sw.dtype != torch.float32:
        fail.append("0f:%s shape/dtype" % c["cell"])
    if abs(float(sw.norm()) - 1.0) > 1e-6:
        fail.append("0f:%s norm" % c["cell"])
    if abs(cos - 0.5569) > 0.0002:
        fail.append("0f:%s cos=%.4f" % (c["cell"], cos))
        if cos > 0.99:
            print("        *** COS ~ 1.0: THE WRONG TENSOR WAS COPIED. The swap arm is a")
            print("        *** RELABELLED NATIVE ARM. ABORT; DO NOT READ.")
print("  GATE 0f: %s" % ("PASS" if not [f for f in fail if f.startswith("0f")] else "FAIL"))

print("=" * 98)
print("GATE 0g -- ARM IDENTITY AUDIT vs the recipient's own KO_AXIS at L18")
# The preregistration asserts EXACTLY 4 differing flags. That assertion is WRONG and contradicts the
# prereg's own central design argument, and the contradiction is now MEASURED rather than argued:
#   * --rescue-norm-match-key : every native KO_AXIS carries normkey='' while VOID condition 6
#     REQUIRES the swap arm to carry cand_rank1. The staging anchor (job 913232) ran the identical
#     arm WITH normkey='cand_rank1' against the native's normkey='' and got max|diff| == 0 on all six
#     readout fields over 230 rows -- so basis == norm-basis really is the identity, exactly as the
#     prereg argued 130 lines before asserting "exactly 4".
#   * --model : /tmp staged copy vs the shared hub path, SAME revision. Same anchor proves it inert.
# Both are therefore EXPECTED differences, discharged by measurement. See DCS-CSI-138.
EXPECT_DIFF = {"--rescue-basis", "--rescue-basis-key", "--arm", "--tag"}
DISCHARGED = {"--rescue-norm-match-key", "--model"}
for c in CELLS:
    nat = rundir(c["tag"], "KO_AXIS", layer=18)
    if nat is None:
        print("     %-16s CANNOT MEASURE: no native KO_AXIS run dir at layer 18" % c["cell"])
        fail.append("0g:%s no native at L18" % c["cell"]); continue
    natm = json.load(open(os.path.join(nat, "RUNMETA.json")))
    sw = json.load(open(os.path.join(dirs[c["cell"]], "RUNMETA.json")))

    def flags(argv):
        out = {}
        for i, a in enumerate(argv):
            if a.startswith("--"):
                out[a] = argv[i + 1] if i + 1 < len(argv) and not argv[i + 1].startswith("--") else True
        return out
    fa, fb = flags(sw["argv"]), flags(natm["argv"])
    diff = sorted({k for k in set(fa) | set(fb) if fa.get(k) != fb.get(k)})
    unexpected = sorted(set(diff) - EXPECT_DIFF - DISCHARGED)
    missing = sorted(EXPECT_DIFF - set(diff))
    print("     %-16s native=%s" % (c["cell"], os.path.basename(nat)[:52]))
    print("        flags compared: %d | differing: %d %s" % (len(set(fa) | set(fb)), len(diff), diff))
    print("        expected-4: %s | discharged-by-measurement: %s | UNEXPECTED: %s"
          % (sorted(EXPECT_DIFF & set(diff)), sorted(DISCHARGED & set(diff)), unexpected or "none"))
    if unexpected or missing:
        fail.append("0g:%s unexpected=%s missing=%s" % (c["cell"], unexpected, missing))
print("  GATE 0g: %s" % ("PASS" if not [f for f in fail if f.startswith("0g")] else "FAIL"))

print("=" * 98)
print("GATE (g) -- S4 DEGENERACY: n_degenerate must be 0 on every admitted row")
for c in CELLS:
    d = dirs[c["cell"]]
    n_rows, n_deg, fired = 0, 0, 0
    with open(os.path.join(d, "results.jsonl")) as fh:
        for line in fh:
            r = json.loads(line)
            n_rows += 1
            lv = r.get("rescue_liveness") or {}
            if lv.get("fired"):
                fired += 1
            n_deg += int(lv.get("n_positions_norm_match_degenerate") or 0)
    lo = c["expect_n"] - 4
    print("     %-16s rows=%-4d fired=%-4d n_degenerate=%d  (need rows>=%d and n_degenerate==0)"
          % (c["cell"], n_rows, fired, n_deg, lo))
    assert n_rows >= lo, "only %d rows -- comparison would be vacuous" % n_rows
    if n_deg != 0:
        fail.append("g:%s n_degenerate=%d" % (c["cell"], n_deg))
        print("        *** NON-ZERO: the foreign direction carries essentially none of the")
        print("        *** recipient's delta. CANNOT ANSWER. NOT A NULL.")
print("  GATE (g): %s" % ("PASS" if not [f for f in fail if f.startswith("g:")] else "FAIL"))

print("=" * 98)
print("PART 3 GATE 0 VERDICT: %s" % ("ALL GATES PASS -- the frozen read may be run ONCE, both directions together"
                                     if not fail else "FAIL -> %s" % fail))
sys.exit(0 if not fail else 1)
