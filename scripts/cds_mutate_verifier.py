#!/usr/bin/env python
"""cds_mutate_verifier.py -- does `cds_verify_install_vs_asr.py` actually have teeth?

A verifier that only ever printed PASS would be indistinguishable from one that works. This script
takes the PUBLISHED JSON, writes a TEMP COPY with ONE minimally perturbed value, points the
verifier at the copy, and requires that (a) the verifier exits non-zero and (b) the check that goes
red is the one belonging to that assertion class -- not merely some collateral aggregate.

Two rules the mutation targets follow, both learned from mutation tests that flattered themselves:

  * LEAST HEADROOM, not most. For each class the target is the cell whose value is HARDEST to
    catch -- the smallest magnitude for a relative comparison, the exact 0.0 for `refusal_rate`
    (which can only be caught by the absolute floor). Mutating install_rate 1.000 -> 2.000 proves
    nothing about install_rate 0.0125.
  * The perturbation is SMALL: 1 part in 1e6 for floats (three orders inside the verifier's own
    1e-9 relative tolerance is the point of the exercise, not a bigger hammer), +1 for counts,
    one character for identifiers.

A class that CANNOT be made to go red is reported as NOT COVERED, loudly, and makes this script
exit non-zero. It is a finding about the verifier, not a nuisance to be dropped.

Nothing in the repository is modified: the mutated JSON lives in a temp directory that is removed.
"""
from __future__ import annotations
import argparse, copy, json, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERIFIER = os.path.join(ROOT, "scripts", "cds_verify_install_vs_asr.py")
PUBLISHED = os.path.join(ROOT, "outputs/boombness/cds_analysis/cds_install_vs_asr.json")

FLOAT_NUDGE = 1e-6      # relative
ZERO_NUDGE = 1e-9       # absolute, for values published as exactly 0.0


# --------------------------------------------------------------------- target pickers
def _cells(d):
    return d["cells"]


def tightest(d, field):
    """Index of the cell whose value of `field` is smallest in magnitude -> least headroom."""
    idx = [i for i, c in enumerate(_cells(d)) if c.get(field) is not None]
    return min(idx, key=lambda i: (abs(_cells(d)[i][field]), i))


def nudge_float(d, field):
    i = tightest(d, field)
    v = _cells(d)[i][field]
    _cells(d)[i][field] = (v * (1.0 + FLOAT_NUDGE)) if v != 0 else ZERO_NUDGE
    return "cell[%d] %s %r -> %r" % (i, field, v, _cells(d)[i][field])


def bump_int(d, field):
    i = tightest(d, field)
    v = _cells(d)[i][field]
    _cells(d)[i][field] = v + 1
    return "cell[%d] %s %d -> %d" % (i, field, v, _cells(d)[i][field])


def _lowest_install_cell(d):
    """A cell that is NOT high-install/low-ASR, so identity mutations do not leak into the
    pair-set aggregate and blur two classes together."""
    return min(range(len(_cells(d))), key=lambda i: _cells(d)[i]["install_rate"])


def mut_pair_identity(d):
    i = _lowest_install_cell(d)
    old = list(_cells(d)[i]["pair"])
    _cells(d)[i]["pair"] = [old[0], old[1][:-1] + ("x" if not old[1].endswith("x") else "y")]
    return "cell[%d] pair %r -> %r" % (i, old, _cells(d)[i]["pair"])


def mut_pair_set(d):
    old = copy.deepcopy(d["high_install_low_asr_pairs"])
    d["high_install_low_asr_pairs"] = old[:-1]
    return "high_install_low_asr_pairs %r -> %r" % (old, d["high_install_low_asr_pairs"])


def mut_verdict(d):
    old = d["verdict"]
    d["verdict"] = ("SUPPORTED BUT SCOPED TO ONE PAIR" if old == "SUPPORTED" else "SUPPORTED")
    return "verdict %r -> %r" % (old, d["verdict"])


def mut_judge_pinned(d):
    i = 0
    old = _cells(d)[i]["judge_pinned"]
    _cells(d)[i]["judge_pinned"] = old.replace("-mini", "")  # a REAL, adjacent model id
    return "cell[%d] judge_pinned %r -> %r" % (i, old, _cells(d)[i]["judge_pinned"])


