#!/usr/bin/env python3
"""dcs_verify_kladder.py — the INDEPENDENT verifier for `DCS-R-080` (the K-ladder, `PR-032`/`PR-036`).

WHY THIS FILE EXISTS. §28.9 of
`external_md/DCS_BOMBNESS_SPECIFICITY_AND_CAUSAL_VALIDATION_PLAN_AND_PROGRESS_20260905.md`
records that no `PR-035`-era result may be promoted until a REAL verifier exists, because the
previous one (`dcs_verify_bombness_specificity.py`) failed in two named ways that this file is
built not to repeat:

  ⛔ `C-049` §22.5 — its mutation harness printed `MUTATION HARNESS OK` on a corruption it never
     detected. It passed whenever ANY check failed, so an unrelated failure satisfied it, and in
     the repo's real state the mutation was never applied at all. ⇒ HERE every mutation is bound
     to ONE DESIGNATED CHECK by id, the harness requires THAT check to fail, the clean baseline is
     required to pass first, and every collateral failure is printed rather than counted as
     success.
  ⛔ `A-021` §13.1 / `C-053` §28.9 — a verifier that reads the producer's own derived fields proves
     nothing. ⇒ HERE nothing is imported from `scripts/dcs_kladder_analysis.py`. Every quantity is
     re-derived from the arm directories
     `outputs/boombness/score_behavior/dcsk*_C_{demo,ctrl}_*/results.jsonl` and their
     `config.json` / `metadata.json` / `DONE.json` / the committed argsfiles / the SLURM job logs,
     with this file's own arithmetic (its own binomial sign test, its own Holm, its own median).
     The producer JSON is read ONLY as the CLAIM under test.

WHAT IT VERIFIES (each check can FAIL independently; ids are stable and are what `--mutate` binds
to):

  C1 ARM IDENTITY   — arm dirs resolved independently; `DONE.json` present and `ok`; exactly 380
                      rows over 38 domains, 10 rows per domain; the arm's recorded argv equals the
                      committed argsfile `runargs/dcs/dcsk<K>_C_<demo|ctrl>.txt` BYTE-FOR-BYTE; the
                      job log header reads `=== boombness: score_behavior.py ===` and echoes the
                      same args line (the `C-047` check); the bank the arm joined is the bank on
                      disk (`bank_file_sha16` recomputed, `C-053` §28.3's lesson).
  C2 DOSE           — `keys_masked` identical demo-vs-control on EVERY prompt family of every rung
                      (not merely equal medians); control draw `match_ratio` = 1.000 with zero rows
                      below 1; 0 liveness violations; 0 decode edits; `attn_implementation` eager;
                      `knockout_last_k` == K on every row.
  C3 PAIRING        — the per-domain delta is on the SAME 38 domains in demo and control, paired:
                      `domain` agrees with the `family_id` prefix on every row, the `family_id`
                      multisets match, per-domain counts match; then the per-domain deltas, the
                      mean, the median, the negative count and the sign-test p are RECOMPUTED and
                      required to match the producer to 1e-9 / 1e-12.
  C4 THE ANCHOR     — `dcsk8r` re-run mean_delta recomputed and required to equal the inherited
                      `dcsk8` value. §11.7's kill criterion. The absolute difference is REPORTED.
  C5 HOLM           — Holm-Bonferroni recomputed over the FIVE DECLARED new rungs K=3..7 (absent
                      rungs enter at p=1.0, `C-052`), and the producer's family declaration is
                      required to be the declared five and not "whatever was on disk".
  C6 K* AND SHAPE   — §11.5's two-part K* rule (Holm p <= 0.05 AND |Δ| >= 0.5·|Δ₈|) and the
                      STEP / RAMP / NEITHER classification, re-derived, with adjacency taken on
                      VALUES of K so a hole in the ladder cannot be read as a one-rung jump.
  C7 TOKEN IDENTITY — §26.1 / `R-079`: all 380 prompts are re-tokenised with the real
                      Llama-3.1-8B-Instruct tokenizer and the token NEWLY ENTERING the cut at each
                      K=1..7 is required to be what §26.1 claims. This is the claim R-080's whole
                      interpretation rests on. The count of agreeing prompts is reported.

USAGE
    python scripts/dcs_verify_kladder.py            # verify the real artifacts; exit 0 iff all pass
    python scripts/dcs_verify_kladder.py --self-test   # synthetic end-to-end fixture; exit 0 iff clean
    python scripts/dcs_verify_kladder.py --mutate      # every mutation must be caught by ITS check

⛔ READ THE `limitations` SECTION AT THE BOTTOM OF THIS DOCSTRING BEFORE QUOTING A PASS.
This verifier checks that the published numbers ARE THE NUMBERS THE RAW ROWS SUPPORT, and that the
runs that produced them were the runs that were preregistered. It does NOT re-run the model, does
not re-derive `semantic_logodds` from logits, and cannot speak to external validity — in
particular it cannot address §27.4's confound (the token entering at K=7 is the readout template's
own option word) which is a fact about the instrument, not about the arithmetic.
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
import json
import os
import re
import shutil
import statistics
import sys
import tempfile
from math import comb

# --------------------------------------------------------------------------- #
# DECLARED CONSTANTS — every one of these is a quotation from the plan, not a tuning knob.
# --------------------------------------------------------------------------- #
EXPECT_N = 380                       # §11.3 --expect-n 380
EXPECT_DOMAINS = 38                  # §11.4 independence unit: domain, n = 38
EXPECT_ROWS_PER_DOMAIN = 10          # 380 / 38, asserted rather than assumed
ALPHA = 0.05                         # §11.4
DECLARED_NEW_RUNGS = (3, 4, 5, 6, 7)  # §11.3 "arms: 10: for each K in {3,4,5,6,7}"
PROFILE_KS = (1, 2, 3, 4, 5, 6, 7, 8)  # §11.5 "The full 8-point profile (1,2,3,4,5,6,7,8)"
HALF_K8_RULE = 0.5                   # §11.5 |Δ_K| >= 0.5·|Δ_8|
STEP_LOW, STEP_HIGH = 0.20, 0.50     # §11.5 declared shapes
RAMP_MAX_SINGLE = 0.40               # §11.5
MEAN_TOL = 1e-9                      # the task's stated reproduction tolerance
EXACT_TOL = 1e-12                    # for quantities that should be bit-reproducible
ANCHOR_TOL = 0.0                     # §27.1 claims the anchor reproduces EXACTLY (diff 0.000000)

#: §27 published claims. The verifier tests the producer against the LOG, not only against itself.
PUBLISHED_K8 = -6.616111537245543    # §11.1 / §27.1 the inherited K=8 value
PUBLISHED_K_STAR = 7                 # §27.2
PUBLISHED_SHAPE = "STEP"             # §27.2 (with §27.7's completeness condition now met)
PUBLISHED_LARGEST_RISE = (6, 7)      # §27.2 "Largest single-rung rise: K=6 -> K=7"

#: §26.1 — the token NEWLY ENTERING the cut at each rung, claimed invariant over all 380 prompts.
SECTION_26_1_TOKENS = {
    1: "\n\n",                 # chat scaffold
    2: "<|end_header_id|>",    # chat scaffold
    3: "assistant",            # chat scaffold (generation header)
    4: "<|start_header_id|>",  # chat scaffold
    5: "<|eot_id|>",           # chat scaffold (end of user turn)
    6: "?",                    # first USER-TEXT token
    7: " bomb",                # first CONTENT word  (§26.4: the readout template's own option word)
}

BANK_BASENAME = "boombness_prompt_bank_cds38_button_bomb.jsonl"
LOG_HEADER = "=== boombness: score_behavior.py ==="

CHECK_IDS = ("C1", "C2", "C3", "C4", "C5", "C6", "C7")


# --------------------------------------------------------------------------- #
# OWN ARITHMETIC — deliberately duplicated rather than imported.
# --------------------------------------------------------------------------- #
def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


def median(xs):
    return float(statistics.median(list(xs)))


def binom_tail(k: int, at_least: int) -> float:
    """P(X >= at_least) for X ~ Binomial(k, 1/2), exactly (integer combinations, one divide)."""
    return sum(comb(k, i) for i in range(at_least, k + 1)) / (2 ** k)


def sign_test(deltas):
    """Exact two-sided sign test over per-cluster deltas. Zeros are UNINFORMATIVE and dropped.

    Independent re-implementation of the declared statistic (§11.4). It is NOT imported from
    `clustered_stats`, so a defect there and a defect here cannot cancel.
    """
    informative = [d for d in deltas if d != 0]
    k = len(informative)
    neg = sum(1 for d in informative if d < 0)
    if k == 0:
        return dict(k_informative=0, n_negative=0, p=1.0, attainable_floor=1.0,
                    can_reach_alpha=False, n_clusters=len(list(deltas)))
    p = min(1.0, 2 * binom_tail(k, max(neg, k - neg)))
    return dict(k_informative=k, n_negative=neg, p=p, attainable_floor=2 / (2 ** k),
                can_reach_alpha=(2 / (2 ** k)) <= ALPHA, n_clusters=len(list(deltas)))


def holm(pvals):
    """Holm-Bonferroni over the family; adjusted p in the input order, monotone by construction."""
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m, adj, prev = len(pvals), [0.0] * len(pvals), 0.0
    for rank, i in enumerate(idx):
        v = min(1.0, (m - rank) * pvals[i])
        prev = max(prev, v)
        adj[i] = prev
    return adj


def close(a, b, tol):
    if a is None or b is None:
        return False
    return abs(float(a) - float(b)) <= tol


# --------------------------------------------------------------------------- #
# TOKENIZERS
# --------------------------------------------------------------------------- #
class RealLlamaTokenizer:
    """The actual Llama-3.1-8B-Instruct tokenizer, used exactly the way `score_behavior.py` uses it.

    ⛔ The templating path is reproduced, not re-invented: `ds_common.apply_template` calls
    `apply_chat_template(to_messages(prompt), tokenize=False, add_generation_prompt=True)` and,
    with `--enable-thinking` unset (`ENABLE_THINKING = None`, the setting every K arm ran under per
    its own `config.json`), the kwarg is NOT passed. Two templating paths that disagree have
    silently shifted a span in this repo before.
    """

    MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"

    def __init__(self):
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        from transformers import AutoTokenizer  # imported lazily: --self-test/--mutate need no HF
        self.tok = AutoTokenizer.from_pretrained(self.MODEL_ID)

    def template(self, prompt: str) -> str:
        return self.tok.apply_chat_template([{"role": "user", "content": prompt}],
                                            tokenize=False, add_generation_prompt=True)

    def encode_with_offsets(self, text: str):
        enc = self.tok(text, add_special_tokens=False, return_offsets_mapping=True)
        return list(enc["input_ids"]), [tuple(o) for o in enc["offset_mapping"]]

    def decode_one(self, tid) -> str:
        return self.tok.decode([tid])


class StubTokenizer:
    """A deterministic stand-in with the Llama-3.1 chat template's SHAPE, for --self-test/--mutate.

    It exists so the token-identity check (C7) and its mutation are exercised on a machine with no
    model weights and no network. ⚠ It is a stand-in for the CONTROL FLOW, not for the real
    tokenizer's segmentation; the real check runs against the real tokenizer and nothing else.
    """

    SPECIAL = re.compile(r"<\|[a-z_]+\|>")
    NL2 = re.compile(r"\n\n")
    WORD = re.compile(r"[ ]?[A-Za-z0-9_]+")
    PUNCT = re.compile(r"[ ]?[^\sA-Za-z0-9_]")
    WS = re.compile(r"\s+")

    def __init__(self):
        self.vocab = {}
        self.inv = {}

    def template(self, prompt: str) -> str:
        return ("<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n"
                + prompt + "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n")

    def _spans(self, text: str):
        out, i, n = [], 0, len(text)
        while i < n:
            for rx in (self.SPECIAL, self.NL2, self.WORD, self.PUNCT, self.WS):
                m = rx.match(text, i)
                if m and m.end() > m.start():
                    out.append((m.start(), m.end()))
                    i = m.end()
                    break
            else:                                     # pragma: no cover - unreachable by design
                out.append((i, i + 1))
                i += 1
        return out

    def encode_with_offsets(self, text: str):
        offs = self._spans(text)
        ids = []
        for a, b in offs:
            s = text[a:b]
            if s not in self.vocab:
                tid = len(self.vocab)
                self.vocab[s] = tid
                self.inv[tid] = s
            ids.append(self.vocab[s])
        return ids, offs

    def decode_one(self, tid) -> str:
        return self.inv[tid]


def query_span_positions(tokenizer, final_query_text: str, templated: str):
    """Re-implementation of `score_behavior.query_span_positions` (:694-718), the span K indexes.

    ⛔ This is the load-bearing structural fact of §26: the span anchors on `final_query_text` and
    runs to the TRUE END of the templated prompt, generation header included. So `_q[-K:]` is the
    last K tokens of the WHOLE chat-templated prompt, not of the question.
    """
    q = (final_query_text or "").strip()
    if not q:
        return []
    ci = templated.rfind(q)
    if ci < 0:
        return []
    _ids, offs = tokenizer.encode_with_offsets(templated)
    return [i for i, (a, b) in enumerate(offs) if b > ci and b > a]


# --------------------------------------------------------------------------- #
# ENVIRONMENT — where the artifacts live. Swapped wholesale by the fixture.
# --------------------------------------------------------------------------- #
class Env:
    def __init__(self, arm_root, runargs_dir, log_dir, producer_json, tokenizer_factory,
                 expected_tokens=None, published=None, bank_basename=BANK_BASENAME):
        self.arm_root = arm_root
        self.runargs_dir = runargs_dir
        self.log_dir = log_dir
        self.producer_json = producer_json
        self.tokenizer_factory = tokenizer_factory
        self.expected_tokens = dict(expected_tokens or SECTION_26_1_TOKENS)
        self.published = dict(published or dict(k8=PUBLISHED_K8, k_star=PUBLISHED_K_STAR,
                                                shape=PUBLISHED_SHAPE,
                                                largest_rise=PUBLISHED_LARGEST_RISE))
        self.bank_basename = bank_basename


def repo_env(repo_root):
    return Env(arm_root=os.path.join(repo_root, "outputs", "boombness", "score_behavior"),
               runargs_dir=os.path.join(repo_root, "runargs", "dcs"),
               log_dir=os.path.join(repo_root, "outputs", "boombness", "logs"),
               producer_json=os.path.join(repo_root, "outputs", "boombness", "dcs_analysis",
                                          "dcs_kladder.json"),
               tokenizer_factory=RealLlamaTokenizer)


# --------------------------------------------------------------------------- #
# RESULT PLUMBING
# --------------------------------------------------------------------------- #
class Check:
    def __init__(self, cid, title):
        self.id, self.title = cid, title
        self.failures, self.facts, self.notes = [], {}, []

    def fail(self, msg):
        self.failures.append(msg)

    def require(self, cond, msg):
        if not cond:
            self.fail(msg)
        return bool(cond)

    @property
    def ok(self):
        return not self.failures


class Report:
    def __init__(self):
        self.checks = {}

    def add(self, c):
        self.checks[c.id] = c
        return c

    @property
    def failed_ids(self):
        return [cid for cid in CHECK_IDS if cid in self.checks and not self.checks[cid].ok]

    @property
    def ok(self):
        return set(self.checks) >= set(CHECK_IDS) and not self.failed_ids

    def render(self, verbose=True):
        lines = []
        for cid in CHECK_IDS:
            c = self.checks.get(cid)
            if c is None:
                lines.append(f"  {cid}  NOT RUN")
                continue
            lines.append(f"  {cid}  {'PASS' if c.ok else 'FAIL'}  {c.title}")
            if verbose:
                for k, v in c.facts.items():
                    lines.append(f"          . {k}: {v}")
                for n in c.notes:
                    lines.append(f"          ~ {n}")
            for f in c.failures:
                lines.append(f"        FAIL: {f}")
        return "\n".join(lines)


# --------------------------------------------------------------------------- #
# ARTIFACT ACCESS — independent of the producer in every respect.
# --------------------------------------------------------------------------- #
class Arm:
    def __init__(self, tag, path):
        self.tag, self.path = tag, path
        self.basename = os.path.basename(path)
        self.rows = [json.loads(l) for l in open(os.path.join(path, "results.jsonl"))
                     if l.strip()]
        self.done = _load_json(os.path.join(path, "DONE.json"))
        self.meta = _load_json(os.path.join(path, "metadata.json"))
        self.config = _load_json(os.path.join(path, "config.json"))

    def by_domain_mean(self):
        d = collections.defaultdict(list)
        for r in self.rows:
            if "semantic_logodds" in r and r["semantic_logodds"] is not None:
                d[r["domain"]].append(float(r["semantic_logodds"]))
        return {k: mean(v) for k, v in d.items()}


def _load_json(p):
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        return json.load(fh)


def resolve_arm_dir(arm_root, tag):
    """Newest COMPLETE `{tag}_*` directory. Resolution is done here, never read from the producer.

    Completeness is part of the selection (`C-051`): a partial dir left by a cancelled job sorts
    newest, and taking `hits[-1]` unconditionally reports a rung as NOT RUN while a complete arm
    for it sits one directory earlier.
    """
    hits = sorted(glob.glob(os.path.join(arm_root, f"{tag}_*")))
    skipped = []
    for h in reversed(hits):
        if os.path.isfile(os.path.join(h, "DONE.json")):
            return h, [os.path.basename(x) for x in hits if x != h]
        skipped.append(os.path.basename(h))
    return None, skipped


def rung_tags(K):
    return f"dcsk{K}_C_demo", f"dcsk{K}_C_ctrl"


# --------------------------------------------------------------------------- #
# C1 — ARM IDENTITY
# --------------------------------------------------------------------------- #
def _check_one_arm(c, env, tag, arm, expect_K, expect_direction):
    b = arm.basename

    if not env or True:
        pass
    # -- DONE.json
    if not c.require(arm.done is not None, f"{b}: DONE.json missing"):
        return
    c.require(arm.done.get("status") == "ok", f"{b}: DONE.json status={arm.done.get('status')!r}")
    c.require(arm.done.get("rows_written") == EXPECT_N,
              f"{b}: DONE.json rows_written={arm.done.get('rows_written')} != {EXPECT_N}")

    # -- population shape, recounted from the rows themselves
    c.require(len(arm.rows) == EXPECT_N, f"{b}: results.jsonl has {len(arm.rows)} rows != {EXPECT_N}")
    doms = collections.Counter(r["domain"] for r in arm.rows)
    c.require(len(doms) == EXPECT_DOMAINS,
              f"{b}: {len(doms)} distinct domains != {EXPECT_DOMAINS}")
    bad = {d: n for d, n in doms.items() if n != EXPECT_ROWS_PER_DOMAIN}
    c.require(not bad, f"{b}: domains not evenly populated: {dict(sorted(bad.items())[:5])}")

    # -- the argsfile, BYTE-FOR-BYTE
    if not c.require(arm.meta is not None, f"{b}: metadata.json missing"):
        return
    argv = arm.meta.get("argv") or []
    if not c.require(len(argv) > 1, f"{b}: metadata.json has no argv"):
        return
    joined = " ".join(argv[1:])
    argsfile = os.path.join(env.runargs_dir, f"{tag}.txt")
    if c.require(os.path.isfile(argsfile), f"{b}: committed argsfile {tag}.txt missing"):
        raw = open(argsfile, "rb").read()
        want = (joined + "\n").encode()
        c.require(raw == want,
                  f"{b}: recorded args do NOT match {tag}.txt byte-for-byte "
                  f"(argsfile {len(raw)}B, recorded {len(want)}B)")

    # -- the argsfile says what the preregistration says it should say
    c.require(f"--knockout-last-k {expect_K} " in joined + " ",
              f"{b}: argv does not carry --knockout-last-k {expect_K}")
    c.require("--knockout-scope query_last_k_rows" in joined,
              f"{b}: argv does not carry --knockout-scope query_last_k_rows")
    c.require(f"--intervene {expect_direction}:attn_knockout:6-14:1.0" in joined,
              f"{b}: argv intervene is not {expect_direction}:attn_knockout:6-14:1.0")
    c.require("--expect-n 380" in joined, f"{b}: argv does not carry --expect-n 380")
    c.require("--attn-impl eager" in joined, f"{b}: argv does not carry --attn-impl eager")
    c.require("--conditions natural_doublespeak" in joined,
              f"{b}: argv does not carry --conditions natural_doublespeak")
    c.require("--query-kinds semantic_forced_choice" in joined,
              f"{b}: argv does not carry --query-kinds semantic_forced_choice")

    # -- the C-047 check: the job log header, and its echoed args line
    jid = arm.meta.get("slurm_job_id")
    if c.require(jid, f"{b}: metadata.json carries no slurm_job_id, so no log can be checked"):
        log = os.path.join(env.log_dir, f"boomb_{jid}.out")
        if c.require(os.path.isfile(log), f"{b}: job log {os.path.basename(log)} missing"):
            with open(log, errors="replace") as fh:
                head = fh.readline().rstrip("\n")
                argline = None
                for ln in fh:
                    if ln.startswith("args: "):
                        argline = ln[len("args: "):].rstrip("\n")
                        break
            c.require(head == LOG_HEADER,
                      f"{b}: job log header is {head!r}, not {LOG_HEADER!r} "
                      f"(C-047: the wrapper fell back to its default script)")
            c.require(argline == joined,
                      f"{b}: job log 'args:' line does not echo the recorded argv "
                      f"(C-047: BOOMB_ARGSFILE was not read)")

    # -- the bank actually joined (C-053 §28.3: a mis-pointed run must never look healthy)
    bp = arm.meta.get("bank_path")
    if c.require(bp, f"{b}: metadata.json carries no bank_path"):
        c.require(os.path.basename(bp) == env.bank_basename,
                  f"{b}: bank basename {os.path.basename(bp)!r} != {env.bank_basename!r}")
        if c.require(os.path.isfile(bp), f"{b}: bank file {bp} not on disk"):
            sha = hashlib.sha256(open(bp, "rb").read()).hexdigest()[:16]
            c.require(sha == arm.meta.get("bank_file_sha16"),
                      f"{b}: bank_file_sha16 {arm.meta.get('bank_file_sha16')} != recomputed {sha}")
            n_lines = sum(1 for l in open(bp) if l.strip())
            c.require(n_lines == arm.meta.get("bank_n_rows"),
                      f"{b}: bank_n_rows {arm.meta.get('bank_n_rows')} != {n_lines} lines on disk")


def check_arm_identity(env, ctx, prod):
    c = Check("C1", "ARM IDENTITY — dirs, DONE, 380x38, argsfile byte-for-byte, log header, bank")
    resolved = {}
    for K, side, tag in ctx["wanted_arms"]:
        path, skipped = resolve_arm_dir(env.arm_root, tag)
        if not c.require(path is not None,
                         f"{tag}: no COMPLETE arm directory (candidates skipped: {skipped})"):
            continue
        resolved[(K, side)] = path
        claimed = ctx["claimed_dirs"].get((K, side))
        c.require(claimed is None or claimed == os.path.basename(path),
                  f"{tag}: producer claims {claimed!r}, independent resolution finds "
                  f"{os.path.basename(path)!r}")
        arm = ctx["arms"].get((K, side))
        if arm is None:
            arm = Arm(tag, path)
            ctx["arms"][(K, side)] = arm
        expect_lastk = 8 if K == "8r" else K       # the anchor IS a K=8 run, under its own tag
        _check_one_arm(c, env, tag, arm, expect_lastk,
                       "demo_all" if side == "demo" else "nondemo_matched_d1")
    c.facts["arms_resolved"] = len(resolved)
    c.facts["rungs_under_test"] = sorted({K for K, _s, _t in ctx["wanted_arms"] if isinstance(K, int)})
    return c


# --------------------------------------------------------------------------- #
# C2 — DOSE
# --------------------------------------------------------------------------- #
def _liveness_count(row):
    v = row.get("hook_liveness_violations", 0)
    if isinstance(v, (list, tuple, set, dict)):
        return len(v)
    return int(v or 0)


def check_dose(env, ctx, prod):
    c = Check("C2", "DOSE — keys_masked identical per family, match_ratio 1.000, 0 liveness, "
                    "0 decode edits, eager")
    ratios, km_pairs = [], []
    for key in ctx["pairs"]:
        K, label = key
        d = ctx["arms"].get((K, "demo"))
        t = ctx["arms"].get((K, "ctrl"))
        if d is None or t is None:
            c.fail(f"{label}: arm pair not loadable, dose cannot be judged")
            continue

        # -- dose equality at the level of the individual prompt family, not the median
        md = {r["family_id"]: r.get("hook_n_keys_masked") for r in d.rows}
        mt = {r["family_id"]: r.get("hook_n_keys_masked") for r in t.rows}
        shared = set(md) & set(mt)
        diff = [f for f in sorted(shared) if md[f] != mt[f]]
        c.require(not diff,
                  f"{label}: keys_masked DIFFERS demo-vs-control on {len(diff)} families "
                  f"(first: {diff[:3]}) — dose broken, §11.7 VOID")
        km_d = median([r.get("hook_n_keys_masked", 0) for r in d.rows])
        km_t = median([r.get("hook_n_keys_masked", 0) for r in t.rows])
        c.require(km_d == km_t, f"{label}: keys_masked median {km_d} vs {km_t}")
        km_pairs.append((label, km_d))

        # -- the producer's own contract block must state what the rows say
        con = (prod.get("contracts") or {}).get(f"K{K}") if isinstance(K, int) else None
        if con:
            for side, arm, kmv in (("demo", d, km_d), ("ctrl", t, km_t)):
                cc = con.get(side) or {}
                c.require(close(cc.get("keys_masked_median"), kmv, EXACT_TOL),
                          f"{label}/{side}: contract keys_masked_median "
                          f"{cc.get('keys_masked_median')} != recomputed {kmv}")
                qre = median([r.get("hook_n_query_rows_edited", 0) for r in arm.rows])
                c.require(close(cc.get("query_rows_edited_median"), qre, EXACT_TOL),
                          f"{label}/{side}: contract query_rows_edited_median "
                          f"{cc.get('query_rows_edited_median')} != recomputed {qre}")
                om = [r["option_mass"] for r in arm.rows if r.get("option_mass") is not None]
                if om:
                    c.require(close(cc.get("option_mass_median"), median(om), EXACT_TOL),
                              f"{label}/{side}: contract option_mass_median "
                              f"{cc.get('option_mass_median')} != recomputed {median(om)}")

        for side, arm in (("demo", d), ("ctrl", t)):
            b = arm.basename
            lv = sum(_liveness_count(r) for r in arm.rows)
            c.require(lv == 0, f"{b}: {lv} liveness violations (must be 0)")
            de = max([int(r.get("hook_n_decode_edits", 0) or 0) for r in arm.rows] or [0])
            c.require(de == 0, f"{b}: max decode edits {de} (must be 0 — the readout must be clean)")
            ks = {r.get("knockout_last_k") for r in arm.rows}
            c.require(ks == {K} if isinstance(K, int) else True,
                      f"{b}: rows carry knockout_last_k {sorted(x for x in ks if x is not None)}, "
                      f"expected {{{K}}}")
            c.require((arm.meta or {}).get("attn_implementation") == "eager",
                      f"{b}: attn_implementation is "
                      f"{(arm.meta or {}).get('attn_implementation')!r}, not 'eager' "
                      f"(§11.3: SDPA has silently dropped custom masks)")
            c.require(((arm.config or {}).get("args") or {}).get("attn_impl") == "eager",
                      f"{b}: config args attn_impl is not 'eager'")

        # -- the control draw: strict count-matching, every row
        feas = (t.meta or {}).get("knockout_feasibility") or {}
        cdr = feas.get("control_draw_match_ratio") or {}
        if not c.require(cdr, f"{t.basename}: control arm records no control_draw_match_ratio"):
            continue
        for name, v in sorted(cdr.items()):
            ratios.append((label, name, v.get("min"), v.get("mean"), v.get("n_below_1")))
            c.require(v.get("n") == EXPECT_N,
                      f"{t.basename}/{name}: match_ratio over n={v.get('n')} != {EXPECT_N}")
            c.require(v.get("min") == 1.0 and v.get("mean") == 1.0,
                      f"{t.basename}/{name}: match_ratio min={v.get('min')} mean={v.get('mean')}, "
                      f"both must be exactly 1.000 (§11.7)")
            c.require(v.get("n_below_1") == 0,
                      f"{t.basename}/{name}: {v.get('n_below_1')} rows below match_ratio 1.0")
        c.require(int(feas.get("infeasible_control", 0) or 0) == 0,
                  f"{t.basename}: infeasible_control = {feas.get('infeasible_control')}")

        dfeas = (d.meta or {}).get("knockout_feasibility") or {}
        c.require(not dfeas.get("control_draw_match_ratio"),
                  f"{d.basename}: a demo_all arm must have NO control draw, yet one is recorded")

    c.facts["keys_masked_median_per_rung"] = {k: v for k, v in km_pairs}
    c.facts["match_ratios"] = [f"{lab}/{nm}: min={mn} mean={mu} below1={nb}"
                               for lab, nm, mn, mu, nb in ratios]
    return c


# --------------------------------------------------------------------------- #
# C3 — PAIRING AND RECOMPUTATION
# --------------------------------------------------------------------------- #
def paired_delta(demo, ctrl):
    a, b = demo.by_domain_mean(), ctrl.by_domain_mean()
    doms = sorted(set(a) & set(b))
    return {d: a[d] - b[d] for d in doms}


def check_pairing(env, ctx, prod):
    c = Check("C3", "PAIRING — same 38 domains, paired; per-domain delta / mean / sign test "
                    "recomputed from results.jsonl")
    recomputed = {}
    for K, label in ctx["pairs"]:
        d, t = ctx["arms"].get((K, "demo")), ctx["arms"].get((K, "ctrl"))
        if d is None or t is None:
            c.fail(f"{label}: arm pair not loadable")
            continue

        # -- the label on each row must be the label its family_id carries. A shuffled domain
        #    column preserves every marginal (and even the mean of the deltas) but destroys the
        #    pairing, so the structural check comes BEFORE any arithmetic.
        for side, arm in (("demo", d), ("ctrl", t)):
            bad = [r["family_id"] for r in arm.rows
                   if r.get("domain") != str(r.get("family_id", "")).split("|")[0]]
            c.require(not bad,
                      f"{arm.basename}: {len(bad)} rows whose `domain` disagrees with the "
                      f"family_id prefix (first: {bad[:3]}) — the pairing key is corrupt")

        fd = collections.Counter(r["family_id"] for r in d.rows)
        ft = collections.Counter(r["family_id"] for r in t.rows)
        c.require(fd == ft,
                  f"{label}: demo and control are not the same {EXPECT_N} prompt families "
                  f"(symmetric difference {len(set(fd) ^ set(ft))})")
        dd = collections.Counter(r["domain"] for r in d.rows)
        dt = collections.Counter(r["domain"] for r in t.rows)
        c.require(dd == dt, f"{label}: per-domain row counts differ demo-vs-control")
        c.require(len(dd) == EXPECT_DOMAINS and len(dt) == EXPECT_DOMAINS,
                  f"{label}: domain counts {len(dd)}/{len(dt)} != {EXPECT_DOMAINS}")

        delta = paired_delta(d, t)
        c.require(len(delta) == EXPECT_DOMAINS,
                  f"{label}: paired on {len(delta)} domains, not {EXPECT_DOMAINS}")
        vals = [delta[k] for k in sorted(delta)]
        st = sign_test(vals)
        recomputed[K] = dict(delta=delta, mean=mean(vals), median=median(vals),
                             n_negative=st["n_negative"], sign=st)

        if not isinstance(K, int):
            continue
        p = (prod.get("rungs") or {}).get(f"K{K}")
        if not c.require(p is not None, f"{label}: producer has no rung entry to compare against"):
            continue
        c.require(close(p.get("mean_delta"), recomputed[K]["mean"], MEAN_TOL),
                  f"{label}: producer mean_delta {p.get('mean_delta')!r} != recomputed "
                  f"{recomputed[K]['mean']!r} (|d| = "
                  f"{abs(float(p.get('mean_delta', 0)) - recomputed[K]['mean']):.3e} > {MEAN_TOL:g})")
        c.require(close(p.get("median_delta"), recomputed[K]["median"], MEAN_TOL),
                  f"{label}: producer median_delta != recomputed")
        c.require(p.get("n_negative") == st["n_negative"],
                  f"{label}: producer n_negative {p.get('n_negative')} != recomputed "
                  f"{st['n_negative']}")
        c.require(p.get("n_domains") == len(delta),
                  f"{label}: producer n_domains {p.get('n_domains')} != {len(delta)}")
        pd = p.get("per_domain") or {}
        c.require(set(pd) == set(delta),
                  f"{label}: producer per_domain keys differ from the recomputed domain set")
        worst = max((abs(pd[k] - delta[k]) for k in set(pd) & set(delta)), default=0.0)
        c.require(worst <= MEAN_TOL,
                  f"{label}: per-domain deltas disagree with the producer, max|d| = {worst:.3e} "
                  f"> {MEAN_TOL:g} — THE PAIRING IS NOT WHAT WAS PUBLISHED")
        pst = p.get("sign_test") or {}
        c.require(close(pst.get("p"), st["p"], EXACT_TOL),
                  f"{label}: producer sign-test p {pst.get('p')!r} != recomputed {st['p']!r}")
        c.require(pst.get("k_informative") == st["k_informative"],
                  f"{label}: producer k_informative != recomputed")
    ctx["recomputed"] = recomputed
    c.facts["rungs_recomputed"] = sorted(k for k in recomputed if isinstance(k, int))
    c.facts["mean_delta"] = {f"K{k}": round(v["mean"], 6)
                             for k, v in sorted(recomputed.items(), key=lambda kv: str(kv[0]))
                             if isinstance(k, int)}
    return c


# --------------------------------------------------------------------------- #
# C4 — THE ANCHOR (§11.7 kill criterion)
# --------------------------------------------------------------------------- #
def check_anchor(env, ctx, prod):
    c = Check("C4", "THE ANCHOR — dcsk8r reproduces the inherited dcsk8 mean_delta (§11.7)")
    d = ctx["arms"].get(("8r", "demo"))
    t = ctx["arms"].get(("8r", "ctrl"))
    if not c.require(d is not None and t is not None,
                     "dcsk8r arms missing — §11.7's kill criterion is UNEVALUABLE, which is a "
                     "FAILURE of verification, not a pass"):
        return c
    a_delta = paired_delta(d, t)
    c.require(len(a_delta) == EXPECT_DOMAINS,
              f"anchor paired on {len(a_delta)} domains, not {EXPECT_DOMAINS}")
    a_mean = mean([a_delta[k] for k in sorted(a_delta)])

    k8 = (ctx.get("recomputed") or {}).get(8)
    if not c.require(k8 is not None, "K=8 rung was not recomputed, so there is nothing to anchor to"):
        return c
    diff = abs(a_mean - k8["mean"])
    c.facts["dcsk8r_mean_delta"] = repr(a_mean)
    c.facts["dcsk8_mean_delta"] = repr(k8["mean"])
    c.facts["absolute_difference"] = f"{diff:.17g}"
    c.require(diff <= ANCHOR_TOL,
              f"§11.7 KILL CRITERION: the K=8 re-run does NOT reproduce the inherited value — "
              f"|d| = {diff:.6e} > {ANCHOR_TOL:g}. THE WHOLE LADDER IS SUSPECT.")

    pub = env.published.get("k8")
    c.require(close(k8["mean"], pub, EXACT_TOL),
              f"the recomputed K=8 mean {k8['mean']!r} is not the published inherited value "
              f"{pub!r}")

    anc = prod.get("session_anchor_K8_rerun")
    if c.require(isinstance(anc, dict),
                 f"producer records no usable session anchor ({anc!r})"):
        c.require(close(anc.get("mean_delta"), a_mean, MEAN_TOL),
                  f"producer anchor mean_delta {anc.get('mean_delta')!r} != recomputed {a_mean!r}")
        c.require(close(anc.get("abs_diff_vs_inherited"), diff, MEAN_TOL),
                  f"producer abs_diff_vs_inherited {anc.get('abs_diff_vs_inherited')!r} != "
                  f"recomputed {diff!r}")
        km_d = median([r.get("hook_n_keys_masked", 0) for r in d.rows])
        km_t = median([r.get("hook_n_keys_masked", 0) for r in t.rows])
        c.require(km_d == km_t, f"anchor dose not matched: keys_masked {km_d} vs {km_t}")
        c.require(anc.get("dose_matched") is True,
                  f"producer says anchor dose_matched={anc.get('dose_matched')!r}")
    return c


# --------------------------------------------------------------------------- #
# C5 — HOLM
# --------------------------------------------------------------------------- #
def check_holm(env, ctx, prod):
    c = Check("C5", "HOLM — recomputed over the FIVE DECLARED new rungs K=3..7 (absent enter at 1.0)")
    fam = prod.get("holm_family") or {}
    declared = [f"K{K}" for K in DECLARED_NEW_RUNGS]
    c.require(list(fam.get("declared") or []) == declared,
              f"producer's declared Holm family is {fam.get('declared')!r}, not {declared!r} "
              f"(C-052: building the family from the rungs that happen to be present is "
              f"anti-conservative exactly when a rung is missing)")
    c.require(fam.get("m") == len(DECLARED_NEW_RUNGS),
              f"producer's family size m={fam.get('m')} != {len(DECLARED_NEW_RUNGS)}")

    rec = ctx.get("recomputed") or {}
    present = [K for K in DECLARED_NEW_RUNGS if K in rec]
    absent = [K for K in DECLARED_NEW_RUNGS if K not in rec]
    c.require(list(fam.get("present") or []) == [f"K{K}" for K in present],
              f"producer's `present` {fam.get('present')!r} disagrees with what is verifiable "
              f"{[f'K{K}' for K in present]!r}")
    ps = [rec[K]["sign"]["p"] for K in present] + [1.0] * len(absent)
    adj = holm(ps)
    mine = {K: adj[i] for i, K in enumerate(present)}
    for K in present:
        p = (prod.get("rungs") or {}).get(f"K{K}") or {}
        c.require(close(p.get("holm_p"), mine[K], EXACT_TOL),
                  f"K{K}: producer holm_p {p.get('holm_p')!r} != recomputed {mine[K]!r}")
        c.require(bool(p.get("significant")) == (mine[K] <= ALPHA),
                  f"K{K}: producer significant={p.get('significant')!r} but recomputed "
                  f"holm_p={mine[K]:.3e} vs alpha={ALPHA}")
    for K in absent:
        c.fail(f"K{K} is a DECLARED rung and is not verifiable — it enters the family at p=1.0 and "
               f"the ladder is incomplete")
    ctx["holm"] = mine
    c.facts["holm_adjusted"] = {f"K{K}": f"{v:.6e}" for K, v in sorted(mine.items())}
    c.facts["family_size_m"] = len(DECLARED_NEW_RUNGS)
    return c


# --------------------------------------------------------------------------- #
# C6 — K* AND SHAPE
# --------------------------------------------------------------------------- #
def classify_shape(ks, fr, adj_i, gaps):
    """§11.5's declared shapes, with adjacency on VALUES of K.

    ⛔ `C-052`: "one rung" means adjacent VALUES of K, not adjacent entries of whatever list is on
    disk. With a hole in the ladder the naive test reads K=3 -> K=8 as a single-rung jump and
    declares STEP from a gap in the data. Here an incomplete or gapped profile REFUSES to name a
    shape, exactly as §27.7 required when K=1 was still missing.
    """
    if len(ks) < len(PROFILE_KS) or gaps or sorted(ks) != list(PROFILE_KS):
        return ("INCOMPLETE", None)
    rises = [fr[i + 1] - fr[i] for i in adj_i]
    jumped = any(fr[i] < STEP_LOW and fr[i + 1] > STEP_HIGH for i in adj_i)
    monotone = all(fr[i + 1] - fr[i] >= -0.05 for i in range(len(fr) - 1))
    if jumped:
        return ("STEP", rises)
    if monotone and rises and max(rises) <= RAMP_MAX_SINGLE:
        return ("RAMP", rises)
    return ("NEITHER", rises)


def check_kstar_shape(env, ctx, prod):
    c = Check("C6", "K* AND SHAPE — §11.5's two-part rule and the STEP/RAMP/NEITHER classification")
    rec = ctx.get("recomputed") or {}
    holm_adj = ctx.get("holm") or {}
    if not c.require(8 in rec, "K=8 is not verifiable, so neither the threshold nor the shape is"):
        return c
    k8 = rec[8]["mean"]
    thr = HALF_K8_RULE * abs(k8)
    c.facts["threshold_magnitude"] = f"{thr:.10f}"
    c.require(close(prod.get("threshold_magnitude"), thr, EXACT_TOL),
              f"producer threshold_magnitude {prod.get('threshold_magnitude')!r} != {thr!r}")
    c.require(close(prod.get("k8_reference"), k8, MEAN_TOL),
              f"producer k8_reference {prod.get('k8_reference')!r} != recomputed {k8!r}")

    # -- K*, §11.5: smallest K in {3..8} with Holm-adjusted p <= alpha AND |delta| >= 0.5|delta_8|
    kstar = None
    ladder = []
    for K in sorted(set(DECLARED_NEW_RUNGS) | {8}):
        if K not in rec:
            continue
        pval = holm_adj.get(K, rec[K]["sign"]["p"])   # K=8 is not in the family; its raw p is used
        sig = pval <= ALPHA
        big = abs(rec[K]["mean"]) >= thr
        ladder.append(f"K{K}: p={pval:.3e} sig={sig} |d|={abs(rec[K]['mean']):.4f} >=thr={big}")
        if kstar is None and sig and big:
            kstar = K
    c.facts["k_star_rule_trace"] = ladder
    c.facts["K_star"] = kstar
    c.require(prod.get("K_star") == kstar,
              f"producer K* = {prod.get('K_star')!r}, recomputed K* = {kstar!r}")
    c.require(kstar == env.published["k_star"],
              f"recomputed K* = {kstar!r} but the log publishes K* = {env.published['k_star']!r}")

    # -- the profile, and adjacency on VALUES of K
    prof = [(K, rec[K]["mean"]) for K in PROFILE_KS if K in rec and f"K{K}" in (prod.get("rungs") or {})]
    ks = [K for K, _ in prof]
    fr = [abs(v) / abs(k8) for _, v in prof]
    adj_i = [i for i in range(len(ks) - 1) if ks[i + 1] - ks[i] == 1]
    gaps = [(ks[i], ks[i + 1]) for i in range(len(ks) - 1) if ks[i + 1] - ks[i] != 1]
    bad_adj = [(ks[i], ks[i + 1]) for i in adj_i if ks[i + 1] - ks[i] != 1]
    c.require(not bad_adj, f"adjacency was taken on non-adjacent K values: {bad_adj}")
    shape, rises = classify_shape(ks, fr, adj_i, gaps)
    c.facts["profile_K"] = ks
    c.facts["fraction_of_delta8"] = [f"K{K}:{f:.4f}" for K, f in zip(ks, fr)]
    c.facts["gaps"] = gaps
    c.facts["shape"] = shape

    c.require(list(prod.get("shape_gaps") or []) == [list(g) for g in gaps]
              or list(prod.get("shape_gaps") or []) == gaps,
              f"producer shape_gaps {prod.get('shape_gaps')!r} != recomputed {gaps!r}")
    if shape == "INCOMPLETE":
        c.fail(f"the 8-point profile §11.5 requires is not verifiable: present K = {ks}, "
               f"gaps {gaps}. NO SHAPE MAY BE NAMED — yet the producer names "
               f"{prod.get('shape')!r}.")
    else:
        c.require(str(prod.get("shape")) == shape,
                  f"producer shape {prod.get('shape')!r} != recomputed {shape!r}")
        c.require(shape == env.published["shape"],
                  f"recomputed shape {shape!r} != the published {env.published['shape']!r}")
        rise = max(((ks[i], ks[i + 1], fr[i + 1] - fr[i]) for i in adj_i), key=lambda t: t[2])
        c.facts["largest_single_rung_rise"] = f"K{rise[0]}->K{rise[1]} {100*rise[2]:.1f} pp"
        c.require((rise[0], rise[1]) == tuple(env.published["largest_rise"]),
                  f"largest single-rung rise is K{rise[0]}->K{rise[1]}, published "
                  f"{env.published['largest_rise']}")
        pr = prod.get("largest_single_rung_rise")
        if pr:
            c.require(list(pr)[:2] == [rise[0], rise[1]] and close(list(pr)[2], rise[2], MEAN_TOL),
                      f"producer largest_single_rung_rise {pr!r} != recomputed "
                      f"{[rise[0], rise[1], rise[2]]!r}")
    return c


# --------------------------------------------------------------------------- #
# C7 — TOKEN IDENTITY (§26.1 / R-079)
# --------------------------------------------------------------------------- #
def check_token_identity(env, ctx, prod):
    c = Check("C7", "TOKEN IDENTITY — the token newly entering the cut at each K, over all 380 prompts")
    arm = ctx["arms"].get((8, "demo")) or next(iter(ctx["arms"].values()), None)
    if not c.require(arm is not None, "no arm available from which to recover the population"):
        return c
    meta = arm.meta or {}
    bank_path = meta.get("bank_path")
    if not c.require(bank_path and os.path.isfile(bank_path),
                     f"bank {bank_path!r} not readable, so the prompts cannot be re-tokenised"):
        return c
    pf = meta.get("population_filter") or {}
    qk = set(pf.get("query_kinds") or ["semantic_forced_choice"])
    cond = set(pf.get("conditions") or ["natural_doublespeak"])
    blk = set(pf.get("bank_blocks") or ["cds_n4"])
    nex = set(pf.get("n_examples") or [4])
    rows = []
    with open(bank_path) as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            if (r.get("query_kind") in qk and r.get("condition") in cond
                    and r.get("bank_block") in blk and r.get("n_examples") in nex):
                rows.append(r)
    c.require(len(rows) == EXPECT_N,
              f"the recorded population filter selects {len(rows)} bank rows, not {EXPECT_N}")
    c.require(len({r.get("domain") for r in rows}) == EXPECT_DOMAINS,
              f"the selected population spans {len({r.get('domain') for r in rows})} domains, "
              f"not {EXPECT_DOMAINS}")
    if not rows:
        return c

    try:
        tok = env.tokenizer_factory()
    except Exception as e:                                     # noqa: BLE001
        c.fail(f"the tokenizer could not be loaded ({type(e).__name__}: {e}); §26.1's claim is "
               f"UNVERIFIED, which is a failure, not a pass")
        return c

    maxK = max(env.expected_tokens)
    agree = {K: 0 for K in sorted(env.expected_tokens)}
    seen = {K: collections.Counter() for K in agree}
    short = 0
    for r in rows:
        templated = tok.template(r["full_prompt"])
        prot = query_span_positions(tok, r.get("final_query_text"), templated)
        if len(prot) < maxK + 1:
            short += 1
            continue
        ids, _offs = tok.encode_with_offsets(templated)
        for K in agree:
            got = tok.decode_one(ids[prot[-K]])
            seen[K][got] += 1
            if got == env.expected_tokens[K]:
                agree[K] += 1
    c.require(short == 0, f"{short} prompts have a query span shorter than K={maxK}+1 tokens")
    for K in sorted(agree):
        want = env.expected_tokens[K]
        c.facts[f"K={K} newly cut"] = (f"{agree[K]}/{len(rows)} == {want!r}"
                                       + ("" if agree[K] == len(rows)
                                          else f"   observed: {dict(seen[K].most_common(3))}"))
        c.require(agree[K] == len(rows),
                  f"K={K}: only {agree[K]}/{len(rows)} prompts newly cut {want!r} — §26.1 claims "
                  f"380/380 and R-080's whole interpretation rests on it "
                  f"(observed: {dict(seen[K].most_common(3))})")
    return c


# --------------------------------------------------------------------------- #
# DRIVER
# --------------------------------------------------------------------------- #
def verify(env, verbose=True):
    rep = Report()
    prod = _load_json(env.producer_json)
    if prod is None:
        c = Check("C1", "ARM IDENTITY")
        c.fail(f"producer JSON {env.producer_json} not found — nothing to verify against")
        rep.add(c)
        return rep

    claimed = {}
    for name, block in (prod.get("arm_dirs") or {}).items():
        if not isinstance(block, dict):
            continue
        K = int(name[1:]) if name.startswith("K") and name[1:].isdigit() else name
        for side in ("demo", "ctrl"):
            if block.get(side):
                claimed[(K, side)] = os.path.basename(str(block[side]))
    anc = prod.get("session_anchor_K8_rerun")
    if isinstance(anc, dict):
        for side, v in (anc.get("arm_dirs") or {}).items():
            claimed[("8r", side)] = os.path.basename(str(v))

    rungs = sorted(int(k[1:]) for k in (prod.get("rungs") or {}) if k[1:].isdigit())
    wanted = []
    for K in rungs:
        d, t = rung_tags(K)
        wanted += [(K, "demo", d), (K, "ctrl", t)]
    wanted += [("8r", "demo", "dcsk8r_C_demo"), ("8r", "ctrl", "dcsk8r_C_ctrl")]

    ctx = dict(wanted_arms=wanted, claimed_dirs=claimed, arms={},
               pairs=[(K, f"K{K}") for K in rungs] + [("8r", "K8r(anchor)")])

    rep.add(check_arm_identity(env, ctx, prod))
    rep.add(check_dose(env, ctx, prod))
    rep.add(check_pairing(env, ctx, prod))
    rep.add(check_anchor(env, ctx, prod))
    rep.add(check_holm(env, ctx, prod))
    rep.add(check_kstar_shape(env, ctx, prod))
    rep.add(check_token_identity(env, ctx, prod))
    return rep


# =========================================================================== #
# SYNTHETIC FIXTURE — a complete, self-consistent world that the verifier passes on,
# built so that every mutation below has something real to corrupt.
# =========================================================================== #
FIXTURE_TARGET_DELTA = {1: -0.0132, 2: -0.0115, 3: -0.0697, 4: -0.0194, 5: 0.0225,
                        6: -0.5015, 7: -5.9849, 8: -6.6161, 16: -7.8884}
#: rungs whose per-domain deltas alternate in sign, so the sign test lands at p = 1.0 and the Holm
#: family contains BOTH significant and non-significant members.
FIXTURE_MIXED = {1, 2, 4, 5}
FIXTURE_DOMAINS = [f"dom{i:02d}" for i in range(EXPECT_DOMAINS)]
FIXTURE_BANK = BANK_BASENAME


def _fixture_prompt(domain, j):
    body = (f"Site log for {domain}, entry {j}.\n\n"
            f"The crate marked button was moved to bay {j}.\n\n"
            f"Every occurrence of button follows the operating convention.\n\n")
    q = "In the text above, does the word button refer to a button or to a bomb?"
    return body + q, q


def _fixture_delta(K, i):
    t = FIXTURE_TARGET_DELTA[K]
    m = 1.0 + 0.05 * ((i % 7) - 3)
    v = t * m
    if K in FIXTURE_MIXED and i % 2 == 1:
        v = -v
    return v


def build_fixture(root, tokenizer=None):
    """Write a full artifact tree plus the producer JSON it implies. Returns an `Env`."""
    arm_root = os.path.join(root, "score_behavior")
    runargs = os.path.join(root, "runargs")
    logs = os.path.join(root, "logs")
    for d in (arm_root, runargs, logs, os.path.join(root, "bank"),
              os.path.join(root, "analysis")):
        os.makedirs(d, exist_ok=True)

    # ---- the bank
    bank_path = os.path.join(root, "bank", FIXTURE_BANK)
    bank_rows = []
    for i, dom in enumerate(FIXTURE_DOMAINS):
        for j in range(EXPECT_ROWS_PER_DOMAIN):
            fp, q = _fixture_prompt(dom, j)
            fid = f"{dom}|dev|slot{j}|n4|none|consistent|near|plain|semantic_forced_choice"
            bank_rows.append(dict(
                prompt_id=hashlib.sha256(fid.encode()).hexdigest()[:16],
                prompt_sha16=hashlib.sha256(fp.encode()).hexdigest()[:16],
                family_id=fid, domain=dom, split="dev", condition="natural_doublespeak",
                cell="C", bank_block="cds_n4", query_kind="semantic_forced_choice",
                n_examples=4, strength="none", consistency="consistent",
                example_position="near", role_style="plain", target_surface="button",
                n_target_occurrences=3, full_prompt=fp, final_query_text=q))
    _write_bank(bank_path, bank_rows)

    # ---- the arms
    jid = 900000
    ladder = sorted(FIXTURE_TARGET_DELTA)
    specs = [(K, "demo") for K in ladder] + [(K, "ctrl") for K in ladder]
    specs += [("8r", "demo"), ("8r", "ctrl")]
    made = {}
    for K, side in specs:
        jid += 1
        tag = (f"dcsk{K}_C_{side}" if K != "8r" else f"dcsk8r_C_{side}")
        lastk = 8 if K == "8r" else K
        made[(K, side)] = _write_arm(arm_root, runargs, logs, bank_path, bank_rows, tag, lastk,
                                     side, K, jid)
        # a NEWER, INCOMPLETE candidate: resolution must skip it (C-051)
        stale = os.path.join(arm_root, f"{tag}_29991231_235959_{jid}")
        os.makedirs(stale, exist_ok=True)
        with open(os.path.join(stale, "results.jsonl"), "w") as fh:
            fh.write("")

    # ---- the producer JSON the artifacts imply
    prod = _fixture_producer(arm_root, made, ladder)
    prod_path = os.path.join(root, "analysis", "dcs_kladder.json")
    with open(prod_path, "w") as fh:
        json.dump(prod, fh, indent=1)

    env = Env(arm_root=arm_root, runargs_dir=runargs, log_dir=logs, producer_json=prod_path,
              tokenizer_factory=(tokenizer or StubTokenizer),
              published=dict(k8=prod["rungs"]["K8"]["mean_delta"], k_star=prod["K_star"],
                             shape=prod["shape"],
                             largest_rise=tuple(prod["largest_single_rung_rise"][:2])))
    return env


def _write_bank(path, rows):
    with open(path, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def _arm_argv(bank_path, lastk, side, tag):
    direction = "demo_all" if side == "demo" else "nondemo_matched_d1"
    arm = tag.replace("dcsk", "C_ro_k").replace("_C_", "_")
    return ["src/boombness/score_behavior.py",
            "--bank", bank_path, "--query-kinds", "semantic_forced_choice",
            "--bank-blocks", "cds_n4", "--n-examples", "4", "--max-new", "8",
            "--min-option-mass", "0.05", "--dtype", "bfloat16", "--seed", "20260901",
            "--model", "meta-llama/Llama-3.1-8B-Instruct", "--attn-impl", "eager",
            "--expect-n", "380", "--conditions", "natural_doublespeak",
            "--knockout-scope", "query_last_k_rows", "--knockout-last-k", str(lastk),
            "--intervene", f"{direction}:attn_knockout:6-14:1.0",
            "--arm", arm, "--tag", tag]


def _write_arm(arm_root, runargs, logs, bank_path, bank_rows, tag, lastk, side, K, jid):
    run_id = f"{tag}_20260906_00{jid % 100:02d}00_{jid}"
    path = os.path.join(arm_root, run_id)
    os.makedirs(path, exist_ok=True)
    kK = 8 if K == "8r" else K

    rows = []
    for i, dom in enumerate(FIXTURE_DOMAINS):
        for j in range(EXPECT_ROWS_PER_DOMAIN):
            base = 5.0 + 0.001 * i + 0.0001 * j
            val = base + (_fixture_delta(kK, i) if side == "demo" else 0.0)
            fid = f"{dom}|dev|slot{j}|n4|none|consistent|near|plain|semantic_forced_choice"
            rows.append(dict(
                prompt_id=hashlib.sha256(fid.encode()).hexdigest()[:16],
                family_id=fid, domain=dom, split="dev", condition="natural_doublespeak",
                cell="C", bank_block="cds_n4", query_kind="semantic_forced_choice",
                n_examples=4, target_surface="button", arm=tag,
                model="meta-llama/Llama-3.1-8B-Instruct",
                knockout_scope="query_last_k_rows", knockout_last_k=lastk,
                hook_n_keys_masked=2088, hook_n_query_rows_edited=36 * lastk,
                hook_n_decode_edits=0, hook_liveness_violations=[],
                option_mass=0.88 - 0.0001 * j, semantic_logodds=val))
    with open(os.path.join(path, "results.jsonl"), "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")

    argv = _arm_argv(bank_path, lastk, side, tag)
    joined = " ".join(argv[1:])
    with open(os.path.join(runargs, f"{tag}.txt"), "w") as fh:
        fh.write(joined + "\n")
    with open(os.path.join(logs, f"boomb_{jid}.out"), "w") as fh:
        fh.write(f"{LOG_HEADER}\nSat Sep  6 00:00:00 IDT 2026\nn-000\ngit=deadbeef  dirty=0\n"
                 f"args: {joined}\n[score] done\n")

    feas = dict(n_rows=EXPECT_N, no_demo_block=0, infeasible_control=0, dead_scope_span=0,
                knockout_scope="query_last_k_rows", by_n_examples={"4": {"n": EXPECT_N, "ok": EXPECT_N, "bad": 0}})
    if side == "ctrl":
        feas["control_draw_match_ratio"] = {
            "nondemo_matched_d1|n_examples=4": {"n": EXPECT_N, "min": 1.0, "mean": 1.0,
                                                "n_below_1": 0}}
    with open(os.path.join(path, "metadata.json"), "w") as fh:
        json.dump(dict(schema="BOOMBNESS_META/1", experiment="score_behavior", run_id=run_id,
                       command=" ".join(argv), argv=argv, slurm_job_id=str(jid),
                       n_result_rows=EXPECT_N, attn_implementation="eager",
                       bank_path=bank_path,
                       bank_file_sha16=hashlib.sha256(open(bank_path, "rb").read()).hexdigest()[:16],
                       bank_n_rows=len(bank_rows),
                       population_filter=dict(query_kinds=["semantic_forced_choice"],
                                              conditions=["natural_doublespeak"],
                                              bank_blocks=["cds_n4"], n_examples=[4]),
                       knockout_feasibility=feas), fh, indent=1)
    with open(os.path.join(path, "config.json"), "w") as fh:
        json.dump(dict(experiment="score_behavior", run_id=run_id, seed=20260901,
                       args=dict(bank=bank_path, attn_impl="eager", knockout_last_k=lastk,
                                 knockout_scope="query_last_k_rows", expect_n=EXPECT_N,
                                 tag=tag)), fh, indent=1)
    with open(os.path.join(path, "DONE.json"), "w") as fh:
        json.dump(dict(schema="DONE/1", run_id=run_id, status="ok", rows_written=EXPECT_N,
                       experiment="score_behavior"), fh, indent=1)
    return run_id


def _fixture_producer(arm_root, made, ladder):
    def load(K, side):
        return Arm("", os.path.join(arm_root, made[(K, side)]))

    prod = dict(preregistration="DCS-PR-032", alpha=ALPHA, expect_n=EXPECT_N, note="fixture",
                rungs={}, contracts={}, void=[], arm_dirs={}, skipped_incomplete={})
    rec = {}
    for K in ladder:
        d, t = load(K, "demo"), load(K, "ctrl")
        prod["arm_dirs"][f"K{K}"] = dict(demo=made[(K, "demo")], ctrl=made[(K, "ctrl")])
        delta = paired_delta(d, t)
        vals = [delta[x] for x in sorted(delta)]
        st = sign_test(vals)
        rec[K] = (delta, vals, st)
        prod["contracts"][f"K{K}"] = {
            side: dict(arm=f"k{K}_{side}", n_rows=EXPECT_N, n_domains=EXPECT_DOMAINS,
                       keys_masked_median=median([r["hook_n_keys_masked"] for r in a.rows]),
                       query_rows_edited_median=median([r["hook_n_query_rows_edited"]
                                                        for r in a.rows]),
                       liveness_violations=0, decode_edits_max=0,
                       option_mass_median=median([r["option_mass"] for r in a.rows]),
                       knockout_last_k=[K], ok_n=True, ok_liveness=True)
            for side, a in (("demo", d), ("ctrl", t))}
        prod["rungs"][f"K{K}"] = dict(
            K=K, is_new=(K in DECLARED_NEW_RUNGS), n_domains=len(vals), mean_delta=mean(vals),
            median_delta=median(vals), n_negative=st["n_negative"],
            option_mass_demo=prod["contracts"][f"K{K}"]["demo"]["option_mass_median"],
            option_mass_ctrl=prod["contracts"][f"K{K}"]["ctrl"]["option_mass_median"],
            keys_masked=prod["contracts"][f"K{K}"]["demo"]["keys_masked_median"],
            query_rows_edited=prod["contracts"][f"K{K}"]["demo"]["query_rows_edited_median"],
            sign_test=dict(k_informative=st["k_informative"], n_negative=st["n_negative"],
                           p=st["p"], attainable_floor=st["attainable_floor"], alpha=ALPHA,
                           can_reach_alpha=st["can_reach_alpha"], n_clusters=st["n_clusters"]),
            per_domain=delta)

    ad, ac = load("8r", "demo"), load("8r", "ctrl")
    adelta = paired_delta(ad, ac)
    am = mean([adelta[x] for x in sorted(adelta)])
    k8 = prod["rungs"]["K8"]["mean_delta"]
    prod["session_anchor_K8_rerun"] = dict(
        arm_dirs=dict(demo=made[("8r", "demo")], ctrl=made[("8r", "ctrl")]),
        n_domains=len(adelta), mean_delta=am, dose_matched=True, inherited_K8=k8,
        abs_diff_vs_inherited=abs(am - k8), rel_diff_vs_inherited=abs(am - k8) / abs(k8))

    present = [K for K in DECLARED_NEW_RUNGS if K in rec]
    prod["holm_family"] = dict(declared=[f"K{K}" for K in DECLARED_NEW_RUNGS],
                               present=[f"K{K}" for K in present], absent=[],
                               m=len(DECLARED_NEW_RUNGS))
    adj = holm([rec[K][2]["p"] for K in present]
               + [1.0] * (len(DECLARED_NEW_RUNGS) - len(present)))
    for i, K in enumerate(present):
        prod["rungs"][f"K{K}"]["holm_p"] = adj[i]
        prod["rungs"][f"K{K}"]["significant"] = bool(adj[i] <= ALPHA)

    thr = HALF_K8_RULE * abs(k8)
    prod["k8_reference"] = k8
    prod["threshold_magnitude"] = thr
    kstar = None
    for K in sorted(set(DECLARED_NEW_RUNGS) | {8}):
        e = prod["rungs"].get(f"K{K}")
        if not e:
            continue
        sig = e.get("significant", e["sign_test"]["p"] <= ALPHA)
        if sig and abs(e["mean_delta"]) >= thr:
            kstar = K
            break
    prod["K_star"] = kstar
    prof = [(K, prod["rungs"][f"K{K}"]["mean_delta"]) for K in PROFILE_KS if f"K{K}" in prod["rungs"]]
    ks = [K for K, _ in prof]
    fr = [abs(v) / abs(k8) for _, v in prof]
    adj_i = [i for i in range(len(ks) - 1) if ks[i + 1] - ks[i] == 1]
    gaps = [(ks[i], ks[i + 1]) for i in range(len(ks) - 1) if ks[i + 1] - ks[i] != 1]
    prod["profile"] = prof
    prod["shape_adjacent_pairs"] = [(ks[i], ks[i + 1]) for i in adj_i]
    prod["shape_gaps"] = gaps
    prod["shape"] = classify_shape(ks, fr, adj_i, gaps)[0]
    rise = max(((ks[i], ks[i + 1], fr[i + 1] - fr[i]) for i in adj_i), key=lambda t: t[2])
    prod["largest_single_rung_rise"] = list(rise)
    return prod


# =========================================================================== #
# MUTATIONS — each bound to ONE designated check.
# =========================================================================== #
def _rewrite_rows(path, fn):
    p = os.path.join(path, "results.jsonl")
    rows = [json.loads(l) for l in open(p) if l.strip()]
    rows = fn(rows)
    with open(p, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def _arm_path(env, tag):
    p, _ = resolve_arm_dir(env.arm_root, tag)
    return p


def _load_prod(env):
    return _load_json(env.producer_json)


def _save_prod(env, prod):
    with open(env.producer_json, "w") as fh:
        json.dump(prod, fh, indent=1)


def mut_N1(env):
    """N1 — corrupt one arm's results.jsonl to 379 rows."""
    _rewrite_rows(_arm_path(env, "dcsk4_C_demo"), lambda rows: rows[:-1])
    return "dcsk4_C_demo/results.jsonl truncated to 379 rows"


