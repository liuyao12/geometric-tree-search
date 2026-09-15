"""Verify proof-prefix and accounting consistency, not timing independently."""
import hashlib
import json
from pathlib import Path
import sys
priorp,checkp,resultp,out=map(Path,sys.argv[1:]);prior,check,result=[json.loads(p.read_text()) for p in [priorp,checkp,resultp]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert result['resumeHash']==check['resultHash']==sha(priorp) and result['resumeCheckHash']==sha(checkp)
assert result['sourceHash']==prior['sourceHash']==check['modelHash'] and result['kernelHash']==prior['kernelHash']
n=len(prior['cores']);assert check['verifiedCores']==result['initialCoreCount']==n and result['cores'][:n]==prior['cores']
assert result['totalRounds']==prior.get('totalRounds',len(prior['rounds']))+len(result['rounds'])
assert abs(result['cumulativeSeconds']-prior.get('cumulativeSeconds',prior['secondsIncludingRestarts'])-result['secondsIncludingRestarts'])<1e-8
added=0
for i,r in enumerate(result['rounds']):
    assert r['round']==i and r['priorCores']==n+added and r['rootRollback']
    if r['newCoreSize'] is not None:
        assert len(result['cores'][n+added]['owners'])==r['newCoreSize'];added+=1
assert len(result['cores'])==n+added
report=dict(priorHash=sha(priorp),resultHash=sha(resultp),verifierHash=sha(Path(__file__)),preservedProofPrefix=n,additionalCores=added,totalRounds=result['totalRounds'],cumulativeSeconds=result['cumulativeSeconds'],limits='Checks recorded hash links, proof-prefix immutability, round counts and arithmetic accounting. Does not independently measure elapsed time or verify new proof semantics; use the separate proof-DAG checker.')
with out.open('x') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
