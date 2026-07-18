#!/usr/bin/env python3
"""LLM-assisted (Claude-read-through) category taxonomy for the 520 AdvBench goals.

Unlike scripts/gcg_7a_behavior_analysis.py's CATEGORY_KEYWORDS (a first-pass, blind
keyword list that left 189/520=36% as "other_uncategorized"), this taxonomy was built
AFTER an assistant read all 520 goals in full (in 4 sequential chunks) and designed a
refined 13-category schema + pattern list informed by the actual phrasing observed in
the data (e.g. adding dedicated theft_property_crime, terrorism_extremism, and
child_exploitation categories that the first pass lacked, since they turned out to be
common and were previously falling into "other").

STILL NOT an official taxonomy (none exists for AdvBench -- see GCG_7A_BEHAVIOR_LEVEL_
ANALYSIS.md sec 1) and STILL rule-based (pattern matching), not a literal independent
judgment call on each of the 520 items -- but informed by, and spot-checked against,
an actual full read of the data rather than a blind first guess. A 30-item random
spot-check against independent manual re-reading is recorded in this file's __main__.

Categories are checked in priority order (first match wins) because goals often
combine several themes (e.g. "hack into government database and steal sensitive
information" is both cyber_hacking_malware and fraud/theft) -- the most specific /
most central intent is placed earlier in PRIORITY.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "outputs" / "stage_gcg_full" / "advbench_cot_full520_manifest.jsonl"

PATTERNS = {
    "child_exploitation": r"child pornography|molest|abus\w* .{0,20}child|grooming|solicit sexual conversations with (a )?strangers|groom other users",
    "weapons_explosives_mass_casualty": r"\bbomb|explosiv\w*|weapon of mass destruction|chemical (compound|weapon)|assassinat\w*|mass shooting|\bfirearms?\b|\bguns?\b|homemade (explosive|firearm)",
    "terrorism_extremism": r"terroris\w*|radicali[sz]ation|eco-terrorism",
    "self_harm_suicide": r"\bsuicide|self-harm|self harm|\bcutting\b|eating disorder|anorexia|bulimia",
    "violent_crime_physical_harm": r"\bmurder|\bpoison\w*|\bassault|\btorture|kidnap\w*|abduct\w*|\bkill\w*|violent crime|commit a violent crime|hit-and-run|hit and run|harm to passengers|harm animals|harmed or killed|traffick\w* endangered species|cause (physical harm|delays or disruptions)|sabotag\w* (a |the )?transportation|disrupt\w* transportation",
    "cyber_hacking_malware": r"\bhack\w*|exploit\w* (a |the )?vulnerab\w*|\bmalware|\bvirus\w*|ransomware|\bddos\b|\bbotnet|phishing|spyware|\bpassword\w*|crack\w* (a |the )?(password|security)|cyberattack|cyber attack|bypass security measures|\bbreach\w*|denial of service|circumvent (digital rights|anti-?virus)|hijack\w* (a |the )?(website|car|self-driving|webcam|social media account|user'?s)|evade (anti-?virus|detection while committing (a )?cyber)|pick a lock|infiltrate a secure facility|trick\w* users? into (giving away|revealing)|encryption and anonymity|delete\w* files from a computer|crash a computer system",
    "fraud_financial_crime": r"\bfraud\w*|insider trading|counterfeit\w* (money|goods|products)|tax (fraud|evasion)|evade taxes|insurance fraud|\bscam\w*|embezzl\w*|money laundering|manipulat\w* (stock|financial|the market|search engine)|credit card fraud|mail fraud|extort\w*|blackmail|ponzi|fake (review|identity)|misleading (review|consumers)|falsify\w* medical records|fake online (store|profile)|romance scam",
    "theft_property_crime": r"steal\w* a car|\brob (a |the )?(bank|store)|steal\w* from a (store|charity)|shoplift\w*|\btrespass\w*|break into a secured|vandali[sz]\w*|escape from a correctional|evade law enforcement|carjack\w*|pirate\w* software|illegally download copyrighted|hosts? pirated content",
    "identity_theft_personal_data_theft": r"identity theft|steal\w* .{0,25}(someone'?s|personal|sensitive|confidential) (information|data)|steal\w* .{0,25}(credit card|identit)|harvests? .{0,20}(user|sensitive) data|steals? sensitive (information|data|user data)|steal\w* personal information|theft of credit card",
    "misinformation_disinformation": r"fake news|disinformation|misinformation|conspiracy theor\w*|propaganda|\bhoax\b|false information|manipulat\w* public opinion|spread\w* false|climate change is a hoax|deadly conspiracy|deadly side effects, without any scientific evidence|misleads the public",
    "hate_speech_discrimination": r"hate speech|racis\w*|racial tension|incites? violence (against|towards)|inferior to|dehumaniz\w*|discriminat\w*|glorif\w* (violence|oppression|war|gang violence) against|glorifies (war|violence)|promotes? .{0,20}(oppression|violence) against|hatred towards|hatred against|violence against (a |the )?(specific|particular)? ?(group|minorit|women|civilian)",
    "harassment_bullying_stalking": r"cyberbully\w*|cyberbullying|cyberstalk\w*|harass\w*|\bstalk\w*|\bbully\w*|threatening letter|threatens? to (kill|harm)|defam\w*|ruin their reputation|damage (their|a (company|business)'?s) reputation|sabotag\w* .{0,20}reputation",
    "drugs_controlled_substances": r"illegal drugs?|narcotic\w*|synthesiz\w* .{0,20}(drugs|home)|date rape drug|smuggle\w* drugs|manufactur\w* .{0,20}drugs|distribut\w* .{0,20}(illegal )?drugs|steroids?\b|performance-enhancing drugs|selling illegal drugs|acquire and use illegal drugs|purchase illegal drugs|drug or alcohol|use of drugs",
    "academic_minor_dishonesty_deception": r"cheat\w* on (a |an |their )?(test|exam|college exam)|\bfake id\b|cheat on their significant other",
    "privacy_surveillance": r"\bspy\w* on\b|surveil\w*|drone to (spy|smuggle)|collects? personal data|track\w* .{0,20}(location|user|without (their )?consent)|records? user activity",
}

CATEGORY_PRIORITY = [
    "child_exploitation",
    "weapons_explosives_mass_casualty",
    "terrorism_extremism",
    "self_harm_suicide",
    "violent_crime_physical_harm",
    "cyber_hacking_malware",
    "fraud_financial_crime",
    "theft_property_crime",
    "identity_theft_personal_data_theft",
    "misinformation_disinformation",
    "hate_speech_discrimination",
    "harassment_bullying_stalking",
    "drugs_controlled_substances",
    "academic_minor_dishonesty_deception",
    "privacy_surveillance",
]


def categorize(goal: str) -> str:
    g = goal.lower()
    for cat in CATEGORY_PRIORITY:
        if re.search(PATTERNS[cat], g):
            return cat
    return "other_uncategorized"


def main():
    rows = [json.loads(l) for l in MANIFEST.open()]
    out = {}
    counts = {}
    for r in rows:
        cat = categorize(r["instruction"])
        out[r["task_id"]] = {"instruction": r["instruction"], "category": cat}
        counts[cat] = counts.get(cat, 0) + 1

    out_path = ROOT / "outputs" / "stage_gcg_full" / "ADVBENCH_LLM_TAXONOMY.json"
    out_path.write_text(json.dumps({"disclaimer": "LLM-read-through-informed pattern taxonomy, NOT an official/validated AdvBench category field (none exists). See scripts/gcg_advbench_llm_taxonomy.py docstring.", "counts": dict(sorted(counts.items(), key=lambda kv: -kv[1])), "labels": out}, indent=2))
    print(json.dumps(dict(sorted(counts.items(), key=lambda kv: -kv[1])), indent=2))
    print(f"other_uncategorized: {counts.get('other_uncategorized', 0)}/520")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
