# DCS-TS116M token-role map -- cell C / semantic_one_word / n_examples=4

Generated 2026-09-07T03:56:57 · tokenizer `meta-llama/Llama-3.1-8B-Instruct` · **CPU only, no weights loaded** · pre-extraction checklist item **X2** of `configs/dcs_ts_pr048.json`.

## What this supersedes and why

`reports/DCS_TS_TOKEN_ROLE_MAP.md` and `scripts/dcs_ts_token_roles.py` were computed on the **ts116** bank family, VOIDED by DCS-C-074: cell C drew the harm pool with the concept word already replaced by the codeword, so the three concept arms were byte-identical (1856/1856 in the primary channel). On that bank criterion (b) of the read-site question -- "token-identical across all three concepts" -- held at every position trivially, and the prompt prefix could not differ by concept because there was only one prompt. Those two files are left unedited; they document a superseded bank. This map re-derives everything on **ts116m**, where the demonstrations differ per concept.

Scope: field `cell` == **C** (NOT `condition`; A-039), query_kind **semantic_one_word**, n_examples **4**, **115** analysed domains x 2 codewords x 3 concepts x 10 family slots = **6900 prompts**. `restaurant_kitchen` excluded (PR-048, prompt-only, preregistered): 60 cell-C rows dropped.

Artifacts: `outputs/dcs_ts/token_roles_ts116m.json.gz` (per-prompt full token ids, decoded tokens, preamble/demo/query/generation-header spans, every codeword and concept occurrence index, a role for every query-side token), this report, `scripts/dcs_ts116m_token_roles.py`.

## Provenance

| bank | rows_sha16 observed | PR-048 published | file_sha16 observed | published | rows | cell-C rows | matched |
|---|---|---|---|---|---|---|---|
| button_bomb | `4ca3ec165ab5b018` | `4ca3ec165ab5b018` OK | `dcd92d723f3e6d00` | `dcd92d723f3e6d00` OK | 22272 | 1160 | 1150 |
| button_knife | `65eb4fa533890eff` | `65eb4fa533890eff` OK | `94fd300d611fccf2` | `94fd300d611fccf2` OK | 22272 | 1160 | 1150 |
| button_gun | `c7ceb5a151a2788a` | `c7ceb5a151a2788a` OK | `8e646dfdb451abc6` | `8e646dfdb451abc6` OK | 22272 | 1160 | 1150 |
| basket_bomb | `1e872cd8cd2f63a5` | `1e872cd8cd2f63a5` OK | `79511d9e254571e6` | `79511d9e254571e6` OK | 22272 | 1160 | 1150 |
| basket_knife | `61e586e4bdca6f28` | `61e586e4bdca6f28` OK | `538ca9b48d905290` | `538ca9b48d905290` OK | 22272 | 1160 | 1150 |
| basket_gun | `f1a8332bdd7c48ce` | `f1a8332bdd7c48ce` OK | `f4c655a723729c08` | `f4c655a723729c08` OK | 22272 | 1160 | 1150 |

Split manifest `data/boombness_prompts/dcs_ts116_domain_split.json` sha16 `be7d2c772d814ef3` (published `be7d2c772d814ef3`), field `dsplit`.

`dsplit` over the 115 analysed domains: {'validation': 23, 'train': 69, 'test': 23}.

## Checks

A check that binds to zero rows is `ERROR_EMPTY`, never a pass. Every check re-derives from raw bank rows plus a real tokenization; none reads a producer-written summary field except `A`, whose entire purpose is to compare against one.

