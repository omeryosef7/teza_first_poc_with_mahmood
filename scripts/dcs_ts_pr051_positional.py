#!/usr/bin/env python3
"""`DCS-PR-051` -- the PAIRED POSITIONAL CONTRAST.

Question, from `configs/dcs_ts_pr051.json`:

    Is concept identity MORE decodable at the codeword's representation than at a downstream
    position that is token-identical across concepts?

This is the instrument that separates two hypotheses the `PR-048` primary CANNOT separate:

    H_bind   the codeword is represented as BOMB    -> identity is LOCALISED at the codeword
    H_gist   the prompt is about bombs              -> identity is available EVERYWHERE and the
                                                       codeword position is not special

Both make the same prediction for an absolute probe read at the codeword, because a gist
representation is available at the codeword too. Only a CONTRAST between the codeword and a
downstream position that is token-identical across concepts can tell them apart.

WHY THE PAIRING IS THE WHOLE POINT
----------------------------------
The absolute measurement in this phase is defeated by a nuisance floor: a bag of surface counts
read off the prompt text reaches 0.7065 accuracy on knife-vs-gun without looking at a single
hidden state (`_y3_result.THE_BAR`). That floor does NOT apply here. Both read sites see the SAME
PROMPT -- the same demonstration block, the same register, the same length, the same
TF-IDF-recoverable content -- so every surface confound is COMMON TO BOTH ARMS and DIFFERENCES OUT.
The preregistration says so in `primary.nuisance_floor`:

    "a paired difference has no surface floor: both sites see the SAME prompt, so any surface
     confound is common to both and differences it out"
    "this is precisely why the paired positional contrast is worth running -- the confound that
     defeats the absolute measurement cancels in the difference"

The nuisance floor for the PAIRED DIFFERENCE is therefore **0.0**, not 0.9217 and not 0.7065. This
is the single strongest methodological argument the phase has, and it is the reason this contrast
is worth the compute.

WHAT GOVERNS
------------
`configs/dcs_ts_pr051.json`, loaded through `scripts/dcs_ts_prereg.py`, which verifies FROZEN
status and every pinned `*_sha16` against the file on disk and REFUSES on a missing threshold.
There is not a single numeric gate literal in this file: alpha, n_perm, the chance level, the
nuisance floor, the layer and C grids, the split, the population filters, the exclusions, the
assumed-SD bracket and the demotion threshold are all fetched through `Prereg.require()`.

The conventions -- run discovery via `DONE.json`, bank-sha verification against the pin, the
explained/unexplained missing-row rule, `select_hparams` with its `SELECTION_TRACE`,
`sign_test_two_sided`, `group_permutation_p`, `fmt_p` -- are IMPORTED from the frozen probe
analyzer `scripts/dcs_ts_pr048_analysis.py`, not reimplemented. A difference between this script's
numbers and PR-048's is therefore a difference of design, not of arithmetic.

ORDER OF OPERATIONS, and W2 IS A BLOCKING GATE
----------------------------------------------
`pre_extraction_checklist` W2 is `blocking: true, done: false` on disk:

    "power for a PAIRED difference at n=23; neither PR-048 nor PR-049 power transfers"

Neither transfers, and the reason is arithmetic rather than rhetorical: PR-048's power is for a
3-way ABSOLUTE accuracy against chance 1/3, PR-049's for a 2-way absolute accuracy against 0.5.
The estimator here is a PAIRED DIFFERENCE against 0.0, whose sampling SD is the SD of the
within-domain difference -- a quantity that appears NOWHERE in the record and is not recoverable
from either of the other two. So W2 is computed here, first, and the gate is enforced:

  * `--stop-after-w2` runs the arithmetic and stops.
  * the arithmetic floors and the MDE bracket are ASSUMPTION-LABELLED; no assumed SD is presented
    as a measurement.
  * the preregistration's own `DEMOTION_CONTINGENCY` is parsed out of the config and enforced
    against a MEASURED paired SD taken on TRAIN+VALIDATION only, before the test split is read.
    If it fires, the contrast is DEMOTED TO EXPLORATORY and said so.

THINGS THIS FILE REFUSES TO DO, each from a specific past failure here
----------------------------------------------------------------------
  * analyse a run whose `bank_rows_sha16` disagrees with the pin           (bank binding)
  * tolerate a missing row whose domain is not a preregistered exclusion   (R-108)
  * select on TEST                                    -- measured FPR 0.4433 vs 0.0467 (A-039)
  * permute at row level                              -- measured FPR 0.2000 (A-039)
  * report a p without its attainable floor beside it                      (C-069)
  * describe a saturated selection surface as localisation                 (C-070)
  * analyse the two sites on different row sets       -- `primary.void`
  * report a statistic over a set it bound zero rows from                  (C-074)

USAGE
    python3 scripts/dcs_ts_pr051_positional.py --stop-after-w2
    python3 scripts/dcs_ts_pr051_positional.py --stop-after-selection
    python3 scripts/dcs_ts_pr051_positional.py --mutate
    python3 scripts/dcs_ts_pr051_positional.py            # the full contrast, reads TEST once
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import OrderedDict, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))

from dcs_ts_prereg import Prereg, PreregError, load, _walk_sha_fields  # noqa: E402

# CONVENTIONS IMPORTED FROM THE FROZEN ANALYZER, NOT REIMPLEMENTED.
from dcs_ts_pr048_analysis import (  # noqa: E402
    _find_run,
    bind_population,
    fmt_p,
    group_permutation_p,
    load_bank_rows,
    load_split,
    select_hparams,
    sign_test_two_sided,
)

# POWER ESTIMATORS IMPORTED FROM THE FROZEN POWER MODULE.
from dcs_ts_power import sign_mde, sign_power, t_mde, t_power  # noqa: E402


# ============================================================================ check ledger
class ZeroBinding(RuntimeError):
    """Raised whenever a computation would evaluate over an empty set."""


class Checks(object):
    """A check that bound zero rows is a FAIL, never a PASS.

    Four verifier harnesses in this repository have shipped checks that passed over empty sets.
    The ledger makes that impossible to do quietly: `n_bound` is a required argument and zero
    flips `ok` to False with the reason recorded.
    """

    def __init__(self):
        self.rows = OrderedDict()

    def add(self, name, claim, ok, n_bound, detail=""):
        if not n_bound:
            ok = False
            detail = "BOUND ZERO ROWS (vacuous check) -- " + str(detail)
        self.rows[name] = dict(claim=claim, ok=bool(ok), n_bound=int(n_bound or 0),
                               detail=str(detail))
        return ok

    @property
    def n_fail(self):
        return sum(0 if r["ok"] else 1 for r in self.rows.values())

    def report(self, fh=sys.stdout):
        for k, r in self.rows.items():
            fh.write("  [%s] %-16s n=%-7d %s\n"
                     % ("PASS" if r["ok"] else "FAIL", k, r["n_bound"], r["claim"]))
            if r["detail"]:
                fh.write("                              %s\n" % r["detail"])


# ============================================================================ prereg accessors
def control_position(pr: Prereg) -> str:
    """The control site's POSITION NAME, taken from the preregistration.

    `design.sites.control_site` reads

        "following (rel_end -9, ' actually', token id 3604) -- job 860925. CHANGED FROM `last` ..."

    so the position name is its first whitespace-delimited token. It is parsed rather than
    hardcoded because a control site that silently disagreed with the frozen file is precisely the
    failure mode this phase keeps hitting; if the parse yields something that is not a bare
    identifier, that is a refusal.
    """
    s = pr.require("design", "sites", "control_site")
    tok = str(s).split()[0].strip()
    if not re.fullmatch(r"[a-z_]+", tok):
        raise PreregError(
            "design.sites.control_site does not begin with a bare position name: %r. The "
            "analyzer will not guess which position it was told to read." % s)
    return tok


def demotion_thresholds(pr: Prereg) -> dict:
    """Parse `power.DEMOTION_CONTINGENCY` -- the prereg's own demotion rule -- into numbers.

    The rule is prose in the frozen file:

        "If the TRAIN-ONLY between-domain SD exceeds 0.188 (0.160 under Holm), conjunctive power
         falls below 0.8 and this contrast is DEMOTED TO EXPLORATORY."

    A threshold published in prose that no code path reads is exactly the B-020 failure. It is
    read here, and a config whose wording no longer yields two numbers is a REFUSAL rather than a
    silent skip.
    """
    s = pr.require("power", "DEMOTION_CONTINGENCY")
    m = re.search(r"exceeds\s+([0-9.]+)\s*\(([0-9.]+)\s+under Holm\)", s)
    if not m:
        raise PreregError("power.DEMOTION_CONTINGENCY no longer states a parseable SD threshold: "
                          "%r -- refusing to run behind a demotion rule I cannot evaluate." % s)
    return {"sd_max_alpha": float(m.group(1)), "sd_max_holm": float(m.group(2)), "text": s}


def declared_effect(pr: Prereg) -> dict:
    """The effect size the preregistration declared it cares about, from the power key name."""
    pw = pr.require("power")
    for k in pw:
        m = re.fullmatch(r"conjunctive_power_delta_([0-9.]+)_n(\d+)_sd_([0-9.]+)", k)
        if m:
            return {"delta": float(m.group(1)), "n": int(m.group(2)),
                    "sd": float(m.group(3)), "key": k, "value": pw[k]}
    raise PreregError("power declares no conjunctive_power_delta_* key -- the effect size this "
                      "design was sized for is not recorded, so W2 cannot be evaluated.")


def holm_family(pr: Prereg, pid: str = "DCS-PR-051") -> dict:
    """Which multiplicity family this contrast sits in, and how many members it has."""
    for fam in pr.require("multiplicity", "families"):
        for mem in fam["members"]:
            if pid in mem:
                return {"family": fam["name"], "n_members": len(fam["members"]),
                        "correction": fam["correction"], "members": fam["members"]}
    raise PreregError("%s is not declared in any multiplicity family" % pid)


# ============================================================================ W2 -- POWER
def w2_power(pr: Prereg, measured_sd: float | None = None,
             measured_label: str = "") -> dict:
    """W2. Power for a PAIRED difference at n = n_test_domains.

    EVERYTHING HERE IS LABELLED. There is no measured per-domain SD for a paired positional
    difference anywhere in this project's record -- the estimator has never been run. So the MDE
    is reported across the preregistration's OWN assumed-SD bracket
    (`power.mde_by_assumed_sd`), every row of which is an ASSUMPTION, and the one number that is
    not an assumption is the optional `measured_sd`, which is taken from TRAIN+VALIDATION only.
    """
    n = int(pr.require("primary", "n_test_domains"))
    alpha = float(pr.require("primary", "alpha"))
    n_perm = int(pr.require("primary", "n_perm"))
    chance = float(pr.require("primary", "chance"))
    if n < 2:
        raise ZeroBinding("W2 with n=%d test domains" % n)

    # ---- FLOORS ------------------------------------------------------------------------------
    # (a) the SIGN TEST floor: the smallest two-sided p an exact binomial sign test can return.
    sign_p_floor = sign_test_two_sided(n, n)[1]
    # (b) the exact PAIRED SIGN-FLIP permutation floor: with n domains there are 2^n sign
    #     assignments, so the exhaustive two-sided floor is 2/2^n. With B random draws the
    #     attainable floor is the MONTE CARLO floor 1/(B+1), which is far looser -- and it is the
    #     one that binds, because n_perm is 10^4 and 2^23 is 8.4x10^6.
    perm_exhaustive_floor = min(1.0, 2.0 * (2.0 ** -n))
    perm_mc_floor = 1.0 / (n_perm + 1.0)
    perm_floor = max(perm_exhaustive_floor, perm_mc_floor)

    # ---- CRITICAL VALUE OF THE BINDING ARM ---------------------------------------------------
    # `power._sign_test_binding` says the sign test is the binding arm because success is
    # CONJUNCTIVE. Re-derived here rather than quoted.
    from scipy import stats as _st
    k_crit, pi_crit = None, None
    for k in range(n + 1):
        if _st.binomtest(k, n, 0.5, alternative="two-sided").pvalue <= alpha:
            if k > n / 2.0:
                k_crit = k
                pi_crit = k / float(n)
                break
    if k_crit is None:
        raise ZeroBinding("no k in 0..%d rejects at alpha=%g -- the sign test cannot reject at "
                          "this n, which would make the conjunctive rule unsatisfiable" % (n, alpha))

    # ---- MDE ACROSS THE PREREGISTERED ASSUMED-SD BRACKET -------------------------------------
    # Two arms, because success is conjunctive and the design is only as powered as its weaker arm:
    #   * the permutation arm, whose power at these n is indistinguishable from the one-sample
    #     t-test on the paired differences (ASSUMPTION, stated);
    #   * the sign test arm, which needs pi = P(d_i > 0) >= pi_80. Converting pi to an accuracy
    #     delta requires a distributional assumption; a normal paired difference gives
    #     delta = sd * Phi^-1(pi_80). That is an ASSUMPTION and is labelled as one.
    pi_80 = sign_mde(n, 0.5, alpha, 0.80)
    z_pi80 = float(_st.norm.ppf(pi_80))
    bracket = pr.require("power", "mde_by_assumed_sd")
    rows = []
    for sd_s in sorted(bracket, key=float):
        sd = float(sd_s)
        rows.append(_mde_row(n, sd, alpha, z_pi80, "ASSUMED",
                             "prereg power.mde_by_assumed_sd (unpaired MDE there: %.4f)"
                             % float(bracket[sd_s])))

    # ---- THE MEASUREMENT-NOISE FLOOR ON THE PAIRED SD -----------------------------------------
    # Z2 of reports/DCS_TS_PR050_PR051_BLOCKERS.md: a per-domain accuracy measured on m rows is
    #     sd_observed(m)^2 = sd_between^2 + p(1-p)/m.
    # A PAIRED difference carries that binomial term TWICE, so even if the TRUE per-domain
    # difference were identical in every domain (sd_between = 0), the observed paired SD cannot go
    # below sqrt(2 p(1-p) / m). This is arithmetic, not an assumption about the model -- and it
    # bounds how small an MDE this design can ever have. m is derived from the preregistration.
    m = (int(pr.require("population", "rows_per_domain_per_concept"))
         * len(pr.require("population", "concepts"))
         * len(pr.require("population", "codewords")))
    noise = {}
    for p_assumed in (0.5, 0.7, 0.9):
        noise["p=%.1f" % p_assumed] = math.sqrt(2.0 * p_assumed * (1 - p_assumed) / m)
    sd_noise_worst = noise["p=0.5"]
    rows.append(_mde_row(n, sd_noise_worst, alpha, z_pi80, "DERIVED-FLOOR",
                         "measurement noise ALONE at m=%d rows per domain per site and p=0.5: "
                         "sqrt(2 p(1-p)/m). Conservative -- the two sites read the SAME rows, so "
                         "their binomial errors are positively correlated and the true paired "
                         "noise term is smaller. No sd below this is attainable with sd_between=0."
                         % m))
    if measured_sd is not None:
        rows.append(_mde_row(n, float(measured_sd), alpha, z_pi80, "MEASURED", measured_label))

    # ---- POWER AT THE DECLARED EFFECT SIZE ---------------------------------------------------
    eff = declared_effect(pr)
    pw_at_delta = []
    for r in rows:
        sd = r["sd"]
        p_perm = t_power(n, eff["delta"], sd, alpha)
        p_sign = sign_power(n, float(_st.norm.cdf(eff["delta"] / sd)), 0.5, alpha)
        pw_at_delta.append({"sd": sd, "kind": r["kind"], "power_perm_arm": p_perm,
                            "power_sign_arm": p_sign,
                            "power_conjunctive_upper_bound": min(p_perm, p_sign)})

    dem = demotion_thresholds(pr)
    verdict, why = _w2_verdict(pr, n, measured_sd, dem, eff, rows, pw_at_delta)

    return {
        "n_domains": n, "alpha": alpha, "n_perm": n_perm, "chance_for_the_difference": chance,
        "sign_test_floor": sign_p_floor,
        "permutation_floor_mc": perm_mc_floor,
        "permutation_floor_exhaustive_2n": perm_exhaustive_floor,
        "permutation_floor_binding": perm_floor,
        "sign_test_k_crit": k_crit, "sign_test_pi_crit": pi_crit,
        "pi_for_80pct_sign_power": pi_80,
        "mde_rows": rows,
        "rows_per_domain_per_site": m,
        "paired_sd_measurement_noise_floor": noise,
        "power_at_declared_delta": {"delta": eff["delta"], "prereg_key": eff["key"],
                                    "prereg_value": eff["value"], "rows": pw_at_delta},
        "demotion_rule": dem,
        "measured_sd": measured_sd, "measured_sd_label": measured_label,
        "verdict": verdict, "verdict_why": why,
        "_assumptions": [
            "The permutation arm's power is approximated by the one-sample t-test on the paired "
            "differences. A paired sign-flip permutation of the mean difference is asymptotically "
            "equivalent to that t-test and is conservative at small n; the approximation is an "
            "ASSUMPTION, not a measurement.",
            "Converting the sign test's pi to an accuracy delta assumes the per-domain paired "
            "difference is normally distributed. It is a bounded, discrete quantity (accuracies "
            "on 40 rows per domain, so differences live on a 1/40 lattice in [-1,1]), so this is "
            "an approximation and is labelled as one.",
            "EVERY SD in the bracket except a row marked MEASURED is an ASSUMPTION. There is no "
            "measured per-domain SD for a paired POSITIONAL difference anywhere in the record; "
            "prereg power._no_measured_2way_sd makes the same statement for the 2-way absolute "
            "estimator.",
        ],
    }


def _mde_row(n, sd, alpha, z_pi80, kind, note):
    d_perm = t_mde(n, sd, alpha, 0.80)
    d_sign = sd * z_pi80
    return {"sd": sd, "kind": kind, "note": note,
            "mde_perm_arm": float(d_perm), "mde_sign_arm": float(d_sign),
            "mde_conjunctive": float(max(d_perm, d_sign))}


def _w2_verdict(pr, n, measured_sd, dem, eff, rows, pw_at_delta):
    """The verdict is the preregistration's own rule, not a fresh judgement call."""
    if measured_sd is None:
        return ("CONDITIONAL -- pending the measured TRAIN/VALIDATION paired SD",
                "The arithmetic is complete but the demotion rule (%s) is stated about a MEASURED "
                "SD. Until that SD exists the contrast is neither cleared nor demoted; the MDE "
                "bracket below says what it would take."
                % dem["text"][:80])
    if measured_sd > dem["sd_max_alpha"]:
        return ("UNDERPOWERED -- DEMOTED TO EXPLORATORY by the preregistration's own "
                "DEMOTION_CONTINGENCY",
                "measured paired SD %.4f exceeds the declared ceiling %.4f, so conjunctive power "
                "at delta=%.2f falls below 0.8. The prereg says the honest outcome is to report "
                "the contrast as underpowered." % (measured_sd, dem["sd_max_alpha"], eff["delta"]))
    if measured_sd > dem["sd_max_holm"]:
        return ("ADEQUATE AT alpha, MARGINAL UNDER HOLM",
                "measured paired SD %.4f is under the alpha ceiling %.4f but over the Holm "
                "ceiling %.4f; conjunctive power at delta=%.2f clears 0.8 uncorrected and does "
                "not clear it under the Holm-corrected alpha."
                % (measured_sd, dem["sd_max_alpha"], dem["sd_max_holm"], eff["delta"]))
    return ("ADEQUATELY POWERED",
            "measured paired SD %.4f is below both declared ceilings (%.4f at alpha, %.4f under "
            "Holm), so conjunctive power at the declared delta=%.2f clears 0.8."
            % (measured_sd, dem["sd_max_alpha"], dem["sd_max_holm"], eff["delta"]))


