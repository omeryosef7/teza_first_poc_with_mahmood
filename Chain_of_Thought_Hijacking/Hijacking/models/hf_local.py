"""Local open-source HF thinking-model TARGET backend for CoT-Hijacking.

Lets the attack TARGET be an open-source model run locally on GPU, while the
attacker LM and judge stay on the API (Gemini). Implements the same
BaseLLM.batched_generate contract as APILiteLLM. Selected via a target-model
string of the form "hf:<hf_repo_id>". Weights load from whatever HF cache the
environment points at (the SLURM script points HF_HOME at node-local storage,
so nothing is written to the project cache).
"""
import os
import re

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from utils.logger import logger

from .base import BaseLLM

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


class HFLocalLLM(BaseLLM):
    def __init__(self, hf_id: str, max_new_tokens: int = 4096):
        self.hf_id = hf_id
        self.max_new_tokens = int(os.getenv("HF_TARGET_MAX_NEW_TOKENS", max_new_tokens))
        logger.info(f"Loading local HF target {hf_id} (max_new_tokens={self.max_new_tokens})")
        self.tokenizer = AutoTokenizer.from_pretrained(hf_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            hf_id, torch_dtype=torch.bfloat16, device_map="cuda"
        )
        self.model.eval()
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def _final_answer(self, text: str) -> str:
        # Return the post-<think> answer; fall back to raw text if the whole
        # generation stayed inside a (possibly truncated) think block.
        stripped = _THINK_RE.sub("", text).strip()
        return stripped if stripped else text.strip()

    @torch.no_grad()
    def batched_generate(self, convs_list, max_n_tokens, temperature, top_p, **kwargs):
        cap = min(int(max_n_tokens), self.max_new_tokens)
        do_sample = temperature is not None and float(temperature) > 0
        outputs = []
        for conv in convs_list:
            # return_dict=True gives input_ids + attention_mask (transformers>=5 returns a
            # BatchEncoding, not a bare tensor); pass the whole encoding to generate().
            inputs = self.tokenizer.apply_chat_template(
                conv, add_generation_prompt=True, return_tensors="pt", return_dict=True
            ).to(self.model.device)
            prompt_len = inputs["input_ids"].shape[1]
            gen_kwargs = dict(max_new_tokens=cap, do_sample=do_sample,
                              pad_token_id=self.tokenizer.pad_token_id)
            if do_sample:
                gen_kwargs.update(temperature=float(temperature), top_p=float(top_p))
            out = self.model.generate(**inputs, **gen_kwargs)
            new_tokens = out[0, prompt_len:]
            text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)
            outputs.append(self._final_answer(text))
        return outputs
