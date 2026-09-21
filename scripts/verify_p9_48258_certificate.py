#!/usr/bin/env python3
"""Replay the unmarked p9-48258 grid non-tiling certificate.

Standard-library geometry and RUP checks by default; --checker may select a
separately built DRAT-trim binary. No solver or learned marking is required.
The accompanying report gives the infinite-to-finite projection argument.
"""
import argparse, gzip, hashlib, json, subprocess, tempfile, time
from collections import Counter
from itertools import permutations, product
from pathlib import Path
from certify_voxel_obstruction import construct
from lib.check_rup import RUPChecker

ROOT = Path(__file__).resolve().parents[1]
BASE = [(0,0,2),(0,1,2),(0,2,0),(0,2,1),(0,2,2),(0,2,3),(0,2,4),(0,3,2),(0,4,2)]

def need(condition,message):
    if not condition: raise ValueError(message)

def normalized(voxels):
    origin=tuple(min(p[i] for p in voxels) for i in range(3))
    return tuple(sorted(tuple(p[i]-origin[i] for i in range(3)) for p in voxels)),origin

def rotations():
    for perm in permutations(range(3)):
        parity=(-1)**sum(perm[i]>perm[j] for i in range(3) for j in range(i+1,3))
        for signs in product([-1,1],repeat=3):
            if parity*signs[0]*signs[1]*signs[2]==1: yield perm,signs

