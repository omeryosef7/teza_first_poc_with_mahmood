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

# ⛔ S-251. THE BANK AND THE EXCLUSIONS ARE DERIVED FROM THE PREREG'S `codeword`, NOT HARD-CODED.
# Until S-251 both were constants naming BASKET. Every family so far is basket, so nothing was wrong in
# fact -- but PR-CSI-013 is a BUTTON family, and launching it through this generator would have produced
# arms carrying BASKET rows under button tags, with `--check` passing: it verified that every flag EXISTS
# and that head lists match the prereg, and never compared the BANK to the preregistration. The numbers
# would have looked entirely plausible. No VOID condition in any prereg mentioned the bank either.
# `codeword` defaults to "basket" because PR-CSI-010/011/012 predate the field (the same treatment
# `control_prefix` got in S-227) -- AND THE DEFAULT IS VERIFIED TO BIND, never assumed (S-168).
EXPECT_N = {"train": 670, "validation": 230}


def bank_for(codeword):
    return "data/boombness_prompts/boombness_prompt_bank_ts116m_%s_bomb.jsonl" % codeword


def exclude_for(codeword, split):
    return "runargs/dcs_cont/exclude_%s_bomb_sow_%s.txt" % (codeword, split)


def codeword_of(prereg):
    return prereg.get("codeword", "basket")


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


def base_arms_of(prereg):
    """The two arms that carry no frozen head list, named by the prereg. Default = PR-CSI-010's."""
    return list(prereg.get("base_arms", ["HD_BASE", "HD_KO"]))


