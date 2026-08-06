# P5 readiness — Head→MLP path matrix (B3)

Scope: plan section `reports/CAUSAL_CONTINUATION_MASTER_PLAN.md:593-610`.
Model: `meta-llama/Llama-3.1-8B-Instruct` — 32 layers × 32 heads (`pair_common.py:501` `_attn_head_dims`).
This is a **code/infrastructure inventory only**. No job launched, no script modified.

Verdict in one line: **the freeze machinery is real, verified-exact on-model, and reusable, but P5 as
literally specified is a ~34–77 GPU-hour exact-patching job per metric and must be decomposed into
AtP-ranking (not a claim) + exact-patch top-k (the claim). Three hard blockers below.**

---

## 1. The freeze primitives in `50_path_patching.py` and how `phase7_direct_total.py` calls them

`50_path_patching.py` starts with a digit, so it cannot be `import`ed by name. Both consumers load it
with `importlib`:

* `scripts/phase7_direct_total.py:33-35` —
  `_spec = importlib.util.spec_from_file_location("pp50", os.path.join(DC, "50_path_patching.py"))`
  → module object `pp50`. (`50_path_patching.py:38-41` does the same trick for `atp48`/`ha49`.)
  **The new P5 script must use this exact pattern.**

### 1a. `FreezeAllHeadsExcept` — `50_path_patching.py:44-83`

```
FreezeAllHeadsExcept(model, z_clean, sender=None, receiver_capture=None)      # :50
  z_clean          : {layer_idx: Tensor[seq, n_heads, head_dim]} on device
  sender           : (L_S, h_S, positions, corrupt_vecs)   corrupt_vecs = list of [head_dim], one per position
  receiver_capture : (L_R, h_R, positions, out_dict)       out_dict["z"] <- [P, head_dim]
```

Mechanism (`_pre`, `:58-72`): a `forward_pre_hook` on **every** `layer.self_attn.o_proj` (`:75-76`).
The o_proj input is the per-head concat `z`; it is reshaped to `[b, seq, n_heads, head_dim]` (`:62`),
then

* `:63-65` — if this is the receiver layer, **capture** `zr[0, pos, h_R, :]` *before* the overwrite
  (ordering is the whole trick; guarded by `tests/test_path_patching.py:154-158`),
* `:66` — `zr[0, :, :, :] = self.z_clean[li]` — freeze **all heads at all positions** to clean,
* `:67-70` — at the sender layer only, write the corrupt vector into head `h_S` at each position.

Because `o_proj(z) = z @ W_o` is linear, this injects exactly the sender's isolated delta with zero
leakage (module docstring `:8-11`).

### 1b. `FreezeMLP` — `50_path_patching.py:86-111`

```
FreezeMLP(model, mlp_clean)                                                    # :89
  mlp_clean : {layer_idx: Tensor[seq, hidden]} on device
```
`forward_hook` on every `layer.mlp` (`:103-104`) replacing the output with the cached clean rows
(`:96-99`). Tuple-output safe. **It has no `receiver_capture` argument — this is the single missing
primitive for P5** (see §5).

### 1c. `ZHeadPatchMulti` — `50_path_patching.py:114-137`
Per-position variant of `pc.ZHeadPatch` (`pair_common.py:509`): patch head `h` with `vecs[i]` at
`positions[i]`. Used to re-inject a captured receiver value (`:224`).

### 1d. `capture_clean_all(lm, text, metric, n_layers)` — `50_path_patching.py:139-164`
One clean forward that returns `(z_clean, mlp_clean, m_clean)` — everything the two freezers need,
plus the baseline metric. Hooks `o_proj` pre (`:145-149`) and `mlp` post (`:150-155`).

### 1e. The three composed effects — `50_path_patching.py:201-225`
* `total_effect(L,h)` `:201-205` — `ZHeadPatchMulti` only, nothing frozen (1 forward).
* `direct_effect(L,h)` `:207-212` — `ExitStack` of `FreezeAllHeadsExcept(sender=…)` + `FreezeMLP`
  (1 forward). This is the skip-path contribution.
