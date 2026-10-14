#!/usr/bin/env python3
"""Fitting-side summary of P4 v2 (in-sample + CV): TOP8 rank among RAW and NC control families.
Uses p4v2_fit_<cw>_r<R>.json / p4v2_cv_<cw>_r<R>.json when present; otherwise parses the partial job logs
(outputs/heretic_csi/logs/p3p4_<job>.out) so a PARTIAL summary is available while jobs run. Fitting side only."""
import glob, json, os, re, sys
REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
P4 = os.path.join(REPO, "outputs/heretic_csi/p2b/prod/p4"); LOGS = os.path.join(REPO, "outputs/heretic_csi/logs")
# effective #params of a rank-r factored edit = r * (active input columns + output dim) per module (head-restricted A
# counts only the active heads' 128-column blocks, not the embedded zeros). o_proj: in 4096 / out 4096 (13 modules,
# L6-18); down_proj: in 14336 / out 4096 (13 modules).
SPEC = {"TOP8": (13, 8 * 128, 4096), "TOP8_L6_14": (9, 8 * 128, 4096), "FULLO": (13, 4096, 4096),
        "MLP": (13, 14336, 4096), "H2": (13, 128, 4096), "CELL_L10H2": (1, 128, 4096), "RH8": (13, 8 * 128, 4096)}


def n_params(key, r):
    if key == "ATTNMLP":
        return n_params("FULLO", r) + n_params("MLP", r)
    m, i, o = SPEC["RH8" if key.startswith("RH8") else key]
    return m * r * (i + o)


LINE = re.compile(r"^\[p4v2\] (\S+)\s+(\{.*\}) \((\d+)s\)$")


def from_logs(cw, r):
    for f in sorted(glob.glob(f"{LOGS}/p3p4_*.out")):
        txt = open(f).read()
        if f"--codeword {cw} --rank {r} --mode fit" not in txt:
            continue
        d = {}
        for ln in txt.splitlines():
            m = LINE.match(ln)
            if m:
                d[m.group(1)] = json.loads(m.group(2))
        return d, os.path.basename(f), "P4V2_FIT_DONE" in txt
    return {}, None, False


def main():
    out = []
    for cw in ("basket", "button"):
        for r in (1, 4):
            fj = f"{P4}/p4v2_fit_{cw}_r{r}.json"
            if os.path.exists(fj):
                diag, src, done = json.load(open(fj))["diag"], os.path.basename(fj), True
            else:
                diag, src, done = from_logs(cw, r)
            if "TOP8" not in diag:
                out.append({"cell": f"{cw} r{r}", "status": "no data yet"}); continue
            t = diag["TOP8"]["net"]
            raw = {k: v["net"] for k, v in diag.items() if k.startswith("RH8RAW_")}
            nc = {k: v["net"] for k, v in diag.items() if k.startswith("RH8NC_")}
            rawf = [v["total_fro"] for k, v in diag.items() if k.startswith("RH8RAW_")]
            row = {"cell": f"{cw} r{r}", "source": src, "complete": done, "TOP8_net": round(t, 4),
                   "TOP8_total_fro": round(diag["TOP8"]["total_fro"], 2),
                   "n_RAW": len(raw), "TOP8_rank_among_RAW": 1 + sum(x >= t for x in raw.values()),
                   "RAW_net_min_max": [round(min(raw.values()), 4), round(max(raw.values()), 4)] if raw else None,
                   "RAW_total_fro_min_max": [round(min(rawf), 2), round(max(rawf), 2)] if rawf else None,
                   "n_NC": len(nc), "TOP8_rank_among_NC": 1 + sum(x >= t for x in nc.values()),
                   "NC_net_min_max": [round(min(nc.values()), 4), round(max(nc.values()), 4)] if nc else None,
                   "NC_vs_v1_rescaled": [(k, round(diag[k]["net"], 4), round(diag[k].get("v1_style_rescaled_net", float("nan")), 4)) for k in list(nc)[:3]],
                   "TOP8_n_params": n_params("TOP8", r), "RH8_n_params_each": n_params("RH8", r),
                   "descriptive": {k: {"net": round(diag[k]["net"], 4), "total_fro": round(diag[k]["total_fro"], 2),
                                       "n_params": n_params(k, r), "gap_closure_all26": round(diag[k].get("gap_closure_all26", float("nan")), 4)}
                                   for k in ("TOP8_L6_14", "FULLO", "MLP", "ATTNMLP", "H2", "CELL_L10H2") if k in diag},
                   "caveat": "net is in-sample, on the variant's OWN modules (o_proj-only variants vs down_proj-only MLP are not on the same "
                             "module set); compare across variants only together with total_fro, n_params and gap_closure_all26."}
            cj = f"{P4}/p4v2_cv_{cw}_r{r}.json"
            if os.path.exists(cj):
                c = json.load(open(cj))
                row["CV"] = {"TOP8_heldout_net": round(c["heldout_net_mean"]["TOP8"], 4), "rank_among_RAW": c["TOP8_rank_among_RAW"],
                             "rank_among_NC": c["TOP8_rank_among_NC"], "n": c["n"]}
            else:
                row["CV"] = "not finished"
            out.append(row)
    print(json.dumps(out, indent=1))
    if len(sys.argv) > 1:
        json.dump(out, open(sys.argv[1], "w"), indent=1)


if __name__ == "__main__":
    main()
