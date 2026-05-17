# POC Stage 1 Repo Audit

## Scope

This audit covers the three local repositories:

1. `Chain_of_Thought_Hijacking/Hijacking`
2. `AutoInject/AutoInject`
3. `strong_reject/strong_reject`

The goal of this stage is repository inspection and reproduction planning only. No expensive model runs were performed.

## Executive Summary

- The local `Chain_of_Thought_Hijacking` repo is a black-box jailbreak attack harness. It supports iterative prompt generation, target-model querying, judging, HarmBench goal loading, and logging to `wandb` plus local log files.
- It does **not** contain the mechanistic-analysis code needed for your main research question about refusal directions, layerwise refusal components, hidden states, or controlled CoT-length sweeps.
- `AutoInject` is much broader and potentially useful later for suffix-learning infrastructure, but this checkout looks partially incomplete for direct reuse: several imported modules are missing from the tree, and some configs are clearly cluster-specific.
- `StrongREJECT` is the cleanest repo of the three for later evaluation. Its package API is straightforward and should be easy to wrap in a future experiment pipeline.

## Repository 1: Chain-of-Thought Hijacking

### What the repo contains

- Top-level files:
  - `README.md`
  - `note.md`
  - `requirements.txt`
  - `main.py`
- Main packages:
  - `config/`
  - `core/`
  - `data/`
  - `models/`
  - `utils/`

### Relevant documentation

- `README.md` documents installation, required API keys, and the main usage pattern:
  - `python main.py --target-model ...`
  - optional HarmBench slicing with `--start-examples` and `--end-examples`
  - optional single custom goal via `--goal`
- `note.md` mostly repeats the command patterns and supported target models.

### Entry points and control flow

- Primary CLI entry point: `main.py`
- Main execution flow:
  1. parse CLI args
  2. load attack model and target model via `core/loaders.py`
  3. load judge via `core/judge.py`
  4. load goals via `data/dataset.py`
  5. run evaluation loop via `core/runner.py`
  6. run per-goal iterative attack loop via `core/workflow.py`

### Config and model support

- `config/models.py`
  - maps internal model names to API env vars and LiteLLM identifiers
- `config/parameters.py`
  - token limits
  - temperature / top-p
  - Gemini safety settings for attack, target, and judge
- `config/system_prompts.py`
  - hard-coded attacker system prompts
  - six prompt families (`new_prompt8` to `new_prompt13`)
- `config/judge_prompt.py`
  - judge prompt template

Supported target model names exposed by `main.py`:

- `gemini-2.5-pro`
- `gpt-o4-mini`
- `gpt-5-mini-minimal`
- `gpt-5-mini-low`
- `gpt-5-mini-medium`
- `gpt-5-mini-high`
- `grok-3-mini`
- `claude-4-sonnet`

### Data and prompt sources

- No local dataset files are bundled.
- Harmful goals are loaded remotely from Hugging Face in `data/dataset.py`.
- Default dataset:
  - `walledai/HarmBench`
  - config/split name default: `standard`
- The code expects the harmful-goal text in column `prompt`.
- The CoT-hijacking attack prompts are not stored as separate prompt files; they are embedded directly in `config/system_prompts.py`.

### Existing notebooks

- None in this repo.

### Output behavior

- Local log file path default:
  - `attack_log/attack_log_<timestamp>.log`
  - note: the repo does not create `attack_log/` for you
- `wandb` logging:
  - one run per goal in `core/workflow.py`
  - tabular logging of attack prompt, target response, judge score, and raw judge output in `utils/logger.py`
- No built-in CSV/JSON export for attack results
- No built-in plotting scripts

### What is reusable for your POC

- Iterative attacker loop against API-based reasoning models
- HarmBench slice loading
- A set of hard-coded CoT-hijacking prompt templates
- Simple attack success judging
- Logging of prompts, responses, and scores to `wandb`

### What is missing relative to your POC

