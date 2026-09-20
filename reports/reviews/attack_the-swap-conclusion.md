No files in the repo were touched; every script I ran is in `/tmp/claude-47249/-home-sharifm-students-omeryosef-first-poc-teza-first-poc-with-mahmood/4da49896-7f0f-40cd-a8f0-50b462615089/scratchpad/`. No sbatch, no git write ops.

---

# R10 ADVERSARIAL REVIEW — LENS: S-138 (THE AXIS SWAP)

## SUMMARY: no BLOCKER. Every committed number reproduced. The CONCLUSION is OVERSTATED.

I reproduced all three headline reads from `domain_means` independently of the reporting code. `+0.001499` vs reported `+0.00150`, rank 4 of 47; `-0.000145` vs reported `-0.00014`, rank 36 of 47; `+0.000900` rank 13; `+0.002236` rank 2. `X = 28` exceedances among 36 blind controls reproduced. Necessity `-0.00852`, 55/67, rank 1 of 9 reproduced from the report's own contrast block.

---

## WHAT SURVIVED MY ATTACK (report these as discharged, they are)

### (b) THE DOSE OBJECTION — DEAD. This was the most likely way to be wrong and it is not wrong.

I pulled `rescue_liveness` per row from `results.jsonl` for the swap arm, the native arm and 7 controls, joined on `prompt_id` over 663 common prompts:

```
arm                    written_mean   delta_mean    proj_mean  maxrel_vs_XSWAP
KO_AXIS                    0.067887     1.301569     0.067887       8.85e-16
XSWAP_FROM_BASKET          0.067887     1.301569     0.074751       0
KO_ORTH                    0.067887     1.301569     0.027763       8.85e-16
KO_SHUF0/15/12             0.067887     1.301569  0.048/0.045/0.034  4.01e-16
KO_RAND0/3/20              0.067887     1.301569  0.019/0.016/0.016  ~5e-16
```
`scratchpad/dose.py`. The swap arm writes a **bit-identical dose** to the native arm and to every control. `KO_AXIS` carries `norm_matched=False` and every other arm `True`, and its `proj_norm_mean == written_norm_mean` exactly — basis==norm-basis really is the identity, now measured per row rather than argued. **The rank is not measuring dose.**

Note for the record: `captured_energy_frac` does NOT track recovery. `KO_AXIS` captures *more* (0.0387) than `XSWAP` (0.0376) and recovers less, so "the swap captured more energy" is also dead.

### (a) THE COMPARISON IS FAIR. I diffed the argv myself and re-derived the staging anchor.

`scratchpad/an1.py` / `anchor.py`, RUNMETA argv parsed into flag maps:

```
KO_AXIS vs XSWAP_FROM_BASKET, 23 vs 24 flags, EXACTLY 5 differ:
  --arm  --tag  --rescue-basis  --rescue-basis-key  --rescue-norm-match-key
```
**`--model` is NOT among them** in the headline cell — both loaded `/tmp/dcs_snap_omeryosef/0e9e39f2…`. The `--model` discharge is only needed for basket/validation, and I re-derived that anchor from scratch rather than accepting gate output:

```
csi1_basket_validation_STAGEANCHOR_AXIS_20260920_170734_754715 (job 913232, commit 1cce381e, /tmp staged, normkey=cand_rank1)
csi1_basket_validation_KO_AXIS_20260916_090004_102474         (job 897658, commit a302f909, NFS hub, no normkey)
230 fired / 230 fired / 230 common
logp_concept logp_codeword semantic_logodds p_concept p_codeword top1_id
option_mass option_mass_core_pair readout consistency
  -> max|diff| = 0.000e+00, differing rows = 0, on all TEN fields
```
That is stronger than S-138 claims (it used six fields) and it simultaneously discharges a *git commit* difference. Both flags are genuinely inert.

### (e) LEAVE-ONE-DOMAIN-OUT — rank 4 survives everything. `scratchpad/loo.py`

```
SWAP basket->button TRAIN  (67 LOO fits): rank min=2 max=5 median=4  hist {2:1, 3:9, 4:49, 5:8}
NATIVE button      TRAIN  (67 LOO fits): rank min=30 max=37 median=36
SWAP button->basket TRAIN (67):          rank min=11 max=17 median=13
SWAP button->basket VALID (23):          rank min=2  max=3  median=2
```
No single domain carries any of the four ranks.

---

## (c) IS RANK 4 ACTUALLY DIFFERENT FROM RANK 36? YES — and this is the part that is real.

