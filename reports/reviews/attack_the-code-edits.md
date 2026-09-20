```
=============================================================================
ADVERSARIAL REVIEW R10 — LENS: bf16 capability guard + compute_capability provenance
=============================================================================
Everything below was measured on c-001 (login node, NVIDIA TITAN Xp, compute
capability 6.1 — verified by running env_metadata()). No sbatch, no file edited
in the repo, no git write. Scratch: /tmp/claude-47249/.../scratchpad/
(mirror/, mirror2/, alloc2.py, axes.py, corp.py, table.py).

=============================================================================
(e) FULL SUITE — NO NEW FAILURES
=============================================================================
  python -m pytest tests/ -q
  -> 8 failed, 1793 passed, 7 skipped, 3 warnings in 1037.96s

Failure set, name for name, identical to R9:
  test_common_provenance::test_a_tokenizer_revision_is_a_resolved_commit...   (1)
  test_donor_patch::test_rescue_liveness_is_recorded_on_the_row              (2)
  test_donor_patch::test_rescue_positions_and_count_reach_the_row
  test_prompt_families_strict::{violating_input_really_violates,
     strict_violation_writes_nothing, strict_violation_does_not_clobber,
     non_strict_violation_still_writes_both_files}                           (4)
  test_tsc_request_filter::test_tokenizer_gate_accepts_...                   (1)
All 8 are the gated-HF / corpus-invariant pre-existing set (the visible
traceback is `OSError: gated repo ... meta-llama/Llama-3.1-8B-Instruct`).
Passed count 1780 (R9) -> 1793 (+13) = exactly the 13 new bf16 tests.
NO NEW FAILURE. The guard and the provenance edit break nothing in the suite.

=============================================================================
BLOCKER 1 — EVERY COMMITTED BASKET AXIS IS FIT ON A V100 bf16 CORPUS
=============================================================================
WHAT I MEASURED (scratchpad/axes.py, torch.load of each configs/dcs_csi_axis_*.pt,
then RUNMETA.json of its meta["corpus"]):

  axis .pt                                    codeword  corpus GPU              corpus dtype
  dcs_csi_axis_basket_behavioral.pt           basket    Tesla V100-SXM2-32GB    bfloat16
  dcs_csi_axis_basket_behavioral_shuf24.pt    basket    Tesla V100-SXM2-32GB    bfloat16
  dcs_csi_axis_basket_L18_PLUS_button_swap.pt basket    Tesla V100-SXM2-32GB    bfloat16
  dcs_csi_axis_basket_L20.pt / _more.pt       basket    Tesla V100-SXM2-32GB    bfloat16
  dcs_csi_axis_basket_semantic.pt             basket    NVIDIA GeForce RTX 3090 bfloat16
  dcs_csi_axis_button_behavioral_L18.pt       button    NVIDIA GeForce RTX 3090 bfloat16
  dcs_csi_axis_button_L18_PLUS_basket_swap.pt button    NVIDIA GeForce RTX 3090 bfloat16
  (all other button axes: RTX 3090)

The single V100 corpus is
  outputs/boombness/extract_boombness/cont1_behavioral_basket_bomb_20260910_113902_3966018
  RUNMETA: gpu "Tesla V100-SXM2-32GB", host rack-gww-dgx1, job 876103,
           argv `scripts/dcs_extract_under_ko.py --bank ...basket... --no-knockout ...`,
           args.dtype "bfloat16";  DONE.json status ok, rows_written 3714.
Its button twin (job 875529, n-305, RTX 3090, 3720 rows) has a byte-identical
argv except the bank.

WHICH COMMITTED READS DEPEND ON IT (measured from each report's run_dirs ->
config.json args.rescue_basis):
  PR-CSI-003 necessity  -> dcs_csi_axis_basket_behavioral_shuf24.pt   (V100 corpus)
  PR-CSI-006 dir. A     -> swap_provenance.donor_file =
                           dcs_csi_axis_basket_behavioral.pt, donor_key cand_rank1
                           (V100 corpus) injected into BUTTON
  PR-CSI-006 dir. B     -> basket recipient file, V100 corpus, 48 of 50 arms
  PR-CSI-005 button L18 -> button axis only (3090 corpus) — clean

WHY IT MATTERS. The headline of S-138 is "basket's axis rescues BUTTON, rank 4 of
47, where button's OWN axis gives rank 36 of 47 — the PROBE decides." The two
probes being contrasted differ in exactly the variable this sprint declared a VOID
condition: basket's cand_rank1 was fit on hidden states produced in EMULATED
bfloat16 on sm_70; button's on native bfloat16 on sm_86. The 46-control family it
is ranked against is 3090-derived. "GPU architecture of the axis fit" is a
perfectly-confounded alternative explanation for the direction of the asymmetry,
and it is unexcluded because no gate reads the corpus at all:
  grep -rn "corpus" scripts/gates/*.py scripts/dcs_csi_subspace_analyze.py \
       scripts/dcs_csi_rederive_subspace.py   ->  (no output)
PR-CSI-005/006 gate 0(a) pins architecture only over the SCORING run dirs
(dcs_csi_pr005_gate0.py:78-97, `assert n >= 50`), never over the axis fit.

This also falsifies a committed sentence. Sprint log line 8179:
  "No committed claim touched a V100."
It is scoped to score_behavior arms; the axis-fit corpora were outside the scan.
Measured: PR-CSI-003 and PR-CSI-006 both rest on a V100 bf16 extraction.

WHAT I CANNOT MEASURE: whether sm_70 bf16 emulation actually perturbs the
extracted hidden states enough to move the rank. That needs a same-bank
re-extraction on a 3090 and a re-fit, i.e. a GPU job — forbidden here. I measured
the confound, not the effect size.

MINIMAL FIX (do not apply): re-extract cont1_behavioral_basket_bomb on a 3090 with
identical argv, re-fit dcs_csi_axis_basket_behavioral.pt, and rebuild the swap .pt;
OR record the corpus GPU in each report and downgrade PR-CSI-006's conclusion to
"probe-or-probe-hardware decides". Structurally: make the analysers read
meta["corpus"]/RUNMETA and refuse a corpus whose compute capability < 8.0.

=============================================================================
BLOCKER 2 — 20 OF 27 "same allocation" CLAIMS IN KNOWN_SHORT ARE FALSE
=============================================================================
scripts/gates/dcs_document_short_runs.py (new this session) writes KNOWN_SHORT
exemptions into src/boombness/run_completeness_check.py. Its TEMPLATE asserts
  "MEASURED here against the full {refn}-row arm {ref} of the same allocation"
but its reference-arm selector is
  pref = rid.rsplit("_", 3)[0].rsplit("_", 1)[0]   # -> "csi1_button_train_KO"
  ... glob(pref + "_*") ... ref = sorted(cands)[-1][1]   # newest by mtime
— no slurm_job_id comparison anywhere in the file.

MEASURED (scratchpad/alloc2.py: parse the 92 KNOWN_SHORT entries, take the 27
carrying the phrase, compare the short run's RUNMETA.slurm_job_id against the job
ids of every run dir named for the claimed reference arm):
  same-allocation claim CONFIRMED: 7
  same-allocation claim FALSE:    20
e.g. csi1_button_train_KO_SHUF9_20260920_160010_927085 (job 912835) cites
     KO_SHUF23, whose only run dirs are jobs 898698 / 901739 / 912837.
     csi1_button_train_KO_RAND6_... (job 912835) cites KO_SHUF14 (jobs
     898698/901739/912837). Full list in the scratch script output.

WHY IT MATTERS: these are permanent, committed records whose job is to justify
exempting rows from the completeness guard. A false provenance sentence inside an
exemption is the exact "prose at one end of a contract, nothing at the other" class
this sprint keeps re-finding. (Scientific damage is limited — all these arms are
RTX 3090, measured — but the record is wrong.)

MINIMAL FIX: select the reference arm by RUNMETA.slurm_job_id equality and assert
it, or drop the words "of the same allocation" and print the two job ids instead.

=============================================================================
(b) CALL-SITE TABLE — 1 OF 106 IN-REPO dc.load_model SITES IS GUARDED
=============================================================================
scratchpad/table.py over src/boombness, scripts, doublespeak_causality (vendored
trees excluded). 106 files call dc.load_model; exactly one contains
get_device_capability.

  GUARDED (1)
    src/boombness/score_behavior.py:3025         --dtype default bfloat16   GUARDED

  UNGUARDED, --dtype DEFAULTS TO bfloat16 (the dangerous set)
    scripts/dcs_extract_under_ko.py:1491   <-- PRODUCED THE V100 CORPUS ABOVE
    src/boombness/extract_boombness.py:814
    src/boombness/aggressive_patching.py:1400
    src/boombness/retrieval_strength.py:88
    src/boombness/semantic_binding_probe.py:622
    src/boombness/refusalness.py:182
    src/boombness/diagnose_readout.py:64
    doublespeak_causality/{01,05,06,07,08,09,10,11,13,14,15,17,18,19,21,48,51}_*.py
    doublespeak_causality/{build_refusal_direction_llama,next5_w5_defense_eval,
      smoke_pipeline}.py, src/probes/activation_extraction.py,
      scripts/{phase6_jacobian_readout,phase_x5_concept_qwen3,
      validate_refusal_directions}.py
    doublespeak_causality/25_eval_gcg_asr.py  (dtype=torch.bfloat16 HARDCODED,
                                               no flag to escape it)

  UNGUARDED, dtype OMITTED -> ds_common.load_model default torch.bfloat16 (~60 files)
    doublespeak_causality/{31,32,34,36,37,39,40,42,44,45,46,47,49,50,52}_*.py,
    doublespeak_causality/next6_*/next7_*, doublespeak_causality/scripts/asym_*,
    doublespeak_causality/scripts/phase*_*.py (~45 files),
    src/boombness/{rah_preflight_transport,rah_transport_assay}.py

  UNGUARDED but not bf16 by default
    src/boombness/surgical_knockout.py:701  (--dtype default float32)
    src/boombness/{diagnose_knockout,dominance}.py (dtype=torch.float32 literal)

The guard's own comment says "Placed at the load site, not at argparse, so no code
path can reach the model without passing it." That is true of score_behavior.py's
one path and false of the repo: 105 other entry points reach dc.load_model in
bfloat16 with no capability check, and one of them is the script that actually
produced the V100 artifact this sprint's whole lesson is about.

GUARD-EVASION ENUMERATION (as asked)
 1. Different entry point. dcs_extract_under_ko.py / extract_boombness.py /
    aggressive_patching.py etc. — UNGUARDED. This is not hypothetical; it is
    BLOCKER 1. MAJOR.
 2. Code path that builds args itself. Not reachable: main() parses argv
    internally and nothing in-repo imports and calls it (grep for subprocess/
    import callers of score_behavior returns only source-text readers). CLEAN.
 3. Multi-GPU where device 0 is not the device used. The guard reads
    get_device_capability(0) only; load_model uses device_map="auto", which can
    shard across devices 1..N. A heterogeneous allocation would pass the guard and
    run half the layers emulated. All CSI sbatch files request --gpus=1, so this
    is latent. MINOR. Fix: min over range(torch.cuda.device_count()).
 4. CUDA_VISIBLE_DEVICES remapping. Not an evasion: device 0 after remapping is
    the same device accelerate places layer 0 on. CLEAN.
 5. CUDA_VISIBLE_DEVICES="" (or a CUDA init failure). torch.cuda.is_available()
    is then False, the guard is skipped, and the model loads on CPU in bfloat16 —
    also non-native on most CPUs. MINOR (slow enough to notice).
 6. Resume path. None exists in score_behavior.py (no --resume, no second
    from_pretrained; grep for AutoModel/from_pretrained in that file: none).
    CLEAN.
 7. Analysers. None of scripts/dcs_csi_subspace_analyze.py,
    dcs_csi_rederive_subspace.py, or scripts/gates/* loads a model. CLEAN.
 8. quantize=. score_behavior never passes it; other sites do
    (asym_p1_reachability, phase4_bombness_intervention, phase5_component_patch,
    phase_behav_refusal) with bf16 compute dtype and no guard. MINOR.
 9. Spelling. `--dtype` has no `choices=`, so only the exact string "bfloat16"
    trips the guard; anything else fails later at getattr(torch, ...). CLEAN.

=============================================================================
(c) IS THE GUARD TOO STRONG? — NO, BUT IT FIRES ON THE LOGIN NODE
=============================================================================
* Only refuses (dtype == "bfloat16") AND cuda available AND major < 8. fp16/fp32
  on a V100 still run; every path past the guard loads a model, so it cannot
  refuse a model-free run (grep: score_behavior has no --dry-run/--no-model mode).
* It DOES fire on c-001 itself: measured compute_capability "6.1" (TITAN Xp).
  Any `python src/boombness/score_behavior.py --dtype bfloat16` on the login node
  now exits. I found no tooling that does this (judge_*.sh call judge_boombness,
  not score_behavior), so no current breakage — confirmed by (e): zero new suite
  failures.
* No existing test breaks on the inserted lines. The nearby source-text tests are
  ordering-based, not distance-based:
  tests/test_readout_liveness.py:228 asserts only `i < j` around
  `lm = dc.load_model(`; tests/test_rah_preflight_spans.py targets another file.

=============================================================================
(d) TEST STRENGTH — 0 OF 13 SURVIVE NOTHING; 13 OF 13 SURVIVE UNREACHABILITY
=============================================================================
  python -m pytest tests/test_bf16_capability_guard.py -q --collect-only -> 13 tests

MUTATION 1 — guard made unreachable by an early return above it.
  Mirror at scratchpad/mirror/ (copies of the test file, score_behavior.py,
  ds_common.py). Inserted `return 0` immediately above the guard comment.
    cd scratchpad/mirror && python -m pytest tests/test_bf16_capability_guard.py -q
    -> 12 passed, 1 skipped
  The 1 skip is test_the_guard_is_absent_from_the_pre_fix_blob, which skips only
  because the mirror is not a git checkout; in the real repo it passes (it asserts
  the OLD blob lacks the guard, which the mutation cannot change).
  => 13 of 13 survive. ZERO tests detect that the guard can never run.

MUTATION 2 — score_behavior.py made SYNTACTICALLY INVALID.
  Appended `def (this is not python` to the mirror's copy (ast.parse -> SyntaxError).
    -> 12 passed, 1 skipped
  The file is never imported by this test module; only read as text. A guard in a
  file that cannot even be parsed still "passes" 12 of 13.

MUTATION 3 — semantic: threshold `_cc[0] < 8` -> `< 7` (scratchpad/mirror2/).
    -> 1 failed, 11 passed, 1 skipped
  Caught by exactly ONE test (test_the_guard_refuses_only_bfloat16_and_only_below_8_0,
  whose regex pins the literal `if _cc[0] < 8:`). The five-case
  test_guard_predicate_truth_table did NOT catch it, and cannot: it re-implements
  the predicate inline —
      got = bool(dtype == "bfloat16" and cuda_available and cc[0] < 8)
      assert got is refuses
  — so it tests Python's `and`, never score_behavior.py. That is five of the
  thirteen collected items that cannot fail for any change to the product code.
  This is the S-042 / R2-M5 / S-134 class, third instance, in the tests written
  to close it.

PROPOSED MINIMAL BEHAVIOURAL TEST (proposal only, NOT written):
 1. Refactor the predicate to a module-level callable in score_behavior.py, e.g.
      def assert_bf16_capability(dtype: str) -> None:  # raises SystemExit
    and call it at the existing site. One-line change at the call site.
 2. Behavioural test, no model, no GPU: monkeypatch torch.cuda.is_available ->
    True, get_device_capability -> (7, 0), get_device_name -> "Tesla V100"; assert
    pytest.raises(SystemExit) for "bfloat16"; assert it returns for "float16"; and
    with (8, 6) assert it returns for "bfloat16". This kills mutations 2 and 3.
 3. Reachability test (this is the one that kills mutation 1, and it is the point):
    ast.parse score_behavior.py, walk main().body, find the index of the
    Expr/Call node for assert_bf16_capability and the index of the statement
    containing dc.load_model; assert the guard call index < load index AND that no
    unconditional `Return` or `Raise` node appears at main().body top level before
    it. An early `return 0` above the guard is exactly such a node, so this test
    fails on mutation 1 — which no current test does.
 4. Delete test_guard_predicate_truth_table or re-point its parametrisation at the
    real callable from (1).

=============================================================================
(a) FIELD TRACE, END TO END — PLUMBED, BUT HALF-PLUMBED DOWNSTREAM
=============================================================================
MEASURED on c-001:
  env_metadata() -> {"gpu": "NVIDIA TITAN Xp", "compute_capability": "6.1", ...}
  dc.write_runmeta(<scratch dir>) then reading the file back:
    ON DISK compute_capability: '6.1'   present: True   schema: RUNMETA/1
  LoadedModel.meta() inherits it (ds_common.py:380 `d.update(env_metadata())`).
  RunDir.finish -> metadata.json splices `**env` wholesale (common.py:665-684),
  so metadata.json gets it with no field-list edit needed.

REAL-ARTIFACT CONFIRMATION (and a correction to the sprint's own account):
  csi1_basket_validation_CODEANCHOR_139_20260920_180707_767634  (job 913314,
     the "wrong first fix" arm):  RUNMETA compute_capability ABSENT,
                                  metadata.json compute_capability = "8.6"
  csi1_basket_validation_CODEANCHOR_139B_20260920_190627_488644 (job 913407,
     running):  RUNMETA "8.6", metadata.json "8.6"
  => The first version was NOT "the field never reached the artifact" (the test
     docstring at tests/test_bf16_capability_guard.py:101-110 and the ds_common
     comment both say so). It reached metadata.json, via the `**env` path, and
     missed only RUNMETA.json. MINOR, but a reader chasing the bug looks in the
     wrong place. Also MINOR: sprint log line ~8902 says "The fix is one line in
     the RUNMETA writer — and it is in score_behavior.py"; the RUNMETA writer is
     doublespeak_causality/ds_common.py:247-260. The release was gated on the
     wrong file.

OTHER ARTIFACTS CARRYING gpu/provenance THAT DO **NOT** CARRY compute_capability
(MAJOR, because S-127a says this field is what the VOID condition depends on):
 1. RUNMETA.json of all 305 historical run dirs. Measured on the committed reads:
      DCS_CSI_REDERIVE_button_train_L18_n46.json  50/50 dirs: gpu "RTX 3090",
        compute_capability key ABSENT, args.dtype bfloat16
      DCS_CSI_REDERIVE_NECESSITY_basket_train.json 12/12 dirs: same
      DCS_CSI_SWAP_* (6 reports): 50 or 53 dirs each, all "RTX 3090", key absent
    So a VOID check written as `m.get("compute_capability") >= 8.0` voids every
    committed arm, and `m.get(...) is None` cannot distinguish "written before the
    fix" from "measured as None on a CPU box" — the exact ambiguity the test
    docstring names. The schema tag is still "RUNMETA/1" on both shapes, so a
    consumer has no contract-level signal. MINIMAL FIX: bump to "RUNMETA/2", or
    write an explicit sentinel ("unmeasured") rather than null, and have readers
    test key presence, not `.get()`.
 2. Every consumer still reads the MODEL STRING, not the new field:
      scripts/gates/dcs_csi_pr005_gate0.py:83,89   `.get("gpu")`
      scripts/gates/dcs_csi_pr006_gate0.py:90      `.get("gpu")`
      scripts/gates/dcs_csi_pr005_gate0d.py:42     prints `.get("gpu")`
      scripts/gates/dcs_csi_pr006_stage_anchor.py:46 prints `.get("gpu")`
      scripts/dcs_csi_rederive_patch.py:918-936 builds
        `"hardware": {arm: {"node":…, "gpu":…}}` + `hardware_verdict`
        ("SAME ARCHITECTURE" / "MIXED OR UNKNOWN") from sacct model strings,
        never from RUNMETA and never from capability.
    The field is produced and nothing consumes it. MAJOR.
 3. DONE.json (ds_common.write_done, explicit field list) carries no env at all.
    MINOR — but note three legacy scripts stuff their own `gpu` into both RUNMETA
    extra and DONE extra without capability:
      doublespeak_causality/scripts/phase5_head_zpatch.py:102,106,287
      doublespeak_causality/scripts/phase9_carry_sufficiency.py:132,282,294
      doublespeak_causality/scripts/phase7_refusal_head_edge.py:182,188,482
 4. config.json (RunDir) carries argparse only — correct, no change wanted.
 5. doublespeak_causality/scripts/backfill_runmeta.py:401,439 reconstruct RUNMETA
    from logs with key lists ("git_commit","gpu","torch","model"); capability is
    not in the logs, so backfilled dirs can never carry it. MINOR, document it.

=============================================================================
MAJOR — THE SOURCE TEXT THAT PRODUCED THE COMMITTED NUMBERS IS UNRECORDED
=============================================================================
This is the risk the uncommitted +474/-7 score_behavior.py diff creates, and
nothing measures it.
 * No run records a hash of the script it executed. grep for sha256/__file__ in
   src/boombness/score_behavior.py and doublespeak_causality/ds_common.py finds
   hashes of prompt ids, banks and probes — never of the executing source.
 * git_dirty comes from `subprocess(["git","status","--porcelain"])`
   (ds_common.py:116-129), while git_commit is read from .git files directly
   (ds_common.py:76-112). MEASURED across the committed reads:
     DCS_CSI_SUBSPACE_button_train_L18_n46:  git_dirty None on 36 of 53 arms,
       True on 17 (blob bc8e7779); commits ff72f424 / ad1288d6 / bd19a7e3 /
       4907efe1 / dabfeb85 all carry git_dirty = None.
     DCS_CSI_SUBSPACE_NECESSITY_basket_train: git_dirty None on 12 of 12.
   None means "could not determine" — `git` is not on PATH on the compute nodes.
   So for every arm in PR-CSI-003/005/006 the working-tree state is UNKNOWN, on a
   tree that has carried an uncommitted score_behavior.py diff all session.
 * scripts/gates/dcs_csi_pr005_gate0d.py:42-43 PRINTS git_commit and git_dirty
   and never asserts either. Its verdict ("the +474/-7 change is INERT",
   S-134) is therefore a bit-identity result between two runs whose source text
   is not recorded anywhere. The bit-identity itself is real and strong; the
   label "current blob" is not established by the artifact.
 MINIMAL FIX: record sha256 of sys.modules[__main__].__file__ (and of
 ds_common.py / donor_patch.py) in RUNMETA, and have gate 0d assert that A's hash
 differs from B's and equals the current file's.

=============================================================================
MINOR FINDINGS
=============================================================================
M1. The guard raises SystemExit at score_behavior.py:3018-3024, which is AFTER
    `run = RunDir(...)` at line 2924. RunDir.__init__ has already created the
    directory, written RUNMETA.json and config.json, and main() has no
    try/except (`run.abort` appears once, at line 4344, on an unrelated path).
    A refused run therefore leaves a directory with neither DONE.json nor
    ABORTED.json. (Read from source; NOT executed — running it would create a
    real run dir under outputs/ and could perturb gate 0d, see M2.) This matches
    the pre-existing pattern of the four sibling refusals nearby, so it is not a
    regression, but on a ~4 GiB quota it is a new way to make orphans.
    FIX: move the capability check above the RunDir construction, or wrap the
    refusal in `run.abort(...)`.
M2. scripts/gates/dcs_csi_pr005_gate0d.py:21 selects
      A_DIR = sorted(glob.glob(".../csi1_button_train_CODEANCHOR_R0_*"))[-1]
    i.e. "the newest dir" — which its own sibling dcs_csi_pr005_gate0.py:33
    explicitly forbids ("Never 'the newest dir'"), selecting by RUNMETA job id
    instead. Measured: exactly 1 CODEANCHOR_R0 dir exists today, so the gate
    currently picks the right one. Latent; interacts with M1 (a refused rerun
    would create a newer, empty CODEANCHOR_R0 dir).
M3. The guard's comment states the mechanism as "the norm-match degeneracy test
    rel = ||P(delta)||/||delta|| < 1e-6 is evaluated on a quantity emulation
    destroys". The test is computed in float64: donor_patch.py:233-234 casts both
    operands `.to(torch.float64)` before the subtraction. The V100 x norm-match ->
    0 rows correlation (S-119 table) is solid; the stated causal mechanism is not
    supported by anything I could find in the repo. Reword or measure.
M4. tests/test_bf16_capability_guard.py:35-38 uses
    `gi = s.index("get_device_capability")` (first occurrence anywhere in the
    file) and `assert between.count("\n") < 40`. Adding one more comment line to
    the guard, or mentioning the function name in an earlier docstring, breaks
    the test for no behavioural reason.
M5. dcs_document_short_runs.py hardcodes "at most {m} row(s) per domain out of 10"
    (the 10 is a literal, not measured) and asserts "both analysers intersect
    (domain, slot) KEYS across all arms before averaging" — a claim about other
    files that this script never checks. It is also the one new gate script with
    no non-vacuity assert: if `added` is 0 it exits silently, and nothing caps how
    many exemptions one invocation may write.

=============================================================================
WHAT I VERIFIED AND FOUND CLEAN (so it is not re-litigated)
=============================================================================
* env_metadata()'s new capture is inside the existing try/except and gated on
  `if cuda_avail:` — it degrades to None and cannot kill a provenance write.
  Confirmed by running it on a CUDA box and by reading the CPU path.
* write_runmeta's enrich-merge (`merged.update({k: v for k, v in rec.items()
  if v is not None})`) cannot blank an already-written capability on a second call.
* The 46-control families really are 46: dcs_csi_pr005_primary_X.py:35-38 and
  dcs_csi_pr006_native_vs_swap.py:24 assert the size before ranking, and
  dcs_csi_pr006_stage_anchor.py:57-62 asserts MIN_ROWS and per-field presence.
  Gate 0d asserts `fa/fb/len(common) >= 600` and all six fields on every common
  row. The new gates DO obey the S-134 rule — dcs_document_short_runs.py is the
  exception (M5).
* All 50 / 53 run dirs behind every committed SUBSPACE/SWAP report ran on
  "NVIDIA GeForce RTX 3090" with args.dtype bfloat16 — no V100 among the SCORING
  arms. The V100 is upstream, in the axis fit (BLOCKER 1).
```