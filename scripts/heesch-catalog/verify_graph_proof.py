#!/usr/bin/env python3
"""Regenerate each graph-search CNF and check its full DRUP proof independently."""
import argparse,gzip,hashlib,importlib.util,json,pathlib,subprocess,tempfile,lzma
HERE=pathlib.Path(__file__).parent;ROOT=HERE.parents[1];F=ROOT/'data/heesch-catalog';spec=importlib.util.spec_from_file_location('corona',HERE/'corona.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
p=argparse.ArgumentParser();p.add_argument('--checker',required=True);a=p.parse_args();rows={r['id']:r for r in json.loads((F/'catalog.json').read_text())['systems']};results=[]
for path in sorted((F/'graph-proofs').glob('*-k*.json')):
 r=json.loads(path.read_text())
 if r['status']!='UNSAT':continue
 data=c.build(rows[r['id']]['voxels'],r['k']);cnf=('p cnf %d %d\n'%(data['variables'],len(data['clauses']))+''.join(' '.join(map(str,x))+' 0\n' for x in data['clauses'])).encode();proof=gzip.open(str(path)[:-5]+'.drup.gz','rb').read();assert hashlib.sha256(proof).hexdigest()==r['proofSHA256']
 with tempfile.TemporaryDirectory() as tmp:
  cp=pathlib.Path(tmp)/'p.cnf';pp=pathlib.Path(tmp)/'p.drup';cp.write_bytes(cnf);pp.write_bytes(proof);checked=subprocess.run([a.checker,str(cp),str(pp)],capture_output=True,text=True);assert checked.returncode==0 and 's VERIFIED' in checked.stdout,(r['id'],checked.stdout[-3000:]);log=path.with_suffix('.checker.log');log.write_text('\n'.join(line.rstrip() for line in checked.stdout.splitlines())+'\n')
 existing=next((candidate for candidate in [F/'deeper'/(r['id']+'-k'+str(r['k'])+'.cnf.xz'),F/'runs'/(r['id']+'-k'+str(r['k'])+'.cnf.gz')] if candidate.exists()),None)
 if existing:
  op=lzma.open if existing.suffix=='.xz' else gzip.open
  assert op(existing,'rb').read()==cnf
 else:
  existing=path.with_suffix('.cnf.xz');existing.write_bytes(lzma.compress(cnf))
 receipt={'id':r['id'],'k':r['k'],'verified':True,'formulaSHA256':hashlib.sha256(cnf).hexdigest(),'proofSHA256':r['proofSHA256'],'proofAdditions':r['proofAdditions'],'formulaArchive':str(existing.relative_to(ROOT)),'proofArchive':str(path.with_suffix('.drup.gz').relative_to(ROOT)),'checkerLog':str(log.relative_to(ROOT))};results.append(receipt);print(json.dumps(receipt),flush=True)
(F/'graph-proof-verification.json').write_text(json.dumps(results,indent=2)+'\n')
