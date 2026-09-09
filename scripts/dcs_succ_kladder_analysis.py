#!/usr/bin/env python3
"""The analyzer for the CONCEPT-FREE K ladder (`src/boombness/kladder_run.py`, job 872512).

WHAT QUESTION THIS FILE IS ALLOWED TO ANSWER
--------------------------------------------
`PR-032` / `R-080` ran the row ladder on `semantic_forced_choice` -- *"...does the word button refer
to a button or to a bomb?"* -- and found a sharp step at **K = 7**, which is the rung at which the
cut first reaches the literal option token ` bomb` **that the readout's own question supplied**.
`R-083` closed that as CANNOT ANSWER: a step at the token that IS the answer, in an instrument that
handed the model the answer, is partly a result about the instrument.

The new ladder runs on `semantic_one_word` -- *"...what does the word button actually refer to?"* --
which contains the concept word on **0 of 32,544** analysed rows. On that template the rungs are:

    K1-K5  response header + chat scaffold (ZERO query content)
    K6 '?'   K7 ' to'   K8 ' refer'   K9 ' actually'
    K10 ' button'   <- THE CODEWORD, the rung this ladder exists for
    K11 ' word'   K12 ' the'   K13 ' does'   K14 ' what'

THE QUESTION IS ONE BIT: **is the step at K = 10?**

DEFECTS THIS FILE EXISTS TO PREVENT
-----------------------------------
1. **A control band that is secretly n = 1.** This project has published one twice. Three
   `nondemo_matched_d{1,2,3}` arms whose draws are not demonstrably three different draws are a
   REFUSAL here, checked two ways -- the three persisted draw seeds must be distinct integers AND
   the three per-row readout vectors must not be pairwise identical -- and the BETWEEN-DRAW sd is
   reported as its own number rather than buried inside a band mean.
2. **A shape read off a hole in the data.** `C-052`: "one rung" means ADJACENT VALUES OF K, never
   adjacent entries of whatever list happens to be on disk. Inherited verbatim.
3. **A denominator that contains the hypothesis.** The old analyzer normalised the profile by
   |delta_K8|, a rung already known to be large. Normalising this ladder by K = 10 would build the
   answer into the scale, so the profile is normalised by the family MAXIMUM -- a quantity no
   hypothesis names. The 0.20/0.50 band and the 0.40 single-rung ramp cap are inherited unchanged
   from `PR-032` section 11.5 so the two ladders' shape verdicts remain comparable.
4. **A rung that is not the rung it claims to be.** Every arm's persisted `surface_span_positions`
   is re-derived against `seq_len` and the row's own query span: rung K must cut exactly the last K
   query rows, ending at the last token, on every row. See LIMITATION below for what this still
   cannot check.
5. **Two arms scored on two populations.** Rows are paired on the COMPOUND key
   `(prompt_id, prompt_sha16)` -- `prompt_id` is not unique across banks, verified this session --
   and every arm must carry the identical key set, the identical bank path and the identical
   argv-vs-config.json settings.

LIMITATION, STATED BECAUSE THE ARTIFACTS CANNOT CLOSE IT
-------------------------------------------------------
Under `--knockout-scope query_last_k_rows` `score_behavior` persists the cut POSITIONS but not
their DECODED TEXT (`surface_span_decoded` is written only on the declared-`rel_end` path). So this
analyzer can prove that rung K cut the last K query rows -- and therefore that it reached
`rel_end = -K` -- but the identity of the token at `rel_end = -10` rests on the frozen token-role
map (`reports/DCS_TS116M_TOKEN_ROLE_MAP.md`, constant in 6900/6900 prompts) and NOT on these run
dirs. The rung->token column is imported from the runner's own `REL_END_ROLE` and cross-checked
against the copy the runner persisted in its manifest; it is never retyped here.

DISCIPLINE
  * EXPLORATORY, TRAIN. Everything printed by this file is a development observation. A rung
    comparison that becomes a claim is frozen in a preregistration and tested once, elsewhere.
  * The independence unit is the DOMAIN. Rows are never counted as independent samples.
  * Every p is printed BESIDE its attainable floor (two-sided sign test floor at n is 2/2**n).
  * Missing != zero: a missing critical field is a refusal, never a default.
  * A gate that passes on an empty selection is not a gate: empty bindings are refused.

USAGE
  python3 scripts/dcs_succ_kladder_analysis.py            # after job 872512 finishes
  python3 scripts/dcs_succ_kladder_analysis.py --selftest
  python3 scripts/dcs_succ_kladder_analysis.py --mutate
"""
from __future__ import annotations

import argparse
import ast
import glob
import hashlib
import importlib
import json
import math
import os
import statistics
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))
from clustered_stats import cluster_bootstrap_ci, cluster_sign_test  # noqa: E402  -- REUSED

RUNNER = os.path.join(REPO, "src", "boombness", "kladder_run.py")
SCORE_ROOT = os.path.join(REPO, "outputs", "boombness", "score_behavior")
MANIFEST = os.path.join(REPO, "outputs", "boombness", "kladder_runner",
                        "ts116m_sowk_train_MANIFEST.json")
SPLIT_MANIFEST = os.path.join(REPO, "data", "boombness_prompts", "dcs_ts116_domain_split.json")
DEFAULT_OUT = os.path.join(REPO, "outputs", "dcs_succ", "kladder_sowk_train.json")

#: The three whole-population exclusions (preregistered, applied before any analysis).
EXCLUDED_DOMAINS = ("restaurant_kitchen", "school_campus", "subway_station")
BASELINE_ARM = "K0_baseline"
PRIMARY = "semantic_logodds"
SECONDARY = ("p_concept", "p_codeword")
#: Fields without which a row cannot be analysed. Absence raises; it never defaults to zero.
REQUIRED_ROW_FIELDS = ("prompt_id", "prompt_sha16", "domain", "cell", "query_kind", "arm",
                       "option_mass", PRIMARY) + SECONDARY
#: Extra fields required of any arm that carries a knockout, so the rung geometry is checkable.
REQUIRED_KO_FIELDS = ("knockout_scope", "knockout_last_k", "surface_span_positions",
                      "surface_span_n_tokens", "seq_len", "query_span_bounds",
                      "n_query_span_positions", "hook_n_edits", "hook_n_keys_masked",
                      "hook_n_query_rows_edited", "hook_liveness_violations")

#: NO FROZEN PREREGISTRATION GOVERNS THIS LADDER, and this file does not pretend one does. The
#: house rule is that an analyzer reads its thresholds from a frozen config via
#: `scripts/dcs_ts_prereg.py` rather than from duplicated prose -- which is exactly why nothing is
#: loaded here: `configs/` carries no entry for the concept-free ladder, so there is no gate to
#: load and inventing a link to an unrelated one would be worse than declaring the constants in
#: the open. Everything below is therefore an EXPLORATORY default, and no number this file prints
#: may be promoted to a claim without a NEW preregistration that fixes these values first. The one
#: threshold that is NOT a default here is the option-mass gate: it is read from the run's own
#: recorded configuration (the manifest's `min_option_mass`, cross-checked against every arm's
#: persisted config.json), never retyped.
PREREG = None
ALPHA = 0.05
#: ---- THE SHAPE RULE, DECLARED HERE AND APPLIED VERBATIM BELOW -------------------------------
#: Let f_K = |mean_delta_K| / max_j |mean_delta_j| over the DECLARED rung family (normalised by the
#: family maximum, never by a named rung -- defect 3 above). Rises are taken over ADJACENT VALUES
#: OF K only (defect 2). Then:
#:   STEP   iff some adjacent rise carries at least STEP_DOMINANCE of the full 0..1 climb AND that
#:          rise crosses the inherited band, from below STEP_LOW to above STEP_HIGH.
#:   RAMP   iff the profile is monotone within RAMP_MONOTONE_TOL and NO single adjacent rise
#:          exceeds RAMP_MAX_SINGLE.
#:   otherwise NEITHER, reported as such with no mechanism claimed.
#: STEP and RAMP are disjoint by construction (0.50 > 0.40). K* is the K at the TOP of the largest
#: adjacent rise -- the rung that the climb happens ON, which is not in general the largest rung.
STEP_LOW, STEP_HIGH = 0.20, 0.50      # PR-032 section 11.5, inherited unchanged
STEP_DOMINANCE = 0.50
RAMP_MAX_SINGLE = 0.40                # PR-032 section 11.5, inherited unchanged
RAMP_MONOTONE_TOL = 0.05


class Refusal(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
# small arithmetic (pure python: this analyzer must run on the login node)
# --------------------------------------------------------------------------- #
def mean(v):
    v = list(v)
    return sum(v) / len(v) if v else float("nan")


def sd(v):
    v = list(v)
    if len(v) < 2:
        return float("nan")
    m = sum(v) / len(v)
    return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))


def median_true(v):
    """The gate statistic `score_behavior.option_mass_block` computes, recomputed here.

    NOT an import: `score_behavior` pulls in torch and this file must stay runnable where torch is
    not. The copy is disciplined by an AGREEMENT ASSERTION instead -- every arm's recomputed value
    is checked against the `median_true` the producer wrote into its own summary.json, and a
    disagreement is a refusal. A second copy of a gate is a second gate unless it is pinned to the
    first one, which is what that assertion does.
    """
    v = sorted(x for x in v if x is not None and not (isinstance(x, float) and math.isnan(x)))
    if not v:
        raise Refusal("option_mass is empty or all-NaN: a gate that passes on an empty selection "
                      "is not a gate")
    return statistics.median(v)


