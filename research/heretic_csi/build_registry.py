"""Build reports/heretic_csi/EXPERIMENT_REGISTRY.json from committed files (F9, interim).
Each entry is declared here (experiment metadata transcribed from the progress log S-entries) and enriched
from disk: sha256 of every listed config/artifact that exists, and the last git commit touching each config.
Re-run any time:  python research/heretic_csi/build_registry.py"""
import hashlib, json, os, subprocess, datetime

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
HERETIC_SHA = "662e4ba27ecaf8878b0938c184a78f75a9116f82"
MODEL = "meta-llama/Llama-3.1-8B-Instruct @ 0e9e39f249a16976918f6564b8830bc894c89659 (bf16, eager)"
SPLIT_FILE = "data/boombness_prompts/dcs_ts116_domain_split.json (seed 202609061; 67 train / 23 val; TEST never used)"
BANKS = {"basket": "boombness_prompt_bank_ts116m_basket_bomb.jsonl (sha16 79511d9e254571e6)",
         "button": "boombness_prompt_bank_ts116m_button_bomb.jsonl (sha16 dcd92d723f3e6d00)"}
SEED = 20260913

def sha(p):
    fp = os.path.join(REPO, p)
    if not os.path.isfile(fp):
        return None
    h = hashlib.sha256()
    with open(fp, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def last_commit(p):
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%h %cI", "--", p], cwd=REPO,
                             capture_output=True, text=True, timeout=30).stdout.strip()
        return out or None
    except Exception:
        return None

E = []
def add(id, phase, desc, split, configs, artifacts, jobs, params, status, verdict, log):
    E.append(dict(id=id, phase=phase, description=desc, split=split, configs=configs, artifacts=artifacts,
                  slurm_jobs=jobs, params=params, status=status, verdict=verdict, log_entries=log))

# P0
add("P0-PhaseA", "P0", "Heretic audit: base->modify->reset->base, dW rank, Optuna resume, readout port",
    "TRAIN (few prompts)", [], ["reports/heretic_csi/PHASE_A_heretic_audit.md",
    "reports/heretic_csi/PHASE_A_heretic_audit_job1023185_r0.json", "reports/heretic_csi/PHASE_A_heretic_audit_job1022919_r0.json"],
    ["1022919 (superseded gate-fail record)", "1023185"], {"env": "/specific/scratches/scratch/omeryosef/envs/heretic_csi"},
    "DONE", "PASS (with upstream findings: reset keeps lora_A; deployed != optimized under preserve_row_magnitudes; resume re-draws trial 0)",
    ["S-062", "S-077"])
add("P0-PhaseB", "P0", "Native last-position Heretic ARA as a control on matched TRAIN populations (target=C, source=A)",
    "TRAIN tune / VAL read once", ["configs/heretic_csi/phaseB"], ["reports/heretic_csi/phaseB/PHASEB_SUMMARY.md"],
    ["1023185", "1023251", "1023386"], {"lora_rank_chosen": 50, "layers": "6-30", "controls": 42},
    "DONE", "MEASURED control: answer-position output bias, NOT codeword-specific installation (scoped S-083)",
    ["S-077", "S-083"])
