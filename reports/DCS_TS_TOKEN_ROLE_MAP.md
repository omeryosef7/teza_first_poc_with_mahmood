# DCS-TS token-role map — cell C / semantic_one_word / n_examples=4

Generated 2026-09-07T00:53:58 · tokenizer `meta-llama/Llama-3.1-8B-Instruct` · **CPU only, no weights loaded**.

Scope: cell **C**, query_kind **semantic_one_word**, n_examples **4**, 116 domains x 2 codewords x 3 concepts = **6960 prompts**.

Artifacts: `outputs/dcs_ts/token_roles_ts116.json.gz` (per-prompt token ids, decoded tokens, spans, occurrences, per-token query roles), this report, `scripts/dcs_ts_token_roles.py`.

## Provenance

| bank | rows_sha16 observed | published | n rows | n matched |
|---|---|---|---|---|
| button_bomb | `c37127790a08519f` | `c37127790a08519f` OK | 22272 | 1160 |
| button_knife | `151ef6734bfdbe6e` | `151ef6734bfdbe6e` OK | 22272 | 1160 |
| button_gun | `e1ff5534b5318ad9` | `e1ff5534b5318ad9` OK | 22272 | 1160 |
| basket_bomb | `86463da433d0eebf` | `86463da433d0eebf` OK | 22272 | 1160 |
| basket_knife | `2839bfbc4d41a8b9` | `2839bfbc4d41a8b9` OK | 22272 | 1160 |
| basket_gun | `60b508bd1aa6d0a7` | `60b508bd1aa6d0a7` OK | 22272 | 1160 |

Split manifest `data/boombness_prompts/dcs_ts116_domain_split.json` sha16 `be7d2c772d814ef3` (field `dsplit`).

Domain split (`dsplit`) over the 116 domains present: {'validation': 23, 'train': 70, 'test': 23}.

## Checks

A check that binds to zero rows is `ERROR_EMPTY`, never a pass.

| check | status | bound to | n bound | n violations |
|---|---|---|---|---|
| `Z_bank_rows_sha16_matches_published` | **PASS** | the six ts116 banks | 6 | 0 |
| `Z_split_manifest_sha16_matches_published` | **PASS** | the domain-split manifest | 1 | 0 |
| `Y_coverage_116dom_x_2cw_x_3concept` | **PASS** | domain x codeword x concept combinations | 696 | 0 |
| `A_token_occurrence_count_matches_bank_field` | **PASS** | every matched prompt | 6960 | 0 |
| `B_codeword_positions_identical_across_concepts` | **PASS** | (codeword, prompt_id, non-reference concept) triples | 4640 | 0 |
| `C_token_ids_identical_across_concepts` | **PASS** | (codeword, prompt_id, non-reference concept) triples | 4640 | 0 |
| `D_no_bomb_knife_gun_token_anywhere` | **PASS** | every matched prompt | 6960 | 0 |
| `E_query_role_census_constant` | **PASS** | every matched prompt | 6960 | 0 |
| `F_tail_constant_except_codeword` | **PASS** | last 28 token positions of every matched prompt | 6960 | 0 |
| `H_codeword_is_one_subtoken` | **PASS** | every codeword occurrence in every prompt | 34809 | 0 |
| `J_no_inflected_codeword_false_occurrences` | **FAIL** | every matched prompt | 6960 | 9 |
| `I_dsplit_consistent_per_domain` | **PASS** | every matched prompt | 6960 | 0 |
| `G_read_position_candidates` | **PASS** | token offsets in the constant tail of every matched prompt | 40 | 0 |
| `G2_nominated_read_position_rel_end_-9` | **PASS** | every matched prompt | 6960 | 0 |

{"n_checks": 14, "n_pass": 13, "n_fail": 1, "n_error_empty": 0}

### Mutation demonstrations (`--mutate`)

