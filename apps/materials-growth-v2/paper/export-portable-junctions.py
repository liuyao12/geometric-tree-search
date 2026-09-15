"""Export geometric pair motifs and endpoint cloud markings without target IDs."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

inp,learned,joined,out=map(Path,sys.argv[1:])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=json.loads(inp.read_text());r=json.loads(learned.read_text())['result'];j=json.loads(joined.read_text())
assert j['inputHash']==sha(inp) and j['learningHash']==sha(learned)
base=[]
for typ in d['types']:
    roles=r['roleOfSite'][typ['offset']:typ['offset']+len(typ['positions'])]
    base.append({'kind':typ['kind'],'anchors':typ['positions'],'t':[r['weightsByRole'][u] for u in roles],
                 'scalarM':[r['scalarLabelsByRole'][u] for u in roles]})
motifs=[]
for entry in j['library']:
    typ=d['types'][entry['key'][0]];roles=r['roleOfSite'][typ['offset']:typ['offset']+2]
    delta=np.asarray(entry['vectors'][0]);marks=[]
    for side in range(2):
        indices=[i for i,c in enumerate(entry['colors']) if c[0]==side]
        marks.append({'vectors':[(np.asarray(entry['vectors'][i])-side*delta).tolist() for i in indices],
                      'colors':[entry['colors'][i][1:] for i in indices]})
    motifs.append({'pairType':entry['key'][0],'anchors':[[0.,0.,0.],delta.tolist()],
                   't':[r['weightsByRole'][u] for u in roles],
                   'scalarM':[r['scalarLabelsByRole'][u] for u in roles],
                   'cloudM':marks})
result={'scope':__doc__,'inputHash':sha(inp),'learningHash':sha(learned),'jointGeometryHash':sha(joined),
        'capacity':r['capacity'],'positionToleranceAngstrom':j['epsilonAngstrom'],
        'markingRadiusAngstrom':2*j['epsilonAngstrom'],
        'markingSemantics':'Each assignment is a set of colored displacement clouds within the radius under a bijection; overlapping assignments require a common cloud witness. Rotations act on every vector; translations act on anchors only.',
        'baseMotifs':base,'motifs':motifs,'limits':['Cloud decorations cover only pairs connecting two pair-only junctions. The base catalog is a reference, not an instruction to bypass learned markings using undecorated pairs.',
                                'Decoration applicability in a new configuration is not yet resolved.',
                                'Target registration and a complete continuous-pose candidate generator are not supplied by this export.',
                                'Verification uses numerical Euclidean residuals with declared tolerance, not an exact-real geometric certificate.']}
with out.open('x') as stream:json.dump(result,stream)
print(json.dumps({'baseMotifs':len(base),'portableDecoratedPairs':len(motifs),'markingRadiusAngstrom':result['markingRadiusAngstrom'],'targetIdentifiersInMotifValues':False}))
