"""Axis hardware provenance gate -- the guard REVIEW R11's MAJOR-1 showed did not exist.

R11 measured that all five basket BEHAVIOURAL axes were fit from activations computed on a Tesla
V100 (sm_70, NO native bf16 -- emulated) under --dtype bfloat16, while all six button axes came from
an RTX 3090 (sm_86, native). The codeword dissociation is therefore confounded with extraction
hardware, and nothing in the repo could have noticed: the axis .pt files carry NO gpu and NO dtype
field at all, `dcs_csi_axis.py` pins five provenance dimensions and not this one, and PR-CSI-005/006
gate 0(a) pin only outputs/boombness/score_behavior, leaving the extract tree outside every gate.

The bf16 guard added in S-139 sits on score_behavior.py, i.e. on the SCORING path. This gate is its
missing twin on the FITTING path: it resolves every axis to the extract run it was fit from and
refuses a non-native-bf16 device.

Exit status: 1 if any axis has bad provenance that is NOT in KNOWN_VOID_PROVENANCE. The five basket
axes are listed there with their measurement, so this gate is green today and turns red the moment a
NEW axis is fit on the wrong hardware -- the KNOWN_SHORT pattern this repo already uses.
"""
import json, os, sys, glob, tempfile

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
os.chdir(REPO)

# Compute capability by device name. bf16 is native from sm_80 (Ampere) onward; anything below
# EMULATES it, which is what S-119/S-121 measured as destroying the norm-match degeneracy test
# (norm-matched on V100: 0 of 670 rows every time, at n=24, 96, 268 and 670).
CC = {
    "NVIDIA GeForce RTX 3090": (8, 6),
    "NVIDIA L40S":             (8, 9),
    "NVIDIA A100":             (8, 0),
    "NVIDIA H100":             (9, 0),
    "Tesla V100-SXM2-32GB":    (7, 0),
    "Quadro RTX 8000":         (7, 5),
    "NVIDIA TITAN Xp":         (6, 1),
}

KNOWN_VOID_PROVENANCE = {
    "dcs_csi_axis_basket_behavioral.pt":
        "REVIEW R11 MAJOR-1, RESOLVED by PR-CSI-009 (S-169). THE PROVENANCE FACT IS UNCHANGED and is "
        "why this entry still exists: this axis was fit from cont1_behavioral_basket_bomb_20260910_"
        "113902_3966018, which ran on a Tesla V100-SXM2-32GB (sm_70) under --dtype bfloat16 -- "
        "EMULATED -- while button's six axes came from an RTX 3090, 5 of 5 against 6 of 6. WHAT IS NO "
        "LONGER UNKNOWN IS THE CONSEQUENCE. PR-CSI-009 re-extracted the same corpus on an RTX 3090 "
        "with EXACTLY ONE argument changed (--layers 18,20), 33 non-exempt args verified identical, "
        "same bank sha16 79511d9e254571e6, same model revision 0e9e39f249a1, same population "
        "(3720 bank rows -> 3714 results, 670 fit rows / 67 domains), and refit the axis at a forced "
        "layer. MEASURED: abs(cos(new, committed)) = 0.998406 at L18 and 0.997866 at L20. Both clear "
        "the 0.99 threshold that was committed at 08:07:11, nine minutes before the job existed. The "
        "residual (0.0016, 0.0021) was ORIGINALLY justified as float noise inside bf16's ~2^-8; "
        "REVIEW R13 showed that reasoning is wrong twice over and S-173 corrects it. 1-cos is "
        "SECOND order in the angle (theta^2/2 reproduces both residuals exactly), so it was being "
        "compared against a FIRST-order relative precision; and the activations themselves differ "
        "by median 2.57%% (L18) / 2.76%% (L20) relative, i.e. ~7x OUTSIDE that bound. The correct "
        "statement is STRONGER than the one it replaces: the fit is ROBUST -- inputs that differ "
        "by ~2.6%% still yield directions agreeing at cos 0.998. "
        "THE EXTRACTION HARDWARE DID NOT MOVE THE FITTED DIRECTION at the layers the committed axes "
        "use. It does NOT become evidence for any other explanation, it says nothing about button, "
        "and the layer ARGMAX was not re-run (the new corpus carries layer_grid [18,20]). "
        "Artifact: reports/DCS_CSI_PR009_HARDWARE_AB.json.",
    "dcs_csi_axis_basket_behavioral_shuf24.pt": "Same corpus, same provenance fact, and same PR-CSI-009 resolution as dcs_csi_axis_basket_behavioral.pt (S-169).",
    "dcs_csi_axis_basket_more.pt":              "Same corpus, same provenance fact, and same PR-CSI-009 resolution as dcs_csi_axis_basket_behavioral.pt (S-169).",
    "dcs_csi_axis_basket_L20.pt":               "Same corpus, same provenance fact, and same PR-CSI-009 resolution as dcs_csi_axis_basket_behavioral.pt (S-169).",
    "dcs_csi_axis_basket_L18_PLUS_button_swap.pt":
        "Same corpus and same finding as dcs_csi_axis_basket_behavioral.pt. Note this is the swap "
        "artifact whose RECIPIENT is basket, so PR-CSI-006's CELL 4 inherits the confound.",
}