# ============================================================================ data binding
def collect_site(pr: Prereg, spec: dict, assign: dict, reps_root: str, tag_prefix: str,
                 want_position: str, layer_grid: list) -> dict:
    """Load one read site. Returns metadata AND features; every verification input is retained
    so `verify()` can re-check it (and `--mutate` can perturb it) without a second 7 GB load."""
    import numpy as np
    import torch

    banks = pr.require("population", "banks")
    concepts = spec["concepts"]
    excluded = set(spec["excluded_domains"])

    per_bank = OrderedDict()
    X_by_layer = {L: [] for L in layer_grid}
    meta = []
    for bname, bpath in spec["banks"].items():
        cw, cc = bname.split("_", 1)
        if cc not in concepts:
            continue
        run = _find_run(reps_root, "%s_%s" % (tag_prefix, bname))
        summ = json.load(open(os.path.join(run, "summary.json")))
        cache = torch.load(os.path.join(run, "cache", "final_occurrence_reps.pt"),
                           map_location="cpu", weights_only=False)
        run_layers = list(cache["layers"])
        rows = load_bank_rows(os.path.join(REPO, bpath))
        # THE POPULATION, bound on the FIELD `cell` (A-039: `condition` binds ZERO rows).
        pop_pids = [pid for pid, r in rows.items()
                    if r["cell"] == spec["cell"] and r["query_kind"] == spec["query_kind"]
                    and r["n_examples"] == spec["n_examples"] and r["domain"] not in excluded]
        present = [pid for pid in pop_pids if pid in cache["reps"]]
        # Missing rows, and WHOSE DOMAIN they belong to -- checked in verify(), not here, so the
        # rule is mutation-testable.
        all_missing = [(pid, rows[pid]["domain"]) for pid, r in rows.items()
                       if r["cell"] == spec["cell"] and r["query_kind"] == spec["query_kind"]
                       and r["n_examples"] == spec["n_examples"] and pid not in cache["reps"]]
        per_bank[bname] = {
            "run": run, "summary": summ, "pinned_rows_sha16": banks[bname]["bank_rows_sha16"],
            "n_pop": len(pop_pids), "n_present": len(present),
            "missing": all_missing, "layers": run_layers,
        }
        for pid in sorted(present):
            r = rows[pid]
            t = cache["reps"][pid]
            t = t if hasattr(t, "shape") else torch.as_tensor(t)
            t = t.float()
            for L in layer_grid:
                X_by_layer[L].append(t[run_layers.index(L)].numpy())
            meta.append({"pid": pid, "bank": bname, "codeword": cw, "concept": cc,
                         "domain": r["domain"], "dsplit": assign[r["domain"]]})
        del cache
    if not meta:
        raise ZeroBinding("read site %r bound ZERO rows -- refusing to report a statistic over an "
                          "empty set (the C-074 shape)" % want_position)
    Xs = {L: np.stack(X_by_layer[L]) for L in layer_grid}
    # THE ROW KEY IS (bank, prompt_id), NOT prompt_id. `prompt_id` is unique only WITHIN a bank --
    # the four banks reuse the same 1130 ids -- so keying the row-set identity check on the id
    # alone would compare 1130 keys where 4520 rows exist and would be blind to a bank going
    # missing entirely. Same family as the matcher/scope bug class: the check's notion of a row
    # was not the row.
    return {"position": want_position, "tag_prefix": tag_prefix, "per_bank": per_bank,
            "meta": meta, "Xs": Xs, "pids": [(m["bank"], m["pid"]) for m in meta]}


