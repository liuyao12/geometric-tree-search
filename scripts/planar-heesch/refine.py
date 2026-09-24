"""Revisit unresolved census matches; preserve shorter attempts."""
import argparse,collections,json,pathlib
from engine import Grid
from run import write_run
p=argparse.ArgumentParser();p.add_argument('--family',required=True);p.add_argument('--size',type=int,required=True);p.add_argument('--seconds',type=float,default=15);p.add_argument('--checker',required=True);p.add_argument('--subdir',default='longer');a=p.parse_args()
base=pathlib.Path('data/planar-heesch/census');out=base/a.subdir;out.mkdir(exist_ok=True)
p=base/f'{a.family}-{a.size}-summary.json';summary=json.loads(p.read_text());catalog={r['id']:r for r in json.load(open('data/planar-heesch/catalog.json'))}
for row in summary['rows']:
 if row['status']!='unknown' or not row.get('publishedId'):continue
 src=catalog[row['publishedId']].copy();src['id']=row['id']
 previous=json.loads((base/row['runs'][-1]).read_text());start=previous['depth'] if previous['status']=='unknown' else previous['depth']+1
 for k in range(start,6):
  r=write_run(src,k,a.seconds,out,a.checker);row['runs'].append(a.subdir+'/'+row['id']+f'-k{k}.json')
  if r['status']=='SAT':row['lowerBound']=max(k,row['lowerBound'])
  elif r['status']=='UNSAT':row.update(status='finite',Hh=k-1,proofVerified=r['proofVerified']);break
  else:break
 (base/(row['id']+'.json')).write_text(json.dumps(row))
 summary['classification']=dict(collections.Counter(x['status'] for x in summary['rows']));p.write_text(json.dumps(summary))
 print(row['id'],row['status'],row.get('Hh'),flush=True)
