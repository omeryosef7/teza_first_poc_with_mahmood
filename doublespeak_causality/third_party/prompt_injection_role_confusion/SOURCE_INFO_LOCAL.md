# SOURCE_INFO_LOCAL.md — upstream snapshot provenance

This file is **local to our project** and is not part of the upstream repository.

## Upstream

| Field | Value |
| --- | --- |
| Repository URL | https://github.com/role-confusion/prompt-injection-as-role-confusion |
| Paper | *Prompt Injection as Role Confusion* |
| Branch | `master` (upstream default branch) |
| Commit SHA | `ec333c40fd43fe991e1ebf66765051b6d7e35784` |
| Commit date | 2026-05-31T23:14:16Z |
| Commit message | `Cleanup` |
| Upstream `pushed_at` | 2026-05-31T23:14:20Z |
| License | MIT (see `LICENSE.md`, retained unmodified) |
| Retrieval date | 2026-08-14 |
| Retrieval method | `curl -L .../archive/refs/heads/master.zip` → `unzip` → `rsync` |
| Files | 110 |
| Size on disk | 7.3 MB |

Archive URL used:

```
https://github.com/role-confusion/prompt-injection-as-role-confusion/archive/refs/heads/master.zip
```

## This is NOT a Git repository

This directory is a **plain downloaded source snapshot**. It is deliberately:

- not a `git clone`;
- not a git submodule;
- not a git subtree;
- not a nested git repository.

No `.git/` directory exists here. Verified at import time with:

```
find third_party/prompt_injection_role_confusion -name .git   # returns nothing
```

The upstream `.gitattributes` and `.gitignore` files are retained as ordinary
files because they are part of the released source tree; they carry no
repository state.

## Snapshot discipline

Treat this tree as **frozen and read-only**.

- Do not modify upstream source in place.
- Do not "fix" upstream bugs here — record them in
  `docs/ROLE_CONFUSION_CODE_REVIEW.md` and handle them in our adaptation.
- Our own research code lives in `doublespeak_causality/src/probes/`, never here.
- If the snapshot ever needs refreshing, create a **new** dated directory and
  mark this one SUPERSEDED rather than overwriting it.

## Files we actually reused / adapted

Filled in as the adaptation proceeds. Authoritative mapping table lives in
`docs/ROLE_CONFUSION_CODE_REVIEW.md` § "Upstream → Our Implementation Mapping".

Code review complete 2026-08-14; no adaptation code written yet. Planned:

| Upstream file | Status | Where it lands in our tree |
| --- | --- | --- |
| `demo/simple_test_helpers.py` (`ReconstructableTextDataset`, `stack_collate`, `convert_outputs_to_df_fast`) | port ~as-is | `src/probes/probe_dataset.py` |
| `demo/role-probe-demo.ipynb` cell 4 (hook-based extractor) | adapt — retarget hook to post-block residual | `src/probes/activation_extraction.py` |
| `utils/probes.py::run_and_export_states` | adapt (batch→df+hs contract) | `src/probes/activation_extraction.py` |
| `utils/probes.py::run_projections` | port ~as-is | `src/probes/probe_projection.py` |
| `experiments/role-analysis/02-train-role-probes.ipynb` (`fit_lr`, `get_probe_result`) | adapt — sklearn, new split key, added metrics | `src/probes/contextual_identity_probe.py` |
| `experiments/cot-forgery-role-confusion/03-project-role-probes.ipynb` cell 14 (declared vs decoded identity) | concept reused, code rewritten | `src/probes/probe_dataset.py` |
| `experiments/.../04-analyze-injection-probe-results.ipynb` cell 19 (confusion→ASR quantile curve) | rewritten in Python | analysis scripts |
| `utils/loader.py`, `utils/role_assignments.py`, `utils/substring_assignments.py`, `utils/chat_templates/`, `utils/openrouter.py`, MoE/top-k paths, R plotting | **not reused** | — |

## Attribution requirement

Any code copied or adapted from this snapshot into our project source tree must
carry a header comment of the form:

```python
# Adapted from:
# role-confusion/prompt-injection-as-role-confusion
# commit ec333c40fd43fe991e1ebf66765051b6d7e35784
# MIT License — see third_party/prompt_injection_role_confusion/LICENSE.md
```
