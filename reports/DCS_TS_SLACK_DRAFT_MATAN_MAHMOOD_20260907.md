# DRAFT — internal update for Matan & Mahmood (thesis-scale doublespeak phase)

**Status: DRAFT. Not sent to anyone. Omer to review before anything goes out.**

Hi both — where the thesis-scale phase stands, including the parts that went against us.

## What we built

An aligned 113-domain, three-concept population (`ts116m`, six banks, {button, basket} x {bomb,
knife, gun}), in which **only the harmful demonstrations differ between arms** — benign, remap,
filler, preamble, skeleton and query are byte-identical, verified 3,616/3,616, and the
corresponding hidden states from three separate extraction runs agree to max|diff| = 0.000e+00.
This replaces the earlier data, whose primary cell differed in **948 of 1008 rows** across arms
because each arm had been generated as its own separate corpus. Split is 67/23/23, frozen
before any outcome existed; the 23 test domains were read exactly once. One model,
Llama-3.1-8B-Instruct, pinned revision.

## On the specific things you asked for

- **Defined for BOMB specifically, not averaged over harm types**: done — bomb is contrasted
  against knife and gun as hard negatives, never pooled into "harmful".
- **Keep difference-in-means**: kept, and it is one of the two primaries (`PR-053`), not a
  fallback.
- **Linear probe**: run as the other primary (`PR-048`), layer 9, selection on validation only.
- **Enough data with proper train/test splits**: 113 domains, directions and selection fit on
  train/validation only, verdicts read once on 23 untouched test domains.
- **"What does the word actually refer to?"**: this is where the answer is unwelcome — see R-112
  below. Our cleanest instrument says the signal is about the prompt, not about that position.

## Results

**R-113 (probe).** The installed concept is linearly decodable from the residual stream at layer 9
at **0.9399** domain-mean 3-way accuracy over the 23 test domains, **23/23 above chance**,
clearing a concept-masked bag-of-words baseline of **0.9217 by 0.0182** — a real margin and a
narrow one, against a floor that is a point estimate with no interval. Both p-values are **at their
arithmetic floors** (k=23/23 exhausts the sign test; 0/10,000 exhausts the permutation), so they
describe design resolution, not effect size, and I am not quoting them as measurements.

**R-112 (position).** A control position **nine tokens downstream**, token-identical across arms
and containing no concept word, decodes the same labels at **0.9261** against **0.9446** at the
codeword. Under our preregistered Holm correction that difference does not survive. So this is a
statement about the **prompt**, not about the codeword position being special — and I trust it more
than any absolute number here, because both arms read identical text so every surface confound
differences out.

**R-111 (axes).** The residualised direction does **not** separate "was it remapped" from "which
concept" — it carries both (0.8309 and 0.8236, both above the surface floor). That hypothesis is
unsupported, and the check that caught it was preregistered for exactly this purpose. Separately,
an inherited number (~0.574) **reverses to 0.8856** once the baseline genuinely cancels — the old
value was an artifact of each arm having its own unaligned baseline.

## Not established

Causal use is **untested** — no intervention has been run this phase. Whether the demonstrations
install the concept **in the model**, rather than merely writing it in the text, is still being
measured (a readout run is in flight, no result yet). And one confound has no adequately powered
instrument on this dataset: the arms differ in **discourse register**, because naturally written
text about bomb hedges at 13.72% versus 0.20% (knife) and 2.33% (gun). Three attempts failed for
the same underlying reason — the confound is produced **by** the manipulation, so no re-analysis of
this corpus removes it.

## The one ask

Do we fund a **register-matched regeneration of the demonstration pools** for the next phase —
matched hedge rate, threat-lexicon density and sentence structure, with a stricter accept filter?
That is the only thing that turns register from a stated limitation into a controlled variable.
Otherwise we carry it as a permanent scope limit of this bank family.

---

**THIS IS A DRAFT. IT HAS NOT BEEN SENT TO ANYONE — not by Slack, email, or any other channel.**