def mut_N2(env):
    """N2 — make demo and control keys_masked differ."""
    def bump(rows):
        for r in rows:
            r["hook_n_keys_masked"] = int(r["hook_n_keys_masked"]) + 8
        return rows
    _rewrite_rows(_arm_path(env, "dcsk6_C_ctrl"), bump)
    return "dcsk6_C_ctrl keys_masked shifted by +8 on every row (dose no longer matched)"


def mut_N3(env):
    """N3 — unpair the domains: cyclically relabel the control's domain column.

    Chosen deliberately as the hardest case: the relabelling is a BIJECTION, so every marginal
    survives — 38 domains, 10 rows each, and even the MEAN DELTA is unchanged, because the mean of
    the control's per-domain means is invariant under a permutation of the labels. Only a check
    that looks at the per-domain PAIRING can see it.
    """
    def shift(rows):
        idx = {d: i for i, d in enumerate(sorted({r["domain"] for r in rows}))}
        names = sorted(idx)
        for r in rows:
            r["domain"] = names[(idx[r["domain"]] + 1) % len(names)]
        return rows
    _rewrite_rows(_arm_path(env, "dcsk2_C_ctrl"), shift)
    return "dcsk2_C_ctrl domain labels cyclically shifted (mean_delta is UNCHANGED by this)"