| check | status | binds to | n bound | n violations |
|---|---|---|---|---|
| `Z1_bank_sha16_matches_PR048` | **PASS** | the six ts116m banks | 6 | 0 |
| `Z2_split_manifest_sha16_matches_published` | **PASS** | the domain-split manifest | 1 | 0 |
| `Y_coverage_115dom_x_2cw_x_3concept` | **PASS** | domain x codeword x concept combinations | 690 | 0 |
| `A_token_occurrence_count_matches_bank_field` | **FAIL** | every matched prompt | 6900 | 2 |
| `B_token_ids_DIFFER_across_concepts_C074_guard` | **PASS** | (codeword, prompt_id, non-reference concept) pairs | 4600 | 0 |
| `C_query_tail_token_ids_identical_across_concepts` | **PASS** | (codeword, prompt_id, non-reference concept) pairs | 4600 | 0 |
| `D_no_bomb_knife_gun_token_anywhere_inflection_aware` | **PASS** | every matched prompt | 6900 | 0 |
| `E_query_role_census_constant` | **PASS** | every matched prompt | 6900 | 0 |
| `F_tail_constant_except_codeword` | **PASS** | last 28 token positions of every matched prompt | 6900 | 0 |
| `H_codeword_is_one_subtoken` | **FAIL** | every codeword occurrence in every prompt | 34509 | 2 |
| `J_no_inflected_codeword_false_occurrences` | **FAIL** | every matched prompt | 6900 | 9 |
| `J2_no_codeword_glued_inside_a_longer_word` | **FAIL** | every matched prompt | 6900 | 2 |
| `A2_bank_own_occurrence_fields_agree` | **FAIL** | every matched prompt | 6900 | 11 |
| `I_dsplit_consistent_per_domain` | **PASS** | every matched prompt | 6900 | 0 |
| `K_excluded_domain_absent` | **PASS** | every matched prompt | 6900 | 0 |
| `L_every_prompt_id_matched_across_three_concepts` | **PASS** | (codeword, prompt_id) keys | 2300 | 0 |
| `G_read_position_candidates` | **PASS** | token offsets in the tail of every matched prompt | 40 | 0 |
| `G2_incumbent_read_position_rel_end_-9` | **PASS** | every matched prompt | 6900 | 0 |
| `G3_incumbent_identical_across_concepts_at_matched_prompt_id` | **PASS** | (codeword, prompt_id) triples | 2300 | 0 |
| `Q2a_last_codeword_rel_end_identical_across_concepts` | **PASS** | (codeword, prompt_id) triples | 2300 | 0 |
| `Q3_length_measured_on_every_matched_prompt` | **PASS** | every matched prompt | 6900 | 0 |
| `Q4_query_roles_bound` | **PASS** | every matched prompt | 6900 | 0 |

`{"n_checks": 22, "n_pass": 17, "n_fail": 5, "n_error_empty": 0}`

### Mutation demonstrations (`--mutate`) -- 26/26 RED

| mutation | target check | status after | RED |
|---|---|---|---|
| bump one row's declared occurrence count | `A_token_occurrence_count_matches_bank_field` | FAIL (3/6900) | YES |
| make one knife prompt's token ids identical to its bomb partner (C-074 replay) | `B_token_ids_DIFFER_across_concepts_C074_guard` | FAIL (1/4600) | YES |
| perturb one gun prompt's token id at rel_end=-9 | `C_query_tail_token_ids_identical_across_concepts` | FAIL (1/4600) | YES |
| plant one literal 'knife' in one prompt | `D_no_bomb_knife_gun_token_anywhere_inflection_aware` | FAIL (1/6900) | YES |
| relabel one query token's role | `E_query_role_census_constant` | FAIL (1/6900) | YES |
| rewrite one prompt's token at rel_end=-7 | `F_tail_constant_except_codeword` | FAIL (1/6900) | YES |
| split one codeword occurrence into 2 subtokens | `H_codeword_is_one_subtoken` | FAIL (3/34509) | YES |
| plant an inflected codeword match in one prompt | `J_no_inflected_codeword_false_occurrences` | FAIL (10/6900) | YES |
| plant a left-glued codeword match in one prompt | `J2_no_codeword_glued_inside_a_longer_word` | FAIL (3/6900) | YES |
| desynchronise one row's two declared occurrence fields | `A2_bank_own_occurrence_fields_agree` | FAIL (12/6900) | YES |
| flip one row's dsplit inside a domain | `I_dsplit_consistent_per_domain` | FAIL (59/6900) | YES |
| relabel one row into the excluded domain | `K_excluded_domain_absent` | FAIL (1/6900) | YES |
| drop the gun arm of one prompt_id | `L_every_prompt_id_matched_across_three_concepts` | FAIL (1/2300) | YES |
| decode the incumbent read position as ' bombing' in one prompt | `G2_incumbent_read_position_rel_end_-9` | FAIL (1/6900) | YES |
| move one prompt's last codeword occurrence downstream of the read position | `G2_incumbent_read_position_rel_end_-9` | FAIL (1/6900) | YES |
| change one knife prompt's token id at the incumbent read position | `G3_incumbent_identical_across_concepts_at_matched_prompt_id` | FAIL (1/2300) | YES |
| shift one knife prompt's LAST codeword rel_end by -1 | `Q2a_last_codeword_rel_end_identical_across_concepts` | FAIL (1/2300) | YES |
| push every codeword occurrence to rel_end=-1 so no offset is downstream | `G_read_position_candidates` | FAIL (1/40) | YES |
| bind the checks to an EMPTY row set -> B_token_ids_DIFFER_across_concepts_C074_guard | `B_token_ids_DIFFER_across_concepts_C074_guard` | ERROR_EMPTY (0/0) | YES |
| bind the checks to an EMPTY row set -> G2_incumbent_read_position_rel_end_-9 | `G2_incumbent_read_position_rel_end_-9` | ERROR_EMPTY (1/0) | YES |
| bind the checks to an EMPTY row set -> Q3_length_measured_on_every_matched_prompt | `Q3_length_measured_on_every_matched_prompt` | ERROR_EMPTY (1/0) | YES |
| bind the checks to an EMPTY row set -> Q4_query_roles_bound | `Q4_query_roles_bound` | ERROR_EMPTY (1/0) | YES |
| corrupt one PR-048 published bank rows_sha16 | `Z1_bank_sha16_matches_PR048` | FAIL (1/6) | YES |
| bind Z1 to zero banks | `Z1_bank_sha16_matches_PR048` | ERROR_EMPTY (0/0) | YES |
| corrupt the observed split-manifest sha16 | `Z2_split_manifest_sha16_matches_published` | FAIL (1/1) | YES |
| drop the gun arm of one whole domain | `Y_coverage_115dom_x_2cw_x_3concept` | FAIL (1/688) | YES |

