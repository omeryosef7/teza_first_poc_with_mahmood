# DCS-A-043 · REVIEW 2 · DATA AND ARTIFACTS

**Window:** `e4d78bf0..b5359329` (12 commits). The first review (`A-042`, `b80db84d..e4d78bf0`) is
not re-reviewed; its findings are cited where they bear.
**Lens:** data and artifacts, re-derived from bytes. Nothing in this report is quoted from a
producer's own summary without recomputing it.
**Discipline observed:** read-only. No file outside this one was written, no job submitted, no
probe run. Section 4 documents one diagnostic that initially sampled without a split filter and
what was done about it.

**Clock at writing:** 2026-09-07 05:55 IDT. Three of six banks are extracted; one extraction is in
flight; **no probe has been run and no outcome exists.**

---

## 0 · Verdict table

| # | Task | Verdict |
|---|---|---|
| 1 | Six ts116m banks re-derived from bytes | **PASS** — 6/6 `bank_file_sha16` and 6/6 `bank_rows_sha16` recompute to the PR-048 pin; 0 duplicate `prompt_id`s in 133,632 rows |
| 2 | Completed `ts116m_full_*` extraction runs | **PASS on 3/3 completed** (button only). `basket_knife` and `basket_gun` **have no run directory and are not queued** — see D2-01 |
| 3 | The reps themselves | **PASS** — 66,816 tensors, all `(9, 4096)`, 0 non-finite, 0 duplicated, per-layer norms reproduce to 0.0 error |
| 4 | Bomb-bank vs knife-bank reps on matched `prompt_id` | **PASS, decisively** — 0/300 identical; cross-concept cosine is *lower* than same-concept cosine at every one of 9 layers. Not the `C-074` shape |
| 5 | Analyser population filter | **PASS** — 1,140 rows/bank × 6 = **6,840**, exactly the blocker agent's figure; 4,080/1,380/1,380 train/val/test |
| 6 | Split integrity | **PASS** — 116 domains, no domain in two splits, analysed 114 = **68/23/23** |

**Ten findings.** One is operational and blocking (D2-01). Four are artifact defects in the two
FROZEN preregistrations whose recorded numbers do not reproduce from the bytes they pin
(D2-02, D2-03, D2-04, D2-05). Two are corpus-quality limits larger than the record admits
(D2-06, D2-07). Three are guard gaps (D2-08, D2-09, D2-10). **None of them voids the phase**, and
none of them touches the four checks that would have: bank binding, read site, rep integrity, and
the cross-concept separation of section 4.

---

## 1 · The six banks, re-derived from bytes

Recomputed with the repo helper `src/boombness/common.py:987` `rows_sha16`, over
`(prompt_id, prompt_sha16)` pairs sorted by `prompt_id` — the pair spelling, not the mapping
spelling, so a duplicated id could not be lost (`common.py:991`).

| bank | rows | domains | `bank_file_sha16` | vs pin | `bank_rows_sha16` | vs pin | dup `prompt_id` |
|---|---|---|---|---|---|---|---|
| `button_bomb`  | 22,272 | 116 | `dcd92d723f3e6d00` | ✅ | `4ca3ec165ab5b018` | ✅ | 0 |
| `button_knife` | 22,272 | 116 | `94fd300d611fccf2` | ✅ | `65eb4fa533890eff` | ✅ | 0 |
| `button_gun`   | 22,272 | 116 | `8e646dfdb451abc6` | ✅ | `c7ceb5a151a2788a` | ✅ | 0 |
| `basket_bomb`  | 22,272 | 116 | `79511d9e254571e6` | ✅ | `1e872cd8cd2f63a5` | ✅ | 0 |
| `basket_knife` | 22,272 | 116 | `538ca9b48d905290` | ✅ | `61e586e4bdca6f28` | ✅ | 0 |
| `basket_gun`   | 22,272 | 116 | `f4c655a723729c08` | ✅ | `f1a8332bdd7c48ce` | ✅ | 0 |

Pins at `configs/dcs_ts_pr048.json:19-48`; `configs/dcs_ts_pr049.json` carries the identical six
pins. **12/12 hashes match. 0/133,632 duplicate prompt_ids.**

### 1.1 The factorial, per bank

Every bank is the same rectangle: 4 cells × 3 query kinds × 3 doses × 116 domains.

| dose | rows per (cell × query_kind) | rows per domain per cell per query_kind |
|---|---|---|
| `n_examples=0` | 232 | 2 |
| `n_examples=4` | 1,160 | **10** |
| `n_examples=8` | 464 | 4 |

36 non-empty (cell, query_kind, n_examples) combinations per bank, `cell ∈ {A,B,C,E}`, all with
`concept` and `codeword` constant within a bank. `by_domain` is flat at 192 rows for all 116
domains in all six banks.

### 1.2 Split manifest

`data/boombness_prompts/dcs_ts116_domain_split.json` — 116 domains, `train` 70 / `validation` 23 /
`test` 23, no domain in two splits (the manifest is a single dict; a domain has one value by
construction, and the roster is exactly the 116 domains present in every bank). Its own
`manifest_sha16` **recomputes to `be7d2c772d814ef3`** under the recipe at
`scripts/dcs_ts_split_manifest.py:136` (sha256 of the body minus the hash field, `sort_keys=True`,
compact separators) — matching both the file and the PR-048 pin.

