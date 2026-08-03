# reports/PHASE5_HEADS.md — All-Head Activation Patching (per-head z necessity)

**Question (plan Q3/Q4):** which attention HEADS are necessary/sufficient for the Doublespeak reading?

> **Statistics corrected 2026-08-03 (audit).** Significance now uses a **Wilcoxon signed-rank** test
> (deterministic, robust to the strong right-skew of the necessity diffs, and able to resolve below the
> Holm threshold). The earlier "60–75 Holm-significant heads" figure came from a sign-flip **permutation
> p that could return exactly 0** — an artifact, because at nperm=2e4 the resolution floor (5e-5) is coarser
> than the 1024-cell Holm threshold α/m=4.9e-5. The corrected result and its conclusion (specific heads,
> mid + late bands, distributed) are below and are robust; only the significance counts changed.

## Method
`scripts/phase5_head_zpatch.py` + `scripts/phase5_analyze.py`. For every (layer, head), replace the
DS per-head attention output z[head] at the FC **answer position** (last token) with the matched BENIGN
z[head]. Necessity(l,h) = C1 − patched, paired over valid examples (DS C1 p_concept > benign), **Wilcoxon
signed-rank, Holm-corrected across the full 32×32 = 1024 head family, per split.** self-swap = exact no-op
(dev 0.0). Reuses `pc.ZHeadCapture` + `pc.ZHeadPatch`. Llama-3.1-8B bf16. Layer-split jobs 704129/704130
(curated) + 704131/704133 (clearharm), **all complete and merged**.

*Scope note:* patching z at the LAST position measures the head's effect on the logit **through the
remaining layers at the answer position** (no other position attends to the last token) — a total/carry
effect, not a strict direct-path contribution. Phase 7 (`direct_total`) separates direct vs mediated.

## Result — specific answer-position heads ARE necessary (Wilcoxon Holm, 1024-cell family)

Holm-significant positive-necessity heads per cell: **curated dev 58 · curated heldout 0 · clearharm
dev 31 · clearharm heldout 31.**

- **curated heldout = 0 is a low-power negative, not a true null.** It is the smallest split (n_valid=21);
  its per-head effects (though the largest in raw magnitude, e.g. L15H4 .106, L14H4 .104 with bootstrap CIs
  excluding 0) are not consistent enough at n=21 to clear a 1024-way Holm. The underpowered structural flag
  is False (pfloor 9.5e-7 < α/m 4.9e-5), so the family is resolvable — the split simply lacks power per head.
- Top heads that survive Holm (necessity C1−patched):
  - **clearharm dev:** L17H27 .035, L14H4 .033, L14H5 .027, L14H23 .021, L30H15 .020, L21H10 .018, L22H11 .018.
  - **clearharm heldout:** L17H27 .016, L14H5 .015, L18H20 .008, L30H15 .008, L31H1 .007, L15H8 .007.
  - **curated dev:** L14H4 .025, L17H27 .023, L15H8 .022, L30H15 .019, L21H10 .016, L22H19 .015, L18H20 .011.

**Heads Holm-significant in all 3 powered cells (curated dev, clearharm dev, clearharm heldout):**
`L17H27, L15H8, L18H20, L14H23, L21H10, L22H19, L30H15, L31H0, L26H13` — a **MID band (L14,15,17,18)** plus
a **LATE band (L21,22,26,30,31)**. (L14H4 strong on both dev cells; L14H5 on both clearharm cells.)

**Distributed within the bands, not a single head.** Even where 30–58 heads survive, no single head
dominates (top-10 ≈ 20–31% of total positive necessity). Effect is spread across many heads,
**layer-concentrated at L14–L15 and L17–L18**, plus a late L21–L31 group.

**Caveat (readout proximity):** the late heads (L30–L31, and to a degree L21+) sit near the unembedding, so
patching their answer-position z perturbs the logit through very few remaining layers — their necessity is
partly proximal and less mechanistically informative than the mid-band (L14–18) heads. Phase 7 tests this.

## Interpretation
- Answer-position carry of the concept runs through a **distributed set of heads in a mid band (L14–18)**
  plus a late/proximal group (L21–31), DOWNSTREAM of the L8–11 demonstration-position retrieval (K/V) and
  the L9 MLP write.
- Refines the "fully distributed" prior: no single query→demo **edge** (edge-KO null) and no single
  dominant head, BUT clear **layer structure** — the mid L14–18 band is causally necessary and replicates
  across the powered cells (both clearharm splits + curated dev).
- Circuit so far: **L8–11 demo retrieval/write (K/V + MLP@L9) → L14–18 answer-position head carry
  (distributed) → L30–31 output → logit.**

## Phase-7 candidate heads (mid-band, cross-cohort, non-proximal)
`L17H27, L15H8, L18H20, L14H23, L14H5` (+ curated-strong L14H4 as secondary). Late L30/L31 excluded as
readout-proximal (they are the DIRECT/TOTAL contrast in Phase 7).

## Caveats / next
- Answer-position effect only; a head writing at an EARLIER position the answer reads is not captured.
- Sufficiency (install DS head-z into benign) not yet run.
- curated heldout under-powered per head (n=21) — the mid-band claim rests on the 3 powered cells.

Reproduce: `python scripts/phase5_analyze.py <L0-15 dir> <L16-31 dir>` (merge halves + Wilcoxon 32×32 Holm).
