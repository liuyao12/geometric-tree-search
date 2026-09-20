"""Periodic Voronoi interface proposals with an omitted-image distance bound.

A geometry-only candidate generator, not a learned connection rule. Includes
self-image edges and records integer lattice shifts. No element/phase fields
enter geometry. Does not force the learner to use every proposed interface.
"""
import hashlib,itertools,json,math,sys
from pathlib import Path
from collections import Counter
import numpy as np
from scipy.spatial import Voronoi

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def graph_audit(n,edges):
    adj=[[] for _ in range(n)]
    for a,b,s in edges:
        s=np.asarray(s,dtype=int);adj[a].append((b,s));adj[b].append((a,-s))
    potentials={};components=[]
    for start in range(n):
        if start in potentials:continue
        potentials[start]=np.zeros(3,dtype=int);stack=[start];nodes=[];cycles=[]
        while stack:
            a=stack.pop();nodes.append(a)
            for b,s in adj[a]:
                if b not in potentials:potentials[b]=potentials[a]+s;stack.append(b)
                else:
                    v=potentials[a]+s-potentials[b]
                    if np.any(v):cycles.append(v)
        rank=0;index=None
        if cycles:
            rank=1
            for a,b in itertools.combinations(cycles,2):
                if np.any(np.cross(a,b)):rank=2;break
            gcd=0
            if rank==2:
                for a,b,c in itertools.combinations(cycles,3):
                    det=int(np.dot(a,np.cross(b,c)))
                    if det:rank=3;gcd=math.gcd(gcd,abs(det))
                    if gcd==1:break
                if rank==3:index=gcd
        components.append(dict(nodes=sorted(nodes),translationRank=rank,latticeIndex=index))
    return dict(quotientComponents=len(components),components=components,connectedPeriodicLift=len(components)==1 and components[0]['translationRank']==3 and components[0]['latticeIndex']==1)

def propose(centers,cell,max_shell=5,start_shell=1):
    cell=np.asarray(cell,dtype=float);centers=np.asarray(centers,dtype=float);fractional=centers@np.linalg.inv(cell);wrapped=(fractional-np.floor(fractional))@cell;n=len(wrapped)
    if n>1:assert min(np.linalg.norm(wrapped[i]-wrapped[j]) for i in range(n) for j in range(i))>1e-8,'Coincident motif centroids require explicit handling'
    span=max(np.linalg.norm(a-b) for a in wrapped for b in wrapped);smin=np.linalg.svd(cell,compute_uv=False)[-1]
    for shell in range(start_shell,max_shell+1):
        shifts=list(itertools.product(range(-shell,shell+1),repeat=3));cloud=np.asarray([p+np.asarray(s)@cell for s in shifts for p in wrapped]);vor=Voronoi(cloud);zero=shifts.index((0,0,0))*n;central=set(range(zero,zero+n));radii=[]
        for i in central:
            vertices=vor.regions[vor.point_region[i]]
            if not vertices or -1 in vertices:break
            radii.append(float(max(np.linalg.norm(vor.vertices[j]-cloud[i]) for j in vertices)))
        if len(radii)!=n:continue
        lower=(shell+1)*smin-span
        if lower<=2*max(radii)+1e-8:continue
        edges=set()
        for (a,b),vertices in zip(vor.ridge_points,vor.ridge_vertices):
            if a not in central and b not in central:continue
            if a not in central:a,b=b,a
            assert -1 not in vertices
            i=a-zero;j=b%n;s=shifts[b//n]
            if i==j and s==(0,0,0):continue
            forward=(i,j,*s);reverse=(j,i,*(-np.asarray(s)));edges.add(min(forward,reverse))
        rows=[(int(e[0]),int(e[1]),list(map(int,e[2:]))) for e in sorted(edges)]
        return dict(edges=rows,shell=shell,wrappedCenters=wrapped.tolist(),maximumCellRadius=max(radii),omittedPointDistanceLowerBound=float(lower),imageBoundMargin=float(lower-2*max(radii)),graph=graph_audit(n,rows))
    raise ValueError('Image enclosure unverified within declared shell budget')

def main():
    coordp,metap,motifp,out=map(Path,sys.argv[1:]);coords=json.loads(coordp.read_text());meta=json.loads(metap.read_text());motifs=json.loads(motifp.read_text());assert motifs['coordinateHash']==sha(coordp) and motifs['metadataHash']==sha(metap)
    cc={c['id']:c for c in coords['configurations']};mm={m['id']:m for m in meta['configurations']};rows=[]
    for r in motifs['rows']:
        if r['training']:continue
        if any(not p['matched'] for p in r['clusters']):rows.append(dict(configuration=r['id'],status='unmapped-motif'));continue
        c=cc[r['id']];centers=[p['fit']['translation'] for p in r['clusters']]
        try:result=propose(centers,c['cell']);rows.append(dict(configuration=r['id'],status='verified-image-bound',**result))
        except ValueError as error:rows.append(dict(configuration=r['id'],status='unknown',reason=str(error)))
    summary=[]
    for phase in sorted({m['phase'] for m in mm.values()}):
        group=[r for r in rows if mm[r['configuration']]['phase']==phase];ok=[r for r in group if r['status']=='verified-image-bound']
        summary.append(dict(phase=phase,frames=len(group),imageBoundVerified=len(ok),connectedPeriodicLifts=sum(r['graph']['connectedPeriodicLift'] for r in ok),edgeCountRange=[min(len(r['edges']) for r in ok),max(len(r['edges']) for r in ok)] if ok else None))
    report=dict(scope=__doc__,coordinateHash=sha(coordp),metadataHash=sha(metap),motifHash=sha(motifp),codeHash=sha(Path(__file__)),rows=rows,summary=summary,
                limits='Numerical Voronoi candidate graph, not learned marking constraints or physical bonds. Distance bound certifies omitted images cannot clip central cells up to numerical construction accuracy; it is not exact-arithmetic Voronoi verification. Integer cycle ranks/indices certify connectivity of the recorded abstract periodic graph only. Candidate graph may change at degeneracies. No interface transfer, learned t-values, shared-pose consistency or GCTS reconstruction established by these counts.')
    with out.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps(summary))
if __name__=='__main__':main()
