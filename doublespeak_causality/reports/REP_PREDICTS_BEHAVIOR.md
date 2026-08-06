# Item-level rep→behavior: a Doublespeak prompt's refusal projection predicts whether it jailbreaks

**Question.** The aggregate results show Doublespeak suppresses the refusal axis and that refusal is the
behavioral locus. Does this hold at the **item level** — do the DS prompts that actually jailbreak differ, in
their refusal-axis projection, from the ones that still refuse? (No GPU: joins two committed runs by item id —
the refusal projection from REFPROJ and the ds_base jailbreak outcome from BEHAV-REFUSAL, 86 clearharm / 51
curated items, full id overlap.)

**Method.** Per DS item: x = refusal-axis projection of the DS prompt at the decision token (REFPROJ, decoder
L21 / hs22); y = ds_base outcome (MALICIOUS vs not, BEHAV-REFUSAL). Mann-Whitney U (one-sided: malicious →
lower projection), point-biserial r, and AUC (does lower projection → jailbreak).

## Result — a strong, significant link on clearharm; a null on curated (explained)

| cohort | n (malicious) | DS-proj malicious (median) | non-malicious | **AUC** (low proj→jailbreak) | Mann-Whitney p | point-biserial r |
|---|---|---|---|---|---|---|
| **clearharm** | 86 (32) | **−1.15** | **+3.60** | **0.874** | **3.8e-09** | **−0.584** (p=3.7e-9) |
| curated | 51 (11) | +0.28 | −0.49 | 0.42 (ns) | 0.79 (ns) | +0.015 (ns) |

- **clearharm: the DS items that jailbreak are precisely those DS most suppresses on the refusal axis.** A DS
  prompt's refusal projection alone classifies its jailbreak outcome at **AUC 0.87** (p=4e-9) — the more DS
  pushes an item off the refusal axis, the more likely it complies. This is the aggregate refusal-locus result
  reproduced *per item*, and it directly explains the **partial base ASR** (~0.36): Doublespeak does not
  suppress refusal equally for every prompt; the ones it under-suppresses keep refusing.
- **curated: no link (p=0.79).** Not a contradiction — curated's DS refusal suppression is more **uniform**
  (projection spread std 1.84 vs clearharm 3.51; curated DS sits at/below benign for nearly all items). When
  refusal is suppressed for *everyone*, the projection cannot discriminate who jailbreaks — so the limiting
  factor on curated must be a **second mechanism**: the codeword remap often makes the generated answer about
  the *benign codeword* rather than the harmful concept (StrongREJECT scores it low even with refusal off). This
  is the concept-**dilution** side of "imperfect refusal suppression."

## Robustness — RECOMPUTED 2026-08-06, and the readout should move to L16

The numbers in the section below were previously quoted but emitted by **no committed code path**
(claim `RP-03`, UNVERIFIED). `scripts/analyze_rep_predicts_behavior.py --sweep` now recomputes them from
the **committed** `refproj` rows — no GPU, no new data — into `outputs/rep_predicts_behavior_sweep.json`.

**Indexing, because it is easy to get wrong:** `refproj` keys are `hidden_states` rows **1..32**, and
`hidden_states[k+1]` is post-block-`k`, so **hs `h` = decoder layer `h−1`**. The historical "L21" readout
is hs22.

**Layer stability — reproduces.** Decoder L17–L31 span **AUC 0.844–0.884**, inside the quoted 0.84–0.89.
**20 of 32** layers are Holm-significant over the 32-layer family.

**The important part — the result does not depend on the one layer whose axis is family-specific.**
P7 §4c validated 11 layers bidirectionally in **both** direction families. **All 11 are
Holm-significant here:**

| decoder layer | 13 | 14 | 15 | **16** | 17 | **18** | 19 | 20 | 24 | 28 | 29 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| AUC | 0.773 | 0.819 | 0.876 | **0.888** | 0.884 | **0.882** | 0.881 | 0.879 | 0.857 | 0.856 | 0.850 |

**Recommendation: re-anchor the readout at L16 (AUC 0.888) or L18 (0.882).** Both *beat* the historical
L21 value of **0.874**, and both validate in **both** direction families where **L21 validates in only
one** (the ClearHarm refit fails induce at L21 outright). This turns a caveat into a strictly better
result — L18 is additionally the direction every behavioral refusal arm in the project ablates.

**⚠️ The cross-validation figure does NOT reproduce.** The previously quoted *"5-fold CV AUC =
0.887 ± 0.106"* is not recoverable: the original fold assignment was never recorded. A deterministic
stratified 5-fold (seed 0) gives **0.869 ± 0.055** at L21 (folds 0.896 / 0.779 / 0.864 / 0.924 / 0.883).
**Cite that number, not the original.** Note also that CV is close to meaningless here — the "classifier"
is a single raw feature with no fitted parameters, so CV measures subsample stability, not generalization.

**curated is unchanged and remains a uniform null:** 0/32 Holm-significant, AUC 0.364–0.605.

## Robustness (audit)

The clearharm effect is **not a layer cherry-pick and not in-sample optimism**: single-feature AUC is stable
**0.84–0.89 across L17–L32** (all Mann-Whitney p<1e-7; only the early L13 is weaker at 0.69, as expected since
refusal is weakly represented early), and **5-fold cross-validated AUC = 0.887 ± 0.106** (out-of-sample logistic
regression on the single projection feature), matching/exceeding the in-sample value. Join verified by
per-item spot-check (low projection→MALICIOUS, high→REJECTED). Note the projection is essentially the model's
refusal-decision variable read at the decision token, so this is a *mechanistic localization* of the gate
(refusal is decided on this axis at this position), not a surprising external predictor — that it lands at
AUC~0.87 rather than 1.0 quantifies how much of the outcome the decision-token refusal axis alone determines.

## Interpretation

**Partial ASR has two sources, and this pins which cohort shows which:**
1. **Refusal re-engagement / under-suppression (clearharm):** ASR is limited because DS suppresses refusal to
   varying degrees; items it under-suppresses refuse — and the projection predicts exactly those (AUC 0.87).
2. **Concept-dilution (curated):** refusal is uniformly suppressed, but the codeword-substituted output is
   often benign, so it fails the harmfulness judge anyway.

Either way the refusal axis remains the **behavioral gate** (rows 2–3 of the results table): the item-level
link shows that where refusal-suppression *varies*, it is the variable that decides the jailbreak.

## Reproduce
`scripts/analyze_rep_predicts_behavior.py` (no GPU) — joins `outputs/refproj_<cohort>_*` (DS projection) with
`outputs/behav_refusal_<cohort>_a1.0_*` (ds_base label) by item id; Mann-Whitney U + point-biserial + AUC at
decoder L21 (hs22). Figure: `figures/rep_predicts_behavior.png`.