A mutation that does not go RED means that check cannot fail.

## Defects this map found

5 of the 22 checks are not PASS. Each is a prompt-only finding, counted with its denominator, and none of them touches the read site -- that last clause is a claim, and the counts that support it are in Q1.

### `A_token_occurrence_count_matches_bank_field` -- 2/6900 (every matched prompt)

Examples (first few):

* `['button', 'gun', '9c5c4946fd79e486', 5, 6]`
* `['basket', 'gun', '9c5c4946fd79e486', 5, 6]`

### `H_codeword_is_one_subtoken` -- 2/34509 (every codeword occurrence in every prompt)

Examples (first few):

* `['basket', 'bomb', 'cef8927c1bfbb0d4', {'span': [166, 169], 'last': 168, 'rel_end': -73, 'n_subtokens': 3, 'in_query': False, 'in_demo': True, 'in_preamble': False}]`
* `['basket', 'bomb', 'bf7c0912cf628877', {'span': [197, 200], 'last': 199, 'rel_end': -50, 'n_subtokens': 3, 'in_query': False, 'in_demo': True, 'in_preamble': False}]`

### `J_no_inflected_codeword_false_occurrences` -- 9/6900 (every matched prompt)

Surfaces and counts: `{'basket|school_campus|basketball.': 9}`; domains: `['school_campus']`.

### `J2_no_codeword_glued_inside_a_longer_word` -- 2/6900 (every matched prompt)

Surfaces and counts: `{'button|gun|subway_station|handbutton': 1, 'basket|gun|subway_station|handbasket': 1}`; domains: `['subway_station']`.

### `A2_bank_own_occurrence_fields_agree` -- 11/6900 (every matched prompt)

Examples (first few):

* `['button', 'gun', '9c5c4946fd79e486', 'subway_station', 6, 5]`
* `['basket', 'bomb', '0014a62ab040f3f4', 'school_campus', 6, 5]`
* `['basket', 'bomb', '597f2c0a3bb5ca9f', 'school_campus', 6, 5]`
* `['basket', 'bomb', '1923a074735f7189', 'school_campus', 6, 5]`
* `['basket', 'knife', '0014a62ab040f3f4', 'school_campus', 6, 5]`
* `['basket', 'knife', '597f2c0a3bb5ca9f', 'school_campus', 6, 5]`


**Three occurrence counters, and they do not agree.** Every one of these findings is the class
the phase has now paid for five times -- *the checker's notion of an occurrence must be exactly
the transformer's* -- extended here to *the substituter's notion must be too*. Each matched row
carries or admits three separate counts of "how many codeword occurrences are in this prompt":

