"""Training-only, one-step geometric endpoint substitutions.

For observations A=(aL,aR), B=(bL,bR) of the same learned base, admit
(aL,bR) when aL is within epsilon of bL OR aR is within epsilon of bR.
Thus one endpoint can be substituted near an observed paired context. There
is no transitive closure and no change to the common-value marking test.
This is a learned hypothesis, not a theorem that unseen connections are valid.
"""
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path
import sys
import time
import numpy as np
from scipy.spatial import cKDTree

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
half=load('half','half-cloud-support.py');cloud=load('cloud','portable-cloud-markings.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def learn(library,radius=None):
    radius=library['markingRadiusAngstrom'] if radius is None else radius
    if not np.isfinite(radius) or radius<0:raise ValueError('Invalid substitution radius')
    motifs=library['motifs']
    groups=defaultdict(list)
    for i,m in enumerate(motifs):groups[m['base']].append(i)
    neighbors=[{i} for i in range(len(motifs))];witnesses=[];checked=0
    for base,ids in sorted(groups.items()):
        for side in range(2):
            buckets=defaultdict(list);features={}
            for i in ids:
                layout,x=half.signature(motifs[i]['cloudM'][side]);buckets[layout].append(i);features[i]=x
            for members in buckets.values():
                tree=cKDTree(np.array([features[i] for i in members]))
                for x,y in sorted(map(tuple,tree.query_pairs(radius+1e-8,p=np.inf,output_type='ndarray'))):
                    i,j=members[x],members[y]
                    if j in neighbors[i]:continue
                    checked+=1
                    fit=cloud.contains(motifs[i]['cloudM'][side],motifs[j]['cloudM'][side],radius)
                    if fit is not None:
                        neighbors[i].add(j);neighbors[j].add(i)
                        witnesses.append(dict(a=i,b=j,side=side,**fit))
    return dict(scope=__doc__,radiusAngstrom=radius,neighbors=[sorted(ns) for ns in neighbors],witnesses=witnesses,
                summary=dict(motifs=len(motifs),bases=len(groups),directedPairs=sum(map(len,neighbors)),
                             coupledPairs=len(motifs),fullCloudChecks=checked),
                limits='Uses training cloud vectors only, without phase, conditions, target contexts or feasibility witnesses. Radius inherited from existing marking tolerance, not selected on developmental outcomes. Finite observed values; not learned anchors/t, complete rotations, proven negatives or growth.')

if __name__=='__main__':
    source,output=map(Path,sys.argv[1:]);start=time.monotonic();result=learn(json.loads(source.read_text()))
    result.update(libraryHash=sha(source),codeHash=sha(__file__),seconds=time.monotonic()-start)
    with output.open('x') as stream:json.dump(result,stream)
    print(json.dumps(dict(**result['summary'],radius=result['radiusAngstrom'],seconds=result['seconds'])))
