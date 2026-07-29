"""
ds_common.py — Core reusable library for the Doublespeak-causality project.

Design goals (see DOUBLESPEAK_CAUSALITY_PLAN.md):
  * Reuse the official paper code in ../doublespeak (LogitLens, Patchscopes, attack).
  * Apply each model's official chat template and preserve native (list-valued) EOS
    (plan §5.9 — prior severe bug from EOS overwrite; do NOT repeat).
  * Robust multi-token target localization AFTER templating (plan §5.10, §8.1):
    the codeword token, the immediately following token, and answer tokens.
  * Matched Direct / Neutral / Doublespeak prompt construction (plan §7, §5.11).
  * Activation capture + patching primitives (plan §8, §9) built on forward hooks.

This module is intentionally dependency-light (torch + transformers) and holds NO
experiment logic — experiments live in the numbered scripts.
"""

from __future__ import annotations

import os
import sys
import json
import time
import socket
import subprocess
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Sequence, Tuple, Any

import torch

# Make the vendored official implementation importable (reuse, don't reimplement).
_HERE = os.path.dirname(os.path.abspath(__file__))
_DOUBLESPEAK_DIR = os.path.normpath(os.path.join(_HERE, "..", "doublespeak"))
if _DOUBLESPEAK_DIR not in sys.path:
    sys.path.insert(0, _DOUBLESPEAK_DIR)

PRIMARY_MODEL = "meta-llama/Llama-3.1-8B-Instruct"


# --------------------------------------------------------------------------- #
# Reproducibility / metadata
# --------------------------------------------------------------------------- #
def git_commit() -> str:
    """Current HEAD sha, for the plan §15 provenance record.

    `git` is not on PATH inside every conda env we run in (it lives in base), which
    silently degraded provenance to "unknown". Fall back to reading .git directly so
    the commit is recorded even without the binary.
    """
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=_HERE, stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        pass
    try:
        d = _HERE
        while True:
            gitdir = os.path.join(d, ".git")
            if os.path.exists(gitdir):
                break
            parent = os.path.dirname(d)
            if parent == d:
                return "unknown"
            d = parent
        if os.path.isfile(gitdir):  # worktree: ".git" is a file pointing elsewhere
            gitdir = open(gitdir).read().split("gitdir:", 1)[1].strip()
        head = open(os.path.join(gitdir, "HEAD")).read().strip()
        if head.startswith("ref:"):
            ref = head.split(" ", 1)[1].strip()
            ref_path = os.path.join(gitdir, ref)
            if os.path.exists(ref_path):
                return open(ref_path).read().strip()
            for line in open(os.path.join(gitdir, "packed-refs")):
                if line.rstrip().endswith(" " + ref):
                    return line.split()[0]
            return "unknown"
        return head
    except Exception:
        return "unknown"