| counter | rule | `school_campus` basketball rows | `subway_station` handgun rows |
|---|---|---|---|
| (i) the bank's `n_codeword_occurrences` | right-permissive | 6 | 6 |
| (ii) the bank's `expected_target_occurrences` span list | left- and right-strict | 5 | 5 |
| (iii) `ds_common.find_word_occurrences_in_text`, re-derived here | left-strict, right-permissive | 6 | 5 |

Check `A` compares (iii) against (i) and sees only the second column. Check `A2` compares (i)
against (ii) and sees both. A checker reading any single one of the three agrees with itself and
reports nothing, which is precisely how C-076 stayed green.

**The individual defects.**

1. `demo_pools_116dom_tsm_gun.json`, pool `subway_station|harm`, sentence 32, reads
   "A witness described the gun as a large, black **handgun** with a silver barrel." The G1
   own-concept gate counts `\bgun\b|\bguns\b`, which is 1 here, so the sentence passed.
   `prompt_families._substitute` is not left-strict, so it rewrote the `gun` inside `handgun`
   too, and the shipped demonstration reads "**handbutton**" / "**handbasket**". The
   inflection-aware whole-word rule of C-076/C-080 is blind to COMPOUNDS; the substituter is
   not. That single pool sentence is the whole of `J2` (2/6900) and the whole of `A` (2/6900).
2. `demo_pools_116dom_tsm_gun.json`, same pool, sentence 33 is TRUNCATED: "After the inspection,
   we felt relieved that no gun" -- no object and no terminal punctuation. No occurrence rule
   catches it, because its occurrence count is correct. It rides in the same demonstration block
   as (1), so it does not widen the affected row set.
3. `A2` is 11/6900: the 2 rows from (1) plus the 9 `school_campus` rows where `basket` sits
   inside `basketball.`, which is the already-preregistered C-075 finding and is also the whole
   of `J` (9/6900). PR-048 excludes `school_campus` from occurrence-ordinal and
   all-codeword-sites knockout analyses, and explicitly NOT from the probe.
4. `H` is unrelated to the substituter. Two `basket_bomb` rows in `theatre_backstage` carry the
   codeword UPPERCASED inside the demonstration text ("BASKET"), and `BASKET` is three subtokens
   where ` basket` is one. The substituter is right to produce it -- `WORD` is one of the three
   case forms it rewrites -- but any analysis that assumes one subtoken per codeword site is
   wrong on those two rows, and there are 2 such occurrences among 34509.

**Scope of the damage.** Items 1-2 are one prompt_id, `9c5c4946fd79e486`, in `subway_station`,
concept `gun`, appearing once per codeword: 2 of 6900 rows. Item 4 is 2 of 6900. Both domains
are TRAIN, so no TEST row is involved. Every one of these sits in the DEMONSTRATION BLOCK,
upstream of the query. The read-site counts in Q1 are unaffected, and that is a claim with
numbers behind it: the query codeword is one subtoken at `rel_end = -10` in 6900/6900 rows,
`Q2a` holds 2300/2300, and the nominated read site is downstream of every codeword occurrence in
6900/6900.

**What is NOT claimed.** That these are harmless. Item 1 leaks concept identity LEXICALLY -- only
the gun arm contains `hand<codeword>` -- so it is a live nuisance for the N5 concept-masked
TF-IDF baseline even though it is invisible to the N3 leakage rule, which looks for whole-word
concept names. The honest options are (a) exclude `subway_station` prospectively, as
`restaurant_kitchen` was, (b) regenerate that one pool sentence and rebuild, or (c) publish it as
a stated 2/6900 contamination and let N5 absorb it. This map does not choose. It hands the choice
over with its denominators, BEFORE any extraction, which is the only moment at which the choice
is not selection.

## The structural fact that governs every answer below

At matched `(codeword, prompt_id)` the token id sequence **DIFFERS** across concepts in 4600/4600 comparisons (each non-reference concept against `bomb`) -- the exact inverse of ts116, and the in-token form of PR-048 gate G2. The **query tail** is nevertheless byte- and token-identical across concepts in 4600/4600 of those same comparisons, and the inflection-aware whole-word count of bomb/knife/gun over the whole templated prompt is 0 in 6900/6900 prompts.

So the three arms now differ **only inside the demonstration block**, which sits between a shared preamble and a shared query. Everything downstream of the demo block is common text at a **shifted offset**. That is the whole content of question 2.

## Q1 -- is `rel_end = -9` still the right read site?

