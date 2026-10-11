"""Project independently derived native scopes into a compact human reader."""
import copy,gzip,hashlib,json
from pathlib import Path
from shared_wang_inventory import Inventory
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n):return json.loads(gzip.decompress((DOCS/n).read_bytes()))
def same(a,b):return json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True)

def build():
    data=load('semantic-inventory-001.json.gz');audit=load('semantic-inventory-audit-001.json.gz')
    training=load(data['training']['name']);policy=json.loads((DOCS/data['policy']['name']).read_text())
    if audit['status']!='passed' or audit['producer_sha256']!=sha(DOCS/'semantic-inventory-001.json.gz') or audit['source_sha256']!=sha(HERE/'audit_semantic_inventory.py'):raise ValueError('independently audited bindings')
    micro=load('proof-boundary-microcode-001.json.gz');inv=Inventory(gzip.decompress((DOCS/'proof-boundary-machine-001.bin.gz').read_bytes()))
    entry=3+4*sum(r is not None for r in micro['rows'][:1688]);transition_rows={}
    def crop(row,cp):
        raw='^'+cp['register_words'][0]+'B'*(row['initial']['capacities'][0]-len(cp['register_words'][0])-1)
        marker=2+cp['heads'][0];left=max(0,marker-4);width=9;height=3
        tape={0:0,1:17,**{2+j:(9 if j==cp['heads'][0] else 1)+'B^01:,;'.index(s) for j,s in enumerate(raw)}}
        q=entry+3;h=marker;rows=[];trajectory=[]
        for y in range(height+1):
            rows.append([inv.head(q,tape.get(x,1)) if x==h else tape.get(x,1) for x in range(left-1,left+width+1)])
            trajectory.append([q,h])
            if y<height:out,w,d=inv.transition(q,tape[h]);tape[h]=w;q=out;h+=d
        tiles=[dict(x=x,y=y,**inv.tile(*rows[y][x:x+3])) for y in range(height) for x in range(width)]
        for t in tiles:
            if t['N']!=rows[t['y']+1][t['x']+1]:raise ValueError('actual native seam')
            for s in t['triple']:
                head=inv.decode(s)
                if head is not None:transition_rows[str(head[0])]=[inv.transition(head[0],a) for a in range(inv.A)]
        return dict(width=width,height=height,left=left,rows=rows,tiles=tiles,trajectory=trajectory,marker=marker,
            prefix_physical_steps=cp['physical_head']+marker+1,
            scope='Three actual primitive transitions at this native line entry. An entry crop, not the full inference or a square-by-square searched native region.')
    view=dict(version='semantic-inventory-reader-001',inventory=data['inventory'],transition_rows=transition_rows,
        cases=data['cases'],donors=[d['case'] for d in training['donors']],promotion=training['promotion']['case'],
        observations=data['observations'],proofs=[],policy=policy,first_decisions=[],
        training=dict(features=training['features'],rate=training['rate'],weights=training['weights'],baseline=training['baseline'],
            queries=training['queries'],cold_seconds=training['cold_seconds'],discovery_seconds=training['discovery_seconds'],
            training_seconds=training['training_seconds'],episodes=[]),
        costs=dict(compile_seconds=data['compile_seconds'],production_seconds=data['total_seconds'],audit_seconds=audit['seconds'],
                   training_stage_seconds=data['training_stage_seconds']),
        audit={k:audit[k] for k in ('status','queries','micro_steps','point_nodes','policy_events','hints','training','finite_equivalence')},
        producer_sha256=sha(DOCS/'semantic-inventory-001.json.gz'),audit_sha256=sha(DOCS/'semantic-inventory-audit-001.json.gz'),
        policy_sha256=sha(DOCS/data['policy']['name']),training_sha256=sha(DOCS/data['training']['name']),
        source_closure_sha256=sha(DOCS/'semantic-inventory-source-closure-001.json'),scope=data['scope'])
    view['audit']['mutations']=len(audit['mutations_rejected'])
    for case in ('renamed-five','renamed-six'):
        for mode in ('fixed','learned'):
            observation=next(o for o in data['observations'] if o['case']==case and o['mode']==mode and o['repetition']==1)
            raw=load(observation['artifact']['name'])
            view['first_decisions'].append(dict(case=case,mode=mode,source=observation['artifact'],event=raw['search']['events'][0]))
    for episode in training['episodes']:
        e={k:copy.deepcopy(v) for k,v in episode.items() if k!='search'}
        e['search']={k:episode['search'][k] for k in ('status','mode','seed','stochastic','limits','weights','metrics','seconds','events','hints','proof')}
        # The reward's base obligations are computed from the recorded registry.
        registry=training['registries'][e['case']];defs={d['name']:d for d in registry['definitions']}
        e['arity']=max([len(defs[n]['definition']['premises']) for n in registry['interfaces']]+[0])
        view['training']['episodes'].append(e)
    for row,checked in zip(data['certificates'],audit['certificates']):
        if row['request_sha256']!=checked['request_sha256']:raise ValueError('checked certificate order')
        events=[json.loads(v) for v in gzip.decompress((DOCS/row['events']['name']).read_bytes()).splitlines()]
        cps={e['event']:e for e in events if e['kind']=='checkpoint'};lines=[]
        for line in checked['lines']:
            f=line['fragment'];r=f['response']
            lines.append(dict(label=line['label'],input=line['input_context'],output=line['output_context'],outcome=line['outcome'],
                node=f['node'],micro_steps=r['steps'],physical_height=f['physical_height'],literal_width=f['literal_width'],q=r['q'],out=r['out'],
                input_head=f['input_head'],output_head=f['output_head'],patch=crop(row,cps[f['from_event']])))
        if row['role']=='primitive_inventory_donor':
            donor=next(d for d in training['donors'] if d['case']['id']==row['case_id'])
            raw=dict(**donor,proof=donor['search']['proof'],mode='base',inventory=None,
                status='native_proof_discovered',records=training['records']);source=data['training']
        elif row['role']=='higher_inventory_donor':
            promoted=training['promotion'];raw=dict(**promoted,proof=promoted['search']['proof'],mode='fixed',
                status='native_proof_discovered',records=training['records']);source=data['training']
        else:
            name='semantic-inventory-001-'+row['sources'][0]+'.json.gz'
            observation=next(o for o in data['observations'] if o['artifact']['name']==name)
            raw=load(name);source=observation['artifact']
        if not same(raw['proof'],row['request']['proof']) or not same(raw['records'][raw['verification_query']]['request'],row['request']):raise ValueError('actual searched proof')
        model=raw['model'];selected={tuple(k) for k in raw['search']['placements']}
        points=[c for c in model['placements'] if tuple(c['key']) in selected]
        path_events=[e for e in raw['search'].get('events',[]) if raw['search']['placements'][:len(e['chosen'])]==e['chosen']]
        trace=dict(case=raw['case'],mode=raw['mode'],status=raw['status'],proof=raw['proof'],source=source,
            inventory=raw['inventory'],selected=points,roots=model['roots'],arity=model.get('arity',0),
            metrics=raw['search'].get('metrics'),seconds=raw['search']['seconds'],path_events=path_events,
            placements=raw['search']['placements'],root_restored=raw['search'].get('root_restored'),
            verification_query=raw['verification_query'],verification=raw['records'][raw['verification_query']])
        view['proofs'].append(dict(name=row['name'],case=row['case_id'],role=row['role'],request=row['request'],
            request_sha256=row['request_sha256'],sources=row['sources'],lines=lines,builder=row['builder'],checker=row['checker'],literal=row['literal'],
            grammar=row['grammar'],events=row['events'],responses=row['responses'],trace=trace))
    return view
if __name__=='__main__':
    v=build();p=DOCS/'semantic-inventory-reader-001.json'
    p.write_text(json.dumps(v,separators=(',',':'))+'\n')
    print(p.name,len(v['proofs']),sum(len(p['lines']) for p in v['proofs']),p.stat().st_size)
