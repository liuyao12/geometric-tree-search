"""Exact proof projection plus every cost observation and compact numeric fit."""
import collections,gzip,hashlib,json
from pathlib import Path
from export_resumable_clusters import project as old
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def compact_fit(p):
    value={k:v for k,v in p.items() if k not in ('updates','selection')}
    value['updates']=[dict(epoch=u['epoch'],context=u['context'],score=u['event']['score'],probabilities=u['event']['probabilities'],selected=u['event']['selected'],expected_reward=u['expected_reward'],weights_after=u['weights_after']) for u in p['updates']]
    if 'selection' in p:value['selection']=dict(p['selection'],candidates=[compact_fit(x) for x in p['selection']['candidates']])
    return value
def project(data,audit):
    tr=data['training'];feedback=tr['feedback'];extra=[dict(c,controls={}) for c in feedback]
    source=dict(data,cases=data['cases']+extra,training=dict(seconds=tr['seconds'],weights=tr['policy']['weights'],features=tr['policy']['features'],episodes=[]))
    out=old(source,audit);out['version']='family-router-reader-001'
    def enrich(r,raw):
        node=raw['search_tree'];ids=set()
        for row in r['timeline']:
            row['hint_in']=node['hint_in'];row['entry_review']=node['review']
            for v in (row['hint_in'],row['hint_id']):
                if v is not None:ids.add(v)
            if row['key'] is not None:node=next(c['tree'] for c in node['children'] if c['key']==row['key'])
        r['hints']=[h for h in r['hints'] if h['id'] in ids]
        for k in ('router_event','routing_seconds','limits','semantic_sha256'):r[k]=raw.get(k)
        index=raw['index']
        if index is None:r['index']=None;return
        queries={};counts=collections.Counter()
        for q in index['queries']:
            key=canonical(q).decode();queries.setdefault(key,q);counts[key]+=1
        r['index']={k:v for k,v in index.items() if k!='queries'}
        r['index']['queries']=[dict(q,occurrences=counts[k]) for k,q in queries.items()]
    for d,raw in zip(out['donors'],data['donors']):enrich(d['result'],raw['result'])
    for c,raw in zip(out['cases'],source['cases']):
        c['timings']=raw['timings']
        for lane,r in c['runs'].items():enrich(r,raw['runs'][lane])
        if 'router' in raw['runs']:
            c['whole_controller_equivalence']={lane:raw['runs'][lane]['search_tree']==raw['runs']['fixed' if raw['runs'][lane]['router_event']['selected'] else 'base']['search_tree'] for lane in ('router','zero')}
        else:c.update(context=raw['context'],returns=raw['returns'])
    out['training']=dict(seconds=tr['seconds'],feedback_seconds=tr['feedback_seconds'],fit_seconds=tr['fit_seconds'],policy_sha256=tr['policy_sha256'],policy=compact_fit(tr['policy']),feedback=out['cases'][len(data['cases']):],
        projection_scope='Every paired cold observation and all numeric fitting actions, probabilities, expected returns and resulting weights. Repeated feature bases, before-weights and gradients are reconstructed by the browser; the complete records remain in the independently audited raw archive.')
    out['cases']=out['cases'][:len(data['cases'])];out['recovery']=data.get('recovery');out['timing_scope']=data['timing_scope']
    out['projection_scope']='Actual positive proof leaves, original point values, encountered hints, complete demanded syntax tables and distinct actual queries with multiplicities. Full failed branches and ordered matching traces remain in the compressed primary audit. Training includes its positive certificates and complete observed cold summaries.'
    return out
def main():
    raw=DOC/'family-router-001.json.gz';data=json.loads(gzip.decompress(raw.read_bytes()));audit=json.loads((DOC/'family-router-audit-001.json').read_bytes())
    if audit['status']!='passed' or audit['input_sha256']!=sha(raw):raise ValueError('exact independent audit required')
    for n,pin in data['sources'].items():
        if sha(HERE/n)!=pin:raise ValueError('measured source '+n)
    result=project(data,audit);path=DOC/'family-router-reader-001.json';path.write_bytes(canonical(result)+b'\n');print(json.dumps(dict(status='exported',bytes=path.stat().st_size)),flush=True)
if __name__=='__main__':main()
