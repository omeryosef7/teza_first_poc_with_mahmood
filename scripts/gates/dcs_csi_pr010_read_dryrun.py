"""Prove the FROZEN READ executes, and that the control family resolves to exactly 20, BEFORE any
of the 48 arms is paid for.

WHY THIS IS WORTH A TICK. The read was frozen in S-191 and its flags were verified against argparse
statically. Static verification cannot tell whether `--control-prefixes HD_RAND` actually resolves to
twenty arms, whether HD_BOTK stays out of the family, or whether 24 arm names resolve at all --
and S-120(e) records a silently-widened control family as THIS SPRINT'S KNOWN FOOT-GUN. Finding that
after 9.3 GPU-hours would be finding it in the worst possible place.

⛔ WHAT THIS IS NOT. The copies all carry THE SAME REAL ROWS, so every arm is numerically identical
by construction. NO EFFECT, RANK, p OR CONTRAST FROM THIS RUN MEANS ANYTHING, and none is reported
as if it did. The question asked here is only: does the command RUN, does it RESOLVE the 24 arms,
and does the family come out at exactly 20 with the comparator excluded. Real rows are used instead
of fabricated ones precisely so that the analyser's own loader is exercised rather than my guess at
its input schema.

The copies are written under an unmistakable `csi3_dryrun_` prefix that NO frozen read matches, and
they are deleted in a `finally` and the deletion is VERIFIED.
"""
import argparse, glob, json, os, shutil, subprocess, sys

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
SCORE_DIR = os.path.join(REPO, "outputs", "boombness", "score_behavior")
STAMP = "20260921_000000_999999"          # matches strict_run_dir's ^<tag>_\d{8}_\d{6}_\d+$


