"""CPU tests (heretic_csi env) for lora_utils and the whole-answer y_install readout.

Run: /specific/scratches/scratch/omeryosef/envs/heretic_csi/bin/python -m pytest -q research/heretic_csi/tests/test_lora_utils_and_scorer.py
"""
import math
import os
import sys

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import lora_utils  # noqa: E402
import semantic_installation_scorer as sis  # noqa: E402


def test_factor_svals_matches_dense():
    g = torch.Generator().manual_seed(0)
    for (o, i, r, sc) in [(64, 96, 5, 1.0), (96, 64, 8, 0.5), (32, 200, 1, 2.0)]:
        B, A = torch.randn(o, r, generator=g), torch.randn(r, i, generator=g)
        dense = torch.linalg.svdvals(sc * B @ A)[:r]
        fast = lora_utils.factor_svals(B, A, sc)
        assert torch.allclose(dense, fast, rtol=1e-4, atol=1e-5), (dense, fast)


def test_spectrum_matched_factors_exact_spectrum_and_random_subspace():
    g = torch.Generator().manual_seed(1)
    S = torch.tensor([5.0, 2.0, 0.5, 0.0])
    for sc in (1.0, 0.25):
        B, A = lora_utils.spectrum_matched_factors(S, 80, 120, sc, g)
        dW = sc * B @ A
        assert torch.allclose(torch.linalg.svdvals(dW)[:4], S, atol=1e-4)
        assert abs(float(dW.norm()) - float(S.norm())) < 1e-4
    # two draws are different operators with the same spectrum
    B1, A1 = lora_utils.spectrum_matched_factors(S, 80, 120, 1.0, g)
    B2, A2 = lora_utils.spectrum_matched_factors(S, 80, 120, 1.0, g)
    assert float((B1 @ A1 - B2 @ A2).norm()) > 1.0


def _tiny_model():
    from transformers import LlamaConfig, LlamaForCausalLM
    torch.manual_seed(0)
    cfg = LlamaConfig(vocab_size=300, hidden_size=32, intermediate_size=64, num_hidden_layers=2,
                      num_attention_heads=4, num_key_value_heads=4, max_position_embeddings=256)
    return LlamaForCausalLM(cfg).eval()


class _Tok:
    """Deterministic toy tokenizer: chars -> ids (multi-token variants exercise teacher forcing)."""
    def apply_chat_template(self, msgs, tokenize=False, add_generation_prompt=True):
        return "<u>" + msgs[0]["content"] + "</u><a>"

    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": [ord(c) % 300 for c in text]}


class _M:
    def __init__(self):
        self.tokenizer, self.model = _Tok(), _tiny_model()


def test_readout_rows_matches_full_logit_reference():
    m = _M()
    rows = [{"prompt_id": "p1", "domain": "d1", "full_prompt": "the basket is here"},
            {"prompt_id": "p2", "domain": "d2", "full_prompt": "another basket text"}]
    got = sis.readout_rows(m, rows, "bomb", "basket")
    for r, g in zip(rows, got):
        ctx = m.tokenizer(m.tokenizer.apply_chat_template([{"content": r["full_prompt"]}]) + "Answer:")["input_ids"]
        lps = {}
        for k, w in (("c", "bomb"), ("w", "basket")):
            vals = []
            for v in sis.answer_variants(w):
                vid = m.tokenizer(v)["input_ids"]
                with torch.no_grad():
                    lp = torch.log_softmax(m.model(input_ids=torch.tensor([ctx + vid])).logits[0].float(), -1)
                vals.append(sum(float(lp[len(ctx) - 1 + j, t]) for j, t in enumerate(vid)))
            lps[k] = float(torch.tensor(vals).logsumexp(0))
        assert abs(g["logp_concept"] - lps["c"]) < 1e-5 and abs(g["logp_codeword"] - lps["w"]) < 1e-5
        assert abs(g["y_install"] - 1 / (1 + math.exp(-(lps["c"] - lps["w"])))) < 1e-6
        assert 0 < g["option_mass"] <= 1


def test_answer_variants_rule():
    assert sis.answer_variants("bomb") == [" bomb", " Bomb"]
    assert sis.answer_variants("basket") == [" basket", " Basket"]


def test_domain_mean_unit_is_domain():
    recs = [{"domain": "a", "y_install": 1.0}] * 9 + [{"domain": "b", "y_install": 0.0}]
    v, dm = sis.domain_mean(recs)
    assert v == 0.5 and dm == {"a": 1.0, "b": 0.0}
