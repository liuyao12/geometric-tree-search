"""Project the actual positive-leaf timeline without inventing search steps."""
import hashlib,json
from pathlib import Path
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def timeline(r):
    if r['proof'] is None or 'hints' not in r:return []
    rows=[];node=r['search_tree']
    for step,key in enumerate(r['placements']):
        child=next(c for c in node['children'] if c['key']==key)
        identity=node.get('hint_start',node['hint_in']);review=node.get('start_review',node['review'])
        rows.append(dict(step=step,key=key,kind=node['kind'],point=node['point'],hint_id=identity,
            phase='started' if 'hint_start' in node else review['phase'],pending=review.get('pending',()),
            eligible=review.get('eligible',()),role=child['role']))
        node=child['tree']
    rows.append(dict(step=len(rows),key=None,kind=node['kind'],point=node['point'],hint_id=node['hint_in'],
        phase=node['review']['phase'],pending=node['review'].get('pending',()),eligible=(),role='terminal'))
    return rows
def project(data,audit):
    def run(r):
        names=('status','placements','tile_generations','proof','endpoint','metrics','seconds','grammar_seconds','total_seconds',
            'positive_check_seconds','tiles','point_check','compact','solution_hints','candidate_universe','weights','mode','seed')
        value={k:r[k] for k in names if k in r};value['timeline']=timeline(r)
        if 'hints' in r:value['hints']=[dict(id=h['id'],chosen=h['chosen'],point=h['point'],item=h['item']) for h in r['hints']]
        return value
    return dict(version='resumable-clusters-reader-001',audit=audit,
        donors=[dict(spec=c['spec'],catalog=c['catalog'],result=run(c['result'])) for c in data['donors']],
        cases=[dict(spec=c['spec'],catalog=c['catalog'],runs={k:run(r) for k,r in c['runs'].items()},
            controls={k:{n:v for n,v in r.items() if n!='region_certificate'} for k,r in c['controls'].items()}) for c in data['cases']],
        library=[dict(name=t['name'],pattern=t['pattern'],level=t['level'],children=t['children'],source_id=t['source']['spec']['id'],source_members=t['source']['members']) for t in data['library']],
        training=dict(seconds=data['training']['seconds'],weights=data['training']['weights'],features=data['training']['features'],
            episodes=[dict(id=i,case=e['spec']['id'],weights_before=e['weights_before'],weights_after=e['update']['weights_after'],
                reward=e['update']['reward'],cost_units=e['update']['cost_units'],attempts=e['result']['metrics']['attempts'],
                policy_events=len(e['result']['policy_events'])) for i,e in enumerate(data['training']['episodes'])]),
        donor_seconds=data['donor_seconds'],seconds=data['seconds'],peak_process_rss_bytes=data['peak_process_rss_bytes'])
def main():
    path=DOC/'resumable-clusters-001.json';data=json.loads(path.read_bytes());audit=json.loads((DOC/'resumable-clusters-audit-001.json').read_bytes())
    if audit['input_sha256']!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('exact audit required')
    (DOC/'resumable-clusters-reader-001.json').write_bytes(canonical(project(data,audit))+b'\n')
if __name__=='__main__':main()
