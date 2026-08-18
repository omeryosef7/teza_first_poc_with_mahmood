"""role_probes.py — Userness / CoTness probes, ported from the Role-Confusion codebase (plan §11).

ADOPTED, NOT REINVENTED. The methodology and hyperparameters here come from
`doublespeak_causality/third_party/prompt_injection_role_confusion`
(Prompt Injection as Role Confusion), specifically
`experiments/role-analysis/02-train-role-probes.ipynb` cells 18/19/26 and
`utils/role_templates.py`. That code was sitting in this repo unused while §11 was marked
"if feasible"; this module exists so we use their design rather than a private reinvention.

WHAT IS TAKEN FROM THEM, AND WHY EACH PIECE MATTERS
  * `render_single_message(model_prefix, role, content)` — wraps ARBITRARY text as a single
    message in a given role. This is the content-constancy device §11 asks for: identical text,
    different role tag. We vendor their dispatcher and add a Llama-3 branch, which their repo
    does not ship (their model set is gpt-oss / Qwen3 / GLM / OLMo / Jamba / Apriel / Nemotron).
  * `SKIP_FIRST_N = 32` — drop the first 32 tokens of every role segment before training. The
    role tag itself sits at the segment start, so without this the probe learns to read the tag
    and reports ~100% while measuring nothing. This is their guard against precisely the
    "stupid probe" failure this sprint already hit once.
  * `C = 5e-3`, L2, `fit_intercept=True`, optional standardization — strong regularization, from
    their per-model `config/probe.yaml`. Note our own probe saturated at `C=1.0`; they had
    already solved that, three orders of magnitude away from the sklearn default.
  * GROUPED train/test split by conversation, never by token.
  * The **tagged / untagged / mistagged** evaluation triad (their cell 26). This is the validity
    test that makes a role probe mean anything:
        untagged   — the same content with NO role tags, concatenated
        tagged     — the content in its TRUE roles via the chat template
        mistagged  — the content wrapped in the WRONG role tag
    A probe that has learned *role* rather than *topic* must follow the TAG, not the content.
    If `P(user)` on mistagged-as-user text does not rise, the probe is measuring content and any
    "Userness predicts ASR" claim built on it is void.

DELIBERATE DEVIATIONS (with reasons)
  * sklearn instead of cuml — cuml is not installed here, and at our n the GPU path buys nothing.
  * `GroupShuffleSplit` instead of their `train_test_split` on unique prompt ids — same grouped
    semantics, expressed in the library we have.
  * Extraction site: their probes are trained on `post_attention_layernorm` output
    (`extraction_key='all_pre_mlp_hidden_states'`). Our patching machinery operates on the
    residual stream (block output), so we extract there instead and RECORD the choice, because
    their published `C` values are then not transferable and must be re-swept. This is flagged
    rather than silently inherited.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DS_DIR, FailureLedger, REPO_ROOT, RunDir, ds, read_jsonl, seed_everything  # noqa: E402

RC_DIR = os.path.join(REPO_ROOT, "doublespeak_causality", "third_party",
                      "prompt_injection_role_confusion")
if RC_DIR not in sys.path:
    sys.path.insert(0, RC_DIR)

# Their constants, kept at their values so results are comparable to the source work.
SKIP_FIRST_N = 32
DEFAULT_C = 5.0e-3
DEFAULT_MAX_ITER = 5000


# --------------------------------------------------------------------------- #
# Role rendering — vendored dispatcher + the Llama-3 branch their repo lacks
# --------------------------------------------------------------------------- #
def render_single_llama3(role: str, content: str) -> str:
    """Wrap arbitrary text as a single Llama-3 message.

    Written in the style of their `render_single_qwen3` and matching the official Llama-3.1
    template exactly (header id, double newline, eot). `cot` has no native slot in Llama-3, so it
    is rendered as an assistant turn whose content is a <thinking> block — which is precisely the
    forgery a CoTness probe should be able to spot, and matches how `prompt_families.wrap_role`
    renders the `cot_like` style.
    """
    if role in ("system", "user", "assistant"):
        return (f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>")
    if role == "cot":
        return ("<|start_header_id|>assistant<|end_header_id|>\n\n"
                f"<thinking>\n{content}\n</thinking><|eot_id|>")
    if role == "tool":
        return ("<|start_header_id|>ipython<|end_header_id|>\n\n"
                f"{content}<|eot_id|>")
    raise ValueError(f"Invalid role {role!r}")


def render_single(model_prefix: str, role: str, content: str, tool_name=None) -> str:
    """Dispatch to their renderer, falling through to our Llama-3 branch."""
    if model_prefix in ("llama3", "llama-3.1-8b-instruct", "llama3-8b"):
        return render_single_llama3(role, content)
    from utils.role_templates import render_single_message  # vendored, unmodified
    return render_single_message(model_prefix, role, content, tool_name=tool_name)


def build_role_conditions(model_prefix: str, segments: Sequence[Tuple[str, str]],
                          role_sep: str = "\n\n") -> Dict[str, str]:
    """Their cell-26 triad, for one conversation given as [(true_role, content), ...].

    Returns {"untagged", "tagged", "user_tagged", "cot_tagged", "tool_tagged"} — the SAME content
    in every case, differing only in the role markup. That is the whole point.
    """
    contents = [c for _, c in segments]
    out = {"untagged": role_sep.join(contents),
           "tagged": "".join(render_single(model_prefix, r, c) for r, c in segments)}
    for role in ("user", "cot", "tool"):
        out[f"{role}_tagged"] = render_single(model_prefix, role, role_sep.join(contents))
    return out


#: The conditions the triad is DEFINED by. The check below asserts these by NAME rather than by
#: counting how many conditions happened to be handed to it: "there are three of them and no two
#: collide" is an incidental property, "untagged, tagged and user_tagged are all present and no two
#: collide" is the identity of the contrast. `cot_tagged` / `tool_tagged` are extra arms and are
#: still checked for content and distinctness, they are just not required to exist.
TRIAD_CONDITIONS = ("untagged", "tagged", "user_tagged")


def check_triad_varies_only_markup(conds: Dict[str, str],
                                   contents: Sequence[str],
                                   required: Sequence[str] = TRIAD_CONDITIONS) -> Dict[str, object]:
    """The triad's own validity condition, as a CHECK rather than as a sentence.

    THREE things must hold for `build_role_conditions` to mean anything, and until 2026-08-19 the
    selftest checked none of them properly:

      0. the named conditions the triad is a contrast BETWEEN actually exist;
      1. every condition carries ALL the content (the triad varies markup, never text);
      2. the conditions are PAIRWISE distinct — if two of them coincide, the "same content,
         different role tag" contrast is not a contrast at that pair.

    (2) was written `conds["untagged"] != conds["tagged"] != conds["user_tagged"]`. Python chains
    that into `(a != b) and (b != c)`, which says NOTHING about `a != c`: with a renderer that
    returns its content unchanged, `untagged == user_tagged` and the assertion still passes. A guard
    that cannot fail the case it exists to catch is not a guard, and this repo has now shipped five
    of those. Returns a verdict dict instead of asserting so the failure can be inspected, counted
    and tested.

    (0) IS THE HOLE THE 2026-08-19 REWRITE OPENED AND THE VERIFICATION PASS CLOSED. The first
    version of this function derived `ok` from `all(content_complete.values()) and not collisions`,
    and BOTH of those are vacuously true over an empty mapping: `check_triad_varies_only_markup({},
    contents)` returned `ok: True`, and so did a `conds` that had simply lost `user_tagged`. That is
    the same vacuous-pass shape as `probes.check_leakage` over zero layers — a verdict from a check
    that ran over nothing — and here it was a REGRESSION as well: the chained assertion it replaced
    at least raised `KeyError` on a missing `user_tagged`, so the rewrite turned a loud failure into
    a silent pass. The required names are now part of the verdict.
    """
    missing = {name: [c for c in contents if c not in text] for name, text in conds.items()}
    content_ok = {name: not miss for name, miss in missing.items()}
    names = sorted(conds)
    collisions = [(a, b) for i, a in enumerate(names) for b in names[i + 1:]
                  if conds[a] == conds[b]]
    missing_conditions = [n for n in required if n not in conds]
    return {"ok": (not missing_conditions) and all(content_ok.values()) and not collisions,
            "required_conditions": list(required),
            "missing_conditions": missing_conditions,
            "content_complete": content_ok,
            "missing_content": {k: v for k, v in missing.items() if v},
            "colliding_pairs": collisions,
            "n_conditions": len(conds),
            "note": "pairwise distinctness is checked over ALL pairs; a chained `a != b != c` "
                    "never tested the (a, c) pair. The required conditions are checked by NAME: "
                    "an empty or truncated mapping passes every pairwise test vacuously."}


# --------------------------------------------------------------------------- #
# Probe training — their fit_lr / get_probe_result on sklearn
# --------------------------------------------------------------------------- #
def fit_lr(x_train, y_train, x_test, y_test, add_scaling: bool = False,
           C: float = DEFAULT_C, seed: int = 0):
    """Their `fit_lr`, on sklearn. Returns (model, accuracy, nll, y_pred)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    from sklearn.metrics import log_loss
    steps = []
    if add_scaling:
        steps.append(("scaler", StandardScaler()))
    steps.append(("clf", LogisticRegression(penalty="l2", max_iter=DEFAULT_MAX_ITER,
                                            fit_intercept=True, C=C, random_state=seed)))
    m = Pipeline(steps)
    m.fit(x_train, y_train)
    acc = float(m.score(x_test, y_test))
    prob = m.predict_proba(x_test)
    return m, acc, float(log_loss(y_test, prob, labels=sorted(set(y_train)))), m.predict(x_test)


