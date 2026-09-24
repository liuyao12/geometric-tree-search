#!/usr/bin/env python3
"""Regenerate and independently re-prove every exclusion before benchmark reuse."""
import argparse,gzip,hashlib,json,subprocess,tempfile,time
from itertools import product
from pathlib import Path
from certify_voxel_obstruction import construct


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input',required=True)
    ap.add_argument('--drat-trim',required=True)
    ap.add_argument('--output',required=True)
    a=ap.parse_args();folder=Path(a.input)
    source=json.loads((folder/'input.json').read_text());summary=json.loads((folder/'summary.json').read_text())
    model=source['model'];known={r['id']:r for r in source['rows']};seen=set();checked=[];begun=time.perf_counter()
    if any(o.get('marks') for o in model['orientations']):raise ValueError('Expected unmarked input')
    radius=summary['radius']
    if type(radius) is not int or not 1<=radius<=10:raise ValueError('Invalid radius')
    for row in summary['rows']:
        if row['id'] in seen or any(row[k]!=known[row['id']][k] for k in ('key','pair','multiplicity')):raise ValueError('Invalid catalogue row')
        seen.add(row['id'])
        if row['status']!='excluded':continue
        occupied={tuple(v[i]+p['translation'][i]//2 for i in range(3)) for p in row['pair'] for v in model['orientations'][p['oi']]['voxels']}
        target=sorted({tuple(v[i]+d[i] for i in range(3)) for v in occupied for d in product(range(-radius,radius+1),repeat=3)})
        data={'model':{**model,'required':[{'pos':[2*x+1 for x in q]} for q in target]},'fixed':row['pair']}
        f,variables,stats=construct(data,amo='sequential')
        cnf=(f'p cnf {f.variables} {len(f.clauses)}\n'+''.join(' '.join(map(str,c))+' 0\n' for c in f.clauses)).encode()
        # Paths come from the enumerated integer ID, never an imported prefix.
        stem=folder/f"pair-{row['id']}"
        if cnf!=gzip.decompress(stem.with_suffix('.cnf.gz').read_bytes()):raise ValueError('Regenerated formula differs')
        proof=gzip.decompress(stem.with_suffix('.drup.gz').read_bytes())
        for name,raw in [('cnfSha256',cnf),('proofSha256',proof)]:
            if hashlib.sha256(raw).hexdigest()!=row['proof'][name]:raise ValueError('Certificate digest mismatch')
        with tempfile.TemporaryDirectory() as tmp:
            cp,pp=Path(tmp)/'formula.cnf',Path(tmp)/'trace.drup';cp.write_bytes(cnf);pp.write_bytes(proof)
            result=subprocess.run([a.drat_trim,str(cp),str(pp),'-t','60'],capture_output=True,text=True,timeout=65)
            if result.returncode or 's VERIFIED' not in result.stdout:raise ValueError('Independent proof replay failed')
        checked.append(row['id'])
    result={'verified':True,'checked':checked,'elapsedMs':(time.perf_counter()-begun)*1000,'summarySha256':hashlib.sha256((folder/'summary.json').read_bytes()).hexdigest()}
    Path(a.output).write_text(json.dumps(result));print(json.dumps(result),flush=True)

if __name__=='__main__':main()
