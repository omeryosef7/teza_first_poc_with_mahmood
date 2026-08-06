# P3 — Attention causality at the DECISION POINT

**Status: COMPLETE — both bands** (jobs `727983` L8–11 and `728189` L14–21, n = 86 each,
`attn_implementation: eager` asserted and recorded; both reconcile at 0 mismatches).

**Verdict: no query→demo-codeword edge bottleneck at the decision point.** Knocking out those edges leaves
the refusal state at the first-generated-token position statistically unchanged — while the *same
machinery*, applied to all incoming edges, moves it by **−0.62**. This is an informative null, not a dead
hook.

---

## 1. What was missing, and why this run exists

B1 was already a clean negative, and the plan (§5 P3) says it should be *presented*, not re-litigated.
What was missing was **destination coverage**: the existing knockout used the query codeword and the
forced-choice answer position, but **never the decision point** — the first generated token, which §8's
refusal result identifies as where the refusal decision is actually read.

Two things had to be built for that destination to be measurable at all:
1. **A different prompt form.** In the forced-choice harness, "final prompt token" *is* the FC answer
   index — the same position under a different name. The decision point requires the bare Doublespeak
   prompt with `add_generation_prompt=True`, whose last token is the first-generated-token position.
2. **A different readout.** There is **no concept/codeword label at the decision token**, so the
   forced-choice `p_concept` is undefined there. The readout is the last-token residual projected on the
   per-layer refusal direction (`hs18` = **decoder L17**, inside the set P7 §4c validated in *both*
   direction families).

## 2. Design

| arm | what it blocks |
|---|---|
| `edge_KO` | decision token → **demonstration codeword** positions (the retrieval pathway) |
| `rand_edge` | decision token → **count-matched random** non-demo positions |
| `all_query_edges` | decision token → **everything causal** (the firing / broad-degradation control) |

All at L8–11 (the concept-write band), all heads, eager attention **asserted at load and recorded in
`summary.json`** — under SDPA the softmax@V product is fused and the knockout would silently no-op.

**The reported quantity is the specificity `Δrefusal − Δrandom`**, where both deltas are taken against
**their own axis's baseline**. A raw shift confounds *"this edge carries refusal"* with *"masking
attention perturbs the residual stream at all"*.

## 3. Result — L8–11, n = 86

| cell | Δ refusal axis | Δ random axis | **specificity** | 95 % CI |
|---|---|---|---|---|
| `edge_KO` | −0.0032 | +0.0002 | **−0.0034** | **[−0.0078, +0.0010]** |
| `rand_edge` | −0.0570 | +0.0042 | −0.0613 | [−0.1379, −0.0007] |
| **`all_query_edges`** | **−0.6664** | −0.0503 | **−0.6161** | **[−0.7705, −0.4643]** |

**Read the third row first.** Blocking every incoming edge to the decision token moves the refusal
projection by **−0.62** with a CI nowhere near zero. The intervention machinery works, this readout is
movable, and the hook fires. That is what licenses reading the first row as a real null instead of a
silent no-op — the failure mode this project has already had to retract twice.

**The first row is the result.** The targeted decision-token → demo-codeword edges carry **no detectable
specific effect**: −0.0034, CI **includes zero**, and two orders of magnitude below what the broad control
produces.

**The second row is worth stating honestly rather than burying.** The *count-matched random* sources show
a **larger** effect (−0.061) than the demo codewords (−0.003), with a CI that only barely excludes zero
(upper bound −0.0007). Whatever this is, it is the opposite of a demo-codeword bottleneck: if the
retrieval edges were special, they would move the readout *more* than arbitrary positions, not less. Given
n = 86, three uncorrected cells, and a bound that close to zero, **I would not claim `rand_edge` is a real
effect** — but it certainly does not rescue a demo-codeword story.

## 3b. Replication on the L14–21 carry band (job `728189`, n = 86)

