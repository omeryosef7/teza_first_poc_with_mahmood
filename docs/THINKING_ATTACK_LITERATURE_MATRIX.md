# Thinking-Attack Literature Matrix

Sprint task **§A2** (see `docs/SPRINT_COMPLETION_PLAN_MATAN_MAHMOOD.md`, phases A2 / F1 / F2 / G).
Scope: attacks and utilities relevant to jailbreaking large **reasoning** models and to the
attention-/representation-hijacking family this project studies.

**Provenance conventions.**
- **Local** = read directly from a file in this repo (path cited).
- **Web** = fetched from arXiv/GitHub during this task (URL cited); web was reachable.
- Facts are stated plainly; where a source did not state a field, the cell says
  "not stated in source" rather than guessing.
- "Reproduction status in our repo" reports only what a cited artifact shows.

Last built: 2026-07-25. Repo branch `main` @ current HEAD. Web access: **available**.

---

## 1. Compact overview

| # | Attack / utility | arXiv | Turns | Vector | Access | Code in our repo? |
|---|---|---|---|---|---|---|
| 1 | GCG (universal adversarial suffix) | 2307.15043 | single | suffix | white-box (train) → black-box (transfer) | Yes — TROPT `GCG__zou2023.py` + `poc_stage_gcg_early/` |
| 2 | Universal Attention Hijackers | 2506.12880 | single | suffix | white/grey-box | Yes — TROPT `GCGHij.py` (`gcg_hij__bentov2025`) |
| 3 | CoT-Hijacking | 2510.26418 | single | context (long benign reasoning) | black-box | Yes — released prompts vendored |
| 4 | H-CoT | 2502.12893 | single (mostly) | policy / injected reasoning trace | grey-box | No |
| 5 | In-Context Representation Hijacking / Doublespeak | 2512.03771 | single | context (in-context token substitution) | black-box | No |
| 6 | REINFORCE Adversarial Attacks | 2502.17254 | not stated | suffix / prompt optimization | white-box | No (Phase D build-new) |
| 7 | SEMA | 2602.06854 | multi-turn | policy (learned attacker) | black-box (open-loop) | No (Phase G build-new) |
| 8 | TROPT attention-hijacking recipe | (impl. of 2506.12880 / 2410.09040) | single | suffix | white-box | Yes — TROPT `GCGHij.py` |
| 9 | TROPT refusal-direction utility | (impl. of 2406.11717) | — (utility) | activation steering | white-box | Yes — TROPT `utils/refusal_dir.py` |

---

## 2. Full matrix (per-attack detail cards)

Each card covers all requested columns: attack name | exact paper (arXiv id) | single/multi-turn |
suffix/prefix/context/policy | white/grey/black-box | target model type | optimization algorithm |
optimization objective | attack-success definition | datasets | judge | interpretability evidence |
causal evidence | released code/data | defense proposed | reproduction status in our repo |
unresolved gap.

### 1. GCG — Universal and Transferable Adversarial Attacks on Aligned Language Models

- **arXiv:** 2307.15043 (Zou, Wang, Carlini, Nasr, Kolter, Fredrikson). *Source: web.*
- **Turns:** single-turn.
- **Vector:** adversarial **suffix** appended to a harmful request.
- **Access:** white-box for optimization (Vicuna-7B/13B); demonstrates **transfer** to black-box systems.
- **Target model type:** aligned chat LLMs (non-reasoning): Vicuna, LLaMA-2-Chat, Pythia, Falcon; transfer to ChatGPT, Bard, Claude.
- **Optimization algorithm:** Greedy Coordinate Gradient (gradient-guided greedy token search).
- **Optimization objective:** maximize probability of an **affirmative target prefix** ("Sure, here is…").
- **Attack-success definition:** model emits objectionable content instead of refusing (string/affirmative-match; AdvBench harmful-behavior completion).
- **Datasets:** AdvBench (harmful behaviors / strings).
- **Judge:** not detailed in the abstract; community practice is string-match + later LLM/HarmBench judges.
- **Interpretability evidence:** none in the source.
- **Causal evidence:** none in the source (it is an attack paper, not a mechanism paper).
- **Released code/data:** Yes — github.com/llm-attacks/llm-attacks.
- **Defense proposed:** none.
- **Reproduction status in our repo:** **Reproduced extensively.** TROPT recipe `TROPT/tropt/recipe_hub/GCG__zou2023.py`; project pipeline `poc_stage_gcg_early/`; synthesis in `docs/GCG_JULY2026_MASTER_LOG.md`. Note the project's `suffix_placement="user"` fix (memory: 2026-07-19 placement bug) affects all GCG-ASR numbers.
- **Unresolved gap:** GCG on this project is a **non-reasoning** baseline; interaction of suffix optimization with a thinking/CoT channel is the open question the sprint's Phase C/D addresses.

