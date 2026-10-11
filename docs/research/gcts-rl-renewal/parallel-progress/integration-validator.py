"""Validate the isolated publication and exact evidence bindings, without reruns."""
import hashlib
import io
import json
import subprocess
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PUB = Path('/private/tmp/gcts-family-router-publish-20261010')
PRIOR = ROOT/'.gcts-active/proof-program-matched-boundaries-20261011/publication.json'
task = json.loads((OUT/'publication-files.json').read_text())
prior = json.loads(PRIOR.read_text())
paths = [r['path'] for r in task['files']]
assert len(paths) == len(set(paths))

def digest(data):
    return hashlib.sha256(data).hexdigest()

for r in task['files']:
    data = (PUB/r['path']).read_bytes()
    assert data == (ROOT/r['path']).read_bytes(), r['path']
    assert digest(data) == r['sha256'] and len(data) == r['bytes'], r['path']
changes = subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=PUB,text=True).splitlines()
assert {r[3:] for r in changes} == set(paths), 'unrelated publication files'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=PUB,text=True).strip() == task['previous_commit']
assert subprocess.check_output(['git','rev-parse','origin/main'],cwd=PUB,text=True).strip() == task['previous_commit']

expected = dict(prior['expected_live_sha256'])
expected.update({r['path']:r['sha256'] for r in task['files']})
locations = {}
objects = []

def register(data, name):
    locations.setdefault(digest(data),[]).append(name)
    if name.endswith('.json'):
        objects.append((name,json.loads(data)))

for name, sha in expected.items():
    data = (PUB/name).read_bytes()
    assert digest(data) == sha, ('public expected binding',name)
    register(data,name)
# Preserve the preceding exact embedded/archive binding receipt. All containing
# public artifacts above retain their byte hashes; this avoids redecoding the
# unchanged 234-MB prior payload bundle merely to rediscover its same locations.
binding_receipts = [ROOT/'.gcts-active/proof-program-native-registry-20261011/bindings.json', ROOT/'.gcts-active/proof-program-search-transport-20261011/artifact-validation.json', PRIOR.parent/'artifact-validation.json']
for receipt in binding_receipts:
    retained = json.loads(receipt.read_text())
    assert retained['status'] == 'passed'
    for r in retained.get('rows',retained.get('bindings',[])):
        for location in r['public_matches']:
            container = location.split('!',1)[0]
            if container in expected:
                locations.setdefault(r['sha256'],[]).append(location)
archives = []
def register_zip(data, label):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            if not name.endswith('/'):
                item=z.read(name)
                register(item,label+'!'+name)
                archives.append({'archive':label,'path':name,'bytes':len(item),'sha256':digest(item)})
                if name.endswith('.zip'):
                    register_zip(item,label+'!'+name)
for r in task['files']:
    if r['path'].endswith('.zip'):
        register_zip((PUB/r['path']).read_bytes(),r['path'])

bindings = []
missing = []
def binding(name, pin, origin, size=None):
    data = (ROOT/name).read_bytes()
    historical=any(origin.endswith('hierarchical-native-review-20261011/'+filename) for filename in ['review-v1.json','review-v2.json','review-v1-receipt.json','review-v2-receipt.json'])
    superseded=(digest(data)!=pin)
    if superseded:
        assert historical and name in ['research/gcts-rl-renewal/native_certificate_transport.py','research/gcts-rl-renewal/native_certificate_stage.py','research/gcts-rl-renewal/hierarchical_certificate_native.py','research/gcts-rl-renewal/hierarchical_certificate_native_audit.py'] and locations.get(pin), (origin,name,'changed root binding without exact retained historical snapshot')
    if size is not None and not superseded:
        assert len(data) == size, (origin,name,'changed root size')
    matches = locations.get(pin,[])
    row={'origin':origin,'path':name,'sha256':pin,'public_matches':matches,'current_root_bytes_match':not superseded,'historical_source_snapshot':superseded}
    bindings.append(row)
    if not matches:
        missing.append(row)

def walk(value, origin):
    if isinstance(value,dict):
        if isinstance(value.get('path'),str) and value['path'].startswith(('docs/','research/','.gcts-active/')) and isinstance(value.get('sha256'),str):
            binding(value['path'],value['sha256'],origin,value.get('bytes'))
        for name,item in value.items():
            if name.startswith(('docs/','research/','.gcts-active/')):
                pin = item.get('sha256') if isinstance(item,dict) else item
                if isinstance(pin,str) and len(pin)==64 and all(c in '0123456789abcdef' for c in pin):
                    binding(name,pin,origin,item.get('bytes') if isinstance(item,dict) else None)
                    continue
            walk(item,origin)
    elif isinstance(value,list):
        for item in value:
            walk(item,origin)

# New JSON documents and the frozen JSON plans/snapshots inside their archives.
for name,value in objects:
    if '!' in name or name in paths:
        walk(value,name)
if missing:
    (OUT/'missing-bindings.json').write_text(json.dumps(missing,indent=2)+'\n')
    print(json.dumps({'status':'missing-public-bindings','unique_files':len(set(r['path'] for r in missing)),'bindings':len(missing)}))
    raise SystemExit(1)

class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.ids=set()
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        if tag in ('a','script','link','img'):
            self.links.extend(attrs[k] for k in ('href','src') if k in attrs)

parsers={}
checks=[]
for name in paths:
    if not name.endswith('.html'):
        continue
    page=PUB/name
    doc=Links(); doc.feed(page.read_text()); parsers[page]=doc
    for link in doc.links:
        url=urlsplit(link)
        if url.scheme or url.netloc:
            continue
        target=(page.parent/unquote(url.path)).resolve() if url.path else page
        if target.is_dir():
            target=target/'index.html'
        assert target.exists(), (name,link)
        if url.fragment and target.suffix=='.html':
            parser=parsers.get(target)
            if parser is None:
                parser=Links(); parser.feed(target.read_text()); parsers[target]=parser
            assert unquote(url.fragment) in parser.ids, (name,link)
        checks.append({'from':name,'link':link})

result={'status':'prepared-validated','base_commit':task['previous_commit'],'task_paths':paths,'task_files':len(paths),'task_bytes':task['total_bytes'],'expected_live_sha256':expected,'expected_live_bytes':{n:(PUB/n).stat().st_size for n in expected},'bindings':len(bindings),'archive_entries':len(archives),'static_link_checks':len(checks),'broad_program_status':'active','scope':task['scope'],'prior_publication_receipt_sha256':digest(PRIOR.read_bytes()),'prior_embedded_bindings_receipt_sha256':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in binding_receipts},'retained_binding_method':'Reuse the preceding exact embedded/archive location receipt after checking every containing public artifact byte hash; all new archives decoded and reconciled.'}
(OUT/'publication.json').write_text(json.dumps(result,indent=2)+'\n')
(OUT/'artifact-validation.json').write_text(json.dumps({'status':'passed','bindings':bindings,'archives':archives,'static_links':checks},indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','task_files','task_bytes','bindings','archive_entries','static_link_checks']}))
