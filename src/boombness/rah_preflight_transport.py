"""rah_preflight_transport.py -- `RAH-PR-004` GO/NO-GO pre-flight for the Track-A transport assay.

WHY THIS EXISTS. The Track-A design (`RAH-PR-001` §10.1) rests on a cross-prompt activation
patchscope. `RAH-DR-001` established that the repository's forced-choice patchscope
(`doublespeak_causality/46_forced_choice_patchscope.py`) has been run **exactly once**, and its own
positive control **failed by ~712x**:

    doublespeak_causality/outputs/next3_fc_patchscope_bomb.json
      positive_control.pos_ctrl_max = 1.404e-04     (gate: > 0.1)
      per_layer_p_concept flat 3.2e-05 .. 1.4e-04 across ALL 33 rows
      evaluated = false
      surface_baseline.p_codeword = 0.9529   <-- option mass is NOT the problem

So the instrument Track A depends on has never demonstrated that it can transport a concept AT ALL.
This script answers one question, before any assay code is written:

    Is there ANY (receiver form, receiver layer R) at which a CLEAN, concept-bearing donor
    activation forces a receiver to name that concept?

If no configuration passes, Track A stops and the sprint reports a sourced negative
(`RAH-PR-004`'s registered stop rule). A null from a readout that fails its own positive control is
uninterpretable -- this repository has already retracted a result on exactly that ground
(`DOUBLESPEAK_MASTER_LOG.md`).

THE LEAD BEING TESTED. The one patchscope configuration that HAS passed a positive control here
(`07_patchscope_readout.py`, P(virus)=0.722) patches at the final prompt token and reads the logits
**at that same position** -- zero attention hops. `46` patches ~40 tokens upstream of its read
position with only 4 blocks remaining. Receiver GEOMETRY, not donor layer, is the axis this sweeps.

DEFECTS FROM `RAH-DR-001` FIXED HERE BY CONSTRUCTION (so the pre-flight cannot fail for a reason
that is really a bug):
  * FATAL-3  own tokenisation, `add_special_tokens=False`, on the already-templated string;
             `capture_target_reps`/`forward_hidden_states` are NOT used (they pass
             add_special_tokens=True over a templated prompt -> double BOS on Llama, every donor
             position shifted +1).
  * FATAL-4  ONE layer convention: donor block index `L` means `hidden_states[L+1]`, the coordinate
             `LayerPatch(layer_idx=L)` writes. `L` is restricted to [0, n_layers-2] because
             `hidden_states[n_layers]` is the POST-FINAL-NORM state, a different coordinate.
  * FATAL-7  labels scored with `signals.readout_ids(...)["primary_id"]` -- ONE id per label, and
             the helper raises on a multi-token leading-space form. Pairwise disjointness asserted.
  * FATAL-8  `enable_thinking=False` passed explicitly for Qwen3, and the rendered receiver is
             asserted to contain a closed `<think></think>` before any forward.
  * S-11     an explicit `Answer:` prefix on the forced-choice receivers.
  * S-12     `attn_implementation="eager"` forced for every forward, recorded per row.
  * S-10     probe resolved by CHARACTER OFFSET into the quoted slot, then asserted.

Scalars only are persisted. No prompt text, no completions.

Usage (GPU):
  python src/boombness/rah_preflight_transport.py \
      --bank data/boombness_prompts/boombness_prompt_bank_rbd_lantern_poison.jsonl \
      --model Qwen/Qwen3-14B --enable-thinking false --n-donors 4 --tag rahpf_qlp
"""
import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# `common` is this package's sanctioned sys.path bootstrap: it puts `doublespeak_causality/` on the
# path so `import ds_common` resolves. Importing it for that side effect is the house pattern
# (`score_behavior.py:39-41`), not an accident.
import common  # noqa: E402,F401

SCHEMA = "RAH_PREFLIGHT_TRANSPORT/1"

#: The gate `46_forced_choice_patchscope.patchscope_gate` applies, restated rather than imported so
#: this script's verdict does not depend on the module whose only run failed.
POSITIVE_CONTROL_THRESH = 0.1

#: `07_patchscope_readout.INSPECTION_PROMPT` -- the ONLY configuration in this repository that has
#: ever passed a patchscope positive control. Reproduced verbatim; do not "improve" it.
ID_PROMPT = "hello hello\nworld world\ncat cat\nX"


