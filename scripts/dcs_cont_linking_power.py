#!/usr/bin/env python3
"""How many DOMAINS does the installation->refusal linking test need? (§42 Phase 2, §43)

WHY THIS FILE EXISTS. `reports/DCS_CONT_NEXT_BANK_SPECIFICATION.md` and the mandate's §43
resource-allocation both turn on ONE quantity: the number of domains a per-domain correlation
linking test needs to stop being underpowered. The spec asserts it -- "~240 domains would put
a rho ~= 0.18 test at 80% power; the present 67 reaches rho ~= 0.34" -- and the claim table
carries "rho 0.176 against an MDE of 0.337" (CONT-ENTRY 124). Those numbers gate the single
most expensive decision left in the phase (build a larger bank, at linear GPU cost), and until
now they existed only as prose. This makes them a committed, reproducible calculation.

It does NOT read the bank, any run, or TEST. It is pure power arithmetic over the DOMAIN as
the independence unit -- so it cannot leak TEST, cannot pool codewords, and cannot manufacture
a result from the withdrawn A16/A17 artifacts. It answers only "what N is required", never
"what did we observe" beyond quoting the already-published rho=0.176 to locate it on the curve.

WHAT THE LINKING TEST IS. A Pearson correlation between a per-domain installation measure and a
per-domain behavioural measure (refusal, or de-refusal), one (x, y) pair per domain, n = number
of domains. The estimator and its unit are fixed by the phase (CONT-ENTRY 124); this file does
not choose them. Fisher's z-transform gives the standard analytic power for exactly this test,
and a Monte-Carlo draw from a bivariate normal cross-checks it so the number is not just a
formula (repo discipline: every reported number re-derived, and --selftest turns a check RED).

  N(rho) = ((z_{1-a/2} + z_{power}) / atanh(rho))^2 + 3      [Fisher z, two-sided]
  MDE(N) = tanh( (z_{1-a/2} + z_{power}) / sqrt(N - 3) )

usage:
  <conda poc_stage2>/python scripts/dcs_cont_linking_power.py
  <conda poc_stage2>/python scripts/dcs_cont_linking_power.py --selftest
"""
from __future__ import annotations
import argparse, json, math, os, sys
import numpy as np
from scipy import stats

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALPHA = 0.05
POWER = 0.80

# The DOMAIN counts this phase actually has, named so the calculation is anchored to the bank
# rather than to a round number. 116 declared - 23 TEST - 3 excluded = 90 usable; the knockout
# arms exist on 67 of those (the shared never-refused stratum uses 67). CONT-ENTRY 124 / NEXT_BANK.
N_KNOCKOUT = 67          # domains where ko/ctrl arms exist -- where the linking test is run today
N_USABLE = 90            # train+val usable domains (no TEST) -- the ceiling without a new bank
RHO_OBSERVED = 0.176     # the published linking-test rho (CONT-ENTRY 124); quoted, not re-fit


def n_for_rho(rho, alpha=ALPHA, power=POWER):
    """Domains needed to detect true |rho| at `power`, two-sided, via Fisher z."""
    if not (0 < abs(rho) < 1):
        raise ValueError("rho must be in (0,1); got %r" % (rho,))
    zc = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
    return (zc / math.atanh(abs(rho))) ** 2 + 3


def mde(n, alpha=ALPHA, power=POWER):
    """Smallest |rho| detectable at `power` with n domains (n > 3), two-sided."""
    if n <= 3:
        raise ValueError("n must exceed 3 for a Fisher-z interval; got %r" % (n,))
    zc = stats.norm.ppf(1 - alpha / 2) + stats.norm.ppf(power)
    return math.tanh(zc / math.sqrt(n - 3))


def analytic_power(rho, n, alpha=ALPHA):
    """Power to reject rho=0 at sample rho's true value, two-sided Fisher z."""
    if n <= 3:
        raise ValueError("n must exceed 3; got %r" % (n,))
    se = 1.0 / math.sqrt(n - 3)
    zc = stats.norm.ppf(1 - alpha / 2)
    zt = math.atanh(abs(rho)) / se
    return stats.norm.cdf(zt - zc) + stats.norm.cdf(-zt - zc)