def env_metadata() -> Dict[str, Any]:
    import transformers
    return {
        "hostname": socket.gethostname(),
        "git_commit": git_commit(),
        "python": sys.version.split()[0],
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "cuda_available": torch.cuda.is_available(),
        "gpu": (torch.cuda.get_device_name(0) if torch.cuda.is_available() else None),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


def set_seed(seed: int) -> None:
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# --------------------------------------------------------------------------- #
# Model loading (house standard: bfloat16 + SDPA; preserve native EOS)
# --------------------------------------------------------------------------- #
@dataclass
class LoadedModel:
    model: Any
    tokenizer: Any
    model_id: str
    revision: Optional[str]
    dtype: str
    device: str
    num_layers: int
    hidden_size: int
    eos_token_ids: List[int]

    def meta(self) -> Dict[str, Any]:
        # Build explicitly — do NOT asdict(self): it deep-copies EVERY field first,
        # including `model` (the whole nn.Module), which OOMs on large models
        # (28GB Qwen3 -> 2x28GB > L40S) before the model/tokenizer keys are filtered.
        d = {"model_id": self.model_id, "revision": self.revision, "dtype": self.dtype,
             "device": self.device, "num_layers": self.num_layers,
             "hidden_size": self.hidden_size, "eos_token_ids": self.eos_token_ids}
        d.update(env_metadata())
        return d


def load_model(
    model_id: str = PRIMARY_MODEL,
    dtype: torch.dtype = torch.bfloat16,
    device_map: str = "auto",
    revision: Optional[str] = None,
    attn_implementation: str = "sdpa",
) -> LoadedModel:
    """Load a chat model with the house-standard config and preserve native EOS.

    Deviations from the reference doublespeak code are deliberate (see
    PAPER_REPRODUCTION_NOTES D1-D3): bfloat16+SDPA instead of fp16, and we never
    overwrite the model's native (possibly list-valued) eos_token_id.
    """
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        revision=revision,
        torch_dtype=dtype,
        device_map=device_map,
        attn_implementation=attn_implementation,
    )
    model.eval()

    # Preserve native EOS; only add a pad token if genuinely missing.
    eos = model.generation_config.eos_token_id
    if eos is None:
        eos = tokenizer.eos_token_id
    eos_list = eos if isinstance(eos, (list, tuple)) else [eos]
    eos_list = [int(e) for e in eos_list if e is not None]
    if tokenizer.pad_token_id is None:
        # Use the first native EOS as pad (does not alter stopping behavior).
        tokenizer.pad_token_id = eos_list[0]

    cfg = model.config
    num_layers = getattr(cfg, "num_hidden_layers", None) or len(_get_layers(model))
    return LoadedModel(
        model=model,
        tokenizer=tokenizer,
        model_id=model_id,
        revision=revision,
        dtype=str(dtype),
        device=str(next(model.parameters()).device),
        num_layers=int(num_layers),
        hidden_size=int(getattr(cfg, "hidden_size")),
        eos_token_ids=eos_list,
    )


def _get_layers(model) -> Sequence:
    """Return the ModuleList of transformer blocks (LLaMA/Gemma/GPT variants)."""
    if hasattr(model, "model") and hasattr(model.model, "layers"):
        return model.model.layers
    if hasattr(model, "transformer") and hasattr(model.transformer, "h"):
        return model.transformer.h
    raise ValueError("Could not locate transformer layers on this model.")


# --------------------------------------------------------------------------- #
# Tokenization / target-token localization (plan §5.10, §8.1)
# --------------------------------------------------------------------------- #
@dataclass
class WordHit:
    """All occurrences of a word in a token sequence, with rich position info."""
    word: str
    variant: str                     # which tokenization matched (" word" / "word")
    subtoken_ids: List[int]          # the token ids that make up this occurrence
    spans: List[Tuple[int, int]]     # [start, end) index spans, one per occurrence
    first_idx: List[int]             # first-subtoken index per occurrence
    last_idx: List[int]              # last-subtoken index per occurrence

    @property
    def n(self) -> int:
        return len(self.spans)


def _encode_variants(tokenizer, word: str) -> List[Tuple[str, List[int]]]:
    """Return distinct (label, token_ids) tokenizations to search for."""
    out = []
    with_space = tokenizer.encode(f" {word}", add_special_tokens=False)
    if with_space:
        out.append((" word", with_space))
    no_space = tokenizer.encode(word, add_special_tokens=False)
    if no_space and no_space != with_space:
        out.append(("word", no_space))
    return out


