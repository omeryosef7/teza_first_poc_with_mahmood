"""common.py — shared plumbing for the Boombness sprint (docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md).

Deliberately thin. Everything model-side is delegated to the mature helpers that already
exist in `doublespeak_causality/` (ds_common, pair_common); this module only supplies:

  1. the sys.path bootstrap that makes `import ds_common as dc` work from `src/boombness/`;
  2. the plan §2.1 run-directory contract (config.json / metadata.json / results.jsonl /
     summary.json / plots/), implemented on top of the house `ds_common.write_runmeta`
     so Boombness runs are both plan-compliant and consistent with every other run in
     this repo;
  3. seeding, and a failure ledger that makes plan §2.2 ("no silent failures") mechanical
     rather than a thing we have to remember.

House conventions inherited from ds_common / pair_common and NOT re-litigated here:
  * 0-indexed block L  <->  hidden_states[L+1];  hidden_states[0] is the embedding.
  * Token positions are resolved on the ALREADY-TEMPLATED string with
    add_special_tokens=False, so indices line up with generation (double-BOS trap).
"""
from __future__ import annotations

import json
import os
import random
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

# --------------------------------------------------------------------------- #
# Paths / bootstrap
# --------------------------------------------------------------------------- #
HERE = os.path.dirname(os.path.abspath(__file__))
SRC_ROOT = os.path.dirname(HERE)                       # <repo>/src
REPO_ROOT = os.path.dirname(SRC_ROOT)                  # <repo>
DS_DIR = os.path.join(REPO_ROOT, "doublespeak_causality")
DATA_DIR = os.path.join(REPO_ROOT, "data", "boombness_prompts")
OUT_ROOT = os.path.join(REPO_ROOT, "outputs", "boombness")
CONFIG_DIR = os.path.join(REPO_ROOT, "configs", "boombness")

if DS_DIR not in sys.path:
    sys.path.insert(0, DS_DIR)


def ds():
    """Import and return the house `ds_common` module (lazily, so CPU-only tools work)."""
    import ds_common as dc  # noqa: E402  (deliberate late import)
    return dc


def pair():
    """Import and return the house `pair_common` module."""
    import pair_common as pc  # noqa: E402
    return pc


