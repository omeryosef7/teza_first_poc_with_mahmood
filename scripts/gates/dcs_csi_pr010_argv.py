"""Emit the exact argv for every PR-CSI-010 arm, DERIVED FROM THE PREREGISTRATION.

WHY GENERATED AND NOT HAND-WRITTEN. 24 arms x 2 splits is 48 command lines carrying a frozen head
list each. Hand-maintained, they are 48 chances for an arm's `--knockout-heads` to drift from the
prereg -- which is PR-CSI-010's VOID condition 5, and it would be invisible in the output because
each arm records only what it was given. Generating them means the prereg is the single source and a
drift is impossible rather than merely checked for.

--check VERIFIES EVERY EMITTED FLAG AGAINST score_behavior's REAL CLI before anything is submitted.
S-167c: `--multipos` was invented by a plan document and did not exist; it cost a submitted job to
discover. Reading argparse is cheaper than a queue slot.
"""
import argparse, ast, json, os, sys

REPO = "/home/sharifm/students/omeryosef/first_poc/teza_first_poc_with_mahmood"
SB = os.path.join(REPO, "src", "boombness", "score_behavior.py")
SNAP = ("/home/sharifm/students/matanbentov/hub/models--meta-llama--Llama-3.1-8B-Instruct/"
        "snapshots/0e9e39f249a16976918f6564b8830bc894c89659")

SPLIT = {
    "train":      {"exclude": "runargs/dcs_cont/exclude_basket_bomb_sow_train.txt", "expect_n": 670},
    "validation": {"exclude": "runargs/dcs_cont/exclude_basket_bomb_sow_validation.txt", "expect_n": 230},
}


def cli_flags(path):
    """Every option string argparse actually declares, read from the AST."""
    tree = ast.parse(open(path, encoding="utf-8").read(), path)
    out = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"):
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    out.add(arg.value)
    return out


def argv_for(arm, heads, split, prereg, seed, tag_prefix):
    sp = SPLIT[split]
    a = ["python", "src/boombness/score_behavior.py",
         "--bank", "data/boombness_prompts/boombness_prompt_bank_ts116m_basket_bomb.jsonl",
         "--model", SNAP,
         "--query-kinds", "semantic_one_word",
         "--conditions", "natural_doublespeak",
         "--n-examples", "4",
         "--exclude-prompt-ids", sp["exclude"],
         "--expect-n", str(sp["expect_n"]),
         "--readout-ids", "whole_answer",
         "--readout-max-batch", "1",
         "--answer-prefix", "Answer:",
         "--min-option-mass", "0.05",
         "--semantic-options", "bank_pair",
         "--option-mass-gate-scope", "pooled",
         "--option-mass-gate-min-dose", "1",
         "--attn-impl", "eager",
         "--dtype", "bfloat16",
         "--seed", str(seed)]
    # HD_BASE drops --intervene/--knockout-scope/--knockout-heads; HD_KO drops only the head list
    # (empty = ALL 32, score_behavior.py:3162); every other arm carries its frozen list.
    if arm != "HD_BASE":
        a += ["--intervene", prereg["intervention"]["intervene"],
              "--knockout-scope", prereg["intervention"]["knockout_scope"]]
        if heads is not None:
            a += ["--knockout-heads", ",".join(str(h) for h in heads)]
    a += ["--arm", arm, "--tag", "%s_%s_%s" % (tag_prefix, split, arm)]
    return a


def all_arms(prereg):
    """(arm, heads) in a fixed order. heads=None means 'no --knockout-heads', i.e. all 32."""
    hs = prereg["head_sets"]
    arms = [("HD_BASE", None), ("HD_KO", None),
            ("HD_TOPK", hs["HD_TOPK"]), ("HD_BOTK", hs["HD_BOTK"])]
    cprefix = prereg.get("control_prefix", "HD_RAND")
    arms += [(k, hs[k]) for k in sorted(hs) if k.startswith(cprefix)]
    return arms


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--split", choices=("train", "validation"), required=True)
    ap.add_argument("--seed", type=int, default=20260913)
    ap.add_argument("--tag-prefix", default="csi3_head_basket")
    ap.add_argument("--check", action="store_true", help="verify every flag against the real CLI")
    ap.add_argument("--emit", choices=("lines", "shell"), default="lines")
    a = ap.parse_args()

    pr = json.load(open(a.prereg))
    arms = all_arms(pr)
    if len(arms) != pr["n_arms_per_split"]:
        sys.exit("REFUSING: built %d arms but the prereg says %d" % (len(arms), pr["n_arms_per_split"]))

    if a.check:
        declared = cli_flags(SB)
        bad = []
        for arm, heads in arms:
            for tok in argv_for(arm, heads, a.split, pr, a.seed, a.tag_prefix):
                if tok.startswith("--") and tok not in declared:
                    bad.append((arm, tok))
        if bad:
            for arm, tok in bad:
                print("ABSENT FLAG  %s  in arm %s" % (tok, arm))
            sys.exit("REFUSING: %d flag(s) are not declared by score_behavior.py" % len(bad))
        # the head lists must still be the prereg's, token for token
        for arm, heads in arms:
            if heads is None:
                continue
            av = argv_for(arm, heads, a.split, pr, a.seed, a.tag_prefix)
            got = [int(x) for x in av[av.index("--knockout-heads") + 1].split(",")]
            if got != list(heads) or got != list(pr["head_sets"][arm]):
                sys.exit("REFUSING: arm %s head list drifted from the prereg" % arm)
        n_with = sum(1 for _, h in arms if h is not None)
        print("CHECK PASSED: %d arms, every flag declared by score_behavior.py; %d arms carry a "
              "frozen head list, 2 carry none (HD_BASE has no intervention, HD_KO = all 32)."
              % (len(arms), n_with))
        print("populations: %s expect-n %d, exclusions %s"
              % (a.split, SPLIT[a.split]["expect_n"], SPLIT[a.split]["exclude"]))
        return

    for arm, heads in arms:
        av = argv_for(arm, heads, a.split, pr, a.seed, a.tag_prefix)
        if a.emit == "lines":
            print(" ".join(av))
        else:
            print(" \\\n  ".join(av))
            print()


if __name__ == "__main__":
    main()
