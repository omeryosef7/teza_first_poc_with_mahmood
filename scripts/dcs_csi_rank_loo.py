"""R6: leave-one-DOMAIN-out stability of the candidate's RANK, both splits."""
import importlib.util, json, os, sys, statistics as st
spec=importlib.util.spec_from_file_location("rd","scripts/dcs_csi_rederive_subspace.py")
rd=importlib.util.module_from_spec(spec); spec.loader.exec_module(rd)
mf=json.load(open("data/boombness_prompts/dcs_ts116_domain_split.json")); assign=mf["assign"]

def run(prefix, split, expect, controls):
    arms=["BASE","KO","KO_FULL","KO_AXIS"]+controls
    dirs={a:rd.run_dir("%s_%s"%(prefix,a),expect,3) for a in arms}
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
def ctls(prefix):
    out=set()
    for d in glob.glob("outputs/boombness/score_behavior/%s_KO_*"%prefix):
        m=re.match(r"^%s_(KO_(?:RAND|SHUF)\d+)_\d{8}_\d{6}_\d+$"%re.escape(prefix),os.path.basename(d))
        if not m: continue
        try: n=sum(1 for _ in open(d+"/results.jsonl"))
        except Exception: n=0
        if n>0: out.add(m.group(1))
    return sorted(out)

run("csi1_basket_train","train",670,[c for c in ctls("csi1_basket_train")])
print()
cv=[c for c in ctls("csi1_basket_validation")]
cv=[c for c in cv if c not in ("KO_SHUF8","KO_SHUF9","KO_SHUF10","KO_SHUF11")]
run("csi1_basket_validation","validation",230,cv)
