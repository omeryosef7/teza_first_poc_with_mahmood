# Proposal: the interventional PATCH test for the query-side representation (§44 #10) — needs GPU

**2026-09-15. Status: decision-ready; BLOCKED on GPU authorisation.** Reuses existing tooling
(`score_behavior.py --rescue-*`) — no new code.

## Why
CONT-162→166 established, observationally and adversarially-verified, that the A1 knockout **causally
perturbs the query-side representation (`rel-6`) specifically along the installation-predictive axis**
(replicated; energy-reduction rival refuted; 3–4× placebo; survives mean-state projection-out). What is
NOT established is the **representation → behaviour** link: whether that query-side perturbation is what
*causes* the knockout's downstream effect. §44 #10 asks exactly this — an "aggressive patch at its site
has causal leverage." That is an INTERVENTION, not a readout.

## The test (existing tooling)
`score_behavior.py` already implements activation "rescue": under the live knockout, capture `resid_post`
at a layer from a CLEAN (unhooked) forward over chosen positions and write it back during generation.
- `--rescue-positions query` — patch the query span (the positions the differ-arms test found causally perturbed).
- `--rescue-donor clean` — from the no-knockout forward (the rescue).
- `--rescue-layer L` — layer to capture/write (fix at the differ-arms winner band, L≈18–20; PR-13 forbids sweeping layers until one rescues).
- token identity over the patched span is re-verified before writing (DonorPatch).

**Arms (per codeword, never pooled):**
1. `ctrl` (no knockout) — baseline.
2. `ko` (knockout, no rescue) — the effect to undo (A4: refusal cut to ~a third; and the de-refusal/content endpoints).
3. **`ko + rescue query from clean`** — the test arm.
4. `ko + rescue-donor self` — identity control (must reproduce arm 2 exactly, else the patch is not writing what it read).
5. `ko + rescue query, --rescue-n-positions K` — size-match control (separate position IDENTITY from COUNT; R-39 caveat).

## Decision rule (pre-declared)
- **Causal leverage (query-side is the bottleneck):** arm 3 moves the endpoint materially back toward
  `ctrl` (arm 1), while arm 4 reproduces arm 2 and arm 5 does not spuriously recover. → the query-side
  representation carries the knockout's effect → §44 #10 PASS.
- **No leverage:** arm 3 stays at arm 2 despite a valid patch (arm 4 identity holds) → the query-side
  perturbation is a correlate, not the causal bottleneck. → honest negative.

## Endpoint (the key design choice, stated openly)
The differ-arms signal was on the BEHAVIOURAL prompt's query-side state. The cleanest matched endpoint
is therefore the knockout's **behavioural effect** on the behavioural prompt — primarily **refusal /
de-refusal** (A4 is a large, measured effect: refusal 0.112→0.040 on the slot0 primary), with the
CR-002 content endpoint secondary. "Installation" per se is a semantic-prompt readout; whether the
knockout even acts on the semantic prompt is a separate question, so installation-on-semantic is a
secondary arm, not the primary. Report refusal recovery as the primary §44 #10 endpoint.

## Cost & guardrails
~4–5 `score_behavior` runs per codeword over the dose-4 behavioural rows (≈ readout scale, ~1 GPU-h
each with the model load; the ~72-min matanbentov-hub NFS load dominates — pin `--model` to the live
snapshot, C-CONT-100/101). ~8–10 GPU-h total. Pin hardware for generation (cross-GPU changes 573/670
completions). `--only-split train,validation` (never TEST). DOMAIN is the independence unit; button and
basket never pooled. Watch quota (200 GB cap, C-CONT-101) — these runs write completions + judge
artifacts, not 11 GB caches, so footprint is small.

## Honest expected value
Given the observational signal is real but the placebo margin is moderate (3–4×) and representation→
behaviour is entirely untested, this could go either way. Either outcome is publishable: a rescue that
restores refusal is the phase's first genuine causal-mediation result; a null cleanly bounds the
query-side representation as a correlate. Flagged for authorisation, not launched (GPU spend).
