"""Shared scalar palettes on multiple types; new own channels at each level.

Only explicitly declared searched shapes are inputs. Catalog and label oracle
strip all inherited/own markings and child descriptions, retaining flattened
base shapes. Every negative is a complete unmarked BASE extension proof. The
learner never filters its label oracle. Values of a palette are shared across
types in one declared scalar channel; absent values remain individually free.
"""
import dataclasses,gc,time
from collections import Counter
from turtle import Model,State,SYMMETRIES,UnionFind,sub,add,transform,verify_patch
from spatial import moved
from cluster_tiles import ClusterModel,ClusterState,make_type
from cluster_learning import corona,exact_keys,check_corona_positive,check_corona_failure

def plain(t):return make_type(Model(),t.identity,t.level,t.expansion)

def contact_catalog(types):
    types=tuple(plain(t) for t in types);model=ClusterModel(types);result=[]
    for a in sorted(types,key=lambda t:t.identity):
        root=ClusterState();root.place(model.placement((a.identity,0,(0,0,0))),seed=True)
        for b in sorted(types,key=lambda t:t.identity):
            keys={(b.identity,o,sub(p,transform(q,g))) for p,v in a.occupancy
                  for o,g in enumerate(SYMMETRIES) for q,w in b.occupancy}
            result.extend((a.identity,*k) for k in sorted(keys) if root.legal(model.placement(k)))
    return tuple(result)

def seeds(types,contact):
    a,b,o,tr=contact;by_name={t.identity:t for t in types}
    left=by_name[a].expansion;right=moved(by_name[b].expansion,SYMMETRIES[o],tr)
    if set(left)&set(right) or not verify_patch(Model(),left+right):raise ValueError('illegal disjoint cluster contact')
    return tuple(sorted(left+right))

class Palette:
    def __init__(self,types):
        if not types or len({t.level for t in types})!=1 or len({t.identity for t in types})!=len(types):raise ValueError('one level and distinct identities required')
        self.types={t.identity:t for t in types};self.level=types[0].level
        self.support={(t.identity,p) for t in types for p,v in t.occupancy}
        self.uf=UnionFind(self.support);self.samples=[];self.history=[];self.cache={}
    def overlaps(self,contact):
        if contact not in self.cache:
            a,b,o,tr=contact
            self.cache[contact]=tuple(((a,world),(b,p)) for p,v in self.types[b].occupancy
                 if (a,(world:=add(transform(p,SYMMETRIES[o]),tr))) in self.support)
        return self.cache[contact]
    def add(self,sample):
        contact=sample['contact'];self.samples.append(sample)
        if sample['status']=='positive':
            for a,b in self.overlaps(contact):self.uf.union(a,b)
        roots=sorted({self.uf.find(p) for p in self.support});colors={r:i for i,r in enumerate(roots)}
        # Save actual changing values after every label. These never enter the
        # unmarked oracle and can change after later positive equalities.
        self.history.append({'labels':len(self.samples),'counts':dict(Counter(s['status'] for s in self.samples)),
                             'classes':len(roots),'values':[(n,p,colors[self.uf.find((n,p))]) for n,p in sorted(self.support)]})
    def finish(self):
        selected=set()
        for sample in self.samples:
            if sample['status']=='negative':
                for a,b in self.overlaps(sample['contact']):
                    if self.uf.find(a)!=self.uf.find(b):selected.update((a,b));break
        roots=sorted({self.uf.find(p) for p in selected});colors={r:i for i,r in enumerate(roots)}
        values={p:colors[self.uf.find(p)] for p in selected}
        markings={name:{p:v for (n,p),v in values.items() if n==name} for name in self.types}
        def accepts(s):return all(values[a]==values[b] for a,b in self.overlaps(s['contact']) if a in values and b in values)
        return markings,{'level':self.level,'channel':f'cluster:{self.level}','support':len(self.support),'assigned':len(values),
                         'free':len(self.support)-len(values),'colors':len(roots),'counts':dict(Counter(s['status'] for s in self.samples)),
                         'positive_accepted':sum(accepts(s) for s in self.samples if s['status']=='positive'),
                         'negative_rejected':sum(not accepts(s) for s in self.samples if s['status']=='negative'),
                         'unresolved_rejected':sum(not accepts(s) for s in self.samples if s['status']=='unresolved'),
                         'method':'online tagged-type positive unions, negative inequality alternatives, sparse scalar witnesses'}

