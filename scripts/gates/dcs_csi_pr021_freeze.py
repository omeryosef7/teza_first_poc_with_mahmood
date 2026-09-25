#!/usr/bin/env python3
"""Emit PR-CSI-021 -- the RUNG 2 (DECODABILITY) family on BASKET VALIDATION cells.

⛔ IT REFUSES TO EMIT unless everything it names already EXISTS (S-167c). In particular it requires
   the TRAIN measurement, because the power table is computed FROM it and a prereg that names a
   power table it cannot compute is a document naming something that does not exist.

WHY THE STATISTIC IS IMPORTED RATHER THAN REIMPLEMENTED
-------------------------------------------------------
S-389 settled that the rung-2 statistic must MIRROR PR-CSI-020's exactly, and the reason is not
symmetry for its own sake: AM-34's ladder claims the rungs are SEPARABLE -- *"information may be
readable at a site without being used there"* -- so testing that claim requires the SAME statistic
applied to a DIFFERENT quantity. If the two families' statistics drifted, a rung-1/rung-2
disagreement would be indistinguishable from an artefact of the statistic.

So this file IMPORTS `binom_ge`, `n_assign` and `power_mc` from `dcs_csi_pr020_freeze.py` -- the
three the FREEZE needs, for the floors and the power table. `perm_tail` and `certifies` belong to
the READ, not the freeze, and are used by `dcs_csi_pr016_argmax_test.py` when the family is read.
Sameness is then a property of the code, not a claim in a docstring.
⚠ An earlier draft of this docstring listed all five as imported here. A test asserting the import
caught it: the docstring claimed more than the code did, which is the defect this whole file exists
to avoid committing at the scale of a prereg.
⚠ S-350's lesson applies and is why this matters: two independent implementations of "the same"
statistic agreed only at M=K, and the difference would have published a PASS against a prereg
saying it could not certify. The way to make two things identical is to make them one thing.

WHAT IS MEASURED (the quantity -- NOT the statistic, which is PR-CSI-020's)
--------------------------------------------------------------------------
For each (layer L, head h) cell, the contribution to the ENDPOINT'S readout position along the
model's own concept-minus-codeword direction, summed over the DEMONSTRATION-BLOCK source positions
that `demo_all` knocks out, divided by the per-prompt rms, averaged per DOMAIN and then over
domains. `scripts/dcs_csi_rung2_celldecode.py` computes it; R35 reviewed it across three agents and
S-395 executed it (recon_rel_err 3.1e-03 against a 3e-2 tolerance, an 8.6x margin).

⛔⛔ THE LIMITATION THAT MUST TRAVEL WITH ANY RESULT (R35-A finding 6, unresolved by design):
   THIS IS A DIRECT-PATH ATTRIBUTION. It projects a layer-L head's output onto a direction defined
   at the FINAL residual, ignoring what layers L+1..31 do to it -- 17 to 25 blocks for band cells.
   The RUNG 1 knockout measures the TOTAL effect including those paths. A cell can be causally
   necessary and have near-zero direct projection, and that would read here as "not decodable".
   This is NOT a defect to be fixed before the read; it is what the instrument measures.

⚠ AND IT IS NOT A DECOMPOSITION OF y_install (S-381/S-382). The endpoint aggregates the casings
   with LOGSUMEXP; this direction aggregates them LINEARLY, which is what makes the per-cell
   decomposition exact. They are built from the same four unembedding rows and the same two
   surfaces, and nothing more may be claimed.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRAIN_ARTEFACT = "reports/DCS_CSI_RUNG2_TRAIN_basket_full.json"
INSTRUMENT = "scripts/dcs_csi_rung2_celldecode.py"
READER = "scripts/dcs_csi_pr021_rung2_read.py"      # ⚠ S-398: does not exist yet -- see below
OUT = "configs/dcs_csi_pr021_rung2_decode_basket_validation.json"

# the population, MEASURED in S-388 and reproduced by the instrument's own gate in S-395
VAL_EXPECT_N, VAL_EXPECT_DOMAINS = 230, 23
BANK = "data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl"
EXCLUDE = "runargs/dcs_cont/exclude_basket_bomb_sow_validation.txt"
BANK_BLOCK, CONDITION = "cds_n4_sow", "natural_doublespeak"
ANSWER_PREFIX = "Answer:"
DTYPE = "bfloat16"
CONCEPT_IDS = [13054, 33909]        # ' bomb', ' Bomb'   -- verified against the tokenizer, S-380
CODEWORD_IDS = [14351, 34217]       # ' basket', ' Basket'


def _pr020():
    """The PR-CSI-020 freeze module, imported so the STATISTIC is shared rather than copied."""
    p = os.path.join(REPO, "scripts", "gates", "dcs_csi_pr020_freeze.py")
    spec = importlib.util.spec_from_file_location("pr020_freeze", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def train_q(art, heads, pred):
    """The MEASURED per-head match rate on TRAIN -- the discovery split.

    S-379 established the power CANNOT be borrowed from PR-CSI-020's causal rate, because that
    would assume the coincidence this experiment exists to test. Measuring it on TRAIN assumes
    nothing: it is the ordinary, non-circular use of a discovery split, and is exactly how
    PR-CSI-018's observed rate informed PR-CSI-020's power table (S-354)."""
    cm = art["cell_mean_over_domains"]
    matched, per_head = 0, {}
    for h in heads:
        vals = {L: abs(cm["L%d_h%d" % (L, h)]) for L in _pr020().BAND
                if cm.get("L%d_h%d" % (L, h)) is not None}
        if len(vals) != len(_pr020().BAND):
            raise SystemExit("REFUSING: the train artefact has no value for every band layer of "
                             "head %d, so its argmax would be taken over an incomplete set." % h)
        top = max(vals, key=lambda L: vals[L])
        hit = (top == pred[str(h)]["layer"])
        matched += hit
        per_head[str(h)] = {"argmax_layer": top, "screen_predicted_layer": pred[str(h)]["layer"],
                            "MATCH": bool(hit)}
    return matched, len(heads), per_head


def main() -> int:
    m = _pr020()
    # ⚠ ORDERED FIRST: an existence check is cheaper than reading and validating the
    # train artefact, and R35-C's F14 is that every cheap refusal belongs before the
    # expensive one -- otherwise a missing reader costs a file read to discover.
    # ⚠⚠ S-398: MY OWN S-167c ENFORCEMENT WAS PARTIAL, and a test would not have caught it.
    # This script refuses when the POWER SOURCE is absent, and then happily emitted a prereg that
    # names NO READ PATH AT ALL. A preregistration must say how it will be read; ours named an
    # `instrument` and stopped there. And the rung-1 reader cannot stand in: pr016 requires
    # ON_PROTOCOL, GATE_0_and_identity.per_arm, rep["E"], rep["ci95"] and rep["CELL_FAMILY"],
    # none of which a rung-2 artefact has -- it has cell_mean_over_domains, no arms, no GATE 0.
    # So the rule this file enforces for the power table applies to itself.
    reader_path = os.path.join(REPO, READER)
    if not os.path.exists(reader_path):
        raise SystemExit(
            "REFUSING TO EMIT: %s does not exist.\n"
            "A prereg must name the READ that will produce its verdict, and the rung-1 reader\n"
            "cannot substitute -- dcs_csi_pr016_argmax_test.py requires a CENSUS report\n"
            "(ON_PROTOCOL, GATE_0_and_identity.per_arm, E, ci95, CELL_FAMILY) and a rung-2\n"
            "artefact has none of those. Naming a read that does not exist is S-167c, the same\n"
            "rule this script already enforces for the power table. (S-398)" % READER)
    art_path = os.path.join(REPO, TRAIN_ARTEFACT)
    if not os.path.exists(art_path):
        raise SystemExit(
            "REFUSING TO EMIT: %s does not exist. The power table is computed FROM the TRAIN\n"
            "measurement, and a prereg naming a power table it cannot compute is a document\n"
            "naming something that does not exist (S-167c). Run the instrument with --limit 0\n"
            "on --split train first." % TRAIN_ARTEFACT)
    art = json.load(open(art_path))
    if art.get("⚠ IS_SMOKE"):
        raise SystemExit("REFUSING: %s is a SMOKE artefact (IS_SMOKE true). A power table from a "
                         "limited, domain-contiguous sample is not a power table." % TRAIN_ARTEFACT)
    if art.get("split") != "train":
        raise SystemExit("REFUSING: the power artefact is split %r, not train. The discovery split "
                         "is what makes this non-circular." % art.get("split"))
    if (art.get("selection_n_rows"), art.get("selection_n_domains")) != (670, 67):
        raise SystemExit("REFUSING: the train artefact covers %r rows / %r domains, not 670/67."
                         % (art.get("selection_n_rows"), art.get("selection_n_domains")))

    pred, screen_meta = m.screen_predictions()
    heads = list(m.HEADS)
    M_tr, K_tr, per_head_tr = train_q(art, heads, pred)
    q_hat = M_tr / float(K_tr)

    adm = [str(h) for h in heads]
    pv = [pred[a]["layer"] for a in adm]
    uq = [a for a in adm if pv.count(pred[a]["layer"]) == 1]
    floors = {"binomial": m.binom_ge(len(adm), len(adm)),
              "conditional": m.binom_ge(len(uq), len(uq)),
              "permutation": 1.0 / m.n_assign(pv)}
    floors["WEAKEST"] = max(floors, key=lambda k: floors[k])

    power = {}
    for q in (1.0 / 9.0, 0.25, 0.33, 0.50, q_hat, 0.83, 1.0):
        power["q=%.4f" % q] = m.power_mc(pred, adm, q, m.MC_N, m.MC_SEED)

    pr = {
        "id": "PR-CSI-021",
        "title": "RUNG 2 (DECODABILITY): is the concept readable from the cell the screen names?",
        "EMITTED_MECHANICALLY_BY": "scripts/gates/dcs_csi_pr021_freeze.py",
        "frozen_utc_date": None,            # set by the caller's commit, not by the clock
        "split": "validation", "codeword": "basket", "concept": "bomb",
        "statistical_unit": "domain",
        "heads": heads, "layers": list(m.BAND), "band": "6-14",
        "instrument": INSTRUMENT,
        "reader": READER,
        "reader_md5": None,          # filled below, once the file exists
        "⚠ THE_STATISTIC_IS_IMPORTED_FROM": "scripts/gates/dcs_csi_pr020_freeze.py -- binom_ge, "
            "perm_tail, certifies, power_mc, n_assign. S-389: the rungs are only comparable if the "
            "statistic is the SAME one applied to a DIFFERENT quantity, and S-350 showed that two "
            "'identical' implementations agreed only at M=K.",
        "QUANTITY": {
            "what": "per-cell contribution to the ENDPOINT's readout position along the model's own "
                    "concept-minus-codeword direction, over demo_all's source positions, divided by "
                    "the per-prompt rms, aggregated per DOMAIN then over domains",
            "direction": "u = g_final * (mean(W[' bomb'],W[' Bomb']) - mean(W[' basket'],W[' Basket']))"
                         "  -- FROZEN in S-382 before any measurement existed",
            "concept_ids": CONCEPT_IDS, "codeword_ids": CODEWORD_IDS,
            "readout_position": "len(tokenize(templated + %r)) - 1 -- the position the ENDPOINT "
                                "reads (score_behavior.py:87). NOT the bare prompt end, which "
                                "score_behavior measured at ~5.6e-06 option mass and abandoned "
                                "2026-08-18 (R35-A/B)." % ANSWER_PREFIX,
            "dtype": DTYPE,
        },
        "PRIMARY": {
            "statistic": "M = number of heads whose |contribution| ARGMAX over the nine band layers "
                         "equals that head's frozen screen-predicted layer",
            "⚠ ABSOLUTE_VALUE": "|contribution|, mirroring PR-CSI-020's -abs(E) argmax. S-389: the "
                "direction is a CONTRAST, so magnitude in either sign means the cell discriminates, "
                "which is what decodability means. The SIGNED value is recorded alongside so the "
                "directional question stays askable without a second run, but it is NOT the primary.",
            "null": "the screen's per-cell prediction is unrelated to where the concept is readable",
            "alpha": m.ALPHA,
            "binomial": "P(Binom(K, 1/9) >= M)",
            "conditional": "the same over heads whose predicted layer is UNIQUE among the set",
            "permutation": "over the DISTINCT assignments of the prediction multiset, scored "
                           "against the OBSERVED ARGMAX VECTOR (S-352)",
            "GATING": "weakest_of_three",
            "SUCCESS": "the WEAKEST of the three <= alpha AND the spanning rule satisfied",
            "FAILURE": "the weakest > alpha with K >= 3",
            "SPANNING_RULE": "the MATCHING heads must not all share one band layer",
            "ALL_THREE_FLOORS_AT_K8": floors,
            "K_IS_FIXED_AT_8": "there is NO rung-2 admission gate. The eight heads are PR-CSI-020's, "
                "every one of which passed rung-1 admission (dropped_heads: [], D40). K is therefore "
                "8 by construction and the floor is known exactly. ⛔ CONSEQUENCE: this family says "
                "NOTHING about heads that fail rung-1 admission, and the head set is rung-1-selected, "
                "which is disclosed here and is NOT held out.",
        },
        "POWER_BY_SEEDED_MONTE_CARLO": {
            "N": m.MC_N, "seed": m.MC_SEED,
            "model": "each head's decodability argmax lands on its predicted layer with probability "
                     "q independently; a miss lands uniformly on one of the other 8 layers",
            "table": power,
            "q_MEASURED_ON_TRAIN": q_hat,
            "⚠ WHY A TRAIN q AND NOT PR-CSI-020's": "S-379: borrowing the CAUSAL rate would assume "
                "the coincidence this experiment tests -- the ladder's claim is that the rungs are "
                "SEPARABLE. A q measured on the DISCOVERY split assumes nothing and is the ordinary "
                "use of one, exactly as PR-CSI-018's rate informed PR-CSI-020 (S-354).",
            "⚠ IT IS AN ESTIMATE": "a train q is an input to a design, not a claim about validation. "
                "It may be wrong in either direction and the verdict does not depend on it.",
            "train_evidence": {"artefact": TRAIN_ARTEFACT, "md5": m.md5(art_path),
                               "M": M_tr, "K": K_tr, "per_head": per_head_tr,
                               "n_rows": art.get("selection_n_rows"),
                               "n_domains": art.get("selection_n_domains")},
        },
        "population": {"validation_domains": VAL_EXPECT_DOMAINS,
                       "validation_expect_n": VAL_EXPECT_N,
                       "bank": BANK, "bank_block": BANK_BLOCK, "condition": CONDITION,
                       "exclude_prompt_ids": EXCLUDE,
                       "⚠ WHAT_KEEPS_TEST_OUT": "the instrument enforces the domain split from "
                           "data/boombness_prompts/dcs_ts116_domain_split.json PER ROW and excludes "
                           "the three preregistered whole-population domains. S-384: the exclusion "
                           "FILE alone is NOT sufficient -- it removes only the non-split part of "
                           "ONE bank_block/condition slice, and relying on it selected 116 domains "
                           "including all 23 TEST ones."},
        "MUST_NOT_BE_SAID_IF_POSITIVE": [
            "that the cell is where the concept IS USED. This is RUNG 2 (decodability), and AM-34's"
            " ladder says in terms: information may be readable at a site without being used there."
            " It stands BESIDE the rung-1 results, never as a stronger version of them.",
            "that this decomposes y_install, or that a cell's share here is its share of the "
            "installation effect. The endpoint aggregates casings with LOGSUMEXP and this direction "
            "is LINEAR (S-381/S-382).",
            "anything about cells' TOTAL contribution. ⛔ THIS IS A DIRECT-PATH ATTRIBUTION and "
            "ignores 17-25 blocks of downstream processing (R35-A).",
            "that this is held out on CODEWORD. It is not -- split only, like PR-CSI-020.",
            "anything about heads outside the eight, which are rung-1-selected and not held out.",
            "the binomial p alone. The claim is the WEAKEST of three, each named.",
        ],
        "MUST_NOT_BE_SAID_IF_NULL": [
            "that the concept is NOT readable at these cells. A direct-path projection can be near "
            "zero for a cell that is causally necessary, which is exactly the separability the "
            "ladder warns about -- in the direction that makes a null UNINFORMATIVE about rung 1.",
            "that PR-CSI-020 / D40 is weakened. The rungs are separable; a rung-2 null retracts "
            "nothing at rung 1 and D40 stands on its own arms.",
            "that the screen is useless. Check the power table before saying anything about what a "
            "null rules out.",
        ],
        "VOID_CONDITIONS": {
            "5": "the screen artefact's md5 must still be %s" % m.md5(
                os.path.join(REPO, m.SCREEN_ARTIFACT)),
            "9": "every prompt measured in ONE slurm job on ONE GPU architecture",
            "10": "attn_implementation == eager (dominance_at requires output_attentions)",
            "11": "scripts/ and src/ unchanged while the job is in flight",
            "12": "the frozen read is not amended after any number from this family is seen",
            "13": "the instrument's recon_rel_err must be RECORDED and within dominance_at's "
                  "dtype tolerance. S-395 measured 3.1e-03 against 3e-2 on train.",
        },
        "WHAT_THIS_CANNOT_ANSWER": [
            "whether the cell is USED (rung 3 repair / rung 4 transfer are untouched)",
            "anything about the other 24 heads or about TEST",
            "whether decodability and necessity coincide -- that is what it MEASURES, not assumes",
        ],
        "instrument_md5": m.md5(os.path.join(REPO, INSTRUMENT)),
    }

    pr["reader_md5"] = m.md5(reader_path)
    outp = os.path.join(REPO, OUT)
    with open(outp, "w", encoding="utf-8") as fh:
        json.dump(pr, fh, indent=1, ensure_ascii=False)
    print("[pr021] wrote %s  md5 %s" % (OUT, m.md5(outp)))
    print("[pr021] TRAIN q = %d/%d = %.4f   (artefact %s, md5 %s)"
          % (M_tr, K_tr, q_hat, TRAIN_ARTEFACT, m.md5(art_path)))
    print("[pr021] floors at K=8: %s  WEAKEST = %s"
          % ({k: "%.6e" % v for k, v in floors.items() if k != "WEAKEST"}, floors["WEAKEST"]))
    print("[pr021] power at the measured q: %s" % power.get("q=%.4f" % q_hat))
    return 0


if __name__ == "__main__":
    sys.exit(main())
