"""Acquire pinned public ice coordinates, preserving the author's split.

Export only opaque IDs, species, positions, cell and PBC to the geometry input.
Phase, source conditions, forces, stresses and energies remain outside it.
This is data admission, not a successful GCTS training or growth experiment.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
from ase.io import read

REPO='venkatkapil24/fine-tuning-MLPs-ice-polymorphs'
COMMIT='c9a4bb534b35bfc8f467d7388f3056325bd2dd4e'
def digest(x):return hashlib.sha256(x).hexdigest()
def acquire(out):
    out=Path(out);out.mkdir();configs=[];metadata=[];files=[];seen={};duplicates=[]
    for phase in ('Ih','II','VI','VIII'):
        for split,name in [('train','training-set-energy-forces-stress-400.extxyz'),('test','validation-set-energy-forces-stress.extxyz')]:
            relative=f'dft_data/{phase}/{name}';url=f'https://raw.githubusercontent.com/{REPO}/{COMMIT}/{relative}'
            path=out/f'{phase}-{split}.extxyz'
            subprocess.run(['curl','-fsSL','--max-time','60',url,'-o',str(path)],check=True)
            raw=path.read_bytes();frames=read(path,index=':',format='extxyz');file_sha=digest(raw)
            assert len(frames)==(400 if split=='train' else 100)
            summary={'phase':phase,'split':split,'source':url,'file':path.name,'sha256':file_sha,'frames':len(frames),
                     'atomCounts':dict(Counter(len(a) for a in frames)),'infoKeys':sorted({k for a in frames for k in a.info})}
            for frame,a in enumerate(frames):
                species=a.get_chemical_symbols();positions=np.asarray(a.positions);cell=a.cell.array
                assert set(species)=={'H','O'} and species.count('H')==2*species.count('O')
                assert np.isfinite(positions).all() and np.isfinite(cell).all() and np.linalg.det(cell)>0 and all(a.pbc)
                key=digest(json.dumps([species,positions.tolist(),cell.tolist()],separators=(',',':')).encode())
                if key in seen:duplicates.append({'first':seen[key],'second':[phase,split,frame]})
                else:seen[key]=[phase,split,frame]
                # Shuffle source ordering, deterministically and independently per frame.
                seed=int(hashlib.sha256(f'{file_sha}:{frame}'.encode()).hexdigest()[:16],16)
                order=np.random.default_rng(seed).permutation(len(a));cid=f'c{len(configs):05d}'
                configs.append({'id':cid,'species':[species[i] for i in order],'positions':positions[order].tolist(),
                                'cell':cell.tolist(),'pbc':[bool(x) for x in a.pbc]})
                metadata.append({'id':cid,'phase':phase,'split':split,'sourceFile':path.name,'sourceFrame':frame,
                                 'sourceSha256':file_sha,'geometrySha256':key,'shuffleSeed':seed,
                                 'atoms':len(a),'temperatureK':None,'pressurePa':None,
                                 'conditionStatus':'Paper-linked conditions under review; not asserted from missing frame metadata.',
                                 'independentTrajectoryId':None})
            files.append(summary);print(json.dumps(summary),flush=True)
    (out/'coordinates.json').write_text(json.dumps({'configurations':configs}))
    report={'repository':REPO,'commit':COMMIT,'paper':'https://doi.org/10.1039/D4FD00107A',
            'files':files,'configurations':metadata,'duplicateExactGeometries':duplicates,
            'summary':{'frames':len(configs),'trainingFrames':sum(c['split']=='train' for c in metadata),
                       'testFrames':sum(c['split']=='test' for c in metadata),'atomsAcrossFrames':sum(len(c['species']) for c in configs),
                       'phases':['Ih','II','VI','VIII'],'conditionMatchedAdmission':False},
            'limits':['Author train/validation split is not an independent-trajectory holdout.',
                      'Nested training-size files were not combined; only 400-frame training files were used.',
                      'No repository license was identified in the checked repository metadata; raw coordinates are not republished.',
                      'No GCTS learning, marking or growth result is implied by data admission.']}
    (out/'provenance.json').write_text(json.dumps(report,indent=2));print(json.dumps(report['summary']),flush=True)

if __name__=='__main__':acquire(sys.argv[1])