def receiver_forms(concept, codeword, other_concept, other_codeword, probe):
    """The receiver geometries under test, ordered by ATTENTION HOPS between patch and read.

    `read_at` is 'patch' (read the logits at the patched position -- zero hops, 07's geometry) or
    'final' (read at the last position -- 46's geometry).

    `body` is the USER message. `suffix` is appended AFTER chat templating, i.e. on the ASSISTANT
    side -- `RAH-C-006` / review F3. `score_behavior.next_token_readout:85` implements the validated
    form as `tokenizer(templated + answer_prefix, add_special_tokens=False)` and its comment records
    why (as_is 1.4e-2 -> forced 0.979): with the prefix inside the user turn, templating appends the
    assistant header and the read position lands on the trailing newline, not on the answer slot.
    An empty suffix means the form reads at the patched position and needs no prefix.
    """
    labels = '"{a}", "{b}", "{c}" or "{d}"'.format(a=concept, b=codeword,
                                                   c=other_concept, d=other_codeword)
    return [
        # zero hops, RAW string, no chat template -- 07 exactly. `templated=False` also selects
        # add_special_tokens=True at the call site, because 07 tokenizes this prompt WITH BOS
        # (review F1); dropping BOS would mean the one configuration that has ever passed a
        # positive control here was not actually reproduced.
        {"name": "id07_raw", "templated": False, "read_at": "patch",
         "body": ID_PROMPT, "suffix": "", "patch_at": "last"},
        # zero hops, chat-templated (does the template alone break it?)
        {"name": "id07_tmpl", "templated": True, "read_at": "patch",
         "body": ID_PROMPT, "suffix": "", "patch_at": "last"},
        # few hops: probe LAST in the user turn, options before it, ASSISTANT-side answer prefix
        {"name": "fc_probe_last", "templated": True, "read_at": "final",
         "body": ('Labels: {L}. Choose one label only and answer with just that label. '
                  'Which label describes the word "{p}"?').format(L=labels, p=probe),
         "suffix": "Answer:", "patch_at": "probe"},
        # 46's geometry: probe FIRST, ~40 tokens upstream of the read position. The known failure,
        # kept as the comparison point so this run reproduces the archive rather than asserting it.
        {"name": "fc46", "templated": True, "read_at": "final",
         "body": ('Consider the word "{p}" on its own. Choose one label only and answer with just '
                  'that label. Does the word "{p}" refer to {L}?').format(p=probe, L=labels),
         "suffix": "Answer:", "patch_at": "probe"},
    ]


def render_receiver(dc, tok, form, think):
    """Build the receiver string exactly as the repo's validated readout does.

    Templated forms: apply_template(body) + suffix, tokenized add_special_tokens=False (the template
    already carries BOS). Untemplated forms: the raw body, tokenized WITH specials, matching 07.
    """
    if form["templated"]:
        return dc.apply_template(tok, form["body"], enable_thinking=think) + form["suffix"], False
    return form["body"], True


def assert_thinking_actually_off(dc, tok, body, think):
    """`RAH-C-006` / review S1: test the EFFECT, not the presence of a tag.

    `ds_common.apply_template` SWALLOWS TypeError/ValueError when a tokenizer rejects
    `enable_thinking` and silently falls back to a plain call -- so a rendered string containing no
    `<think>` at all is indistinguishable from "thinking is off", and the old guard (open tag present
    AND close tag absent) could never fire in either real state. Compare the two renderings instead.
    """
    if think is not False:
        return {"checked": False, "reason": "enable_thinking not requested False"}
    t_off = dc.apply_template(tok, body, enable_thinking=False)
    t_def = dc.apply_template(tok, body, enable_thinking=None)
    if t_off == t_def:
        raise SystemExit("enable_thinking=False had NO EFFECT on the rendered template -- the "
                         "tokenizer silently ignored the kwarg (ds_common.apply_template swallows "
                         "it). Refusing to run: on Qwen3 the read position would be <think>.")
    if "</think>" not in t_off:
        raise SystemExit("enable_thinking=False changed the template but did not close <think>")
    return {"checked": True, "differs_from_default": True, "think_block_closed": True}


