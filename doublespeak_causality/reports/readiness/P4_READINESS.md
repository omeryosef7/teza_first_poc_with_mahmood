# P4 readiness — Induction heads: identify, then patch properly (B2, B5)

**Scope.** Code/infrastructure inventory only, against
`reports/CAUSAL_CONTINUATION_MASTER_PLAN.md` §5 **P4** (lines 565–589). No job launched, no script
modified, no commit. All paths are relative to
`/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/doublespeak_causality/`.

**One-line verdict.**
- **P4a (identification)** — *near-launchable*: every primitive it needs already exists, but no script
  wires them together and no SLURM wrapper points at one. **~1 new script (~200 lines) + 1 wrapper**,
  **zero new primitives**, **≈0.3 GPU-h**. There is also a **zero-new-code partial** (§2.5) that
  reproduces the 3.508× ratio on ClearHarm instead of the n = 12 carrot/bomb pair.
- **P4b (the full sweep)** — **NOT launchable**, and not launchable in the literal form the plan
  specifies: the spec is **≈440 GPU-h** (§6.2) and contains a **structural impossibility** for the K/V
  cells under GQA (§6.4). It needs the position flag (§1.3), an occurrence-aligned donor rule (§6.3),
  and a hook-firing assertion that **does not exist anywhere in this repo** (§4).

---

## 1. Which position(s) `phase5_head_zpatch.py` patches, and the cost of making it configurable

### 1.1 It patches exactly one position: the last token of the forced-choice prompt

The script says so in its own docstring (`scripts/phase5_head_zpatch.py:5-10`):

```python
# scripts/phase5_head_zpatch.py:5-10
Which attention HEADS carry the Doublespeak reading? For every (layer, head), replace the DS
per-head attention output z[head] at the FC ANSWER position (last token) with the matched
BENIGN z[head] (necessity: does removing that head's contribution drop the concept reading?).
Patching at the last position measures the head's TOTAL effect on the final logit via the
remaining layers at the answer position (no other position attends to the last token; this is
a total/carry effect, NOT a strict direct-path contribution ...
```

The position is computed once, as `seq_len - 1`, and never varies:

```python
# scripts/phase5_head_zpatch.py:108-114
@torch.no_grad()
def capture_z_last(tok):
    """{L: Tensor[n_heads, head_dim]} of per-head z at the LAST position."""
    last = tok["input_ids"].shape[1] - 1
    with pc.ZHeadCapture(lm.model, layers) as cap:
        lm.model(**tok, return_dict=True)
    return {l: cap.acts[l][0, last].view(n_heads, head_dim).float().cpu() for l in layers}, last
```

and every one of the three patch call sites uses that single scalar as a one-element list:

```python
# scripts/phase5_head_zpatch.py:133   (ds_last is bound here, and only here)
z_ds, ds_last = capture_z_last(ds_tok)

# scripts/phase5_head_zpatch.py:140-142   (the 32x32 necessity cell)
donor = z_b[l][h].to(dev)
p_patched = readout(ds_tok, cid, kid,
                    [pc.ZHeadPatch(lm.model, l, h, [ds_last], donor)])

# scripts/phase5_head_zpatch.py:149 / :152   (self-swap and norm-random controls)
p_self = readout(ds_tok, cid, kid, [pc.ZHeadPatch(lm.model, lp, 0, [ds_last], self_v)])
p_rand = readout(ds_tok, cid, kid, [pc.ZHeadPatch(lm.model, lp, 0, [ds_last], rand_v.to(dev))])
```

So: **1 position, hard-coded as the final token, for all 1024 (layer, head) cells and for both
controls.** `PHASE5_HEADS.md:74` concedes the consequence in one line —
*"Answer-position effect only; a head writing at an EARLIER position the answer reads is not
captured."* The L8–11 retrieval band was therefore **never patched where it acts**, and the near-null
it produced on ClearHarm (`logs/ds_headz_704131.out:8,10` — 1 Holm-significant head in dev, 4 in
heldout, all L12–L15) is **uninformative about L8–11**, not evidence against it.

The same single-position defect applies to the sibling scripts:

| script | patched position | line |
|---|---|---|
| `scripts/phase5_head_zpatch.py` | FC last token | :111, :142 |
| `scripts/phase5b_qkv.py` | FC last token (`ds_last`) | :277, :294, :300, :308 |
| `scripts/phase4b_pattern.py` | FC last token (attention **row** at `ds_last`) | :266, :312-315 |
| `scripts/phase4c_carryedge.py` | answer position as the **query** of the KO edge | :103, :91 |