Both prospective exclusions sit in **train**: `restaurant_kitchen` → train, `subway_station` →
train. Analysed split is therefore **68 / 23 / 23 over 114 domains**, as the prereg states
(`configs/dcs_ts_pr048.json:157`). ✅

### 1.3 A join hazard that is broader than the log states

The log records (`external_md/…20260906.md:521-522`) that *"the `button` and `basket` banks share
all 22,272 `prompt_id`s — `prompt_id` does not encode the codeword."*

From bytes, the hazard is **one axis wider**: all **15/15** bank pairs share all 22,272
`prompt_id`s, including the *concept* pairs. In the primary cell all **1,160/1,160** ids are
shared while **1,160/1,160** carry a *different* `prompt_sha16`. So `prompt_id` encodes neither the
codeword nor the concept — it is a family/slot address, and `prompt_sha16` is the content hash.

This cuts both ways and both are worth stating: a join on `prompt_id` across *any* two banks
silently pairs different prompts (the hazard), and a join on `prompt_id` across two banks is
exactly the matched-pair key that makes section 4's cross-check possible (the use). Mandate §7's
compound key `(bank_file_sha16, prompt_id)` is required for the former.

---

## 2 · Extraction runs

### 2.1 Completed runs — all three verify

| field | `button_bomb` | `button_knife` | `button_gun` |
|---|---|---|---|
| run dir | `…_20260907_040927_3131687` | `…_20260907_043559_3133560` | `…_20260907_044459_4158652` |
| `DONE.json` present / status | ✅ `ok` | ✅ `ok` | ✅ `ok` |
| `rows_written` | 22,272 | 22,272 | 22,272 |
| `n_rows_captured` / `bank_n_rows` | 22,272 / 22,272 | 22,272 / 22,272 | 22,272 / 22,272 |
| `n_cached` | 22,272 | 22,272 | 22,272 |
| **cache tensor count** (loaded) | **22,272** | **22,272** | **22,272** |
| `failures.n_failed` | **0** | **0** | **0** |
| `failure_reasons` / `skip_reasons` | `{}` / `{}` | `{}` / `{}` | `{}` / `{}` |
| `bank_rows_sha16` vs PR-048 pin | ✅ | ✅ | ✅ |
| `bank_file_sha16` vs PR-048 pin | ✅ | ✅ | ✅ |
| `attn_implementation` | `eager` | `eager` | `eager` |
| `position` | `codeword_last` | `codeword_last` | `codeword_last` |
| `knockout_applied` | `false` | `false` | `false` |
| `layers` | `[6..14]` | `[6..14]` | `[6..14]` |
| SLURM job | 860352 | 860353 | 860468 |
| wall | 58.0 min | 59.0 min | 58.0 min |
| `git_commit` / `git_dirty` | `38e663ef` / **true** | `b691085e` / **true** | `b691085e` / **true** |
| tied-vs-raw last-layer relnorm | 0.6276 | 0.6280 | 0.6280 |

Every guarded field is right. The cache tensor count equalling the row count was verified by
loading, not by reading `n_cached`: `len(cache["reps"])` is 22,272 in each of the three files, and
each cache's key set is a bijection onto the bank's `prompt_id`s (every key resolved in the bank,
22,272 keys, 0 duplicate ids).

`git_dirty: true` on all three means `git_commit` does not fully identify the code that ran. Known
class, noted, not re-litigated.

### 2.2 Two partial runs of the same bank exist and carry the same pins

| run | rows | bank sha | attn | position | `DONE.json` |
|---|---|---|---|---|---|
| `ts116m_smoke_20260907_040624_3130479` | **4** / 22,272 | `4ca3ec165ab5b018` (= `button_bomb`) | eager | codeword_last | ✅ `ok` |
| `ts116m_thru_20260907_040803_3131089` | **256** / 22,272 | `4ca3ec165ab5b018` | eager | codeword_last | ✅ `ok` |

These are legitimate smoke runs and the analyser will not select them (its tag prefix is
`ts116m_full`). They are listed because they are the existence proof for D2-08: a 4-row cache
satisfies every binding check the frozen analyser performs.

### 2.3 In flight — and the log's status line is wrong

| run | state |
|---|---|
| `ts116m_full_basket_bomb_20260907_054404_4164227` | **RUNNING**, 3,302 / 22,272 rows, no `DONE.json`, no cache file yet |
| `basket_knife` | **no run directory exists** |
| `basket_gun` | **no run directory exists** |

