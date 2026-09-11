# DCS-CONT REVIEW-3 — STATISTICAL

Adversarial re-computation of the statistical claims that landed **after** REVIEW-2, i.e.
`external_md/DCS_BOMBNESS_REPRESENTATION_TO_CAUSAL_ASR_CONTINUATION_20260910.md`, CONT-ENTRY
**068–082**. REVIEW-2/STATISTICAL (`reports/DCS_CONT_REVIEW2_STATISTICAL.md`, entries 049–063) is not
repeated; where it already settled something I cite it and move on.

Everything below was **recomputed from the artifacts on disk** with
`/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`, CPU only, no SLURM, no GPU.
Corpora read: `cont1_behavioral_button_bomb_20260910_152806_272296`,
`cont1_behavioral_button_bomb_TEST_20260911_160414_251697`,
`cont1_behavioral_basket_bomb_20260910_113902_3966018`,
`s15_behavioral_button_gun_20260911_210424_1293102`,
`s15_behavioral_button_knife_20260911_150342_902441`, plus the six `ts116m_readout_*` runs. The
loaders are the repo's own (`scripts/dcs_cont_layerpos_map.py`: `load_split`, `load_corpus`,
`load_installation`, `family_slot`, `spearman`); the review instruments live in the session scratchpad
and nothing in `configs/` or `scripts/` was edited. **The TEST split was read only for `DR-072`, which
is already spent; no new TEST quantity was created for any other family.**

---

## VERDICT

**`DR-072` is clean and survives every attack I could mount on it.** `rho_test = +0.605431`, the
comparator `+0.547451`, 23/23 domains positive and the permutation null all reproduce **to the digit**
from the corpora. The missing interval is supplied: **`rho_test = +0.6054`, 95 % CI `[+0.528, +0.678]`**
(4000-resample domain bootstrap). The "declines monotonically" sentence in CONT-ENTRY 075 is wrong —
`0.6241 → 0.6784 → 0.6054` rises then falls — but the VALIDATION peak is not a selection artifact: with
one TRAIN-only predictor scored on both held-out sets, VALIDATION `+0.6784` vs TEST `+0.6069` differ by
`+0.0715`, 95 % CI `[−0.060, +0.184]`. The 23/23 sign statistic is exactly `0.5^23 = 1.2e-7` under the
null, and is **not independent** corroboration (null correlation with the pooled ρ is `+0.71`). The TEST
comparator margin, which REVIEW-2 could only bound as straddling zero on VALIDATION, is **`+0.0580`,
95 % CI `[+0.0157, +0.0984]`** on TEST. **A12 reproduces to the digit on all six contrasts**; its
`p = 0.00005` is exactly the 20000-draw floor and is nowhere labelled as one; multiplicity across the
six contrasts is immaterial; and the knife/gun reversal that `C-CONT-057` flags is itself significant
(codeword × contrast interaction `+0.1119`, CI `[+0.091, +0.133]`).

**Section 15 does not come through intact.** Three findings, in order of damage. (1) **The reported
permutation p-values in the §15 tables belong to a different statistic than the one the column and the
prose name.** The `perm_p` column reproduces exactly when computed for `rho_B` alone and not when
computed for `B − ctx`: knife's headline *"+0.0623, significantly non-zero, p at the 2000-permutation
floor"* is in fact **p = 0.071–0.085** (three implementations, two permutation schemes), with the
observed value sitting **below its own null's 95th percentile**; gun's reported `0.14643` is likewise
`rho_B`'s p, the difference's being `0.71`. At the domain level — the independence unit this program
declares everywhere else — knife's effect is `+0.0314`, 95 % CI `[−0.063, +0.126]`, positive in 47/90
domains, sign-flip `p = 0.51`: **statistically indistinguishable from gun**. (2) **The "matched
context-only prototype" is built from the two cells CONT-ENTRY 077's own alignment table reports as
0 % aligned to C, and its ≈0 value is an averaging artifact**: `ρ(cos(C,A)) = −0.1923` and
`ρ(cos(C,E)) = +0.2225`, so any average of them lands near zero — `(A+B)/2` gives `+0.2366` and
`(B+E)/2` gives `+0.4108`. Against the fair single-cell matched comparator the excess is **`+0.1598`,
CI `[+0.073, +0.244]`** (button) and `+0.1703` (basket), not `+0.4053`. (3) **The matched pairing does
no work at all**: replacing each slot's B twin with a *different* slot's B twin from the same domain
gives `+0.4163` (vs `+0.3823` matched) and the domain-mean B prototype gives `+0.5057`. The result is
about C's alignment with a domain-generic explicit-concept direction, not with its aligned twin —
which is exactly the thing §46's prerequisite 7 was supposed to be about.

