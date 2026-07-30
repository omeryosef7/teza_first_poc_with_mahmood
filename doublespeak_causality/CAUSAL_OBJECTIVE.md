# The Causal Objective — terms, and the intervention that validates (or kills) each

**CAUSAL_CORE_PLAN §7 + §16.12 (S10).** The plan's rule is explicit: *do not define the
objective via cosine similarity; a useful objective is a quantity interventions have shown to
control interpretation/behaviour, and every term must be validated by intervention before
optimizing.* This document applies that rule to the fixed pair (`carrot` ↔ `bomb`,
Llama-3.1-8B), using only results already on disk.

Evidence sources: S6 controls (job 693609), S6 dose (693607 `cloze`, 693608 `one_word`),
S5 replace (693597), S8 knockout (693623 per-layer, 693647 all-layers) and component
patching (693614), S11 gate (693655/6/7). All numbers are `p_concept` — the next-token
probability mass on the concept under a **gate-passing** safe semantic readout (S2).

---

## 1. The causal quantity

`J_causal = P(target interpretation | do(+d)) − P(target interpretation | do(−d))`

Measured on `NEUTRAL_CODEWORD` prompts at all codeword positions, α as a fraction of the
residual norm, directions cross-fitted on the opposite split.

**Important measurement caveat.** On `NEUTRAL_CODEWORD` the baseline is ≈0, so the `do(−d)`
half is **floor-limited**: it cannot go lower, and every negative-α cell is identically 0 *by
construction*. `J_causal` computed there is therefore one-sided. Downward control must be
measured where the score is high — by projecting the direction **out of a `DOUBLESPEAK`
prompt** (baseline 0.215 `cloze`). Both halves are reported below.

---

## 2. Term-by-term verdict

| # | candidate term (plan §7) | intervention evidence | verdict |
|---|---|---|---|
| T1 | semantic score along **`d_Direct`** at codeword positions | add on Neutral: early **+0.167**, mid **+0.533**, late **+0.971**; Holm-significant; **exceeds all 60 window-matched controls (180 across the three windows)** (control mean +0.00002, max +0.0002); monotone in α (Spearman +0.81/+0.86); position-specific (adjacent +0.013, random token +0.004); concept-specific (3 other remap directions exactly 0). Project-out on DS: mid **−0.157**, late −0.068. | ✅ **VALIDATED — bidirectional.** The load-bearing term. |
| T2 | projection on the **`d_DS`** direction / DS subspace | add at matched relative strength (‖d_DS‖/‖h‖ = 0.44 vs `d_Direct` 0.69): **exactly 0.0000** at every window, on **both** readouts. Project-out of DS: −0.03…+0.04. Replacement (Neutral←DS): matched by its own shuffled-source control. | ❌ **KILLED.** The obvious objective — "make the state look like the hijacked state" — is **causally inert**. It must not appear in the objective. |
| T3 | **early-Neutral retention** (`λ` term) | project-out `d_Direct` at **early** layers *increases* the final concept reading: **+0.192** (`cloze`) / **+0.280** (`one_word`). Adding `d_Direct` early is the *weakest* install (+0.167 vs +0.971 late) and raises the literal reading instead (p_codeword 0.008 → 0.488). | ✅ **VALIDATED**, and with the sign the plan predicted: suppressing concept content early *helps*. |
| T4 | semantic score inside the **attack window** | install and remove windows **differ**: install peaks **late** (+0.971), removal peaks **mid** (−0.157). Mid over-steers at α=2 (+0.536 → +0.328); late saturates (+0.987). | ✅ **VALIDATED, but not a single window** — see §3. |
| T5 | attention routing from the demonstrations | knockout is **not demonstration-specific**: all-layers `demos_all` −99.9% vs count-matched random −99.7%; per-layer −0.0057 vs −0.0077. Blocking only prior codeword occurrences: −2.8% (NS). | ❌ **KILLED as a term.** No evidence of a demonstration-specific route to optimize toward. |
| T6 | attention-output vs MLP-output component | all component patches ≤ 0.019; `Neutral_from_DS` exactly 0. | ❌ **KILLED** — no component-level handle at a single position. |
| T7 | early refusal-direction suppression (`β`) | **not measured in this sprint.** The readout here is *semantic*, not refusal; no refusal-direction intervention was run on the fixed pair. | ⬜ **UNVALIDATED — excluded.** Per §7 it must not enter the objective until an intervention supports it. |
| T8 | task-relevance retention (`γ`) | **not measured.** | ⬜ **UNVALIDATED — excluded.** |

