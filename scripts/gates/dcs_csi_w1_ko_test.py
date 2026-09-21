"""Does W1's ScopedAttentionKnockout call actually CHANGE anything? A no-op knockout is the
failure this whole screen would be blind to. Tiny CPU Llama, W1's exact call shape."""
import sys, torch
sys.path.insert(0, "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood/doublespeak_causality")
import pair_common as pc
from transformers import LlamaConfig, LlamaForCausalLM

torch.manual_seed(0)
cfg = LlamaConfig(vocab_size=128, hidden_size=64, intermediate_size=128,
                  num_hidden_layers=6, num_attention_heads=4, num_key_value_heads=4,
                  attn_implementation="eager")
m = LlamaForCausalLM(cfg).eval()
for q in m.parameters(): q.requires_grad_(False)
band = [1, 2, 3]
nh, hd = pc._attn_head_dims(m)
ids = torch.tensor([[1, 5, 9, 12, 7, 3, 11, 2, 8, 4]])
with torch.no_grad(): emb = m.get_input_embeddings()(ids)

dk   = [1, 2, 3]            # demo block  (blocked keys)
qs   = {5, 6, 7, 8, 9}      # query span
surf = [7, 8]               # target surface inside the query span
p_star = max(surf)

def zs(ctx=None):
    with pc.ZHeadCapture(m, band) as cap, torch.no_grad():
        if ctx is None:
            m(inputs_embeds=emb, use_cache=False)
        else:
            with ctx: m(inputs_embeds=emb, use_cache=False)
        return {L: cap.acts[L][0].float().view(-1, nh, hd)[p_star].clone() for L in band}

z_clean = zs()
ko = pc.ScopedAttentionKnockout(m, sorted(set(band)), blocked_keys=dk,
                                mode="target_surface_row_only",
                                query_span=qs, demo_span=dk, surface_span=surf)
z_ko = zs(ko)

tot = 0.0
for L in band:
    d = float((z_ko[L] - z_clean[L]).abs().sum())
    tot += d
    print("layer %d: |z_ko - z_clean| at p*=%d  =  %.6f" % (L, p_star, d))
print("ko_delta_total = %.6f" % tot)
assert tot > 0, "FAIL: the knockout is a NO-OP -- it changed nothing at p*"

# A row OUTSIDE the surface span must be untouched: the scope is target_surface_row_only.
with pc.ZHeadCapture(m, band) as cap, torch.no_grad():
    m(inputs_embeds=emb, use_cache=False)
    zc_all = {L: cap.acts[L][0].float().clone() for L in band}
with pc.ZHeadCapture(m, band) as cap, torch.no_grad():
    with pc.ScopedAttentionKnockout(m, sorted(set(band)), blocked_keys=dk,
                                    mode="target_surface_row_only", query_span=qs,
                                    demo_span=dk, surface_span=surf):
        m(inputs_embeds=emb, use_cache=False)
    zk_all = {L: cap.acts[L][0].float().clone() for L in band}
L0 = band[0]
off = [p for p in range(ids.shape[1]) if p not in set(surf)]
d_off = float((zk_all[L0][off] - zc_all[L0][off]).abs().sum())
d_on  = float((zk_all[L0][surf] - zc_all[L0][surf]).abs().sum())
print("layer %d: delta ON surface rows = %.6f | OFF surface rows = %.6f" % (L0, d_on, d_off))
assert d_on > 0, "FAIL: surface rows unchanged"
assert d_off == 0.0, "FAIL: SCOPE LEAK -- rows outside target_surface were edited (%.8f)" % d_off
print("ALL KNOCKOUT CHECKS PASSED (live, and scoped to the surface rows only)")
