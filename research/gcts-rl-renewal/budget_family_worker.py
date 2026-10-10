"""Fresh solve process with cold input/library loads and certified markings."""
import argparse,gzip,hashlib,json,resource,sys,time
from pathlib import Path
import dependency_budget as B
import budget_family_search as S
import check_dependency_budget as V
from budget_family_cases import registry
from run_adaptive_clusters import inventory
from run_resumable_clusters import control
from dependency_budget_worker import SOURCES as OLD
from compact_contexts import compile_request
from serialized_kernel import canonical

HERE=Path(__file__).resolve().parent
SOURCES=tuple(dict.fromkeys((*OLD,'budget_family_policy.py','budget_family_search.py',
    'budget_family_cases.py','budget_family_worker.py','run_budget_families.py',
    'check_budget_families.py','budget_family_join.py','quantifier_family_patterns.py','quantifier_family_join.py',
    'indexed_family_join.py','resumable_clusters.py','receptor_attention.py')))
LIMITS=dict(attempts=10000,seconds=60,proposal_limit=32)
HEURISTIC=(0.,0.,2.,1.,2.,0.,0.,0.,0.,0.,0.,0.)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def semantic(record):
    r=record['result'];fields=('status','placements','tile_generations','proof','endpoint',
        'candidate_universe','search_tree','hints','solution_hints','policy_events',
        'attention_support','weights','stochastic','seed','mode','feature_mode','limits',
        'tiles','root_marks')
    index=r['index']
    return dict(spec=record['spec'],catalog=record['catalog'],
        certificate={k:v for k,v in record['certificate'].items() if k!='seconds'},
        result={k:r[k] for k in fields},metrics={k:v for k,v in r['metrics'].items() if not k.endswith('seconds')},
        graph_metrics=r['graph_metrics'],index={k:v for k,v in index.items() if k!='build_seconds'} if index else None)

def solve(group,index,lane,library_path=None,weights=None,stochastic=False,seed=0):
    started=time.perf_counter();spec=registry()[('donor','training','evaluation').index(group)][index]
    if lane=='saturation':
        r=control(spec,'saturation');r['total_seconds']=time.perf_counter()-started
        return dict(spec=spec,result=r)
    load_start=time.perf_counter()
    library=json.loads(gzip.decompress(Path(library_path).read_bytes())) if library_path else []
    library_load=time.perf_counter()-load_start
    cat_start=time.perf_counter();cat=inventory(spec);grammar=time.perf_counter()-cat_start
    original=B.Model(cat,spec['target'],spec['bound'],spec['hypotheses']);cert=B.synthesis(original)
    began=time.perf_counter();V.certificate(cat['rules'],spec,cert);certification=time.perf_counter()-began
    model=B.Model(cat,spec['target'],spec['bound'],spec['hypotheses'],cert)
    parameters=(HEURISTIC if lane in ('families','occupied') else [0.]*12 if lane=='zero' else weights)
    if lane=='budget':parameters=None
    prep=time.perf_counter()-started
    r=S.search(model,library,'base' if lane=='budget' else 'policy',parameters,stochastic,seed,
               **LIMITS,feature_mode='occupied' if lane=='occupied' else 'justified')
    checked=time.perf_counter()
    r['tiles']=[dict(key=k,occupancy=model.placement(k).occupancy,marks=model.placement(k).marks) for k in r['placements']]
    r['root_marks']=tuple(sorted(model.initial().marks.items()))
    V.state(cat['rules'],spec,r['placements'],model.requirements)
    if r['proof'] is not None:
        stripped=[dict(t,marks=[(p,v) for p,v in t['marks'] if p[0]!=-3000]) for t in r['tiles']]
        r['point_check']=V.A.certificate(cat['rules'],spec,r,stripped)
        r['compact']=compile_request(r['proof'],spec['target'],spec['hypotheses'],spec['theory'])
    r.update(library_load_seconds=library_load,grammar_seconds=grammar,
        synthesis_seconds=cert['seconds'],certification_seconds=certification,
        preparation_seconds=prep,positive_check_seconds=time.perf_counter()-checked,
        total_seconds=time.perf_counter()-started)
    record=dict(spec=spec,catalog=cat,certificate=cert,result=r)
    r['semantic_sha256']=hashlib.sha256(canonical(semantic(record))).hexdigest()
    return record

def main():
    p=argparse.ArgumentParser();p.add_argument('--group',choices=('donor','training','evaluation'),required=True)
    p.add_argument('--case',type=int,required=True);p.add_argument('--lane',choices=('budget','families','rl','zero','occupied','saturation'),required=True)
    p.add_argument('--library',type=Path);p.add_argument('--weights');p.add_argument('--stochastic',action='store_true');p.add_argument('--seed',type=int,default=0)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();pins={n:sha(HERE/n) for n in SOURCES}
    record=solve(a.group,a.case,a.lane,a.library,json.loads(a.weights) if a.weights else None,a.stochastic,a.seed)
    record['sources']=pins;record['peak_process_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1024 if sys.platform=='linux' else 1)
    if any(sha(HERE/n)!=v for n,v in pins.items()):raise ValueError('measured source changed')
    a.output.parent.mkdir(parents=True,exist_ok=True);tmp=a.output.with_suffix('.partial')
    tmp.write_bytes(gzip.compress(canonical(record)+b'\n',mtime=0));tmp.replace(a.output)

if __name__=='__main__':main()
