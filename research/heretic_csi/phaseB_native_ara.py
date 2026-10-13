#!/usr/bin/env python3
"""HERETIC-CSI Phase B (mandate §6): NATIVE Heretic ARA (shipped modifier, last-prefill position) as a CONTROL.

Uses Heretic's own Model / Evaluator / ARA / KLDivergence / Optuna (multivariate TPE + JournalStorage, as in
heretic/main.py) on OUR frozen populations (research/heretic_csi/phaseB_make_datasets.py), configured
through a generated config.toml (Heretic's native input). The only deviation from shipped Heretic is a
loader wrapper forcing attn_implementation="eager" (CSI constant); system_prompt="" so the Llama-3.1 chat
template is byte-identical to the CSI no-system template (verified 2026-10-13).

Objectives (Heretic Scorer plugins): maximize y_install on opt_A (SOURCE rows, TRAIN, plugin
semantic_installation_scorer.py), minimize Heretic KLDivergence on opt_C texts; y_install on opt_C
recorded (optimization="none").

PREDECLARED FREEZE RULE v2 (2026-10-14, after adversarial review; v1 = jobs 1023185/1023251 lacked the
option-mass clause): among COMPLETE trials with KL <= 1.0 AND opt_A median option mass >= 0.05 (readout not
collapsed), pick the one with the largest opt_A y_install; ties -> lower KL; if none feasible, the lowest-KL
trial. Option mass is recorded for EVERY trial and every read (base-reference key floors, CSI AM-53/54). The whole
Pareto front (study.best_trials) and every trial are saved.

PREDECLARED READ (after freeze, once): y_install on trainread_A/C and val_A/C; KL on val_C. Controls on
val_A (rank-matched, same layers/modules): spectrum-matched random LoRA (same singular values as the
learned per-module dW, random orthonormal U,V; N=--n-rand), label-shuffled ARA (good/bad = random
half-half mixes of the C and A fit rows; --n-shuffle seeds), identity (= base). Primary statistic:
dY_A = mean over val domains of [y_A(mod) - y_A(base)]; one-sided rank among ARA+controls (floor
1/(1+n_controls)). Frozen params are then refit at the --extra-ranks (descriptive, MEASURED).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sys
import time

ap = argparse.ArgumentParser()
ap.add_argument("--codeword", required=True)
ap.add_argument("--model", required=True)
ap.add_argument("--workdir", required=True)
ap.add_argument("--out-dir", default="reports/heretic_csi/phaseB")
ap.add_argument("--blob-dir", required=True, help="large artifacts (LoRA factors) outside the repo")
ap.add_argument("--rank", type=int, default=50)
ap.add_argument("--n-trials", type=int, default=16)
ap.add_argument("--n-startup", type=int, default=8)
ap.add_argument("--n-rand", type=int, default=39)
ap.add_argument("--n-shuffle", type=int, default=3)
ap.add_argument("--extra-ranks", default="1,8")
ap.add_argument("--seed", type=int, default=20261013)
ap.add_argument("--kl-feasible", type=float, default=1.0)
ap.add_argument("--cross-codeword", default="", help="MEASURED specificity read: other codeword's val_A/val_C under this edit")
ap.add_argument("--xcheck-run-dirs", default="", help="comma list of frozen score_behavior BASE run dirs for this codeword")
A = ap.parse_args()
sys.argv = [sys.argv[0]]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
DS = os.path.join(REPO, "configs/heretic_csi/phaseB", A.codeword)
MAN = json.load(open(os.path.join(DS, "MANIFEST.json")))
OUT = os.path.join(REPO, A.out_dir)
os.makedirs(OUT, exist_ok=True)
ATT = f"job{os.environ.get('SLURM_JOB_ID', 'none')}_r{os.environ.get('SLURM_RESTART_COUNT', '0')}_{int(time.time())}"
WORK = os.path.join(A.workdir, ATT)
BLOB = os.path.join(A.blob_dir, ATT)
os.makedirs(WORK, exist_ok=True)
os.makedirs(BLOB, exist_ok=True)
import glob as _glob, shutil as _shutil  # noqa: E402
SRC = {}
os.makedirs(os.path.join(WORK, "src_snapshot"), exist_ok=True)
for _f in sorted(_glob.glob(os.path.join(HERE, "*.py")) + _glob.glob(os.path.join(HERE, "slurm", "*.slurm"))):
    _shutil.copy2(_f, os.path.join(WORK, "src_snapshot", os.path.basename(_f)))
    SRC[os.path.relpath(_f, REPO)] = hashlib.sha256(open(_f, "rb").read()).hexdigest()

# KL prompts as a Heretic local dataset (texts of opt_C, and val_C for the final read)
for name in ("opt_C", "val_C"):
    d = os.path.join(WORK, f"kl_{name}")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "train.jsonl"), "w") as fh:
        for l in open(os.path.join(DS, f"{name}.jsonl")):
            fh.write(json.dumps({"text": json.loads(l)["full_prompt"]}) + "\n")

SCORER = os.path.join(HERE, "semantic_installation_scorer.py") + ":SemanticInstallationScore"
toml = f'''
model = "{A.model}"
dtypes = ["bfloat16"]
batch_size = 8
max_batch_size = 8
seed = {A.seed}
system_prompt = ""
n_trials = {A.n_trials}
n_startup_trials = {A.n_startup}
study_checkpoint_dir = "ckpt"
scorers = [
  {{ plugin = "{SCORER}", optimization = "maximize", instance_name = "A" }},
  {{ plugin = "heretic.scorers.kl_divergence.KLDivergence", optimization = "minimize" }},
  {{ plugin = "{SCORER}", optimization = "none", instance_name = "C" }},
]
modifiers = [ {{ plugin = "heretic.modifiers.ara.ARA" }} ]

[scorer.SemanticInstallationScore]
codeword = "{A.codeword}"
[scorer.SemanticInstallationScore_A]
prompts_jsonl = "{os.path.join(DS, 'opt_A.jsonl')}"
[scorer.SemanticInstallationScore_C]
prompts_jsonl = "{os.path.join(DS, 'opt_C.jsonl')}"
[scorer.KLDivergence.prompts]
dataset = "{os.path.join(WORK, 'kl_opt_C')}"
split = "train"
column = "text"

[modifier.ARA]
lora_rank = {A.rank}
[modifier.ARA.good_prompts]
dataset = "{os.path.join(DS, 'fit_good')}"
split = "train"
column = "text"
[modifier.ARA.bad_prompts]
dataset = "{os.path.join(DS, 'fit_bad')}"
split = "train"
column = "text"
'''
os.chdir(WORK)
open("config.toml", "w").write(toml)

import torch  # noqa: E402
import torch.nn.functional as F  # noqa: E402
import transformers  # noqa: E402
import optuna  # noqa: E402
from optuna.samplers import TPESampler  # noqa: E402
from optuna.storages import JournalStorage  # noqa: E402
from optuna.storages.journal import JournalFileBackend, JournalFileOpenLock  # noqa: E402
from optuna.trial import TrialState  # noqa: E402

import heretic.model as hm  # noqa: E402
from heretic.config import Settings, SingleDatasetSpecification  # noqa: E402
from heretic.evaluator import Evaluator  # noqa: E402
from heretic.modifier import load_and_init_modifiers  # noqa: E402
from heretic.modifiers.ara import ARA, Parameters, Settings as ARASettings  # noqa: E402
from heretic.plugin import Context  # noqa: E402
from heretic.scorers.keyword_rate import KeywordRate, Settings as KWSettings  # noqa: E402
from heretic.utils import Prompt  # noqa: E402
from semantic_installation_scorer import readout_rows, domain_mean, floor_summary, READOUT_IMPL  # noqa: E402
import lora_utils  # noqa: E402

_orig_gmc = hm.get_model_class


class _EagerLoader:
    def __init__(self, cls):
        self.cls = cls

    def from_pretrained(self, *a, **k):
        k.setdefault("attn_implementation", "eager")
        return self.cls.from_pretrained(*a, **k)


hm.get_model_class = lambda m: _EagerLoader(_orig_gmc(m))
T0 = time.time()


def log(*x):
    print(f"[{time.time()-T0:7.1f}s]", *x, flush=True)


cap = torch.cuda.get_device_capability(0)
if cap[0] < 8:
    raise SystemExit(f"REFUSE: native bf16 needs cc>=8.0, got {cap}")
R = {"schema": "hcsi_phaseB/2", "codeword": A.codeword, "args": vars(A), "attempt": ATT, "manifest": MAN,
     "source_sha256": SRC, "source_snapshot_dir": os.path.join(WORK, "src_snapshot"),
     "env": {"torch": torch.__version__, "transformers": transformers.__version__, "optuna": optuna.__version__,
             "gpu": torch.cuda.get_device_name(0), "cc": list(cap)},
     "freeze_rule": f"v2: COMPLETE trials with KL<={A.kl_feasible} AND opt_A median option mass>=0.05: max opt_A y_install (tie: lower KL); else min KL"}
OUTJ = os.path.join(OUT, f"PHASEB_native_ara_{A.codeword}_{ATT}.json")


def dump():
    json.dump(R, open(OUTJ, "w"), indent=2)


settings = Settings()
transformers.set_seed(A.seed)
model = hm.Model(settings)
assert getattr(model.model.config, "_attn_implementation", None) == "eager"
log("model loaded (eager, bf16)")


def rows_of(name):
    return [json.loads(l) for l in open(os.path.join(DS, f"{name}.jsonl"))]


LAST_RECS = {}
BASE_KEYS = {}


def read(name, cw=None):
    cw = cw or A.codeword
    rows = ([json.loads(l) for l in open(os.path.join(REPO, "configs/heretic_csi/phaseB", cw, f"{name}.jsonl"))]
            if cw != A.codeword else rows_of(name))
    recs = readout_rows(model, rows, "bomb", cw)
    LAST_RECS[(cw, name)] = recs
    if (cw, name) not in BASE_KEYS:  # first read of a set is the BASE arm (all base reads precede any LoRA)
        BASE_KEYS[(cw, name)] = {r["prompt_id"] for r in recs if r["option_mass"] >= 0.05}
    v, dm = domain_mean(recs)
    fl = floor_summary(recs, 0.05, BASE_KEYS[(cw, name)])
    return {"y_domain_mean": v, "domain_means": dm, "n_rows": len(recs), "n_domains": len(dm), **fl,
            "mean_logp_concept": sum(r["logp_concept"] for r in recs) / len(recs),
            "mean_logp_codeword": sum(r["logp_codeword"] for r in recs) / len(recs)}


kl_val_prompts = [Prompt(system="", user=r["full_prompt"]) for r in rows_of("val_C")]

kw = KeywordRate(heretic_settings=settings, settings=KWSettings(prompts=SingleDatasetSpecification(
    dataset=os.path.join(DS, "val_behav_C"), split="train", column="text")))
kw.init(Context(settings=settings, model=model))


def refusal():
    """SECONDARY: Heretic's own keyword-refusal rate on 46 behavioral cell-C val prompts (100 greedy tokens).
    A keyword heuristic, not content-true success; never optimized."""
    c = Context(settings=settings, model=model)
    resp = c.get_responses(kw.prompts)
    return {"rate": kw.get_score(c).value, "n": len(resp), "responses_head": [r[:160] for r in resp]}


# -------- base reads (pure base model, before any LoRA) --------
base = {n: read(n) for n in ("trainread_A", "trainread_C", "val_A", "val_C")}
base_opt_A = read("opt_A")  # fixes the BASE option-mass key set for the replay read of opt_A
XC = A.cross_codeword
if XC:  # MEASURED (not preregistered): does the edit raise P(bomb) on ANOTHER codeword's prompts too?
    base_x = {n: read(n, XC) for n in ("val_A", "val_C")}
    R["base_cross"] = {"codeword": XC, **base_x}
base_kl_logits = F.log_softmax(model.get_logits_batched(kl_val_prompts).float(), -1).cpu()
R["base"] = base
R["readout_impl"] = READOUT_IMPL
ref = {}
for d in [x for x in A.xcheck_run_dirs.split(",") if x]:
    for l in open(os.path.join(REPO, d, "results.jsonl")):
        r = json.loads(l)
        if r.get("readout") == "semantic":
            ref[r["prompt_id"]] = r
mine = {r["prompt_id"]: r for n in ("trainread_C", "val_C") for r in LAST_RECS[(A.codeword, n)]}
common = sorted(set(ref) & set(mine))
if common:
    dyx = [abs(mine[k]["y_install"] - 1 / (1 + math.exp(-(ref[k]["logp_concept"] - ref[k]["logp_codeword"]))))
           for k in common]
    R["readout_xcheck"] = {"n_common": len(common), "max_abs_dy": max(dyx), "mean_abs_dy": sum(dyx) / len(dyx),
                           "max_abs_dlogp_concept": max(abs(mine[k]["logp_concept"] - ref[k]["logp_concept"]) for k in common)}
else:
    R["readout_xcheck"] = {"n_common": 0}
log("readout xcheck", R["readout_xcheck"])
R["base_refusal"] = refusal()
dump()
log("base reads", {n: round(v["y_domain_mean"], 4) for n, v in base.items()})

# -------- Heretic study (as main.py: Evaluator baselines first, then modifier init) --------
evaluator = Evaluator(settings, model)
entry = load_and_init_modifiers(settings, model)[0]
ara: ARA = entry.modifier


def all_modules():
    for li in range(len(model.get_layers())):
        for comp, mods in model.get_layer_modules(li).items():
            for mi, m in enumerate(mods):
                yield (li, comp, mi), m


# DEVIATION FROM SHIPPED HERETIC (Phase A finding): Heretic's reset zeroes lora_B only, so lora_A carries over
# between trials and every trial's L-BFGS start depends on trial history (not replayable). We restore lora_A to
# its post-apply_lora value at every reset so each trial (and the frozen re-read) starts from the same state.
A_INIT = {k: m.lora_A["default"].weight.detach().clone() for k, m in all_modules()}


def restore_A():
    with torch.no_grad():
        for k, m in all_modules():
            m.lora_A["default"].weight.copy_(A_INIT[k])
names = evaluator.get_objective_names()
directions = evaluator.get_objective_directions()
R["objective_names"] = names
jpath = os.path.join(WORK, "study.journal")
storage = JournalStorage(JournalFileBackend(jpath, lock_obj=JournalFileOpenLock(jpath)))
study = optuna.create_study(sampler=TPESampler(n_startup_trials=A.n_startup, n_ei_candidates=128,
                                               multivariate=True, seed=A.seed),
                            storage=storage, directions=directions, study_name="heretic", load_if_exists=True)


def objective(trial):
    ctx = Context(settings=settings, model=model)
    p = ara.suggest_parameters(ctx, trial)
    trial.set_user_attr("parameters", p.to_dict())
    ara.reset_model(ctx)
    restore_A()
    t = time.time()
    ara.modify_model(ctx, p)
    scores = evaluator.get_scores()
    trial.set_user_attr("scores", evaluator.get_paired_score_records(scores))
    trial.set_user_attr("named", {n: s.value for n, s in scores})
    trial.set_user_attr("option_mass", {e.name: {k: e.scorer.last_detail[k] for k in
                                                 ("median_option_mass", "frac_below_floor", "collapsed", "y_floor",
                                                  "n_rows_floor", "n_domains_floor")}
                                        for e in evaluator._scorer_entries if getattr(e.scorer, "last_detail", None)})
    trial.set_user_attr("seconds", time.time() - t)
    log("trial", trial.number, p.to_dict(), {n: round(s.value, 4) for n, s in scores})
    return evaluator.get_objective_values(scores)


study.optimize(objective, n_trials=A.n_trials - len(study.trials))
done = [t for t in study.trials if t.state == TrialState.COMPLETE]
nm = {n: n for n in done[0].user_attrs["named"]}
kA = next(n for n in nm if "y_install" in n and "- A" in n)
kC = next(n for n in nm if "y_install" in n and "- C" in n)
kKL = next(n for n in nm if "KL" in n)
R["trials"] = [{"number": t.number, "params": t.user_attrs["parameters"], "named": t.user_attrs["named"],
                "option_mass": t.user_attrs.get("option_mass"), "seconds": t.user_attrs["seconds"]} for t in done]
R["baseline_option_mass"] = {e.name: getattr(e.scorer, "baseline_detail", None) for e in evaluator._scorer_entries}


def _collapsed_A(t):
    om = t.user_attrs.get("option_mass", {})
    return any(v["collapsed"] for k, v in om.items() if "- A" in k)

R["pareto_front"] = [t.number for t in study.best_trials]
feas = [t for t in done if t.user_attrs["named"][kKL] <= A.kl_feasible and not _collapsed_A(t)]
chosen = (max(feas, key=lambda t: (t.user_attrs["named"][kA], -t.user_attrs["named"][kKL])) if feas
          else min(done, key=lambda t: t.user_attrs["named"][kKL]))
R["chosen_trial"] = chosen.number
R["chosen_feasible"] = bool(feas)
P = Parameters.from_dict(chosen.user_attrs["parameters"])
dump()
log("chosen", chosen.number, P.to_dict())

ctx = Context(settings=settings, model=model)


def lora_modules():
    for li in range(P.start_layer_index, P.end_layer_index):
        for comp, mods in model.get_layer_modules(li).items():
            for mi, m in enumerate(mods):
                yield (li, comp, mi), m


def factor_svals(m):
    return lora_utils.factor_svals(m.lora_B["default"].weight, m.lora_A["default"].weight, m.scaling["default"])


def kl_val():
    lq = F.log_softmax(model.get_logits_batched(kl_val_prompts).float(), -1).cpu()
    return float(F.kl_div(lq, base_kl_logits, reduction="batchmean", log_target=True))


def dy(cur, ref):
    ds_ = sorted(set(cur["domain_means"]) & set(ref["domain_means"]))
    return sum(cur["domain_means"][d] - ref["domain_means"][d] for d in ds_) / len(ds_)


# -------- frozen-ARA reads --------
ara.reset_model(ctx)
restore_A()
ara.modify_model(ctx, P)
_rep = read("opt_A")
R["replay_chosen_trial"] = {"trial_value_opt_A": chosen.user_attrs["named"][kA], "replayed_opt_A": _rep["y_domain_mean"],
                            "abs_diff": abs(chosen.user_attrs["named"][kA] - _rep["y_domain_mean"])}
log("replay chosen", R["replay_chosen_trial"])
spec = {}
svals = {}
factors = {}
for k, m in lora_modules():
    S = factor_svals(m)
    svals[k] = S
    spec["|".join(map(str, k))] = {"fro": float(S.norm()), "top": [float(x) for x in S],
                                   "rel_fro_W": float(S.norm() / m.base_layer.weight.float().norm())}
    factors["|".join(map(str, k))] = (m.lora_A["default"].weight.detach().cpu().clone(),
                                     m.lora_B["default"].weight.detach().cpu().clone())
fpath = os.path.join(BLOB, f"ara_factors_{A.codeword}_r{A.rank}.pt")
torch.save({"params": P.to_dict(), "factors": factors}, fpath)
ara_read = {n: read(n) for n in ("trainread_A", "trainread_C", "val_A", "val_C")}
R["ara"] = {"reads": ara_read, "kl_val_C": kl_val(), "refusal": refusal(), "spectra": spec, "factors_path": fpath,
            "factors_sha256": hashlib.sha256(open(fpath, "rb").read()).hexdigest(),
            "dY": {n: dy(ara_read[n], base[n]) for n in ara_read}}
if XC:
    ax = {n: read(n, XC) for n in ("val_A", "val_C")}
    R["ara"]["cross"] = {"codeword": XC, "reads": ax, "dY": {n: dy(ax[n], base_x[n]) for n in ax}}
    log("cross-codeword dY", XC, R["ara"]["cross"]["dY"])
dump()
log("ARA reads dY", {n: round(v, 4) for n, v in R["ara"]["dY"].items()}, "KL", R["ara"]["kl_val_C"])

# -------- controls on val_A --------
ctrl = []
gen = torch.Generator().manual_seed(A.seed)
for i in range(A.n_rand):  # spectrum-matched random operator, same modules
    with torch.no_grad():
        for k, m in lora_modules():
            Bw, Aw = m.lora_B["default"].weight, m.lora_A["default"].weight
            Bn, An = lora_utils.spectrum_matched_factors(svals[k], Bw.shape[0], Aw.shape[1],
                                                         float(m.scaling["default"]), gen)
            Bw.copy_(Bn.to(Bw.device, Bw.dtype))
            Aw.copy_(An.to(Aw.device, Aw.dtype))
    rd = read("val_A")
    ctrl.append({"kind": "random_spectrum_matched", "i": i, "dY_val_A": dy(rd, base["val_A"]),
                 "median_option_mass": rd["median_option_mass"], "frac_below_floor": rd["frac_below_floor"],
                 "y_floor": rd["y_floor"]})
    log("ctrl rand", i, round(ctrl[-1]["dY_val_A"], 4))
ara.reset_model(ctx)

fit_good, fit_bad = rows_of("fit_good"), rows_of("fit_bad")
for j in range(A.n_shuffle):  # label-shuffled ARA: same params, good/bad = random C/A mixtures
    rng = random.Random(A.seed + 1000 + j)
    pool = [r["full_prompt"] for r in fit_good + fit_bad]
    rng.shuffle(pool)
    dirs = []
    for half, nm_ in ((pool[:len(fit_good)], "g"), (pool[len(fit_good):], "b")):
        d = os.path.join(WORK, f"shuf{j}_{nm_}")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "train.jsonl"), "w") as fh:
            for t in half:
                fh.write(json.dumps({"text": t}) + "\n")
        dirs.append(d)
    model.model = model.model.unload()  # drop LoRA wrappers (no merge), recapture I/O on the base model
    sh = ARA(heretic_settings=settings, settings=ARASettings(
        good_prompts=SingleDatasetSpecification(dataset=dirs[0], split="train", column="text"),
        bad_prompts=SingleDatasetSpecification(dataset=dirs[1], split="train", column="text"),
        lora_rank=A.rank))
    sh.init(ctx)
    sh.modify_model(ctx, P)
    rd = read("val_A")
    ctrl.append({"kind": "label_shuffled_ara", "i": j, "dY_val_A": dy(rd, base["val_A"]),
                 "median_option_mass": rd["median_option_mass"], "frac_below_floor": rd["frac_below_floor"],
                 "y_floor": rd["y_floor"]})
    log("ctrl shuf", j, round(ctrl[-1]["dY_val_A"], 4))
    sh.reset_model(ctx)
    ara = sh  # current LoRA owner

obs = R["ara"]["dY"]["val_A"]
n_ge = sum(1 for c in ctrl if c["dY_val_A"] >= obs)
R["controls"] = ctrl
R["primary"] = {"statistic": "dY_val_A (domain-mean y_install shift, val domains)", "observed": obs,
                "n_controls": len(ctrl), "rank_from_top": 1 + n_ge, "p_one_sided": (1 + n_ge) / (1 + len(ctrl)),
                "floor": 1 / (1 + len(ctrl)),
                "installation_fraction": obs / (base["val_C"]["y_domain_mean"] - base["val_A"]["y_domain_mean"])}
dump()
log("primary", R["primary"])

# -------- frozen params refit at other ranks (descriptive) --------
R["extra_ranks"] = {}
for r in [int(x) for x in A.extra_ranks.split(",") if x.strip()]:
    model.model = model.model.unload()
    ar = ARA(heretic_settings=settings, settings=ARASettings(
        good_prompts=SingleDatasetSpecification(dataset=os.path.join(DS, "fit_good"), split="train", column="text"),
        bad_prompts=SingleDatasetSpecification(dataset=os.path.join(DS, "fit_bad"), split="train", column="text"),
        lora_rank=r))
    ar.init(ctx)
    ar.modify_model(ctx, P)
    rr = {n: read(n) for n in ("val_A", "val_C")}
    R["extra_ranks"][r] = {"dY": {n: dy(rr[n], base[n]) for n in rr}, "kl_val_C": kl_val(),
                           "median_option_mass": {n: rr[n]["median_option_mass"] for n in rr}}
    log("rank", r, R["extra_ranks"][r])
    ar.reset_model(ctx)
    dump()

R["wall_seconds"] = time.time() - T0
dump()
log("wrote", OUTJ)
print("PHASEB_DONE", OUTJ, flush=True)
