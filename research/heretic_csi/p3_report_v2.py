#!/usr/bin/env python3
"""Render reports/heretic_csi/P3_SVD_REPORT_v2.md (supersedes P3_SVD_REPORT.md, which is kept) from
P3_svd_descriptive_v2.json, P3_write_direction_v2.json and P3_alignment_aniso.json. Changes vs v1 (review #2 MEDIUM-8):
alignment judged against an ANISOTROPIC null (directions drawn from the module-output covariance) with a
DIMENSION-MATCHED null for the PLS-4 subspace statistic; effective rank labelled 'energy-entropy'; the shared write
direction is stated as largely expected by construction."""
import json, os
REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
R = os.path.join(REPO, "reports/heretic_csi")
d = json.load(open(os.path.join(R, "P3_svd_descriptive_v2.json")))
w = json.load(open(os.path.join(R, "P3_write_direction_v2.json")))
an = json.load(open(os.path.join(R, "P3_alignment_aniso.json")))
med = lambda xs: sorted(xs)[len(xs) // 2]   # noqa: E731
L = ["# P3 v2 — SVD / geometry of the learned P2b weight operators (DESCRIPTIVE)", "",
     "Supersedes `P3_SVD_REPORT.md` (kept for provenance). Sources: `P3_svd_descriptive_v2.json`, "
     "`P3_write_direction_v2.json`, `P3_alignment_aniso.json`. TRAIN-fitted operators (objective mse / steer 0.3). "
     "Geometry of the FIT only — no endpoint, no causal claim. Total norm = sqrt(sum of squared per-module Frobenius norms). "
     "Effective rank = **energy-entropy** rank exp(H(s²/Σs²)) (smaller than the s/Σs version).", "",
     "## Per-cell summary (CAND)", "",
     "| cw | rank | total ‖ΔW‖ | o_proj share of ‖ΔW‖² | top-3 layers by ‖ΔW‖² share | median energy-entropy eff. rank | median top-1 Frobenius frac | median ‖ΔW‖/‖W‖ |",
     "|---|---|---|---|---|---|---|---|"]
cells = sorted([c for c in d["cells"] if c["key"] == "CAND"], key=lambda c: (c["codeword"], c["rank"]))
for c in cells:
    m = c["modules"]
    top = sorted(c["norm2_by_layer"].items(), key=lambda kv: -kv[1])[:3]
    L.append(f"| {c['codeword']} | {c['rank']} | {c['total_fro']:.2f} | {c['norm2_by_comp']['o_proj']:.3f} | "
             + ", ".join(f"L{k} {v:.2f}" for k, v in top)
             + f" | {med([x['eff_rank'] for x in m]):.2f} | {med([x['cum_frac'][0] for x in m]):.3f} | {med([x['rel'] for x in m]):.4f} |")
L += ["", "## Cross-codeword overlap of CAND write subspaces (same rank, same module): mean cos² of principal angles (null k/4096)", "",
      "| rank | median over modules | min | max |", "|---|---|---|---|"]
by = {}
for x in d.get("cross_codeword", []):
    by.setdefault(x["rank"], []).append(x["mean_cos2"])
for r in sorted(by):
    v = by[r]; L.append(f"| {r} | {med(v):.3f} | {min(v):.3f} | {max(v):.3f} |")
L += ["", "## Alignment vs the ANISOTROPIC null (review #2 fix)", "",
      "Statistic: squared projection of the reference direction on the write subspace U_k (k=min(r,4)). p_aniso = upper-tail "
      "empirical p against 2000 directions drawn from the module's clean codeword-row output covariance; p_iso = the old "
      "isotropic null (for comparison). PLS-4 uses a dimension-matched 4-d subspace null (isotropic and anisotropic).", "",
      "| cw | rank | #stats | #p_iso ≤ 0.01 | #p_aniso ≤ 0.01 | stats with p_aniso ≤ 0.01 |", "|---|---|---|---|---|---|"]
for c in sorted(an["cells"], key=lambda c: (c["codeword"], c["rank"])):
    tot = iso = ani = 0; hits = []
    for n, m in c["modules"].items():
        for k, v in m["align"].items():
            tot += 1
            pi = v.get("p_iso", v.get("p_iso4")); pa_ = v.get("p_aniso", v.get("p_aniso4"))
            iso += pi <= 0.01; ani += pa_ <= 0.01
            if pa_ <= 0.01:
                hits.append(f"{n}:{k}={v['s']:.4f}")
    L.append(f"| {c['codeword']} | {c['rank']} | {tot} | {iso} | {ani} | {', '.join(hits) if hits else 'none'} |")
L += ["", "## What the operator WRITES: the mean KO→clean output gap", ""]
for cw, v in w["per_codeword"].items():
    fm = [x["frac_mean_gap"] for x in v["modules"].values()]
    L.append(f"- **{cw}**: share of per-prompt gap energy that is the common mean shift: min {min(fm):.2f} / median {med(fm):.2f} / max {max(fm):.2f}.")
    for k, row in sorted(v["operators"].items(), key=lambda kv: (int(kv[0].split(":")[0][1:]), kv[0])):
        L.append(f"  - {k}: mean |cos(U1, mean gap)| = {sum(x['g'] for x in row.values())/len(row):.3f}")
cc = w["cross_codeword_gap_cos"]
L.append("- **cross-codeword** |cos(mean gap basket, mean gap button)|: " + ", ".join(f"{k} {v:.2f}" for k, v in cc.items()))
L += ["", "## Reading (descriptive only)", "",
      "- At ranks 1–2 the candidate and every fitted control (DER, SHUF) write along the mean KO→clean output gap g "
      "(|cos(U1, g)| ≈ 1.00). This is **largely expected by construction** (review #2): a DER pairing is a permutation of "
      "all rows, so its mean target−source equals g exactly, and a rank-1 MSE fit of a mostly-common shift recovers g. "
      "Consequence (unchanged): candidate-vs-DER/SHUF tests input-side (read, A) specificity only; candidate-vs-RAND also "
      "tests the write direction; an input-independent mean-gap (bias) control would be needed to separate 'adds the "
      "mean shift' from 'input-conditional operator'.",
      "- The mean gap is a large common component (see shares above) and is largely codeword-general at L6–14, less so at "
      "L18 (cross-codeword cosines above).",
      "- Alignment with refusal / d_surface / PLS: under the ANISOTROPIC null **no statistic reaches p ≤ 0.01 in any "
      "cell** (table). The anisotropic null mean is 0.01–0.22 (q99 0.07–0.54) because the write subspace lies in the "
      "high-variance part of each module's output; the reference directions project on it LESS than a typical "
      "activation direction does, while still MORE than an isotropic random direction (the isotropic null flags many "
      "modules). The two nulls bracket the answer and all absolute values are tiny (squared projection ≤ ~0.04, "
      "|cos| ≤ ~0.2). Positive-control sanity: a genuinely aligned direction (squared projection ≈ 1, e.g. the mean gap "
      "g itself at r1) would exceed every anisotropic q99 (max 0.54), so the null is not powerless. **Conclusion: no "
      "evidence that the learned operators write along refusal, d_surface or the P2a probe axes.**",
      "- PLS-4 (L18) uses a dimension-matched 4-d null; see `P3_alignment_aniso.json` (`p_iso4`, `p_aniso4`)."]
open(os.path.join(R, "P3_SVD_REPORT_v2.md"), "w").write("\n".join(L) + "\n")
print("wrote P3_SVD_REPORT_v2.md")
