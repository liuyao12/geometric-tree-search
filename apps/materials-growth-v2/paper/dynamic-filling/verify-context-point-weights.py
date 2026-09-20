"""Independent partition uniqueness, exact sums and rational optimality checks."""
import hashlib
import itertools
import json
import sys
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
import numpy as np
from ase.geometry import find_mic


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def rational_solve(A,b):
    M=[[F(v) for v in row]+[F(y)] for row,y in zip(A,b)]
    cols=len(A[0]);pivots=[];r=0
    for c in range(cols):
        pivot=next((i for i in range(r,len(M)) if M[i][c]),None)
        if pivot is None:continue
        M[r],M[pivot]=M[pivot],M[r]
        scale=M[r][c];M[r]=[v/scale for v in M[r]]
        for i in range(len(M)):
            if i!=r:
                scale=M[i][c];M[i]=[x-scale*y for x,y in zip(M[i],M[r])]
        pivots.append(c);r+=1
        if r==len(M):break
    assert all(any(row[:-1]) or not row[-1] for row in M)
    solution=[F(0)]*cols
    for i,c in enumerate(pivots):solution[c]=M[i][-1]
    assert all(sum(F(x)*y for x,y in zip(row,solution))==F(target) for row,target in zip(A,b))
    return solution,len(pivots)


def main():
    motifp,interfacep,contextp,choicep,coordp,neighborhoodp,resultp,out=map(Path,sys.argv[1:])
    motifs,interfaces,inventory,choices,coords,neighborhoods,result=[json.loads(p.read_text()) for p in [motifp,interfacep,contextp,choicep,coordp,neighborhoodp,resultp]]
    assert result['neighborhoodHash']==sha(neighborhoodp)
    for key,p in [('motifHash',motifp),('interfaceHash',interfacep),('contextHash',contextp),('choiceHash',choicep),('coordinateHash',coordp)]:assert neighborhoods[key]==sha(p)
    cc={r['id']:r for r in coords['configurations']};rr={r['id']:r for r in motifs['rows']}
    nn={r['configuration']:r for r in neighborhoods['rows']}
    chosen={r['configuration']:r['witness'] for r in choices['rows'] if r['witness'] and not r['recurringOnly']}
    weights={(r['context'],r['port']):F(r['t']) for r in result['weights']}
    assert len(weights)==len(result['weights']) and all(0<v<=1 for v in weights.values())
    assert len(result['rows'])==len(nn) and {r['configuration'] for r in result['rows']}==set(nn)
    equations=[];eval_sums={};unique=0
    for row in result['rows']:
        cid=row['configuration'];training=row['training']
        assert training==nn[cid]['training'] and len(row['groups'])==len(nn[cid]['groups'])
        for group,source in zip(row['groups'],nn[cid]['groups']):
            assert group['members']==source['members']
            P,V=[],[]
            for member in group['members']:
                k=member['cluster'];ci=member['context'];pi=member['port']
                assert inventory['contexts'][ci]['ports'][pi]==[member['interface'],member['role']]
                pose=rr[cid]['clusters'][k]['fit'] if training else chosen[cid][k]['pose']
                model=interfaces['models'][member['interface']];role=member['role']
                P.append(np.asarray(model['anchor'+role])@pose['rotationRow']+pose['translation'])
                V.append(np.asarray(model['value'+role])@pose['rotationRow'])
            P,V=np.asarray(P),np.asarray(V)
            delta,_=find_mic(P-P[0],np.asarray(cc[cid]['cell']),pbc=True);P=P[0]+delta
            actual=tuple(sorted(tuple(p['indices']) for p in group['points']))
            assert sorted(j for block in actual for j in block)==list(range(len(P)))
            for point in group['points']:
                ids=point['indices']
                for cloud,key in [(P,'position'),(V,'marking')]:
                    error=max(np.linalg.norm(cloud[ids]-point[key]['center'],axis=1))
                    assert error<=.15+1e-9
                variables=[(group['members'][j]['context'],group['members'][j]['port']) for j in ids]
                assert sum((weights[k] for k in variables),F(0))==1
                if training:equations.append(variables)
                else:eval_sums[cid]=eval_sums.get(cid,0)+1
            # Enumerate canonical set partitions independently, using only a
            # necessary pairwise bound. Unique optimum under this relaxation
            # plus checked common-ball witnesses proves uniqueness here.
            n=len(P);admissible=[]
            for labels in itertools.product(range(n),repeat=n):
                if labels[0]!=0 or any(labels[i]>1+max(labels[:i]) for i in range(1,n)):continue
                blocks=[tuple(i for i in range(n) if labels[i]==v) for v in range(max(labels)+1)]
                if all(np.linalg.norm(cloud[i]-cloud[j])<=.30+1e-9 for block in blocks for i in block for j in block for cloud in [P,V]):admissible.append(tuple(sorted(blocks)))
            best=min(map(len,admissible));best_parts={p for p in admissible if len(p)==best}
            assert best_parts=={actual} and group['status']=='unique-minimum'
            unique+=1
    adjacency=defaultdict(set)
    for equation in equations:
        for u in equation:
            adjacency[u].update(equation)
    assert set(adjacency)==set(weights)
    seen=set();nullity=0;certificates=0
    for root in weights:
        if root in seen:continue
        pending=[root];seen.add(root);members=[]
        while pending:
            u=pending.pop();members.append(u)
            for v in adjacency[u]:
                if v not in seen:seen.add(v);pending.append(v)
        member_set=set(members)
        rows=sorted({tuple(sorted(e)) for e in equations if e[0] in member_set})
        A=[[row.count(v) for row in rows] for v in members]
        _,rank=rational_solve(A,[weights[v] for v in members])
        # w=A^T lambda and Aw=1 are an exact stationarity/feasibility
        # certificate for the strictly convex minimum-norm problem.
        nullity+=len(members)-rank;certificates+=1
    assert nullity==result['summary']['freeParameters']
    report=dict(resultHash=sha(resultp),verifierHash=sha(Path(__file__)),uniquePartitions=unique,
                exactTrainingSums=len(equations),exactEvaluationSums=eval_sums,
                rationalOptimalityCertificates=certificates,freeParameters=nullity,
                limits='Exact algebra applies to the inferred finite incidences; geometric/common-ball witnesses remain approximate. '
                       'Minimum-point-count and minimum-norm are explicit priors. No rigid exact-support, full material coverage or growth proof.')
    with out.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps(report))


if __name__=='__main__':main()
