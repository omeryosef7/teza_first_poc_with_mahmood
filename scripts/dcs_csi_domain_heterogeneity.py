"""Is the axis's recovery HETEROGENEOUS across domains, and is it predicted by the knockout's size?"""
import importlib.util, json, glob, os, re, statistics as st
spec=importlib.util.spec_from_file_location("rd","scripts/dcs_csi_rederive_subspace.py")
rd=importlib.util.module_from_spec(spec); spec.loader.exec_module(rd)
assign=json.load(open("data/boombness_prompts/dcs_ts116_domain_split.json"))["assign"]

def spearman(x,y):
    def rk(v):
        o=sorted(range(len(v)),key=lambda i:v[i]); r=[0]*len(v)
        for p,i in enumerate(o): r[i]=p+1
        return r
    a,b=rk(x),rk(y); n=len(x)
    ma,mb=st.mean(a),st.mean(b)
    num=sum((a[i]-ma)*(b[i]-mb) for i in range(n))
    den=(sum((a[i]-ma)**2 for i in range(n))*sum((b[i]-mb)**2 for i in range(n)))**.5
    return num/den if den else float("nan")

def go(prefix,split,expect,skip=()):
    ctl=set()
    for d in glob.glob("outputs/boombness/score_behavior/%s_KO_*"%prefix):
        m=re.match(r"^%s_(KO_(?:RAND|SHUF)\d+)_\d{8}_\d{6}_\d+$"%re.escape(prefix),os.path.basename(d))
        if m and m.group(1) not in skip:
            try:
                if sum(1 for _ in open(d+"/results.jsonl"))>0: ctl.add(m.group(1))
            except Exception: pass
    arms=["BASE","KO","KO_FULL","KO_AXIS"]+sorted(ctl)
    dirs={a:rd.run_dir("%s_%s"%(prefix,a),expect,3) for a in arms}
    vals={a:rd.arm_values(d,split,assign) for a,d in dirs.items()}
    keys=set.intersection(*[set(v) for v in vals.values()])
    dm={a:rd.domain_means(v,keys) for a,v in vals.items()}
    doms=sorted(dm["KO"])
    cand=[dm["KO_AXIS"][d]-dm["KO"][d] for d in doms]
    ko   =[dm["BASE"][d]-dm["KO"][d]     for d in doms]      # knockout magnitude
    full =[dm["KO_FULL"][d]-dm["KO"][d]  for d in doms]      # whole-state recoverability
    base =[dm["BASE"][d] for d in doms]
    ctlm =[st.mean([dm[c][d]-dm["KO"][d] for c in sorted(ctl)]) for d in doms]
    print("== %s (%d domains, %d controls)"%(split,len(doms),len(ctl)))
    print("   candidate per-domain: mean %+.5f  sd %.5f  min %+.5f  max %+.5f"
          %(st.mean(cand),st.pstdev(cand),min(cand),max(cand)))
    print("   control-mean per-domain: sd %.5f  (candidate sd / control sd = %.2f)"
          %(st.pstdev(ctlm), st.pstdev(cand)/st.pstdev(ctlm) if st.pstdev(ctlm) else float('nan')))
    print("   spearman(candidate, knockout size BASE-KO) = %+.3f"%spearman(cand,ko))
    print("   spearman(candidate, whole-state recovery)  = %+.3f"%spearman(cand,full))
    print("   spearman(candidate, BASE installation)     = %+.3f"%spearman(cand,base))
    top=sorted(zip(doms,cand),key=lambda t:-t[1])[:4]
    bot=sorted(zip(doms,cand),key=lambda t:t[1])[:3]
    print("   top:    "+", ".join("%s %+.5f"%t for t in top))
    print("   bottom: "+", ".join("%s %+.5f"%t for t in bot))
    sh=sorted(cand,reverse=True)
    print("   share of the total carried by the top domain: %.1f%%  top 5: %.1f%%"
          %(100*sh[0]/sum(cand),100*sum(sh[:5])/sum(cand)))

go("csi1_basket_train","train",670)
print()
go("csi1_basket_validation","validation",230,skip=("KO_SHUF8","KO_SHUF9","KO_SHUF10","KO_SHUF11"))
