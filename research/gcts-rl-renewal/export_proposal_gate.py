"""Project actual positive leaves, pre-join decisions, and recorded updates."""
import collections,gzip,hashlib,json
from pathlib import Path
from export_resumable_clusters import project as old
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def project(data,audit):
    # The earlier projector expects a work-proxy update. Use only its unchanged
    # proof projection, then export this experiment's actual wall-time updates.
    source=dict(data,training=dict(data['training'],episodes=[]))
    out=old(source,audit);out['version']='proposal-gate-reader-001';out['timing_scope']=data['timing_scope']
    def enrich(r,raw):
        node=raw['search_tree'];ids=set()
        for row in r['timeline']:
            row['hint_in']=node['hint_in'];row['entry_review']=node['review']
            row['gate_event']=raw['gate_events'][node['gate_event']] if 'gate_event' in node else None
            for value in (row['hint_in'],row['hint_id']):
                if value is not None:ids.add(value)
            if row['key'] is not None:node=next(c['tree'] for c in node['children'] if c['key']==row['key'])
        r['hints']=[h for h in r['hints'] if h['id'] in ids]
        for k in ('semantic_sha256','gate_weights','gate_features','stochastic','limits'):r[k]=raw.get(k)
        index=raw['index']
        if index is None:r['index']=None;return
        queries={};counts=collections.Counter()
        for q in index['queries']:
            key=canonical(q).decode();queries.setdefault(key,q);counts[key]+=1
        r['index']={k:v for k,v in index.items() if k!='queries'}
        r['index']['queries']=[dict(q,occurrences=counts[k]) for k,q in queries.items()]
        r['index']['projection_scope']='Every demanded syntax table and distinct actual query with multiplicity. The complete ordered trace remains in the independently replayed raw artifact.'
    for d,raw in zip(out['donors'],data['donors']):enrich(d['result'],raw['result'])
    for c,raw in zip(out['cases'],data['cases']):
        c['timings']=raw['timings']
        for lane,r in c['runs'].items():enrich(r,raw['runs'][lane])
        c['defer_choices_equal_base']={lane:raw['runs'][lane]['placements']==raw['runs']['base']['placements'] and not raw['runs'][lane]['hints'] for lane in ('gate','zero_gate','eager_zero')}
    out['training']={k:v for k,v in data['training'].items() if k not in ('episodes','specs')}
    out['training']['episodes']=[dict(id=i,case=e['spec']['id'],weights_before=e['weights_before'],baseline_after=e['baseline_after'],update=e['update'],
        status=e['result']['status'],total_seconds=e['result']['total_seconds'],limits=e['result']['limits'],metrics=e['result']['metrics'],
        events=[{k:event[k] for k in ('id','features','score','probabilities','draw','selected','gradient')} for event in e['result']['gate_events']]) for i,e in enumerate(data['training']['episodes'])]
    out['training']['projection_scope']='All numeric sampled request events and observed inclusive-time update fields. The source contexts, chosen prefixes, catalogs and full training trees remain in the independently audited raw artifact.'
    out['projection_scope']='Actual positive-leaf original tiles, retained hints, pre-join gate events and reviews; complete demanded syntax tables and distinct queries with multiplicities; all recorded numeric training updates. Full failures and ordered proposal traces remain in the independently replayed compressed artifact.'
    return out
def main():
    path=DOC/'proposal-gate-001.json.gz';data=json.loads(gzip.decompress(path.read_bytes()));audit=json.loads((DOC/'proposal-gate-audit-001.json').read_bytes())
    if audit['status']!='passed' or audit['input_sha256']!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('Exact independent audit binding required')
    for n,pin in data['sources'].items():
        if hashlib.sha256((HERE/n).read_bytes()).hexdigest()!=pin:raise ValueError('Measured source changed: '+n)
    result=project(data,audit);(DOC/'proposal-gate-reader-001.json').write_bytes(canonical(result)+b'\n')
    print(json.dumps(dict(version=result['version'],cases=[c['spec']['id'] for c in result['cases']],weights=result['training']['weights'],bytes=(DOC/'proposal-gate-reader-001.json').stat().st_size,
        controls=[dict(case=c['spec']['id'],saturation=c['controls']['saturation']['total_seconds'],base=c['timings']['base']['median_seconds']) for c in result['cases']])),flush=True)
if __name__=='__main__':main()
