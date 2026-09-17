"""R6: leave-one-DOMAIN-out stability of the candidate's RANK, both splits.

S-104 made this parameterisable. It was hardcoded to basket and passed no run-dir filter, so once
S-103 re-ran the button arms at a second layer under the same tags it would have REFUSED on button
(two complete dirs per tag) -- and, worse, it silently defined its control family by globbing every
directory matching the tag, which after a layer re-run mixes layers into one family. With no
arguments it does exactly what it did before, so R6's and R7's published numbers stay reproducible.
"""
import argparse, importlib.util, json, os, sys, statistics as st
spec=importlib.util.spec_from_file_location("rd","scripts/dcs_csi_rederive_subspace.py")
rd=importlib.util.module_from_spec(spec); spec.loader.exec_module(rd)
mf=json.load(open("data/boombness_prompts/dcs_ts116_domain_split.json")); assign=mf["assign"]

def run(prefix, split, expect, controls, allow_short=3, layer=None, jobs=None):
    arms=["BASE","KO","KO_FULL","KO_AXIS"]+controls
    dirs={a:rd.run_dir("%s_%s"%(prefix,a),expect,allow_short,layer=layer,jobs=jobs) for a in arms}
    vals={a:rd.arm_values(d,split,assign) for a,d in dirs.items()}
    keys=set.intersection(*[set(v) for v in vals.values()])
    dm={a:rd.domain_means(v,keys) for a,v in vals.items()}
    doms=sorted(dm["KO"])
    def diffs(a,drop=None):
        ds=[d for d in doms if d!=drop]
        return sum(dm[a][d]-dm["KO"][d] for d in ds)/len(ds)
    full=diffs("KO_AXIS"); ranks=[]
    for drop in [None]+doms:
        c=diffs("KO_AXIS",drop)
        r=1+sum(1 for x in controls if diffs(x,drop)>=c)
        ranks.append((drop,c,r))
    base=ranks[0]
    loo=ranks[1:]
    worst=max(loo,key=lambda t:t[2])
    print("%s/%s  n_domains=%d  full cand=%+.5f rank=%d of %d"%(prefix,split,len(doms),base[1],base[2],len(controls)+1))
    print("   LOO: rank stays 1 in %d of %d drops; worst drop = %s -> rank %d (cand %+.5f)"
          %(sum(1 for t in loo if t[2]==1),len(loo),worst[0],worst[2],worst[1]))
    print("   cand range across LOO: %+.5f .. %+.5f"%(min(t[1] for t in loo),max(t[1] for t in loo)))
    return loo

import glob,re
def ctls(prefix, layer=None, jobs=None):
    """Control arm NAMES for `prefix`. A name is admitted only if it resolves to exactly one run dir
    UNDER THE SAME FILTERS the analysis will use -- otherwise a tag re-run at a second layer would
    contribute its other layer's directory to this family without anything saying so."""
    out=set()
    for d in glob.glob("outputs/boombness/score_behavior/%s_KO_*"%prefix):
        m=re.match(r"^%s_(KO_(?:RAND|SHUF)\d+)_\d{8}_\d{6}_\d+$"%re.escape(prefix),os.path.basename(d))
        if not m: continue
        try: n=sum(1 for _ in open(d+"/results.jsonl"))
        except Exception: n=0
        if n>0: out.add(m.group(1))
    keep=[]
    for name in sorted(out):
        try:
            rd.run_dir("%s_%s"%(prefix,name), EXPECT_BY_PREFIX.get(prefix,670), ALLOW_SHORT,
                       layer=layer, jobs=jobs)
        except SystemExit as e:
            print("   [ctls] EXCLUDING %s: %s"%(name, str(e).split(chr(10))[0]))
            continue
        keep.append(name)
    return keep


EXPECT_BY_PREFIX={}
ALLOW_SHORT=3

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--tag-prefix", default=None, help="omit to reproduce R6/R7's basket runs exactly")
    ap.add_argument("--split", default="train")
    ap.add_argument("--expect-n", type=int, default=670)
    ap.add_argument("--allow-short", type=int, default=3)
    ap.add_argument("--require-rescue-layer", type=int, default=None)
    ap.add_argument("--require-slurm-job", default=None)
    ap.add_argument("--exclude-controls", default="")
    a=ap.parse_args()
    jobs=[x for x in re.split(r"[ ,]+", a.require_slurm_job or "") if x] or None
    if a.tag_prefix is None:
        EXPECT_BY_PREFIX={"csi1_basket_train":670,"csi1_basket_validation":230}
        run("csi1_basket_train","train",670,ctls("csi1_basket_train"))
        print()
        cv=[c for c in ctls("csi1_basket_validation")
            if c not in ("KO_SHUF8","KO_SHUF9","KO_SHUF10","KO_SHUF11")]
        run("csi1_basket_validation","validation",230,cv)
    else:
        EXPECT_BY_PREFIX={a.tag_prefix:a.expect_n}
        ALLOW_SHORT=a.allow_short
        ex={x for x in re.split(r"[ ,]+", a.exclude_controls) if x}
        cs=[c for c in ctls(a.tag_prefix, layer=a.require_rescue_layer, jobs=jobs) if c not in ex]
        run(a.tag_prefix,a.split,a.expect_n,cs,allow_short=a.allow_short,
            layer=a.require_rescue_layer,jobs=jobs)