def mut_bank_sha(d):
    i = 0
    old = _cells(d)[i]["bank_rows_sha16"]
    ch = "0" if old[-1] != "0" else "1"
    _cells(d)[i]["bank_rows_sha16"] = old[:-1] + ch
    return "cell[%d] bank_rows_sha16 %r -> %r" % (i, old, _cells(d)[i]["bank_rows_sha16"])


def mut_converse(d):
    old = copy.deepcopy(d["converse_cells"])
    d["converse_cells"] = old[:-1]
    return "converse_cells: dropped 1 (%d -> %d)" % (len(old), len(d["converse_cells"]))


def ends(sfx):
    return lambda label: label.endswith(sfx)


def has(sub):
    return lambda label: sub in label


# class name -> (mutation fn, predicate identifying the check that MUST go red)
CLASSES = [
    ("installation rate",   lambda d: nudge_float(d, "install_rate"),   ends(" install_rate")),
    ("installation n",      lambda d: bump_int(d, "install_n"),         ends(" install_n")),
    ("installation wins",   lambda d: bump_int(d, "install_wins"),      ends(" install_wins")),
    ("installation ties",   lambda d: bump_int(d, "install_ties"),      ends(" install_ties")),
    ("installation domains", lambda d: bump_int(d, "install_domains"),  ends(" install_domains")),
    ("ASR",                 lambda d: nudge_float(d, "asr"),            ends(" asr")),
    ("ASR n",               lambda d: bump_int(d, "asr_n"),             ends(" asr_n")),
    ("malicious count",     lambda d: bump_int(d, "asr_malicious"),     ends(" asr_malicious")),
    ("refusal rate",        lambda d: nudge_float(d, "refusal_rate"),   ends(" refusal_rate")),
    ("pair identity",       mut_pair_identity,                          has("pair from bank")),
    ("pair-set",            mut_pair_set,                               has("distinct lexical pairs")),
    ("verdict",             mut_verdict,                                has("verdict string")),
    ("judge pinning",       mut_judge_pinned,                           has("judge_pinned")),
    ("bank_rows_sha16",     mut_bank_sha,                               has("bank_rows_sha16 published")),
    ("converse cells",      mut_converse,                               has("converse cells")),
]


def run_verifier(path):
    p = subprocess.run([sys.executable, VERIFIER, "--published", path, "--quiet"],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    labels = []
    for line in p.stdout.splitlines():
        if line.startswith("  - ") and " : " in line:
            labels.append(line[4:].split(" : ", 1)[0].strip())
    return p.returncode, labels, p.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--published", default=PUBLISHED)
    a = ap.parse_args()

    base = json.load(open(a.published))

    rc0, _, out0 = run_verifier(a.published)
    print("baseline (unmutated) verifier exit=%d -- %s\n"
          % (rc0, "GREEN" if rc0 == 0 else "ALREADY RED, mutations below mean less"))

    tmp = tempfile.mkdtemp(prefix="cds_mut_")
    rows, uncovered = [], []
    try:
        for name, mutate, want in CLASSES:
            d = copy.deepcopy(base)
            what = mutate(d)
            p = os.path.join(tmp, "mut.json")
            json.dump(d, open(p, "w"), indent=1)
            rc, labels, _ = run_verifier(p)
            targeted = [l for l in labels if want(l)]
            ok = rc != 0 and bool(targeted)
            rows.append((name, ok, rc, len(labels), targeted[:1], what))
            if not ok:
                uncovered.append((name, rc, labels, what))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("%-22s %-6s %-5s %-8s %s" % ("CLASS", "RED?", "exit", "#failed", "targeted check that went red"))
    for name, ok, rc, nfail, targeted, what in rows:
        print("%-22s %-6s %-5d %-8d %s" % (name, "yes" if ok else "NO", rc, nfail,
                                           targeted[0] if targeted else "-- none --"))
        print("%-22s   mutation: %s" % ("", what))

    print("\n%d/%d assertion classes provably go red." % (len(rows) - len(uncovered), len(rows)))
    if uncovered:
        print("\n!!! NOT COVERED -- these mutations did NOT turn the verifier red. This is a "
              "FINDING about the verifier, not about the data:")
        for name, rc, labels, what in uncovered:
            print("  - %-22s exit=%d  mutation: %s  failures seen: %r" % (name, rc, what, labels))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
