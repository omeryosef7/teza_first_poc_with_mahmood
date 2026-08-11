# TWO-SIGNAL SELECTIVE DEFENSE — GATE G

*Asymmetry sprint deliverable (plan §15.6). Run: `outputs/defense_2signal_clearharm_20260811_225420_751316`
(job 751316, 3317 s, a5000). Script `scripts/asym_p5_defense_2signal.py`.*

**Pre-registration note.** The n=3 smoke showed the concept axis scoring attack-structured
*benign* prompts **higher** than doublespeak attacks, and that warning — together with a
prediction that this phase would land as plan §17 **RESULT 8** (an honest negative) — was
written into the execution log **before** this run's arms were judged. The prediction held.

---

## 1. Design

**Hypothesis.** The concept circuit is behaviourally epiphenomenal, but that does not make it
useless: it might be a good *detector*. The refusal axis is the *actuator*. So restore refusal
**only when concept-remapping evidence is present AND refusal is suppressed**.

**Why it was worth testing.** The prior-sprint Gate-F gated defense used the refusal
projection alone and reproduced the unconditional tradeoff exactly, because attack-structured
benign prompts sit *below* the attacks on the refusal axis — a one-sided refusal threshold
fires on benign more than on attacks. The concept axis is near-orthogonal
(**cos = −0.0108** at L18, measured in this run), so it carries independent information.

**Features** — both read pre-generation, in one forward, at the decision token, `hs[19]`. No
future-token leakage by construction. **Thresholds fit on TRAIN only and frozen before any
test generation:** `T_refusal = 4.4778` (train direct-harmful refusal mean),
`T_concept = 2.0231` (train attack-structured-benign concept mean). Restoration =
`AllPositionAdd(L18, v_refusal, α)` with **α = 2.5893** (v3b-train-fit).

**Seven arms**, all derived from just two generations per (item, condition):
`none` · `uncond` · `gate_refusal` · `gate_concept` · `gate_two` · `gate_random` (Bernoulli
matched to gate_two's train fire-rate, p=0.4529) · `gate_shuffled` (features permuted within
split). **Five conditions**, each ≥40 unique test items: harmful doublespeak, harmful direct,
attack-structured benign, neutral/codeword benign, unrelated-normal.

---

## 2. Results

### TRAIN (n=85) — where the thresholds were fit. Looks like a win.

| arm | DS ASR | Δ vs none | p | benign over-refusal | Δ vs none | p |
|---|---|---|---|---|---|---|
| none | 0.282 | — | — | 0.377 | — | — |
| uncond | 0.129 | **−0.153** | 0.0044 | 0.741 | **+0.365** | 7e-08 |
| gate_refusal | 0.129 | −0.153 | 0.0044 | 0.741 | +0.365 | 7e-08 |
| **gate_concept** | 0.129 | **−0.153** | 0.0010 | 0.518 | **+0.141** | 0.0005 |
| **gate_two** | 0.129 | **−0.153** | 0.0010 | 0.518 | **+0.141** | 0.0005 |
| gate_random | 0.235 | −0.047 | 0.29 (ns) | 0.529 | +0.153 | 0.0002 |
| gate_shuffled | 0.224 | −0.059 | 0.18 (ns) | 0.541 | +0.165 | 0.0001 |

On train the two-signal gate **Pareto-dominates its random control**: it keeps the *entire*
unconditional ASR reduction (−0.153) while paying **39 %** of the over-refusal cost
(+0.141 vs +0.365), whereas the random gate buys a similar over-refusal saving (+0.153) but
**loses the ASR benefit** (−0.047, ns). That is a real signal that the gate features carry
information.

### TEST (n=42) — the locked evaluation. It all vanishes.

| arm | DS ASR | Δ vs none | p | benign over-refusal | Δ vs none | p |
|---|---|---|---|---|---|---|
| none | 0.143 | — | — | 0.452 | — | — |
| uncond | 0.191 | **+0.048** | 0.63 (ns) | 0.571 | +0.119 | 0.063 |
| gate_two | 0.167 | +0.024 | 1.0 (ns) | 0.476 | +0.024 | 1.0 (ns) |
| gate_random | 0.119 | −0.024 | 1.0 (ns) | 0.452 | 0.000 | 1.0 |
| gate_shuffled | 0.143 | 0.000 | 1.0 | 0.452 | 0.000 | 1.0 |

