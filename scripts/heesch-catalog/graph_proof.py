#!/usr/bin/env python3
"""Record a checkable DRUP certificate from the graph search, without SAT solving."""
import argparse,gzip,hashlib,importlib.util,json,pathlib,time
HERE=pathlib.Path(__file__).parent;spec=importlib.util.spec_from_file_location('graph',HERE/'graph.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
class ProofSearch(g.Search):
 def __init__(self,data,learn,seconds,k,stream):super().__init__(data,learn,seconds,k);self.stream=stream;self.additions=0
 def emit(self,roles):self.stream.write((' '.join(str(-v-1) for v in roles)+' 0\n').encode());self.additions+=1
 def learn_dead(self,q):
  before=len(self.rules);super().learn_dead(q)
  for r in self.rules[before:]:self.emit(r['roles'])
 def dfs(self,*args):
  result=super().dfs(*args)
  if not result:self.emit(self.stack)
  return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ids',required=True);p.add_argument('--k',type=int,choices=[1,2],default=2);p.add_argument('--seconds',type=float,default=180);p.add_argument('--out',required=True);a=p.parse_args();out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
 for row in json.load(open('data/heesch-catalog/catalog.json'))['systems']:
  if row['id'] not in a.ids.split(','):continue
  data=g.c.build(row['voxels'],a.k);stem=out/(row['id']+'-k'+str(a.k));path=pathlib.Path(str(stem)+'.drup.gz')
  with gzip.GzipFile(str(path),'wb',mtime=0) as f:
   search=ProofSearch(data,True,a.seconds,a.k,f);r=search.run();r['proofAdditions']=search.additions
  if r['status']!='UNSAT':path.unlink()
  else:
   h=hashlib.sha256()
   with gzip.open(path,'rb') as f:
    for block in iter(lambda:f.read(1<<20),b''):h.update(block)
   r['proofSHA256']=h.hexdigest()
  r.update(id=row['id'],k=a.k);pathlib.Path(str(stem)+'.json').write_text(json.dumps({key:v for key,v in r.items() if key not in ['rules','witness']}));print(json.dumps({key:v for key,v in r.items() if key not in ['rules','witness']}),flush=True)
