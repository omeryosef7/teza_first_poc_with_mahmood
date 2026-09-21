"""Is the last-layer zero gradient at p*!=last STRUCTURAL, or a broken capture?
Prediction if structural: (a) last layer at p*=last is NONZERO; (b) with layers ABOVE the band,
the same band layer at p*!=last becomes NONZERO."""
import sys, torch
sys.path.insert(0, "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/doublespeak_causality")
import pair_common as pc
from transformers import LlamaConfig, LlamaForCausalLM

def gnorm(n_layers, band, p_star, seed=0):
    torch.manual_seed(seed)
    cfg = LlamaConfig(vocab_size=128, hidden_size=64, intermediate_size=128,
                      num_hidden_layers=n_layers, num_attention_heads=4,
                      num_key_value_heads=4, attn_implementation="eager")
    m = LlamaForCausalLM(cfg).eval()
    for q in m.parameters(): q.requires_grad_(False)
    ids = torch.tensor([[1, 5, 9, 12, 7, 3]])
    with torch.no_grad(): emb = m.get_input_embeddings()(ids)
    emb = emb.detach().clone().requires_grad_(True)
    nh, hd = pc._attn_head_dims(m)
    with pc.ZHeadCapture(m, band) as cap:
        out = m(inputs_embeds=emb, use_cache=False)
        lp = torch.log_softmax(out.logits[0, -1, :].float(), dim=-1)
        (lp[torch.tensor([10])].logsumexp(0) - lp[torch.tensor([20])].logsumexp(0)).backward()
        return {L: float(cap.acts[L].grad[0].view(-1, nh, hd)[p_star].norm()) for L in band}

print("(a) 2 layers, band=[0,1], p*=5 (THE LAST position):", gnorm(2, [0,1], 5))
print("(b) 2 layers, band=[0,1], p*=4 (not last)        :", gnorm(2, [0,1], 4))
print("(c) 4 layers, band=[0,1], p*=4 (2 layers ABOVE)  :", gnorm(4, [0,1], 4))
print("(d) 4 layers, band=[2,3], p*=4 (top layer is 3)  :", gnorm(4, [2,3], 4))
