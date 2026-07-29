"""
gcg_mixed_cache.py — Track B (temporal-GCG) step 2: assemble the MIXED reference cache.

The temporal objective J = late_harmful_align − λ·early_harmful_align is realised (GCG_MAC_COMPARISON §2)
as a layer-weighted repr_loss against a MIXED reference:
  early layers (idx < --split-layer) → BENIGN reference reps  (from the Neutral-instruction cache)
  late  layers (idx >= --split-layer) → HARMFUL reference reps (from the Direct-instruction cache)

Both input caches are produced by the EXISTING `poc_stage_gcg_early/build_reference_cache.py` (one run per
manifest from step 1). This script is pure tensor/dict surgery — no model, no harmful text — so it is fully
benign and unit-testable offline (`--self-test`).

Each cache dir (see reference_cache.ReferenceCache): a `REFERENCE_CACHE_MANIFEST.json` (one JSON/line:
task_id, cache_key, layers, positions, ...) + per-task `{safe_task_id}_{cache_key}.pt` files holding
{input_ids, hidden_states:{str(layer):{str(pos):tensor}}}. The merged cache keeps the BENIGN input_ids +
metadata (the candidate is optimized on the Neutral prompt) and swaps late-layer hidden_states for harmful.

Usage:
  python doublespeak_causality/gcg_mixed_cache.py \
    --benign-cache-dir  outputs/gcg/cache_llama_neutral \
    --harmful-cache-dir outputs/gcg/cache_llama_direct \
    --out-cache-dir     outputs/gcg/cache_llama_mixed --split-layer 18
  python doublespeak_causality/gcg_mixed_cache.py --self-test
"""
import argparse
import json
import os
import shutil


def _safe(task_id):
    return task_id.replace("/", "_").replace(" ", "_")


def _load_manifest(cache_dir):
    p = os.path.join(cache_dir, "REFERENCE_CACHE_MANIFEST.json")
    out = {}
    with open(p) as f:
        for line in f:
            line = line.strip()
            if line:
                e = json.loads(line)
                out[e["task_id"]] = e
    return out


def merge(benign_dir, harmful_dir, out_dir, split_layer):
    import torch
    bman, hman = _load_manifest(benign_dir), _load_manifest(harmful_dir)
    os.makedirs(out_dir, exist_ok=True)
    out_manifest = os.path.join(out_dir, "REFERENCE_CACHE_MANIFEST.json")
    if os.path.exists(out_manifest):
        os.remove(out_manifest)                       # idempotent rebuild
    tasks = sorted(set(bman) & set(hman))
    skipped = sorted((set(bman) ^ set(hman)))
    n = 0
    for tid in tasks:
        bm, hm = bman[tid], hman[tid]
        # both caches must share key config so positions/layers align (instruction is NOT in the key)
        if bm["cache_key"] != hm["cache_key"]:
            raise ValueError(f"{tid}: benign/harmful cache_key differ ({bm['cache_key']} vs {hm['cache_key']}) "
                             "— rebuild both with identical neutral_suffix/layers/positions/thinking.")
        if sorted(bm.get("layers", [])) != sorted(hm.get("layers", [])):
            raise ValueError(f"{tid}: benign/harmful layer sets differ.")
        bpt = torch.load(os.path.join(benign_dir, f"{_safe(tid)}_{bm['cache_key']}.pt"),
                         map_location="cpu", weights_only=False)
        hpt = torch.load(os.path.join(harmful_dir, f"{_safe(tid)}_{hm['cache_key']}.pt"),
                         map_location="cpu", weights_only=False)
        b_hs, h_hs = bpt["hidden_states"], hpt["hidden_states"]
        if set(b_hs) != set(h_hs):
            raise ValueError(f"{tid}: hidden_states layer keys differ between caches.")
        merged_hs = {}
        for lkey, posd in b_hs.items():               # early←benign, late←harmful (by integer layer idx)
            merged_hs[lkey] = posd if int(lkey) < split_layer else h_hs[lkey]
        merged = {"input_ids": bpt["input_ids"], "hidden_states": merged_hs}
        torch.save(merged, os.path.join(out_dir, f"{_safe(tid)}_{bm['cache_key']}.pt"))
        meta = dict(bm)                                # keep benign metadata (candidate optimizes Neutral prompt)
        meta["mixed_split_layer"] = split_layer
        meta["harmful_source"] = "direct"
        with open(out_manifest, "a") as f:
            f.write(json.dumps(meta, ensure_ascii=True) + "\n")
        n += 1
    return {"n_merged": n, "split_layer": split_layer, "skipped_unpaired": skipped,
            "out_cache_dir": out_dir}


def _self_test():
    import torch
    import tempfile
    root = tempfile.mkdtemp(prefix="mixedcache_selftest_")
    bdir, hdir, odir = (os.path.join(root, d) for d in ("benign", "harmful", "mixed"))
    layers, positions, key = [0, 10, 20, 30], [0, 1, 2], "deadbeef"
    for cdir, val in ((bdir, 1.0), (hdir, 2.0)):       # benign reps=1.0, harmful reps=2.0
        os.makedirs(cdir)
        with open(os.path.join(cdir, "REFERENCE_CACHE_MANIFEST.json"), "w") as f:
            for tid in ("t1", "t2"):
                f.write(json.dumps({"task_id": tid, "cache_key": key, "layers": layers,
                                    "positions": positions, "dtype": "float16"}) + "\n")
                hs = {str(L): {str(p): torch.full((4,), val) for p in positions} for L in layers}
                torch.save({"input_ids": torch.tensor([1, 2, 3]) if val == 1.0 else torch.tensor([9, 9, 9]),
                            "hidden_states": hs}, os.path.join(cdir, f"{tid}_{key}.pt"))
    info = merge(bdir, hdir, odir, split_layer=15)
    ok = True
    for tid in ("t1", "t2"):
        d = torch.load(os.path.join(odir, f"{tid}_{key}.pt"), map_location="cpu", weights_only=False)
        hs = d["hidden_states"]
        early_ok = all(hs[str(L)][str(0)][0].item() == 1.0 for L in (0, 10))    # early ← benign(1.0)
        late_ok = all(hs[str(L)][str(0)][0].item() == 2.0 for L in (20, 30))    # late  ← harmful(2.0)
        ids_ok = d["input_ids"].tolist() == [1, 2, 3]                            # benign input_ids kept
        ok = ok and early_ok and late_ok and ids_ok
        print(f"  {tid}: early=benign {early_ok} | late=harmful {late_ok} | benign_input_ids {ids_ok}")
    shutil.rmtree(root)
    print("SELF-TEST", "PASS" if ok and info["n_merged"] == 2 else "FAIL", "|", info["n_merged"], "merged")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--benign-cache-dir")
    ap.add_argument("--harmful-cache-dir")
    ap.add_argument("--out-cache-dir")
    ap.add_argument("--split-layer", type=int, default=18,
                    help="layers with idx < split take BENIGN reps; idx >= split take HARMFUL reps")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        raise SystemExit(_self_test())
    if not (args.benign_cache_dir and args.harmful_cache_dir and args.out_cache_dir):
        ap.error("--benign-cache-dir, --harmful-cache-dir, --out-cache-dir required (or --self-test)")
    print(json.dumps(merge(args.benign_cache_dir, args.harmful_cache_dir, args.out_cache_dir,
                           args.split_layer), indent=2))


if __name__ == "__main__":
    main()
