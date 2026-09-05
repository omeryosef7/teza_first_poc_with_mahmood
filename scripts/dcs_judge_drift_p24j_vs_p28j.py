#!/usr/bin/env python3
"""DCS-PR-028b bonus: measure judge-session drift on THIS bank, from the re-judge.

⚠ WRITTEN BEFORE THE DATA. Frozen while 852000-852004 were generating and before any p28j_ arm
existed, so the analysis cannot be tuned to its own answer.

WHY IT IS WORTH ANYTHING. Two estimates of judge-session drift disagree by 8x:
  * judge_session_drift.json  0.0020   -- AdvBench, 13 sessions, ASR 0.065
  * DCS-R-049                 0.0158   -- this bank, ONE re-judge of ONE arm, net +6 / 380
On the PR-028 primary that spread is the difference between a 3% and a 25% bias. PR-028b re-judges
five arms that already carry p24j labels, so five pairs of labels exist over BYTE-IDENTICAL
completions -- 5 x 1160 rows, the same bank and the same ASR range as the primary.

⛔ BYTE-IDENTITY IS CHECKED, NOT ASSUMED. Drift is only drift if the text did not change;
`completion_sha256_16` must match per prompt_id, and rows where it does not are EXCLUDED and
counted, never silently averaged in. (A partial or re-generated arm would otherwise read as judge
noise -- judge_session_drift.json records that exact mistake in its own coverage_rule_history.)

THE TEST THAT MATTERS IS NOT "HOW MANY FLIPPED". It is whether the NET is distinguishable from
symmetric noise, because only a systematic offset biases the primary. Under the null that flips are
symmetric, the number flipping one way is Binomial(n_flips, 0.5) -- an exact two-sided binomial
test. R-049's net +6 on 18 flips is 1.41 sd, i.e. NOT established as an offset; this asks the same
question with ~15x the flips.
"""
import argparse, glob, importlib.util, json, math, os, sys
import statistics as st

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location("cdt", os.path.join(REPO, "scripts/cds_domain_test.py"))
cdt = importlib.util.module_from_spec(_s); _s.loader.exec_module(cdt)


def newest(pat):
    d = sorted(x for x in glob.glob(os.path.join(REPO, pat)) if os.path.isfile(x + "/DONE.json"))
    return d[-1] if d else None


def binom_two_sided(k, n, p=0.5):
    """Exact two-sided binomial test by the method of small probabilities."""
    if n == 0:
        return float("nan")
    def pmf(i):
        return math.comb(n, i) * p ** i * (1 - p) ** (n - i)
    obs = pmf(k)
    return min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= obs * (1 + 1e-9)))


