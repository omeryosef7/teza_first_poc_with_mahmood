#!/usr/bin/env python
"""cds_verify_stage2.py -- INDEPENDENT verifier for the Stage-2 button-specificity artifact.

Re-derives every headline number in
    outputs/boombness/cds_analysis/cds2_button_specificity_domain_test.json
straight from the raw judge `results.jsonl` files, by a code path written from scratch.

It does NOT import, exec, or copy `scripts/cds_domain_test.py`. Standard library only.
It reads ONLY scalar columns of `results.jsonl` and never opens `gens.jsonl`.

Exact binomial: implemented here as INTEGER arithmetic over `math.comb` and `fractions.Fraction`
(the producer used floating-point `p**k` pmf terms), and cross-checked against
  (a) a multiplicative-recurrence tail that never calls `math.comb`, and
  (b) for a small k, brute-force enumeration of all 2**n sign patterns.

Comparison tolerance is RELATIVE (1e-9) with a small ABSOLUTE floor (1e-12) so that it is not
vacuous on values that are exactly 0 or very small.
"""
from __future__ import annotations
import argparse, json, math, os, sys
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_ARTIFACT = os.path.join(ROOT, "outputs/boombness/cds_analysis",
                                "cds2_button_specificity_domain_test.json")
JUDGE_ROOT = os.path.join(ROOT, "outputs/boombness/judge")
JUDGE_PREFIX = "cds2j_button_"
DOSE = 4
ALPHA = 0.05
PIN = "openai/gpt-4o-mini"
RTOL = 1e-9
# NOTE: an absolute floor large enough to matter is VACUOUS here -- p-values in this artifact go
# down to 3e-19, so any floor above ~1e-19 would swallow a total corruption of the p-value.
# The floor therefore exists ONLY to make exact zeros comparable, and is otherwise never binding.
ATOL = 0.0

# ------------------------------------------------------------------ check ledger
CHECKS = []
WARNINGS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print("%-4s %s%s" % ("PASS" if ok else "FAIL", name, ("   | " + detail) if detail else ""))
    return bool(ok)


def close(got, want):
    """Relative tolerance with an absolute floor; exact-equal ints/bools handled by caller."""
    if got is None or want is None:
        return got is want
    try:
        g, w = float(got), float(want)
    except (TypeError, ValueError):
        return got == want
    if math.isnan(g) or math.isnan(w):
        return False
    scale = max(abs(g), abs(w))
    if scale == 0.0:                 # both exactly zero
        return True
    if g == 0.0 or w == 0.0:         # exactly one is zero -> no relative tolerance can excuse it
        return abs(g - w) <= ATOL
    return abs(g - w) <= RTOL * scale


def check_num(name, got, want):
    return check(name, close(got, want), "derived=%r published=%r" % (got, want))


def check_int(name, got, want):
    return check(name, isinstance(want, int) and not isinstance(want, bool) and got == want,
                 "derived=%r published=%r" % (got, want))


def check_eq(name, got, want):
    return check(name, got == want, "derived=%r published=%r" % (got, want))


# ------------------------------------------------------------------ exact binomial (mine)
def two_sided_sign_p_exact(x, n):
    """Exact two-sided equal-tail-doubled binomial p at p=1/2, as an exact Fraction.

    Integer arithmetic only: sum_{k<=min(x,n-x)} C(n,k) over 2**n, doubled, capped at 1.
    """
    if n == 0:
        return Fraction(1, 1)
    lo = min(x, n - x)
    tail = sum(math.comb(n, k) for k in range(lo + 1))       # exact integer
    p = Fraction(2 * tail, 1 << n)
    return p if p < 1 else Fraction(1, 1)


def two_sided_sign_p_recurrence(x, n):
    """Same quantity WITHOUT math.comb: C(n,k+1) = C(n,k)*(n-k)/(k+1), exact integers."""
    if n == 0:
        return Fraction(1, 1)
    lo = min(x, n - x)
    c, tail = 1, 0
    for k in range(lo + 1):
        tail += c
        c = c * (n - k) // (k + 1)
    p = Fraction(2 * tail, 1 << n)
    return p if p < 1 else Fraction(1, 1)