def decorate(t,marking):
    return make_type(Model(),t.identity,t.level,t.expansion,inherited=t.marks,own_marking=marking,children=t.children)

def disagreements(types,markings):
    """Literal support/value scan independent of catalog membership or graph."""
    base=Model();result=set()
    for a in types:
        for b in types:
            ma,mb=markings[a.identity],markings[b.identity]
            for o,g in enumerate(SYMMETRIES):
                translations={sub(p,transform(q,g)) for p in ma for q in mb}
                for tr in translations:
                    right=moved(b.expansion,g,tr)
                    if set(a.expansion)&set(right) or not verify_patch(base,a.expansion+right):continue
                    if any((world:=add(transform(p,g),tr)) in ma and ma[world]!=v for p,v in mb.items()):
                        result.add((a.identity,b.identity,o,tr))
    return result

def learn(types,identity,node_limit=2000,seconds=3,retry_nodes=20000,retry_seconds=20):
    start=time.monotonic();catalog=contact_catalog(types);encoder=Palette(types);samples=[];base=Model();catalog_seconds=time.monotonic()-start
    for i,contact in enumerate(catalog):
        if i and i%70==0:base=Model();gc.collect()
        fixed=seeds(types,contact);r=corona(base,fixed,node_limit,seconds)
        if r['status']=='unresolved':
            prior=r;r=corona(base,fixed,retry_nodes,retry_seconds);r['prior_attempt']=prior
        r['contact']=contact;samples.append(r);encoder.add(r)
        if (i+1)%100==0 or i+1==len(catalog):print(identity,'labels',i+1,'/',len(catalog),dict(Counter(s['status'] for s in samples)),flush=True)
    markings,stats=encoder.finish();label_seconds=time.monotonic()-start
    # Check exclusions independently before activating any newly marked type.
    audit_start=time.monotonic();negative_nodes=positive=0
    for i,s in enumerate(samples):
        fixed=seeds(types,s['contact'])
        if s['status']=='negative':
            ok,n=check_corona_failure(Model(),fixed,s['certificate'])
            if not ok:raise ValueError('independent base failure rejected')
            negative_nodes+=n
        elif s['status']=='positive':
            if not check_corona_positive(Model(),fixed,s['witness']):raise ValueError('independent positive rejected')
            positive+=1
        if (i+1)%100==0:print(identity,'audit',i+1,'/',len(samples),'nodes',negative_nodes,flush=True)
    rejected=disagreements(types,markings);by_key={s['contact']:s for s in samples}
    if not rejected<=by_key.keys() or any(by_key[k]['status']!='negative' for k in rejected):raise ValueError('uncertified marking exclusion')
    counts=stats['counts'];gate=(not counts.get('unresolved',0) and stats['positive_accepted']==counts.get('positive',0)
                               and (not counts.get('negative',0) or stats['negative_rejected']>counts['negative']/2))
    return {'id':identity,'prototypes':[dataclasses.asdict(t) for t in types],
            'catalog_count':len(catalog),'samples':samples,'history':encoder.history,
            'markings':{n:sorted(v.items()) for n,v in markings.items()},'statistics':stats,
            'disagreements':sorted(rejected),'activation_gate_passed':gate,
            'catalog_seconds':catalog_seconds,'label_and_synthesis_seconds':label_seconds,
            'independent_audit':{'positive':positive,'negative_nodes':negative_nodes,'exclusions':len(rejected),
                                 'seconds':time.monotonic()-audit_start},'seconds':time.monotonic()-start,
            'conditional_scope':'disjoint occurrences of these shapes in a complete unmarked base point tiling satisfy the shared scalar channel; finite groupings can be restricted; plane existence not asserted'}

def unpack_markings(stage):return {n:{tuple(p):v for p,v in rows} for n,rows in stage['markings'].items()}
