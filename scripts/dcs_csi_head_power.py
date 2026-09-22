"""§22 POWER for the HEAD-LEVEL rank test: what is the smallest effect PR-CSI-010 could have seen?

WHY THIS AND NOT `dcs_csi_power.py`. That script analyses the BEHAVIOURAL native-refusal endpoint of
the patch test -- D=90 domains, R=2 rows, a within-domain rate in {0, 0.5, 1}. PR-CSI-010's endpoint
is `y_install` on 23 held-out domains at 10 rows each, adjudicated by a RANK of one candidate among
20 controls. Different endpoint, different unit count, different test. Nothing was reusable.

WHAT IT ANSWERS. §6's CANNOT ANSWER branch includes *"the split is underpowered for head-sized
effects"*. That branch was written as a worry with no number attached. This computes the number:
the minimum-detectable effect at 80% power for the exact test that was run.

THE TEST'S OWN CEILING COMES FIRST. With 20 controls the attainable floor is 1/21 = 0.047619, so
ONLY rank 1 certifies at alpha = 0.05 -- rank 2 gives 0.095 and cannot pass however large the effect.
"Power" here therefore means P(candidate ranks strictly first of 21), and no amount of effect buys a
second chance.

⛔ WHAT THE NOISE MODEL ASSUMES, STATED BECAUSE IT IS THE WEAK POINT. The null spread is taken from
the 20 control arms' own E values. That spread conflates TWO sources: domain sampling noise, and
genuine arm-to-arm heterogeneity between different random 8-head sets. Treating the combination as
"noise" is the conservative choice for an MDE (a wider null makes detection harder), but it is NOT a
clean estimate of domain sampling error alone, and this analysis cannot separate them -- doing so
would need repeated draws of the SAME head set, which no arm provides.
"""
import argparse, glob, importlib.util, json, os, random, statistics, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return m


lpm = _load("lpm", os.path.join(REPO, "scripts", "dcs_cont_layerpos_map.py"))
rederive = _load("rederive", os.path.join(REPO, "scripts", "dcs_csi_rederive_patch.py"))


def atomic_write_json(path, obj):
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_atomic_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2); fh.write("\n"); fh.flush(); os.fsync(fh.fileno())
        if os.path.getsize(tmp) == 0:
            raise OSError("0 bytes after flush+fsync")
        json.load(open(tmp))
        os.chmod(tmp, 0o644); os.replace(tmp, path)
        try:
            dfd = os.open(d, os.O_RDONLY)
            try: os.fsync(dfd)
            finally: os.close(dfd)
        except OSError:
            pass
    except Exception as e:
        try: os.unlink(tmp)
        except OSError: pass
        raise OSError("atomic_write_json FAILED for %s: %r" % (path, e)) from e
    return os.path.getsize(path)


