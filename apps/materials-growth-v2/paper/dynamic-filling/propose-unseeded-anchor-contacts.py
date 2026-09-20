"""Shared-anchor contact domains without successful-assembly target sites.

All evaluation frames, frozen context library and original atom-valid poses.
Ports are candidate alternatives, NOT assumed jointly present. Enumerate
weight-compatible pairs/triples with common position and marking balls.
These contacts are hypotheses, not independent geometric point IDs or a cover.
"""
import hashlib,importlib.util,itertools,json,sys
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction
import numpy as np
from scipy.spatial import cKDTree
from ase.geometry import find_mic,minkowski_reduce


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def nearby(P,cell,radius=.30):
    reduced,_=minkowski_reduce(cell)
    reduced=np.asarray(reduced)
    wrapped=(np.asarray(P)@np.linalg.inv(reduced)%1)@reduced
    span=float(np.linalg.norm(np.ptp(wrapped,axis=0)))
    sigma=float(np.linalg.svd(reduced,compute_uv=False)[-1])
    shell=max(1,int(np.floor((span+radius)/sigma)))
    assert (shell+1)*sigma-span>radius
    shifts=np.asarray(list(itertools.product(range(-shell,shell+1),repeat=3)))@reduced
    if len(shifts)*len(P)>2000000:
        return None,dict(status='unknown-image-budget',shell=shell,replicatedPoints=len(shifts)*len(P))
    images=(wrapped[None,:,:]+shifts[:,None,:]).reshape(-1,3)
    tree=cKDTree(images);pairs=set()
    for i,point in enumerate(wrapped):
        for index in tree.query_ball_point(point,radius+1e-9):
            j=index%len(P)
            if i<j:pairs.add((i,j))
    return sorted(pairs),dict(status='image-bound-verified',shell=shell,margin=(shell+1)*sigma-span-radius)


def prune_contacts(candidates,supports,contacts):
    """Necessary consistency under one context per given motif occurrence."""
    owners=defaultdict(set)
    for ci,c in enumerate(candidates):
        for s in c['supports']:owners[s].add(ci)
    possibilities=[]
    for contact in contacts:
        grouped=defaultdict(list)
        for s in contact['supports']:grouped[supports[s]['cluster']].append(s)
        possibilities.append({k:(set.intersection(*(owners[s] for s in ss)),set(ss)) for k,ss in grouped.items()})
    active=set(range(len(candidates)));rounds=0
    while True:
        rounds+=1;covered=defaultdict(set);live=[]
        for ei,poss in enumerate(possibilities):
            allowed={k:ids&active for k,(ids,ss) in poss.items()}
            if not all(allowed.values()):continue
            live.append(ei)
            for k,ids in allowed.items():
                for ci in ids:covered[ci].update(poss[k][1])
        retained={ci for ci in active if set(candidates[ci]['supports'])<=covered[ci]}
        if retained==active:
            return dict(candidates=sorted(active),contacts=live,rounds=rounds,
                        clusters=len({candidates[ci]['cluster'] for ci in active}))
        active=retained


