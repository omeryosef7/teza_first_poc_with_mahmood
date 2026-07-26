# SEMA Reproduction Status

**Date:** 2026-07-25
**Sprint reference:** `docs/SPRINT_COMPLETION_PLAN_MATAN_MAHMOOD.md` §G1 (Priority 6, Phase G1–G8)
**Status:** BLOCKED — pending author code access
**Scope of this document:** design + status only. NO training, NO downloads, NO GPU/SLURM were run to produce it.

---

## 1. What SEMA is (from public sources)

**Paper:** SEMA: Simple yet Effective Learning for Multi-Turn Jailbreak Attacks
**arXiv:** 2602.06854 — https://arxiv.org/abs/2602.06854 (VERIFIED reachable 2026-07-25)
**Submission date:** 2026-02-06
**Venue:** ICLR 2026 (paper states 37 pages, 13 tables, 7 figures)
**Authors (from arXiv abstract page):** Mingqian Feng, Xiaodong Liu, Weiwei Yang, Jialin Song, Xuekai Zhu, Chenliang Xu, Jianfeng Gao
**DOI:** https://doi.org/10.48550/arXiv.2602.06854
**Additional public mirrors:** Microsoft Research publication page; Hugging Face papers page (`huggingface.co/papers/2602.06854`); OpenReview `forum?id=6eSNG1VNkl`.

### Method (two paper-stated stages)

SEMA frames multi-turn adversarial attack on safety-aligned chatbots as the real threat model
(single-turn being a special case) and states that prior approaches break under **exploration
complexity** and **intent drift**. Its pipeline:

- **Stage I — Prefilling self-tuning.** Fine-tune the attacker on non-refusal, well-structured,
  self-generated multi-turn adversarial prompts produced with a minimal prefix ("prefilling"),
  to yield usable rollouts and stabilize the subsequent RL stage.
- **Stage II — RL with an intent-drift-aware reward, via GRPO.** Train the attacker to elicit
  valid multi-turn adversarial prompts while holding the same harmful objective. The
  intent-drift-aware reward is stated to combine three components: **intent alignment**,
  **compliance risk**, and **level of detail**.

### Reported headline result (from abstract, UNVERIFIED by us)

Average **80.1% ASR@1** across three closed- and open-source victim models on AdvBench,
reported as +33.9 points over prior SOTA. We have not reproduced or independently checked
this number; it is quoted from the abstract only.

---

## 2. Code availability

**GitHub repo:** https://github.com/fmmarkmq/SEMA — repository is PUBLIC and exists (VERIFIED 2026-07-25).

**Executable code: NOT released.** The README states the full code is under review by Microsoft
Research and cannot be publicly released at this time; direct access is offered only after the
requester agrees to a "SEMA Code Access Terms and Responsible Use Agreement." Contact listed:
`mingqian.feng@rochester.edu`.

What the repo currently exposes (per README fetch, UNVERIFIED at file level since we did not clone):
- README with project overview and ICLR 2026 acceptance note
- a requirements file
- bash script templates for the two training stages (prefilling self-tuning; RL)
- paper reference

> Caveat: the repo contents above come from a single web fetch of the README on 2026-07-25, not a
> local clone (clone/download is out of scope for this sprint phase). Treat file-level claims as
> UNVERIFIED until access is granted and the repo is inspected directly.

---

## 3. Prior access attempts in THIS repository

**Result: ABSENT.** A repository-wide search for a whole-word `SEMA` reference
(`grep -rwil "sema" docs/ scripts/`) returns only:
- `docs/SPRINT_COMPLETION_PLAN_MATAN_MAHMOOD.md` (the planning doc that scheduled this phase)

No prior email, no access request, no correspondence, no cloned SEMA code, and no SEMA-derived
scripts exist anywhere in the tree as of 2026-07-25. The sprint plan itself confirms this at §73:
"SEMA / multi-turn attacker-policy learning. **No code, no simulator exists** (verified)."

This document + `scripts/multiturn_simulator.py` (skeleton) are the first SEMA-related artifacts.

---

## 4. Draft academic code-access request email

> Fill the `[SENDER ...]` placeholders before sending. Send from an academic address.