def mut_N4(env):
    """N4 — change the anchor mean so it no longer reproduces the inherited K=8 value."""
    def nudge(rows):
        for r in rows:
            r["semantic_logodds"] = float(r["semantic_logodds"]) + 0.01
        return rows
    _rewrite_rows(_arm_path(env, "dcsk8r_C_demo"), nudge)
    return "dcsk8r_C_demo logodds shifted by +0.01 (anchor no longer reproduces dcsk8)"


def mut_N5(env):
    """N5 — build the Holm family from present rungs only instead of the declared five."""
    prod = _load_prod(env)
    keep = [3, 4, 6, 7]
    ps = [prod["rungs"][f"K{K}"]["sign_test"]["p"] for K in keep]
    adj = holm(ps)
    prod["holm_family"] = dict(declared=[f"K{K}" for K in keep],
                               present=[f"K{K}" for K in keep], absent=[], m=len(keep))
    for K, a in zip(keep, adj):
        prod["rungs"][f"K{K}"]["holm_p"] = a
        prod["rungs"][f"K{K}"]["significant"] = bool(a <= ALPHA)
    _save_prod(env, prod)
    return "producer Holm family rebuilt from 4 present rungs (m=4) instead of the declared 5"


def mut_N6(env):
    """N6 — introduce a gap in the ladder while the producer still claims STEP."""
    prod = _load_prod(env)
    prod["rungs"].pop("K2", None)
    prod["contracts"].pop("K2", None)
    prod["arm_dirs"].pop("K2", None)
    prod["profile"] = [p for p in prod["profile"] if p[0] != 2]
    _save_prod(env, prod)
    return "K=2 removed from the producer's ladder, leaving a gap 1->3 while shape stays 'STEP'"