def holm(pvals):
    """Holm-Bonferroni over the family; adjusted p in the input order.

    Same algorithm as `scripts/dcs_kladder_analysis.holm`, reimplemented rather than imported
    because that module imports numpy, which is absent from the login-node interpreter. The
    selftest imports the original when numpy IS available and asserts the two agree, so the
    duplication is pinned rather than merely repeated.
    """
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m, adj, prev = len(pvals), [0.0] * len(pvals), 0.0
    for rank, i in enumerate(idx):
        v = min(1.0, (m - rank) * pvals[i])
        prev = max(prev, v)
        adj[i] = prev
    return adj


def sha16(path):
    if not os.path.exists(path):
        raise Refusal("pinned artifact %r does not exist; its provenance is not verifiable and "
                      "this analyzer does not report unverified provenance" % path)
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def boot_ci(deltas_by_domain, n_boot, seed):
    """Domain-level bootstrap CI of the mean paired delta. Resamples DOMAINS, not rows."""
    rows = [{"d": d, "v": v} for d, v in sorted(deltas_by_domain.items())]
    if not rows:
        raise Refusal("bootstrap asked for an empty domain set")
    pt, lo, hi = cluster_bootstrap_ci(rows, lambda r: r["d"],
                                      lambda rr: mean(r["v"] for r in rr),
                                      n_boot=n_boot, seed=seed)
    return dict(point=pt, lo=lo, hi=hi, n_boot=n_boot,
                caveat=("the cluster bootstrap under-covers below ~30 clusters; n=%d here"
                        % len(rows)))


# --------------------------------------------------------------------------- #
# provenance: the rung -> token map comes FROM THE RUNNER
# --------------------------------------------------------------------------- #
def _ast_constant(path, name):
    """Read a module-level literal out of a source file WITHOUT executing it."""
    with open(path, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=path)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    return ast.literal_eval(node.value)
    raise Refusal("%s does not define %s at module level; the rung->token map cannot be taken "
                  "from the runner and this file will NOT retype it" % (path, name))


def rung_roles(runner_path, manifest, mode="auto"):
    """(REL_END_ROLE, QUERY_SPAN_ROWS, source) taken from the RUNNER, cross-checked with manifest.

    `mode='import'` executes the runner module (which drags in torch via score_behavior);
    `mode='ast'` reads the same two literals out of the same file without executing it. `auto`
    tries the executed import and falls back. Either way the result must agree with the copy the
    runner PERSISTED in its manifest -- if the file on disk has drifted from the file that produced
    these run dirs, the rung labels are wrong and that is a refusal, not a footnote.
    """
    src, roles, span = None, None, None
    if mode in ("auto", "import"):
        try:
            mod = importlib.import_module("kladder_run")
            roles = {int(k): v for k, v in mod.REL_END_ROLE.items()}
            span = int(mod.QUERY_SPAN_ROWS)
            src = "import kladder_run"
        except Exception as e:  # noqa: BLE001 -- torch may be absent; the AST path is equivalent
            if mode == "import":
                raise Refusal("--roles-source import failed: %r" % (e,))
    if roles is None:
        roles = {int(k): v for k, v in _ast_constant(runner_path, "REL_END_ROLE").items()}
        span = int(_ast_constant(runner_path, "QUERY_SPAN_ROWS"))
        src = "ast(%s)" % os.path.basename(runner_path)

    persisted = manifest.get("rung_roles")
    if not persisted:
        raise Refusal("the manifest carries no rung_roles; the runner's map cannot be cross-"
                      "checked against the map that actually ran")
    mine = {str(k): v for k, v in roles.items()}
    if mine != dict(persisted):
        diff = sorted(set(mine) | set(persisted),
                      key=lambda k: int(k) if k.lstrip("-").isdigit() else 0)
        bad = [(k, persisted.get(k), mine.get(k)) for k in diff if persisted.get(k) != mine.get(k)]
        raise Refusal("the runner source's REL_END_ROLE disagrees with the map persisted in the "
                      "manifest, so the rung labels do not describe these runs: %r" % (bad,))
    return roles, span, src


# --------------------------------------------------------------------------- #
# arm discovery and loading
# --------------------------------------------------------------------------- #
def find_arm_dir(root, tag):
    """The ONE completed run dir for `tag`, or a refusal.

    C-051: selecting `hits[-1]` unconditionally reports a rung as NOT RUN when a partial dir sorts
    newest. C-051's fix picked the newest COMPLETE dir; this file goes further and refuses when two
    complete dirs match, because choosing between two completed populations by mtime is how two
    arms end up scored on different data.
    """
    hits = sorted(glob.glob(os.path.join(root, tag + "_*")))
    if not hits:
        raise Refusal("MISSING ARM: no run dir matches %s_* under %s" % (tag, root))
    done = [h for h in hits if os.path.exists(os.path.join(h, "DONE.json"))]
    if not done:
        raise Refusal("ARM WITHOUT DONE.json: %s matches %s but none carries a DONE.json. A run "
                      "without DONE.json may have stopped mid-population; it is not read."
                      % ([os.path.basename(h) for h in hits], tag))
    if len(done) > 1:
        raise Refusal("%d COMPLETED run dirs match %s: %s. Refusing to pick one by mtime."
                      % (len(done), tag, [os.path.basename(h) for h in done]))
    return done[0]


def _same(a, b):
    if a is None or b is None:
        return False
    if str(a) == str(b):
        return True
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return False


def config_vs_argv(cfg_args, argv):
    """Disagreements between an arm's persisted config.json and the manifest's argv for that arm.

    The manifest records what the runner MEANT to run; config.json records what score_behavior
    actually parsed. A silent divergence between them (a flag renamed, a default changed under the
    runner, an arm relaunched by hand) makes the manifest a work of fiction, so it is checked
    key-for-key rather than trusted.
    """
    bad = []
    i = 0
    while i < len(argv):
        flag = argv[i]
        if not flag.startswith("--"):
            raise Refusal("manifest argv is not flag/value pairs at %r" % flag)
        if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
            key, val, i = flag[2:].replace("-", "_"), True, i + 1     # a bare switch
        else:
            key, val, i = flag[2:].replace("-", "_"), argv[i + 1], i + 2
        if key not in cfg_args:
            bad.append((key, "ABSENT FROM config.json", val))
            continue
        if not _same(cfg_args[key], val):
            bad.append((key, cfg_args[key], val))
    return bad


