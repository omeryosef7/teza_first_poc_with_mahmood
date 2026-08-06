# P4a — Induction-head identification on ClearHarm

**Status: ✅ COMPLETE** (jobs `728475` dev, `728476` heldout; **zero new analysis code** —
`next7_attention_retrieval.py` already computed this and had only never been pointed at a ClearHarm bench).

**Verdict: the query codeword attends to the demonstration-codeword positions at ≈2× the rate of
count-matched random positions, replicated on both splits. The token-identity retrieval signal is real on
ClearHarm — and about half the magnitude the single carrot/bomb pair suggested.**

---

## 1. Why this run existed

The project's only induction-head evidence was a **band-mean 3.508× attention ratio on n = 12 of the old
carrot/bomb pair** (`logs`, N7-L). Everything downstream — the "induction candidates" P4b freezes, the
retrieval-pathway story — rested on that single-pair number. P4a replaces it with a ClearHarm-native
measurement on **44 dev + 42 heldout** distinct concepts.

## 2. Method (reused verbatim)

Eager forward with `output_attentions` on DOUBLESPEAK prompts. For the **query-codeword position**, average
attention mass to each source set over the mid-band heads (L7–L14), count-normalised per key:

| source set | positions |
|---|---|
| `prev_codewords` | earlier occurrences of the **same codeword** (the demonstrations) |
| `demos_all` | all demonstration tokens |
| `random_matched` | count-matched random earlier **non-codeword** tokens |

The reported statistic is `demo_codeword_over_random` = mean attn per demo-codeword key ÷ mean attn per
random-matched key.

## 3. Result

| split | n | `prev_codewords` | `demos_all` | `random_matched` | **ratio** |
|---|---|---|---|---|---|
| dev | 44 | 0.007379 | 0.003717 | 0.003502 | **2.107×** |
| heldout | 42 | 0.007036 | 0.003646 | 0.003451 | **2.039×** |

**The signal is specific to the codeword, not to demonstrations in general.** Attention to the demo
*codeword* positions (0.0074) is roughly double attention to *all* demo tokens (0.0037) and to random
matched positions (0.0035) — the latter two are nearly equal, so a generic "attend back to the
demonstrations" effect is not what is driving it. It is token-identity retrieval: the query codeword
preferentially attends to earlier occurrences of *that same codeword*.

**It replicates across the split** (2.107 vs 2.039), so it is not a dev artifact.

## 4. Reading, with the honest downward revision

The retrieval signal the circuit story depends on **is present on ClearHarm** — but at **≈2.0–2.1×**, not
the **3.508×** the carrot/bomb pair showed. The single-pair number **overstated the effect by ~1.7×**.
That is the expected direction: a single hand-built pair is chosen partly because it works cleanly, whereas
44 varied ClearHarm concepts include harder cases. The *conclusion* (token-identity retrieval exists) is
unchanged and now rests on a real sample; the *magnitude* used anywhere downstream should be the ClearHarm
one.

## 5. Honest limitations

- **Head-averaged over the L7–L14 band.** This is the identification statistic, not a per-head map. The
  per-head resolution — which heads carry it, and whether they are the same heads P4b patches — is the
  remaining part of P4a and needs the per-head breakdown, not just the band mean.
- **Attention mass is correlational.** A high query→demo-codeword attention weight is consistent with
  retrieval but does not by itself establish that the information *read* through that edge is causal. That
  is exactly what P4b's z-patch at those positions tests; P4a only says *where to look*.
- **Two splits, one cohort.** No curated replication yet.
- The `random_matched` pool excludes codeword tokens but is drawn from the in-demo span, so it is a
  conservative control (it cannot accidentally include the very positions being tested).

## 6. Provenance note — a bug fixed after these numbers were produced

Both jobs **crashed with `KeyError: 'codeword'`** on a log line (`next7_attention_retrieval.py:92`) that
assumed a single carrot/bomb pair bench (`pair['codeword']`); the multi-concept ClearHarm `pair` block has
no such key. **The crash is cosmetic** — it fires *after* `json.dump` wrote `attn_retrieval.json`, so the
numbers above are complete and were re-read directly from those committed files. The log line now uses
`.get()` and the result JSON now records `split` / `readout` / `n_used` / `bench`, so future runs exit 0
and are self-describing. `split`/`n` for these two dirs were backfilled from the launch parameters.

## 7. Reproduce

```
sbatch --time=01:00:00 --nodelist=n-801,n-802,n-803,n-804,n-805,t-806 \
  doublespeak_causality/slurm/run_p4a_identify.sh                              # dev
sbatch --time=01:00:00 --nodelist=n-801,n-802,n-803,n-804,n-805,t-806 \
  --export=ALL,DSSPLIT=heldout,DSNITEMS=42 doublespeak_causality/slurm/run_p4a_identify.sh
```
Run dirs: `outputs/attn_retrieval_Llama-3.1-8B-Instruct_20260806_172234_728475` (dev),
`…_728476` (heldout).
