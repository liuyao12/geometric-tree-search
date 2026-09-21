#!/usr/bin/env python3
"""Solver-free replay of two p9-42947 grid pair obstructions.

An empty required voxel has no nonoverlapping covering placement. Enumerate the
complete proper cubic orientation orbit independently; no marking is consumed.
"""
import argparse,json,time
from itertools import permutations,product
from pathlib import Path

def need(value,message):
    if not value:raise ValueError(message)

def normalized(voxels):
    low=tuple(min(v[i] for v in voxels) for i in range(3))
    return tuple(sorted(tuple(v[i]-low[i] for i in range(3)) for v in voxels)),low

def rotations():
    for perm in permutations(range(3)):
        parity=(-1)**sum(perm[i]>perm[j] for i in range(3) for j in range(i+1,3))
        for signs in product([-1,1],repeat=3):
            if parity*signs[0]*signs[1]*signs[2]==1:yield perm,signs

def rotated(cells,r):
    perm,signs=r
    return [tuple((signs[i]*(2*v[perm[i]]+1)-1)//2 for i in range(3)) for v in cells]

def verify(data):
    need(data['allowReflections'] is False,'Unexpected reflections')
    expected_base=[(0,0,1),(0,1,0),(0,1,1),(0,1,2),(1,0,0),(1,0,1),(1,1,0),(1,2,0),(2,0,1)]
    need(data['tile']=='p9-42947' and list(map(tuple,data['prototype']))==expected_base,'Wrong catalogue prototype')
    base=data['prototype'];orientations=[list(map(tuple,o)) for o in data['orientations']]
    need(all(len(v)==3 and all(type(x) is int for x in v) for o in [base,*orientations] for v in o),'Noninteger voxel')
    need(len(set(map(tuple,base)))==len(base)==9,'Invalid prototype')
    expected={normalized(rotated(base,r))[0] for r in rotations()}
    shapes=[normalized(o)[0] for o in orientations]
    need(len(set(shapes))==len(shapes)==8 and set(shapes)==expected,'Incomplete or wrong proper orientation orbit')
    need(all(len(set(o))==len(o)==9 for o in orientations),'Invalid orientation')
    rows=[];schemas=set();lookup={normalized(o)[0]:(i,normalized(o)[1]) for i,o in enumerate(orientations)}
    for row in data['obstructions']:
        need(len(row['pair'])==2,'Expected a pair');placed=[]
        for p in row['pair']:
            oi=p['oi'];t=p['translation']
            need(type(oi) is int and 0<=oi<len(orientations) and len(t)==3 and all(type(x) is int and x%2==0 for x in t),'Invalid half-unit placement')
            placed.append({tuple(v[i]+t[i]//2 for i in range(3)) for v in orientations[oi]})
        need(not placed[0]&placed[1],'Seed tiles already overlap')
        occupied=placed[0]|placed[1];q=tuple(row['deadVoxel'])
        need(len(q)==3 and all(type(x) is int for x in q),'Invalid dead voxel')
        need(q not in occupied,'Claimed dead voxel is occupied')
        # Sharing a corner with a seed means this voxel must be covered to fill
        # the seed's positive weighted corner support to capacity.
        need(any(max(abs(q[i]-v[i]) for i in range(3))<=1 for v in occupied),'Dead voxel is outside seed corona obligations')
        checked=0
        for o in orientations:
            for anchor in o:
                t=tuple(q[i]-anchor[i] for i in range(3))
                candidate={tuple(v[i]+t[i] for i in range(3)) for v in o}
                need(bool(candidate&occupied),'A legal placement covers the claimed dead voxel');checked+=1
        for r in rotations():
            transformed=[]
            for cells in placed:
                shape,origin=normalized(rotated(cells,r));oi,offset=lookup[shape]
                transformed.append((oi,tuple(2*(origin[i]-offset[i]) for i in range(3))))
            for a,b in [transformed,transformed[::-1]]:schemas.add((a[0],b[0],*(b[1][i]-a[1][i] for i in range(3))))
        rows.append({'orbit':row['orbit'],'deadVoxel':list(q),'coveringPlacementsChecked':checked})
    need(len(rows)==2 and len(schemas)==24,'Unexpected number of pair classes')
    return {'verified':True,'orientations':8,'properRotations':24,'relativePairSchemas':len(schemas),'obstructions':rows,'scope':'Necessary pair exclusions for proper cubic rotations and integer translations. No global non-tiling or aperiodicity claim.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--input',default=str(Path(__file__).resolve().parents[1]/'data/3d-p9-42947-pair-obstructions-2026-09-21.json'));a=parser.parse_args()
    started=time.perf_counter();result=verify(json.loads(Path(a.input).read_text()));result['elapsedMs']=(time.perf_counter()-started)*1000
    print(json.dumps(result,indent=2))
