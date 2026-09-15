"""Compare nested raw-cloud libraries without conflating new bases and contexts."""
import hashlib
import json
from pathlib import Path
import sys

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
one_library,multi_library,one_check,multi_check,one_result,multi_result,output=sys.argv[1:]
a,b=map(read,[one_library,multi_library]);x,y=map(read,[one_result,multi_result]);cx,cy=map(read,[one_check,multi_check])
assert cx['resultHash']==sha(one_result) and cy['resultHash']==sha(multi_result)
assert x['portableHash']==sha(one_library) and y['portableHash']==sha(multi_library)
assert b['baseMotifs'][:len(a['baseMotifs'])]==a['baseMotifs'] and b['motifs'][:len(a['motifs'])]==a['motifs']
assert x['sourceHashes']==y['sourceHashes'] and x['codeHashes']==y['codeHashes']
old={r['id']:r for r in x['results']};rows=[]
for r in y['results']:
    before=old[r['id']];assert r['training']==before['training']
    previous={q['edge']:q for q in before['registrations']}
    common_base_coupled=0;common_base_factorized=0;new_base_coupled=0;new_base_factorized=0
    for q in r['registrations']:
        p=previous[q['edge']]
        for side in range(2):assert set(p['endpointMatches'][side])<=set(q['endpointMatches'][side])
        assert set(p['coupledMatches'])<=set(q['coupledMatches'])
        if q['base'] is not None and q['base']<len(a['baseMotifs']):
            common_base_coupled+=bool(q['coupledMatches']);common_base_factorized+=q['factorized']
        else:
            new_base_coupled+=bool(q['coupledMatches']);new_base_factorized+=q['factorized']
    rows.append(dict(id=r['id'],training=r['training'],edges=r['edges'],oneCoupled=before['coupledEdges'],oneFactorized=before['factorizedEdges'],
        multiCoupled=r['coupledEdges'],multiFactorized=r['factorizedEdges'],commonBaseCoupled=common_base_coupled,commonBaseFactorized=common_base_factorized,
        newBaseCoupled=new_base_coupled,newBaseFactorized=new_base_factorized,oneComplete=before['factorizedComplete'],multiComplete=r['factorizedComplete']))
group=[r for r in rows if not r['training']]
summary={k:sum(r[k] for r in group) for k in group[0] if k not in ['id','training']}
result=dict(scope=__doc__,inputHashes={Path(p).name:sha(p) for p in sys.argv[1:-1]},codeHash=sha(__file__),
    oneLibrary=a['summary'],multiLibrary=b['summary'],developmental=summary,results=rows,
    limits='Positive developmental-cover compatibility, not negative-connection specificity or tree search. Both raw-cloud lanes differ from the earlier prototype-compressed marking library.')
with Path(output).open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:v for k,v in result.items() if k!='results'}),flush=True)
