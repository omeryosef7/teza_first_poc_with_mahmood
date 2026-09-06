# The ts116 authoritative metadata sidecar

**Artifact** `outputs/dcs_ts/ts116_sidecar.jsonl.gz` — 133,632 rows, 115 columns, 21,313,085 bytes
gzipped, `file_sha16 = 2d669592d58b434e`
**Producer** `scripts/dcs_ts_sidecar.py` (CPU only; no GPU, no SLURM, no model, no network)
**Built** 2026-09-07T00:47:21, run commit `974e404ac92c8fb859b3eb1f7e8838b072ee4101` (working tree dirty)
**Schema** `dcs_ts_sidecar/1`
**Status** 32/32 checks PASS; 24/24 mutations turn their target check RED.

> The sidecar's own `file_sha16` is **not stable across rebuilds**: every row embeds
> `sidecar_built_at` and `sidecar_run_commit`. Pin a rebuild against `bank_rows_sha16` +
> `split_manifest_sha16` + row count, which *are* stable, not against the gz's file hash.

---

## 1. What it is

One row per bank row, across all six PHASE-3 ts116 banks, carrying the mandate section 7 metadata
so that a run's per-prompt output can be joined back to its design cell.

| bank stem | `bank_sha` (= `bank_file_sha16`) | `bank_rows_sha16` | codeword | concept | rows |
|---|---|---|---|---|---|
| `ts116_button_bomb`  | `91bdb4e6f109dc9f` | `c37127790a08519f` | button | bomb  | 22,272 |
| `ts116_button_knife` | `646c2bd5350b69a9` | `151ef6734bfdbe6e` | button | knife | 22,272 |
| `ts116_button_gun`   | `3199375e2ae8ae2a` | `e1ff5534b5318ad9` | button | gun   | 22,272 |
| `ts116_basket_bomb`  | `ccec5f23a3390c25` | `86463da433d0eebf` | basket | bomb  | 22,272 |
| `ts116_basket_knife` | `46cfd285273863c0` | `2839bfbc4d41a8b9` | basket | knife | 22,272 |
| `ts116_basket_gun`   | `eb4387acec242c8b` | `60b508bd1aa6d0a7` | basket | gun   | 22,272 |
| **total** | | | | | **133,632** |

The six `bank_rows_sha16` values are **pinned in the script** (`EXPECTED_ROWS_SHA16`) against entry
R-098's published values, and `CHK-BANK-ROWS-SHA-PIN` refuses to describe a bank that is not the one
the sprint recorded.

Design coverage, re-derived from the emitted rows (not from any `_meta.json` summary):
cells A/B/C/E × query kinds behavioral / semantic_one_word / semantic_forced_choice,
**11,136 rows in each of the 12 combinations**; `n_examples` ∈ {0: 16,704 · 4: 83,520 · 8: 33,408}.

### What it reuses rather than rewrites

| Reused from | What |
|---|---|
| `src/boombness/dcs_metadata.py` | `load_bank`, `derive_row`, `sha16`, `file_sha16`, `mask_prompt`, `AMBIGUITY_RULES`, `CONTEXT_KIND_MAP`, `BANK_DIR` — and, load-bearingly, the **`(bank_file_sha16, prompt_id)` compound key** |
| `src/boombness/population_index.py` | `git_commit_safe`, `git_dirty_safe` — provenance that cannot kill the run on a node with no git binary |
| `src/boombness/prompt_families.py` | `CONDITIONS`, `QUERY_KINDS`, `_char_spans` — the **generator's own** occurrence matcher, so this audit tests the corpus rather than a freshly written regex |
| `src/boombness/common.py` | `read_jsonl`, `rows_sha16` |

`scripts/dcs_metadata_sidecar.py` (the 8-core-bank sibling) was read first and its key discipline,
collision tests and read-only stance are carried over, but it is deliberately **not imported**: it
hardcodes the 38-domain-era `CORE_BANKS` / `CORE_CELLS` / `CORE_N_EXAMPLES` and joins R-078
installation readouts that do not exist for ts116. Importing it would drag that population in.
**No file owned by another agent is edited.** Every bank `.jsonl` and `_meta.json` is opened `'r'`
only, and `CHK-BANK-IMMUTABLE` recomputes each bank's `file_sha16` after the read pass and compares
it to the value taken before.

---

## 2. ⛔ The join key. `prompt_id` alone is **not** a key — proved, not asserted

