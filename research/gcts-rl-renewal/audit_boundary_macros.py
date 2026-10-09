"""Literal singleton inventory and scheduler replay for every exported move."""
import copy,hashlib,json,resource,time
from collections import Counter
from pathlib import Path
from turtle import BASE,SYMMETRIES,VERTICES
from region_tiles import Boundary
from boundary_macros import problems,mine,singleton,Proposer
from run_boundary_macros import HERE,DOCS,families
from resident_regions import Universe
from audit_geometry import audit as geometry_audit

def normal(x):return json.loads(json.dumps(x))
def exact_key(k):
    n,o,tr=k
    if n!='base' or type(o) is not int or not 0<=o<12 or len(tr)!=3 or any(type(v) is not int for v in tr) or sum(tr):
        raise ValueError('invalid exact base pose')
    return n,o,tuple(tr)

class Oracle:
    """Compile all literal transformed positive support in the authored P.

    Does not read Universe, RegionModel, Graph, model.cache or alignments.
    Each replay domain scans this independently enumerated full inventory.
    """
    def __init__(self,allowed):
        self.values={}
        for o,(sign,perm) in enumerate(SYMMETRIES):
            entries=tuple((tuple(sign*p[i] for i in perm),v) for p,v in BASE.items())
            q,_=entries[0]
            for anchor in sorted(allowed):
                tr=tuple(a-b for a,b in zip(anchor,q));occ=tuple((tuple(a+b for a,b in zip(p,tr)),v) for p,v in entries)
                if all(p in allowed for p,v in occ):self.values['base',o,tr]=occ

    def replay(self,r,b):
        saved=r['state']
        if any(type(g) is not int or g<0 for g in saved['tile_generations']):return False
        if any(type(v) is not int or not 0<=v<=12 for p,v in saved['totals']):return False
        if type(r['accepted_base_tiles']) is not int:return False
        totals=dict(b.exterior);selected=set();owned=set(b.owned);gens={p:0 for p,v in b.exterior};gens.update({p:0 for p in b.required})
        tile_gens=[];placements=[]
        for step in r['execution']:
            key=exact_key(step['placement']);domains={p:set() for p in b.required if totals.get(p,0)<12}
            for k,occ in self.values.items():
                if k in selected or (k[1],k[2]) in owned or any(totals.get(p,0)+v>12 for p,v in occ):continue
                for p,v in occ:
                    if p in domains:domains[p].add(k)
            if not domains or any(not cs for cs in domains.values()):return False
            forced=sorted(p for p,cs in domains.items() if len(cs)==1)
            point=forced[0] if forced else min(domains,key=lambda p:(gens[p],len(domains[p]),p))
            if tuple(step['point'])!=point or step['kind']!=('forced' if forced else 'branch') or key not in domains[point]:return False
            occ=self.values[key];incident=[gens[p] for p,v in occ if p in gens];gen=1+min(incident) if incident else 0
            tile_gens.append(gen);placements.append(key);selected.add(key);owned.add((key[1],key[2]))
            for p,v in occ:totals[p]=totals.get(p,0)+v;gens[p]=min(gens.get(p,gen),gen)
        s=normal(r['state']);complete=all(totals.get(p,0)==12 for p in b.required)
        return (normal(placements)==s['placements'] and normal(tile_gens)==s['tile_generations'] and
                normal(sorted(owned))==s['base_expansion'] and normal(sorted(totals.items()))==s['totals'] and
                normal(sorted(b.marks))==s['marks'] and r['accepted_base_tiles']==len(placements) and
                r['coverage_fraction']==sum(totals.get(p,0)==12 for p in b.required)/len(b.required) and
                (r['status']!='finite_exact_region' or complete) and r['certificate'] is None)

def main():
    start=time.monotonic();path=DOCS/'boundary-macros-001.json';d=json.loads(path.read_text())
    for name,sha in d['sources'].items():assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==sha
    train=problems(True);evals=problems();fs=families();declarations={b.identity:b for b in (*train,*evals,*(b for f in fs for b in f))}
    assert d['training_problems']==normal([b.packed() for b in train])
    assert d['problems']==normal([b.packed() for b in evals])
    assert d['movable_families']==normal([[b.packed() for b in f] for f in fs])
    oracle=Oracle(train[0].allowed);assert len(oracle.values)==d['inventory']['placements']
    checked=complete=moves=rejected=0;patches=[]
    def replay(r,b,display=False):
        nonlocal checked,complete,moves,rejected
        assert r['admissible_placements']==len(oracle.values)
        assert oracle.replay(r,b),'literal scheduler or value replay failed'
        checked+=1;moves+=len(r['execution']);complete+=r['status']=='finite_exact_region'
        if r['execution']:
            bad=copy.deepcopy(r);bad['execution'][0]['point']=[90,-45,-45]
            assert not oracle.replay(bad,b);rejected+=1
        if display and r['status']=='finite_exact_region':
            patches.append({'lane':r.get('lane','movable')+'/'+b.identity,'seed':r['seed'],'placements':r['state']['base_expansion']})
    for r in d['donors']+d['training']['episodes']:replay(r,declarations[r['problem']])
    for r in d['evaluation']:replay(r,declarations[r['problem']],True)
    for r in d['movable_evaluation']:
        family=fs[r['family']];assert [a['boundary'] for a in r['attempts']]==[b.identity for b in family[:len(r['attempts'])]]
        for a in r['attempts']:replay(a['result'],declarations[a['boundary']],True)
        assert r['selected']==(r['attempts'][-1]['boundary'] if r['attempts'][-1]['result']['status']=='finite_exact_region' else None)
    # Rebuild the mined shapes solely from the new training trajectories.
    u=Universe((singleton(),),train[0].allowed);library,info=mine(d['donors'],u.model)
    assert normal(library)==d['library']
    for field in ('connected_windows','distinct_shapes','selected','sizes','selection'):assert normal(info[field])==d['mining'][field]
    assert d['training']['initial_weights']=={} and d['training']['initial_marking']=={} and not d['training']['training_witness_imported']
    assert d['training']['updates']==len(d['training']['episodes'])
    assert set(r['seed'] for r in d['donors']).isdisjoint(r['seed'] for r in d['evaluation'])
    assert set(r['seed'] for r in d['training']['episodes']).isdisjoint(r['seed'] for r in d['evaluation'])
    geometry=geometry_audit({'point_model':{'vertices':VERTICES},'pair_catalog':{'samples':[]},'evaluation':patches})
    d['independent_audit']={'states_replayed':checked,'complete_states':complete,'scheduled_base_moves_checked':moves,
        'literal_inventory_placements':len(oracle.values),'clusters_reconstructed':len(library),'tampered_schedules_rejected':rejected,
        'geometry':geometry,'seconds':time.monotonic()-start,'peak_process_memory_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'audit_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'scope':'every saved constituent: complete literal singleton domains, global scheduler, values, ownership, generations and authored target; no negative certificate or plane proof'}
    path.write_text(json.dumps(d,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in d['independent_audit'].items() if k!='geometry'},indent=2),flush=True)

if __name__=='__main__':main()
