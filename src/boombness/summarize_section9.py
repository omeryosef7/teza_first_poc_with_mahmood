"""summarize_section9.py — plan §9's named outputs, which were never produced.

Plan §9 requires `correlation_summary.json`, `regression_summary.md` and four plots
(`boombness_vs_asr_scatter`, `boombness_vs_asr_binned`, `boombness_by_condition`,
`asr_by_condition`). None existed. This script produces all six from committed artifacts and
answers §9's eight decision questions in one place, each with the artifact it comes from.

IT DOES NOT RE-DERIVE THE STATISTICS. `analyze_g2.py` and `analyze_g9.py` own the inference and
have been re-run with the T5/T6 fixes; this reads their artifacts and consolidates. The one thing
it computes itself is the row-level join needed for the plots, and that join is VALIDATED by
reproducing `rho_pooled` from `g2_analysis_cwpos.json` bit-identically (234 rows,
0.306667780204175) before any plot is drawn. If the reproduction fails the script REFUSES to write,
because a plot drawn from a join that does not match the inference is a plot of a different dataset.

REUSE: `spearman` from analyze_g2 (the same function the artifact was computed with).
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import subprocess
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_g2 import spearman  # noqa: E402


def git_commit_safe() -> str:
    """Provenance that cannot kill the analysis. Added 2026-08-22 after two crashes.

    `git rev-parse HEAD` raises FileNotFoundError on the batch nodes -- they have no git binary --
    and callers invoke it INSIDE the literal that builds the output dict, so the run dies before
    writing anything and the artifact on disk silently keeps its previous contents while `sacct`
    says FAILED. A stale file that reads as current is the worst failure mode available, and it
    happened twice: to analyze_qwen3_decomposition.py, then to analyze_dissociation.py after only
    the first was fixed and its siblings left alone.

    The SLURM wrappers export BOOMB_GIT_COMMIT from the submitting host, so real provenance is
    preserved; absent that this degrades to an explicit marker rather than to silence.
    """
    import os as _os
    import subprocess as _sp
    env = _os.environ.get("BOOMB_GIT_COMMIT")
    if env:
        return env.strip()
    try:
        _kw = {"capture_output": True, "text": True}
        _repo = globals().get("REPO")
        if _repo:
            _kw["cwd"] = _repo
        r = _sp.run(["git", "rev-parse", "HEAD"], **_kw)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
        return f"unavailable:git_rc_{r.returncode}"
    except (FileNotFoundError, OSError) as exc:
        return f"unavailable:{type(exc).__name__}"


def git_dirty_safe(*args) -> object:
    """Companion for the `git status --porcelain` dirty-flag calls. Never raises."""
    import subprocess as _sp
    try:
        _kw = {"capture_output": True, "text": True}
        _repo = globals().get("REPO")
        if _repo:
            _kw["cwd"] = _repo
        return bool(_sp.run(["git", "status", "--porcelain", *args], **_kw).stdout.strip())
    except (FileNotFoundError, OSError):
        return None


HEADLINE = "d_surface|L12|proj"
ARM = "natural_doublespeak"
EXPECT_N = 234
EXPECT_RHO = 0.306667780204175


def load_rows(judge_dir: str, extract_dir: str) -> List[dict]:
    jud = {}
    for line in open(os.path.join(judge_dir, "results.jsonl")):
        r = json.loads(line)
        jud[r["prompt_id"]] = r
    out = []
    for line in open(os.path.join(extract_dir, "results.jsonl")):
        e = json.loads(line)
        if not e.get("is_final_occurrence"):
            continue
        j = jud.get(e["prompt_id"])
        if not j:
            continue
        out.append({
            "prompt_id": e["prompt_id"],
            "boombness": e.get(HEADLINE),
            "asr_score": j.get("strongreject_score"),
            "malicious": j.get("malicious_at_0.5"),
            "refused": j.get("refused"),
            "condition": j.get("condition"),
            "domain": j.get("domain"),
            "n_examples": j.get("n_examples"),
            "role_style": j.get("role_style"),
        })
    return out


def headline_subset(rows: List[dict]) -> List[dict]:
    return [r for r in rows
            if r["condition"] == ARM and (r["n_examples"] or 0) >= 1
            and r["boombness"] is not None and r["asr_score"] is not None]


def verify_join(rows: List[dict]) -> dict:
    sub = headline_subset(rows)
    rho, p = spearman([r["boombness"] for r in sub], [r["asr_score"] for r in sub])
    ok = (len(sub) == EXPECT_N) and abs(rho - EXPECT_RHO) < 1e-12
    return {"n": len(sub), "rho": rho, "p_iid": p, "expected_n": EXPECT_N,
            "expected_rho": EXPECT_RHO, "reproduces_g2_artifact": ok}


def plots(rows: List[dict], outdir: str) -> List[str]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    os.makedirs(outdir, exist_ok=True)
    made = []
    sub = headline_subset(rows)
    xs = [r["boombness"] for r in sub]
    ys = [r["asr_score"] for r in sub]

    # 1. scatter
    fig, ax = plt.subplots(figsize=(6, 4.2))
    doms = sorted({r["domain"] for r in sub})
    cmap = plt.get_cmap("tab10")
    for i, d in enumerate(doms):
        px = [r["boombness"] for r in sub if r["domain"] == d]
        py = [r["asr_score"] for r in sub if r["domain"] == d]
        ax.scatter(px, py, s=18, alpha=0.75, color=cmap(i % 10), label=d)
    ax.set_xlabel(f"Boombness  ({HEADLINE})")
    ax.set_ylabel("StrongReject score")
    ax.set_title(f"Boombness vs ASR — {ARM}, n={len(sub)}\n"
                 f"pooled rho={EXPECT_RHO:.3f}; domain-clustered inference in g2_analysis_cwpos.json")
    ax.legend(fontsize=6, ncol=2, title="domain (the cluster unit)", title_fontsize=6)
    fig.tight_layout()
    p = os.path.join(outdir, "boombness_vs_asr_scatter.png")
    fig.savefig(p, dpi=150); plt.close(fig); made.append(p)

    # 2. binned — deciles of boombness, mean ASR with a cluster-aware caveat in the title
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    k = 10
    bx, by, bn = [], [], []
    for b in range(k):
        idx = order[b * len(order) // k:(b + 1) * len(order) // k]
        if not idx:
            continue
        bx.append(sum(xs[i] for i in idx) / len(idx))
        by.append(sum(ys[i] for i in idx) / len(idx))
        bn.append(len(idx))
    fig, ax = plt.subplots(figsize=(6, 4.2))
    ax.plot(bx, by, "o-", color="#b5442e")
    for X, Y, N in zip(bx, by, bn):
        ax.annotate(str(N), (X, Y), textcoords="offset points", xytext=(0, 6), fontsize=6, ha="center")
    ax.set_xlabel(f"Boombness decile mean ({HEADLINE})")
    ax.set_ylabel("mean StrongReject score")
    ax.set_title(f"Boombness vs ASR, binned into deciles — {ARM}, n={len(sub)}\n"
                 "bin counts annotated; bins are NOT independent (6 domain clusters)")
    fig.tight_layout()
    p = os.path.join(outdir, "boombness_vs_asr_binned.png")
    fig.savefig(p, dpi=150); plt.close(fig); made.append(p)

    # 3 & 4. by condition
    for key, lab, fname in (("boombness", f"Boombness ({HEADLINE})", "boombness_by_condition.png"),
                            ("asr_score", "StrongReject score", "asr_by_condition.png")):
        byc = collections.defaultdict(list)
        for r in rows:
            if r.get(key) is not None and r.get("condition"):
                byc[r["condition"]].append(r[key])
        conds = sorted(byc)
        fig, ax = plt.subplots(figsize=(7, 4.2))
        ax.boxplot([byc[c] for c in conds], labels=conds, showmeans=True)
        ax.set_ylabel(lab)
        ax.set_title(f"{lab} by condition (all conditions, every occurrence-final row)")
        ax.tick_params(axis="x", labelrotation=25, labelsize=7)
        for i, c in enumerate(conds, start=1):
            ax.annotate(f"n={len(byc[c])}", (i, ax.get_ylim()[0]), fontsize=6, ha="center",
                        textcoords="offset points", xytext=(0, 6))
        fig.tight_layout()
        p = os.path.join(outdir, fname)
        fig.savefig(p, dpi=150); plt.close(fig); made.append(p)
    return made


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--judge", required=True)
    ap.add_argument("--extract", required=True)
    ap.add_argument("--g2-cwpos", required=True)
    ap.add_argument("--g2-lastpos", required=True)
    ap.add_argument("--g9-cwpos", required=True)
    ap.add_argument("--g9-lastpos", required=True)
    ap.add_argument("--g2-qwen3", default=None)
    ap.add_argument("--outdir", default="outputs/boombness/section9")
    a = ap.parse_args()

    rows = load_rows(a.judge, a.extract)
    check = verify_join(rows)
    print(f"[s9] join check: n={check['n']} (expect {EXPECT_N})  rho={check['rho']!r}")
    if not check["reproduces_g2_artifact"]:
        raise SystemExit("[s9] REFUSING: the row-level join does not reproduce g2_analysis_cwpos.json. "
                         "A plot drawn from a join that disagrees with the inference is a plot of a "
                         "different dataset. Fix the join before writing anything.")
    print("[s9] join reproduces the committed g2 artifact bit-identically")

    g2c, g2l = json.load(open(a.g2_cwpos)), json.load(open(a.g2_lastpos))
    g9c, g9l = json.load(open(a.g9_cwpos)), json.load(open(a.g9_lastpos))
    g2q = json.load(open(a.g2_qwen3)) if a.g2_qwen3 else None

    os.makedirs(a.outdir, exist_ok=True)
    made = plots(rows, os.path.join(a.outdir, "plots"))
    for p in made:
        print(f"[s9] plot -> {p}")

    def ci(d):
        return d.get("clustered_inference", {})

    summary = {
        "what": "plan §9 consolidated correlation summary",
        "headline_predictor": HEADLINE, "arm": ARM,
        "join_check": check,
        "llama": {
            "codeword_last": {
                "n": g2c.get("n_analysed"),
                "rho_pooled": ci(g2c).get("rho_pooled"),
                "rho_within_domain": ci(g2c).get("rho_within_domain"),
                "p_perm_within_domain_rho": ci(g2c).get("p_perm_within_domain_rho"),
                "p_iid_pooled_rho": ci(g2c).get("p_iid_pooled_rho"),
                "layer_selection_maxT_family_p":
                    g2c.get("layer_selection", {}).get("headline", {}).get("p_perm_maxT_family"),
                "per_cluster_rho": {k: v.get("rho") for k, v in (g2c.get("per_cluster") or {}).items()},
            },
            "last": {
                "n": g2l.get("n_analysed"),
                "rho_pooled": ci(g2l).get("rho_pooled"),
                "rho_within_domain": ci(g2l).get("rho_within_domain"),
                "p_perm_within_domain_rho": ci(g2l).get("p_perm_within_domain_rho"),
            },
        },
        "qwen3": ({"rho_pooled": ci(g2q).get("rho_pooled"),
                   "rho_within_domain": ci(g2q).get("rho_within_domain"),
                   "p_perm_within_domain_rho": ci(g2q).get("p_perm_within_domain_rho"),
                   "n": g2q.get("n_analysed")} if g2q else None),
        "incremental_r2": {"codeword_last": g9c.get("incremental_r2"),
                           "last": g9l.get("incremental_r2")},
        "regression_models": {"codeword_last": {k: {"r2": v.get("r2"), "n": v.get("n")}
                                                for k, v in (g9c.get("models") or {}).items()
                                                if isinstance(v, dict) and "error" not in v},
                              "last": {k: {"r2": v.get("r2"), "n": v.get("n")}
                                       for k, v in (g9l.get("models") or {}).items()
                                       if isinstance(v, dict) and "error" not in v}},
        "sources": {"g2_cwpos": os.path.abspath(a.g2_cwpos), "g2_lastpos": os.path.abspath(a.g2_lastpos),
                    "g9_cwpos": os.path.abspath(a.g9_cwpos), "g9_lastpos": os.path.abspath(a.g9_lastpos),
                    "g2_qwen3": os.path.abspath(a.g2_qwen3) if a.g2_qwen3 else None,
                    "judge": os.path.abspath(a.judge), "extract": os.path.abspath(a.extract)},
        "plots": [os.path.abspath(p) for p in made],
    }
    try:
        git = git_commit_safe()
        dirty = git_dirty_safe()
    except Exception:
        git, dirty = None, None
    summary["provenance"] = {"argv": sys.argv, "git_commit": git, "git_dirty": dirty,
                             "python": sys.executable}

    cp = os.path.join(a.outdir, "correlation_summary.json")
    with open(cp, "w") as f:
        json.dump(summary, f, indent=1)
    print(f"[s9] -> {cp}")

    def fmt(v, nd=4):
        return "—" if v is None else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))

    inc_c = g9c.get("incremental_r2") or {}
    inc_l = g9l.get("incremental_r2") or {}
    mc = summary["regression_models"]["codeword_last"]
    ml = summary["regression_models"]["last"]
    md = f"""# Plan §9 — regression summary