def find_word_occurrences(tokenizer, input_ids: Sequence[int], word: str) -> WordHit:
    """Locate every occurrence of `word` (as a subtoken run) in input_ids.

    Tries space-prefixed and bare tokenizations (matches doublespeak/mech_interp
    but returns ALL occurrences and full span info, not just the last position).
    Raises if not found so callers never silently analyze the wrong position.
    """
    ids = list(int(i) for i in input_ids)
    variants = _encode_variants(tokenizer, word)
    # Collect matches from ALL tokenization variants (a word can appear both
    # sentence-initial and mid-sentence, tokenizing differently). Previously we
    # returned only the first variant with any match, which UNDERCOUNTS occurrences
    # (needed correct for attention-knockout over all codeword sites, plan §11).
    # Dedup by last-subtoken index, keeping the longest span at each (a longer
    # space-prefixed match subsumes a bare sub-match ending at the same token).
    by_last: Dict[int, Tuple[int, int, str, List[int]]] = {}  # last -> (start,end,variant,ids)
    for variant, tok_ids in variants:
        L = len(tok_ids)
        for i in range(len(ids) - L + 1):
            if ids[i:i + L] == tok_ids:
                last = i + L - 1
                prev = by_last.get(last)
                if prev is None or L > (prev[1] - prev[0]):
                    by_last[last] = (i, i + L, variant, tok_ids)
    if not by_last:
        raise ValueError(f"word {word!r} not found in token sequence (tried "
                         f"{[v for v, _ in variants]})")
    order = sorted(by_last)
    spans = [(by_last[l][0], by_last[l][1]) for l in order]
    return WordHit(
        word=word,
        variant="+".join(sorted({by_last[l][2] for l in order})),
        subtoken_ids=by_last[order[0]][3],   # ids of the first occurrence
        spans=spans,
        first_idx=[s for s, _ in spans],
        last_idx=[e - 1 for _, e in spans],
    )


@dataclass
class TargetPositions:
    """Positions to analyze for one prompt (plan §8.1: not only the codeword)."""
    codeword_last: int               # last subtoken of the last codeword occurrence
    codeword_all_last: List[int]     # last-subtoken idx of every occurrence
    following: Optional[int]         # token immediately after the last codeword
    seq_len: int                     # prompt length (answer tokens are >= this)

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def target_positions(tokenizer, input_ids: Sequence[int], codeword: str) -> TargetPositions:
    """Resolve the codeword position, the following token, and seq length.

    `following` is the position right after the last codeword subtoken (the
    downstream-transfer probe site, plan §8.1). None if the codeword is the last
    token (e.g. immediately before the generation prompt)."""
    hit = find_word_occurrences(tokenizer, input_ids, codeword)
    last = hit.last_idx[-1]
    seq_len = len(input_ids)
    following = last + 1 if (last + 1) < seq_len else None
    return TargetPositions(
        codeword_last=last,
        codeword_all_last=hit.last_idx,
        following=following,
        seq_len=seq_len,
    )


# --------------------------------------------------------------------------- #
# Matched prompt construction: Direct / Neutral / Doublespeak (plan §7)
# --------------------------------------------------------------------------- #
@dataclass
class Conditions:
    """The matched prompt strings for one (concept, codeword) item."""
    direct: str        # harmful concept used directly
    neutral: str       # codeword substituted, NO demonstrations
    doublespeak: str   # demonstrations + substituted query
    harmful_word: str
    codeword: str
    demos: str


def build_conditions(
    harmful_instruction: str,
    harmful_word: str,
    codeword: str,
    demos: str,
    instruction_prefix: str = "Do not reason, just",
    instruction_suffix: str = "given the context.",
) -> Conditions:
    """Construct the three matched conditions from one harmful instruction.

    Matching (plan §5.11): Direct and Neutral share identical wording except the
    harmful_word<->codeword swap; Doublespeak = Neutral query preceded by demos.
    `demos` are the in-context sentences (codeword already substituted in), e.g.
    from doublespeak.DoublespeakAttack.generate_in_context_examples or the fixed
    fallback. All prompts are RAW text; apply the chat template via `to_messages`.
    """
    assert harmful_word in harmful_instruction, (
        f"harmful_word {harmful_word!r} must appear in instruction to be swapped")
    substituted_query = harmful_instruction.replace(harmful_word, codeword)
    direct = f"{instruction_prefix} {harmful_instruction} {instruction_suffix}"
    neutral = f"{instruction_prefix} {substituted_query} {instruction_suffix}"
    doublespeak = f"{demos}\n\n{instruction_prefix} {substituted_query} {instruction_suffix}"
    return Conditions(
        direct=direct, neutral=neutral, doublespeak=doublespeak,
        harmful_word=harmful_word, codeword=codeword, demos=demos,
    )


