# P4b-1 — Per-head z-necessity at the DEMO positions (where the retrieval heads act)

**Status: ✅ COMPLETE** for the z channel, **both** position-sets — DEMO (jobs `728710` L0–15, `728711`
L16–31) and QUERY (jobs `729356` L0–15, `729357` L16–31), each pooled to the pre-registered **1 024-cell**
family; n_valid = 44 dev / 41 heldout. The demo position-set is §3; the query position-set is §7.

**Verdict: no single head is a concept-reading bottleneck at the demonstration positions. Per-head
necessity is small (≤ 0.014) and distributed; only two heads — L13H18 and L14H13 — are necessary robustly
(both splits AND both the full and clean-subset analyses).** This is the head-level analogue of P3's
distributed-retrieval finding, now measured at the positions the retrieval heads act rather than only at
the forced-choice answer token.

---

## 1. What this closes

`phase5_head_zpatch.py` had only ever patched head z at the **FC answer position**; `PHASE5_HEADS.md:74`
conceded *"a head writing at an EARLIER position the answer reads is not captured."* P4b-1 patches each
head's z at the **demonstration-codeword positions** — the L8–11 retrieval sites — with the benign
counterpart's z, and measures whether the concept readout drops.

## 2. Estimand (as corrected in `P4B_PREREGISTRATION.md` §2)

Per (layer, head): `necessity(l,h) = mean_i[ p_concept(DS) − p_concept(DS with head z at the demo
positions ← benign donor) ]`, over valid items (`C1 > benign floor`), **Wilcoxon signed-rank, Holm across
the 1 024-cell head family, per split.** The benign donor is the same prompt with the concept removed —
the matched counterfactual. Controls: **self-swap = exact 0.0** (locality; verified 0.00e+00 both splits)
and a probe-head norm-matched random donor.

*(An earlier draft of the pre-registration defined a per-cell random subtraction; that estimand is not
computable from the emitted data and was corrected before any result was read — see the §2 banner.)*

## 3. Result — the 1 024-cell pooled analysis

Guard `--expect-cells 1024` passed (n_cells = 1024 both splits); `selfswap_dev` = 0.00e+00; not
underpowered (pfloor 1e-13 ≪ α/m = 4.9e-5).

**Confirmed heads (Holm-significant positive necessity on BOTH dev AND heldout, pre-reg §4):**

| analysis | n | confirmed heads |
|---|---|---|
| **full** | 44 / 41 | **L4H16, L10H2, L13H18, L14H13** |
| **clean subset** (exact-count items only) | 37 / 36 | **L8H11, L13H18, L14H13** |
| **robust (in both)** | — | **L13H18, L14H13** |

Effect sizes are small — the largest confirmed necessity is **L4H16 = 0.0142** (dev) / 0.0061 (heldout);
the robust pair sits at **L13H18 ≈ 0.0022, L14H13 ≈ 0.0028**. Patching one head's z at the 12 demo
positions moves the concept readout by at most ~1.4 pp, and for most heads by far less.

## 4. Reading

**Concept reading at the demonstration positions is distributed across heads, not bottlenecked.** The
top-necessity head (L7H23, 0.0158 dev) is not even Holm-confirmed on both splits; the confirmed set is
small and the effects are ~1 pp. No single head, when its demo-position z is replaced by the benign
counterpart, collapses the concept readout.

**The two robust heads are in the L13–L14 carry band, not the L8–L11 write band.** L13H18 and L14H13
survive every cut. The write-band candidate L8H11 is confirmed only on the clean subset, and L4H16 only on
the full set — both are marginal. So the heads whose z is *individually* necessary for the concept to still
be read at the demo positions are carry-band heads, consistent with the circuit's L14–21 carry stage
mattering for what survives to the readout.

**This agrees with P3.** P3 found no single query→demo *attention edge* is a bottleneck; P4b-1 finds no
single *head's z-output* at the demo positions is a bottleneck either. Two different causal handles, same
distributed-redundant conclusion.

## 5. Honest limitations

- **Small effects near the measurement floor.** The confirmed necessities are 0.001–0.014. They are
  Holm-significant because they are *consistent* across items (paired Wilcoxon), not because they are
  large. This is a "distributed and weak", not a "no effect", result.