| cell | Δ refusal axis | Δ random axis | **specificity** | 95 % CI |
|---|---|---|---|---|
| `edge_KO` | −0.0026 | −0.0000 | **−0.0026** | **[−0.0056, +0.0003]** |
| `rand_edge` | +0.1219 | +0.0050 | +0.1169 | [−0.0262, +0.2630] |
| **`all_query_edges`** | **+1.0755** | −0.1663 | **+1.2417** | **[+0.9248, +1.5547]** |

**The null replicates.** `edge_KO` is −0.0026 with a CI including zero, essentially identical to the
−0.0034 of the write band. So the absence of a query→demo edge bottleneck at the decision point holds
across **both** the concept-write band (L8–11) and the carry band (L14–21).

**The firing control fires in both bands — and flips sign.** L8–11 gives **−0.62**, L14–21 gives
**+1.24**. Both are far from zero, so the hook demonstrably works in each band; the sign difference is
itself interpretable: severing *all* context at the carry band drives the residual **toward** refusal
(a decision token with no context to condition on defaults to refusing), whereas at the write band it
drives away from it. Either way, the machinery moves this readout by ~0.6–1.2 while the targeted
demo-codeword edges move it by ~0.003.

**`rand_edge` is noise — now settled.** §3 flagged it as barely excluding zero at L8–11 (−0.061, upper
bound −0.0007) and declined to call it real. On the carry band it is **+0.117 with a CI that includes
zero** — and it has **changed sign**. A quantity that reverses sign between bands and straddles zero in
one of them is not an effect. That caution was correct and the claim stays withdrawn.

## 4. Reading

The plan's exit condition was: *"either a causal edge appears at the decision token (new result), or the
paper states with full coverage that retrieval is distributed/redundant with no single query→demo edge
bottleneck."*

**The second exit is met, and now with the decision point covered.** Concept retrieval reaches the
decision token, but not through any identifiable query→demo attention edge — consistent with the
distributed/redundant reading, and now demonstrated at the position where the refusal decision is actually
made rather than only at a forced-choice probe.

## 5. Honest limitations

- ~~L8–11 only.~~ **Both bands now done (§3b) and the null replicates.** Still only two bands, not all 32
  layers — "no bottleneck" is established for the write and carry bands, which are the two the circuit
  story implicates, not for every layer.
- **One readout layer.** hs18 / decoder L17. It is inside P7's both-families validated set, but a single
  layer. A direction that is valid does not guarantee the *readout* is sensitive to every mechanism.
- **Destination = the decision token only.** The `query_cw` destination under the decision form has not
  been run, so this is not yet the full destination × source matrix the plan sketches.
- **`prompt_form: decision` + `destination: answer` is the decision token.** The name `answer` is
  inherited from the forced-choice code path; the pair is unambiguous because `prompt_form` is written
  into every row, but the word alone is not.
- **No per-head resolution.** This is the band-level pathway test (`--mode band`); single-head knockouts
  were already shown negligible and are not repeated here.
- n = 86, three cells, **no multiple-comparison correction** across cells.

## 6. Reproduce

```
sbatch --time=02:00:00 --nodelist=n-801,n-802,n-804,n-805,t-806 \
  --export=ALL,DSBENCH=doublespeak_causality/data/bench/bench_clearharm.json,DSNPROMPTS=0,\
DSLAYERS=8-11,DSMODE=band,DSFORM=decision,DSREADOUT=refusal_proj,DSDEST=answer,DSPROJ=18 \
  doublespeak_causality/slurm/run_phase4_edgeko.sh
```
Run dirs: `outputs/phase4_edgeKO_clearharm_20260806_135051_727983` (L8–11) and
`outputs/phase4_edgeKO_clearharm_20260806_141548_728189` (L14–21, `DSLAYERS=14-21`).

**Note on a bug fixed before this run.** The first smoke (726211) reported a random-axis shift of −0.89 in
*every* cell — a constant, not an effect. `Δrandom` was being differenced against the **refusal** axis's
baseline, so it measured the fixed offset between two directions (−0.608 vs +0.224). Both baselines are
now stored per item and the aggregator **refuses to run** if `base_proj_random` is missing. Confirmed
fixed by re-smoke 726616 before 727983 was launched.
