"""Training cross-frame coverage under finite tolerance-feasible base self-maps.

Both cloud values rotate with the same proper base transform; endpoint swaps
follow the support permutation. Not independent rotation of individual clouds.
Coverage uses either endpoint, matching the preceding substitution diagnostic.
This is sensitivity analysis only, not an exact symmetry quotient or new search.
"""
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
import sys
import numpy as np
from scipy.spatial import cKDTree
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
cloud=module('cloud','portable-cloud-markings.py');half=module('half','half-cloud-support.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
library_path,maps_path,nearest_path,output=map(Path,sys.argv[1:])
library,maps,nearest=[json.loads(p.read_text()) for p in [library_path,maps_path,nearest_path]]
assert maps['libraryHash']==nearest['libraryHash']==sha(library_path)
radius=library['markingRadiusAngstrom'];motifs=library['motifs'];frames={r['motif']:set(r['sourceFrames']) for r in nearest['results']}
initial={r['motif'] for r in nearest['results'] if r['distanceAngstrom'] is not None and r['distanceAngstrom']<=radius+1e-10}
covered=set(initial);groups=defaultdict(list);witnesses=[];checks=0
for i,m in enumerate(motifs):groups[m['base']].append(i)
for row in maps['results']:
    base=row['base'];ids=groups[base]
    if all(m['numericallyExact'] for m in row['maps']):continue
    buckets=defaultdict(list);features={}
    for i in ids:
        if i in covered:continue
        for side in range(2):
            layout,x=half.signature(motifs[i]['cloudM'][side]);buckets[side,layout].append(i);features[i,side]=x
    trees={key:cKDTree(np.array([features[i,key[0]] for i in members])) for key,members in buckets.items()}
    for pose_index,pose in enumerate(row['maps']):
        if pose['numericallyExact']:continue
        for j in ids:
            transformed=[None,None]
            for source_side,target_side in enumerate(pose['endpointMap']):transformed[target_side]=cloud.transform(motifs[j]['cloudM'][source_side],pose['rotationRow'])
            for side,value in enumerate(transformed):
                layout,x=half.signature(value);key=(side,layout)
                if key not in trees:continue
                for local in trees[key].query_ball_point(x,radius+1e-8,p=np.inf):
                    i=buckets[key][local]
                    if i in covered or frames[i]&frames[j]:continue
                    checks+=1;fit=cloud.contains(motifs[i]['cloudM'][side],value,radius)
                    if fit is not None:
                        covered.add(i);witnesses.append(dict(motif=i,donor=j,base=base,pose=pose_index,endpoint=side,fit=fit))
report=dict(scope=__doc__,libraryHash=sha(library_path),mapsHash=sha(maps_path),nearestHash=sha(nearest_path),codeHash=sha(Path(__file__)),
            summary=dict(contexts=len(motifs),originalCovered=len(initial),additionalCovered=len(covered-initial),totalCovered=len(covered),cloudChecks=checks),
            witnesses=witnesses,limits='Finite Procrustes self-map sensitivity within positional tolerance. Only positive context matches, not search candidates or full reconstructions. No complete continuous-pose, independent-trajectory or physical-condition claim.')
with output.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report['summary']))
