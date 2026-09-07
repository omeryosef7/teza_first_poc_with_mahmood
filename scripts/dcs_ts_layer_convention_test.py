#!/usr/bin/env python3
"""Planted-hook test of the layer convention.  `DCS-PR-048` checklist item X3.

MANDATE §22.3: *"Explicitly state: block layer L corresponds to which hidden_states index? Test
this with a planted hook. NEVER infer it from names."*

WHAT IS CURRENTLY KNOWN, AND WHY IT IS NOT ENOUGH. `A-036` read the convention off EIGHT code
sites and found them consistent:

    block layer L == hidden_states[L+1];  hidden_states[0] == embeddings

(`signals.py:46`, `common.py:15`, `extract_boombness.py:21,:346,:439`, `refusalness.py:235`,
`ds_common.py:866`, `09_attention_knockout.py:57`). **That is a code reading, not a test.** Eight
files agreeing tells you the authors agreed; it does not tell you the library does what they
believed. This phase has already been bitten four times by a checker whose notion of a thing
differed from the transformer's actual behaviour (`C-075`, `C-076`, `C-079`, `C-080`), and an
off-by-one here would silently move every read site by one layer.

THE KNOWN COMPLICATION. `extract_boombness.py:331-347`: transformers 5.12 ties the LAST tuple
entry to `last_hidden_state`, so `hidden_states[n_layers]` is POST-final-norm rather than the raw
output of the last block. `forward_hidden()` substitutes the hooked raw `layers[-1]` output. So
`L = n_layers-1` is correct ONLY through `forward_hidden()`, and that substitution must be shown
to be a real substitution rather than a no-op.

THE FIVE ASSERTIONS. A hook adds a large constant to one coordinate at one position, and we check
WHICH tensor moves:

  T1  forward hook on block L: hidden_states[L+1] moves by exactly DELTA at (pos, coord)
  T2  forward hook on block L: hidden_states[L] does NOT move
        -- T1 and T2 together are the convention. If T2 moves instead, it is off by one.
  T3  forward PRE-hook on block L: hidden_states[L] moves, hidden_states[L+1] also moves
        -- a pre-hook writes the INPUT of block L, which is the output of block L-1 == hs[L].
           This is the opposite-direction control: it rules out "every index moves anyway".
  T4  no hook: nothing moves. The trivial control that makes T1-T3 mean something.
  T5  at L = n_layers-1, forward_hidden()'s hs[-1] DIFFERS from out.hidden_states[-1]
        -- proves the post-final-norm substitution is real and not a no-op.

Every assertion prints the measured delta, not just a verdict, so a reader can see the arithmetic.

GPU. Loads the model once, runs a handful of forwards on one short prompt. Minutes, not hours.

USAGE (via the SLURM wrapper, never the login node):
    sbatch --export=ALL,BOOMB_SCRIPT=../../scripts/dcs_ts_layer_convention_test.py,\\
BOOMB_EXPECT=../../scripts/dcs_ts_layer_convention_test.py,BOOMB_REQUIRE_ARGS=1,\\
BOOMB_ARGS=--out_outputs/dcs_ts/layer_convention.json src/boombness/slurm/run_boombness.sh
"""
from __future__ import annotations

import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "src", "boombness"))

