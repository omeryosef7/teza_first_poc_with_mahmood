#!/usr/bin/env python3
"""INDEPENDENT verifier for DCS-PR-031 (the Bombness specificity result).

⛔ This file deliberately does NOT import `scripts/dcs_bombness_specificity.py`. A verifier that
reuses the producer's own functions re-derives the producer's bugs and proves nothing (the lesson
of `DCS-A-004`, which reproduced every published number to the digit and still had to falsify two
published claims). Everything here is re-derived from the LOWEST-LEVEL artifacts on disk: the bank
JSONL files, the extractor's `RUNMETA.json`/`config.json`, and the raw
`cache/final_occurrence_reps.pt` tensors.

WHAT IT CHECKS
  1. POPULATION IDENTITY  — row counts, cell/domain/family structure, and the fact that the analysis
     population is exactly what `PR-031` declared.
  2. THE KEY HAZARD       — that `prompt_id` collides across banks, so any join on it alone is
     wrong. The verifier PROVES the collision rather than trusting the note.
  3. CONFIG IDENTITY      — all eight runs share model, layers, position, dtype and seed. An arm
     extracted at a different position or layer set is not comparable and the comparison is void.
  4. CACHE INTEGRITY      — shapes, dtype, layer list, and that every analysed prompt_id is present.
  5. STATISTIC RE-DERIVATION — per-domain held-out accuracy recomputed from scratch, with its own
     fold construction and standardisation, and compared against the producer's JSON.
  6. LEAKAGE              — that the probe channel's question text does not contain the concept word
     (the §2.3 disqualification of `semantic_forced_choice`), checked on the actual prompts.

MUTATION HARNESS: `--mutate <kind>` deliberately corrupts an input and asserts the verifier FAILS.
A verifier that cannot fail is not a verifier.
"""
from __future__ import annotations
import argparse, collections, glob, hashlib, json, os, sys
import numpy as np

CODEWORDS = ("button", "basket")
CONCEPTS = ("bomb", "knife", "gun", "club")
EXPECT_ROWS = 2736
EXPECT_LAYERS = [6, 7, 8, 9, 10, 11, 12, 13, 14]
EXPECT_POSITION = "codeword_last"


class Report:
    def __init__(self):
        self.checks, self.failed = [], 0

    def ok(self, name, detail=""):
        self.checks.append(("PASS", name, detail)); print(f"  [PASS] {name}  {detail}")

    def bad(self, name, detail=""):
        self.checks.append(("FAIL", name, detail)); self.failed += 1
        print(f"  [FAIL] {name}  {detail}")

    def note(self, name, detail=""):
        self.checks.append(("NOTE", name, detail)); print(f"  [note] {name}  {detail}")


def bank_path(bd, cw, cc):
    return os.path.join(bd, f"boombness_prompt_bank_{cw}_{cc}.jsonl")


def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def check_population(bd, rep):
    print("\n[1] POPULATION IDENTITY")
    pid_sets, shapes = {}, {}
    for cw in CODEWORDS:
        for cc in CONCEPTS:
            p = bank_path(bd, cw, cc)
            if not os.path.exists(p):
                rep.bad(f"bank missing {cw}_{cc}", p); continue
            rows = [json.loads(l) for l in open(p)]
            if len(rows) != EXPECT_ROWS:
                rep.bad(f"{cw}_{cc} row count", f"{len(rows)} != {EXPECT_ROWS}")
            pids = [r["prompt_id"] for r in rows]
            if len(set(pids)) != len(pids):
                rep.bad(f"{cw}_{cc} duplicate prompt_id within bank",
                        f"{len(pids) - len(set(pids))} dupes")
            pid_sets[(cw, cc)] = set(pids)
            for qk in ("semantic_one_word", "comprehension_usage"):
                sub = [r for r in rows if r["query_kind"] == qk]
                cells = collections.Counter(r["cell"] for r in sub)
                doms = len({r["domain"] for r in sub})
                shapes[(cw, cc, qk)] = (len(sub), dict(cells), doms)
    ref = None
    for k, v in shapes.items():
        if k[2] == "comprehension_usage":
            if ref is None:
                ref = v
            elif v != ref:
                rep.bad("comprehension_usage shape differs across banks", f"{k}: {v} vs {ref}")
    if ref:
        rep.ok("comprehension_usage identical across all 8 banks",
               f"n={ref[0]} cells={ref[1]} domains={ref[2]}")
    return pid_sets


