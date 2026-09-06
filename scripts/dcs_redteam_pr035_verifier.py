#!/usr/bin/env python3
"""dcs_redteam_pr035_verifier.py — an ADVERSARIAL harness against `scripts/dcs_verify_pr035.py`.

WHY THIS FILE EXISTS
--------------------
`C-053` §28.9 records that **no `PR-035` result may be promoted until the verifier is rebuilt**,
*"since a verifier that reads the producer's derived fields proves nothing"*, and `C-049` §22.5
records the previous harness printing `MUTATION HARNESS OK` on a corruption it never detected.

`scripts/dcs_verify_pr035.py` was written to be that rebuilt verifier. **This file is the attack on
it.** It verifies nothing about `PR-035`; it verifies the VERIFIER, by corrupting the verifier's own
synthetic fixture world and asking whether it still prints `VERIFIED`.

⛔ NOTHING HERE TOUCHES THE REPO. Every corruption is applied to a throwaway copy of the target's
own fixture under a `TemporaryDirectory`. No repo file is read except the target module and no repo
file is written at all.

WHAT THE TARGET CLAIMS, AND WHAT ACTUALLY HOLDS (checked, not taken on trust)
----------------------------------------------------------------------------
  ✅ `C-049` §22.5 is NOT repeated. `cmd_mutate` binds each defect to ONE designated check id and
     accepts only `rep.status_of(designated) == "FAIL"`; a defect caught by some OTHER check, and a
     defect that was never applied at all, are both printed `*** NOT CAUGHT ***` and the harness
     exits 1. Pinned here by `_pin_designated_binding` with three synthetic outcomes.
  ✅ Its mutations are really applied: with the run directory or the producer JSON absent, `m4`/`m2`
     RAISE rather than silently no-op. And a vacuous mutation cannot produce a false pass, because
     the designated check would then still PASS. Pinned by `_pin_mutations_not_skippable`.
  ✅ It imports nothing from `scripts/dcs_bombness_specificity.py`. Pinned by `_pin_no_producer_import`.
  ✅ All ELEVEN of its declared mutations M1..M11 are caught by their designated checks — reproduced
     by running the target's own `--mutate` (9m14s, exit 0, every line CAUGHT).
  ✅ `C6_BLOCKING_NULL` is a genuine independent recomputation, and `C2b_REP_CACHE_BINDING` is
     calibrated for the real artifacts: on `bombspec_button_bomb_20260905_212802_2909400` the cache
     reproduces its own `results.jsonl` hnorm columns at q95 relative error **5.7e-07** against a
     1e-3 threshold, while M1's cache swap sits at **5.3e-01**. Both checks are real.

WHAT IT DOES NOT CATCH (this file's finding — seven corruptions, all `verified_fails = false`)
----------------------------------------------------------------------------------------------
  X1  FABRICATED HEADLINE   — `P2_primary.per_domain`, its permutation `p`, `null_mean`, `null_q95`
                              and the knife-vs-club `p` are rewritten to a self-consistent POSITIVE
                              (acc 0.7200, p = 0.0099) on a fixture whose cell-C rows are pure
                              noise. All 14 checks PASS. ⛔ The headline instrument is NEVER
                              recomputed: `C6` recomputes the n_examples=0 null and nothing else,
                              and `C8`/`C9` only check that the producer's numbers agree with each
                              other. This is §28.9's own sentence — *"a verifier that reads the
                              producer's derived fields proves nothing"* — surviving in the one
                              place that decides whether `PR-035` is promoted.
  X2  NO FOLD TABLE         — `P2_primary.picks` and `.n_domains` deleted. `C5_FOLD_DISCIPLINE`
                              (`if not node.get("picks"): continue`), `C7_INDEPENDENCE_UNIT`
                              (`if "n_domains" not in node: continue`) and `C4_LAYER_BAND` (which
                              only walks nodes that carry a `layer`) then have nothing to bite on
                              and the run VERIFIES with no fold discipline stated at all.
                              ⛔ The producer chooses which checks apply to it.
  X3  LAYER AS A STRING     — the same corruption as the target's own M8 (`layer = 20`, outside
                              L6-14) serialised as `"20"`. `C4` gates on
                              `_num(node.get("layer")) is not None`, so a non-numeric layer is
                              SKIPPED, not flagged. ⚠ The producer writes its JSON with
                              `json.dump(..., default=str)` (`dcs_bombness_specificity.py:725`),
                              which stringifies any numpy/torch integer. M8's detection is real but
                              type-fragile.
  X4  §28.2 ON THE PRIMARY  — the defect that `C-053` §28.2 called run-voiding for the null — picks
                              grid-searched on the population's OWN true labels — applied to the
                              HEADLINE. On pure-noise cell-C rows it lifts the primary from
                              acc 0.2953 / p = 0.99 to acc 0.3787 / **p = 0.0488**, i.e. it
                              manufactures §23.5 clause 3 out of nothing, and all 14 checks PASS.
                              `C5b_SELECTION_POPULATION` re-selects on cell B for the NULL ONLY;
                              the primary's picks are never re-selected.
  X5  CLAUSE 5 DELETED      — X1's POSITIVE, with `length_only_control` removed entirely.
                              `derive_verdict` treats `length_acc is None` as clause 5 PASSED, and
                              no check asserts the control exists. ⛔ §28.4's own lesson (*"a
                              missing control was reported as a control that FAILED"*) was fixed for
                              the knife-vs-club control and left standing for the length control.
  X6  PRODUCER-SIDE §28.3   — the `gun` class's primary rows joined to **button_club's** hidden
                              states (the 8-way `prompt_id` collision makes this lossless), the
                              blocking null joined correctly. Every file on disk stays self-
                              consistent, so `C2a`/`C2b` — which check FILES, never the join the
                              producer performed — pass, `C6` is untouched, and the run VERIFIES.
                              ⚠ A CYCLIC mis-join (bomb→knife→gun→bomb) is even worse: it is a
                              relabelling, so every reported number is BIT-IDENTICAL to the clean
                              run. No arithmetic check can ever see it.
  X7  CLAUSE 4 DELETED      — `P2_knife_vs_club_CONTROL_bomb_absent` and its permutation deleted.
                              §23.4(5)/§28.4 make it decision-critical and §23.3 asserts class-set
                              completeness for the `club` RUN — but nothing asserts the CONTROL was
                              computed. On a NEGATIVE the verdict never reaches clause 4, so the
                              deletion is invisible.
  (background) The target's own baseline fixture omits FIVE of §23.4's six required instruments —
  `P1`, the LOBO secondary, the cell-`F` comparator, the basket transfer and the 2-way
  bomb-vs-knife — and is declared VERIFIED. There is no instrument-presence check anywhere; X2, X5
  and X7 are three faces of that one hole.

USAGE
    python scripts/dcs_redteam_pr035_verifier.py --self-test    # exit 0: the attack rig is sound
    python scripts/dcs_redteam_pr035_verifier.py --mutate       # exit 0: every declared outcome seen
    python scripts/dcs_redteam_pr035_verifier.py --mutate --only X1,X4 --report out.json

EXIT SEMANTICS (read this before quoting a run)
    `--mutate` exits 0 when EVERY attack behaved EXACTLY as declared: each `SURVIVES` attack left
    ALL FOURTEEN of the target's checks PASSING — not merely its own — and each `CAUGHT` positive
    control failed its designated check. ⛔ Exit 0 is therefore a finding AGAINST the verifier, not
    a pass for it. Runtime is ~12 min for the full set (the target's `C6` recomputation dominates).

LIMITATIONS OF THIS FILE
    1. It attacks the target on the target's OWN synthetic fixture. It demonstrates MISSING CHECKS,
       not defects in any real `PR-035` number — the producer JSON does not exist yet, so the
       target currently exits 2 (CANNOT VERIFY) on the repo.
    2. Every survivor is a self-consistent producer output. It does not claim the real analyzer has
       any of these defects; it claims the verifier could not tell you if it did.
    3. It does not attack the preregistration, `C-053` §28.5's structural cell-C/cell-F confound, or
       external validity. A verifier cannot be blamed for those and this file does not try.
    4. X3 is a latent type-fragility: the frozen producer's `LAYERS_ALLOWED` is a tuple of python
       ints, so no live run emits a string layer today.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import dcs_verify_pr035 as V  # noqa: E402  the VERIFIER UNDER TEST

TARGET = os.path.join(_HERE, "dcs_verify_pr035.py")
PRODUCER = os.path.join(_HERE, "dcs_bombness_specificity.py")
ALL_CHECKS = sorted(V.CHECK_DOC)

#: permutations for the attack-side recomputations (X4, X6).  Small on purpose: these blocks are
#: rewritten as a self-consistent producer WOULD have written them, and `p_floor` is restated to
#: match, so `C9` still recomputes.  The target's own null recomputation is unaffected.
ATTACK_NPERM = 40


# --------------------------------------------------------------------------- #
# FIXTURE PLUMBING — one build per process, copied per attack.
# --------------------------------------------------------------------------- #
_CACHE = {}


def cached_fixture(work):
    """Build the TARGET's own fixture once (deterministic seed ladder) and cache it."""
    if "root" not in _CACHE:
        root = os.path.join(work, "_pristine")
        info = V.build_fixture(root, verbose=False)
        _CACHE["root"] = root
        _CACHE["info"] = info
    return _CACHE["root"]