> ### D2-01 · "The three basket banks are still running" is false; one is, and the other two are inside a single sequential job with a wall-clock deadline
>
> The log states at `external_md/…20260906.md:2140-2141`: *"The three basket
> banks are still running."* And at `:2133`: *"the multi-bank job on button_gun at 12,200/22,272
> **with three basket banks behind it**."*
>
> From bytes: `squeue` holds exactly **one** job, `860468`. `sacct -X` shows `860354`, `860355`,
> `860356`, `860357` all **`CANCELLED`** at 2026-09-07T04:42:32 — the reshape of commit `4aca75c0`.
> The surviving job runs `scripts/dcs_ts_extract_multi.py` over
> `runargs/dcs_ts116m_rest.args`, i.e. `button_gun,basket_bomb,basket_knife,basket_gun`
> **sequentially in one allocation** (`scripts/dcs_ts_extract_multi.py:70-78`, `subprocess.call`
> per bank, fail-closed). So the three basket banks are not three running jobs; they are one
> running bank and two that have not started.
>
> **Why this matters, and it is arithmetic, not pedantry.** Everything left rides on one job with
> one `TimeLimit=06:00:00`, started 04:44:04. Measured rate on the live bank: 3,302 rows in the
> 9 minutes since 05:46 = **367 rows/min**, consistent with the completed banks (22,272 in 58 min
> = 384/min). Remaining work at 05:55 is 18,970 + 22,272 + 22,272 = **63,514 rows ≈ 173 min**, plus
> ~2 min of model reload per bank. Projected finish ≈ **08:51**; the wall falls at **10:44**.
> **Margin ≈ 1 h 53 m — the job fits, with roughly 32 % headroom.** If it did not fit, the failure
> mode is a `basket_gun` directory with no `DONE.json`, which the frozen analyser refuses
> (`scripts/dcs_ts_pr048_analysis.py:213-215`) rather than silently analysing five banks.
>
> **Ask:** replace the status sentence with the job shape and the deadline arithmetic. A reader of
> the log today would believe three GPUs are working and that a single node failure costs one bank.
> One node failure currently costs **three**.

---

## 3 · The reps themselves

Loaded all three `cache/final_occurrence_reps.pt` (1,649,019,931 bytes each) and checked every
tensor, not a sample.

| check | `button_bomb` | `button_knife` | `button_gun` |
|---|---|---|---|
| `len(cache["reps"])` | 22,272 | 22,272 | 22,272 |
| distinct shapes | `{(9,4096): 22272}` | `{(9,4096): 22272}` | `{(9,4096): 22272}` |
| storage dtype | `torch.float16` ×22,272 | same | same |
| rows with any NaN/Inf | **0 / 22,272** | **0 / 22,272** | **0 / 22,272** |
| rows exactly equal to row 0 | **0 / 22,271** | **0 / 22,271** | **0 / 22,271** |
| distinct tensor fingerprints | 20,880 | 20,880 | 20,880 |
| `cache["layers"]` | `[6..14]` | same | same |
| `cache["position"]` | `codeword_last` | same | same |
| `cache["layer_convention"]` | `block_L == hidden_states[L+1]; hidden_states[0] == embeddings` | same | same |
| max abs error recomputing `hnorm|L*` from the tensor (200 rows × 9 layers) | **0.0** | **0.0** | **0.0** |

**The 20,880 is fully explained and is not a capture defect.** 22,272 − 20,880 = **1,392**, and the
banks contain exactly 1,392 duplicate `prompt_sha16` values — all at `n_examples=0`, in 696 pairs
`(A, n0) ≡ (C, n0)` and 696 pairs `(B, n0) ≡ (E, n0)`, 232 of each per query kind. With no
demonstrations the benign-literal and doublespeak cells *are the same prompt*, so identical reps
there are correct behaviour. **0 of those 1,392 rows are in the primary population** (`n_examples=4`).

This is a byte-level extension of `C-081`: the `n_examples=0` null is degenerate not only across
*concepts* (three arms, one prompt) but also across *cells* within a bank (A ≡ C, B ≡ E). Anything
that reports N1 as evidence about cell separation is reading arithmetic, not the model.

### 3.1 Per-layer norms are plausible, monotone, and dispersed

Over all 22,272 rows of `button_bomb` (the other two banks agree to within 0.1):

| layer | min | mean | max | sd |
|---|---|---|---|---|
| 6 | 4.720 | 5.535 | 6.314 | 0.261 |
| 8 | 5.359 | 6.632 | 7.823 | 0.496 |
| 10 | 6.624 | 7.673 | 8.886 | 0.417 |
| 12 | 7.251 | 8.535 | 10.063 | 0.468 |
| 14 | 8.407 | 9.557 | 11.017 | 0.359 |

Smoothly increasing with depth, no zeros, no outliers, sd well away from 0. An all-constant
capture — the failure this check exists for — is excluded twice over: by the 0/22,271 exact-equality
count and by these dispersions.

### 3.2 The read site is what the preregistration says it is

From `results.jsonl` (22,272 rows/run, 0 duplicate `prompt_id`):

* `position` = `codeword_last` in 66,816/66,816 rows; `n_subtokens` = 1 in 66,816/66,816.
* In the **primary population** (cell C × `semantic_one_word` × `n_examples=4`, both exclusions
  applied): `token_text` = `" button"` in **1,140/1,140** rows of each button bank, at
  `token_pos − seq_len` = **−10** in **1,140/1,140**, with `n_occurrences` = 5 in **1,140/1,140**.
  Zero variation. This reproduces the prereg's `_read_site_note` claim exactly.