```
distinct (bank_file_sha16, prompt_id)   133,632   <- unique, = row count
distinct prompt_id                       22,272   -> collision excess 111,360
prompt_id multiplicity histogram         {6: 22272}   (every id appears in all six banks)
distinct prompt_sha16                    76,560   -> duplicate excess 57,072 (not a fallback key)
```

`CHK-PID-FANOUT` does not stop at those counts. It **simulates the mistake**: it builds a readout
table keyed by `prompt_id` from one bank (`ts116_button_bomb`) and left-joins it onto all 133,632
rows. **111,360 rows receive a readout from the wrong bank**, silently — `button_bomb` numbers
attributed to `basket_gun` prompts. That is the hazard this sidecar exists to prevent, and the
check **fails if the hazard is absent**, because a key discipline with no demonstrated hazard is an
unproven claim.

`prompt_sha16` is not a rescue either: 57,072 duplicate-excess rows. Cells that differ only in an
axis the prompt text does not encode hash identically.

**Always join on `join_key`**, emitted on every row as `f"{bank_file_sha16}:{prompt_id}"`.

---

## 3. ⚠️ `split` vs `dsplit` — two different cuts, and one of them will leak your result

| column | unit | values | source |
|---|---|---|---|
| `within_domain_split` (the bank's `split`) | **sentence**, inside each domain | dev / heldout | the bank row |
| `dsplit` | **domain** | train / validation / test | `data/boombness_prompts/dcs_ts116_domain_split.json`, `manifest_sha16 = be7d2c772d814ef3`, seed 202609061 |

`CHK-SPLIT-NOT-DSPLIT` measures it: **116/116 domains straddle `within_domain_split`**, so grouping
by it gives you every domain on both sides. It cannot function as a domain-level split. The bank's
field is therefore renamed to `within_domain_split` in the sidecar and every row carries
`split_field_note` spelling the distinction out.

`dsplit` totals, re-derived from the emitted rows:

| dsplit | domains | rows |
|---|---|---|
| train | 70 | 80,640 |
| validation | 23 | 26,496 |
| test | 23 | 26,496 |

Every domain receives **exactly one** `dsplit` (`CHK-DSPLIT-TOTAL`, `CHK-DSPLIT-ROWSTATUS`,
133,632/133,632 rows `dsplit_status == "OK"`), and the assignment is identical in all six banks
(`CHK-DSPLIT-BANK-INVARIANT`).

The manifest is parsed with `object_pairs_hook`, **not** a plain `json.load`. A domain assigned
twice in the JSON is a duplicate key, and `json.load` silently keeps only the last one — the
ambiguous case would be invisible to a normal parse. The `dsplit_ambiguous` mutation injects exactly
that and turns `CHK-DSPLIT-TOTAL` red.

Discipline, quoted from the manifest: *discovery scripts read `train` only; `test` is used only for
frozen confirmatory replication, never for layer/head/path/direction/threshold selection.*

---

## 4. Finding: the bank uses **two different occurrence matchers**, and they disagree on 180 rows

This was not known before this sidecar was built.

* `expected_target_occurrences` / `n_target_occurrences` come from
  `prompt_families._char_spans` — **whole-word**, case-insensitive (`\b…\b`).
* `n_codeword_occurrences` / `n_concept_occurrences` come from `prompt_families.py:521-522`,
  `full.lower().count(word.lower())` — a **substring** count.

Re-deriving the substring rule reproduces the bank field on **133,632/133,632** rows, so the bank
field is fully modelled (`CHK-OCCURRENCE-COUNTS`). But the two matchers diverge on **180 rows**,
all of them the same cause:

| where | rows |
|---|---|
| `ts116_basket_bomb`, domain `school_campus` | 60 |
| `ts116_basket_knife`, domain `school_campus` | 60 |
| `ts116_basket_gun`, domain `school_campus` | 60 |
| **total** | **180** (0.135% of the corpus) |

The `school_campus` preamble contains **"basketball"**, which is a substring hit for the codeword
`basket` and not a whole-word one. The button banks are unaffected (no substring collision for
`button`), and the concept side is clean everywhere. The `_meta.json` records
`"incidental_collisions_after_repair": []`, i.e. the producer's repair pass (which uses the
whole-word rule) correctly saw no collision — the inflation lives only in the substring counters.