---

## 3. The objective

Only validated terms enter it:

```
J_attack-window  =   J_semantic(d_Direct, MID..LATE)          # T1, T4
                   + λ · J_early-neutral-retention             # T3
```

with **no `d_DS` term** (T2 killed), **no routing term** (T5/T6 killed), and **no refusal or
task term** until T7/T8 are validated by intervention.

Concretely, for a candidate demonstration block `x`:

- `J_semantic(x)` = `p_concept` at the readout position — the same forward-only score used
  throughout, so it is directly comparable to every number in `CAUSAL_CORE_PROGRESS.md`.
- `J_early-neutral-retention(x)` = `−⟨h_early(x), d̂_Direct⟩` at the codeword positions,
  i.e. reward *low* Direct-component early. Sign fixed by T3, not assumed.

**Window guidance from T4:** the install and removal windows are not the same. An attack that
must *install* the reading should target late layers; a *defence* that wants to remove it gets
most leverage at mid. Reporting one "attack window" number would flatten a real asymmetry.

---

## 4. What this predicts, and the honest caveats

**Prediction.** An optimizer that maximises `J_attack-window` should move the reading; one
that maximises alignment to `d_DS` (the natural interpretability-derived objective, and the
one the prior sprint's temporal `repr_loss` most resembles) should **not**. That is a
falsifiable difference between the two objectives and is the cleanest thing S12 can test.

**Caveat 1 — `d_Direct` is close to a token substitution.** `d_Direct ≈ h_bomb − h_carrot`, so
adding it at every codeword position partly *is* soft-substituting the token, and the
near-ceiling +0.971 at late layers (immediately upstream of the readout) is consistent with
that. What makes it more than a norm perturbation is the specificity: adjacent/random token
sites do ~nothing, and three other remapping directions do exactly nothing. The objective
should be described as "the target interpretation is causally installable at the codeword
position", never as "we recovered the hijack's mechanism".

**Caveat 2 — the objective is defined on a *representation* score.** Per plan §9, a decrease
in this objective is **not** an attack success. S12's success criterion is held-out
**behavioral ASR**, and the causal score is only an intermediate.

**Caveat 3 — the `d_DS` null is the most load-bearing negative here**, so its own controls
matter: the DS arm demonstrably ran (10–12 layers patched at 4–9 positions), `d_DS` is a large
vector (0.44 of the residual norm), and `d_unrelated` at a near-identical norm ratio is also
inert — so the contrast is not magnitude. It replicates on both readouts.

**Caveat 4 — one pair, one model.** Everything here is `carrot`↔`bomb` on Llama-3.1-8B.
Per §15 this is not yet a general mechanism, and §16.18 gates scale-up on the fixed-pair chain.

---

## 5. Status of the chain (§2's ordering)

| step | question | answer |
|---|---|---|
| 1 | where do codeword and concept reps differ? | ✅ at the codeword position: `cos(d_Direct, d_DS)` = 0.28 there vs 0.83 at the final prompt token |
| 2 | when does the codeword acquire the meaning? | ✅ purely contextual — `d_DS` is *exactly zero* at `resid_pre` L0 (identical static embedding) |
| 3 | which intervention *causes* the target reading? | ✅ `d_Direct`, +0.533 mid / +0.971 late, beyond all 60 window-matched controls (each window) |
| 4 | which intervention *removes* it? | ✅ project-out `d_Direct` from DS, −0.157 mid |
| 5 | where does attention carry the mapping? | ❌ no demonstration-specific route found (random control matches) |
| 6 | is the causal quantity optimizable through tokens? | ⚠️ an existence proof says yes (real DS demos reach 0.476) but gradient relaxation retains only **0.43%** after discretization — an optimization gap |
| 7 | does the optimized rep improve real attack success? | ⬜ S12, not yet run |
