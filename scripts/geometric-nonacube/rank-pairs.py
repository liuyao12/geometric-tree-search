import argparse,json,itertools,importlib.util,pathlib
p=argparse.ArgumentParser();p.add_argument("folder");a=p.parse_args();ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('n',ROOT/'scripts/search-nonacube-two-corona.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
root=n.cells((0,(0,0,0)));pairs=sorted(n.candidates(n.halo(root)-root,root))
for path in sorted(pathlib.Path(a.folder).glob('*.json')):
 d=json.load(open(path));points=[tuple(p) for p in d['points']];idx={p:i for i,p in enumerate(points)};fields=[[set(x) for x in f] for f in d['fields']];full=set(range(len(d['states'])));rejected=[]
 for oi,c in pairs:
  t=tuple(2*x for x in c)
  for pi,p in enumerate(points):
   other=tuple(p[i]-t[i] for i in range(3));pj=idx.get(other)
   if pj is not None and not fields[0][pi]&fields[oi][pj]:rejected.append({'oi':oi,'translation':t,'at':p});break
 result={'source':path.name,'rank':d['result']['rank'],'action':d['result']['action'],'extent':d['result']['extentHalfUnits'],'examinedPairs':len(pairs),'rejectedPairs':len(rejected),'examples':rejected[:10]}
 print(json.dumps(result),flush=True)