**On the attenuation argument (CONT-ENTRY 082), the conclusion survives and the reasoning does not.**
The quoted `1.63×` sd ratio is a ratio of numbers from **two different populations** (bomb's `0.3739`
is the 1080-slot A12 population, knife's `0.2295` is the 900-slot §15 population); matched, it is
`1.20×` on the population the correlation is actually computed on. More fundamentally, a marginal sd
carries **no** information about rank attenuation: scrambling a fraction of bomb's `y` within domain
leaves the within-domain sd **exactly** `0.2955` while `B − ctx` walks `+0.4053 → +0.362 → +0.231 →
+0.176 → +0.091 → −0.022`. The like-for-like test the entry declined to build — quantile-map bomb's `y`
onto knife's exact within-domain marginal, bomb's ranks preserved — costs a factor of **1.41**
(`+0.4053 → +0.2869`), leaving a **4.6×** residual gap, not 6.5×. And the attenuation-proof estimator
exists and was not used: per-domain Spearman is *exactly* invariant to any within-domain monotone remap
of `y`, and it gives bomb `+0.4338 [+0.335, +0.533]` against knife `+0.0314 [−0.063, +0.126]`. So
"variance loss cannot explain the gap" **survives on a better argument**, while "knife's effect is real
and significant" **fails**, and A13's "concept-DEPENDENT, not concept-specific" loses its lower anchor.

---

## FINDINGS BY SEVERITY

### S1 (claim FAILS) — §15's reported `perm_p` is the p-value of `rho_B`, not of the `B − ctx` difference it is attached to

**Claim.** CONT-ENTRY 082: *"Knife gives **+0.0623** — significantly non-zero (p at the
2000-permutation floor, so not the gun-style inconclusive null)"*, and the tables in CONT-ENTRY
077/078/079/082 plus `reports/DCS_CONT_S15_{MATCHED_REFERENCE,CROSS_CODEWORD,GUN_CONTROL,KNIFE_CONTROL}.json`
print a `perm_p` in the same row as the `B − ctx` difference.

**Test.** Rebuilt the statistic from the corpora (all four ρ reproduce to the digit — see the
verification table below), then ran the within-domain label permutation on the **difference**, 2000
draws, predictor fixed; and separately on `rho_B` alone; and separately under a global (across-domain)
permutation; in two independent implementations (pure-Python `spearman` from the repo, and a vectorised
`scipy.rankdata` version).

| dataset | statistic | observed | null p50 / p95 / max | **p** | record's `perm_p` |
|---|---|---|---|---|---|
| bomb / button | `B − ctx` | +0.4053 | −0.0023 / +0.0843 / +0.1910 | **0.00050** (floor) | 0.00050 ✅ |
| bomb / basket | `B − ctx` | +0.3317 | −0.0020 / +0.0804 / +0.1684 | **0.00050** (floor) | 0.00050 ✅ |
| **knife / button** | **`B − ctx`** | **+0.0623** | −0.0009 / **+0.0710** / +0.1656 | **0.071** | **0.00050 ❌** |
| knife / button | `rho_B` | +0.1206 | — | **0.00025–0.00050** (floor) | — |
| **gun / button** | **`B − ctx`** | **−0.0196** | +0.0051 / +0.0743 / +0.1422 | **0.72** | **0.14643 ❌** |
| gun / button | `rho_B` | +0.0320 | — | **0.151** (4000 draws) / 0.157 (2000) | 0.14643 ✅ |

Knife's `B − ctx` under a *global* permutation: `p = 0.081`. Pure-Python replication at a third seed:
`p = 0.0845`. Alternative statistics checked for gun, to rule out a different mis-attribution:
`rho_B − rho_A` → `p = 0.292`, `rho_B − rho_E` → `p = 0.953` — neither matches `0.14643`; `rho_B` alone
does. **The `perm_p` column is `rho_B`'s.** For bomb both are at the floor, which is why the
mis-attribution is invisible on the two datasets the entries look at most.

**The domain-level test, which the phase's own independence unit requires.** Per-domain Spearman,
90 domains, 20000-draw sign-flip permutation, t-interval:

| dataset | `rho_B` | `rho_ctx` | **`rho_B − rho_ctx`** | 95 % CI | domains + | sign-flip p |
|---|---|---|---|---|---|---|
| bomb / button | +0.3794 | −0.0544 | **+0.4338** | [+0.335, +0.533] | 74/90 | <5e-5 (floor) |
| bomb / basket | +0.3465 | −0.0209 | **+0.3674** | [+0.275, +0.460] | 70/90 | <5e-5 (floor) |
| **knife / button** | +0.1022 | +0.0708 | **+0.0314** | **[−0.063, +0.126]** | **47/90** | **0.506** |
| gun / button | +0.0411 | +0.0789 | −0.0378 | [−0.135, +0.059] | 42/90 | 0.433 |

Slot-level domain bootstrap of knife's headline number: **`+0.0623`, 95 % CI `[−0.0251, +0.1506]`**
(B = 4000). Paired across concepts on the same 90 domains: bomb − knife `+0.4024`, CI
`[+0.263, +0.542]`; **knife − gun `+0.0692`, CI `[−0.051, +0.190]`, p = 0.256.**

