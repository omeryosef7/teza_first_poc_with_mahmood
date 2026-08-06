# VERIFY P4b-1 PATCH (scripts/phase5_head_zpatch.py, --positions demo|query|all)

Adversarial correctness audit of the demo-position z-patching path added 2026-08-06, the code
the live P4b-1 jobs run. Numeric evidence from the completed smoke
`outputs/phase5_headz_clearharm_demo_20260806_181558_728619` (positions=demo, n_prompts=2, layers
8-11, cohort clearharm) and from replicating the exact resolver over ALL 86 DOUBLESPEAK/BENIGN_REMAP
pairs of `data/bench/bench_clearharm.json` with the real Llama-3.1-8B-Instruct tokenizer.

## VERDICT: BUG-FOUND-BUT-RUN-OK

One real defect (item 1: trailing-alignment pairs non-corresponding demo slots for 5/86 items, and
under-covers DS codeword sites for 1 item). It is a donor-matching *imperfection*, not a sign
inversion or a control failure, and its impact on the aggregate per-head necessity and the Holm
family is negligible. Items 2, 3, 4, 5 are all CORRECT. The currently-running demo-position numbers
remain interpretable — do NOT kill the run on this basis, but log the caveat.

---

## Item 1 — TRAILING ALIGNMENT (the subtlest risk): REAL BUG, LOW-MEDIUM severity

**Location:** `scripts/phase5_head_zpatch.py:178-191`
```
k = min(len(ds_pos), len(b_pos))
ds_pos, b_pos = ds_pos[-k:], b_pos[-k:]
...
vecs = [z_b[l][bp][h].to(dev) for bp in b_pos]      # patched at ds_pos[i]
```

**What I checked numerically** (resolver replicated verbatim over all 86 pairs):
- Structural match holds at the metadata level: all 86 pairs have `n_demos=12`, identical
  `demo_style`, identical `codeword` (0 mismatches).
- But the *tokenizer-resolved* demo codeword-occurrence counts DIVERGE:
  - DS demo-count distribution:      `{12: 84, 11: 1, 6: 1}`
  - BENIGN demo-count distribution:  `{12: 83, 13: 3}`
  - **pairs with `len(ds_demo) != len(b_demo)`: 5 / 86**
  - `k=min` distribution: `{12: 84, 11: 1, 6: 1}` — so **k is NOT constant 12**; it is 11 and 6
    for two items. This is exactly the "varying k = smoking gun" the task flagged.
  - mismatch items: `dev/clearharm_0067 (11 vs 12)`, `dev/clearharm_0071 (12 vs 13)`,
    `dev/clearharm_0085 (12 vs 13)`, `heldout/clearharm_0053 (12 vs 13)`,
    `heldout/clearharm_0084 (6 vs 12)`.

**Why it is wrong:** in those 5 items trailing alignment pairs DS demo position *i* with a BENIGN
donor from a *different* demonstration sentence (e.g. clearharm_0084: DS demos 0-5 paired with
BENIGN demos 6-11; the ds=11/b=12 and ds=12/b=13 cases shift every pair by one slot). The i-th DS
position and i-th benign donor do NOT correspond to the same demonstration slot — precisely the
failure mode the task asked to rule out.

**Why it does NOT kill the run** (the mitigating facts, also numerically grounded):
1. Demo sentences have **no cross-condition slot correspondence by construction** — DS demos and
   BENIGN_REMAP demos are independently sampled sentence pools remapped onto the same codeword
   (`30_build_pair_benchmark.py` / clearharm builder). "Same demonstration slot" is not a
   meaningful invariant; there is no ground-truth pairing to violate.
2. In **every** mismatch case the donor is still a *benign codeword z* drawn from a benign
   demonstration site. The counterfactual sign ("replace DS reading with a benign reading") is
   preserved; the patch is never inverted and never pulls in a non-benign donor.
3. Only 5/86 items are affected; per-item necessity magnitudes are ~0.01 (smoke benign move
   p95 = 0.0109, mean 0.0018), and the necessity is averaged/paired across the valid item set with
   Wilcoxon+Holm over 128 cells — 5 marginally-noisier items cannot flip Holm significance.
4. The smoke itself (n_prompts=2 → the 4 items clearharm_0004/0007/0000/0001) hit only k=12 pairs,
   all perfectly matched (ds_demo=b_demo=12), which is why n_patch_pos is a constant 12 in
   summary.json. The 5 misaligned items only surface in the FULL 86-item live run.

**Secondary note (under-coverage):** `heldout/clearharm_0084` resolves only 6 DS codeword sites in a
12-demo block, so its DS necessity patches ~half the retrieval sites and under-estimates that one
item's effect. 1/86, negligible; flag only.

**Fix (post-hoc, not run-blocking):** align by matched demonstration index rather than blind
trailing (e.g. only accept pairs where `len(ds_demo)==len(b_demo)`, or record both raw counts and
drop the 5 mismatched items in analysis). The run already records `n_patch_pos=k`; add
`n_ds_pos`/`n_b_pos` so the analyzer can filter. Impact of leaving as-is: LOW.

