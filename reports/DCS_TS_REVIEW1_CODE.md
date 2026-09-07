# DCS thesis-scale — REVIEW 1, LENS A: CODE REVIEW

Mandate §29A. Range reviewed: `b80db84d..e4d78bf0` (9 commits, 44 files, +31,019/−4).
Reviewer read the diffs and re-ran read-only measurements against the on-disk artifacts.
Python for measurement: `/home/sharifm/students/omeryosef/miniconda3/envs/poc_stage2/bin/python`.

**Working-tree caveat, stated first because it changes what "HEAD" means.** At review time four of
the reviewed scripts carry uncommitted edits (`git status`): `scripts/dcs_ts_build_ts116n.sh`,
`scripts/dcs_ts_gen_concept_harm_pools.py`, `scripts/dcs_ts_length_match_pools.py`,
`scripts/dcs_ts_verify_ts116n.py` (+95/−14 vs HEAD; the `BANK_TAG`/`POOLS_TAG` parameterisation and
the C-079 case-form filter). Findings below are cited at the line numbers of the **working tree**
where the two differ, and the divergence is itself recorded as MINOR-14.

Also present and untracked: all six `ts116m` banks (`boombness_prompt_bank_ts116m_*.jsonl`,
12 files) and all six `ts116` (VOID) bank rows. No GPU job has run; no hidden state exists.

---

## Summary of findings

| # | Rank | One line |
|---|---|---|
| CRIT-1 | CRITICAL | The FROZEN preregistration pins `ts116n`; the phase has already built `ts116m` |
| CRIT-2 | CRITICAL | The analyzer that "refuses to run on null shas" does not exist |
| CRIT-3 | CRITICAL | The mandatory GPU preflight verifies the VOID `ts116` banks, never `ts116n`/`ts116m` |
| MAJ-1 | MAJOR | `dcs_ts_build_banks.sh` still live and unmarked; two committed scripts pin VOID row hashes |
| MAJ-2 | MAJOR | The zero-dose null is 50 % duplicate rows; the preset comment claims they are dropped |
| MAJ-3 | MAJOR | Seed `20260906` collision re-introduced by this phase's own generator |
| MAJ-4 | MAJOR | The `restaurant_kitchen` "second seed" was not a second draw — 13 of 14 seeds reused |
| MAJ-5 | MAJOR | `gen_concept_harm_pools.verify()` is strictly weaker than the filter it verifies |
| MAJ-6 | MAJOR | `BOOMB_EXPECT` does not close the 853040 hole it was written for |
| MAJ-7 | MAJOR | Two different read sites are frozen in two artifacts (`codeword_last` vs `rel_end −9`) |
| MIN-1..14 | MINOR | see below |

**Checked and found clean** (stated so the absence is on the record, not an omission):
splits (item 3) and joins (item 4). Details in "Checks that passed".

---

# CRITICAL

## CRIT-1 — the FROZEN preregistration names a bank family the phase has already superseded

`configs/dcs_ts_pr046.json`:
- `.status = "FROZEN"`, `.frozen_at = "2026-09-07"`
- `.population.bank_family = "ts116n"`
- `.population.banks.button_bomb.bank_file_sha16 = "42341368bdbe6ebc"` (and five siblings)
- `.population.pools.harm_bomb.path = data/boombness_prompts/demo_pools_116dom_ts_bomb.json`

Measured on disk:

```
sha256(boombness_prompt_bank_ts116n_button_bomb.jsonl)[:16] = 42341368bdbe6ebc   <- what is pinned
sha256(boombness_prompt_bank_ts116m_button_bomb.jsonl)[:16] = dcd92d723f3e6d00   <- what exists now
```

All six `ts116m` banks exist (`ls data/boombness_prompts/ | grep ts116m` → 12 files, 6 jsonl +
6 meta). `ts116m` is the family that carries the C-076 inflection filter and the C-077 length
matching — i.e. the two defects the phase itself declared disqualifying. The frozen config pins the
family that still has them, and names none of the `demo_pools_116dom_tsm_*.json` pools that
`scripts/dcs_ts_length_match_pools.py:59` writes.

**Failure scenario.** Extraction is submitted against `ts116m` (the corrected banks). The analyzer,
when written, loads `configs/dcs_ts_pr046.json`, computes `bank_file_sha16` of the extracted bank,
gets `dcd92d723f3e6d00`, compares against the pinned `42341368bdbe6ebc`, and either (a) refuses —
blocking the run for the correct reason but with no path forward, or (b) is "unblocked" by editing
the frozen file after the gates have been seen, which voids the freeze. The third branch — extract
against `ts116n` because that is what the config says — runs the flagship probe on a corpus with a
known plural leak (30 of 3680 primary rows, 4 in TEST) and a known length confound
(N4 = 0.4174 acc / 0.5750 AUROC, z = +6.62).

