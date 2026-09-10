#!/usr/bin/env python3
"""Build the donor-family map for the `cinstall_hi_to_lo` positive control. Mandate section 21.

THE EXPERIMENT THIS ENABLES
---------------------------
Every transplant this project has run is either token-mismatched (B->C, E->A), where the
intervention is large, perfectly consistent and points the WRONG way, or token-matched (C->A),
where it does nothing. So no run so far can distinguish

    (a) the instrument cannot transfer a semantic reading at all, from
    (b) the query codeword genuinely carries no doublespeak-specific store.

`C(high-install) -> C(low-install)` is the only pair on this bank that is BOTH token-matched and
has a non-degenerate readout on both sides (cell C option mass 0.302; cells B and E are 0.011 and
0.036, below the run's own gate, because asked what ' bomb' refers to a model paraphrases). If it
transfers, (b) is supported and the C->A null becomes real evidence. If it does not, (a) holds and
every transplant null in this project -- PHASE-9's included -- is uninformative.

CONSTRUCTION
  * installation per family from the CONCEPT-FREE one-word channel of cell C (section 4 forbids the
    forced-choice channel, and the readout run contains both);
  * recipients: the lowest-installation families, one per domain;
  * donors: the highest-installation families, one per domain;
  * every recipient is mapped to the highest-installation donor NOT IN ITS OWN DOMAIN;
  * TRAIN only.
"""
from __future__ import annotations
import argparse, importlib.util, json, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location("lpm", os.path.join(REPO, "scripts",
                                                                "dcs_cont_layerpos_map.py"))
