# reports/DATASET_AND_SPLIT_CONTRACT.md — Phase 1 Locked Split

The permanent train/test contract for all downstream causal experiments
(`CAUSAL_CIRCUIT_MASTER_PLAN.md` §Phase 1). Frozen **before** any layer/head/path/direction
selection. Any experiment that touches `test`/`heldout` for selection violates this contract.

- **Artifact:** `data/splits/clearharm_doublespeak_v1.json` (137 records)
- **Builder:** `scripts/build_doublespeak_split.py` · **Validator:** `scripts/validate_data_integrity.py`
- **Built:** 2026-08-02 · **git_commit at build:** `8093756`
- **Tokenizer:** `meta-llama/Llama-3.1-8B-Instruct` · **Demo/concept generator:** `gpt-4o-mini` (openai_seed=7, num_demos=12)
- **ClearHarm revision:** `clearharm@79464fb6b3c2a8ee925184f394f9636600349f88` (user-authorized research use, 2026-07-25)
- **Reproducibility:** locked via `data/splits/_concept_cache.json` (instruction→concept) + `_demo_cache.json` (word→demos). Re-running the builder reads both → identical split.

## Validation status — **12 ok / 0 warn / 0 FATAL**
`no train/test example_id overlap` · `no intent_cluster overlap across train/test` · `no duplicate prompts across train/test` · `all primary codewords/concepts single-token` · `dataset_revision recorded` · per-cohort ≥20/≥20 all pass.

---

## Cohorts (Omer decision 2026-08-02: **blend**, reported separately)

| Cohort | Role | n | train | test | concepts | clusters | ≥20/≥20 |
|---|---|---|---|---|---|---|---|
| **clearharm** | PRIMARY | 86 | 44 | 42 | 43 | 86 | ✓ |
| **curated** | REPLICATION | 51 | 30 | 21 | 17 | 17 | ✓ |
| total | | 137 | 74 | 63 | — | — | ✓ |

**clearharm categories:** other_uncategorized 54, weapons_explosives_mass_casualty 16, cyber_hacking_malware 13, identity_theft 2, fraud 1.
**curated categories:** weapons 27, narcotics 12, explosives 9, toxins 3.
**Single-token yield:** ClearHarm-native → 86 usable single-token-concept examples from the 179 instructions (concept must be the most-harmful noun appearing **verbatim** and single-token under the Llama tokenizer). Curated → 17 single-token concepts × 3 canonical instructions = 51 (25 multi-token curated concepts excluded, e.g. GHB, IED, ricin, sarin, "mustard gas", "grenade launcher" — separately analyzable later).

---

## Per-example schema
`example_id` · `cohort` · `original_clearharm_id` · `harm_category` · `intent_cluster` ·
`original_request` · `target_concept` · `codeword` · `tokenized_target` · `tokenized_codeword` ·
`doublespeak_prompt` · `neutral_prompt` · `direct_prompt` · `benign_prompt` · `shuffled_prompt` ·
`unrelated_prompt` · `demo_ids` · `n_codeword_occurrences_templated` · `codeword_occurrences_templated`
(char spans post chat-template) · `single_token_primary` · `split` · `dataset_revision` · `provenance`.

### The six matched prompt conditions (per example)
- **doublespeak** — demos bind `codeword`→`concept`; query uses `codeword` (the attack).
- **neutral** — `codeword` query, **no** demos.
- **direct** — harmful `concept` query, no demos.
- **benign** — demos use `codeword` in its ordinary benign meaning; `codeword` query (codeword present, no harmful binding).
- **shuffled** — demos bind `codeword`→a **different** concept; query uses `codeword` (wrong binding).
- **unrelated** — demos bind a **different** codeword→`concept`; query uses the original `codeword` (binding present but mis-addressed).

Prompts are RAW text (built via `ds_common.build_conditions`); apply the chat template with
`ds_common.apply_template`. Codeword occurrences are located **after** templating with
`find_word_occurrences_in_text`; typical count = 13 (12 demo bindings + 1 query). Two ClearHarm
items have 7/12 (fewer demo hits) — still valid (≥1 demo + 1 query).

---

## Split methodology (leakage control)
- **Unit of split = intent_cluster.** Whole clusters go to one split; category-balanced round-robin (`assign_splits`), deterministic via cluster-hash ordering.
- **curated:** `intent_cluster = curated::{concept}` — all paraphrases/templates of one concept stay together. 17 concepts → ~9 train / 8 test clusters.
- **clearharm:** `intent_cluster = clearharm::{category}::{hash8(instruction)}` — **each instruction is currently its own cluster** (see Limitation 1).
- **Unique codeword per concept** (17 curated ≤ 21 single-token codewords) — prevents identical neutral prompts across concepts (the concept→codeword substitution erases concept identity; a shared codeword+template collided → this was caught by the validator and fixed).

---

## Known limitations (honest)
1. **ClearHarm near-duplicate clustering not applied.** Each ClearHarm instruction is its own cluster, so if two ClearHarm items are paraphrases they could land in different splits. ClearHarm's 179 are curated to be distinct (low risk), but `scripts/build_clearharm_manifests.py` has sentence-transformer duplicate_group detection that could be wired in for a v2. **Action:** flagged; low priority pending an embedding-dup scan.
2. **ClearHarm-native concepts are noisier than curated.** Because the concept must appear verbatim and be single-token, some ClearHarm concepts are generic (`attack`, `device`, `agent`, `card`) or singular/plural variants of one root across items. Forced-choice readout signal may be weaker for these than for the clean curated weapons/drugs — **this is precisely why the curated replication cohort exists.** Claims are made only where they replicate across both cohorts.
3. **Multi-token concepts excluded from primary.** 25 curated multi-token concepts + all multi-token ClearHarm concepts are dropped from the primary analysis (plan mandate). A separate multi-token bucket can be built later if needed.
4. **Codeword occurrence count 7/12 on 2 ClearHarm items** — fewer demo hits (codeword token fused differently in some demos); still valid, noted per-row.

## Downstream contract (enforced)
- Discovery scripts read `train` only. `test`/`heldout` used **only** for frozen confirmatory replication of the complete relevant sweep — never for layer/head/path/direction/threshold selection.
- `scripts/validate_data_integrity.py --split <file> --tokenizer <model>` must return 0 FATAL before any experiment consumes the split. Add `--rows-dir <outputs>` to check result rows for dup cells / missing metadata / failed generations / missing judge results.