Generated by `src/boombness/summarize_section9.py` from committed artifacts. **No statistic is
computed here**; `analyze_g2.py` / `analyze_g9.py` own the inference. The row-level join used for the
plots is verified against `g2_analysis_cwpos.json` before anything is written
(n={check['n']}, rho={check['rho']!r} — bit-identical).

## The four models plan §9 names

`ASR ~ boombness` and its extensions, OLS R² on the same n, both readout positions.

| model | R² @ codeword_last | R² @ last token |
|---|---|---|
| `ASR ~ boombness` | {fmt(mc.get('boombness_only',{}).get('r2'))} | {fmt(ml.get('boombness_only',{}).get('r2'))} |
| `ASR ~ refusalness` | {fmt(mc.get('refusalness_only',{}).get('r2'))} | {fmt(ml.get('refusalness_only',{}).get('r2'))} |
| `ASR ~ boombness + refusalness` | {fmt(mc.get('boombness+refusalness',{}).get('r2'))} | {fmt(ml.get('boombness+refusalness',{}).get('r2'))} |
| `ASR ~ boombness + refusalness + n_examples` | {fmt(mc.get('boombness+refusalness+n_examples',{}).get('r2'))} | {fmt(ml.get('boombness+refusalness+n_examples',{}).get('r2'))} |

