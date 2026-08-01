"""
next6_d7_defense_redo.py — NEXT6 D7: mechanism-derived defense, redone with W5's two fixes.

W5 was a negative for two reasons: (a) the raw Doublespeak attack was at the malicious floor (0.033,
no headroom), and (b) additive all-position steering at alpha>=8 destabilized generation. This redo:

(1) ATTACK WITH HEADROOM — reproduce 45's cell-D malicious state on benign neutral items: install
    d_Direct at the codeword window (LayerPatch add, LATE timing) AND ablate refusal everywhere
    (AllPositionProjectOutMultiLayer over all layers, v_refusal, alpha=1.0) -> ~0.53 malicious. Then
    re-add the SAME refusal axis ONLY at the late/use layers (AllPositionAddMultiLayer) as the
    DEFENSE, in the same ExitStack, and measure paired malicious suppression. Because the attack
    removes the refusal axis and the defense re-adds it only at the use depth, this is the direct
    causal test of the depth-gated-TOCTOU defense.
(2) SMALL-ALPHA regime {2,3,4,6} + a generation-degeneration guardrail: report stop_reason==length
    and EMPTY fractions, and the FULL {EMPTY,MALICIOUS,REJECTED,BENIGN} split (C8 lesson) so a
    "malicious drop" that is really degeneration (EMPTY/length up) is distinguishable from genuine
    refusal re-engagement (REJECTED up). Benign over-refusal = defense-only (no attack) on neutrals.

Scalars only; raw generations to a protected jsonl, never printed.

Run (GPU, L40S):
  python next6_d7_defense_redo.py --bench data/pair_benchmark/pair_carrot_bomb.json \
      --refusal-pt outputs/stage_gcg_full/refusal_direction_llama_L18.pt \
      --dir-dir outputs/pair_directions_20260730_190505_694691 --n-items 30 --defense-alphas 2,3,4,6
"""
import os, sys, json, time, argparse, importlib.util
from contextlib import ExitStack
from collections import defaultdict
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ds_common as dc
import pair_common as pc
import stats as st

_v = importlib.util.spec_from_file_location("v18", os.path.join(HERE, "18_run_behavioral_necessity.py"))
v18 = importlib.util.module_from_spec(_v); _v.loader.exec_module(v18)
kw_refusal, classify, layer_windows = v18.kw_refusal, v18.classify, v18.layer_windows