---

## Item 2 — OCCURRENCE ORDER: CORRECT

`ds_common.find_word_occurrences_in_text` (ds_common.py:703-714) builds `ordered = [by_last[k] for k
in sorted(by_last)]` and sets `spans`, `last_idx=[b-1 for _,b in ordered]` from the same `ordered`
list, so spans and last_idx are parallel and ascending. Empirically, `last_idx == sorted(last_idx)`
for **0/86** DS prompts (no non-monotone case). `ds_pos`/`b_pos` are therefore consistently
left-to-right ordered before trailing. CORRECT.

---

## Item 3 — DEMO/QUERY SPLIT: CORRECT

`scripts/phase5_head_zpatch.py:106-114`. `q_char = templated.rfind(FC_PREFIX)` (rfind → the LAST,
i.e. the FC question, robust even if the prefix string recurred earlier); `q_tok` = token length of
`templated[:q_char]`; demo = `span[0] < q_tok`, query = `span[0] >= q_tok`.

Numeric check over all 86 pairs: the FC question contains the codeword exactly twice (`"the word
X"` and `"or to X"`), and the resolved **query-count is exactly 2 for all 86 DS AND all 86 BENIGN**
prompts (`query-count != 2` count = 0). No demo occurrence is misclassified into the query bucket
and both FC-question codewords land in query — this is the exact char-offset-vs-token-index bug that
`phase6_mlp_causal.py:123` warns about, and it is NOT present here. CORRECT.

---

## Item 4 — SELF-SWAP no-op & hook actually fires: CORRECT

`scripts/phase5_head_zpatch.py:207-211` builds self_vecs from DS's OWN z (`z_ds[lp][pp][0]`) at the
SAME `patch_pos`, then `ZHeadPatchMulti(lm.model, lp, 0, patch_pos, self_vecs)`.

From the smoke raw.jsonl (all 4 selfswap rows):
| sid | split | C1 | p_self | dev |
|---|---|---|---|---|
| clearharm_0004 | dev | 1.000000 | 1.000000 | 0.0 |
| clearharm_0007 | dev | 0.999901 | 0.999901 | 0.0 |
| clearharm_0000 | heldout | 0.067547 | 0.067547 | 0.0 |
| clearharm_0001 | heldout | 1.000000 | 1.000000 | 0.0 |

Self-swap deviation is **exactly 0.0** (summary `selfswap_max_dev = 0.0`). Critically this is a
genuine no-op and NOT a silently-dead hook, because the benign cells on the SAME code path DO move:
of 512 benign rows, **493 move** (96.3% at >1e-9; **43% at >1e-6** — matching the task's stated
ground-truth figure; 20% at >1e-4). ZHeadPatchMulti fires; feeding DS's own z back is a true
identity. CORRECT.

(normrand deviations 0.0/6e-6/0.0128/0.0 are the expected small norm-matched-random control.)

---

## Item 5 — ZHeadPatchMulti vecs↔positions ordering & head sweep: CORRECT

`_donor_ctx(l, h)` (phase5_head_zpatch.py:189-191): `vecs = [z_b[l][bp][h] for bp in b_pos]`,
`ZHeadPatchMulti(model, l, h, ds_pos, vecs)`. `50_path_patching.py:123-129`:
`zr[0, positions[i], head, :] = vecs[i]`. So `vecs[i]` (benign z at `b_pos[i]`, head `h`) is written
at `ds_pos[i]`, head `h`. `ds_pos` and `b_pos` are both `[-k:]` slices in the same left-to-right
order, so the i-index is consistent between them. `h` is the swept head from the
`for h in range(n_heads)` loop (phase5_head_zpatch.py:195), not a fixed head. `capture_z_at`
(line 116-121) returns `{l: {pp: [n_heads, head_dim]}}` keyed by the exact `b_pos`/`ds_pos` passed,
so every `z_b[l][bp]` / `z_ds[lp][pp]` key exists. CORRECT.

---

## Bottom line

| # | Check | Result | Severity |
|---|---|---|---|
| 1 | Trailing alignment = same demo slot | **NO** for 5/86 items; k∈{12,11,6} | LOW-MEDIUM (run OK) |
| 2 | Occurrence order left-to-right | YES (0/86 non-monotone) | — |
| 3 | FC codewords → query, demos not misclassified | YES (query-count=2 for all 86) | — |
| 4 | Self-swap exact 0.0 AND hook fires | YES (dev=0.0; 43%/96% benign move) | — |
| 5 | vecs↔positions ordering, head swept | YES | — |

The demo-position numbers the live jobs are producing are interpretable. The only real defect
(item 1) affects donor *matching quality* for ~6% of items without inverting the counterfactual or
biasing the family-wise result; it warrants an analysis-time caveat, not a run kill.