def mc_power(rho, n, alpha=ALPHA, n_sim=20000, seed=20260913):
    """Monte-Carlo cross-check: draw n domain pairs from a bivariate normal with the given
    population rho, run the exact Pearson test, and report the rejection rate. This is the
    number the analytic formula must match; a large gap means the analytic column is wrong."""
    rng = np.random.default_rng(seed)
    cov = np.array([[1.0, rho], [rho, 1.0]])
    L = np.linalg.cholesky(cov)
    rej = 0
    for _ in range(n_sim):
        xy = rng.standard_normal((n, 2)) @ L.T
        _, p = stats.pearsonr(xy[:, 0], xy[:, 1])
        rej += (p < alpha)
    return rej / n_sim


def report():
    zc = stats.norm.ppf(1 - ALPHA / 2) + stats.norm.ppf(POWER)
    out = {"schema": "dcs_cont_linking_power/1", "unit": "DOMAIN", "test": "Pearson r, Fisher z",
           "alpha": ALPHA, "power_target": POWER, "z_crit_sum": round(zc, 5),
           "domain_counts": {"knockout_arms": N_KNOCKOUT, "usable_no_test": N_USABLE,
                             "declared_total": 116, "test_withheld": 23, "excluded": 3},
           "mde_at_current_N": {}, "n_needed_for_rho": {}, "observed": {}}

    print("=== installation->behaviour linking test: domain-level power (Fisher z) ===")
    print("alpha=%.2f two-sided, power=%.2f, unit=DOMAIN\n" % (ALPHA, POWER))

    print("MDE (smallest detectable rho) at the domain counts we have:")
    for label, n in (("knockout arms (today)", N_KNOCKOUT), ("usable, no TEST", N_USABLE)):
        m = mde(n)
        out["mde_at_current_N"]["N=%d" % n] = round(m, 4)
        print("  N=%3d  (%-22s)  MDE = %.4f" % (n, label, m))
    print()

    print("Domains needed for 80% power, by true rho  (analytic vs Monte-Carlo at that N):")
    for rho in (0.15, 0.176, 0.18, 0.20, 0.25, 0.30, 0.337, 0.40):
        n = n_for_rho(rho)
        n_up = int(math.ceil(n))
        pw = analytic_power(rho, n_up)
        pw_mc = mc_power(rho, n_up)
        out["n_needed_for_rho"]["%.3f" % rho] = {"n": n_up, "power_analytic": round(pw, 4),
                                                 "power_mc": round(pw_mc, 4)}
        flag = ""
        if abs(rho - RHO_OBSERVED) < 1e-6:
            flag = "  <- the OBSERVED linking rho (CONT-ENTRY 124)"
        print("  rho=%.3f -> N=%3d   power@N: analytic %.3f / MC %.3f%s"
              % (rho, n_up, pw, pw_mc, flag))
    print()

    # Locate the observed rho on today's design.
    pw_now = analytic_power(RHO_OBSERVED, N_KNOCKOUT)
    pw_now_mc = mc_power(RHO_OBSERVED, N_KNOCKOUT)
    m67 = mde(N_KNOCKOUT)
    out["observed"] = {"rho": RHO_OBSERVED, "N_today": N_KNOCKOUT,
                       "power_today_analytic": round(pw_now, 4),
                       "power_today_mc": round(pw_now_mc, 4),
                       "mde_today": round(m67, 4),
                       "underpowered": bool(RHO_OBSERVED < m67),
                       "n_needed_for_observed_rho": int(math.ceil(n_for_rho(RHO_OBSERVED)))}
    print("The observed linking test today:")
    print("  rho=%.3f at N=%d: power = %.3f (MC %.3f); MDE here = %.3f -> observed is %s the MDE."
          % (RHO_OBSERVED, N_KNOCKOUT, pw_now, pw_now_mc, m67,
             "BELOW" if RHO_OBSERVED < m67 else "above"))
    print("  to make THIS rho detectable at 80%% power would need N=%d domains."
          % out["observed"]["n_needed_for_observed_rho"])
    return out