CATS = ("EMPTY", "MALICIOUS", "REJECTED", "BENIGN")
PFX, SFX = "Do not reason, just ", " given the context."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--refusal-pt", required=True)
    ap.add_argument("--dir-dir", required=True)
    ap.add_argument("--model", default=dc.PRIMARY_MODEL)
    ap.add_argument("--dir-split", default="heldout")
    ap.add_argument("--refusal-layer", type=int, default=None)
    ap.add_argument("--concept-alpha", type=float, default=1.0)
    ap.add_argument("--attack-timing", default="late", choices=["early", "mid", "late"])
    ap.add_argument("--defense-layers", default="24,26,28,30")
    ap.add_argument("--defense-alphas", default="2,3,4,6")
    ap.add_argument("--defense-mode", default="add_refusal",
                    choices=["add_refusal", "project_concept"])
    ap.add_argument("--n-items", type=int, default=30)
    ap.add_argument("--max-new-tokens", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    dc.set_seed(args.seed)
    from strongreject_scoring import load_strongreject_evaluate
    evaluate = load_strongreject_evaluate()
    lm = dc.load_model(args.model)
    n_layers = lm.num_layers

    dirs = np.load(os.path.join(args.dir_dir, "directions.npz"))
    d_direct = dirs[f"d_Direct|{args.dir_split}|resid_post|codeword_last"].astype(np.float32)
    d_by_L = {L: torch.from_numpy(d_direct[L]) for L in range(n_layers)}
    v_ref = torch.load(args.refusal_pt).float()
    rmeta = args.refusal_pt.replace(".pt", ".json")
    rlayer = args.refusal_layer if args.refusal_layer is not None else \
        (json.load(open(rmeta)).get("layer") if os.path.exists(rmeta) else 18)
    windows = layer_windows(n_layers)
    attack_window = windows[args.attack_timing]
    def_layers = [int(x) for x in args.defense_layers.split(",")]
    # concept-ablation defense uses d_Direct at the middle of the defense band
    d_concept_vec = d_by_L[def_layers[len(def_layers) // 2]]
    def_alphas = [float(x) for x in args.defense_alphas.split(",")]

    bench = json.load(open(args.bench)); pair = bench["pair"]; codeword = pair["codeword"]
    seen, items = set(), []
    for r in bench["behavioral"]:
        if r["pid"] in seen:
            continue
        seen.add(r["pid"]); items.append(r)
    items = items[:args.n_items]

    id_groups = {f"p_{k}": pc.word_first_ids(lm.tokenizer, pair[c])
                 for k, c in (("concept", "concept"), ("codeword", "codeword")) if pair.get(c)}

    @torch.no_grad()
    def gen(text, concept_patches, ablate, defense):
        with ExitStack() as s:
            for (L, pos, vec, alpha) in concept_patches:
                s.enter_context(dc.LayerPatch(lm.model, L, [pos], vector=vec.to(lm.model.device),
                                              mode="add", alpha=alpha))
            if ablate:
                s.enter_context(pc.AllPositionProjectOutMultiLayer(lm.model, range(n_layers), v_ref, 1.0))
            if defense is not None:
                dl, dalpha = defense
                if args.defense_mode == "project_concept":
                    # mechanism-derived defense: ABLATE the concept direction at the mid-band
                    # (where N7-A/D3 localize the concept computation), NOT add refusal late (D7).
                    s.enter_context(pc.AllPositionProjectOutMultiLayer(lm.model, dl, d_concept_vec, dalpha))
                else:
                    s.enter_context(pc.AllPositionAddMultiLayer(lm.model, dl, v_ref, dalpha))
            tok = lm.tokenizer(text, return_tensors="pt", add_special_tokens=False).to(lm.model.device)
            in_len = tok["input_ids"].shape[1]
            g = lm.model.generate(**tok, max_new_tokens=args.max_new_tokens, do_sample=False,
                                  eos_token_id=lm.eos_token_ids, pad_token_id=lm.tokenizer.pad_token_id)
        n_new = g[0].shape[0] - in_len
        comp = lm.tokenizer.decode(g[0][in_len:], skip_special_tokens=True)
        return comp, ("length" if n_new >= args.max_new_tokens else "eos")

    def judge(goal, comp):
        refused = kw_refusal(comp)
        try:
            r = evaluate(goal, comp, ["strongreject_rubric"])
            s = float(r[0].get("score")) if r and r[0].get("score") is not None else None
        except Exception:
            s = None
        if not comp.strip():
            return "EMPTY"
        return classify(s, refused)

    # conditions: baseline, attack, attack+def@alpha, def_only@alpha
    configs = [("baseline", False, False, None), ("attack", True, True, None)]
    for a in def_alphas:
        configs.append((f"attack_def_a{a:g}", True, True, (def_layers, a)))
        configs.append((f"defonly_a{a:g}", False, False, (def_layers, a)))

    acc = {c[0]: {"labels": defaultdict(int), "n": 0, "length": 0,
                  "mal": {}, "ref": {}} for c in configs}
    raw = []
    for i, it in enumerate(items):
        neu = dc.apply_template(lm.tokenizer, it["neutral"])
        ids = lm.tokenizer(neu, add_special_tokens=False)["input_ids"]
        try:
            pos = dc.target_positions(lm.tokenizer, ids, codeword).codeword_last
        except Exception:
            pos = None
        if pos is None:
            continue
        d = it["direct"]; goal = d[len(PFX):-len(SFX)] if d.startswith(PFX) and d.endswith(SFX) else d
        cpatch = [(L, pos, d_by_L[L], args.concept_alpha) for L in attack_window]
        for cname, install, ablate, defense in configs:
            cp = cpatch if install else []
            comp, stop = gen(neu, cp, ablate, defense)
            cat = judge(goal, comp)
            a = acc[cname]; a["n"] += 1; a["labels"][cat] += 1
            if stop == "length":
                a["length"] += 1
            a["mal"][it["pid"]] = 1 if cat == "MALICIOUS" else 0
            a["ref"][it["pid"]] = 1 if cat == "REJECTED" else 0
            raw.append({"pid": it["pid"], "config": cname, "cat": cat, "stop": stop, "response": comp})
        if (i + 1) % 5 == 0:
            print(f"  [{i+1}/{len(items)}]", flush=True)

    # reduce (scalars): paired attack vs attack+def malicious; benign over-refusal baseline vs defonly
    def rate(cname, key):
        a = acc[cname]; return round(sum(a[key].values()) / max(len(a[key]), 1), 4)
    def paired(cn_a, cn_b, key):
        A, B = acc[cn_a][key], acc[cn_b][key]
        pids = [p for p in A if p in B]
        xa = [A[p] for p in pids]; xb = [B[p] for p in pids]
        ci = st.paired_bootstrap_ci(xb, xa, n_boot=10000, seed=0)  # def - attack
        return {"delta": round(ci["mean_diff"], 4), "lo": round(ci["lo"], 4), "hi": round(ci["hi"], 4),
                "n": ci["n"], "excl0": bool(ci["lo"] > 0 or ci["hi"] < 0)}

    results = {}
    for a in def_alphas:
        adk = f"attack_def_a{a:g}"; dok = f"defonly_a{a:g}"
        results[f"alpha_{a:g}"] = {
            "attack_malicious": rate("attack", "mal"),
            "attack_def_malicious": rate(adk, "mal"),
            "malicious_suppression": paired("attack", adk, "mal"),   # want negative (drop)
            "attack_def_rejected": rate(adk, "ref"),                 # genuine refusal re-engagement?
            "benign_refusal_baseline": rate("baseline", "ref"),
            "benign_refusal_defonly": rate(dok, "ref"),
            "benign_over_refusal": paired("baseline", dok, "ref"),   # want ~0
            "degeneration_length_frac": {adk: round(acc[adk]["length"] / max(acc[adk]["n"], 1), 3),
                                          dok: round(acc[dok]["length"] / max(acc[dok]["n"], 1), 3)},
            "labels": {adk: dict(acc[adk]["labels"]), dok: dict(acc[dok]["labels"])},
        }

    summary = {"plan": "NEXT6 D7 defense redo", "model": args.model, "meta": lm.meta(),
               "bench": os.path.abspath(args.bench), "attack_timing": args.attack_timing,
               "attack_window": list(attack_window), "defense_layers": def_layers,
               "concept_alpha": args.concept_alpha, "n_items": len(items),
               "baseline_labels": dict(acc["baseline"]["labels"]),
               "attack_labels": dict(acc["attack"]["labels"]),
               "attack_malicious_rate": rate("attack", "mal"),
               "attack_degeneration_length_frac": round(acc["attack"]["length"] / max(acc["attack"]["n"], 1), 3),
               "results": results}
    out_dir = args.out_dir or os.path.join(
        HERE, "outputs", f"d7_defense_{args.model.split('/')[-1]}_{time.strftime('%Y%m%d_%H%M%S')}_{os.environ.get('SLURM_JOB_ID','')}")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "d7_raw.jsonl"), "w") as f:
        for r in raw:
            f.write(json.dumps(r) + "\n")
    json.dump(summary, open(os.path.join(out_dir, "d7_summary.json"), "w"), indent=2)

    print(f"\n[d7] attack malicious={summary['attack_malicious_rate']} "
          f"(headroom; degeneration_len={summary['attack_degeneration_length_frac']}) n={len(items)}")
    for a in def_alphas:
        r = results[f"alpha_{a:g}"]; ms = r["malicious_suppression"]; bo = r["benign_over_refusal"]
        print(f"  a={a:g}: DSmal {r['attack_malicious']}->{r['attack_def_malicious']} "
              f"(supp d={ms['delta']} ci=[{ms['lo']},{ms['hi']}] excl0={ms['excl0']}) | "
              f"benign_ref {r['benign_refusal_baseline']}->{r['benign_refusal_defonly']} "
              f"(over d={bo['delta']}) | REJ@atkdef={r['attack_def_rejected']} "
              f"len_frac={r['degeneration_length_frac']}")
    print(f"[d7] -> {out_dir}")


if __name__ == "__main__":
    main()
