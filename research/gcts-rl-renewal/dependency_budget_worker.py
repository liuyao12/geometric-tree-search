"""One cold solve, including synthesis, certification and proof verification."""
import argparse
import gzip
import hashlib
import resource
import sys
import time
from pathlib import Path

import dependency_budget as B
import dependency_budget_search as S
import check_dependency_budget as V
from dependency_budget_cases import registry
from run_adaptive_clusters import inventory
from run_resumable_clusters import SOURCES as OLD, control
from compact_contexts import compile_request
from serialized_kernel import canonical

HERE=Path(__file__).resolve().parent
SOURCES=tuple(dict.fromkeys((*OLD, 'dependency_budget.py', 'dependency_budget_search.py',
    'dependency_budget_cases.py', 'dependency_budget_worker.py', 'run_dependency_budget.py',
    'check_dependency_budget.py', 'quantifier_family_cases.py', 'receptor_attention_cases.py')))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def semantic(record):
    result=record['result']
    fields=('status','placements','tile_generations','proof','endpoint','metrics',
            'graph_metrics','search_tree','candidate_universe','limits','tiles','root_marks')
    cert=record['certificate']
    return dict(spec=record['spec'], catalog=record['catalog'],
                certificate={k:v for k,v in cert.items() if k!='seconds'} if cert else None,
                result={k:result[k] for k in fields})


def solve(index, lane):
    started=time.perf_counter();spec=registry()[index]
    if lane=='saturation':
        result=control(spec,'saturation');result['total_seconds']=time.perf_counter()-started
        return dict(spec=spec,result=result)
    cat_start=time.perf_counter();cat=inventory(spec);grammar=time.perf_counter()-cat_start
    original=B.Model(cat,spec['target'],spec['bound'],spec['hypotheses'])
    cert=B.synthesis(original) if lane=='budget' else None
    verification_started=time.perf_counter()
    if cert:V.certificate(cat['rules'],spec,cert)
    certification=time.perf_counter()-verification_started
    model=B.Model(cat,spec['target'],spec['bound'],spec['hypotheses'],cert)
    prep=time.perf_counter()-started
    result=S.search(model,attempts=50000,seconds=60)
    checked=time.perf_counter()
    result['tiles']=[dict(key=k,occupancy=model.placement(k).occupancy,marks=model.placement(k).marks) for k in result['placements']]
    result['root_marks']=tuple(sorted(model.initial().marks.items()))
    V.state(cat['rules'],spec,result['placements'],model.requirements if cert else None)
    if result['proof'] is not None:
        stripped=[dict(t,marks=[(p,v) for p,v in t['marks'] if p[0]!=-3000]) for t in result['tiles']]
        result['point_check']=V.A.certificate(cat['rules'],spec,result,stripped)
        result['compact']=compile_request(result['proof'],spec['target'],spec['hypotheses'],spec['theory'])
    result.update(grammar_seconds=grammar,synthesis_seconds=cert['seconds'] if cert else 0.,
                  certification_seconds=certification,preparation_seconds=prep,
                  positive_check_seconds=time.perf_counter()-checked,total_seconds=time.perf_counter()-started)
    record=dict(spec=spec,catalog=cat,certificate=cert,result=result)
    result['semantic_sha256']=hashlib.sha256(canonical(semantic(record))).hexdigest()
    return record


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--case',type=int,required=True)
    parser.add_argument('--lane',choices=('base','budget','saturation'),required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    pins={n:sha(HERE/n) for n in SOURCES};record=solve(args.case,args.lane)
    record['sources']=pins
    record['peak_process_rss_bytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1024 if sys.platform=='linux' else 1)
    if any(sha(HERE/n)!=pin for n,pin in pins.items()):raise ValueError('measured source changed')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    temporary=args.output.with_suffix('.partial');temporary.write_bytes(gzip.compress(canonical(record)+b'\n',mtime=0));temporary.replace(args.output)


if __name__=='__main__':main()
