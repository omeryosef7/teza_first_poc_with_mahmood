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

    systematic = p < 0.05
    verdict = (f"SYSTEMATIC OFFSET {d_asr:+.5f} (p={p:.4f})" if systematic
               else f"NO SYSTEMATIC OFFSET (p={p:.4f}); |drift| <= {abs(d_asr):.5f} is noise")
    print(f"\nVERDICT: {verdict}")
    print(f"  vs judge_session_drift.json 0.00202 and R-049 0.0158 "
          f"-- this estimate rests on {f} flips over {tot['n']} rows")
    if systematic:
        print(f"  ⚠ PR-028b's re-judge was therefore NECESSARY: mixing sessions would have biased "
              f"the primary by (5/8)*{d_asr:+.5f} = {5/8*d_asr:+.5f} on a -0.0391 effect.")

    os.makedirs(os.path.join(REPO, os.path.dirname(a.out)), exist_ok=True)
    json.dump({"per_arm": per_arm, "pooled": {**tot, "net": net, "d_asr": d_asr,
               "binom_p": p, "systematic": systematic}, "verdict": verdict},
              open(os.path.join(REPO, a.out), "w"), indent=1)
    print(f"\n-> {a.out}")


if __name__ == "__main__":
    main()