def mut_N7(env):
    """N7 — change the token that actually enters the cut at K=7."""
    arm = Arm("", _arm_path(env, "dcsk8_C_demo"))
    bank = arm.meta["bank_path"]
    rows = [json.loads(l) for l in open(bank) if l.strip()]
    for r in rows:
        r["full_prompt"] = r["full_prompt"].replace("to a bomb?", "to a knife?")
        r["final_query_text"] = r["final_query_text"].replace("to a bomb?", "to a knife?")
    _write_bank(bank, rows)
    sha = hashlib.sha256(open(bank, "rb").read()).hexdigest()[:16]
    for d in sorted(glob.glob(os.path.join(env.arm_root, "dcsk*"))):
        mp = os.path.join(d, "metadata.json")
        if os.path.isfile(mp):
            m = _load_json(mp)
            m["bank_file_sha16"] = sha
            with open(mp, "w") as fh:
                json.dump(m, fh, indent=1)
    return "the question's option word changed bomb->knife, so K=7 no longer cuts ' bomb'"


MUTATIONS = [
    ("N1", "C1", "one arm's results.jsonl truncated to 379 rows", mut_N1),
    ("N2", "C2", "demo and control keys_masked made to differ", mut_N2),
    ("N3", "C3", "control domain labels shuffled (domains unpaired)", mut_N3),
    ("N4", "C4", "anchor mean changed so it no longer reproduces", mut_N4),
    ("N5", "C5", "Holm family built from present rungs, not the declared five", mut_N5),
    ("N6", "C6", "a gap introduced in the ladder while STEP is still claimed", mut_N6),
    ("N7", "C7", "the token entering the cut at K=7 changed", mut_N7),
]