**No arm reduces DS ASR on the held-out set.** The unconditional defense nominally *increases*
it (+0.048, ns). The DS baseline on test is **0.143** — a floor, with almost nothing to
reduce.

### Unrelated-normal (n=40)
`refusal_rate = 0.000` for **every arm**, even though the refusal gate fires on **100 %** of
these prompts. Replicates the prior finding: the utility cost of refusal restoration is
confined to **attack-adjacent** inputs and does not spill onto ordinary requests.

---

## 3. GATE G — FAIL

The plan's criterion: a meaningful defense must **(1)** causally reduce DS ASR relative to no
defense, **AND (2)** reduce attack-structured-benign over-refusal relative to unconditional
restoration.

> **Criterion (1) FAILS on the locked test set** — ΔASR = **+0.048, ns, wrong sign**.
> Criterion (2) is therefore moot. **GATE G: HONEST NEGATIVE** (plan §17 **RESULT 8**).

### Three things that make this negative interpretable rather than merely null

1. **The "two-signal" gate is not two-signal.** `gate_concept` and `gate_two` are
   **numerically identical on every condition and both splits**. The refusal half of the AND
   contributes nothing, because the refusal gate fires on 87 % of attack-structured benign
   prompts and **100 %** of unrelated ones — a threshold that fires on almost everything
   cannot narrow anything. What was tested is effectively a *concept-only* gate.
2. **The over-refusal saving is not specific.** On train, `gate_two` (+0.141),
   `gate_random` (+0.153) and `gate_shuffled` (+0.165) have heavily overlapping CIs. **Any**
   gate firing at ≈45 % halves the over-refusal. Without the Bernoulli and shuffled-feature
   controls, the train numbers would have been reported as a two-signal win. They are the
   reason this is a negative rather than a false positive.
3. **The concept axis points the wrong way, as pre-registered.** On test the concept gate
   fires on **0.262** of doublespeak attacks but **0.381** of attack-structured benign
   prompts — more on benign than on attacks, exactly the failure mode that sank the
   refusal-only gate. Train separability: `ds_concept 1.9934` vs
   `benign_attack_concept 2.0231`.

### The floor-effect caveat, stated plainly
Test DS ASR without any defense is **0.143**. A defense cannot demonstrate a reduction
against a baseline that is already near zero, so **this run does not establish that the
two-signal gate would fail on a split with real headroom** — it establishes that it did not
succeed here, and that its apparent train-side advantage is not attributable to the concept
signal. The train split (baseline 0.282) had headroom and there the *gates* did beat their
random control on ASR; that result is **EXPLORATORY** (thresholds were fit on the same split)
and cannot be promoted.

---

## 4. What would make this a fair re-test
1. A test cohort with **non-floor** DS ASR — the current v3 test split is too well-defended for a defense experiment. The untouched `dev` split (n=37) or a re-balanced cohort should be checked for baseline headroom *before* spending GPU.
2. A **concept axis fitted to discriminate attack from attack-structured benign**, rather than the current one (fit at `codeword_last` on the `dev` split for a different purpose). The present axis was never optimized for this decision and demonstrably orders the two conditions the wrong way.
3. A refusal threshold that actually **selects** — the current one fires on ~90–100 % of inputs, so it cannot contribute to an AND.

## 5. Verdict for the paper
> The concept circuit is behaviourally epiphenomenal **and**, as currently fitted, is not a
> usable attack detector either: it scores attack-structured benign prompts slightly *higher*
> than real doublespeak attacks. A gate built on it reproduces the unconditional
> refusal-restoration tradeoff, and its apparent train-side reduction in over-refusal is
> matched by a Bernoulli gate firing at the same rate. Refusal restoration remains
> **non-selective** even when given concept information. This is plan §17 **RESULT 8**.