# ============================================================================ verification
def verify(pr: Prereg, spec: dict, assign: dict, sites: dict, layer_grid, c_grid,
           mut: str | None = None) -> Checks:
    """Every gate, evaluated on already-loaded metadata so `--mutate` is cheap.

    Each check binds a COUNTED set and a zero bind is a FAIL.
    """
    ck = Checks()
    prim, ctrl = sites["primary"], sites["control"]

    # --- PRE-frozen ---------------------------------------------------------------------------
    shas = list(_walk_sha_fields(pr.obj))
    ck.add("PRE-frozen", "the preregistration is FROZEN and every pinned *_sha16 verifies "
           "against the file on disk", pr.obj.get("status") == "FROZEN", len(shas),
           "%d hashes pinned; loaded through dcs_ts_prereg.load(), which refuses on any mismatch"
           % len(shas))

    # --- W1/W3 checklist ----------------------------------------------------------------------
    cl = {i["id"]: i for i in pr.require("pre_extraction_checklist")}
    other_open = [k for k, v in cl.items() if k != "W2" and v["blocking"] and not v["done"]]
    ck.add("CHK-W1W3", "every BLOCKING pre-analysis item other than W2 (which this run computes) "
           "is marked done in the frozen config", not other_open, len(cl),
           "open besides W2: %s; W2 on disk is done=%s and is answered by this run's W2 section"
           % (other_open or "none", cl["W2"]["done"]))

    # --- BANK-sha, SITE-pos, ATTN, KO ---------------------------------------------------------
    n_runs = 0
    bad_sha, bad_pos, bad_attn, bad_ko, bad_fail = [], [], [], [], []
    want_attn = pr.require("model", "attn_impl")
    for site_key, site in (("primary", prim), ("control", ctrl)):
        want_pos = site["position"]
        if mut == "wrong_position" and site_key == "control":
            want_pos = prim["position"]          # demand the primary position at the control site
        for bname, b in site["per_bank"].items():
            n_runs += 1
            pinned = b["pinned_rows_sha16"]
            if mut == "wrong_sha" and site_key == "control" and not bad_sha:
                pinned = "0" * 16
            if b["summary"].get("bank_rows_sha16") != pinned:
                bad_sha.append("%s/%s: run %s vs pin %s"
                               % (site_key, bname, b["summary"].get("bank_rows_sha16"), pinned))
            got_pos = b["summary"].get("position")
            if mut == "wrong_attn" and site_key == "primary" and not bad_attn:
                got_attn = "sdpa"
            else:
                got_attn = b["summary"].get("attn_implementation")
            if got_pos != want_pos:
                bad_pos.append("%s/%s: %r != %r" % (site_key, bname, got_pos, want_pos))
            if got_attn != want_attn:
                bad_attn.append("%s/%s: %r != %r" % (site_key, bname, got_attn, want_attn))
            ko = b["summary"].get("knockout_applied")
            if mut == "knockout_on" and site_key == "primary" and not bad_ko:
                ko = True
            if ko is not False:
                bad_ko.append("%s/%s: knockout_applied=%r" % (site_key, bname, ko))
            if b["summary"].get("failures", {}).get("n_failed", -1) < 0:
                bad_fail.append("%s/%s" % (site_key, bname))
    ck.add("BANK-sha", "every run's bank_rows_sha16 equals the preregistration's pin",
           not bad_sha, n_runs, "; ".join(bad_sha[:3]))
    ck.add("SITE-pos", "each run was extracted at the position its site declares "
           "(primary %r, control %r)" % (prim["position"], ctrl["position"]),
           not bad_pos, n_runs, "; ".join(bad_pos[:3]))
    ck.add("ATTN", "every run used the preregistered attention implementation %r" % want_attn,
           not bad_attn, n_runs, "; ".join(bad_attn[:3]))
    ck.add("KO", "every run is the no-knockout baseline", not bad_ko, n_runs,
           "; ".join(bad_ko[:3]))
    ck.add("FAILREPORT", "every run reports failures.n_failed", not bad_fail, n_runs,
           "; ".join(bad_fail[:3]))

    # --- POP-bind -----------------------------------------------------------------------------
    n_prim, n_ctrl = len(prim["meta"]), len(ctrl["meta"])
    if mut == "empty_population":
        n_prim = n_ctrl = 0
    ck.add("POP-bind", "the population (cell=%s x %s x n_examples=%s, concepts %s, minus %d "
           "whole-population exclusions) binds rows at BOTH sites"
           % (spec["cell"], spec["query_kind"], spec["n_examples"], spec["concepts"],
              len(spec["excluded_domains"])),
           n_prim > 0 and n_ctrl > 0 and n_prim == n_ctrl, min(n_prim, n_ctrl),
           "primary %d rows, control %d rows" % (n_prim, n_ctrl))

    # --- MISS-explained -----------------------------------------------------------------------
    excluded = set(spec["excluded_domains"])
    if mut == "keep_excluded_domains":
        excluded = set()
    unexplained, n_checked, n_missing = [], 0, 0
    for site_key, site in (("primary", prim), ("control", ctrl)):
        for bname, b in site["per_bank"].items():
            n_checked += b["n_pop"] + len([1 for _, d in b["missing"] if d in excluded])
            for pid, dom in b["missing"]:
                n_missing += 1
                if dom not in excluded:
                    unexplained.append("%s/%s/%s (%s)" % (site_key, bname, pid, dom))
    ck.add("MISS-explained", "every population row absent from a cache belongs to a "
           "PREREGISTERED whole-population exclusion (R-108: a blanket n_failed==0 is the wrong "
           "guard; an UNEXPLAINED absence silently shrinks the population)",
           not unexplained, n_checked,
           "%d absent rows examined, %d unexplained%s"
           % (n_missing, len(unexplained), (": " + "; ".join(unexplained[:3])) if unexplained else ""))

    # --- ROWSET-identical ---------------------------------------------------------------------
    p_pids, c_pids = set(prim["pids"]), set(ctrl["pids"])
    if mut == "drop_control_rows":
        c_pids = set(sorted(c_pids)[5:])
    only_p, only_c = p_pids - c_pids, c_pids - p_pids
    ck.add("ROWSET-identical", "the two sites are analysed on IDENTICAL row sets, keyed on "
           "(bank, prompt_id) -- pairing a difference across two populations would make the "
           "statistic meaningless (primary.void)",
           not only_p and not only_c and len(prim["pids"]) == len(ctrl["pids"]),
           len(p_pids | c_pids),
           "|primary|=%d |control|=%d |intersection|=%d only-primary=%d only-control=%d"
           % (len(p_pids), len(c_pids), len(p_pids & c_pids), len(only_p), len(only_c)))
    # And the ORDER too: both sites iterate the same bank order and sort within bank, so the two
    # feature matrices are row-aligned. Asserted rather than assumed, because the pairing at the
    # DOMAIN level is only meaningful if each domain's accuracy at the two sites is computed over
    # the same rows.
    order_ok = list(prim["pids"]) == list(ctrl["pids"])
    if mut == "shuffle_control_order":
        order_ok = False
    ck.add("ROWORDER", "the two sites' row sequences are element-wise identical, so each domain's "
           "accuracy at the two sites is computed over the same rows", order_ok,
           len(prim["pids"]),
           "first mismatch at index %s" % next((i for i, (x, y) in
                                                enumerate(zip(prim["pids"], ctrl["pids"]))
                                                if x != y), None))

    # --- SPLIT --------------------------------------------------------------------------------
    a2 = dict(assign)
    if mut == "corrupt_split":
        te = sorted(d for d, s in a2.items() if s == "test")[:5]
        for d in te:
            a2[d] = "train"
            a2[d + "__ghost"] = "test"
    doms = sorted({m["domain"] for m in prim["meta"]})
    by = defaultdict(set)
    for d in doms:
        by[a2[d]].add(d)
    want = {"train": pr.require("split", "n_train"), "validation": pr.require("split", "n_validation"),
            "test": pr.require("split", "n_test")}
    n_analysed = pr.require("split", "n_domains_analysed")
    ok_counts = (len(doms) == n_analysed and len(by["validation"]) == want["validation"]
                 and len(by["test"]) == want["test"])
    ck.add("SPLIT-shape", "the ANALYSED split is %d domains = %d train / %d validation / %d test "
           "(3 whole-population exclusions all sit in TRAIN, so validation and test stay full)"
           % (n_analysed, n_analysed - want["validation"] - want["test"],
              want["validation"], want["test"]),
           ok_counts, len(doms),
           "observed %d domains: %d train / %d validation / %d test"
           % (len(doms), len(by["train"]), len(by["validation"]), len(by["test"])))
    overlap = by["train"] & by["test"]
    ck.add("LEAK-domain", "no domain appears in both train and test; DOMAIN is the independence "
           "unit", not overlap, len(by["train"]) + len(by["test"]),
           "overlap=%d %s" % (len(overlap), sorted(overlap)[:3]))

    # --- GRID ---------------------------------------------------------------------------------
    lg, cg = list(layer_grid), list(c_grid)
    if mut == "empty_grid":
        lg = []
    ck.add("GRID", "the selection grid is the preregistered %d layers x %d C values"
           % (len(layer_grid), len(c_grid)), bool(lg) and bool(cg), len(lg) * len(cg),
           "layers=%s C=%s" % (lg, cg))

    # --- BALANCE ------------------------------------------------------------------------------
    per_dom = defaultdict(lambda: defaultdict(int))
    for m in prim["meta"]:
        per_dom[m["domain"]][m["concept"]] += 1
    test_doms = sorted(by["test"] & set(per_dom))
    bad_bal = []
    for d in test_doms:
        counts = [per_dom[d][c] for c in spec["concepts"]]
        if mut == "unbalanced_domain" and d == (test_doms[0] if test_doms else None):
            counts[0] = 0
        if min(counts) == 0 or len(set(counts)) != 1:
            bad_bal.append("%s %s" % (d, counts))
    ck.add("BALANCE", "every TEST domain carries both concept arms in equal numbers, so a "
           "within-domain accuracy is a meaningful quantity", not bad_bal, len(test_doms),
           "%d test domains; offenders %s" % (len(test_doms), bad_bal[:3]))

    # --- GUARD-TEST ---------------------------------------------------------------------------
    # Selection reads VALIDATION only. Measured FPR: validation-selected 0.0467, test-selected
    # 0.4433 -- a 9.5x inflation. The guard is a check so it is mutation-testable.
    sel_splits = {"validation"}
    if mut == "select_on_test":
        sel_splits = {"validation", "test"}
    n_sel = sum(1 for m in prim["meta"] if m["dsplit"] in sel_splits)
    ck.add("GUARD-TEST", "the hyperparameter selection set contains ZERO test rows "
           "(validation-selected FPR 0.0467 vs test-selected 0.4433)",
           "test" not in sel_splits, n_sel,
           "selection reads splits %s (%d rows)" % (sorted(sel_splits), n_sel))

    # --- UNIT ---------------------------------------------------------------------------------
    unit = pr.require("primary", "independence_unit")
    if mut == "row_level_unit":
        unit = "row"
    ck.add("UNIT", "the independence unit is DOMAIN; permutation is at the domain level "
           "(row-level permutation measured FPR 0.2000)", unit == "domain", len(doms),
           "primary.independence_unit=%r" % unit)

    # --- FLOOR --------------------------------------------------------------------------------
    nf = pr.require("primary", "nuisance_floor")
    floor = nf["accuracy"]
    if mut == "surface_floor":
        floor = pr.require("_y3_result", "THE_BAR")   # a string; not a number -> must refuse
    ok_floor = isinstance(floor, (int, float)) and float(floor) == 0.0
    ck.add("FLOOR", "the nuisance floor for the PAIRED DIFFERENCE is 0.0 -- both sites see the "
           "SAME prompt, so every surface confound is common to both arms and differences out",
           ok_floor, 1, "primary.nuisance_floor.accuracy = %r" % (floor,))

    return ck