- **Trailing-alignment imperfection (verified LOW-MEDIUM).** 5 of 86 DS/benign pairs resolve to unequal
  demo-codeword counts, so the benign donor for those items comes from a non-corresponding demonstration
  slot (still a valid benign codeword z; sign never inverts); one item (`clearharm_0084`) covers only 6 of
  ~12 sites. The **clean-subset sensitivity analysis** (73 exact-count items) is exactly the control for
  this, and **L13H18 / L14H13 survive it** — the robust pair is not an alignment artifact. The heads that
  differ between full and clean (L4H16, L10H2 vs L8H11) are the marginal ones, and the full-vs-clean
  difference confounds alignment with the n = 86 → 73 power change, so neither cut's *exclusive* heads
  should be over-read.
- **z channel, clearharm only.** The demo AND query position-sets are now both done (§3, §7); the all
  position-set, the Q / K-V(group) / pattern channels, and a curated replication are the remaining P4b
  cells (`P4B_PREREGISTRATION.md` §3).
- Per-shard `summary.json` files are Holm-corrected over 512 cells (2× too lenient) and **must not be
  quoted**; only the pooled `--expect-cells 1024` output is authoritative.

## 6. Reproduce

```
# full 1024-cell pooled analysis
python scripts/phase5_analyze.py \
  outputs/phase5_headz_clearharm_demo_20260806_184037_728710 \
  outputs/phase5_headz_clearharm_demo_20260806_184037_728711 --expect-cells 1024
# clean-subset sensitivity
python scripts/phase5_analyze.py <same two dirs> \
  --only-sids-file outputs/p4b1_clean_subset.json --expect-cells 1024
```
Run: `DSBENCH=…/bench_clearharm.json DSPOS=demo DSLAYERS=0-15|16-31 slurm/run_phase5_headz.sh`.

---

## 7. Query position-set — confirmatory (✅ COMPLETE, added 2026-08-07)

The pre-registration (`P4B_PREREGISTRATION.md` §3) required a **second position-set** — patching each head's
z at the **query** codeword (the request token), not only at the demonstration sites — to check whether the
concept reading is bottlenecked at the point of use rather than at retrieval. Same estimand, same 1 024-cell
Holm family, same both-splits confirmation rule. Jobs `729356` (L0–15) / `729357` (L16–31), pooled over
88 408 rows; `selfswap_dev` = 0.00e+00; not underpowered (pfloor 1.1e-13 ≪ α/m = 4.9e-5); n_valid 44 / 41.

**Confirmed heads (Holm-sig positive necessity on BOTH dev AND heldout):**

| position-set | confirmed heads | largest effect (dev / heldout) |
|---|---|---|
| demo (§3, full) | L4H16, L10H2, L13H18, L14H13 | L4H16 0.0142 / 0.0061 |
| **query (this section)** | **L11H4, L16H28, L21H10** | **L11H4 0.0118 / 0.0030** |

Per-split Holm sets: dev {L11H4 0.0118, L11H13 0.0105, L11H12 0.0064, L16H28 0.0019, L21H10 0.0004};
heldout {L11H4 0.0030, L10H30 0.0012, L21H10 0.0009, L16H28 0.0008}. The both-splits intersection is
**{L11H4, L16H28, L21H10}**.

**Reading — the distributed/no-bottleneck conclusion holds at the query position too, and *more strongly*.**
The confirmed query heads are even smaller than the demo ones (max 0.0118 dev, 0.0030 heldout — patching one
head's z at the query codeword moves the readout by ≤ 1.2 pp), and they are a **different, mostly earlier
set** (an L11 cluster + the carry head L21H10) than the demo set. Two of the three (L16H28, L21H10) are
answer-position carry-band heads, consistent with the concept being read from the residual by the answer
position rather than freshly at the query token. **No single head bottlenecks concept-reading at either the
demonstration sites or the query codeword** — the same distributed-redundant signature P3 found for
attention edges. Per-shard `summary.json` (Holm over 512 cells) must not be quoted; only this pooled
`--expect-cells 1024` output is authoritative.

Reproduce:
```
python scripts/phase5_analyze.py \
  outputs/phase5_headz_clearharm_query_20260806_220942_729356 \
  outputs/phase5_headz_clearharm_query_20260806_221321_729357 --expect-cells 1024
```