# P2a activation-space rank sweep
for cw in ("basket", "button"):
    for r, split, f, jobs, verdict, log in [
        (1, "VALIDATION", f"reports/heretic_csi/hcsi_p2a_{cw}_r1.json", ["968532" if cw == "basket" else "968534"],
         "PASS 1/57 (floor-sensitive, S-052)" if cw == "basket" else "DOES NOT PASS 14/57", ["S-049", "S-052"]),
        (16, "VALIDATION", f"reports/heretic_csi/hcsi_p2a_{cw}_r16.json", ["968533" if cw == "basket" else "968535"],
         "DOES NOT PASS 10/57", ["S-049"]),
        (4, "TRAIN-K4", f"reports/heretic_csi/hcsi_p2a_{cw}_r4_train.json", ["969085" if cw == "basket" else "969087"],
         "3/57 (descriptive)" if cw == "basket" else "PASS 1/57 (TRAIN, multiplicity)", ["S-051"]),
        (8, "TRAIN-K4", f"reports/heretic_csi/hcsi_p2a_{cw}_r8_train.json", ["969086" if cw == "basket" else "969088"],
         "4/57" if cw == "basket" else "3/57", ["S-051"]),
        (4, "VALIDATION", f"reports/heretic_csi/hcsi_p2a_{cw}_r4_validation.json", ["1022699" if cw == "basket" else "1022698"],
         "1/57 FRAGILE, descriptive" if cw == "basket" else "PASS 1/57 (prereg S051; superseded by powered S-084)",
         ["S-072", "S-073", "S-083"])]:
        add(f"P2a-{cw}-r{r}-{split}", "P2a", "activation-space PLS rank-r rescue at L18 rel-6 under KO demo_all:attn_knockout:6-14",
            split, ["configs/heretic_csi/hcsi_ranksweep_SHA256SUMS.txt"] + (["configs/heretic_csi/prereg_S051_rank4_validation.json"] if (r == 4 and split == "VALIDATION") else []),
            [f], jobs, {"bank": BANKS[cw], "controls": "46 RAND + 10 SHUF", "seed": SEED}, "DONE", verdict, log)
add("P2a-button-r4-POWERED", "P2a", "S-084 powered re-test: button r4 VAL vs 200 controls, Holm over 3 VAL looks", "VALIDATION",
    ["configs/heretic_csi/prereg_S084_button_r4_powered.json", "configs/heretic_csi/prereg_S084_button_r4_powered_AMENDMENT_1.json",
     "configs/heretic_csi/ANALYSIS_COMMANDS_S084.md"],
    ["reports/heretic_csi/P2A_BUTTON_R4_POWERED.json", "reports/heretic_csi/P2A_BUTTON_R4_POWERED_BINDING.json",
     "reports/heretic_csi/hcsi_p2a_button_r4ext_validation_analyzer.json", "reports/heretic_csi/VERIFY_S084_powered.json"],
    ["1022698", "1027577", "1032110"], {"controls": "190 RAND + 10 SHUF", "floor": 0.005, "seed": SEED},
    "DONE", "CONFIRMED: rank 1/201, p=0.004975, Holm 0.0149, beats all SHUF, LODO 23/23 (independently verified)",
    ["S-125", "S-126"])
add("P2a-contrast", "P2a", "basket-vs-button r1->r4 specificity interaction (descriptive)", "VALIDATION (already read)",
    [], ["reports/heretic_csi/P2A_BUTTON_R4_CONTRAST_v2.json", "reports/heretic_csi/P2A_BUTTON_R4_CONTRAST.json"], [],
    {}, "DONE", "v1 WITHDRAWN (row-set bug); v2 sign depends on control family => no contrast support", ["S-085", "S-097", "S-098"])
