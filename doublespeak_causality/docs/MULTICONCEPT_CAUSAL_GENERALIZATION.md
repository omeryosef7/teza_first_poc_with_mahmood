# MULTI-CONCEPT CAUSAL GENERALIZATION — GATE F

*Asymmetry sprint deliverable (plan §15.5). Aggregate: `reports/ASYM_P4_MULTICONCEPT.json`,
produced by `scripts/asym_p4_aggregate.py`. Held-out (`heldout`) split only, StrongREJECT ≥ 0.5
recomputed from continuous per-item scores.*

**What this addresses.** The program's detailed causal result was localized almost entirely on
CARROT↔BOMB — the handoff's own stated limitation ("single concept pair per family; generality
across concepts assumed, not exhaustively tested"). This phase runs the causal battery on all
five pair benchmarks with the **frozen, concept-agnostic pooled L18 refusal axis, not
reselected per pair**, and the bomb-localized concept circuit (write L8–11 + carry heads).

Both effects are defined as **ablation minus its own matched-random control**, so they are
paired two-arm contrasts and "ablating anything moves behaviour" cannot masquerade as a
mechanism.

---

## 1. Results

| pair | test n | **refusal-specific ΔASR** | 95 % CI | McNemar p | **concept-specific ΔASR** | p | `ds_base` |
|---|---|---|---|---|---|---|---|
| **grenade** | 40 | **+0.525** | [+0.38, +0.68] | **9.5e-07** | **+0.048** | 1.0 | **0.350** |
| **cocaine** | 38 | **+0.500** | [+0.34, +0.66] | **3.8e-06** | −0.026 | 1.0 | 0.053 |
| **pistol** | 29 | **+0.414** | [+0.24, +0.59] | **0.00049** | *(running)* | — | 0.000 |
| **bomb** | 26 | **+0.385** | [+0.19, +0.58] | **0.00195** | +0.062 | 1.0 | 0.115 |
| **chlorine** | 27 | +0.185 | [−0.04, +0.41] | 0.18 (ns) | *(running)* | — | 0.000 |

**Refusal half:** 5/5 positive, **sign-consistent**, median **+0.414**, range
[+0.185, +0.525], **4/5 significant after Holm-Bonferroni**.
**Concept half:** null in every pair tested (3/3, all p = 1.0), sign-**inconsistent**
(−0.026 … +0.062), 0/3 significant.

`pooled_usable = False` for both halves — the ranges exceed the 0.25 heterogeneity bar, so no
pooled number is reported (plan §8.4).

---

## 2. The power constraint that decides how this is read

**Concept ablation can only LOWER ASR.** A null from a pair whose Doublespeak attack barely
succeeds is therefore not evidence of epiphenomenality — there was nothing to remove. Grading
each pair by the attack headroom it actually had (`ds_base` ASR on the held-out split,
threshold 0.15):

| pair | `ds_base` | concept-half test |
|---|---|---|
| grenade | 0.350 | **INFORMATIVE** |
| bomb | 0.115 | marginal |
| cocaine | 0.053 | marginal |
| pistol | 0.000 | **floor-limited — the attack does not work on this pair** |
| chlorine | 0.000 | **floor-limited — the attack does not work on this pair** |

This constraint was written into the execution log **before** the remaining arms landed, and
is enforced in code (`--min-ds-base`) rather than applied by hand afterwards.

The refusal half has no such problem: it *raises* ASR from a low baseline, so it has headroom
by construction. That asymmetry in testability — not an asymmetry in the phenomenon — is why
the two halves generalize so differently here.

---

## 3. GATE F — **PARTIAL**

> **The refusal half GENERALIZES.** Ablating the frozen, concept-agnostic refusal direction
> raises harmful behaviour on **5/5 concept pairs**, sign-consistently, with a median specific
> ΔASR of **+0.414** and 4/5 significant after family-wise correction — including on four
> concepts the circuit was never localized on. Chlorine's miss is explained by its
> baseline: the model already complies with **0.519** of direct chlorine requests, leaving
> little room to move, while its refusal_rate still collapses 0.444 → 0.037 under ablation.
>
> **The concept half is UNDERPOWERED across the family.** It is null wherever tested, but only
> **1 of 5 pairs (grenade)** had enough attack headroom for that null to mean anything.
>
> **Verdict: the full dissociation is properly demonstrated on 1 informative pair (grenade),
> consistent on 2 marginal ones (bomb, cocaine), and untestable on 2 (pistol, chlorine).
> "The dissociation is general across concepts" is NOT established by this experiment** and
> must not be claimed from it (plan Gate F: "Do not say 'general across concepts' from 2/5").

On grenade specifically — the one pair where both halves are powered — the dissociation is
clean: **refusal-specific +0.525 (p = 9.5e-07)** against **concept-specific +0.048 (p = 1.0)**
on the same 40 held-out items, with the concept effect's sign *positive* (destroying the
concept circuit did not reduce the attack at all).

---

## 4. Heterogeneity, reported rather than smoothed (plan §8.4)

1. **The Doublespeak attack is strongly concept-dependent** — `ds_base` spans 0.000 (pistol,
   chlorine) to 0.350 (grenade). Two of five concepts are effectively immune to the attack as
   rendered by this bench.
2. **Attack strength and refusal-lever strength are different axes.** Cocaine has almost the
   weakest attack (0.053) and the second-*largest* refusal lever (+0.500).
3. **The matched-random ablation control is not inert in every pair.** cocaine and bomb: 0.000
   at every dose. grenade: 0.225 vs a 0.150 baseline. pistol: 0.483 vs 0.414. chlorine: 0.482
   vs 0.519. "Random ablation is flat" is a **pair-dependent** statement, and the specific
   contrast (ablation − matched random) is what carries the claim.
4. **Baseline refusal differs widely**: cocaine and bomb refuse 100 % of direct requests;
   pistol 48 %; chlorine 44 %.
5. **Dose-response is not monotone everywhere** — chlorine peaks at α=0.5 (0.741) and falls at
   α=1.0 (0.667); pistol saturates at α=0.5.

---

## 5. Limitations
* The concept circuit ablated is **bomb-localized** (write layers 8–11 and 9 carry heads fixed
  from the CARROT↔BOMB mapping, per plan §8.2). A concept-half null on another pair could be
  mis-localization rather than epiphenomenality. This is a *sanctioned* reuse, but it caps how
  strongly the concept nulls can be read.
* `phase10`'s random control is count-matched but **not layer-band-matched** (its head pool
  spans all layers, while the carry heads live in L14–21).
* Two pairs contribute nothing to the concept half. A concept-generality claim needs pairs
  where the attack works — i.e. a bench-construction problem, not more GPU.
* Per-pair test n is 26–40; the refusal effects are large enough to clear this, the concept
  nulls are not.