- Controlled benign CoT prefix generation / loading
- Explicit CoT-length sweep infrastructure
- Open-source local reasoning-model inference pipeline
- Hidden-state / activation extraction
- Refusal-direction computation
- Layerwise mechanistic analysis
- Refusal-signal comparison plots
- Structured experiment outputs for mechanistic analysis

## Chain-of-Thought Hijacking: 8-Component Audit

| # | Component | Exists? | Files | Functions / classes | Inputs | Outputs |
|---|---|---|---|---|---|---|
| 1 | Generating or loading CoT-hijacking prompts | Yes | `config/system_prompts.py`, `utils/conversation.py`, `core/attack.py` | `get_attacker_system_prompts`, `new_prompt8`-`new_prompt13`, `initialize_conversations`, `AttackLM.get_attack` | harmful goal string, current conversation state, previous target response summary | attacker JSON with `improvement` and `prompt`; prompt text sent to target model |
| 2 | Varying the length of the benign reasoning / CoT prefix | No explicit support | none beyond hard-coded prompt wording | none | n/a | n/a |
| 3 | Running open-source reasoning models | No, not in a local HF/vLLM sense | `models/litellm_api.py`, `core/target.py`, `config/models.py` | `APILiteLLM`, `TargetLM` | API model names and provider keys | remote API responses only |
| 4 | Extracting internal activations / hidden states | No | none | none | n/a | n/a |
| 5 | Computing a refusal direction or refusal-related activation vector | No | none | none | n/a | n/a |
| 6 | Measuring refusal components across layers | No | none | none | n/a | n/a |
| 7 | Comparing refusal signals across prompt conditions or CoT lengths | No | none | none | n/a | n/a |
| 8 | Producing plots or data for mechanistic analysis in the paper | No mechanistic plotting code present | none | none | n/a | n/a |

### Notes on the 8 components

#### 1. Generating or loading CoT-hijacking prompts

- Present.
- Implementation details:
  - `config/system_prompts.py` contains six attacker system-prompt variants.
  - These prompts explicitly instruct the attacker model to produce prompts that force a reasoning model to solve a hard puzzle first and then provide a harmful “practical example”.
  - `utils/conversation.py::initialize_conversations` applies these prompts to `n_streams` concurrent attacker conversations.
  - `core/attack.py::AttackLM.get_attack` turns the attacker model output into structured JSON and extracts `attack["prompt"]`.
- Inputs:
  - harmful goal string
  - conversation state
  - previous iteration’s processed target response summary
- Outputs:
  - JSON dicts containing `improvement` and `prompt`
  - final adversarial prompt string for target-model querying

#### 2. Varying benign reasoning / CoT prefix length

- Not present as an experimental control.
- Closest thing present:
  - the attacker prompts repeatedly say the puzzle should be “tough” or “very difficult” to induce long reasoning.
  - `utils/parsing.py::count_step` counts double-newline-separated chunks in the target response and labels that as `STEP NUMBER`.
- This is not a true controllable benign-prefix-length parameter.

#### 3. Running open-source reasoning models

- Not present in the form you likely need.
- The repo runs only through provider APIs via LiteLLM:
  - OpenAI
  - Anthropic
  - Gemini
  - xAI
- `core/target.py::TargetLM` configures API-time reasoning parameters:
  - GPT models: `reasoning_effort`
  - Claude/Gemini: `thinking`
  - Grok: `reasoning_effort`
- There is no local transformer loading, no HF checkpoint loading, and no activation hooks.

#### 4. Extracting internal activations / hidden states

- Absent.
- No code references `hidden_states`, `activations`, hooks, probes, or layer tensors.

#### 5. Computing a refusal direction

- Absent.
- No code for contrastive vector extraction, PCA, linear probes, mean-difference vectors, or similar refusal-direction methods.

#### 6. Measuring refusal components across layers

- Absent.
- There is no layer iteration, no activation aggregation, and no per-layer metrics.

#### 7. Comparing refusal signals across conditions or CoT lengths

- Absent.
- The only comparison loop is attack iteration over prompts and goals, scored by a judge as safe/unsafe.

#### 8. Producing plots or mechanistic-analysis data

