"""W1.1 -- a DOMAIN-CLUSTERED bootstrap over the AtP screen's head ranking.

WHAT THIS CLOSES. S-181 reported a ranking with no uncertainty attached, and S-185 repeated the
point: "a trustworthy estimator of an unstable quantity is still unstable". `S[h]` is a single
summed number per head, so nothing in the screen distinguishes

    h19 leads in 60 of 67 domains        from        h19 leads in 12, with three outliers carrying it

and those two support very different claims. The statistical unit is the DOMAIN (rule 3.3), so the
resampling unit is the domain -- not the row, which would treat ten rows of one domain as ten
independent observations and shrink every interval by roughly sqrt(10).

WHAT IT REPORTS, and the first two need no distributional assumption at all:
  * in how many domains each head is individually the most negative -- a plain count;
  * the per-domain sign consistency of the leader;
  * a percentile CI on S[h] and on the GAP between the top two heads, over B domain resamples;
  * P(h ranks first), which is the number S-181 was missing.

CANNOT ANSWER, stated in advance: a bootstrap describes the sampling variability of THESE 67 domains
under resampling. It does not extend to the held-out 23, and it cannot repair a biased estimator --
if AtP is systematically wrong in some domain, resampling that domain returns the same wrong value.
R14 measured exactly that: 3 of 40 domains fail the true-patch gate individually.
"""
import argparse, json, os, sys, random, statistics, tempfile

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "scripts"))


def atomic_write_json(path, obj):
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_atomic_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=False); fh.write("\n")
            fh.flush(); os.fsync(fh.fileno())
        if os.path.getsize(tmp) == 0:
            raise OSError("temp file is 0 bytes after a successful flush+fsync")
        with open(tmp, "r", encoding="utf-8") as fh:
            json.load(fh)
        try:
            mode = os.stat(path).st_mode & 0o7777
        except OSError:
            mode = 0o644
        os.chmod(tmp, mode); os.replace(tmp, path)
        try:
            dfd = os.open(d, os.O_RDONLY)
            try: os.fsync(dfd)
            finally: os.close(dfd)
        except OSError:
            pass
    except Exception as e:
        try: nb = os.path.getsize(tmp)
        except OSError: nb = -1
        try: os.unlink(tmp)
        except OSError: pass
        raise OSError("atomic_write_json FAILED for %s -- %d bytes reached the temp file; the "
                      "destination is UNCHANGED. Cause: %r" % (path, nb, e)) from e
    return os.path.getsize(path)