* `edge_effect(L_S,h_S,L_R,h_R)` `:214-225` — **2 forwards**: run 3a with both freezers +
  `receiver_capture` fills `out["z"]`; run 3b re-injects that `z` with `ZHeadPatchMulti` and lets
  everything downstream recompute.
* Reconstruction gate `:238-254` (`TOTAL ≈ DIRECT + Σ_R EDGE`, `--recon-tol` default 0.15, `:282`).
* Edge loop `:231-235` — **hard-coded `if L_R > L_S`**, so the non-downstream case is *excluded*,
  never *measured* (see §3).

### 1f. Exactly how `phase7_direct_total.py` calls them (the concrete reuse path)

`scripts/phase7_direct_total.py`, inner loop `:125-148`:

```
z_clean, mlp_clean, m_clean = pp50.capture_clean_all(lm, <templated FC prompt>, metric, L)   # :125-126
donor  = benign_z[ls][hs]                 # [head_dim] benign z at the benign answer pos      # :129
self_v = z_clean[ls][ds_last, hs]         # DS's own z at the answer pos (self-swap control)   # :130

m_tot  = run_metric(ds_t, cid, kid, [pc.ZHeadPatch(model, ls, hs, [ds_last], donor)])          # :132
m_dir  = run_metric(ds_t, cid, kid,
           [pp50.FreezeAllHeadsExcept(model, z_clean, sender=(ls, hs, [ds_last], [donor])),
            pp50.FreezeMLP(model, mlp_clean)])                                                 # :134-137
m_tot_self = … ZHeadPatch(…, self_v)                                                           # :139
m_dir_self = … FreezeAllHeadsExcept(sender=(ls,hs,[ds_last],[self_v])) + FreezeMLP(…)          # :140-143
```

Note the differences from `50_path_patching.py` that P5 inherits:
* **positions**: `phase7` patches the *answer position only* (`ds_last`), `50` patches the full
  token-aligned position set from `atp48.build_alignment` (`50:174`, 44 positions in the one on-model
  run). Position count costs nothing extra in forward passes — it lives inside the hook.
* **corpus**: `phase7` runs over a whole bench with per-item CIs (51 items curated, 86 items
  `bench_clearharm.json`); `50` runs a single fixed clean/corrupt pair.
* **contrast**: `phase7` clean = DOUBLESPEAK, donor = matched `BENIGN_REMAP`; `50` clean =
  DOUBLESPEAK, corrupt = matched `NEUTRAL_CODEWORD` (`48_attribution_patching.py:235-253`).

For P5 the `phase7` shape is the right one (multi-item ⇒ CIs ⇒ Holm), with `50`'s multi-position
sender injection folded in.

---

## 2. Which of the plan's SIX path tests already have an implementation

| # | plan test | status | where |
|---|---|---|---|
| 1 | sender patched, **downstream frozen** | ✅ **exists, head sender** | `50_path_patching.py:207-212` `direct_effect`; `scripts/phase7_direct_total.py:134-137` |
| 2 | sender ablated, **receiver restored** | ⚠️ **exists only for MLP-sender → head-receiver** (the reverse of P5) | `scripts/phase7b_mediation.py:13-16` arms `A_neutralizeL9` / `B_L9_freezeCarry`, emitted `:139-140`, `mediation_frac` `:146-149` |
| 3 | receiver patched, **sender clean** | ⚠️ **head-receiver only** (`edge_effect` run 3b) | `50_path_patching.py:222-225` |
| 4 | **direct vs total** | ✅ **exists, complete, with CI-grade n** | `scripts/phase7_direct_total.py` whole file; `50_path_patching.py:238-254` |
| 5 | **edge necessity** | ❌ **not implemented for component edges** | the only "edge necessity" in the repo is *attention* query→key edge knockout: `scripts/phase4c_carryedge.py:106-116`, `scripts/phase4_edge_knockout.py` — a different object |
| 6 | **edge sufficiency** | ⚠️ closest analogue is head-receiver `edge_effect` (`50:214-225`) and *component* (not path) sufficiency `scripts/phase7c_sufficiency.py:7-11,100-110` | |

