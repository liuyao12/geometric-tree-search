"""Audited discovery -> formula/English/native-square presentation projection."""
import gzip,hashlib,json
from pathlib import Path
from shared_wang_inventory import Inventory
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n):return json.loads(gzip.decompress((DOCS/n).read_bytes()))
def build():
    data=load('native-inventory-001.json.gz');audit=load('native-inventory-audit-001.json.gz');training=load(data['training']['name']);policy=json.loads((DOCS/data['policy']['name']).read_text())
    if audit['producer_sha256']!=sha(DOCS/'native-inventory-001.json.gz') or audit['source_sha256']!=sha(HERE/'audit_native_inventory_policy.py'):raise ValueError('audited bindings')
    micro=load('proof-boundary-microcode-001.json.gz');inv=Inventory(gzip.decompress((DOCS/'proof-boundary-machine-001.bin.gz').read_bytes()));entry=3+4*sum(r is not None for r in micro['rows'][:1688]);transition_rows={}
    def crop(row,cp):
        raw='^'+cp['register_words'][0]+'B'*(row['initial']['capacities'][0]-len(cp['register_words'][0])-1);marker=2+cp['heads'][0];left=max(0,marker-4);width=9;height=3;tape={0:0,1:17,**{2+j:(9 if j==cp['heads'][0] else 1)+'B^01:,;'.index(s) for j,s in enumerate(raw)}};q=entry+3;h=marker;rows=[];trajectory=[]
        for y in range(height+1):
            rows.append([inv.head(q,tape.get(x,1)) if x==h else tape.get(x,1) for x in range(left-1,left+width+1)]);trajectory.append([q,h])
            if y<height:out,w,d=inv.transition(q,tape[h]);tape[h]=w;q=out;h+=d
        tiles=[dict(x=x,y=y,**inv.tile(*rows[y][x:x+3])) for y in range(height) for x in range(width)]
        for t in tiles:
            if t['N']!=rows[t['y']+1][t['x']+1]:raise ValueError('actual native seam')
            for s in t['triple']:
                head=inv.decode(s)
                if head is not None:transition_rows[str(head[0])]=[inv.transition(head[0],a) for a in range(inv.A)]
        return dict(width=width,height=height,left=left,rows=rows,tiles=tiles,trajectory=trajectory,marker=marker,prefix_physical_steps=cp['physical_head']+marker+1,scope='Three actual literal transitions at this proof-line entry. This crop is not the full inference or a searched native-square patch.')

    view=dict(version='native-inventory-reader-001',inventory=data['inventory'],transition_rows=transition_rows,cases=data['cases'],donors=[d['case'] for d in training['donors']],observations=data['observations'],proofs=[],policy=policy,training=dict(episodes=training['episodes'],features=training['features'],rate=training['rate'],weights=training['weights'],baseline=training['baseline'],queries=training['queries'],cold_seconds=training['cold_seconds'],training_seconds=training['training_seconds']),costs=dict(compile_seconds=data['compile_seconds'],production_seconds=data['total_seconds'],audit_seconds=audit['seconds'],training_stage_seconds=data['training_stage_seconds']),audit=dict(status=audit['status'],queries=audit['queries'],micro_steps=audit['micro_steps'],point_nodes=audit['point_nodes'],policy_events=audit['policy_events'],hints=audit['hints'],training=audit['training'],mutations=len(audit['mutations_rejected']),sha256=sha(DOCS/'native-inventory-audit-001.json.gz')),producer_sha256=sha(DOCS/'native-inventory-001.json.gz'),policy_sha256=sha(DOCS/data['policy']['name']),training_sha256=sha(DOCS/data['training']['name']),limits=dict(attempts=2000,seconds=30,proposal_limit=24,proposal_checks=2048,compile_queries=64,micro_steps=10**9),scope=data['scope'])
    for row,checked in zip(data['certificates'],audit['certificates']):
        if row['request_sha256']!=checked['request_sha256']:raise ValueError('checked case order')
        events=[json.loads(v) for v in gzip.decompress((DOCS/row['events']['name']).read_bytes()).splitlines()];cps={e['event']:e for e in events if e['kind']=='checkpoint'};lines=[]
        for l in checked['lines']:
            f=l['fragment'];r=f['response'];lines.append(dict(label=l['label'],input=l['input_context'],output=l['output_context'],outcome=l['outcome'],node=f['node'],micro_steps=r['steps'],physical_height=f['physical_height'],literal_width=f['literal_width'],q=r['q'],out=r['out'],input_head=f['input_head'],output_head=f['output_head'],patch=crop(row,cps[f['from_event']])))
        if row['role']=='inventory_donor':
            donor=next(d for d in training['donors'] if d['case']['id']==row['case_id'])
            trace=dict(**donor,proof=donor['search']['proof'],status='native_proof_discovered',records=training['records'],queries=training['queries'])
        else:
            primary=next(o for o in data['observations'] if o['case']==row['case_id'] and o['mode']=='learned' and o['status']=='native_proof_discovered')
            trace=load(primary['artifact']['name'])
        if trace['proof']!=row['request']['proof']:raise ValueError('actual discovered proof')
        view['proofs'].append(dict(name=row['name'],case=row['case_id'],role=row['role'],request=row['request'],request_sha256=row['request_sha256'],sources=row['sources'],lines=lines,builder=row['builder'],checker=row['checker'],literal=row['literal'],grammar=row['grammar'],events=row['events'],responses=row['responses'],trace=trace))
    return view
if __name__=='__main__':
    v=build();p=DOCS/'native-inventory-reader-001.json';p.write_text(json.dumps(v,separators=(',',':'))+'\n');print(p.name,len(v['proofs']),sum(len(p['lines']) for p in v['proofs']),p.stat().st_size)
