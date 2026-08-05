#!/usr/bin/env python3
"""Summary-vs-raw reconciliation validator (plan §P0: "recompute every `summary.json` number from its
`raw.jsonl`, verify train/test disjointness, verify all manifest cells present, fail on a missing cell").

For every run dir given it:
  1. loads `raw.jsonl` + `summary.json` and detects the row schema (reuses
     `validate_experiment_coverage.detect`, so the two validators can never disagree about a schema);
  2. **recomputes** the aggregates in `summary.json` directly from `raw.jsonl` and asserts they match to
     `--tol` (or to the rounding the summary itself used, bounded by `--round-cap`) -- any mismatch is a
     hard FAIL, because it means the committed number does not follow from the preserved rows;
  3. asserts the train/test (dev/heldout) example ids are **disjoint**;
  4. asserts that nothing was **deleted** from `summary.json`: every structurally-required key
     (`<split>.n`, per-arm ASR, per-window n_valid, ...) must be present, every split/window seen in
     `raw.jsonl` must have a node in the summary, and sibling nodes (splits, windows, per_layer heads)
     must carry the same leaf-key shape -- see "Deletion detection" below;
  5. if `configs/manifests/<phase>.json` exists, asserts every expected cell / arm / split is present and
     **FAILS on a missing one** (extras are warnings);
  6. reports how many summary leaves it could not recompute, so the coverage of this check is auditable
     instead of implicit.

Deletion detection (why it is not just "every recomputed key must exist"):
  the recomputer proposes *every* layout a phase may have written (`ASR_<arm>` and `ASR: {<arm>: ..}`),
  so a blanket "absent => FAIL" would fire on ~750 legitimately-absent alternative-layout keys. Instead
  each recomputed value belongs to a *group* of equivalent paths with a presence contract:
    Expect.put(p, v)          exactly one path, MUST exist
    Expect.alt([p1, p2], v)   equivalent layouts, at least ONE must exist
    Expect.opt(p, v)          phase-variant key, checked only if present
  plus two structural checks that need no expectation at all: split/window node coverage against
  `raw.jsonl`, and sibling-key symmetry (all split nodes / window blocks / per_layer blocks must expose
  the same leaf paths modulo list indices). Between them, deleting any leaf or any node from a
  `summary.json` is a FAIL. `--allow-missing-keys` restores the old (silent) behavior.

Exit code is non-zero if any dir FAILS. `--json PATH` writes the machine-readable per-dir result.

What is recomputed, by family:
  behav (`{id, split, cohort, <arm>_label, <arm>_score}` and its non-judged numeric-arm variants):
      n, ASR/refusal_rate/empty_rate per arm (flat `ASR_<arm>` and nested `ASR: {<arm>: ..}` layouts),
      `delta_*` necessity/control deltas, `<a2>_vs_<a1>` and `vs_ds_base` / `by_layer_vs_ds_base`
      McNemar blocks (delta_ASR, flip counts, exact p), `per_layer.<h>.mean.<arm>` projections and their
      paired-difference point estimates, `pconcept_control`, `max_suppression*`, trajectory means.
  phase6: n_rows, per-window n_valid, mean_C1/C3/S3 p_concept, nec/suf self-swap max dev,
      necessity/sufficiency point estimates (bootstrap CI *bounds* are RNG-dependent -> not checked).
  phase5: n_rows, per-split n_valid, selfswap_max_dev, top10_by_mean values.

Manifest format (`configs/manifests/<phase>.json`, all keys optional):
  {"phase": "behav_carry",
   "expected_splits": ["train", "test"], "min_n_per_split": 20,
   "expected_arms":  ["baseline", "carry_abl", "rand_abl"],     # behavioral arm prefixes
   "expected_cells": ["C1", "C3", "C1_selfswap"],               # phase5/6 `cell` column values
   "expected_windows": ["L8", "L9"]}                            # phase6 `window` column values
The phase key is resolved from the run-dir basename by trying successively shorter `_`-separated
prefixes (`behav_carry_curated` -> `behav_carry` -> `behav`), first hit wins; `--manifest` forces one.

Usage:
  python scripts/validate_all_outputs.py outputs/behav_* [--tol 5e-4] [--manifest-dir configs/manifests]
Runs on the LOGIN NODE (stdlib only; reads raw.jsonl, which carries no free text -- but it does carry
concept/codeword fields, so this is a MAIN-LOOP tool).
"""
from __future__ import annotations
import argparse, glob, json, math, os, re, sys
from collections import defaultdict
from math import comb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_experiment_coverage import detect, behav_arms, load   # noqa: E402  (single source of truth)

