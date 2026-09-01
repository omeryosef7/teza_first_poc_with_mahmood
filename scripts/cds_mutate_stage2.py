#!/usr/bin/env python
"""cds_mutate_stage2.py -- adversarial test of `scripts/cds_verify_stage2.py`.

A verifier that has only ever agreed has proved nothing. For each assertion class this script
perturbs the PUBLISHED artifact by a SMALL amount in a temp copy and demands the verifier go RED.

Each mutation targets the value with the LEAST HEADROOM in its class -- the smallest count, the
smallest p-value, the smallest fraction -- because that is where an absolute tolerance would be
vacuous and a lazy check would sail through. A class that CANNOT be made to go red is reported
loudly as a hole in the verifier.
"""
from __future__ import annotations
import copy, json, os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(ROOT, "outputs/boombness/cds_analysis",
                   "cds2_button_specificity_domain_test.json")
VERIFY = os.path.join(ROOT, "scripts", "cds_verify_stage2.py")
EPS = 1e-8          # just above the verifier's 1e-9 relative tolerance


def comp(doc, a, b):
    for c in doc["comparisons"]:
        if c["arm_a"] == a and c["arm_b"] == b:
            return c
    raise KeyError((a, b))


def argmin_comp(doc, key):
    """The comparison whose `key(c)` is smallest -- the least-headroom target."""
    return min(doc["comparisons"], key=key)


# ---------------------------------------------------------------- mutations
def m_asr_a(d):
    c = argmin_comp(d, lambda c: c["asr_a"])
    old = c["asr_a"]; c["asr_a"] = old * (1 + EPS)
    return "asr_a", "%s vs %s: asr_a %.17g -> %.17g (rel +1e-8)" % (c["arm_a"], c["arm_b"], old, c["asr_a"])


def m_asr_b(d):
    c = argmin_comp(d, lambda c: c["asr_b"])
    old = c["asr_b"]; c["asr_b"] = old * (1 + EPS)
    return "asr_b", "%s vs %s: asr_b %.17g -> %.17g (rel +1e-8)" % (c["arm_a"], c["arm_b"], old, c["asr_b"])


def m_attacks(d):
    c = argmin_comp(d, lambda c: c["attacks_a"])
    old = c["attacks_a"]; c["attacks_a"] = old + 1
    return "attacks", "%s vs %s: attacks_a %d -> %d" % (c["arm_a"], c["arm_b"], old, c["attacks_a"])


def m_k_domains(d):
    c = argmin_comp(d, lambda c: c["k_domains"])
    old = c["k_domains"]; c["k_domains"] = old - 1
    return "k_domains", "%s vs %s: k_domains %d -> %d" % (c["arm_a"], c["arm_b"], old, c["k_domains"])


def m_domain_counts(d):
    c = argmin_comp(d, lambda c: c["PRIMARY_domain_sign"]["domains_a_higher"])
    s = c["PRIMARY_domain_sign"]
    old = s["domains_a_higher"]; s["domains_a_higher"] = old + 1
    return "per_domain_up_down", ("%s vs %s: domains_a_higher %d -> %d (smallest in the artifact)"
                                  % (c["arm_a"], c["arm_b"], old, s["domains_a_higher"]))


def m_k_informative(d):
    c = argmin_comp(d, lambda c: c["PRIMARY_domain_sign"]["k_informative"])
    s = c["PRIMARY_domain_sign"]
    old = s["k_informative"]; s["k_informative"] = old - 1
    return "k_informative", "%s vs %s: k_informative %d -> %d" % (c["arm_a"], c["arm_b"], old, s["k_informative"])


def m_sign_p(d):
    c = argmin_comp(d, lambda c: c["PRIMARY_domain_sign"]["p_value"])
    s = c["PRIMARY_domain_sign"]
    old = s["p_value"]; s["p_value"] = old * (1 + EPS)
    return "sign_p_value", "%s vs %s: sign p %.6e -> %.6e (rel +1e-8 on the SMALLEST p)" % (
        c["arm_a"], c["arm_b"], old, s["p_value"])


def m_mcnemar_p(d):
    c = argmin_comp(d, lambda c: c["SECONDARY_row_mcnemar"]["p_value"])
    m = c["SECONDARY_row_mcnemar"]
    old = m["p_value"]; m["p_value"] = old * (1 + EPS)
    return "mcnemar_p", "%s vs %s: McNemar p %.6e -> %.6e (rel +1e-8; abs tol would be vacuous)" % (
        c["arm_a"], c["arm_b"], old, m["p_value"])


def m_mcnemar_counts(d):
    c = argmin_comp(d, lambda c: c["SECONDARY_row_mcnemar"]["discordant_a_only"])
    m = c["SECONDARY_row_mcnemar"]
    old = m["discordant_a_only"]; m["discordant_a_only"] = old + 1
    return "mcnemar_counts", "%s vs %s: discordant_a_only %d -> %d" % (c["arm_a"], c["arm_b"], old, m["discordant_a_only"])


def m_noop(d):
    c = argmin_comp(d, lambda c: c["NOOP_GUARD_frac_byte_identical"])
    old = c["NOOP_GUARD_frac_byte_identical"]
    c["NOOP_GUARD_frac_byte_identical"] = old * (1 + EPS)
    return "noop_fraction", "%s vs %s: noop %.17g -> %.17g (rel +1e-8)" % (c["arm_a"], c["arm_b"], old, c["NOOP_GUARD_frac_byte_identical"])


