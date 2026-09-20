#!/usr/bin/env python3
"""Is the pooled control family ONE null, or two families that must not be pooled? (R5, S-095)

The subspace verdict reads the candidate's rank in a POOLED family of random-subspace and
shuffled-label controls. That pooling is an assumption: if the two families differ in location, the
pooled rank is not a p-value. R5 tested it at 12 shuffled vs 22 random and got exact-permutation
p = 0.714. S-095 PREREGISTERED a re-test once group K raises the shuffled family, because a test that
passed at one n is not a licence at another.

Written and committed BEFORE group K's arms finished, so the procedure is fixed in advance rather
than chosen after seeing which answer it gives.

Reports, per split: each family's n / mean / sd / max, the observed difference in means, and a
two-sided permutation p -- EXACT by full enumeration when the number of splits is tractable, else
Monte-Carlo with its own floor reported. Also reports the candidate's rank WITHIN each family, since
R5's finding was that the shuffled family binds the margin even when the means agree.
"""
from __future__ import annotations
import argparse, glob, importlib.util, itertools, json, os, random, re, statistics as st

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_s = importlib.util.spec_from_file_location("rd", os.path.join(REPO, "scripts",
                                                               "dcs_csi_rederive_subspace.py"))
rd = importlib.util.module_from_spec(_s); _s.loader.exec_module(rd)

MAX_EXACT = 400000


def perm_p(a, b, seed=20260916, n_mc=200000):
    """Two-sided permutation test on the difference in means. Returns (p, floor, mode)."""
    pool = list(a) + list(b)
    k, n = len(a), len(pool)
    obs = abs(st.mean(a) - st.mean(b))

    def diff(idx):
        s = [pool[i] for i in idx]
        r = [pool[i] for i in range(n) if i not in idx]
        return abs(st.mean(s) - st.mean(r))

    total = 1
    for i in range(k):
        total = total * (n - i) // (i + 1)
    if total <= MAX_EXACT:
        hits = 0
        for comb in itertools.combinations(range(n), k):
            if diff(set(comb)) >= obs - 1e-15:
                hits += 1
        return hits / total, 1.0 / total, "exact(%d)" % total
    rng = random.Random(seed)
    idx = list(range(n))
    hits = 0
    for _ in range(n_mc):
        rng.shuffle(idx)
        if diff(set(idx[:k])) >= obs - 1e-15:
            hits += 1
    return (hits + 1) / (n_mc + 1), 1.0 / (n_mc + 1), "monte-carlo(%d)" % n_mc


def collect(prefix, split, expect, allow_short, candidate, skip):
    names = set()
    for d in glob.glob(os.path.join(rd.SB, prefix + "_KO_*")):
        m = re.match(r"^%s_(KO_(?:RAND|SHUF)\d+)_\d{8}_\d{6}_\d+$" % re.escape(prefix),
                     os.path.basename(d))
        if not m or m.group(1) in skip:
            continue
        try:
            n = sum(1 for _ in open(os.path.join(d, "results.jsonl"), encoding="utf-8"))
        except OSError:
            n = 0
        if n >= expect - allow_short:
            names.add(m.group(1))
    ctl = sorted(names)
    arms = ["KO", candidate] + ctl
    dirs = {a: rd.run_dir("%s_%s" % (prefix, a), expect, allow_short) for a in arms}
    assign = json.load(open(os.path.join(REPO, "data/boombness_prompts/dcs_ts116_domain_split.json"),
                            encoding="utf-8"))["assign"]
    vals = {a: rd.arm_values(d, split, assign) for a, d in dirs.items()}
    keys = set.intersection(*[set(v) for v in vals.values()])
    dm = {a: rd.domain_means(v, keys) for a, v in vals.items()}
    doms = sorted(dm["KO"])
    eff = {a: sum(dm[a][d] - dm["KO"][d] for d in doms) / len(doms) for a in [candidate] + ctl}
    return eff, ctl, len(keys), len(doms)


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
    ap.add_argument("--tag-prefix", required=True)
    ap.add_argument("--split", required=True, choices=("train", "validation"))
    ap.add_argument("--expect-n", type=int, required=True)
    ap.add_argument("--allow-short", type=int, default=3)
    ap.add_argument("--candidate", default="KO_AXIS")
    ap.add_argument("--skip", default="", help="comma list of control arms to exclude")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    skip = {x for x in a.skip.split(",") if x}
    eff, ctl, nkeys, ndom = collect(a.tag_prefix, a.split, a.expect_n, a.allow_short,
                                    a.candidate, skip)
    cand = eff[a.candidate]
    fam = {"shuffled": [c for c in ctl if "SHUF" in c], "random": [c for c in ctl if "RAND" in c]}
    out = {"schema": "dcs_csi_family_exchangeability/1", "tag_prefix": a.tag_prefix,
           "split": a.split, "n_keys": nkeys, "n_domains": ndom, "candidate": round(cand, 6),
           "families": {}}
    print("[exch] %s/%s  %d keys / %d domains  candidate %+.5f" % (a.tag_prefix, a.split, nkeys,
                                                                   ndom, cand))
    for nm, members in fam.items():
        if not members:
            continue
        v = [eff[c] for c in members]
        rank = 1 + sum(1 for x in v if x >= cand)
        out["families"][nm] = {"n": len(v), "mean": round(st.mean(v), 6),
                               "sd": round(st.pstdev(v), 6), "max": round(max(v), 6),
                               "candidate_rank": rank, "of": len(v) + 1,
                               "floor": round(1.0 / (len(v) + 1), 4),
                               "certifiable_at_0.05": (1.0 / (len(v) + 1)) <= 0.05}
        print("   %-9s n=%2d mean=%+.6f sd=%.6f max=%+.6f | cand rank %d of %d (floor %.4f)%s"
              % (nm, len(v), st.mean(v), st.pstdev(v), max(v), rank, len(v) + 1,
                 1.0 / (len(v) + 1), "" if (1.0 / (len(v) + 1)) <= 0.05 else "  FLOOR-LIMITED"))
    if len(fam["shuffled"]) and len(fam["random"]):
        sh = [eff[c] for c in fam["shuffled"]]
        rn = [eff[c] for c in fam["random"]]
        p, floor, mode = perm_p(sh, rn)
        d = st.mean(sh) - st.mean(rn)
        sd_ratio = (st.pstdev(sh) / st.pstdev(rn)) if st.pstdev(rn) else float("nan")
        out["exchangeability"] = {"mean_diff": round(d, 6), "p_two_sided": p,
                                 "p_floor": floor, "test_mode": mode,
                                 "sd_ratio_shuffled_over_random": round(sd_ratio, 3),
                                 "poolable_at_0.05": p > 0.05}
        print("   shuffled-random mean diff = %+.6f   p = %.4f (%s, floor %.2e)"
              % (d, p, mode, floor))
        print("   sd ratio shuffled/random = %.2f" % sd_ratio)
        print("   VERDICT: families are %s at alpha=0.05"
              % ("POOLABLE (not separated)" if p > 0.05 else "NOT POOLABLE -- the pooled rank is "
                 "not a single null and must be withdrawn"))
    if a.out:
        _atomic_json_dump(out, a.out, indent=1)
        print("wrote", os.path.relpath(a.out, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