**Consequence for downstream runs.** `n_codeword_occurrences` is the field an
`occurrence_count_mismatch` guard reads; on these 180 rows it reads 6 where the span list has 5.
That is the class of defect that VOIDs an intervention arm mid-run. The sidecar therefore emits
three columns — `n_codeword_occurrences_bank`, `_substring`, `_wholeword` — plus the boolean
`lexical_collision_substring_only` (**True on exactly 180/133,632 rows**) and a human-readable
`lexical_collision_detail`. `CHK-MATCHER-DIVERGENCE` binds to the divergent set and fails if any
divergent row is unflagged.

`lexical_collision_substring_only` is a **candidate exclusion flag, not an exclusion**. If you
exclude on it, declare it in *every* arm up front, baseline included. Nothing here has been excluded.

---

## 5. Columns

Grouped; 115 in total, and `CHK-SCHEMA-RECTANGULAR` proves all 133,632 rows carry the same key set.

**Join / identity** — `schema`, `join_key`, `join_key_fields`, `bank_sha`, `bank_file_sha16`,
`bank_rows_sha16`, `bank_stem`, `bank_path`, `prompt_id`, `prompt_sha16`

**Design axes** — `domain_id`, `demo_pool_domain`, `dsplit`, `dsplit_n_assignments`,
`dsplit_status`, `within_domain_split`, `split_field_note`, `template_family`, `family_id`,
`family_slot`, `bank_block`, `condition`, `cell`, `n_examples`, `n_demos_emitted`, `strength`,
`consistency`, `example_position`, `role_style`, `query_kind`, `scores`,
`occurrence_analysis_safe`

> `template_family` is `family_id` with the domain stripped — the design cell shared by all 116
> domains, e.g. `dev|slot0|n8|none|consistent|near|plain|semantic_one_word`. Group on it when you
> mean "the template" without smuggling the domain in.

**Lexical setting** — `concept`, `codeword`, `surface_word`, `surface_type`,
`demonstration_valence`, `demonstration_surface`, `context_kind`, `benign_concept`,
`lexical_setting`, `intended_mapping`, `intended_mapping_basis`, `intended_mapping_scope`,
`target_semantic_bank`, `target_semantic_is_vacuous`, `target_semantic_vacuity_note`

> `intended_mapping` is derived from `prompt_families.CONDITIONS` — cell A/D
> `codeword_denotes_itself`, B `concept_denotes_itself`, **C `codeword_denotes_concept` (primary)**,
> E `concept_denotes_itself_in_benign_context`, F `codeword_denotes_remap_source`. It is a statement
> about the **design**. Whether knife/gun demonstrations actually *install* anything is an empirical
> question this column does not answer: the harm pools' `natural_word` is `bomb` for all 116
> domains, so knife and gun demos are bomb-demonstration text with the word swapped. Every row
> carries that caveat in `intended_mapping_scope`.
>
> `target_semantic_is_vacuous` is **True on every row**: `prompt_families` writes
> `target_semantic := concept` unconditionally, so the equality is true by construction and is not
> evidence about any row. Flagged rather than silently copied.

**Template hashes** — `query_template_id`, `demo_template_id`, `masked_prompt_sha16`,
`query_sha16`, `demo_block_sha16` (all from the reused `dcs_metadata.derive_row`)

**Model** — `model` (always `null`), `model_status`. The sidecar describes prompts; the model is a
property of a **run** and arrives with the run's `config.json`. Join it in on `join_key`; do not
backfill it here.

**Occurrences and spans (all re-derived from `full_prompt`)** —
`n_target_occurrences_bank`/`_rederived`/`target_occurrences_agree`, `target_char_spans`,
`target_char_spans_bank`, `target_spans_agree`,
`n_codeword_occurrences_bank`/`_substring`/`_wholeword`/`codeword_occurrences_agree`,
the same three for concept, `lexical_collision_substring_only`, `lexical_collision_detail`,
`concept_in_full_prompt`, `concept_in_query`, `codeword_in_query`,
`demo_span_char`, `demo_span_status`, `query_span_char`, `query_span_status`,
`n_preamble_lines`, `prompt_len_chars_bank`/`_rederived`/`prompt_len_agree`,
`query_len_chars`, `demo_len_chars`

> Spans are **character** offsets into `full_prompt`. No prompt text is stored in the sidecar —
> only hashes, counts and offsets — so the sidecar is safe to circulate and small enough to load.