MUTATIONS = OrderedDict([
    ("wrong_sha", "a run's bank_rows_sha16 disagrees with the pin -> BANK-sha"),
    ("wrong_position", "the control run is demanded at the primary position -> SITE-pos"),
    ("wrong_attn", "a run used a different attention implementation -> ATTN"),
    ("knockout_on", "a run has a knockout applied -> KO"),
    ("empty_population", "the population binds zero rows -> POP-bind"),
    ("keep_excluded_domains", "the preregistered exclusions are not applied -> MISS-explained"),
    ("drop_control_rows", "the control site loses 5 rows -> ROWSET-identical"),
    ("corrupt_split", "five test domains are also train -> SPLIT-shape / LEAK-domain"),
    ("empty_grid", "the selection grid is empty -> GRID"),
    ("unbalanced_domain", "a test domain loses one concept arm -> BALANCE"),
    ("shuffle_control_order", "the control rows are no longer row-aligned -> ROWORDER"),
    ("select_on_test", "selection reads the test split -> GUARD-TEST"),
    ("row_level_unit", "the independence unit becomes the row -> UNIT"),
    ("surface_floor", "the 0.7065 SURFACE floor is applied to the paired difference -> FLOOR"),
])


# ============================================================================ the probe
def fit_site(pr, spec, site, layer_grid, c_grid, max_iter=2000):
    """Fit the SAME frozen probe design at one site. Selection on VALIDATION only."""
    import numpy as np
    import warnings
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    concepts = spec["concepts"]
    meta, Xs = site["meta"], site["Xs"]
    y = np.array([concepts.index(m["concept"]) for m in meta])
    dom = np.array([m["domain"] for m in meta])
    spl = np.array([m["dsplit"] for m in meta])
    tr, va, te = spl == "train", spl == "validation", spl == "test"
    for nm, msk in (("train", tr), ("validation", va), ("test", te)):
        if msk.sum() == 0:
            raise ZeroBinding("site %s: the %s split bound ZERO rows" % (site["position"], nm))
    if set(dom[tr]) & set(dom[te]):
        raise ZeroBinding("DOMAIN LEAKAGE at site %s" % site["position"])

    conv = {"n": 0, "where": []}

    def fit_eval(L, C, fit_mask, eval_mask, why=""):
        # standardisation fit on TRAIN only (classifier.standardisation, D1)
        sc = StandardScaler().fit(Xs[L][tr])
        clf = LogisticRegression(C=C, max_iter=max_iter)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always", ConvergenceWarning)
            clf.fit(sc.transform(Xs[L][fit_mask]), y[fit_mask])
            if any(issubclass(x.category, ConvergenceWarning) for x in w):
                conv["n"] += 1
                if len(conv["where"]) < 5:
                    conv["where"].append("%s L=%s C=%s" % (why, L, C))
        Xe = sc.transform(Xs[L][eval_mask])
        return clf.predict(Xe), clf.predict_proba(Xe), y[eval_mask], dom[eval_mask]

    def domain_mean_acc(pred, truth, doms):
        per = {}
        for d in sorted(set(doms)):
            m = doms == d
            per[d] = float((pred[m] == truth[m]).mean())
        if not per:
            raise ZeroBinding("domain-mean accuracy over ZERO domains")
        return float(np.mean(list(per.values()))), per

    # ---- SELECTION, VALIDATION ONLY ----------------------------------------------------------
    scores, order = {}, []
    for L in layer_grid:
        for C in c_grid:
            pred, _, truth, doms = fit_eval(L, C, tr, va, why="select")
            acc, _ = domain_mean_acc(pred, truth, doms)
            scores[(L, C)] = acc
            order.append((L, C))
    trace = select_hparams(scores, order)
    L_sel, C_sel = trace["chosen"]
    trace = dict(trace)
    trace["chosen"] = [L_sel, C_sel]
    trace["worst_acc"] = float(min(scores.values()))
    trace["surface_range"] = float(max(scores.values()) - min(scores.values()))
    trace["validation_surface"] = {"L%s_C%s" % (L, C): scores[(L, C)] for (L, C) in order}

    return {"trace": trace, "L": L_sel, "C": C_sel, "conv": conv,
            "_fit_eval": fit_eval, "_dma": domain_mean_acc,
            "_masks": (tr, va, te), "_y": y, "_dom": dom,
            "val_paired_source": None}


