"""Full byte/hash/EOF residency check only; no model or module evaluation."""
from pathlib import Path
import json,hashlib
S=Path('/private/tmp/gcts-head-gated-ROOT-source-20261017');P=Path('/private/tmp/gcts-receiver-inference-ROOT-source-20261017')
c=json.loads((S/'Source-contract-v1.json').read_bytes());oldc=json.loads((P/'Source-contract-v2.json').read_bytes());old=json.loads((P/'ROOT-direct-byte-preflight-v1.json').read_bytes())
refs={x['path']:x for x in old['files']}
for role in ('intake','receiver_provider','family_engine','receiver_cases'):refs.pop(oldc['sources'][role]['path'])
for x in [*c['sources'].values(),*c['inputs'].values(),*c['original_model_sources'].values(),*c['original_model_inputs'].values()]:refs[x['path']]=x
files=[]
for path,x in sorted(refs.items()):
 with Path(path).open('rb')as f:
  b=f.read(16777217);assert len(b)<=16777216 and f.read(1)==b''
 v={'path':path,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};assert v==x;files.append(v)
v={'schema':'ROOT-head-gated-direct-byte-preflight-v1','scope':'Original prior direct caller-readset with current22source pins and declared original17 authority union; full byte/hash/EOF data only, no OS-cache-cold claim.','files_count':len(files),'bytes':sum(x['bytes']for x in files),'files':files,'scientific_calls':0,'sources_evaluated':False}
p=S/'ROOT-direct-byte-preflight-v1.json';assert not p.exists();p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n');print(json.dumps({'files':len(files),'bytes':v['bytes'],'scientific_calls':0}))