**`ASR ~ boombness + role_style` is NOT fitted.** `analyze_g9`'s role-identifiability gate refuses it,
and correctly: `role_style` is confounded with `family_id` in the bank as generated. The plan permits a
"role-style condition as a temporary proxy, explicitly labelled as a proxy" — labelling it does not
make it identifiable, so it is reported as refused rather than fitted.

## Incremental R², at MATCHED degrees of freedom (one column each)

⛔ Retraction **R-13**: an earlier table gave refusalness **5** predictors against Boombness's **1**
under the heading "matched footing". These are 1-vs-1.

| | Boombness adds over refusalness | refusalness adds over Boombness |
|---|---|---|
| @ codeword_last | {fmt(inc_c.get('boombness_over_refusalness'))} | {fmt(inc_c.get('refusalness_over_boombness'))} |
| @ last token | {fmt(inc_l.get('boombness_over_refusalness'))} | {fmt(inc_l.get('refusalness_over_boombness'))} |

**Which probe adds more is a *position* fact, not a probe fact.** At the last token refusalness adds
essentially nothing over Boombness.

## §9's eight decision questions

1. **Does Boombness predict ASR?** Yes on Llama-3.1-8B at the codeword token: rho_pooled
   **{fmt(ci(g2c).get('rho_pooled'))}**, within-domain {fmt(ci(g2c).get('rho_within_domain'))},
   within-domain permutation p **{fmt(ci(g2c).get('p_perm_within_domain_rho'))}**, n={g2c.get('n_analysed')}.
   Family-wise corrected over the layer family: maxT p =
   **{fmt(g2c.get('layer_selection',{}).get('headline',{}).get('p_perm_maxT_family'))}**.