def m_capable(d):
    c = argmin_comp(d, lambda c: c["PRIMARY_domain_sign"]["attainable_p_floor"])
    s = c["PRIMARY_domain_sign"]
    s["CAPABLE"] = not s["CAPABLE"]
    return "capable_flag", "%s vs %s: CAPABLE flipped to %s" % (c["arm_a"], c["arm_b"], s["CAPABLE"])


def m_p_floor(d):
    c = argmin_comp(d, lambda c: c["PRIMARY_domain_sign"]["attainable_p_floor"])
    s = c["PRIMARY_domain_sign"]
    old = s["attainable_p_floor"]; s["attainable_p_floor"] = old * (1 + EPS)
    return "attainable_p_floor", "%s vs %s: floor %.6e -> %.6e (rel +1e-8 on a 2.3e-10 value)" % (
        c["arm_a"], c["arm_b"], old, s["attainable_p_floor"])


def m_delta_asr(d):
    # least headroom of all: a value that is EXACTLY 0.0, where a relative nudge is a no-op and
    # only a correct zero-handling rule can catch the change.
    c = argmin_comp(d, lambda c: abs(c["delta_asr"]))
    old = c["delta_asr"]
    c["delta_asr"] = old * (1 + EPS) if old else 1e-12
    return "delta_asr", "%s vs %s: delta_asr %.17g -> %.17g" % (c["arm_a"], c["arm_b"], old, c["delta_asr"])


def m_prov_nrows(d):
    k = list(d["provenance"])[0]
    old = d["provenance"][k]["n_rows"]; d["provenance"][k]["n_rows"] = old - 1
    return "provenance_n_rows", "arm %s: n_rows %d -> %d" % (k, old, d["provenance"][k]["n_rows"])


def m_prov_judge(d):
    k = list(d["provenance"])[-1]
    ctr = d["provenance"][k]["judge_model_used"]
    key = list(ctr)[0]
    ctr[key] -= 1
    ctr["openai/gpt-4o"] = 1
    return "provenance_judge_model", "arm %s: one row reattributed to a different judge model" % k


def m_prov_status(d):
    k = list(d["provenance"])[1]
    ctr = d["provenance"][k]["judge_status"]
    ctr["ok"] -= 1
    ctr["error"] = 1
    return "provenance_judge_status", "arm %s: one judge_status ok -> error" % k


def m_noop_verdict(d):
    c = d["comparisons"][0]
    c["NOOP_VERDICT"] = "NO-OP BY CONSTRUCTION -- must not be reported as a control"
    return "noop_verdict_string", "%s vs %s: verdict string flipped without changing the fraction" % (c["arm_a"], c["arm_b"])


def m_n_rows_paired(d):
    c = argmin_comp(d, lambda c: c["n_rows_paired"])
    old = c["n_rows_paired"]; c["n_rows_paired"] = old - 1
    return "n_rows_paired", "%s vs %s: n_rows_paired %d -> %d" % (c["arm_a"], c["arm_b"], old, c["n_rows_paired"])


MUTATIONS = [m_asr_a, m_asr_b, m_attacks, m_k_domains, m_domain_counts, m_k_informative,
             m_sign_p, m_mcnemar_p, m_mcnemar_counts, m_noop, m_capable, m_p_floor,
             m_delta_asr, m_n_rows_paired, m_prov_nrows, m_prov_judge, m_prov_status,
             m_noop_verdict]


def run_verifier(path):
    r = subprocess.run([sys.executable, VERIFY, "--artifact", path],
                       capture_output=True, text=True)
    fails = [ln.split("|")[0].strip()[5:].strip()
             for ln in r.stdout.splitlines() if ln.startswith("FAIL")]
    return r.returncode, fails


def main():
    base = json.load(open(ART))
    tmpd = tempfile.mkdtemp(prefix="cds_mutate_")

    print("BASELINE (unmutated published artifact)")
    rc, fails = run_verifier(ART)
    print("  exit=%d failures=%d  ->  %s\n" % (rc, len(fails),
          "GREEN as expected" if rc == 0 else "ALREADY RED: " + repr(fails[:5])))

    results, holes = [], []
    for fn in MUTATIONS:
        doc = copy.deepcopy(base)
        cls, desc = fn(doc)
        p = os.path.join(tmpd, "mut_%s.json" % cls)
        json.dump(doc, open(p, "w"), indent=1)
        # sanity: the mutation must actually have changed the file
        changed = json.load(open(p)) != base
        rc, fails = run_verifier(p)
        red = rc != 0
        results.append((cls, red, changed, len(fails), fails[:3], desc))
        print("%-6s %-24s %s" % ("RED" if red else "GREEN(!)", cls, desc))
        print("        exit=%d  failing checks=%d  first=%s" % (rc, len(fails), fails[:3]))
        if not red or not changed:
            holes.append((cls, desc, changed))

    print("\n%s\nSUMMARY: %d mutation classes, %d caught (RED), %d NOT caught"
          % ("=" * 78, len(results), sum(1 for r in results if r[1]),
             sum(1 for r in results if not r[1])))
    if holes:
        print("\n*** VERIFIER HOLES -- these mutations did NOT turn the verifier red ***")
        for cls, desc, changed in holes:
            print("  - %-24s %s   (json actually changed: %s)" % (cls, desc, changed))
        sys.exit(1)
    print("every mutation class was caught")


if __name__ == "__main__":
    main()
