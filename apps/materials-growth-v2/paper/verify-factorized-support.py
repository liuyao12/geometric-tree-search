"""Independent brute-array replay of signature-support elimination records."""
import collections,hashlib,json,pathlib,sys
import numpy as np
source_path,blocks_path,filtered_path,proof_path,output=map(pathlib.Path,sys.argv[1:])
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads(source_path.read_text());data=json.loads(blocks_path.read_text());filtered=json.loads(filtered_path.read_text());proof=json.loads(proof_path.read_text())
assert proof['originalBlocksHash']==digest(blocks_path) and proof['sourceModelHash']==digest(source_path) and proof['filteredHash']==digest(filtered_path)
def feature(c):
    groups=collections.defaultdict(list)
    for color,vector in zip(c['colors'],c['vectors'],strict=True):groups[json.dumps(color,sort_keys=True)].append(vector)
    layout=tuple((k,len(groups[k])) for k in sorted(groups))
    value=np.array([x for k in sorted(groups) for axis in range(3) for x in sorted(v[axis] for v in groups[k])])
    assert np.isfinite(value).all() and np.max(np.abs(value))<=10000
    return layout,value
reports=[]
for row,new,p in zip(data['models'],filtered['models'],proof['proofs'],strict=True):
    assert row['capacity']==2 and p['threshold']==2*row['cloudRadius']+1e-8
    for mark,atom in p['anchorWitnesses'].items():
        assert atom in row['required']
        assert {i for i,b in enumerate(row['blocks']) if mark in b['markPoints']}=={i for i,b in enumerate(row['blocks']) if any(t['point']==atom for t in b['t'])}
    records={};groups=collections.defaultdict(list);count={}
    for i,b in enumerate(row['blocks']):
        assert all(t['value']==1 for t in b['t']) and len(set(b['markPoints']))==2
        for side,cs in enumerate(b['endpointChoices']):
            count[i,side]=len(cs)
            for j,c in enumerate(cs):
                layout,x=feature(source['clouds'][c['cloud']]);key=(b['markPoints'][side],layout);token=(i,side,j)
                records[token]=(key,x);groups[key].append(token)
    arrays={key:np.array([records[token][1] for token in tokens]) for key,tokens in groups.items()}
    live={key:np.ones(len(tokens),dtype=bool) for key,tokens in groups.items()};offset={t:(key,k) for key,tokens in groups.items() for k,t in enumerate(tokens)}
    removed=set()
    for removal in p['removals']:
        token=(removal['block'],removal['side'],removal['index']);assert token not in removed and token in records
        i,side,j=token;key,x=records[token]
        if removal['reason']=='empty-other-endpoint':assert count[i,1-side]==0
        else:
            assert removal['reason']=='no-complement-signature'
            # No producer KD tree or support routine is used in this check.
            near=np.flatnonzero(live[key] & (np.max(np.abs(arrays[key]-x),axis=1)<=p['threshold']))
            for k in near:
                other,s,_=groups[key][k]
                assert count[other,1-s]==0 or row['blocks'][other]['inventory']==row['blocks'][i]['inventory']
        removed.add(token);count[i,side]-=1;kkey,index=offset[token];live[kkey][index]=False
    allowed=[[[j for j in range(len(b['endpointChoices'][side])) if (i,side,j) not in removed] for side in (0,1)] for i,b in enumerate(row['blocks'])]
    assert allowed==p['allowed']
    for i,(a,b) in enumerate(zip(row['blocks'],new['blocks'],strict=True)):
        for field in ('id','inventory','t','markPoints','rotationRow'):assert a[field]==b[field]
        for side in (0,1):assert b['endpointChoices'][side]==[dict(a['endpointChoices'][side][j],originalIndex=j) for j in allowed[i][side]]
    byid={b['id']:b for b in new['blocks']}
    for oldlift,lift in zip(row['trainingLifts'],new['trainingLifts'],strict=True):
        assert oldlift['name']==lift['name']
        for old,c in zip(oldlift['selected'],lift['selected'],strict=True):
            assert old['block']==c['block'];b=byid[c['block']]
            assert b['endpointChoices'][0][c['left']]['originalIndex']==old['left'] and b['endpointChoices'][1][c['right']]['originalIndex']==old['right']
    reports.append({'file':row['file'],'removedRecordsChecked':len(removed),'trainingLiftsPreserved':len(new['trainingLifts'])})
    print(json.dumps(reports[-1]),flush=True)
with output.open('x') as f:json.dump({'scope':__doc__,'proofHash':digest(proof_path),'filteredHash':digest(filtered_path),'verifierHash':digest(pathlib.Path(__file__)),'results':reports,'limits':'Necessary signature relaxation only; surviving cloud pairs need not agree. Finite half-weight model, not a new learned law or continuous-pose certificate.'},f,indent=2)