def argv_for(arm, heads, split, prereg, seed, tag_prefix):
    cw = codeword_of(prereg)
    a = ["python", "src/boombness/score_behavior.py",
         "--bank", bank_for(cw),
         "--model", SNAP,
         "--query-kinds", "semantic_one_word",
         "--conditions", "natural_doublespeak",
         "--n-examples", "4",
         "--exclude-prompt-ids", exclude_for(cw, split),
         "--expect-n", str(EXPECT_N[split]),
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
    # ⛔⛔ S-260. THE CLEAN-REFERENCE ARM IS NAMED BY THE PREREG, NOT BY THE LITERAL "HD_BASE".
    # This line read `arm != "HD_BASE"`, so PR-CSI-013's base arm BT_BASE was given --intervene with
    # no --knockout-heads -- an ALL-32 KNOCKOUT standing in as the family's CLEAN REFERENCE. Every
    # effect in that family would have been measured against a knocked-out baseline. 918967 ran 14 of
    # 23 arms this way and is VOID.
    # S-251 generalised all_arms() to take `base_arms` from the prereg and DID NOT generalise THIS
    # FUNCTION, four lines below it: the ENUMERATION was fixed and the EMISSION was left hard-coded.
    if arm != base_arms_of(prereg)[0]:
        a += ["--intervene", prereg["intervention"]["intervene"],
              "--knockout-scope", prereg["intervention"]["knockout_scope"]]
        if heads is not None:
            a += ["--knockout-heads", ",".join(str(h) for h in heads)]
    a += ["--arm", arm, "--tag", "%s_%s_%s" % (tag_prefix, split, arm)]
    return a


def all_arms(prereg):
    """(arm, heads) in a fixed order. heads=None means 'no --knockout-heads', i.e. all 32."""
    hs = prereg["head_sets"]
    # S-251. The BASE arms are named by the prereg, defaulting to PR-CSI-010's names so the three
    # basket families emit byte-identically. Before this, both names were constants AND "HD_TOPK" /
    # "HD_BOTK" were required keys -- so a family that does not have them (PR-CSI-013's arms are
    # BT_SINGLE and BT_CTRL_*) died on a bare `KeyError: 'HD_TOPK'`. Fail-closed, but naming the
    # SYMPTOM rather than the cause, which is the defect S-246 fixed in the four rank tools.
    base = list(prereg.get("base_arms", ["HD_BASE", "HD_KO"]))
    if len(base) != 2:
        sys.exit("REFUSING: base_arms must name exactly 2 arms, got %r" % (base,))
    for b in base:                      # the default is VERIFIED to bind, never assumed (S-168)
        if b in hs:
            sys.exit("REFUSING: base arm %r also appears in head_sets -- it carries no head list" % b)
    arms = [(base[0], None), (base[1], None)]
    if "HD_TOPK" in hs and "HD_BOTK" in hs:
        arms += [("HD_TOPK", hs["HD_TOPK"]), ("HD_BOTK", hs["HD_BOTK"])]
    # S-247. A CENSUS prereg (NO_RANK_TEST) has no control_prefix, so prefix-matching would build only
    # the four arms above; the n_arms_per_split assertion below then refuses -- loudly, which is right,
    # but the generator is still the ONE place an arm's argv is defined and duplicating it for a second
    # family would duplicate the flag-verification logic with it. So enumerate EVERY remaining
    # head_sets entry instead. `control_pool` is skipped explicitly: it is a DRAW POOL, not an arm, and
    # it lives in head_sets for provenance (pr010_freeze.py:128).
    if prereg.get("NO_RANK_TEST"):
        arms += [(k, hs[k]) for k in sorted(hs)
                 if k not in ("HD_TOPK", "HD_BOTK", "control_pool")]
    else:
        cprefix = prereg.get("control_prefix", "HD_RAND")
        named = {a for a, _ in arms}
        arms += [(k, hs[k]) for k in sorted(hs) if k.startswith(cprefix)]
        # S-251: a rank family whose CANDIDATE is not HD_TOPK (PR-CSI-013's is BT_SINGLE) still needs
        # its candidate emitted. Anything in head_sets that is neither already named nor a control
        # prefix match nor the draw pool is a candidate arm and is added, sorted, after the controls.
        rest = [k for k in sorted(hs)
                if k not in named and not k.startswith(cprefix) and k != "control_pool"
                and k not in {a for a, _ in arms}]
        arms += [(k, hs[k]) for k in rest]
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
        # S-251: the BANK and the EXCLUSIONS must carry the prereg's codeword, and the files must
        # EXIST. A generator that silently emits another codeword's rows is the one error in this
        # pipeline that would produce entirely plausible numbers.
        cw = codeword_of(pr)
        bank, excl = bank_for(cw), exclude_for(cw, a.split)
        for label, path in (("bank", bank), ("exclusions", excl)):
            if cw not in os.path.basename(path):
                sys.exit("REFUSING: the %s path %r does not carry the prereg's codeword %r"
                         % (label, path, cw))
            if not os.path.exists(os.path.join(REPO, path)):
                sys.exit("REFUSING: the %s for codeword %r does not exist: %r -- absence is not a "
                         "pass (R20-6)" % (label, cw, path))
        for arm, heads in arms:
            av = argv_for(arm, heads, a.split, pr, a.seed, a.tag_prefix)
            got_bank = av[av.index("--bank") + 1]
            got_excl = av[av.index("--exclude-prompt-ids") + 1]
            if got_bank != bank or got_excl != excl:
                sys.exit("REFUSING: arm %s emits bank %r / exclusions %r, not the codeword %r's"
                         % (arm, got_bank, got_excl, cw))
        # S-260: --check PASSED on the broken argv because it only verified that flags EXIST and that
        # head lists match the prereg. It never asserted the ONE THING that makes a base arm a base
        # arm. Assert it here.
        b0 = base_arms_of(pr)[0]
        av0 = argv_for(b0, None, a.split, pr, a.seed, a.tag_prefix)
        if "--intervene" in av0 or "--knockout-scope" in av0 or "--knockout-heads" in av0:
            sys.exit("REFUSING: the clean-reference arm %r carries an intervention flag -- it would be "
                     "a knockout standing in as the baseline (S-260): %s"
                     % (b0, [t for t in av0 if t.startswith("--knock") or t == "--intervene"]))
        for arm, heads in arms:
            if arm == b0:
                continue
            av = argv_for(arm, heads, a.split, pr, a.seed, a.tag_prefix)
            if "--intervene" not in av:
                sys.exit("REFUSING: arm %r carries NO --intervene but is not the clean reference %r"
                         % (arm, b0))
        print("BASE-ARM CHECK PASSED: %r carries no intervention flag; all %d other arms carry "
              "--intervene" % (b0, len(arms) - 1))
        print("CODEWORD CHECK PASSED: %r -> bank %s, exclusions %s (both exist; every arm agrees)"
              % (cw, os.path.basename(bank), os.path.basename(excl)))
        n_with = sum(1 for _, h in arms if h is not None)
        # S-251: name the ACTUAL base arms. This line said "HD_BASE / HD_KO" unconditionally, which is
        # wrong text on any family that names them otherwise (PR-CSI-013's are BT_BASE / BT_KO).
        b0, b1 = arms[0][0], arms[1][0]
        print("CHECK PASSED: %d arms, every flag declared by score_behavior.py; %d arms carry a "
              "frozen head list, 2 carry none (%s has no intervention, %s = all 32)."
              % (len(arms), n_with, b0, b1))
        print("populations: %s expect-n %d, exclusions %s"
              % (a.split, EXPECT_N[a.split], exclude_for(codeword_of(pr), a.split)))
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
