#!/usr/bin/env python3
"""Regenerate the exact formula and optionally independently replay its proof."""
import argparse, gzip, hashlib, importlib.util, json, pathlib, subprocess, tempfile
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--drat-trim');a=ap.parse_args()
root=pathlib.Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('corona',root/'scripts/search-nonacube-two-corona.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);d=m.build()
cnf=(f"p cnf {d['stats']['variables']} {len(d['clauses'])}\n"+''.join(' '.join(map(str,c))+' 0\n' for c in d['clauses'])).encode()
p=root/'data/nonacube-search-replay';receipt=json.loads((p/'proof-receipt.json').read_text())
assert cnf==gzip.decompress((p/'proof.cnf.gz').read_bytes())
proof=gzip.decompress((p/'proof.drup.gz').read_bytes())
assert hashlib.sha256(cnf).hexdigest()==receipt['hashes']['cnf']
assert hashlib.sha256(proof).hexdigest()==receipt['hashes']['drup']
print('Fresh formula matches the published proof input; both hashes verified.',flush=True)
if a.drat_trim:
    with tempfile.TemporaryDirectory() as t:
        c=pathlib.Path(t)/'formula.cnf';c.write_bytes(cnf)
        r=pathlib.Path(t)/'proof.drup';r.write_bytes(proof)
        result=subprocess.run([str(pathlib.Path(a.drat_trim).resolve()),str(c),str(r)],capture_output=True,text=True)
        print(result.stdout)
        assert result.returncode==0 and 's VERIFIED' in result.stdout
else:print('Proof not replayed in this invocation. Supply --drat-trim /path/to/drat-trim.')