def pct(xs, q):
    ys = sorted(xs)
    if not ys:
        return None
    k = (len(ys) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(ys) - 1)
    return ys[lo] + (ys[hi] - ys[lo]) * (k - lo)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen", required=True)
    ap.add_argument("--B", type=int, default=10000, help="domain resamples")
    ap.add_argument("--seed", type=int, default=20260921)
    ap.add_argument("--ci", type=float, default=0.95)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    scr = json.load(open(a.screen))
    if "S_by_domain_head" not in scr:
        sys.exit("REFUSING: this screen predates W1.1 and carries no per-domain terms; they cannot "
                 "be recovered from the sum. Re-run the screen.")
    per_dom = {d: [float(x) for x in v] for d, v in scr["S_by_domain_head"].items()}
    doms = sorted(per_dom)
    n_heads = len(next(iter(per_dom.values())))
    print("[boot] SIZE domains = %d | heads = %d | B = %d | seed = %d"
          % (len(doms), n_heads, a.B, a.seed))
    if len(doms) < 2:
        sys.exit("VACUOUS: a bootstrap over fewer than 2 domains is not a bootstrap")

    # THE PER-DOMAIN TERMS MUST RECONSTRUCT THE SCREEN'S OWN S[h], OR ONE OF THEM IS WRONG.
    # This is the whole reason to check rather than trust: the accumulation is new code, and a
    # ranking built on terms that do not sum to the published statistic would be a silent fork.
    recon = [sum(per_dom[d][h] for d in doms) for h in range(n_heads)]
    pub = [float(scr["S_signed_by_head"][str(h)]) for h in range(n_heads)]
    worst = max(abs(recon[h] - pub[h]) for h in range(n_heads))
    rel = worst / max(abs(x) for x in pub)
    print("[boot] reconstruction vs published S[h]: worst abs diff %.3e (rel %.3e)" % (worst, rel))
    if rel > 1e-6:
        sys.exit("REFUSING: per-domain terms do not reconstruct the published S[h] (rel %.3e)" % rel)

    # --- assumption-free counts -----------------------------------------------------------
    leader_count = {h: 0 for h in range(n_heads)}
    for d in doms:
        leader_count[min(range(n_heads), key=lambda h: per_dom[d][h])] += 1
    order = sorted(range(n_heads), key=lambda h: pub[h])
    h1, h2 = order[0], order[1]
    neg_dom = sum(1 for d in doms if per_dom[d][h1] < 0)

    # --- domain-clustered bootstrap -------------------------------------------------------
    rng = random.Random(a.seed)
    n = len(doms)
    boot_S = {h: [] for h in range(n_heads)}
    first_count = {h: 0 for h in range(n_heads)}
    gaps = []
    for _ in range(a.B):
        pick = [doms[rng.randrange(n)] for _ in range(n)]
        tot = [0.0] * n_heads
        for d in pick:
            v = per_dom[d]
            for h in range(n_heads):
                tot[h] += v[h]
        for h in range(n_heads):
            boot_S[h].append(tot[h])
        first_count[min(range(n_heads), key=lambda h: tot[h])] += 1
        gaps.append(tot[h2] - tot[h1])          # > 0 means h1 is still ahead (more negative)

    lo_q, hi_q = (1 - a.ci) / 2, 1 - (1 - a.ci) / 2
    out = {
        "schema": "dcs_csi_head_atp_bootstrap/1",
        "screen": a.screen, "split": scr.get("split"), "band": scr.get("band"),
        "codeword": scr.get("codeword"), "concept": scr.get("concept"),
        "n_domains": len(doms), "n_heads": n_heads, "B": a.B, "seed": a.seed, "ci": a.ci,
        "resampling_unit": "DOMAIN (rule 3.3); resampling rows would shrink every interval by ~sqrt(10)",
        "reconstruction_worst_abs_diff": worst,
        "point_top5": [{"head": h, "S": round(pub[h], 6)} for h in order[:5]],
        "leader_domain_counts": {str(h): leader_count[h] for h in range(n_heads) if leader_count[h]},
        "top_head": h1, "runner_up": h2,
        "top_head_leads_in_n_domains": leader_count[h1],
        "top_head_negative_in_n_domains": neg_dom,
        "P_rank1": {str(h): round(first_count[h] / a.B, 4) for h in range(n_heads) if first_count[h]},
        "S_CI": {str(h): [round(pct(boot_S[h], lo_q), 6), round(pct(boot_S[h], hi_q), 6)]
                 for h in order[:5]},
        "gap_top1_minus_top2": {
            "point": round(pub[h2] - pub[h1], 6),
            "CI": [round(pct(gaps, lo_q), 6), round(pct(gaps, hi_q), 6)],
            "P_gap_positive": round(sum(1 for g in gaps if g > 0) / a.B, 4),
            "meaning": "positive = head %d stays ahead of head %d under domain resampling" % (h1, h2),
        },
        "CANNOT_ANSWER": ("a bootstrap describes resampling variability of THESE domains. It does not "
                          "extend to the held-out 23 and cannot repair a biased estimator -- R14 found "
                          "3 of 40 domains failing the true-patch gate individually."),
    }
    n_b = atomic_write_json(a.out, out)
    print("[boot] wrote+verified %s (%d bytes)" % (a.out, n_b))
    print("[boot] top head h%d: leads in %d/%d domains | negative in %d/%d | P(rank1) = %.4f"
          % (h1, leader_count[h1], len(doms), neg_dom, len(doms), first_count[h1] / a.B))
    print("[boot] S[h%d] %.1f  CI [%.1f, %.1f]" % (h1, pub[h1], *out["S_CI"][str(h1)]))
    print("[boot] gap h%d - h%d = %.1f  CI [%.1f, %.1f]  P(>0) = %.4f"
          % (h2, h1, out["gap_top1_minus_top2"]["point"], *out["gap_top1_minus_top2"]["CI"],
             out["gap_top1_minus_top2"]["P_gap_positive"]))


if __name__ == "__main__":
    main()
