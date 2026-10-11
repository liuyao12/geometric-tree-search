"""Audited discovery -> formula/English/native-square presentation projection."""
import gzip,hashlib,json
from pathlib import Path
from shared_wang_inventory import Inventory
HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n):return json.loads(gzip.decompress((DOCS/n).read_bytes()))
def build():
    data=load('certificate-boundary-001.json.gz');audit=load('certificate-boundary-audit-001.json.gz')
    if audit['producer_sha256']!=sha(DOCS/'certificate-boundary-001.json.gz') or audit['source_sha256']!=sha(HERE/'audit_certificate_boundary.py'):raise ValueError('audited bindings')
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
    view=dict(version='certificate-boundary-reader-001',inventory=data['inventory'],transition_rows=transition_rows,cases=data['cases'],observations=data['observations'],proofs=[],costs=dict(compile_seconds=data['compile_seconds'],production_seconds=data['total_seconds'],audit_seconds=audit['seconds']),audit=dict(status=audit['status'],queries=audit['queries'],micro_steps=audit['micro_steps'],mutations=len(audit['mutations_rejected']),sha256=sha(DOCS/'certificate-boundary-audit-001.json.gz')),producer_sha256=sha(DOCS/'certificate-boundary-001.json.gz'),limits=data['limits'],scope=data['scope'])
    for row,checked in zip(data['certificates'],audit['certificates']):
        if row['request_sha256']!=checked['request_sha256']:raise ValueError('checked case order')
        events=[json.loads(v) for v in gzip.decompress((DOCS/row['events']['name']).read_bytes()).splitlines()];cps={e['event']:e for e in events if e['kind']=='checkpoint'};lines=[]
        for l in checked['lines']:
            f=l['fragment'];r=f['response'];lines.append(dict(label=l['label'],input=l['input_context'],output=l['output_context'],outcome=l['outcome'],node=f['node'],micro_steps=r['steps'],physical_height=f['physical_height'],literal_width=f['literal_width'],q=r['q'],out=r['out'],input_head=f['input_head'],output_head=f['output_head'],patch=crop(row,cps[f['from_event']])))
        case=next(o['case'] for o in data['observations'] if o['found'] and o['artifact']['name'].removeprefix('certificate-boundary-001-').removesuffix('.json.gz') in row['sources'])
        primary=next(o for o in data['observations'] if o['case']==case and o['mode']=='prefix' and o['repetition']==1);trace=load(primary['artifact']['name'])
        view['proofs'].append(dict(name=row['name'],case=case,request=row['request'],request_sha256=row['request_sha256'],sources=row['sources'],lines=lines,builder=row['builder'],checker=row['checker'],literal=row['literal'],grammar=row['grammar'],events=row['events'],responses=row['responses'],trace=trace))
    return view
if __name__=='__main__':
    v=build();p=DOCS/'certificate-boundary-reader-001.json';p.write_text(json.dumps(v,separators=(',',':'))+'\n');print(p.name,len(v['proofs']),sum(len(p['lines']) for p in v['proofs']),p.stat().st_size)
