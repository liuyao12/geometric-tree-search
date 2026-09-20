"""Infer common-point partitions and fit exact rational t on training contexts.

Explicit priors: minimize number of shared points within each proximity group;
each block must have common position AND marking radius-.15 witnesses. Then
minimize the squared norm of context-local port weights subject to training
point sums=1. No interface edge IDs are used in partition decisions. Existing
anchor/value learning remains edge-proposal-dependent; this is not independent
discovery of connections or a complete geometric filling/search pipeline.
"""
import hashlib
import importlib.util
import itertools
import json
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
import numpy as np


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def partitions(items):
    if not items:
        yield []
        return
    first,*rest=items
    for tail in partitions(rest):
        yield [(first,)]+tail
        for k in range(len(tail)):
            yield tail[:k]+[tuple(sorted((first,)+tail[k]))]+tail[k+1:]


def partition_group(P,V,ball):
    n=len(P)
    if n>8:
        return dict(status='unknown-size-budget')
    blocks={}
    for size in range(1,n+1):
        for ids in itertools.combinations(range(n),size):
            position,marking=ball(P[list(ids)]),ball(V[list(ids)])
            statuses=[position['status'],marking['status']]
            status='accepted' if all(s=='common-ball-witness' for s in statuses) else 'rejected' if 'diameter-obstruction' in statuses else 'unknown'
            blocks[ids]=dict(status=status,position=position,marking=marking)
    best=[]
    unknown_min=n+1
    for partition in partitions(list(range(n))):
        statuses=[blocks[b]['status'] for b in partition]
        if 'rejected' in statuses:
            continue
        if 'unknown' in statuses:
            unknown_min=min(unknown_min,len(partition))
        elif not best or len(partition)<len(best[0]):
            best=[partition]
        elif len(partition)==len(best[0]):
            best.append(partition)
    assert best
    status='unique-minimum' if len(best)==1 and unknown_min>len(best[0]) else 'ambiguous-or-unknown'
    return dict(status=status,minimumPoints=len(best[0]),verifiedMinimumPartitions=len(best),unknownMinimumPoints=unknown_min if unknown_min<=n else None,
                points=[dict(indices=list(ids),position=blocks[ids]['position'],marking=blocks[ids]['marking']) for ids in best[0]])


def fit_pair_weights(pairs):
    """Exact minimum-norm solution of x_u+x_v=1 on a graph.

An odd cycle fixes its component to 1/2. A bipartite component has one free
parameter; minimum norm picks b/(a+b) on its a-vertex side and a/(a+b) on
the other. Parallel equations do not reweight the regularizer.
"""
    adjacency=defaultdict(set)
    for u,v in pairs:
        adjacency[u].add(v)
        adjacency[v].add(u)
    colors,weights,components={}, {}, []
    for root in sorted(adjacency):
        if root in colors:
            continue
        colors[root]=0
        pending=[root]
        members=[]
        odd=False
        while pending:
            u=pending.pop()
            members.append(u)
            for v in adjacency[u]:
                if v not in colors:
                    colors[v]=1-colors[u]
                    pending.append(v)
                elif colors[v]==colors[u]:
                    odd=True
        a=sum(colors[u]==0 for u in members)
        b=len(members)-a
        for u in members:
            weights[u]=Fraction(1,2) if odd else Fraction(b if colors[u]==0 else a,a+b)
        components.append(dict(variables=len(members),oddCycle=odd,freeParameters=0 if odd else 1,sideSizes=[a,b]))
    assert all(weights[u]+weights[v]==1 for u,v in pairs)
    return weights,components


def main():
    motifp,interfacep,contextp,choicep,coordp,neighborhoodp,out=map(Path,sys.argv[1:])
    motifs,interfaces,inventory,choices,coords,neighborhoods=[json.loads(p.read_text()) for p in [motifp,interfacep,contextp,choicep,coordp,neighborhoodp]]
    for key,p in [('motifHash',motifp),('interfaceHash',interfacep),('contextHash',contextp),('choiceHash',choicep),('coordinateHash',coordp)]:
        assert neighborhoods[key]==sha(p)
    geometry=load('geometry','audit-anchor-neighborhoods.py')
    periodic=load('periodic','verify-offatom-interfaces.py')
    cc={r['id']:r for r in coords['configurations']}
    rr={r['id']:r for r in motifs['rows']}
    evaluated={r['configuration']:r['witness'] for r in choices['rows'] if r['witness'] is not None and not r['recurringOnly']}
    rows=[]
    pairs=[]
    for row in neighborhoods['rows']:
        cid=row['configuration']
        groups=[]
        for group in row['groups']:
            P,V=[],[]
            for member in group['members']:
                k=member['cluster']
                pose=rr[cid]['clusters'][k]['fit'] if row['training'] else evaluated[cid][k]['pose']
                R,tr=np.asarray(pose['rotationRow']),np.asarray(pose['translation'])
                model=interfaces['models'][member['interface']]
                role=member['role']
                P.append(np.asarray(model['anchor'+role])@R+tr)
                V.append(np.asarray(model['value'+role])@R)
            P=np.asarray(P)
            P=np.array([P[0]+periodic.mic(p-P[0],cc[cid]['cell']) for p in P])
            part=partition_group(P,np.asarray(V),geometry.common_ball)
            part['members']=group['members']
            groups.append(part)
            if row['training']:
                assert part['status']=='unique-minimum','Do not choose an unresolved point partition for training'
                for point in part['points']:
                    ids=point['indices']
                    assert len(ids)==2,'This exact weight solver is specialized to observed pair incidence'
                    pairs.append(tuple((group['members'][j]['context'],group['members'][j]['port']) for j in ids))
        rows.append(dict(configuration=cid,training=row['training'],groups=groups))
    weights,components=fit_pair_weights(pairs)
    evaluation=[]
    for row in rows:
        if row['training']:
            continue
        equations=[]
        for group in row['groups']:
            for point in group['points']:
                keys=[(group['members'][j]['context'],group['members'][j]['port']) for j in point['indices']]
                total=sum((weights[k] for k in keys),Fraction(0))
                equations.append(dict(variables=keys,total=str(total),filled=total==1))
        evaluation.append(dict(configuration=row['configuration'],uniquePartition=all(g['status']=='unique-minimum' for g in row['groups']),
                               allSumsOne=all(e['filled'] for e in equations),equations=equations))
    result=dict(scope=__doc__,neighborhoodHash=sha(neighborhoodp),codeHash=sha(Path(__file__)),
                rows=rows,weights=[dict(context=k[0],port=k[1],t=str(v)) for k,v in sorted(weights.items())],components=components,evaluation=evaluation,
                summary=dict(trainingEquations=len(pairs),variables=len(weights),freeParameters=sum(c['freeParameters'] for c in components),
                             weightHistogram=dict(Counter(str(v) for v in weights.values())),
                             partitionStatuses=dict(Counter(g['status'] for r in rows for g in r['groups'])),
                             evaluationFrames=len(evaluation),evaluationExactSums=sum(r['uniquePartition'] and r['allSumsOne'] for r in evaluation)),
                limits='Minimum number of common points is a prior, not uniquely inferred without that prior. '
                       'Minimum-norm t is a declared regularizer where training equations have free parameters. '
                       'Geometry and marking witnesses are approximate; rational t-sums are exact only on these inferred finite incidences. '
                       'Atom-site coverage, rigid tile support consistency across frames, completeness and blind growth remain unproved.')
    with out.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result['summary']))


if __name__=='__main__':main()
