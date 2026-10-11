"""Matched13row fresh-process observations; no ordinary artifact input."""
import argparse
import copy
import gc
import gzip
import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path
from certificate_boundary_search import canonical
from commutativity_cluster_points import Model
from commutativity13_executor_search import search
from commutativity13_json import save

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.gcts-active/commutativity13-20261011'
PARENT=ROOT/'.gcts-active/commutativity-receptors-20261011'


def load(path):
    with gzip.open(path,'rt') as stream:return json.load(stream)


def verify(plan):
    for p,h in {**plan['source_sha256'],**plan['input_sha256']}.items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h:raise ValueError('exact fresh executor source/input '+p)


def binding(record,domains,length):
    roots=sorted(record['roots'])
    return dict(schema='exact-scalar-point-model-v1',length=length,
                required_points=[dict(point=p,generation=0) for p in roots],
                initial=dict(roots=[[p,0] for p in roots],generations=[[p,0] for p in roots],marks=sorted(record['initial_marks']),totals=[],allowed_points=roots),
                placements=sorted(record['placements'],key=lambda p:p['key']),injective_catalog=record['catalog'],inference_rules=record['inference_rules'],
                rule_modes=[i+1 if r['premises'] else 0 for i,r in enumerate(record['inference_rules'])],row_domains=domains,arity=2,capacity=12,registry_sha256=record['registry_sha256'])


def single(name):
    began=time.perf_counter();plan=json.loads((OUT/'execution-freeze.json').read_text());verify(plan)
    observation=next(v for v in plan['observations'] if v['id']==name)
    gate=json.loads((OUT/'preflight-audit-v2.json').read_text())
    if gate['status']!='passed_complete_exact_proposer_serialization_and13model_preflight':raise ValueError('complete independent preflight gate')
    spec=copy.deepcopy(plan['case']);spec.update(id=name,length=13)
    registry=PARENT/'native-complete/registry.json.gz';stage=time.perf_counter()
    model=Model(spec,load(PARENT/'attempt-02/two-lemmas-retained-core.json.gz'),load(registry),json.loads((PARENT/'native-complete/registry-audit.json').read_text()),registry.read_bytes())
    setup=time.perf_counter()-stage;record=model.record();h=hashlib.sha256(canonical(binding(record,model.domains,13))).hexdigest()
    if h!=gate['complete_model_sha256']:raise ValueError('exact complete model/initial boundary across lanes')
    stage=time.perf_counter();save(OUT/(name+'-model.json.gz'),dict(case=spec,model=record,row_domains=model.domains,complete_model_sha256=h));model_serialization=time.perf_counter()-stage
    del record;gc.collect()
    observed=search(model,mode=observation['mode'],seed=observation['rep'],attempts=5000,seconds=60,rss_bytes=536870912)
    checkpoint=dict(id=name,case=spec,observation=observation,status=observed['status'],proof=observed['proof'],metrics=observed['metrics'],placements=observed['placements'],complete_model_sha256=h,
                    search_seconds=observed['seconds'],peak_rss_bytes=observed['peak_rss_bytes'],native_target_queries=0,ordinary_word_or_witnesses_used=False)
    (OUT/(name+'-checkpoint.json')).write_text(json.dumps(checkpoint,indent=2)+'\n')
    stage=time.perf_counter();save(OUT/(name+'-search.json.gz'),dict(case=spec,observation=observation,search=observed,native_target_queries=0));trace_serialization=time.perf_counter()-stage
    summary=dict(id=name,mode=observation['mode'],rep=observation['rep'],status=observed['status'],metrics=observed['metrics'],limits=observed['limits'],
                 proof_rows=len(observed['proof']) if observed['proof'] else None,complete_model_sha256=h,
                 model_setup_seconds=setup,model_serialization_seconds=model_serialization,
                 proposer_cold_initialization_seconds=observed['proposer_initialization_seconds'],search_seconds=observed['seconds'],
                 proposal_seconds=observed['metrics'].get('proposal_seconds',0.),trace_serialization_seconds=trace_serialization,
                 process_seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                 search_wall_overshoot_seconds=max(0.,observed['seconds']-60),memory_overshoot_bytes=max(0,resource.getrusage(resource.RUSAGE_SELF).ru_maxrss-536870912),
                 native_target_queries=0,whole_native_status='not_executed',
                 cache='Fresh coldstatic/ranking cache per process. ExactLRU rankings warm only on that observation. Initialization is included in search seconds; proposal seconds exclude initial static index.',
                 scope='Same13row complete marked region/153rules/94definitions and5000attempt60swall ceilings in base/fixed. Fixedweights authored; no RLtraining or ordinaryproof input.')
    if summary['peak_rss_bytes']>536870912:summary['status']='unknown_observation_host_memory_budget'
    (OUT/(name+'-summary.json')).write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)


def main():
    began=time.perf_counter();plan=json.loads((OUT/'execution-freeze.json').read_text());verify(plan)
    result=dict(status='running_order_balanced_matched13searches',observations=[],native_target_queries=0,unexecuted=[v['id'] for v in plan['observations']])
    for observation in plan['observations']:
        if time.perf_counter()-began>=300:
            result['status']='unknown_total_search_producer_time_budget';break
        p=subprocess.run([sys.executable,__file__,'--single',observation['id']])
        if p.returncode!=0:
            result['status']='unknown_or_failed_observation_process';break
        result['observations'].append(json.loads((OUT/(observation['id']+'-summary.json')).read_text()))
        result['unexecuted'].remove(observation['id']);result['seconds']=time.perf_counter()-began
        (OUT/'search-summary.json').write_text(json.dumps(result,indent=2)+'\n')
        if result['observations'][-1]['peak_rss_bytes']>536870912:
            result['status']='unknown_search_producer_memory_budget';break
    else:result['status']='complete_four_matched13_search_observations_pending_independent_audit'
    result.update(seconds=time.perf_counter()-began,producer_wall_overshoot_seconds=max(0.,time.perf_counter()-began-300),dispatcher_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if result['seconds']>300:result['status']='unknown_total_search_producer_time_budget'
    (OUT/'search-summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--single');args=p.parse_args()
    if args.single:single(args.single)
    else:main()