def rotate_cells(voxels,translation,rotation):
    perm,signs=rotation
    # Rotate voxel centers, then recover the lower integer corners. This also
    # handles the -1 offset of an interval reflected about the origin.
    return [tuple((signs[i]*(2*p[perm[i]]+1+translation[perm[i]])-1)//2 for i in range(3)) for p in voxels]

def weights(voxels):
    result=Counter()
    for p in voxels:
        result[tuple(2*x+1 for x in p)]+=8
        for d in product([0,1],repeat=3): result[tuple(2*(p[i]+d[i]) for i in range(3))]+=1
    return dict(result)

def audit_geometry(root,pairs):
    model=root['model'];orientations=[list(map(tuple,o['voxels'])) for o in model['orientations']]
    expected={normalized(rotate_cells(BASE,[0,0,0],r))[0] for r in rotations()}
    actual={normalized(o)[0] for o in orientations}
    need(len(orientations)==len(actual)==3 and actual==expected,'Orientation table is not the complete proper rotation orbit')
    need(orientations[0]==BASE,'Wrong root tile')
    for data in [root,*pairs]:
        m=data['model'];need(m['capacity']==8 and m['placementDomain']=={'kind':'scaled_cubic','translationStep':2},'Wrong point/translation domain')
        need(not m['allowReflections'],'Unexpected reflection policy')
        need([o['voxels'] for o in m['orientations']]==[list(map(list,o)) for o in orientations],'Models differ')
        for o in m['orientations']:
            need(not o.get('marks'),'Certificate must not contain learned assignments')
            observed={tuple(c['pos']):c['weight'] for c in o['cells']}
            need(len(observed)==len(o['cells']) and observed==weights(o['voxels']),'Incorrect center/corner point data')
    need(root['fixed']==[{'oi':0,'translation':[0,0,0]}],'Wrong fixed root')
    lookup={normalized(o)[0]:(i,normalized(o)[1]) for i,o in enumerate(orientations)}
    templates=set()
    for data in pairs:
        need('fixed' not in data and not data.get('pairExclusions'),'Local proof must be unmarked and unrestricted')
        pair=data['pair'];need(len(pair)==2,'Wrong pair size')
        occupied=[]
        for p in pair:
            need(all(type(x) is int and x%2==0 for x in p['translation']),'Noninteger translation')
            occupied.append({tuple(v[i]+p['translation'][i]//2 for i in range(3)) for v in orientations[p['oi']]})
        need(not occupied[0].intersection(occupied[1]),'Pair already overlaps')
        for r in rotations():
            transformed=[]
            for p in pair:
                shape,origin=normalized(rotate_cells(orientations[p['oi']],p['translation'],r));oi,offset=lookup[shape]
                transformed.append((oi,tuple(2*(origin[i]-offset[i]) for i in range(3))))
            for a,b in [transformed,transformed[::-1]]:templates.add((a[0],b[0],*(b[1][i]-a[1][i] for i in range(3))))
    declared=set()
    for a,b in root['pairExclusions']:
        need(a['translation']==[0,0,0],'Non-rooted pair schema')
        declared.add((a['oi'],b['oi'],*b['translation']))
    need(len(declared)==len(root['pairExclusions'])==192 and declared==templates,'Symmetry expansion differs from the proved four pairs')
    target=set()
    for p in model['required']:
        q=p['pos']
        if all(x%2 for x in q):target.add(tuple((x-1)//2 for x in q))
        else:
            need(all(x%2==0 for x in q),'Mixed target parity')
            target.update(tuple(q[i]//2+d[i] for i in range(3)) for d in product([-1,0],repeat=3))
    need(target==set(product(range(-3,4),range(-1,6),range(-1,6))),'Wrong rooted 7-cube target')
    return {'orientations':3,'properRotations':24,'localPairs':len(pairs),'relativePairSchemas':len(templates),'requiredVoxels':len(target)}

def digest(data):return hashlib.sha256(data).hexdigest()

def verify(bundle,checker=None):
    manifest=json.loads((bundle/'manifest.json').read_text())
    for name,sha in manifest['files'].items():need(digest((bundle/name).read_bytes())==sha,'File digest mismatch: '+name)
    inputs={name:json.loads((bundle/(name+'.input.json')).read_text()) for name in manifest['cases']}
    geometry=audit_geometry(inputs['root-window'],[v for k,v in inputs.items() if k!='root-window'])
    rows=[]
    for name,data in inputs.items():
        started=time.monotonic();receipt=json.loads((bundle/(name+'.json')).read_text())
        need(digest((bundle/(name+'.input.json')).read_bytes())==receipt['inputSha256'],'Input digest mismatch')
        frontier=json.loads((bundle/(name+'.frontier.json')).read_text()) if name!='root-window' else None
        if frontier:need(frontier['problemSha256']==digest(json.dumps(data,sort_keys=True,separators=(',',':')).encode()),'Wrong frontier context')
        formula,_,stats=construct(data,frontier['frontierPoints'] if frontier else None)
        dimacs=(f'p cnf {formula.variables} {len(formula.clauses)}\n'+''.join(' '.join(map(str,c))+' 0\n' for c in formula.clauses)).encode()
        stored=gzip.decompress((bundle/(name+'.cnf.gz')).read_bytes());proof=gzip.decompress((bundle/(name+'.drup.gz')).read_bytes())
        need(dimacs==stored and digest(stored)==receipt['cnfSha256'],'Formula regeneration mismatch')
        need(digest(proof)==receipt['proofSha256'],'Proof digest mismatch')
        if checker:
            with tempfile.TemporaryDirectory(prefix='gcts-proof-') as tmp:
                cnf=Path(tmp)/'input.cnf';cnf.write_bytes(stored);trace=Path(tmp)/'proof.drup';trace.write_bytes(proof)
                p=subprocess.run([str(checker),str(cnf),str(trace),'-t','60'],text=True,capture_output=True,timeout=70)
                need(p.returncode==0 and 's VERIFIED' in p.stdout,'External proof checker rejected '+name)
                check={'verified':True,'method':'external DRAT-trim'}
        else:check=RUPChecker(formula.clauses).verify(proof.decode().splitlines())
        row={'case':name,**stats,'proofCheck':check,'seconds':time.monotonic()-started};rows.append(row);print(json.dumps(row),flush=True)
    return {'verified':True,'geometry':geometry,'cases':rows,'scope':manifest['scope']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--bundle',type=Path,default=ROOT/'data/p9-48258-grid-obstruction');p.add_argument('--checker',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    result=verify(a.bundle,a.checker)
    if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'verified':True,'geometry':result['geometry'],'scope':result['scope']}),flush=True)
