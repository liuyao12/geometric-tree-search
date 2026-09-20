"""Reference-kernel model with generated, initially dormant latent sites.

Inputs contain no chosen contact cover. All consistency-surviving contact
representatives define a finite site domain; all compatible alignments of
surviving contexts are enumerated. Atom roots are required; selected positive
port supports activate latent sites through the existing kernel.
"""
import hashlib,itertools,json,sys
from pathlib import Path
from collections import defaultdict
import numpy as np
from ase.geometry import find_mic


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    proposalp,coordp,motifp,out=map(Path,sys.argv[1:])
    proposal,coords,motifs=[json.loads(p.read_text()) for p in [proposalp,coordp,motifp]]
    assert proposal['coordinateHash']==sha(coordp) and proposal['motifHash']==sha(motifp)
    cc={c['id']:c for c in coords['configurations']};rr={r['id']:r for r in motifs['rows']};frames=[]
    for row in proposal['rows']:
        cid=row['configuration'];c=cc[cid];cell=np.asarray(c['cell']);inverse=np.linalg.inv(cell)
        points=[];keys={}
        def point(p):
            # Declared finite geometric domain: fractional coordinates rounded
            # to 12 decimals modulo one. This is numerical discretization,
            # not a claim of exact continuous geometry or a physical lattice.
            key=tuple(int(v)%10**12 for v in np.rint((np.asarray(p)@inverse%1)*10**12))
            if key not in keys:
                keys[key]=len(points);points.append(dict(id=f'p{len(points)}',fractionalKey=key,position=(np.asarray(key)/10**12@cell).tolist()))
            return keys[key]
        atoms=[point(p) for p in c['positions']]
        assert len(set(atoms))==len(atoms)
        complete=row['imageBound']['status']=='image-bound-verified' and row['tripleUnknown']==0
        if complete:
            for ei in row['consistency']['contacts']:point(row['contacts'][ei]['position'])
        target=np.asarray([p['position'] for p in points]);candidates=[];alignmentStates=0
        for ci in row.get('consistency',{}).get('candidates',[]):
            context=row['candidates'][ci];supports=[row['supports'][s] for s in context['supports']];domains=[]
            for support in supports:
                delta,_=find_mic(target-np.asarray(support['position']),cell,pbc=True)
                domains.append(np.flatnonzero(np.linalg.norm(delta,axis=1)<=.15+1e-9).tolist())
            for mapping in itertools.product(*domains):
                alignmentStates+=1
                if alignmentStates>100000:
                    complete=False;break
                totals=defaultdict(int);ports=[];marks=[]
                for atom in rr[cid]['clusters'][context['cluster']]['ids']:totals[f'p{atoms[atom]}']+=6
                for si,support,pi in zip(context['supports'],supports,mapping):
                    point_id=f'p{pi}';totals[point_id]+=support['units']
                    ports.append(dict(point=point_id,support=si,value=support['value'],units=support['units']))
                    for channel,v in enumerate(support['value']):marks.append(dict(point=point_id,channel=str(channel),lo=v-.15-1e-9,hi=v+.15+1e-9))
                if max(totals.values())>6:continue
                candidates.append(dict(id=f'c{len(candidates)}',sourceCandidate=ci,context=context['context'],cluster=context['cluster'],
                                       t=[dict(point=p,value=v) for p,v in sorted(totals.items())],m=marks,ports=ports))
            if not complete:break
        frames.append(dict(configuration=cid,capacity=6,required=[f'p{i}' for i in atoms],points=points,candidates=candidates,complete=complete,alignmentStates=alignmentStates))
    result=dict(scope=__doc__,proposalHash=sha(proposalp),coordinateHash=sha(coordp),motifHash=sha(motifp),codeHash=sha(Path(__file__)),frames=frames,
                limits='Known atom sites and original motif partition/poses remain given. Contact consistency preprocessing already uses learned markings; '
                       'an unmarked run on this pool is not an unmarked baseline. Finite contact-representative domain, fractional numerical discretization, '
                       '100000 alignment budget per frame. Interval marking relaxation needs Euclidean-ball replay. No blind growth or continuous completeness.')
    with out.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(dict(frames=len(frames),complete=sum(f['complete'] for f in frames),nonempty=[dict(configuration=f['configuration'],points=len(f['points']),candidates=len(f['candidates'])) for f in frames if f['candidates']])))


if __name__=='__main__':main()
