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

import glob


def discover_sufficiency():
    """Auto-map {model_short: {window: dir}} from all sufficiency summaries (latest per model+window)."""
    out = {}
    for d in sorted(glob.glob(os.path.join(HERE, "outputs", "beh_sufficiency_*"))):
        p = os.path.join(d, "sufficiency_summary.json")
        if not os.path.exists(p):
            continue
        try:
            s = json.load(open(p))
        except Exception:
            continue
        model = s.get("model", "?").split("/")[-1]
        short = {"Llama-3.1-8B-Instruct": "Llama-3.1-8B", "Qwen3-14B": "Qwen3-14B",
                 "Phi-4-mini-reasoning": "Phi-4-mini"}.get(model, model)
        for w in s.get("results", {}):
            out.setdefault(short, {})[w] = os.path.basename(d)   # later dirs overwrite → latest wins
    return out


SUFF = discover_sufficiency()
LLAMA = SUFF.get("Llama-3.1-8B", {})
QWEN = SUFF.get("Qwen3-14B", {})
PHI4 = SUFF.get("Phi-4-mini", {})
def _latest_necessity(model_sub="Llama-3.1-8B-Instruct"):
    """Latest necessity dir for a model that has all 4 windows in its summary (auto, not hardcoded)."""
    cands = []
    for d in sorted(glob.glob(os.path.join(HERE, "outputs", f"beh_necessity_{model_sub}_*"))):
        p = os.path.join(d, "necessity_summary.json")
        if not os.path.exists(p):
            continue
        try:
            res = json.load(open(p)).get("results", {})
        except Exception:
            continue
        if all(w in res for w in ("early", "mid", "late", "late_half_to_end")):
            cands.append(os.path.basename(d))
    return cands[-1] if cands else "beh_necessity_Llama-3.1-8B-Instruct_20260727_204515"


NEC = _latest_necessity()


def direct_rates(dirs):
    """Per window: Direct-injection refusal + malicious rate among baseline-benign Neutrals."""
    out = {}
    for win, d in dirs.items():
        p = os.path.join(HERE, "outputs", d, "sufficiency_raw.jsonl")
        if not os.path.exists(p):
            continue
        rows = [json.loads(l) for l in open(p)]
        # per-CONDITION baseline-BENIGN conditioning (base,cw,context_len); context_len absent in
        # pre-iter18 raw falls back to (base,cw,None). Fixes an audit bug where (base,cw)-only
        # membership pulled in Direct rows from context-lengths whose baseline was NOT benign.
        k = lambda r: (r["base_id"], r["codeword"], r.get("context_len"))
        benign = {k(r) for r in rows if r["arm"] == "baseline_neutral" and r["cat"] == "BENIGN"}
        dr = [r for r in rows if r["arm"].startswith("suff_Direct_") and k(r) in benign]
        c = Counter(r["cat"] for r in dr); n = len(dr) or 1
        out[win] = {"refusal": c.get("REJECTED", 0) / n, "malicious": c.get("MALICIOUS", 0) / n, "n": len(dr)}
    return out