def load_arm(root, tag_prefix, arm_rec, manifest_args, split_domains, alpha_readout_key):
    """One arm: its dir, rows, contract and gate verdict -- or a refusal."""
    arm_id = arm_rec["arm_id"]
    d = find_arm_dir(root, "%s_%s" % (tag_prefix, arm_id))
    base = os.path.basename(d)

    done = json.load(open(os.path.join(d, "DONE.json"), encoding="utf-8"))
    cfg = json.load(open(os.path.join(d, "config.json"), encoding="utf-8"))
    summary = json.load(open(os.path.join(d, "summary.json"), encoding="utf-8"))
    meta_path = os.path.join(d, "metadata.json")
    meta = json.load(open(meta_path, encoding="utf-8")) if os.path.exists(meta_path) else {}

    if cfg.get("run_id") != base:
        raise Refusal("%s: config.json run_id %r is not the directory it sits in" % (base, cfg.get("run_id")))
    if done.get("status") != "ok":
        raise Refusal("%s: DONE.json status %r" % (base, done.get("status")))
    disagree = config_vs_argv(cfg.get("args") or {}, arm_rec["argv"])
    if disagree:
        raise Refusal("%s: persisted config.json disagrees with the manifest argv for arm %s: %r"
                      % (base, arm_id, disagree))

    rows = [json.loads(l) for l in open(os.path.join(d, "results.jsonl"), encoding="utf-8")]
    if not rows:
        raise Refusal("%s: results.jsonl is empty" % base)
    if int(done.get("rows_written", -1)) != len(rows):
        raise Refusal("%s: DONE.json says %s rows, results.jsonl has %d"
                      % (base, done.get("rows_written"), len(rows)))
    expect_n = int(manifest_args["expect_n"])
    if len(rows) != expect_n:
        raise Refusal("%s: %d rows, expect_n is %d. A row count that is not the declared "
                      "population is a different population, not a smaller one."
                      % (base, len(rows), expect_n))

    keyed, seen = {}, set()
    for r in rows:
        for f in REQUIRED_ROW_FIELDS:
            if f not in r or r[f] is None:
                raise Refusal("%s: row %r is missing %r. Missing is not zero."
                              % (base, r.get("prompt_id"), f))
        if r["arm"] != arm_id:
            raise Refusal("%s: row carries arm %r, expected %r" % (base, r["arm"], arm_id))
        if r["query_kind"] != manifest_args["query_kinds"]:
            raise Refusal("%s: row query_kind %r != %r" % (base, r["query_kind"],
                                                           manifest_args["query_kinds"]))
        k = (r["prompt_id"], r["prompt_sha16"])
        if k in seen:
            raise Refusal("%s: duplicate compound key %r; pairing would silently average two rows"
                          % (base, k))
        seen.add(k)
        keyed[k] = r

    doms = {r["domain"] for r in rows}
    bad_dom = doms & set(EXCLUDED_DOMAINS)
    if bad_dom:
        raise Refusal("%s: rows from preregistered whole-population exclusions %r" % (base, bad_dom))
    if split_domains is not None and doms != split_domains:
        raise Refusal("%s: domain set is not the declared population (%d rows domains vs %d "
                      "declared; only-in-arm %r, only-in-manifest %r)"
                      % (base, len(doms), len(split_domains),
                         sorted(doms - split_domains)[:5], sorted(split_domains - doms)[:5]))

    con = dict(arm=arm_id, run_dir=base, n_rows=len(rows), n_domains=len(doms),
               wall_seconds=done.get("wall_seconds"), rc=arm_rec.get("rc"))

    K = int(arm_rec["k"] or 0)
    if arm_rec["kind"] == "baseline":
        if cfg["args"].get("intervene") or int(cfg["args"].get("knockout_last_k") or 0):
            raise Refusal("%s: the BASELINE arm's config carries an intervention" % base)
        con["geometry"] = "baseline: no knockout"
    else:
        con["geometry"] = _rung_geometry(rows, K, base)
        con["keys_masked_median"] = statistics.median([r["hook_n_keys_masked"] for r in rows])
        con["query_rows_edited_median"] = statistics.median(
            [r["hook_n_query_rows_edited"] for r in rows])
        viol = sum(_as_count(r["hook_liveness_violations"]) for r in rows)
        if viol:
            raise Refusal("%s: %d liveness violations -- the knockout did not fire where it was "
                          "declared to, which fails in the direction that looks like a clean null"
                          % (base, viol))
        if min(int(r["hook_n_edits"]) for r in rows) <= 0:
            raise Refusal("%s: a row records hook_n_edits == 0: a knockout that never fired"
                          % base)

    # ---- the option-mass gate, recomputed AND checked against the producer's own verdict
    thr = float(manifest_args["min_option_mass"])
    med = median_true([r["option_mass"] for r in rows])
    blk = (summary.get("option_mass") or {}).get(alpha_readout_key)
    if blk is None:
        raise Refusal("%s: summary.json has no option_mass bucket %r" % (base, alpha_readout_key))
    if not _same(blk.get("median_true"), med):
        raise Refusal("%s: recomputed median option mass %.6g disagrees with the producer's "
                      "%r -- the two copies of the gate statistic do not agree"
                      % (base, med, blk.get("median_true")))
    passed = med >= thr
    if bool(blk.get("reportable")) != passed:
        raise Refusal("%s: producer reportable=%r, recomputed gate=%r at threshold %g"
                      % (base, blk.get("reportable"), passed, thr))
    gate_str = str(summary.get("option_mass_gate", ""))
    if passed and not gate_str.startswith("PASS"):
        raise Refusal("%s: the semantic bucket passes but summary.json records %r -- some OTHER "
                      "bucket failed the tail gate and this analyzer cannot say which"
                      % (base, gate_str))
    if passed and int(arm_rec.get("rc", 0)) == 4:
        raise Refusal("%s: exited rc=4 while its semantic option mass passes the gate; the reason "
                      "for the non-zero exit is not the gate this analyzer knows about" % base)
    con.update(option_mass_median_true=med, option_mass_threshold=thr, gate_pass=bool(passed),
               gate_producer=gate_str)

    draw_seeds = ((meta.get("knockout_feasibility") or {}).get("control_draw_seeds") or {})
    return dict(arm_id=arm_id, kind=arm_rec["kind"], k=K, draw=arm_rec.get("draw", ""),
                run_dir=d, rows=keyed, contract=con, gate_pass=bool(passed),
                draw_seeds=draw_seeds, bank=cfg["args"]["bank"],
                exclude=cfg["args"]["exclude_prompt_ids"])


def _as_count(v):
    """`hook_liveness_violations` is a LIST on knockout rows and an int in older artifacts."""
    if isinstance(v, (list, tuple, set)):
        return len(v)
    return int(v or 0)


def _rung_geometry(rows, K, base):
    """Prove, per row, that rung K cut exactly the last K query rows and reached rel_end -K.

    This is the only part of the rung->token claim the ARTIFACTS can carry: the decoded text of the
    cut positions is persisted only on the declared-rel_end path, which this runner does not use.
    """
    if K < 1:
        raise Refusal("%s: a knockout arm with K=%d" % (base, K))
    for f in REQUIRED_KO_FIELDS:
        if f not in rows[0]:
            raise Refusal("%s: knockout rows lack %r, so the rung geometry cannot be verified and "
                          "will NOT be assumed" % (base, f))
    n_bad = 0
    for r in rows:
        pos = sorted(int(x) for x in r["surface_span_positions"])
        lo, hi = (int(x) for x in r["query_span_bounds"])
        seq = int(r["seq_len"])
        ok = (str(r["knockout_scope"]) == "query_last_k_rows"
              and int(r["knockout_last_k"]) == K
              and int(r["surface_span_n_tokens"]) == K
              and len(pos) == K
              and int(r["n_query_span_positions"]) == hi - lo + 1     # query span is contiguous
              and hi == seq - 1                                       # ... and reaches the end
              and pos[-1] == seq - 1 and pos[0] == seq - K)
        n_bad += (not ok)
    if n_bad:
        raise Refusal("%s: %d/%d rows do not cut exactly the last %d query rows ending at the "
                      "final token, so rung K=%d is not the rung it is labelled as"
                      % (base, n_bad, len(rows), K, K))
    return "verified on %d/%d rows: cut == last %d query rows == rel_end -1..-%d" % (
        len(rows), len(rows), K, K)


# --------------------------------------------------------------------------- #
# the paired statistic
# --------------------------------------------------------------------------- #
def paired_domain_deltas(arm, baseline, field):
    """domain -> mean over that domain's PROMPTS of (arm - baseline), paired on the compound key.

    Paired at the prompt and aggregated to the DOMAIN, which is the declared independence unit. A
    key present in one arm and not the other is a refusal: an unmatched population turns a paired
    contrast into an unpaired one without saying so.
    """
    a, b = arm["rows"], baseline["rows"]
    if set(a) != set(b):
        raise Refusal("arm %s and %s do not carry the same (prompt_id, prompt_sha16) key set "
                      "(%d vs %d; %d only in the arm, %d only in the baseline)"
                      % (arm["arm_id"], baseline["arm_id"], len(a), len(b),
                         len(set(a) - set(b)), len(set(b) - set(a))))
    if not a:
        raise Refusal("empty binding: no rows to pair for arm %s" % arm["arm_id"])
    per = defaultdict(list)
    for k, ra in a.items():
        rb = b[k]
        if ra["domain"] != rb["domain"]:
            raise Refusal("key %r is domain %r in %s and %r in the baseline"
                          % (k, ra["domain"], arm["arm_id"], rb["domain"]))
        per[ra["domain"]].append(float(ra[field]) - float(rb[field]))
    return {d: mean(v) for d, v in per.items()}


def summarise_deltas(deltas, alpha, n_boot, seed):
    vals = [deltas[d] for d in sorted(deltas)]
    st = cluster_sign_test(vals, alpha=alpha)
    return dict(n_domains=len(vals), mean_delta=mean(vals), median_delta=statistics.median(vals),
                sd_across_domains=sd(vals),
                n_negative=sum(1 for v in vals if v < 0),
                n_positive=sum(1 for v in vals if v > 0),
                p=st["p"], p_floor=st["attainable_floor"], can_reach_alpha=st["can_reach_alpha"],
                sign_test=dict(st), sign_summary=st.summary(),
                bootstrap=boot_ci(deltas, n_boot, seed))


