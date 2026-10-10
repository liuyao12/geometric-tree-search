"""Presentation projection of the audited per-inference fragment controls."""
import gzip,json,hashlib
from pathlib import Path
from shared_wang_inventory import Inventory

HERE=Path(__file__).resolve().parent;DOCS=HERE.parents[1]/'docs/research/gcts-rl-renewal'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def build():
    data=json.loads(gzip.decompress((DOCS/'logical-wang-clusters-001.json.gz').read_bytes()))
    audit=json.loads(gzip.decompress((DOCS/'logical-wang-clusters-audit-001.json.gz').read_bytes()))
    if audit['input_sha256']!=digest(DOCS/'logical-wang-clusters-001.json.gz'):raise ValueError('audited input')
    if audit['source_sha256']!=digest(HERE/'audit_logical_wang_clusters.py'):raise ValueError('audit source')
    shared=json.loads((DOCS/'shared-wang-reader-001.json').read_text())
    micro=json.loads(gzip.decompress((DOCS/'proof-boundary-microcode-001.json.gz').read_bytes()))
    inv=Inventory(gzip.decompress((DOCS/'proof-boundary-machine-001.bin.gz').read_bytes()))
    entry=3+4*sum(r is not None for r in micro['rows'][:1688]);start=entry+3
    if micro['rows'][1688][0]!=0:raise ValueError('entry stub tape')
    transition_rows={}
    def crop(row,cp):
        raw='^'+cp['register_words'][0]+'B'*(row['initial']['capacities'][0]-len(cp['register_words'][0])-1)
        marker=2+cp['heads'][0];left=max(0,marker-4);width=9;height=3
        tape={0:0,1:17,**{2+j:(9 if j==cp['heads'][0] else 1)+'B^01:,;'.index(s) for j,s in enumerate(raw)}}
        q=start;h=marker;rows=[];trajectory=[]
        for y in range(height+1):
            rows.append([inv.head(q,tape.get(x,1)) if x==h else tape.get(x,1) for x in range(left-1,left+width+1)])
            trajectory.append([q,h])
            if y<height:
                out,w,d=inv.transition(q,tape[h]);tape[h]=w;q=out;h+=d
        tiles=[dict(x=x,y=y,**inv.tile(*rows[y][x:x+3])) for y in range(height) for x in range(width)]
        for t in tiles:
            if t['N']!=rows[t['y']+1][t['x']+1]:raise ValueError('actual literal seam')
            for symbol in t['triple']:
                head=inv.decode(symbol)
                if head is not None and str(head[0]) not in transition_rows:
                    transition_rows[str(head[0])]=[inv.transition(head[0],s) for s in range(inv.A)]
        return dict(width=width,height=height,left=left,rows=rows,tiles=tiles,trajectory=trajectory,
            marker=marker,prefix_physical_steps=cp['physical_head']+marker+1,
            scope='three actual literal transitions at the first entry-stub read of this line; cropped lateral context; not the entire inference cluster')
    view=dict(version='logical-wang-clusters-reader-001',inventory=shared['inventory'],cases=[],transition_rows=transition_rows,
        audit=dict(status='passed',sha256=digest(DOCS/'logical-wang-clusters-audit-001.json.gz'),
            seconds=audit['seconds'],checked_rules=audit['checked_rules'],mutations=len(audit['mutations_rejected'])),
        production_seconds=data['total_seconds'],source_sha256=digest(DOCS/'logical-wang-clusters-001.json.gz'))
    for row,result in zip(data['cases'],audit['cases']):
        if row['name']!=result['name']:raise ValueError('case order')
        events=[json.loads(v) for v in gzip.decompress((DOCS/row['events']['name']).read_bytes()).splitlines()]
        cps={e['event']:e for e in events if e['kind']=='checkpoint'}
        lines=[]
        for line in result['lines']:
            f=line['fragment'];r=f['response'];i=f['from_event'];cp=cps[i]
            lines.append(dict(label=line['label'],input=line['input_context'],output=line['output_context'],outcome=line['outcome'],
                node=f['node'],micro_steps=r['steps'],physical_height=f['physical_height'],literal_width=f['literal_width'],
                q=r['q'],out=r['out'],input_head=f['input_head'],output_head=f['output_head'],
                pre_intervals=sum(len(b['pre']) for b in r['bands']),write_intervals=sum(len(b['writes']) for b in r['bands']),
                bands=[dict(tape=b['tape'],shift=b['shift'],extent=b['extent'],pre=len(b['pre']),writes=len(b['writes'])) for b in r['bands']],
                patch=crop(row,cp)))
        view['cases'].append(dict(name=row['name'],request=row['request'],target=row['request']['target'],
            result=result['result'],lines=lines,contexts=result['contexts'],fragments=result['fragments'],
            provenance=row['provenance'],builder=row['builder'],checker=row['checker'],
            grammar=row['grammar'],events=row['events'],responses=row['responses']))
    return view
def main():
    view=build();path=DOCS/'logical-wang-clusters-reader-001.json';path.write_text(json.dumps(view,separators=(',',':'))+'\n')
    print(path.name,len(view['cases']),sum(len(p['lines']) for p in view['cases']),'line instances',path.stat().st_size,'bytes')
if __name__=='__main__':main()