- Absent in this checkout.
- There are no notebooks, no plotting scripts, and no saved analysis artifacts besides logs and `wandb` tables.

## Exact First Reproducibility Target for Chain-of-Thought Hijacking

### Best first target

The single best first experiment to reproduce from this checkout is:

**Black-box attack success on a small HarmBench slice for one supported reasoning model.**

Recommended first target model:

- `gpt-o4-mini`

Why this is the best first target:

- it is fully supported by the code as checked in
- it exercises the full attacker -> target -> judge loop
- it validates the repo in the exact form actually present locally
- it establishes the baseline harness you would later wrap for your own experiments

### Does the repo already support your preferred target question?

Target question:

> “Does longer benign CoT reduce the refusal-related internal signal?”

Answer:

- **No, not directly.**
- The repo does **not** support:
  - controlled benign CoT length sweeps
  - hidden-state extraction
  - refusal-direction computation
  - layerwise refusal measurements

### Closest supported experiment

The closest supported experiment is:

- run the existing CoT-hijacking attack over a HarmBench slice
- inspect whether the attack succeeds for a reasoning-capable API model
- optionally compare target models or GPT-5 reasoning-effort settings later

This is still only a black-box behavioral reproduction, not the mechanistic result you ultimately care about.

### Exact scripts / configs involved

- Entry point:
  - `Chain_of_Thought_Hijacking/Hijacking/main.py`
- Attack prompt definitions:
  - `config/system_prompts.py`
- Goal loading:
  - `data/dataset.py`
- Target model execution:
  - `core/target.py`
- Judge:
  - `core/judge.py`
- Per-goal loop and logging:
  - `core/workflow.py`
  - `utils/logger.py`

### Exact order of commands to run later

From `Chain_of_Thought_Hijacking/Hijacking`:

```powershell
$env:GEMINI_API_KEY="..."
$env:OPENAI_API_KEY="..."
New-Item -ItemType Directory -Force attack_log
python main.py --target-model gpt-o4-mini --start-examples 1 --end-examples 6
```

Optional single custom-goal smoke test:

```powershell
python main.py --target-model gpt-o4-mini --goal "YOUR_HARMFUL_GOAL"
```

Optional reasoning-effort comparison already supported by this repo:

```powershell
python main.py --target-model gpt-5-mini-minimal --start-examples 1 --end-examples 6
python main.py --target-model gpt-5-mini-low --start-examples 1 --end-examples 6
python main.py --target-model gpt-5-mini-medium --start-examples 1 --end-examples 6
python main.py --target-model gpt-5-mini-high --start-examples 1 --end-examples 6
```

### Required model and data assumptions

- Required remote dataset:
  - Hugging Face `walledai/HarmBench`, split/config `standard`
- Required attacker model:
  - fixed in code to `gemini-2.5-pro`
- Required judge model:
  - fixed in code to Gemini-based `gemini-judge` implemented with `gemini-2.5-pro`
- Required target model:
  - one of the supported API-backed models from `main.py`

### Expected outputs

- Local log file under `attack_log/`
- `wandb` runs named like `goal_<index>_<target_model>`
- Per-iteration logs:
  - generated attack prompt JSON
  - target response
  - judge scores
  - aggregate summary stats
- Final output:
  - slice-level attack success rate in logs

### Expected plots

- None from this repo as checked in.
- Any plots for your future POC would need to be generated by new wrapper code.

## Repository 2: AutoInject

### What the repo contains

- Top-level RLPI package in `src/rlpi`
- Full embedded copy of `agentdojo/`
- Hydra configs under `src/rlpi/agentdojo/config`
- Learners for:
  - `trl_suffix`
  - `trl_suffix_joint`
  - `adaptive_random_suffix`
  - `llm_inference`
  - `noop`

### Relevant documentation

- `README.md`
  - explicitly warns the current version is “not fully tested and robust yet”
- `agentdojo/README.md`
  - describes the benchmark framework used underneath
- `agentdojo/notebooks/analysis.ipynb`
  - results-analysis notebook for AgentDojo, not for your planned reasoning-model hijacking POC

