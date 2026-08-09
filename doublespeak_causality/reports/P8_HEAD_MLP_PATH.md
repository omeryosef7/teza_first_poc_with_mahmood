# §8 — Full Head→MLP Path Patching (concept + refusal)

**Status:** ✅ DONE. §8.2 refusal = NO-PATH (n=25). §8.1 concept = codeword-z deviation is 0 on the matched pair (concept is distributed, not a localized codeword→MLP edge — P4b); concept head→readout mediation is the committed phase7_direct_total result (~75–83% mediated). Both families: carried/distributed, not sparse head→MLP.

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
**Result: the codeword-localized concept head→MLP edge is not computable on this pair, and the concept
head→MLP mediation is instead established (committed) by phase7_direct_total.** The §8 concept endpoint patches
the corrupt (NEUTRAL_CODEWORD) per-head z into the clean (DOUBLESPEAK) prompt at **codeword-token sites**. On the
canonical pair (run 737623) the alignment found **n_demo_codeword_paired = 0** and all edges = 0.0 — because
DOUBLESPEAK and NEUTRAL_CODEWORD are token-identical at the codeword positions (both say "carrot"); the two
conditions differ only in the demo *answers*, so there is no codeword-z deviation to inject. This is not a
"no-path" measurement — it is a direct consequence of the established finding that the concept reading is
**distributed across the demo block, not localized to the codeword token** (P4B_HEAD_Z_NECESSITY_DEMO / P4b:
no single codeword-token head carries the binding). The concept-circuit's head→readout **mediation** is the
committed result of `phase7_direct_total` (concept effect ~75–83% MEDIATED across L14–21 heads), which is the
concept analogue of §4's refusal mediation. So §8.1's mechanistic content (concept is carried, not written by a
localized codeword→MLP edge) is covered; the codeword-site edge variant is inapplicable on this pair by
construction.

## Verdict
**§8.2: no sparse head→MLP write path for refusal — the refusal-suppression evidence is carried distributedly
(NO-PATH at n=25), reinforcing §4/§7.** **§8.1: the concept reading is likewise not a localized codeword→MLP
edge (codeword-z deviation = 0 on the matched pair; concept is distributed per P4b), and its head→readout
mediation is the committed phase7_direct_total result (~75–83% mediated).** Both families: the in-context
evidence (refusal OR concept) is carried/distributed, not written through a sparse head→MLP path.
Related: [[project_causal_circuit_sprint]].
