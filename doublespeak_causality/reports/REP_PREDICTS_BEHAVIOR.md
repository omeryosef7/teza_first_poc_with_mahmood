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