```
To: mingqian.feng@rochester.edu
Cc: [SENDER ADVISOR EMAIL — e.g. Prof. Sharif / Prof. Mahmood]
Subject: Academic code-access request — SEMA (arXiv 2602.06854), ICLR 2026

Dear Mingqian Feng and co-authors,

I am [SENDER NAME], a [SENDER ROLE, e.g. graduate student] at [SENDER INSTITUTION],
working under [SENDER ADVISOR] on the safety evaluation of multi-turn jailbreak attacks
against reasoning ("thinking") LLMs. We have been studying SEMA (arXiv 2602.06854) and
would like to build on your two-stage approach (prefilling self-tuning + GRPO with the
intent-drift-aware reward) for a controlled academic red-teaming study.

Your GitHub README (github.com/fmmarkmq/SEMA) notes that the full code is under Microsoft
Research review and available on request after agreeing to the SEMA Code Access Terms and
Responsible Use Agreement. We would be grateful to receive that agreement and, upon signing,
access to the training code.

Intended use is strictly non-production defensive research: reproducing the attacker-training
pipeline at academic compute scale to characterize and defend against multi-turn intent drift.
Results would be used only for academic publication with responsible-disclosure norms, and we
will honor any redistribution and citation restrictions you specify.

If helpful, I can share our IRB/ethics context and institutional affiliation letter.

Thank you for making the work available and for considering this request.

Best regards,
[SENDER NAME]
[SENDER ROLE], [SENDER INSTITUTION]
[SENDER EMAIL]
[SENDER ADVISOR / LAB]
```

---

## 5. Two reproduction tracks (neither started)

Both tracks are DESIGN-ONLY at this date; **neither has been started** (no data, no training,
no checkpoints).

### Track A — Paper-faithful reproduction (BLOCKED on §2 access)

Reproduce SEMA exactly as published:
- **Stage I: prefilling self-tuning** — SFT the attacker on self-generated, non-refusal,
  well-structured multi-turn adversarial prompts seeded with a minimal prefix.
- **Stage II: GRPO with the intent-drift-aware reward** — the three-part reward (intent
  alignment + compliance risk + level of detail), same victim/benchmark setup as the paper
  (AdvBench; three victim models) to target the reported ~80.1% ASR@1 regime.

**Blocker:** requires the authors' released code and exact reward/hyperparameter definitions,
which are gated behind the access agreement (§2). Cannot begin until access is granted.

### Track B — Scaled academic reimplementation (independent of §2, still not started)

A from-scratch reimplementation at the compute available in this project (L40S nodes; see
project SLURM rules), reusing this repo's existing infrastructure:
- **Victim model loading** → `poc_stage4/qwen3_model.py`
  (`load_qwen3_model` / `load_gemma4_model`).
- **Success judging** → `poc_stage2b/judge.py` (`score_with_gemini_judge`) and/or the
  StrongREJECT evaluator under `strong_reject/strong_reject/strong_reject/evaluate.py`.
- **Multi-turn rollout** → `scripts/multiturn_simulator.py` (skeleton delivered this sprint;
  provides the open-loop-plan vs closed-loop baseline harness the RL loop would sit on top of).

**Status:** the simulator skeleton exists but its core methods are `NotImplementedError` stubs;
no reward model, no GRPO loop, and no attacker-policy training have been written. A smoke test of
the simulator (see the script) is a prerequisite before any RL is attempted. This track documents
the scaled-reimplementation gap rather than claiming paper reproduction (see sprint plan §310).

---

## 6. Open-question / gate mapping

Per `docs/SPRINT_COMPLETION_PLAN_MATAN_MAHMOOD.md`:
- Open question 7 ("SEMA reproducible at available compute?"): still OPEN.
- Definition-of-done for the SEMA workstream ("SEMA access documented + ≥ scaled multi-turn
  evaluated"): the **access-documented** half is satisfied by this file; the
  **scaled-multi-turn-evaluated** half is NOT (no runs).

---

## 7. Verification log (what was and was not checked)

| Claim | How checked | Status |
|---|---|---|
| arXiv 2602.06854 exists, title/authors/date | `WebFetch` arXiv abstract page, 2026-07-25 | VERIFIED |
| github.com/fmmarkmq/SEMA public, code not released, contact email | `WebFetch` repo README, 2026-07-25 | VERIFIED (single fetch; not cloned) |
| 80.1% ASR@1 / +33.9pp headline number | abstract text only | UNVERIFIED (quoted, not reproduced) |
| Repo file list (requirements, bash templates) | README fetch only, not a clone | UNVERIFIED at file level |
| No prior SEMA access request / code in this repo | `grep -rwil "sema" docs/ scripts/` | VERIFIED ABSENT |
| Victim loader + judge reuse targets exist | `ls` of cited paths | VERIFIED present |

---

*Sources: https://arxiv.org/abs/2602.06854 · https://github.com/fmmarkmq/SEMA ·
https://openreview.net/forum?id=6eSNG1VNkl ·
https://www.microsoft.com/en-us/research/publication/sema-simple-yet-effective-learning-for-multi-turn-jailbreak-attacks/*
