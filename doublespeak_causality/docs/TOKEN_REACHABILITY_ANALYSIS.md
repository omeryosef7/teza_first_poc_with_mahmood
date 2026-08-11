# TOKEN REACHABILITY ANALYSIS

*Asymmetry sprint deliverable (plan §15.2). Methods are frozen and stated here BEFORE the
scaled results are read; the results sections are filled from the runs cited inline.*

**Question.** The refusal direction is a causal, dose-dependent, specific, quantization-robust
lever *when ablated in activation space*, yet targeting it with a token-space (GCG) objective
performs like a random direction. Is that because the direction is **not reachable from
suffix tokens**, or for some other reason?

---

## 1. Setup and notation

Let a doublespeak prompt be rendered with the chat template and a 16-token suffix placed at
the end of the **user** content (`suffix_placement=user`, byte-identical to the GCG optimizer
— we call `poc_stage_gcg_early.suffix_token_manager.build_suffix_spans` itself rather than
re-implementing it).

* `E ∈ R^{16 × d}` — the suffix token embeddings, `d = 4096`.
* `h_{ℓ,p} ∈ R^{d}` — the residual stream at `hidden_states[ℓ]`, token position `p`.
* `v ∈ R^{d}`, `‖v‖ = 1` — a target direction.
* `s(v) = ⟨h_{ℓ,p}, v⟩` — the scalar we care about (the refusal projection).
* `J = ∂h_{ℓ,p} / ∂E ∈ R^{d × 16d}` — the input→activation Jacobian at the base point.

### 1.1 Positions (load-bearing — see execution log E0.3)
Three different positions are in play across the program's code paths, and conflating them
was one of this sprint's Phase-0 findings:

| name | definition | who uses it |
|---|---|---|
| **`decision`** | last token of the templated prompt, i.e. after `<\|eot_id\|><\|start_header_id\|>assistant<\|end_header_id\|>\n\n` | where the refusal axis was **fitted** (`build_refusal_direction_llama.py:83`), where it was causally **validated**, and where the mech-validity readout measures it. **PRIMARY** here. |
| **`last_suffix`** | the last suffix token, still inside the user turn — 5 template tokens earlier | what the **GCG objective** read (`gcg_optimizer.py:687`). **SECONDARY**, reported to quantify the mismatch (defect D2). |
| all positions | every token, every decode step | what the **activation ablation** modifies (`pair_common.py:637`) — an intervention-scope asymmetry (defect D3). |

The template tail is **measured** from the live tokenizer, never hardcoded: render two
prompts whose user content differs only in its tail and walk backwards while the token ids
agree. For Llama-3.1-8B-Instruct this returns **5**, matching the manual token layout in E0.3.

### 1.2 Layer off-by-one
A direction file labelled `L{k}` was fitted at `hidden_states[k+1]`. Every script here takes
**fit** layers on the CLI and adds `+1` internally; both numbers are asserted at runtime and
written to `meta.json` (`fit_layers_refusal`, `hidden_states_index_rows`). Primary target:
refusal fit layer **L18 → `hs[19]`**; concept fit layer **L9 → `hs[10]`**.

---

## 2. Measurement 1 — local sensitivity `‖Jᵀv‖` (plan §5.2)

For a target direction `v`,

```
g(v) = ∂⟨h_{ℓ,p}, v⟩ / ∂E  =  Jᵀ v   ∈ R^{16 × d}
```

computed by a single forward pass followed by chunked **batched** reverse-mode autograd
(`torch.autograd.grad(h, E_suffix, grad_outputs=V, is_grads_batched=True)`, chunk 16, with a
per-direction loop as fallback if vmap rejects the attention kernel). Reported quantities:

* `‖Jᵀv‖` — the Frobenius norm over all 16 suffix positions (the headline sensitivity);
* `‖g_j(v)‖` for `j = 1..16` — the **per-suffix-position profile** (plan §5.2 question C);
* `⟨h, v⟩` at the base point, and `‖h‖`, so sensitivity can be read relative to scale.

All directions are **unit norm**, so `‖Jᵀv‖` is directly comparable across them.

> **This had to be written fresh.** `scripts/phase6_jacobian_readout.py` creates an
> `inputs_embeds` leaf but only to keep model weights out of the gradient buffer — it never
> reads `embeds.grad`, so no input-embedding Jacobian existed in the repo. GCG's
> `_token_gradients` is also unusable as-is: it differentiates a one-hot, **row-normalizes**
> the result (`gcg_optimizer.py:210`), and folds in an unconditional cross-entropy term.