def get_probe_result(sample_df: List[Dict], layer_hs: np.ndarray, roles_map: Dict[str, int],
                     add_scaling: bool = False, C: float = DEFAULT_C, seed: int = 0,
                     test_size: float = 0.1) -> Dict:
    """Their `get_probe_result`: grouped split by conversation, train on content tokens only.

    `sample_df` rows need `role`, `prompt_ix` (conversation id), `sample_ix` (row into layer_hs)
    and `token_in_seg_ix`. Rows with `token_in_seg_ix < SKIP_FIRST_N` must already be filtered
    out by the caller, exactly as their cell 19 does.
    """
    from sklearn.model_selection import GroupShuffleSplit
    idx = np.arange(len(sample_df))
    groups = np.array([r["prompt_ix"] for r in sample_df])
    y = np.array([roles_map[r["role"]] for r in sample_df])
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    tr, te = next(gss.split(idx, y, groups))

    if len(set(y[tr].tolist())) < len(roles_map):
        raise ValueError(f"missing roles in train split: {sorted(set(y[tr].tolist()))} "
                         f"vs roles_map {roles_map}")

    rows = np.array([r["sample_ix"] for r in sample_df])
    x_tr, x_te = layer_hs[rows[tr]], layer_hs[rows[te]]
    m, acc, nll, y_pred = fit_lr(x_tr, y[tr], x_te, y[te], add_scaling=add_scaling, C=C, seed=seed)

    per_role = {}
    inv = {v: k for k, v in roles_map.items()}
    for cls, name in inv.items():
        sel = y[te] == cls
        if sel.sum():
            per_role[name] = {"n": int(sel.sum()),
                              "recall": float((y_pred[sel] == cls).mean())}
    return {"acc": acc, "nll": nll, "n_train": int(len(tr)), "n_test": int(len(te)),
            "n_groups_train": int(len(set(groups[tr].tolist()))),
            "n_groups_test": int(len(set(groups[te].tolist()))),
            "per_role": per_role, "model": m, "roles_map": dict(roles_map)}