**One more strike, from the site sweep** (all 20/23 sites, L24, same 900 slots): bomb's `B − ctx` at
`cw_demo_mean` is **the maximum over all 20 sites** (`+0.4053`; runner-up `cw_demo_last +0.3782`,
median `+0.048`). Knife's value at the same prespecified site is **16th of 23** — its own data give
`+0.2653` at `rel-4`, `+0.1931` at `rel-10`, `+0.1534` at `rel-9`, and a median of `+0.0991`. Knife's
"effect" at the prespecified site is *below the typical magnitude the same statistic takes at arbitrary
sites in the same knife corpus*.

**Survives / weakened / fails.** **FAILS.** Knife's `+0.0623` is not significant on the statistic it is
reported for, not significant at the domain level, and not distinguishable from gun's. Three
consequences, stated as corrections rather than fixes:
1. CONT-ENTRY 082's *"it is **not** unique to `bomb` either — knife's effect is real and significant"*
   is unsupported. The evidence supports **bomb ≫ {knife, gun}, with knife and gun both not
   established**, which is the "bomb is special on these three concepts" pole the entry rejected.
2. CONT-ENTRY 079's gun row (`−0.0196`, `p = 0.146`) should read `p = 0.72`. Its conclusion (gun
   inconclusive) is unaffected; only the number is wrong.
3. **In fairness to the record, "not established" is not "zero".** The domain-level test has
   `se = 0.0475`, MDE(80 %) `= 0.133`, and only **0.26 power** against a true effect of knife's pooled
   `+0.0623`. The data cannot separate "knife has a real effect ~6× smaller than bomb's" from "knife has
   none". That is the honest statement, and it is weaker than either pole CONT-ENTRY 080 pre-registered.

**Auditability note.** The §15 analysis script is **not in the repo** — only the four
`reports/DCS_CONT_S15_*.json` outputs. Every ρ in them reproduces exactly from the corpora; the
`perm_p` does not, and there is no code on disk to adjudicate what it computed. REVIEW-2 made the same
recommendation about entry 063's per-run counts.

---

### S1 (claim SURVIVES in sign, magnitude WEAKENED 2.5×) — the "matched context-only prototype" is near zero by construction

**Claim.** CONT-ENTRY 077/078: `cos(h_C, h_B)` predicts installation at `+0.3823` (button) / `+0.3223`
(basket) *"and exceeds the matched context-only prototype"* (`−0.0230` / `−0.0094`) by **`+0.4053`,
95 % CI `[+0.2943, +0.5101]`** — presented as satisfying §15's explicit two-part rule.

**Test.** Recomputed every reference at `cw_demo_mean` L24, within domain, 900 slots / 90 domains, and
built the comparators the entry did not.

| reference for `cos(h_C, ·)` | button/bomb | basket/bomb | knife | gun |
|---|---|---|---|---|
| **B — explicit concept, same harm context, exact 1-word swap** | **+0.3823** | **+0.3223** | +0.1206 | +0.0320 |
| **E — explicit concept, benign context** | **+0.2225** | +0.1520 | **+0.1377** | **+0.0885** |
| A — literal codeword, benign context | −0.1923 | −0.1187 | −0.0491 | +0.0055 |
| **`(A+E)/2` — the record's "matched context-only prototype"** | **−0.0230** | −0.0094 | +0.0583 | +0.0515 |
| `(A+B)/2` | +0.2366 | +0.2091 | +0.0821 | +0.0213 |
| `(B+E)/2` | +0.4108 | +0.3342 | +0.1636 | +0.0890 |

