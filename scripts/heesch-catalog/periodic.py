#!/usr/bin/env python3
"""Small two-copy cyclic-quotient search, followed by an exact certificate replay.

A failed search is not evidence of non-tiling. Successful certificates partition
all cosets of a full-rank lattice with properly rotated prototype copies.
"""
import argparse,itertools,json,pathlib
from corona import norm,orientations
ROOT=pathlib.Path(__file__).resolve().parents[2]
def verify(row,cert):
 n=cert['modulus'];c=cert['coefficients'];assert c[0]==1
 shapes=set(orientations(row['voxels']));residues=[]
 for placement in cert['placements']:
  cells=placement['cells'];assert len(cells)==len(row['voxels'])
  assert len(set(map(tuple,cells)))==len(cells) and norm(cells) in shapes
  residues.extend(sum(a*b for a,b in zip(c,p))%n for p in cells)
 assert sorted(residues)==list(range(n))
 # These independent vectors lie in the kernel and have determinant n.
 # Surjectivity follows from c[0]=1, so they generate the entire kernel.
 periods=[[n,0,0],[-c[1],1,0],[-c[2],0,1]]
 assert all(sum(a*b for a,b in zip(c,p))%n==0 for p in periods)
 return dict(cert,periodVectors=periods,residues=residues,verified=True,
             heesch='infinite',kind='two-copy-cyclic-quotient')
def search(row):
 v=row['voxels'];n=2*len(v);full=set(range(n));shapes=orientations(v)
 for a,b in itertools.product(range(n),repeat=2):
  coeff=(1,a,b)
  def residues(shape):return {sum(c*x for c,x in zip(coeff,p))%n for p in shape}
  s=residues(v)
  if len(s)!=len(v):continue
  target=full-s
  for sh in shapes:
   r=residues(sh)
   if len(r)!=len(v):continue
   for t in range(n):
    if {(x+t)%n for x in r}==target:
     return verify(row,{'id':row['id'],'coefficients':coeff,'modulus':n,
       'placements':[{'cells':v},{'cells':[[p[0]+t,p[1],p[2]] for p in sh]}]})
 return {'id':row['id'],'verified':False,'status':'No certificate in this restricted family; no Heesch bound.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--ids',required=True);p.add_argument('--verify-only',action='store_true');a=p.parse_args()
 catalog=json.loads((ROOT/'data/heesch-catalog/catalog.json').read_text());out=ROOT/'data/heesch-catalog/periodic';out.mkdir(exist_ok=True)
 for row in catalog['systems']:
  if row['id'] not in a.ids.split(','):continue
  path=out/(row['id']+'.json')
  if a.verify_only:result=verify(row,json.loads(path.read_text()))
  else:result=search(row);path.write_text(json.dumps(result,indent=2)+'\n')
  print(json.dumps({'id':row['id'],'verified':result['verified']}))
