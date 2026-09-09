#!/usr/bin/env python3
"""Emit the `--exclude-prompt-ids` file for the THREE preregistered whole-population exclusions.

WHY A SCRIPT AND NOT A HAND-WRITTEN LIST. `score_behavior.main` refuses an exclusion id that is
not present in the selected population, so the list must be scoped to exactly the
(query_kind, bank_block, condition) an arm selects. A hand-maintained list would be a different
list per arm, edited by hand, which is the shape `CDS-C-001` warns about. This derives it from the
bank every time and prints the arithmetic, so "which rows did you exclude" is answerable from the
file rather than from memory.

The three domains and their authority (frozen before any outcome of this phase):
  restaurant_kitchen  DCS-C-082   knives are natural kitchen furniture, so bomb/gun harm pools
                                  generated for it keep naming a knife
  subway_station      DCS-C-087
  school_campus       DCS-C-075 / DCS-R-108
They are excluded from the ENTIRE analysis population, all concepts, all cells -- not per arm.

USAGE
  python3 scripts/dcs_ts_make_exclusions.py \
      --bank data/boombness_prompts/boombness_prompt_bank_ts116m_button_bomb.jsonl \
      --query-kind behavioral --bank-block cds_n4 --condition natural_doublespeak \
      --out runargs/dcs_succ/exclude_button_bomb_behavioral_cds_n4_C.txt
"""
from __future__ import annotations
import argparse, hashlib, json, os, sys

EXCLUDED_DOMAINS = ("restaurant_kitchen", "school_campus", "subway_station")
SPLIT_MANIFEST = "data/boombness_prompts/dcs_ts116_domain_split.json"
AUTHORITY = {"restaurant_kitchen": "DCS-C-082", "school_campus": "DCS-C-075 / DCS-R-108",
             "subway_station": "DCS-C-087"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", required=True)
    ap.add_argument("--query-kind", required=True)
    ap.add_argument("--bank-block", required=True)
    ap.add_argument("--condition", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--split", default="",
                    help="if given, ALSO exclude every row whose domain the frozen manifest "
                         "assigns to a different split. The manifest is read, never regenerated.")
    a = ap.parse_args()

    keep_domains = None
    if a.split:
        man = json.load(open(os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), SPLIT_MANIFEST), encoding="utf-8"))
        if a.split not in set(man["assign"].values()):
            print("REFUSING: split %r is not a value of the frozen manifest" % a.split,
                  file=sys.stderr)
            return 2
        keep_domains = {d for d, s_ in man["assign"].items() if s_ == a.split}

    sel, exc, doms = 0, [], set()
    with open(a.bank, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if (r["query_kind"] != a.query_kind or r["bank_block"] != a.bank_block
                    or r["condition"] != a.condition):
                continue
            sel += 1
            doms.add(r["domain"])
            if r["domain"] in EXCLUDED_DOMAINS or (
                    keep_domains is not None and r["domain"] not in keep_domains):
                exc.append(r["prompt_id"])

    if not exc:
        # An empty exclusion that still gets recorded as an exclusion is the failure mode the
        # runner's own loader refuses on. Refuse it here too, one step earlier.
        print("REFUSING: the selection (%s, %s, %s) contains none of %s -- an empty exclusion "
              "file would be a no-op recorded as an exclusion."
              % (a.query_kind, a.bank_block, a.condition, list(EXCLUDED_DOMAINS)), file=sys.stderr)
        return 2
    if len(set(exc)) != len(exc):
        print("REFUSING: duplicate prompt_id in the derived list", file=sys.stderr)
        return 2

    exc = sorted(exc)
    sha = hashlib.sha256("\n".join(exc).encode("utf-8")).hexdigest()[:16]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("# Derived by scripts/dcs_ts_make_exclusions.py from %s\n" % a.bank)
        fh.write("# selection: query_kind=%s bank_block=%s condition=%s split=%s\n"
                 % (a.query_kind, a.bank_block, a.condition, a.split or "ALL"))
        if a.split:
            fh.write("# split source: %s (frozen; read, never regenerated). Rows outside split "
                     "%r are excluded IN ADDITION to the three whole-population exclusions.\n"
                     % (SPLIT_MANIFEST, a.split))
        fh.write("# %d selected rows over %d domains; %d rows EXCLUDED (%d preregistered "
                 "whole-population domains%s); %d rows remain over %d domains\n"
                 % (sel, len(doms), len(exc), len(EXCLUDED_DOMAINS),
                    "" if not a.split else " PLUS every domain outside split %r" % a.split,
                    sel - len(exc),
                    len((doms if keep_domains is None else doms & keep_domains)
                        - set(EXCLUDED_DOMAINS))))
        for d in EXCLUDED_DOMAINS:
            fh.write("#   %-20s %s\n" % (d, AUTHORITY[d]))
        fh.write("# exclusion_sha16 = %s\n" % sha)
        for i in exc:
            fh.write(i + "\n")

    # F6: this line used to print len(doms - EXCLUDED_DOMAINS), which ignores the --split filter,
    # so it said 113 while the file header it had just written said 67. Same shape as D-002: a
    # count that is not the count. It now reports the domains that actually REMAIN.
    remaining_domains = (doms if keep_domains is None else doms & keep_domains) - set(
        EXCLUDED_DOMAINS)
    print("wrote %s: selected=%d excluded=%d remain=%d domains_remain=%d exclusion_sha16=%s"
          % (a.out, sel, len(exc), sel - len(exc), len(remaining_domains), sha))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