### 2.1 Control families (four, in increasing strictness)
The first smoke run showed why one control family is not enough: **any** direction derived
from real activations beats an isotropic random direction, because the residual stream is
strongly anisotropic. So each cell carries:

| kind | construction | what it rules out |
|---|---|---|
| `random` | 100 isotropic unit vectors, `pair_common.norm_matched_random(seed=42+row)` | the plan's §3.8 norm-matched control |
| `actrandom` | 100 unit vectors drawn as `unit(Σ^{1/2} g)`, `Σ` = empirical residual covariance at that row | **⚠ DEGENERATE — see §2.3.** Intended as a diverse "looks like a real activation direction" null; in practice the covariance is rank-1-dominated so these draws are 97–99 % mutually parallel, i.e. effectively ONE direction. |
| `foreign` | the concept vector evaluated at the refusal row (and vice versa) | a real, structured, non-random but *wrong* direction |
| `otherlayer` | refusal directions fitted at L10/L14/L22, evaluated at the target row | the same mechanism, wrong depth |

`Σ` is pooled over all positions rather than only the two target positions: with 2 samples
per prompt the estimate would have rank ≤ 2·n_prompts (79 in a 4096-dim space) and sampling
from it would confine the control to a tiny subspace, making the null artificially strong.

### 2.2 Gate C statistic
Per prompt, the mechanism's `‖Jᵀv‖` is compared to the **per-prompt median** of the control
distribution, giving a paired sample across prompts. Reported: mean percentile among
controls, fraction of prompts above the control median, a MAD-based robust z, and a paired
bootstrap CI (10,000 resamples). Verdict ∈ {UNUSUALLY-LOW, NORMAL, UNUSUALLY-HIGH,
UNSTABLE}, where a CI containing 0 → NORMAL and 0.2 < consistency < 0.8 → UNSTABLE.

---

## 3. Measurement 2 — does the linear model predict REAL token moves? (plan §5.3, Gate B)

A first-order prediction is only meaningful if it survives contact with actual vocabulary
substitutions. For suffix position `j` and a substitution `t_old → t_new`:

```
predicted  Δs(v) = ⟨ g_j(v), e_{t_new} − e_{t_old} ⟩
actual     Δs(v) = ⟨ h(sub) − h(base), v ⟩
```

reported as Pearson `r`, OLS slope of actual-on-predicted, sign agreement, and relative
absolute error, per direction kind.

### 3.1 The ε-scan (added after the smoke run)
The first smoke showed poor agreement (`r ≈ 0.05–0.27`). That has two very different causes,
and the plan requires distinguishing them before any interpretation. A real token swap is a
**large** perturbation, so we walk continuously along the *same* direction:

```
e(ε) = e_{t_old} + ε · (e_{t_new} − e_{t_old}),     ε ∈ {0.01, 0.05, 0.1, 0.25, 0.5, 1.0}
```

`ε = 1` reproduces the real token swap exactly. Then:

* **agreement good at small ε, decaying toward ε = 1** → the Jacobian is **correct** and real
  token moves simply leave the linear regime. That is itself a result about why
  gradient-guided discrete search is hard here, and Gate B passes on the implementation.
* **disagreement even at small ε** → the implementation is broken and must be fixed before
  any scientific reading (plan Gate B).

---

## 4. Measurement 3 — the empirical local token-reachable subspace (plan §5.4)

For every real substitution `s` we keep `Δh_s ∈ R^d` and accumulate the second moment
`C = Σ_s Δh_s Δh_sᵀ` in a streaming fashion (blocks of 256, `C += BᵀB` on GPU). The
eigenvectors of `C` are exactly the right singular vectors of the stacked `Δh` matrix, so a
rank-`r` basis `U_r` follows from one eigendecomposition without ever materializing the
matrix. Then

```
R(v) = ‖U_rᵀ v‖² / ‖v‖²      for r ∈ {1, 2, 4, 8, 16, 32, 64, 128, 256}
```

Reported against **both** nulls: the isotropic expectation `r/d` and the empirical
distribution of `R` over the 100 `random` and 100 `actrandom` controls (percentile and ratio).

**Honesty constraints (pre-registered, gap matrix §E.5).**
* The candidate tokens are **direction-agnostic random vocabulary**, never
  refusal-top-gradient candidates — otherwise the candidate-selection rule itself would
  inflate `R(v_refusal)`.
* This is the ***empirical local* token-reachable subspace** — a finite candidate set at one
  base point. It is never described as "the vocabulary-reachable subspace".

---

## 5. Measurement 4 — cross-prompt coherence (plan §5.5)

A direction can be reachable on every prompt individually yet require a *different* token
move on each — which would explain why a **universal** suffix cannot exploit it. Per prompt
we store `g(v)` (flattened, `16d`), L2-normalize, and report:

* mean / median pairwise cosine across prompts, and the fraction of positive pairs;
* the eigenspectrum of the stacked `[n_prompts × 16d]` matrix, the fraction of variance in
  the top 1/3/5 components, and the participation ratio.

Compared between the mechanism direction and the control families. If refusal gradients are
no more coherent across prompts than random ones, universal-suffix failure becomes
mechanistically interpretable (H3/H5).

---

## 6. Results

### 6.1 Extended mechanistic validity of the ALREADY-OPTIMIZED suffixes (§19.1, §19.2)
*Run: `outputs/asym_p1c_mechval_20260811_212142_750363` (job 750363), analysis
`ANALYSIS_P1C.json`. Full tables in the execution log entry "PHASE 1c RESULT".*

**Reproduction first.** Seed 42, held-out, `decision`, L18→`hs[19]`: no-suffix baseline
**3.4023** (handoff 3.40), refusal-suffix drop **−1.664** vs random-suffix **−2.045**
(handoff Q5: −1.66 vs −2.04). Exact.

**(a) The Q5 conclusion does not replicate.** Refusal-optimized vs its matched random,
paired over 37 held-out prompts: seed 42 **+0.381**, seed 43 **−1.464** (37/37 prompts),
seed 44 **−1.345** (35/37); all p ≈ 1e-4. Mean drop across seeds: refusal **−2.013** (sd
0.513) vs random **−1.204** (sd 0.810). The mechanism suffix moves its own target **more**
than random on average; the published single-seed claim to the contrary rests on one
unusually effective random draw. **Gate D clause (ii) is WITHDRAWN as unsupported; clause (i)
— no ASR advantage — stands.** The dissociation therefore *sharpens*: token optimization can
control the internal coordinate, and behaviour still does not follow.

**(c) No train→held-out overfitting.** Transfer ratio (test drop / train drop) is **> 1 in
all 9 cells** (1.17–2.00): the universal suffix suppresses refusal *more* on held-out prompts
than on the pool it was optimized on. The "universal suffix overfits its suppression"
hypothesis is **rejected**.

**(§19.2) The suppression is generic and not localized at the target.** Across fit layers
L10–L24 the drop is ~0 before L14, grows monotonically with depth, and is deepest at **L24**
— not at the **L18** layer the objective optimized. The refusal-suffix and random-suffix
depth profiles are near-identical in shape, Pearson **r = 0.9965** (refusal vs vanilla
doublespeak r = 0.9968). **Strong support for H4 (generic adversarial suppression):** the
suffixes differ in the *magnitude* of a shared profile, not in *where* they act.

**(D2) The fit/use position mismatch is material.** Refusal-minus-random at `last_suffix`
(what the optimizer read) is **−0.067 / −0.063 / −1.013** across seeds, versus
**+0.381 / −1.464 / −1.345** at `decision` — ~20× smaller in 2 of 3 seeds, and the absolute
projections sit in different regimes (≈ −2.1 vs ≈ +1.7). Consistent with defects D1/D2: the
objective barely steered the coordinate it was pointed at, while the behaviourally relevant
coordinate moved a lot, generically.

### 6.2 Local sensitivity, finite-difference validation, subspace, coherence
*Runs: `asym_p1_reachability.py` on the frozen train pool (job 750361, n=40) and on held-out
test (job 750362, n=37); analysis `scripts/asym_p1_analyze.py` → `ANALYSIS.json`.*

**PENDING — jobs in flight at the time of writing.** This section is filled from
`ANALYSIS.json` (Gate B verdict, Gate C classification, `R(v)` table, coherence table) and
must not be written from the smoke run, whose n=2 / 4-control configuration is not
interpretable.

---

## 7. Reproduction

```
sbatch --export=ALL,ASYM_SPLIT=train,ASYM_NMAX=40 doublespeak_causality/slurm/run_asym_p1_reach.sh
sbatch --export=ALL,ASYM_SPLIT=test,ASYM_NMAX=37  doublespeak_causality/slurm/run_asym_p1_reach.sh
python doublespeak_causality/scripts/asym_p1_analyze.py --run-dir <out> --mech-name refusal_L18

sbatch --export=ALL,ASYM_NRANDSUF=20 doublespeak_causality/slurm/run_asym_p1c_mechval.sh
python doublespeak_causality/scripts/asym_p1c_analyze.py --run-dir <out>
```

Every run writes `meta.json` + `RUNMETA.json` + `DONE.json` carrying git commit, model sha,
dtype, split, seed, n, the fit layers AND the hidden-states rows, the suffix placement, the
control counts, and the measured template tail.