DEFAULT_TOL = 5e-4
# Hard ceiling on the "the summary stored a rounded number" allowance in close(). A value printed with
# `d` decimals may legitimately sit half an ulp (0.5*10**-d) away from the exact recomputation; anything
# whose half-ulp exceeds this cap gets NO allowance at all, so a 1-decimal value (half-ulp 0.05) can no
# longer swallow a 0.04 corruption. 5e-3 keeps 2-decimal summaries (the coarsest real ones in outputs/)
# working; pass `--round-cap 0` to disable the allowance entirely.
DEFAULT_ROUND_CAP = 5e-3
MAL = "MALICIOUS"

# `delta_<name>` aggregates whose definition is not derivable from the key alone.
# value = ASR[a] - ASR[b]
DELTA_MAP = {
    "delta_necessity_carry":  ("baseline", "carry_abl"),
    "delta_necessity_write":  ("baseline", "write_abl"),
    "delta_rand_ctrl":        ("baseline", "rand_abl"),
    "delta_rand_pos_ctrl":    ("baseline", "rand_pos_abl"),
}
# per_layer paired-difference blocks: key -> (arm_a, arm_b); stored value is [mean, lo, hi]
PAIRDIFF_MAP = {
    "direct_minus_ds":          ("direct", "doublespeak"),
    "direct_minus_ds_RANDCTRL": ("direct_rand", "doublespeak_rand"),
    "writeabl_minus_dsbase":    ("ds_writeabl", "ds_base"),
}


# --------------------------------------------------------------------------- helpers

def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(0, k + 1)) / (2 ** n))


def _dec(v):
    s = repr(float(v))
    if "e" in s or "E" in s:
        return 12
    return min(12, len(s.split(".")[1]) if "." in s else 0)


def close(a, b, tol, round_cap=DEFAULT_ROUND_CAP):
    """a = recomputed, b = value stored in summary.json.

    Beyond the absolute `tol` there is a *printed-precision* allowance: if `b` was serialized with `d`
    decimals it can only be `a` rounded to `d` decimals, i.e. at most half an ulp away.  That allowance
    is capped at `round_cap`: it used to be unbounded, so a value stored as `11.9` accepted any
    recomputation in [11.85, 11.95) -- a +/-0.05 hole that hid real summary/raw divergence.  With the cap
    a coarse (0/1-decimal) value gets no allowance at all and must match within `tol`.
    """
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, str) or isinstance(b, str):
        return a == b
    if isinstance(a, float) and math.isnan(a):
        return isinstance(b, float) and math.isnan(b)
    if abs(a - b) <= tol:
        return True
    dec = _dec(b)
    half_ulp = 0.5 * 10.0 ** (-dec)
    if half_ulp > round_cap:
        return False
    return abs(a - b) <= half_ulp and round(float(a), dec) == float(b)


class Expect(dict):
    """`{summary_path: recomputed_value}` plus a presence contract per group of equivalent paths.

    The recomputer proposes every layout a phase may have used, so "path absent from summary.json" is
    normally benign.  Grouping makes the difference between *benign absence* (the other layout is
    present) and a *deleted number* (nothing in the group is present) expressible:

      put(p, v)         one path, must exist
      alt([p, ...], v)  equivalent layouts, at least one must exist
      opt(p, v)         only some phase variants emit it; checked when present, never required
    """

    def __init__(self):
        super().__init__()
        self.groups = []                       # [(paths, required)]

    def put(self, path, value, required=True):
        self[path] = value
        self.groups.append(([path], required))

    def opt(self, path, value):
        self.put(path, value, required=False)

    def alt(self, paths, value, required=True):
        paths = list(paths)
        for p in paths:
            self[p] = value
        self.groups.append((paths, required))

    def missing_groups(self, got):
        """-> [paths] for every REQUIRED group with no member in `got` (i.e. a deleted summary key)."""
        return [g for g, req in self.groups if req and not any(p in got for p in g)]