def two_sided_sign_p_bruteforce(x, n):
    """Enumerate all 2**n up/down patterns; count those at least as extreme. Small n only."""
    lo = min(x, n - x)
    hits = 0
    for mask in range(1 << n):
        u = bin(mask).count("1")
        if min(u, n - u) <= lo:
            hits += 1
    p = Fraction(hits, 1 << n)
    return p if p < 1 else Fraction(1, 1)


def two_sided_sign_p_convolution(x, n):
    """Third path: build the Binomial(n, 1/2) pmf by exact repeated convolution of Fractions.

    Uses neither math.comb nor factorials -- only Fraction addition -- so a bug in the
    combinatorial code above cannot hide behind a shared helper.
    """
    if n == 0:
        return Fraction(1, 1)
    dist = [Fraction(1, 1)]
    half = Fraction(1, 2)
    for _ in range(n):
        nxt = [Fraction(0, 1)] * (len(dist) + 1)
        for k, v in enumerate(dist):
            nxt[k] += v * half
            nxt[k + 1] += v * half
        dist = nxt
    lo = min(x, n - x)
    tail = sum(dist[k] for k in range(lo + 1))
    p = 2 * tail
    return p if p < 1 else Fraction(1, 1)


def p_floor(k_inf):
    return 2.0 / (2 ** k_inf) if k_inf > 0 else 1.0


# ------------------------------------------------------------------ raw data
SCALARS = ("prompt_id", "domain", "n_examples", "malicious_at_0.5", "refused",
           "completion_sha256_16", "judge_model_used", "judge_status", "split")


def load_arm(judge_dir):
    """Read only scalar columns. Returns {prompt_id: {...}} plus duplicate-id count."""
    rows, dups, total = {}, 0, 0
    with open(os.path.join(judge_dir, "results.jsonl")) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            total += 1
            if raw.get("n_examples") != DOSE:
                continue
            pid = raw["prompt_id"]
            if pid in rows:
                dups += 1
            rows[pid] = {k: raw.get(k) for k in SCALARS}
            rows[pid]["attack"] = 1 if raw.get("malicious_at_0.5") else 0
    return rows, dups, total