| mutation | target check | status after | went RED |
|---|---|---|---|
| shift one knife prompt's last codeword position by +1 | `B_codeword_positions_identical_across_concepts` | FAIL | YES |
| perturb one gun prompt's token id at rel_end=-9 | `C_token_ids_identical_across_concepts` | FAIL | YES |
| plant one literal 'bomb' in one prompt | `D_no_bomb_knife_gun_token_anywhere` | FAIL | YES |
| relabel one query token's role | `E_query_role_census_constant` | FAIL | YES |
| bump one row's declared occurrence count | `A_token_occurrence_count_matches_bank_field` | FAIL | YES |
| change the ' refer' token in one prompt | `F_tail_constant_except_codeword` | FAIL | YES |
| truncate one prompt's last 6 tokens | `F_tail_constant_except_codeword` | FAIL | YES |
| decode the nominated read position as ' bombing' in one prompt | `G2_nominated_read_position_rel_end_-9` | FAIL | YES |
| move one prompt's last codeword occurrence downstream of the read position | `G2_nominated_read_position_rel_end_-9` | FAIL | YES |
| plant an inflected codeword match in one prompt | `J_no_inflected_codeword_false_occurrences` | FAIL | YES |
| bind the checks to an EMPTY row set | `B_codeword_positions_identical_across_concepts` | ERROR_EMPTY | YES |

## The finding that governs every answer below

At matched `(codeword, prompt_id)` the **token id sequence is identical across all three concepts in 4640/4640 comparisons** (each non-reference concept against `bomb`), and the strict whole-word count of bomb/knife/gun over the whole templated prompt is **0 in 6960/6960 prompts**.

These prompts do not merely *align* across concepts — in this cell they are the **same prompt**. `demo_surface` and `query_surface` are both `codeword` for 6960/6960 matched rows, the harm pools' `natural_word` is `bomb` for all 116 domains, and the concept never surfaces. Two consequences, both load-bearing:

1. **Criterion (b) of Q1 is satisfied at every token position, trivially.** Ranking the candidates therefore turns entirely on (a), (c), (d) and on what the position *is*, not on whether it survives a concept swap.
2. **The concept label is not identifiable from the input in this cell.** Any probe trained to separate bomb/knife/gun on cell-C `semantic_one_word` `n_examples=4` prompts is being fed byte-identical text under three different labels, so its ceiling is chance (1/3) by construction. If such a probe reports above chance, the signal is coming from something other than the prompt — run order, batching, or a leaked label — and that is a bug to find, not a result. This is the intended shape of the fix to the old 0.7485 figure, but it should be stated as a **null by construction**, not replicated as a measurement.

Whether knife and gun demonstrations actually INSTALL is untouched by any of this and remains **UNKNOWN** from prompt analysis alone: the three arms differ only in the `target_semantic` label, so installation can only be established behaviourally, on GPU.

## DEFECT — 9 prompts count a longer word as a codeword occurrence

`J_no_inflected_codeword_false_occurrences` is **FAIL**: 9/6960 prompts contain a match the house finder accepts that is not the codeword. Surfaces and counts: `{'basket|school_campus|basketball.': 9}`.

`ds_common.find_word_occurrences_in_text` rejects a match whose LEFT neighbour is alphanumeric but accepts one whose RIGHT neighbour is (its comment: "allow inflections (carrots) but not substrings inside a longer word (scarrot)"). The generator used the same rule, so the bank's own `n_codeword_occurrences` is 6 on these rows and a checker that compares the finder against that field agrees with itself and reports nothing — which is exactly why this check re-derives from the templated text instead.

Consequences, stated narrowly:

* The extra hit is in the **preamble**, upstream of every demonstration, and is a benign literal use of an unrelated word. It does not touch the nominated read position: all 6960 prompts still have that position strictly after every match.
* It DOES affect any analysis indexed by occurrence ORDINAL (occurrence 1, 2, ...), any per-occurrence attention knockout that claims to block "every codeword site", and any count of demo-installed occurrences, on these rows.
* The clean fix is a right-boundary-strict matcher; the cheap fix is to exclude the 9 rows. Either way the choice must be stated, because the two give different denominators.

## Q1 — the downstream neutral read position

