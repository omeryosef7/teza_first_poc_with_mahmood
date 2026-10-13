#!/usr/bin/env python3
"""HERETIC-CSI Phase A (mandate §5): audit Heretic's OWN Model + ARA machinery on Llama-3.1-8B-Instruct.

Runs in the isolated `heretic_csi` venv (pinned Heretic @ 662e4ba2, torch 2.13 / transformers 5.6 /
peft 0.19 / optuna 4.8). Uses Heretic's classes UNCHANGED; the only deviation is a wrapper that forces
`attn_implementation="eager"` at load (CSI constant; Heretic itself sets none => SDPA). No upstream patch.

Checks (each recorded with numbers, not "the command completed"):
  1. model loads (dtype, attn impl actually in effect);
  2. identity: logits after `apply_lora` (B=0) == base logits;
  3. ARA modify with a fixed small parameter set changes logits;
  4. learned dW per module: Frobenius norm, singular spectrum, numerical rank vs configured lora_rank;
  5. DEPLOYED-vs-OPTIMIZED operator: with preserve_row_magnitudes=True ARA's loss is computed on
     normalize(W+BA)*||W||_row but PEFT runs W+BA. We measure the gap (both dW and ARA loss);
  6. reset: logits + greedy generations after `reset_model` == base (max-abs error);
  7. replay: re-running modify with the same params reproduces dW (max-abs diff) and logits;
  8. Optuna JournalStorage resume on a toy 2+1-trial study; replay of a stored trial reproduces its value.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--bank", required=True)
ap.add_argument("--split-file", required=True)
ap.add_argument("--out", required=True, help="output stem, e.g. reports/heretic_csi/PHASE_A_heretic_audit")
ap.add_argument("--workdir", required=True, help="empty dir (Heretic reads ./config.toml if present)")
ap.add_argument("--rank", type=int, default=8)
ap.add_argument("--start-layer", type=int, default=12)
ap.add_argument("--end-layer", type=int, default=16)
ap.add_argument("--n-prompts", type=int, default=16)
ap.add_argument("--optuna-trials", type=int, default=2)
ap.add_argument("--seed", type=int, default=20261013)
ap.add_argument("--xcheck-run-dir", default=None, help="frozen score_behavior BASE run dir (same bank) for readout cross-check")
ap.add_argument("--xcheck-n", type=int, default=24)
A = ap.parse_args()
sys.argv = [sys.argv[0]]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Heretic Settings parses CLI args; give it none.
os.makedirs(A.workdir, exist_ok=True)
assert not os.path.exists(os.path.join(A.workdir, "config.toml")), "workdir must not contain config.toml"
OUT_STEM = os.path.abspath(A.out)
A.bank, A.split_file = os.path.abspath(A.bank), os.path.abspath(A.split_file)
if A.xcheck_run_dir:
    A.xcheck_run_dir = os.path.abspath(A.xcheck_run_dir)
os.chdir(A.workdir)

import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402
import transformers  # noqa: E402
import optuna  # noqa: E402
from optuna.samplers import TPESampler  # noqa: E402
from optuna.storages import JournalStorage  # noqa: E402
from optuna.storages.journal import JournalFileBackend, JournalFileOpenLock  # noqa: E402

import heretic.model as hm  # noqa: E402
from heretic.config import Settings, SingleDatasetSpecification  # noqa: E402
from heretic.plugin import Context  # noqa: E402
from heretic.modifiers.ara import ARA, Parameters, Settings as ARASettings, ara_loss  # noqa: E402
from heretic.utils import Prompt  # noqa: E402

_orig_gmc = hm.get_model_class


class _EagerLoader:
    """Wraps the class Heretic picks so from_pretrained always gets attn_implementation='eager'."""

    def __init__(self, cls):
        self.cls = cls

    def from_pretrained(self, *a, **k):
        k.setdefault("attn_implementation", "eager")
        return self.cls.from_pretrained(*a, **k)


hm.get_model_class = lambda m: _EagerLoader(_orig_gmc(m))

T0 = time.time()
R: dict = {"schema": "hcsi_phaseA/1", "argv": vars(A), "checks": {}, "env": {
    "torch": torch.__version__, "cuda": torch.version.cuda, "transformers": transformers.__version__,
    "optuna": optuna.__version__, "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    "compute_cap": list(torch.cuda.get_device_capability(0)) if torch.cuda.is_available() else None,
    "slurm_job": os.environ.get("SLURM_JOB_ID"), "slurm_restart": os.environ.get("SLURM_RESTART_COUNT", "0"),
}}
cap = R["env"]["compute_cap"]
if cap is None or cap[0] < 8:
    raise SystemExit(f"REFUSE: native bf16 requires compute capability >= 8.0, got {cap}")


def log(*x):
    print(f"[{time.time()-T0:7.1f}s]", *x, flush=True)


# ---------------- data: real TRAIN rows (cell C vs cell A, semantic_one_word, basket) ----------------
split = json.load(open(A.split_file))
train_domains = {d for d, s_ in split["assign"].items() if s_ == "train"}
assert len(train_domains) == split["n_train"], (len(train_domains), split["n_train"])
rows = [json.loads(l) for l in open(A.bank)]
rows = [r for r in rows if r.get("query_kind") == "semantic_one_word" and r.get("domain") in train_domains]
byc = {c: sorted([r for r in rows if r["cell"] == c], key=lambda r: (r["domain"], r["prompt_id"])) for c in "AC"}
n = A.n_prompts
good_rows, bad_rows = byc["C"][:n], byc["A"][:n]  # mechanics only; Phase B defines the science populations
eval_rows = byc["C"][n:n + 8] + byc["A"][n:n + 8]
os.makedirs("ds_good", exist_ok=True)
os.makedirs("ds_bad", exist_ok=True)
for d, rr in (("ds_good", good_rows), ("ds_bad", bad_rows)):
    with open(os.path.join(d, "train.jsonl"), "w") as fh:
        for r in rr:
            fh.write(json.dumps({"text": r["full_prompt"]}) + "\n")
R["data"] = {"n_good": len(good_rows), "n_bad": len(bad_rows), "n_eval": len(eval_rows),
             "good_ids_sha16": hashlib.sha256("|".join(r["prompt_id"] for r in good_rows).encode()).hexdigest()[:16],
             "bad_ids_sha16": hashlib.sha256("|".join(r["prompt_id"] for r in bad_rows).encode()).hexdigest()[:16]}

settings = Settings(model=A.model, dtypes=["bfloat16"], device_map="auto", batch_size=8, max_batch_size=8,
                    seed=A.seed, system_prompt="", study_checkpoint_dir="ckpt")
transformers.set_seed(A.seed)
log("loading model")
model = hm.Model(settings)
attn = getattr(model.model.config, "_attn_implementation", None)
R["checks"]["load"] = {"ok": True, "dtype": str(model.dtype), "attn_implementation": attn,
                       "n_layers": len(model.get_layers())}
assert attn == "eager", f"eager not in effect: {attn}"
log("loaded", R["checks"]["load"])

# ---------------- readout cross-check: our whole_answer port vs frozen score_behavior BASE rows ----------------
if A.xcheck_run_dir:
    from semantic_installation_scorer import readout_rows  # noqa: E402
    ref = [json.loads(l) for l in open(os.path.join(A.xcheck_run_dir, "results.jsonl"))]
    ref = [r for r in ref if r.get("readout") == "semantic"][:A.xcheck_n]
    bank_by_id = {}
    with open(A.bank) as fh:
        for l in fh:
            r = json.loads(l)
            bank_by_id[r["prompt_id"]] = r
    mine = readout_rows(model, [bank_by_id[r["prompt_id"]] for r in ref], "bomb", ref[0]["target_surface"])
    dc = [abs(m["logp_concept"] - r["logp_concept"]) for m, r in zip(mine, ref)]
    dk = [abs(m["logp_codeword"] - r["logp_codeword"]) for m, r in zip(mine, ref)]
    yr = [1 / (1 + math.exp(-(r["logp_concept"] - r["logp_codeword"]))) for r in ref]
    dy = [abs(m["y_install"] - y) for m, y in zip(mine, yr)]
    R["checks"]["readout_xcheck_vs_score_behavior"] = {
        "ref_run_dir": A.xcheck_run_dir, "n": len(ref), "max_abs_dlogp_concept": max(dc),
        "max_abs_dlogp_codeword": max(dk), "max_abs_dy_install": max(dy), "mean_abs_dy_install": sum(dy) / len(dy),
        "note": "ref = poc_stage2 (older transformers) eager bf16; ours = heretic_csi env eager bf16; same rows"}
    log("xcheck", R["checks"]["readout_xcheck_vs_score_behavior"])

eval_prompts = [Prompt(system=settings.system_prompt, user=r["full_prompt"]) for r in eval_rows]
gen_prompts = eval_prompts[:4]


def logits():
    return model.get_logits_batched(eval_prompts).float().cpu()


def _gen_ids():
    inputs, outs = model.generate(gen_prompts, max_new_tokens=16)
    return [o[inputs["input_ids"].shape[1]:].tolist() for o in outs]


def kl_rows(p_logits, q_logits):
    lp, lq = F.log_softmax(p_logits, -1), F.log_softmax(q_logits, -1)
    return (lp.exp() * (lp - lq)).sum(-1)


L_base = logits()
G_base = _gen_ids()
L_base2 = logits()
R["checks"]["base_determinism"] = {"max_abs_logit_diff_base_vs_base": float((L_base2 - L_base).abs().max())}
log("base logits", tuple(L_base.shape))

# ---------------- ARA init (captures module I/O at [:, -1, :], applies zero-B LoRA) ----------------
ara_settings = ARASettings(
    good_prompts=SingleDatasetSpecification(dataset=os.path.abspath("ds_good"), split="train", column="text"),
    bad_prompts=SingleDatasetSpecification(dataset=os.path.abspath("ds_bad"), split="train", column="text"),
    lora_rank=A.rank, preserve_row_magnitudes=True)
ara = ARA(heretic_settings=settings, settings=ara_settings)
ctx = Context(settings=settings, model=model)
ara.init(ctx)
L_id = logits()
G_id = _gen_ids()
R["checks"]["identity_after_apply_lora"] = {"max_abs_logit_diff": float((L_id - L_base).abs().max()),
                                            "max_KL_base_to_identity": float(kl_rows(L_base, L_id).max()),
                                            "greedy16_identical_to_base": G_id == G_base}
A_INIT = {}
log("identity", R["checks"]["identity_after_apply_lora"])

params = Parameters(start_layer_index=A.start_layer, end_layer_index=A.end_layer,
                    preserve_good_behavior_weight=0.5, steer_bad_behavior_weight=0.1,
                    overcorrect_relative_weight=0.5, neighbor_count=5)
R["params"] = params.to_dict()


def module_iter():
    for li in range(params.start_layer_index, params.end_layer_index):
        for comp, mods in model.get_layer_modules(li).items():
            for mi, m in enumerate(mods):
                yield li, comp, mi, m


def snapshot_dw():
    out = {}
    for li, comp, mi, m in module_iter():
        A_ = m.lora_A["default"].weight.detach().float()
        B_ = m.lora_B["default"].weight.detach().float()
        sc = float(m.scaling["default"])
        out[(li, comp, mi)] = (sc * (B_ @ A_)).cpu()
    return out


def module_report(dws):
    rep = []
    for (li, comp, mi), dW in dws.items():
        m = model.get_layer_modules(li)[comp][mi]
        W = m.base_layer.weight.detach().float().cpu()
        rn = W.norm(dim=1, keepdim=True)
        dW_obj = F.normalize(W + dW, p=2, dim=1) * rn - W  # what ARA's loss "sees"
        S = torch.linalg.svdvals(dW.cuda()).cpu()
        tol = float(S.max()) * max(dW.shape) * torch.finfo(torch.float32).eps if S.numel() else 0.0
        p = (S ** 2) / (S ** 2).sum().clamp_min(1e-30)
        eff_rank = float(torch.exp(-(p * (p.clamp_min(1e-30)).log()).sum()))
        S_obj = torch.linalg.svdvals(dW_obj.cuda()).cpu()
        # ARA loss on the captured I/O, evaluated with deployed vs objective-form weights
        gi, go = ara.good_module_io[li][comp][mi]
        bi, bo = ara.bad_module_io[li][comp][mi]
        gi, go, bi, bo = gi.float(), go.float(), bi.float(), bo.float()

        def loss_with(Weff):
            return float(ara_loss(go, bo, gi @ Weff.T, bi @ Weff.T, params))
        rep.append({
            "layer": li, "component": comp, "module": mi,
            "fro_dW": float(dW.norm()), "fro_W": float(W.norm()), "rel_fro": float(dW.norm() / W.norm()),
            "configured_rank": A.rank, "numerical_rank": int((S > tol).sum()), "effective_rank_entropy": eff_rank,
            "top_singular": [float(s) for s in S[:min(10, S.numel())]],
            "fro_dW_objective_form": float(dW_obj.norm()),
            "numerical_rank_objective_form": int((S_obj > float(S_obj.max()) * max(dW.shape) * 1.2e-7).sum()),
            "rel_gap_deployed_vs_objective": float((dW - dW_obj).norm() / dW_obj.norm().clamp_min(1e-30)),
            "ara_loss_base": loss_with(W), "ara_loss_deployed_W_plus_BA": loss_with(W + dW),
            "ara_loss_objective_form": loss_with(W + dW_obj),
        })
    return rep


def all_modules():
    for li in range(len(model.get_layers())):
        for comp, mods in model.get_layer_modules(li).items():
            for mi, m in enumerate(mods):
                yield li, comp, mi, m


for li, comp, mi, m in all_modules():  # PEFT's random lora_A init = the state modify #1 starts from
    A_INIT[(li, comp, mi)] = m.lora_A["default"].weight.detach().clone()


def restore_A():
    with torch.no_grad():
        for li, comp, mi, m in all_modules():
            m.lora_A["default"].weight.copy_(A_INIT[(li, comp, mi)])


log("modify #1")
t = time.time()
ara.modify_model(ctx, params)
R["checks"]["modify_seconds"] = time.time() - t
dW1 = snapshot_dw()
L_mod = logits()
kl_mod = kl_rows(L_base, L_mod)
R["checks"]["modify_changes_logits"] = {"max_abs_logit_diff": float((L_mod - L_base).abs().max()),
                                        "mean_KL_base_to_mod": float(kl_mod.mean()), "n": int(kl_mod.numel())}
R["modules"] = module_report(dW1)
log("modify done", R["checks"]["modify_changes_logits"])

log("reset")
ara.reset_model(ctx)
L_reset = logits()
G_reset = _gen_ids()
dW_reset = snapshot_dw()
R["checks"]["reset"] = {
    "max_abs_logit_diff_vs_base": float((L_reset - L_base).abs().max()),
    "max_abs_logit_diff_vs_identity": float((L_reset - L_id).abs().max()),
    "max_abs_dA_vs_init_after_reset": max(float((m.lora_A["default"].weight - A_INIT[(li, c, mi)]).abs().max())
                                         for li, c, mi, m in module_iter()),
    "greedy16_identical": G_reset == G_base, "n_gen_prompts": len(G_base),
    "max_abs_dW_after_reset": max(float(v.abs().max()) for v in dW_reset.values())}
log("reset", R["checks"]["reset"])

log("replay (modify #2 with identical params; shipped reset keeps lora_A from modify #1)")
transformers.set_seed(A.seed)
ara.modify_model(ctx, params)
dW2 = snapshot_dw()
L_mod2 = logits()
R["checks"]["replay_shipped_history_dependent"] = {
    "max_abs_dW_diff": max(float((dW1[k] - dW2[k]).abs().max()) for k in dW1),
    "max_rel_fro_dW_diff": max(float((dW1[k] - dW2[k]).norm() / dW1[k].norm().clamp_min(1e-30)) for k in dW1),
    "max_abs_logit_diff_vs_mod1": float((L_mod2 - L_mod).abs().max())}
log("replay shipped", R["checks"]["replay_shipped_history_dependent"])
ara.reset_model(ctx)
restore_A()
ara.modify_model(ctx, params)
dW3 = snapshot_dw()
L_mod3 = logits()
R["checks"]["replay"] = {
    "note": "reset + lora_A restored to its post-apply_lora value (the state modify #1 started from)",
    "max_abs_dW_diff": max(float((dW1[k] - dW3[k]).abs().max()) for k in dW1),
    "max_rel_fro_dW_diff": max(float((dW1[k] - dW3[k]).norm() / dW1[k].norm().clamp_min(1e-30)) for k in dW1),
    "max_abs_logit_diff_vs_mod1": float((L_mod3 - L_mod).abs().max())}
log("replay A-restored", R["checks"]["replay"])
ara.reset_model(ctx)

# ---------------- Optuna resume (Heretic's own sampler/storage config) ----------------
jpath = os.path.abspath("optuna_toy.journal")
if os.path.exists(jpath):
    os.remove(jpath)


def make_study():
    st = JournalStorage(JournalFileBackend(jpath, lock_obj=JournalFileOpenLock(jpath)))
    return optuna.create_study(sampler=TPESampler(n_startup_trials=30, n_ei_candidates=128, multivariate=True,
                                                  seed=A.seed), storage=st, directions=["minimize"],
                               study_name="heretic", load_if_exists=True)


def toy_objective(trial):
    p = ara.suggest_parameters(ctx, trial)
    # keep the toy cheap: clamp to a 4-layer window inside the suggested range (recorded)
    p.end_layer_index = min(p.end_layer_index, p.start_layer_index + 4)
    trial.set_user_attr("parameters", p.to_dict())
    ara.reset_model(ctx)
    restore_A()
    ara.modify_model(ctx, p)
    v = float(kl_rows(L_base, logits()).mean())
    ara.reset_model(ctx)
    return v


s1 = make_study()
s1.optimize(toy_objective, n_trials=A.optuna_trials)
n_before = len(s1.trials)
del s1
s2 = make_study()  # resume from journal
n_loaded = len(s2.trials)
s2.optimize(toy_objective, n_trials=1)
t0 = s2.trials[0]
p0 = Parameters.from_dict(t0.user_attrs["parameters"])
ara.reset_model(ctx)
restore_A()
ara.modify_model(ctx, p0)
v_replay = float(kl_rows(L_base, logits()).mean())
ara.reset_model(ctx)
R["checks"]["optuna_resume"] = {"n_trials_first_session": n_before, "n_trials_loaded_on_resume": n_loaded,
                                "n_trials_after_resume": len(s2.trials),
                                "trial0_value": t0.values[0], "trial0_replay_value": v_replay,
                                "trial0_abs_diff": abs(t0.values[0] - v_replay),
                                "trial_values": [tr.values[0] for tr in s2.trials],
                                "note": "toy objective = mean KL(base||mod) on 16 eval prompts; end_layer clamped to start+4"}
log("optuna", R["checks"]["optuna_resume"])

# ---------------- verdicts ----------------
c = R["checks"]
xc = c.get("readout_xcheck_vs_score_behavior")
R["verdicts"] = {
    "load_eager_bf16": c["load"]["attn_implementation"] == "eager" and "bfloat16" in c["load"]["dtype"],
    "base_deterministic": c["base_determinism"]["max_abs_logit_diff_base_vs_base"] == 0.0,
    # identity: LoRA-wrapped (B=0) vs unwrapped base may differ at bf16 rounding; require greedy-identical + KL<1e-4
    "identity_within_bf16": c["identity_after_apply_lora"]["greedy16_identical_to_base"]
    and c["identity_after_apply_lora"]["max_KL_base_to_identity"] < 1e-4,
    "modify_nonzero": c["modify_changes_logits"]["max_abs_logit_diff"] > 0,
    "rank_le_configured": all(m["numerical_rank"] <= A.rank for m in R["modules"]),
    "reset_exact_to_identity": c["reset"]["max_abs_logit_diff_vs_identity"] == 0.0 and c["reset"]["greedy16_identical"]
    and c["reset"]["max_abs_dW_after_reset"] == 0.0,
    "reset_keeps_lora_A": c["reset"]["max_abs_dA_vs_init_after_reset"] > 0,
    "replay_A_restored_rel_lt_1e-3": c["replay"]["max_rel_fro_dW_diff"] < 1e-3,
    "replay_shipped_rel": c["replay_shipped_history_dependent"]["max_rel_fro_dW_diff"],
    "optuna_resumed": c["optuna_resume"]["n_trials_loaded_on_resume"] == A.optuna_trials
    and c["optuna_resume"]["n_trials_after_resume"] == A.optuna_trials + 1,
    "optuna_trial0_replay_abs_diff": c["optuna_resume"]["trial0_abs_diff"],
    # readout fidelity: the FROZEN pipeline's own cross-GPU-type noise is mean|dy| 0.009-0.013 (max up to 0.25);
    # within one GPU type it is exactly 0. Criterion: mean|dy| <= 0.015 (cross-hardware envelope).
    "readout_xcheck_mean_dy_le_0.015": (xc["mean_abs_dy_install"] <= 0.015) if xc else None,
    "max_rel_gap_deployed_vs_objective": max(m["rel_gap_deployed_vs_objective"] for m in R["modules"]),
}
R["wall_seconds"] = time.time() - T0
att = f"job{R['env']['slurm_job']}_r{R['env']['slurm_restart']}"
with open(f"{OUT_STEM}_{att}.json", "w") as fh:
    json.dump(R, fh, indent=2)
log("wrote", f"{OUT_STEM}_{att}.json")
print("VERDICTS", json.dumps(R["verdicts"]), flush=True)
print("PHASEA_DONE", flush=True)