def score_roleness(model, X: np.ndarray, roles_map: Dict[str, int], role: str,
                   clip: float = 1e-6) -> np.ndarray:
    """Per-token P(role), their Userness/CoTness quantity. Clipped as they do."""
    if role not in roles_map:
        raise KeyError(f"{role!r} not in roles_map {roles_map}")
    p = model.predict_proba(X)[:, list(model.classes_).index(roles_map[role])]
    return np.clip(p, clip, 1.0 - clip)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true",
                    help="check the vendored renderers and the triad construction (CPU, no model)")
    ap.add_argument("--model-prefix", default="llama3")
    args = ap.parse_args()

    if args.selftest:
        segs = [("user", "The report describes an object near the bridge."),
                ("assistant", "It is logged in the inventory.")]
        conds = build_role_conditions(args.model_prefix, segs)
        print(f"role conditions built: {sorted(conds)}")
        contents = [c for _, c in segs]
        verdict = check_triad_varies_only_markup(conds, contents)
        for name, text in sorted(conds.items()):
            print(f"  {name:12s} len={len(text):4d} "
                  f"contains-all-content={verdict['content_complete'][name]}")
        if not verdict["ok"]:
            print(f"  TRIAD INVALID: missing_conditions={verdict['missing_conditions']} "
                  f"missing_content={verdict['missing_content']} "
                  f"colliding_pairs={verdict['colliding_pairs']}")
            return 1
        print(f"  pairwise-distinct over all {verdict['n_conditions']} conditions: OK")
        print("\nSKIP_FIRST_N =", SKIP_FIRST_N, " C =", DEFAULT_C,
              "  (their values, kept for comparability)")
        print("selftest OK")
        return 0

    print("nothing to do; use --selftest, or import this module")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
