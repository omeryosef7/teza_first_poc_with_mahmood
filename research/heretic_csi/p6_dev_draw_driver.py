#!/usr/bin/env python3
"""THE ONLY way to run the P6 DEV draw (review #8 item 1; PREREG_P6_AMENDMENT_5/6).
REFUSES unless every one of the 20 UNTOUCHED codewords (p6_dev_draw.ZIPF) has a manifest with a FINAL gate decision:
  g3_status in {PASS, FAIL}; if G3 PASS: g1_status in {PASS, FAIL}; if G1 PASS: g2_status in {PASS, FAIL}.
  Any UNDECIDED / ERROR / missing manifest => refuse (nothing written).
Survivors = G3 PASS & G1 PASS & G2 PASS. Their installer strength (g1.install_strength_C_minus_A) must be a finite
number (NaN/missing => refuse). Then p6_dev_draw.draw(strength, survivors) is called ONCE and written to
configs/heretic_csi/P6_DEV_DRAW.json — REFUSES if that file already exists (the draw is never re-run). The output
records every manifest's sha256, the gate table, and the sha256 of p6_dev_draw.py and this driver.
--check: validate and print the table WITHOUT drawing or writing."""
import argparse, hashlib, json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import p6_dev_draw  # noqa: E402
REPO = os.environ.get("P6_REPO", "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood")
OUT = os.path.join(REPO, "configs/heretic_csi/P6_DEV_DRAW.json")
H = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()

ap = argparse.ArgumentParser(); ap.add_argument("--check", action="store_true"); a = ap.parse_args()
rows, problems, shas = {}, [], {}
# AMENDMENT_7: contingent replacement codewords (only if configs/heretic_csi/P6_EXTENSION.json exists) join the pool
EXT = os.path.join(REPO, "configs/heretic_csi/P6_EXTENSION.json")
ZIPF = dict(p6_dev_draw.ZIPF)
if os.path.exists(EXT):
    for r in json.load(open(EXT))["replacements"]:
        ZIPF[r["word"]] = r["zipf"]
    shas["_extension_file"] = H(EXT)
for cw in sorted(ZIPF):
    man = os.path.join(REPO, f"outputs/heretic_csi/p6/stage0_{cw}.json")
    if not os.path.exists(man):
        problems.append(f"{cw}: no manifest"); continue
    m = json.load(open(man)); shas[cw] = H(man)
    g3, g1, g2 = m.get("g3_status"), m.get("g1_status"), m.get("g2_status")
    if g3 not in ("PASS", "FAIL"):
        problems.append(f"{cw}: g3_status={g3} not final")
    elif g3 == "PASS" and g1 not in ("PASS", "FAIL"):
        problems.append(f"{cw}: g1_status={g1} not final")
    elif g3 == "PASS" and g1 == "PASS" and g2 not in ("PASS", "FAIL"):
        problems.append(f"{cw}: g2_status={g2} not final")
    surv = g3 == "PASS" and g1 == "PASS" and g2 == "PASS"
    s = (m.get("g1") or {}).get("install_strength_C_minus_A")
    if surv and not (isinstance(s, (int, float)) and math.isfinite(s)):
        problems.append(f"{cw}: survivor with missing/non-finite installer strength {s!r}")
    rows[cw] = {"g3": g3, "g1": g1, "g2": g2, "survivor": surv, "install_strength": s, "zipf": ZIPF[cw]}
print(json.dumps(rows, indent=0))
if problems:
    print("REFUSING DEV DRAW:\n  " + "\n  ".join(problems)); sys.exit(2)
surv = [c for c, r in rows.items() if r["survivor"]]
print(f"ALL FINAL: {len(surv)} survivors of 20 untouched")
if a.check:
    print("CHECK_OK (no draw written)"); sys.exit(0)
if os.path.exists(OUT):
    print(f"REFUSING: {OUT} already exists — the DEV draw is run exactly once"); sys.exit(3)
res = p6_dev_draw.draw({c: rows[c]["install_strength"] for c in surv}, surv, zipf=ZIPF)
rec = {"schema": "hcsi_p6_dev_draw/1", "draw": res, "n_survivors": len(surv), "gate_table": rows,
       "manifest_sha256": shas, "code_sha256": {"p6_dev_draw.py": H(os.path.join(os.path.dirname(__file__), "p6_dev_draw.py")),
                                                 "p6_dev_draw_driver.py": H(__file__)},
       "excluded_from_pool": {"candle": "G3_FAIL (AMENDMENT_5: no rescue arms)", "envelope": "excluded pre-GPU", "carrot": "excluded"}}
fd = os.open(OUT, os.O_WRONLY | os.O_CREAT | os.O_EXCL)  # atomic create-once
with os.fdopen(fd, "w") as f:
    json.dump(rec, f, indent=1)
print("WROTE", OUT, H(OUT)); print(json.dumps(res))