# P2b weight operator
for cw in ("basket", "button"):
    add(f"P2b-{cw}-TRAIN", "P2b", "position-aware weight operator dW=BA (o_proj+down_proj L6-18), primary r{1,4} + CWONLY secondary",
        "TRAIN-K4 (in-sample)", ["configs/heretic_csi/PREREG_P2B.json"] + [f"configs/heretic_csi/PREREG_P2B_AMENDMENT_{i}.json" for i in range(1, 8)]
        + ["configs/heretic_csi/ANALYSIS_COMMANDS_P2B.md"],
        [f"reports/heretic_csi/p2b_{cw}_primary_train.json", f"reports/heretic_csi/p2b_{cw}_neutpos_train.json",
         f"reports/heretic_csi/p2b_{cw}_meanbias_nm_train.json", f"reports/heretic_csi/p2b_{cw}_r1_deployed_train.json",
         f"reports/heretic_csi/p2b_{cw}_r4_deployed_train.json"],
        (["1023012", "1034929", "1023508", "1035278", "1036622", "1040065", "1040124"] if cw == "basket"
         else ["1023264", "1035131", "1023509", "1035278", "1036626", "1040065", "1040124"]),
        {"objective": "paired MSE, steer 0.3 (TRAIN CV)", "controls_primary": "61 RAND + 5 SHUF + 15 DER", "seed": SEED},
        "DONE", ("basket r4 PASS (in-sample, fragile); r1 fail; CWONLY pass" if cw == "basket" else "all fail"),
        ["S-135", "S-136", "S-138", "S-140"])
    add(f"P2b-{cw}-VAL", "P2b", "frozen operators on VALIDATION; outcome mapping per amendment 5", "VALIDATION",
        ["configs/heretic_csi/PREREG_P2B_VALIDATION.json", "configs/heretic_csi/ANALYSIS_COMMANDS_P2B.md"],
        [f"reports/heretic_csi/p2b_{cw}_primary_validation.json", f"reports/heretic_csi/p2b_{cw}_meanbias_nm_validation.json",
         "reports/heretic_csi/VERIFY_P2B_VAL.json"],
        (["1023578", "1023579", "1040101", "1041761"] if cw == "basket" else ["1036679", "1036680", "1040122", "1040170", "1041761"]),
        {"seed": SEED}, "DONE",
        ("outcome D: basket r4 PRIMARY PASS (marginal, LODO loses 9/23); CWONLY r1/r4 PASS (robust)" if cw == "basket"
         else "outcome D: button no specific carrier at r1/r4"), ["S-156", "S-157", "S-191"])
add("P2b-rank-curve", "P2b", "descriptive ranks {2,8,16,32,50} + primary {1,4}", "TRAIN-K4 (in-sample)",
    ["configs/heretic_csi/ANALYSIS_COMMANDS_P2B.md"],
    ["reports/heretic_csi/P2B_RANK_CURVE_TRAIN.json", "reports/heretic_csi/P2B_RANK_CURVE_TRAIN.png",
     "reports/heretic_csi/p2b_basket_descriptive_ranks_train.json", "reports/heretic_csi/p2b_button_descriptive_ranks_train.json"],
    ["1040700", "1040701", "1040759", "1040766"], {"controls": "41 RAND + 5 SHUF + 5 DER"}, "DONE",
    "DESCRIPTIVE: rank-flat rescue r1-50; sparse non-monotone pairing specificity", ["S-188"])
# P3
add("P3-SVD", "P3", "SVD / effective rank / write direction / alignment (anisotropic null)", "TRAIN factors", [],
    ["reports/heretic_csi/P3_SVD_REPORT_v2.md", "reports/heretic_csi/P3_alignment_aniso.json",
     "reports/heretic_csi/P3_svd_descriptive_v2.json", "reports/heretic_csi/P3_write_direction_v2.json"],
    ["1023746", "1023764", "1023765", "1023766"], {}, "DONE",
    "DESCRIPTIVE: shared mean-gap write direction (by construction); no alignment detectable at the null's sensitivity",
    ["S-079", "S-089", "S-097"])
add("P3-TRUNC", "P3", "top-k truncation / component removal of basket r4 operator", "VALIDATION",
    ["configs/heretic_csi/PREREG_P3_TRUNC.json", "configs/heretic_csi/PREREG_P3_TRUNC_ERRATUM.json"],
    ["reports/heretic_csi/p3_basket_r4_validation.json", "reports/heretic_csi/P3_TRUNC_READ_VOID.md",
     "reports/heretic_csi/p3_basket_r4_validation.NOT_QUOTABLE.md"], ["1041078"], {"controls": "40 per k"}, "DONE",
    "VOID (REEXP per-row tolerance failed; kept VOID)", ["S-158", "S-167", "S-176", "S-180"])
