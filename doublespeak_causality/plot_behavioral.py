"""
plot_behavioral.py — publication figures for the behavioral-causality sprint (benign: reads label
data + summaries, no harmful text, no GPU). Generates:
  fig_toctou_timing.png    — the HEADLINE: Direct-injection REFUSAL rate by injection depth, Llama + Qwen3
                             (the architecture-general TOCTOU causal timing law).
  fig_necessity_windows.png — behavioral necessity Δ per layer window vs identity/random controls (Llama).
  fig_sufficiency_depth.png — sufficiency: DS-inject vs Direct-inject malicious rate by depth (Llama).

Usage: python plot_behavioral.py
"""
import os
import sys
import json
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figures")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, HERE)
import importlib.util
_s = importlib.util.spec_from_file_location("v17", os.path.join(HERE, "17_validate_behavioral_triplets.py"))
v17 = importlib.util.module_from_spec(_s)
sys.path.insert(0, os.path.join(HERE, "..", "poc_stage3"))
_s.loader.exec_module(v17)
kw = v17.kw_refusal

# result dirs (this sprint's runs)
LLAMA = {"early": "beh_sufficiency_Llama-3.1-8B-Instruct_20260727_213542",
         "mid": "beh_sufficiency_Llama-3.1-8B-Instruct_20260727_203514",
         "late": "beh_sufficiency_Llama-3.1-8B-Instruct_20260727_215026"}
QWEN = {"early": "beh_sufficiency_Qwen3-14B_20260728_091747",
        "late": "beh_sufficiency_Qwen3-14B_20260728_091938"}
NEC = "beh_necessity_Llama-3.1-8B-Instruct_20260727_204515"


def direct_rates(dirs):
    """Per window: Direct-injection refusal + malicious rate among baseline-benign Neutrals."""
    out = {}
    for win, d in dirs.items():
        p = os.path.join(HERE, "outputs", d, "sufficiency_raw.jsonl")
        if not os.path.exists(p):
            continue
        rows = [json.loads(l) for l in open(p)]
        benign = {(r["base_id"], r["codeword"]) for r in rows
                  if r["arm"] == "baseline_neutral" and r["cat"] == "BENIGN"}
        dr = [r for r in rows if r["arm"].startswith("suff_Direct_") and (r["base_id"], r["codeword"]) in benign]
        c = Counter(r["cat"] for r in dr); n = len(dr) or 1
        out[win] = {"refusal": c.get("REJECTED", 0) / n, "malicious": c.get("MALICIOUS", 0) / n, "n": len(dr)}
    return out


def fig_toctou():
    ll, qw = direct_rates(LLAMA), direct_rates(QWEN)
    order = ["early", "mid", "late"]
    xs = list(range(len(order)))
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(xs, [ll.get(w, {}).get("refusal", float("nan")) for w in order], "o-", color="#c0392b",
            lw=2.4, ms=9, label="Llama-3.1-8B refusal")
    qorder = [order.index("early"), order.index("late")]
    ax.plot([xs[order.index("early")], xs[order.index("late")]],
            [qw.get("early", {}).get("refusal", float("nan")), qw.get("late", {}).get("refusal", float("nan"))],
            "s--", color="#e67e22", lw=2.4, ms=9, label="Qwen3-14B refusal")
    ax.plot(xs, [ll.get(w, {}).get("malicious", float("nan")) for w in order], "^:", color="#2980b9",
            lw=1.8, ms=8, label="Llama malicious (compliance)")
    ax.set_xticks(xs); ax.set_xticklabels(["early\n(0–9)", "mid\n(10–19)", "late\n(20–31)"])
    ax.set_ylabel("rate (among benign Neutrals)"); ax.set_ylim(-0.03, 1.03)
    ax.set_xlabel("layer window where the harmful concept is injected")
    ax.set_title("TOCTOU causal timing: early injection → refusal, late → compliance\n"
                 "(architecture-general: Llama + Qwen3)", fontsize=10)
    ax.legend(fontsize=8, loc="center left"); ax.grid(alpha=0.25)
    fig.tight_layout(); p = os.path.join(OUT, "fig_toctou_timing.png"); fig.savefig(p, dpi=150); plt.close(fig)
    print(f"  -> {p}")


def fig_necessity():
    d = json.load(open(os.path.join(HERE, "outputs", NEC, "necessity_summary.json")))
    res = d["results"]; wins = ["early", "mid", "late", "late_half_to_end"]
    xs = list(range(len(wins)))
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar([x - 0.25 for x in xs], [res[w]["delta_necessity"] for w in wins], 0.25, label="necessity Δ", color="#c0392b")
    ax.bar(xs, [res[w]["delta_identity_control"] for w in wins], 0.25, label="identity control", color="#95a5a6")
    ax.bar([x + 0.25 for x in xs], [res[w]["delta_random_control"] for w in wins], 0.25, label="random control", color="#3498db")
    ax.set_xticks(xs); ax.set_xticklabels(["early", "mid", "late", "late-half"])
    ax.set_ylabel("Δ = fraction of malicious flipped to benign")
    ax.set_title("Behavioral necessity is EARLY-layer specific (Llama, n=20)", fontsize=10)
    ax.legend(fontsize=8); ax.grid(alpha=0.25, axis="y")
    fig.tight_layout(); p = os.path.join(OUT, "fig_necessity_windows.png"); fig.savefig(p, dpi=150); plt.close(fig)
    print(f"  -> {p}")


def fig_sufficiency():
    def mal(dirs):
        out = {}
        for win, d in dirs.items():
            s = json.load(open(os.path.join(HERE, "outputs", d, "sufficiency_summary.json")))
            r = s["results"].get(win, {})
            out[win] = (r.get("suff_DS_malicious_rate"), r.get("suff_Direct_malicious_rate"))
        return out
    m = mal(LLAMA); order = ["early", "mid", "late"]; xs = list(range(len(order)))
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(xs, [m[w][0] for w in order], "o-", color="#8e44ad", lw=2.4, ms=9, label="Neutral←DS (hijacked state)")
    ax.plot(xs, [m[w][1] for w in order], "s-", color="#16a085", lw=2.4, ms=9, label="Neutral←Direct (raw concept)")
    ax.set_xticks(xs); ax.set_xticklabels(["early", "mid", "late"])
    ax.set_ylabel("malicious rate (behavioral sufficiency)")
    ax.set_xlabel("injection window")
    ax.set_title("Sufficiency dissociation: raw concept ≫ hijacked state at MID\n"
                 "(opposite of rep-level Patchscopes DS>Direct)", fontsize=10)
    ax.legend(fontsize=8); ax.grid(alpha=0.25)
    fig.tight_layout(); p = os.path.join(OUT, "fig_sufficiency_depth.png"); fig.savefig(p, dpi=150); plt.close(fig)
    print(f"  -> {p}")


if __name__ == "__main__":
    print("[plot] generating behavioral-causality figures:")
    fig_toctou(); fig_necessity(); fig_sufficiency()
    print("[plot] done -> figures/")
