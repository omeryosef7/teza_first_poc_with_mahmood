#!/usr/bin/env python3
"""Build `reports/CLAIM_AUDIT_TABLE.md` — every paper-facing claim traced to the run that produced it.

Plan: §5 P14 ("paper assembly + claim audit").

WHY THIS SCRIPT EXISTS
----------------------
A hand-maintained claim table rots the moment a run lands or a report is corrected.  This script keeps
the *mechanical* half of the table honest and re-derivable:

  1. **run-dir existence** — does every cited `outputs/<run>` still exist, and does it carry the
     §2.1 contract files (`RUNMETA.json`, `DONE.json`, `summary.json`, `raw.jsonl`)?
  2. **does the summary still recompute** — every cited run dir is handed to
     `scripts/validate_all_outputs.py`, which recomputes each `summary.json` aggregate from
     `raw.jsonl`; the per-dir verdict (`ok` / `WARN` / `FAIL` / `SKIP-legacy`) and the
     recomputed/mismatched counts are folded into the table.
  3. **row counts** — `raw.jsonl` line counts, so an n quoted in a report can be checked against the
     rows that actually exist.
  4. **per-claim numeric checks** — each claim may carry `checks`, small declarative specs that
     re-derive its headline number straight from the committed artifacts (a `summary.json` leaf, a
     rate over `raw.jsonl`, the 2x2 interaction estimator, an argmax over layers, ...).  A claim whose
     check does not reproduce is reported as `CHECK-FAIL` no matter what its recorded status says.

The *editorial* half — the claim sentence, its phase, its source section, and its STATUS
(VERIFIED / WITHDRAWN / SUPERSEDED / UNDERPOWERED / UNVERIFIED / PENDING) — lives in the `CLAIMS`
registry below and is a human judgement.  Statuses are deliberately strict:

  VERIFIED      recomputed from raw during this sprint, and it matches
  WITHDRAWN     actively retracted; must never be cited again
  SUPERSEDED    replaced by a later, better measurement
  UNDERPOWERED  the number is right but the design cannot support the inference
  UNVERIFIED    asserted in a report but never recomputed from raw
  PENDING       the producing run is still in flight

SAFETY: this script reads only numeric / label / id / split fields.  It never opens `gens.jsonl`,
never reads a `response`/`completion`/`instruction`/`harmful_word` field, and never emits any
generation text.

Usage
-----
    python scripts/build_claim_audit.py                 # rebuild reports/CLAIM_AUDIT_TABLE.md
    python scripts/build_claim_audit.py --no-validate   # skip validate_all_outputs (faster)
    python scripts/build_claim_audit.py --print         # summary to stdout, do not write
    python scripts/build_claim_audit.py --json out.json # machine-readable audit result

Exit code is non-zero if any claim's numeric check fails or any cited run dir has vanished.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DC = os.path.dirname(HERE)                      # doublespeak_causality/
OUT_MD = os.path.join(DC, "reports", "CLAIM_AUDIT_TABLE.md")

# The StrongREJECT judge flips ~2 pp of labels on BYTE-IDENTICAL text (P8.1 §"Read this first";
# measured at alpha=0, an exact numerical no-op, with generations sha256-verified identical).
# Any |dASR| below this is uninterpretable regardless of n.
NOISE_FLOOR = 0.02

STATUSES = ("VERIFIED", "WITHDRAWN", "SUPERSEDED", "UNDERPOWERED", "UNVERIFIED", "PENDING")

# ---------------------------------------------------------------------------------------------
# Run dirs, named once so a rename is a one-line fix.
# ---------------------------------------------------------------------------------------------
D = {
    # P2 — all-occurrence MLP write
    "p2_ch_all":      "outputs/phase6_KO_clearharm_mlp_out_all_layer_20260805_142528_714998",
    "p2_cu_all":      "outputs/phase6_KO_curated_mlp_out_all_layer_20260805_142420_714999",
    "p2_v2_all":      "outputs/phase6_KO_clearharm_mlp_out_all_layer_20260805_220938_718027",
    "p2_ch_demo":     "outputs/phase6_mlpKO_clearharm_demo_layer_20260803_102135_703532",
    "p2_cu_demo":     "outputs/phase6_mlpKO_curated_demo_layer_20260803_102227_703531",
    # P10 — decode-safe concept write
    "p10_ds":         "outputs/behav_write_clearharm_L8_9_10_11_ds_20260805_232238_718938",
    # prior-sprint behavioral
    "bw_ch":          "outputs/behav_write_clearharm_L8_9_10_11_20260804_110157_707908",
    "bw_cu":          "outputs/behav_write_curated_L8_9_10_11_20260804_110156_707909",
    "bc_ch":          "outputs/behav_carry_clearharm_20260804_100009_707831",
    "bc_cu":          "outputs/behav_carry_curated_20260804_100428_707832",
    "br_ch":          "outputs/behav_refusal_clearharm_a1.0_20260804_133355_708038",
    "br_cu":          "outputs/behav_refusal_curated_a1.0_20260804_125055_708039",
    "br_twin":        "outputs/behav_refusal_clearharm_a1.0_20260804_125311_708038",
    "inj_ch":         "outputs/behav_refinject_clearharm_L18_20260804_141615_710769",
    "inj_cu":         "outputs/behav_refinject_curated_L18_20260804_142104_710770",
    "cal_ch":         "outputs/refinject_cal_clearharm_20260804_194105_711685",
    "cal_cu":         "outputs/refinject_cal_curated_20260804_213213_711769",
    "refproj_ch":     "outputs/refproj_clearharm_20260804_162641_711392",
    "refproj_cu":     "outputs/refproj_curated_20260804_162641_711393",
    "p7c_ch":         "outputs/phase7c_suffic_clearharm_20260803_221441_706025",
    "wrx_ch":         "outputs/write_refusal_intx_clearharm_20260804_231656_711887",
    "wrx_cu":         "outputs/write_refusal_intx_curated_20260804_232905_711888",
    "p9_ch":          "outputs/phase9_dose_clearharm_L9_20260803_174517_704863",
    "p9_cu":          "outputs/phase9_dose_curated_L9_20260803_173754_704861",
    "p5_ch":          "outputs/phase5_headz_clearharm_20260804_021315_707473",
    "p5_cu":          "outputs/phase5_headz_curated_20260803_124603_704130",
    # P8.1 alpha sweep
    "a_ch":           "outputs/behav_refusal_clearharm_asweep0.0-0.25-0.5-0.75-1.0-1.5-2.0_20260805_171237_716014",
    "a_cu":           "outputs/behav_refusal_curated_asweep0.0-0.25-0.5-0.75-1.0-1.5-2.0_20260805_171236_716015",
    # P1 published baseline (Phase 2.1)
    "p21_ch":         "outputs/behavioral_split_beh_clearharm",
    "p21_cu":         "outputs/behavioral_split_beh_curated",
    # P7 refusal-direction validation
    "p7_smoke":       "outputs/refval_clearharm_20260805_215332_717880",
    "p7_full":        "outputs/refval_clearharm_20260806_033340_720463",
    # P8 core on v3 (in flight)
    # O3 (bughunt HIGH): this pointed at ..._035033_720724, which holds ONLY a RUNMETA -- job 720724
    # stalled on n-801 and produced no data; the cohort was re-run as 721956. The audit was
    # green-lighting an empty directory for the project's flagship n=242 result, because a dir with
    # no raw.jsonl is "SKIP-legacy", not a failure. Repointed to the completed run.
    "p8_v3_ch":       "outputs/behav_refusal_clearharm_asweep0.25_20260806_051610_721956",
    "p8_v3_gen":      "outputs/behav_refusal_generated_asweep0.25_20260806_035601_720725",
}

# ---------------------------------------------------------------------------------------------
# Check primitives.  Each returns (ok: bool|None, detail: str).  None == not applicable.
# ---------------------------------------------------------------------------------------------


def _dig(obj, dotted):
    # `dotted` may be a LIST of segments instead of a dotted string. That is not cosmetic: some of
    # our keys are alpha values whose names literally contain a dot ("0.25"), so splitting on "."
    # silently walks the wrong path (pooled["0"]["25"]) and the check would fail for a bogus reason.
    parts = list(dotted) if isinstance(dotted, (list, tuple)) else dotted.split(".")
    cur = obj
    for part in parts:
        if part == "":
            continue
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


def _load_json(path):
    with open(path, "r") as fh:
        return json.load(fh)


def _rows(path, fields=None):
    """Read raw.jsonl.  If `fields` is given only those keys are retained -- the harness never needs
    generation text, and not retaining it is the cheapest possible safety guarantee."""
    out = []
    with open(path, "r") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue            # truncated tail of a live run
            out.append({k: r[k] for k in fields if k in r} if fields else r)
    return out


def chk_summary(c):
    p = os.path.join(DC, c["dir"], "summary.json")
    if not os.path.exists(p):
        return False, "no summary.json"
    try:
        got = _dig(_load_json(p), c["path"])
    except (KeyError, IndexError, TypeError) as exc:
        return False, f"path {c['path']} missing ({exc})"
    tol = c.get("tol", 5e-4)
    ok = abs(float(got) - float(c["expect"])) <= tol
    return ok, f"{c['path']}={got} vs {c['expect']}"


def chk_rows(c):
    p = os.path.join(DC, c["dir"], c.get("file", "raw.jsonl"))
    if not os.path.exists(p):
        return False, f"no {c.get('file','raw.jsonl')}"
    n = sum(1 for line in open(p) if line.strip())
    return n == c["expect"], f"rows={n} vs {c['expect']}"


def chk_rate(c):
    """Fraction of rows matching `where` whose `field` equals `eq`."""
    p = os.path.join(DC, c["dir"], c.get("file", "raw.jsonl"))
    if not os.path.exists(p):
        return False, "no raw file"
    keep = list({c["field"], *c.get("where", {}).keys()})
    rows = _rows(p, keep)
    sel = [r for r in rows if all(r.get(k) == v for k, v in c.get("where", {}).items())]
    if not sel:
        return False, "no matching rows"
    hit = sum(1 for r in sel if r.get(c["field"]) == c["eq"])
    got = hit / len(sel)
    return abs(got - c["expect"]) <= c.get("tol", 5e-4), f"{hit}/{len(sel)}={got:.4f} vs {c['expect']}"


def chk_empty_frac(c):
    """Fraction of rows whose `field` is empty/whitespace after str().  Reads the field's LENGTH only;
    the value is never printed."""
    p = os.path.join(DC, c["dir"], c.get("file", "raw.jsonl"))
    if not os.path.exists(p):
        return False, "no raw file"
    rows = _rows(p, [c["field"]])
    n = len(rows)
    blank = sum(1 for r in rows if len(str(r.get(c["field"], "")).strip()) == 0)
    return blank == c["expect"], f"blank={blank}/{n} vs {c['expect']}"


def chk_interaction(c):
    """Recompute the within-item 2x2 interaction estimator straight from raw labels.

    D_i = Y(1,1) - Y(1,0) - Y(0,1) + Y(0,0);  Ihat = mean(D_i)
    I_max = 1 - ASR(1,0) - ASR(0,1) + ASR(0,0)   (the arithmetic ceiling; marginals only)
    """
    p = os.path.join(DC, c["dir"], "raw.jsonl")
    if not os.path.exists(p):
        return False, "no raw.jsonl"
    a00, a10, a01, a11 = c["cells"]
    keep = [f"{a}_label" for a in (a00, a10, a01, a11)] + ["split"]
    rows = _rows(p, keep)
    if c.get("split"):
        rows = [r for r in rows if r.get("split") == c["split"]]
    rows = [r for r in rows if all(k in r for k in keep if k != "split")]
    if not rows:
        return False, "no complete rows"
    n = len(rows)
    M = lambda r, a: 1 if r[f"{a}_label"] == "MALICIOUS" else 0   # noqa: E731
    y = {k: sum(M(r, k) for r in rows) / n for k in (a00, a10, a01, a11)}
    Dv = [M(r, a11) - M(r, a10) - M(r, a01) + M(r, a00) for r in rows]
    stat = c["stat"]
    got = {
        "Ihat": sum(Dv) / n,
        "I_max": 1 - y[a10] - y[a01] + y[a00],
        "ASR01": y[a01],
        "ASR10": y[a10],
        "ASR00": y[a00],
        "ASR11": y[a11],
        "D+2": float(Dv.count(2)),
        "D-2": float(Dv.count(-2)),
        "n": float(n),
    }[stat]
    return abs(got - float(c["expect"])) <= c.get("tol", 5e-4), f"{stat}={got:.4f} vs {c['expect']} (n={n})"


def chk_label_flips(c):
    """Count label flips between two arms on the same items -- the judge-noise-floor measurement."""
    p = os.path.join(DC, c["dir"], "raw.jsonl")
    if not os.path.exists(p):
        return False, "no raw.jsonl"
    a, b = c["arms"]
    rows = _rows(p, [f"{a}_label", f"{b}_label", f"{a}_score", f"{b}_score"])
    rows = [r for r in rows if f"{a}_label" in r and f"{b}_label" in r]
    n = len(rows)
    flips = sum(1 for r in rows if r[f"{a}_label"] != r[f"{b}_label"])
    got = {"flips": float(flips), "n": float(n)}[c.get("stat", "flips")]
    return abs(got - float(c["expect"])) <= 1e-9, f"flips={flips}/{n} vs {c['expect']}"


def chk_argmax(c):
    """Assert a given layer is the argmax of a per-layer leaf in summary.json."""
    p = os.path.join(DC, c["dir"], "summary.json")
    if not os.path.exists(p):
        return False, "no summary.json"
    s = _load_json(p)
    bad = []
    for split, blk in s.get("by_split", {}).items():
        w = blk.get("windows", {})
        if not w:
            continue
        best = max(w.items(), key=lambda kv: _dig(kv[1], c["leaf"]))[0]
        if best != c["expect"]:
            bad.append(f"{split}->{best}")
    return (not bad), ("argmax=" + c["expect"] + " in all splits" if not bad else "argmax mismatch " + ",".join(bad))


def chk_leaf_extreme(c):
    """max/min of a per-layer leaf across every split x window (self-swap and sufficiency guards)."""
    p = os.path.join(DC, c["dir"], "summary.json")
    if not os.path.exists(p):
        return False, "no summary.json"
    s = _load_json(p)
    vals = []
    for blk in s.get("by_split", {}).values():
        for w in blk.get("windows", {}).values():
            try:
                vals.append(float(_dig(w, c["leaf"])))
            except (KeyError, IndexError, TypeError):
                pass
    if not vals:
        return False, "leaf absent"
    got = max(abs(v) for v in vals) if c["agg"] == "maxabs" else max(vals)
    return got <= c["at_most"] + c.get("tol", 1e-9), f"{c['agg']}({c['leaf']})={got:.4g} <= {c['at_most']}"


def chk_json_path(c):
    """Assert a path in an arbitrary committed JSON is present / absent / equal."""
    p = os.path.join(DC, c["file"])
    if not os.path.exists(p):
        return False, f"missing {c['file']}"
    try:
        got = _dig(_load_json(p), c["path"])
    except (KeyError, IndexError, TypeError):
        return (c.get("expect_present") is False), f"{c['path']} ABSENT"
    if c.get("expect_present") is False:
        return False, f"{c['path']} unexpectedly present"
    if "expect" in c:
        exp = c["expect"]
        # Booleans must compare by identity, not numerically: float(False) == float(0) == 0.0, so a
        # numeric compare would let provisional=0 (or 0.0, or an absent-but-falsy value) pass a
        # check that is supposed to assert the literal `false`.
        if isinstance(exp, bool) or isinstance(got, bool):
            return got is exp, f"{c['path']}={got!r} vs {exp!r}"
        return abs(float(got) - float(c["expect"])) <= c.get("tol", 5e-4), f"{c['path']}={got} vs {c['expect']}"
    return True, f"{c['path']} present"


def chk_split_stat(c):
    """Structural facts about a dataset split file (counts, straddling)."""
    p = os.path.join(DC, c["file"])
    if not os.path.exists(p):
        return False, f"missing {c['file']}"
    obj = _load_json(p)
    recs = obj["records"] if isinstance(obj, dict) and "records" in obj else obj
    if isinstance(recs, dict):
        recs = recs.get("examples", [])
    stat = c["stat"]
    if stat == "n":
        got = len(recs)
    elif stat == "n_concepts":
        got = len({r.get("target_concept") for r in recs})
    elif stat == "n_clusters":
        got = len({r.get("intent_cluster") for r in recs})
    elif stat == "straddling_concepts":
        by = {}
        for r in recs:
            by.setdefault(r.get("target_concept"), set()).add(r.get("split"))
        got = sum(1 for v in by.values() if len(v) > 1)
    elif stat == "straddling_codewords":
        by = {}
        for r in recs:
            by.setdefault(r.get("codeword"), set()).add(r.get("split"))
        got = sum(1 for v in by.values() if len(v) > 1)
    else:
        return None, f"unknown stat {stat}"
    return got == c["expect"], f"{stat}={got} vs {c['expect']}"


CHECKERS = {
    "summary": chk_summary,
    "rows": chk_rows,
    "rate": chk_rate,
    "empty_frac": chk_empty_frac,
    "interaction": chk_interaction,
    "label_flips": chk_label_flips,
    "argmax": chk_argmax,
    "leaf_extreme": chk_leaf_extreme,
    "json_path": chk_json_path,
    "split_stat": chk_split_stat,
}

# ---------------------------------------------------------------------------------------------
# THE CLAIM REGISTRY.
# One entry per quantitative or definitive claim in the paper-facing reports.
# ---------------------------------------------------------------------------------------------
PY = "python"          # /home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python
P6A = "python scripts/phase6_analyze.py {d}"
BCA = "python scripts/phase_behav_carry_analyze.py {d}"

CLAIMS = [
    # ============================== P2 — all-occurrence concept write ==========================
    dict(id="P2-01", phase="P2", status="VERIFIED",
         claim="Patching ALL codeword occurrences gives L9 write necessity +0.0889 on clearharm dev (n=44), vs +0.0625 demo-only.",
         source="PHASE2_ALL_OCCURRENCES.md §2", dirs=[D["p2_ch_all"], D["p2_ch_demo"]],
         script="scripts/phase6_mlp_causal.py --positions all", recompute=P6A.format(d=D["p2_ch_all"]),
         note="Point estimates match summary.json exactly. The CIs printed in the report are a fresh analyzer bootstrap and differ from the stored CI by <=0.005 (dev [0.037,0.153] reported vs [0.0360,0.1571] stored).",
         checks=[dict(kind="summary", dir=D["p2_ch_all"], path="by_split.dev.windows.L9.necessity_specific_ci.0", expect=0.0889),
                 dict(kind="summary", dir=D["p2_ch_demo"], path="by_split.dev.windows.L9.necessity_specific_ci.0", expect=0.0625)]),
    dict(id="P2-02", phase="P2", status="VERIFIED",
         claim="clearharm heldout (n=41): L9 all-occurrence necessity +0.0348 vs +0.0153 demo-only.",
         source="PHASE2_ALL_OCCURRENCES.md §2", dirs=[D["p2_ch_all"], D["p2_ch_demo"]],
         script="scripts/phase6_mlp_causal.py", recompute=P6A.format(d=D["p2_ch_all"]),
         checks=[dict(kind="summary", dir=D["p2_ch_all"], path="by_split.heldout.windows.L9.necessity_specific_ci.0", expect=0.0348),
                 dict(kind="summary", dir=D["p2_ch_demo"], path="by_split.heldout.windows.L9.necessity_specific_ci.0", expect=0.0153)]),
    dict(id="P2-03", phase="P2", status="VERIFIED",
         claim="curated dev +0.1003 and curated heldout +0.1797 L9 all-occurrence necessity (vs +0.0493 / +0.0970 demo-only).",
         source="PHASE2_ALL_OCCURRENCES.md §2", dirs=[D["p2_cu_all"], D["p2_cu_demo"]],
         script="scripts/phase6_mlp_causal.py", recompute=P6A.format(d=D["p2_cu_all"]),
         checks=[dict(kind="summary", dir=D["p2_cu_all"], path="by_split.dev.windows.L9.necessity_specific_ci.0", expect=0.1003),
                 dict(kind="summary", dir=D["p2_cu_all"], path="by_split.heldout.windows.L9.necessity_specific_ci.0", expect=0.1797)]),
    dict(id="P2-04", phase="P2", status="VERIFIED",
         claim="The v2 116-example bench replicates: L9 all-occurrence +0.1101 (dev n=59) / +0.0649 (heldout n=55).",
         source="PHASE2_ALL_OCCURRENCES.md §2b", dirs=[D["p2_v2_all"]],
         script="scripts/phase6_mlp_causal.py", recompute=P6A.format(d=D["p2_v2_all"]),
         checks=[dict(kind="summary", dir=D["p2_v2_all"], path="by_split.dev.windows.L9.necessity_specific_ci.0", expect=0.1101),
                 dict(kind="summary", dir=D["p2_v2_all"], path="by_split.heldout.windows.L9.necessity_specific_ci.0", expect=0.0649)]),
    dict(id="P2-05", abstract_block='A control/robustness check that supports P2-01..04, not an abstract line of its own.', phase="P2", status="VERIFIED",
         claim="L9 is the argmax necessity layer in every split of all three benches under --positions all.",
         source="PHASE2_ALL_OCCURRENCES.md §2/§2b", dirs=[D["p2_ch_all"], D["p2_cu_all"], D["p2_v2_all"]],
         script="scripts/phase6_analyze.py", recompute=P6A.format(d=D["p2_ch_all"]),
         checks=[dict(kind="argmax", dir=d, leaf="necessity_specific_ci.0", expect="L9")
                 for d in (D["p2_ch_all"], D["p2_cu_all"], D["p2_v2_all"])]),
    dict(id="P2-06", abstract_block='A patch-primitive no-op control. Methods section, not the abstract.', phase="P2", status="VERIFIED",
         claim="Self-swap controls are exactly 0.0 at every layer and split (necessity and sufficiency), so the patch primitive is an exact no-op.",
         source="PHASE2_ALL_OCCURRENCES.md §2", dirs=[D["p2_ch_all"], D["p2_cu_all"], D["p2_v2_all"]],
         script="scripts/phase6_mlp_causal.py", recompute=P6A.format(d=D["p2_ch_all"]),
         checks=[dict(kind="leaf_extreme", dir=d, leaf=leaf, agg="maxabs", at_most=0.0)
                 for d in (D["p2_ch_all"], D["p2_cu_all"], D["p2_v2_all"])
                 for leaf in ("nec_selfswap_max_dev", "suf_selfswap_max_dev")]),
    dict(id="P2-07", abstract_block='A negative supporting result (necessity-not-sufficiency); belongs in the body next to P2-01..04.', phase="P2", status="VERIFIED",
         claim="Sufficiency (install the DS write into a benign prompt) stays <= ~0 at every layer -- the write is necessary, not sufficient.",
         source="PHASE2_ALL_OCCURRENCES.md §2/§4", dirs=[D["p2_ch_all"], D["p2_cu_all"], D["p2_v2_all"]],
         script="scripts/phase6_mlp_causal.py", recompute=P6A.format(d=D["p2_ch_all"]),
         checks=[dict(kind="leaf_extreme", dir=d, leaf="sufficiency_specific_ci.0", agg="max", at_most=0.02)
                 for d in (D["p2_ch_all"], D["p2_cu_all"], D["p2_v2_all"])]),
    dict(id="P2-08", phase="P2", status="UNDERPOWERED",
         claim="All-occurrence patching 'roughly DOUBLES' the L9 write (1.38x-2.27x across six cells), so the demo-only measurement understates the write by ~2x.",
         source="PHASE2_ALL_OCCURRENCES.md §3/§4", dirs=[D["p2_ch_all"], D["p2_ch_demo"], D["p2_cu_all"], D["p2_cu_demo"], D["p2_v2_all"]],
         script="scripts/phase6_mlp_causal.py", recompute=P6A.format(d=D["p2_ch_all"]),
         note="NOT an n problem and NOT fixable by more items: demo-only and all-occurrence are separate runs, so the ratio compares two independently-estimated effects with no CI on the increment. The report itself flags this (§4). A within-item PAIRED contrast of the two position sets is required before the '2x' goes in the paper.")

    ,
    # ============================== P10 — decode-safe concept write ============================
    dict(id="P10-01", abstract_block='NON-SIGNIFICANT (McNemar p=0.508) and it flips sign on the test split (P10-02). A large point estimate on a null arm must never be quoted as an effect.', phase="P10", status="VERIFIED", effect=0.0682,
         claim="Decode-safe write ablation moves ASR by +0.068 on clearharm train (n=44), McNemar p=0.508, Holm 1.0.",
         source="P10_DECODE_SAFE_WRITE.md §3", dirs=[D["p10_ds"]],
         script="scripts/phase_behav_write.py", recompute=BCA.format(d=D["p10_ds"]),
         checks=[dict(kind="summary", dir=D["p10_ds"], path="by_split.train.delta_necessity_write_decodesafe", expect=0.0682),
                 dict(kind="rows", dir=D["p10_ds"], expect=86)]),
    dict(id="P10-02", abstract_block='NON-SIGNIFICANT (p=0.581) and opposite in sign to train. Same reason as P10-01.', phase="P10", status="VERIFIED", effect=-0.0715,
         claim="Decode-safe write ablation moves ASR by -0.071 on clearharm test (n=42), McNemar p=0.581 -- the OPPOSITE sign to train.",
         source="P10_DECODE_SAFE_WRITE.md §3", dirs=[D["p10_ds"]],
         script="scripts/phase_behav_write.py", recompute=BCA.format(d=D["p10_ds"]),
         checks=[dict(kind="summary", dir=D["p10_ds"], path="by_split.test.delta_necessity_write_decodesafe", expect=-0.0715)]),
    dict(id="P10-03", phase="P10", status="VERIFIED", effect=-0.0227,
         claim="The historical prefill-only arm reproduces at -0.023 (train) / +0.095 (test), also sign-flipping across the split.",
         source="P10_DECODE_SAFE_WRITE.md §3", dirs=[D["p10_ds"], D["bw_ch"]],
         script="scripts/phase_behav_write.py", recompute=BCA.format(d=D["p10_ds"]),
         note="Matches the 2026-08-04 prefill-only run (behav_write_...707908: train -0.0227) to 4 dp, which is what makes the two phasings apples-to-apples.",
         checks=[dict(kind="summary", dir=D["p10_ds"], path="by_split.train.delta_necessity_write_prefill", expect=-0.0227),
                 dict(kind="summary", dir=D["p10_ds"], path="by_split.test.delta_necessity_write_prefill", expect=0.0952),
                 dict(kind="summary", dir=D["bw_ch"], path="by_split.train.delta_necessity_write", expect=-0.0227)]),
    dict(id="P10-04", phase="P10", status="VERIFIED", effect=0.0227,
         claim="The specificity-controlled contrast (write - count-matched random, decode damage held constant) is +0.023 on train and -0.072 on test.",
         source="P10_DECODE_SAFE_WRITE.md §3", dirs=[D["p10_ds"]],
         script="scripts/phase_behav_write.py", recompute=BCA.format(d=D["p10_ds"]),
         note="Sign-flipping across a pre-registered split is the signature of noise. |train| = 2.3 pp, i.e. AT the judge noise floor.",
         checks=[dict(kind="summary", dir=D["p10_ds"], path="by_split.train.delta_write_vs_randpos_decodesafe", expect=0.0227),
                 dict(kind="summary", dir=D["p10_ds"], path="by_split.test.delta_write_vs_randpos_decodesafe", expect=-0.0715)]),
    dict(id="P10-05", abstract_block='A control-arm magnitude (generic decode damage), quoted to defend the design; not a finding.', phase="P10", status="VERIFIED", effect=0.0455,
         claim="Generic decode damage alone (random-position decode-safe arm) moves train ASR +0.0455 -- ~2/3 of the apparent +0.068 'necessity'.",
         source="P10_DECODE_SAFE_WRITE.md §3", dirs=[D["p10_ds"]],
         script="scripts/phase_behav_write.py", recompute=BCA.format(d=D["p10_ds"]),
         note="This is why the raw baseline-vs-decodesafe delta must never be read as the effect.",
         checks=[dict(kind="summary", dir=D["p10_ds"], path="by_split.train.delta_decode_damage", expect=0.0455)]),
    dict(id="P10-06", abstract_block='A decoder-breakage guard. Methods section.', phase="P10", status="VERIFIED",
         claim="empty_rate = 0.0 in all 10 cells, so no P10 null is decoder breakage.",
         source="P10_DECODE_SAFE_WRITE.md §3", dirs=[D["p10_ds"]],
         script="scripts/phase_behav_write.py", recompute=BCA.format(d=D["p10_ds"]),
         checks=[dict(kind="summary", dir=D["p10_ds"], path=f"by_split.{sp}.empty.{arm}", expect=0.0)
                 for sp in ("train", "test")
                 for arm in ("baseline", "write_abl_prefill", "rand_pos_abl_prefill",
                             "write_abl_decodesafe", "rand_pos_abl_decodesafe")]),
    dict(id="P10-07", phase="P10", status="UNDERPOWERED",
         claim="The L8-11 concept write is behaviorally inert during generation, not merely during prefill (the concept-write null SURVIVES the decode-safe re-test).",
         source="P10_DECODE_SAFE_WRITE.md §4/§5", dirs=[D["p10_ds"]],
         script="scripts/phase_behav_write.py", recompute=BCA.format(d=D["p10_ds"]),
         note="n=86. At the measured flip-noise level 80% power needs n~275 for dASR=0.09 and n~419 for dASR=0.07 (P10_0 §5). "
              "NOTE a mis-citation to fix: P10_DECODE_SAFE_WRITE §5 attributes n~275 to dASR~0.07; P10.0's own table gives 275 for 0.09 and 419 for 0.07. "
              "The defensible sentence is 'no effect detectable at this n', never 'no effect'. v3 (170+154) is the power upgrade.")

    ,
    # ============================== P8.1 — alpha calibration ==================================
    dict(id="P81-01", phase="P8.1", status="VERIFIED",
         claim="The StrongREJECT judge flips ~2 pp of labels on BYTE-IDENTICAL text: 1/51 curated (2.0%) and 1/86 clearharm (1.2%), with 5/86 score changes and max |dscore| = 1.00.",
         source="PHASE8_1_ALPHA_CALIBRATION.md §'Read this first' 1", dirs=[D["a_ch"], D["a_cu"]],
         script="scripts/analyze_alpha_calibration.py",
         recompute="python scripts/analyze_alpha_calibration.py --md reports/_p8_1_tables.md",
         note="alpha=0 is an exact IEEE no-op (h - 0*proj*d == h) and the generations were sha256-verified byte-identical, so this isolates judge nondeterminism with the generation held exactly constant. THE MOST IMPORTANT METHODS NUMBER IN THE PAPER.",
         checks=[dict(kind="label_flips", dir=D["a_ch"], arms=("direct_base", "direct_refabl_a0.0"), expect=1),
                 dict(kind="label_flips", dir=D["a_cu"], arms=("direct_base", "direct_refabl_a0.0"), expect=1)]),
    dict(id="P81-02", abstract_block='Restates the consequence of P81-01; cite P81-01.', phase="P8.1", status="VERIFIED",
         claim="Consequence: any |dASR| below ~2 pp is indistinguishable from judge nondeterminism, and Ihat -- a contrast of FOUR judged arms -- has a floor of at least 2 pp.",
         source="PHASE8_1_ALPHA_CALIBRATION.md §'Read this first' 1", dirs=[D["a_ch"], D["a_cu"]],
         script="scripts/analyze_alpha_calibration.py",
         recompute="python scripts/analyze_alpha_calibration.py --md reports/_p8_1_tables.md",
         note="Every row of this table whose |effect| < 0.02 is flagged with the dagger below."),
    dict(id="P81-03", null_by_design=True, phase="P8.1", status="VERIFIED", effect=0.0,
         claim="The alpha=0 anchor behaves as a perfect no-op on the full clearharm cohort: Ihat = +0.000 exactly, ref-rand dASR = +0.000, D=+2 and D=-2 both 0.",
         source="PHASE8_1_ALPHA_CALIBRATION.md §'Full tables'", dirs=[D["a_ch"]],
         script="scripts/phase_behav_refusal.py --alphas 0,...", recompute="python scripts/analyze_alpha_calibration.py",
         checks=[dict(kind="interaction", dir=D["a_ch"], cells=("direct_base", "ds_base", "direct_refabl_a0.0", "ds_refabl_a0.0"), stat="Ihat", expect=0.0),
                 dict(kind="interaction", dir=D["a_ch"], cells=("direct_base", "ds_base", "direct_refabl_a0.0", "ds_refabl_a0.0"), stat="D+2", expect=0)]),
    dict(id="P81-04", abstract_block='A calibration/design constant (which dose to run at), not a scientific finding.', phase="P8.1", status="VERIFIED",
         claim="alpha = 0.25 is the sole qualifying operating point on clearharm: ASR(refusal-ablation alone) = 0.291 and I_max = +0.477 (2.6x the +0.186 available at alpha=1.0), at the FULL n=86.",
         source="PHASE8_1_ALPHA_CALIBRATION.md §'Headline answers' + CONTINUATION_PROGRESS 'P8.1 FINAL'",
         dirs=[D["a_ch"]], script="scripts/analyze_alpha_calibration.py",
         recompute="python scripts/analyze_alpha_calibration.py --run clearharm=" + D["a_ch"],
         note="ARTIFACT DRIFT: the committed report still shows the n=78 PROVISIONAL numbers (ASR 0.295, I_max +0.487) under a 'do not cite' banner. The n=86 values below are recomputed directly from the completed run dir.",
         checks=[dict(kind="rows", dir=D["a_ch"], expect=86),
                 dict(kind="interaction", dir=D["a_ch"], cells=("direct_base", "ds_base", "direct_refabl_a0.25", "ds_refabl_a0.25"), stat="ASR01", expect=0.2907),
                 dict(kind="interaction", dir=D["a_ch"], cells=("direct_base", "ds_base", "direct_refabl_a0.25", "ds_refabl_a0.25"), stat="I_max", expect=0.4767)]),
    dict(id="P81-05", phase="P8.1", status="VERIFIED", effect=-0.0233,
         claim="At the de-saturated operating point alpha=0.25 the interaction is Ihat = -0.023 -- no interaction detectable, and |Ihat| sits at the judge noise floor.",
         source="PHASE8_1_ALPHA_CALIBRATION.md + CONTINUATION_PROGRESS 'P8.1 FINAL'", dirs=[D["a_ch"]],
         script="scripts/analyze_alpha_calibration.py", recompute="python scripts/analyze_alpha_calibration.py --run clearharm=" + D["a_ch"],
         note="THIS IS THE ROW THAT WITHDRAWS P8.0. Recomputed from raw labels this sprint.",
         checks=[dict(kind="interaction", dir=D["a_ch"], cells=("direct_base", "ds_base", "direct_refabl_a0.25", "ds_refabl_a0.25"), stat="Ihat", expect=-0.0233)]),
    dict(id="P81-06", phase="P8.1", status="VERIFIED",
         claim="The alpha=0.25 interaction has p = 0.8597 with 95% CI [-0.151, +0.105].",
         source="PHASE8_1_ALPHA_CALIBRATION.md (FINAL, n=86) + outputs/alpha_calibration.json", dirs=[D["a_ch"]],
         script="scripts/analyze_alpha_calibration.py", recompute="python scripts/analyze_alpha_calibration.py --run clearharm=" + D["a_ch"],
         note="WAS UNVERIFIED and was the most dangerous row in this table: the permutation p and the bootstrap CI that WITHDRAW P8.0 "
              "existed in no committed artifact -- `outputs/alpha_calibration.json` held the curated cohort only, and the report on disk "
              "was the n=78 PROVISIONAL version with its own 'do not cite' banner. FIXED 2026-08-06: job 716014 had in fact completed "
              "(86/86 rows, DONE + summary), the analyzer was re-run over BOTH cohorts, and the report was re-issued at n=86. The "
              "regenerated values match the prose exactly (perm_p 0.859743, ci95 [-0.15116, +0.10465]) and are now checked from JSON below.",
         # list paths, not dotted: the alpha key is literally "0.25" and would be split in two.
         checks=[dict(kind="json_path", file="outputs/alpha_calibration.json",
                      path=["cohorts", "clearharm", "splits", "pooled", "0.25", "binary", "perm_p"], expect=0.8597),
                 dict(kind="json_path", file="outputs/alpha_calibration.json",
                      path=["cohorts", "clearharm", "splits", "pooled", "0.25", "binary", "Ihat"], expect=-0.0233),
                 dict(kind="json_path", file="outputs/alpha_calibration.json",
                      path=["cohorts", "clearharm", "splits", "pooled", "0.25", "binary", "ci95", 0], expect=-0.1512),
                 dict(kind="json_path", file="outputs/alpha_calibration.json",
                      path=["cohorts", "clearharm", "splits", "pooled", "0.25", "binary", "ci95", 1], expect=0.1047),
                 dict(kind="json_path", file="outputs/alpha_calibration.json",
                      path=["cohorts", "clearharm", "provisional"], expect=False)]),
    dict(id="P81-07", phase="P8.1", status="VERIFIED",
         claim="Ihat tracks the arithmetic ceiling almost perfectly: Spearman(I_max, Ihat_binary) = +0.991 on clearharm pooled (n=86) and +0.955 on curated (n=51).",
         source="PHASE8_1_ALPHA_CALIBRATION.md §'Read this first' 2", dirs=[D["a_ch"], D["a_cu"]],
         script="scripts/analyze_alpha_calibration.py", recompute="python scripts/analyze_alpha_calibration.py",
         note="I_max is a function of the MARGINAL cells only -- it carries no information about the joint cell -- so a real mechanism has no reason to track it. Independently recomputed at +0.991 this sprint."),
    dict(id="P81-08", phase="P8.1", status="VERIFIED",
         claim="On curated the ceiling REVERSES between alpha=1.5 and 2.0 (I_max +0.353 -> +0.412) and Ihat reverses with it (-0.353 -> -0.196).",
         source="PHASE8_1_ALPHA_CALIBRATION.md §'Read this first' 2", dirs=[D["a_cu"]],
         script="scripts/analyze_alpha_calibration.py", recompute="python scripts/analyze_alpha_calibration.py",
         note="The decisive detail: Ihat follows I_max even where I_max is NON-monotone in alpha, which rules out 'both merely trend with dose'.",
         checks=[dict(kind="interaction", dir=D["a_cu"], cells=("direct_base", "ds_base", "direct_refabl_a2.0", "ds_refabl_a2.0"), stat="I_max", expect=0.4118, tol=1e-3),
                 dict(kind="interaction", dir=D["a_cu"], cells=("direct_base", "ds_base", "direct_refabl_a1.5", "ds_refabl_a1.5"), stat="I_max", expect=0.3529, tol=1e-3)]),
    dict(id="P81-09", abstract_block='Reproduces a number whose MECHANISTIC READING IS WITHDRAWN (P80-02). Citing it without the ceiling context would resurrect the retracted claim.', phase="P8.1", status="VERIFIED", effect=-0.2093,
         claim="At alpha = 1.0 -- the dose P8.0 used -- the same estimator on the same items reproduces significant sub-additivity: Ihat = -0.209 (P8.0's own run gave -0.186).",
         source="PHASE8_1_ALPHA_CALIBRATION.md + PHASE8_0 banner", dirs=[D["a_ch"], D["br_ch"]],
         script="scripts/analyze_alpha_calibration.py", recompute="python scripts/analyze_interaction_2x2.py",
         note="The 0.023 gap between two runs of the SAME condition is itself the judge-instability envelope.",
         checks=[dict(kind="interaction", dir=D["a_ch"], cells=("direct_base", "ds_base", "direct_refabl_a1.0", "ds_refabl_a1.0"), stat="Ihat", expect=-0.2093),
                 dict(kind="interaction", dir=D["br_ch"], cells=("direct_base", "ds_base", "direct_refabl", "ds_refabl"), stat="Ihat", expect=-0.186)]),
    dict(id="P81-10", phase="P8.1", status="VERIFIED", effect=0.186,
         claim="Specificity holds at the operating point: refusal-ablation minus norm-matched random ablation = +0.186 dASR at alpha=0.25, McNemar p = 0.0001 (~9x the noise floor), with the random arm leaving refusal_rate at 0.872 vs the true arm's 0.674.",
         source="PHASE8_1_ALPHA_CALIBRATION.md §'Headline answers'", dirs=[D["a_ch"]],
         script="scripts/analyze_alpha_calibration.py", recompute="python scripts/analyze_alpha_calibration.py",
         note="First time this project has had the random-direction control at any dose other than alpha=1.0.",
         checks=[dict(kind="rate", dir=D["a_ch"], field="direct_refabl_a0.25_label", eq="MALICIOUS", expect=0.2907),
                 dict(kind="rate", dir=D["a_ch"], field="direct_randabl_a0.25_label", eq="MALICIOUS", expect=0.1047)]),
    dict(id="P81-11", abstract_block='A cohort-selection/design result. Body, not abstract.', phase="P8.1", status="VERIFIED",
         claim="On curated NO alpha qualifies -- the dose response steps from 0.294 at alpha=0 (the no-op) straight to 0.529 at alpha=0.25, over the 0.20-0.40 band; the clearharm operating point does NOT transfer.",
         source="PHASE8_1_ALPHA_CALIBRATION.md §'Headline answers'", dirs=[D["a_cu"]],
         script="scripts/analyze_alpha_calibration.py", recompute="python scripts/analyze_alpha_calibration.py",
         checks=[dict(kind="rate", dir=D["a_cu"], field="direct_refabl_a0.25_label", eq="MALICIOUS", expect=0.5294),
                 dict(kind="rate", dir=D["a_cu"], field="direct_refabl_a0.0_label", eq="MALICIOUS", expect=0.2941)]),
    dict(id="P81-12", abstract_block='A cohort-quality observation. Body, not abstract.', phase="P8.1", status="VERIFIED",
         claim="On curated the attack is NET-NEGATIVE by ASR: ds_base 0.275 < direct_base 0.314 -- making curated a poor interaction cohort regardless of dose.",
         source="PHASE8_1_ALPHA_CALIBRATION.md §'Headline answers'", dirs=[D["a_cu"]],
         script="scripts/analyze_alpha_calibration.py", recompute="python scripts/analyze_alpha_calibration.py",
         checks=[dict(kind="rate", dir=D["a_cu"], field="ds_base_label", eq="MALICIOUS", expect=0.2745),
                 dict(kind="rate", dir=D["a_cu"], field="direct_base_label", eq="MALICIOUS", expect=0.3137)]),
    dict(id="P81-13", phase="P8.1", status="UNDERPOWERED",
         claim="D_i = +2 (the item-level synergy signature: neither factor jailbreaks alone but both do together) occurs ZERO times on the PRIMARY clearharm cohort at every dose (0/86), but is NOT zero everywhere -- curated shows 4 occurrences (a=0.5:1, 1.5:1, 2.0:2 of 51 items). The ceiling-immune no-synergy backstop holds on clearharm, not universally.",
         source="PHASE8_1_ALPHA_CALIBRATION.md tables + PHASE8_0 §2.3", dirs=[D["a_ch"], D["a_cu"], D["br_ch"]],
         script="scripts/analyze_interaction_2x2.py", recompute="python scripts/analyze_alpha_calibration.py",
         note="CORRECTED 2026-08-06 (bughunt F1): was VERIFIED with the false claim 'zero in every cohort'. The check only tested the clearharm dir while CITING the curated dir as evidence and never checking it -- so the audit certified 8/8 ok on a claim the project's own PHASE8_1 report (lines 307/311) contradicts. Recomputed from curated raw: D=+2 counts {0.5:1, 1.5:1, 2.0:2} = 4 total. The clearharm 0/86 IS the ceiling-immune backstop and stands; the '137 items, zero' phrasing does not. Curated checks now included below and EXPECTED to reflect the true nonzero counts.",
         checks=[dict(kind="interaction", dir=D["a_ch"], cells=("direct_base", "ds_base", f"direct_refabl_a{a}", f"ds_refabl_a{a}"), stat="D+2", expect=0)
                 for a in ("0.0", "0.25", "0.5", "0.75", "1.0", "1.5", "2.0")]
                + [dict(kind="interaction", dir=D["br_ch"], cells=("direct_base", "ds_base", "direct_refabl", "ds_refabl"), stat="D+2", expect=0)]
                + [dict(kind="interaction", dir=D["a_cu"], cells=("direct_base", "ds_base", f"direct_refabl_a{a}", f"ds_refabl_a{a}"), stat="D+2", expect=exp)
                   for a, exp in [("0.0", 0), ("0.25", 0), ("0.5", 1), ("0.75", 0), ("1.0", 0), ("1.5", 1), ("2.0", 2)]]),

    # ============================== P8.0 — the withdrawn pilot ================================
    dict(id="P80-01", abstract_block='The number is sound but its MECHANISTIC READING IS WITHDRAWN (P80-02); quoting it in an abstract would resurrect the retracted claim.', phase="P8.0", status="VERIFIED", effect=-0.186,
         claim="AS A MEASUREMENT AT alpha=1.0: clearharm pooled Ihat = -0.186 [-0.349, -0.023], permutation p = 0.045 (n=86).",
         source="PHASE8_0_PILOT_INTERACTION.md §2.2", dirs=[D["br_ch"]],
         script="scripts/analyze_interaction_2x2.py", recompute="python scripts/analyze_interaction_2x2.py",
         note="The number is real; what it MEANS is withdrawn (see P80-02).",
         checks=[dict(kind="interaction", dir=D["br_ch"], cells=("direct_base", "ds_base", "direct_refabl", "ds_refabl"), stat="Ihat", expect=-0.186),
                 dict(kind="interaction", dir=D["br_ch"], cells=("direct_base", "ds_base", "direct_refabl", "ds_refabl"), stat="I_max", expect=0.1744)]),
    dict(id="P80-02", phase="P8.0", status="WITHDRAWN",
         claim="'Doublespeak and refusal-ablation are sub-additive => they act on a SHARED REFUSAL BOTTLENECK.'",
         source="PHASE8_0_PILOT_INTERACTION.md §5.1/§5.2 (banner + inline withdrawal)", dirs=[D["br_ch"], D["a_ch"]],
         script="scripts/analyze_interaction_2x2.py", recompute="python scripts/analyze_alpha_calibration.py",
         note="WITHDRAWN 2026-08-05 -- the sub-additivity is a SATURATION ARTIFACT of running the ablation at alpha=1.0, not a property of the mechanism. In detail: Ihat tracks the ceiling (Spearman +0.991), and at the "
              "de-saturated alpha=0.25 Ihat = -0.023, p = 0.86. Significance appears only as headroom disappears (p 0.86 -> 0.38 -> 0.064 -> 0.020 -> 0.005 -> 0.0004 "
              "while I_max falls +0.477 -> +0.023). Absence of a detectable interaction is NOT evidence of independence either."),
    dict(id="P80-03", phase="P8.0", status="WITHDRAWN",
         claim="'Six pooled estimates, all six with p < 0.05' (binary ASR, graded score and compliance as three corroborating outcomes).",
         source="PHASE8_0_PILOT_INTERACTION.md §5.1 correction", dirs=[D["br_ch"]],
         script="scripts/analyze_interaction_2x2.py", recompute="python scripts/analyze_interaction_2x2.py",
         note="WITHDRAWN after adversarial review: the binary MALICIOUS label is a DETERMINISTIC threshold of the graded score (0 violations of label <=> score >= 0.25 "
              "across 5 arms x 137 rows), so the three outcomes are ONE measurement viewed three ways. The framing inflated the apparent weight of evidence."),
    dict(id="P80-04", phase="P8.0", status="WITHDRAWN", effect=-0.431,
         claim="curated compliance interaction Ihat = -0.431 [-0.569, -0.294], p < 0.0001.",
         source="PHASE8_0_PILOT_INTERACTION.md §3/§5.1", dirs=[D["br_cu"]],
         script="scripts/analyze_interaction_2x2.py", recompute="python scripts/analyze_interaction_2x2.py",
         note="WITHDRAWN as algebraically degenerate -- it is the MAIN EFFECT of refusal ablation, not an interaction. Compliance = 1.000 in BOTH Doublespeak arms, so D_i collapses to Y(0,0) - Y(0,1) -- the MAIN EFFECT of refusal "
              "ablation on the direct arm, not an interaction at all."),
    dict(id="P80-05", phase="P8.0", status="WITHDRAWN", effect=0.579,
         claim="Among refusal-ablation-resistant items, Doublespeak on top of ablation adds +0.579 ASR.",
         source="PHASE8_0_PILOT_INTERACTION.md §2.5", dirs=[D["br_ch"]],
         script="scripts/analyze_interaction_2x2.py", recompute="python scripts/analyze_interaction_2x2.py",
         note="WITHDRAWN as a causal estimate: the subgroup is defined by conditioning on a POST-TREATMENT outcome (Y(0,1)=0), which selects for downward judge noise "
              "in exactly that arm; the effect is inflated by regression to the mean. Same family of error as the headroom-vs-saturated split (tick 15), where the "
              "subgroup algebra mechanically forces D_i >= 0."),
    dict(id="P80-06", phase="P8.0", status="SUPERSEDED",
         claim="'The 7.5% label-flip rate between technical replicates in the signal arms is StrongREJECT judge variance.'",
         source="PHASE8_0_PILOT_INTERACTION.md §5.3b", dirs=[D["br_ch"], D["br_twin"]],
         script="scripts/analyze_interaction_2x2.py", recompute="python scripts/analyze_interaction_2x2.py",
         note="SUPERSEDED by the byte-identical measurement (P81-01): with the generation held EXACTLY constant the judge flips only ~2 pp. So of the 7.5% replicate "
              "flip rate, ~2 pp is irreducible judge variance and the remainder is genuine generation difference. The instability itself stands (Ihat swings 0.050 "
              "between replicates on the same 80 items), and it is why p = 0.045 must not be reported as a clean significance."),
    dict(id="P80-07", abstract_block='A design diagnostic (the ceiling), quoted to explain why P80-02 fell. Body, not abstract.', phase="P8.0", status="VERIFIED",
         claim="At alpha=1.0 the design is severely ceiling-limited: I_max = +0.174 and 54/86 (62.8%) of items are already jailbroken by one factor alone, so they can only contribute D_i <= 0.",
         source="PHASE8_0_PILOT_INTERACTION.md §2.4", dirs=[D["br_ch"]],
         script="scripts/analyze_interaction_2x2.py", recompute="python scripts/analyze_interaction_2x2.py",
         note="Written as a caveat; it turned out to be the whole story.",
         checks=[dict(kind="interaction", dir=D["br_ch"], cells=("direct_base", "ds_base", "direct_refabl", "ds_refabl"), stat="I_max", expect=0.1744)])

    ,
    # ============================== P10.0 — graded re-analysis ================================
    dict(id="P100-01", abstract_block='FAILS ITS OWN SPECIFICITY CONTROL (P100-02): a size-matched random-head ablation reaches 53% of it and the contrast is p=0.382.', phase="P10.0", status="VERIFIED", effect=0.0741,
         claim="BEHAV-CARRY / clearharm pooled on the graded StrongREJECT score: d = +0.0741 [+0.009, +0.142], Wilcoxon p = 0.0343, permutation p = 0.0337 (n=86).",
         source="P10_0_GRADED_REANALYSIS.md §2/§3", dirs=[D["bc_ch"]],
         script="scripts/analyze_graded_reanalysis.py",
         recompute="python scripts/analyze_graded_reanalysis.py --out-json outputs_scratch/p10_0.json",
         note="Reproduces plan §0.5's pilot number exactly. Reproducing it is not the same as it surviving -- see P100-02."),
    dict(id="P100-02", phase="P10.0", status="WITHDRAWN",
         claim="'The graded score flips the carry-head verdict (p=0.033) => the L14-21 carry heads ARE behaviorally necessary.'",
         source="P10_0_GRADED_REANALYSIS.md §2/§4/§7", dirs=[D["bc_ch"], D["bc_cu"]],
         script="scripts/analyze_graded_reanalysis.py", recompute="python scripts/analyze_graded_reanalysis.py",
         note="FAILS ITS OWN SPECIFICITY CONTROL -- the targeted ablation is not demonstrably better than a size-matched random one. The random-head arm gives +0.0392 in the same cell -- 53% of the carry effect -- and the direct "
              "within-item contrast (random - carry) is +0.0349 [-0.039, +0.110], permutation p = 0.382. The targeted ablation is NOT demonstrably better than a "
              "random one of the same size. Also: only 22/86 items are non-tied; leave-one-out p reaches 0.0624; dropping the 5 largest positive diffs gives p = 0.466; "
              "curated goes the other way (-0.017, p = 0.794); exactly 1 of 24 graded tests reaches p<0.05 and it is the pooled cell (neither split alone: 0.114/0.208). "
              "DO NOT write 'the carry heads are behaviorally necessary' from this."),
    dict(id="P100-03", abstract_block='A null contrast. It is the reason P100-01 is blocked, not a standalone claim.', phase="P10.0", status="VERIFIED", effect=0.0349,
         claim="The specificity contrast (random-head minus carry-head, graded, within item) is +0.0349 [-0.039, +0.110], permutation p = 0.382 -- null.",
         source="P10_0_GRADED_REANALYSIS.md §4", dirs=[D["bc_ch"]],
         script="scripts/analyze_graded_reanalysis.py", recompute="python scripts/analyze_graded_reanalysis.py",
         note="Every one of the 6 specificity contrasts is null, including one-sided. No cell shows the targeted ablation beating its random control."),
    dict(id="P100-04", phase="P10.0", status="VERIFIED", effect=-0.0044,
         claim="BEHAV-WRITE is null on the graded endpoint too (clearharm pooled -0.0044, p = 0.941) -- the graded re-analysis rescues nothing for the concept write.",
         source="P10_0_GRADED_REANALYSIS.md §3", dirs=[D["bw_ch"]],
         script="scripts/analyze_graded_reanalysis.py", recompute="python scripts/analyze_graded_reanalysis.py"),
    dict(id="P100-05", phase="P10.0", status="VERIFIED",
         claim="Post-hoc power of the binary carry test was 0.135 (train) / 0.086 (test); at 80% power n = 275 for dASR = 0.09 and n = 419 for dASR = 0.07 (p0 = 0.0894 from the random-control arms, b=25/c=24/n=274).",
         source="P10_0_GRADED_REANALYSIS.md §5", dirs=[D["bc_ch"], D["bc_cu"], D["bw_ch"], D["bw_cu"]],
         script="scripts/analyze_graded_reanalysis.py", recompute="python scripts/analyze_graded_reanalysis.py",
         note="A test with 9-14% power did not, and could not, license the word 'inert'. This is the n that every behavioral null in the paper must be quoted against."),
    dict(id="P100-06", abstract_block='A property of the exact test, not of the model. Methods section.', phase="P10.0", status="VERIFIED",
         claim="Four binary cells sit at or above the exact test's granularity floor (0.0625-0.500) and COULD NOT have produced a significant result under any data whatsoever.",
         source="P10_0_GRADED_REANALYSIS.md §5", dirs=[D["bc_ch"], D["bc_cu"], D["bw_cu"]],
         script="scripts/analyze_graded_reanalysis.py", recompute="python scripts/analyze_graded_reanalysis.py",
         note="Reporting those as 'null' was never meaningful."),
    dict(id="P100-07", phase="P10.0", status="WITHDRAWN",
         claim="'The concept circuit is behaviorally INERT.'",
         source="P10_0_GRADED_REANALYSIS.md §7.1 (retraction)", dirs=[D["bc_ch"], D["bw_ch"]],
         script="scripts/analyze_graded_reanalysis.py", recompute="python scripts/analyze_graded_reanalysis.py",
         note="RETRACTED as worded -- it rested on binary tests with 8-14% power, four of which were arithmetically incapable of rejecting. The supportable statement is "
              "'no effect detectable at this n', and after P10 the honest version is P10-07 / BC-02."),
    dict(id="P100-08", artifact='outputs_scratch/p10_0.json (analysis output, regenerated on demand)', abstract_block='An analysis-code bug fix.', phase="P10.0", status="VERIFIED",
         claim="A binary-search bug made 12 of 16 '>4000' entries in the power table false (true values ~2500-4150); fixed, and a leaf-by-leaf diff shows exactly 16 values changed and nothing else.",
         source="P10_0_GRADED_REANALYSIS.md correction note + §8", dirs=[],
         script="scripts/analyze_graded_reanalysis.py", recompute="python scripts/analyze_graded_reanalysis.py",
         note="A <=0.25% residual offset against an external audit's values is documented and does not change any qualitative statement.")

    ,
    # ============================== P1 — published-baseline audit =============================
    dict(id="P1-01", abstract_block='An audit verdict on a defect that had zero exposure; the number that matters is P1-02 / FIN-01.', phase="P1", status="VERIFIED",
         claim="ZERO of the 411 Phase 2.1 generations are empty or whitespace-only, so `14_behavioral_eval.py`'s missing EMPTY label cannot have shifted any published number. VERDICT: SAFE.",
         source="P1_BASELINE_AUDIT.md §'Result'", dirs=[D["p21_ch"], D["p21_cu"]],
         script="scripts/audit_phase21_baseline.py", recompute="python scripts/audit_phase21_baseline.py",
         checks=[dict(kind="empty_frac", dir=D["p21_ch"], file="behavioral_raw.jsonl", field="response", expect=0),
                 dict(kind="empty_frac", dir=D["p21_cu"], file="behavioral_raw.jsonl", field="response", expect=0),
                 dict(kind="rows", dir=D["p21_ch"], file="behavioral_raw.jsonl", expect=258),
                 dict(kind="rows", dir=D["p21_cu"], file="behavioral_raw.jsonl", expect=153)]),
    dict(id="P1-02", abstract_block='The same six numbers as FIN-01; cite FIN-01.', phase="P1", status="VERIFIED",
         claim="All 6 published Phase 2.1 malicious rates recompute exactly: clearharm direct .1163 / neutral .2558 / doublespeak .3488; curated .2549 / .0392 / .2353.",
         source="P1_BASELINE_AUDIT.md §'Every published rate recomputes exactly'", dirs=[D["p21_ch"], D["p21_cu"]],
         script="scripts/14_behavioral_eval.py (published) / audit_phase21_baseline.py (audit)",
         recompute="python scripts/audit_phase21_baseline.py",
         checks=[dict(kind="rate", dir=D["p21_ch"], file="behavioral_raw.jsonl", where={"condition": c}, field="label", eq="MALICIOUS", expect=e)
                 for c, e in (("direct", 0.1163), ("neutral", 0.2558), ("doublespeak", 0.3488))]
                + [dict(kind="rate", dir=D["p21_cu"], file="behavioral_raw.jsonl", where={"condition": c}, field="label", eq="MALICIOUS", expect=e)
                   for c, e in (("direct", 0.2549), ("neutral", 0.0392), ("doublespeak", 0.2353))]),
    dict(id="P1-03", abstract_block='A secondary generation-length observation. Methods/limitations.', phase="P1", status="VERIFIED",
         claim="Truncation at max_new_tokens=200 is heavy and cohort-asymmetric: stop_reason=length on 65/258 (25%) of clearharm but 110/153 (72%) of curated generations.",
         source="P1_BASELINE_AUDIT.md §'Secondary finding'", dirs=[D["p21_ch"], D["p21_cu"]],
         script="scripts/audit_phase21_baseline.py", recompute="python scripts/audit_phase21_baseline.py",
         note="Common-mode across conditions so it does not bias the DS-vs-direct contrast, but it is a plausible contributor to curated's complied-but-benign gap and "
              "the concept-dilution reading. Behavioral harnesses use 220; record stop_reason in every future run.",
         checks=[dict(kind="rate", dir=D["p21_ch"], file="behavioral_raw.jsonl", field="stop_reason", eq="length", expect=0.2519, tol=2e-3),
                 dict(kind="rate", dir=D["p21_cu"], file="behavioral_raw.jsonl", field="stop_reason", eq="length", expect=0.7190, tol=2e-3)])

    ,
    # ============================== P1b — dataset =============================================
    dict(id="P1b-01", artifact='data/splits/clearharm_doublespeak_v3.json', phase="P1b", status="VERIFIED",
         claim="ClearHarm Doublespeak split v3.1: 324 examples / 224 single-token concepts / 215 intent clusters, train 162 / dev 82 / test 80, with ZERO concepts, codewords or clusters straddling any split pair and 0 placeholder demos.",
         source="P1B_V3_SPLIT.md §2/§5", dirs=[], script="scripts/expand_concepts_v3.py --stage build",
         recompute="python scripts/validate_data_integrity.py --split data/splits/clearharm_doublespeak_v3.json --tokenizer meta-llama/Llama-3.1-8B-Instruct",
         checks=[dict(kind="split_stat", file="data/splits/clearharm_doublespeak_v3.json", stat="n", expect=324),
                 dict(kind="split_stat", file="data/splits/clearharm_doublespeak_v3.json", stat="straddling_concepts", expect=0),
                 dict(kind="split_stat", file="data/splits/clearharm_doublespeak_v3.json", stat="straddling_codewords", expect=0)]),
    dict(id="P1b-02", artifact='data/splits/clearharm_doublespeak_v3.json (_meta.leakage)', phase="P1b", status="VERIFIED",
         claim="v1's leakage: 14/43 concepts and 17/21 codewords straddle train/test, and 77/86 rows (90%) carry at least one leak -- so v1 supports NO 'unseen concept' or 'unseen codeword' generalization claim.",
         source="P1B_V3_SPLIT.md §1", dirs=[], script="scripts/build_split_v3.py",
         recompute="python scripts/build_split_v3.py  # prints the [leak] v1 line",
         note="v1's `no intent_cluster overlap` check was VACUOUS -- intent_cluster was a per-INSTRUCTION hash, so all 86 rows were 86 distinct clusters. "
              "Every published behavioral number in this project was measured on v1."),
    dict(id="P1b-03", artifact='data/splits/clearharm_doublespeak_v3.json (_meta.spend_usd_approx) + data/expanded_concepts_v3.json', abstract_block='Cost accounting.', phase="P1b", status="VERIFIED",
         claim="The v3.1 expansion cost $0.14 across 496 OpenAI calls, and recovery (not generation) produced the concepts: steps 1-2 cost $0.026 for +25 concepts.",
         source="P1B_V3_SPLIT.md §4.5", dirs=[], script="scripts/expand_concepts_v3.py",
         recompute="python -c \"import json;print(json.load(open('data/splits/clearharm_doublespeak_v3.json'))['_meta']['spend_usd_approx'])\""),
    dict(id="P1b-04", artifact='data/splits/clearharm_doublespeak_v3.json', phase="P1b", status="VERIFIED",
         claim="v3 has TWO cohorts -- clearharm (170 real ClearHarm instructions) and generated (154 gpt-4o-mini one-liners) -- so every headline result on v3 must be reported per cohort as well as pooled.",
         source="P1B_V3_SPLIT.md §6.2", dirs=[], script="scripts/expand_concepts_v3.py",
         recompute="python scripts/validate_data_integrity.py --split data/splits/clearharm_doublespeak_v3.json",
         note="A cohort x condition interaction would mean the generated arm is NOT exchangeable with real ClearHarm and the two cannot be pooled. "
              "Cross-split instruction TF-IDF rose 0.489 -> 0.621 (still 0 pairs above the 0.7 threshold)."),
    dict(id="P1b-05", artifact='data/splits/clearharm_doublespeak_v3.json', phase="P1b", status="WITHDRAWN",
         claim="'Zero ClearHarm instruction pairs exceed TF-IDF cosine 0.5' (plan §5 P1b).",
         source="P1B_V3_SPLIT.md §1 (correction to the plan)", dirs=[], script="scripts/build_split_v3.py",
         recompute="python scripts/build_split_v3.py",
         note="FALSE: max pairwise cosine is 0.690 with 3 pairs above 0.5. The conclusion survives (the built v3's cross-split max is lower and no concept straddles), "
              "but the post-split near-duplicate audit is therefore REQUIRED, not optional."),
    dict(id="P1b-06", phase="P1b", status="VERIFIED",
         claim="The P8 core factorial on v3 runs at alpha=0.25 with n = 242 (clearharm 127 + generated 115), not the 324 the power table targets, because dev is reserved for selection by design.",
         source="CONTINUATION_PROGRESS.md tick 35", dirs=[D["p8_v3_ch"], D["p8_v3_gen"]],
         script="scripts/phase_behav_refusal.py --alphas 0.25", recompute="python scripts/analyze_interaction_2x2.py",
         note="RESOLVED: both cohorts completed -- clearharm 721956 (127 rows) and generated 720725 (115), n=242 total, and reports/P8_INTERACTION_V3.md is COMPLETE. "
              "The PENDING status and the 720724 pointer were both stale: 720724 stalled on n-801 with no data and the cohort was re-run as 721956. "
              "242 is still 2.8x the n=86 that made P8.1's CI uninterpretable. The write-up must quote n=242.")

    ,
    # ============================== BEHAV-REFUSAL — the positive locus =========================
    dict(id="BR-01", phase="BEHAV-REFUSAL", status="VERIFIED", effect=0.432,
         claim="Ablating the L18 refusal direction at every layer/position through generation raises ASR by +0.432/+0.476 (clearharm train/test) and +0.433/+0.429 (curated), every split p <= 0.004.",
         source="PHASE_BEHAV_REFUSAL.md §'Result'", dirs=[D["br_ch"], D["br_cu"]],
         script="scripts/phase_behav_refusal.py", recompute=BCA.format(d=D["br_ch"]),
         note="THE strongest behavioral effect in the project -- ~20x the judge noise floor.",
         checks=[dict(kind="rate", dir=D["br_ch"], where={"split": "train"}, field="direct_refabl_label", eq="MALICIOUS", expect=0.5682),
                 dict(kind="rate", dir=D["br_ch"], where={"split": "train"}, field="direct_base_label", eq="MALICIOUS", expect=0.1364),
                 dict(kind="rate", dir=D["br_ch"], where={"split": "test"}, field="direct_refabl_label", eq="MALICIOUS", expect=0.5476)]),
    dict(id="BR-02", null_by_design=True, phase="BEHAV-REFUSAL", status="VERIFIED", effect=0.0,
         claim="Clean specificity: a norm-matched RANDOM direction has no effect on any split (dASR 0.000 on clearharm, McNemar p >= 0.5, refusal_rate unchanged).",
         source="PHASE_BEHAV_REFUSAL.md §'Result' 2", dirs=[D["br_ch"], D["br_cu"]],
         script="scripts/phase_behav_refusal.py", recompute=BCA.format(d=D["br_ch"]),
         checks=[dict(kind="rate", dir=D["br_ch"], where={"split": "train"}, field="direct_randabl_label", eq="MALICIOUS", expect=0.1364),
                 dict(kind="rate", dir=D["br_ch"], where={"split": "test"}, field="direct_randabl_label", eq="MALICIOUS", expect=0.0714)]),
    dict(id="BR-03", phase="BEHAV-REFUSAL", status="VERIFIED", effect=0.182,
         claim="Refusal-ablation alone is at least as strong an attack as Doublespeak on all four splits (significantly on 3/4): e.g. clearharm train .568 vs ds_base .386.",
         source="PHASE_BEHAV_REFUSAL.md §'Result' 3", dirs=[D["br_ch"], D["br_cu"]],
         script="scripts/phase_behav_refusal.py", recompute=BCA.format(d=D["br_ch"]),
         checks=[dict(kind="rate", dir=D["br_ch"], where={"split": "train"}, field="ds_base_label", eq="MALICIOUS", expect=0.3864)]),
    dict(id="BR-04", phase="BEHAV-REFUSAL", status="VERIFIED", effect=0.386,
         claim="Necessity: re-injecting +alpha*refusal-axis into Doublespeak generation drives ASR monotonically to 0.000 at alpha=12 in all four cells (clearharm p=2e-5 / 3e-5), refusal_rate -> 1.000.",
         source="PHASE_BEHAV_REFUSAL.md §'Necessity'", dirs=[D["inj_ch"], D["inj_cu"]],
         script="scripts/phase_behav_refusal_inject.py", recompute=BCA.format(d=D["inj_ch"]),
         checks=[dict(kind="summary", dir=D["inj_ch"], path="by_split.train.ASR.ds_refadd12", expect=0.0),
                 dict(kind="summary", dir=D["inj_ch"], path="by_split.test.ASR.ds_refadd12", expect=0.0),
                 dict(kind="summary", dir=D["inj_ch"], path="by_split.train.refusal_rate.ds_refadd12", expect=1.0)]),
    dict(id="BR-05", phase="BEHAV-REFUSAL", status="VERIFIED", effect=0.114,
         claim="The re-injection is axis-specific: a norm-matched random push of equal norm at alpha=8 NEVER lowers ASR (it raises it to 0.500 on clearharm) and never restores refusal.",
         source="PHASE_BEHAV_REFUSAL.md §'Necessity'", dirs=[D["inj_ch"], D["inj_cu"]],
         script="scripts/phase_behav_refusal_inject.py", recompute=BCA.format(d=D["inj_ch"]),
         checks=[dict(kind="summary", dir=D["inj_ch"], path="by_split.train.ASR.ds_randadd8", expect=0.5),
                 dict(kind="summary", dir=D["inj_ch"], path="by_split.test.ASR.ds_randadd8", expect=0.5)]),
    dict(id="BR-06", abstract_block='A coherence/decoder-breakage guard, and one leg of that audit (reading the completions) is a human inspection this table cannot re-derive.', phase="BEHAV-REFUSAL", status="VERIFIED",
         claim="The ASR->0 is genuine refusal restoration, not decoder breakage: empty_rate = 0.000 in every cell at every alpha, and the effect is already strong at the milder alpha=8.",
         source="PHASE_BEHAV_REFUSAL.md §'Coherence audit'", dirs=[D["inj_ch"], D["inj_cu"]],
         script="scripts/phase_behav_refusal_inject.py", recompute=BCA.format(d=D["inj_ch"]),
         note="The third leg of that audit -- reading the alpha=8/12 completions and finding fluent refusals -- is a human inspection and is NOT re-derivable by this script."),
    dict(id="BR-07", phase="BEHAV-REFUSAL", status="VERIFIED", effect=0.383,
         claim="Doublespeak only PARTIALLY suppresses refusal: ds_base refusal_rate .45-.48 on clearharm, against direct .84-.88 and full ablation .05-.10.",
         source="PHASE_BEHAV_REFUSAL.md §'Corroborating detail'", dirs=[D["br_ch"]],
         script="scripts/phase_behav_refusal.py", recompute=BCA.format(d=D["br_ch"]),
         note="This headroom is why ds_refabl exceeds either factor alone, and it is the mechanism-level reason Doublespeak's base ASR is only ~0.36.",
         checks=[dict(kind="rate", dir=D["br_ch"], where={"split": "train"}, field="ds_base_label", eq="REJECTED", expect=0.4773),
                 dict(kind="rate", dir=D["br_ch"], where={"split": "train"}, field="direct_base_label", eq="REJECTED", expect=0.8409)]),
    dict(id="BR-08", phase="BEHAV-REFUSAL", status="VERIFIED", effect=-0.25,
         claim="Calibrated depth-localization: injecting each layer's own refusal direction at alpha = its measured direct-ds projection gap rescues the model at L22 (dASR -0.250, p=0.001 train; -0.167, p=0.039 test) and at L16/L28, with the random control null at every layer.",
         source="PHASE_BEHAV_REFUSAL.md §'Calibrated localization'", dirs=[D["cal_ch"], D["cal_cu"], D["p7_full"]],
         script="scripts/phase_refusal_inject_calibrated.py", recompute=BCA.format(d=D["cal_ch"]),
         note="PENDING because it depends on the per-layer refusal directions, whose validation (job 720463) is still in flight. The DSVALN=3 smoke says L22 is VALID "
              "(separation +0.413), which is reassuring, but each smoke flag is a single-item decision.",
         checks=[dict(kind="summary", dir=D["cal_ch"], path="by_split.train.by_layer_vs_ds_base.22.delta_ASR", expect=-0.25),
                 dict(kind="summary", dir=D["cal_ch"], path="by_split.train.by_layer_vs_ds_base.16.delta_ASR", expect=-0.2046),
                 dict(kind="summary", dir=D["cal_ch"], path="by_split.train.by_layer_vs_ds_base.28.delta_ASR", expect=-0.2273)]),
    dict(id="BR-09", phase="P7", status="VERIFIED", effect=None,
         claim="The behaviorally meaningful refusal representation first becomes CAUSALLY MANIPULABLE at ~L13: L9 / all of L0-L12 carry NO validated linear refusal axis in EITHER direction family (incl. the out-of-sample benign re-run); the axis first validates at L13, and only {L13-L20, L24, L28, L29} validate in both families. The L22 rescue is significant in both cohorts.",
         source="reports/P7_REFUSAL_DIRECTION_VALIDATION.md §4c (jobs 720463/721957/722611/724931)",
         dirs=["outputs/refval_clearharm_20260806_054117_722611", D["p7_full"], "outputs/refval_clearharm_20260806_111105_724931"],
         script="scripts/validate_refusal_directions.py",
         recompute="python scripts/validate_all_outputs.py outputs/refval_clearharm_20260806_054117_722611",
         note="REFRAMED + RESOLVED 2026-08-06. The OLD phrasing ('L9 is ns, so the decision is read mid-late') was UNINFORMATIVE: L0-L12 carry no valid refusal axis "
              "in either family (existing.invalid_layers and clearharm.invalid_layers both include 0-11), so 'L9 ns' was injecting a direction that does not control "
              "refusal -- it should do nothing regardless of depth. The supportable, positive statement is the ONSET of causal manipulability at L13, drawn identically "
              "by two independently-built direction families. Evidence: full-32 validation 722611 (existing valid_layers start at 13, n_valid 12; clearharm valid_layers "
              "start at 13, n_valid 15), the ablate/bidirectional runs 720463/721957, and the out-of-sample benign re-run 724931 (L9 invalid in both families on the "
              "benign population too). CAVEAT that must travel: L22 validates in the clearharm refit only under the harmless population; anchor depth statements on "
              "L16/L18, which validate in both families on all three populations tested.",
         checks=[dict(kind="json_path", file=os.path.join("outputs/refval_clearharm_20260806_054117_722611", "summary.json"), path=["by_family","existing","n_valid"], expect=12),
                 dict(kind="json_path", file=os.path.join("outputs/refval_clearharm_20260806_054117_722611", "summary.json"), path=["by_family","clearharm","n_valid"], expect=15),
                 dict(kind="json_path", file=os.path.join("outputs/refval_clearharm_20260806_054117_722611", "summary.json"), path=["by_family","existing","best_layer"], expect=15)]),
    dict(id="BR-10", phase="P7", status="VERIFIED",
         claim="At DSVALN=20 on the headline layers, L9 FAILS BOTH validation arms in BOTH direction families "
               "(ablate_spec -0.050/-0.100; induce_spec +0.000/+0.000 against a full +1.000 headroom), while L16 and "
               "L18 validate strongly in both (induce_spec +1.000/+1.000 and +0.900/+0.800). L22 validates in the "
               "ClearHarm refit only: the shipped `existing` L22 direction passes ablate (+0.250) but induces NOTHING.",
         source="reports/P7_REFUSAL_DIRECTION_VALIDATION.md §4b (job 721957)", dirs=[D["p7_smoke"], D["p7_full"]],
         script="scripts/validate_refusal_directions.py", recompute="python scripts/validate_refusal_directions.py --run-dir " + D["p7_full"],
         note="RESOLVED 2026-08-06 by jobs 720463 (ablate, 840 rows) and 721957 (corrected bidirectional, 630 rows). The old SMOKE (DSVALN=3) made every validity "
              "flag a one-item decision and is superseded. L9 is the ONLY layer invalid in both families and it fails BOTH arms -- not merely unnecessary for refusal "
              "but insufficient to produce it. CAVEAT THAT MUST TRAVEL WITH THE DEPTH CLAIM: `existing` L22 induces +0.000, so the published \'L22 significant\' result "
              "rests on a direction validated in only one of two families; anchor depth statements on L16/L18. NOTE the induce arm of 720463 is DEFECTIVE (it ran on "
              "`neutral`, a disguised-harmful population refusing at 0.750, capping induce_gain at +0.25); cite 721957. NOT YET COVERED: L21 (RP-01) and L30 (TR-01) "
              "are not in the headline set; job 722611 runs the full 32 layers. "
              "SECOND GAP -- CLOSED 2026-08-06: both `validate_all_outputs.py` and `validate_experiment_coverage.py` now recognize the `refval` schema. Every completed "
              "refval dir reconciles: 1702 summary values recomputed from raw.jsonl, 0 mismatched. Negative-controlled (a corrupted rate, a corrupted roll-up and a "
              "flipped verdict are each caught), and the recomputer distinguishes `both_gains_positive` (raw gains only) from `valid` (gains AND specificities); "
              "conflating the two produced 4 spurious summary!=raw FAILs on 720463 before it was fixed. A fit_split==eval_split guard was added at the same time.",
         checks=[dict(kind="json_path", file=os.path.join(D["p7_smoke"], "summary.json"), path="by_family.existing.n_valid", expect=15),
                 dict(kind="json_path", file=os.path.join(D["p7_smoke"], "summary.json"), path="by_family.clearharm.n_valid", expect=13)]),
    dict(id="P7-D1", phase="P7", status="VERIFIED",
         claim="The per-layer refusal-direction verdicts are POPULATION-DEPENDENT: on the only induce population out-of-sample for BOTH direction "
               "families (the v3 benign condition), L16/L18/L21/L22/L30 ALL validate in BOTH families while L9 fails in both. The earlier "
               "one-family-only verdicts at L21/L22/L30 were artifacts of scoring `existing` on its own fit set.",
         source="reports/P7_REFUSAL_DIRECTION_VALIDATION.md (D1 resolution)", dirs=['outputs/refval_clearharm_20260806_111105_724931'],
         script="scripts/validate_refusal_directions.py --induce-eval benign",
         recompute="python scripts/validate_all_outputs.py outputs/refval_clearharm_20260806_111105_724931",
         note="RESOLVED 2026-08-06 by job 724931 (--induce-eval benign, the v3 benign condition, which is out-of-sample for BOTH direction families and so is the only fair comparison). On that population L21, L22 and L30 ALL validate in BOTH families; the earlier one-family verdicts came from the harmless population, where `existing` was scored IN-SAMPLE (defect D1). The splits there also went in OPPOSITE directions (L21 existing-only, L22/L30 clearharm-only), the signature of an artifact rather than a systematic family difference. L9 remains invalid in BOTH families on BOTH populations. CAVEAT: the v3 benign population is NOT a clean floor -- it refuses at 0.450, so induce headroom is 0.550, not the 1.000 "
              "the harmless set gave; benign-based induce gains are NOT comparable to harmless-based ones and must not be pooled. n=20 per cell, so one "
              "induce item = 0.05. What is robust is the CONTRAST: L9 fails on all three populations tested (neutral, harmless, benign) while L16/L18 "
              "pass on all of them.",
         checks=[dict(kind="json_path", file=os.path.join('outputs/refval_clearharm_20260806_111105_724931', "summary.json"), path=["by_family","existing","n_valid"], expect=5),
                 dict(kind="json_path", file=os.path.join('outputs/refval_clearharm_20260806_111105_724931', "summary.json"), path=["by_family","clearharm","n_valid"], expect=5)]),
    dict(id="P4B-1", phase="P4b", status="VERIFIED",
         claim="Per-head z-necessity at the DEMO positions is distributed and small (all confirmed effects <=0.014): no single head bottlenecks concept-reading. Only L13H18 and L14H13 (L13-14 carry band) are Holm-significant positive-necessity on BOTH dev and heldout AND robust to the clean-subset sensitivity check; head-level analogue of P3's distributed retrieval.",
         source="reports/PHASE4B_HEAD_Z_NECESSITY_DEMO.md", dirs=['outputs/phase5_headz_clearharm_demo_20260806_184037_728710', 'outputs/phase5_headz_clearharm_demo_20260806_184037_728711'],
         script="scripts/phase5_head_zpatch.py --positions demo",
         recompute="python scripts/phase5_analyze.py outputs/phase5_headz_clearharm_demo_20260806_184037_728710 outputs/phase5_headz_clearharm_demo_20260806_184037_728711 --expect-cells 1024",
         note='Pooled 1024-cell Holm family (--expect-cells 1024 enforced), Wilcoxon per split, self-swap=0.00e+00 (locality), not underpowered. Full n=44/41 confirms {L4H16,L10H2,L13H18,L14H13}; clean-subset n=37/36 confirms {L8H11,L13H18,L14H13}; robust intersection = {L13H18,L14H13}. Effects Holm-sig because CONSISTENT across items, not large. LIMITATION: trailing-align imperfection on 5/86 demo-count-mismatched items (LOW-MEDIUM, verified), controlled by the clean subset. Per-shard summary.json is 2x too lenient (512-cell) and must NOT be quoted -- only the pooled path.'),
    dict(id="P7-32", phase="P7", status="VERIFIED",
         claim="Across all 32 layers, only 11 refusal directions validate bidirectionally in BOTH families (L13-L20, L24, L28, L29). "
               "L0-L12 FAIL in both without exception; L13-L20 PASS in both without exception. Per family: existing 12/32, clearharm 15/32.",
         source="reports/P7_REFUSAL_DIRECTION_VALIDATION.md §4c", dirs=["outputs/refval_clearharm_20260806_054117_722611"],
         script="scripts/validate_refusal_directions.py",
         recompute="python scripts/validate_all_outputs.py outputs/refval_clearharm_20260806_054117_722611",
         note="The contiguity is what makes this credible: two independently-built direction families draw the SAME boundary at L13. "
              "Machine-reconciled: 1348 summary values recomputed from raw.jsonl, 0 mismatched, 64 cells, 0 dups, empty_max 0.0. "
              "CONSEQUENCE: of the layers carrying published claims, only L18 is in the cross-validated set -- L21 (RP-01), L22 (BR-08) and L30 (TR-01) each validate "
              "in exactly one family, and L8/L9 (BR-11's onset) validate in neither. CAVEAT: induce n=10 (the held-out harmless half), so a +0.100 induce specificity "
              "is a SINGLE item; L22 and L30 clear the bar on clearharm by exactly that margin and must not be called strongly validated.",
         checks=[dict(kind="json_path", file=os.path.join("outputs/refval_clearharm_20260806_054117_722611", "summary.json"), path="by_family.existing.n_valid", expect=12),
                 dict(kind="json_path", file=os.path.join("outputs/refval_clearharm_20260806_054117_722611", "summary.json"), path="by_family.clearharm.n_valid", expect=15),
                 dict(kind="json_path", file=os.path.join("outputs/refval_clearharm_20260806_054117_722611", "summary.json"), path="by_family.clearharm.best_layer", expect=18)]),
    dict(id="BR-11", phase="BEHAV-REFUSAL", status="UNDERPOWERED",
         abstract_block="The ONSET half of this claim is not supportable: it places refusal suppression at hs9 (~L8), but L0-L12 have NO valid refusal axis in EITHER family. A projection onto a direction that neither ablates nor induces refusal is not a refusal measurement. The depth-growth half (L13+) stands.",
         claim="Representational signature: Doublespeak's refusal-axis projection at the decision token sits far below direct-harmful and at/below the benign level, with suppression onsetting at hs9 (~L8, the concept-write band) and growing monotonically through depth; the norm-matched random direction shows zero condition gap.",
         source="PHASE_BEHAV_REFUSAL.md §'Representational signature'", dirs=[D["refproj_ch"], D["refproj_cu"], D["p7_full"]],
         script="scripts/phase_refusal_projection.py", recompute="python scripts/phase_refusal_projection.py --run-dir " + D["refproj_ch"],
         note="PENDING on the same per-layer direction validation. Separately: this harness tokenizes with add_special_tokens=True on an already-templated string, so "
              "it runs a DOUBLE-BOS 38-token forward. Checked and it does not bite -- the readout is at the LAST position either way, and the extra BOS is common-mode "
              "across direct/ds/neutral so it cancels in the paired delta."),
    dict(id="BR-12", phase="PHASE2_DIRECTIONS", status="VERIFIED",
         claim="The concept axis is orthogonal to the refusal axis: mean cos(concept, refusal) = 0.012 / 0.061 and max |cos| <= 0.153 over all 32 layers, both cohorts.",
         source="PHASE2_DIRECTIONS.md; FINAL_CAUSAL_CIRCUIT_REPORT.md Q9(a)", dirs=["outputs/unified_directions"],
         script="scripts/build_unified_directions.py", recompute="python scripts/build_unified_directions.py",
         note="RECOMPUTED 2026-08-06 from the committed outputs/unified_directions/{clearharm,curated}.json per-layer cosines: clearharm mean 0.012, max|cos| 0.078; "
              "curated mean 0.061, max|cos| 0.153 -- both match the shipped summary exactly and satisfy the claim. CAVEAT (cross-convention, unchanged): the refusal "
              "vectors were built through `ds_common.forward_hidden_states` (double BOS, 38 tokens) while the concept vectors come from `pair_common` / "
              "`48_attribution_patching` (single BOS, 37 tokens), so the cosine compares vectors from slightly different contexts. One extra BOS is a small perturbation "
              "and the claim has a wide margin, so this is a methods caveat, not an invalidation -- but it has never been MEASURED both ways.",
         checks=[dict(kind="json_path", file="outputs/unified_directions/clearharm.json", path=["summary","mean_cos_concept_refusal"], expect=0.012),
                 dict(kind="json_path", file="outputs/unified_directions/clearharm.json", path=["summary","max_abs_cos_concept_refusal"], expect=0.0777),
                 dict(kind="json_path", file="outputs/unified_directions/curated.json", path=["summary","max_abs_cos_concept_refusal"], expect=0.1527)])

    ,
    # ============================== BEHAV-CARRY / BEHAV-WRITE (prior sprint) ===================
    dict(id="BC-01", abstract_block='NON-SIGNIFICANT (McNemar p=0.289/0.375), does not replicate on curated, and is not distinguishable from its count-matched random-head control (P100-02/03).', phase="BEHAV-CARRY", status="VERIFIED", effect=0.0909,
         claim="Carry-head (L14-21, 9 heads) ablation through generation moves ASR by +0.091 (clearharm train, McNemar p=0.289) and +0.071 (test, p=0.375); curated reverses (-0.100) and is null on test.",
         source="PHASE_BEHAV_CARRY.md §'Result'", dirs=[D["bc_ch"], D["bc_cu"]],
         script="scripts/phase_behav_carry.py", recompute=BCA.format(d=D["bc_ch"]),
         checks=[dict(kind="summary", dir=D["bc_ch"], path="by_split.train.delta_necessity_carry", expect=0.0909),
                 dict(kind="summary", dir=D["bc_ch"], path="by_split.test.delta_necessity_carry", expect=0.0714),
                 dict(kind="summary", dir=D["bc_ch"], path="by_split.train.delta_rand_ctrl", expect=0.0227)]),
    dict(id="BC-02", phase="BEHAV-CARRY", status="UNDERPOWERED",
         claim="'The L14-21 carry heads are behaviorally NULL / the concept circuit is behaviorally inert.'",
         source="PHASE_BEHAV_CARRY.md §'Interpretation'; FINAL_CAUSAL_CIRCUIT_REPORT.md headline", dirs=[D["bc_ch"], D["bc_cu"]],
         script="scripts/phase_behav_carry.py", recompute="python scripts/analyze_graded_reanalysis.py",
         note="n=44/42 per split, post-hoc power 0.135 / 0.086; n ~ 275 needed at 80% power for dASR = 0.09. The clearharm test cell also sits AT the exact test's "
              "granularity floor (0.0625), i.e. it could not have rejected under any data. Say 'no effect detectable at this n', not 'inert'."),
    dict(id="BW-01", phase="BEHAV-WRITE", status="SUPERSEDED", effect=-0.0227,
         claim="The prefill-only L8-11 write ablation is a clean null (all dASR in [-0.023, +0.067], every McNemar p >= 0.69, all CIs include 0).",
         source="PHASE_BEHAV_WRITE.md §'Result'", dirs=[D["bw_ch"], D["bw_cu"], D["p10_ds"]],
         script="scripts/phase_behav_write.py", recompute=BCA.format(d=D["bw_ch"]),
         note="SUPERSEDED by P10 -- this arm fired during PREFILL ONLY, so the generation phase was never tested. `ComponentOutSwap`'s position guard drops every position when seq==1, so this arm fired during PREFILL ONLY and the generation phase "
              "was never tested -- the null was UNTESTED for decode, not corrupted (token 0 is always <|begin_of_text|> under the Llama template, so a codeword index "
              "can never be 0 and the decode phase was a clean no-op). P10 re-ran it decode-safe; see P10-01..07.",
         checks=[dict(kind="summary", dir=D["bw_ch"], path="by_split.train.delta_necessity_write", expect=-0.0227),
                 dict(kind="summary", dir=D["bw_ch"], path="by_split.test.delta_necessity_write", expect=0.0)]),
    dict(id="WR-01", abstract_block='A positive control confirming the ablation fired; the finding it supports (WR-02) is PENDING.', phase="WRITE x REFUSAL", status="VERIFIED",
         claim="Positive control for the write x refusal interaction study fires: ablating the L8-11 write drops the FC p_concept readout in every cell (clearharm .884->.799 / .858->.817; curated .811->.751 / .690->.457, CIs exclude 0).",
         source="PHASE_WRITE_REFUSAL_INTX.md §'Result'", dirs=[D["wrx_ch"], D["wrx_cu"]], script="scripts/phase_write_refusal_interaction.py",
         recompute="python scripts/validate_all_outputs.py " + D["wrx_ch"],
         note="The source report names NO run dir; the two dirs above were traced through the harness's naming convention (`write_refusal_intx_<cohort>_<ts>_<jid>`), not through the report.",
         checks=[dict(kind="summary", dir=D["wrx_ch"], path="by_split.train.pconcept_control.ds", expect=0.8844),
                 dict(kind="summary", dir=D["wrx_ch"], path="by_split.train.pconcept_control.writeabl", expect=0.7988),
                 dict(kind="summary", dir=D["wrx_cu"], path="by_split.test.pconcept_control.writeabl", expect=0.457, tol=1e-3)]),
    dict(id="WR-02", phase="WRITE x REFUSAL", status="VERIFIED",
         claim="The concept-write and the refusal-suppression are CAUSALLY INDEPENDENT: restricted to the P7-validated layers {L13-L20,24,28,29}, frac_of_direct_gap_restored is <=|0.05| in every cell (<=|0.025| on clearharm), i.e. write-ablation leaves DS's refusal suppression unmoved WHERE THE REFUSAL AXIS IS REAL.",
         source="PHASE_WRITE_REFUSAL_INTX.md §'Result'", dirs=[D["wrx_ch"], D["wrx_cu"], D["p7_full"]], script="scripts/phase_write_refusal_interaction.py",
         recompute="python scripts/validate_all_outputs.py " + D["wrx_ch"],
         note="RESOLVED + STRENGTHENED 2026-08-06. The original 'every layer' framing was blocked because L0-L12 carry no valid refusal axis (P7); restricting the readout "
              "to the P7-validated layers makes the independence claim rest only on layers where the projection is a real refusal measurement -- and it holds there with "
              "room to spare. Recomputed from committed rows (328 summary values, 0 mismatched): max|frac_of_direct_gap_restored| over validated layers = 0.023/0.025 "
              "(clearharm train/test) and 0.050/0.019 (curated train/test). This harness uses SINGLE-BOS tokenization (cleaner than the original projection harness). "
              "It is the mechanistic reason offered for why the concept circuit is behaviorally epiphenomenal, so it carries real weight in the paper's argument.",
         checks=[dict(kind="summary", dir=D["wrx_ch"], path="by_split.train.per_layer.18.frac_of_direct_gap_restored", expect=0.007),
                 dict(kind="summary", dir=D["wrx_ch"], path="by_split.test.per_layer.16.frac_of_direct_gap_restored", expect=0.025),
                 dict(kind="summary", dir=D["wrx_cu"], path="by_split.train.per_layer.18.frac_of_direct_gap_restored", expect=-0.05)]),

    # ============================== item-level rep -> behavior =================================
    dict(id="RP-01", abstract_block='RESOLVED -- L21 validates in BOTH families on the out-of-sample benign population (job 724931). Kept blocked only because an abstract should still name the readout layer explicitly.', phase="REP->BEHAV", status="VERIFIED", effect=None,
         claim="Item level: a Doublespeak prompt's refusal-axis projection at the decision token classifies its jailbreak outcome at AUC 0.874 on clearharm (n=86, 32 malicious), Mann-Whitney p = 3.8e-9, point-biserial r = -0.584.",
         source="REP_PREDICTS_BEHAVIOR.md §'Result'", dirs=[D["refproj_ch"], D["br_ch"], D["p7_full"]],
         script="scripts/analyze_rep_predicts_behavior.py", recompute="python scripts/analyze_rep_predicts_behavior.py",
         note="Re-run and reproduced exactly this sprint (AUC 0.874, p=3.82e-09, r=-0.584). Read at decoder L21 / hs22, which the P7 smoke marks VALID in the "
              "`existing` family -- but the full validation (720463) has not landed, and the projection was computed in the double-BOS forward."),
    dict(id="RP-02", abstract_block='A NULL (AUC 0.42, p=0.79). It is informative as a contrast to RP-01, which is itself blocked.', phase="REP->BEHAV", status="VERIFIED",
         claim="curated shows NO item-level link (AUC 0.42, p = 0.79) because its DS refusal suppression is uniform -- which isolates concept-DILUTION as the second source of partial ASR.",
         source="REP_PREDICTS_BEHAVIOR.md §'Result'", dirs=[D["refproj_cu"], D["br_cu"]],
         script="scripts/analyze_rep_predicts_behavior.py", recompute="python scripts/analyze_rep_predicts_behavior.py"),
    dict(id="RP-03", phase="REP->BEHAV", status="VERIFIED",
         claim="The AUC is not a layer cherry-pick: single-feature AUC is stable 0.844-0.884 across decoder L17-L31, and Holm-significant at 20 of 32 layers -- "
               "including ALL 11 layers P7 validated in both direction families.",
         source="REP_PREDICTS_BEHAVIOR.md §'Robustness (audit)'; recomputed into outputs/rep_predicts_behavior_sweep.json",
         dirs=[D["refproj_ch"], D["br_ch"]],
         script="scripts/analyze_rep_predicts_behavior.py --sweep",
         recompute="python scripts/analyze_rep_predicts_behavior.py --sweep",
         note="WAS UNVERIFIED (the shipped script emitted only the single-layer result). CLOSED 2026-08-06 by adding --sweep, which recomputes every layer from the "
               "COMMITTED refproj rows -- no GPU, no new data. The stability half reproduces exactly: L17-L31 span 0.844-0.884, inside the quoted 0.84-0.89. "
               "INDEXING: refproj keys are hidden_states rows 1..32 and hs h == decoder layer h-1, so the historical 'L21' readout is hs22. "
               "THE CV HALF DOES NOT REPRODUCE: the quoted '5-fold CV AUC = 0.887 +- 0.106' is not recoverable because the original fold assignment was never "
               "recorded. A deterministic stratified 5-fold (seed 0) gives 0.869 +- 0.055 at L21. Cite that, not the original. Note also that CV is near-meaningless "
               "here -- the 'classifier' is one raw feature with no fitted parameters, so CV measures subsample stability, not generalization.",
         checks=[dict(kind="json_path", file="outputs/rep_predicts_behavior_sweep.json",
                      path=["cohorts", "clearharm", "n_holm_sig_p7_valid"], expect=11),
                 dict(kind="json_path", file="outputs/rep_predicts_behavior_sweep.json",
                      path=["cohorts", "clearharm", "best_layer_p7_valid", "auc"], expect=0.8883),
                 dict(kind="json_path", file="outputs/rep_predicts_behavior_sweep.json",
                      path=["cohorts", "curated", "n_holm_sig"], expect=0)]),
    dict(id="RP-04", phase="REP->BEHAV", status="VERIFIED",
         claim="The rep->behavior readout does NOT depend on the one layer whose axis is family-specific: all 11 P7-both-families layers are "
               "Holm-significant on clearharm (AUC 0.773 at L13 to 0.888 at L16), so the readout can be re-anchored on a both-families axis "
               "(L16 or L18) at no measurable cost.",
         source="outputs/rep_predicts_behavior_sweep.json + P7 §4c", dirs=[D["refproj_ch"], D["br_ch"]],
         script="scripts/analyze_rep_predicts_behavior.py --sweep",
         recompute="python scripts/analyze_rep_predicts_behavior.py --sweep",
         note="CORRECTED 2026-08-06 after self-review. The FIRST version of this row claimed L16's 0.888 was 'HIGHER' than L21's 0.874 and that the result "
              "'got stronger'. That was wrong on three counts and is withdrawn: (1) SELECTION -- 0.888 is the argmax over 11 correlated layers, and under H0 "
              "the expected max of 11 correlated estimates exceeds any fixed one, so 'higher' is what selection manufactures; (2) NO PAIRED TEST -- the two AUCs "
              "come from the SAME 86 items on adjacent, strongly correlated residual layers; (3) the gap is inside the script's own measured noise (4 adjacent "
              "layers span 0.007; the 5-fold sd at L21 is 0.055). Now measured properly with a paired ITEM-bootstrap that recomputes BOTH AUCs on each resample "
              "(AUC is not a mean, so stats.paired_bootstrap_ci does not apply): dAUC(L16-L21) = +0.0139, 95% CI [-0.0148, +0.0446], STRADDLES ZERO. "
              "The supportable claim is 'at least as good as, and validated in both families' -- which is still exactly what is needed to retire RP-01's caveat. "
              "TERMINOLOGY: 'cross-validated' was being used for two different things; in this project it means VALIDATED IN BOTH DIRECTION FAMILIES, not k-fold CV. "
              "There is no cross-validated 0.888 -- the 5-fold runs at one layer only.",
         checks=[dict(kind="json_path", file="outputs/rep_predicts_behavior_sweep.json",
                      path=["cohorts", "clearharm", "best_layer_p7_valid", "decoder_layer"], expect=16),
                 dict(kind="json_path", file="outputs/rep_predicts_behavior_sweep.json",
                      path=["cohorts", "clearharm", "delta_auc_best_vs_reference", "straddles_zero"], expect=True)]),
    dict(id="TR-01", phase="TRAJECTORY", status="VERIFIED",
         claim="The refusal outcome is set at the DECISION POINT: DS-refused and DS-jailbreak trajectories are separated at generated token 0 (projection 9.1 vs -2.1 at L30) and never cross, falsifying mid-generation re-engagement.",
         source="PHASE_REFUSAL_TRAJECTORY.md §'Result'", dirs=[D["p7_full"]], script="scripts/phase_refusal_trajectory.py",
         recompute="python scripts/phase_refusal_trajectory.py",
         note="AT RISK for the same reason as BR-09: the readout layer is **L30, which the P7 smoke marks INVALID** in the `existing` direction family. If the L30 "
              "direction does not control refusal, the trajectory separation is a projection onto an unvalidated axis. The qualitative claim may well survive at a "
              "validated layer (L18/L22) -- but it must be re-read there. The source report names no run dir."),
    dict(id="TR-02", abstract_block='A cohort-specific observation that supports the two-source partial-ASR reading; body, not abstract.', phase="TRAJECTORY", status="VERIFIED",
         claim="curated's DS refusal rate is exactly 0.000 -- zero of its generations refuse -- yet curated ASR is only ~0.10, isolating concept-dilution as a refusal-independent limit on the attack.",
         source="PHASE_REFUSAL_TRAJECTORY.md §'Result'", dirs=[D["br_cu"]], script="scripts/phase_refusal_trajectory.py",
         recompute=BCA.format(d=D["br_cu"]),
         checks=[dict(kind="summary", dir=D["br_cu"], path="by_split.train.refusal_rate.ds_base", expect=0.0),
                 dict(kind="summary", dir=D["br_cu"], path="by_split.test.refusal_rate.ds_base", expect=0.0)])

    ,
    # ============================== prior-sprint synthesis (FINAL report) ======================
    dict(id="FIN-01", phase="Phase 2", status="VERIFIED",
         claim="Behavioral grounding: on the locked ClearHarm split, Doublespeak malicious-rate 0.349 vs direct 0.116 (3.0x); curated neutral floor 0.039.",
         source="FINAL_CAUSAL_CIRCUIT_REPORT.md §'Behavioral grounding'; PHASE2_BEHAVIORAL.md", dirs=[D["p21_ch"], D["p21_cu"]],
         script="scripts/14_behavioral_eval.py", recompute="python scripts/audit_phase21_baseline.py",
         note="Same artifacts as P1-02, audited SAFE. This is Gate 1."),
    dict(id="FIN-02", phase="Phases 3-9", status="SUPERSEDED",
         claim="The circuit is 'demonstration-codeword K/V retrieval (L8-11) + L9 MLP write AT THE DEMONSTRATIONS -> L14-21 carry heads -> L30-31 proximal output -> logit'.",
         source="FINAL_CAUSAL_CIRCUIT_REPORT.md §'The circuit'", dirs=[D["p2_ch_all"], D["p2_cu_all"], D["p2_v2_all"]],
         script="scripts/phase6_mlp_causal.py", recompute=P6A.format(d=D["p2_ch_all"]),
         note="The DEMO-ONLY framing is superseded by P2: the write operates over EVERY codeword occurrence in context, and the demo-only measurement understates it. "
              "The layer structure itself is unchanged. FINAL_CAUSAL_CIRCUIT_REPORT.md and PHASE6_MLP.md both still carry the narrow framing and need editing."),
    dict(id="FIN-03", phase="Phase 7c", status="VERIFIED", effect=None,
         claim="The L14-21 carry HEAD-SET is partially sufficient for the concept readout: installing the DS carry-head z into a benign prompt raises p_concept to 0.16-0.47 (20-53% of the full DS reading), significant and specific in all 4 cells.",
         source="FINAL_CAUSAL_CIRCUIT_REPORT.md Q4; PHASE7_PATH.md", dirs=[D["p7c_ch"], "outputs/phase7c_suffic_curated_20260803_222439_706024"],
         script="scripts/phase7c_sufficiency.py", recompute="python scripts/validate_all_outputs.py " + D["p7c_ch"] + " outputs/phase7c_suffic_curated_20260803_222439_706024",
         note="RECOMPUTED 2026-08-06 from both traced dirs (clearharm 706025, curated 706024; 24 summary values, 0 mismatched). mean_S3_carry_install spans all 4 cells: "
              "clearharm 0.434/0.467 (dev/heldout), curated 0.162/0.240 -- i.e. 0.16-0.47, matching the claim. Every cell's sufficiency_raw_ci (S3-S1) and "
              "sufficiency_specific_ci (S3-Srand) excludes 0, so significant AND specific in all 4 cells; self_install_max_dev = 0.0 (locality). PHASE7_PATH.md cites "
              "NO run dir; both dirs were traced by the harness's naming convention. Representational only -- its BEHAVIORAL sufficiency is untested (prior "
              "state-injection was <=0.16).",
         checks=[dict(kind="summary", dir=D["p7c_ch"], path="by_split.heldout.mean_S3_carry_install", expect=0.4674),
                 dict(kind="summary", dir="outputs/phase7c_suffic_curated_20260803_222439_706024", path="by_split.dev.mean_S3_carry_install", expect=0.1617),
                 dict(kind="summary", dir="outputs/phase7c_suffic_curated_20260803_222439_706024", path="by_split.heldout.mean_S3_carry_install", expect=0.2395)]),
    dict(id="FIN-04", phase="Phase 5b", status="WITHDRAWN",
         claim="'The Q/K/V decomposition of the carry heads is a null -- K/V contribute ~0.'",
         source="FINAL_CAUSAL_CIRCUIT_REPORT.md §'Scale-up validation' (Phase 5b)", dirs=["outputs/phase5b_qkv_curated_20260804_013548_707412"],
         script="scripts/phase5b_qkv.py", recompute="python scripts/validate_all_outputs.py outputs/phase5b_qkv_curated_*",
         note="RETRACTED (audit iter-85) -- the ~0 is a POSITIONING ARTIFACT, not inertness. The K/V cells patched only the ANSWER position, but under causal masking K/V are read from EARLIER source positions that were "
              "never touched -- so the ~0 is a POSITIONING ARTIFACT, not inertness. The harness also lacked a positive control and the only run was an n=2 smoke. "
              "A corrected K/V-at-source-positions re-run with a positive control is future work."),
    dict(id="FIN-05", phase="Phase 11 / GCG", status="SUPERSEDED",
         claim="'A mechanism-derived GCG objective does not improve held-out ASR -- it is net-negative (a well-controlled null).'",
         source="FINAL_CAUSAL_CIRCUIT_REPORT.md Q12; GCG_MAC_EVALUATION.md", dirs=[],
         script="scripts/ (GCG harnesses)", recompute="(needs a re-run with objective.repr_in_selection=true)",
         note="SUPERSEDED by the P9.0 bug fix: `_evaluate_candidates` never passed hidden states to `composite_loss`, so the representation/refusal objective entered "
              "only the GRADIENT and NOT candidate selection. EVERY prior 'mechanism-derived GCG fails' statement was made with the objective effectively disabled. "
              "The null must be re-established or withdrawn; it cannot be cited as it stands."),
    dict(id="FIN-06", phase="Phase 5", status="UNDERPOWERED",
         claim="Carry-head necessity head claims (1024-cell head family, Wilcoxon-Holm) on curated heldout.",
         source="FINAL_CAUSAL_CIRCUIT_REPORT.md §'Honest limitations'", dirs=[D["p5_ch"], D["p5_cu"]],
         script="scripts/phase5_head_zpatch.py", recompute="python scripts/phase5_analyze.py <dir>",
         note="curated heldout n=21 is under-powered for a 1024-cell family and returned 0 Holm-significant heads; the v2 bench (116 ex) fixes it (dev 58 / heldout 44 "
              "Holm-sig heads). Head claims rest on the 3 powered cells, which the report does state.")

    ,
    # ============================== cross-cutting artifact / method claims =====================
    dict(id="META-01", artifact='repo-wide: every recognized run dir', abstract_block='Infrastructure/verification claim about the repo, not about the model.', phase="P0", status="VERIFIED",
         claim="Every behavioral summary number recomputes from its raw rows: 14,482 summary values recomputed across the recognized run dirs, 0 mismatches.",
         source="CONTINUATION_PROGRESS.md 'Data integrity' + 'Validator schema coverage'", dirs=[],
         script="scripts/validate_all_outputs.py", recompute="python scripts/validate_all_outputs.py outputs/*",
         note="This is the guarantee that lets any VERIFIED row above be trusted at all. 6/6 deliberate negative controls fire."),
    dict(id="META-02", artifact='repo-wide: outputs/', abstract_block='A scope limitation of the validator. Methods/limitations.', phase="P0", status="VERIFIED",
         claim="Validator SCOPE, stated honestly: of 397 output dirs only 96 carry `raw.jsonl`; the other 275 are SKIP-legacy (nothing to recompute against).",
         source="CONTINUATION_PROGRESS.md 'Validator scope'", dirs=[],
         script="scripts/validate_all_outputs.py", recompute="python scripts/validate_all_outputs.py outputs/*",
         note="A 'VERIFIED' status is only as strong as the raw rows being on disk. Legacy dirs cannot be re-derived at all."),
    dict(id="META-03", phase="P0", status="VERIFIED", abstract_block='A per-dir data defect (the sole summary!=raw mismatch in the corpus). Methods/limitations.',
         claim="Phase 9's `monotone_decreasing` dose-response flag is STALE ON DISK: in 2 of the 5 phase9_dose dirs the committed summary flag disagrees with its own rows under the current [0,1] alpha definition (summary=False, recomputed=True); it is the only summary!=raw mismatch anywhere in the cited corpus.",
         source="CONTINUATION_PROGRESS.md 'Validator schema coverage'; PHASE9_DOSE.md", dirs=[D["p9_ch"], D["p9_cu"]],
         script="scripts/phase9_dose.py", recompute="python scripts/validate_all_outputs.py outputs/phase9_dose_*",
         note="CONFIRMED as a data defect (status VERIFIED like META-04/META-05: the DEFECT is what is verified, reproduced live this audit). "
              "`validate_all_outputs.py` reports "
              "`FAIL: summary!=raw at by_split.heldout.monotone_decreasing: summary=False recomputed=True` on "
              "`phase9_dose_curated_L9_20260803_173754_704861`. The flag was computed under the PRE-AUDIT alpha>1-inclusive definition and disagrees with its own "
              "rows under the current [0,1] definition, in 2 of the 5 `phase9_dose` dirs. **This is the only `summary!=raw` mismatch anywhere in the cited corpus.** "
              "Any dose-monotonicity claim must be recomputed before it is cited. Two further dirs carry a committed summary.json over a 0-row raw.jsonl."),
    dict(id="META-04", abstract_block='A per-dir data defect. Methods/limitations.', phase="P0", status="VERIFIED",
         claim="`phase6_mlpKO_curated_layer_20260803_092718_703457` reports POOLED dev+heldout (n=51 = 30+21) with no `by_split` block -- any number cited from that dir is a pooled number, contrary to the §1.5 split-separation rule.",
         source="CONTINUATION_PROGRESS.md 'Data integrity'", dirs=["outputs/phase6_mlpKO_curated_layer_20260803_092718_703457"],
         script="scripts/phase6_mlp_causal.py", recompute="python scripts/validate_experiment_coverage.py outputs/phase6_mlpKO_curated_layer_20260803_092718_703457"),
    dict(id="META-05", abstract_block='A per-dir data defect. Methods/limitations.', phase="P0", status="VERIFIED",
         claim="The job-708038 aborted twin (`behav_refusal_clearharm_a1.0_20260804_125311_708038`) has no summary.json and only 36 test rows vs 42 in the authoritative twin; it is excluded from every reported number.",
         source="CONTINUATION_PROGRESS.md 'Data integrity'", dirs=[D["br_twin"], D["br_ch"]],
         script="scripts/validate_all_outputs.py", recompute="python scripts/validate_all_outputs.py " + D["br_twin"],
         note="It is retained on purpose: it is the technical replicate that measures the judge-instability envelope (P80-06)."),
    dict(id="META-06", artifact='repo-wide: 369 RUNMETA.json', abstract_block='A provenance defect that was fixed. Methods/limitations.', phase="P0", status="VERIFIED",
         claim="34 SLURM job ids in the reconstructed provenance records were FABRICATED by a regex that matched the timestamp's HHMMSS field; all were deleted and re-written under a distinct `RUNMETA/1-reconstructed` schema tag.",
         source="CONTINUATION_PROGRESS.md 'Review defects fixed'", dirs=[],
         script="scripts/backfill_runmeta.py", recompute="python scripts/audit_artifacts.py",
         note="0 of 369 RUNMETA now carry a job id equal to the dir's HHMMSS. Relevant to this table because job ids are part of every claim's provenance."),
]

# ---------------------------------------------------------------------------------------------
# Mechanical evaluation
# ---------------------------------------------------------------------------------------------


def audit_dir(rel):
    """Existence + §2.1 contract + raw row count for one run dir."""
    p = os.path.join(DC, rel)
    info = {"dir": rel, "exists": os.path.isdir(p), "rows": None, "files": []}
    if not info["exists"]:
        return info
    for f in ("RUNMETA.json", "DONE.json", "summary.json"):
        if os.path.exists(os.path.join(p, f)):
            info["files"].append(f.split(".")[0])
    for cand in ("raw.jsonl", "behavioral_raw.jsonl"):
        fp = os.path.join(p, cand)
        if os.path.exists(fp):
            info["files"].append("raw")
            info["rows"] = sum(1 for line in open(fp) if line.strip())
            break
    return info


def run_validator(dirs):
    """Hand every cited run dir to validate_all_outputs.py and parse its per-dir verdict."""
    verdicts = {}
    existing = [d for d in dirs if os.path.isdir(os.path.join(DC, d))]
    if not existing:
        return verdicts, "no dirs"
    # The validator's JSON goes to a real temp file, never into the repo: this script is only ever
    # allowed to write its own report.
    with tempfile.TemporaryDirectory(prefix="claim_audit_") as td:
        jf = os.path.join(td, "validate.json")
        cmd = [sys.executable, os.path.join(HERE, "validate_all_outputs.py"), *existing, "--quiet", "--json", jf]
        try:
            proc = subprocess.run(cmd, cwd=DC, capture_output=True, text=True, timeout=900)
        except (subprocess.TimeoutExpired, OSError) as exc:
            return verdicts, f"validator not run ({exc})"
        tail = (proc.stdout or "").strip().splitlines()
        summary_line = next((ln for ln in reversed(tail) if "summary values recomputed" in ln), "")
        if os.path.exists(jf):
            try:
                res = _load_json(jf)
                rows = res if isinstance(res, list) else res.get("dirs", res.get("results", []))
                for r in rows:
                    key = os.path.basename(str(r.get("dir", r.get("path", ""))).rstrip("/"))
                    verdicts[key] = {
                        "status": r.get("status", "?"),
                        "checked": r.get("n_checked", r.get("checked")),
                        "mismatched": len(r.get("mismatches", [])),
                        "issues": r.get("issues", []),
                    }
            except (json.JSONDecodeError, AttributeError, TypeError):
                pass
    return verdicts, summary_line


def evaluate(claims, do_validate=True):
    all_dirs = sorted({d for c in claims for d in c.get("dirs", [])})
    dir_info = {d: audit_dir(d) for d in all_dirs}
    verdicts, vsummary = ({}, "skipped") if not do_validate else run_validator(all_dirs)

    for c in claims:
        assert c["status"] in STATUSES, f"{c['id']}: bad status {c['status']}"
        # numeric checks
        results = []
        for spec in c.get("checks", []) or []:
            fn = CHECKERS.get(spec["kind"])
            if fn is None:
                results.append((None, f"unknown check {spec['kind']}"))
                continue
            try:
                results.append(fn(spec))
            except Exception as exc:                                  # noqa: BLE001
                results.append((False, f"{spec['kind']} raised {type(exc).__name__}: {exc}"))
        c["_checks"] = results
        n_run = len([r for r in results if r[0] is not None])
        n_bad = len([r for r in results if r[0] is False])
        c["_check_verdict"] = "n/a" if not n_run else ("CHECK-FAIL" if n_bad else f"{n_run}/{n_run} ok")
        c["_check_detail"] = [d for ok, d in results if ok is False]
        # dirs
        # O3 (bughunt HIGH): "exists" was too weak a contract. A run dir that stalled before writing
        # any data still EXISTS (it has a RUNMETA), so it passed this check and was then reported as
        # "SKIP-legacy" by the validator -- which is not a failure state. The flagship n=242 result was
        # therefore pointing at an empty directory and nobody noticed. A cited dir must contain DATA.
        missing = [d for d in c.get("dirs", []) if not dir_info[d]["exists"]]
        # Precisely: a dir holding NOTHING BUT RUNMETA.json is a run that died before writing data.
        # Do not test for raw.jsonl/summary.json by name -- legitimate artifact dirs use other names
        # (outputs/unified_directions ships .npz; behavioral_split_* ships behavioral_raw.jsonl), and
        # flagging those would be a false positive that trains the reader to ignore this check.
        def _is_empty_run(d):
            full = os.path.join(DC, d)
            try:
                files = [f for f in os.listdir(full) if not f.startswith(".")]
            except OSError:
                return False
            return files == ["RUNMETA.json"]
        empty = [d for d in c.get("dirs", []) if dir_info[d]["exists"] and _is_empty_run(d)]
        c["_empty_dirs"] = empty
        missing = missing + [d + " (EMPTY: no raw.jsonl and no summary.json)" for d in empty]
        c["_missing_dirs"] = missing
        c["_traceable"] = bool(c.get("dirs")) and not missing
        vs = [verdicts.get(os.path.basename(d), {}).get("status") for d in c.get("dirs", []) if d in dir_info]
        c["_validator"] = ",".join(sorted({v for v in vs if v})) or "-"
        # noise floor
        e = c.get("effect")
        c["_floor"] = None if e is None else ("below" if abs(e) < NOISE_FLOOR else ("at" if abs(e) < 1.5 * NOISE_FLOOR else "above"))
    return dir_info, verdicts, vsummary


# ---------------------------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------------------------
BADGE = {"VERIFIED": "✅ VERIFIED", "WITHDRAWN": "🛑 WITHDRAWN", "SUPERSEDED": "♻️ SUPERSEDED",
         "UNDERPOWERED": "⚠️ UNDERPOWERED", "UNVERIFIED": "❓ UNVERIFIED", "PENDING": "⏳ PENDING"}


def first_sentence(text, limit=260):
    """First sentence of a note, for the compact DO-NOT-CITE tables. Splits on '. ' (period + space) so
    a decimal point never truncates the reason -- an earlier version cut 'max cosine is 0.690' to
    'max cosine is 0'."""
    t = (text or "").strip()
    if not t:
        return "see notes"
    cut = t.find(". ")
    out = t if cut < 0 else t[: cut + 1]
    return out if len(out) <= limit else out[: limit - 1].rstrip() + "\u2026"


def esc(text):
    """Markdown table cells cannot contain a bare pipe. Several claims legitimately do
    (|dASR|, max |cos|, |Ihat|), and an unescaped one silently shifts every later column."""
    return str(text).replace("|", "\\|")


def short_dirs(c, dir_info):
    if not c.get("dirs"):
        return f"*(not a run: `{c['artifact']}`)*" if c.get("artifact") else "**⚠ none cited**"
    out = []
    for d in c["dirs"]:
        base = os.path.basename(d)
        info = dir_info[d]
        mark = "" if info["exists"] else " ❌MISSING"
        rows = f" ({info['rows']}r)" if info["rows"] is not None else ""
        out.append(f"`{base}`{rows}{mark}")
    return "<br>".join(out)


def render(claims, dir_info, verdicts, vsummary, do_validate):
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    hist = {}
    for c in claims:
        hist[c["status"]] = hist.get(c["status"], 0) + 1
    L = []
    A = L.append

    A("# CLAIM AUDIT TABLE — every paper-facing claim traced to the run that produced it")
    A("")
    A(f"**Generated by `scripts/build_claim_audit.py` — {now}. Do not hand-edit: edit the `CLAIMS` "
      "registry in that script and re-run.** The claim text, phase, source section and STATUS are "
      "human judgements held in the registry; the run-dir existence, row counts, summary-recompute "
      "verdicts and per-claim numeric checks in the last columns are re-derived from disk on every run.")
    A("")
    A(f"**Claims catalogued: {len(claims)}.**")
    A("")
    A("| status | n | meaning |")
    A("|---|---|---|")
    for s in STATUSES:
        meaning = {
            "VERIFIED": "recomputed from raw this sprint, matches",
            "WITHDRAWN": "actively retracted — must never be cited",
            "SUPERSEDED": "replaced by a later, better measurement",
            "UNDERPOWERED": "the number is right but the design cannot support the inference",
            "UNVERIFIED": "asserted in a report but never recomputed from raw",
            "PENDING": "the producing run is still in flight",
        }[s]
        A(f"| {BADGE[s]} | {hist.get(s, 0)} | {meaning} |")
    A("")
    A("---")
    A("")
    A("## The five corrections this table exists to keep visible")
    A("")
    A("These were established during the continuation sprint and **must not be quietly dropped** from any "
      "downstream document. Each has a row below.")
    A("")
    A("1. **P8.0's \"sub-additive ⇒ shared refusal bottleneck\" is WITHDRAWN** (P80-02). P8.1 showed `Î` "
      "tracks the design's ceiling (Spearman **+0.991**); at the de-saturated **α = 0.25**, "
      "**Î = −0.023, p = 0.86** — no interaction detectable. The sub-additivity is a property of running "
      "the ablation at a saturating dose, not of the mechanism. *Absence of a detectable interaction is "
      "not evidence of independence either.*")
    A("2. **P10.0's graded carry-head effect FAILS its specificity control** (P100-02). The size-matched "
      "random-head arm reaches **53 %** of the carry effect (+0.0392 vs +0.0741) and the direct "
      "`rand − carry` contrast is **+0.0349, p = 0.382**. This is **not** evidence the carry heads matter.")
    A("3. **The concept-write behavioral null SURVIVES the decode-safe re-test (P10) but is UNDERPOWERED** "
      "(P10-07). n = 86; 80 % power needs **n ≈ 275** at ΔASR = 0.09 (**n ≈ 419** at 0.07). Write "
      "*\"no effect detectable at this n\"*, never *\"no effect\"*.")
    A("4. **The per-layer refusal-direction validation has LANDED and reframes the depth claim** (BR-08…BR-11, "
      "TR-01, WR-02, RP-01). Jobs **720463 / 721957 / 722611 / 724931** completed: **L0-L12 (incl. L9) carry NO "
      "valid refusal axis in either family**, the axis first validates at **L13**, and only "
      "**{L13-L20, L24, L28, L29}** validate in both families. So \"L9 ns\" is uninformative and is replaced by "
      "the positive onset-at-L13 statement (BR-09, now VERIFIED); WR-02's independence claim is re-stated on the "
      "validated layers only (also VERIFIED). **L30** (the trajectory readout, TR-01) validates in only one "
      "family — re-read depth/trajectory statements at L16/L18.")
    A("5. **The judge has a measured ~2 pp label-flip floor on BYTE-IDENTICAL text** (P81-01), so any "
      "|ΔASR| below ~2 pp is uninterpretable. Every row below is flagged against it.")
    A("")
    A("**Also newly surfaced by this audit, and not previously recorded anywhere:**")
    A("")
    A("- ~~**The P8.1 report on disk is STALE and self-labelled \"do not cite\"** (P81-04, P81-06). It carries "
      "the n = 78 PROVISIONAL clearharm table, while `outputs/alpha_calibration.json` contains **only the "
      "curated cohort** — the clearharm block is absent entirely. The FINAL n = 86 numbers that withdraw "
      "P8.0 live only in `CONTINUATION_PROGRESS.md` prose. The point estimates recompute exactly from the "
      "completed run dir (done here), but **the p-value and CI exist in no committed artifact.**~~ "
      "**FIXED 2026-08-06, the same day this audit surfaced it.** This was the audit's most valuable find: "
      "the evidence withdrawing P8.0 was prose-only. Job 716014 had in fact completed (86/86 rows, "
      "`DONE.json` + `summary.json`); the analyzer was re-run over **both** cohorts, `alpha_calibration.json` "
      "now carries the clearharm block with `provisional: false`, and the report was re-issued at n = 86. "
      "The regenerated values match the prose exactly — `Ihat` −0.02326, CI [−0.15116, +0.10465], "
      "`perm_p` 0.859743, Spearman +0.991031 — and are now asserted by checks on P81-06. The n = 78 → 86 "
      "refresh did move `I_max` (α=0.25: +0.487 → **+0.4767**; α=1.0: +0.231 → **+0.1860**), but α = 0.25 "
      "remained the sole qualifying dose at every n, so no conclusion depended on the partial file.")
    A("- **`P10_DECODE_SAFE_WRITE.md` §5 mis-cites its own power source** (P10-07): it attributes n ≈ 275 to "
      "ΔASR ≈ 0.07, but P10.0 §5 gives 275 for 0.09 and **419** for 0.07.")
    A("- ~~**`REP_PREDICTS_BEHAVIOR.md`'s robustness paragraph is not reproducible** (RP-03): the shipped "
      "script emits only the single-layer result, so the L17–L32 AUC sweep and the 5-fold CV AUC "
      "0.887 ± 0.106 exist in no committed code path or JSON.~~ **RESOLVED 2026-08-06.** `--sweep` now "
      "recomputes every layer from the committed refproj rows (stability half reproduces: L17–L31 span "
      "0.844–0.884). The withdrawn CV AUC 0.887 ± 0.106 is not recoverable (original folds unrecorded) and "
      "has been struck from REP_PREDICTS_BEHAVIOR.md; a deterministic 5-fold (seed 0) gives 0.869 ± 0.055 "
      "at L21 — cite that, though CV is near-meaningless for a single unfitted feature.")
    A("- **Four paper-facing reports name no run directory at all** — PHASE5_HEADS, PHASE7_PATH, "
      "PHASE9_DOSE, CAUSAL_OBJECTIVE (and PHASE_WRITE_REFUSAL_INTX). Their dirs were recovered here through "
      "harness naming conventions, not through the reports.")
    A("- **The P7 `refval` row schema is unknown to `validate_all_outputs.py`**, so that dir FAILs "
      "reconciliation and no P7 number has ever been machine-recomputed from its rows (BR-10).")
    A("")
    A("---")
    A("")
    A("## The judge noise floor governs this whole table")
    A("")
    A(f"The StrongREJECT judge flips **~2 pp of labels on BYTE-IDENTICAL text** (P8.1: `alpha=0` is an exact "
      "IEEE no-op, generations sha256-verified identical, 1/51 curated and 1/86 clearharm labels still "
      "flipped, max |Δscore| = 1.00). **Any |ΔASR| below ≈2 pp is uninterpretable**, and `Î` — a contrast of "
      "four judged arms — has a floor of *at least* that. Every row below whose effect is at or under the "
      "floor is marked in the **floor** column:")
    A("")
    A("- `‡ BELOW` — |effect| < 2 pp: **do not cite as an effect at all**")
    A("- `† AT` — 2 pp ≤ |effect| < 3 pp: at the floor, cite only with the floor stated alongside")
    A("- `above` — comfortably above the floor")
    A("")
    A("---")
    A("")
    A("## The table")
    A("")
    A("| # | claim | phase | source (report §) | run dir(s) | producing script | recomputation command | status | effect vs floor | mechanical check |")
    A("|---|---|---|---|---|---|---|---|---|---|")
    for c in claims:
        floor = {"below": "‡ BELOW", "at": "† AT", "above": "above", None: "—"}[c["_floor"]]
        eff = "" if c.get("effect") is None else f"{c['effect']:+.4g} "
        chk = c["_check_verdict"]
        if c["_missing_dirs"]:
            chk += " · ❌dir missing"
        if do_validate and c["_validator"] not in ("-", ""):
            chk += f" · val:{c['_validator']}"
        A(f"| {c['id']} | {esc(c['claim'])} | {c['phase']} | {esc(c['source'])} | {short_dirs(c, dir_info)} | "
          f"`{esc(c['script'])}` | `{esc(c['recompute'])}` | {BADGE[c['status']]} | {eff}{floor} | {esc(chk)} |")
    A("")
    A("### Notes, corrections and caveats (per claim)")
    A("")
    for c in claims:
        if c.get("note"):
            A(f"- **{c['id']}** — {c['note']}")   # prose, not a table cell -- pipes are safe here
    A("")
    A("---")
    A("")

    # ------- abstract eligible -------
    mech = [c for c in claims if c["status"] == "VERIFIED" and c["_floor"] in (None, "above")
            and c["_check_verdict"] != "CHECK-FAIL"]
    elig = [c for c in mech if not c.get("abstract_block")]
    blocked = [c for c in mech if c.get("abstract_block")]
    A("## ABSTRACT-ELIGIBLE — the only claims a paper abstract may carry")
    A("")
    A("Two gates, both must pass. **Gate 1 (mechanical, re-derived every run):** status VERIFIED *and* "
      "(the effect is above the ~2 pp judge noise floor **or** the claim is not a ΔASR effect at all) *and* "
      "no numeric check failed. **Gate 2 (editorial, `abstract_block` in the registry):** the claim is a "
      "*finding*, not a control arm, a calibration constant, a non-significant null, or a number whose "
      "interpretation has been retracted. Gate 1 alone lets a non-significant null through with a large "
      "point estimate, which is exactly the error this table exists to prevent — so Gate 2 is listed "
      "explicitly below rather than applied silently.")
    A("")
    A(f"**{len(elig)} of {len(claims)} claims are abstract-eligible.**")
    A("")
    A("| # | claim | why it holds |")
    A("|---|---|---|")
    for c in elig:
        why = f"recomputed from `{os.path.basename(c['dirs'][0])}`" if c.get("dirs") else "recomputed from committed artifacts"
        if c.get("effect") is not None:
            why += f"; effect {c['effect']:+.3f} = {abs(c['effect'])/NOISE_FLOOR:.0f}× the noise floor"
        A(f"| {c['id']} | {esc(c['claim'])} | {esc(why)} |")
    A("")
    A("### Passed Gate 1 but blocked at Gate 2 — verified numbers that are NOT abstract material")
    A("")
    A("| # | claim | why it is blocked |")
    A("|---|---|---|")
    for c in blocked:
        A(f"| {c['id']} | {esc(c['claim'][:150])} | {esc(c['abstract_block'])} |")
    A("")
    A("### Sentences that are safe to write from the above")
    A("")
    A("1. *Ablating a single refusal direction is a stronger jailbreak than Doublespeak itself* "
      "(ΔASR +0.43–0.48, every split p ≤ 0.004; a norm-matched random direction does nothing), *and "
      "re-injecting that direction into Doublespeak drives ASR to 0.000, dose-dependently and "
      "axis-specifically.* — BR-01, BR-02, BR-03, BR-04, BR-05. **This is the strongest result in the "
      "project**: 22× the noise floor, both cohorts, both splits, necessity and sufficiency closed.")
    A("2. *The L9 concept write operates over every codeword occurrence in context, not only the "
      "demonstrations: L9 is the argmax and Holm-significant on all three benches under all-occurrence "
      "patching, against a count-matched control.* — P2-01…P2-05. **Quote the per-cell effect sizes; "
      "do NOT write \"doubles\"** — the ratio compares two independently-estimated effects with no CI on "
      "the increment (P2-08).")
    A("3. *The StrongREJECT judge flips ~2 % of labels on byte-identical generations, so any ΔASR below "
      "~2 pp is uninterpretable.* — P81-01. A genuine methods contribution, and it bounds every behavioral "
      "number in the paper.")
    A("4. *A previously reported sub-additive interaction between Doublespeak and refusal-ablation is a "
      "saturation artifact: Î tracks the design's arithmetic ceiling with Spearman +0.991 — including "
      "through a reversal of that ceiling — and vanishes at a de-saturated dose.* — P81-07, P81-08. "
      "**Report this as a negative-result / methodology finding, and state explicitly that it is NOT "
      "evidence the two channels are independent** (the α=0.25 CI spans [−0.151, +0.105] at n=86).")
    A("5. *Doublespeak is an imperfect refusal suppressor: it leaves 45–48 % of clearharm items still "
      "refusing, and D_i = +2 -- an item neither factor jailbreaks alone but both do together -- never occurs "
      "on the primary clearharm cohort (0/86 at any dose; curated shows 4/51 item-doses, so this is a "
      "clearharm-specific, not universal, no-synergy backstop).* -- BR-07, P81-13.")
    A("")
    A("### Sentences that are NOT safe")
    A("")
    A("- ❌ *Doublespeak and refusal-ablation act on a shared refusal bottleneck.* — **WITHDRAWN** (P80-02).")
    A("- ❌ *The concept circuit is behaviorally inert / the carry heads are behaviorally necessary.* — the "
      "first is an underpowered null (P100-07, BC-02, P10-07), the second fails its specificity control "
      "(P100-02). The defensible wording is **\"no effect is detectable at n = 86, where 80 % power "
      "requires n ≈ 275\"**, and for the carry heads **\"not distinguishable from a size-matched random "
      "ablation\"**.")
    A("- ❌ *All-occurrence patching doubles the write.* — UNDERPOWERED design (P2-08); a within-item paired "
      "contrast is needed first.")
    A("- ❌ *A mechanism-derived GCG objective fails.* — SUPERSEDED (FIN-05): the objective was never in "
      "candidate selection.")
    A("- ⚠️ The OLD framing **\"the refusal decision is read mid-late, not early\"** — RETIRED. The validation "
      "(720463/721957/722611/724931) landed: L0-L12 carry no valid refusal axis, so \"L9 ns\" was "
      "uninformative. Cite the positive replacement instead — **the refusal axis first becomes causally "
      "manipulable at L13** (BR-09), anchored on L16/L18 which validate in both families.")
    A("")
    A("---")
    A("")

    # ------- do not cite -------
    A("## DO NOT CITE")
    A("")
    A("### Retracted outright (WITHDRAWN)")
    A("")
    A("| # | claim | why it is dead |")
    A("|---|---|---|")
    for c in claims:
        if c["status"] == "WITHDRAWN":
            A(f"| {c['id']} | {esc(c['claim'])} | {esc(first_sentence(c.get('note')))} |")
    A("")
    A("### Replaced (SUPERSEDED) — cite the successor, never the original")
    A("")
    A("| # | claim | superseded by |")
    A("|---|---|---|")
    for c in claims:
        if c["status"] == "SUPERSEDED":
            A(f"| {c['id']} | {esc(c['claim'])} | {esc(first_sentence(c.get('note')))} |")
    A("")
    A("### Cannot be cited yet (PENDING / UNVERIFIED / UNDERPOWERED)")
    A("")
    A("| # | status | claim | what unblocks it |")
    A("|---|---|---|---|")
    for c in claims:
        if c["status"] in ("PENDING", "UNVERIFIED", "UNDERPOWERED"):
            A(f"| {c['id']} | {BADGE[c['status']]} | {esc(c['claim'])} | {esc(first_sentence(c.get('note')))} |")
    A("")
    A("### Below the noise floor — uninterpretable as effects")
    A("")
    A("These are effects small enough that the judge alone could produce them. **Do not quote any of them "
      "as a magnitude**; quote them only as \"not detectable\".")
    A("")
    A("| # | effect | claim |")
    A("|---|---|---|")
    small = [c for c in claims if c["_floor"] in ("below", "at") and not c.get("null_by_design")]
    for c in small:
        A(f"| {c['id']} | {c['effect']:+.4f} ({'BELOW' if c['_floor']=='below' else 'AT'} the ~2 pp floor) | {esc(c['claim'])} |")
    if not small:
        A("| — | — | *(none)* |")
    A("")
    A("**Distinct from the above: controls that are SUPPOSED to be zero.** For these, sitting at the floor "
      "is the result, not a limitation — but it also means the control can only ever demonstrate "
      "*\"no larger than the judge noise\"*, never exact inertness.")
    A("")
    A("| # | effect | claim |")
    A("|---|---|---|")
    for c in claims:
        if c["_floor"] in ("below", "at") and c.get("null_by_design"):
            A(f"| {c['id']} | {c['effect']:+.4f} | {esc(c['claim'])} |")
    A("")
    A("---")
    A("")

    # ------- untraceable -------
    A("## Claims that could NOT be traced to a run directory — the dangerous ones")
    A("")
    A("A claim is listed here if it cites no run directory at all, if a cited directory has vanished, if a "
      "numeric check failed, or if it has never been recomputed from raw. Claims whose evidence is "
      "legitimately not a run (a dataset file, a repo-wide audit) carry an explicit `artifact` instead and "
      "are not listed. **These are the rows to fix before submission.**")
    A("")
    A("| # | status | claim | what is missing |")
    A("|---|---|---|---|")
    untraceable = []
    for c in claims:
        problems = []
        if not c.get("dirs") and not c.get("artifact"):
            problems.append("the source report names **no run directory** and no artifact could be identified")
        if c["_missing_dirs"]:
            problems.append("cited dir(s) absent from disk: " + ", ".join(f"`{d}`" for d in c["_missing_dirs"]))
        if c["_check_verdict"] == "CHECK-FAIL":
            problems.append("numeric check FAILED: " + "; ".join(c["_check_detail"]))
        if c["status"] == "UNVERIFIED":
            problems.append("never recomputed from raw")
        if problems:
            untraceable.append(c)
            A(f"| {c['id']} | {BADGE[c['status']]} | {esc(c['claim'][:150])} | " + esc("; ".join(problems)) + " |")
    if not untraceable:
        A("| — | — | *(none)* | — |")
    A("")
    A("---")
    A("")

    # ------- mechanical appendix -------
    A("## Mechanical appendix — the state of every cited run directory")
    A("")
    A(f"`validate_all_outputs.py` verdict: {vsummary if do_validate else '(skipped with --no-validate)'}")
    A("")
    A("| run dir | exists | contract files | raw rows | summary recompute (validate_all_outputs) |")
    A("|---|---|---|---|---|")
    for d, info in sorted(dir_info.items()):
        v = verdicts.get(os.path.basename(d))
        if not do_validate:
            vtxt = "(skipped)"
        elif v is None:
            vtxt = "not run"
        else:
            vtxt = f"**{v['status']}**" if v["status"] == "FAIL" else v["status"]
            if v.get("checked") is not None:
                vtxt += f" — {v['checked']} values recomputed, {v['mismatched']} mismatched"
            if v.get("issues"):
                vtxt += " — " + "; ".join(str(i) for i in v["issues"])[:180]
        A(f"| `{os.path.basename(d)}` | {'yes' if info['exists'] else '**NO**'} | "
          f"{'+'.join(info['files']) or '—'} | {info['rows'] if info['rows'] is not None else '—'} | {vtxt} |")
    A("")
    fails = [d for d in dir_info if verdicts.get(os.path.basename(d), {}).get("status") == "FAIL"]
    if fails:
        A(f"**{len(fails)} cited run dir(s) FAIL the summary-vs-raw reconciliation:**")
        A("")
        for d in sorted(fails):
            iss = verdicts.get(os.path.basename(d), {}).get("issues", [])
            A(f"- `{os.path.basename(d)}` — " + esc("; ".join(str(i) for i in iss) or "see validator output"))
        A("")
        A("A FAIL is only a *numeric* mismatch when the message says `summary!=raw`. A missing `summary.json` "
          "or an unrecognized row schema is a contract/coverage gap: real, but it means the number was never "
          "checked, not that it is wrong. **A `summary!=raw` FAIL means a committed number does not follow "
          "from its own preserved rows and must be recomputed before it is cited.**")
        A("")
    A("### Standing scope limits on the word VERIFIED")
    A("")
    A("1. Only **96 of 397** output dirs carry `raw.jsonl`; the rest cannot be recomputed at all (META-02).")
    A("2. `validate_all_outputs.py` reports WARN (not ok) on dirs with no `configs/manifests/<phase>.json`; "
      "WARN is a manifest gap, not a numeric mismatch. Only FAIL means a summary no longer follows from its rows.")
    A("3. Reports **PHASE5_HEADS.md, PHASE7_PATH.md, PHASE9_DOSE.md and CAUSAL_OBJECTIVE.md cite no run "
      "directory at all**; their run dirs were traced here through the harnesses' naming conventions. Every "
      "paper-facing report should name its run dir, as PHASE2_ALL_OCCURRENCES / P10 / P8.1 do.")
    A("4. This pass audited the reports listed in plan §5 P14. The individual phase reports for Phases 3–10 "
      "were **not** re-audited claim-by-claim; their headline statements enter here only through "
      "`FINAL_CAUSAL_CIRCUIT_REPORT.md` (rows FIN-*), and a full pass over them is outstanding.")
    A("")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=OUT_MD)
    ap.add_argument("--no-validate", action="store_true", help="skip validate_all_outputs.py")
    ap.add_argument("--print", dest="only_print", action="store_true", help="do not write the report")
    ap.add_argument("--json", help="also write the machine-readable audit result here")
    args = ap.parse_args()

    dir_info, verdicts, vsummary = evaluate(CLAIMS, do_validate=not args.no_validate)
    md = render(CLAIMS, dir_info, verdicts, vsummary, do_validate=not args.no_validate)

    if not args.only_print:
        os.makedirs(os.path.dirname(args.out), exist_ok=True)
        with open(args.out, "w") as fh:
            fh.write(md)
        print(f"wrote {args.out}")

    if args.json:
        payload = {
            "generated": datetime.now(timezone.utc).isoformat(),
            "n_claims": len(CLAIMS),
            "histogram": {s: sum(1 for c in CLAIMS if c["status"] == s) for s in STATUSES},
            "claims": [{k: v for k, v in c.items() if not k.startswith("_") and k != "checks"}
                       | {"check_verdict": c["_check_verdict"], "check_detail": c["_check_detail"],
                          "missing_dirs": c["_missing_dirs"], "floor": c["_floor"]}
                       for c in CLAIMS],
            "dirs": dir_info,
            "validator_summary": vsummary,
        }
        with open(args.json, "w") as fh:
            json.dump(payload, fh, indent=1)
        print(f"wrote {args.json}")

    hist = {s: sum(1 for c in CLAIMS if c["status"] == s) for s in STATUSES}
    n_fail = sum(1 for c in CLAIMS if c["_check_verdict"] == "CHECK-FAIL")
    n_miss = sum(1 for c in CLAIMS if c["_missing_dirs"])
    n_untraced = sum(1 for c in CLAIMS if not c.get("dirs") and not c.get("artifact"))
    print(f"claims={len(CLAIMS)}  " + "  ".join(f"{s}={hist[s]}" for s in STATUSES))
    print(f"numeric checks: {sum(len(c['_checks']) for c in CLAIMS)} run, {n_fail} claim(s) CHECK-FAIL")
    print(f"run dirs: {len(dir_info)} cited, {n_miss} claim(s) with a missing dir, {n_untraced} claim(s) cite no dir")
    for c in CLAIMS:
        if c["_check_verdict"] == "CHECK-FAIL":
            print(f"  CHECK-FAIL {c['id']}: " + " | ".join(c["_check_detail"]))
        for d in c["_missing_dirs"]:
            print(f"  MISSING DIR {c['id']}: {d}")
    return 1 if (n_fail or n_miss) else 0


if __name__ == "__main__":
    sys.exit(main())