lpm = importlib.util.module_from_spec(_s); _s.loader.exec_module(lpm)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--readout-run", required=True)
    ap.add_argument("--bank", default="data/boombness_prompts/"
                                      "boombness_prompt_bank_ts116m_button_bomb.jsonl")
    ap.add_argument("--split", default="train", choices=["train", "validation"])
    ap.add_argument("--n-recipients", type=int, default=24)
    ap.add_argument("--n-donor-pool", type=int, default=8,
                    help="rotate recipients over the top-N highest-installation donor families")
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-domains", required=True)
    a = ap.parse_args()

    assign = lpm.load_split()
    keep = {d for d, s in assign.items() if s == a.split} - set(lpm.EXCLUDED_DOMAINS)

    # per-ROW installation, keyed by the bank's own family_id (what the patcher indexes by)
    path = os.path.join(REPO, a.readout_run, "results.jsonl")
    inst = {}
    import math
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("query_kind") != "semantic_one_word" or r.get("cell") != "C":
                continue
            if r.get("n_examples") != 4 or r.get("domain") not in keep:
                continue
            lc, lk = r.get("logp_concept"), r.get("logp_codeword")
            if lc is None or lk is None:
                raise lpm.Refusal("row %r missing logp fields" % r.get("prompt_id"))
            m = max(lc, lk)
            inst[r["family_id"]] = (math.exp(lc - m) / (math.exp(lc - m) + math.exp(lk - m)),
                                    r["domain"])
    if not inst:
        raise lpm.Refusal("no cell-C semantic_one_word dose-4 rows in %r" % a.readout_run)

    # the patcher pairs on the family_ids present in the BANK for the patched query kind; the
    # readout run's family_ids carry the same fields, so they index the same families.
    ordered = sorted(inst.items(), key=lambda kv: -kv[1][0])
    # one family per domain, highest first, as donors; lowest first, as recipients
    seen, donors = set(), []
    for f, (p, d) in ordered:
        if d not in seen:
            seen.add(d); donors.append((f, p, d))
    seen2, recips = set(), []
    for f, (p, d) in reversed(ordered):
        if d not in seen2:
            seen2.add(d); recips.append((f, p, d))
    recips = recips[:a.n_recipients]

    # ROTATE the donor. Mapping every recipient onto the single best donor would make the whole
    # instrument check rest on one prompt's idiosyncrasy: a null would be indistinguishable from
    # "that particular donor state does not transfer". Round-robin over the top donors instead, so
    # a null is a statement about the intervention rather than about one row.
    # THE MAP MUST BE TOTAL OVER THE RECIPIENT DOMAINS. The patcher selects families itself,
    # round-robin over domains, and will not necessarily pick the exact slot listed here; an
    # unmapped family is a hard refusal mid-run. So every cell-C family in a recipient domain gets
    # a donor, not just the single lowest-installation one.
    # THE DOMAIN FILE MUST CARRY THE DONORS TOO. --only-domains-file filters the rows the patcher
    # loads at all, so a donor whose domain is absent has no row to donate and the run refuses
    # mid-flight (observed: job 876304, "donor family farm_storage|... has no natural_doublespeak
    # row"). Recipients AND donors therefore both go in the file, and the map is total over the
    # union so the patcher's own round-robin selection can never land on an unmapped family.
    recip_domains = {rd for _, _, rd in recips}
    donor_domains = {dd for _, _, dd in donors[:a.n_donor_pool]}
    load_domains = recip_domains | donor_domains
    recips = [(f, p, d) for f, (p, d) in ordered if d in load_domains]
    recips.sort(key=lambda t: (t[2], t[0]))
    mapping, rows = {}, []
    for i, (rf, rp, rd) in enumerate(recips):
        pool = [(df, dp, dd) for df, dp, dd in donors[:a.n_donor_pool] if dd != rd]
        if not pool:
            raise lpm.Refusal("no donor outside domain %r in the top-%d pool" % (rd, a.n_donor_pool))
        pick = pool[i % len(pool)]
        mapping[rf] = pick[0]
        rows.append({"recipient_family": rf, "recipient_domain": rd, "recipient_install": rp,
                     "donor_family": pick[0], "donor_domain": pick[2], "donor_install": pick[1]})
    out = {"schema": "dcs_cont_donor_map/1", "split": a.split,
           "readout_run": a.readout_run, "channel": "semantic_one_word", "cell": "C",
           "n_recipients": len(rows), "map": mapping, "detail": rows,
           "recipient_install_range": [min(r["recipient_install"] for r in rows),
                                       max(r["recipient_install"] for r in rows)],
           "donor_install_range": [min(r["donor_install"] for r in rows),
                                   max(r["donor_install"] for r in rows)],
           "primary_stratum": {
               "rule": "recipient_install < 0.10",
               "declared": "in the map artifact, before any transplant row existed",
               "why": ("the map must be TOTAL over the recipient domains because the patcher "
                       "selects families itself, which readmits some already-installed recipients. "
                       "A transplant into a recipient that already reads the concept has almost no "
                       "gap to close and cannot show transfer. The stratum is defined on the "
                       "PREDICTOR (baseline installation), never on the outcome -- mandate section "
                       "4 forbids post-hoc exclusion by outcome."),
               "n_in_stratum": sum(1 for r in rows if r["recipient_install"] < 0.10),
               "n_total": len(rows)},
           "n_load_domains": len(load_domains),
           "n_recipient_domains": len(recip_domains),
           "n_donor_domains": len(donor_domains),
           "n_distinct_donors": len({r["donor_family"] for r in rows}),
           "n_distinct_donor_domains": len({r["donor_domain"] for r in rows})}
    op = os.path.join(REPO, a.out); os.makedirs(os.path.dirname(op), exist_ok=True)
    json.dump(out, open(op, "w", encoding="utf-8"), indent=1)
    od = os.path.join(REPO, a.out_domains); os.makedirs(os.path.dirname(od), exist_ok=True)
    with open(od, "w", encoding="utf-8") as fh:
        fh.write("# recipient domains for the cinstall_hi_to_lo positive control (%s split)\n"
                 % a.split)
        for dom in sorted(load_domains):
            fh.write(dom + "\n")
    print("[donormap] %d recipients | recipient installation %.4f..%.4f | donor %.4f..%.4f"
          % (len(rows), out["recipient_install_range"][0], out["recipient_install_range"][1],
             out["donor_install_range"][0], out["donor_install_range"][1]))
    print("[donormap] wrote %s and %s" % (a.out, a.out_domains))
    for r in rows[:4]:
        print("    %-22s (%.3f) <- %-22s (%.3f)" % (r["recipient_domain"], r["recipient_install"],
                                                    r["donor_domain"], r["donor_install"]))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except lpm.Refusal as e:
        print("REFUSING: %s" % e, file=sys.stderr); raise SystemExit(2)
