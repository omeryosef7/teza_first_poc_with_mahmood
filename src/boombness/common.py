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
        """Record the CONTENT hash of the prompt bank, not just its path.

        PROVENANCE FIX (audit B5, 2026-08-17). Runs recorded a bank path and a row count, but the
        bank at that path has been regenerated three times this sprint (1464 -> 1752 -> 2352 rows).
        The phase board ended up citing 1752-row evidence for runs that had actually consumed 1464,
        and re-running any upstream job today would silently consume a different bank. Retraction
        R1's stated root cause was joining across bank regenerations via a `prompt_id` that does not
        hash prompt text; nothing has gone wrong yet only because the four headline runs happen to
        agree. A content hash makes a mismatched join detectable instead of invisible.
        """
        import hashlib
        h, n = hashlib.sha256(), 0
        try:
            with open(bank_path, "rb") as f:
                for line in f:
                    h.update(line)
                    n += 1
        except OSError as e:
            self._extra_meta.update({"bank_path": bank_path, "bank_content_sha16": None,
                                     "bank_hash_error": str(e)})
            return
        self._extra_meta.update({"bank_path": os.path.abspath(bank_path),
                                 "bank_content_sha16": h.hexdigest()[:16],
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
