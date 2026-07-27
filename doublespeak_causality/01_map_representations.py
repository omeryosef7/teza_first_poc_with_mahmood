"""
01_map_representations.py — Stage 1 (plan §8): map how the codeword representation
moves from Neutral toward Direct across layers, under matched conditions.

For each seed item and each condition (Direct / Neutral / Doublespeak) it captures
per-layer residual vectors at the codeword position AND the following token (plan
§8.1 — the decoded concept may transfer downstream). It then:
  * builds a per-layer harmful direction d_harm = mean(Direct) - mean(Neutral)
    with LEAVE-ONE-ITEM-OUT cross-validation (plan §8.2 — never train & test the
    direction on the same example);
  * measures the Doublespeak trajectory: projection onto d_harm, cosine to the
    Direct/Neutral centroids, a normalized Direct-vs-Neutral score, and the
    reference Patchscopes P(bomb) vs P(carrot) crossover (reuse doublespeak/);
  * adds nearest-neighbor (logit-lens) decoding as an AUXILIARY diagnostic only
    (plan §8.1 — not standalone evidence);
  * summarizes semantic onset layer, early/late alignment, AUC, early->late change.

Deterministic. Writes JSON + a registry row. Prints numbers only, never harmful
generations (plan §5.12).

Run (after Llama-8B is available), on an L40S via SLURM or interactively:
  python 01_map_representations.py --model meta-llama/Llama-3.1-8B-Instruct \
      --data data/seed_concepts.json --templated
"""
import os
import sys
import json
import time
import argparse

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ds_common as dc
from mech_interp import LogitLens, Patchscopes  # vendored official code (reuse)

CONDITIONS = ("direct", "neutral", "doublespeak")


def build_items(data_path):
    d = json.load(open(data_path))
    items = []
    for it in d["items"]:
        demos = "\n".join(it["demos"]) if isinstance(it["demos"], list) else it["demos"]
        cond = dc.build_conditions(it["harmful_instruction"], it["harmful_word"],
                                   it["codeword"], demos)
        items.append({"id": it["id"], "category": it["category"],
                      "harmful_word": it["harmful_word"], "codeword": it["codeword"],
                      "cond": cond})
    return items


def condition_text(lm, cond_obj, name, templated):
    raw = getattr(cond_obj, name)
    return dc.apply_template(lm.tokenizer, raw) if templated else raw


def collect_reps(lm, items, templated):
    """reps[item_id][condition] = {'codeword_last': [L+1,H], 'following': [L+1,H]?}"""
    out = {}
    for it in items:
        out[it["id"]] = {}
        for c in CONDITIONS:
            text = condition_text(lm, it["cond"], c, templated)
            # For Direct, the analyzed word is the harmful_word; else the codeword.
            word = it["harmful_word"] if c == "direct" else it["codeword"]
            cap = dc.capture_target_reps(lm, text, word)
            out[it["id"]][c] = cap["reps"]
    return out


def leave_one_out_directions(reps, items, pos="codeword_last"):
    """Per held-out item, d_harm^(l) = mean_{train}(Direct) - mean_{train}(Neutral).
    Returns dir_by_heldout[item_id] -> tensor [L+1, H]."""
    ids = [it["id"] for it in items]
    dir_by_heldout = {}
    for held in ids:
        train = [i for i in ids if i != held]
        direct = torch.stack([reps[i]["direct"][pos] for i in train], 0).mean(0)
        neutral = torch.stack([reps[i]["neutral"][pos] for i in train], 0).mean(0)
        dir_by_heldout[held] = direct - neutral  # [L+1, H]
    return dir_by_heldout


def centroids(reps, items, cond, pos="codeword_last"):
    return torch.stack([reps[it["id"]][cond][pos] for it in items], 0).mean(0)  # [L+1,H]


def trajectory(reps, items, dir_by_heldout, pos="codeword_last"):
    """Per item, per layer: DS alignment metrics using the HELD-OUT direction."""
    ids = [it["id"] for it in items]
    L = reps[ids[0]]["neutral"][pos].shape[0]
    result = {}
    for it in items:
        i = it["id"]
        d = dir_by_heldout[i]                      # [L+1,H]
        ds = reps[i]["doublespeak"][pos]           # [L+1,H]
        neu = reps[i]["neutral"][pos]
        dire = reps[i]["direct"][pos]
        proj, cos_dir, cos_neu, norm_score = [], [], [], []
        # F6 (iter15): iterate over BLOCK OUTPUTS only, indexing reps[l+1] so trajectory index l is
        # the 0-indexed transformer layer (matching 05/07 where layer L ↔ reps[L+1]). Previously
        # range(L) used reps[0]=embedding as "layer 0", shifting every onset/argmax label by one.
        for l in range(L - 1):
            k = l + 1                              # reps index = output of block l (skips embedding)
            dl = d[k]
            dn = dl / (dl.norm() + 1e-8)
            # projection of (DS - Neutral) onto harmful direction (centered)
            proj.append(float(torch.dot((ds[k] - neu[k]).float(), dn.float())))
            cos_dir.append(dc.cosine(ds[k], dire[k]))
            cos_neu.append(dc.cosine(ds[k], neu[k]))
            # normalized position between neutral(0) and direct(1) along d
            denom = float(torch.dot((dire[k] - neu[k]).float(), dn.float()))
            num = float(torch.dot((ds[k] - neu[k]).float(), dn.float()))
            # F5 (iter15): when the Direct-vs-Neutral basis is ~degenerate (|denom| tiny) the ratio
            # is undefined — clamp to avoid an exploding/garbage alignment value.
            norm_score.append(0.0 if abs(denom) < 1e-4
                              else max(-5.0, min(5.0, num / denom)))
        result[i] = {"proj_on_dharm": proj, "cos_to_direct": cos_dir,
                     "cos_to_neutral": cos_neu, "norm_direct_vs_neutral": norm_score}
    return result


