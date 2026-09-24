#!/usr/bin/env python3
"""Reproducible Glucose runs, verified witnesses, and optional checked DRUP."""
import argparse,gzip,hashlib,json,pathlib,subprocess,tempfile,time
from engine import Grid,solve

def write_run(row,depth,seconds,out,checker=None):
    path=out/(row['id']+f'-k{depth}.json')
    if path.exists():return json.loads(path.read_text())
    grid=Grid(row['family']);r=solve(grid,grid.from_source(row['cells']),depth,seconds,proof=bool(checker))
    data=r.pop('_data');proof=r.pop('_proof',None)
    r.update(id=row['id'],family=row['family'],cells=row['cells'],expectedHc=row['Hc'],expectedHh=row['Hh'],source=row['source'],solver='Glucose3',outerHolesAllowed=True)
    if proof is not None:
        cnf=f"p cnf {data['variables']} {len(data['clauses'])}\n"+''.join(' '.join(map(str,c))+' 0\n' for c in data['clauses'])
        stem=path.with_suffix('')
        for suffix,content in [('cnf',cnf),('drup',proof)]:
            raw=content.encode();r[suffix+'SHA256']=hashlib.sha256(raw).hexdigest()
            with gzip.GzipFile(str(stem)+'.'+suffix+'.gz','wb',mtime=0) as f:f.write(raw)
        with tempfile.TemporaryDirectory() as tmp:
            a=pathlib.Path(tmp)/'formula.cnf';b=pathlib.Path(tmp)/'proof.drup';a.write_text(cnf);b.write_text(proof)
            start=time.perf_counter();check=subprocess.run([checker,str(a),str(b)],capture_output=True,text=True,timeout=180)
            r['proofVerified']='s VERIFIED' in check.stdout;r['proofCheckSeconds']=time.perf_counter()-start
            pathlib.Path(str(stem)+'.checker.log').write_text(check.stdout+check.stderr)
            assert r['proofVerified'],check.stdout[-2000:]
    path.write_text(json.dumps(r,separators=(',',':')))
    print(json.dumps({k:v for k,v in r.items() if k not in ('witness','cells')}),flush=True)
    return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--ids',default='omino-17-44,omino-17-193,hex-11-19,iamond-20-131');p.add_argument('--seconds',type=float,default=30);p.add_argument('--out',default='data/planar-heesch/runs');p.add_argument('--checker');p.add_argument('--depth',type=int);a=p.parse_args()
    out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
    for row in json.load(open('data/planar-heesch/catalog.json')):
        if row['id'] not in a.ids.split(','):continue
        for k in ([a.depth] if a.depth else [row['Hh'],row['Hh']+1]):write_run(row,k,a.seconds,out,a.checker)