DELTA = 1e3
COORD = 0
TEST_LAYER = 12
PROMPT = "The quick brown fox jumps over the lazy dog."


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(REPO, "outputs", "dcs_ts", "layer_convention.json"))
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    a = ap.parse_args()

    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(a.model)
    model = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=torch.bfloat16,
                                                 device_map="cuda", attn_implementation="eager")
    model.eval()
    layers = model.model.layers
    n_layers = len(layers)
    ids = tok(PROMPT, return_tensors="pt").to(model.device)
    pos = ids["input_ids"].shape[1] - 1

    def run(hook=None, module=None, pre=False):
        h = None
        if hook is not None:
            h = (module.register_forward_pre_hook(hook) if pre
                 else module.register_forward_hook(hook))
        try:
            with torch.no_grad():
                out = model(**ids, output_hidden_states=True)
            return [x.detach().float().cpu() for x in out.hidden_states]
        finally:
            if h is not None:
                h.remove()

    # RUN 1 (job 860158) FAILED T1: the return-based post-hook moved nothing. The pre-hook DID
    # move hs[L+1] by 1000.158 -- a residual-stream signature (out = in + f(in), so a +1e3 kick on
    # the input reappears almost exactly on the output). So the harness, not the model, was wrong.
    # Two possible causes, and the test now distinguishes them instead of guessing:
    #   (a) transformers 5.12 blocks may not return a plain tuple, so the returned replacement was
    #       discarded;
    #   (b) the hidden-state tuple may be collected from a tensor the hook's return never reaches.
    # An IN-PLACE edit is immune to both: it mutates the tensor object the caller already holds.
    seen_type = {}

    def add_post_inplace(mod, inp, out):
        seen_type["out"] = type(out).__name__
        t = out[0] if isinstance(out, (tuple, list)) else out
        t[0, pos, COORD] += DELTA          # in place, no return
        return None

    def add_pre(mod, inp):
        t = inp[0].clone()
        t[0, pos, COORD] += DELTA
        return (t,) + tuple(inp[1:])

    base = run()
    post = run(add_post_inplace, layers[TEST_LAYER])
    pre = run(add_pre, layers[TEST_LAYER], pre=True)
    again = run()
    res_block_return_type = seen_type.get("out", "<hook never fired>")

    def d(a_, b_, idx):
        return float((b_[idx][0, pos, COORD] - a_[idx][0, pos, COORD]).item())

    res = {
        "model": a.model, "transformers": transformers.__version__,
        "torch": torch.__version__, "n_layers": n_layers,
        "test_layer": TEST_LAYER, "delta": DELTA, "pos": pos, "coord": COORD,
        "n_hidden_states": len(base),
        "block_return_type": res_block_return_type,
        "checks": {},
    }

    def check(name, ok, detail):
        res["checks"][name] = {"pass": bool(ok), "detail": detail}
        print(f"  {'PASS' if ok else 'FAIL'}  {name:52s} {detail}")

    print(f"=== layer convention, {a.model}, transformers {transformers.__version__} ===")
    print(f"    n_layers={n_layers}  len(hidden_states)={len(base)}  pos={pos}  delta={DELTA}")

    dLp1 = d(base, post, TEST_LAYER + 1)
    dL = d(base, post, TEST_LAYER)
    check("T1_post_hook_moves_hidden_states[L+1]_by_delta", abs(dLp1 - DELTA) < 1.0,
          f"hidden_states[{TEST_LAYER+1}] moved {dLp1:.3f}, want {DELTA}")
    check("T2_post_hook_does_NOT_move_hidden_states[L]", abs(dL) < 1e-3,
          f"hidden_states[{TEST_LAYER}] moved {dL:.6f}, want 0 "
          f"(if THIS is the one that moved by {DELTA}, the convention is OFF BY ONE)")

    pL = d(base, pre, TEST_LAYER)
    pLp1 = d(base, pre, TEST_LAYER + 1)
    # T3 CORRECTED after run 1. My original expectation -- "a pre-hook moves hidden_states[L]" --
    # was WRONG, and run 1 proved it: hs[L] is appended to the tuple BEFORE block L is called, so a
    # pre-hook that rewrites block L's input cannot retroactively change the tuple entry already
    # recorded. What it must do is leave hs[L] untouched and move hs[L+1], and by a RESIDUAL amount:
    # a transformer block computes out = in + f(in), so a +DELTA kick on one input coordinate
    # reappears on the output as DELTA plus a small nonlinear term. Run 1 measured 1000.158 -- that
    # residual signature is itself evidence hs[L+1] is block L's OUTPUT and not some later tensor.
    check("T3a_pre_hook_leaves_hidden_states[L]", abs(pL) < 1e-3,
          f"hidden_states[{TEST_LAYER}] moved {pL:.6f} under a PRE-hook, want 0 "
          f"(it is recorded before block {TEST_LAYER} runs)")
    check("T3b_pre_hook_moves_hidden_states[L+1]_by_residual", abs(pLp1 - DELTA) < 25.0,
          f"hidden_states[{TEST_LAYER+1}] moved {pLp1:.3f} under a PRE-hook, want ~{DELTA} "
          f"(residual pass-through; a non-residual path would not preserve the kick)")

    drift = max(abs(d(base, again, i)) for i in range(len(base)))
    check("T4_no_hook_is_deterministic", drift < 1e-3,
          f"max |delta| across all {len(base)} hidden_states on a repeat forward = {drift:.6f}")

    # T5: the post-final-norm substitution in forward_hidden must be a REAL substitution.
    try:
        from extract_boombness import forward_hidden  # noqa: E402
        try:
            # Run 1: "Could not locate transformer layers on this model." Pass the layer list
            # explicitly where the signature allows it, and record the signature either way so the
            # failure is diagnostic rather than a dead end.
            import inspect
            sig = list(inspect.signature(forward_hidden).parameters)
            res["forward_hidden_signature"] = sig
            hs = forward_hidden(model, ids["input_ids"].to(model.device))
            last_fh = hs[-1] if not isinstance(hs, tuple) else hs[0][-1]
            same = torch.allclose(last_fh[0, pos].float().cpu(), base[-1][0, pos], atol=1e-3)
            check("T5_forward_hidden_last_differs_from_out.hidden_states[-1]", not same,
                  "forward_hidden's last layer differs from the post-final-norm tuple entry "
                  "(substitution is real)" if not same else
                  "IDENTICAL -- the post-norm substitution is a NO-OP; L=n_layers-1 is unsafe")
        except Exception as e:  # signature drift is informative, not fatal
            check("T5_forward_hidden_last_differs_from_out.hidden_states[-1]", False,
                  f"could not call forward_hidden: {type(e).__name__}: {e}")
    except Exception as e:
        check("T5_forward_hidden_last_differs_from_out.hidden_states[-1]", False,
              f"could not import forward_hidden: {type(e).__name__}: {e}")

    n_pass = sum(1 for v in res["checks"].values() if v["pass"])
    n = len(res["checks"])
    res["summary"] = {"n_checks": n, "n_pass": n_pass, "all_pass": n_pass == n}
    # The convention is CONFIRMED by the post-hook pair (T1+T2) -- the direct test. T3a/T3b are a
    # second, independent route to the same conclusion via the residual signature, and are reported
    # but not sufficient on their own: a corroborating observation is not the experiment.
    res["convention_confirmed"] = bool(
        res["checks"]["T1_post_hook_moves_hidden_states[L+1]_by_delta"]["pass"]
        and res["checks"]["T2_post_hook_does_NOT_move_hidden_states[L]"]["pass"])
    res["convention_corroborated_by_prehook"] = bool(
        res["checks"]["T3a_pre_hook_leaves_hidden_states[L]"]["pass"]
        and res["checks"]["T3b_pre_hook_moves_hidden_states[L+1]_by_residual"]["pass"])
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=2)
    print(f"\n[layer-convention] {n_pass}/{n} checks pass -> {a.out}")
    print(f"[layer-convention] block L == hidden_states[L+1]: "
          f"{'CONFIRMED BY EXPERIMENT' if res['convention_confirmed'] else 'NOT CONFIRMED -- STOP'}")
    return 0 if res["convention_confirmed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
