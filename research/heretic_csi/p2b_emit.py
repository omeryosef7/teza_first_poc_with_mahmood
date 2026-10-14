#!/usr/bin/env python3
"""Emit a p2b_runner argv-file (one `<OPSPEC>\\t<score_behavior command>` line per arm).

The score_behavior flags are BYTE-IDENTICAL to research/heretic_csi/slurm/rescue_sweep.slurm (the
validated P2a recipe): COMMON + KO (+ RESC for KO_FULL). Only the OPSPEC column is new.

Arm families (--what):
  capture   BASE (clean=TARGET) and KO (SOURCE) with capture hooks -> <capdir>/cap_<cw>_{BASE,KO}.pt
  liveness  BASE, KO, KO_FULL (whole-state rescue, layer 18, query positions), KO_IDENT (zero operator)
  rank      per rank r: KO_CAND_r, BASE_CAND_r (preservation), KO_CWONLY_r / KO_ATLAST_r (CAND applied only
            at the codeword / last row), KO_NEUT_r (last-row fit, own norm), [KO_CAPOP_r: CAND + capture of
            the deployed module I/O], KO_SHUF_r_j, KO_DER_r_j, KO_RAND_r_i (RAND seeds 7000+100r+i)
"""
import argparse, os

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"


def common(cw, snap, excl, limit):
    lim = f" --limit {limit}" if int(limit) else ""
    return (f"--bank data/boombness_prompts/boombness_prompt_bank_ts116m_{cw}_bomb.jsonl --model {snap} "
            f"--query-kinds semantic_one_word --conditions natural_doublespeak --n-examples 4 "
            f"--readout-ids whole_answer --readout-max-batch 1 --exclude-prompt-ids {excl}{lim} "
            f"--min-option-mass 0.05 --seed 20260913 --dtype bfloat16 --attn-impl eager")


