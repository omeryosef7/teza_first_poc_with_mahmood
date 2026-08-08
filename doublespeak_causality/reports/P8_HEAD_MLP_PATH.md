# §8 — Full Head→MLP Path Patching (concept + refusal)

**Status:** ◐ §8.2 refusal **DONE** (n=25, ≥20/cell); §8.1 concept RUNNING (canonical pair, job 737623).

## §8.2 REFUSAL — head→MLP write path (v3 clearharm test, **n=25 items aggregated**)
**Verdict: NO-PATH — there is NO specific sparse head→MLP write path carrying the refusal-suppression
evidence.** The candidate §7 refusal heads' edges into the L8–17 MLP band do **not** clear the specificity
controls when aggregated over 25 items. Consistent with §4 (refusal is 72–88% mediated/distributed) and §7
(head-distributed, no bottleneck).

**Run:** `phase8_hmpath_refusal_..._737616` (`scripts/phase8_head_mlp_path.py --item-idxs 0-24`). Senders = §7
top-6 heads (L13–20 band); receivers = MLP L8–17; endpoint = decision-token refusal projection (L18);
clean=DS, corrupt=neutral. 3 random-sender + 3 random-receiver + matched-head controls per item; self-donor
locality null. Edges pooled across items → verdict re-applied on pooled medians.

| quantity | value |
|---|---|
| candidate median abs edge | 0.0306 |
| control median abs edge | 0.0212 |
| ratio (needs ≥2×) | **1.44× → fails** |
| self-donor null max | 0.000 (locality ✓) |
| specific / sparse | **False / False** |
| strongest pooled edge | L15h7→MLP16 = 0.070 (sign-consistency only **0.64**) |

**Per-item verdicts: 17/25 NO-PATH, 6 SPARSE-GRAPH, 2 DISTRIBUTED** — i.e. the sparse-path picture appears on
a minority of items and does not survive pooling.

### ⚠️ Why ≥20/cell mattered here (single-item false positive)
The first "full" run used **item 0 only** and reported **SPARSE-GRAPH (specific=True, L13h11→MLP-L14=0.090)**.
Item 0 is one of the 6 SPARSE-GRAPH items; the 25-item aggregate corrects this to **NO-PATH**. A single-item
path-patching result is not trustworthy for this endpoint — the ≥20/cell rule caught a genuine false positive.

### Mediation recap (pooled TOTAL vs DIRECT per sender — mirrors §4)
The pooled per-sender TOTAL (head→readout) is large while DIRECT (skip-path) is ~0 for the L13 heads
(L13h9 TOTAL 0.199 / DIRECT 0.013; L13h18 0.258 / 0.020), rising to L16h10 (0.067 / 0.059) — the same
carry→readout depth gradient §4 found. The heads matter for refusal, but **not via a localized head→MLP edge**.

## §8.1 CONCEPT — retrieval heads → L8–13 MLP write (canonical CARROT/BOMB pair)
RUNNING (job 737623): family=concept, senders=retrieval heads (L7–14 from the 49_head_attribution ranking),
receivers=MLP L8–13, endpoint=p_concept. Uses the canonical fixed pair (the established concept-circuit design;
the p_concept endpoint is deterministic per pair, not a behavioral sample). Result to be appended on completion.

## Verdict (interim)
**§8.2: no sparse head→MLP write path for refusal — the refusal-suppression evidence is carried distributedly
(NO-PATH at n=25), reinforcing §4/§7.** §8.1 concept pending. Related: [[project_causal_circuit_sprint]].
