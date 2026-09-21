#!/usr/bin/env python3
"""Regenerate a voxel pair CNF and check its RUP proof using external DRAT-trim.

Uses no SAT solver or learned marking. Geometry is audited independently of the
point-model compiler; the report states the finite-to-infinite implication.
"""
import argparse,gzip,hashlib,json,subprocess,tempfile,time
from collections import Counter
from itertools import permutations,product
from pathlib import Path
from certify_voxel_obstruction import construct

def need(value,message):
    if not value:raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()
def normalized(cells):
    origin=tuple(min(p[i] for p in cells) for i in range(3))
    return tuple(sorted(tuple(p[i]-origin[i] for i in range(3)) for p in cells)),origin
def rotations():
    for perm in permutations(range(3)):
        sign=(-1)**sum(perm[i]>perm[j] for i in range(3) for j in range(i+1,3))
        for signs in product([-1,1],repeat=3):
            if sign*signs[0]*signs[1]*signs[2]==1:yield perm,signs
def rotate(cells,translation,r):
    perm,signs=r
    return [tuple((signs[i]*(2*p[perm[i]]+1+translation[perm[i]])-1)//2 for i in range(3)) for p in cells]
def weights(cells):
    sums=Counter()
    for p in cells:
        sums[tuple(2*x+1 for x in p)]+=8
        for d in product([0,1],repeat=3):sums[tuple(2*(p[i]+d[i]) for i in range(3))]+=1
    return dict(sums)
def audit_geometry(data,base):
    m=data['model'];need(m['capacity']==8 and m['placementDomain']=={'kind':'scaled_cubic','translationStep':2},'Wrong point domain')
    need(not m.get('allowReflections') and not data.get('pairExclusions') and not data.get('fixed'),'Expected unrestricted proper-rotation pair')
    need(len(base)==len(set(map(tuple,base))) and all(len(p)==3 and all(type(x) is int for x in p) for p in base),'Invalid base geometry')
    orientations=[o['voxels'] for o in m['orientations']]
    expected={normalized(rotate(base,[0,0,0],r))[0] for r in rotations()};actual={normalized(o)[0] for o in orientations}
    need(len(actual)==len(orientations) and actual==expected,'Wrong orientation orbit')
    for o in m['orientations']:
        need(not o.get('marks'),'Learned assignment in certificate')
        observed={tuple(c['pos']):c['weight'] for c in o['cells']}
        need(len(observed)==len(o['cells']) and observed==weights(o['voxels']),'Incorrect center/corner data')
    pair=data['pair'];need(len(pair)==2,'Expected two seed tiles');occupied=[]
    for p in pair:
        need(type(p['oi']) is int and 0<=p['oi']<len(orientations) and len(p['translation'])==3 and all(type(x) is int and x%2==0 for x in p['translation']),'Invalid seed placement')
        occupied.append({tuple(v[i]+p['translation'][i]//2 for i in range(3)) for v in orientations[p['oi']]})
    need(not occupied[0].intersection(occupied[1]),'Pair overlaps before corona check')
    lookup={normalized(o)[0]:(i,normalized(o)[1]) for i,o in enumerate(orientations)};templates=set()
    for r in rotations():
        transformed=[]
        for p in pair:
            shape,origin=normalized(rotate(orientations[p['oi']],p['translation'],r));oi,offset=lookup[shape]
            transformed.append((oi,tuple(2*(origin[i]-offset[i]) for i in range(3))))
        for a,b in [transformed,transformed[::-1]]:templates.add((a[0],b[0],*(b[1][i]-a[1][i] for i in range(3))))
    return {'volume':len(base),'orientations':len(orientations),'properRotations':24,'relativePairSchemas':len(templates)}
def verify(bundle,checker):
    manifest=json.loads((bundle/'manifest.json').read_text())
    for name,digest in manifest['files'].items():need(sha((bundle/name).read_bytes())==digest,'File digest mismatch: '+name)
    raw=(bundle/'pair.input.json').read_bytes();data=json.loads(raw);frontier=json.loads((bundle/'frontier.json').read_text())
    geometry=audit_geometry(data,manifest['voxels'])
    need(frontier['problemSha256']==sha(json.dumps(data,sort_keys=True,separators=(',',':')).encode()),'Wrong frontier context')
    formula,_,stats=construct(data,frontier['frontierPoints'])
    dimacs=(f'p cnf {formula.variables} {len(formula.clauses)}\n'+''.join(' '.join(map(str,c))+' 0\n' for c in formula.clauses)).encode()
    need(sha(dimacs)==manifest['cnfSha256'],'Regenerated formula differs')
    proof=gzip.decompress((bundle/'proof.drup.gz').read_bytes());need(sha(proof)==manifest['proofSha256'],'Proof digest differs')
    start=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='gcts-pair-proof-') as tmp:
        cnf=Path(tmp)/'input.cnf';cnf.write_bytes(dimacs);trace=Path(tmp)/'proof.drup';trace.write_bytes(proof)
        p=subprocess.run([str(checker),str(cnf),str(trace),'-U','-t','60'],text=True,capture_output=True,timeout=70)
        need(p.returncode==0 and 's VERIFIED' in p.stdout,'External RUP checker rejected proof')
    return {'verified':True,'geometry':geometry,'stats':{**stats,'variables':formula.variables,'clauses':len(formula.clauses)},'checkerSeconds':time.monotonic()-start,'proofMethod':'DRAT-trim, RUP-only mode','scope':manifest['scope']}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,required=True);p.add_argument('--checker',type=Path,required=True);p.add_argument('--output',type=Path);a=p.parse_args()
    result=verify(a.bundle,a.checker)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
