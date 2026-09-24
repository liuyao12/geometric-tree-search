#!/usr/bin/env python3
"""Rebuild the geometric reduction; audit all learned anchor patterns; optionally check DRUP."""
import argparse,collections,gzip,hashlib,importlib.util,json,pathlib,subprocess,tempfile
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('direct',HERE/'build.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 return h.hexdigest()
def verify(folder,checker=None):
 folder=pathlib.Path(folder);data=b.build();hist=collections.Counter();deletions=empty=0;atoms=0;examples=[];wanted={2,3,4,5,6,8,10,15,20,30,43};count=0;proofhash=hashlib.sha256()
 with tempfile.TemporaryDirectory(prefix='nonacube-anchor-check-') as temp:
  stem=pathlib.Path(temp)/'problem';b.write(data,stem)
  assert folder.joinpath('placements.txt').read_bytes()==stem.with_suffix('.placements.txt').read_bytes()
  with gzip.open(folder/'problem.cnf.gz','rb') as f:assert hashlib.sha256(f.read()).hexdigest()==digest(stem.with_suffix('.cnf'))
  poses=data['universe'];assert len(set(poses))==len(poses);positions={s:i+1 for i,s in enumerate(poses)}
  # At active root anchor 0, prototype offset -center reconstructs exactly the
  # intended placement. Distinct roles in a channel cannot alias each other.
  for i,(oi,c) in enumerate(poses,1):offset=tuple(-x for x in c);assert positions[(oi,tuple(-x for x in offset))]==i
  voxels=[b.n.cells(s) for s in poses];proof=pathlib.Path(temp)/'proof.drup'
  with gzip.open(folder/'anchor-proof.drup.gz','rb') as source,proof.open('wb') as out:
   for line in source:
    proofhash.update(line);out.write(line);row=line.split()
    if row and row[0]==b'd':deletions+=1;continue
    values=list(map(int,row));assert values and values[-1]==0
    if len(values)==1:empty+=1;continue
    assert all(-len(poses)<=v<0 for v in values[:-1]);ids=[-v for v in values[:-1]];assert len(ids)==len(set(ids))
    k=len(ids);hist[k]+=1;atoms+=k;count+=1
    if k in wanted:
     occupied=set(data['root']);packing=True
     for v in ids:
      if occupied&voxels[v-1]:packing=False;break
      occupied.update(voxels[v-1])
     if packing:examples.append({'learnedIndex':count,'roles':k,'placements':[poses[v-1] for v in ids],'variables':ids,'nonoverlapWithRoot':True});wanted.remove(k)
  assert empty>0
  result={'formula':data['stats'],'formulaSHA256':digest(stem.with_suffix('.cnf')),'proofSHA256':proofhash.hexdigest(),'placementSHA256':digest(folder/'placements.txt'),'patterns':count,'atoms':atoms,'largestPattern':max(hist),'unaryPatterns':hist[1],'sizeHistogram':dict(sorted(hist.items())),'proofDeletions':deletions,'terminalEmptyLines':empty,'allLearnedRulesArePlacementOnly':True,'geometricAnchorBijection':True,'patternRolesDistinct':True,'drupVerified':False}
  if checker:
   completed=subprocess.run([str(checker),str(stem.with_suffix('.cnf')),str(proof)],capture_output=True,text=True)
   if completed.returncode or 's VERIFIED' not in completed.stdout:raise AssertionError(completed.stdout+completed.stderr)
   result.update(drupVerified=True,checkerSHA256=digest(checker));(folder/'proof-check.log').write_text(completed.stdout+completed.stderr)
 return result,examples
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',default=str(ROOT/'data/nonacube-geometric-learning'));p.add_argument('--drat-trim');p.add_argument('--output');p.add_argument('--examples');a=p.parse_args();result,examples=verify(a.data,a.drat_trim)
 if a.output:pathlib.Path(a.output).write_text(json.dumps(result,indent=2)+'\n')
 if a.examples:pathlib.Path(a.examples).write_text(json.dumps(examples,indent=2)+'\n')
 print(json.dumps(result))