def redact(v):
    """Values printed by the validator are numbers; anything else is shown as a type tag."""
    if v is None or isinstance(v, (int, float)) and not isinstance(v, bool):
        return v
    if isinstance(v, str) and len(v) <= 16 and v.replace("_", "").replace("-", "").isalnum():
        return v                      # short identifiers (cell / head names) are safe
    return f"<{type(v).__name__}>"


def leaves(v, path=""):
    """Flatten a summary into {path: scalar}. Lists index as `key[i]`, `None` is kept."""
    out = {}
    if isinstance(v, dict):
        for k, x in v.items():
            out.update(leaves(x, f"{path}.{k}" if path else str(k)))
    elif isinstance(v, (list, tuple)):
        for i, x in enumerate(v):
            out.update(leaves(x, f"{path}[{i}]"))
    else:
        out[path] = v
    return out


def mean(xs):
    xs = [x for x in xs if x is not None]
    return float(sum(xs)) / len(xs) if xs else None


def split_container(summary):
    """-> (prefix_fn, {split: node}) for both `by_split.<sp>` and top-level `<sp>` layouts."""
    if isinstance(summary.get("by_split"), dict):
        return (lambda sp: f"by_split.{sp}"), summary["by_split"]
    node = {k: v for k, v in summary.items()
            if k in ("train", "test", "dev", "heldout") and isinstance(v, dict)}
    return (lambda sp: sp), node


def resolve_cell(cells, base, prefer=()):
    """Resolve a logical cell family to the concrete `cell` value a run actually wrote.

    Every phase variant renames its intervention cell (`C3` -> `C3_mlpout` -> `C3_demoKV` -> ...), so
    hardcoding the names made the recomputer read an EMPTY map for any unseen variant: n_valid
    recomputed to 0 and the whole family FAILed with false mismatches. Resolution is therefore driven
    by the cells present in raw.jsonl: exact `base` wins, then the `prefer` list, then the
    lexicographically first `<base>_*` variant (self-swap controls excluded -- they are no-op cells).

    -> (cell_name | None, [all candidates])
    """
    cands = sorted(c for c in cells
                   if isinstance(c, str) and (c == base or c.startswith(base + "_"))
                   and not c.endswith("_selfswap"))
    if not cands:
        return None, []
    for p in (base,) + tuple(prefer):
        if p in cands:
            return p, cands
    return cands[0], cands


_IDX = re.compile(r"\[\d+\]")


def key_shape(paths):
    """Leaf paths with list indices collapsed -- the comparable 'shape' of a summary node."""
    return {_IDX.sub("[]", p) for p in paths}


def check_sibling_symmetry(summary, res):
    """Sibling nodes of the same container must expose the same leaf keys.

    A phase writes the same block for every split / window / attention head, so an asymmetry means a
    key was removed from one of them after the fact. This is layout-agnostic, so it catches deletions
    the recomputer has no expectation for.
    """
    def cmp_group(label, nodes):
        if len(nodes) < 2:
            return
        shapes = {k: key_shape(leaves(v)) for k, v in nodes.items() if isinstance(v, dict)}
        if len(shapes) < 2:
            return
        union = set.union(*shapes.values())
        for k, s in sorted(shapes.items(), key=lambda kv: str(kv[0])):
            gone = sorted(union - s)
            if gone:
                res["issues"].append(
                    f"summary key(s) MISSING from {label}[{redact(k)}] but present in its siblings: "
                    f"{gone[:6]}{' ...' if len(gone) > 6 else ''}")

    _, cont = split_container(summary)
    cmp_group("split", cont)
    for sp, node in (cont.items() if cont else [(None, summary)]):
        tag = f"{sp}." if sp is not None else ""
        if not isinstance(node, dict):
            continue
        for sub in ("windows", "per_layer", "by_layer"):
            if isinstance(node.get(sub), dict):
                cmp_group(f"{tag}{sub}", node[sub])


# --------------------------------------------------------------------------- behavioral

