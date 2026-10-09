"""External problem declarations, JSON replay and negative-tree checking.

This does not trust proof-provided boundaries, type definitions or success
flags. It reconstructs declarations from run_regions and the explicit old
artifact provenance, then replays values without any search-domain index.
"""
import copy,dataclasses,hashlib,json,time
from pathlib import Path
from cluster_tiles import ClusterModel,ClusterType,ClusterState,compose_type,verify_state
from spatial import keys_tuple
from coverage import hexagon
from region_tiles import Boundary,RegionModel,verify_region,unpack_state,check_failure
from run_regions import HERE,DOCS,load_types,problems,movable_cases
from audit_geometry import audit as geometry_audit
from turtle import VERTICES

def normal(x):return json.loads(json.dumps(x))

def parent_type(t):
    return ClusterType(t['identity'],t['level'],keys_tuple(t['expansion']),tuple((tuple(p),v) for p,v in t['occupancy']),
        tuple(((tuple(p),ch),v) for (p,ch),v in t['marks']),tuple((n,o,tuple(tr)) for n,o,tr in t['children']))

def main():
    start=time.monotonic();path=DOCS/'regions-001.json';d=json.loads(path.read_text());types=load_types();single=types[:1]
    train,evals=problems();families=movable_cases(evals);declarations={b.identity:b for b,m in train+evals}
    assert normal(d['training']['problems'])==normal([{'boundary':b.packed(),'construction':m} for b,m in train])
    assert normal(d['problems'])==normal([{'boundary':b.packed(),'construction':m} for b,m in evals])
    assert normal(d['movable_families'])==normal([[b.packed() for b in family] for family in families])
    for name,sha in d['reuse']['artifacts'].items():assert hashlib.sha256((DOCS/name).read_bytes()).hexdigest()==sha
    for name,sha in d['source_sha256'].items():
        if name not in ('test_region_tiles.py','audit_regions.py'):assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==sha
    models={};checked=complete=base=rejected=negative_nodes=0;checked_paths=[]
    def model(boundary,lane):
        k=boundary,lane=='singletons'
        if k not in models:models[k]=RegionModel(single if k[1] else types,boundary)
        return models[k]
    def replay(r,boundary,lane,path):
        nonlocal checked,complete,base,rejected,negative_nodes
        m=model(boundary,lane);s=unpack_state(m,boundary,r['state']);exact=r['status']=='finite_exact_region'
        assert verify_region(m,boundary,s,exact)
        assert r['required_points']==len(boundary.required)
        assert r['coverage_fraction']==sum(s.totals.get(p,0)==12 for p in boundary.required)/len(boundary.required)
        assert r['accepted_base_tiles']==len(s.owned_base-set(boundary.owned));assert r['accepted_cluster_tiles']==len(s.order)
        if r['status']=='exhausted_finite_region':
            ok,n=check_failure(m,boundary,r['certificate']);assert ok;negative_nodes+=n
        else:assert r['certificate'] is None
        checked+=1;complete+=exact;base+=r['accepted_base_tiles'];checked_paths.append(path)
        if exact:
            for field in ['totals','marks','tile_generations','base_expansion']:
                bad=copy.deepcopy(r['state'])
                if field=='marks':bad[field].append([[[100,-50,-50],'base'],0])
                else:bad[field]=[]
                try:unpack_state(m,boundary,bad)
                except (ValueError,TypeError):rejected+=1
                else:raise AssertionError('tampered state accepted')
    for i,r in enumerate(d['training']['episodes']):replay(r,declarations[r['problem']],'aggregate',f'training/{i}')
    for i,r in enumerate(d['evaluation']):replay(r,declarations[r['problem']],r['lane'],f'evaluation/{i}')
    for i,r in enumerate(d['movable_evaluation']):
        family=families[r['family']];ids=[b.identity for b in family]
        assert [a['boundary'] for a in r['attempts']]==ids[:len(r['attempts'])]
        for j,a in enumerate(r['attempts']):replay(a['result'],family[j],r['lane'],f'movable/{i}/{j}')
        if r['status']=='finite_exact_movable_region':
            assert r['selected']==r['attempts'][-1]['boundary'];assert r['attempts'][-1]['result']['status']=='finite_exact_region'
    points=frozenset(hexagon(5));negative=Boundary('closed-hex-control',points,points)
    assert normal(d['negative_control']['boundary'])==normal(negative.packed())
    replay(d['negative_control']['result'],negative,'singletons','negative-control')
    proof=copy.deepcopy(d['negative_control']['result']['certificate']);proof['children'].pop()
    assert not check_failure(model(negative,'singletons'),negative,proof)[0];rejected+=1
    # Reconstruct every new type from the searched children; a certificate cannot
    # replace that descending expansion by an unrelated prototype.
    cm=ClusterModel(types);parents=[]
    for r in d['evaluation']:
        if r['lane']=='aggregate+RL' and r['status']=='finite_exact_region':
            parents.append(compose_type(cm,'solution-'+r['problem'],tuple((n,o,tuple(tr)) for n,o,tr in r['state']['placements'])))
    assert normal([dataclasses.asdict(t) for t in parents])==d['local_solution_types']['types']
    cm=ClusterModel(types+parents);transformed=0
    for t in parents:
        for o in range(12):
            s=ClusterState();s.place(cm.placement((t.identity,o,(0,0,0))),seed=True)
            assert verify_state(cm,s);transformed+=1
    patches=[]
    for r in d['evaluation']:
        if r['status']=='finite_exact_region':patches.append({'lane':r['lane']+'/'+r['problem'],'seed':r['seed'],'placements':r['state']['base_expansion']})
    for r in d['movable_evaluation']:
        if r['selected']:
            last=r['attempts'][-1]['result'];patches.append({'lane':r['lane']+'/movable/'+str(r['family']),'seed':last['seed'],'placements':last['state']['base_expansion']})
    geometry=geometry_audit({'point_model':{'vertices':VERTICES},'pair_catalog':{'samples':[]},'evaluation':patches})
    d['independent_audit']={'states_replayed':checked,'completed_states':complete,'new_base_placements_replayed':base,
        'negative_tree_nodes_checked':negative_nodes,'tampered_certificates_rejected':rejected,
        'local_solution_types':len(parents),'transformed_expansions_checked':transformed,'checked_paths':checked_paths,
        'geometry':geometry,'audit_source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'post_run_test_source_sha256':hashlib.sha256((HERE/'test_region_tiles.py').read_bytes()).hexdigest(),
        'seconds':time.monotonic()-start,'scope':'externally reconstructed boundary declarations; point/ownership/generation/expansion replay; complete negative tree; no plane or geometric faithfulness claim'}
    path.write_text(json.dumps(d,separators=(',',':'))+'\n');print(json.dumps(d['independent_audit'],indent=2),flush=True)

if __name__=='__main__':main()
