"""cited_artifact_check.py — a run id cited in the deliverable that does not exist, or must not be used.

WHY. The plan document cites run directories as the evidence for its claims. Nothing checked that
those directories still exist, or that they pass the admissibility rules this sprint spent days
building. A claim whose artifact is missing or excluded reads exactly like a claim whose artifact is
fine — the citation is a string.

This is the §11.4 deep-review check, promoted from an ad-hoc script into a guard, for the reason
that check itself demonstrated: **run once by hand it found nothing; the value is in it running
every time.**

THE HAND-LISTING BUG THIS MODULE WAS BORN FROM. The first version of that ad-hoc check searched
FOUR output roots, chosen from memory, and reported **14 missing run ids**. Widening to all 36
roots gave **0 missing** — every id was in an experiment directory I had not listed. So the
hand-listing failure happened *inside the check written to catch hand-listing failures*, and the
only thing that stopped it becoming a false claim in a deep-review section was that 14 was
implausible enough to re-run. **Implausibility is not a control.**

Hence the rule this module enforces on itself: **enumerate the SEARCH SPACE, not just the row set.**
`_roots()` globs every directory under the output root; it never names one.

ADMISSIBILITY vs EXISTENCE are separate, per §11.2. A cited run may exist and still be unusable —
partial, excluded, gate-failed. Both are checked, and a run may be cited as a *documented negative
example* (this sprint cites two), so `CITED_AS_REFUSED` names those with a reason. Silence is not
allowed; that is §7.5's rule applied to artifacts.

Reads directory metadata only. No model, no generations, no network.
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PLAN = os.path.join(ROOT, "external_md", "BOOMBNESS_RESEARCH_VALIDATION_AND_OBJECTIVE_PLAN.md")
OUT_ROOT = os.path.join(ROOT, "outputs", "boombness")

sys.path.insert(0, HERE)

#: Run ids deliberately cited as examples of runs that MUST NOT be used. The value is the reason and
#: is required — an unexplained exemption is the silence this guard exists to prevent.
CITED_AS_REFUSED = {
    "ab_C_20260819_002240_1397246":
        "cited INSIDE §0.2.5 as the 482-row partial that the first corpus sweep wrongly ingested "
        "and reported under the complete run's tag; it is the negative example of that section",
    "w640_20260827_224651_3802479":
        "cited under §0.12, whose heading reads 'and my own guard refused it' — the run is the "
        "subject of a refusal, not the evidence for a claim",
}

#: A run id as this repo writes them: <tag>_<YYYYMMDD>_<HHMMSS>_<pid>.
RUN_ID = re.compile(r"\b([A-Za-z0-9_]+_20[0-9]{6}_[0-9]{6}_[0-9]+)\b")

#: The corpus has never cited fewer than this many run ids. A collapse means the SCANNER broke, not
#: that the citations vanished — the degenerate-pass floor from §7.6, which this module inherits
#: rather than rediscovers.
MIN_EXPECTED = 10


def _roots():
    """Every directory under the output root. ENUMERATED, never hand-listed — see module docstring."""
    if not os.path.isdir(OUT_ROOT):
        return []
    return [os.path.join(OUT_ROOT, d) for d in sorted(os.listdir(OUT_ROOT))
            if os.path.isdir(os.path.join(OUT_ROOT, d))]


def cited_ids(text: str):
    return sorted(set(RUN_ID.findall(text)))


def resolve(run_id: str, roots=None):
    """The directory a cited id refers to, or None. Searches every root."""
    for r in (roots if roots is not None else _roots()):
        p = os.path.join(r, run_id)
        if os.path.isdir(p):
            return p
    return None


def main() -> int:
    if not os.path.isfile(PLAN):
        print("[cited-artifact] plan missing; nothing to check")
        return 0
    import asr_protocol as ap

    ids = cited_ids(open(PLAN, encoding="utf-8").read())
    roots = _roots()

    if len(ids) < MIN_EXPECTED:
        print(f"[cited-artifact] FAIL — only {len(ids)} run ids found in the plan, expected at "
              f"least {MIN_EXPECTED}. The scanner has broken; a guard that checks nothing must not "
              f"report success.")
        return 1

    missing, inadmissible, ok = [], [], 0
    for rid in ids:
        d = resolve(rid, roots)
        if d is None:
            missing.append(rid)
            continue
        try:
            ap.check_run_readable(d)
            ok += 1
        except Exception as e:                      # noqa: BLE001 — any refusal is a refusal
            if rid in CITED_AS_REFUSED:
                ok += 1
            else:
                inadmissible.append((rid, os.path.basename(os.path.dirname(d)), str(e)[:70]))

    print(f"[cited-artifact] {len(ids)} run ids cited across {len(roots)} enumerated roots; "
          f"{ok} usable or documented-refused")
    for rid in missing:
        print(f"  MISSING {rid}: cited in the plan, found in none of the {len(roots)} roots")
    for rid, root, why in inadmissible:
        print(f"  INADMISSIBLE {rid} (in {root}): {why}")
        print(f"      -> fix the claim, or add {rid} to CITED_AS_REFUSED with a reason")
    if missing or inadmissible:
        print("[cited-artifact] FAIL — a claim cites an artifact that is absent or unusable.")
        return 1
    print("[cited-artifact] every cited artifact exists and is usable or documented-refused")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