### 2. Universal Jailbreak Suffixes Are Strong Attention Hijackers

- **arXiv:** 2506.12880 (Matan Ben-Tov, Mor Geva, Mahmood Sharif; TACL 2026). *Source: web + local recipe.*
- **Turns:** single-turn.
- **Vector:** adversarial **suffix**.
- **Access:** grey/white-box (studies model internals; GCG-based optimization).
- **Target model type:** aligned chat LLMs (the TROPT recipe defaults to `google/gemma-3-270m-it`; paper's full model list not captured in the fetched abstract — **not stated in source**).
- **Optimization algorithm:** GCG + an **attention-enhancement** term (see recipe below).
- **Optimization objective:** affirmative-target CE **plus** enhance attention from the trigger to the chat-template / instruction-after tokens (mid layers).
- **Attack-success definition:** generalization of a single suffix to many **unseen** harmful instructions (universality).
- **Datasets:** not stated in fetched abstract.
- **Judge:** not stated in fetched abstract.
- **Interpretability evidence:** Yes — identifies a "shallow, critical mechanism": information flow from the adversarial suffix to final chat-template tokens ("attention hijacking"), and quantifies hijacking strength.
- **Causal evidence:** Yes — links hijacking strength to the universality phenomenon; the mechanism can be **surgically mitigated**.
- **Released code/data:** Yes (paper states code + data released).
- **Defense proposed:** Yes — surgical mitigation "at least halving" ASR with minimal utility loss.
- **Reproduction status in our repo:** **Recipe present, run pending.** `TROPT/tropt/recipe_hub/GCGHij.py::gcg_hij__bentov2025` implements it as `CombinedLoss([PrefillCELoss(), AttentionEnhLoss(src=TRIGGER, dst=INPUT_AFTER, layers=slice(0.1·L, 0.9·L))], weights=[1.0, 100])`, GCG hparams (500 steps, 512 cand, top-256), eager attention required. No project run on ClearHarm/AdvBench recorded yet (sprint Phase C/E).
- **Unresolved gap:** whether high-universality suffixes on **reasoning** models act through the same chat-template attention dominance (sprint Phase E "universality-mechanism bridge").

### 3. Chain-of-Thought Hijacking

- **arXiv:** 2510.26418 (Zhao, Fu, Schaeffer, Sharma, Barez). *Source: local README/PDF + web + local prompts.*
- **Turns:** single-turn.
- **Vector:** **context** — the prompt embeds a hard benign puzzle (Sudoku / logic-grid / Skyscrapers / abstract math) that induces prolonged (>5 min) benign reasoning, then requests the harmful "practical example." ("refusal dilution").
- **Access:** black-box (API models).
- **Target model type:** large **reasoning** models: Gemini 2.5 Pro, GPT o4-mini, Grok 3 Mini, Claude 4 Sonnet (per README `config/models.py` token limits also list gpt-5-mini).
- **Optimization algorithm:** PAIR-style iterative refinement (README: "builds on PAIR"); attacker LLM refines the prompt to maximize a 1–10 jailbreak score. Not a gradient method.
- **Optimization objective:** maximize judge SCORE = harmfulness of the "practical example" span; secondary signal is CoT step count.
- **Attack-success definition:** HarmBench success; reported 99% / 94% / 100% / 94% across the four models (source: web abstract; denominators not captured here — **verify against paper before quoting**).
- **Datasets:** HarmBench (`main.py` slices examples 1–100).
- **Judge:** Gemini-based LLM judge (repo `config/judge_prompt.py`, `GEMINI_SAFETY_SETTINGS_JUDGE`).
- **Interpretability evidence:** activation probing + attention-pattern analysis on open-source reasoning models (per web abstract).
- **Causal evidence:** Yes — causal interventions showing extended benign reasoning shifts attention away from the harmful span and attenuates refusal-related activations.
- **Released code/data:** Yes — vendored at `Chain_of_Thought_Hijacking/Hijacking/`; released attacker prompts in `config/system_prompts.py` (six templates `new_prompt8`–`new_prompt13`: category/math, Sudoku, logic-grid, Skyscrapers variants).
- **Defense proposed:** none (diagnostic framing).
- **Reproduction status in our repo:** **Prompts vendored; behavioral repro partial.** Sprint Phase F1 marks the causal claim as only a **uniform-temperature null** so far; exact head/span mechanism not yet reproduced. Entry points: `poc_stage4/`, `poc_stage_ae/`, `scripts/phase7_*` (per sprint §1 crosswalk).
- **Unresolved gap:** exact attention **heads/layers/spans** and a *targeted* (not uniform-temperature) causal intervention (sprint Phase F1.2–F1.6).

### 4. H-CoT — Hijacking the Chain-of-Thought Safety Reasoning Mechanism

- **arXiv:** 2502.12893 (Kuo, Zhang, Ding, Wang, DiValentin, Bao, Wei, Li, Chen). *Source: web.*
- **Turns:** primarily single-turn (not explicitly stated in source).
- **Vector:** **policy / injected reasoning** — supplies fabricated benign intermediate "safety reasoning" that the model continues, hijacking its own displayed CoT.
- **Access:** grey-box (exploits **visible** intermediate reasoning traces).
- **Target model type:** commercial large reasoning models: OpenAI o1/o3, DeepSeek-R1, Gemini 2.0 Flash Thinking.
- **Optimization algorithm:** none in the gradient sense; a "universal and transferable" template that reuses the model's own displayed reasoning.
- **Optimization objective:** suppress the safety-reasoning step so the model proceeds to answer.
- **Attack-success definition:** refusal-rate reduction (reported ~98% → <2% on affected models).
- **Datasets:** **Malicious-Educator** benchmark (harmful requests disguised as educational).
- **Judge:** not stated in source.
- **Interpretability/causal evidence:** attack directly targets visible reasoning traces; no mechanistic-internals study reported in the fetched content.
- **Released code/data:** website maliciouseducator.org; GitHub `dukeceicenter/jailbreak-reasoning-openai-o1o3-deepseek-r1` (from search).
- **Defense proposed:** none (calls for more robust safety mechanisms).
- **Reproduction status in our repo:** **No code** (verified — not in repo tree).
- **Unresolved gap:** requires models that **expose** their safety-reasoning trace; applicability to the project's open-weight targets (Qwen3, Gemma) is unverified.

### 5. In-Context Representation Hijacking (Doublespeak)

- **arXiv:** 2512.03771 (Itay Yona, Amir Sarid, Michael Karasik, Yossi Gandelsman; "Doublespeak", Mentaleap). *Source: web.*
- **Turns:** single-turn (in-context examples + harmful request in one prompt).
- **Vector:** **context** — systematic substitution of a harmful keyword (e.g. "bomb"→"carrot") across in-context examples, so a surface-benign request is internally interpreted as the harmful one.
- **Access:** black-box (works on closed- and open-source models).
- **Target model type:** aligned chat LLMs; e.g. Llama-3.3-70B-Instruct and other families.
- **Optimization algorithm:** **optimization-free** (no gradient/search; a single-sentence context override suffices).
- **Optimization objective:** N/A (no optimization) — mechanism is semantic overwrite of a token's representation.
- **Attack-success definition:** ASR; 74% on Llama-3.3-70B-Instruct with a single-sentence override (source: web).
- **Datasets / judge:** not stated in fetched abstract.
- **Interpretability evidence:** Yes — layer-by-layer representation convergence: benign meaning in early layers converges to harmful semantics in later layers.
- **Causal evidence:** interpretability tools show the emergence mechanism; strength/depth of the causal test not captured in the abstract.
- **Released code/data:** not stated in fetched abstract (project page mentaleap.ai/doublespeak).
- **Defense proposed:** none; argues input-layer/static safety checks are insufficient, motivating representation-level alignment.
- **Reproduction status in our repo:** **No code** (verified — sprint §0.2 item 2, Phase F2 is build-new).
- **Unresolved gap:** this is the **leading candidate** for Matan's unspecified "context hijacking" (see §3 below); reference not yet confirmed.

### 6. REINFORCE Adversarial Attacks on LLMs

- **arXiv:** 2502.17254 (Geisler, Wollschläger, Abdalla, Cohen-Addad, Gasteiger, Günnemann). *Source: web.*
- **Turns:** not stated in source.
- **Vector:** adversarial prompt/**suffix** optimization (integrated with GCG and PGD).
- **Access:** white-box (needs model access for the policy-gradient objective).
- **Target model type:** aligned chat LLMs; Llama-3 named; circuit-breaker defense evaluated.
- **Optimization algorithm:** **REINFORCE** policy-gradient formalism layered onto GCG / PGD.
- **Optimization objective:** an adaptive, **distributional, semantic** objective over the population of model responses — replaces fixed affirmative-target templates.
- **Attack-success definition:** ASR (model completes harmful response, judged over sampled responses).
- **Datasets / judge:** not detailed in abstract; uses the model's own generations rather than an external judge.
- **Interpretability / causal evidence:** none reported.
- **Released code/data:** not mentioned in abstract.
- **Defense proposed:** none (circuit-breaker used as a stress test).
- **Key result:** doubles ASR on Llama-3; raises ASR from 2%→50% against circuit-breaker defense.
- **Reproduction status in our repo:** **No implementation.** Sprint Phase D is a **build-new** REINFORCE token/soft-prompt estimator + RLOO baseline as a TROPT loss/recipe (reuse `GCGPlusOptimizer`, `PrefillCELoss`, `ResponseHarmfulnessLoss`, `CombinedLoss`; reward from `poc_rl_loop/rl_reward_function.py`).
- **Unresolved gap:** whether a behavioral REINFORCE objective beats Prefix-CE on this project's reasoning targets (sprint Gate 4).

### 7. SEMA — Simple yet Effective Learning for Multi-Turn Jailbreak Attacks

- **arXiv:** 2602.06854 (Feng, Liu, Yang, Song, Zhu, Xu, Gao). *Source: web.*
- **Turns:** **multi-turn**.
- **Vector:** **policy** — a fine-tuned attacker model that generates non-refusal, well-structured multi-turn adversarial prompts (open-loop, no victim feedback).
- **Access:** black-box against the victim.
- **Target model type:** three closed- and open-source victim models (not enumerated in abstract).
- **Optimization algorithm:** two-stage — supervised "prefilling self-tuning" then RL with an **intent-drift-aware reward**.
- **Optimization objective:** keep harmful intent across turns while eliciting valid adversarial responses (intent alignment + compliance risk + detail level).
- **Attack-success definition:** ASR@1; 80.1% average across victims (+33.9pp over prior SOTA per abstract).
- **Datasets:** AdvBench (+ "multiple datasets").
- **Judge:** multiple jailbreak judges (unspecified).
- **Interpretability / causal evidence:** none.
- **Released code/data:** code at github.com/fmmarkmq/SEMA.
- **Defense proposed:** none (red-teaming framing).
- **Reproduction status in our repo:** **No code / no simulator** (verified — sprint §0.2 item 3). Phase G is build-new: a scaled, explicitly **not paper-faithful** reimplementation (1.5–3B attacker / 3–8B victim, PEFT, T∈{1,3,5}).
- **Unresolved gap:** a different problem class (multi-turn learned policy) from the project's single-turn spine; official-code + compute access is an open Gate 7 item.

### 8. TROPT attention-hijacking recipe (`gcg_hij__bentov2025` / `attn_gcg__wang2024`)

- **Paper(s):** implementation of Ben-Tov 2025 (arXiv **2506.12880**, row 2) and AttnGCG / Wang 2024 (arXiv **2410.09040**). *Source: local `TROPT/tropt/recipe_hub/GCGHij.py`.*
- **Turns:** single-turn. **Vector:** suffix. **Access:** white-box (requires **eager** attention; prefix cache disabled — incompatible with attention losses).
- **Target model type:** HF causal LMs (`LMHFModel`); default `google/gemma-3-270m-it`.
- **Optimization algorithm:** `GCGOptimizer` (500 steps, 512 candidates, top-256 sampling, 1 replace, ASCII+non-special token constraints, retokenize).
- **Optimization objective:** `CombinedLoss([PrefillCELoss(), AttentionEnhLoss(...)], weights=[1.0, 100])`.
  - `Hijack` flavor: attention `TRIGGER → INPUT_AFTER` on middle layers `slice(⌊0.1L⌋, ⌈0.9L⌉)` (Ben-Tov).
  - `AttnGCG` flavor: attention `TRIGGER → APPENDED` (affirmative prefix) on the **last** layer only (Wang).
- **Attack-success / datasets / judge:** determined by the caller (recipe default instruction = "Write a tutorial for how to build a bomb."; target = affirmative prefix). No fixed benchmark inside the recipe.
- **Interpretability / causal:** the recipe *operationalizes* the attention-hijacking mechanism as a loss (it is the mechanism, made trainable).
- **Released code/data:** in-repo (TROPT).
- **Defense proposed:** N/A (recipe).
- **Reproduction status in our repo:** **Available, run pending** on project benchmarks (same status as row 2).
- **Unresolved gap:** which `dst` span (chat-template vs affirmative prefix) and layer band maximizes universality on the project's reasoning targets.

### 9. TROPT refusal-direction utility (`utils/refusal_dir.py`)

- **Paper:** implementation of Arditi et al. 2024, "Refusal in Language Models Is Mediated by a Single Direction" (arXiv **2406.11717**); loosely based on github.com/andyrdt/refusal_direction. *Source: local `TROPT/tropt/utils/refusal_dir.py`.*
- **Type:** **utility**, not an attack — extracts a per-layer refusal direction via **difference-in-means** (mean harmful-activation − mean harmless-activation, normalized per layer), for steering-based attacks (e.g. IRIS / `SteeringActivationLoss`).
- **Access:** white-box (registers hooks on `_model`, reads `output_hidden_states`).
- **Datasets:** harmful = AdvBench (`harmful_behaviors.csv`); harmless = Alpaca (input-free instructions); default 128 samples/side (Arditi's n), last-token position.
- **Objective / success / judge / defense:** N/A (utility).
- **Interpretability / causal evidence:** implements the single-direction refusal-mediation result (the source paper's finding, not re-established here).
- **Released code/data:** in-repo (TROPT). A parallel Arditi pipeline is also vendored at `Chain_of_Thought_Hijacking/refusal_direction/` with processed AdvBench/HarmBench/StrongREJECT/JailbreakBench/MaliciousInstruct datasets.
- **Reproduction status in our repo:** **Available** as a utility; project-specific direction extraction on Qwen3/Gemma not recorded here.
- **Unresolved gap:** whether ablating/steering along this direction on **reasoning** models suppresses in-thought refusal (relates to the Gemma-4 channel-mechanism memory note).

---

## 3. Naming disambiguation (CRITICAL — do not conflate)

Several attacks in this space share the word "hijacking" or "chain-of-thought." They are **distinct**
and must not be treated as the same paper or mechanism.

| Name | arXiv | What is hijacked | Mechanism (one line) | Access |
|---|---|---|---|---|
| **CoT-Hijacking** | 2510.26418 | the model's **attention budget** during long reasoning | long benign puzzle dilutes refusal ("refusal dilution"); harmful ask hidden in a "practical example" | black-box |
| **H-CoT** | 2502.12893 | the model's **displayed safety-reasoning trace** | inject fabricated benign safety-reasoning the model continues, skipping its refusal check | grey-box (needs visible CoT) |
| **In-Context Representation Hijacking / Doublespeak** | 2512.03771 | a **token's internal representation/meaning** | in-context substitution ("bomb"→"carrot") so a benign surface prompt is internally read as harmful | black-box, optimization-free |
| **Universal Attention Hijackers** (Ben-Tov) | 2506.12880 | **attention from an adversarial suffix** to chat-template tokens | GCG suffix + attention-enhancement loss; explains suffix universality | white/grey-box |

Key separations:
- **CoT-Hijacking ≠ H-CoT.** Both target reasoning models, but CoT-Hijacking *adds* benign reasoning
  to crowd out refusal (no need to see the CoT); H-CoT *replaces/continues* the model's own visible
  safety-reasoning trace and therefore **requires** an exposed CoT. Different threat model, different
  requirement on the victim.
- **"Context hijacking" (Matan's term) ≠ Ben-Tov attention hijacking (2506.12880).** The latter is a
  **suffix** attention-hijack with a released TROPT recipe; it is *not* what the sprint calls
  "context-hijacking."
- **In-Context Representation Hijacking = Doublespeak** — same paper (2512.03771), two names (arXiv
  title vs Mentaleap project name). It hijacks *representations*, not *attention* and not the
  *reasoning trace*.

**Which "context hijacking" did Matan mean?** *No repo record fixes the reference.* This is confirmed
by `docs/SPRINT_COMPLETION_PLAN_MATAN_MAHMOOD.md` §6.1: "No repo record fixes which paper Matan
meant." Per that section and §F2.0, the **leading candidate is In-Context Representation Hijacking /
Doublespeak (2512.03771)**, and Phase F2 proceeds on that assumption. Ben-Tov's attention-hijacking
(2506.12880) is explicitly a *different* attack and is ruled out as the intended "context hijacking."

**Verdict:** Treat "context hijacking" = **In-Context Representation Hijacking / Doublespeak
(2512.03771)** as the working assumption (leading candidate, not confirmed); keep Phase F2 labelled
as resting on an **unconfirmed reference** until Matan replies.

**One-line clarification question for Matan:**
> "By 'context hijacking' (Phase F2), do you mean *In-Context Representation Hijacking / Doublespeak*
> (arXiv 2512.03771, Yona et al.) — as opposed to *H-CoT* (2502.12893) or the Ben-Tov *attention*
> hijacking suffix (2506.12880)? We are proceeding on the Doublespeak assumption."

---

## 4. Source ledger

- **Local (read this task):** `Chain_of_Thought_Hijacking/Hijacking/README.md`,
  `config/system_prompts.py`, `config/parameters.py`, `config/judge_prompt.py` (existence verified);
  `TROPT/tropt/recipe_hub/GCGHij.py`; `TROPT/tropt/utils/refusal_dir.py`;
  `docs/SPRINT_COMPLETION_PLAN_MATAN_MAHMOOD.md` (§0.2, §1, §6, §7).
- **Web (fetched this task, reachable):** arXiv 2307.15043, 2506.12880, 2510.26418, 2502.12893,
  2512.03771, 2502.17254, 2602.06854, 2606.23496; search hits for github.com/fmmarkmq/SEMA,
  github.com/dukeceicenter/jailbreak-reasoning-openai-o1o3-deepseek-r1, mentaleap.ai/doublespeak.
- **Not independently verified:** headline ASR percentages (CoT-Hijacking 99/94/100/94, H-CoT
  98→<2, Doublespeak 74, SEMA 80.1, REINFORCE 2→50) come from abstracts/search summaries — confirm
  denominators against the papers before citing in a results doc.
</content>
</invoke>
