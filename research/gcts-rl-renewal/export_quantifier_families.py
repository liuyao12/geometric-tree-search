"""Exact positive-leaf and distinct-query projection of the full audited data."""
import collections,gzip,hashlib,json
from pathlib import Path
from export_resumable_clusters import project as old
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def project(data,audit):
    out=old(data,audit);out['version']='quantifier-families-reader-001';out['timing_scope']=data['timing_scope']
    def enrich(r,raw):
        node=raw['search_tree'];ids=set()
        for row in r['timeline']:
            row['hint_in']=node['hint_in'];row['entry_review']=node['review']
            for v in (row['hint_in'],row['hint_id']):
                if v is not None:ids.add(v)
            if row['key'] is not None:node=next(c['tree'] for c in node['children'] if c['key']==row['key'])
        r['hints']=[h for h in r['hints'] if h['id'] in ids];r['semantic_sha256']=raw.get('semantic_sha256')
        index=raw['index']
        if index is None:r['index']=None;return
        queries={};counts=collections.Counter()
        for q in index['queries']:
            key=canonical(q).decode();queries.setdefault(key,q);counts[key]+=1
        r['index']={k:v for k,v in index.items() if k!='queries'}
        r['index']['queries']=[dict(q,occurrences=counts[k]) for k,q in queries.items()]
        r['index']['projection_scope']='Every demanded syntax table and distinct actual query with its occurrence count. Full ordered query trace remains in the raw audit artifact.'
    for d,raw in zip(out['donors'],data['donors']):enrich(d['result'],raw['result'])
    for c,raw in zip(out['cases'],data['cases']):
        c['timings']=raw['timings']
        for lane,r in c['runs'].items():enrich(r,raw['runs'][lane])
        a,b=raw['runs']['fixed'],raw['runs']['rl'];c['fixed_and_rl_choices_equal']=a['placements']==b['placements'] and a['hints']==b['hints']
        c['rl_and_base_choices_equal']=raw['runs']['base']['placements']==b['placements'] and not b['hints']
    out['projection_scope']='Positive-leaf original tiles, actually encountered hints and reviews, complete demanded syntax tables and distinct queries with exact multiplicities. Full failures, pools, policy events and ordered queries are in the independently replayed raw artifact.'
    return out
def main():
    path=DOC/'quantifier-families-001.json.gz';data=json.loads(gzip.decompress(path.read_bytes()));audit=json.loads((DOC/'quantifier-families-audit-001.json').read_bytes())
    if audit['status']!='passed' or audit['input_sha256']!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('exact independent audit binding')
    (DOC/'quantifier-families-reader-001.json').write_bytes(canonical(project(data,audit))+b'\n')
if __name__=='__main__':main()