Criteria, each counted over the full population: (a) strictly after every codeword occurrence; (b) token-identical across all three concepts **at matched `prompt_id`**; (c) contains none of bomb/knife/gun; (d) exists in every matched prompt.

**Incumbent `rel_end = -9`** -- modal decoding `' actually'`, 1 distinct token id(s) over 6900 prompts, id `3604`.

| criterion | count | denominator |
|---|---|---|
| (a) strictly after every codeword occurrence | 6900 | 6900 prompts |
| (b) identical across the three concepts at matched prompt_id | 2300 | 2300 triples |
| (c) no bomb/knife/gun substring in any decoding seen there | yes | 1 distinct decoding(s) |
| (d) present in every matched prompt | 6900 | 6900 prompts |

**VERDICT: `rel_end = -9` PASSES all four criteria on ts116m.** Per-prompt confirmation: `G2_incumbent_read_position_rel_end_-9` 6900/6900; per-triple confirmation of criterion (b): `G3_incumbent_identical_across_concepts_at_matched_prompt_id` 2300/2300.

### Ranked alternatives (9 offsets satisfy all four)

| rank | rel_end | decoded | token id | role(s) | (a) n after / N | (b) n triples identical / N | (c) | (d) n present / N |
|---|---|---|---|---|---|---|---|---|
| 1 | `-9` | `' actually'` | 3604 | user_instruction_scaffold | 6900/6900 | 2300/2300 | yes | 6900/6900 |
| 2 | `-8` | `' refer'` | 8464 | user_instruction_scaffold | 6900/6900 | 2300/2300 | yes | 6900/6900 |
| 3 | `-7` | `' to'` | 311 | user_instruction_scaffold | 6900/6900 | 2300/2300 | yes | 6900/6900 |
| 4 | `-6` | `'?'` | 30 | punctuation | 6900/6900 | 2300/2300 | yes | 6900/6900 |
| 5 | `-5` | `'<|eot_id|>'` | 128009 | chat_scaffold | 6900/6900 | 2300/2300 | yes | 6900/6900 |
| 6 | `-4` | `'<|start_header_id|>'` | 128006 | response_header | 6900/6900 | 2300/2300 | yes | 6900/6900 |
| 7 | `-3` | `'assistant'` | 78191 | response_header | 6900/6900 | 2300/2300 | yes | 6900/6900 |
| 8 | `-2` | `'<|end_header_id|>'` | 128007 | response_header | 6900/6900 | 2300/2300 | yes | 6900/6900 |
| 9 | `-1` | `'\n\n'` | 271 | response_header | 6900/6900 | 2300/2300 | yes | 6900/6900 |

Ranking rule, fixed in source before scoring: query content and instruction scaffold before punctuation before chat scaffold; within a tier, nearest to the codeword first. Ranks 5-9 are chat scaffold and response header, not query content: a null read there is a null about the readout, not about the query. The substantive alternatives to rank 1 are ranks 2 and 3.

### `rel_end = -9` is NOT the preregistered primary read site, and must not be confused with it

PR-048 `read_site.position` is **`codeword_last`**, which on this population is `rel_end = -10`, decoded `' button'`. It appears in the disqualified table above because criterion (a) asks for a position strictly AFTER every codeword occurrence and the codeword is not after itself -- that is a property of the question this map answers, not a defect in the preregistered site. The two are separate positions with separate jobs:

* **`rel_end = -10` (`codeword_last`)** -- the PR-048 primary. Its `rel_end` is identical across all three concepts in 2300/2300 triples and it is one subtoken in every prompt, so it is addressable end-relatively. It carries 2 distinct token ids across the population -- one per codeword, `button` and `basket` -- which is expected and is why the two codeword banks are analysed as a transfer pair rather than pooled.
* **`rel_end = -9`** -- the DOWNSTREAM NEUTRAL site this map nominates: the repo's `following` position (`ds_common.target_positions`, `extract_boombness --position following`), one token past the query codeword. It is the control read for anything that must not sit on the codeword itself.

31 of the 40 scored offsets are disqualified. The 16 nearest the end are listed with the criterion that killed them; the full scoring, all 40 offsets, is in the JSON under `read_position_candidates`:

| rel_end | modal decoded | fails (a) | fails (b) | fails (c) | fails (d) |
|---|---|---|---|---|---|
| `-25` | `' one'` | X (0/6900) |  |  |  |
| `-24` | `' word'` | X (0/6900) |  |  |  |
| `-23` | `' and'` | X (0/6900) |  |  |  |
| `-22` | `' nothing'` | X (0/6900) |  |  |  |
| `-21` | `' else'` | X (0/6900) |  |  |  |
| `-20` | `'.'` | X (0/6900) |  |  |  |
| `-19` | `' In'` | X (0/6900) |  |  |  |
| `-18` | `' the'` | X (0/6900) |  |  |  |
| `-17` | `' text'` | X (0/6900) |  |  |  |
| `-16` | `' above'` | X (0/6900) |  |  |  |
| `-15` | `','` | X (0/6900) |  |  |  |
| `-14` | `' what'` | X (0/6900) |  |  |  |
| `-13` | `' does'` | X (0/6900) |  |  |  |
| `-12` | `' the'` | X (0/6900) |  |  |  |
| `-11` | `' word'` | X (0/6900) |  |  |  |
| `-10` | `' button'` | X (0/6900) |  |  |  |

## Q2 -- does the codeword position move across concepts?

This is the question ts116 could not ask. Reported both ways, because the answer differs between them and the difference is the whole reason a read site must be end-relative.

| concept | prompts | occurrences/prompt | LAST codeword absolute index | LAST codeword rel_end | FIRST codeword absolute | demo-block occurrences absolute |
|---|---|---|---|---|---|---|
| bomb | 2300 | 5.0013 ± 0.0361 [5, 6] | 220.2157 ± 13.1055 [191, 269] | -10.0 ± 0.0 [-10, -10] | 151.8509 ± 11.967 [37, 191] | 174.058 ± 20.7117 [118, 245] |
| knife | 2300 | 5.0013 ± 0.0361 [5, 6] | 219.4957 ± 12.425 [182, 266] | -10.0 ± 0.0 [-10, -10] | 147.1226 ± 11.5351 [37, 183] | 169.0457 ± 20.1097 [121, 235] |
| gun | 2300 | 5.0013 ± 0.0361 [5, 6] | 220.6896 ± 13.1067 [187, 269] | -10.0 ± 0.0 [-10, -10] | 149.633 ± 11.8746 [37, 193] | 172.2417 ± 20.8466 [122, 237] |

At matched `(codeword, prompt_id)`, over 2300 triples:

* the **full list of ABSOLUTE codeword indices** is identical across all three concepts in **0/2300** triples;
* the **full list of END-RELATIVE indices** is identical in **0/2300**;
* the **LAST (query) codeword's `rel_end`** is identical in **2300/2300** (check `Q2a_last_codeword_rel_end_identical_across_concepts`).

Cross-concept spread (max-min within a triple) of the LAST codeword index: **absolute 9.3557 ± 5.9002 tokens, range [0, 50]**; **end-relative 0.0 ± 0.0, range [0, 0]**.

**Consequence, stated as the task states it: an end-relative read site is safe under prefix drift and an absolute one is not.** The demo block is the only text that differs between the arms and it sits upstream of the query, so it moves every absolute index downstream of it while leaving every end-relative index untouched. Any extraction that pins a constant integer index, rather than `len(input_ids) + rel_end`, reads a different token in each concept arm.

## Q3 -- full-prompt token-length distribution per concept

| concept | n | mean | sd | min | max |
|---|---|---|---|---|---|
| bomb | 2300 | 230.2157 | 13.1055 | 201 | 279 |
| knife | 2300 | 229.4957 | 12.425 | 192 | 276 |
| gun | 2300 | 230.6896 | 13.1067 | 197 | 279 |
| **pooled** | 6900 | 230.1336 | 12.8906 | 192 | 279 |

Cross-concept spread of the means: **1.1939 tokens** on a pooled sd of **12.8906**.

Paired within-`prompt_id` difference against `bomb` (preamble and query are shared, so this isolates the demo block):

| concept | n pairs | mean delta | sd | min | max |
|---|---|---|---|---|---|
| knife - bomb | 2300 | -0.72 | 8.7223 | -50 | 20 |
| gun - bomb | 2300 | 0.4739 | 7.7347 | -32 | 38 |

### The C-084 claim, verified or refuted

PR-048 `population._register_asymmetry.n4_in_tokens` states bomb 196.21 / knife 195.5 / gun 196.69 on a 13-token sd.