One thing a reader should not carry away wrongly: `rel_end = −10` holds for the *`semantic_one_word`*
query kind only. Across the full bank the read offset takes three values — −11 (11,136 rows,
`behavioral` plus cell-A/C `semantic_forced_choice`), −10 (7,424), −7 (3,712, cells B/E
`semantic_forced_choice`). The prereg scopes its claim correctly; the log's summary sentences do not
always carry the scope.

And a fact worth having on record before anyone reaches for a control: in **cells B and E the read
token *is the concept word itself*** — `" bomb"`, `" knife"`, `" gun"` in 11,136/22,272 rows of each
bank. Those cells are lexically decodable at the read site by construction and can never serve as a
concept-identity control.

---

## 4 · CRITICAL CROSS-CHECK — bomb-bank vs knife-bank reps on a matched `prompt_id`

**Result: they differ, decisively, and in the direction the design requires.**

**Split discipline, disclosed.** My first pass sampled 300 matched `prompt_id`s from the whole
primary population, which included test domains. That computation produced only cosine
similarities between hidden states — no labels were fitted, no classifier trained, no accuracy or
outcome statistic computed. I discarded it and recomputed on **TRAIN domains only** (680 matched
ids, 300 sampled). Only the train-only numbers are reported below. The discarded pooled numbers
were within 0.002 of these at every layer.

Matched-pair cosine, cell C × `semantic_one_word` × `n_examples=4`, TRAIN only, n = 300 pairs:

| layer | bomb↔knife | bomb↔gun | knife↔gun | *within-bank, same domain, different prompt* |
|---|---|---|---|---|
| 6 | 0.9472 | 0.9571 | 0.9669 | 0.9719 / 0.9769 / 0.9703 |
| 8 | 0.9124 | 0.9289 | 0.9440 | 0.9470 / 0.9589 / 0.9491 |
| 9 | 0.9006 | 0.9216 | 0.9339 | 0.9429 / 0.9501 / 0.9413 |
| 11 | 0.8838 | 0.8997 | 0.9179 | 0.9208 / 0.9345 / 0.9238 |
| 12 | 0.8869 | 0.9029 | 0.9198 | 0.9243 / 0.9353 / 0.9255 |
| 14 | 0.8656 | 0.8837 | 0.9034 | 0.9095 / 0.9199 / 0.9137 |

**Identical rows: 0 / 300 in every pair, at every layer. Minimum cosine over the sample: 0.7185
(bomb↔gun, L14). Maximum: 0.9920 (knife↔gun, L6) — never 1.0.**

Three readings, stated as measurements and not as an outcome:

1. **Not `C-074`.** Cell C differs across concepts by construction (G2, re-derived in §5.2), and the
   hidden states differ accordingly. The binding is right.
2. **The concept swap moves the rep further than the prompt swap does.** At every one of the 9
   layers, the cross-concept matched-pair cosine is *below* the within-bank same-domain
   different-prompt cosine (e.g. L9: 0.9006 vs 0.9429). Two prompts that share a domain, a
   preamble, a slot and a codeword and differ only in which harm pool their four demonstrations
   came from are further apart than two prompts of the same concept in the same domain. There is a
   large systematic between-arm shift at the read site.
3. **`knife↔gun` is the closest pair at every layer**, bomb sits apart. Consistent with the
   register asymmetry the prereg measured on prompt text (hedged 14.1 % bomb / 0.2 % knife / 3.4 %
   gun) and with `R-106`'s finding that knife-vs-gun is the clean contrast and bomb-vs-anything is
   register-contaminated. It is *not* evidence that the probe will work: reading (2) is exactly
   what a strong register or length signal would also produce, which is why PR-049's bar is 0.7065
   and not 0.5.

---

## 5 · The analyser's population filter

### 5.1 It binds 6,840, and the figure is confirmed

Filter as implemented: `cell == "C"` **and** `query_kind == "semantic_one_word"` **and**
`n_examples == 4`, minus domains whose prereg exclusion scope contains `"ENTIRE"`
(`scripts/dcs_ts_pr048_analysis.py:103-104, 240, 271-274`).

| bank | primary rows | train | validation | test | domains | rows/domain |
|---|---|---|---|---|---|---|
| `button_bomb`  | 1,140 | 680 | 230 | 230 | 114 | 10 |
| `button_knife` | 1,140 | 680 | 230 | 230 | 114 | 10 |
| `button_gun`   | 1,140 | 680 | 230 | 230 | 114 | 10 |
| `basket_bomb`  | 1,140 | 680 | 230 | 230 | 114 | 10 |
| `basket_knife` | 1,140 | 680 | 230 | 230 | 114 | 10 |
| `basket_gun`   | 1,140 | 680 | 230 | 230 | 114 | 10 |
| **pooled (PR-048)** | **6,840** | **4,080** | **1,380** | **1,380** | 114 | **60** |
| PR-049 (knife+gun only) | 4,560 | 2,720 | 920 | 920 | 114 | 40 |