# --------------------------------------------------------------------------- #
# the control band
# --------------------------------------------------------------------------- #
def control_band(demo, ctrls, baseline, alpha, n_boot, seed):
    """The demo-minus-control contrast at one rung, plus the BETWEEN-DRAW sd, or a refusal.

    THE BAND MUST BE A BAND. This project has twice published a three-draw control band whose three
    draws were one draw wearing three names. Checked two independent ways here, and either failure
    is a refusal rather than a caveat.
    """
    if len(ctrls) < 2:
        raise Refusal("a control BAND needs at least two draws; rung K=%d has %d"
                      % (demo["k"], len(ctrls)))
    # (1) provenance: three distinct persisted draw seeds
    seeds = {}
    for c in ctrls:
        s = c["draw_seeds"].get(c["draw"])
        if s is None:
            raise Refusal("control arm %s does not persist a draw seed for %r "
                          "(metadata.knockout_feasibility.control_draw_seeds). Missing is not "
                          "'the same seed'." % (c["arm_id"], c["draw"]))
        seeds[c["arm_id"]] = int(s)
    if len(set(seeds.values())) != len(seeds):
        raise Refusal("the control band at K=%d has %d arms but only %d distinct draw seeds %r: "
                      "it is not a band, it is one draw with several names"
                      % (demo["k"], len(seeds), len(set(seeds.values())), seeds))
    # (2) empirical: the per-row readouts must not be pairwise identical
    vecs = {c["arm_id"]: [c["rows"][k][PRIMARY] for k in sorted(c["rows"])] for c in ctrls}
    ids = sorted(vecs)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            if vecs[ids[i]] == vecs[ids[j]]:
                raise Refusal("control draws %s and %s produce BYTE-IDENTICAL per-row readouts on "
                              "all %d rows: the same key set was drawn twice"
                              % (ids[i], ids[j], len(vecs[ids[i]])))

    per_draw = {}
    for c in ctrls:
        dd = paired_domain_deltas(c, baseline, PRIMARY)
        per_draw[c["arm_id"]] = dict(draw=c["draw"], seed=seeds[c["arm_id"]],
                                     gate_pass=c["gate_pass"],
                                     mean_delta=mean(dd.values()), deltas=dd,
                                     keys_masked_median=c["contract"].get("keys_masked_median"),
                                     option_mass_median_true=c["contract"]["option_mass_median_true"])
    draw_means = [per_draw[a]["mean_delta"] for a in sorted(per_draw)]

    # the band centre, per domain, is the mean over draws -- so the contrast is against the BAND
    doms = sorted(set.intersection(*[set(per_draw[a]["deltas"]) for a in per_draw]))
    if not doms:
        raise Refusal("empty binding: the control draws share no domain at K=%d" % demo["k"])
    demo_d = paired_domain_deltas(demo, baseline, PRIMARY)
    if set(demo_d) != set(doms):
        raise Refusal("demo and control domain sets differ at K=%d" % demo["k"])
    contrast = {d: demo_d[d] - mean(per_draw[a]["deltas"][d] for a in per_draw) for d in doms}

    dose = {a: per_draw[a]["keys_masked_median"] for a in per_draw}
    dose_ok = all(_same(v, demo["contract"].get("keys_masked_median")) for v in dose.values())
    out = dict(
        K=demo["k"], n_draws=len(ctrls), draw_seeds=seeds,
        per_draw={a: {k: v for k, v in per_draw[a].items() if k != "deltas"} for a in per_draw},
        draw_means=draw_means,
        between_draw_sd=sd(draw_means),
        between_draw_range=(min(draw_means), max(draw_means)),
        band_mean=mean(draw_means),
        demo_mean=mean(demo_d.values()),
        dose_matched=bool(dose_ok),
        dose_keys_masked=dict(demo=demo["contract"].get("keys_masked_median"), controls=dose),
        demo_minus_each_draw={a: mean(demo_d[d] - per_draw[a]["deltas"][d] for d in doms)
                              for a in per_draw})
    out["contrast"] = summarise_deltas(contrast, alpha, n_boot, seed)
    if not dose_ok:
        out["VOID"] = ("DOSE MISMATCH: the control blocks a different number of keys than the "
                       "demonstration arm, so this contrast is not the contrast it claims. The "
                       "rung's demo-vs-baseline delta is unaffected and is still reported.")
    return out


# --------------------------------------------------------------------------- #
# the shape
# --------------------------------------------------------------------------- #
def classify_shape(profile, declared_ks):
    """Apply the rule declared at the top of this file. `profile` is [(K, mean_delta), ...]."""
    out = dict(rule=("f_K = |mean_delta_K| / max_j |mean_delta_j| over the declared family; rises "
                     "over ADJACENT K only; STEP iff a single adjacent rise >= %.2f of the full "
                     "climb AND crosses %.2f -> %.2f; RAMP iff monotone within %.2f and no single "
                     "adjacent rise > %.2f; else NEITHER"
                     % (STEP_DOMINANCE, STEP_LOW, STEP_HIGH, RAMP_MONOTONE_TOL, RAMP_MAX_SINGLE)),
               declared_family=list(declared_ks), present=[K for K, _ in profile])
    missing = [K for K in declared_ks if K not in dict(profile)]
    if missing:
        out["shape"] = ("INCOMPLETE -- rungs %r are not reportable (missing or CANNOT ANSWER); a "
                        "shape read off the rungs that happen to be present is a shape read off a "
                        "hole in the data. No shape called." % missing)
    ks = [K for K, _ in profile]
    vals = [v for _, v in profile]
    if len(ks) < 3:
        out.setdefault("shape", "INCOMPLETE -- fewer than three rungs present")
        return out
    top = max(abs(v) for v in vals)
    if top == 0:
        out["shape"] = "FLAT -- every rung is exactly zero; no shape called"
        return out
    f = [abs(v) / top for v in vals]
    out["profile_normalised"] = list(zip(ks, f))
    out["normaliser"] = dict(statistic="max |mean_delta| over the declared family", value=top,
                             at_K=ks[max(range(len(vals)), key=lambda i: abs(vals[i]))],
                             why=("normalising by a NAMED rung (the old ladder used K=8) puts the "
                                  "hypothesis in the denominator; the family maximum does not"))
    adj = [i for i in range(len(ks) - 1) if ks[i + 1] - ks[i] == 1]
    out["adjacent_pairs"] = [(ks[i], ks[i + 1]) for i in adj]
    out["gaps"] = [(ks[i], ks[i + 1]) for i in range(len(ks) - 1) if ks[i + 1] - ks[i] != 1]
    if not adj:
        out.setdefault("shape", "INCOMPLETE -- no two adjacent rungs are present")
        return out
    rises = [(ks[i], ks[i + 1], f[i + 1] - f[i]) for i in adj]
    biggest = max(rises, key=lambda t: t[2])
    out["largest_single_rung_rise"] = dict(from_K=biggest[0], to_K=biggest[1], rise=biggest[2],
                                           rise_raw=(vals[ks.index(biggest[1])]
                                                     - vals[ks.index(biggest[0])]))
    out["K_star"] = biggest[1]
    out["all_rises"] = rises

    # SIGN COHERENCE. The profile is read in |.|, and |.| is only a scale if every rung that
    # carries material magnitude points the SAME WAY. A ladder with a large positive excursion at
    # one rung and a large negative one at another has no single climb to describe, and calling it
    # STEP would be an artifact of the absolute value.
    signs = [1 if v > 0 else (-1 if v < 0 else 0) for v in vals]
    material = [i for i in range(len(ks)) if f[i] >= STEP_LOW]
    dom_sign = 1 if sum(s > 0 for s in signs) >= sum(s < 0 for s in signs) else -1
    out["sign"] = dict(dominant=dom_sign, n_with_dominant=sum(1 for s in signs if s == dom_sign),
                       material_rungs=[ks[i] for i in material],
                       material_signs=[signs[i] for i in material])
    if len({signs[i] for i in material if signs[i]}) > 1:
        out["shape"] = ("SIGN-INCOHERENT -- rungs %r carry material magnitude in BOTH directions, "
                        "so |mean_delta| is not a scale here. No shape called."
                        % [ks[i] for i in material])
        return out
    if "shape" in out:
        return out                       # INCOMPLETE was already decided; K* is context only
    stepped = [(a, b, r) for (a, b, r) in rises
               if r >= STEP_DOMINANCE and f[ks.index(a)] < STEP_LOW and f[ks.index(b)] > STEP_HIGH]
    monotone = all(f[i + 1] - f[i] >= -RAMP_MONOTONE_TOL for i in range(len(f) - 1))
    if stepped:
        out["shape"] = "STEP"
        out["step_rungs"] = stepped
    elif monotone and max(r for _, _, r in rises) <= RAMP_MAX_SINGLE:
        out["shape"] = "RAMP"
    else:
        out["shape"] = "NEITHER -- reported as such, no mechanism claimed"
    return out