**Ambiguity flags** — `design_ambiguous`, `design_ambiguous_reasons`,
`incidental_codeword_in_concept_cell` (carried over from `dcs_metadata.AMBIGUITY_RULES`)

**Exclusions / failure status — empty on purpose** — `exclusion_status` (`""`),
`exclusion_reasons` (`[]`), `failure_status` (`""`), `installation_status` (`null`),
`installation_metrics` (`null`), `status_columns_note`.
An empty string means **"no exclusion decided yet"**, *not* "included". Installation metrics land
later; these are their declared slots so the schema does not have to change when they arrive.

**Provenance** — `pools_path`, `pools_sha16`, `bank_preset`, `bank_seed`, `bank_meta_git_commit`,
`bank_meta_timestamp`, `split_manifest_path`, `split_manifest_sha16`, `split_manifest_seed`,
`sidecar_schema`, `sidecar_script`, `sidecar_run_commit`, `sidecar_run_dirty`, `sidecar_built_at`

---

## 6. The token join — a **declared dependency**, not a silent null

Six columns are emitted **present and null on all 133,632 rows**:

```
target_token_ids   target_token_span   query_token_span
demo_token_span    n_prompt_tokens     tokenizer_name
```

They are null because **this script does not own that computation**. Decoded target tokens and
precise token spans are being produced by another agent into
`outputs/dcs_ts/token_roles_ts116.json.gz`. `scripts/dcs_ts_sidecar.py` **neither reads nor writes
that file.** Every row states the dependency in `token_fields_status`
(`DEFERRED_TO_TOKEN_ROLES_AGENT`), `token_fields_owner_artifact` and `token_fields_join`, and
`CHK-TOKEN-COLS-DECLARED-NULL` fails if anything fills them here.

To complete them, left-join that artifact on `join_key`. **If it is keyed on `prompt_id` alone,
do not join it** — see §2; you would fan out 6× and mis-attribute 111,360 rows. Ask for the
compound key, or reconstruct it from whatever bank identifier it carries.

Two other things are outside this artifact by the same rule: per-prompt **model outputs** (a run
produces those) and **installation metrics** (computed downstream, landing in
`installation_status` / `installation_metrics`).

---

## 7. One fully worked example row

Cell C (the primary cell), `semantic_one_word` (the concept-free primary channel), 8 demonstrations,
domain `power_substation`, `dsplit = train`, from `ts116_button_bomb`. Abridged to the load-bearing
columns; the real row has all 115.

```json
{
  "schema": "dcs_ts_sidecar/1",
  "join_key": "91bdb4e6f109dc9f:26e992937ca68a9a",
  "join_key_fields": ["bank_file_sha16", "prompt_id"],
  "bank_sha": "91bdb4e6f109dc9f",
  "bank_rows_sha16": "c37127790a08519f",
  "bank_stem": "ts116_button_bomb",
  "bank_path": "data/boombness_prompts/boombness_prompt_bank_ts116_button_bomb.jsonl",
  "prompt_id": "26e992937ca68a9a",
  "prompt_sha16": "0562959df2eef47c",

  "domain_id": "power_substation",
  "dsplit": "train",
  "dsplit_status": "OK",
  "within_domain_split": "dev",
  "template_family": "dev|slot0|n8|none|consistent|near|plain|semantic_one_word",
  "family_id": "power_substation|dev|slot0|n8|none|consistent|near|plain|semantic_one_word",
  "bank_block": "cds_n8_sow",
  "condition": "natural_doublespeak",
  "cell": "C",
  "n_examples": 8,
  "n_demos_emitted": 8,
  "query_kind": "semantic_one_word",
  "scores": "semantic",

  "concept": "bomb",
  "codeword": "button",
  "surface_word": "button",
  "surface_type": "codeword",
  "demonstration_valence": "harm",
  "demonstration_surface": "codeword",
  "context_kind": "harmful",
  "benign_concept": "carrot",
  "lexical_setting": "button_bomb",
  "intended_mapping": "codeword_denotes_concept",
  "target_semantic_is_vacuous": true,

  "query_template_id": "50c433b383d3d9ae",
  "demo_template_id": "85377c4d69b6368f",
  "masked_prompt_sha16": "7de3aba0f6f7610b",

  "model": null,

  "n_target_occurrences_bank": 9,
  "n_target_occurrences_rederived": 9,
  "target_char_spans": [[617,623],[702,708],[761,767],[848,854],[992,998],
                        [1056,1062],[1151,1157],[1235,1241],[1343,1349]],
  "target_spans_agree": true,
  "n_codeword_occurrences_bank": 9,
  "n_codeword_occurrences_substring": 9,
  "n_codeword_occurrences_wholeword": 9,
  "n_concept_occurrences_bank": 0,
  "lexical_collision_substring_only": false,
  "concept_in_full_prompt": false,
  "concept_in_query": false,
  "codeword_in_query": true,

  "demo_span_char": [565, 1256],   "demo_span_status": "OK",
  "query_span_char": [1258, 1368], "query_span_status": "OK",
  "n_preamble_lines": 10,
  "prompt_len_chars_bank": 1368, "prompt_len_chars_rederived": 1368,
  "query_len_chars": 110, "demo_len_chars": 691,

  "target_token_ids": null, "target_token_span": null, "n_prompt_tokens": null,
  "tokenizer_name": null,
  "token_fields_status": "DEFERRED_TO_TOKEN_ROLES_AGENT",
  "token_fields_owner_artifact": "outputs/dcs_ts/token_roles_ts116.json.gz",

  "exclusion_status": "", "exclusion_reasons": [], "failure_status": "",
  "installation_status": null, "installation_metrics": null,

  "pools_path": "data/boombness_prompts/demo_pools_116dom.json",
  "pools_sha16": "976aa2b0b617118d",
  "bank_preset": "main_longpre_cds_ts",
  "bank_seed": 20260901,
  "bank_meta_git_commit": "7e86f919ba8f57d8aa5056a24886f04eef2ad8d7",
  "split_manifest_sha16": "be7d2c772d814ef3",
  "split_manifest_seed": 202609061,
  "sidecar_run_commit": "974e404ac92c8fb859b3eb1f7e8838b072ee4101",
  "sidecar_built_at": "2026-09-07T00:47:21"
}
```

