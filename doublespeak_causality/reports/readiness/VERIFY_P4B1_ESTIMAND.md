# VERIFY P4B-1 — Does the computed estimand match P4B_PREREGISTRATION.md §2?

**Verdict: NO. The pre-registered specificity-controlled estimand is neither computed nor
computable from the emitted raw.** This is a measurement gap in the exact code the full P4b-1
jobs are running on (`scripts/phase5_head_zpatch.py`), not a smoke-only reduction.

Ground truth used: `outputs/phase5_headz_clearharm_demo_20260806_181558_728619/{raw.jsonl,summary.json}`
(520 rows: 512 `benign` = 2 splits x 2 items x 4 layers x 32 heads; 4 `selfswap`; 4 `normrand`).
All numbers below recomputed directly from `raw.jsonl`, independent of `phase5_analyze.py`.

---

## The pre-registered estimand (§2, and §6.2 "fixed and cannot change after seeing results")

```
necessity_specific(l,h,P) = mean_i[ p_concept(DS) − p_concept(DS, head (l,h) z at P ← BENIGN) ]   # arm A, per (l,h)
                           − mean_i[ p_concept(DS) − p_concept(DS, head (l,h) z at P ← RANDOM) ]   # arm B, per (l,h)
```

Two arms, **both indexed by (l,h)**. A positive value = benign donor reduces the readout *more
than a count-matched random perturbation does* at this specific head → head is necessary.

---

## FINDING 1 — CRITICAL (the real defect): the random arm B does not exist per (l,h); the §2 estimand is not computable

**Where:** `scripts/phase5_head_zpatch.py:200-221` (emission), `:252-263` (aggregation);
`scripts/phase5_analyze.py:5,80-97` (analyzer); docstring `phase5_head_zpatch.py:14-16`.

**What.** The `normrand` (random-donor) cell is emitted at **one probe head only** —
`lp = layers[len(layers)//2]`, `head = 0` (`phase5_head_zpatch.py:202,221`) — once per item, not
per (l,h). The smoke confirms it: `normrand` appears at exactly `(layer=10, head=0)` for all 4
rows (= 2 items x 2 splits); `benign` spans all 4 layers x 32 heads. So for 127 of the 128
(l,h) cells per split there is **no random arm to subtract**, and even at the single probe cell
the random value is a lone scalar per item at head 0.

Neither consumer subtracts it. Both the in-script summary (`:260` `diffs = [r["C1"] - r["p_concept"] ... cell=="benign"]`)
and the analyzer (`phase5_analyze.py:88` `diffs = [c1_of[s] - d[s] ...]`) compute **arm A only**:

```
reported "necessity"(l,h) = mean_i[ C1 − p_benign_patched ]        # arm A only — NOT necessity_specific
```

The `normrand` rows are read **nowhere** in either the summary loop or the analyzer — only
`selfswap` is read, and only for the locality control (`:256-257`, `phase5_analyze.py:78`). The
run script's own docstring (`:14-16`) reframes the random donor as a single-probe *"norm-matched
random vector (must be ~0)"* sanity check and defines *"Necessity(L,h) = C1 − patched_benign"* —
i.e. the code author reinterpreted §2's per-cell subtracted arm as a one-probe pass/fail check.
This directly contradicts §2 and the §6.2 lock ("Estimand = specificity-controlled necessity").

**Failure scenario (the garbage the run will produce).** The full job finishes, `summary.json`
lists `top10_by_mean` / `holm_sig_heads`, and those get read as the pre-registered
*specificity-controlled* necessary heads. They are not — they are un-subtracted arm A. The
missing subtraction is **material, not a rounding detail**: at the one heldout item where both
arms exist (`clearharm_0000`), arm A (benign) = **+5.0e-09** ≈ 0, but arm B (random) = **−1.28e-02**.
The specificity-controlled value there would be A−B = **+0.0128**, six orders of magnitude larger
than the reported arm-A "necessity" of ~0. Conversely, generic random-perturbation damage of
order 0.013 at the probe is the *same magnitude* as the reported headline cells (heldout
L8H11 = 0.0114, L8H29/L9H23/L10H1/L9H19 = 0.0086). So the reported per-head "necessity" numbers
sit entirely inside the band of generic perturbation noise that §2's random arm was designed to
subtract off — and that subtraction cannot be performed at those cells because arm B was never
measured there. The random arm is also empirically **not ~0** (−0.0128), violating even the
code's own docstring assumption.