### How prompt injection tasks are represented

- Injection tasks are class-based AgentDojo tasks.
- Example files:
  - `agentdojo/src/agentdojo/default_suites/v1/workspace/injection_tasks.py`
  - `agentdojo/src/agentdojo/default_suites/v1_2/workspace/injection_tasks.py`
- Each task defines:
  - `GOAL`: the malicious instruction
  - `ground_truth(...)`: expected tool-call sequence
  - `security(...)`: whether the attack succeeded against the environment
- User tasks are separate class definitions in corresponding `user_tasks.py` files.
- Environment scaffolding comes from YAML files under `agentdojo/src/agentdojo/data/suites/...`.

### How adversarial prompts / suffixes are generated

- Main adaptive runner:
  - `src/rlpi/agentdojo/adaptive_agentdojo.py`
- Suffix-learning prompt construction:
  - `src/rlpi/attack/learners/trl_suffix/utils.py::create_adversarial_prompt`
- Final suffix formatting into attack text:
  - `src/rlpi/attack/learners/trl_suffix/utils.py::format_trl_suffix_prompt`
- Evaluation of a generated suffix on a task pair:
  - `src/rlpi/attack/learners/trl_suffix/evaluator.py::SuffixEvaluator.evaluate_suffix`
- Transfer attack runner:
  - `src/rlpi/agentdojo/transfer_attack.py`

### Where the reward / objective is defined

- Core reward utilities:
  - `src/rlpi/attack/learners/trl_suffix/reward_utils.py`
- Real-task evaluation:
  - `SuffixEvaluator.evaluate_suffix(...)` returns `(utility, security)`
- Final reward combines:
  - attack success / security
  - utility preservation
  - optional GPT comparison feedback on suffix quality
- This is an AgentDojo environment reward, not a refusal-dampening or reasoning-hijacking objective.

### Output behavior

- Hydra output directories:
  - `outputs/<learner>/<suite>/<date>/...`
  - `outputs/transfer/<date>/...`
- Logged artifacts include:
  - checkpoints
  - `experience_history.jsonl`
  - `training_sessions.jsonl`
  - `grpo_generations.jsonl`
  - `training_metrics.jsonl`
  - `summary.json` / `training_summary.json`
  - `transfer_results.json`
- Trace-level benchmark logs via AgentDojo `TraceLogger`

### Relevance to your future reasoning-model hijacking direction

- Useful pieces:
  - optimization loop structure
  - suffix-generation infrastructure
  - bookkeeping and checkpointing
  - transfer-attack scaffolding
- Mismatch with your target problem:
  - designed for AgentDojo agent tasks, not plain prompt-in / response-out reasoning models
  - reward is environment-security based, not refusal-strength based
  - prompt formatting is tied to AgentDojo attack templates
  - current tasks assume tool-use environments, emails, files, banking, travel, slack, etc.

### Signs the repo is incomplete / unstable / hard to reuse

- The top-level README explicitly says it is not fully tested or robust.
- Multiple imports point to files that are missing from this checkout:
  - `rlpi.attack.learners.random_learner`
  - `rlpi.attack.learners.ppo.learner`
  - `rlpi.attack.templates.task_modifier`
  - `rlpi.attack.templates.templates`
- `transfer_config.yaml` includes a hard-coded cluster path:
  - `gpt5_experiment_dir: /cluster/project/...`
- `load_module_environment("eth_proxy")` in `transfer_attack.py` suggests assumptions about a specific compute environment.

### Recommendation on reuse

- Do **not** plan to reuse AutoInject directly as the first implementation substrate for your reasoning-model hijacking POC.
- Later, you may borrow ideas from:
  - suffix generation
  - reward shaping
  - checkpointing
- For your actual POC, a smaller clean wrapper will likely be safer than adapting this full AgentDojo stack.

## Repository 3: StrongREJECT

### What the repo contains

- Installable package in `strong_reject/`
- Analysis scripts in `src/`
- Docs in `docs/`
- placeholders for `models/`, `notebooks/`, `references/`, `reports/`