**Bottom line: 1 of 6 is done as specified (direct-vs-total); 3 more exist with a HEAD receiver and
must be re-pointed at an MLP receiver; 2 (edge necessity, true edge sufficiency for head→MLP) do not
exist.** No sender × receiver sweep exists anywhere — the plan's gap statement (`:595-596`) is
accurate.

Receiver-side primitives that already exist and remove most of the work:
* `pc.ComponentOutSwap` (`pair_common.py:374-433`) — per-position overwrite of `layer.mlp` output with
  distinct rows. This **is** the MLP analogue of `ZHeadPatchMulti`; no new patch class is needed.
  Self-swap exactness is unit-tested (`tests/test_componentoutswap_synthetic.py`).
* `pc.SubmodulePatch(..., "mlp_out", ...)` (`pair_common.py:286-370`) — single-vector variant, used by
  `51_mlp_attribution.py:116`.
* `51_mlp_attribution.py:31-58` `_MLPActGradCapture` / `capture_mlp_outputs` — per-layer MLP-output
  activations **and grads**, i.e. the whole receiver-side AtP stack.
* `51_mlp_attribution.py:76-77` records that the **L31 MLP is a legitimate receiver** (upstream of the
  final norm), so `receivers = MLP[L_S+1 … 31]` as the plan writes it is well-defined.

---

## 3. Controls — what exists, what does not

| plan control | exists? | evidence |
|---|---|---|
| **self-freeze must be exactly 0** | ✅ **implemented and passing on-model** — but in `phase7_direct_total.py`, **not** in `50_path_patching.py` | see below |
| random **receiver** | ❌ for MLP receivers. Nearest: `phase7b_mediation.py:15` `ctrl_freezeRand` freezes count-matched random **heads** | |
| random **sender** | ❌ for path tests. Nearest: `phase5_head_zpatch.py:146-154` norm-matched random vector at one probe head; `phase6_mlp_causal.py:222,235` random **positions** | |
| **non-downstream impossible control** | ❌ **not merely missing — structurally excluded**: `50_path_patching.py:233` only forms edges with `L_R > L_S`. Nothing ever measures an upstream receiver and asserts 0 | |
| **norm-matched path** | ⚠️ helper exists, never used in a path test: `pc.norm_matched_random` `pair_common.py:958-964` (and `orthogonal_random:966`); hand-rolled equivalent at `phase5_head_zpatch.py:150-152` | |

### Does anything check that self-freeze is exactly 0? **Yes — and it passes.**

`scripts/phase7_direct_total.py` writes two self-consistency scalars per item×head (`:144-148`):
* `m_frozen_clean` = metric under *freeze-all-clean + clean sender* → must equal `m_clean`,
* `TOTAL_self` = metric under a self-swap patch → must be 0.

and gates on them at `:162-177`:
```
TOL = 0.05
trustworthy = (freeze_consistency_dev <= TOL) and (selfswap_max_dev <= TOL)
... "median_direct_frac": … if fracs.size and trustworthy else None      # :173
```
i.e. a failing freeze **nulls out** `direct_frac` rather than silently reporting it (the fix logged as
audit findings 14/15, `:163-165`).

**Measured values (both cohorts, all 10 heads, both splits):
`selfswap_max_dev = 0.0` and `freeze_consistency_dev = 0.0`** —
`outputs/phase7_directtotal_curated_20260803_160846_704725/summary.json` (510 rows, n=30 dev / 21
heldout) and `outputs/phase7_directtotal_clearharm_20260803_160846_704726/summary.json` (860 rows,
n=44 / 42). So the freeze machinery is exact on-model at the answer position on Llama-3.1-8B.

