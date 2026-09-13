# Proposal: the differ-across-arms causal test for the query-side probe (§44 #10) — needs GPU authorisation

**2026-09-13. Status: BLOCKED on GPU authorisation. This is a go/no-go spec, not a run.**

## Why this is the one remaining move that matters
The Phase-4 candidate sweep is complete (CONT-ENTRY 154): F5 (demo-side rank-1 ridge) is the
**strongest** installation predictor and **nothing beats it on held-out VALIDATION** (F6 low-rank and
F8 query-side also transfer above the raw-state floor but do not exceed F5) — and F5 is **causally
inert**: its site `cw_demo_mean` is bit-identical across `ko`/`ctrl` (C-CONT-040), so it cannot mediate
the one intervention this phase owns. The query-side probe (F8, CONT-ENTRY 152) is the only candidate whose
site the knockout actually edits, but it is ~70 % collinear with F5 and its causal relevance is
untested. The **only** measurement that can turn a query-side probe into a §44 #10-eligible candidate
— or close the question negatively — is whether the query-side hidden state **differs between `ko`
and `ctrl`** and whether that difference carries installation information.

## Why it is cheap: ctrl already exists
The differ-across-arms test needs paired `ko` and `ctrl` hidden states at the query sites. **`ctrl`
already exists**: `cont1_behavioral_{button,basket}_bomb` are no-knockout base multiposition caches
(`knockout_applied=False`, `arm=None`), dose 4, layers [0,2,…,31], sites incl. `cw_query`(==rel-11),
`rel-6`, `cw_demo_mean`. Each is on its OWN codeword's bank — **button `dcd92d723f3e6d00`, basket
`79511d9e254571e6`** (they are NOT the same bank; conflating them would be a button/basket pooling
error). So only the **`ko` arm** must be generated per codeword, matched to that codeword's own bank
so prompt_ids pair exactly, and the CPU analysis must assert the per-codeword `bank_sha` before
pairing. This cost saving is conditional on the `ko` run using the same demonstration arm as `cont1`
(`--arm demo_all`); if the demo config differs, the positive control (`||h_ko−h_ctrl||` at
`cw_demo_mean` ≈ 0) will fail and `ctrl` must be regenerated (~4 jobs, not 2).

## The GPU run (2 jobs, ~4–8 GPU-h total)
Per codeword, one knockout-live extraction (the surgical A1 scope), matched to `cont1`:

```
python scripts/dcs_extract_under_ko.py \
  --bank data/boombness_prompts/boombness_prompt_bank_ts116m_<CW>_bomb.jsonl \
  --knockout-scope target_surface_row_only   # the surgical A1 knockout (KO-1), NOT legacy_all_query \
  --arm demo_all --attn-impl eager           # eager is forced when the knockout is live \
  --capture-codeword-occ --capture-rel-end "-1,-2,-3,-4,-5,-6,-7,-8,-9,-10,-11" \
  --layers 16,18,20,22,24,26,28,30,31 \
  --only-n-examples 4                          # dose 4, matches cont1 \
  --only-split train,validation                # NEVER read TEST \
  --model /home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/snapshots/0e9e39f249a16976918f6564b8830bc894c89659 \
  --tag cont1ko
```
- SLURM: `--partition=killable --account=gpu-research --gpus=1 --cpus-per-task=4 --mem=48G` (the
  `run_boombness.sh` footprint). Model is 8B bf16 (~16 GB) + hooks → fits one 24 GB GPU.
- Hardware must be **pinned** for generation (cross-GPU changes 573/670 completions); readouts are
  offset −0.0002, so the *comparison* to `cont1` is safe across GPUs, but the `ko` run itself should
  pin one node. Liveness gate: `assert_knockout_live` aborts a run that cannot prove the knockout
  fired — so a silently-weaker knockout cannot pass.

## The CPU analysis (a small extension of `dcs_cont_qprobe.py`, run after the ko cache lands)
Pair `ko` vs `ctrl`(cont1) by prompt_id, cell C, per domain (independence unit = DOMAIN; button and
basket never pooled):
1. **Positive control (validates the extraction):** `||h_ko − h_ctrl||` at `cw_demo_mean` must be
   ≈ 0 — this is C-CONT-040's known invariance. If it is not ≈ 0, the extraction is mis-paired and
   the test is void.
2. **The effect:** `||h_ko − h_ctrl||` at `cw_query`(rel-11) and `rel-6`. Because `cw_query` is the
   edited row, a non-zero difference is near-certain; that alone is not the result.
3. **The decisive quantity:** project both arms' states onto the frozen F8 query-side probe direction
   `w_q` and ask whether the readout `⟨h, w_q⟩` **shifts across arms in the installation direction**,
   and whether that per-domain shift **tracks the knockout's per-domain effect on installation /
   refusal** (the A1/A4 effects, already measured).

## Decision rule (pre-declared)
- **§44 #10 candidate** iff: control ≈ 0 (validated) AND the query-side readout shifts across arms AND
  the shift correlates with the behavioural effect. → proceed to a patch test (Phase 7/11).
- **Negative close** iff: the query-side state differs across arms but the readout shift is NOT
  installation-directed / does NOT track the effect (generic perturbation), OR the shift is null. →
  the query-side probe is causally inert too, and the phase has a confirmed *predictor* (F5) with no
  causal *mediator*.
- **POWER CAVEAT (from CONT-ENTRY 150).** Step 3's "tracks the per-domain effect" is a domain-level
  correlation on ~67 domains — exactly the regime `dcs_cont_linking_power.py` showed is underpowered
  (MDE ≈ 0.337 at N=67; ~0.30 power for ρ≈0.18). So a *null* on the tracking correlation is only
  informative down to that MDE: below it, "no causal component" is **indistinguishable from
  underpowered**, and the negative close must be stated as "no effect detectable above MDE 0.337",
  not "no effect". Steps 1–2 (the ‖Δ‖ magnitudes) are not correlation-limited and remain informative.

## Honest expected value
Given the query-side is ~70 % collinear with the causally-inert F5, the most likely outcome is the
**negative close**: `cw_query` will differ across arms (it is edited) but the installation-relevant
component is largely the F5-shared part, which is not knockout-sensitive. That is still worth running —
it converts "untested" into a definite answer on the phase's central causal question, on ~4–8 GPU-h.
It is flagged for authorisation rather than launched because it is the first GPU spend this session.
