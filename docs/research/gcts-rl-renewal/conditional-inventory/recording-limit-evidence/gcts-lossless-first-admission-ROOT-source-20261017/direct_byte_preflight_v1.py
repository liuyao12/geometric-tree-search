"""Complete file read/hash/EOF only; no scientific module evaluation."""
import hashlib,json
from pathlib import Path
S=Path('/private/tmp/gcts-lossless-first-admission-ROOT-source-20261017');P=Path('/private/tmp/gcts-first-admission-ROOT-source-20261017')
c=json.loads((S/'Source-contract-v1.json').read_bytes());oldc=json.loads((P/'Source-contract-v1.json').read_bytes());old=json.loads((P/'ROOT-direct-byte-preflight-v1.json').read_bytes())
refs={x['path']:x for x in old['files']}
for role in ('intake','receiver_cases','family_engine'):refs.pop(oldc['sources'][role]['path'])
for x in [*c['sources'].values(),*c['inputs'].values(),*c['original_model_sources'].values(),*c['original_model_inputs'].values()]:refs[x['path']]=x
files=[]
for path,x in sorted(refs.items()):
    with Path(path).open('rb')as f:
        b=f.read(16777217);assert len(b)<=16777216 and f.read(1)==b''
    v={'path':path,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};assert v==x;files.append(v)
v={'schema':'ROOT-lossless-first-admission-direct-byte-preflight-v1','scope':'Same original and current scientific readset; only intake/helper/engine diagnostic implementation pins changed. Whole bytes/EOF/hash only; no OS-cache-cold claim.','files_count':len(files),'bytes':sum(x['bytes']for x in files),'files':files,'scientific_calls':0,'sources_evaluated':False}
p=S/'ROOT-direct-byte-preflight-v1.json';assert not p.exists();p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps({'files':len(files),'bytes':v['bytes'],'scientific_calls':0}))