def main():
    coordp,metap,motifp,interfacep,contextp,weightp,out=map(Path,sys.argv[1:])
    coords,meta,motifs,interfaces,inventory,learned=[json.loads(p.read_text()) for p in [coordp,metap,motifp,interfacep,contextp,weightp]]
    assert motifs['coordinateHash']==interfaces['coordinateHash']==sha(coordp)
    assert motifs['metadataHash']==sha(metap) and inventory['interfaceHash']==sha(interfacep)
    ball=load('balls','audit-anchor-neighborhoods.py').common_ball
    cc={r['id']:r for r in coords['configurations']};mm={r['id']:r for r in meta['configurations']}
    weights={(w['context'],w['port']):Fraction(w['t'])*6 for w in learned['weights']}
    types=defaultdict(list)
    for ci,context in enumerate(inventory['contexts']):types[context['baseType']].append(ci)
    rows=[]
    for frame in motifs['rows']:
        if frame['training']:continue
        cid=frame['id'];c=cc[cid];cell=np.asarray(c['cell']);supports=[];keys={};candidates=[]
        for k,cluster in enumerate(frame['clusters']):
            assert cluster['matched']
            R,tr=np.asarray(cluster['fit']['rotationRow']),np.asarray(cluster['fit']['translation'])
            for ci in types[cluster['type']]:
                ids=[]
                for pi,(mi,role) in enumerate(inventory['contexts'][ci]['ports']):
                    units=weights[ci,pi];assert units.denominator==1 and 2<=units<=4
                    key=(k,mi,role,int(units))
                    if key not in keys:
                        keys[key]=len(supports);model=interfaces['models'][mi]
                        supports.append(dict(cluster=k,interface=mi,role=role,units=int(units),
                                             position=(np.asarray(model['anchor'+role])@R+tr).tolist(),
                                             value=(np.asarray(model['value'+role])@R).tolist()))
                    ids.append(keys[key])
                candidates.append(dict(cluster=k,context=ci,supports=ids))
        P=np.asarray([s['position'] for s in supports]);V=np.asarray([s['value'] for s in supports])
        proximity,bound=nearby(P,cell)
        row=dict(configuration=cid,supports=supports,candidates=candidates,imageBound=bound,contacts=[],tripleUnknown=0)
        rows.append(row)
        if proximity is None:continue
        twos=defaultdict(set)
        for i,j in proximity:
            if np.linalg.norm(V[i]-V[j])>.30+1e-9:continue
            d,_=find_mic(P[j]-P[i],cell,pbc=True)
            if supports[i]['units']+supports[j]['units']==6:
                row['contacts'].append(dict(supports=[i,j],position=(P[i]+d/2).tolist(),value=((V[i]+V[j])/2).tolist()))
            if supports[i]['units']==supports[j]['units']==2:
                twos[i].add(j);twos[j].add(i)
        tried=0
        for i in sorted(twos):
            for j in sorted(k for k in twos[i] if k>i):
                for k in sorted(twos[i]&twos[j]):
                    if k<=j:continue
                    tried+=1
                    if tried>100000:
                        row['tripleUnknown']+=1
                        break
                    ids=[i,j,k];delta,_=find_mic(P[ids]-P[i],cell,pbc=True)
                    pos,val=ball(P[i]+delta),ball(V[ids])
                    if pos['status']==val['status']=='common-ball-witness':
                        row['contacts'].append(dict(supports=ids,position=pos['center'],value=val['center']))
                    elif 'diameter-obstruction' not in [pos['status'],val['status']]:row['tripleUnknown']+=1
                if tried>100000:break
            if tried>100000:break
        covered={i for contact in row['contacts'] for i in contact['supports']}
        row['candidatesWithAllPortsSupported']=sum(all(i in covered for i in candidate['supports']) for candidate in candidates)
        row['clustersWithSupportedCandidate']=len({candidate['cluster'] for candidate in candidates if all(i in covered for i in candidate['supports'])})
        row['clusters']=len(frame['clusters'])
        row['consistency']=prune_contacts(candidates,supports,row['contacts'])
        if len(rows)%10==0:print(json.dumps(dict(frames=len(rows),lastSupports=len(supports),lastContacts=len(row['contacts']))),flush=True)
    summary=[]
    for phase in sorted({m['phase'] for m in mm.values()}):
        group=[r for r in rows if mm[r['configuration']]['phase']==phase]
        summary.append(dict(phase=phase,frames=len(group),rawCandidates=sum(len(r['candidates']) for r in group),
                            contactCounts=dict(Counter(len(c['supports']) for r in group for c in r['contacts'])),
                            framesWithAllClustersSupported=sum(r.get('clustersWithSupportedCandidate',-1)==r.get('clusters',-2) for r in group),
                            candidateContextsWithAllPortsSupported=sum(r.get('candidatesWithAllPortsSupported',0) for r in group),
                            framesAfterContextConsistency=sum(r.get('consistency',{}).get('clusters',-1)==r.get('clusters',-2) for r in group),
                            contextsAfterConsistency=sum(len(r.get('consistency',{}).get('candidates',[])) for r in group),
                            imageBudgetStops=sum(r['imageBound']['status']!='image-bound-verified' for r in group),
                            unresolvedTriples=sum(r['tripleUnknown'] for r in group)))
    result=dict(scope=__doc__,coordinateHash=sha(coordp),metadataHash=sha(metap),motifHash=sha(motifp),
                interfaceHash=sha(interfacep),contextHash=sha(contextp),weightHash=sha(weightp),codeHash=sha(Path(__file__)),rows=rows,summary=summary,
                limits='Successful-cover and latent-target geometry are not used; only the training-fitted weights field is read from the weight artifact. Known target atom positions and original fitted motif partition/poses remain given. '
                       'Each contact has common position/value witnesses and exact weight sum, but contacts may share incompatible candidate alternatives. '
                       'All-ports-supported is only a necessary local condition; candidates/contacts must be selected jointly. '
                       'Pair/triple classes cover these positive weight sizes only. No full continuous pose domain, global point identity or growth claim.')
    with out.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
