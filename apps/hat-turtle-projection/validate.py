"""Independent geometry checks for the generated finite projection patch."""
import json, math, pathlib, time
from collections import defaultdict
root=pathlib.Path(__file__).resolve().parent
patch=json.loads((root/'patch.json').read_text())
vertices=patch['vertices'];tiles=patch['tiles']
assert len({tuple(v) for v in vertices})==len(vertices)
assert all(len(v)==4 and all(isinstance(x,int) for x in v) for v in vertices)
edge_counts=defaultdict(int)
for poly in tiles:
    assert len(poly)==14 and len(set(poly))==14
    for a,b in zip(poly,poly[1:]+poly[:1]):edge_counts[tuple(sorted((a,b)))]+=1
assert all(n in (1,2) for n in edge_counts.values())
assert len(vertices)-len(edge_counts)+len(tiles)==1
edges=list(edge_counts)
EPS=1e-8

def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def bad_intersection(a,b,c,d):
    if max(a[0],b[0])+EPS<min(c[0],d[0]) or max(c[0],d[0])+EPS<min(a[0],b[0]):return False
    if max(a[1],b[1])+EPS<min(c[1],d[1]) or max(c[1],d[1])+EPS<min(a[1],b[1]):return False
    u,v,w,t=cross(a,b,c),cross(a,b,d),cross(c,d,a),cross(c,d,b)
    if ((u>EPS and v<-EPS) or (u<-EPS and v>EPS)) and ((w>EPS and t<-EPS) or (w<-EPS and t>EPS)):return True
    if max(abs(u),abs(v),abs(w),abs(t))<EPS:
        axis=0 if abs(a[0]-b[0])>=abs(a[1]-b[1]) else 1
        return min(max(a[axis],b[axis]),max(c[axis],d[axis]))-max(min(a[axis],b[axis]),min(c[axis],d[axis]))>EPS
    # A non-incident vertex cannot lie strictly inside another edge.
    for p,q,r,k in [(a,b,c,u),(a,b,d,v),(c,d,a,w),(c,d,b,t)]:
        if abs(k)<EPS and min(p[0],q[0])-EPS<=r[0]<=max(p[0],q[0])+EPS and min(p[1],q[1])-EPS<=r[1]<=max(p[1],q[1])+EPS:
            if math.dist(r,p)>EPS and math.dist(r,q)>EPS:return True
    return False

results=[];baseline_signs=None
for fraction in [0,.25,.5,.75,1]:
    theta=math.pi/3-fraction*math.pi/6;c,s=math.cos(theta),math.sin(theta)
    pts=[(c*(p+q/2)+s*math.sqrt(3)*r/2,c*math.sqrt(3)*q/2+s*(r/2+t)) for p,q,r,t in vertices]
    areas=[]
    for poly in tiles:
        area=sum(pts[a][0]*pts[b][1]-pts[b][0]*pts[a][1] for a,b in zip(poly,poly[1:]+poly[:1]))/2
        assert abs(area)>EPS
        areas.append(area)
    signs=[1 if a>0 else -1 for a in areas]
    if baseline_signs is None:baseline_signs=signs
    assert signs==baseline_signs,'A tile flipped during projection'
    assert max(map(abs,areas))-min(map(abs,areas))<1e-7,'Noncongruent tile areas'
    buckets=defaultdict(list);comparisons=0
    for i,(a,b) in enumerate(edges):
        pa,pb=pts[a],pts[b]
        cells=[(x,y) for x in range(math.floor(min(pa[0],pb[0])/2),math.floor(max(pa[0],pb[0])/2)+1) for y in range(math.floor(min(pa[1],pb[1])/2),math.floor(max(pa[1],pb[1])/2)+1)]
        candidates=set(j for cell in cells for j in buckets[cell])
        for j in candidates:
            q,r=edges[j]
            if a in (q,r) or b in (q,r):continue
            comparisons+=1
            assert not bad_intersection(pa,pb,pts[q],pts[r]),('Crossing or overlapping edges',fraction,i,j)
        for cell in cells:buckets[cell].append(i)
    results.append({'fraction':fraction,'tileArea':abs(areas[0]),'properCrossingsOrOverlaps':0,'edgePairsChecked':comparisons})
    print('Passed',fraction,'edge pairs checked',comparisons,flush=True)
result={'geometry':{'integerVertices':len(vertices),'tiles':len(tiles),'sharedEdges':sum(n==2 for n in edge_counts.values()),'eulerCharacteristic':1,'samples':results},'browser':{'status':'pending'}}
(root/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
