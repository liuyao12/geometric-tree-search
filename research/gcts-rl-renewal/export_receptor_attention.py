"""Actual proof leaves and branch-attention projection of audited traces."""
import hashlib
import json
import math
from pathlib import Path
from receptor_attention_artifact import load
from export_resumable_clusters import timeline
from serialized_kernel import canonical
HERE=Path(__file__).resolve().parent;DOC=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def project(data,audit):
    def run(raw):
        names=('status','placements','tile_generations','proof','endpoint','metrics','seconds','grammar_seconds','total_seconds','worker_setup_seconds',
            'positive_check_seconds','tiles','point_check','compact','solution_hints','candidate_universe','weights','mode','seed','semantic_sha256','attention_support','attention_prep_seconds')
        r={k:raw[k] for k in names if k in raw};r['timeline']=timeline(raw);node=raw['search_tree'];ids=set();events=[]
        for row in r['timeline']:
            row.update(hint_in=node['hint_in'],entry_review=node['review'],attention_event=node.get('policy_event'))
            for value in (row['hint_in'],row['hint_id']):
                if value is not None:ids.add(value)
            if 'policy_event' in node:
                e=raw['policy_events'][node['policy_event']];events.append({**{k:v for k,v in e.items() if k!='items'},
                    'items':[{k:v for k,v in item.items() if k not in ('occupancy','marks')} for item in e['items']]})
            if row['key'] is not None:node=next(c['tree'] for c in node['children'] if c['key']==row['key'])
        r['hints']=[h for h in raw['hints'] if h['id'] in ids];r['attention_events']=events
        r['projection_scope']='Exact positive leaf, reviews and actual attention events on that leaf. Proposal aggregate point values are deterministically reconstructed from original members in this reader; full failed branches, every proposal pool, sampled event and matching query remain in hash-bound raw traces.'
        return r
    training=[]
    for i,e in enumerate(data['training']['episodes']):
        r=e['result'];training.append(dict(id=i,epoch=e['epoch'],training_index=e['training_index'],case=e['spec']['id'],status=r['status'],
            total_seconds=r['total_seconds'],budget_seconds=r['limits']['seconds'],attempts=r['metrics']['attempts'],events=len(r['policy_events']),
            nonempty_events=sum(bool(v['items']) for v in r['policy_events']),family_choices=sum(v['selected']!=0 for v in r['policy_events']),
            weights_before=e['weights_before'],update=e['update']))
    train=data['training'];costs={lane:0.0 for lane in data['lanes']};cases=[]
    for c in data['cases']:
        for lane in data['lanes']:costs[lane]+=sum(s['seconds'] for s in c['timings'][lane]['samples'])
        cases.append(dict(spec=c['spec'],catalog=c['catalog'],runs={lane:run(r) for lane,r in c['runs'].items()},timings=c['timings'],
            controls={k:{n:v for n,v in r.items() if n!='region_certificate'} for k,r in c['controls'].items()}))
    return dict(version='receptor-attention-reader-001',audit=audit,lanes=data['lanes'],budgets=data['budgets'],scope=data['scope'],timing_scope=data['timing_scope'],
        donors=[dict(spec=d['spec'],catalog=d['catalog'],result=run(d['result'])) for d in data['donors']],
        library=[dict(name=t['name'],pattern=t['pattern'],level=t['level'],children=t['children'],source_id=t['source']['spec']['id'],source_members=t['source']['members']) for t in data['library']],
        training=dict(specs=train['specs'],features=train['features'],initial_weights=train['initial_weights'],weights=train['weights'],baselines=train['baselines'],seconds=train['seconds'],episodes=training,
            initial_baselines={b['spec']['id']:int(b['result']['status']=='finite_exact_proof_region')-math.log1p(b['result']['total_seconds']/.001)/math.log1p(b['result']['limits']['seconds']/.001) for b in train['initial_baseline_runs']}),
        cases=cases,
        donor_seconds=data['donor_seconds'],evaluation_seconds=data['evaluation_seconds'],seconds=data['seconds'],evaluation_observed_seconds=costs,
        first_use_attention_seconds=costs['attention']+data['donor_seconds']+train['seconds'])
def main():
    path=DOC/'receptor-attention-001.json';data=load(path);audit=json.loads((DOC/'receptor-attention-audit-001.json').read_text())
    if audit['status']!='passed' or audit['input_sha256']!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('exact independent manifest audit required')
    (DOC/'receptor-attention-reader-001.json').write_bytes(canonical(project(data,audit))+b'\n')
if __name__=='__main__':main()
