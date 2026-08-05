# Phase REFUSAL-TRAJECTORY — the refusal outcome is decided at the decision point, not re-engaged

**Question.** Doublespeak's base ASR is only ~0.36 — why do ~half the DS attempts still refuse? Two
hypotheses: (a) refusal **re-engages mid-generation** (prompt-level suppression decays as the answer unfolds),
or (b) the outcome is **fixed at the decision position** (DS under-suppresses some prompts at token 0, which
then refuse from the start). Test: track the refusal-axis projection along the generated tokens, split by
outcome. Reuses the generation + per-layer refusal projection (`phase_refusal_trajectory.py`); outcome labeled
by kw_refusal (no API). clearharm (44/42), curated (30/21).

## Result — the outcome is set at the DECISION POINT (token 0); no mid-generation re-engagement

Refusal-axis projection (L30) at the first generated token, by outcome (clearharm test, n=42; ds_refused
rate 0.45):

| condition | projection @ token 0 | trajectory |
|---|---|---|
| Direct harmful (refuses) | **13.6** | high → decays as refusal text is emitted |
| Doublespeak → **refuses** | **9.1** (≈ Direct) | high → decays (then partial rise: residual refusal text) |
| Doublespeak → **jailbreak** | **−2.1** (suppressed) | stays low/negative throughout |

The refused-DS and complied-DS trajectories are **separated from token 0** and never cross: the DS prompts
that end up refusing already carry a near-Direct refusal signal at the first generated token, while the ones
that jailbreak are suppressed from the start and stay suppressed. **Hypothesis (a) — mid-generation
re-engagement — is falsified; hypothesis (b) — decision-point suppression — holds.** This is the temporal
form of the item-level predictor (REP_PREDICTS_BEHAVIOR, AUC 0.87): the decision-token projection decides the
outcome, and the trajectory shows that decision is made at generation step 0.

**curated confirms the second partial-ASR source.** curated DS has **`ds_refused_rate = 0.000`** — *zero* of
its generations refuse (uniform suppression; every trajectory starts at/below benign, projection ≈ −2.6),
yet curated ASR is only ~0.10. So curated's non-jailbreaks are **not refusals** — they are benign
codeword-dilution outputs that fail the harmfulness judge. This is the **concept-dilution** mechanism, cleanly
isolated: refusal is fully off, but the codeword remap makes the answer about the benign word.

## Interpretation — partial ASR, resolved into two decision-point mechanisms

1. **Under-suppression (clearharm):** DS suppresses refusal to *varying* degrees at the decision token; the
   under-suppressed prompts refuse from token 0 (their projection starts near Direct). The refusal axis is the
   gate, read at the decision point.
2. **Concept-dilution (curated):** DS suppresses refusal for *everyone* (0% refusals), but the codeword-
   substituted output is often benign, so it fails the harm judge despite refusal being off.

Both are set at/near the decision position, not by a dynamic that unfolds during generation. This completes
the refusal-locus account: the refusal axis decides compliance at the decision token, and where it does not
gate (curated, uniform suppression) the residual limiter is the (behaviorally-inert) concept remap diluting
the output.

## Reproduce
```
sbatch --time=00:20:00 --export=ALL,DSBENCH=doublespeak_causality/data/behavioral/beh_clearharm.json,DSMAXNEW=120,DSN=0 \
  doublespeak_causality/slurm/run_reftraj.sh          # + beh_curated.json
```
Runs: clearharm `refusal_traj_clearharm_*711956`, curated `..._711957`. Figure: `figures/refusal_trajectory.png`.