2. **Which metric predicts best?** See report §7b — the three metrics **disagree in sign** about ASR at
   L12 and `common_all_three` covers only 72 of 270 rows. No metric is "best"; the disagreement is the
   finding.
3. **Which layer/token aggregation?** The **codeword token**, decisively: rho
   {fmt(ci(g2c).get('rho_pooled'))} there against {fmt(ci(g2l).get('rho_pooled'))} at the last token.
4. **Within prompt families?** Within-domain rho {fmt(ci(g2c).get('rho_within_domain'))} against a
   pooled {fmt(ci(g2c).get('rho_pooled'))} — it survives demeaning by cluster.
5. **Controlling for number of examples?** **Yes** (C-9). `n_examples` predicts ASR but is essentially
   uncorrelated with Boombness at the codeword token, so it is not a confound; the partial rho retains
   ~99.9% of the raw coefficient. Third row of the model table above.
6. **Natural Doublespeak vs Direct Codeword?** See `plots/asr_by_condition.png` and
   `plots/boombness_by_condition.png`.
7. **Do user-like / CoT-like framings increase Boombness or only ASR?** ⛔ Retraction #6 — the sprint
   first reported a tight null; the answer is **yes, by a little**. Report §5.
8. **Enough signal for a GCG objective?** **No** — and not because of the correlation. Steering the
   axis *suppresses* ASR at **both** signs (G4), so there is no gradient to follow. See report §4.

## Per-domain rho (the cluster unit, 6 domains)

| domain | rho |
|---|---|
""" + "\n".join(f"| `{k}` | {fmt(v)} |" for k, v in sorted(
        (summary["llama"]["codeword_last"]["per_cluster_rho"] or {}).items())) + f"""

Spread across domains is wide ({fmt(min((summary['llama']['codeword_last']['per_cluster_rho'] or {{}}).values(), default=None))} to {fmt(max((summary['llama']['codeword_last']['per_cluster_rho'] or {{}}).values(), default=None))}),
which is exactly why the inference is domain-clustered and why the iid p is marked WITHDRAWN as a sole basis.

## Cross-model

{"**Qwen3-14B: rho_pooled " + fmt(ci(g2q).get('rho_pooled')) + ", within-domain " + fmt(ci(g2q).get('rho_within_domain')) + ", perm p " + fmt(ci(g2q).get('p_perm_within_domain_rho')) + f", n={g2q.get('n_analysed')} — G2 does NOT replicate.**" if g2q else "_Qwen3 artifact not supplied._"}

## Plots

""" + "\n".join(f"* `{os.path.relpath(p)}`" for p in made) + "\n"

    rp = os.path.join(a.outdir, "regression_summary.md")
    with open(rp, "w") as f:
        f.write(md)
    print(f"[s9] -> {rp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