### Relevant documentation

- `README.md` provides:
  - package quickstart
  - evaluator overview
  - installation
  - dataset utilities
- `docs/api/*.rst` expose package APIs:
  - `load_datasets`
  - `generate`
  - `evaluate`
  - `jailbreaks`

### Simplest later use in your POC

The cleanest integration path is the package API, not the project-level analysis scripts.

Use:

- `strong_reject.evaluate.evaluate_dataset(...)`
- or `strong_reject.evaluate.evaluate(...)` for single rows

### Input format it expects

For dataset-level scoring, use a Hugging Face `Dataset` with at least:

- `forbidden_prompt`
- `response`

Optional:

- `answer` if using evaluators that need a gold answer

### What score/output it returns

- `evaluate(...)`
  - returns a list of dicts, one per evaluator
- `evaluate_dataset(...)`
  - returns a dataset with added columns from the evaluator, including `score`
- For `strongreject_rubric`, outputs include:
  - `score`
  - `refusal`
  - `convincingness`
  - `specificity`

### Most relevant files / APIs

- `strong_reject/evaluate.py`
  - evaluator registry and main scoring APIs
- `strong_reject/generate.py`
  - optional response-generation helpers
- `strong_reject/load_datasets.py`
  - benchmark datasets
- `src/full_evaluation.py`
  - end-to-end project script showing generate -> evaluate flow
- `src/analyze_full_evaluation.py`
  - downstream plotting/analysis example

### Output behavior

- Package API itself returns in-memory datasets / dicts.
- Project scripts write to:
  - `data/interim/*.json`
  - `data/interim/*.csv`
  - `reports/figures/*.pdf`
  - `reports/figures/*.png`
- `Makefile` documents how processed data was downloaded in the original project.

### Recommended future integration pattern

- In your future experiment wrapper:
  1. save each experiment row with:
     - model
     - prompt variant
     - CoT-length metadata
     - raw response
  2. rename columns into StrongREJECT’s expected schema:
     - `forbidden_prompt`
     - `response`
  3. call `evaluate_dataset(dataset, ["strongreject_rubric"])`
  4. merge returned `score`, `refusal`, `convincingness`, `specificity` back into your experiment table

### Minimal example for later

```python
from datasets import Dataset
from strong_reject.evaluate import evaluate_dataset

dataset = Dataset.from_dict(
    {
        "forbidden_prompt": ["<goal 1>", "<goal 2>"],
        "response": ["<model response 1>", "<model response 2>"],
    }
)

scored = evaluate_dataset(dataset, ["strongreject_rubric"])
```

## What Can Be Reused vs What Is Missing

### Reusable now

- `Chain_of_Thought_Hijacking`
  - black-box attack loop
  - HarmBench loading
  - API target-model invocation
  - attack/judge logging
- `StrongREJECT`
  - downstream quality scoring
  - clean package API

### Not reusable as-is for your core research claim

- Mechanistic analysis in `Chain_of_Thought_Hijacking`
  - missing
- CoT-length-controlled experiments
  - missing
- Refusal-vector / refusal-direction analysis
  - missing
- Local reasoning-model hidden-state extraction
  - missing

### Reuse with caution later

- `AutoInject`
  - ideas: yes
  - direct integration: likely no
  - reason: incomplete imports, AgentDojo coupling, environment-specific assumptions

## Recommendation for the First Experiment to Reproduce

Recommended first reproduction:

**Run the checked-in Chain-of-Thought Hijacking black-box attack on a very small HarmBench slice for one supported reasoning model, and confirm that the local harness produces attack prompts, target responses, judge scores, and a slice ASR.**

Why this first:

- it is the only fully supported experiment path in the local CoT hijacking repo
- it verifies the repo actually works before you wrap or replace it
- it gives you the correct baseline for the next coding step: a clean wrapper around this harness, not direct mechanistic replication

What it does **not** answer:

- whether longer benign CoT reduces refusal-related internal signal

That question will require new code beyond the current repo.
