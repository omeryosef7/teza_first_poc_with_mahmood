"""
next6_d6_depth_story.py — NEXT6 D6: unify the three depth signals into one timeline (CPU).

Reuses committed NEXT5 artifacts (no GPU, scalars only):
  * W3-b per-layer projections (DOUBLESPEAK): concept component (onto d_Direct) and codeword
    component (onto d_repeated) across layers  ->  where superposition builds.
  * W4-B z-AtP sum|AtP| by layer  ->  where attention heads causally contribute to the readout.
  * T3 (47_repr_toctou): the refusal check acts EARLY for bomb (install_effect early >> mid).

Produces the depth table + the load-bearing quantities and an HONEST narrative (including the
decoupling of the attention write-band from the concept-projection growth rate).

Run: python next6_d6_depth_story.py
"""
import os, sys, json, glob
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))

w3 = json.load(open(sorted(glob.glob(os.path.join(HERE, "outputs/pair_reps_*_694691/w3b_superposition.json")))[-1]))
ha = json.load(open(sorted(glob.glob(os.path.join(HERE, "outputs/head_attr_*696255")))[-1] + "/head_attribution.json"))

conc = np.array(w3["per_condition"]["DOUBLESPEAK"]["per_layer_concept_mean"])
code = np.array(w3["per_condition"]["DOUBLESPEAK"]["per_layer_codeword_mean"])
atp = np.array([ha["sum_abs_atp_by_layer"].get(str(L), 0.0) for L in range(len(conc))])
L = len(conc)

emergence = np.diff(conc)                        # concept rise L->L+1
corr_all = float(np.corrcoef(atp[:L-1], emergence)[0, 1])
corr_norl = float(np.corrcoef(atp[:L-2], emergence[:L-2])[0, 1])   # exclude the readout jump

check_lo, check_hi = 0, 10                        # bomb refusal check = EARLY (T3)
use_lo, use_hi = 20, L
conc_check = float(conc[check_lo:check_hi].mean())
conc_use = float(conc[use_lo:use_hi].mean())
write_band = (7, 15)
write_share = float(atp[write_band[0]:write_band[1]].sum() / atp.sum())

out = {
    "pair": "bomb", "model": "Llama-3.1-8B-Instruct",
    "per_layer": {"concept_DS": [round(float(x), 4) for x in conc],
                  "codeword_DS": [round(float(x), 4) for x in code],
                  "zatp_write": [round(float(x), 4) for x in atp]},
    "toctou_depth_gradient": {
        "concept_at_check_depth_early_L0_9": round(conc_check, 4),
        "concept_at_use_depth_L20_end": round(conc_use, 4),
        "use_over_check_ratio": round(conc_use / max(conc_check, 1e-6), 2),
    },
    "write_band": {"band": list(write_band), "share_of_total_zatp": round(write_share, 4),
                   "peak_layer": int(atp.argmax())},
    "write_vs_emergence_corr": {"all": round(corr_all, 3), "excl_readout_jump": round(corr_norl, 3),
                                "note": "attention WRITE band (mid) is DECOUPLED from concept-projection GROWTH rate (late) — honest nuance"},
    "codeword_leads": {"codeword_L2_6_mean": round(float(code[2:7].mean()), 4),
                       "concept_L2_6_mean": round(float(conc[2:7].mean()), 4)},
}
json.dump(out, open(os.path.join(HERE, "outputs", "next6_depth_story.json"), "w"), indent=2)

print("=== NEXT6 D6 — depth timeline (bomb, Llama-3.1-8B) ===")
print(" L | concept_DS | codeword_DS | zAtP_write")
for l in range(L):
    print(f"{l:2d} | {conc[l]:+9.3f} | {code[l]:+10.3f} | {atp[l]:8.2f}")
print()
print(f"TOCTOU depth gradient: concept @check(early L0-9)={conc_check:+.3f}  @use(late L20+)={conc_use:+.3f}  "
      f"ratio={conc_use/max(conc_check,1e-6):.1f}x")
print(f"codeword LEADS: codeword@L2-6={code[2:7].mean():+.3f} vs concept@L2-6={conc[2:7].mean():+.3f}")
print(f"attention write band L7-14 = {write_share:.1%} of z-AtP, peak L{int(atp.argmax())}")
print(f"corr(write, concept-emergence rate) = {corr_all:.3f} (excl readout jump {corr_norl:.3f}) "
      f"-> write and projection-growth are DECOUPLED (honest)")
print("-> outputs/next6_depth_story.json")
