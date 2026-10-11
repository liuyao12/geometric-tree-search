"""Checkpointed automatic point search and generic whole certification.

The fixed grammar/pruning plans contain no selected target-proof path. All
selected placements/tree/model are saved before any whole checking. The same
searched request is mechanically expanded/shared; exact duplicate validation
requests may reuse completed native checks with separate historical costs.
"""
import copy,gzip,hashlib,json,resource,subprocess,time
from pathlib import Path
from left_successor_points import Model
from native_receptor_points import search
from induction_receptors_closure import expand
from induction_receptors_compaction import formula_dag
from audit_semantic_proofs import whole_replay
from certificate_boundary_search import digest
from semantic_inventory_worker import oracle_for
from proof_boundary import boundary_words

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];OUT=ROOT/'.gcts-active/left-successor-20261011';TMP=Path('/private/tmp/gcts-left-successor-search-20261011')
def load(p):return json.loads(gzip.decompress(p.read_bytes()))
def save(p,v):p.write_bytes(gzip.compress(json.dumps(v,separators=(',',':')).encode(),mtime=0))
def need(t,m):
    if not t:raise ValueError(m)
def main():
    began=time.perf_counter();plan=json.loads((OUT/'search-plan.json').read_text());base=json.loads((OUT/'plan.json').read_text());need(json.loads((OUT/'admission-audit.json').read_text())['status']=='passed_complete_reachable_native_admission','complete native union audit')
    for p,h in plan['source_sha256'].items():need(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'frozen search source '+p)
    TMP.mkdir(parents=True,exist_ok=True);compile_start=time.perf_counter();subprocess.run(['clang++','-O3','-std=c++17',str(HERE/'boundary_oracle.cpp'),'-o',str(TMP/'oracle')],check=True);oracle=oracle_for(dict(directory=str(TMP/'native'),executable=str(TMP/'oracle')));summary=dict(status='running',observations=[],native_queries=0,native_validation_cache_hits=0,compile_and_oracle_setup_seconds=time.perf_counter()-compile_start);checked={}
    try:
        for obs in plan['observations']:
            spec=copy.deepcopy(base['case']);spec.update(id=obs['id'],length=obs['length']);c=load(OUT/(obs['lane']+'-reachable-core.json.gz'));admission=json.loads((OUT/(obs['lane']+'-admission.json')).read_text());model=Model(spec,c,admission);r=search(model,**plan['search_limits']);r['command_skeleton']=r['proof']
            if r['proof'] is not None:r['proof']=model.decode(r['placements'])
            raw=dict(case=spec,lane=obs['lane'],rep=obs['rep'],model=model.record(),search=r,whole_variants=[],peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,checkpoint='Complete point trace saved before whole checking');save(OUT/(obs['id']+'.json.gz'),raw);metric=dict(id=obs['id'],lane=obs['lane'],rep=obs['rep'],length=obs['length'],status=r['status'],attempts=r['metrics'].get('attempts',0),search_seconds=r['seconds'],model_setup_seconds=model.compile_seconds,placements=len(model.cache),peak_rss_bytes=raw['peak_rss_bytes'],whole_variants=[]);summary['observations'].append(metric);(OUT/'search-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('SEARCH CHECKPOINT',json.dumps(metric),flush=True)
            if r['proof'] is not None:
                names={p['name'] for p in r['proof'] if p['rule']=='block'};original=dict(protocol='gcts-fol-1',theory=spec['theory'],blocks=[d for d in c['definitions'] if d['name'] in names],proof=r['proof'],target=spec['target']);prep=time.perf_counter();expanded=expand(original);primitive=copy.deepcopy(original);primitive.update(blocks=[],proof=formula_dag(expanded));need(whole_replay(original)['status']==whole_replay(primitive)['status']=='accepted' and primitive['theory']==original['theory'] and primitive['target']==original['target'],'same searched theorem and separate host audits');raw.update(original_request=original,expanded_commands=len(expanded),primitive_request=primitive,compaction_preparation_seconds=time.perf_counter()-prep);save(OUT/(obs['id']+'.json.gz'),raw)
                for mode in plan['whole_variants']:
                    request=original if mode=='selected-high-level' else primitive;h=digest(request);cached=h in checked
                    if cached:q=checked[h];summary['native_validation_cache_hits']+=1
                    else:
                        q=oracle.request(request,plan['native_steps'],'left_successor_discovered_'+mode);fixed,free=boundary_words(q['request']);q.update(boundary_words=dict(fixed=fixed,free=free),limit=plan['native_steps']);checked[h]=q;save(OUT/'search-native.json.gz',oracle.records)
                        for name in ('input.bin','output.bin'):(OUT/('search-query-%03d-'%q['id']+name+'.gz')).write_bytes(gzip.compress((TMP/'native'/name).read_bytes(),mtime=0))
                    value=dict(mode=mode,query=q['id'],native_status=q['result']['status'],request_sha256=h,proof_commands=len(request['proof']),cached_exact_request=cached,historical_native_seconds=q['seconds'],historical_micro_steps=q['result']['micro_steps']);raw['whole_variants'].append(value);metric['whole_variants'].append(value);save(OUT/(obs['id']+'.json.gz'),raw);summary['native_queries']=len(oracle.records);(OUT/'search-summary.json').write_text(json.dumps(summary,indent=2)+'\n');print('WHOLE CHECKPOINT',obs['id'],json.dumps(value),flush=True)
            del model,c,admission,raw,r
        summary.update(status='complete_search_and_native_observations_pending_independent_audit',seconds=time.perf_counter()-began,scope='All search observations and whole outcomes checkpointed, including unknowns. Without/with inventory lanes differ semantically; repetitions use the same inventory with fresh models. No RL, search-speed or target success claim before complete independent tree/whole replay.')
    finally:
        summary.update(seconds=time.perf_counter()-began,native_queries=len(oracle.records));(OUT/'search-summary.json').write_text(json.dumps(summary,indent=2)+'\n');save(OUT/'search-native.json.gz',oracle.records);oracle.close()
if __name__=='__main__':main()
