"""Independent text parsing and exact coordinate-export checks; no ASE parser."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
import numpy as np

def verify(folder):
    folder=Path(folder);d=json.loads((folder/'coordinates.json').read_text());p=json.loads((folder/'provenance.json').read_text())
    byid={c['id']:c for c in d['configurations']};assert len(byid)==len(d['configurations'])==len(p['configurations'])
    parsed={}
    for file in p['files']:
        raw=(folder/file['file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==file['sha256']
        lines=raw.decode().splitlines();i=0;frames=[]
        while i<len(lines):
            if not lines[i].strip():i+=1;continue
            n=int(lines[i]);header=lines[i+1]
            properties=re.search(r'Properties=([^ ]+)',header)[1]
            assert properties in ('species:S:1:pos:R:3:REF_forces:R:3','species:S:1:pos:R:3:forces:R:3')
            cell=np.array(list(map(float,re.search(r'Lattice="([^"]+)"',header)[1].split()))).reshape(3,3,order='F')
            # Extended XYZ stores the three lattice vectors column-major.
            rows=[row.split() for row in lines[i+2:i+2+n]];assert len(rows)==n and all(len(row)==7 for row in rows)
            frames.append(([row[0] for row in rows],np.array([[float(x) for x in row[1:4]] for row in rows]),cell.T))
            assert 'pbc="T T T"' in header;i+=n+2
        assert len(frames)==file['frames'];parsed[file['file']]=frames
    atom_total=0;seen={};duplicates=[];cross_split=[]
    for meta in p['configurations']:
        c=byid[meta['id']];assert set(c)=={'id','species','positions','cell','pbc'}
        species,positions,cell=parsed[meta['sourceFile']][meta['sourceFrame']]
        key=hashlib.sha256(json.dumps([species,positions.tolist(),cell.tolist()],separators=(',',':')).encode()).hexdigest()
        assert key==meta['geometrySha256']
        where=[meta['phase'],meta['split'],meta['sourceFrame']]
        if key in seen:
            record={'first':seen[key],'second':where};duplicates.append(record)
            if seen[key][1]!=where[1]:cross_split.append(record)
        else:seen[key]=where
        order=np.random.default_rng(meta['shuffleSeed']).permutation(len(species))
        assert c['species']==[species[i] for i in order] and np.array_equal(c['positions'],positions[order]) and np.array_equal(c['cell'],cell)
        assert c['pbc']==[True]*3 and len(species)==meta['atoms'] and np.linalg.det(cell)>0
        counts=Counter(species);assert set(counts)=={'O','H'} and counts['H']==2*counts['O']
        assert meta['temperatureK'] is None and meta['pressurePa'] is None and meta['independentTrajectoryId'] is None
        atom_total+=len(species)
    assert atom_total==p['summary']['atomsAcrossFrames']
    assert duplicates==p['duplicateExactGeometries']
    out={'verifiedFrames':len(byid),'verifiedAtomsAcrossFrames':atom_total,'sourceFiles':len(parsed),
         'geometryExportWhitelistPassed':True,'conditionMatchedAdmission':False,
         'duplicateExactGeometries':len(duplicates),'crossSplitExactDuplicates':len(cross_split),
         'duplicateCheckScope':'Exact source atom ordering and coordinates only; not rigid/permutation equivalence or trajectory independence.',
         'learningTested':False,'growthTested':False}
    print(json.dumps(out,indent=2));return out
if __name__=='__main__':
    r=verify(sys.argv[1])
    if len(sys.argv)>2:
        with Path(sys.argv[2]).open('x') as f:json.dump(r,f,indent=2)
