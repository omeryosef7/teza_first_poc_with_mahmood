# DCS thesis-scale sprint — the remaining phases, and which of them are GATED OFF

*2026-09-07. Decisions recorded before any of them runs, so that a phase that does not run is a
recorded decision with a reason rather than a phase that was quietly dropped.*

Mandate §31 lists PHASES 1–14. PHASES 1–7 are complete. This file states, for each of 8 and
10–14, whether it runs, and if not, on whose authority it is held.

---

## PHASE 8 — corrected causal knockout — **DEFERRED, not skipped**

`configs/dcs_ts_pr056_phase8.json` is FROZEN and verifies clean under the loader, but its analyzer
**does not exist** (`scripts/` has no `pr056`/`phase8` analyzer) and the config returns **6
refusals** under `--for-extraction`. So PHASE 8 cannot run today regardless of scheduling.

PHASE 9's own checklist item **Q8** asks only that PHASE 8 be *"completed or explicitly deferred so
the two GPU phases do not compete for fair-share."* This is that explicit deferral, and the reason
is the one Q8 names: fair-share is depleted, PHASE 9 is the phase that answers the mandate's
central causal question (CLAIM C), and two GPU phases contending is the exact failure Q8 was
written to prevent.

Binding constraint carried forward, from `A-045`: the corrected knockout must **read strictly above
the band floor** and must **not select on a saturating population**. Those are ONE requirement, not
two — a knockout selected at a site where the measure is saturated cannot be rescued by reading it
somewhere better.

**Status: DEFERRED behind PHASE 9. Not abandoned. Q8 satisfied.**

## PHASE 10 — the "last bomb row" symmetry experiment with downstream readout — **UNSTARTED, runnable**

No preregistration, no analyzer, and **zero mentions in the progress log**. Genuinely not started.

It is independent of PHASE 9's outcome and is therefore the natural next GPU phase once PHASE 9's
arms are submitted and the 6-job cap has room. It needs a preregistration first, per mandate §21
and the house rule that nothing runs before it is preregistered.

## PHASE 11 — concept-free semantic-position knockout / corrected K-mechanism — **UNSTARTED, runnable, reusable code exists**

Also zero mentions in the log. But it does **not** start from nothing: `scripts/dcs_kladder_analysis.py`,
`dcs_verify_kladder.py`, `dcs_verify_kladder_rowlevel.py` and `dcs_redteam_kladder_verifier.py`
already exist from earlier phases, which is exactly the reuse the mandate asks for rather than new
code. The *concept-free* requirement is the new part: the readout must not name the answer in its
own question, which is the instrument finding R-116 established (the display channel takes knife
from 0.000 to 0.628 purely by naming "knife" in the prompt).

## PHASE 12 — behavioural controls, `mapping_use`, ASR — **GATED OFF by its own precondition**

The mandate does not list PHASE 12 unconditionally. It reads:

> PHASE 12
> **Only if representation story is solid:**
> row-randomized behavioural controls; mapping_use; ASR.

**The representation story is not solid, and this phase's own results are what established that.**
Three findings, none of them speculative:

- **`R-112`** — CLAIM A is narrowed to the *prompt*, not the codeword: a control nine tokens
  downstream, token-identical across concepts and carrying no concept token, decodes identity at
  **0.9261** against the codeword's **0.9446**, and under the preregistered Holm *both* p-values
  fail. Codeword ≈ control.
- **`R-116`** — two of the three arms do not install at all on the primary concept-free channel
  (**bomb 0.619, knife 0.000, gun 0.009** of 113 domains). So the three-way separation is *which
  demonstration set is present*, not *which concept was installed*.
- **CLAIM B is UNSUPPORTED** — `R-111`'s question D failed: the residual axis carries remapping and
  identity together.

A precondition written into the mandate is not a hurdle to be argued past. **PHASE 12 does not run**
unless PHASE 9 returns a positive causal result that repairs the representation story, and even
then the R-116 installation asymmetry has to be addressed first, because an ASR number computed
over arms that never installed their concept would be uninterpretable in exactly the way §33 bans.

**Status: GATED OFF. Reopens only on a PHASE 9 positive.**

## PHASE 13 — representation destruction ↔ downstream use on the SAME bank — **BLOCKED on PHASE 9**

This is the mediation test, and it is downstream of PHASE 9 by construction: it needs a
representation-destruction result to correlate against downstream use. It also inherits `R-097`'s
lesson — the reason PHASE 7 had to run at all was that a mediation question with no `y` measured
where `x` lives is a CANNOT ANSWER, not a null.

## PHASE 14 — adversarial audits, literature update, paper-facing summary — **IN PROGRESS**

The adversarial-audit component is running continuously rather than as a terminal phase, which is
the right shape for it: the PR-053 direction export is under adversarial review now, and the
four-hour reviews have been folded in throughout. The paper-facing summary exists in draft as
`reports/DCS_TS_CLAIM_TABLE.md` plus the collaborator draft.

Outstanding within PHASE 14: the **literature update**, which has not been done in this phase.

---

## The honest summary of the sprint's shape

Of the mandate's fourteen phases, **1–7 are complete**, **9 is in flight** with 7 of 12 blockers
closed, **8 is deferred behind it**, **10 and 11 are runnable but unstarted**, **12 is gated off by
its own written precondition**, **13 is blocked on 9**, and **14 runs continuously with the
literature update outstanding**.

Two of those are decisions rather than states — PHASE 8's deferral and PHASE 12's gate — and both
are recorded here with the authority they rest on, so that neither reads later as a phase that was
skipped without anyone noticing.