Two caveats to carry into P5:
1. The gate is `<= 0.05`, not `== 0`. The plan says **exactly 0**. Since the observed value *is* 0.0 at
   the reported precision (rounding to 4–5 dp, `:174-176`), P5 should tighten the assertion to
   `|dev| <= 1e-6` and record the raw unrounded value, so a future regression cannot hide under 0.05.
2. `50_path_patching.py` itself has **no self-freeze cell at all** — only the reconstruction tolerance
   (`:253`). Any P5 code path derived from `50` (multi-position sender injection) must carry the
   `phase7` self-freeze cell across, per position set.

### Synthetic coverage gap
`tests/test_path_patching.py` verifies completeness to 1e-4 (`:145-151`), capture-before-overwrite
ordering (`:154-158`), and the head freeze (`:161-172`) — **but its toy MLP returns zeros**
(`tests/test_path_patching.py:38`, "MLP == 0 -> no MLP-mediated path"). **The head→MLP path — exactly
what P5 measures — has zero synthetic coverage.** This is the cheapest, highest-value pre-GPU task
(§5, Stage 0).

---

## 4. Combinatorial size, cost, and the required decomposition

### 4a. Sender / receiver counts (exact)

Receivers for a sender at layer ℓ: `R(ℓ) = 31 − ℓ` (MLPs at ℓ+1 … 31).

| sender family | # senders | Σ receivers | pairs |
|---|---|---|---|
| all L8–11 heads | 4×32 = **128** | 23+22+21+20 = 86 per head-column | 32×86 = **2 752** |
| all L14–21 heads | 8×32 = **256** | 17+16+…+10 = 108 | 32×108 = **3 456** |
| train-selected **induction** heads | **0 available** (blocker B1) — expected ~8–10, expected ⊂ L8–11 ⇒ subset, no new pairs | — | 0 |
| train-selected **carry** heads | 8 of the canonical set are ⊂ L14–21; `L30H15`, `L31H0` are **+2** new senders | 1 + 0 | **1** |
| random count-matched senders (≈20, drawn outside the bands) | **20** | mean R ≈ 16.7 | ≈ **334** |
| **total** | **≈ 406 distinct senders** | | **≈ 6 543 ordered pairs** |

### 4b. Forward passes (per prompt, per metric)

Measured throughput, derived from the two completed `phase7_direct_total` jobs (out-dir creation → last
mtime; model load excluded):
* job 704725: 51 prompts × 10 heads → `51×2 + 510×4 = 2 142` forwards in **189 s** ⇒ **0.088 s/fwd**
* job 704726: 86 prompts × 10 heads → `86×2 + 860×4 = 3 612` forwards in **240 s** ⇒ **0.066 s/fwd**

Planning constant: **0.08 s per forward on one L40S** (freeze forwards are the expensive half; prompts
are ~120–250 tokens).

Critical accounting insight: the capture forward can be shared. One frozen forward with
`sender = corrupt` can capture the recomputed output of **every** MLP simultaneously (the receiver
loop in `50:231-235` re-runs it per receiver only because `FreezeAllHeadsExcept` captures a single
head). So:

| item | forwards/prompt |
|---|---|
| sender-level: TOTAL, DIRECT, self-freeze, self-swap → 4 × 406 | 1 624 |
| sender-level all-MLP receiver capture (1 per sender) | 406 |
| pair-level tests 2, 3, 5, 6 → 4 patched forwards × 6 543 | 26 172 |
| non-downstream impossible control (1 upstream receiver per sender × 4) | 1 624 |
| **subtotal** | **≈ 29 800** |
| + norm-matched-path control on every injecting test (2 × 6 543) | +13 086 → **≈ 42 900** |

Random-receiver and random-sender controls are **free**: a full matrix already contains them; they are
a selection over the computed cells, not extra forwards.

### 4c. Wall clock

