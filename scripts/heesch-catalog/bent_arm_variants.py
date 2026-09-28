#!/usr/bin/env python3
"""Enumerate fixed-length six-arm bends and verify first-corona exclusions.

All arms have two outward and two sideways steps. Overlapping arms are excluded.
Placement searches allow proper cubic rotations; mirror classes stay distinct.
The census is not a tiling classification of the untested shapes.
Usage: python scripts/heesch-catalog/bent_arm_variants.py --enumerate
       python scripts/heesch-catalog/bent_arm_variants.py --verify /path/to/drat-trim
"""
import argparse, collections, gzip, hashlib, itertools, json, pathlib, subprocess, tempfile, time
import corona
from verify_bent_six_arm import rotations,star
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=ROOT/'data/bent-six-arm/variants'
D=[(1,0,0),(0,1,0),(0,0,1),(-1,0,0),(0,-1,0),(0,0,-1)]
def shape(b):
 points=[(0,0,0)]
 for i,j in enumerate(b):
  d,e=D[i],D[j]
  points.extend(tuple(a*x for x in d) for a in (1,2))
  points.extend(tuple(2*x+a*y for x,y in zip(d,e)) for a in (1,2))
 return sorted(set(points))
def enumerate_all():
 choices=[[j for j,e in enumerate(D) if sum(x*y for x,y in zip(d,e))==0] for d in D]
 maps=[]
 for p in itertools.permutations(range(3)):
  for s in itertools.product((-1,1),repeat=3):
   if (-1)**sum(p[i]>p[j] for i in range(3) for j in range(i+1,3))*s[0]*s[1]*s[2]==1:
    maps.append([D.index(tuple(s[k]*d[p[k]] for k in range(3))) for d in D])
 def canonical(b):
  bs=[]
  for r in maps:
   t=[0]*6
   for i,j in enumerate(b):t[r[i]]=r[j]
   bs.append(tuple(t))
  return min(bs)
 classes={};volumes=collections.Counter()
 for b in itertools.product(*choices):
  vs=shape(b);volumes[len(vs)]+=1
  if len(vs)!=25:continue
  k=canonical(b)
  if k not in classes:classes[k]={'bends':k,'voxels':shape(k),'assignments':0,'antipodal':all(k[(i+3)%6]==(k[i]+3)%6 for i in range(3))}
  classes[k]['assignments']+=1
 rows=[];geometric_keys=set()
 for i,(k,r) in enumerate(sorted(classes.items())):
  r['id']=f'bend_{i:03d}';orbit=rotations(r['voxels']);r['orientations']=len(orbit)
  # Independently canonicalize voxel sets via quarter-turn group generation.
  assert orbit[0] not in geometric_keys;geometric_keys.add(orbit[0]);assert len(orbit)==r['assignments']
  rows.append(r)
 assert sum(volumes.values())==4096 and sum(r['assignments'] for r in rows)==1496 and len(rows)==72
 assert sum(r['antipodal'] for r in rows)==3
 return {'directions':D,'scope':'Two outward and two sideways steps; no overlap between arms; proper-rotation classes. Mirrors not identified unless properly congruent.','rawAssignments':4096,'nonoverlappingAssignments':1496,'overlappingAssignmentsExcluded':2600,'centralSymmetricAssignments':sum(r['assignments'] for r in rows if r['antipodal']),'rows':rows}
def verify(row,checker):
 shapes=rotations(row['voxels']);root=frozenset(shapes[0]);near=star(root)-root;pool={}
 for oi,s in enumerate(shapes):
  ranges=[range(min(q[a] for q in near)-max(v[a] for v in s),max(q[a] for q in near)-min(v[a] for v in s)+1) for a in range(3)]
  for t in itertools.product(*ranges):
   tile=frozenset(tuple(v[a]+t[a] for a in range(3)) for v in s)
   if tile&near and not tile&root:pool[(oi,t)]=tile
 data=corona.build(row['voxels'],1)
 assert tuple(data['shapes'])==shapes and data['near']==near and set(data['universe'])==set(pool)
 assert all(data['cells'](s)==tile for s,tile in pool.items())
 stem=OUT/(row['id']+'-k1');run=json.loads(pathlib.Path(str(stem)+'.json').read_text())
 assert run['status']=='UNSAT'
 cnf=('p cnf %d %d\n'%(data['variables'],len(data['clauses']))+''.join(' '.join(map(str,c))+' 0\n' for c in data['clauses'])).encode()
 assert cnf==gzip.decompress(pathlib.Path(str(stem)+'.cnf.gz').read_bytes())
 proof=gzip.decompress(pathlib.Path(str(stem)+'.drup.gz').read_bytes());sha=lambda x:hashlib.sha256(x).hexdigest()
 assert sha(cnf)==run['formulaSHA256'] and sha(proof)==run['proofSHA256']
 start=time.perf_counter()
 with tempfile.TemporaryDirectory() as temp:
  p=pathlib.Path(temp);(p/'f.cnf').write_bytes(cnf);(p/'p.drup').write_bytes(proof)
  r=subprocess.run([checker,str(p/'f.cnf'),str(p/'p.drup')],capture_output=True);log=r.stdout+r.stderr
  (OUT/(row['id']+'-check.log')).write_bytes(log);assert r.returncode==0 and b's VERIFIED' in log
 result={'id':row['id'],'result':'H=0','scope':'Integer translations, proper cubic rotations, full face/edge/vertex corona','placements':len(pool),'independentRectangularScan':True,'independentQuarterTurnOrientations':True,'cnfRegenerated':True,'proofVerified':True,'proofCheckSeconds':time.perf_counter()-start,'formulaSHA256':sha(cnf),'proofSHA256':sha(proof),'checkerCommit':'2e3b2dc0ecf938addbd779d42877b6ed69d9a985'}
 (OUT/(row['id']+'-verification.json')).write_text(json.dumps(result,indent=2)+'\n');return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--enumerate',action='store_true');p.add_argument('--verify');p.add_argument('--ids',default='bend_018');p.add_argument('--solve',action='store_true');args=p.parse_args();OUT.mkdir(exist_ok=True)
 catalog=enumerate_all()
 if args.enumerate:(OUT/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n');print(json.dumps({k:v for k,v in catalog.items() if k!='rows'}))
 if args.solve:
  for row in catalog['rows']:
   if row['id'] in args.ids.split(','):corona.run(row,1,120,OUT)
 if args.verify:
  for row in catalog['rows']:
   if row['id'] in args.ids.split(','):print(json.dumps(verify(row,args.verify)),flush=True)
