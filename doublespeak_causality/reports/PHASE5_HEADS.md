# reports/PHASE5_HEADS.md — All-Head Activation Patching (per-head z necessity)

**Question (plan Q3/Q4):** which attention HEADS are necessary/sufficient for the Doublespeak reading?

## Method
`scripts/phase5_head_zpatch.py` + `scripts/phase5_analyze.py`. For every (layer, head), replace the
DS per-head attention output z[head] at the FC **answer position** (last token) with the matched BENIGN
z[head] (necessity = the head's DIRECT contribution to the final concept-vs-codeword logit; nothing
attends to the last position downstream). Readout = FC DE_context p_concept. Reuses `pc.ZHeadCapture`
(o_proj-input z) + `pc.ZHeadPatch` (replace one head's z at a position). Necessity(l,h) = C1 − patched,
paired over valid examples (DS C1 p_concept > benign). **Holm-corrected across the full 32×32 = 1024
head family, per split.** self-swap = exact no-op (dev 0.0). Model Llama-3.1-8B bf16. Layer-split jobs
704129/704130 (curated) merged; clearharm 704131/704133 pending.

## Cross-cohort robust head set (corrects an earlier curated-only over-claim)

Robustness = Holm-significant positive necessity in each of the 4 cells (curated dev/heldout,
clearharm dev/heldout), computed independently per cell:
- **Significant in ALL 4 cells:** `L21H10, L22H19, L26H13, L30H15, L31H0, L31H1` — these are **late /
  output-proximal** heads.
- **Significant in ≥3 cells:** + `L14H20, L15H8, L17H27, L18H16, L25H23, L27H7, L31H6` → a **MID band
  (L14,15,17,18)** plus a **LATE band (L21,22,25,26,27,30,31)**.
- The very large curated L14–L15 effects (L14H4 .10, L15H4 .11) are **cohort-dependent** — they do NOT hit
  Holm on clearharm (smaller, noisier cohort), though nearby heads L14H5 / L15H8 / L15H11 do. So L14–L15 is
  real and curated-strong but per-head cohort-sensitive; the **cross-cohort-robust** necessity is broader
  and includes a late output band.
- **Caveat (readout proximity):** late heads (L30–L31, and to a degree L21+) sit near the unembedding, so
  patching their answer-position z DIRECTLY perturbs the final logit — their necessity is partly proximal
  and less mechanistically informative than the mid-band (L14–18) heads, which are further from the readout.

**Phase-7 candidate heads (mid-band, cross-cohort-replicating, non-proximal):**
`L14H5, L15H8, L15H11, L17H27, L18H20, L18H16` (+ curated-strong L14H4, L15H4 as a secondary set).

## Result (curated; dev=train, heldout=test — both REPLICATE)

**Specific answer-position heads ARE necessary** (unlike the query→demo *edges*, which were null in the
Phase-4 edge-knockout). Holm-significant positive-necessity heads: **75 (dev) / 60 (heldout)**.

Top heads (heldout, necessity C1−patched [95% CI]):
- **L15H4 0.106 [.043,.178]**, **L14H4 0.104 [.055,.158]**, **L18H20 0.094 [.038,.154]**,
  L15H11 0.073, L14H5 0.071, L29H31 0.062, L21H14 0.062, L22H11 0.060, L21H10 0.054, L15H8 0.052.
- **Replicate on dev**: L14H4, L15H8, L15H11, L18H20, L21H10 significant on BOTH splits.

**Layer concentration** (Σ positive head-necessity per layer, both splits agree):
- peak **L14, L15** (heldout 0.41, 0.37), then **L13** (0.31), **L17–L18** (0.21, 0.19), **L21–L22**.

**Distributed within the band:** top-10 heads = only **20% (heldout) / 31% (dev)** of total positive
necessity → not a few dominant heads; the effect is spread across many heads, but sharply
**layer-concentrated at L13–L15 (peak L14–15)**, with secondary L17–18 and L21–22.

## Interpretation
- The answer-position carry of the concept runs through a **distributed set of heads concentrated at
  L13–L15**, DOWNSTREAM of the L8–11 demonstration-position retrieval (K/V) + L9 MLP write.
- Refines the "fully distributed" prior: no single query→demo **edge** matters (edge-KO null), and no
  single head dominates (top-10 = 20%), BUT there is clear **layer structure** — a concentrated
  L13–L15 answer-position head band is causally necessary and replicates train→test.
- Coherent circuit so far: **L8–11 demo-codeword retrieval/write (K/V + MLP@L9) → L13–L15 answer-position
  head carry (distributed) → logit.**

## Caveats / next
- Answer-position DIRECT effect only (a head that writes at an EARLIER position which the answer then
  reads is not captured here). Demo/query-position head-z = follow-up.
- Direct logit effect at L13–L15 may mix "retrieval" heads (read binding from demos) and "output" heads
  (move concept→logit). **Phase 7 path-patching** (these heads → the answer, and demo-write → these heads)
  is needed to separate carry from retrieval.
- Sufficiency (install DS head-z into benign) not yet run.
- clearharm cross-cohort replication pending (704131/704133).

Reproduce: `python scripts/phase5_analyze.py <L0-15 dir> <L16-31 dir>` (merge halves + 32×32 Holm).