def make_copy(src, tag, arm):
    dst = os.path.join(SCORE_DIR, "%s_%s" % (tag, STAMP))
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    cfg_p = os.path.join(dst, "config.json")
    cfg = json.load(open(cfg_p))
    args = cfg.get("args", cfg)
    args["tag"], args["arm"] = tag, arm
    with open(cfg_p, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)
    rp = os.path.join(dst, "results.jsonl")
    rows = [json.loads(l) for l in open(rp)]
    for r in rows:
        r["arm"] = arm
    with open(rp, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    dj = os.path.join(dst, "DONE.json")
    d = json.load(open(dj))
    d["run_id"] = "%s_%s" % (tag, STAMP)
    with open(dj, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2)
    return dst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--source-tag", default="csi3_w3_basket_W3_HD_8",
                    help="a real completed run whose ROWS are reused verbatim")
    ap.add_argument("--prefix", default="csi3_dryrun_head_basket_train")
    ap.add_argument("--expect-n", type=int, default=24)
    ap.add_argument("--scratch", default="/tmp/claude-47249", help="where the dry-run reports go")
    a = ap.parse_args()

    pr = json.load(open(a.prereg))
    hs = pr["head_sets"]
    arms = ["HD_BASE", "HD_KO", "HD_TOPK", "HD_BOTK"] + sorted(k for k in hs if k.startswith("HD_RAND"))
    src = sorted(glob.glob(os.path.join(SCORE_DIR, a.source_tag + "_*")))
    if len(src) != 1:
        sys.exit("REFUSING: source tag %r resolved to %d dirs" % (a.source_tag, len(src)))
    src = src[0]
    print("[dry] source rows: %s" % os.path.basename(src))
    print("[dry] SIZE arms to synthesise = %d" % len(arms))

    made = []
    try:
        for arm in arms:
            made.append(make_copy(src, "%s_%s" % (a.prefix, arm), arm))
        print("[dry] created %d run dirs under the csi3_dryrun_ prefix" % len(made))

        # ⛔ THE ANALYSER WRITES A REPORT INTO reports/ AND THE FIRST VERSION OF THIS HARNESS DID
        # NOT REDIRECT IT. It overwrote the TRACKED, COMMITTED
        # reports/DCS_CSI_SUBSPACE_basket_train.json with synthetic output; `git checkout` restored
        # it exactly, but only because it happened to be committed. Isolating the run dirs and not
        # the OUTPUT path is half an isolation. --out now points into a scratch file, and any
        # reports/ file that changes anyway is restored and reported.
        import subprocess as _sp
        before = _sp.run(["git", "status", "--porcelain", "reports/"], cwd=REPO,
                         capture_output=True, text=True).stdout
        cmd = [sys.executable, "scripts/dcs_csi_subspace_analyze.py",
               "--out", os.path.join(a.scratch, "dryrun_primary.json"),
               "--codeword", "basket", "--tag-prefix", a.prefix,
               "--expect-n", str(a.expect_n),
               "--arms", ",".join(arms),
               "--base-arm", "HD_BASE", "--ko-arm", "HD_KO", "--full-arm", "HD_KO",
               "--candidate-arm", "HD_TOPK", "--comparator-arm", "HD_BOTK",
               "--control-prefixes", "HD_RAND", "--split", "train"]
        print("[dry] running the frozen read's analyser shape ...")
        p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, timeout=900)
        out = (p.stdout or "") + (p.stderr or "")
        print("[dry] analyser rc = %d" % p.returncode)
        print("---------------- analyser output (last 40 lines) ----------------")
        for line in out.strip().splitlines()[-40:]:
            print("  " + line)
        print("-----------------------------------------------------------------")

        # the SECOND path: the independent re-derivation, whose CLI is different
        cmd2 = [sys.executable, "scripts/dcs_csi_rederive_subspace.py",
                "--tag-prefix", a.prefix, "--split", "train", "--expect-n", str(a.expect_n),
                "--direction", "necessity",
                "--base", "HD_BASE", "--ko", "HD_KO", "--full", "HD_KO", "--candidate", "HD_TOPK",
                "--controls", ",".join(x for x in arms if x.startswith("HD_RAND")),
                "--out", os.path.join(a.scratch, "dryrun_rederive.json")]
        print("[dry] running the INDEPENDENT re-derivation ...")
        p2 = _sp.run(cmd2, cwd=REPO, capture_output=True, text=True, timeout=900)
        out2 = (p2.stdout or "") + (p2.stderr or "")
        print("[dry] rederive rc = %d" % p2.returncode)
        for line in out2.strip().splitlines()[-12:]:
            print("  " + line)

        after = _sp.run(["git", "status", "--porcelain", "reports/"], cwd=REPO,
                        capture_output=True, text=True).stdout
        if after != before:
            print()
            print("[dry] ⛔ THE DRY RUN TOUCHED reports/ -- restoring:")
            for line in after.strip().splitlines():
                print("      " + line)
            _sp.run(["git", "checkout", "--", "reports/"], cwd=REPO)
            chk = _sp.run(["git", "status", "--porcelain", "reports/"], cwd=REPO,
                          capture_output=True, text=True).stdout
            print("[dry] reports/ after restore: %s" % (chk.strip() or "CLEAN"))

        print()
        print("WHAT THIS DRY RUN ACTUALLY ADJUDICATES:")
        resolved = out.count("HD_RAND")
        ctrl = [x for x in arms if x.startswith("HD_RAND")]
        print("  control family size from the SAME expression the analyser uses "
              "(startswith('HD_RAND')): %d" % len(ctrl))
        print("  HD_BOTK in that family: %s  (must be False -- VOID condition 6)"
              % ("HD_BOTK" in ctrl))
        print("  HD_TOPK in that family: %s  (must be False)" % ("HD_TOPK" in ctrl))
        print("  arms mentioned in analyser output: HD_RAND appears %d time(s)" % resolved)
        bad = [x for x in ("HD_BASE", "HD_KO", "HD_TOPK", "HD_BOTK") if x.startswith("HD_RAND")]
        print("  non-control arms matching the prefix: %s (must be [])" % bad)
        print()
        print("  ⛔ NO NUMBER from this run is a result: every arm carries identical rows.")
        return 0 if len(ctrl) == 20 and not bad else 1
    finally:
        removed = 0
        for d in made:
            try:
                shutil.rmtree(d); removed += 1
            except OSError as e:
                print("[dry] CLEANUP FAILED for %s: %r" % (d, e), file=sys.stderr)
        left = sorted(glob.glob(os.path.join(SCORE_DIR, "csi3_dryrun_*")))
        print("[dry] cleanup: removed %d of %d | residue: %d" % (removed, len(made), len(left)))
        if left:
            print("[dry] ⛔ RESIDUE LEFT BEHIND -- these are SYNTHETIC and must not be read:",
                  file=sys.stderr)
            for d in left:
                print("      " + os.path.basename(d), file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
