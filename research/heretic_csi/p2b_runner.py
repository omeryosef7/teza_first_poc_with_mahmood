#!/usr/bin/env python3
"""P2b arm runner: many score_behavior arms in ONE process (model loads once), each optionally under a
weight-space operator (ΔW=B@A hooks) or a module-I/O capture.

REUSE. This is `scripts/dcs_csi_arm_runner.py`'s design (memoised `ds_common.load_model` keyed on every
load parameter, `score_behavior.main()` per arm with a rewritten argv, hook census before/after each
arm) with ONE addition: an OPSPEC per argv line. score_behavior.py is NOT edited (PR-CSI-003 VOID rule).

argv-file line format:  <OPSPEC>\t<python src/boombness/score_behavior.py ...>
  OPSPEC = none
         | capture:<out.pt>:<codeword>[:<n_extra>]  read o_proj/down_proj I/O at the codeword row, the
                                                 last prompt row and <n_extra> seeded random prompt rows
                                                 (PRESERVE set; never BOS, codeword or last) of every
                                                 semantic readout (hooks are pure readers)
         | op:<factors.pt>:<key>                 apply the saved operator factors[key]
         | rand:<factors.pt>:<key>:<seed>        random rank-matched operator, Fro-norm-matched per module
                                                 to factors[key] (seeded; regenerated, not stored)
         | ident:<factors.pt>:<key>              zero operator with factors[key]'s shapes/rank (no-op)

The operator hooks are installed around the whole arm and removed after; the census must read 0
before the next arm. A sidecar `p2b_operator.json` is written into the arm's run directory recording
the OPSPEC, the factors file sha, per-module norms/rank, and how often the hooks fired.

POSITIONS (capture). `string_option_readout(lm, context, ...)` tokenises `context = templated +
"Answer:"` ONCE and appends each answer variant's ids, so every variant forward shares the context
prefix. The bare templated prompt is `ctx_ids[:-len(ids("Answer:"))]` (tail verified, refuses
otherwise); the codeword row is bare rel_end=-10 resolved by `positions.anchor_from_rel_end` with its
LOUD decode self-check; the neutral/last row is bare rel_end=-1. Never `[:, -1]` of the forward.
"""
import argparse, hashlib, importlib.util, json, os, random, re, shlex, sys, time

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
sys.path.insert(0, os.path.join(REPO, "doublespeak_causality"))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))
sys.path.insert(0, os.path.join(REPO, "research", "heretic_csi"))
SCORE_DIR = os.path.join(REPO, "outputs/boombness/score_behavior")

import torch                                    # noqa: E402
import ds_common as dc                          # noqa: E402
import p2b_operator as po                       # noqa: E402
from positions import anchor_from_rel_end, REL_END_CODEWORD_ROW  # noqa: E402

_spec = importlib.util.spec_from_file_location("arm_runner", os.path.join(REPO, "scripts/dcs_csi_arm_runner.py"))
arm_runner = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(arm_runner)

FIT_LAYERS_DEFAULT = list(range(6, 19))


def sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]


_FACT_CACHE = {}


def load_factors(path):
    if path not in _FACT_CACHE:
        _FACT_CACHE.clear()
        _FACT_CACHE[path] = torch.load(path, map_location="cpu")
    return _FACT_CACHE[path]


def resolve_op(spec):
    """OPSPEC -> (kind, factors-or-None, meta)."""
    parts = spec.split(":")
    kind = parts[0]
    if kind == "none":
        return kind, None, {}
    if kind == "capture":
        return kind, None, {"out": parts[1], "codeword": parts[2],
                            "n_extra": int(parts[3]) if len(parts) > 3 else 0}
    path, key = parts[1], parts[2]
    blob = load_factors(path)
    fac = blob["operators"][key]["factors"]
    meta = {"factors_file": path, "factors_sha16": sha16(path), "key": key,
            "fit_meta": blob["operators"][key].get("meta", {})}
    if kind == "op":
        return kind, fac, meta
    shapes = {n: (B.shape[0], A.shape[1]) for n, (A, B) in fac.items()}
    rank = next(iter(fac.values()))[0].shape[0]
    if kind == "rand":
        seed = int(parts[3])
        norms = {n: po.fro_norm(A, B) for n, (A, B) in fac.items()}
        meta.update(seed=seed, norm_matched_to=key)
        return kind, po.random_norm_matched(shapes, rank, norms, seed), meta
    if kind == "ident":
        return kind, po.identity_factors(shapes, rank), meta
    raise SystemExit(f"unknown OPSPEC {spec!r}")


def newest_run_dir(tag, t0):
    pat = re.compile(r"^" + re.escape(tag) + r"_\d{8}_\d{6}_\d+$")
    c = [os.path.join(SCORE_DIR, d) for d in os.listdir(SCORE_DIR) if pat.match(d)]
    c = [d for d in c if os.path.getmtime(d) >= t0 - 5]
    return max(c, key=os.path.getmtime) if c else None


