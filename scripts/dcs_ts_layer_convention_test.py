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

    def add_post(mod, inp, out):
        # A block returns a tuple whose first element is the hidden state.
        t = out[0] if isinstance(out, tuple) else out
        t = t.clone()
        t[0, pos, COORD] += DELTA
        return (t,) + tuple(out[1:]) if isinstance(out, tuple) else t

    def add_pre(mod, inp):
        t = inp[0].clone()
        t[0, pos, COORD] += DELTA
        return (t,) + tuple(inp[1:])

    base = run()
    post = run(add_post, layers[TEST_LAYER])
    pre = run(add_pre, layers[TEST_LAYER], pre=True)
    again = run()

    def d(a_, b_, idx):
        return float((b_[idx][0, pos, COORD] - a_[idx][0, pos, COORD]).item())

    res = {
        "model": a.model, "transformers": transformers.__version__,
        "torch": torch.__version__, "n_layers": n_layers,
        "test_layer": TEST_LAYER, "delta": DELTA, "pos": pos, "coord": COORD,
        "n_hidden_states": len(base),
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
    check("T3_pre_hook_moves_hidden_states[L]", abs(pL - DELTA) < 1.0,
          f"hidden_states[{TEST_LAYER}] moved {pL:.3f} under a PRE-hook, want {DELTA}; "
          f"hidden_states[{TEST_LAYER+1}] moved {pLp1:.3f} (expected nonzero: it propagates)")

    drift = max(abs(d(base, again, i)) for i in range(len(base)))
    check("T4_no_hook_is_deterministic", drift < 1e-3,
          f"max |delta| across all {len(base)} hidden_states on a repeat forward = {drift:.6f}")

    # T5: the post-final-norm substitution in forward_hidden must be a REAL substitution.
    try:
        from extract_boombness import forward_hidden  # noqa: E402
        try:
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
    res["convention_confirmed"] = bool(res["checks"]["T1_post_hook_moves_hidden_states[L+1]_by_delta"]["pass"]
                                       and res["checks"]["T2_post_hook_does_NOT_move_hidden_states[L]"]["pass"])
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=2)
    print(f"\n[layer-convention] {n_pass}/{n} checks pass -> {a.out}")
    print(f"[layer-convention] block L == hidden_states[L+1]: "
          f"{'CONFIRMED BY EXPERIMENT' if res['convention_confirmed'] else 'NOT CONFIRMED -- STOP'}")
    return 0 if res["convention_confirmed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