# --------------------------------------------------------------------------- #
# the analysis
# --------------------------------------------------------------------------- #
def analyse(manifest_path, root, runner, split_manifest, alpha=ALPHA, n_boot=3000, seed=20260909,
            roles_source="auto", allow_non_train=False, hash_bank=True):
    man = json.load(open(manifest_path, encoding="utf-8"))
    for f in ("args", "arms", "rung_roles"):
        if f not in man:
            raise Refusal("manifest %s lacks %r" % (manifest_path, f))
    if "finished" not in man:
        raise Refusal("the manifest carries no `finished` timestamp: the ladder is MID-FLIGHT. "
                      "Arms that have not been written yet would be reported as missing and the "
                      "rung family would be scored against a partial ladder.")
    A = man["args"]
    split = str(A.get("split"))
    if split != "train" and not allow_non_train:
        raise Refusal("this analyzer is EXPLORATORY and reads TRAIN only; the manifest says %r"
                      % split)
    if split == "train" and "train" not in os.path.basename(A["exclude_prompt_ids"]):
        raise Refusal("the manifest says split=train but the population is set by "
                      "--exclude-prompt-ids %r, whose name does not say train. The runner's "
                      "--split flag does NOT feed the population (it only names the manifest "
                      "file), so the two must be checked against each other."
                      % os.path.basename(A["exclude_prompt_ids"]))

    roles, span_rows, roles_src = rung_roles(runner, man, roles_source)
    declared_ks = [int(x) for x in str(A["k_list"]).split(",") if x.strip()]
    control_ks = ([int(x) for x in str(A["control_ks"]).split(",") if x.strip()]
                  if A.get("control_ks") else list(declared_ks))
    draws = [d.strip() for d in str(A["controls"]).split(",") if d.strip()]
    if not declared_ks:
        raise Refusal("empty binding: the manifest declares no rungs")

    sm = json.load(open(split_manifest, encoding="utf-8"))
    split_domains = {d for d, s in sm["assign"].items()
                     if s == split and d not in EXCLUDED_DOMAINS}
    if not split_domains:
        raise Refusal("empty binding: the frozen split manifest assigns no %r domains" % split)

    by_id = {a["arm_id"]: a for a in man["arms"]}
    expected = [BASELINE_ARM] + ["K%02d_demo" % k for k in declared_ks]
    expected += ["K%02d_%s" % (k, d) for k in control_ks for d in draws]
    absent = [a for a in expected if a not in by_id]
    if absent:
        raise Refusal("MISSING ARM(S) in the manifest: %r" % absent)
    bad_rc = {a: by_id[a].get("rc") for a in expected if int(by_id[a].get("rc", -1)) not in (0, 4)}
    if bad_rc:
        raise Refusal("arm(s) exited with an rc this analyzer cannot interpret: %r" % bad_rc)

    mass_key = "semantic/%s" % A["query_kinds"]
    arms = {}
    for a in expected:
        arms[a] = load_arm(root, A["tag_prefix"], by_id[a], A, split_domains, mass_key)

    banks = {x["bank"] for x in arms.values()}
    if len(banks) != 1:
        raise Refusal("arms name %d different banks: %r" % (len(banks), sorted(banks)))
    base = arms[BASELINE_ARM]
    if not base["gate_pass"]:
        raise Refusal("the BASELINE arm is below the option-mass gate (%.4g < %.4g). Every rung is "
                      "a delta against it, so the whole ladder is CANNOT ANSWER, not just a rung."
                      % (base["contract"]["option_mass_median_true"],
                         base["contract"]["option_mass_threshold"]))

    res = dict(
        label="EXPLORATORY (train) -- the ladder SHAPE is a development observation, not a claim",
        question=("is the step at K=10, the CODEWORD rung, on a readout that never names the "
                  "concept? (semantic_one_word carries the concept word on 0/32544 rows)"),
        preregistration=("NONE -- exploratory. configs/ carries no frozen entry for the "
                         "concept-free ladder; alpha and the shape thresholds are in-code "
                         "EXPLORATORY defaults, and the option-mass gate is read from the run's "
                         "own recorded min_option_mass."),
        manifest=manifest_path, manifest_started=man.get("started"),
        manifest_finished=man.get("finished"), host=man.get("host"),
        runner_args=A, alpha=alpha, n_boot=n_boot, seed=seed,
        rung_roles_source=roles_src, query_span_rows=span_rows,
        readout=dict(primary=PRIMARY, secondary=list(SECONDARY),
                     query_kind=A["query_kinds"], condition=A["conditions"]),
        population=dict(split=split, n_domains_declared=len(split_domains),
                        n_rows_per_arm=int(A["expect_n"]),
                        exclusions=list(EXCLUDED_DOMAINS),
                        split_manifest=split_manifest,
                        split_manifest_sha16=sm.get("manifest_sha16")),
        provenance=dict(bank=sorted(banks)[0],
                        bank_file_sha16=(sha16(sorted(banks)[0]) if hash_bank else "NOT HASHED"),
                        exclude_prompt_ids=base["exclude"],
                        exclude_file_sha16=(sha16(base["exclude"]) if hash_bank else "NOT HASHED"),
                        model=A["model"], band=A["band"]),
        limitation=("query_last_k_rows persists the cut POSITIONS but not their decoded text, so "
                    "rung K is verified to reach rel_end -K on every row while the IDENTITY of the "
                    "token there rests on the frozen token-role map, not on these run dirs."),
        contracts={a: arms[a]["contract"] for a in sorted(arms)},
        rungs={}, cannot_answer=[], controls={}, holm_families={})

    # ---- per rung: demo minus baseline, paired within domain
    for k in declared_ks:
        arm = arms["K%02d_demo" % k]
        rec = dict(K=k, rel_end_reached=-k, rung_reaches=roles.get(-k, "BEYOND THE MAPPED SPAN"),
                   run_dir=arm["contract"]["run_dir"],
                   option_mass_median_true=arm["contract"]["option_mass_median_true"],
                   gate_pass=arm["gate_pass"], geometry=arm["contract"]["geometry"])
        if not arm["gate_pass"]:
            rec["status"] = ("CANNOT ANSWER: median option mass %.4g < %.4g. The readout is not "
                             "answering the question on this rung; the other rungs are unaffected "
                             "and are still reported."
                             % (arm["contract"]["option_mass_median_true"],
                                arm["contract"]["option_mass_threshold"]))
            res["cannot_answer"].append(k)
        else:
            deltas = paired_domain_deltas(arm, base, PRIMARY)
            rec.update(summarise_deltas(deltas, alpha, n_boot, seed))
            rec["per_domain_delta"] = deltas
            rec["baseline_mean"] = mean(base["rows"][kk][PRIMARY] for kk in base["rows"])
            rec["arm_mean"] = mean(arm["rows"][kk][PRIMARY] for kk in arm["rows"])
            for f in SECONDARY:
                rec["mean_delta_" + f] = mean(paired_domain_deltas(arm, base, f).values())
            rec["status"] = "OK"
        res["rungs"][k] = rec

    # ---- Holm over the DECLARED rung family. A rung that is CANNOT ANSWER enters at p = 1.0 so
    # ---- the present rungs pay their full declared correction (C-052: building the family from
    # ---- what is on disk is anti-conservative exactly when a rung is missing).
    fam = sorted(declared_ks)
    ps = [res["rungs"][k].get("p", 1.0) for k in fam]
    adj = holm(ps)
    for k, p in zip(fam, adj):
        if res["rungs"][k]["status"] == "OK":
            res["rungs"][k]["holm_p"] = p
            res["rungs"][k]["significant_holm"] = bool(p <= alpha)
    res["holm_families"]["rungs"] = dict(
        family=["K%d" % k for k in fam], m=len(fam), alpha=alpha,
        entered_at_p1=["K%d" % k for k in fam if res["rungs"][k]["status"] != "OK"],
        statement="Holm-Bonferroni over the %d DECLARED demo rungs K%d..K%d" % (
            len(fam), fam[0], fam[-1]))

    # ---- the control band at the rungs that carry one
    cfam = sorted(control_ks)
    for k in cfam:
        demo = arms["K%02d_demo" % k]
        ctrls = [arms["K%02d_%s" % (k, d)] for d in draws]
        gated = [c["arm_id"] for c in ctrls if not c["gate_pass"]] + (
            [] if demo["gate_pass"] else [demo["arm_id"]])
        if gated:
            res["controls"][k] = dict(K=k, status="CANNOT ANSWER: below the option-mass gate: %r"
                                                  % gated)
            continue
        res["controls"][k] = control_band(demo, ctrls, base, alpha, n_boot, seed)
    live = [k for k in cfam if "contrast" in res["controls"].get(k, {})]
    cps = [res["controls"][k]["contrast"]["p"] if k in live else 1.0 for k in cfam]
    cadj = holm(cps)
    for k, p in zip(cfam, cadj):
        if k in live:
            res["controls"][k]["contrast"]["holm_p"] = p
            res["controls"][k]["contrast"]["significant_holm"] = bool(p <= alpha)
    res["holm_families"]["control_contrasts"] = dict(
        family=["K%d" % k for k in cfam], m=len(cfam), alpha=alpha,
        entered_at_p1=["K%d" % k for k in cfam if k not in live],
        statement="Holm-Bonferroni over the %d DECLARED control-band contrasts (demo minus the "
                  "mean of the three dose-matched non-demo draws), a SEPARATE family from the "
                  "rung family above" % len(cfam))

    # ---- the shape
    profile = [(k, res["rungs"][k]["mean_delta"]) for k in fam
               if res["rungs"][k]["status"] == "OK"]
    res["profile"] = profile
    res["shape"] = classify_shape(profile, fam)
    return res


