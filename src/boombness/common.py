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

import hashlib
import json
import math
import os
import random
import re
import statistics
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

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
SEED_LOG: List[Dict[str, Any]] = []
"""Every seed this PROCESS actually applied, in order, as {"label", "seed"}.

WHY A LOG AND NOT A NUMBER (retraction R-12, 2026-08-18). `score_behavior.py` recursed into
composed arms without passing `control_seed`, so three runs launched with `--seed 20260901/2/3`
all drew `[20260824, 20260834, 20260824, 20260834]` and produced byte-identical generations. The
run directories recorded the seed that was *requested* on the command line and nothing recorded
the seeds that were *applied*, so on disk the three runs were indistinguishable from three
independent draws -- and the artifact whose entire purpose was to measure draw-to-draw variance
reported a band of one draw stated three times. A requested seed is an intention; only the applied
seeds are provenance. `RunDir.finish` writes both, and flags them when they disagree.
"""


def seed_everything(seed: int, label: str = "main") -> int:
    """Seed python/numpy/torch. Returns the seed so callers can log it.

    Also appends to `SEED_LOG` (see above) so `RunDir.finish` can record the seeds this process
    ACTUALLY applied, not just the one its argparse namespace asked for.
    """
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
    try:
        rec_seed: Any = int(seed)
    except Exception:
        rec_seed = repr(seed)[:80]
    SEED_LOG.append({"label": str(label), "seed": rec_seed})
    return seed


# --------------------------------------------------------------------------- #
# Model / tokenizer revision provenance (plan §2.1)
# --------------------------------------------------------------------------- #
# Plan §2.1 requires "model name and revision" AND "tokenizer name and revision" in every run's
# metadata. Measured 2026-08-19 over the committed artifacts: `tokenizer_revision` appears in
# ZERO of the 189 config.json / 171 metadata.json files, and `model_revision` appears in 103 of
# them with the value `null` in every single one -- because `ds_common.load_model(revision=None)`
# stores what the caller ASKED for, and every caller asked for nothing.
#
# The obvious repair -- record the string "main" -- is worse than recording nothing, because a
# branch name is not provenance: `main` on the Hub moves, and a field called `tokenizer_revision`
# holding `"main"` reads as though a specific artefact had been pinned when nothing was. Every
# run in this sprint sets HF_HUB_OFFLINE=1, so there is no network to ask; but the resolved
# commit IS obtainable offline, because the local cache is content-addressed by it:
#
#     .cache/huggingface/hub/models--meta-llama--Llama-3.1-8B-Instruct/
#         refs/main       -> "0e9e39f249a16976918f6564b8830bc894c89659"
#         snapshots/0e9e39f249a16976918f6564b8830bc894c89659/...
#
# So the fields below are split by what is actually known, and the name says which is which:
#   *_revision_requested        the string the caller passed (may be None, may be "main")
#   *_revision_resolved_commit  a 40-hex commit sha, or None. NEVER a branch name.
#   *_revision_resolution_source how it was obtained (see `resolve_hf_revision`)
#   *_revision_unresolved_reason why it is None, when it is
# plus, for the tokenizer, a content hash of the tokenizer files actually on disk
# (`tokenizer_files_sha16`), which is provenance that cannot drift at all and is available even
# when the snapshot did not come from the Hub.

_HEX40 = re.compile(r"^[0-9a-f]{40}$")

_TOKENIZER_FILENAMES = ("tokenizer.json", "tokenizer_config.json", "special_tokens_map.json",
                        "vocab.json", "merges.txt", "tokenizer.model", "added_tokens.json")


def hf_cache_roots() -> List[str]:
    """Candidate HF hub cache roots, most authoritative first, de-duplicated.

    The SLURM wrappers export `HF_HOME=$PROJECT_DIR/.cache/huggingface` (plus HF_HUB_CACHE on
    some of them) BEFORE python starts, so reading the environment here is reading what the run
    actually used. The repo-local and user-home defaults are appended for CPU-side tooling that
    is launched without the wrapper.
    """
    roots: List[str] = []
    for env in ("HF_HUB_CACHE", "HUGGINGFACE_HUB_CACHE"):
        v = os.environ.get(env)
        if v:
            roots.append(v)
    v = os.environ.get("HF_HOME")
    if v:
        roots.append(os.path.join(v, "hub"))
    v = os.environ.get("TRANSFORMERS_CACHE")
    if v:
        roots.append(v)
    roots.append(os.path.join(REPO_ROOT, ".cache", "huggingface", "hub"))
    roots.append(os.path.expanduser("~/.cache/huggingface/hub"))
    seen, out = set(), []
    for r in roots:
        a = os.path.abspath(r)
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out


def _commit_from_path(p: Any) -> Tuple[Optional[str], Optional[str]]:
    """(commit, snapshot_dir) if `p` lies inside an HF `snapshots/<40-hex>/` directory."""
    if not p:
        return None, None
    try:
        parts = os.path.abspath(str(p)).split(os.sep)
    except Exception:
        return None, None
    for i, seg in enumerate(parts):
        if seg == "snapshots" and i + 1 < len(parts) and _HEX40.match(parts[i + 1]):
            return parts[i + 1], os.sep.join(parts[: i + 2])
    return None, None


def _paths_from_obj(obj: Any) -> List[Any]:
    """Filesystem paths a loaded tokenizer/model can tell us about itself.

    Deliberately duck-typed and fully guarded: this is provenance code and must never be the
    thing that kills a GPU run. `vocab_file` is checked BEFORE `name_or_path` because it is the
    file that was actually opened, whereas `name_or_path` is frequently the bare repo id.
    """
    out: List[Any] = []
    for attr in ("vocab_file", "merges_file"):
        out.append(getattr(obj, attr, None))
    try:
        init_kw = getattr(obj, "init_kwargs", None)
        if isinstance(init_kw, dict):
            out.append(init_kw.get("name_or_path"))
            out.append(init_kw.get("vocab_file"))
            out.append(init_kw.get("tokenizer_file"))
    except Exception:
        pass
    out.append(getattr(obj, "name_or_path", None))
    cfg = getattr(obj, "config", None)
    if cfg is not None:
        out.append(getattr(cfg, "_name_or_path", None))
    return [p for p in out if p]