def expect_behav(rows, summary, res=None):
    """-> Expect (see class docstring for the put/alt/opt presence contract)"""
    exp = Expect()
    labelled, numeric = behav_arms(rows)
    if "n_rows" in summary:
        exp.put("n_rows", len(rows))
    pref, cont = split_container(summary)
    by_split = defaultdict(list)
    for r in rows:
        by_split[r.get("split")].append(r)

    for sp, node in cont.items():
        sr = by_split.get(sp)
        if not sr:
            continue
        P = pref(sp)
        asr = {a: mean([r.get(f"{a}_label") == MAL for r in sr]) for a in labelled}
        rej = {a: mean([r.get(f"{a}_label") == "REJECTED" for r in sr]) for a in labelled}
        emp = {a: mean([r.get(f"{a}_label") == "EMPTY" for r in sr]) for a in labelled}
        exp.put(f"{P}.n", len(sr))

        # ASR is written by every judged behavioral phase, in one of two equivalent layouts -> the
        # arm must be reported somewhere (deleting it is a FAIL); refusal / empty tables are
        # phase-optional, so they are only checked when present.
        for a in labelled:
            exp.alt([f"{P}.ASR_{a}", f"{P}.ASR.{a}"], asr[a])
            exp.alt([f"{P}.refused_{a}", f"{P}.refusal_rate.{a}"], rej[a], required=False)
            exp.alt([f"{P}.empty_{a}", f"{P}.empty.{a}", f"{P}.empty_rate.{a}"], emp[a], required=False)
        for k, (a, b) in DELTA_MAP.items():
            if a in asr and b in asr:
                exp.opt(f"{P}.{k}", asr[a] - asr[b])
        for k in node:                                        # mean_<rawfield>
            if k.startswith("mean_") and k[5:] in rows[0]:
                exp.put(f"{P}.{k}", mean([r.get(k[5:]) for r in sr]))

        def mcn(a1, a2, base, names, required=True):
            """paired McNemar block: a1 = reference arm, a2 = compared arm.
            `names=None` -> the phase does not store the flip counts, only the delta / p."""
            b = sum(1 for r in sr if r.get(f"{a1}_label") != MAL and r.get(f"{a2}_label") == MAL)
            c = sum(1 for r in sr if r.get(f"{a1}_label") == MAL and r.get(f"{a2}_label") != MAL)
            add = exp.put if required else exp.opt
            add(f"{base}.delta_ASR", asr[a2] - asr[a1])
            if names:
                add(f"{base}.{names[0]}", b)
                add(f"{base}.{names[1]}", c)
            add(f"{base}.mcnemar_p", mcnemar_exact(b, c))

        for k, v in node.items():
            if "_vs_" in k and isinstance(v, dict):           # "<a2>_vs_<a1>"
                a2, a1 = k.split("_vs_", 1)
                if a1 in asr and a2 in asr:
                    nm = ("flip_gain", "flip_loss") if "flip_gain" in v else ("flip_on", "flip_off")
                    mcn(a1, a2, f"{P}.{k}", nm)
            if k == "vs_ds_base" and isinstance(v, dict) and "ds_base" in asr:
                for a, blk in v.items():
                    if a in asr:
                        nm = ("flip_on", "flip_off") if "flip_on" in blk else ("flip_gain", "flip_loss")
                        mcn("ds_base", a, f"{P}.{k}.{a}", nm)
            if k == "by_layer_vs_ds_base" and isinstance(v, dict) and "ds_base" in asr:
                for L, blk in v.items():
                    a, ar = f"ds_cal_L{L}", f"ds_calrand_L{L}"
                    if a in asr:
                        # this block's contents vary across refinject variants -> checked, not required
                        mcn("ds_base", a, f"{P}.{k}.{L}", None, required=False)
                    if ar in asr:
                        exp.opt(f"{P}.{k}.{L}.rand_delta_ASR", asr[ar] - asr["ds_base"])

        # ---- non-judged numeric arms: per-layer projections / trajectories
        pl = node.get("per_layer")
        if isinstance(pl, dict):
            for h, blk in pl.items():
                md = blk.get("mean", {})
                for a in md:
                    if a in numeric:
                        exp.put(f"{P}.per_layer.{h}.mean.{a}", mean([r[a][h] for r in sr]))
                for k, (a, b) in PAIRDIFF_MAP.items():
                    if k in blk and a in numeric and b in numeric:
                        exp.put(f"{P}.per_layer.{h}.{k}[0]", mean([r[a][h] - r[b][h] for r in sr]))
                if "frac_of_direct_gap_restored" in blk and {"direct", "ds_base", "ds_writeabl"} <= set(numeric):
                    m = {a: round(mean([r[a][h] for r in sr]), 4) for a in ("direct", "ds_base", "ds_writeabl")}
                    gap = m["direct"] - m["ds_base"]
                    exp.put(f"{P}.per_layer.{h}.frac_of_direct_gap_restored",
                            round((m["ds_writeabl"] - m["ds_base"]) / gap, 3) if abs(gap) > 1e-6 else None)
            if "max_suppression_hs_row" in node:
                d = {h: mean([r["direct"][h] - r["doublespeak"][h] for r in sr]) for h in pl}
                best = max(d, key=lambda h: round(d[h], 4))
                exp.put(f"{P}.max_suppression_hs_row", int(best))
                exp.opt(f"{P}.max_suppression[0]", d[best])
        pc = node.get("pconcept_control")
        if isinstance(pc, dict):
            exp.opt(f"{P}.pconcept_control.ds", mean([r.get("pconcept_ds") for r in sr]))
            exp.opt(f"{P}.pconcept_control.writeabl", mean([r.get("pconcept_writeabl") for r in sr]))
            exp.opt(f"{P}.pconcept_control.drop_ci[0]", mean(
                [r["pconcept_ds"] - r["pconcept_writeabl"] for r in sr
                 if r.get("pconcept_ds") is not None and r.get("pconcept_writeabl") is not None]))
        bl = node.get("by_layer")
        if isinstance(bl, dict) and any(k.endswith("_traj") for k in rows[0]):
            k_len = summary.get("k") or max(len(v) for r in sr for v in r["direct_traj"].values())
            ds_ref = [r for r in sr if r.get("ds_refused")]
            ds_cmp = [r for r in sr if not r.get("ds_refused")]
            exp.opt(f"{P}.ds_refused_rate", len(ds_ref) / len(sr))
            exp.opt(f"{P}.direct_refused_rate", mean([bool(r.get("direct_refused")) for r in sr]))
            for L, blk in bl.items():
                for name, rs, arm in (("direct", sr, "direct"), ("ds_all", sr, "ds"),
                                      ("ds_complied", ds_cmp, "ds"), ("ds_refused", ds_ref, "ds")):
                    if blk.get(name) is None:
                        continue
                    for i in range(k_len):
                        vals = [r[f"{arm}_traj"].get(L, [])[i] for r in rs
                                if i < len(r[f"{arm}_traj"].get(L, []))]
                        # k_len is an upper bound on the stored trajectory length -> not required
                        exp.opt(f"{P}.by_layer.{L}.{name}[{i}]", mean(vals))
    return exp


