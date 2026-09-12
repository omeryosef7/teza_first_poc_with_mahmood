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


if __name__ == "__main__":
    fid = "hospital_supply|dev|slot0|n4|none|consistent|near|plain|behavioral"
    other = fid.replace("slot0", "slot12")
    assert Scope.PRIMARY.keeps(fid) and not Scope.PRIMARY.keeps(other)
    assert Scope.ALL_SLOTS.keeps(fid) and Scope.ALL_SLOTS.keeps(other)
    try:
        Scope.require("slot0"); raise SystemExit("FAIL: a bare string was accepted")
    except TypeError:
        pass
    print("dcs_cont_scope self-test OK:", Scope.PRIMARY.tag)
