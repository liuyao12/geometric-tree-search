#!/usr/bin/env python3
"""Extract real coronas from published infinite tilings, then test both encoders.

Independent geometry uses cubical complexes (all incident voxels at vertices),
not the encoder's halo routine. Exact quotient lookup recovers a tile covering
any voxel, without truncating the periodic tiling to a guessed search box.
"""
import argparse,hashlib,importlib.util,itertools,json,pathlib,time
from pysat.solvers import Glucose3
from verify_papoutsis import determinant,normalized,rotations,verify as verify_periodic
import corona
ROOT=pathlib.Path(__file__).resolve().parents[2]
F=ROOT/'data/heesch-catalog';OUT=F/'positive-controls';OUT.mkdir(exist_ok=True)
def adjugate(B):
 return [[(-1)**(i+j)*determinant([[B[r][c] for c in range(3) if c!=i] for r in range(3) if r!=j]) for j in range(3)] for i in range(3)]
def rowmul(x,B):return tuple(sum(x[i]*B[i][j] for i in range(3)) for j in range(3))
def plus(x,y):return tuple(a+b for a,b in zip(x,y))
def minus(x,y):return tuple(a-b for a,b in zip(x,y))
def vertex_star(cells):
 # Closed unit cubes meet at faces, edges or vertices precisely when their
 # incident corner sets intersect. Complete every vertex's eight voxel sectors.
 vertices={plus(v,d) for v in cells for d in itertools.product((0,1),repeat=3)}
 return {minus(v,d) for v in vertices for d in itertools.product((0,1),repeat=3)}
def orient_to_root(tile,root):
 for perm in itertools.permutations(range(3)):
  parity=(-1)**sum(perm[i]>perm[j] for i in range(3) for j in range(i+1,3))
  for signs in itertools.product((-1,1),repeat=3):
   if parity*signs[0]*signs[1]*signs[2]!=1:continue
   rot=lambda x:tuple(signs[i]*x[perm[i]] for i in range(3))
   cells=list(map(rot,tile));offset=tuple(-min(x[i] for x in cells) for i in range(3))
   if frozenset(plus(x,offset) for x in cells)==root:return rot,offset
 raise AssertionError('No proper rotation to canonical root')
def oracle(certificate,root,root_role):
 rot,offset=orient_to_root(certificate['base_blocks'][root_role],root)
 tiles=[tuple(plus(rot(v),offset) for v in tile) for tile in certificate['base_blocks']]
 B=[rot(v) for v in certificate['offsets']];det=determinant(B);A=adjugate(B);mod=abs(det)
 key=lambda p:tuple(x%mod for x in rowmul(p,A));representatives={}
 for role,tile in enumerate(tiles):
  for v in tile:
   k=key(v);assert k not in representatives;representatives[k]=(role,v)
 assert len(representatives)==mod
 def owner(q):
  role,rep=representatives[key(q)];delta=minus(q,rep);coeff=rowmul(delta,A)
  assert all(x%det==0 for x in coeff)
  assert rowmul(tuple(x//det for x in coeff),B)==delta
  return frozenset(plus(v,delta) for v in tiles[role])
 assert all(owner(q)==root for q in root)
 return owner
def extract(owner,root):
 # Every tile meeting the root is first layer; every new tile meeting that
 # whole layer is second layer. This is computed solely from the infinite tiling.
 first={owner(q) for q in vertex_star(root)}-{root}
 inner=root.union(*first);second={owner(q) for q in vertex_star(inner)}-first-{root}
 return first,second
def independent_check(root,first,second,prototype):
 seen=set();ori=rotations(prototype)
 for t in [root,*first,*second]:
  assert normalized(t) in ori and not seen.intersection(t);seen.update(t)
 assert all(t&vertex_star(root) for t in first)
 assert all(not (t&vertex_star(root)) for t in second)
 assert vertex_star(root)<=seen and vertex_star(root.union(*first))<=seen
 return {'firstLayerTiles':len(first),'secondLayerTiles':len(second),'totalTiles':1+len(first)+len(second),'coveredVoxels':len(seen)}
def pose(tile,shapes):
 lo=tuple(min(v[i] for v in tile) for i in range(3));shape=normalized(tile)
 return (shapes.index(shape),lo)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--ids',default='polycube_p9_02127,polycube_p9_24025');args=ap.parse_args()
 audit=json.loads((F/'papoutsis/audit.json').read_text());rows={r['id']:r for r in json.loads((F/'catalog.json').read_text())['systems']};receipts=[]
 spec=importlib.util.spec_from_file_location('original',ROOT/'scripts/search-nonacube-two-corona.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
 for id in args.ids.split(','):
  match=next(m for m in audit['matches'] if m['id']==id);source=next(c for c in audit['certificates'] if c['path']==match['path']);cert=json.loads((ROOT/source['localFile']).read_text());verify_periodic(cert)
  shapes=tuple(sorted(rotations(rows[id]['voxels'])));old.SHAPES=shapes;data=old.build();generic=corona.build(rows[id]['voxels'],2)
  assert data['clauses']==generic['clauses'] and data['universe']==generic['universe'] and data['root']==generic['root']
  cnf=('p cnf %d %d\n'%(data['stats']['variables'],len(data['clauses']))+''.join(' '.join(map(str,c))+' 0\n' for c in data['clauses'])).encode()
  ids={s:i+1 for i,s in enumerate(data['universe'])};root=data['root'];results=[]
  for role in range(len(cert['base_blocks'])):
   owner=oracle(cert,root,role);first,second=extract(owner,root);check=independent_check(root,first,second,rows[id]['voxels'])
   chosen={ids[pose(tile,shapes)] for tile in first|second} # Missing candidates fail here.
   # Fix EVERY placement variable. Only cardinality auxiliaries remain free.
   assumptions=[i if i in chosen else -i for i in range(1,len(ids)+1)]
   started=time.perf_counter()
   with Glucose3(bootstrap_with=data['clauses']) as solver:
    assert solver.solve(assumptions=assumptions)
    model=set(solver.get_model());assert all(any(lit in model for lit in clause) for clause in data['clauses'])
    # Negative controls keep all other placement variables fixed. Removing a
    # first-layer tile leaves the root uncovered; removing a second-layer tile
    # leaves an active first-neighbor boundary uncovered.
    for layer in [first,second]:
     removed=min(ids[pose(t,shapes)] for t in layer)
     broken=[-lit if lit==removed else lit for lit in assumptions]
     assert solver.solve(assumptions=broken) is False
   results.append(dict(rootMotifRole=role,formulaAccepts=True,allClausesChecked=True,missingFirstLayerTileRejected=True,missingSecondLayerTileRejected=True,**check))
   if role==0:
    witness={'id':id,'sourceCertificate':source['localFile'],'root':sorted(root),'corona1':[sorted(t) for t in sorted(first,key=lambda t:sorted(t))],'corona2':[sorted(t) for t in sorted(second,key=lambda t:sorted(t))],**check}
    (OUT/(id+'-periodic-coronas.json')).write_text(json.dumps(witness,indent=2)+'\n')
  receipt={'id':id,'motifCopies':len(cert['base_blocks']),'sourceCertificate':source['localFile'],'allRootRolesChecked':len(results),'sameClausesInOriginalAndGenericEncoder':True,'formulaSHA256':hashlib.sha256(cnf).hexdigest(),'results':results}
  receipts.append(receipt);print(json.dumps({k:v for k,v in receipt.items() if k!='results'}),flush=True)
 (OUT/'periodic-witness-checks.json').write_text(json.dumps(receipts,indent=2)+'\n')
if __name__=='__main__':main()
