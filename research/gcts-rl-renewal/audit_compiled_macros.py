"""Independent literal envelope compilation and saved schedule replay."""
import copy,hashlib,json,resource,time
from collections import defaultdict
from pathlib import Path
from turtle import SYMMETRIES,Graph,VERTICES
from resident_regions import Universe
from boundary_macros import singleton,problems,mine,Proposer
from compiled_macros import CompiledProposer
from run_boundary_macros import families
from run_compiled_macros import HERE,DOCS
from audit_boundary_macros import Oracle,normal
from audit_geometry import audit as geometry_audit
from region_tiles import packed_state

def sha(value):return hashlib.sha256(json.dumps(value,separators=(',',':')).encode()).hexdigest()

def literal_domains(oracle,state):
    out={p:set() for p in state.required if state.totals.get(p,0)<12}
    for key,values in oracle.values.items():
        if key in state.selected or (key[1],key[2]) in state.owned_base or any(state.totals.get(p,0)+v>12 for p,v in values):continue
        for p,v in values:
            if p in out:out[p].add(key)
    return out

class TraceGraph:
    """Observe actual reference planning without changing its point graph."""
    def __init__(self,graph,traces,trace=None):self.graph=graph;self.traces=traces;self.trace=trace
    def copy(self):
        trace=[];self.traces.append(trace)
        return TraceGraph(self.graph.copy(),self.traces,trace)
    def decision(self,state):return self.graph.decision(state)
    def update(self,model,state,changed):
        self.graph.update(model,state,changed)
        if self.trace is not None:self.trace.append(state.order[-1])

def literal_compilation(library,inventory):
    templates=set();by_orientation=defaultdict(list)
    for key in inventory:by_orientation[key[1]].append(key)
    for m in library:
        for sign,perm in SYMMETRIES:
            patch=[]
            for o,tr in m['expansion']:
                hs,hp=SYMMETRIES[o];g=sign*hs,tuple(hp[perm[j]] for j in range(3))
                patch.append((SYMMETRIES.index(g),tuple(sign*tr[i] for i in perm)))
            templates.add(tuple(sorted(patch)))
    patches=set()
    for template in sorted(templates):
        orientation,anchor=template[0]
        for name,o,tr in by_orientation[orientation]:
            delta=tuple(a-b for a,b in zip(tr,anchor))
            patch=tuple(sorted(('base',q,tuple(a+b for a,b in zip(p,delta))) for q,p in template))
            if all(k in inventory for k in patch):patches.add(patch)
    patches=tuple(sorted(patches));index=defaultdict(list)
    for i,patch in enumerate(patches):
        for k in patch:index[k].append(i)
    return {'patches':len(patches),'incidences':sum(map(len,index.values())),'indexed_base_poses':len(index),
            'templates':len(templates),'patch_sha256':sha(patches),'incidence_sha256':sha(sorted(index.items()))}