# --------------------------------------------------------------------------- #
def render(res):
    L = []
    L.append("=" * 100)
    L.append("CONCEPT-FREE K LADDER -- %s" % res["label"])
    L.append("  %s" % res["question"])
    L.append("  readout %s on %s / %s; band %s; %d domains x %d rows; rung roles from %s"
             % (res["readout"]["primary"], res["readout"]["query_kind"],
                res["readout"]["condition"], res["provenance"]["band"],
                res["population"]["n_domains_declared"], res["population"]["n_rows_per_arm"],
                res["rung_roles_source"]))
    L.append("=" * 100)
    L.append("%3s %-46s %11s %7s %9s %10s %10s %9s %8s"
             % ("K", "rung reaches (rel_end -K)", "mean_delta", "f", "neg/dom", "p", "p_floor",
                "holm", "opt_mass"))
    fn = dict(res["shape"].get("profile_normalised") or [])
    for k in sorted(res["rungs"]):
        e = res["rungs"][k]
        role = str(e["rung_reaches"])[:46]
        if e["status"] != "OK":
            L.append("%3d %-46s   %s" % (k, role, e["status"].split(".")[0]))
            continue
        L.append("%3d %-46s %+11.4f %7.3f %4d/%-4d %10.3e %10.3e %9s %8.3f"
                 % (k, role, e["mean_delta"], fn.get(k, float("nan")), e["n_negative"],
                    e["n_domains"], e["p"], e["p_floor"],
                    ("%.4f" % e["holm_p"]) if "holm_p" in e else "-",
                    e["option_mass_median_true"]))
    L.append("")
    L.append("SHAPE = %s" % res["shape"].get("shape"))
    L.append("  rule: %s" % res["shape"]["rule"])
    r = res["shape"].get("largest_single_rung_rise")
    if r:
        L.append("  largest single-rung rise: K%d -> K%d, %+.3f in f units (%+.4f raw); K* = %s"
                 % (r["from_K"], r["to_K"], r["rise"], r["rise_raw"], res["shape"].get("K_star")))
    L.append("")
    L.append("CONTROL BAND (demo minus the three dose-matched non-demo draws), per rung:")
    for k in sorted(res["controls"]):
        c = res["controls"][k]
        if "contrast" not in c:
            L.append("  K%-3d %s" % (k, c.get("status")))
            continue
        ct = c["contrast"]
        L.append("  K%-3d demo %+8.4f  band %+8.4f  BETWEEN-DRAW sd %.4f over %d draws %s"
                 % (k, c["demo_mean"], c["band_mean"], c["between_draw_sd"], c["n_draws"],
                    ["%+.4f" % x for x in c["draw_means"]]))
        L.append("       contrast %+8.4f  %d/%d neg  p=%.3e (floor %.3e)  holm=%s  dose_matched=%s"
                 % (ct["mean_delta"], ct["n_negative"], ct["n_domains"], ct["p"], ct["p_floor"],
                    ("%.4f" % ct["holm_p"]) if "holm_p" in ct else "-", c["dose_matched"]))
        L.append("       95%% CI [%+.4f, %+.4f] (domain bootstrap, %d draws)"
                 % (ct["bootstrap"]["lo"], ct["bootstrap"]["hi"], ct["bootstrap"]["n_boot"]))
        if "VOID" in c:
            L.append("       VOID: %s" % c["VOID"])
    L.append("")
    for name, f in res["holm_families"].items():
        L.append("HOLM FAMILY %-18s m=%d  %s  (entered at p=1.0: %s)"
                 % (name, f["m"], f["statement"], f["entered_at_p1"] or "none"))
    if res["cannot_answer"]:
        L.append("CANNOT ANSWER rungs (option-mass gate): %r" % res["cannot_answer"])
    L.append("LIMITATION: %s" % res["limitation"])
    L.append("EXPLORATORY (train). No number here is a claim.")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# selftest
# --------------------------------------------------------------------------- #
def _synth(base_dir, *, n_dom=12, per_dom=2, ks=range(1, 15), control_ks=(8, 9, 10, 11),
           step_at=10, effect=-3.0, ramp=False, break_=None, gate_fail_K=None, seed=7):
    """A complete synthetic run tree with a PLANTED shape, written exactly as the runner writes."""
    import random
    rnd = random.Random(seed)
    os.makedirs(base_dir, exist_ok=True)
    root = os.path.join(base_dir, "score_behavior")
    os.makedirs(root, exist_ok=True)
    bank = os.path.join(base_dir, "bank_button_bomb.jsonl")
    excl = os.path.join(base_dir, "exclude_button_bomb_sow_train.txt")
    open(bank, "w").write("{}\n")
    open(excl, "w").write("x\n")

    doms = ["dom%02d" % i for i in range(n_dom)]
    keys = [(d, j) for d in doms for j in range(per_dom)]
    split_path = os.path.join(base_dir, "split.json")
    json.dump({"assign": {d: "train" for d in doms}, "manifest_sha16": "0" * 16},
              open(split_path, "w"))

    base_vals = {k: 1.5 + 0.3 * rnd.gauss(0, 1) for k in keys}
    draws_l = ["nondemo_matched_d1", "nondemo_matched_d2", "nondemo_matched_d3"]
    seq_len, qlo = 208, 180

    def eff(K):
        if ramp:
            return effect * K / max(ks)
        return effect if K >= step_at else 0.0

    def write_arm(arm_id, kind, K, draw, vals, *, no_done=False, cfg_break=False,
                  rename_domain=None, gate_fail=False, draw_seed=None):
        d = os.path.join(root, "ts116m_sowk_%s_20260909_000000_1" % arm_id)
        os.makedirs(d, exist_ok=True)
        argv = ["--bank", bank, "--query-kinds", "semantic_one_word",
                "--conditions", "natural_doublespeak", "--n-examples", "4",
                "--readout-ids", "whole_answer", "--attn-impl", "eager", "--max-new", "8",
                "--min-option-mass", "0.05", "--dtype", "bfloat16",
                "--model", "meta-llama/Llama-3.1-8B-Instruct", "--seed", "20260909",
                "--exclude-prompt-ids", excl, "--expect-n", str(len(keys)),
                "--arm", arm_id, "--tag", "ts116m_sowk_%s" % arm_id]
        if kind != "baseline":
            argv += ["--intervene", "%s:attn_knockout:6-14:1.0" % (
                "demo_all" if kind == "demo" else draw),
                "--knockout-scope", "query_last_k_rows", "--knockout-last-k", str(K)]
        cargs = {"bank": bank, "query_kinds": "semantic_one_word",
                 "conditions": "natural_doublespeak", "n_examples": "4",
                 "readout_ids": "whole_answer", "attn_impl": "eager", "max_new": 8,
                 "min_option_mass": 0.05, "dtype": "bfloat16",
                 "model": "meta-llama/Llama-3.1-8B-Instruct", "seed": 20260909,
                 "exclude_prompt_ids": excl, "expect_n": len(keys), "arm": arm_id,
                 "tag": "ts116m_sowk_%s" % arm_id,
                 "intervene": "" if kind == "baseline" else argv[argv.index("--intervene") + 1],
                 "knockout_scope": ("legacy_all_query" if kind == "baseline"
                                    else "query_last_k_rows"),
                 "knockout_last_k": 0 if kind == "baseline" else K}
        if cfg_break:
            cargs["n_examples"] = "8"
        json.dump({"experiment": "score_behavior", "run_id": os.path.basename(d), "args": cargs},
                  open(os.path.join(d, "config.json"), "w"))
        om = 0.02 if gate_fail else 0.33
        rows = []
        for (dom, j) in keys:
            r = {"prompt_id": "%s_%d" % (dom, j), "prompt_sha16": "s%s%d" % (dom, j),
                 "domain": ("dom99" if dom == rename_domain else dom),
                 "cell": "C", "condition": "natural_doublespeak",
                 "query_kind": "semantic_one_word", "arm": arm_id,
                 "option_mass": om, "semantic_logodds": vals[(dom, j)],
                 "p_concept": 0.4, "p_codeword": 0.1}
            if kind != "baseline":
                r.update({"knockout_scope": "query_last_k_rows", "knockout_last_k": K,
                          "surface_span_positions": list(range(seq_len - K, seq_len)),
                          "surface_span_n_tokens": K, "seq_len": seq_len,
                          "query_span_bounds": [qlo, seq_len - 1],
                          "n_query_span_positions": seq_len - qlo,
                          "hook_n_edits": 1728, "hook_n_keys_masked": 1728,
                          "hook_n_query_rows_edited": 36, "hook_liveness_violations": []})
            rows.append(r)
        with open(os.path.join(d, "results.jsonl"), "w") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")
        json.dump({"option_mass": {"semantic/semantic_one_word": {
                       "n": len(rows), "median_true": om, "reportable": om >= 0.05}},
                   "option_mass_gate": "PASS" if om >= 0.05 else "OVERRIDDEN — NOT REPORTABLE"},
                  open(os.path.join(d, "summary.json"), "w"))
        json.dump({"knockout_feasibility": ({"control_draw_seeds": {draw: draw_seed}}
                                            if draw_seed is not None else {})},
                  open(os.path.join(d, "metadata.json"), "w"))
        if not no_done:
            json.dump({"status": "ok", "rows_written": len(rows), "wall_seconds": 1.0},
                      open(os.path.join(d, "DONE.json"), "w"))
        return dict(arm_id=arm_id, kind=kind, k=K, draw=draw, argv=argv,
                    rc=(4 if gate_fail else 0))

    arms = [write_arm(BASELINE_ARM, "baseline", 0, "", base_vals)]
    for K in ks:
        vals = {k: base_vals[k] + eff(K) + 0.02 * rnd.gauss(0, 1) for k in keys}
        arms.append(write_arm("K%02d_demo" % K, "demo", K, "", vals,
                              no_done=(break_ == "no_done" and K == 3),
                              cfg_break=(break_ == "config_argv" and K == 4),
                              rename_domain=("dom00" if break_ == "domain_mismatch" and K == 5
                                             else None),
                              gate_fail=(gate_fail_K == K)))
        if K in control_ks:
            for i, dr in enumerate(draws_l, 1):
                same = (break_ == "identical_draws")
                off = 0.0 if same else 0.05 * i
                cv = {k: base_vals[k] - 0.2 + off + (0.0 if same else 0.01 * rnd.gauss(0, 1))
                      for k in keys}
                # identical_draws collides the READOUTS while leaving the seeds distinct, so
                # only the empirical check can fire; identical_seeds does the reverse.
                sd_ = 100 if break_ == "identical_seeds" else 100 + i
                arms.append(write_arm("K%02d_%s" % (K, dr), "control", K, dr, cv, draw_seed=sd_))
    man = {"started": "t0", "finished": "t1", "host": "h",
           "args": {"bank": bank, "query_kinds": "semantic_one_word",
                    "conditions": "natural_doublespeak", "n_examples": 4, "band": "6-14",
                    "k_list": ",".join(str(k) for k in ks),
                    "controls": ",".join(draws_l),
                    "control_ks": ",".join(str(k) for k in control_ks),
                    "exclude_prompt_ids": excl, "expect_n": len(keys), "split": "train",
                    "model": "meta-llama/Llama-3.1-8B-Instruct", "max_new": 8,
                    "min_option_mass": 0.05, "seed": 20260909, "tag_prefix": "ts116m_sowk"},
           "rung_roles": {str(k): v for k, v in
                          _ast_constant(RUNNER, "REL_END_ROLE").items()},
           "arms": arms}
    if break_ == "missing_arm":
        man["arms"] = [a for a in man["arms"] if a["arm_id"] != "K07_demo"]
    mp = os.path.join(base_dir, "MANIFEST.json")
    json.dump(man, open(mp, "w"))
    return mp, root, split_path