def summarize(norm_score, onset_thresh=0.5, early_frac=0.35, late_frac=0.65):
    L = len(norm_score)
    early_hi = int(L * early_frac)
    late_lo = int(L * late_frac)
    onset = next((l for l, s in enumerate(norm_score) if s >= onset_thresh), None)
    early = sum(norm_score[:early_hi]) / max(1, early_hi)
    late = sum(norm_score[late_lo:]) / max(1, L - late_lo)
    auc = sum(norm_score) / L
    return {"semantic_onset_layer": onset, "early_alignment": early,
            "late_alignment": late, "auc_alignment": auc,
            "early_to_late_change": late - early,
            "max_alignment": max(norm_score),
            "argmax_layer": int(max(range(L), key=lambda l: norm_score[l]))}


def patchscopes_trajectory(lm, items, templated):
    """Reuse the official Patchscopes to get P(codeword) vs P(harmful) per layer
    for the Doublespeak prompt — the paper's headline observational metric."""
    ps = Patchscopes(lm.model, lm.tokenizer)
    out = {}
    for it in items:
        text = condition_text(lm, it["cond"], "doublespeak", templated)
        try:
            res = ps.analyze_patchscope_probabilities(
                source_prompt=text, benign_token=it["codeword"],
                malicious_token=it["harmful_word"], layer_interval=1)
            out[it["id"]] = {"layers": res["layers"],
                             "p_codeword": res["benign_probs"],
                             "p_harmful": res["malicious_probs"]}
        except Exception as e:
            out[it["id"]] = {"error": str(e)[:200]}
    return out


def nn_decode_aux(lm, items, templated, topk=5):
    """AUXILIARY ONLY (plan §8.1): logit-lens argmax around the codeword for the
    Doublespeak prompt. Not evidence of meaning; a corroborating signal."""
    lens = LogitLens(lm.model, lm.tokenizer)
    out = {}
    for it in items:
        text = condition_text(lm, it["cond"], "doublespeak", templated)
        try:
            r = lens.analyze_token_predictions(text, it["codeword"], layer_interval=4)
            # keep only decoded strings per layer (compact)
            out[it["id"]] = {str(l): [p["text"] for p in preds]
                             for l, preds in r["predictions"].items()}
        except Exception as e:
            out[it["id"]] = {"error": str(e)[:200]}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--data", default=os.path.join(os.path.dirname(__file__),
                                                   "data", "seed_concepts.json"))
    ap.add_argument("--templated", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--dtype", default="bfloat16", choices=["bfloat16","float16"])
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_dir = args.out_dir or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "outputs",
        f"stage1_repmap_{args.model.split('/')[-1]}_{ts}")
    os.makedirs(out_dir, exist_ok=True)

    lm = dc.load_model(args.model, dtype=getattr(__import__('torch'), args.dtype))
    items = build_items(args.data)

    reps = collect_reps(lm, items, args.templated)
    report = {"model": args.model, "meta": lm.meta(), "templated": args.templated,
              "n_items": len(items), "positions": {}}

    for pos in ("codeword_last", "following"):
        # 'following' may be missing for some prompts; require all items to have it
        if not all("following" in reps[it["id"]][c] for it in items for c in CONDITIONS):
            if pos == "following":
                report["positions"][pos] = {"skipped": "not present for all items/conditions"}
                continue
        dirs = leave_one_out_directions(reps, items, pos)
        traj = trajectory(reps, items, dirs, pos)
        summ = {i: summarize(traj[i]["norm_direct_vs_neutral"]) for i in traj}
        report["positions"][pos] = {"trajectory": traj, "summary": summ,
                                    "direction_norms": {
                                        i: [float(dirs[i][l].norm()) for l in range(dirs[i].shape[0])]
                                        for i in dirs}}

    report["patchscopes"] = patchscopes_trajectory(lm, items, args.templated)
    report["nn_decode_aux"] = nn_decode_aux(lm, items, args.templated)
    report["status"] = "COMPLETE"

    with open(os.path.join(out_dir, "stage1_results.json"), "w") as f:
        json.dump(report, f, indent=2)

    # Console summary — numbers only.
    print(f"[stage1] model={args.model} items={len(items)} -> {out_dir}")
    for i, s in report["positions"].get("codeword_last", {}).get("summary", {}).items():
        print(f"  {i}: onset={s['semantic_onset_layer']} "
              f"early={s['early_alignment']:.2f} late={s['late_alignment']:.2f} "
              f"dE->L={s['early_to_late_change']:+.2f} auc={s['auc_alignment']:.2f}")


if __name__ == "__main__":
    main()