def selftest():
    """Every check binds to a value and one mutation drives it RED (repo discipline)."""
    # 1. spec cross-check: the prose numbers must fall out of the formula.
    n18 = n_for_rho(0.18)
    assert 235 <= n18 <= 245, "rho=0.18 should need ~240 domains, got %.1f" % n18
    m67 = mde(67)
    assert abs(m67 - 0.337) < 0.003, "MDE at N=67 should be ~0.337, got %.4f" % m67
    # 2. monotonicity: smaller effects need more domains; more domains detect smaller effects.
    assert n_for_rho(0.15) > n_for_rho(0.30)
    assert mde(90) < mde(67)
    # 3. analytic power must equal a definitional recompute, and match MC within noise.
    for rho, n in ((0.18, 240), (0.30, 90), (0.176, 67)):
        a = analytic_power(rho, n)
        b = mc_power(rho, n, n_sim=40000)
        assert abs(a - b) < 0.02, "analytic %.3f vs MC %.3f at rho=%.3f N=%d" % (a, b, rho, n)
    # a design at its own N_for_rho must land at ~0.80 power by construction.
    assert abs(analytic_power(0.25, int(math.ceil(n_for_rho(0.25)))) - 0.80) < 0.01
    # 4. the RED demonstration: a wrong unit (rows, ~670, not domains) would call the test
    #    powered. Show that swapping N=67 for N=670 flips the underpowered verdict, so the
    #    unit is load-bearing and the guard would catch its loss.
    assert RHO_OBSERVED < mde(67), "observed rho must be below the domain-unit MDE"
    assert RHO_OBSERVED > mde(670), "at the WRONG (row) unit it would look powered -- unit matters"
    # 5. guards raise rather than return nonsense.
    for bad in (0.0, 1.0, -1.0, 1.5):   # abs(rho) in (0,1); a real negative rho is fine
        try:
            n_for_rho(bad); raise SystemExit("FAIL: n_for_rho accepted rho=%r" % (bad,))
        except ValueError:
            pass
    for bad in (3, 2, 0):
        try:
            mde(bad); raise SystemExit("FAIL: mde accepted n=%r" % (bad,))
        except ValueError:
            pass
    print("dcs_cont_linking_power self-test OK: "
          "N(0.18)=%.0f, MDE(67)=%.4f, MDE(90)=%.4f, observed rho=%.3f is below MDE(67)"
          % (n18, m67, mde(90), RHO_OBSERVED))


def _atomic_json_dump(obj, path, **kw):
    """Atomic, VERIFIED JSON write. Fix for sprint entry S-124.

    Replaces `json.dump(x, open(p, "w"), ...)`, whose handle is never closed: `open` truncates the
    destination immediately and the buffered bytes are flushed only in the GC finaliser, where
    CPython PRINTS and then SWALLOWS an EDQUOT. A full quota therefore produced a 0-byte file at a
    real artifact name, with "wrote <path>" on stdout and exit status 0 -- indistinguishable from a
    finished report. Temp file + fsync + size check + re-parse + os.replace makes the write ATOMIC
    as well as checked: a half-written file never appears at the real name, and whatever was there
    before survives a failure. On any error this RAISES, naming the path and the byte count.
    """
    import tempfile                        # local: keeps this helper drop-in and import-order-free
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_atomic_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, **kw)
            fh.flush()
            os.fsync(fh.fileno())          # EDQUOT surfaces HERE, not in a GC finaliser
        n = os.path.getsize(tmp)
        if n == 0:
            raise OSError("temp file is 0 bytes after a flush+fsync that reported success")
        with open(tmp, "r", encoding="utf-8") as fh:
            json.load(fh)                  # a truncated write does not re-parse
        try:
            mode = os.stat(path).st_mode & 0o7777   # keep the artifact's existing permissions:
        except OSError:                             # mkstemp makes the temp file 0600 and
            mode = 0o644                            # os.replace would carry that onto the report
        os.chmod(tmp, mode)
        os.replace(tmp, path)              # atomic within the directory
    except Exception as e:
        try:
            n = os.path.getsize(tmp)
        except OSError:
            n = -1
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise OSError("atomic_json_dump FAILED for %s -- %d bytes reached the temp file; the "
                      "destination is UNCHANGED (never truncated). Cause: %r" % (path, n, e)) from e
    return os.path.getsize(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", default="reports/DCS_CONT_LINKING_POWER.json")
    a = ap.parse_args()
    if a.selftest:
        selftest(); return 0
    out = report()
    p = os.path.join(REPO, a.out)
    _atomic_json_dump(out, p, indent=1)
    print("\nwrote %s" % os.path.relpath(p, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