Before exclusions each bank has 1,160 primary rows over 116 domains; the two excluded domains
remove 20 rows/bank, 120 across the six banks.

**Cross-check against the PR-049 blocker agent: `reports/DCS_TS_PR049_BLOCKERS.md:40` reports
"6840 = 114 domains × 10 rows × 3 concepts × 2 codewords; 120 rows dropped by the two exclusions".
Confirmed exactly, every factor.** Its companion observation at `:52` — that those 6,840 rows carry
only 1,140 distinct `prompt_id`s — is also confirmed (§1.3).

The pooled test set is 23 domains × 60 rows = 1,380, so **`power.deff_at_m60` is computed at the
right m**. Which brings up the arithmetic beneath it.

> ### D2-02 · The premise Q-012 was resolved on is misstated by 3×; the conclusion survives, the sentence does not
>
> `configs/dcs_ts_pr048.json:217` closes Q-012 with: *"`power.deff_at_m60` = 6.22 … are computed at
> m=60 rows per domain. **The bank carries 30 rows per domain per concept per codeword**, so m=60 is
> arithmetically TWO codewords."*
>
> From bytes the bank carries **10** rows per domain per concept per codeword in the primary cell,
> not 30 — and PR-048 says so itself two hundred lines earlier
> (`configs/dcs_ts_pr048.json:89`, `"rows_per_domain_per_concept": 10`). The 30 is rows per domain
> per *codeword* summed over the three concepts, or rows per domain per concept summed over the
> three query kinds; it is not per-concept-per-codeword under any reading.
>
> **The conclusion is nevertheless correct**, by the route the artifact did not write down:
> 3 concepts × 10 rows × 1 codeword = 30 rows/domain, so m = 60 **is** two codewords. Verified:
> pooled test is 1,380 rows over 23 domains = 60.
>
> This is worth fixing rather than shrugging at, because the sentence is doing load-bearing work —
> it is the *entire* stated evidence that the primary pools both codewords, written specifically to
> keep that decision out of the analyst's hands. A resolution whose premise is off by 3× invites
> exactly the re-litigation it was written to prevent. **Ask:** correct the premise to
> "10 rows per domain per concept per codeword, hence 30 per domain per codeword, hence m=60 is two
> codewords", and cite `rows_per_domain_per_concept` rather than restating it.

> ### D2-03 · Q-012 is closed in PR-048 and left open in PR-049
>
> Q-012 is *"the primary statistic never named a codeword."* `configs/dcs_ts_pr049.json:200` reads:
> *"2-way knife-vs-gun argmax accuracy on the 23 untouched TEST domains, domain-mean"* — and stops,
> the identical gap. PR-049 contains **no** `_codeword_scope_reading` block; the string `codeword`
> appears 7 times in the file, none of them scoping the primary.
>
> Worse, PR-049 cannot be closed by the route PR-048 used: its `power` block
> (`sign_test_floor_n23`, `mde_by_assumed_sd`, `conjunctive_power_delta_0.15_n23_sd_0.1406`) carries
> **no m, no deff and no `n_eff_test_rows`**, so there is no arithmetic in it that implies a
> codeword count.
>
> The artifact does resolve it, but somewhere else and only implicitly: `secondary.hedge_free_stratum`
> reports *"bomb 248/460, knife 452/460, gun 420/460"* test rows per arm, and 460 = 23 × 10 × **2
> codewords**. That is derivable, and I derived it — but Q-012's whole point was that a reading
> which must be derived at analysis time by whoever is holding the data is a post-hoc choice.
> **Ask:** write the same one-paragraph resolution into PR-049, citing the 460, before the co-primary
> is run.

### 5.2 G1, G2 and G3 re-derived from bytes — and the gate numbers on record are for a population that no longer exists

I re-derived the gates independently of `scripts/dcs_ts_verify_ts116n.py`:

| gate | my re-derivation, over all 116 domains | PR-048/049 record | current verifier constant |
|---|---|---|---|
| G1 shared valences | **348/348** benign+remap+filler pools byte-identical to the shared file, for **each** of the three concepts | pass | — |
| G1 own-concept | **4,640/4,640** harm sentences per concept carry exactly one whole-word own-concept token and **0** other-concept tokens (13,920/13,920 total) | pass | — |
| G1 compounds | **1/13,920** glued occurrence, `subway_station|harm[32]` `"…a large, black handgun…"`, in an excluded domain → **0/13,680** in the analysed population | "exactly ONE" ✅ | — |
| G2 | **1,160/1,160** primary rows differ across all three concepts, **116/116** domains, for **both** codewords | `"115/115"` | **114** |
| G3a | **3,712/3,712** cell-A concept-free rows (behavioral + `semantic_one_word`) byte-identical across the three concepts, both codewords | `"3680/3680"` | 3,648 would follow |
| G3b | 0/1,856 cell-A `semantic_forced_choice` rows identical — correct, that is the arm G3b covers by substitution | `"1840/1840"` | 1,824 would follow |

The gates **pass, and pass more strongly than recorded** — I get 116/116 where the record claims
115/115, and 3,712/3,712 where it claims 3,680/3,680. But:

> ### D2-04 · One gate, three populations, inside one frozen file
>
> In `configs/dcs_ts_pr048.json` the G2 **rule** says *"…in **116/116** domains"* (line 303); the G2
> **result** four hundred lines later says *"**115/115** domains differ"* (line 335); and the
> verifier the same block names as its authority computes `N_DOMAINS = 116 - len(EXCLUDED_DOMAINS)`
> = **114** (`scripts/dcs_ts_verify_ts116n.py:123`, with `EXCLUDED_DOMAINS` = two domains at line 78).
> `configs/dcs_ts_pr049.json:335-336` carries the same 115/3,680/1,840 verbatim.
>
> The 115s and the 3,680 (= 115 × 32) and the 1,840 (= 115 × 16) are all one-domain-excluded
> numbers: they are the `restaurant_kitchen`-only era, recorded before `C-087` added
> `subway_station`. So **`gates_g1_g3.result: "19/19 PASS"` in both frozen preregistrations is a
> result that no run of the named verifier can now reproduce** — today it would print 114/114,
> 3,648/3,648, 1,824/1,824.
>
> This is the third time in this window that a recorded gate number outran the gate that produced
> it (`C-080` retracted `R-101`'s 19/19; `C-089` found a selftest gone stale). The pattern is
> specific: the *result* strings are hand-copied while the *constants* move. It is benign here only
> because I checked the bytes and they are stronger, not because the discrepancy is small.
>
> **Ask:** re-run `scripts/dcs_ts_verify_ts116n.py` and paste its current output into both frozen
> files as a dated correction (a superseding note, not an edit-in-place of a frozen result), and
> reconcile the G2 rule's "116/116" against the verifier's 114 — they are asking different
> questions and only one of them is the gate.

> ### D2-05 · `restaurant_kitchen`'s exclusion rationale does not reproduce against the pools PR-048 pins
>
> `configs/dcs_ts_pr048.json:94` justifies the exclusion with a quotation:
> *"bomb and gun harm pools generated for it keep naming a knife: bomb[39] 'A misplaced knife on the
> edge of the counter was a potential bomb hazard.'"*
>
> That sentence is **not in the pinned pools.** `grep -rl` finds it in exactly one file:
> `data/boombness_prompts/demo_pools_116dom_ts_bomb.json` — the **ts116n**-era pools, which PR-048
> supersedes. In the pinned `demo_pools_116dom_tsm_bomb.json` (`content_sha16 e561c812ee355c73`,
> verified in §5.3), `restaurant_kitchen|harm[39]` is *"The temperature gauge showed a bomb of
> fluctuating temperatures in the cold unit."* Across all three pinned pools,
> `restaurant_kitchen|harm` contains **0/120 cross-concept sentences**. The 60-candidate precursors
> in `data/boombness_prompts/ts_cand/` are clean too: **0/180**.
>
> By contrast `subway_station`'s rationale reproduces **exactly**: `handgun` at index 32 and the
> truncated *"After the inspection, we felt relieved that no gun"* at index 33, both present at
> those indices in the shipped `tsm_gun` pool. One exclusion is byte-backed; the other is inherited.
>
> **The exclusion should stand** — it is prospective, it costs one TRAIN domain, val and test stay
> 23/23, and reversing it now that reps exist would be the worse move. But the prereg's own
> summary sentence, *"Excluding it makes all three ORIGINAL uniform-seed pools fully clean (0 of
> 13920 contaminated)"*, is inverted: **all 116 domains of the pinned pools are already clean
> (0/13,920 cross-concept), `restaurant_kitchen` included.** **Ask:** relabel the exclusion as
> inherited from PR-046/ts116n and prospective, and drop the claim that it is what makes the pools
> clean.

### 5.3 Pool hashes

| pool | recomputed | file `_meta` | PR-048 pin | |
|---|---|---|---|---|
| `demo_pools_116dom_tsm_bomb.json` | `e561c812ee355c73` | `e561c812ee355c73` | `e561c812ee355c73` | ✅ |
| `demo_pools_116dom_tsm_knife.json` | `27eaf6a76f6d0526` | `27eaf6a76f6d0526` | `27eaf6a76f6d0526` | ✅ |
| `demo_pools_116dom_tsm_gun.json` | `50ba5d1fbeb5764f` | `50ba5d1fbeb5764f` | `50ba5d1fbeb5764f` | ✅ |
| `demo_pools_116dom.json` (shared) | `d3662f44d48b6329` | `976aa2b0b617118d` | `976aa2b0b617118d` | ⚠️ |

Recipe: sha256 of `json.dumps(obj["pools"], sort_keys=True, separators=(",",":"))`, first 16 hex
(`scripts/dcs_ts_length_match_pools.py:207-208`, `scripts/dcs_ts_gen_concept_harm_pools.py:181-183`).

