#!/usr/bin/env python3
"""Independent first-corona candidate audit and DRAT check for six bent arms.

Run: python scripts/heesch-catalog/verify_bent_six_arm.py /path/to/drat-trim
Optional --solve regenerates the Glucose discovery artifacts before checking.
Specialized lattice-corona SAT control; not a GCTS marking experiment.
"""
import argparse, gzip, hashlib, itertools, json, pathlib, subprocess, tempfile, time
import corona
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'data/bent-six-arm'
def sha(b):return hashlib.sha256(b).hexdigest()
def normalized(tile):
 lo=tuple(min(v[a] for v in tile) for a in range(3))
 return tuple(sorted(tuple(v[a]-lo[a] for a in range(3)) for v in tile))
def rotations(tile):
 # Generate the rotation group by quarter turns, not signed permutations.
 seen={normalized(tile)};queue=list(seen)
 for s in queue:
  for rotate in [lambda v:(v[0],-v[2],v[1]),lambda v:(v[2],v[1],-v[0])]:
   t=normalized([rotate(v) for v in s])
   if t not in seen:seen.add(t);queue.append(t)
 return tuple(sorted(seen))
def star(tile):
 corners={tuple(v[a]+d[a] for a in range(3)) for v in tile for d in itertools.product((0,1),repeat=3)}
 return {tuple(v[a]-d[a] for a in range(3)) for v in corners for d in itertools.product((0,1),repeat=3)}
def main():
 p=argparse.ArgumentParser();p.add_argument('checker');p.add_argument('--solve',action='store_true');args=p.parse_args()
 row=json.loads((OUT/'tile.json').read_text());vs=set(map(tuple,row['voxels']))
 directions=[(1,0,0),(0,1,0),(0,0,1),(-1,0,0),(0,-1,0),(0,0,-1)]
 expected={(0,0,0)}
 for d,e in zip(directions,directions[1:]+directions[:1]):
  expected.update(tuple(j*x for x in d) for j in (1,2))
  expected.update(tuple(2*x+j*y for x,y in zip(d,e)) for j in (1,2))
 assert vs==expected and len(vs)==25 and {tuple(-x for x in v) for v in vs}==vs
 shapes=rotations(vs);assert len(shapes)==8
 if args.solve:corona.run(row,1,120,OUT)
 root=frozenset(shapes[0]);near=star(root)-root;pool={}
 for oi,shape in enumerate(shapes):
  ranges=[range(min(q[a] for q in near)-max(v[a] for v in shape),max(q[a] for q in near)-min(v[a] for v in shape)+1) for a in range(3)]
  for t in itertools.product(*ranges):
   tile=frozenset(tuple(v[a]+t[a] for a in range(3)) for v in shape)
   if tile&near and not tile&root:pool[(oi,t)]=tile
 data=corona.build(row['voxels'],1)
 assert tuple(data['shapes'])==shapes and data['root']==root and data['near']==near
 assert set(data['universe'])==set(pool)
 assert all(data['cells'](s)==tile for s,tile in pool.items())
 stem=OUT/'bent_six_arm_25-k1'
 cnf=('p cnf %d %d\n'%(data['variables'],len(data['clauses']))+''.join(' '.join(map(str,c))+' 0\n' for c in data['clauses'])).encode()
 assert cnf==gzip.decompress(pathlib.Path(str(stem)+'.cnf.gz').read_bytes())
 proof=gzip.decompress(pathlib.Path(str(stem)+'.drup.gz').read_bytes());run=json.loads(pathlib.Path(str(stem)+'.json').read_text())
 assert sha(cnf)==run['formulaSHA256'] and sha(proof)==run['proofSHA256'] and run['status']=='UNSAT'
 start=time.perf_counter()
 with tempfile.TemporaryDirectory() as temp:
  d=pathlib.Path(temp);(d/'f.cnf').write_bytes(cnf);(d/'p.drup').write_bytes(proof)
  r=subprocess.run([args.checker,str(d/'f.cnf'),str(d/'p.drup')],capture_output=True)
  log=r.stdout+r.stderr;(OUT/'drat-trim.log').write_bytes(log)
  assert r.returncode==0 and b's VERIFIED' in log
 receipt={'result':'H=0','scope':'Integer translations and proper cubic rotations; complete face/edge/vertex touching corona. No claim about arbitrary Euclidean placements.','prototypeVoxels':25,'properOrientations':len(shapes),'centralInversionVerified':True,'rootBoundaryVoxels':len(near),'rootNeighborPlacements':len(pool),'independentQuarterTurnOrientations':True,'independentRectangularCandidateScan':True,'formulaRegeneratedByteForByte':True,'proofVerified':True,'formulaSHA256':sha(cnf),'proofSHA256':sha(proof),'proofCheckSeconds':time.perf_counter()-start,'proofChecker':'DRAT-trim','proofCheckerCommit':'2e3b2dc0ecf938addbd779d42877b6ed69d9a985'}
 receipt['sourceSHA256']={s:sha((ROOT/s).read_bytes()) for s in ['scripts/heesch-catalog/verify_bent_six_arm.py','scripts/heesch-catalog/corona.py','data/bent-six-arm/tile.json']}
 (OUT/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
