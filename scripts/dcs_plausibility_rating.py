#!/usr/bin/env python
"""dcs_plausibility_rating.py -- `DCS-PR-019`'s external plausibility instrument.

WRITTEN AND COMMITTED BEFORE ANY RATING EXISTS, with the rubric text inline, because `PR-019`
declares "one look, no re-prompting, no rubric revision after seeing rho".

WHY AN EXTERNAL RATER. Every candidate in `R-044` came from Llama's own forward pass on these very
prompts, which is exactly why its two strongest predictors were circular. This asks a DIFFERENT
model, on a prompt that contains no codeword, no demonstrations and no doublespeak frame -- only
the domain name and the concept word.

BATCHED, THREE TIMES, SHUFFLED -- and that is deliberate, not convenient. `PR-019` gates on
reliability before correlating anything, and at temperature 0 a repeated IDENTICAL prompt returns
an identical answer, so a repeat-based gate would be a check that cannot fail
(`feedback_check_reads_same_broken_source`). Shuffling the item order across three batched calls
makes the gate test something real: ORDER SENSITIVITY. The trade-off, stated rather than hidden, is
that a batched rater may rank items against each other instead of rating each independently.

RELIABILITY GATE (declared in `PR-019`, enforced here): if more than 4 of 38 domains have a
max-min spread > 1 point across the three passes, the instrument is UNRELIABLE, the artifact is
stamped CANNOT_ANSWER, and no correlation is computed. The ratings are NOT reported descriptively
as a consolation.

Never runs on the login node -- `feedback_judge_cpu_not_login`.
"""
from __future__ import annotations
import argparse, collections, json, os, random, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA = "DCS_PLAUSIBILITY/1"
MAX_SPREAD = 1
MAX_DOMAINS_OVER = 4
N_PASSES = 3
SEED = 20260904

# THE RUBRIC. Committed with PR-019. It names no codeword, no demonstration, no doublespeak frame,
# and no result -- the rater cannot infer which domains the experiment found interesting.
RUBRIC = """You are rating how physically plausible it is that a particular object is present in a
particular workplace setting, as a matter of ordinary world knowledge. This is a factual
plausibility judgement about everyday environments, not a judgement about anything else.

Rate each setting from 1 to 5 for the object "{concept}":
  1 = it would be extremely surprising to find this object here
  2 = unlikely
  3 = possible but not typical
  4 = plausible
  5 = entirely unremarkable to find this object here

Answer with ONE line per setting, in the order given, formatted exactly as:
<setting name><TAB><integer 1-5>
No commentary, no headings, no blank lines."""


def domains_from_bank(bank: str, block: str) -> tuple[list[str], str]:
    doms, concept = set(), None
    with open(bank, encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("bank_block") != block:
                continue
            doms.add(r["domain"])
            concept = r["concept"]
    if not doms:
        sys.exit(f"REFUSING: no rows in block {block} of {bank}")
    return sorted(doms), concept


def parse(text: str, expected: list[str]) -> dict:
    got = {}
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.replace("\t", "|").rsplit("|", 1)
        if len(parts) != 2:
            parts = line.rsplit(None, 1)
        if len(parts) != 2:
            continue
        name, val = parts[0].strip(), parts[1].strip()
        if name in expected and val.isdigit() and 1 <= int(val) <= 5:
            got[name] = int(val)
    return got


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bank", default=os.path.join(
        ROOT, "data/boombness_prompts/boombness_prompt_bank_cds38_button_bomb.jsonl"))
    ap.add_argument("--block", default="cds_n4")
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--tag", default="dcs_plausibility")
    ap.add_argument("--out", default=os.path.join(ROOT, "outputs/boombness/dcs_analysis"))
    a = ap.parse_args()

    doms, concept = domains_from_bank(a.bank, a.block)
    print(f"[plaus] {len(doms)} domains, concept={concept!r}, model={a.model}, "
          f"{N_PASSES} shuffled passes")

    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        sys.exit("REFUSING: OPENAI_API_KEY not set")
    import urllib.request

    rnd = random.Random(SEED)
    passes, orders = [], []
    for i in range(N_PASSES):
        order = list(doms)
        rnd.shuffle(order)
        orders.append(order)
        body = json.dumps({
            "model": a.model, "temperature": 0, "max_tokens": 900,
            "messages": [{"role": "user", "content":
                          RUBRIC.format(concept=concept) + "\n\nSettings:\n"
                          + "\n".join(order)}]}).encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions", data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = json.load(resp)
        used = payload.get("model", "")
        if not used.startswith(a.model):
            sys.exit(f"REFUSING: asked for {a.model}, response stamped {used!r}")
        got = parse(payload["choices"][0]["message"]["content"], doms)
        missing = [d for d in doms if d not in got]
        if missing:
            sys.exit(f"REFUSING pass {i}: {len(missing)} domains unrated, e.g. {missing[:5]}")
        passes.append(got)
        print(f"[plaus] pass {i}: {len(got)}/{len(doms)} rated, model={used}")

    spread = {d: max(p[d] for p in passes) - min(p[d] for p in passes) for d in doms}
    over = sorted(d for d in doms if spread[d] > MAX_SPREAD)
    mean = {d: sum(p[d] for p in passes) / N_PASSES for d in doms}

    out = {"schema": SCHEMA, "concept": concept, "model": a.model, "n_domains": len(doms),
           "n_passes": N_PASSES, "seed": SEED, "rubric": RUBRIC.format(concept=concept),
           "orders": orders, "passes": passes, "spread": spread,
           "mean_rating": mean,
           "reliability": {"max_spread_allowed": MAX_SPREAD,
                           "max_domains_over_allowed": MAX_DOMAINS_OVER,
                           "n_domains_over": len(over), "domains_over": over,
                           "STATUS": "UNRELIABLE" if len(over) > MAX_DOMAINS_OVER else "OK"}}
    if out["reliability"]["STATUS"] == "UNRELIABLE":
        out["VERDICT"] = ("CANNOT_ANSWER -- PR-019's reliability gate FAILED. The ratings are "
                          "deliberately NOT reported descriptively as a consolation.")
    os.makedirs(a.out, exist_ok=True)
    dst = os.path.join(a.out, f"{a.tag}.json")
    json.dump(out, open(dst, "w"), indent=2, sort_keys=True)
    print(f"[plaus] reliability: {len(over)} of {len(doms)} domains spread > {MAX_SPREAD} "
          f"-> {out['reliability']['STATUS']}")
    print(f"-> {dst}")


if __name__ == "__main__":
    main()