> ### D2-06 · `content_sha16` names two incompatible recipes, and the shared-pools pin is not independently recomputable
>
> The three concept pools verify. The **shared** pools file does not, because it was written by a
> different producer using a different recipe: `src/boombness/demo_pools.py:1506` hashes
> `"\n\n".join(raw_for_hash)` — the concatenated raw sentence text in generation order — under the
> **same field name** `content_sha16`. Its `_meta` also carries `merged_from`, so the generation
> order is not recoverable from the file, and an independent verifier therefore **cannot recompute
> `976aa2b0b617118d` from the bytes at all**.
>
> `configs/dcs_ts_pr048.json:51` pins `shared_pools_sha16: "976aa2b0b617118d"` in the same block as
> three pins that *are* recomputable, with nothing marking the difference.
>
> This is `LEGACY_BANK_HASH_KEY` again, which the repo already documented and paid for
> (`src/boombness/common.py:984-1012`: *"Two functions, one name, never compared"*). The identical
> shape has reappeared one field over. It is currently harmless — G1 checks the shared valences by
> **byte comparison** (348/348 per concept, §5.2), which is strictly stronger than any hash — but
> the pin reads as verified provenance and is not.
> **Ask:** either annotate the pin with its recipe, or replace it with the file-bytes sha
> `2cb193cee81dd92a`, which anyone can check.

---

## 6 · Two corpus-quality limits larger than the record states

> ### D2-07 · The truncation defect is 52 sentences in the analysed population, not one; and it is not balanced across arms in TEST
>
> `configs/dcs_ts_pr048.json:101` excludes `subway_station` partly for a truncated harm sentence,
> and notes it is invisible to occurrence rules *"because its count is correct."* True — and that
> is precisely why the population of the defect was never counted.
>
> I scanned all **13,920** harm sentences for a missing terminal `.`/`!`/`?` (allowing trailing
> quotes and brackets). **53 are truncated. 52 of them survive both exclusions**, i.e. 52 sit in the
> analysed 114 domains, against the 1 the prereg names. They are unambiguous mid-clause cuts, not
> stylistic: `farm_storage|bomb[33]` = *"A bomb was"*, `farm_storage|knife[35]` = *"A knife"*,
> `farm_storage|gun[32]` = *"A gun was located on a"*, `radiology_suite|knife[31]` = *"The presence
> of a knife in the imaging suite was"*.
>
> **What actually reaches the probe.** Each truncated pool sentence lands in exactly one primary
> prompt, so in the pooled 6,840-row primary population **104 rows (1.5 %)** carry a truncated
> demonstration. By arm and split:
>
> | | train | validation | test | total |
> |---|---|---|---|---|
> | bomb | 24 | 4 | **10** | 38 |
> | knife | 24 | 14 | **0** | 38 |
> | gun | 16 | 8 | **4** | 28 |
> | **total** | 64 | 26 | **14** | **104** |
>
> Overall the arms are near-balanced (38/38/28 of 2,280 each), which is the reassuring half. The
> unreassuring half is the TEST column: **10 bomb, 0 knife, 4 gun of 1,380 confirmatory rows.**
> A truncated final demonstration is a syntactic cue available at the read site, it is 1.0 % of
> test rows, and it is present in one arm and absent from another. That is small — but PR-048's
> MDE is 0.0925 and PR-049's is 0.0859, and "small relative to the MDE" is a claim someone should
> make deliberately rather than by not looking.
>
> **Ask:** record the 52/13,920 and the 14/1,380 test breakdown as a stated corpus limit now,
> **before** any outcome exists, so it cannot later be produced as an explanation for whichever
> direction the result goes. Do **not** regenerate the pools: they are pinned, three banks are
> extracted against them, and a post-extraction regeneration is a new preregistration.

> ### D2-08 · The `basketball` compound reaches 9 primary rows, and the "read site unaffected" defence is right for the wrong reason
>
> `configs/dcs_ts_pr048.json:108-110` excludes `school_campus` from occurrence-ordinal and
> all-codeword-sites knockout analyses only, and explicitly **not** from the probe, because *"its
> read site is unaffected."*
>
> Re-derived: in the primary population of each **basket** bank, exactly **3/1,140** rows contain
> `basket` glued inside a word — `school_campus`, family slots 0, 8 and 12 — and all 3 carry
> `n_codeword_occurrences = 6` where every other primary row in every bank carries 5
> (`button` banks: 0/1,140 compounds, 1,140/1,140 at 5 occurrences). Across the three basket banks
> that is **9 primary rows**, all in TRAIN (`school_campus` → train).
>
> The defence holds — the spurious match is in the preamble, the read site is the *last* occurrence,
> and the completed button extractions confirm `n_occurrences = 5` in 3,420/3,420 primary rows — but
> it holds *because school_campus is in train*, not because the row is clean. Nine training rows
> carry an extra `basket` token their labels do not account for. Worth one sentence in the limits,
> and worth **re-running this exact count on the basket caches when they land**, since no basket
> extraction has yet been observed at the read site.

---

## 7 · Three guard gaps