Criteria: (a) strictly after every codeword occurrence, (b) byte- and token-identical across all three concepts, (c) contains none of bomb/knife/gun, (d) present in every one of the 6960 matched prompts.

| rank | rel_end | decoded | token id | role | (a) | (b) | (c) | (d) |
|---|---|---|---|---|---|---|---|---|
| 1 | `-9` | `' actually'` | 3604 | user_instruction_scaffold | 6960/6960 | 1 distinct id | yes | 6960/6960 |
| 2 | `-8` | `' refer'` | 8464 | user_instruction_scaffold | 6960/6960 | 1 distinct id | yes | 6960/6960 |
| 3 | `-7` | `' to'` | 311 | user_instruction_scaffold | 6960/6960 | 1 distinct id | yes | 6960/6960 |
| 4 | `-6` | `'?'` | 30 | punctuation | 6960/6960 | 1 distinct id | yes | 6960/6960 |
| 5 | `-5` | `'<|eot_id|>'` | 128009 | chat_scaffold | 6960/6960 | 1 distinct id | yes | 6960/6960 |
| 6 | `-4` | `'<|start_header_id|>'` | 128006 | response_header | 6960/6960 | 1 distinct id | yes | 6960/6960 |
| 7 | `-3` | `'assistant'` | 78191 | response_header | 6960/6960 | 1 distinct id | yes | 6960/6960 |
| 8 | `-2` | `'<|end_header_id|>'` | 128007 | response_header | 6960/6960 | 1 distinct id | yes | 6960/6960 |
| 9 | `-1` | `'\n\n'` | 271 | response_header | 6960/6960 | 1 distinct id | yes | 6960/6960 |

**NOMINATED: `rel_end = -9`** — the token at index `len(input_ids) -9`, decoded `' actually'`, token id `3604`. It is the token immediately after the final-query codeword occurrence, i.e. the repo's own `following` site (`ds_common.target_positions`, `extract_boombness --position following`), so a readout there is directly comparable with every existing `following` result. Verified per prompt by check `G2_nominated_read_position_rel_end_-9`: 6960/6960 prompts have the same token id there, strictly after every codeword occurrence, with no concept substring.

Two positions in the table deserve separate names rather than a rank:

* `rel_end = -6` (`'?'`) is the last token of the user turn and the last position whose content the model can attend to before the header.
* `rel_end = -1` (`'\n\n'`, the last token of `<|start_header_id|>assistant<|end_header_id|>\n\n`) is the **generation position** — the row the first output token is sampled from. It satisfies all four criteria but it is response scaffold, not query content, so a null there is a null about the readout, not about the query.

Full candidate scoring, including the disqualified offsets, is in the JSON under `read_position_candidates`.

### Why the offsets are stated relative to the END

`button` and `basket` are each **one subtoken** in every one of 34809 codeword occurrences, so the two codeword banks do not shift the tail relative to each other. Over the last 28 token positions of all 6960 prompts, the only position that varies is [-10] (the codeword itself); 0 other positions vary. Absolute indices are NOT stable — prompt length varies with the domain preamble — so a read position must be given as `len(input_ids) + rel_end`, never as a constant index.

## Q3 — query-side scaffold vs content, per prompt

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

Query-side tokens per prompt: **28**, of which **5** are chat scaffold / response header and **23** are query content. The census is identical in all 6960 prompts (check `E_query_role_census_constant`).

**The K-ladder correction.** Counting rungs backwards from the end of the sequence, `K=1` is `rel_end=-1` = `'\n\n'` (response_header), `K=2` is `rel_end=-2` = `'<|end_header_id|>'` (response_header), `K=3` `'assistant'`, `K=4` `'<|start_header_id|>'`, `K=5` `'<|eot_id|>'` (chat_scaffold). **The first five rungs carry no query content at all.** The first query-content rung is `K=6` (`'?'`, punctuation) and the first non-punctuation query token is `K=7` (`' to'`). Any future claim of the form "K=1/2 rows are query rows" is false for this bank and this template; the table above is the exact per-prompt breakdown that settles it.

