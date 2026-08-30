"""rah_transport_assay.py -- the Track-A donor->receiver assay.

THE QUESTION. Under `demo_processing_only`, forced-choice binding collapses (Qwen3 75/80 -> 9/80).
Was the semantic representation DESTROYED, or is it still present and merely unreportable?

THE CONSTRUCTION. Capture the model's internal state at the CODEWORD position of a
`natural_doublespeak` prompt -- with the intervention hooks LIVE -- and transplant it into an
independent, never-intervened receiver that decodes it as a 4-way forced choice. The options exist
only in the receiver and only AFTER the donor state was captured, so they cannot have created it.
This is what escapes the exposure/option-mass dilemma the predecessor sprint proved is otherwise
inescapable (`RBD-R-033`).

    DONOR  natural_doublespeak x behavioral row, hooks live, NO options anywhere
             |  capture resid_post at (donor layer L, codeword position in the QUERY span)
             v
    RECEIVER fc_probe_last, ALWAYS unintervened, frozen by RAH-R-010 at depth 0.125
             |  LayerPatch(replace) at (R, probe slot); read 4 option ids after "Answer:"
             v
    4-cell distribution: mapped-concept / literal-codeword / other-concept / other-codeword

WHAT IS INHERITED, AND FROM WHERE
  * receiver form, R, probe, label ids, span resolution: `rah_preflight_transport` (imported, not
    copied), frozen by `RAH-R-010` -- fc_probe_last at depth fraction 0.125, min uplift 0.8516
    across six level-A runs.
  * arm-active donor capture: the pattern at `score_behavior.py:1892-1928`, the ONLY place in this
    repository where a capture forward runs under live intervention hooks.
  * intervention construction, span helpers: `score_behavior.make_intervention`,
    `demo_key_positions`, `query_span_positions`; `donor_patch.ActivationCapture`.

DEFECTS FROM `RAH-DR-001` / `RAH-DR-002` DESIGNED OUT RATHER THAN GUARDED AGAINST
  * F2 (vacuity): a donor layer at or below the band's first layer makes base and dpo BIT-IDENTICAL,
    and every validity gate still passes because none of them sees the dpo arm. `--donor-layer` is
    REFUSED unless L > lo, and `delta_norm` / `cos_base_dpo` are recorded per row so a vacuous cell
    is visible in the artifact rather than inferred.
  * D-late DELETED. A late band with a fixed mid-depth capture site is `D-base` relabelled. The
    same-band, count-matched key control (`nondemo_matched_d*`) replaces it: band, depth, dose and
    key COUNT fixed, only key IDENTITY varies.
  * S-15: the receiver forward happens OUTSIDE every knockout context. `blocked_keys` are absolute
    DONOR-prompt positions; applied to a 50-token receiver they would mask arbitrary tokens with no
    error. The contexts are entered for the donor forward and exited before the receiver runs.
  * S-12: `attn_implementation="eager"` for every arm including the unintervened ones, recorded per
    row, because a kernel swap between arms is result-bearing in this repo.
  * S-16: liveness asserts key PRESENCE before value -- `stats.get(k, 0)` lets a MISSING
    required-zero counter pass silently (`RAH-R-002-b`).
  * S-21: option order is counterbalanced over 2 rotations per family and averaged.

WHAT THIS FILE DOES NOT DO. It computes no verdict, no equivalence test and no aggregate. It emits
one row per (family x arm x rotation) and stops. Analysis lives elsewhere, so that adding an arm
cannot quietly change a published estimate.
"""
import argparse
import contextlib
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common  # noqa: E402,F401  (sys.path bootstrap for ds_common / pair_common)
import rah_preflight_transport as pf  # noqa: E402  -- the FROZEN receiver, imported not copied

SCHEMA = "RAH_TRANSPORT_ASSAY/1"

#: Frozen by `RAH-R-010`: fc_probe_last at depth fraction 0.125.
FROZEN_FORM = "fc_probe_last"
FROZEN_DEPTH_FRACTION = 0.125

#: First layer of each model's knockout band. A donor layer must be strictly ABOVE it or the
#: base and dpo arms are bit-identical at a query position (`RAH-DR-001` F2).
BAND_LO = {"meta-llama/Llama-3.1-8B-Instruct": 6, "Qwen/Qwen3-14B": 7}

#: Donor arms that require a live forward. Derived controls are computed from these afterwards.
LIVE_ARMS = ("base", "dpo", "keys")