> ### D2-09 · The frozen analyser never checks that an extraction finished, or that the knockout was off
>
> `scripts/dcs_ts_pr048_analysis.py:250-263` validates three things per bank: `bank_rows_sha16`
> against the pin, `position`, and `attn_implementation`. Then it loads the cache.
>
> `grep -n "knockout\|n_rows_captured\|n_failed\|bank_n_rows\|n_cached" scripts/dcs_ts_pr048_analysis.py`
> returns **nothing**. So the analyser would accept, silently:
>
> * a **partial** extraction — `_find_run` requires `DONE.json` (`:200-216`, correctly, per
>   `C-051`/`C-012`), but `DONE.json` is written by any run that finishes, *including a `--smoke` or
>   `--limit` run*. `outputs/…/ts116m_smoke_20260907_040624_3130479` is the live proof: 4 rows of
>   22,272, `DONE.json` `status: ok`, `bank_rows_sha16 4ca3ec165ab5b018`, `eager`, `codeword_last` —
>   every guarded field correct. Only the directory tag keeps it out.
> * a **knockout** extraction — the extractor defaults to `arm=demo_all`,
>   `knockout_scope=legacy_all_query` and only `--no-knockout` disables it
>   (`outputs/…/config.json` shows those defaults sitting in `args` on all three completed runs).
>   A rerun that lost the flag would produce `knockout_applied: true` with an identical bank sha,
>   position and attn, and the analyser would not notice.
> * a run with **failures** — `failures.n_failed > 0` is not read.
>
> No live artifact is affected: all five ts116m runs on disk are `knockout_applied: false`, and the
> three completed ones are 22,272/22,272 with `n_failed = 0`. This is a gap, not a defect.
> **Ask:** three lines beside the existing three checks — `n_rows_captured == bank_n_rows`,
> `failures.n_failed == 0`, `knockout_applied is False`. The analyser is frozen and must not be
> edited to rescue an outcome, but adding *refusals* before any outcome exists strictly narrows
> what it will accept, which is the one direction a freeze permits.

> ### D2-10 · The exclusion selector is a substring test, one window after `C-086`
>
> `scripts/dcs_ts_pr048_analysis.py:103-104` selects the analysis-wide exclusions with
> `"ENTIRE" in str(e.get("scope","")).upper()`.
>
> Today it is exactly right: it binds `{restaurant_kitchen, subway_station}` (both scoped *"the
> ENTIRE analysis population, all concepts, all cells"*) and correctly skips `school_campus`
> (*"occurrence-ordinal and all-codeword-sites knockout analyses only"*). I verified the resulting
> set by recomputing the population: 1,140 rows/bank, 114 domains.
>
> But `C-086` in this same window was *"my extraction gate opened while two blockers were
> outstanding because **'not done' contains 'done'**"*. This is that construction. A future
> exclusion scoped *"excluded from the ENTIRE knockout analysis"* would wrongly drop a domain from
> the probe; one scoped *"the whole analysis population"* would wrongly stay in. The population of
> a frozen confirmatory analysis should not be selected by prose matching.
> **Ask:** give exclusions an explicit `"analysis_wide": true|false` boolean and read that, keeping
> `scope` as human prose. Same fix `C-086` took.

---

## 8 · What I checked and found nothing wrong with

Recorded so a later reader knows these were tested, not assumed.

* `rows_sha16` was used from `src/boombness/common.py:987`, not reimplemented; the pair spelling
  was used so a duplicate id could not be hidden.
* Every cache key resolves to a bank row; the key set is a bijection onto the bank's 22,272
  `prompt_id`s in all three completed runs.
* `hnorm|L*` in `results.jsonl` recomputes from the cached tensor to **0.0** absolute error over
  200 sampled rows × 9 layers × 3 runs — the results log and the cache are the same numbers, not
  two independent claims.
* The caches store `float16` while the model ran `bfloat16`. That is a widening of the mantissa,
  not a loss, at these magnitudes (norms 4.7–11.0, nowhere near the fp16 range limit), and
  `cache["dtype"]` labels it honestly.
* N3 full-prompt leakage, re-derived independently: **0/6,840** primary rows contain any whole-word
  concept token (own or other), all inflections, case-insensitive, both codewords.
* Model provenance is identical across the three completed runs: `meta-llama/Llama-3.1-8B-Instruct`
  at commit `0e9e39f249a16976918f6564b8830bc894c89659`, `tokenizer_files_sha16 813ffe05da8767ce`,
  32 layers, hidden 4096, bf16, eager, L40S — matching the PR-048 `model` block.
* `layer_convention` is the string `R-104` confirmed by experiment, and it is recorded in all three
  caches, all three summaries and all 66,816 result rows.
* Split integrity: 116 domains in the manifest, 116 in every bank, identical sets; no domain in two
  splits; analysed 114 = 68/23/23; both excluded domains in train.

## 9 · What remains unknown

* **The three basket banks' reps.** One is 15 % extracted, two have not started. Everything in
  sections 3 and 4 is button-only. In particular the `basketball` occurrence count of D2-08, and
  the `basket` read site itself, are **UNKNOWN** at the tensor level.
* Whether the truncated demonstrations of D2-07 are separable at the read site. Not measured —
  measuring it means fitting a classifier, which is the probe.
* Whether the between-arm shift of §4 reading (2) is concept identity or register. That is the
  question the phase exists to answer and it is not answerable from these bytes.