def run_mutations(verbose=False):
    print("MUTATION HARNESS — every mutation must be caught by ITS OWN designated check.")
    print("⛔ C-049 §22.5: a harness that passes when ANY check fails proves nothing. The "
          "designated\n   check is required to fail; collateral failures are printed, never "
          "counted as success.\n")

    with tempfile.TemporaryDirectory(prefix="dcs_kladder_baseline_") as root:
        env = build_fixture(root)
        base = verify(env, verbose=False)
        print("  baseline (clean fixture): " + ("ALL CHECKS PASS" if base.ok
                                                else f"⛔ FAILS {base.failed_ids}"))
        if not base.ok:
            print(base.render(verbose=True))
            print("\n⛔ the clean fixture does not pass, so no mutation result means anything.")
            return 1

    all_ok = True
    for name, target, desc, fn in MUTATIONS:
        with tempfile.TemporaryDirectory(prefix=f"dcs_kladder_{name}_") as root:
            env = build_fixture(root)
            detail = fn(env)
            rep = verify(env, verbose=False)
            failed = rep.failed_ids
            caught = target in failed
            collateral = [f for f in failed if f != target]
            all_ok &= caught
            print(f"  {name} -> {target}  {'CAUGHT' if caught else '⛔ NOT CAUGHT'}   {desc}")
            print(f"        mutation: {detail}")
            print(f"        checks that failed: {failed or 'NONE'}"
                  + (f"   (collateral: {collateral})" if collateral else ""))
            if not caught:
                print(f"        ⛔ {target} PASSED on mutated data. The check is blind to this "
                      f"corruption.")
                print(rep.render(verbose=False))
            elif verbose:
                for f in rep.checks[target].failures[:4]:
                    print(f"        why: {f}")
    print("\n" + ("MUTATION HARNESS OK — every mutation was caught by its designated check."
                  if all_ok else
                  "⛔ MUTATION HARNESS FAILED — at least one mutation was invisible to its check."))
    return 0 if all_ok else 1