The same stale default is compiled into the gate runner: `scripts/dcs_ts_verify_ts116n.py:79-80`
defaults `BANK_TAG=ts116n`, `POOLS_TAG=ts`, so `python3 scripts/dcs_ts_verify_ts116n.py` with no
environment gates the superseded family and prints `19/19 gates pass` for it.

*What would resolve it:* a decision, recorded before any extraction, on which family is the
population, and a re-freeze of PR-046 against that family's six shas — or an explicit
supersession entry. I cannot make that decision from the code; UNKNOWN which is intended.

## CRIT-2 — the analyzer that enforces every preregistered threshold does not exist

`configs/dcs_ts_pr046.json`:
- `.artifacts.analyzer = "scripts/dcs_ts_pr046_analysis.py"`
- `.artifacts.analyzer_commit = null`

```
$ ls scripts/dcs_ts_pr046_analysis.py
ls: cannot access 'scripts/dcs_ts_pr046_analysis.py': No such file or directory
```

The authoritative log makes the enforcement claim explicitly
(`external_md/DCS_THESIS_SCALE_BOMBNESS_CAUSAL_CONFIRMATION_PLAN_AND_PROGRESS_20260906.md:1016-1023`):

> every `*_sha` field is `null` and the analyzer **refuses to run** while any of them still is …
> the analyzer refuses to start if the file is missing, if a sha is null, or if a gate it needs is
> absent. *A number in a markdown log that no program consults is a wish, not a preregistration.*

Answering the brief's item 6 directly: **the refusal code does not exist yet; it is promised, not
written.** Grepping every consumer of the config file finds exactly two, and neither enforces a
threshold:

```
scripts/dcs_ts116n_audit_leakage.py:56,64        reads the preregistered exclusion list only
scripts/dcs_ts116n_audit_concept_backing.py:63,1105-1115  reads population.banks.*.bank_file_sha16 (CHK-21)
scripts/dcs_ts_verify_ts116n.py:71               mentions the config in a comment; reads nothing
scripts/dcs_ts_length_match_pools.py:7           quotes the deferred_decision_rule in a docstring
```

Every other number in the file — `.primary.alpha`, `.primary.n_perm = 10000`, the p-floor rule,
`.power.mde_accuracy_delta = 0.0925`, `.power.flip_trigger.rule`, `.read_site.layer_grid`,
`.classifier.C_grid`, `.nulls_required` (8 entries), `.phase4_gates_on_ts116n` (5 entries) — is
read by no code path. Two of the five gates named in `.phase4_gates_on_ts116n` are additionally
described by prose only.

