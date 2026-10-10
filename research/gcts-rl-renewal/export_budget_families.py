"""Exact positive leaves, family expansions and justified attention snapshots."""
import hashlib,json
from pathlib import Path
from budget_family_artifact import load
from export_resumable_clusters import timeline
from serialized_kernel import canonical

HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'

def project(data,audit):
    def run(raw):
        fields=('status','placements','tile_generations','proof','endpoint','metrics','candidate_universe',
            'tiles','root_marks','point_check','compact','seconds','total_seconds','preparation_seconds',
            'positive_check_seconds','limits','semantic_sha256','weights','mode','feature_mode','seed',
            'attention_support','attention_prep_seconds','solution_hints')
        r={k:raw[k] for k in fields if k in raw};r['timeline']=timeline(raw)
        node=raw['search_tree'];ids=set();events=[]
        for row in r['timeline']:
            row.update(hint_in=node['hint_in'],entry_review=node['review'],attention_event=node.get('policy_event'),census=node['census'])
            for identity in (row['hint_in'],row['hint_id']):
                if identity is not None:ids.add(identity)
            if 'policy_event' in node:
                e=raw['policy_events'][node['policy_event']]
                events.append({**{k:v for k,v in e.items() if k!='items'},'items':[{k:v for k,v in item.items() if k not in ('occupancy','marks')} for item in e['items']]})
            if row['key'] is not None:node=next(c['tree'] for c in node['children'] if c['key']==row['key'])
        r['hints']=[h for h in raw['hints'] if h['id'] in ids];r['attention_events']=events
        return r
    training=[]
    for j,e in enumerate(data['training']['episodes']):
        r=e['result'];training.append(dict(id=j,epoch=e['epoch'],training_index=e['training_index'],case=e['spec']['id'],
            status=r['status'],total_seconds=r['total_seconds'],budget_seconds=r['limits']['seconds'],attempts=r['metrics']['attempts'],
            events=len(r['policy_events']),nonempty_events=sum(bool(v['items']) for v in r['policy_events']),family_choices=sum(v['selected']!=0 for v in r['policy_events']),weights_before=e['weights_before'],update=e['update']))
    cases=[];costs={k:0. for k in data['lanes']};equal=[]
    for c in data['cases']:
        for lane in data['lanes']:costs[lane]+=sum(s['total_seconds'] for s in c['timings'][lane]['samples'])
        a,b=c['runs']['families'],c['runs']['rl']
        same=a['placements']==b['placements'] and a['hints']==b['hints']
        if same:equal.append(c['spec']['id'])
        cases.append(dict(spec=c['spec'],catalog=c['catalog'],certificate=c['certificates']['budget'],
            runs={k:run(r) for k,r in c['runs'].items()},timings=c['timings'],
            control={k:v for k,v in c['controls']['saturation'].items() if k!='region_certificate'},fixed_rl_same_choices=same))
    train=data['training']
    return dict(version='budget-families-reader-001',cases=cases,lanes=data['lanes'],limits=data['limits'],audit=audit,
        donors=[dict(spec=d['spec'],catalog=d['catalog'],certificate=d['certificate'],result=run(d['result'])) for d in data['donors']],
        library=[dict(name=t['name'],pattern=t['pattern'],level=t['level'],children=t['children'],source_id=t['source']['spec']['id'],source_members=t['source']['members']) for t in data['library']],
        training=dict(specs=train['specs'],features=train['features'],epochs=train['epochs'],rate=train['rate'],
            initial_weights=train['initial_weights'],weights=train['weights'],baselines=train['baselines'],seconds=train['seconds'],episodes=training,
            initial_baselines={b['spec']['id']:int(b['result']['status']=='finite_exact_proof_region')-__import__('math').log1p(b['result']['total_seconds']/.001)/__import__('math').log1p(b['result']['limits']['seconds']/.001) for b in train['initial_baseline_runs']}),
        donor_seconds=data['donor_seconds'],evaluation_seconds=data['evaluation_seconds'],seconds=data['seconds'],evaluation_observed_seconds=costs,
        first_use_rl_seconds=costs['rl']+data['donor_seconds']+train['seconds'],fixed_rl_same_cases=equal,
        scope=data['scope'],timing_scope=data['timing_scope'],
        projection_scope='Actual positive source/point leaves, completed family expansions, hint reviews, and displayed attention events on those leaves. Full failed branches, complete matching queries and sampled training actions remain in hash-bound raw records. The browser checks the displayed data and training summary algebra; the separate audit replays all primary trees.')

def main():
    path=DOC/'budget-families-001.json';data=load(path);audit=json.loads((DOC/'budget-families-audit-001.json').read_text())
    if audit['status']!='passed' or audit['input_sha256']!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('exact passed audit required')
    (DOC/'budget-families-reader-001.json').write_bytes(canonical(project(data,audit))+b'\n')

if __name__=='__main__':main()