def to_messages(prompt: str) -> List[Dict[str, str]]:
    """Wrap a raw prompt as a single user turn for apply_chat_template."""
    return [{"role": "user", "content": prompt}]


def apply_template(tokenizer, prompt: str, add_generation_prompt: bool = True,
                   enable_thinking: Optional[bool] = None) -> str:
    """Render the official chat template around a raw user prompt (plan D2).

    enable_thinking (Phase 7): None → model default (do NOT pass the kwarg); True/False → pass
    explicitly. Qwen3's default is thinking-ON, and enable_thinking=False must be passed EXPLICITLY
    (it injects an empty <think></think>); passing only True was a silent no-op — see qwen3_model.py.
    Tokenizers that don't accept the kwarg fall back to a standard call.
    """
    kwargs = dict(tokenize=False, add_generation_prompt=add_generation_prompt)
    if enable_thinking is not None:
        try:
            return tokenizer.apply_chat_template(to_messages(prompt), enable_thinking=enable_thinking, **kwargs)
        except (TypeError, ValueError):
            pass  # tokenizer doesn't support the kwarg → standard call
    return tokenizer.apply_chat_template(to_messages(prompt), **kwargs)


# --------------------------------------------------------------------------- #
# Activation capture (per-layer residual stream) — plan §8.1
# --------------------------------------------------------------------------- #
@torch.no_grad()
def forward_hidden_states(lm: LoadedModel, text: str) -> Dict[str, Any]:
    """Run a forward pass and return per-layer hidden states + input_ids.

    hidden_states is a tuple of (num_layers + 1) tensors: index 0 = embeddings,
    index L (1..num_layers) = residual stream AFTER block L-1 (post-block).
    """
    tok = lm.tokenizer(text, return_tensors="pt").to(lm.model.device)
    out = lm.model(**tok, output_hidden_states=True, return_dict=True)
    return {
        "input_ids": tok["input_ids"][0].tolist(),
        "hidden_states": out.hidden_states,   # tuple[L+1] of [1, seq, hidden]
        "logits": out.logits,                 # [1, seq, vocab]
    }


@torch.no_grad()
def capture_target_reps(
    lm: LoadedModel, text: str, codeword: str,
) -> Dict[str, Any]:
    """Capture per-layer residual vectors at the codeword and following token.

    Returns numpy-free torch tensors on CPU:
      reps[position_name] -> tensor [num_layers+1, hidden]  (incl. embedding row 0)
    position_name in {"codeword_last", "following"} (following omitted if None).
    """
    fwd = forward_hidden_states(lm, text)
    pos = target_positions(lm.tokenizer, fwd["input_ids"], codeword)
    hs = fwd["hidden_states"]
    n = len(hs)
    reps: Dict[str, torch.Tensor] = {}
    stack = lambda p: torch.stack([hs[l][0, p, :].float().cpu() for l in range(n)], dim=0)
    reps["codeword_last"] = stack(pos.codeword_last)
    if pos.following is not None:
        reps["following"] = stack(pos.following)
    return {"reps": reps, "positions": pos.as_dict(), "input_ids": fwd["input_ids"]}