`phase4c_carryedge.py` is the only one of the four whose *keys* are the demo-codeword positions
(:91, :106) — but its query is still the answer token, so it tests "does the answer position read the
demos" and not "does head X write something at the demo position that the answer later reads".

### 1.2 The patching primitive is already position-general — the script is the bottleneck

`pair_common.ZHeadPatch` takes a **sequence** of positions and loops over it:

```python
# pair_common.py:519-520, 537-539
def __init__(self, model, layer_idx: int, head: int, positions: Sequence[int],
             corrupt_vec: torch.Tensor):
...
    for p in self.positions:
        if 0 <= p < seq:                       # skip out-of-range (decode-step safe)
            zr[0, p, self.head, :] = v
```

Note the one real limitation: it writes **the same `[head_dim]` vector to every position**. A
demo-position patch needs a *different* donor per occurrence, so either (a) instantiate one
`ZHeadPatch` per position inside the same `ExitStack` — but two pre-hooks on the same `o_proj` chain,
and the second sees the first's edited tensor, which is fine because they touch disjoint positions —
or (b) add a `Dict[int, Tensor]` overload. Option (a) needs no primitive change.
`scripts/phase5b_qkv.QKVHeadPatch` (:146-162) has the identical shape and identical limitation.

### 1.3 Effort to make the position configurable: **small — ~40–60 lines, all of it already written elsewhere**

The template exists verbatim in `scripts/phase6_mlp_causal.py`, which **already has the flag P4 needs**:

```python
# scripts/phase6_mlp_causal.py:74
ap.add_argument("--positions", default="demo", choices=["demo", "query", "all"],
```

```python
# scripts/phase6_mlp_causal.py:126-131
q_char = templated.rfind(FC_PREFIX)
q_tok = len(lm.tokenizer(templated[:q_char], add_special_tokens=False)["input_ids"])
hit = dc.find_word_occurrences_in_text(lm.tokenizer, templated, codeword)
demo_pos = [li for span, li in zip(hit.spans, hit.last_idx) if span[0] < q_tok]
query_pos = [li for span, li in zip(hit.spans, hit.last_idx) if span[0] >= q_tok]
pos = {"demo": demo_pos, "query": query_pos, "all": demo_pos + query_pos}[args.positions]
```

The comment above those lines records a bug already paid for once — comparing a **token** index
against a **char** offset silently made `query_pos` always empty. Reuse this block; do not re-derive it.

Concrete diff for `phase5_head_zpatch.py`:

1. `build_fc` (:91-95) currently returns only `tok`; make it return `(templated, tok, pos_list)` using
   the block above. **+6 lines.**
2. `capture_z_last` (:109-114) indexes `cap.acts[l][0, last]`; change to
   `cap.acts[l][0, poslist]` → `[n_pos, n_heads, head_dim]`. **+2 lines.**
3. Donor alignment: DS and BENIGN prompts differ in length and can differ in occurrence *count*, so
   donors must be matched by **occurrence order, trailing-aligned**, never by raw token index. Lift
   `scripts/phase6_mlp_causal.py:191-203` (`m = min(len(ds_demo_cw), len(b_demo_cw))`,
   `ds_swap_pos = ds_demo_cw[-m:]`, `b_swap_pos = b_demo_cw[-m:]`, plus the
   `demo_cw_count_mismatch` skip counter). **+12 lines.**
4. One `ZHeadPatch` per position inside the existing `ExitStack` (the `ctx` list at :100-102 already
   supports N contexts). **+4 lines.**
5. Position-set name into the emitted row and into the `summary.json` key. **+4 lines.**

Everything else — the readout, the validity filter (`C1 > benign_p_concept`, :183-184), the Wilcoxon +
Holm family (:160-179) — is unchanged. **This is a flag on an existing script, not a new script**, and
it is the single change that unblocks P4b-stage-1.

> Under this task's hard rules the edit was **not** made. The plan-level recommendation is to add
> `--positions {answer,demo,query,all_codewords}` to `phase5_head_zpatch.py` rather than fork it.

---

## 2. What P4a needs, and what already exists

P4a asks for four descriptive quantities, per (layer, head), on **train only**:

| # | quantity | exists? | where / why not |
|---|---|---|---|
| A | attention mass **query-codeword pos → demo-codeword positions** | **partial** | head-**averaged**, band-only, pair bench (§2.1) |
| B | attention mass **decision pos → demo-codeword positions** | **no** | nothing measures mass from the decision/answer position (§2.2) |
| C | **previous-token-head** score | **no** | zero occurrences repo-wide (§2.3) |
| D | **repeated-token / induction** score | **no** | zero occurrences repo-wide (§2.3) |
| E | overlap with the L8–11 K/V necessity band | **yes** | published bands in `reports/PHASE4_DEMO_RETRIEVAL.md` / `PHASE5_HEADS.md`; pure post-hoc set arithmetic, no GPU |

### 2.1 (A) — exists, but head-averaged and on the wrong benchmark

`next7_attention_retrieval.py` is the *only* attention-mass measurement in the repo:

```python
# next7_attention_retrieval.py:64-75
out = lm.model(**tok, output_attentions=True)
...
for L in band:
    a = out.attentions[L][0, :, q, :]              # [heads, seq]
    masses.append(float(a[:, K].sum(dim=-1).mean() / len(K)))  # per-key, head-avg
```

`.mean()` over the head axis is the problem: it produces **one band-mean scalar**, which is exactly the
`3.508×` number the plan calls out as the entire existing evidence base. Removing the `.mean()` and
keeping the `[heads]` vector is a **one-character-class change**, but the surrounding script is also
band-limited (`--band-lo 7 --band-hi 14`, :37-38), n-limited (`--n-items 12`, :39), and reads the
**pair** benchmark. The key-set machinery it delegates to
(`36_pair_attention.source_positions`, `36_pair_attention.py:53-115`) already implements
`prev_codewords` / `demos_all` / `demos_first` / `demos_last` / `request_only` / `random_matched`
with a count-matched random control — that is genuinely reusable.

**Query position:** `pc.resolve_positions(...).codeword_last` (`pair_common.py:83, :86`) is the **last**
occurrence, i.e. the query codeword. Correct for (A) as long as the prompt still contains the request
line — see the caveat in §2.4.

### 2.2 (B) — does not exist, but the capture primitive does

Nothing anywhere measures per-head attention mass *from the decision position*. The primitive is
already written, in-file and private, in `scripts/phase4b_pattern.py`:

```python
# scripts/phase4b_pattern.py:101-105
class _EagerAttnCapture:
    """Capture post-softmax attention rows attn_weights[0, head, qpos, :k_len] for a list of
    (layer, head, qpos) sites, by wrapping `eager_attention_forward`. Non-invasive: the original
    outputs are returned unchanged. After the forward, `.rows[(layer, head, qpos)]` is a float32
    CPU tensor of length k_len (the current sequence length)."""
```

It takes an arbitrary `(layer, head, qpos)` site list, so a single eager forward with
`sites = [(l, h, qpos) for l in range(32) for h in range(32) for qpos in {query_cw, decision}]`
yields every number (A) and (B) need. `output_attentions=True` (the `next7` route) is equally viable
and simpler: at ~250–300 templated tokens the full attention tensor is 32 × 32 × 300² × 2 B ≈ 184 MB.

**Definitional caveat the plan does not resolve.** In the forced-choice harness the *decision position*
and the *answer position* are the **same token** (the last one) — `phase5_head_zpatch.py:111`,
`phase4b_pattern.py:266`. They only separate in the **behavioral** harness, where the decision position
is the last prompt token before generation, i.e. `pc.PairPositions.final_prompt` /
`get("first_generated")` (`pair_common.py:49, :52-56, :88`). P4a should measure **both harnesses**, or
state explicitly that under FC readout the plan's five position sets collapse to four.

### 2.3 (C) and (D) — genuinely absent

```
grep -rn --include="*.py" -e "induction" -e "prev_token" -e "previous_token" -e "repeated_token" .
```
returns exactly three hits, none of them an implementation:
`build_refusal_direction_llama.py:145` (the English word "induction" in a comment),
`deck_build/build_deck.py:406` (slide copy), and
`scripts/phase4_edge_knockout.py:2` (the docstring calls the edge-knockout an "induction test", which
it is not — it is a causal knockout, not a head-identification score).

So the standard Elhage-style diagnostics — random-repeated-token sequence, prev-token score
`mean_i A[i, i-1]`, induction score `mean_i A[i, i-seq_len+1]` — **must be written from scratch**.
They are ~40 lines and need **no benchmark and no prompt text at all** (random token ids), which also
makes them the safest possible artifact to commit.

### 2.4 Position resolution for the ClearHarm FC prompt: two incompatible conventions already in the repo

This will silently produce the wrong answer if not chosen deliberately.

