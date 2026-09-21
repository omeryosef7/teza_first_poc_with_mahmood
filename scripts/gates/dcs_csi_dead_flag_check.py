"""Refuse any CLI flag that is declared and never read.

WHY THIS EXISTS. `dcs_csi_head_atp.py` shipped with `--topk` and `--min-corr` in its argparse and
NO reference to either in the body. Both printed in --help, both accepted on the command line, both
did exactly nothing. A flag that silently controls nothing is worse than a missing flag: a run
invoked with `--min-corr 0.7` would record that it gated at 0.7 while gating at nothing at all.
Argparse cannot catch this -- an unread attribute is not an error -- so it is checked here.
"""
import ast, sys

def dead_flags(path):
    tree = ast.parse(open(path, encoding="utf-8").read(), path)
    declared = {}          # dest -> option string
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"):
            opts = [a.value for a in node.args if isinstance(a, ast.Constant)
                    and isinstance(a.value, str)]
            dest = next((kw.value.value for kw in node.keywords
                         if kw.arg == "dest" and isinstance(kw.value, ast.Constant)), None)
            if dest is None:
                longs = [o for o in opts if o.startswith("--")]
                if not longs:
                    continue                      # positional; its name IS the dest
                dest = longs[0][2:].replace("-", "_")
            declared[dest] = opts[0] if opts else dest
    used = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    return sorted((f, d) for d, f in declared.items() if d not in used)

if __name__ == "__main__":
    bad = 0
    for path in sys.argv[1:]:
        dead = dead_flags(path)
        if dead:
            bad = 1
            print("DEAD FLAGS in %s:" % path)
            for flag, dest in dead:
                print("   %-18s (dest %r) is declared and NEVER read" % (flag, dest))
        else:
            print("OK   %s -- every declared flag is read" % path)
    sys.exit(bad)