def eval_site_on(fitted, which):
    """Evaluate a fitted site on 'validation' or 'test' at ITS selected config."""
    import numpy as np
    from sklearn.metrics import roc_auc_score
    tr, va, te = fitted["_masks"]
    msk = {"validation": va, "test": te}[which]
    pred, proba, truth, doms = fitted["_fit_eval"](fitted["L"], fitted["C"], tr, msk,
                                                   why="eval:" + which)
    acc, per = fitted["_dma"](pred, truth, doms)
    try:
        auroc = float(roc_auc_score(truth, proba[:, 1]))
    except Exception:
        auroc = float("nan")
    bal = float(np.mean([ (pred[truth == c] == c).mean() for c in sorted(set(truth)) ]))
    return {"domain_mean_accuracy": acc, "per_domain": per, "row_accuracy": float((pred == truth).mean()),
            "balanced_accuracy": bal, "auroc": auroc, "n_rows": int(msk.sum()),
            "n_domains": len(per)}


# ============================================================================ the contrast
def paired_contrast(pr, per_dom_primary, per_dom_control, seed):
    """The statistic: paired per-domain difference, primary minus control.

    The null is a PAIRED DOMAIN-LEVEL PERMUTATION OF THE SITE LABEL. Exchanging the site label
    within a domain negates that domain's difference, so the null is the set of 2^n sign
    assignments -- sampled at n_perm draws. This is exchangeable under H0 by construction and
    permutes at the DOMAIN level, never the row level.
    """
    import numpy as np
    doms = sorted(set(per_dom_primary) & set(per_dom_control))
    if not doms:
        raise ZeroBinding("the paired contrast bound ZERO domains")
    if set(per_dom_primary) != set(per_dom_control):
        raise ZeroBinding("the two sites produced per-domain accuracies over DIFFERENT domain "
                          "sets -- the pairing is undefined (primary.void)")
    d = np.array([per_dom_primary[x] - per_dom_control[x] for x in doms])
    n = len(d)
    obs = float(d.mean())
    sd = float(d.std(ddof=1))
    se = sd / math.sqrt(n)
    from scipy import stats as _st
    tcrit = float(_st.t.isf(pr.require("primary", "alpha") / 2.0, n - 1))
    ci = (obs - tcrit * se, obs + tcrit * se)

    # bootstrap over DOMAINS, the independence unit
    rng = np.random.default_rng(seed)
    boot = np.array([d[rng.integers(0, n, n)].mean() for _ in range(10000)])
    bci = (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))

    # sign test: ties are dropped (a zero difference carries no directional information) and BOTH
    # the tie-dropped and the naive n=23 versions are reported, because which one is used changes
    # the attainable floor.
    k_pos = int((d > 0).sum())
    k_neg = int((d < 0).sum())
    n_tie = int((d == 0).sum())
    n_eff = k_pos + k_neg
    sp_all, sfl_all = sign_test_two_sided(max(k_pos, k_neg), n)
    if n_eff:
        sp_eff, sfl_eff = sign_test_two_sided(max(k_pos, k_neg), n_eff)
    else:
        sp_eff, sfl_eff = 1.0, 1.0

    # paired sign-flip permutation
    n_perm = int(pr.require("primary", "n_perm"))
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n_perm, n))
    nulls = (signs * d).mean(axis=1)
    p_two, fl_two, ne_two = group_permutation_p(abs(obs), list(np.abs(nulls)))
    p_one, fl_one, ne_one = group_permutation_p(obs, list(nulls))

    return {
        "n_domains": n, "domains": doms,
        "per_domain_difference": {x: float(v) for x, v in zip(doms, d)},
        "mean_difference": obs, "sd_difference": sd, "se": se,
        "ci95_t": [float(ci[0]), float(ci[1])],
        "ci95_domain_bootstrap": [bci[0], bci[1]],
        "sign_test": {"k_positive": k_pos, "k_negative": k_neg, "n_tied": n_tie,
                      "n_all": n, "p_all": sp_all, "floor_all": sfl_all,
                      "formatted_all": fmt_p(sp_all, sfl_all),
                      "n_eff": n_eff, "p_tiedropped": sp_eff, "floor_tiedropped": sfl_eff,
                      "formatted_tiedropped": fmt_p(sp_eff, sfl_eff)},
        "permutation": {"n_perm": n_perm,
                        "p_two_sided": p_two, "floor": fl_two, "n_exceed": ne_two,
                        "formatted_two_sided": fmt_p(p_two, fl_two, ne_two),
                        "p_one_sided": p_one, "n_exceed_one": ne_one,
                        "formatted_one_sided": fmt_p(p_one, fl_one, ne_one),
                        "null_mean": float(nulls.mean()), "null_sd": float(nulls.std(ddof=1))},
    }


