#!/usr/bin/env python3
"""Audit the ring witness, complete placement universe, and checked UNSAT proof.

Usage: python scripts/heesch-catalog/verify_ring.py /path/to/drat-trim
Uses an independent rectangular translation scan and cube-vertex incidence.
This is a specialized lattice-corona SAT audit, not the GCTS scheduler.
"""
import gzip, hashlib, importlib.util, itertools, json, pathlib, subprocess, sys, tempfile, time
import corona
from positive_control_witnesses import vertex_star
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'data/ring-octocube'
def digest(b): return hashlib.sha256(b).hexdigest()
def shape(axis):
 axes=[i for i in range(3) if i!=axis]; result=[]
 for a,b in itertools.product(range(3),repeat=2):
  if (a,b)==(1,1): continue
  v=[0,0,0];v[axes[0]]=a;v[axes[1]]=b;result.append(tuple(v))
 return tuple(sorted(result))
SHAPES=tuple(sorted(shape(i) for i in range(3)))
def scan(target,root):
 result={}
 for oi,s in enumerate(SHAPES):
  # A placement intersecting target must lie in these inclusive ranges.
  ranges=[range(min(q[a] for q in target)-max(v[a] for v in s),max(q[a] for q in target)-min(v[a] for v in s)+1) for a in range(3)]
  for offset in itertools.product(*ranges):
   tile=frozenset(tuple(v[a]+offset[a] for a in range(3)) for v in s)
   if not tile&root and tile&target:result[(oi,offset)]=tile
 return result

def main():
 prototype=json.loads((OUT/'tile.json').read_text())['voxels']
 witness=json.loads((OUT/'ring_octocube-k1.json').read_text())['witness']
 root=frozenset(map(tuple,witness['root']));assert root==frozenset(SHAPES[0])
 occupied=set(root)
 for raw in witness['tiles']:
  tile=frozenset(map(tuple,raw));lo=tuple(min(v[a] for v in tile) for a in range(3))
  assert tuple(sorted(tuple(v[a]-lo[a] for a in range(3)) for v in tile)) in SHAPES
  assert not tile&occupied and tile&vertex_star(root);occupied.update(tile)
 assert vertex_star(root)<=occupied
 near=vertex_star(root)-root;first=scan(near,root)
 requirements={s:vertex_star(t)-root-t for s,t in first.items()}
 target=set(near).union(*requirements.values());universe=scan(target,root)
 data=corona.build(prototype,2)
 assert tuple(data['shapes'])==SHAPES and set(first)==data['first'] and set(universe)==set(data['universe'])
 assert requirements==data['requirements'] and target==data['target']
 assert all(data['cells'](s)==t for s,t in universe.items())
 spec=importlib.util.spec_from_file_location('original',ROOT/'scripts/search-nonacube-two-corona.py')
 old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);old.SHAPES=SHAPES
 original=old.build();assert original['clauses']==data['clauses'] and original['universe']==data['universe']
 cnf=('p cnf %d %d\n'%(data['variables'],len(data['clauses']))+''.join(' '.join(map(str,c))+' 0\n' for c in data['clauses'])).encode()
 assert cnf==gzip.decompress((OUT/'ring_octocube-k2.cnf.gz').read_bytes())
 proof=gzip.decompress((OUT/'ring_octocube-k2.drup.gz').read_bytes())
 run=json.loads((OUT/'ring_octocube-k2.json').read_text());assert digest(cnf)==run['formulaSHA256'] and digest(proof)==run['proofSHA256']
 start=time.perf_counter()
 with tempfile.TemporaryDirectory() as tmp:
  f=pathlib.Path(tmp);(f/'formula.cnf').write_bytes(cnf);(f/'proof.drup').write_bytes(proof)
  p=subprocess.run([sys.argv[1],str(f/'formula.cnf'),str(f/'proof.drup')],capture_output=True)
  log=p.stdout+p.stderr;(OUT/'drat-trim.log').write_bytes(log)
  assert p.returncode==0 and b's VERIFIED' in log
 receipt={'result':'H=1','scope':'Integer translations and cubic-lattice rotations; full face/edge/vertex touching coronas. No claim for arbitrary rigid motions.', 'firstCoronaTiles':len(witness['tiles']), 'firstCoronaGeometryVerified':True,'rootNeighborPlacements':len(first),'twoCoronaPlacements':len(universe),'independentRectangularCandidateScan':True,'sameClausesAsOriginalNonacubeEncoder':True,'formulaSHA256':digest(cnf),'proofSHA256':digest(proof),'proofChecker':'DRAT-trim','proofCheckerCommit':'2e3b2dc0ecf938addbd779d42877b6ed69d9a985','proofVerified':True,'proofCheckSeconds':time.perf_counter()-start}
 files=['scripts/heesch-catalog/verify_ring.py','scripts/heesch-catalog/corona.py','scripts/heesch-catalog/positive_control_witnesses.py','scripts/search-nonacube-two-corona.py']
 receipt['sourceSHA256']={p:digest((ROOT/p).read_bytes()) for p in files}
 (OUT/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