**Failure scenario.** This is the repository's own recorded, twice-realised failure mode
(the log's own sentence above; and `feedback_published_threshold_never_enforced`). The concrete
version here: the p-floor rule and the `n_perm = 10000` value live only in JSON, so the first
analysis script written under time pressure uses `n_perm = 1000`, prints `p = 0.001`, and nothing
compares that to the floor `9.999e-05` the config declares. Status of the claim as of `e4d78bf0`:
**not enforced anywhere.**

## CRIT-3 — the mandatory pre-submission preflight gates the VOID bank family

`scripts/dcs_ts_preflight.sh:86-88`:

```bash
echo "[4] frozen artifacts"
if bash scripts/dcs_ts_build_banks.sh check >/dev/null 2>&1; then note OK "6/6 ts116 banks match bank_rows_sha16"
else note FAIL "ts116 bank drift or missing -- run: bash scripts/dcs_ts_build_banks.sh build"; fi
```

`scripts/dcs_ts_build_banks.sh:60` builds/checks
`boombness_prompt_bank_ts116_${cw}_${cc}.jsonl` — the family `DCS-C-074` declared VOID
(`scripts/dcs_ts_build_ts116n.sh:6-10`). The script's own header, line 2, is the one every
submission in the phase is supposed to run first: *"Run this BEFORE every sbatch in this phase.
Exit 0 means it is safe to submit."*

**Two concrete failures, in opposite directions.**
1. Extraction is submitted against `ts116n`/`ts116m`. Preflight prints
   `OK 6/6 ts116 banks match bank_rows_sha16` and exits 0. **The banks that will actually be read
   were never checked.** A drifted or half-rebuilt `ts116m` bank passes the gate.
2. The VOID `ts116` rows are deleted — which is the correct hygiene action, and they are currently
   only untracked working-tree files — and `dcs_ts_build_banks.sh check` then fails on six missing
   files. Preflight prints `=== PREFLIGHT FAIL -- do not submit ===` and exits 1, blocking every
   GPU submission in the phase for a bank nothing uses. The remediation it prints
   (`run: bash scripts/dcs_ts_build_banks.sh build`) instructs the operator to **regenerate the
   void banks**.

---

# MAJOR

## MAJ-1 — the VOID build path is still live and unmarked, and two committed scripts pin its hashes

`scripts/dcs_ts_build_banks.sh` is committed at HEAD, carries no VOID marker anywhere in its 91
lines, and `MODE="${1:-build}"` (`:56`) means the **default** invocation
`bash scripts/dcs_ts_build_banks.sh` regenerates six void banks into `data/boombness_prompts/`.
Its header (`:26-32`) still advertises `22272/22272 aligned` as VERIFIED OUTPUT — the exact
alignment statistic C-074 showed to be vacuous — and `:40-47` still describes the word-swap design
as the accepted design.

Two more committed scripts hardcode R-098's void row hashes as the thing to verify against:

- `scripts/dcs_ts_sidecar.py:85-97` — `TS_BANKS = ("ts116_button_bomb", …)` and
  `EXPECTED_ROWS_SHA16 = {"ts116_button_bomb": "c37127790a08519f", …}`, with the comment
  *"the sidecar refuses to describe a bank that is not the one the sprint recorded"*.
- `scripts/dcs_ts_token_roles.py:58,69-73` — `BANK_TMPL = "boombness_prompt_bank_ts116_{cw}_{cc}.jsonl"`,
  same six hashes, output `outputs/dcs_ts/token_roles_ts116.json.gz`.
- `scripts/dcs_ts_power.py:70` — `boombness_prompt_bank_ts116_{codeword}_{concept}.jsonl`.

**Failure scenario.** The sidecar is the declared landing table for the analysis join
(`scripts/dcs_ts_sidecar.py:328-331`, `join_key = f"{bank_file_sha16}:{prompt_id}"`). Run as
committed it emits `outputs/dcs_ts/ts116_sidecar.jsonl.gz` describing the void banks, and its
`bank_file_sha16` column then carries void shas. Any later join of extraction rows (from `ts116m`)
against that sidecar on `(bank_file_sha16, prompt_id)` matches **zero** rows — which is the benign
outcome. The malign one: the sidecar's pin is a *hard refusal*, so an operator who "fixes" it by
editing `EXPECTED_ROWS_SHA16` re-points a verifier at whatever is on disk, and the pin stops being
a pin.

`scripts/dcs_ts_power.py` reading the void banks is the least severe of the four: the power numbers
frozen into `.power.*` depend on the domain roster and rows-per-domain, which are identical across
`ts116`/`ts116n`/`ts116m` (measured: 1160 primary rows = 116 domains × 10 in both `ts116n` and
`ts116m`). The numbers survive; the provenance string does not.

## MAJ-2 — the zero-dose null carries 1,392 duplicate prompts per bank, and the preset comment says it does not

`src/boombness/prompt_families.py`, the new `main_longpre_cds_ts` preset, states:

> The zero-dose block uses `slots=[0]` because with no demonstrations every slot yields the same
> text; the remaining duplicates across `splits` are dropped by `generate_bank` and counted in
> `stats["n_duplicate_prompt_id_rows_dropped"]` rather than silently deduped.

Measured on `data/boombness_prompts/boombness_prompt_bank_ts116n_button_bomb.jsonl`:

```
n0 rows                 2784
n0 distinct full_prompt 1392        <- every zero-dose prompt appears exactly twice
n0 by split             dev 1392 / heldout 1392
```

and from `boombness_prompt_bank_ts116n_button_bomb_meta.json`:

```
n_duplicate_prompt_id_rows_dropped = 0
duplicate_drops_by_condition       = {}
```

The dedup never fired. `prompt_id = sha(family_id|condition)` and `family_id` carries the
within-domain `split`, so the dev and heldout copies of a zero-demonstration prompt have identical
text and **different** `prompt_id`s. `generate_bank` deduplicates on `prompt_id`, so it cannot see
them. Identical in `ts116m` (2784 / 1392).

**Failure scenario.** The zero-dose cell is the design's sharpest null — *"a probe that still
separates {bomb, knife, gun} is reading the bank, not the model"*. Run as built, every row in it is
present twice. Any row-level statistic over the null reports n = 2784 where the honest n is 1392,
halving the standard error of the null while the row count looks healthy; a per-row bootstrap or
permutation over the null is anticonservative by exactly that factor. And 1,392 duplicate prompts
× 6 banks = **8,352 redundant forward passes** of a 196–280-token prompt through Llama-3.1-8B, paid
for in GPU time for zero information. The comment asserting the opposite is the reason nobody would
look.

## MAJ-3 — the seed collision the phase documented avoiding was re-introduced by the phase's own generator

`scripts/dcs_ts_split_manifest.py:37-40` is explicit:

> SEED. 202609061, not 20260906. The bare date is already `POWER_SEED` in
> `scripts/dcs_pr042_mediation.py:142` … reusing it would make two unrelated randomisations share a
> stream and make any "same seed" assertion ambiguous.

The same commit range then ships:

- `scripts/dcs_ts_gen_concept_harm_pools.py:316` — `ap.add_argument("--seed", type=int, default=20260906)`
- `src/boombness/slurm/run_ts_harm_pools.sh:31` — `: "${TSH_SEED:=20260906}"`
- `configs/dcs_ts_pr046.json` `.population.pools._seed = 20260906`

against existing live users of the identical literal:

```
scripts/dcs_pr042_mediation.py:142   POWER_SEED = 20260906
scripts/dcs_mask_overlap.py:443      ap.add_argument("--seed", ..., default=20260906)
scripts/dcs_diffmeans_directions.py:912  _synth(planted=True, seed=20260906)
scripts/dcs_verify_pr035.py:1106,1287    _fix_write(root, seed=20260906) / build_fixture(...)
```

A second collision was introduced alongside it: `20260907` is simultaneously the FPR-simulation
seed (`scripts/dcs_ts_power.py:529,699` — `section6_fpr(..., seed=20260907)`, and the CLI default)
and the `restaurant_kitchen` pool-regeneration seed (`scripts/dcs_ts_verify_ts116n.py:60`).

**Failure scenario.** The write-up says "seed 20260906" of the harm pools; a reader or a later
reproduction script resolves that to `POWER_SEED` and reruns the mediation power calculation
believing it shares a stream with corpus generation, or vice versa. Concretely: `dcs_mask_overlap.py`
run with its default seed and the harm-pool generation are now indistinguishable by seed in any
provenance table, and the manifest's own justification for `202609061` no longer holds for the
phase as a whole. The split seed is clean; nothing else new is.

## MAJ-4 — the `restaurant_kitchen` exclusion rests on a "second seed" that reused 13 of the first 14 seeds

`scripts/dcs_ts_verify_ts116n.py:54-72` justifies the one preregistered exclusion:

> Regenerating the domain at a second seed (20260907) cleaned bomb and knife and left gun
> contaminated again. **That is the domain, not the draw**, and a third bump would start to be
> selection rather than repair.

But `scripts/dcs_ts_gen_concept_harm_pools.py`, in `generate()`, retries with

```python
for rnd in range(14):
    got = gen_demos(client, model, concept, int(n_per_pool * 2), seed + rnd, style_hint=hint)
```

The base run at `--seed 20260906` therefore consumed OpenAI seeds **20260906 … 20260919**. A rerun
at `--seed 20260907` consumes **20260907 … 20260920** — **13 of its 14 seeds are seeds the first
run already used**, with the same model, the same style hint and the same concept word. It is not a
second draw; it is the first draw with its first round removed and one new round appended.

**Failure scenario.** The inference "that is the domain, not the draw" is not supported by the
evidence offered for it: an almost-identical seed sequence reproducing an almost-identical
contamination is the expected result even if the domain is perfectly fine. The exclusion may still
be correct on its face (a kitchen genuinely affords knives) — but the *replication* cited as
decisive is confounded, and it is the sentence that turns a prompt-only judgement call into a
recorded finding. To establish it properly you would need a seed disjoint from `[20260906, 20260920]`,
e.g. `--seed 20270101`.

## MAJ-5 — `gen_concept_harm_pools.verify()` is strictly weaker than the filter it exists to verify

`scripts/dcs_ts_gen_concept_harm_pools.py`. The **filter** (`_clean_strict`) enforces two conditions
and the file documents at length why both are needed (C-076 and C-079, lines 76-131):

```python
if not s or len(rx.findall(s)) != 1 or len(rx_sing.findall(s)) != 1:
```

The **verifier** (`verify()`, the `elif val == "harm"` branch) enforces only the first:

```python
rx = _forms_re(concept)                      # (?i)\b(?:bomb|bombs)\b  -- case-INSENSITIVE, all forms
for i, s in enumerate(pool.get("sentences", [])):
    n = len(rx.findall(s))
    if n != 1:
        errs.append(...)
```

There is no `rx_sing` and no `_substitutable_forms` check in `verify()`, and this is the function
that `main()` calls as the final line of a generation run (`return verify(a.out)`) and that
`--verify` exposes as the standalone check.

**Failure scenario.** A harm pool containing `"Several bombs were found in the loading bay."`
(plural-only) or `'A container marked "bOMB" was found…'` (unsubstitutable case — the file's own
C-079 example, lines 98-101) passes `--verify` with exactly one counted occurrence and prints
`[gen-harm-pools] OK: … carry exactly one whole-word 'bomb' per sentence`. `build_demo_block`
rewrites neither, the sentence survives assembly unchanged, the demonstration contributes **zero**
codeword occurrences, and the failure only surfaces later as
`prompt_families --strict` refusing the whole bank with an alignment-violation count (the file
records 170 such violations for exactly this cause). The checker's notion of an occurrence is not
the transformer's — the bug class this same file names and claims to have closed.

Two secondary holes in the same function: it never checks
`_meta["content_sha16"]` against a recomputation of `pools`, so an edited pools file verifies clean
while its recorded hash lies; and it never checks the domain count, so a pools file generated with
a truncated `--domains` (the live `sbatch --export` comma-truncation hazard, which
`run_ts_harm_pools.sh:44` is exposed to via `${TSH_DOMAINS:+--domains "$TSH_DOMAINS"}`) verifies as
OK over whatever subset it happens to contain.

## MAJ-6 — `BOOMB_EXPECT` does not close the failure it was written for

`src/boombness/slurm/run_boombness.sh:56-86` adds the guard, and its own header states the cause:

> Jobs 853040-853045 were exported `ARGSFILE=...` — a variable this runner never reads — so all six
> fell through to that default, ran the WRONG SCRIPT, and exited `COMPLETED 0:0`.

That incident had **two** mistyped variables at once. The guard covers one of them. There is no
guard on the other:

```
:87   : "${BOOMB_ARGSFILE:=}"
:88   : "${BOOMB_ARGS:=}"
:89   if [ -n "$BOOMB_ARGSFILE" ]; then ...      # entire block skipped when unset
:148  python -u "src/boombness/$BOOMB_SCRIPT" $BOOMB_ARGS
```

**Failure scenario.** The phase's own recommended submission line
(`scripts/dcs_ts_preflight.sh:118`) is
`sbatch --export=ALL,BOOMB_SCRIPT=$s,BOOMB_EXPECT=$s,BOOMB_ARGSFILE=<file>`. Mistype the third —
`ARGSFILE=` instead of `BOOMB_ARGSFILE=`, the exact typo of 853040 — and: `BOOMB_SCRIPT` is
PROVIDED, `BOOMB_EXPECT` matches, both new guards pass, the write guard passes, the GPU guard
passes, and line 148 runs **the right script with an empty argv**, falling through to every
argparse default. On `extract_boombness.py` that is a different bank, a different position and a
different layer set, written to a default output directory, exiting `COMPLETED 0:0`. Nothing in the
job distinguishes it from the intended run except the one line `args:` (`:111`), which prints empty.
A one-line `[ -z "$BOOMB_ARGS" ] && refuse` (or requiring `BOOMB_ARGSFILE` whenever `BOOMB_EXPECT`
is set) would close it.

Secondary: the guard is opt-in, so mistyping `BOOMB_EXPECT` itself (`EXPECT=`, `BOOM_EXPECT=`)
silently disables it — an opt-in guard against silent defaults inherits the property it guards
against. `scripts/dcs_ts_preflight.sh:120` mitigates by telling the operator to read the log line,
which is a human step, not a guard.

**Item 9 answered: no existing caller is broken.** Every `BOOMB_SCRIPT` value in the repository
resolves under `src/boombness/`:

```
scripts/rbd_submit_wave.sh:22        BOOMB_SCRIPT=score_behavior.py            -> exists
scripts/rah3_repro_manifest.py:65    BOOMB_SCRIPT=rah_preflight_transport.py   -> exists
(default)                            extract_boombness.py                      -> exists
reports/DCS_TS_PHASE1_BRIEFING:1248  BOOMB_SCRIPT=../../scripts/dcs_extract_under_ko.py
                                     -> src/boombness/../../scripts/dcs_extract_under_ko.py exists; `[ -f ]` resolves it
```

The `-f` test runs after `cd "$PROJECT_DIR"` (`:46`), so relative resolution is well defined. The
only theoretical break is a caller passing `BOOMB_EXPECT` and `BOOMB_SCRIPT` that differ only by a
`./` prefix, since the comparison at `:74` is a literal string equality; no such caller exists.

## MAJ-7 — two different read sites are frozen in two artifacts

`configs/dcs_ts_pr046.json`:
```
.read_site.position          = "codeword_last"
.read_site.layer_convention  = "block L == hidden_states[L+1]; hidden_states[0] == embeddings"
```

`scripts/dcs_ts_token_roles.py:84-88`:
```python
#: The read position this map NOMINATES, fixed in source before the ranking is computed:
#: one token past the final-query codeword, i.e. the repo's own `following` site
#: (ds_common.target_positions / extract_boombness position="following"), expressed as an
#: offset from the END of the sequence …
NOMINATED_REL_END = -9
```

`codeword_last` and `following` are two different token positions, one apart. The frozen
preregistration names the first; the committed token-role map nominates and gate-checks the second
(`G2_nominated_read_position_rel_end_-9`, `:569`), and the report
`reports/DCS_TS_TOKEN_ROLE_MAP.md` is the artifact a reader would consult for "where do we read".

**Failure scenario.** Extraction is run at `position=following` because the token-role map says −9
is verified; the analyzer (when written) reads `.read_site.position = "codeword_last"` from the
frozen config and either refuses, or silently accepts a column named differently, and the
published design and the executed design differ by one token. Compounding it: `NOMINATED_REL_END =
-9` was validated only against the `ts116` banks (`BANK_TMPL`, `:58`) whose cell-C prompts were
byte-identical across concepts by the C-074 defect. On `ts116n`/`ts116m` the harm demonstrations
differ per concept, so the tail is no longer trivially shared; the −9 constant has **not** been
re-derived on the corrected banks. Its checks are tail-relative, not absolute (`i = r["n_tokens"] +
NOMINATED_REL_END`, `:557`), so the offset class is correct — but the *value* is unverified on the
population that will be measured.

*Item 5 otherwise clean:* the new code uses end-relative coordinates throughout
(`rel_end`, `gen_header_pos = n - 1` at `:222`, `spans` computed from the offset mapping at
`:162-180`). No absolute position index computed from one example and reused across examples was
found in the range — the `feedback_absolute_position_index_bug` class does not appear here.

---

# MINOR

**MIN-1 — the excluded domain is still built and will still be extracted.**
`scripts/dcs_ts_build_ts116n.sh:48-56` builds all 116 domains; `restaurant_kitchen` is excluded only
downstream, in `scripts/dcs_ts_verify_ts116n.py:72` and the two audit scripts. Measured: the
`ts116n` and `ts116m` primary cell (C × `semantic_one_word` × n=4) each contain 10
`restaurant_kitchen` rows per bank, 60 across six banks, plus its share of every other cell (192
rows per bank total for that domain). Those forward passes are paid for and then discarded.

**MIN-2 — three artifacts, two train counts.**
`scripts/dcs_ts_split_manifest.py:69` `N_TRAIN = 70`, and `verify()` hard-asserts it at `:162`;
`configs/dcs_ts_pr046.json` `.split.n_train = 69`; `scripts/dcs_ts_sidecar.py:106`
`EXPECTED_DSPLIT_COUNTS = {"train": 70, …}`. The config's `_exclusion_note` explains the difference
(70 assigned, 69 analysed) and the manifest is correctly not regenerated — but any check that
compares the two numbers directly fails, and a reader gets two answers to "how big is train".

**MIN-3 — the domain count is hardcoded, not derived.**
`scripts/dcs_ts_verify_ts116n.py:73` `N_DOMAINS = 116 - len(EXCLUDED_DOMAINS)`. If the pools roster
ever changes, G2's `need 115/115` becomes a wrong constant rather than a detected drift. Deriving it
from the same pool keys `dcs_ts_split_manifest.domain_roster()` reads would make it self-correcting.

**MIN-4 — the retry loop and its own error message disagree.**
`scripts/dcs_ts_gen_concept_harm_pools.py` `generate()` loops `for rnd in range(14)`, but the
`RuntimeError` it raises says *"after 8 rounds"* and the module docstring (`:47`) says *"the same
8-round retry"*. A reader diagnosing a short pool computes the wrong number of API rounds — and it
is the number MAJ-4 turns on.

**MIN-5 — generated pool metadata records the wrong codeword.**
`scripts/dcs_ts_gen_concept_harm_pools.py`, `generate()`'s `meta` dict: `"codeword": "carrot"`,
hardcoded. The phase's codewords are `button` and `basket`; pools carry no codeword at all. Anyone
joining or filtering on `_meta["codeword"]` sees `carrot` in all three thesis-scale pools files.

**MIN-6 — the n0 row arithmetic in the build header is wrong.**
`scripts/dcs_ts_build_banks.sh:31-32`: *"the n_examples=0 null is EXACTLY byte-identical across
concepts in both concept-free channels (928 rows = 2 cells x 2 query kinds x 232)"*. The bank has
four cells at n0 (measured: A/B/C/E × 3 query kinds × 232 = 2784), so the concept-free n0 population
is 4 × 2 × 232 = 1856, not 928.

**MIN-7 — the length-match "before" baseline is a proxy, not the measured corpus.**
`scripts/dcs_ts_length_match_pools.py:142`: `before[cc] += [len(s) for s in pools[cc][:N_KEEP]]` —
the first 40 *usable candidates* from the 60-candidate file. The N4 = 0.4174 figure that fired the
trigger was measured on the `ts116n` pools, a different generation run. The printed
`cross-concept mean spread: X -> Y (Z% reduction)` therefore compares the after-state against a
reconstruction, not against the thing that was measured. The remedy is free: read the `ts116n`
pools for the "before" arm.

**MIN-8 — the "shared" quantile target is not concept-neutral.**
`scripts/dcs_ts_length_match_pools.py:143`:
`targets = _quantiles([len(s) for cc in CONCEPTS for s in pools[cc]], N_KEEP)`. The pooled
distribution weights each concept by its *usable-candidate count*, which differs across concepts
after the `usable()` filter. The docstring's claim (`:27-29`) that *"no concept's own distribution
defines the goal"* holds only when the three counts are equal. Effect is small and the direction is
unknowable without measuring; it is a stated property that is not quite true.

**MIN-9 — G1's own-concept count still misses the C-076 class.**
`scripts/dcs_ts_verify_ts116n.py`, `g1_pools()`:
```python
if len(re.findall(rf"(?i)\b{re.escape(cc)}\b", s)) != 1:   # singular only
    bad_occ.append(...)
for other in CONCEPTS:
    if other != cc and re.search(rf"(?i)\b{other}s?\b", s):  # plural-aware for OTHER concepts
```
The other-concept check is plural-aware; the own-concept check is not. A knife harm sentence
containing `knife` once and `knives` once — the exact C-076 shape, eight of which shipped — passes
G1. The generator now filters them out upstream, so G1 is redundant rather than wrong today; but
the gate that is supposed to be the last line of defence cannot detect the defect it postdates.

**MIN-10 — the incidental-collision screen misses irregular plurals (latent, not live).**
`src/boombness/prompt_families.py:1341`:
`hits = len(re.findall(rf"(?i)\b{re.escape(codeword)}s?\b", sent))`. `knifes?` does not match
`knives`. The C-072 change (this range) extended the screen from codeword to *concept*, so this
regex is now applied to `knife` — a shared benign/remap/filler sentence containing `knives` would
pass the screen, be left unrepaired, be substituted only in its singular form (if any), and
desynchronise the knife arm from bomb and gun in a *shared* pool, which is precisely the alignment
the phase depends on. Measured: `demo_pools_116dom.json` contains **0** occurrences of `bombs`,
`knives` or `guns` across all pools, so nothing is broken today. Latent.

**MIN-11 — a denominator that is not a count.**
`scripts/dcs_ts_split_manifest.py:207,211`: `n_checks = 6` is a literal, while `verify()` appends a
variable number of errors. With two failures from one check family the script prints
`2 of 6 checks FAILED`, which is not arithmetic anyone can act on. (The house rule is rows with
denominators; here the denominator is decorative.)

**MIN-12 — the C-077 trigger was fired by a number computed on the TEST partition.**
`scripts/dcs_ts116n_audit_leakage.py:477-479` assigns rows to train/test by `dsplit` and
`fit_eval` reports accuracy on the 23 TEST domains; N4 = 0.4174 is that number, and it caused a
corpus rebuild (`ts116m`). The measurement is prompt-only, uses no model and no outcome, so it does
not violate the letter of `.split.discipline` (*"never for layer/head/path/direction/threshold
selection"*). It is still a design decision informed by the test partition, and the config's own
sentence *"test is read once, by the frozen …"* now has one prior read. Worth one line in the
write-up rather than a code change.

**MIN-13 — hardcoded absolute paths (item 1).**
Only one new instance: `src/boombness/slurm/run_ts_harm_pools.sh:24-25` hardcodes
`/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood` and
`/home/sharifm/students/omeryosef/miniconda3/etc/profile.d/conda.sh`. This matches the existing
house pattern (`run_boombness.sh:45`, `:47`) and is arguably required for a SLURM script that starts
with no CWD guarantee, so it is recorded rather than objected to. **Every new Python script and
every new `scripts/*.sh` derives its root correctly** — `REPO = os.path.dirname(os.path.dirname(
os.path.abspath(__file__)))` in all six new Python files, `cd "$(dirname "$0")/.."` in
`dcs_ts_preflight.sh:26`, `dcs_ts_build_ts116n.sh:35`, `dcs_ts_build_banks.sh:49`. No `/tmp`
argsfile appears anywhere; `dcs_ts_preflight.sh:107` actively refuses one.

**MIN-14 — HEAD is not what will run.**
Four reviewed scripts carry uncommitted edits at review time (see the caveat at the top). Notably
`dcs_ts_gen_concept_harm_pools.py` gained `_substitutable_forms()` (C-079) in the working tree only,
and `dcs_ts_verify_ts116n.py` / `dcs_ts_build_ts116n.sh` gained the `BANK_TAG`/`POOLS_TAG`
parameterisation in the working tree only. Any statement of the form "at commit `e4d78bf0` the
filter handles case forms" is false. The shared-tree rule applies
(`git commit -- <paths>` only); I have committed nothing.

---

# Checks that passed

**Item 3, SPLITS — clean.** The `dsplit`/`split` separation is applied consistently, and I found no
code path that uses the within-domain `dev`/`heldout` cut where the domain cut is meant.
`scripts/dcs_ts_audit_leakage.py:157-158` and `scripts/dcs_ts116n_audit_leakage.py:207-208` both
hard-refuse a manifest whose `field_name != "dsplit"`. The bank's `split` field appears only in
display and deterministic-sampling contexts
(`dcs_ts_audit_concept_backing.py:306` sample key, `dcs_ts_power.py:202` `within_split` census,
`dcs_ts_audit_leakage.py:552` a row label) and is explicitly renamed at the join boundary:
`scripts/dcs_ts_sidecar.py:344` `"within_domain_split": r.get("split")`, with
`SPLIT_FIELD_NOTE` at `:116-118` spelling out the hazard. The one place both names sit side by side
in one record is `scripts/dcs_ts_token_roles.py:306` (`"split": row["split"], "dsplit": dsplit`),
which is correct but is the one row shape where a careless downstream `groupby("split")` would do
the wrong thing silently.

**Item 4, JOINS — clean, no `prompt_id`-alone join found.** Every cross-bank join in the range
carries the codeword or the full bank identity:

```
scripts/dcs_ts_sidecar.py:328-331     join_key = f"{bank_file_sha16}:{prompt_id}"; join_key_fields declared
scripts/dcs_ts_sidecar.py:524         asserts distinct (bank_file_sha16, prompt_id) == n rows
scripts/dcs_ts_audit_leakage.py:391   by_key[(r["bank_codeword"], r["prompt_id"])][r["bank_concept"]]
scripts/dcs_ts_audit_leakage.py:414   keyed on (codeword, cell, query_kind, n_examples, prompt_id)
scripts/dcs_ts_token_roles.py:332     by[(r["codeword"], r["concept"], r["prompt_id"])]
```

`scripts/dcs_ts_verify_ts116n.py`'s `load_bank()` keys on bare `prompt_id`, but every use is
*within one codeword* (`for cw in CODEWORDS:` at `:172`, three concept banks loaded into `banks`
inside that loop), so the button/basket collision cannot occur; concept banks of one codeword are
*supposed* to share `prompt_id`, and that shared key is what G2/G3 measure against. Correct as
written — but it is one refactor away from being wrong, and it carries no comment saying so.

**Item 9, existing `run_boombness.sh` callers — none broken.** See MAJ-6.

---

## What I could not establish

- **Which bank family is the population** (`ts116n` as frozen, or `ts116m` as built). UNKNOWN.
  Resolving it needs a decision recorded outside the code; the artifacts currently disagree.
- **Whether `NOMINATED_REL_END = -9` holds on `ts116n`/`ts116m`.** UNKNOWN. It requires re-running
  `scripts/dcs_ts_token_roles.py` against the corrected banks, which needs the tokenizer; I did not
  run it (read-only, and it is a model-adjacent load).
- **Whether the `restaurant_kitchen` exclusion is right on the merits.** Probably yes on the domain
  argument; the *replication* offered as evidence is confounded (MAJ-4). Establishing it needs one
  regeneration at a seed outside `[20260906, 20260920]`.