## Q4 — layer convention (code reading; needs a GPU test)

Repo convention: **block layer L == hidden_states[L+1]; hidden_states[0] == embeddings**

* `src/boombness/signals.py:46` — `LAYER_CONVENTION = "block_L == hidden_states[L+1]; hidden_states[0] == embeddings"`
* `src/boombness/common.py:15` — `* 0-indexed block L  <->  hidden_states[L+1];  hidden_states[0] is the embedding.`
* `src/boombness/extract_boombness.py:21` — `LAYER CONVENTION: block L == hidden_states[L+1]; hidden_states[0] is the embedding.`
* `src/boombness/extract_boombness.py:346` — `is uniform: `hs[L+1]` is the raw output of block `L` for every `L`.`
* `src/boombness/extract_boombness.py:439` — `torch.stack([hs[L + 1, pos, :] for L in layers], dim=0)`
* `src/boombness/refusalness.py:235` — `h = out.hidden_states[L + 1][0, pos, :].float().cpu()`
* `doublespeak_causality/ds_common.py:866` — `index 0 = embeddings, index L (1..num_layers) = residual stream AFTER block L-1 (post-block).`
* `doublespeak_causality/09_attention_knockout.py:57` — `return out.hidden_states[readout_layer + 1][0, pos, :]`

**Caveat** (`src/boombness/extract_boombness.py:331-347`): transformers 5.12 ties the last entry of out.hidden_states to last_hidden_state, so hidden_states[n_layers] is the POST-FINAL-NORM state, not block n_layers-1's raw output. forward_hidden() substitutes the hooked raw output of layers[-1] so hs[L+1] is uniform in L. L = n_layers-1 is only correct through forward_hidden(); any caller reading out.hidden_states[-1] directly reads a different coordinate.

**Inconsistencies found by grep (flags, not adjudications):**

* `doublespeak_causality/44_kv_mediation.py:[289, 292]` — line 289 reads out.hidden_states[R + 1] (block convention) and line 292 reads out.hidden_states[best_ps_layer] BARE, in the same function. If best_ps_layer is a BLOCK index the two reads are one layer apart. _FLAG, not adjudicated here — needs the caller's definition of best_ps_layer_
* `doublespeak_causality/18_run_behavioral_necessity.py:99` — reps = torch.stack([hs[l][0, pos.codeword_last, :] ... for l in range(len(hs))]) — row index l of `reps` is hidden_states[l], so row l is block l-1 and row 0 is the embedding. A consumer treating row l as block l is off by one. _FLAG — depends on how the returned tensor is indexed downstream_

**Everything above is a reading of source comments and index arithmetic. It cannot distinguish the intended convention from an implementation that silently disagrees with its own docstring.** The planted-hook test that would settle it:

1. Load the model on GPU. Pick a block index L (e.g. 12) and a position p.

2. Register a forward hook on model.model.layers[L] that adds a large unique constant c (e.g. 1e3 on coordinate 0) to out[0][:, p, :].

3. Run one forward with output_hidden_states=True on any prompt, hooked and unhooked.

4. ASSERT hidden_states[L+1][0, p, 0] moves by exactly 1e3 and hidden_states[L][0, p, 0] does NOT move. If hidden_states[L] is the one that moved, the repo convention is off by one.

5. Repeat at L = n_layers-1 through extract_boombness.forward_hidden and assert the same equality, since that is the only path applying the post-final-norm substitution; also assert forward_hidden's hs[-1] differs from out.hidden_states[-1] by the RMSNorm, i.e. that the substitution is not a no-op.

6. Repeat with a forward PRE-hook on layers[L] and assert it moves hidden_states[L], not hidden_states[L+1].

7. Repeat once for every model family the sprint uses (Llama-3.1-8B-Instruct, Qwen3-14B); the tie_last_hidden_states behaviour is a transformers-version property, not a model property, so also pin transformers.__version__ in the artifact.


Fails if: the delta appears at an index other than L+1, or the L=n_layers-1 case disagrees between the raw tuple and forward_hidden().
