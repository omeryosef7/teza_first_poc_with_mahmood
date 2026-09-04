#!/usr/bin/env python
"""dcs_verify_merge_audit.py -- mutation harness for `scripts/dcs_merge_audit_pools.py`.

`PR-024`'s pool audit is the only thing standing between a bad demonstration pool and a 116-domain
bank that 16 GPU-hours will be spent on. A guard that has never rejected anything is not a guard, so
each refusal is fired deliberately here on synthetic pools.

⛔ It pins TWO non-refusals: a sentence appearing in two domains is REPORTED, not fatal. That is
a deliberate choice and it is recorded rather than left implicit -- with 116 domains x 40 sentences
per valence, an identical short filler line arising twice is plausible by chance, and blocking a
16-GPU-hour run on one collision would be the wrong trade. ⚠ Any non-zero count is reported as a
caveat on domain independence, which is the unit `B-009` exists to strengthen.

⛔ The second non-refusal is an INCIDENTAL COLLISION. `DCS-C-036` rescoped that from fatal to
reported: pools are written around ONE codeword and one concept, so every OTHER codeword appearing
incidentally is expected -- those banks are built by substitution, and `prompt_families` already
refuses at bank build with a per-codeword guard and `--incidental-replace`. The old rule rejected
27 of the CANONICAL pools, i.e. the ones every committed bank was built from.

Synthetic pools only -- no real sentence text is read or emitted.
"""
from __future__ import annotations
import json, os, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, "scripts", "dcs_merge_audit_pools.py")
META = {"generator": "gpt-4o-mini", "openai_seed": 20260828, "concept": "bomb",
        "codeword": "carrot", "remap_source_word": "bicycle", "n_per_pool": 4,
        "per_split": 2, "content_sha16": "x"}


def pool(dom, val, sents):
    return {f"{dom}|{val}": {"domain": dom, "valence": val, "natural_word": "carrot",
                             "sentences": sents, "n": len(sents)}}


def run(a, b, expect_refuse, label, n=4):
    with tempfile.TemporaryDirectory() as td:
        pa, pb, out, rep = (os.path.join(td, x) for x in ("a.json", "b.json", "m.json", "r.json"))
        json.dump({"_meta": a[0], "pools": a[1]}, open(pa, "w"))
        json.dump({"_meta": b[0], "pools": b[1]}, open(pb, "w"))
        r = subprocess.run([sys.executable, S, "--existing", pa, "--new", pb, "--out", out,
                            "--report", rep, "--expect-n", str(n)],
                           capture_output=True, text=True)
        refused, wrote = r.returncode != 0, os.path.exists(out)
        ok = refused == expect_refuse and (not expect_refuse or not wrote)
        print(f"  {'PASS' if ok else 'FAIL'}  {label:52s} refused={refused} wrote={wrote}")
        return ok


def main() -> None:
    A = (META, {**pool("alpha", "benign", ["a carrot here", "two carrot", "three carrot", "four carrot"]),
                **pool("alpha", "harm", ["a bomb here", "two bomb", "three bomb", "four bomb"])})
    B = (META, {**pool("beta", "benign", ["b carrot one", "b carrot two", "b carrot three", "b carrot four"]),
                **pool("beta", "harm", ["b bomb one", "b bomb two", "b bomb three", "b bomb four"])})
    ok = [
        run(A, B, False, "clean pair -> merges"),
        run(A, ({**META, "openai_seed": 20260816}, B[1]), True, "seed mismatch -> REFUSE"),
        run(A, ({**META, "codeword": "button"}, B[1]), True, "codeword mismatch -> REFUSE"),
        run(A, (META, {**pool("alpha", "benign", ["x carrot", "y carrot", "z carrot", "w carrot"])}),
            True, "domain in BOTH halves -> REFUSE"),
        run(A, (META, {**pool("beta", "benign", ["only carrot one", "only carrot two"])}),
            True, "short pool -> REFUSE"),
        # DCS-C-036: this expectation was flipped from REFUSE to report-only, and the harness
        # CAUGHT the change rather than letting it pass silently -- which is the point of pinning
        # a contract. Pool-level collision-freedom was the wrong rule: 27 of the CANONICAL
        # 38-domain pools carry these words, so every committed bank in the phase was built from
        # pools the old check rejected. Collisions are repaired at BANK BUILD, per codeword.
        run(A, (META, {**pool("beta", "benign", ["carrot and a knife", "b carrot two",
                                                 "b carrot three", "b carrot four"])}),
            False, "collision in a pool -> REPORTED, not fatal (C-036)"),
        run(A, (META, {**pool("beta", "harm", ["a bomb here", "q bomb", "r bomb", "s bomb"])}),
            False, "duplicate sentence across domains -> reported, NOT fatal"),
    ]
    print()
    if not all(ok):
        print("VERIFY: FAIL")
        sys.exit(1)
    print(f"VERIFY: PASS ({len(ok)}/{len(ok)})")


if __name__ == "__main__":
    main()
