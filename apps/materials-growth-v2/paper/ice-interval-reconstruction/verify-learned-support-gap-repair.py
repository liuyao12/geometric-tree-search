"""Independent source-coordinate replay of frozen plus replacement motifs."""
import hashlib,itertools,json
from collections import defaultdict,Counter
from fractions import Fraction
from pathlib import Path
import sys
import numpy as np
from scipy.spatial import cKDTree
args=sys.argv[1:];search_mode=args[0]=='--search'
if search_mode:
    coordp,supportp,poolp,repairp,out=map(Path,args[1:])
else:coordp,supportp,repairp,out=map(Path,args)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
coords,support,repair=[json.loads(p.read_text()) for p in [coordp,supportp,repairp]]
if search_mode:
    pool=json.loads(poolp.read_text());assert repair['poolHash']==sha(poolp)
    models={r['id']:r for r in pool['models']};rows=[]
    for run in repair['results']:
        assert (run['status']=='complete')==run['complete']
        entry=models[run['id']];selected=run['selected']
        assert len(selected)==len(set(selected)) and set(entry['model']['initial'])<=set(selected)
        candidates={p['id']:p for p in entry['model']['candidates']}
        for key in selected:
            p=entry['geometry'][key]
            assert candidates[key]['t']==[dict(point=f'a:{a}',value=v) for a,v in zip(p['ids'],p['units'])]
        rows.append(dict(id=run['id'],status='unmarked-filling-awaiting-replay' if run['complete'] else 'unmarked-partial-awaiting-replay',searchStatus=run['status'],fixed=[entry['geometry'][k] for k in selected if k in entry['model']['initial']],added=[entry['geometry'][k] for k in selected if k not in entry['model']['initial']]))
    repair=dict(sourceHashes=pool['sourceHashes'],rows=rows)
assert repair['sourceHashes'][coordp.name]==sha(coordp) and repair['sourceHashes'][supportp.name]==sha(supportp)
cc={c['id']:c for c in coords['configurations']};groups=defaultdict(list)
for a in support['anchors']:groups[a['type']].append(a)
rows=[]
for result in repair['rows']:
    if result['status'] not in ['unmarked-filling-awaiting-replay','unmarked-partial-awaiting-replay']:continue
    c=cc[result['id']];cell=np.asarray(c['cell']);inv=np.linalg.inv(cell);tol=support['positionTolerance']
    assert np.linalg.svd(cell,compute_uv=False)[-1]>tol
    pos=(np.asarray(c['positions'])@inv%1)@cell;shifts=np.asarray(list(itertools.product([-1,0,1],repeat=3)))@cell
    clouds=(pos[:,None,:]+shifts[None,:,:]).reshape(-1,3);tree=cKDTree(clouds)
    totals=[Fraction(0) for _ in pos];maximum=0.;seen=set();maps=Counter()
    placements=result['fixed']+result['added']
    for p in placements:
        aa=groups[p['type']];assert aa
        R=np.asarray(p['rotationRow']);tr=np.asarray(p['translation'])
        assert abs(np.linalg.det(R)-1)<1e-8 and np.max(np.abs(R.T@R-np.eye(3)))<1e-8
        identity=(p['type'],tuple(R.ravel()),tuple(tr));assert identity not in seen;seen.add(identity)
        assigned=[]
        for a,expected,units in zip(aa,p['ids'],p['units'],strict=True):
            w=Fraction(a['t']).limit_denominator(1000000);assert 0<w<=1 and 2*w==units
            x=((np.asarray(a['position'])@R+tr)@inv%1)@cell
            hits=[j for j in tree.query_ball_point(x,tol+1e-9) if c['species'][j//27]==a['species']]
            assert len(hits)==1;atom=hits[0]//27;assert atom==expected
            assigned.append(atom);totals[atom]+=w;maximum=max(maximum,float(np.linalg.norm(clouds[hits[0]]-x)))
        assert len(set(assigned))==len(assigned);maps[p['type'],tuple(assigned)]+=1
    assert all(0<=v<=1 for v in totals),(result['id'],Counter(totals))
    complete=all(v==1 for v in totals)
    if result['status']=='unmarked-filling-awaiting-replay':assert complete,(result['id'],Counter(totals))
    rows.append(dict(id=result['id'],atoms=len(pos),placements=len(placements),fixedPlacements=len(result['fixed']),addedPlacements=len(result['added']),
                     complete=complete,searchStatus=result.get('searchStatus'),fullyFilled=sum(v==1 for v in totals),partiallyFilled=sum(0<v<1 for v in totals),untouched=sum(v==0 for v in totals),maxPositionErrorAngstrom=maximum,duplicateTypeCorrespondences=sum(v-1 for v in maps.values() if v>1)))
report=dict(repairHash=sha(repairp),poolHash=sha(poolp) if search_mode else None,supportHash=sha(supportp),verifierHash=sha(Path(__file__)),rows=rows,
            limits='Independent exact rational t filling and tolerance-based proper-pose replay. Distinct supplied rigid placements; repeated type/correspondence counts reported separately. Does not independently certify the scheduler trace. No marking check, pose-universe completeness or blind-growth claim.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(rows))