def by_domain(run_dir):
    inst, _n, _k = lpm.load_installation(run_dir)
    per = {}
    for (dom, _slot), p in inst.items():
        per.setdefault(dom, []).append(float(p))
    return {d: statistics.fmean(v) for d, v in per.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--tag-prefix", required=True)
    ap.add_argument("--split", required=True, choices=("train", "validation"))
    ap.add_argument("--expect-n", type=int, required=True)
    ap.add_argument("--require-slurm-job", default=None)
    ap.add_argument("--B", type=int, default=20000, help="simulations per effect size")
    ap.add_argument("--seed", type=int, default=20260922)
    ap.add_argument("--target-power", type=float, default=0.80)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    pr = json.load(open(a.prereg))
    cprefix = pr.get("control_prefix", "HD_RAND")
    controls = sorted(k for k in pr["head_sets"] if k.startswith(cprefix))
    if not controls:
        sys.exit("REFUSING: control_prefix %r matches no head set" % cprefix)
    arms = ["HD_BASE", "HD_KO", "HD_TOPK"] + controls
    jobs = a.require_slurm_job.split(",") if a.require_slurm_job else None

    per = {}
    for arm in arms:
        d = rederive.strict_run_dir("%s_%s" % (a.tag_prefix, arm), a.expect_n,
                                    row_file="results.jsonl", require_slurm_jobs=jobs)
        per[arm] = by_domain(d)
    doms = sorted(set.intersection(*(set(v) for v in per.values())))
    n_dom = len(doms)
    want = pr["population"]["%s_domains" % a.split]
    print("[power] SIZE domains = %d (preregistered %d) | arms = %d | controls = %d"
          % (n_dom, want, len(arms), len(controls)))
    if n_dom != want:
        sys.exit("REFUSING: %d domains but the prereg says %d" % (n_dom, want))

    base = per["HD_BASE"]
    E = {arm: statistics.fmean([per[arm][d] - base[d] for d in doms]) for arm in arms if arm != "HD_BASE"}
    ctrl_E = [E[c] for c in controls]
    mu0, sd0 = statistics.fmean(ctrl_E), statistics.stdev(ctrl_E)
    print("[power] control E: mean %.6f  sd %.6f  (n=%d)" % (mu0, sd0, len(ctrl_E)))
    print("[power] observed candidate E = %.6f | E(HD_KO) = %.6f" % (E["HD_TOPK"], E["HD_KO"]))

    floor = 1.0 / (len(controls) + 1)
    rng = random.Random(a.seed)

    def power_at(delta):
        """P(a candidate with true mean mu0+delta ranks strictly first of 21).

        The 20 controls are resampled from their OWN empirical E values with replacement, so the
        null keeps whatever shape it actually has rather than being assumed Gaussian; the candidate
        is drawn from the same empirical distribution and shifted by delta.
        """
        hit = 0
        for _ in range(a.B):
            cs = [ctrl_E[rng.randrange(len(ctrl_E))] for _ in range(len(controls))]
            cand = ctrl_E[rng.randrange(len(ctrl_E))] + delta
            if cand < min(cs):
                hit += 1
        return hit / a.B

    # scan delta downward (more negative = stronger) until power crosses the target
    curve, mde = [], None
    step = 0.002
    delta = 0.0
    while delta > -0.20:
        p = power_at(delta)
        curve.append({"delta": round(delta, 6), "power": round(p, 4)})
        if mde is None and p >= a.target_power:
            mde = delta
        if p >= 0.995 and mde is not None:
            break
        delta -= step

    obs_power = power_at(E["HD_TOPK"] - mu0)
    frac_of_ko = (mde / E["HD_KO"]) if (mde is not None and E["HD_KO"]) else None

    out = {
        "schema": "dcs_csi_head_power/1",
        "prereg": a.prereg, "prereg_id": pr["id"], "split": a.split,
        "n_domains": n_dom, "n_controls": len(controls), "B": a.B, "seed": a.seed,
        "attainable_floor": floor,
        "ONLY_RANK_1_CERTIFIES": ("with %d controls the floor is %.6f, so rank 2 gives %.6f and "
                                  "cannot pass at alpha=0.05 for ANY effect size"
                                  % (len(controls), floor, 2*floor)),
        "control_E": {"mean": mu0, "sd": sd0, "values": [round(v, 8) for v in sorted(ctrl_E)]},
        "observed": {"E_HD_TOPK": E["HD_TOPK"], "E_HD_KO": E["HD_KO"],
                     "candidate_shift_vs_control_mean": E["HD_TOPK"] - mu0,
                     "power_at_the_observed_effect": round(obs_power, 4)},
        "target_power": a.target_power,
        "MDE": None if mde is None else round(mde, 6),
        "MDE_as_fraction_of_E_HD_KO": None if frac_of_ko is None else round(frac_of_ko, 4),
        "curve": curve,
        "NOISE_MODEL_CAVEAT": ("the null spread is the 20 control arms' own E sd, which conflates "
                               "domain sampling noise with genuine arm-to-arm heterogeneity between "
                               "different random 8-head sets. Conservative for an MDE, but NOT a "
                               "clean estimate of domain sampling error; separating them would need "
                               "repeated draws of the SAME head set, which no arm provides"),
        "CANNOT_ANSWER": ("this is the power of the RANK test as run. It says nothing about the "
                          "power of the F criterion's ci95, nor about TRAIN, nor about any head set "
                          "other than one behaving like a random draw plus a constant shift"),
    }
    n = atomic_write_json(a.out, out)
    print("[power] wrote+verified %s (%d bytes)" % (a.out, n))
    print("[power] attainable floor %.6f -- ONLY rank 1 certifies" % floor)
    print("[power] MDE at %.0f%% power = %s  (%.1f%% of E(HD_KO) = %.6f)"
          % (100*a.target_power, out["MDE"], 100*(frac_of_ko or 0), E["HD_KO"]))
    print("[power] power at the OBSERVED effect = %.4f" % obs_power)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