def _run(mp, root, split_path, **kw):
    return analyse(mp, root, RUNNER, split_path, n_boot=200, roles_source="ast", **kw)


def selftest():
    import io
    import shutil
    import tempfile
    ok = True

    def chk(name, cond):
        nonlocal ok
        print("  %-58s %s" % (name, "PASS" if cond else "FAIL"))
        ok = ok and bool(cond)

    def refuses(name, fn, needle=""):
        try:
            fn()
            chk(name, False)
        except Refusal as e:
            chk(name, needle.lower() in str(e).lower())
        except Exception as e:  # noqa: BLE001
            print("    (raised %r, not a Refusal)" % (e,))
            chk(name, False)

    # ---- arithmetic, pinned exactly
    chk("mean is exact", mean([1.0, 2.0, 3.0]) == 2.0 and mean([2.0]) == 2.0)
    chk("mean uses every element", mean([0.0, 0.0, 3.0]) == 1.0)
    chk("sd of 3 is exact", abs(sd([1.0, 2.0, 3.0]) - 1.0) < 1e-12 and math.isnan(sd([1.0])))
    chk("sd of identical draws is 0", sd([2.0, 2.0, 2.0]) == 0.0)
    chk("median_true is the true median", median_true([1.0, 2.0, 3.0, 4.0]) == 2.5)
    st = cluster_sign_test([-1.0] * 12)
    chk("sign test 12/12 == 2/2^12 with its floor",
        abs(st["p"] - 2.0 / 2 ** 12) < 1e-15 and abs(st["attainable_floor"] - 2.0 / 2 ** 12) < 1e-15)
    st5 = cluster_sign_test([-1.0] * 5)
    chk("floor at n=5 is 2/32 and cannot reach alpha",
        abs(st5["attainable_floor"] - 0.0625) < 1e-12 and not st5["can_reach_alpha"])
    chk("holm is exact on a known family",
        [round(x, 6) for x in holm([0.01, 0.02, 0.04])] == [0.03, 0.04, 0.04])
    chk("holm is monotone (step-down)", holm([0.5, 0.001])[0] >= holm([0.5, 0.001])[1])
    try:
        sys.path.insert(0, os.path.join(REPO, "scripts"))
        legacy = importlib.import_module("dcs_kladder_analysis").holm
        ps = [0.001, 0.03, 0.2, 0.9]
        chk("holm agrees with the legacy implementation",
            [round(x, 12) for x in holm(ps)] == [round(x, 12) for x in legacy(ps)])
    except Exception:                                   # numpy absent on the login node
        print("  %-58s SKIP (numpy absent)" % "holm vs legacy dcs_kladder_analysis.holm")

    # ---- shape classifier, on profiles whose answer is known by construction
    fam = list(range(1, 15))
    stepp = [(k, 0.0 if k < 10 else -3.0) for k in fam]
    rampp = [(k, -3.0 * k / 14) for k in fam]
    s1, s2 = classify_shape(stepp, fam), classify_shape(rampp, fam)
    chk("planted STEP is called STEP at K*=10", s1["shape"] == "STEP" and s1["K_star"] == 10)
    chk("planted RAMP is called RAMP", s2["shape"] == "RAMP")
    # the plateau drifts after the step, so the LARGEST rung is K=14 while the step is at K=10
    tilt = classify_shape([(k, 0.0 if k < 10 else -3.0 - 0.1 * (k - 10)) for k in fam], fam)
    chk("K* is the top of the largest RISE, not the largest rung",
        tilt["K_star"] == 10 and tilt["normaliser"]["at_K"] == 14 and tilt["shape"] == "STEP")
    s3 = classify_shape([(k, v) for k, v in stepp if k != 9], fam)
    chk("a hole in the ladder refuses a shape", s3["shape"].startswith("INCOMPLETE"))
    s4 = classify_shape([(k, (-3.0 if k >= 10 else 0.0) + (2.0 if k == 3 else 0.0)) for k in fam],
                        fam)
    chk("a mixed-sign profile is SIGN-INCOHERENT or NEITHER",
        s4["shape"].startswith("SIGN-INCOHERENT") or s4["shape"].startswith("NEITHER"))

    # ---- the pairing refusals, as units
    A = {"arm_id": "a", "rows": {("p1", "s1"): {"domain": "d1", PRIMARY: 1.0},
                                 ("p2", "s2"): {"domain": "d1", PRIMARY: 3.0}}}
    B = {"arm_id": "base", "rows": {("p1", "s1"): {"domain": "d1", PRIMARY: 0.0},
                                    ("p2", "s2"): {"domain": "d1", PRIMARY: 1.0}}}
    chk("paired delta is the mean of the per-prompt deltas",
        paired_domain_deltas(A, B, PRIMARY) == {"d1": 1.5})
    C = {"arm_id": "a", "rows": {k: v for k, v in list(A["rows"].items())[:1]}}
    refuses("refuses an unmatched key set", lambda: paired_domain_deltas(C, B, PRIMARY),
            "same (prompt_id, prompt_sha16) key set")
    D = {"arm_id": "a", "rows": {("p1", "s1"): {"domain": "OTHER", PRIMARY: 1.0},
                                 ("p2", "s2"): {"domain": "d1", PRIMARY: 3.0}}}
    refuses("refuses a key whose domain differs from the baseline's",
            lambda: paired_domain_deltas(D, B, PRIMARY), "in the baseline")
    refuses("refuses an empty binding", lambda: paired_domain_deltas(
        {"arm_id": "a", "rows": {}}, {"arm_id": "b", "rows": {}}, PRIMARY), "empty binding")

    tmp = tempfile.mkdtemp(prefix="kladder_selftest_")
    try:
        # ---- end to end on a planted STEP at K=10
        mp, root, sp = _synth(os.path.join(tmp, "step"))
        res = _run(mp, root, sp)
        chk("end-to-end STEP at K=10", res["shape"]["shape"] == "STEP"
            and res["shape"]["K_star"] == 10)
        chk("every rung >= 10 is significant after Holm",
            all(res["rungs"][k]["significant_holm"] for k in range(10, 15)))
        chk("every rung < 10 is null in magnitude",
            all(abs(res["rungs"][k]["mean_delta"]) < 0.2 for k in range(1, 10)))
        chk("each rung reports p beside its floor",
            all("p_floor" in res["rungs"][k] for k in range(1, 15)))
        chk("the rung label at K=10 names the CODEWORD",
            "CODEWORD" in res["rungs"][10]["rung_reaches"])
        chk("Holm family is the 14 DECLARED rungs",
            res["holm_families"]["rungs"]["m"] == 14)
        chk("the domain is the unit (n_domains == 12, not 24 rows)",
            res["rungs"][10]["n_domains"] == 12)
        chk("the delta is recovered at its planted size",
            abs(res["rungs"][10]["mean_delta"] + 3.0) < 0.05)
        chk("bootstrap CI brackets the planted effect",
            res["rungs"][10]["bootstrap"]["lo"] < -3.0 < res["rungs"][10]["bootstrap"]["hi"])
        b = res["controls"][10]
        chk("control band reports 3 draws and a non-zero BETWEEN-DRAW sd",
            b["n_draws"] == 3 and b["between_draw_sd"] > 1e-6)
        chk("control band reports the three seeds distinctly",
            len(set(b["draw_seeds"].values())) == 3)
        chk("demo-minus-control contrast is large and negative at K=10",
            b["contrast"]["mean_delta"] < -2.0 and "holm_p" in b["contrast"])
        chk("control contrasts are their OWN Holm family",
            res["holm_families"]["control_contrasts"]["m"] == 4)
        chk("rung geometry is verified, not assumed",
            "verified" in res["contracts"]["K10_demo"]["geometry"])
        chk("output is labelled EXPLORATORY (train)", "EXPLORATORY (train)" in res["label"])
        txt = render(res)
        chk("render prints p_floor beside p", "p_floor" in txt and "BETWEEN-DRAW sd" in txt)

        # ---- end to end on a planted RAMP
        mp2, root2, sp2 = _synth(os.path.join(tmp, "ramp"), ramp=True)
        chk("end-to-end RAMP", _run(mp2, root2, sp2)["shape"]["shape"] == "RAMP")

        # ---- a gated rung is CANNOT ANSWER and the ladder still reports the others
        mp3, root3, sp3 = _synth(os.path.join(tmp, "gate"), gate_fail_K=6)
        r3 = _run(mp3, root3, sp3)
        chk("a gated rung is CANNOT ANSWER, the ladder continues",
            r3["cannot_answer"] == [6] and r3["rungs"][10]["status"] == "OK"
            and r3["rungs"][6]["status"].startswith("CANNOT ANSWER"))
        chk("a CANNOT ANSWER rung enters Holm at p=1.0 and refuses a shape",
            r3["holm_families"]["rungs"]["entered_at_p1"] == ["K6"]
            and r3["shape"]["shape"].startswith("INCOMPLETE"))

        # ---- every declared refusal
        for tag, needle in (("missing_arm", "missing arm"), ("no_done", "without done.json"),
                            ("config_argv", "disagrees with the manifest argv"),
                            ("domain_mismatch", "domain set"),
                            ("identical_seeds", "distinct draw seeds"),
                            ("identical_draws", "byte-identical")):
            m, rt, s = _synth(os.path.join(tmp, tag), break_=tag)
            refuses("refuses on %s" % tag, lambda m=m, rt=rt, s=s: _run(m, rt, s), needle)

        # ---- a mid-flight manifest is refused outright
        m, rt, s = _synth(os.path.join(tmp, "midflight"))
        man = json.load(open(m))
        man.pop("finished")
        json.dump(man, open(m, "w"))
        refuses("refuses a MID-FLIGHT manifest", lambda: _run(m, rt, s), "mid-flight")

        # ---- a runner whose REL_END_ROLE drifted from the manifest's copy
        m, rt, s = _synth(os.path.join(tmp, "roles"))
        man = json.load(open(m))
        man["rung_roles"]["-10"] = "something else entirely"
        json.dump(man, open(m, "w"))
        refuses("refuses when the rung->token map has drifted",
                lambda: _run(m, rt, s), "disagrees with the map persisted")

        # ---- a producer/analyzer disagreement about the gate statistic
        m, rt, s = _synth(os.path.join(tmp, "gatestat"))
        p = glob.glob(os.path.join(rt, "ts116m_sowk_K10_demo_*", "summary.json"))[0]
        j = json.load(open(p))
        j["option_mass"]["semantic/semantic_one_word"]["median_true"] = 0.99
        json.dump(j, open(p, "w"))
        refuses("refuses when the two gate copies disagree", lambda: _run(m, rt, s),
                "disagrees with the producer")

        # ---- a row missing a critical field is not a zero
        m, rt, s = _synth(os.path.join(tmp, "missingfield"))
        p = glob.glob(os.path.join(rt, "ts116m_sowk_K10_demo_*", "results.jsonl"))[0]
        lines = open(p).read().strip().split("\n")
        j = json.loads(lines[0])
        j.pop("semantic_logodds")
        lines[0] = json.dumps(j)
        open(p, "w").write("\n".join(lines) + "\n")
        refuses("refuses a row missing the readout (missing != zero)",
                lambda: _run(m, rt, s), "missing is not zero")

        # ---- a rung whose cut is not the last K rows is not that rung
        m, rt, s = _synth(os.path.join(tmp, "geom"))
        p = glob.glob(os.path.join(rt, "ts116m_sowk_K10_demo_*", "results.jsonl"))[0]
        lines = open(p).read().strip().split("\n")
        j = json.loads(lines[0])
        j["surface_span_positions"] = list(range(100, 110))
        lines[0] = json.dumps(j)
        open(p, "w").write("\n".join(lines) + "\n")
        refuses("refuses a rung whose cut is not the last K query rows",
                lambda: _run(m, rt, s), "not the rung it is labelled as")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok else 1