def main():
    start=time.monotonic();path=DOCS/'compiled-macros-001.json';d=json.loads(path.read_text())
    for name,s in d['sources'].items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==s
    train=problems(True);evals=problems();fs=families();declarations={b.identity:b for b in (*train,*evals,*(b for f in fs for b in f))}
    assert d['training_problems']==normal([b.packed() for b in train]);assert d['problems']==normal([b.packed() for b in evals])
    assert d['movable_families']==normal([[b.packed() for b in f] for f in fs])
    oracle=Oracle(train[0].allowed);assert len(oracle.values)==d['inventory']['placements']
    checked=complete=moves=rejected=0;patches=[]
    def replay(r,b,display=False):
        nonlocal checked,complete,moves,rejected
        assert oracle.replay(r,b);assert r['admissible_placements']==len(oracle.values)
        checked+=1;moves+=len(r['execution']);complete+=r['status']=='finite_exact_region'
        if r['execution']:
            bad=copy.deepcopy(r);bad['execution'][0]['point']=[90,-45,-45];assert not oracle.replay(bad,b);rejected+=1
        if display and r['status']=='finite_exact_region':patches.append({'lane':r.get('lane','movable')+'/'+b.identity,'seed':r['seed'],'placements':r['state']['base_expansion']})
    for r in d['donors']+d['training']['episodes']:replay(r,declarations[r['problem']])
    for r in d['evaluation']:replay(r,declarations[r['problem']],True)
    for c in d['attempt_controls']:
        for r in c['results']:replay(r,declarations[c['problem']])
        assert c['equivalent'] and all(c['results'][0][f]==c['results'][1][f] for f in c['fields'])
    for r in d['movable_evaluation']:
        family=fs[0];assert [a['boundary'] for a in r['attempts']]==[b.identity for b in family[:len(r['attempts'])]]
        for a in r['attempts']:replay(a['result'],declarations[a['boundary']],True)
        assert r['selected']==(r['attempts'][-1]['boundary'] if r['attempts'][-1]['result']['status']=='finite_exact_region' else None)
    u=Universe((singleton(),),train[0].allowed);library,info=mine(d['donors'],u.model);assert normal(library)==d['library']
    literal=literal_compilation(library,set(oracle.values))
    for k,v in literal.items():assert d['compilation'][k]==v
    # Compare the complete offered lists at actual boundary traces. Static
    # literal incidence proves the envelope representation; these are additional
    # implementation checks, not an exhaustive proof over all mutable states.
    raw=Proposer(library);compiled=CompiledProposer(library,u);pools=hits=0;examples=[];offered=dead_offers=offered_moves=0
    for b in evals:
        r=next(r for r in d['evaluation'] if r['problem']==b.identity and r['lane']=='raw' and r['replica']==0)
        for count in (0,min(3,len(r['execution'])),min(6,len(r['execution']))):
            m=u.bind(b);s=b.initial()
            for step in r['execution'][:count]:s.place(m.placement((step['placement'][0],step['placement'][1],tuple(step['placement'][2]))))
            g=Graph(m,s);kind,p,keys=g.decision(s)
            if kind!='branch':continue
            before=g.fingerprint();state=s.copy();validation_traces=[]
            expected=raw.actions(m,s,g,keys)
            assert expected==raw.actions(m,s,TraceGraph(g,validation_traces),keys)
            assert expected==compiled.actions(m,s,g,keys);assert expected==compiled.actions(m,s,g,keys)
            assert g.fingerprint()==before and s==state;pools+=1;hits+=1
            macros=[a for a in expected if len(a)>1];outcomes=[]
            for action in macros:
                child=s.copy();cg=g.copy();log=list(r['execution'][:count])
                for k in action:
                    kind,point,domain=cg.decision(child);assert k in domain
                    log.append({'kind':kind,'point':point,'placement':k,'macro_length':len(action),'macro_offset':len(log)-count})
                    cg.update(m,child,child.place(m.placement(k)))
                assert cg.domains==literal_domains(oracle,child)
                kind,point,domain=cg.decision(child);outcomes.append({'kind':kind,'point':point})
                offered+=1;dead_offers+=kind=='dead';offered_moves+=len(action)
                trial={'state':packed_state(child),'execution':log,'status':'candidate_prefix','certificate':None,
                       'accepted_base_tiles':len(child.order),'coverage_fraction':sum(child.totals.get(p,0)==12 for p in b.required)/len(b.required)}
                assert oracle.replay(trial,b)
            examples.append({'problem':b.identity,'prefix_moves':count,'scheduled_point':p,'candidate_count':len(keys),
                             'context':s.order,'macro_actions':macros,'macro_outcomes':outcomes,'validation_prefixes':validation_traces})
    assert d['training']['initial_weights']=={} and d['training']['initial_marking']=={} and not d['training']['saved_artifact_imported']
    assert d['training']['updates']==len(d['training']['episodes'])
    assert set(r['seed'] for r in d['donors']+d['training']['episodes']).isdisjoint(r['seed'] for r in d['evaluation'])
    # Equal completed reference/representation traces must have identical search
    # outcomes/counters. A wall cutoff does not imply semantic inequivalence.
    pairs=0;fields=d['attempt_controls'][0]['fields']
    for problem in (b.identity for b in evals):
        for replica in (0,1):
            for reference,variants in (('raw',('compiled','shared','cached')),('raw+RL',('cached+RL',))):
                root=next(r for r in d['evaluation'] if r['problem']==problem and r['replica']==replica and r['lane']==reference)
                for lane in variants:
                    r=next(r for r in d['evaluation'] if r['problem']==problem and r['replica']==replica and r['lane']==lane)
                    if root['status']==r['status']=='finite_exact_region':assert all(root[f]==r[f] for f in fields);pairs+=1
    geometry=geometry_audit({'point_model':{'vertices':VERTICES},'pair_catalog':{'samples':[]},'evaluation':patches})
    d['proposal_pool_examples']=examples
    d['independent_audit']={'states_replayed':checked,'complete_states':complete,'scheduled_base_moves_checked':moves,
        'literal_inventory_placements':len(oracle.values),'literal_compilation':literal,'clusters_reconstructed':len(library),
        'exact_attempt_pairs':len(d['attempt_controls']),'equal_completed_representation_pairs':pairs,
        'complete_proposal_pools_compared':pools,'cache_hits_checked':hits,'tampered_schedules_rejected':rejected,
        'offered_continuations_checked':offered,'offered_constituent_moves_checked':offered_moves,'known_dead_offers':dead_offers,
        'geometry':geometry,'seconds':time.monotonic()-start,'peak_process_memory_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'audit_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'helper_source_sha256':{n:hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('audit_boundary_macros.py','audit_geometry.py')},
        'scope':'literal complete envelope compilation, every saved base scheduler decision and target, exact matched work controls; sampled proposal-pool checks; no plane theorem or learned marking'}
    path.write_text(json.dumps(d,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in d['independent_audit'].items() if k!='geometry'},indent=2),flush=True)

if __name__=='__main__':main()