def fig_toctou():
    ll, qw, ph = direct_rates(LLAMA), direct_rates(QWEN), direct_rates(PHI4)
    order = ["early", "mid", "late"]
    xs = list(range(len(order)))
    xi = {w: xs[order.index(w)] for w in order}
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    ax.plot(xs, [ll.get(w, {}).get("refusal", float("nan")) for w in order], "o-", color="#c0392b",
            lw=2.4, ms=9, label="Llama-3.1-8B refusal")
    def two(rates, style, color, lbl):
        pts = [(xi[w], rates[w]["refusal"]) for w in ("early", "late") if w in rates]
        if len(pts) == 2:
            ax.plot([p[0] for p in pts], [p[1] for p in pts], style, color=color, lw=2.4, ms=9, label=lbl)
    two(qw, "s--", "#e67e22", "Qwen3-14B refusal")
    two(ph, "D-.", "#27ae60", "Phi-4-mini refusal")
    ax.plot(xs, [ll.get(w, {}).get("malicious", float("nan")) for w in order], "^:", color="#2980b9",
            lw=1.8, ms=8, label="Llama malicious (compliance)")
    ax.set_xticks(xs); ax.set_xticklabels(["early\n(0–9)", "mid\n(10–19)", "late\n(20–31)"])
    ax.set_ylabel("rate (among benign Neutrals)"); ax.set_ylim(-0.03, 1.03)
    ax.set_xlabel("layer window where the harmful concept is injected")
    nmods = 1 + (1 if qw else 0) + (1 if ph else 0)
    ax.set_title(f"TOCTOU causal timing: early injection → refusal, late → compliance\n"
                 f"(architecture-general across {nmods} model{'s' if nmods > 1 else ''})", fontsize=10)
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
    nan = float("nan")
    def val(w, i):  # guard: a window run may be missing (KeyError) or carry a None rate on a partial summary
        v = m.get(w, (nan, nan))[i]
        return nan if v is None else v
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(xs, [val(w, 0) for w in order], "o-", color="#8e44ad", lw=2.4, ms=9, label="Neutral←DS (hijacked state)")
    ax.plot(xs, [val(w, 1) for w in order], "s-", color="#16a085", lw=2.4, ms=9, label="Neutral←Direct (raw concept)")
    ax.set_xticks(xs); ax.set_xticklabels(["early", "mid", "late"])
    ax.set_ylabel("malicious rate (behavioral sufficiency)")
    ax.set_xlabel("injection window")
    ax.set_title("Sufficiency dissociation: raw concept ≫ hijacked state at MID\n"
                 "(opposite of rep-level Patchscopes DS>Direct)", fontsize=10)
    ax.legend(fontsize=8); ax.grid(alpha=0.25)
    fig.tight_layout(); p = os.path.join(OUT, "fig_sufficiency_depth.png"); fig.savefig(p, dpi=150); plt.close(fig)
    print(f"  -> {p}")


def fig_crossmodel():
    """Behavioral reproduction across architectures: eligible + clean-success bases per model.
    Auto-includes any curated screen whose corrected summary exists (Llama/Qwen3/Phi-4/DeepSeek-R1)."""
    import glob
    models = []  # (label, eligible, clean, n_bases)
    for name, label in [("curated_v1", "Llama-3.1-8B"), ("curated_qwen3_nothink", "Qwen3-14B"),
                        ("curated_phi4", "Phi-4-mini"), ("curated_deepseek_r1", "DeepSeek-R1-8B")]:
        # prefer the corrected reclassified summary; else the raw
        for fn in ("screen_summary_reclassified.json", "screen_summary.json"):
            p = os.path.join(HERE, "outputs", f"behavioral_screen_{name}", fn)
            if os.path.exists(p):
                d = json.load(open(p))
                models.append((label, d.get("n_eligible_bases"), d.get("n_clean_success_bases"), d.get("n_bases")))
                break
    if not models:
        print("  (no screens for cross-model figure)"); return
    xs = list(range(len(models)))
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar([x - 0.2 for x in xs], [m[1] for m in models], 0.4, label="eligible bases", color="#2c3e50")
    ax.bar([x + 0.2 for x in xs], [m[2] for m in models], 0.4, label="clean-success bases", color="#c0392b")
    for i, m in enumerate(models):
        if m[3]:
            ax.text(i - 0.2, (m[1] or 0) + 0.5, f"{m[1]}/{m[3]}", ha="center", fontsize=8)
    ax.set_xticks(xs); ax.set_xticklabels([m[0] for m in models])
    ax.set_ylabel("bases"); ax.set_title("Behavioral Doublespeak jailbreak reproduces across architectures", fontsize=10)
    ax.legend(fontsize=8); ax.grid(alpha=0.25, axis="y")
    fig.tight_layout(); p = os.path.join(OUT, "fig_crossmodel_behavioral.png"); fig.savefig(p, dpi=150); plt.close(fig)
    print(f"  -> {p}")


if __name__ == "__main__":
    print("[plot] generating behavioral-causality figures:")
    fig_toctou(); fig_necessity(); fig_sufficiency(); fig_crossmodel()
    print("[plot] done -> figures/")