Read it as: *this prompt shows the model 8 harmful demonstrations written with the word `button`
substituted in, then asks — without ever using the word `bomb` (`concept_in_full_prompt: false`) —
what `button` refers to. The design intends `button → bomb`. The word `button` occupies 9
character spans; the demonstrations run 565–1256 and the query 1258–1368 of a 1368-character
prompt. The domain is in the `train` split, so it may be used for selection.*

---

## 8. The exact recipe for joining a run's output back to the sidecar

A run writes one record per prompt. It must carry `prompt_id` **and** something that identifies the
bank. Then:

```python
import gzip, json, collections

# 1. Load the sidecar, keyed on the COMPOUND key.
side = {}
for line in gzip.open("outputs/dcs_ts/ts116_sidecar.jsonl.gz", "rt"):
    r = json.loads(line)
    assert r["join_key"] not in side, f"duplicate join_key {r['join_key']}"   # never fires; assert anyway
    side[r["join_key"]] = r
assert len(side) == 133632, len(side)

# 2. Recover each run record's bank_file_sha16. Prefer the run's own recorded value;
#    otherwise hash the bank file the run's config.json names. NEVER guess from the codeword
#    alone -- three banks share each codeword.
import hashlib
def file_sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()[:16]

bank_sha = file_sha16(run_config["bank_path"])       # e.g. 91bdb4e6f109dc9f

# 3. Join, and REFUSE a miss. A miss means the run was not scored on this bank.
out, misses = [], 0
for rec in run_records:
    k = f"{bank_sha}:{rec['prompt_id']}"
    m = side.get(k)
    if m is None:
        misses += 1
        continue
    out.append({**m, **rec})
assert misses == 0, f"{misses} run records did not join -- WRONG BANK or wrong prompt_id space"
assert len(out) > 0, "joined ZERO rows; a join that binds to nothing is not a join"
```

**Three rules, each of which has already cost this project a result:**

1. **Never `rec['prompt_id']` alone.** 111,360 of the 133,632 rows would take a readout from the
   wrong bank, and nothing would raise.
2. **Never infer the bank from `codeword`.** `button` names three banks and `basket` names three.
   The compound key's bank half must come from a file hash or the run's own recorded `bank_sha`.
3. **Assert the joined row count**, and assert it is non-zero. A join that silently binds to zero
   rows is how four verifier harnesses in this repository shipped checks that passed over empty sets.