def atomic_write_json(path, obj):
    """Temp + fsync + size check + re-parse OF THE TEMP FILE + chmod + os.replace (S-130 shape;
    R11 MAJOR-5 caught this helper being written the other way round in a sibling gate)."""
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_atomic_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        if os.path.getsize(tmp) == 0:
            raise OSError("temp file is 0 bytes after a flush+fsync that reported success")
        with open(tmp, "r", encoding="utf-8") as fh:
            json.load(fh)
        try:
            mode = os.stat(path).st_mode & 0o7777
        except OSError:
            mode = 0o644
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except Exception as e:
        try:
            nb = os.path.getsize(tmp)
        except OSError:
            nb = -1
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise OSError("atomic_write_json FAILED for %s -- %d bytes reached the temp file; the "
                      "destination is UNCHANGED. Cause: %r" % (path, nb, e)) from e
    return os.path.getsize(path)


def dig(o, keys):
    if isinstance(o, dict):
        for k in keys:
            if k in o and o[k] not in (None, ""):
                return o[k]
        for v in o.values():
            r = dig(v, keys)
            if r:
                return r
    return None


def main():
    import torch
    axes = sorted(glob.glob("configs/dcs_csi_axis_*.pt"))
    # NON-VACUITY FIRST (S-134): a gate that can pass on an empty comparison is not a gate.
    print("[axis-prov] SIZE axes examined = %d" % len(axes))
    if not axes:
        sys.exit("VACUOUS: zero axis .pt files found -- refusing to report a pass")

    rows, bad, unresolved = [], [], []
    print("\n%-46s %-52s %-24s %-10s %s" % ("axis", "corpus extract run", "GPU", "dtype", "cc"))
    for p in axes:
        name = os.path.basename(p)
        try:
            d = torch.load(p, map_location="cpu", weights_only=False)
        except Exception as e:
            unresolved.append((name, "load failed: %r" % (e,)))
            continue
        meta = d.get("meta", d) if isinstance(d, dict) else {}
        corpus = str(meta.get("corpus") or "")
        base = os.path.basename(corpus.rstrip("/"))
        rm = os.path.join("outputs/boombness/extract_boombness", base, "RUNMETA.json")
        if not base or not os.path.exists(rm):
            unresolved.append((name, "corpus %r has no RUNMETA.json" % (corpus or "<missing>",)))
            print("%-46s %-52s %-24s %-10s %s" % (name[:46], (base or "<none>")[:52], "?", "?", "?"))
            continue
        j = json.load(open(rm))
        gpu = str(dig(j, ["gpu", "gpu_name", "device_name"]))
        dtype = str(dig(j, ["dtype", "torch_dtype"]))
        cc = CC.get(gpu)
        ccs = ("%d.%d" % cc) if cc else "UNKNOWN"
        native = (cc is not None and cc[0] >= 8)
        offend = (dtype == "bfloat16" and not native)
        rows.append(dict(axis=name, corpus=base, gpu=gpu, dtype=dtype, compute_capability=ccs,
                         native_bf16=native, offending=offend,
                         known=name in KNOWN_VOID_PROVENANCE))
        flag = ""
        if offend:
            flag = "  <== EMULATED bf16" + ("  [KNOWN]" if name in KNOWN_VOID_PROVENANCE else "  *** UNDOCUMENTED ***")
            if name not in KNOWN_VOID_PROVENANCE:
                bad.append(name)
        print("%-46s %-52s %-24s %-10s %s%s" % (name[:46], base[:52], gpu[:24], dtype, ccs, flag))

    if unresolved:
        print("\nUNRESOLVED (cannot check -- treated as a FAILURE, not a pass):")
        for n, why in unresolved:
            print("   %-46s %s" % (n, why))

    n_off = sum(1 for r in rows if r["offending"])
    print("\n[axis-prov] axes resolved            : %d" % len(rows))
    print("[axis-prov] emulated-bf16 provenance : %d (%d documented, %d undocumented)"
          % (n_off, n_off - len(bad), len(bad)))
    if not rows:
        sys.exit("VACUOUS: no axis resolved a corpus -- refusing to report a pass")

    out = dict(schema="dcs_csi_axis_hardware_provenance/1",
               n_axes=len(axes), n_resolved=len(rows), n_emulated_bf16=n_off,
               n_undocumented=len(bad), rows=rows,
               unresolved=[{"axis": n, "why": w} for n, w in unresolved],
               known_void_provenance=sorted(KNOWN_VOID_PROVENANCE))
    n = atomic_write_json("reports/DCS_CSI_AXIS_HARDWARE_PROVENANCE.json", out)
    print("[axis-prov] wrote+verified reports/DCS_CSI_AXIS_HARDWARE_PROVENANCE.json (%d bytes)" % n)

    if bad or unresolved:
        print("\nFAIL:")
        for n_ in bad:
            print("   UNDOCUMENTED emulated-bf16 provenance: %s" % n_)
        for n_, w in unresolved:
            print("   UNRESOLVED: %s -- %s" % (n_, w))
        sys.exit(1)
    print("\nPASS (every offending axis is documented in KNOWN_VOID_PROVENANCE)")


if __name__ == "__main__":
    main()