Control family (exactly the 46, `KO_ORTH` excluded) mean `+0.000284`, sd `0.000743`:

| | value | z vs family | rank |
|---|---|---|---|
| XSWAP_FROM_BASKET | +0.00150 | **+1.64** | 4 of 47 |
| KO_AXIS (native) | −0.00014 | **−0.57** | 36 of 47 |

2.21 control-sd apart. But the family z is the weak test. The strong one is **paired within the one report, on the same 67 domains, against the same KO baseline** (`scratchpad/an1.py`, `order.py`):

```
XSWAP_FROM_BASKET - KO_AXIS = +0.001644
   domain bootstrap ci95 [+0.000664, +0.002605]   p2 = 0.0014
   47 of 67 domains positive; sign test p = 6.5e-04
```
**The 32-rank gap is not noise.** And the probe ordering replicates with a near-constant magnitude in all three cells:

```
recipient BUTTON train  : basket probe - button probe = +0.001644  ci [+0.00066,+0.00261]  p=0.0014
recipient BASKET train  : basket probe - button probe = +0.001749  ci [+0.00069,+0.00288]  p=0.0007
recipient BASKET valid  : basket probe - button probe = +0.001770  ci [+0.00024,+0.00367]  p=0.019
```
That is an additive probe main effect, replicated three times. **The "C1 supported" half of the claim holds.**

---

## MAJOR-1 — "the STATE hypothesis is REFUTED" is absence of evidence. The recipient effect was never tested.

I built the 2×2 the entry's argument implies. Both TRAIN reports carry the *same 67 domain names* (intersection 67 of 67), so it pairs. `scratchpad/twoby2.py`:

```
                        probe=basket   probe=button
recipient=button          +0.001499      -0.000145
recipient=basket          +0.002649      +0.000900

PROBE main effect      +0.001696  ci95 [+0.000912,+0.002497]  p2 < 1e-4   <- established
RECIPIENT main effect  +0.001097  ci95 [-0.000569,+0.002890]  p2 = 0.201  <- NOT tested, not refuted
INTERACTION            -0.000105  ci95 [-0.001482,+0.001230]  p2 = 0.888
|recipient| / |probe| = 0.647
```

**Basket is a better recipient than button for BOTH probes**, by a point estimate 65% the size of the probe effect, and the confidence interval on that recipient effect comfortably contains values *larger* than the probe effect. The interaction is flat, which is exactly what "both a probe effect and a recipient effect, additively" looks like.

S-138's refutation argument is: "the STATE hypothesis predicts a transplanted direction lands where button's own axis lands; it did not." That is a refutation of a **pure**-state model with **zero** probe effect. Nobody's state hypothesis has to be pure. The data are equally consistent with *both* factors mattering, and the recipient factor is simply underpowered here.

Caveat stated honestly: this recipient contrast crosses button and basket, which the sprint's own rule forbids pooling. That cuts *for* my finding, not against it — the experiment contains no legitimate test of the recipient factor at all, so "REFUTED" has no measurement standing behind it.

**Minimal fix:** in the S-138 entry, replace "the STATE hypothesis is REFUTED" with "a pure-state model with no probe effect is refuted; the recipient factor is not estimated by this design." Do not edit the append-only entry — record the correction in a new entry.

---

## MAJOR-2 — the swap arm is not exchangeable with the control family it is ranked against.

`scratchpad/geom.py` / `cosrec.py`, computed from the `.pt` files directly:

```
cos(swap_cand_from_basket, button cand_rank1) = 0.556893     (gate 0f expected 0.5569 — verified)
torch.equal(swap_cand_from_basket, basket cand_rank1) = True  (it really is basket's axis)
|cos with native| over the 46 CONTROLS: min 0.0001  median 0.0156  MAX 0.1894
   -> the swap axis is 2.9x more aligned with the native axis than ANY control
```
The rank test's null requires the candidate to be exchangeable with the controls. It is not: the controls are constructed near-orthogonal to the native axis, the "foreign" axis retains 56% of it. `reports/DCS_CSI_EXCHANGEABILITY_basket_train_n46.json` tests shuffled-vs-random poolability only; nothing tests candidate-vs-family exchangeability, and by construction nothing can.

**I tried to convert this into an explanation and failed, and I am reporting the failure:**
```
Pearson r(|cos with native axis|, recovery) over the 46 controls = -0.027
linear fit extrapolated to |cos|=0.5569 predicts +0.000035; observed +0.001499 (resid +1.95 sd)
```
No trend. The alignment asymmetry does not explain rank 4. It is still an unstated assumption violation that belongs in the entry.