def check_prompt_id_collision(pid_sets, rep):
    print("\n[2] THE JOIN HAZARD — prompt_id must NOT be treated as a key")
    keys = sorted(pid_sets)
    if len(keys) < 2:
        rep.note("collision check skipped", "fewer than 2 banks"); return
    a, b = keys[0], keys[1]
    inter = pid_sets[a] & pid_sets[b]
    if len(inter) == len(pid_sets[a]) == len(pid_sets[b]):
        rep.ok("prompt_id COLLIDES 100% across banks (as A-019 states)",
               f"{a} vs {b}: {len(inter)}/{len(pid_sets[a])} shared -> compound key MANDATORY")
    else:
        rep.bad("prompt_id collision not as documented",
                f"{a} vs {b}: {len(inter)} shared of {len(pid_sets[a])}/{len(pid_sets[b])}")
    n_all = len(set.intersection(*[pid_sets[k] for k in keys]))
    rep.note("prompt_ids common to ALL banks", str(n_all))


def check_configs(runs, rep):
    print("\n[3] CONFIG IDENTITY ACROSS RUNS")
    seen = {}
    for k, d in sorted(runs.items()):
        mp = os.path.join(d, "RUNMETA.json")
        if not os.path.exists(mp):
            rep.bad(f"RUNMETA missing {k}", d); continue
        m = json.load(open(mp))
        args = m.get("args", {})
        sig = (args.get("model"), str(args.get("layers")), args.get("position"),
               args.get("dtype"), args.get("seed"), args.get("stage"))
        seen.setdefault(sig, []).append(f"{k[0]}_{k[1]}")
        if args.get("position") != EXPECT_POSITION:
            rep.bad(f"{k} position", f"{args.get('position')!r} != {EXPECT_POSITION!r}")
    if len(seen) == 1:
        sig, who = next(iter(seen.items()))
        rep.ok("all runs share model/layers/position/dtype/seed/stage",
               f"{len(who)} runs, sig={sig}")
    else:
        for sig, who in seen.items():
            rep.bad("CONFIG SPLIT — arms are not comparable", f"{sig} <- {who}")


def check_caches(runs, bd, rep):
    print("\n[4] CACHE INTEGRITY")
    import torch
    for k, d in sorted(runs.items()):
        p = os.path.join(d, "cache", "final_occurrence_reps.pt")
        if not os.path.exists(p):
            rep.bad(f"cache missing {k}", p); continue
        blob = torch.load(p, map_location="cpu")
        if list(blob["layers"]) != EXPECT_LAYERS:
            rep.bad(f"{k} layer list", f"{blob['layers']} != {EXPECT_LAYERS}")
        if blob.get("position") != EXPECT_POSITION:
            rep.bad(f"{k} cache position", str(blob.get("position")))
        reps = blob["reps"]
        anyk = next(iter(reps))
        shp = tuple(reps[anyk].shape)
        if shp != (len(EXPECT_LAYERS), 4096):
            rep.bad(f"{k} rep shape", str(shp))
        rows = [json.loads(l) for l in open(bank_path(bd, *k))]
        want = {r["prompt_id"] for r in rows
                if r["query_kind"] in ("semantic_one_word", "comprehension_usage")}
        miss = want - set(reps)
        if miss:
            rep.bad(f"{k} reps missing for analysed rows", f"{len(miss)}/{len(want)}")
        else:
            rep.ok(f"{k[0]}_{k[1]} cache complete", f"{len(reps)} stacks, all {len(want)} analysed rows present")


def check_leakage(bd, rep):
    print("\n[5] LEAKAGE — does the probe channel's question name the concept?")
    for qk, expect_safe in (("semantic_one_word", True), ("comprehension_usage", True),
                            ("semantic_forced_choice", False)):
        leaks = {}
        for cc in CONCEPTS:
            rows = [json.loads(l) for l in open(bank_path(bd, "button", cc))]
            sub = [r for r in rows if r["query_kind"] == qk and r["cell"] == "C"]
            if not sub:
                continue
            leaks[cc] = sum(1 for r in sub if cc in r["final_query_text"].lower())
        total_leak = sum(leaks.values())
        if expect_safe and total_leak == 0:
            rep.ok(f"{qk}: cell-C question NEVER names the concept", f"{leaks} -> usable as probe channel")
        elif expect_safe:
            rep.bad(f"{qk}: cell-C question NAMES THE CONCEPT", f"{leaks} -> NOT leakage-safe")
        elif total_leak > 0:
            rep.ok(f"{qk}: confirmed to leak (correctly disqualified)", f"{leaks}")
        else:
            rep.bad(f"{qk}: expected to leak but does not", f"{leaks}")