def mutate():
    """Every mutation must be caught by the selftest. A verifier that survives its own sabotage is
    not a verifier."""
    g = globals()
    muts = []

    def add(name, target, repl):
        muts.append((name, target, repl))

    add("holm drops the (m - rank) factor", "holm", lambda ps: list(ps))
    add("sign test drops the two-sided factor", "cluster_sign_test",
        lambda v, alpha=ALPHA: dict(p=min(1.0, sum(1 for x in v if x < 0) / max(1, len(v))),
                                    attainable_floor=1 / 2 ** len(v), can_reach_alpha=True,
                                    k_informative=len(v),
                                    n_negative=sum(1 for x in v if x < 0), alpha=alpha,
                                    n_clusters=len(v), summary=lambda: ""))
    add("mean drops the last element", "mean",
        lambda v: (lambda l: sum(l[:-1]) / (len(l) - 1) if len(l) > 1 else float("nan"))(list(v)))
    add("sd of the control draws is reported as 0", "sd", lambda v: 0.0)
    add("K* is the largest rung instead of the largest rise", "classify_shape",
        lambda profile, fam: dict(rule="x", shape="STEP",
                                  K_star=max(profile, key=lambda t: abs(t[1]))[0],
                                  largest_single_rung_rise=dict(from_K=0, to_K=0, rise=0.0,
                                                                rise_raw=0.0),
                                  normaliser=dict(at_K=0), profile_normalised=[]))
    add("the option-mass gate always passes", "median_true", lambda v: 1.0)
    add("dirs without DONE.json are accepted", "find_arm_dir",
        lambda root, tag: sorted(glob.glob(os.path.join(root, tag + "_*")))[-1])
    add("the control-band distinctness check is skipped", "control_band",
        lambda demo, ctrls, baseline, alpha, n_boot, seed: dict(
            K=demo["k"], n_draws=len(ctrls), draw_seeds={}, per_draw={}, draw_means=[0.0],
            between_draw_sd=0.0, between_draw_range=(0.0, 0.0), band_mean=0.0,
            demo_mean=0.0, dose_matched=True, dose_keys_masked={}, demo_minus_each_draw={},
            contrast=summarise_deltas(paired_domain_deltas(demo, baseline, PRIMARY), alpha,
                                      n_boot, seed)))
    add("paired deltas ignore an unmatched key set", "paired_domain_deltas",
        lambda arm, baseline, field: (lambda ks: {d: mean(v) for d, v in
                                                  _by_dom(arm, baseline, field, ks).items()})(
            sorted(set(arm["rows"]) & set(baseline["rows"]))))
    add("the geometry check accepts any cut", "_rung_geometry",
        lambda rows, K, base: "not checked")
    add("config.json is not checked against the manifest argv", "config_vs_argv",
        lambda cfg_args, argv: [])

    red = 0
    for name, target, repl in muts:
        orig = g[target]
        g[target] = repl
        try:
            import io
            buf, old = io.StringIO(), sys.stdout
            sys.stdout = buf
            try:
                rc = selftest()
            finally:
                sys.stdout = old
            caught = (rc != 0)
        except Exception:                       # noqa: BLE001 -- a crash is also a catch
            caught = True
        finally:
            g[target] = orig
        red += caught
        print("  MUTATION %-56s %s" % (name, "RED (caught)" if caught else "GREEN -- NOT CAUGHT"))
    print("  %d/%d mutations caught" % (red, len(muts)))
    return 0 if red == len(muts) else 1


def _by_dom(arm, baseline, field, keys):
    per = defaultdict(list)
    for k in keys:
        per[arm["rows"][k]["domain"]].append(float(arm["rows"][k][field])
                                             - float(baseline["rows"][k][field]))
    return per


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default=MANIFEST)
    ap.add_argument("--root", default=SCORE_ROOT)
    ap.add_argument("--runner", default=RUNNER)
    ap.add_argument("--split-manifest", default=SPLIT_MANIFEST)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--alpha", type=float, default=ALPHA)
    ap.add_argument("--n-boot", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=20260909)
    ap.add_argument("--roles-source", default="auto", choices=["auto", "import", "ast"],
                    help="where REL_END_ROLE comes from: an executed import of the runner, or the "
                         "same literal read out of the same file without executing it. Never "
                         "retyped, and always cross-checked against the manifest's own copy.")
    ap.add_argument("--i-am-the-frozen-analyzer", action="store_true",
                    help="required to read anything but train; nothing in this phase passes it")
    ap.add_argument("--no-bank-hash", action="store_true",
                    help="skip hashing the 69MB bank; the artifact then records NOT HASHED")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--mutate", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        print("=== selftest ===")
        return selftest()
    if a.mutate:
        print("=== mutation harness ===")
        return mutate()

    res = analyse(a.manifest, a.root, a.runner, a.split_manifest, alpha=a.alpha, n_boot=a.n_boot,
                  seed=a.seed, roles_source=a.roles_source,
                  allow_non_train=a.i_am_the_frozen_analyzer, hash_bank=not a.no_bank_hash)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    print(render(res))
    print("\n[write] %s" % a.out)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Refusal as e:
        print("REFUSING: %s" % e, file=sys.stderr)
        raise SystemExit(2)