class CaptureWrap:
    """Monkeypatches signals.string_option_readout to arm a CaptureHooks per readout call."""

    def __init__(self, sg, cap, tokenizer, codeword, n_extra=0):
        self.sg, self.cap, self.tok, self.cw, self.n_extra = sg, cap, tokenizer, codeword, n_extra
        self.orig = sg.string_option_readout
        self.ans_ids = None

    def __enter__(self):
        def wrapped(lm, context, options, max_batch=16):
            ctx = lm.tokenizer(context, add_special_tokens=False)["input_ids"]
            if self.ans_ids is None:
                self.ans_ids = lm.tokenizer("Answer:", add_special_tokens=False)["input_ids"]
            k = len(self.ans_ids)
            if ctx[-k:] != self.ans_ids:
                raise SystemExit(f"[p2b capture] REFUSING: context does not end with the ids of "
                                 f"'Answer:' {self.ans_ids}; tail={ctx[-k:]}")
            bare = ctx[:-k]
            a = anchor_from_rel_end(bare, lm.tokenizer, self.cw, REL_END_CODEWORD_ROW,
                                    require_codeword_match=True)
            pos = {"cw": a.abs_pos, "last": len(bare) - 1}
            h16 = hashlib.sha256(json.dumps(ctx).encode()).hexdigest()[:16]
            if self.n_extra:
                pool = [i for i in range(1, len(bare) - 1) if i != a.abs_pos]
                for j, p in enumerate(sorted(random.Random(h16).sample(pool, self.n_extra))):
                    pos[f"x{j}"] = p
            meta = {"anchor": a.to_dict(), "bare_len": len(bare), "positions": dict(pos),
                    "ctx_sha16": h16,
                    "last_token": lm.tokenizer.decode([bare[-1]]),
                    "context_tail": context[-160:]}
            self.cap.arm(pos, meta)
            res = self.orig(lm, context, options, max_batch=max_batch)
            if self.cap.pending is not None:
                raise SystemExit("[p2b capture] REFUSING: readout ran but the capture never fired")
            return res
        self.sg.string_option_readout = wrapped
        return self

    def __exit__(self, *exc):
        self.sg.string_option_readout = self.orig
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--argv-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--fit-layers", default="6-18")
    ap.add_argument("--expect-n", type=int, default=0,
                    help="row count of a COMPLETE arm; >0 enables skip-if-done (requeue safety, S-051)")
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.fit_layers.split("-"))
    names = [po.module_name(l, c) for l in range(lo, hi + 1) for c in ("o_proj", "down_proj")]

    lines = [l.rstrip("\n") for l in open(a.argv_file) if l.strip() and not l.startswith("#")]
    if a.expect_n:
        # REQUEUE SAFETY (S-051). A preempted+requeued allocation must not re-run an arm that already
        # landed: a second run dir under the same tag makes strict_run_dir refuse the whole family.
        # Skip arms with exactly one COMPLETE run; refuse if any tag already has more than one.
        _sp = importlib.util.spec_from_file_location("rederive", os.path.join(REPO, "scripts/dcs_csi_rederive_patch.py"))
        _rd = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(_rd)
        keep, skipped = [], []
        for line in lines:
            av = shlex.split(line.split("\t", 1)[1])
            tag = av[av.index("--tag") + 1]
            try:
                _rd.strict_run_dir(tag, a.expect_n, row_file="results.jsonl")
                skipped.append(tag)
            except SystemExit as e:
                if "more than one" in str(e):
                    sys.exit("REFUSING: tag %r already has more than one complete run (%s)" % (tag, str(e)[:160]))
                keep.append(line)
        if skipped:
            print("[p2b] SKIPPING %d already-complete arm(s)" % len(skipped), flush=True)
        lines = keep
        if not lines:
            print("[p2b] nothing to run"); return 0
    real_load = dc.load_model
    cache, loads = {}, []

    def memo_load_model(model_id=dc.PRIMARY_MODEL, dtype=torch.bfloat16, device_map="auto",
                        revision=None, attn_implementation="sdpa", quantize=None):
        key = (str(model_id), str(dtype), str(device_map), str(revision), str(attn_implementation), str(quantize))
        if key not in cache:
            t0 = time.time()
            cache[key] = real_load(model_id=model_id, dtype=dtype, device_map=device_map, revision=revision,
                                   attn_implementation=attn_implementation, quantize=quantize)
            loads.append({"key": list(key), "seconds": round(time.time() - t0, 3)})
            print("[p2b] MODEL LOAD #%d (%.1fs) key=%s" % (len(loads), loads[-1]["seconds"], key), flush=True)
        return cache[key]
    dc.load_model = memo_load_model
    import score_behavior as sb   # noqa: E402
    import signals as sg          # noqa: E402

    # The operator/capture hooks need the model BEFORE score_behavior.main() runs; the first arm of the
    # file must therefore be a plain arm (OPSPEC none) that loads it, or we pre-load with the same key
    # score_behavior will request. We pre-load from the first line's --model/--dtype/--attn-impl.
    first = shlex.split(lines[0].split("\t", 1)[1])
    mdl = first[first.index("--model") + 1]
    if torch.cuda.is_available() and torch.cuda.get_device_capability(0)[0] < 8:
        sys.exit("REFUSING: non-native-bf16 GPU %s (V100/Turing prohibited)" % torch.cuda.get_device_name(0))
    lm = memo_load_model(model_id=mdl, dtype=torch.bfloat16, device_map="auto", revision=None,
                         attn_implementation="eager", quantize=None)

    results, argv0 = [], list(sys.argv)
    for i, line in enumerate(lines):
        spec, cmd = line.split("\t", 1)
        argv = shlex.split(cmd)
        if argv and argv[0] == "python":
            argv = argv[1:]
        tag = argv[argv.index("--tag") + 1]
        arm = argv[argv.index("--arm") + 1]
        pre_n, pre_w = arm_runner.hook_census_all(cache)
        if pre_n:
            sys.exit("REFUSING before arm %s: %d hook(s) survive: %s" % (arm, pre_n, pre_w[:6]))
        kind, fac, meta = resolve_op(spec)
        t0 = time.time()
        status, rc, side = "ok", None, {"opspec": spec, "kind": kind, **{k: v for k, v in meta.items()
                                                                         if k != "fit_meta"}}
        if "fit_meta" in meta:
            side["fit_meta"] = meta["fit_meta"]
        if fac is not None:
            side["module_fro"] = {n: po.fro_norm(A, B) for n, (A, B) in fac.items()}
            side["rank"] = int(next(iter(fac.values()))[0].shape[0])
            side["n_params"] = int(sum(A.numel() + B.numel() for A, B in fac.values()))
        sys.argv = argv
        cap = None
        try:
            if kind == "capture":
                cap = po.CaptureHooks(lm.model, names)
                with cap, CaptureWrap(sg, cap, lm.tokenizer, meta["codeword"], meta["n_extra"]):
                    rc = sb.main()
            elif fac is not None:
                hk = po.OperatorHooks(lm.model, fac)
                with hk:
                    rc = sb.main()
                side["hook_calls"] = hk.n_calls
                side["mean_last_pos_delta_norm"] = hk.delta_norm_sum / max(1, hk.n_calls)
            else:
                rc = sb.main()
            if rc:   # main() RETURNED nonzero (e.g. 4 = option-mass gate overridden): rows exist, flag it
                status = "returned_rc%s" % rc
        except SystemExit as e:
            rc = e.code if isinstance(e.code, int) else 1
            status = "refused" if rc else "ok"
            if rc:
                print("[p2b] arm %s SystemExit: %s" % (arm, e), flush=True)
        except Exception as e:  # noqa: BLE001
            status, rc = "raised: %r" % (e,), 1
        finally:
            sys.argv = argv0
        rd = newest_run_dir(tag, t0)
        side["run_dir"] = rd
        if cap is not None:
            torch.save({"records": cap.records, "names": names, "tag": tag, "arm": arm, "run_dir": rd,
                        "argv": argv}, meta["out"])
            side["capture_out"] = meta["out"]
            side["n_capture_records"] = len(cap.records)
        if rd:
            json.dump(side, open(os.path.join(rd, "p2b_operator.json"), "w"), indent=1)
        wall = round(time.time() - t0, 1)
        post_n, post_w = arm_runner.hook_census_all(cache)
        results.append({"i": i, "arm": arm, "tag": tag, "opspec": spec, "status": status, "rc": rc,
                        "wall": wall, "hooks_after": post_n, "run_dir": rd})
        print("[p2b] %3d/%d %-22s %-8s rc=%s %7.1fs hooks_after=%d %s"
              % (i + 1, len(lines), arm, status, rc, wall, post_n, spec[:60]), flush=True)
        if len(loads) > 1:
            print("[p2b] REFUSING: a second model load happened (memo key mismatch) -- operator hooks "
                  "were installed on the pre-loaded model, not the one the arm used", flush=True)
            results[-1]["status"] = "VOID_second_model_load"
            break
        if post_n:
            print("[p2b] REFUSING: arm %s leaked %d hooks %s" % (arm, post_n, post_w[:6]), flush=True)
            break
    json.dump({"schema": "hcsi_p2b_runner/1", "n_lines": len(lines), "n_run": len(results),
               "n_ok": sum(r["status"] == "ok" for r in results), "loads": loads, "arms": results},
              open(a.out, "w"), indent=1)
    print("[p2b] arms ok %d/%d | MODEL LOADS %d" % (sum(r["status"] == "ok" for r in results), len(lines), len(loads)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
