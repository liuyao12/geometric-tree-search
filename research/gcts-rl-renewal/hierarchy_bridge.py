"""Marking-guided finite case proofs and descending cluster refinement.

Reuse the preceding declared shapes/palettes explicitly. The plane conclusion
below uses independently checked unmarked base failures, not marked exhaustion
alone. The logical/Wang envelope reasons over externally validated geometry
lemmas; it is not a serialized unbounded geometry or first-order checker.
"""
import dataclasses,json,time
from collections import defaultdict
from pathlib import Path
from turtle import Model,Graph,SYMMETRIES,compose,transform,sub
from spatial import canonical,moved
from cluster_tiles import make_type,ClusterModel,compose_type,verify_state
from coarse_continuation import RootModel,LiteralOracle,root_state
from cluster_learning import check_corona_failure,check_corona_positive,exact_keys
import logic
from kernel_machine import Catalog

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
PARENT='local-parent-5'
def normal(v):return json.loads(json.dumps(v))
def definitions(d,lane):
    return tuple(make_type(Model(),t['identity'],t['level'],t['expansion'],
        inherited=tuple(((tuple(p),ch),v) for (p,ch),v in t['marks']),
        children=tuple((n,o,tuple(tr)) for n,o,tr in t['children'])) for t in d['inventories'][lane])

def next_family(defs,stage):
    model=ClusterModel(defs);by_shape=defaultdict(list)
    for i,s in enumerate(stage['samples']):
        if s['status']!='positive':continue
        a,b,o,tr=s['contact'];keys=((a,0,(0,0,0)),(b,o,tuple(tr)))
        t=compose_type(model,'candidate',keys);by_shape[canonical(t.expansion)].append((i,keys))
    parents=[];provenance=[]
    for j,shape in enumerate(sorted(by_shape)):
        i,keys=min(by_shape[shape]);t=compose_type(model,'candidate',keys)
        for g in SYMMETRIES:
            expansion=moved(t.expansion,g);origin=min(tr for o,tr in expansion)
            if tuple(sorted((o,sub(tr,origin)) for o,tr in expansion))==shape:break
        child_keys=tuple((n,SYMMETRIES.index(compose(g,SYMMETRIES[o])),sub(transform(tr,g),origin)) for n,o,tr in keys)
        t=compose_type(model,'ten-parent-'+str(j),child_keys)
        if t.expansion!=shape or len(t.expansion)!=10:raise ValueError('invalid promoted expansion')
        parents.append(t);provenance.append({'type':t.identity,'samples':[k for k,_ in by_shape[shape]],
            'children':child_keys,'normalization':[SYMMETRIES.index(g),tuple(-x for x in origin)]})
    return tuple(parents),provenance

def point_lemma(free,marked,stage):
    start=time.monotonic();s=root_state(marked,PARENT);model=RootModel(marked,(PARENT,),s);graph=Graph(model,s)
    kind,p,_=graph.decision(s)
    if kind!='dead':raise ValueError('no marked root leaf to guide a case proof')
    raw=root_state(free,PARENT);keys=tuple(sorted(LiteralOracle(free,(PARENT,)).domain(raw,p)))
    if not keys or raw.totals[p]>=12:raise ValueError('a nonempty capacity-legal case cover is required')
    indexed={(r['contact'][2],tuple(r['contact'][3])):(i,r) for i,r in enumerate(stage['samples'])}
    cases=[];proof_nodes=0
    for k in keys:
        i,r=indexed[k[1],k[2]];fixed=tuple(sorted(raw.owned_base|set(model.placement(k).expansion)))
        if r['status']!='negative' or fixed!=exact_keys(r['seed_expansion']):raise ValueError('case has no matching unmarked base failure')
        ok,n=check_corona_failure(Model(),fixed,r['certificate'])
        if not ok:raise ValueError('base case certificate rejected')
        c=model.placement(k);disputes=[(q,s.marks[q],v) for q,v in c.marks if q in s.marks and s.marks[q]!=v]
        if not disputes:raise ValueError('case was not eliminated by the declared values')
        cases.append({'placement':k,'source_sample':i,'base_failure_nodes':n,'disagreements':disputes});proof_nodes+=n
    return {'root':PARENT,'point':p,'root_units':raw.totals[p],'capacity':12,'active_types':(PARENT,),
        'cases':cases,'base_failure_nodes':proof_nodes,'marked_root_certificate':{'dead':p},
        'root_graph':{'frontier':len(graph.domains),'candidates':len(graph.edges),'incidences':sum(map(len,graph.domains.values()))},
        'seconds':time.monotonic()-start,
        'lifting':'A complete unmarked parent-only point tiling normalizes a used parent to this root. Its partial point needs a distinct further parent from this complete finite domain. Every such pair has an exhausted unmarked base-corona tree, contradicting complete base coverage.',
        'scope':'no complete point tiling by this one five-turtle prototype and all twelve transforms; no base turtle non-tiling or finite-region impossibility'}