**Minimal fix:** state in the entry that the swap arm's rank p is descriptive, not a valid permutation p, because the candidate is not drawn from the control family's directional distribution.

---

## MAJOR-3 — an alternative mechanism the entry does not consider, and it is STATE-flavoured.

From `rescue_liveness`, `|cos(axis, the recipient's own knockout delta)|` averaged over 670 rows (`scratchpad/align.py`):

```
XSWAP_FROM_BASKET (basket's axis)  0.056749
KO_AXIS           (button's axis)  0.051459
best control (KO_SHUF0)            0.036661
```
**Basket's axis is a better fit to BUTTON's own knockout delta than button's own axis is.** That is not "the probe decides, not the recipient's state" — it is "button's state-delta has a real direction and button's rank-1 probe mis-estimates it while basket's happens to land closer." That reading is a *state* reading. It is not proven either (alignment predicts recovery only weakly among controls, r = 0.19, n = 46), but it is a live alternative that the entry's dichotomy does not contain.

---

## (d) THE SPLIT — rank 13 vs rank 2 IS within noise, and rank 13 is extremely fragile.

`scratchpad/split.py`:

```
button->basket TRAIN      n=67 cand +0.000900  z=+0.475  rank 13
button->basket VALIDATION n=23 cand +0.002236  z=+2.647  rank  2
VALIDATION - TRAIN = +0.001336  ci95 [-0.000895,+0.003720]  p2 = 0.254
train/validation domain overlap = 0
```
**Not distinguishable.** And on the fragility the entry asks about:

```
TRAIN      : nearest control ABOVE the candidate is +4.0e-05 away, nearest BELOW +2.3e-05 away
             rank under resampling of the 46 controls: [7, 19] (median 13)
VALIDATION : gaps +5.4e-04 / +5.4e-04
             rank under resampling of the 46 controls: [1, 4] (median 2)
```
Rank 13 sits in a dense pileup — six controls within 1e-4. S-138's point 1 ("at rank 2 of 47 the ordering is one control away from rank 3") understates it in the wrong direction: **the TRAIN number is the fragile one.** Reporting the split rather than picking a side was correct; the reason given should be that the two are statistically indistinguishable, not that validation has less power.

---

## MAJOR-4 — the report does not record which tensor the headline arm used.

```
in_sample["XSWAP_FROM_BASKET"]["basis_sha16"] = None
```
All 52 other arms carry a real sha16. The one arm the entire conclusion rests on is the one arm whose basis provenance the report leaves null. It is recoverable from `arm_meta.rescue_basis` + `basis_keys` and gate 0f checked the file, but the report cannot self-certify. Related: that same block reports `fit_domains_sha16 = 4614853e…` and `evaluation_is_in_sample = True` for the swap arm — those are **button's** fit domains, inherited by default; the swap basis was fit on basket. The field is meaningless for a swap arm and reads as if it were meaningful.

**Minimal fix:** populate `basis_sha16` from the donor key's tensor, and either null out or relabel `fit_split`/`fit_domains_sha16`/`evaluation_is_in_sample` for cross-codeword arms.

---

## MINOR findings

**MINOR-1 — `dcs_csi_pr006_native_vs_swap.py:24` uses a different estimator for the two numbers it exists to make comparable.**
```python
native = round(inst["KO_AXIS"] - ko, 5)        # difference of 5-dp-rounded pooled installation
swap   = crd["candidate"]                       # 5-dp-rounded DOMAIN-MEAN recovery
```
Measured gap between the two estimators over all 53 arms: **max 8.8e-6** — small, but on quantities of size 1.4e-4. And it already sits on an exact tie: `round(native,5) = -0.00014 == KO_SHUF16`, with a `v >= x` tie rule. I confirmed on unrounded `domain_means` that the true rank is 36 either way, so **no reported rank is wrong**. It is not guaranteed by the code. Minimal fix: compute both sides from `control_recovery_distribution` / `contrasts`, never from `installation_by_arm` differences.

**MINOR-2 — `dcs_csi_pr006_gate0.py` gate 0g allowlists `--model` by NAME, not by VALUE.**
`DISCHARGED = {"--rescue-norm-match-key", "--model"}` would pass a run that loaded a *different model revision*, not just a different path to the same one. The staging anchor discharged one specific path pair. Minimal fix: assert the two `--model` values end in the same revision sha.

