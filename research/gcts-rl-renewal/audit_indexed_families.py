"""Reconstruct primary trees, syntax indexes, cache lifetimes and timing bindings."""
import copy,gzip,hashlib,json,statistics,time
from pathlib import Path
import check_indexed_families as J
import check_resumable_clusters as V
from audit_resumable_clusters import audit as original_audit
from indexed_cases import registry
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def semantic(r):
    keys=('status','placements','tile_generations','proof','endpoint','candidate_universe','search_tree','hints','solution_hints','policy_events')
    return dict(**{k:r[k] for k in keys},metrics={k:v for k,v in r['metrics'].items() if not k.endswith('seconds')})
def audit(data):
    started=time.perf_counter();ds,ts,es=registry()
    compatible=[dict(c,runs={('fixed' if k=='enumerated' else 'index-fixed' if k=='indexed' else k):r for k,r in c['runs'].items()}) for c in data['cases'][:9]]
    base=original_audit(dict(data,cases=compatible));templates={t['name']:t for t in data['library']};extra=[];indexes=[]
    V.N(V.F([c['spec'] for c in data['cases']])==V.F(es),'whole declarative registry')
    for i,d in enumerate(data['donors']):indexes.append(J.index(d,d['result'],{t['name']:t for t in data['library'] if t['source']['spec']['id']==ds[0]['id']},i>0))
    for e in data['training']['episodes']:indexes.append(J.index(e,e['result'],templates,True))
    repeats=0
    for i,c in enumerate(data['cases']):
        rules,forms=V.A.A.inventory(c['spec']);V.N(V.F(c['catalog']['rules'])==V.F(rules) and V.F(c['catalog']['formulas'])==V.F(forms),'complete independent grammar')
        statuses=set()
        for name,r in c['runs'].items():
            if i>=9:extra.append(V.result(rules,c['spec'],templates,r))
            indexes.append(J.index(c,r,templates,name not in ('base','enumerated')))
            pin=V.V.digest(semantic(r));V.N(pin==r['semantic_sha256'],'retained primary semantic digest');t=c['timings'][name];samples=t['samples'];V.N(len(samples)==8,'eight cold observations')
            lanes=('base','enumerated','indexed','rl','zero')
            for j,s in enumerate(samples):
                offset=(i+j)%5;V.N(s['repetition']==j and tuple(s['order'])==lanes[offset:]+lanes[:offset],'cyclic matched lane order')
                V.N(s['semantic_sha256']==pin,'every repeated trace bound to primary')
                V.N(s['seconds']>=s['search_seconds']+s['grammar_seconds']+s['positive_check_seconds']>=0 and 0<=s['index_build_seconds']<=s['search_seconds'],'declared nonnegative inclusive clocks')
            values=[s['seconds'] for s in samples];V.N(t['median_seconds']==statistics.median(values) and t['min_seconds']==min(values) and t['max_seconds']==max(values),'exact observed timing summary');repeats+=len(samples);statuses.add(r['status'])
        V.N(len(statuses)==1,'same bounded result across lanes')
        V.N(c['runs']['enumerated']['semantic_sha256']==c['runs']['indexed']['semantic_sha256'],'exact ordered pool and whole-tree equivalence')
        if i>=9:
            for r in c['controls'].values():
                if r['proof'] is not None:
                    V.A.A.proof(r['proof'],c['spec']['target'],c['spec']['hypotheses'],c['spec']['theory'])
                    V.N(r['fits_region_bound']==(len(r['proof'])<=c['spec']['bound']),'control horizon')
                    if r['fits_region_bound']:V.A.certificate(rules,c['spec'],r['region_certificate'],r['region_certificate']['tiles']);V.certificate(c['spec'],r['region_certificate'])
        print(c['spec']['id'],'index replayed',flush=True)
    sample=next(c for c in data['cases'] if c['spec']['id']=='indexed-tail-five');mutations=[]
    for name in ('query','binding','ground-match','ground-formula','query-hits','aggregate-misses','model','library','digest-hits'):
        r=copy.deepcopy(sample['runs']['indexed']);a=r['index']
        if name=='query':a['queries'].pop()
        elif name=='binding':next(q for q in a['queries'] if q['bound'])['bound'][0][1]=['bot']
        elif name=='ground-match':next(n for n in a['nodes'].values() if n['rows'])['rows'].pop()
        elif name=='ground-formula':next(n for n in a['nodes'].values() if n['rows'])['rows'][0][1]['0']=['bot']
        elif name=='query-hits':a['metrics']['query_cache_hits']+=1
        elif name=='aggregate-misses':a['metrics']['aggregate_cache_misses']+=1
        elif name=='model':a['context']='!'
        elif name=='library':a['library_pin']='!'
        else:a['metrics']['item_digest_hits']+=1
        try:J.index(sample,r,templates,True)
        except (ValueError,KeyError,IndexError,TypeError):mutations.append(name)
        else:raise ValueError('accepted corrupt index '+name)
    return dict(status='passed',searches=base['searches']+len(extra),independent_states=base['independent_states']+sum(c['nodes'] for c in extra),index_records=sum(i['indexed'] for i in indexes),index_queries=sum(i.get('queries',0) for i in indexes),
        templates=len(templates),levels=base['levels'],on_policy_draws=base['on_policy_draws'],repeated_cold_summaries=repeats,base_mutations=base['mutations_rejected'],index_mutations=mutations,seconds=time.perf_counter()-started,
        scope='Complete primary trees, full proposal pools, every lazy syntax table/query/cache counter and source/kernel certificate are independently replayed. Eight cold timing summaries per lane are source-pinned and digest-bound to retained primary trees; full repeat traces are not retained or independently replayed. Classical negative/unknown traces and measured wall clocks are not independently reconstructed.')
def main():
    path=DOC/'indexed-families-001.json.gz';data=json.loads(gzip.decompress(path.read_bytes()))
    for n,pin in data['sources'].items():V.N(sha(HERE/n)==pin,'measured source '+n)
    out=audit(data);out.update(version='indexed-families-audit-001',input_sha256=sha(path),source_sha256=sha(__file__),
        helpers={n:sha(HERE/n) for n in ('check_indexed_families.py','check_resumable_clusters.py','audit_resumable_clusters.py','check_adaptive_clusters.py','check_movable_regions.py','check_compact_contexts.py','indexed_cases.py','resumable_cases.py')})
    (DOC/'indexed-families-audit-001.json').write_bytes(V.P(out)+b'\n');print(json.dumps(out),flush=True)
if __name__=='__main__':main()
