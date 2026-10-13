#!/usr/bin/env python3
"""Replay saved Phase-B ARA LoRA factors (no re-optimization) and read y_install on any codeword's frozen sets.

Two uses: (1) replay check — the saved operator must reproduce the Phase-B dY on its own codeword (mandate §21
"replay saved parameters -> identical or tolerance-matched"); (2) MEASURED cross-codeword specificity — does an
edit fit on codeword X raise P(bomb) on codeword Y's prompts (a context-independent answer bias)?
"""
import argparse
import json
import os
import sys
import time

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--factors", required=True, help="ara_factors_<cw>_r<rank>.pt from phaseB_native_ara.py")
ap.add_argument("--rank", type=int, required=True)
ap.add_argument("--reads", required=True, help="comma list cw:set, e.g. basket:val_A,button:val_A,button:val_C")
ap.add_argument("--out", required=True)
a = ap.parse_args()
sys.argv = [sys.argv[0]]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.abspath(a.out)
os.makedirs(os.path.dirname(OUT), exist_ok=True)

import torch  # noqa: E402
import heretic.model as hm  # noqa: E402
from heretic.config import Settings  # noqa: E402
from semantic_installation_scorer import readout_rows, domain_mean, READOUT_IMPL  # noqa: E402

_orig = hm.get_model_class


class _Eager:
    def __init__(self, c):
        self.c = c

    def from_pretrained(self, *x, **k):
        k.setdefault("attn_implementation", "eager")
        return self.c.from_pretrained(*x, **k)


hm.get_model_class = lambda m: _Eager(_orig(m))
T0 = time.time()
settings = Settings(model=a.model, dtypes=["bfloat16"], batch_size=8, max_batch_size=8, system_prompt="")
model = hm.Model(settings)
assert getattr(model.model.config, "_attn_implementation", None) == "eager"
reads = [tuple(x.split(":")) for x in a.reads.split(",") if x]


def do_reads():
    out = {}
    for cw, name in reads:
        rows = [json.loads(l) for l in open(os.path.join(REPO, "configs/heretic_csi/phaseB", cw, f"{name}.jsonl"))]
        recs = readout_rows(model, rows, "bomb", cw)
        v, dm = domain_mean(recs)
        out[f"{cw}:{name}"] = {"y_domain_mean": v, "domain_means": dm, "n_rows": len(recs), "n_domains": len(dm)}
    return out


base = do_reads()
blob = torch.load(a.factors)
model.apply_lora(a.rank)
n_set = 0
with torch.no_grad():
    for li in range(len(model.get_layers())):
        for comp, mods in model.get_layer_modules(li).items():
            for mi, m in enumerate(mods):
                key = f"{li}|{comp}|{mi}"
                if key in blob["factors"]:
                    Aw, Bw = blob["factors"][key]
                    m.lora_A["default"].weight.copy_(Aw.to(m.lora_A["default"].weight.device))
                    m.lora_B["default"].weight.copy_(Bw.to(m.lora_B["default"].weight.device))
                    n_set += 1
assert n_set == len(blob["factors"]), (n_set, len(blob["factors"]))
mod = do_reads()


def dy(c, b):
    ds = sorted(set(c["domain_means"]) & set(b["domain_means"]))
    return sum(c["domain_means"][d] - b["domain_means"][d] for d in ds) / len(ds)


R = {"schema": "hcsi_phaseB_replay/1", "factors": a.factors, "params": blob["params"], "rank": a.rank,
     "n_modules_set": n_set, "readout_impl": READOUT_IMPL, "gpu": torch.cuda.get_device_name(0),
     "job": os.environ.get("SLURM_JOB_ID"), "base": base, "replayed": mod,
     "dY": {k: dy(mod[k], base[k]) for k in base}, "wall_seconds": time.time() - T0}
json.dump(R, open(OUT, "w"), indent=2)
print("dY", json.dumps(R["dY"]), flush=True)
print("REPLAY_DONE", OUT, flush=True)