# --------------------------------------------------------------------------- #
# Seeding
# --------------------------------------------------------------------------- #
def seed_everything(seed: int) -> int:
    """Seed python/numpy/torch. Returns the seed so callers can log it."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        pass
    return seed


# --------------------------------------------------------------------------- #
# Failure ledger (plan §2.2)
# --------------------------------------------------------------------------- #
@dataclass
class FailureLedger:
    """Counts every example we did NOT successfully process, with a reason.

    Plan §2.2: "Never report only successful subsets without saying how many failed."
    A run's summary.json is only allowed to be written through `RunDir.finish`, which
    refuses to omit this block.
    """
    attempted: int = 0
    succeeded: int = 0
    failures: Dict[str, int] = field(default_factory=dict)
    examples: Dict[str, List[str]] = field(default_factory=dict)

    def ok(self, n: int = 1) -> None:
        self.attempted += n
        self.succeeded += n

    def fail(self, reason: str, ident: str = "", n: int = 1) -> None:
        self.attempted += n
        self.failures[reason] = self.failures.get(reason, 0) + n
        if ident:
            xs = self.examples.setdefault(reason, [])
            if len(xs) < 10:                      # ids only, never prompt text
                xs.append(str(ident))

    @property
    def n_failed(self) -> int:
        return sum(self.failures.values())

    def as_dict(self) -> Dict[str, Any]:
        return {
            "n_attempted": self.attempted,
            "n_succeeded": self.succeeded,
            "n_failed": self.n_failed,
            "failure_reasons": dict(sorted(self.failures.items())),
            "failure_example_ids": {k: v for k, v in sorted(self.examples.items())},
        }


# --------------------------------------------------------------------------- #
# Run directory contract (plan §2.1)
# --------------------------------------------------------------------------- #
class RunDir:
    """Plan §2.1 output contract, layered on the house RUNMETA/DONE contract.

    Produces, under outputs/boombness/<experiment>/<run_id>/:
        config.json     resolved configuration (argparse namespace + explicit extras)
        metadata.json   provenance: git commit+dirty, model/tokenizer/revision, dataset,
                        seed, command, timestamps, slurm id, gpu, counts
        results.jsonl   one row per unit of analysis
        summary.json    aggregates + the failure ledger
        plots/          figures
        cache/          large tensors (only if the run asks for it)
        RUNMETA.json    house convention (written by ds_common.write_runmeta)
        DONE.json       house convention (written on successful finish)

    Usage:
        run = RunDir("aggressive_patching", args, tag="smoke")
        run.log_row({...}); ...
        run.finish(summary={...}, ledger=ledger)
    """

    def __init__(self, experiment: str, args: Any = None, tag: str = "",
                 run_id: Optional[str] = None, out_root: Optional[str] = None,
                 want_cache: bool = False):
        stamp = time.strftime("%Y%m%d_%H%M%S")
        self.experiment = experiment
        self.run_id = run_id or (f"{tag}_{stamp}_{os.getpid()}" if tag else f"{stamp}_{os.getpid()}")
        root = out_root or OUT_ROOT
        self.path = os.path.join(root, experiment, self.run_id)
        self.plots = os.path.join(self.path, "plots")
        self.cache = os.path.join(self.path, "cache")
        os.makedirs(self.plots, exist_ok=True)
        if want_cache:
            os.makedirs(self.cache, exist_ok=True)

        # A reused run directory would silently DOUBLE its results, because log_row appends.
        # run_id carries a timestamp and a pid so a collision means something is wrong; fail
        # rather than produce a file whose row count no longer matches the ledger.
        if os.path.exists(os.path.join(self.path, "results.jsonl")):
            raise FileExistsError(
                f"{self.path}/results.jsonl already exists — refusing to append to an existing "
                "run directory (rows would silently duplicate). Use a new run_id/tag.")

        self._args = args
        self._results_fh = None
        self._n_rows = 0
        self._t0 = time.time()
        self._extra_meta: Dict[str, Any] = {}

        # House provenance first (plan §2.1 wants it written as the FIRST action).
        try:
            ds().write_runmeta(self.path, args=args, extra={"experiment": experiment,
                                                            "plan": "BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md"})
        except Exception as e:                                        # never fatal
            self._extra_meta["_runmeta_error"] = repr(e)[:300]

        cfg = {}
        if args is not None:
            cfg = dict(vars(args)) if hasattr(args, "__dict__") else dict(args)
        self.write_json("config.json", {"experiment": experiment, "run_id": self.run_id,
                                        "args": _jsonable(cfg)})

    # -- io ---------------------------------------------------------------- #
    def p(self, *parts: str) -> str:
        return os.path.join(self.path, *parts)

    def write_json(self, name: str, obj: Any) -> str:
        path = self.p(name)
        with open(path, "w") as f:
            json.dump(_jsonable(obj), f, indent=2)
        return path

    def log_row(self, row: Dict[str, Any]) -> None:
        """Append one result row to results.jsonl (flushed, so a killed job keeps its rows)."""
        if self._results_fh is None:
            self._results_fh = open(self.p("results.jsonl"), "a")
        self._results_fh.write(json.dumps(_jsonable(row)) + "\n")
        self._results_fh.flush()
        self._n_rows += 1

    def note_model(self, model_id: str, revision: Optional[str] = None,
                   tokenizer_id: Optional[str] = None, dtype: Optional[str] = None,
                   attn_implementation: Optional[str] = None, **kw) -> None:
        self._extra_meta.update({"model": model_id, "model_revision": revision,
                                 "tokenizer": tokenizer_id or model_id, "dtype": dtype,
                                 "attn_implementation": attn_implementation, **kw})

    def note(self, **kw) -> None:
        self._extra_meta.update(kw)

    def note_bank(self, bank_path: str) -> None:
        """Record CONTENT hashes of the prompt bank, not just its path.

        TWO HASHES, TWO NAMES (defect T11, 2026-08-18). This method and
        `prompt_families.generate_bank` both wrote a key literally called `bank_content_sha16`,
        and they computed DIFFERENT FUNCTIONS: this one hashes the FILE BYTES
        (71bea179345ed118 for the committed 2352-row bank), `prompt_families` hashes the
        concatenation of the per-row `prompt_sha16` values sorted by `prompt_id`
        (7002854cf834e9f9 for the same bank). The report header quoted the first, the bank's
        progress/meta record the second, and nothing ever compared them -- so the identifier that
        the docstring below calls the defence against a mismatched join could not detect one,
        because the two ends of the join were never the same function. That is the fourth dead
        guard of this sprint, and the most self-defeating: it reads as though it had been checked.

        Both are now computed and stored under DISTINCT names:
            bank_file_sha16  sha256 of the raw file bytes, truncated to 16 hex chars.
                             Sensitive to key order and whitespace; the right thing to compare
                             when asking "is this literally the same file".
            bank_rows_sha16  sha256 over "|".join(prompt_sha16 sorted by prompt_id) -- byte-for-byte
                             the function in prompt_families -- so a run's metadata can be compared
                             against the bank's own *_meta.json. None when the rows carry no
                             `prompt_sha16` (external banks, plan 14 / ClearHarm).
        The legacy ambiguous key is NO LONGER WRITTEN. `bank_hashes()` below reads old artifacts.

        PROVENANCE FIX (audit B5, 2026-08-17). Runs recorded a bank path and a row count, but the
        bank at that path has been regenerated three times this sprint (1464 -> 1752 -> 2352 rows).
        The phase board ended up citing 1752-row evidence for runs that had actually consumed 1464,
        and re-running any upstream job today would silently consume a different bank. Retraction
        R1's stated root cause was joining across bank regenerations via a `prompt_id` that does not
        hash prompt text; nothing has gone wrong yet only because the four headline runs happen to
        agree. A content hash makes a mismatched join detectable instead of invisible.
        """
        if not bank_path:
            self._extra_meta.update({"bank_path": None, "bank_file_sha16": None,
                                     "bank_rows_sha16": None})
            return
        import hashlib
        h, n = hashlib.sha256(), 0
        id_sha_pairs: List[Any] = []
        rows_hashable = True
        try:
            with open(bank_path, "rb") as f:
                for line in f:
                    h.update(line)
                    if not line.strip():
                        continue
                    n += 1
                    if rows_hashable:
                        try:
                            r = json.loads(line)
                            id_sha_pairs.append((str(r["prompt_id"]), str(r["prompt_sha16"])))
                        except Exception:
                            # No per-row shas (external bank, or not jsonl): the rows-hash is not
                            # defined for this file. Say so with None; never fall back to the file
                            # hash under the rows name, which is the exact conflation being fixed.
                            rows_hashable = False
                            id_sha_pairs = []
        except OSError as e:
            self._extra_meta.update({"bank_path": bank_path, "bank_file_sha16": None,
                                     "bank_rows_sha16": None, "bank_hash_error": str(e)})
            return
        self._extra_meta.update({"bank_path": os.path.abspath(bank_path),
                                 "bank_file_sha16": h.hexdigest()[:16],
                                 "bank_rows_sha16": rows_sha16(id_sha_pairs) if id_sha_pairs else None,
                                 "bank_n_rows": n})

    def finish(self, summary: Optional[Dict[str, Any]] = None,
               ledger: Optional[FailureLedger] = None) -> str:
        """Write metadata.json + summary.json + DONE.json. Ledger is MANDATORY (plan §2.2)."""
        if ledger is None:
            raise ValueError(
                "RunDir.finish requires a FailureLedger — plan §2.2 forbids reporting a "
                "successful subset without stating how many examples failed and why.")
        if self._results_fh is not None:
            self._results_fh.close()
            self._results_fh = None

        dc = ds()
        try:
            env = dc.env_metadata()
        except Exception as e:
            env = {"_env_error": repr(e)[:300]}

        meta = {
            "schema": "BOOMBNESS_META/1",
            "experiment": self.experiment,
            "run_id": self.run_id,
            "plan": "docs/BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md",
            "command": " ".join(sys.argv),
            "argv": list(sys.argv),
            "python_executable": sys.executable,
            "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
            "slurm_nodelist": os.environ.get("SLURM_NODELIST"),
            "n_result_rows": self._n_rows,
            "wall_seconds": round(time.time() - self._t0, 2),
            "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            **env,
            **self._extra_meta,
        }
        try:
            meta["git_dirty"] = dc.git_dirty()
        except Exception:
            pass
        self.write_json("metadata.json", meta)

        summ = dict(summary or {})
        summ["failures"] = ledger.as_dict()
        summ["n_result_rows"] = self._n_rows
        self.write_json("summary.json", summ)

        try:
            dc.write_done(self.path, rows_written=self._n_rows,
                          extra={"experiment": self.experiment})
        except Exception:
            self.write_json("DONE.json", {"ok": True, "n_result_rows": self._n_rows,
                                          "finished_at": meta["finished_at"]})
        return self.path


    def abort(self, reason: str, summary: Optional[Dict[str, Any]] = None,
              ledger: Optional[FailureLedger] = None) -> str:
        """Close a run that tripped an abort gate: metadata + summary + ABORTED.json, NO DONE.json.

        ADDED 2026-08-18 for defect T12. `judge_boombness` wrote DONE.json (via `finish`) and only
        THEN evaluated its null-judgement abort gate, so a run that tripped the gate -- the plan
        3.6 house rule is "STOP, do not treat null as benign" -- still satisfied `require_done` and
        every downstream analyzer would read its ASR as a finished number. The process exit code
        said 1; the artifact on disk said DONE. Only one of those two is what a re-run, a phase
        board, or a colleague three weeks later actually consults.

        `require_done` already refuses a directory carrying ABORTED.json, so writing that marker
        instead of DONE is what makes the gate reach the consumer side.
        """
        self.note(aborted=True, abort_reason=reason)
        if self._results_fh is not None:
            self._results_fh.close()
            self._results_fh = None
        summ = dict(summary or {})
        summ["aborted"] = True
        summ["abort_reason"] = reason
        if ledger is not None:
            summ["failures"] = ledger.as_dict()
        summ["n_result_rows"] = self._n_rows
        meta = {"schema": "BOOMBNESS_META/1", "experiment": self.experiment,
                "run_id": self.run_id, "aborted": True, "abort_reason": reason,
                "command": " ".join(sys.argv), "n_result_rows": self._n_rows,
                "wall_seconds": round(time.time() - self._t0, 2),
                "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"), **self._extra_meta}
        self.write_json("metadata.json", meta)
        self.write_json("summary.json", summ)
        self.write_json("ABORTED.json", {"ok": False, "reason": reason,
                                         "n_result_rows": self._n_rows,
                                         "aborted_at": meta["finished_at"]})
        done = self.p("DONE.json")
        if os.path.exists(done):
            # Belt and braces: if some earlier code path already declared success, the abort must
            # win. A directory holding BOTH markers is worse than either.
            os.replace(done, self.p("DONE.json.retracted_by_abort"))
        return self.path


def _jsonable(obj: Any, _d: int = 0) -> Any:
    if _d > 8:
        return repr(obj)[:400]
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _jsonable(v, _d + 1) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_jsonable(v, _d + 1) for v in obj]
    for attr in ("tolist", "item"):
        if hasattr(obj, attr):
            try:
                return _jsonable(getattr(obj, attr)(), _d + 1)
            except Exception:
                pass
    return repr(obj)[:400]



def _ledger_counts(run_dir: str) -> Dict[str, Any]:
    """Read the failure-ledger counts out of summary.json, if present. Best-effort by design:
    a run whose summary is unreadable is not thereby declared empty."""
    try:
        with open(os.path.join(run_dir, "summary.json")) as f:
            return (json.load(f) or {}).get("failures") or {}
    except Exception:
        return {}


def require_done(run_dir: str, allow_partial: bool = False) -> Dict[str, Any]:
    """Refuse to analyse a run that never finished. Returns the DONE payload.

    ADDED 2026-08-17 after the mid-session sweep found that NO analyzer checked this. The
    completeness invariant was written only on the PRODUCER side (`RunDir.finish` writes DONE.json)
    and never read on the CONSUMER side, so every analysis script would happily compute a headline
    number over a truncated run. At the moment the sweep ran there were SEVEN such directories on
    disk — including two stale-dead ones from hours earlier that look full-sized (4002 and 724 rows)
    and would not announce themselves as partial.

    This is the same shape as the sprint's three dead guards and its four one-of-two-paths bugs: an
    invariant asserted at one end of a contract and never checked at the other. `allow_partial`
    exists so that deliberately inspecting a running job stays possible, but it must be asked for.
    """
    d = os.path.join(run_dir, "DONE.json")
    if os.path.exists(d):
        try:
            with open(d) as f:
                payload = json.load(f)
        except Exception:
            payload = {}
        # A FINISHED run is not necessarily a run that PRODUCED anything. `finish()` writes
        # DONE.json whenever the ledger is present, including when every unit failed, so a run
        # with n_succeeded = 0 was indistinguishable from a complete one to this function --
        # the same assert-at-one-end/never-check-at-the-other shape this guard exists to close.
        # Found 2026-08-18 by a tokenization_audit run that could not load the tokenizer (401 on
        # a gated repo), recorded n_attempted=1 / n_succeeded=0, wrote NO results.jsonl, and still
        # presented as DONE. §2.4 is a mandatory gate, so that run would have passed it vacuously.
        led = _ledger_counts(run_dir)
        if led and led.get("n_attempted", 0) > 0 and led.get("n_succeeded", 0) == 0:
            if allow_partial:
                print(f"[require_done] WARNING: {os.path.basename(run_dir)} finished but "
                      f"0/{led['n_attempted']} units succeeded; continuing only because "
                      f"--allow-partial was passed. Nothing from it may be reported.")
                return payload
            raise SystemExit(
                f"[require_done] REFUSING: {run_dir} has DONE.json but its failure ledger records "
                f"0 of {led['n_attempted']} units succeeded "
                f"(reasons: {led.get('failure_reasons')}). The run finished; it produced nothing. "
                f"Pass --allow-partial only to inspect it, never to report from it.")
        return payload
    if os.path.exists(os.path.join(run_dir, "ABORTED.json")):
        raise SystemExit(f"[require_done] {run_dir} is marked ABORTED — it holds no usable data.")
    n = 0
    rp = os.path.join(run_dir, "results.jsonl")
    if os.path.exists(rp):
        with open(rp) as f:
            n = sum(1 for _ in f)
    if allow_partial:
        print(f"[require_done] WARNING: {os.path.basename(run_dir)} has NO DONE.json "
              f"({n} rows) — analysing a PARTIAL run because --allow-partial was passed. "
              f"Nothing computed from it may be reported.")
        return {}
    raise SystemExit(
        f"[require_done] REFUSING: {run_dir} has no DONE.json, so the run did not finish and its "
        f"{n} rows are a truncated prefix of unknown length. Any number computed from it would be "
        f"over partial data with no failure accounting. Wait for the run, or pass --allow-partial "
        f"to inspect it deliberately (its output must not be reported).")

# --------------------------------------------------------------------------- #
# Bank identity: TWO hashes, TWO names (defect T11, 2026-08-18)
# --------------------------------------------------------------------------- #
# `RunDir.note_bank` hashed the bank's FILE BYTES and `prompt_families.generate_bank` hashed the
# concatenated per-row `prompt_sha16` values -- and both wrote the result under the single key
# `bank_content_sha16`. Two functions, one name, never compared: the report header quoted
# 71bea179345ed118 (file bytes) and the bank meta quoted 7002854cf834e9f9 (rows), as if they were
# one identifier. A reader who checked "the hashes are different, so the join is wrong" would have
# been wrong; a reader who checked "they are equal" could never see a true mismatch, because the
# two values are never equal for any input. The guard was dead on arrival.
#
# The fix is naming plus an actual comparison:
#   bank_file_sha16  sha256(raw file bytes)[:16]              -- "the same file"
#   bank_rows_sha16  sha256("|".join(prompt_sha16 by id))[:16] -- "the same prompts"
# `rows_sha16` is the ONE implementation of the second; prompt_families calls it too, so the two
# ends of the join cannot drift apart again by editing one of two copies (the one-of-two-paths
# shape this sprint has now hit six times).

LEGACY_BANK_HASH_KEY = "bank_content_sha16"


def rows_sha16(id_sha_pairs) -> str:
    """sha16 over the bank's per-row prompt hashes, ordered by prompt_id.

    Accepts a mapping {prompt_id: prompt_sha16} or an iterable of (prompt_id, prompt_sha16)
    pairs. Pairs are preferred: a bank with a DUPLICATED prompt_id would silently lose a row
    through a mapping, and "the two banks hash the same" must not be reachable by losing rows.
    Verified against the committed 2352-row bank: both spellings give 7002854cf834e9f9, which is
    the value `data/boombness_prompts/boombness_prompt_bank_meta.json` already carries.
    """
    import hashlib
    pairs = list(id_sha_pairs.items()) if isinstance(id_sha_pairs, dict) else list(id_sha_pairs)
    pairs.sort(key=lambda kv: str(kv[0]))
    return hashlib.sha256("|".join(str(v) for _, v in pairs).encode()).hexdigest()[:16]


def bank_hashes(obj: Dict[str, Any], legacy: str = "file") -> Dict[str, Optional[str]]:
    """Read bank identity out of an artifact dict, old spelling or new.

    `obj` may be a run's metadata.json, a summary.json, or a bank *_meta.json `stats` block.
    Artifacts written before 2026-08-18 carry only the ambiguous `bank_content_sha16`; what it
    MEANS depends on who wrote it, which is precisely the defect -- so the caller must say:
        legacy="file"  for a run metadata.json (RunDir.note_bank wrote file bytes)
        legacy="rows"  for a bank meta / prompt_families stats block
    As of this session, on disk: 80 committed run metadata.json files carry the legacy key with a
    file-bytes value (74 of them 71bea179345ed118, plus 3+3 from two other banks), and one bank
    meta carries it with a rows value (7002854cf834e9f9). Nothing else reads the key at all.
    """
    if legacy not in ("file", "rows"):
        raise ValueError("legacy must be 'file' or 'rows'")
    out = {"bank_file_sha16": obj.get("bank_file_sha16"),
           "bank_rows_sha16": obj.get("bank_rows_sha16"),
           "legacy_key_present": LEGACY_BANK_HASH_KEY in obj,
           "legacy_interpreted_as": None}
    legacy_val = obj.get(LEGACY_BANK_HASH_KEY)
    if legacy_val and out[f"bank_{legacy}_sha16"] is None:
        out[f"bank_{legacy}_sha16"] = legacy_val
        out["legacy_interpreted_as"] = legacy
    return out


def compare_bank_hashes(run_meta: Dict[str, Any], bank_meta: Dict[str, Any],
                        strict: bool = True) -> Dict[str, Any]:
    """The comparison `note_bank`'s docstring promised and nobody ever wrote.

    `run_meta`  a run's metadata.json (or any dict from `RunDir.note_bank`).
    `bank_meta` the bank's *_meta.json -- either the whole file or its `stats` block.

    Returns a verdict dict; raises SystemExit on a real mismatch when `strict`. A hash that is
    simply ABSENT on one side is reported as `unknown`, never as agreement: an old artifact that
    predates the rows hash must not be able to certify a join it never recorded.
    """
    stats = bank_meta.get("stats") if isinstance(bank_meta.get("stats"), dict) else bank_meta
    a = bank_hashes(run_meta, legacy="file")
    b = bank_hashes(stats, legacy="rows")
    verdict: Dict[str, Any] = {"run_bank_path": run_meta.get("bank_path"),
                               "run": {k: a[k] for k in ("bank_file_sha16", "bank_rows_sha16")},
                               "bank": {k: b[k] for k in ("bank_file_sha16", "bank_rows_sha16")},
                               "checked": [], "mismatched": [], "unknown": []}
    for key in ("bank_file_sha16", "bank_rows_sha16"):
        if a[key] and b[key]:
            verdict["checked"].append(key)
            if a[key] != b[key]:
                verdict["mismatched"].append(key)
        else:
            verdict["unknown"].append(key)
    verdict["ok"] = bool(verdict["checked"]) and not verdict["mismatched"]
    if strict and verdict["mismatched"]:
        raise SystemExit(
            f"[compare_bank_hashes] REFUSING: the run consumed a DIFFERENT bank than the one it is "
            f"being joined against: {[(k, a[k], b[k]) for k in verdict['mismatched']]}. This bank "
            f"has been regenerated three times this sprint (1464 -> 1752 -> 2352 rows); joining "
            f"across regenerations by prompt_id is retraction R1's stated root cause.")
    return verdict


# --------------------------------------------------------------------------- #
# Direction-payload provenance (defect T8, 2026-08-18)
# --------------------------------------------------------------------------- #
def validate_direction_payload(payload: Dict[str, Any], path: str = "", model: Any = None,
                               position: Optional[str] = None,
                               layers: Optional[Iterable[int]] = None,
                               strict: bool = True) -> Dict[str, Any]:
    """Check a `--fit-dir` payload's OWN meta against the run that is about to consume it.

    WHY THIS EXISTS. Every consumer of `--fit-dir` (extract_boombness.main,
    aggressive_patching, surgical_knockout) `torch.load`s `directions_fit_<split>.pt` and reads
    `payload[name][L]` -- and not one of them ever read `payload["meta"]`, which records the
    `position`, the `model` and the layer set the directions were FITTED on. The 2026-08-17
    phantom-cell fix added a per-row assertion that the READOUT index matches `--position`; that
    proves where h was READ, not where d was FITTED. So the original phantom cell -- fit at one
    position, applied at another -- still passed every guard in the repo, as does the worse
    cross-MODEL version (a Llama-fitted d_surface projected onto Qwen3 activations, which yields
    perfectly plausible cosines because nothing about the arithmetic complains).

    LATENCY VERIFIED, 2026-08-18, before writing the fix: 70 committed run directories under
    outputs/boombness carry a `fit_dir` in config.json (57 score_behavior, 6 surgical_knockout,
    5 aggressive_patching, 2 extract_boombness), resolving to 3 distinct fit runs. Loading each
    payload's meta and comparing it to the consuming run's own model and position gives 0
    mismatches: all Llama runs consume the Llama fit at codeword_last, all Qwen3 runs consume the
    Qwen3 fit at codeword_last. No committed number moves. The guard is closing a hole, not
    correcting a result.

    Returns the verdict dict (also suitable for `run.note`). Raises SystemExit when `strict` and
    anything mismatches, because the alternative -- a warning in a log nobody reads -- is how the
    three dead guards died.
    """
    meta = payload.get("meta") if isinstance(payload, dict) else None
    v: Dict[str, Any] = {"path": path, "fit_meta_present": isinstance(meta, dict),
                         "problems": [], "checked": []}
    if not isinstance(meta, dict):
        # An UNLABELLED payload is not a passing payload. Anything that old predates
        # signals.estimate_directions' meta block, so it cannot be shown to match anything.
        v["problems"].append("payload has no `meta` block: provenance unknowable")
        if strict:
            raise SystemExit(f"[validate_direction_payload] REFUSING {path or 'payload'}: no "
                             f"`meta` block, so the position/model it was fitted at cannot be "
                             f"checked against this run.")
        return v

    v["fit_position"] = meta.get("position")
    v["fit_model"] = meta.get("model")
    v["fit_split"] = meta.get("split_fitted_on")
    v["fit_layers_n"] = len(payload.get("layers") or [])

    if position is not None and meta.get("position") is not None:
        v["checked"].append("position")
        if meta["position"] != position:
            v["problems"].append(
                f"position: directions were FITTED at {meta['position']!r} but this run reads at "
                f"{position!r} -- the phantom cell, exactly")
    elif position is not None:
        v["problems"].append("position: payload meta records no position to check against")

    if model is not None and meta.get("model") is not None:
        v["checked"].append("model")
        # Compare on the repo-id BASENAME: callers legitimately pass either the bare id or the
        # local snapshot path for the same weights, and a false alarm here would train people to
        # pass --skip-... flags, which is how a guard becomes decoration.
        a, b = os.path.basename(str(meta["model"])), os.path.basename(str(model))
        if a != b:
            v["problems"].append(
                f"model: directions were FITTED on {meta['model']!r} but this run is {model!r} -- "
                f"a direction from another model's residual basis produces plausible cosines and "
                f"means nothing")
    elif model is not None:
        v["problems"].append("model: payload meta records no model to check against")

    if layers is not None:
        want = sorted(set(int(L) for L in layers))
        have = set(int(L) for L in (payload.get("layers") or []))
        missing = [L for L in want if L not in have]
        v["checked"].append("layers")
        v["n_layers_requested"] = len(want)
        v["n_layers_missing_from_fit"] = len(missing)
        v["layers_missing_from_fit"] = missing[:64]
        if missing:
            # NOT fatal by itself: a deliberately layer-subsetted fit (the Qwen3 depth sweep fits
            # 14 of 40 blocks) is a legitimate thing to consume. It IS the upstream cause of T8b,
            # so it must be counted and surfaced rather than discovered later as a column of
            # blanks; the consumer reports per-layer coverage in its own summary.json.
            v["problems_nonfatal"] = [
                f"layers: {len(missing)} of {len(want)} requested block layers have no fitted "
                f"direction ({missing[:8]}{'...' if len(missing) > 8 else ''}); every direction "
                f"column at those layers will be ABSENT from results.jsonl"]

    if strict and v["problems"]:
        raise SystemExit(f"[validate_direction_payload] REFUSING {path or 'payload'}: "
                         + " | ".join(v["problems"]))
    return v


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def write_jsonl(path: str, rows: Iterable[Dict[str, Any]]) -> int:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    n = 0
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(_jsonable(r)) + "\n")
            n += 1
    return n


def clustered_proportion_ci(flags, clusters, n_boot: int = 4000, seed: int = 20260818,
                            alpha: float = 0.05):
    """Percentile CI for a proportion whose observations are CLUSTERED, by resampling CLUSTERS.

    WHY. Every ASR interval in this sprint was a Wilson binomial with z=1.96 over PROMPTS
    (`judge_boombness.wilson`, `analyze_steering.wilson`), i.e. it treated the 270 prompts of an arm
    as 270 independent Bernoulli draws. They are not: they are 6 domains x ~45 prompts, and prompts
    within a domain share a stem, a demo pool and a target. Audit 11 measured the consequence as
    roughly a 1.9x understatement of the interval. Every OTHER inference in this sprint clusters on
    domain (analyze_g2, analyze_g8, analyze_g9, analyze_position, reanalyze_corrected), so the
    headline number was the only one that did not.

    Returns (lo, hi, n_clusters). The Wilson interval is still reported beside it, labelled iid, so
    the two are visibly different rather than one silently replacing the other.
    """
    import random as _random
    by = {}
    for f, c in zip(flags, clusters):
        by.setdefault(c, []).append(1.0 if f else 0.0)
    keys = sorted(by, key=str)
    G = len(keys)
    if G < 2:
        return (float("nan"), float("nan"), G)
    rng = _random.Random(seed)
    means = []
    for _ in range(n_boot):
        draw = [by[keys[rng.randrange(G)]] for _ in range(G)]
        tot = [v for d in draw for v in d]
        if tot:
            means.append(sum(tot) / len(tot))
    if not means:
        return (float("nan"), float("nan"), G)
    means.sort()
    lo = means[int(alpha / 2 * len(means))]
    hi = means[min(len(means) - 1, int((1 - alpha / 2) * len(means)))]
    return (lo, hi, G)
