#!/usr/bin/env python3
"""Render Phase A / Phase B JSON artifacts to markdown (no recomputation; numbers copied from the JSON).

Usage: python research/heretic_csi/phaseAB_report.py --phaseA <json> [--phaseB <json> ...] --out <md>
"""
import argparse
import json

ap = argparse.ArgumentParser()
ap.add_argument("--phaseA", default=None)
ap.add_argument("--phaseB", action="append", default=[])
ap.add_argument("--out", required=True)
a = ap.parse_args()
L = []
f = lambda x, d=4: (f"{x:.{d}g}" if isinstance(x, float) else str(x))  # noqa: E731

if a.phaseA:
    R = json.load(open(a.phaseA))
    c, v = R["checks"], R["verdicts"]
    L += [f"# Phase A — Heretic machinery audit (`{a.phaseA}`)", "",
          f"Env: {R['env']}", f"Params (fixed): `{json.dumps(R['params'])}`, rank={R['argv']['rank']}", "",
          "| check | value | verdict |", "|---|---|---|",
          f"| load | {c['load']} | eager+bf16={v['load_eager_bf16']} |",
          f"| identity after apply_lora (B=0) | max|dlogit|={f(c['identity_after_apply_lora']['max_abs_logit_diff'])} | {v['identity_exact']} |",
          f"| modify changes model | max|dlogit|={f(c['modify_changes_logits']['max_abs_logit_diff'])}, mean KL={f(c['modify_changes_logits']['mean_KL_base_to_mod'])} (n={c['modify_changes_logits']['n']}) | {v['modify_nonzero']} |",
          f"| reset -> base | max|dlogit|={f(c['reset']['max_abs_logit_diff_vs_base'])}, greedy16 identical={c['reset']['greedy16_identical']} (n={c['reset']['n_gen_prompts']}), max|dW| after reset={f(c['reset']['max_abs_dW_after_reset'])} | {v['reset_exact']} |",
          f"| replay same params | max rel ||dW1-dW2||={f(c['replay']['max_rel_fro_dW_diff'])}, max|dlogit|={f(c['replay']['max_abs_logit_diff_vs_mod1'])} | {v['replay_dW_rel_lt_1e-3']} |",
          f"| Optuna resume | {c['optuna_resume']['n_trials_first_session']} -> loaded {c['optuna_resume']['n_trials_loaded_on_resume']} -> {c['optuna_resume']['n_trials_after_resume']}; trial0 value {f(c['optuna_resume']['trial0_value'])} vs replay {f(c['optuna_resume']['trial0_replay_value'])} | {v['optuna_resumed']} |"]
    if "readout_xcheck_vs_score_behavior" in c:
        x = c["readout_xcheck_vs_score_behavior"]
        L += [f"| y_install readout vs frozen score_behavior | n={x['n']}, max|dy|={f(x['max_abs_dy_install'])}, max|dlogp_c|={f(x['max_abs_dlogp_concept'])} | {v['readout_xcheck_max_dy_lt_0.02']} |"]
    L += ["", "## Learned dW per module (ARA, preserve_row_magnitudes=True)", "",
          "| layer | comp | ||dW||_F | ||dW||/||W|| | num. rank (cfg) | eff. rank | top-3 s | rel gap deployed vs objective-form | ARA loss base / deployed / objective-form |",
          "|---|---|---|---|---|---|---|---|---|"]
    for m in R["modules"]:
        L.append(f"| {m['layer']} | {m['component']} | {f(m['fro_dW'])} | {f(m['rel_fro'])} | {m['numerical_rank']} ({m['configured_rank']}) | {f(m['effective_rank_entropy'],3)} | {', '.join(f(s,3) for s in m['top_singular'][:3])} | {f(m['rel_gap_deployed_vs_objective'])} | {f(m['ara_loss_base'])} / {f(m['ara_loss_deployed_W_plus_BA'])} / {f(m['ara_loss_objective_form'])} |")
    L += ["", f"max rel gap (deployed W+BA vs objective-form normalize(W+BA)*||W||_row): **{f(v['max_rel_gap_deployed_vs_objective'])}**", ""]

for pb in a.phaseB:
    R = json.load(open(pb))
    L += [f"# Phase B — native last-position Heretic ARA as a control: `{R['codeword']}` (`{pb}`)", "",
          f"Freeze rule (predeclared): {R['freeze_rule']}. Chosen trial {R.get('chosen_trial')} (feasible={R.get('chosen_feasible')}); Pareto front: {R.get('pareto_front')}",
          f"Readout impl: {R.get('readout_impl')}; readout xcheck vs frozen score_behavior: {R.get('readout_xcheck')}", "",
          "## Optuna trials (TRAIN objectives)", "", "| trial | params | scores | s |", "|---|---|---|---|"]
    for t in R.get("trials", []):
        L.append(f"| {t['number']} | `{json.dumps(t['params'])}` | {', '.join(f'{k}={f(x)}' for k, x in t['named'].items())} | {f(t['seconds'],3)} |")
    if "ara" in R:
        L += ["", "## Frozen-ARA reads (domain-mean y_install; dY vs base, same rows)", "",
              "| set | base y | ARA y | dY | n_rows/n_dom | median option mass base->ARA | mean logp concept base->ARA | mean logp codeword base->ARA |",
              "|---|---|---|---|---|---|---|---|"]
        for n, rd in R["ara"]["reads"].items():
            b = R["base"][n]
            L.append(f"| {n} | {f(b['y_domain_mean'])} | {f(rd['y_domain_mean'])} | {f(R['ara']['dY'][n])} | {rd['n_rows']}/{rd['n_domains']} | {f(b['median_option_mass'])} -> {f(rd['median_option_mass'])} | {f(b['mean_logp_concept'])} -> {f(rd['mean_logp_concept'])} | {f(b['mean_logp_codeword'])} -> {f(rd['mean_logp_codeword'])} |")
        L += ["", f"KL(base||ARA) on val_C first token: {f(R['ara']['kl_val_C'])}",
              f"Keyword refusal (SECONDARY; Heretic KeywordRate, 46 behavioral val C prompts): base {f(R['base_refusal']['rate'])} -> ARA {f(R['ara']['refusal']['rate'])}"]
    if "primary" in R:
        p = R["primary"]
        L += ["", "## Primary (val_A) vs rank-matched controls", "",
              f"observed dY_val_A = **{f(p['observed'])}**; rank {p['rank_from_top']}/{p['n_controls']+1}; one-sided p = {f(p['p_one_sided'])} (floor {f(p['floor'])}); installation fraction of the base C-A gap = {f(p['installation_fraction'])}", "",
              "| control | dY_val_A |", "|---|---|"]
        for cc in sorted(R["controls"], key=lambda x: -x["dY_val_A"]):
            L.append(f"| {cc['kind']} #{cc['i']} | {f(cc['dY_val_A'])} |")
    if R.get("extra_ranks"):
        L += ["", "## Frozen params refit at other ranks (descriptive / MEASURED)", "", "| rank | dY val_A | dY val_C | KL val_C |", "|---|---|---|---|"]
        for r, e in R["extra_ranks"].items():
            L.append(f"| {r} | {f(e['dY']['val_A'])} | {f(e['dY']['val_C'])} | {f(e['kl_val_C'])} |")
    L.append("")

open(a.out, "w").write("\n".join(L) + "\n")
print("wrote", a.out)
