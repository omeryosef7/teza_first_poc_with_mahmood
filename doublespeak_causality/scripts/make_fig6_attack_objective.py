#!/usr/bin/env python
"""
Figure F6 -- §14-18 Gate-7 attack-objective (mechanism-derived GCG). Controlled NEGATIVE for Claim F.

Reads the committed held-out StrongREJECT ASR per arm. Prefers live eval summaries
(outputs/stage_gcg_full/phase9_gcg_mac_matrix_arm*seed{SEED}/p9_heldout_asr_summary.json) when present;
otherwise falls back to the seed-42 first-cut numbers committed in reports/P_GATE7_FIRSTCUT.md.
Shows arm04 (vanilla) vs arm07-L18 (refusal, validated) vs arm07-L22 (unvalidated) vs arm07-rand-L18
(norm-matched RANDOM control). The decisive fact: random >= refusal => NOT mechanism-specific.
"""
import json, os, glob, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "figures/fig6_attack_objective.png")
ARM_ROOT = os.path.join(ROOT, "outputs/stage_gcg_full")

# committed seed-42 first-cut numbers (from reports/P_GATE7_FIRSTCUT.md), used as fallback / seed-42 group
SEED42 = {"arm04": 0.262, "arm07-L18": 0.405, "arm07-L22": 0.500, "arm07-rand-L18": 0.476}
LABELS = ["arm04\n(vanilla)", "arm07-L18\n(refusal, validated)", "arm07-L22\n(unvalidated)", "arm07-rand-L18\n(RANDOM ctrl)"]
KEYS = ["arm04", "arm07-L18", "arm07-L22", "arm07-rand-L18"]
COLORS = ["#8a8a8a", "#2a78d6", "#7fb0e0", "#eb6834"]

def load_seed(seed):
    """return {key: ASR} from live eval summaries for a seed, or None if incomplete."""
    pat = {
        "arm04": f"phase9_gcg_mac_matrix_arm04*seed{seed}",
        "arm07-L18": f"phase9_gcg_mac_matrix_arm07*L18*seed{seed}",  # excludes rand below
        "arm07-L22": f"phase9_gcg_mac_matrix_arm07*L22*seed{seed}",
        "arm07-rand-L18": f"phase9_gcg_mac_matrix_arm07*rand*L18*seed{seed}",
    }
    out = {}
    for k, g in pat.items():
        cands = [d for d in glob.glob(os.path.join(ARM_ROOT, g, "p9_heldout_asr_summary.json"))
                 if not (k == "arm07-L18" and "rand" in d)]
        if not cands: return None
        try:
            s = json.load(open(sorted(cands)[0]))
            out[k] = s.get("ASR", s.get("asr"))
        except Exception:
            return None
    if any(v is None for v in out.values()): return None
    return out

groups = {}
s42 = load_seed(42) or SEED42
groups["seed 42"] = s42
s43 = load_seed(43)
if s43: groups["seed 43"] = s43

fig, ax = plt.subplots(figsize=(9, 5))
x = np.arange(len(KEYS)); n_g = len(groups); w = 0.8 / n_g
for gi, (gname, vals) in enumerate(groups.items()):
    hatch = None if gi == 0 else "//"
    bars = ax.bar(x + (gi - (n_g-1)/2)*w, [vals[k] for k in KEYS], w,
                  color=COLORS, edgecolor="black", linewidth=0.6, hatch=hatch,
                  label=gname if n_g > 1 else None)
    for xi, k in zip(x, KEYS):
        ax.annotate(f"{vals[k]:.3f}", (xi + (gi-(n_g-1)/2)*w, vals[k]),
                    textcoords="offset points", xytext=(0, 3), ha="center", fontsize=8)
ax.set_xticks(x); ax.set_xticklabels(LABELS, fontsize=9)
ax.set_ylabel("held-out StrongREJECT ASR (test n=42)")
ax.axhline(s42["arm04"], color="#8a8a8a", ls=":", lw=1, alpha=0.7)
if n_g > 1: ax.legend(title="seed", fontsize=9)
ax.set_title("§14-18 Gate-7: mechanism-derived GCG objective is NOT refusal-specific\n"
             "(random-direction control ≥ validated-refusal objective ⇒ Claim F NOT supported)", fontsize=11)
ax.grid(alpha=0.25, axis="y")
fig.tight_layout()
os.makedirs(os.path.dirname(OUT), exist_ok=True)
fig.savefig(OUT, dpi=140, bbox_inches="tight")
print(f"[fig6] wrote {OUT}  (groups: {list(groups)})")