def _repo_cache_dirname(repo_id: str) -> str:
    return "models--" + str(repo_id).replace("/", "--")


def resolve_hf_revision(repo_id: Any, requested: Optional[str] = None,
                        obj: Any = None) -> Dict[str, Any]:
    """Resolve a model/tokenizer id to the CONCRETE commit it was loaded from, offline.

    Returns a dict that is safe to splat into metadata:
        {"repo_id", "requested", "resolved_commit", "resolution_source",
         "snapshot_dir", "unresolved_reason"}

    `resolved_commit` is a 40-hex sha or None. It is NEVER a branch name -- that is the whole
    point of this function; see the block comment above.

    `resolution_source` is one of, in the order they are tried:
      "loaded_snapshot_path"       the loaded object named a file inside snapshots/<sha>/.
                                   Authoritative: it is where the bytes came from.
      "id_is_snapshot_path"        the caller passed a snapshot path as the model id.
      "local_dir_git_head"         the id is a local git checkout; HEAD is its revision.
      "hf_cache_ref:<name>"        the local cache's refs/<name> pointer. Concrete, and it is
                                   what an HF_HUB_OFFLINE=1 load of that ref resolves to on this
                                   machine right now -- but it is a property of the cache, not
                                   proof that THIS run read it, which is why the source says so.
      "hf_cache_single_snapshot"   only one snapshot of the repo is cached, so a successful
                                   offline load can only have used it.
    `unresolved_reason` is set (and resolved_commit stays None) when none of these apply --
    including the deliberately-refused case where the cache holds SEVERAL snapshots and no ref
    tells us which one, because guessing there is exactly how a provenance field starts lying.
    """
    out: Dict[str, Any] = {"repo_id": (str(repo_id) if repo_id is not None else None),
                           "requested": requested, "resolved_commit": None,
                           "resolution_source": None, "snapshot_dir": None,
                           "unresolved_reason": None}
    if obj is not None:
        for p in _paths_from_obj(obj):
            c, d = _commit_from_path(p)
            if c:
                out.update({"resolved_commit": c, "resolution_source": "loaded_snapshot_path",
                            "snapshot_dir": d})
                return out
    if repo_id:
        c, d = _commit_from_path(repo_id)
        if c:
            out.update({"resolved_commit": c, "resolution_source": "id_is_snapshot_path",
                        "snapshot_dir": d})
            return out
        if os.path.isdir(str(repo_id)) and os.path.exists(os.path.join(str(repo_id), ".git")):
            try:
                import subprocess
                sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(repo_id),
                                              stderr=subprocess.DEVNULL).decode().strip()
                if _HEX40.match(sha):
                    out.update({"resolved_commit": sha,
                                "resolution_source": "local_dir_git_head",
                                "snapshot_dir": os.path.abspath(str(repo_id))})
                    return out
            except Exception:
                pass
        ref_names = [r for r in (requested, "main") if r]
        for root in hf_cache_roots():
            repo_dir = os.path.join(root, _repo_cache_dirname(repo_id))
            if not os.path.isdir(repo_dir):
                continue
            snap_root = os.path.join(repo_dir, "snapshots")
            for ref in ref_names:
                if requested and _HEX40.match(str(requested)):
                    break                       # an explicit sha needs no ref lookup
                ref_path = os.path.join(repo_dir, "refs", str(ref))
                try:
                    sha = open(ref_path).read().strip()
                except OSError:
                    continue
                if _HEX40.match(sha):
                    snap = os.path.join(snap_root, sha)
                    out.update({"resolved_commit": sha,
                                "resolution_source": f"hf_cache_ref:{ref}",
                                "snapshot_dir": snap if os.path.isdir(snap) else None})
                    return out
            if requested and _HEX40.match(str(requested)):
                snap = os.path.join(snap_root, str(requested))
                if os.path.isdir(snap):
                    # NOT "id_is_snapshot_path" (verifier fix): the id was a repo id and the sha
                    # came from the caller's `revision=`. A resolution_source that names a source
                    # the value did not come from is the same class of lie as recording "main".
                    out.update({"resolved_commit": str(requested),
                                "resolution_source": "requested_sha_present_in_cache",
                                "snapshot_dir": snap})
                    return out
            try:
                snaps = sorted(s for s in os.listdir(snap_root) if _HEX40.match(s))
            except OSError:
                snaps = []
            if len(snaps) == 1:
                out.update({"resolved_commit": snaps[0],
                            "resolution_source": "hf_cache_single_snapshot",
                            "snapshot_dir": os.path.join(snap_root, snaps[0])})
                return out
            if len(snaps) > 1:
                out["unresolved_reason"] = (
                    f"{len(snaps)} snapshots cached under {repo_dir} and no refs/{ref_names} "
                    f"pointer: which one was loaded is not recoverable offline, and guessing "
                    f"would put a value that looks authoritative into a provenance field")
                return out
        if out["unresolved_reason"] is None:
            out["unresolved_reason"] = (
                f"no HF cache entry {_repo_cache_dirname(repo_id)} under any of "
                f"{hf_cache_roots()}, and the id is neither a snapshot path nor a git checkout")
    else:
        out["unresolved_reason"] = "no repo id given"
    return out