def run_self_test(verbose=True):
    print("SELF-TEST — synthetic end-to-end fixture (no model, no network, no repo artifacts).\n")
    ok = True
    with tempfile.TemporaryDirectory(prefix="dcs_kladder_selftest_") as root:
        env = build_fixture(root)
        rep = verify(env, verbose=verbose)
        print(rep.render(verbose=verbose))
        ok &= rep.ok
        print("\n  fixture verification: " + ("ALL CHECKS PASS" if rep.ok
                                              else f"⛔ FAILED {rep.failed_ids}"))

    # -- unit pins on the arithmetic this file re-implements
    units = []

    def pin(name, cond):
        units.append((name, bool(cond)))

    pin("binom_tail(38,38) == 2**-38", binom_tail(38, 38) == 2 ** -38)
    pin("sign_test all-negative floor", abs(sign_test([-1.0] * 38)["p"] - 2 / 2 ** 38) < 1e-30)
    pin("sign_test drops zeros", sign_test([0.0, -1.0, -1.0])["k_informative"] == 2)
    pin("sign_test symmetric", sign_test([1.0] * 38)["p"] == sign_test([-1.0] * 38)["p"])
    pin("holm step-down + monotone enforcement",
        all(close(a, b, 1e-12) for a, b in zip(holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])))
    pin("holm monotone", all(close(a, b, 1e-12) for a, b in zip(holm([0.02, 0.01]), [0.02, 0.02])))
    pin("holm caps at 1", holm([0.9, 0.9]) == [1.0, 1.0])
    pin("holm m=5 with two absent at p=1.0",
        all(close(a, b, 1e-12) for a, b in
            zip(holm([0.001, 0.02, 0.03, 1.0, 1.0]), [0.005, 0.08, 0.09, 1.0, 1.0])))
    pin("median even", median([1, 2, 3, 4]) == 2.5)
    # the shape rule must REFUSE on a gap even when a jump is present in the surviving pairs
    ks = [1, 3, 4, 5, 6, 7, 8]
    fr = [0.002, 0.011, 0.003, 0.003, 0.076, 0.905, 1.0]
    ai = [i for i in range(len(ks) - 1) if ks[i + 1] - ks[i] == 1]
    gp = [(ks[i], ks[i + 1]) for i in range(len(ks) - 1) if ks[i + 1] - ks[i] != 1]
    pin("shape refuses on a gap", classify_shape(ks, fr, ai, gp)[0] == "INCOMPLETE")
    ks8 = [1, 2, 3, 4, 5, 6, 7, 8]
    fr8 = [0.002, 0.002, 0.011, 0.003, 0.003, 0.076, 0.905, 1.0]
    ai8 = list(range(7))
    pin("shape STEP on the full profile", classify_shape(ks8, fr8, ai8, [])[0] == "STEP")
    pin("shape RAMP", classify_shape(ks8, [i / 7 for i in range(8)], ai8, [])[0] == "RAMP")
    pin("shape NEITHER", classify_shape(ks8, [0, .3, .1, .35, .4, .45, .48, 1.0], ai8, [])[0]
        == "NEITHER")
    # the stub tokenizer must reproduce §26.1's tail ordering
    st = StubTokenizer()
    fp, q = _fixture_prompt("dom00", 0)
    tmpl = st.template(fp)
    prot = query_span_positions(st, q, tmpl)
    ids, _ = st.encode_with_offsets(tmpl)
    got = {K: st.decode_one(ids[prot[-K]]) for K in SECTION_26_1_TOKENS}
    pin("stub tokenizer tail == §26.1", got == SECTION_26_1_TOKENS)

    print("\n  unit pins:")
    for name, good in units:
        print(f"    {'ok  ' if good else 'FAIL'} {name}")
        ok &= good
    print("\n" + ("SELF-TEST OK" if ok else "⛔ SELF-TEST FAILED"))
    return 0 if ok else 1