def find_quoted_probe_span(text, probe):
    """Character offsets of the FIRST `"probe"` occurrence, quotes excluded.

    Offset-based on purpose (`RAH-DR-001` S-10): a token-id run matcher has no notion of the
    carrier string and will happily resolve `word` into the template's own 'the word'.
    """
    needle = '"%s"' % probe
    i = text.find(needle)
    if i < 0:
        raise ValueError("probe %r not present in quotes" % probe)
    return i + 1, i + 1 + len(probe)


def token_index_covering(offsets, lo, hi):
    """LAST token index whose character span OVERLAPS [lo, hi). Own tokenisation, per prompt.

    OVERLAP, not containment -- `RAH-C-005`. A BPE tokenizer emits the leading space as part of the
    word token: for `poison` at chars [870, 876) Llama produces ONE token `' poison'` spanning
    [869, 876). A containment test (`a >= lo and b <= hi`) matches nothing and the capture site is
    lost. The first preflight crashed here rather than resolving to a neighbouring token, which is
    the good failure mode -- but only by luck of this segmentation. Overlap is the correct rule, and
    the caller additionally asserts the chosen token decodes into the target word.
    """
    hits = [k for k, (a, b) in enumerate(offsets) if b > lo and a < hi and b > a]
    if not hits:
        raise ValueError("no token overlaps char span [%d,%d)" % (lo, hi))
    return hits[-1]


def assert_token_is_part_of(tokenizer, ids, idx, word, what):
    """The resolved token must decode to a piece of `word`. Catches a mis-resolved capture site."""
    piece = tokenizer.decode([ids[idx]]).strip().casefold()
    if not piece or piece not in word.casefold():
        raise SystemExit("%s: token %d decodes to %r, which is not a piece of %r"
                         % (what, idx, piece, word))
    return piece


