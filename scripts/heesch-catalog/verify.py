#!/usr/bin/env python3
"""Independent raw-voxel witness check plus external UNSAT check and regeneration."""
import argparse,gzip,lzma,hashlib,importlib.util,itertools,json,pathlib,subprocess,tempfile
HERE=pathlib.Path(__file__).parent;spec=importlib.util.spec_from_file_location('corona',HERE/'corona.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
p=argparse.ArgumentParser();p.add_argument('--data',default='data/heesch-catalog');p.add_argument('--checker',required=True);p.add_argument('--subdir',default='runs');a=p.parse_args();folder=pathlib.Path(a.data);catalog={r['id']:r for r in json.loads((folder/'catalog.json').read_text())['systems']};results=[]
for path in sorted((folder/a.subdir).glob('*-k*.json')):
 r=json.loads(path.read_text());row=catalog[r['id']];d=c.build(row['voxels'],r['k']);assert len(d['clauses'])==r['clauses']
 receipt={'id':r['id'],'k':r['k'],'status':r['status']}
 if r['status']=='SAT':
  w=r['witness'];root=set(map(tuple,w['root']));assert c.norm(root) in d['shapes'];tiles=[set(map(tuple,t)) for t in w['tiles']];occupied=set(root)
  for t in tiles:assert c.norm(t) in d['shapes'] and not t&occupied;occupied.update(t)
  inner=set(root);left=list(tiles)
  for k in range(r['k']):
   halo={tuple(v[i]+s[i] for i in range(3)) for v in inner for s in itertools.product((-1,0,1),repeat=3)};assert halo<=occupied
   layer=[t for t in left if t&halo];left=[t for t in left if not t&halo];inner.update(set().union(*layer))
  receipt['voxelWitnessVerified']=True
 if r['status']=='UNSAT':
  cnf='p cnf %d %d\n'%(d['variables'],len(d['clauses']))+''.join(' '.join(map(str,x))+' 0\n' for x in d['clauses']);assert hashlib.sha256(cnf.encode()).hexdigest()==r['formulaSHA256'];stem=str(path)[:-5]
  opener,suffix=(gzip.open,'.gz') if pathlib.Path(stem+'.cnf.gz').exists() else (lzma.open,'.xz');assert opener(stem+'.cnf'+suffix,'rb').read()==cnf.encode();proof=opener(stem+'.drup'+suffix,'rb').read();assert hashlib.sha256(proof).hexdigest()==r['proofSHA256']
  with tempfile.TemporaryDirectory() as tmp:
   cp=pathlib.Path(tmp)/'p.cnf';pp=pathlib.Path(tmp)/'p.drup';cp.write_text(cnf);pp.write_bytes(proof);run=subprocess.run([a.checker,str(cp),str(pp)],capture_output=True,text=True)
   assert run.returncode==0 and 's VERIFIED' in run.stdout,(r['id'],run.stdout,run.stderr);receipt['dratVerified']=True;receipt['checkerWarnings']=run.stdout.count('WARNING:');receipt['checkerSummary']='\n'.join(line.rstrip() for line in run.stdout.splitlines() if 'WARNING:' not in line)[-2000:];log=pathlib.Path(stem+'.checker.log.xz');log.write_bytes(lzma.compress(run.stdout.encode()));receipt['checkerLog']=str(log.relative_to(folder))
 results.append(receipt);print(json.dumps(receipt),flush=True)
(folder/(a.subdir+'-verification.json')).write_text(json.dumps(results,indent=2)+'\n')
