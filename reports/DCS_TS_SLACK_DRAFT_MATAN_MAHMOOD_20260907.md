# DRAFT — internal update for Matan & Mahmood (thesis-scale doublespeak phase)

**Status: DRAFT. Not sent to anyone. Omer to review before anything goes out.**

Hi both — where the thesis-scale phase stands, including the parts that went against us.

## What we built

An aligned 113-domain, three-concept population (`ts116m`, six banks, {button, basket} x {bomb,
knife, gun}), in which **only the harmful demonstrations differ between arms** — benign, remap,
filler, preamble, skeleton and query are byte-identical, verified 3,616/3,616, and the
corresponding hidden states from three separate extraction runs agree to max|diff| = 0.000e+00.
It replaces earlier data whose arms had each been generated as a separate corpus. Split 67/23/23,
frozen before any outcome existed; the 23 test domains read exactly once. One model,
Llama-3.1-8B-Instruct, pinned revision.

## On the specific things you asked for

- **Defined for BOMB specifically, not averaged over harm types**: done — bomb is contrasted
  against knife and gun as hard negatives, never pooled into "harmful".
- **Keep difference-in-means / linear probe**: both kept, as the two primaries (`PR-053`, `PR-048`
  at layer 9), neither a fallback; selection on validation only.
- **Enough data with proper train/test splits**: 113 domains, verdicts read once on 23 untouched
  test domains.
- **"What does the word actually refer to?"**: answered directly, and with no statistic. Asked
  exactly that on the concept-free channel (cell C, dose 4), the top answers are **` Bomb` 779**,
  ` Alarm` 119, ` Basket` 97 when **bomb** was demonstrated; ` Container` 348, ` Basket` 324,
  ` Button` 208 and **never ` Knife`** when knife was; ` Basket` 295, ` Button` 247 and **never
  ` Gun`** when gun was. The model says "Bomb" for bomb, and **answers with the codeword itself**
  for knife and gun. The other half of the answer is unwelcome — see R-112: the signal is about the
  prompt, not about that position.

## Results

**R-116 (installation — the newest result, and it changes what R-113 means).** Installation is no
longer an assumption: we measured it on all six banks, **32,544 rows, 113 domains**. On the
concept-free channel (cell C, dose 4), the fraction of 113 domains where the model reports the
concept at probability ≥ 0.5 is **bomb 0.619, knife 0.000, gun 0.009** — on the same 23 test
domains the probe used, **bomb 0.522, knife 0.000, gun 0.000**; median log-odds **+0.99 / −6.83 /
−7.38**. Per concept, never pooled: **bomb installs in a majority of domains, knife and gun do not
install at all.** That 0.5 is a labelled reference point chosen after I had seen four of the six
banks, **not a preregistered gate** — the primary reporting mode is the full 0.10–0.90 sweep
(bomb/knife/gun: 0.10 → 109/49/17, 0.25 → 103/3/2, 0.50 → 70/0/1, 0.75 → 21/0/0, 0.90 → 4/0/0).
**bomb ≫ {knife, gun} holds at every cut**; I had written that "the ordering" holds at every
cut, and that is too strong — knife and gun swap places at 0.50 (1 vs 0). The statement that
survives the whole sweep is just **neither knife nor gun installs**. All three arms do move in the right direction from the benign
baseline — direction yes, level no.

**R-113 (probe), and how R-116 narrows it.** The demonstration arm is linearly decodable from the
residual stream at layer 9 at **0.9399** domain-mean 3-way accuracy over the 23 test domains,
**23/23 above chance**, clearing a concept-masked bag-of-words baseline of **0.9217 by 0.0182** — a real margin
and a narrow one, against a floor that is a point estimate with no interval. Both p-values are **at
their arithmetic floors** (k=23/23 exhausts the sign test; 0/10,000 exhausts the permutation), so
they describe design resolution, not effect size, and I am not quoting them as measurements. **The
number stands; what it is a number about has changed**: it separates three classes, two of which do
not install, so it is not distinguishing *which concept was installed* — it is distinguishing
**which demonstration set is present**. That converges with R-112 from a completely independent
direction: R-112 says the signal is not localised at the codeword, R-116 says that for knife and gun
there was no installed concept for it to be localised *to*.

**R-116 (channels) — the thing I would most want to show you.** The **same rows** scored through our
two readout channels: on the concept-free channel knife installs in **0.000** of 113 domains; on the
forced-choice channel, **0.628**. The entire difference is that forced choice **names the answer in
its own question** — the concept word appears in the prompt on **100 %** of forced-choice rows and
**0 %** of concept-free rows, and on that channel the model picks **` Knife` 502 times in cell A**,
the *benign* baseline where no knife demonstration exists at all. Had the forced-choice channel been
primary, this phase would have reported that **all three concepts install** and that the probe
measures concept identity. Making the concept-free channel primary was recorded in PR-048 before any
of this was visible, against the known risk that its option mass would be too small to use — a risk
now retired (median 0.1138 against a 0.05 gate, though still a minority of the mass).

**R-112 (position).** A control position **nine tokens downstream**, token-identical across arms
and containing no concept word, decodes the same labels at **0.9261** against **0.9446** at the
codeword. Under our preregistered Holm correction that difference does not survive. So this is a
statement about the **prompt**, not about the codeword position being special — and I trust it more
than any absolute number here, because both arms read identical text so every surface confound
differences out.

**R-111 (axes).** The residualised direction does **not** separate "was it remapped" from "which
concept" — it carries both (0.8309 and 0.8236, both above the surface floor). That hypothesis is
unsupported, and the check that caught it was preregistered for exactly this purpose.

## Two things R-116 forces, briefly

**The codeword matters as much as the concept**: `button_bomb` installs in **92/113** domains,
`basket_bomb` in **46/113** — same concept, exactly half. "The concept installs" is under-specified
unless it names the codeword.

**And it changed the causal design before we spent GPU on it.** §10.1's patch arm was to move a
C_knife representation into a C_bomb prompt — but the knife donor installs nothing in 113/113
domains, so a null there would look identical whether or not the axis is causally used. That arm is
**demoted to exploratory**; §10.2's **projection-out becomes the primary causal test**, since it
acts on a bomb prompt where the concept does install.

## Not established

Causal use is **untested** — no intervention has been run this phase, on either arm. And one
confound has no adequately powered instrument on this dataset: the arms differ in **discourse
register**, because naturally written text about bomb hedges at 13.72% versus 0.20% (knife) and
2.33% (gun). Three attempts failed for
the same underlying reason — the confound is produced **by** the manipulation, so no re-analysis of
this corpus removes it.

## The one ask

Do we fund a **register-matched regeneration of the demonstration pools** for the next phase —
matched hedge rate, threat-lexicon density and sentence structure, with a stricter accept filter?
That is the only thing that turns register from a stated limitation into a controlled variable.
Otherwise we carry it as a permanent scope limit of this bank family.

---

**THIS IS A DRAFT. IT HAS NOT BEEN SENT TO ANYONE — not by Slack, email, or any other channel.**
