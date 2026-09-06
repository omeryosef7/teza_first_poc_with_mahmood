"""Head-to-head: ORIGINAL vs GLOBAL-EXCLUDED permutation null, SAME data, SAME seeds.
Measures (a) FPR on pure noise (must be <= alpha) and (b) p on planted signal (power)."""
import sys, numpy as np
sys.path.insert(0,"scripts")
import dcs_bombness_specificity as M
from math import factorial

def group_permute_ORIGINAL(rows, rng, classes):
    out=[]
    for d in sorted({r["domain"] for r in rows}):
        perm=list(classes); rng.shuffle(perm); mapping=dict(zip(classes,perm))
        for r in rows:
            if r["domain"]==d:
                q=dict(r); q["perm_label"]=mapping[r.get("perm_group",r["concept"])]; out.append(q)
    return out

def perm_p(rows, layers, classes, picks, obs, n_perm, seed, gp):
    rng=np.random.default_rng(seed); null=[]
    for _ in range(n_perm):
        pr=gp(rows,rng,list(classes))
        pd=M.loo_with_picks(pr,layers,classes,lambda r:r["perm_label"],picks)
        if pd: null.append(float(np.mean(list(pd.values()))))
    null=np.array(null)
    return (1.0+float((null>=obs).sum()))/(1.0+len(null))

H,NREP,NPERM=32,100,100
doms=[f"d{i}" for i in range(6)]
layers=list(M.LAYERS_ALLOWED)
for classes in (("a","b"),("a","b","c")):
    for sep,label in ((0.0,"PURE NOISE (FPR must be <= 0.05)"),(0.8,"PLANTED SIGNAL (power)")):
        fo=fc=0; po=[];pc=[]
        for rep in range(NREP):
            rng=np.random.default_rng(5000+rep)
            rows=[]
            for d in doms:
                for ci,c in enumerate(classes):
                    for _ in range(12):
                        rows.append(dict(domain=d,concept=c,cell="C",block="b",split="s",n_examples=4,
                            family=None,codeword="x",n_chars=100,layers=layers,
                            vec=rng.normal(0,1,(len(layers),H))+sep*(np.arange(len(layers))[:,None]*0+ci)))
            lab=lambda r:r["concept"]
            obs=M.loo_domain(rows,layers,classes,lab,tag="c")
            if obs["mean_acc"] is None: continue
            a=perm_p(rows,layers,classes,obs["picks"],obs["mean_acc"],NPERM,7,group_permute_ORIGINAL)
            b=perm_p(rows,layers,classes,obs["picks"],obs["mean_acc"],NPERM,7,M.group_permute)
            po.append(a); pc.append(b)
            fo+= (a<=0.05); fc+= (b<=0.05)
        n=len(po)
        print(f"{len(classes)}-class {label}")
        print(f"   ORIGINAL  (keeps global relabels): rate={fo}/{n}={fo/n:.3f}  median p={np.median(po):.3f}  min={min(po):.4f}")
        print(f"   EXCLUDING global relabels        : rate={fc}/{n}={fc/n:.3f}  median p={np.median(pc):.3f}  min={min(pc):.4f}")
