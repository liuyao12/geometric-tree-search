"""Complete native admission of the proved-pruned union, with exact reuse.

The complete unpruned grammars and reachability witnesses remain unchanged.
Only byte-identical accepted full requests may reuse a pilot check. Every new
request and parser tape is checkpointed; any unknown/rejection stops before a
model can be constructed. Independent native audits are a separate next gate.
"""
import gzip,hashlib,json,subprocess,time
from pathlib import Path
from certificate_boundary_search import canonical,digest
from semantic_inventory_worker import oracle_for
from proof_boundary import boundary_words

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/left-successor-20261011';TMP=Path('/private/tmp/gcts-left-successor-admission-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def need(t,m):
    if not t:raise ValueError(m)
def native_request(theory,d):
    taut=['imp',['bot'],['bot']];return dict(protocol='gcts-fol-1',theory=theory,blocks=[d],proof=[dict(rule='tautology',formula=taut)],target=taut)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'admission-plan.json').read_text());base=json.loads((OUT/'plan.json').read_text());need(json.loads((OUT/'reachability-audit.json').read_text())['status']=='passed_finite_grammar_structural_pruning','complete proved pruning replay')
    for p,h in plan['source_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen admission source '+p)
    pilot=load(OUT/'pilot-native.json.gz');union={}
    for lane in base['variants']:
        c=load(OUT/(lane+'-reachable-core.json.gz'))
        for d in c['definitions']:
            if d['name'] in union:need(union[d['name']]==d,'identical union definition')
            union[d['name']]=d
    need(sorted(union)==plan['union_names'],'complete declared union');TMP.mkdir(parents=True,exist_ok=True);compile_start=time.perf_counter();subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True);oracle=oracle_for(dict(directory=str(TMP/'native'),executable=str(TMP/'oracle')));summary=dict(status='checking_native_union',definitions=[],native_queries=0,reused_exact_queries=0,new_native_micro_steps=0,compile_and_oracle_setup_seconds=time.perf_counter()-compile_start)
    try:
        for d in [union[n] for n in plan['union_names']]:
            request=native_request(base['case']['theory'],d);h=digest(request);entry=plan['reuse'].get(d['name'])
            if entry is not None:
                q=pilot[entry['pilot_query']];need(q['request']==request and q['request_sha256']==h==entry['request_sha256'] and q['result']['status']=='accepted','exact accepted native request reuse');summary['reused_exact_queries']+=1;row=dict(name=d['name'],request_sha256=h,status='accepted',source='pilot-exact-request',query=q['id'],historical_seconds=q['seconds'],historical_micro_steps=q['result']['micro_steps'])
            else:
                if len(oracle.records)>=plan['ceilings']['new_queries'] or time.perf_counter()-began>=plan['ceilings']['seconds'] or summary['new_native_micro_steps']>=plan['ceilings']['aggregate_micro_steps']:
                    summary['status']='unknown_native_admission_budget';return
                q=oracle.request(request,plan['ceilings']['per_query_micro_steps'],'left_successor_complete_reachable_definition');fixed,free=boundary_words(q['request']);q.update(boundary_words=dict(fixed=fixed,free=free),limit=plan['ceilings']['per_query_micro_steps'],definition_name=d['name']);save(OUT/'admission-native.json.gz',oracle.records)
                for name in ('input.bin','output.bin'):(OUT/('admission-query-%03d-'%q['id']+name+'.gz')).write_bytes(gzip.compress((TMP/'native'/name).read_bytes(),mtime=0))
                summary['new_native_micro_steps']+=q['result']['micro_steps'];row=dict(name=d['name'],request_sha256=h,status=q['result']['status'],source='fresh-native-request',query=q['id'],seconds=q['seconds'],micro_steps=q['result']['micro_steps'])
            summary['definitions'].append(row);summary.update(native_queries=len(oracle.records),seconds=time.perf_counter()-began);(OUT/'admission-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(row),flush=True)
            if row['status']!='accepted':summary['status']='unknown_or_rejected_native_union';return
        summary.update(status='native_complete_pending_independent_replays',complete_definitions=len(union),scope='Every reachable union definition accepted under exact original theory. Exact reused queries retain historical costs. No model/search until the whole pilot and admission native computations are independently replayed.')
    finally:
        summary.update(native_queries=len(oracle.records),seconds=time.perf_counter()-began,target_searches=0);(OUT/'admission-summary.json').write_text(json.dumps(summary,indent=2)+'\n');save(OUT/'admission-native.json.gz',oracle.records);oracle.close()
if __name__=='__main__':main()