def interpret(pr, contrast, sig, powered) -> tuple[str, str]:
    """The three readings are FIXED IN THE PREREGISTRATION. This function selects among them; it
    does not invent a fourth, and it does not soften any of them."""
    fixed = pr.require("design", "_interpretation_fixed_before_the_numbers_exist")
    obs = contrast["mean_difference"]
    if sig and obs > 0:
        key = "codeword >> control"
    elif sig and obs < 0:
        key = "control >> codeword"
    else:
        key = "codeword ~= control"
    return key, fixed[key]


# ============================================================================ main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", default="configs/dcs_ts_pr051.json")
    ap.add_argument("--reps", default="outputs/boombness/extract_boombness")
    ap.add_argument("--primary-tag", default="ts116m_full")
    ap.add_argument("--control-tag", default="ts116m_following")
    ap.add_argument("--stop-after-w2", action="store_true")
    ap.add_argument("--stop-after-selection", action="store_true",
                    help="everything up to and including selection and the W2 demotion check; "
                         "TEST is never read")
    ap.add_argument("--mutate", action="store_true")
    a = ap.parse_args()

    # (1) ENFORCE the preregistration. for_extraction=False, and the reason is stated rather than
    # assumed: W2 is the one BLOCKING checklist item still open on disk, and W2 is what THIS
    # SCRIPT computes -- so loading with for_extraction=True would be circular. The extraction it
    # gates has already run (W1 done, job 860925). CHK-W1W3 below re-checks that every OTHER
    # blocking item is closed, and the frozen config is not edited by this run.
    pr = load(a.prereg, for_extraction=False)
    ext_errs = None
    try:
        load(a.prereg, for_extraction=True)
    except PreregError as e:
        ext_errs = str(e)

    spec = bind_population(pr)
    assign = load_split(pr)
    layer_grid = pr.require("read_site", "layer_grid")
    c_grid = pr.require("read_site", "C_grid")
    prim_pos = pr.require("read_site", "position")
    ctrl_pos = control_position(pr)
    fam = holm_family(pr)
    seed = int(pr.require("split", "seed"))

    out = {"prereg": a.prereg, "primary_position": prim_pos, "control_position": ctrl_pos,
           "population": spec, "multiplicity": fam,
           "prereg_for_extraction_says": ext_errs}

    print("=" * 92)
    print("DCS-PR-051  PAIRED POSITIONAL CONTRAST   %s  vs  %s" % (prim_pos, ctrl_pos))
    print("=" * 92)
    print("  population: cell=%s x %s x n_examples=%s  concepts=%s"
          % (spec["cell"], spec["query_kind"], spec["n_examples"], spec["concepts"]))
    print("  exclusions: %s" % spec["excluded_domains"])
    print("  multiplicity: %s family, %d members, %s"
          % (fam["family"], fam["n_members"], fam["correction"]))
    if ext_errs:
        print("  NOTE load(for_extraction=True) still refuses, and correctly:")
        for ln in ext_errs.splitlines()[1:]:
            print("       " + ln.strip())
        print("       W2 is what this run computes. The frozen config is NOT edited.")

    # ---------------------------------------------------------------- W2, the blocking gate ---
    print("\n" + "-" * 92)
    print("W2 -- POWER FOR A PAIRED DIFFERENCE (blocking gate; run BEFORE anything else)")
    print("-" * 92)
    w2a = w2_power(pr, measured_sd=None)
    out["W2_arithmetic"] = w2a
    print("  n = %d test domains, alpha = %g, n_perm = %d, chance for the DIFFERENCE = %g"
          % (w2a["n_domains"], w2a["alpha"], w2a["n_perm"], w2a["chance_for_the_difference"]))
    print("  sign-test attainable floor (two-sided, n=%d)      : %.6e"
          % (w2a["n_domains"], w2a["sign_test_floor"]))
    print("  permutation floor, Monte-Carlo at n_perm=%d     : %.6e"
          % (w2a["n_perm"], w2a["permutation_floor_mc"]))
    print("  permutation floor, exhaustive over 2^%d sign flips: %.6e"
          % (w2a["n_domains"], w2a["permutation_floor_exhaustive_2n"]))
    print("  -> the BINDING floor is %.6e (the Monte-Carlo one; the design could resolve "
          "%.0fx deeper\n     if the sign flips were enumerated instead of sampled)"
          % (w2a["permutation_floor_binding"],
             w2a["permutation_floor_mc"] / w2a["permutation_floor_exhaustive_2n"]))
    print("  sign test rejects at alpha=%g only from k >= %d of %d domains (pi >= %.4f)"
          % (w2a["alpha"], w2a["sign_test_k_crit"], w2a["n_domains"], w2a["sign_test_pi_crit"]))
    print("  pi needed for 80%% sign-test power: %.4f" % w2a["pi_for_80pct_sign_power"])
    print("\n  MDE in ACCURACY UNITS for the paired difference, 80%% power, alpha=%g:" % w2a["alpha"])
    print("    %-8s %-9s %-11s %-11s %-11s" % ("sd", "kind", "perm arm", "sign arm", "CONJUNCTIVE"))
    for r in w2a["mde_rows"]:
        print("    %-8.4f %-9s %-11.4f %-11.4f %-11.4f"
              % (r["sd"], r["kind"], r["mde_perm_arm"], r["mde_sign_arm"], r["mde_conjunctive"]))
    print("  Every sd marked ASSUMED is an ASSUMPTION taken from prereg power.mde_by_assumed_sd."
          "\n  There is no measured paired positional SD anywhere in this project's record.")
    print("  DERIVED, not assumed: with m=%d rows per domain per site the paired SD cannot fall "
          "below\n  sqrt(2 p(1-p)/m) = %s even if the true per-domain difference were constant."
          % (w2a["rows_per_domain_per_site"],
             ", ".join("%.4f at %s" % (v, k) for k, v in
                       w2a["paired_sd_measurement_noise_floor"].items())))
    print("  W2 (arithmetic only) verdict: %s" % w2a["verdict"])
    print("    %s" % w2a["verdict_why"])
    print("  demotion rule parsed from the prereg: SD > %.4f -> EXPLORATORY (%.4f under Holm)"
          % (w2a["demotion_rule"]["sd_max_alpha"], w2a["demotion_rule"]["sd_max_holm"]))
    if a.stop_after_w2:
        print("\n--stop-after-w2: no representation was loaded. Dry run complete.")
        _dump(out)
        return 0

    # ---------------------------------------------------------------- load both sites ---------
    reps_root = a.reps if os.path.isabs(a.reps) else os.path.join(REPO, a.reps)
    print("\n" + "-" * 92)
    print("BINDING BOTH READ SITES")
    print("-" * 92)
    sites = {}
    for key, tag, pos in (("primary", a.primary_tag, prim_pos),
                          ("control", a.control_tag, ctrl_pos)):
        print("  loading %-8s tag=%-18s position=%s ..." % (key, tag, pos))
        sites[key] = collect_site(pr, spec, assign, reps_root, tag, pos, layer_grid)
        print("      %d rows over %d domains from %d banks"
              % (len(sites[key]["meta"]), len({m["domain"] for m in sites[key]["meta"]}),
                 len(sites[key]["per_bank"])))

    ck = verify(pr, spec, assign, sites, layer_grid, c_grid, mut=None)
    print("\n  CHECK LEDGER")
    ck.report()
    out["checks"] = {k: v for k, v in ck.rows.items()}
    if ck.n_fail:
        print("\n  %d CHECK(S) FAILED -- refusing to report a contrast behind a failed gate."
              % ck.n_fail)
        _dump(out)
        return 1
    out["n_rows_per_site"] = len(sites["primary"]["meta"])
    out["row_sets_identical"] = True

    if a.mutate:
        print("\n" + "-" * 92)
        print("MUTATION HARNESS -- every check must be demonstrably reachable")
        print("-" * 92)
        n_red = 0
        for name, why in MUTATIONS.items():
            try:
                mck = verify(pr, spec, assign, sites, layer_grid, c_grid, mut=name)
                red = mck.n_fail > 0
                which = [k for k, v in mck.rows.items() if not v["ok"]]
            except (ZeroBinding, PreregError, ValueError, KeyError, TypeError) as e:
                red, which = True, ["RAISED %s" % type(e).__name__]
            n_red += red
            print("  %-5s %-24s %-58s -> %s"
                  % ("RED" if red else "GREEN", name, why, ",".join(which) or "NOTHING WENT RED"))
        print("  [mutate] %d/%d mutations turned a check RED" % (n_red, len(MUTATIONS)))
        out["mutations"] = {"n": len(MUTATIONS), "n_red": n_red, "names": list(MUTATIONS)}
        if n_red != len(MUTATIONS):
            print("  AN UNREACHABLE CHECK IS NOT A GUARD.", file=sys.stderr)
            _dump(out)
            return 1

    # ---------------------------------------------------------------- fit + select ------------
    print("\n" + "-" * 92)
    print("FITTING THE SAME FROZEN PROBE DESIGN INDEPENDENTLY AT EACH SITE")
    print("  selection reads VALIDATION only, separately per site; TEST is untouched")
    print("-" * 92)
    fitted, valres = {}, {}
    for key in ("primary", "control"):
        f = fit_site(pr, spec, sites[key], layer_grid, c_grid)
        fitted[key] = f
        t = f["trace"]
        print("  %-8s (%s): layer=%s C=%s  best_val_acc=%.4f  worst=%.4f  range=%.4f  "
              "n_tied=%d/%d  inert=%s  saturated=%s"
              % (key, sites[key]["position"], t["chosen"][0], t["chosen"][1], t["best_acc"],
                 t["worst_acc"], t["surface_range"], t["n_tied_at_best"], t["n_grid"],
                 t["inert"], t["saturated"]))
        if t["_warning"]:
            print("      !! %s" % t["_warning"])
        valres[key] = eval_site_on(f, "validation")
        print("      validation domain-mean acc at the selected config = %.4f"
              % valres[key]["domain_mean_accuracy"])
    out["SELECTION_TRACE"] = {k: fitted[k]["trace"] for k in fitted}
    out["validation_at_selected"] = valres

    # ---- the MEASURED paired SD, on VALIDATION -- still not the test split -------------------
    import numpy as np
    vdoms = sorted(set(valres["primary"]["per_domain"]) & set(valres["control"]["per_domain"]))
    if not vdoms:
        raise ZeroBinding("the validation paired SD bound ZERO domains")
    vd = np.array([valres["primary"]["per_domain"][d] - valres["control"]["per_domain"][d]
                   for d in vdoms])
    measured_sd = float(vd.std(ddof=1))
    w2 = w2_power(pr, measured_sd=measured_sd,
                  measured_label="MEASURED on the %d VALIDATION domains at each site's own "
                                 "selected config; TEST not read" % len(vdoms))
    out["W2"] = w2
    out["validation_paired_difference"] = {"mean": float(vd.mean()), "sd": measured_sd,
                                           "n_domains": len(vdoms)}
    print("\n  W2, MEASURED ARM (validation only, %d domains):" % len(vdoms))
    print("    validation paired difference mean = %+.4f  sd = %.4f" % (vd.mean(), measured_sd))
    print("    demotion ceilings: %.4f at alpha, %.4f under Holm"
          % (w2["demotion_rule"]["sd_max_alpha"], w2["demotion_rule"]["sd_max_holm"]))
    mrow = [r for r in w2["mde_rows"] if r["kind"] == "MEASURED"][0]
    print("    MDE at the measured sd: perm arm %.4f, sign arm %.4f, CONJUNCTIVE %.4f"
          % (mrow["mde_perm_arm"], mrow["mde_sign_arm"], mrow["mde_conjunctive"]))
    prow = [r for r in w2["power_at_declared_delta"]["rows"] if r["kind"] == "MEASURED"][0]
    print("    power at the declared delta=%.2f: perm arm %.3f, sign arm %.3f, conjunctive "
          "upper bound %.3f" % (w2["power_at_declared_delta"]["delta"], prow["power_perm_arm"],
                                prow["power_sign_arm"], prow["power_conjunctive_upper_bound"]))
    print("    W2 VERDICT: %s" % w2["verdict"])
    print("      %s" % w2["verdict_why"])

    if a.stop_after_selection:
        print("\n--stop-after-selection: TEST WAS NOT READ. Dry run complete.")
        _dump(out)
        return 0

    if w2["verdict"].startswith("UNDERPOWERED"):
        print("\n  W2 IS A BLOCKING GATE AND IT FAILED. The preregistration says the honest "
              "outcome is\n  to report the contrast as UNDERPOWERED rather than to run it and "
              "quote a number.\n  TEST WAS NOT READ.")
        out["outcome"] = "UNDERPOWERED -- test not read"
        _dump(out)
        return 0

    # ---------------------------------------------------------------- TEST, read once ---------
    print("\n" + "-" * 92)
    print("TEST -- read ONCE, at each site's own selected config")
    print("-" * 92)
    tst = {k: eval_site_on(fitted[k], "test") for k in fitted}
    out["test_absolute"] = tst
    for k in ("primary", "control"):
        print("  %-8s (%s): domain-mean acc %.4f  row acc %.4f  balanced %.4f  AUROC %.4f  "
              "(%d rows / %d domains)"
              % (k, sites[k]["position"], tst[k]["domain_mean_accuracy"], tst[k]["row_accuracy"],
                 tst[k]["balanced_accuracy"], tst[k]["auroc"], tst[k]["n_rows"], tst[k]["n_domains"]))

    con = paired_contrast(pr, tst["primary"]["per_domain"], tst["control"]["per_domain"], seed)
    out["contrast"] = con
    alpha = pr.require("primary", "alpha")
    nf = pr.require("primary", "nuisance_floor")
    floor_acc = float(nf["accuracy"])
    clears = con["mean_difference"] > floor_acc

    sig_perm = con["permutation"]["p_two_sided"] < alpha
    sig_sign = con["sign_test"]["p_tiedropped"] < alpha
    sig = sig_perm and sig_sign
    key, reading = interpret(pr, con, sig, True)

    print("\n  PAIRED DIFFERENCE (%s minus %s), over %d TEST domains"
          % (prim_pos, ctrl_pos, con["n_domains"]))
    print("    mean = %+.4f   sd = %.4f   se = %.4f" % (con["mean_difference"],
                                                        con["sd_difference"], con["se"]))
    print("    95%% CI (t)         [%+.4f, %+.4f]" % tuple(con["ci95_t"]))
    print("    95%% CI (bootstrap) [%+.4f, %+.4f]" % tuple(con["ci95_domain_bootstrap"]))
    print("    NUISANCE FLOOR for the difference = %.4f (%s)" % (floor_acc, nf["source"]))
    print("    clears_floor = %s" % clears)
    s = con["sign_test"]
    print("    sign test  k+=%d k-=%d ties=%d   tie-dropped n=%d: %s"
          % (s["k_positive"], s["k_negative"], s["n_tied"], s["n_eff"], s["formatted_tiedropped"]))
    print("               naive over all %d domains: %s" % (s["n_all"], s["formatted_all"]))
    p = con["permutation"]
    print("    permutation (paired sign-flip of the SITE label, %d draws, DOMAIN level)"
          % p["n_perm"])
    print("      two-sided %s" % p["formatted_two_sided"])
    print("      one-sided %s" % p["formatted_one_sided"])
    print("    Holm: PR-051 sits in the %s family (%d members), %s. The most conservative "
          "first\n          step is alpha/%d = %.5f."
          % (fam["family"], fam["n_members"], fam["correction"], fam["n_members"],
             alpha / fam["n_members"]))
    out["significance"] = {"alpha": alpha, "sig_permutation": bool(sig_perm),
                           "sig_sign_test": bool(sig_sign), "conjunctive": bool(sig),
                           "holm_first_step_alpha": alpha / fam["n_members"],
                           "sig_under_holm_first_step": bool(
                               con["permutation"]["p_two_sided"] < alpha / fam["n_members"]
                               and con["sign_test"]["p_tiedropped"] < alpha / fam["n_members"]),
                           "clears_nuisance_floor": bool(clears)}
    # THE SAME TRICHOTOMY, EVALUATED TWICE -- uncorrected, and under the preregistration's OWN
    # multiplicity rule. multiplicity declares PR-051 a member of the SECONDARY family with Holm
    # across its 8 members, so the corrected reading is not an afterthought: it is what the frozen
    # file asks for. Reporting only the uncorrected branch when the two disagree would be choosing
    # the answer after seeing it.
    sig_holm = out["significance"]["sig_under_holm_first_step"]
    key_h, reading_h = interpret(pr, con, sig_holm, True)
    out["interpretation"] = {"uncorrected": {"key": key, "reading": reading},
                             "holm_first_step": {"alpha": alpha / fam["n_members"],
                                                 "key": key_h, "reading": reading_h},
                             "branches_agree": key == key_h,
                             "fixed_before_the_numbers_existed": True}
    print("\n  INTERPRETATION (fixed in the preregistration before any number existed):")
    print("    UNCORRECTED (alpha=%g):        %s" % (alpha, key.upper()))
    print("      %s" % reading)
    print("    HOLM FIRST STEP (alpha=%.5f): %s" % (alpha / fam["n_members"], key_h.upper()))
    print("      %s" % reading_h)
    if key != key_h:
        print("    THE TWO BRANCHES DISAGREE. The preregistration declares the Holm correction, so "
              "the\n    corrected branch is the confirmatory one and the uncorrected branch is "
              "reported beside\n    it rather than instead of it.")
    # DESCRIPTIVE, so the size of the effect is not hidden behind its p-value.
    hp = 1.0 - tst["control"]["domain_mean_accuracy"]
    print("    SIZE: the control site already reaches %.4f, so the codeword site's advantage of "
          "%+.4f\n          closes %.1f%% of the %.4f headroom that remained. Identity is "
          "decodable at %.4f at a\n          position that is token-identical across concepts "
          "and carries no concept token."
          % (tst["control"]["domain_mean_accuracy"], con["mean_difference"],
             100.0 * con["mean_difference"] / hp, hp, tst["control"]["domain_mean_accuracy"]))
    out["effect_size_context"] = {
        "control_absolute": tst["control"]["domain_mean_accuracy"],
        "primary_absolute": tst["primary"]["domain_mean_accuracy"],
        "control_headroom": hp,
        "fraction_of_headroom_closed": con["mean_difference"] / hp}
    _dump(out)
    return 0


def _dump(out):
    print("\n===JSON===")
    print(json.dumps(out, indent=2, default=str))
    print("===ENDJSON===")


if __name__ == "__main__":
    raise SystemExit(main())
