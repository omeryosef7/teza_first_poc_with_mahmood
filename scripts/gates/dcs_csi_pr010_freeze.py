"""Freeze PR-CSI-010: the section 4 head-level causal experiment.

WHY A GENERATOR AND NOT A HAND-WRITTEN JSON. The head sets are derived FROM a committed screen and
the 20 control draws are derived FROM seeds. Typing them by hand would put numbers in the
preregistration that no command reproduces, which is the failure S-180 recorded about unreproducible
commands -- one level worse here, because a preregistration whose contents cannot be re-derived
cannot be shown to predate the data it governs.

THE SELECTOR IS THE PREREGISTERED ONE AND THE REASONING IS RECORDED. Section 3.4's fallback
(selection by true single-head patch effect) applies ONLY if the true-patch gate FAILS. It PASSED
(916044: pearson 0.7817, spearman 0.7852, both >= 0.7). R14-3 showed the estimate's top-10 cell set
overlaps truth 8 of 10, and S-189 showed h19 leads outright in only 42 of 67 domains -- both are real
reasons one MIGHT prefer true-patch selection, and both became visible ONLY AFTER the gate result.
Substituting the selector now would be a POST-HOC selector change justified by data already seen,
which is exactly what a preregistration exists to forbid. They are recorded as limitations on
INTERPRETATION, not as grounds to re-select.
"""
import argparse, json, os, random, sys, tempfile

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"


def atomic_write_json(path, obj):
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_atomic_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=False); fh.write("\n")
            fh.flush(); os.fsync(fh.fileno())
        if os.path.getsize(tmp) == 0:
            raise OSError("0 bytes after flush+fsync")
        with open(tmp, "r", encoding="utf-8") as fh:
            json.load(fh)
        try:
            mode = os.stat(path).st_mode & 0o7777
        except OSError:
            mode = 0o644
        os.chmod(tmp, mode); os.replace(tmp, path)
        try:
            dfd = os.open(d, os.O_RDONLY)
            try: os.fsync(dfd)
            finally: os.close(dfd)
        except OSError:
            pass
    except Exception as e:
        try: nb = os.path.getsize(tmp)
        except OSError: nb = -1
        try: os.unlink(tmp)
        except OSError: pass
        raise OSError("atomic_write_json FAILED for %s -- %d bytes reached temp; destination "
                      "UNCHANGED. Cause: %r" % (path, nb, e)) from e
    return os.path.getsize(path)


def draw(pool, k, seed):
    """One control draw. random.Random(seed).sample over a SORTED pool, so the result depends only
    on (pool, k, seed) and not on dict or set iteration order."""
    return sorted(random.Random(seed).sample(sorted(pool), k))