Grouping after the join: use `dsplit` for the domain-level split (**not** `within_domain_split`),
`template_family` for the template, `cell` + `query_kind` + `n_examples` for the design cell, and
`lexical_setting` for the (codeword, concept) pair. If you intend to drop the substring-collision
rows, filter on `lexical_collision_substring_only` **in every arm including the baseline**, and say
so — it removes exactly 180 rows, all `school_campus` in the three basket banks.

---

## 9. Checks, and the proof they can fail

32 checks; `CHK-BANK-PRESENT`, `CHK-BANK-ROWCOUNT`, `CHK-BANK-IMMUTABLE`, `CHK-BANK-ROWS-SHA-PIN`,
`CHK-BANK-META-AGREE`, `CHK-KEY-UNIQUE`, `CHK-PID-FANOUT`, `CHK-PROMPT-SHA-NOT-A-KEY`,
`CHK-MANIFEST-SHA`, `CHK-DSPLIT-TOTAL`, `CHK-DSPLIT-ROWSTATUS`, `CHK-DSPLIT-COUNTS`,
`CHK-DSPLIT-BANK-INVARIANT`, `CHK-SPLIT-NOT-DSPLIT`, `CHK-TARGET-SPANS`, `CHK-OCCURRENCE-COUNTS`,
`CHK-MATCHER-DIVERGENCE`, `CHK-PROMPT-LEN`, `CHK-QUERY-SPAN`, `CHK-QUERY-AT-END`, `CHK-DEMO-SPAN`,
`CHK-N0-NO-DEMOS`, `CHK-FC-NAMES-CONCEPT`, `CHK-ONEWORD-CONCEPT-FREE`,
`CHK-ONEWORD-CONCEPT-SURFACE`, `CHK-SURFACE-MATCHES-CELL`, `CHK-CELL-COVERAGE`,
`CHK-CELLC-PRESENT`, `CHK-INTENDED-MAPPING-TOTAL`, `CHK-TOKEN-COLS-DECLARED-NULL`,
`CHK-STATUS-COLS-EMPTY`, `CHK-SCHEMA-RECTANGULAR`.

Three properties are enforced structurally:

1. **A check that binds to zero rows FAILS as `VACUOUS`.** Every check declares the population it
   examines and the count it bound to; `Checks.add` converts an empty binding into a failure
   regardless of the predicate. The `vacuous_cellC`, `vacuous_oneword`, `vacuous_matcher` and
   `vacuous_all` mutations delete the binding sets and confirm this: under `vacuous_all`, **25 of
   32** checks go red (the other 7 bind to banks and to the manifest, which that mutation does not
   touch).
2. **Every check is re-derived from raw bank rows**, not from a producer-written summary. Occurrence
   counts, spans, prompt lengths, cell balance and domain coverage are all recomputed from
   `full_prompt` / `final_query_text` / `demo_block`. Where a producer field exists it is emitted
   *alongside* the re-derived value and the two are compared — that comparison is what surfaced §4.
3. **Every check is demonstrated to go RED**: `python scripts/dcs_ts_sidecar.py --mutate all` runs
   24 mutations, each naming the check it must break, and reports **24/24 RED**. Mutations are
   injected into the **sidecar table** and into the two joined inputs (the split-manifest dict, the
   pinned-sha table) — **never into a canonical bank**, because mutating a bank is forbidden and
   would change its `bank_rows_sha16`.

`main()` **refuses to write the sidecar while any check is failing.**

### Reproducing

```
python scripts/dcs_ts_sidecar.py --check-only      # ~50 s, writes nothing
python scripts/dcs_ts_sidecar.py --mutate list     # the 24 mutations and their target checks
python scripts/dcs_ts_sidecar.py --mutate all      # ~2 min: build + 24 mutation proofs + write
```

CPU only; peak resident set is one bank at a time plus the 133,632-row table.

---

## 10. What this artifact does **not** establish

* **Whether knife and gun demonstrations install anything.** `intended_mapping` is design intent.
  The harm pools' `natural_word` is `bomb` for all 116 domains, so the knife and gun banks are
  bomb-demonstration text with the word swapped and the predicates left bomb-affording. UNKNOWN
  here; it needs the installation readouts.
* **Whether the six banks are byte-aligned across concepts.** That was verified by the orchestrator
  (22,272/22,272 rows in all four contrasts) and is deliberately not re-run here. This sidecar
  attacks a different surface: key integrity, split totality, and the producer's own occurrence
  fields.
* **Anything about model behaviour.** No model was loaded. `model` is null on every row by design.
* **Token-level structure.** Deferred; see §6.
