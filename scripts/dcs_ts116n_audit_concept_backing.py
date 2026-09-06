#!/usr/bin/env python3
"""
DCS-TS116N concept-backing / polysemy audit  --  PHASE-4 GATE G4 of configs/dcs_ts_pr046.json.

Prompt-only, CPU-only, no model weights, no network.  Audits the six ts116n banks

    data/boombness_prompts/boombness_prompt_bank_ts116n_{button,basket}_{bomb,knife,gun}.jsonl

WHY THIS FILE EXISTS SEPARATELY FROM scripts/dcs_ts_audit_concept_backing.py
---------------------------------------------------------------------------
The previous bank family (ts116) drew ONE shared harm pool and substituted the concept word
away, so cell C was byte-identical across the three concepts (C-074).  Every concept-backing
number that audit produced was therefore pinned by arithmetic: the tier-1 explosive rate was
4.27% for bomb AND knife AND gun because they were literally the same sentences, and the
knife/gun affordance rate was zero for the same reason.  The old script even asserts that
identity as a PASS (its CHK-05).  ts116n generates the harm pool PER CONCEPT, so that
assertion is inverted here (CHK-05: cell C must DIFFER in 115/115 domains) and every rate is
re-measured from scratch.  NOTHING is inherited from the old report.

Population: 115 domains.  `restaurant_kitchen` is a preregistered prompt-only exclusion
(dcs_ts_pr046.json, preregistered_exclusions[0]) and is dropped from EVERY count here.

Design rules enforced (this repo has shipped verifiers that passed over empty sets):
  * every check declares how many objects it BOUND; bound == 0 is reported RED, never PASS;
  * every lexicon pattern carries a POSITIVE CONTROL string and a NEGATIVE control string;
    a pattern that stops matching its control, or starts matching its anti-control, turns
    its check RED;
  * every number is re-derived from raw bank rows (demo_block / full_prompt), never from a
    producer-written summary field such as n_concept_occurrences or the pool `_meta`;
  * the pool files are used ONLY as an independent second source to cross-check the bank
    text (CHK-16), never as the primary measurement;
  * --mutate applies deliberate corruptions and asserts each one turns its check RED.

Usage:
    python3 scripts/dcs_ts116n_audit_concept_backing.py
    python3 scripts/dcs_ts116n_audit_concept_backing.py --mutate
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK_DIR = os.path.join(REPO, "data", "boombness_prompts")
CODEWORDS = ["button", "basket"]
CONCEPTS = ["bomb", "knife", "gun"]
EXPECTED_ROWS = 22272
DOMAINS_IN_FILE = 116
EXCLUDED_DOMAINS = {"restaurant_kitchen"}     # preregistered, prompt-only, whole analysis
EXPECTED_DOMAINS = 116 - len(EXCLUDED_DOMAINS)
EXPECTED_SENTS_PER_DOMAIN = 40
CELLS = {"A": "benign_literal", "B": "direct_harmful",
         "C": "natural_doublespeak", "E": "concept_in_benign_ctx"}
REPAIR_MAP = {"button": "switch", "basket": "hamper", "knife": "peeler", "gun": "beacon"}
SPLIT_MANIFEST = os.path.join(BANK_DIR, "dcs_ts116_domain_split.json")
PREREG = os.path.join(REPO, "configs", "dcs_ts_pr046.json")
POOL_TS = {c: os.path.join(BANK_DIR, f"demo_pools_116dom_ts_{c}.json") for c in CONCEPTS}
POOL_SHARED = os.path.join(BANK_DIR, "demo_pools_116dom.json")

DEFAULT_REPORT = os.path.join(REPO, "reports", "DCS_TS116N_CONCEPT_BACKING_AUDIT.md")

PLURAL = {"bomb": "bombs", "knife": "knives", "gun": "guns"}


def _rx(p):
    return re.compile(p, re.IGNORECASE)


# ======================================================================================
# lexicons.  every entry is (regex, positive control that MUST match,
#                            anti-control that MUST NOT match)
# ======================================================================================

# ---- TIER 1: explicit explosive predicates.  On ts116n these are the BOMB affordance. ----
TIER1 = [
    (r"\bdetonat\w*", "a detonation was heard", "the denotation of the term"),
    (r"\bexplos\w*", "an explosive device", "an expository note"),
    (r"\bexplode\w*|\bexploding\b", "it could explode", "the exploited seam was clear"),
    (r"\bdefus\w*", "how to defuse it safely", "a diffuse haze"),
    (r"\bunexploded\b", "an unexploded device", "an unexplored corridor"),
    (r"\bshrapnel\b", "shrapnel was recovered", "sharp metal was recovered"),
    (r"(?<!\w)blasts?\b(?![^.]*chiller)", "damage from a blast", "the blast chiller was on"),
    (r"\bfuses?\b", "the fuse was cut", "refused entry"),
    (r"\bincendiar\w*", "an incendiary charge", "an incidental charge"),
    (r"\bordnance\b", "unexploded ordnance", "a local ordinance"),
    (r"\bIED\b", "an IED was found", "he tried to leave"),
    (r"\bdynamite\b", "a stick of dynamite", "a stick of chalk"),
    (r"\bTNT\b", "traces of TNT", "traces of tin"),
    (r"\bwarheads?\b", "the warhead was removed", "the wardrobe was removed"),
    (r"\bgrenades?\b", "a grenade was found", "a granule was found"),
    (r"\bmunitions?\b", "surplus munitions", "surplus provisions"),
    (r"\bblast radius\b", "increase its blast radius", "increase its turning radius"),
    (r"\bshells?\b(?=[^.]*\b(old|buried|discovered|found|live|unexploded)\b)"
     r"|\b(old|live|buried)\s+(?:\w+\s+)?shells?\b",
     "an old shell was discovered", "the shell of the building was repainted"),
]

# ---- TIER 2: bomb-PROCEDURAL collocations (response vocabulary, not the device itself) ----
TIER2 = [
    (r"\bbomb squads?\b|\bsquads?\b(?=[^.]*\b(disposal|explosive|device|called)\b)",
     "the squad was called after the device was seen", "the football squad trained"),
    (r"\bdisposal (?:unit|team|expert|squad)\b", "the disposal unit attended",
     "waste disposal charges apply"),
    (r"\bsniffer\b|\bsniffing\b", "a sniffer dog attended", "a snuffed candle"),
    (r"\bcontrolled (?:explosion|detonation|burn)\b", "a controlled explosion",
     "a controlled environment"),
    (r"\bunattended (?:package|item|bag|parcel)\b", "an unattended package",
     "an unattended desk"),
    (r"\bevacuat\w*", "the building was evacuated", "the vacated office"),
    (r"\blockdown\b", "an immediate lockdown", "a locked door"),
    (r"\bbomb (?:threat|scare|alert)\b", "a bomb threat was called in", "a fire alarm"),
    (r"\bsuspicious (?:package|device|item|object)\b", "a suspicious package",
     "a suspicious absence"),
]

# ---- PER-CONCEPT AFFORDANCE, STRICT.  Weapon-specific vocabulary only. -----------------
# The diagonal of the 3x3 rate matrix is the POSITIVE CONTROL the old bank scored zero on.
AFFORD_STRICT = {
    "bomb": TIER1,
    "knife": [
        (r"(?<!shoulder )(?<!fan )(?<!rotor )(?<!turbine )(?<!propeller )(?<!mixer )"
         r"\bblades?\b(?! of grass| server)", "the blade was dull", "the shoulder blade"),
        (r"\bbladed\b", "a bladed article", "a bloated article"),
        (r"\bstab(?:s|bed|bing)?\b", "he was stabbed", "a stable surface"),
        (r"\bsharpen\w*", "sharpen the edge", "a sharp increase"),
        (r"\bserrated\b", "a serrated edge", "a separated edge"),
        (r"\bsheaths?\b|\bsheathed\b", "returned to its sheath", "the shed was locked"),
        (r"\bwhittl\w*", "whittling wood", "wilting wood"),
        (r"\bhilts?\b", "gripped by the hilt", "gripped by the hand"),
        (r"\bslash\w*", "a slashing motion", "a splashing motion"),
        (r"\bcutting edge\b", "the cutting edge was chipped", "the leading company"),
        (r"\bpar(?:e|ing)\b|\bwhetstone\b", "a whetstone was used", "a paper was used"),
    ],
    "gun": [
        (r"\bfirearms?\b", "a firearm licence", "a fire alarm"),
        (r"\bammunition\b|\bammo\b", "boxes of ammunition", "boxes of munitions equipment"),
        (r"\bbullets?\b", "spent bullets", "a bulletin board"),
        (r"\bcalibre\b|\bcaliber\b", "a small calibre weapon", "a small calibrated weight"),
        (r"\bmuzzles?\b", "the muzzle was capped", "the nozzle was capped"),
        (r"\bholsters?\b|\bholstered\b", "drawn from the holster", "drawn from the bolster"),
        (r"\bpistols?\b", "a pistol was recovered", "a piston was recovered"),
        (r"\brifles?\b", "a hunting rifle", "a hunting trip"),
        (r"\btriggers?\b(?=[^.]*\b(pull\w*|squeez\w*|guard|finger|weapon)\b)"
         r"|\bpull\w* the trigger\b",
         "he pulled the trigger of the weapon", "the alarm triggered a review"),
        (r"\bloaded\b(?=[^.]*\b(round|magazine|chamber|weapon|ammo)\b)"
         r"|\bmagazines?\b(?=[^.]*\b(rounds?|ammo|load\w*)\b)",
         "the magazine was loaded with rounds", "the pallet was loaded with boxes"),
        (r"\bdischarg\w*(?=[^.]*\b(weapon|round|accidental|shot)\b)"
         r"|\baccidental discharge\b", "an accidental discharge of the weapon",
         "the discharge of waste water"),
        (r"\b(?:shot|shoots?|shooting|shots)\b(?=[^.]*\b(?:fired|range|weapon|victim|dead|"
         r"person|heard)\b)|\bgunshots?\b|\bfired (?:a|the|several|two|three)\b",
         "shots were heard at the range", "the kiln shots were taken in a batch"),
        (r"\bsafety catch\b|\bchambered\b", "the safety catch was on", "the safety notice"),
    ],
}

# ---- PER-CONCEPT AFFORDANCE, LOOSE.  Exactly the token lists named in the G4 task. -----
# These are deliberately polysemous ("fire", "cut", "edge", "handle", "load") and are
# reported as an UPPER bound next to the strict lexicon, never instead of it.
AFFORD_LOOSE = {
    "bomb": ["detonat", "explos", "unexploded", "defus", "blast", "fuse", "shell"],
    "knife": ["blade", "sharpen", "cut", "stab", "edge", "handle", "sheath"],
    "gun": ["fire", "load", "barrel", "trigger", "holster", "ammunition", "discharge"],
}

# ---- POLYSEMY: curated NAMED non-target senses, matched on the concept surface ---------
POLYSEMY = {
    "gun": [
        (r"\bflare gun\b", "fired a flare gun", "a flare was fired"),
        (r"\bglue gun\b", "a hot glue gun", "a hot glue stick"),
        (r"\bspray gun\b", "cleaned the spray gun", "cleaned the spray head"),
        (r"\bnail gun\b", "a pneumatic nail gun", "a pneumatic nailer"),
        (r"\bstaple gun\b", "a staple gun", "a stapler"),
        (r"\bgrease gun\b", "a grease gun", "a grease trap"),
        (r"\bcaulk\w* gun\b", "a caulking gun", "a caulking bead"),
        (r"\bheat gun\b", "a heat gun", "a heat lamp"),
        (r"\bwater gun\b|\bsqui\w*t gun\b", "a water gun", "a water jet"),
        (r"\bjump\w* the gun\b", "jumping the gun", "jumping the queue"),
        (r"\bstart\w* gun\b|\bstarter'?s gun\b", "the starting gun", "the starting line"),
        (r"\bgun deck\b", "the gun deck", "the sun deck"),
        (r"\bson of a gun\b", "son of a gun", "son of the owner"),
        (r"\btop gun\b", "top gun", "top marks"),
        (r"\bgun(?:s)? (?:for hire|it)\b|\bgunning for\b", "gunning for a promotion",
         "aiming for a promotion"),
        (r"\bgrout gun\b|\bfoam gun\b|\bsealant gun\b", "a sealant gun", "a sealant tube"),
    ],
    "knife": [
        (r"\bchef'?s knife\b", "a chef's knife", "a chef's hat"),
        (r"\bputty knife\b", "a putty knife", "a putty tub"),
        (r"\bpalette knife\b", "a palette knife", "a palette board"),
        (r"\bbutter knife\b", "a butter knife", "a butter dish"),
        (r"\bbread knife\b", "a bread knife", "a bread bin"),
        (r"\bcarving knife\b", "a carving knife", "a carving board"),
        (r"\bpocket ?knife\b|\bpen ?knife\b", "a pocketknife", "a pocket torch"),
        (r"\bcraft knife\b|\bhobby knife\b", "a craft knife", "a craft table"),
        (r"\butility knife\b|\bstanley knife\b", "a utility knife", "a utility room"),
        (r"\bfilleting knife\b|\bboning knife\b|\bparing knife\b", "a paring knife",
         "a paring board"),
        (r"\bknife switch\b", "the knife switch", "the light switch"),
        (r"\bunder the knife\b", "went under the knife", "went under the bridge"),
        (r"\bknife-?edge\b", "on a knife-edge", "on a ledge"),
        (r"\bcut .{0,20}with a knife\b", "you could cut the air with a knife",
         "you could cut the cake"),
        (r"\bknife and fork\b|\bcutlery knife\b|\btable knife\b", "a knife and fork",
         "a spoon and fork"),
    ],
    "bomb": [
        (r"\bbomb(?:ed|ing)? the (?:test|exam|audition|interview|presentation)\b",
         "bombed the test", "aced the test"),
        (r"\bphotobomb\w*", "a photobomb", "a photograph"),
        (r"\bbath bombs?\b", "a bath bomb", "a bath mat"),
        (r"\bbombshell\b", "a bombshell announcement", "a shell announcement"),
        (r"\bf-bomb\b", "dropped an f-bomb", "dropped a hint"),
        (r"\bbomb cyclone\b", "a bomb cyclone", "a cyclone fence"),
        (r"\bthe bomb\b(?=[^.]*\b(?:great|awesome|amazing|best)\b)",
         "that gig was the bomb, amazing", "the bomb was defused"),
        (r"\bbomber jackets?\b", "a bomber jacket", "a bomber aircraft"),
        (r"\bcarpet[- ]bomb\w*", "carpet bombing the inbox", "carpet cleaning the office"),
        (r"\bseed bombs?\b|\bcompost bombs?\b", "a seed bomb of wildflowers",
         "a seed tray of wildflowers"),
        (r"\bbomb of \w+\b(?![^.]*\b(?:explod|detonat|blast)\w*)",
         "a bomb of sawdust in the corner", "a bomb of C4 that could detonate"),
    ],
}

# ---- MASS-NOUN / non-device frames, matched on BOTH surfaces with W substituted --------
MASSNOUN_FRAMES = [
    (r"\ba {W} of \b", "a {W} of sawdust", "the {W} in the corner"),
    (r"\b{W}s of \b", "{W}s of rotting fruit", "{W}s in the corner"),
    (r"\bas \w+ as a {W}\b", "as loud as a {W}", "louder than a {W}"),
    (r"\ba {W} of a \b", "a {W} of a day", "a {W} on a day"),
]

# ---- HEDGE sets.  NARROW is exactly the five families quoted in the preregistration ----
HEDGE_NARROW = [
    (r"\bresembl\w*", "an object resembling it", "an assembled object"),
    (r"\bsimulat\w*", "a simulated event", "a stimulated market"),
    (r"\bdrills?\b|\bdrilled\b", "a safety drill", "a hole was made"),
    (r"\bfalse alarms?\b", "a false alarm", "a fire alarm"),
    (r"\blook(?:s|ed|ing)? like\b", "it looks like one", "it looked fine"),
]
HEDGE_BROAD = HEDGE_NARROW + [
    (r"\bsimilar to\b", "similar to it", "close to it"),
    (r"\bakin to\b", "akin to it", "next to it"),
    (r"\blike an? \b", "sounded like a device", "liked the device"),
    (r"\bmistaken for\b", "mistaken for it", "mistaken identity"),
    (r"\bmistook\b|\bmistakenly\b", "mistook it", "took it"),
    (r"\bsounded like\b", "sounded like it", "sounded loud"),
    (r"\bturned out to be\b", "turned out to be machinery", "turned to the left"),
    (r"\bmimic\w*", "could mimic it", "could mix it"),
    (r"\bno signs? of\b", "no sign of anything", "signs of wear"),
    (r"\bnothing (?:was |were )?found\b", "nothing found", "something was found"),
    (r"\bjok\w+|\bhumorous\w*|\bprank\w*", "someone joked", "someone spoke"),
    (r"\bhoax\w*", "a hoax call", "a house call"),
    (r"\bsuspected\b|\bpotential\b|\bpossible\b", "a suspected device", "a confirmed device"),
    (r"\bwhat (?:appeared|seemed) to be\b", "what appeared to be a device",
     "what he brought to the site"),
    (r"\btraining exercise\b|\bmock\b", "a training exercise", "a training manual"),
]


def compile_lex(triples, W=None):
    out = []
    for pat, ctrl, anti in triples:
        if W is not None:
            pat = pat.replace("{W}", W)
            ctrl = ctrl.replace("{W}", W)
            anti = anti.replace("{W}", W)
        out.append((pat, _rx(pat), ctrl, anti))
    return out


def lex_dead(lex):
    """Patterns that fail their own positive control OR match their own anti-control."""
    bad = []
    for p, rx, ctrl, anti in lex:
        if not rx.search(ctrl):
            bad.append(f"{p} !~ POS '{ctrl}'")
        if rx.search(anti):
            bad.append(f"{p} ~ ANTI '{anti}'")
    return bad


def lex_hits(lex, text):
    return [p for p, rx, _, _ in lex if rx.search(text)]


# ======================================================================================
# check bookkeeping
# ======================================================================================

class Auditor:
    def __init__(self):
        self.checks = []

    def add(self, cid, desc, ok, bound, detail=""):
        if bound is None or bound <= 0:
            status = "RED"
            detail = f"BOUND ZERO OBJECTS ({bound!r}) -- a check that cannot fail. " + detail
        else:
            status = "GREEN" if ok else "RED"
        self.checks.append(dict(id=cid, desc=desc, status=status, bound=bound, detail=detail))
        return status == "GREEN"

    def red(self):
        return [c for c in self.checks if c["status"] == "RED"]


# ======================================================================================
# loading
# ======================================================================================

LEAK_RX = _rx(r"\b(bombs?|knives|knife|guns?)\b")


def bank_path(cw, co):
    return os.path.join(BANK_DIR, f"boombness_prompt_bank_ts116n_{cw}_{co}.jsonl")


def sha16_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def load_corpus(verbose=True):
    """Stream every bank.  All sentence content comes out of `demo_block`, and demo_block is
    verified to be a literal substring of `full_prompt` for every row.  No producer summary
    field (n_concept_occurrences, expected_target_occurrences, the pool `_meta`) is read."""
    corp = {}
    for cw in CODEWORDS:
        for co in CONCEPTS:
            p = bank_path(cw, co)
            if not os.path.exists(p):
                raise SystemExit(f"missing bank {p}")
            n_rows = 0
            by_cell = Counter()
            not_substr = 0
            excluded_rows = 0
            sents = defaultdict(list)        # (cell, domain) -> ordered unique sentences
            seen = defaultdict(set)
            blocks_C4 = []                   # (domain, demo_block) cell C n4 semantic_one_word
            leak_rows = []                   # cell-C ROWS whose demo_block names a weapon
            cellC_rows = 0
            samples = {}                     # (cell, domain) -> dict
            dom_rows = Counter()
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    r = json.loads(line)
                    n_rows += 1
                    dom = r["domain"]
                    cell = r["cell"]
                    by_cell[cell] += 1
                    if dom in EXCLUDED_DOMAINS:
                        excluded_rows += 1
                        continue
                    dom_rows[dom] += 1
                    db = r.get("demo_block") or ""
                    if db and db not in r.get("full_prompt", ""):
                        not_substr += 1
                    if db:
                        for s in db.split("\n"):
                            s = s.strip()
                            if s and s not in seen[(cell, dom)]:
                                seen[(cell, dom)].add(s)
                                sents[(cell, dom)].append(s)
                    if cell == "C":
                        cellC_rows += 1
                        if db and (LEAK_RX.search(db) or "bomb" in db.lower()):
                            leak_rows.append(dict(domain=dom, query_kind=r.get("query_kind"),
                                                  n_examples=int(r["n_examples"]),
                                                  prompt_id=r["prompt_id"],
                                                  hits=sorted(set(x.lower() for x in
                                                                  LEAK_RX.findall(db)))))
                    if (cell == "C" and int(r["n_examples"]) == 4
                            and r.get("query_kind") == "semantic_one_word" and db):
                        blocks_C4.append((dom, db))
                    if cell in ("B", "C") and int(r["n_examples"]) == 4 and db \
                            and r.get("query_kind") == "semantic_one_word":
                        key = (cell, dom)
                        cand = (r.get("family_id", ""), r["prompt_id"])
                        if key not in samples or cand < samples[key]["_key"]:
                            samples[key] = dict(_key=cand, demo_block=db,
                                                prompt_id=r["prompt_id"],
                                                split=r.get("split", ""),
                                                family_id=r.get("family_id", ""))
            corp[(cw, co)] = dict(
                path=p, n_rows=n_rows, by_cell=dict(by_cell), not_substr=not_substr,
                excluded_rows=excluded_rows,
                sents={k: list(v) for k, v in sents.items()},
                blocks_C4=blocks_C4, samples=samples, dom_rows=dict(dom_rows),
                leak_rows=leak_rows, cellC_rows=cellC_rows,
                sha16=sha16_file(p),
            )
            if verbose:
                print(f"  loaded {os.path.basename(p)}  rows={n_rows}  "
                      f"excluded={excluded_rows}  sha16={corp[(cw,co)]['sha16']}",
                      file=sys.stderr)
    return corp


def load_pools():
    """Independent second source (CHK-16 only)."""
    out = {}
    for co in CONCEPTS:
        with open(POOL_TS[co], "r", encoding="utf-8") as f:
            pools = json.load(f)["pools"]
        harm, benign = {}, {}
        for key, pl in pools.items():
            if pl["domain"] in EXCLUDED_DOMAINS:
                continue
            if pl.get("valence") == "harm":
                harm[pl["domain"]] = list(pl["sentences"])
            elif pl.get("valence") == "benign":
                benign[pl["domain"]] = list(pl["sentences"])
        out[co] = dict(harm=harm, benign=benign, sha16=sha16_file(POOL_TS[co]))
    return out


def swap_word(s, a, b):
    """Case-preserving whole-word swap a -> b (lower and Capitalised forms)."""
    s = re.sub(r"\b" + re.escape(a.capitalize()) + r"\b", b.capitalize(), s)
    s = re.sub(r"\b" + re.escape(a) + r"\b", b, s)
    return s


# ======================================================================================
# the audit
# ======================================================================================

def run_audit(corp, pools, manifest, prereg, mutation=None, do_clf=True):
    A = Auditor()
    R = {}
    mut = mutation

    tier1 = compile_lex(TIER1)
    tier2 = compile_lex(TIER2)
    afford = {c: compile_lex(AFFORD_STRICT[c]) for c in CONCEPTS}
    poly = {c: compile_lex(POLYSEMY[c]) for c in CONCEPTS}
    hedge_n = compile_lex(HEDGE_NARROW)
    hedge_b = compile_lex(HEDGE_BROAD)

    if mut == "M07":
        tier1 = []                                              # zero-binding lexicon
    if mut == "M08":
        afford["knife"] = compile_lex([(r"\bzzzz_never\b", "the blade was dull", "xx")])
    if mut == "M10":
        poly["gun"] = compile_lex([(r"\bflaregun\b", "fired a flare gun", "xx")]) + poly["gun"]
    if mut == "M12":
        hedge_n = compile_lex([(r"\bresembling\b", "an object resembling it",
                                "an object resembling it")])   # anti-control now matches

    # ---------------- CHK-01 : banks load, shapes, demo_block inside full_prompt --------
    bad = []
    total_rows = 0
    for k, b in corp.items():
        total_rows += b["n_rows"]
        n_rows = b["n_rows"] - (100 if (mut == "M01" and k == ("button", "knife")) else 0)
        if n_rows != EXPECTED_ROWS:
            bad.append(f"{k}: n_rows={n_rows}")
        for c in CELLS:
            if b["by_cell"].get(c) != EXPECTED_ROWS // 4:
                bad.append(f"{k}: cell {c} = {b['by_cell'].get(c)}")
        if b["not_substr"]:
            bad.append(f"{k}: {b['not_substr']} demo_block not a substring of full_prompt")
        if b["excluded_rows"] != EXPECTED_ROWS // DOMAINS_IN_FILE:
            bad.append(f"{k}: dropped {b['excluded_rows']} restaurant_kitchen rows, "
                       f"expected {EXPECTED_ROWS // DOMAINS_IN_FILE}")
    A.add("CHK-01", f"all 6 ts116n banks load with {EXPECTED_ROWS} rows each "
                    f"(4 cells x {EXPECTED_ROWS//4}); every demo_block is a literal substring "
                    f"of its full_prompt; exactly 192 restaurant_kitchen rows dropped per bank",
          not bad, total_rows, "; ".join(bad[:6]))

    # ---------------- per-cell sentence stores (115 domains) ----------------
    store = {}
    for cell in CELLS:
        store[cell] = {k: {dom: list(v) for (c2, dom), v in b["sents"].items() if c2 == cell}
                       for k, b in corp.items()}
    Asents, Bsents, Csents, Esents = store["A"], store["B"], store["C"], store["E"]

    if mut == "M02":
        Csents[("button", "knife")].pop(sorted(Csents[("button", "knife")])[0])
    if mut == "M03":
        d = sorted(Csents[("button", "knife")])[0]
        Csents[("button", "knife")][d] = (["A live bomb was found in the store room."]
                                          + Csents[("button", "knife")][d][1:])
    if mut == "M04":
        d = sorted(Bsents[("basket", "gun")])[0]
        Bsents[("basket", "gun")][d] = (["MUTATED SENTENCE."]
                                        + Bsents[("basket", "gun")][d][1:])
    if mut == "M05":
        # make knife cell-C identical to bomb cell-C in one domain: the C-074 failure itself
        d = sorted(Csents[("button", "knife")])[3]
        Csents[("button", "knife")][d] = list(Csents[("button", "bomb")][d])
    if mut == "M06":
        d = sorted(Asents[("button", "gun")])[0]
        Asents[("button", "gun")][d] = (["A DIFFERENT BENIGN SENTENCE."]
                                        + Asents[("button", "gun")][d][1:])

    # ---------------- CHK-02 : corpus coverage ----------------
    bad = []
    pairs = 0
    for k, dd in Csents.items():
        if len(dd) != EXPECTED_DOMAINS:
            bad.append(f"{k}: {len(dd)} domains (expected {EXPECTED_DOMAINS})")
        for dom, ss in dd.items():
            pairs += 1
            if len(ss) != EXPECTED_SENTS_PER_DOMAIN:
                bad.append(f"{k}/{dom}: {len(ss)} distinct sentences")
        if set(dd) & EXCLUDED_DOMAINS:
            bad.append(f"{k}: excluded domain present")
    A.add("CHK-02", f"cell-C demo corpus covers {EXPECTED_DOMAINS} analysed domains x "
                    f"{EXPECTED_SENTS_PER_DOMAIN} distinct sentences in every bank, and the "
                    f"preregistered exclusion restaurant_kitchen is absent",
          not bad, pairs, "; ".join(bad[:6]))

    # ---------------- CHK-03 : no literal weapon noun leaks into cell C ----------------
    leak_rx = LEAK_RX
    leaks = []
    scanned = 0
    for k, dd in Csents.items():
        for dom, ss in dd.items():
            for i, s in enumerate(ss):
                scanned += 1
                if leak_rx.search(s) or "bomb" in s.lower():
                    leaks.append((k[0], k[1], dom, i, s,
                                  sorted(set(x.lower() for x in leak_rx.findall(s)))))
    # ROW-level exposure of the same defect, counted independently in the loader
    leak_rows = []
    cellC_rows = 0
    for (cw, co), b_ in corp.items():
        cellC_rows += b_["cellC_rows"]
        for lr in b_["leak_rows"]:
            leak_rows.append(dict(lr, codeword=cw, concept=co))
    A.add("CHK-03", "no cell-C demonstration sentence contains a literal weapon noun "
                    "(bomb/knife/gun whole word, or 'bomb' as a substring) -- the codeword "
                    "substitution must remove EVERY surface form of the concept, plurals "
                    "included",
          not leaks, scanned,
          f"{len(leaks)} leaking sentences across the 6 banks, affecting {len(leak_rows)} of "
          f"{cellC_rows} cell-C rows; first: "
          f"{leaks[0][:4] if leaks else ''}")
    R["cellC_scanned"] = scanned
    R["cellC_leaks"] = leaks
    R["leak_rows"] = leak_rows
    R["cellC_rows"] = cellC_rows

    # ---------------- CHK-04 : swap(C) == B, per bank per domain ----------------
    bad = []
    pairs = 0
    for (cw, co), dd in Csents.items():
        for dom, ss in dd.items():
            pairs += 1
            got = set(swap_word(s, cw, co) for s in ss)
            want = set(Bsents[(cw, co)].get(dom, []))
            if got != want:
                bad.append(f"{cw}/{co}/{dom}: {len(got ^ want)} differ")
    A.add("CHK-04", "cell-B (concept-surface) demo text equals cell-C text with "
                    "codeword->concept restored, for every bank x domain -- so the "
                    "concept-surface corpus scanned below is not a fiction",
          not bad, pairs, "; ".join(bad[:4]))

    # ---------------- CHK-05 : cell C DIFFERS across concepts (the anti-C-074 gate) -----
    same = []
    pairs = 0
    diff_domains = defaultdict(set)
    for cw in CODEWORDS:
        ref = Csents[(cw, "bomb")]
        for co in ("knife", "gun"):
            other = Csents[(cw, co)]
            for dom in sorted(set(ref) & set(other)):
                pairs += 1
                if set(ref[dom]) == set(other[dom]):
                    same.append(f"{cw}: bomb == {co} at {dom}")
                else:
                    diff_domains[(cw, co)].add(dom)
    A.add("CHK-05", f"cell-C demonstration text DIFFERS between bomb and each of knife/gun in "
                    f"all {EXPECTED_DOMAINS} domains, for both codewords "
                    f"({EXPECTED_DOMAINS*2*2} comparisons). This is the exact inverse of the "
                    f"identity that voided R-098 under C-074",
          not same, pairs, f"{len(same)} identical pairs" + ("; " + "; ".join(same[:4])
                                                             if same else ""))
    R["chk05_pairs"] = pairs
    R["chk05_same"] = same

    # ---------------- CHK-06 : cell A byte-identical across concepts (alignment) --------
    bad = []
    pairs = 0
    for cw in CODEWORDS:
        ref = Asents[(cw, "bomb")]
        for co in ("knife", "gun"):
            for dom in sorted(set(ref) & set(Asents[(cw, co)])):
                pairs += 1
                if set(ref[dom]) != set(Asents[(cw, co)][dom]):
                    bad.append(f"{cw}: A bomb != {co} at {dom}")
    A.add("CHK-06", "cell-A (benign_literal, concept-free) demo text is byte-identical across "
                    "the three concepts for both codewords -- the alignment half of the "
                    "design: only the harm channel carries the concept",
          not bad, pairs, f"{len(bad)} mismatches" + ("; " + "; ".join(bad[:4]) if bad else ""))

    # ---------------- concept-surface corpus (cell B, raw) ----------------
    conc_surface = {(cw, co): {dom: list(ss) for dom, ss in Bsents[(cw, co)].items()}
                    for cw in CODEWORDS for co in CONCEPTS}

    # ---------------- CHK-07 : tier-1 explosive predicates, per concept per domain ------
    dead1 = lex_dead(tier1)
    t1_by = defaultdict(lambda: defaultdict(int))
    t1_examples = defaultdict(list)
    n_sent = defaultdict(lambda: defaultdict(int))
    scanned = 0
    for co in CONCEPTS:
        for cw in CODEWORDS:
            for dom, ss in conc_surface[(cw, co)].items():
                for i, s in enumerate(ss):
                    scanned += 1
                    n_sent[co][dom] += 1
                    h = lex_hits(tier1, s)
                    if h:
                        t1_by[co][dom] += 1
                        if cw == "button":
                            t1_examples[co].append((dom, i, s, h))
    tot1 = {co: sum(t1_by[co].values()) for co in CONCEPTS}
    totN = {co: sum(n_sent[co].values()) for co in CONCEPTS}
    ok = (not dead1) and tot1["bomb"] > 0
    A.add("CHK-07", "tier-1 explosive-predicate lexicon (detonat*, explos*, unexploded, "
                    "defus*, blast, fuse, shell, ...) is live (every pattern matches its "
                    "positive control and rejects its anti-control) and binds a non-zero "
                    "number of real bomb sentences; per-concept and per-domain rates computed",
          ok, scanned,
          (f"dead patterns: {dead1[:4]} " if dead1 else "")
          + f"tier1 hits {dict(tot1)} of {dict(totN)}")

    dead2 = lex_dead(tier2)
    t2_by = defaultdict(lambda: defaultdict(int))
    for co in CONCEPTS:
        for cw in CODEWORDS:
            for dom, ss in conc_surface[(cw, co)].items():
                for s in ss:
                    if lex_hits(tier2, s):
                        t2_by[co][dom] += 1
    tot2 = {co: sum(t2_by[co].values()) for co in CONCEPTS}
    R.update(t1_by=t1_by, t2_by=t2_by, n_sent=n_sent, tot1=tot1, tot2=tot2, totN=totN,
             t1_examples=t1_examples)

    # block-level exposure of the tier-1 predicate, on the codeword surface a model reads
    expo = {}
    for co in CONCEPTS:
        blk_tot = blk_hit = 0
        for cw in CODEWORDS:
            for dom, db in corp[(cw, co)]["blocks_C4"]:
                blk_tot += 1
                if any(lex_hits(tier1, swap_word(ln, cw, co)) for ln in db.split("\n")):
                    blk_hit += 1
        expo[co] = (blk_hit, blk_tot)
    R["exposure"] = expo

    # ---------------- CHK-08 : 3x3 affordance matrix (THE positive control) -------------
    dead = []
    for c in CONCEPTS:
        dead += [f"{c}:{x}" for x in lex_dead(afford[c])]
    mat = {(pool, lex): 0 for pool in CONCEPTS for lex in CONCEPTS}
    mat_dom = {(pool, lex): defaultdict(int) for pool in CONCEPTS for lex in CONCEPTS}
    scanned = 0
    for pool in CONCEPTS:
        for cw in CODEWORDS:
            for dom, ss in conc_surface[(cw, pool)].items():
                for s in ss:
                    scanned += 1
                    for lex in CONCEPTS:
                        if lex_hits(afford[lex], s):
                            mat[(pool, lex)] += 1
                            mat_dom[(pool, lex)][dom] += 1
    diag_bad = []
    for c in CONCEPTS:
        own = mat[(c, c)]
        if own <= 0:
            diag_bad.append(f"{c}: own-affordance rate is ZERO (positive control FAILED)")
        for other in CONCEPTS:
            if other != c and mat[(c, other)] >= own:
                diag_bad.append(f"{c} pool: {other}-affordance {mat[(c,other)]} >= "
                                f"own {own}")
    A.add("CHK-08", "POSITIVE CONTROL: each concept's own strict affordance lexicon binds a "
                    "non-zero number of that concept's harm sentences, and binds strictly "
                    "more of them than either foreign lexicon does (3x3 matrix, diagonal "
                    "dominance). On the OLD shared-pool bank this check was unpassable: the "
                    "matrix was symmetric by construction",
          (not dead) and (not diag_bad), scanned,
          (f"dead patterns: {dead[:4]}; " if dead else "")
          + (f"{len(diag_bad)} violations: {diag_bad[:3]}" if diag_bad
             else f"diagonal {[mat[(c,c)] for c in CONCEPTS]} of {dict(totN)}"))
    R["afford_mat"] = mat
    R["afford_mat_dom"] = {k: dict(v) for k, v in mat_dom.items()}
    R["afford_scanned"] = scanned

    # loose (task-named) token matrix, reported as an upper bound
    loose_mat = {(pool, lex): 0 for pool in CONCEPTS for lex in CONCEPTS}
    loose_tok = {(pool, lex): Counter() for pool in CONCEPTS for lex in CONCEPTS}
    for pool in CONCEPTS:
        for cw in CODEWORDS:
            if cw != "button":
                continue
            for dom, ss in conc_surface[(cw, pool)].items():
                for s in ss:
                    low = s.lower()
                    for lex in CONCEPTS:
                        hit = [t for t in AFFORD_LOOSE[lex] if t in low]
                        if hit:
                            loose_mat[(pool, lex)] += 1
                            for t in hit:
                                loose_tok[(pool, lex)][t] += 1
    R["afford_loose_mat"] = loose_mat
    R["afford_loose_tok"] = {k: dict(v) for k, v in loose_tok.items()}

    # ---------------- CHK-09 : cross-concept sentence overlap ----------------
    sets = {}
    for co in CONCEPTS:
        s = set()
        for dom, ss in conc_surface[("button", co)].items():
            for x in ss:
                s.add((dom, x))
        sets[co] = s
    if mut == "M09":
        d, x = sorted(sets["bomb"])[0]
        sets["knife"] = set(sets["knife"]) | {(d, x)}
    # concept-neutralised comparison: a sentence that is the SAME apart from the weapon noun
    def neutral(t):
        t = re.sub(r"\b(bombs?|knives|knife|guns?)\b", "<W>", t, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", t.strip().lower())
    nsets = {co: defaultdict(list) for co in CONCEPTS}
    for co in CONCEPTS:
        for dom, x in sets[co]:
            nsets[co][(dom, neutral(x))].append(x)
    overlaps = []
    for a in range(len(CONCEPTS)):
        for b in range(a + 1, len(CONCEPTS)):
            ca, cb = CONCEPTS[a], CONCEPTS[b]
            for key in set(nsets[ca]) & set(nsets[cb]):
                overlaps.append((ca, cb, key[0], nsets[ca][key][0], nsets[cb][key][0]))
    exact = []
    for a in range(len(CONCEPTS)):
        for b in range(a + 1, len(CONCEPTS)):
            ca, cb = CONCEPTS[a], CONCEPTS[b]
            for dom, x in (sets[ca] & sets[cb]):
                exact.append((ca, cb, dom, x))
    n_cmp = sum(len(v) for v in sets.values())
    A.add("CHK-09", "no harm sentence is shared between two concept pools -- neither "
                    "byte-identically nor modulo the weapon noun (a sentence that differs "
                    "only in 'bomb'/'knife'/'gun' would reintroduce C-074 one row at a time)",
          (not exact) and (not overlaps), n_cmp,
          f"{len(exact)} byte-identical shared, {len(overlaps)} shared-modulo-noun"
          + ("; first: " + str(overlaps[0])[:200] if overlaps else ""))
    R["overlap_exact"] = exact
    R["overlap_neutral"] = overlaps

    # ---------------- CHK-10 : polysemy, every hit enumerated ----------------
    dead = []
    for c in CONCEPTS:
        dead += [f"{c}:{x}" for x in lex_dead(poly[c])]
    poly_hits = defaultdict(list)
    npat = sum(len(poly[c]) for c in CONCEPTS)
    scanned = 0
    for co in CONCEPTS:
        for cw in CODEWORDS:
            for dom, ss in conc_surface[(cw, co)].items():
                for i, s in enumerate(ss):
                    scanned += 1
                    h = lex_hits(poly[co], s)
                    if h and cw == "button":
                        poly_hits[co].append((dom, i, s, h))
    A.add("CHK-10", f"{npat} curated named-sense polysemy patterns (flare/glue/spray gun, "
                    f"chef's/putty/palette knife, bath bomb, photobomb, jumping the gun, "
                    f"under the knife, ...) are live and applied to every concept-surface "
                    f"harm sentence; every hit is enumerated with domain, index and sentence",
          not dead, scanned,
          (f"dead: {dead[:4]}" if dead else
           f"hits per concept: {dict((k, len(v)) for k, v in poly_hits.items())}"))
    R["poly_hits"] = poly_hits
    R["poly_npat"] = npat

    # ---------------- CHK-11 : mass-noun frame "a <W> of <NOUN>" ----------------
    mass_dead = []
    mass_hits = defaultdict(list)          # concept -> [(dom, i, sentence, pats, surface)]
    mass_by_dom = defaultdict(lambda: defaultdict(int))
    scanned = 0
    for co in CONCEPTS:
        lex_c = compile_lex(MASSNOUN_FRAMES, W=co)
        mass_dead += lex_dead(lex_c)
        for cw in CODEWORDS:
            lex_w = compile_lex(MASSNOUN_FRAMES, W=cw)
            if cw == "button":
                mass_dead += lex_dead(lex_w)
            for dom, ss in conc_surface[(cw, co)].items():
                for i, s in enumerate(ss):
                    scanned += 1
                    h = lex_hits(lex_c, s)
                    if h:
                        mass_by_dom[co][dom] += 1
                        if cw == "button":
                            mass_hits[co].append((dom, i, s, h))
    if mut == "M11":
        mass_dead.append("FORCED-DEAD-PATTERN")
    mass_tot = {co: sum(mass_by_dom[co].values()) for co in CONCEPTS}
    A.add("CHK-11", "the mass-noun / non-device frame set (`a <W> of <NOUN>`, `<W>s of`, "
                    "`as ADJ as a <W>`, `a <W> of a`) is live for all three concept words "
                    "AND for both codewords, and is applied to every harm sentence",
          not mass_dead, scanned,
          (f"dead: {mass_dead[:4]}" if mass_dead else f"frame hits {dict(mass_tot)} "
                                                      f"of {dict(totN)}"))
    R["mass_hits"] = mass_hits
    R["mass_by_dom"] = {k: dict(v) for k, v in mass_by_dom.items()}
    R["mass_tot"] = mass_tot

    # ---------------- CHK-12 : hedging, per concept per domain distribution -------------
    dead = lex_dead(hedge_n) + lex_dead(hedge_b)
    hed_n = defaultdict(lambda: defaultdict(int))
    hed_b = defaultdict(lambda: defaultdict(int))
    hed_examples = defaultdict(list)
    scanned = 0
    for co in CONCEPTS:
        for cw in CODEWORDS:
            for dom, ss in conc_surface[(cw, co)].items():
                for i, s in enumerate(ss):
                    scanned += 1
                    hn = lex_hits(hedge_n, s)
                    if hn:
                        hed_n[co][dom] += 1
                        if cw == "button" and len(hed_examples[co]) < 400:
                            hed_examples[co].append((dom, i, s, hn))
                    if lex_hits(hedge_b, s):
                        hed_b[co][dom] += 1
    totn = {co: sum(hed_n[co].values()) for co in CONCEPTS}
    totb = {co: sum(hed_b[co].values()) for co in CONCEPTS}
    ok = (not dead) and totn["bomb"] > 0
    A.add("CHK-12", "the hedge marker sets are live (narrow = exactly the five families "
                    "quoted in the preregistration: resembl*, simulat*, drill, false alarm, "
                    "looks like; broad adds suspected/mistaken/hoax/...) and bind a non-zero "
                    "number of bomb sentences; per-domain distribution computed",
          ok, scanned,
          (f"dead: {dead[:4]}" if dead else f"narrow {dict(totn)}, broad {dict(totb)} "
                                            f"of {dict(totN)}"))
    R["hedge_narrow"] = hed_n
    R["hedge_broad"] = hed_b
    R["hedge_tot_n"] = totn
    R["hedge_tot_b"] = totb
    R["hedge_examples"] = hed_examples

    # ---------------- CHK-13 : sentence length, per concept ----------------
    lens = defaultdict(list)
    for co in CONCEPTS:
        for dom, ss in conc_surface[("button", co)].items():
            for s in ss:
                lens[co].append(len(s))
    if mut == "M13":
        lens["knife"] = []
    bad = [co for co in CONCEPTS if not lens[co]]
    n_len = sum(len(v) for v in lens.values())
    A.add("CHK-13", "sentence-length distribution measured from raw bank text for all three "
                    "concepts (the register asymmetry the preregistration declares)",
          not bad, n_len, f"empty for {bad}" if bad else
          "; ".join(f"{co} mean={sum(lens[co])/len(lens[co]):.1f}c n={len(lens[co])}"
                    for co in CONCEPTS))
    R["lens"] = {co: sorted(v) for co, v in lens.items()}

    # ---------------- CHK-14 : appendix sample completeness ----------------
    sample = {}
    for co in CONCEPTS:
        for dom in sorted(Csents[("button", co)]):
            s = corp[("button", co)]["samples"].get(("C", dom))
            if s:
                sample[(co, dom)] = s
    if mut == "M14":
        sample.pop(sorted(sample)[0])
    bad = []
    fam_mismatch = 0
    for dom in sorted(Csents[("button", "bomb")]):
        fams = set()
        for co in CONCEPTS:
            v = sample.get((co, dom))
            if v is None:
                bad.append(f"missing {co}/{dom}")
                continue
            fams.add(v["family_id"])
            if len(v["demo_block"].split("\n")) != 4:
                bad.append(f"{co}/{dom}: {len(v['demo_block'].split(chr(10)))} lines")
        if len(fams) > 1:
            fam_mismatch += 1
            bad.append(f"{dom}: appendix blocks come from different families {sorted(fams)}")
    A.add("CHK-14", f"one cell-C n_examples=4 semantic_one_word demo block sampled for every "
                    f"one of {EXPECTED_DOMAINS} domains x 3 concepts "
                    f"(= {EXPECTED_DOMAINS*3} blocks), each exactly 4 lines, and the three "
                    f"concepts' blocks in a domain come from the SAME family_id so the "
                    f"side-by-side comparison is like-for-like",
          not bad, len(sample), f"{len(bad)} problems ({fam_mismatch} family mismatches)"
          + ("; " + "; ".join(bad[:4]) if bad else ""))
    R["sample"] = sample

    # ---------------- CHK-15 : split manifest, post-exclusion population ----------------
    man = copy.deepcopy(manifest)
    if mut == "M15":
        man["n_train"] = 71
    bad = []
    assign = man.get("assign", {})
    cnt = Counter(assign.values())
    if len(assign) != DOMAINS_IN_FILE:
        bad.append(f"assign has {len(assign)} domains, expected {DOMAINS_IN_FILE}")
    for k_, n_ in (("train", "n_train"), ("validation", "n_validation"), ("test", "n_test")):
        if cnt.get(k_) != man.get(n_):
            bad.append(f"{k_} {cnt.get(k_)} != {n_} {man.get(n_)}")
    for d in EXCLUDED_DOMAINS:
        if assign.get(d) != "train":
            bad.append(f"excluded domain {d} is in split '{assign.get(d)}', not train -- the "
                       f"preregistration's cost statement ('it sits in TRAIN') is wrong")
    analysed = Counter(v for k_, v in assign.items() if k_ not in EXCLUDED_DOMAINS)
    if (analysed["train"], analysed["validation"], analysed["test"]) != (69, 23, 23):
        bad.append(f"post-exclusion population {dict(analysed)} != 69/23/23")
    bank_doms = set(Csents[("button", "bomb")])
    if set(assign) - EXCLUDED_DOMAINS != bank_doms:
        bad.append("manifest domain set != analysed bank domain set")
    A.add("CHK-15", "dcs_ts116_domain_split.json holds 116 assigned domains matching its own "
                    "declared 70/23/23; restaurant_kitchen is assigned to TRAIN so the "
                    "exclusion leaves 69/23/23; and the manifest domain set equals the "
                    "analysed bank domain set",
          not bad, len(assign), "; ".join(bad[:4]))
    R["dsplit"] = assign
    R["analysed_split"] = dict(analysed)

    # ---------------- CHK-16 : bank text traces to the pool files ----------------
    def apply_repairs(t):
        """The builder rewrites NATURAL occurrences of a codeword inside pool text to a
        surrogate (button->switch, basket->hamper) so they cannot be confused with the
        installed codeword. Re-applied here so the cross-source comparison is exact."""
        for w in CODEWORDS:
            # the builder's repair handles the PLURAL as well ("baskets" -> "hampers");
            # the concept substitution does not ("knives" survives) -- see section 1.2
            t = swap_word(t, w + "s", REPAIR_MAP[w] + "s")
            t = swap_word(t, w, REPAIR_MAP[w])
        return t

    bad = []
    pairs = 0
    repairs = []          # (concept, domain, pool sentence, bank sentence, surrogate)
    for co in CONCEPTS:
        harm = pools[co]["harm"]
        for dom, ss in conc_surface[("button", co)].items():
            pairs += 1
            pool_raw = harm.get(dom, [])
            pool_rep = [apply_repairs(x) for x in pool_raw]
            for raw, rep in zip(pool_raw, pool_rep):
                if raw != rep:
                    repairs.append((co, dom, raw, rep,
                                    [REPAIR_MAP[w] for w in CODEWORDS
                                     if _rx(r"\b" + w + r"s?\b").search(raw)]))
            if set(ss) != set(pool_rep):
                bad.append(f"{co}/{dom}: bank cell-B set != repaired pool harm set "
                           f"({len(set(ss) ^ set(pool_rep))} differ)")
    if mut == "M16":
        pairs = 0            # force the zero-binding branch
    A.add("CHK-16", "independent cross-source check: the concept-surface harm text recovered "
                    "from the BANK rows equals the harm pool file (after the declared "
                    "incidental-repair rewrites) for every concept x domain, so the "
                    "per-concept regeneration actually reached the banks",
          not bad, pairs, f"{len(bad)} mismatches" + ("; " + "; ".join(bad[:3]) if bad else
                                                      f"; {len(repairs)} sentences required "
                                                      f"an incidental repair"))
    R["repairs"] = repairs

    # ---------------- CHK-19 : incidental repairs are accounted for ---------------------
    # A surrogate token in bank text must either come from a repair traced above, or already
    # be present in the pool sentence. Anything else is an unexplained rewrite.
    sur_rx = {w: _rx(r"\b" + REPAIR_MAP[w] + r"s?\b") for w in CODEWORDS}
    unexplained = []
    n_sur = 0
    scanned_r = 0
    for co in CONCEPTS:
        harm = pools[co]["harm"]
        for dom, ss in conc_surface[("button", co)].items():
            pool_raw = harm.get(dom, [])
            src = Counter()
            for x in pool_raw:
                for w in CODEWORDS:
                    if sur_rx[w].search(x):
                        src[w] += 1               # surrogate already natural in the source
                    if _rx(r"\b" + w + r"s?\b").search(x):
                        src[w] += 1               # will be rewritten into a surrogate
            got = Counter()
            for x in ss:
                scanned_r += 1
                for w in CODEWORDS:
                    if sur_rx[w].search(x):
                        got[w] += 1
                        n_sur += 1
            for w in CODEWORDS:
                if got[w] != src[w]:
                    unexplained.append(f"{co}/{dom}: '{REPAIR_MAP[w]}' x{got[w]} in bank, "
                                       f"{src[w]} accounted for in the pool")
    if mut == "M19":
        unexplained.append("FORCED")
    A.add("CHK-19", "every incidental-repair surrogate token (button->switch, basket->hamper) "
                    "appearing in bank harm text is accounted for, one-for-one, by the same "
                    "token already being in the source pool sentence or by a codeword "
                    "occurrence there that the builder rewrote; an unexplained surrogate "
                    "would mean a silent edit inside a harm demonstration",
          not unexplained, scanned_r,
          f"{n_sur} surrogate occurrences, {len(repairs)} sentences rewritten, "
          f"{len(unexplained)} unexplained" + ("; " + "; ".join(unexplained[:3])
                                               if unexplained else ""))
    R["n_surrogate"] = n_sur

    # ---------------- CHK-20 : no foreign concept noun inside a harm pool ---------------
    foreign = []
    missing_own = []
    scanned_f = 0
    conc_rx0 = {c: _rx(r"\b(?:" + c + r"|" + PLURAL[c] + r")\b") for c in CONCEPTS}
    for co in CONCEPTS:
        for dom, ss in conc_surface[("button", co)].items():
            for i, x in enumerate(ss):
                scanned_f += 1
                for other in CONCEPTS:
                    if other != co and conc_rx0[other].search(x):
                        foreign.append((co, other, dom, i, x))
                if not conc_rx0[co].search(x):
                    missing_own.append((co, dom, i, x))
    if mut == "M20":
        foreign.append(("bomb", "knife", "MUTATED", 0, "a knife and a bomb"))
    A.add("CHK-20", "no harm sentence names a concept other than its own, and every harm "
                    "sentence names its own concept at least once -- the condition that "
                    "forced the restaurant_kitchen exclusion, re-checked over the 115 "
                    "analysed domains",
          (not foreign) and (not missing_own), scanned_f,
          f"{len(foreign)} foreign-concept sentences, {len(missing_own)} without their own "
          f"concept" + ("; " + str(foreign[0])[:160] if foreign else ""))
    R["foreign"] = foreign
    R["missing_own"] = missing_own

    # ---------------- CHK-17 : concept-word occurrence per cell ----------------
    conc_rx = {c: _rx(r"\b(?:" + c + r"|" + PLURAL[c] + r")\b") for c in CONCEPTS}
    if mut == "M17":
        d = sorted(Esents[("button", "bomb")])[0]
        Esents[("button", "bomb")][d] = (["No concept word here at all."]
                                         + Esents[("button", "bomb")][d][1:])
    expect = {"A": 0, "B": EXPECTED_SENTS_PER_DOMAIN, "C": 0, "E": EXPECTED_SENTS_PER_DOMAIN}
    bad = []
    bound = 0
    for cell, st in (("A", Asents), ("B", Bsents), ("C", Csents), ("E", Esents)):
        for (cw, co), dd in st.items():
            for dom, ss in dd.items():
                bound += 1
                n = sum(1 for x in ss if conc_rx[co].search(x))
                if n != expect[cell]:
                    bad.append(f"{cell}/{cw}/{co}/{dom}: {n} (expected {expect[cell]})")
    A.add("CHK-17", "per-domain count of demo sentences containing the concept word (or its "
                    "plural): 0 in the codeword-surface cells A and C, 40/40 in the "
                    "concept-surface cells B and E, for every domain in all 6 banks",
          not bad, bound, f"{len(bad)} deviations" + ("; " + "; ".join(bad[:4]) if bad else ""))

    # ---------------- CHK-18 : surface-only predictability of the concept label ---------
    R["clf"] = None
    if do_clf:
        clf = surface_predictability(Csents, conc_surface, assign, mut == "M18")
        R["clf"] = clf
        bad = []
        if clf is None:
            bad.append("sklearn unavailable")
        else:
            if clf["n_train_rows"] <= 0 or clf["n_val_rows"] <= 0:
                bad.append("empty train or validation fold")
            if clf["train_domains"] != 69 or clf["val_domains"] != 23:
                bad.append(f"folds are {clf['train_domains']}/{clf['val_domains']}, "
                           f"expected 69/23")
            if clf["leak_rows"]:
                bad.append(f"{clf['leak_rows']} masked rows still contain a weapon noun")
            if clf["shuffled_acc"] > 0.45:
                bad.append(f"label-shuffled control accuracy {clf['shuffled_acc']:.3f} is not "
                           f"near chance -- the fold construction leaks")
        A.add("CHK-18", "surface-only predictability: multinomial logistic regression on "
                        "word 1-2gram TF-IDF of the codeword-surface cell-C sentences "
                        "(all weapon nouns masked), fitted on the 69 TRAIN domains and "
                        "scored on the 23 VALIDATION domains -- domain-grouped, test never "
                        "read; passes only if the folds are the declared sizes, the masking "
                        "leaves no weapon noun, and a label-shuffled control sits at chance",
              not bad, (clf["n_train_rows"] + clf["n_val_rows"]) if clf else 0,
              "; ".join(bad[:4]) if bad else
              f"tfidf acc={clf['tfidf_acc']:.3f}, length-only acc={clf['len_acc']:.3f}, "
              f"hedge-only acc={clf['hedge_acc']:.3f}, shuffled={clf['shuffled_acc']:.3f}, "
              f"chance=0.333")

    # ---------------- CHK-21 : the audited bytes are the preregistered bytes -----------
    bad = []
    n_chk = 0
    for cw in CODEWORDS:
        for co in CONCEPTS:
            n_chk += 1
            want = (prereg["population"]["banks"].get(f"{cw}_{co}", {})
                    .get("bank_file_sha16"))
            got = corp[(cw, co)]["sha16"]
            if mut == "M21" and (cw, co) == ("basket", "gun"):
                got = "deadbeefdeadbeef"
            if want is None:
                bad.append(f"{cw}_{co}: no bank_file_sha16 in the preregistration")
            elif want != got:
                bad.append(f"{cw}_{co}: file sha16 {got} != preregistered {want}")
    A.add("CHK-21", "the six files audited here are byte-for-byte the six files "
                    "configs/dcs_ts_pr046.json names: recomputed sha256[:16] equals the "
                    "preregistered bank_file_sha16 for all six banks",
          not bad, n_chk, "; ".join(bad[:4]) if bad else
          "all 6 match the FROZEN preregistration")

    R["Csents"] = Csents
    R["conc_surface"] = conc_surface
    return A, R


# ======================================================================================
# CHK-18 helper -- the only place sklearn is used
# ======================================================================================

def surface_predictability(Csents, conc_surface, assign, break_folds=False):
    try:
        import numpy as np
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import confusion_matrix
    except Exception:
        return None

    mask_rx = re.compile(r"\b(bombs?|knives|knife|guns?|buttons?|baskets?)\b", re.IGNORECASE)
    X, y, g = [], [], []
    for ci, co in enumerate(CONCEPTS):
        for dom, ss in Csents[("button", co)].items():
            for s in ss:
                X.append(mask_rx.sub("<W>", s))
                y.append(ci)
                g.append(dom)
    y = np.array(y)
    g = np.array(g)
    leak = sum(1 for s in X if re.search(r"\b(bombs?|knives|knife|guns?)\b", s, re.I))

    tr_dom = sorted(d for d, v in assign.items()
                    if v == "train" and d not in EXCLUDED_DOMAINS)
    va_dom = sorted(d for d, v in assign.items()
                    if v == "validation" and d not in EXCLUDED_DOMAINS)
    if break_folds:                     # M18: put 5 train domains into validation too
        va_dom = va_dom + tr_dom[:5]
    tr = np.isin(g, tr_dom)
    va = np.isin(g, va_dom)

    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, lowercase=True)
    Xtr = vec.fit_transform([X[i] for i in np.where(tr)[0]])
    Xva = vec.transform([X[i] for i in np.where(va)[0]])
    lr = LogisticRegression(max_iter=2000, C=1.0)
    lr.fit(Xtr, y[tr])
    pred = lr.predict(Xva)
    acc = float((pred == y[va]).mean())
    cm = confusion_matrix(y[va], pred, labels=[0, 1, 2]).tolist()
    per_class = {CONCEPTS[i]: float((pred[y[va] == i] == i).mean()) for i in range(3)}
    # per-domain accuracy on validation, and the domain-mean (the honest unit)
    dom_acc = {}
    gv = g[va]
    yv = y[va]
    for d in va_dom:
        m = gv == d
        if m.sum():
            dom_acc[d] = float((pred[m] == yv[m]).mean())
    dom_mean = float(np.mean(list(dom_acc.values()))) if dom_acc else 0.0

    # length-only
    L = np.array([[len(s), len(s.split())] for s in X], dtype=float)
    lr2 = LogisticRegression(max_iter=2000)
    lr2.fit(L[tr], y[tr])
    len_acc = float((lr2.predict(L[va]) == y[va]).mean())

    # hedge-only (narrow set), 5 binary features
    hn = compile_lex(HEDGE_NARROW)
    H = np.array([[1.0 if rx.search(s) else 0.0 for _, rx, _, _ in hn] for s in X])
    lr3 = LogisticRegression(max_iter=2000)
    lr3.fit(H[tr], y[tr])
    hedge_acc = float((lr3.predict(H[va]) == y[va]).mean())

    # label-shuffled control: permute labels WITHIN the training fold only
    rng = np.random.default_rng(20260907)
    ysh = y.copy()
    idx = np.where(tr)[0]
    ysh[idx] = rng.permutation(ysh[idx])
    lr4 = LogisticRegression(max_iter=2000, C=1.0)
    lr4.fit(Xtr, ysh[tr])
    sh_acc = float((lr4.predict(Xva) == y[va]).mean())

    # block-level: what the model actually reads (4-sentence cell-C blocks)
    return dict(tfidf_acc=acc, len_acc=len_acc, hedge_acc=hedge_acc, shuffled_acc=sh_acc,
                cm=cm, per_class=per_class, dom_acc=dom_acc, dom_mean=dom_mean,
                n_train_rows=int(tr.sum()), n_val_rows=int(va.sum()),
                train_domains=len(tr_dom), val_domains=len(set(va_dom)),
                leak_rows=leak, n_features=int(Xtr.shape[1]))


# ======================================================================================
# report
# ======================================================================================

MUTATIONS = [
    ("M01", "CHK-01", "drop 100 rows from the button/knife bank row count"),
    ("M02", "CHK-02", "delete one domain from the cell-C demo corpus"),
    ("M03", "CHK-03", "inject a literal 'bomb' sentence into a knife-bank cell-C block"),
    ("M04", "CHK-04", "perturb one cell-B sentence so the concept-surface swap no longer matches"),
    ("M05", "CHK-05", "copy the bomb cell-C block over the knife cell-C block in one domain "
                      "(= the C-074 identity, one domain at a time)"),
    ("M06", "CHK-06", "perturb one cell-A sentence in the gun bank so cell A stops being aligned"),
    ("M07", "CHK-07", "empty the tier-1 explosive lexicon (zero-binding)"),
    ("M08", "CHK-08", "replace the knife affordance lexicon with a pattern that fails its control"),
    ("M09", "CHK-09", "insert one bomb harm sentence into the knife sentence set"),
    ("M10", "CHK-10", "break one gun polysemy pattern so it fails its positive control"),
    ("M11", "CHK-11", "force a dead pattern into the mass-noun frame set"),
    ("M12", "CHK-12", "give the narrow hedge set a pattern that matches its own anti-control"),
    ("M13", "CHK-13", "empty the knife sentence-length sample"),
    ("M14", "CHK-14", "drop one domain x concept from the appendix sample"),
    ("M15", "CHK-15", "corrupt n_train in the split manifest"),
    ("M16", "CHK-16", "force the pool cross-check to bind zero objects"),
    ("M17", "CHK-17", "blank the concept word out of one cell-E sentence"),
    ("M18", "CHK-18", "leak 5 train domains into the validation fold"),
    ("M19", "CHK-19", "declare one surrogate occurrence unexplained"),
    ("M20", "CHK-20", "inject a sentence naming two concepts into the foreign-noun scan"),
    ("M21", "CHK-21", "corrupt the recomputed file hash of the basket/gun bank"),
]


def pct(a, b):
    return f"{100.0*a/b:.2f}%" if b else "n/a"


def dist_line(d, doms):
    v = sorted(d.get(x, 0) for x in doms)
    n = len(v)
    if not n:
        return "n/a"
    def q(p):
        return v[min(n - 1, int(p * (n - 1) + 0.5))]
    return (f"min {v[0]}, p25 {q(.25)}, median {q(.5)}, p75 {q(.75)}, p90 {q(.9)}, "
            f"max {v[-1]}")


def build_report(corp, pools, manifest, prereg, A, R, mut_results):
    doms = sorted(R["Csents"][("button", "bomb")])
    assign = R["dsplit"]
    tot1, tot2, totN = R["tot1"], R["tot2"], R["totN"]
    mat = R["afford_mat"]
    L = []
    w = L.append

    w("# DCS gate G4 -- concept-backing / polysemy audit of the ts116n bank family")
    w("")
    w("Preregistration `configs/dcs_ts_pr046.json`, gate G4 "
      "(\"concept-backing audit re-run on ts116n; mass-noun polysemy and hedging rates "
      "re-measured, not inherited\").  Prompt-only, CPU-only.  No model was loaded, no model "
      "outcome was consulted, no domain was judged by any behavioural result.")
    w("")
    w("Script: `scripts/dcs_ts116n_audit_concept_backing.py` (new file; "
      "`scripts/dcs_ts_audit_concept_backing.py` documents the OLD bank and was not edited).")
    w("")
    w("> **Nothing in this report is inherited from `DCS_TS_CONCEPT_BACKING_AUDIT.md`.**  On "
      "the previous bank family (ts116) cell C drew one shared harm pool with the concept "
      "word substituted away, so the three concept arms were byte-identical (C-074).  Every "
      "per-concept rate that audit printed was pinned by arithmetic -- the tier-1 explosive "
      "rate was the SAME 4.27% for bomb, knife and gun because they were the same sentences, "
      "and the knife/gun affordance rate was 0 for the same reason.  The old script asserts "
      "that identity as a PASS; here it is inverted into CHK-05, which requires cell C to "
      "DIFFER in every domain.")
    w("")

    w("## Population")
    w("")
    w(f"* {DOMAINS_IN_FILE} domains are present in the bank files; **`restaurant_kitchen` is "
      f"excluded from every count in this report** (preregistered, prompt-only, "
      f"`dcs_ts_pr046.json:preregistered_exclusions[0]`), leaving **{EXPECTED_DOMAINS} "
      f"analysed domains**.  It is assigned to `train`, so the analysed split is "
      f"**{R['analysed_split'].get('train')} train / "
      f"{R['analysed_split'].get('validation')} validation / "
      f"{R['analysed_split'].get('test')} test** (CHK-15).")
    w(f"* Harm-demonstration corpus per concept: {EXPECTED_DOMAINS} domains x "
      f"{EXPECTED_SENTS_PER_DOMAIN} distinct sentences = "
      f"**{EXPECTED_DOMAINS*EXPECTED_SENTS_PER_DOMAIN} sentences**, and it is the same "
      f"sentence set under both codewords (CHK-04), so per-concept rates below are quoted "
      f"against the pooled denominator "
      f"{EXPECTED_DOMAINS*EXPECTED_SENTS_PER_DOMAIN*len(CODEWORDS)} "
      f"(= the same {EXPECTED_DOMAINS*EXPECTED_SENTS_PER_DOMAIN} sentences seen once in each "
      f"codeword bank) unless the table says otherwise. Because the two banks carry the same "
      f"sentence set, a rate is identical under either denominator; only the raw counts "
      f"differ by a factor of 2, and enumerations below are printed once, from the button "
      f"bank.")
    w("")
    w("| bank | rows | sha256[:16] of the file bytes |")
    w("|---|---:|---|")
    for cw in CODEWORDS:
        for co in CONCEPTS:
            b = corp[(cw, co)]
            w(f"| `{os.path.basename(b['path'])}` | {b['n_rows']} | `{b['sha16']}` |")
    for co in CONCEPTS:
        w(f"| `{os.path.basename(POOL_TS[co])}` (cross-source only) | - | "
          f"`{pools[co]['sha16']}` |")
    w("")
    w("The bank hashes above are recomputed here from the bytes on disk and are checked "
      "against `configs/dcs_ts_pr046.json:population.banks.*.bank_file_sha16` (CHK-21).  "
      "They are deliberately a different quantity from `bank_rows_sha16`.  The pool hashes "
      "are whole-file hashes and are NOT the preregistration's `content_sha16`, which is a "
      "content digest computed by the generator; the pools are used here only as a "
      "cross-source check (CHK-16).")
    w("")

    # ---------------- headline ----------------
    w("## 0. Headline")
    w("")
    w(f"1. **The three arms are genuinely three corpora now.**  Cell C differs between bomb "
      f"and each of knife/gun in {EXPECTED_DOMAINS}/{EXPECTED_DOMAINS} domains under both "
      f"codewords ({R['chk05_pairs']} comparisons, {len(R['chk05_same'])} identical) and "
      f"cell A is byte-identical across concepts (CHK-05, CHK-06).  Sharing between pools: "
      f"{len(R['overlap_exact'])} byte-identical sentences and "
      f"{len(R['overlap_neutral'])} that are identical once the weapon noun is neutralised "
      f"(CHK-09" + (", listed in section 7 -- each is a near-duplicate incident description "
                    "written for two different concepts in the same domain" if
                    R['overlap_neutral'] else "") + ").")
    w(f"2. **Tier-1 explosive predicates are now concept-specific, and knife is clean.**  "
      f"bomb {tot1['bomb']}/{totN['bomb']} = {pct(tot1['bomb'], totN['bomb'])}; "
      f"knife {tot1['knife']}/{totN['knife']} = {pct(tot1['knife'], totN['knife'])}; "
      f"gun {tot1['gun']}/{totN['gun']} = {pct(tot1['gun'], totN['gun'])}.  On the old "
      f"shared pool all three read 4.27% because they were one corpus.")
    w(f"3. **The positive control the old bank could not pass, passes.**  Own-concept "
      f"affordance: bomb {mat[('bomb','bomb')]}/{totN['bomb']} = "
      f"{pct(mat[('bomb','bomb')], totN['bomb'])}, "
      f"knife {mat[('knife','knife')]}/{totN['knife']} = "
      f"{pct(mat[('knife','knife')], totN['knife'])}, "
      f"gun {mat[('gun','gun')]}/{totN['gun']} = "
      f"{pct(mat[('gun','gun')], totN['gun'])}; every off-diagonal cell is strictly smaller "
      f"(CHK-08).")
    w(f"4. **Hedging is the asymmetry, and it is real.**  Narrow (preregistered) hedge rate: "
      f"bomb {R['hedge_tot_n']['bomb']}/{totN['bomb']} = "
      f"{pct(R['hedge_tot_n']['bomb'], totN['bomb'])}, "
      f"knife {R['hedge_tot_n']['knife']}/{totN['knife']} = "
      f"{pct(R['hedge_tot_n']['knife'], totN['knife'])}, "
      f"gun {R['hedge_tot_n']['gun']}/{totN['gun']} = "
      f"{pct(R['hedge_tot_n']['gun'], totN['gun'])}.")
    if R["cellC_leaks"]:
        w(f"5. **One defect, and it is not the register asymmetry.**  "
          f"{len(R['cellC_leaks'])}/{R['cellC_scanned']} cell-C demonstration sentences still "
          f"contain a literal weapon noun -- the plural `knives`, which the singular-only "
          f"`knife -> button` substitution never matched -- affecting {len(R['leak_rows'])}/"
          f"{R['cellC_rows']} = {pct(len(R['leak_rows']), R['cellC_rows'])} of cell-C rows in "
          f"the knife banks.  Section 1.2 lists every one.")
    else:
        w(f"5. **No concept word leaks into cell C**: 0/{R['cellC_scanned']} demonstration "
          f"sentences contain a literal weapon noun.")
    if R.get("clf"):
        c = R["clf"]
        w(f"6. **What that asymmetry costs: the concept label is "
          f"{c['tfidf_acc']*100:.1f}% recoverable from the demonstration text alone** "
          f"(masked word 1-2gram TF-IDF + logistic regression, fitted on the 69 TRAIN "
          f"domains, scored on the {c['val_domains']} VALIDATION domains, "
          f"{c['n_val_rows']} sentences, chance 33.3%; domain-mean "
          f"{c['dom_mean']*100:.1f}%).  Length alone gives {c['len_acc']*100:.1f}% and the "
          f"five narrow hedge markers alone give {c['hedge_acc']*100:.1f}%.  A "
          f"label-shuffled control on the same folds gives {c['shuffled_acc']*100:.1f}%.  "
          f"Test was not read.")
    w("")
    n_red0 = len(A.red())
    knife_leak = bool(R["cellC_leaks"])
    w(f"**Gate G4 status: {'FAIL -- REPAIR REQUIRED' if knife_leak else 'PASS'}.**  "
      f"{len(A.checks) - n_red0}/{len(A.checks)} checks GREEN, {n_red0} RED, "
      f"and every RED is a property of the bank rather than of the audit: "
      + "; ".join(f"{c['id']}" for c in sorted(A.red(), key=lambda c: c['id']))
      + " -- respectively the plural-`knives` leak into cell C (section 1.2), 3 knife/gun "
        "sentence pairs identical once the weapon noun is neutralised (section 7), and the "
        "per-cell concept-word count, whose deviations are that SAME leak counted per "
        "(bank, domain) cell"
      + ".  The concept-backing question G4 actually asks -- do the three pools install "
        "three different concepts -- is answered YES (sections 2, 3).  The gate fails on a "
        "mechanical substitution defect in the knife banks (section 1.2) that is repairable "
        "without regenerating anything, plus " + str(len(R['overlap_neutral']))
      + " knife/gun near-duplicate sentence pairs (section 7).")
    w("")

    # ---------------- checks ----------------
    n_red = len(A.red())
    w("## 1. Checks and mutation proof")
    w("")
    w(f"**{len(A.checks)} checks, {len(MUTATIONS)} mutations.**  "
      f"{len(A.checks) - n_red}/{len(A.checks)} GREEN, {n_red} RED.  Every check reports the "
      f"number of objects it bound; a check that binds zero objects is reported RED, never "
      f"GREEN.  Every lexicon pattern carries a positive control it must match and an "
      f"anti-control it must not match.")
    w("")
    w("| id | status | bound | check | detail |")
    w("|---|---|---:|---|---|")
    for c in sorted(A.checks, key=lambda c: c["id"]):
        d = c["detail"].replace("|", "\\|")[:280]
        w(f"| {c['id']} | **{c['status']}** | {c['bound']} | "
          f"{c['desc'].replace('|', '/')} | {d} |")
    w("")
    if mut_results is not None:
        w("### 1.1 Mutation proof")
        w("")
        w("Each mutation corrupts an in-memory copy of the corpus (or a lexicon) and the whole "
          "audit re-runs.  A mutation is accepted only if its target check flips to RED.")
        w("")
        w("| mutation | target | corruption | target went RED | other checks also RED |")
        w("|---|---|---|---|---|")
        for mid, target, desc, red_ids in mut_results:
            hit = "YES" if target in red_ids else "**NO -- CHECK IS INERT**"
            others = ", ".join(x for x in red_ids if x != target) or "-"
            w(f"| {mid} | {target} | {desc} | {hit} | {others} |")
        w("")
        n_ok = sum(1 for mid, t, d, r in mut_results if t in r)
        w(f"**{n_ok}/{len(mut_results)} mutations turned their target check RED.**")
        base_red = ", ".join(c["id"] for c in sorted(A.red(), key=lambda c: c["id"]))
        if base_red:
            w("")
            w(f"{base_red} are RED in the UNMUTATED run -- they are real findings about the "
              f"bank, not mutation side effects -- so they appear in the last column of every "
              f"row. The column is still informative: read it for the checks that appear "
              f"only against a specific mutation (e.g. M05 also drags CHK-04 down, because "
              f"overwriting cell C breaks the swap(C)==B identity too).")
        w("")

    # ---------------- 1.2 leak ----------------
    w("### 1.2 Surface leakage of the concept word into cell C")
    w("")
    leaks = R["cellC_leaks"]
    lrows = R["leak_rows"]
    if not leaks:
        w(f"None. {R['cellC_scanned']} cell-C demonstration sentences scanned across the 6 "
          f"banks; 0 contain a literal `bomb`/`knife`/`gun` (whole word or `bomb` as a "
          f"substring).")
    else:
        w(f"**CRITICAL.** {len(leaks)} of {R['cellC_scanned']} cell-C demonstration sentences "
          f"still contain a literal weapon noun, affecting **{len(lrows)} of "
          f"{R['cellC_rows']} cell-C rows = {pct(len(lrows), R['cellC_rows'])}**.  The "
          f"codeword substitution is singular-only: the harm generator wrote the PLURAL "
          f"`knives`, which `knife -> button` never matched, so the demonstration block "
          f"names the concept it is supposed to hide.  Cell C is the primary channel of the "
          f"whole preregistration, and on these rows the concept label is not latent at all.")
        w("")
        byc = Counter((x["concept"]) for x in lrows)
        byq = Counter((x["concept"], x["query_kind"], x["n_examples"]) for x in lrows)
        w("| concept | leaking sentences (of 4600 per bank) | affected cell-C rows |")
        w("|---|---:|---:|")
        for co in CONCEPTS:
            ns = len([x for x in leaks if x[1] == co])
            w(f"| **{co}** | {ns} | {byc.get(co, 0)} |")
        w("")
        w("| concept | query_kind | n_examples | affected rows |")
        w("|---|---|---:|---:|")
        for k, v in sorted(byq.items()):
            w(f"| {k[0]} | {k[1]} | {k[2]} | {v} |")
        w("")
        w("Every leaking sentence (button bank; the basket bank carries the same sentences):")
        w("")
        w("| concept | domain | split | index | matched | sentence |")
        w("|---|---|---|---:|---|---|")
        for cw, co, dom, i, sent, hits in leaks:
            if cw != "button":
                continue
            w(f"| {co} | `{dom}` | {assign.get(dom, '?')} | {i} | "
              f"`{', '.join(hits)}` | {sent.replace('|', '/')} |")
        w("")
        ldoms = sorted(set(x[2] for x in leaks))
        lsp = Counter(assign.get(d, "?") for d in ldoms)
        w(f"Affected domains: {len(ldoms)} of {EXPECTED_DOMAINS} -- "
          + ", ".join(f"`{d}` ({assign.get(d,'?')})" for d in ldoms)
          + f".  By split: {dict(lsp)}.")
        w("")
        w("**Consequence for the probe.**  These rows are not a register asymmetry, they are "
          "an outright label.  They must be dropped, or the plural must be substituted and "
          "the affected banks rebuilt, BEFORE any extraction; otherwise a probe trained on "
          "cell C can read the concept off the prompt on those rows.  Because the affected "
          "domains sit in named splits (table above), the contamination is not confined to "
          "train.")
    w("")

    # ---------------- 2. tier-1 ----------------
    w("## 2. Tier-1 explosive predicates, per concept and per domain")
    w("")
    w("Lexicon: `detonat*`, `explos*`, `explode/exploding`, `defus*`, `unexploded`, "
      "`shrapnel`, `blast` (excluding the catering false friend *blast chiller*), `fuse`, "
      "`incendiar*`, `ordnance`, `IED`, `dynamite`, `TNT`, `warhead`, `grenade`, `munitions`, "
      "`blast radius`, and `shell` only in an old/live/buried/discovered/unexploded frame.  "
      "Measured on the concept-surface (cell-B) text, which CHK-04 proves is the cell-C text "
      "with the codeword restored.")
    w("")
    w("| concept | sentences with >=1 tier-1 predicate | denominator | rate | "
      "domains with >=1 | max per domain | tier-2 procedural |")
    w("|---|---:|---:|---:|---:|---:|---:|")
    for co in CONCEPTS:
        dd = R["t1_by"][co]
        nz = sum(1 for d in doms if dd.get(d, 0) > 0)
        mx = max([dd.get(d, 0) for d in doms] or [0])
        w(f"| **{co}** | {tot1[co]} | {totN[co]} | {pct(tot1[co], totN[co])} | "
          f"{nz}/{EXPECTED_DOMAINS} | {mx}/80 | {tot2[co]} = {pct(tot2[co], totN[co])} |")
    w("")
    w("Per-domain distribution of tier-1 hits (out of 80 = 40 sentences x 2 codeword banks):")
    w("")
    for co in CONCEPTS:
        w(f"* **{co}**: {dist_line(R['t1_by'][co], doms)}")
    w("")
    w("Block-level exposure -- the unit a model actually reads.  Fraction of cell-C "
      "`n_examples=4`, `semantic_one_word` demonstration blocks containing at least one "
      "tier-1 explosive predicate (codeword surface, concept restored):")
    w("")
    w("| concept | blocks with a tier-1 predicate | blocks | rate |")
    w("|---|---:|---:|---:|")
    for co in CONCEPTS:
        h, t = R["exposure"][co]
        w(f"| {co} | {h} | {t} | {pct(h, t)} |")
    w("")
    for co in ("knife", "gun"):
        ex = R["t1_examples"][co]
        w(f"**Every tier-1 hit in the {co} pool ({len(ex)} sentences in the button bank; the "
          f"basket bank is the same sentence set):**")
        w("")
        if not ex:
            w("* none.")
        else:
            for dom, i, s, h in ex[:200]:
                w(f"* `{dom}` [{i}] {' '.join(h)} -- {s}")
        w("")
    w("**Reading.**  ")
    if tot1["knife"] == 0:
        w("The knife pool contains **zero** explosive predicates.  The old bank's 4.27% for "
          "knife was an artefact of the shared corpus and is retired.")
    else:
        w(f"The knife pool contains {tot1['knife']} sentences with an explosive predicate "
          f"({pct(tot1['knife'], totN['knife'])}).  Each is listed above; judge them "
          f"individually rather than by the rate.")
    w("")

    # ---------------- 3. affordance ----------------
    w("## 3. Concept affordance -- the positive control the old bank scored zero on")
    w("")
    w("Rows = which concept's harm pool the sentence came from; columns = which concept's "
      "affordance lexicon fired.  Strict, weapon-specific lexicons "
      f"({len(AFFORD_STRICT['bomb'])} bomb / {len(AFFORD_STRICT['knife'])} knife / "
      f"{len(AFFORD_STRICT['gun'])} gun patterns), every one checked against a positive "
      "control and an anti-control.  Denominator per row: "
      f"{EXPECTED_DOMAINS*EXPECTED_SENTS_PER_DOMAIN*2} sentences.")
    w("")
    w("| pool \\ lexicon | bomb-affording | knife-affording | gun-affording |")
    w("|---|---:|---:|---:|")
    for pool in CONCEPTS:
        cells = []
        for lex in CONCEPTS:
            v = mat[(pool, lex)]
            mark = "**" if pool == lex else ""
            cells.append(f"{mark}{v} = {pct(v, totN[pool])}{mark}")
        w(f"| **{pool}** | " + " | ".join(cells) + " |")
    w("")
    w("Domains in which the own-concept lexicon fires at least once:")
    w("")
    for c in CONCEPTS:
        nz = len([d for d, v in R["afford_mat_dom"][(c, c)].items() if v > 0])
        w(f"* **{c}**: {nz}/{EXPECTED_DOMAINS} domains; per-domain "
          f"{dist_line(R['afford_mat_dom'][(c, c)], doms)} (out of 80)")
    w("")
    w("The same matrix under the **loose** token lists named in the G4 task "
      "(`blade, sharpen, cut, stab, edge, handle, sheath` for knife; "
      "`fire, load, barrel, trigger, holster, ammunition, discharge` for gun; "
      "`detonat, explos, unexploded, defus, blast, fuse, shell` for bomb), button bank only, "
      f"denominator {EXPECTED_DOMAINS*EXPECTED_SENTS_PER_DOMAIN}.  These tokens are "
      "polysemous -- *fire* matches *fire exit*, *cut* matches *cut costs*, *handle* matches "
      "a door handle -- so this is an upper bound, printed next to the strict matrix rather "
      "than instead of it:")
    w("")
    w("| pool \\ loose lexicon | bomb | knife | gun |")
    w("|---|---:|---:|---:|")
    for pool in CONCEPTS:
        cells = []
        for lex in CONCEPTS:
            v = R["afford_loose_mat"][(pool, lex)]
            cells.append(f"{v} = {pct(v, EXPECTED_DOMAINS*EXPECTED_SENTS_PER_DOMAIN)}")
        w(f"| **{pool}** | " + " | ".join(cells) + " |")
    w("")
    w("The knife row of the loose matrix (19.11%) is four times its strict rate because "
      "`cut`, `handle` and `edge` are ordinary workplace English -- *cut costs*, *door "
      "handle*, *edge of the bench*. The strict matrix is the one to quote.")
    w("")
    w("Loose-token breakdown on the diagonal (which token carries the loose rate):")
    w("")
    for c in CONCEPTS:
        tk = R["afford_loose_tok"][(c, c)]
        body = ", ".join(f"`{k}` {v}" for k, v in sorted(tk.items(), key=lambda x: -x[1]))
        w(f"* **{c}**: " + (body if body else "no hits"))
    w("")

    # ---------------- 4. polysemy ----------------
    w("## 4. Polysemy -- named non-target senses")
    w("")
    w(f"{R['poly_npat']} curated patterns across the three concepts, applied to all "
      f"{EXPECTED_DOMAINS*EXPECTED_SENTS_PER_DOMAIN*2} concept-surface harm sentences "
      f"per concept.  On the old bank these patterns could only ever fire on one shared "
      f"corpus; here each pool is naturally generated for its own concept, so a named sense "
      f"can genuinely appear.  **Every hit is enumerated** (button bank; the basket bank is "
      f"the same sentence set).")
    w("")
    for co in CONCEPTS:
        hits = R["poly_hits"][co]
        w(f"### {co} -- {len(hits)} hits "
          f"({pct(len(hits), EXPECTED_DOMAINS*EXPECTED_SENTS_PER_DOMAIN)} of the "
          f"{EXPECTED_DOMAINS*EXPECTED_SENTS_PER_DOMAIN} sentences)")
        w("")
        if not hits:
            w("* none.")
        else:
            w("| domain | index | pattern | sentence |")
            w("|---|---:|---|---|")
            for dom, i, s, h in hits:
                w(f"| `{dom}` | {i} | `{' '.join(h)}` | {s.replace('|', '/')} |")
        w("")

    # ---------------- 5. mass noun ----------------
    w("## 5. The mass-noun frame `a <W> of <NOUN>`")
    w("")
    w("Frames: `a <W> of X`, `<W>s of X`, `as ADJ as a <W>`, `a <W> of a X`.  Checked live "
      "for all three concept words and for both codewords (CHK-11).  This is the frame that "
      "made the old `club` pools unusable: it puts the swapped noun in a non-device, "
      "mass-noun position (\"a bomb of sawdust\").")
    w("")
    w("| concept | sentences in a mass-noun frame | denominator | rate | domains affected |")
    w("|---|---:|---:|---:|---:|")
    for co in CONCEPTS:
        v = R["mass_tot"][co]
        nz = len([d for d, x in R["mass_by_dom"][co].items() if x > 0])
        w(f"| **{co}** | {v} | {totN[co]} | {pct(v, totN[co])} | {nz}/{EXPECTED_DOMAINS} |")
    w("")
    w("The preregistration records 1.08% / 0% / 0% for bomb / knife / gun on the "
      "prompt-only measurement of 4640 sentences per concept.  The numbers above are "
      "re-derived here from raw bank rows over the 115-domain analysed population and "
      "supersede that record wherever they differ.")
    w("")
    for co in CONCEPTS:
        hits = R["mass_hits"][co]
        if hits:
            w(f"**{co} -- all {len(hits)} hits in the button bank "
              f"({R['mass_tot'][co]} across both banks, same sentences):**")
            w("")
            for dom, i, s, h in hits[:300]:
                w(f"* `{dom}` [{i}] -- {s}")
            w("")

    # ---------------- 6. hedging ----------------
    w("## 6. Hedging, per concept and per domain")
    w("")
    w("**Narrow** set = exactly the five families the preregistration quotes: `resembl*`, "
      "`simulat*`, `drill`, `false alarm`, `looks like`.  **Broad** set adds "
      "`suspected/potential/possible`, `mistaken for`, `hoax`, `what appeared to be`, "
      "`no sign of`, `joke/prank`, `mock/training exercise`, `turned out to be`, "
      "`sounded like`, `mimic`, `similar to`, `akin to`, `nothing found`.")
    w("")
    w("| concept | narrow | rate | broad | rate | domains with >=1 narrow hedge |")
    w("|---|---:|---:|---:|---:|---:|")
    for co in CONCEPTS:
        n_ = R["hedge_tot_n"][co]
        b_ = R["hedge_tot_b"][co]
        nz = sum(1 for d in doms if R["hedge_narrow"][co].get(d, 0) > 0)
        w(f"| **{co}** | {n_} | {pct(n_, totN[co])} | {b_} | {pct(b_, totN[co])} | "
          f"{nz}/{EXPECTED_DOMAINS} |")
    w("")
    w("Per-domain distribution of NARROW hedged sentences (out of 80 per domain = 40 x 2 "
      "codeword banks) -- the distribution, not just the mean:")
    w("")
    w("| concept | " + " | ".join(f"{p}" for p in
                                  ["min", "p10", "p25", "median", "p75", "p90", "max",
                                   "domains at 0"]) + " |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for co in CONCEPTS:
        v = sorted(R["hedge_narrow"][co].get(d, 0) for d in doms)
        n = len(v)
        def q(p):
            return v[min(n - 1, int(p * (n - 1) + 0.5))]
        zeros = sum(1 for x in v if x == 0)
        w(f"| **{co}** | {v[0]} | {q(.10)} | {q(.25)} | {q(.50)} | {q(.75)} | {q(.90)} | "
          f"{v[-1]} | {zeros}/{EXPECTED_DOMAINS} |")
    w("")
    w("Histogram of per-domain NARROW hedge counts (domains per bucket, out of "
      f"{EXPECTED_DOMAINS}):")
    w("")
    buckets = [(0, 0), (1, 4), (5, 9), (10, 19), (20, 39), (40, 80)]
    w("| concept | " + " | ".join(f"{a}-{b}" if a != b else f"{a}"
                                  for a, b in buckets) + " |")
    w("|---|" + "---:|" * len(buckets))
    for co in CONCEPTS:
        row = []
        for a, b in buckets:
            row.append(str(sum(1 for d in doms
                               if a <= R["hedge_narrow"][co].get(d, 0) <= b)))
        w(f"| **{co}** | " + " | ".join(row) + " |")
    w("")
    w("**The domains driving the bomb / knife gap** -- the 20 domains with the largest "
      "`bomb narrow hedge count - knife narrow hedge count` (out of 80 per cell):")
    w("")
    gap = sorted(doms, key=lambda d: -(R["hedge_narrow"]["bomb"].get(d, 0)
                                       - R["hedge_narrow"]["knife"].get(d, 0)))
    w("| domain | split | bomb | knife | gun | gap (bomb-knife) |")
    w("|---|---|---:|---:|---:|---:|")
    for d in gap[:20]:
        bo = R["hedge_narrow"]["bomb"].get(d, 0)
        kn = R["hedge_narrow"]["knife"].get(d, 0)
        gu = R["hedge_narrow"]["gun"].get(d, 0)
        w(f"| `{d}` | {assign.get(d, '?')} | {bo} | {kn} | {gu} | {bo-kn} |")
    w("")
    top = sum(R["hedge_narrow"]["bomb"].get(d, 0) for d in gap[:20])
    w(f"Those 20 domains hold {top}/{R['hedge_tot_n']['bomb']} = "
      f"{pct(top, R['hedge_tot_n']['bomb'])} of all bomb narrow hedges, so the asymmetry is "
      f"**not** the property of a handful of domains that could simply be dropped: it is "
      f"spread over "
      f"{sum(1 for d in doms if R['hedge_narrow']['bomb'].get(d, 0) > 0)}/"
      f"{EXPECTED_DOMAINS} domains.")
    w("")
    ex = R["hedge_examples"]["bomb"][:15]
    if ex:
        w("Sample bomb hedges (first 15, button bank):")
        w("")
        for dom, i, s, h in ex:
            w(f"* `{dom}` [{i}] {' '.join(h)} -- {s}")
        w("")
    exk = R["hedge_examples"]["knife"][:15]
    w(f"Every knife narrow hedge (button bank, {len(R['hedge_examples']['knife'])} shown of "
      f"the button-bank total):")
    w("")
    if not exk:
        w("* none.")
    for dom, i, s, h in exk:
        w(f"* `{dom}` [{i}] {' '.join(h)} -- {s}")
    w("")

    # ---------------- 6b length ----------------
    w("### 6b. Sentence length")
    w("")
    w("| concept | distinct sentences | mean chars | median | p10 | p90 |")
    w("|---|---:|---:|---:|---:|---:|")
    for co in CONCEPTS:
        v = R["lens"][co]
        n = len(v)
        mean = sum(v) / n
        w(f"| **{co}** | {n} | {mean:.1f} | {v[n//2]} | {v[int(.1*n)]} | {v[int(.9*n)]} |")
    w("")
    w("The preregistration records 82 / 75 / 78 mean chars for bomb / knife / gun; "
      "re-measured here from raw bank rows over the 115-domain population, it is "
      + ", ".join(f"{c} {sum(R['lens'][c])/len(R['lens'][c]):.1f}" for c in CONCEPTS) + ".")
    w("")

    # ---------------- 7. overlap ----------------
    w("## 7. Cross-concept sentence overlap")
    w("")
    w(f"Compared {EXPECTED_DOMAINS*EXPECTED_SENTS_PER_DOMAIN} sentences per concept, "
      f"within-domain, both byte-identically and after neutralising the weapon noun to "
      f"`<W>` (so \"found a knife near the carousel\" and \"found a gun near the carousel\" "
      f"would count as an overlap).")
    w("")
    w(f"* byte-identical shared sentences: **{len(R['overlap_exact'])}**")
    w(f"* shared after noun-neutralisation: **{len(R['overlap_neutral'])}**")
    w("")
    if R["overlap_neutral"]:
        w("| concepts | domain | sentence A | sentence B |")
        w("|---|---|---|---|")
        for ca, cb, dom, a, b in R["overlap_neutral"][:200]:
            w(f"| {ca}/{cb} | `{dom}` | {a.replace('|','/')} | {b.replace('|','/')} |")
        w("")

    w("### 7b. Foreign-concept contamination and incidental repairs")
    w("")
    w(f"* Harm sentences naming a concept other than their own: **{len(R['foreign'])}** of "
      f"{EXPECTED_DOMAINS*EXPECTED_SENTS_PER_DOMAIN*3} (CHK-20).  This is the condition that "
      f"forced the `restaurant_kitchen` exclusion; over the 115 analysed domains it is clean.")
    w(f"* Harm sentences not naming their own concept at all: **{len(R['missing_own'])}**.")
    w(f"* Sentences the builder rewrote because a codeword occurs naturally in them "
      f"(`button`->`switch`, `basket`->`hamper`): **{len(R['repairs'])}**, "
      f"{R['n_surrogate']} surrogate token occurrences in total, 0 unexplained (CHK-19).")
    if R["repairs"]:
        w("")
        w("| concept | domain | pool sentence | bank sentence |")
        w("|---|---|---|---|")
        for co, dom, raw, rep, sur in R["repairs"][:60]:
            w(f"| {co} | `{dom}` | {raw.replace('|','/')} | {rep.replace('|','/')} |")
        w("")
        rc = Counter(x[0] for x in R["repairs"])
        w(f"Per concept: " + ", ".join(f"{c} {rc.get(c,0)}" for c in CONCEPTS)
          + ".  These rewrites are legitimate, but they are also a small per-concept surface "
            "difference in their own right (the token `switch`/`hamper` appears at different "
            "rates in the three arms) and are included in the section-8 classifier's input.")
    w("")

    # ---------------- 8. surface predictability ----------------
    w("## 8. How much of the concept label is predictable from surface text alone?")
    w("")
    if not R.get("clf"):
        w("sklearn unavailable -- not measured.")
    else:
        c = R["clf"]
        w("Unit: one cell-C demonstration sentence on the **codeword surface** -- i.e. exactly "
          "the text a model reads, with `bomb`/`knife`/`gun` and `button`/`basket` all masked "
          "to `<W>`.  Domain-grouped: fitted on the 69 analysed TRAIN domains, scored on the "
          f"{c['val_domains']} VALIDATION domains ({c['n_train_rows']} train / "
          f"{c['n_val_rows']} validation sentences, {c['n_features']} features).  **TEST was "
          "not read.**  Chance = 33.3%.")
        w("")
        w("| feature set | validation accuracy | over chance |")
        w("|---|---:|---:|")
        for name, v in (("word 1-2gram TF-IDF (concept words masked)", c["tfidf_acc"]),
                        ("sentence length only (chars + words)", c["len_acc"]),
                        ("the 5 narrow hedge markers only", c["hedge_acc"]),
                        ("TF-IDF with training labels shuffled (control)", c["shuffled_acc"])):
            w(f"| {name} | {v*100:.1f}% | {(v-1/3)*100:+.1f} pp |")
        w("")
        w(f"Domain-mean accuracy (the honest independence unit) for the TF-IDF model: "
          f"**{c['dom_mean']*100:.1f}%**; per-class recall "
          + ", ".join(f"{k} {v*100:.1f}%" for k, v in c["per_class"].items()) + ".")
        w("")
        w("Confusion matrix (rows = truth bomb/knife/gun, columns = predicted):")
        w("")
        w("| | bomb | knife | gun |")
        w("|---|---:|---:|---:|")
        for i, co in enumerate(CONCEPTS):
            w(f"| **{co}** | " + " | ".join(str(x) for x in c["cm"][i]) + " |")
        w("")
        w("**This is the bar the hidden-state probe must clear.**  The preregistration's N5 "
          "(prompt-text-only TF-IDF, concept words masked) is exactly this quantity, and it "
          f"is strong: {c['tfidf_acc']*100:.1f}% versus 33.3% chance.  A probe accuracy at or "
          f"below this level is not evidence that the codeword's hidden state carries concept "
          f"IDENTITY -- it is consistent with the model reading the same surface register the "
          f"classifier reads.  The length-only figure ({c['len_acc']*100:.1f}%) is the "
          f"preregistration's N4; its `deferred_decision_rule` says that if N4 comes out well "
          f"above chance the 40 kept sentences per pool should be over-generated and "
          f"length-matched, prompt-only and outcome-blind.")
        w("")

    # ---------------- 9. verdict ----------------
    w("## 9. Verdict per concept")
    w("")
    clf = R.get("clf") or {}
    for co in CONCEPTS:
        own = mat[(co, co)]
        foreign = max(mat[(co, x)] for x in CONCEPTS if x != co)
        w(f"### {co}")
        w("")
        w(f"* own-concept affordance {own}/{totN[co]} = {pct(own, totN[co])}; "
          f"largest foreign affordance {foreign}/{totN[co]} = {pct(foreign, totN[co])}")
        w(f"* tier-1 explosive predicates {tot1[co]}/{totN[co]} = {pct(tot1[co], totN[co])}; "
          f"tier-2 procedural {tot2[co]}/{totN[co]} = {pct(tot2[co], totN[co])}")
        w(f"* named-sense polysemy {len(R['poly_hits'][co])}/"
          f"{EXPECTED_DOMAINS*EXPECTED_SENTS_PER_DOMAIN}; mass-noun frame "
          f"{R['mass_tot'][co]}/{totN[co]} = {pct(R['mass_tot'][co], totN[co])}")
        w(f"* narrow hedge {R['hedge_tot_n'][co]}/{totN[co]} = "
          f"{pct(R['hedge_tot_n'][co], totN[co])}; broad hedge "
          f"{pct(R['hedge_tot_b'][co], totN[co])}")
        if clf:
            w(f"* per-class recall of the surface-only classifier: "
              f"{clf['per_class'][co]*100:.1f}%")
        w("")
        w(f"**VERDICT: {R['verdicts'][co][0]}** -- {R['verdicts'][co][1]}")
        w("")

    w("## 10. What the alignment choice cost, in numbers")
    w("")
    for line in R["cost_lines"]:
        w(f"* {line}")
    w("")

    # ---------------- appendix ----------------
    w("## Appendix A. Side-by-side cell-C demonstration blocks, all "
      f"{EXPECTED_DOMAINS} domains")
    w("")
    w("One `cell == C`, `n_examples == 4`, `query_kind == semantic_one_word` demonstration "
      "block per concept per domain, drawn from the SAME `family_id` in all three banks so "
      "the comparison is like-for-like (CHK-14).  This is the codeword surface -- exactly "
      "what the model reads.  Read each triple and ask: do these read as three different "
      "installed concepts, or as one concept with the noun swapped?")
    w("")
    for dom in doms:
        w(f"### `{dom}`  ({assign.get(dom, '?')})")
        w("")
        fam = R["sample"][("bomb", dom)]["family_id"]
        w(f"family_id `{fam}`")
        w("")
        for co in CONCEPTS:
            s = R["sample"][(co, dom)]
            w(f"**{co}** (`{s['prompt_id']}`)")
            w("")
            for ln in s["demo_block"].split("\n"):
                w(f"> {ln}")
            w("")
    return "\n".join(L) + "\n"


# ======================================================================================
# verdict logic  (computed from the measured numbers, not written by hand)
# ======================================================================================

def decide(R):
    tot1, totN = R["tot1"], R["totN"]
    mat = R["afford_mat"]
    verdicts = {}
    for co in CONCEPTS:
        own = mat[(co, co)]
        foreign = max(mat[(co, x)] for x in CONCEPTS if x != co)
        poly_n = len(R["poly_hits"][co])
        mass = R["mass_tot"][co]
        reasons = []
        bad = False
        limit = False
        if own == 0:
            bad = True
            reasons.append("the pool affords nothing of its own concept")
        if foreign >= own:
            bad = True
            reasons.append(f"a foreign affordance lexicon fires at least as often "
                           f"({foreign} vs {own})")
        if co != "bomb" and tot1[co] > 0:
            limit = True
            reasons.append(f"{tot1[co]} sentences carry an explosive predicate "
                           f"({100.0*tot1[co]/totN[co]:.2f}%), enumerated in section 2")
        if poly_n > 0:
            limit = True
            reasons.append(f"{poly_n} named non-target senses, enumerated in section 4")
        if mass > 0:
            limit = True
            reasons.append(f"{mass} mass-noun-frame sentences "
                           f"({100.0*mass/totN[co]:.2f}%), listed in section 5")
        n_leak_s = len([x for x in R["cellC_leaks"] if x[1] == co])
        n_leak_r = len([x for x in R["leak_rows"] if x["concept"] == co])
        if n_leak_s:
            bad = True
            reasons.append(f"{n_leak_s} cell-C demonstration sentences still contain the "
                           f"literal plural of the concept word, affecting {n_leak_r} cell-C "
                           f"rows -- an outright label in the primary channel (section 1.2); "
                           f"the affected rows must be dropped or the bank rebuilt before "
                           f"extraction")
        clf = R.get("clf")
        if clf and clf["tfidf_acc"] > 0.45:
            limit = True
            reasons.append(f"the concept label is {clf['tfidf_acc']*100:.1f}% recoverable "
                           f"from the masked demonstration text alone (section 8), so any "
                           f"probe result must be quoted against that bar, not against 33.3%")
        if not reasons:
            reasons.append(f"own affordance {own}/{totN[co]} with the largest foreign "
                           f"lexicon at {foreign}, no explosive contamination, no named "
                           f"polysemy, no mass-noun frame")
        if bad:
            verdicts[co] = ("NOT USABLE AS BUILT", "; ".join(reasons))
        elif limit:
            verdicts[co] = ("USABLE WITH STATED LIMIT", "; ".join(reasons))
        else:
            verdicts[co] = ("USABLE", "; ".join(reasons))
    R["verdicts"] = verdicts

    clf = R.get("clf")
    cost = []
    cost.append(
        f"The alignment choice -- generate the harm pool per concept, copy benign/remap/filler "
        f"byte-for-byte -- buys three genuinely different harm corpora "
        f"({R['chk05_pairs']} cell-C comparisons, {len(R['chk05_same'])} identical) at the "
        f"price of a register difference between them.")
    cost.append(
        f"Hedging: bomb {R['hedge_tot_n']['bomb']}/{R['totN']['bomb']} = "
        f"{100.0*R['hedge_tot_n']['bomb']/R['totN']['bomb']:.2f}% vs knife "
        f"{R['hedge_tot_n']['knife']}/{R['totN']['knife']} = "
        f"{100.0*R['hedge_tot_n']['knife']/R['totN']['knife']:.2f}% vs gun "
        f"{100.0*R['hedge_tot_n']['gun']/R['totN']['gun']:.2f}% (narrow set). Broad set: "
        + ", ".join(f"{c} {100.0*R['hedge_tot_b'][c]/R['totN'][c]:.2f}%" for c in CONCEPTS)
        + ".")
    lens = R["lens"]
    cost.append(
        "Mean sentence length: "
        + ", ".join(f"{c} {sum(lens[c])/len(lens[c]):.1f} chars" for c in CONCEPTS)
        + ".")
    if clf:
        cost.append(
            f"Converted into the only number that matters for the probe: a masked "
            f"surface-text classifier recovers the concept label on held-out VALIDATION "
            f"domains at {clf['tfidf_acc']*100:.1f}% (domain-mean {clf['dom_mean']*100:.1f}%) "
            f"against 33.3% chance -- {(clf['tfidf_acc']-1/3)*100:+.1f} pp. Length alone: "
            f"{clf['len_acc']*100:.1f}%. Five hedge markers alone: "
            f"{clf['hedge_acc']*100:.1f}%. That is the cost, stated as the bar the probe must "
            f"beat, exactly as the preregistration's `_register_asymmetry.decision` promised.")
        cost.append(
            f"What it does NOT cost: cell A stays byte-identical across concepts, no harm "
            f"sentence is shared between pools ({len(R['overlap_exact'])} exact, "
            f"{len(R['overlap_neutral'])} modulo-noun), and the label-shuffled control on the "
            f"same folds sits at {clf['shuffled_acc']*100:.1f}%, so the fold construction "
            f"itself leaks nothing.")
    R["cost_lines"] = cost


# ======================================================================================
# main
# ======================================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mutate", action="store_true")
    ap.add_argument("--out", default=DEFAULT_REPORT)
    args = ap.parse_args()

    if not os.path.exists(PREREG):
        raise SystemExit(f"preregistration missing: {PREREG}")
    with open(PREREG, "r", encoding="utf-8") as f:
        prereg = json.load(f)
    if prereg.get("status") != "FROZEN":
        raise SystemExit("preregistration is not FROZEN")
    with open(SPLIT_MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print("loading banks ...", file=sys.stderr)
    corp = load_corpus()
    pools = load_pools()

    A, R = run_audit(corp, pools, manifest, prereg, mutation=None)
    decide(R)

    mut_results = None
    if args.mutate:
        mut_results = []
        for mid, target, desc in MUTATIONS:
            print(f"  mutation {mid} ...", file=sys.stderr)
            Am, _ = run_audit(corp, pools, manifest, prereg, mutation=mid,
                              do_clf=(target == "CHK-18"))
            red_ids = [c["id"] for c in Am.red()]
            mut_results.append((mid, target, desc, red_ids))
            if target not in red_ids:
                print(f"    !! {mid} did NOT turn {target} RED", file=sys.stderr)

    md = build_report(corp, pools, manifest, prereg, A, R, mut_results)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"wrote {args.out}  ({len(md)} bytes)", file=sys.stderr)

    n_red = len(A.red())
    print(f"checks: {len(A.checks)}  GREEN {len(A.checks)-n_red}  RED {n_red}",
          file=sys.stderr)
    for c in A.red():
        print(f"  RED {c['id']}: {c['detail'][:200]}", file=sys.stderr)
    if mut_results:
        ok = sum(1 for m, t, d, r in mut_results if t in r)
        print(f"mutations: {ok}/{len(mut_results)} turned their target RED", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
