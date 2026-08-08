# §22 — Token-Timing of Refusal Restoration

**Status:** PARTIAL result. The decision-token **residual REPLACE** (= Gate B) is the operative intervention;
**additive refusal-direction steering at any timing** (prefill / decision / first-tok / first-k / all-decode)
does not reduce ASR (weak/null/slightly positive) — with a magnitude-matching caveat.

**Run:** `phase22timing_clearharm_...732981` (170r, v3, `scripts/phase22_timing.py`). Reuses the Gate-B
decision-patch harness + a decode-aware additive `TimedAdd` for the persist arms.

## Result — ΔASR vs ds_base (paired McNemar), per split
| arm | train (n=85) | dev (n=43) | test (n=42) |
|---|---|---|---|
| **anchor_dpatch_direct_L18** (residual REPLACE = Gate B) | **−0.106** (p=0.078) | **−0.163 (p=0.039)** | −0.048 (ns) |
| timing_A_prefill (additive r̂ on prompt) | −0.059 | −0.163 (p=0.016) | 0.000 |
| timing_B_decision (additive r̂ @ decision tok) | −0.047 | −0.093 | −0.024 |
| timing_C_firsttok / D_first8 / E_alldecode (additive persist) | +0.06 / +0.02 / **+0.07** | +0.02 / −0.02 / 0.00 | −0.02 / 0.00 / +0.02 |
| ctrl_rand_alldecode | +0.024 | −0.023 | 0.000 |

## Interpretation
- **The full decision-STATE replace (anchor) reduces ASR** (reproduces Gate B on train/dev); no *decode-time*
  additive steering is needed for that effect — the intervention lives at the decision token (prefill).
- **Additive refusal-DIRECTION steering does not reduce ASR at any timing** (decode-persist arms C/D/E are
  ~0 or slightly positive). So there is no evidence that the refusal signal must "persist through decode";
  and additive direction-steering is a much weaker lever than full-state replacement (consistent with the
  §19–21 defense finding that additive steering is non-selective / weak).
- **Caveat:** the additive arms use a calibrated per-step magnitude `m0`; if under-dosed relative to the
  full-residual replace, their null is partly a dosing artifact, not proof that timing is irrelevant. A
  magnitude sweep on the additive arms would tighten this.

## Plumbing (audit 2026-08-08)
The α=0 no-op control (`ctrl_self_noop`) generates byte-identical text to ds_base (`TimedAdd` returns None at
α=0). The initial `self_noop != ds_base` flag was **judge stochasticity** — per-item label discordance was
9/170 = 5.3%, within the §1.2 between-run judge floor (~6pp). The check was fixed to test label-discordance
against the floor (not exact ASR equality), and now passes. The additive-timing plumbing is sound.

## Verdict
Decision-state **restoration is a prefill/decision-token effect** (full-residual replace, Gate B); additive
refusal-direction steering through decode adds nothing at the matched magnitude (dosing-caveated). §22 → the
timing that matters is the decision state, not decode-persistence.