def search(defs,active,root,node_limit=4000,seconds=15):
    start=time.monotonic();s=root_state(defs,root);required=frozenset(s.totals)
    model=RootModel(defs,active,s);graph=Graph(model,s);construction=time.monotonic()-start
    count=branches=forced=backs=attempts=0;found=None;best=s.copy();best_path=();peaks=[0,0,0]
    class Budget(Exception):pass
    def visit(state,g,path):
        nonlocal count,branches,forced,backs,attempts,found,best,best_path
        count+=1
        if count>node_limit or time.monotonic()-start>seconds:raise Budget()
        for i,v in enumerate((len(g.domains),len(g.edges),sum(map(len,g.domains.values())))):peaks[i]=max(peaks[i],v)
        kind,p,keys=g.decision(state)
        if kind=='dead':return {'dead':p}
        covered=sum(state.totals.get(p,0)==12 for p in required)
        if covered>sum(best.totals.get(p,0)==12 for p in required):best=state.copy();best_path=path
        if covered==len(required):found=state.copy();best_path=path;return None
        if kind=='empty':raise AssertionError('missing root obligation')
        if kind=='forced':forced+=1
        else:branches+=1
        children=[]
        for key in keys:
            c=model.placement(key);attempts+=len(c.expansion);child=state.copy();cg=g.copy()
            cg.update(model,child,child.place(c));step={'kind':kind,'point':p,'placement':key}
            proof=visit(child,cg,path+(step,))
            if found is not None:return None
            children.append({'placement':key,'proof':proof});backs+=1
        return {'kind':kind,'point':p,'children':children}
    tree=None
    try:tree=visit(s,graph,());status='positive' if found is not None else 'negative'
    except (Budget,RecursionError):status='unresolved';tree=None
    result=found or best
    if not verify_state(model,result,required if found else ()):raise ValueError('bad flattened result')
    return {'root':root,'active_types':active,'status':status,'nodes':count,'branches':branches,'forced':forced,'backtracks':backs,
        'attempted_base_placements':attempts,'seconds':time.monotonic()-start,'construction_seconds':construction,
        'required':sorted(required),'covered':sum(result.totals.get(p,0)==12 for p in required),'placements':result.order,
        'base_expansion':sorted(result.owned_base),'tile_generations':result.tile_generations,'execution':best_path,
        'certificate':tree if status=='negative' else None,'peak_frontier':peaks[0],'peak_candidates':peaks[1],'peak_incidences':peaks[2],
        'metrics':dict(model.metrics),'root_compiled_keys':len(model.initial_legal),'root_compatible_keys':sum(model.initial_legal.values()),
        'budget':{'nodes':node_limit,'seconds':seconds,'construction_included':True},
        'scope':'unbounded root-support corona, all exposed obligations checked before success; active inventory is explicit'}

def proof_catalog(distractors=3):
    """Geometry supplies checked external axioms; no proof informs the catalog."""
    pred=lambda s:('pred',s,())
    T,P,Q=map(pred,('Plane10','Plane5','CoveredRoot5'))
    refine=logic.Imp(T,P);cover=logic.Imp(P,Q);blocked=logic.Not(Q)
    nP=logic.Not(P);nT=logic.Not(T)
    a=logic.Imp(blocked,logic.Imp(cover,nP));b=logic.Imp(nP,logic.Imp(refine,nT))
    axioms={'checked_refinement':refine,'checked_complete_cover':cover,'checked_all_base_failures':blocked}
    fs=[T,P,Q,refine,cover,blocked,nP,nT,a,logic.Imp(cover,nP),b,logic.Imp(refine,nT)]
    symbols={p[1]:0 for p in (T,P,Q)}
    for i in range(distractors):
        q=pred('Unused'+str(i));symbols[q[1]]=0;axioms['unused_'+str(i)]=q;fs.append(q)
    return Catalog(logic.Kernel({},symbols,axioms),fs),{'five':nP,'ten':nT}