**Post-hoc recoverable? No.** The raw contains no per-(l,h) random readout; it cannot be
reconstructed from what is emitted. This is an unrecoverable measurement gap, exactly as the task
anticipated.

**Fix.** Emit `normrand` per (l,h) — run the random-donor readout inside the same
`for l: for h:` benign loop (`phase5_head_zpatch.py:~189-198`), writing a `normrand` row per cell —
then subtract it in `:260-263` and `phase5_analyze.py:87-91`
(`necessity_specific = mean(A) − mean(B)` per cell, sign per §2). This roughly doubles readout
cost (a second full sweep). Until then, the run cannot produce the §2 estimand and its output must
not be labelled `necessity_specific`. The already-computed `benign` arm-A readouts are valid and
reusable, so the gap is in the specificity control, not the benign sweep itself.

---

## FINDING 2 — arm-A recomputation matches the analyzer/summary exactly (NOT-A-BUG; confirms what IS computed)

Recomputed `mean_i[C1 − p_benign]` per (l,h) from `raw.jsonl` with the analyzer's own valid
filter (`benign_p_concept` not None and `C1 > benign_p_concept`), top 5 cells:

| split | cell | recomputed | summary.json `top10_by_mean` |
|---|---|---|---|
| heldout | L8H11 | 0.0114 | 0.0114 ✓ |
| heldout | L8H29 | 0.0086 | 0.0086 ✓ |
| heldout | L9H23 | 0.0086 | 0.0086 ✓ |
| heldout | L10H1 | 0.0086 | 0.0086 ✓ |
| heldout | L9H19 | 0.0086 | 0.0086 ✓ |
| dev | L10H2 | 0.0 (2.0e-05) | 0.0 ✓ |
| dev | L10H24 | 0.0 (1.0e-05) | 0.0 ✓ |

The analyzer and in-script summary faithfully compute **arm A**. The defect is not an arithmetic
error in arm A — it is that arm A alone is not the pre-registered estimand (Finding 1).

---

## FINDING 3 — sign convention is correct (NOT-A-BUG)

Estimand orientation is `C1 − p_patched` (`phase5_head_zpatch.py:260`, `phase5_analyze.py:88`),
so a benign donor that **reduces** the concept readout below the intact value C1 yields a
**positive** number = "necessary". This matches §2 ("positive = benign donor reduces the concept
readout"). Confirmed on heldout L8H11 (= +0.0114 > 0, benign patch lowers readout). The absent
arm-B subtraction (Finding 1) would preserve this sign convention once added.

---

## FINDING 4 — C1 semantics correct (NOT-A-BUG)

`C1` is stored per row and is **exactly constant across all (l,h) within an item** (1 distinct
value per sid across all 128 benign cells; verified for all 4 items). It does **not** depend on
which head is patched, as required for an intact-DS reference. It also **equals the intact DS
readout**: the `selfswap` cells (DS's own z patched back in) have `p_concept == C1` to full
precision, and all four `selfswap` cells give `|C1 − p_concept| = 0.0` exactly — so the §5
self-swap locality control (must be exactly 0.0) holds in this smoke.

---

## Bottom line

- §5 controls (self-swap = 0.0 exactly) hold; arm A is computed correctly and reproducibly.
- **But the §2 / §6.2 estimand — specificity-controlled necessity with a per-(l,h) random arm
  subtracted — is not what the running code computes, and cannot be reconstructed from the
  emitted raw** (random arm sampled at one probe head only). The reported per-head "necessity"
  is un-subtracted arm A, and the smoke shows the omitted random term is orders of magnitude
  larger than arm A at the one cell where it is measured and comparable in size to the headline
  cells. Interpreting the full-run `summary.json` as pre-registered necessary heads would be a
  preregistration violation. The run should be stopped and reconfigured to emit `normrand` per
  (l,h) before its numbers are read as the §2 estimand; the benign readouts already produced are
  salvageable.
