"""CPU mechanism test for W1: frozen params + inputs_embeds root + ZHeadCapture grads.
Tiny random Llama, 2 layers, eager. Proves z.grad is populated and NO param .grad exists."""
import sys, torch
sys.path.insert(0, "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/doublespeak_causality")
import pair_common as pc
from contextlib import contextmanager
from transformers import LlamaConfig, LlamaForCausalLM

@contextmanager
def frozen_params(model):
    saved = [(q, q.requires_grad) for q in model.parameters()]
    try:
        for q, _ in saved: q.requires_grad_(False)
        yield
    finally:
        for q, flag in saved: q.requires_grad_(flag)

torch.manual_seed(0)
cfg = LlamaConfig(vocab_size=128, hidden_size=64, intermediate_size=128,
                  num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=4,
                  attn_implementation="eager")
m = LlamaForCausalLM(cfg).eval()
print("loaded attn =", getattr(m.config, "_attn_implementation", "<unrecorded>"))
band = [0, 1]
n_heads, head_dim = pc._attn_head_dims(m)
print("n_heads=%d head_dim=%d" % (n_heads, head_dim))

ids = torch.tensor([[1, 5, 9, 12, 7, 3]])
with torch.no_grad():
    emb = m.get_input_embeddings()(ids)
emb = emb.detach().clone().requires_grad_(True)

p_star = 4
c_ids = torch.tensor([10]); w_ids = torch.tensor([20])
m.zero_grad(set_to_none=True)
with frozen_params(m), pc.ZHeadCapture(m, band) as cap:
    with torch.enable_grad():
        out = m(inputs_embeds=emb, use_cache=False)
        lp = torch.log_softmax(out.logits[0, -1, :].float(), dim=-1)
        M = lp[c_ids].logsumexp(0) - lp[w_ids].logsumexp(0)
        M.backward()
    for L in band:
        z = cap.acts[L]
        assert z.requires_grad, "FAIL: z does not require grad at layer %d" % L
        assert z.grad is not None, "FAIL: z.grad is None at layer %d" % L
        g = z.grad[0].detach().float().view(-1, n_heads, head_dim)[p_star]
        print("layer %d: z.grad OK, shape %s, |g| = %.6f" % (L, tuple(g.shape), g.norm()))

n_with_grad = sum(1 for q in m.parameters() if q.grad is not None)
print("PARAMS WITH .grad ALLOCATED =", n_with_grad, "(must be 0)")
assert n_with_grad == 0, "FAIL: param grad buffers were allocated -- the OOM bug is still live"
assert all(q.requires_grad for q in m.parameters()), "FAIL: frozen_params did not restore flags"
print("M =", float(M))
print("ALL MECHANISM CHECKS PASSED")