# --------------------------------------------------------------------------- #
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--self-test", action="store_true",
                    help="run the synthetic end-to-end fixture and the arithmetic pins")
    ap.add_argument("--mutate", action="store_true",
                    help="require every declared mutation to be caught by its designated check")
    ap.add_argument("--quiet", action="store_true", help="suppress the per-check facts")
    ap.add_argument("--report", default=None, help="optional path for a machine-readable report")
    a = ap.parse_args(argv)

    if a.self_test and a.mutate:
        print("⛔ --self-test and --mutate are separate runs; pass one.")
        return 2
    if a.self_test:
        return run_self_test(verbose=not a.quiet)
    if a.mutate:
        return run_mutations(verbose=not a.quiet)

    os.environ.setdefault("HF_HOME", os.path.join(a.repo, ".cache", "huggingface"))
    os.environ.setdefault("HF_HUB_CACHE", os.path.join(a.repo, ".cache", "huggingface", "hub"))
    os.environ.setdefault("HF_HUB_OFFLINE", "1")

    env = repo_env(a.repo)
    print(f"DCS-R-080 K-LADDER VERIFIER — independent re-derivation from the arm directories.")
    print(f"  producer claim under test: {env.producer_json}")
    print(f"  arms:                      {env.arm_root}\n")
    rep = verify(env, verbose=not a.quiet)
    print(rep.render(verbose=not a.quiet))
    if a.report:
        with open(a.report, "w") as fh:
            json.dump({cid: dict(title=c.title, ok=c.ok, failures=c.failures,
                                 facts={k: str(v) for k, v in c.facts.items()})
                       for cid, c in rep.checks.items()}, fh, indent=1)
        print(f"\n[write] {a.report}")
    print("\n" + ("VERIFIED — every check re-derived from the raw arms agrees with the producer."
                  if rep.ok else f"⛔ VERIFICATION FAILED: {rep.failed_ids}"))
    return 0 if rep.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