def tokenizer_files_sha16(snapshot_dir: Optional[str]) -> Dict[str, Any]:
    """Content hash of the tokenizer files in `snapshot_dir`. Drift-proof provenance.

    A commit sha says which Hub revision was pinned; this says what the bytes were, which is the
    thing that actually determines tokenization -- and it is obtainable even when the revision is
    not (a local directory, a hand-assembled snapshot). Returns
    {"tokenizer_files_sha16", "tokenizer_files_hashed", "tokenizer_files_bytes"} with None/[] when
    the directory is unknown or holds none of the known tokenizer files.
    """
    empty = {"tokenizer_files_sha16": None, "tokenizer_files_hashed": [],
             "tokenizer_files_bytes": None}
    if not snapshot_dir or not os.path.isdir(snapshot_dir):
        return empty
    h, names, nbytes = hashlib.sha256(), [], 0
    for name in _TOKENIZER_FILENAMES:            # fixed order: the hash must not depend on listdir
        p = os.path.join(snapshot_dir, name)
        if not os.path.isfile(p):
            continue
        # Hash each file into its OWN digest first and fold it in only on a COMPLETE read. The
        # first version updated `h` as it read and `continue`d on OSError, so a truncated read
        # left that file's bytes inside the hash while `tokenizer_files_hashed` omitted the name
        # -- provenance whose manifest does not describe its own digest.
        try:
            fh_digest, fbytes = hashlib.sha256(), 0
            with open(p, "rb") as f:
                while True:
                    chunk = f.read(1 << 20)
                    if not chunk:
                        break
                    fh_digest.update(chunk)
                    fbytes += len(chunk)
        except OSError:
            continue
        h.update(name.encode())
        h.update(b"\0")
        h.update(fh_digest.digest())
        nbytes += fbytes
        names.append(name)
    if not names:
        return empty
    return {"tokenizer_files_sha16": h.hexdigest()[:16], "tokenizer_files_hashed": names,
            "tokenizer_files_bytes": nbytes}


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
        # "open" -> "finished" | "aborted". Guards the T12/R-12 class: a second terminal write
        # must not be able to overwrite the first one's verdict (see `finish` / `abort`).
        self._state = "open"
        self._n_seed_records_at_start = len(SEED_LOG)

        # House provenance first (plan §2.1 wants it written as the FIRST action).
        try:
            ds().write_runmeta(self.path, args=args, extra={"experiment": experiment,
                                                            "plan": "BOOMBNESS_OBJECTIVE_SPRINT_PLAN.md"})
        except Exception as e:                                        # never fatal
            self._extra_meta["_runmeta_error"] = repr(e)[:300]

        cfg = {}
        if args is not None:
            cfg = dict(vars(args)) if hasattr(args, "__dict__") else dict(args)
        self._seed, self._seed_source = _resolve_seed(args)
        self._config = {"experiment": experiment, "run_id": self.run_id,
                        # plan §2.1 "random seed": promoted OUT of `args` to a top-level field.
                        # It lived only inside `args` before, where it is indistinguishable from
                        # any other CLI knob and absent entirely for callers that build a RunDir
                        # from a dict; `seed_source` says where the value came from.
                        "seed": self._seed, "seed_source": self._seed_source,
                        "args": _jsonable(cfg)}
        self.write_json("config.json", self._config)

    # -- io ---------------------------------------------------------------- #
    def p(self, *parts: str) -> str:
        return os.path.join(self.path, *parts)

    # The four files that constitute a run's VERDICT. `finish`/`abort` own them; a caller that
    # writes them directly bypasses the mandatory failure ledger and the abort/DONE exclusion.
    # The class docstring has always claimed "a run's summary.json is only allowed to be written
    # through RunDir.finish" and nothing enforced it -- an invariant asserted in prose at one end
    # of a contract and never checked at the other, which is the exact shape of this sprint's
    # five dead guards. `write_json` now enforces it.
    TERMINAL_FILES = ("summary.json", "metadata.json", "DONE.json", "ABORTED.json")

    def _write_json_unchecked(self, name: str, obj: Any) -> str:
        path = self.p(name)
        with open(path, "w") as f:
            json.dump(_jsonable(obj), f, indent=2)
        return path

    def write_json(self, name: str, obj: Any) -> str:
        if os.path.basename(name) in self.TERMINAL_FILES:
            raise PermissionError(
                f"RunDir.write_json refuses to write {name!r}: it is a terminal file, written "
                f"only by RunDir.finish() (which requires a FailureLedger, plan §2.2) or "
                f"RunDir.abort(). Writing it directly would produce a run that reports a "
                f"successful subset with no statement of how many examples failed.")
        return self._write_json_unchecked(name, obj)

    def log_row(self, row: Dict[str, Any]) -> None:
        """Append one result row to results.jsonl (flushed, so a killed job keeps its rows)."""
        if self._results_fh is None:
            self._results_fh = open(self.p("results.jsonl"), "a")
        self._results_fh.write(json.dumps(_jsonable(row)) + "\n")
        self._results_fh.flush()
        self._n_rows += 1

    def note_model(self, model_id: str, revision: Optional[str] = None,
                   tokenizer_id: Optional[str] = None, dtype: Optional[str] = None,
                   attn_implementation: Optional[str] = None,
                   tokenizer_obj: Any = None, model_obj: Any = None,
                   tokenizer_revision: Optional[str] = None, **kw) -> None:
        """Record model/tokenizer identity AND their RESOLVED revisions (plan §2.1).

        `revision` / `tokenizer_revision` are what the caller ASKED for and are stored under
        `*_revision_requested`; the concrete commit is resolved offline out of the HF cache (or,
        better, out of the loaded object if `tokenizer_obj` / `model_obj` are passed) and stored
        under `*_revision_resolved_commit`. See the block comment at `resolve_hf_revision`: a
        field named `tokenizer_revision` holding `"main"` is worse than no field at all.

        The legacy key `model_revision` keeps its old meaning (the requested value, null in all
        103 committed artifacts that carry it) so nothing that reads it changes meaning.
        """
        tok_id = tokenizer_id or model_id
        mrev = resolve_hf_revision(model_id, requested=revision, obj=model_obj)
        trev = resolve_hf_revision(tok_id, requested=(tokenizer_revision or revision),
                                   obj=tokenizer_obj)
        meta: Dict[str, Any] = {
            "model": model_id, "model_revision": revision,
            "model_revision_requested": revision,
            "model_revision_resolved_commit": mrev["resolved_commit"],
            "model_revision_resolution_source": mrev["resolution_source"],
            "model_revision_unresolved_reason": mrev["unresolved_reason"],
            "tokenizer": tok_id,
            "tokenizer_revision_requested": tokenizer_revision or revision,
            "tokenizer_revision_resolved_commit": trev["resolved_commit"],
            "tokenizer_revision_resolution_source": trev["resolution_source"],
            "tokenizer_revision_unresolved_reason": trev["unresolved_reason"],
            "tokenizer_snapshot_dir": trev["snapshot_dir"],
            "dtype": dtype, "attn_implementation": attn_implementation,
        }
        meta.update(tokenizer_files_sha16(trev["snapshot_dir"]))
        meta.update(kw)
        self._extra_meta.update(meta)

    def note_seed(self, seed: Any, source: str = "note_seed") -> None:
        """Declare the run's seed when it is not `args.seed` (plan §2.1 "random seed").

        Rewrites config.json so the file on disk never disagrees with the run.
        """
        self._seed, self._seed_source = seed, source
        self._config["seed"] = _jsonable(seed)
        self._config["seed_source"] = source
        self._write_json_unchecked("config.json", self._config)

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
        """Write metadata.json + summary.json + DONE.json. Ledger is MANDATORY (plan §2.2).

        The ledger requirement is checked BEFORE anything else and there is no second path to
        summary.json: `write_json` refuses the terminal filenames, and a run that has already
        finished or aborted refuses to finish again. Those three together are the guard; the
        `ledger is None` check alone was one end of a contract with nothing at the other, which
        is how `write_json("summary.json", ...)` would have sailed past it.
        """
        if ledger is None:
            raise ValueError(
                "RunDir.finish requires a FailureLedger — plan §2.2 forbids reporting a "
                "successful subset without stating how many examples failed and why.")
        if not isinstance(ledger, FailureLedger) and not hasattr(ledger, "as_dict"):
            raise TypeError(
                f"RunDir.finish got {type(ledger).__name__} where a FailureLedger was required; "
                f"plan §2.2 needs the failure counts and reasons, not a placeholder.")
        if self._state != "open":
            raise RuntimeError(
                f"RunDir.finish called on a run already {self._state}: {self.path}. A second "
                f"terminal write would overwrite the first verdict (T12: a directory holding "
                f"both DONE and ABORTED is worse than either).")
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
            **self._seed_meta(),
        }
        try:
            meta["git_dirty"] = dc.git_dirty()
        except Exception:
            pass
        self._write_json_unchecked("metadata.json", meta)

        summ = dict(summary or {})
        summ["failures"] = ledger.as_dict()
        summ["n_result_rows"] = self._n_rows
        self._write_json_unchecked("summary.json", summ)

        self._state = "finished"
        try:
            dc.write_done(self.path, rows_written=self._n_rows,
                          extra={"experiment": self.experiment})
        except Exception:
            self._write_json_unchecked("DONE.json", {"ok": True, "n_result_rows": self._n_rows,
                                                     "finished_at": meta["finished_at"]})
        return self.path

    def _seed_meta(self) -> Dict[str, Any]:
        """plan §2.1 "random seed", recorded as intention AND as fact (retraction R-12).

        `seed` is what the run was asked for; `seeds_applied` is every seed this PROCESS actually
        passed to `seed_everything`. When the requested seed never appears among the applied ones,
        `seed_never_applied` is True -- which is precisely the state the three ClearHarm band
        draws were in, and which nothing on disk could then express.

        THE WINDOW IS THE PROCESS, NOT THE RUNDIR'S LIFETIME (verifier fix, 2026-08-19). The first
        version of this method read `SEED_LOG[self._n_seed_records_at_start:]`, i.e. only the seeds
        applied AFTER the RunDir was constructed. Every one of the eight scripts in this package
        calls `seed_everything(args.seed)` BEFORE it constructs its RunDir --
        judge_boombness 134/171, score_behavior 280/310, probes 662/676, extract_boombness 681/688,
        refusalness 137/145, surgical_knockout 626/641, aggressive_patching 1164/1195,
        tokenization_audit 181/189 -- so that window was EMPTY in production, `seeds_applied` came
        out `[]` on every real run, and `bool(applied) and ...` made `seed_never_applied` False:
        an affirmative "the requested seed was applied", derived from an empty collection, in the
        exact case (R-12) the field exists to catch. A guard whose condition cannot be true in the
        order its callers actually use is this sprint's dead-guard shape, and it passed its own
        test only because the test seeded AFTER constructing the RunDir.
        The per-run window is still recorded, under a name that says what it is.
        """
        applied = [dict(r) for r in SEED_LOG]
        since = [dict(r) for r in SEED_LOG[self._n_seed_records_at_start:]]
        vals = [r["seed"] for r in applied]
        # A per-draw seeding loop (which is what score_behavior's composed arm needs, R-12) can
        # apply thousands of seeds; metadata.json must stay readable. The COUNT and the
        # never-applied test below are computed over the whole list, never over the truncation.
        cap = 300
        truncated = len(applied) > cap
        if truncated:
            applied = applied[:cap - 50] + [{"label": "...TRUNCATED...",
                                             "n_omitted": len(applied) - cap}] + applied[-50:]
            since = since[:cap] if len(since) > cap else since
        out: Dict[str, Any] = {
            "seed": self._seed,
            "seed_source": self._seed_source,
            "seeds_applied": applied,
            "seeds_applied_truncated": truncated,
            "n_seeds_applied": len(vals),
            "n_distinct_seeds_applied": len({_norm_seed(v) for v in vals}),
            "seeds_applied_after_run_start": since,
            "seed_never_applied": None,
        }
        if self._seed is not None:
            # Compare on the normalised value: config.json's seed goes through `_jsonable`, so a
            # run built from a mapping can carry "42" where `seed_everything` recorded 42, and a
            # string/int mismatch must not masquerade as an R-12 event.
            out["seed_never_applied"] = _norm_seed(self._seed) not in [_norm_seed(v) for v in vals]
            if out["seed_never_applied"]:
                print(f"[RunDir] PROVENANCE WARNING: config seed {self._seed!r} "
                      f"({self._seed_source}) is not among the {len(vals)} seed(s) this process "
                      f"applied ({vals[:20]}{' ...' if len(vals) > 20 else ''}). Retraction "
                      f"R-12 was exactly this: a run labelled with a "
                      f"seed it never used. (An EMPTY list means `seed_everything` was never "
                      f"called at all, which is the strongest form of the same state, not a "
                      f"reason to stay silent.) Recorded as metadata.json['seed_never_applied'].")
        return out


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

        THE STATE MACHINE RUNS IN BOTH DIRECTIONS (verifier fix, 2026-08-19). `finish` was given a
        `self._state` check and `abort` was not -- the one-of-two-paths shape that has hit this
        repo three times. Measured on the patched code before this fix: `finish(ledger=led)` then
        `abort("...")` was accepted silently, REPLACED the summary.json that carried the ledger
        with one whose `failures` was null, and deleted DONE.json, leaving no trace on disk that a
        finished verdict had ever existed; a second `abort` likewise overwrote the first abort
        reason. An abort AFTER a finish is still allowed -- it must be, or a late gate could never
        retract a DONE (defect T12) -- but it is now RECORDED (`aborted_after_finish`,
        `retracted_verdict`) instead of silent, and a second terminal write of the SAME kind is
        refused, because that one can only lose information.
        """
        if self._state == "aborted":
            raise RuntimeError(
                f"RunDir.abort called on a run already aborted: {self.path}. The second reason "
                f"({reason!r}) would overwrite the first, and the first is the one that stopped "
                f"the run.")
        aborted_after_finish = (self._state == "finished")
        self.note(aborted=True, abort_reason=reason)
        if aborted_after_finish:
            print(f"[RunDir] ABORT AFTER FINISH: {self.path} had already written DONE.json; the "
                  f"abort wins (T12) and DONE.json is retracted, but the finished verdict it "
                  f"replaces is recorded as metadata.json['aborted_after_finish'].")
            self.note(aborted_after_finish=True,
                      retracted_verdict="DONE.json written by finish() was retracted by abort()")
        if self._results_fh is not None:
            self._results_fh.close()
            self._results_fh = None
        summ = dict(summary or {})
        summ["aborted"] = True
        summ["abort_reason"] = reason
        if ledger is not None:
            summ["failures"] = ledger.as_dict()
        summ["n_result_rows"] = self._n_rows
        if ledger is None:
            # An abort is not a report, so a ledger is not required here -- but its ABSENCE must
            # be stated, or `_ledger_counts` reads the missing block the same way it reads a
            # clean one (`{}` -> falsy -> no complaint), which is how "unknown" becomes "fine".
            summ["failures"] = None
            summ["failures_absent_reason"] = "abort() was called without a FailureLedger"
        meta = {"schema": "BOOMBNESS_META/1", "experiment": self.experiment,
                "run_id": self.run_id, "aborted": True, "abort_reason": reason,
                "command": " ".join(sys.argv), "n_result_rows": self._n_rows,
                "wall_seconds": round(time.time() - self._t0, 2),
                "finished_at": time.strftime("%Y-%m-%dT%H:%M:%S"), **self._extra_meta,
                **self._seed_meta()}
        if aborted_after_finish and os.path.exists(self.p("summary.json")):
            # The finished summary carries the FailureLedger this abort's summary may not have.
            # Overwriting it in place would delete the only statement of how many examples failed,
            # which is precisely what plan 2.2 forbids; keep it beside the abort.
            os.replace(self.p("summary.json"), self.p("summary.json.retracted_by_abort"))
        self._write_json_unchecked("metadata.json", meta)
        self._write_json_unchecked("summary.json", summ)
        self._write_json_unchecked("ABORTED.json", {"ok": False, "reason": reason,
                                                    "n_result_rows": self._n_rows,
                                                    "aborted_at": meta["finished_at"]})
        self._state = "aborted"
        done = self.p("DONE.json")
        if os.path.exists(done):
            # Belt and braces: if some earlier code path already declared success, the abort must
            # win. A directory holding BOTH markers is worse than either.
            os.replace(done, self.p("DONE.json.retracted_by_abort"))
        return self.path


def _norm_seed(v: Any) -> Any:
    """Normalise a seed for comparison: 42, "42" and 42.0 are the same seed.

    `config.json`'s seed passes through `_jsonable`, while `seed_everything` records `int(seed)`,
    so an un-normalised `in` test would report a type difference as retraction R-12.
    """
    try:
        return int(v)
    except (TypeError, ValueError):
        return repr(v)


def _resolve_seed(args: Any) -> Tuple[Any, Optional[str]]:
    """(seed, source) from a run's args, for the plan §2.1 top-level `seed` field.

    Works for an argparse Namespace and for a plain mapping (some drivers build a RunDir from a
    dict). Returns (None, None) rather than 0 or "unknown" when there is no seed: a run with no
    seed must not be recorded as a run seeded with something.
    """
    if args is None:
        return None, None
    seed = None
    if hasattr(args, "seed"):
        seed = getattr(args, "seed")
    elif isinstance(args, dict):
        seed = args.get("seed")
    else:
        try:
            seed = dict(args).get("seed")
        except Exception:
            seed = None
    if seed is None:
        return None, None
    return _jsonable(seed), "args.seed"


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
                        strict: bool = True, require_checked: bool = False) -> Dict[str, Any]:
    """The comparison `note_bank`'s docstring promised and nobody ever wrote.

    `run_meta`  a run's metadata.json (or any dict from `RunDir.note_bank`).
    `bank_meta` the bank's *_meta.json -- either the whole file or its `stats` block.

    Returns a verdict dict; raises SystemExit on a real mismatch when `strict`. A hash that is
    simply ABSENT on one side is reported as `unknown`, never as agreement: an old artifact that
    predates the rows hash must not be able to certify a join it never recorded.

    `require_checked` also refuses when NOTHING could be compared. Default False because the
    2026-08-19 sweep (below) found 97 of 114 committed run metadata.json files are in exactly
    that state, and turning them all fatal would break re-analysis of the sprint's own artifacts;
    callers that need a certified join should pass it. `ok` is False either way, so the caller can
    already tell -- what `strict` alone could NOT do is stop a legacy artifact being joined to
    ANY bank without a word, which is the residual half of the T11 dead guard.

    RESULT OF THE SWEEP THIS FUNCTION WAS WRITTEN FOR (2026-08-19, first time ever run over the
    artifacts). 171 committed metadata.json; 57 record no bank; 114 do, over 4 distinct banks.
    Comparing each run against the bank at its OWN recorded `bank_path`:
        102  file hash AGREES with the bank now on disk at that path   (85 of them legacy-keyed,
             so their rows hash is UNKNOWN; 17 also agree on the rows hash)
         12  recorded no hash at all (`bank_path: null`)
          0  MISMATCH, on either hash.
    Independently recomputed: the committed 2352-row bank hashes to 71bea179345ed118 (file bytes)
    and 7002854cf834e9f9 (rows), and `boombness_prompt_bank_meta.json`'s legacy
    `bank_content_sha16` is 7002854cf834e9f9 -- i.e. the two functions that once shared that key
    do indeed compute different values on the same file, and `bank_hashes(legacy=...)` is
    calibrated the right way round for each side.
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
    # Row count is a WEAK identity (two different 2352-row banks collide) but it is recorded on
    # 102 of the 114 bank-carrying artifacts, including legacy ones whose hashes cannot be
    # compared at all -- so it converts some "unknown" joins into a detectable mismatch instead
    # of leaving them wholly unchecked. Reported separately so nobody mistakes it for a hash.
    n_run, n_bank = run_meta.get("bank_n_rows"), stats.get("n_rows")
    verdict["n_rows"] = {"run": n_run, "bank": n_bank}
    if n_run is not None and n_bank is not None:
        verdict["checked_weak"] = ["bank_n_rows"]
        if int(n_run) != int(n_bank):
            verdict["mismatched"].append("bank_n_rows")
    else:
        verdict["checked_weak"] = []
    verdict["ok"] = bool(verdict["checked"]) and not verdict["mismatched"]

    # SEVERITY (2026-08-19). Not every mismatch is the same defect, and treating them alike would
    # have broken the pipeline the moment the external banks gained a `*_meta.json`.
    #
    #   bank_rows_sha16 / bank_n_rows differ -> the run saw DIFFERENT PROMPTS. Fatal: this is
    #       retraction R1's root cause, joining across regenerations by prompt_id.
    #   ONLY bank_file_sha16 differs        -> same rows, rewritten file. BENIGN, and it happens
    #       for a good reason: R-14's fix added `final_query_text` to every external row, which
    #       changed the file bytes while leaving every row identity untouched (verified: 0 old
    #       prompt_ids missing, 0 old rows altered). Refusing here would make every pre-R-14
    #       generation permanently unjudgeable against the corrected bank -- i.e. the guard would
    #       block exactly the re-judging that fixed the defect it exists to prevent.
    #
    # So `strict` refuses on identity, warns on bytes. The two-hash design is what makes the
    # distinction possible; a single ambiguous `bank_content_sha16` could not express it.
    FATAL_KEYS = ("bank_rows_sha16", "bank_n_rows")
    fatal = [k for k in verdict["mismatched"] if k in FATAL_KEYS]
    benign = [k for k in verdict["mismatched"] if k not in FATAL_KEYS]
    verdict["mismatched_fatal"] = fatal
    verdict["mismatched_benign"] = benign
    if benign and not fatal:
        verdict["benign_note"] = (
            "file bytes differ but row identity matches: the bank file was rewritten without "
            "changing which prompts it contains (e.g. R-14 adding `final_query_text`). The join "
            "is sound.")
        print(f"[compare_bank_hashes] NOTE: {benign} differ but row identity matches — "
              f"the bank file was rewritten without changing which prompts it contains. "
              f"Join accepted.")
    if strict and fatal:
        raise SystemExit(
            f"[compare_bank_hashes] REFUSING: the run consumed a DIFFERENT bank than the one it is "
            f"being joined against: "
            f"{[(k, a.get(k, n_run), b.get(k, n_bank)) for k in fatal]}. This bank "
            f"has been regenerated three times this sprint (1464 -> 1752 -> 2352 rows); joining "
            f"across regenerations by prompt_id is retraction R1's stated root cause.")
    if require_checked and not verdict["checked"]:
        raise SystemExit(
            f"[compare_bank_hashes] REFUSING: nothing could be compared between the run "
            f"({verdict['run']}) and the bank ({verdict['bank']}), so this join is asserted by "
            f"prompt_id alone -- which is what retraction R1 was. Pass require_checked=False only "
            f"to inspect a pre-2026-08-18 artifact, never to certify one.")
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