| concept | claimed mean | observed, chat template applied | diff | observed, raw `full_prompt` | diff | raw + BOS | diff |
|---|---|---|---|---|---|---|---|
| bomb | 196.21 | 230.2157 | 34.0057 | 195.2157 | 0.9943 | 196.2157 | 0.0057 |
| knife | 195.5 | 229.4957 | 33.9957 | 194.4957 | 1.0043 | 195.4957 | 0.0043 |
| gun | 196.69 | 230.6896 | 33.9996 | 195.6896 | 1.0004 | 196.6896 | 0.0004 |

The chat template contributes a constant **35.0 ± 0.0** tokens (range [35, 35]) on top of the raw `full_prompt`.

**VERDICT: the C-084 figures are VERIFIED, on the raw `full_prompt` with `add_special_tokens=True`.** The raw-column difference is 0.9943, 1.0043 and 1.0004 tokens -- a constant +1 in all three, which is exactly the `<|begin_of_text|>` BOS that `add_special_tokens=True` prepends and `add_special_tokens=False` does not. Adding it back reproduces all three published means to the fourth decimal. The ORDERING is reproduced too (gun > bomb > knife) and so is the spread: **1.1939 tokens** against the published 1.19.

The claim rests on the spread-to-sd ratio, not the absolute means: **1.1939 tokens of cross-concept mean spread on a pooled sd of 12.8906** (claimed sd 13), i.e. the between-concept mean difference is under a tenth of the within-concept spread. The paired table above is the sharper version of the same statement, since preamble and query are shared inside a triple.

What did NOT survive re-derivation is any absolute positional statement: see Q2. Length and position are separate quantities here, and only the first is matched.

## Q4 -- query-side scaffold vs content, and the K-ladder

| role | tokens per prompt |
|---|---|
| chat_scaffold | 1 |
| user_instruction_scaffold | 11 |
| punctuation | 3 |
| codeword | 1 |
| concept_word | 0 |
| neutral_content | 0 |
| answer_format_instruction | 8 |
| response_header | 4 |

Query-side tokens per prompt: **28**, of which **5** are chat scaffold / response header and **23** are query content. The census is identical in 6900/6900 prompts.

### The K-ladder, counting rungs back from the end of the sequence

| K | rel_end | modal decoded | distinct decodings | role(s) | carries query content |
|---|---|---|---|---|---|
| 1 | `-1` | `'\n\n'` | 1 | response_header (6900) | no |
| 2 | `-2` | `'<|end_header_id|>'` | 1 | response_header (6900) | no |
| 3 | `-3` | `'assistant'` | 1 | response_header (6900) | no |
| 4 | `-4` | `'<|start_header_id|>'` | 1 | response_header (6900) | no |
| 5 | `-5` | `'<|eot_id|>'` | 1 | chat_scaffold (6900) | no |
| 6 | `-6` | `'?'` | 1 | punctuation (6900) | yes |
| 7 | `-7` | `' to'` | 1 | user_instruction_scaffold (6900) | yes |
| 8 | `-8` | `' refer'` | 1 | user_instruction_scaffold (6900) | yes |
| 9 | `-9` | `' actually'` | 1 | user_instruction_scaffold (6900) | yes |
| 10 | `-10` | `' button'` | 2 | codeword (6900) | yes |
| 11 | `-11` | `' word'` | 1 | user_instruction_scaffold (6900) | yes |
| 12 | `-12` | `' the'` | 1 | user_instruction_scaffold (6900) | yes |
| 13 | `-13` | `' does'` | 1 | user_instruction_scaffold (6900) | yes |
| 14 | `-14` | `' what'` | 1 | user_instruction_scaffold (6900) | yes |

**The first 5 rungs carry zero query content.** The first query-content rung is `K=6`; the first non-punctuation query-content rung is `K=7`. On the superseded ts116 map the figure was FIVE; it is re-derived here rather than inherited.

## Layer convention

Not re-derived. PR-048 `read_site.layer_convention_verified_by` records the planted-hook GPU test, job 860184, 2026-09-07: **block layer L == `hidden_states[L+1]`; `hidden_states[0]` == embeddings**, CONFIRMED BY EXPERIMENT. The superseded ts116 map's Q4 was a reading of source comments; that reading is now settled and is not repeated. The open defect recorded with it stands: `extract_boombness.forward_hidden` raises on Llama-3.1-8B under transformers 5.12, so the LAST layer is unreadable by the sanctioned path. This phase reads the 6-14 band, so it does not bite here.

