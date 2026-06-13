# Literature Watch Alerts

_Prepared for Mahmood meeting, June 2026_

---

## Where to Set Alerts

### Google Scholar Alerts
URL: https://scholar.google.com/scholar_alerts

### Semantic Scholar Alerts
URL: https://www.semanticscholar.org/

### arXiv (cs.CR, cs.AI, cs.LG)
Alerts via: https://arxiv.org/ or RSS feeds at:
- cs.CR (Cryptography and Security): https://arxiv.org/list/cs.CR/recent
- cs.AI (Artificial Intelligence): https://arxiv.org/list/cs.AI/recent
- cs.LG (Learning): https://arxiv.org/list/cs.LG/recent

---

## Recommended Search Strings

### Primary: Our Direct Topic

| Search String | Platform | Alert Frequency |
|--------------|----------|----------------|
| `"chain-of-thought hijacking" LLM` | Google Scholar, Semantic Scholar | Weekly |
| `"reasoning hijacking" safety LLM` | Google Scholar | Weekly |
| `"CoT hijacking" safety` | Semantic Scholar | Weekly |
| `"delayed safety" reasoning language model` | arXiv | Weekly |
| `"thinking trace" safety jailbreak` | arXiv, Google Scholar | Weekly |
| `"puzzle wrapper" LLM safety` | Google Scholar | Monthly |

### Secondary: Representation-Level Attacks

| Search String | Platform | Alert Frequency |
|--------------|----------|----------------|
| `"representation hijacking" language model` | Semantic Scholar | Weekly |
| `"in-context representation" safety attack` | arXiv | Weekly |
| `"doublespeak" LLM safety` | Google Scholar | Monthly |
| `Layer activation jailbreak reasoning` | arXiv | Weekly |

### Tertiary: Safety-Before-CoT and RL for Safety

| Search String | Platform | Alert Frequency |
|--------------|----------|----------------|
| `"safety before chain-of-thought"` | Google Scholar, arXiv | Monthly |
| `"reasoning safety commitment" LLM` | arXiv | Monthly |
| `RLHF jailbreak reasoning model` | arXiv | Monthly |
| `"Qwen3" safety jailbreak reasoning` | arXiv | Monthly |
| `"extended thinking" safety attack` | Google Scholar | Monthly |

---

## Citation Tracking Table (Template)

Use this table to track new papers you find:

| Date Found | Title | Authors | Venue/ArXiv ID | Our Relevance (H/M/L) | Key Finding | Action |
|-----------|-------|---------|---------------|----------------------|-------------|--------|
| 2026-06-11 | LITERATURE_BRIDGE_DELAYED_SAFETY_COMMITMENT.md covers these | — | — | — | — | done |

---

## CoT Hijacking Paper Citation Status

**Note on local verification:**

The CoT Hijacking paper (the anchor paper for this research) can be located in the repo at:
- `Chain_of_Thought_Hijacking/` (local copy or related code)

As of June 2026, to check citation information:
1. Search Google Scholar for the exact title of the CoT Hijacking paper
2. Check OpenReview if the paper was submitted to ICLR, NeurIPS, or ICML
3. Semantic Scholar: search for the paper title to see forward citations

**Action:** Check citation counts and any citing papers before the meeting to see if
the community has already extended the behavioral findings. Citation information
cannot be verified locally — requires web search.

---

## Key Concepts to Track (Terminological Variants)

Different papers use different names for related phenomena:

| Our Term | Common Variants in Literature |
|---------|------------------------------|
| Chain-of-Thought Hijacking | CoT hijacking, reasoning hijacking, thought injection |
| Delayed safety commitment | Safety reasoning delay, safety bypass via reasoning |
| Puzzle wrapper | Filler wrapper, benign preamble, reasoning misdirection |
| Onset timing | Safety trigger timing, refusal timing, commitment point |
| Behavior-conditioned direction | Behavioral steering vector, compliance direction |

---

## Suggested Review Schedule

| Cadence | Action |
|---------|--------|
| Before every meeting | Check arXiv cs.CR and cs.AI for last 2 weeks |
| Monthly | Run all search strings on Semantic Scholar |
| Quarterly | Full Google Scholar alert review + citation check on anchor papers |
| Before paper submission | Comprehensive related work sweep |