# P4
add("P4-fits", "P4", "head-restricted o_proj operators: TOP8 vs 60 RAW + 60 NC random 8-head sets (+ FULLO, MLP, ATTNMLP, H2, L10H2, TOP8_L6_14)",
    "TRAIN (fit-side)", ["configs/heretic_csi/PREREG_P4.json"] + [f"configs/heretic_csi/PREREG_P4_AMENDMENT_{i}.json" for i in range(1, 5)],
    ["reports/heretic_csi/P4V2_FIT_SUMMARY_partial.json", "reports/heretic_csi/P4V2_FIT_SUMMARY_partial2.json",
     "reports/heretic_csi/P4_HEAD_RESTRICTED_DESIGN_v2.md"],
    ["1023752", "1023754", "1023756", "1023758", "1024034", "1024035", "1024036", "1024037"], {}, "RUNNING (1 fit left)",
    "fit-side partial: TOP8 not distinctive vs random head sets", ["S-089", "S-100", "S-113"])
add("P4-eval", "P4", "head-restricted operator rescue eval (TRAIN-K4 then VAL)", "TRAIN-K4 / VALIDATION", [], [], [], {},
    "PENDING", "PENDING", [])
# P5/P6
add("P5-heldout-probe", "P5", "held-out probe quality basket vs button (C1)", "TRAIN fit -> VAL score", [],
    ["reports/heretic_csi/hcsi_p6_heldout_probe_basket.json", "reports/heretic_csi/hcsi_p6_heldout_probe_button.json"],
    ["1022696"], {}, "DONE", "C1 unsupported held-out; decodability difference CANNOT ANSWER", ["S-054", "S-065"])
add("P6-stage0-gates", "P6", "new-codeword Stage-0 (readout, L18 extraction, axisfit) + gates G1/G2/G3", "TRAIN",
    ["configs/heretic_csi/PREREG_P6.json"] + [f"configs/heretic_csi/PREREG_P6_AMENDMENT_{i}.json" for i in range(1, 7)],
    ["reports/heretic_csi/hcsi_p6_g2_lamp.json", "reports/heretic_csi/hcsi_p6_g2_kettle.json", "reports/heretic_csi/hcsi_p6_g2_pencil.json",
     "reports/heretic_csi/hcsi_p6_g2_ladder.json", "reports/heretic_csi/hcsi_p6_bank_checks.json", "reports/heretic_csi/hcsi_p6_occ_check.json",
     "reports/heretic_csi/hcsi_p6_power_iut.json"],
    ["1040103", "1040547", "1041177", "1041485", "1041401", "1041734", "1041850"], {"gpu": "l40s", "partition": "killable"},
    "RUNNING", "interim: G3 fail candle; G3 pass 14; G2 pass lamp/kettle/pencil/ladder; others pending", ["S-142", "S-146", "S-168", "S-178"])
add("P6-rescue", "P6", "DEV draw + per-codeword rescue + H6a", "VALIDATION", [], [], [], {}, "PENDING", "PENDING", [])
add("P7-design", "P7", "behavioral linking design", "VALIDATION (planned)", ["configs/heretic_csi/PREREG_P7_DRAFT.json"],
    ["reports/heretic_csi/P7_DESIGN.md"], [], {}, "DONE (design)",
    "primary pre-labelled CANNOT ANSWER / UNDERPOWERED (MDE 0.0907 vs plausible <=0.0021)", ["S-193"])

head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
for e in E:
    e["configs"] = [{"path": p, "sha256": sha(p), "last_commit": last_commit(p)} for p in e["configs"]]
    e["artifacts"] = [{"path": p, "sha256": sha(p)} for p in e["artifacts"]]
    e["heretic_sha"] = HERETIC_SHA
    e["model"] = MODEL
    e["domain_split"] = SPLIT_FILE
out = {"schema": "hcsi_registry/1", "interim": True, "built_at": datetime.datetime.now().isoformat(timespec="seconds"),
       "repo_head_at_build": head, "source_log": "external_md/HERETIC_CAUSAL_SEMANTIC_INSTALLATION_PLAN_AND_PROGRESS_20261001.md",
       "experiments": E}
p = os.path.join(REPO, "reports/heretic_csi/EXPERIMENT_REGISTRY.json")
json.dump(out, open(p, "w"), indent=1)
missing = [a["path"] for e in E for a in e["configs"] + e["artifacts"] if a["sha256"] is None]
print("wrote", p, "entries", len(E), "missing files:", missing)
