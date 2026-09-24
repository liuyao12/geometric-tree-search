#!/usr/bin/env python3
"""Replay selected published periodic witnesses using exact integer quotients.

No SAT solver, period search, or floating-point geometry is used. This checks
existence of the archived motifs, not minimality or a complete polycube census.
"""
import hashlib,itertools,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
def determinant(a):
 if len(a)==1:return a[0][0]
 return sum((-1)**j*a[0][j]*determinant([r[:j]+r[j+1:] for r in a[1:]]) for j in range(len(a)))
def normalized(cells):
 lo=[min(p[i] for p in cells) for i in range(3)]
 return tuple(sorted(tuple(p[i]-lo[i] for i in range(3)) for p in cells))
def rotations(cells):
 result=set()
 for p in itertools.permutations(range(3)):
  parity=(-1)**sum(p[i]>p[j] for i in range(3) for j in range(i+1,3))
  for s in itertools.product((-1,1),repeat=3):
   if parity*s[0]*s[1]*s[2]==1:result.add(normalized([[s[i]*v[p[i]] for i in range(3)] for v in cells]))
 return result
def verify(data):
 B=data['offsets'];assert len(B)==3 and all(len(p)==3 for p in B)
 N=abs(determinant(B));assert N>0
 # Row-vector convention: x adj(B) modulo det(B) identifies x modulo Z^3 B.
 adj=[[(-1)**(i+j)*determinant([[B[r][c] for c in range(3) if c!=i] for r in range(3) if r!=j]) for j in range(3)] for i in range(3)]
 key=lambda p:tuple(sum(p[i]*adj[i][j] for i in range(3))%N for j in range(3))
 assert all(key(p)==(0,0,0) for p in B)
 proto=data['original_block'];assert len(set(map(tuple,proto)))==len(proto)
 ori=rotations(proto);seen=set()
 for tile in data['base_blocks']:
  assert len(tile)==len(proto) and normalized(tile) in ori
  for v in tile:
   assert all(type(x)==int for x in v)
   k=key(v);assert k not in seen;seen.add(k)
 # The quotient has index N. N distinct residues prove exact infinite cover.
 assert len(seen)==N==len(proto)*len(data['base_blocks'])
 return ori
if __name__=='__main__':
 audit=json.loads((ROOT/'data/heesch-catalog/papoutsis/audit.json').read_text());catalog={r['id']:r for r in json.loads((ROOT/'data/heesch-catalog/catalog.json').read_text())['systems']};verified={}
 for r in audit['certificates']:
  raw=(ROOT/r['localFile']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256'];data=json.loads(raw);ori=verify(data);assert len(data['base_blocks'])==r['copies'];verified[r['path']]=ori
 for m in audit['matches']:
  ours=catalog[m['id']]['voxels']
  if m['reflectionUsedForMatch']:ours=[[-v[0],v[1],v[2]] for v in ours]
  assert normalized(ours) in rotations(m['inputEntry'])
  if m['hasCertificate']:assert normalized(m['inputEntry']) in verified[m['path']]
 print(json.dumps({'verifiedPeriodicCertificates':len(verified),'catalogMappingsChecked':len(audit['matches']),'sourceCommit':audit['sourceCommit']}))
