#!/usr/bin/env python3
"""One way to filter slots, and it cannot be called without naming the scope.

WHY THIS FILE EXISTS. Four separate defects in this phase are the same defect:

    C-CONT-072  a ratio built from two different slot scopes, neither stated
    C-CONT-083  the quantitative dissociation, significant on all-slots and null on the declared
                primary; the entry never said which it used
    C-CONT-088  the linking test, +0.176 all-slots and -0.074 on the primary, scope unstated
    C-CONT-089  the de-refusal analysis, computed on all-slots two entries after I declared
                slot0 primary and all-slots "secondary, and only if labelled"

None was a subtle statistical trap. In each case the filter was an inline `if 'slot0' in ...` (or its
absence), the choice was never written down, and the number went into the record naked. The fix is
not more care; it is removing the option to be silent.

USE
    from dcs_cont_scope import Scope
    sc = Scope.PRIMARY            # or Scope.ALL_SLOTS -- there is no default
    rows = [r for r in rows if sc.keeps(r["family_id"])]
    ...
    result["scope"] = sc.tag      # a dict that names the scope, its basis, and its declaration

Every function here REQUIRES the scope to be passed. There is no default argument, because a default
is how three of the four defects above happened -- the filter was simply absent.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class _Scope:
    name: str
    slot: str | None
    why: str

    def keeps(self, family_id: str) -> bool:
        """True if this row is inside the scope. `family_id` is the bank's, e.g.
        'domain|split|slot0|n4|none|consistent|near|plain|behavioral'."""
        if self.slot is None:
            return True
        return self.slot in str(family_id).split("|")

    @property
    def tag(self) -> Dict[str, str]:
        """Drop this into any result artifact. A number without it is a number nobody can check."""
        return {"scope": self.name, "slot_filter": self.slot or "(none -- all slots)",
                "why": self.why}


class Scope:
    #: The dose ladder's declared primary (CONT-ENTRY 094), inherited by DR-074 and CONT-ENTRY 120.
    #: slot0 is the ONLY slot present at dose 0, so it is the only balanced dose contrast.
    PRIMARY = _Scope("slot0 PRIMARY", "slot0",
                     "declared in CONT-ENTRY 094; the only slot present at dose 0, so the only "
                     "balanced dose contrast")
    #: Legitimate for rare-event analyses where slot0 leaves too few events -- but it must be SAID.
    #: CONT-ENTRY 122/123 used this without saying so and A15's quantities had to be relabelled.
    ALL_SLOTS = _Scope("all slots SECONDARY", None,
                       "secondary per CONT-ENTRY 120; defensible for rare-event analyses "
                       "(refusals) where the primary leaves too few events, but only if labelled")

    @staticmethod
    def require(scope) -> "_Scope":
        """Call at the top of any analysis. Raises rather than guessing."""
        if not isinstance(scope, _Scope):
            raise TypeError(
                "scope must be Scope.PRIMARY or Scope.ALL_SLOTS, explicitly. There is no default: "
                "four defects in this phase (C-CONT-072/083/088/089) were an unstated slot scope.")
        return scope

    @staticmethod
    def for_dose_contrast(slots_a, slots_b, scope=None) -> "_Scope":
        """The admissible scope for a contrast between two arms with different slot sets.

        A dose contrast may only use slots present in BOTH arms. Anything else compares
        different slot compositions and calls the difference a dose effect -- which is
        exactly what inflated basket's ASR dose slope 4.2x (CONT-ENTRY 117, C-CONT-091).

        REVIEW-7 asked why nobody had proposed a slot-STRATIFIED estimator. This is the
        answer, and it is a fact about the bank rather than a preference: on ts116m every
        dose pair on BOTH codewords shares exactly one slot, slot0. So the stratified
        estimator collapses to the slot0 primary and recovers no extra information.
        ALL_SLOTS is therefore not merely secondary for dose work -- it is inadmissible.
        """
        shared = set(slots_a) & set(slots_b)
        if not shared:
            raise ValueError("the two arms share NO slot; no dose contrast is defined")
        if scope is Scope.ALL_SLOTS:
            raise ValueError(
                "ALL_SLOTS is inadmissible for a dose contrast: the arms share only %s, so "
                "'all slots' would compare %d slot(s) against %d. See C-CONT-091."
                % (sorted(shared), len(set(slots_a)), len(set(slots_b))))
        if shared == {"slot0"}:
            return Scope.PRIMARY
        raise NotImplementedError(
            "arms share %s, more than slot0 alone. A genuine stratified estimator is now "
            "possible and must be written deliberately -- do not silently fall back to the "
            "primary and call it stratified." % sorted(shared))


# ---------------------------------------------------------------------------
# POPULATION -- the second half of the same lesson (C-CONT-094)
# ---------------------------------------------------------------------------
# Scope was not enough. On 2026-09-12 I published seven numbers computed with the
# 23 TEST domains IN (CONT-ENTRY 133), and a FROZEN config asserting
# "does_not_read_TEST": true whose own inputs spanned all 116 domains. Neither was
# caught by the scope guard, because population is a different axis.
#
# So population is now required in the same way and by the same call. A number
# needs BOTH to be interpretable, and this phase has now been bitten by each.


@dataclass(frozen=True)
class _Population:
    name: str
    keeps_test: bool
    why: str

    def keeps(self, domain: str, assign: Dict[str, str]) -> bool:
        return self.keeps_test or assign.get(domain) != "test"

    @property
    def tag(self) -> Dict[str, str]:
        return {"population": self.name, "why": self.why}


class Population:
    TRAIN_VAL = _Population(
        "train+val", False,
        "the default for all exploratory and most confirmatory work; leaves TEST unspent")
    ALL_INCLUDING_TEST = _Population(
        "ALL (TEST INCLUDED)", True,
        "only for a preregistered single TEST read with its own written authorisation. "
        "Passing this SPENDS TEST -- it is never the convenient choice")

    @staticmethod
    def require(population) -> "_Population":
        if not isinstance(population, _Population):
            raise TypeError(
                "population must be Population.TRAIN_VAL or Population.ALL_INCLUDING_TEST, "
                "explicitly. There is no default: C-CONT-094 was seven published numbers and a "
                "frozen config's inputs, all silently computed with TEST in.")
        return population


def domain_bootstrap(domains, stat, n_boot, seed, max_drop=0.05):
    """Domain-clustered percentile bootstrap that will not hide its own failures.

    C-CONT-098 (REVIEW-9/D8): a ratio bootstrap elsewhere in this phase skipped every
    resample whose denominator was zero and reported the percentiles of what was left --
    on one arm that silently DISCARDED 36% of draws, which is no longer the interval it
    claims to be. Here dropped draws are counted, returned, and raise past `max_drop`.
    """
    import random as _r
    g = _r.Random(seed)
    dl = list(domains); vals = []; dropped = 0
    for _ in range(n_boot):
        s = [dl[g.randrange(len(dl))] for _ in dl]
        v = stat(s)
        if v is None or v != v:      # None or NaN
            dropped += 1
        else:
            vals.append(v)
    if dropped > max_drop * n_boot:
        raise ValueError(
            "bootstrap discarded %d of %d draws (%.1f%%, limit %.0f%%) -- the surviving "
            "percentiles are not the interval they appear to be. Use a different estimator."
            % (dropped, n_boot, 100.0 * dropped / n_boot, 100 * max_drop))
    vals.sort()
    return {"point": stat(dl), "lo": vals[int(.025 * len(vals))],
            "hi": vals[int(.975 * len(vals))], "n_boot": n_boot,
            "draws_dropped": dropped, "seed": seed}


def filter_rows(rows, scope, population, assign, family_key="family_id",
                domain_key="domain"):
    """The only sanctioned way to narrow rows for an analysis in this phase.

    Requires BOTH axes explicitly and returns (kept, provenance). Raises on an
    empty result rather than letting a downstream mean be computed over nothing --
    four defects in this phase (C-CONT-036/056/066/069) were silent empty or
    mis-keyed selections that produced plausible numbers.
    """
    sc = Scope.require(scope)
    po = Population.require(population)
    kept = [r for r in rows
            if sc.keeps(r.get(family_key, "")) and po.keeps(r.get(domain_key), assign)]
    if not kept:
        raise ValueError("filter_rows kept 0 of %d rows (scope=%s, population=%s). "
                         "Refusing to return an empty set silently."
                         % (len(rows), sc.name, po.name))
    # C-CONT-095: both tags carry a "why" key, so {**sc.tag, **po.tag} silently DROPPED the
    # scope's rationale and relabelled it with the population's. Namespaced instead -- a
    # provenance dict that quietly loses half its provenance is worse than none.
    # C-CONT-097 (REVIEW-9/D7): the LABEL "train+val" was attached to a train-ONLY corpus --
    # all 67 domains are `train` and the 23 validation domains are absent entirely, so the
    # filter is a no-op here and the name overstates what was included. A label describes the
    # FILTER; only a census describes the DATA. Both are recorded now, and the census is the
    # one an artifact should be read against.
    doms = {r.get(domain_key) for r in kept}
    census = {}
    for d in doms:
        census[assign.get(d, "UNASSIGNED")] = census.get(assign.get(d, "UNASSIGNED"), 0) + 1
    prov = {"scope": sc.tag, "population": po.tag,
            "rows_in": len(rows), "rows_kept": len(kept),
            "domains_kept": len(doms),
            "split_census": dict(sorted(census.items())),
            "filter_was_a_noop": len(kept) == len(rows)}
    assert prov["scope"]["why"] != prov["population"]["why"], "provenance collision"
    return kept, prov


if __name__ == "__main__":
    fid = "hospital_supply|dev|slot0|n4|none|consistent|near|plain|behavioral"
    other = fid.replace("slot0", "slot12")
    assert Scope.PRIMARY.keeps(fid) and not Scope.PRIMARY.keeps(other)
    assert Scope.ALL_SLOTS.keeps(fid) and Scope.ALL_SLOTS.keeps(other)
    try:
        Scope.require("slot0"); raise SystemExit("FAIL: a bare string was accepted")
    except TypeError:
        pass
    # dose-contrast admissibility (C-CONT-091)
    assert Scope.for_dose_contrast(["slot0"], ["slot0", "slot4"]) is Scope.PRIMARY
    try:
        Scope.for_dose_contrast(["slot0"], ["slot0", "slot4"], scope=Scope.ALL_SLOTS)
        raise SystemExit("FAIL: ALL_SLOTS accepted for a dose contrast")
    except ValueError:
        pass
    try:
        Scope.for_dose_contrast(["slot0"], ["slot4"])
        raise SystemExit("FAIL: disjoint slot sets accepted")
    except ValueError:
        pass
    try:
        Scope.for_dose_contrast(["slot0", "slot4"], ["slot0", "slot4"])
        raise SystemExit("FAIL: a real stratified case was silently reduced to the primary")
    except NotImplementedError:
        pass
    # population (C-CONT-094)
    A = {"d_tr": "train", "d_te": "test"}
    rows = [{"family_id": "x|dev|slot0|n4", "domain": "d_tr"},
            {"family_id": "x|dev|slot0|n4", "domain": "d_te"},
            {"family_id": "x|dev|slot4|n4", "domain": "d_tr"}]
    kept, prov = filter_rows(rows, Scope.PRIMARY, Population.TRAIN_VAL, A)
    assert len(kept) == 1 and prov["population"]["population"] == "train+val", prov
    assert prov["split_census"] == {"train": 1}, prov          # C-CONT-097
    try:
        domain_bootstrap(["a", "b"], lambda s: None, 100, 1)   # C-CONT-098
        raise SystemExit("FAIL: a bootstrap that dropped every draw returned an interval")
    except ValueError:
        pass
    ok = domain_bootstrap(["a", "b"], lambda s: 1.0, 100, 1)
    assert ok["draws_dropped"] == 0 and ok["point"] == 1.0
    assert prov["scope"]["why"].startswith("declared in CONT-ENTRY 094"), \
        "the scope rationale must survive the merge (C-CONT-095)"
    kept, _ = filter_rows(rows, Scope.PRIMARY, Population.ALL_INCLUDING_TEST, A)
    assert len(kept) == 2
    for bad in (None, "train+val", Scope.PRIMARY):
        try:
            Population.require(bad); raise SystemExit("FAIL: %r accepted as a population" % (bad,))
        except TypeError:
            pass
    try:
        filter_rows(rows, Scope.PRIMARY, Population.TRAIN_VAL, {"d_tr": "test", "d_te": "test"})
        raise SystemExit("FAIL: an empty selection was returned silently")
    except ValueError:
        pass
    print("dcs_cont_scope self-test OK:", Scope.PRIMARY.tag, Population.TRAIN_VAL.tag)
