"""unanalysed_triage.py — of the runs no artifact cites, WHICH COULD CHANGE A CONCLUSION?

WHY THIS EXISTS, AND WHY IT IS SEPARATE FROM `unanalysed_inventory.py`.

The inventory counts the drop-offs and says, in its own docstring, that it "deliberately does NOT try
to decide which gaps matter". That was the right call for a counter: a smoke test and an abandoned arm
both belong in the list, and a counter that editorialises is a counter you stop trusting.

But audit #12 asked the question the count cannot answer. "78 judged runs are cited by no artifact" is
not a finding, it is an anxiety. The finding is: *of those 78, which ones, if analysed, could move a
number this sprint reports?* Most cannot -- they are replicates of arms already analysed, or they run
on a population no headline claim is about. A few might. Naming that few is the whole point, because an
unanalysed run that could overturn a claim and an unanalysed smoke test are the same row in a count and
opposite things in a report.

So the inventory keeps its neutrality and this adds the judgment on top, where the judgment can be
argued with separately.

HOW IT DECIDES. Every run is addressed by IDENTITY -- (model, bank, declared `--intervene` spec) --
never by tag. A run is triaged as:

  base_or_control       the run has no intervention; it is a baseline, consumed by whatever cites it
  underpowered          fewer than --min-analysable rows: cannot move a cluster test either way
  off_headline_population  a bank no headline claim is about
  replicate_of_cited    an identical (model, bank, spec) IS cited somewhere; this can tighten an
                        interval but cannot reverse a sign. Its ASR gap vs the cited twin is
                        reported, because a large gap is itself a finding about judge/seed noise.
  COULD_CHANGE          an intervention arm, adequately powered, on a headline population, whose
                        (model, bank, spec) appears in NO cited artifact. These are the answer.

Reads NUMERIC fields only (`malicious_at_0.5`), never generations or judge text.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from unanalysed_inventory import git_commit_safe  # noqa: E402

# Banks the sprint's headline claims are actually about.
HEADLINE_BANKS = ("advbench_heldout_495", "clearharm", "boombness_prompt_bank")


def _asr(d: str):
    """Mean `malicious_at_0.5` and the prompt-id SET over a judge run. Numeric/categorical only."""
    n = k = 0
    ids = set()
    try:
        for line in open(os.path.join(d, "results.jsonl"), encoding="utf-8"):
            try:
                r = json.loads(line)
            except Exception:
                continue
            v = r.get("malicious_at_0.5")
            if v is None:
                continue
            n += 1
            k += 1 if v else 0
            pid = r.get("prompt_id")
            if pid is not None:
                ids.add(pid)
    except OSError:
        return None, 0, set()
    return (k / n if n else None), n, ids


def _gens_info(judge_dir: str) -> dict:
    """Config + TRUE model + the generation run's own tag, for the run behind a judge dir.

    Two traps here, both found by running this:

    * `config.json` records `model: None` whenever the run took the script default, so 78 of 107
      uncited runs read as model "unknown". The identity key is (model, bank, spec), so an unknown
      model silently merges two models' runs into one "replicate". The authoritative value is in
      `metadata.json`, which also pins the resolved revision.
    * THE JUDGE TAG IS NOT THE GENERATION TAG. Judge run `f3d_armA_*` scores generations from
      `fuF_addR_g02_*`. A script that names the generation tag was reading as "nobody consumed this".
    """
    out = {"cfg": {}, "gens_dir": None, "gens_tag": None, "model": "unknown"}
    try:
        cfg = json.load(open(os.path.join(judge_dir, "config.json")))
        gens = (cfg.get("args", cfg) or {}).get("gens")
        if not gens:
            return out
        gens = gens.rstrip("/")
        if gens.endswith("gens.jsonl"):
            gens = os.path.dirname(gens)
        out["gens_dir"] = gens
        out["gens_tag"] = _tag(os.path.basename(gens))
        g = json.load(open(os.path.join(gens, "config.json")))
        out["cfg"] = (g.get("args", g) or {}) or {}
    except Exception:
        return out
    try:
        md = json.load(open(os.path.join(out["gens_dir"], "metadata.json")))
        out["model"] = os.path.basename(str(md.get("model") or "")) or "unknown"
    except Exception:
        m = out["cfg"].get("model")
        out["model"] = os.path.basename(str(m)) if m else "unknown"
    return out


def _tag(basename: str) -> str:
    """The stable identity of a run: its tag, with the `_<date>_<time>_<pid>` suffix stripped.

    `q3dec_B11_20260821_182849_1074916` -> `q3dec_B11`. Scripts glob on the tag; only the launcher
    ever sees the full directory name, so the tag is what a consumer can be expected to name.
    """
    return re.sub(r"_\d{8}_\d{6}_\d+$", "", basename)


def _bank_id(path: str) -> str:
    b = os.path.basename(str(path or "")).replace(".jsonl", "")
    return b or "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default="outputs/boombness")
    ap.add_argument("--min-analysable", type=int, default=400,
                    help="below this a run cannot move a domain-clustered test")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    # WHAT COUNTS AS "CONSUMED" -- and why the first version of this got it wrong.
    #
    # v1 only scanned committed ARTIFACTS for a literal `/judge/<run>` path. That produced 94
    # "COULD_CHANGE" rows, which is not a shortlist, it is noise. The cause was real but different
    # from unanalysed data: `q3dec_B11*` is read by `analyze_qwen3_decomposition.py`, yet that
    # script's artifact never records WHICH runs it read. A run analysed by a committed script whose
    # output does not name its inputs is indistinguishable, from the outside, from a run nobody
    # touched.
    #
    # So a run is consumed if EITHER an artifact names it OR a committed script names its TAG -- the
    # basename with the `_<date>_<time>_<pid>` suffix stripped, which is the stable identity a script
    # globs on. Addressing by tag rather than by full directory name is the same
    # address-by-identity rule the angle resolver had to learn.
    #
    # The artifacts that are themselves indexes of runs (this file, the inventory) are EXCLUDED:
    # an index listing a run is not an analysis consuming it, and letting them count would make this
    # check pass by merely having been run once.
    INDEXES = ("unanalysed_inventory.json", "unanalysed_triage.json")
    cited = set()
    corpus = []
    for p in (glob.glob(os.path.join(args.root, "*.json"))
              + glob.glob(os.path.join(args.root, "*", "*.json"))):
        if os.path.basename(p) in INDEXES:
            continue
        try:
            blob = open(p, encoding="utf-8").read()
        except OSError:
            continue
        corpus.append(blob)
        for seg in blob.split("/judge/")[1:]:
            cited.add(seg.split('"')[0].split("/")[0])
    for p in glob.glob(os.path.join(HERE, "*.py")) + glob.glob("scripts/*.py"):
        if os.path.basename(p) in ("unanalysed_triage.py", "unanalysed_inventory.py"):
            continue
        try:
            corpus.append(open(p, encoding="utf-8").read())
        except OSError:
            pass
    CORPUS = "\n".join(corpus)

    runs = []
    for d in sorted(glob.glob(os.path.join(args.root, "judge", "*"))):
        if not os.path.isdir(d) or not os.path.exists(os.path.join(d, "DONE.json")):
            continue
        info = _gens_info(d)
        g = info["cfg"]
        asr, n, ids = _asr(d)
        b = os.path.basename(d)
        jt, gt = _tag(b), info["gens_tag"]
        via = ("artifact_path" if b in cited
               else "corpus_names_judge_tag" if jt in CORPUS
               else "corpus_names_gens_tag" if (gt and gt in CORPUS)
               else None)
        runs.append({
            "judge": b,
            "tag": jt,
            "gens_tag": gt,
            "n": n,
            "asr": asr,
            "model": info["model"],
            "bank": _bank_id(g.get("bank")),
            "spec": g.get("intervene") or None,
            # SEED IS PART OF A CONTROL'S IDENTITY. Two independent draws of `random:project_out:...`
            # share a spec string but are different directions; calling the second a "replicate that
            # cannot reverse a sign" is false -- adding control draws is exactly what refuted L6.
            "seed": g.get("seed"),
            "cited": via is not None,
            "consumed_via": via,
            "_ids": ids,
        })

    # JUDGE SHARDS ARE DISJOINT HALVES, NOT SEPARATE RUNS -- the C-11 bug class, which this script
    # reproduced. `dsL29J0` (248 rows) and `dsL29J1` (247 rows) have ZERO prompt-id overlap and union
    # to exactly 495: one full run of `d_surface:project_out:29-29:1.0`, split across two judge dirs.
    # Triaging each half against the 400-row threshold marked twelve fully-powered, genuinely
    # unanalysed arms as "underpowered" -- an UNDER-estimate of what needs attention, i.e. the unsafe
    # direction, in a script whose docstring claimed it erred the safe way.
    #
    # So: group by the generation run and spec, union the prompt ids, and triage the LOGICAL run.
    # Overlapping ids mean a genuine re-judge, not a shard, and are kept separate.
    def _merge_shards(runs):
        groups = {}
        for r in runs:
            groups.setdefault((r["gens_tag"], r["model"], r["bank"], r["spec"]), []).append(r)
        merged = []
        for gk, v in groups.items():
            if len(v) == 1:
                v[0]["n_union"] = v[0]["n"]
                v[0]["shards"] = [v[0]["judge"]]
                merged.append(v[0])
                continue
            union, overlap = set(), False
            for r in v:
                if union & r["_ids"]:
                    overlap = True
                union |= r["_ids"]
            if overlap:
                # a real re-judge of the same prompts: keep the shards distinct
                for r in v:
                    r["n_union"] = r["n"]
                    r["shards"] = [r["judge"]]
                    r["note"] = "re-judge (prompt ids overlap a sibling), not a shard"
                    merged.append(r)
                continue
            head = dict(v[0])
            head["n_union"] = len(union) or sum(x["n"] for x in v)
            head["shards"] = sorted(x["judge"] for x in v)
            head["n"] = sum(x["n"] for x in v)
            tot = sum(x["n"] for x in v)
            head["asr"] = (sum((x["asr"] or 0) * x["n"] for x in v) / tot) if tot else None
            head["cited"] = any(x["cited"] for x in v)
            head["consumed_via"] = next((x["consumed_via"] for x in v if x["consumed_via"]), None)
            head["note"] = f"{len(v)} disjoint judge shards unioned to {head['n_union']} rows"
            merged.append(head)
        return merged

    runs = _merge_shards(runs)

    def key(r):
        return (r["model"], r["bank"], r["spec"], r.get("seed"))

    cited_keys = {key(r) for r in runs if r["cited"]}
    cited_by_key = {}
    for r in runs:
        if r["cited"]:
            cited_by_key.setdefault(key(r), []).append(r)

    triaged = []
    for r in runs:
        if r["cited"]:
            continue
        v, why = None, None
        if r["spec"] is None:
            v, why = "base_or_control", "no intervention: a baseline, consumed by whatever cites it"
        elif r.get("n_union", r["n"]) < args.min_analysable:
            v, why = "underpowered", (f"{r.get('n_union', r['n'])} rows (union of "
                                      f"{len(r.get('shards', []))} shard(s)) < {args.min_analysable}")
        elif not any(b in r["bank"] for b in HEADLINE_BANKS):
            v, why = "off_headline_population", f"bank {r['bank']} is not a headline population"
        elif key(r) in cited_keys:
            twin = cited_by_key[key(r)][0]
            gap = (None if (r["asr"] is None or twin["asr"] is None)
                   else round(r["asr"] - twin["asr"], 4))
            v = ("additional_control_draw" if "random" in str(r["spec"]).lower()
                 else "replicate_of_cited")
            why = (f"identical (model, bank, spec) is cited as {twin['judge']}; "
                   f"ASR gap vs that twin = {gap}")
            r["twin"] = twin["judge"]
            r["asr_gap_vs_twin"] = gap
        else:
            v = "COULD_CHANGE"
            why = ("an intervention arm on a headline population whose (model, bank, spec) appears "
                   "in no cited artifact")
        r["verdict"], r["why"] = v, why
        triaged.append(r)

    order = ["COULD_CHANGE", "additional_control_draw", "replicate_of_cited",
             "off_headline_population", "underpowered", "base_or_control"]
    counts = {v: sum(1 for r in triaged if r["verdict"] == v) for v in order}
    could = [r for r in triaged if r["verdict"] == "COULD_CHANGE"]
    reps = [r for r in triaged if r["verdict"] in ("replicate_of_cited", "additional_control_draw")
            and r.get("asr_gap_vs_twin") is not None]
    worst = max((abs(r["asr_gap_vs_twin"]) for r in reps), default=None)

    out = {
        "question": "of the judged runs no committed artifact cites, which could change a conclusion?",
        "why_separate_from_the_inventory":
            "the inventory counts and refuses to editorialise; audit #12 asked which gaps MATTER. "
            "An unanalysed run that could overturn a claim and an unanalysed smoke test are the same "
            "row in a count and opposite things in a report.",
        "min_analysable": args.min_analysable,
        "headline_banks": list(HEADLINE_BANKS),
        "n_judge_runs_done": len(runs),
        "n_uncited": len(triaged),
        "counts": counts,
        "COULD_CHANGE": sorted(could, key=lambda r: (r["bank"], str(r["spec"]))),
        "largest_replicate_asr_gap": worst,
        "replicates": sorted(reps, key=lambda r: -abs(r["asr_gap_vs_twin"]))[:25],
        "all": triaged,
        "caveat": "'COULD_CHANGE' means NOT RULED OUT, not 'is a problem'. It is the shortlist to "
                  "analyse, and it is the only list here that needs action.",
        "screen_that_did_not_fire": (
            "off_headline_population is 0 -- every uncited run is on a headline bank. The screen is "
            "VACUOUS on this data, not passed. Reporting it as a passed check would be a false "
            "assurance; it is kept only so it fires if an off-population run ever appears."),
        "known_blind_spot": (
            "consumption is detected by NAME. A script that builds its tags dynamically -- e.g. "
            "analyze_qwen3_decomposition.py composes `--tag-prefix q3dec_` + arm -- never contains "
            "the literal tag, so its inputs read as unconsumed. That is why the first run of this "
            "script reported 94 COULD_CHANGE and this one reports far fewer: the fix was to also "
            "match the GENERATION tag, but a fully dynamic tag can still evade it. This list is "
            "therefore an OVER-estimate of what is unanalysed, which is the safe direction."),
        "provenance": {"argv": sys.argv, "git_commit": git_commit_safe()},
    }
    for r in runs:
        r.pop("_ids", None)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)

    print(f"judge runs (DONE): {len(runs)}   uncited: {len(triaged)}")
    for v in order:
        print(f"   {v:26s} {counts[v]:>4d}")
    print(f"\nCOULD CHANGE A CONCLUSION ({len(could)}):")
    for r in could:
        print(f"   {r['judge'][:44]:46s} n={r['n']:<5d} asr={r['asr']}  {str(r['spec'])[:46]}")
    if worst is not None:
        print(f"\nlargest replicate ASR gap vs its cited twin: {worst}")
    print(f"\n[triage] -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