# --------------------------------------------------------------------------- #
# Patching / directional intervention primitives (plan §9, §10)
# --------------------------------------------------------------------------- #
class LayerPatch:
    """Context manager that overwrites/edits the post-block residual at given
    positions of a single transformer layer, via a forward hook.

    Modes:
      * replace: h[pos] = vector           (activation patching, plan §9)
      * add:     h[pos] += alpha * vector  (directional injection, plan §10.1)
      * project_out: remove component along `vector` at pos (plan §10.2)

    The hook edits ONLY the requested positions and layer (unit-tested for
    locality). `vector` must be shaped [hidden] and on the model device/dtype.
    """

    def __init__(self, model, layer_idx: int, positions: Sequence[int],
                 vector: Optional[torch.Tensor] = None, mode: str = "replace",
                 alpha: float = 1.0):
        self.layers = _get_layers(model)
        self.layer_idx = layer_idx
        self.positions = list(positions)
        self.vector = vector
        self.mode = mode
        self.alpha = alpha
        self._handle = None

    def _hook(self, module, inputs, output):
        is_tuple = isinstance(output, tuple)
        hidden = output[0] if is_tuple else output
        hidden = hidden.clone()
        v = None
        if self.vector is not None:
            v = self.vector.to(hidden.dtype).to(hidden.device)
        seq = hidden.shape[1]
        for p in self.positions:
            # Generation-safe: during KV-cached decode steps the current forward
            # only holds the new token (seq==1), so a fixed prompt position is out
            # of range — skip it (the patched value is already baked into the KV
            # cache from prefill). Prevents IndexError under generate().
            if p < 0 or p >= seq:
                continue
            if self.mode == "replace":
                hidden[0, p, :] = v
            elif self.mode == "add":
                hidden[0, p, :] = hidden[0, p, :] + self.alpha * v
            elif self.mode == "project_out":
                d = v / (v.norm() + 1e-8)
                comp = torch.dot(hidden[0, p, :].float(), d.float()).to(hidden.dtype)
                hidden[0, p, :] = hidden[0, p, :] - self.alpha * comp * d.to(hidden.dtype)
            else:
                raise ValueError(f"unknown mode {self.mode}")
        return (hidden,) + tuple(output[1:]) if is_tuple else hidden

    def __enter__(self):
        self._handle = self.layers[self.layer_idx].register_forward_hook(self._hook)
        return self

    def __exit__(self, *exc):
        if self._handle is not None:
            self._handle.remove()
            self._handle = None
        return False


# --------------------------------------------------------------------------- #
# Generation (native EOS preserved) — plan §5.9
# --------------------------------------------------------------------------- #
@torch.no_grad()
def generate(lm: LoadedModel, prompt: str, max_new_tokens: int = 256,
             templated: bool = True, enable_thinking: Optional[bool] = None) -> Dict[str, Any]:
    """Deterministic greedy generation using the native chat template + EOS.

    enable_thinking (Phase 7): forwarded to apply_template when templated (None = model default).

    Returns the decoded completion (input stripped) and the stop reason. Does not
    print harmful content (plan §5.12) — callers decide what to persist/redact.
    """
    text = apply_template(lm.tokenizer, prompt, enable_thinking=enable_thinking) if templated else prompt
    tok = lm.tokenizer(text, return_tensors="pt", add_special_tokens=not templated
                       ).to(lm.model.device)
    in_len = tok["input_ids"].shape[1]
    out = lm.model.generate(
        **tok,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        eos_token_id=lm.eos_token_ids,          # preserve list-valued EOS
        pad_token_id=lm.tokenizer.pad_token_id,
    )
    gen_ids = out[0][in_len:]
    n = gen_ids.shape[0]
    completion = lm.tokenizer.decode(gen_ids, skip_special_tokens=True)
    stopped = "length" if n >= max_new_tokens else "eos"
    return {"completion": completion, "n_new_tokens": int(n), "stop_reason": stopped,
            "prompt_tokens": int(in_len)}


def cosine(a: torch.Tensor, b: torch.Tensor) -> float:
    a = a.float().flatten(); b = b.float().flatten()
    return float(torch.dot(a, b) / (a.norm() * b.norm() + 1e-8))
