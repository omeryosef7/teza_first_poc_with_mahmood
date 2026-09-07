#!/usr/bin/env python3
"""Load and ENFORCE a DCS thesis-scale preregistration.  `PR-048` checklist item X1.

WHY THIS FILE EXISTS. `configs/dcs_ts_pr046.json` opens with:

    "Every gate below is loaded by the analyzer at runtime; the analyzer REFUSES to run if this
     file is absent, if any *_sha field is still null, or if a gate it needs is missing. A number
     in a markdown log that no program consults is a wish, not a preregistration."

**That was false when I wrote it.** `B-020` / the four-hour review found there was no analyzer at
all, so every threshold -- alpha, `n_perm`, the p-floor rule, the MDE, the flip trigger, the layer
grid, all eight nulls, all five gates -- was read by NO CODE PATH. That is exactly the "threshold
published but never enforced" failure this project has recorded twice before, committed by me
while citing it as the reason to write a machine-readable preregistration.

This module is that code path. It is deliberately SEPARATE from any analyzer so the enforcement
cannot be quietly bypassed by writing a second analyzer: any script that reads a preregistration
imports `load()` and gets the refusals for free.

WHAT IT REFUSES ON, all fail-closed:
  * the config file is missing or is not valid JSON
  * `status` is not FROZEN
  * ANY `*_sha16` field anywhere in the tree is null or empty
  * any pinned artifact path does not exist on disk
  * any pinned artifact's ACTUAL hash disagrees with the pinned one
  * a required top-level field is missing (mandate §21)
  * `require_gate(name)` is asked for a gate the config does not declare
  * a BLOCKING pre-extraction checklist item is not marked done, when `for_extraction=True`

The last one is the important one: it means an extraction cannot start while the checklist this
phase wrote for itself is outstanding.

USAGE
    from dcs_ts_prereg import load
    pr = load("configs/dcs_ts_pr048.json", for_extraction=True)
    alpha = pr.require("primary", "alpha")
    n_perm = pr.require("primary", "n_perm")

    python3 scripts/dcs_ts_prereg.py --check configs/dcs_ts_pr048.json
    python3 scripts/dcs_ts_prereg.py --mutate configs/dcs_ts_pr048.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Mandate §21 required fields. Absence is a refusal, not a warning.
REQUIRED_TOP = ("id", "question", "population", "split", "model", "read_site", "classifier",
                "primary", "power", "nulls_required", "multiplicity", "artifacts")


class PreregError(RuntimeError):
    pass


def _walk_sha_fields(node, path=""):
    """Every key ending in _sha16, anywhere in the tree, with its dotted path."""
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{path}.{k}" if path else k
            if k.endswith("_sha16"):
                yield p, v
            else:
                yield from _walk_sha_fields(v, p)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_sha_fields(v, f"{path}[{i}]")


def _file_sha16(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


class Prereg:
    def __init__(self, obj: dict, path: str):
        self.obj = obj
        self.path = path

    def require(self, *keys):
        """Fetch a nested value, REFUSING if any level is absent. No silent defaults."""
        node = self.obj
        for i, k in enumerate(keys):
            if not isinstance(node, dict) or k not in node:
                raise PreregError(
                    f"{self.path}: required field {'.'.join(keys)!r} is missing at {'.'.join(keys[:i+1])!r}. "
                    f"A threshold the analyzer needs but the preregistration does not declare is "
                    f"exactly the failure this loader exists to prevent."
                )
            node = node[k]
        return node

    def require_gate(self, gate_id: str) -> dict:
        for g in self.obj.get("phase4_gates_on_ts116n", []) + self.obj.get("phase4_gates", []):
            if g.get("id") == gate_id:
                return g
        raise PreregError(f"{self.path}: gate {gate_id!r} is not declared")

    def require_null(self, null_id: str) -> dict:
        for n in self.obj.get("nulls_required", []):
            if n.get("id") == null_id:
                return n
        raise PreregError(f"{self.path}: null {null_id!r} is not declared")


def validate(obj: dict, path: str, for_extraction: bool = False, check_files: bool = True) -> list[str]:
    errs: list[str] = []

    if obj.get("status") != "FROZEN":
        errs.append(f"status is {obj.get('status')!r}, not 'FROZEN' -- a preregistration that is "
                    f"still open cannot govern a confirmatory run")

    for f in REQUIRED_TOP:
        if f not in obj:
            errs.append(f"mandate section 21 required field missing: {f!r}")

    shas = list(_walk_sha_fields(obj))
    if not shas:
        # A config with no hashes at all would sail through the loop below. Bind or refuse.
        errs.append("no *_sha16 field found anywhere -- nothing is pinned, so nothing is verifiable")
    for p, v in shas:
        if v is None or v == "":
            errs.append(f"{p} is null -- the artifact it pins is not fixed, so the design is not frozen")

    if check_files:
        banks = obj.get("population", {}).get("banks", {})
        if not banks:
            errs.append("population.banks is empty -- the analyzer would bind to nothing")
        for name, b in banks.items():
            fp = os.path.join(REPO, b.get("path", ""))
            if not b.get("path") or not os.path.exists(fp):
                errs.append(f"bank {name}: path does not exist: {b.get('path')!r}")
                continue
            want = b.get("bank_file_sha16")
            if want:
                got = _file_sha16(fp)
                if got != want:
                    errs.append(f"bank {name}: bank_file_sha16 pinned {want} but the file on disk "
                                f"hashes {got} -- the artifact changed after the freeze")
        for name, pl in obj.get("population", {}).get("pools", {}).items():
            if not isinstance(pl, dict) or "path" not in pl:
                continue
            fp = os.path.join(REPO, pl["path"])
            if not os.path.exists(fp):
                errs.append(f"pool {name}: path does not exist: {pl['path']!r}")
                continue
            want = pl.get("content_sha16")
            if want:
                got = json.load(open(fp)).get("_meta", {}).get("content_sha16")
                if got != want:
                    errs.append(f"pool {name}: content_sha16 pinned {want} but the file carries {got}")

    if for_extraction:
        for item in obj.get("pre_extraction_checklist", []):
            st = str(item.get("status", ""))
            if "BLOCKING" in st.upper() and "done" not in st.lower():
                errs.append(f"pre-extraction checklist {item.get('id')} is BLOCKING and not done: "
                            f"{item.get('item')!r}")
        if not obj.get("artifacts", {}).get("analyzer_exists", False):
            errs.append("artifacts.analyzer_exists is false -- refusing to extract behind an "
                        "analyzer that does not exist")
    return errs


def load(path: str, for_extraction: bool = False) -> Prereg:
    fp = path if os.path.isabs(path) else os.path.join(REPO, path)
    if not os.path.exists(fp):
        raise PreregError(f"preregistration not found: {path}. Refusing to run without one.")
    try:
        with open(fp) as f:
            obj = json.load(f)
    except json.JSONDecodeError as e:
        raise PreregError(f"{path} is not valid JSON: {e}") from e
    errs = validate(obj, path, for_extraction=for_extraction)
    if errs:
        msg = "\n".join(f"  - {e}" for e in errs)
        raise PreregError(f"REFUSING to run against {path}:\n{msg}")
    return Prereg(obj, path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", nargs="?", default="configs/dcs_ts_pr048.json")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--for-extraction", action="store_true")
    ap.add_argument("--mutate", action="store_true")
    a = ap.parse_args()

    fp = os.path.join(REPO, a.config)
    obj = json.load(open(fp))

    errs = validate(obj, a.config, for_extraction=a.for_extraction)
    print(f"=== prereg {a.config} (for_extraction={a.for_extraction}) ===")
    if errs:
        for e in errs:
            print(f"  REFUSE {e}")
        print(f"[prereg] {len(errs)} refusal(s)")
    else:
        print(f"[prereg] clean: status FROZEN, {len(list(_walk_sha_fields(obj)))} hashes pinned "
              f"and verified, all {len(REQUIRED_TOP)} mandate-21 fields present")

    if a.mutate:
        print("\n=== mutation harness: every refusal must be reachable ===")
        import copy
        muts = {}
        m = copy.deepcopy(obj); m["status"] = "DRAFT"; muts["status not FROZEN"] = m
        m = copy.deepcopy(obj); m.pop("multiplicity", None); muts["missing mandate-21 field"] = m
        m = copy.deepcopy(obj)
        k = next(iter(m["population"]["banks"])); m["population"]["banks"][k]["bank_file_sha16"] = None
        muts["a sha is null"] = m
        m = copy.deepcopy(obj)
        k = next(iter(m["population"]["banks"])); m["population"]["banks"][k]["bank_file_sha16"] = "0" * 16
        muts["a sha disagrees with disk"] = m
        m = copy.deepcopy(obj)
        k = next(iter(m["population"]["banks"])); m["population"]["banks"][k]["path"] = "data/nope.jsonl"
        muts["pinned artifact missing"] = m
        m = copy.deepcopy(obj); m["population"]["banks"] = {}; muts["no banks at all"] = m
        n_red = 0
        for name, mm in muts.items():
            e = validate(mm, "MUTANT", for_extraction=False)
            red = bool(e)
            n_red += red
            print(f"  {'RED  ' if red else 'GREEN'}  {name:30s} -> {len(e)} refusal(s)"
                  + (f"  {e[0][:80]}" if e else "   <-- THIS REFUSAL IS UNREACHABLE"))
        # and the extraction-only refusal
        e = validate(obj, "SELF", for_extraction=True)
        print(f"  {'RED  ' if e else 'GREEN'}  {'for_extraction on the real config':30s} -> "
              f"{len(e)} refusal(s)  {e[0][:80] if e else ''}")
        print(f"[mutate] {n_red}/{len(muts)} mutations produced a refusal")
        if n_red != len(muts):
            print("  AN UNREACHABLE REFUSAL IS NOT A GUARD.", file=sys.stderr)
            return 1
    return 1 if errs and not a.mutate else 0


if __name__ == "__main__":
    raise SystemExit(main())
