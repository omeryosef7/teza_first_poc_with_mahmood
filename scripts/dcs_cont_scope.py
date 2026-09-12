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
    prov = {**sc.tag, **po.tag,
            "rows_in": len(rows), "rows_kept": len(kept),
            "domains_kept": len({r.get(domain_key) for r in kept})}
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
    assert len(kept) == 1 and prov["population"] == "train+val", prov
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