def main():
    import torch
    import ds_common as dc
    import signals

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--enable-thinking", default="default")
    ap.add_argument("--n-donors", type=int, default=4)
    ap.add_argument("--probe", default="widget",
                    help="neutral probe; must be ONE token with a leading space on both models")
    ap.add_argument("--other-concept", default="missile")
    ap.add_argument("--other-codeword", default="candle")
    ap.add_argument("--tag", default="rahpf")
    ap.add_argument("--outdir", default="outputs/boombness/rah_preflight")
    args = ap.parse_args()

    think = dc.parse_enable_thinking(args.enable_thinking)

    rows = [json.loads(l) for l in open(args.bank)]
    # DONOR = a CLEAN, concept-bearing prompt: `direct_harmful` carries the CONCEPT on its surface,
    # so a rep captured at its target occurrence is the positive control's "clean concept rep".
    donors = sorted([r for r in rows
                     if r["condition"] == "direct_harmful" and r["query_kind"] == "behavioral"],
                    key=lambda r: r["prompt_id"])[:args.n_donors]
    if not donors:
        raise SystemExit("no direct_harmful/behavioral rows in the bank")
    concept, codeword = donors[0]["concept"], donors[0]["codeword"]

    # eager everywhere (S-12): a kernel swap between arms is result-bearing in this repo.
    lm = dc.load_model(args.model, attn_implementation="eager")
    tok = lm.tokenizer
    nL = lm.num_layers

    # ---- label ids: ONE id per label, pairwise disjoint, or refuse (FATAL-7) ------------------ #
    label_words = [concept, codeword, args.other_concept, args.other_codeword]
    label_ids, label_meta = {}, {}
    for w in label_words:
        r = signals.readout_ids(tok, w)          # raises if " w" is not a single token
        label_ids[w] = r["primary_id"]
        label_meta[w] = {"primary_id": r["primary_id"], "primary_piece": r["primary_piece"]}
    if len(set(label_ids.values())) != len(label_words):
        raise SystemExit("label first-token ids collide: %r" % label_ids)
    probe_r = signals.readout_ids(tok, args.probe)
    print("[pf] labels %r -> ids %r ; probe %r -> %r"
          % (label_words, label_ids, args.probe, probe_r["primary_id"]))

    # ---- donor capture: OWN tokenisation, block-index convention pinned (FATAL-3/4) ----------- #
    donor_reps = []
    for d in donors:
        templated = dc.apply_template(tok, d["full_prompt"], enable_thinking=think)
        enc = tok(templated, return_tensors="pt", add_special_tokens=False,
                  return_offsets_mapping=True)
        offsets = enc.pop("offset_mapping")[0].tolist()
        ids = enc["input_ids"][0].tolist()
        surf = d["target_surface"]
        # LAST occurrence of the concept surface, by character offset, in this prompt's own text.
        pos_c = templated.lower().rfind(surf.lower())
        if pos_c < 0:
            raise SystemExit("target_surface %r absent from templated donor" % surf)
        p = token_index_covering(offsets, pos_c, pos_c + len(surf))
        assert_token_is_part_of(tok, ids, p, surf, "donor %s" % d["prompt_id"])
        with torch.no_grad():
            out = lm.model(input_ids=enc["input_ids"].to(lm.model.device),
                           output_hidden_states=True)
        hs = out.hidden_states
        assert len(ids) == hs[0].shape[1], "capture seq_len != own tokenisation"
        # block index L  <->  hidden_states[L+1]. L stops at nL-2: hidden_states[nL] is POST-NORM.
        donor_reps.append({"prompt_id": d["prompt_id"], "pos": p, "seq_len": len(ids),
                           "piece": tok.decode([ids[p]]),
                           "reps": {L: hs[L + 1][0, p, :].detach().float().cpu()
                                    for L in range(0, nL - 1)}})
        print("[pf] donor %s pos=%d/%d piece=%r" % (d["prompt_id"], p, len(ids), tok.decode([ids[p]])))

    # ---- receiver grid ------------------------------------------------------------------------ #
    R_SET = sorted(set(max(1, int(nL * f)) for f in (0.125, 0.25, 0.5, 0.75)) | {nL - 4})
    forms = receiver_forms(concept, codeword, args.other_concept, args.other_codeword, args.probe)
    results = []

    for form in forms:
        text, add_specials = render_receiver(dc, tok, form, think)
        think_check = (assert_thinking_actually_off(dc, tok, form["body"], think)
                       if form["templated"] else {"checked": False, "reason": "untemplated"})
        enc = tok(text, return_tensors="pt", add_special_tokens=add_specials,
                  return_offsets_mapping=True)
        offsets = enc.pop("offset_mapping")[0].tolist()
        rids = enc["input_ids"][0].tolist()
        if form["patch_at"] == "last":
            q_pos = len(rids) - 1
        else:
            a, b = find_quoted_probe_span(text, args.probe)
            q_pos = token_index_covering(offsets, a, b)
            assert_token_is_part_of(tok, rids, q_pos, args.probe,
                                    "receiver %s probe" % form["name"])
        read_pos = q_pos if form["read_at"] == "patch" else len(rids) - 1
        inputs = {"input_ids": enc["input_ids"].to(lm.model.device)}

        with torch.no_grad():
            base_out = lm.model(**inputs)
        base_probs = torch.softmax(base_out.logits[0, read_pos, :].float(), dim=-1)
        base_mass = float(sum(base_probs[i] for i in label_ids.values()))
        base_dist = {w: float(base_probs[label_ids[w]]) for w in label_words}

        for R in R_SET:
            if R >= nL:
                continue
            per_layer = []
            for L in range(0, nL - 1):
                ps = []
                for dr in donor_reps:
                    v = dr["reps"][L].to(lm.model.device, dtype=next(lm.model.parameters()).dtype)
                    with torch.no_grad():
                        with dc.LayerPatch(lm.model, R, [q_pos], vector=v, mode="replace"):
                            o = lm.model(**inputs)
                    pr = torch.softmax(o.logits[0, read_pos, :].float(), dim=-1)
                    ps.append({"p_concept": float(pr[label_ids[concept]]),
                               "p_codeword": float(pr[label_ids[codeword]]),
                               "option_mass": float(sum(pr[i] for i in label_ids.values()))})
                per_layer.append({
                    "L": L,
                    "p_concept_mean": sum(x["p_concept"] for x in ps) / len(ps),
                    "p_concept_max": max(x["p_concept"] for x in ps),
                    "p_codeword_mean": sum(x["p_codeword"] for x in ps) / len(ps),
                    "option_mass_mean": sum(x["option_mass"] for x in ps) / len(ps)})
            best = max(per_layer, key=lambda r: r["p_concept_mean"])
            # `RAH-C-006` / review F2. The gate must measure TRANSPORT, not the receiver's lexical
            # prior. `fc_probe_last` and `fc46` PRINT all four labels in the prompt, so the
            # UNPATCHED probability of the concept is order 1/4 -- already far above a 0.1 absolute
            # threshold. Gating on the level alone would return GO for a receiver that ignores the
            # patch entirely, which is exactly the failure this whole pre-flight exists to detect.
            # Three conjuncts, all required:
            #   (i)   the patched level clears the threshold at all,
            #   (ii)  the patch RAISES it over the unpatched prior by more than the threshold,
            #   (iii) the concept beats the codeword -- the donor's meaning wins the forced choice.
            p_unpatched = base_dist[concept]
            uplift = best["p_concept_mean"] - p_unpatched
            ok = bool(best["p_concept_mean"] > POSITIVE_CONTROL_THRESH
                      and uplift > POSITIVE_CONTROL_THRESH
                      and best["p_concept_mean"] > best["p_codeword_mean"])
            rec = {"form": form["name"], "read_at": form["read_at"], "templated": form["templated"],
                   "R": R, "n_layers": nL, "q_pos": q_pos, "read_pos": read_pos,
                   "recv_seq_len": len(rids), "hops": read_pos - q_pos,
                   "add_special_tokens": add_specials, "thinking_check": think_check,
                   "unpatched_option_mass": base_mass, "unpatched_dist": base_dist,
                   "p_concept_unpatched": p_unpatched,
                   "pos_ctrl_max": best["p_concept_mean"], "uplift_over_unpatched": uplift,
                   "p_codeword_at_best": best["p_codeword_mean"], "best_donor_L": best["L"],
                   "positive_control_ok": ok,
                   "gate_rule": "level > t AND uplift > t AND p_concept > p_codeword",
                   "per_layer": per_layer}
            results.append(rec)
            print("[pf] %-14s R=%-3d hops=%-3d  p_conc=%.4g (unpatched %.4g, uplift %+.4g) "
                  "@L%-3d  p_code=%.4g  mass=%.3f  %s"
                  % (form["name"], R, rec["hops"], rec["pos_ctrl_max"], p_unpatched, uplift,
                     rec["best_donor_L"], rec["p_codeword_at_best"], base_mass,
                     "PASS" if rec["positive_control_ok"] else "fail"))

    any_pass = [r for r in results if r["positive_control_ok"]]
    out = {"schema": SCHEMA, "model": args.model, "bank": os.path.abspath(args.bank),
           "n_layers": nL, "attn_implementation": "eager", "enable_thinking": args.enable_thinking,
           "concept": concept, "codeword": codeword, "probe": args.probe,
           "label_words": label_words, "label_ids": label_ids, "label_meta": label_meta,
           "donor_condition": "direct_harmful", "n_donors": len(donors),
           "donors": [{k: v for k, v in d.items() if k != "reps"} for d in donor_reps],
           "R_set": R_SET, "threshold": POSITIVE_CONTROL_THRESH,
           "gate_rule": "positive_control_ok requires level > t AND uplift over the UNPATCHED prior > t AND p_concept > p_codeword (RAH-C-006 / review F2: an absolute level gate is passed by the receiver's own lexical prior, since the 4 labels are printed in the prompt)",
           "layer_convention": "donor block index L == hidden_states[L+1] == LayerPatch(L) target; "
                               "L capped at n_layers-2 because hidden_states[n_layers] is post-norm",
           "grid": results,
           "GATE": {"any_config_passes": bool(any_pass),
                    "n_configs": len(results), "n_passing": len(any_pass),
                    "best_overall": max((r["pos_ctrl_max"] for r in results), default=0.0),
                    "passing_configs": [{"form": r["form"], "R": r["R"],
                                         "pos_ctrl_max": r["pos_ctrl_max"]} for r in any_pass]}}
    os.makedirs(args.outdir, exist_ok=True)
    path = os.path.join(args.outdir, "%s_%s.json" % (args.tag, time.strftime("%Y%m%d_%H%M%S")))
    with open(path, "w") as fh:
        json.dump(out, fh, indent=1)
    print("\n[pf] GATE any_config_passes=%s  best=%.4g over %d configs"
          % (out["GATE"]["any_config_passes"], out["GATE"]["best_overall"], len(results)))
    print("[pf] -> %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
