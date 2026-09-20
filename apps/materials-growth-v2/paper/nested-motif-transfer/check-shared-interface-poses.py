"""Finite shared-pose consistency audit of learned pair interfaces.

This is a diagnostic finite-domain CSP, not the GCTS frontier tree search.
Domains contain original motif poses and saved positive pair-witness poses.
No learned value, tolerance, motif identity or source coordinate is refitted.
"""
import hashlib,importlib.util,json,sys
from pathlib import Path
from collections import defaultdict
import numpy as np
from ase.geometry import find_mic

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def solve(domains,relations,limit=100000):
    assignment={};nodes=0;stopped=False
    def visit(k):
        nonlocal nodes,stopped
        if nodes>=limit:stopped=True;return None
        nodes+=1
        if k==len(domains):return dict(assignment)
        for value in range(len(domains[k])):
            if any((value,assignment[b]) not in allowed for a,b,allowed in relations if a==k and b in assignment):continue
            if any((assignment[a],value) not in allowed for a,b,allowed in relations if b==k and a in assignment):continue
            assignment[k]=value;found=visit(k+1);del assignment[k]
            if found is not None:return found
            if stopped:break
        return None
    result=visit(0)
    return result,dict(nodes=nodes,status='consistent' if result is not None else 'unknown-budget' if stopped else 'exhausted-saved-pose-domain')

def components(n,edges):
    parent=list(range(n))
    def root(i):
        while parent[i]!=i:i=parent[i]
        return i
    for a,b in edges:parent[root(a)]=root(b)
    return len({root(i) for i in range(n)})

def main():
    coordp,metap,motifp,interfacep,pairp,out=map(Path,sys.argv[1:]);coords=json.loads(coordp.read_text());meta=json.loads(metap.read_text());motifs=json.loads(motifp.read_text());interfaces=json.loads(interfacep.read_text());pairs=json.loads(pairp.read_text())
    for key,path in [('coordinateHash',coordp),('metadataHash',metap),('motifHash',motifp),('interfaceHash',interfacep)]:assert pairs[key]==sha(path)
    cc={c['id']:c for c in coords['configurations']};mm={m['id']:m for m in meta['configurations']};rr={r['id']:r for r in motifs['rows']};byframe=defaultdict(list)
    spec=importlib.util.spec_from_file_location('periodic',Path(__file__).with_name('periodic-interface-proposals.py'));periodic=importlib.util.module_from_spec(spec);spec.loader.exec_module(periodic)
    for p in pairs['rows']:byframe[p['configuration']].append(p)
    rows=[]
    for cid,group in byframe.items():
        c=cc[cid];clusters=rr[cid]['clusters'];domains=[[p['fit']] for p in clusters]
        for p in group:
            if p['witness'] is None:continue
            o=interfaces['observations'][p['observation']]
            for suffix in ['A','B']:
                pose=p['witness']['pose'+suffix];k=o['cluster'+suffix]
                # Exact serialized duplicate only; no unproved symmetry quotient.
                if pose not in domains[k]:domains[k].append(pose)
        relations=[];witnesses={};edges=[];periodic_edges=[];relation_counts=[]
        for p in group:
            oi=p['observation'];o=interfaces['observations'][oi];a=o['clusterA'];b=o['clusterB'];edges.append((a,b));allowed=set()
            raw=np.asarray(clusters[b]['fit']['translation'])-clusters[a]['fit']['translation'];delta,_=find_mic(raw,np.asarray(c['cell']),pbc=c['pbc']);shift=(delta-raw)@np.linalg.inv(c['cell']);assert max(abs(shift-np.round(shift)))<1e-8
            periodic_edges.append((a,b,np.round(shift).astype(int).tolist()))
            models=[(i,m) for i,m in enumerate(interfaces['models']) if m['trainingFrames']>=2 and (m['typeA'],m['typeB'])==(o['typeA'],o['typeB'])]
            for ai,pa in enumerate(domains[a]):
                for bi,pb in enumerate(domains[b]):
                    RA=np.asarray(pa['rotationRow']);RB=np.asarray(pb['rotationRow']);d,_=find_mic(np.asarray(pb['translation'])-pa['translation'],np.asarray(c['cell']),pbc=c['pbc'])
                    for mi,m in models:
                        x=np.asarray(m['anchorA'])@RA;y=np.asarray(m['anchorB'])@RB+d;u=np.asarray(m['valueA'])@RA;v=np.asarray(m['valueB'])@RB
                        errors=[float(np.linalg.norm(x-y)),float(np.linalg.norm(u-v)),float(max(np.linalg.norm(u-d),np.linalg.norm(v-d)))]
                        if all(e<=interfaces[key]+1e-9 for e,key in zip(errors,['positionPairTolerance','valuePairTolerance','valueTargetTolerance'])):
                            allowed.add((ai,bi));witnesses[oi,ai,bi]=dict(observation=oi,interface=mi,errors=errors);break
            relations.append((a,b,allowed));relation_counts.append(len(allowed))
        solution,stats=solve(domains,relations);selected=[]
        if solution is not None:
            for p in group:
                oi=p['observation'];o=interfaces['observations'][oi];selected.append(witnesses[oi,solution[o['clusterA']],solution[o['clusterB']]])
        rows.append(dict(configuration=cid,motifs=len(clusters),proposedPairs=len(group),proposalComponents=components(len(clusters),edges),periodicEdges=periodic_edges,periodicGraph=periodic.graph_audit(len(clusters),periodic_edges),pairwiseComplete=all(p['witness'] is not None for p in group),domainSizes=list(map(len,domains)),relationSizes=relation_counts,search=stats,poses=[domains[k][solution[k]] for k in range(len(clusters))] if solution is not None else None,selected=selected))
    summary=[]
    for phase in sorted({m['phase'] for m in mm.values()}):
        group=[r for r in rows if mm[r['configuration']]['phase']==phase]
        summary.append(dict(phase=phase,frames=len(group),pairwiseComplete=sum(r['pairwiseComplete'] for r in group),sharedPoseConsistent=sum(r['poses'] is not None for r in group),connectedAndConsistent=sum(r['poses'] is not None and r['proposalComponents']==1 for r in group),disconnectedProposalFrames=sum(r['proposalComponents']>1 for r in group),connectedPeriodicLifts=sum(r['periodicGraph']['connectedPeriodicLift'] for r in group),allComponentsRankZero=sum(all(c['translationRank']==0 for c in r['periodicGraph']['components']) for r in group)))
    report=dict(scope=__doc__,coordinateHash=sha(coordp),metadataHash=sha(metap),motifHash=sha(motifp),interfaceHash=sha(interfacep),pairResultHash=sha(pairp),codeHash=sha(Path(__file__)),periodicHelperHash=sha(Path(__file__).with_name('periodic-interface-proposals.py')),rows=rows,summary=summary,
                limits='Consistency only within a finite saved-pose domain and fixed nearest-centroid pair graph. Exhaustion is not continuous infeasibility. Integer edge-image cycles audit abstract periodic connectivity, not material growth. Cross-interface marking coincidences and multi-way common values remain unaudited. No learned t-values, condition matching or blind growth.')
    with out.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps(summary))
if __name__=='__main__':main()