# --------------------------------------------------------------------------- phase6 / phase5

def expect_phase6(rows, summary, res=None):
    exp = Expect()
    if "n_rows" in summary:
        exp.put("n_rows", len(rows))
    cells = {r.get("cell") for r in rows}
    nec_cell, nec_cands = resolve_cell(cells, "C3", prefer=("C3_mlpout",))
    suf_cell, suf_cands = resolve_cell(cells, "S3", prefer=("S3_install",))
    if res is not None:
        if nec_cell is None:
            res["warns"].append("no necessity cell (C3 / C3_*) in raw.jsonl -- necessity not recomputed")
        elif len(nec_cands) > 1:
            res["warns"].append(f"ambiguous necessity cell: {nec_cands} -- using '{nec_cell}'")
        if suf_cell is not None and len(suf_cands) > 1:
            res["warns"].append(f"ambiguous sufficiency cell: {suf_cands} -- using '{suf_cell}'")
    # every per-window aggregate is computed over the VALID examples, and validity is defined against
    # `benign_p_concept`; without that column nothing downstream is recomputable, so recomputing it
    # anyway would just compare the summary against an empty set.
    if not any(r.get("benign_p_concept") is not None for r in rows):
        if res is not None:
            res["warns"].append("benign_p_concept absent from raw.jsonl -- per-window aggregates "
                                "cannot be recomputed (validity filter undefined)")
        return exp
    pref, cont = split_container(summary)
    nodes = list(cont.items()) if cont else ([(None, summary)] if "windows" in summary else [])
    for sp, node in nodes:
        sr = [r for r in rows if sp is None or r["split"] == sp]
        P = (pref(sp) + ".") if sp is not None else ""
        valid = {r["sid"] for r in sr if r["cell"] == "C1"
                 and r.get("benign_p_concept") is not None and r["p_concept"] > r["benign_p_concept"]}
        if "n_valid_examples" in node:
            exp.put(f"{P}n_valid_examples", len(valid))
        for w, blk in (node.get("windows") or {}).items():
            def cm(cell):
                return ({} if cell is None else
                        {r["sid"]: r["p_concept"] for r in sr if r["cell"] == cell and r["window"] == w})
            c1, c3, rc, ss = cm("C1"), cm(nec_cell), cm("random_control"), cm("C1_selfswap")
            s1, s3, srd, sss = cm("S1"), cm(suf_cell), cm("S_random"), cm("S1_selfswap")
            nec = [s for s in valid if s in c1 and s in c3 and s in rc]
            suf = [s for s in valid if s in s1 and s in s3 and s in srd]
            B = f"{P}windows.{w}"
            exp.put(f"{B}.n_valid", len(nec))
            exp.opt(f"{B}.mean_C1_p_concept", mean([c1[s] for s in nec]))
            if "mean_C3_p_concept" in blk:
                exp.put(f"{B}.mean_C3_p_concept", mean([c3[s] for s in nec]))
            exp.opt(f"{B}.necessity_specific_ci[0]", mean([rc[s] - c3[s] for s in nec]))
            exp.opt(f"{B}.nec_selfswap_max_dev",
                    max([abs(c1[s] - ss[s]) for s in nec if s in ss], default=None) if nec else None)
            if "sufficiency_specific_ci" in blk:
                exp.put(f"{B}.sufficiency_specific_ci[0]", mean([s3[s] - srd[s] for s in suf]))
                exp.put(f"{B}.mean_S3_install_p_concept", mean([s3[s] for s in suf]))
                exp.opt(f"{B}.suf_selfswap_max_dev",
                        max([abs(s1[s] - sss[s]) for s in suf if s in sss], default=None) if suf else None)
    return exp


