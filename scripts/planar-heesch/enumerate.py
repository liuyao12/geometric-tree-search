#!/usr/bin/env python3
"""Complete small free-polyform census, bounded classification with receipts."""
import argparse,collections,hashlib,json,pathlib,time
from engine import Grid,enumerate_free,periodic
from run import write_run
p=argparse.ArgumentParser();p.add_argument('--family',required=True,choices=['omino','hex','iamond']);p.add_argument('--size',required=True,type=int);p.add_argument('--seconds',type=float,default=2);p.add_argument('--depth',type=int,default=4);p.add_argument('--checker');a=p.parse_args()
out=pathlib.Path('data/planar-heesch/census');out.mkdir(parents=True,exist_ok=True)
g=Grid(a.family);shapes,counts=enumerate_free(g,a.size);published=json.load(open('data/planar-heesch/catalog.json'))
lookup={g.orientations(g.from_source(r['cells']))[0]:r for r in published if r['family']==a.family and r['size']==a.size}
summary=dict(family=a.family,size=a.size,counts=counts,rows=[])
for index,shape in enumerate(shapes):
    sid=f'{a.family}-{a.size}-enum-{index+1}';path=out/(sid+'.json')
    if path.exists():r=json.loads(path.read_text())
    else:
        start=time.perf_counter();cert=periodic(g,shape);r=dict(id=sid,cells=shape,publishedId=lookup.get(shape,{}).get('id'))
        if cert:r.update(status='periodic',certificate=cert)
        else:
            src=[(3*x+s,3*y+s) if a.family=='iamond' else (x,y) for x,y,s in shape]
            row=dict(id=sid,family=a.family,cells=src,Hc=lookup.get(shape,{}).get('Hc'),Hh=lookup.get(shape,{}).get('Hh'),source=lookup.get(shape,{}).get('source'))
            r.update(status='unknown',lowerBound=0,runs=[])
            for k in range(1,a.depth+1):
                result=write_run(row,k,a.seconds,out,a.checker);r['runs'].append(f'{sid}-k{k}.json')
                if result['status']=='SAT':
                    r['lowerBound']=k
                    if result['witness']['holeFree']:r['holeFreeLowerBound']=k
                elif result['status']=='UNSAT':
                    r.update(status='finite',Hh=k-1,proofVerified=result.get('proofVerified',False));break
                else:break
        r['seconds']=time.perf_counter()-start;path.write_text(json.dumps(r))
    summary['rows'].append(r);summary['classification']=dict(collections.Counter(x['status'] for x in summary['rows']))
    (out/f'{a.family}-{a.size}-summary.json').write_text(json.dumps(summary))
    print(index+1,len(shapes),summary['classification'],flush=True)