def fresh(work, name):
    """A private copy of the pristine fixture, re-pointed at its new path (as the target does)."""
    root = os.path.join(work, f"atk_{name}")
    shutil.rmtree(root, ignore_errors=True)
    shutil.copytree(cached_fixture(work), root)
    V._rebase_fixture(root)
    V._BLOB_INFO.clear()
    return root


def tree_digest(root):
    h = hashlib.sha256()
    for base, _dirs, files in sorted(os.walk(root)):
        for f in sorted(files):
            p = os.path.join(base, f)
            h.update(os.path.relpath(p, root).encode())
            with open(p, "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()


def pools_of(root):
    return V._fix_pools(root)[1]


def joined_rows(root, pools, classes, population, join=None):
    """Rebuild the producer's own join: bank rows + the hidden states of `join[class]`'s run.

    `join` is the mis-pointing under test; `None` means each class reads its OWN run, which is what
    a correct producer does.
    """
    out, layers = [], None
    for c in classes:
        run_cc = (join or {}).get(c, c)
        d = V._run_dir(root, V.PRIMARY_CODEWORD, run_cc)
        rows = pools[(V.PRIMARY_CODEWORD, c, population)]
        layers, reps = V.load_reps_subset(d, {r["prompt_id"] for r in rows})
        for r in rows:
            out.append(dict(domain=r["domain"], bank_block=r.get("bank_block"), concept=c,
                            n_chars=len(r["full_prompt"]), vec=reps[r["prompt_id"]]))
    return layers, out


def put_block(res, key, obs):
    """Write a recomputed instrument back exactly as the producer writes one (§C9-consistent)."""
    node = res[key]
    node.update(per_domain=obs["per_domain"], mean_acc=obs["mean_acc"],
                n_above_chance=obs["n_above_chance"], n_domains=obs["n_domains"],
                picks=obs["picks"], train_fold_acc=obs["train_fold_acc"])
    node["mean_train_fold_acc"] = (float(np.mean(list(obs["train_fold_acc"].values())))
                                   if obs["train_fold_acc"] else None)
    node["fit_capable"] = bool(obs["train_fold_acc"] and
                               node["mean_train_fold_acc"] > obs["chance"])


def put_perm(res, key, pt, observed_mean):
    node = res[key]
    node.update(pt)
    node["p_floor"] = 1.0 / (1.0 + pt["n_perm"])
    node["observed_mean"] = observed_mean
    node["excess_over_null"] = observed_mean - pt["null_mean"]


def restate_verdict(res):
    """Print the verdict §23.5 implies for whatever numbers now stand.

    An adversary who left the verdict stale would be caught by `C8`, and rightly: `C8` works. This
    models the HONEST-ARITHMETIC producer, which is the only interesting adversary for a verifier.
    """
    prim, pp = res["P2_primary"], res["P2_primary_permutation"]
    kcp = res.get("P2_knife_vs_club_CONTROL_bomb_absent_permutation") or {}
    lenc = res.get("length_only_control") or {}
    obs_mean = float(np.mean([float(v) for v in prim["per_domain"].values()]))
    cat, why = V.derive_verdict(
        null_p=V.get_path(res, "null_n_examples_0.permutation.p_one_sided"),
        fit_capable=prim["fit_capable"], length_acc=lenc.get("mean_acc"),
        probe_null_q95=pp.get("null_q95"), primary_p=pp.get("p_one_sided"),
        above_null=obs_mean > pp["null_mean"], ctrl_p=kcp.get("p_one_sided"),
        primary_present=True)
    res["verdict"] = f"{cat} — {why}"
    res["verdict_inputs"] = dict(P2_perm_p=pp.get("p_one_sided"),
                                 knife_club_ctrl_p=kcp.get("p_one_sided"),
                                 above_null=bool(obs_mean > pp["null_mean"]),
                                 fit_capable=bool(prim["fit_capable"]),
                                 null_control_passed=True)
    return cat


def _lab(r):
    return r["concept"]


# --------------------------------------------------------------------------- #
# THE ATTACKS.  Each returns (detail, evidence-dict).
# --------------------------------------------------------------------------- #
def x1_fabricated_headline(root):
    """X1 — the headline instrument is never recomputed, so it can simply be written."""
    res = V._load_res(root)
    prim, pp = res["P2_primary"], res["P2_primary_permutation"]
    was = (prim["mean_acc"], pp["p_one_sided"], V.verdict_category(res["verdict"]))
    doms = sorted(prim["per_domain"])
    vals = [0.71, 0.74, 0.68, 0.75, 0.72, 0.72][:len(doms)]
    prim["per_domain"] = dict(zip(doms, vals))
    prim["mean_acc"] = float(np.mean(vals))
    prim["n_above_chance"] = int(sum(1 for v in vals if v > prim["chance"]))
    prim["train_fold_acc"] = {d: 0.95 for d in doms}
    prim["mean_train_fold_acc"] = 0.95
    prim["fit_capable"] = True
    pp.update(null_mean=0.3352, null_sd=0.052, null_q95=0.4211,
              p_one_sided=1.0 / (1.0 + pp["n_perm"]), p_floor=1.0 / (1.0 + pp["n_perm"]),
              observed_mean=prim["mean_acc"],
              excess_over_null=prim["mean_acc"] - 0.3352)
    res["P2_knife_vs_club_CONTROL_bomb_absent_permutation"]["p_one_sided"] = 0.0198
    if "length_only_control" in res:
        res["length_only_clause"] = dict(length_acc=res["length_only_control"]["mean_acc"],
                                         probe_null_q95=pp["null_q95"], passes=True)
    cat = restate_verdict(res)
    V._save_res(root, res)
    return (f"P2 primary rewritten: acc {was[0]:.4f} -> {prim['mean_acc']:.4f}, "
            f"p {was[1]:.4f} -> {pp['p_one_sided']:.4f}, verdict {was[2]} -> {cat}",
            {"what the fixture's cell-C rows actually contain": "iid noise, no class signal",
             "checks that recompute the primary": "NONE (C6 recomputes the null only)",
             "§28.9": "'a verifier that reads the producer's derived fields proves nothing'"})


def x2_no_fold_table(root):
    """X2 — the producer decides which of the target's checks apply to it."""
    res = V._load_res(root)
    n_picks = len(res["P2_primary"].get("picks") or {})
    res["P2_primary"].pop("picks", None)
    res["P2_primary"].pop("n_domains", None)
    V._save_res(root, res)
    return (f"P2_primary.picks ({n_picks} folds) and .n_domains deleted",
            {"C5_FOLD_DISCIPLINE": "skips a node with no 'picks' (`continue`)",
             "C7_INDEPENDENCE_UNIT": "skips a node with no 'n_domains' (`continue`)",
             "C4_LAYER_BAND": "walks only nodes that carry a 'layer'; the picks were its source"})


def x3_layer_as_string(root):
    """X3 — M8's own corruption, serialised as a string, evades M8's designated check."""
    res = V._load_res(root)
    d = sorted(res["P2_primary"]["picks"])[0]
    res["P2_primary"]["picks"][d]["layer"] = "20"
    V._save_res(root, res)
    return (f"P2_primary.picks[{d}].layer = '20' (string) — the target's own M8, retyped",
            {"C4 gate": "`_num(node.get('layer')) is not None` -> None for a str, node SKIPPED",
             "producer serialisation": "json.dump(..., default=str) at "
                                       "dcs_bombness_specificity.py:725 stringifies any "
                                       "numpy/torch integer"})


def x4_selection_on_own_labels(root):
    """X4 — `C-053` §28.2's run-voiding defect, moved from the null to the primary."""
    res = V._load_res(root)
    pools = pools_of(root)
    before = {d: (p["layer"], p["C"]) for d, p in res["P2_primary"]["picks"].items()}
    was = (res["P2_primary"]["mean_acc"], res["P2_primary_permutation"]["p_one_sided"])
    layers, C = joined_rows(root, pools, V.PRIMARY_CLASSES, "C")
    obs = V.loo_domain(C, layers, V.PRIMARY_CLASSES, _lab, selection_rows=C)
    pt = V.permutation_p(C, layers, V.PRIMARY_CLASSES, obs["picks"], ATTACK_NPERM, 99,
                         obs["mean_acc"])
    put_block(res, "P2_primary", obs)
    put_perm(res, "P2_primary_permutation", pt, obs["mean_acc"])
    _, KC = joined_rows(root, pools, ("knife", "club"), "C")
    kc = V.loo_domain(KC, layers, ("knife", "club"), _lab, selection_rows=KC)
    kcp = V.permutation_p(KC, layers, ("knife", "club"), kc["picks"], ATTACK_NPERM, 97,
                          kc["mean_acc"])
    put_block(res, "P2_knife_vs_club_CONTROL_bomb_absent", kc)
    put_perm(res, "P2_knife_vs_club_CONTROL_bomb_absent_permutation", kcp, kc["mean_acc"])
    cat = restate_verdict(res)
    V._save_res(root, res)
    after = {d: (p["layer"], p["C"]) for d, p in obs["picks"].items()}
    return (f"(layer, C) grid-searched on the PRIMARY's own test labels: acc "
            f"{was[0]:.4f} -> {obs['mean_acc']:.4f}, p {was[1]:.4f} -> {pt['p_one_sided']:.4f}, "
            f"verdict {cat}",
            {"picks, cell-B selected": before, "picks, self-selected": after,
             "§23.5 clause 3 (3-way p <= 0.05)": f"now {'MET' if pt['p_one_sided'] <= V.ALPHA else 'not met'} "
                                                 f"on rows that carry no class signal",
             "C5b_SELECTION_POPULATION": "re-selects on cell B for the NULL only"})


def x5_clause5_control_deleted(root):
    """X5 — a POSITIVE promoted with §23.5's mandatory length-only control simply absent."""
    detail1, _ = x1_fabricated_headline(root)
    res = V._load_res(root)
    had = res.get("length_only_control", {}).get("mean_acc")
    res.pop("length_only_control", None)
    res.pop("length_only_clause", None)
    cat = restate_verdict(res)
    V._save_res(root, res)
    return (f"{detail1}; then length_only_control (acc {had}) deleted — verdict still {cat}",
            {"derive_verdict": "`length_ok = (length_acc is None or ...)` -> a MISSING control "
                               "passes clause 5",
             "§28.4's lesson": "applied to the knife-vs-club control only"})


MISJOIN = dict(gun="club")


def x6_producer_side_misjoin(root):
    """X6 — §28.3's cross-bank join, committed in the producer's memory rather than on disk."""
    res = V._load_res(root)
    pools = pools_of(root)
    was = res["P2_primary"]["mean_acc"]
    layers, C = joined_rows(root, pools, V.PRIMARY_CLASSES, "C", join=MISJOIN)
    _, B = joined_rows(root, pools, V.PRIMARY_CLASSES, "B", join=MISJOIN)
    obs = V.loo_domain(C, layers, V.PRIMARY_CLASSES, _lab, selection_rows=B)
    pt = V.permutation_p(C, layers, V.PRIMARY_CLASSES, obs["picks"], ATTACK_NPERM, 98,
                         obs["mean_acc"])
    put_block(res, "P2_primary", obs)
    put_perm(res, "P2_primary_permutation", pt, obs["mean_acc"])
    cat = restate_verdict(res)
    V._save_res(root, res)
    return (f"the `gun` class's primary + selection rows joined to button_club's cache: "
            f"acc {was:.4f} -> {obs['mean_acc']:.4f}, p {pt['p_one_sided']:.4f}, verdict {cat}",
            {"why the join is lossless": "prompt_id collides 8-way (the target's own C2c proves "
                                         "it): zero missing rows, no VOID",
             "C2a / C2b": "check FILES against their own bank and their own results.jsonl — both "
                          "are still perfectly self-consistent",
             "C0": "compares provenance.run_dir to the globbed dir; the producer recorded the "
                   "RIGHT dir and opened the wrong cache",
             "C6": "recomputes the NULL, which this attack leaves correctly joined"})


def x7_clause4_control_deleted(root):
    """X7 — the decision-critical knife-vs-club control is simply not there."""
    res = V._load_res(root)
    had = (res.get("P2_knife_vs_club_CONTROL_bomb_absent") or {}).get("mean_acc")
    res.pop("P2_knife_vs_club_CONTROL_bomb_absent", None)
    res.pop("P2_knife_vs_club_CONTROL_bomb_absent_permutation", None)
    cat = restate_verdict(res)
    V._save_res(root, res)
    return (f"knife-vs-club control (acc {had}) and its permutation deleted — verdict still {cat}",
            {"§23.4(5) / §28.4": "the control that decides concept-identity vs remapping STRENGTH",
             "why it is invisible": "on a NEGATIVE, derive_verdict never reaches clause 4, and no "
                                    "check asserts that a declared instrument was computed",
             "§23.3": "asserts the club RUN exists, never that the CONTROL was computed"})


#: (id, expectation, one-line description, fn).  "SURVIVES" demands that ALL 14 checks still PASS.
ATTACKS = [
    ("X1", "SURVIVES", "the headline is fabricated; nothing recomputes it",
     x1_fabricated_headline),
    ("X2", "SURVIVES", "deleting the fold table deletes C5, C7 and C4's evidence",
     x2_no_fold_table),
    ("X3", "SURVIVES", "M8's out-of-band layer, retyped as a string, evades C4",
     x3_layer_as_string),
    ("X4", "SURVIVES", "§28.2 on the PRIMARY: p 0.99 -> 0.049 on pure noise",
     x4_selection_on_own_labels),
    ("X5", "SURVIVES", "a POSITIVE with §23.5's clause-5 control deleted",
     x5_clause5_control_deleted),
    ("X6", "SURVIVES", "§28.3 cross-bank join committed by the producer, not on disk",
     x6_producer_side_misjoin),
    ("X7", "SURVIVES", "§23.5's clause-4 control deleted",
     x7_clause4_control_deleted),
    # -- POSITIVE CONTROLS: the target's OWN mutations, replayed through THIS rig.  If these do not
    #    fire here, the survivors above prove nothing (they would just mean the rig disabled the
    #    verifier).
    ("P1", "CAUGHT:C6_BLOCKING_NULL", "positive control — the target's M9 (null misreported)",
     V.m9_wrong_null_accuracy),
    ("P2", "CAUGHT:C5_FOLD_DISCIPLINE", "positive control — the target's M5 (domain in own fold)",
     V.m5_domain_in_own_fold),
    ("P3", "CAUGHT:C2b_REP_CACHE_BINDING", "positive control — the target's M1 (cache swap)",
     V.m1_swap_rep_cache),
]


# --------------------------------------------------------------------------- #
# RUNNER
# --------------------------------------------------------------------------- #
def run_attack(work, name, fn, precondition_ok=True):
    """Corrupt a private copy of the fixture and ask the target for a verdict.

    The clean-copy precondition is established ONCE per run (`run_mutations` verifies a fresh copy
    before any attack); re-verifying it per attack would double a 14-check run that is dominated by
    the target's own null recomputation, and the copies are byte-identical by construction.
    """
    if not precondition_ok:
        return dict(name=name, precondition_ok=False, failed=[], passed=[],
                    detail="the CLEAN copy does not verify; any attack result would be meaningless",
                    evidence={}, bytes_changed=False, verdict=None, failure_text={})
    root = fresh(work, name)
    before = tree_digest(root)
    out = fn(root)
    detail, evidence = out if isinstance(out, tuple) else (str(out or fn.__doc__ or name), {})
    changed = tree_digest(root) != before
    rep = V.run_verify_on_fixture(root)
    try:
        verdict = V._load_res(root).get("verdict")
    except Exception:                                             # noqa: BLE001
        verdict = None
    res = dict(name=name, precondition_ok=True, failed=rep.failed(),
               passed=[c for c in ALL_CHECKS if rep.status_of(c) == "PASS"],
               detail=detail, evidence=evidence, bytes_changed=changed, verdict=verdict,
               failure_text={c: m for c, s, m in rep.rows if s == "FAIL"})
    shutil.rmtree(root, ignore_errors=True)
    return res


def judge(expectation, res):
    if not res["precondition_ok"]:
        return False, "the clean fixture failed before the corruption was applied"
    if not res["bytes_changed"]:
        return False, "the corruption changed NOTHING on disk — a vacuous attack is not a finding"
    if expectation == "SURVIVES":
        if res["failed"]:
            return False, f"expected blindness, but the verifier failed {res['failed']}"
        if len(res["passed"]) != len(ALL_CHECKS):
            return False, f"only {len(res['passed'])}/{len(ALL_CHECKS)} checks even ran"
        return True, f"the verifier printed VERIFIED — all {len(ALL_CHECKS)} checks PASS"
    want = expectation.split(":", 1)[1]
    if want in res["failed"]:
        return True, f"caught by its designated check {want}"
    return False, f"positive control did NOT fire on {want} (failed instead: {res['failed'] or 'NOTHING'})"


def run_mutations(work, verbose=True, only=None, report_path=None):
    print("RED-TEAM HARNESS vs. scripts/dcs_verify_pr035.py")
    print("⛔ A `SURVIVES` line means the verifier under test printed VERIFIED on corrupted")
    print("   artifacts.  A survivor is credited only when ALL 14 of its checks PASS — this file")
    print("   refuses to commit `C-049` §22.5's error in the other direction.\n")
    attacks = [a for a in ATTACKS if not only or a[0] in only]
    print("[rig] building the target's own fixture once (attacks run on private copies)...")
    cached_fixture(work)
    clean_root = fresh(work, "clean")
    base = V.run_verify_on_fixture(clean_root)
    shutil.rmtree(clean_root, ignore_errors=True)
    clean_ok = base.ok() and len(base.rows) == len(ALL_CHECKS)
    print(f"[rig] BASELINE (clean copy, no corruption): "
          f"{'VERIFIED, all 14 checks PASS' if clean_ok else 'FAILED ' + str(base.failed())}")
    if not clean_ok:
        print("⛔ the unmutated fixture does not verify — no attack result below would mean "
              "anything.")
        return 1
    print(f"[rig] {len(attacks)} attacks to run\n")

    results, ok = [], True
    for name, expectation, desc, fn in attacks:
        res = run_attack(work, name, fn, precondition_ok=clean_ok)
        good, why = judge(expectation, res)
        ok &= good
        res.update(expectation=expectation, description=desc, as_declared=good, verdict_why=why)
        results.append(res)
        head = ("⛔ NOT CAUGHT — VERIFIER SAYS VERIFIED"
                if expectation == "SURVIVES" and good
                else ("CAUGHT" if good else "⛔ NOT AS DECLARED"))
        print(f"  {name}  [{expectation.split(':')[0]:>8}]  {head}")
        print(f"        {desc}")
        print(f"        corruption : {res['detail']}")
        print(f"        producer verdict now : {res['verdict']!r}")
        print(f"        checks that FAILED   : {res['failed'] or 'NONE — all 14 passed'}")
        if verbose:
            for k, v in (res.get("evidence") or {}).items():
                print(f"          . {k}: {v}")
            for cid, msg in (res.get("failure_text") or {}).items():
                print(f"          ~ {cid}: {msg[:160]}")
        print()

    surv = [r for r in results if r["expectation"] == "SURVIVES" and r["as_declared"]]
    ctrl = [r for r in results if r["expectation"].startswith("CAUGHT")]
    n_surv_declared = sum(1 for a in attacks if a[1] == "SURVIVES")
    print("=== SUMMARY ===")
    for r in results:
        print(f"  {r['name']:<3} {r['expectation'].split(':')[0]:<9} "
              f"{'AS DECLARED' if r['as_declared'] else '⛔ NOT AS DECLARED':<18} "
              f"failed={r['failed'] or 'none'}")
    print(f"\nSURVIVING CORRUPTIONS: {len(surv)}/{n_surv_declared} "
          f"— {', '.join(r['name'] for r in surv) or 'none'}")
    print(f"POSITIVE CONTROLS FIRING: {sum(1 for r in ctrl if r['as_declared'])}/{len(ctrl)} "
          f"(if these do not fire, the survivors above prove nothing)")
    if report_path:
        with open(report_path, "w") as fh:
            json.dump(dict(target=TARGET, checks=ALL_CHECKS, results=results), fh, indent=1,
                      default=str)
        print(f"[write] {report_path}")
    print("\n" + ("⛔ VERIFIER BREACHED — every declared corruption behaved exactly as declared.\n"
                  "   dcs_verify_pr035.py is blind to X1..X7; §28.9's promotion gate is NOT yet\n"
                  "   satisfied by it, and in particular the P2 PRIMARY is never recomputed."
                  if ok else
                  "HARNESS INCONCLUSIVE — at least one attack did not behave as declared; nothing\n"
                  "   above may be quoted until the discrepancy is explained."))
    return 0 if ok else 1


# --------------------------------------------------------------------------- #
# SELF-TEST — the rig, and the target's claims that DO hold.
# --------------------------------------------------------------------------- #
class _StubReport(V.Report):
    def __init__(self, failing):
        super().__init__()
        for c in ALL_CHECKS:
            self.add(c, c not in failing, "stub")


def _pin_designated_binding():
    """`C-049` §22.5: is a defect credited when the WRONG check fires, or when NOTHING fires?

    Exercised against the target's real `cmd_mutate` with stubbed compute, so the acceptance rule
    itself is under test rather than a paraphrase of it.
    """
    seen = {}

    def fake_build(root, **kw):
        os.makedirs(root, exist_ok=True)
        with open(os.path.join(root, "producer.json"), "w") as fh:
            json.dump({}, fh)
        return dict(root=root, null_p=0.9)

    def fake_verify(root, **kw):
        return _StubReport(seen.get(os.path.basename(root), ()))

    saved = (V.build_fixture, V.run_verify_on_fixture, V.MUTATIONS, V._rebase_fixture)
    try:
        V.build_fixture, V.run_verify_on_fixture = fake_build, fake_verify
        V._rebase_fixture = lambda root: None
        seen["mut_RIGHT"] = ("C5_FOLD_DISCIPLINE",)
        seen["mut_WRONG"] = ("C1_POPULATION_IDENTITY",)      # some OTHER check fires
        seen["mut_NOOP"] = ()                                # nothing fires at all
        outs = {}
        for mid in ("RIGHT", "WRONG", "NOOP"):
            V.MUTATIONS = [(mid, f"synthetic {mid}", lambda root: None, "C5_FOLD_DISCIPLINE")]
            buf = io.StringIO()
            with tempfile.TemporaryDirectory() as w, contextlib.redirect_stdout(buf):
                rc = V.cmd_mutate(w)
            outs[mid] = (rc, buf.getvalue())
        # ⚠ match the per-mutation verdict `*** NOT CAUGHT ***`, never the bare phrase: the
        # target's own banner contains "counts as NOT CAUGHT (C-049 §22.5)".
        flag = "*** NOT CAUGHT ***"
        return (outs["RIGHT"][0] == 0 and flag not in outs["RIGHT"][1]
                and outs["WRONG"][0] == 1 and flag in outs["WRONG"][1]
                and outs["NOOP"][0] == 1 and flag in outs["NOOP"][1])
    finally:
        V.build_fixture, V.run_verify_on_fixture, V.MUTATIONS, V._rebase_fixture = saved


def _pin_mutations_not_skippable():
    """`C-049` §22.5: with the input absent, does a mutation silently do nothing?"""
    with tempfile.TemporaryDirectory() as root:
        os.makedirs(os.path.join(root, "runs"), exist_ok=True)
        for fn in (V.m4_wrong_bank_sha, V.m1_swap_rep_cache):
            try:
                fn(root)
                return False                      # returned normally == silently skipped
            except Exception:                     # noqa: BLE001  loud is correct
                pass
        try:
            V.m2_drop_exclusion(root)             # no producer.json
            return False
        except Exception:                         # noqa: BLE001
            return True


def _pin_no_producer_import():
    with open(TARGET) as fh:
        src = fh.read()
    body = src.split('"""', 2)[-1]
    return ("import dcs_bombness_specificity" not in body
            and "from dcs_bombness_specificity" not in body)


def _pin_c4_is_type_gated():
    """The unit fact behind X3 — no fixture needed."""
    node = {"layer": "20"}
    walked = [n for _p, n in V._walk({"picks": {"d": node}}) if isinstance(n, dict) and "layer" in n]
    return bool(walked) and V._num(node["layer"]) is None and V._num(20) == 20


def _pin_missing_length_control_passes_clause5():
    """The unit fact behind X5 — a MISSING clause-5 control is treated as a PASSED one."""
    base = dict(null_p=0.4, fit_capable=True, length_acc=0.34, probe_null_q95=0.40,
                primary_p=0.01, above_null=True, ctrl_p=0.01, primary_present=True)
    return (V.derive_verdict(**base)[0] == "POSITIVE"
            and V.derive_verdict(**{**base, "length_acc": None})[0] == "POSITIVE"
            and V.derive_verdict(**{**base, "length_acc": 0.9})[0] == "VOID")


def _pin_instrument_presence_unasserted():
    """§23.4 requires six instruments; the target's OWN baseline reports one of them.

    Read off the target's fixture producer JSON, so it is a fact about the artefact the target
    itself declares VERIFIED, not an opinion about the source.
    """
    root = cached_fixture(_WORK[0])
    res = V._load_res(root)
    required = ["P1_trainB_testC", "P2_leave_one_block_out", "P2_bomb_vs_benign_remap",
                "P2_basket_lexical_transfer", "P2_bomb_vs_knife_2way_gun_excluded"]
    missing = [k for k in required if k not in res]
    _PINS["§23.4 instruments absent from a VERIFIED baseline"] = missing
    return len(missing) == len(required)


def _pin_clean_fixture_verifies(work):
    root = fresh(work, "clean")
    rep = V.run_verify_on_fixture(root)
    ran = [c for c, _s, _m in rep.rows]
    shutil.rmtree(root, ignore_errors=True)
    return rep.ok() and sorted(ran) == ALL_CHECKS


def _pin_cheap_attacks_change_bytes(work):
    for name, expectation, _desc, fn in ATTACKS:
        if expectation != "SURVIVES" or name in ("X4", "X6"):   # the heavy two: covered in --mutate
            continue
        root = fresh(work, f"bytes_{name}")
        before = tree_digest(root)
        fn(root)
        after = tree_digest(root)
        shutil.rmtree(root, ignore_errors=True)
        if before == after:
            return False
    return True


_PINS = {}
_WORK = [None]


def run_self_test(work, verbose=True):
    _WORK[0] = work
    print("SELF-TEST — is this attack rig sound, and which of the target's claims hold?\n")
    pins = [
        ("the target's clean fixture verifies here, and all 14 checks run",
         lambda: _pin_clean_fixture_verifies(work)),
        ("✅ C-049 §22.5 NOT repeated: wrong-check and no-op mutations are both NOT CAUGHT, exit 1",
         _pin_designated_binding),
        ("✅ the target's mutations are really applied: a missing input RAISES, never no-ops",
         _pin_mutations_not_skippable),
        ("✅ the target imports nothing from dcs_bombness_specificity.py", _pin_no_producer_import),
        ("X3's premise: C4 skips a `layer` that is not a JSON number", _pin_c4_is_type_gated),
        ("X5's premise: derive_verdict treats a MISSING length control as clause 5 PASSED",
         _pin_missing_length_control_passes_clause5),
        ("X2/X5/X7's premise: §23.4's instruments are absent from the target's own VERIFIED baseline",
         _pin_instrument_presence_unasserted),
        ("every cheap SURVIVES attack actually changes bytes on disk (X4/X6 are asserted in --mutate)",
         lambda: _pin_cheap_attacks_change_bytes(work)),
    ]
    ok = True
    for label, fn in pins:
        try:
            good = bool(fn())
        except Exception as e:                                    # noqa: BLE001
            good, label = False, f"{label}  [raised {type(e).__name__}: {e}]"
        ok &= good
        print(f"  [{'PASS' if good else 'FAIL'}] {label}")
    for k, v in _PINS.items():
        print(f"  (note) {k}: {v}")

    print("\n  declared attacks:")
    for name, expectation, desc, _fn in ATTACKS:
        print(f"    {name}  [{expectation.split(':')[0]:>8}]  {desc}")
    print("\n" + ("SELF-TEST OK — the rig is sound; run --mutate for the findings."
                  if ok else "⛔ SELF-TEST FAILED — the findings may not be quoted."))
    return 0 if ok else 1


# --------------------------------------------------------------------------- #
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--self-test", action="store_true",
                    help="check the attack rig and reproduce the target's claims that hold")
    ap.add_argument("--mutate", action="store_true",
                    help="apply every declared corruption and require the declared outcome")
    ap.add_argument("--only", default=None, help="comma-separated attack ids, e.g. X1,X4")
    ap.add_argument("--quiet", action="store_true", help="suppress the per-attack evidence")
    ap.add_argument("--report", default=None, help="optional path for a machine-readable report")
    ap.add_argument("--work", default=None, help="scratch dir (default: a temp dir, removed after)")
    ap.add_argument("--limitations", action="store_true", help="print what this file cannot show")
    a = ap.parse_args(argv)

    if a.limitations:
        print(__doc__.split("LIMITATIONS OF THIS FILE")[-1])
        return 0
    if a.self_test == a.mutate:
        print("⛔ pass exactly one of --self-test / --mutate.")
        return 2
    work = a.work or tempfile.mkdtemp(prefix="pr035_redteam_")
    os.makedirs(work, exist_ok=True)
    only = {s.strip() for s in a.only.split(",")} if a.only else None
    try:
        if a.self_test:
            return run_self_test(work, verbose=not a.quiet)
        return run_mutations(work, verbose=not a.quiet, only=only, report_path=a.report)
    finally:
        _WORK[0] = None
        if not a.work:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