def wilson_ci(k: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    """iid Wilson score interval. THE house implementation -- pure stdlib, exact z.

    `judge_boombness.wilson` and `analyze_steering.wilson` are two byte-identical copies of this
    with a hard-coded z=1.96; both should import this instead (cross-file dependency, not edited
    here). Diffed against `scipy.stats.binomtest(k, n).proportion_ci(method="wilson")` over the
    full grid n in {1..60, 96, 179, 270, 495} x k in {0..n}: max absolute difference 3.9e-06,
    which is the z=1.96-vs-1.959964 rounding in the copies, not a formula difference.

    NOT valid on its own for this design (prompts are clustered in domains) -- it is here because
    `clustered_proportion_ci` needs a defensible fallback when the cluster bootstrap degenerates.
    """
    if n <= 0:
        return (float("nan"), float("nan"))
    z = statistics.NormalDist().inv_cdf(1.0 - alpha / 2.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def _as_flag(f: Any, i: int) -> float:
    """Coerce one outcome to 0.0/1.0, REFUSING the values that used to coerce silently.

    `1.0 if f else 0.0` -- the old body -- has two silent failure modes, both of which this
    project's plan §2.2 forbids and neither of which any call site could see:
      * `None` (a judge failure, an absent field, `r.get("malicious_at_0.5")`) became 0.0, i.e.
        an unmeasured prompt was counted as a NON-attack and shrank the ASR;
      * `float("nan")` is TRUTHY in Python, so a NaN score became 1.0, i.e. an unmeasured prompt
        was counted as an ATTACK SUCCESS. `judge_boombness` explicitly turns a NaN judge score
        into a null row upstream, which is the only reason this has not already bitten.
    A missing outcome belongs in the FailureLedger, not in the numerator or the denominator.
    """
    if f is None:
        raise ValueError(
            f"clustered_proportion_ci: flags[{i}] is None. A missing outcome must be counted in "
            f"the FailureLedger and EXCLUDED by the caller, not silently coerced to 0 (which "
            f"reports an unmeasured prompt as a non-attack).")
    if isinstance(f, bool):
        return 1.0 if f else 0.0
    if isinstance(f, (int, float)):
        x = float(f)
        if math.isnan(x):
            raise ValueError(
                f"clustered_proportion_ci: flags[{i}] is NaN. `1.0 if nan else 0.0` is 1.0 -- a "
                f"NaN outcome would be counted as an attack SUCCESS. Exclude it and record it in "
                f"the FailureLedger.")
        if x not in (0.0, 1.0):
            raise ValueError(
                f"clustered_proportion_ci: flags[{i}] = {f!r} is not a 0/1 outcome; this is a "
                f"PROPORTION estimator, not a mean estimator.")
        return x
    try:                                    # numpy bool_/integer/floating and the like
        return _as_flag(f.item(), i)
    except AttributeError:
        raise ValueError(f"clustered_proportion_ci: flags[{i}] = {f!r} is not a 0/1 outcome")


def clustered_proportion_ci(flags, clusters, n_boot: int = 4000, seed: int = 20260818,
                            alpha: float = 0.05, return_diag: bool = False):
    """Percentile CI for a proportion whose observations are CLUSTERED, by resampling CLUSTERS.

    WHY. Every ASR interval in this sprint was a Wilson binomial with z=1.96 over PROMPTS
    (`judge_boombness.wilson`, `analyze_steering.wilson`), i.e. it treated the 270 prompts of an arm
    as 270 independent Bernoulli draws. They are not: they are 6 domains x ~45 prompts, and prompts
    within a domain share a stem, a demo pool and a target. Audit 11 measured the consequence as
    roughly a 1.9x understatement of the interval. Every OTHER inference in this sprint clusters on
    domain (analyze_g2, analyze_g8, analyze_g9, analyze_position, reanalyze_corrected), so the
    headline number was the only one that did not.

    Returns (lo, hi, n_clusters), or (lo, hi, n_clusters, diag) with `return_diag`. The Wilson
    interval is still reported beside it, labelled iid, so the two are visibly different rather
    than one silently replacing the other.

    ---------------------------------------------------------------------------------------------
    AUDIT AGAINST SCIPY, 2026-08-19 (`analyze_g8.t_sf` was wrong for a year; nothing here was to be
    assumed right). What was checked, and what it found:

    ARITHMETIC -- CLEAN. At the default n_boot=4000 the order statistics this function picks,
    `means[int(.025*B)]` and `means[int(.975*B)]`, agree to the last bit with `np.quantile(means,
    [.025,.975])` under EVERY numpy interpolation method (inverted_cdf/linear/lower/higher/
    nearest/midpoint). Only below B~1000 do they diverge, by one order statistic (+0.0037 on a
    0.09-wide interval at B=200). The cluster draw is uniform: 200k draws over G=6 give
    `scipy.stats.chisquare` p=0.096.

    DEFECT 1, SILENT TRUNCATION -- FIXED. `zip(flags, clusters)` dropped the tail when the two
    sequences had different lengths. Demonstrated pre-fix with 270 flags and 269 clusters: it
    returned an interval, computed over 269 rows, saying nothing. Both call sites happen to build
    the two lists from one comprehension, so this was latent, not active. Now a ValueError.

    DEFECT 2, SILENT COERCION -- FIXED. See `_as_flag`: None counted as a failure, NaN counted as a
    SUCCESS.

    DEFECT 3, ZERO-WIDTH "95% CI" -- FIXED, AND IT IS ON DISK. A cluster bootstrap can only move
    the estimate by re-weighting clusters, so when every cluster has the same proportion -- and in
    particular when the proportion is 0 or 1 -- every resample gives the identical value and the
    interval collapses to a point. Swept over every JSON under outputs/boombness (936 files, 340
    `ci95_domain_clustered` fields at the time of the sweep and rising as runs land): **exactly 10
    are zero-width**, all in two summary.json files, and no other field is affected:
        judge/len_D_20260818_130635_3307401     benign_remap / cell F, ASR 0.000, n=36  -> [0,0]
        judge/q3_C20_20260818_174110_179027     role_style=tool, ASR 1.000, n=72        -> [1,1]
                                                n_examples 0 (11/16 in all 6 domains)   -> [.6875,.6875]
                                                n_examples 1                            -> [.5,.5]
    scipy's exact interval for k=0,n=36 is [0, 0.0974] and for k=n=72 is [0.9501, 1]. A zero-width
    95% interval is not a conservative statement, it is a false one. Such cells now fall back to
    `wilson_ci` and say so in `diag["interval_source"]`; every non-degenerate field is untouched,
    bit for bit (pinned by `test_d_non_degenerate_intervals_are_bit_identical_to_the_pre_fix_code`,
    which diffs this function against the pre-fix one exported from git).

    LIMITATION, NOT A DEFECT -- SMALL G UNDER-COVERS. Monte-Carlo (beta-binomial clusters, 600-800
    replicates, truth = the superpopulation p) measures coverage of this nominal-95% interval as:
        G=6:  0.861 (low ICC) / 0.839 (high ICC)      <- the sprint's 6-domain design
        G=16: 0.914 / 0.921                           <- the AdvBench 16-cluster design
        G=40: 0.917 / 0.945
    against an iid Wilson at 0.904 / 0.603. So clustering is unambiguously the right correction
    (Wilson collapses to 60% coverage the moment clusters are heterogeneous), but at G=6 this
    interval is still ~10 points anticonservative and must not be read as exact. `n_clusters` has
    always been returned; it is the number that says how much to trust the other two. A two-stage
    bootstrap (resample clusters, then rows within them) was measured too and is not adopted: it
    over-covers, 0.993-1.000, and would change every published interval.
    """
    flags = list(flags)
    clusters = list(clusters)
    if len(flags) != len(clusters):
        raise ValueError(
            f"clustered_proportion_ci: {len(flags)} flags but {len(clusters)} cluster labels. "
            f"zip() would have silently analysed the first {min(len(flags), len(clusters))} rows "
            f"and reported an interval over a population nobody chose.")
    by: Dict[Any, List[float]] = {}
    for i, (f, c) in enumerate(zip(flags, clusters)):
        by.setdefault(c, []).append(_as_flag(f, i))
    keys = sorted(by, key=str)
    G = len(keys)
    n_obs = len(flags)
    n_succ = int(sum(sum(v) for v in by.values()))
    diag: Dict[str, Any] = {"n_clusters": G, "n_obs": n_obs, "n_success": n_succ,
                            "point": (n_succ / n_obs if n_obs else float("nan")),
                            "n_boot": n_boot, "seed": seed, "alpha": alpha,
                            "boot_lo": None, "boot_hi": None,
                            "degenerate_bootstrap": None, "interval_source": None,
                            "coverage_caveat": (None if G >= 16 else
                                                f"G={G} clusters: measured coverage of this "
                                                f"nominal-{1 - alpha:.0%} interval is ~0.84-0.86 "
                                                f"at G=6 (see docstring); do not read as exact")}

    def _ret(lo, hi):
        return (lo, hi, G, diag) if return_diag else (lo, hi, G)

    if G < 2:
        diag["interval_source"] = "undefined:fewer_than_2_clusters"
        return _ret(float("nan"), float("nan"))
    rng = random.Random(seed)
    means = []
    for _ in range(n_boot):
        draw = [by[keys[rng.randrange(G)]] for _ in range(G)]
        tot = [v for d in draw for v in d]
        if tot:
            means.append(sum(tot) / len(tot))
    if not means:
        diag["interval_source"] = "undefined:no_bootstrap_replicates"
        return _ret(float("nan"), float("nan"))
    means.sort()
    lo = means[int(alpha / 2 * len(means))]
    hi = means[min(len(means) - 1, int((1 - alpha / 2) * len(means)))]
    diag["boot_lo"], diag["boot_hi"] = lo, hi
    diag["degenerate_bootstrap"] = bool(hi <= lo)
    if diag["degenerate_bootstrap"]:
        # Identity of the failure, not an incidental property of it: the interval has zero width,
        # whatever produced that. Covers the boundary cases (all-0 / all-1) AND the equal-cluster-
        # proportion case that is on disk at ASR 0.6875 with n=96.
        wlo, whi = wilson_ci(n_succ, n_obs, alpha=alpha)
        diag["interval_source"] = "wilson_iid_fallback:cluster_bootstrap_had_zero_width"
        diag["wilson_iid"] = [wlo, whi]
        # SAY IT OUT LOUD (verifier fix, 2026-08-19). Both live callers -- judge_boombness:298 and
        # analyze_steering:139 -- take the THREE-tuple and write the result to a field named
        # `ci95_domain_clustered`. Without this line the returned interval is an iid Wilson
        # published under a clustered name with nothing on disk saying so, which is the same
        # "one silently replacing the other" this function's own docstring forbids. The proper
        # repair is for those two call sites to take `return_diag=True` and record
        # `diag["interval_source"]`; that is a cross-file change and is reported as one. Until
        # then the substitution is at least in the run log rather than nowhere.
        print(f"[clustered_proportion_ci] DEGENERATE BOOTSTRAP: all {G} clusters give the same "
              f"proportion ({n_succ}/{n_obs}), so the cluster percentile interval has ZERO width "
              f"[{lo}, {hi}] -- a zero-width 95% interval is false, not conservative. Returning "
              f"the iid Wilson [{wlo:.4f}, {whi:.4f}] INSTEAD. If the caller writes this into a "
              f"field named `ci95_domain_clustered`, that field is iid for this cell; record "
              f"return_diag=True's `interval_source` beside it.")
        return _ret(wlo, whi)
    diag["interval_source"] = "cluster_percentile_bootstrap"
    return _ret(lo, hi)
