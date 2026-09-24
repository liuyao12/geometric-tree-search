"""Find a simply connected witness by sound hole cuts in the same universe.

Each cut forbids retaining an enclosing boundary while leaving a hole cell
empty. It permits filling that cell. Parent-contact clauses exclude extraneous
components; this routine is used for positive witnesses, not upper bounds.
"""
import argparse,json,pathlib,threading,time
from pysat.solvers import Glucose3
from engine import Grid,build,verify

def solve_holefree(row,depth,seconds):
 g=Grid(row['family']);shape=g.from_source(row['cells']);d=build(g,shape,depth);inc={}
 for (i,j),v in d['ids'].items():
  for q in d['tiles'][i]:inc.setdefault((q,j),[]).append(v)
 # Require every selected tile to have a selected parent at a smaller label.
 for (i,j),v in d['ids'].items():
  if j==1:continue
  near=g.halo(d['tiles'][i])-d['tiles'][i]
  parents={w for q in near for h in range(1,j) for w in inc.get((q,h),())}
  d['clauses'].append([-v]+sorted(parents))
 cuts=0;start=time.perf_counter()
 with Glucose3(bootstrap_with=d['clauses']) as s:
  timer=threading.Timer(seconds,s.interrupt);timer.start()
  try:
   while True:
    status=s.solve_limited(expect_interrupt=True)
    if status is not True:return dict(status='unknown' if status is None else 'UNSAT',cuts=cuts,seconds=time.perf_counter()-start)
    model=set(s.get_model());selected={i:v for (i,j),v in d['ids'].items() if v in model}
    tiles=[d['tiles'][i] for i in selected];occupied=set(d['root']).union(*tiles);holes=g.holes(occupied)
    if not holes:
     witness=verify(g,shape,d['root'],tiles,depth);assert witness['holeFree']
     return dict(status='SAT',witness=witness,cuts=cuts,seconds=time.perf_counter()-start)
    boundary={(x+a,y+b,t) for x,y,z in holes for a,b,t in g.edges[z]}-holes
    rim=[-v for i,v in selected.items() if d['tiles'][i]&boundary]
    for q in sorted(holes):
     fill=[v for j in range(1,depth+1) for v in inc.get((q,j),())]
     s.add_clause(rim+fill);cuts+=1
  finally:timer.cancel();timer.join()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seconds',type=float,default=90);p.add_argument('--ids',default='omino-17-44,omino-17-193,hex-11-19,iamond-20-131');a=p.parse_args()
 for row in json.load(open('data/planar-heesch/catalog.json')):
  if row['id'] not in a.ids.split(','):continue
  r=solve_holefree(row,row['Hc'],a.seconds);r.update(id=row['id'],depth=row['Hc'])
  pathlib.Path('data/planar-heesch/runs',row['id']+'-holefree.json').write_text(json.dumps(r))
  print({k:v for k,v in r.items() if k!='witness'},flush=True)