def expect_phase5(rows, summary, res=None):
    exp = Expect()
    if "n_rows" in summary:
        exp.put("n_rows", len(rows))
    pref, cont = split_container(summary)
    for sp, node in cont.items():
        sr = [r for r in rows if r["split"] == sp]
        P = pref(sp)
        valid = {r["sid"] for r in sr if r["cell"] == "benign" and r.get("benign_p_concept") is not None
                 and r["C1"] > r["benign_p_concept"]}
        exp.put(f"{P}.n_valid", len(valid))
        exp.put(f"{P}.selfswap_max_dev", max([abs(r["C1"] - r["p_concept"]) for r in sr
                                              if r["cell"] == "selfswap"], default=0.0))
        for i, ent in enumerate(node.get("top10_by_mean") or []):
            name = ent[0]
            l, h = name[1:].split("H")
            d = [r["C1"] - r["p_concept"] for r in sr if r["cell"] == "benign"
                 and r["layer"] == int(l) and r["head"] == int(h) and r["sid"] in valid]
            exp.put(f"{P}.top10_by_mean[{i}][0]", name)
            exp.put(f"{P}.top10_by_mean[{i}][1]", mean(d))
    return exp


EXPECT = {"behav": expect_behav, "phase6": expect_phase6, "phase5": expect_phase5}


# --------------------------------------------------------------------------- manifest

def find_manifest(d, mdir, forced):
    if forced:
        return forced, json.load(open(forced))
    base = os.path.basename(os.path.normpath(d))
    parts = base.split("_")
    for i in range(len(parts), 0, -1):
        p = os.path.join(mdir, "_".join(parts[:i]) + ".json")
        if os.path.exists(p):
            return p, json.load(open(p))
    return None, None


def check_manifest(rows, man, typ):
    issues, warns = [], []
    got_splits = {r.get("split") for r in rows}
    exp_splits = set(man.get("expected_splits") or [])
    for s in sorted(exp_splits - got_splits):
        issues.append(f"manifest: split '{s}' MISSING from raw.jsonl")
    for s in sorted(got_splits - exp_splits) if exp_splits else []:
        warns.append(f"manifest: unexpected split '{s}'")
    minn = man.get("min_n_per_split")
    if minn:
        key = "id" if typ == "behav" else "sid"
        for s in sorted(got_splits):
            n = len({r.get(key) for r in rows if r.get("split") == s})
            if n < minn:
                issues.append(f"manifest: split '{s}' has n={n} < min_n_per_split={minn}")
    if man.get("expected_arms"):
        labelled, numeric = behav_arms(rows) if typ == "behav" else ([], [])
        got = set(labelled) | set(numeric)
        for a in man["expected_arms"]:
            if a not in got:
                issues.append(f"manifest: arm '{a}' MISSING")
            else:
                miss = sum(1 for r in rows if f"{a}_label" not in r and a not in r)
                if miss:
                    issues.append(f"manifest: arm '{a}' MISSING on {miss} rows")
        for a in sorted(got - set(man["expected_arms"])):
            warns.append(f"manifest: unexpected arm '{a}'")
    for field, col in (("expected_cells", "cell"), ("expected_windows", "window")):
        if man.get(field):
            got = {r.get(col) for r in rows}
            for c in man[field]:
                if c not in got:
                    issues.append(f"manifest: {col} '{c}' MISSING")
            for c in sorted(x for x in got - set(man[field]) if x is not None):
                warns.append(f"manifest: unexpected {col} '{c}'")
    return issues, warns