**MINOR-3 — `dcs_csi_pr005_gate0.py` GATE 0(a) can silently drop up to 4 stage-1 arms from the GPU pin.**
```python
for a in STAGE1_ARMS:
    d = newest(a, STAGE1_JOBS)
    if d is None: continue          # silent
assert n >= 50
```
18 stage-1 arms are expected; `n >= 50` with 36 new arms tolerates 4 missing. In fact 54 were inspected and it did not bite. Minimal fix: `assert n == 36 + len(STAGE1_ARMS)`.

**MINOR-4 — the native arm's code is not recoverable from any commit, and I measured that it did not matter.**
```
KO_AXIS / KO / BASE / KO_FULL / KO_ORTH + 10 stage-1 controls: commit bc8e7779, git_dirty=True
XSWAP_FROM_BASKET: commit 1cce381e; the 36 new controls span 5 further commits
```
The candidate and its comparator were produced 3 days and several commits apart, and the comparator's tree was dirty. I tested for a code-cohort artefact (`scratchpad/an2.py`):
```
36 new-commit controls mean +0.000291   vs   10 old-commit controls mean +0.000258
difference +0.000034, permutation p = 0.902 (B=200000)
```
Nothing there — it is 2% of the +0.001644 effect. The staging anchor's bit-identity across `a302f909` -> `1cce381e` independently corroborates it. Recording it because "git_dirty=True on the arm that anchors the contrast" should not pass unremarked.

**MINOR-5 — the gates DO obey the S-134 rule.** I checked all seven new gate scripts. `pr006_gate0` asserts 3 run dirs / 3 log sets / key counts / row floors; `pr005_gate0` prints "36 expected | N FINISHED" and `sys.exit(2)` on any shortfall; `gate0d` and `stage_anchor` assert `fa/fb/common >= MIN_ROWS` and field presence per row; `native_vs_swap` asserts `len(ctrl)==46`; `primary_X` asserts the 10+36 partition is fully present. **No vacuous gate found this round.** That attack came up empty.

---

## VERDICT ON S-138: **OVERSTATED** (not refuted).

The measurement is sound. The mechanism sentence is not.

**Supported by what I measured:** a probe main effect, +0.0017, replicated in all three cells with overlapping CIs, p between 0.019 and 1e-4, dose-matched to 1e-16, LOO-stable, argv-clean, staging-inert.

**Not supported:** "the dissociation is a property of the PROBE, **not** of the recipient's representation," and "the STATE hypothesis is **REFUTED**." The recipient factor has a point estimate 65% the size of the probe factor and a CI that includes effects larger than it. The experiment did not test it.

**Also not supported by the project's own rule:** the commit title says "Basket's axis **rescues** BUTTON." `scripts/gates/dcs_csi_pr006_native_vs_swap.py` — run just now, unmodified — prints for that exact cell:
```
PRE-FIXED RULE: HELPS == rank <= 2  ->  swap does NOT help
```
z = +1.64 against its family, rank p = 0.085, `specificity_all_controls_rejected: false`, and the report's own `VERDICT` string is "**PRIMARY DOES NOT PASS**… It is INSIDE the controls, not above them." The sprint-log body is honest about this in its "What may NOT be said" section; the commit title and the S-138 headline are not.

### The honest wording

> Basket's axis, transplanted into button's knockout at an identical dose, recovers +0.00150 where button's own axis recovers −0.00014 on the same 67 domains and the same 46 controls: a paired difference of +0.00164, ci95 [+0.00066, +0.00261], p = 0.0014, 47 of 67 domains positive. The same ordering holds inside basket (+0.00175 train, +0.00177 validation). **A probe main effect is established and replicated.** The swap arm itself does not clear its preregistered bar — rank 4 of 47, p = 0.085, inside the control family — and its rank p is descriptive rather than a valid permutation p, because the swap axis retains cos 0.557 with the native axis where no control exceeds 0.19.
>
> **This does not refute the state hypothesis.** The recipient contrast, which this design does not test, has a point estimate of +0.0011 with ci95 [−0.0006, +0.0029] — 65% of the probe effect and compatible with more — and the probe-by-recipient interaction is flat (−0.0001, p = 0.89). The correct statement is that a **pure**-state model predicting **no** probe effect is refuted, and that probe and recipient contributions are jointly unresolved. A candidate mechanism the entry should carry: basket's axis is more aligned with **button's own** knockout delta (mean |cos| 0.0567) than button's own axis is (0.0515), which is a state-side reading of the same data.
>
> Direction B does not split: rank 13 (train) and rank 2 (validation) differ by +0.00134, ci95 [−0.00089, +0.00372], p = 0.25. The train rank is the fragile one — six controls lie within 1e-4 of it, and resampling the family gives [7, 19].