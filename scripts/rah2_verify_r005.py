#!/usr/bin/env python3
"""Independent verifier for `RAH2-R-005`. Stdlib only; imports nothing from the producer.

Re-derives every number in R-005's two tables straight from the committed artifacts and REFUSES
(exit 1) on any mismatch. Written to be re-runnable as an audit: `python3 scripts/rah2_verify_r005.py`

The point is not to re-run the model -- it is to check that the published table is what the raw
`grid` records say, computed by code that shares nothing with `rah_preflight_transport.py`.
"""
import glob
import json
import sys

GATE_CONTROL = 0.1          # `RAH2-PR-001` positive-control threshold
GATE_MASS = 0.05            # `RAH2-PR-001` option-mass gate
FAILS = []


def one(pattern):
    hits = sorted(glob.glob("outputs/boombness/rah_preflight/" + pattern))
    if len(hits) != 1:
        raise SystemExit("expected exactly 1 artifact for %r, got %d" % (pattern, len(hits)))
    return json.load(open(hits[0]))


def best_pconc(d, form):
    """Max over R of `pos_ctrl_max`, which the producer defines at the p_concept-argmax donor layer."""
    rows = [r for r in d["grid"] if r["form"] == form]
    if not rows:
        return None
    return max(rows, key=lambda r: r["pos_ctrl_max"])


def check(label, got, want, tol=5e-4):
    ok = got is not None and abs(got - want) <= tol
    print("  %-42s published %-12.6g artifact %-12.6g %s"
          % (label, want, got if got is not None else float("nan"), "OK" if ok else "MISMATCH"))
    if not ok:
        FAILS.append(label)


print("== R-005 table 1: positive control, P(concept) under a concept-bearing donor")
pcf_p, pcf_q = one("rah2pcf_p_cb_*.json"), one("rah2pcf_q_cb_*.json")
pc_p, pc_q = one("rah2pc_p_cb_*.json"), one("rah2pc_q_cb_*.json")
for d, tag, table in ((pcf_p, "Llama", {"fc_probe_last": 0.9087, "id07_raw": 0.8409}),
                      (pcf_q, "Qwen3", {"fc_probe_last": 1.0000, "id07_raw": 0.8404}),
                      (pcf_p, "Llama", {"fewshot_syn": 0.0197, "fewshot_cat": 0.0658}),
                      (pcf_q, "Qwen3", {"fewshot_syn": 0.0965, "fewshot_cat": 0.0087}),
                      (pc_p, "Llama", {"id07_tmpl": 0.5011, "cat_cue": 0.0091,
                                       "synonym": 0.0013, "defn_oneword": 3.53e-05}),
                      (pc_q, "Qwen3", {"id07_tmpl": 0.0142, "cat_cue": 0.0354,
                                       "synonym": 1.48e-08, "defn_oneword": 2.57e-08})):
    assert d["donor_condition"] == "direct_harmful", "table 1 must use the registered control donor"
    for form, want in table.items():
        b = best_pconc(d, form)
        check("%s %s pos-control" % (tag, form), b["pos_ctrl_max"] if b else None, want)

print("\n== the validated-readout verdict (gate %.2f) -- recomputed, not read" % GATE_CONTROL)
for d, tag in ((pcf_p, "Llama"), (pcf_q, "Qwen3")):
    for form in ("id07_raw", "fewshot_syn", "fewshot_cat"):
        b = best_pconc(d, form)
        validated = b["pos_ctrl_max"] > GATE_CONTROL
        expect = (form == "id07_raw")
        print("  %-24s validated=%-5s expected=%-5s %s"
              % (tag + " " + form, validated, expect, "OK" if validated == expect else "MISMATCH"))
        if validated != expect:
            FAILS.append("verdict %s %s" % (tag, form))

print("\n== R-005 table 2: id07_raw under the DOUBLESPEAK donor, at the selected layer")
for pat, tag, want in (("rah2p3_p_cb_*.json", "Llama dev", 0.0353),
                       ("rah2p3_p_lp_*.json", "Llama held-out", 0.00673),
                       ("rah2p3_q_cb_*.json", "Qwen3 dev", 0.3887),
                       ("rah2p3_q_lp_*.json", "Qwen3 held-out", 0.000401)):
    d = one(pat)
    assert d["donor_condition"] == "natural_doublespeak"
    rows = [r for r in d["grid"] if r["form"] == "id07_raw"]
    got = max(r["patched_option_mass_at_best"] for r in rows)
    check("%s id07_raw mass" % tag, got, want, tol=6e-4)
    # the held-out claim is "fails the gate at EVERY depth" -- check all five, not the best
    if "held-out" in tag:
        n_pass = sum(r["positive_control_ok"] for r in rows)
        print("     held-out gate: %d/%d depths pass  %s" % (n_pass, len(rows),
                                                             "OK" if n_pass == 0 else "MISMATCH"))
        if n_pass:
            FAILS.append("%s held-out gate" % tag)

print("\n== C-018: the collapse is real and the upper bound is NOT the selected-layer value")
d = one("rah2p3_q_lp_*.json")
rows = [r for r in d["grid"] if r["form"] == "id07_raw"]
sel = max(r["patched_option_mass_at_best"] for r in rows)
ub = max(pl["option_mass_mean"] for r in rows for pl in r["per_layer"])
print("  Qwen3 held-out id07_raw: selected-layer %.6g vs max-over-(R,L) %.6g  ratio %.1fx"
      % (sel, ub, ub / sel))
if not ub > 100 * sel:
    FAILS.append("C-018 upper-bound gap")
    print("  MISMATCH: C-018 claimed the upper bound is the misleading quantity")

print("\n%s" % ("FAILED: " + ", ".join(FAILS) if FAILS else "ALL CHECKS PASS"))
sys.exit(1 if FAILS else 0)