| script | prompt fed to the model | what "query codeword" means |
|---|---|---|
| `phase6_mlp_causal.py:120`, `phase4b_pattern.py:264`, `phase4c_carryedge.py:71` | `demo_block_of(raw)` + FC question — **request line stripped** | the codeword **inside the FC question** |
| `phase4_edge_knockout.py:82` | **full** DS prompt + FC question | the codeword on the **request line** (:92) |

`phase4_edge_knockout.py:79-92` documents why it made the other choice:

```python
# scripts/phase4_edge_knockout.py:80-92
# KEEP the full DS prompt (demos + request-line QUERY codeword) and append the FC question,
# so the retrieval destination is the actual query codeword (space-prefixed, findable), not
# the quote-wrapped codeword inside the question. demo = before request; query = request..question.
...
demo_pos = [li for li in hit.last_idx if li < req_tok]
query_pos = [li for li in hit.last_idx if req_tok <= li < q_tok]  # request-line query codeword
```

**For P4a the `phase4_edge_knockout` convention is the correct one** — the plan's "query-codeword
position" is the retrieval destination in the *attack*, not a quoted token in a probe question. Pick it
explicitly and record the choice in the run metadata.

### 2.5 A zero-new-code partial that upgrades the headline number today

`next7_attention_retrieval.py` reads a bench with a `pair` key and rows carrying `probe_word` /
`readout` / `condition` / `split` — and `data/bench/bench_clearharm.json` satisfies all of that
(`{'pair', '_meta', 'semantic'}`; rows have `readout: "fixed"`, 44 DOUBLESPEAK/dev, 42/heldout). So

```
python next7_attention_retrieval.py --bench data/bench/bench_clearharm.json \
    --readout fixed --split dev --n-items 44 --band-lo 7 --band-hi 14
```

would replace *"band-mean 3.508× on n = 12 of the old carrot/bomb pair"* with the same statistic on
**n = 44 ClearHarm train items** — still head-averaged, but no longer a single-pair artifact.
Two caveats: it has **no SLURM wrapper**, and `36_pair_attention.source_positions:56` calls
`dc.find_word_occurrences` (strict id matching) with **no `try/except`**, so a ClearHarm codeword that
only resolves via character offsets will raise and kill the run — the exact failure mode
`ds_common.find_word_occurrences_in_text:652-661` was written to fix.

---

## 3. The demo-codeword position helper — does it exist, and does it return all occurrences?

### 3.1 `resolve_all_occurrences` — **does not exist**

`grep -rn --include="*.py" "resolve_all_occurrences" .` → **zero hits** anywhere in the repo.

### 3.2 `find_word_occurrences_in_text` — **exists, and returns ALL occurrences**

`ds_common.py:650-715`. It is offset-based and tokenizer-agnostic, and its docstring states the
motivation is completeness:

```python
# ds_common.py:652-659
"""Locate every occurrence of `word` by CHARACTER OFFSETS. Exact and tokenizer-agnostic.

Prefer this over `find_word_occurrences` whenever the caller still has the text.
Token-id matching has to guess how a word tokenizes in context; offset mapping just
reads it off. On DeepSeek-R1-Distill-Llama-8B, id matching found 3.74 codeword
occurrences per benchmark prompt and failed outright on 8%; offsets find all of them.
That completeness matters for attention knockout, which must block *every* codeword
site (plan §11)."""
```

It returns a `WordHit` (`ds_common.py:430-442`) carrying **`spans`, `first_idx`, `last_idx` — one entry
per occurrence**:

```python
# ds_common.py:709-715
return WordHit(
    word=word, variant="+".join(sorted(variants)),
    subtoken_ids=list(ids[ordered[0][0]:ordered[0][1]]),
    spans=ordered,
    first_idx=[a for a, _ in ordered],
    last_idx=[b - 1 for _, b in ordered],
)
```