def _t_sf_local(t, df):
    """Upper-tail P(T > t). scipy when available; otherwise a continued-fraction incomplete beta."""
    try:
        from scipy import stats
        return float(stats.t.sf(t, df))
    except Exception:
        pass
    x = df / (df + t * t)
    a, b = df / 2.0, 0.5
    if x <= 0: ib = 0.0
    elif x >= 1: ib = 1.0
    else:
        lbeta = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
        front = math.exp(math.log(x) * a + math.log(1 - x) * b - lbeta) / a
        f, c, d = 1.0, 1.0, 0.0
        for i in range(300):
            m_ = i // 2
            if i == 0: num = 1.0
            elif i % 2 == 0: num = (m_ * (b - m_) * x) / ((a + 2*m_ - 1) * (a + 2*m_))
            else: num = -((a + m_) * (a + b + m_) * x) / ((a + 2*m_) * (a + 2*m_ + 1))
            d = 1.0 + num * d; d = 1e-30 if abs(d) < 1e-30 else d; d = 1.0 / d
            c = 1.0 + num / c; c = 1e-30 if abs(c) < 1e-30 else c
            f *= c * d
            if abs(1 - c * d) < 1e-10: break
        ib = front * (f - 1)
    return 0.5 * ib if t > 0 else 1.0 - 0.5 * ib


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+",
                    default=["dcsp24_base", "dcsp24_demo", "dcsp24_d1", "dcsp24_d2", "dcsp24_d3"])
    ap.add_argument("--old-prefix", default="p24j")
    ap.add_argument("--new-prefix", default="p28j")
    ap.add_argument("--out", default="outputs/boombness/dcs_analysis/dcs_judge_drift_p24j_p28j.json")
    a = ap.parse_args()

    per_arm, tot = [], {"n": 0, "flips": 0, "up": 0, "excluded_sha": 0,
                        "ref_flips": 0, "ref_up": 0}
    for tag in a.arms:
        od, nd = newest(f"outputs/boombness/judge/{a.old_prefix}_{tag}_*"), \
                 newest(f"outputs/boombness/judge/{a.new_prefix}_{tag}_*")
        if not od or not nd:
            print(f"  SKIP {tag}: "
                  f"{'old missing ' if not od else ''}{'new missing' if not nd else ''}")
            continue
        old, new = cdt.load_arm(od), cdt.load_arm(nd)
        ids = sorted(set(old) & set(new))
        # BYTE-IDENTITY GATE
        same = [i for i in ids if old[i]["sha"] == new[i]["sha"]]
        excluded = len(ids) - len(same)
        up = sum(1 for i in same if new[i]["attack"] and not old[i]["attack"])
        down = sum(1 for i in same if old[i]["attack"] and not new[i]["attack"])
        rup = sum(1 for i in same if new[i]["refused"] and not old[i]["refused"])
        rdown = sum(1 for i in same if old[i]["refused"] and not new[i]["refused"])
        n = len(same)
        asr_o = sum(old[i]["attack"] for i in same) / n if n else float("nan")
        asr_n = sum(new[i]["attack"] for i in same) / n if n else float("nan")
        per_arm.append({"arm": tag, "n": n, "excluded_sha_mismatch": excluded,
                        "asr_old": asr_o, "asr_new": asr_n, "d_asr": asr_n - asr_o,
                        "up": up, "down": down, "flips": up + down, "net": up - down,
                        "refused_up": rup, "refused_down": rdown})
        tot["n"] += n; tot["flips"] += up + down; tot["up"] += up
        tot["excluded_sha"] += excluded
        tot["ref_flips"] += rup + rdown; tot["ref_up"] += rup
        print(f"  {tag:14s} n={n:5d} excl={excluded:3d}  ASR {asr_o:.4f} -> {asr_n:.4f} "
              f"({asr_n-asr_o:+.4f})  flips={up+down:4d} net={up-down:+4d}  "
              f"refused net={rup-rdown:+4d}")

    if not per_arm:
        sys.exit("no arm has labels in BOTH sessions yet -- run judge_pr028_all10.sh first")

    f, u = tot["flips"], tot["up"]
    net = 2 * u - f
    p = binom_two_sided(u, f)
    d_asr = net / tot["n"] if tot["n"] else float("nan")
    print(f"\nPOOLED over {len(per_arm)} arms, {tot['n']} byte-identical rows "
          f"({tot['excluded_sha']} excluded for sha mismatch)")
    print(f"  flips {f}  ({u} up, {f-u} down)  net {net:+d}  => drift in ASR = {d_asr:+.5f}")
    print(f"  exact two-sided binomial vs symmetric noise: p = {p:.4f}")
    sd = math.sqrt(f) if f else float("nan")
    print(f"  net/sd = {net/sd:+.2f} (sd = sqrt(flips) = {sd:.2f})")
    rf, ru = tot["ref_flips"], tot["ref_up"]
    print(f"  refusal label: {rf} flips, net {2*ru-rf:+d}"
          + ("   ⚠ C-023 assumed refusal labels are stable" if rf else "   ✅ (C-023 holds)"))

    # ⛔ THE PREREGISTERED BINOMIAL IS AT THE WRONG UNIT, and this is added at readout rather than
    # quietly swapped: it is REPORTED ALONGSIDE, never replaced. 5800 rows are not 5800 independent
    # replicates of a SESSION offset -- there are five arms, and rows cluster within them (this
    # phase measured domain ICC 0.089-0.112). The session offset is an arm-level quantity, so the
    # arm is the replicate. C-016/R-016 is this repository's standing record of exactly this error;
    # R-067 hit it again from a new direction. Note the correction moves AWAY from significance,
    # so it is not a search for a better p.
    arm_vals = [r["d_asr"] for r in per_arm]
    if len(arm_vals) > 1:
        am = st.fmean(arm_vals); asd = st.stdev(arm_vals)
        ase = asd / math.sqrt(len(arm_vals))
        at = am / ase if ase > 0 else float("nan")
        ap = 2 * _t_sf_local(abs(at), len(arm_vals) - 1) if ase > 0 else float("nan")
        crit = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
                6: 2.447, 7: 2.365}.get(len(arm_vals) - 1, 1.96)
        lo, hi = am - crit * ase, am + crit * ase
        n_neg = sum(1 for v in arm_vals if v < 0)
        print(f"\n  ARM-LEVEL (the arm is the replicate; this is the unit the estimand lives at)")
        print(f"    mean {am:+.5f}  sd {asd:.5f}  SE {ase:.5f}  t({len(arm_vals)-1}) = {at:+.2f}  "
              f"p = {ap:.4f}")
        print(f"    95% CI [{lo:+.5f}, {hi:+.5f}]   sign test: {n_neg}/{len(arm_vals)} negative "
              f"(floor {2/2**len(arm_vals):.4f})")
        arm_level = {"mean": am, "sd": asd, "se": ase, "t": at, "p": ap, "ci": [lo, hi],
                     "n_negative": n_neg, "k_arms": len(arm_vals)}
    else:
        arm_level = None
        print("\n  ARM-LEVEL: needs >=2 arms")

    # THE VERDICT COMES FROM THE ARM-LEVEL TEST when it is available.
    systematic = (arm_level["p"] < 0.05) if arm_level else (p < 0.05)
    _pp = arm_level["p"] if arm_level else p
    verdict = (f"SYSTEMATIC OFFSET {d_asr:+.5f} (arm-level p={_pp:.4f})" if systematic
               else f"NO ESTABLISHED OFFSET at the arm level (p={_pp:.4f}); point estimate "
                    f"{d_asr:+.5f}, CI spans zero. Row-level binomial p={p:.4f} is at the WRONG "
                    f"UNIT and is reported for the record only.")
    print(f"\nVERDICT: {verdict}")
    print(f"  vs judge_session_drift.json 0.00202 and R-049 0.0158 "
          f"-- this estimate rests on {f} flips over {tot['n']} rows")
    if systematic:
        print(f"  ⚠ PR-028b's re-judge was therefore NECESSARY: mixing sessions would have biased "
              f"the primary by (5/8)*{d_asr:+.5f} = {5/8*d_asr:+.5f} on a -0.0391 effect.")

    os.makedirs(os.path.join(REPO, os.path.dirname(a.out)), exist_ok=True)
    json.dump({"per_arm": per_arm, "pooled": {**tot, "net": net, "d_asr": d_asr,
               "binom_p": p, "systematic": systematic},
               "arm_level": arm_level, "verdict": verdict},
              open(os.path.join(REPO, a.out), "w"), indent=1)
    print(f"\n-> {a.out}")


if __name__ == "__main__":
    main()