(All four record values reproduce to ≥ 6 decimals. The task brief's `(h_A+h_B)/2` reading of the
comparator is not what was computed; the record's own text — "mean of A and E" — is correct.)

**Three problems, in increasing order of seriousness.**

1. **The comparator's ≈0 is an averaging artifact.** `ρ(cos(C,A)) = −0.1923` and `ρ(cos(C,E)) = +0.2225`
   have *opposite signs*; their mean vector's cosine correlates `−0.0230`, essentially the average.
   Any comparator formed by averaging those two cells is near zero whatever the geometry does, and the
   table above shows the number is entirely a choice of which pair to average.
2. **The comparator is the *un*matched pair, and the entry printed the evidence.** CONT-ENTRY 077's own
   alignment table reports `B→C` agreeing on `seq_len`, `token_pos` and demo positions in **99 %** of
   slots, and `A→C` / `E→C` in **4 % / 4 % / 0 %**. So `B` is the only aligned reference and the
   "matched context-only prototype" is built from the two cells measured as *not* aligned to C. The
   `+0.4053` therefore confounds *reference is the explicit concept* with *reference shares C's
   demonstration context and token layout* — the one comparison §15 exists to keep separate.
3. **The fair comparator is E** — the same concept word, same word-swap relation to C, differing in
   demonstration valence rather than in alignment:

| contrast | button/bomb | basket/bomb | knife | gun |
|---|---|---|---|---|
| `B − ctx(A+E)/2` (record) | +0.4053 `[+0.296,+0.510]` | +0.3317 `[+0.236,+0.429]` | +0.0623 `[−0.025,+0.151]` | −0.0196 `[−0.109,+0.065]` |
| **`B − E` (fair, single-cell, matched swap)** | **+0.1598 `[+0.073,+0.244]`** | **+0.1703 `[+0.079,+0.265]`** | **−0.0171 `[−0.082,+0.049]`** | −0.0565 `[−0.139,+0.025]` |
| `B − A` | +0.5746 `[+0.455,+0.685]` | +0.4411 `[+0.339,+0.546]` | +0.1697 `[+0.068,+0.270]` | +0.0264 `[−0.065,+0.116]` |

Domain-level `B − E`: bomb/button `+0.1802 [+0.096,+0.265]`, p = 0.0001; bomb/basket `+0.1758
[+0.081,+0.271]`, p = 0.00035; knife `−0.0147`, p = 0.73; gun `−0.0376`, p = 0.36.

**Survives / weakened / fails.** **SURVIVES in sign, WEAKENED in magnitude.** §15's rule ("increases,
and exceeds a matched reference") is still met for bomb on both codewords against the *hardest* matched
comparator available, at `+0.16`, CI excluding zero. But `+0.4053` is the excess over a comparator
chosen from the unaligned cells and constructed from two opposite-signed terms; it should be reported
as **`+0.16` (vs E) with `+0.41` (vs the A/E mean) as the loose upper reading**, not the other way
round. For knife and gun the fair comparator shows **no excess at all** (both negative point estimates),
which is independent of, and consistent with, the S1 finding above.

---

### S1 (framing claim FAILS; substantive claim survives) — the matched pairing does no work; a mismatched partner does better

**Claim.** CONT-ENTRY 077: *"§15's matched reference was constructible all along… **B→C is fully
aligned in 928 of 930 slots**… This is exactly §15's construction, and the reason it looked impossible
before is that the phase kept reaching for A→C"*, promoting §46 prerequisite 7 ("aligned reference
comparisons") to ✅ **NOW MET**.

**Test.** If the *alignment of the specific pair* is what makes the measurement work, then breaking the
pairing while keeping everything else should destroy it. Within each domain I deranged the B partners
(every slot gets another slot's B state, no fixed points), 20 independent derangements; and separately
replaced B with the domain's mean B state.

| reference | button/bomb | basket/bomb | knife | gun |
|---|---|---|---|---|
| B, **matched** partner (the record's statistic) | +0.3823 | +0.3223 | +0.1206 | +0.0320 |
| B, **mismatched** partner, same domain (20 derangements) | **+0.4163** (sd 0.016) | **+0.3267** (sd 0.024) | +0.1582 | +0.0926 |
| **domain-mean B prototype** | **+0.5057** | **+0.4299** | +0.2007 | +0.1367 |

**Survives / weakened / fails.** The *substantive* claim — as installation rises, cell C's
demonstration-side state moves toward the explicit-concept state — **SURVIVES**, and is in fact
*stronger* when measured against a domain prototype. The *framing* **FAILS**: the slot-level alignment
that CONT-ENTRY 077 identifies as the missing piece contributes nothing (it is 0.034 *worse* than a
random same-domain partner, 2.1× the sd over derangements), and the quantity actually being measured is
alignment with a **domain-generic** explicit-concept direction. That matters for §46 prerequisite 7,
which asks for *aligned* reference comparisons: the box is ticked, but the alignment is not load-bearing
and the entry's narrative ("the bank already contains the matched pair, and that is why this works")
is not supported by the data it rests on.

---

### S1 (reasoning FAILS, conclusion SURVIVES on a different argument) — the knife/gun attenuation argument

**Claim.** CONT-ENTRY 082: *"its within-domain sd is **0.2295 against bomb's 0.3739**, a ratio of
**1.63×**, while the effect ratio is **6.5×**. Variance loss of 1.6× cannot produce an effect loss of
6.5×."* A13's entire narrowing ("concept-dependent, not general") rests on this.

**Test 1 — where the two sd numbers come from.** The formula is the **mean of per-domain population
sd** (ddof = 0); with that formula I reproduce both quoted numbers exactly, but **from different
populations**:

| | A12 population (12 slots/domain, 1080 slots) | §15 population (10 slots/domain, 900 slots, 4-cell complete) |
|---|---|---|
| bomb / button | **0.3739** ← *entry 079's and entry 082's number* | 0.2758 |
| knife / button | 0.2188 ← *entry 079's number* | **0.2295** ← *entry 082's number* |
| gun / button | 0.0849 ← *entry 079's number* | 0.0883 |

⇒ The `1.63×` is `0.3739 / 0.2295`, a ratio across two populations. Matched, it is **1.71×** on the A12
population and **1.20×** on the §15 population — the one on which the `+0.4053` and `+0.0623` are
actually computed.

**Test 2 — is the sd ratio even the right quantity? No.** Two constructions settle it.
*(a) Rank scramble.* Permute a fraction of bomb's `y` **within domain**. The y multiset per domain is
unchanged, so every moment — mean, sd, quantiles — is **exactly** preserved:

| fraction scrambled | 0.0 | 0.2 | 0.4 | 0.6 | 0.8 | 1.0 |
|---|---|---|---|---|---|---|
| `B − ctx` | **+0.4053** | +0.3620 | +0.2308 | +0.1760 | +0.0912 | −0.0225 |
| within-domain sd of `y` | 0.2955 | 0.2955 | 0.2955 | 0.2955 | 0.2955 | 0.2955 |

*(b) Monotone compression.* Per-domain Spearman is **exactly** invariant to any monotone remap of `y`
within a domain. So at one and the same sd ratio the effect ratio can be anything from 1× to ∞:
**the sd ratio carries zero information about rank attenuation**, and both the defence CONT-ENTRY 082
rejects and the arithmetic it rejects it with are non-sequiturs. (The entry half-sees this — *"Spearman
is rank-based, so variance compression attenuates it through ties and floor effects rather than by a
clean scaling law"* — and then quotes the ratio as if it bounded something.)

**Test 3 — the like-for-like comparison the entry declined to build.** Quantile-map bomb's `y` **within
each domain** onto knife's exact within-domain marginal (bomb's ranks preserved; knife's floor
structure, 54.3 % of slots below 0.01, imported wholesale), then recompute:

```
bomb  B-ctx, own y                                   +0.4053
bomb  B-ctx, y remapped to knife's exact marginal    +0.2869     <- costs a factor 1.41
knife B-ctx, actual                                  +0.0623
residual gap, like-for-like                          4.6x   (not 6.5x)
```

The 1.41 is real and is *not* rank-attenuation: the pooled statistic ranks **within-domain-centred**
values *across* domains, so it is invariant to a global monotone transform but **not** to a
within-domain one — it re-weights domains by their `y` spread. That is a property of the estimator the
record chose, and it is the one channel through which knife's marginal genuinely does cost effect size.

**Test 4 — the attenuation-proof estimator, which exists.** Per-domain Spearman is immune to Test 3's
channel by construction. Domain level (from the S1 table above): bomb **+0.4338 `[+0.335, +0.533]`**,
knife **+0.0314 `[−0.063, +0.126]`**, paired bomb − knife **+0.4024 `[+0.263, +0.542]`**, sign-flip p at
the floor.

**Survives / weakened / fails.** The conclusion *"variance loss cannot explain the gap"* **SURVIVES**,
on Tests 3 and 4 rather than on the sd ratio; the correct residual is **4.6×** on the pooled statistic
and "knife not distinguishable from zero" on the attenuation-proof one. The *reasoning* **FAILS**, and
the `1.63×` figure should be withdrawn (mixed populations; matched value 1.20×). The *other* half of
CONT-ENTRY 082's conclusion — "not unique to bomb either, knife's effect is real" — **fails** for the
reasons in the first S1 finding. Net effect on A13: what is licensed is **bomb ≫ knife ≈ gun on these
three concepts, with knife and gun each not established and the study underpowered (0.26) against an
effect the size of knife's point estimate**. The structural caveat the entry already records — three
concepts, installability confounded with geometry strength — stands and is the binding one.

---

### S2 (claim SURVIVES; every missing uncertainty supplied) — `DR-072` on TEST

**Claim.** CONT-ENTRY 075: `rho_test = +0.6054` on 230 slots / 23 TEST domains, fit on 900 slots /
90 train+validation domains, λ = 1e2 fixed, positive in 23/23, permutation `p = 0.00050` with the
predictor held fixed, inside the prespecified window `[0.55, 0.70]`.

**Reproduction (independent rebuild from the two corpora, ridge dual form per the frozen config).**

| quantity | reported | recomputed |
|---|---|---|
| fit / TEST shape | 90 doms / 900 slots, 23 / 230 | **identical** |
| `rho_test` | +0.6054 | **+0.605431** |
| comparator (ridge λ→∞) | +0.5475 | **+0.547451** |
| per-domain mean / median / positive | +0.6401 / +0.7212 / 23/23 | **identical** |
| null p50 / p95 / max, p | +0.0002 / +0.1204 / +0.2417, 0.00050 | −0.0015 / +0.1192 / +0.2351, **0.00050** (seed-level jitter only) |

**(a) Is the within-domain, predictor-fixed permutation the right null?** **Yes, and it is exact.**
With the predictor frozen by `configs/dcs_cont_dr072_f5_confirmation.json` and the TEST domains disjoint
from the fit domains, permuting `y` within domain is the complete conditional null: it leaves `x`, each
domain's `y` multiset and the block structure untouched and destroys only the within-domain
slot↔slot pairing. Two things it does **not** do, neither of them a defect but neither stated:
it says nothing about **between-domain** prediction (removed by centring — REVIEW-2 measured the
uncentred version at `+0.6139` on VALIDATION, so this costs nothing), and it prices **no search**,
because the search was paid for on other populations. `p = 0.00050` is exactly the 2000-draw floor
`1/2001` and is not labelled as one anywhere; here it does not matter — the observed `+0.6054` exceeds
the null maximum `+0.2351` by 2.6×, so the true p is many orders below the floor.

**(b) 23/23 domains.** Under the same null the per-domain sign is exactly symmetric (measured null
count: mean **11.50**, sd **2.39**, max 19 over 2000 draws, against `23 × 0.5 = 11.5`), so the exact
null probability is **`0.5^23 = 1.19e-7`** — far below what 2000 permutations can express. It is **not
independent evidence**: across null draws the pooled ρ and the positive-count correlate **`+0.71`**, and
in the observed data the count is a coarsening of the same 23 per-domain ρ whose mean (`+0.6401`) is
what the pooled statistic reports. It establishes **consistency of sign**, which is worth stating, and
nothing about magnitude. (REVIEW-2 said the same of the 22/23 on VALIDATION; the entry repeats the
statistic without the caveat.)

**(c) `0.6241 → 0.6784 → 0.6054`.** Two things. First, **the sequence is not monotone** — CONT-ENTRY
075's *"The estimate declines monotonically across populations"* is wrong as written; it rises by
`+0.054` then falls by `+0.073`. Second, the VALIDATION peak is **not** evidence of selection: the three
numbers come from three different estimators (TRAIN is LOO with nested λ; VALIDATION is a TRAIN-fit
predictor; TEST is a TRAIN+VALIDATION-fit predictor), so I made them comparable by scoring **one
TRAIN-only predictor** on both held-out sets:

```
TRAIN-only fit (67 domains), lambda=1e2, identical predictor:
  VALIDATION  +0.6784  (23 domains)      <- reproduces the record exactly
  TEST        +0.6069  (23 domains)
  VALIDATION - TEST = +0.0715   95% CI [-0.0596, +0.1838]   P(diff<=0) = 0.135
```

Two held-out sets of 23 domains each, one predictor, and the difference is well inside noise. Adding the
23 VALIDATION domains to the fit moves TEST from `+0.6069` to `+0.6054` — i.e. essentially nothing. **No
selection story is needed and none is supported.**

**(d) The CI the record does not have.**

| quantity | estimate | 95 % CI |
|---|---|---|
| **`rho_test` (pooled, domain bootstrap B = 4000)** | **+0.6054** | **[+0.5282, +0.6777]** |
| per-domain ρ, Fisher-z mean | +0.6722 | [+0.5970, +0.7356] |
| **TEST comparator margin (F5 − ridge λ→∞)** | **+0.0580** | **[+0.0157, +0.0984]**, P(≤0) = 0.004, F5 wins 15/23 domains |

The prespecified window `[0.55, 0.70]` contains the **point estimate**; the 95 % CI's lower limit
`+0.528` falls outside it. *"Lands inside the prespecified window"* is therefore a statement about the
point estimate only — consistent with REVIEW-2's finding that the window carries no decision weight in
the frozen rule anyway. Separately, the comparator margin that REVIEW-2 could only bound as
`[−0.003, +0.131]` on VALIDATION **excludes zero on TEST** (`+0.058 [+0.016, +0.098]`), so the
(correctly renamed) λ-tuning claim gains modest genuine support from the confirmatory read, with the
per-domain sign test still only 15/23.

**Survives / weakened / fails.** **SURVIVES**, in full, with the interval supplied and two wording
corrections (the "monotone decline"; the unlabelled permutation floor).

---

### S2 (claim SURVIVES to the digit; floor unlabelled, multiplicity immaterial) — A12 concept-dependence

**Claim.** CONT-ENTRY 080: six domain-paired contrasts on 1080 slots / 90 domains, 20000-draw sign-flip
permutation, 4000-resample domain bootstrap.

**Reproduction.** Recomputed from the six `ts116m_readout_*` runs via `load_installation`, restricted to
the 1080 slots shared by all three concepts within each codeword, train+validation, 90 domains:

| codeword | contrast | record | **recomputed** | record CI | **recomputed CI** | domains + |
|---|---|---|---|---|---|---|
| button | bomb − knife | +0.4314 | **+0.4314** | [+0.3858,+0.4747] | [+0.3868,+0.4741] | 89/90 ✅ |
| button | bomb − gun | +0.5166 | **+0.5166** | [+0.4766,+0.5546] | [+0.4779,+0.5548] | 87/90 ✅ |
| button | knife − gun | +0.0852 | **+0.0852** | [+0.0585,+0.1124] | [+0.0587,+0.1120] | 70/90 ✅ |
| basket | bomb − knife | +0.3612 | **+0.3612** | [+0.3241,+0.3992] | [+0.3237,+0.4006] | 88/90 ✅ |
| basket | bomb − gun | +0.3346 | **+0.3346** | [+0.3009,+0.3707] | [+0.2991,+0.3703] | 88/90 ✅ |
| basket | knife − gun | −0.0267 | **−0.0267** | [−0.0438,−0.0108] | [−0.0436,−0.0112] | 40/90 ✅ |

**Is `p = 0.00005` attainable with 20000 draws?** It is **exactly the floor**: `1/(20000+1) =
4.99975e-5`, which rounds to `0.00005`. Five of the six contrasts sit on it (zero exceedances) and the
sixth reproduces at `0.00100` against the reported `0.00110` (seed). **It is nowhere labelled as a
floor**; it should be written `p < 5e-5 (20000-draw permutation floor)`. The distinction matters because
`bomb − knife` and `knife − gun` are reported with the *same* p while their effect sizes differ 5× —
the floor is hiding a very large difference in evidential strength that the CIs do show.

**Multiplicity across the six contrasts.** Bonferroni α = `0.05/6 = 0.0083`; the largest reported p is
`0.00110`, and `0.00110 × 6 = 0.0066 < 0.05`. Every contrast survives the crudest available correction,
and the two headline ones survive it by four orders of magnitude. **Immaterial.**

**Is the knife/gun reversal real?** This is the claim `C-CONT-057` rests on, and it had no test. Paired
by domain across codewords (same 90 domains), the codeword × (knife − gun) **interaction** is
**`+0.1119`, 95 % CI `[+0.0905, +0.1332]`, positive in 77/90 domains, sign-flip p at the floor**. The
sign reversal is **not** sampling noise. `C-CONT-057`'s correction is correct and is now supported by a
test rather than by two point estimates.

**Are three concepts enough for the ordering claim?** No, and the limitation is of a kind the CIs above
cannot express. Every test here treats the **domain** as the unit, so what is licensed is *"across
domains, for these three specific concepts, `bomb` installs far above `knife` and `gun`"*. There is no
concept-level replicate, so no interval can be put on "concept-dependence" as a property of concepts;
`n = 3` also makes installability perfectly confounded with any other concept-level covariate (harm
salience, token frequency, sub-token count). CONT-ENTRY 082 states this for the *geometry*; A12 needs the
same sentence, and the phrase *"the doublespeak remap is strongly concept-dependent"* (entry 079)
should carry "on the three concepts this bank family contains".

**Survives / weakened / fails.** **SURVIVES.** Add the floor label, and the concept-level caveat.

---

### S3 (claim SURVIVES) — `DR-073a`, the basket ASR primary, is powered at its declared MDE

**Claim.** CONT-ENTRY 071: basket primary `−0.0090`, CI `[−0.0254, +0.0090]`, `p = 0.4017`, MDE(80 %)
`0.0254`, verdict **NULL, POWERED** — with the MDE's paired-sd input inherited from button via a
`×1.0975` proxy, which the entry discloses.

**Test.** Back-computed the realised precision from the persisted interval
(`outputs/dcs_cont/dr073_basket_primary.json`): half-width `0.01717` ⇒ `se = 0.00876` ⇒ per-domain
`sd = 0.0717` over 67 domains ⇒ **realised MDE(80 %) = 0.0245** against the prespecified `0.02541`.

**Survives / weakened / fails.** **SURVIVES.** The borrowed sd proxy came in slightly *conservative*
(realised precision marginally better than declared), so "POWERED" holds at the declared MDE rather than
being rescued by it. The entry's own three caveats — relative vs absolute framing, corrected rates being
upper bounds, necessity-only — are the binding limitations and I found nothing to add to them. REVIEW-2's
domain-unit verification of `scripts/dcs_cont_asr_primary.py` carries over unchanged (same script, same
declaration structure).

---

### S3 (characterisation, requested) — what `cos(h_C, h_B)` measures, and whether the readout can drive it

**What it is.** At `cw_demo_mean` the vector is the mean state over the **four demonstration codeword
rows**. Cells B and C are token-identical except for the surface word at exactly those rows
(` bomb` ↔ ` button`), and they share the harm demonstration pool; `PAIR_ALIGNMENT` classes them as
`absolute` and 928/930 slots agree on demo positions. So `cos(h_C, h_B)` is **how far the model's state
at the ` button` demonstration rows has moved toward the state it holds at the corresponding ` bomb`
rows** — a direct read-off of "has the in-context remap taken hold at the demonstration sites". Measured:
`cos(C,B)` mean **0.6545**, sd 0.0445; `cos(C,A)` mean **0.8061** — at these rows the state is *closer to
the same-token/different-context cell than to the same-context/different-token cell*, i.e. token identity
dominates, and what §15 detects is the residual drift of the ` button` rows toward ` bomb`. The sign
structure the entries note (toward B, away from A) is exactly that, and it is coherent.

**Can the readout drive it mechanically?** No shared arithmetic: `y_install` is
`softmax(logp_concept, logp_codeword)` on the **`semantic_one_word`** prompt, while `h_C` is read on the
**`behavioral`** prompt — different prompts, different forward passes, and `load_corpus` refuses a
predictor corpus that is not `query_kind == behavioral` precisely to prevent the adjacency. Four checks
for a common numerical driver, all negative:

| control | button/bomb | basket/bomb | knife | gun |
|---|---|---|---|---|
| `ρ(‖h_C‖, y)` | −0.1905 | −0.2339 | −0.0993 | −0.0433 |
| `ρ(‖h_B‖, y)` | +0.0004 | −0.0717 | +0.0314 | +0.0737 |
| **`ρ(cos(h_A, h_E), y)`** — the *identical* button↔concept word swap under **benign** demos | **+0.0364** | +0.0602 | −0.0595 | +0.0077 |
| site specificity (`B−ctx` at `cw_demo_mean` vs 19 other sites) | **max of 20**, median +0.048 | — | 16th of 23 | — |

The `cos(A,E)` control is the informative one: the same one-word swap, the same two prompts, the same
cosine, under demonstrations that teach no remap, does **not** predict installation. So the correlation
is not a generic property of "two prompts one word apart", and it is not carried by state norms, and for
bomb it is sharply localised at the demonstration codeword rows.

**What remains, and cannot be tested on this bank.** Slots within a domain differ by their
**demonstration draw**, and the same draw enters both the behavioural prompt (where `h_C` is read) and
the semantic prompt (where `y` is read). A slot whose demonstrations happen to teach the remap harder
will raise both. That is a **common cause**, not circularity, and arguably it *is* the claim — but it
means the finding is close to tautological in content ("the state at the codeword looks more like the
state at the concept when the model reports the codeword means the concept") and is not independent
evidence about representational structure. `CONT-ENTRY 076` already established that the intervention
that would break this — a within-domain demonstration-side patch — is not constructible on this bank.

---

## VERIFICATION TABLE — what reproduced exactly

| entry | quantity | verdict |
|---|---|---|
| 075 | `rho_test` +0.6054, comparator +0.5475, 23/23, null p50/p95/max | ✅ to the digit |
| 077 | `rho_B` +0.3823, `rho_E` +0.2225, `rho_A` −0.1923, ctx −0.0230, diff +0.4053, CI [+0.294,+0.510] | ✅ to 6 dp |
| 078 | basket L24 +0.3223 / +0.1520 / −0.1187 / −0.0094, diff +0.3317 | ✅ |
| 079 | gun L24 `rho_B` +0.0320, ctx +0.0515, diff −0.0196; `y_install` means and within-domain sds (1080-slot population) | ✅ |
| 080 | all six A12 diffs, all six CIs, all six domain counts | ✅ to the digit |
| 082 | knife L24 +0.1206 / +0.0583 / +0.0623; knife within-domain sd 0.2295 (900-slot population) | ✅ values, ❌ population-matching |
| 077/078/079/082 | the `perm_p` column for `B − ctx` | ❌ reproduces only as `rho_B`'s p |
| 075 | "declines monotonically across populations" | ❌ the sequence is not monotone |
| 082 | "1.63× within-domain sd ratio" | ❌ mixed populations; matched = 1.20× (§15 pop) / 1.71× (A12 pop) |

## WHAT I DID NOT CHECK

* **`F6`'s corrected deflation curve (CONT-ENTRY 068)** — the rank 1/2/4/8/16 table was not recomputed;
  it is EXPLORATORY, carries no p-value, and the conclusion it reverses was already withdrawn.
* **The GPU noise-floor contrast (CONT-ENTRY 070)** — `+0.0149 [−0.018,+0.048]` raw and
  `+0.0015 [−0.015,+0.019]` corrected were taken as given; the completion-hash work is a data claim, not
  a statistical one, and REVIEW-2's design-effect finding about clustered ASR rows applies to it too
  (67 domains × 10 rows, same structure).
* **The basket `−0.2435` installation drop** and the button `−0.2150` — inherited from CONT-ENTRY 049 and
  already outside REVIEW-2's recomputation as well.
* **The C-CONT-058 clock-skew audit (CONT-ENTRY 081)** — no statistic depends on it, as the entry states.
* **Nothing new was read on TEST.** `DR-072`'s single read is spent; my recomputation re-scores the same
  frozen predictor on the same TEST corpus and creates no new confirmatory quantity.