The id-matching sibling `find_word_occurrences` (`ds_common.py:500-565`) also returns all occurrences
and explicitly says so (:503-505: *"returns ALL occurrences and full span info, not just the last
position"*), with a documented fix at :509-514 for a bug where only the first matching tokenization
variant was kept, which **undercounted** occurrences.

**But: the two convenience wrappers on top of it collapse to the last occurrence, and that is the trap.**

```python
# ds_common.py:752   (target_positions)
last = hit.last_idx[-1]

# pair_common.py:83, :86   (resolve_positions)
last = last_idxs[-1]
...
codeword_all=last_idxs, codeword_last=last,
```

`dc.TargetPositions` does keep `codeword_all_last` (:722, :757) and `pc.PairPositions` keeps
`codeword_all` (:46, :86) — the full list survives — but **`codeword_last` is what almost every caller
reads**, and it is the *query* codeword, not the demos. Any P4 code must go through
`find_word_occurrences_in_text` + the `phase6_mlp_causal.py:126-131` demo/query split, **never**
through `.codeword_last`.

### 3.3 A precomputed, model-free occurrence table already exists in the v3 split

`data/splits/clearharm_doublespeak_v3.json` stores, per example,
`codeword_occurrences_templated` (list of `{"span": [a, b], "last_idx": null}`) and
`n_codeword_occurrences_templated`, written by `scripts/build_doublespeak_split.py:154-155`.
Distribution over the 324 v3 examples: **13 occurrences × 313, 14 × 6, 12 × 3, 15 × 1, 7 × 1** —
i.e. the expected 12 demonstrations + 1 query, with a handful of exceptions that must not be assumed
away. Useful as a **cross-check** on the runtime resolver (a mismatch is a loud bug signal); not
usable as the resolver itself, because `last_idx` is `null` and the spans were computed against the
raw templated DS prompt, not the FC-augmented one.

---

## 4. Does any existing harness assert that the hook fired?

**No. Not one. There is no activation-delta assertion anywhere in this repo.**

`grep -rn --include="*.py" -e "n_fired" -e "hook_fired" -e "delta_norm" -e "donor_dist" .` → zero hits.
What exists instead falls into three weaker categories:

**(a) Self-swap no-op checks — these detect the opposite failure.** `selfswap_max_dev`
(`phase5_head_zpatch.py:188-190, :202`; `phase5b_qkv.py:331-335`; `phase4b_pattern.py:365`) confirms
that patching a donor **equal to the original** changes nothing. A hook that never fires passes this
check **perfectly** (`selfswap_dev = 0.0` in every run — `logs/ds_headz_704130.out:8,10`). It is
evidence *against* corruption, and **zero evidence** that the intervention had reach.

**(b) Readout-level positive controls — two exist, both downstream, neither an activation measurement.**

```python
# scripts/phase4c_carryedge.py:112-114
# POSITIVE-firing control: block carry heads' answer -> ALL earlier keys (must change the
# reading if the knockout fires AND the carry heads' attention matters at all).
KO_all = readout(ds_tok, cid, kid, ko_ctx(ans, list(range(ans))))
```

```python
# scripts/phase_write_refusal_interaction.py:109
# positive control: FC p_concept DS vs DS+writeabl (demo block only, codeword substituted)
```

Both confound "the hook fired" with "the component matters": the `KO_all` comment says so in its own
parenthesis. A null on either is un-attributable.

**(c) GPU-free synthetic primitive tests — the strongest thing present, but offline.**
`tests/test_zhead_synthetic.py` (5 asserts) proves `ZHeadPatch` "overwrites ONLY the target head's z at
the target positions ... and the o_proj output reflects the change"; `tests/test_attnknockout_synthetic.py`
(290 lines) proves `AttentionKnockout` "sets EXACTLY the requested (query, key) cells to finfo.min",
and explicitly guards the SDPA footgun because *"ds_common.load_model defaults to
attn_implementation='sdpa' ... a knockout that did not raise would silently be a NO-OP and every
'knockout has no effect' number would be vacuous"* (:8-12). These certify the **primitive on a toy
module**. They do **not** certify that any given production cell fired against the real model, with
the real donor, at the real position — which is precisely where the retraction happened.

### 4.1 The standing retraction says the same thing, in the file itself

```python
# scripts/phase5b_qkv.py:38-43
*** AUDIT RETRACTION (iter-85): this result is INCONCLUSIVE, not a clean null. The K/V cells
patch only the ANSWER position, but under causal masking K/V are read from EARLIER source positions
(never patched) -> the K/V ~0 is a POSITIONING ARTIFACT. There is also NO positive control proving the
patch fires, and the only run was the n=2 smoke. FIX before re-use: patch K/V at the SOURCE positions the
head attends to; add a positive control (zero/large-donor must move the readout); record ||donor-self||;
run full n both splits. ***
```

Plan §1.8: *"A retracted result stays retracted and is never silently rebuilt on (`phase5b_qkv.py` Q/K/V)."*

### 4.2 New finding from the retained smoke: the hook **did** fire — the readout was at ceiling

I recomputed the deltas in the only `phase5b_qkv` run ever retained
(`outputs/phase5b_qkv_curated_20260804_013548_707412/raw.jsonl`, 36 rows, n = 2 curated):

| cell | `C1` | `C1 − patched` |
|---|---|---|
| L14H4 `q` | 0.999995 | +1.08e-06 |
| L14H4 `q_self` | 0.999995 | **0.0 exactly** |
| L14H4 `k` | 0.999995 | +1.67e-07 |
| L14H4 `v` | 0.999995 | +3.39e-07 |
| L15H8 `q` | 0.999995 | +2.39e-06 |

Two things follow, and both matter for how P4b is designed:

1. **`QKVHeadPatch` is not a no-op** — the non-self cells move by ~1e-6 while `*_self` is bit-exact 0.
   The reported `Q_nec = [0.0, 0.0, 0.0]` is a **4-dp rounding artifact in the summary**, not a dead hook.
2. **The curated FC readout was saturated at `C1 = 0.999995`.** With ~5e-6 of headroom, no intervention
   can register. The retraction diagnosed a *positioning* artifact; there is a **second, independent
   ceiling artifact** stacked on top of it. `logs/ds_p4bp_707474.out` shows the clearharm bench is
   healthier (`C1 = 0.879 dev / 0.869 heldout`), so **P4b must run on clearharm, not curated**, and must
   filter items on `C1 < 1 − ε` in addition to the existing `C1 > benign_p_concept` validity rule
   (`phase5_head_zpatch.py:183-184`).

### 4.3 What "assert the hook fired" has to mean, concretely

Per emitted cell, three scalars that no current script records:

- `donor_dist = ||donor − self||₂` and `rel = donor_dist / ||self||₂` — a donor that happens to equal
  the original is an invisible no-op. (Explicitly demanded by the retraction: *"record ||donor−self||"*.)
- `act_delta` — recapture the **downstream** activation under the patch and report
  `||h_patched − h_clean||` at a fixed probe (e.g. `resid_post` at the answer position). This is the
  only measurement that distinguishes "fired but had no effect" from "never fired".
- `n_hook_calls` — a counter incremented inside `_hook` / `_pre`. Costs one integer; catches the
  silent-skip branch `if 0 <= p < seq` (`pair_common.py:538`) dropping every position — the exact
  mechanism behind §0.9's prefill-only class of bug.

Plus an **arm-level positive control that must move the readout**: a zero donor or a large-norm donor
at the same head and the same positions. If that arm does not move `p_concept`, the cell's null is
un-reportable. Neither `ZHeadPatch` nor `QKVHeadPatch` needs modifying for any of this — the counters
go in the harness.

---

## 5. P4a — identification (train-only, descriptive, cheap)

### 5.1 Design that follows from the inventory

Single eager forward per DOUBLESPEAK train item; capture per-head attention rows at
`{query_codeword_pos, decision_pos}`; sum mass over `{demo_codeword_positions, count-matched random
non-codeword positions, all-demo-tokens}` using `36_pair_attention.source_positions:53-115`; emit a
`[32 × 32 × n_qpos × n_keyset]` table. Separately, a **prompt-free** synthetic battery
(random repeated token sequences) for the prev-token and induction scores. Then the L8–11 overlap is
pure post-hoc arithmetic on the published bands.

**Freeze the candidate set to a committed JSON before anything touches heldout** (plan §5 P4a).

### 5.2 What must be written

| item | status |
|---|---|
| `scripts/phase4a_induction_id.py` (~200 lines) | **missing** — the only new code |
| per-head attention capture | **exists** — `phase4b_pattern._EagerAttnCapture:101-142`, or `output_attentions=True` |
| key-set + count-matched random control | **exists** — `36_pair_attention.source_positions:53-115` |
| demo/query position split | **exists** — `phase4_edge_knockout.py:86-92` (preferred) or `phase6_mlp_causal.py:126-131` |
| all-occurrence finder | **exists** — `ds_common.find_word_occurrences_in_text:650` |
| prev-token / induction score | **missing** — ~40 lines, no benchmark, no prompt text |
| `slurm/run_ds_p4a.sh` | **missing** — copy `slurm/run_phase4_edgeko.sh` and swap the final `python` line |
| `configs/manifests/p4a.json` | **missing** — §1.6 forbids launching without it; the directory is empty |

### 5.3 Cost

One eager forward per item (86 items across both splits in v1; 44 if train-only) plus ~100 tiny
synthetic forwards. Model load dominates. **≈0.3 GPU-h · 1 job · `--time=00:40:00` · 1 × L40S.**
Attention tensors ≈ 184 MB at 300 tokens; `--mem=48G` is ample (see the measured-footprint note at
`slurm/run_phase4_edgeko.sh:15-18` — 4 CPU / 48 G allocates in minutes, 8 CPU / 64 G sat pending 3.5 h).

### 5.4 Launch readiness: **NOT-READY today, ~30–45 min of writing away**

No script, no wrapper, no manifest. Nothing about the physics or the primitives blocks it.

---

## 6. P4b — the full sweep

### 6.1 What the plan literally asks for

> All 32×32 heads × {pattern, Q, K, V, z, head-result} × {demo codewords, query codeword, decision
> token, answer position, all codewords}, both readouts, both splits.

= 32 × 32 × 6 × 5 = **30,720 cells**.

### 6.2 Cost of the literal spec: **≈440 GPU-h — infeasible**

Measured throughput on this exact harness and model (Llama-3.1-8B bf16, L40S, ~250–300-token FC prompts):

| run | rows | wall (incl. model load) | forwards/s |
|---|---|---|---|
| `logs/ds_headz_704131.out` (clearharm, L0–15, SDPA `ZHeadPatch`) | 44,204 | 12:37:26 → 13:14:38 | **≈ 23** |
| `logs/ds_headz_704130.out` (curated, L16–31, SDPA) | 26,214 | 12:37:26 → 13:04:11 | **≈ 17** |
| `logs/ds_edgeko_703327.out` (curated, **eager** + mask rebuild, 4 layers) | 1,024 | 07:15:25 → 07:25:29 | **≈ 3.4** |

Take 20 f/s SDPA (z, Q, K, V, head-result) and 5 f/s eager (pattern cells — `phase4b_pattern.py:13-21`
makes eager mandatory).

```
30,720 cells x 86 items x 2 readouts x ~4 arms (necessity, self-swap, count-matched random,
                                                positive control)          = 21.1M forwards
  5/6 SDPA-able : 17.6M / 20 f/s = 244 GPU-h
  1/6 eager     :  3.5M /  5 f/s = 195 GPU-h
                                   ---------
                                   439 GPU-h  ~= 110 four-hour L40S jobs
```

At the standing **max-6-parallel** rule that is ~19 waves ≈ 3–4 days of clean wall clock, on the
**`killable`** partition, with no checkpointing in any of these scripts. **Do not launch this.**

### 6.3 A staged design that is actually affordable (~35–50 GPU-h)

| stage | cells | forwards | GPU-h | jobs |
|---|---|---|---|---|
| **P4b-1** z-patch × 5 position sets, **train only** (44 items), 1 readout, 3 arms | 1024 × 5 | 676k | **≈ 9.4** | 3 × ~3.2 h (split by layer band, as 704130/704131 already do) |
| **P4b-2** freeze top ~40 heads (P4b-1 ∪ P4a candidates) × 6 activation types × 5 positions × 86 items × 4 arms, both readouts | 40 × 6 × 5 | ~412k, incl. the eager pattern subset | **≈ 25** | 6 |

P4b-1 is the decisive experiment: it is the *first* test of the L8–11 band at the positions where it
acts, and it costs under 10 GPU-h.

### 6.4 Blockers — P4b cannot be launched until all of these are settled

1. **No position-configurable head-patch script.** §1.3. This is the minimal unblocking change.
2. **Donor alignment across DS/BENIGN at demo positions.** Prompts differ in length *and* in occurrence
   count (v3 shows 7–15 occurrences). Donors must be occurrence-order trailing-aligned
   (`phase6_mlp_causal.py:191-203`) with a `demo_cw_count_mismatch` counter; index-aligned patching is
   silently wrong. `phase4b_pattern.align_row:211-225` already flags the analogous approximation
   ("APPROXIMATE across lengths ... documented as a risk") and its smoke logged
   `len_mismatch = 58/59` — i.e. the mismatch is the **norm**, not the exception.
3. **GQA makes a 32×32 K/V matrix structurally impossible.** Llama-3.1-8B has 32 query heads and **8**
   KV heads; `phase5b_qkv.py:286-288` maps `kv = h // group` — so patching "K for head h" perturbs the
   KV slice shared by **4 query heads**. The current summary nonetheless labels the result `L{l}H{h}`
   (:353), which reads as head-level and is not. The K/V panel of the matrix is **32 × 8**, and must be
   reported and Holm-corrected as such.
4. **No hook-firing assertion.** §4. The plan makes this a hard gate, and §1.8 makes the retraction
   binding. Nothing may be reported from Q/K/V until `donor_dist`, `act_delta`, `n_hook_calls` and a
   firing positive control are emitted per cell.
5. **Readout ceiling.** §4.2 — curated `C1 = 0.999995`. Use clearharm; add a `C1 < 1 − ε` filter.
6. **Position-set definition.** Under FC readout "decision token" ≡ "answer position" (§2.2); the five
   sets are four unless a behavioral/generation harness is added. Resolve before writing the manifest.
7. **Multiple testing.** `phase5_analyze.py` Holm-corrects a 1024-cell family; 30,720 cells under Holm
   annihilates any real effect. A pre-registered family structure (per position set? per activation
   type? train-frozen head subset only?) must be fixed **before** the run.
8. **Split leakage (§0.4).** 14/43 concepts and 17/21 codewords straddle train/test in v1.
   `data/splits/clearharm_doublespeak_v3.json` exists (324 examples: 162 train / 82 dev / 80 test) but
   **no bench was ever built from it** — `data/bench/` holds only v1-derived files
   (`bench_clearharm.json`, `bench_clearharm_v2.json`, `bench_curated.json`, all
   `_meta.source_split = clearharm_doublespeak_v1.json`). `scripts/split_to_bench.py` (CPU-only) closes
   the gap, **but it writes `bench_<cohort>.json` and v3 still uses cohort `clearharm`** — running it
   with the default `--out-dir data/bench` would **overwrite `bench_clearharm.json`**, the file every
   retained result was produced against. Use a separate `--out-dir`. P4a is train-only and descriptive,
   so leakage does not invalidate it; **any P4b test-split claim requires the v3 bench.**
9. **`configs/manifests/` is empty**; §1.6 forbids launching without an enumerated cell manifest.
10. **`ds_common.load_model` defaults to `attn_implementation="sdpa"`** (`ds_common.py:373`). Pattern
    cells and any `AttentionKnockout` cell must pass `eager` explicitly or become silent no-ops (§0.9).

### 6.5 Launch readiness: **NOT-READY.** Blockers 1, 2, 4 and 7 are hard prerequisites for P4b-1; add 3, 5, 6, 8 before P4b-2.

---

## 7. P4c — behavioral (out of scope here, one note)

P4c must use **decode-safe** primitives only. Per §0.9, `ZHeadPatch` (`pair_common.py:538`),
`ComponentOutSwap`, `SubmodulePatch` and `dc.LayerPatch` are all **prefill-only** — their
`if 0 <= p < seq` guard drops every position on a KV-cached decode step (`seq == 1`). The only
decode-safe head primitive is `pair_common.AllPositionZHeadAblate` (:553-598), and even there
`mode="mean"` is prefill-only by its own docstring (:558-560) — **`mode="zero"` is the only
decode-safe head ablation in the repo.**

---

## 8. Summary table

| | P4a | P4b |
|---|---|---|
| new primitives needed | **none** | none (harness-level counters only) |
| new code | 1 script ~200 lines + 1 wrapper + 1 manifest | `--positions` flag on `phase5_head_zpatch.py` (~40–60 lines) + alignment + firing assertions |
| GPU cost | **≈0.3 GPU-h**, 1 job | **≈440 GPU-h as specified**; **≈35–50 GPU-h staged** |
| launchable today | **no** (near — nothing physical blocks it) | **no** (10 blockers, §6.4) |
| zero-code partial available | **yes** — §2.5 | no |

**Files referenced:** `scripts/phase5_head_zpatch.py`, `scripts/phase5b_qkv.py`,
`scripts/phase4b_pattern.py`, `scripts/phase4c_carryedge.py`, `scripts/phase4_edge_knockout.py`,
`scripts/phase6_mlp_causal.py`, `scripts/phase_write_refusal_interaction.py`, `pair_common.py`,
`ds_common.py`, `36_pair_attention.py`, `next7_attention_retrieval.py`, `49_head_attribution.py`,
`tests/test_zhead_synthetic.py`, `tests/test_attnknockout_synthetic.py`,
`slurm/run_phase5_headz.sh`, `slurm/run_phase4_edgeko.sh`,
`outputs/phase5b_qkv_curated_20260804_013548_707412/raw.jsonl`,
`logs/ds_headz_704130.out`, `logs/ds_headz_704131.out`, `logs/ds_edgeko_703327.out`,
`logs/ds_p4bp_707474.out`, `logs/ds_p5bq_707412.out`,
`data/splits/clearharm_doublespeak_v3.json`, `reports/PHASE5_HEADS.md`,
`reports/PHASE2_ALL_OCCURRENCES.md`.
