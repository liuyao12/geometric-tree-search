"""Independent brute-array completeness check for the conservative partner index."""
import collections,hashlib,json,pathlib,sys
import numpy as np
source_path,blocks_path,index_path,output=map(pathlib.Path,sys.argv[1:])
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=json.loads(source_path.read_text());data=json.loads(blocks_path.read_text());index=json.loads(index_path.read_text())
assert index['sourceModelHash']==digest(source_path) and index['blocksHash']==digest(blocks_path)
reports=[]
for row,graph in zip(data['models'],index['models'],strict=True):
    assert (row['file'],row['fold'])==(graph['file'],graph['fold'])
    expected_records=[[i,s,j] for i,b in enumerate(row['blocks']) for s,cs in enumerate(b['endpointChoices']) for j in range(len(cs))]
    assert expected_records==graph['records'];assert len(graph['neighbors'])==len(expected_records)
    threshold=2*row['cloudRadius']+1e-8;assert threshold==graph['threshold']
    groups=collections.defaultdict(list);vectors=[];inventories=[]
    for k,(i,s,j) in enumerate(expected_records):
        b=row['blocks'][i];cloud=source['clouds'][b['endpointChoices'][s][j]['cloud']];parts=collections.defaultdict(list)
        for color,v in zip(cloud['colors'],cloud['vectors'],strict=True):parts[json.dumps(color,sort_keys=True)].append(v)
        layout=tuple((c,len(parts[c])) for c in sorted(parts));v=np.array([x for c in sorted(parts) for a in range(3) for x in sorted(p[a] for p in parts[c])]);assert np.isfinite(v).all() and np.max(np.abs(v))<=10000
        vectors.append(v);groups[b['markPoints'][s],layout].append(k);inventories.append(b['inventory'])
    for ids in groups.values():
        array=np.array([vectors[k] for k in ids]);owner=np.array([inventories[k] for k in ids])
        for k in ids:
            expected=sorted(ids[a] for a in np.flatnonzero((np.max(np.abs(array-vectors[k]),axis=1)<=threshold)&(owner!=inventories[k])))
            assert graph['neighbors'][k]==expected, 'Missing or extra complement-index edge'
    reports.append(graph['report']);print(json.dumps(reports[-1]),flush=True)
with output.open('x') as f:json.dump({'scope':__doc__,'indexHash':digest(index_path),'blocksHash':digest(blocks_path),'sourceModelHash':digest(source_path),'verifierHash':digest(pathlib.Path(__file__)),'results':reports,'limits':'Complete signature superset, not certified cloud compatibility. Runtime must retain full marking checks.'},f,indent=2)