def build(screen_path, k, n_controls, seed_base, screen_blob, gate_path,
          pool_mode="complement", pr_id="PR-CSI-010"):
    scr = json.load(open(screen_path))
    S = {int(h): float(v) for h, v in scr["S_signed_by_head"].items()}
    n_heads = scr["n_heads"]
    topk = sorted(S, key=lambda h: S[h])[:k]                  # SIGNED, most negative (design 3.3)
    botk = sorted(S, key=lambda h: abs(S[h]))[:k]             # closest to zero
    # THE CONTROL POOL IS NOW EXPLICIT, and "complement" reproduces PR-CSI-010 exactly.
    # R18/AM-26 measured why the choice matters: an 8-head draw from the complement has expected
    # sum S = +150.6 where an all-32 draw has -152.1 -- OPPOSITE SIGNS. "complement" tests the
    # candidate against other sets drawn from the rest; "all" tests it against ARBITRARY sets, which
    # is the harder question and cannot be answered by re-reading PR-CSI-010's arms.
    if pool_mode == "complement":
        pool = sorted(set(range(n_heads)) - set(topk))        # K of (32-K), candidates excluded
    elif pool_mode == "all":
        pool = sorted(range(n_heads))                          # draws MAY contain candidate heads
    else:
        raise SystemExit("unknown pool_mode %r" % pool_mode)
    # THE CONTROL PREFIX IS PART OF THE PREREGISTRATION, NOT A CONSTANT IN THE TOOLS.
    # PR-CSI-010 and PR-CSI-011 both draw 20 controls, and under the old naming both called
    # them HD_RAND00..19 while meaning DIFFERENT HEAD SETS (PR-010 HD_RAND00 = [1,3,7,8,9,
    # 14,15,30], PR-011 = [10,11,15,16,18,20,22,26]). A read that loaded the wrong prereg
    # would then validate the wrong heads under the right names -- the S-104 duplicate-tag
    # hazard moved up a level, from run dirs to arm identities. Distinct prefixes make the
    # confusion impossible to express.
    prefix = "HD_RAND" if pool_mode == "complement" else "HD_ALL32_"
    controls = {("%s%02d" % (prefix, i)): draw(pool, k, seed_base + i)
                for i in range(n_controls)}
    gate = json.load(open(gate_path))
    return {
        "id": pr_id,
        "title": "Section 4 head-level causal experiment for basket: is an 8-head subset privileged?",
        "frozen_utc_date": "2026-09-21",
        "design_ref": "reports/DCS_CSI_PHASE3_HEAD_CIRCUIT_DESIGN.md sections 4, 5, 6",
        "endpoint": "y_install; concept-free semantic_one_word; cell C; n_examples 4",
        "statistical_unit": "DOMAIN (never the row); button is NEVER pooled with basket",
        "population": {"train_domains": 67, "train_expect_n": 670,
                       "validation_domains": 23, "validation_expect_n": 230,
                       "test_domains_touched": 0,
                       "test_domains": ["restaurant_kitchen", "school_campus", "subway_station"]},
        "intervention": {"intervene": "demo_all:attn_knockout:6-14:1.0",
                         "knockout_scope": "target_surface_row_only", "band": "6-14"},
        "K": k,
        "K_PROVENANCE": ("K=8 was fixed in the design BEFORE any AtP number existed (design 4.2: "
                         "'K is not tuned to the screen'). It is not re-chosen here."),
        "selector": "S[h] SIGNED, summed over the band at p* (design 3.3); |AtP| is never the selector",
        "selector_justification": (
            "Design 3.4's fallback (selection by true single-head patch effect) applies ONLY if the "
            "true-patch gate FAILS. It PASSED. R14-3 (top-10 cell overlap with truth 8 of 10) and "
            "S-189 (h19 leads outright in 42 of 67 domains) are reasons one might prefer true-patch "
            "selection, and BOTH became visible only after the gate result. Substituting the selector "
            "now would be a post-hoc change justified by data already seen. They are limitations on "
            "INTERPRETATION, not grounds to re-select."),
        "screen_provenance": {
            "screen": screen_path, "screen_blob": screen_blob,
            "n_rows_used": scr["n_rows_used"], "n_domains": scr["n_domains"],
            "attn_implementation_loaded": scr["attn_implementation_loaded"],
            "model_id": scr["model_id"], "dtype": scr["dtype"],
            "S_by_head_topk_values": [round(S[h], 6) for h in topk],
            "reproductions": ("S[h] reproduced BIT-IDENTICALLY by jobs 915891, 915941 and 916132"),
        },
        "gate2_attribution_trustworthiness": {
            "artifact": gate_path, "pearson": gate["pearson"], "spearman": gate["spearman"],
            "min_corr": gate["min_corr"], "TRUSTWORTHY": gate["TRUSTWORTHY"],
            "row_sampling": gate.get("row_sampling"), "n_domains_in_gate": gate.get("n_domains_in_gate"),
            "fallback_used": not gate["TRUSTWORTHY"],
        },
        "head_sets": {"HD_TOPK": topk, "HD_BOTK": botk, "control_pool": pool, **controls},
        "control_prefix": prefix,
        "control_pool_mode": pool_mode,
        "control_pool_note": ("complement = the 32-K non-candidate heads (PR-CSI-010); all = every "
                              "head, so a draw MAY contain candidate heads. R18/AM-26: the two pools' "
                              "expected sum S have OPPOSITE SIGNS (+150.6 vs -152.1)"),
        "control_draw_rule": ("sorted(random.Random(seed_base + i).sample(sorted(control_pool), K)) "
                             "for i in 0..%d; seed_base = %d" % (n_controls - 1, seed_base)),
        "seed_base": seed_base, "n_controls": n_controls,
        "arms": {
            "HD_BASE": "no --intervene; the clean reference (--base-arm)",
            "HD_KO": "--knockout-heads omitted = all 32; positive control AND ceiling (--ko-arm/--full-arm)",
            "HD_TOPK": "the candidate (--candidate-arm)",
            "HD_BOTK": "matched opposite end; the COMPARATOR (--comparator-arm), NOT in the control family",
            "%s00..%02d" % (prefix, n_controls - 1): "the dose-matched control family (--control-prefixes %s)" % prefix,
        },
        "n_arms_per_split": 4 + n_controls,
        # THE FLOOR IS STORED EXACTLY, NOT ROUNDED. round(1/21, 4) = 0.0476 is BELOW the true
        # 0.047619..., so rounding moves a p-value floor in the direction that FLATTERS the result.
        # The consequence here is 1.9e-5 and changes no verdict; the principle is that a threshold
        # must never be stored more favourably than it is. `floor_p_display` is for prose only.
        "attainable_floor": {"n_controls": n_controls,
                             "floor_p": 1.0 / (n_controls + 1),
                             "floor_p_display": "%.4f" % (1.0 / (n_controls + 1)),
                             "note": ("rank 1 of %d gives p = floor = %.4f, which clears alpha=0.05 "
                                      "ONLY at rank 1; rank 2 gives %.4f and does NOT pass"
                                      % (n_controls + 1, 1.0 / (n_controls + 1), 2.0 / (n_controls + 1)))},
        "GATE_0_liveness": {"per_arm": ["knockout_liveness.scope_violations == {}",
                                        "frac_rows_scope_live == 1.0", "total_prefill_edits > 0",
                                        "total_decode_edits == 0",
                                        "realised-dose identity of design 4.2: all-head arm records "
                                        "n_edits with n_heads_edited=1 (broadcast); a K-head arm "
                                        "records K explicit rows"],
                            "on_failure": "VOID -- not a result"},
        "GATE_1_positive_control": {"condition": "E(HD_KO) < 0 with ci95 UPPER bound < 0",
                                    "on_failure": "CANNOT ANSWER; report feasibility and STOP; "
                                                  "do NOT report the candidate"},
        "verdicts": {
            "WE_FOUND_THE_WRITER": "HD_TOPK rank 1 of %d vs HD_RAND AND F >= 0.50 with ci95 on F excluding 0" % (n_controls + 1),
            "PARTIALLY_LOCALISED": "rank 1 of %d AND 0 < F < 0.50" % (n_controls + 1),
            "IT_IS_DISTRIBUTED": "GATE 1 passes AND HD_TOPK inside the HD_RAND distribution (p > 0.05) "
                                 "AND the HD_RAND arms themselves show a clear effect",
            "CANNOT_ANSWER": "GATE 1 fails; or GATE 0 fails on any arm; or E(HD_KO) and the whole "
                             "HD_RAND family are all indistinguishable from 0 on validation; or "
                             "candidate and controls are separated by less than single-arm "
                             "run-to-run reproducibility",
        },
        "F_definition": "F = E(HD_TOPK) / E(HD_KO), E(arm) = mean over domains of (y_install(arm) - y_install(HD_BASE))",
        "TRAIN_IS_DESCRIPTIVE": ("the heads were chosen using TRAIN activations, so a TRAIN rank of 1 "
                                 "is partly a restatement of the selection. Every TRAIN rank is to be "
                                 "printed with the words 'selection-contaminated, not an inferential "
                                 "statement' beside it."),
        "multiplicity": ("VALIDATION adjudicates with ONE preregistered test: one candidate against "
                         "%d controls is one test in a family of one. No correction is needed and "
                         "none is applied. HD_BOTK is the comparator and does NOT enter the control "
                         "distribution (S-120(e): a silently-widened control family is this sprint's "
                         "known foot-gun)." % n_controls),
        "HONEST_EXPECTATION_BEFORE_THE_DATA": ("attention-head effects read 5 positions downstream and "
                                               "4+ layers later are usually distributed. PARTIALLY "
                                               "LOCALISED or DISTRIBUTED is expected, with F well "
                                               "under 0.50. A WE_FOUND_THE_WRITER verdict should read "
                                               "as the surprise it would be."),
        "VOID_CONDITIONS": [
            "1. compared arms not all on one GPU architecture (PR-CSI-003 precedent; S-119/S-121)",
            "2. attn_implementation LOADED != eager on any arm (an SDPA knockout is a silent no-op)",
            "3. any arm's worktree not clean at submit, or provenance not exported by the submitter",
            "4. src/boombness/score_behavior.py modified while any arm of this family is running",
            "5. the head sets or seeds differing from this file in any arm's recorded config",
            "6. HD_BOTK entering the control family, or the control family resolving to fewer than "
            "   %d arms" % n_controls,
            "7. any TEST domain appearing in any arm's population",
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen", required=True)
    ap.add_argument("--gate", required=True)
    ap.add_argument("--screen-blob", required=True, help="the commit the screen was produced under")
    ap.add_argument("--K", type=int, default=8)
    ap.add_argument("--n-controls", type=int, default=20)
    ap.add_argument("--seed-base", type=int, default=20260921)
    ap.add_argument("--pool-mode", choices=("complement", "all"), default="complement",
                    help="complement reproduces PR-CSI-010; all draws from every head")
    ap.add_argument("--pr-id", default="PR-CSI-010")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    pr = build(a.screen, a.K, a.n_controls, a.seed_base, a.screen_blob, a.gate,
               pool_mode=a.pool_mode, pr_id=a.pr_id)
    if not pr["gate2_attribution_trustworthiness"]["TRUSTWORTHY"]:
        print("NOTE: gate 2 FAILED -- design 3.4's fallback selection applies and this prereg's "
              "selector clause does not hold. Refusing to freeze.", file=sys.stderr)
        sys.exit(2)
    n = atomic_write_json(a.out, pr)
    print("[pr010] wrote+verified %s (%d bytes)" % (a.out, n))
    print("[pr010] HD_TOPK = %s" % pr["head_sets"]["HD_TOPK"])
    print("[pr010] HD_BOTK = %s" % pr["head_sets"]["HD_BOTK"])
    print("[pr010] arms per split = %d | floor p = %s"
          % (pr["n_arms_per_split"], pr["attainable_floor"]["floor_p"]))


if __name__ == "__main__":
    main()