KO = "--intervene demo_all:attn_knockout:6-14:1.0 --knockout-scope target_surface_row_only"
RESC = "--rescue-positions query --rescue-layer 18"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cw", required=True)
    ap.add_argument("--snap", required=True)
    ap.add_argument("--excl", required=True)
    ap.add_argument("--limit", default="0")
    ap.add_argument("--prefix", required=True, help="tag prefix, e.g. hcsi_p2b_basket_k4")
    ap.add_argument("--what", required=True, choices=("capture", "liveness", "rank", "addon", "addon_nm"))
    ap.add_argument("--capdir", default=None)
    ap.add_argument("--factors-dir", default=None)
    ap.add_argument("--ranks", default="")
    ap.add_argument("--nrand", type=int, default=46)
    ap.add_argument("--nshuf", type=int, default=5)
    ap.add_argument("--nder", type=int, default=5)
    ap.add_argument("--cw-nrand", type=int, default=0, help="codeword-row-only RAND controls (for KO_CWONLY)")
    ap.add_argument("--cw-nder", type=int, default=0, help="codeword-row-only DER controls (for KO_CWONLY)")
    ap.add_argument("--capop", action="store_true", help="add the deployed-I/O capture arm (needs --capdir)")
    ap.add_argument("--no-base-cand", action="store_true")
    ap.add_argument("--meanbias", default=None, help="addon: meanbias_<cw>.pt from p2b_meanbias.py")
    ap.add_argument("--n-extra", type=int, default=6, help="extra clean PRESERVE rows captured per prompt (BASE only)")
    a = ap.parse_args()
    C = common(a.cw, a.snap, a.excl, a.limit)
    sb = "python src/boombness/score_behavior.py"
    out = []

    def emit(spec, flags, arm):
        out.append(f"{spec}\t{sb} {flags} --arm {arm} --tag {a.prefix}_{arm}")

    if a.what == "capture":
        emit(f"capture:{a.capdir}/cap_{a.cw}_BASE.pt:{a.cw}:{a.n_extra}", C, "BASE")
        emit(f"capture:{a.capdir}/cap_{a.cw}_KO.pt:{a.cw}", f"{C} {KO}", "KO")
    elif a.what == "liveness":
        fp = os.path.join(a.factors_dir, f"factors_{a.cw}_r1.pt")
        emit("none", C, "BASE")
        emit("none", f"{C} {KO}", "KO")
        emit("none", f"{C} {KO} {RESC} --rescue-donor clean", "KO_FULL")
        emit(f"ident:{fp}:CAND", f"{C} {KO}", "KO_IDENT")
    elif a.what == "addon":
        # PREREG AMENDMENT 3 (DESCRIPTIVE comparators): input-independent mean-gap bias (all rows / codeword row /
        # on the clean prompt) + DER/SHUF fitted controls at their RAW fitted norm, per primary rank.
        if not (a.meanbias and os.path.exists(a.meanbias)):
            raise SystemExit("addon needs --meanbias <existing file>")
        emit(f"bias:{a.meanbias}:all", f"{C} {KO}", "KO_MEANBIAS")
        emit(f"bias:{a.meanbias}:cw", f"{C} {KO}", "KO_CWMEANBIAS")
        emit(f"bias:{a.meanbias}:all", C, "BASE_MEANBIAS")
        for r in [int(x) for x in a.ranks.split(",") if x]:
            fp = os.path.join(a.factors_dir, f"factors_{a.cw}_r{r}.pt")
            for j in range(a.nder):
                emit(f"opraw:{fp}:DER{j}", f"{C} {KO}", f"KO_DERRAW_r{r}_{j}")
            for j in range(a.nshuf):
                emit(f"opraw:{fp}:SHUF{j}", f"{C} {KO}", f"KO_SHUFRAW_r{r}_{j}")
            # AMENDMENT 7 (DESCRIPTIVE): where does NEUT (last-row fit) act? its frozen factors at one row only
            emit(f"opat:{fp}:NEUT:cw", f"{C} {KO}", f"KO_NEUT_CWONLY_r{r}")
            emit(f"opat:{fp}:NEUT:last", f"{C} {KO}", f"KO_NEUT_ATLAST_r{r}")
    elif a.what == "addon_nm":
        # AMENDMENT 6 (DESCRIPTIVE): norm-matched mean-gap bias at all rows, per primary rank (CAND norms differ by rank)
        for r in [int(x) for x in a.ranks.split(",") if x]:
            mb = os.path.join(a.factors_dir, f"meanbias_nm_{a.cw}_r{r}.pt")
            if not os.path.exists(mb):
                raise SystemExit(f"missing {mb}")
            emit(f"bias:{mb}:all", f"{C} {KO}", f"KO_MEANBIAS_NM_r{r}")
            emit(f"bias:{mb}:all", C, f"BASE_MEANBIAS_NM_r{r}")
    else:
        for r in [int(x) for x in a.ranks.split(",") if x]:
            fp = os.path.join(a.factors_dir, f"factors_{a.cw}_r{r}.pt")
            if not os.path.exists(fp):
                raise SystemExit(f"missing {fp}")
            emit(f"op:{fp}:CAND", f"{C} {KO}", f"KO_CAND_r{r}")
            if not a.no_base_cand:
                emit(f"op:{fp}:CAND", C, f"BASE_CAND_r{r}")
            emit(f"opat:{fp}:CAND:cw", f"{C} {KO}", f"KO_CWONLY_r{r}")      # CAND only at the codeword row
            emit(f"opat:{fp}:CAND:last", f"{C} {KO}", f"KO_ATLAST_r{r}")    # CAND only at the last row (norm-matched position ctrl)
            emit(f"op:{fp}:NEUT", f"{C} {KO}", f"KO_NEUT_r{r}")            # fit at the last row, own norm (descriptive)
            if a.capop:
                emit(f"capop:{a.capdir}/capop_{a.cw}_r{r}.pt:{a.cw}:{fp}:CAND", f"{C} {KO}", f"KO_CAPOP_r{r}")
            for j in range(a.nshuf):
                emit(f"op:{fp}:SHUF{j}", f"{C} {KO}", f"KO_SHUF_r{r}_{j}")
            for j in range(a.nder):
                emit(f"op:{fp}:DER{j}", f"{C} {KO}", f"KO_DER_r{r}_{j}")
            for i in range(a.nrand):
                emit(f"rand:{fp}:CAND:{7000 + 100 * r + i}", f"{C} {KO}", f"KO_RAND_r{r}_{i}")
            # OPTIONAL codeword-row-only control family for KO_CWONLY (same seeds/fits, applied ONLY at the row)
            for i in range(a.cw_nrand):
                emit(f"randat:{fp}:CAND:{7000 + 100 * r + i}:cw", f"{C} {KO}", f"KO_CWRAND_r{r}_{i}")
            for j in range(a.cw_nder):
                emit(f"opat:{fp}:DER{j}:cw", f"{C} {KO}", f"KO_CWDER_r{r}_{j}")
    print("\n".join(out))


if __name__ == "__main__":
    main()