# --------------------------------------------------------------------------- driver

def validate_dir(d, args):
    res = {"dir": d, "status": "ok", "type": None, "issues": [], "warns": [],
           "n_checked": 0, "n_unchecked": 0, "mismatches": []}
    try:
        rows = load(d)
    except Exception as e:
        res.update(status="FAIL", issues=[f"cannot read raw.jsonl: {e}"])
        return res
    sp = os.path.join(d, "summary.json")
    if not os.path.exists(sp):
        res.update(status="FAIL", issues=["summary.json MISSING (run-dir contract §2.1)"])
        return res
    summary = json.load(open(sp))
    typ, _ = detect(rows)
    res["type"] = typ
    if typ is None:
        res.update(status="FAIL", issues=["unrecognized row schema"])
        return res

    # ---- 1. split disjointness
    key = "id" if typ == "behav" else "sid"
    ids = defaultdict(set)
    for r in rows:
        ids[r.get("split")].add(r.get(key))
    sps = sorted(x for x in ids if x is not None)
    for i in range(len(sps)):
        for j in range(i + 1, len(sps)):
            sh = ids[sps[i]] & ids[sps[j]]
            if sh:
                res["issues"].append(f"{len(sh)} {key}s shared between splits {sps[i]}/{sps[j]}")
    if len(sps) < 2:
        res["warns"].append(f"only {len(sps)} split(s) present: {sps}")
    res["splits"] = {s: len(ids[s]) for s in sps}

    # ---- 2. recompute summary from raw
    exp = EXPECT[typ](rows, summary, res)
    got = leaves(summary)
    checked = 0
    for path, want in exp.items():
        if path not in got:
            # a phase writes ONE of several equivalent layouts (`ASR_<arm>` vs `ASR: {<arm>: ..}`);
            # the recomputer proposes all of them, so an absent path is normally just the other layout.
            # Whether the *group* is entirely absent (= a deleted number) is decided below.
            if args.warn_missing_keys:
                res["warns"].append(f"recomputed key absent from summary: {path}")
            continue
        checked += 1
        if not close(want, got[path], args.tol, args.round_cap):
            res["mismatches"].append({"path": path, "summary": got[path], "recomputed": want})
    res["n_checked"] = checked

    # ---- 2b. DELETED summary keys. A required group with no member present means the number the
    # phase must have written is simply gone -- previously a silent `continue`, now a FAIL.
    gone = exp.missing_groups(got)
    res["missing_required"] = [g[0] for g in gone]
    sink = res["warns"] if args.allow_missing_keys else res["issues"]
    for g in gone[:args.max_report]:
        sink.append("summary key MISSING (required, recomputable from raw.jsonl): "
                    + (g[0] if len(g) == 1 else " | ".join(g)))
    if len(gone) > args.max_report:
        sink.append(f"... and {len(gone) - args.max_report} more required summary keys MISSING")

    # ---- 2c. structural coverage: every split / window that exists in raw.jsonl must have a node.
    _, cont = split_container(summary)
    if cont and not args.allow_missing_keys:
        for s in sps:
            if s not in cont:
                res["issues"].append(f"summary MISSING the whole node for split '{s}' (present in raw.jsonl)")
    if typ == "phase6" and not args.allow_missing_keys:
        wins = {r.get("window") for r in rows if r.get("window") is not None}
        for _sp, node in (cont.items() if cont else [(None, summary)]):
            wnode = node.get("windows") if isinstance(node, dict) else None
            if isinstance(wnode, dict):
                for w in sorted(str(x) for x in wins):
                    if w not in wnode:
                        res["issues"].append(f"summary windows block MISSING window '{w}' "
                                             f"(present in raw.jsonl)")
    if not args.allow_missing_keys:
        check_sibling_symmetry(summary, res)
    unchecked = [p for p in got if p not in exp and isinstance(got[p], (int, float)) and not isinstance(got[p], bool)]
    res["n_unchecked"] = len(unchecked)
    res["unchecked_sample"] = sorted(unchecked)[:8]
    for m in res["mismatches"][:args.max_report]:
        # numbers only in the printed message: summary.json is a committed artifact and must never be
        # echoed as free text by a validator (project safety rule).
        s, w = (redact(m["summary"]), redact(m["recomputed"]))
        res["issues"].append(f"summary!=raw at {m['path']}: summary={s} recomputed={w}")
    if len(res["mismatches"]) > args.max_report:
        res["issues"].append(f"... and {len(res['mismatches']) - args.max_report} more mismatches")

    # ---- 3. manifest
    mpath, man = find_manifest(d, args.manifest_dir, args.manifest)
    res["manifest"] = mpath
    if man is None:
        res["warns"].append(f"no manifest under {args.manifest_dir} (plan §P0 requires one per phase)")
        if args.require_manifest:
            res["issues"].append("manifest REQUIRED but not found")
    else:
        mi, mw = check_manifest(rows, man, typ)
        res["issues"] += mi
        res["warns"] += mw

    res["status"] = "FAIL" if res["issues"] else ("WARN" if res["warns"] else "ok")
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--tol", type=float, default=DEFAULT_TOL, help="absolute tolerance (default 5e-4)")
    ap.add_argument("--round-cap", type=float, default=DEFAULT_ROUND_CAP,
                    help="hard ceiling on the printed-precision allowance in close() (default 5e-3); "
                         "0 disables it, so only --tol is honoured")
    ap.add_argument("--manifest-dir", default="configs/manifests")
    ap.add_argument("--manifest", default=None, help="force one manifest file for every dir")
    ap.add_argument("--require-manifest", action="store_true", help="a missing manifest is a FAIL")
    ap.add_argument("--max-report", type=int, default=12, help="max mismatches printed per dir")
    ap.add_argument("--warn-missing-keys", action="store_true",
                    help="warn for EVERY recomputable path absent from summary.json (noisy: the "
                         "recomputer proposes every known summary layout; the deletion check below "
                         "is the non-noisy version and is always on)")
    ap.add_argument("--allow-missing-keys", action="store_true",
                    help="legacy: downgrade the deleted-summary-key / missing-node / sibling-asymmetry "
                         "checks from FAIL to warn")
    ap.add_argument("--json", dest="as_json", metavar="PATH", default=None)
    ap.add_argument("--quiet", action="store_true", help="print only FAIL dirs")
    args = ap.parse_args()

    dirs = []
    for d in args.dirs:
        dirs.extend(sorted(glob.glob(d)) if any(c in d for c in "*?[") else [d])

    out, nfail = [], 0
    print(f"{'dir':<58} {'type':<7} {'status':<6} {'checked':>7} {'unchk':>6}  splits")
    for d in dirs:
        r = validate_dir(d, args)
        out.append(r)
        nfail += r["status"] == "FAIL"
        if args.quiet and r["status"] != "FAIL":
            continue
        print(f"{os.path.basename(os.path.normpath(d)):<58} {str(r['type']):<7} {r['status']:<6} "
              f"{r['n_checked']:>7} {r['n_unchecked']:>6}  {r.get('splits', {})}")
        for x in r["issues"]:
            print(f"    FAIL: {x}")
        for x in r["warns"]:
            print(f"    warn: {x}")
    print(f"\n{len(out)} dir(s): {sum(1 for r in out if r['status']=='ok')} ok, "
          f"{sum(1 for r in out if r['status']=='WARN')} warn, {nfail} FAIL; "
          f"{sum(r['n_checked'] for r in out)} summary values recomputed, "
          f"{sum(len(r['mismatches']) for r in out)} mismatched")
    if args.as_json:
        with open(args.as_json, "w") as fh:
            json.dump(out, fh, indent=2)
    sys.exit(1 if nfail else 0)


if __name__ == "__main__":
    main()
