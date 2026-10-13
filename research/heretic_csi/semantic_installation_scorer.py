"""Heretic external Scorer plugin: the frozen CSI semantic-installation endpoint `y_install`.

Load in Heretic as `research/heretic_csi/semantic_installation_scorer.py:SemanticInstallationScore`.

DEFINITION (frozen; ported from src/boombness/score_behavior.py `--readout-ids whole_answer` (the CSI
default used by every P2a run) = signals.string_option_readout + signals.answer_variants; and
scripts/dcs_cont_layerpos_map.py::load_installation for y_install. NOT reinterpreted):
  templated = chat_template([{"role":"user","content": full_prompt}], add_generation_prompt=True)
              (no system message; on Llama-3.1 an EMPTY system message renders byte-identically)
  context   = templated + "Answer:"           (tokenized with add_special_tokens=False)
  variants  = {concept: [" bomb", " Bomb"], codeword: [" basket", " Basket"]}  (ANSWER_CASES, spaced)
  logp(v)   = sum_j log P(v_j | context, v_<j)   (teacher-forced whole answer; batch of 1, no padding)
  logp_opt  = logsumexp over that option's variants
  y_install = sigmoid(logp_concept - logp_codeword)          (two-way softmax)
  option_mass = exp(logsumexp over all 4 variant logps)       (readout-validity, CSI floor 0.05)

Score contract (fixed for every experiment; never changes meaning):
  direction : declared by the TOML `optimization` field of the run (maximize when installing).
  population: the rows of `prompts_jsonl` (one frozen file per use, sha256 recorded).
  unit      : DOMAIN — value = mean over domains of the domain-mean y_install.
  baseline  : the unmodified model on the same rows (`get_baseline_score`).
  denominator: n_domains (and n_rows) reported in `last_detail`.
OPTION-MASS FLOOR (readout validity; CSI AM-53/54 rule — the key set comes from ONE reference arm, the BASE
model, never per arm): `value` stays the frozen all-rows protocol; `last_detail` additionally reports
  y_floor        : the same statistic restricted to rows whose BASE option_mass >= floor (keys fixed at baseline),
  frac_below_floor / median_option_mass of the CURRENT arm (collapse detector: an edit that wins y_install by
  destroying the answer distribution shows up here), and n_rows / n_domains for both denominators.
`collapsed` = median option mass of the current arm < floor.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict

import torch
from pydantic import BaseModel, Field

from heretic.plugin import Context
from heretic.scorer import Score, Scorer

ANSWER_PREFIX = "Answer:"
READOUT_IMPL = "whole_answer_bs1_logits_to_keep/v2"


class Settings(BaseModel):
    prompts_jsonl: str = Field(description="jsonl rows with full_prompt, domain, family_slot, prompt_id, codeword, concept")
    concept: str = Field(default="bomb")
    codeword: str = Field(description="basket | button | ...")
    option_mass_floor: float = Field(default=0.05)


def answer_variants(word: str):
    stem = " " + word
    return [stem, stem[:1] + stem[1:2].upper() + stem[2:]]


@torch.no_grad()
def readout_rows(model, rows, concept: str, codeword: str):
    """model = heretic.model.Model. One forward per (row, variant), batch 1 (frozen CSI setting)."""
    tok, hf = model.tokenizer, model.model
    opts = {"concept": answer_variants(concept), "codeword": answer_variants(codeword)}
    vids = {k: [tok(v, add_special_tokens=False)["input_ids"] for v in vs] for k, vs in opts.items()}
    out = []
    for r in rows:
        templated = tok.apply_chat_template([{"role": "user", "content": r["full_prompt"]}],
                                            tokenize=False, add_generation_prompt=True)
        ctx_ids = tok(templated + ANSWER_PREFIX, add_special_tokens=False)["input_ids"]
        lps = {}
        for k, vlist in vids.items():
            vals = []
            for vid in vlist:
                t = torch.tensor([ctx_ids + vid], device=hf.device)
                # keep only the len(vid)+1 last positions: row j predicts variant token j (row j <-> abs
                # position len(ctx)-1+j); the final row is unused. Same logits, far less memory.
                lg = hf(input_ids=t, use_cache=False, logits_to_keep=len(vid) + 1).logits[0]
                lp = torch.log_softmax(lg.float(), -1).cpu()
                vals.append(sum(float(lp[j, tid]) for j, tid in enumerate(vid)))
            lps[k] = vals
        lc = float(torch.tensor(lps["concept"]).logsumexp(0))
        lk = float(torch.tensor(lps["codeword"]).logsumexp(0))
        om = math.exp(float(torch.tensor(lps["concept"] + lps["codeword"]).logsumexp(0)))
        out.append({"prompt_id": r["prompt_id"], "domain": r["domain"], "family_slot": r.get("family_slot"),
                    "cell": r.get("cell"), "logp_concept": lc, "logp_codeword": lk,
                    "y_install": 1.0 / (1.0 + math.exp(-(lc - lk))), "option_mass": om})
    return out


def floor_summary(recs, floor, ref_keys=None):
    """Option-mass validity summary. ref_keys: prompt_ids admitted by the BASE arm (None -> all rows)."""
    om = sorted(r["option_mass"] for r in recs)
    kept = [r for r in recs if ref_keys is None or r["prompt_id"] in ref_keys]
    out = {"median_option_mass": om[len(om) // 2], "frac_below_floor": sum(o < floor for o in om) / len(om),
           "collapsed": om[len(om) // 2] < floor, "floor": floor,
           "n_rows_floor": len(kept), "n_domains_floor": len({r["domain"] for r in kept})}
    out["y_floor"] = domain_mean(kept)[0] if kept else None
    return out


def domain_mean(recs, key="y_install"):
    by = defaultdict(list)
    for r in recs:
        by[r["domain"]].append(r[key])
    dm = {d: sum(v) / len(v) for d, v in by.items()}
    return sum(dm.values()) / len(dm), dm


class SemanticInstallationScore(Scorer):
    settings: Settings

    @property
    def reproducible(self) -> bool:
        return True

    @property
    def score_name(self) -> str:
        return f"y_install[{self.settings.codeword}]"

    def init(self, ctx: Context) -> None:
        raw = open(self.settings.prompts_jsonl, "rb").read()
        self.prompts_sha256 = hashlib.sha256(raw).hexdigest()
        self.rows = [json.loads(l) for l in raw.decode().splitlines() if l.strip()]
        self.last_detail = None
        self.ref_keys = None  # set by get_baseline_score (BASE arm)

    def _score(self, ctx: Context) -> Score:
        recs = readout_rows(ctx.get_model(), self.rows, self.settings.concept, self.settings.codeword)
        v, dm = domain_mean(recs)
        fl = floor_summary(recs, self.settings.option_mass_floor, self.ref_keys)
        self.last_detail = {"rows": recs, "n_rows": len(recs), "n_domains": len(dm), "value": v,
                            "prompts_sha256": self.prompts_sha256, **fl}
        flag = " [red]COLLAPSED[/]" if fl["collapsed"] else ""
        return Score(value=v, rich_display=f"[bold]{v:.4f}[/] (n_dom={len(dm)}, med_om={fl['median_option_mass']:.3g}){flag}",
                     md_display=f"{v:.4f}")

    def get_baseline_score(self, ctx: Context) -> Score:
        sc = self._score(ctx)
        self.ref_keys = {r["prompt_id"] for r in self.last_detail["rows"]
                         if r["option_mass"] >= self.settings.option_mass_floor}
        self.last_detail.update(floor_summary(self.last_detail["rows"], self.settings.option_mass_floor, self.ref_keys))
        self.baseline_detail = {k: v for k, v in self.last_detail.items() if k != "rows"}
        return sc

    def get_score(self, ctx: Context) -> Score:
        return self._score(ctx)
