#!/usr/bin/env python3
"""dcs_readout_family.py -- the PROBABILITY / READOUT FAMILY, reported side by side.

WHAT THIS IS. A REPORTING INSTRUMENT. It turns the single headline number
`semantic_logodds` into the whole family of quantities it was condensed from, so that a reader can
see -- for every population already on disk -- what the log-odds is a ratio *of*, and how much
probability mass the two contrasted options actually hold.

    A. logp_concept          whole-answer log P(the CONCEPT word)      [teacher-forced, all variants]
    B. logp_codeword         whole-answer log P(the CODEWORD)          [same construction]
    C. semantic_logodds      = A - B                                   [the phase headline]
    D. concept_binary_prob   = exp(A) / (exp(A) + exp(B))              [the NORMALISED two-option
                               probability -- see the naming rule below]
    E. option_mass           = exp(A) + exp(B)                         [how much of the next-answer
                               distribution the two options hold between them]
    F. decoded top-1 / semantic category                               [what the model would SAY]

⛔ NAMING RULE, LOAD-BEARING. `D` is called **`concept_binary_prob`** (`bomb_binary_prob` when the
concept is `bomb`). It is ⛔ **NOT** `P(bomb)`. It is not a full-vocabulary probability; it is a
probability *conditional on the answer being one of the two scored options*. The plan fixes this
name in §6.4 and forbids the other one.

⛔ WHY `E` IS PRINTED BESIDE `D` EVERYWHERE. §1.5 of the plan (`R-050`) makes this a PHASE-WIDE
rule: `option_mass` collapses **0.877 -> 0.264** when no mapping is installed, so a log-odds -- and
equally a binary probability -- computed on a weakly-mapped population contrasts two options the
model **largely rejects**. `C` and `D` are mass-invariant by construction: they cannot see that
collapse. `E` is the only member of the family that can. A population whose median `E` is below
`DEGRADED_OPTION_MASS` is stamped **MEASURED IN A DEGRADED REGIME** in every table and in the JSON.

⛔ WHAT THIS IS NOT.
  * It computes **no p-value**, runs **no test**, and declares **no hypothesis supported**.
    There is no sign test, no Holm family, no bootstrap in this file, on purpose.
  * It does **not** contrast `bomb` against `knife`/`gun`/`club`. That comparison is `PR-035`,
    which is preregistered and running; pre-empting it here would be a second, uncorrected look at
    the same question. Each `inst_*` arm is reported **on its own**, and the code refuses to emit a
    cross-arm difference.
  * It reads only artifacts that already exist. No GPU, no model weights, no generation. The only
    model asset touched is the **tokenizer**, to decode `top1_id` for `F`.

REUSE. Arm discovery (`find_arm`/`load_arm`, including the `C-051` completeness rule that refuses a
partial run dir) is imported from `scripts/dcs_kladder_analysis.py`. The answer-variant construction
for `F`'s category test is imported from `src/boombness/signals.py` (`answer_variants`), the same
function that built the probabilities being reported. Nothing here is a second copy of either.

CRASH > SILENT SKIP. Every row is checked for the eleven fields the family needs and for the
identity `C == A - B` before anything is reported. A violation exits; it is never repaired in place
and never dropped quietly.

USAGE
    python scripts/dcs_readout_family.py --self-test
    # `F` needs the Llama tokenizer, which is a GATED repo: point HF at the local cache first,
    # or the load 401s. No weights are fetched; this is the tokenizer only.
    export HF_HOME=$HOME/.cache/huggingface HF_HUB_OFFLINE=1
    python scripts/dcs_readout_family.py --family all
    python scripts/dcs_readout_family.py --family inst --out /path/to/dir
    # no tokenizer reachable at all -> A..E only, with F stamped DECODE UNAVAILABLE:
    python scripts/dcs_readout_family.py --family kladder --no-decode

⛔ Nothing is written unless `--out DIR` is given; the default is print-only.
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import math
import os
import statistics as st
import sys
from decimal import Decimal, getcontext

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
SB_ROOT = os.path.join(ROOT, "outputs", "boombness", "score_behavior")
BANK_DIR = os.path.join(ROOT, "data", "boombness_prompts")

SCHEMA = "DCS_READOUT_FAMILY/1"

# §1.5 / R-050: below this the two options are a minority of the answer distribution and the
# mass-invariant members of the family (C, D) are contrasting options the model largely rejects.
DEGRADED_OPTION_MASS = 0.05   # C-059/C-064 H1: the plan fixes this at 0.05 (§18.3, §40.4).
#: 0.30 was an unpreregistered bar 6x too high; it mislabelled PR-037 K=9 (0.105) as degraded.

# The eleven fields `score_behavior.py` writes that this instrument depends on. Verified per row.
REQUIRED_FIELDS = (
    "logp_concept", "logp_codeword", "p_concept", "p_codeword", "option_mass",
    "semantic_logodds", "semantic_margin_p_diff", "top1_id", "readout",
    "n_variants_concept", "n_variants_codeword",
)
GROUPING_FIELDS = ("condition", "domain", "cell", "query_kind")

# Tolerances for the identities that must hold if the rows mean what their names say.
TOL_LOGODDS = 1e-6      # C == A - B  (exact in practice: both are float64 of the same subtraction)
TOL_MASS = 1e-5         # E == exp(A) + exp(B)

ARM_FAMILIES = {
    # R-078 / PR-034 -- the forced-choice installation gate, one arm per concept bank.
    "inst": ["inst_button_bomb", "inst_button_knife", "inst_button_gun", "inst_button_club"],
    # PR-032 / R-079..R-081 -- the K ladder (new rungs, inherited rungs, and the K=8 re-run anchor).
    "kladder": [f"dcsk{k}_C_{s}" for k in ("1", "2", "3", "4", "5", "6", "7", "8", "8r", "16")
                for s in ("demo", "ctrl")],
    # PR-037 / R-082..R-083 -- the semantic_one_word ladder.
    "pr037": [f"dcssow_{t}_{s}" for t in ("base", "ref", "ko1", "k5", "k6", "k9", "k10")
              for s in ("demo", "ctrl")],
}


# --------------------------------------------------------------------------------------------
# D -- the normalised two-option probability, and the only place it is ever computed
# --------------------------------------------------------------------------------------------
def concept_binary_prob(logp_concept: float, logp_codeword: float) -> float:
    """D = exp(A) / (exp(A) + exp(B)), computed as the logistic of (A - B).

    ⛔ NOT `P(bomb)`. This is P(answer is the concept | answer is one of the two scored options).
    It is blind to `option_mass` by construction, which is exactly why `option_mass` is reported
    beside it everywhere.

    The algebraically identical naive form `exp(A)/(exp(A)+exp(B))` is 0/0 = NaN whenever both
    log-probabilities underflow -- and they do: `inst_button_bomb` carries rows at
    `logp_concept = -13.87` and this phase has readouts down near 1e-5, with `benign_literal`
    populations lower still. The logistic form is exact for every finite input, so the family
    never reports a NaN where the ratio is perfectly well defined.
    """
    d = logp_concept - logp_codeword
    if d >= 0.0:
        return 1.0 / (1.0 + math.exp(-d))
    e = math.exp(d)
    return e / (1.0 + e)


def _dist(vals):
    """Distribution, not a mean alone (§6.4: 'Distributions, not means alone')."""
    s = sorted(vals)
    n = len(s)
    if n == 0:
        return None
    return {
        "n": n,
        "median": float(st.median(s)),
        "mean": float(st.fmean(s)),
        "p10": float(s[max(0, int(round(0.10 * (n - 1))))]),
        "p90": float(s[min(n - 1, int(round(0.90 * (n - 1))))]),
        "min": float(s[0]),
        "max": float(s[-1]),
    }


# --------------------------------------------------------------------------------------------
# F -- decoded top-1 and its semantic category
# --------------------------------------------------------------------------------------------
def build_categoriser(concept: str, codeword: str):
    """Category test built from the SAME variant construction that built A and B.

    A single decoded token can be the whole answer (' Bomb') or only its first subtoken (' Car' for
    'Carrot'), so a prefix of a variant counts. ⛔ A token that prefixes BOTH options -- ' b'
    prefixes ' bomb' and ' button' -- is reported as `ambiguous`, never assigned to one of them.
    """
    sys.path.insert(0, os.path.join(ROOT, "src", "boombness"))
    sys.path.insert(0, os.path.join(ROOT, "src"))
    from signals import answer_variants  # noqa: E402  -- reuse, not a second construction

    # The scored variants are the leading-space forms (`spaced=True`), because that is what the
    # readout scored. A decoded token may carry the space or not depending on where it sits, so
    # both sides are compared with leading whitespace stripped and case folded -- the variant list
    # is still the one `answer_variants` built, not a second construction.
    vc = [v.strip().lower() for v in answer_variants(concept, True)]
    vw = [v.strip().lower() for v in answer_variants(codeword, True)]

    def hit(tok_text: str, variants) -> str:
        t = tok_text.strip().lower()
        if not t:
            return ""
        if any(t == v for v in variants):
            return "exact"
        if any(v.startswith(t) for v in variants):
            return "prefix"
        return ""

    def categorise(tok_text: str) -> str:
        c, w = hit(tok_text, vc), hit(tok_text, vw)
        if c and w:
            return "ambiguous"
        if c:
            return "concept" if c == "exact" else "concept_prefix"
        if w:
            return "codeword" if w == "exact" else "codeword_prefix"
        if tok_text.strip().lower() in ("neither", "none"):
            return "neither"
        return "other"

    return categorise


def load_tokenizer(model: str):
    """Tokenizer only -- no weights, no GPU. Fails loudly rather than skipping `F` in silence."""
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(model)


# --------------------------------------------------------------------------------------------
# arm discovery / bank identity
# --------------------------------------------------------------------------------------------
def _import_kladder():
    """Reuse `find_arm` (C-051 completeness rule) and `load_arm` rather than re-deriving them."""
    sys.path.insert(0, SCRIPTS)
    import dcs_kladder_analysis as kl  # noqa: E402
    return kl


def bank_identity(run_dir: str):
    """(concept, codeword, bank_basename) for a run, read from its own config and its own bank."""
    cfg = json.load(open(os.path.join(run_dir, "config.json")))
    bank = cfg["args"]["bank"]
    base = os.path.basename(bank)
    if not os.path.exists(bank):
        alt = os.path.join(BANK_DIR, base)
        if not os.path.exists(alt):
            sys.exit(f"REFUSING {os.path.basename(run_dir)}: bank not found ({bank}); the concept "
                     f"and codeword cannot be established, so category `F` is undefined")
        bank = alt
    with open(bank) as fh:
        for i, line in enumerate(fh):
            r = json.loads(line)
            if isinstance(r, dict) and r.get("concept") and r.get("codeword"):
                return str(r["concept"]), str(r["codeword"]), base
            if i > 2000:
                break
    sys.exit(f"REFUSING {os.path.basename(run_dir)}: no row in {base} carries `concept`/`codeword`")


def verify_rows(rows, arm: str) -> dict:
    """The verification the task demanded be done rather than assumed. Exits on any violation."""
    if not rows:
        sys.exit(f"REFUSING {arm}: zero rows")
    for i, r in enumerate(rows):
        miss = [f for f in REQUIRED_FIELDS if f not in r]
        if miss:
            sys.exit(f"REFUSING {arm}: row {i} lacks {miss}. This instrument reports a family it "
                     f"cannot compute without them; it does not substitute defaults.")
    d_lo = max(abs(r["semantic_logodds"] - (r["logp_concept"] - r["logp_codeword"])) for r in rows)
    if d_lo > TOL_LOGODDS:
        sys.exit(f"REFUSING {arm}: semantic_logodds != logp_concept - logp_codeword "
                 f"(max |diff| = {d_lo:.3e} > {TOL_LOGODDS:.0e}). C is not A - B on this arm, so "
                 f"the family is not the family it claims to be.")
    d_m = max(abs(r["option_mass"] - (math.exp(r["logp_concept"]) + math.exp(r["logp_codeword"])))
              for r in rows)
    readouts = sorted({str(r["readout"]) for r in rows})
    nvar = sorted({(int(r["n_variants_concept"]), int(r["n_variants_codeword"])) for r in rows})
    asym = [p for p in nvar if p[0] != p[1]]
    return {
        "n_rows": len(rows),
        "max_abs_C_minus_AmB": float(d_lo),
        "max_abs_E_minus_expA_plus_expB": float(d_m),
        "E_equals_expA_plus_expB": bool(d_m <= TOL_MASS),
        "readout": readouts,
        "n_variants_pairs": [list(p) for p in nvar],
        "variant_count_asymmetric": [list(p) for p in asym],
        "variant_symmetry_note": (
            "equal variant counts per option is what makes A and B comparable; an asymmetric pair "
            "is recorded, never averaged over" if asym else
            "each option contributes the same number of surface variants"),
    }


# --------------------------------------------------------------------------------------------
# the family, per population
# --------------------------------------------------------------------------------------------
def family_of(rows, categorise, tok) -> dict:
    A = [r["logp_concept"] for r in rows]
    B = [r["logp_codeword"] for r in rows]
    C = [r["semantic_logodds"] for r in rows]
    D = [concept_binary_prob(r["logp_concept"], r["logp_codeword"]) for r in rows]
    E = [r["option_mass"] for r in rows]

    cats = collections.Counter()
    toks = collections.Counter()
    for r in rows:
        text = tok.decode([int(r["top1_id"])]) if tok is not None else f"<id {r['top1_id']}>"
        toks[text] += 1
        cats[categorise(text) if tok is not None else "DECODE UNAVAILABLE"] += 1
    n = len(rows)

    med_E = float(st.median(E))
    out = {
        "n": n,
        "A_logp_concept": _dist(A),
        "B_logp_codeword": _dist(B),
        "C_semantic_logodds": _dist(C),
        "D_concept_binary_prob": _dist(D),
        "E_option_mass": _dist(E),
        "F_top1_category_frac": {k: v / n for k, v in cats.most_common()},
        "F_top1_category_counts": dict(cats.most_common()),
        "F_top1_decoded_counts": dict(toks.most_common(8)),
        "option_mass_median": med_E,
        "regime": ("MEASURED IN A DEGRADED REGIME" if med_E < DEGRADED_OPTION_MASS else "ok"),
        "degraded": bool(med_E < DEGRADED_OPTION_MASS),
    }
    out["D_name_note"] = (
        "D is `concept_binary_prob` = P(answer is the concept | answer is one of the two scored "
        "options). ⛔ It is NOT P(concept) over the vocabulary. Read it against "
        f"E_option_mass (median {med_E:.3f}), which is the share of the answer distribution the "
        "two options hold between them.")
    return out


def report_arm(tag: str, run_dir: str, rows, tok) -> dict:
    concept, codeword, bank = bank_identity(run_dir)
    categorise = build_categoriser(concept, codeword) if tok is not None else (lambda t: "")
    d_name = f"{concept}_binary_prob"

    res = {
        "tag": tag,
        "run_dir": os.path.basename(run_dir),
        "bank": bank,
        "concept": concept,
        "codeword": codeword,
        "D_field_name_for_this_arm": d_name,
        "verification": verify_rows(rows, tag),
        "overall": family_of(rows, categorise, tok),
        "by_condition": {},
        "by_condition_and_domain": {},
    }
    conds = sorted({str(r.get("condition")) for r in rows})
    for c in conds:
        sub = [r for r in rows if str(r.get("condition")) == c]
        res["by_condition"][c] = family_of(sub, categorise, tok)
        res["by_condition"][c]["cells"] = sorted({str(r.get("cell")) for r in sub})
        per = {}
        for dom in sorted({str(r.get("domain")) for r in sub}):
            per[dom] = family_of([r for r in sub if str(r.get("domain")) == dom], categorise, tok)
        res["by_condition_and_domain"][c] = per
    res["degraded_populations"] = sorted(
        [f"{tag}|{c}" for c in conds if res["by_condition"][c]["degraded"]] +
        [f"{tag}|{c}|{d}" for c in conds
         for d, v in res["by_condition_and_domain"][c].items() if v["degraded"]])
    return res


# --------------------------------------------------------------------------------------------
# printing
# --------------------------------------------------------------------------------------------
def _line(label: str, f: dict, dname: str) -> str:
    a, b, c, d, e = (f["A_logp_concept"], f["B_logp_codeword"], f["C_semantic_logodds"],
                     f["D_concept_binary_prob"], f["E_option_mass"])
    flag = "  ⛔ DEGRADED" if f["degraded"] else ""
    return (f"  {label:34s} n={f['n']:4d}  "
            f"A {a['median']:+8.3f}  B {b['median']:+8.3f}  C {c['median']:+8.3f}  "
            f"{dname} {d['median']:.4f}  option_mass {e['median']:.3f}{flag}")


def print_arm(res: dict, per_domain: bool) -> None:
    dn = "D=" + res["D_field_name_for_this_arm"]
    v = res["verification"]
    print(f"\n=== {res['tag']}  ({res['run_dir']})  concept={res['concept']} "
          f"codeword={res['codeword']}  n={v['n_rows']} ===")
    print(f"    verified: C==A-B (max |diff| {v['max_abs_C_minus_AmB']:.1e}); "
          f"E==exp(A)+exp(B): {v['E_equals_expA_plus_expB']} "
          f"(max |diff| {v['max_abs_E_minus_expA_plus_expB']:.1e}); "
          f"variants {v['n_variants_pairs']}")
    print(_line("OVERALL", res["overall"], dn))
    top = res["overall"]["F_top1_decoded_counts"]
    cat = res["overall"]["F_top1_category_frac"]
    print("    F top-1 decoded: " + "  ".join(f"{k!r}x{n}" for k, n in list(top.items())[:5]))
    print("    F category frac: " + "  ".join(f"{k}={p:.3f}" for k, p in cat.items()))
    for c, f in res["by_condition"].items():
        print(_line(f"condition={c} (cell {','.join(f['cells'])})", f, dn))
        if per_domain:
            for dom, fd in res["by_condition_and_domain"][c].items():
                print(_line(f"    domain={dom}", fd, dn))


# --------------------------------------------------------------------------------------------
# self-test
# --------------------------------------------------------------------------------------------
def self_test() -> int:
    """D must be recoverable from A and B on synthetic values -- including where the naive form dies."""
    getcontext().prec = 60
    fails = []

    def ref(a, b):
        """High-precision reference for exp(a)/(exp(a)+exp(b)) -- independent of the implementation."""
        ea, eb = Decimal(a).exp(), Decimal(b).exp()
        return float(ea / (ea + eb))

    cases = [
        (-1.0, -1.0, 0.5),
        (0.0, 0.0, 0.5),
        (math.log(0.75), math.log(0.25), 0.75),
        (math.log(0.25), math.log(0.75), 0.25),
        (-0.9826540946960449, -4.631653785705566, None),   # a real inst_button_bomb cell-C row
        (-13.871758460998535, -2.8199868202209473, None),  # a real inst_button_bomb cell-A row
        (-2.0, -7.0, None), (5.0, -5.0, None), (-30.0, -1.0, None),
    ]
    for a, b, want in cases:
        got = concept_binary_prob(a, b)
        r = ref(a, b)
        if abs(got - r) > 1e-12:
            fails.append(f"D({a},{b}) = {got!r} != reference {r!r}")
        if want is not None and abs(got - want) > 1e-12:
            fails.append(f"D({a},{b}) = {got!r} != expected {want!r}")

    # D is recovered from A and B THROUGH C: D == logistic(C), C == A - B.
    for a, b, _ in cases:
        c = a - b
        if abs(concept_binary_prob(a, b) - 1.0 / (1.0 + math.exp(-c))) > 1e-12:
            fails.append(f"D != logistic(C) at A={a} B={b}")

    # The underflow case that is the whole reason the logistic form is used. Both members of the
    # naive quotient are 0.0 there, so the naive form is NaN while the ratio is exactly 0.5.
    a = b = -800.0
    if math.exp(a) != 0.0 or math.exp(b) != 0.0:
        fails.append("expected exp(-800) to underflow to 0.0; the underflow test is not testing it")
    if concept_binary_prob(a, b) != 0.5:
        fails.append(f"D(-800,-800) = {concept_binary_prob(a, b)!r}, expected exactly 0.5")
    if concept_binary_prob(-800.0, -810.0) <= 0.5:
        fails.append("D(-800,-810) should exceed 0.5")
    if not (0.0 <= concept_binary_prob(-1e4, 3.0) <= 1e-12):
        fails.append("D(-1e4, 3) should be ~0")
    if concept_binary_prob(3.0, -1e4) < 1.0 - 1e-12:
        fails.append("D(3, -1e4) should be ~1")

    # Monotone in C, and symmetric: D(a,b) + D(b,a) == 1.
    prev = -1.0
    for c in [-40, -10, -3, -1, 0, 1, 3, 10, 40]:
        d = concept_binary_prob(float(c), 0.0)
        if d < prev:
            fails.append("D is not monotone increasing in C")
        prev = d
    for a, b, _ in cases:
        if abs(concept_binary_prob(a, b) + concept_binary_prob(b, a) - 1.0) > 1e-12:
            fails.append(f"D(A,B)+D(B,A) != 1 at {a},{b}")

    # E is exp(A)+exp(B) and is INDEPENDENT of D: two rows with identical D and 1000x different E.
    for a, b in ((math.log(0.6), math.log(0.2)), (math.log(0.0006), math.log(0.0002))):
        if abs(concept_binary_prob(a, b) - 0.75) > 1e-12:
            fails.append("the mass-invariance demonstration is broken")
    if abs((0.6 + 0.2) - 1000 * (0.0006 + 0.0002)) > 1e-12:
        fails.append("the two demonstration rows do not differ 1000x in option_mass")

    # The degraded-regime rule is strict inequality at 0.30.
    for med, want in ((0.2999, True), (0.30, False), (0.264, True), (0.877, False)):
        if bool(med < DEGRADED_OPTION_MASS) != want:
            fails.append(f"degraded flag wrong at median option_mass {med}")

    # F categorisation, including the ambiguity guard.
    try:
        cat = build_categoriser("bomb", "button")
        checks = [(" bomb", "concept"), (" Bomb", "concept"), ("bomb", "concept"),
                  (" button", "codeword"), (" Button", "codeword"),
                  (" b", "ambiguous"), (" bo", "concept_prefix"), (" bu", "codeword_prefix"),
                  (" Neither", "neither"), (" The", "other"), (" ", "other")]
        for text, want_c in checks:
            got_c = cat(text)
            if got_c != want_c:
                fails.append(f"category({text!r}) = {got_c} != {want_c}")
        cat2 = build_categoriser("bomb", "carrot")
        if cat2(" Car") != "codeword_prefix":
            fails.append("first-subtoken prefix of a multi-token codeword not caught")
    except Exception as exc:  # noqa: BLE001
        fails.append(f"categoriser unavailable ({exc!r}) -- F cannot be self-tested")

    # _dist reports a distribution, not a mean alone.
    d = _dist([1.0, 2.0, 3.0, 4.0, 100.0])
    if d["median"] != 3.0 or d["n"] != 5 or d["max"] != 100.0:
        fails.append(f"_dist wrong: {d}")

    for f in fails:
        print("FAIL: " + f)
    print(f"self-test: {'PASS' if not fails else 'FAIL'} ({len(fails)} failures)")
    return 1 if fails else 0


# --------------------------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--family", action="append", default=[],
                    choices=sorted(ARM_FAMILIES) + ["all"],
                    help="which already-on-disk arm family to report (repeatable)")
    ap.add_argument("--tag", action="append", default=[],
                    help="an explicit score_behavior tag, in addition to --family")
    ap.add_argument("--root", default=SB_ROOT)
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct",
                    help="tokenizer only; no weights are loaded")
    ap.add_argument("--no-decode", action="store_true",
                    help="⛔ report A-E only. F is then stamped DECODE UNAVAILABLE rather than "
                         "silently omitted. Use only when no tokenizer is reachable.")
    ap.add_argument("--per-domain", action="store_true", default=True)
    ap.add_argument("--no-per-domain", dest="per_domain", action="store_false")
    ap.add_argument("--out", default=None,
                    help="directory for the JSON artifact; omit to print only")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.family and not a.tag:
        ap.error("nothing to report: pass --family and/or --tag")

    tags = list(a.tag)
    for fam in a.family:
        for f in (sorted(ARM_FAMILIES) if fam == "all" else [fam]):
            tags += ARM_FAMILIES[f]
    seen, ordered = set(), []
    for t in tags:
        if t not in seen:
            seen.add(t)
            ordered.append(t)

    kl = _import_kladder()
    tok = None if a.no_decode else load_tokenizer(a.model)

    out = {
        "schema": SCHEMA,
        "families": a.family,
        "model_tokenizer": a.model if tok is not None else "DECODE UNAVAILABLE (--no-decode)",
        "degraded_option_mass_threshold": DEGRADED_OPTION_MASS,
        "arms": {},
        "missing_or_incomplete": {},
        "skipped_incomplete_candidates": {},
        "degraded_populations": [],
        "NOTE_D_NAMING": (
            "D is `concept_binary_prob` (`<concept>_binary_prob` per arm) = exp(A)/(exp(A)+exp(B)) "
            "⛔ never `P(bomb)`: it is conditional on the answer being one of the two scored "
            "options, not a full-vocabulary probability. `option_mass` (E) is reported beside it "
            "in every table, per §1.5/R-050 (mass collapses 0.877 -> 0.264 with no mapping "
            "installed, and C and D cannot see that)."),
        "NOTE_SCOPE": (
            "REPORTING INSTRUMENT ONLY. No p-value, no test, no hypothesis verdict is computed "
            "here. ⛔ No bomb-vs-knife/gun/club contrast is computed: that is PR-035, which is "
            "preregistered and running. Each arm is reported on its own."),
    }

    skipped = {}
    for tag in ordered:
        d = kl.find_arm(a.root, tag, skipped)
        if d is None:
            out["missing_or_incomplete"][tag] = "NO COMPLETE RUN DIR (no DONE.json)"
            continue
        rows = kl.load_arm(d)
        if rows is None:
            out["missing_or_incomplete"][tag] = f"{os.path.basename(d)}: no results.jsonl"
            continue
        res = report_arm(tag, d, rows, tok)
        out["arms"][tag] = res
        out["degraded_populations"] += res["degraded_populations"]
        print_arm(res, a.per_domain)

    out["skipped_incomplete_candidates"] = skipped

    print("\n" + "=" * 96)
    print(f"arms reported: {len(out['arms'])}   "
          f"missing/incomplete: {len(out['missing_or_incomplete'])}")
    for t, why in sorted(out["missing_or_incomplete"].items()):
        print(f"  ⛔ {t}: {why}")
    deg = out["degraded_populations"]
    print(f"\n⛔ MEASURED IN A DEGRADED REGIME (median option_mass < {DEGRADED_OPTION_MASS}): "
          f"{len(deg)} populations")
    arm_lvl = [p for p in deg if p.count("|") == 1]
    print(f"   at arm x condition level ({len(arm_lvl)}):")
    for p in arm_lvl:
        print(f"     {p}")
    dom_lvl = collections.Counter(p.rsplit("|", 1)[0] for p in deg if p.count("|") == 2)
    print("   at arm x condition x domain level, by population:")
    for k, n in sorted(dom_lvl.items()):
        print(f"     {k}: {n} domain(s)")
    if not deg:
        print("     none")
    print("\n⛔ No p-value, no test and no hypothesis verdict is computed by this file. "
          "\n⛔ No bomb-vs-knife/gun/club contrast is computed here; that is PR-035.")

    if a.out:
        os.makedirs(a.out, exist_ok=True)
        dst = os.path.join(a.out, "dcs_readout_family.json")
        json.dump(out, open(dst, "w"), indent=2, sort_keys=True)
        print(f"\n-> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