#: `RAH-C-008` / `RAH-DR-002` F5. In nuisance-ensemble mode the ONLY live arm is `base`, and the
#: intervened arms are not merely unused -- they are never constructed. The equivalence margin is
#: derived from this run, so the run that produces the margin must be structurally incapable of
#: seeing the effect the margin will later be used to judge.
NUISANCE_LIVE_ARMS = ("base",)


def label_rotations(labels, n):
    """`n` option orders placing the MAPPED concept in a different slot each time.

    labels is [concept, codeword, other_concept, other_codeword]. Rotation r puts the concept at
    position r and keeps the other three in their relative order, so option POSITION cannot be
    confounded with option IDENTITY across the ensemble.
    """
    c, rest = labels[0], labels[1:]
    out = []
    for r in range(min(n, len(labels))):
        out.append(rest[:r] + [c] + rest[r:])
    return out


def parse_band(band):
    """'6-14' -> [6..14], matching `score_behavior.py:1517` exactly (inclusive of hi)."""
    lo, hi = (int(x) for x in band.split("-"))
    if hi < lo:
        raise SystemExit("band %r is inverted" % band)
    return list(range(lo, hi + 1))


def build_arm_spec(arm, band, key_arm, scope="demo_processing_only"):
    """`--intervene` spec for a live arm, in `make_intervention`'s own dict shape.

    The shape is `{direction, mode, layers, alpha}` (`score_behavior.py:906`), where `direction`
    selects the KEY SET from `KNOCKOUT_ARMS`, `mode` is always `attn_knockout`, `layers` is the
    explicit list of block indices and alpha is always 1.0 (a mask edit is not dosable).
    `base` returns None -- no hooks are constructed at all, not an identity hook.
    """
    if arm == "base":
        return None, None
    if arm == "dpo":
        return {"direction": "demo_all", "mode": "attn_knockout",
                "layers": parse_band(band), "alpha": 1.0}, scope
    if arm == "keys":
        # Same band, same scope, same key COUNT, different key IDENTITY. This is the control that
        # REPLACES the deleted late band: a late band with a fixed mid-depth capture site would be
        # `D-base` relabelled, because the capture site never sees it (`RAH-DR-001` F2).
        return {"direction": key_arm, "mode": "attn_knockout",
                "layers": parse_band(band), "alpha": 1.0}, scope
    raise ValueError("unknown live arm %r" % arm)


def liveness_snapshot(stats, arm, problems, label):
    """`S-16`: assert key PRESENCE first. A MISSING required-zero counter must FAIL, not pass."""
    if arm == "base":
        if stats:
            problems.append("%s: base arm produced knockout stats %r" % (label, sorted(stats)))
        return {"arm": arm, "checked": "base_expects_no_hooks", "n_prefill_edits": 0}
    required_present = ("n_prefill_edits", "n_decode_edits")
    missing = [k for k in required_present if k not in stats]
    if missing:
        problems.append("%s: liveness counters MISSING %r -- missing is not zero" % (label, missing))
        return {"arm": arm, "MISSING": missing}
    if int(stats["n_prefill_edits"]) <= 0:
        problems.append("%s: n_prefill_edits=%r, the hook did not fire"
                        % (label, stats["n_prefill_edits"]))
    if int(stats["n_decode_edits"]) != 0:
        problems.append("%s: n_decode_edits=%r, must be 0 for a prefill-only scope"
                        % (label, stats["n_decode_edits"]))
    return {"arm": arm, "n_prefill_edits": int(stats["n_prefill_edits"]),
            "n_decode_edits": int(stats["n_decode_edits"]),
            "n_keys_masked": int(stats.get("n_keys_masked", -1)),
            "n_query_rows_edited": int(stats.get("n_query_rows_edited", -1))}