def rederive(result_json, runs, bd, rep, mutate=None):
    print("\n[6] STATISTIC RE-DERIVATION (independent implementation)")
    if not os.path.exists(result_json):
        rep.note("no producer JSON yet", result_json); return
    import torch
    from sklearn.linear_model import LogisticRegression
    res = json.load(open(result_json))
    prim = res.get("P2_primary")
    if not prim:
        rep.note("no P2_primary in producer JSON", ""); return
    classes = tuple(res["primary_classes"]); cw = res["primary_codeword"]
    chan = res["channel"]; nex = set(res["n_examples_primary"])

    data = []
    for cc in classes:
        d = runs.get((cw, cc))
        if d is None:
            rep.bad("missing run for re-derivation", f"{cw}_{cc}"); return
        blob = torch.load(os.path.join(d, "cache", "final_occurrence_reps.pt"), map_location="cpu")
        layers = list(blob["layers"]); reps = blob["reps"]
        for r in (json.loads(l) for l in open(bank_path(bd, cw, cc))):
            if r["query_kind"] != chan or r["cell"] != "C" or r["n_examples"] not in nex:
                continue
            if r["prompt_id"] in reps:
                data.append((r["domain"], cc, reps[r["prompt_id"]].float().numpy(), layers))
    if mutate == "shuffle_labels":
        rng = np.random.default_rng(0)
        labs = [d[1] for d in data]; rng.shuffle(labs)
        data = [(d[0], labs[i], d[2], d[3]) for i, d in enumerate(data)]
    if mutate == "zero_reps":
        data = [(d[0], d[1], np.zeros_like(d[2]), d[3]) for d in data]

    mine = {}
    for dom in sorted({d[0] for d in data}):
        pk = prim["picks"].get(dom)
        if not pk:
            continue
        L, C = int(pk["layer"]), float(pk["C"])
        j = data[0][3].index(L)
        tr = [d for d in data if d[0] != dom]; te = [d for d in data if d[0] == dom]
        Xtr = np.stack([d[2][j] for d in tr]); Xte = np.stack([d[2][j] for d in te])
        ytr = np.array([classes.index(d[1]) for d in tr])
        yte = np.array([classes.index(d[1]) for d in te])
        mu, sd = Xtr.mean(0), Xtr.std(0); sd[sd < 1e-8] = 1.0
        clf = LogisticRegression(C=C, max_iter=3000).fit((Xtr - mu) / sd, ytr)
        mine[dom] = float((clf.predict((Xte - mu) / sd) == yte).mean())

    theirs = prim["per_domain"]
    worst, bad = 0.0, []
    for dom, v in mine.items():
        if dom in theirs:
            delta = abs(v - theirs[dom]); worst = max(worst, delta)
            if delta > 1e-9:
                bad.append((dom, theirs[dom], v))
    if not mine:
        rep.bad("re-derivation produced nothing", "")
    elif bad:
        rep.bad("per-domain accuracy DISAGREES with producer",
                f"max|delta|={worst:.6f}; e.g. {bad[:3]}")
    else:
        rep.ok("per-domain accuracy reproduces exactly",
               f"{len(mine)} domains, max|delta|={worst:.2e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-root", default="outputs/boombness/extract_boombness")
    ap.add_argument("--run-prefix", default="bombspec")
    ap.add_argument("--bank-dir", default="data/boombness_prompts")
    ap.add_argument("--result", default="outputs/boombness/dcs_analysis/dcs_bombness_specificity.json")
    ap.add_argument("--mutate", default=None,
                    choices=["shuffle_labels", "zero_reps"],
                    help="corrupt an input and REQUIRE the verifier to fail")
    a = ap.parse_args()

    runs = {}
    for cw in CODEWORDS:
        for cc in CONCEPTS:
            hits = sorted(glob.glob(os.path.join(a.runs_root, f"{a.run_prefix}_{cw}_{cc}_*")))
            if hits:
                runs[(cw, cc)] = hits[-1]
    print(f"VERIFIER for DCS-PR-031 — {len(runs)}/8 run dirs found")
    rep = Report()
    pid_sets = check_population(a.bank_dir, rep)
    check_prompt_id_collision(pid_sets, rep)
    if runs:
        check_configs(runs, rep)
        check_caches(runs, a.bank_dir, rep)
    check_leakage(a.bank_dir, rep)
    if runs:
        rederive(a.result, runs, a.bank_dir, rep, mutate=a.mutate)

    print(f"\n=== {sum(1 for c in rep.checks if c[0]=='PASS')} passed, {rep.failed} FAILED ===")
    if a.mutate:
        if rep.failed == 0:
            print(f"MUTATION HARNESS FAILED: input was corrupted with {a.mutate!r} and the verifier "
                  f"still passed. The verifier cannot fail and proves nothing.")
            return 2
        print(f"MUTATION HARNESS OK: corruption {a.mutate!r} was caught.")
        return 0
    return 1 if rep.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