| configuration | fwd/prompt | per prompt | n = 20 | n = 51 (curated dev+heldout) | n = 116 (`bench_clearharm_v2`) |
|---|---|---|---|---|---|
| full matrix, concept metric | 29 800 | 40 min | **13.3 h** | **33.8 h** | **76.9 h** |
| + norm-matched everywhere | 42 900 | 57 min | 19.1 h | 48.6 h | 110.6 h |
| **× 2 for the refusal graph** (separate prompt condition ⇒ separate forwards) | | | 27 h | **68 h** | 154 h |

`slurm/run_phase7_dt.sh` defaults to `--time=04:00:00` on `killable`. **The full matrix is 9–20 shards
of 4 h per metric. It is infeasible as one job and should not be attempted as one.**

### 4d. Principled decomposition (recommended)

**Stage 0 — GPU-free (do first).** Extend the toy in `tests/test_path_patching.py` with a *non-zero
linear* MLP and assert (a) `TOTAL == DIRECT + Σ_R EDGE_head + Σ_R EDGE_mlp` to 1e-5, (b) self-freeze
and self-swap are **exactly** 0, (c) an upstream (non-downstream) receiver edge is **exactly** 0.
Cost: 0 GPU. Without this, the head→MLP edge path is untested code.

**Stage A — AtP edge ranking. THIS IS A RANKING, NOT A CLAIM.**
Per prompt: for each sender, one frozen forward (`FreezeAllHeadsExcept(sender=corrupt)` + capture-variant
`FreezeMLP`) yields `Δmlp_R(S)` for **all** receivers at once; one backward
(`51_mlp_attribution.py:94-99`) yields `g_mlp[R]` for all R. Then
`AtP_edge[S→R] = g_mlp[R] · Δmlp_R(S)` for all 6 543 edges.
Cost: **406 forwards + 1 backward per prompt ≈ 33 s** ⇒ n=51 in ~28 min, n=116 in ~64 min, per metric.
**One job covers the entire matrix.** Nothing from Stage A may appear in the paper as a causal edge —
per the plan (`:604-606`) AtP is ranking only. In the write-up these numbers get a column labelled
"AtP rank (not a causal estimate)".

**Stage B — exact patching = THE CLAIM.** Take the top-k edges by |AtP| (k ≈ 100 per metric) **plus a
stratified random sample of ≈50 non-top edges** (calibrates the null and bounds the miss rate), and run
all six tests plus all five controls with per-item bootstrap CIs and Holm across the k+50 family, dev to
select / heldout to confirm (same protocol as `scripts/phase5_analyze.py`).
Cost: ≈ 80 senders × 5 + 150 pairs × 4 + 80 non-downstream + 300 norm-matched ≈ **1 380 forwards/prompt
≈ 110 s** ⇒ **1.6 GPU-h at n=51**, **3.6 GPU-h at n=116**, per metric. Two jobs (concept, refusal).

**The mandatory AtP trust gate comes free**: Stage B produces exact deltas for the same cells Stage A
ranked, so report Pearson **and** Spearman of AtP vs exact and require `min ≥ 0.7` exactly as
`48_attribution_patching.py:409-412` and `51_mlp_attribution.py:123-126`. If the gate fails, the ranking
is discarded and only the exactly-patched edges are reported (they remain valid — they are exact).

**Claim boundary, to be stated verbatim in `PHASE5_HEAD_TO_MLP_PATH_MATRIX.md`:** every edge drawn in
the causal graph carries an exact-patch effect with a CI; edges outside the top-k are reported as
"ranked, not exactly tested", with the random-stratum false-negative rate quoted.

---

## 5. Minimal change to unblock (no existing script modified)

One new file, `scripts/phase_p5_head_mlp_paths.py`, ~150 lines, structured exactly like
`scripts/phase7_direct_total.py`:

1. `importlib`-load `pp50` (`phase7_direct_total.py:33-35` pattern) and `atp48`/`mlp51`.
2. **Subclass, do not edit**:
   ```python
   class FreezeMLPCapture(pp50.FreezeMLP):
       """FreezeMLP + capture every layer's recomputed mlp output BEFORE the overwrite."""
   ```
   overriding only `_hook` to stash `h[0, positions, :]` into an out-dict before returning `hc`.
   This is the *only* missing primitive; `50_path_patching.py` stays untouched.
3. Receiver patching: reuse `pc.ComponentOutSwap(model, positions, {L_R: rows}, "mlp_out")` —
   already exists, already self-swap-tested.
4. `--stage {atp,exact}`, `--edges-from <atp json>`, `--topk`, `--random-stratum`, `--metric
   {logit_diff,refusal}`, `--positions {answer,aligned}`, and a `--controls` list including
   `self_freeze,non_downstream,rand_sender,rand_receiver,norm_matched`.
5. Carry `phase7`'s trust gate across verbatim (`phase7_direct_total.py:162-177`) with `TOL` tightened
   to 1e-6 for the self-freeze cell.

Plus one SLURM wrapper `slurm/run_p5_paths.sh` cloned from `slurm/run_phase7_dt.sh` (which already
documents the 4 cpu / 48 G fast-allocation footprint and the comma-in-`--export` guard).

---

## 6. Blockers

1. **Induction heads do not exist.** `grep -rl induction scripts reports outputs` returns only prose
   (`reports/CAUSAL_PATCHING_AUDIT.md`, `reports/FINAL_CAUSAL_CIRCUIT_REPORT.md`, …) and
   `scripts/phase4_edge_knockout.py`'s docstring. There is **no train-selected induction-head set on
   disk**. Plan row B2 (`:413`) says the same. P5's induction-sender family is **gated on P4**. The
   L8–11/L14–21 full-band families are unaffected and can proceed.
2. **The only on-model run of `50_path_patching.py` FAILED its own reconstruction gate.**
   `outputs/path_patch_Llama-3.1-8B-Instruct_20260731_181722_697419/path_patching.json`:
   `median_rel_err = 1.0059`, `recon_ok = false`, `parallel_score_median_direct_frac = 0.0`,
   `verdict = "UNTRUSTWORTHY (recon gate failed; report TOTAL/DIRECT only)"` (8 senders L9–L13, 24
   head→head edges). The likely cause is precisely P5's premise: with **MLPs frozen**, head→head edges
   cannot span the effect, because the mediation runs through the MLPs. P5 adding MLP receivers is the
   test of that hypothesis — but P5 must **pre-register** the completeness criterion
   (`TOTAL ≈ DIRECT + Σ_R^{heads} EDGE + Σ_R^{MLPs} EDGE`, `recon_tol` fixed in advance) and report it
   whether or not it passes. Do not inherit the 0.15 default silently.
3. **The refusal-suppression graph is gated on P7 §0.10.** A refusal-metric graph needs per-layer
   refusal directions; 66 files exist in `outputs/refusal_alllayers/` but the plan states they have
   **zero validation metadata** and only 5 layers were generation-validated (L12 failed),
   `CAUSAL_CONTINUATION_MASTER_PLAN.md:648-651`. Building the second graph before that rebuild would
   make the "genuinely novel object" (`:608-609`) rest on unvalidated directions. Recommended order:
   concept graph now, refusal graph after P7's rebuild.

Secondary risks (not blockers): (a) no synthetic coverage of the MLP path (§3); (b) `phase7`-style
answer-position-only patching will miss demo-codeword-site edges — use `atp48.build_alignment`
positions (`48_attribution_patching.py:256-301`) for the L8–11 sender band, which costs no extra
forwards; (c) `bench_clearharm_v2.json` has 59 dev / 57 heldout DOUBLESPEAK items — plenty for CIs, and
n is the main cost multiplier, so pick n deliberately (n=20 for Stage B pilot, n=51–116 for the final).