def main():
    import torch
    import ds_common as dc
    import pair_common as pc
    import signals
    from extract_boombness import resolve_occurrences
    from donor_patch import ActivationCapture
    import score_behavior as sb

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bank", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--band", required=True, help="knockout band, e.g. 6-14 (Llama) / 7-17 (Qwen3)")
    ap.add_argument("--donor-layer", type=int, required=True,
                    help="donor BLOCK index L; captured state is hidden_states[L+1]. MUST be > lo.")
    ap.add_argument("--enable-thinking", default="default")
    ap.add_argument("--n-rows", type=int, default=80)
    ap.add_argument("--n-examples", type=int, default=8)
    ap.add_argument("--probe", default="widget")
    ap.add_argument("--other-concept", required=True)
    ap.add_argument("--other-codeword", required=True)
    ap.add_argument("--rotations", type=int, default=2,
                    help="option orders, each placing the mapped concept in a different slot")
    ap.add_argument("--nuisance-ensemble", action="store_true",
                    help="MARGIN MODE. Computes ONLY the base donor -- the intervened arms are "
                         "never constructed -- and sweeps the nuisance axes (option order x "
                         "receiver wording). This is the run that produces the equivalence margin, "
                         "so it is structurally incapable of seeing the effect that margin judges.")
    ap.add_argument("--seed", type=int, default=20260830)
    ap.add_argument("--key-control-arm", default="nondemo_capped_d1",
                    help="key set for the same-band key control. Default is the CAPPED policy: "
                         "on this population STRICT count-matching is infeasible (the demo block "
                         "is larger than the entire protected complement), which the run MEASURES "
                         "per row rather than assuming. See RAH-R-011.")
    ap.add_argument("--tag", default="rahta")
    ap.add_argument("--outdir", default="outputs/boombness/rah_transport")
    args = ap.parse_args()

    lo = BAND_LO[args.model]
    if args.donor_layer <= lo:
        raise SystemExit("REFUSING: donor layer %d <= band lo %d. At or below the band's first "
                         "layer a QUERY-position residual is BIT-IDENTICAL between the base and "
                         "dpo arms, every validity gate still passes because none of them sees "
                         "the dpo arm, and the assay would report 'preserved' on two tensors that "
                         "were the same bytes (RAH-DR-001 F2)." % (args.donor_layer, lo))
    band_lo_arg = int(args.band.split("-")[0])
    if band_lo_arg != lo:
        raise SystemExit("REFUSING: --band starts at %d but this model's recorded band lo is %d; "
                         "the vacuity constraint is derived from lo and must not drift from it"
                         % (band_lo_arg, lo))

    if args.key_control_arm not in sb.KNOCKOUT_ARMS:
        raise SystemExit("--key-control-arm %r is not a valid key set; KNOCKOUT_ARMS=%r"
                         % (args.key_control_arm, sb.KNOCKOUT_ARMS))
    think = dc.parse_enable_thinking(args.enable_thinking)
    rng = random.Random(args.seed)
    problems = []

    rows_all = [json.loads(l) for l in open(args.bank)]
    pop = sorted([r for r in rows_all
                  if r["condition"] == "natural_doublespeak" and r["query_kind"] == "behavioral"
                  and r["n_examples"] == args.n_examples],
                 key=lambda r: r["prompt_id"])[:args.n_rows]
    if not pop:
        raise SystemExit("empty population")
    concept, codeword = pop[0]["concept"], pop[0]["codeword"]

    live_arms = NUISANCE_LIVE_ARMS if args.nuisance_ensemble else LIVE_ARMS
    if args.nuisance_ensemble:
        assert "dpo" not in live_arms and "keys" not in live_arms, \
            "nuisance mode must not construct an intervened arm"
        print("[ta] NUISANCE-ENSEMBLE MODE: live arms = %r; no intervened arm is constructed"
              % (live_arms,))

    lm = dc.load_model(args.model, attn_implementation="eager")   # S-12: eager for EVERY arm
    tok, nL = lm.tokenizer, lm.num_layers
    R = max(1, int(nL * FROZEN_DEPTH_FRACTION))

    labels = [concept, codeword, args.other_concept, args.other_codeword]
    label_ids = {}
    for w in labels:
        label_ids[w] = signals.readout_ids(tok, w)["primary_id"]   # raises on multi-token
    if len(set(label_ids.values())) != len(labels):
        raise SystemExit("label first-token ids collide: %r" % label_ids)
    print("[ta] model=%s nL=%d R=%d (depth %.3f) band=%s donorL=%d labels=%r"
          % (args.model, nL, R, FROZEN_DEPTH_FRACTION, args.band, args.donor_layer, label_ids))

    # ---------------- PASS 1: capture donors, one live forward per (row, live arm) -------------- #
    donors = []
    infeasible_rows = {}
    for row in pop:
        pid = row["prompt_id"]
        try:
            templated_r, ids_r, last_idx, _following, _nsub = resolve_occurrences(
                dc, tok, row, enable_thinking=think)
        except ValueError as e:
            problems.append("%s: resolve:%s" % (pid, e))
            continue
        dk, dk_reason = sb.demo_key_positions(tok, row, templated_r)
        if dk_reason:
            problems.append("%s: demokeys:%s" % (pid, dk_reason))
            continue
        prot = sb.query_span_positions(tok, row, templated_r, dk)
        if not prot:
            # S-17: an empty query span is a hard failure, never a silent fallback to another site.
            problems.append("%s: query_span_positions returned EMPTY -- refusing to fall back" % pid)
            continue
        in_query = sorted(set(last_idx) & set(prot))
        if not in_query:
            problems.append("%s: no codeword occurrence inside the query span" % pid)
            continue
        p_cw = in_query[-1]          # the mechanistic site: last codeword use in the request
        piece = tok.decode([ids_r[p_cw]]).strip().casefold()
        if not piece or piece not in codeword.casefold():
            problems.append("%s: capture token %r is not a piece of %r" % (pid, piece, codeword))
            continue

        # MEASURED, not assumed: would a STRICT count-matched control have been constructible?
        _slog = {}
        try:
            sb.nondemo_control_draw(dk, len(ids_r), protected=prot, seed=args.seed,
                                    policy="strict", log=_slog)
            strict_ok = True
        except sb.InfeasibleControl:
            strict_ok = False
        rec = {"strict_match_feasible": strict_ok,
               "strict_pool_size": _slog.get("pool_size"),
               "strict_demo_count": _slog.get("demo_count"),
               "prompt_id": pid, "family_id": row["family_id"], "domain": row["domain"],
               "split": row["split"], "seq_len": len(ids_r), "capture_pos": p_cw,
               "capture_piece": piece, "n_demo_keys": len(dk), "n_query_span": len(prot),
               "vectors": {}, "liveness": {}}
        for arm in live_arms:
            spec, scope = build_arm_spec(arm, args.band, args.key_control_arm)
            kstats = {} if spec else None
            kdraw = {}
            try:
                ctxs = sb.make_intervention(
                    dc, pc, lm, spec, None, control_seed=args.seed, demo_keys=dk,
                    seq_len=len(ids_r), knock_stats=kstats, protected=prot,
                    knock_scope=scope or "demo_processing_only", draw_log=kdraw) if spec else []
            except sb.InfeasibleControl as e:
                # A control that CANNOT be constructed on this row is recorded, never skipped
                # silently and never substituted. `RAH-R-011`.
                rec.setdefault("infeasible", {})[arm] = str(e)
                infeasible_rows.setdefault(arm, []).append(pid)
                continue
            rec.setdefault("draw", {})[arm] = {
                k: kdraw.get(k) for k in ("pool_size", "demo_count", "achieved_count",
                                          "control_draw_match_ratio", "policy", "seed")
                if k in kdraw}
            cap = ActivationCapture(lm.model, args.donor_layer, [p_cw])
            with torch.no_grad():
                with contextlib.ExitStack() as st:
                    for c in ctxs:
                        st.enter_context(c)      # hooks LIVE for the donor forward only
                    st.enter_context(cap)
                    lm.model(input_ids=torch.tensor([ids_r], device=lm.model.device))
            # every knockout context is now EXITED. The receiver never runs under them (S-15).
            if cap.acts is None:
                problems.append("%s/%s: donor capture empty" % (pid, arm))
                continue
            v = cap.acts[0].detach().float().cpu()
            rec["vectors"][arm] = v
            rec["liveness"][arm] = liveness_snapshot(kstats or {}, arm, problems,
                                                     "%s/%s" % (pid, arm))
        # base and dpo are REQUIRED; a missing key control is degraded, not fatal, and is counted.
        _required = {"base"} if args.nuisance_ensemble else {"base", "dpo"}
        if not _required <= set(rec["vectors"]):
            problems.append("%s: missing a REQUIRED donor arm; have %r"
                            % (pid, sorted(rec["vectors"])))
            continue
        vb = rec["vectors"]["base"]
        rec["norm_base"] = float(vb.norm())
        if "dpo" in rec["vectors"]:
            vd = rec["vectors"]["dpo"]
            d = (vd - vb)
            rec["delta_norm_dpo_base"] = float(d.norm())
            rec["rel_delta_dpo_base"] = float(d.norm() / vb.norm()) if float(vb.norm()) else None
            rec["cos_base_dpo"] = float((vb @ vd) / (vb.norm() * vd.norm()))
            rec["norm_dpo"] = float(vd.norm())
        else:
            rec["delta_norm_dpo_base"] = None
            rec["rel_delta_dpo_base"] = None
            rec["cos_base_dpo"] = None
        if "keys" in rec["vectors"]:
            rec["norm_keys"] = float(rec["vectors"]["keys"].norm())
        donors.append(rec)
        if len(donors) % 20 == 0:
            print("[ta] captured %d/%d donors" % (len(donors), len(pop)))

    if not donors:
        raise SystemExit("no donors captured; problems=%r" % problems[:5])

    # VACUITY GATE (F2, empirical form): if the two arms are bit-identical the cell is VACUOUS.
    have_dpo = [r for r in donors if r.get("delta_norm_dpo_base") is not None]
    if have_dpo:
        n_zero = sum(1 for r in have_dpo if r["delta_norm_dpo_base"] == 0.0)
        vacuity = {"n_rows": len(have_dpo), "n_delta_exactly_zero": n_zero,
                   "median_rel_delta": sorted(r["rel_delta_dpo_base"]
                                              for r in have_dpo)[len(have_dpo) // 2],
                   "median_cos": sorted(r["cos_base_dpo"] for r in have_dpo)[len(have_dpo) // 2],
                   "VACUOUS": n_zero == len(have_dpo)}
        print("[ta] vacuity: %d/%d rows delta EXACTLY zero; median rel-delta %.4g, median cos %.4f"
              % (n_zero, len(have_dpo), vacuity["median_rel_delta"], vacuity["median_cos"]))
        if vacuity["VACUOUS"]:
            problems.append("VACUOUS CELL: every dpo donor is bit-identical to its base donor")
    else:
        vacuity = {"not_applicable": "nuisance-ensemble mode constructs no intervened arm"}

    # ---------------- derived controls, computed from the captured bank ------------------------- #
    import torch as _t
    base_stack = _t.stack([r["vectors"]["base"] for r in donors])
    mean_vec = base_stack.mean(0)
    # D-exch: a seeded DERANGEMENT over families, persisted (S-13 + the repo's own draw rule).
    idx = list(range(len(donors)))
    der = idx[:]
    while any(a == b for a, b in zip(idx, der)):
        rng.shuffle(der)
    perm_dims = list(range(base_stack.shape[1]))
    rng.shuffle(perm_dims)

    # ---------------- PASS 2: decode every arm through the FROZEN receiver ---------------------- #
    out_rows = []
    orders = label_rotations(labels, args.rotations)
    variants = []
    for rot, order in enumerate(orders):
        if args.nuisance_ensemble:
            forms = pf.nuisance_receiver_forms(order[0], order[1], order[2], order[3], args.probe)
        else:
            forms = [f for f in pf.receiver_forms(order[0], order[1], order[2], order[3],
                                                  args.probe) if f["name"] == FROZEN_FORM]
        for form in forms:
            variants.append((rot, order, form))
    print("[ta] %d receiver variants = %d option orders x %d wordings"
          % (len(variants), len(orders), len(variants) // max(1, len(orders))))

    for rot, order, form in variants:
        text, adds = pf.render_receiver(dc, tok, form, think)
        if form["templated"]:
            pf.assert_thinking_actually_off(dc, tok, form["body"], think)
        enc = tok(text, return_tensors="pt", add_special_tokens=adds, return_offsets_mapping=True)
        offs = enc.pop("offset_mapping")[0].tolist()
        rids = enc["input_ids"][0].tolist()
        q_pos = pf.token_index_covering(offs, *pf.find_quoted_probe_span(text, args.probe))
        pf.assert_token_is_part_of(tok, rids, q_pos, args.probe, "receiver rot%d" % rot)
        read_pos = len(rids) - 1
        inputs = {"input_ids": enc["input_ids"].to(lm.model.device)}
        dtype = next(lm.model.parameters()).dtype

        with torch.no_grad():
            base_logits = lm.model(**inputs).logits[0, read_pos, :].float()
        unpatched = torch.softmax(base_logits, -1)

        def decode(vec):
            with torch.no_grad():
                with dc.LayerPatch(lm.model, R, [q_pos], vector=vec.to(lm.model.device, dtype=dtype),
                                   mode="replace"):
                    lg = lm.model(**inputs).logits[0, read_pos, :].float()
            p = torch.softmax(lg, -1)
            lp = torch.log_softmax(lg, -1)
            return ({w: float(p[label_ids[w]]) for w in labels},
                    {w: float(lp[label_ids[w]]) for w in labels})

        for i, r in enumerate(donors):
            vb = r["vectors"]["base"]
            # Donor-side controls are ALWAYS available (they are derived from `base`); the live
            # intervened arms are present only when they were constructed. In nuisance-ensemble
            # mode they never are, so referencing them unconditionally is a crash, not a null --
            # which is how this was caught (`RAH-C-009`).
            arms = {"base": vb,
                    "exch": donors[der[i]]["vectors"]["base"],
                    "mean": mean_vec,
                    "perm": vb[perm_dims],
                    "rand": _t.randn(vb.shape, generator=_t.Generator().manual_seed(
                        args.seed + i)) * (vb.norm() / (vb.shape[0] ** 0.5))}
            for _live in ("dpo", "keys"):
                if _live in r["vectors"]:
                    arms[_live] = r["vectors"][_live]
            for arm, vec in arms.items():
                probs, logps = decode(vec)
                out_rows.append({
                    "prompt_id": r["prompt_id"], "family_id": r["family_id"],
                    "domain": r["domain"], "split": r["split"], "rotation": rot,
                    "receiver_variant": form["name"],
                    "variant_key": "%s|rot%d" % (form["name"], rot),
                    "arm": arm, "model": args.model, "bank": os.path.basename(args.bank),
                    "concept": concept, "codeword": codeword,
                    "other_concept": args.other_concept, "other_codeword": args.other_codeword,
                    "donor_layer": args.donor_layer, "receiver_R": R, "n_layers": nL,
                    "band": args.band, "attn_implementation": "eager",
                    "capture_pos": r["capture_pos"], "capture_piece": r["capture_piece"],
                    "donor_seq_len": r["seq_len"], "n_query_span": r["n_query_span"],
                    "n_demo_keys": r["n_demo_keys"],
                    "q_pos": q_pos, "read_pos": read_pos, "option_order": order,
                    "p": probs, "logp": logps,
                    "option_mass": sum(probs.values()),
                    "p_unpatched": {w: float(unpatched[label_ids[w]]) for w in labels},
                    # PRIMARY estimand companion (S-1): harm-matched, concept vs OTHER CONCEPT,
                    # so a donor that merely raises harm salience cannot win it.
                    "margin_harm_matched": logps[concept] - logps[args.other_concept],
                    "margin_vs_codeword": logps[concept] - logps[codeword],
                    "argmax_label": max(probs, key=probs.get),
                    "donor_norm": float(vec.norm()),
                    "delta_norm_dpo_base": r["delta_norm_dpo_base"],
                    "rel_delta_dpo_base": r["rel_delta_dpo_base"],
                    "cos_base_dpo": r["cos_base_dpo"],
                    "liveness": r["liveness"].get(arm)})
        print("[ta] variant %s rot%d decoded: %d rows total" % (form["name"], rot, len(out_rows)))

    os.makedirs(args.outdir, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    run = os.path.join(args.outdir, "%s_%s" % (args.tag, stamp))
    os.makedirs(run, exist_ok=True)
    with open(os.path.join(run, "rows.jsonl"), "w") as f:
        for r in out_rows:
            f.write(json.dumps(r) + "\n")
    meta = {"schema": SCHEMA, "model": args.model, "bank": os.path.abspath(args.bank),
            "n_layers": nL, "receiver_R": R, "depth_fraction": FROZEN_DEPTH_FRACTION,
            "receiver_form": FROZEN_FORM, "donor_layer": args.donor_layer, "band": args.band,
            "band_lo": lo, "attn_implementation": "eager", "enable_thinking": args.enable_thinking,
            "condition": "natural_doublespeak", "n_examples": args.n_examples,
            "labels": labels, "label_ids": label_ids, "probe": args.probe,
            "rotations": args.rotations, "seed": args.seed,
            "nuisance_ensemble": bool(args.nuisance_ensemble),
            "live_arms": list(live_arms),
            "n_receiver_variants": len(variants),
            "receiver_variants": sorted(set("%s|rot%d" % (f["name"], r) for r, _o, f in variants)),
            "n_families_requested": len(pop), "n_families_captured": len(donors),
            "n_rows_written": len(out_rows), "vacuity": vacuity,
            "derangement": der, "problems": problems,
            "key_control_arm": args.key_control_arm,
            "key_control_infeasible_rows": {k: len(v) for k, v in infeasible_rows.items()},
            "strict_match_feasible_rows": sum(1 for r in donors if r.get("strict_match_feasible")),
            "n_rows_with_key_arm": sum(1 for r in donors if "keys" in r["vectors"]),
            "complete": len(donors) == len(pop) and not problems}
    with open(os.path.join(run, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print("[ta] families %d/%d, rows %d, problems %d -> %s"
          % (len(donors), len(pop), len(out_rows), len(problems), run))
    for p in problems[:10]:
        print("   PROBLEM:", p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