def derive(a_rows, b_rows):
    """Everything the artifact claims for one ordered pair (a, b), derived from scratch."""
    ids = sorted(set(a_rows) & set(b_rows))
    n = len(ids)
    dom_a, dom_b, dom_seen = {}, {}, set()
    dn = up = same_sha = atk_a = atk_b = 0
    for pid in ids:
        a, b = a_rows[pid], b_rows[pid]
        d = a["domain"]
        dom_seen.add(d)
        dom_a[d] = dom_a.get(d, 0) + a["attack"]
        dom_b[d] = dom_b.get(d, 0) + b["attack"]
        atk_a += a["attack"]
        atk_b += b["attack"]
        if a["attack"] == 1 and b["attack"] == 0:
            dn += 1
        elif b["attack"] == 1 and a["attack"] == 0:
            up += 1
        if a["completion_sha256_16"] and a["completion_sha256_16"] == b["completion_sha256_16"]:
            same_sha += 1
    dom_higher_a = sum(1 for d in dom_seen if dom_a[d] > dom_b[d])
    dom_higher_b = sum(1 for d in dom_seen if dom_b[d] > dom_a[d])
    k_inf = dom_higher_a + dom_higher_b
    p_sign = two_sided_sign_p_exact(dom_higher_b, k_inf)
    p_mcn = two_sided_sign_p_exact(up, up + dn)
    return {
        "n_rows_paired": n,
        "k_domains": len(dom_seen),
        "attacks_a": atk_a, "attacks_b": atk_b,
        "asr_a": (atk_a / n) if n else 0.0,
        "asr_b": (atk_b / n) if n else 0.0,
        "delta_asr": ((atk_b - atk_a) / n) if n else 0.0,
        "domains_a_higher": dom_higher_a, "domains_b_higher": dom_higher_b,
        "k_informative": k_inf,
        "p_sign_frac": p_sign, "p_sign": float(p_sign),
        "attainable_p_floor": p_floor(k_inf),
        "CAPABLE": p_floor(k_inf) <= ALPHA,
        "discordant_a_only": dn, "discordant_b_only": up,
        "p_mcn_frac": p_mcn, "p_mcn": float(p_mcn),
        "noop": (same_sha / n) if n else 0.0,
    }


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description="independent verifier for the Stage-2 artifact")
    ap.add_argument("--artifact", default=DEFAULT_ARTIFACT)
    a = ap.parse_args()
    pub = json.load(open(a.artifact))
    print("VERIFYING %s\n" % a.artifact)

    # ---- 0. self-test of my own exact binomial against two independent derivations
    for (x, n) in ((0, 1), (1, 3), (3, 12), (2, 16), (5, 18)):
        mine = two_sided_sign_p_exact(x, n)
        check("binom/self  x=%d n=%d  recurrence agrees" % (x, n),
              mine == two_sided_sign_p_recurrence(x, n), "p=%s" % mine)
        if n <= 18:
            check("binom/self  x=%d n=%d  brute-force 2**n enumeration agrees" % (x, n),
                  mine == two_sided_sign_p_bruteforce(x, n), "p=%s" % mine)
    # closed form for the symmetric edge case: x=0 -> p = 2/2**n exactly
    check("binom/self  x=0 n=20 equals closed form 2/2**20",
          two_sided_sign_p_exact(0, 20) == Fraction(2, 1 << 20))
    check("binom/self  n=0 degenerate p=1", two_sided_sign_p_exact(0, 0) == 1)

    # ---- 1. arms and judge dirs
    prov = pub["provenance"]
    arms = list(prov)
    check_eq("meta/schema", pub.get("schema"), "CDS_DOMAIN_TEST/1")
    check_num("meta/alpha", ALPHA, pub.get("alpha"))
    check_eq("meta/dose", DOSE, pub.get("dose"))
    check_eq("meta/outcome", "attack", pub.get("outcome"))
    check_eq("meta/n_arms", 5, len(arms))
    disc = sorted(d for d in os.listdir(JUDGE_ROOT) if d.startswith(JUDGE_PREFIX))
    used = sorted(os.path.basename(prov[k]["judge_dir"].rstrip("/")) for k in arms)
    check_eq("prov/judge dirs are exactly the five %s* runs on disk" % JUDGE_PREFIX, used, disc)

    loaded = {}
    for k in arms:
        d = prov[k]["judge_dir"]
        rows, dups, total = load_arm(d)
        loaded[k] = rows
        check_int("prov/%s n_rows at n_examples==%d is 380" % (k, DOSE), len(rows), 380)
        check("prov/%s no duplicate prompt_id" % k, dups == 0, "dups=%d" % dups)
        check("prov/%s every raw row is dose %d (no filtering happened)" % (k, DOSE),
              total == len(rows), "raw=%d kept=%d" % (total, len(rows)))
        check_int("prov/%s published n_rows matches derived" % k, len(rows), prov[k]["n_rows"])
        bad_m = sorted({r["judge_model_used"] for r in rows.values()} - {PIN})
        check("prov/%s every judge_model_used == %s" % (k, PIN), not bad_m, "offenders=%r" % bad_m)
        check_eq("prov/%s published judge_model_used counter" % k,
                 {PIN: len(rows)}, prov[k]["judge_model_used"])
        bad_s = sorted({str(r["judge_status"]) for r in rows.values()} - {"ok"})
        check("prov/%s every judge_status == ok" % k, not bad_s, "offenders=%r" % bad_s)
        check_eq("prov/%s published judge_status counter" % k,
                 {"ok": len(rows)}, prov[k]["judge_status"])
        check_eq("prov/%s published all_pinned_4o_mini flag" % k,
                 True, prov[k]["all_pinned_4o_mini"])

    # published frac_stop_length must agree with the gens summary.json it names (scalar field only)
    for k in arms:
        g = prov[k].get("gens_dir")
        src = None
        if g and os.path.exists(os.path.join(g, "summary.json")):
            sm = json.load(open(os.path.join(g, "summary.json")))
            src = (sm.get("counts") or {}).get("frac_stop_length", sm.get("frac_stop_length"))
        else:
            WARNINGS.append("arm %s: gens_dir has no summary.json" % k)
        check_eq("prov/%s frac_stop_length matches its gens summary.json" % k,
                 src, prov[k].get("frac_stop_length"))
        if prov[k].get("frac_stop_length") is None:
            WARNINGS.append("arm %s: frac_stop_length is NULL -- the truncation gate the producer "
                            "docstring says it reports is UNPOPULATED in this artifact" % k)

    # balanced design: the domain sign test assumes each domain contributes rows in both arms
    sizes = {}
    for pid in loaded[arms[0]]:
        dm = loaded[arms[0]][pid]["domain"]
        sizes[dm] = sizes.get(dm, 0) + 1
    check("design/38 domains x 10 rows, balanced", len(sizes) == 38 and set(sizes.values()) == {10},
          "k_domains=%d rows_per_domain=%r" % (len(sizes), sorted(set(sizes.values()))))

    ref_ids = set(loaded[arms[0]])
    for k in arms[1:]:
        check("prov/%s prompt_id set identical to %s" % (k, arms[0]),
              set(loaded[k]) == ref_ids,
              "only_ref=%d only_arm=%d" % (len(ref_ids - set(loaded[k])),
                                           len(set(loaded[k]) - ref_ids)))
    # domain labels must agree row-for-row across arms, else "per-domain" is ill-defined
    for k in arms[1:]:
        mism = sum(1 for pid in ref_ids
                   if loaded[k][pid]["domain"] != loaded[arms[0]][pid]["domain"])
        check("prov/%s domain label agrees with %s on every prompt_id" % (k, arms[0]),
              mism == 0, "mismatches=%d" % mism)

    # ---- 2. the ten comparisons
    comps = pub["comparisons"]
    check_eq("comps/count is 10", 10, len(comps))
    want_pairs = {frozenset((x, y)) for i, x in enumerate(arms) for y in arms[i + 1:]}
    got_pairs = {frozenset((c["arm_a"], c["arm_b"])) for c in comps}
    check_eq("comps/cover all 10 unordered arm pairs", want_pairs, got_pairs)

    smallest_kinf = min(c["PRIMARY_domain_sign"]["k_informative"] for c in comps)
    brute_done = False
    for c in comps:
        A, B = c["arm_a"], c["arm_b"]
        tag = "%s_vs_%s" % (A, B)
        d = derive(loaded[A], loaded[B])
        s = c["PRIMARY_domain_sign"]
        m = c["SECONDARY_row_mcnemar"]
        check_int("%s/n_rows_paired" % tag, d["n_rows_paired"], c["n_rows_paired"])
        check_int("%s/k_domains" % tag, d["k_domains"], c["k_domains"])
        check_num("%s/asr_a" % tag, d["asr_a"], c["asr_a"])
        check_num("%s/asr_b" % tag, d["asr_b"], c["asr_b"])
        check_num("%s/delta_asr" % tag, d["delta_asr"], c["delta_asr"])
        check_int("%s/attacks_a" % tag, d["attacks_a"], c["attacks_a"])
        check_int("%s/attacks_b" % tag, d["attacks_b"], c["attacks_b"])
        check("%s/asr_a consistent with attacks_a/n" % tag,
              close(d["attacks_a"] / d["n_rows_paired"], c["asr_a"]))
        check("%s/asr_b consistent with attacks_b/n" % tag,
              close(d["attacks_b"] / d["n_rows_paired"], c["asr_b"]))
        check_int("%s/domains_a_higher" % tag, d["domains_a_higher"], s["domains_a_higher"])
        check_int("%s/domains_b_higher" % tag, d["domains_b_higher"], s["domains_b_higher"])
        check_int("%s/k_informative" % tag, d["k_informative"], s["k_informative"])
        check("%s/k_informative == up+down and <= k_domains" % tag,
              s["k_informative"] == s["domains_a_higher"] + s["domains_b_higher"]
              <= c["k_domains"])
        check_num("%s/sign p_value" % tag, d["p_sign"], s["p_value"])
        check_num("%s/attainable_p_floor == 2/2**k_inf" % tag,
                  d["attainable_p_floor"], s["attainable_p_floor"])
        check("%s/sign p >= attainable floor" % tag,
              d["p_sign"] >= d["attainable_p_floor"] * (1 - RTOL),
              "p=%.6g floor=%.6g" % (d["p_sign"], d["attainable_p_floor"]))
        check_eq("%s/CAPABLE flag" % tag, d["CAPABLE"], s["CAPABLE"])
        check_eq("%s/CAPABLE note wording matches flag" % tag,
                 d["CAPABLE"], s["note"] == "capable")
        check_int("%s/mcnemar discordant_a_only" % tag,
                  d["discordant_a_only"], m["discordant_a_only"])
        check_int("%s/mcnemar discordant_b_only" % tag,
                  d["discordant_b_only"], m["discordant_b_only"])
        check_num("%s/mcnemar p_value" % tag, d["p_mcn"], m["p_value"])
        check_num("%s/NOOP_GUARD_frac_byte_identical" % tag,
                  d["noop"], c["NOOP_GUARD_frac_byte_identical"])
        check_eq("%s/NOOP_VERDICT matches fraction" % tag,
                 "NO-OP BY CONSTRUCTION -- must not be reported as a control"
                 if d["noop"] >= 0.99 else "arm changed completions; usable",
                 c["NOOP_VERDICT"])
        # independent re-derivation of the p-values by the comb-free recurrence
        check("%s/sign p reproduced by comb-free recurrence" % tag,
              d["p_sign_frac"] == two_sided_sign_p_recurrence(d["domains_b_higher"],
                                                              d["k_informative"]))
        check("%s/mcnemar p reproduced by comb-free recurrence" % tag,
              d["p_mcn_frac"] == two_sided_sign_p_recurrence(
                  d["discordant_b_only"],
                  d["discordant_a_only"] + d["discordant_b_only"]))
        check("%s/sign p reproduced by exact convolution (no comb, no factorial)" % tag,
              d["p_sign_frac"] == two_sided_sign_p_convolution(d["domains_b_higher"],
                                                               d["k_informative"]),
              "exact p = %s" % d["p_sign_frac"])
        check("%s/mcnemar p reproduced by exact convolution" % tag,
              d["p_mcn_frac"] == two_sided_sign_p_convolution(
                  d["discordant_b_only"],
                  d["discordant_a_only"] + d["discordant_b_only"]))
        if not brute_done and d["k_informative"] == smallest_kinf and d["k_informative"] <= 24:
            check("%s/sign p reproduced by brute-force 2**%d enumeration"
                  % (tag, d["k_informative"]),
                  d["p_sign_frac"] == two_sided_sign_p_bruteforce(d["domains_b_higher"],
                                                                  d["k_informative"]),
                  "exact p = %s" % d["p_sign_frac"])
            brute_done = True

    # doses: if every raw row is already dose 4, the --dose filter is untested by this data
    doses = set()
    for k in arms:
        with open(os.path.join(prov[k]["judge_dir"], "results.jsonl")) as fh:
            for line in fh:
                if line.strip():
                    doses.add(json.loads(line).get("n_examples"))
    if doses == {DOSE}:
        WARNINGS.append("every raw judge row is already n_examples==%d, so the dose restriction is "
                        "a NO-OP on this data: a dose-filtering bug would be invisible here" % DOSE)
    if all(c["PRIMARY_domain_sign"]["CAPABLE"] for c in comps):
        WARNINGS.append("CAPABLE is True in all 10 comparisons: the INCAPABLE branch and its "
                        "'UNINFORMATIVE BY CONSTRUCTION' note are never exercised by this data")
    if all(c["NOOP_GUARD_frac_byte_identical"] < 0.99 for c in comps):
        WARNINGS.append("no arm is anywhere near the 0.99 no-op threshold (max %.3f): the NO-OP "
                        "branch of the guard is never exercised by this data"
                        % max(c["NOOP_GUARD_frac_byte_identical"] for c in comps))

    if WARNINGS:
        print("\nWARNINGS (not failures -- weak spots where this data cannot test the claim):")
        for w in WARNINGS:
            print("  ! %s" % w)

    n_fail = sum(1 for _, ok, _ in CHECKS if not ok)
    print("\n%d checks, %d failures" % (len(CHECKS), n_fail))
    if n_fail:
        print("FAILED CHECKS:")
        for name, ok, detail in CHECKS:
            if not ok:
                print("  - %s   | %s" % (name, detail))
    print("VERDICT: %s" % ("RED" if n_fail else "GREEN"))
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
