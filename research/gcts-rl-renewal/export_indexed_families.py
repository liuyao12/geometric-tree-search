"""Audited reader projection, inclusive cold timing samples and real queries."""
import gzip,hashlib,json
from pathlib import Path
from export_resumable_clusters import project as previous
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def project(data,audit):
    out=previous(data,audit);out['version']='indexed-families-reader-001';out['timing_scope']=data['timing_scope']
    def entry_reviews(projected,raw):
        node=raw['search_tree']
        for step in projected['timeline']:
            step['hint_in']=node['hint_in'];step['entry_review']=node['review']
            if step['key'] is not None:node=next(c['tree'] for c in node['children'] if c['key']==step['key'])
    for d,raw in zip(out['donors'],data['donors']):entry_reviews(d['result'],raw['result'])
    for c,raw in zip(out['cases'],data['cases']):
        c['timings']=raw['timings']
        for lane,r in c['runs'].items():
            r['index']=raw['runs'][lane]['index'];r['semantic_sha256']=raw['runs'][lane]['semantic_sha256'];entry_reviews(r,raw['runs'][lane])
        a,b=raw['runs']['indexed'],raw['runs']['rl']
        c['fixed_and_rl_choices_equal']=a['placements']==b['placements'] and a['hints']==b['hints'] and {k:v for k,v in a['metrics'].items() if not k.endswith('seconds')}=={k:v for k,v in b['metrics'].items() if not k.endswith('seconds')}
        if not c['fixed_and_rl_choices_equal']:raise ValueError('assessment must be revised')
    return out
def main():
    path=DOC/'indexed-families-001.json.gz';data=json.loads(gzip.decompress(path.read_bytes()));audit=json.loads((DOC/'indexed-families-audit-001.json').read_bytes())
    if audit['status']!='passed' or audit['input_sha256']!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('exact audit binding')
    (DOC/'indexed-families-reader-001.json').write_bytes(canonical(project(data,audit))+b'\n')
if __name__=='__main__':main()
